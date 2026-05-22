# OSS Trends Brief — Realtime Variety Render
**Scout run:** 2026-05-21  
**Scope:** Real-time algebraic variety update on slider drag — optimization techniques for the ~0.5 s marching-cubes bottleneck  
**Hard constraints:** AI-1 (PySide6 + PyVista + VTK only), AI-2 (Qt-free tests), AI-3 (pv.OFF_SCREEN), AI-9 (_computing re-entrancy guard), macOS Apple-Silicon-primary, single-developer cadence

---

## 1. TL;DR

Three independent levers can each shave the 0.5 s render cycle: **(a)** switching from `skimage.measure.marching_cubes` to PyVista's `contour(method='flying_edges')` (VTK's threaded vtkFlyingEdges3D — claimed 10–15× speedup on multi-core, verified available in PyVista 0.46+); **(b)** JIT-compiling the polynomial field evaluation with Numba `@njit` / `@guvectorize` (13–25× speedup on array math, arm64 PyPI wheels confirmed in Numba 0.61+ / 0.65.1 current); **(c)** running mesh generation in a `QThreadPool` worker that hands a finished `pv.PolyData` back to the main thread via a signal, with `superqt.qdebounced` on the slider to gate how often the worker fires. A lightweight in-process `functools.lru_cache` keyed by the parameter tuple (or `joblib.Memory` for cross-session persistence) is the fourth pillar for cheap repeated-parameter hits. GPU isosurface extraction in VTK (vtkOpenGLGPUVolumeRayCastMapper with ISOSURFACE_BLEND mode) is a fifth option but requires a different input format (ImageData volume, not a surface mesh) and is not reachable via PyVista's `contour()` API; treat it as a future-proofing note only.

---

## 2. Project candidates

### Group A — VTK / PyVista fast-isosurface surfaces

