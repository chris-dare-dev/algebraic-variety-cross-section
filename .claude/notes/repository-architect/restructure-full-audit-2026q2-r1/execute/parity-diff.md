# Parity diff report — restructure-full-audit-2026q2-r1

## Test collection diff
  - baseline tests: 499
  - post     tests: 503
  - delta:          4
  - removed (in pre, not post): 0
  - added   (in post, not pre): 4

## Coverage diff (totals)
  - baseline coverage XML missing or unparseable

## Import-time diff
  - baseline: 759.9 ms
  - post:     683.1 ms
  - delta:    -10.1%

## Star-imports diff
  - new star-imports introduced: 0
  - star-imports removed:        0

## Symbol relocation audit (top-level def/class only)
  - symbols whose location changed: 25
    ~ ViewPanel: ['view_panel.py:43'] -> ['panels/view.py:43']
    ~ ParametersPanel: ['parameters_panel.py:36'] -> ['panels/parameters.py:36']
    ~ _DraggableDot: ['parameter_grid_panel.py:69'] -> ['panels/parameter_grid_panel.py:68']
    ~ ParameterGridPanel: ['parameter_grid_panel.py:123'] -> ['panels/parameter_grid_panel.py:122']
    ~ _make_swatch: ['appearance_panel.py:40'] -> ['panels/appearance.py:40']
    ~ _apply_swatch_color: ['appearance_panel.py:57'] -> ['panels/appearance.py:57']
    ~ _border_for_theme: ['appearance_panel.py:79'] -> ['panels/appearance.py:79']
    ~ AppearancePanel: ['appearance_panel.py:92'] -> ['panels/appearance.py:92']
    ~ test_dark_stylesheet_includes_role_selectors: ['tests/test_styles_palette.py:668'] -> ['tests/test_styles_palette.py:669']
    ~ test_bg_toggle_checked_token_is_six_digit_hex_in_both_palettes: ['tests/test_styles_palette.py:738'] -> ['tests/test_styles_palette.py:739']
    ~ test_bg_toggle_checked_value_appears_in_both_stylesheets: ['tests/test_styles_palette.py:773'] -> ['tests/test_styles_palette.py:774']
    ~ test_appearance_panel_colors_buttons_have_colors_button_role: ['tests/test_styles_palette.py:799'] -> ['tests/test_styles_palette.py:800']
    ~ test_appearance_panel_display_and_quality_group_header: ['tests/test_styles_palette.py:848'] -> ['tests/test_styles_palette.py:849']
    ~ test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox: ['tests/test_styles_palette.py:900'] -> ['tests/test_styles_palette.py:901']
    ~ test_dark_stylesheet_dock_title_has_explicit_color: ['tests/test_styles_palette.py:962'] -> ['tests/test_styles_palette.py:963']
    ~ test_dark_stylesheet_statusbar_has_explicit_background: ['tests/test_styles_palette.py:976'] -> ['tests/test_styles_palette.py:977']
    ~ test_get_variety_default_colors_returns_correct_dict: ['tests/test_styles_palette.py:992'] -> ['tests/test_styles_palette.py:993']
    ~ test_border_swatch_light_wcag_3_to_1_against_all_variety_fills: ['tests/test_styles_palette.py:1019'] -> ['tests/test_styles_palette.py:1020']
    ~ test_border_swatch_dark_wcag_3_to_1_against_bg_panel: ['tests/test_styles_palette.py:1048'] -> ['tests/test_styles_palette.py:1049']
    ~ test_border_swatch_dark_export_wired_through_appearance_panel: ['tests/test_styles_palette.py:1088'] -> ['tests/test_styles_palette.py:1089']
    ~ test_border_swatch_light_and_dark_diverge: ['tests/test_styles_palette.py:1139'] -> ['tests/test_styles_palette.py:1140']
    ~ test_qmenu_rule_present_in_both_stylesheets: ['tests/test_styles_palette.py:1154'] -> ['tests/test_styles_palette.py:1155']
    ~ test_preview_badge_separator_matches_base_msg: ['tests/test_styles_palette.py:1178'] -> ['tests/test_styles_palette.py:1179']
    ~ test_spinner_icon_rebind_sites_have_qtimer_lifetime_comment: ['tests/test_styles_palette.py:1208'] -> ['tests/test_styles_palette.py:1209']
    ~ test_subtype_tooltips_have_lod_disclosure: ['tests/test_styles_palette.py:1241'] -> ['tests/test_styles_palette.py:1242']
  - symbols lost entirely (present in pre, absent in post): 0
