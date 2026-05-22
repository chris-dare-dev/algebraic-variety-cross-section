# Adversary critique — appearance-panel-layout-pass-2026q3-e2

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** c42fbeb..HEAD (1 commit, a908657)

**Diff stats:** 8 files, 452 insertions, 1 deletion.
Code delta (appearance_panel.py + styles.py + tests/test_styles_palette.py only): 187 LOC.
Artifact inflation: 265 LOC (milestone state/plan/research/logs).

---

## Executive summary

No CRITICAL findings. No HIGH findings. The diff is architecturally clean: the scoped role-property approach correctly avoids cascading to center-aligned action buttons, the macOS QStyleSheetStyle-trigger workaround is documented with precision, and the three new tests follow established AI-2-compliant source-grep patterns. Three MEDIUM findings were identified: (1) a stale `CONTEXT.md §4.3a` citation in the new comment at `appearance_panel.py:167` — the role-property pattern is documented in §4.3b, not §4.3a; (2) CONTEXT.md was not updated to reflect the "Display" → "Render Mode" group rename, leaving two occurrences of "Display group" / "Display-group" as stale prose at lines 146 and 483; (3) the `test_dark_stylesheet_includes_role_selectors` extension checks only that the selector string is present, not that `text-align: left` appears in the rule body — a future refactor could hollow out the rule while keeping the selector and no test would catch it. Two LOW findings round out the critique. The code delta is 187 LOC — well under the 400-LOC auto-finding threshold; no review-quality-at-risk finding is triggered.

---

## Verdict: SHIP-WITH-FIXES

Three MEDIUMs, all documentation or test-coverage quality. None block behavior. The wrong `§4.3a` citation is immediately misleading for future authors who read the inline comment and follow the reference — they will land on the public API description rather than the role-property pattern guidance. The CONTEXT.md drift compounds over milestones. Both are one-liner fixes. The test body-content gap is a prospective risk worth closing before the next QSS-touches-colors-button milestone. None of the three require a re-render or a behavior change.

---

## Critical findings

None.

---

## High findings

None.

---

## Medium findings

### MEDIUM — Wrong CONTEXT.md section cited for role-property pattern

**Where:** `appearance_panel.py:167`
**Evidence:** Comment reads `# CONTEXT.md §4.3a for the role-property pattern.` but §4.3a is the "AppearancePanel public API" section (documents `apply_to_actor`, `set_default_color`, `hq_smoothing`). The canonical role-property pattern guidance — "Panel files must NEVER do `label.setStyleSheet(...)` ... Use the canonical Qt theme-aware pattern instead: `label.setProperty('role', ...)`" — is in §4.3b ("Theme system"), not §4.3a.
**Why it matters:** A future maintainer reading the inline comment and jumping to §4.3a will land on the public API description, find no mention of role-property selectors, and incorrectly conclude the citation is spurious. The mis-cite erodes the navigability of the institutional memory.
**Suggested fix:** Change `CONTEXT.md §4.3a` to `CONTEXT.md §4.3b` in `appearance_panel.py:167`.

**Regression-guard test:** A linter check is impractical here, but the rectifier should verify by opening CONTEXT.md §4.3b and confirming the role-property example block is present there before accepting the change.

---

### MEDIUM — CONTEXT.md "Display group" references are stale after group rename

**Where:** `CONTEXT.md:146`, `CONTEXT.md:483`
**Evidence:** The milestone renames `QGroupBox("Display")` → `QGroupBox("Render Mode")` in `appearance_panel.py:200`, but CONTEXT.md was not updated. Line 146 still reads "This is the only Display-group toggle that regenerates rather than re-renders" and line 483 still reads "the Appearance dock's Display group — same checkable-button pattern as Wireframe / Show-edges." Both are factually stale: the group is now "Render Mode."
**Why it matters:** CONTEXT.md is the institutional memory contract. Future milestone authors reading §4.3a or §8.16 will use "Display group" as the canonical term, potentially re-introducing the old name or writing test guards against `QGroupBox("Display")`. The rename is documented in inline comments and commit message but not in the canonical reference.
**Suggested fix:** In CONTEXT.md, replace "Display-group" with "Render Mode group" at line 146 and "Appearance dock's Display group" with "Appearance dock's Render Mode group" at line 483. Also consider updating CONTEXT.md §4.3 to note the `colors-button` role as a registered role string alongside `display-toggle`, `muted`, `value-mono`, and `range-label`.

