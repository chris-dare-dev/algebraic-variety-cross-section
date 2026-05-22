# Adversary critique — Focus Ring Contrast Fix

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** `focus-ring-contrast-2026q2-e1` · `17f7d527..HEAD` (1 commit)

---

## Executive summary

No CRITICALs. No code-path HIGHs. One automatic HIGH (diff-size auto-finding: 466 LOC, though ~417 lines are milestone artifacts and only ~49 are code). One MEDIUM (CONTEXT.md §8 missing an 8.14 entry documenting the WCAG 1.4.11 FOCUS_RING fix as a caught-and-fixed bug — the fix is load-bearing institutional memory). One LOW (AI-12 entry in `app-invariants.md` does not mention the FOCUS_RING non-text 3:1 floor, leaving it text-centric only).

All contrast ratio claims independently verified: `#3c82c4` vs `#f0f0f0` = 3.5558:1 (commit claims 3.556 — consistent), vs `#252526` = 3.7792:1 (commit claims 3.779 — consistent). Both clear the WCAG 2.1 §1.4.11 non-text 3:1 floor. The old value `#5b9bd5` independently confirmed at 2.5975:1 on light (fail). The dark twin test (`test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark`) margin for FOCUS_RING decreases from 5.17:1 to 3.78:1 — still ≥3.0, still passes. Full suite: 296 passed.

**Safe to merge.** The HIGH is not code-actionable (artifact inflation pattern). The MEDIUM is a documentation gap that does not block functionality. Fix the MEDIUM before milestone close.

---

## Critical findings (must-fix before this can ship)

None.

---

## High findings (should-fix this iteration)

### HIGH — Diff size exceeds 400-LOC review-quality threshold

**Where:** no specific file (cross-cutting)
**Evidence:** `git diff 17f7d527..HEAD | wc -l` = 466. Per Cisco / LinearB defect-detection research, diffs above 400 LOC place review quality at risk. The 466-LOC total breaks down as: `styles.py` ~14 insertions (code), `tests/test_styles_palette.py` ~35 insertions (code), ~268 lines research brief, ~50 lines plan, ~50 lines state.json/dispatch, ~7 lines researcher lessons. Code delta is ~49 LOC; artifact content accounts for ~417 LOC (≥89% of the diff).
**Why it matters:** The auto-finding is non-waivable per checklist policy, even when the inflation source is documentation artifacts. Reviewers scanning the full diff need to distinguish code from artifacts.
**Suggested fix:** No code action required. The finding is satisfied by noting the artifact breakdown explicitly. A future process improvement could separate milestone-artifact commits from code commits so the code diff stays under 400 LOC.

**Regression-guard test:** N/A — process finding only; no code regression is possible here.

---

## Medium findings (nice-to-fix)

### MEDIUM — CONTEXT.md §8 missing 8.14 entry for the WCAG 1.4.11 FOCUS_RING fix

**Where:** `CONTEXT.md` (no line — the entry is absent, not malformed)
**Evidence:** CONTEXT.md §8 "Bugs caught and fixed" has entries 8.1–8.13. The FOCUS_RING 2.60:1 → 3.56:1 fix closes a real, documented WCAG 1.4.11 violation that was deferred from `panel-refresh-2026q2-e2`. There is no §8.14 entry recording the pattern: "FOCUS_RING `#5b9bd5` measured 2.60:1 on `BG_PANEL` — below the non-text 3:1 floor; darkened to `#3c82c4` (3.56:1 light / 3.78:1 dark)." The §8 section is the institutional memory read by future agents; a caught-and-fixed WCAG violation belongs there.
**Why it matters:** Without a §8 entry, the next agent auditing `styles.py` for AI-12 compliance cannot distinguish "this value was chosen for aesthetics" from "this value was chosen to clear a specific WCAG floor after the prior value failed." The deferred-finding provenance is currently only in the comment block at `styles.py:83-90` and the commit message — both require reading source history; §8 is the canonical summary.
**Suggested fix:** Add a §8.14 entry in `CONTEXT.md` documenting the FOCUS_RING WCAG 1.4.11 fix pattern: the old value, the measured ratio, the fix, and the test guard added. Mirror the §8.3 short-hex pattern (one paragraph, citable).

