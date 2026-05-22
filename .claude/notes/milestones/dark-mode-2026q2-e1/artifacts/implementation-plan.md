# Implementation plan — dark-mode-2026q2-e1

**Inline path.** ~270 LOC across 5 files. Researcher's recommended sequencing.

1. **styles.py refactor** — Extract the existing `APP_STYLESHEET` f-string into a `_render_stylesheet(palette: dict) -> str` function so the same template renders against either palette. Add `PALETTE_DARK` (19 tokens, all WCAG-verified per the brief). Add `VARIETY_DEFAULT_COLOR_DARK = VARIETY_DEFAULT_COLOR` (reuse — all 4 light colors pass 3:1 on `BG_PANEL_DARK=#252526`, closing MF1). Add `get_variety_default_colors(theme)` accessor. Module-level constants `APP_STYLESHEET = _render_stylesheet(PALETTE_LIGHT)` and `APP_STYLESHEET_DARK = _render_stylesheet(PALETTE_DARK)`.

2. **app.py** — Add Theme menu (Light / Dark / Follow-system) via `menuBar().addMenu` + `QAction` + `QActionGroup`. `_on_theme_changed(name)` swaps `QApplication.setStyleSheet` synchronously (AI-9 safe). Track active theme via `self._active_theme`. Wire `QGuiApplication.styleHints().colorSchemeChanged` for follow-system. Update both `_on_variety_changed` and `_on_subtype_changed` to call `styles.get_variety_default_colors(self._active_theme).get(name, BG_SURFACE_DEFAULT)`. Change `main()` default to `APP_STYLESHEET_DARK`.

3. **appearance_panel.py** — ZERO changes needed (researcher confirmed). The `set_default_color(hex_str)` signature is theme-agnostic; theme resolution happens at the call site in `app.py` via `get_variety_default_colors`.

4. **tests/test_styles_palette.py** — Add 7 dark twins (parallel to existing light tests) + 5 `VARIETY_DEFAULT_COLOR_DARK` tests + 1 `get_variety_default_colors` test. Reuse existing module-level `_luminance`/`_ratio` helpers; no new fixtures needed. Honor the BG_DOCK_HEADER structural-contrast exception (do NOT assert 3:1 there).

5. **CONTEXT.md §4.3b** — Add a Theme System section (~25 LOC) documenting dual-palette pattern, `_render_stylesheet` parameterization, where the Theme menu lives, the V0 "dark default, no persistence" contract.

6. **Verify** — `.venv/bin/python -m pytest tests/ -q` (must include new dark-bg WCAG tests; expect 180+12 = 192 total). Off-screen render verification with the dark default applied. Manual theme-toggle smoke test via `app.py` launch (out-of-scope for automated tests; document the manual step).

7. **Commit** — Single conventional commit: `feat(dark-mode-2026q2-e1): add PALETTE_DARK + APP_STYLESHEET_DARK + Theme menu`.

**Pre-existing AI-11 violation** at `app.py:475` (`Qt.AA_ShareOpenGLContexts` unqualified) is **explicitly OUT of scope** per the researcher — fixing it would contaminate this milestone's scope. Will surface in a later milestone or as a follow-up.
