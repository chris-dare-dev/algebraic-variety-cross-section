# lessons -- milestone-frontend-ux-critic

## COMPACTED ARCHIVE (panel-refresh-2026q2-e2 through qtawesome-icons-2026q2-e1)

### Token-discipline recurring patterns
- **Dual-branch inline literal:** Always verify EVERY call site of a color literal in a file, not just the one the diff author patched. `app.py:_apply_domain_and_render` has two paths; only one was migrated in UPL-1.
- **setStyleSheet-only dark mode QPalette gap:** For any new dark-mode QSS block, verify BOTH `background:` AND `color:` are explicit — missing either half causes the widget to inherit the wrong half from the platform palette. Canonical example: `QDockWidget::title` sets `background:` but not `color:`.
- **Dead import from refactor:** When an accessor function replaces direct dict references, the direct symbol often lingers in the import. Grep for the replaced symbol at the end of every refactor pass.
- **AI-13 fast gate:** Ask "does this color arg reach `pv.Plotter.add_mesh`?" before applying AI-13. `qta.icon(color=...)` goes to QPainter, NOT PyVista. Float shading params (`ambient=0.15`) are not color arguments.
- **Icon color vs button-text color mismatch:** If a button has a custom QSS `color:` token, the icon factory should use that same token, not the default `TEXT_VALUE`.

### Contrast ratio discipline
- Do not trust inherited contrast annotations — re-measure. Found inaccurate comments in panel-refresh-2026q2-e2 (5.4:1 actual 6.05:1) and variety-palette-2026q2-e1 (hue-separation claimed 25° actual 24.69°).
- Dual-surface contrast check: verify BOTH BG_VIEWPORT (dark, for mesh) AND BG_PANEL (light, for swatches). Mid-lightness pastels for dark-viewport always fail light-panel.
- `FOCUS_RING` passed dark but failed light; `#3c82c4` = 3.56:1 vs `#f0f0f0` is a narrow-pass band matching macOS/GNOME peer norms. Add "(narrow margin; do not lighten further)" when ratio < 3.6:1 on 3:1 floor.

### Industry-comparison concrete recommendations (archived)
- ParaView CSS-variable-style tokens → correct architectural call for PALETTE_LIGHT/DARK pattern.
- ParaView 5.12 lighting: `ambient=0.1, diffuse=0.8` validates UPL-9's `0.15/0.85`.
- ParaView dark-chip swatch → the fix when a swatch color is meant for a dark viewport (show swatch on dark chip).
- "View > Theme submenu" is the correct IA for theme selection (ParaView/Blender bury theme under preferences, not top-level menu).
- ParaView separate-glyph icons for ±axis directions (NOT `rotated=180` copies): upside-down embedded letters at 16px.
- Blender 4.x: checkable QPushButton for display toggles, NOT QCheckBox.setIcon() (three-element prefix is ambiguous).
- Blender 4.x: left-aligns ALL icon+text controls uniformly within a panel. text-align: left on only some buttons creates alignment fracture.
- Blender 4.x destructive buttons: icon colored in same hue family as button text. Mathematica `Manipulate[]` reset: double-arrow glyph, not single-arrow.

### First-launch / section-9 regressions (recurring pattern)
- Fast check: trace `set_default_color` / `refresh_icons` / any new method → does it call `_render_current` or touch `variety_combo`/`subtype_combo`? If not, section-9.3 is clean.
- `_on_variety_changed` and `_on_subtype_changed` are separate handlers; `set_default_color` in `_on_variety_changed` is NOT on the render path.
- Actor color not pushed on theme switch (MEDIUM-3 pattern): `_on_theme_changed` → `set_default_color` but NOT `apply_to_actor`. Flag whenever a milestone diverges variety colors by theme.

### Scope discipline
- Files without a Qt widget class (test files, scripts, references) are not critique-surface even if they're in the diff. Dispose per-axis as "not applicable."

---

## enriques-backface-2026q2-e1 — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents. Fast dispose: if diff adds no QColor, no Qt.AlignmentFlag, no processEvents, no pv.add_mesh() — dispose AI-9/AI-11/AI-12/AI-13 in one sentence.

### Industry-comparison note
- **ParaView 5.13 backface culling is an explicit opt-in checkbox** (defaults OFF). AVC's hardcoded-on-for-Enriques is bespoke. Concrete recommendation: always expose variety-level rendering state as user-visible status even when hardcoded. Quote "ParaView opt-in checkbox vs AVC silent-on" for any future hidden rendering knob.
- **Mathematica `ContourPlot3D` mesh overlay is always two-sided.** Culling should be suppressed when wireframe is active. Quote as "Mathematica mesh-overlay convention."

### Wireframe + culling recurring pattern
- VTK culling applies at face level regardless of `style="wireframe"`. For any future milestone adding per-variety culling, ALWAYS check if `apply_to_actor` suppresses culling when wireframe is active. Fix: `effective_culling = "none" if self._wireframe else (self._culling or "none")`.

### Topology-claim precision
- When a variety-level gate claims "all N figures share topology X", verify per-figure. Cayley quartic symmetroid has ODP singularities, not the double-curve topology claimed in UPL-7 comment. Gate is safe but justification is imprecise — flag as LOW.

