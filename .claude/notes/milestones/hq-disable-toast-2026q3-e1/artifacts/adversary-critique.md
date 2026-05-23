# Adversary critique — HQ auto-disable status-bar toast

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-23 | **Subject:** hq-disable-toast-2026q3-e1 / a52fba3..5a1f4a3

**Diff stats:** 871 total lines (766 insertions / 5 deletions across 8 files).
Functional delta: `app.py` +52/-5 (57 LOC), `tests/test_hq_disable_toast.py` +151/-0 (new file), `CONTEXT.md` +2/-1.
Artifact inflation: 561 lines across `.claude/` research brief, dispatch log, state.json, implementation plan, researcher lessons.

---

## Executive summary

No CRITICALs. One process HIGH (diff-size auto-finding — 871 lines, non-waivable). The most notable behavioral findings are MEDIUM: the combined variety-branch messages (base + `_hq_note`) reach 167–174 characters, well above the ~120-char `QStatusBar` visible-clip band documented in `CONTEXT.md` (§8 bbox milestone), so the toast's critical "Double-pass smooth disabled" text may be hidden off the right edge of the status bar on a standard window width; and Test 1's ordering assertion covers `_on_variety_changed` but provides no parallel ordering guard for `_on_subtype_changed`. Two LOWs: the Enriques variety branch appends `_hq_note` but this is a logically dead code path (the empty-string case is always taken), and the `double-curve topology` literal in Test 4 is the sole test needle for the subtype handler's wording, making it brittle against minor rephrasing.

Two MEDIUMs, two LOWs, one process HIGH. Safe to ship after the MEDIUMs close — the functional contract is correct.

---

## Verdict: SHIP-WITH-FIXES

The dual-call-site implementation is correct and the ordering contract is upheld at runtime. Both MEDIUMs are documentation/test-coverage gaps, not behavioral bugs. The visible-clip MEDIUM is the highest-priority fix: the toast message the milestone exists to show may be clipped at the exact point where it becomes informative ("Double-pass smooth disabled..."). Rectify the two MEDIUMs before close; the two LOWs are optional at the maintainer's discretion.

---

## Critical findings

None.

---

## High findings

### HIGH — Diff size exceeds 400 LOC (review-quality-at-risk auto-finding)

**Where:** no specific file (cross-cutting)
**Evidence:** `git diff a52fba3..5a1f4a3 | wc -l` = 871 lines. Defect-detection research (Cisco / LinearB) shows review quality degrades above 400 LOC. Functional delta is 208 LOC (app.py 57 + test 151); 663 lines are pipeline artifacts (research brief 465 + state.json 50 + plan 35 + dispatch 2 + researcher lessons 9 + CONTEXT.md 2). **No code action required** — the artifact breakdown confirms the functional delta is within the safe review zone.
**Why it matters:** Auto-finding per adversary checklist. Non-waivable. Artifact inflation is the documented sixth occurrence of this pattern in this codebase; disposition is "no code action required."
**Suggested fix:** No fix needed. The functional production code is 208 LOC — well within the 400-LOC defect-detection safe zone.

---

## Medium findings

### MEDIUM — Combined variety-branch messages exceed the ~120-char QStatusBar clip band

**Where:** `app.py:554`, `app.py:564`, `app.py:584`, `app.py:589`
**Evidence:** The base CY3 message is 101 chars; Fano 99 chars; Enriques 106 chars. With `_hq_note` appended ("  Double-pass smooth disabled — only available on Enriques figs 1+2." = 67 chars), the combined strings reach 169, 167, and 174 characters respectively. CONTEXT.md documents `QStatusBar`'s ~120-char visible-clip band (§8 status-bar-bbox milestone). The "Double-pass smooth disabled" clause begins at character 103–113 of the combined message — just past the clip threshold — meaning the most informative part of the toast may be hidden on a standard window width.
**Why it matters:** The milestone's sole purpose is to inform the user their toggle was auto-disabled. If that clause is clipped on a typical macOS window (~800–1200px wide), the user sees only the variety context message and the feature gap the milestone closes is not actually closed for them.
**Suggested fix:** Shorten `_hq_note` to " [Double-pass off — Enriques 1+2 only]" (~39 chars), bringing all combined messages under 150 chars and keeping the critical information visible. Alternatively, emit a separate `showMessage` call after the variety branch (replacing the variety message with a shorter dedicated toast that includes the key context), but this requires changing the Option-A design decision.
**Regression-guard test:** `assert len("Calabi–Yau 3-fold — each figure is a 2D real shadow of a 6-dimensional manifold.  Now choose a model." + _hq_note_value) <= 150` would catch regression; or assert the `_hq_note` literal in app.py is under 50 chars.

