# agent-b research brief — realtime-variety-render-e5

**Milestone:** realtime-variety-render-e5 — Numba JIT field-evaluation kernel v0 (CAND-2)
**Lens:** Numba-mechanics / perf / integration
**Date:** 2026-05-22

---

## 1. TL;DR

Replace the two NumPy-broadcasting field expressions in `fermat_quartic` and `enriques_figure_1` with `@njit(parallel=True, cache=True)` out-array-fill kernels (kernel writes into a pre-allocated `np.empty`, `prange` over the outer i-axis), and set `numba.config.THREADING_LAYER = "workqueue"` once at `surfaces.py` import time before any kernel is defined — the spike's `spike-numba-test.py` is the working template, copy its structure verbatim. The main risk is CPU oversubscription: the e5 Numba kernel and the e6 VTK Flying Edges contour run back-to-back on the *same* e4 `QThreadPool` worker, so two SMP-style thread pools (Numba workqueue + VTK SMP) can each spawn ~core-count threads; the mitigation is a conservative `numba.set_num_threads(...)` cap at import time. Backup plan: if `parallel=True` shows no measured win over serial `@njit` (the fused-loop serial kernel already gave ~100× over NumPy in the spike), ship `@njit(cache=True)` *serial* — it clears the ≥5× target alone and removes the entire oversubscription question.

---

## 2. Prior art in this repo