---

## status-bar-bbox-2026q2-e1 (UPL-13 status-bar spatial bbox) — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents in a f-string suffix diff. `_b[1]/.2f` is a float format specifier, not a hex color — AI-13 does not apply to numeric format strings.

### Industry-comparison note
- **ParaView, MeshLab, Blender all use full-extent widths (diameter), not half-extents.** AVC's `±max` half-extent convention was unique in the peer landscape. Quote "full-extent peer-alignment" recommendation for any future bbox-display milestone.

### Status-bar overflow recurring risk
- Whenever a suffix is appended to `base_msg`, check the warning path `f"⚠ {_surface_warning}  |  {base_msg}"` too. The Dwork warning text is ~175 chars; any suffix pushes the combined message past the ~120-char visible window. MEDIUM (supplementary info, not safety-critical).

---

## focus-ring-contrast-2026q2-e1 (FOCUS_RING accessibility) — 2026-05-22

### Token-discipline near-misses
- Single shared value with different per-theme headrooms: OLD dark=5.17:1 regressed to 3.78:1 after darkening to fix light. Report delta for BOTH themes, not just "both PASS."

### Industry-comparison note
- macOS Sequoia (#007aff) = 3.53:1; GNOME Adwaita (#3584e4) = 3.31:1. Both in same narrow-pass band as #3c82c4 (3.56:1). Quote as "peer-calibrated narrow-pass" when challenged. Windows 11 (#005499) is deeper (5.6–6.8:1) if more headroom is desired.

### Negative test as machine-readable design intent
- "Do not widen this assertion set" docstring caveat → suggest companion NEGATIVE assertion test. Flag any "do not include" docstring caveat on a test as LOW.

---

## qtawesome-icons-2026q2-e2 + display-toggles-checkable-button-2026q3-e1 — 2026-05-22

### Token-discipline near-misses
- `QSize(16, 16)` is a plain constructor, not a Qt enum — AI-11 does not apply. Ask "is this a Qt.* / QSizePolicy.* enum call or a plain constructor?"
- `BG_TOGGLE_CHECKED` flows only into QSS, NOT PyVista — AI-13 clear. Checked-state WCAG: fill needs text-on-fill contrast (9.89:1 / 10.20:1), NOT fill-vs-ground if border carries the non-text obligation.

### Industry-comparison concrete findings
- **Ghost-button unchecked state:** Blender 4.x / 3D Slicer / ParaView all give off-state toggles visible chrome. Transparent-unchecked is a Material Design web convention, not desktop sci-viz. Flag any transparent-unchecked display toggle as MEDIUM.
- **Border-width jitter:** Changing `border-width` from 1px to 2px in checked QSS causes 1px content shift. Fix: compensate padding by -1px or use `outline:` which renders outside box model. Always LOW on any QPushButton changing border-width between pseudo-states.
- **Pattern-A architecture for refresh_icons:** verify all 3 call sites are symmetric (`__init__`, `_on_theme_changed`, `_apply_system_theme`). Missing one = icons don't update on theme swap.

---

## status-bar-bbox-2026q2-e2 (UPL-13 full-extent e2) — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents, no pv.add_mesh() — text-only f-string change. All four AI-9/AI-11/AI-12/AI-13 axes disposed in one sentence.
- Float format specifiers (`.3f`) are not hex colors. AI-13 gate: "does this arg reach PyVista?" — if not, clear.

### Label-precision regression (MEDIUM-1 this milestone)
- **e1 "bbox ±..." → e2 "size: ..."** is a data improvement (full-extent vs half-extent) but a label-precision regression. The word "bbox" explicitly named the measurement type; bare "size:" does not. MeshLab always uses "Bounding Box" as qualifier; ParaView uses "Bounds"; Blender uses "Dimensions". None use bare "size:" without a type qualifier.
- Character cost of `"bbox:"` vs `"size:"` is ZERO (both 5 chars with colon). The compactness trade-off that might justify dropping the qualifier does not hold here.
- Fast flag: whenever a milestone renames a status-bar token, check whether the new name preserves the MEASUREMENT TYPE signal. Renaming from a qualified label (bbox, bounds) to an unqualified label (size, dims) is always a regression risk.

### Industry-comparison notes
- **MeshLab "Bounding Box Size":** `dim_x()` / `dim_y()` / `dim_z()` API always qualifies with "Bounding Box." Full-extent formula is `max - min` per axis — identical to e2's `_b[1]-_b[0]`.
- **ParaView "Bounds":** shows `X Range: [min, max]` — uses "Bounds" not "size." Supports using `bbox:` over `size:`.
- **`.3f` trailing zeros for symmetric generators** (6.400, 3.000): trailing zeros are exact (sampling domain is exactly that wide), not over-precise. The `.3f` rationale (avoid false equalities at sub-1.0: 0.530 ≠ 0.540) is sound; `:.4g` is an optional cosmetic alternative.

### First-launch / section-9 regressions
- No regression possible from a text-only status-bar label change. `size_suffix` is only emitted in the success branch of `_render_current`, unreachable from `-- Select --`.