### MEDIUM — Test 1 ordering assertion covers only `_on_variety_changed`, not `_on_subtype_changed`

**Where:** `tests/test_hq_disable_toast.py:768–786`
**Evidence:** `test_hq_disable_toast_captures_prior_state_before_eligible_call` uses `_APP_SRC.find("set_hq_smoothing_eligible(False)")` to locate the "clear" call. In `_on_subtype_changed` the call is `set_hq_smoothing_eligible(is_hq_eligible)` — the `(False)` literal never appears in that handler. So the ordering assertion (capture before clear) only validates the variety-handler ordering; a future refactor that accidentally moves `_prior_hq = self.appearance_panel.hq_smoothing` to after the `set_hq_smoothing_eligible(is_hq_eligible)` call in `_on_subtype_changed` would silently pass all four tests while breaking the subtype-change toast for the Enriques Fig.1→Fig.3 case.
**Why it matters:** The researcher explicitly identified the dual-call-site requirement as "load-bearing." A test suite that validates one site's ordering but not the other provides a false sense of coverage for the most subtle part of the implementation.
**Suggested fix:** Add a fifth test (or extend test 1) that asserts `_APP_SRC.find("_prior_hq = self.appearance_panel.hq_smoothing", subtype_method_start) < _APP_SRC.find("set_hq_smoothing_eligible(is_hq_eligible)", subtype_method_start)`, where `subtype_method_start` is located via `_APP_SRC.find("def _on_subtype_changed")`.
**Regression-guard test:** `idx_sub_def = _APP_SRC.find("def _on_subtype_changed"); idx_sub_capture = _APP_SRC.find("_prior_hq = self.appearance_panel.hq_smoothing", idx_sub_def); idx_sub_clear = _APP_SRC.find("set_hq_smoothing_eligible(is_hq_eligible)", idx_sub_def); assert idx_sub_capture < idx_sub_clear`

---

## Low findings

### LOW — Enriques variety branch appends `_hq_note` via a logically dead code path

**Where:** `app.py:584`
**Evidence:** `_hq_note` is non-empty only when `_prior_hq` is True. `_prior_hq` can be True only when the user had Double-pass smooth enabled, which is only possible on Enriques Figs. 1+2. `_on_variety_changed("Enriques surface")` fires only when the variety combo CHANGES to Enriques — i.e., the user was previously on a different variety. But being on a different variety means HQ was ineligible and `_hq_smoothing` was False. Therefore `_prior_hq` is always False when the Enriques branch of `_on_variety_changed` fires. The `{_hq_note}` interpolation in `app.py:584` always expands to an empty string. The inline comment at `app.py:578–581` correctly explains this, but the interpolation itself is dead code.
**Why it matters:** Dead code that is proven-always-empty by logical argument is an ongoing maintenance burden: future authors who add a new "re-select same variety" path might accidentally create a case where `_prior_hq` is True in the Enriques branch, and the comment will have aged past its context. The empty-string append is harmless at runtime.
**Suggested fix:** Either remove the `{_hq_note}` from the Enriques branch's `showMessage` call and tighten the comment to say "Enriques branch intentionally does NOT append `_hq_note` — the HQ state is managed by `_on_subtype_changed`"; or add a `# type: ignore` + inline assertion `assert not _hq_note, "unreachable"` to surface any future violation. The former is cleaner.

### LOW — Test 4 needle "double-curve topology" is the sole wording guard for the subtype handler

