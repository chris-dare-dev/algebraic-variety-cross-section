# Adversary critique — qtawesome-icons-2026q2-e2 (v1 camera-preset + display-toggle icons)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** `930392e..HEAD` (commit `4c72cee`) — `feat(qtawesome-icons-2026q2-e2): extend qtawesome to camera-preset buttons + display toggles (v1)`

---

## Executive summary

The headline finding is a MEDIUM process gap: the capture script
`render-panel-chrome.py` does not call `appearance_panel.refresh_icons(theme_name)` on either
the `appearance_empty` or `appearance_populated` instances, so the panel-chrome PNGs for the
Appearance panel will show iconless Wireframe and Show-edges checkboxes — contradicting the live
app and falsifying §8.12's claim that the capture script "mirrors this discipline."  The mandatory
HIGH is the auto-finding for diff size (1054 lines, ~53% milestone artifacts; no code action
required, but non-waivable).  No CRITICALs.  One HIGH (auto), two MEDIUMs, two LOWs.  The
code itself is sound: AI-1 through AI-15 are all clean, all 9 new icon factories use
verified `mdi6.*` names, mock tests cover both themes for every new function, and `rotated=180`
is correctly scoped to the minus-direction presets only.  Safe to merge after M1 and M2 rectify.

---

## Critical findings

None.

---

## High findings

### HIGH — Review-quality-at-risk: diff exceeds 400 LOC

**Where:** no specific file
**Evidence:** `git diff 930392e..HEAD | wc -l` = 1054 lines across 11 files.  Code and test
content (icons.py, view_panel.py, appearance_panel.py, app.py, tests/test_icons.py, CONTEXT.md)
accounts for ~493 lines (~47%); the remaining ~561 lines (~53%) are milestone-artifact files
(research brief at 425 lines, state.json, dispatch.log, implementation plan, researcher
lessons.md).
**Why it matters:** Cisco and LinearB defect-detection research establishes that human reviewers
reliably miss bugs above 400 total diff lines; this threshold is set in the checklist as a
non-waivable auto-finding.
**Suggested fix:** No code change required.  The artifact inflation is the dominant driver; the
code delta alone (~493 lines) is well within the 400-line zone.  Disposition: no code action
needed — log the auto-finding and proceed to merge after M1 and M2 close.
**Regression-guard test:** Not applicable (process finding, not a code defect).

---

## Medium findings

### MEDIUM — Capture script misses `refresh_icons` for AppearancePanel — icons won't appear in panel-chrome PNGs

**Where:** `.claude/scripts/frontend-uplift/render-panel-chrome.py:293-340`
**Evidence:** Lines 350 and 375 call `view_empty.refresh_icons(theme_name)` and
`view_populated.refresh_icons(theme_name)`; lines 400 and 420 call the same for params
instances.  The AppearancePanel block (lines 293–340) constructs `appearance_empty` and
`appearance_populated` but contains no `refresh_icons` call on either instance before the
`_grab_in_dock` calls.
**Why it matters:** The visual-scout captures for the Appearance panel will show bare text
checkboxes ("Wireframe", "Show edges") with no icons — the live app shows `mdi6.grid` and
`mdi6.border-outside` glyphs.  This creates a false baseline that will cause the next
frontend-uplift agent to flag "missing icons" on a milestone that has already shipped them.
Additionally, CONTEXT.md §8.12 asserts "The capture script `render-panel-chrome.py` mirrors
this discipline (calls `refresh_icons` after each panel construction)" — that claim is now
factually wrong for AppearancePanel.
**Suggested fix:** Add `appearance_empty.refresh_icons(theme_name)` immediately after line 296
(construction of `appearance_empty`) and `appearance_populated.refresh_icons(theme_name)`
immediately after line 325 (construction of `appearance_populated`), matching the comment
pattern already used for the view and parameters blocks.  Update §8.12 to add
`appearance_panel.py:refresh_icons` to the reference list alongside `view_panel.py` and
`parameters_panel.py`.
**Regression-guard test:** Add a `grep`-based assertion in the capture script's module-level
comment block (or a companion shell test) that errors if `appearance_empty.refresh_icons` is
absent from the script body — identical to the existing view/params note at line 346.

### MEDIUM — `_iso_btn is not None` guard is paranoid given unconditional construction

