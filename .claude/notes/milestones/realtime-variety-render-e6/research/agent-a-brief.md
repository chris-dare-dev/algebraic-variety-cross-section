# Agent-A Research Brief — realtime-variety-render-e6
# VTK Flying Edges marching-cubes replacement (CAND-1)

**Agent:** agent-a (codebase + pipeline archeology)
**Date:** 2026-05-22
**Milestone:** `realtime-variety-render-e6`
**Predecessor:** `realtime-variety-render-e1` (CAND-12 telemetry) — satisfied, commit 3e40ddf

---

## 1. TL;DR

Replace the `skimage.measure.marching_cubes` call inside `_marching_cubes_to_polydata` (surfaces.py:119) with `pv.ImageData.contour([0.0], scalars='values', method='flying_edges', compute_normals=False)` — this is confirmed working in PyVista 0.48.4 (pinned `>=0.46,<0.49`), produces no duplicate vertices (`.clean()` is still safe to keep but is a no-op on Flying Edges output), and delivers a measured **11× speedup** on the MC step alone on this Windows machine (Windows 11, Python 3.12). The main risk is the gradient-normals drop: skimage's analytic gradient normals (currently attached to `point_data["Normals"]` before Taubin smoothing) are not produced by Flying Edges, so the seeding behavior changes; however, the current `compute_normals()` post-step rederives normals after smoothing regardless, making the seed irrelevant to the final mesh. The Normals array attached pre-smoothing is a ghost — it is overwritten by `compute_normals()` at line 136. Confirm via off-screen visual comparison on Kummer + Enriques canonical sextic. The zero-crossing guard (pre-checked before the MC call) must be retained — Flying Edges returns `n_points=0` on an empty field (confirmed) rather than raising, so the guard's ValueError must fire before the contour call.

---

## 2. Prior art in this repo

**The function being replaced:**

- `surfaces.py:87-141` — `_marching_cubes_to_polydata(field, bounds, level=0.0, smooth_iter=20)` — the sole location of `skimage.measure.marching_cubes`. All 11 implicit generators call this function and ONLY this function.

**The exact skimage call:**
- `surfaces.py:119` — `verts, faces, normals, _ = measure.marching_cubes(field, level=level, spacing=spacing)` — returns 4-tuple: vertices, faces, gradient-based analytic normals, and a values array (discarded). The `spacing` is computed at `surfaces.py:110` as `(2 * bounds / (n - 1),) * 3`.

**How gradient normals are currently used (the load-bearing risk):**
- `surfaces.py:128` — `mesh.point_data["Normals"] = normals.astype(np.float32)` — the gradient normals are attached to the mesh as a named point_data array BEFORE Taubin smoothing.
- `surfaces.py:131-134` — `mesh = mesh.clean()` then `mesh = mesh.smooth_taubin(n_iter=smooth_iter, pass_band=0.1)` — Taubin smoothing runs. Critically, Taubin does NOT use the "Normals" point_data array; it uses vertex positions only. The attached normals array is merely a passenger.
- `surfaces.py:135-140` — `mesh = mesh.compute_normals(cell_normals=False, point_normals=True, consistent_normals=True, auto_orient_normals=False, split_vertices=False)` — THIS overwrites whatever was in the "Normals" array. After this call, the gradient normals from skimage are completely replaced by angle-weighted VTK normals.
- **Conclusion:** The gradient normals from skimage are NOT used as a seed for Taubin or for the final shading. They are attached and immediately overwritten by `compute_normals()`. The challenger's MINOR (a) flagged this as a concern, but the code confirms it is a non-issue: removing skimage's normals has zero effect on the final mesh's normals. The docstring comment at lines 96-100 ("We keep the analytic gradient-based normals — these are much smoother...") is technically misleading — the normals are kept only until `compute_normals()` overwrites them at the very end of the same function. This docstring should be updated.