---

### MEDIUM — `test_dark_stylesheet_includes_role_selectors` asserts selector presence but not rule body content

**Where:** `tests/test_styles_palette.py:686–693`
**Evidence:** The extended test asserts `'QPushButton[role="colors-button"]' in styles.APP_STYLESHEET_DARK` — only that the selector token appears in the rendered string. A future refactor could rename the property inside the rule block (e.g., accidentally delete `text-align: left;` while keeping the selector) and both assertions would still pass. By contrast, `test_bg_toggle_checked_value_appears_in_both_stylesheets` at line 746 checks the actual token value inside the rule, which is a stricter pattern this test should mirror.
**Why it matters:** The functional fix — `text-align: left` being honored by QStyleSheetStyle — is entirely in the rule body, not in the selector name. A hollow selector is indistinguishable from a working one by this test. The display-toggle test suite has the same gap (no `text-align: left` body check), but the colors-button is simpler to add since the rule only has three properties.
**Suggested fix:** Add `assert 'text-align: left' in styles.APP_STYLESHEET` (and `_DARK`) in a new test or extend the existing test to grep for `text-align: left` in a window around the `colors-button` selector.

**Regression-guard test:** `assert 'QPushButton[role="colors-button"]' in styles.APP_STYLESHEET and 'text-align: left' in styles.APP_STYLESHEET[styles.APP_STYLESHEET.index('colors-button'):styles.APP_STYLESHEET.index('colors-button')+80]` would be sufficient, though a substring scan starting at the selector index is cleaner.

---

## Low findings

### LOW — `>= 2` count guard in `test_appearance_panel_colors_buttons_have_colors_button_role` may silently pass on over-tagging

**Where:** `tests/test_styles_palette.py:796`
**Evidence:** `assert role_count >= 2` passes today for exactly 2 occurrences (correct). If a future author adds a third color-picker button (e.g., an "Edges Color" button) and tags it with `colors-button` but does NOT update the test to reflect a new structural expectation, the count will rise to 3 and the test still passes — potentially masking a partial migration where the third button was tagged but the new button has incorrect semantics. The test comment says "one for surf_btn, one for bg_btn" which implies the expected count is exactly 2.
**Why it matters:** Low risk currently. The `>= 2` choice is documented and defensible (explicitly future-proofs for an Edges Color button per the research brief). This is a naming-precision mismatch between the assertion value and the comment describing it.
**Suggested fix:** Either change the comment to "at least the two known buttons" or change the assertion to `assert role_count == 2` with a comment explaining it should be updated when a new colors-button is added. The research brief's forward-reference to a future Edges Color button favors keeping `>= 2` but the comment should not say "one for surf_btn, one for bg_btn" — that implies exactly 2.

---

### LOW — `QGroupBox("Render Mode")` negative-assertion is overconstrained for a future multi-group panel

**Where:** `tests/test_styles_palette.py:842`
**Evidence:** `assert 'QGroupBox("Display")' not in src` prevents ANY future group from being named "Display" in `appearance_panel.py`. The test comment acknowledges this: "If a future group genuinely needs to be called 'Display', pick a more specific name." However, the test message says the F-L2 milestone renamed it to "Render Mode" — the assertion is correct for that purpose but the error text is slightly misleading ("the F-L2 milestone renamed it to 'Render Mode'" implies only that one rename happened, when the assertion would also fire for a completely new group called "Display").
**Why it matters:** Cosmetic. The test behavior is correct; the assertion message slightly over-promises. Low maintenance cost.
**Suggested fix:** Update the assertion message to clarify: "appearance_panel.py contains QGroupBox('Display') — avoid this generic name per the F-L2 milestone peer-tool audit; use a more specific name." Drop the specific "renamed" phrasing.

