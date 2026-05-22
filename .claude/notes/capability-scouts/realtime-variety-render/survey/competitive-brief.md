# Competitive Landscape Scout — Real-Time Variety Render
## Scout role: Competitive landscape (peer scientific-viz / algebraic-geometry desktop apps)
**Run date:** 2026-05-21  
**Scope:** How peer tools make a parametric/implicit surface respond interactively to a dragged parameter — what they render DURING drag vs ON release, and which optimization techniques they use.

---

## 1. TL;DR

Mathematica `Manipulate` + `ControlActive` is the canonical peer pattern: render a coarse, fast preview during drag (reduced `PlotPoints`, step-doubled marching resolution) and automatically upgrade to full quality on mouse-button release — a two-pass LOD approach that requires zero additional infrastructure. ParaView goes further with a dual-mode pipeline: geometric LOD decimation + image subsampling during interaction, full still-render on release, all mediated by VTK's `vtkPVRenderView` interactive/still render switching. The most actionable near-term win for this app is replacing `skimage.measure.marching_cubes` with `pv.ImageData.contour(method='flying_edges')` (PyVista's VTK-threaded wrapper, 1-2 orders of magnitude faster than scikit-image's Cython MC at the same resolution, available in the current `pyvista>=0.46` pin), combined with a `QTimer`-debounce on `valueChanged` to allow continuous updates at coarse resolution during drag and full-resolution on release.

---

## 2. Top Capability Candidates

Ranked by estimated impact/effort ratio for this app's hard constraints (AI-1: PySide6+PyVista+VTK only; AI-9: re-entrancy guard; AI-3: pv.OFF_SCREEN; macOS Apple Silicon primary; single-developer cadence).

---

### C-1 — PyVista Flying Edges (`pv.ImageData.contour(method='flying_edges')`)
**Source app:** VTK / PyVista (directly available in the current dep stack)  
**Public evidence:** https://www.kitware.com/really-fast-isocontouring/ · https://vtk.org/doc/nightly/html/classvtkFlyingEdges3D.html · https://docs.pyvista.org/api/core/_autosummary/pyvista.DataSetFilters.contour.html  
**License:** VTK BSD-3-Clause; PyVista MIT  

**UI/UX angle:** Invisible to the user — same mesh quality, faster response. Could enable reducing the debounce delay from "release only" to 50-150 ms continuous updates without UI thrashing.

**Technical angle:**
`vtkFlyingEdges3D` is a four-pass parallelized isosurfacing algorithm threaded with `vtkSMPTools`. Kitware benchmarks report "1-2 orders of magnitude faster than Marching Cubes even in single-thread mode." The PyVista API is:
```python
grid = pv.ImageData(dimensions=(n, n, n), spacing=(...), origin=(...))
grid.point_data["field"] = scalar_array.ravel(order="F")
mesh = grid.contour([0.0], scalars="field", method='flying_edges')
```
This replaces the current `skimage.measure.marching_cubes(field, ...)` + `pv.PolyData(verts, faces)` construction in `surfaces.py:_marching_cubes_to_polydata` (lines 48-102). The output is a `pv.PolyData` with the same downstream smoothing pipeline. **Key difference:** `vtkFlyingEdges3D` does not return gradient-based analytic normals; normals must be derived via `mesh.compute_normals()` post-extraction (same as the current post-Taubin step at line 97). The flying_edges output may also differ slightly from MC around degenerate triangles — the existing `test_mesh_generators.py` smoke tests will catch regressions.