- **`surfaces.py:243-319` `fermat_quartic`** — target #1. The NumPy field expression is `surfaces.py:308-318`: builds `g`, `np.meshgrid(g,g,g,indexing="ij")`, `X2,Y2,Z2 = X*X,...`, then the degree-4 polynomial `F` and `F = np.clip(F, -200.0, 200.0)`. `n` is adaptive (`surfaces.py:303-304`, `np.clip(round(220*bounds/2.5),200,220)`), `bounds` adaptive (`:292-293`). Reference formula = lines 310-316 verbatim, including the `- c` term and the `np.clip` post-step.
- **`surfaces.py:396-423` `enriques_figure_1`** — target #2. NumPy field at `:414-422`: `g=linspace`, meshgrid `indexing="ij"`, `X2,Y2,Z2`, `F = X2*Y2 + X2*Z2 + Y2*Z2 + X2*Y2*Z2 + c*(X*Y*Z)*(1+X2+Y2+Z2)`, then `F = np.clip(F, -10.0, 10.0)`. `n=240`, `bounds=1.89` (fixed defaults, `:398-400`).
- **`surfaces.py:86-177` `_marching_cubes_to_polydata`** — the implicit-pipeline sink. Both target kernels feed it (`fermat_quartic` `:319`, `enriques_figure_1` `:423`). It expects a `field: np.ndarray` of shape `(n,n,n)`; `field.ravel(order="F")` at `:146`. AI-6 lock — kernel changes the *field array* only, never this helper or the contour/Taubin/normals chain.
- **`render_worker.py:118-198` `MeshWorker`** — the e4 background-thread worker. `surface.generate()` is called at `render_worker.py:174` (`mesh = self._generate(**self._params)`) inside `_compute()`, which runs on a `QThreadPool` worker thread (`run()` `:146-151`). **This confirms the first-call JIT compile happens off the GUI thread for free** — no eager warm-up needed. `gen_ms` is measured by `time.perf_counter()` brackets at `render_worker.py:164` / `:180` (CAND-12 telemetry field, `MeshResult.gen_ms` `:99`).
- **`app.py:513-583` `_render_current`** — submit-only dispatch; constructs `MeshWorker(surface.generate, dict(params), self._generation)` at `app.py:576`, starts it on `self._render_pool` (a dedicated `QThreadPool`, `app.py:180`) at `:583`.
- **`app.py:586-706` `_on_mesh_ready`** — result slot. CAND-12 telemetry surfaces at **`app.py:636`** (`print(f"[render] {surface.label}: {result.gen_ms:.0f} ms")`) and in the status bar at `:683` / `:699` (`{result.gen_ms:.0f} ms`). This `[render] <label>: <ms>` stdout line is the before/after measurement channel for the acceptance signal.
- **Spike artifacts** — `.claude/notes/roadmaps/realtime-variety-render/spike-numba-arm64.md` (verdict VALIDATED-WITH-CAVEAT) and `spike-numba-test.py`. The test script's `_field_njit_parallel` (`:88-100`) is the **literal kernel template**: out-array param, `prange(n)` outer, plain `range` inner, scalar `g[i]*g[i]` reads. `numba.config.THREADING_LAYER = "workqueue"` is set at script line 57, *before* any kernel runs.
- **`tests/test_mesh_generators.py`** + **`tests/test_marching_cubes_empty.py`** — existing generator/helper tests; the new numerical-spot-check file should be a separate `tests/test_numba_field_kernels.py` (pattern precedent: e6 lessons — keep contract tests separate from smoke tests).
- **`requirements.txt`** — 5 lines, no numba today; `numpy>=1.26,<3` (dev venv has numpy 2.4.6 per spike §2). scikit-image was *removed* as a dependency in e6 (CONTEXT.md §3 line 57) — numba is the first new compute dependency since.

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Numba `@njit` / `prange` docs | numba.readthedocs.io/en/stable/user/parallel.html | `parallel=True` + `prange` auto-parallelizes the marked loop; out-array writes inside `prange` are the canonical pattern (no reduction race when each iteration writes disjoint `out[i,...]`). | Kernel structure — outer `prange` over i is race-free. |
| Numba caching docs | numba.readthedocs.io/en/stable/developer/caching.html | `cache=True` persists compiled code to a `__pycache__/*.nb*` file next to the source module; cache key includes source hash, numba/llvmlite version, CPU features. **`cache=True` IS supported for `parallel=True`** kernels (the prior "no cache for parallel" limitation was lifted years ago, ≥0.x stable). Cache is per-machine; invalidates automatically on source/version/CPU change. | Confirms `@njit(parallel=True, cache=True)` is a valid combination; JIT cost is once-per-machine. |
| Numba threading-layer docs | numba.readthedocs.io/en/stable/user/threading-layer.html | Three layers: `tbb`, `omp`, `workqueue`. `workqueue` is the always-available, dependency-free built-in. Must be selected via `numba.config.THREADING_LAYER` (or `NUMBA_THREADING_LAYER` env) **before the first parallel kernel runs**. `numba.threading_layer()` only returns a value *after* a parallel call. `numba.set_num_threads(k)` caps the pool. | Threading-layer selection mechanics + the oversubscription cap. |
| numba 0.65.x PyPI | pypi.org/project/numba/ | numba 0.65.x ships `macosx_*_arm64`, `macosx_*_x86_64`, `win_amd64`, `manylinux` wheels; declares `numpy>=1.22` and `llvmlite>=0.x` as the only hard deps. License **BSD-2-Clause** (confirmed — Anaconda Inc., 2-clause). | requirements.txt pin; arm64 wheel availability. |
| llvmlite PyPI | pypi.org/project/llvmlite/ | numba's LLVM binding, pulled transitively (no explicit pin needed). License **BSD-2-Clause** (confirmed). Spike resolved llvmlite 0.47.0. | Transitive-dep license clearance. |
| Spike report §4, §6, §8 | repo-local `spike-numba-arm64.md` | (a) version pin `>=0.60,<0.62` is STALE — numba 0.60-0.61 caps numpy at ~2.1-2.2, repo runs 2.4.6 → must pin `numba>=0.65,<0.66`. (b) first-call JIT ~700-1500 ms EXCEEDS the 500 ms budget — no eager warm-up; rely on e4 worker + `cache=True`. (c) `workqueue` confirmed selectable and active. | The two spec corrections + the threading-layer + cache decisions. |

(Per memory lessons: for a well-specified mechanical pipeline-swap milestone the external-research budget is small — the signal here is repo-local file:line attach points + the spike verdict, not arXiv triangulation.)

## 4. Recommended approach

**Kernel structure (both generators).** For each target, add a module-level `@njit(parallel=True, cache=True)` kernel that takes the 1-D axis array `g` plus the scalar params and an out-array, and fills `out` in place — exactly the `spike-numba-test.py:_field_njit_parallel` shape:

