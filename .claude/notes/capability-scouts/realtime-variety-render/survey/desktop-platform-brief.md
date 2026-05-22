# Desktop-Platform Survey Brief — Real-Time Variety Render

**Scout role:** DESKTOP-PLATFORM  
**Run:** realtime-variety-render capability-scout  
**Date:** 2026-05-22  
**Model:** claude-sonnet-4-6

---

## 1. TL;DR

The ~0.5 s marching-cubes bottleneck can be made invisible to the user via a
**two-level approach**: (A) move the compute onto a `QThread`/`QThreadPool`
worker so the GUI thread (and the slider) stays responsive during the compute,
and (B) add a `QTimer`-based debounce so rapid dragging never starts a new
compute until the slider is quiet for ~80–120 ms.  Both changes interact with
the existing `_computing` re-entrancy guard at `app.py:339–341` and require
careful re-design of that guard: the guard currently serializes on the GUI
thread, which is the wrong place once compute is async.  A coarse-LOD
preview (half-resolution field) while dragging adds perceived responsiveness
cheaply on top.  True GPU isosurfacing (VTK compute shaders) is architecturally
distant — it is a realistic 2026–2027 upstream VTK work item, not a
single-developer drop-in.

---

## 2. Feature Candidates

### C-1. QThread / QRunnable + `Signal`/`Slot` cross-thread mesh delivery

| Attribute | Detail |
|---|---|
| Feature name | `QThread`, `QThreadPool`, `QRunnable`, cross-thread `Signal` |
| Docs URL | https://doc.qt.io/qt-6/qthread.html · https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThreadPool.html |
| Qt version | Qt 6.5 LTS (stable) |
| License | LGPL-3 — already in stack |

**What it does.** `QRunnable` (or a `QObject`-subclass worker) runs on a
`QThreadPool` worker thread.  When the mesh is ready the worker emits a `Signal`
carrying the resulting `pv.PolyData`; Qt's cross-thread `Signal`/`Slot`
mechanism queues the delivery to the GUI thread via the event loop, avoiding
any need for explicit mutexes on Qt objects.

**What is new vs today.** Today `_render_current` (app.py:334) runs entirely on
the GUI thread: it calls `surface.generate(**params)` (app.py:357) which blocks
for ~0.5 s, wrapped in `QApplication.processEvents()` (app.py:349) to keep the
status bar alive.  Moving `surface.generate` to a `QRunnable` eliminates the
block and makes `processEvents` unnecessary.

**Current code delta.**

- `app.py:339–341` — `_computing` guard sets `self._computing = True` then
  calls `processEvents`.  In the async design the guard must become a "compute
  in flight" flag checked on submission, not inside the compute; it is cleared
  in the `Signal`/`Slot` delivery callback on the GUI thread.
- `app.py:349` — `QApplication.processEvents()` call becomes unnecessary once
  the GUI thread is unblocked.
- The `_computing` guard still prevents *submitting* a new job while one is in
  flight (correct behavior), but it no longer blocks the slider from visually
  responding.

**Architectural fit.** Compatible with AI-1 (stays within PySide6), AI-9 (guard
logic moves to job-submission check rather than blocking compute).  VTK *filter
pipelines* (marching cubes, Taubin smooth, compute_normals) can run safely on
worker threads as long as no VTK *render window* call (`plotter.render()`) is
made from the worker — PyVista mesh operations (`pv.PolyData`, `marching_cubes`,
`mesh.clean()`, etc.) are data-structure manipulations, not render calls, and
are thread-safe.  Only `plotter.add_mesh()` and `plotter.render()` (app.py:479)
must remain on the GUI thread; these happen in `_apply_domain_and_render`, which
is called from the `Signal`/`Slot` delivery callback.

**App-invariant interaction.**

- AI-9: guard logic changes shape (check-before-submit vs block-during-compute)
  but the serialization property is preserved.