**Where:** `view_panel.py:424`
**Evidence:** `self._iso_btn` is initialised to `None` at line 71, then unconditionally set to
a `QPushButton` in `_make_view_presets_group` at line 140, which is called unconditionally from
`_build_ui` at line 84, which is called unconditionally from `__init__` at line 73.  There is
no code path in which `refresh_icons` is callable before `_iso_btn` has been promoted to
a `QPushButton`.  The `if self._iso_btn is not None:` guard at line 424 therefore silently
succeeds on every live invocation.  The same analysis applies to `_preset_btns.get(label)`:
all 6 labels present in `_PRESET_ICON_FACTORIES` are unconditionally added by the
`for label, row, col, method, tip in presets:` loop at line 131 — the `.get` can never return
`None` for any of the six keys.
**Why it matters:** Defensive patterns that can never fire are Axis-10 scope-discipline
violations (CONTEXT.md §12: "no defensive error handling for scenarios that can't happen —
trust internal code").  More concretely, the `if btn is not None:` branch silently swallows
a hypothetical future refactor where `_make_view_presets_group` is made conditional, masking
a regression instead of crashing loudly.  The `.get` with `is not None` check suggests the
dict might be sparsely populated, which is misleading to future readers.
**Suggested fix:** Replace `self._preset_btns.get(label)` with `self._preset_btns[label]`
(KeyError is the correct signal if a label goes missing) and replace `if self._iso_btn is not
None:` with a direct `self._iso_btn.setIconSize(...)` / `self._iso_btn.setIcon(...)` call
(the `None` guard is noise).

---

## Low findings

### LOW — CONTEXT.md §8.12 reference list omits `appearance_panel.py:refresh_icons`

**Where:** `CONTEXT.md:396`
**Evidence:** §8.12 reads "see [`view_panel.py:refresh_icons`](view_panel.py) /
[`parameters_panel.py:refresh_icons`](parameters_panel.py)" — `appearance_panel.py` is the
third panel that now exposes `refresh_icons` (added by this milestone), but it is absent from
the link list.
**Why it matters:** A future maintainer reading §8.12 to understand the refresh_icons pattern
sees only two of three panels; the AppearancePanel extension remains invisible in the
institutional record.  This is the slower kind of doc drift — not wrong today, just incomplete.
**Suggested fix:** Extend the reference list to "… / [`appearance_panel.py:refresh_icons`](appearance_panel.py)" to complete the three-panel picture.  (Note: this LOW and MEDIUM M1 above share a root cause; batching the §8.12 fix with M1 is the efficient path.)

### LOW — `icons.py` module docstring still carries the original `camera-retake` name in the top-level file docstring `__doc__` history

**Where:** `icons.py:1` (module docstring)
**Evidence:** The file docstring opening line reads `"""Icon factory for Algebraic Variety Viewer
(qtawesome-icons-2026q2-e1, UPL-4)."""` — the module was created in e1 but is now extended in
e2.  The milestone tag is thus stale as a "last-updated" marker, though the per-section headers
inside the module (`# v0`, `# v1`) already attribute the two phases correctly.
**Why it matters:** Stale milestone tags in module docstrings cause confusion in `git log
--follow`-style archaeology when a developer searches for which commit introduced a function.
The description is a cosmetic issue, not functional.
**Suggested fix:** Update the opening line to `(qtawesome-icons-2026q2-e1/e2, UPL-4 v0/v1)` or
simply remove the milestone tag from the module-level docstring (the per-section headers and
`CONTEXT.md §3` are the canonical attribution — the module docstring does not need to track it).

---

## What was done well

- **Lazy-import discipline preserved exactly.** The 9 new factory functions all call
  `_get_qta()` (the existing lazy sentinel), never importing `qtawesome` at module scope.  The
  existing `test_icons_module_does_not_import_qtawesome_at_module_load` test continues to
  enforce this without any modification needed.

- **Dual-theme coverage in every new mock test.** All three new mock tests
  (`test_v0_icons_still_bind_correctly`, `test_camera_preset_icons_correct_names_and_colors`,
  `test_display_toggle_icons_correct_names_and_colors`) loop over `("dark", "light")` with
  `mock_qta.icon.reset_mock()` between iterations.  This closes the theme-coverage gap flagged
  as a pattern in the prior lesson (a single theme per function leaves half the color-routing
  logic untested).

- **`rotated=180` scoping is precise and correctly documented.** The kwarg appears on exactly
  the three minus-direction factories (`preset_minus_x_icon`, `preset_minus_y_icon`,
  `preset_minus_z_icon`); the isometric icon and both display-toggle icons are correctly kwarg-free.
  The docstrings for each minus factory explain why MDI6 has no separate "left-arrow" variant
  and cite the qtawesome 1.4.x docs as authority for the rotation approach.

- **AI-9 is clean.** `refresh_icons` in both `view_panel.py` and `appearance_panel.py` calls
  only `setIcon` / `setIconSize`, which are synchronous Qt property setters.  No
  `processEvents`, no `QMovie`, no timer.  The deferred spinner rationale is documented in
  both the module docstring and CONTEXT.md §9 with the exact AI-9 surface that makes it
  non-trivial — a future v2 implementer has the information they need.

- **Button-promotion preserves all v0 bindings.** The `test_v0_icons_still_bind_correctly`
  test directly verifies that the v0 factory names and icon names are unchanged after the v1
  refactor.  This is the exact regression-guard pattern recommended by the prior milestone's
  adversary critique.

- **`_wireframe_cb` and `_edges_cb` are genuine instance attrs — no promotion needed.**
  Both attributes are assigned unconditionally in `_build_toggles_group` (appearance_panel.py
  lines 167, 173), which is called from `_build_ui` at line 128.  The implementation correctly
  identifies that no promotion work is needed here (unlike the view-preset buttons, which
  required promotion from loop-locals).

- **CONTEXT.md §9 wording is correct.** The updated bullet accurately reflects the post-v1
  state: the spinner remains deferred (v2), and the claim that "camera-preset and display-toggle
  icons closed in v1" is true.  The wording "deferred beyond `qtawesome-icons-2026q2-e2`"
  correctly expresses that v2 is a future milestone, not an active scope item.

- **Module-level constants `WIREFRAME_ICON_NAME` / `SHOW_EDGES_ICON_NAME` exposed for testability.**
  Exporting these constants so `test_wireframe_and_edges_icons_are_distinct_names` can assert
  directly on them (rather than scraping docstrings) is a clean API discipline that makes the
  "these two icons must differ" invariant machine-checkable.

---

## Recommended rectification order

1. **Fix M1 (capture script + §8.12 documentation) first** — add `appearance_empty.refresh_icons(theme_name)` and `appearance_populated.refresh_icons(theme_name)` to `render-panel-chrome.py` after each AppearancePanel construction, and update §8.12 to include `appearance_panel.py:refresh_icons` in the reference list.  These are the same two-sentence change; batch them in one commit.
2. **Fix M2 (paranoid guards in view_panel.py:refresh_icons)** — replace the `.get(label)` + `is not None` pattern with direct `[]` indexing, and replace the `_iso_btn is not None` guard with a direct call.  Single-function change, low risk.
3. **Fix L1 alongside M1** — the §8.12 reference list extension for AppearancePanel shares the same file and the same edit session as M1; batch them.
4. **L2 (module docstring milestone tag) is optional** — address at maintainer's discretion; it has no functional impact.

---

*End of critique.  Mandatory rectification: H1 (auto-finding, no code action needed), M1, M2.  L1 is recommended alongside M1.  L2 is optional.*

---

## Frontend UI/UX findings

*Merged from `frontend-critique.md`. Qt-panel critic emitted 0 CRITICAL, 0 HIGH, 2 MEDIUM, 3 LOW. Severity-ids prefixed with `F-`.*

### MEDIUM — F-M1: rotated 180° axis-label glyphs are illegible at 16px

**Where:** `icons.py` `preset_minus_{x,y,z}_icon`
**Evidence:** MDI6 `axis-{x,y,z}-arrow` embeds the X/Y/Z label as part of the glyph. At 16px the label character is ~4-5px tall. Rotated 180°, the "X" stays recognizable (~axis-symmetric), but "Y" rotated 180° looks like λ and "Z" rotated 180° looks like S (rotational symmetry of the Latin glyph at low resolution). Blender 4.x uses distinct per-direction SVGs (no rotation); ParaView uses cube-face glyphs with the facing surface highlighted.
**Why it matters:** Icons are supposed to enable pre-reading recognition. An upside-down ambiguous glyph defeats that purpose for the minus directions; users will fall back to reading the text label ("-Y"), which is exactly what icons were added to avoid.
**Suggested fix:** Two paths: (a) replace minus icons with rotation-independent glyphs (e.g. `mdi6.arrow-left-bold` for -X), losing the axis-label embed but gaining glyph clarity; (b) accept with documented comment in `icons.py` if the button text label is judged sufficient disambiguation.

### MEDIUM — F-M2: QCheckBox icon placement creates `[check][icon][label]` triple prefix

**Where:** `appearance_panel.py:_build_toggles_group` + `refresh_icons`
**Evidence:** `QCheckBox.setIcon()` renders the icon between the check indicator and the text label — visual order: `☐ [grid-icon] Wireframe`. No peer scientific-viz app uses this pattern: Blender uses checkable QPushButton with icon (no separate check-square); ParaView uses plain text checkboxes (no icon); 3D Slicer uses checkable QPushButton with paired ON/OFF icons. The triple-prefix can read as two competing affordances (check OR icon).
**Suggested fix:** Two paths: (a) move icon to a companion `QLabel` to the left of the checkbox (`[icon] ☐ [text]`); (b) migrate the two toggles to `QPushButton(checkable=True)` (Blender/Slicer precedent — eliminates the check-square indicator entirely, icon becomes the primary affordance). Path B is the cleaner long-term fix but is a non-trivial widget-type change touching `_on_wireframe_toggled` / `_on_edges_toggled` signal wiring + QSS for the checked state.

### LOW — F-L1: Isometric button aesthetic divergence from compact 2-col grid

**Where:** `view_panel.py:_make_view_presets_group` (iso button spans both columns)
**Evidence:** Isometric button is 2-column wide (~210px) at typical dock width; icon at flush-left + "Isometric" label leaves wide empty space between them, reading more like a list item than a click target compared to the compact 2-col ortho grid above.
**Suggested fix:** Polish-pass scope; consider center-aligned icon-only (label moves to tooltip) to match ParaView's compact preset toolbar.

### LOW — F-L2: minus-direction tooltips don't mention rotation strategy for screen readers

**Where:** `view_panel.py` minus-direction button tooltips
**Evidence:** Tooltips read e.g. "Look along the -X axis (shows ZY plane)" — accurate but silent on icon rotation. Screen-reader users get no signal that the inverted glyph mirrors the axis direction.
**Suggested fix:** Append " — icon mirrors the axis direction" to minus-direction tooltips. Accessibility polish.

### LOW — F-L3: `_preset_btns.get()` + None-guard pattern is unreachable but undocumented

**Where:** `view_panel.py:refresh_icons`
**Evidence:** Same observation as adversary M2 from the frontend angle. The guard is dead code as long as `_preset_btns` and `_PRESET_ICON_FACTORIES` stay in sync.
**Suggested fix:** Either remove the defensive pattern (adversary M2's preference) or add a one-line comment explaining the safety-net intent.

---

## Combined rectification order

1. **M1 + L1** (capture script + CONTEXT.md §8.12) — same edit session, batch as one commit.
2. **M2 / F-L3** (paranoid defensive guards in view_panel.py:refresh_icons) — replace `.get()` + `is not None` with direct `[]` indexing. Trust the constructor (Axis-10 scope discipline).
3. **L2** (module docstring milestone tag) — small touch alongside M1's CONTEXT.md edits.
4. **F-M1** (rotated glyph legibility) — **accept-with-documented-comment**. The button text labels ("-X", "-Y", "-Z") are present and the +/- pairs are positioned adjacent in the grid for direct visual comparison. Switching to `mdi6.arrow-*-bold` for minus directions would lose the axis-label embed (the whole reason axis-arrow was preferred over generic arrows per research §B); a hybrid approach (axis-arrow + / arrow- -) would be visually inconsistent. Document the known legibility caveat in `icons.py` so a future maintainer can re-litigate with industry-comparison evidence.
5. **F-M2** (QCheckBox triple-prefix) — **DEFER** to a future milestone (`display-toggles-checkable-button-2026q3-e1` or similar). The migration from QCheckBox to QPushButton(checkable=True) is a real widget-type change touching signal wiring + QSS for the checked-state visual; legitimately deserves its own pipeline run with focused research on the checked-state QSS treatment in both themes.
6. **F-L1** + **F-L2** — defer to a polish pass. Both are real but neither blocks ship.
7. **H1** (diff LOC) — process-only; ~53% milestone artifacts; no code action.

---

## Rectification status (orchestrator, 2026-05-22)

**Fixed in rect commit:**

- **M1 (adversary MEDIUM, capture-script appearance_panel skip):** Added `appearance_empty.refresh_icons(theme_name)` (line ~302) and `appearance_populated.refresh_icons(theme_name)` (line ~331) to `.claude/scripts/frontend-uplift/render-panel-chrome.py`. The capture script now mirrors the live app's icon discipline for ALL three icon-bearing panels. Panel-chrome PNGs will now show the Wireframe `mdi6.grid` and Show-edges `mdi6.border-outside` icons correctly.

- **L1 (adversary LOW, CONTEXT.md §8.12 reference list):** Updated §8.12 to include `appearance_panel.py:refresh_icons` in the panel reference list (the third panel that now exposes `refresh_icons` — added by v1). Also tightened the capture-script verification wording so a future maintainer reading §8.12 has explicit line-number guidance.

- **M2 (adversary MEDIUM, paranoid defensive guards in view_panel.py:refresh_icons):** Replaced `self._preset_btns.get(label)` + `if btn is not None:` with direct `self._preset_btns[label]` indexing. Replaced `if self._iso_btn is not None:` with a direct call. The constructor chain (`__init__` → `_build_ui` → `_make_view_presets_group`) populates both `_preset_btns` (all 6 labels) and `_iso_btn` unconditionally; defensive guards that can never fire are Axis-10 scope-discipline violations per CONTEXT.md §12 ("trust internal code"). Added a 4-line comment block in `refresh_icons` documenting the rationale so a future maintainer doesn't re-introduce the guards out of caution. KeyError/AttributeError now loudly signals constructor-invariant drift rather than silently no-op'ing.

- **L2 (adversary LOW, stale milestone tag in icons.py module docstring):** Updated opening line from `"(qtawesome-icons-2026q2-e1, UPL-4)"` to `"(qtawesome-icons-2026q2-e1/e2, UPL-4 v0/v1)"`. The per-section headers inside the module already attribute the two phases correctly; the docstring opening line now matches.

- **F-M1 (frontend MEDIUM, rotated glyph legibility — accepted with documented comment):** Added a 12-line "known legibility caveat at 16px" block to `icons.py:preset_minus_x_icon` docstring explaining: (a) the X glyph remains recognizable rotated, but Y reads as λ and Z reads as S; (b) the button text labels ("-X", "-Y", "-Z") carry the unambiguous disambiguation; (c) the +/- pair adjacency in the grid layout enables direct visual comparison; (d) the axis-arrow family was preferred over `mdi6.arrow-*` for the embedded axis label, even at the cost of rotation legibility for Y/Z; (e) future migration to ParaView-style cube-face glyphs or Blender-style distinct per-direction SVGs is a polish-pass scope, not a v1 bug. Future maintainers can re-litigate with industry-comparison evidence.

**Deferred (out of v1 scope):**

- **F-M2 (frontend MEDIUM, QCheckBox triple-prefix `[check][icon][label]`):** Real UX observation — Blender, ParaView, and 3D Slicer all avoid this pattern. The fix (migrate Wireframe + Show-edges to `QPushButton(checkable=True)`) is a non-trivial widget-type change touching `_on_wireframe_toggled` / `_on_edges_toggled` signal wiring + QSS for the checked-state visual treatment in both themes. Legitimately deserves its own pipeline run with focused research on the checked-state QSS for both themes. Disposition: defer-for-followup as `display-toggles-checkable-button-2026q3-e1` (or merge into a broader checkable-toggle milestone if other display-mode controls are converted at the same time).

- **F-L1 (frontend LOW, Isometric button center-alignment):** Polish-pass scope. Real aesthetic divergence but doesn't block ship. Defer.

- **F-L2 (frontend LOW, minus-direction tooltip rotation note for screen readers):** Accessibility polish. Defer.

**Process-only:**

- **H1 (adversary HIGH, 1054-LOC diff):** Process-only; ~53% milestone artifacts, code delta is ~493 LOC. No code action.

**Invalidated:** none — all five code-actionable findings (M1, M2, L1, L2, F-M1) re-verified present before fixing. F-L3 is the same finding as adversary M2 from the frontend angle; closed by M2's fix.

**Test suite:** 301 passed (no regressions — the test surface didn't change in rectify, only the code under test).

**Architecture note recorded:** the F-M1 acceptance + docstring is the pattern for "real UX critique that's correct on the merits but not scope-fittable inside the current milestone." Documenting the caveat at the call site (rather than burying it in the milestone notes) means a future maintainer reading `preset_minus_x_icon` sees the rotation-legibility tradeoff inline and can revisit it with full context.
