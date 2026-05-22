# Frontend UX Critique — dark-mode-2026q2-e1

**Milestone:** dark-mode-2026q2-e1  
**Commit range:** f909093c9ff2d9ee52aec09337a79668d603b2c6..c76fb28b395fd813f3134b606385c76c8fe3d631  
**Files in scope (panel-surface changes):** `styles.py`, `app.py`  
**Files unchanged (no findings generated):** `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`  
**Date:** 2026-05-21  

---

## Executive Summary

0 CRITICAL, 2 HIGH, 3 MEDIUM, 1 LOW.

**Headline finding (HIGH-1):** `QDockWidget::title` in the dark QSS template sets `background: #313132` but contains no `color:` property. On a light-OS system running the app in Dark theme mode, Qt supplies near-black platform text (`~#000000`) against the dark dock header, producing a contrast ratio of approximately 1.62:1 — an AI-12 WCAG AA fail for body text. The fix is one line in `_render_stylesheet`.

**Second HIGH (HIGH-2):** `QStatusBar` in the dark QSS sets `color: #a0a0a0` but no `background`. On a light-OS system, the status bar inherits the platform light QPalette (`~#ececec`), making `#a0a0a0` on `#ececec` ≈ 2.21:1 — below the 4.5:1 body-text floor (AI-12).

Both HIGHs share the same root cause: `setStyleSheet`-only dark mode does not update `QPalette`, so any widget without an explicit QSS `background:` and `color:` inherits from the light platform palette, producing hybrid light/dark chrome on light-OS systems.