---

## Low findings (cosmetic / future iteration)

### LOW — AI-12 in `app-invariants.md` covers text contrast only; non-text 3:1 floor for focus indicators not mentioned

**Where:** `.claude/references/app-invariants.md:132-134`
**Evidence:** The AI-12 entry reads: "Aim for ≥4.5:1 on body text, ≥3:1 on large text per WCAG 2.1 AA." It does not mention the WCAG 2.1 §1.4.11 non-text UI component floor (focus rings, active controls: ≥3:1). This milestone's finding was exactly in the non-text category — a future agent reading AI-12 as "text only" would not flag FOCUS_RING as AI-12-relevant.
**Why it matters:** The Challenger and adversary-critic both walk AI-1..AI-15 using `app-invariants.md` as the canonical checklist. Omitting the non-text 3:1 floor means future focus-ring or border-token regressions could slip past the Challenger's AI-12 check.
**Suggested fix:** Append a sentence to the AI-12 implication: "Non-text UI components (focus rings, component boundaries per WCAG 2.1 §1.4.11) require ≥3:1 against the adjacent panel background."

---

## What was done well

- **Accurate dual-background arithmetic before committing.** The milestone correctly identified that `#3c82c4` clears 3:1 on BOTH `#f0f0f0` (light, 3.56:1) and `#252526` (dark, 3.78:1) simultaneously, avoiding the need for a per-theme palette split. The arithmetic was independently verified to ≤0.001 precision.

- **Symmetric test design with deliberate scope constraint.** `test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel` is FOCUS_RING-only by design — the docstring explicitly explains why the four structural border tokens (`BORDER_GROUP_BOX`, `BORDER_DOCK_HEADER`, `BORDER_CAMERA_BTN`, `BORDER_RESET_BTN`) are excluded from the light assertion set. A 1:1 copy of the dark twin would have produced a false-positive regression since those tokens are ~1.1–1.4:1 on `#f0f0f0`. The exclusion rationale is documented in the test docstring, not just in a commit message.

- **Preserved PALETTE_DARK structural-contrast comment integrity.** The dark comment block at `styles.py:224-230` was updated to explain both the new value AND the history (prior value, prior margin, why the single-shared-value strategy was chosen). Future maintainers reading just the dark block get the full picture without needing to cross-reference the light block.

- **AI-2 compliance in the new test.** `test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel` (lines 440–472) imports only `styles` and uses the module-level `_ratio` helper — no Qt, no `QApplication`, no `PySide6` at test-module scope. The Qt imports elsewhere in the file are deferred inside function bodies and do not affect this test's runtime.

- **Single-shared-value strategy preserves key-identical palette discipline.** The `dark-mode-2026q2-e1` milestone established the key-identical pattern; this fix honored it by choosing a value that satisfies both themes rather than splitting `FOCUS_RING` into per-theme values. `test_palette_dark_has_minimum_tokens` would have caught a key-split immediately.

- **Dark-twin test margin explicitly noted in commit message.** The commit message calls out that the FOCUS_RING dark margin decreases from 5.17:1 to 3.78:1 — still ≥3.0, still passes — and states that `test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark` continues to pass. This proactively surfaces the only potential regression concern and resolves it with evidence.

- **All existing palette guards continue to pass.** `test_every_palette_value_is_six_digit_hex`, `test_app_stylesheet_dark_no_raw_hex`, and `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` all pass with the new value. The 6-digit-hex invariant (AI-13) is automatically guarded by the existing suite with no new test needed.

- **Comment rounding is consistent.** The inline token comment says "3.56:1"; the commit message says "3.556:1". The computed value is 3.5558:1. "3.556" (3 decimal places) and "3.56" (2 decimal places) are both accurate representations of the same number — no false precision.

---

## Recommended rectification order

1. **No CRITICALs or blocking HIGHs.** The HIGH auto-finding requires no code change; it is documented as artifact-inflation and requires no rectification.
2. **Fix the MEDIUM (CONTEXT.md §8.14 entry)** before milestone close. Add one paragraph to `CONTEXT.md` §8 documenting the WCAG 1.4.11 FOCUS_RING fix. This is a ~5-minute documentation edit.
3. **Address the LOW (AI-12 non-text floor) at maintainer's discretion.** Append one sentence to `app-invariants.md:134`. Can batch with the next milestone that touches `app-invariants.md`.

