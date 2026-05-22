# Synthesis — realtime-variety-render

**Date:** 2026-05-22
**Inputs:** 5 survey briefs (competitive, math-research, oss-trends, desktop-platform, adversary)
**Question:** What capabilities would shrink/hide the ~0.5–1.45 s marching-cubes latency enough to make the variety update continuously as a slider or grid-dot is dragged?

---

## 1. Executive summary

**13 candidates**, overwhelmingly in the **Performance/numerics** category with a few in **Interaction/UI** and **Rendering/mesh**. The five scouts converged hard: the same 4–5 techniques surfaced independently in 4–5 briefs each. The dominant finding (adversary §8 timing table, math-research Theme A) is that the ~0.5 s is **not** in VTK rendering — `add_mesh`+`render` cost 9 ms+<1 ms — it is entirely inside `surface.generate()`, split roughly **field-evaluation 41–45% / marching-cubes 45% / smoothing+clean+normals ~10%**. The top theme is **two-pass LOD is the universal peer pattern** (Mathematica `ControlActive`, ParaView interactive/still, Surfer, Desmos) — every peer renders a coarse preview during drag and snaps to full quality on release; this app already has the "snap on release" half (INT-2) and is missing the "coarse preview during drag" half. The top tension is the **AI-15 honesty boundary**: a coarse-grid preview can misrepresent topology (Kummer's 16 nodes, the Dwork conifold), and parameter-space mesh interpolation is mathematically fraudulent — both need explicit disclaimers or get parking-lotted. A second hard constraint surfaced by the oss-trends scout: **pyvistaqt reportedly hangs on macOS with PySide6 ≥ 6.10** (issue #793, Feb 2026) — any threading work must verify the PySide6 pin.

The single biggest insight for sequencing: the **parametric Hanson pipeline is already 27–38 ms** (20–50× faster than the implicit pipeline) and could support continuous drag *today* with zero compute optimization — it is wired to the slow discipline only by uniform signal-routing.

---

## 2. Triangulation strength

- **5-brief candidates (strongest signal):** CAND-3 (coarse-preview LOD), CAND-4 (background thread)
- **4-brief:** CAND-1 (Flying Edges), CAND-2 (Numba JIT)
- **3-brief:** CAND-6 (debounce), CAND-7 (mesh cache)
- **2-brief:** CAND-5 (queue-latest guard), CAND-13 (resolution-cap hygiene)
- **1-brief but adversary-anchored to code evidence (treat as strong):** CAND-8 (Hanson fast path — adversary H-3), CAND-9 (mesh update-in-place — adversary H-4), CAND-10 (field sub-expression cache — adversary H-2), CAND-11 (clipped-mesh cache — adversary M-4), CAND-12 (telemetry — adversary M-5)

Single-brief candidates here are NOT weak signal — the adversary scout is the only one that traced the actual code with a timing probe, so its H-/M-findings are code-anchored facts, not opinions. They are flagged for challenger scrutiny on effort, not on whether the gap is real.

---

## 3. Foundational candidates (sequence these first)

The scouts agree the optimizations are not independent — they form a dependency DAG:

- **CAND-12 (timing instrumentation)** is foundational #0: you cannot tune or regression-guard latency you do not measure. The adversary scout had to run its own off-screen probe because the app has no telemetry. ~XS effort, unblocks honest before/after comparison for every other candidate.
- **CAND-4 (background-thread worker)** is the architectural unlock (adversary C-1, "the single highest-leverage change; every other optimization builds on it"). Coarse-preview LOD, queue-latest, and continuous drag all assume mesh generation is off the GUI thread.
- **CAND-5 (queue-latest re-entrancy guard)** + **CAND-6 (debounce)** are the interaction-discipline prerequisites: without them, continuous drag either drops the final frame (current `_computing` DROP semantics — adversary C-2 CRITICAL) or thrashes.

Phase 4 must sequence CAND-12 → {CAND-4, CAND-5, CAND-6} → CAND-3 → the rest.

---

## 4. Candidate catalog

### CAND-1 — Replace scikit-image marching cubes with VTK Flying Edges

**Category:** Performance/numerics
**Size:** S
**Evidence triangulation:** 4 briefs (competitive C-1, math-research T-3, oss-trends, desktop-platform)

**What it is:** Swap `skimage.measure.marching_cubes` in `surfaces.py:_marching_cubes_to_polydata` for VTK's `vtkFlyingEdges3D`, exposed via `pv.ImageData(...).contour([0.0], method='flying_edges')`. Flying Edges is a four-pass, row-oriented, SMP-threaded isocontouring algorithm — Kitware benchmarks it at 1–2 orders of magnitude faster than classic marching cubes "even in single-thread mode."

**Why it matters:** Zero new dependencies (VTK is already the foundation), mathematically identical output to machine precision, and it directly attacks the ~45%-of-budget marching-cubes step. On its own it does not make continuous update viable, but it shrinks the latency budget every other candidate works within.

**Sources:**
- Competitive scout C-1: drop-in replacement, ~15 LOC, `pv.ImageData.contour(method='flying_edges')`
- Math-research scout T-3: Schroeder et al. LDAV 2015; topologically identical to MC
- OSS-trends scout: `vtkFlyingEdges3D` SMP-threaded; PyVista `contour()` already wraps it (not the default)
- Desktop-platform scout: VTK SMP backend (TBB/OpenMP) — Apple-Silicon wheels ship OpenMP

**Closest app analog (today):** `surfaces.py:_marching_cubes_to_polydata` (~line 48–102), the `skimage.measure.marching_cubes` call ~line 80.

**Sketch:** Build a `pv.ImageData` with `dimensions`/`spacing`/`origin` from the existing sampling box, set the field as a point-data array (`order="F"` ravel), call `.contour([level], method='flying_edges')`. The output `pv.PolyData` enters the same `clean()`/`smooth_taubin()`/`compute_normals()` downstream path. **Trade-off the challenger must weigh:** Flying Edges does NOT return scikit-image's analytic gradient normals (currently seeded into Taubin smoothing) — normals must come from `compute_normals()` post-extraction, a minor shading-quality change. Existing `tests/test_mesh_generators.py` smoke tests catch regressions.

**Open questions:**
- Measured speedup on Apple Silicon (OpenMP not TBB in the wheel) — needs CAND-12 telemetry to confirm the 1–2-orders-of-magnitude claim holds locally.
- Does dropping gradient-seeded normals visibly degrade shading on high-curvature surfaces (Enriques sextic)?

---

### CAND-2 — Numba JIT-compile the implicit-field evaluation kernel

**Category:** Performance/numerics
**Size:** M
**Evidence triangulation:** 4 briefs (competitive C-10, math-research T-2, oss-trends, desktop-platform)

**What it is:** Replace the NumPy-broadcasting polynomial field evaluation in each implicit generator with a Numba `@njit(parallel=True)` kernel that fuses the per-term arithmetic into a single threaded loop over the grid, eliminating O(n³) intermediate-array allocations and enabling AVX SIMD + multi-core.

**Why it matters:** Field evaluation is the single largest cost (41–45% of `generate()`; ~155 ms of 378 ms for Fermat, ~305 ms of 1056 ms for Enriques). Math-research estimates 10–30× field-eval speedup; combined with CAND-1 this could bring an n≈150 full-res update toward ~50 ms — genuinely interactive. Numba is BSD-2-Clause (clean for the LGPL stack) and ships arm64 macOS wheels (Numba 0.60+/0.65+).

**Sources:**
- Competitive scout C-10: `@njit` on the field kernel; first-call JIT latency is the UX risk
- Math-research scout T-2: 10–30× via loop fusion + AVX; numerically identical (full AI-15 compliance, no disclaimer)
- OSS-trends scout: Numba arm64 PyPI wheels confirmed; `@guvectorize(target='parallel')` 13–25× on array math
- Desktop-platform scout: Numba JIT as a field-eval candidate

**Closest app analog (today):** The `np.meshgrid` + polynomial broadcasting inside each implicit generator (`fermat_quartic`, `kummer_surface`, `enriques_*`, `calabi_yau_dwork` in `surfaces.py`).

**Sketch:** Per generator, factor the field math into a `@njit(parallel=True, cache=True)` kernel taking the grid axes + parameters and returning the field array. Warm the JIT at app startup (or on first surface selection) by calling each kernel once with defaults — never let the ~1–3 s first-call compile fire mid-drag. `cache=True` persists compiled code across launches. AI-6 footprint: field-eval only; the output is still a plain ndarray into `_marching_cubes_to_polydata`.

**Open questions:**
- First-call latency management: startup warm-up vs lazy-on-first-select — which is the better UX?
- Numba's NumPy subset may force restructuring vectorized expressions into explicit loops — per-generator effort varies (degree-6 Enriques is the heaviest).
- Apple-Silicon `parallel=True` threading-layer stability in 2026 — verify.

---

### CAND-3 — Two-pass coarse-preview LOD (coarse grid during drag, full-res on release)

**Category:** Performance/numerics + Interaction/UI
**Size:** M
**Evidence triangulation:** 5 briefs (competitive C-2/C-6, math-research T-1, oss-trends, desktop-platform, adversary H-1/M-1/M-2/M-3)

**What it is:** During a drag, regenerate the implicit surface on a coarse grid (n≈60–120 vs the production 220–260) with smoothing/clean/normal-recompute skipped; on release, regenerate at full resolution and quality. The adversary timing shows n=120 cuts field+MC from 326 ms to 55 ms (6×) and n=80 to ~15 ms (~22×).

**Why it matters:** This is the universal peer pattern (Mathematica `ControlActive`, ParaView interactive/still, Surfer, Desmos). It is the technique that actually delivers a continuously-moving surface during drag. The skipped post-steps (`smooth_taubin`, `clean`, `compute_normals` — adversary M-1/M-2/M-3) are already gated by existing parameters (`smooth_iter=0` is handled) so the coarse path is mostly plumbing, not new code.

**Sources:**
- Competitive scout C-2 (Mathematica `ControlActive` two-pass) + C-6 (`step_size` coarse grid)
- Math-research scout T-1 (two-resolution LOD) + T-9 (topology-safe coarse-resolution bounds — Stander-Hart/Plantinga-Vegter)
- Adversary scout H-1 (no coarse path; grid resolution monolithic) + M-1/M-2/M-3 (Taubin/clean/normals all skippable for preview)
- OSS-trends + desktop-platform: coarse-LOD listed as a primary intervention

**Closest app analog (today):** `surfaces.py:_marching_cubes_to_polydata` already accepts `smooth_iter` (the LOD hook exists); generators take a fixed `n`. No coarse path is wired.

**Sketch:** Thread an optional `n` (and `smooth_iter=0`, `skip_clean=True`) override through `surface.generate()` → `_marching_cubes_to_polydata`. The drag path calls with `coarse_n≈80`; the release path with full `n`. A status-bar badge ("Preview — coarse resolution; true surface on release") is **mandatory per AI-15** — the coarse mesh is not the true variety and may misrepresent thin features. Math-research T-9 offers a path to upgrade the disclaimer from "topology may differ" to "topology guaranteed" by computing per-surface Lipschitz-bounded safe coarse resolutions, but no Python implementation exists — treat that as a v2 refinement.

**Open questions:**
- Coarse `n` floor: n=80 is ~22× faster but may merge Kummer nodes / miss the Dwork conifold — what is the smallest n that is honest enough?
- Depends on CAND-4 (a coarse render still blocks the GUI thread without a worker) and CAND-5/6 (drag-discipline). It is a downstream candidate.
- AI-15: the disclaimer wording + when it shows/hides.

---

### CAND-4 — Background-thread mesh-generation worker

**Category:** Performance/numerics (architecture)
**Size:** L
**Evidence triangulation:** 5 briefs (competitive C-4/C-11, math-research T-4, oss-trends, desktop-platform, adversary C-1)

**What it is:** Move `surface.generate(**params)` off the Qt GUI thread onto a `QThread`/`QThreadPool`+`QRunnable` (or `concurrent.futures`) worker. The worker computes the `pv.PolyData` and hands it back to the main thread via a `Qt.QueuedConnection` signal; the main thread does `add_mesh`/`render` (VTK rendering must stay on the GUI thread — confirmed by PyVista discussion #4006 and the macOS Cocoa main-thread requirement). The `_computing` guard becomes "worker in flight"; the `QApplication.processEvents()` re-entrancy workaround in `_render_current` can be removed entirely.

**Why it matters:** The adversary scout calls this "the single highest-leverage change; every other optimization builds on it." Today the entire pipeline blocks the GUI thread — the slider freezes for the full 0.5–1.45 s. A worker keeps the slider responsive, enables stale-job cancel-and-resubmit, and is the prerequisite for continuous drag.

**Sources:**
- Adversary scout C-1 (CRITICAL — synchronous main-thread monolith)
- Competitive scout C-4 (napari `@thread_worker` pattern) + C-11 (generator-yield progressive delivery: yield coarse, then yield full)
- Math-research scout T-4 (QThread; VTK on main thread; `_computing` becomes `isRunning()`)
- OSS-trends scout: `QThreadPool`/`QRunnable` + finished-`pv.PolyData` via signal; building PolyData off-thread is safe
- Desktop-platform scout: redesigning the AI-9 `_computing` guard from blocking-flag to submit-time-check is the prerequisite for everything else

**Closest app analog (today):** `app.py:_render_current` / `_apply_domain_and_render` (~line 334–479) — fully synchronous; `_computing` guard ~line 339–341; `QApplication.processEvents()` ~line 349.

**Sketch:** A `QRunnable` carries `(surface, params, n)` and emits `mesh_ready(pv.PolyData)`. `MainWindow` tracks `self._mesh_worker`; a new request cancels/supersedes the in-flight one (cooperative abort flag checked between coarse/full yields — competitive C-11). On `mesh_ready`, the main thread runs the existing clip+`add_mesh`+`render`. AI-9 interaction is the crux: the worker must never touch the plotter; only `pv.PolyData` crosses the thread boundary. **AI-3 / macOS:** verify no Qt+VTK GL-context interaction under threading on arm64 (desktop-platform flagged this). **Pin risk:** oss-trends flags pyvistaqt hangs on macOS with PySide6 ≥ 6.10 (issue #793) — confirm/pin before shipping threading.

**Open questions:**
- `QThread` vs `QThreadPool`+`QRunnable` vs `concurrent.futures` — which fits the cancel-and-resubmit pattern cleanest?
- Does the worker import `superqt`'s `thread_worker` (BSD-3-Clause, no napari dependency) or hand-roll? superqt's generator-worker supports the coarse-then-full yield cleanly.
- macOS arm64 Qt+VTK threading safety needs an explicit spike before this is L-effort-confident.

---

### CAND-5 — Re-entrancy guard: drop → queue-latest

**Category:** Interaction/UI (correctness)
**Size:** XS
**Evidence triangulation:** 2 briefs (adversary C-2 CRITICAL, competitive C-3 context)

**What it is:** Change the `_computing` guard from a pure DROP to a "queue the latest" pattern: when a render is requested while one is in flight, set `_pending_render = True`; in the `finally` block, if pending, schedule one catch-up render via `QTimer.singleShot(0, ...)`.

**Why it matters:** Today (adversary C-2) a fast drag-and-release fires N events; every event after the first hits `if self._computing: return` and is silently discarded — the slider's **final resting position is never rendered**. The user sees a long dead zone then a stale frame. This is a CRITICAL correctness bug independent of any optimization, and a ~2-line fix.

**Sources:**
- Adversary scout C-2 (CRITICAL): pure DROP semantics; `app.py:339–341`
- Competitive scout C-3: debounce + execute-latest is the canonical Mathematica/Observable/Desmos pattern

**Closest app analog (today):** `app.py` `_render_current` `_computing` guard, ~line 339–341.

**Sketch:** Add `self._pending_render: bool`. On a render request while `_computing`, set it. In `_render_current`'s `finally`, if `_pending_render`, clear it and `QTimer.singleShot(0, lambda: self._render_current(...))`. Composes with CAND-4 (with a worker, "pending" means resubmit the latest params after the current worker returns).

**Open questions:** none — well-specified; ships standalone or folds into CAND-4.

---

### CAND-6 — Debounce slider/grid `valueChanged` (QTimer or superqt)

**Category:** Interaction/UI
**Size:** S
**Evidence triangulation:** 3 briefs (competitive C-3, oss-trends, desktop-platform)

**What it is:** Gate drag-time render requests through a 50–150 ms debounce so a coarse render fires at most ~6–20×/s during a drag rather than on every pixel of slider/dot motion. Either a hand-rolled single-shot `QTimer` (zero new deps) or `superqt`'s `@qdebounced` decorator (BSD-3-Clause, PySide6-verified, v0.8.2).

**Why it matters:** Continuous drag without throttling would queue dozens of renders per second — even coarse ones thrash. Debounce is "table stakes for slider-driven heavy computation" (competitive Theme 4) and is the cheapest safety net even before LOD/threading land. The `sliderReleased`/dot-release path bypasses the debounce as the full-res trigger.

**Sources:**
- Competitive scout C-3: QTimer pattern (no dep) or `superqt` (1 dep); KDAB throttle-vs-debounce guidance, 50–100 ms for mesh viz
- OSS-trends scout: `superqt.qdebounced` BSD-3-Clause, ~80 ms interval
- Desktop-platform scout: `QTimer` single-shot debounce as the standard "render after N ms of slider quiet" pattern

**Closest app analog (today):** `parameters_panel.py` `_on_value_changed` (live label only, no render) / `_on_slider_released` (the render trigger); the grid panel's `_on_drag_move` / `_on_drag_release` have the identical two-phase structure.

**Sketch:** A single-shot `QTimer` in `ParametersPanel` (and `ParameterGridPanel`); `valueChanged`/`_on_drag_move` restarts it; on timeout it emits a new `params_preview_changed` signal (coarse path). `sliderReleased`/`_on_drag_release` emits the existing full-res `params_changed` directly. Prefer the QTimer form to avoid a new dep unless `superqt` is already being pulled in by CAND-4's worker.

**Open questions:**
- Debounce interval (50 / 80 / 150 ms) — tune against measured coarse-render cost from CAND-12.
- Whether to share one debounce utility between `ParametersPanel` and `ParameterGridPanel` (a `ui_helpers` addition) — likely yes.

---

### CAND-7 — LRU parameter-tuple mesh cache

**Category:** State/persistence
**Size:** S
**Evidence triangulation:** 3 briefs (competitive C-5, oss-trends, desktop-platform)

**What it is:** An in-memory `OrderedDict` cache (8–16 entries, ~50–160 MB) keyed by `(surface, rounded-parameter-tuple)`; `_render_current` checks it before calling `surface.generate()`. Reversing a slider to a recently-visited value becomes instant.

**Why it matters:** Cheap win for the "hover around one parameter" exploration pattern and for the 2D/3D grid where the dot revisits cells. Pairs naturally with idle-time pre-rendering of neighboring parameter values (the user's "pre-rendering/preloading" ask).

**Sources:**
- Competitive scout C-5: `OrderedDict` with max-size eviction; key = rounded sorted param tuple; clear on surface switch
- OSS-trends scout: `functools.lru_cache` / `joblib.Memory` (disk-backed) / `diskcache`
- Desktop-platform scout: LRU mesh caching listed

**Closest app analog (today):** `app.py` `_raw_mesh` is a single-slot cache (AI-10); `surface.generate(**params)` ~line 357 is the cache-miss call site; `_on_subtype_changed` must invalidate.

**Sketch:** `self._mesh_cache: OrderedDict` on `MainWindow`. Key = `(subtype_id, tuple(round(v, k) for k,v in sorted(params.items())))`. Hit → skip `generate()`. Miss → generate, store, evict oldest. Clear on `_on_subtype_changed`. Memory cap by entry count. If CAND-4 lands, the worker writes results back on the main thread only (no cross-thread cache writes). Optional v2: a disk-backed tier via `joblib.Memory`/`diskcache` for cross-launch persistence — but mesh objects are large; weigh against value.

**Open questions:**
- Rounding precision for the key — too coarse merges distinct surfaces, too fine never hits.
- Idle-time pre-render of neighbor parameter values (true "preloading") — fold in here or separate candidate? (Recommend fold in as a v2 of this candidate.)

---

### CAND-8 — Fast-pipeline differentiation: continuous update for the parametric Hanson surfaces

**Category:** Interaction/UI
**Size:** XS
**Evidence triangulation:** 1 brief (adversary H-3) — code-anchored, high-confidence

**What it is:** The Calabi–Yau Hanson parametric surfaces regenerate in 27–38 ms (adversary §8 timing) — 20–50× faster than the implicit pipeline and already well within the ~100 ms "instant" threshold. Tag each `Surface` with a `fast`/`typical_ms` hint; for fast surfaces, wire the slider/dot `valueChanged` (debounced) straight to a render with NO coarse-LOD path needed.

**Why it matters:** The adversary calls this "the easiest win in the entire roadmap." It delivers genuine continuous drag for an entire variety family **with zero compute optimization** — purely UI signal-routing. It is also a clean proving ground for the continuous-drag interaction discipline before the harder implicit-pipeline work.

**Sources:**
- Adversary scout H-3: Hanson parametric 27–38 ms treated identically to implicit 650+ ms; `parameters_panel.py:229–230` fires uniformly; `Surface` dataclass has no speed metadata.

**Closest app analog (today):** `Surface` dataclass in `surfaces.py` (no `fast` field); `parameters_panel.py` `_on_slider_released`; `app.py` `_on_params_changed`. The `_grid_to_polydata` Hanson path.

**Sketch:** Add a `fast: bool = False` (or `typical_ms: int`) field to the `Surface` dataclass (AI-8 — confirm `frozen` allows a defaulted field add). When the current surface is `fast`, `ParametersPanel`/`ParameterGridPanel` connect the debounced `valueChanged`/`_on_drag_move` to the render path; otherwise keep release-only (or coarse-LOD once CAND-3 lands). Composes with CAND-5/CAND-6.

**Open questions:**
- `fast: bool` vs a measured `typical_ms` threshold — the latter is more honest but needs CAND-12 telemetry to populate.
- Confirm the AI-8 frozen-dataclass field addition is clean (same pattern as the recent `recommends_backface_culling` discussion).

---

### CAND-9 — In-place mesh update (`mapper.SetInputData`) instead of remove+add_mesh

**Category:** Rendering/mesh
**Size:** S
**Evidence triangulation:** 1 brief (adversary H-4) — code-anchored

**What it is:** When a new mesh has the same vertex count as the current actor's mesh (small parameter perturbations), update `actor.mapper` input in place + `Modified()` + `render()` instead of `remove_actor` + `add_mesh` (which rebuilds mapper+actor and re-uploads the full VBO to the GPU).

**Why it matters:** `add_mesh` is only 9 ms (adversary §8) so this is a *small* win in absolute terms — but during continuous drag every millisecond and every GPU round-trip counts, and it removes an actor-lifecycle churn. Lower priority than the compute-side candidates.

**Sources:**
- Adversary scout H-4: `app.py:415–416` `_clear_actor` then `app.py:455` `add_mesh` rebuilds mapper+actor every render; PyVista exposes `actor.mapper` in-place update used in its own animation examples.

**Closest app analog (today):** `app.py` `_clear_actor` (~415) + `add_mesh` (~455) in `_apply_domain_and_render`.

**Sketch:** If `new_mesh.n_points == self._actor_mesh.n_points`, set the mapper's dataset in place + `Modified()` + `render()`; else fall back to the full `remove_actor`+`add_mesh` (topology changed). Vertex-count comparison is the cheap discriminator. AI-9/AI-10 unaffected.

**Open questions:**
- Coarse↔full LOD swaps change vertex count every time — so this only helps within a single LOD level during drag, not at the coarse→full snap. Quantify the realistic win with CAND-12 before committing.

---

### CAND-10 — Field sub-expression caching (static/term decomposition)

**Category:** Performance/numerics
**Size:** M
**Evidence triangulation:** 1 brief (adversary H-2) — code-anchored

**What it is:** Several implicit fields decompose additively as `F = F_static(x,y,z) + p · F_term(x,y,z)` where `p` is one parameter. When only `p` changes, cache the parameter-independent arrays and recompute only the changed term — reducing field-eval cost roughly proportionally to the term count (2–4× for 4-parameter surfaces).

**Why it matters:** Targets the 41–45%-of-budget field-eval step specifically for the common single-slider-move case. **However** it overlaps heavily with CAND-2 (Numba JIT) which attacks the same step more generally — the challenger should assess whether CAND-2 makes CAND-10's marginal value too thin to justify the per-generator decomposition work.

**Sources:**
- Adversary scout H-2: `surfaces.py:379–387` `enriques_figure_2` recomputes the full field every call; the `lam0·x²y²z²` term is independent of `c`.

**Closest app analog (today):** Each implicit generator's field assembly in `surfaces.py`; generators are intentionally stateless pure functions (AI-8/AI-14) — caching needs a wrapper layer.

**Sketch:** Per generator (where the field genuinely factors), split into a static part + per-parameter terms; memoize the static arrays keyed by the unchanged parameters. Requires detecting which parameter changed (the app currently passes the full param dict with no diff). AI-8/AI-14 generator contract unchanged if the cache is a wrapper.

**Open questions:**
- Strong overlap with CAND-2 — likely redundant if Numba lands. Flag for the challenger.
- Not all fields factor cleanly (Hanson is parametric and already fast; Kummer's field is multiplicative in places).

---

### CAND-11 — Clipped-mesh cache (decouple domain-clip from parameter render)

**Category:** Performance/numerics
**Size:** XS
**Evidence triangulation:** 1 brief (adversary M-4) — code-anchored

**What it is:** Cache `self._clipped_mesh` alongside `_raw_mesh`; invalidate it only when `_raw_mesh` changes OR domain settings change. Today `_apply_domain_and_render` re-runs `clip_to_domain` (a full `mesh.copy()` + scalar-tag + clip) on every render even when only an appearance setting changed.

**Why it matters:** Small, isolated optimization that removes a `mesh.copy()`+clip from the common parameter-drag path. Low risk, low effort.

**Sources:**
- Adversary scout M-4: `app.py:413` `clip_to_domain` runs every `_apply_domain_and_render`; `view_panel.py:422` `mesh.copy()` before tagging.

**Closest app analog (today):** `app.py:_apply_domain_and_render` ~line 413; the existing single-slot `_raw_mesh` cache (AI-10).

**Sketch:** Second cache slot `_clipped_mesh`. Invalidate on raw-mesh change or `domain_settings()` change. Appearance-only changes skip re-clipping and call `appearance_panel.apply_to_actor` directly. Natural extension of the AI-10 raw-mesh cache.

**Open questions:** none — well-specified.

---

### CAND-12 — Render-pipeline timing instrumentation

**Category:** Performance/numerics (telemetry) + Typography/docs
**Size:** XS
**Evidence triangulation:** 1 brief (adversary M-5) — code-anchored; foundational

**What it is:** Add `time.perf_counter()` brackets around `surface.generate()` (and optionally per sub-step) and surface the ms count in the status bar (e.g., "Fermat quartic · 43,840 verts · 0.66 s"). The "~0.5 s" figure in CONTEXT.md/AI-9 is an informal estimate; the adversary measured 0.66–1.45 s.

**Why it matters:** Foundational #0 — every other candidate's impact claim ("6× faster", "10–30× field eval") needs a measured before/after, and regression detection needs a baseline. The adversary scout had to write its own probe because the app has no telemetry. Near-zero risk, ~XS effort.

**Sources:**
- Adversary scout M-5: no `add_mesh`/`render` timing; the 0.5 s estimate is unverified; status bar already shows mesh stats and could carry the ms.

**Closest app analog (today):** `app.py:_render_current` status-bar message (~line 326 area) already reports vertex/face counts.

**Sketch:** `perf_counter` bracket around `surface.generate()`; append ` · {ms} ms` (or seconds) to the existing status-bar string. Optional debug-mode per-step breakdown (field / MC / smooth / normals). Pure telemetry — no AI interaction.

**Open questions:**
- Per-step breakdown always-on vs debug-flag-gated? (Recommend the total always-on, the breakdown behind a flag.)

---

### CAND-13 — Grid-resolution-cap tuning + skip-redundant-render hygiene

**Category:** Performance/numerics
**Size:** XS
**Evidence triangulation:** 2 briefs (adversary L-1/L-2/L-3, math-research §5 adaptive-resolution note)

**What it is:** Three small hygiene fixes: (a) lower the Fermat-quartic adaptive `n` cap from 260 to ~220 for the interactive path (260³ ≈ 17.6M voxels, measured 1.45 s — the comment claims "~1 s", already wrong); (b) lower Enriques Fig 4's hardcoded `n=260` to ~220 (its field is smooth, no near-singularities); (c) a `_render_dirty` flag to skip `plotter.render()` when nothing changed.

**Why it matters:** Pure tuning — no architecture change, no new code paths. Reserves the 260-resolution grids for the screenshot/export path where quality matters and latency does not.

**Sources:**
- Adversary scout L-1 (Fermat n cap), L-2 (Enriques Fig 4 n=260), L-3 (redundant `render()` calls)
- Math-research §5: adaptive-bounds + adaptive-n already partially implemented; this extends the tuning.

**Closest app analog (today):** `surfaces.py:225` (`n = np.clip(round(220*bounds/2.5), 200, 260)`), `surfaces.py:438` (Enriques Fig 4 `n=260`), `app.py:479` (unconditional `render()`).

**Sketch:** Adjust the two resolution caps; add a `_render_dirty` bool gating the final `render()`. Keep a separate higher-resolution path for screenshot/export (ties to a future export candidate).

**Open questions:**
- Is the quality delta between n=220 and n=260 truly imperceptible at viewport zoom? Spot-check with renders.

---

## 5. Cross-cutting tensions

1. **AI-15 honesty vs continuous-update fidelity.** A coarse-grid preview (CAND-3) can misrepresent topology — Kummer's 16 nodes merging, the Dwork conifold at ψ=1, Enriques double curves. Math-research Theme B + T-9 say this is honest *only* with a visible "coarse preview — true surface on release" disclaimer; the Stander-Hart/Plantinga-Vegter literature could upgrade that to a topology-guarantee but has no Python implementation. **Resolution:** CAND-3 ships with a mandatory status-bar disclaimer; the topology-guarantee refinement is a v2 parking-lot item.

2. **Parameter-space mesh interpolation is mathematically fraudulent.** Both competitive (C-5-adjacent) and math-research (T-7) surfaced morphing between cached meshes — visually smooth, near-free per frame — but the interpolated mesh corresponds to *no algebraic equation* and will show false geometry through topological bifurcations. **Resolution:** parking lot. Permissible only as an explicitly-labeled "animated transition", never as "the variety at this parameter" — and even disclaimed it is high-risk for a math-education tool. Not in the catalog.

3. **CAND-2 (Numba) vs CAND-10 (sub-expression cache) overlap.** Both attack the field-eval step. Numba is more general (every generator, no per-field decomposition) and numerically identical; sub-expression caching needs bespoke per-generator work and only helps single-parameter moves. **Resolution:** the challenger should assess whether CAND-10 survives once CAND-2 is on the table — likely demote CAND-10.

4. **GPU isosurfacing genuinely eliminates the bottleneck but conflicts with AI-1/AI-3.** SURFER's GPU raytracing and VTK's `vtkGPUVolumeRayCastMapper` (competitive C-9, math-research T-10) render implicit surfaces with no triangle mesh at all — instant parameter response — but produce a rasterized image, not a `pv.PolyData`: no domain clipping (AI-4), no mesh export, no Hanson normals (AI-7), and macOS Metal-backend support in VTK is still "experimental". **Resolution:** parking lot; revisit only if VTK's GPU path matures and the app accepts a separate non-mesh render mode.

5. **PySide6 ≥ 6.10 macOS hang risk.** OSS-trends flagged pyvistaqt issue #793 (Feb 2026) — pyvistaqt reportedly hangs on macOS with PySide6 ≥ 6.10. Any threading work (CAND-4) must verify and possibly pin `PySide6 <6.10`. This is a *constraint*, not a candidate — Phase 4 should note it as a spike/risk on CAND-4.

---

## 6. What's already in flight / already done

- **INT-2 render-on-release** — the deliberate current discipline this whole scout proposes to *augment* (not replace). Per CONTEXT.md interaction vocabulary, continuous re-render during drag is the INT-NO-1 anti-pattern *given the current architecture*; the candidates above are the architecture changes that would make a (coarse) drag-time render no longer an anti-pattern.
- **Adaptive bounds + adaptive `n`** — `fermat_quartic` and `kummer_surface` already scale the sampling box and resolution with parameters (`surfaces.py:218/225/282`). CAND-13 extends this tuning.
- **`_raw_mesh` cache (AI-10)** — single-slot cache already makes the domain-clip slider snappy. CAND-7 (LRU) and CAND-11 (clipped-mesh) extend it.
- **`smooth_iter` parameter** — `_marching_cubes_to_polydata` already accepts it; CAND-3's coarse path reuses it (`smooth_iter=0`).
- **Dwork conifold warning (AI-14)** — already emitted; CAND-3 makes it more important (a coarse preview is even less likely to capture the singularity).

---

## 7. Parking lot (surfaced but not cataloged)

- **Parameter-space mesh interpolation / morphing** — AI-15 violation (tension #2). Animated-transition-only, disclaimed; not a variety-rendering candidate.
- **GPU isosurfacing / raycasting (SURFER, VTK GPU volume mapper)** — AI-1/AI-3 conflict (tension #4); rasterized output breaks AI-4/AI-7 and mesh export.
- **Span-space / interval-tree isovalue acceleration** (math-research T-5) — accelerates *isovalue* sweeps, not *parameter* changes; the app has no isovalue slider. Inapplicable.
- **Dual contouring / surface nets / adaptive octree** (math-research T-6) — no production Python implementation in the LGPL stack; from-scratch is research-grade effort.
- **Incremental / windowed marching cubes** (competitive parking lot, math-research T-8) — re-extract only sign-changed cells; elegant but needs a stateful field cache + partial-update bookkeeping; CAND-3's coarse/fine LOD reaches similar latency with far less complexity.
- **SymPy → LLVM IR symbolic field pre-compilation** (math-research parking lot) — research-grade; superseded in practice by CAND-2.
- **Dask/Ray parallel marching cubes** — sub-volume stitching produces inconsistent boundary vertices; complex to do correctly.
- **trame / WebGPU browser companion** — AI-1 (desktop PySide6 app).

---

## 8. Evidence index

| Candidate | competitive | math-research | oss-trends | desktop-platform | adversary |
|---|---|---|---|---|---|
| CAND-1 Flying Edges | C-1 | T-3 | ✓ | ✓ | — |
| CAND-2 Numba JIT | C-10 | T-2 | ✓ | ✓ | — |
| CAND-3 Coarse LOD | C-2/C-6 | T-1/T-9 | ✓ | ✓ | H-1/M-1/M-2/M-3 |
| CAND-4 Background thread | C-4/C-11 | T-4 | ✓ | ✓ | C-1 |
| CAND-5 Queue-latest guard | C-3 ctx | — | — | — | C-2 |
| CAND-6 Debounce | C-3 | — | ✓ | ✓ | — |
| CAND-7 Mesh cache | C-5 | — | ✓ | ✓ | — |
| CAND-8 Hanson fast path | — | (Theme E) | — | — | H-3 |
| CAND-9 In-place mesh update | — | — | — | — | H-4 |
| CAND-10 Field sub-expr cache | — | — | — | — | H-2 |
| CAND-11 Clipped-mesh cache | — | — | — | — | M-4 |
| CAND-12 Timing telemetry | — | — | — | — | M-5 |
| CAND-13 Resolution-cap hygiene | — | §5 | — | — | L-1/L-2/L-3 |

---

*Synthesis written by the main session reading 5 survey briefs. Foundational candidates (CAND-12, CAND-4, CAND-5, CAND-6) flagged for Phase 4 DAG ordering. Two techniques parking-lotted on AI-15 (mesh interpolation) and AI-1/AI-3 (GPU isosurfacing) grounds.*
