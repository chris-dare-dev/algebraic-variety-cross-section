# agent-b research brief — realtime-variety-render-e4

**Milestone:** `realtime-variety-render-e4` — CAND-4 background-thread worker ONLY (CAND-3 coarse-LOD deferred to e4b).
**Lens:** VTK / PyVista / Qt-threading / re-entrancy.
**Date:** 2026-05-22

---

## 1. TL;DR

Use **`QThreadPool` + `QRunnable`** (not `QThread` + `moveToThread`): the e3 spike already proved this exact pattern works on Windows, the spike test script (`spike-thread-test.py`) is a ready-to-adapt working harness, and `QThreadPool` gives free supersede semantics — a stale worker just emits into a slot that drops it, no thread teardown needed. The main risk is the **worker-in-flight re-entrancy redesign** (AI-9): `_computing` stops being a synchronous in-method flag and becomes a job-generation counter so a rapid cancel-and-resubmit burst delivers only the *latest* mesh; getting the stale-result discard wrong silently renders an out-of-date surface. Backup plan if `QThreadPool` supersede proves fragile: keep one persistent `QThread`+worker-object and a monotonic job-id, discarding any signal whose id is not the latest requested — same discard logic, different thread primitive.

---

## 2. Prior art in this repo

- **`app.py:480-615` `_render_current`** — the method being restructured. Today: synchronous. Sets `self._computing = True` at `app.py:498`, shows `WaitCursor` at `app.py:500`, calls `QApplication.processEvents()` at `app.py:506` (the workaround the brief says to remove), calls `surface.generate(**params)` synchronously at `app.py:521` inside a `warnings.catch_warnings(record=True)` block, brackets it with `time.perf_counter()` at `app.py:514`/`549` (CAND-12 telemetry), catches `ValueError`/`Exception` at `app.py:530`/`544`, and in the `finally` (`app.py:600-615`) restores the cursor, clears `_computing`, and fires the `_pending_render` catch-up via `QTimer.singleShot(0, ...)`.
- **`app.py:494-497` the e1 queue-latest guard** — `if self._computing: self._pending_render = True; self._pending_reset_camera = reset_camera; return`. This is the exact mechanism the brief says to "extend to cover worker-in-flight". Today it works because the whole render is synchronous, so `_computing` is only ever True for the duration of one call stack. With a worker, `_computing`-True spans *event-loop iterations*, and `_pending_render` must coalesce multiple drag ticks into one resubmit.
- **`app.py:600-615` the `finally` catch-up block** — `QTimer.singleShot(0, lambda: self._render_current(reset_camera=_catch_up_reset))`. With a worker this logic moves into the worker-result slot (the `finally` no longer marks "render complete" — only "job dispatched").
- **`app.py:139` `self._raw_mesh = None`** init; **`app.py:524` `self._raw_mesh = new_mesh`** assignment — the critical hand-off point. In the worker design the worker produces `new_mesh`; the main-thread slot assigns `self._raw_mesh` (VTK #18782: this assignment IS the main-thread ref-retention).
- **`app.py:140-148, 617-628` the CAND-11 `_clipped_mesh` cache + `_invalidate_clipped_mesh()`** — must still be invalidated when a worker result lands (the `self._raw_mesh = new_mesh; self._invalidate_clipped_mesh()` pair at `app.py:524-525` moves into the slot).
- **`app.py:630-718` `_apply_domain_and_render`** — unchanged in body; the brief says it "receives the worker result via a Qt.QueuedConnection signal", meaning the *slot* calls `_apply_domain_and_render(reset_camera=...)` after assigning `_raw_mesh`. All VTK GL calls (`plotter.add_mesh` `app.py:694`/`664`/`705`, `plotter.render()` `app.py:683`/`718`, `reset_camera` `app.py:716`) live here — they stay main-thread. Good: no GL call needs to move.
- **`app.py:413-455` `_on_params_changed` / `_on_params_preview_changed`** — the two render entry points (release + debounced drag tick). Both call `_render_current`; both inherit the new worker dispatch automatically.
- **`app.py:457-466` `_on_domain_changed`** — calls `_apply_domain_and_render` *directly* (AI-10: no regenerate). This path does NOT go through the worker — it re-clips the cached `_raw_mesh`. Confirm the worker refactor leaves this synchronous path intact.
- **`surfaces.py:32-49` `Surface` dataclass** — `generate: Callable[..., pv.PolyData]`; `typical_ms` field. The worker calls `surface.generate(**params)` exactly as `_render_current` does today. No `surfaces.py` change needed for e4.
- **`surfaces.py:60-78` `should_render_on_drag`** — pure predicate; unchanged. The worker dispatch is orthogonal to speed-routing.
- **`ui_helpers.py:96-165` `Debouncer`** — single-shot `QTimer`; its docstring (`ui_helpers.py:117-119`) explicitly states the debounced callback "never inside `_render_current`'s `_computing` window — so it composes with the `_computing` guard". The worker refactor must preserve this composition property.
- **e3 spike test `spike-thread-test.py`** — a *working* `QRunnable` + `WorkerSignals(QObject)` + `Qt.QueuedConnection` + explicit `self._result` retention harness. Lines 81-116 are the directly-adaptable `WorkerSignals`/`MeshWorker` classes. Variant B (lines 201-272) is the rapid cancel-and-resubmit stress that mirrors e4's supersede path.
- **e3 spike report** (`spike-cand4-thread-safety.md`) §6 has the concrete VTK #18782 mitigation code; §7 the macOS pre-ship checklist (manual gate, cannot run on Windows).
- **CONTEXT.md §4.4 / §8.5 / AI-9** — the documented `_computing` + `processEvents` re-entrancy contract being rewritten.
- **CONTEXT.md §9** — "No tests for app.py / MainWindow" — the existing documented Qt-test gap that the e4 worker-lifecycle gap extends.

**No production worker/thread code exists** — grep for `QThread|QRunnable|QThreadPool|moveToThread|worker` finds matches only in `.claude/notes/` and the spike script, never in `app.py`/`surfaces.py`/panels. This is greenfield in `app.py`.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| e3 spike report (repo) | `.claude/notes/roadmaps/realtime-variety-render/spike-cand4-thread-safety.md` | 3/3 stress variants PASS on Windows; VTK #18782 mitigation = `self._result = mesh` before emit + main-thread slot retains ref; e4 cleared to proceed; do NOT tighten PySide6 pin (pyvistaqt 0.11.4 has #793 fix). | Primary — the authoritative go decision + mitigation spec. |
| e3 spike test script (repo) | `.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py` | Working `QRunnable`+`WorkerSignals(QObject)`+`Qt.ConnectionType.QueuedConnection`+`self._result` retention. Uses `QThreadPool.globalInstance()`, `setMaxThreadCount(4)`. | Primary — directly adaptable worker skeleton. |
| desktop-platform scout brief (repo) | `.claude/notes/capability-scouts/realtime-variety-render/survey/desktop-platform-brief.md` C-1 | "PyVista mesh operations (`pv.PolyData`, marching cubes, `mesh.clean()`) are data-structure manipulations, not render calls, and are thread-safe. Only `plotter.add_mesh()`/`plotter.render()` must stay on GUI thread." Confirms AI-9 guard "moves to job-submission check rather than blocking compute". PySide6 releases the GIL during QThread execution → real parallelism. | Confirms the worker/GL split is sound; sizes the refactor at M (2-4 days). |
| pyvista discussion #4006 | github.com/pyvista/pyvista/discussions/4006 | Maintainer-confirmed pattern: data generation safe on background threads; all rendering on GUI thread. Worker-builds-PolyData / main-renders is the accepted community split. (Cited via spike report §3.3 — page itself not re-fetched.) | Confirms the architectural split is the canonical pattern, not a workaround. |
| VTK GitLab #18782 | gitlab.kitware.com/vtk/vtk/-/issues/18782 | SMP + Python-GC crash when worker-built `pv.PolyData` is released. Mitigation: explicit Python ref retention across the cross-thread hand-off. (Page returns "Access Denied" — spike report §3.2 is the operative secondary source.) | Mandatory mitigation; drives the `self._result` + slot-retain rule. |
| pyvistaqt #793 / PR #810 | github.com/pyvista/pyvistaqt/issues/793, pull/810 | macOS-only Cocoa event-loop hang on PySide6 ≥6.10; fixed in pyvistaqt 0.11.4 (already pinned `>=0.11.4,<0.12` in `requirements.txt`). | Confirms NO `requirements.txt` change needed (brief AI-1 constraint). |
| Qt 6 docs — QThreadPool/QRunnable | doc.qt.io/qtforpython-6/PySide6/QtCore/QThreadPool.html | `QRunnable` is not a `QObject` and cannot emit signals directly — attach a `QObject` signal-carrier. `QThreadPool` auto-deletes runnables (`setAutoDelete`) after `run()` returns. Pool keeps the runnable alive until `run()` completes. | Drives the `WorkerSignals(QObject)` carrier pattern and the ref-lifetime reasoning. |
| superqt `qdebounced` | superqt.readthedocs.io | BSD-3-Clause debounce decorators. NOT needed — repo already has `ui_helpers.Debouncer`; no new dep. | Rejected — see §5. |

---

## 4. Recommended approach

**Primary: `QThreadPool` + `QRunnable` worker with a monotonic job-id supersede guard.** Adapt the spike's `WorkerSignals`/`MeshWorker` classes into `app.py` (a small private worker class, or a new `render_worker.py` module — implementer's call; one file is fine for ~60 LOC).

