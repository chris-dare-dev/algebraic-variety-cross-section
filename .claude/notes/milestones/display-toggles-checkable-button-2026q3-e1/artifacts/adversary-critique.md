# Adversary critique — QCheckBox → checkable QPushButton display-toggle migration

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** `display-toggles-checkable-button-2026q3-e1`, commit `bb8c369..2f60b93`

---

## Executive summary

The most notable process finding is a mandatory review-quality-at-risk HIGH: the total diff is 995 lines, though 642 of those (65%) are milestone artifact inflation — the functional code delta is 333 LOC. Zero CRITICALs and zero code-path HIGHs. The sole MEDIUM is an Axis 7 test-guard weakness: the positive regression guard `test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox` uses single-occurrence checks for `setCheckable(True)` and `setProperty("role", "display-toggle")`, meaning a partial-migration regression (one of the two buttons reverted while the other retains the sentinel string) would pass the test. Two LOWs cover a stale `_cb` attribute-name convention and an unverified `text-align: left` platform interaction. All AI invariants (AI-1 through AI-15) are clean. SHIP-WITH-FIXES: the MEDIUM is a pre-existing test-guard pattern in this test file (single-`in` vs. count), not a live bug, so the fix is lightweight.

---

## Critical findings (must-fix before this can ship)

None.

---

## High findings (should-fix this iteration)

### HIGH — Review-quality-at-risk: diff exceeds 400 LOC

**Where:** no specific file (process finding)
**Evidence:** `git diff bb8c369..2f60b93 | wc -l` = 995. Code files (`appearance_panel.py`, `styles.py`, `tests/test_styles_palette.py`, `CONTEXT.md`) account for 333 LOC; milestone artifact files (`.claude/notes/milestones/display-toggles-checkable-button-2026q3-e1/`) add 642 LOC (65% of total). Per Cisco/LinearB defect-detection research, diffs over 400 LOC have measurably lower review yield.
**Why it matters:** Automatic finding per the adversary-critique checklist. Non-waivable. In this specific diff the code delta is well under 400 lines and the inflation is purely documentation — no code action required.
**Suggested fix:** No code change needed. The finding is logged as required. The disposition is "process compliant; artifact inflation confirmed."
**Regression-guard test:** No code regression guard needed; the artifact generation is external.

---

## Medium findings (nice-to-fix)

### MEDIUM — Positive regression guard uses single-occurrence check; misses partial-button regression

**Where:** `tests/test_styles_palette.py:805` and `tests/test_styles_palette.py:810`
**Evidence:** `assert "setCheckable(True)" in src` and `assert 'setProperty("role", "display-toggle")' in src` are single-occurrence checks (`in` not `count`). If a future refactor reverts `_wireframe_cb` to a non-checkable QPushButton while leaving `_edges_cb` intact (or vice versa), the single `setCheckable(True)` from the surviving button causes the assertion to pass. The negative assertions (`'QCheckBox("Wireframe")' not in src`, `'QCheckBox("Show edges")' not in src`) are correctly button-specific and would catch a full reversion, but they do not catch the half-migration scenario where QPushButton syntax is retained but `setCheckable(True)` is dropped from one instance.
**Why it matters:** The regression guard is the only AI-2-compliant test for the widget-type contract. A partial regression (one non-checkable display-toggle button) would be invisible to the suite — the button would render as a non-sticky push button with no active-state indicator, silently re-introducing the F-M2 UX problem for one of the two toggles.
**Suggested fix:** Change the positive assertions to count-based checks: `assert src.count("setCheckable(True)") >= 2` and `assert src.count('setProperty("role", "display-toggle")') >= 2`. This matches the two-button construction pattern and catches half-migration regressions.

---

## Low findings (cosmetic / future iteration)

### LOW — `_wireframe_cb` / `_edges_cb` naming convention is historically inaccurate post-migration

