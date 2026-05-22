# Adversary critique — variety-palette-2026q2-e1

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-21 | **Subject:** variety-palette-2026q2-e1 / ae2b70d..b976674

---

## Diff stats

| Metric | Value |
|---|---|
| Commits | 1 (`b976674`) |
| Files changed | 4 (`app.py`, `appearance_panel.py`, `styles.py`, `tests/test_styles_palette.py`) |
| Lines changed | +196 / -20 (258 total — below 400-LOC auto-finding threshold) |
| Tests before / after | 175 / 178 (net +3: +4 new, −1 stub) |

---

## Executive summary

The highest-severity finding is a **stale UPL-5 forward-reference left standing in three places** (`styles.py:22`, `styles.py:46`, `appearance_panel.py:82`) after this milestone is the one that implements UPL-5's intent — these comments now describe a future work that has already shipped. No CRITICALs. One HIGH (stale forward-reference comments, documentation drift that directly contradicts the current state of the module). Two MEDIUMs: (1) the new `AppearancePanel.set_default_color()` public API has zero direct test coverage — only the underlying dict is exercised; (2) the nested `luminance/ratio` implementation inside `test_critical_text_tokens_meet_wcag_aa_on_bg_panel` was consciously left as a duplicate rather than refactored to use the new module-level helpers, violating the Axis 10 "no backward-compat shims" scope discipline rule. One LOW: CONTEXT.md section 4 (panel API catalogue) was not updated with the new `set_default_color` method signature. Foundation is sound, math is correct, Unicode keys are verified, all 4 WCAG ratios independently re-confirmed, wire path is correct. Safe to merge after the HIGH and MEDIUMs rectify.

---

## Critical findings

None.

---

## High findings

### HIGH — Stale UPL-5 forward-references contradict shipped reality

**Where:** `styles.py:22`, `styles.py:46`, `appearance_panel.py:82`
**Evidence:** The module docstring at `styles.py:22` reads `"VARIETY_DEFAULT_COLOR — empty stub; UPL-5 will populate with per-variety default surface colors"`. The block comment at `styles.py:46` reads `"UPL-5 (per-variety surface color) will populate VARIETY_DEFAULT_COLOR from this same module"`. The initializer comment at `appearance_panel.py:82` reads `"UPL-5 will override _surface_color per-variety via apply_to_actor()"`. All three statements are now false: this milestone (`variety-palette-2026q2-e1`, closing UPL-2) has populated the dict and wired the override via `set_default_color`. The `styles.py` diff correctly updated the `VARIETY_DEFAULT_COLOR` block comment to say "populated by variety-palette-2026q2-e1" but left the two pre-existing stale references in the module docstring and the `PALETTE_LIGHT` block comment untouched. `appearance_panel.py` adds the new method at line 320 but the `__init__` comment at line 82 still promises future work that has arrived.
**Why it matters:** A maintainer reading the module docstring or `appearance_panel.__init__` will believe the dict is still an empty stub and that the color override is still wired through `apply_to_actor` rather than `set_default_color`. This is the class of comment drift that causes future agents to re-implement already-shipped work or to look in the wrong place for the wire point.
**Suggested fix:** Update `styles.py:22` to `"VARIETY_DEFAULT_COLOR — per-variety default surface colors, keyed by variety family name. Populated in variety-palette-2026q2-e1 (UPL-2)."` Update `styles.py:46` analogously. Update `appearance_panel.py:82` to reference `set_default_color` as the current mechanism.
**Regression-guard test:** The stale comment is not testable, but a grep-based CI lint rule `grep -n "UPL-5 will" styles.py appearance_panel.py` that asserts zero matches would catch any re-introduction.

---

## Medium findings

### MEDIUM — `set_default_color` public method has no direct test

**Where:** `appearance_panel.py:320`; test coverage gap in `tests/`
**Evidence:** The four new tests in `tests/test_styles_palette.py` all exercise `styles.VARIETY_DEFAULT_COLOR` as a data structure (key set, hex format, WCAG ratio, key-vs-VARIETIES). None of them instantiate `AppearancePanel` and call `set_default_color`, so the method's two observable postconditions — `self._surface_color` is updated and `self._surf_swatch` receives the new color via `_apply_swatch_color` — are never asserted. The `QColor.isValid()` guard (the early-return on invalid hex) is also uncovered. Because `AppearancePanel` is a Qt widget, a full instantiation test would conflict with AI-2. However, the method's core logic (`QColor(hex_str)`, guard, `self._surface_color = color`, `_apply_swatch_color(...)`) is plain Python — a test that monkey-patches `_apply_swatch_color` and inspects `_surface_color` directly would work without a QApplication.
**Why it matters:** If a future refactor accidentally breaks the `_surf_swatch` refresh (e.g., passes `color.name()` instead of `color` to `_apply_swatch_color`), the four palette tests will continue to pass, and the swatch will silently stop updating on variety switch. The bug is invisible until a user notices the swatch is stuck.
**Suggested fix:** Add a test in `tests/test_styles_palette.py` (or a new `tests/test_appearance_panel_color.py`) that creates a minimal mock of `AppearancePanel._surface_color` and `_surf_swatch` and asserts both are updated by `set_default_color`; also assert the invalid-hex guard returns without mutation.

