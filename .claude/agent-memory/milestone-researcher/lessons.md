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

## variety-palette-2026q2-e1 (2026-05-21)
- For pure palette/wiring milestones, skip arXiv and OSS web searches entirely — all signal is in repo-local files and numerically-computed contrast ratios.
- WCAG contrast computation for variety colors: "surface color on dark viewport" uses the 4.5:1 text threshold (not 3:1 non-text) because the surface-family name appears as rendered text in the status bar using the same color token. Confirm what threshold applies before computing candidates.
- Unicode key identity is a silent failure mode for VARIETY_DEFAULT_COLOR: "Calabi–Yau 3-fold" uses U+2013 en-dash (not ASCII hyphen), "Fano 3-fold (ρ=1)" uses U+03C1. The only safe approach is copy-paste from surfaces.py, confirmed at surfaces.py:968 and surfaces.py:986.
- Hue separation ≥25 degrees (HSV) between all variety color pairs is the minimum for perceptual distinguishability. Pairwise luminance ratios near 1.0 are fine if hue angles differ sufficiently — don't mistake near-equal luminance for near-equal appearance.
- The stub test `test_variety_default_color_is_stub_for_upl5` asserts `== {}` and must be DELETED (not supplemented) when the dict is populated — otherwise the test suite contains a guaranteed contradiction.
- `set_default_color` on AppearancePanel must NOT call render — the caller flows naturally into `_render_current` → `apply_to_actor`. Calling render inside `set_default_color` would be premature (no mesh exists yet on variety-combo change before subtype is selected).
- BG_SURFACE_DEFAULT is the correct fallback in `VARIETY_DEFAULT_COLOR.get(name, BG_SURFACE_DEFAULT)` — it's already exported from styles.py but may not be imported at the call site in app.py; check import line first.
