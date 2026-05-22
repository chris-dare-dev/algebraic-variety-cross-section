# Frontend UX Critique — display-toggles-checkable-button-2026q3-e1

**Milestone:** display-toggles-checkable-button-2026q3-e1  
**Commit range:** bb8c369726d4e961f481bc8c769c7994e23a2ee4..HEAD  
**Files changed:** `appearance_panel.py`, `styles.py`, `tests/test_styles_palette.py`, `CONTEXT.md`  
**Critic:** milestone-frontend-ux-critic (claude-sonnet-4-6)  
**Date:** 2026-05-22

---

## Executive Summary

0 CRITICAL, 0 HIGH, 3 MEDIUM, 2 LOW.

The migration from `QCheckBox` to `QPushButton(checkable=True)` is architecturally sound and
industry-aligned. Token discipline is clean across all axes (AI-9, AI-11, AI-12, AI-13 all
pass). No first-launch regression. The three MEDIUM findings are: (1) the unchecked
ghost-button style contradicts how Blender, 3D Slicer, and ParaView handle off-state toggles
in their display panels -- all three use a visually non-transparent off state; (2)
`text-align: left` on the display-toggle buttons creates an alignment mismatch with the
`Surface...` / `Background...` buttons directly above them in the same panel, which are
center-aligned by Qt default; (3) the WCAG 1.4.11 argument for the checked state carries
correctly at the button's outer edge (FOCUS_RING 3.56:1 / 5.17:1 vs panel ground) but the
comment's "~1.10:1 by design" fill-vs-hover claim is accurate yet invites confusion because
the more meaningful adjacent-surface contrast (FOCUS_RING vs BG_TOGGLE_CHECKED fill) is
3.17:1 (light) / 4.55:1 (dark) -- above the 3:1 floor -- and is not documented.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM-1 — Unchecked ghost-button style diverges from industry peer off-state convention

**Where:** `styles.py:504-510` (the `QPushButton[role="display-toggle"]` base rule)  
**Evidence:** The unchecked state sets `border: 1px solid transparent; background: transparent`.
At first launch (or any time both toggles are off), the two buttons render as plain
icon+text strings with no visible button chrome. Blender 4.x N-panel viewport overlay
section uses buttons with a visible background fill even in their off/unchecked state
(rgba darkening of the panel surface, not transparent). 3D Slicer 5.x module panel
toggles have a raised-style visible border in their default/inactive state. ParaView
uses plain `QCheckBox` (no icon) which has an always-visible check-square indicator.
In all three peers, the interactive affordance is visible before the user hovers.
In this implementation, the affordance is only revealed on hover.  
**Why it matters:** A researcher opening the Appearance dock for the first time sees
"Wireframe" and "Show edges" as what appears to be two plain labels with icons. Without
hovering, there is no visual signal that these are clickable controls. The tab-stop and
focus ring (via `QAbstractButton:focus`) will reveal them as interactive via keyboard
navigation, but mouse-first users will have to discover by accident or hover.  
**Suggested fix:** Add a minimal off-state border and background to the unchecked rule,
e.g. `border: 1px solid {palette["BORDER_CAMERA_BTN"]}; background: transparent` (the
camera-button border is already used for hover and is intentionally below 3:1 as a
structural separator on light -- this keeps the visual weight similar to the hover state
but at resting contrast). This mirrors the Blender/Slicer convention without introducing
a new token.

---

### MEDIUM-2 — `text-align: left` on display-toggle buttons misaligns with the Colors group above