### MEDIUM — Duplicate `luminance` / `ratio` implementation retained as "backward-compat"

**Where:** `tests/test_styles_palette.py:230-242` (nested inside `test_critical_text_tokens_meet_wcag_aa_on_bg_panel`)
**Evidence:** The module-level comment at `tests/test_styles_palette.py:21-23` states: `"The local nested copy in that test is left in place for backward-compat readability of its self-contained fixture; this module-level pair is the source of truth for new callers."` The nested `luminance` / `ratio` functions at lines 230-242 are identical to the module-level `_luminance` / `_ratio` at lines 26-41 — verified by direct comparison. The phrase "backward-compat readability" applied to a test helper that has no external callers is an Axis 10 scope-discipline violation: it is precisely the "backwards-compat shim" pattern that CONTEXT.md section 12 forbids.
**Why it matters:** Two implementations of the same WCAG formula in the same file drift independently. If WCAG 2.x is ever revised (e.g., the 0.03928 linearization threshold is updated to 0.04045 per the WCAG 2.2 erratum discussion), whoever updates the module-level helper may not notice the nested copy. Both implementations use 0.03928 today — a future maintainer updating only one will silently produce inconsistent test results.
**Suggested fix:** Replace the nested `luminance` / `ratio` functions inside `test_critical_text_tokens_meet_wcag_aa_on_bg_panel` with calls to the module-level `_luminance` / `_ratio`. No change to the test's assertions needed; only the local function definitions are removed.

---

## Frontend UI/UX findings

