# Spike Report: Numba arm64 availability and stability
## (realtime-variety-render — e5 Numba JIT spike)

**Spike:** roadmap §9 spike-lane item 2 — "Numba arm64 availability and stability" (≤2 days)
**Validates §4 [MUST]:** *Numba `@njit(parallel=True)` is available and stable on macOS arm64 (Numba ≥0.60) with the `workqueue` threading layer (not unguarded TBB).*
**Blocks:** `realtime-variety-render-e5`
**Date:** 2026-05-22
**Dev machine:** Windows 11 10.0.26200 (AMD64), Python 3.11.9
**Primary target:** macOS Apple Silicon (arm64)
**Spike script:** `.claude/notes/roadmaps/realtime-variety-render/spike-numba-test.py` (re-runnable)

---

## 1. Verdict

| Assumption | Verdict |
|---|---|
| **[MUST]** Numba `@njit(parallel=True)` is available and stable with the `workqueue` threading layer (not unguarded TBB) | **VALIDATED-WITH-CAVEAT** |
| **[SHOULD]** First-call JIT latency for the v0 2-generator scope stays under 500 ms | **NOT MET — warm-up strategy is mandatory, not optional** |

**Overall: e5 is cleared to proceed**, with two corrections to the roadmap's e5 spec (see §5) and the macOS on-device checklist (§7) completed before shipping.

### Verdict rationale

`@njit` and `@njit(parallel=True)` (with `prange`) both compile, run, and produce results **numerically identical to the NumPy reference** to `rtol=atol=1e-12` on a representative degree-4 field grid (the Fermat-quartic / Enriques-sextic family shape). The `workqueue` threading layer was explicitly requested via `numba.config.THREADING_LAYER = "workqueue"` and confirmed as the **active** layer by `numba.threading_layer()` after the parallel kernel ran — so the [MUST]'s "not unguarded TBB" requirement is satisfiable and satisfied. The caveats are (a) the roadmap's version pin is stale, (b) the first-call JIT cost exceeds the [SHOULD] budget, and (c) Windows-not-macOS — see §3–§5.

---

## 2. Environment

| Package | Version | Notes |
|---|---|---|
| Python | 3.11.9 | |
| numpy | **2.4.6** | newer than the roadmap pin assumed |
| numba | **0.65.1** | installed by the spike; `pip install numba` resolved this |
| llvmlite | 0.47.0 | numba's LLVM binding, pulled transitively |

`pip install numba` resolved to **numba 0.65.1** and **did NOT downgrade numpy** — numba 0.65.1 declares `numpy>=1.22` and accepts numpy 2.4.6. There was no dependency conflict with the existing pinned stack (`PySide6`, `pyvista 0.48.4`, `pyvistaqt 0.11.4`, `vtk 9.6.2`).

numba is currently **installed in the dev venv** (the venv is gitignored). e5 owns the formal `requirements.txt` edit.

---

## 3. Empirical Results (spike script run)

Representative kernel: a degree-4 polynomial scalar field `x⁴+y⁴+z⁴ + c·(x²y²+y²z²+x²z²)` sampled on an `n³` grid (`n=96`) — the exact shape of the e5 v0 targets (Fermat quartic, Enriques canonical sextic), which today use NumPy `meshgrid` broadcasting.

| Check | Result |
|---|---|
| `@njit` serial — compiles, runs, `numeric == NumPy` | **PASS** (first-call JIT 1156 ms; warm 0.19 ms) |
| `@njit(parallel=True)` + `prange` — compiles, runs, `numeric == NumPy` | **PASS** (first-call JIT 360 ms; warm 0.10 ms) |
| `numba.threading_layer()` after the parallel call | `'workqueue'` — **PASS** (the [MUST] requirement) |
| `numba.get_num_threads()` | 16 (dev machine core count) |
| Numerical equivalence to NumPy | `np.allclose(rtol=1e-12, atol=1e-12)` — exact |

**Speedup (warm, n=96):** NumPy broadcasting 18.75 ms → `@njit` serial 0.19 ms (~100×) → `@njit(parallel=True)` 0.10 ms (~184×). The e5 acceptance target is **≥5× field-eval speedup** — cleared by a wide margin. (The large factor is partly because NumPy broadcasting allocates many intermediate `X2/Y2/Z2/...` temporaries that a fused Numba kernel avoids; the real-generator speedup will be smaller than 100× but comfortably past 5×.)

---

## 4. First-call JIT latency — the [SHOULD] is not met

Measured first-call (compilation) cost: **serial kernel 1156 ms + parallel kernel 360 ms = 1516 ms total**. The §4 [SHOULD] budget is **≤500 ms total for the v0 2-kernel scope**.

e5 v0 ships **two `@njit(parallel=True)` kernels** (Fermat + Enriques canonical). A single parallel kernel compiled in ~360 ms here; two would be ~700–800 ms — still **over the 500 ms budget**. (The serial kernel's 1156 ms is inflated by being the *first* LLVM invocation of the process — cold LLVM init; it is not representative of a parallel kernel's marginal cost. But even discounting that, 2× parallel kernels exceed 500 ms.)

**Consequence:** the §4 [SHOULD] fallback — *"move warm-up to background thread at first surface selection rather than eager app startup"* — is **mandatory for e5, not optional**. e5 must JIT-warm the kernels off the GUI thread. This is low-risk: **the e4 background-thread worker is the natural host** — the first `surface.generate()` for Fermat or Enriques already runs on a `QThreadPool` worker, so the JIT compile happens off-thread for free on the first real render. No eager app-startup warm-up is needed; the e4 worker absorbs it. e5 should NOT add a separate startup warm-up path — it should rely on the e4 worker and simply accept that the *first* Fermat/Enriques render after launch carries the ~400 ms compile (still off the GUI thread, so the UI never freezes).