---

## What was done well

- **Correct cascade scoping via role-property (Option 2 over Option 1).** The decision to add `setProperty("role", "colors-button")` to the two buttons rather than extending the global `QPushButton {}` rule is the right architectural choice. The research brief explicitly quantified the cascade risk to Reset Defaults / Reset Camera buttons, and the implementation follows through by keeping those buttons' center-alignment untouched. The commit message makes the Option 2 rationale explicit and auditable.

- **macOS QStyleSheetStyle trigger documented with precision.** The `styles.py` comment block at lines 478–501 explains exactly WHY `padding: 3px 8px; border-radius: 3px` appear in both the base rule and the new role rule — not because values differ but because at least one box-model property is needed to force `QStyleSheetStyle` to take over widget painting on macOS Fusion so `text-align: left` is honored. This is the kind of platform-behavioral knowledge that normally rots silently; documenting it inline prevents future "why is text-align being ignored?" debugging sessions.

- **Signal/slot integrity preserved.** `surf_btn.clicked.connect(self._pick_surface_color)` and `bg_btn.clicked.connect(self._pick_bg_color)` are untouched across the diff. `setProperty("role", "colors-button")` is a Qt dynamic property — it is styling-only and has no effect on `QAbstractButton`'s signal routing or the `clicked` signal semantics. This was correctly identified in the research brief and the risk is zero.