(Merged from `frontend-critique.md` — the frontend-ux critic walked the 12-axis UI/UX checklist; 8/12 axes were not applicable to this milestone's diff.  Findings below cover the one new MEDIUM and one new LOW (the second LOW overlapped with the adversary HIGH and is consolidated under that entry).  Full 12-axis walkthrough in `frontend-critique.md`.)

### MEDIUM — Swatch chip contrast on BG_PANEL is below WCAG AA for all four family colors

**Where:** `styles.py:122-127` (VARIETY_DEFAULT_COLOR values); `appearance_panel.py:50-54` (`_apply_swatch_color`)
**Evidence:** Independent re-measurement against `BG_PANEL (#f0f0f0)`: K3 #8e9ed4 → 2.31:1, Enriques #c4a882 → 1.99:1, CY3 #85b5d0 → 1.94:1, Fano #8fbe85 → 1.87:1.  All four PASS against `BG_VIEWPORT (#2f2f2f)` at 5.09–6.29:1 (the rendered mesh is legible), but fail WCAG 2.1 §1.4.11 non-text-contrast 3:1 threshold against the light panel background where the 20×20 px swatch chip sits.
**Why it matters:** The swatch is the sole visual confirmation that the variety-family default has been applied before the user clicks "Surface…". Users with mild CVD or on low-contrast displays may not notice the seeding and re-select manually. Identity-cue value is diminished.
**Suggested fix (V1 / UPL-4 scope):** Either (a) render the 20×20 swatch inside a small dark-panel wrapper matching BG_VIEWPORT (the ParaView "mini-viewport chip" pattern), (b) add a darker 2 px swatch border, or (c) add a thin variety-name label below the chip to make it decorative-only.  Defer to UPL-4 since the wrapper background would need to respect active theme.

### LOW — Hue-separation comment claims ">=25° pairwise" but K3 vs CY3 measures 24.69°

**Where:** `styles.py:120`
**Evidence:** Float-precision HSV: K3 226.29° vs CY3 201.60° → 24.69°.  All other pairs comfortably exceed 25°.  The perceptual distinction is fine; the quantitative claim is just inaccurate.
**Suggested fix:** Change to ">=24° pairwise (K3–CY3 is the tightest pair at ~24.7°, perceptually distinct under mild CVD due to saturation difference)."

---

## Low findings

### LOW — CONTEXT.md section 4 not updated with new `AppearancePanel.set_default_color` API

**Where:** `/CONTEXT.md` section 4 (panel architecture / public-API catalogue)
**Evidence:** CONTEXT.md section 4 (line 129 in the current file) documents `appearance_panel.apply_to_actor(self._actor)` as the primary AppearancePanel outbound API. The new `set_default_color(hex_str)` method is a second public entry point added in this milestone; it mutates `_surface_color` and refreshes `_surf_swatch` without triggering a render. This contract (who calls it, when, and why it doesn't render) is load-bearing for future panel-wiring work (UPL-3, UPL-25) but is not recorded in CONTEXT.md.
**Why it matters:** Future agents auditing AppearancePanel's public surface will miss this method when planning color-related features. The method's "does NOT trigger render" contract is non-obvious and worth capturing alongside the UPL-25 forward-ref already in the commit message.
**Suggested fix:** Add a one-line entry to CONTEXT.md section 4 under AppearancePanel's API listing: `set_default_color(hex_str)` — seeds `_surface_color` and refreshes swatch on variety/subtype switch; does NOT trigger render (caller flows into `_render_current` → `apply_to_actor`).

---

## What was done well

- **Unicode key codepoints copy-pasted, not retyped.** The Calabi–Yau key uses U+2013 (en-dash) and the Fano key uses U+03C1 (rho), confirmed by direct byte-level inspection. The inline comments `# U+2013 en-dash in key` and `# U+03C1 rho in key` at `styles.py:125-126` are a clear audit trail for any future maintainer who reads the source in a terminal that renders both characters identically to their ASCII lookalikes.

- **`set_default_color` correctly decoupled from rendering (AI-9 safe).** The method mutates `self._surface_color` and refreshes the swatch without calling `processEvents` or triggering any render path. The call in `_on_variety_changed` happens inside the `blockSignals(True)` window, and the call in `_on_subtype_changed` happens before `_render_current`, so `apply_to_actor` reads the updated color on the very next pass. No re-entrancy risk introduced.

- **WCAG ratios independently verified against the correct background.** All four hex values clear 4.5:1 against `BG_VIEWPORT` (#2f2f2f): K3 5.095:1, Enriques 5.910:1, CY3 6.068:1, Fano 6.294:1. Using the text-contrast threshold (4.5:1) rather than the non-text threshold (3:1) was the right call — the surface fills the dark canvas and functions as a family-identity cue, not a decorative accent.

- **Dynamic BG_VIEWPORT lookup in the WCAG test.** `test_variety_default_color_wcag_on_bg_viewport` reads `bg = styles.PALETTE_LIGHT["BG_VIEWPORT"]` rather than hardcoding `"#2f2f2f"`. If the viewport background changes in a future token update, the test automatically re-verifies the new ratio — no silent stale assertion.

- **The `QColor.isValid()` guard in `set_default_color` is correctly placed.** An invalid hex value silently preserves the existing color rather than corrupting `_surface_color` to a black `QColor(0,0,0,0)`. This matches the existing defensive pattern throughout the panel code and is the correct behavior when the input comes from a dict that the test suite already validates.

- **The `VARIETY_DEFAULT_COLOR.get(variety, BG_SURFACE_DEFAULT)` fallback is correct.** Both `_on_variety_changed` and `_on_subtype_changed` use `.get()` with `BG_SURFACE_DEFAULT` as the default, ensuring a new variety added to `VARIETIES` without a corresponding `VARIETY_DEFAULT_COLOR` entry gracefully reverts to the legacy lightsteelblue rather than crashing. The `test_variety_default_color_keys_match_surfaces_varieties` guard catches the reverse (stale dict key after a variety rename).

- **Hue separation documented in the block comment.** The `styles.py:120` note `"Hue separations are >=25° pairwise (perceptually distinct even under mild color-vision deficiency)"` is a concrete, auditable claim — not a vague "visually distinct" assertion. This is the right epistemic standard for a milestone that sets design tokens used by future UPL-3 (color-map preset picker) and UPL-4 (dark mode).

- **Stub test replaced, not orphaned.** `test_variety_default_color_is_stub_for_upl5` was removed and four substantive tests were added in its place. The old test's assertion `assert styles.VARIETY_DEFAULT_COLOR == {}` would have failed after this milestone; keeping it would have broken the test suite immediately.

---

## Recommended rectification order

1. **Fix the HIGH: update the three stale UPL-5 forward-references.** Update `styles.py:22`, `styles.py:46`, and `appearance_panel.py:82` to reflect that the dict is now populated and the wire mechanism is `set_default_color`. Two-minute change; no test changes needed.

2. **Fix MEDIUM 2 (duplicate luminance): remove the nested functions from `test_critical_text_tokens_meet_wcag_aa_on_bg_panel`.** Replace the local `luminance` and `ratio` functions with calls to the module-level `_luminance` and `_ratio`. Reduces test file by ~12 lines; assertions unchanged.

3. **Fix MEDIUM 1 (missing set_default_color test): add a minimal test.** A test that directly exercises `set_default_color` against a mock or lightweight fixture, asserting `_surface_color` update and `QColor.isValid()` guard behavior. Can live in `tests/test_styles_palette.py` without a QApplication if `_apply_swatch_color` is patched.

4. **LOW: update CONTEXT.md section 4.** One-line addition documenting `set_default_color`'s "no render" contract.

---

*End of critique. Mandatory rectification: the HIGH and both MEDIUMs. The LOW is recommended before milestone close but does not block merge.*
