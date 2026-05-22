# Adversary critique — Numba JIT field-evaluation kernels (CAND-2)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** realtime-variety-render-e5 / commit range `3a07e6e..49f3f67`

> Format reference: `.claude/references/critique-format.md`.

**Diff stats:** 1 commit, 9 files, +777/-20. Production+test surface only: `surfaces.py` (+138/-20), `requirements.txt` (+1), `tests/test_numba_field_kernels.py` (+142 new). Remaining ~496 lines are pipeline artifacts (research briefs, implementation plan, dispatch log, state.json, researcher memory).

---

## Executive summary

- **[HIGH]** Total diff exceeds the 400-LOC review-quality threshold (885 lines); ~56% is pipeline artifacts — production+test surface is ~281 LOC, well within review capacity. Auto-finding logged; no code action required.
- **[MEDIUM]** The kernel-context comment in `fermat_quartic` and the milestone framing both claim `n` is "int-coerced in-generator", but `enriques_figure_1` does NOT coerce `n` — its `n: int = 240` parameter reaches `np.linspace`/`np.empty` directly. Latent (no slider exposes `n`), but the comment is inaccurate.
- **[MEDIUM]** No smoke-test coverage was added to `tests/test_mesh_generators.py` proving the *post-kernel* `fermat_quartic()` / `enriques_figure_1()` still return non-empty `pv.PolyData` — the new test exercises the kernels in isolation but not the full generator path through `_marching_cubes_to_polydata`. (Existing generator tests do cover this; verified 365/365 pass — so this is a "no NEW guard for the integration seam" gap, not a hole.)
- **[MEDIUM]** `numba.config.THREADING_LAYER` is set as a global, process-wide mutation at `surfaces.py` import time with no guard against a host process that has already pinned a different layer; harmless today but an undocumented import side-effect.
- **[LOW]** The `cache=True` JIT artifacts land in `__pycache__/` next to `surfaces.py` — already gitignored, so no repo-pollution risk, but this is not stated in the milestone artifacts.
- **[LOW]** The Fermat/Enriques polynomials are fully symmetric in x,y,z, so an axis-transposition transcription bug would be invisible to the equivalence test; an asymmetric probe confirmed the mapping is correct, but the test file does not encode that probe.
- **[LOW]** CONTEXT.md / `.claude/references/app-invariants.md` were not updated to record `numba` as a sanctioned compute dependency under AI-1, nor to note the new kernel layer in the AI-6 pipeline description.

**Verdict: SHIP-WITH-FIXES.** Numerical equivalence is sound — the kernels are verified term-exact and axis-correct, all 365 tests pass, and AI-1/AI-2/AI-6/AI-14 are respected. No CRITICALs, no HIGHs in the code path. The two MEDIUMs (inaccurate `n`-coercion comment, missing integration-seam guard) and the doc LOWs should close before milestone close, but none block.

---

## Critical findings (must-fix before this can ship)

None.

---

## High findings (should-fix this iteration)

### HIGH — Diff exceeds 400-LOC review-quality threshold (auto-finding)

**Where:** `git diff 3a07e6e..49f3f67` — 885 lines total.
**Evidence:** `git diff | wc -l` = 885 (> 400). Breakdown: production `surfaces.py` +138/-20, `requirements.txt` +1, test `tests/test_numba_field_kernels.py` +142 new; the remaining ~496 lines are `.claude/notes/...` pipeline artifacts (research briefs A/B 398 lines, implementation-plan 45, dispatch.log 4, state.json 51, researcher memory 18).
**Why it matters:** The auto-finding is non-waivable per the agent contract. However, per the milestone-specific instruction and the documented artifact-inflation pattern (sixth confirmed occurrence), review quality is judged on the production+test surface — ~281 LOC — which is comfortably reviewable.
**Suggested fix:** No code action required. Disposition: artifact-inflated diff; the reviewable code surface is small and was read end-to-end.

---

## Medium findings (nice-to-fix)

### MEDIUM — `n`-coercion comment is inaccurate for the Enriques generator