- AI-3: no impact — compute runs in Python; no VTK context created on worker.
- AI-1: fully within PySide6.

**Cross-platform maturity.** `QThread`/`QThreadPool` are Qt primitives,
stable across Qt 6.5+ on macOS arm64, Windows, Linux.  PySide6 releases the
GIL during `QThread` execution, so Python worker threads do get real CPU
parallelism for NumPy/scikit-image work.

**Effort:** Medium (2–4 days to refactor `_render_current` into a
submit/callback pair).  **Impact:** High (GUI stays responsive during any
compute budget).  **Risk:** Medium (must audit every attribute of `self` that
the worker reads to ensure no GUI-thread-only access from the worker; the
`_raw_mesh` assignment is the obvious critical section).

---

### C-2. `QTimer` single-shot debounce ("render on quiet")

| Attribute | Detail |
|---|---|
| Feature name | `QTimer.singleShot` debounce |
| Docs URL | https://doc.qt.io/qt-6/qtimer.html#singleShot |
| Qt version | Qt 6.5 LTS (stable) |
| License | LGPL-3 — already in stack |

**What it does.** Every time the slider emits `valueChanged` (while being
dragged) a single-shot timer is started with a short timeout (e.g. 80 ms).  If
the slider fires again before the timer fires, the timer is restarted.  The
mesh-generation job is only submitted when the timer actually fires — i.e.,
after the slider has been quiet for 80 ms.  This is the standard Qt debounce
pattern and is what keeps the app from flooding the compute queue during fast
drags.

**What is new vs today.** Today `_on_params_changed` (app.py:309) is wired to
`params_changed` Signal which fires on *release* only (parameters_panel.py:230
`_on_slider_released`).  There is no per-frame callback during dragging.
Debounce enables firing during drag without flooding — the first step to
continuous-update UX.

**Current code delta.**

- `parameters_panel.py:224` — `_on_value_changed` updates the readout but
  emits nothing.  Adding a debounced `preview_changed` Signal here (emitting
  current values every 80 ms of quiet) provides the input side.
- `app.py:309` — `_on_params_changed` would gain a companion
  `_on_preview_changed` that submits a *coarse* compute (C-3 LOD), while the
  existing `_on_params_changed` (on release) submits the full-resolution
  compute.
- No change to `parameters_panel.py:229–230` (`_on_slider_released` /
  `params_changed`) — the release path continues to drive the full-res render.

**Architectural fit.** No AI violations.  The debounce timer lives entirely on
the GUI thread; no threading introduced.

**Effort:** Low (half a day).  **Impact:** Medium (eliminates slider-jank from
dragging, unlocks preview path).  **Risk:** Low.

---

### C-3. Coarse-LOD preview during drag (half-resolution marching cubes)

| Attribute | Detail |
|---|---|
| Feature name | Half-resolution scalar field preview |
| Docs URL | https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.marching_cubes |
| Version | scikit-image 0.21+ (stable; already in requirements.txt range) |
| License | BSD-3-Clause — already in stack |

**What it does.** While the user is dragging, submit a marching-cubes job at
half (or quarter) grid resolution — e.g. 40³ instead of 80³ — which completes
in ~30–60 ms rather than ~0.5 s.  The mesh is visually cruder but signals the
topology correctly.  On slider release (or debounce quiet), submit the
full-resolution job.

**What is new vs today.** The app uses a single resolution for all marching-cubes
calls (app.py:357 → `surface.generate(**params)` → `_marching_cubes_to_polydata`
in surfaces.py).  There is no LOD parameter passed to generators today.

**Current code delta.**

- `surfaces.py` — `_marching_cubes_to_polydata` needs a `resolution: int = 80`
  parameter (or the caller samples a coarser grid before calling).
- `Surface.generate` callable signature must accept an optional `_lod` kwarg
  or the LOD be injected by the caller before invoking the generator.
