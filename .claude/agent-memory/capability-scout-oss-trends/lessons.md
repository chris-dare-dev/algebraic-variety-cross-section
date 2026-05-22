# OSS Trends Scout — Lessons

## Lesson 1 — Performance-focused survey: separate the bottleneck layers first (2026-05-21)
When the brief is "make X faster", establish upfront which pipeline stage is the bottleneck *before* searching for tools. In this run: field evaluation (NumPy, ~150 ms) and marching cubes (~350 ms) are separate bottlenecks requiring separate tools (Numba JIT vs. vtkFlyingEdges3D). A scout that searches only for "fast marching cubes" would miss the more tractable field-eval win.

## Lesson 2 — PyVista's contour() has a method= parameter; it does NOT use flying_edges by default (2026-05-21)
`mesh.contour(method='flying_edges')` calls vtkFlyingEdges3D (10–15× speedup). Default `method='contour'` calls vtkContourFilter which uses classic marching cubes. This distinction is not surfaced in the top-level PyVista docs; requires reading the API reference and the VTK forum discussion. Always verify the default vs. opt-in status of a claimed perf feature.

## Lesson 3 — Numba arm64 wheels are now first-class (Tier 1) on PyPI from 0.61+ (2026-05-21)
The historical "Numba doesn't have arm64 wheels" concern is resolved since Numba 0.61.2 (April 2025). Current stable is 0.65.1 (April 2026). When re-surveying scientific Python perf tools for Apple Silicon, check PyPI wheel listings directly rather than relying on cached knowledge of the arm64 gap.

## Lesson 4 — VTK/Qt threading boundary: build PolyData off-thread, render on GUI thread (2026-05-21)
The safe threading pattern is universally consistent across PyVista discussions: `pv.PolyData` construction (numpy arrays, VTK data objects) is safe off the GUI thread; `plotter.add_mesh()` and `plotter.render()` are NOT thread-safe and must be called on the GUI thread. Always surface this boundary explicitly in any threading recommendation for PyVista + Qt apps. `QRunnable` + signals is the correct pattern; `pyvistaqt.BackgroundPlotter` is for independent plotters and does not fit the `QtInteractor`-in-`QMainWindow` architecture.

## Lesson 5 — pyvistaqt hangs on macOS with PySide6 6.10+ (reported Feb 2026, issue #793) (2026-05-21)
This is an active upstream risk for the app. A requirements pin of `PySide6 >=6.6,<6.10` is prudent until resolved. When surveying Qt deps for a macOS-primary app, always search for open compatibility issues with recent Qt minor versions.

## Lesson 6 — joblib is already transitively installed; prefer it over diskcache for cross-session PolyData caching (2026-05-21)
`joblib` is a transitive dep of `scikit-image` and therefore already in the venv. `diskcache` provides similar cross-session memoization but adds a new dependency with no significant advantage for a single-developer desktop app. Always check transitive deps in requirements.txt before recommending a new install.

## Lesson 7 — GPU isosurface candidates (isoext, CuMCubes) require CUDA; irrelevant for macOS primary platform (2026-05-21)
When the platform is macOS Apple Silicon, CUDA-based GPU compute is a non-starter (no CUDA hardware). Filter these out early rather than researching them in depth. VTK's own GPU isosurface mode (ISOSURFACE_BLEND) is in-stack but requires ImageData volume input and is not exposed via PyVista's contour() API.
