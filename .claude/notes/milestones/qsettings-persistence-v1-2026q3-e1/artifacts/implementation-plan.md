# Implementation plan — qsettings-persistence-v1-2026q3-e1

**Inline path. ~158 LOC across 3 files.** Lifts CONTEXT.md §9 "No state persistence" for V1 scope only (geometry + dock layout + last variety+subtype). Per-subtype slider values, colors, theme, camera pose, clip state — all explicitly OUT-OF-SCOPE per the user-confirmed V1 tier.

**One load-bearing detail** from the researcher's AI-9 audit: the restore path's `setCurrentText(saved_variety)` fires the existing `_on_variety_changed` handler which writes back to QSettings (a no-op same-value write). The write-back is synchronous — no `processEvents`, no infinite loop, no AI-9 violation. Verified.

1. **app.py — `main()` (~line 1225)** —
   - Add `QApplication.setOrganizationName("AVC")` and `QApplication.setApplicationName("AlgebraicVarietyCrossSection")` immediately BEFORE `app = QApplication(sys.argv)`. Static methods, set on the class — no instance needed; subsequent `QSettings()` no-arg constructions inherit.
   - Add `QSettings` to the `PySide6.QtCore` import block.
   ~3 LOC delta.

2. **app.py — `_save_settings()` + `_restore_settings()` methods** —
   - `_save_settings()`: writes `Window/geometry` (`saveGeometry()`), `Window/state` (`saveState()`), `Window/schema_version=1`; calls `settings.sync()` to flush. ~8 LOC.
   - `_restore_settings()`: reads `Window/schema_version`; if `< 1`, returns no-op (graceful V0 fallback). Otherwise reads geometry, state, then `LastSession/variety` + `LastSession/subtype` with `if saved in VARIETIES` guards; calls `setCurrentText` on the combo boxes (which fires the existing handlers). ~18 LOC.
   ~26 LOC delta.

3. **app.py — call sites** —
   - End of `__init__` after `self._setup_shortcuts()` (line 358 area): add `self._restore_settings()` call.
   - `_on_variety_changed` (line 380) inside the `if name in VARIETIES:` branch: add `QSettings().setValue("LastSession/variety", name)` write-back.
   - `_on_subtype_changed` (line 491) inside the `if variety in VARIETIES and name in VARIETIES[variety]:` guard, before `_render_current(reset_camera=True)`: add `QSettings().setValue("LastSession/subtype", name)` write-back.
   - `closeEvent` (line 1189) FIRST line of method body: add `self._save_settings()` call BEFORE the signal disconnect and BEFORE `waitForDone(30000)`.
   - Comment at `app.py:1040` ("UPL-25's territory"): update to note V1 ships geometry/variety; theme remains V2.
   ~10 LOC delta.

4. **tests/test_qsettings_persistence.py (new)** — 8 pure source-grep tests per researcher §6:
   - `test_app_imports_qsettings`
   - `test_app_sets_org_and_app_name_in_main`
   - `test_app_persists_window_geometry`
   - `test_app_persists_window_state`
   - `test_app_persists_last_session_variety_and_subtype`
   - `test_app_settings_schema_version_key_present`
   - `test_app_save_called_in_close_event`
   - `test_app_restore_is_guarded_against_first_launch`
   ~80 LOC delta.

5. **CONTEXT.md** —
   - §9 paragraph replacement: "No state persistence" → "State persistence — V1 shipped" with key schema list + V2/V3 scope deferral note.
   - New §4.5 (or appropriate section) documenting persistence architecture (key schema, save/restore timing, backing-store paths per OS, first-launch behavior).
   ~40 LOC delta.

6. **Verify** —
   - `.venv/bin/pytest tests/ -q` reaches 393 + 8 = 401.
   - **No off-screen render verification needed** — pure persistence plumbing, no VTK changes.
   - Static `import app` smoke check to confirm `QSettings` import + `setOrganizationName` placement doesn't break startup.

7. **Commit** — `feat(qsettings-persistence-v1-2026q3-e1): persist window geometry + last variety/subtype across launches (CONTEXT.md §9 V1 lift)`.