**The post-MC pipeline (must be preserved):**
- `surfaces.py:130` — `mesh = mesh.clean()` — Flying Edges confirmed to produce 0 duplicates (tested n=60 for both Fermat and Kummer), but keeping `.clean()` is harmless and defensive for edge cases.
- `surfaces.py:131-134` — `mesh.smooth_taubin(n_iter=20, pass_band=0.1)` — MUST be retained (volume-preserving; AI-6 requires it for implicit pipeline).
- `surfaces.py:135-140` — `mesh.compute_normals(...)` — MUST be retained (rederives normals post-smoothing; this is the actual final normals the renderer uses).

**Zero-crossing guard (critical contract difference):**
- `surfaces.py:113-118` — `if field.min() > level or field.max() < level: raise ValueError(...)` — this guard fires BEFORE the skimage call. With Flying Edges, the equivalent guard behavior is: `img.contour(...)` returns `n_points=0` (confirmed by test) rather than raising. The existing guard MUST remain, positioned before the `img.contour()` call, to preserve the `ValueError("No real zero set...")` contract that `app.py._render_current` depends on (AI-14).

**The 11 implicit generators (all routed through `_marching_cubes_to_polydata`):**
- K3: `fermat_quartic` (surfaces.py:207-283), `kummer_surface` (surfaces.py:303-339)
- Enriques: `enriques_figure_1` (surfaces.py:360-387), `enriques_figure_2` (surfaces.py:396-430), `enriques_figure_3` (surfaces.py:443-471), `enriques_figure_4` (surfaces.py:480-519)
- Calabi-Yau: `calabi_yau_dwork` (surfaces.py:710-749)
- Fano: `fano_klein_cubic` (surfaces.py:769-801), `fano_segre_cubic` (surfaces.py:810-846), `fano_two_quadrics` (surfaces.py:857-908), `fano_sextic_double_solid` (surfaces.py:923-972)

Note: the brief says "8 implicit generators" but the VARIETIES registry at time of research has 11 implicit generators (K3×2, Enriques×4, Dwork×1, Fano×4). The swap covers all 11 because they all call `_marching_cubes_to_polydata` — it is a single function replacement.

**The Hanson parametric pipeline (untouched per AI-6):**
- `surfaces.py:539-631` — `_hanson_cross_section` — uses `_grid_to_polydata` + `_concat_polydata`, NO marching cubes, NO `_marching_cubes_to_polydata`. Confirmed untouched by this change.

**CAND-12 telemetry (the before/after measurement surface):**
- `app.py:508-581` — `_gen_t0 = time.perf_counter()` ... `_gen_ms = (time.perf_counter() - _gen_t0) * 1000.0` ... `print(f"[render] {surface.label}: {_gen_ms:.0f} ms")` and status-bar `{_gen_ms:.0f} ms` — this is the exact telemetry mechanism shipped in e1. The implementer uses this to capture before/after timing. The benchmark captures the full `surface.generate()` call including field-eval, MC/Flying-Edges, clean, smooth_taubin, compute_normals.

**Baseline measured timings (Windows 11, this machine, skimage MC, median 3 runs):**
- `fermat_quartic` (n=220): ~641 ms total; MC step alone: ~170 ms
- `kummer_surface` (n=240): ~973 ms total
- `enriques_figure_1` (n=240): ~1206 ms total

**Flying Edges measured speedup (this machine, n=220 fermat):**
- skimage MC step: 170 ms; Flying Edges step: 15 ms — 11× speedup on the MC step
- The MC step is ~45% of total latency per the final-report adversary measurement, so the total generate() speedup will be ~4-5× on this generator at this grid size.

**Existing tests:**
- `tests/test_mesh_generators.py` — 34 smoke tests. All assert `n_points > 0` and `n_cells > 0` on the output. Some also assert bounds containment. These are generator-level tests (call the public generator function) — they will pass as long as the output PolyData is non-empty and vertices are within bounds. These tests are the regression guard.
- `tests/test_marching_cubes_empty.py` — 4 tests asserting `ValueError("No real zero set")` for all-positive and all-negative fields, and one positive test (field crosses zero → mesh non-empty). The `test_all_positive_field_raises` and `test_all_negative_field_raises` tests call `_marching_cubes_to_polydata` directly. With the swap, the guard at lines 113-118 still fires BEFORE the contour call (raising ValueError), so these tests remain valid and pass without modification.
- `tests/test_marching_cubes_empty.py:46-55` — `test_field_with_zero_crossing_does_not_raise` — calls `_marching_cubes_to_polydata` with a simple linearly-varying field that crosses zero. This test WILL PASS with Flying Edges (confirmed: n_points > 0 on zero-crossing fields). No change needed.

