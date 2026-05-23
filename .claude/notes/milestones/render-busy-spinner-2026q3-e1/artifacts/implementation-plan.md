# Implementation plan — render-busy-spinner-2026q3-e1

**Inline path. ~135–150 LOC across 4 files.** Lift the CONTEXT.md §9 spinner deferral. The original AI-9 blocker (QMovie.updated firing during processEvents) is structurally obsolete since realtime-variety-render-e4 moved surface.generate() onto a QThreadPool worker.

**Two load-bearing researcher catches** that this plan honors:
1. Widget MUST be `QPushButton(flat=True, enabled=False)`, NOT `QLabel` — qtawesome `Spin` animation requires `QIcon.paint()` in `paintEvent`, which only `QAbstractButton` subclasses call. `QLabel.setPixmap()` captures a static frame and the animation dies.
2. Position MUST be `addPermanentWidget(spinner)` (right side), NOT `addWidget` — `addWidget` slots get obscured by `showMessage()` calls, and the app calls `showMessage` at every render event.

1. **icons.py** —
   - Replace the deferral comment at icons.py:57–61 with a "shipped by …" note.
   - Add module constant `RENDER_BUSY_SPINNER_ICON_NAME = "mdi6.loading"` after `HQ_SMOOTHING_ICON_NAME` (line 188).
   - Add factory `render_busy_spinner_icon(widget, theme="dark")` that returns `qta.icon("mdi6.loading", color=_icon_color(theme), animation=qta.Spin(widget, interval=10, step=6))`. Full docstring covering AI-9 audit + AI-15 attestation per researcher §4.6.
   ~30 LOC delta.

2. **app.py** —
   - Add `QPushButton` to the `from PySide6.QtWidgets import …` block.
   - In `MainWindow.__init__` immediately after the `QStatusBar` construction (~app.py:149): construct `self._render_busy_spinner = QPushButton()`, `.setFlat(True)`, `.setEnabled(False)`, `.setFixedSize(16, 16)`, `.setToolTip(…activity indicator, not progress…)`, `.setVisible(False)`, `self.statusBar().addPermanentWidget(self._render_busy_spinner)`.
   - After the three existing `refresh_icons()` calls (~app.py:301–303): set the spinner icon via `icons.render_busy_spinner_icon(self._render_busy_spinner, self._active_theme)`.
   - In `_on_theme_changed` and `_apply_system_theme`: same one-liner to refresh the icon.
   - At app.py:670 (`self._computing = True`): add `self._render_busy_spinner.setVisible(True)`.
   - At app.py:829 (`self._computing = False` in `_on_mesh_ready` finally): add `self._render_busy_spinner.setVisible(False)`.
   ~22 LOC delta.

3. **tests/test_render_busy_spinner.py** (new file) — 6 pure-source-grep tests (AI-2 compliant) per researcher §6:
   - `test_app_has_render_busy_spinner_widget` (constructed + addPermanentWidget)
   - `test_app_render_busy_spinner_uses_qtawesome_spin_animation` (icons.py uses qta.Spin)
   - `test_app_render_busy_spinner_starts_hidden` (setVisible(False) precedes setVisible(True) in source)
   - `test_app_render_busy_spinner_shown_on_computing_true` (spinner show adjacent to _computing=True)
   - `test_app_render_busy_spinner_hidden_on_computing_false` (spinner hide adjacent to _computing=False)
   - `test_icons_module_has_render_busy_spinner_icon_factory` (factory + constant + mdi6 family)
   - PLUS an AI-9 regression-guard: assert `icons.py`'s `render_busy_spinner_icon` docstring contains "AI-9" and "paint" (anchors the future-maintainer understanding that the timer is a paint-path-only construct).
   ~80 LOC delta.

4. **CONTEXT.md** — replace the §9 spinner-deferral paragraph with a "shipped by render-busy-spinner-2026q3-e1" note covering: (a) the AI-9-blocker-now-obsolete rationale, (b) the QPushButton-not-QLabel + addPermanentWidget-not-addWidget gotchas (load-bearing for future maintainers), (c) the activity-not-progress AI-15 attestation. If `§3` has an inline spinner deferral sentence, update it too.
   ~12 LOC delta.

5. **Verify** —
   - `.venv/bin/pytest tests/ -q` reaches 385 + 7 = 392.
   - **No off-screen render verification needed** — status-bar widget is Qt-chrome, not a VTK render path.

6. **Commit** — `feat(render-busy-spinner-2026q3-e1): status-bar render-busy spinner (CONTEXT.md §9 deferral closed)`.