**Where:** `tests/test_hq_disable_toast.py:866–871`
**Evidence:** The only test assertion that specifically validates the subtype handler's toast (as opposed to the variety handler's) is `assert "double-curve topology" in _APP_SRC`. A natural rewording — e.g., "double-curve singularities" (anatomically more precise per CONTEXT.md §8.13), or "Figs. 1+2 double-curve topology" — would fail this test even though the behavior is correct. No other test checks the subtype handler's message content.
**Why it matters:** The needle is overly specific in wording but not specific enough in location — it does not anchor to `_on_subtype_changed` scope. A future edit that moves the exact phrase to a comment rather than a runtime string would also pass the test. The combination of over-specific wording + under-specific location creates a brittle guard.
**Suggested fix:** Replace the needle with a more stable substring — e.g., "double-curve" alone — and anchor it after `_APP_SRC.find("def _on_subtype_changed")` to confirm the phrase appears in the subtype handler's scope, not just anywhere in the file.

---

## What was done well

- **Dual-call-site requirement correctly implemented.** Both `_on_variety_changed` (app.py:533) and `_on_subtype_changed` (app.py:660) capture `_prior_hq` before the eligible-clear call and conditionally emit the toast. The researcher's load-bearing catch was fully honored — the Enriques Fig.1→Fig.3 subtype-only transition is covered.
- **Ordering constraint respected at both sites.** `_prior_hq = self.appearance_panel.hq_smoothing` appears at character 27274, `set_hq_smoothing_eligible(False)` at 27333 (variety handler); and 34606 vs 34796 (subtype handler). Both captures precede their respective clears by a comfortable margin.
- **AI-9 clean.** `hq_smoothing` is a pure Python `@property` returning a bool — no signal emission, no processEvents. `showMessage` is a synchronous paint update. No re-entrancy surface introduced.
- **AI-15 honest.** "only available on Enriques figs 1+2" exactly matches `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` (frozenset containing "Canonical sextic [Fig. 1]" and "Diagonal λ-family [Fig. 2]"). The message is factually accurate and explains the eligibility scope, not just the outcome.
- **Option A (per-branch `_hq_note` string) correctly chosen over Option B (timeout showMessage) and Option C (currentMessage append).** The research brief's analysis of Option B's replace-not-append semantics and Option C's race fragility is sound, and the implementation follows the correct Option A design.
- **CONTEXT.md §4.3a extended with the dual-call-site constraint documented.** The sentence "Both call sites are required: the variety-only handler misses the Enriques-Fig.1 → Enriques-Fig.3 transition (subtype-only change)" is a clear and accurate institutional memory entry.
- **Four AI-2-compliant source-grep tests.** No QApplication, no MainWindow, no live statusBar mutation — all four tests read `app.py` as text. The test docstring explicitly states the AI-2/AI-3 compliance rationale.
- **Test 4 (dual-call-site count) closes the "did both sites get implemented?" gap.** Counting `_prior_hq = self.appearance_panel.hq_smoothing` ≥ 2 is the right proxy for dual-handler coverage, confirming that the researcher's optional-but-recommended test was included.
- **453 tests pass, confirming zero regressions.** A pure status-bar text change with no VTK path touched correctly skips off-screen render verification, and the suite confirms this is correct.
- **Inline implementation with no new module, no new signals, no new panel API.** The minimal scope respects the single-developer cadence and produces a tight, reviewable diff (208 functional LOC).

---

## Recommended rectification order

1. **Fix the message-length MEDIUM first.** Shorten `_hq_note` in `app.py:541–544` so combined messages fall under 150 chars. This is a one-line string change with four f-string call sites to verify. The fix directly determines whether the milestone's UX goal is achieved on a standard window width.
2. **Add the subtype-handler ordering assertion (test coverage MEDIUM).** Add a fifth test to `tests/test_hq_disable_toast.py` that locates `def _on_subtype_changed` in the source and asserts `_prior_hq` capture precedes `set_hq_smoothing_eligible(is_hq_eligible)` within that method's scope. This closes the single most important ordering gap in the current test suite.
3. **LOWs are optional follow-ups.** The Enriques dead-code-path comment cleanup (LOW 1) and the subtype-handler test needle update (LOW 2) improve long-term maintainability but do not affect current correctness. Address at the maintainer's discretion.

---

*End of critique. Mandatory rectification: the two MEDIUMs (message-length clip + subtype ordering test). LOWs optional.*
## Frontend UI/UX findings

_Merged from milestone-frontend-ux-critic._

# Frontend UX Critique — hq-disable-toast-2026q3-e1

