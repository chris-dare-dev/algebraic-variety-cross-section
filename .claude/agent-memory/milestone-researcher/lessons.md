# lessons -- milestone-researcher

## panel-refresh-2026q2-e2 (2026-05-20)
- For palette-extraction milestones, grep all 5 source files first (`styles.py`, `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `app.py`) before writing a single token — `view_panel.py` and `parameters_panel.py` had zero hex literals, saving false scope.
- AI-13 (6-digit hex) violations can hide in Qt stylesheet strings that never touch PyVista — they are still worth fixing to remove ambiguity, and the `appearance_panel.py:48` `#888` case is the canonical example.
- When the milestone explicitly requires a `PALETTE_LIGHT` dict, the backward-compat pattern (old named constants become `= PALETTE_LIGHT["TOKEN"]`) is the zero-call-site-change migration; recommend it proactively so implementer doesn't break 5 import sites.
- AI-11 violations in existing code (`Qt.AA_ShareOpenGLContexts` at `app.py:429`) should be noted as out-of-scope pre-existing issues rather than silently fixed or ignored.
- WCAG contrast verification for disabled-state colors (`TEXT_DISABLED = #aaaaaa`) correctly uses the WCAG exception for disabled elements; don't flag intentional low-contrast disabled text as a bug.

## panel-refresh-2026q2-e2 (2026-05-20)
- For palette-token refactors: scan ALL files that import from styles.py AND all files using inline hex literals not yet in styles.py (grep for `#[0-9a-fA-F]{3,6}` across *.py catches both 3-digit and 6-digit hex). appearance_panel.py and app.py both had untracked hex that styles.py did not cover.
- External naming conventions (qt-material, napari, ParaView, QPalette) all confirm semantic role names beat CSS-hex-variable names: BG_VIEWPORT not viewport_background_hex, TEXT_MUTED not muted_color_hex.
- `styles.py` not `palette.py` is correct for AVC scale: any split adds navigation cost without benefit when the existing module is already the centralized stylesheet per CONTEXT.md §2 and AI-12 references it explicitly.
- Downstream API planning: map every downstream milestone (UPL-4 dark-mode, UPL-5 per-variety color, UPL-11 overlay) to its specific dict key reads BEFORE writing the brief so token names are stable across the sprint. Renaming tokens after UPL-1 ships invalidates downstream sketches.
- SHORT HEX AI-13 adjacency: appearance_panel.py:48 `#888` is Qt-stylesheet-only (safe for Qt, but flagged by UPL-21). Resolving it in the same PR as PALETTE_LIGHT is the cleanest approach — add `SWATCH_BORDER = "#888888"` to the dict.

## graph-and-window-2026q2-e1 (2026-05-21)
- For XS-effort tooling milestones (3 candidates, 1-day sprint), keep the brief proportionate: skip arXiv/OSS web searches entirely. The brief value comes from precise file:line attach points, not external triangulation.
- `clearFocus()` is the correct Qt primitive to suppress focus-ring artifacts in offscreen widget grabs — `setFocusPolicy(Qt.FocusPolicy.NoFocus)` on a container widget does NOT prevent child tab-stops from receiving focus. Memorize this distinction for any future milestone touching panel-chrome captures.
- Bare `QDockWidget` outside `QMainWindow` is explicitly cleared by AI-3's clarifying paragraph — safe for offscreen panel grabs. The QSS `QDockWidget::title` rule fires on standalone dock widgets, which is the entire point of UPL-27.
- For `add_mesh` lighting kwargs (ambient/diffuse), check whether `appearance_panel.apply_to_actor()` overrides VTK actor properties post-add — if it calls `SetAmbient`/`SetDiffuse` the `add_mesh` kwargs would be overwritten. Check this before implementing any lighting-param candidate.
- When a milestone touches `render-panel-chrome.py` and `agent-prompts.md` in the same PR, sequence the agent-prompts.md edit first (simpler, no Qt import changes) then the chrome script (has import and call-site changes).