**Where:** `appearance_panel.py:185` and `appearance_panel.py:193`
**Evidence:** The attributes `self._wireframe_cb` and `self._edges_cb` use the `_cb` suffix conventionally associated with `QCheckBox` (abbreviation "cb"). They now hold `QPushButton` instances. The naming was intentionally preserved per the commit message ("attribute names `_wireframe_cb` / `_edges_cb` are preserved across the migration so `refresh_icons` and `apply_to_actor` need no update"). There are 23 reference sites across `appearance_panel.py`, `render-panel-chrome.py`, and docstrings.
**Why it matters:** Future contributors reading `self._wireframe_cb.setIcon(...)` may assume QCheckBox semantics and reach for `checkState()` or `stateChanged` instead of `isChecked()` and `toggled`. The mismatch is strictly a readability/maintainability concern — no runtime impact.
**Suggested fix:** Either rename to `_wireframe_btn` / `_edges_btn` across all 23 sites in a dedicated micro-commit (trivial but broad), or add a one-line comment at the attribute declaration: `# QPushButton(checkable=True); _cb suffix is historical — see CONTEXT.md §8.15`. The comment approach is lower risk for a single-developer workflow.

### LOW — `text-align: left` on `QPushButton` in QSS: not verified across macOS platform styles

**Where:** `styles.py:509`
**Evidence:** `QPushButton[role="display-toggle"]` includes `text-align: left;`. This is a documented QSS property for QPushButton per Qt 6 reference. The concern is that on macOS without an explicit `app.setStyle("Fusion")` call, the native macOS QPushButton widget may center-align text regardless of QSS. However, because the rule also sets `background: transparent` and `border: 1px solid transparent` — explicit QSS properties that trigger `QStyleSheetStyle` to take over full widget painting — the `text-align` directive is almost certainly honored. No visual regression has been reported and `render-panel-chrome.py` captures both checked and unchecked states.
**Why it matters:** If the native macOS style overrides `text-align` despite the `QStyleSheetStyle` trigger, the button text ("Wireframe", "Show edges") would appear center-aligned instead of icon-aligned-left, breaking visual consistency with the prior QCheckBox layout.
**Suggested fix:** Optionally add a smoke test in `render-panel-chrome.py`'s post-capture hash-check section that notes the expected text-left alignment, or document the behavior in `CONTEXT.md §8.15` as explicitly tested under macOS + PySide6. No code change required if visual scout captures confirm the left-aligned rendering.

### LOW — Vertical rhythm regression from QPushButton height vs QCheckBox height not explicitly tested

**Where:** `styles.py:505` (`padding: 3px 8px`)
**Evidence:** `QPushButton` with `padding: 3px 8px` and a `16x16` icon renders at approximately 22–24 px total height on macOS. The `QCheckBox` it replaces typically renders at 18–20 px (indicator + icon-size label). The "Display" group box in the Appearance dock may be 4–8 px taller after the migration. No height regression guard exists; the `render-panel-chrome.py` captures will show any change, but no pixel-height assertion is in the test suite.
**Why it matters:** The height increase is minor and does not affect usability. The concern is that a tighter dock layout elsewhere (if future panels are added above or below "Display") could have less breathing room. This is a cosmetic forward-risk, not a blocking issue.
**Suggested fix:** Document the approximate button height in `CONTEXT.md §8.15` as part of the implementation pattern, or add a `min-height`/`max-height` constraint in the QSS rule if strict vertical-rhythm matching is required. Not blocking.

---

## What was done well

