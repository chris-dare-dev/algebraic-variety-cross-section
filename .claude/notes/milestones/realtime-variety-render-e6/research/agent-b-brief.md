# Research Brief — realtime-variety-render-e6 (agent-b)
**Agent lens:** VTK/PyVista Flying Edges API, normal quality, benchmarking
**Date:** 2026-05-22

---

## 1. TL;DR

Replace `skimage.measure.marching_cubes` with `pv.ImageData.contour([level], method='flying_edges')` in `surfaces.py:_marching_cubes_to_polydata`. The challenger's "normals lost" objection is **largely moot**: `vtkFlyingEdges3D` computes gradient normals natively via `compute_normals=True` in PyVista's `contour()` call — verified by probe on the installed PyVista 0.48.4 + VTK 9.6.2. The ravel-order risk is real and non-obvious: `indexing='ij'` meshgrid arrays must be raveled with `order='F'` (Fortran, column-major) to match VTK's ijk (x-fastest) layout; using `order='C'` silently swaps the x and z axes in the isosurface (verified by asymmetric ellipsoid probe). Measured speedup on this machine: 7–10x on the MC-only step at production resolutions (n=220–260), yielding a 2.5x full-pipeline improvement (including field-eval + Taubin + normals). No new dependencies; zero AI-1..AI-15 conflicts.

---

## 2. Prior art in this repo

- `surfaces.py:87–141` — `_marching_cubes_to_polydata`: the function to replace. Pipeline: zero-crossing guard → `measure.marching_cubes` → build `pv.PolyData` → `clean()` → `smooth_taubin` → `compute_normals`. The skimage normals are attached pre-Taubin as a seed (line 128) but are overwritten by `compute_normals()` post-Taubin (line 136).
- `surfaces.py:109` — `spacing = (2 * bounds / (n - 1),) * 3` — uniform grid spacing, exactly the `spacing` parameter `pv.ImageData` needs.
- `surfaces.py:119` — `measure.marching_cubes(field, level=level, spacing=spacing)` — the single call to replace.
- `surfaces.py:120` — `verts -= bounds` — origin correction. **With `pv.ImageData(origin=(-bounds, -bounds, -bounds))` this shift is done automatically; the explicit `verts -= bounds` line is eliminated.**
- `surfaces.py:266` — Fermat quartic n cap at 220 (e1 CAND-13 lowered from 260).
- `surfaces.py:480` — enriques_figure_4 uses `n=220` (already at the cap).
- `surfaces.py:711` — calabi_yau_dwork uses `n=260` (unchanged — implicit pipeline, will benefit from FE).
- `app.py:514–549` — CAND-12 telemetry: `time.perf_counter()` brackets around `surface.generate()`, prints `[render] label: NNN ms` to stdout. This is the before/after measurement mechanism.
- `tests/test_mesh_generators.py` — smoke tests: non-empty mesh + vertex bounds check for all implicit generators. These tests guard the FE replacement.
- `tests/test_marching_cubes_empty.py` — likely tests the `ValueError("No real zero set...")` guard. Implementer must verify the FE path preserves this guard (it does — the field min/max check happens before `grid.contour()`).

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| PyVista 0.48.4 `contour()` API (live probe) | installed pyvista 0.48.4 | `method='flying_edges'` + `compute_normals=True` produce a `pv.PolyData` with a `Normals` point array (unit-length, gradient-derived). Confirmed by probe. | Critical — the exact API the implementer needs |
| VTK 9.6.2 vtkFlyingEdges3D (live probe) | vtk.vtkVersion.GetVTKVersion() | VTK 9.6.2 installed; vtkFlyingEdges3D ships in VTK 9.x. SMP threading active. | Confirms SMP path is available |
| PyVista `pv.ImageData` constructor | live probe | `pv.ImageData(dimensions=(n,n,n), spacing=(s,s,s), origin=(-b,-b,-b))` — three keyword args, no positional. Returns an `UnstructuredGrid`-like object; `.contour()` is on the `DataSet` mixin. | Implementation detail — exact constructor call |
| Ravel order verification (live probe) | asymmetric ellipsoid probe (local) | `indexing='ij'` meshgrid: F-order ravel is **required**. C-order silently swaps x↔z axes. Verified: x_radius=2 / z_radius=3 — F-order maps x→[−2,2] correctly; C-order swaps x and z bounds. | CRITICAL — wrong ravel = wrong surface geometry |
| compute_normals=True verification (live probe) | live probe | `contour(..., compute_normals=True)` stores a `Normals` (984,3) float array in point_data; unit-length (min/max norm = 1.000). Challenger "normals lost" objection is moot. | Resolves challenger MINOR objection (a) |
| Benchmark MC vs FE at n=80,160,220,240,260 (live probe) | local benchmark | MC-only speedup: 1.3x at n=80, 2.7x at n=160, 7.4x at n=220, 10.2x at n=240, 10.3x at n=260. Full-pipeline (with Taubin) at n=220: 2.5x. Field-eval dominates at small n. | Answers challenger MINOR objection (b) |
| Kitware "Really Fast Isocontouring" blog (oss-trends scout) | https://www.kitware.com/really-fast-isocontouring/ | 13.8–14.5x at 16 threads (Intel x86). Single-thread 2–4x. | Calibrates the "1–2 orders of magnitude" claim: 7–10x on this Windows 11 machine is in the right register |
| capability-scout final-report §3 Rank 6 (CAND-1) | `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md:110–119` | MINOR objections: (a) FE drops skimage gradient normals; (b) speedup claim needs local measurement with CAND-12. Both resolved by probes above. | Source of challenger objections |

