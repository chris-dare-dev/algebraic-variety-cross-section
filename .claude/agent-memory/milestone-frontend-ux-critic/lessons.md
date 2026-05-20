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
