# Adversary Brief — Real-Time Variety Render

**Scout role:** Current-state adversary  
**Topic:** Real-time parameter response (continuous drag update during slider/grid-dot drag)  
**Date:** 2026-05-21  
**Codebase revision:** `3e68e9e` (main)  
**Timing platform:** Windows 11, AMD/Intel (single-core NumPy, off-screen, no Qt overhead)

---

## 1. Executive Summary

The app re-renders only on slider *release* (INT-2 discipline) because implicit-surface mesh generation takes 0.65–1.45 s per frame. This is the right conservative choice *given the current architecture*, but the architecture itself has five compounding problems that make continuous drag (INT-NO-1 goal) hard:

1. The entire 3D field is resampled on every render call, even when only one of four parameters changes by one step.
2. The generation pipeline is synchronous and main-thread-blocking; there is no worker thread or cancellation path.
3. The re-entrancy guard (`_computing`) **drops** intermediate updates rather than queuing the latest one — so rapid drag produces long dead zones of visual silence followed by a single stale frame.
4. Grid resolution is fixed at 220–260, chosen for quality; no coarse-preview LOD path exists.
5. The parametric Hanson pipeline (27–38 ms) and the implicit pipeline (650 ms – 1.45 s) use the *same* interaction discipline, even though Hanson is already 20× faster and could plausibly support continuous drag today.

The gap is not a single missing feature; it is an architectural absence: no progressive rendering, no coarse preview, no background thread, no parameter-space caching, and no differentiation between fast and slow pipelines.

---

## 2. Critical Gaps

### C-1 — Entire pipeline is synchronous and main-thread-blocking

**Severity:** CRITICAL

**What peers/SOTA expect:** Surfer (Imaginary.org), Mathematica `Manipulate`, and GeoGebra all offload compute to a background thread and show either an in-progress preview or at minimum a responsive UI while the mesh generates. ParaView's pipeline runs in a separate process (pvserver). Any app with sub-100 ms target response times isolates the compute path.

**What the app has today:** `app.py:334–404` (`_render_current`) runs the full generate → clip → add_mesh → render sequence synchronously on the Qt main thread. `QApplication.processEvents()` at `app.py:349` is called once to update the status bar before the mesh starts — this is a workaround for responsiveness, not actual concurrency. The wait cursor appears but the UI freezes for the full generation duration.

**Credible v1 fill-in:** Move `surface.generate(**params)` into a `QThread` or `concurrent.futures.ThreadPoolExecutor` worker. The main thread submits the job and immediately returns; the worker calls back via a `Qt.QueuedConnection` signal when done. The `_computing` guard becomes a cancel-and-resubmit pattern. This is the single highest-leverage change; every other optimization builds on it.

**App-invariant interaction:** AI-9 (`_computing` guard). The guard must be extended rather than removed: the worker thread must not call `plotter.add_mesh()` or `plotter.render()` directly (VTK renders are not thread-safe); it must hand the finished `pv.PolyData` back to the main thread via a signal.

**Why not fixed yet:** The current architecture predates any real-time interaction goal. INT-2 (render-on-release) was the correct conservative choice when 0.5 s latency was first observed, and no follow-up performance pass has occurred.

---

### C-2 — Re-entrancy guard drops intermediate updates instead of queuing the latest

**Severity:** CRITICAL

**What peers/SOTA expect:** Real-time parameter explorers (Mathematica Manipulate, Observable Plot, Desmos) use a "debounce + execute latest" pattern: intermediate updates during a burst are dropped, but the *most recent* parameter snapshot is always committed once the current render finishes. The user sees the surface catch up to their final position even if intermediate frames were dropped.

**What the app has today:** `app.py:339–341`:
```python
if self._computing:
    return
```
This is a pure DROP. If the user drags a slider quickly and releases at a different position while a render is in progress, the `sliderReleased` signal fires `_on_params_changed` → `_render_current`, which hits `_computing = True` and returns immediately. The final resting position of the slider is never rendered until the user releases *again* or triggers another event. Under rapid drag (N events fired), every event except the first is silently discarded with no "pending" re-render.

**Credible v1 fill-in:** Add a `_pending_render: bool` flag. When `_computing is True` and a new render is requested, set `_pending_render = True`. In the `finally` block of `_render_current`, if `_pending_render` is True, clear it and schedule a single `QTimer.singleShot(0, lambda: self._render_current(...))` to catch up. This is a two-line change that eliminates stale-final-frame bugs.

