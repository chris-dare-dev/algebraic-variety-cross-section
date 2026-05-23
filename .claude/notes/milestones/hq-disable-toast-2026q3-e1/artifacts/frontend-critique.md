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
