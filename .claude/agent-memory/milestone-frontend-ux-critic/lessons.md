# lessons -- milestone-frontend-ux-critic

## panel-refresh-2026q2-e2 (UPL-1 palette tokenization) — 2026-05-20

### Token-discipline near-miss
- **Dual-branch inline literal:** When a function has two code paths that use the same color (e.g. `app.py:_apply_domain_and_render` has a normal-render path and an empty-clip path), a refactor that only touches one path leaves a silent residual literal in the other. Verify EVERY call site of a color literal in the file, not just the one the diff author patched. `app.py:364` retained `"#888888"` while `app.py:386` (same actor, normal path) was correctly migrated to `COLOR_WIREFRAME_OVERLAY`.
- **Backward-compat alias vs. palette subscript inconsistency in QSS:** The new pattern is `PALETTE_LIGHT["KEY"]` inside `APP_STYLESHEET`. One rule (status bar) still used the legacy alias `{COLOR_MUTED}`. The test passes because values match, but the authoring pattern is inconsistent and will confuse UPL-4 sweep. Flag any remaining alias uses inside APP_STYLESHEET as MEDIUM.

### Contrast ratio comment accuracy
- Do not trust inherited contrast annotations — re-measure with the luminance formula already present in `test_styles_palette.py`. Found two inaccurate comments (5.4:1 vs actual 6.05:1 for TEXT_MUTED; 6.1:1 vs actual 8.37:1 for TEXT_RESET_BTN). Always verify before propagating to dark-mode palette design.
- `FOCUS_RING` claimed >=3:1 but measured 2.60:1. Including a token in a documented palette with a false spec annotation is a UPL-1 artifact even if the token pre-existed the refactor.

### Industry-comparison note (not a finding this milestone — architecture-level)
- ParaView: uses named CSS-variable-style tokens in its color scheme XML so that theme swap (dark/light) is a single dict substitution — exactly what PALETTE_LIGHT sets up. The parallel PALETTE_DARK pattern proposed here is the correct architectural call.
- VisIt: has a hard-coded dark/light switch in its Qt theme manager with ~40 inline hex literals — the pattern UPL-1 is specifically avoiding. No finding here because UPL-1 is moving away from that anti-pattern.

### First-launch / section-9 regressions
- UPL-1 was a stylesheet-only refactor; no auto-render temptation was present. Worth flagging fast: any refactor that touches `appearance_panel.py` constructor `self._surface_color` or `self._bg_color` defaults could silently change launch colors. Verify the QColor() constructor calls still receive the same 6-digit hex as before.

## graph-and-window-2026q2-e1 (UPL-9 lighting + UPL-27/28 scout tooling) — 2026-05-21

### Token-discipline near-misses
- No short-hex or shorthand-enum slip in this diff. `Qt.DockWidgetArea.LeftDockWidgetArea` was the one new Qt enum — already qualified. `p.set_background("#2f2f2f")` was the one new hex string flowing into PyVista — already 6-digit. Both passed clean on first read.
- New numeric kwargs (`ambient=0.15`, `diffuse=0.85`) are not color arguments — AI-13 does not apply to float shading params. Make this check fast: ask "does this arg accept a color string?" before applying AI-13 to a new kwarg.

### Industry-comparison note (UPL-9 lighting calibration)
- ParaView 5.12 default implicit-surface material: `ambient=0.1, diffuse=0.8, specular=0.1`. UPL-9's post-patch `ambient=0.15, diffuse=0.85` is in the same regime — a concrete validation that the values are industry-calibrated, not arbitrary. Quote the ParaView defaults when UPL-9 is questioned.
- Mathematica `ContourPlot3D` default ambient ≈ 0.2, which visibly lifts K3 saddle-region concavities. UPL-9's 0.15 is slightly more conservative and is the correct call for a dark viewport (Mathematica uses a lighter default background).

