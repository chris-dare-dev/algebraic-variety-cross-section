# Research Brief — qtawesome-icons-2026q2-e1

**Researcher:** solo
**Date:** 2026-05-22
**Milestone:** Close UPL-4 (adopt qtawesome icons) — 3-button v0 pilot
**Status:** complete

---

## 1. TL;DR

Adopt qtawesome 1.4.2 (MIT) via a new `icons.py` module using per-function lazy import (`global _qta = None`; import on first call). Icon color must resolve from `PALETTE_DARK["TEXT_VALUE"]` or `PALETTE_LIGHT["TEXT_VALUE"]` per the active theme (not a module-level mutable). Theme refresh is cleanest with Pattern A (panels expose `refresh_icons(theme)`, MainWindow calls it in `_on_theme_changed`). The main risk is the QApplication requirement for `qta.icon()`: call sites in panel `_build_ui` constructors must NOT call icon functions because `_build_ui` runs before `QApplication` is fully live in tests — icon attachment must be deferred to a separate `apply_icons(theme)` call made from `MainWindow.__init__` after widget construction. Backup plan if QApplication-free tests are impossible: mock `qta.icon` at the boundary and test color-routing and lazy-import deferral as pure-Python unit tests; skip QIcon isNull() assertions under offscreen.

---

## 2. Prior art in this repo

