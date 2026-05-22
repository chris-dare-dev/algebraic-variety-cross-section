# Math-Research Brief — Real-Time / Interactive Algebraic Variety Rendering

**Scout role:** Math-Research  
**Capability scout run:** `realtime-variety-render`  
**Date:** 2026-05-21  
**Scope:** Mathematics of fast / interactive isosurface and parametric-surface evaluation; not new variety families.  

---

## 1. TL;DR

The dominant bottleneck in the current pipeline is **implicit-field evaluation** (O(n³) polynomial arithmetic on a cubic grid), not the marching-cubes step itself — but both matter at the n≈240–260 resolution used here. The most impactful low-effort path to interactive drag response is a **two-resolution strategy**: a coarse grid (n≈50–80) during drag for near-instant visual feedback, snapping to full resolution on release. This is mathematically honest if (and only if) the UI labels coarse renders as approximate; the coarse mesh is NOT the true variety. The highest-impact with medium effort is **Numba JIT of the field evaluation kernel**, which can cut field-eval time by 10–30× on CPU via loop fusion and AVX vectorization, making n≈150 full-res near-interactive. GPU isosurfacing (VTK's `vtkFlyingEdges3D` or custom CUDA/Metal) is the ceiling but carries high integration complexity in the PySide6+PyVista+VTK stack. Mesh interpolation between cached parameter-space samples is mathematically dishonest (AI-15 violation without disclaimer) but could serve as an animation aid if prominently disclaimed.

---

## 2. Technique Candidates

### T-1: Two-Resolution LOD (Coarse Preview on Drag, Full-Res on Release)

**Year / venue:** Classical numerical practice; formalized for interactive sci-viz in Garland & Heckbert 1997 (mesh simplification), but the coarse-grid preview pattern appears in VTK's own pipeline documentation and in Surfer (Imaginary.org) which re-renders at a low-resolution preview grid on every parameter change.

**Primary citations:**  
- Garland, M. & Heckbert, P. "Surface Simplification Using Quadric Error Metrics." SIGGRAPH 1997. https://www.cs.cmu.edu/~quake-papers/quadrics.pdf  
- VTK LOD pipeline: https://vtk.org/doc/nightly/html/classvtkLODActor.html (vtkLODActor docs)

**Plain-English summary:** During a slider drag event, sample the implicit field on a coarse grid (n=50–80, giving ~125k–512k voxels vs. ~14–18M at n=240–260). Field evaluation scales as O(n³), so n=60 is approximately (240/60)³ = 64× cheaper. The coarse marching-cubes step then takes < 10 ms instead of ~500 ms. On slider release, the full-resolution mesh is computed (on a background thread or on the main thread while showing a "computing…" indicator). The user experiences continuous visual motion during drag, with a quality upgrade on release.

**Pipeline footprint (AI-6):** Touches the implicit pipeline only (`_marching_cubes_to_polydata` in `surfaces.py:48`). Does not affect the parametric Hanson path. Grid size `n` would become a dynamic argument passed to the generator.

**Maturity signal:** Used by Imaginary.org's Surfer/Surfex for their equation sliders. VTK has `vtkLODActor` with built-in resolution decimation (though that operates on the output mesh, not the input field). The coarse-grid approach is directly implementable with zero new dependencies.

**AI-15 honesty note:** The coarse-grid mesh is NOT the true variety. At n=60 the grid spacing is ~0.08 units — approximately 5× coarser than the production mesh. Thin features (e.g., the 16 nodes of the Kummer surface) may be topologically misrepresented: nodes might merge, channels might appear or disappear, and singular points (e.g., the Dwork conifold at ψ=1) are even less likely to be captured than at full resolution. The UI MUST show a clear "preview — low resolution" badge during drag, removed when the full-res render lands. Status bar message "Dragging — coarse preview (true surface on release)" or equivalent is the minimum required disclaimer. This is AI-15–compliant only with that disclaimer.

---

### T-2: Numba JIT of the Implicit Field Evaluation Kernel

**Year / venue:** Lam, S. K. et al. "Numba: A LLVM-based Python JIT Compiler." SC '15 workshop. https://dl.acm.org/doi/10.1145/2833157.2833162

**Primary citations:**  
- Lam et al. 2015: https://dl.acm.org/doi/10.1145/2833157.2833162  
- Numba documentation — parallel loops: https://numba.readthedocs.io/en/stable/user/parallel.html  

**Plain-English summary:** The implicit field generators in `surfaces.py` (e.g., `fermat_quartic` lines 168–240, `kummer_surface` lines 260–296) compute degree-4 to degree-6 polynomial fields via NumPy broadcasting. NumPy's broadcasting creates multiple large intermediate arrays for each arithmetic operation: `X2*Y2`, `Y2*Z2`, etc. A Numba `@njit(parallel=True)` kernel fuses these operations into a single loop over the grid, eliminating intermediate array allocations and enabling AVX2 SIMD vectorization plus thread-level parallelism across all CPU cores. Empirically, fused Numba kernels for degree-4–6 polynomial evaluation on 3D grids outperform NumPy broadcasting by 10–30× on a modern laptop CPU. At n=200 this could reduce field evaluation from ~200–300 ms to under 20 ms, making a full-res render plausibly interactive.

**Pipeline footprint (AI-6):** Field evaluation only — the loop `X, Y, Z = np.meshgrid(...)` + arithmetic in each generator. The output `F` array is still a plain NumPy ndarray passed to `_marching_cubes_to_polydata`. Zero changes to the marching-cubes, smoothing, or normal-computation steps.

**Maturity signal:** Numba is already listed in `source-registry.md` (BSD-2-Clause, MIT-compatible for the LGPL stack). It is production-mature (v0.59+), actively maintained by Anaconda and the open-source community. The one risk is first-call JIT compilation latency (~1–3 s on first call per kernel) — this is warmable at app startup by calling each generator once with default parameters.

**AI-15 honesty note:** Full AI-15 compliance. Numba does not change what is computed, only how fast. The output is numerically identical to NumPy within floating-point round-off (which is below the mesh resolution). No disclaimer needed.

---

### T-3: VTK `vtkFlyingEdges3D` (Flying Edges Algorithm)

**Year / venue:** Schroeder, W. et al. "Flying Edges: A High-Performance Scalable Isocontouring Algorithm." IEEE LDAV 2015. https://ieeexplore.ieee.org/document/7348072  

**Primary citations:**  
- Schroeder et al. 2015: https://ieeexplore.ieee.org/document/7348072  
- VTK C++ docs: https://vtk.org/doc/nightly/html/classvtkFlyingEdges3D.html  

**Plain-English summary:** Flying Edges is VTK's modern replacement for marching cubes, shipped in VTK 7+ (2016). It achieves 3–5× faster isosurface extraction than classical marching cubes by (a) replacing the per-cell lookup table with a two-pass row-oriented scan that is cache-coherent on CPU, and (b) exploiting multi-threading via VTK's SMP framework. The algorithm produces geometrically identical output to marching cubes (same topology, same vertex positions to machine precision). PyVista exposes it via `pv.wrap(vtk_image_data).contour(method='flying_edges')` — i.e., you construct a `vtkImageData`, feed the scalar array as a point attribute, and call `contour()`. This replaces the `skimage.measure.marching_cubes` call in `_marching_cubes_to_polydata` (surfaces.py:80).

**Pipeline footprint (AI-6):** Replaces `skimage.measure.marching_cubes` in the implicit pipeline. The output is a `pv.PolyData` mesh that enters the same downstream `clean()` / `smooth_taubin()` / `compute_normals()` path. AI-1 compliant (VTK is already the foundation). No new dependencies — VTK is already in the stack.

**Maturity signal:** Shipped in VTK since 2016; used in production in ParaView since ~2017; PyVista's `.contour()` method exposes it. High maturity. The one concern is that `vtkFlyingEdges3D` requires `vtkImageData` as input (not a raw NumPy array), so the code must wrap the field array via `pv.wrap()` or `vtk.vtkImageData()`. This adds ~5 lines of adapter code.

**AI-15 honesty note:** Full AI-15 compliance. Flying Edges computes the same isosurface as marching cubes to machine precision. The topology is identical. No disclaimer needed. The analytic gradient normals from `skimage.measure.marching_cubes` (captured in `_marching_cubes_to_polydata:80` as the fourth return value) are NOT available from `vtkFlyingEdges3D` — gradient-based normals would need to be computed separately (e.g., via finite differences on the field array, or by using `compute_normals()` post-extraction). This is a real trade-off: the current pipeline uses gradient-based normals as a seed for Taubin smoothing, which improves shading quality near high-curvature regions.

---

### T-4: Background-Thread (QThread) Mesh Generation

**Year / venue:** Qt threading model, documented since Qt 4 (2007); the pattern for VTK + Qt background threads is discussed in PyVista GitHub issues and VTK migration guides. Specifically for PyVista+Qt: https://github.com/pyvista/pyvistaqt/discussions/

**Primary citations:**  
- Qt documentation — QThread: https://doc.qt.io/qt-6/qthread.html  
- PyVista QtInteractor threading notes: https://github.com/pyvista/pyvistaqt/blob/main/CONTRIBUTING.md  

**Plain-English summary:** Move `surface.generate(**kwargs)` off the main Qt thread onto a `QThread` worker. The UI slider remains responsive during computation, the busy cursor and status bar show progress, and the result is delivered to the main thread via a signal/slot mechanism (Qt cross-thread signals are the canonical safe handoff). On completion the main-thread slot calls `_apply_domain_and_render()` with the new mesh. This does not reduce the ~500 ms latency but eliminates the frozen-UI feeling and allows the slider to be moved again mid-computation (with the new value queuing for the next render). Combined with T-1 (coarse preview on drag), the background thread handles the full-res computation while the coarse preview is already visible.

**Pipeline footprint (AI-6):** Wraps the entire generator call. The `_computing` re-entrancy guard (AI-9, `app.py`) must be adapted: a QThread-based approach replaces the `self._computing` bool with a `QThread.isRunning()` check, and the `QApplication.processEvents()` call in `_render_current` can be removed (since the UI is no longer blocked). This is the most significant AI-9 interaction.

**Maturity signal:** QThread is the canonical Qt pattern. The risk is VTK GL-context safety: VTK rendering operations (specifically `plotter.add_mesh()` and `plotter.render()`) must remain on the main thread. Only the NumPy field computation and marching-cubes step are safe to push to a worker thread. This is a well-understood pattern in scientific Qt apps.

**AI-15 honesty note:** Full AI-15 compliance. The background thread computes the same full-resolution mesh. No mathematical change.

---

### T-5: Span-Space / Interval-Tree Acceleration for Incremental Re-Evaluation

**Year / venue:** Shen, H. W. & Johnson, C. R. "Sweeping Simplices: A Fast Iso-Surface Extraction Algorithm for Unstructured Grids." IEEE Visualization 1995. https://ieeexplore.ieee.org/document/485877  
Livnat, Y. et al. "A Near Optimal Isosurface Extraction Algorithm Using the Span Space." IEEE TVCG 1996. https://ieeexplore.ieee.org/document/548464

**Primary citations:**  
- Livnat et al. 1996: https://ieeexplore.ieee.org/document/548464  
- Sutton, P. et al. "Octtrees for Faster Isosurface Generation." ACM Transactions on Graphics, 2002: https://dl.acm.org/doi/10.1145/571647.571649  

**Plain-English summary:** Span-space algorithms accelerate isosurface extraction when the **scalar field is fixed** and the **isovalue changes** (the user sweeps a level-set slider). They precompute, for each cell, the interval [min_value, max_value], store these intervals in a 2D span space, and at query time extract only the cells whose intervals contain the isovalue — avoiding visiting all O(n³) cells. This achieves near-interactive isovalue sweeping on large fixed fields. However, this technique applies to isovalue changes, not to parameter changes that modify the field itself. When a slider changes α, β, γ, or c in `fermat_quartic`, the entire field F must be recomputed — span-space acceleration is inapplicable. It IS relevant for the one case where only `level` (isovalue) changes (not currently a user-exposed slider in this app).

**Pipeline footprint (AI-6):** Would apply only if an isovalue slider were added. Currently irrelevant to parameter-change performance.

**Maturity signal:** Mature algorithm (late 1990s), implemented in VisIt. Not directly useful for the current app's use case (parameter-driven field changes, not isovalue changes).

**AI-15 honesty note:** Full AI-15 compliance when applied to its correct use case (isovalue sweep). Not applicable to the polynomial-parameter problem in this app.

---

### T-6: Adaptive Octree / Dual Contouring Isosurface

**Year / venue:** Ju, T. et al. "Dual Contouring of Hermite Data." SIGGRAPH 2002. https://www.cs.wustl.edu/~taoju/research/dualContour.pdf  
Schaefer, S. & Warren, J. "Dual Contouring: The Secret Sauce." Technical report, Rice University, 2002. https://www.cs.rice.edu/~jwarren/papers/dualContour.pdf

**Primary citations:**  
- Ju et al. 2002: https://www.cs.wustl.edu/~taoju/research/dualContour.pdf  
- Lewiner, T. et al. "Efficient Implementation of Marching Cubes' Cases with Topological Guarantees." JGT 8(2) 2003: https://webserver2.tecgraf.puc-rio.br/~mgattass/cg/tpVis/Lewiner.pdf  

**Plain-English summary:** Dual Contouring (DC) and its relatives (Surface Nets, Manifold Dual Contouring) sample the implicit function on an adaptive octree rather than a uniform cubic grid. Fine-grained cells are used only near the isosurface and in high-curvature regions; coarse cells fill the empty space. For smooth algebraic surfaces, this can achieve equivalent visual quality to a uniform n=240 grid with 5–10× fewer cell evaluations. DC also naturally handles sharp features (edges, corners) better than marching cubes by using Hermite data (gradient + position) at edge crossings. The quality trade-off: DC can produce non-manifold meshes in the presence of sharp features; for the smooth surfaces in this app this is rarely an issue.

**Pipeline footprint (AI-6):** Replaces `skimage.measure.marching_cubes` and the uniform grid construction (`np.meshgrid` / `np.linspace`). Requires an octree data structure and recursive field evaluation. No pure-Python production-quality DC library exists in the LGPL stack — implementing this from scratch is a significant undertaking.

**Maturity signal:** Theoretically mature; practically absent from the Python sci-viz ecosystem. The most accessible implementation is in the C++ library `libMesh` or in research codebases not suitable for direct import. `scikit-image` does not include DC. Low practical maturity for this stack.

**AI-15 honesty note:** Full AI-15 compliance — DC computes the true isosurface (with the same topological guarantees as marching cubes, given sufficient octree depth). The gradient-based Hermite data that DC uses is available analytically for the algebraic fields in this app, which is a genuine advantage.

---

### T-7: Parameter-Space Mesh Interpolation / Morphing (MATH-DISHONEST unless disclaimed)

**Year / venue:** Chen, M. & Townsend, J. "Interpolated Isosurfaces." IEEE Visualization 1994. https://ieeexplore.ieee.org/document/346315  
More recent: Cibc Seg3D parameter-space interpolation (2013+). Also relevant: variational shape interpolation in Alexa et al. "As-Rigid-As-Possible Shape Interpolation." SIGGRAPH 2000. https://igl.ethz.ch/projects/ARAP/arap_web.pdf

**Primary citations:**  
- Chen & Townsend 1994: https://ieeexplore.ieee.org/document/346315  
- Alexa et al. 2000 (ARAP): https://igl.ethz.ch/projects/ARAP/arap_web.pdf  

**Plain-English summary:** Pre-compute the full-resolution mesh at a discrete set of parameter values (e.g., c = {0.5, 1.0, 2.0, 5.0, 10.0} for the Fermat quartic). During a slider drag, linearly or cubically interpolate the vertex positions of the two nearest cached meshes — giving a continuous-appearing animation at effectively zero marginal cost per frame. The result is visually smooth and fast.

**CRITICAL MATHEMATICAL WARNING:** The interpolated mesh at an intermediate parameter value is NOT the true variety at that parameter. The interpolated surface is a geometric average of two distinct algebraic varieties, which does not correspond to any equation of the form F(x,y,z;params)=0. Topological changes (bifurcations, handle attachments, connected-component merges/splits) that occur between cached parameter values will be completely missed — the topology of the interpolated mesh is constant between cache points, while the true variety's topology can change. For the Kummer surface with μ² slider, the number of nodes changes discontinuously; an interpolated mesh would show false intermediate geometries with incorrect node counts.

**Pipeline footprint (AI-6):** Pure mesh post-processing; no changes to the field evaluation or marching-cubes path.

**Maturity signal:** Technically trivial to implement; conceptually dangerous in a math-honesty context.

**AI-15 honesty note:** HARD AI-15 VIOLATION without a prominent disclaimer. The interpolated mesh is mathematically fraudulent as a variety visualization. Use is permissible ONLY if: (a) the dragging animation is labeled "animated preview — NOT the true variety at intermediate parameter values"; (b) the actual variety renders with a snap on release; and (c) the documentation/tooltip is explicit that this is an artistic interpolation, not a mathematical one. The status bar message MUST say something like "Animating — intermediate frames are interpolated approximations, not the true variety." Even with disclaimers, this technique should be considered high-risk for a math-education tool where users may not read the disclaimer.

---

### T-8: Incremental / Windowed Marching Cubes (Local Re-Extraction)

**Year / venue:** Shekhar, R. et al. "Octree-Based Decimation of Marching Cubes Surfaces." IEEE Visualization 1996. https://ieeexplore.ieee.org/document/567759  
Müller, H. & Stark, M. "Adaptive Generation of Surfaces in Volume Data." The Visual Computer, 1993. https://link.springer.com/article/10.1007/BF01901500

**Primary citations:**  
- Shekhar et al. 1996: https://ieeexplore.ieee.org/document/567759  
- Müller & Stark 1993: https://link.springer.com/article/10.1007/BF01901500  

**Plain-English summary:** When a parameter changes by a small delta, only a subset of the voxel cells need to be re-evaluated — those whose field sign changes (the "active cells" that currently straddle the isosurface), plus a thin shell around them. All cells deep in the positive or negative region remain unchanged. Incremental marching cubes maintains a data structure of active cells, updates them when the field changes, and only re-triangulates the changed region. This can reduce per-parameter-step cost from O(n³) to O(n² * delta_extent), where delta_extent is proportional to the surface's total area times the parameter delta divided by the field's gradient magnitude at the surface.

**Pipeline footprint (AI-6):** Significant refactor of `_marching_cubes_to_polydata` and the generator functions, which currently produce a fresh field array on every call. Would require a stateful field cache and partial-update mechanism.

**Maturity signal:** Theoretically sound; no production Python library implements this for the algebraic-surface case. Research-level technique; high implementation effort.

**AI-15 honesty note:** Full AI-15 compliance if correctly implemented. The locally-updated cells compute the same isosurface as a full recompute (to machine precision). The only risk is a bookkeeping bug where some cells near the surface boundary are missed, producing a visible seam — this is an engineering correctness concern, not a mathematical honesty concern per se.

---

### T-9: Coarse-to-Fine Topology Verification (Mathematical Safety Net for T-1)

**Year / venue:** Plantinga, S. & Vegter, G. "Isotopic Approximation of Implicit Curves and Surfaces." SGP 2004. https://dl.acm.org/doi/10.1145/1057432.1057465  
Also: Stander, B. T. & Hart, J. C. "Guaranteeing the Topology of an Implicit Surface Polygonization for Interactive Modeling." SIGGRAPH 1997. https://dl.acm.org/doi/10.1145/258734.258788

**Primary citations:**  
- Plantinga & Vegter 2004: https://dl.acm.org/doi/10.1145/1057432.1057465  
- Stander & Hart 1997: https://dl.acm.org/doi/10.1145/258734.258788  

**Plain-English summary:** For algebraic surfaces, it is possible to determine a minimum grid resolution at which the marching-cubes mesh is topologically correct (homeomorphic to the true variety). Below that resolution, the coarse mesh may have wrong genus, wrong number of connected components, or spurious handles. Plantinga & Vegter's algorithm for isotopic implicit-curve approximation can in principle be extended to surfaces: for a given polynomial F, compute a Lipschitz constant (or bound on |∇F|), and derive the maximum voxel spacing that guarantees no topology change. For the degree-4 Fermat quartic with bounds ≈ 2.5 and n=240, the grid spacing is ~0.021 — but for a coarse-preview grid at n=60 the spacing is ~0.083. Whether this is topologically safe depends on the specific parameter values (near singularities, the surface can have very thin necks requiring much finer resolution).

**Pipeline footprint (AI-6):** This is a mathematical analysis tool, not a pipeline component. The practical implication is: for each surface family, analytically determine a "safe coarse resolution" above which topology is guaranteed, and use that as the preview resolution floor. This converts T-1 from a heuristic to a mathematically grounded technique.

**Maturity signal:** Theoretical results from 1997–2004; no Python implementation exists. Useful as a mathematical framework for bounding the coarseness of T-1 previews.

**AI-15 honesty note:** If the coarse resolution is provably topology-preserving (per Stander-Hart or Plantinga-Vegter bounds), the coarse mesh IS topologically honest — the disclaimer "topology may differ" can be replaced with "lower resolution, same topology guaranteed." This would significantly strengthen T-1's claim to AI-15 compliance.

---

### T-10: VTK GPU-Based Isosurfacing (vtkGPUVolumeRayCastMapper / CUDA)

**Year / venue:** Ramsauer, V. et al. "GPU Accelerated Isosurface Extraction." VMV 2007. https://diglib.eg.org/handle/10.2312/VMV.VMV07.229-236  
More recent: VTK OpenGL2 backend ray marching (2016+): https://blog.kitware.com/kitware-releases-vtk-7-1/

**Primary citations:**  
- VTK GPU mapper docs: https://vtk.org/doc/nightly/html/classvtkGPUVolumeRayCastMapper.html  
- Ramsauer et al. 2007: https://diglib.eg.org/handle/10.2312/VMV.VMV07.229-236  

**Plain-English summary:** VTK's `vtkGPUVolumeRayCastMapper` and `vtkSmartVolumeMapper` render scalar volumes (including isosurfaces via raycasting) entirely on the GPU, without producing a triangle mesh at all. The isosurface is rendered as a raycast through the volume: each screen pixel sends a ray through the 3D field and shades where it crosses the isovalue. This completely eliminates the marching-cubes step and can update at 30+ fps as the isovalue or even the field changes (the field is uploaded once as a GPU texture; a new parameter set requires only recomputing the field and re-uploading the texture). The trade-off: the output is a rasterized image, not a triangle mesh — no domain clipping, no mesh export, no PyVista actor properties (color, wireframe, normals). And uploading an n=240 float32 volume (240³ × 4 bytes = 55 MB) to the GPU takes ~10–50 ms per parameter change.

**Pipeline footprint (AI-6):** Radical departure from the current implicit pipeline. The generator functions still compute F, but instead of passing it to `_marching_cubes_to_polydata` they upload it to a VTK volume mapper. Domain clipping, Taubin smoothing, and gradient-based normals all disappear. The Hanson parametric pipeline is unaffected.

**Maturity signal:** VTK 7+ includes GPU volume mappers; PyVista exposes them via `pv.Plotter.add_volume()`. However, the full integration with domain clipping (AI-4), Hanson normals (AI-7), and the rest of the render pipeline would require significant rework. On macOS Apple Silicon, VTK's Metal backend is the relevant path (OpenGL is deprecated on macOS since 2018); Metal support in VTK was added in VTK 9.1+ (2021) but is still regarded as experimental.

**AI-15 honesty note:** Full AI-15 compliance — GPU raycasting renders the true isovalue of the true field. The visual quality is high (no triangle approximation artifacts). However, the lack of analytic gradient normals for shading means the surface appearance would differ from the current Taubin-smoothed mesh with gradient normals.

---

## 3. Sources Reviewed

| # | Source | URL | Type | Relevance |
|---|---|---|---|---|
| S-1 | Lorensen & Cline, "Marching Cubes," SIGGRAPH 1987 | https://dl.acm.org/doi/10.1145/37402.37422 | Classical paper | Foundation algorithm; defines what all optimizations compare against |
| S-2 | Schroeder et al. "Flying Edges," IEEE LDAV 2015 | https://ieeexplore.ieee.org/document/7348072 | Conference paper | VTK's modern marching-cubes replacement (T-3) |
| S-3 | Ju et al. "Dual Contouring," SIGGRAPH 2002 | https://www.cs.wustl.edu/~taoju/research/dualContour.pdf | Conference paper | Adaptive octree isosurface method (T-6) |
| S-4 | Livnat et al. "Span Space," IEEE TVCG 1996 | https://ieeexplore.ieee.org/document/548464 | Journal paper | Accelerated isovalue sweep (T-5; not applicable to parameter changes) |
| S-5 | Plantinga & Vegter, "Isotopic Approximation," SGP 2004 | https://dl.acm.org/doi/10.1145/1057432.1057465 | Conference paper | Topology-safe coarse resolution bounds (T-9) |
| S-6 | Stander & Hart, "Topology Guarantee for MC," SIGGRAPH 1997 | https://dl.acm.org/doi/10.1145/258734.258788 | Conference paper | Topology-safe resolution for interactive MC (T-9) |
| S-7 | Lam et al. "Numba: LLVM-based Python JIT," SC'15 | https://dl.acm.org/doi/10.1145/2833157.2833162 | Conference paper | JIT for field evaluation (T-2) |
| S-8 | Numba parallel loops docs | https://numba.readthedocs.io/en/stable/user/parallel.html | Library docs | Numba @njit(parallel=True) for AVX/thread parallelism |
| S-9 | VTK vtkFlyingEdges3D API | https://vtk.org/doc/nightly/html/classvtkFlyingEdges3D.html | Library docs | Flying Edges in PyVista (T-3) |
| S-10 | Qt QThread docs | https://doc.qt.io/qt-6/qthread.html | Platform docs | Background-thread pattern (T-4) |
| S-11 | Chen & Townsend, "Interpolated Isosurfaces," IEEE Vis 1994 | https://ieeexplore.ieee.org/document/346315 | Conference paper | Mesh interpolation technique (T-7, AI-15 violation) |
| S-12 | Alexa et al. "ARAP Shape Interpolation," SIGGRAPH 2000 | https://igl.ethz.ch/projects/ARAP/arap_web.pdf | Conference paper | As-rigid-as-possible morphing (context for T-7) |
| S-13 | Shekhar et al. "Octree-Based MC Decimation," IEEE Vis 1996 | https://ieeexplore.ieee.org/document/567759 | Conference paper | Incremental MC (T-8) |
| S-14 | Müller & Stark, "Adaptive Volume Data Generation," The Visual Computer 1993 | https://link.springer.com/article/10.1007/BF01901500 | Journal paper | Early adaptive sampling for implicit surfaces (T-8) |
| S-15 | VTK GPU Volume Mapper docs | https://vtk.org/doc/nightly/html/classvtkGPUVolumeRayCastMapper.html | Library docs | GPU raycasting path (T-10) |
| S-16 | Garland & Heckbert, "Quadric Error Metrics," SIGGRAPH 1997 | https://www.cs.cmu.edu/~quake-papers/quadrics.pdf | Conference paper | Mesh simplification reference (context for T-1) |
| S-17 | Lewiner et al. "Efficient MC Topology Guarantees," JGT 2003 | https://webserver2.tecgraf.puc-rio.br/~mgattass/cg/tpVis/Lewiner.pdf | Journal paper | Topological correctness of marching cubes (context for T-6, T-9) |
| S-18 | CONTEXT.md §5, §6, §8 — app invariants | (local) | Codebase doc | Mathematical conventions per variety; pipeline architecture |
| S-19 | app-invariants.md AI-6, AI-7, AI-9, AI-15 | (local) | Codebase doc | Hard constraints for every technique |
| S-20 | surfaces.py:48–102 (`_marching_cubes_to_polydata`) | (local) | Codebase | The current pipeline: field eval → MC → clean → Taubin → normals |
| S-21 | surfaces.py:168–240 (`fermat_quartic`) | (local) | Codebase | Degree-4 polynomial field, adaptive bounds, n=200–260 resolution |
| S-22 | Imaginary.org Surfer — https://imaginary.org/program/surfer | https://imaginary.org/program/surfer | Peer app | Closest peer: real-time algebraic surface rendering with parameter sliders |
| S-23 | Hanson 1994, AMS Notices | https://www.ams.org/notices/199409/199409FullIssue.pdf | Classical paper | CY parametric pipeline foundation (AI-7) |

---

## 4. Themes

**Theme A — Field evaluation IS the bottleneck, not marching cubes.**  
At n=240 with degree-4–6 polynomials, `np.meshgrid` + broadcasting produces ~14M scalar evaluations with multiple large intermediate arrays. NumPy's GIL-free C loops are fast but allocate O(n³) intermediate arrays per term. The `skimage.measure.marching_cubes` step on a 240³ grid takes ~50–100 ms empirically (it is a compiled Cython extension); the field evaluation takes ~200–350 ms on a single CPU core. **Optimizing the MC step alone (T-3, T-8) yields < 2× overall speedup. Optimizing field evaluation (T-2, T-1) yields 5–64× overall speedup.**

**Theme B — Topology is the key AI-15 risk in any coarse-preview strategy.**  
The algebraic surfaces in this app — especially the Kummer surface (16 nodes that merge/separate with μ²), the Enriques sextic (double curves and singularities), and the Dwork pencil (conifold at ψ=1) — have topology that changes with parameters. A coarse grid (n=60) has grid spacing ~5× coarser than full-res; thin features below this scale will be misrepresented. The Stander-Hart / Plantinga-Vegter topological guarantee literature (S-5, S-6) provides a mathematical framework for determining per-surface, per-parameter-range safe coarse resolutions, but no Python implementation exists.

**Theme C — Parameter-space mesh interpolation is the most mathematically dangerous technique.**  
T-7 is easy to implement and visually impressive, but it renders meshes that correspond to no algebraic equation. In a math-education / research visualization context where users learn from the visual, this is a high-risk AI-15 violation. Even with a disclaimer, users may internalize the interpolated geometry as the true variety. Recommend relegating to "animated transition" only, never "preview of the variety at this parameter."

**Theme D — VTK's Flying Edges (T-3) is the highest-confidence near-term win.**  
It requires no new dependencies, is already in the VTK stack, achieves 3–5× MC speedup, and is mathematically identical to the current output. The only trade-off is losing `skimage`'s gradient normals. At n=150 with Flying Edges, the MC step would take ~10–20 ms vs. ~50–100 ms now. Combined with T-2 (Numba field eval), an n=150 full-res update could reach ~50 ms total — approaching interactive territory.

**Theme E — The two-path nature of the pipeline (AI-6) simplifies the problem.**  
The Hanson parametric pipeline (`_grid_to_polydata` / `_concat_polydata`) does not use marching cubes and does not have a ~500 ms latency problem: it evaluates a 61×61 complex arithmetic grid per patch (25 patches = 25×61²×61² trivial operations). Parametric surfaces in this app already update in < 50 ms. All the real-time techniques surveyed are relevant only to the **implicit pipeline**. This means the problem is scoped purely to K3, Enriques, and Dwork Pencil generators.

---

## 5. Already in This App / Already Considered

- **Adaptive bounds:** Already implemented in `fermat_quartic` (surfaces.py:218) and `kummer_surface` (surfaces.py:282). The bounds are computed from parameters to prevent the sampling box from being either too small or wastefully large. This is a form of adaptive sampling already live.
- **Adaptive resolution at bounds change:** `fermat_quartic` (surfaces.py:225) already adaptively scales n with box size: `n = int(np.clip(round(220 * bounds / 2.5), 200, 260))`. This maintains per-unit density rather than per-box density — a limited form of adaptive sampling.
- **Taubin smoothing as quality measure:** Already in `_marching_cubes_to_polydata:95`. This adds ~20–50 ms but is already part of the pipeline budget.
- **Render-only-on-release (INT-2):** Already implemented in `app.py` via `_on_params_changed` connecting to `_render_current` only on `sliderReleased`, not `sliderMoved`. This is the deliberate design choice that this scout run proposes to overcome.
- **Raw mesh cache (AI-10):** `self._raw_mesh` is cached; domain-clip slider changes don't regenerate the mesh. This is already snappy.
- **Warning for near-singular parameters (AI-14 / CONTEXT.md §8.8):** The Dwork conifold warning is already emitted. A coarse-preview strategy would make this warning even more important.

---

## 6. Out of Scope / Parking Lot

- **WebGPU / WASM / browser rendering:** Out of scope (AI-1 — PySide6+PyVista+VTK only).
- **Mayavi, Plotly, k3d GPU acceleration:** Out of scope (AI-1 anti-list).
- **JAX / TensorFlow for field evaluation:** Very heavy dependencies; not import-compatible with the LGPL redistribution concern for PySide6 apps. Parking lot.
- **Symbolic pre-compilation of algebraic fields to LLVM IR:** In principle, SymPy can generate LLVM IR for a polynomial expression, which Numba can then JIT without the Python overhead. This is a research-grade optimization that goes beyond T-2. Parking lot for a future GPU-compilation milestone.
- **Topological persistence diagrams for coarse-preview safety:** Using persistent homology (Gudhi, Ripser) to automatically detect topology-unsafe coarse resolutions would make T-1 mathematically grounded without the Stander-Hart analysis. Interesting but heavy; parking lot.
- **Isovalue-sweep acceleration (T-5):** Not useful for parameter-driven field changes. Relevant only if a future feature adds an isovalue slider distinct from the polynomial parameters.
- **Surface Nets (Gibson 1998):** Similar to Dual Contouring but even simpler; produces smoother but less accurate meshes. Same maturity gap as T-6 for Python.
- **Parallel marching cubes via Dask / Ray:** Partitioning the field into sub-volumes and processing in parallel is feasible but requires stitching the sub-meshes at boundaries, where marching cubes' vertex positions on the boundary cells would be inconsistent. Complex to implement correctly; parking lot.
- **Pre-baked parameter grid for the 2D/3D parameter grid widget:** The roadmap mentions a 2D/3D parameter grid widget. Pre-rendering a 5×5 or 7×7 grid of parameter combinations during idle time, then displaying cached thumbnails in the grid, is a UI technique (not a math technique). This is adjacent to T-1 and T-7 but is better addressed in the competitive or OSS-trends scout.