**App-invariant interaction:** AI-9. The `_computing` guard pattern is sound; only the drop-vs-queue semantics need changing.

**Why not fixed yet:** The drop behavior is invisible under slow/deliberate slider use, which is the only interaction pattern the current release-only discipline supports.

---

## 3. High Gaps

### H-1 — No coarse-preview LOD path; grid resolution is monolithic

**Severity:** HIGH

**What peers/SOTA expect:** Surfer (Imaginary.org) renders a low-resolution preview (~50³ voxels) while the slider is moving and upgrades to full resolution on release. SageMath's 3D plots default to a fast low-res grid and offer a `plot3d(..., adaptive=True)` upgrade. The visual feedback loop is maintained at 10–20 fps by sacrificing triangle count.

**What the app has today:** `surfaces.py:225` sets `n = int(np.clip(round(220 * bounds / 2.5), 200, 260))` for the Fermat quartic — a fixed adaptive formula that always targets quality. The Kummer surface uses a hard-coded `n=240` (`surfaces.py:260`). All Enriques figures use `n=240` (`surfaces.py:318, 353, 401, 438`). The Dwork pencil uses `n=260` (`surfaces.py:669`). No surface exposes a low-quality fast path.

**Credible v1 fill-in:** Add an optional `n` override to `_marching_cubes_to_polydata` (it already accepts `smooth_iter` for this purpose) and add a `coarse_n: int = 80` parameter to each generator. During drag, call `generate(..., n=coarse_n)`; on release, call with the full `n`. The timing probe shows n=120 reduces field+MC from 326 ms to 55 ms — a 6× speedup with visually acceptable triangle density (12K vs 43K verts). n=80 would be even faster and still recognizable.

**App-invariant interaction:** AI-6 (marching cubes pipeline), AI-10 (raw mesh cache). The coarse mesh during drag and the full mesh on release are both `pv.PolyData` returned by the same generator contract; the `_raw_mesh` cache stores whichever is current.

**Why not fixed yet:** The INT-2 discipline (render-on-release) means there is no drag-time render to show a preview. The LOD concept only becomes useful once C-1 (worker thread) is addressed.

---

### H-2 — Full 3D field re-evaluated on every parameter change, even single-slider moves

**Severity:** HIGH