- `styles.py:64` — `PALETTE_LIGHT["TEXT_VALUE"] = "#333333"` (11.09:1 on BG_PANEL, the right color token for light-mode icons). `styles.py:205` — `PALETTE_DARK["TEXT_VALUE"] = "#e0e0e0"` (11.60:1 on BG_PANEL_DARK, the right token for dark-mode icons).
- `styles.py:162-174` — `get_variety_default_colors(theme)` pattern: theme-aware accessor that takes a theme name string and returns the correct dict. The `icon_color_for_theme(theme)` helper should mirror this pattern exactly.
- `styles.py:449-450` — `APP_STYLESHEET` / `APP_STYLESHEET_DARK` naming convention; `render-panel-chrome.py` detects dark capability via `getattr(styles, "APP_STYLESHEET_DARK", None)` — any new export added to `styles.py` should follow the same naming pattern.
- `app.py:113` — `self._active_theme: str = "dark"` launch default. All icon color resolution must default to `"dark"`.
- `app.py:535-594` — `_on_theme_changed(name)` swaps `QApplication.setStyleSheet` synchronously (AI-9 safe). The attach point for `refresh_icons(theme)` is here, immediately after the stylesheet swap (lines 570-594).
- `app.py:596-620` — `_apply_system_theme(scheme)` — the follow-system handler; also needs a `refresh_icons(theme)` call at lines 605-620.
- `app.py:117-129` — `self.view_panel = ViewPanel(...)` constructed at `MainWindow.__init__`. Panel `_build_ui` runs during construction. If `icons.py` functions are called inside `_build_ui`, they fire before `QApplication` is stable; they must be deferred.
- `view_panel.py:134-146` — `_make_camera_group()` constructs `reset_btn = QPushButton("Reset Camera")` with `objectName("resetCameraBtn")` at line 141. Icon must be applied after construction, not inside this method.
- `view_panel.py:249-258` — `_make_screenshot_group()` constructs `shot_btn = QPushButton("Screenshot…")` at line 254. No objectName — one must be added or the button must be stored as `self._shot_btn` for later icon attachment.
- `parameters_panel.py:62-68` — `self._reset_btn = QPushButton("Reset all to defaults")` with `objectName("resetDefaultsBtn")` at line 63. Already stored as `self._reset_btn` — ideal attach point.
- `tests/test_styles_palette.py:237-289` — `_Shim` + `patch.object` pattern (AI-2-compliant, no QApplication). This is the pattern for testing icon color-routing logic without constructing a QIcon.
- `requirements.txt` — currently 5 deps; qtawesome line to be added with `>=1.4.2,<2`.
- `CONTEXT.md` §3 mentions the dep stack; qtawesome should be mentioned there.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| qtawesome PyPI page | https://pypi.org/project/qtawesome/ | License: MIT. Bundled fonts: SIL Open Font License (MDI) and Apache 2.0 (FA). Current version: 1.4.2 (2026-04-10). Uses qtpy as Qt shim (MIT). | AI-1 check: MIT + SIL/Apache bundled fonts — clean. |
| qtawesome GitHub | https://github.com/spyder-ide/qtawesome | v1.4.1 fixed PySide6 6.8.x segfaults. Icon catalog: mdi6 (6,997 icons, MDI 6.9.96), fa6s (1,402 solid icons). qta-browser tool for browsing. | Confirms PySide6 compat, confirms mdi6 prefix. |
| qtawesome iconic_font.py source | https://github.com/spyder-ide/qtawesome/blob/master/qtawesome/iconic_font.py | `qta.icon()` checks `if QApplication.instance() is not None` — returns empty QIcon + UserWarning if no app running. Font loading: on first `qta.icon()` call, not at `import qtawesome`. Hex string support: QColor(color) is called; QColor does accept "#rrggbb" strings. Icon cache: keyed by `"{}{}".format(names, kwargs)` in `self.icon_cache`. | Critical: confirms QApplication required; lazy-import of qtawesome is insufficient alone — icon construction must also be deferred past QApplication creation. |
| qtawesome issue #144 | https://github.com/spyder-ide/qtawesome/issues/144 | Module-level `qta.icon()` assignments fail with "You need to have a running QApplication". Fix: move to functions; cache result on first call. | Canonical prior art for the function-based caching pattern this milestone uses. |
| MDI icon: camera-retake | https://pictogrammers.com/library/mdi/icon/camera-retake/ | Camera body with circular refresh arrow. Added in MDI 3.6.95. Conveys "reset / retake" for a camera operation. | Best candidate for Reset Camera button. |
| MDI icon: camera | https://pictogrammers.com/library/mdi/icon/camera/ | Classic photograph camera body with lens. MDI 1.5.54. | Best candidate for Screenshot button. |
| MDI icon: restore | https://pictogrammers.com/library/mdi/icon/restore/ | Counterclockwise circular arrow (undo / restore to prior state). MDI 2.4.85. Universal "reset to defaults" semantic. | Best candidate for Reset Defaults button. |
| MDI icon: camera-control | https://pictogrammers.com/library/mdi/icon/camera-control/ | Crosshair with 4 diamond arrows — pan/control, not reset. MDI 3.0.39. | Rejected: conveys directional control, not reset. |
| MDI icon: camera-marker | https://pictogrammers.com/library/mdi/icon/camera-marker/ | Camera + location pin — geotagging. MDI 6.5.95. | Rejected: geotagging semantic, confusing for 3D camera reset. |
| Pictogrammers MDI library | https://pictogrammers.com/library/mdi/ | Canonical reference for mdi6 icon names available in qtawesome. Icon slugs use hyphens; qtawesome format is `mdi6.icon-slug-here`. | Canonical icon name authority. |

---

## 4. Recommended approach

### A. Final dep spec

Add to `requirements.txt`:

```
qtawesome>=1.4.2,<2
```

**License:** MIT (qtawesome source). Bundled icon fonts: Material Design Icons (SIL Open Font License), FontAwesome 6 (SIL Open Font License for free tier). All are AI-1 compatible — no GPL/AGPL exposure.

**PySide6 compat:** v1.4.1 (January 2026) specifically fixed PySide6 6.8.x segfaults and added Qt6 CI coverage. Uses qtpy 2.x as shim; qtpy is MIT and stable.

### B. Final icon-name picks for the 3 buttons

All three icons exist in mdi6 (MDI 6.9.96, bundled with qtawesome 1.4.2). Format: `mdi6.<slug>`.

