"""Spike: Numba arm64 availability + stability  (realtime-variety-render e5 spike).

Validates the section-4 [MUST]: "Numba @njit(parallel=True) is available and
stable ... with the workqueue threading layer (not unguarded TBB)".

Standalone script (NOT a pytest test -- AI-2). Run:
    .venv/Scripts/python.exe .claude/notes/roadmaps/realtime-variety-render/spike-numba-test.py

What it checks:
  1. numba imports; version + llvmlite version reported.
  2. plain @njit compiles and runs, numerically == NumPy.
  3. @njit(parallel=True) + prange compiles and runs, numerically == NumPy.
  4. the `workqueue` threading layer is selectable and is the ACTIVE layer
     for the parallel kernel (the [MUST] explicitly rules out unguarded TBB,
     which could contend with VTK's SMP threads in the e4 worker).
  5. first-call JIT latency is measured (the section-4 [SHOULD]: warm-up
     budget <= 500 ms for the v0 2-generator scope).
  6. NumPy-vs-Numba speedup on a representative degree-4 field grid.

The kernel mirrors the e5 v0 target shape: a degree-4 polynomial scalar
field sampled on an n^3 grid (the Fermat-quartic / Enriques-sextic family
is exactly this -- broadcasting NumPy today, a prange kernel under e5).
"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

print("=" * 68)
print("Numba arm64 availability + stability spike")
print("=" * 68)

# --- 1. import + versions --------------------------------------------------
import platform

import numpy as np

print(f"platform : {platform.platform()}")
print(f"machine  : {platform.machine()}")
print(f"python   : {sys.version.split()[0]}")
print(f"numpy    : {np.__version__}")

try:
    import numba
    from numba import njit, prange
    import llvmlite
except Exception as exc:  # noqa: BLE001
    print(f"FAIL: numba import failed: {exc}")
    sys.exit(1)

print(f"numba    : {numba.__version__}")
print(f"llvmlite : {llvmlite.__version__}")

# Request the workqueue threading layer BEFORE any parallel function is
# compiled/run.  workqueue is Numba's always-available, dependency-free
# layer; the [MUST] rules out unguarded TBB (it could contend with VTK SMP).
numba.config.THREADING_LAYER = "workqueue"

failures: list[str] = []
BOUNDS = 1.8
N = 96  # representative interactive grid size


# --- reference + kernels ---------------------------------------------------
def field_numpy(n: int, c: float, bounds: float = BOUNDS) -> np.ndarray:
    """NumPy-broadcasting degree-4 field (the current surfaces.py style)."""
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    return X2 * X2 + Y2 * Y2 + Z2 * Z2 + c * (X2 * Y2 + Y2 * Z2 + X2 * Z2)


@njit(cache=False)
def _field_njit(g, c, out):
    n = g.shape[0]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                x2 = g[i] * g[i]
                y2 = g[j] * g[j]
                z2 = g[k] * g[k]
                out[i, j, k] = (
                    x2 * x2 + y2 * y2 + z2 * z2
                    + c * (x2 * y2 + y2 * z2 + x2 * z2)
                )


@njit(parallel=True, cache=False)
def _field_njit_parallel(g, c, out):
    n = g.shape[0]
    for i in prange(n):  # parallel over the outer axis
        for j in range(n):
            for k in range(n):
                x2 = g[i] * g[i]
                y2 = g[j] * g[j]
                z2 = g[k] * g[k]
                out[i, j, k] = (
                    x2 * x2 + y2 * y2 + z2 * z2
                    + c * (x2 * y2 + y2 * z2 + x2 * z2)
                )


def _run(label, kernel, jit_budget_note=False):
    g = np.linspace(-BOUNDS, BOUNDS, N)
    out = np.empty((N, N, N), dtype=np.float64)
    ref = field_numpy(N, 1.0)
    # first call -> compilation happens here
    t0 = time.perf_counter()
    kernel(g, 1.0, out)
    jit_ms = (time.perf_counter() - t0) * 1000.0
    if not np.allclose(out, ref, rtol=1e-12, atol=1e-12):
        max_err = float(np.max(np.abs(out - ref)))
        failures.append(f"{label}: numerical mismatch vs NumPy (max |err|={max_err:.2e})")
        print(f"  FAIL [{label}]: numerical mismatch, max|err|={max_err:.2e}")
        return None
    # warm (compiled) timing -- best of 5
    warm = []
    for _ in range(5):
        t0 = time.perf_counter()
        kernel(g, 1.0, out)
        warm.append((time.perf_counter() - t0) * 1000.0)
    warm_ms = min(warm)
    print(f"  PASS [{label}]: numeric==NumPy | first-call(JIT) {jit_ms:7.1f} ms"
          f" | warm {warm_ms:7.2f} ms")
    return jit_ms, warm_ms


print()
print("--- 2/3. njit + njit(parallel=True) compile, run, numeric check ---")
serial = _run("@njit serial", _field_njit)
par = _run("@njit parallel", _field_njit_parallel)

# --- 4. threading layer ----------------------------------------------------
print()
print("--- 4. active threading layer ---")
try:
    layer = numba.threading_layer()  # only valid AFTER a parallel call ran
    print(f"  numba.threading_layer() -> {layer!r}")
    print(f"  numba.get_num_threads() -> {numba.get_num_threads()}")
    if layer != "workqueue":
        failures.append(
            f"threading layer is {layer!r}, expected 'workqueue' "
            "(the [MUST] rules out unguarded TBB)"
        )
        print(f"  FAIL: expected 'workqueue', got {layer!r}")
    else:
        print("  PASS: workqueue is the active layer")
except Exception as exc:  # noqa: BLE001
    failures.append(f"threading_layer() raised: {exc}")
    print(f"  FAIL: threading_layer() raised: {exc}")

# --- 5/6. JIT-latency budget + speedup ------------------------------------
print()
print("--- 5/6. JIT-latency budget + speedup ---")
# NumPy reference timing (best of 5)
npt = []
for _ in range(5):
    t0 = time.perf_counter()
    field_numpy(N, 1.0)
    npt.append((time.perf_counter() - t0) * 1000.0)
numpy_ms = min(npt)
print(f"  NumPy broadcasting        : {numpy_ms:7.2f} ms  (n={N})")
if serial:
    print(f"  @njit serial   warm       : {serial[1]:7.2f} ms"
          f"  ({numpy_ms / serial[1]:4.2f}x)")
if par:
    print(f"  @njit parallel warm       : {par[1]:7.2f} ms"
          f"  ({numpy_ms / par[1]:4.2f}x)")
    total_jit = (serial[0] if serial else 0.0) + par[0]
    print(f"  total first-call JIT cost : {total_jit:7.1f} ms"
          f"  (section-4 [SHOULD] budget: <= 500 ms for the v0 2-kernel scope)")

print()
print("=" * 68)
if failures:
    print(f"RESULT: FAIL ({len(failures)} issue(s))")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS -- @njit + @njit(parallel=True) compile, run, are")
print("numerically identical to NumPy, and run on the workqueue layer.")
sys.exit(0)