```
@njit(parallel=True, cache=True)
def _fermat_field_kernel(g, alpha, beta, gamma, c, out):
    n = g.shape[0]
    for i in prange(n):
        for j in range(n):
            for k in range(n):
                x = g[i]; y = g[j]; z = g[k]
                x2 = x*x; y2 = y*y; z2 = z*z
                val = ( x2*x2 + y2*y2 + z2*z2
                        + alpha*(x2*y2 + y2*z2 + z2*x2)
                        + beta*(x*y*z)*(x+y+z)
                        + gamma*(x2+y2+z2) - c )
                # clip inside the kernel — matches np.clip(F,-200,200)
                if val < -200.0: val = -200.0
                elif val > 200.0: val = 200.0
                out[i,j,k] = val
```

The generator then becomes: `g = np.linspace(...); F = np.empty((n,n,n)); _fermat_field_kernel(g, alpha, beta, gamma, c, F); return _marching_cubes_to_polydata(F, bounds)`. The Enriques kernel mirrors this with its formula (`x2*y2 + x2*z2 + y2*z2 + x2*y2*z2 + c*(x*y*z)*(1+x2+y2+z2)`, clip ±10.0). **The `np.clip` MUST move inside the kernel** so the kernel is numerically identical to the current `F = np.clip(F,...)` step — keeping `np.clip` outside re-introduces a NumPy temp pass and defeats the fusion, and a kernel that omits it would not match the reference.

**Threading layer + thread cap.** At the *top* of `surfaces.py`, immediately after `import numba` (and before any `@njit` decorator is evaluated — decorator evaluation is lazy compile but the config must be set before first *call*; setting it at import is the safe, spike-proven placement):
```
import numba
numba.config.THREADING_LAYER = "workqueue"
numba.set_num_threads(max(1, numba.config.NUMBA_NUM_THREADS // 2))   # see Risk R1
from numba import njit, prange
```
Place this block above the `ParamSpec`/`Surface` dataclasses. `workqueue` keeps Numba off VTK's SMP pool (spike §6).

**`cache=True`.** Set on both decorators. The first Fermat/Enriques render after a fresh install pays the ~400-800 ms compile *on the e4 worker thread* (off the GUI thread — no freeze); every later process reuses the on-disk cache. **No eager startup warm-up** — the spike (§4, §8) explicitly rejects it. Reword the roadmap's "startup warm-up ≤500 ms" acceptance signal to "first-call JIT happens off the GUI thread (e4 worker) and `cache=True` is set".

