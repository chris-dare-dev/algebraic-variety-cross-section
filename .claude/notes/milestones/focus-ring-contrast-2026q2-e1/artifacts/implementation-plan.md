# Implementation plan — focus-ring-contrast-2026q2-e1

**Inline path. ~35 LOC across 2 files.** Close the deferred M4 finding from `panel-refresh-2026q2-e2` (UPL-1). Researcher confirmed Option A (single shared value `#3c82c4`) clears 3:1 on both panel backgrounds with margin: 3.56:1 on light, 3.78:1 on dark.

1. **styles.py:88 + 83-87** — Change `PALETTE_LIGHT["FOCUS_RING"]` from `#5b9bd5` to `#3c82c4`. Replace the 5-line deferral comment block with the new "fixed in focus-ring-contrast-2026q2-e1" comment recording both measured ratios (3.56:1 light, 3.78:1 dark). ~7 LOC delta.

2. **styles.py:225 + 222-224** — Change `PALETTE_DARK["FOCUS_RING"]` from `#5b9bd5` to `#3c82c4` (still a shared value with PALETTE_LIGHT, preserving the key-identical pattern). Replace the 3-line PALETTE_DARK comment block to reflect the new value and cross-theme pass. ~5 LOC delta.

3. **tests/test_styles_palette.py** — Add `test_light_non_text_borders_meet_wcag_aa_on_bg_panel` immediately after the existing `test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark` (~line 437). **Critical nuance the researcher caught:** the test must be FOCUS_RING-only, NOT a 1:1 copy of the dark test. The 4 structural border tokens (BORDER_GROUP_BOX, BORDER_DOCK_HEADER, BORDER_CAMERA_BTN, BORDER_RESET_BTN) measure 1.1–1.4:1 on the LIGHT panel — they are structural separators, not WCAG 1.4.11-subject UI components against the panel ground (mirror of the dark mode pattern documented in CONTEXT.md §4.3b). Only FOCUS_RING bears the obligation on light. Docstring explicitly names this distinction so a future maintainer doesn't "helpfully" expand the assertion set. ~20 LOC.

4. **Verify** —
   - `pytest tests/ -q` stays at 295+1 = 296.
   - Sanity-check that the new test FAILS on the pre-change `#5b9bd5` value (proves the regression guard works) — done via a temporary local revert + re-run before committing.
   - Existing `test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark` continues to pass (FOCUS_RING dark margin drops from 5.17 to 3.78, still ≥3.0).
   - Existing `test_app_stylesheet_dark_no_raw_hex` continues to pass (`#3c82c4` is in PALETTE_DARK).
   - No off-screen render required (palette-only change, no render pipeline touched per CONTEXT.md §10).

5. **Commit** — `feat(focus-ring-contrast-2026q2-e1): darken FOCUS_RING to #3c82c4 (WCAG 1.4.11 fix on light theme)`.