**Critic:** milestone-frontend-ux-critic
**Date:** 2026-05-23
**Commit range:** `a52fba3fa889e1e473b39091b2860ec2b6a9c545..5a1f4a392079692365dfe706d750a0137764d61a`
**Scope:** `app.py` only (`_on_variety_changed` and `_on_subtype_changed` modifications + `CONTEXT.md` update).  No Qt-panel files changed (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `styles.py` untouched).

---

## Executive summary

1 HIGH, 0 MEDIUM, 1 LOW.

The milestone correctly closes F-L2 (silent HQ-disable on navigation) and the dual-call-site design (`_on_variety_changed` + `_on_subtype_changed`) is architecturally sound.  The prior-state capture ordering is correct and the subtype toast works well within the visible band.  However, the three variety-branch messages (CY3, Fano, Enriques) compose to 167–174 chars, pushing the load-bearing keyword "disabled" past the empirical ~120-char QStatusBar clip point.  A user switching from Enriques Fig.1 (HQ on) to CY3 sees `"Calabi–Yau 3-fold — each figure is a 2D real shadow of a 6-dimensional manifold.  Now choose a model.  Double-pass smoot"` — the word "disabled" and the scope explanation are clipped.  The feature's sole purpose for the cross-variety case is undermined.

No gate required.

---

## CRITICAL

None.

---

## HIGH

### HIGH — Variety-branch HQ toast clipped past ~120-char visible band

**Where:** `app.py:552-554` (CY3 branch), `app.py:562-564` (Fano branch), `app.py:582-584` (Enriques branch)

**Evidence:** Measured rendered string lengths:

| Branch | Total chars | "disabled" starts at | Visible within 120? |
|---|---|---|---|
| CY3 + `_hq_note` | 169 | char 121 | NO |
| Fano + `_hq_note` | 167 | char 119 | NO (borderline) |
| Enriques + `_hq_note` | 174 | char 126 | NO |
| Fallback (K3/etc.) + `_hq_note` | 108 | char 42 | YES |

The CY3 visible tail is `"…Now choose a model.  Double-pass smoot"` — the word `disabled` and the entire scope explanation (`"only available on Enriques figs 1+2."`) are clipped.  This is the 3 most common paths (CY3 is the largest variety; Fano is next; Enriques is also common).  The fallback branch (K3, hypothetical future variety) is 108 chars and renders correctly.

This is the same overflow pattern documented in lessons.md ("Status-bar overflow: empirical clip ~120 chars; hoist load-bearing tokens LEFT of any separator").  The prior fix pattern was to hoist the load-bearing token left.  Here, the variety description is also important, so the fix is to shorten the `_hq_note` suffix.

**Why it matters:** The feature's sole purpose for the cross-variety case (e.g., Enriques Fig.1 → K3) is to surface the "why" of the auto-disable.  With the keyword `disabled` clipped, the user sees `"Double-pass smoot"` — truncated mid-word, no explanatory scope, no confirmation the toggle was cleared.  The fix (shorter suffix) is trivial; the status as shipped defeats the feature for 3 of 4 variety branches.

**Suggested fix:** Shorten `_hq_note` to `"  [Double-pass smooth off]"` (25 chars) or `"  [HQ off — Enriques only]"` (26 chars).  At 25-26 chars, CY3+note = 126 chars total, which is over 120 by 6 — still borderline.  The cleanest fix is to hoist the note before the "Now choose a model." phrase, e.g. `"Calabi–Yau 3-fold — …manifold.  [Double-pass smooth off]  Now choose a model."` so the disclosure appears at chars 51-76, well within the visible band.  Alternatively, drop the variety description in favor of a two-part message: emit the variety-context message first, then immediately replace with a toast-only message containing the HQ note — but this would lose the variety context.  The hoist-before-CTA approach is the lowest-risk fix: `f"…manifold.{_hq_note}  Now choose a model."` keeps the variety context in the visible band and puts the HQ note before the generic CTA.

---

## MEDIUM

None.

---

## LOW

### LOW — Subtype toast `(double-curve topology)` partially clipped for Fig.4

**Where:** `app.py:672-674` (`_on_subtype_changed` toast branch)