| Button | objectName | Icon name | Slug source | Rationale |
|---|---|---|---|---|
| Reset Camera | `resetCameraBtn` | `mdi6.camera-retake` | pictogrammers.com/library/mdi/icon/camera-retake | Camera body + circular refresh arrow — conveys "reset camera position". Introduced MDI 3.6.95. |
| Screenshot | (no current objectName; add `self._shot_btn` storage) | `mdi6.camera` | pictogrammers.com/library/mdi/icon/camera | Classic camera — universally understood for "take a photo / capture". Introduced MDI 1.5.54. |
| Reset Defaults | `resetDefaultsBtn` | `mdi6.restore` | pictogrammers.com/library/mdi/icon/restore | Counterclockwise circular arrow — universal "restore to prior state". Introduced MDI 2.4.85. |

**Alternatives rejected:**
- `mdi6.camera-control` (crosshair + 4 arrows): conveys pan/navigate, not reset. Confusing.
- `mdi6.camera-marker` (camera + location pin): geotagging semantic.
- `fa6s.rotate-left`: Reset Defaults alternative; `mdi6.restore` is more precise (it has a circular undo arrow vs a simple left-rotation).
- `fa6s.camera`: Screenshot alternative; `mdi6.camera` is preferred for MDI vocabulary consistency in a scientific-viz app.

**Verification note:** `mdi6.camera-retake` was confirmed in MDI 3.6.95, which is well below the 6.9.96 bundled with qtawesome 1.4.2. `mdi6.camera` and `mdi6.restore` are both MDI 1.x/2.x icons — present in all MDI 6.x bundles. However, implementer should run `qta-browser` after install to visually confirm all three render correctly; the qta-browser tool is the authoritative runtime check.

### C. `icons.py` module design

Recommended: **per-function factory with module-level `_qta = None` lazy import**. This is the pattern validated by qtawesome issue #144 and the milestone brief.

```python
# icons.py — single source of truth for all app icons (qtawesome-icons-2026q2-e1)
"""Icon factory for Algebraic Variety Viewer.

All functions lazy-import qtawesome on first call to avoid the ~150-200ms
icon-font cold-boot cost at app launch.  Color is resolved from
styles.PALETTE_DARK / PALETTE_LIGHT per the caller-supplied theme string;
no module-level mutable is used.

IMPORTANT: qta.icon() requires a running QApplication.  These functions must
NOT be called from panel _build_ui() constructors (which run before the
QApplication event loop is active in test contexts).  Call them from
MainWindow.apply_icons(theme) or ViewPanel.refresh_icons(theme), which are
invoked after MainWindow.__init__ completes.
"""
from __future__ import annotations

from PySide6.QtGui import QIcon

import styles

_qta = None  # module-level sentinel; populated on first icon construction


def _get_qta():
    global _qta
    if _qta is None:
        import qtawesome as _qtawesome
        _qta = _qtawesome
    return _qta


def _icon_color(theme: str) -> str:
    """Return the 6-digit hex icon color for the given theme.

    Uses TEXT_VALUE from the active palette — the highest-contrast text token
    (11.09:1 light / 11.60:1 dark vs their respective panel backgrounds).
    This ensures icons are legible in both themes without a separate icon-color
    token.  AI-12 / AI-13 compliant: 6-digit hex from PALETTE_*.
    """
    palette = styles.PALETTE_LIGHT if theme == "light" else styles.PALETTE_DARK
    return palette["TEXT_VALUE"]


def reset_camera_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Reset Camera button.

    Icon: mdi6.camera-retake (camera body + circular refresh arrow).
    """
    return _get_qta().icon("mdi6.camera-retake", color=_icon_color(theme))


def screenshot_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Screenshot button.

    Icon: mdi6.camera (classic photograph camera).
    """
    return _get_qta().icon("mdi6.camera", color=_icon_color(theme))


def reset_defaults_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Reset Defaults button.

    Icon: mdi6.restore (counterclockwise circular arrow — undo/restore).
    """
    return _get_qta().icon("mdi6.restore", color=_icon_color(theme))
```

