# Implementation plan — appearance-panel-layout-pass-2026q3-e2

**Inline path. ~19 LOC across 3 files.** Close the deferred F-M2 (text-align cross-group fracture) and F-L2 (Display group header rename) from `display-toggles-checkable-button-2026q3-e1`. Researcher recommended Option 2 (new `colors-button` role + QSS rule) over Option 1 (global QPushButton text-align) and Option 3 (center-align display toggles).

1. **appearance_panel.py** —
   - `_build_color_group()`: after each of the two `QPushButton("Surface…")` / `QPushButton("Background…")` constructions, add `setProperty("role", "colors-button")`. Each button now picks up the new QSS rule.
   - `_build_toggles_group()`: rename `QGroupBox("Display")` → `QGroupBox("Render Mode")` per MeshLab peer convention (the exact term they use for wireframe/solid/edges toggle controls). Add an inline comment citing the F-L2 rationale and milestone id.
   ~5 LOC delta.

2. **styles.py:_render_stylesheet** — Add a new `QPushButton[role="colors-button"]` rule block after the existing global `QPushButton {}` rule. Inline comment explains: (a) F-M2 closure rationale, (b) why the rule must include box-model properties (padding + border-radius) to force `QStyleSheetStyle` on macOS so `text-align: left` is honored by the native painter, (c) why we don't extend `text-align` to the global `QPushButton` rule (would cascade to Reset Defaults / Reset Camera / view-preset buttons which are intentionally center-aligned). ~12 LOC delta.

3. **tests/test_styles_palette.py** — Two test additions:
   - Extend `test_dark_stylesheet_includes_role_selectors`: add `QPushButton[role="colors-button"]` to the required-selectors tuple so both `APP_STYLESHEET` and `APP_STYLESHEET_DARK` are guarded.
   - New `test_appearance_panel_colors_buttons_have_colors_button_role`: source-text grep (AI-2 compliant) asserting `src.count('setProperty("role", "colors-button")') >= 2` in `appearance_panel.py`.
   - New `test_appearance_panel_render_mode_group_header`: source-text grep asserting `QGroupBox("Render Mode")` exists in `appearance_panel.py` and `QGroupBox("Display")` does NOT.
   ~30 LOC delta.

4. **Verify** —
   - `pytest tests/ -q` reaches 368 + 3 = 371.
   - **Off-screen panel-chrome render verification**: re-run `.claude/scripts/frontend-uplift/render-panel-chrome.py /tmp/panel-chrome-after` and visually confirm:
     (a) "Surface…" / "Background…" text is now left-aligned (matching Wireframe / Show edges / HQ smoothing).
     (b) Group header reads "Render Mode" not "Display".
     (c) Reset Defaults / Reset Camera / view-preset buttons retain center-alignment (no regression — the role-property rule does NOT cascade to them).

5. **Commit** — `feat(appearance-panel-layout-pass-2026q3-e2): close F-M2 + F-L2 — text-align consistency across Colors and Display groups via colors-button role; rename Display group to Render Mode`.
