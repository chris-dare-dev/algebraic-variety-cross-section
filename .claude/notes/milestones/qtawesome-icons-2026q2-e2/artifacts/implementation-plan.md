# Implementation plan — qtawesome-icons-2026q2-e2

**Inline path. ~170 LOC across 6 files.** Extend qtawesome to 9 additional icons (7 camera presets + 2 display toggles). Spinner deferred to v2 per AI-9 risk analysis. Pattern-A architecture from e1 reused without modification.

1. **icons.py** — Add 9 new factory functions following the established e1 signature shape:
   - `preset_plus_x_icon(theme)` → `mdi6.axis-x-arrow` (rotated=0)
   - `preset_minus_x_icon(theme)` → `mdi6.axis-x-arrow` rotated=180
   - `preset_plus_y_icon(theme)` → `mdi6.axis-y-arrow` (rotated=0)
   - `preset_minus_y_icon(theme)` → `mdi6.axis-y-arrow` rotated=180
   - `preset_plus_z_icon(theme)` → `mdi6.axis-z-arrow` (rotated=0)
   - `preset_minus_z_icon(theme)` → `mdi6.axis-z-arrow` rotated=180
   - `preset_isometric_icon(theme)` → `mdi6.axis-arrow` (no rotation)
   - `wireframe_icon(theme)` → `mdi6.grid`
   - `show_edges_icon(theme)` → `mdi6.border-outside`
   All use `_icon_color(theme)` (TEXT_VALUE — same as Reset Camera / Screenshot). Module-level constants `WIREFRAME_ICON_NAME` and `SHOW_EDGES_ICON_NAME` so Test D (distinctness) can verify them without docstring scraping. Update module-level `Icons` docstring section to enumerate v1 additions. ~70 LOC.

2. **view_panel.py** — Promote loop-locals to stored dict:
   - Initialize `self._preset_btns: dict[str, QPushButton] = {}` and `self._iso_btn: QPushButton | None = None` in `__init__` before `_build_ui()`.
   - In `_make_view_presets_group()`, store each created button as `self._preset_btns[label] = btn`; promote `iso_btn` → `self._iso_btn`.
   - Extend `refresh_icons(theme)` to set icons on all 7 promoted attrs (preserve existing v0 Reset Camera + Screenshot calls — regression-guarded by Test A). ~22 LOC.

3. **appearance_panel.py** — Add a new `refresh_icons(theme)` method (no existing one — `self._wireframe_cb` and `self._edges_cb` already stored as instance attrs by `_build_toggles_group`, so no promotion needed). Method calls `icons.wireframe_icon(theme)` and `icons.show_edges_icon(theme)` with `setIconSize(QSize(16, 16))` matching the view_panel convention. ~12 LOC.

4. **app.py** — Add `self.appearance_panel.refresh_icons(theme)` to all 3 attach points (init, `_on_theme_changed`, `_apply_system_theme`) right after the existing `view_panel.refresh_icons` calls. ~3 LOC.

5. **tests/test_icons.py** — 4 new tests + extend Test E (QApplication smoke):
   - **Test A** (`test_v0_icons_still_bind_correctly`): regression guard verifying the 3 v0 icons (`reset_camera_icon`, `screenshot_icon`, `reset_defaults_icon`) still call `qta.icon` with the documented mdi6 names. Currently `test_icon_functions_call_qta_icon_with_correct_args` covers this — Test A is a dedicated rename with a clearer pass/fail signal.
   - **Test B** (`test_camera_preset_icons_correct_names_and_colors`): for each of 7 preset factories, assert `qta.icon` called with correct `mdi6.axis-{x,y,z}-arrow` (or `mdi6.axis-arrow` for iso) + correct `rotated=` (0 or 180) + `color=_icon_color(theme)`. Both themes.
   - **Test C** (`test_display_toggle_icons_correct_names_and_colors`): `wireframe_icon` and `show_edges_icon` call qta with `mdi6.grid` / `mdi6.border-outside` + TEXT_VALUE color (NOT TEXT_RESET_BTN — standard toggles). Both themes.
   - **Test D** (`test_wireframe_and_edges_icons_are_distinct_names`): assert `icons.WIREFRAME_ICON_NAME != icons.SHOW_EDGES_ICON_NAME`. Guards against copy-paste error where both toggles get the same glyph.
   - **Extend Test E**: add all 9 new icon functions to the `targets` tuple. Skip pattern unchanged.
   ~75 LOC.

6. **CONTEXT.md** — Update §3 stack-rationale paragraph to reflect v1 closing (camera presets + display toggles); update §9 deferred-scope bullet to narrow to "render spinner only (deferred to v2)". ~10 LOC delta.

7. **Verify** —
   - `pytest tests/ -q` stays at 297+5 = 302.
   - No off-screen render required (icon-only change, no generator/render-pipeline touch per CONTEXT.md §10).
   - Manual sanity: the 9 new icons visually distinct at 16px (researcher confirmed via charmap; no QApplication-based render needed to ship).

8. **Commit** — `feat(qtawesome-icons-2026q2-e2): extend qtawesome to camera-preset buttons + display toggles (v1)`.
