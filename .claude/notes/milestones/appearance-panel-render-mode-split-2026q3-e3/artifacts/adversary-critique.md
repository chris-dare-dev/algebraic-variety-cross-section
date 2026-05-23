# Adversary critique — QGroupBox "Display & Quality" rename (F-M2 closure)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** appearance-panel-render-mode-split-2026q3-e3

**Commit range:** `9fbb97436149638caffa28132d6eea4dfaa0a5ed..ab4b51e`
**Diff stats:** 595 total lines (208 production+test, 387 milestone artifact files); 10 files changed, 433 insertions, 42 deletions
**Test result:** 385 passed, 0 failed (confirmed by running `.venv/bin/pytest tests/ -q`)

---

## Executive summary

The dominant finding is a process-level auto-HIGH for diff size (595 total lines, though 65% is milestone artifact inflation with no code-action required). The only substantive finding is a LOW-severity stale docstring: `tests/test_styles_palette.py:801` within `test_appearance_panel_colors_buttons_have_colors_button_role` still references "Render Mode groups" — this is a sibling test function that was not listed in the brief's update scope and was missed. No CRITICALs. No code-path HIGHs. The `&&` Qt escape is correctly applied. All "Render Mode" switch/dict-lookup paths are clean (none existed). The three-layer regression guard (positive + 2 negative) is correctly structured. The CONTEXT.md prose updates are internally consistent. All AI-1..AI-15 invariants are clean.

---

## Critical findings

None.

---

## High findings

### HIGH — Diff size exceeds 400-line review-quality-at-risk threshold

**Where:** no specific file (diff-level finding)
**Evidence:** `git diff 9fbb974..ab4b51e | wc -l` = 595 lines. The Cisco / LinearB defect-detection research establishes that reviewer effectiveness degrades significantly above 400 LOC per review session.
**Why it matters:** This finding is non-waivable per the checklist protocol. In this specific case the concern is materially mitigated: 387 of 595 lines (65%) are pure milestone artifact files (`.claude/notes/milestones/.../research/agent-solo-brief.md`, `implementation-plan.md`, `dispatch.log`, `state.json`, and `milestone-researcher/lessons.md`). The production+test delta is 208 lines, which is squarely in the well-reviewed range.
**Suggested fix:** No code action required. Orchestrator should note the artifact-inflation ratio as the standard disposition for this repo's milestone pipeline.
**Regression-guard test:** n/a — process finding, not a code defect.

---

## Medium findings

None.

---

## Low findings

### LOW — Stale "Render Mode groups" docstring in sibling test function