**Where:** `styles.py:509` (`text-align: left` in the base display-toggle rule)  
**Evidence:** In the Appearance panel layout order: Colors group (Surface..., Background...
buttons) → Display group (Wireframe, Show edges) → Opacity group → Shading group. The
`Surface...` and `Background...` buttons inherit Qt's default `QPushButton` text alignment,
which is center. The `display-toggle` role rule explicitly sets `text-align: left`. The
result is two vertically adjacent groups where buttons in one group are center-aligned and
buttons in the next are left-aligned. On a narrow panel (~200px minimum width) this
is visually jarring: the "Surface..." label appears over the center of the button, while
"Wireframe" and "Show edges" are pushed left with the icon.  
**Why it matters:** `text-align: left` is correct for icon+label buttons (the icon anchors
left, text follows), but the mismatch with the adjacent `Surface...` / `Background...`
buttons breaks the vertical rhythm across group boundaries. Blender's N-panel keeps
consistent left-alignment for ALL icon-bearing controls within a section. ParaView's
Properties panel uses consistent left-alignment within each group.  
**Suggested fix:** Add `text-align: left` to the base `QPushButton` rule (the `padding: 3px
8px; border-radius: 3px` block at `styles.py:464-467`), or apply it specifically to the
Colors-group buttons via an additional QSS rule. Adding it globally is the lower-friction
path and matches industry convention: desktop scientific-viz apps left-align button text
uniformly.

---

### MEDIUM-3 — WCAG annotation documents fill-vs-hover contrast but omits the more informative fill-vs-border contrast

**Where:** `styles.py:116-123` and `styles.py:497-503` (palette and QSS comments)  
**Evidence:** The palette comment states: "its contrast vs the hover tint is ~1.10:1 by
design (state communicated by border, not fill)." The 1.10:1 fill-vs-hover claim is
verified accurate (measured 1.108:1 light, 1.147:1 dark). However the comment implies
the fill's only WCAG-relevant contrast pair is fill-vs-hover. The more meaningful pair for
understanding accessibility is FOCUS_RING border vs BG_TOGGLE_CHECKED fill (the inward
face of the 2px active-state border): measured 3.172:1 (light) / 4.547:1 (dark). This
value exceeds the 3:1 WCAG 1.4.11 non-text floor in both themes, which is a positive
result worth documenting -- it shows the border reads against the fill it's adjacent to,
not just against the panel ground. A future palette maintainer reading only the "1.10:1 by
design" line may incorrectly conclude the fill region is contrast-problematic without
understanding the full picture.  
**Why it matters:** Incomplete contrast annotations have caused two prior misreadings in
this codebase (panel-refresh-2026q2-e2: two annotations were off by 0.6-2.3 ratio points;
focus-ring-contrast-2026q2-e1: the PALETTE_DARK dark-headroom regression was not initially
documented). A comment that reports one pair but not the adjacent pair invites the same
mistake at the next refactor.  
**Suggested fix:** Extend the annotation to: "Fill-vs-hover: ~1.10:1 by design (state
carried by border). FOCUS_RING border vs BG_TOGGLE_CHECKED fill: 3.17:1 (light) / 4.55:1
(dark) -- above 3:1 floor, documents that the active indicator reads against its own
interior fill." No code change required; annotation-only.

---

## LOW

### LOW-1 — 1px content-shift jitter when toggling from unchecked to checked

**Where:** `styles.py:504-522` (all four pseudo-state rules for `display-toggle`)  
**Evidence:** The unchecked state has `border: 1px solid transparent` and the checked
state has `border: 2px solid {FOCUS_RING}`. Qt's QPushButton box model adds border width
outside the content box. When the border width increases from 1px to 2px, the button
either grows by 2px (if layout is non-fixed) or the content+padding area shrinks by 1px
on each side (if the layout allocates a fixed size). In either case, the icon and text
shift ~1px relative to the panel when the user clicks the toggle. This is the classic
border-width-change jitter pattern.  
**Why it matters:** The jitter is subtle (1px) but visible on Retina/HiDPI displays where
users are sensitive to micro-alignment. It is most noticeable when rapidly clicking
Wireframe on/off.  
**Suggested fix:** Compensate padding in the checked rule to maintain constant content
position: `checked: padding: 2px 7px` (1px less on each side, offsetting the 1px border
growth). Or alternatively, use `outline: 2px solid {FOCUS_RING}` instead of changing
`border-width`, since `outline` renders outside the box model and does not shift content.
The `outline` approach matches the existing `QAbstractButton:focus` rule's mechanism and
would give the checked state visually identical chrome to the focus ring.