---

*End of critique. Mandatory rectification: none (all CRITICALs and HIGHs are non-code-actionable or absent). MEDIUM is strongly recommended before milestone close.*

---

## Frontend UI/UX findings

*Merged from `frontend-critique.md` (milestone-frontend-ux-critic). Qt-panel critic emitted 0 CRITICAL, 0 HIGH, 1 MEDIUM, 2 LOW. Severity-ids prefixed with `F-`.*

### MEDIUM — F-M1: dark-panel focus-ring contrast is a net regression (5.17:1 → 3.78:1)

**Where:** `styles.py` PALETTE_DARK FOCUS_RING block
**Evidence:** Old `#5b9bd5` measured 5.17:1 on `#252526` (72% headroom above 3:1 floor). New shared `#3c82c4` measures 3.78:1 (26% headroom). Both PASS, but the dark posture is objectively weaker — and dark is the launch default per CONTEXT.md §4.3b, so the majority of sessions experience the lower-headroom ring. The commit framed this as a neutral trade ("single shared value satisfies both themes") without acknowledging the 1.39:1 drop.
**Why it matters:** A future palette touch lightening `#3c82c4` even slightly (e.g. to `#4c8ec8`) would drop dark contrast to ~3.0:1 — boundary. The erosion is one PR away because the comment obscures it.
**Suggested fix:** Two options: (a) restore per-theme FOCUS_RING — PALETTE_LIGHT keeps `#3c82c4`, PALETTE_DARK reverts to `#5b9bd5` (recovers the 5.17:1 dark headroom; the old dark value already PASSED, the failure was light-only). (b) Keep shared value but amend the dark comment to quantify the drop. Option (a) is the architecturally cleaner fix because the dark mode milestone already established that per-theme values are appropriate when contrast demands it (see PALETTE_DARK TEXT_VALUE / TEXT_MUTED / BORDER_* all differ from light). The "key-identical palettes" pattern means same KEYS, not same VALUES.

### LOW — F-L1: light-panel margin is narrow (3.56:1, 0.556 absolute headroom)

**Where:** `styles.py` PALETTE_LIGHT FOCUS_RING inline comment
**Evidence:** 18.5% above the 3:1 floor — same narrow-pass band as macOS Sequoia `#007aff` (3.53:1) and GNOME Adwaita `#3584e4` (3.31:1) on comparable backgrounds. Not wrong; fragile. A designer reading "3.56:1 — PASS" might lighten to `#4c8ec8` (looks similar) and land at exactly 3.0:1.
**Suggested fix:** Amend inline comment to `(3.56:1 — PASS, narrow margin; do not lighten further)`.

### LOW — F-L2: test-scope deterrent is docs-only, not code-enforced

**Where:** `tests/test_styles_palette.py:440-472` docstring caveat
**Evidence:** The docstring warns "Caveat on token scope (do NOT widen this assertion set)" and explains why the four light structural border tokens are excluded. Correct and well-explained — but there's no machine-readable guard. A future maintainer copying the dark test pattern for "completeness" could widen the light tuple, see failures, and "fix" PALETTE_LIGHT structural borders — silently degrading the intentional low-contrast separators.
**Suggested fix:** Add a negative-assertion test `test_light_structural_borders_intentionally_below_3_1` that asserts the four border tokens measure < 3.0:1 on BG_PANEL_LIGHT. Makes the asymmetry between the two tests machine-readable.

---

## Combined rectification order

1. **F-M1 (MEDIUM)** — Revert PALETTE_DARK["FOCUS_RING"] to `#5b9bd5`. Recovers 5.17:1 dark headroom without compromising the light fix. Update the PALETTE_DARK comment block to record per-theme values + rationale. Architecturally consistent with dark-mode-2026q2-e1's "same keys, values may differ" pattern.
2. **M1 (MEDIUM)** — Add CONTEXT.md §8.14 entry documenting the WCAG 1.4.11 FOCUS_RING fix (caught-and-fixed pattern; institutional memory).
3. **F-L1 (LOW)** — Append "narrow margin; do not lighten further" to PALETTE_LIGHT FOCUS_RING comment.
4. **F-L2 (LOW)** — Add `test_light_structural_borders_intentionally_below_3_1` negative-assertion guard.
5. **L1 (LOW, deferred)** — AI-12 non-text 3:1 floor mention in `app-invariants.md`. Batch with next milestone touching that file.
6. **H1 (HIGH, process-only)** — diff-LOC overage. No code action; 89% of diff is documentation artifacts.