**Where:** `surfaces.py:411-413` (Fermat kernel-context comment), `surfaces.py:497-500` (`enriques_figure_1` signature + body).
**Evidence:** The Fermat comment states "`n` is already int-coerced above (AI-8)" — true for `fermat_quartic`, which runs `n = int(np.clip(round(...), 200, 220))` at line 409. But `enriques_figure_1(c=1.0, n=240, bounds=1.89)` performs **no** coercion: `n` flows straight from the parameter into `np.linspace(-bounds, bounds, n)` and `np.empty((n, n, n), ...)`. The milestone framing ("int `n` coerced in-generator, kernel sees only float `g`") therefore does not hold uniformly. `ENRIQUES_FIGURE_1_PARAMS` exposes only `c`, so the GUI cannot pass a float `n` — the gap is latent, reachable only by a direct float-`n` caller, and `np.linspace`/`np.empty` would raise `TypeError` (loud, not silent).
**Why it matters:** AI-8 says "coerce ints inside the generator." Fermat complies; Enriques relies on the default literal `240` being an int and on no caller passing a float. A future caller (a screenshot/export path passing computed `n`) would hit a raw `TypeError` rather than a graceful coercion. More immediately, the comment misrepresents the codebase to the next agent.
**Suggested fix:** Either add `n = int(round(n))` at the top of `enriques_figure_1` (mirrors `_grid_to_polydata`'s `grid = int(round(grid))` idiom at line 713), or reword the Fermat comment so it does not generalize a per-generator fact.

### MEDIUM — No new regression guard for the post-kernel generator integration seam

**Where:** `tests/test_numba_field_kernels.py` (new file); absent from `tests/test_mesh_generators.py`.
**Evidence:** The new test calls `_fermat_field_kernel` / `_enriques_fig1_field_kernel` directly against NumPy references — excellent for the transcription contract. But it never exercises `fermat_quartic()` / `enriques_figure_1()` *through* the kernel into `_marching_cubes_to_polydata`. The seam where the kernel-filled `F` array meets the contour helper (dtype, C-contiguity, the `np.empty` pre-allocation, the F-order ravel inside the helper) is only covered by the *pre-existing* `test_mesh_generators.py` tests, which were not touched this milestone.
**Why it matters:** A kernel that produces a correct field but, e.g., a non-C-contiguous or wrong-dtype array could pass the equivalence test (which compares values) yet break `_marching_cubes_to_polydata`. The e6 lesson flagged exactly this class — an array-layout bug that passes value-level smoke tests. The existing `test_enriques_figure_1_defaults` / `test_fermat_quartic_defaults` happen to catch it (verified: 365/365 pass), so this is a "no NEW guard pinning the e5 change" gap, not an uncovered hole.
**Suggested fix:** Add one assertion in the new test file that calls each generator at defaults and asserts `mesh.n_points > 0` and `isinstance(mesh, pv.PolyData)` — pins the kernel→helper seam to this milestone's test file. (If keeping the test pyvista-free per its docstring, instead note in the milestone artifacts that `test_mesh_generators.py` is the integration guard.)
**Regression-guard test:** `fermat_quartic()` and `enriques_figure_1()` at default params each return a `pv.PolyData` with `n_points > 0` (the kernel-filled `np.empty` array survives `_marching_cubes_to_polydata`).

### MEDIUM — `THREADING_LAYER` is a process-wide import side-effect with no guard

**Where:** `surfaces.py:29` — `numba.config.THREADING_LAYER = "workqueue"`.
**Evidence:** Importing `surfaces` unconditionally mutates a global Numba config field. There is no check for whether the host process (a future embedding, a notebook, a test harness importing surfaces after another Numba consumer) has already selected a layer, and no way to opt out.
**Why it matters:** Today `surfaces` is imported only by the app and the test suite, both of which want exactly this — so the mutation is benign. But "importing a module reconfigures a third-party library's global threading" is a non-obvious side-effect; if Numba is ever used elsewhere in-process with a different layer expectation, import order silently decides the winner. The placement (before `from numba import njit, prange`) is correct and spike-proven; the concern is the unconditional global write, not the timing.
**Suggested fix:** Acceptable as-is for a single-app codebase, but document the import side-effect in the comment block (it currently explains *why* `workqueue` and *when* it must be set, but not that this is a process-global write) or guard with a respect-existing-setting check. At minimum, record it in CONTEXT.md §8 as a known intentional side-effect.

---

## Low findings (cosmetic / future iteration)

### LOW — Numba disk cache location not documented in milestone artifacts

**Where:** `surfaces.py:208` (`@njit(parallel=True, cache=True)` on `_fermat_field_kernel`), `surfaces.py:243` (Enriques kernel).
**Evidence:** `cache=True` persists the compiled kernel to disk. With `NUMBA_CACHE_DIR` unset (verified), Numba writes the cache into `__pycache__/` adjacent to `surfaces.py`. `.gitignore` already lists `__pycache__/` (verified: `git status --ignored` shows `__pycache__/` ignored), so there is no repo-pollution risk.
**Why it matters:** No live risk — the cache is already gitignored. But the milestone artifacts do not state where the cache lands, so a future agent debugging "stale JIT after a kernel edit" has to rediscover it. (Numba invalidates the cache on source change via a content hash, so staleness is unlikely — worth noting too.)
**Suggested fix:** One line in CONTEXT.md or the implementation plan: cache lands in `__pycache__/` (gitignored), keyed by source hash, so a kernel edit auto-invalidates.

### LOW — Equivalence test cannot detect an axis-transposition bug (symmetric polynomials)

**Where:** `tests/test_numba_field_kernels.py:50-78` (`_FERMAT_POINTS`), `:91-105` (`_ENRIQUES_C`).
**Evidence:** Both Fermat (`x⁴+y⁴+z⁴ + α(x²y²+...) + ...`) and Enriques (`x²y²+x²z²+y²z² + ...`) are fully symmetric under any permutation of x,y,z. A kernel that mapped `i→z, k→x` instead of `i→x, k→z` would produce a field *identical* to the reference for every parameter point — the equivalence test would pass on a transposed kernel. An independent asymmetric probe (`g=[0,1,2]`, `α=β=γ=c=0` → `x⁴+y⁴+z⁴`) confirmed `out[1,0,0]=1.0`, `out[0,0,2]=16.0`, `out[2,1,0]=17.0` — the `i→x, j→y, k→z` mapping is correct. So no bug exists; the test merely cannot *guard* against the reintroduction of one.
**Why it matters:** Low — the kernel is correct and the symmetric polynomials make a transposition harmless to the rendered surface anyway (a symmetric field contours to the same isosurface regardless of axis labelling). The gap matters only if a future non-symmetric generator reuses this test pattern.
**Suggested fix:** Optionally add one asymmetric-probe assertion (the `g=[0,1,2]` check above) so the mapping is pinned; or note in the test docstring that axis-mapping correctness is delegated to the symmetric-polynomial argument.

### LOW — AI-1 / AI-6 reference docs not updated for the new compute dependency and kernel layer

**Where:** `.claude/references/app-invariants.md` (AI-1, AI-6), CONTEXT.md §3 / §4.
**Evidence:** `numba` is now a hard runtime dependency (`requirements.txt:5`) and the implicit-surface field-evaluation path has a new JIT-kernel layer between the generator and `_marching_cubes_to_polydata`. AI-1's anti-list and AI-6's pipeline description were not updated. The `surfaces.py:18-28` comment correctly argues numba is AI-1-clean (BSD-2-Clause, pure compute, no renderer), but that reasoning lives only in a code comment, not the institutional-memory contract.
**Why it matters:** Low — stale-docs slow poison. A future Challenger evaluating a candidate "add Numba for X" would not see from AI-1 that Numba is already a sanctioned, in-tree dependency.
**Suggested fix:** Add a one-line note to AI-1 (numba is an accepted pure-compute dependency — it is not a renderer) and to AI-6 (the two highest-cost implicit generators evaluate their field via `@njit` kernels; the pipeline contract downstream of the field array is unchanged).

---

## What was done well

- **Term-for-term transcription with a verbatim NumPy reference in the test.** `tests/test_numba_field_kernels.py:30-58` reproduces the *exact* pre-e5 NumPy field expressions as `_fermat_ref` / `_enriques_ref`, with an explicit "do NOT simplify these" warning. The test is genuinely independent of the post-e5 generator code — it imports only the kernels, never the generators. This is the correct way to pin an equivalence contract.
- **Identical operator order preserved.** The kernels keep the exact IEEE-754 op sequence of the former NumPy expressions (`x2*x2 + y2*y2 + z2*z2 + alpha*(...) + beta*(x*y*z)*(x+y+z) + ...`). Per-voxel evaluation is near-bit-exact; the `rtol=atol=1e-9` tolerance is well-calibrated — loose enough for arm-vs-x86 ULP drift, tight enough that a dropped term or wrong sign (orders-of-magnitude shift) fails loudly.
- **`np.clip` correctly folded as scalar min/max.** The `if val < -200.0: val = -200.0 elif val > 200.0: val = 200.0` form is exactly equivalent to `np.clip(F, -200.0, 200.0)` and the `respects_clip_bounds` tests pin it directly at the slider extremes.
- **`parallel=True` soundness is correctly reasoned.** The comment at `surfaces.py:200-203` correctly notes every `out[i,j,k]` write is independent (no cross-iteration reduction), so `prange` parallel execution is bit-identical to serial — there is genuinely no summation-order risk here, unlike a parallel reduction.
- **`THREADING_LAYER` placement is correct and spike-grounded.** `numba.config.THREADING_LAYER = "workqueue"` is set *before* `from numba import njit, prange`, and the `# noqa: E402` is correctly applied to the deferred import. The `workqueue` choice (dependency-free, isolates Numba's pool from VTK's SMP pool) is justified against the e4 worker contention concern and cites spike §6.
- **JIT-latency honesty.** The comment at `surfaces.py:204-208` is honest that the first cold-cache render pays ~400-800 ms compile, explains it runs inside the e4 background worker (off the GUI thread), and explicitly declines an eager startup warm-up per the spike. No overclaiming.
- **AI-6 respected — the pipeline contract is untouched.** The kernels only change *how* the `F` array is built; both generators still call `_marching_cubes_to_polydata(F, bounds)` exactly as before. The `_marching_cubes_to_polydata` zero-crossing pre-check, Flying Edges contour, Taubin smoothing, and the e6 F-order ravel are all unchanged — no pipeline mixing.
- **Zero-crossing sanity test.** `test_kernels_have_a_zero_crossing_at_defaults` asserts each default-parameter field straddles 0, confirming the kernels feed a non-degenerate field and the AI-14 `ValueError` guard in `_marching_cubes_to_polydata` is not spuriously tripped.
- **Dependency pin is correct and spike-verified.** `numba>=0.65,<0.66` reflects the spike's finding that the roadmap's stale `0.60,<0.62` pin is incompatible with numpy 2.4.x; numba 0.65.1 is verified against the installed numpy with no downgrade (confirmed: `numba 0.65.1` imports cleanly in the venv).
- **Test grid kept small (`_N = 32`).** Keeps the JIT-warm equivalence test fast (0.83 s for 9 tests) while still exercising all three parameter regimes per generator including the clip caps.

---

## Recommended rectification order

1. **Fix the two MEDIUMs together (one `surfaces.py` edit + one test edit).** Either add `n = int(round(n))` to `enriques_figure_1` (MEDIUM #1 — makes the Fermat comment's AI-8 claim true for both generators) or reword the comment; and add the integration-seam assertion (MEDIUM #2) pinning `fermat_quartic()` / `enriques_figure_1()` → non-empty `pv.PolyData`. Both are small, both close this milestone's test/doc debt.
2. **Document the `THREADING_LAYER` import side-effect (MEDIUM #3).** Comment expansion or CONTEXT.md §8 entry — no code behavior change needed.
3. **Batch the doc LOWs.** AI-1/AI-6 reference-doc updates and the Numba-cache-location note are one editing pass over `.claude/references/app-invariants.md` + CONTEXT.md.
4. **The axis-probe LOW is optional** — the kernel is verified correct; add the asymmetric probe only if cheap.

---

*End of critique. Mandatory rectification: all CRITICALs and HIGHs — here, only the non-waivable diff-size auto-HIGH, which needs no code action. The three MEDIUMs are strongly recommended before milestone close.*

---

## Rectification status (filled in Phase 4)

- **Commit:** (rectification commit — see `git log`, subject `rect(realtime-variety-render-e5): ...`)
- **Fixed:** all 7 findings closed (1 HIGH acknowledged, 3 MEDIUM, 3 LOW).
  - **H1** — diff-size auto-finding: acknowledged, no code action. The diff is artifact-inflated (~496 of 885 lines are `.claude/notes` pipeline artifacts); the production+test surface is ~281 LOC and was reviewed end-to-end.
  - **M1** — inaccurate `n`-coercion claim: added `n = int(round(n))` to `enriques_figure_1` (mirrors `_grid_to_polydata`'s idiom), so the AI-8 in-generator int-coercion now holds for both kernel-backed generators. Verified `enriques_figure_1(n=240.0)` no longer reaches `np.linspace` as a float.
  - **M2** — no NEW integration-seam guard: added `test_numba_kernel_generators_round_trip` to `tests/test_mesh_generators.py` — calls `fermat_quartic()` / `enriques_figure_1()` at default and non-default params, asserting the kernel-filled array round-trips through `_marching_cubes_to_polydata` to a non-empty PolyData.
  - **M3** — `THREADING_LAYER` process-global side-effect: expanded the `surfaces.py` import-block comment to flag it explicitly as a process-wide write, and documented it in CONTEXT.md §3.
  - **L1** — Numba cache location: documented in CONTEXT.md §3 (`__pycache__/`, gitignored, source-hash-keyed → auto-invalidated).
  - **L2** — axis-transposition test gap: added an axis-mapping note to `test_numba_field_kernels.py`'s module docstring — explains that for fully-symmetric fields a transposed kernel is bit-identical to the reference *and harmless* (same isosurface), so axis-order correctness is delegated to the symmetry argument rather than a (useless) assertion.
  - **L3** — reference docs: AI-1 now states compute dependencies (numba) are not AI-1 conflicts; AI-6 notes the field-array computation is an implementation detail and records the e5 kernel swap. Also corrected a stale `§8.15`→`§8.17` reference in AI-6 (a merge-renumber artifact in the edited line).
- **Invalidated on re-verification:** none (all findings confirmed present).
- **Deferred to next milestone:** none.
- **Test additions:** `tests/test_mesh_generators.py::test_numba_kernel_generators_round_trip`. Full suite green: 366 passed.
- **Note:** the Phase 2 off-screen renders remain valid — the rectification only added an int-coercion no-op (`int(round(240))`), a test, and docs; no field math or render-path change.
