# Implementation plan — qtawesome-icons-2026q2-e1

**Inline path.** ~148 LOC across 7 files. Researcher's sequencing + R1/R3 fixes baked in.

1. **requirements.txt** — Add `qtawesome>=1.4.2,<2` (MIT, PySide6 6.8.x segfault fixed in 1.4.1).

2. **Install dep into .venv** — `.venv/bin/pip install 'qtawesome>=1.4.2,<2'`.

3. **icons.py** (new) — Per-function lazy-import factory: `_qta = None` sentinel + `_get_qta()` lazy-import; `_icon_color(theme)` → returns `PALETTE_*['TEXT_VALUE']`; 3 icon factories. Docstring warns: qta.icon() requires running QApplication.

4. **view_panel.py** — Promote 2 local vars to instance attrs (R1, R3) + add `refresh_icons(theme)`.

5. **parameters_panel.py** — Add `refresh_icons(theme)` using existing `self._reset_btn`.

6. **app.py** — Call `refresh_icons` in 3 places: `MainWindow.__init__` (initial paint), `_on_theme_changed` (after stylesheet swap), `_apply_system_theme` (after stylesheet swap).

7. **tests/test_icons.py** (new) — 4 tests; 3 AI-2-compliant + 1 QApplication-guarded with pytest.skip.

8. **CONTEXT.md §3** — Brief dep-stack mention.

9. **Verify** — pytest passes; cold-boot timing `time .venv/bin/python -c "import app"` shows <50ms regression.

10. **Commit** — `feat(qtawesome-icons-2026q2-e1): adopt qtawesome for Reset Camera / Screenshot / Reset Defaults icons (v0)`.