**Where:** `tests/test_styles_palette.py:801`
**Evidence:** The docstring of `test_appearance_panel_colors_buttons_have_colors_button_role` (a test function NOT in the brief's update scope) reads: "re-introducing the cross-group vertical-rhythm fracture between the Colors and **Render Mode groups** that this milestone closed." The group has been renamed to "Display & Quality"; the prose is now stale.
**Why it matters:** A future reader grepping for "Render Mode" to audit rename completeness will find this hit and need to determine whether it is intentional historical context or an oversight. It is an oversight — no code-quote attribution marks it as historical. Docstrings are not historical records; they describe current behavior. Unlike the inline comments in `appearance_panel.py:202` (which explicitly use past-tense attribution), this docstring uses present tense ("that this milestone closed"), making the stale group name actively misleading.
**Suggested fix:** Change `"the Colors and Render Mode groups"` to `"the Colors and Display & Quality groups"` in the docstring at `tests/test_styles_palette.py:801`.

---

## What was done well

- **`&&` Qt escape correctly applied.** The source literal `QGroupBox("Display && Quality")` at `appearance_panel.py:221` is the correct form. The inline comment block (lines 218–220) explicitly documents why the double `&&` is required — "a single `&` would underline `Q` and bind it as an Alt+Q accelerator" — which anchors this non-obvious Qt behavior for future maintainers without requiring them to consult Qt docs.

- **No switch/dict-lookup paths depend on the literal string "Render Mode".** Source-grep over all `.py` files confirms the string appears only in inline comments and docstrings — never in a dictionary key, `if`/`elif` chain, or `match`/`case` block. The rename is fully safe with respect to control-flow correctness.

- **Three-layer regression guard structure.** The positive assertion (`'QGroupBox("Display && Quality")' in src`) plus two negatives (`'QGroupBox("Render Mode")' not in src` and `'QGroupBox("Display")' not in src`) at `tests/test_styles_palette.py:866–890` provide protection against the current name, the immediately-prior name, and the even-older name. This is stronger than the prior milestone's guard (which had only positive + 1 negative).

- **Test function renamed to match the new assertion.** `test_appearance_panel_render_mode_group_header` → `test_appearance_panel_display_and_quality_group_header` at `tests/test_styles_palette.py:842` eliminates the "function name contradicts what it asserts" confusion that would arise if the old name were kept. The rename is consistent with the `hq-smoothing-label-rename-2026q3-e1` precedent for test function renaming.

- **AI-15 honesty attestation is verified by code.** "Display" is backed by `appearance_panel.py:396` (`actor.prop.style = "wireframe"`) and `appearance_panel.py:405` (`actor.prop.show_edges = checked`) — direct actor property toggles, no mesh regeneration. "Quality" is backed by `appearance_panel.py:423` (`self.hq_smoothing_changed.emit(checked)`) emitting into `MainWindow._on_hq_smoothing_changed → _invalidate_clipped_mesh() + _render_current()` — confirmed full-regeneration path. The label accurately names both axes.

- **CONTEXT.md prose correctly updated with full rename lineage.** Both `CONTEXT.md:147` and `CONTEXT.md:488` now carry the "Display" → "Render Mode" → "Display & Quality" parenthetical trail with milestone-id attribution. Future git-blame readers can reconstruct the group's naming history without hunting commits.

- **Historical comment rationale preserved and attributed.** `appearance_panel.py:202–207` keeps the MeshLab/Blender/ParaView peer-tool audit as attributed past-tense context ("'Render Mode' replaced the generic 'Display' header. MeshLab uses that exact term..."), then appends the superseding rationale with the current milestone id. This follows the precedent established by `hq-smoothing-label-rename-2026q3-e1` and avoids erasing the institutional memory of why "Render Mode" was chosen originally.

- **Internal symbol names correctly left unchanged.** `_build_toggles_group`, `"display-toggle"` role property (on all 3 buttons: `_wireframe_cb`, `_edges_cb`, `_hq_smoothing_cb`), and variable `vl` are all untouched. The brief's explicit guidance to keep internal names was followed precisely — no unnecessary blast-radius churn.

- **385 tests pass with no regressions.** The renamed test is correctly discovered by pytest (function name follows `test_` prefix convention); no orphaned references to the old function name exist in the test suite.

---


## Cross-critic agreement

The following findings cluster within 5 lines of each other in the same file. Multiple critics flagged the same area -- these are the strongest signals to fix first.

- **M1, L2** at `appearance_panel.py:221-221` (LOW): 1 — Compound header breaks single-noun peer rhythm in the Appearance dock; 1 — "Quality" reads ambiguously without the tooltip context that doesn't exist on the group header

## Recommended rectification order

1. **Fix the single LOW.** Update `tests/test_styles_palette.py:801`: change "Render Mode groups" → "Display & Quality groups" in the `test_appearance_panel_colors_buttons_have_colors_button_role` docstring. One-line change; re-run `pytest tests/ -q` to confirm 385 pass.
2. **The HIGH (diff-size auto-finding) requires no code action.** The artifact-inflation disposition ("no code action required") applies. Log it and move on.

---

*End of critique. Mandatory rectification: none (no CRITICALs or code-path HIGHs). The single LOW at `tests/test_styles_palette.py:801` is recommended before milestone close.*
## Frontend UI/UX findings

_Merged from milestone-frontend-ux-critic._

# Frontend UX Critique — appearance-panel-render-mode-split-2026q3-e3

**Critic:** milestone-frontend-ux-critic  
**Date:** 2026-05-22  
**Commit range:** `9fbb97436149638caffa28132d6eea4dfaa0a5ed..ab4b51e`  
**Files reviewed:** `appearance_panel.py`, `styles.py`  
**Status:** complete

---

## Executive Summary

This milestone delivers a single label rename: `QGroupBox("Render Mode")` → `QGroupBox("Display && Quality")`. The rename is semantically correct (the group is heterogeneous — two display-pipeline toggles and one mesh-regeneration quality toggle), the `&&` Qt literal-ampersand escape is correctly applied, and all comment blocks that referenced the old name are updated consistently. No logic, no widget structure, no color, no enum, and no event-loop code changed.

**Finding counts: 0 CRITICAL / 0 HIGH / 1 MEDIUM / 1 LOW**

The sole MEDIUM is a cosmetic register break: "Display & Quality" is the only two-word compound among four otherwise single-noun group headers, which creates a rhythm asymmetry on first-launch inspection before any variety is selected. The LOW is a minor industry-idiom observation.

No gate question. Recommended next step: ship as-is or accept the MEDIUM cosmetic finding as a known trade-off and close F-M2.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM-1 — Compound header breaks single-noun peer rhythm in the Appearance dock

**Where:** `appearance_panel.py:221`  
**Evidence:** The four QGroupBox headers in the Appearance dock, in vertical order, are: `"Colors"`, `"Display && Quality"` (displayed as "Display & Quality"), `"Opacity"`, `"Shading"`. Three are single bare nouns; one is a two-word compound with an ampersand. On first launch the header is visible immediately (the scroll area is unlocked, the group is always rendered), so a math researcher sees "Display & Quality" before selecting any variety.  
**Why it matters:** The compound header breaks the visual rhythm of its peers. In desktop sci-viz peers, within a single dock, group-box headers are either all single-noun ("Render", "Color", "Clip") or all compound ("View Presets", "Clip Region", "Scene Aids", "Export") — consistent within their panel. The View dock uses only compound headers; the Appearance dock uses only single-noun headers except for this one group. The asymmetry is particularly visible on first launch because "Display & Quality" is the only header whose label wraps to two words and forces the user's eye to process a different grammatical structure mid-scan. **ParaView 5.13's Properties panel** uses consistent compound headers throughout ("Representation", "Coloring", "Styling", "Lighting" — all single nouns) precisely to allow the user to scan labels at a glance without any cognitive shift. **Blender 4.x's N-panel** alternates between single-noun and compound labels within a panel only when the compound label accurately describes a fundamentally different control category — it does not do so for aesthetic reasons. Here "Quality" is accurate but "Display" is also one of the three existing single-noun candidates for this group's label (already rejected in F-L2 as too generic). The trade-off is real: the compound label IS more semantically accurate than "Render Mode"; the cost is a panel-rhythm break.  
**Suggested fix:** Either (a) accept the asymmetry as a consciously chosen trade-off (the label precision is worth more than rhythm uniformity — defensible given the genuinely heterogeneous group contents) and document it; or (b) rename the other groups to compound headers ("Surface Colors", "Surface Opacity", "Surface Shading") so the dock is uniformly compound. Option (a) is cheaper and the current label is honest. This is explicitly a subjective trade-off, not a hard correctness failure.

---

## LOW

### LOW-1 — "Quality" reads ambiguously without the tooltip context that doesn't exist on the group header

**Where:** `appearance_panel.py:221`  
**Evidence:** The word "Quality" in the header has no tooltip (`QGroupBox` headers do not receive tooltips in the current panel architecture — confirmed: no `setToolTip` call on the returned `box` object). A math researcher encountering "Display & Quality" for the first time may interpret "Quality" as image quality (antialiasing, SSAO), render quality (shadow maps, lighting model), or mesh quality (vertex count, resolution). The actual meaning — mesh-generation fidelity (a second Taubin pass) — is only discoverable by hovering the individual "Double-pass smooth" button.  
**Why it matters:** **MeshLab** explicitly labels its second-pass operation "TwoStep Smooth" in the filter menu, placing the descriptor in the operation's own name, not in the group header. The group header "Filters > Smoothing, Fairing and Deformation" is a full-phrase that removes ambiguity. **3D Slicer's Display panel** uses "Quality" only for volume-rendering sample distance, where the mapping to image quality is direct and unambiguous. AVC's "Quality" in a group that contains display toggles breaks the reader's expectation set by those peers.  
**Suggested fix:** This is LOW because each button's existing tooltip resolves the ambiguity on hover, and the group header label is not required to fully self-describe its contents. The partial mitigation — ensuring the "Double-pass smooth" tooltip remains visible on a disabled (greyed-out) button on macOS — requires `QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets, True)` in `main()` (a pre-existing LOW from `enriques-hq-smoothing-2026q3-e1`'s critique, still open). If that attribute is not set, the "Quality" label becomes even more ambiguous when the button is greyed out and the tooltip is invisible.

