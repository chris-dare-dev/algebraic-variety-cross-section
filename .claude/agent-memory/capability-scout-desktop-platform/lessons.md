# Lessons — capability-scout-desktop-platform

## L-1 (2026-05-22) — VTK GL context thread-affinity is the hard ceiling on macOS

On macOS (arm64 and x86_64) the VTK OpenGL context has strict thread-affinity:
`makeCurrent` must be called on the context's creation thread (the Qt GUI thread).
Any `plotter.render()`, `plotter.add_mesh()`, or `plotter.remove_actor()` call
from a worker thread is undefined behavior and crashes on arm64 Macs.  When
proposing async compute, always map the boundary clearly: data manipulation
(NumPy, scikit-image, VTK filter pipelines) is safe on worker threads; VTK
*render window* calls must stay on the GUI thread and are delivered via
`Signal`/`Slot` cross-thread queued connections.

## L-2 (2026-05-22) — AI-9 `_computing` guard semantics change under async compute

The `_computing` guard in `_render_current` (app.py:339–341) serializes renders
by blocking the GUI thread during compute.  That works when compute is
synchronous but is the wrong shape for async workers: the guard should become
a "job in flight" flag checked at submit time, cleared in the GUI-thread
delivery callback.  When writing any brief that proposes async compute,
explicitly model this transformation rather than leaving it implicit.

## L-3 (2026-05-22) — GPU isosurfacing via VTK is a parking-lot item (2026)

As of 2026-05, VTK's WebGPU backend exists as an experimental *renderer*
(replacing the rasterizer), not a GPU-compute algorithm layer.  There is no
shipping GPU-side marching-cubes / FlyingEdges pass.  OSPRay is CPU-bound.
When a brief asks about GPU isosurfacing for VTK-based apps, flag it honestly
as a 2026–2027 upstream dependency, not a near-term candidate.

## L-4 (2026-05-22) — `vtkFlyingEdges3D` requires `vtkImageData`, not raw NumPy

The FlyingEdges speedup is real (2–5× on multi-core), but accessing it from
PyVista requires wrapping the scalar field into a `vtkImageData` with correct
spacing and origin before calling `mesh.contour(method='flying_edges')`.  The
analytic gradient normals from scikit-image's `marching_cubes` are lost in this
path — this is a visual quality trade-off that must be disclosed to the
implementing agent.

## L-5 (2026-05-22) — Candidate layering: debounce first, async second, LOD third

For latency-reduction in Qt+VTK apps the correct order of implementation is:
1. `QTimer` debounce (trivial; no threading; immediate UX win for slider-jank)
2. `QThread`/`QRunnable` async compute (medium effort; makes GUI always responsive)
3. Coarse LOD preview during drag (depends on async being in place)
4. FlyingEdges / Numba speedups (stack on top)
Each step is independently shippable.  Pitching them all at once without the
layering sequence leads to over-scoped milestones.

## L-6 (2026-05-22) — `superqt.qdebounced` is a drop-in for hand-rolled QTimer debounce

`superqt` (already in the source registry) provides `@qdebounced(timeout=N)`
as a tested, one-decorator replacement for a hand-rolled `QTimer` debounce
slot.  Always prefer it over custom `QTimer` wiring when the dependency is
already considered.