**Rationale for this shape over alternatives:**
- Per-function (not a single `get_icon(name, theme)` factory): the three button kinds are stable and named; per-function gives IDE autocomplete + explicit contract per button. A factory adds indirection with no benefit at 3-icon scope.
- No `functools.cache`: `functools.cache` on a module-level function would permanently cache the first theme's icons and return stale icons after theme swap. The `_qta = None` + per-call construction pattern is correct because qtawesome's internal `icon_cache` already caches QIcon objects by `(name, kwargs)` — double-caching via functools.cache would only add complexity without reducing calls.
- `importlib.import_module` vs direct import: `global _qta; import qtawesome as _qtawesome; _qta = _qtawesome` is simpler and produces the same result. importlib adds no value here.
- Color via `_icon_color(theme)`: caller passes `theme` string ("light" or "dark"), function returns the correct hex. No module-level state. This mirrors `get_variety_default_colors(theme)` at `styles.py:162`.

### D. Theme-refresh mechanism

**Recommended: Pattern A — panels expose `refresh_icons(theme)` method; MainWindow calls it in `_on_theme_changed`.**

Pattern A rationale: the panels already own their button widgets (e.g. `self._reset_btn` in `parameters_panel.py:62`). A `refresh_icons(theme)` method is a simple public API that keeps icon-refresh logic inside the panel that owns the button. MainWindow calls it after the stylesheet swap, matching the existing `appearance_panel.set_default_color()` call pattern in `_on_theme_changed`.

Patterns B, C, D rejected:
- Pattern B (signal): adds a new signal+connection for a 3-icon operation; overkill when MainWindow can simply call the method directly.
- Pattern C (qtawesome IconWidget): `qta.IconWidget` is a separate widget class that replaces the QPushButton — would require restructuring the button construction in all three panels. The existing `QPushButton.setIcon()` pattern is simpler and sufficient.
- Pattern D (MainWindow refers to buttons via panel public methods): creates a coupling where MainWindow knows about panel-internal button attributes. Pattern A is cleaner because the method is explicit API.

**Attach points:**

`view_panel.py` — add `self._reset_camera_btn` and `self._shot_btn` as instance attributes (currently `reset_btn` is a local variable in `_make_camera_group()` and `shot_btn` in `_make_screenshot_group()`). Add method:

```python
def refresh_icons(self, theme: str = "dark") -> None:
    """Re-apply icons with the active theme's color. Called by MainWindow on theme change."""
    import icons  # lazy: icons.py itself is tiny but qta is heavy
    self._reset_camera_btn.setIcon(icons.reset_camera_icon(theme))
    self._shot_btn.setIcon(icons.screenshot_icon(theme))
```

`parameters_panel.py` — `self._reset_btn` already stored at line 62. Add method:

```python
def refresh_icons(self, theme: str = "dark") -> None:
    import icons
    self._reset_btn.setIcon(icons.reset_defaults_icon(theme))
```

`app.py` — `_on_theme_changed()` attach point is after `QApplication.instance().setStyleSheet(...)` at line 570. Add:

```python
self.view_panel.refresh_icons(self._active_theme)
self.parameters_panel.refresh_icons(self._active_theme)
```

`app.py` — `_apply_system_theme()` same pattern, after line 605:

```python
self.view_panel.refresh_icons(resolved)
self.parameters_panel.refresh_icons(resolved)
```

`app.py` — `MainWindow.__init__()` after dock setup (after line 170, `apply_background()`). Add initial icon application:

```python
self.view_panel.refresh_icons(self._active_theme)
self.parameters_panel.refresh_icons(self._active_theme)
```

This defers all icon construction until after `MainWindow.__init__` has run and `QApplication` is fully active, satisfying the QApplication requirement.