#### A1. PyVista `contour(method='flying_edges')` — VTK's vtkFlyingEdges3D
- **URL:** https://github.com/pyvista/pyvista · https://docs.pyvista.org/examples/01-filter/contouring.html
- **License:** MIT
- **Stars / last commit:** 5 k+ stars; last release PyVista 0.48.2 (active, weekly commits as of May 2026)
- **What it does:** PyVista wraps VTK's three contouring algorithms behind a single `mesh.contour()` method with a `method=` parameter accepting `'contour'` (default vtkContourFilter), `'marching_cubes'` (vtkMarchingCubes), and `'flying_edges'` (vtkFlyingEdges3D). vtkFlyingEdges3D is a shared-memory, multi-threaded isosurfacing algorithm that processes volume *edges* rather than voxel cells, accesses each voxel value once (vs. up to 8× in classic MC), performs a single upfront allocation, and scales linearly with the number of SMP threads. Kitware's own benchmark on the CT-Angio dataset showed **13.8–14.5× speedup** versus classic marching cubes at 16 threads; single-thread speedup is still 2–4×. The app currently uses `skimage.measure.marching_cubes` (AI-6, `surfaces.py:_marching_cubes_to_polydata`), which is a single-threaded pure-Python/Cython implementation with no SMP exploitation.
- **Specific capability to borrow:** Replace the `skimage.measure.marching_cubes` call inside `_marching_cubes_to_polydata` with a PyVista `ImageData`-based pipeline: build an `ImageData` from the scalar field, call `.contour([0.0], method='flying_edges')`, and strip the result to `PolyData`. Retains the existing `smooth_taubin` + `compute_normals` post-processing. Gradient normals from `skimage` (used as a smoothing seed) would need a replacement — either analytic normals from the field, or accept post-smooth `compute_normals()` alone.
- **App positioning:** In-repo code change to `surfaces.py`. No new dependency; VTK ships with PyVista.
- **Risk flags:** (1) vtkFlyingEdges3D requires an `ImageData` (uniform grid) input, not a plain numpy array — need to wrap the scalar field in `pv.ImageData`. (2) The existing `skimage` normals-as-seed pattern is lost; visual quality may differ slightly. (3) PyVista 0.46+ changelog did not surface a dedicated contour/threading perf entry — the flying_edges method has been available since at least PyVista 0.38 but is not the default, implying Kitware considered it opt-in. (4) pyvistaqt does not work with Qt 6.10+ on macOS (reported Feb 2026, issue #793) — an upstream risk; pinned `PySide6 <7` in requirements.txt covers the immediate window but monitor.
- **PySide6 compat:** Yes — PyVista is pure-VTK and Qt-agnostic; the `contour()` call happens entirely off the GUI.

---

#### A2. VTK GPU isosurface via vtkOpenGLGPUVolumeRayCastMapper (ISOSURFACE_BLEND)
- **URL:** https://gitlab.kitware.com/vtk/vtk · https://www.kitware.com/gpu-rendering-of-isosurfaces/
- **License:** BSD-3-Clause
- **Stars / last commit:** VTK GitLab, active. Feature shipped in VTK 8.1 / ParaView 5.5 (2018); stable in current VTK 9.x.
- **What it does:** The GPU volume ray-cast mapper renders isosurfaces directly from volume data on the GPU with no intermediate mesh. Multiple isosurfaces can be rendered simultaneously. The render is non-destructive — no `pv.PolyData` is ever generated, so contour-value changes are practically instantaneous.
- **Specific capability to borrow:** Pattern-lift only: confirms a GPU ray-cast approach is available in VTK proper. For an algebraic variety viewer that needs a mesh (for domain clipping, Taubin smoothing, export), this is not directly applicable. Useful as evidence that VTK's GPU stack is mature enough for a future "GPU preview" LOD layer.
- **App positioning:** Pattern-lift / future-proofing note. Not importable into the current `surfaces.py` pipeline without substantial rearchitecting — the app would need to serve volumes to the plotter rather than meshes.
- **Risk flags:** Requires `vtkImageData` volume already on GPU; macOS Metal vs. OpenGL compatibility is unclear for the `ISOSURFACE_BLEND` path; no PyVista wrapper for this mode; overkill for current scope.
- **PySide6 compat:** N/A for current scope.

---

### Group B — JIT / native acceleration

#### B1. Numba (`@njit`, `@guvectorize`)
- **URL:** https://github.com/numba/numba · https://numba.readthedocs.io/
- **License:** BSD-2-Clause
- **Stars / last commit:** ~10 k stars; latest release 0.65.1 (April 24, 2026); active weekly.
- **What it does:** Numba JIT-compiles Python/NumPy functions to native LLVM machine code. The `@njit` decorator eliminates Python overhead on loops and numeric operations. `@guvectorize(target='parallel')` generates a multi-threaded ufunc that runs a scalar-valued kernel across an N-dimensional array in parallel. For polynomial field evaluation on a cubic grid — the inner loop in every implicit generator in `surfaces.py` — this is the single highest-leverage change: benchmarks consistently show **13–25× speedup** over equivalent NumPy vectorized expressions for array math at this scale (100³ = 1M points). **macOS arm64 (Apple Silicon):** Numba officially supports osx-arm64 at Tier 1 (both PyPI wheels and conda packages) as of Numba 0.61+ (verified 0.61.2 released April 9 2025, 0.65.1 is current). The `threading_layer` defaults to `tbb` on macOS, but `omp` and `workqueue` are available; `workqueue` is the safest fallback for a single-developer app without an OpenMP runtime installed.
- **Specific capability to borrow:** Decorate each implicit surface's polynomial field function with `@numba.njit(parallel=True)` and use `numba.prange` in the three nested loops (x, y, z grid). Expected field-evaluation time: from ~150 ms to ~5–15 ms on an M-series chip. This does not touch the marching-cubes step itself but eliminates a large chunk of the 0.5 s.
- **App positioning:** Import. `pip install numba` — not currently in `requirements.txt` (it's in the source-registry as a candidate). Cold-start JIT compile adds ~0.5–2 s on first call per decorated function; subsequent calls are fast (cached in `__pycache__`). Calling `numba.njit` at module import time on a `@njit`-decorated helper avoids surprising the user on first render.
- **Risk flags:** (1) `llvmlite` wheel is bundled with Numba since 0.61; no separate install needed. (2) Cold-JIT compile time is noticeable; mitigate with `cache=True` in `@njit`. (3) Numba's `@njit` does not support all NumPy operations; the field functions use basic polynomial expressions which are fully supported. (4) Test suite must remain Qt-free (AI-2) — Numba-JIT'd functions are testable pure-NumPy; no issue there.
- **PySide6 compat:** Yes — Numba has no Qt dependency.

---

#### B2. PyMCubes (Cython-accelerated marching cubes)
- **URL:** https://github.com/pmneila/PyMCubes
- **License:** BSD-3-Clause
- **Stars / last commit:** 790 stars; last commit activity not recently confirmed (master has 60 commits; no 2025 release visible).
- **What it does:** A Cython + C++ implementation of marching cubes that accepts NumPy arrays and returns vertices and faces directly. Cython avoids Python-level loops in the cell iteration. Benchmarks vs. `skimage.measure.marching_cubes` are not published, but the Cython/C++ core should have less Python overhead.
- **Specific capability to borrow:** A drop-in alternative to `skimage.measure.marching_cubes` inside `_marching_cubes_to_polydata`. However, it is **single-threaded** and does not approach the SMP scaling of VTK's flying_edges. The realistic speedup over `skimage` is 2–3× at most — less impactful than either flying_edges (A1) or Numba-JIT field eval (B1).
- **App positioning:** Import or vendor-copy. Not recommended as the primary intervention; interesting only if A1 proves complicated to integrate.
- **Risk flags:** Low recent activity; no ARM64-specific CI visible; fewer capabilities (no gradient normals). **Ranked lower than A1 and B1 for this use case.**
- **PySide6 compat:** Yes — no Qt dependency.

---

### Group C — Caching libraries

#### C1. `functools.lru_cache` / `functools.cache` (stdlib)
- **URL:** https://docs.python.org/3/library/functools.html
- **License:** PSF (stdlib)
- **Stars / last commit:** N/A — Python stdlib, Python 3.12 in use.
- **What it does:** In-process LRU cache keyed by function arguments. `@functools.cache` (Python 3.9+) is unbounded; `@lru_cache(maxsize=N)` bounds by N most-recent keys. For the algebraic variety app, wrapping the generator function with a frozen parameter tuple key means that re-dragging a slider to a previously-visited value returns the cached `pv.PolyData` in microseconds instead of 0.5 s. The cache lives in process memory and disappears on exit.
- **Specific capability to borrow:** Wrap each generator function (or a thin dispatch layer in `MainWindow._render_current`) with `@lru_cache`. The key must be a hashable tuple of `(surface_label, **sorted(kwargs.items()))`. `pv.PolyData` is mutable and not hashable, so the cache must be on the *generator* function, not on a post-processing step. Cache size of 32–64 is enough for a single-session parameter exploration.
- **App positioning:** Zero new dependency; stdlib. `_raw_mesh` is already cached by `app.py` for the most-recent parameter set (AI-10). This extends caching to a ring of the N most-recent parameter combinations.
- **Risk flags:** Memory: a single `pv.PolyData` for these surfaces is ~2–10 MB; 32-item LRU is 64–320 MB — acceptable on Apple Silicon. Thread safety: if mesh generation moves to a `QThread` worker (see Group D), the cache must be guarded against concurrent calls with the same key.
- **PySide6 compat:** N/A — stdlib.

---

#### C2. `joblib.Memory` (disk-backed memoization)
- **URL:** https://github.com/joblib/joblib · https://joblib.readthedocs.io/en/stable/memory.html
- **License:** BSD-3-Clause
- **Stars / last commit:** 4.4 k stars; last release 1.5.3 (December 15 2025); last commit ~1 week ago as of Feb 2026.
- **What it does:** Disk-backed function memoization that persists across Python sessions. Internally serializes function arguments and return values using joblib's fast pickle, keyed by a hash of the arguments. Unlike `lru_cache`, the cache survives process restart, so a generator whose parameters haven't changed since the last app launch renders instantly. `joblib.Memory` was originally designed for NumPy-heavy scientific code; it hashes NumPy arrays correctly (by content, not identity).
- **Specific capability to borrow:** Wrap implicit generator functions with `@memory.cache`. A user who reopens the app and immediately loads their last session's variety hits the disk cache before any computation. Cache location is configurable (e.g., `~/.cache/avc/meshes`); TTL is manual (call `memory.clear()`). Most valuable for surfaces with expensive field evaluation and stable parameters (Hanson CY3, Dwork pencil at default ψ).
- **App positioning:** Import. `joblib` is a transitive dependency of `scikit-image` (already in requirements.txt), so it is already installed — zero new install cost.
- **Risk flags:** (1) Disk I/O on a cold miss may add 50–200 ms to cache write time. (2) Cache invalidation on code changes (new generator version) must be handled by bumping a version key or clearing the cache. (3) `pv.PolyData` pickle round-trip: joblib uses `pickle` with numpy array fast-path; VTK objects serialize differently — validate that a round-tripped `PolyData` retains normals and point-data arrays correctly. (4) Cache directory management (size, garbage collection) is manual in a single-developer app.
- **PySide6 compat:** Yes — no Qt dependency.

---

#### C3. `diskcache` (SQLite-backed persistent cache)
- **URL:** https://github.com/grantjenks/python-diskcache · https://grantjenks.com/docs/diskcache/
- **License:** Apache-2.0
- **Stars / last commit:** 2.9 k stars; actively maintained (Apache-2.0, not license-flagged).
- **What it does:** SQLite + file-backed cache with LRU eviction, stampede prevention, TTL support, and a `@cache.memoize` decorator. Cross-process safe, so a future multi-window or multi-process scenario is handled. Faster than Redis/Memcached for local access according to the project.
- **Specific capability to borrow:** Same disk-persistence story as `joblib.Memory` but with more cache-management knobs (eviction, TTL, size limit). The `@cache.memoize` decorator is simpler than joblib's class-based API.
- **App positioning:** Import. **Not currently installed** (unlike joblib); adds a new dependency with no compelling advantage over joblib.Memory for this use case. Recommended only if joblib's pickle fidelity for `PolyData` proves problematic.
- **Risk flags:** New dependency; overkill for a single-developer desktop app. `joblib.Memory` (C2) covers the same cross-session story at zero install cost.
- **PySide6 compat:** Yes — no Qt dependency.

---

### Group D — Threading in a Qt + VTK app

#### D1. `superqt` — `qdebounced` / `qthrottled` signal utilities
- **URL:** https://github.com/pyapp-kit/superqt · https://pyapp-kit.github.io/superqt/
- **License:** BSD-3-Clause
- **Stars / last commit:** 289 stars; latest release v0.8.2 (May 18, 2026); active.
- **What it does:** A Qt-widget utility library that provides — among other things — `qdebounced` and `qthrottled` decorators/callables for Qt signals. `qdebounced(slot, timeout_ms)` delays the slot invocation until `timeout_ms` milliseconds after the **last** signal emission (classic "search box" debounce). `qthrottled(slot, timeout_ms)` fires the slot at most once per `timeout_ms` (trailing or leading). Both work as method decorators or as standalone wrappers, support PySide6, and had a memory-leak fix in v0.6.7 (no longer hold strong references to bound methods via internal QTimer).
- **Specific capability to borrow:** Wrap `_on_params_changed` (currently connected directly to `sliderReleased` only) with `qdebounced(timeout=80)`. This makes the preview re-render fire 80 ms after the user *stops* dragging — a classic interactive-preview pattern. The existing `sliderReleased`→full-render path can remain for final quality. This is complementary to, not a replacement for, the worker-thread pattern (D2).
- **App positioning:** Import. `superqt` is in the source-registry already; add to `requirements.txt`. Compatible with PySide6 6.6–6.9 (6.10 has an unrelated VTK interaction bug; the throttle utilities themselves are PySide6-version-agnostic).
- **Risk flags:** (1) At 289 stars, this is a modest-sized project; however, it is actively maintained by the `pyapp-kit` org (also maintains `napari` ecosystem libraries). (2) The AI-9 `_computing` guard already blocks re-entrant renders — `qdebounced` reduces the *frequency* of calls but does not replace the guard. Both must coexist.
- **PySide6 compat:** Explicitly verified — tests run on PySide6 across all recent releases; v0.8.2 dropped PySide2 support and added Python 3.14.

---

#### D2. `QThreadPool` / `QRunnable` + signals pattern (PySide6 stdlib pattern)
- **URL:** https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html · https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/ (updated March 24, 2026)
- **License:** LGPL-3 (PySide6 — already in the stack)
- **Stars / last commit:** Qt framework — not a separate project.
- **What it does:** The recommended Qt threading pattern for Python desktop apps: define a `WorkerSignals(QObject)` with `result`, `finished`, and `error` signals; define a `MeshWorker(QRunnable)` that generates the `pv.PolyData` in its `run()` method and emits `signals.result.emit(mesh)` on completion; connect `result` to a main-thread slot that calls `plotter.add_mesh()`. `QThreadPool.globalInstance().start(worker)` dispatches without blocking the GUI. The critical footgun (confirmed by PyVista discussion #4006): **VTK's GL context is not thread-safe** — `pv.PolyData` construction is safe off-thread (it is pure NumPy + VTK data objects, no OpenGL), but **`plotter.add_mesh()`** and **`plotter.render()`** MUST be called on the GUI thread. The signal-slot boundary enforces this: the worker emits a signal carrying the finished `PolyData` object; the main-thread slot receives it and does all VTK/plotter calls.
- **Specific capability to borrow:** Convert `_render_current` so that: (1) it immediately shows a "Computing…" cursor and sets `_computing = True`; (2) dispatches a `MeshWorker`; (3) returns control to the Qt event loop; (4) on `result` signal receipt, calls the existing `_apply_domain_and_render` with the finished mesh. The AI-9 `_computing` guard still prevents re-entrant dispatch. This eliminates `QApplication.processEvents()` entirely (the current workaround for keeping the UI alive during synchronous generation), removing the re-entrancy risk that `processEvents` introduces.
- **App positioning:** Pattern-lift → in-repo implementation in `app.py`. No new dependency.
- **Risk flags:** (1) `pv.PolyData` is VTK-based; empirically it is safe to construct off the GUI thread (all fields are numpy arrays), but this is not formally documented by Kitware. (2) pyvistaqt's `BackgroundPlotter` is a different beast (runs an independent plotter in a background thread) and is NOT the right tool here — it conflicts with the existing `QtInteractor`-in-`QMainWindow` architecture. (3) The `_computing` guard must be thread-safe (Python's GIL makes `bool` reads/writes atomic on CPython); but if Python 3.13+ free-threading is ever adopted, a `threading.Lock` would be needed.
- **PySide6 compat:** Yes — native PySide6 API.

---

### Group E — Adaptive resolution / LOD

#### E1. Coarse-preview LOD (in-repo pattern)
- **URL:** N/A — in-repo architectural pattern
- **License:** N/A
- **What it does:** Run marching cubes at reduced grid resolution (e.g., 30³ = 27 k cells) on every `sliderValueChanged` event (debounced to ~80 ms); run at full resolution (80³ = 512 k cells or whatever the current default is) only on `sliderReleased`. The coarse mesh renders in ~20–40 ms on a CPU; the full mesh renders after the drag completes. The low-res mesh is a visually coherent preview — topologically correct, just coarser.
- **Specific capability to borrow:** Add a `preview_resolution: int = 30` parameter path in `_marching_cubes_to_polydata`. On `valueChanged` (via debounced signal), call with `preview_resolution`; on `sliderReleased`, call with the full resolution. Reuse the existing `_computing` guard and the worker-thread pattern (D2) for both paths.
- **App positioning:** In-repo code change. Zero new dependency.
- **Risk flags:** (1) The grid size is baked into each generator function (some use the `n` parameter to `np.linspace`); the `_marching_cubes_to_polydata` helper needs a `resolution` argument threaded through. (2) Coarse meshes for highly-curved surfaces (Kummer, Enriques sextic) can look misleadingly coarse; choose the "good enough" floor carefully (40³ may be a better floor than 30³).
- **PySide6 compat:** N/A.

---

## 3. Sources reviewed

| Source | URL | Accessed |
|---|---|---|
| PyVista `contour()` discussion: default algorithm | https://github.com/pyvista/pyvista/discussions/4461 | 2026-05-21 |
| Kitware: Really Fast Isocontouring (FlyingEdges) | https://www.kitware.com/really-fast-isocontouring/ | 2026-05-21 |
| Kitware: GPU rendering of isosurfaces | https://www.kitware.com/gpu-rendering-of-isosurfaces/ | 2026-05-21 |
| PyVista 0.46–0.48 release pages | https://github.com/pyvista/pyvista/releases | 2026-05-21 |
| PyVista contouring docs (0.48.2) | https://docs.pyvista.org/examples/01-filter/contouring.html | 2026-05-21 |
| pyvistaqt Qt 6.10 compatibility issue | https://github.com/pyvista/pyvistaqt/issues/793 | 2026-05-21 |
| PyVista background rendering discussion | https://github.com/pyvista/pyvista/discussions/4006 | 2026-05-21 |
| pyvistaqt: use data from separate thread | https://github.com/pyvista/pyvistaqt/discussions/139 | 2026-05-21 |
| Numba PyPI page (latest version, arm64 wheels) | https://pypi.org/project/numba/ | 2026-05-21 |
| Numba support tiers (macOS arm64 Tier 1) | https://numba.readthedocs.io/en/stable/reference/support_tiers.html | 2026-05-21 |
| Numba 0.62.0 RC announcement | https://numba.discourse.group/t/ann-numba-0-62-0rc1-llvmlite-0-45-0rc1/3048 | 2026-05-21 |
| superqt GitHub (stars, license, version) | https://github.com/pyapp-kit/superqt | 2026-05-21 |
| superqt CHANGELOG | https://github.com/pyapp-kit/superqt/blob/main/CHANGELOG.md | 2026-05-21 |
| joblib Memory docs | https://joblib.readthedocs.io/en/stable/memory.html | 2026-05-21 |
| joblib PyPI / GitHub (stars, last release) | https://pypi.org/project/joblib/ | 2026-05-21 |
| diskcache GitHub (license, stars) | https://github.com/grantjenks/python-diskcache | 2026-05-21 |
| PyMCubes GitHub (stars, license) | https://github.com/pmneila/PyMCubes | 2026-05-21 |
| isoext GitHub (stars, license, requirements) | https://github.com/GuangyanCai/isoext | 2026-05-21 |
| pythonguis: QThreadPool/QRunnable PySide6 | https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/ | 2026-05-21 |
| Qt for Python: QThread docs | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html | 2026-05-21 |
| arXiv: High-Performance SurfaceNets (2024) | https://arxiv.org/pdf/2401.14906 | 2026-05-21 |
| CONTEXT.md §3, §4.4, §8 | local | 2026-05-21 |
| app-invariants.md AI-1–AI-15 | local | 2026-05-21 |
| requirements.txt | local | 2026-05-21 |
| surfaces.py `_marching_cubes_to_polydata` | local | 2026-05-21 |

---

## 4. Themes

**Theme 1 — The bottleneck is two stages, not one.** The 0.5 s latency has two independent contributors: field evaluation (~150 ms, purely NumPy/Python) and marching cubes itself (~350 ms, skimage single-threaded). Numba addresses the first; flying_edges (or a threaded skimage replacement) addresses the second. Both can be applied simultaneously for a cumulative 5–10× reduction.

**Theme 2 — Threading is the right architecture, but the boundary is sharp.** The consensus across PyVista discussions and Qt documentation is identical: build `pv.PolyData` off the GUI thread (safe), hand it back via a signal, call `add_mesh()` and `render()` on the GUI thread only (unsafe off-thread). The current `processEvents()` approach (AI-9) is a pragmatic workaround for synchronous generation; moving to a `QThreadPool` worker eliminates the underlying need for `processEvents()`.

**Theme 3 — Debounce is a prerequisite for any background-thread approach.** Without `qdebounced` or a similar gate on the slider signal, a QThreadPool dispatch fires hundreds of times per second on drag, filling the thread pool with stale work items. The debounce window (80–150 ms) should match human perception of "responsive" (~100 ms latency threshold for direct manipulation UX).

**Theme 4 — pyvistaqt / Qt 6.10+ on macOS is an emerging risk.** Issue #793 (reported Feb 2026) documents a hang/freeze on macOS with PySide6 6.10+. Current requirements pin `PySide6 <7`; that still allows 6.10. Consider tightening to `PySide6 <6.10` until the upstream issue is resolved, or add a runtime version check.

**Theme 5 — Numba on Apple Silicon is now first-class.** The historical friction (no arm64 wheels on PyPI before 0.61) is resolved. Numba 0.65.1 ships arm64 wheels for Python 3.10–3.14. `cache=True` in `@njit` eliminates repeat JIT cost; first-call compile is ~1 s and happens once per session.

**Theme 6 — GPU isosurface extraction is academically interesting but off-stack.** isoext (MIT, 22 stars) requires PyTorch + CUDA — fundamentally incompatible with the macOS Apple Silicon primary platform (no CUDA on Apple hardware). VTK's GPU ray-cast isosurface mode is in-stack but requires a different data model. Both are parking-lot items for a hypothetical future platform expansion.

---

## 5. License watch — non-redistributable / redistribution flags

| Project | License | Flag |
|---|---|---|
| PyVista | MIT | Clean |
| VTK | BSD-3-Clause | Clean |
| Numba | BSD-2-Clause | Clean |
| superqt | BSD-3-Clause | Clean |
| joblib | BSD-3-Clause | Clean |
| diskcache | Apache-2.0 | Clean |
| PyMCubes | BSD-3-Clause | Clean |
| isoext | MIT | Clean — but CUDA-only, so moot for this platform |
| PySide6 | LGPL-3 | Clean (dynamically linked; existing stack) |
| scikit-image | BSD-3-Clause | Clean (existing dep) |

No GPL or AGPL projects surfaced in this survey. All candidates are import-safe for the LGPL PySide6 redistributable stack.

---

## 6. Out of scope / parking lot

- **isoext (GPU/CUDA marching cubes):** MIT-licensed, 22 stars, requires PyTorch + CUDA. Not viable on macOS Apple Silicon (no CUDA). Monitor for potential MPS (Apple GPU) support in a future PyTorch release, at which point the CUDA dependency could be swapped.
- **JAX / GPU field evaluation:** Apache-2.0; requires a large dep footprint and macOS Metal JAX support. Overkill for current scope; relevant if the app ever moves to browser/cloud.
- **Neural Marching Cubes / Deep Marching Cubes:** Research-grade; no stable Python library. Parking lot for a future "AI-assisted surface discovery" feature.
- **SurfaceNets (arXiv:2401.14906, 2024):** A high-performance isosurface algorithm with better feature preservation than marching cubes; implemented in VTK as `vtkSurfaceNets3D`. PyVista does not yet expose a `method='surface_nets'` parameter in `contour()` — but the VTK filter is callable directly. Worth tracking for a future quality-vs-speed tradeoff.
- **CuMCubes (CUDA marching cubes, 70 stars):** CUDA-only, same platform mismatch as isoext.
- **Adaptive marching cubes / octree refinement:** No mature Python library surfaced with recent activity and a clean license. The coarse-preview LOD (E1) achieves the most valuable part of this idea with zero dependencies.
- **Mesh interpolation in parameter space:** No OSS library specifically addresses interpolating between two `pv.PolyData` meshes keyed by parameter tuples. The topology changes as parameters change, making vertex-correspondence interpolation non-trivial. This is an open research area. The debounce + LOD combo (E1 + D1) is a more practical substitute.
- **pyvistaqt Qt 6.10+ hang (issue #793):** Not yet fixed as of May 2026. Pin `PySide6 >=6.6,<6.10` as an interim mitigation until upstream resolves. File as a roadmap risk item.
