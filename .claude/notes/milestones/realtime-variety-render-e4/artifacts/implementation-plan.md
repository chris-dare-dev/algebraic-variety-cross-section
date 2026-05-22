# Implementation plan — realtime-variety-render-e4 (CAND-4 background-thread worker)

Inline path. Split scope: CAND-4 worker ONLY (CAND-3 coarse-LOD → e4b).

1. **New `render_worker.py`.** `WorkerSignals(QObject)` (carries `finished =
   Signal(object)`), `MeshWorker(QRunnable)` (runs the whole former
   `_render_current` compute body off-thread: `warnings.catch_warnings`
   capture, `perf_counter` timing, `surface.generate()`, ValueError/Exception
   capture), a `MeshResult` dataclass payload, and the Qt-free
   `is_stale_result(result_gen, current_gen)` free function. VTK #18782:
   `MeshWorker.run()` sets `self._result = mesh` before emitting.

2. **Rewrite `app.py:_render_current`.** Becomes submit-only: keep the e1
   `_computing` / `_pending_render` queue-latest guard (one worker in flight,
   latest request queued); increment a new monotonic `self._generation`;
   capture `_inflight_surface` / `_inflight_params` / `_inflight_reset_camera`
   on the instance (so the slot uses the surface that was generated, not a
   since-changed `_current_surface`); push WaitCursor; `QThreadPool.start(worker)`;
   **remove the `QApplication.processEvents()` call**. No try/finally here.

3. **New slot `_on_mesh_ready(result)`** (`@Slot(object)`, QueuedConnection →
   runs on GUI thread). First line retains the mesh (VTK #18782). Defensive
   `is_stale_result` discard. Then the former post-generate body — error/warning
   branching, `_raw_mesh` assign, `_invalidate_clipped_mesh`,
   `_apply_domain_and_render`, status-bar build — all moved here. `finally`:
   restore cursor, clear `_computing` + `_active_worker`, fire the
   `_pending_render` catch-up `QTimer.singleShot(0, ...)`.

4. **`closeEvent`:** `QThreadPool.globalInstance().waitForDone(30000)` before
   `plotter.close()` so no worker touches `pv.PolyData` during VTK teardown.
   New imports: `QThreadPool, Slot`.

5. **Tests + docs.** New `tests/test_render_worker.py` — Qt-free unit tests for
   `is_stale_result` and the `MeshResult` dataclass (the live dispatch /
   QueuedConnection / cancel-resubmit cannot be tested without pytest-qt — AI-2).
   Update CONTEXT.md §4.4 (AI-9: `_computing` now spans the async round-trip;
   re-entrancy re-analysis) and §9 (worker-lifecycle test gap; point at the e3
   spike script + spike §7 macOS pre-ship checklist). Off-screen render
   verification of the worker compute path (AI-3, never MainWindow offscreen).

Constraints: AI-1 (PySide6+PyVista+pyvistaqt; no pin change), AI-2, AI-3,
AI-6 (Hanson untouched — worker dispatches uniformly, no coarse-LOD),
AI-9 (re-entrancy re-analysis). Predecessor e3 spike verdict: e4 cleared.
