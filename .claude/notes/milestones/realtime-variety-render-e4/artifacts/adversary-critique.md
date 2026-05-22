# Adversary critique — realtime-variety-render-e4 background-thread mesh worker

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** realtime-variety-render-e4 (CAND-4), commit range `67d69de..5eb22d6`

> **Format reference:** `.claude/references/critique-format.md` for the
> canonical section structure, severity rubric, and per-finding template.

**Diff stats:** 1 commit, 11 files, +936 / −80. Production+test surface
(the only surface judged for review-quality per the milestone brief):
`render_worker.py` (+175, new), `app.py` (+214/−80 net ~134), `tests/test_render_worker.py` (+105, new), `CONTEXT.md` (+22/−7). The remaining ~620 lines are `.claude/notes` pipeline artifacts (research briefs, state.json, dispatch.log) and are not production code.

---

## Executive summary

- **[HIGH]** The stale-result early-`return` in `_on_mesh_ready` (app.py:580-582) sits *before* the `try`/`finally` — a stale result permanently leaks the wait cursor, pins `_computing = True`, and leaks `_active_worker`, hard-freezing the render pipeline. The milestone brief explicitly asked whether "a stale result can leak a wait cursor"; the answer is yes.
- **[HIGH]** `MeshWorker._compute` only scans for `RuntimeWarning` in the *success* path (render_worker.py:167-171); a generator that emits a `RuntimeWarning` and *then* raises is possible, but more importantly the success-path warning loop runs after `mesh = self._generate(...)` returns — fine — yet the `caught` list is never referenced on the error paths, so a warning emitted before a `ValueError` is silently dropped. Lower-impact but a real divergence from the pre-e4 contract.
- **[MEDIUM]** `is_stale_result` is exercised by 4 unit tests, but the production call site at app.py:580 can — per the worker's own docstring — never return `True` while the single-flight guard holds. The test suite proves the predicate; nothing proves the *slot's* behaviour when it does fire. Combined with the HIGH above this is an untested permanent-freeze path.
- **[MEDIUM]** `closeEvent` calls `QThreadPool.globalInstance().waitForDone(30000)` — the *global* pool. Any unrelated `QRunnable` (none today, but the pool is process-global) would extend the teardown wait; and if a worker genuinely hangs, the user waits 30 s on a close with no feedback.
- **[MEDIUM]** `_inflight_params` is the *same dict object* `parameters_panel.values()` returned, passed by reference into both `MeshWorker` and retained as `self._inflight_params`. If `parameters_panel.values()` ever returns a cached/mutated dict the worker reads it off-thread while the GUI thread mutates it. Today `values()` builds a fresh dict, so this is latent, not live — worth a defensive note.
- **[LOW]** `_pending_reset_camera` is overwritten by whichever `_render_current` call lands last while a worker is in flight; a `reset_camera=True` subtype-switch request queued behind a later `reset_camera=False` slider request loses its camera reset.
- **[LOW]** `MeshResult.error_message` / `warning_text` default to `""`; `_on_mesh_ready` does substring tests (`"No real zero set" in msg`) that are correct but undocumented as the contract between worker and slot — a docstring cross-reference would harden it.
- **What was done well:** the VTK #18782 mitigation is implemented exactly as the e3 spike §6 prescribed (worker `self._result` retain before emit, slot `mesh = result.mesh` as first statement); `processEvents()` is fully removed closing the §8.5 hazard; the AI-2 coverage gap is documented honestly and specifically in CONTEXT.md §9.

**Verdict: SHIP-WITH-FIXES.** The architecture is sound and the threading contract faithfully implements the e3 spike. One HIGH (the cursor/`_computing` freeze on the stale path) is a genuine hard-hang bug and must be fixed before ship; the second HIGH is a contract-fidelity gap. No CRITICALs — no segfault, no AI-1/AI-3 violation, no false math claim.

---

## Critical findings (must-fix before this can ship)

None.

---

## High findings (should-fix this iteration)