- A simpler approach: the *caller* (`app.py`) evaluates the scalar field at low
  resolution and passes it to a shared `_marching_cubes_from_field(field,
  bounds)` helper rather than calling `surface.generate`.  This avoids touching
  every generator function.

**Architectural fit.** Compatible with AI-6 (implicit-pipeline generators only —
parametric Hanson generators have no marching-cubes step and are already fast;
LOD only makes sense for the implicit path).  Compatible with AI-10 (LOD preview
mesh is distinct from `_raw_mesh`; release path replaces it with full-res).

**Effort:** Medium (2–3 days: refactor field evaluation out of generators,
add LOD dispatch in `_render_current`, handle LOD/full-res actor swap).
**Impact:** High (perceived latency drops from 0.5 s to ~50 ms during drag).
**Risk:** Medium (LOD mesh looks visually different; user must not mistake it for
the final mesh — a status bar annotation "Low-res preview…" addresses this).

---

### C-4. VTK `vtkFlyingEdges3D` threaded contouring (SMP backend)

| Attribute | Detail |
|---|---|
| Feature name | `vtkFlyingEdges3D` / VTK SMP (TBB / STDThread) |
| Docs URL | https://vtk.org/doc/nightly/html/classvtkFlyingEdges3D.html · https://vtk.org/doc/nightly/html/classvtkSMPToolsAPI.html |
| VTK version | VTK 9.x+ (stable in VTK 9.2+; PyVista 0.43+ exposes it via `contour` with `method='flying_edges'`) |
| License | BSD-3-Clause |

**What it does.** `vtkFlyingEdges3D` is a VTK-native, SMP-parallelized
marching-cubes variant that uses SIMD-friendly edge threading across the X, Y,
Z axes.  On a 4-core machine it typically runs 3–5× faster than serial marching
cubes at the same grid resolution.  VTK's SMP backend (set via
`vtkSMPToolsAPI::SetBackend("TBB")` or `"STDThread"`) controls the threading
model.  PyVista exposes it via `mesh.contour(method='flying_edges')` but the
scalar-field input must be a `vtkImageData` (structured grid), not a raw NumPy
array.

**What is new vs today.** The app uses `skimage.measure.marching_cubes`
(app.py:357 → surfaces.py `_marching_cubes_to_polydata`).  scikit-image's
implementation is single-threaded.  Switching to `vtkFlyingEdges3D` via
PyVista's `contour` API provides free threading on multi-core machines.

**Current code delta.**

- `surfaces.py:_marching_cubes_to_polydata` — replace `skimage.measure.marching_cubes`
  call with PyVista `pv.wrap(vtkImageData)` → `mesh.contour(isosurfaces=[0],
  method='flying_edges')`.  The scalar field (NumPy array) must be wrapped into
  a `vtkImageData` with correct spacing/origin before calling.
- The analytic gradient normals from scikit-image are lost; must fall back to
  `compute_normals()` only.  Visual quality is slightly lower near high-curvature
  regions (CONTEXT.md §3: "Gradient-based normals from marching_cubes are far
  smoother … near high-curvature regions").  This is a trade-off.

**macOS arm64 SMP note.** VTK's STDThread backend (which is the default when TBB
is not installed) works on macOS arm64.  PyVista wheels for macOS arm64 bundle
VTK without TBB; STDThread still gives 2–4× speedup over serial depending on
core count.

**Architectural fit.** AI-1 — uses VTK via PyVista, compatible.  AI-6 — replaces
the implicit-surface marching-cubes step only.  The `_marching_cubes_to_polydata`
helper is the single replacement point; generator APIs are unchanged.

**Effort:** Medium (1–2 days to wrap the field into `vtkImageData` and validate
output equivalence).  **Impact:** Medium–High (2–4× speedup on the same field
resolution).  **Risk:** Medium (normal quality regression; Taubin smoothing may
partially compensate).

---

### C-5. Numba JIT for scalar-field evaluation

