
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)
- Hotspots observed: app.py 1900 LOC (9 logical sections; _on_mesh_ready 239 LOC, _render_current 173 LOC, _on_variety_changed 178 LOC); surfaces.py 1811 LOC (Numba kernels 401 LOC are the cleanest extraction candidate — no local imports)
- Surprising overlap not in prior runs: parameters_panel.py imports parameter_grid_panel.py — they are NOT duplicates but a strict parent/child container relationship; the misleading naming is a documentation gap, not an architecture gap
- Surprising finding: .claude/ is mostly git-tracked (380 files) despite CONTEXT.md:47 saying "Don't commit .claude/" — the .gitignore only excludes .claude/worktrees/ and .claude/scheduled_tasks.lock; this is a governance discrepancy
- AI-invariant constraints encountered: AI-8 (VARIETIES registry + ParamSpec/Surface must stay co-importable from surfaces); AI-12 (parameter_grid_panel.py:L232 BG_GRID_SCENE hardcode is a dark-mode gap NOT caught by test_no_inline_color_styles_in_panel_files because that test omits parameter_grid_panel.py from its panel_files tuple); AI-6 (numba.config side effect on surfaces.py import must travel with any kernel extraction)

## CORRECTION 2026-05-23 (restructure-full-audit-2026q2-r1 batch 3)
- The AI-12 gap described above (`parameter_grid_panel.py:L232 BG_GRID_SCENE hardcode`) was CLOSED by Batch 3.
- `parameter_grid_panel.py` L232 (approximate) no longer calls `setStyleSheet(f"background: {BG_GRID_SCENE}...")`. It now uses `self._view.setProperty("role", "grid-scene")` + `style().unpolish()`/`style().polish()` — the canonical QSS-role pattern from CONTEXT.md §4.3b.
- `styles.py` gained `QWidget[role="grid-scene"]` selectors in both palette render paths.
- `test_no_inline_color_styles_in_panel_files` now covers `parameter_grid_panel.py` (added to the guard tuple in `tests/test_styles_palette.py`).
- The original lesson text above remains as historical record of the gap at audit time; this CORRECTION notes it is resolved.
