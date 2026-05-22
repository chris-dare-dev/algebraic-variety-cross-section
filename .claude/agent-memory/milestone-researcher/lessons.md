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

## dark-mode-2026q2-e1 (2026-05-22)
- For dark-mode stylesheet milestones, compute WCAG ratios numerically before writing a single token — ratio(candidate, BG_PANEL_DARK) must be explicit; "passes qualitatively" is not sufficient for the AI-12 sub-task the challenger MAJOR-flagged.
- BG_PANEL_DARK = #252526 is the right anchor: dark but not pitch-black, leaves room for structural separation (dock header), and is in the Quanta/3Blue1Brown/VS Code dark register confirmed by synthesis.md.
- Structural background tokens (BG_DOCK_HEADER, BG_RESET_BTN, BG_CAMERA_BTN_HOVER) do NOT need 3:1 vs BG_PANEL because they are not UI component boundaries — the BORDER token carries the WCAG 1.4.11 obligation. Document this explicitly to prevent the implementer from flagging them as failures.
- QGuiApplication.styleHints().colorScheme() (Qt 6.5+, guaranteed by the >=6.6 pin) provides native follow-system detection with a colorSchemeChanged signal — no darkdetect dep needed. darkdetect is BSD-3-Clause but polling-only; the Qt native API wins.
- APP_STYLESHEET_DARK naming is load-bearing: render-panel-chrome.py detects it via getattr(styles, "APP_STYLESHEET_DARK", None) (styles.py:151-157). Do NOT rename.
- _render_stylesheet(palette: dict) approach avoids all drift risk from duplicate f-string templates. Every palette token must be referenced as palette["TOKEN"] inside the function, not via named constants (which are bound to PALETTE_LIGHT at module load).
- VARIETY_DEFAULT_COLOR_DARK is identical to VARIETY_DEFAULT_COLOR: all four light-mode colors clear 3:1 (swatch chip) and 4.5:1 (canvas) against BG_PANEL_DARK (#252526) and BG_VIEWPORT (#2f2f2f) respectively. Reuse verbatim — close the MF1 deferred finding with a test assertion, not new hex values.
- Pattern A (styles.get_variety_default_colors(theme) in app.py) keeps AppearancePanel decoupled from theme state. AppearancePanel.set_default_color() signature stays hex-string-only. No change to appearance_panel.py beyond ~5 LOC for the import of the new accessor.
- TEXT_DISABLED_DARK must NOT have a WCAG test — it intentionally uses WCAG §1.4.3 disabled exception. Document in the dict comment, not a test assertion. Same pattern as light mode TEXT_DISABLED = #aaaaaa.
- For dark-mode milestones, LOC estimate splits: ~270 LOC total (styles.py ~75, app.py ~55, appearance_panel.py ~5, tests ~110, CONTEXT.md ~25). This fits the inline (non-delegated) path.

## qtawesome-icons-2026q2-e1 (2026-05-22)
- `qta.icon()` requires a running QApplication — confirmed from iconic_font.py source. Returns empty QIcon + UserWarning (no exception) if called without one. This means panel `_build_ui()` constructors must NOT call icon functions; defer all `qta.icon()` calls to a `refresh_icons(theme)` method called from `MainWindow.__init__` after widget construction.
- Lazy-import of `qtawesome` at module level (`import qtawesome` statement) does NOT trigger font loading. Font loading fires on the first `qta.icon()` call. Both deferred-import AND deferred first-call are needed to avoid the ~150-200ms cold-boot cost at app-module-import time.
- The `global _qta = None` pattern with per-function import is the canonical fix for qtawesome module-level issue #144. `functools.cache` is wrong here because it would pin the first theme's icon color across theme swaps.
- MDI icon picks for 3D viewer buttons: `mdi6.camera-retake` (Reset Camera — camera + circular refresh arrow), `mdi6.camera` (Screenshot — classic camera body), `mdi6.restore` (Reset Defaults — counterclockwise undo arrow). All in MDI 1.x–3.x, safely in the mdi6 6.9.96 bundle. Run `qta-browser` to verify at install time.
- qtawesome `color=` argument accepts "#rrggbb" 6-digit hex strings — `QColor(color)` is the underlying call. AI-13 compliance is automatic when using `PALETTE_*["TEXT_VALUE"]` as the color source.
- For XS/S icon-adoption milestones, skip arXiv and OSS web searches entirely. The value is in precise file:line attach points and icon-name verification, not external triangulation. Web research budget: 15 minutes on PyPI + icon catalog pages only.
- Instance-attribute storage gap: `view_panel.py` `_make_camera_group()` and `_make_screenshot_group()` both create buttons as local variables (not stored as instance attrs). Implementer must add `self._reset_camera_btn` and `self._shot_btn` to enable `refresh_icons()` to reach the buttons.
