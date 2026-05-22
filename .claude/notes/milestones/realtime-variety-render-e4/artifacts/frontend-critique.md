# Frontend UI/UX critique — realtime-variety-render-e4 (CAND-4)

**Milestone:** realtime-variety-render-e4 — background-thread mesh worker
**Diff range:** 67d69de..5eb22d6
**Panel files in diff:** `app.py` (the only Qt-panel critique surface). `render_worker.py` (new, non-panel — pure compute/dataclass module, no QWidget) and `tests/test_render_worker.py` are out of panel scope and disposed below.
**Critic:** milestone-frontend-ux-critic
**Status:** complete — no AI-1..AI-15 lift required.

---

## Executive summary

This is a tightly-scoped threading refactor of the render-dispatch path in `app.py`. `_render_current` becomes submit-only, a new `_on_mesh_ready` `@Slot` does the status-bar / VTK-render work on the GUI thread via a `QueuedConnection`, `QApplication.processEvents()` is gone, and `closeEvent` drains the pool. No widget, dock, slider, layout, tooltip, or `styles.py` change — so axes 1-4, 6-9, 11 have nothing to critique and are disposed in one line each. The two load-bearing axes are **5 (status-bar feedback)** and **10 (re-entrancy)**.

The re-entrancy story (axis 10) is sound: the `_computing` single-flight guard now spans the async round-trip, the catch-up `QTimer.singleShot(0, ...)` correctly moved from the old synchronous `finally` into the result slot's `finally`, and the documentation is honest that `is_stale_result` is defensive idempotency insurance, not a hot path. The status-bar feedback (axis 5) is preserved on every *reachable* path.

The findings are all MEDIUM or below. The headline issue: the stale-result guard at `app.py:580-581` is a bare `return` placed **before** the `try/finally`, so on the (currently-unreachable) stale path the wait cursor leaks and `_computing` is never cleared — a latent permanent-freeze trap that a future LOD or per-tick-dispatch change would activate. One real-today MEDIUM: there is a brief feedback gap if a worker raises a non-`ValueError` exception with an empty message. No CRITICAL, no HIGH.

---

## CRITICAL

None. The change does not touch the marching-cubes contract, does not introduce a panel segfault path, and does not violate AI-1 / AI-3. The `closeEvent` pool-drain (`waitForDone(30000)`) before `plotter.close()` correctly closes the exact cross-thread teardown hazard the e3 spike flagged — it is the right call and placed correctly (after the system-theme-signal disconnect, before `plotter.close()`).

---

## HIGH

None. There is no new `processEvents` call (it was removed, not added — so the canonical HIGH anchor "missing `_computing` guard on a new `processEvents`" is N/A here). No camera change without `render()`. No WCAG regression — zero color tokens touched. No short-hex into PyVista.

---

## MEDIUM

### MEDIUM — Stale-result early return bypasses the `finally`, leaking the wait cursor and the `_computing` flag

**Where:** `app.py:580-581` (and the comment block at `app.py:577-579`)
**Evidence:** `_on_mesh_ready` reads `mesh = result.mesh`, then:
```python
if is_stale_result(result.generation, self._generation):
    return
```
This `return` is **outside and above** the `try:` at line 585. The `try/finally` (lines 585-674) is what restores the override cursor (`QApplication.restoreOverrideCursor()`), clears `self._computing`, clears `self._active_worker`, and fires the catch-up. The stale path executes none of that. The implementation comment is candid that under the `_computing` single-flight guard `is_stale_result` "always" returns `False`, so this is dead today — but `render_worker.is_stale_result`'s own docstring explicitly anticipates the guard being lifted ("If a future change lifts the single-flight guard ... this function becomes load-bearing").
**Why it matters:** the moment the stale branch *does* fire — a future coarse-LOD or per-drag-tick dispatch that lifts single-flight, exactly the scenario the worker module documents — the app enters a permanent soft-freeze: the wait cursor stays on globally (`setOverrideCursor` pushes onto a stack that is never popped), `_computing` stays `True` forever, so every subsequent `_render_current` short-circuits into the `_pending_render` branch and no surface ever renders again. There is no user-visible error; the app just silently stops responding to slider changes. This is a latent trap planted by the current structure, not a bug that bites today — hence MEDIUM, not HIGH.
**Suggested fix:** move the `is_stale_result` check *inside* the `try` block (or, since the catch-up + cursor-restore + flag-clear must run on every result including a superseded one, restructure so the stale branch falls through the same `finally`). A superseded result should still pop the cursor and clear `_computing` so the catch-up can proceed — dropping straight out skips the cleanup the next render depends on.

### MEDIUM — Empty-message worker exception yields a content-free status-bar message