### First-launch / section-9 regressions
- Lighting kwarg changes inside `_apply_domain_and_render` are safe with respect to section 9.3 (no auto-render) because that function is only called from `_render_current`, which is only called after a subtype is selected. No first-launch temptation in this diff.
- Watch for the dual-path risk: `_apply_domain_and_render` has an early-return branch (empty clip) that does NOT reconstruct `self._actor`. Future actor-creation added to that branch will silently miss whatever lighting kwargs are in the main path. Flag this as MEDIUM whenever the early-return branch gains an `add_mesh` call.

### Scope discipline
- Three files changed, only one (`app.py`) is on the Qt-panel critique surface. Scout-script changes (`.claude/scripts/`) and reference-template changes (`.claude/references/`) are internal tooling with no user-visible UX surface. Explicitly dispose of them per-axis as "not applicable" — do not manufacture UX findings on tooling-only changes.

## variety-palette-2026q2-e1 (UPL-2 per-variety surface palette) — 2026-05-21

### Token-discipline near-misses
- No short-hex or shorthand-enum slip in this diff. All four VARIETY_DEFAULT_COLOR entries are verified 6-digit. `QColor.name()` always returns 7-char `#rrggbb` — never short-hex — so the `actor.prop.color = color.name()` write path is inherently AI-13 safe. Make this check fast: confirm `QColor.name()` → 7-char output rather than tracing the hex through the call chain.
- Stale forward-ref comments ("UPL-5 will populate") survived the diff because the block-level comment was updated but the module docstring was not. Pattern to flag fast: when a dict stub is populated in a milestone, grep for ALL comments that reference the stub by name and update them in the same pass.

