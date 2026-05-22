# Adversary critique — VTK Flying Edges marching-cubes replacement

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** realtime-variety-render-e6 / commit range `42b6c17..864337f`

> Format reference: `.claude/references/critique-format.md`.

**Diff stats:** 1 commit, 9 files, +619 / −27. Source+test surface (the only LOC that matters for review-quality): `surfaces.py` + `tests/test_mesh_generators.py` = 192 LOC. Remaining ~555 LOC are `.claude/notes` pipeline artifacts (research briefs, state.json, dispatch log).

---

## Executive summary

- The core swap is sound: `skimage.measure.marching_cubes` → `pv.ImageData(...).contour(method='flying_edges')` is mathematically equivalent, the Fortran-order ravel correctly handles the `indexing="ij"` ↔ VTK i-fastest mismatch, and Hanson stays untouched (AI-6 respected). [context]
- **[MEDIUM]** The AI-14 `ValueError`-on-empty-field contract has a narrow hole: a field where `field.min() == field.max() == level` passes the strict-inequality guard but Flying Edges returns a 0-point PolyData that is then returned silently — verified empirically. The old skimage path raised. Behavior regression.
- **[MEDIUM]** `scikit-image` is now a fully unused dependency. The commit message claims it "stays in requirements.txt for transitive use" — verified false: no `.py` file imports it and it is not in pyvista's dependency tree.
- **[MEDIUM]** Docstring claims Flying Edges is "~7-10× faster"; the commit message's own measured number is 3.0–4.0× (298ms→98ms = 3.04×). Internal contradiction in load-bearing documentation.
- **[LOW]** No CONTEXT.md §8 entry for the `clean()`-collapses-to-degenerate-cells / orientation-island shading bug — this is exactly the load-bearing "pitfall fixed mid-build" class §8 exists to record.
- **[LOW]** AI-6 anchor text in `adversary-critique-checklist.md` and CONTEXT.md §4.2 still describe the helper's pipeline as including `clean()`; now stale.
- No CRITICALs. No HIGHs. The 33 mesh-generator + empty-field tests pass; the new winding guards are well-constructed and genuinely encode the regression.
- **Verdict: SHIP-WITH-FIXES** — the two MEDIUM correctness/accuracy items should close before milestone close; LOWs are optional.

---

## Verdict

**SHIP-WITH-FIXES.** The Flying Edges replacement is correct, the axis-order subtlety is handled and explicitly documented, and the `clean()` removal is well-reasoned and test-guarded. The only correctness item is a narrow AI-14 edge case (uniform field → silent empty mesh) that no real generator triggers but which the old code handled by raising; the rest are documentation-accuracy fixes. Nothing blocks ship.

---

## Critical findings (must-fix before this can ship)

None.

---

## High findings (should-fix this iteration)

None.

---

## Medium findings (nice-to-fix)

### MEDIUM — Uniform field bypasses the AI-14 ValueError guard and returns an empty PolyData

**Where:** `surfaces.py:127-152`
**Evidence:** The guard is `if field.min() > level or field.max() < level: raise ValueError(...)`. Both comparisons are strict, so a field with `field.min() == field.max() == level` (e.g. an all-zero field with `level=0.0`) passes the guard. `grid.contour([level], method="flying_edges")` then returns a 0-point PolyData, which is returned unchanged (the `mesh.n_points > 0` checks skip smoothing and normals but do not raise). Verified empirically: `_marching_cubes_to_polydata(np.zeros((10,10,10)), bounds=1.0)` returns `PolyData` with `n_points == 0`. The old `skimage.measure.marching_cubes` path raised an internal error on a degenerate/no-crossing field — so this is a behavior regression from "crash with traceback" to "silent empty mesh".
**Why it matters:** AI-14 requires implicit generators return a `pv.PolyData` *or* raise `ValueError`; an empty PolyData with 0 points is technically a PolyData but is not a real zero set, and `MainWindow._render_current` would `add_mesh` an empty actor with no status-bar message — a silent blank viewport rather than the intended "No real zero set" status line. No current generator produces an exactly-uniform field, so user impact is near-zero today, but the contract hole is real.
**Suggested fix:** After the `contour` call, add `if mesh.n_points == 0: raise ValueError("No real zero set ...")` reusing the same message, OR widen the pre-check to also catch the zero-width-range case. One line.
**Regression-guard test:** `test_marching_cubes_empty.py` — assert `_marching_cubes_to_polydata(np.zeros((10,10,10)), bounds=1.0)` raises `ValueError` matching `"No real zero set"`.