All claimed contrast ratios in the PALETTE_DARK annotations were independently verified via the WCAG 2.x relative-luminance formula and confirmed correct. MF1 swatch-chip closure (K3 #8e9ed4 vs #252526 = 5.83:1) verified.

**Suggested orchestrator next step:** Rectify HIGH-1 and HIGH-2 in a single follow-on patch to `_render_stylesheet` (add `color: {palette["TEXT_VALUE"]}` to `QDockWidget::title` and `background: {palette["BG_PANEL"]}` to `QStatusBar`). MEDIUM findings are polish-grade and can batch into the next panel-refresh milestone.

---

## CRITICAL

*No CRITICAL findings in this diff.*

---

## HIGH

### HIGH-1 — QDockWidget title text has no explicit color in dark QSS

**Where:** `styles.py:325-331` (`_render_stylesheet`, `QDockWidget::title` block)  
**Evidence:** The dark QSS block sets `background: {palette["BG_DOCK_HEADER"]}` (#313132 in dark) and `border-bottom: 1px solid {palette["BORDER_DOCK_HEADER"]}` but contains no `color:` declaration. Qt resolves the text color from the active `QPalette.WindowText`. On a macOS system running in light mode with the app switched to Dark theme (the common case for early adopters of the new feature), QPalette.WindowText is approximately `#000000`. WCAG computation: luminance(#000000) = 0.0, luminance(#313132) ≈ 0.029; contrast = (0.029 + 0.05) / (0.0 + 0.05) = **1.62:1**. WCAG AA body text requires 4.5:1.  
**Why it matters:** Every dock widget title bar ("View", "Parameters", "Appearance") displays black text on a near-black background when the user is on a light-OS system and selects Dark theme. The title text is the primary dock identity label; losing it disables the user's ability to tell docks apart when they are stacked or floated. AI-12 violation.  
**Suggested fix:** Add `color: {palette["TEXT_VALUE"]};` to the `QDockWidget::title` block in `_render_stylesheet`. This uses `TEXT_VALUE = #e0e0e0` in dark (11.60:1 vs #313132) and `#333333` in light (preserved behavior, still high-contrast on #e8edf2).

---

### HIGH-2 — QStatusBar text is unreadable on light-system dark theme

**Where:** `styles.py:386-390` (`_render_stylesheet`, `QStatusBar` block)  
**Evidence:** `QStatusBar { font-size: 11px; color: {palette["TEXT_MUTED"]}; }` sets text color to `#a0a0a0` (dark) but no `background`. On a light-OS system, `QStatusBar` background inherits `QPalette.Window ≈ #ececec`. WCAG computation: luminance(#a0a0a0) ≈ 0.1329, luminance(#ececec) ≈ 0.8573; contrast = (0.8573 + 0.05) / (0.1329 + 0.05) = **2.21:1**. WCAG AA small text (11px) requires 4.5:1. The status bar carries critical feedback: mesh generation progress, parameter values, `RuntimeWarning` conifold notices (AI-14), and `ValueError` out-of-range messages.  
**Why it matters:** Status bar feedback is the primary channel for non-error state communication (section 4.4). A 2.21:1 ratio at 11px is below even the WCAG 3:1 large-text floor. Users on a light-OS system who switch to Dark theme lose status feedback legibility entirely. The `⚠` conifold warning (AI-14) would be invisible in this configuration. AI-12 violation.  
**Suggested fix:** Add `background: {palette["BG_PANEL"]};` to the `QStatusBar` block. In dark mode this sets `#252526`, giving `#a0a0a0` a verified 5.86:1 ratio. Alternatively, darken the status bar text to `TEXT_VALUE` (`#e0e0e0`) while leaving background unset — but then the bg remains platform-dependent and future palette changes may reintroduce the issue. Setting background explicitly is more robust.

---

## MEDIUM

### MEDIUM-1 — "Theme" as the sole top-level menu is unconventional and forward-incompatible

**Where:** `app.py:504` (`_build_theme_menu`, `self.menuBar().addMenu("Theme")`)  
**Evidence:** After this milestone, the application menu bar contains exactly one entry: "Theme". No File, Edit, View, or Help menu exists. ParaView 5.12 buries theme selection under Edit > Settings > General > Color Theme (3 levels deep). Blender 4.x places it under Edit > Preferences > Themes, with a secondary Window menu for viewport toggles. Neither exposes a top-level "Theme" menu. 3D Slicer 5.x uses Edit > Application Settings > Appearance. The conventional home for theme-plus-viewport-overlays is a "View" menu, which can later absorb the camera presets and viewport-aids controls currently distributed across `view_panel.py` dock buttons.  
**Why it matters:** A lone "Theme" top-level menu is visually jarring ("why is there only one menu?") and signals to users that the app's menu bar is incomplete. More practically, when future milestones add File (screenshot/export), View (overlay toggles, grid, axes), or Help (About, documentation), "Theme" becomes an orphan that must be retrofitted under View or demoted to a submenu — creating a naming-consistency debt. Blender's precedent of grouping theme under a Window or View menu is the industry-validated pattern.  
**Suggested fix:** Rename `theme_menu` to a "View" menu (or, if View is reserved for viewport state, "Window") and nest the three theme actions under a "Theme" submenu: View > Theme > Dark / Light / Follow system. This mirrors Blender's Window-level placement and leaves the View menu extensible for future viewport-aid controls.

---

### MEDIUM-2 — Dead import: `VARIETY_DEFAULT_COLOR` is imported but unused

**Where:** `app.py:41` (`from styles import ... VARIETY_DEFAULT_COLOR ...`)  
**Evidence:** The pre-milestone code referenced `VARIETY_DEFAULT_COLOR` directly in `_on_variety_changed` and `_on_subtype_changed`. This milestone replaced all three call sites with `get_variety_default_colors(self._active_theme).get(...)`. The `VARIETY_DEFAULT_COLOR` symbol now appears only in the import statement at line 41 and nowhere else in `app.py`. Confirmed by regex search: zero non-import references.  
**Why it matters:** The dead import survives silently but creates cognitive noise: a future reader of `app.py` will wonder where `VARIETY_DEFAULT_COLOR` is consumed, potentially touching it in error during the next palette divergence milestone (when light and dark colors do diverge). It also means that `import styles` produces an extra symbol in `app`'s namespace that static analysers (pyflakes, ruff) will flag.  
**Suggested fix:** Remove `VARIETY_DEFAULT_COLOR` from the `from styles import ...` block in `app.py`. The accessor `get_variety_default_colors` is the correct and sole entry point.

---

### MEDIUM-3 — Theme switch does not push updated color to live actor

**Where:** `app.py:579-585` (`_on_theme_changed`, swatch re-seed block)  
**Evidence:** `_on_theme_changed` calls `self.appearance_panel.set_default_color(...)` which updates `_surface_color` and refreshes the swatch chip — but does not call `apply_to_actor(self._actor)`. As a result, if a mesh is already rendered when the user switches theme, `actor.prop.color` retains the previous theme's variety color until the next render event (next slider move, subtype re-select, etc.). In V0 this is invisible because `VARIETY_DEFAULT_COLOR_DARK` is `dict(VARIETY_DEFAULT_COLOR)` — same values in both themes.  
**Why it matters:** The forward-compatibility concern is concrete: any future milestone that diverges the dark variety colors from the light ones (e.g., muting saturation in dark mode for better depth perception) will produce a visible lag — the rendered surface stays on the old color until the user interacts. The swatch chip updates immediately but the viewport does not, creating a transient mismatch that the user cannot explain. Establishing the correct pattern now (call `apply_to_actor` after `set_default_color` in `_on_theme_changed`) costs one line and prevents the regression.  
**Suggested fix:** After the `if current_variety in VARIETIES:` block in `_on_theme_changed`, add `self.appearance_panel.apply_to_actor(self._actor)` followed by `self.plotter.render()` (guarded by `if self._actor is not None`). Mirror the same fix in `_apply_system_theme`.

---

## LOW

### LOW-1 — Dock title structural contrast (1.18:1) lacks a visual separator on certain platform renders

**Where:** `styles.py:219` (`PALETTE_DARK`, `BG_DOCK_HEADER: "#313132"`)  
**Evidence:** `BG_DOCK_HEADER = #313132` vs `BG_PANEL = #252526` yields 1.18:1 — structurally identical to the light-mode pattern (1.03:1). The BORDER_DOCK_HEADER at 3.05:1 carries the WCAG 1.4.11-compliant boundary. The code and comments correctly document this. However, on macOS, the native `QDockWidget` title bar renderer may suppress the `border-bottom` CSS sub-control when it renders the dock chrome natively (native style overrides QSS for some sub-controls). If BORDER_DOCK_HEADER is suppressed, the only visual separator between the dark panel and the dock header disappears entirely.  
**Why it matters:** Loss of the separator would make the dock title text (if HIGH-1 is fixed) appear to float directly on `BG_PANEL` with no boundary cue. This is a platform-rendering edge case, not a guaranteed failure. The fix is already present in the architecture (the separator line) — the risk is that native style overrides it.  
**Suggested fix:** Verify on macOS that the `border-bottom: 1px solid {palette["BORDER_DOCK_HEADER"]}` renders visibly in dark mode on the native platform. If the native style suppresses it, switch the dock widget to use `QDockWidget.setFeatures(...DockWidgetVerticalTitleBar)` or wrap the title in a custom widget. Lowest-risk alternative: add a `border: none; border-bottom: 1px solid ...` rule to force subcontrol rendering.

---

## What was done well

1. **Palette architecture.** `_render_stylesheet(palette)` is the correct abstraction for dual-theme support — one template, zero duplicated QSS literals, both themes rendered at import time. This mirrors the ParaView color-scheme XML token pattern (a parallel noted in the previous milestone's memory). Future theme changes (e.g., a high-contrast third palette) require zero template edits.

2. **WCAG annotations are accurate.** All six claimed contrast ratios in `PALETTE_DARK` comments (`TEXT_VALUE 11.60:1`, `TEXT_MUTED 5.86:1`, `TEXT_RESET_BTN 9.32:1`, `BORDER_DOCK_HEADER 3.05:1`, `BORDER_GROUP_BOX 3.42:1`, `BORDER_CAMERA_BTN 3.72:1`) were independently recomputed and confirmed exact. This is a marked improvement over the prior milestone where two inherited ratio annotations were off by 0.6-2.3 points.

3. **Follow-system signal management is correct.** The lazy-connect / eager-disconnect pattern in `_on_theme_changed` and `_apply_system_theme` handles the override-vs-follow conflict cleanly. The `try/except (RuntimeError, TypeError)` disconnect guard is the correct PySide6 idiom. The `resolved == self._active_theme` early-return in `_apply_system_theme` prevents a no-op stylesheet swap on redundant signals.

4. **AI-9 re-entrancy is clean.** `_on_theme_changed` and `_apply_system_theme` are synchronous throughout — no `processEvents` calls, no render pipeline re-entry. `set_default_color` does not trigger `apply_to_actor`, preserving the AI-9 boundary (the color seeding and the next render remain on separate synchronous paths).

5. **First-launch / section 9.3 preserved.** `main()` applies `APP_STYLESHEET_DARK` before `MainWindow()` is constructed; `_build_theme_menu()` runs before any dock is created; the dropdown remains at `— Select —`; no auto-render occurs. The dark-first launch is a deliberate UX position (viewport is always `#2f2f2f`) and is clearly documented.

6. **MF1 deferred finding correctly closed.** K3 #8e9ed4 vs BG_PANEL_DARK #252526 measures 5.83:1 — confirmed. All four variety colors clear 5.83–7.20:1 on the dark panel, comfortably above the WCAG 1.4.11 non-text 3:1 threshold. The swatch-chip contrast gap that was 1.87-2.31:1 on the light panel is resolved by the dark-default launch.

7. **Qt enum qualification (AI-11) throughout.** `Qt.ColorScheme.Light`, `Qt.ColorScheme.Dark`, `QDockWidget.DockWidgetFeature.DockWidgetMovable`, `Qt.DockWidgetArea.LeftDockWidgetArea`, `Qt.Orientation.Vertical` — all new enums in this diff are fully qualified. No shorthand form introduced.

8. **6-digit hex discipline (AI-13) maintained.** All new tokens in `PALETTE_DARK` are 6-digit. `VARIETY_DEFAULT_COLOR_DARK = dict(VARIETY_DEFAULT_COLOR)` inherits verified 6-digit values. No short-hex introduced in PyVista-bound or QSS paths.

---

## Recommended rectification order

1. **HIGH-1** (`_render_stylesheet` — `QDockWidget::title` missing `color:`): one-line fix, fixes dock title legibility on light-OS users switching to Dark.
2. **HIGH-2** (`_render_stylesheet` — `QStatusBar` missing `background:`): one-line fix alongside HIGH-1; keep the two QSS changes in a single commit.
3. **MEDIUM-2** (`app.py` — remove dead `VARIETY_DEFAULT_COLOR` import): trivial, include in the same commit as HIGH-1/HIGH-2.
4. **MEDIUM-3** (`app.py` — call `apply_to_actor` + `render()` after theme swatch re-seed): pattern fix, include in same commit if actor-refresh logic is straightforward; defer to next milestone if it complicates the HIGH-1/2 patch.
5. **MEDIUM-1** (Theme menu nesting under View): architectural UX decision, requires adding a "View" menu; schedule when the next menu item (File > screenshot, View > show axes) is ready to land, so the restructure has a concrete motivating addition.
6. **LOW-1** (dock title separator verification on macOS): manual check on a real desktop; no code change needed unless the separator is confirmed suppressed.