### HIGH — Stale-result early return bypasses the cursor/`_computing`/`_active_worker` cleanup

**Where:** `app.py:580-582` (the `is_stale_result` guard) vs. `app.py:585` (`try:`) and `app.py:658-674` (`finally:`)
**Evidence:** `_on_mesh_ready` does `if is_stale_result(result.generation, self._generation): return` at line 580-582, *before* the `try:` at line 585. The `finally` block that runs `QApplication.restoreOverrideCursor()`, `self._computing = False`, `self._active_worker = None`, and the catch-up scheduling is the `finally` of that `try`. A `return` at line 582 therefore exits the method without running any of it.
**Why it matters:** The milestone brief asks directly: "can a stale result leak a wait cursor?" — yes. If a stale result ever reaches the slot, the override wait cursor is never popped, `_computing` stays `True` forever (so `_render_current` thereafter only ever records `_pending_render` and returns — no worker is ever dispatched again), and `_active_worker` leaks. The app is permanently frozen with a spinning cursor. The worker's docstring (render_worker.py:56-60) concedes the single-flight guard makes this "defensive insurance, not a hot path" — but defensive code that fires into a permanent freeze is worse than no defensive code. AI-9 re-entrancy invariant in spirit: the guard state must always be released.
**Suggested fix:** Move the `setOverrideCursor`-pairing cleanup so it runs on *every* exit, or move the `is_stale_result` check inside the `try` (it would then hit the `finally`). Note that running the full `finally` on a stale result is itself correct — it should clear `_computing` and fire any pending catch-up; a stale result still means "the in-flight worker is done."
**Regression-guard test:** A Qt-free unit test cannot drive the slot, but `is_stale_result` plus a slot-state harness can: assert that after a simulated stale delivery the object's `_computing` is `False` and no override cursor remains. At minimum, add a CONTEXT.md §8 entry and an `is_stale_result` test asserting the *contract* ("a True return must still release the guard").

### HIGH — Worker drops a `RuntimeWarning` emitted on a generator that then raises

**Where:** `render_worker.py:153-171`
**Evidence:** `_compute` enters `with warnings.catch_warnings(record=True) as caught:` then `mesh = self._generate(...)`. On the `except ValueError` / `except Exception` branches (lines 156-165) it returns a `MeshResult` *without ever inspecting `caught`*. The `warning_text` extraction loop at lines 167-171 only runs on the success fall-through. The pre-e4 code (67d69de app.py) had the identical structure, so this is not a regression — but the e4 docstring (render_worker.py:149-152) claims the worker reproduces "the *entire* former synchronous render-compute body" and AI-14 says `MainWindow` surfaces RuntimeWarnings; a warning emitted just before a raise is silently lost.
**Why it matters:** AI-14 contract: generators may emit `RuntimeWarning` as a soft signal. `calabi_yau_dwork` warns at the conifold point; if a future generator warns and then determines the field is empty and raises `ValueError`, the user sees only "No surface to render" with no `⚠` context. Low probability today, but the worker docstring overstates fidelity.
**Suggested fix:** Either capture `warning_text` before constructing the error-path `MeshResult`s (move the `caught` scan above the `except` returns is impossible — restructure so the scan runs in a `finally`-like position), or honestly narrow the docstring claim to "the success-path warning capture." The cheap fix is the latter; the correct fix is the former.

---

## Medium findings (nice-to-fix)

### MEDIUM — The permanent-freeze stale path is entirely untested

**Where:** `tests/test_render_worker.py` (whole file) vs. `app.py:580`
**Evidence:** Four tests cover `is_stale_result` as a pure predicate (lines 34-53). None covers what `_on_mesh_ready` *does* with a `True` return — and per the HIGH above, what it does is freeze. The AI-2 Qt-free constraint genuinely blocks driving the live slot, but the *consequence* of a stale return (guard must still be released) is a pure-logic contract that a harness test could pin.
**Why it matters:** The milestone's headline risk is the async re-entrancy re-analysis. The one branch where the analysis is most fragile (stale discard) has zero coverage. Test count went 333→341 (+8) — all on the easy pure pieces.
**Suggested fix:** Add a contract test: a tiny stand-in object with `_computing`, `_active_worker`, `_pending_render` attributes plus the slot's cleanup extracted as a free function (mirroring how `is_stale_result` and `clipped_cache_is_valid` were extracted). Then the "stale result still releases the guard" rule is AI-2-testable.

