# Frontend UX Critique — qtawesome-icons-2026q2-e2

**Milestone:** qtawesome-icons-2026q2-e2 (UPL-4 v1 — camera presets + display toggles)
**Commit range:** `930392e3f18890859c3cf5f851b846a2077191ec..HEAD`
**Files reviewed end-to-end:** `app.py`, `view_panel.py`, `appearance_panel.py`, `icons.py`, `tests/test_icons.py`
**Files unchanged (confirmed):** `styles.py`, `parameters_panel.py`, `surfaces.py`
**Critic:** milestone-frontend-ux-critic (Sonnet 4.6)
**Date:** 2026-05-22

---

## Executive Summary

0 CRITICAL, 0 HIGH, 2 MEDIUM, 3 LOW.

The milestone is well-scoped and correctly wired. The Pattern-A `refresh_icons` architecture is consistent with the v0 precedent, all three call sites in `app.py` are symmetric, and there are no AI-9/AI-11/AI-12/AI-13 violations.

The two MEDIUM findings are both about the **rotated-glyph axis-label legibility** problem at 16 px and an **icon-placement asymmetry** between the preset grid and the Appearance-dock checkboxes. Neither is a regression in the v1 diff itself, but both are user-visible quality-of-life gaps that compound as the icon surface grows. Three LOWs address preset button crowding, a missing negative-direction accessibility label, and a minor wiring opportunity for the `_preset_btns` dict-miss guard.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM-1 — Rotated 180° axis-label glyphs are illegible at 16 px

**Where:** `icons.py:207`, `icons.py:217`, `icons.py:227`
**Evidence:** `preset_minus_x_icon`, `preset_minus_y_icon`, `preset_minus_z_icon` all call `qta.icon("mdi6.axis-x/y/z-arrow", ..., rotated=180)`. The MDI6 `axis-x-arrow` glyph is a horizontal arrow with a capital "X" embedded immediately to the right of the arrowhead. At 16 px the label character is approximately 4–5 px tall. When rotated 180° by qtawesome (which applies a QTransform rotation on the 16 px pixmap), the "X" / "Y" / "Z" character is rendered upside-down and mirror-reversed. At 16 px, an upside-down "X" is visually indistinguishable from a right-side-up "X" (X-axis symmetry), but an upside-down "Y" and upside-down "Z" lose their categorical identity — "Z" rotated 180° looks like "S" (rotational symmetry of the Latin glyph at low resolution), and "Y" rotated 180° looks like a lambda "λ". The button text label ("-X", "-Y", "-Z") does compensate as a fallback identifier, but only if the user reads it — the icon's sole purpose is to provide pre-reading recognition. Blender 4.x uses separate rightward/leftward axis-arrow SVGs (no rotation) for exactly this reason: its View > Numpad-aligned preset icons in the N-panel use distinct per-direction geometry rather than mirrored copies.
**Why it matters:** Users scanning the View Presets group while the surface is rendering rely on icon shape as the primary locator. An upside-down glyph with an illegible embedded character defeats the icon's purpose for the minus-direction presets, degrading the very discoverability the v1 milestone is intended to improve. The -Y and -Z buttons are the worst offenders.
**Suggested fix:** Replace the three minus-direction `rotated=180` calls with alternative glyph names that express the opposite direction without relying on rotation: `mdi6.axis-x-arrow-lock` (non-rotating stable), or — better — use `mdi6.arrow-left` / `mdi6.arrow-down` as the icon anchor for the minus directions, retaining the existing button text "-X" / "-Y" / "-Z" as the label that unambiguously distinguishes the axis. Alternatively, render the minus-direction icons at 20 px instead of 16 px where the character is legible even when inverted; the `setFixedHeight(26)` buttons have enough vertical room.

---

### MEDIUM-2 — QCheckBox icon placement is visually inconsistent with QPushButton icon-on-left convention

**Where:** `appearance_panel.py:448–451`
**Evidence:** `QCheckBox.setIcon()` on PySide6 renders the icon between the platform-drawn check indicator and the text label — i.e., the layout is `[check-square] [icon] [label]`. For the Wireframe and Show-edges checkboxes the rendered order will be: `☐ [grid-icon] Wireframe` and `☐ [border-icon] Show edges`. This creates a three-element prefix before the text label that does not match any peer pattern in the scientific-viz landscape. ParaView's Properties panel uses plain checkboxes (no icon, no indicator prefix — just text) for display toggles. Blender's N-panel uses icon-only `QToolButton`-equivalent widgets for shading mode, not icon+checkbox combinations. 3D Slicer uses icon-bearing `QPushButton` toggle buttons (checkable push buttons) rather than native checkboxes. The `[check-square][icon][label]` triple-prefix is a UI convention found primarily in file-manager "favorites" lists, not in rendering-mode controls; a researcher unfamiliar with Qt internals will read the check indicator and the icon as two competing affordances (which one do I interact with?) rather than a single checkbox with a mnemonic icon.
**Why it matters:** The intended benefit of the icons — reduce label-reading time — is partially undermined if the icon's position in the widget generates visual ambiguity about the control's affordance. This is not a regression from the v1 diff (the checkboxes are new as icon targets; they had no icon before), but the placement decision warrants an explicit evaluation before it ships.
**Suggested fix:** Two paths: (A) keep `QCheckBox` with icon, but move the icon to a companion `QLabel` to the left of the checkbox, giving the layout `[icon-label] ☐ [text]` — preserves the visual association without the triple-prefix; (B) convert the two display toggles to `QPushButton(checkable=True)` (consistent with Blender/Slicer patterns), which renders as `[icon] [label]` without a check-square indicator. Path B aligns with the peer convention and removes the triple-prefix ambiguity entirely.