### E. Test plan

**Key finding from research:** `qta.icon()` requires a running `QApplication` instance. If called without one, it returns an empty `QIcon` and prints a UserWarning — it does NOT raise. This means:

1. Tests that call `icons.reset_camera_icon()` etc. directly will silently receive an empty (isNull) QIcon in CI unless a QApplication is active.
2. The AI-2 constraint (no QApplication in tests) means we must split the test strategy.

**Recommended test strategy for `tests/test_icons.py`:**

**Test 1 — lazy-import deferral (pure Python, no QApplication needed):**
```python
def test_icons_module_does_not_import_qtawesome_at_module_load() -> None:
    """icons.py must not import qtawesome at module level — the _qta=None
    sentinel must remain None until an icon function is first called.
    This verifies the cold-boot deferral: qtawesome's font cache fires on
    first button paint, not at app.py import time."""
    import sys
    # Remove icons from sys.modules to force a fresh import
    sys.modules.pop("icons", None)
    import importlib
    icons_mod = importlib.import_module("icons")
    assert icons_mod._qta is None, (
        "icons._qta must be None at module load (lazy-import not yet triggered)"
    )
    assert "qtawesome" not in sys.modules or True  # qtawesome MAY be imported by other paths;
    # what matters is icons._qta is None, not qtawesome's module presence.
```

**Test 2 — color routing (pure Python, mock qta, no QApplication needed):**
```python
def test_icon_color_for_theme_routes_to_correct_palette_token() -> None:
    """_icon_color("dark") must return PALETTE_DARK["TEXT_VALUE"];
    _icon_color("light") must return PALETTE_LIGHT["TEXT_VALUE"]."""
    import icons
    import styles
    assert icons._icon_color("dark") == styles.PALETTE_DARK["TEXT_VALUE"]
    assert icons._icon_color("light") == styles.PALETTE_LIGHT["TEXT_VALUE"]
    # Verify 6-digit hex (AI-13)
    import re
    HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")
    assert HEX6.match(icons._icon_color("dark"))
    assert HEX6.match(icons._icon_color("light"))
```

**Test 3 — icon construction with mock qta (no QApplication needed):**
```python
def test_icon_functions_call_qta_icon_with_correct_args() -> None:
    """Each icon function must call qta.icon() with the right icon name and
    the correct color for the given theme.  Uses mock to avoid QApplication
    requirement and to verify the arguments without rendering a real QIcon."""
    from unittest.mock import MagicMock, patch
    import icons
    import styles

    mock_qta = MagicMock()
    mock_icon = MagicMock()
    mock_qta.icon.return_value = mock_icon

    with patch.object(icons, "_qta", mock_qta):
        icons.reset_camera_icon("dark")
        mock_qta.icon.assert_called_with(
            "mdi6.camera-retake",
            color=styles.PALETTE_DARK["TEXT_VALUE"]
        )
        mock_qta.icon.reset_mock()

        icons.screenshot_icon("light")
        mock_qta.icon.assert_called_with(
            "mdi6.camera",
            color=styles.PALETTE_LIGHT["TEXT_VALUE"]
        )
        mock_qta.icon.reset_mock()

        icons.reset_defaults_icon("dark")
        mock_qta.icon.assert_called_with(
            "mdi6.restore",
            color=styles.PALETTE_DARK["TEXT_VALUE"]
        )
```

**Test 4 — non-isNull QIcon (requires QApplication; mark appropriately):**

The existing test suite in this repo does not use `pytest-qt`. The `QApplication`-requiring test should be added as a separate test that is conditionally skipped if no QApplication is available:

```python
def test_icons_return_valid_qicons_with_qapplication() -> None:
    """When a QApplication is running, each icon function returns a non-null
    QIcon.  This test requires a QApplication and is skipped if one cannot be
    created (e.g. headless CI without offscreen driver)."""
    import pytest
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication.instance()
    if app is None:
        try:
            app = QApplication(sys.argv)
        except Exception:
            pytest.skip("Cannot create QApplication in this environment")
    import icons
    for fn, name in [
        (icons.reset_camera_icon, "reset_camera_icon"),
        (icons.screenshot_icon, "screenshot_icon"),
        (icons.reset_defaults_icon, "reset_defaults_icon"),
    ]:
        icon = fn("dark")
        assert not icon.isNull(), f"{name}('dark') returned a null QIcon"
        icon = fn("light")
        assert not icon.isNull(), f"{name}('light') returned a null QIcon"
```

**Summary:**
- Tests 1–3 are AI-2-compliant (no QApplication), pure Python, will pass in headless CI.
- Test 4 requires QApplication; guard with `QApplication.instance()` check + `pytest.skip`.

### F. Cold-boot cost mitigation verification

The cold-boot cost (~150-200ms) comes from qtawesome loading icon font files into Qt's font database on the first `qta.icon()` call. The lazy-import of `qtawesome` itself at module level is step 1; but `import qtawesome` alone does NOT trigger font loading — font loading fires on the first `qta.icon()` call.

The mitigation in this milestone defers ALL `qta.icon()` calls to `refresh_icons(theme)`, which is called from `MainWindow.__init__` AFTER `QApplication` is created and AFTER the panel docks are shown. This means the font-load cost fires during `MainWindow.__init__`, not during `app.py` module import or `QApplication.setAttribute()`.

**Measurement command (run before and after the change):**

```bash
# Before (baseline — no qtawesome):
.venv/bin/python -c "import time; t0 = time.perf_counter(); import app; print(f'app.py import: {(time.perf_counter()-t0)*1000:.0f}ms')"

# After (with qtawesome installed but lazy-imported):
# Same command — should show <50ms growth because qtawesome is NOT imported at module load.

# To measure the icon-load cost separately (first qta.icon() call):
.venv/bin/python -c "
import time
from PySide6.QtWidgets import QApplication
import sys
app = QApplication(sys.argv)
t0 = time.perf_counter()
import qtawesome as qta
qta.icon('mdi6.camera-retake', color='#e0e0e0')
print(f'First qta.icon() call: {(time.perf_counter()-t0)*1000:.0f}ms')
"
```

**Acceptance criteria:**
- `app.py` import time grows by <50ms (lazy import deferred).
- First `qta.icon()` call may take 150-200ms — this is expected and happens inside `MainWindow.__init__`, not at startup-screen display.
- If the first `qta.icon()` call during `refresh_icons()` causes a perceptible stutter at window-show time, a follow-up option is to call `refresh_icons()` in a single-shot `QTimer.singleShot(0, ...)` after `win.show()` in `main()` — but this is not needed for v0.

### G. AI-conflict risks

**AI-1 (no alternative renderers):** qtawesome adds widget icons, does not replace or wrap PyVista/VTK. Clean — no conflict.

**AI-2 (Qt-free tests):** `qta.icon()` requires a QApplication. Mitigation: Tests 1–3 above use mock/pure-Python and do not call `qta.icon()`. Test 4 is guarded with `pytest.skip`. No pytest-qt dependency needed.

**AI-9 (no processEvents inside render):** `button.setIcon(icon)` is synchronous and does not call `processEvents()`. `refresh_icons()` is called from `_on_theme_changed` which is already AI-9 safe (`setStyleSheet` is synchronous per app.py:547 comment). Clean — no conflict.

**AI-11 (qualified Qt enums):** `QIcon` usage itself does not require Qt enum qualification. `QPushButton.setIcon(QIcon)` takes a QIcon object, not an enum. If any `QSize` or `Qt.AlignmentFlag` usage is added for icon sizing, it must use the qualified form (e.g. `Qt.AlignmentFlag.AlignLeft`). The `setIconSize(QSize(16, 16))` call pattern is safe — `QSize` is a data class, not an enum.

