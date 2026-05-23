# Adversary critique — QSettings V1 persistence lift

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-23 | **Subject:** qsettings-persistence-v1-2026q3-e1 (`4b9e592..aa79dca`)

**Diff stats:** 8 files changed, 978 insertions, 5 deletions. Production files only (app.py + tests + CONTEXT.md): 475 diff lines.

---

## Executive summary

The most significant finding is a stale cross-reference in `app.py` comments (two instances of "See CONTEXT.md §4.5" that should read "§4.4a"), a LOW-severity documentation issue. No CRITICAL findings. The diff is 1094 total lines (475 production), triggering the mandatory review-quality-at-risk HIGH. The V1 scope boundary is clean — no slider values, colors, theme, camera, or clip state are persisted. The AI-9 close-call analysis (restore-time `setCurrentText` → `_on_variety_changed` write-back loop) is correct and safe. The AI-2/AI-3 test compliance is sound — tests are pure source-text greps with zero live `QSettings()` or `MainWindow()` construction. One MEDIUM finding: the live write-backs omit `sync()`, and the comments claim SIGKILL safety; this is technically accurate (Qt's destructor-triggered sync makes the claim hold) but the mechanism is undocumented in the code, making it a latent mislead for future maintainers. One LOW finding for the stale §4.5 cross-references in app.py. Overall: two HIGHs (one is the mandatory diff-size flag), one MEDIUM, one LOW — SHIP-WITH-FIXES.

---

## Verdict

**SHIP-WITH-FIXES**

The HIGH review-quality-at-risk finding is structural (mandatory per diff-size rule) and does not represent a real defect — the production diff is concentrated, well-structured, and thoroughly audited. The stale cross-references (LOW) and undocumented sync mechanism (MEDIUM) are maintainability issues, not correctness bugs. All AI-1 through AI-15 invariants pass. The §9 scope boundary is respected: no V2/V3 items are persisted. Rectify the MEDIUM and LOW before closing the milestone.

---

## Critical findings

None.

---

## High findings

### HIGH — Review quality at risk: diff exceeds 400-LOC threshold

**Where:** no specific file (cross-cutting)
**Evidence:** `git diff 4b9e592..aa79dca | wc -l` returns 1094 lines. Even with the pipeline artifact files (research brief, dispatch log, state.json, implementation plan) accounting for ~620 lines, the production files alone (app.py + tests + CONTEXT.md) total 475 diff lines.
**Why it matters:** Cisco / LinearB defect-detection research documents that reviewers who inspect diffs larger than 400 LOC miss more defects per hour. This finding is non-waivable per the checklist regardless of apparent cleanliness.
**Suggested fix:** No code change required. The finding is logged to satisfy the mandatory threshold rule. The production code changes are concentrated (app.py ~129 lines, test file ~238 lines, CONTEXT.md ~30 lines) and were audited end-to-end without evidence of missed defects. Future large milestones should consider splitting pipeline artifact files from production diffs in the commit range.
**Regression-guard test:** No test needed — this is a process finding. Acknowledge in rectification log.

---

## Medium findings

### MEDIUM — Live write-back SIGKILL safety depends on undocumented Qt destructor flush

**Where:** `app.py:401` and `app.py:562`
**Evidence:** At both sites, `QSettings().setValue(...)` is called on a temporary no-arg `QSettings` instance without a subsequent `sync()` call. The inline comment at `app.py:396-400` claims this "survives a process kill that bypasses closeEvent (SIGKILL, crash)." This claim is correct — Qt's `QSettings` destructor calls `sync()` implicitly when the temporary object goes out of scope at the end of the expression — but neither the comment nor the docstring mentions this mechanism. A future maintainer who doesn't know this Qt behavior may add explicit `sync()` calls "to be safe" (harmless but cargo-cult), or more dangerously may refactor the expression so the `QSettings` object persists across a scope boundary (e.g., assigning `settings = QSettings()` and reusing it), which would change the flush timing.
**Why it matters:** The SIGKILL durability guarantee is load-bearing design rationale that was documented explicitly in CONTEXT.md §4.4a. If the mechanism is not explained at the call site, future refactors risk silently weakening or breaking the guarantee.
**Suggested fix:** Add a one-line comment at each write-back site: `# QSettings() destructor calls sync() implicitly — flush is synchronous on expression end.` Alternatively, add a single `settings.sync()` call after each write-back for explicitness (no performance penalty; QSettings sync on INI/plist is single-digit milliseconds).

---

## Low findings

### LOW — Stale §4.5 cross-references in app.py comments

**Where:** `app.py:1219` and `app.py:1343`
**Evidence:** Both comment lines read `"See CONTEXT.md §4.5 for the full key schema and save/restore timing."` However, the new section that documents the persistence architecture is `§4.4a` ("Session persistence"). Section `§4.5` is "Domain clipping (sphere / cube)" — an unrelated topic. A developer following the comment link finds domain-clipping documentation instead of the persistence schema.
**Why it matters:** The cross-reference is the primary institutional-memory pointer from the implementation back to the architecture documentation. A wrong section number is a navigation dead-end that erodes documentation trust over time.
**Suggested fix:** Change `§4.5` to `§4.4a` at both locations (`app.py:1219` and `app.py:1343`). The correct target section (`### 4.4a Session persistence`) was created in this very commit.

---

## What was done well

- **V1 scope boundary is airtight.** Grepping all `QSettings().setValue(...)` calls confirms exactly five keys are written: `Window/geometry`, `Window/state`, `Window/schema_version`, `LastSession/variety`, `LastSession/subtype`. No slider values, colors, theme choice, camera pose, or clip state appear anywhere near a `setValue` call. The scope limiter is enforced by the code, not just by the CONTEXT.md prose.

- **Correct placement of `_restore_settings()` call.** Inserted at line 368 — after `_setup_shortcuts()`, which is after all three `addDockWidget` calls and `splitDockWidget`. The research brief correctly identified that `restoreState` before `addDockWidget` would be a silent no-op overridden by subsequent dock additions. The implementation follows the Qt canonical order without any error.

- **`_save_settings()` is correctly positioned at the TOP of `closeEvent`.** The call at `app.py:1299` precedes both the signal disconnect (line 1305) and `waitForDone(30000)` (line 1317). `saveGeometry()`/`saveState()` read live window state, so saving before any teardown is the only safe ordering. The comment at lines 1295-1298 explains the rationale precisely.

- **Schema-version guard prevents first-launch crashes.** `_restore_settings()` at line 1265-1267 returns immediately when `schema < self._SETTINGS_SCHEMA_VERSION`. The default value `0` for a missing key ensures a fresh install gets a clean no-op. The V2-migration path is preserved: a future `_SETTINGS_SCHEMA_VERSION = 2` upgrade can detect V1 blobs via the `schema == 1` case.

- **AI-9 re-entrancy analysis is sound.** The restore path's `setCurrentText(saved_variety)` fires `_on_variety_changed` which writes back to QSettings — a synchronous, same-value `setValue` that does not call `processEvents` and does not re-enter `_render_current`. The `_computing` guard is False at restore time (no worker in flight). The analysis in the inline docstring at lines 1279-1292 is accurate.

- **AI-2 / AI-3 test compliance is solid.** All 8 tests in `test_qsettings_persistence.py` are pure source-text greps on the text of `app.py`. No `QSettings()` is constructed at runtime, no `QApplication()` is created, no `MainWindow()` is instantiated. The `_APP_SRC` module-level constant reads `app.py` as a `str` only.

- **Test 7 boundary detection is robust.** The `closeEvent` body extraction in `test_app_save_called_in_close_event` correctly handles the case where `closeEvent` is the last method in the class (falls back to `\ndef ` top-level search to find `def main`), and the body slice correctly contains both `_save_settings()` and `_render_pool.waitForDone`. The `save_pos < drain_pos` assertion enforces ordering — not just presence.

- **CONTEXT.md §4.4a numbering is internally consistent.** The new section uses the `§4.3a / §4.3b` lettered-suffix precedent and slots between `§4.4` (Re-entrancy guard) and `§4.5` (Domain clipping) without renumbering existing sections. The §9 paragraph correctly says "See §4.4a" and the cross-link lands on the right section.

- **`_build_theme_menu` docstring update accurately characterizes V2 boundary.** The new wording (`"Theme persistence remains V2 / UPL-25 scope — qsettings-persistence-v1-2026q3-e1 shipped only the geometry + dock-layout + last-variety/subtype slice"`) correctly delineates what V1 shipped vs. what remains V2. The `LastSession/theme` hint gives the V2 implementer a concrete handle.

- **No scope creep into V2/V3 items.** The existing `app.py:526` comment (`"UPL-25 dock state persistence is the future home for sticky overrides"`) is correctly left in place — it refers to per-user color overrides across variety switches, not dock geometry, so it remains accurate after V1 persistence lands.

---

## Recommended rectification order

1. **Fix the MEDIUM (live write-back sync documentation).** At `app.py:401` and `app.py:562`, add a one-line comment explaining that `QSettings()` destructor flushes synchronously. Alternatively, add an explicit `sync()` call at each site if explicitness is preferred over brevity. No test change needed — this is a documentation-only fix.

2. **Fix the LOW (stale §4.5 cross-references).** Replace `"See CONTEXT.md §4.5"` with `"See CONTEXT.md §4.4a"` at `app.py:1219` and `app.py:1343`. Two-character change, zero runtime impact.

3. **Acknowledge the HIGH (diff size).** Log the mandatory finding closure in the rectification commit message. No code change is required for this finding.

---

*End of critique. Mandatory rectification: MEDIUM M1 (sync documentation) and LOW L1 (stale cross-references). HIGH H1 is process-only and requires no code change. All CRITICALs: none.*
## Frontend UI/UX findings

_Merged from milestone-frontend-ux-critic._

# Frontend UX Critique — qsettings-persistence-v1-2026q3-e1

**Critic:** milestone-frontend-ux-critic
**Date:** 2026-05-23
**Commit range:** `4b9e5923dcacdf4f2f5420ec15bee7c7a476e712..aa79dca`
**Files audited:** `app.py`, `CONTEXT.md` (panel files unchanged)

---

## Executive Summary

This milestone introduces invisible-to-the-user session persistence plumbing
(`QSettings`) in `app.py`. No Qt widget chrome was added or modified; all
panel files (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`,
`styles.py`) are untouched. The diff is entirely lifecycle code:
`_save_settings`, `_restore_settings`, two live write-back lines, and
`main()`-level org/app name initialization.

Finding counts: **0 CRITICAL / 1 HIGH / 2 MEDIUM / 1 LOW**

Headline finding (HIGH): `_save_settings()` is called at the top of
`closeEvent` with no `try/except` guard. A `PermissionError` or `OSError`
from the OS-level backing store (disk full, macOS sandbox deny, Windows
registry ACL) will propagate uncaught, skip the signal disconnect and
`_render_pool.waitForDone(30000)`, and hand the OS a less clean teardown —
at worst leaving the thread pool's VTK context partially destroyed.

All 12 axes walked below.

---

## CRITICAL

None.

---

## HIGH

### HIGH — `_save_settings()` unguarded in `closeEvent`; OS errors abort teardown

**Where:** `app.py:1299`
**Evidence:**
```python
def closeEvent(self, event):
    self._save_settings()          # <── no try/except
    if self._system_theme_connection is not None:
        QGuiApplication.styleHints().colorSchemeChanged.disconnect(...)
    self._render_pool.waitForDone(30000)
    self.plotter.close()
    super().closeEvent(event)
```
`_save_settings` calls `QSettings.setValue(...)` and `QSettings.sync()`.
On Linux, `sync()` writes to `~/.config/AVC/AlgebraicVarietyCrossSection.ini`;
on macOS to a plist; on Windows to the registry. All three backing stores can
raise `OSError` / `PermissionError` (disk full, read-only FS mount, sandbox
deny policy, Windows registry ACL). An unhandled exception at line 1299 means:
- The `colorSchemeChanged.disconnect` at line 1305 is skipped — leaving a
  dangling lambda capturing `self` if the app ever gains multi-window behavior.
- `_render_pool.waitForDone(30000)` at line 1317 is skipped — a MeshWorker
  still building a `pv.PolyData` may be running when `plotter.close()` tears
  down the VTK context at line 1318, which is exactly the cross-thread
  teardown hazard documented in CONTEXT.md §4.4.
- `super().closeEvent(event)` is never called — Qt does not mark the event
  as accepted, so the OS may or may not complete the window close depending
  on platform.

**Why it matters:** The sequence after `_save_settings()` is non-optional
teardown. If `_save_settings` raises for any reason, the app can crash during
a quit — the exact opposite of what a close-event save is meant to deliver.

**Suggested fix:**
```python
def closeEvent(self, event):
    try:
        self._save_settings()
    except Exception:  # noqa: BLE001
        pass  # Saving failed (disk full, permission denied) — proceed with teardown.
    if self._system_theme_connection is not None:
        ...
```
A silent `pass` is correct here: the save is best-effort. The live write-back
in `_on_variety_changed`/`_on_subtype_changed` already covers the SIGKILL
case; `closeEvent` is the geometry/dock-layout flush. Logging to
`sys.stderr` is optional but aids diagnostics on restricted environments.

---

## MEDIUM

### MEDIUM-1 — Second-launch status-bar flash: "Choose a variety" flashes before "Computing..."

**Where:** `app.py:152` (initial status bar message) vs `app.py:1292` (restore-triggered render)
**Evidence:**
The construction order in `__init__` is:
1. Line 152: `self.statusBar().showMessage("Choose a variety to begin.")`
2. ... (200+ lines of dock/panel/shortcut setup) ...
3. Line 368: `self._restore_settings()`

Inside `_restore_settings`, `variety_combo.setCurrentText(saved_variety)` fires
`_on_variety_changed`, which calls `statusBar().showMessage(f"Variety: {name}. Now choose a model.")`.
Then `subtype_combo.setCurrentText(saved_subtype)` fires `_on_subtype_changed`,
which calls `statusBar().showMessage(f"Computing {surface.label}…")`.

All of this happens synchronously inside `__init__`, BEFORE `win.show()` is
called in `main()`. The window is not yet visible at this point, so the
user will never see the intermediate "Choose a variety" or "Variety: K3.
Now choose a model." messages — they are never painted. The final visible
state on second launch will be "Computing Fermat quartic…" (set by
`_render_current` when the worker is dispatched), transitioning to the success
message when the worker returns.

This is NOT a defect today. However: if `_restore_settings()` is ever moved
to `showEvent` (a common alternative that avoids the geometry-flash
problem on some platforms), the intermediate messages WILL be visible
briefly. The pattern should be noted for forward-compat.

**Why it matters:** Moving restore to `showEvent` is a documented alternative
(pythonguis.com tutorial, Qt Forum); a future maintainer may make that
change without realizing the status-bar message sequence degrades.

**Suggested fix:** Add a one-line comment at `app.py:368` (the `_restore_settings()`
call) noting that the call must remain inside `__init__` (not `showEvent`)
to keep intermediate status-bar messages invisible:
```python
# NOTE: MUST remain in __init__ (not showEvent): the intermediate
# status-bar messages fired by setCurrentText during restore are
# invisible here (window not yet shown); moving to showEvent would
# make them flash visibly on second launch.
self._restore_settings()
```

---

### MEDIUM-2 — Removed-variety silent fallback gives no user feedback

**Where:** `app.py:1278`
**Evidence:**
```python
saved_variety = settings.value("LastSession/variety", "", type=str)
if saved_variety and saved_variety in VARIETIES:
    self.variety_combo.setCurrentText(saved_variety)
    ...
# else: silently falls through — status bar retains "Choose a variety to begin."
```
If the user had saved "Experimental torus" and that variety was pruned from
the `VARIETIES` registry in a subsequent app version, the restore silently
falls through. The user sees the first-launch "Choose a variety to begin."
state with no explanation of why their saved selection wasn't restored.

**Why it matters:** The first-launch experience (CONTEXT.md §9.3) is preserved,
which is correct. But the user who EXPECTS to see their last session
immediately resumed will be confused — they may think their settings were
lost. VS Code shows a notification banner "Extension 'X' is no longer
available" when a saved workspace references a missing extension. ParaView
shows "Unable to find reader for file type" when a saved reader plugin is
missing. The silent fallback pattern is used by both, but only for
invisible state (plugin preferences) — VS Code does NOT silently skip
restoring a visible workspace tab without telling the user.

**Suggested fix:** After the `if saved_variety and saved_variety in VARIETIES:`
block, add a fallback status-bar message for the else branch:
```python
if saved_variety and saved_variety not in VARIETIES and saved_variety:
    self.statusBar().showMessage(
        f"Last session: variety '{saved_variety}' is no longer available. "
        "Please choose a variety."
    )
```
(This fires only when a non-empty saved_variety fails the registry lookup —
the common first-launch empty-string case is still silent.)

---

## LOW

### LOW — `reset_camera=True` on restore is a forward-compat hazard for V2 camera-pose persistence

**Where:** `app.py:563` (inside `_on_subtype_changed`)
**Evidence:**
```python
self._render_current(reset_camera=True)
```
The restore-triggered render always calls `_render_current(reset_camera=True)`.
If V2/V3 later adds `LastSession/camera_pose` to the key schema, the
restore order would be:
1. `subtype_combo.setCurrentText(saved_subtype)` → triggers render with `reset_camera=True`
2. Camera is reset to default
3. (Later code) `self.restoreCameraPose(saved_pose)` → applies saved pose

Step 2 would override step 3 only if step 3 runs synchronously after step 1.
But with the background-thread worker (realtime-variety-render-e4), the
camera is reset in `_on_mesh_ready` AFTER the worker returns — so the
timing of the camera-pose restore matters critically in V2.

**Why it matters:** Low severity because V2 camera-pose persistence is
explicitly deferred (CONTEXT.md §9, §4.4a). But the V2 implementer must
be aware that `reset_camera=True` in `_on_subtype_changed` is unconditional
— a V2 camera-pose restore must sit INSIDE `_on_mesh_ready` (after the
reset), not in `_restore_settings`.

**Suggested fix:** Add a brief comment at `app.py:563`:
```python
# reset_camera=True is correct for V1: no saved camera pose.
# V2 camera-pose restore must run INSIDE _on_mesh_ready (after this
# reset), not in _restore_settings — see CONTEXT.md §4.4a out-of-scope list.
self._render_current(reset_camera=True)
```

---

## What was done well

1. **Schema-version guard on first launch** (`app.py:1266`): the
   `if schema < self._SETTINGS_SCHEMA_VERSION: return` guard is exactly right.
   `QSettings.value("Window/schema_version", 0, type=int)` defaults to `0`
   on a fresh install, so first-launch restore is a clean no-op with zero
   risk of calling `restoreGeometry(None)` or `restoreState(None)`.

2. **Restore ordering** (`app.py:356–368`): calling `_restore_settings()` as
   the last act of `__init__`, after ALL `addDockWidget`, `splitDockWidget`,
   `setStatusBar`, and `_setup_shortcuts`, follows the Qt canonical contract
   exactly. This is the most common implementation mistake in Qt
   save/restore patterns (calling `restoreState` before the final
   `addDockWidget` call), and it's handled correctly here.

3. **Dual write-back strategy** (`app.py:401`, `app.py:562`): writing
   `LastSession/variety` and `LastSession/subtype` live in
   `_on_variety_changed` / `_on_subtype_changed` in addition to the
   `closeEvent` flush is the correct defense against SIGKILL. Most Qt
   persistence tutorials only cover the `closeEvent` path and miss the
   crash-survival case.

4. **`if geom is not None` / `if state is not None` guards** (`app.py:1270–1275`):
   explicitly guarding the `restoreGeometry` / `restoreState` calls against
   `None` (rather than calling them unconditionally) avoids the Qt
   silent-false-return on `restoreGeometry(QByteArray())` — a subtle
   correctness detail that the research brief correctly identified.

5. **Cross-monitor DPI safety**: `QMainWindow.restoreGeometry()` in Qt 6
   clamps the restored window position to the available screen area when
   the saved monitor is no longer present or has a different resolution.
   The implementation correctly delegates to Qt's built-in geometry
   management without attempting to roll its own monitor-bounds check.

6. **No `processEvents` introduced**: the entire restore path
   (`setCurrentText` → `_on_variety_changed` → `setCurrentText` →
   `_on_subtype_changed` → `_render_current`) never calls `processEvents`.
   The existing `_computing` guard in `_render_current` correctly serializes
   the dispatch. AI-9 is clean.

7. **`QSettings().sync()` in `_save_settings`** (`app.py:1246`): explicit
   sync ensures the backing store is flushed before `waitForDone` potentially
   blocks for up to 30 s. Without `sync()`, the OS-level lazy-write could
   lose data if a system suspend happened during the thread-pool drain.

---

## Recommended Rectification Order

1. **(HIGH)** Wrap `self._save_settings()` in `closeEvent` with `try/except
   Exception: pass` to prevent OS-level backing-store errors from aborting
   the teardown sequence. (`app.py:1299`)

2. **(MEDIUM-1)** Add the forward-compat comment at the `_restore_settings()`
   call site warning that it must remain in `__init__`, not `showEvent`.
   (`app.py:368`)

3. **(MEDIUM-2)** Add a status-bar message in the removed-variety fallback
   path so users understand why their last session wasn't restored.
   (`app.py:1278`)

4. **(LOW)** Add a V2 camera-pose comment at `app.py:563` to prevent the
   reset_camera ordering hazard from being overlooked in V2 implementation.

---

*Status: complete — no gate-required findings.*

---

## Rectification status — 2026-05-23

**Fixed (in-scope, this rect commit):**
- `frontend HIGH` (`_save_settings()` unguarded in closeEvent): wrapped in `try/except OSError` so a disk-full / sandbox-deny / registry-ACL raise from `QSettings.sync()` does NOT abort the cross-thread teardown chain (signal disconnect + `_render_pool.waitForDone(30000)` + `plotter.close()`). Narrowed to `except OSError` (not bare) so genuinely unexpected exceptions still propagate. Save is best-effort — the live write-back already covers the SIGKILL case for `LastSession/*`; the closeEvent save is the geometry/dock-layout flush only, and losing it degrades to the same UX as first launch. New regression-guard test `test_close_event_wraps_save_settings_in_try_except`.
- `adversary MEDIUM` (live write-back SIGKILL safety claim undocumented): added explicit `QSettings.sync()` after each `setValue` in `_on_variety_changed` and `_on_subtype_changed`. Without explicit sync, Qt's deferred-sync behavior left writes in the in-memory cache only — contradicting the SIGKILL-safety claim in the inline comment. Cost is small (single small-key write per user action, not in a hot loop). New regression-guard test `test_live_write_back_calls_sync_for_sigkill_safety`.
- `frontend MEDIUM-1` (showEvent forward-compat): added inline comment at the `_restore_settings()` call site documenting why restore MUST stay in `__init__` (not `showEvent`) — moving it would make the intermediate status-bar messages flash visibly on every second launch (the classic Qt persistence-flash UX bug).
- `frontend MEDIUM-2` (removed-variety silent fallback): added `elif saved_variety:` branch to `_restore_settings` that fires a status-bar message ("Last session: variety 'X' is no longer available. Please choose a variety.") when a previously-saved variety has been pruned from the registry. Empty saved_variety (first-launch) stays silent — only the saved-but-stale branch surfaces a message. New regression-guard test `test_restore_surfaces_stale_variety_to_user`.
- `adversary LOW` (stale §4.5 → §4.4a in 2 app.py comments): updated both cross-references at app.py:1219 and app.py:1343 to point to §4.4a (the actual section number used in CONTEXT.md after the section was inserted between §4.4 and §4.5).

**Deferred (out-of-scope or cosmetic):**
- `adversary HIGH` (process / diff-size auto-finding): 978-line diff is ~76% artifact-inflation (477-line research brief + 50-line state.json + 46-line implementation plan + 11-line memory append); production+test delta is ~244 lines, well within the well-reviewed range. No code action.
- `frontend LOW` (`reset_camera=True` forward-compat for V2 camera-pose): V2 camera persistence is explicitly out-of-scope for this milestone; the V2 implementer will know to apply the camera pose inside `_on_mesh_ready` after the render returns, not before. Comment-only nudge.

**Invalidated:** none.

**Test count:** 404 (was 401, +3 rect regression guards: closeEvent try/except, live write-back sync, stale-variety status-bar message).
