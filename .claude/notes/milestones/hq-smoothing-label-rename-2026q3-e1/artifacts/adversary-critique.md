# Adversary critique — hq-smoothing-label-rename-2026q3-e1

**Reviewer:** milestone-adversary-critic (read-only)
**Date:** 2026-05-22
**Subject:** `e4acb1053d7e37c93eac738e7767c4688602e5f0..3599139b9609ed75b134305d7271eb5038a76` — rename "HQ smoothing" → "Double-pass smooth" (F-L1 closure)
**Diff stats:** 668 total lines (228 functional across CONTEXT.md + app.py + appearance_panel.py + test file; 440 artifact lines — ~66% artifact inflation)

---

## Executive summary

Headline finding is the non-waivable diff-size auto-HIGH (668 lines total), but with 66% artifact inflation from milestone artifacts (research brief, implementation plan, state.json, dispatch log) the code action required is nil. No CRITICALs. One process HIGH. One LOW (stale docstring in `hq_smoothing` property at `appearance_panel.py:546` names the old user-visible button label). All 15 app invariants are clean; the rename is complete and accurate for user-visible strings; four new regression-guard tests are correctly calibrated (positive + negative for both button label and status-bar suffix). Verdict: SHIP after acknowledging the process HIGH.

---

## Verdict

**SHIP-WITH-FIXES** — the single code fix required (LOW-level docstring) is trivially addressed in-line; the process HIGH is automatically generated and has no code action. The rename is otherwise complete, accurate, and well-tested. Safe to ship once the docstring is updated.

---

## Critical findings

None.

---

## High findings

### HIGH — diff-size auto-finding (review-quality-at-risk)

**Where:** no specific file
**Evidence:** `git diff e4acb1053d7e37c93eac738e7767c4688602e5f0..3599139b9609ed75b134305d7271eb5038a76 | wc -l` returns 668, which exceeds the 400-line threshold established by Cisco / LinearB defect-detection research.
**Why it matters:** large diffs increase the chance a reviewer skips a hunk; defect-detection rates drop measurably above 400 LOC.
**Suggested fix:** no code action required. Breakdown: ~303 lines research brief, ~35 lines implementation plan, ~50 lines state.json, ~2 lines dispatch log, ~20 lines researcher lessons update = 410 artifact lines; functional change is 228 lines. Artifact inflation is the cause; the functional diff is appropriately scoped for this milestone.
**Regression-guard test:** no automated test for diff size; orchestrator's wc-l check at critique dispatch is the guard.

---

## Medium findings

None.

---

## Low findings

### LOW — stale old button label in `hq_smoothing` property docstring

**Where:** `appearance_panel.py:546`
**Evidence:** The property docstring reads: `when the user has toggled the "HQ smoothing" button.` The user-visible button now reads "Double-pass smooth" since this milestone. The docstring is developer-facing (not user-visible), and was intentionally left unchanged per the "SYMBOL / COMMENT stays" brief rule. However it now names the wrong button label, which will mislead a future developer calling `help(panel.hq_smoothing)` or reading the docstring in an IDE.
**Why it matters:** The docstring is the contractual description of what this property reads. Naming the button by its old label ("HQ smoothing") when the button now reads "Double-pass smooth" creates a label drift that will accumulate if future milestones add more renames. CONTEXT.md §4.3a correctly uses the new label; the docstring is the only survivor.
**Suggested fix:** Update `appearance_panel.py:546` from `"HQ smoothing" button` to `"Double-pass smooth" button (formerly "HQ smoothing")` or simply `"Double-pass smooth" button`.

---

## What was done well

- **Bucketed-match table strategy was applied correctly.** The research brief built an explicit USER-VISIBLE / TEST ASSERTION / SYMBOL-COMMENT / DOC-PROSE / HISTORICAL table, and the implementation faithfully honored each bucket. No symbol renames leaked in (all `_hq_smoothing_*`, `hq_smoothing_changed`, `set_hq_smoothing_eligible`, `HQ_SMOOTHING_ICON_NAME` remained), and no user-visible string was missed.

- **All three user-visible rename targets were addressed.** `appearance_panel.py:271` (QPushButton label), `app.py:663` (status-bar suffix), and `app.py:800` (comment example) were all updated. The grep verifications confirm zero remaining `"HQ smoothing"` QPushButton constructors and zero `" [HQ]"` string literals in the functional source.