### MEDIUM — scikit-image is now an unused dependency; commit message claim is false

**Where:** `requirements.txt:5` (`scikit-image>=0.22,<0.27`); commit `864337f` message
**Evidence:** The commit message states "scikit-image stays in requirements.txt for transitive use." Verified false: `git grep "import skimage|from skimage"` over all `*.py` returns nothing (the only two remaining `skimage` mentions in `surfaces.py:110,134` are docstring/comment prose), and `importlib.metadata.requires('pyvista')` contains no `scikit-image` / `scikit_image` entry — pyvista depends on `vtk`, not skimage. After this diff scikit-image is a fully orphaned direct dependency.
**Why it matters:** A stale dependency inflates install footprint and the supply-chain surface, and the false "transitive use" justification will mislead the next maintainer into keeping it. The milestone's own commit body advertises a "zero new dependencies" win while leaving a now-dead one in place.
**Suggested fix:** Either drop the `scikit-image` line from `requirements.txt`, or — if intentionally retained for some out-of-tree reason — correct the commit/CONTEXT note to say so honestly. Recommend dropping it.

### MEDIUM — Docstring speedup figure (7-10×) contradicts the commit's measured 3-4×

**Where:** `surfaces.py:99` ("~7-10× faster on the marching-cubes step at production resolutions")
**Evidence:** The docstring claims "~7-10× faster". The same commit's message reports "Measured 3.0-4.0x faster on the isocontour step (n=240: 298ms -> 98ms)" — and 298/98 = 3.04×. The docstring and the commit's own benchmark disagree by ~2-3×.
**Why it matters:** The docstring is the durable artifact a future maintainer reads; an unsupported 7-10× claim will be cited downstream as fact. AI-15-adjacent honesty discipline — load-bearing performance claims must match the measurement.
**Suggested fix:** Replace "~7-10×" with the measured "~3-4× (n=240, 298ms→98ms)", matching the commit message, or cite the specific resolution at which 7-10× was observed if such a measurement exists.

---

## Low findings (cosmetic / future iteration)

### LOW — No CONTEXT.md §8 entry for the clean()-degenerate-cell shading bug

**Where:** CONTEXT.md §8 (not present in diff)
**Evidence:** The diff fixes a real, subtle, load-bearing bug — `clean()` collapsing near-coincident vertices into zero-area degenerate cells that `vtkPolyDataNormals`' orientation walk cannot cross, splitting the Enriques sextic into inside-out shading islands. This is documented thoroughly in the docstring (`surfaces.py:110-119`) and the test docstring but not in CONTEXT.md §8, the canonical "bugs caught and fixed" registry.
**Why it matters:** §8 is the institutional-memory contract; a future agent considering re-adding `clean()` for vertex-merge hygiene would not find this warning where they would look for it. Per the checklist Axis 9 anchor, every load-bearing fix needs a §8 callout.
**Suggested fix:** Add a §8.N entry: "Flying Edges + clean() → degenerate cells → orientation islands; clean() removed in realtime-variety-render-e6."

### LOW — Stale AI-6 pipeline description: helper no longer runs clean()

**Where:** `.claude/references/milestone-pipeline/adversary-critique-checklist.md:58-64`; `.claude/references/app-invariants.md:73` (AI-6); CONTEXT.md §4.2
**Evidence:** AI-6's text and the Axis 2 anchor both describe `_marching_cubes_to_polydata`'s pipeline as `marching_cubes → mesh.clean() → smooth_taubin → compute_normals`. After this diff the `clean()` step is gone and `skimage.measure.marching_cubes` is replaced by `vtkFlyingEdges3D`. These reference docs now misdescribe the helper.
**Why it matters:** Documentation drift — future critics walking the checklist would flag a *correct* absence of `clean()` as a regression, or expect a skimage call that no longer exists. Slow poison per Axis 9.
**Suggested fix:** Update the AI-6 entry and the Axis 2 anchor to describe the Flying Edges pipeline (`contour(flying_edges) → smooth_taubin → compute_normals`, no clean()).

---

## What was done well