---

## Rectification status (orchestrator, 2026-05-22)

**Fixed in rect commit:**
- **F-M1 (frontend MEDIUM, dark headroom regression)** — Architecture reverted from single-shared-value to per-theme. PALETTE_LIGHT keeps `#3c82c4` (3.56:1 — closes the original AI-12 failure on light); PALETTE_DARK reverts to `#5b9bd5` (5.17:1 — preserved). The critic's framing was correct: the "key-identical palettes" pattern from dark-mode-2026q2-e1 means same KEYS, values may differ when contrast demands. The original feat commit's "single shared value satisfies both themes" was technically true but compromised the dark headroom (5.17 → 3.78, dropping from 72% to 26% above floor) unnecessarily — the original `#5b9bd5` already passed dark cleanly. Comments in both palette blocks rewritten to explain the per-theme rationale. Existing `test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark` continues to pass (FOCUS_RING dark back to 5.17:1).
- **M1 (adversary MEDIUM, missing CONTEXT.md §8 entry)** — Added §8.14 entry documenting (a) the WCAG 1.4.11 violation pattern, (b) the per-theme fix architecture, (c) the rectify-pass architecture-reversal lesson (single-shared looked clean but eroded dark headroom — the critic's catch), (d) the dual test guards (positive + negative). Mirror of §8.3 short-hex / §8.13 culling-per-variety pattern.
- **F-L1 (frontend LOW, narrow-margin annotation)** — Appended `"narrow margin; do not lighten further"` to the PALETTE_LIGHT inline comment plus full prose context (peer-platform comparison: macOS Sequoia `#007aff` 3.53:1, GNOME Adwaita `#3584e4` 3.31:1 — same band). The narrow-margin warning is now visible at the token, not buried.
- **F-L2 (frontend LOW, code-enforced scope deterrent)** — Added `test_light_structural_borders_intentionally_below_3_1` negative-assertion test. Asserts the 4 light structural border tokens measure `< 3.0:1` on BG_PANEL_LIGHT (currently ~1.1-1.4:1). Any future palette change that darkens them to clear 3:1 fires LOUDLY with a message naming the architectural intent — forcing a deliberate design decision rather than a silent panel-chrome degradation. Machine-readable counterpart to the docstring caveat in the sibling test.

**Deferred:**
- **L1 (adversary LOW, app-invariants AI-12 non-text floor mention)** — One-sentence amendment to `.claude/references/app-invariants.md:132-134` adding the WCAG 1.4.11 non-text 3:1 floor to the AI-12 entry. Out of strict palette scope; batch with next milestone that touches `app-invariants.md`. Defer.

**Invalidated:** none — all four code findings (F-M1, M1, F-L1, F-L2) re-verified present before fixing.

**Process-only:**
- **H1 (adversary HIGH, diff-LOC overage)** — 466-LOC diff dominated by ~417 lines of milestone documentation artifacts. No code action. Disposition: resolved-no-code-change / doc-artifacts inflated total.

**Test suite:** 297 passed (290 baseline + 5 bbox + 1 light FOCUS_RING + 1 light structural-border negative guard). No regressions.

**Architecture lesson recorded:** the initial implementation defaulted to Option A (single shared value) because the arithmetic confirmed it was feasible (3.56:1 light, 3.78:1 dark). The critic's catch was that "feasible" ≠ "optimal" — the original `#5b9bd5` already passed dark at 5.17:1, so collapsing both themes onto the new darker value sacrificed dark headroom for a notional consistency that the codebase's own dark-mode milestone had already shown wasn't necessary (TEXT_VALUE / TEXT_MUTED / BORDER_* all theme-divergent). Same KEYS, values may differ when contrast demands. Now recorded in CONTEXT.md §8.14 for future agents.