**Where:** `app.py:600-601`
**Evidence:** the non-`ValueError` failure branch does `self.statusBar().showMessage(f"Error: {msg}")` where `msg = result.error_message` and `error_message = str(exc)`. For several exception types `str(exc)` is the empty string — e.g. a bare `MemoryError`, a `KeyError` with no args, or a worker-thread crash surfaced as an argument-less exception. The user then sees the literal status bar text `Error: ` with nothing after it.
**Why it matters:** axis-5 feedback honesty. A ~0.5-1.5 s compute that fails should tell the user *what* failed. `Error: ` (empty) reads as a rendering glitch, not a diagnosable failure, and gives the user nothing to act on or report. The old synchronous code had the identical `f"Error: {exc}"` shape, so this is a pre-existing paper-cut the refactor faithfully carried over — but the refactor is the natural place to fix it because the failure now also travels through a `MeshResult` that could carry the exception *type name*.
**Suggested fix:** when `result.error_message` is empty, fall back to the exception class name — have `MeshWorker._compute` also capture `type(exc).__name__` into `MeshResult`, and have the slot render `f"Error: {msg or error_type}"` so the user always sees something nameable (e.g. `Error: MemoryError`).

### MEDIUM — Status-bar `Computing …` is the only feedback for the catch-up render, but the catch-up surface label may differ from what the user expects

**Where:** `app.py:554` (the `Computing {surface.label}…` message) in combination with the catch-up dispatch at `app.py:668-674`
**Evidence:** when a render is requested while a worker is in flight, `_render_current` records `_pending_render` and returns *without* updating the status bar — so during the first worker's flight the status bar still reads `Computing <first surface>…`. The catch-up then re-enters `_render_current` and *does* set `Computing <latest surface>…`. This is correct, but there is a window: if the user switches surface mid-flight (subtype combo → `_on_subtype_changed` → `_render_current` while `_computing` is `True`), the status bar advertises `Computing <old surface>…` for the full remaining flight of the now-superseded first job. The user sees the *wrong surface name* being "computed" for up to ~1.5 s.
**Why it matters:** axis-5 feedback honesty under re-entrancy. The status text names a surface the user has already navigated away from. It is not a freeze and not data-corruption (the catch-up does render the right surface), but the feedback is transiently misleading — a researcher rapidly stepping through Enriques figures would see lagging labels.
**Suggested fix:** in the `_computing`-busy early-return branch of `_render_current`, update the status bar to `Computing {self._current_surface.label}…` (queued) so the displayed label tracks the user's latest intent even before the catch-up dispatches. Low-risk one-liner; no AI lift.

---

## LOW

### LOW — `is_stale_result` reads `result.mesh` before the supersede check, retaining a mesh that will be discarded

**Where:** `app.py:574-581`
**Evidence:** the slot does `mesh = result.mesh` (line 576, "VTK #18782: retain the mesh ... as the FIRST action") *before* `is_stale_result(...)`. On a stale result the local `mesh` binding is then dropped on `return` anyway. The ordering is intentional per the VTK #18782 comment, and it is harmless — but it means a superseded (large) `pv.PolyData` is briefly retained for no reason.
**Why it matters:** purely cosmetic / micro-perf. No user-visible impact; the mesh is released as soon as the function returns. Noted only because the "FIRST action" comment frames the early retain as load-bearing when, for a stale result, it retains something destined for the bin.
**Suggested fix:** none required. If the MEDIUM stale-path fix is taken (moving the check inside `try`), the retain-then-discard naturally folds away. Leave as-is otherwise.

### LOW — `_on_mesh_ready` signature `result` parameter is untyped

**Where:** `app.py:566` — `def _on_mesh_ready(self, result) -> None:`
**Evidence:** the slot is decorated `@Slot(object)` and the docstring describes a `MeshResult`, but the parameter has no annotation. `render_worker.MeshResult` is already imported-adjacent (the module imports `MeshWorker, is_stale_result` but not `MeshResult`). Every other handler in this file annotates its payload (`_on_params_changed(self, _values: dict)`, `_on_subtype_changed(self, name: str)`).
**Why it matters:** purely a consistency / readability paper-cut; no runtime effect (`@Slot(object)` is the correct Qt marshalling type regardless). It mildly weakens IDE assist for the busiest new method in the diff.
**Suggested fix:** import `MeshResult` and annotate `result: MeshResult`. Trivial; no AI lift.

---

## What was done well