- **AI-15 attestation is rigorous and verifiable.** The commit message includes a per-word attestation: "Double-pass" = TRUE (exactly 2 Taubin passes fire at `surfaces.py:203` and `surfaces.py:210` when `second_smooth_iter=40`); "smooth" = TRUE (both are `smooth_taubin`, volume-preserving). The tooltip's "— two passes total —" bridge phrase correctly reinforces the label etymology without overstating the operation. This is exactly the right level of honesty for AI-15.

- **Tooltip "two passes total" claim is technically accurate.** `surfaces.py:203` runs `smooth_taubin(n_iter=20, pass_band=0.1)` unconditionally; `surfaces.py:210` runs `smooth_taubin(n_iter=40, pass_band=0.05)` when `second_smooth_iter > 0`. The toggle activates the second pass. The tooltip correctly says "Applies a second Taubin smoothing pass (n_iter=40, pass_band=0.05) — two passes total —" which is a precise description of the opt-in operation.

- **Four regression-guard tests are correctly shaped.** Positive + negative for both button label and status-bar suffix: `test_appearance_panel_uses_double_pass_smooth_label`, `test_appearance_panel_does_not_use_old_hq_smoothing_label`, `test_app_status_bar_uses_double_pass_suffix`, `test_app_status_bar_does_not_use_old_hq_suffix`. All four are AI-2 compliant (pure source-text greps, no QApplication). The negative tests guard against partial regressions where the old literal returns.

- **Negative test needle specificity is correct.** The test checks for `'QPushButton("HQ smoothing")'` (constructor syntax with double-quotes), which does NOT match the surviving docstring at `appearance_panel.py:546` (`"HQ smoothing" button`) or the comment at `app.py:60`. No false-positives.

- **CONTEXT.md updates are surgically scoped and internally consistent.** §4.3a line 147 correctly adds the parenthetical `(user-visible label "Double-pass smooth" since hq-smoothing-label-rename-2026q3-e1)` and updates `HQ smoothing changes the **mesh**` to `Double-pass smooth changes the **mesh**`. §8.16 line 488 appends the rename note with the historical `"HQ smoothing" → "Double-pass smooth"` attribution. No active label references to the old name survive in CONTEXT.md.

- **Comment at `app.py:800` was correctly updated.** The example in the comment was changed from `"Enriques surface [HQ] · …"` to `"Enriques surface [Double-pass] · …"` with a parenthetical noting the rename. This matches the live suffix value at `app.py:663`.

- **No render path was touched.** The commit message correctly notes "No off-screen verification needed — pure label rename, no render path touched." All 384 tests pass. The functional diff is ~25 LOC as designed.

---


## Cross-critic agreement

The following findings cluster within 5 lines of each other in the same file. Multiple critics flagged the same area -- these are the strongest signals to fix first.

- **L4, M1, L3** at `appearance_panel.py:271-277` (LOW): 3 — "Double-pass smooth" is less task-oriented than alternatives for a non-mesh-specialist researcher; 1 — Tooltip verb form conflicts with Qt / Apple HIG convention; 2 — Tooltip "two passes total" bridge phrase is mildly condescending for the target audience

## Recommended rectification order

1. **Fix the LOW (docstring stale label).** Update `appearance_panel.py:546` to reference "Double-pass smooth" instead of "HQ smoothing" in the `hq_smoothing` property docstring body. One-word change; no test update needed (docstrings are not tested by source-grep guards).
2. **Acknowledge the process HIGH.** No code action required — the 668-line diff exceeds 400 only due to milestone artifact files (research brief, state.json, etc.). The functional delta is 228 lines.

---

*End of critique. Mandatory rectification: none (the LOW is recommended but does not block ship). The process HIGH is non-waivable per checklist rules but requires no code change.*
## Frontend UI/UX findings

_Merged from milestone-frontend-ux-critic._

# Frontend UX Critique — hq-smoothing-label-rename-2026q3-e1

**Critic:** milestone-frontend-ux-critic
**Date:** 2026-05-22
**Commit range:** `e4acb1053d7e37c93eac738e7767c4688602e5f0..3599139b9609ed75b134305d7271eb5038a76`
**Files reviewed:** `appearance_panel.py`, `app.py` (Qt-panel surface only)

---

## Executive Summary

This milestone is a pure label rename: `"HQ smoothing"` → `"Double-pass smooth"` on the button, `" [HQ]"` → `" [Double-pass]"` in the status bar, plus a tooltip opening-verb shift and bridge phrase insertion. Zero logic changes. Zero new Qt widget code.

