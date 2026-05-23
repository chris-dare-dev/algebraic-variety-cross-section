# Research Brief — qsettings-persistence-v1-2026q3-e1

**Researcher:** milestone-researcher (solo mode)
**Date:** 2026-05-23
**Output path:** `.claude/notes/milestones/qsettings-persistence-v1-2026q3-e1/research/agent-solo-brief.md`

---

## 1. TL;DR

Use `QCoreApplication.setOrganizationName("AVC") + setApplicationName("AlgebraicVarietyCrossSection")` in `main()` and `QSettings()` (no-arg form) at every call site — the global-singleton form is idiomatic Qt, avoids repeated string literals, and keeps key schema the canonical `Window/geometry`, `Window/state`, `LastSession/variety`, `LastSession/subtype`.  Main risk: the restore call must sit at the very end of `MainWindow.__init__` AFTER `_setup_shortcuts()` (the last call today) because `setCurrentText` on `variety_combo` fires `_on_variety_changed` which must find `subtype_combo` already constructed; if restore is inserted before dock or panel construction the `restoreState` returns silently but the dock geometry is then overridden by subsequent `addDockWidget` calls.  Backup plan: if the singleton form creates any platform registry issues, fall back to `QSettings("AVC", "AlgebraicVarietyCrossSection")` explicit constructor — behavior is identical, just verbose.

---

## 2. §9 Non-Goal Lift Confirmation

### Exact §9 text (CONTEXT.md:514)

```
- **No state persistence.** App doesn't save window layout, last-used surface, slider values,
  or color choices via `QSettings`. Every launch starts fresh.
```

This is a **pure deferral**, not a principled rejection. The sentence is a capability absence log ("doesn't save"), not a "we decided this is wrong" veto. Adjacent §9 entries confirm the pattern — the "Render-busy spinner icon — **shipped**" entry in §9 proves items in §9 are closeable deferrals, not permanent bans. The dark-mode §4.3b also explicitly names "Persisting the user's theme + dock layout is UPL-25's territory" (CONTEXT.md:156-158), confirming this was always intended as follow-on work.

### V1 scope rationale

The brief limits V1 to: geometry (size/position), dock layout (QMainWindow state), last variety, last subtype. The risks of lifting this specific slice are minimal:

- **Geometry/state:** `saveGeometry()` and `saveState()` are Qt builtins that handle multi-monitor edge cases and version-tag their own binary format — Qt silently ignores unknown binary blobs, so a stale save from an older build gracefully falls back to defaults.
- **Last variety/subtype:** read from `VARIETIES` registry at restore time — if the saved variety was later removed from the registry, the `if saved_variety in VARIETIES` guard makes it a no-op.

The explicitly deferred items (per-subtype slider values, colors, theme, camera pose, clip state) carry real second-order risks:
- **Slider values:** require per-subtype schema versioning — if a ParamSpec range changes between releases, a saved value outside the new range would either crash or silently render at the clamped default.
- **Colors:** a per-surface color saved in V1 would be re-applied on the next subtype switch, overriding the V2 theme-aware `set_default_color` reset logic (see UPL-25 comment at `app.py:509`).
- **Camera pose:** a pose saved at one window resolution would give a wrongly-angled view if the user resized the window.

**The user has authorized this lift** by invoking the milestone pipeline for `qsettings-persistence-v1-2026q3-e1`.

---

## 3. Codebase Audit

### 3.1 `MainWindow.__init__` construction order (app.py)