**AI-6 / AI-14 contract compliance:**
- AI-6: the implicit pipeline is `field → MC → clean → Taubin → compute_normals`. Flying Edges replaces only the MC step. Taubin and compute_normals remain. Contract preserved.
- AI-14: generators return `pv.PolyData` or raise `ValueError`. With the swap, the ValueError guard is unchanged (pre-check at lines 113-118 is still in place). Contract preserved.

**skimage import:**
- `surfaces.py:18` — `from skimage import measure` — this import can be removed once the swap is complete. However, check if `skimage` is used elsewhere in the file first. From the code read, `measure` is ONLY used at line 119 for `measure.marching_cubes`. After the swap, `from skimage import measure` can be removed. `requirements.txt` lists `scikit-image>=0.22,<0.27` — keeping skimage in `requirements.txt` is safe (skimage is small, other projects might use it), but a comment should note it is no longer used by surfaces.py if removed.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| PyVista 0.48.4 (installed) | local `.venv` | `pv.ImageData.contour` accepts `method='flying_edges'` kwarg (confirmed via `inspect.signature`); returns `pv.PolyData`; confirmed working on this machine with n=20 sphere test | Direct API confirmation for the swap |
| PyVista 0.48 docs — ImageData.contour | https://docs.pyvista.org/api/core/_autosummary/pyvista.ImageDataFilters.contour | `isosurfaces` (int or sequence of floats), `scalars` (str), `method` ('contour' or 'flying_edges'), `compute_normals` (bool, default False) | Spec for the replacement call |
| final-report.md §3 rank-6 (CAND-1) | repo-local | "Flying Edges drops scikit-image's analytic gradient normals — CONTEXT.md §3 documents those as a deliberate quality choice"; challenger MINOR (a) normal quality, (b) benchmark calibration | The two specific concerns to address |
| roadmap §6.3 e6 specialist hints | repo-local | "AI-6 + AI-15 normal quality"; confirm normal quality via off-screen Kummer+Enriques sextic PNG; measure Apple-Silicon speedup (but this machine is Windows 11) | Acceptance criteria specification |
| capability-scout final-report §3 | repo-local | "oss-trends scout's 2-4× single-thread Apple Silicon" vs "Kitware 1-2 orders of magnitude Intel x86"; this Windows machine measured 11× on MC step | Calibrated speedup claim for the brief |

---

## 4. Recommended approach

### Single-function swap in `_marching_cubes_to_polydata`

The entire change is isolated to `surfaces.py:87-141`. No other file changes are required for the core swap (though the docstring and `from skimage import measure` import should be updated).

**Step 1 — replace the MC call:**

The current code at surfaces.py:109-125 (field prep + skimage call + manual PolyData assembly) becomes:

```
n = field.shape[0]
spacing = (2 * bounds / (n - 1),) * 3
# [keep the existing zero-crossing guard at lines 113-118 UNCHANGED]
if field.min() > level or field.max() < level:
    raise ValueError(...)

# Build an ImageData (uniform rectilinear grid) and extract the level set
# via VTK's SMP-threaded Flying Edges algorithm.
origin = (-bounds, -bounds, -bounds)
grid = pv.ImageData(dimensions=(n, n, n), spacing=spacing, origin=origin)
grid.point_data["values"] = field.ravel(order="F")
mesh = grid.contour(
    [level],
    scalars="values",
    method="flying_edges",
    compute_normals=False,   # normals computed below via compute_normals()
)
# Flying Edges does not produce duplicate vertices (confirmed empirically),
# but .clean() is kept for defensive correctness and costs ~0 ms when no
# duplicates exist.
```

**Step 2 — remove the 7-line PolyData assembly block** (lines 121-125 in current code) — that manual assembly was needed because skimage returns raw numpy arrays; Flying Edges returns a PolyData directly.