### MEDIUM — `closeEvent` waits on the process-global QThreadPool with a 30 s cap

**Where:** `app.py:961`
**Evidence:** `QThreadPool.globalInstance().waitForDone(30000)`. The global pool is shared process-wide; the comment (app.py:958-960) calls 30 s "a safety net." If a `surface.generate()` genuinely wedges, the user clicks close and the window hangs for 30 s with no cursor change and no message.
**Why it matters:** A hung close is a poor UX and, on macOS, the OS may show a "not responding" spinner. The e3 spike §7 macOS checklist is the substitute gate but does not cover a wedged-worker close.
**Suggested fix:** Consider a dedicated `QThreadPool` member on `MainWindow` rather than the global instance (isolates the drain to *this app's* workers), and/or a shorter cap with a logged warning. At minimum document in CONTEXT.md §4.4 that close blocks up to 30 s on a stuck worker. Not ship-blocking — `surface.generate()` is CPU-bound and ≲1.5 s in practice.

### MEDIUM — `_inflight_params` aliases the dict handed to the worker

**Where:** `app.py:539` (`params = self.parameters_panel.values() ...`), `app.py:549` (`self._inflight_params = params`), `app.py:556` (`MeshWorker(surface.generate, params, ...)`)
**Evidence:** The same `params` dict object is (a) passed by reference into `MeshWorker`, (b) stored as `self._inflight_params`, and (c) read by the worker thread via `self._generate(**self._params)`. If `parameters_panel.values()` ever returns a shared/cached dict, the worker thread reads it while the GUI thread could mutate it — a data race.
**Why it matters:** Cross-thread mutation of a shared dict is undefined behaviour. Today `values()` constructs a fresh dict per call so this is latent, not live — but the e4 threading contract makes "what objects cross the thread boundary" load-bearing, and this aliasing is undocumented.
**Suggested fix:** Either copy at the boundary (`dict(params)` into the worker) or add a one-line invariant comment that `parameters_panel.values()` MUST return a fresh dict and a test asserting two calls return non-identical objects.

---

## Low findings (cosmetic / future iteration)

### LOW — `_pending_reset_camera` is last-writer-wins across queued requests

**Where:** `app.py:534-535`, `app.py:670-671`
**Evidence:** While a worker is in flight, every `_render_current` call overwrites `_pending_reset_camera`. A subtype switch (`reset_camera=True`) queued behind a later slider release (`reset_camera=False`) loses the camera reset.
**Why it matters:** Minor UX: after a subtype switch the camera should reframe; if a slider drag lands in the same in-flight window the catch-up renders without reframing. Rare and self-correcting on the next subtype switch.
**Suggested fix:** OR the pending reset flag (`self._pending_reset_camera = self._pending_reset_camera or reset_camera`) so a queued reset request is never silently downgraded.

### LOW — Worker↔slot string-contract is implicit

**Where:** `render_worker.py:82-86` (`error_is_value_error` doc) vs. `app.py:594` (`"No real zero set" in msg`)
**Evidence:** `_on_mesh_ready` branches on the substring `"No real zero set"` inside `error_message`. `MeshResult`'s docstring documents `error_is_value_error` but not that the slot further substring-matches the message text.
**Why it matters:** If the AI-14 ValueError message text in `surfaces.py` is ever reworded, the "No surface to render" vs "Parameter out of range" routing silently flips with no test catching it.
**Suggested fix:** Add a cross-reference comment in `MeshResult` noting the slot substring-matches, or (better) carry an explicit enum/flag for the empty-field case rather than re-deriving it from message text.

### LOW — `MeshWorker._compute` `Any` typing on params loses the ParamSpec contract

**Where:** `render_worker.py:36`, `render_worker.py:122`
**Evidence:** `params: dict[str, Any]`. Generator params are all `float` (ints coerced inside generators per AI-8). `dict[str, float]` would be the honest type.
**Why it matters:** Cosmetic — `Any` understates the AI-8 contract. No runtime impact.
**Suggested fix:** Narrow to `dict[str, float]` to match the `ParamSpec` numeric contract.

---

## What was done well

- **VTK #18782 mitigation implemented exactly as the e3 spike §6 prescribed.** `MeshWorker.run` sets `self._result = result.mesh` *before* `self.signals.finished.emit(result)` (render_worker.py:141-142), and `_on_mesh_ready` retains `mesh = result.mesh` as its literal first statement (app.py:576). Both halves of the documented mitigation are present and commented with the issue number.
- **`QApplication.processEvents()` removed entirely, closing the §8.5 re-entrancy hazard at the root.** The pre-e4 code needed the `_computing` guard *because of* `processEvents`; e4 removes the cause, not just the symptom. CONTEXT.md §8.5 is updated to mark it resolved while keeping it as institutional memory with an explicit "do not reintroduce" warning.
- **AI-2 coverage gap documented honestly and specifically.** CONTEXT.md §9 enumerates exactly which paths are untestable Qt-free (QThreadPool dispatch, QueuedConnection delivery, queue-latest coalescing, cancel-and-resubmit, closeEvent drain) and names the substitute gate (e3 spike script + spike §7 macOS checklist). This is not a hand-wave — it is a precise scope statement.
- **`is_stale_result` extracted as a Qt-free free function** mirroring the established `clipped_cache_is_valid` / `should_render_on_drag` pattern, so the supersede predicate gets real unit coverage under AI-2.
- **The job context is correctly snapshotted at dispatch.** `_inflight_surface` / `_inflight_params` / `_inflight_reset_camera` (app.py:548-550) are captured *before* `QThreadPool.start()`, and `_on_mesh_ready` uses those — not a fresh `_current_surface` / `parameters_panel.values()` — so the result slot describes the surface that was actually generated even if the user changed selection mid-flight. This directly addresses the brief's "`_current_surface` may be None or change between dispatch and the slot" concern.
- **The error-path branching faithfully reproduces the pre-e4 status-bar prefixes.** `error_is_value_error` lets `_on_mesh_ready` route to "No surface to render" / "Parameter out of range" / "Error:" exactly as the synchronous code did (compare app.py:586-601 to 67d69de app.py:528-545). The `MeshResult` dataclass cleanly separates the ValueError case (AI-14) from generic exceptions.
- **`catch_warnings` correctly relocated onto the worker thread** with an explicit comment (render_worker.py:151-152) that `catch_warnings` is not thread-shared and a main-thread context manager cannot see a worker-thread warning. CONTEXT.md §4.6 is updated to match.
- **`closeEvent` drains the pool before `plotter.close()`** (app.py:961-962) — the cross-thread teardown hazard the e3 spike flagged is addressed, and in the correct order (drain workers, *then* destroy the VTK context).
- **Worker captures every failure mode rather than letting exceptions propagate** off-thread (render_worker.py:113-117 docstring + 156-165) — an exception on a `QRunnable` cannot be caught by a main-thread `try`, and the code correctly recognizes this and ships failures inside the `MeshResult`.

---

## Frontend UI/UX findings

Merged from the `milestone-frontend-ux-critic` pass (app.py touched the
render-dispatch path). The frontend critic found 0 CRITICAL / 0 HIGH /
3 MEDIUM / 2 LOW. Its stale-result finding is the SAME issue as HIGH-1
above (the adversary critic graded it HIGH for the permanent-freeze
failure mode; the frontend critic graded it MEDIUM as dead-today) — the
rectifier should treat it as one fix. The remaining frontend findings are
new and additive.

### MEDIUM — Empty-message worker exception yields a content-free status-bar message

**Where:** `app.py:600-601`
**Evidence:** the non-`ValueError` failure branch does `showMessage(f"Error: {msg}")` where `msg = result.error_message = str(exc)`. For a bare `MemoryError`, an arg-less `KeyError`, etc., `str(exc)` is `""` — the user sees the literal text `Error: ` with nothing after it. The pre-e4 synchronous code had the identical `f"Error: {exc}"` shape, so this is a faithfully-carried-over paper-cut.
**Why it matters:** axis-5 feedback honesty. A ~0.5-1.5 s compute that fails should say *what* failed; `Error: ` reads as a render glitch, not a diagnosable failure. The refactor is the natural fix site — the failure now travels through a `MeshResult` that could also carry the exception type name.
**Suggested fix:** have `MeshWorker._compute` capture `type(exc).__name__` into `MeshResult` and have the slot render `f"Error: {msg or error_type}"` so the message is never content-free (e.g. `Error: MemoryError`).

### MEDIUM — Stale `Computing …` label during a mid-flight surface switch

**Where:** `app.py` `_render_current` `_computing`-busy early-return branch + the catch-up dispatch
**Evidence:** when a render is requested while a worker is in flight, `_render_current` records `_pending_render` and returns *without* updating the status bar — so the status bar keeps reading `Computing <first surface>…` for the full remaining flight even after the user switched subtype. The catch-up later corrects it, but for up to ~1.5 s the status text names a surface the user already navigated away from.
**Why it matters:** axis-5 feedback honesty under re-entrancy — a researcher rapidly stepping through Enriques figures sees lagging labels. Not a freeze, not data corruption (the catch-up renders the right surface), but transiently misleading.
**Suggested fix:** in the `_computing`-busy early-return branch, update the status bar to `Computing {self._current_surface.label}…` so the label tracks the user's latest intent before the catch-up dispatches. One-liner.

### LOW — `is_stale_result` reads `result.mesh` before the supersede check

**Where:** `app.py` `_on_mesh_ready` (the `mesh = result.mesh` retain before the `is_stale_result` check)
**Evidence:** the slot binds `mesh = result.mesh` ("VTK #18782: FIRST action") *before* the `is_stale_result` check; on a stale result that retain is immediately dropped on `return`. Intentional per the #18782 comment and harmless — noted only because the "FIRST action" framing implies load-bearing when, for a stale result, it briefly retains a mesh destined for the bin.
**Why it matters:** purely cosmetic / micro-perf; no user-visible impact.
**Suggested fix:** none required — folds away naturally if the HIGH-1 fix moves the `is_stale_result` check inside the `try`.

### LOW — `_on_mesh_ready` `result` parameter is untyped

**Where:** `app.py` `def _on_mesh_ready(self, result) -> None:`
**Evidence:** the slot is `@Slot(object)` and the docstring describes a `MeshResult`, but the parameter has no annotation — unlike every other handler in the file (`_on_params_changed(self, _values: dict)`, `_on_subtype_changed(self, name: str)`).
**Why it matters:** consistency / readability paper-cut; no runtime effect. Mildly weakens IDE assist on the busiest new method in the diff.
**Suggested fix:** import `MeshResult` and annotate `result: MeshResult`.

---

## Recommended rectification order

1. **Fix the HIGH cursor/`_computing` freeze (app.py:580).** Move the `is_stale_result` check inside the `try` (so a stale return still hits the `finally`), or hoist the cursor-restore / guard-clear / catch-up into an unconditional cleanup. This is the only ship-blocker. Pair it with a CONTEXT.md §8 entry — a permanent-freeze path on the new async architecture is exactly the kind of load-bearing bug §8 exists to record.
2. **Fix or honestly narrow the HIGH warning-drop (render_worker.py:153-171).** Cheap path: narrow the docstring to "success-path warning capture." Correct path: restructure so `caught` is scanned regardless of which branch fires.
3. **Batch the MEDIUMs.** The stale-path test (MEDIUM-1) is the natural companion to fixing HIGH-1 — extract the slot cleanup as a free function and test the contract. The `closeEvent` global-pool note (MEDIUM-2) and the `_inflight_params` aliasing note (MEDIUM-3) are independent one-to-three-line documentation/defensive changes.
4. **LOWs are optional follow-ups** — the `_pending_reset_camera` OR-fix is a one-liner worth taking; the typing and string-contract LOWs are at the maintainer's discretion.

---

*End of critique. Mandatory rectification: all HIGHs (no CRITICALs). Everything else is optional but recommended before milestone close.*

---

## Rectification status (filled in Phase 4)

- **Commit:** (rectification commit — see `git log`, subject `rect(realtime-variety-render-e4): ...`)
- **Fixed:** all 12 findings (2 HIGH, 5 MEDIUM, 5 LOW) closed.
  - **HIGH-1** — stale-result freeze: the `is_stale_result` check moved *inside* the `try` in `_on_mesh_ready`, so the `finally` cleanup (cursor restore, `_computing` clear, catch-up) runs on every path. CONTEXT.md §8.16 records the landmine. Verification: the live slot can't be tested Qt-free (AI-2) — confirmed by code inspection; the structural invariant ("worker-slot early returns sit inside the try") is documented in §8.16.
  - **HIGH-2** — dropped warning: `MeshWorker._compute` restructured so `warnings.catch_warnings` wraps the `try`/`except` and `caught` is scanned on every path. Regression test `test_compute_captures_warning_emitted_before_raise`.
  - **MEDIUM (untested stale path)** — structurally resolved by the HIGH-1 fix (the permanent-freeze path no longer exists); `is_stale_result` keeps its 4 unit tests; the live-slot gap stays documented in CONTEXT.md §9.
  - **MEDIUM (closeEvent global pool)** — `MainWindow` now owns a dedicated `_render_pool = QThreadPool()`; `closeEvent` drains it, not the process-global instance.
  - **MEDIUM (`_inflight_params` aliasing)** — the worker receives `dict(params)`, its own copy, making the thread boundary explicit.
  - **MEDIUM (empty-message exception)** — `MeshResult.error_type` added; `MeshWorker._compute` captures `type(exc).__name__`; the slot renders `f"Error: {msg or error_type}"`. Regression test `test_compute_captures_error_type_on_empty_message`.
  - **MEDIUM (stale `Computing …` label)** — the `_computing`-busy branch of `_render_current` now refreshes the status bar to the current surface label.
  - **LOW (`_pending_reset_camera` last-writer-wins)** — the busy branch ORs the flag (`_pending_reset_camera or reset_camera`).
  - **LOW (worker↔slot string contract)** — `MeshResult.error_is_value_error` docstring now cross-references the slot's `"No real zero set"` substring match.
  - **LOW (`Any` typing)** — `MeshWorker` params narrowed to `dict[str, float]`.
  - **LOW (mesh retain before stale check)** — folded away: `mesh = result.mesh` now runs *after* the supersede check.
  - **LOW (untyped `result` param)** — `_on_mesh_ready(self, result: MeshResult)` annotated; `MeshResult` imported.
- **Invalidated on re-verification:** none (both HIGHs confirmed present before fixing).
- **Deferred to next milestone:** none.
- **Test additions:** `tests/test_render_worker.py` — 6 new `MeshWorker._compute` tests (success, warning-on-success, warning-before-raise, ValueError payload, generic exception, empty-message error_type). Full suite green: 347 passed.
- **Manual-verification note (AI-2):** the live worker dispatch / `QueuedConnection` delivery / `closeEvent` drain cannot be exercised Qt-free. Off-screen `QCoreApplication` round-trip of the production `MeshWorker` (success / ValueError / RuntimeWarning paths) was re-run post-rectify and passed; the spike §7 macOS on-device checklist remains the pre-ship gate.