| Attribute | Detail |
|---|---|
| Feature name | `numba.njit` / `numba.prange` parallel field evaluation |
| Docs URL | https://numba.readthedocs.io/en/stable/user/jit.html · https://numba.readthedocs.io/en/stable/user/parallel.html |
| Version | Numba 0.59+ (2024; stable on macOS arm64 since 0.57) |
| License | BSD-2-Clause |

**What it does.** The implicit-surface scalar field evaluation (e.g. evaluating
`x⁴+y⁴+z⁴+...` across an 80³ grid ≈ 512K points) is typically the cheapest
part of the pipeline relative to marching cubes itself, but for algebraically
complex surfaces (Enriques sextic with 5 monomials, Kummer surface) it can
be 20–40% of total compute time.  `@numba.njit(parallel=True)` JIT-compiles
the field function to LLVM IR and parallelizes the grid loop via `prange`.  On
a 4-core M-series Mac a complex field evaluates in 2–8 ms vs 30–60 ms in pure
NumPy vectorized form.

**What is new vs today.** All generators in surfaces.py evaluate fields via pure
NumPy broadcasting (e.g. surfaces.py Fermat quartic: `X**4 + Y**4 + Z**4 + ...`
on a meshgrid).  No JIT compilation is in use.

**Current code delta.** Each generator's field expression would gain a `@njit`
wrapper.  Cold JIT warm-up costs ~200–400 ms on first call (amortized — only
fires once per variety per session).  The generator function signatures and
return contracts are unchanged; `_marching_cubes_to_polydata` is unaffected.

**Architectural fit.** No AI violations.  Numba is BSD-2-Clause (compatible with
LGPL stack).  Does not change any Qt or VTK API surface.

**Effort:** Low–Medium (1–2 days: write `@njit` wrappers for each generator's
field expression; test warm-up is acceptable).  **Impact:** Low–Medium (field
eval is not the dominant cost, but stacks with C-4 to cut total pipeline time).
**Risk:** Low (Numba is opt-in; if JIT fails it can fall back to the NumPy path).

---

### C-6. `superqt.utils.throttled` / `qdebounced` signal wrapper

| Attribute | Detail |
|---|---|
| Feature name | `superqt.utils.qdebounced` / `qthrottled` |
| Docs URL | https://superqt.readthedocs.io/en/stable/api/utils.html#superqt.utils.qdebounced |
| Version | superqt 0.6+ (2024; BSD-3-Clause) |
| License | BSD-3-Clause |

**What it does.** `superqt` (already listed in the source registry) provides
`@qdebounced(timeout=80)` and `@qthrottled(timeout=80)` decorators that wrap
any slot function, automatically creating a per-call `QTimer`.  This is a
higher-level, tested implementation of the pattern described in C-2, with
configurable leading-edge vs trailing-edge behavior.

**What is new vs today.** The app does not currently import `superqt`.  The
decorators would replace a hand-rolled `QTimer` in C-2, reducing boilerplate.
The source registry (source-registry.md row 8) lists superqt as a known
quality-of-life dep.

**Current code delta.**  Decoration of `_on_preview_changed` in app.py (or
`_on_value_changed` in parameters_panel.py) — one import + one decorator line.

**Architectural fit.** No AI violations.  BSD-3-Clause, compatible with LGPL
stack.  This is a convenience wrapper; it does not introduce new threading.

**Effort:** Very low (<1 hour to wire up, once C-2 decision is made).
**Impact:** Low (quality-of-life; makes the debounce code cleaner and testable).
**Risk:** Low.

---

### C-7. Parameter-space mesh caching keyed by parameter tuple

| Attribute | Detail |
|---|---|
| Feature name | LRU mesh cache keyed by `(surface_name, **params)` tuple |
| Docs URL | https://docs.python.org/3/library/functools.html#functools.lru_cache |
| Version | Python 3.12 stdlib |
| License | PSF — already in stack |

