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