`cache=True` on the `@njit` decorators is a second mitigation: numba persists compiled kernels to disk, so the JIT cost is paid once per machine, not once per process. e5 should set `cache=True` (the spike script used `cache=False` to measure cold cost honestly).

---

## 5. Corrections to the roadmap e5 spec

The spike surfaced two spec errors in roadmap §6.3 / §8 `realtime-variety-render-e5`:

1. **The version pin `numba>=0.60,<0.62` is stale and wrong for this environment.** numba 0.60–0.61 supports numpy only up to ~2.1–2.2; this repo runs **numpy 2.4.6**, which needs **numba ≥0.65**. e5 must pin **`numba>=0.65,<0.66`** (and `llvmlite` follows transitively — no explicit pin needed). The roadmap's `<0.62` upper bound would make `pip install` either fail or downgrade numpy and break the pinned `pyvista`/`vtk` stack.

2. **The "startup warm-up strategy ... ≤500 ms" acceptance signal is not achievable as written** (§4). e5 should drop the eager-startup warm-up entirely and instead document that the first Fermat/Enriques render absorbs the JIT compile **on the e4 worker thread** (off the GUI thread — no freeze), plus set `cache=True` so the cost is once-per-machine. The acceptance signal should be reworded from "first-call JIT < 500 ms" to "first-call JIT happens off the GUI thread (e4 worker) and `cache=True` is set".

---

## 6. Threading-layer interaction with the e4 worker (challenger CAND-2 objection c)

The challenger flagged that Numba's parallel threading could contend with VTK's SMP threading inside the e4 worker. The spike confirms the mitigation: **`workqueue` is selectable and stable**. `workqueue` is Numba's built-in, dependency-free layer — it does not share a thread pool with VTK's SMP backend (`STDThread`/TBB). e5 must set `numba.config.THREADING_LAYER = "workqueue"` (or the `NUMBA_THREADING_LAYER=workqueue` env var) **at import time in `surfaces.py`, before any `@njit(parallel=True)` kernel is first called** — exactly as the spike script does. With `workqueue` selected, a Numba kernel running inside the e4 `QThreadPool` worker uses its own thread pool and does not fight VTK SMP. e5 should also consider `numba.set_num_threads(...)` to cap Numba's worker count so a Numba kernel + VTK Flying Edges (also SMP-threaded, e6) running back-to-back on the same e4 worker do not jointly oversubscribe the CPU.

---

## 7. Residual macOS verification

This spike ran on **Windows AMD64**. The [MUST] targets **macOS Apple Silicon (arm64)**. The following must be confirmed on actual arm64 hardware before e5 ships:

1. **Wheel availability:** `pip install "numba>=0.65,<0.66"` on macOS arm64 resolves an Apple-Silicon wheel (numba ships `macosx_*_arm64` wheels for 0.65.x — confirm against the *installed* numpy 2.4.6).
2. **`workqueue` on arm64:** `numba.config.THREADING_LAYER = "workqueue"` then `numba.threading_layer()` returns `'workqueue'` after a parallel call (the spike confirmed this on Windows; arm64 should match — `workqueue` is platform-independent C, but verify).
3. **Numeric equivalence on arm64:** re-run `spike-numba-test.py` on macOS — confirm the kernels are still `allclose` to NumPy (arm64 NEON vs x86 SSE/AVX float ordering can differ at the ULP level; `rtol=1e-12` should still hold for a degree-4 polynomial, but verify).
4. **JIT latency on arm64:** measure first-call compile cost on Apple Silicon (LLVM codegen speed differs); confirm the e4-worker-absorbs-it conclusion still holds.
5. **No contention with VTK SMP on arm64:** run a Numba `parallel=True` kernel and a VTK Flying Edges contour back-to-back on the same thread and confirm no crash/hang (arm64 is where VTK SMP issues historically surfaced — cf. the e3 spike's VTK #18782 caveat).

The spike script `spike-numba-test.py` is the re-runnable harness for items 2–4; item 5 is exercised naturally by the e5 implementation's off-screen render verification.

---

## 8. Recommendation for e5

**Proceed.** The spike evidence supports starting e5 (Numba JIT field-evaluation kernels) under these conditions:

1. **Pin `numba>=0.65,<0.66`** in `requirements.txt` (NOT the roadmap's stale `>=0.60,<0.62`).
2. **Set the `workqueue` threading layer** at `surfaces.py` import time, before any `@njit(parallel=True)` kernel runs.
3. **Use `@njit(parallel=True, cache=True)`** — `cache=True` makes the JIT cost once-per-machine.
4. **No eager startup warm-up.** The first Fermat/Enriques render absorbs the ~400 ms JIT compile on the **e4 worker thread** (off the GUI thread). Reword the e5 acceptance signal accordingly (§5 item 2).
5. **Keep the NumPy reference paths** for the numerical spot-check tests — e5's `tests/` must assert `@njit` kernel output `== NumPy` reference at ≥3 parameter points each for Fermat + Enriques canonical (Qt-free, AI-2 clean).
6. **Complete the §7 macOS on-device checklist** before shipping — a bounded ~0.5-day exercise on Apple Silicon.

Numba is genuinely available, stable, numerically exact, and ~100–184× faster than NumPy broadcasting on the representative kernel with the `workqueue` layer active. The two roadmap-spec corrections (§5) and the macOS residual (§7) are the only open items; neither blocks starting e5 implementation on Windows.