- **Fortran-order ravel correctly bridges the axis-order mismatch.** `field.ravel(order="F")` is exactly right: the field is built with `np.meshgrid(..., indexing="ij")` (x = slowest NumPy axis) while VTK `ImageData` stores i (=x) as fastest-varying. The inline comment (`surfaces.py:133-139`) explicitly calls out that a C-order ravel would silently transpose x↔z and *still pass the non-empty/bounds smoke tests* — a genuinely subtle trap, documented at the call site where the next maintainer needs it.
- **`origin=(-bounds, -bounds, -bounds)` cleanly replaces the old `verts -= bounds`.** Folding the coordinate offset into `ImageData` construction is the idiomatic VTK approach and removes a manual post-processing step.
- **The `clean()` removal is reasoned, not cargo-culted.** The docstring explains the precise failure mechanism (degenerate cells block the orientation walk → inside-out shading) and notes it was verified by off-screen MC-vs-FE comparison on the Enriques sextic — directly addressing the milestone-adversary memory lesson that topology/shading claims must be verified on the actual figure.
- **The winding-consistency guard is mathematically correct and well-encoded.** `_assert_consistent_winding` (`test_mesh_generators.py:53`) checks the right invariant: on a consistently wound closed surface every directed edge `(a,b)` appears at most once. The `n_points+1` radix packing of edge pairs into int64 keys is a correct, allocation-light way to detect duplicate directed edges.
- **Regression tests target the right surfaces.** The Enriques canonical sextic (the actual e6 regression case), Kummer (16 nodes, high curvature — most stress on the contour), and Fermat quartic give three distinct topology classes rather than three trivial variations.
- **AI-3 respected.** Verification was done via off-screen MC-vs-FE comparison (per the commit message); no `MainWindow()` construction under offscreen anywhere in the diff.
- **AI-6 respected.** The change is scoped strictly to the implicit `_marching_cubes_to_polydata` helper; the parametric Hanson path (`_grid_to_polydata`/`_concat_polydata`) is untouched, and the commit message states this explicitly.
- **AI-14 guard rationale is documented.** The comment at `surfaces.py:123-126` explains *why* the explicit pre-check is still needed (Flying Edges returns an empty mesh rather than erroring) — correct reasoning, even though it has the uniform-field hole flagged above.
- **The `mesh.n_points > 0` guards on smoothing and normals correctly tolerate tiny/empty meshes** without crashing — verified on a near-degenerate single-cell field that produced a 6-point mesh.

---

## Recommended rectification order

1. **No CRITICALs or HIGHs** — nothing blocks ship.
2. **Batch the two MEDIUM correctness/accuracy items in `surfaces.py`:** add the `mesh.n_points == 0` → `ValueError` guard after `contour` (closes the AI-14 hole) and correct the "7-10×" docstring figure to the measured "~3-4×". Both are in the same function; one commit, plus the new `test_marching_cubes_empty.py` assertion.
3. **Decide scikit-image:** drop the `requirements.txt:5` line (recommended) or correct the false "transitive use" claim. Trivial, do alongside step 2.
4. **LOWs are optional follow-ups:** add the CONTEXT.md §8 entry and refresh the stale AI-6 / Axis 2 pipeline descriptions. Worth doing before milestone close so the reference docs stay accurate, but not blocking.

---

*End of critique. Mandatory rectification: all CRITICALs and HIGHs (none). The two MEDIUM items are strongly recommended before milestone close; LOWs at maintainer discretion.*

---

## Rectification status (filled in Phase 4)

- **Commit:** (rectification commit — see `git log`, subject `rect(realtime-variety-render-e6): ...`)
- **Fixed:** M1, M2, M3, L1, L2 — all findings closed.
  - **M1** — uniform-field AI-14 hole: added `if mesh.n_points == 0: raise ValueError(...)` after the contour call (`surfaces.py`); regression test `test_uniform_field_at_level_raises` in `tests/test_marching_cubes_empty.py`.
  - **M2** — orphaned dependency: dropped `scikit-image` from `requirements.txt`.
  - **M3** — docstring speedup: `~7-10×` → measured `~3-4× (n=240, 298 ms→98 ms)` (`surfaces.py`).
  - **L1** — added CONTEXT.md §8.15 documenting the `clean()`-degenerate-cell shading bug.
  - **L2** — refreshed stale pipeline descriptions: CONTEXT.md §3/§4.2/§8.6, `app-invariants.md` AI-6/AI-14, `adversary-critique-checklist.md` Axis 2 anchor.
- **Invalidated on re-verification:** none.
- **Deferred to next milestone:** none — both LOWs were doc-accuracy fixes the critique itself recommended before milestone close, so they were closed here rather than deferred.
- **Test additions:** `tests/test_marching_cubes_empty.py::test_uniform_field_at_level_raises`. Full suite green: 333 passed.