---

## Axis disposal (no findings)

**Axes disposed cleanly:**

1. **Visual hierarchy** — "Display & Quality" is the second of four groups; the Colors group (the most-used picker) remains the first eye-stop. No regression.
2. **Dock layout** — Appearance dock group order (Colors → Display & Quality → Opacity → Shading) unchanged. View dock (left) / Parameters dock (right-top) / Appearance dock (right-bottom) layout per CONTEXT.md §4 untouched.
3. **First-launch UX** — `_build_toggles_group` is called from `_build_ui` → `__init__` only; no path to `_render_current` or `variety_combo`. The header is visible pre-selection as a structural label, not as an interactive element that could auto-render. CONTEXT.md §9.3 clean.
4. **Slider affordances** — No sliders touched. N/A.
5. **Status-bar feedback** — No status-bar text changed. N/A.
6. **Tooltip honesty (AI-15)** — No tooltips changed. No new variety. N/A.
7. **Color contrast (AI-12)** — No color literals introduced. N/A.
8. **Color format (AI-13)** — No hex literals introduced. `"Display && Quality"` is a Python string, not a color argument. N/A.
9. **Qt enum form (AI-11)** — No Qt enum usage introduced. `QGroupBox("Display && Quality")` is a string constructor call, not an enum. N/A.
10. **Re-entrancy (AI-9)** — No `processEvents()` call added. No event-loop change. N/A.
11. **Keyboard shortcuts and `&&` escape correctness** — The `&&` form is the correct Qt literal-ampersand escape for `QGroupBox` (which inherits mnemonic/accelerator handling from `QLabel`). A bare `"Display & Quality"` would have underlined "Q" and bound `Alt+Q` as an unintended group-box accelerator — this milestone correctly uses `&&`. The comment at `appearance_panel.py:218–220` documents this rationale explicitly. `Ctrl+R`, `Ctrl+Shift+S`, and `Ctrl+D` are not in `appearance_panel.py`; the rename does not touch `app.py`. No shortcut conflict introduced.
12. **Industry comparison** — ParaView 5.13 uses "Representation" (single-noun) for its display/quality panel. MeshLab uses "Render Mode" (two-word, but noun phrase without ampersand) for display-pipeline controls only — not for mixed display+quality groups. Blender 4.x uses "Viewport Overlays" (compound) and "Shading" (single-noun) as separate groups rather than combining them. 3D Slicer's "Display" panel uses "Quality" only for volume-rendering resolution, not for mesh smoothing. AVC's "Display & Quality" is a novel compound label without a direct peer precedent for the mixed-category pattern; the nearest precedent is **ParaView's "Display" tab**, which the research brief cites — it combines representation + quality settings in a single tab. The label is defensible and more honest than the prior "Render Mode" (which MeshLab uses only for pure display-pipeline controls). Peer-specificity check passes: the industry comparison supports the rename rationale even if no peer uses exactly this label.

