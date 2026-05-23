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