- **Complete QCheckBox removal with zero orphaned import.** The `QCheckBox` import was cleanly removed from `appearance_panel.py:17` (post-migration line count) with a grep-verified clean result: no remaining QCheckBox widget construction anywhere in `appearance_panel.py`. The only remaining QCheckBox references are in inline comments explaining the migration history — exactly right.
- **Attribute names preserved for zero-diff API surface.** `_wireframe_cb` and `_edges_cb` retained their names, meaning `refresh_icons()`, `apply_to_actor()`, and `render-panel-chrome.py` required zero changes. The shared `QAbstractButton` API (`setIcon`, `setIconSize`, `toggled`) was exploited correctly.
- **Capture script wired before this milestone landed.** `render-panel-chrome.py:335–336` correctly calls `_wireframe_cb.setChecked(True)` and `_edges_cb.setChecked(True)` followed by `refresh_icons(theme_name)` at line 339 — the checked state is visually captured. This was set up by the prior `qtawesome-icons-2026q2-e2` rect M1 commit, and the current milestone correctly notes it needs no change.
- **All four QSS pseudo-states covered with precise WCAG attribution.** The rule block covers unchecked, `:hover`, `:checked`, and `:checked:hover`, with the `:checked:hover` state correctly retaining the `2px solid FOCUS_RING` border (the WCAG 1.4.11 carrier) while reverting the fill to the hover tint. The WCAG obligation is on the border, not the fill — the design is correct and the comment in styles.py:496–502 makes this explicit.
- **BG_TOGGLE_CHECKED token isolation.** The new token flows through `palette["BG_TOGGLE_CHECKED"]` in `_render_stylesheet` — zero raw hex in the QSS template. The `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` test, which is not a new test, will verify this on every run.
- **AI-13 guard test is per-palette and per-theme.** `test_bg_toggle_checked_token_is_six_digit_hex_in_both_palettes` checks PALETTE_LIGHT and PALETTE_DARK independently, AND adds a cross-theme inequality assertion (same value in both palettes would produce a near-invisible checked state in one theme). This three-in-one check is efficient and directly prevents the most likely misconfiguration.
- **Dead-token guard prevents silent no-op.** `test_bg_toggle_checked_value_appears_in_both_stylesheets` catches the "token declared but not consumed by any QSS rule" scenario. This pattern of verifying token presence in the rendered stylesheet (not just the palette dict) is the correct approach and mirrors the established suite convention.
- **Signal loop analysis documented.** The commit message explicitly notes that `_on_wireframe_toggled` and `_on_edges_toggled` never call `setChecked()` back on the button — the signal-loop re-entrancy risk (which would be an AI-9 concern) is ruled out by construction, and that analysis is recorded.
- **CONTEXT.md §8.15 is fully self-contained.** The new section documents the migration rationale, the implementation pattern (including the `setFlat(False)` non-goal), the checked-state WCAG design, and the test-guard inventory — everything a future agent needs to either repeat the pattern or safely refactor. The `text on checked fill` contrast ratios (9.89:1 light, 10.20:1 dark) are cited with arithmetic verifiable from the palette values.
- **view_panel QCheckBoxes correctly left untouched.** The four view_panel checkboxes (`_domain_overlay_cb`, `_axes_cb`, `_bbox_cb`, `_grid_cb`) are text-only (no `setIcon` calls) — the triple-prefix defect does not apply to them. Leaving them as QCheckBox is the correct call per the `CONTEXT.md §8.15` rule ("use plain QCheckBox only for text-only toggles where the check-square IS the intended affordance").

---


## Cross-critic agreement

The following findings cluster within 5 lines of each other in the same file. Multiple critics flagged the same area -- these are the strongest signals to fix first.

- **L3, L2** at `styles.py:505-509` (LOW): Vertical rhythm regression from QPushButton height vs QCheckBox height not explicitly tested; `text-align: left` on `QPushButton` in QSS: not verified across macOS platform styles

## Recommended rectification order

1. **Fix the MEDIUM (test guard).** Change `assert "setCheckable(True)" in src` → `assert src.count("setCheckable(True)") >= 2` and `assert 'setProperty("role", "display-toggle")' in src` → `assert src.count('setProperty("role", "display-toggle")') >= 2` in `test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox`. Two lines; no other test changes needed.
2. **LOWs at maintainer discretion.** Rename `_wireframe_cb`/`_edges_cb` or add a naming comment; verify `text-align: left` via a visual-scout run and document the result in `CONTEXT.md §8.15`; optionally add a height comment to the QSS rule. None of these block ship.

---

*End of critique. Mandatory rectification: none (zero CRITICALs); MEDIUM test-guard fix is strongly recommended before milestone close to preserve regression guard integrity.*

---

## Frontend UI/UX findings