---

## What was done well

1. **The `&&` escape is exactly correct.** A single `&` would silently create an `Alt+Q` keyboard accelerator on the group box — a subtle Qt footgun for compound labels. The implementation pre-empts this and documents the reason in the inline comment at lines 218–220. No other QGroupBox in this codebase uses `&` in its title; this is the first compound header and the escape was handled correctly on the first attempt.

2. **Comment discipline is thorough without being excessive.** The updated comment block at lines 200–221 preserves the historical peer-tool rationale (why "Render Mode" was chosen by `appearance-panel-layout-pass-2026q3-e2`) and appends the superseding rationale for this milestone. A future reader gets full chronological context from the code comments alone — no need to search git history. The inline cite pattern (`appearance-panel-render-mode-split-2026q3-e3 (F-M2 closure)`) is consistent with the rest of the codebase.

3. **All comment-only propagation sites are updated.** Four locations referenced "Render Mode group" in inline comments (`appearance_panel.py:156`, `159`, `175`; `styles.py:483`). All four are updated. None are missed. The diff shows careful mechanical discipline — no stale references remain in the changed files.

4. **The semantic justification is load-bearing and accurate.** The label "Display & Quality" honestly describes the group: Wireframe and Show edges change `actor.prop.*` (display-pipeline, no regeneration); Double-pass smooth changes the mesh (quality toggle, regeneration required). The label is not marketing language; it is a correct categorical description of the two axes the group's controls operate on. This closes the MEDIUM-2 from `appearance-panel-layout-pass-2026q3-e2`'s adversary critique cleanly.