---

## 4. Recommended approach

### Step 1 — Replace `_marching_cubes_to_polydata` MC step

The exact substitution for lines `surfaces.py:119–128`:

```
# OLD (lines 119–128):
verts, faces, normals, _ = measure.marching_cubes(field, level=level, spacing=spacing)
verts -= bounds
n_faces = faces.shape[0]
pv_faces = np.empty((n_faces, 4), dtype=np.int64)
pv_faces[:, 0] = 3
pv_faces[:, 1:] = faces
mesh = pv.PolyData(verts, pv_faces.ravel())
mesh.point_data["Normals"] = normals.astype(np.float32)

# NEW:
spacing_val = 2 * bounds / (n - 1)
grid = pv.ImageData(
    dimensions=(n, n, n),
    spacing=(spacing_val, spacing_val, spacing_val),
    origin=(-bounds, -bounds, -bounds),
)
grid.point_data["field"] = field.ravel(order="F")  # F-order required for indexing='ij'
mesh = grid.contour(
    [level],
    scalars="field",
    method="flying_edges",
    compute_normals=True,  # vtkFlyingEdges3D gradient normals natively
)
```

The `origin=(-bounds, -bounds, -bounds)` accounts for the coordinate shift that `verts -= bounds` previously did manually — no explicit shift needed.

The `compute_normals=True` argument instructs `vtkFlyingEdges3D` to compute gradient-based normals internally, storing them as the `Normals` point array. These are gradient normals from the scalar field, functionally equivalent to `skimage`'s analytic gradient normals. The challenger's "normals lost" objection does NOT apply.

### Step 2 — Remove the skimage import

After the replacement, `from skimage import measure` is only used in `_marching_cubes_to_polydata`. Remove it. (`scikit-image` stays in `requirements.txt` — it may have other usages, but in practice the import can be removed from `surfaces.py`.)

### Step 3 — Add a `realtime-variety-render-e6` comment

Following the established comment pattern (e.g., `# realtime-variety-render-e1-s3 (CAND-13):`), add a comment block on the new `grid = pv.ImageData(...)` block documenting the FE replacement and the ravel-order requirement.

### Step 4 — Verify normals path consistency

After `grid.contour(compute_normals=True)`, the mesh has a `Normals` point array. The subsequent `mesh.clean()` call can discard point data arrays in some versions — verify with a probe that `Normals` is preserved after `clean()`. If not, call `compute_normals=True` on the contour and then just let the existing `compute_normals()` call at the end of the pipeline re-derive them (the `compute_normals=True` at the `contour()` step is a seed optimization, not load-bearing, since `compute_normals()` at the end always runs).

### Step 5 — Off-screen visual comparison (acceptance criterion)

The milestone brief requires off-screen visual comparison on Kummer + Enriques canonical sextic to confirm no shading regression on high-curvature surfaces. Write a small off-screen probe (AI-3 compliant: `pv.OFF_SCREEN = True`, no `MainWindow`) that renders both the MC-pipeline and FE-pipeline results for `kummer_surface(mu_squared=1.3, n=120)` and `enriques_figure_1(c=1.0, n=120)` to PNG and saves side-by-side. The Kummer surface has 16 nodes (high curvature); the Enriques canonical sextic has double-curve edges — both are the right stress test for normals quality.

### Step 6 — Before/after timing via CAND-12 telemetry

Run the app (`python app.py`), load Fermat quartic and drag the `c` slider, observe `[render] ... NNN ms` in stdout. Do the same with the FE replacement. The measured full-pipeline speedup at n=220 on this machine (Windows 11, VTK 9.6.2) is **~2.5x** (228 ms → 92 ms). At the MC-only level the speedup is **~7x** (173 ms → 23 ms); the remaining cost is field-eval (~40%) + Taubin + normals.