| Line | What happens | Persistence relevance |
|------|-------------|----------------------|
| 104 | `super().__init__()` | Must precede all Qt calls |
| 106 | `self.setWindowTitle(...)` | — |
| 107 | `self.resize(1200, 800)` | **Replaced by `restoreGeometry`** — call restoreGeometry AFTER this line and AFTER all addDockWidget calls |
| 119 | `self.variety_combo = QComboBox()` | variety_combo constructed here |
| 134 | `self.subtype_combo = QComboBox()` | subtype_combo constructed here |
| 151 | `self.setStatusBar(QStatusBar())` | Required before `restoreState` |
| 172–192 | `_render_busy_spinner` widget construction | Required before `restoreState` (it's added to statusBar) |
| 238 | `self._render_pool = QThreadPool()` | — |
| 252 | `self._set_subtype_enabled(False)` | Sets initial disabled state |
| 261 | `self._build_theme_menu()` | Adds menu bar (required before `restoreState` or state covers menu bar too) |
| 264–276 | ViewPanel + view_dock + `addDockWidget` (left) | **`restoreState` must follow ALL addDockWidget calls** |
| 279–300 | AppearancePanel + appearance_dock + `addDockWidget` (right) | Same |
| 302–322 | ParametersPanel + params_dock + `addDockWidget` (right) | Same |
| 324 | `splitDockWidget(params_dock, appearance_dock, ...)` | Same |
| 331 | `appearance_panel.apply_background()` | — |
| 343–354 | `refresh_icons(...)` + spinner icon | — |
| 356–357 | `_setup_shortcuts()` | **Last call in `__init__` today** |

**Insert point for restore**: after line 357 (`_setup_shortcuts()`), before the method returns. This is AFTER all `addDockWidget` calls, all panel constructions, all statusBar setup, all menu bar setup.

### 3.2 `closeEvent` (app.py:1189–1209)

Existing `closeEvent` at app.py:1189:
```python
def closeEvent(self, event):
    # dark-mode-2026q2-e1 rect L2: disconnect follow-system signal
    if self._system_theme_connection is not None:
        QGuiApplication.styleHints().colorSchemeChanged.disconnect(...)
        self._system_theme_connection = None
    # realtime-variety-render-e4: drain in-flight mesh workers
    self._render_pool.waitForDone(30000)
    self.plotter.close()
    super().closeEvent(event)
```

**New save call** must be inserted at the VERY START of `closeEvent` (app.py:1189), before the signal disconnect and BEFORE `waitForDone`. Rationale: `waitForDone` can block up to 30s; save should happen while the GUI is still live and before any teardown begins. Save order:
1. `self._save_settings()` ← NEW — atomically writes all keys
2. disconnect follow-system signal (existing)
3. `waitForDone(30000)` (existing)
4. `plotter.close()` (existing)
5. `super().closeEvent(event)` (existing)

### 3.3 `_on_variety_changed` (app.py:380–489)

Signal handler at app.py:380. The `setValue("LastSession/variety", name)` call should be added at app.py:392 (inside the `if name in VARIETIES:` branch), immediately after the `self._set_subtype_enabled(True)` call. **Do not** add it in the `else` branch (the `_PLACEHOLDER` case).

### 3.4 `_on_subtype_changed` (app.py:491–539)

Signal handler at app.py:491. The `setValue("LastSession/subtype", name)` call should be added at app.py:538, just before `self._render_current(reset_camera=True)` (but after `self.parameters_panel.set_specs(surface.params)`). Only add inside the `if variety in VARIETIES and name in VARIETIES[variety]:` block (line 493 guard).

### 3.5 `variety_combo` and `subtype_combo` confirmed

- `self.variety_combo` constructed at app.py:119 — confirmed `QComboBox`.
- `self.subtype_combo` constructed at app.py:134 — confirmed `QComboBox`.
- Both use `currentTextChanged.connect(...)` signal.

### 3.6 First-launch placeholder state (app.py:152)

`self.statusBar().showMessage("Choose a variety to begin.")` — confirms the app opens with no variety selected. On restore, if `saved_variety` is valid, `setCurrentText` fires `_on_variety_changed` which shows `f"Variety: {name}. Now choose a model."` — this immediately fires `_on_subtype_changed` if a saved subtype is in the list. The status bar message will therefore end up as the render-completion message after the first render, which is correct.

### 3.7 UPL-25 comment at app.py:509 and 1040

- app.py:509: `"# (UPL-25 dock state persistence is the future home for sticky overrides)"` — this is the color-override deferral comment; it refers to per-user color overrides persisting ACROSS variety switches. The V1 milestone does NOT address sticky color overrides, so this comment stays accurate and should not be removed.
- app.py:1040: `"Persisting the user's pick is UPL-25's territory (QSettings dock + theme state)."` — this should be UPDATED to note that geometry/dock/variety is shipped in V1; theme persistence is still V2/UPL-25.

### 3.8 No existing QSettings usage

Grep confirms: zero `QSettings`, `setOrganizationName`, `saveGeometry`, `restoreGeometry`, `saveState`, `restoreState` calls in the production code. Only `QCoreApplication` appears in test_debounce.py (as a lightweight Qt harness for the debounce timer tests, not for settings).

---

## 4. Recommended Approach

### 4.1 QSettings initialization — global singleton form in `main()`

Add to `main()` in app.py (before `QApplication(sys.argv)`):
```python
QApplication.setOrganizationName("AVC")
QApplication.setApplicationName("AlgebraicVarietyCrossSection")
```
Then at every call site use `QSettings()` (no-arg form). This is the canonical Qt idiom: the org/app name pair is set once globally in `main()` and every subsequent `QSettings()` constructor inherits them. Backing stores: INI file on Linux (`~/.config/AVC/AlgebraicVarietyCrossSection.ini`), plist on macOS (`~/Library/Preferences/AVC.AlgebraicVarietyCrossSection.plist`), registry on Windows (`HKCU\Software\AVC\AlgebraicVarietyCrossSection`).

Import required in app.py: `QSettings` from `PySide6.QtCore`.

### 4.2 Key schema

| Key | Qt type | Value |
|-----|---------|-------|
| `Window/geometry` | `QByteArray` | `self.saveGeometry()` |
| `Window/state` | `QByteArray` | `self.saveState()` |
| `Window/schema_version` | `int` | `1` (for future migration) |
| `LastSession/variety` | `str` | e.g. `"K3 surface"` |
| `LastSession/subtype` | `str` | e.g. `"Fermat quartic  [Fig. 1]"` |

**schema_version recommendation:** Add it now (cost: 1 LOC). When V2 adds per-subtype slider values, `_restore_settings()` can read `schema_version` and migrate/ignore V1-only saved state. Backward-compat: if `schema_version` key is absent, treat as V0 (pre-persistence) and skip all restore.

### 4.3 `_save_settings()` method

```python
def _save_settings(self) -> None:
    """Persist window geometry, dock layout, and last-used variety/subtype."""
    settings = QSettings()
    settings.setValue("Window/geometry", self.saveGeometry())
    settings.setValue("Window/state", self.saveState())
    settings.setValue("Window/schema_version", 1)
    # LastSession keys are written live in _on_variety_changed /
    # _on_subtype_changed; save() here is a safety flush.
    settings.sync()
```

### 4.4 `_restore_settings()` method

```python
def _restore_settings(self) -> None:
    """Restore window geometry, dock layout, and last-used variety/subtype."""
    settings = QSettings()
    schema = settings.value("Window/schema_version", 0, type=int)
    if schema < 1:
        return  # V0 / no saved state — graceful no-op

    geom = settings.value("Window/geometry", None)
    if geom is not None:
        self.restoreGeometry(geom)

    state = settings.value("Window/state", None)
    if state is not None:
        self.restoreState(state)

    saved_variety = settings.value("LastSession/variety", "", type=str)
    if saved_variety and saved_variety in VARIETIES:
        # setCurrentText fires _on_variety_changed which rebuilds subtype_combo
        self.variety_combo.setCurrentText(saved_variety)
        saved_subtype = settings.value("LastSession/subtype", "", type=str)
        if saved_subtype and saved_subtype in VARIETIES[saved_variety]:
            # setCurrentText fires _on_subtype_changed which triggers the
            # first render.  The _computing guard handles any re-entrancy.
            self.subtype_combo.setCurrentText(saved_subtype)
```

### 4.5 Write-back in `_on_variety_changed` (app.py:392 inside `if name in VARIETIES:`)

```python
QSettings().setValue("LastSession/variety", name)
```

### 4.6 Write-back in `_on_subtype_changed` (before `self._render_current(reset_camera=True)` at app.py:539)

```python
QSettings().setValue("LastSession/subtype", name)
```

Note: constructing `QSettings()` per-call is cheap (no file I/O at construction; Qt caches the backing store in-process).

### 4.7 `closeEvent` modification

Insert `self._save_settings()` as the FIRST line of `closeEvent` (app.py:1189), before the signal disconnect and before `waitForDone`.

### 4.8 Re-entrancy analysis (AI-9)

The `setCurrentText(saved_variety)` in `_restore_settings()` fires `_on_variety_changed`, which calls:
- `subtype_combo.blockSignals(True)` → rebuilds subtype list → `blockSignals(False)`
- `appearance_panel.set_default_color(...)` → pure attribute set, no render
- `appearance_panel.set_culling(...)` → pure attribute set, no render
- `appearance_panel.set_hq_smoothing_eligible(False)` → pure attribute set, no render
- `statusBar().showMessage(...)` → synchronous label update
- `QSettings().setValue("LastSession/variety", name)` ← the WRITE BACK

The write-back is a no-op (same value just restored), but it is safe: `QSettings.setValue` is synchronous, does not call `processEvents`, and does not emit signals that reach `_render_current`. No infinite loop.

The subsequent `setCurrentText(saved_subtype)` on `subtype_combo` fires `_on_subtype_changed` which calls `_render_current(reset_camera=True)`. This is the intended behavior — the restore triggers the first render of the saved surface. `_computing` is False at this point (no worker in flight). `_render_current` sets `_computing = True`, dispatches `MeshWorker` via `_render_pool.start(worker)`, and returns immediately. No re-entrancy.

The `QSettings().setValue("LastSession/subtype", name)` write-back in `_on_subtype_changed` is similarly a no-op safe write.

**No `processEvents` is introduced at any restore call site.** AI-9 green.

---

## 5. Decisions Matrix

| Decision | Options | Recommended | Justification |
|----------|---------|-------------|---------------|
| QSettings constructor form | `QSettings("AVC", "AlgebraicVarietyCrossSection")` per call vs `QApplication.setOrganizationName + QSettings()` global | **Global singleton (`main()` + no-arg calls)** | Qt canonical idiom; no string literal repetition; one authoritative place to change org/app name |
| Application name | `"algebraic-variety-cross-section"` (brief) vs `"AlgebraicVarietyCrossSection"` (CamelCase Qt) vs `"avc"` (short) | **`"AlgebraicVarietyCrossSection"`** | Qt conventions use CamelCase (e.g. all Qt Creator app templates); hyphens in plist filenames are legal but unusual; `"avc"` risks collision with other tools. macOS plist: `AVC.AlgebraicVarietyCrossSection.plist` — readable. Linux INI: `AlgebraicVarietyCrossSection.ini` under `~/.config/AVC/` — readable. |
| `schema_version` key | Add now vs wait for V2 | **Add now** | 1 LOC, zero runtime cost; enables V2 to detect and migrate V1-only state. Without it, V2 must either blindly clear settings or risk applying a V1 state blob to a V2 key schema. |
| Save timing | `closeEvent` only vs `closeEvent` + live write-back in `_on_variety_changed`/`_on_subtype_changed` | **Both** (as specified in the brief) | `closeEvent` saves geometry + state (which can only be read from the live window); live write-back ensures last variety/subtype is preserved even if the process is killed (SIGKILL, crash) before `closeEvent` fires. |
| Restore timing | End of `__init__` vs `showEvent` | **End of `__init__`** (after `_setup_shortcuts()`) | The Qt canonical recommendation (Python Qt tutorials, Qt Forum: "call read_settings() AFTER creating dock widgets but before `show()`"). `showEvent` fires after `show()` which can cause a geometry flash (default geometry briefly visible before the restore snaps it). `__init__` restore is the standard pattern. |

---

## 6. Test Plan

All tests are pure source-text greps (AI-2 compliant, no QApplication construction). Pattern: read `app.py` as text, `assert "<literal_string>" in _APP_SRC`.

**File name:** `tests/test_qsettings_persistence.py`

```
_APP_SRC = (pathlib.Path(__file__).parent.parent / "app.py").read_text(encoding="utf-8")
```

### Test 1 — `test_app_imports_qsettings`
```python
assert "from PySide6.QtCore import" in _APP_SRC
assert "QSettings" in _APP_SRC
```
Guards against QSettings being forgotten in the import list.

### Test 2 — `test_app_sets_org_and_app_name_in_main`
```python
assert 'QApplication.setOrganizationName("AVC")' in _APP_SRC
assert 'QApplication.setApplicationName("AlgebraicVarietyCrossSection")' in _APP_SRC
```
Locks the exact org/app name strings so a rename doesn't silently create a second settings store.

### Test 3 — `test_app_persists_window_geometry`
```python
assert "saveGeometry()" in _APP_SRC
assert "restoreGeometry(" in _APP_SRC
```
Guards the geometry save/restore call pair.

### Test 4 — `test_app_persists_window_state`
```python
assert "saveState()" in _APP_SRC
assert "restoreState(" in _APP_SRC
```
Guards the dock-layout save/restore call pair.

### Test 5 — `test_app_persists_last_session_variety_and_subtype`
```python
assert '"LastSession/variety"' in _APP_SRC
assert '"LastSession/subtype"' in _APP_SRC
```
Locks the exact key name strings.

### Test 6 — `test_app_settings_schema_version_key_present`
```python
assert '"Window/schema_version"' in _APP_SRC
```
Ensures forward-compat schema_version key is included.

### Test 7 — `test_app_save_called_in_close_event`
```python
close_event_pos = _APP_SRC.find("def closeEvent(")
save_pos = _APP_SRC.find("_save_settings()", close_event_pos)
assert close_event_pos != -1
assert save_pos != -1, "_save_settings() must be called in closeEvent"
```
Guards that save happens at close.

### Test 8 — `test_app_restore_is_guarded_against_first_launch`
```python
assert "in VARIETIES" in _APP_SRC  # guard on variety restore
# More specific guard for the schema_version check
assert "schema_version" in _APP_SRC
assert "if schema < 1" in _APP_SRC or "schema_version" in _APP_SRC
```
Guards that first-launch restore is a no-op (schema_version guard catches V0 state).

---

## 7. AI-1..AI-15 Conflict Scan

| Invariant | Status | Notes |
|-----------|--------|-------|
| AI-1 (PySide6 + PyVista stack) | GREEN | QSettings is PySide6/Qt — no renderer changes |
| AI-2 (Qt-free tests) | GREEN | All tests are source-text greps; `QSettings()` is never constructed in tests |
| AI-3 (no MainWindow under offscreen) | GREEN | No `MainWindow()` construction in tests |
| AI-4 (clip_scalar, not clip_box) | GREEN | No domain clipping changes |
| AI-5 (clip_scalar scalars= kwarg) | GREEN | Not touched |
| AI-6 (implicit vs parametric pipelines) | GREEN | No generator changes |
| AI-7 (Hanson normals) | GREEN | No mesh generation changes |
| AI-8 (VARIETIES registry contract) | GREEN | Registry read-only; `if name in VARIETIES` guard is the correct pattern |
| AI-9 (re-entrancy guard) | GREEN | `_restore_settings()` sits at end of `__init__`; `setCurrentText` fires `_on_variety_changed` → `_on_subtype_changed` → `_render_current`, all of which use the existing `_computing` guard. The live write-back calls in `_on_variety_changed` / `_on_subtype_changed` are synchronous, no processEvents, no re-entry. |
| AI-10 (raw mesh cache; domain clip doesn't regenerate) | GREEN | No changes to mesh caching or domain clip paths |
| AI-11 (fully-qualified Qt enums) | YELLOW | `QSettings` itself uses no Qt enums. New import line must follow existing fully-qualified enum import pattern. Verify no new `Qt.AlignLeft`-style shortcuts are introduced. |
| AI-12 (WCAG AA contrast) | GREEN | No new UI text or colors |
| AI-13 (6-digit hex only) | GREEN | No hex values added |
| AI-14 (generator contract: PolyData or ValueError) | GREEN | No generator changes |
| AI-15 (math claim honesty) | GREEN | No math-related changes; QSettings is pure UI plumbing |

**One close call: AI-9.** The restore path fires `_on_variety_changed` which writes back to QSettings (`setValue("LastSession/variety", name)`). This is a synchronous `QSettings.setValue()` — it does NOT call `processEvents`, does NOT emit a signal into `_render_current`, and does NOT recursively call `_on_variety_changed`. The write-back is safe.

---

## 8. CONTEXT.md Update Plan

### 8.1 §9 paragraph replacement

Replace (CONTEXT.md:514):
```
- **No state persistence.** App doesn't save window layout, last-used surface, slider values,
  or color choices via `QSettings`. Every launch starts fresh.
```

With:
```
- **State persistence — V1 shipped** (`qsettings-persistence-v1-2026q3-e1`, UPL-25 partial).
  Window geometry (size + position), dock layout (`QMainWindow.saveState`), and last-used
  variety + subtype are saved to `QSettings("AVC", "AlgebraicVarietyCrossSection")` on
  `closeEvent` and restored at the end of `MainWindow.__init__`.  Key schema:
  `Window/geometry`, `Window/state`, `Window/schema_version` (= 1), `LastSession/variety`,
  `LastSession/subtype`.  Backing store: INI on Linux, plist on macOS, registry on Windows.
  V2/V3 follow-ons (per-subtype slider values, theme preference, surface/bg colors, camera
  pose, clip state) remain explicitly out-of-scope.  Comment at `app.py:1040`
  ("UPL-25's territory — QSettings dock + theme state") updated to reflect geometry + variety
  shipped; theme + per-surface overrides remain V2.
```

### 8.2 New §4.5 (or §4.5 shift) — Session Persistence Architecture

Insert between the existing §4.5 (Domain clipping) and §4.6 (Warning surfacing):

```
### 4.5 Session persistence (qsettings-persistence-v1-2026q3-e1, UPL-25 partial)

`MainWindow` persists four categories of state on `closeEvent` via `QSettings`:

**Key schema (V1):**
| Key | Type | Description |
|-----|------|-------------|
| `Window/geometry` | `QByteArray` | `saveGeometry()` — position, size, multi-monitor |
| `Window/state` | `QByteArray` | `saveState()` — dock layout (floating, docked, sizes) |
| `Window/schema_version` | `int` | `1` — for future V2 migration |
| `LastSession/variety` | `str` | e.g. `"K3 surface"` |
| `LastSession/subtype` | `str` | e.g. `"Fermat quartic  [Fig. 1]"` |

**Save timing:**
- `closeEvent` (primary): calls `self._save_settings()` BEFORE the signal disconnect and
  thread-pool drain.  `_save_settings()` calls `settings.sync()` to flush.
- Live write-back (secondary): `_on_variety_changed` and `_on_subtype_changed` each call
  `QSettings().setValue(...)` when a valid variety/subtype is selected — preserves the last
  choice even on crash/SIGKILL before `closeEvent`.

**Restore timing:** end of `MainWindow.__init__`, AFTER all `addDockWidget` / `splitDockWidget` /
`setStatusBar` / menu-bar calls.  `restoreState` must follow every `addDockWidget` or the
dock geometry is overridden by the subsequent `addDockWidget` call.  `restoreGeometry` is
safe to call at any point after `super().__init__()`.

**First-launch (no saved state):** `schema_version` defaults to `0`; `_restore_settings()`
returns immediately with a no-op.  `restoreGeometry(None)` and `restoreState(None)` are
not called — the `if geom is not None:` guard prevents the Qt silent-false-return path.

**Backing store:** `~/.config/AVC/AlgebraicVarietyCrossSection.ini` (Linux),
`~/Library/Preferences/AVC.AlgebraicVarietyCrossSection.plist` (macOS),
`HKCU\Software\AVC\AlgebraicVarietyCrossSection` (Windows).  User-invisible; no migration
needed within V1.

**Out-of-scope (V2/V3):** per-subtype slider values, theme preference, surface/bg colors,
camera pose, clip state.  The `app.py:509` comment "(UPL-25 dock state persistence…)" refers
to per-user color overrides persisting across variety switches — this remains V2.
```

### 8.3 Update `_build_theme_menu` docstring comment at app.py:1040

Change:
```python
the next launch returns to dark.  Persisting the user's pick is
UPL-25's territory (QSettings dock + theme state).
```
To:
```python
the next launch returns to dark.  Persisting the user's theme choice
is V2/UPL-25 scope (qsettings-persistence-v1-2026q3-e1 ships geometry +
variety only; theme preference is explicitly out-of-scope for V1).
```

---

## 9. Estimated Diff Size + Inline vs Delegated

| File | Change type | Estimated LOC delta |
|------|-------------|---------------------|
| `app.py` | New imports (`QSettings` added to `PySide6.QtCore` import) | +1 |
| `app.py` | `main()`: 2 `setOrganizationName`/`setApplicationName` calls | +2 |
| `app.py` | `_save_settings()` method | +8 |
| `app.py` | `_restore_settings()` method | +18 |
| `app.py` | `closeEvent`: insert `self._save_settings()` + inline comment | +3 |
| `app.py` | `_on_variety_changed`: 1 `setValue` call + inline comment | +2 |
| `app.py` | `_on_subtype_changed`: 1 `setValue` call + inline comment | +2 |
| `app.py` | `_build_theme_menu` docstring update | +2, -2 |
| `tests/test_qsettings_persistence.py` | New test file (8 tests + boilerplate) | +80 |
| `CONTEXT.md` | §9 paragraph + new §4.5 | +40, -4 |

**Total: ~+158 LOC net** (app.py ~+38, tests ~+80, CONTEXT.md ~+40)

**Recommendation: inline (all in `app.py`, no separate settings module).** The total surface area is small (5 touch points in app.py). A separate `settings.py` module is premature abstraction for V1 scope — it would add an import and an indirection for 3 methods. If V2 adds per-subtype slider persistence (which requires a schema migration), extracting a `settings.py` at that point is justified.

---

## 10. References

| Location | Line | Claim |
|----------|------|-------|
| `CONTEXT.md` | 514 | Exact §9 "No state persistence" text |
| `CONTEXT.md` | 156–158 | "Persisting the user's theme + dock layout is UPL-25's territory" — confirms V0 deferral intent |
| `app.py` | 104–357 | `MainWindow.__init__` full construction order |
| `app.py` | 119 | `self.variety_combo = QComboBox()` construction |
| `app.py` | 134 | `self.subtype_combo = QComboBox()` construction |
| `app.py` | 151 | `self.setStatusBar(QStatusBar())` |
| `app.py` | 261 | `self._build_theme_menu()` — last menu-related setup before docks |
| `app.py` | 276 | `self.addDockWidget(... view_dock)` — first dock |
| `app.py` | 300 | `self.addDockWidget(... appearance_dock)` — second dock |
| `app.py` | 322 | `self.addDockWidget(... params_dock)` — third dock |
| `app.py` | 324 | `self.splitDockWidget(...)` — dock stacking |
| `app.py` | 356–357 | `self._setup_shortcuts()` — last call in `__init__` today; restore inserts after |
| `app.py` | 380 | `def _on_variety_changed(self, name: str)` — slot; `setValue` adds here |
| `app.py` | 392 | Inside `if name in VARIETIES:` — safe write-back location |
| `app.py` | 491 | `def _on_subtype_changed(self, name: str)` — slot; `setValue` adds here |
| `app.py` | 493 | `if variety not in VARIETIES or name not in VARIETIES[variety]: return` guard |
| `app.py` | 539 | Before `self._render_current(reset_camera=True)` — subtype write-back location |
| `app.py` | 509 | UPL-25 comment re: per-user color overrides (V2; stays) |
| `app.py` | 1040 | UPL-25 comment re: theme persistence (update to reflect V1 ships geometry) |
| `app.py` | 1189–1209 | Existing `closeEvent` — signal disconnect + `waitForDone(30000)` + `plotter.close()` |
| `app.py` | 1207 | `self._render_pool.waitForDone(30000)` — MUST be preceded by save |
| `app.py` | 1212–1236 | `main()` function — add `setOrganizationName`/`setApplicationName` before `QApplication(sys.argv)` |
| Qt Forum | https://forum.qt.io/topic/23867/solved-why-does-restoregeometry-return-false | `restoreGeometry(QByteArray())` returns False and does nothing — safe |
| pythonguis.com | https://www.pythonguis.com/tutorials/restore-window-geometry-pyqt/ | Call `restoreGeometry`/`restoreState` AFTER dock construction; `closeEvent` is the save point |
| Qt for Python docs | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QSettings.html | `QSettings()` no-arg form uses `QCoreApplication.organizationName()` + `applicationName()` |

---

## 11. AI-15 Disclaimers

Not applicable. This milestone introduces no new mathematical objects, no new variety figures, no new rendering of abstract mathematical spaces. Zero AI-15 surface.

---

## 12. Open Questions for the User

None. The milestone brief is fully specified. The only ambiguity was the application name string (`"algebraic-variety-cross-section"` vs `"AlgebraicVarietyCrossSection"`) — resolved in the decisions matrix above in favor of `"AlgebraicVarietyCrossSection"` per Qt convention, consistent with the note in the brief that acknowledges this choice.