*Merged from `frontend-critique.md`. Qt-panel critic emitted 0 CRITICAL, 0 HIGH, 3 MEDIUM, 2 LOW. Severity-ids prefixed with `F-`.*

### MEDIUM — F-M1: unchecked ghost-button style diverges from industry peer off-state convention

**Where:** `styles.py` `QPushButton[role="display-toggle"]` base rule
**Evidence:** Unchecked state is `border: 1px solid transparent; background: transparent`. Blender 4.x N-panel viewport overlay uses visible-background rgba darkening even when off; 3D Slicer 5.x has raised-style visible borders in inactive state; ParaView's plain `QCheckBox` has always-visible check-square. In all three peers, the interactive affordance is visible BEFORE hover. In this implementation, the affordance is only revealed on hover or via keyboard tab-stop.
**Why it matters:** A researcher opening the Appearance dock for the first time sees "Wireframe" and "Show edges" as what appears to be plain icon+label strings — no visual signal that these are clickable controls. Mouse-first users must discover by hover or accident; keyboard-first users get the focus ring. This is exactly the discoverability problem the migration was supposed to solve, just shifted from "two competing affordances" to "no visible affordance at rest."
**Suggested fix:** Add a minimal off-state border + slight background tint to the unchecked rule — e.g. `border: 1px solid {palette["BORDER_CAMERA_BTN"]}; background: transparent`. The camera-button border is already established for outlined controls and intentionally below 3:1 as a structural separator. This mirrors the Blender/Slicer convention without introducing a new token.

### MEDIUM — F-M2: `text-align: left` misaligns display-toggle buttons with adjacent Colors-group buttons

**Where:** `styles.py` `QPushButton[role="display-toggle"]` base rule, `text-align: left`
**Evidence:** Appearance-panel layout order: Colors group (Surface…, Background… buttons — Qt default center-aligned) → Display group (Wireframe, Show edges — explicitly left-aligned) → Opacity → Shading. The result: vertically adjacent groups where buttons in one are center-aligned and buttons in the next are left-aligned. On a narrow panel (~200px min width) this is visually jarring.
**Why it matters:** `text-align: left` is the correct choice for icon+label display toggles (icon anchors left, text follows), but the mismatch with the Colors-group buttons (which have no icons currently but still center-align) creates a vertical-rhythm fracture across group boundaries. Blender N-panel and ParaView Properties keep consistent left-alignment for all icon-bearing controls within a section.
**Suggested fix:** Two paths: (a) extend `text-align: left` to the global `QPushButton` rule so all buttons are uniformly left-aligned, or (b) explicitly center-target the `text-align: left` to the display-toggle role only (which is what we have — but accept the inter-group inconsistency). Option (a) is the broader change and could regress the Reset Defaults / Reset Camera button visuals; option (b) is the safer scope and the inconsistency is a forward-risk, not a current-render bug. **Recommendation: defer to a future Appearance-panel layout-pass milestone** where the Colors-group buttons can be redesigned with consistent icon-bearing left-alignment as a coherent batch — out of v0 scope for this milestone.

### MEDIUM — F-M3: WCAG annotation omits the more informative FOCUS_RING-vs-fill contrast pair

**Where:** `styles.py` PALETTE_LIGHT / PALETTE_DARK BG_TOGGLE_CHECKED comments + the QSS rule comment
**Evidence:** Existing annotation: "its contrast vs the hover tint is ~1.10:1 by design (state communicated by border, not fill)." Accurate but incomplete. The more informative pair for WCAG-understanding is FOCUS_RING border vs BG_TOGGLE_CHECKED fill: measured 3.17:1 (light) / 4.55:1 (dark) — above the 3:1 floor in BOTH themes. A future maintainer reading "1.10:1 by design" may incorrectly conclude the fill region is contrast-problematic without understanding that the active-state border reads against its own interior fill, not just against the panel ground.
**Why it matters:** Incomplete contrast annotations have caused two prior misreadings in this codebase (panel-refresh-2026q2-e2 off-by-0.6-2.3, focus-ring-contrast PALETTE_DARK headroom regression). Annotation hygiene is institutional memory.
**Suggested fix:** Extend the annotation to also cite the FOCUS_RING vs BG_TOGGLE_CHECKED ratios (3.17:1 light / 4.55:1 dark — both clear 3:1, documenting that the active indicator reads against its own interior fill). Documentation-only; no code change.