---

## LOW

### LOW-1 — Preset grid button crowding at default panel width with 16 px icon

**Where:** `view_panel.py:131–144`
**Evidence:** Preset buttons have `setFixedHeight(26)`. The `QGridLayout` is 2-column, so each button's width is approximately `(panel_width − 2×insets − spacing) / 2`. At the minimum dock width (~220 px after insets), each button is ~100 px wide. The layout renders `[icon-16px] [~4px padding] ["+X" text]` — total icon+gap+text is roughly 35 px, leaving ~65 px of empty space per button. This is not crowded at minimum width. However, the Isometric button spans 2 columns (`addWidget(iso_btn, 3, 0, 1, 2)`) and renders `[icon-16px] [Isometric]` at full panel width — approximately 210 px wide for an icon+8-char label. The button does not look crowded but the icon's leading position produces excessive left padding relative to the text mass (icon is flush-left; label floats right in the remaining space on most Qt styles). Peer convention (ParaView's Camera Controls toolbar): icon is centered, label is omitted — the icon is the control. The "Isometric" label is valuable, but the icon+long-label combination in a fixed-height 26 px button reads more like a list item than a click target.
**Why it matters:** Low visual impact, but the Isometric button's aesthetics diverge from the compact 2-column ortho preset grid above it.
**Suggested fix:** Set `setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)` via an explicit icon size alignment, or add `setIconSize(QSize(16,16))` with `setLayoutDirection(Qt.LayoutDirection.LeftToRight)` — already done. This is already handled; the LOW is about considering whether the Isometric button should use a center-aligned icon with no label (tooltip-only) to match the compact grid above it, as ParaView does for its isometric "perspective" button.

---

### LOW-2 — No accessible tooltip update for minus-direction preset buttons mentioning the rotation strategy

**Where:** `view_panel.py:123–129`
**Evidence:** The minus-direction presets have tooltips `"Look along the -X axis (shows ZY plane)"` etc. With 16 px rotated icons, a user who is unsure why the "-X" button's icon looks "upside down" relative to the "+X" button has no in-app explanation. The tooltip does not mention the rotation convention.
**Why it matters:** Very low impact — the button text label already fully disambiguates. But for accessibility (screen readers announce the tooltip), a note that the icon direction mirrors the axis direction would be informative.
**Suggested fix:** Append ` — icon shows the axis direction, mirrored for the negative direction` to minus-direction button tooltips, or document the convention in the group box tooltip ("Icons point along each view direction; minus-direction icons are mirrored").

---

### LOW-3 — `_preset_btns.get(label)` None-guard is unreachable in practice but undocumented

**Where:** `view_panel.py:419–423`
**Evidence:** `refresh_icons` uses `btn = self._preset_btns.get(label)` and guards with `if btn is not None`. The guard implies `label` might not be in `_preset_btns`, but `_preset_btns` is populated in `_make_view_presets_group` for all six labels `["+X", "-X", "+Y", "-Y", "+Z", "-Z"]` that exactly match `_PRESET_ICON_FACTORIES` keys — a 1:1 mapping. The guard is dead code as long as the two dicts stay in sync.
**Why it matters:** The guard is not harmful — it makes the method safe if the two dicts drift apart during future maintenance. But without a comment explaining why it exists, a future reader might remove it as "obviously always True" and lose the safety net.
**Suggested fix:** Add a one-line comment: `# guard: if future refactor renames a preset label, refresh_icons degrades gracefully rather than raising`.

---

## Industry comparison

**ParaView 6.1 View Presets (camera toolbar):** ParaView uses icon-only buttons (no text label) for its six ortho-axis presets, with each button carrying a distinct colored-face cube icon where the facing surface is highlighted to indicate the view direction. The minus direction buttons use a separate glyph (cube with opposite face highlighted), NOT a rotated copy of the plus direction icon. AVC's approach (rotated axis-arrow glyph + text label) is more information-dense than ParaView's icon-only convention, which trades per-direction legibility for compactness. The concrete recommendation: either adopt ParaView's icon-only compact buttons (remove label text, rely on tooltip) or use non-rotation-dependent glyphs for minus directions (MEDIUM-1 recommendation above). Mixing long text labels with small rotated icons is a convention found in neither ParaView nor Blender.

**Blender 4.x N-panel (Viewport Shading section):** Display toggles (wireframe overlay, edge display, cavity shading) use icon-bearing `QPushButton`-equivalent widgets set to `checkable=True`, NOT `QCheckBox` with icon. The check state is communicated by the button's pressed/depressed appearance, not by a separate check-square indicator. The icon is the primary affordance; pressing/releasing the button is the interaction. AVC's `QCheckBox + setIcon` produces a three-element prefix (`[check-square][icon][label]`) that has no direct equivalent in Blender's panel vocabulary. This is the concrete model for MEDIUM-2's suggested fix (B).

**3D Slicer 5.x Modules panel:** Toggleable display controls (Show/Hide mesh, Show/Hide labels) use `QPushButton` with `setCheckable(True)` and explicit checked/unchecked icon states — i.e., two different `QIcon`s for the checked and unchecked states. AVC's current implementation uses a single icon regardless of checked state; the icon's appearance is the same whether Wireframe is ON or OFF. 3D Slicer's pattern (separate icons for ON/OFF) provides a stronger affordance: the icon itself signals the current state, not just the action. This is an improvement opportunity beyond v1 scope but worth tracking — a `setChecked` → `setIcon` signal connection would handle it.

**MeshLab 2023:** Uses a top-toolbar button set for rendering modes (smooth / flat / wireframe / bounding box). Each mode is a mutually-exclusive radio-style button with a distinct icon; Wireframe and Show-edges are NOT separate toggles — they are mode selections. AVC's independent checkboxes (Wireframe and Show-edges can both be checked simultaneously, though Show-edges is suppressed when Wireframe is active) is a more nuanced model than MeshLab's mutually-exclusive modes, and the tooltip "inactive in wireframe mode" correctly communicates the dependency. No finding here — the AVC design is more expressive than MeshLab's.

---

## What was done well

1. **Pattern-A `refresh_icons` architecture is consistent and complete.** All three `refresh_icons` call sites in `app.py` are symmetric: initial construction (`MainWindow.__init__`), explicit theme change (`_on_theme_changed`), and system-driven theme change (`_apply_system_theme`). No call site was missed, which was the class of bug that would produce icons that do not re-render on theme swap. The v0 precedent (qtawesome-icons-2026q2-e1) was followed precisely.

2. **`_preset_btns` dict + instance-attr pattern is the correct fix for loop-local buttons.** Storing the six ortho-preset buttons as a dict keyed by label text is the minimal change needed to enable `refresh_icons` to reach them — no API surface change, no panel-constructor restructuring. The v0 milestone already established this pattern for `_reset_camera_btn`; v1 generalizes it cleanly.

3. **Wireframe / Show-edges icon pair selection is defensible.** `mdi6.grid` (open uniform lattice) and `mdi6.border-outside` (filled center + outer border) are semantically distinct at 16 px and were explicitly chosen to avoid `mdi6.border-all` (equal-weight grid — too close to `mdi6.grid`). The `test_wireframe_and_edges_icons_are_distinct_names` regression guard and the `WIREFRAME_ICON_NAME` / `SHOW_EDGES_ICON_NAME` module constants are exactly the right test hooks for a future palette sweep.

4. **No AI-9/AI-11/AI-12/AI-13/AI-15 violations.** `QSize(16, 16)` is a data class (no Qt enum). All hex colors route through `PALETTE_LIGHT/DARK["TEXT_VALUE"]` — 6-digit, tested. No `processEvents` added. No camera state changes without `render()`. No new variety claims requiring AI-15 disclaimers.

5. **New test coverage is thorough.** `test_camera_preset_icons_correct_names_and_colors` covers both themes for all 7 preset factories and asserts the `rotated=` kwarg. `test_display_toggle_icons_correct_names_and_colors` covers both themes for both toggle factories. `test_wireframe_and_edges_icons_are_distinct_names` guards the copy-paste regression. The v0 icons are guarded by `test_v0_icons_still_bind_correctly`. This is the right test discipline for an icon factory — mock at the qta boundary, assert the exact call args, and cover both themes.

---

## Recommended rectification order

1. **MEDIUM-1** (rotated axis-label legibility) — evaluate whether minus-direction icons need rotation-independent glyph alternatives. Consult the MDI6 catalog for `mdi6.arrow-left-circle-outline` (X−), `mdi6.arrow-down-circle-outline` (Y−/Z−) as replacements. If the button text label is judged sufficient disambiguation, close MEDIUM-1 as accepted-risk with a comment in `icons.py` documenting the known legibility caveat for the -Y and -Z 180° rotations.

2. **MEDIUM-2** (checkbox icon placement) — decide between path A (icon QLabel to the left) or path B (checkable QPushButton). Path B is recommended based on Blender/Slicer precedent but requires migrating two checkboxes to QPushButton, which is a small but non-trivial change to `_build_toggles_group` and `_on_wireframe_toggled`/`_on_edges_toggled` signal connections.

3. **LOW-3** (None-guard comment) — one-line code comment; add in the same commit as MEDIUM-1 or MEDIUM-2 rectification.

4. **LOW-1 and LOW-2** — can be deferred to a dedicated polish pass; neither affects functional correctness.