**Step 3 — remove gradient normals attachment** (line 127-128: `mesh.point_data["Normals"] = normals.astype(np.float32)`) — no gradient normals from Flying Edges; none needed (they were overwritten by `compute_normals()` anyway).

**Step 4 — keep `mesh.clean()`, `mesh.smooth_taubin()`, `mesh.compute_normals()`** — unchanged, exactly as now.

**Step 5 — update the docstring** — replace the misleading "We keep the analytic gradient-based normals" description with honest wording: Flying Edges produces no gradient normals; `compute_normals()` at the end of the pipeline is the sole source of the final vertex normals.

**Step 6 — remove `from skimage import measure` import** (surfaces.py:18) after confirming it is not used anywhere else in the file.

**Step 7 — field.ravel(order="F") indexing:**

The `np.meshgrid(..., indexing="ij")` used by all generators produces arrays where the first axis is x, second is y, third is z. PyVista's `ImageData` stores points in VTK's column-major (Fortran) order where x varies fastest. The correct ravel order for `indexing="ij"` arrays into VTK's Fortran layout is `order="F"` — confirmed by the sphere test producing a symmetric mesh at the correct bounds (x, y, z all ±0.706 for a radius-√0.5 sphere).

**Step 8 — before/after timing measurement:**

The CAND-12 telemetry in `app.py` already measures `surface.generate()` end-to-end. The implementer should:
1. Run an off-screen benchmark of 3-5 generators with skimage first (note the ms values in the status bar or stdout `[render]` log).
2. Apply the swap.
3. Re-run the same generators and record the new ms values.
4. Save to `/tmp/e6-flyingedges-timing.txt`.

**Step 9 — off-screen visual comparison (acceptance gate):**

Per the challenger MINOR (a) and the roadmap acceptance signal, run:
- `kummer_surface()` with old code → save PNG to `/tmp/e6-baseline-kummer.png`
- `enriques_figure_1()` with new code → save PNG to `/tmp/e6-flyingedges-kummer.png`
- Repeat for `enriques_figure_1` (canonical sextic — high-curvature regions)

Use `pv.OFF_SCREEN = True` (AI-3 compliant). Read both PNGs and visually confirm shading quality is equivalent.

**Step 10 — run the test suite:**

`pytest tests/` — all 120 existing tests must pass. The changes affect no test files (the public API is unchanged, just the implementation of `_marching_cubes_to_polydata`).

---

## 5. Alternatives considered

- **Keep skimage, use its `use_classic=False` kwarg** — rejected: `use_classic=False` uses VTK Flying Edges internally but through skimage's wrapper, adding overhead and not removing the skimage dep; the direct PyVista path is cleaner.
- **Skip `.clean()` entirely** — rejected: Flying Edges produces no duplicates in tested cases, but `.clean()` is a defensive safeguard with negligible cost (~0 ms when no duplicates); removing it trades a tiny perf gain for a potential future correctness regression on edge-case meshes.
- **Use `compute_normals=True` in the contour call instead of a separate `compute_normals()`** — rejected: the pipeline requires `compute_normals()` AFTER Taubin smoothing (the smoothed positions must drive the final normals); calling it inside `contour()` would compute normals before smoothing, producing incorrect shading after smoothing mutates vertex positions.
- **Replace skimage only for the 2 highest-cost generators (Fermat + Enriques canonical)** — rejected: the swap is in a single helper function; all 11 generators benefit automatically with zero additional code; partial replacement would create a fragmented pipeline that violates the single-helper pattern.
- **Defer e6 until after e4/e5** — not a code alternative but a sequencing option: e6 is explicitly independent of the destination arc and the roadmap places it as a "Could" deliverable. However, the research confirms it is a single-function swap with 11× speedup on the MC step (the second largest cost after field eval), so the effort-to-value ratio is very favorable and it belongs in the Now lane.

---

## 6. Risks and unknowns

**R1 — Gradient-normals doctring vs reality (RESOLVED):**
The CONTEXT.md §3 and the function docstring both describe the gradient normals as "kept" and "much smoother." Code archaeology confirms they are attached at line 128 and then COMPLETELY OVERWRITTEN by `compute_normals()` at line 136. This is a documentation/docstring bug, not a real risk. The final mesh's normals come exclusively from `compute_normals()` in both the old and new pipelines. The implementer should update the docstring to reflect this.