**Evidence:** The Fig.4 subtype toast (`"Subtype: Quartic Kummer surface  [Fig. 4].  Double-pass smooth disabled — only available on Enriques figs 1+2 (double-curve topology)."`) is 134 chars.  The load-bearing tokens `"Double-pass smooth disabled"` (at char 63) and `"Enriques figs 1+2"` (at char 92) are both within the 120-char visible band.  Only the parenthetical `"(double-curve topology)."` clips at char 120 — `"(double-curve t"` is visible, `"opology)."` is not.

The Fig.3 toast at 129 chars clips `"opology)."` (10 chars) similarly.

**Why it matters:** The parenthetical `(double-curve topology)` is the explanatory "why" — the subtype-only variant intentionally adds this per the research brief ("adds '(double-curve topology)' as the WHY explanation").  Clipping it loses the explanation.  However, the core disclosure (`disabled — only available on Enriques figs 1+2`) is fully visible; the clipped portion is supplementary.

**Suggested fix:** Trim the parenthetical to `(dbl-curve)` (saves 11 chars, bringing Fig.4 to 123 chars) or remove it from the inline toast and rely on the CONTEXT.md §8.13 reference for the deeper explanation.  Alternatively, drop the subtype prefix (`"Subtype: Quartic Kummer surface  [Fig. 4].  "` = 43 chars) in favor of a shorter prefix: `"Fig.4 selected.  Double-pass smooth disabled — Enriques figs 1+2 only (double-curve topology)."` = 94 chars — well within 120.

---

## What was done well

**Dual-call-site architecture is correct.** The research brief's load-bearing insight was that `_on_variety_changed` alone misses the Enriques Fig.1 → Fig.3 subtype-only transition.  Both handlers are wired, and the prior-state capture appears at exactly the right ordering position in each (before `set_hq_smoothing_eligible()` clears `_hq_smoothing`).

**Prior-state capture ordering is precisely correct.** `_prior_hq = self.appearance_panel.hq_smoothing` is placed before `self.appearance_panel.set_hq_smoothing_eligible(False)` in `_on_variety_changed` (app.py:533–534) and before the `is_hq_eligible` computation + eligible call in `_on_subtype_changed` (app.py:660–665).  Reading after the eligible call would always return False (per the `blockSignals` pattern in `appearance_panel.py`).

**Conditional guard prevents noise on the common path.** The `if _prior_hq` guard in both handlers means the toast fires only when the user had Double-pass smooth enabled.  The vast majority of sessions (HQ never enabled, or HQ off at switch time) remain silent.  Correct design.

**Subtype toast timing is appropriate.** The subtype toast fires immediately before `_render_current` and persists for ~449 ms until the render-completion message overwrites it.  During that window the user can read the explanation.  This is the correct timing strategy — Option B (timeout `showMessage`) was correctly rejected in the design brief.

**Double-toast avoided.** The Enriques-variety → Enriques-Fig.3 path does not produce a double toast: the variety handler clears `_hq_smoothing` via `set_hq_smoothing_eligible(False)`, so when `_on_subtype_changed` fires next, `_prior_hq = False` and the subtype toast guard is silent.  The two handlers do not interfere.

**AI-9/AI-11/AI-12/AI-13 all clear.** No `processEvents()` added, no new Qt enum symbols, no new color literals anywhere in the diff.  The `showMessage` calls are synchronous status-bar updates with no re-entrancy surface.

**Test suite is rigorous and correctly scoped.** All 4 tests are pure source-text greps (AI-2 compliant): test 1 verifies capture ordering, test 2 verifies the conditional guard, test 3 verifies the AI-15 message content (label name + scope explanation), test 4 verifies the dual-call-site count (`>= 2` captures).  No `QApplication` construction anywhere.

**First-launch path clean.** Neither `_on_variety_changed`'s new code nor `_on_subtype_changed`'s new code touches `_render_current`, `variety_combo`, or `subtype_combo` at construction time.  Section 9.3 (no first-launch auto-render) is preserved.

**CONTEXT.md update is accurate and minimal.** One sentence added to §4.3a explaining the dual-handler toast pattern, the F-L2 closure, and the prior-state capture ordering constraint.  Correct documentation without over-engineering.

**AI-15 honesty.** The toast text `"Double-pass smooth disabled — only available on Enriques figs 1+2."` accurately names the current user-visible label (correct since `hq-smoothing-label-rename-2026q3-e1`) and the actual eligibility gate (`_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` frozenset at app.py:73–76).  No marketing language.