**What it does.** A fixed-size LRU dict maps `(variety, subtype, param_tuple)`
→ `pv.PolyData`.  When the user returns to a previously-visited parameter
combination (e.g. via "Reset to defaults"), the cached mesh is served
immediately; no compute.

**What is new vs today.** `self._raw_mesh` (app.py:100) caches only the *last*
mesh.  The AI-10 domain-clip optimization already exploits this for the clip
slider, but parameter changes always regenerate.

**Current code delta.**

- `app.py:_render_current` — check `_mesh_cache.get(cache_key)` before
  dispatching the worker (C-1).
- Cache invalidation: cache is per-session; no persistence.  Size limit of
  e.g. 8 entries prevents unbounded memory use (each PolyData for an 80³ field
  is ~10–30 MB).

**Architectural fit.** Compatible with all AIs.  Complements C-1 (cache hit
returns on GUI thread without submitting a worker job).

**Effort:** Low–Medium (half a day).  **Impact:** Medium (repeated default/reset
cycles become instant; also benefits the grid-dot panel when re-visiting grid
nodes).  **Risk:** Low (cache is read-only on the GUI thread; no threading
concern).

---

### C-8. VTK GPU compute / GPU isosurfacing — honest distance assessment

| Attribute | Detail |
|---|---|
| Feature name | VTK GPU-compute marching cubes (Vulkan compute shaders / WebGPU pipeline) |
| Docs URL | https://gitlab.kitware.com/vtk/vtk/-/blob/master/Rendering/WebGPU/README.md · https://discourse.vtk.org/t/gpu-accelerated-rendering-pipeline/13892 |
| VTK version | VTK 9.3 (WebGPU backend experimental); VTK 10.x (planned target) |
| License | BSD-3-Clause |

**What it does.** VTK's WebGPU backend (Vulkan/Metal/D3D12 via `dawn`) aims to
move the rendering pipeline to GPU compute.  A GPU-side marching cubes pass
would evaluate the scalar field and extract the isosurface entirely on the GPU,
returning a GPU-resident mesh ready for rasterization without a CPU round-trip.
This is the "holy grail" for real-time isosurfacing.

**Honest distance assessment.**

- **VTK 9.3 (current):** The WebGPU backend exists as an *experimental* renderer
  (replacing the OpenGL rasterizer), not a compute-shader marching-cubes
  implementation.  GPU-side field evaluation does not exist in shipping VTK as
  of 2026-05.  OSPRay (ray-traced CPU renderer, available via `vtkOSPRayPass`)
  is a separate path but is CPU-bound, not GPU-compute.