**Worker (`QRunnable`):** holds `job_id: int`, `surface`, `params`, a `WorkerSignals(QObject)` carrier with `finished = Signal(int, object)` and `failed = Signal(int, str)` (carry the `job_id` so the slot can discard stale results). `run()` wraps `surface.generate(**params)` in `warnings.catch_warnings(record=True)` exactly as `_render_current` does today (the RuntimeWarning capture for the Dwork conifold per CONTEXT.md §4.6 must move into the worker — capture the warning text and emit it alongside the mesh, e.g. `finished.emit(job_id, mesh, warning_str)`). On `ValueError` or any `Exception`, emit `failed.emit(job_id, str(exc))`. **VTK #18782:** `self._result = mesh` before `finished.emit(...)`.

**MainWindow dispatch (`_render_current` becomes submit-only):**
- Replace `self._computing: bool` with `self._current_job_id: int` (monotonic) and `self._inflight_job_id: int | None`.
- On a render request: increment `_current_job_id`, build a worker with that id, store it in `self._inflight_worker` (Python ref keeps it alive — belt-and-suspenders alongside `QThreadPool`'s own retention), set the `WaitCursor`, show `Computing …`, `pool.start(worker)`, return. **No `processEvents()`** — the event loop is already free because the compute is off-thread.
- A new request while one is in flight does NOT block: it just increments the id and submits a new worker. The old worker still runs to completion but its result is discarded by id mismatch. This IS the queue-latest semantic — and it supersedes *better* than e1's `_pending_render` because there is no serialization wait.

**Result slot (`@Slot(int, object, str)`, `Qt.QueuedConnection`):**
- `if job_id != self._current_job_id: return` — discard stale/superseded results.
- `self._raw_mesh = mesh` (VTK #18782: main-thread ref retention, immediate). `self._invalidate_clipped_mesh()`.
- Run the existing post-generate body: telemetry log, `_apply_domain_and_render(reset_camera=...)`, status-bar `base_msg` / warning-path formatting (`app.py:549-599`). `reset_camera` must be carried on the worker (or in a dict keyed by job_id) since the slot fires later.
- Restore cursor, clear `_inflight_worker` ref.

**Failure slot (`@Slot(int, str)`):** id-check, then the existing `ValueError`/`Exception` status-bar branches (`app.py:530-548`) — set `_raw_mesh = None`, `_invalidate_clipped_mesh()`, show message. The "No real zero set" prefix logic is preserved by passing through enough info (emit a category flag or re-classify the message string).

**AI-9 re-analysis (the load-bearing part):** today's hazard is `processEvents()` re-entering `_render_current` mid-call. Removing `processEvents()` *eliminates* that re-entrancy class entirely — the worker dispatch is fire-and-return, never drains the event queue mid-method. The NEW hazard is **stale-result delivery**: the id-guard at the top of the result slot is the sole defense and must be the first statement. A secondary subtlety: `_on_domain_changed` (`app.py:457`) still runs synchronously and reads `_raw_mesh` — if a worker result lands between a domain change and its re-clip, the id-guard does not cover it, but this is benign (the domain path always re-reads the current `_raw_mesh`). Document the new contract in CONTEXT.md §4.4.

**Telemetry:** the `time.perf_counter()` bracket moves into the worker's `run()` (around `surface.generate`); emit `_gen_ms` alongside the mesh so the slot's `print("[render] ...")` + status-bar `NNN ms` (CAND-12) still work.

---

## 5. Alternatives considered

- **`QThread` + `moveToThread(worker)` persistent worker object** — viable backup, but a persistent thread needs explicit lifecycle teardown in `closeEvent` and an in-thread job queue; `QThreadPool` gives supersede for free. Keep as the backup plan if pool supersede misbehaves.
- **Subclassing `QThread` and overriding `run()`** — Qt docs and community guidance discourage it (the `QThread` object lives on the *creating* thread; only `run()` is on the new thread — easy to get signal affinity wrong). Rejected.
- **`concurrent.futures.ThreadPoolExecutor`** — no Qt event-loop integration; delivering the result back to the GUI thread still needs a `QTimer`/signal bounce. `QThreadPool` is already the right primitive and is what the spike validated. Rejected.
- **`superqt.qdebounced` / `superqt` worker utilities** — adds a dependency for something `ui_helpers.Debouncer` (debounce) and a ~60-LOC worker class (dispatch) already cover. AI-1 favors minimal deps. Rejected.
- **Keeping `_computing` as a bool and adding `_pending_render` for the worker** — a bool cannot express "which job is latest"; a fast burst of 5 ticks needs a *counter* so the slot can discard 4 stale results. The e1 bool+flag worked only because the render was synchronous. A monotonic id is required. Rejected (this is a redesign, not an extension — say so in the brief to the implementer).
- **Cancelling the in-flight worker** (`QThreadPool` has no real preemption; `QRunnable` cannot be interrupted mid-`generate()`) — there is no clean cancel; the stale worker runs to completion and its result is discarded by id. Accept this (a superseded `generate()` wastes one core for <0.5 s — harmless). Do NOT attempt a cooperative-cancel flag inside `surface.generate` (would require touching every generator — out of scope, AI-8).

---

## 6. Risks and unknowns

- **AI-9 (re-entrancy) — the central risk.** The `_computing` bool→job-id-counter change is a *semantic redesign*. The stale-result discard (`if job_id != self._current_job_id: return`) must be the first line of the result slot AND the failure slot. Miss it and a slow superseded worker silently overwrites `_raw_mesh` with an out-of-date surface after the user has already moved the slider. The implementer must re-derive the AI-9 analysis from scratch — quoting the old `_computing` contract is not sufficient.
- **AI-2 (Qt-free tests) — known coverage gap, must be documented in CONTEXT.md §9.** What CAN be tested Qt-free: (a) the worker's *pure compute call* — `surface.generate(**params)` is already covered by `tests/test_mesh_generators.py`; (b) a pure-function supersede predicate, if the implementer extracts one — e.g. `is_latest_job(job_id, current_id) -> bool` as a free function mirroring the `clipped_cache_is_valid` / `should_render_on_drag` precedent (both are Qt-free free functions extracted precisely so the logic is unit-testable — `app.py:56-83`, `surfaces.py:60-78`). Strongly recommend the implementer extract the id-comparison as such a free function. What genuinely CANNOT be tested Qt-free: the live `QThreadPool` dispatch, the `QueuedConnection` signal delivery, the worker-in-flight cancel-and-resubmit timing, and `closeEvent` teardown — all need a running `QApplication` and `pytest-qt`, which AI-2 forbids until the macOS Qt+VTK offscreen segfault is resolved. The e3 spike script (`spike-thread-test.py`) is the *manual* substitute regression harness — it can be re-run on demand. Document this gap explicitly in CONTEXT.md §9 alongside the existing "No tests for app.py / MainWindow" entry.
- **VTK #18782 (PolyData ownership) — AI-7/AI-10/AI-14 adjacent.** The mesh is built on the worker; `self._result = mesh` before emit keeps refcount >0 across the hand-off; the slot's `self._raw_mesh = mesh` is the main-thread retention. The window between emit and slot execution is covered because the worker object (holding `self._result`) is kept alive by `QThreadPool` until `run()` returns AND by `self._inflight_worker` on the main side. Risk: if the implementer clears `self._inflight_worker` *before* the result slot runs, the only ref is `self._result` inside a runnable the pool may have already auto-deleted — clear `_inflight_worker` *inside* the result slot, not at dispatch. The spike validated this on Windows; macOS arm64 is the residual unknown (spike §7 manual gate).
- **macOS pre-ship gate.** The spike's §7 checklist (pyvistaqt #793 confirmation under PySide6 6.11.x, worker+`QtInteractor` coexistence, full `add_mesh`+`render` path, rapid-supersede stress under Cocoa, VTK SMP backend check, `processEvents` Cocoa run-loop semantics) cannot run on this Windows machine. Implementation proceeds on Windows per spike guidance; the checklist is a documented manual gate before shipping. The implementer should add a CONTEXT.md note pointing to spike §7.
- **`processEvents()` removal — status-bar liveness.** Today `processEvents()` at `app.py:506` exists to repaint the `Computing …` message during the blocking generate. With the worker, the event loop is free, so the status bar updates naturally — but the implementer must still call `showMessage("Computing …")` *before* `pool.start()` so the message paints. Removing `processEvents()` is correct and required; just sequence the status update before dispatch.
- **`WaitCursor` lifetime.** `QApplication.setOverrideCursor(WaitCursor)` at dispatch must be paired with `restoreOverrideCursor()` in *both* the result slot and the failure slot (today it is in the `finally`). A superseded job that never reaches a non-stale slot must not leak a cursor push — since each dispatch pushes one cursor, ensure exactly one restore per dispatch. Cleanest: push the cursor on dispatch, restore it in whichever slot handles that job_id; for a *superseded* job whose slot returns early on the id-check, the restore still must happen — so restore the cursor *before* the id-check return, or (simpler) only show the WaitCursor for the latest job and restore unconditionally at the top of every slot. Flag this for careful implementation — it is a classic worker-refactor leak.
- **~500 ms render budget.** Unchanged — the worker does not speed up `generate()`; it moves the cost off the GUI thread so the slider stays live. The destination latency win (coarse-LOD) is e4b. e4's user-visible win is purely "the GUI no longer freezes".
- **`_on_params_preview_changed` interaction.** Fast drag ticks (Hanson, `should_render_on_drag` True) now each dispatch a worker. Hanson `generate()` is 11-39 ms (`surfaces.py:1048-1067`) — bursts of workers complete fast and the id-guard discards superseded ones cleanly. No special-casing needed; the supersede guard handles it. Confirm the worker dispatch path does not regress the e2 continuous-drag behavior.
- **`closeEvent` (`app.py:885`)** — add `QThreadPool.globalInstance().waitForDone(<timeout>)` (or `clear()` + `waitForDone()`) before `self.plotter.close()` so a worker is not still touching `pv.PolyData` while the VTK context tears down. The spike used `pool.waitForDone(30000)`.

---

## 7. AI-15 disclaimers

**N/A for this milestone.** e4 adds no new variety, figure, or mathematical object — it is a pure threading refactor of the existing render dispatch. No "real shadow" / "birational" / "parametric cross-section" disclaimer applies. (The AI-15 "Preview" badge that *would* accompany coarse-LOD is explicitly deferred to e4b per the milestone brief and roadmap §6.3.)

---

## 8. Open questions for the user

None. The milestone brief is fully specified: scope is split (CAND-4 only), the e3 spike cleared e4 to proceed with a concrete mitigation, the `requirements.txt` pin decision is settled (no change), and the AI-2 test gap is acknowledged as documentation-only. The one implementer-level decision — `QThreadPool`+`QRunnable` vs `QThread`+`moveToThread` — is resolved in §4 (primary + backup) and does not need user input.