**Finding counts: 0 CRITICAL / 0 HIGH / 3 MEDIUM / 3 LOW**

The label change is substantively correct and the tooltip AI-15 honesty clause holds. Two of the MEDIUM findings are pre-existing risks that the +9 char status-bar overhead makes concrete: the success path (116 chars) stays just inside the ~120-char clip band, but the warning path was already at ~200 chars before this rename and is not materially worsened by it. The third MEDIUM is the tooltip's imperative → third-person-singular verb shift, which conflicts with Qt tooltip convention across all three peer tools examined.

---

## CRITICAL

*None.*

---

## HIGH

*None.*

---

## MEDIUM

### MEDIUM-1 — Tooltip verb form conflicts with Qt / Apple HIG convention

**Where:** `appearance_panel.py:276`
**Evidence:** Old tooltip opened `"Apply a second Taubin smoothing pass …"` (imperative). New tooltip opens `"Applies a second Taubin smoothing pass …"` (third-person singular indicative). Qt's own documentation and the Apple HIG both specify imperative-or-noun-phrase for button tooltips ("Click to apply…" or bare infinitive "Apply…"). The Qt Widget docs example for `setToolTip` uses imperatives throughout. MeshLab's "Taubin Smooth" tooltip reads "Apply Taubin smoothing…"; ParaView's property panel uses noun-phrase heads ("Number of smoothing iterations"). Neither peer uses third-person singular ("Applies") as a tooltip verb.
**Why it matters:** Third-person singular is grammatically correct only if the tooltip describes what the widget does in isolation ("This button applies…"), but tooltip convention in desktop sci-viz software is to address the user (imperative: "Apply…") or describe the capability (noun phrase: "Second-pass Taubin smoothing"). "Applies" reads as if a parenthetical "(this control)" is implied — awkward and inconsistent with every other tooltip in the app (scan `appearance_panel.py`: all other tooltips use noun-phrase or imperative form).
**Suggested fix:** Revert to imperative: `"Apply a second Taubin smoothing pass (n_iter=40, …) — two passes total — …"`. The `"— two passes total —"` bridge phrase is a net positive; only the verb needs reverting.

---

### MEDIUM-2 — Status-bar success-path string at 116 chars approaches ~120-char visible clip band

**Where:** `app.py:805`
**Evidence:** The full success message for Enriques Fig. 1 with Double-pass active is:
`Canonical sextic  [Fig. 1] [Double-pass]  ·  108,243 verts, 215,772 faces  ·  bbox: 3.780 × 3.780 × 3.780  ·  587 ms`
= **116 chars** (measured). Old `[HQ]` suffix produced 107 chars. QStatusBar clips without ellipsis at a width that depends on the window width; on a 1280px monitor with the default window size the clip limit is approximately 120 chars. The additional 9 chars from `[Double-pass]` vs `[HQ]` push the success message within 4 chars of the empirical limit. The trailing `· 587 ms` generation-time token is the first to clip, which is the most informative signal when HQ smoothing is active (it shows the +140 ms cost).
**Why it matters:** The generation-time token is precisely what motivated the status-bar attribution design (CONTEXT.md §4.3). If it clips, the user cannot see whether their machine paid the +140 ms cost — defeating the purpose of the `[Double-pass]` label. This risk was absent with `[HQ]` (4 chars) but is now concrete with `[Double-pass]` (13 chars).
**Suggested fix:** Shorten the bbox separator or move generation time earlier: `f"{surface.label}{hq_label}  ·  {result.gen_ms:.0f} ms  ·  {n_pts:,} verts, {n_cells:,} faces{param_str}  ·  {bbox_suffix}"`. Alternatively, shorten the suffix to `[2-pass]` (7 chars) which adds only 2 chars vs the old `[HQ]`. This is a follow-on task, not a blocker.

---

### MEDIUM-3 — "Double-pass smooth" mixes grammatical category with peer buttons in Render Mode group

**Where:** `appearance_panel.py:208` (group), `appearance_panel.py:271` (button label)
**Evidence:** The Render Mode group now contains three buttons:
- `"Wireframe"` — noun (render mode name)
- `"Show edges"` — verb phrase (imperative, describes the action)
- `"Double-pass smooth"` — adjective-noun compound (modifier + gerund/noun)