### LOW — F-L1: 1px content-shift jitter when toggling between unchecked (`border: 1px transparent`) and checked (`border: 2px FOCUS_RING`)

**Where:** `styles.py` display-toggle pseudo-state rules
**Evidence:** Qt's QPushButton box model adds border width outside the content box. The 1px → 2px border-width change shifts content ~1px when the user clicks the toggle (most noticeable on Retina/HiDPI when rapidly clicking).
**Suggested fix:** Two options: (a) compensate padding in the checked rule (e.g. `padding: 2px 7px` to offset the 1px border growth on each side), or (b) use `outline: 2px solid FOCUS_RING` instead of changing `border-width` — `outline` renders outside the box model and never shifts content. Option (b) is cleaner and mirrors the existing `QAbstractButton:focus` mechanism. **Recommended: option (b).**

### LOW — F-L2: "Display" group header is generic; Blender uses "Overlay" / "Shading", 3D Slicer uses "Display Type"

**Where:** `appearance_panel.py:_build_toggles_group` — `QGroupBox("Display")`
**Evidence:** Current layout has flat groups Colors / Display / Opacity / Shading. The "Display" name is generic for the Wireframe + Show-edges pair; as the panel gains more controls (future back-face-culling toggle, grid overlay, etc.), the distinction between "style mode" controls and "appearance quantity" controls will blur.
**Suggested fix:** Rename to "Render Mode" or "Surface Style" — one-character diff with no layout impact. Defer if scope is tight.

---

## Combined rectification order

1. **F-M1 (MEDIUM — discoverability):** Add `border: 1px solid {palette["BORDER_CAMERA_BTN"]}` to the unchecked rule so the affordance is visible at rest. Industry-aligned with Blender/Slicer/ParaView. Single-line QSS change.
2. **F-L1 (LOW — 1px jitter):** Switch checked-state from `border: 2px` to `outline: 2px` to eliminate the 1px content shift. Same WCAG-bearing FOCUS_RING color; just renders outside the box model. Cascades naturally with the existing `QAbstractButton:focus` mechanism. Single-line QSS change; batch with F-M1.
3. **M1 (adversary MEDIUM — count-based test guard):** Replace `assert "setCheckable(True)" in src` with `assert src.count("setCheckable(True)") >= 2` (and same for the role property). 2-line fix; catches half-migration regressions.
4. **F-M3 (MEDIUM — WCAG annotation completeness):** Extend palette + QSS comments to cite the 3.17:1 / 4.55:1 FOCUS_RING-vs-BG_TOGGLE_CHECKED ratios. Documentation-only.
5. **Deferred:**
   - **F-M2** — `text-align` cross-group inconsistency. Real but the fix requires a coordinated Appearance-panel layout pass (Colors-group buttons would need icon+left-align treatment too). Out of v0 scope; open as `appearance-panel-layout-pass-2026q3-e1` for a coherent batch.
   - **F-L2** — "Display" → "Render Mode" rename. Defer to the same layout-pass milestone.
   - **L1, L2, L3** (adversary LOWs) — `_cb` naming, `text-align` platform note, vertical-rhythm height comment. Polish; defer.
6. **H1** — process-only (995-LOC diff, 65% artifacts). No code action.

---

## Rectification status (orchestrator, 2026-05-22)

**Fixed in rect commit:**

- **F-M1 (frontend MEDIUM, discoverability)**: Replaced `border: 1px solid transparent` with `border: 1px solid {palette["BORDER_CAMERA_BTN"]}` in the unchecked rule. Display toggles now show a visible 1px outline at rest — mouse-first users see the affordance without needing to hover. Reuses the existing BORDER_CAMERA_BTN token (no new palette entry). Industry-aligned with Blender N-panel viewport-shading and 3D Slicer modules-panel inactive-state convention.