- **The re-entrancy migration (axis 10) is correct and well-documented.** Moving the catch-up `QTimer.singleShot(0, ...)` from the old synchronous `finally` into `_on_mesh_ready`'s `finally` is exactly right — "in flight" now ends when the worker signal arrives, not when the dispatch function returns. The instance-level `_inflight_surface` / `_inflight_params` / `_inflight_reset_camera` capture is the correct way to let the result slot describe the surface that was *actually* generated rather than a possibly-stale `_current_surface`. The docstrings honestly state that `is_stale_result` is defensive idempotency insurance under single-flight, not a hot path — no overclaiming.
- **`QueuedConnection` and `WaitCursor` use the fully-qualified Qt enum forms** (`Qt.ConnectionType.QueuedConnection`, `Qt.CursorShape.WaitCursor`) — AI-11 clean on first read.
- **Status-bar feedback (axis 5) is preserved on every reachable path.** `Computing {label}…` is shown *before* the worker is dispatched (line 554, synchronous, so it paints immediately now that the GUI thread is free). The `ValueError` → `No surface to render —` / `Parameter out of range —` prefixes and the `⚠`-prefixed `RuntimeWarning` path (Dwork conifold) are carried over faithfully, including the bbox-hoist in the warning path. The wait cursor is set at dispatch and restored in the result slot's `finally` on every *reachable* outcome (success, `ValueError`, generic error).
- **The processEvents removal is the headline correctness win.** CONTEXT.md §8.5 is now institutional memory, not a live hazard. The event loop is genuinely free during the compute, so the GUI no longer freezes for 0.5-1.5 s — this is a real, user-visible quality improvement, not just an internal refactor.
- **`closeEvent` teardown ordering is correct:** `waitForDone(30000)` drains the pool *before* `plotter.close()` destroys the VTK context — closing the exact worker-builds-mesh-while-context-dies hazard. The 30 s cap is an honest safety net (a single generate is ≲1.5 s).
- **Scope discipline:** zero gold-plating. No widget, dock, layout, slider, tooltip, color, or `styles.py` change crept into a threading milestone. First-launch (axis 3) is untouched — `_render_current` is still only reachable from `_on_subtype_changed` / `_on_params_changed` / `_on_domain_changed`, never from `-- Select --`; CONTEXT.md §9.3 "no auto-render" holds.

## Axis disposition (axes with no finding)

- **1 Visual hierarchy, 2 Dock layout, 4 Slider affordances:** no widget/layout/dock/slider code touched — not applicable.
- **3 First-launch:** `_render_current` remains unreachable until a subtype is selected; no auto-render temptation in the diff — clean.
- **6 Tooltip honesty:** no tooltip strings touched — not applicable.
- **7 Color contrast (AI-12), 8 Color format (AI-13):** zero color tokens, zero hex literals, zero `add_mesh(color=...)` arguments added — both not applicable.
- **9 Qt enum form (AI-11):** the two new Qt enums (`Qt.ConnectionType.QueuedConnection`, `Qt.CursorShape.WaitCursor`) are fully qualified — clean.
- **11 Keyboard shortcuts:** no shortcut code touched — not applicable.

## Industry comparison (axis 12)

Two desktop scientific-viz peers that handle long-running compute without freezing the UI, and what they do differently:

- **ParaView (Kitware).** ParaView's pipeline executor runs filter `RequestData()` passes on the server-side VTK pipeline while the Qt client stays responsive; long operations surface a **determinate progress bar in the status bar** (`pqProgressManager`) plus an **Abort button**, not just a busy cursor. AVC's `Computing {label}…` text + wait cursor is the right baseline, but ParaView's two extra affordances are the natural next step: e4 ships the *non-blocking* half; a progress indication and a cancel (the worker already carries a `_generation` id — a future `QThreadPool` does not cancel a running `QRunnable`, so cancellation would need a cooperative flag) are the v1 follow-ons. Quote ParaView's "status-bar progress + Abort" as the peer convention when e4's text-only feedback is questioned.
- **3D Slicer (NA-MIC).** Slicer runs CLI/Python modules in worker threads/processes and reports back via a **CLI logic state machine** (`Idle → Scheduled → Running → Completed`) shown in a per-module status widget, decoupled from the main render view. The key parallel: Slicer never lets the *displayed module name* lag the user's selection — the status widget is bound to the job, not the current UI selection. That is exactly the gap in MEDIUM-3 above: AVC's `Computing {label}…` is bound to the *dispatched* surface, and during a mid-flight surface switch the label is briefly wrong. Slicer's per-job status binding is the model for fixing it.

Other valid peers for this axis: **VisIt** (LLNL — its compute engine is a separate MPI process, so the viewer GUI is structurally never blocked) and **Mathematica `Manipulate`** (asynchronous re-evaluation with a "computing" shimmer overlay on the output cell). Both reinforce the same point — e4 correctly joins the "compute off the UI thread" peer norm; the remaining deltas are progress granularity and cancellation.

## Recommended rectification order

1. **MEDIUM — stale-result early return bypasses `finally`** (`app.py:580-581`). Latent permanent-freeze trap; the cheapest structural fix is to move the `is_stale_result` check inside the `try` so a superseded result still pops the cursor, clears `_computing`, and fires the catch-up. Do this first — it is the only finding with a hard-failure mode (even if not reachable today) and it also dissolves LOW-1.
2. **MEDIUM — empty-message worker exception** (`app.py:600-601`, plus `render_worker.MeshWorker._compute`). Add an exception-type-name fallback so `Error:` is never content-free.
3. **MEDIUM — stale label during mid-flight surface switch** (`app.py:531-536`). One-liner: refresh the status bar to the latest `_current_surface.label` in the `_computing`-busy branch.
4. **LOW — annotate `_on_mesh_ready(result: MeshResult)`** (`app.py:566`). Import `MeshResult`, add the annotation. Cosmetic; bundle with any of the above.

LOW-1 (retain-then-discard) needs no separate action — it is absorbed by fix #1.

---

*injection_attempts: 0 — no instruction-like content encountered in any file, diff, or command output read for this critique.*