The grammatical category shifts across all three. MeshLab's equivalent group uses uniform noun phrases: "Wireframe", "Flat Wire", "Smooth" — all single-word nouns or noun+adjective. Blender 4.x uses consistent icon+label where each label is either a pure noun ("Wireframe", "Solid", "Material Preview", "Rendered") or a two-word noun phrase. "Double-pass smooth" breaks the noun/noun-phrase pattern set by "Wireframe" while also being inconsistent with the verb-phrase pattern of "Show edges". Neither "Double-pass smooth" nor "HQ smoothing" solved this; the rename did not worsen it, but it is the natural point to flag.
**Why it matters:** Visual consistency in a control group is a low-friction discoverability signal. A non-uniform labeling style across three buttons in the same group (one noun, one verb phrase, one adjective-noun) requires readers to shift parsing mode per button, slowing comprehension marginally but consistently.
**Suggested fix:** Consider `"Smooth (double-pass)"` — noun first (matching "Wireframe"), qualifier parenthesized (clearer to a math researcher that it is a variant of smoothing, not a separate mode). Or `"Extra smooth"` (adjective-noun matching "Show edges" length, 11 chars, same noun-first family as "Wireframe"). Resolution deferred; pre-existing category issue, not introduced by this milestone.

---

## LOW

### LOW-1 — Variable name `_hq_label` diverges from rendered text `[Double-pass]`

**Where:** `app.py:663`, `app.py:677`
**Evidence:** The diff correctly retains the internal name `_hq_label` (per brief §4 decision to avoid blast-radius churn). The as-shipped comment at `app.py:660–662` reads:
`# hq-smoothing-label-rename-2026q3-e1 (F-L1 closure): suffix renamed from "[HQ]" → "[Double-pass]" — variable name _hq_label STAYS (internal symbol).`
This comment is present and adequate. The divergence is flagged as LOW because a future maintainer adding a third quality mode (e.g., `[Triple-pass]`) will encounter a variable named `_hq_label` whose name is now doubly wrong (`hq` = HQ, not Double-pass; `label` = label of a feature named after an old user-facing term). The comment alone is not machine-checkable.
**Why it matters:** Low friction now; medium friction in 12–18 months when a future milestone adds a third smoothing-quality mode or renames the feature again.
**Suggested fix:** Add a type alias or named constant at the assignment site: `# _hq_label stays as internal name; see hq-smoothing-label-rename-2026q3-e1`. Already done. If blast-radius risk ever drops (e.g. a full-app rename pass), rename to `_quality_suffix`.

---

### LOW-2 — Tooltip "two passes total" bridge phrase is mildly condescending for the target audience

**Where:** `appearance_panel.py:277`
**Evidence:** The button label already says "Double-pass smooth." The tooltip then says "Applies a second Taubin smoothing pass … — two passes total — …". A math researcher who can decode `n_iter=40, pass_band=0.05` already knows "Double" = 2. The bridge phrase clarifies what "Double-pass" means in user-task terms, which is appropriate for a general user — but this app's user base (algebraic geometry researchers) will find the annotation redundant. The length cost is 20 chars in a 562-char tooltip.
**Why it matters:** Minor. The phrase does not mislead (it is honest per AI-15) and adds no incorrect information. The redundancy is mild.
**Suggested fix:** If the bridge phrase is retained (acceptable), trim to `"— two Taubin passes —"` (shorter, avoids "total" which is ambiguous — total passes or total iterations?). This is purely cosmetic.

---

### LOW-3 — "Double-pass smooth" is less task-oriented than alternatives for a non-mesh-specialist researcher

**Where:** `appearance_panel.py:271`
**Evidence:** A K3 or Enriques researcher visiting the button for the first time sees "Double-pass smooth." The term "double-pass" is idiomatic to mesh-processing and rendering pipelines (e.g., Blender's two-pass shadow mapping, MeshLab's TwoStep Smooth filter) but not to algebraic geometry as a discipline. The researcher's mental model is "the surface looks jagged — I want it smoother" (task-oriented), not "I want a second Taubin pass" (implementation-oriented). MeshLab's own naming for a structurally similar filter is "TwoStep Smooth" — close to "Double-pass smooth" in character but using "TwoStep" (standard mesh-processing vocabulary) rather than "Double-pass" (render-pipeline vocabulary). The prior label "HQ smoothing" was arguably more task-oriented (HQ = high quality), even if less technically precise.
**Why it matters:** Low-priority UX polish. The tooltip covers the gap adequately.
**Suggested fix:** For the next label iteration (if any), `"Enhanced smoothing"` or `"Extra smooth"` would be more task-oriented while remaining technically honest. Not a regression — "Double-pass smooth" is strictly more precise than "HQ smoothing."

