# Implementation plan — realtime-variety-render-e5 (Numba JIT field kernels v0)

Inline path. Scope: CAND-2 v0 — Fermat quartic + Enriques canonical sextic only.

1. **surfaces.py imports.** After `import numpy as np`, add `import numba` +
   `numba.config.THREADING_LAYER = "workqueue"` (set at import, before any
   kernel is first *called* — keeps Numba off VTK's SMP pool) + `from numba
   import njit, prange`. numba is the first new compute dependency since
   scikit-image was dropped in e6 — pure compute, no renderer (AI-1 clean).

2. **Two `@njit(parallel=True, cache=True)` kernels** (module-level, in the
   Helpers section after `_marching_cubes_to_polydata`): `_fermat_field_kernel`
   and `_enriques_fig1_field_kernel`. Out-array-fill pattern — `prange` over
   the outer i-axis, plain `range` j/k, scalar `g[i]`/`g[j]`/`g[k]` reads.
   Each is a **term-by-term transcription** of the current NumPy expression in
   the IDENTICAL operator order (so the per-voxel IEEE-754 op sequence matches
   NumPy's elementwise evaluation) with `np.clip` folded in as scalar
   `min/max`. No `set_num_threads` cap: only one e4 worker runs at a time
   (single-flight guard) and the kernel + VTK Flying Edges are sequential
   within `generate()` — no concurrent oversubscription.

3. **Rewrite the two generators' field blocks.** In `fermat_quartic`
   (surfaces.py:306-318) and `enriques_figure_1` (:414-422): keep the
   `g = np.linspace(...)` line, delete the `np.meshgrid` + `X2,Y2,Z2` + `F=(…)`
   + `np.clip` block, replace with `F = np.empty((n, n, n)); _<kernel>(g, …, F)`.
   `n` stays int-coerced in the generator (AI-8); the kernel only sees `g` +
   float params. `_marching_cubes_to_polydata` and the AI-14 ValueError guard
   are downstream and untouched (AI-6 / AI-14 clean).

4. **requirements.txt.** Add `numba>=0.65,<0.66` (spike-corrected — the
   roadmap's `>=0.60,<0.62` is stale, incompatible with numpy 2.4.x). llvmlite
   is transitive, no explicit pin.

5. **Tests + verification.** New `tests/test_numba_field_kernels.py` (Qt-free,
   AI-2): a NumPy reference function copy-pasted from the current surfaces.py
   field expressions; assert `np.allclose(kernel, ref, rtol=1e-9, atol=1e-9)`
   at ≥3 parameter points each for Fermat + Enriques (1e-9 absorbs any
   op-fusion ULP drift while still catching transcription bugs by orders of
   magnitude). Off-screen render verify Fermat + Enriques Fig 1 (AI-3); measure
   before/after generate() timing for the ≥5× field-eval acceptance signal.

Constraints: AI-1 (numba = compute dep, allowed), AI-2 (Qt-free tests), AI-3
(pv.OFF_SCREEN), AI-6 (implicit pipeline; Hanson untouched), AI-8 (int `n`
coerced in-generator), AI-14 (PolyData-or-ValueError contract unchanged).
Predecessor e4 complete; Numba arm64 spike passed (VALIDATED-WITH-CAVEAT).
