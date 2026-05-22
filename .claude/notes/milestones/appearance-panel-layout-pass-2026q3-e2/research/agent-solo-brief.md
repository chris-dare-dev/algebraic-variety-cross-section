# Research Brief — appearance-panel-layout-pass-2026q3-e2

**Agent:** solo (Sonnet 4.6)
**Date:** 2026-05-22
**Scope:** Close deferred F-M2 + F-L2 from `display-toggles-checkable-button-2026q3-e1`: text-alignment consistency across Colors and Display groups, plus Display group header rename.

---

## TL;DR

Adopt **Option 2** (add `setProperty("role", "colors-button")` to `surf_btn` and `bg_btn` in `_build_color_group`, add a new QSS rule `QPushButton[role="colors-button"]` with `text-align: left`). This matches the established role-property pattern, avoids cascading `text-align: left` to Reset Defaults / Reset Camera / view-preset buttons, and the additional 2 `setProperty` calls + 4 QSS lines is the minimum-footprint fix. Rename `QGroupBox("Display")` to `QGroupBox("Render Mode")` — MeshLab uses the exact term and all three peer tools (Blender, Slicer, ParaView) use domain-specific rather than generic terms for their render-mode controls. Risk: the new `colors-button` role string must be documented in CONTEXT.md to prevent future refactors treating it as dead. Backup: if the role-property route is rejected, Option 1 (global `QPushButton` `text-align: left`) works but adds non-fatal visual drift to Reset Defaults / Reset Camera labels (they use `objectName`-based rules that fire after the base rule — center-alignment would be overridden by any explicit `text-align` in their specific rules, which currently don't have one, so the base-rule change WOULD center→left shift them too; this is a cosmetic regression the user has signaled concern about).

---

## Prior art in this repo

- `appearance_panel.py:152–178` — `_build_color_group()`: constructs `surf_btn = QPushButton("Surface…")` and `bg_btn = QPushButton("Background…")`, no `setProperty("role", ...)` call, no `objectName` set. These are plain `QPushButton` instances picking up only the base `QPushButton { padding: 3px 8px; border-radius: 3px; }` rule — zero explicit `text-align` → Qt platform default (center).
- `appearance_panel.py:181–257` — `_build_toggles_group()`: constructs `_wireframe_cb`, `_edges_cb`, `_hq_smoothing_cb` all with `setProperty("role", "display-toggle")`, picking up `text-align: left` from the role-specific QSS rule at `styles.py:530–535`.
- `styles.py:472–476` — Global `QPushButton` rule: `padding: 3px 8px; border-radius: 3px;` — NO `text-align` property. Qt's default for QPushButton is center-aligned text.
- `styles.py:479–500` — `QPushButton#resetDefaultsBtn` and `QPushButton#resetCameraBtn` rules — no `text-align` property in either. If Option 1 (global `text-align: left`) is adopted, these would inherit left-alignment unless a per-name `text-align: center` override is added.
- `styles.py:530–553` — `QPushButton[role="display-toggle"]` base and pseudo-state rules: `text-align: left` in the base rule at line 535. This is the established pattern for left-aligned icon-bearing display-toggle buttons.
- `styles.py:400–571` — `_render_stylesheet(palette)`: the single template function; both themes auto-pick up any change. Adding a `QPushButton[role="colors-button"]` rule here follows the existing pattern (AI-13 compliant, AI-11 safe).
- `.claude/notes/milestones/display-toggles-checkable-button-2026q3-e1/artifacts/adversary-critique.md:111–116` — F-M2 finding (the deferred one this milestone closes): explicitly names the two fix options and recommends deferring to a layout-pass milestone. The finding text: "On a narrow panel (~200px min width) this is visually jarring." Also confirms: "text-align: left is the correct choice for icon+label display toggles."
- `.claude/notes/milestones/display-toggles-checkable-button-2026q3-e1/artifacts/adversary-critique.md:131–135` — F-L2 finding (the deferred header rename): "Rename to 'Render Mode' or 'Surface Style' — one-character diff with no layout impact."
- `CONTEXT.md:4.3b` — theme system: role-property pattern is the canonical QSS cascade mechanism; widget-level `setStyleSheet()` calls are explicitly banned (they override the QSS cascade and break dark mode).
- `tests/test_styles_palette.py:663–706` — `test_dark_stylesheet_includes_role_selectors()`: current guard checks for `QPushButton[role="display-toggle"]` presence in both stylesheets. Adding a `colors-button` rule here would require extending this test with the new role selector.
- `tests/test_styles_palette.py:768–825` — `test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox()`: count-based guards for `setCheckable(True)` >= 2 and `setProperty("role", "display-toggle")` >= 2. The `colors-button` buttons are NOT checkable; a new test for their role property would be a separate test function.
- `render-panel-chrome.py:293–351` — appearance panel capture: currently sets `_wireframe_cb.setChecked(True)` and `_edges_cb.setChecked(True)` for the populated state. No surface/background button visual-state differentiation. The captured PNGs at `/tmp/panel-chrome-before/` confirm the alignment fracture: Colors group buttons are center-aligned; Display group buttons are left-aligned.

### Visual verification (captured 2026-05-22)

Panel-chrome captures (`/tmp/panel-chrome-before/appearance-{light,dark}-empty-default.png`) confirm:

**Light theme:** "Surface…" and "Background…" text is centered in their buttons; "Wireframe" / "Show edges" / "HQ smoothing" are left-aligned with icons anchoring left. The vertical-rhythm fracture crosses the Colors/Display group boundary — visible as a text-indentation step change between adjacent groups.

**Dark theme:** Same pattern, same fracture. The dark-theme `BG_TOGGLE_CHECKED` fill on checked Display buttons makes the icon-left-aligned layout even more prominent relative to the center-aligned Colors buttons above.

---

## External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Blender 4.x N-panel (Properties shelf, Item tab) | https://docs.blender.org/manual/en/latest/interface/window_system/regions.html | All panel buttons in the N-panel are left-aligned with icons; the "Viewport Overlays" / "Viewport Shading" toggle buttons use icon-left + text-left layout. "Display" equivalent is "Overlay" (toggle-style panel). | Confirms left-align as the standard for icon-bearing controls; also supports "Render Mode" over generic "Display" |
| 3D Slicer 5.x Volumes Module | https://slicer.readthedocs.io/en/latest/user_guide/modules/volumes.html | Module panels use "Display" as a collapsible section name, but within it the render-mode controls (Volume Rendering, MIP, composite) are labelled by type, not "Display". The section heading "Display" is used for the entire appearance collection, not just render-mode. | Supports more specific naming than "Display" for the render-mode sub-group. "Display Type" is used for the type selector widget within the Display section, not the section header. |
| ParaView 5.13 Properties panel | https://docs.paraview.org/en/latest/UsersGuide/displayingData.html | Uses "Representation" for the surface/wireframe/points selector dropdown (most specific), and "Styling" or "Coloring" for color-related controls. All buttons and controls are left-aligned. | "Representation" is closest to our Wireframe + Show-edges pair. Too technical for a QGroupBox header — our group is simpler (toggles not a full rep picker). "Render Mode" is closer in scope. |
| MeshLab Render menu | https://www.meshlab.net/ (documentation) | Has a literal "Render Mode" menu item covering solid/wireframe/flat/smooth. Qt-native UI uses left-aligned controls throughout. "Render Mode" is the exact term for wireframe/solid/edges toggle set. | Direct vocabulary match: "Render Mode" for the toggles group. This is the strongest peer-tool citation for the header rename. |
| Qt 6 QPushButton QSS reference | https://doc.qt.io/qt-6/stylesheet-reference.html | `text-align` is a valid QSS property for `QPushButton`. On macOS with Fusion style (or any style that triggers `QStyleSheetStyle`), the QSS `text-align` is honored. AVC already sets `background: transparent` and `border: 1px solid ...` in the `display-toggle` rule which forces `QStyleSheetStyle` to take over full painting — so `text-align: left` is honored. For colors-button buttons, the rule would need at least one box-model property to force `QStyleSheetStyle` — the `border` from the display-toggle rule precedent is the cleanest approach. | Critical: the colors-button rule MUST include at least one box-model property (border, background, or padding) to force QStyleSheetStyle and guarantee text-align is honored on macOS Fusion. |
| Qt 6 Dynamic Properties and Stylesheets | https://doc.qt.io/qt-6/stylesheet-syntax.html#id-selector | `setProperty("role", "colors-button")` after the button is shown requires `style()->unpolish(widget); style()->polish(widget)` to reapply QSS if the property is set post-construction but before `show()`. Since `_build_color_group` sets the property at construction time (before `show()` is called by the QApplication event loop), no explicit unpolish/polish is required. | Confirms Option 2 does not require unpolish/polish as long as the role is set pre-show. |

---

## Recommended approach

### Part A: Text-alignment fix — Option 2 (new `colors-button` role)

**Recommended: Option 2.**

Add `setProperty("role", "colors-button")` to `surf_btn` and `bg_btn` in `appearance_panel.py:_build_color_group` (2 lines). Add a `QPushButton[role="colors-button"]` QSS rule in `styles.py:_render_stylesheet` that sets `text-align: left` plus a box-model property to force `QStyleSheetStyle` on macOS (2–4 lines of QSS).

**Why not Option 1 (global `text-align: left`):**

The global `QPushButton {}` rule at `styles.py:473–476` has no `text-align`. Adding it there would apply to ALL `QPushButton` instances: Reset Defaults (`#resetDefaultsBtn`), Reset Camera (`#resetCameraBtn`), view-preset buttons in `view_panel.py`, and the screenshot button. None of these have icons; their labels are expected to be center-aligned. The per-name rules (`QPushButton#resetDefaultsBtn`, `QPushButton#resetCameraBtn`) would need `text-align: center` overrides to restore center-alignment — adding a maintenance burden and breaking a reasonable future reader's expectation that the base rule is the default and named rules only add deltas. The F-M2 finding explicitly flagged "option (a) is the broader change and could regress the Reset Defaults / Reset Camera button visuals."

**Why not Option 3 (center-align the display-toggle buttons to match Colors):**

The display-toggle buttons have icons; centering icon+text would produce a less-scannable layout where the icon floats to the center of the button. Every peer tool surveyed (Blender, 3D Slicer, ParaView, MeshLab) uses left-aligned layout for icon-bearing panel controls. The F-M2 finding text itself says "text-align: left is the correct choice for icon+label display toggles."

**Exact QSS rule for the colors-button role:**

```
QPushButton[role="colors-button"] {
    text-align: left;
    padding: 3px 8px;
    border-radius: 3px;
}
```

The `padding` and `border-radius` re-state the base rule values explicitly, which is required to force `QStyleSheetStyle` to take over widget painting on macOS so that `text-align: left` is actually honored. Without at least one box-model property, `text-align` may be ignored by the native QPushButton painter. The values are copied from the base `QPushButton {}` rule so no visual change results beyond the alignment. No `:hover`, `:checked`, `:disabled` variants needed — the Colors buttons are plain action buttons (not toggles), and their hover state can remain at Qt-platform default (the platform hover brush).

**Important:** the surface preservation rule from the brief: `surf_btn.clicked.connect(self._pick_surface_color)` and `bg_btn.clicked.connect(self._pick_bg_color)` — neither signal nor slot is touched by this change. The buttons remain plain `QPushButton` (not checkable); the role-property change is styling-only.

### Part B: Display group header rename — "Render Mode"

**Recommended: "Render Mode".**

Rationale:
- MeshLab uses "Render Mode" as the literal menu name for wireframe/solid/flat toggle controls — the closest exact match.
- Blender uses "Viewport Overlays" and "Viewport Shading" — both more specific than "Display", but neither maps cleanly to a simple QGroupBox title at our scope level.
- ParaView uses "Representation" for the equivalent selector — too technical and implies a full representation picker (surface/volume/wireframe/points) rather than simple overlay toggles.
- 3D Slicer uses "Display Type" within a "Display" section — adds "Type" suffix but not relevant to our two-toggle + HQ case.
- The AVC Display group hosts Wireframe + Show edges + HQ smoothing — all of which modify how the surface is rendered, not what is displayed. "Render Mode" communicates this correctly.
- The F-L2 finding from the prior milestone explicitly recommends "Render Mode" as the first option.

**One-line change:** `appearance_panel.py:182` — `QGroupBox("Display")` → `QGroupBox("Render Mode")`.

### Implementation plan (exact LOC)

1. `appearance_panel.py:161` — after `surf_btn = QPushButton("Surface…")`, add `surf_btn.setProperty("role", "colors-button")`.
2. `appearance_panel.py:172` — after `bg_btn = QPushButton("Background…")`, add `bg_btn.setProperty("role", "colors-button")`.
3. `appearance_panel.py:182` — change `QGroupBox("Display")` to `QGroupBox("Render Mode")`.
4. `styles.py:_render_stylesheet` — after the base `QPushButton {}` rule (after line 476), insert:
   ```
   /* --- Colors-group buttons (Appearance dock) -------------------------------- */
   /* appearance-panel-layout-pass-2026q3-e2 (F-M2 closure): left-align text in
      the Surface… / Background… color-picker buttons to match the Display-group
      display-toggle buttons.  Uses the role-property pattern (AI-11 compliant)
      rather than extending the global QPushButton rule (which would regress
      Reset Defaults / Reset Camera center-alignment).  The padding + border-radius
      re-state the base rule values to force QStyleSheetStyle on macOS so that
      text-align: left is honored by the native painter.
      No box model change: no icons yet on these buttons — left-align without
      icon produces the same visual as left-align with icon (text anchors to
      padding-left edge, which is the left swatch boundary in the HBoxLayout). */
   QPushButton[role="colors-button"] {{
       text-align: left;
       padding: 3px 8px;
       border-radius: 3px;
   }}
   ```
   Total: ~15 lines of QSS + comment.
5. No signal/slot changes. No new palette tokens. No icon changes.

**Estimated total delta:** ~4 Python lines + ~15 QSS lines (with comment) = ~19 LOC. Well under the "small milestone <=200 LOC" threshold.

---

## Alternatives considered

- **Option 1: global `QPushButton { text-align: left; }`** — rejected because it cascades to Reset Defaults, Reset Camera, and view-panel buttons that are intentionally center-aligned (no icons) and would need `text-align: center` overrides in their per-name rules, increasing maintenance surface. The brief explicitly flagged this risk.
- **Option 3: center-align Display-group buttons** — rejected because icon-bearing controls universally use left-align in all three peer tools surveyed, and the F-M2 finding text explicitly endorses left-align as correct for icon+label.
- **Add icons to Colors buttons and keep center-align** — would match the color buttons to the Display group visually by adding icons, but the swatch (`_surf_swatch`, `_bg_swatch`) already serves as the visual affordance for color. Adding an icon BESIDE the swatch would create a new visual complexity not present in any peer tool. Out of scope for a pure alignment-pass milestone.
- **Rename to "Overlay"** — Blender's term; but "Overlay" implies additive visual layers (wireframe drawn on top of solid), while our group also contains the mode-switching Wireframe toggle which replaces the solid, not overlays it. Semantically imprecise.
- **Rename to "Representation"** — ParaView's term; too technical for the AVC level of complexity and implies a full representation picker.
- **Rename to "Shading"** — conflicts with the existing "Shading" group just below (Smooth/Flat radio buttons). Would introduce a name collision within the same panel.
- **Rename to "Surface Style"** — plausible but HQ smoothing is not a "style" — it's a geometry pass. "Render Mode" is more accurate.

---

## Risks and unknowns

1. **`text-align: left` on macOS without `QStyleSheetStyle` trigger** — confirmed risk from the prior adversary critique (F-M2's L2 LOW). The fix: the `colors-button` QSS rule MUST include `padding` or `border` or `background` to force `QStyleSheetStyle`. The recommended rule above includes `padding: 3px 8px; border-radius: 3px;` which are sufficient triggers. Verification via panel-chrome re-capture after the fix is mandatory.
2. **No `unpolish`/`polish` needed** — `setProperty("role", "colors-button")` is set at construction time in `_build_color_group()`, before the panel's first `show()`. Qt evaluates QSS at polish time (first paint). Post-construction `setProperty` calls that happen after the widget is already shown DO require `unpolish/polish` to force re-evaluation — but this is a construction-time call, so it is safe.
3. **AI-11 compliance** — `setProperty("role", "colors-button")` is a pure string/data property, not a Qt enum. AI-11 covers Qt enum qualification, not property strings. No conflict.
4. **AI-13 compliance** — No new hex color tokens introduced. The `colors-button` rule has no color declarations. No conflict.
5. **Test suite impact (AI-2)** — New test needed: `test_appearance_panel_colors_buttons_have_colors_button_role` as a grep/count test (source-text check) asserting `src.count('setProperty("role", "colors-button")') >= 2`. Also extend `test_dark_stylesheet_includes_role_selectors` to check for `QPushButton[role="colors-button"]` in both stylesheets. Both are AI-2-compliant grep tests; no `QApplication` needed.
6. **`render-panel-chrome.py` update** — The `appearance_populated` state setup in the capture script currently pokes `_opacity_slider.setValue(72)` + `_wireframe_cb.setChecked(True)` + `_edges_cb.setChecked(True)`. No change needed for the alignment fix since the Colors buttons do not have a "checked" state. However, the post-capture documentation note in the script mentioning the role-property pattern should mention the new `colors-button` role for completeness — optional, not blocking.
7. **"Render Mode" does not perfectly describe HQ smoothing** — HQ smoothing is a geometry-quality toggle, not strictly a "render mode." However, the grouping is pragmatic (all three are Display-group display controls); the term is close enough and used by MeshLab for an analogous toggle set. Future refactors that split HQ smoothing to its own "Quality" group would be out of scope here.
8. **`QGroupBox("Render Mode")` test impact** — `test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox` does not test the group header name. A simple grep test for `QGroupBox("Render Mode")` could be added to the test file as a regression guard, but is optional given the simplicity of the change. Recommend including it for consistency with the suite's "every behavioral claim has a test" ethos.

---

## AI-15 disclaimers

Not applicable. This milestone proposes no new varieties or figures — it is a pure visual-alignment + header-label pass.

---

## AI-1..AI-15 conflict matrix

| Invariant | Status | Notes |
|---|---|---|
| AI-1 (PySide6 + PyVista stack) | CLEAN | No renderer or framework changes |
| AI-2 (Qt-free tests) | CLEAN | New tests are source-text grep only |
| AI-3 (no `MainWindow` under offscreen) | CLEAN | No `MainWindow` changes |
| AI-4 (clip_scalar not clip_box) | CLEAN | Unrelated |
| AI-5 (clip_scalar `scalars=` kwarg) | CLEAN | Unrelated |
| AI-6 (pipeline discipline) | CLEAN | Unrelated |
| AI-7 (Hanson normals) | CLEAN | Unrelated |
| AI-8 (Surface/ParamSpec registry) | CLEAN | Unrelated |
| AI-9 (re-entrancy guard) | CLEAN | No `processEvents`; `setProperty` is synchronous and GUI-thread-safe |
| AI-10 (raw mesh cached) | CLEAN | Unrelated |
| AI-11 (fully-qualified Qt enums) | CLEAN | `setProperty` uses plain strings, not Qt enums |
| AI-12 (WCAG AA text contrast) | CLEAN | No new color tokens; no text-color changes |
| AI-13 (6-digit hex only) | CLEAN | No new hex color literals |
| AI-14 (generator contract) | CLEAN | Unrelated |
| AI-15 (math honesty) | CLEAN | Not applicable (no new varieties) |

---

## Test plan

All tests must be AI-2-compliant (source-text grep, no `QApplication`).

1. **New: `test_appearance_panel_colors_buttons_have_colors_button_role`**
   - Grep `appearance_panel.py` source for `setProperty("role", "colors-button")`.
   - Assert `count >= 2` (covers both `surf_btn` and `bg_btn`).
   - Assert neither button uses `setCheckable` (they are action buttons, not toggles).

2. **New: `test_dark_stylesheet_includes_colors_button_role_selector`** (or extend `test_dark_stylesheet_includes_role_selectors`)
   - Assert `QPushButton[role="colors-button"]` is present in both `APP_STYLESHEET` and `APP_STYLESHEET_DARK`.
   - Assert the rule includes `text-align: left` (substring check on the rendered stylesheet string).

3. **New (optional but recommended): `test_appearance_panel_toggles_group_header_is_render_mode`**
   - Grep `appearance_panel.py` source for `QGroupBox("Render Mode")`.
   - Assert it appears and `QGroupBox("Display")` does NOT appear.

4. **Extend existing `test_dark_stylesheet_includes_role_selectors` (or add parallel)**
   - Add `QPushButton[role="colors-button"]` to the expected selectors list in the existing role-selector test.

5. **No test needed for signal/slot behavior** — the change is purely visual (QSS + `setProperty`). The existing `_pick_surface_color` and `_pick_bg_color` connection tests (if they exist) are unaffected.

---

## Visual verification plan

1. **Before**: Panel-chrome PNGs already captured at `/tmp/panel-chrome-before/appearance-{light,dark}-empty-default.png`. Alignment fracture confirmed (Colors group center-aligned, Display group left-aligned).

2. **After implementation**: Re-run `render-panel-chrome.py /tmp/panel-chrome-after`. Inspect:
   - `appearance-light-empty-default.png`: "Surface…" and "Background…" text should now be left-aligned, matching "Wireframe" / "Show edges" / "HQ smoothing".
   - `appearance-dark-empty-default.png`: same verification on dark theme.
   - `appearance-light-populated-default.png`: checked state of Wireframe/Show-edges should be unaffected; Colors buttons should be left-aligned.
   - Group header should read "Render Mode" (not "Display") in both themes.

3. **Regression check**: `appearance-light-empty-default.png` and `appearance-dark-empty-default.png` for Reset Defaults and Reset Camera buttons (in `parameters_panel.py` and `view_panel.py` panel-chrome captures) should be visually unchanged from before — center-aligned label text.

4. **Optional pixel diff**: Run `compare -metric PSNR /tmp/panel-chrome-before/appearance-light-empty-default.png /tmp/panel-chrome-after/appearance-light-empty-default.png /dev/null` (ImageMagick). Expect a non-zero PSNR (images differ — alignment changed). Run same compare on `view-light-empty-default.png` — expect identical (0 pixel diff — no view-panel changes).

---

## Open questions for the user

None. The brief is fully specified:
- Option 2 is recommended with clear rationale.
- "Render Mode" is recommended with peer-tool citations.
- Implementation is <=19 LOC.
- No gate-required scenarios — no competing approaches with equal priority signals.