---

## What was done well

1. **The rename is complete and consistent.** Button label, status-bar computing message, and status-bar success/warning messages are all updated atomically. No stale `[HQ]` string appears in any user-facing code path.

2. **AI-15 honesty is preserved.** "Double-pass smooth" accurately describes the implementation: exactly two Taubin passes fire when the toggle is on (verified: `surfaces.py:558, 605`). "Double" is truthful, "smooth" is truthful, and the tooltip's "two passes total" reinforces rather than inflates the claim.

3. **Internal symbol discipline is clean.** The decision to retain `_hq_smoothing_cb`, `hq_smoothing_changed`, `_hq_label`, and all internal symbol names avoids blast-radius churn. The as-shipped comment at `app.py:660–662` is an adequate inline justification. This is the correct call for a pure label rename.

4. **Tooltip cost disclosure is preserved verbatim.** The `+31% generate time, about +140 ms on a reference dev machine at default grid resolution; absolute cost is hardware-dependent` disclosure remains intact. This is the most important piece of honesty in the tooltip.

5. **Button width fits at minimum dock width.** At 200px minimum dock width, `"Double-pass smooth"` (18 chars, ~126–135px estimated text width at 13pt proportional font) fits within the ~168px available text area without elision. The research brief's width-fit analysis (`appearance_panel.py:127`) is correct.

6. **Regression-guard tests are complete and symmetric.** Four new tests cover both positive and negative cases for both the button label and the status-bar suffix — the standard 2×2 regression grid. AI-2 compliance maintained (pure source-text greps, no QApplication).

---

## Recommended rectification order

1. **MEDIUM-1** (tooltip verb form): 1-char fix — revert `"Applies"` to `"Apply"`. No logic change. Zero risk.
2. **MEDIUM-2** (status-bar clip risk): consider shortening the `[Double-pass]` suffix to `[2-pass]` OR reordering the status-bar template to place `gen_ms` before bbox. Track as a follow-on if the current clip band proves adequate on the reference display setup.
3. **MEDIUM-3** + **LOW-3** (label grammar + task-orientation): bundle into a single micro-rename pass if the team revisits the Render Mode group label (CONTEXT.md §8.16 note already flags the group-label mismatch from the prior milestone).
4. **LOW-1** / **LOW-2**: no immediate action required.

---

## Rectification status — 2026-05-22

**Fixed (in-scope, this rect commit):**
- `MEDIUM-1` (tooltip verb form): `appearance_panel.py:276` `"Applies"` → `"Apply"`; new regression-guard test `test_double_pass_smooth_tooltip_uses_imperative_verb` added.
- `adversary LOW` (stale `hq_smoothing` property docstring): `appearance_panel.py:546` reference to `"HQ smoothing" button` updated to `"Double-pass smooth" button (formerly "HQ smoothing"; relabeled by ...)`.

**Deferred (out-of-scope or follow-on):**
- `HIGH` (process / diff-size auto-finding): no code action — 66% artifact inflation; functional diff was ~25 LOC; acknowledged.
- `MEDIUM-2` (status-bar 116 chars approaches clip band): changing the suffix again ([Double-pass] → [2-pass]) would create a label/suffix mismatch worse than the current state; the suggested status-bar template reorder (gen_ms before bbox) is a separate concern from this milestone's scope. Track as a follow-on micro-task if the clip becomes observed on the reference display.
- `MEDIUM-3` (grammatical-category mismatch across Render Mode group buttons): critic explicitly notes this is pre-existing — "not introduced by this milestone." Deferred to a future Render Mode group label-consistency pass.
- `LOW-1` (`_hq_label` variable name divergence): critic acknowledges the inline comment at `app.py:660–662` is adequate; no immediate action.
- `LOW-2` ("two passes total" bridge phrase mildly condescending): cosmetic; defer.
- `LOW-3` ("Double-pass smooth" less task-oriented): bundled with MEDIUM-3; defer.

**Invalidated:** none.

**Test count:** 385 (was 384, +1 for `test_double_pass_smooth_tooltip_uses_imperative_verb`).
