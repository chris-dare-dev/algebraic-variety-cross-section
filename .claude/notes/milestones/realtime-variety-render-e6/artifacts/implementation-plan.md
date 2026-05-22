# Implementation plan — realtime-variety-render-e6 (VTK Flying Edges)

Inline path. Single function: `surfaces.py:_marching_cubes_to_polydata`.

1. **Swap the isocontouring call.** Replace the `skimage.measure.marching_cubes`
   block (`surfaces.py:119-128`) with `pv.ImageData(dimensions=(n,n,n),
   spacing=(s,)*3, origin=(-bounds,)*3)` + `field.ravel(order="F")` +
   `.contour([level], scalars="field", method="flying_edges",
   compute_normals=True, compute_scalars=False)`. **F-order ravel is
   load-bearing** — C-order silently transposes x/z under `indexing="ij"`.

2. **Origin shift + guard.** `origin=(-bounds,)*3` replaces the manual
   `verts -= bounds`. The zero-crossing `ValueError` guard (lines 113-118)
   stays *before* the contour call — `vtkFlyingEdges3D` returns an empty mesh
   (not an error) when no isosurface exists, so AI-14's `ValueError` contract
   depends on that guard remaining.

3. **Docstring + import.** Rewrite the function docstring step 1 to describe
   Flying Edges (SMP-threaded, gradient normals via `compute_normals=True`).
   Remove the now-dead `from skimage import measure` import (line 18 —
   `measure` is used nowhere else in `surfaces.py`). `scikit-image` stays in
   `requirements.txt` (transitive / future use).

4. **Test.** Run `.venv/Scripts/python.exe -m pytest tests/ -q` — the
   `tests/test_mesh_generators.py` smoke tests and `test_marching_cubes_empty.py`
   guard the swap. All must stay green; no new tests strictly required (the
   swap is behavior-preserving) but a topology/orientation guard is worth
   adding since the smoke tests only check non-empty + bounds.

5. **Off-screen visual comparison (acceptance gate).** Render Kummer (16
   nodes — high curvature) and Enriques canonical sextic (double curves) via
   `pv.OFF_SCREEN = True` (never `MainWindow` — AI-3); confirm the FE result
   is geometrically correct (F-order verified — not transposed) and shading
   is equivalent to the MC baseline. Measure before/after timing.

Constraints: AI-1 (VTK in-stack), AI-3, AI-6 (implicit pipeline only —
Hanson untouched), AI-13, AI-14. Predecessor e1 (CAND-12 telemetry) complete.
