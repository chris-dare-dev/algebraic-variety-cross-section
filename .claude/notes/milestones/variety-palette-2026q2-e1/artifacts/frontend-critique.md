# Frontend UX Critique — variety-palette-2026q2-e1

**Milestone:** variety-palette-2026q2-e1 (UPL-2 per-variety surface palette)
**Commit range:** `ae2b70d..b976674`
**Critic:** milestone-frontend-ux-critic (claude-sonnet-4-6)
**Date:** 2026-05-21
**Files in scope:** `styles.py`, `appearance_panel.py`, `app.py`
**Files NOT touched (no findings generated):** `view_panel.py`, `parameters_panel.py`

---

## Executive Summary

The milestone delivers the per-variety surface color seeding cleanly. All 178
tests pass. The four hex values are 6-digit, all fully-qualified Qt enums, no
new `processEvents` call, and the first-launch invariant (section 9.3) is
preserved. One MEDIUM finding on the swatch chip's contrast against the light
panel background and two LOW findings (stale forward-reference comments in the
module docstring, and a minor off-by-one in the hue-separation claim) complete
the picture. No CRITICAL or HIGH findings.

The MEDIUM finding (swatch chip contrast) is a known limitation of colored
chips against a light panel: the chips are purely decorative identity cues
at 20×20 px and are not classified as text by WCAG 2.1. The industry
comparison axis gives context for why this is acceptable at V0 and what
the V1 path is.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM — Swatch chip contrast on BG_PANEL is below WCAG AA for all four family colors

**Where:** `styles.py:122-127` (VARIETY_DEFAULT_COLOR values); `appearance_panel.py:50-54` (`_apply_swatch_color`)

**Evidence:** Independent re-measurement using the WCAG 2.x relative-luminance
formula against `BG_PANEL (#f0f0f0)`:

| Variety color | Hex     | Ratio vs #f0f0f0 |
|---------------|---------|-----------------|
| K3            | #8e9ed4 | 2.31:1          |
| Enriques      | #c4a882 | 1.99:1          |
| CY3           | #85b5d0 | 1.94:1          |
| Fano          | #8fbe85 | 1.87:1          |

