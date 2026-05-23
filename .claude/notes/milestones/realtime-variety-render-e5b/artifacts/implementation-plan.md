# Implementation plan — realtime-variety-render-e5b (Numba JIT v1)

Inline path. Mechanical extension of the e5 v0 kernel pattern to the 9
remaining implicit generators.

1. **Read the e5 v0 templates as the canonical pattern.** `_fermat_field_kernel`
   (`surfaces.py:314-344`) and `_enriques_fig1_field_kernel` (`:347-374`):
   `@njit(parallel=True, cache=True)`; `prange` outer i with `x = g[i]; x2 =
   x*x` hoisted; plain `range` j/k inner; scalar per-voxel polynomial in
   identical operator order; clip folded as `if val < lo: val = lo; elif val
   > hi: val = hi`. **Use explicit multiplies for `**N` operators** (no
   `**3`, `**5`, `**6` — write `x*x*x`, `x4 = x2*x2; x5 = x4*x`, `x2*x2*x2`)
   so per-voxel IEEE-754 op order matches the NumPy reference at
   `rtol=atol=1e-9`.

2. **Add 9 new kernels in `surfaces.py` Helpers section.** Place after
   `_enriques_fig1_field_kernel`. One kernel per generator following
   agent-a's transcription table:
   - `_kummer_field_kernel(g, mu_squared, lam, sqrt2, out)` — clip ±50
   - `_enriques_fig2_field_kernel(g, lam0, lam3, c, out)` — clip ±10
   - `_enriques_fig3_field_kernel(g, k, out)` — clip ±50
   - `_enriques_fig4_field_kernel(g, tau, phi2, one_plus_2phi, out)` — clip ±20
   - `_dwork_field_kernel(g, psi, out)` — clip ±100 (explicit `**5`)
   - `_klein_cubic_field_kernel(g, z0, out)` — clip ±50
   - `_segre_cubic_field_kernel(g, a, b, out)` — clip ±1000 (explicit `**3`)
   - `_two_quadrics_field_kernel(g, p, q, mu, eps, lam0..lam4, out)` — clip ±200
   - `_sextic_double_solid_field_kernel(g, R, alpha, R6, out)` — clip ±200

3. **Rewrite the 9 generator field blocks.** Collapse each to the golden
   three lines: `g = np.linspace(...); F = np.empty((n,n,n),
   dtype=np.float64); _<surface>_field_kernel(g, <params>, F); return
   _marching_cubes_to_polydata(F, bounds[, second_smooth_iter=...])`.
   **Preserve every existing ValueError pre-check and RuntimeWarning** —
   Kummer pole/no-zero-set guards (`:546-551`), Dwork conifold warning
   (`:979-990`), two-quadrics ε-tube warning (`:1137-1142`) all stay in the
   generator BEFORE the kernel call (AI-14). Add `n = int(round(n))` to
   Enriques figs 2/3/4 for defensive AI-8 hygiene (mirrors fig 1).

4. **Extend `tests/test_numba_field_kernels.py`.** Add 9 verbatim NumPy
   reference functions, 9 `@pytest.mark.parametrize` blocks with 3 param
   points each (default/mid/extreme — agent-a's table), 9 `respects_clip_
   bounds` tests, and 9 entries in `test_kernels_have_a_zero_crossing_at_
   defaults`. Tolerance `rtol=atol=1e-9` inherited from e5. Avoid
   ψ=1 / ε<0.08 in the Dwork / two-quadrics parameter sweep to skip the
   RuntimeWarnings during pure-kernel equivalence checks.

5. **Verify + doc + commit.** Run `.venv/Scripts/python.exe -m pytest
   tests/ -q` (expect ~436 tests = current 410 + ~26 e5b additions). Off-
   screen render verify Kummer + Dwork + Klein cubic via `pv.OFF_SCREEN`
   (sample across the 4 variety families; AI-3 — never `MainWindow`).
   Update CONTEXT.md §3 numba bullet: "v0 scope is these 2 of 8 implicit
   generators; the rest are a future v1" → "v0+v1 covers all 11 implicit
   generators". `§8.20` workqueue caveat unchanged (single-flight scales
   for free). Commit ≤200 LOC each — likely 3 commits: (a) 4-5 kernels +
   generator rewrites, (b) remaining 4-5, (c) tests + CONTEXT.md.

Constraints: AI-1 (numba sanctioned per e5), AI-2 (Qt-free tests), AI-3
(pv.OFF_SCREEN), AI-6 (implicit pipeline only; Hanson untouched), AI-8
(int coercion in-generator), AI-14 (PolyData-or-ValueError; warnings
preserved). e4+e4b+e5 predecessors complete; macOS arm64 spike residual
carries forward.