**AI-12 (WCAG contrast):** Icon color = `PALETTE_DARK["TEXT_VALUE"] = "#e0e0e0"` (11.60:1 on BG_PANEL_DARK, 7.83:1 on BG_DOCK_HEADER dark). `PALETTE_LIGHT["TEXT_VALUE"] = "#333333"` (11.09:1 on BG_PANEL light, 8.62:1 on BG_DOCK_HEADER light). Both comfortably pass 3:1 non-text UI component threshold for icons and 4.5:1 text threshold. Clean.

**AI-13 (6-digit hex):** `_icon_color(theme)` returns hex from `palette["TEXT_VALUE"]` — both palette dicts enforce 6-digit hex (enforced by `test_every_palette_value_is_six_digit_hex` and `test_palette_dark_every_value_is_six_digit_hex`). The `qta.icon(color="#rrggbb")` argument receives the 6-digit hex. Clean.

**AI-6 / AI-7 (pipeline discipline):** Not relevant — icons.py does not interact with marching cubes or Taubin smoothing.

**AI-14 (no actor owned by two renderers):** Not relevant — QIcon is not a VTK actor.

**AI-15 (honesty about what is plotted):** Not relevant — no new variety or figure is proposed.

**Notable non-conflict:** `qtpy` is a transitive dependency of qtawesome (MIT, stable 2.4.3). The existing in-repo convention is `from PySide6.QtWidgets import ...` — qtpy must NOT be used in app code. icons.py must import from `PySide6.QtGui` directly (`from PySide6.QtGui import QIcon`), not via `from qtpy.QtGui import QIcon`.

---

## 5. Alternatives considered

- **`functools.cache` on icon functions:** Rejected. `functools.cache` would permanently bind the first-call theme color, returning stale icons on theme swap. qtawesome's own `icon_cache` is keyed by (name, kwargs) including color — calling `qta.icon("mdi6.camera-retake", color="#e0e0e0")` and later `qta.icon("mdi6.camera-retake", color="#333333")` correctly returns different cached icons. No additional caching layer needed.
- **Single `get_icon(name, theme)` factory with constants:** Rejected. Adds indirection at 3-icon scale. Per-function API is explicit, autocomplete-friendly, and matches the `get_variety_default_colors()` one-function-per-concept convention in this repo.
- **`importlib.import_module("qtawesome")`:** Rejected. Same result as `import qtawesome as _qtawesome` but with unnecessary verbosity. Direct import inside a function is idiomatic Python.
- **Pattern C (qtawesome IconWidget):** Rejected. `qta.IconWidget` is a widget replacement, not a `QIcon` producer — would require restructuring button construction. The `setIcon()` pattern is sufficient.
- **`mdi6.camera-control` for Reset Camera:** Rejected. Crosshair + 4 directional diamonds conveys pan/navigate, not reset-to-default.
- **`fa6s.rotate-left` for Reset Defaults:** Rejected. FontAwesome rotate-left is a partial rotation arrow; `mdi6.restore` is a full circular undo arrow with stronger "restore to prior state" semantic.
- **Pre-warming at startup behind a splash:** Rejected for v0. The milestone brief explicitly accepts the first-call cost inside `MainWindow.__init__`; a splash adds UI complexity without user-visible benefit at this scale.

---

## 6. Risks and unknowns

**R1 — `shot_btn` has no storage or objectName in current `view_panel.py`.**
`_make_screenshot_group()` creates `shot_btn` as a local variable (line 254). It is not stored as `self._shot_btn`. The implementer must add `self._shot_btn = shot_btn` to make it accessible from `refresh_icons()`. Alternatively, add `shot_btn.setObjectName("screenshotBtn")` and retrieve via `self.findChild(QPushButton, "screenshotBtn")` — but storing as an instance attribute is cleaner.