---

### LOW-2 — Industry comparison: Blender 4.x separates display-mode toggles from viewport-color controls with a subgroup header; this panel merges them under one "Display" group

**Where:** `appearance_panel.py:161-203` (`_build_toggles_group`)  
**Evidence:** Blender 4.x N-panel has a "Viewport Shading" section that separates
"Wireframe" / "Solid" / "Material" mode buttons (top cluster) from color/lighting
controls (lower cluster). 3D Slicer separates display-type controls (Volume Rendering,
Surface, etc.) from color controls in distinct collapsible sections. In this panel, the
"Display" group (Wireframe + Show-edges toggles) sits between "Colors" above and
"Opacity" below. The grouping is logical but the header "Display" is generic -- a new
user cannot tell from the header alone that this group controls render style vs. color vs.
transparency.  
**Why it matters:** As the panel gains more controls (e.g. a future backface-culling
toggle exposed here, or a grid overlay), the flat list of groups will lengthen and the
distinction between "style mode" controls vs "appearance quantity" controls will blur. The
current layout is fine at current scale but is the wrong pattern to extend.  
**Suggested fix:** Consider renaming the group header from "Display" to "Render Mode" or
"Surface Style" to clarify its scope. This is a naming-only change (no layout impact) and
costs zero token budget. Blender calls the analogous section "Overlay" or "Shading" --
both more specific than "Display".

---

## What was done well

1. **Token discipline is exemplary.** `BG_TOGGLE_CHECKED` is defined in both palettes as a
   6-digit hex, documented with contrast ratios, and proven unused-token-clean by the new
   `test_bg_toggle_checked_value_appears_in_both_stylesheets` test. No AI-13 risk.

2. **The WCAG argument is architecturally correct.** Delegating the active-state WCAG
   obligation to the FOCUS_RING border (already proven at 3.56:1 / 5.17:1 in prior
   milestones) rather than the fill avoids introducing a new WCAG obligation on the fill
   token. This is the right call.

3. **Attribute-name preservation (`_wireframe_cb`, `_edges_cb`) across the widget-type
   migration** means `refresh_icons` and `apply_to_actor` required zero changes. The
   migration is surgically scoped.

4. **The `QCheckBox` import removal is clean.** The diff removes `QCheckBox` from the
   imports without leaving a dead import. The test
   `test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox` provides source-
   level regression coverage that is AI-2-compliant (grep, no QApplication needed).

5. **First-launch is unaffected.** Both toggles start `setChecked(False)` -- the unchecked
   transparent state at launch is the same as before the migration. No auto-render path
   was introduced. Section 9.3 is clean.

6. **The four-pseudo-state QSS coverage** (unchecked, :hover, :checked, :checked:hover)
   is complete. Peer implementations that omit `:checked:hover` often leave the checked
   state lost visually when the user re-hovers it; this implementation handles all four
   branches correctly.

7. **Keyboard accessibility is preserved.** `QPushButton(checkable=True)` responds to
   Spacebar by default (inherited from `QAbstractButton`). The `QAbstractButton:focus`
   outline rule already in the stylesheet applies without any new code.

---

## Recommended rectification order

1. **MEDIUM-1 (discoverability):** Add a minimal off-state border to the unchecked display-
   toggle rule. Single-line QSS change, zero test impact.
2. **MEDIUM-2 (text-align consistency):** Add `text-align: left` to the global QPushButton
   base rule (or the Colors group specifically). Single-line QSS change.
3. **MEDIUM-3 (annotation):** Extend the palette comment with the FOCUS_RING-vs-fill ratio
   pair. Documentation-only, zero code impact.
4. **LOW-1 (jitter):** Switch from `border: 2px` to `outline: 2px` for the `:checked` and
   `:checked:hover` rules to eliminate the 1px content shift. Cascades naturally with the
   existing `QAbstractButton:focus` outline mechanism.
5. **LOW-2 (naming):** Rename the "Display" group header to "Render Mode" or "Surface
   Style". One-character diff in `_build_toggles_group`.