### Contrast ratio comment accuracy
- Researcher-annotated ratios (5.09 / 5.91 / 6.07 / 6.29) verified correct against BG_VIEWPORT (#2f2f2f). However, hue-separation claim ">=25° pairwise" was false: K3 vs CY3 measured 24.69° (float HSV). The integer HSV rounding (226° vs 202° = 24°) makes it even further below the claim. Always verify float HSV, not integer, when checking hue-separation specs.
- The dual-surface contrast check pattern (colors pass against dark viewport; fail against light panel) is a recurring pattern for any palette milestone. Check BOTH backgrounds: BG_VIEWPORT for rendered mesh legibility AND BG_PANEL for swatch chip legibility. These are separate WCAG assessments (mesh = non-text at scale ≥3:1; swatch chip = non-text UI component ≥3:1). Mid-lightness pastels chosen for dark-viewport legibility will always fail the light-panel check.

### Industry-comparison note (concrete recommendation generated)
- ParaView 5.12 color-preset swatch: rendered on a dark chip matching the render view background — this is exactly the V1 fix for the MEDIUM swatch-contrast finding. When a swatch shows a color meant for a dark viewport, the swatch chip should also use a dark background so the viewport-calibrated contrast applies. "Dark-chip swatch inset" is the ParaView-validated recommendation; quote it by name in future uplift candidates involving color swatches on light panels.

### First-launch / section-9 regressions
- No regression in this diff. The call-site guard pattern (`if name in VARIETIES:` before `set_default_color`) ensures the color seed only fires after a real variety is selected, never on `-- Select --`. Fast check: trace `set_default_color` to `_render_current` — they must NOT be on the same synchronous call path unless a subtype is selected. In this diff, `_render_current` is only in `_on_subtype_changed`, which is a separate handler from `_on_variety_changed` where the first `set_default_color` call lives.
- Re-seed on subtype switch (second call in `_on_subtype_changed`) is the correct design for V0 (no sticky overrides, reset-on-switch). This is the intentional "re-seed on switch-back" semantic documented in the UPL-25 forward-ref comment. Flag any future change that adds QSettings persistence for `self._surface_color` as an AI-9 / section-9.1 scope question (explicit non-goal).

## dark-mode-2026q2-e1 (PALETTE_DARK + Theme menu) — 2026-05-21

### Token-discipline near-misses
- **setStyleSheet-only dark mode always leaves a QPalette gap.** When dark mode is implemented via `QApplication.setStyleSheet(dark_qss)` without a parallel `QPalette` update, any widget that lacks an explicit `background:` and `color:` in the QSS inherits the LIGHT system palette. The two recurring failure points are (a) `QDockWidget::title` — sets `background:` but not `color:`, so text is near-black on a dark header on light-OS systems; (b) `QStatusBar` — sets `color:` but not `background:`, so the status bar background is the platform light grey, making a mid-grey text token (like `#a0a0a0`) illegible. Check both axes for EVERY new dark-mode QSS block: `background:` AND `color:` must be explicit, or the widget inherits the wrong half from the platform palette. The dock title finding is the canonical example of this class of bug.
- **Dead import from refactor.** When an accessor function (`get_variety_default_colors`) replaces all direct dict references (`VARIETY_DEFAULT_COLOR`), the direct symbol often lingers in the import statement. Check imports at the end of every refactor pass — one grep for the replaced symbol name with a non-import context filter is sufficient. In this milestone: `VARIETY_DEFAULT_COLOR` survived at line 41 with zero non-import uses.

### Industry-comparison note (concrete recommendation generated)
- **"Theme" as a lone top-level menu is the correct semantic but wrong IA.** ParaView, Blender, and 3D Slicer all bury theme selection under preferences, never expose it as a top-level menu. Blender's closest analog is a "Window" menu or shortcut toggle; ParaView uses Edit > Settings. The forward-compatible pattern for this app is a "View" menu containing a "Theme" submenu — which also becomes the natural home for future viewport-overlay toggles (Show Axes, Grid, etc.). Quote this as the "View > Theme submenu" recommendation when evaluating any future menu-bar addition.
- **Ratio verification cadence.** This is the first milestone where ALL six claimed PALETTE_DARK contrast ratios verified exactly against independent computation (no rounding or annotation error). The prior milestone had two misses. The correct workflow: verify during implementation AND again during critique. Annotate in the palette dict with the formula result, not an approximation.

### First-launch / section-9 regressions
- No regression in this diff. Dark-first launch (`main()` applies `APP_STYLESHEET_DARK` before `MainWindow()`) is intentional and documented. `_build_theme_menu()` runs before docks are created; the dropdown stays at `— Select —`; no auto-render occurs. Fast check: trace `_build_theme_menu` → does it call `_render_current` or `_on_subtype_changed`? In this diff: no. The theme-change path also does not auto-render — it only calls `set_default_color` (swatch-only, no render). Safe.
- **Actor color not pushed on theme switch (MEDIUM-3 pattern).** `_on_theme_changed` calls `set_default_color` but not `apply_to_actor`. In V0 this is invisible (light + dark colors are identical). In any future milestone that diverges variety colors by theme, the live actor will lag behind the swatch until the next user interaction. Flag this pattern immediately on any milestone that adds `set_default_color` calls in a non-render path: always ask "does the live actor also need updating?"

## qtawesome-icons-2026q2-e1 (UPL-4 qtawesome button icons) — 2026-05-21

### Token-discipline near-misses
- **No short-hex or shorthand-enum slip in this diff.** `icons.py` passes color from `PALETTE_LIGHT/DARK["TEXT_VALUE"]` — already 6-digit, already tested. `qta.icon(color=...)` goes to Qt's QPainter, NOT PyVista; AI-13 applies only when the hex flows into `pv.Plotter.add_mesh(color=...)` or similar. Make this check fast: ask "does the color string reach PyVista?" before flagging AI-13.
- **Icon color vs button-text color mismatch:** When a button has a QSS `color:` override (e.g. `TEXT_RESET_BTN` on `#resetDefaultsBtn`), the icon factory's use of `TEXT_VALUE` breaks the button's intentional color family. Always check: does the button have a custom QSS color token? If yes, the icon should use that same token, not the default `TEXT_VALUE`. Both `TEXT_RESET_BTN` values (light + dark) are already 6-digit and WCAG-safe — no lift needed to fix it.

### Industry-comparison note (concrete recommendation generated)
- **ParaView's iconographic separation of reset-camera vs screenshot is the concrete recommendation:** ParaView uses a reset/home-style glyph for "reset camera" and a camera/film-strip glyph for "screenshot" — categorically different glyphs for categorically different actions. When two buttons share a camera-body anchor (as `mdi6.camera-retake` and `mdi6.camera` do), the icon disambiguation is lost at small sizes (16–22 px). Future icon choices: reset-camera → non-camera semantic (fit-to-screen, arrow-expand-all, home-circle); screenshot → camera (plain). The reset action and the capture action should NOT share the same base glyph family.
- **Blender 4.x destructive button convention:** Red-family buttons (delete, destructive restore) use icons colored in the same hue family as the button text — not neutral grey. The `#resetDefaultsBtn` has this problem. Quote this as "Blender destructive-button icon hue convention" when evaluating any future icon color choice on a themed button.
- **Mathematica `Manipulate[]` reset icon:** Uses a double-arrow "rewind to start" glyph, not the single-arrow undo glyph. The visual difference signals "go back to initial state" vs "undo one step." When a reset-to-defaults icon is proposed, the single-circle-arrow (`mdi6.restore`) is ambiguous against the Ctrl+Z undo convention; double-arrow or clockwise-restore variants are less likely to mislead.

### First-launch / section-9 regressions
- No regression in this diff. `refresh_icons()` is visual-chrome-only: no dropdown changes, no `_render_current` call, no `processEvents`. Fast check: does the new method touch any of `variety_combo`, `subtype_combo`, `_render_current`, `_on_subtype_changed`? If not, section-9.3 is safe.
- **Icon-before-show ordering:** The correct pattern is `MainWindow.__init__` calls `refresh_icons()` → `MainWindow()` returns → `win.show()`. Icons are set before the window is shown. If `refresh_icons()` were ever moved to after `win.show()`, users would see an iconless-then-icon flash. Verify this ordering in any future milestone that restructures `main()`.

### Scope discipline
- `tests/test_icons.py` and `requirements.txt` changed but have no Qt-panel UX surface. Disposed as not applicable. Keep this fast: files without a Qt widget class are not critique-surface even if they're in the diff.

## enriques-backface-2026q2-e1 (UPL-7 per-variety back-face culling) — 2026-05-22

### Token-discipline near-misses
- No short-hex or shorthand-enum slip in this diff.  The change adds no colors
  (no AI-13 surface), no Qt enums (no AI-11 surface), no processEvents (no AI-9
  surface).  Make this check fast: if the diff adds no `QColor`, no
  `Qt.AlignmentFlag`, and no `processEvents`, dispose all three axes in
  one sentence.

### Industry-comparison note (concrete recommendations generated)
- **ParaView 5.13 backface culling is an explicit opt-in checkbox** (Properties >
  Backface Styling, defaults OFF).  AVC's hardcoded-on-for-Enriques is bespoke
  relative to this convention.  The concrete recommendation: even when culling
  is technically required (double-curve seam), the user needs a status-bar
  signal or dock indicator — both competitors expose it as user-visible state.
  Quote the "ParaView opt-in checkbox vs AVC silent-on" contrast whenever
  evaluating any "hidden knob" rendering setting.
- **Mathematica `ContourPlot3D` mesh overlay is always two-sided.** Culling
  does NOT propagate to wireframe/mesh display in Mathematica — the
  mesh overlay is a topology display, not a shading surface.  This is the
  concrete model for the wireframe+culling interaction: suppress culling when
  wireframe mode is active.  Quote this as "Mathematica mesh-overlay
  convention" when evaluating any future culling-or-style interaction.

### First-launch / section-9 regressions
- No first-launch regression: `set_culling` lives inside
  `if name in VARIETIES:` in `_on_variety_changed`, never reachable from
  `-- Select --`.  Fast check pattern: trace `set_culling` to its call
  site; if it's guarded by `name in VARIETIES`, section-9.3 is clean.

### Wireframe + culling interaction — a recurring pattern to flag fast
- VTK culling applies at the face level regardless of `style="wireframe"`.
  In wireframe mode, culling hides back-facing edges, not just back-facing
  faces.  For any future milestone that adds per-variety culling, ALWAYS
  check if the `apply_to_actor` code suppresses culling when wireframe is
  active.  The fix is one line: `effective_culling = "none" if self._wireframe
  else (self._culling or "none")`.  This is the MEDIUM-2 pattern.

### Topology-claim precision for variety-level gates
- When a variety-level gate (culling, smoothing, lighting) claims "all N
  figures share topology X", verify per-figure.  The Cayley quartic symmetroid
  has ODP singularities, not the double-curve topology claimed in the UPL-7
  comment.  The gate is safe (harmless on Cayley), but the justification is
  imprecise — flag as LOW whenever a comment over-asserts math.

## status-bar-bbox-2026q2-e1 (UPL-13 status-bar spatial bbox) — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents in this diff. The change adds a single f-string suffix — no new color or Qt enum surface at all. Make this check fast: if the diff adds no QColor, no Qt.AlignmentFlag, no processEvents, and no pv.add_mesh() call, dispose AI-9/AI-11/AI-12/AI-13 in one sentence.
- `_b[1]/.2f` is a float format specifier, not a hex color — AI-13 does not apply to numeric format strings. Make this explicit when scanning: "does this arg accept a color string?" is the gate.

### Industry-comparison note (concrete recommendation generated)
- **ParaView, MeshLab, Blender all use full-extent widths (diameter), not half-extents.** ParaView's Information panel: `X Range: -1.000 to 1.000`. MeshLab's Quoted Box: `X: 2.000`. Blender status bar: `Dimensions: X: 2.00 m`. AVC's `±max` half-extent convention is unique in the peer landscape. The concrete recommendation: switch to full-extent widths (`size: Lx × Ly × Lz` computed as `bounds[1]-bounds[0]`) to align with peer vocabulary AND simultaneously fix the Hanson asymmetry issue — these two problems share a single root cause (half-extent display).
- Quote this as the "full-extent peer-alignment" recommendation for any future bbox-display milestone.

### First-launch / section-9 regressions
- No first-launch regression possible: the bbox readout lives inside the success branch of `_render_current`, which is only reached after a subtype is selected and mesh generation succeeds. Fast check: is the readout line reachable before `_on_subtype_changed` fires? If not, section-9.3 is clean.

### Status-bar overflow is the recurring risk for narrow UX milestones
- The Dwork warning path produces a 294-char status-bar message after this milestone. The ±max bbox suffix is the marginal factor that pushes the already-long warning message past visible bounds. Pattern to flag fast: whenever a suffix is appended to `base_msg`, also check the warning path `f"⚠ {_surface_warning}  |  {base_msg}"` — the warning text can be 145+ chars, so any suffix added to base_msg may be invisible on the warning path. This is MEDIUM (not HIGH) because the bbox is supplementary information, not safety-critical feedback.
- The warning path overflow is a pre-existing structural issue; the bbox suffix makes it worse but doesn't create it. Attribute correctly when writing findings.

## focus-ring-contrast-2026q2-e1 (UPL-4 FOCUS_RING accessibility) — 2026-05-22

### Token-discipline near-misses
- No short-hex or shorthand-enum in this diff. `#3c82c4` is 6-digit; no Qt enums added; no processEvents. All three axes disposed in one pass.
- The "single shared value" framing for a per-theme token is not automatically good. When OLD light=2.60:1 (FAIL) and OLD dark=5.17:1 (PASS), darkening to fix light reduces dark from 5.17:1 to 3.78:1 — a net regression in dark headroom even though both ends pass the floor. Always report the delta for BOTH themes, not just "both PASS."

### Contrast ratio comment accuracy
- Both palette comment ratios (3.56:1 light, 3.78:1 dark) verified exactly. Good discipline continued from dark-mode-2026q2-e1.
- Key discipline: "PASS" in a comment should be annotated with headroom when the margin is below ~20% above the floor. 3.56:1 on a 3:1 floor = 18.5% headroom — narrow enough that one-shade lightening reaches the boundary. Pattern: if ratio < 3.6:1 against a 3:1 floor, add "(narrow margin; do not lighten further)" to the comment.

### Industry-comparison note (concrete recommendation generated)
- macOS Sequoia default blue (#007aff) = 3.53:1 vs #f0f0f0; GNOME Adwaita (#3584e4) = 3.31:1. Both are in the same narrow-pass band as #3c82c4 (3.56:1). This is the "platform-conventional narrow-pass band" for cobalt-blue focus rings — it is not a design error, it is the peer norm. Quote this as "peer-calibrated narrow-pass" when a focus ring is challenged for thin headroom.
- Windows 11 (#005499) and macOS proper focus ring (~#0058d0) are both darker (5.6–6.8:1 on light) — they use a noticeably deeper navy that trades visual weight for accessibility margin. If the app ever wants to improve headroom, that is the direction.

### First-launch / section-9 regressions
- No first-launch regression possible from a palette-token-only diff. Fast check: does the diff touch any constructor default, any QColor() init, or any value flowing into `_render_current`? If not, section-9.3 is clean.

### Negative test as machine-readable design intent
- The docstring-only deterrent ("do NOT widen this assertion set") is a recurring pattern risk. Whenever a test has a "don't add X" docstring caveat, the stronger fix is a complementary NEGATIVE test (assert < threshold) that makes the intent machine-readable. Flag any "do not include" docstring caveat on a test as LOW and suggest a companion negative-assertion test.

## qtawesome-icons-2026q2-e2 (UPL-4 v1 camera presets + display toggles) — 2026-05-22

### Token-discipline near-misses
- No short-hex or shorthand-enum slip in this diff. `QSize(16, 16)` is a data class — not a Qt enum — so AI-11 does not apply. Make this check fast: ask "is this a Qt.* / QSizePolicy.*  enum call or a plain constructor?" `QSize(w, h)` is always the latter.
- Icon color (`_icon_color(theme)`) returns `PALETTE_LIGHT/DARK["TEXT_VALUE"]` — already 6-digit, already tested. The color does NOT flow to PyVista (AI-13 does not apply). The fast gate from qtawesome-icons-2026q2-e1 still applies: "does this color reach pv.Plotter.add_mesh?" — if not, AI-13 is clear.

### Industry-comparison surprises (concrete findings generated)
- **ParaView uses separate-glyph icons for plus/minus axis directions — NOT rotated copies.** This is the MEDIUM-1 finding: MDI6 `rotated=180` on an axis-arrow glyph produces an upside-down embedded letter ("Z" → looks like "S"; "Y" → looks like "λ") at 16 px. Quote this as the "ParaView separate-glyph convention" whenever evaluating minus-direction camera preset icons.
- **Blender + 3D Slicer use checkable QPushButton for display toggles, NOT QCheckBox+setIcon.** `QCheckBox.setIcon()` in PySide6 renders `[check-indicator][icon][label]` — a three-element prefix that is visually ambiguous (which element is the affordance?). The peer convention is `QPushButton(checkable=True)` which renders `[icon][label]` with the button depression signaling state. Flag any `QCheckBox.setIcon()` as MEDIUM when the control is a display-mode toggle (not a preference or binary option).

### First-launch / section-9 regressions
- No first-launch regression. `refresh_icons` is visual-chrome-only — no dropdown, no `_render_current`, no actor creation. Fast check: does `refresh_icons` call anything other than `setIcon` / `setIconSize` on existing widgets? If not, section-9.3 is clean. This check takes under 5 seconds on a visual scan of the method body.
- Pattern-A architecture (icons applied after construction, re-applied on theme swap at THREE call sites: `__init__`, `_on_theme_changed`, `_apply_system_theme`) is the established correct pattern. When a new panel gains a `refresh_icons` method, verify all three call sites are symmetric — missing one call site is the class of bug that produces "icons don't update on theme swap."
