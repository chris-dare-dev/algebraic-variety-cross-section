# Frontend UI/UX Critique — focus-ring-contrast-2026q2-e1

**Milestone:** `focus-ring-contrast-2026q2-e1`
**Commit range:** `17f7d527dde429f20c7cdd803e2c0b532304a778..HEAD`
**Changed files (Qt-panel surface):** `styles.py`, `tests/test_styles_palette.py`
**Critic:** milestone-frontend-ux-critic (claude-sonnet-4-6)
**Date:** 2026-05-22

---

## Executive summary

Zero CRITICAL findings. Zero HIGH findings. One MEDIUM finding (dark-panel
contrast is a net regression, though it remains above the 3:1 floor). Two
LOW findings (narrow light-panel margin leaves little tolerance for future
palette drift; test-scope docstring deterrent is documentation-only, not
code-enforced). The arithmetic in the palette comments is independently
verified correct. The change is a genuine accessibility improvement for the
light theme and a compliant (if narrower) result on dark.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM — Dark-panel focus-ring contrast is a net regression (5.17:1 → 3.78:1)

**Where:** `styles.py:230` (`PALETTE_DARK["FOCUS_RING"]`)

**Evidence:** Independent WCAG 2.x luminance computation:
- `#5b9bd5` (old) vs `#252526` (BG_PANEL_DARK) = **5.173:1**
- `#3c82c4` (new) vs `#252526` (BG_PANEL_DARK) = **3.779:1**

The old value passed dark at 5.17:1 — 72% headroom above the 3:1 floor.
The new shared value passes at 3.78:1 — only 26% headroom. While both clear
the WCAG 1.4.11 non-text 3:1 floor, the dark-mode accessibility posture is
objectively weaker, and the migration comment frames this as a neutral trade
("single shared value satisfies both themes") without acknowledging the
regression in dark headroom.

The practical risk: the dark app is the **launch default** per CONTEXT.md
§4.3b. The majority of sessions will experience the lower-headroom ring.
A monitor or rendering environment that shows the `#252526` panel as even
slightly lighter (e.g., uncalibrated display, low brightness) will push
the perceived contrast below 3:1 before the WCAG-computed figure does.

**Why it matters:** The comment reads "both PASS" which is literally true
but obscures a 1.39:1 drop. A future maintainer seeing "both PASS" has no
signal that dark headroom eroded. If a subsequent palette touch lightens
`#3c82c4` by even a small amount (e.g., to `#4c8ec8`) the dark contrast
falls to approximately 3.0:1 — the exact boundary — while the light
contrast is still fine. The erosion is one PR away.

**Suggested fix:** Either (a) keep a per-theme FOCUS_RING value (`#3c82c4`
light, `#5b9bd5` dark — the symmetric fix is to keep the old dark value as
the new dark token since it already passes both floors) rather than a shared
value, or (b) amend the comment to read something like "Dark contrast
dropped from 5.17:1 to 3.78:1 — still above 3:1 floor but reduced headroom;
see test_dark_non_text_borders for the live guard."

---

## LOW

### LOW-1 — Light-panel contrast margin is narrow; palette comment overstates confidence

**Where:** `styles.py:90` (inline comment on `PALETTE_LIGHT["FOCUS_RING"]`)

**Evidence:** `#3c82c4` vs `#f0f0f0` = **3.556:1** — only 18.5% above the
3:1 floor (0.556:1 absolute headroom). The comment states "3.56:1 — PASS"
with no qualification. For comparison: macOS Sequoia system blue
(`#007aff`) clears 3.53:1 and GNOME Adwaita (`#3584e4`) clears 3.31:1 on
the same background — the new value is in the same narrow-pass band used by
peer platforms. This is not wrong, but it is fragile.

The existing `test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel` test
will catch a future regression, so the risk is bounded. The issue is the
comment's tone of finality: "PASS" implies comfortable headroom it does not
have.

**Why it matters:** A designer reading the comment might choose `#4c8ec8`
(one shade lighter, still looks similar) believing the annotation implies
headroom. That shade measures approximately 3.0:1 — passing only at the
floor. The comment should convey that this is a near-floor pass.

**Suggested fix:** Amend the inline comment to: `(3.56:1 — PASS, narrow
margin; do not lighten further)`.