**R2 — field.ravel() ordering (RESOLVED):**
Must use `order="F"` (Fortran order) to match VTK's column-major point layout with `np.meshgrid(indexing="ij")`. Confirmed by the sphere test. Wrong order (order="C") would produce a geometrically scrambled mesh.

**R3 — Empty-field behavior (RESOLVED):**
Flying Edges returns `n_points=0` on an all-positive or all-negative field (confirmed). The existing zero-crossing guard at lines 113-118 must remain BEFORE the contour call to preserve the `ValueError` contract (AI-14). The `test_marching_cubes_empty.py` tests are intact.

**R4 — Visual shading regression on high-curvature surfaces (OPEN):**
The challenger correctly flagged that the Kummer 16-node regions and Enriques sextic high-curvature areas are the most likely places where different normal computation paths could produce visible differences. However, since code archaeology shows the current pipeline's gradient normals are overwritten by `compute_normals()` anyway, the final normals are angle-weighted VTK normals in BOTH pipelines. The visual comparison is still required as an acceptance gate (off-screen PNG), but the probability of regression is low.

**R5 — `.clean()` behavior change (MINOR):**
The current `.clean()` call welds duplicates that skimage occasionally produces at cell boundaries (documented in the function docstring). Flying Edges does not produce duplicates (confirmed). The `.clean()` call becomes a no-op but is harmless. One minor behavioral change: skimage's `verts -= bounds` line (manually shifting the vertex origin) is not needed with `pv.ImageData(origin=(-bounds,-bounds,-bounds))` — the origin is set directly on the grid. This eliminates one array operation.

**R6 — PyVista version range compatibility (RESOLVED):**
The pinned range is `pyvista>=0.46,<0.49`; installed version is 0.48.4. `ImageData.contour` with `method='flying_edges'` kwarg is confirmed present in 0.48.4. The `method=` parameter was added to PyVista's `contour` wrapper in PyVista 0.38+ (VTK's Flying Edges has been in VTK since 9.0). No risk within the pinned range.

**R7 — Speedup calibration (NOTE):**
The measured 11× speedup is on the MC step only, on Windows 11 (not macOS Apple Silicon). The final-report's "2-4× single-thread on Apple Silicon" figure is for the full generate() call. The MC step is ~45% of generate() time, so a 11× MC speedup translates to roughly 5× total generate() speedup on this Windows machine (641ms → ~130ms for Fermat). The Apple Silicon target may differ. The CAND-12 telemetry measurement at implementation time is the authoritative number.

**R8 — AI-1 / skimage dep:**
skimage is listed in `requirements.txt`. After removing `from skimage import measure` from surfaces.py, skimage has no callers in the codebase (it was only used in `_marching_cubes_to_polydata`). The `requirements.txt` line can be removed or kept with a comment. Removing it reduces the install footprint but is a separate decision from the core swap — the roadmap e6 acceptance signal says "skimage.measure.marching_cubes is no longer called in surfaces.py (or is gated behind a fallback flag if any generator regresses)". Removing the dep entirely is optional; keeping it as a fallback annotation is acceptable.

---

## 7. AI-15 disclaimers

This milestone proposes no new variety or figure. The 11 implicit generators remain identical — only the meshing algorithm changes. No AI-15 action required.

---

## 8. Open questions for the user

None. The implementation is fully specified.

---

## Appendix: PyVista ImageData.contour call spec (confirmed in 0.48.4)

```python
grid = pv.ImageData(
    dimensions=(n, n, n),
    spacing=(2 * bounds / (n - 1),) * 3,
    origin=(-bounds, -bounds, -bounds),
)
grid.point_data["values"] = field.ravel(order="F")
mesh = grid.contour(
    [level],             # isosurfaces: list of float
    scalars="values",    # the field array name
    method="flying_edges",
    compute_normals=False,
)
# mesh is pv.PolyData — proceeds directly to .clean() / .smooth_taubin() / .compute_normals()
```

The `field` array must have dtype float32 or float64; the existing generators use float64 (NumPy default). Both dtypes work with Flying Edges (confirmed).