---

## 5. Alternatives considered

- **`compute_normals=False` on contour() + post-Taubin `compute_normals()`**: The current pipeline already calls `compute_normals()` after Taubin, so the Taubin smoothing step overwrites any normals from the contour step anyway. Using `compute_normals=True` is a minor optimization (normals are available earlier for debugging) but is not strictly necessary. The existing `compute_normals()` at line 136 re-derives correct normals post-smoothing regardless.
- **Calling `vtkFlyingEdges3D` directly via `vtk.*` API**: More verbose, bypasses PyVista's convenience. Not recommended — PyVista 0.48.4's `contour(method='flying_edges')` is the right level.
- **`C` order ravel**: Rejected. Asymmetric ellipsoid probe confirmed that `order='C'` silently swaps x and z axes when combined with `indexing='ij'` meshgrid. This would produce geometrically wrong isosurfaces that pass all existing smoke tests (the tests only check non-empty + bounds, not topology or orientation).
- **`pv.wrap(vtkImageData)` pattern**: Equivalent to direct `pv.ImageData()` constructor but more verbose. No advantage.
- **Keeping skimage for gradient_direction normalization**: The `gradient_direction` kwarg in skimage MC controls whether gradient points inward or outward. Flying Edges computes gradients from the scalar field and the sign convention is consistent with skimage's default. No correction needed.

---

## 6. Risks and unknowns

### R1 — Ravel order (CRITICAL, easy to miss)
`indexing='ij'` in numpy meshgrid places x as the first axis (row-major in the physical layout sense). VTK's ImageData stores points with i (=x) as the **fastest** varying index — Fortran order. Therefore `field.ravel(order='F')` is required. Using `order='C'` silently transposes the x and z axes in the isosurface without any error or warning. This is the single highest regression risk. The smoke tests in `test_mesh_generators.py` will NOT catch this because they only check non-empty + bounds — a transposed surface is still non-empty and within bounds. The off-screen visual comparison (Step 5 above) is the right acceptance gate for this.

### R2 — `clean()` discarding Normals
PyVista's `mesh.clean()` merges duplicate vertices. It may or may not preserve point data arrays depending on the version. In the current pipeline this doesn't matter because `compute_normals()` always runs after `smooth_taubin()`. The `compute_normals=True` on the contour step is strictly optional. Implementer should not add any logic that relies on the Normals array surviving through `clean()`.

### R3 — `compute_scalars=True` (default) on contour()
By default, `contour()` carries the scalar field values as a point array named `"field"`. This adds a few KB of point data to the mesh. The existing code does not use these scalars downstream. The implementer may optionally add `compute_scalars=False` to suppress this, but it's not load-bearing.

### R4 — AI-6 pipeline isolation
The replacement is confined to `_marching_cubes_to_polydata`. The Hanson parametric generators (`calabi_yau_quintic`, `calabi_yau_cubic`, `calabi_yau_asymmetric`) do NOT call this function — they use `_grid_to_polydata` + `_concat_polydata`. The replacement is implicit-pipeline-only. AI-6 is satisfied.

### R5 — AI-14 contract
The FE pipeline returns `pv.PolyData` (confirmed by probe: `type(mesh) = <class 'pyvista.core.pointset.PolyData'>`). The zero-crossing guard `if field.min() > level or field.max() < level: raise ValueError(...)` must remain in place before the `grid.contour()` call, since `vtkFlyingEdges3D` returns an empty mesh (not an error) when no isosurface exists. AI-14 requires `ValueError` for the empty-field case.

### R6 — Normal orientation winding vs skimage
The skimage MC uses `gradient_direction='descent'` by default, producing outward-pointing normals for level-set surfaces (convention: field > 0 outside). Flying Edges computes gradients from the scalar field with the same outward convention. However, after Taubin smoothing + `compute_normals(consistent_normals=True)`, the normals are re-derived from triangle winding anyway. Visual comparison (Step 5) is the definitive check.

### R7 — Test suite guard
Existing `tests/test_mesh_generators.py` smoke tests pass through `_marching_cubes_to_polydata` and will exercise the FE path without modification. The implementer must run the full test suite post-replacement to confirm no regressions.

---

## 7. AI-15 disclaimers

Not applicable — this milestone does not propose any new variety or figure. It is a pure internal-pipeline replacement.

---

## 8. Open questions for the user

None — the milestone is fully specified. The ravel-order and normal-quality risks identified above are addressable by the implementer without user input.