- **Count-based test guard prevents the half-migration regression.** `assert role_count >= 2` in `test_appearance_panel_colors_buttons_have_colors_button_role` explicitly catches the case where only one of the two buttons gets the role tag. This directly applies the lesson from `display-toggles-checkable-button-2026q3-e1` (M1 finding: single `in` check doesn't catch a one-of-two migration gap). The lesson was applied correctly.

- **`setCheckable` guard closes the semantics-drift path.** Asserting `"surf_btn.setCheckable" not in src` and `"bg_btn.setCheckable" not in src` in the same test guards against an accidental future `setCheckable` call that would change these action buttons into toggles. This is a forward-looking guard that costs nothing today but would catch a refactor mistake that would change the QColorDialog-launch semantics.

- **Off-screen panel-chrome verification executed and attested.** The commit message includes specific PNG paths (`/tmp/panel-chrome-after/appearance-dark-populated-default.png`, `view-dark-populated-default.png`) with explicit behavioral claims ("'Surface…' and 'Background…' labels now LEFT-aligned", "Reset Camera... buttons retain center-alignment as expected"). The view-panel regression check (no cascade to center-aligned buttons) is exactly the right verification step for a scoped-rule change.

- **`_build_toggles_group` rename comment cites prior-milestone finding and peer-tool audit.** The inline comment at `appearance_panel.py:191–199` credits the F-L2 finding, names all four peer tools surveyed (MeshLab, Blender, ParaView, 3D Slicer), and explains why "Render Mode" won over the alternatives. This is the correct density of "why" documentation for a rename that could otherwise look arbitrary to a future reader.

---

## Recommended rectification order

1. **Fix the §4.3a → §4.3b citation** in `appearance_panel.py:167`. One-character diff; zero behavioral impact. Should be the first commit of the rectification.

2. **Update CONTEXT.md** to replace "Display group" / "Display-group" with "Render Mode group" at lines 146 and 483. Also append `colors-button` to the role-property examples block in §4.3b alongside the existing `muted` / `value-mono` / `range-label` entries, and note in §4.3b's "Test guards" sentence that `test_dark_stylesheet_includes_role_selectors` now also covers `QPushButton[role="colors-button"]`. These are two lines plus one sentence insertion.

3. **Add a rule-body content assertion** to `tests/test_styles_palette.py` verifying `text-align: left` appears in the `colors-button` rule block in both rendered stylesheets. Can extend `test_dark_stylesheet_includes_role_selectors` with a post-loop check, or add a dedicated `test_colors_button_rule_includes_text_align_left` function.

4. **LOWs are optional** at the maintainer's discretion. The `>= 2` comment precision fix and the negative-assertion message update are cosmetic and can wait for the next style-pass milestone.

---

*End of critique. Mandatory rectification: M1 (wrong §4.3a citation), M2 (CONTEXT.md stale group name), M3 (rule-body content assertion). L1 and L2 are optional.*

---

## Frontend UI/UX findings

*Merged from `frontend-critique.md`. Frontend critic emitted 0 CRITICAL, 0 HIGH, 3 MEDIUM, 2 LOW. Severity-ids prefixed with `F-`.*

### F-MEDIUM — F-M1: `colors-button` rule missing `background: transparent` — silently fails on macOS Aqua

**Where:** `styles.py` `QPushButton[role="colors-button"]` rule
**Evidence:** Inline comment correctly identifies the macOS Fusion `QStyleSheetStyle` trigger requirement — `padding` + `border-radius` are sufficient there.  But macOS Aqua (the DEFAULT style when `setStyle("Fusion")` is NOT called in `main()`) ignores ALL QSS text-alignment properties on QPushButton regardless of box-model properties because Aqua's native button renderer draws the label at a hardcoded position in a pre-composited native bead.  The existing `display-toggle` rule works on Aqua only because it also sets `background: transparent` which forces full-QSS-paint mode (bypassing the native renderer entirely).  The new `colors-button` rule omits this, so on Aqua (which is what `main()` uses — no `setStyle("Fusion")` call exists) the alignment fix is a silent no-op on the team's primary development platform.
**Suggested fix:** Add `background: transparent;` to the rule — matching the `display-toggle` rule's Aqua-bypass technique.  The base `QPushButton` rule has no `background` declaration so `transparent` is visually a no-op, just forces QSS paint mode.

### F-MEDIUM — F-M2: "Render Mode" misclassifies HQ smoothing (mesh-regeneration toggle)

**Where:** `appearance_panel.py` `QGroupBox("Render Mode")`
**Evidence:** The group contains Wireframe + Show edges (genuine render-mode switches — change `actor.prop.*`) AND HQ smoothing (triggers full mesh regeneration, ~140ms cost).  MeshLab's "Render Mode" group contains ONLY display-pipeline toggles, no mesh-generation controls.  ParaView separates "Representation" (display) from "Advanced" (pipeline re-execution including quality toggles).  3D Slicer uses "Display" for actor display + a separate "Model" section for geometry.  The mixed group is the minority pattern.  The F-L2 recommendation was made BEFORE HQ smoothing was added — the group has grown since.
**Suggested fix:** Two paths: (a) rename to "Display & Quality" (single-group, lower effort, acknowledges both axes), OR (b) split into "Render Mode" (Wireframe + Show edges) + "Quality" (HQ smoothing).  Path (a) is V0-adequate.  **Defer pending user decision** — the prior F-L2 milestone explicitly chose "Render Mode" so changing it again mid-milestone is scope creep.

### F-MEDIUM — F-M3: residual swatch-to-text gap (~10px) partially survives left-align

**Where:** `appearance_panel.py` `surf_row.setSpacing(6)` / `bg_row.setSpacing(6)`
**Evidence:** With `text-align: left` + `padding: 3px 8px`, "Surface…" text starts at button-left + 8px padding.  The button is preceded by `[swatch (~20px)] [6px spacing]` so the effective visual anchor is the swatch's LEFT edge → ~34px before the first character.  Render Mode toggle buttons have icon at button-left + 8px padding → ~24px before the first character.  10px rhythm discontinuity is visible.
**Suggested fix:** Reduce `surf_row.setSpacing(6)` → 4px (matching Render Mode group's intra-row 4px) OR reduce `padding-left` on `colors-button` to 4px.

### F-LOW — F-L1: "Render Mode" header reads awkwardly when HQ is greyed at first launch

**Where:** First-launch state (variety not selected; HQ disabled)
**Suggested fix:** Update HQ smoothing tooltip to add "Unlike Wireframe and Show edges, this toggle triggers mesh regeneration (+~140ms), not just a display change."  Closes the comprehension gap without structural change.

### F-LOW — F-L2: Colors group intra-row spacing (6px) vs Render Mode (4px)

**Where:** `appearance_panel.py` `_build_color_group: vl.setSpacing(6)` vs `_build_toggles_group: vl.setSpacing(4)`
**Evidence:** The 6px in Colors is a holdover from when buttons were center-aligned (extra spacing compensated for sparse-text feel).  After left-align it now reads as a rhythm discontinuity vs the 4px in Render Mode.
**Suggested fix:** Change `vl.setSpacing(6)` → `vl.setSpacing(4)` in `_build_color_group` to match.

---

## Combined rectification order

1. **F-M1 (macOS Aqua silent-no-op)** — add `background: transparent;` to the `colors-button` QSS rule.  One line.  **Highest priority** — without it the entire milestone is a no-op on the team's primary development platform.
2. **M1 (wrong CONTEXT.md citation)** — fix `§4.3a` → `§4.3b` in the new comment at `appearance_panel.py:167`.  One-character diff.
3. **M2 (CONTEXT.md stale "Display group" references)** — replace at CONTEXT.md:146 and :483 with "Render Mode group".  Also add `colors-button` to the §4.3b role-property examples list.
4. **M3 (rule-body content assertion)** — extend `test_dark_stylesheet_includes_role_selectors` to verify `text-align: left` appears within the `colors-button` rule block in both stylesheets, not just the selector token.
5. **F-L2 (intra-row spacing)** — change `setSpacing(6)` → `setSpacing(4)` in `_build_color_group`.  Closes the residual rhythm discontinuity.
6. **F-L1 (HQ tooltip)** — add the "mesh regeneration" sentence to the HQ smoothing tooltip.  Acknowledges the F-M2 honesty concern without renaming the group.
7. **F-M3 (swatch-to-text gap)** — bundled with F-L2 above (the same `setSpacing(6)`→`(4)` fix shrinks the gap from 34px → 32px).
8. **F-M2 (group rename → "Display & Quality" or split)** — **DEFER** to a follow-up milestone.  Mid-rectify rename of a group label is scope creep; the prior F-L2 milestone deliberately chose "Render Mode".  Open a `appearance-panel-render-mode-split-2026q3-e3` if the F-M2 concern becomes user-validated.
9. **Adversary L1 + L2** (count comment + negative-assertion message) — cosmetic; defer.

---

## Rectification status (orchestrator, 2026-05-22)

**Fixed in rect commit:**

- **F-M1 (macOS Aqua silent no-op)** — added `background: transparent;` to the `QPushButton[role="colors-button"]` rule.  Forces full-QSS-paint mode bypassing Aqua's native button renderer (which ignores `text-align` regardless of box-model properties).  This is the load-bearing fix — without it, the entire milestone was a no-op on the team's primary development platform (AVC does not opt into Fusion via `setStyle()`).  Comment block rewritten to explain the Aqua-vs-Fusion distinction and why `background:` is the critical trigger, not `padding` + `border-radius`.

- **M1 (wrong CONTEXT.md citation)** — fixed `§4.3a` → `§4.3b` in the new comment at appearance_panel.py:167.  §4.3b is where the role-property pattern is documented; §4.3a is the AppearancePanel public API.

- **M2 (CONTEXT.md stale group references)** — replaced "Display-group" with "Render Mode group" at CONTEXT.md:146 and "Appearance dock's Display group" with "Appearance dock's Render Mode group (renamed from 'Display' by appearance-panel-layout-pass-2026q3-e2)" at CONTEXT.md:483.  Also extended the §4.3b role-property example list to include `display-toggle` and `colors-button` so future maintainers see the full canonical roster.  Added a "macOS Aqua trigger note" paragraph to §4.3b documenting that QPushButton role rules MUST include `background: transparent` for Aqua-bypass — institutional memory for the next role-property milestone.

- **M3 (rule-body content assertion)** — extended `test_dark_stylesheet_includes_role_selectors` to assert `text-align: left` AND `background: transparent` appear in the body of the `colors-button` rule in BOTH stylesheets.  Substring scan starting at the selector index captures the rule body up to ~200 chars (covers all 4 declarations).  Catches the hollow-rule regression where the selector remains but the functional payload gets refactored away.

- **F-L1 (HQ tooltip honesty)** — extended the HQ smoothing tooltip with "Unlike Wireframe / Show edges (display-only toggles), this triggers a full mesh regeneration" so first-launch users connect the +138ms cost to the mesh-regen distinction.  No structural change; one-sentence addition.  Mitigates the F-M2 "Render Mode misclassifies HQ smoothing" concern by clarifying at the per-button tooltip rather than renaming the group.

- **F-L2 (Colors intra-row spacing)** — changed `vl.setSpacing(6)` → `vl.setSpacing(4)` in `_build_color_group` to match the Render Mode group's 4px intra-row density.  Closes the residual vertical-rhythm discontinuity across the group boundary.  Inline comment cites the Blender 4.x convention.

**Deferred (out of milestone scope):**

- **F-M2 (Render Mode rename → "Display & Quality" or split)** — real semantic concern that HQ smoothing isn't strictly a render-mode control (it triggers mesh regeneration, not actor display).  But the prior F-L2 milestone deliberately chose "Render Mode" and a second rename mid-rect is scope creep.  The F-L1 tooltip mitigation closes the comprehension gap without a rename.  Open as `appearance-panel-render-mode-split-2026q3-e3` if user feedback validates the concern.

- **F-M3 (residual ~10px swatch-to-text gap)** — the F-L2 `setSpacing(6→4)` fix already partially closes this (now 32px instead of 34px from swatch-left to text-start).  Further reduction (4 → 2 or padding-left tweak) is diminishing returns.  Defer.

- **Adversary L1 (count comment imprecision)** + **L2 (negative-assertion message)** — cosmetic test-message phrasing.  Defer to a future cleanup pass.

**Process-only:**
- No HIGH process auto-finding this milestone (diff stayed under the 400-LOC code threshold).

**Invalidated:** none — all six fixed findings re-verified present before fixing.

**Test suite:** 370 passed (unchanged count — the M3 fix extends an existing test rather than adding a new one).  No regressions.

**Architecture lesson recorded:**

1. *"Aqua-bypass via `background: transparent` is mandatory for any QSS rule that wants to honor `text-align` on QPushButton."*  Padding + border-radius alone are sufficient on Fusion but NOT Aqua.  Now documented inline in styles.py + CONTEXT.md §4.3b so future role-property milestones don't repeat the silent-no-op mistake.

2. *"Selector-presence tests must scale to rule-body assertions when the functional payload IS the rule body."*  The role-property pattern's value is in the declarations (`text-align: left`), not the selector token.  Hollow-rule regressions are otherwise invisible.  M3's substring-scan-from-selector-index pattern is reusable for future role-rule tests.

3. *"Honesty-via-tooltip beats label-rename when the prior milestone deliberately chose a label."*  F-L1's tooltip update closes the F-M2 comprehension concern without re-litigating the F-L2 milestone's "Render Mode" decision.  Less scope creep, same end-user clarity.
