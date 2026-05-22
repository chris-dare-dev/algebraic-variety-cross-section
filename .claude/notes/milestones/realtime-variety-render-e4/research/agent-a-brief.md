# Research Brief — realtime-variety-render-e4 (agent-a)

**Milestone:** `realtime-variety-render-e4` — SPLIT SCOPE: CAND-4 (background-thread worker) ONLY.
CAND-3 (coarse-preview LOD) deferred to follow-up `e4b` per user scope decision + roadmap §6.3.
**Researcher:** agent-a · **Date:** 2026-05-22 · **Status:** complete

---

## 1. TL;DR

Move `surface.generate()` off the GUI thread onto a `QRunnable` + `QThreadPool` worker using
the *exact* pattern the e3 spike already validated (`spike-thread-test.py` §`MeshWorker`):
worker builds `pv.PolyData`, retains `self._result = mesh` before emitting a `Qt.QueuedConnection`
`Signal(object)`, and a main-thread `@Slot` retains the ref immediately on receipt — all VTK GL
calls (`add_mesh`/`render`) stay on the GUI thread. **Main risk:** the e1 `_computing` /
`_pending_render` queue-latest guard must be *extended* (not replaced) so the in-flight state
spans the entire async worker round-trip, and the live worker reference must be held by
`MainWindow` for the full flight or the supersede path drops it mid-run (VTK #18782). **Backup
plan:** if `QThreadPool`-managed worker lifetime proves hard to reason about for the supersede
case, use a single explicit `QThread` + moved `QObject` worker with a generation-counter (stale
results discarded by id) — same signal/ref discipline, more deterministic ownership.

---

## 2. Prior art in this repo

- **`app.py:480-615` `_render_current`** — the synchronous dispatch this milestone rewrites.
  Today: `_computing` set at `app.py:498`, `surface.generate(**params)` called *synchronously*
  inside `warnings.catch_warnings` at `app.py:519-521`, `processEvents()` at `app.py:506`,
  `_apply_domain_and_render` at `app.py:553`, `_computing` cleared in the `finally` at
  `app.py:602`. **All of this becomes asynchronous** — the `try` body splits across two stack
  frames (dispatch frame + worker-result slot frame).
- **`app.py:494-497` the queue-latest guard** — e1-s2 (CAND-5, commit `3e40ddf` per brief):
  `if self._computing: self._pending_render = True; self._pending_reset_camera = reset_camera; return`.
  This is the pattern the milestone says to *extend*. Read end-to-end: the guard's contract is
  "one render in flight + at most one queued catch-up that re-reads the LATEST param values."
- **`app.py:600-615` the `finally` catch-up** — `QTimer.singleShot(0, lambda: self._render_current(...))`.
  In the worker design this catch-up scheduling moves into the **worker-result slot**, because
  "in flight" now ends when the worker signal arrives, not when the dispatch function returns.
- **`app.py:139,148,150,158,162` the MainWindow state slots** — `_raw_mesh`, `_clipped_mesh`,
  `_computing`, `_pending_render`, `_pending_reset_camera`. The worker design adds at least one
  new slot for the live worker ref (e.g. `self._active_worker`).
- **`app.py:515-548` the warnings + exception handling** — `catch_warnings(record=True)`,
  `except ValueError` (sets `_raw_mesh=None`, status bar, `return`), `except Exception`. **This
  must move INTO the worker** — `warnings.catch_warnings` is not thread-shared, and an exception
  raised on the worker thread cannot be caught by a main-thread `try`. The worker must capture
  the warning text + any exception and ship them across the signal as part of the payload.
- **`app.py:514,549-551` the CAND-12 timing bracket** — `_gen_t0 = time.perf_counter()` ...
  `_gen_ms`. The `perf_counter` start must move to the worker (or to dispatch time); the
  duration is computed in the worker and shipped in the payload so the status-bar `NNN ms`
  token at `app.py:582` survives.
- **`ui_helpers.py:96-165` `Debouncer` / `DebounceCounter`** — e1-s4 (CAND-6). The `Debouncer`
  docstring (lines 113-119) explicitly states it "composes with the `_computing` guard and the
  s2 `QTimer.singleShot(0)` catch-up without re-entrancy." The worker design must preserve that
  composition: a debounced drag tick still calls `_render_current`, which now does a
  *non-blocking* worker dispatch instead of a blocking generate.
- **`surfaces.py:32-78` `Surface` dataclass + `should_render_on_drag`** — `typical_ms` field
  (e2-s1, CAND-8). The worker payload should round-trip the surface label; the speed-routing
  predicate is unaffected — fast (Hanson) surfaces still route through `_render_current`, which
  now dispatches a worker for *every* surface uniformly.
- **`app.py:457-466` `_on_domain_changed`** — re-clips the *cached* `_raw_mesh` without
  regenerating (AI-10). **This path must NOT spawn a worker** — it calls
  `_apply_domain_and_render` directly. Only `surface.generate()` moves to the worker;
  `clip_to_domain` stays synchronous on the GUI thread (it is fast and touches no shared state).
- **`.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py:81-117`** — the e3
  spike's `WorkerSignals` (`QObject` with `finished = Signal(object)` + `error = Signal(str)`)
  and `MeshWorker` (`QRunnable` with `self._result` retention). **This is the production
  blueprint.** Variants A/B/C all PASSED on Windows; the supersede stress (Variant B, 30 cycles,
  80 ms overlap) is the rapid cancel-and-resubmit path e4 must replicate.
- **`app.py:885-897` `closeEvent`** — already calls `self.plotter.close()`. The worker design
  should ensure no worker is mid-flight emitting into a torn-down window — drain
  `QThreadPool.globalInstance().waitForDone()` or disconnect signals here.
- **CONTEXT.md §4.4 / §8.5 / AI-9** — the `processEvents` re-entrancy guard. The milestone
  *removes* the `processEvents()` workaround (`app.py:506`); see §6 for the AI-9 re-analysis.
- **CONTEXT.md §9 / `.claude/references/app-invariants.md` AI-2** — "No tests for app.py /
  MainWindow." The worker-lifecycle / cancel-resubmit coverage gap must be documented in
  CONTEXT.md §9 (the milestone mandates this).

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| e3 spike report | `.claude/notes/roadmaps/realtime-variety-render/spike-cand4-thread-safety.md` | e4 cleared to proceed; QRunnable+QueuedConnection+`self._result` retention validated 3/3 on Windows; pyvistaqt 0.11.4 has #793 fix; **do not** tighten PySide6 pin | The mandatory blueprint — §6 worker code skeleton, §7 macOS gate |
| e3 spike test script | `.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py` | Working `WorkerSignals`/`MeshWorker` reference impl; `QThreadPool.globalInstance()`, `Signal(object)`, `error = Signal(str)` | Direct production blueprint — port `MeshWorker.run()` verbatim, parameterize the generator call |
| capability-scout final report | `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` §3 rank-10 | CAND-4 spec: worker hands `pv.PolyData` via `Qt.QueuedConnection`; `_computing`→"worker in flight"; remove `processEvents`; challenger MAJOR (a) effort, (b) #793, (c) #18782, (d) AI-2 test gap | Defines the milestone scope + the 4 challenger objections to design around |
| roadmap §6.3 epic e4 | `plans/realtime-variety-render-roadmap.md:170-177` | Specialist hint: `_computing` guard changes blocking→"worker in flight"; AI-9 re-entrancy must be re-done for worker dispatch path | Confirms split-scope (CAND-3 → e4b) and the AI-9 re-analysis mandate |
| pyvista discussion #4006 | https://github.com/pyvista/pyvista/discussions/4006 (via spike report §3.2-3.3) | Accepted community pattern: data generation safe off-thread; ALL rendering (`add_mesh`/`render`/GL) must stay on GUI thread; explicit Python ref retention prevents GC crash | Confirms the worker/render split is the canonical pattern, not a local invention |
| VTK GitLab #18782 | https://gitlab.kitware.com/vtk/vtk/-/issues/18782 (Access Denied; via spike §3.2) | SMP + Python-GC interaction can crash when worker-built `PolyData` is dropped; mitigation = explicit ref kept until main thread has retained | The mandatory `self._result = mesh` discipline |
| pyvistaqt #793 / PR #810 | https://github.com/pyvista/pyvistaqt/issues/793, /pull/810 (via spike §3.1) | macOS-only `QtInteractor` hang on PySide6 ≥6.10; FIXED in pyvistaqt 0.11.4 (already pinned `>=0.11.4,<0.12`) | No pin change needed; macOS on-device gate remains (spike §7) |
| PySide6 `QThreadPool`/`QRunnable` docs | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QRunnable.html | `QRunnable` cannot emit signals itself — needs a child `QObject` carrier (`WorkerSignals`); `QThreadPool` owns the runnable's lifetime through `run()`; `setAutoDelete` default True | Confirms the `WorkerSignals` carrier pattern; informs the live-ref ownership decision |

*All findings above are first-party project docs or Qt/PyVista official docs — no third-party
OSS code is being adopted, so no license audit applies. The only dependency surface is the
already-pinned `PySide6 / pyvista / pyvistaqt` stack (`requirements.txt`).*

---

## 4. Recommended approach

**Port the e3 spike's `MeshWorker` pattern into production, with a generation-counter for the
supersede path.**

**Worker (`QRunnable` + `WorkerSignals` carrier):** Define a `WorkerSignals(QObject)` with
`finished = Signal(object)` and a `MeshWorker(QRunnable)` taking `(generate_callable, params,
label, generation_id)`. Its `run()` does the *entire* current `try`-body compute: wrap
`generate(**params)` in `warnings.catch_warnings(record=True)`, capture the first
`RuntimeWarning` text, time it with `perf_counter`, and `except (ValueError, Exception)` to
capture the error. It packages a result object — `{mesh | None, warning_text, error_kind,
error_msg, gen_ms, generation_id}` (a small dataclass or tuple) — sets `self._result = <that
object>` (VTK #18782 ref retention), then `self.signals.finished.emit(result)`. Connect with
`Qt.ConnectionType.QueuedConnection`.

**Dispatch (`_render_current`):** Keep the function name and the `_current_surface is None`
early-return. Replace the synchronous body. The `_computing` guard semantics flip from
"blocking compute window" to **"worker in flight"**: if `self._computing` is True, set
`_pending_render = True` + `_pending_reset_camera` and return (UNCHANGED — this is the e1
queue-latest contract, now spanning the async window). Otherwise: set `_computing = True`,
`setOverrideCursor(WaitCursor)`, increment `self._generation` (a monotonically increasing int),
read `params = self.parameters_panel.values()`, show `"Computing …"`, construct a `MeshWorker`
with the current `_generation`, **store it in `self._active_worker`** (the MainWindow-held live
ref — keeps the worker + its `self._result` alive across the flight), connect `finished`, and
`QThreadPool.globalInstance().start(worker)`. Then return — the GUI thread is now free.
**Remove the `QApplication.processEvents()` call entirely** (`app.py:506`).

**Result slot (`@Slot(object)` `_on_mesh_ready`):** Runs on the GUI thread (QueuedConnection
guarantees this). FIRST line: retain the mesh — `mesh = result.mesh` (main-thread ref before
the worker's `_result` can be GC'd). **Discard stale results:** if `result.generation_id !=
self._generation`, this is a superseded job — drop it, do nothing (no render). Else: this is
the latest job — apply it. Handle the error/warning branches exactly as `app.py:530-548`
currently does (`_raw_mesh = None`, `_invalidate_clipped_mesh`, status bar) but now in this
slot. On success: `self._raw_mesh = mesh`, `_invalidate_clipped_mesh`, `_apply_domain_and_render`,
build the status-bar message (`app.py:555-599` logic moves here). FINALLY: `restoreOverrideCursor`,
`_computing = False`, `self._active_worker = None`, and **the catch-up** — if `_pending_render`,
clear it and `QTimer.singleShot(0, lambda: self._render_current(reset_camera=_catch_up_reset))`.

**Why a generation counter on top of the worker ref:** `QThreadPool` may have >1 thread; a
rapid drag can have an old worker still in `run()` when a new one is dispatched. The
`_computing` guard already coalesces *dispatch* (only one worker is ever in flight from the
guard's POV — extra requests become `_pending_render`), so in practice at most one worker is
"current." But a superseded worker whose `run()` already finished can still deliver a queued
`finished` signal *after* `_computing` was cleared and a new worker started. The generation id
makes the slot idempotent against that race — drop any result whose id ≠ current. This is the
robust, low-cost insurance the supersede / cancel-and-resubmit path needs.

**What stays on the GUI thread (AI-1 / spike §8.4):** `add_mesh`, `render`, `reset_camera`,
`plotter.*`, `clip_to_domain`, `apply_to_actor`, all of `_apply_domain_and_render`. The worker
touches *only* `surface.generate()` and pure NumPy/PyVista mesh construction.

---

## 5. Alternatives considered

- **Explicit `QThread` + `moveToThread(worker)`** — more verbose ownership; viable backup
  (TL;DR) but `QThreadPool`+`QRunnable` is what the e3 spike already validated, so it is the
  lower-risk default. Keep this in reserve only if pool-managed lifetime obscures the supersede case.
- **`concurrent.futures.ThreadPoolExecutor` + `QTimer` polling** — non-Qt thread pool; loses
  the `QueuedConnection` thread-affinity guarantee that delivers the result *on* the GUI thread,
  reintroducing a manual marshal. Rejected — fights the Qt event loop.
- **Keep `processEvents()` as a "safety net" alongside the worker** — defeats the purpose;
  re-introduces the exact AI-9 re-entrancy surface the milestone removes. Rejected.
- **Cancel the in-flight worker on supersede (interrupt `generate()`)** — `surface.generate()`
  is pure NumPy/VTK with no cancellation token; interrupting it cleanly is impossible. The
  queue-latest + generation-id "let it finish, discard the result" approach is correct and is
  what e1 already established. Rejected (not actually cancellable).
- **`superqt.@qthrottled`/thread helpers** — adds a dependency (BSD-3) for what is ~40 lines of
  `QRunnable`; the e3 spike proved the hand-rolled pattern. Rejected — no dependency justified.
- **Tighten `PySide6` pin to `<6.10`** — explicitly rejected by spike §5/§8: pyvistaqt 0.11.4
  already carries the #793 fix; `>=6.6,<7` stays. (Hard constraint AI-1 in the brief.)

---

## 6. Risks and unknowns

- **AI-9 re-entrancy re-analysis (MANDATORY).** Removing `processEvents()` removes the *original*
  re-entrancy source — slider-release events can no longer drain mid-`_render_current`. The new
  re-entrancy surface is the **`finished` signal slot**: `_on_mesh_ready` calls
  `_apply_domain_and_render` → `plotter.render()`, and the `finally` schedules a
  `QTimer.singleShot(0)` catch-up. Because the slot runs on the GUI thread via
  `QueuedConnection`, it is *serialized* with all other GUI events — it cannot re-enter itself.
  The catch-up `singleShot(0)` runs on a *later* event-loop turn with `_computing` already
  False, so it enters `_render_current` cleanly (same as e1). **Verdict: the worker design is
  AI-9-safe AND strictly better than the `processEvents` version** — there is no synchronous
  event-queue drain anywhere in the render path anymore. The implementer must still confirm:
  (a) no `processEvents()` is reintroduced; (b) `_computing` is set *before* `start(worker)` and
  cleared *only* in the slot (not in the dispatch function); (c) the dispatch function does NOT
  fall through to `_apply_domain_and_render` (that moves entirely into the slot).
- **VTK #18782 PolyData ownership (AI-7 / AI-10 / AI-14).** The `self._result = mesh` retention
  in the worker + `mesh = result.mesh` as the *first* slot line is non-negotiable (spike §6).
  Additional hazard for the **supersede path**: `MainWindow` must hold `self._active_worker`
  for the worker's whole flight — if the only ref is a local in `_render_current`, the worker
  (and its `self._result`) can be GC'd the instant dispatch returns. Hold the worker ref on the
  instance; release it (`self._active_worker = None`) only in the slot's `finally`, *after* the
  main thread has retained the mesh into `self._raw_mesh`. Note `QRunnable` default
  `setAutoDelete(True)` deletes the C++ side after `run()` — the Python `WorkerSignals` child
  and `self._result` must outlive that; holding the Python worker ref on `MainWindow` covers it.
- **~500 ms render budget.** This milestone does NOT make `generate()` faster (that is e4b/e5) —
  it makes the GUI *responsive during* the ~0.5–1.45 s. Acceptance is "GUI does not freeze," not
  "render is fast." Status bar should show `"Computing …"` immediately and the busy cursor
  should be visible the whole flight (set in dispatch, restored in slot).
- **AI-2 worker-lifecycle test gap (MUST be documented in CONTEXT.md §9).** The worker dispatch,
  the supersede/generation-id discard, and the cancel-and-resubmit coalescing all require a live
  `QApplication` + event loop to exercise — `pytest-qt` is an AI-2 BLOCKER (macOS Qt+VTK
  offscreen segfault). **Mitigation already partly in place:** the *pure* logic can still be
  Qt-free-tested — extract the generation-id staleness predicate as a free function (mirror the
  `clipped_cache_is_valid` / `should_render_on_drag` pattern, e.g.
  `is_stale_result(result_gen, current_gen) -> bool`) so the discard decision has a unit test.
  The async lifecycle itself stays uncovered; document this in CONTEXT.md §9 and point at the
  e3 spike script + the spike §7 macOS on-device checklist as the substitute acceptance gate.
- **macOS pre-ship gate (cannot run on Windows).** Spike §7's 6-item on-device checklist
  (QtInteractor under PySide6 6.11.x, worker+QtInteractor coexistence, full add_mesh+render
  path, rapid supersede under Cocoa, VTK SMP backend, processEvents drain) is a documented
  manual gate. Implementation proceeds on Windows per spike guidance; the checklist is a
  pre-ship blocker, not a pre-implementation one.
- **Status-bar / warning ordering.** The Dwork conifold `RuntimeWarning` (`app.py:583-597`) is
  caught inside `warnings.catch_warnings` — that context manager must wrap the `generate()` call
  *inside the worker*, and the warning text shipped in the payload. A `catch_warnings` on the
  main thread cannot see a warning raised on the worker thread. Same for the CAND-12 `[render]
  … ms` stdout `print` (`app.py:551`) — emit it from the slot using the payload's `gen_ms`.
- **Reset-camera flag plumbing.** `reset_camera` is a per-call argument today. It must be
  carried from dispatch into the worker payload (or stored alongside `_generation`) so the slot
  knows whether to `reset_camera()`. The existing `_pending_reset_camera` slot already models
  this for the catch-up; extend the same idea to the in-flight job.
- **Effort.** Challenger rated CAND-4 L (final-report §3 rank-10), realistically L+ once the
  async refactor of `_render_current` + the slot split + CONTEXT.md §9 doc are counted. The
  split-scope (CAND-3 dropped) keeps it bounded — no coarse-LOD path, no `coarse_n` table, no
  AI-15 badge. This is purely the threading refactor of one function.

---

## 7. AI-15 disclaimers

**N/A for this milestone.** e4 (split scope) adds no new variety, figure, or mathematical
object — it is a pure Qt-threading refactor of the existing render dispatch. No "real shadow" /
"birational" / "parametric cross-section" disclaimer is needed. (The AI-15 "Preview" badge that
the original combined-scope roadmap §6.3 mentions belongs to CAND-3 / e4b, which is explicitly
out of scope here.)

---

## 8. Open questions for the user

*None.* The milestone brief, the e3 spike report, the capability-scout rank-10 spec, and roadmap
§6.3 together fully specify the approach. The split-scope decision (CAND-4 only, CAND-3 → e4b) is
already made. Implementation proceeds on Windows; the macOS on-device checklist is a documented
pre-ship manual gate, not a blocker for this milestone's code.