- **F-L1 (frontend LOW, 1px jitter)**: Replaced the `:checked` and `:checked:hover` border-width change (1px → 2px) with `outline: 2px solid FOCUS_RING; outline-offset: -1px` on top of a static 1px border. `outline` renders outside the QPushButton box model and never shifts content. The negative `outline-offset` keeps the outline visually inside the border-frame so the active-state indicator hugs the button rather than floating. This is the same mechanism the existing `QAbstractButton:focus` rule uses — natural QSS cascade.

- **M1 (adversary MEDIUM, count-based test guard)**: Replaced `assert "setCheckable(True)" in src` with `assert src.count("setCheckable(True)") >= 2`, and same pattern for `setProperty("role", "display-toggle")`. The previous single-`in` check let a half-migration regression (one toggle reverted, the other intact) pass silently because one surviving sentinel string was enough. Count-based guard fires loudly on any non-2 occurrence. Error message names the half-migration scenario so a future maintainer reading the failure understands the architectural intent.

- **F-M3 (frontend MEDIUM, WCAG annotation completeness)**: Extended both PALETTE_LIGHT and PALETTE_DARK BG_TOGGLE_CHECKED comments AND the QSS rule comment to cite the FOCUS_RING-vs-BG_TOGGLE_CHECKED contrast pair (3.17:1 light / 4.55:1 dark). Both clear the 3:1 floor, documenting that the active-state indicator reads against EITHER the panel ground OR its own interior fill. This closes the annotation gap that has produced two prior misreadings in this codebase (panel-refresh-2026q2-e2 off-by-0.6-2.3, focus-ring-contrast PALETTE_DARK headroom regression).

**Deferred (out of v0 scope):**

- **F-M2 (frontend MEDIUM, text-align cross-group inconsistency)**: Real but the fix requires a coordinated Appearance-panel layout pass — the Colors-group buttons (Surface…, Background…) would need icon-bearing + left-align treatment too for visual coherence. Out of this milestone's surgical-substitution scope. Open as `appearance-panel-layout-pass-2026q3-e2` for a coherent batch where the entire panel's icon-and-text-alignment story is redesigned together.

- **F-L2 (frontend LOW, "Display" → "Render Mode" rename)**: Polish-pass scope. Defer to the same layout-pass milestone as F-M2.

- **L1, L2, L3 (adversary LOWs, naming + platform note + height comment)**: `_cb` attribute naming is historical but no runtime impact (handlers use `isChecked()` / `.toggled` which work on both QCheckBox and QPushButton; this is the SAME attribute name reused for the new widget type). `text-align: left` platform interaction is the kind of thing best caught by visual-scout PNG captures rather than by a code-level test. Vertical-rhythm height delta is a forward-risk only. All defer.

**Process-only:**

- **H1 (adversary HIGH, 995-LOC diff)**: ~65% milestone documentation artifacts; code delta is 333 LOC. No code action.

**Invalidated:** none — all four code-actionable findings (F-M1, F-L1, M1, F-M3) re-verified present before fixing.

**Test suite:** 336 passed (no regressions — the test surface didn't change in rectify, only the code under test).

**Architecture lessons recorded:**

1. *"Outline, not border-width, for state changes"* — the F-L1 finding plus the existing `QAbstractButton:focus` rule both use this pattern. Now documented in the QSS comment block in styles.py so future maintainers picking up the role-property pattern know to prefer `outline:` over `border-width:` changes.

2. *"Visible chrome at rest"* — the F-M1 finding crystallized the industry-convention insight that interactive controls should be visible BEFORE hover. The unchecked-with-visible-border pattern is now the canonical baseline for any future role-property-driven button styling.

3. *"Cite all adjacent-surface contrast pairs"* — the F-M3 annotation pattern (border-vs-panel + border-vs-fill) is the right scope for WCAG documentation when the indicator sits on a non-panel adjacent surface. Apply to any future tokens with similar layered visual treatment.