**requirements.txt.** Add `numba>=0.65,<0.66` (NOT the roadmap's stale `>=0.60,<0.62`). No `llvmlite` line (transitive). No `numpy` change — numba 0.65.1 accepts numpy 2.4.6.

**Tests** — `tests/test_numba_field_kernels.py`, pure NumPy+Numba (AI-2): for each generator, compute the field both ways (call the njit kernel into an `np.empty`, and the literal NumPy expression as the reference) at ≥3 parameter points each, assert `np.allclose(rtol=1e-12, atol=1e-12)`. Use small `n` (e.g. 32-48) to keep the suite inside the 4 s budget. The reference NumPy expression in the test must be copy-pasted from the current `surfaces.py` lines so the test pins "kernel == today's NumPy".

**Telemetry capture.** The before/after signal is the existing `[render] <label>: <ms>` stdout line (`app.py:636`) — capture it for Fermat + Enriques before the change (NumPy baseline) and after. Optionally also instrument a one-off field-eval-only timer in the spike-style harness; do not add new telemetry to `MeshWorker` (out of slice).

Word count ~470.

## 5. Alternatives considered

- **Eager startup warm-up thread** — rejected: spike §4/§8 explicitly says don't; the e4 worker already absorbs the first-call compile off the GUI thread, and `cache=True` makes it once-per-machine. Adding a warm-up path is dead code.
- **`@guvectorize` / `@vectorize`** instead of `@njit`+`prange` — rejected: more decorator machinery, signature strings, and no clear win over a plain fused `prange` loop for a 3-D grid fill; the spike validated the plain `njit` path, not guvectorize.
- **Keep `np.clip` outside the kernel** — rejected: re-introduces a full-array NumPy temp pass and breaks numeric-identity framing; clip-in-kernel is a trivial `if/elif` per voxel.
- **`parallel=True` with no `set_num_threads` cap** — rejected as the *default*: on a many-core machine Numba spawns core-count threads and, running back-to-back with VTK Flying Edges SMP on the same e4 worker, can oversubscribe (Risk R1). A conservative cap is cheap insurance.
- **TBB threading layer** — rejected: spike [MUST] explicitly rules out unguarded TBB (shares/contends with VTK SMP); `workqueue` is the required, dependency-free choice.
- **Numba-ize all 11 implicit generators now** — rejected: out of slice. v0 scope is exactly Fermat quartic + Enriques canonical sextic (the two highest-cost per the roadmap).
- **Kernel returns a new array instead of filling `out`** — acceptable but the out-fill pattern matches the spike template and makes the `np.empty` allocation explicit at the call site; recommend out-fill for consistency with the validated spike.

## 6. Risks and unknowns

- **R1 — Numba-vs-VTK-SMP thread oversubscription (the headline risk).** Inside one e4 `QThreadPool` worker, `surface.generate()` runs the Numba `parallel=True` kernel and then VTK Flying Edges (e6, also SMP-threaded) back-to-back. They are sequential, not concurrent, so true simultaneous oversubscription is limited — but each spins up its own thread pool, and on a busy machine the combined thread churn can regress latency vs. serial. Mitigation: `numba.set_num_threads(...)` cap (≈ half core count) at import; the `workqueue` layer keeps Numba's pool separate from VTK's. If measured `parallel=True` shows no win, fall back to serial `@njit` (the backup plan — serial already cleared ~100× in the spike). The implementer should measure both.
- **R2 — `cache=True` for `parallel=True`.** Confirmed supported by current numba docs; the on-disk cache lives in `surfaces.py`'s `__pycache__`. Unknown: whether a read-only install dir blocks cache writes (numba then silently recompiles each process — degraded, not broken). Not a blocker; note it.
- **R3 — numeric identity at the ULP level.** Spike confirmed `rtol=atol=1e-12` on x86; arm64 NEON float ordering can differ. The kernel reorders the polynomial evaluation relative to NumPy broadcasting (per-voxel scalar ops vs. whole-array temps), so exact bit-identity is not guaranteed — `np.allclose(rtol=1e-12, atol=1e-12)` is the correct test tolerance, not `array_equal`. Degree-4/6 polynomials are well-conditioned; this should hold.
- **R4 — import latency.** `import numba` at `surfaces.py` module load adds a measurable cost (numba imports llvmlite + LLVM bindings — order ~100-300 ms cold). `surfaces.py` is imported at app startup, so this lands on the cold-boot path, not a render. Acceptable (one-time, < the qtawesome font-load cost the repo already accepts) but worth noting; do NOT lazy-import numba (the `@njit` decorators need it at module scope).
- **R5 — AI conflicts:** AI-1 numba is a pure compute dep, no renderer change — clean. AI-2 tests are pure NumPy/Numba — clean. AI-6 kernels feed `_marching_cubes_to_polydata` unchanged; Hanson parametric generators untouched — clean. AI-8 `n` int-coercion stays inside the generator (`int(np.clip(...))` already at `surfaces.py:304`) — clean; do not pass a float `n` to the kernel, coerce first. AI-14 generators still return `pv.PolyData` / raise `ValueError` via the unchanged `_marching_cubes_to_polydata` zero-set guard — clean. No AI violations.
- **R6 — render-time budget.** No regression risk: field eval gets *faster*; the ≥5× target is far inside the spike's measured ~100-184×. Total `generate()` budget (~500 ms) is unaffected except favorably.
- **Unknown — macOS arm64 residual.** Spike §7 lists 5 on-device checks (wheel resolves, `workqueue` active, numeric `allclose`, JIT latency, no VTK-SMP crash). The dev machine is Windows; the implementer cannot close these here. Note as a ship-gate, not an implementation blocker.

## 7. AI-15 disclaimers

N/A for this milestone. e5 adds no new variety, figure, or tooltip — it only changes *how* the Fermat-quartic and Enriques-canonical-sextic scalar field arrays are computed (NumPy broadcasting → Numba JIT). The mathematical objects, their docstrings, and `SUBTYPE_TOOLTIPS` entries are unchanged. The "real shadow / birational" honesty disclaimers already present in both generators' docstrings (`surfaces.py:250-286`, `:386-413`) require no edit.

## 8. Open questions for the user

None — the milestone brief, the spike report, and the two spike-driven spec corrections fully specify the slice. The only genuinely-open items (macOS arm64 on-device checks, spike §7) are a documented ship-gate, not an implementation ambiguity.