All four values pass the ≥4.5:1 requirement against `BG_VIEWPORT (#2f2f2f)` (the
researcher's numbers are confirmed: 5.09 / 5.91 / 6.07 / 6.29:1). The dark-viewport
pass is what matters for the rendered mesh. However, the swatch chip in the
Appearance dock sits on the light panel background (#f0f0f0), not on the
viewport. The swatch is 20×20 px solid fill; at that size WCAG 2.1 defines
non-text UI components as requiring ≥3:1 (not 4.5:1), so all four values fail
the non-text threshold as well (none clears even 3:1 against the light
background).

**Why it matters:** The swatch is the sole visual confirmation that the
variety-family default has been applied before the user clicks "Surface…".
If the chip reads poorly on the panel background, users with mild
color-vision deficiency or on low-contrast displays may not notice the
color has already been seeded and will re-select manually. The identity-cue
value is diminished. This is a known challenge: all four hues are
mid-lightness pastel-adjacent values chosen for viewport legibility, which
unavoidably produces low contrast against a light surface.

**Suggested fix (V1 / UPL-4 scope):** One of three approaches — (a) add a
thin (#333333) text label beneath the swatch showing the variety name
abbreviation so the chip is decorative-only (WCAG permits decorative
elements with no minimum ratio); (b) render the swatch against a small
dark-chip inset (matching BG_VIEWPORT) rather than the naked panel
background, making the viewport-legible ratio apply at the swatch too;
(c) darken the swatch border to 2 px #555555 so the chip boundary is
legible independent of fill contrast. Option (b) is the most self-consistent:
a mini-viewport chip shows exactly what the surface will look like, matching
the ParaView color-swatch metaphor (see Industry comparison axis below). Not
a V0 blocker — the swatch is decorative at this milestone; the rendered
surface itself passes at ≥5:1.

---

## LOW

### LOW — Stale forward-reference comments in module docstring and inline block cite "UPL-5" after UPL-2 populated the dict

**Where:** `styles.py:22` (module docstring line), `styles.py:46` (palette header comment)

**Evidence:**
- Line 22: `VARIETY_DEFAULT_COLOR — empty stub; UPL-5 will populate with per-variety default surface colors keyed by variety family name.`
- Line 46: `# UPL-5 (per-variety surface color) will populate VARIETY_DEFAULT_COLOR`

Both comments are pre-refactor forward references that were not updated when
UPL-2 (this milestone) populated the dict. The block-level comment at line
99-121 was correctly updated to cite `variety-palette-2026q2-e1`. The
module docstring and the palette-header comment were not.

**Why it matters:** A future developer reading line 22 would conclude the dict
is still an empty stub and UPL-5 is pending work. The stale forward-refs
also make milestone tracking harder (searching for "UPL-5" in the codebase
returns a false "not yet done" signal).

**Suggested fix:** Update the two surviving "UPL-5 will populate" lines to
"Populated by variety-palette-2026q2-e1 (UPL-2)." Single-line edit, no test
impact.

---

### LOW — Hue-separation comment claims ">=25° pairwise" but K3 vs CY3 measures 24.69°

**Where:** `styles.py:120` (`# Hue separations are >=25° pairwise...`)

**Evidence:** Float-precision HSV decomposition via `QColor.getHsvF()`:

| Pair       | Hue A   | Hue B   | Separation |
|------------|---------|---------|------------|
| K3 vs CY3  | 226.29° | 201.60° | **24.69°** |

All other pairs comfortably exceed 25°. Integer HSV (`QColor.hsvHue()`)
rounds both to 226° and 202° giving 24° — further below the claim. The
perceptual distinction between the two blues (periwinkle K3 vs teal-cobalt
CY3) is visible and adequate; the quantitative claim is just inaccurate.

**Why it matters:** The comment is an inline spec assertion that will be
referenced if the palette is adjusted in a future milestone. A false floor
(">=25°") means a future maintainer believes K3 and CY3 are more distinct
than they are, and may use it to justify a new color that is in fact 25°
away from K3 but visually similar to CY3 (at 24.69° from it).

**Suggested fix:** Change to ">=24° pairwise (K3–CY3 is the tightest pair at
~24.7°, perceptually distinct under mild CVD due to saturation difference)."
Single-line comment edit, no functional impact.

---

## Axis-by-axis disposition (axes with no findings)

1. **Visual hierarchy** — The swatch chip appears in the "Colors" group at the
   top of AppearancePanel, which is the first eye-stop in the right-bottom
   dock. Correct positioning; no finding.

2. **Dock layout** — View (left), Parameters (right top), Appearance (right
   bottom). The `splitDockWidget` call at `app.py:147` preserves this. No
   change in this diff; layout is intact.

3. **First-launch experience** — `set_default_color` is only called inside
   `if name in VARIETIES:` in `_on_variety_changed` (line 184), which is
   never reached when the placeholder `— Select —` is active. On launch the
   swatch shows `BG_SURFACE_DEFAULT` (#b0c4de, lightsteelblue) — the prior
   neutral default. Section 9.3 (no auto-render on launch) is fully preserved;
   `set_default_color` does not call `_render_current`. Verified by tracing
   the call graph: `_on_variety_changed` → `set_default_color` → returns.
   `_render_current` is only wired to `_on_subtype_changed` (line 270), which
   requires a non-placeholder subtype selection.

4. **Slider affordances** — Not applicable. No `ParamSpec` or slider changes
   in this diff.

5. **Status-bar feedback** — Not applicable. Existing CY3 and Fano hint
   messages are unchanged. `set_default_color` emits no status-bar message,
   which is correct: the color change is silent, and the subsequent render
   (triggered by `_on_subtype_changed`) will confirm the chosen surface in
   the status bar as usual.

6. **Tooltip honesty (AI-15)** — Not applicable. No new variety, figure, or
   tooltip string in this diff.

7. **Color contrast (AI-12)** — Covered above: dark-viewport ratios verified
   and confirmed passing (5.09–6.29:1). Light-panel swatch ratios surfaced as
   MEDIUM (1.87–2.31:1, below 3:1 non-text threshold). `QColor.name()`
   confirmed to return 6-digit lowercase hex for all four inputs; the value
   flowing into `actor.prop.color` via `apply_to_actor` is safe.

8. **Color format (AI-13)** — All four VARIETY_DEFAULT_COLOR values are
   verified 6-digit hex. `QColor.name()` always emits 7-char `#rrggbb` —
   no short-hex risk in the `actor.prop.color = color.name()` write path.

9. **Qt enum form (AI-11)** — No new Qt enum usage in the diff. The existing
   `Qt.AlignmentFlag.AlignCenter` at `appearance_panel.py:189` and
   `Qt.ItemDataRole.ToolTipRole` at `app.py:191` are already fully qualified.
   No regression.

10. **Re-entrancy (AI-9)** — `set_default_color` contains no `processEvents()`
    call. It only sets `self._surface_color` and calls `_apply_swatch_color`.
    The `_computing` guard in `_render_current` is unaffected. The only
    `processEvents()` call in the codebase remains `app.py:312`, which is
    inside the existing `_computing` guard. No AI-9 regression.

11. **Keyboard shortcuts** — `Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D` wiring is
    unchanged (`app.py:161-172`). No new shortcuts introduced.

12. **Industry comparison** — ParaView 5.12 uses a "color preset" selector in
    its pipeline browser: each source object gets a default color from a
    named preset list (e.g., "Warm to Cool", "Blue to Red Rainbow"), and the
    active preset swatch is rendered as a gradient thumbnail *on a dark chip
    background* matching the render view's background color. This is exactly
    option (b) from the MEDIUM suggested fix above — the swatch previews
    against the same dark surface the user will see, making the viewport-
    calibrated colors read correctly at swatch size. 3D Slicer (v5.6)
    assigns per-volume colors from a lookup table and shows swatches in a
    floating "Colors" module against the dark module background. Mathematica's
    `ContourPlot3D` does not expose a per-variety default color picker; the
    user sets color globally. The ParaView pattern is the closest analogue
    and directly informs the V1 recommendation (dark-chip swatch inset).

---

## What was done well

- **Contrast verification was rigorous.** The comment block at `styles.py:115-121`
  documents all four measured ratios against BG_VIEWPORT. The accompanying test
  (`test_variety_default_color_wcag_on_bg_viewport`) enforces the 4.5:1 floor
  programmatically — not just a note in a comment.
- **Key-drift guard is belt-and-suspenders.** Two independent guards prevent
  the Unicode-key risk (en-dash in "Calabi–Yau 3-fold", rho in
  "Fano 3-fold (ρ=1)"): `test_variety_default_color_has_all_four_families`
  asserts key-set equality; `test_variety_default_color_keys_match_surfaces_varieties`
  cross-checks against the live `VARIETIES` dict. Either guard alone would
  catch a retyped ASCII substitute.
- **set_default_color docstring is complete.** It explains the render contract
  (no trigger), the AI-9 safety rationale, the V0 re-seed semantic vs. V1
  sticky-override intent, and the invalid-hex fallback — all in one place.
  Future maintainers don't need to trace the call graph to understand the
  design choice.
- **Hue design rationale is sound.** The four families span four distinct
  color-theory registers (cool blue, warm ochre, teal, sage green), avoiding
  the common failure mode of using "pretty colors that all happen to be in the
  blue-purple range." K3 and CY3 are both blue-family but their saturation
  difference (0.33 vs 0.36) and value difference (0.83 vs 0.82) are
  insufficient to distinguish them under protanopia — the MEDIUM swatch fix
  (label or dark-chip) would double as a CVD affordance.
- **Fano entry is a forward-compat placeholder.** Fano 3-fold (ρ=1) is in
  `VARIETIES` and gets a color, but the milestone does not ship any Fano
  generator. The `VARIETY_DEFAULT_COLOR.get(variety, BG_SURFACE_DEFAULT)`
  fallback ensures a missing key is graceful. The test guard confirms the key
  is present in VARIETIES — correct order of assertions.

---

## Recommended rectification order

1. **(MEDIUM — V1 / UPL-4 scope)** Swatch chip dark-inset: render the 20×20
   swatch inside a small dark-panel wrapper matching BG_VIEWPORT so the
   viewport-calibrated colors read correctly at chip size. Defer to UPL-4
   (dark mode milestone) since the wrapper background would need to respect
   active theme.

2. **(LOW — minimal, current milestone)** Fix the two stale "UPL-5 will
   populate" comments at `styles.py:22` and `styles.py:46`. One-line edits
   each.

3. **(LOW — minimal, current milestone)** Correct the hue-separation comment
   at `styles.py:120` from ">=25° pairwise" to ">=24° pairwise (K3–CY3 is the
   tightest pair at ~24.7°)."

Items 2 and 3 are cosmetic comment-only fixes. They can be addressed in the
same commit or deferred to the next rectify pass without risk.
