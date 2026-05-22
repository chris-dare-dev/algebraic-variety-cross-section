# Implementation plan — display-toggles-checkable-button-2026q3-e1

**Inline path. ~85 LOC across 4 files.** Migrate Wireframe + Show-edges display toggles from `QCheckBox + setIcon()` (which produces the `[check-square][icon][label]` triple-prefix flagged as F-M2 in qtawesome-icons-2026q2-e2) to `QPushButton(checkable=True)` with the established QSS role-property pattern. Industry-aligned: Blender N-panel, 3D Slicer modules panel, ParaView all use checkable QPushButton (or plain text checkboxes) — never QCheckBox+icon.

1. **appearance_panel.py:_build_toggles_group** — Replace `self._wireframe_cb = QCheckBox("Wireframe")` and `self._edges_cb = QCheckBox("Show edges")` with `QPushButton("Wireframe")` / `QPushButton("Show edges")` instances. Each calls `setCheckable(True)`, `setChecked(self._wireframe/False)`, `setProperty("role", "display-toggle")` (the QSS hook), `setToolTip(...)` (preserved), and `.toggled.connect(self._on_*_toggled)` (signal name + signature identical via QAbstractButton). The variable names stay `_wireframe_cb` / `_edges_cb` to avoid churn in `refresh_icons` and `apply_to_actor`. Remove `QCheckBox` from imports if no other site uses it. ~20 LOC.

2. **styles.py** — Add `BG_TOGGLE_CHECKED` token to both `PALETTE_LIGHT` (`#d4e6f5`) and `PALETTE_DARK` (`#1a3048`). Append a `QPushButton[role="display-toggle"]` rule block to `_render_stylesheet` (after the Reset Camera button rules around line ~480) covering 4 states: unchecked (transparent), `:hover` (BG_CAMERA_BTN_HOVER fill + BORDER_CAMERA_BTN border, reused tokens), `:checked` (BG_TOGGLE_CHECKED fill + 2px FOCUS_RING border — the WCAG 1.4.11 indicator), `:checked:hover` (hover fill + 2px FOCUS_RING border). FOCUS_RING is already proven 3.56:1 light / 5.17:1 dark on BG_PANEL. ~25 LOC.

3. **tests/test_styles_palette.py** — 4 new tests:
   - `test_bg_toggle_checked_is_six_digit_hex` — AI-13 guard for the new token in both palettes.
   - `test_bg_toggle_checked_in_both_stylesheets` — asserts both `APP_STYLESHEET` and `APP_STYLESHEET_DARK` contain the new BG_TOGGLE_CHECKED hex (verifies template uses the token).
   - `test_display_toggle_role_selector_in_both_stylesheets` — asserts `QPushButton[role="display-toggle"]` appears in both stylesheets (parallels existing role-selector tests).
   - `test_appearance_panel_display_toggles_are_qpushbutton` — source-text grep guard (AI-2 compliant): no `QCheckBox("Wireframe")` / `QCheckBox("Show edges")` literals remain; `setCheckable(True)` and `setProperty("role", "display-toggle")` present in `appearance_panel.py`. Documents in the docstring why we use source-grep (QPushButton construction requires QApplication; AI-2 bans that).
   ~40 LOC.

4. **CONTEXT.md** — Add §8.15 "QCheckBox with icon creates a triple-prefix affordance — use QPushButton(checkable=True) for icon-bearing toggles" recording the migration pattern: rule (QPushButton+checkable for icon-bearing, plain QCheckBox for text-only), implementation steps (setCheckable + setProperty("role", "display-toggle") + .toggled signal), WCAG checked-state design (2px FOCUS_RING border carries the 3:1 obligation; BG_TOGGLE_CHECKED fill is decorative reinforcement). ~15 LOC.

5. **Verify** —
   - `pytest tests/ -q` stays at 333 + 4 = 337.
   - No off-screen render required (panel-chrome change, no VTK touch).
   - The capture-script `render-panel-chrome.py` already calls `appearance_panel.refresh_icons(theme_name)` after the e2 rect — captured Appearance PNGs will now show the new checkable QPushButton styling automatically when the script next runs.

6. **Commit** — `feat(display-toggles-checkable-button-2026q3-e1): migrate Wireframe + Show-edges to QPushButton(checkable=True) — close F-M2 from qtawesome-icons-e2`.