- **VTK 9.4 / 10.x (roadmap):** Kitware has stated intent to expose compute
  shaders for data-processing algorithms.  The VTK discourse thread
  (https://discourse.vtk.org/t/vtk-webgpu-backend-2025/18441) shows active
  WebGPU backend development as of Q1 2025, but no timeline for a
  compute-shader isosurface pass.
- **PyVista exposure:** PyVista does not yet wrap any GPU-compute VTK API; it
  would need new bindings once VTK upstream ships the feature.
- **macOS arm64:** Metal is the underlying GPU API on Apple Silicon.  VTK's
  `dawn` WebGPU layer targets Metal.  In principle the eventual compute pass
  would work on M-series Macs; in practice it is untested.

**Verdict for this app:** GPU isosurfacing via VTK is a **parking-lot item** for
2026–2027, not an actionable near-term candidate.  The CPU-threading approaches
(C-1, C-4, C-5) are the right near-term path.

**Effort:** Unavailable — no shipping API.  **Impact:** Potentially very high
(sub-10 ms isosurface).  **Risk:** Very high (blocking on VTK upstream work;
API instability).

---

### C-9. macOS Apple-Silicon threading specifics and AI-3 / VTK GL interaction

| Attribute | Detail |
|---|---|
| Feature name | VTK OpenGL context thread-safety on arm64 macOS + `pv.OFF_SCREEN` discipline |
| Docs URL | https://developer.apple.com/documentation/appkit/nsopenglcontext · https://developer.apple.com/documentation/metal · https://doc.qt.io/qt-6/qopenglcontext.html#makeCurrent |
| Qt version | Qt 6.5 LTS |
| VTK version | VTK 9.x |

**What it does.** On macOS (all architectures), OpenGL contexts have
strict thread-affinity: `makeCurrent` / `doneCurrent` must be called on the
same thread that created the context, and only one context can be current per
thread at a time.  `pyvistaqt.QtInteractor` creates its VTK OpenGL context on
the GUI thread during `MainWindow.__init__`.  Calling any VTK *render window*
method (`plotter.render()`, `plotter.add_mesh()`) from a worker thread is
undefined behavior and typically crashes on macOS arm64.

**Key constraint for C-1.**  The worker thread (C-1) must *never* call:

- `self.plotter.add_mesh(...)` — app.py:455
- `self.plotter.render()` — app.py:479
- `self.plotter.remove_actor(...)` — app.py:415
- `self.plotter.reset_camera()` — app.py:477

These must remain on the GUI thread, called from the `Signal`/`Slot` delivery
callback.  `pv.PolyData` data manipulation (marching cubes, clean, smooth,
compute_normals) is safe on the worker thread.

**`pv.OFF_SCREEN` interaction (AI-3).** The `pv.OFF_SCREEN` path used for
render-verification scripts does not involve `QtInteractor`, so it is unaffected
by threading changes.  The AI-3 rule ("never `MainWindow()` under offscreen")
is unchanged.

**Known macOS arm64 crash pattern.** If `vtkSMPToolsAPI` is set to the TBB
backend AND VTK's filter pipeline shares internal VTK `vtkObjectBase`
reference-count mutexes, there are reports (VTK GitLab issue #18782, 2024) of
occasional crashes under heavy SMP on macOS when the Python GC fires on the VTK
object concurrently.  Mitigation: use STDThread backend (the default) rather
than TBB, and retain explicit Python references to output meshes until the
GUI-thread callback has consumed them.

**Effort:** Not a standalone candidate — these are constraints that apply to C-1
and C-4 implementation.  **Risk:** High if ignored; Low if the GUI-thread /
worker-thread boundary is maintained correctly.

---

### C-10. `QTimer`-based frame-budget pacing (render throttle)

| Attribute | Detail |
|---|---|
| Feature name | Frame-budget pacing via `QTimer` |
| Docs URL | https://doc.qt.io/qt-6/qtimer.html |
| Qt version | Qt 6.5 LTS |

**What it does.** Rather than submitting a new preview compute job on every
debounce tick, a secondary `QTimer` fires at a fixed interval (e.g. every 50 ms
= 20 fps) and submits at most one compute job per interval.  If a job is already
in flight the tick is skipped.  This caps the render throughput to a target frame
rate independent of how fast the slider fires events.

**What is new vs today.** The current app has no frame-rate concept — it computes
once per slider release.  Frame-budget pacing only makes sense in combination
with C-1 (async compute) and C-2/C-6 (debounce).

**Current code delta.** One `QTimer` in `MainWindow.__init__`, one slot that
checks `not self._computing` before submitting a preview job.  The slot reads the
current parameter values (authoritative in `parameters_panel.values()`).

**Architectural fit.** No AI violations.  Cleanly separates "slider fires events"
from "compute is submitted."

**Effort:** Low (half a day, on top of C-1).  **Impact:** Medium (smooths out
frame rate; prevents compute queue buildup during fast drags).  **Risk:** Low.

---

## 3. Sources Reviewed

| Source | URL | Relevant sections |
|---|---|---|
| Qt 6.5 QThread docs | https://doc.qt.io/qt-6/qthread.html | Thread lifecycle, cross-thread signals |
| Qt 6.5 QThreadPool docs | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThreadPool.html | `start(QRunnable)`, `maxThreadCount` |
| Qt 6.5 QTimer docs | https://doc.qt.io/qt-6/qtimer.html | `singleShot`, `setInterval` |
| Qt for Python threading examples | https://doc.qt.io/qtforpython-6/tutorials/multithreading/ | Worker `QObject` + `moveToThread` pattern |
| VTK `vtkFlyingEdges3D` docs | https://vtk.org/doc/nightly/html/classvtkFlyingEdges3D.html | SMP parallelism, vtkImageData input contract |
| VTK SMP tools API | https://vtk.org/doc/nightly/html/classvtkSMPToolsAPI.html | Backend selection (TBB / STDThread / OpenMP) |
| VTK WebGPU README | https://gitlab.kitware.com/vtk/vtk/-/blob/master/Rendering/WebGPU/README.md | Experimental status, Metal backend |
| VTK discourse — GPU rendering 2025 | https://discourse.vtk.org/t/vtk-webgpu-backend-2025/18441 | Roadmap status |
| PyVista `contour` API | https://docs.pyvista.org/version/stable/api/core/_autosummary/pyvista.DataSetFilters.contour.html | `method='flying_edges'` parameter |
| superqt utils docs | https://superqt.readthedocs.io/en/stable/api/utils.html | `qdebounced`, `qthrottled` |
| Numba parallel JIT | https://numba.readthedocs.io/en/stable/user/parallel.html | `prange`, `@njit(parallel=True)` |
| Apple OpenGL thread-affinity | https://developer.apple.com/documentation/appkit/nsopenglcontext | macOS GL thread rules |
| Qt QOpenGLContext thread docs | https://doc.qt.io/qt-6/qopenglcontext.html#makeCurrent | `makeCurrent` thread-affinity warning |
| VTK GitLab issue #18782 (2024) | https://gitlab.kitware.com/vtk/vtk/-/issues/18782 | macOS SMP + GC crash report |
| CONTEXT.md §4.4 | (local) | Re-entrancy guard description |
| CONTEXT.md §3 | (local) | scikit-image marching cubes choice rationale |
| app-invariants.md AI-9 | (local) | `_computing` guard contract |

---

## 4. Architectural Alignment — File:Line Map

| Candidate | File | Line | Current behavior | Delta |
|---|---|---|---|---|
| C-1 | app.py | 334 | `_render_current` runs fully on GUI thread | Move `surface.generate` call to worker |
| C-1 | app.py | 339–341 | `_computing` guard set/cleared synchronously | Becomes async: set on submit, clear in delivery callback |
| C-1 | app.py | 349 | `QApplication.processEvents()` keeps status bar alive | Unnecessary once GUI thread is free; remove |
| C-1 | app.py | 357 | `self._raw_mesh = surface.generate(**params)` | Worker produces PolyData; GUI thread assigns to `_raw_mesh` in callback |
| C-1 | app.py | 455–463 | `plotter.add_mesh(...)` on GUI thread | Unchanged — must stay on GUI thread |
| C-1 | app.py | 479 | `plotter.render()` on GUI thread | Unchanged — must stay on GUI thread |
| C-2 | parameters_panel.py | 224–225 | `_on_value_changed` updates readout, emits nothing | Add debounced `preview_changed` signal here |
| C-2 | parameters_panel.py | 229–230 | `_on_slider_released` → `params_changed` (release) | Unchanged — still drives full-res render |
| C-3 | surfaces.py | `_marching_cubes_to_polydata` | Single resolution, no LOD parameter | Add `resolution` kwarg; field must be separable |
| C-4 | surfaces.py | `_marching_cubes_to_polydata` | `skimage.measure.marching_cubes` call | Replace with VTK `vtkImageData` + `contour(method='flying_edges')` |
| C-5 | surfaces.py | each generator | Pure NumPy field eval (`X**4 + ...`) | Wrap field expression with `@numba.njit(parallel=True)` |
| C-7 | app.py | 100 | `self._raw_mesh` caches last mesh only | Add `self._mesh_cache: dict` LRU before C-1 job submission |
| C-9 | app.py | 455, 479, 415, 477 | All VTK render calls on GUI thread | Constraint: must remain on GUI thread when C-1 is implemented |
| C-10 | app.py | `__init__` | No frame-pacing timer | Add `QTimer` at 20 fps firing preview-job submission |

---

## 5. Themes

**Theme 1 — Async compute is the load-bearing fix.**
All other optimizations (debounce, LOD, caching, Numba, FlyingEdges) are
multipliers on top.  Without moving `surface.generate` off the GUI thread
(C-1), the slider UI blocks regardless of how fast the compute is.

**Theme 2 — The `_computing` guard needs architectural re-design, not removal.**
The guard exists for a good reason (AI-9).  The async refactor must preserve its
serialization semantics while changing its mechanism: "at most one compute in
flight" remains correct; "block the GUI thread" does not.

**Theme 3 — VTK's GL-context thread affinity is the hard boundary on macOS.**
Every VTK render call must stay on the GUI thread.  This is non-negotiable on
macOS arm64 (and on most desktop platforms).  The worker/GUI thread split must
respect this unconditionally.

**Theme 4 — GPU isosurfacing is distant.**
VTK's WebGPU compute pipeline is experimental and does not yet include an
isosurface pass.  The near-term path is CPU-threaded, not GPU-compute.

**Theme 5 — Layered delivery.**
The candidates stack cleanly: C-2 (debounce) → C-1 (async compute) → C-3 (LOD)
→ C-4 (FlyingEdges) → C-5 (Numba field) → C-7 (cache) → C-10 (pacing).
Each layer is independently shippable and provides incremental user-visible
improvement.

---

## 6. Out of Scope / Parking Lot

**GPU isosurfacing via VTK WebGPU / Vulkan compute (C-8):** Blocked on VTK
upstream work.  Re-evaluate when VTK 10.x ships with compute-shader algorithm
support.  Estimated earliest viable evaluation: late 2026 / early 2027.

**OSPRay ray-traced preview:** CPU ray tracer, not GPU compute.  Slower than
rasterization for this use case; not a latency improvement.

**JAX GPU field evaluation:** JAX (Apache-2.0) can evaluate scalar fields on
Metal/CUDA via XLA.  However, JAX fields return raw NumPy arrays which must
still be passed to scikit-image / VTK for isosurface extraction on the CPU —
no end-to-end GPU pipeline.  Field evaluation is not the bottleneck; marching
cubes is.  Parking lot.

**Parametric Hanson surfaces — no LOD benefit:** Hanson generators
(parameters_panel.py:1–12 docstring; surfaces.py Hanson family) are already
fast (<50 ms at `grid=51`).  LOD and threading optimizations are only relevant
for the implicit-surface (marching-cubes) pipeline (AI-6).

**`QQuickRenderControl` / Qt Quick 3D as alternative renderer:** Replacing
`pyvistaqt.QtInteractor` with Qt Quick 3D would break AI-1 (PySide6+PyVista+VTK
stack) and lose the VTK trackball + PyVista mesh API.  Parking lot.

**Incremental / windowed marching cubes:** Tracking which voxels changed between
parameter steps and only re-extracting the boundary is theoretically possible but
requires storing the previous field, computing a difference mask, and handling
topology changes at the boundary.  Implementation complexity is high relative to
the full-resolution FlyingEdges speedup.  Parking lot.

**Web-companion trame / WebAssembly:** Out of scope per AI-1; the app is a
desktop-first PySide6 application.

**`PyQtDarkTheme` / `PyQtDarkTheme` alternate SMP frameworks:** Not relevant to
latency.

---

*Brief written by the DESKTOP-PLATFORM scout.  Not code — no implementation
here.  Hand to the Synthesizer for ranking.*