---

## Industry comparison

**VS Code status-bar vs notification framework:** VS Code surfaces "Setting X was disabled" via its notification toast framework (floating banner, right side, dismissible), not the status bar.  AVC has no notification framework — the status bar is the only user-visible ephemeral feedback channel.  Using `showMessage` here is the correct architectural choice given the app's scope.  The VS Code comparison is informative for what a future notification system might look like (UPL), not an actionable finding for this milestone.

**ParaView's status-bar pattern:** ParaView uses the status bar for plugin-load failures and render-pipeline messages — short, single-line messages that fit within the visible window width.  ParaView never composes a 174-char multi-clause message into a single status bar string; it either truncates deliberately (showing a summary) or uses a two-line status area.  This confirms that the 174-char variety+note composite is outside the peer convention for status-bar UX in desktop scientific-viz tools.

---

## Recommended rectification order

1. **HIGH-1 (variety-branch overflow):** Hoist `_hq_note` to appear before `"Now choose a model."` in the 3 long variety branches, or shorten the note to `"  [Double-pass smooth off]"` (25 chars).  The hoist approach is cleanest — it preserves full note text and keeps "Now choose a model." as the trailing CTA.  Affects 3 `showMessage` call sites in `_on_variety_changed`.

2. **LOW-1 (subtype toast clip):** Optionally shorten the subtype parenthetical from `(double-curve topology)` to `(dbl-curve)` or drop the subtype-name prefix.  This is a cosmetic polish that can be deferred to the next milestone touching `_on_subtype_changed`.

---

## Rectification status — 2026-05-23

**Fixed (in-scope, this rect commit):**
- `cross-critic HIGH/MEDIUM` (status-bar clip-band defeat): hoisted the HQ-disable disclosure to the FRONT of every variety-branch message (renamed `_hq_note` → `_hq_prefix` to signal the leading role). Both Phase 3 critics independently flagged this as the headline finding: my initial append-after-context pattern (Option A from the research brief) produced combined messages of 165-174 chars, exceeding the ~120-char QStatusBar visible-clip band and silently clipping the "Double-pass smooth disabled" disclosure off the right edge — defeating the entire feature. New message structure: `f"{_hq_prefix}{variety context...}"` with prefix `"Double-pass smooth disabled (Enriques figs 1+2 only).  "` (55 chars). The disclosure now ends at char 55, well within the visible band; the variety context tail can clip without losing the load-bearing information.
- `subtype handler reorder`: subtype-handler message similarly reordered — `"Double-pass smooth disabled (Enriques figs 1+2 only — double-curve topology).  Subtype: {name}."` — disclosure leads, subtype name follows. Longest subtype name (`"Diagonal λ-family  [Fig. 2]"`) produces ~116-char total, fully within the visible band.
- `adversary MEDIUM-2` (subtype-handler ordering test missing): added `test_hq_disable_toast_subtype_handler_captures_prior_before_eligible_call` which explicitly scopes the ordering check to the `_on_subtype_changed` method body (the original test's source-grep find()-on-first-occurrence pattern validated only the variety handler).
- `regression-guard test`: added `test_hq_disable_toast_disclosure_leads_each_variety_message` which (a) asserts `_hq_prefix` is present, (b) asserts the OLD `_hq_note` symbol is ABSENT (prevents regression to the append pattern), and (c) verifies the `f"{_hq_prefix}<variety>` opening in all four variety branches.
- `stale comment cleanup`: removed `_hq_note` reference in inline comment that survived the variable rename.

**Deferred (out-of-scope or cosmetic):**
- `HIGH adversary` (process / diff-size auto-finding): standard process disposition; production+test delta is well below the 400-LOC threshold.
- Wording-style alternatives ("figs 1+2" vs "Fig. 1 and Fig. 2"): the chosen "figs 1+2" is shorter (saves ~6 chars from each message) which materially helps the clip-band budget; defer alternative wording exploration to a feedback-driven follow-on if researchers report confusion.

**Invalidated:** none.

**Test count:** 455 pass (was 453, +2 rect regression guards). Both guards anchor the clip-band fix so a future refactor can't silently regress to the append-after-context pattern.