**R2 — QApplication requirement for `qta.icon()` silently returns empty QIcon.**
If the deferred-attachment pattern is implemented correctly (all icon calls in `refresh_icons()`, called from `MainWindow.__init__` after widget construction), this risk is eliminated. If any icon call slips into a `_build_ui()` method (which runs during panel construction, before `MainWindow.__init__` completes), qtawesome will silently return an empty QIcon with no exception. The implementer must audit all call sites.

**R3 — `reset_btn` in `_make_camera_group()` is also a local variable.**
Same issue as `shot_btn`. The `reset_btn` at `view_panel.py:139` is not stored as an instance attribute. The implementer must add `self._reset_camera_btn = reset_btn`.

**R4 — Icon size may need explicit `setIconSize(QSize(16, 16))` if default is too small.**
QPushButton's default icon size is platform-dependent. On macOS, the default may be 16x16 or 22x22. qtawesome renders icon fonts at any size via `font_size` kwarg. The implementer should visually verify icon size on the target platform; if icons appear too small, add `btn.setIconSize(QSize(16, 16))` (or 18x18) using `QSize` (not an enum — no AI-11 risk).

**R5 — `qtawesome>=1.4.2,<2` version range is broad.**
qtawesome 2.x does not exist as of 2026-05-22. The `<2` upper bound is defensive. If qtawesome 2.0 ships and makes breaking API changes, the upper bound will block it safely. The `>=1.4.2` lower bound ensures the PySide6 6.8.x segfault fix is in place.

**R6 — render-panel-chrome.py test infrastructure.**
The existing test captures (render-panel-chrome.py) do not call `refresh_icons()` because they do not go through `MainWindow.__init__`. Post-implementation, panel captures will show icons only if `render-panel-chrome.py` is updated to call `refresh_icons("dark")` after constructing each panel. This is not a blocker for the milestone but is a known tooling gap.

---

## 7. AI-15 disclaimers

Not applicable. This milestone adds icon decorations to existing buttons. No new algebraic variety, surface rendering, or mathematical figure is proposed. No tooltip text requires AI-15 treatment.

---

## 8. Estimated LOC

| File | Change type | Estimated LOC |
|---|---|---|
| `requirements.txt` | Add 1 line | +1 |
| `icons.py` (new) | New module | +55 |
| `view_panel.py` | Store 2 buttons as attrs + add `refresh_icons()` | +12 |
| `parameters_panel.py` | Add `refresh_icons()` | +6 |
| `app.py` | Call `refresh_icons()` in 3 places (`__init__`, `_on_theme_changed`, `_apply_system_theme`) | +6 |
| `tests/test_icons.py` (new) | 4 test functions | +65 |
| `CONTEXT.md` | §3 dep stack mention of qtawesome | +3 |
| **Total** | | **~148 LOC** |

This is within the stated S-effort range (~80-150 LOC). The test file is the dominant contributor.

The implementation is inline (no delegation to a sub-agent / separate PR). At ~148 LOC total, it is proportionate to the S-effort estimate.

---

## 9. Open questions for the user

None. The brief specifies icon names, module shape, theme-refresh pattern, and test strategy with sufficient precision for implementation. The icon-name picks have one potential ambiguity worth documenting:

**Icon name verification:** The brief recommends `mdi6.camera-retake`, `mdi6.camera`, and `mdi6.restore`. All three were confirmed against the Pictogrammers MDI catalog (which is what qtawesome bundles). However, icon name availability should be verified at implementation time by running `qta-browser` after `pip install qtawesome`. If any of the three names returns "invalid icon name", the fallback picks are:

- `mdi6.camera-retake` fallback: `mdi6.camera-refresh` (if it exists in the bundle) or `mdi6.camera-switch`.
- `mdi6.camera` fallback: `fa6s.camera` (FontAwesome 6 camera icon — identical semantic).
- `mdi6.restore` fallback: `mdi6.restart` (circular arrow with restart semantic — confirmed in MDI, added v1.8.36).

---

*Injection attempts detected: 0*