**Complexity:** Low-medium. Drop-in replacement in `_marching_cubes_to_polydata`, ~15 lines changed. Requires profiling to measure actual speedup on Apple Silicon M-series (VTK's TBB path may or may not be enabled in the PyPI wheel — check `vtkmodules.vtkFiltersCore.vtkFlyingEdges3D().GetSMPEnabled()`).

**Gating constraints:** pyvista>=0.46 already in requirements.txt. On Apple Silicon the VTK wheels ship with OpenMP, not TBB, which may reduce the multi-thread benefit. Still faster than scikit-image MC in single-thread mode. Does NOT provide analytic gradient normals — acceptable since we already call `compute_normals()` post-Taubin.

**Cross-reference:** `surfaces.py:48-102` (`_marching_cubes_to_polydata`), `surfaces.py:80` (the `measure.marching_cubes` call).

**Impact: HIGH | Effort: LOW | Risk: LOW**

---

### C-2 — Two-Pass LOD: Coarse Preview During Drag, Full Resolution on Release (Mathematica `ControlActive` pattern)
**Source app:** Mathematica `Manipulate` + `ControlActive`  
**Public evidence:** https://reference.wolfram.com/language/ref/ControlActive.html (paywalled but documented in web search results) · https://reference.wolfram.com/language/tutorial/AdvancedManipulateFunctionality.html · https://reference.wolfram.com/language/tutorial/IntroductionToManipulate.html  
**License:** Wolfram proprietary — study only, not vendored  

**UI/UX angle:** The canonical pattern described in Wolfram docs: "While you drag the slider, a fast but somewhat crude rendering of the plot is created in real time, and when you release the control, a smooth rendering shows up a moment later." `ControlActive[fast_version, slow_version]` switches the computation inside `Manipulate` based on whether a control is being actively dragged. Built-in 3D plotting functions like `Plot3D` **automatically** switch to fewer `PlotPoints` during drag — no user code needed. The result is a "jagged but immediate" preview that upgrades to full quality on release.

**Technical angle for this app:** `scikit-image.measure.marching_cubes` (or the flying_edges replacement from C-1) accepts a `step_size` parameter. `step_size=1` is full resolution; `step_size=3` or `step_size=4` is ~3-4x coarser in each dimension (27-64x fewer voxels evaluated) and correspondingly faster. The implementation hook is in `_marching_cubes_to_polydata` / the flying_edges equivalent. During drag, pass `step_size=3`; on release, pass `step_size=1`. The QSlider `valueChanged` signal is emitted during drag; `sliderReleased` is emitted only on release. Currently `parameters_panel.py:229-230` (`_on_slider_released`) connects only `sliderReleased` to `params_changed`. Adding a `valueChanged` → coarse-preview path requires:
1. A `_on_value_changed_drag` slot in `ParametersPanel` that emits a new `params_preview_changed` signal with the current values.
2. `MainWindow._on_params_preview_changed` → `_render_current(reset_camera=False, step_size=3)`.
3. The re-entrancy guard (AI-9) already blocks overlapping renders — the coarse render drops if a full render is in-flight.
4. A debounce (C-3 below) prevents thrashing even at coarse resolution.

**Complexity:** Medium. Requires a second render path or a `step_size` parameter threading through `_render_current` → generator functions. Must not break the existing `sliderReleased` → full-res path. The `_computing` guard (AI-9) remains the correctness backstop.

**Gating constraints:** `skimage.measure.marching_cubes` `step_size` parameter documented in scikit-image 0.22+. Note: `step_size` reduces voxel sampling density; normals still derivable from the coarser field. The coarse mesh will be visually rougher but geometrically correct. The Hanson parametric pipeline (CY3 Hanson figures) already re-renders in under 0.1s and does not benefit from this technique.

**Cross-reference:** `parameters_panel.py:224-230` (`_on_value_changed`, `_on_slider_released`); `app.py:309-313` (`_on_params_changed`); `app.py:334-404` (`_render_current`); `surfaces.py:48-102` (`_marching_cubes_to_polydata`).

**Impact: HIGH | Effort: MEDIUM | Risk: LOW-MEDIUM**

---

### C-3 — QTimer Debounce on `valueChanged` (KDAB / Qt idiom)
**Source app:** Qt ecosystem / KDAB signal throttlers · superqt library (BSD-3-Clause)  
**Public evidence:** https://www.kdab.com/signal-slot-connection-throttlers/ · https://github.com/pyapp-kit/superqt (BSD-3-Clause) · https://forum.qt.io/topic/157973 (QTimer debounce pattern) · PySide6 docs: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html  
**License:** Qt LGPL-3.0 (already used); superqt BSD-3-Clause (import-compatible with PySide6 LGPL stack)  

**UI/UX angle:** Combining C-2 with a debounce of 50-150 ms means the coarse render fires at most 6-20 times per second during a slow drag, not on every pixel of slider movement. Industry norm for a "search box that fires after typing stops" is 100-200 ms; for real-time mesh visualization 50-100 ms is appropriate. A debouncer activates the slot only after a grace period since the last signal emission — ideal for rapid slider drags.

**Technical angle:** Two options:
1. **Pure QTimer pattern** (zero new deps): Create a single-shot `QTimer` in `ParametersPanel.__init__`. On `valueChanged`, restart the timer (`_debounce_timer.start(100)`). On timeout, emit `params_changed` with current values (the coarse-res variant if C-2 is implemented). `sliderReleased` bypasses the timer and emits the full-res signal directly.
2. **superqt `@qthrottled`/`@qdebounced`** (adds 1 dep): superqt's `utilities` include signal throttling decorators. BSD-3-Clause licensed. Used by napari (which also uses PySide2/PyQt/PySide6). However, superqt is not in `requirements.txt` and adds a dependency; the QTimer pattern is equivalent and requires no new dep.

**Complexity:** Low (QTimer approach) or Low-medium (superqt). The QTimer approach is self-contained in `ParametersPanel`. The `_computing` guard in `app.py` already protects against overlapping re-renders; debounce adds a second layer that reduces how often the guard fires.

**Gating constraints:** AI-9 re-entrancy guard remains the correctness backstop. QTimer-based debounce is a standard PySide6 pattern with no new invariant conflicts. The `sliderReleased`-only path must remain intact as the full-resolution trigger.

**Cross-reference:** `parameters_panel.py:39-96` (`__init__` — where the timer would be created); `parameters_panel.py:224-230` (`_on_value_changed`, `_on_slider_released`); `app.py:309-313` (`_on_params_changed`); `app.py:339-341` (`self._computing` guard).

**Impact: MEDIUM | Effort: LOW | Risk: VERY LOW**

---

### C-4 — Background-Thread Mesh Generation with Main-Thread VTK Render (napari / superqt `@thread_worker` pattern)
**Source app:** napari (BSD-3-Clause) · superqt `thread_worker` / `GeneratorWorker` (BSD-3-Clause)  
**Public evidence:** https://napari.org/dev/guides/threading.html · https://github.com/napari/napari (BSD-3-Clause) · https://github.com/pyvista/pyvista/discussions/4006 (critical: threading + VTK context constraints) · https://github.com/pyapp-kit/superqt (BSD-3-Clause)  
**License:** napari BSD-3-Clause; superqt BSD-3-Clause  

**UI/UX angle:** Move the mesh generation (`surface.generate(**params)`) off the main thread entirely. The UI slider and status bar remain fully responsive during the ~0.5s computation. When the mesh is ready, the worker signals the main thread, which calls `_apply_domain_and_render()`. napari uses exactly this pattern: `@thread_worker` converts a long-running function into a `QRunnable`-based worker that emits `.returned` / `.yielded` Qt signals back to the main thread. napari 0.5.3 (2024) moved `Layer.get_status` computation to a background thread, "dramatically improving performance for 3D surface layers with lots of polygons."

**Technical angle — critical constraints:**
- **VTK must run on the main thread.** PyVista discussion #4006 confirms: "On macOS, the Cocoa window must run from the main thread." `plotter.add_mesh()` and `plotter.render()` are NOT thread-safe. The pattern is: run `surface.generate()` on the worker thread, deliver the resulting `pv.PolyData` back to the main thread via a signal, and call `_apply_domain_and_render()` there.
- **Stale-result cancellation:** When the user drags quickly, multiple workers may be queued. The previous worker must be cancelled before starting a new one (napari's `worker.quit()`). This requires tracking `self._mesh_worker` in `MainWindow`.
- **AI-9 interplay:** The current `self._computing` guard and `QApplication.processEvents()` pattern in `_render_current` (app.py:339-404) would need to be restructured: `_computing` becomes "worker in flight" rather than "main thread is blocked."
- **`QApplication.processEvents()` removal:** If mesh generation moves off-thread, the `processEvents()` call at `app.py:349` can be removed entirely, eliminating the re-entrancy risk it was introduced to solve.

**Complexity:** High. Requires refactoring `_render_current` into a compute phase (worker thread) and a render phase (main thread). Adds ~60-80 lines of threading infrastructure. The payoff is a fully non-blocking UI during mesh generation.

**Gating constraints:** AI-9 guard becomes moot once `processEvents()` is removed. AI-1 stack unchanged. Requires superqt (BSD-3-Clause, import-compatible) OR manual `QThread`/`QRunnable` wiring. macOS Cocoa restriction (VTK on main thread) must be respected.

**Cross-reference:** `app.py:334-404` (`_render_current`); `app.py:339-341` (`_computing` guard); `app.py:349` (`QApplication.processEvents()`); `app.py:100-103` (instance variables `_actor`, `_raw_mesh`, `_computing`).

**Impact: HIGH | Effort: HIGH | Risk: MEDIUM-HIGH**

---

### C-5 — LRU Parameter-Space Mesh Cache (keyed by parameter tuple)
**Source app:** Conceptual — patterns from procedural modeling cache literature  
**Public evidence:** "A runtime cache for interactive procedural modeling," ScienceDirect (https://www.sciencedirect.com/science/article/abs/pii/S0097849312000702) · Python `functools.lru_cache` (stdlib) · `threading` thread-safety note: https://bugs.python.org/issue28969  
**License:** N/A (Python stdlib); study-only for the ScienceDirect paper  

**UI/UX angle:** When a user reverses a slider (drags left then right back to a previous value), the mesh is already in the cache — instant response. Especially valuable for the "hovering around one parameter" exploration pattern.

**Technical angle:** Key each mesh by a frozenset or tuple of rounded parameter values. `functools.lru_cache` cannot cache `pv.PolyData` objects directly (unhashable), but a simple `dict` with a max-size eviction policy (`collections.OrderedDict`) works. The cache key is `tuple(round(v, precision) for v in sorted(params.items()))`. Cache size of 8-16 meshes is ~50-150 MB depending on mesh complexity. The cache lives on `MainWindow` as `self._mesh_cache`. `_render_current` checks the cache before calling `surface.generate()`.

**Complexity:** Medium-low. The caching logic is pure Python dict manipulation (~20 lines). The challenge is cache invalidation when the surface type changes (`_on_subtype_changed` must clear the cache).

**Gating constraints:** Memory budget on a typical MacBook: 16 meshes at ~10 MB each = 160 MB. Acceptable. `pv.PolyData` objects are reference-counted; explicit `del` on eviction. Thread-safety is not required if the cache lives on the main thread only (compatible with C-4 if the worker thread never writes to the cache). `functools.lru_cache` with a wrapper function is NOT thread-safe per CPython issue 28969; the dict approach with a lock is safer.

**Cross-reference:** `app.py:357` (`self._raw_mesh = surface.generate(**params)` — this is the call to cache); `app.py:100-103` (instance variables — `_mesh_cache` would be added here); `app.py:272-307` (`_on_subtype_changed` — must invalidate cache).

**Impact: MEDIUM | Effort: LOW-MEDIUM | Risk: LOW**

---

### C-6 — `step_size` Coarse Grid for Parametric Preview + Adaptive Bounds Tightening
**Source app:** scikit-image `measure.marching_cubes` documentation; GeoGebra 3D (implicit solver design)  
**Public evidence:** https://scikit-image.org/docs/stable/auto_examples/edges/plot_marching_cubes.html (`step_size` param) · https://imaginary.org/program/surfer (SURFER uses GPU raytracing, not MC, for interactive preview) · arXiv:2304.09673 "Synchronized-tracing of implicit surfaces"  
**License:** scikit-image BSD-3-Clause (already in use)  

**UI/UX angle:** A coarse-grid mesh (`step_size=3` or `step_size=4`) at 50×50×50 effective voxels renders visibly rougher than the full 150×150×150 grid but is geometrically correct (topologically consistent per scikit-image docs: "result will always be topologically correct"). For exploratory drag it gives the user immediate geometric feedback — they can see when the surface topology changes or when a hole opens up.

**Technical angle:** `skimage.measure.marching_cubes(field, level=0, step_size=3)` samples every 3rd voxel in each dimension, reducing the mesh computation by ~27x. The field array still needs to be evaluated at full resolution (otherwise bounds effects differ), but the MC extraction itself is the bottleneck. Alternatively, evaluate the field at a coarser grid (n//3 × n//3 × n//3) for the preview and full grid for the final render. Either approach integrates cleanly into `_marching_cubes_to_polydata` with an optional `step_size` parameter.

**Complexity:** Very low — one parameter change to the existing `marching_cubes` call.

**Gating constraints:** scikit-image 0.22+ (already pinned). The Taubin smoothing post-step still applies (and may be less critical at preview quality). The Hanson parametric pipeline does not use marching cubes and is not affected. The `_render_current` function would need to accept a `step_size` parameter that flows through to `surface.generate`.

**Cross-reference:** `surfaces.py:80` (`measure.marching_cubes(field, level=level, spacing=spacing)` — `step_size=1` default); `surfaces.py:48-102` (`_marching_cubes_to_polydata` — add optional `step_size` kwarg).

**Impact: MEDIUM | Effort: VERY LOW | Risk: VERY LOW**

---

### C-7 — ParaView Dual-Mode Render (Interactive LOD + Still Render Switching)
**Source app:** ParaView / VTK (`vtkPVRenderView`)  
**Public evidence:** https://docs.paraview.org/en/latest/Tutorials/SelfDirectedTutorial/visualizingLargeModels.html §4.9 · https://www.paraview.org/paraview-docs/v5.13.2/cxx/classvtkPVRenderView.html  
**License:** Apache-2.0  

**UI/UX angle:** ParaView implements a two-mode render pipeline: "interactive render" (fast, coarser, during mouse drag / camera manipulation) and "still render" (full quality, after interaction ends). "As you drag your mouse in a 3D view to move the data, you may see an approximate rendering while you are moving the mouse, but the full detail will be presented as soon as you release the mouse button." An optional delay parameter defers the still render to allow chained interactions.

**Technical angle:** ParaView uses two distinct mechanisms:
1. **Geometric LOD** — replaces the mesh with a `vtkLODActor`-decimated low-poly version during camera interaction. This applies to *camera moves*, not parameter changes.
2. **Image subsampling** — reduces the render resolution in each dimension during interaction, then inflates to full size ("image-level LOD").
For **parameter changes** (not camera moves), ParaView re-executes the full filter pipeline on release (not during drag). The interactive LOD applies to the display of the *existing* mesh during camera interaction, not to the mesh re-generation pipeline. This is an important distinction: ParaView does NOT run marching cubes during a slider drag — it waits for release, then runs the filter pipeline, then shows a still render. The interactive LOD is a display-side optimization, not a generation-side one. **Lesson:** Display-side LOD (image subsampling or mesh decimation during camera interaction) is independent from generation-side LOD (coarser marching cubes during parameter drag). This app already benefits from VTK's camera-interaction performance implicitly.

**Complexity:** The display-side LOD is already handled by VTK under `QtInteractor`. The filter-pipeline on release is the current INT-2 behavior. Nothing to implement for the ParaView pattern specifically — but the pattern validates the two-level strategy in C-2.

**Gating constraints:** AI-1 compliant (VTK is the underlying stack). The `vtkLODActor` approach (geometric LOD) is available in PyVista as `plotter.add_mesh(..., pbr=False)` combined with custom decimation, but this is out of scope for parameter-response latency (it addresses camera-rotation smoothness, not mesh generation speed).

**Cross-reference:** No direct code analog — this is a design-pattern reference. Closest: `app.py:455-479` (`_apply_domain_and_render` where `plotter.add_mesh()` is called).

**Impact: LOW (direct) — HIGH (as validation of two-level strategy) | Effort: N/A (already implicit in VTK)**

---

### C-8 — Desmos 3D Web Worker Async Compute Pattern
**Source app:** Desmos 3D Calculator (closed-source, browser-based)  
**Public evidence:** "Real-time graphics in Desmos, with just math and a browser," ACM SIGGRAPH RTL 2025 (https://dl.acm.org/doi/10.1145/3721243.3735987) · Desmos help center  
**License:** Proprietary — study only  

**UI/UX angle:** Desmos runs its math engine "in a pool of web workers that asynchronously reports results to the front-end so the interface can remain responsive." For implicit surfaces: "the 3D calculator generates a mesh using a 3D solver on the CPU and uploads it to the GPU for rendering." This is a browser-side analogue of the background-thread pattern (C-4). The Desmos paper explicitly notes raycasting "forces re-running the full computation on every frame, even if the underlying geometry doesn't change (e.g., because the user rotates the surface)" — which is why they prefer CPU mesh generation + GPU display. The insight for this app: separating the geometry computation from the display pipeline (as C-4 proposes) is the correct architectural direction even if GPU isosurfacing is not feasible.

**Technical angle:** The web worker approach maps to `QThread`/`thread_worker` in Qt. No direct code is adoptable (closed-source JavaScript), but the architecture validates C-4. One differentiator: Desmos can start a new mesh computation immediately on parameter change (sliders respond continuously), relying on the worker pool to serialize or cancel stale computations. This is the target end state for this app.

**Cross-reference:** No direct code analog. Conceptual validation of C-4 architecture.

**Impact: MEDIUM (as external validation) | Effort: N/A — pattern reference only**

---

### C-9 — SURFER (Imaginary.org) GPU Raytracing for Implicit Surfaces
**Source app:** SURFER / Imaginary.org  
**Public evidence:** https://imaginary.org/program/surfer · "Real-Time Algebraic Surface Visualization," Springer LNCS 2008 (https://link.springer.com/chapter/10.1007/978-3-540-68783-2_6, paywalled) · https://www.mathcom.wiki/index.php?title=SURFER_(IMAGINARY_exhibit)  
**License:** SURFER is proprietary; study only  

**UI/UX angle:** SURFER renders algebraic surfaces "in real time" during equation editing and parameter dragging. The key is GPU raytracing / raycasting: the surface is never tessellated into a triangle mesh — instead, a pixel shader evaluates the polynomial at each ray step. This makes every parameter change instant (the GPU re-evaluates the polynomial for the new parameter on the next frame). There is no mesh generation step at all.

**Technical angle:** SURFER's approach ("Ray Tracing Type Techniques for Rendering Algebraic Surfaces using Programmable Graphics Hardware") is fundamentally incompatible with AI-1 (PySide6+PyVista+VTK required) and AI-3 (`pv.OFF_SCREEN`). VTK's rendering pipeline works with tessellated geometry; it does not support pixel-shader implicit surface evaluation natively. Porting SURFER's GPU raytracing to VTK would require writing custom GLSL shaders injected via `vtkOpenGLRenderer` — a substantial engineering effort outside the single-developer cadence and well beyond the scope of a latency optimization. However, the SURFER architecture is the gold standard for "instant response" — it identifies the marching-cubes tessellation step as the root bottleneck that no CPU optimization can fully eliminate.

**Gating constraints:** AI-1 hard conflict (would require custom GLSL, not PyVista). AI-3 conflict (pv.OFF_SCREEN verification would not apply to a raycasting renderer). Parking-lot item: possible future exploration of VTK's shader injection API for simple polynomial surfaces.

**Cross-reference:** No analog — this is a fundamentally different rendering architecture.

**Impact: VERY HIGH (if feasible) | Effort: VERY HIGH | Risk: HIGH (AI-1 conflict) — PARKING LOT**

---

### C-10 — Numba JIT Compilation of the Scalar Field Evaluation
**Source app:** xyzcad (AGPL-3.0, study only)  
**Public evidence:** https://github.com/TheTesla/xyzcad · https://pypi.org/project/xyzcad/ · Numba docs: https://numba.pydata.org/  
**License:** Numba BSD-2-Clause (import-compatible); xyzcad AGPL-3.0 (study only, not vendored)  

**UI/UX angle:** Invisible to the user. The bottleneck in `_marching_cubes_to_polydata` is two steps: (a) scalar field evaluation (`field = f(x, y, z)` over a 150³ grid) and (b) marching cubes extraction. Numba `@njit(parallel=True)` JIT-compiles the field evaluation loop, achieving 10-120x speedup over NumPy vectorized code on CPU (depending on function complexity). The first call has compilation overhead (~0.5-2s), but subsequent calls use the cached machine code.

**Technical angle:** xyzcad uses `@njit` on user-defined `f(x,y,z)` functions. For this app's generator functions (`fermat_quartic`, `kummer_surface`, etc.) the scalar field evaluation is already vectorized with NumPy broadcasting, so the raw speedup from Numba would be modest (2-5x for simple polynomial evaluation). However, on the specific functions with expensive inner loops (e.g., `calabi_yau_dwork` which computes `x⁵ + y⁵ + z⁵`) Numba's SIMD/AVX path could be significant. The compilation overhead on first call is the main user-visible cost — acceptable if the JIT is warmed up at app startup or lazily on first surface selection (not on slider move).

**Complexity:** Medium. Wrapping each generator's field-evaluation step in `@njit` requires restructuring from NumPy vectorized expressions to explicit loops (or Numba's limited NumPy subset). The `xyzcad` approach requires defining the function separately from the generator wrapper. First-call latency is a UX risk if JIT fires during user interaction. Cache to disk with `@njit(cache=True)` mitigates this on subsequent launches.

**Gating constraints:** Numba BSD-2-Clause (import-compatible with PySide6 LGPL). AGPL risk only if vendoring xyzcad code (we do not). Apple Silicon: Numba 0.60+ supports Apple Silicon M-series with native ARM code generation (as of 2024). `@njit(parallel=True)` uses OpenMP on macOS. The marching cubes extraction step (the other half of the ~0.5s budget) is not accelerated by Numba — it remains in scikit-image's Cython. Combined with C-1 (flying edges), Numba JIT addresses the field-eval half.

**Cross-reference:** `surfaces.py:80` (the `measure.marching_cubes` call is the extraction half); the field evaluation at `surfaces.py:48-78` (implicit function sampling — this is the Numba target). Specific generators: `k3_fermat_quartic` ~line 160, `kummer_surface` ~line 200, `enriques_sextic` ~line 250, `calabi_yau_dwork` ~line 430.

**Impact: MEDIUM | Effort: MEDIUM-HIGH | Risk: MEDIUM (first-call latency, ARM support quality)**

---

### C-11 — napari `@thread_worker` Generator Pattern for Progressive Mesh Delivery
**Source app:** napari (BSD-3-Clause) / superqt (BSD-3-Clause)  
**Public evidence:** https://napari.org/dev/guides/threading.html · https://github.com/napari/napari (BSD-3-Clause) · napari 0.5.3 release notes (2024)  
**License:** napari BSD-3-Clause; superqt BSD-3-Clause  

**UI/UX angle:** A refinement of C-4 using the generator/yield pattern. The worker yields a coarse mesh first (quick), then yields the full-resolution mesh. The main thread displays each yield result. This gives the user a "fast rough preview → smooth final" experience without a separate code path: one `@thread_worker`-decorated generator handles both LOD levels.

**Technical angle:**
```python
@thread_worker
def compute_mesh(params, surface):
    # Step 1: yield a coarse preview
    coarse = surface.generate(**{**params, '_step_size': 3})
    yield ('preview', coarse)
    # Step 2: yield the full-resolution mesh
    full = surface.generate(**{**params, '_step_size': 1})
    yield ('final', full)
```
The worker checks `self.abort_requested` between yields — if a new slider move has fired, the worker exits cleanly and a new one starts. The main thread's `yielded` slot handles both the coarse and the final update. This is the cleanest architecture for combining C-2 and C-4.

**Complexity:** High (same as C-4 plus generator pattern). But the code organization is cleaner than separate coarse/full render paths.

**Gating constraints:** Same as C-4 — VTK on main thread, Cocoa constraint on macOS. The generator `yield` pattern plays well with the AI-9 guard replacement (no more `processEvents()`). superqt's `thread_worker` is actually superqt's API (which napari imports as `napari.qt.threading.thread_worker`) — directly importable from superqt BSD-3-Clause without bringing napari as a dependency.

**Cross-reference:** Same as C-4. `app.py:334-404` (`_render_current` — full replacement target).

**Impact: HIGH | Effort: HIGH | Risk: MEDIUM**

---

## 3. Sources Reviewed

| Source | URL | Type | Key Finding |
|---|---|---|---|
| Mathematica `Manipulate` docs (web search) | https://reference.wolfram.com/language/tutorial/IntroductionToManipulate.html | Official docs | Built-in LOD during drag: "jagged while dragging, improves on release" |
| Mathematica `ControlActive` docs (web search) | https://reference.wolfram.com/language/ref/ControlActive.html | Official docs | `ControlActive[fast, slow]` — the canonical two-pass pattern |
| Mathematica `SynchronousUpdating` (web search) | https://reference.wolfram.com/language/ref/SynchronousUpdating.html | Official docs | `SynchronousUpdating->False` for async non-blocking updates |
| ParaView Large Models tutorial | https://docs.paraview.org/en/latest/Tutorials/SelfDirectedTutorial/visualizingLargeModels.html | Official docs | Interactive/still render modes; LOD threshold; image subsampling |
| VTK `vtkFlyingEdges3D` reference | https://vtk.org/doc/nightly/html/classvtkFlyingEdges3D.html | VTK API docs | SMP-threaded, 1-2 orders of magnitude faster than MC |
| Kitware "Really Fast Isocontouring" | https://www.kitware.com/really-fast-isocontouring/ | Kitware blog | Flying Edges benchmarks vs. MC; "faster even in single-thread mode" |
| PyVista contouring tutorial | https://tutorial.pyvista.org/tutorial/04_filters/solutions/d_contouring.html | PyVista docs | `pv.ImageData.contour(method='flying_edges')` API usage |
| PyVista threading discussion #4006 | https://github.com/pyvista/pyvista/discussions/4006 | GitHub discussion | VTK must run on main thread; `add_mesh` not thread-safe; macOS Cocoa constraint |
| napari threading guide | https://napari.org/dev/guides/threading.html | napari docs | `@thread_worker` decorator; generator yield pattern; worker.quit() cancellation |
| napari 0.5.3 release notes | https://napari.org/dev/release/release_0_5_3.html | Release notes | Layer.get_status moved to background thread in 2024 — dramatic perf improvement |
| superqt PyPI | https://pypi.org/project/superqt/ | PyPI | BSD-3-Clause; throttling/debouncing utilities; `thread_worker` |
| superqt GitHub | https://github.com/pyapp-kit/superqt | GitHub repo | BSD-3-Clause; `FunctionWorker`, `GeneratorWorker`, `create_worker` |
| KDAB Signal Throttlers | https://www.kdab.com/signal-slot-connection-throttlers/ | Blog post | Throttle (interval) vs debounce (grace period) — 50-100ms for mesh viz |
| Desmos 3D / SIGGRAPH RTL 2025 | https://dl.acm.org/doi/10.1145/3721243.3735987 | Conference paper | Web worker pool for async CPU mesh gen; CPU MC → GPU upload; continuous slider |
| SURFER / Imaginary | https://imaginary.org/program/surfer · https://www.mathcom.wiki/index.php?title=SURFER_(IMAGINARY_exhibit) | Program page | GPU raytracing for real-time algebraic surfaces; no tessellation |
| "Real-Time Algebraic Surface Visualization" Springer | https://link.springer.com/chapter/10.1007/978-3-540-68783-2_6 | Academic paper (paywalled) | SURFER's GPU raytracing technique (fragmentary) |
| xyzcad GitHub | https://github.com/TheTesla/xyzcad | GitHub repo (AGPL-3.0) | Numba @njit for MC-based CAD; first-run compilation cost noted |
| scikit-image marching_cubes docs | https://scikit-image.org/docs/stable/auto_examples/edges/plot_marching_cubes.html | scikit-image docs | `step_size` parameter — coarser output, topologically correct |
| WebGPU Marching Cubes (Usher 2024) | https://www.willusher.io/graphics/2024/04/22/webgpu-marching-cubes/ | Blog post | GPU MC 31-54ms on M2 Max — benchmark reference |
| GeoGebra 3D (community pages) | https://www.geogebra.org/m/CSTxvXce | GeoGebra | Implicit surface slider interaction (limited technical info available) |
| SageMath three.js / interact | https://trac.sagemath.org/ticket/12402 | Trac ticket | SageMath releases-on-interact; no continuous drag update |
| QTimer debounce pattern | https://forum.qt.io/topic/157973 | Qt Forum | QTimer 200ms debounce for QSlider valueChanged |
| PySide6 QTimer docs | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html | Qt docs | Single-shot timer for debounce implementation |

---

## 4. Cross-References to This App

| File:line | Current behavior | Candidate |
|---|---|---|
| `surfaces.py:48-102` | `_marching_cubes_to_polydata` — calls `skimage.measure.marching_cubes` | C-1 (replace with `pv.ImageData.contour(method='flying_edges')`), C-6 (add `step_size` param) |
| `surfaces.py:80` | `measure.marching_cubes(field, level=level, spacing=spacing)` — single call, no step_size | C-6 (add `step_size=step_size` kwarg to enable coarse preview) |
| `parameters_panel.py:224-230` | `_on_value_changed` (live label only) and `_on_slider_released` (triggers re-render) | C-2 (add coarse-render path on `valueChanged`), C-3 (add QTimer debounce) |
| `parameters_panel.py:39-96` | `__init__` — where a `QTimer` debounce timer would be created | C-3 |
| `app.py:309-313` | `_on_params_changed` — connected to `sliderReleased` only | C-2 (add `_on_params_preview_changed` for continuous coarse updates) |
| `app.py:334-404` | `_render_current` — blocking, uses `processEvents()` | C-4, C-11 (move `surface.generate()` to background thread) |
| `app.py:339-341` | `self._computing` guard + `processEvents()` | C-4 (would remove `processEvents()` if generation is off-thread) |
| `app.py:349` | `QApplication.processEvents()` — re-entrancy source (AI-9) | C-4 (eliminate this call) |
| `app.py:357` | `self._raw_mesh = surface.generate(**params)` — cache miss every time | C-5 (insert LRU cache check here) |
| `app.py:100-103` | `_actor`, `_raw_mesh`, `_computing` instance vars | C-4/C-5 (add `_mesh_cache`, `_mesh_worker` vars here) |
| `app.py:272-307` | `_on_subtype_changed` | C-5 (cache invalidation on surface switch) |
| `parameter_grid_panel.py` | Grid dot release triggers `grid_params_changed` signal → same `params_changed` path | C-2/C-3 (same debounce/coarse path needed for grid panel dot-drag) |
| No analog | GPU raytracing for implicit surfaces | C-9 (SURFER pattern — parking lot, AI-1 conflict) |

---

## 5. Themes

**Theme 1 — Two-pass LOD is the universal pattern.**
Every scientific visualization tool surveyed that handles slow parameter-driven computations (Mathematica `Manipulate`, ParaView, Desmos 3D) converges on the same solution: a fast coarse pass during drag, a full-quality pass on release. The implementations differ (Wolfram uses `ControlActive` + `PlotPoints` reduction, ParaView uses geometric decimation + image subsampling, Desmos uses web worker async) but the UX contract is identical. This app's INT-2 (release-only) discipline is architecturally sound but leaves the "coarse preview during drag" half unimplemented.

**Theme 2 — Flying Edges is the obvious first step, already available.**
VTK's `vtkFlyingEdges3D` (available as `pv.ImageData.contour(method='flying_edges')`) is 1-2 orders of magnitude faster than `skimage.measure.marching_cubes` and is already in the dependency stack. This is a free upgrade with minimal code change. It doesn't alone make continuous updates viable but significantly shrinks the latency budget.

**Theme 3 — Async compute (background thread) is the gold standard but has high VTK-specific friction.**
Desmos, napari, and Blender geometry nodes all use async computation pipelines. For this app, the VTK-on-main-thread constraint (confirmed by PyVista discussion #4006 and macOS Cocoa requirement) means only the mesh generation step (`surface.generate()`) can move off-thread; all VTK/PyVista rendering calls must remain on the main thread. This is a real but navigable constraint.

**Theme 4 — Debouncing / throttling is table stakes for slider-driven heavy computation.**
The Qt ecosystem (KDAB, superqt, napari) uniformly recommends debouncing heavy computation triggered by `QSlider.valueChanged`. A 50-100ms QTimer debounce is a ~5-line change that prevents multiple overlapping renders during fast drags. This is lower-effort than LOD or threading and should be the first safety net even if coarse rendering is not implemented.

**Theme 5 — GPU isosurfacing (SURFER approach) eliminates the bottleneck entirely but conflicts with AI-1.**
SURFER and WebGPU MC achieve interactive algebraic surface rendering by moving the entire surface extraction to the GPU. For this app, VTK's rendering pipeline is the constraint — PyVista does not expose per-pixel shader evaluation for implicit functions. This remains a parking-lot item unless VTK's shader injection API is explored.

---

## 6. Out of Scope / Parking Lot

- **GPU pixel-shader raytracing** (SURFER approach): Real-time algebraic surface rendering by evaluating the polynomial per-pixel in a GLSL fragment shader. Requires custom `vtkOpenGLRenderer` shader injection. High effort, AI-1 boundary. Park for future exploration once the stack has been confirmed with VTK shader injection.
- **WebGPU/WebGL MC**: Relevant for a potential browser companion (trame) but out of scope for the desktop PySide6 app.
- **Maple `interactiveparams`**: Limited documentation; appears to be legacy and superseded by Maple's `Explore` command. No actionable pattern surfaced.
- **Houdini SOP parameter caching**: Houdini's geometry node caching is deep pipeline infrastructure — far beyond single-developer scope and not mappable to PyVista's actor model.
- **Incremental/adaptive marching cubes**: Updating only the voxels whose scalar values changed between parameter steps (exploiting parameter continuity). Theoretically elegant but requires per-voxel change detection and significant MC implementation work. The `step_size` coarse/fine approach (C-6) achieves similar latency reduction with much less complexity.
- **Neural/learned implicit surfaces**: Neural marching cubes, DMTet — deep learning approaches to surface extraction. Academic interest only; not applicable to the app's polynomial surface generators.
- **GeoGebra 3D internals**: GeoGebra's implicit surface solver appears to be browser-side JavaScript marching cubes. Limited technical documentation publicly available; classified as a peer reference but no extractable pattern beyond "it works."
- **3D Slicer background segmentation**: Relevant for async parameter update patterns but the medical imaging context (volume segmentation vs. algebraic surface extraction) limits direct applicability.