5. **AI-1 through AI-15 are all clean.** A pure string-literal label rename at a QGroupBox constructor call touches zero lines of logic, zero color tokens, zero Qt enum usages, zero event-loop code. The critique has nothing to surface on those axes — that is the correct result for an XS label-only milestone.

---

## Recommended rectification order

1. **(MEDIUM-1 — optional / accept-as-known):** If visual rhythm matters post-ship: rename the other three groups to compound headers ("Surface Colors", "Surface Opacity", "Surface Shading") to unify the dock. Or document the asymmetry as a chosen trade-off in CONTEXT.md §4 and close. This is a cosmetic call, not a correctness issue.

2. **(LOW-1 — already tracked):** Ensure `QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets, True)` is set in `main()` so the "Double-pass smooth" tooltip (which explains the "Quality" semantic) is visible even when the button is greyed out on macOS. This was flagged in the `enriques-hq-smoothing-2026q3-e1` critique and remains open.

---

## Rectification status — 2026-05-23

**Fixed (in-scope, this rect commit):**
- `adversary LOW` (sibling docstring): `tests/test_styles_palette.py:801` updated from "Render Mode groups" → "Display & Quality groups" with a milestone-id citation noting the lineage. Caught by the adversary's audit of all "Render Mode" mentions across the test suite after the rename; the docstring uses present tense ("that this milestone closed") so the stale group name was actively misleading rather than historical context.

**Deferred (out-of-scope or follow-on):**
- `HIGH` (process / diff-size auto-finding): 595-line diff is 65% artifact inflation; production+test delta is 208 lines, squarely in the well-reviewed range. No code action — acknowledged.
- `MEDIUM-1` (compound header breaks single-noun peer rhythm): the critic explicitly offers two paths — (a) accept the asymmetry as a consciously chosen trade-off (label precision > rhythm uniformity), or (b) rename all four Appearance dock group headers to compound forms ("Surface Colors", "Surface Opacity", "Surface Shading"). Choosing Path (a) here: the heterogeneous group contents genuinely warrant the compound label, and a panel-wide consistency pass is its own milestone scope. Track Path (b) as `appearance-panel-compound-header-consistency-2026q3-e4` if user feedback validates the rhythm-break concern.
- `LOW-1` ("Quality" ambiguity): the per-button tooltips on Wireframe / Show edges / Double-pass smooth already resolve any ambiguity on hover. `AA_EnableToolTipsOnDisabledWidgets` is already set at `app.py:1152` (from `enriques-hq-smoothing-2026q3-e1`), so the tooltip remains visible even when the Double-pass-smooth button is greyed out at first launch. No additional action needed.

**Invalidated:** none.

**Test count:** 385 (unchanged — no new tests, one docstring update).