**What peers/SOTA expect:** Algebraic-surface explorers with multiple independent parameters (e.g., Mathematica's `ContourPlot3D` with `Manipulate`) cache the field array when only one of N parameters changes. Some use partial re-evaluation: if parameters can be factored, only the affected sub-expression is recomputed. The Enriques Fig 2 has three sliders (lam0, lam3, c) but the `lam0·x²y²z²` term is independent of `c`.

**What the app has today:** `surfaces.py:379–387` (`enriques_figure_2`) recomputes the full field `F` from scratch every call. The same pattern holds for all generators: `fermat_quartic` (`surfaces.py:226–239`), `kummer_surface` (`surfaces.py:286–295`), `calabi_yau_dwork` (`surfaces.py:703–705`). There is no intermediate field cache, no sub-expression memoization, and no parameter-sensitivity analysis. `app.py:357` calls `surface.generate(**params)` with no attempt to detect which parameter changed.

**Credible v1 fill-in:** For generators where the field factors into independent additive terms (Fermat quartic, Enriques Fig 2, Dwork pencil), the field can be decomposed as `F = F_static(x,y,z) + p * F_term(x,y,z)`. Caching `F_static + F_term` arrays keyed by the *unchanged* parameters and only recomputing the changed term reduces field-eval time roughly proportionally to the number of terms (e.g., 2–4× for 4-parameter surfaces). For the 50%-dominant field-eval step (155 ms of 378 ms for Fermat), this is meaningful.

**App-invariant interaction:** None directly; the generator contract (`pv.PolyData` or `ValueError`) is unchanged. The cache lives inside or alongside the generator.

**Why not fixed yet:** The generator functions are intentionally stateless pure functions (matches AI-14, AI-8 contract). Adding a cache requires either making them stateful or adding a thin caching wrapper at the `MainWindow` layer — both have been implicitly deferred.

---

### H-3 — Hanson parametric pipeline (27–38 ms) treated identically to implicit pipeline (650+ ms)

**Severity:** HIGH

**What peers/SOTA expect:** Scientific viz apps with multiple render pipelines at dramatically different costs (e.g., ParaView's surface-rendering vs volume-rendering) use different interaction disciplines: fast pipelines support continuous update, slow pipelines use progressive or deferred update.

**What the app has today:** `parameters_panel.py:229–230` fires `params_changed` on `sliderReleased` regardless of which surface is active. `app.py:309–313` routes all `params_changed` signals through the same `_render_current` path with the same `_computing` guard. The Hanson quintic at `grid=41` generates in 27 ms (timing probe above), which is well within the 100 ms human-perception threshold for "instant" response. Yet the app never attempts continuous rendering for it.

**Credible v1 fill-in:** Each `Surface` in the registry could carry a `fast: bool` attribute (or a `typical_ms: int` hint). `ParametersPanel` would connect the slider's `valueChanged` signal (not just `sliderReleased`) to a debounced-emit when `_current_surface.fast` is True. No changes to the render pipeline are required for the Hanson case — the 27 ms budget is already safe for `valueChanged`-driven continuous renders (at 10–30 fps drag rate) with no LOD needed.

**App-invariant interaction:** AI-9 (`_computing` guard). The guard still prevents re-entrancy; the change is only in *when* the signal fires.

**Why not fixed yet:** Slider wiring is uniform — one signal, one pattern, all surfaces. Differentiating by surface speed requires per-surface metadata that does not yet exist in the `Surface` dataclass (AI-8).

---

### H-4 — `plotter.add_mesh()` on every render: no mesh update-in-place

**Severity:** HIGH

**What peers/SOTA expect:** VTK's `vtkPolyDataMapper` supports `SetInputData(newPolyData)` without re-creating the actor or the mapper. PyVista exposes `actor.mapper.SetInputData(mesh)` followed by `render()` as a low-overhead path for animated mesh updates — used in PyVista's own animation examples. ParaView uses this extensively for in-place mesh updates during parameter sweeps.

**What the app has today:** `app.py:415–416` calls `self._clear_actor()` (removes the actor via `plotter.remove_actor`) then `app.py:455` calls `plotter.add_mesh(clipped, ...)` which creates a new mapper, actor, and uploads the full mesh to GPU memory. On a 400K-face mesh, this involves a full VBO upload even if the topology is similar to the previous mesh. There is no path for `actor.mapper.dataset = new_mesh` or equivalent.

**Credible v1 fill-in:** When the new mesh has the same vertex count as the old one (e.g., small parameter perturbations), update `self._actor.mapper.dataset` in place and call `self._actor.mapper.Modified()` + `plotter.render()`. When vertex count changes (topology change), fall back to the full `remove_actor` + `add_mesh` path. This eliminates one GPU upload round-trip per render at the cost of a vertex-count comparison.

**App-invariant interaction:** AI-9, AI-10. The `_raw_mesh` cache is unaffected; only the VTK plumbing changes.

**Why not fixed yet:** The current `clear + add` pattern was established when correctness was the priority. No performance-conscious pass has revisited the actor lifecycle.

---

## 4. Medium Gaps

### M-1 — `smooth_taubin(n_iter=20)` is non-trivially expensive and cannot be skipped during drag

**Severity:** MEDIUM

**What the timing shows:** For the Enriques canonical sextic (heaviest surface), Taubin smoothing costs 182 ms out of 1,056 ms total (17%). For the Fermat quartic, it costs 22 ms out of 378 ms (6%). This is non-trivial for the heavier surfaces.

**What the app has today:** `surfaces.py:95` hardcodes `n_iter=20, pass_band=0.1` in `_marching_cubes_to_polydata`. There is no `fast` parameter to disable or reduce smoothing for a coarse-preview render.

**Credible v1 fill-in:** `_marching_cubes_to_polydata` already accepts `smooth_iter: int = 20`. Passing `smooth_iter=0` for coarse previews eliminates the smoothing cost. The `n` override from H-1 and `smooth_iter=0` together would bring the Enriques canonical sextic from 1.2 s to under 100 ms at coarse resolution.

**App-invariant interaction:** AI-6. `smooth_iter=0` is explicitly handled (`surfaces.py:94–95`: `if smooth_iter > 0 and mesh.n_points > 0`). The API already supports it; only the call sites need to use it.

**Why not fixed yet:** Same as H-1 — no coarse-preview path exists yet.

---

### M-2 — `mesh.clean()` cost is variable and unsuppressable

**Severity:** MEDIUM

**What the timing shows:** `clean()` costs 13 ms for Fermat quartic (43K verts) and 103 ms for Enriques canonical sextic (400K verts). At high resolution it is the third-largest cost step.

**What the app has today:** `surfaces.py:91` always calls `mesh.clean()`. The purpose is to weld duplicate vertices that marching cubes occasionally produces at cell boundaries. For coarse-preview renders where visual quality is intentionally degraded, this step is unnecessary.

**Credible v1 fill-in:** Skip `clean()` in the coarse/preview path. Normals and topology may have hairline seams at coarse resolution, but this is acceptable for a 27–55 ms preview that the user will never screenshot.

**App-invariant interaction:** AI-6. The final full-quality render still calls `clean()` as today.

**Why not fixed yet:** Bound to the same coarse-preview gap as H-1.

---

### M-3 — `compute_normals()` post-smoothing costs 15–156 ms at full resolution

**Severity:** MEDIUM

**What the timing shows:** `compute_normals()` costs 17 ms for Fermat (43K verts) and 156 ms for Enriques canonical sextic (400K verts). For the heaviest surfaces it is the second-largest post-MC step.

**What the app has today:** `surfaces.py:97–102` always calls `compute_normals(cell_normals=False, point_normals=True, ...)` after smoothing. This is correct for the quality path.

**Credible v1 fill-in:** For the coarse-preview path, the gradient-based normals from `marching_cubes` are already attached as `mesh.point_data["Normals"]` (`surfaces.py:89`). Skipping `compute_normals()` and relying on the pre-smoothing analytic normals for the preview would save 156 ms on the heaviest surface. The final full-quality render still runs the full pipeline.

**App-invariant interaction:** AI-6. Normals are attached before smoothing (`surfaces.py:89`); the analytic normals are therefore already present if smoothing is skipped.

**Why not fixed yet:** Bound to the same coarse-preview gap as H-1.

---

### M-4 — Domain clip re-runs on every render, not only when domain settings change

**Severity:** MEDIUM

**What the app has today:** `app.py:413` calls `self.view_panel.clip_to_domain(self._raw_mesh)` in every call to `_apply_domain_and_render`. When only a parameter changes (not the domain), the clipped result is the same as the previous one — but it is recomputed from scratch regardless. `view_panel.py:422` calls `mesh.copy()` before tagging vertices, then clips. For a 400K-vert mesh this is a full copy + scalar tag + clip operation every time.

**Credible v1 fill-in:** Cache the clipped mesh alongside `_raw_mesh`: `self._clipped_mesh`. Invalidate it when either `_raw_mesh` changes *or* `domain_settings()` changes. When only appearance settings change, call `appearance_panel.apply_to_actor` directly without re-clipping. This is a minor optimization but reduces latency for the most common edit (parameter drag) by one `mesh.copy()` + one clip call.

**App-invariant interaction:** AI-10 (raw mesh cached). A second `_clipped_mesh` cache is the natural extension.

**Why not fixed yet:** Low-visibility optimization. The domain-clip path is already fast relative to mesh generation; no one has measured it.

---

### M-5 — No `add_mesh` / `render` timing instrumentation; the 0.5 s estimate is informal

**Severity:** MEDIUM

**What the app has today:** The `~0.5 s` estimate in CONTEXT.md §4.4 and `app-invariants.md` AI-9 is stated without timing evidence. The actual measured cost on this machine ranges from 0.66 s (Fermat quartic, default params) to 1.45 s (Fermat quartic with large bounds, Enriques Fig 4). The `add_mesh` + `render` sub-steps cost 9 ms + <1 ms respectively — they are negligible and previously unknown.

**Credible v1 fill-in:** The status bar already shows "Computing…" with elapsed time implicit. Adding a `time.perf_counter()` bracket around `surface.generate()` and surfacing the ms count in the status bar (e.g., "Fermat quartic · 43,840 verts · 85,676 faces · 0.66 s") would give users and developers calibrated feedback and make regression detection trivial.

**App-invariant interaction:** None. Pure telemetry addition.

**Why not fixed yet:** No one has measured it formally; the informal 0.5 s estimate was sufficient for the INT-2 decision.

---

## 5. Low Gaps

### L-1 — Adaptive n formula (Fermat quartic) can produce 260³ = 17.6M voxel grids

**Severity:** LOW

**What the app has today:** `surfaces.py:225`: `n = int(np.clip(round(220 * bounds / 2.5), 200, 260))`. At `c=20, gamma=-10` the adaptive bounds grow to ~3.8 (timing probe: 1.45 s, 343K verts). A worst-case `n=260, bounds=5.2` (the physical maximum) would generate 260³ = 17.6M voxels and take over 2 s. The cap at 260 was intentional (`surfaces.py:223`: "~17M voxels worst-case, ~1 s") but the comment's "~1 s" is already wrong on this machine (1.45 s at n=260 default).

**Credible v1 fill-in:** Lower the cap to 220 for the interactive path. The quality difference between n=220 and n=260 is imperceptible at typical viewport zoom levels. Reserve n=260 for the screenshot/export path.

**App-invariant interaction:** None.

**Why not fixed yet:** The 260 cap was set without measured timing on the actual target hardware.

---

### L-2 — Enriques Fig 4 hardcodes n=260 even though its field is already smooth

**Severity:** LOW

**What the app has today:** `surfaces.py:438` calls `_marching_cubes_to_polydata(F, bounds)` with the default n passed to `enriques_figure_4`, which is `n: int = 260` (`surfaces.py:437`). At 1.45 s on this machine it is the joint-slowest surface.

**Credible v1 fill-in:** The icosahedral sextic's field is a degree-6 polynomial with no near-singularities at the default tau=0.18. n=220 would produce visually equivalent output at ~30% lower cost based on the Enriques Fig 1 comparison (240 → 1.22 s; 220 → estimated 0.9 s).

**App-invariant interaction:** None.

**Why not fixed yet:** n=260 was set during the Enriques pass for visual quality without per-step timing.

---

### L-3 — `plotter.render()` is called on every `_apply_domain_and_render`, even for non-visible changes

**Severity:** LOW

**What the app has today:** `app.py:479` calls `self.plotter.render()` unconditionally at the end of every `_apply_domain_and_render` call. If the domain settings did not change and the mesh is the same, this render call is redundant (VTK will redraw the same frame). On macOS with a 120 Hz ProMotion display, this costs one vsync (8.3 ms) per spurious call.

**Credible v1 fill-in:** Track a `_render_dirty: bool` flag. Skip `render()` if nothing changed. This matters only if the interaction rate rises (e.g., for the pending LOD/worker thread work) and is a micro-optimization today.

**App-invariant interaction:** None.

**Why not fixed yet:** Negligible cost in the current release-only interaction model.

---

## 6. What the App Does Well

- **Raw mesh caching is implemented and working.** `_on_domain_changed` calls `_apply_domain_and_render` without regenerating the mesh (AI-10, `app.py:315–320`). The domain-clip slider is genuinely snappy.
- **`_marching_cubes_to_polydata` is a clean, single-responsibility helper.** The `smooth_iter` parameter is already present for future LOD use; the pre-MC zero-crossing check prevents cryptic errors; the gradient-normal attachment before smoothing is the correct quality pattern.
- **The generator contract is strictly enforced** (`pv.PolyData` or `ValueError`). This makes the generators straightforwardly testable and mockable, which will matter for any async or caching layer.
- **The `_computing` guard correctly prevents VTK actor corruption from re-entrant renders.** Its drop semantics are a gap (C-2), but the existence of the guard is correct — without it, concurrent `add_mesh` calls would corrupt the renderer.
- **Hanson parametric generators are already fast enough for continuous drag** (27–38 ms). The infrastructure gap (H-3) is UI-layer wiring, not a fundamental performance problem. This is the easiest win in the entire roadmap.
- **`add_mesh` + `render` are negligible** (9 ms + <1 ms). The performance problem is entirely in `surface.generate()`. This means the VTK plumbing is not the bottleneck — the fix is in the Python compute layer, not the GL layer.

---

## 7. Themes

**Theme 1 — Synchronous monolith.** The entire compute-to-render path is one blocking call on the main thread. Every other gap (LOD, caching, drop-vs-queue, pipeline differentiation) is downstream of this architectural choice. C-1 is the unlock.

**Theme 2 — Uniform treatment of non-uniform pipelines.** The Hanson parametric path is 20–50× faster than the implicit path but is wired identically. Differentiating by pipeline type (fast vs slow) would yield the first real-time wins without any compute optimization.

**Theme 3 — No progressive rendering contract.** The app's mental model is binary: "computing" or "done." There is no concept of "coarse preview → refine." Every optimization that requires a two-pass render (LOD, async worker) needs this contract to be introduced first.

**Theme 4 — Costs are concentrated in two steps.** Field evaluation and `marching_cubes()` together account for ~87% of total generation time (330 ms out of 378 ms for Fermat quartic; 606 ms of 1,056 ms for Enriques canonical sextic). All other steps (clean, Taubin, normals, add_mesh, render) are secondary and should not be the first target.

---

## 8. Render-Pipeline Cost Breakdown

### 8.1 Per-surface end-to-end timing (measured, off-screen, no Qt overhead)

| Surface | Grid n | Voxels (n³) | Total (s) | Verts | Faces |
|---|---|---|---|---|---|
| Hanson quintic grid=41 | — | — | **0.027** | 42,025 | 80,000 |
| Hanson quintic grid=61 | — | — | **0.038** | 93,025 | 180,000 |
| Hanson cubic torus grid=33 | — | — | **0.006** | 9,801 | 18,432 |
| Hanson asymmetric (5,3) grid=35 | — | — | **0.009** | 18,375 | 34,680 |
| Fermat quartic (defaults) | 220 | 10.6M | **0.656** | 42,840 | 85,676 |
| Enriques Fig 2 diagonal | 240 | 13.8M | **0.758** | 56,756 | 112,536 |
| Enriques Fig 3 Cayley | 240 | 13.8M | **0.702** | 138,345 | 274,479 |
| Kummer surface (defaults) | 240 | 13.8M | **0.964** | 192,864 | 383,032 |
| Dwork pencil ψ=0.5 | 260 | 17.6M | **1.388** | 198,204 | 394,876 |
| Enriques Fig 1 canonical sextic | 240 | 13.8M | **1.216** | 399,507 | 799,826 |
| Enriques Fig 4 icosahedral sextic | 260 | 17.6M | **1.445** | 464,568 | 922,880 |
| Fermat quartic (c=20, gamma=-10) | ~260 | ~17.6M | **1.451** | 343,080 | 686,156 |

*Note: Hanson parametric surfaces use a different pipeline (no marching cubes) — timing is not comparable.*

### 8.2 Sub-step breakdown for Fermat quartic (n=220, bounds=2.5, defaults)

| Step | Time (s) | % of total | Notes |
|---|---|---|---|
| Field evaluation (meshgrid + polynomial) | 0.155 | 41% | All NumPy; scales as O(n³) |
| `skimage.measure.marching_cubes()` | 0.171 | 45% | Cython; scales as O(n³) voxels + O(faces) output |
| `mesh.clean()` | 0.013 | 3% | Vertex deduplication |
| `smooth_taubin(n_iter=20)` | 0.022 | 6% | VTK-side loop; scales as O(verts × iters) |
| `compute_normals()` | 0.017 | 5% | VTK-side; scales as O(faces) |
| `plotter.add_mesh()` | 0.009 | 2% | GPU upload; *negligible* |
| `plotter.render()` | <0.001 | <1% | *negligible* (no Qt present) |
| **TOTAL** | **0.387** | 100% | Off-screen; add ~0.27 s for Qt overhead at runtime |

### 8.3 Sub-step breakdown for Enriques canonical sextic (n=240, bounds=1.8)

| Step | Time (s) | % of total | Notes |
|---|---|---|---|
| Field evaluation | 0.305 | 29% | Degree-6 polynomial; more operations than quartic |
| `skimage.measure.marching_cubes()` | 0.301 | 29% | 400K verts output amplifies postprocessing |
| `mesh.clean()` | 0.103 | 10% | Large output mesh |
| `smooth_taubin(n_iter=20)` | 0.182 | 17% | Scales with vert count: 10× more verts than Fermat default |
| `compute_normals()` | 0.156 | 15% | Scales with face count |
| `plotter.add_mesh()` | 0.009 | <1% | *negligible* |
| `plotter.render()` | <0.001 | <1% | *negligible* |
| **TOTAL** | **1.056** | 100% | Consistent with measured end-to-end 1.216 s |

### 8.4 Half-resolution comparison (field + MC only, Fermat quartic)

| Resolution | n³ voxels | Field + MC (s) | Verts | Speedup |
|---|---|---|---|---|
| Full (n=220) | 10.6M | 0.326 | 42,840 | 1× |
| Half (n=120) | 1.73M | 0.055 | 12,672 | **6×** |
| Quarter (n=80) | 0.51M | est. ~0.015 | ~6,000 | est. **22×** |

*A coarse-preview path at n=80–120 would bring the dominant two steps well below the 60 ms frame budget.*

### 8.5 Key finding: add_mesh + render are not the bottleneck

The `plotter.add_mesh()` call costs 9 ms; `plotter.render()` costs <1 ms off-screen. These steps are negligible and should not be the target of optimization. The bottleneck is entirely in `surface.generate()` — specifically field evaluation and `marching_cubes()`. Any real-time strategy must reduce, cache, or parallelize these two steps.
