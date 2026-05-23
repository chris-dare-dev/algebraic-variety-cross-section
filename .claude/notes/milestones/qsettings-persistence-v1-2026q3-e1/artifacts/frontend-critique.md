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