---

### LOW-2 — Test-scope deterrent in `test_light_non_text_focus_ring` is documentation-only

**Where:** `tests/test_styles_palette.py:453–463` (docstring caveat in
`test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel`)

**Evidence:** The docstring includes the warning "Caveat on token scope (do
NOT widen this assertion set)" and explains that the four structural border
tokens (`BORDER_GROUP_BOX`, `BORDER_DOCK_HEADER`, `BORDER_CAMERA_BTN`,
`BORDER_RESET_BTN`) in `PALETTE_LIGHT` are intentionally ~1.1–1.4:1 and
must not be tested against the 3:1 floor. This is correct and well-explained.
However, the deterrent is documentation; there is no code-level guard (e.g.,
a comment assertion or a separate negative test) that would fail CI if a
future maintainer widened the `non_text_tokens` tuple to include those four
tokens.

**Why it matters:** The dark-twin test
(`test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark`) DOES include
those four tokens and passes because they were intentionally darkened. The
asymmetry between the two tests is intentional but not immediately obvious:
a maintainer reading the dark test and wanting to add the same coverage for
light could add the four tokens to the wrong test, produce false failures,
and then change `PALETTE_LIGHT` values to "fix" them — silently degrading
light-mode structural chrome.

**Suggested fix:** Add a lightweight negative guard: a separate test
`test_light_structural_borders_intentionally_below_3:1` that *asserts* the
four structural tokens are less than 3.0:1 on `BG_PANEL_LIGHT`. This makes
the design intent machine-readable: any future attempt to meet the 3:1
threshold on those tokens will fail that test and force a deliberate design
decision rather than an accidental palette change.

---

## What was done well

1. **Arithmetic is correct and independently verified.** The comment
   annotations `2.60:1 → 3.56:1 (light), 5.17:1 → 3.78:1 (dark)` match
   independent computation to three decimal places. This continues the
   strong ratio-annotation discipline established in dark-mode-2026q2-e1.

2. **Token hygiene is clean.** The new value `#3c82c4` is 6-digit (AI-13
   compliant), no new Qt enums are introduced (AI-11 clean), no
   `processEvents` is added (AI-9 clean), and the change touches exactly
   two palette entries — no scope creep.

3. **Both palettes updated atomically.** `PALETTE_LIGHT["FOCUS_RING"]` and
   `PALETTE_DARK["FOCUS_RING"]` change in the same commit. The single-shared-value
   pattern preserves the key-identical palette invariant enforced by
   `test_palette_dark_has_minimum_tokens`.

4. **Test added for the specific failure this fixes.** The new
   `test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel` closes a
   gap that was present through the entire prior palette migration history
   (the light FOCUS_RING floor was never asserted before this milestone).
   The docstring explanation is thorough and correctly attributes the prior
   FAIL to `panel-refresh-2026q2-e2`.

5. **Industry alignment confirmed.** The new `#3c82c4` (3.56:1 on light)
   lands in exactly the same band as macOS Sequoia `#007aff` (3.53:1) and
   GNOME Adwaita `#3584e4` (3.31:1) against comparable light panel
   backgrounds — the value is not arbitrary but aligns with mainstream
   desktop accessibility practice.

6. **No first-launch regression.** Focus ring is invisible until keyboard
   navigation begins. Section 9.3 (no auto-render) is unaffected.

---

## Recommended rectification order

1. **MEDIUM — Dark-panel regression comment.** Add a quantitative note to
   the `PALETTE_DARK["FOCUS_RING"]` comment acknowledging the drop from
   5.17:1 to 3.78:1 and why this is an intentional trade. Alternatively,
   restore `#5b9bd5` as the dark-only token (breaking the shared-value
   pattern but recovering the 5.17:1 dark headroom). Low effort; high
   documentation value.

2. **LOW-1 — Narrow-margin comment.** Add `(narrow margin; do not lighten
   further)` to the `PALETTE_LIGHT["FOCUS_RING"]` inline comment.
   One-word change; prevents future over-lightening.

3. **LOW-2 — Negative test guard.** Add
   `test_light_structural_borders_intentionally_below_3:1` asserting
   `< 3.0:1` for the four structural light-palette border tokens. This makes
   the asymmetry between the light and dark border tests machine-readable.
