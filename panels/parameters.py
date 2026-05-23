"""ParametersPanel — dynamic slider panel driven by a Surface's ParamSpec list.

Repopulated each time the user picks a different surface. Emits ``params_changed``
when a slider is released, carrying the current parameter dict. The signal fires
on release rather than continuously to avoid thrashing the marching-cubes call.

The panel also hosts a **grid mode** (:class:`parameter_grid_panel.ParameterGridPanel`):
a "Grid mode" toggle swaps the slider stack for a draggable-dot grid that
adjusts two or three parameters at once. Both views share one source of
parameter truth — toggling preserves the current values, and the grid funnels
its changes back through the same ``params_changed`` signal, so the single
``_computing``-guarded render path in ``app.py`` is unchanged.
"""

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

import parameter_grid as pg
from panels.parameter_grid_panel import ParameterGridPanel
from surfaces import ParamSpec
from ui_helpers import Debouncer, build_slider_row


class ParametersPanel(QWidget):
    # Emitted on a slider RELEASE (or Reset) — the full-render trigger for
    # every surface, fast or slow.  Unchanged since before e2 (INT-2).
    params_changed = Signal(dict)
    # realtime-variety-render-e2-s2 (CAND-8): emitted on a DEBOUNCED drag tick
    # (at most once per 80 ms during a continuous drag), carrying the live
    # {name: value} dict.  A distinct signal — not a second `params_changed`
    # emit — so a consumer can tell a drag-tick from a release: `app.py`
    # speed-routes drag ticks (fast surfaces render, slow surfaces ignore)
    # while releases always render.  e4's coarse-LOD work will also key off
    # this drag/release distinction (coarse mesh on preview, full on release).
    params_preview_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sliders: dict[str, QSlider] = {}
        self._value_labels: dict[str, QLabel] = {}
        self._specs: list[ParamSpec] = []

        # realtime-variety-render-e1-s4 (CAND-6): shared QTimer debounce for
        # drag-time slider ticks.  DORMANT in e1 — `_on_value_changed`
        # registers ticks with `request()` (so the coalescing machinery is
        # wired and exercisable), but the deferred callback only updates the
        # live readout; it does NOT trigger a render.  Render-on-drag is
        # gated to e2 (`typical_ms` speed routing) / e4 (coarse-LOD); until
        # then the render trigger stays exclusively on `sliderReleased`
        # (INT-2).  The release path calls `_debouncer.cancel()` so a
        # trailing debounced callback can never shadow the release render.
        self._debouncer = Debouncer(self._on_debounced_tick)

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(6, 6, 6, 6)
        self._root.setSpacing(6)

        # Context hint banner — shown only when a variety provides extra context
        # (e.g. CY3 parametric surfaces).  Hidden by default.
        # dark-mode-2026q2-e1 rect: QSS role property (was MUTED_TEXT_STYLE inline).
        self._hint_label = QLabel("")
        self._hint_label.setProperty("role", "muted")
        self._hint_label.setWordWrap(True)
        self._hint_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._hint_label.hide()
        self._root.addWidget(self._hint_label)

        # Grid-mode toggle — swaps the slider stack for the draggable-dot grid.
        # Disabled for 0/1-param surfaces (a grid needs >= 2 axes).
        self._grid_toggle = QPushButton("Grid mode")
        self._grid_toggle.setCheckable(True)
        self._grid_toggle.setEnabled(False)
        self._grid_toggle.setToolTip("Grid mode needs at least 2 parameters")
        self._grid_toggle.toggled.connect(self._on_grid_toggled)
        self._root.addWidget(self._grid_toggle)

        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(10)
        self._root.addLayout(self._content_layout)

        # dark-mode-2026q2-e1 rect: QSS role property (was MUTED_TEXT_STYLE inline).
        self._empty_label = QLabel("(no parameters for this surface)")
        self._empty_label.setProperty("role", "muted")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(self._empty_label)

        # Grid panel — created once, shown only while the toggle is checked.
        self._grid_panel = ParameterGridPanel()
        self._grid_panel.grid_params_changed.connect(self._on_grid_params_changed)
        # e2-s2 (CAND-8): relay the grid's debounced drag preview into this
        # panel's `params_preview_changed` so a grid dot-drag on a Hanson
        # surface gets the same speed-routed continuous render as a slider.
        self._grid_panel.grid_params_preview_changed.connect(
            self._on_grid_params_preview_changed
        )
        self._grid_panel.hide()
        self._root.addWidget(self._grid_panel)

        # Reset button — styled via object name so the app stylesheet targets it
        self._reset_btn = QPushButton("Reset all to defaults")
        self._reset_btn.setObjectName("resetDefaultsBtn")
        self._reset_btn.setToolTip(
            "Reset all parameter sliders to their default values (Ctrl+D)"
        )
        self._reset_btn.clicked.connect(self._reset_defaults)
        self._reset_btn.setEnabled(False)
        self._root.addWidget(self._reset_btn)

        self._root.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_context_hint(self, text: str) -> None:
        """Show or hide a small informational banner above the sliders.

        Pass an empty string to hide the banner (e.g. for K3/Enriques where
        no extra context is needed).  Pass a non-empty string to show it —
        used by MainWindow to surface CY3-specific notes ("each figure is a
        2D real shadow of a 6-dimensional manifold") without cluttering the
        panel with permanent text.
        """
        if text:
            self._hint_label.setText(text)
            self._hint_label.show()
        else:
            self._hint_label.hide()

    def set_specs(self, specs: Iterable[ParamSpec]) -> None:
        """Rebuild the panel for a new surface's parameter spec list.

        Switching surfaces resets both the slider stack and the grid panel
        consistently: each is rebuilt from the new specs with default values.
        """
        self._clear_content()
        self._specs = list(specs)

        # Grid mode is only meaningful for >= 2 parameters.  Switching to a
        # 0/1-param surface forces the panel back to slider view and disables
        # the toggle.
        grid_ok = pg.grid_enabled(self._specs)
        self._grid_toggle.blockSignals(True)
        self._grid_toggle.setEnabled(grid_ok)
        if not grid_ok and self._grid_toggle.isChecked():
            self._grid_toggle.setChecked(False)
        self._grid_toggle.setToolTip(
            "Adjust two or three parameters at once on a draggable grid"
            if grid_ok
            else "Grid mode needs at least 2 parameters"
        )
        self._grid_toggle.blockSignals(False)

        if not self._specs:
            self._empty_label.show()
            self._content_layout.addWidget(self._empty_label)
            self._reset_btn.setEnabled(False)
            self._grid_panel.hide()
            return

        self._empty_label.hide()
        for spec in self._specs:
            self._content_layout.addWidget(self._build_row(spec))
        self._reset_btn.setEnabled(True)

        # Rebuild the grid panel from the same specs + default values so the
        # two views start coherent.
        defaults = {spec.name: spec.default for spec in self._specs}
        if grid_ok:
            self._grid_panel.set_specs(self._specs, defaults)
        # Honor whichever view the toggle currently selects.
        self._apply_view_mode()

    def values(self) -> dict[str, float]:
        """Return the current {name: value} dict from whichever view is active.

        Grid mode and slider mode share one source of truth: in grid mode the
        grid panel's values are authoritative, otherwise the sliders are.
        """
        if self._grid_toggle.isChecked():
            return dict(self._grid_panel.values())
        return {spec.name: self._slider_to_value(spec) for spec in self._specs}

    def refresh_icons(self, theme: str = "dark") -> None:
        """Re-apply the qtawesome icon on the Reset Defaults button with
        the active theme's color.  Called by ``MainWindow.__init__``
        after panel construction and by ``MainWindow._on_theme_changed``
        / ``_apply_system_theme`` on theme swap.  See ``icons.py`` for the
        full QApplication-availability discipline this method respects
        (qtawesome-icons-2026q2-e1 / UPL-4).

        Sets an explicit 16x16 icon size for platform-independent
        rendering (frontend-ux critic LOW-1 — matches the size set on the
        View dock's icons).
        """
        import icons
        from PySide6.QtCore import QSize

        self._reset_btn.setIconSize(QSize(16, 16))
        self._reset_btn.setIcon(icons.reset_defaults_icon(theme))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _clear_content(self) -> None:
        # Detach every widget currently in the content layout.
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w is not None and w is not self._empty_label:
                w.setParent(None)
                w.deleteLater()
        self._sliders.clear()
        self._value_labels.clear()

    def _build_row(self, spec: ParamSpec) -> QWidget:
        """Build one slider row via the shared factory and register its widgets.

        The label+slider+range layout lives in :func:`ui_helpers.build_slider_row`
        so the slider stack here and the residual sliders in the grid panel
        (:meth:`parameter_grid_panel.ParameterGridPanel._build_residual_row`)
        cannot drift apart.  The factory applies the dark-mode-aware QSS
        ``role`` properties for the colour-bearing labels.
        """
        row, slider, value_lbl = build_slider_row(
            spec,
            spec.default,
            on_value_changed=self._on_value_changed,
            on_released=self._on_slider_released,
            include_description=True,
        )
        self._sliders[spec.name] = slider
        self._value_labels[spec.name] = value_lbl
        return row

    def _on_value_changed(self, spec: ParamSpec) -> None:
        # Live-update the readout, but don't regenerate until release.
        v = self._slider_to_value(spec)
        self._value_labels[spec.name].setText(pg.format_value(v, spec))
        # CAND-6 (e1-s4): register the drag tick with the shared debounce.
        # Dormant in e1 — `_on_debounced_tick` does not render; this only
        # exercises the coalescing machinery so e2/e4 can activate it.
        self._debouncer.request()

    def _on_debounced_tick(self) -> None:
        """Debounced drag-tick callback (CAND-6 e1-s4, activated e2-s2).

        Fires at most once per debounce interval (80 ms) during a continuous
        slider drag.  e2-s2 (CAND-8): it now emits `params_preview_changed`
        with the live values.  The panel deliberately does NOT decide whether
        a render happens — it has no visibility into the current surface's
        `typical_ms`.  `app.py` connects this signal to a speed-routed
        handler (`should_render_on_drag`): fast surfaces (Hanson) render at
        every tick, slow surfaces ignore the preview and stay release-only.
        The release path (`params_changed`) is unchanged for all surfaces.
        """
        self.params_preview_changed.emit(self.values())

    def _on_slider_released(self) -> None:
        # CAND-6 (e1-s4): cancel any pending debounced drag callback so it
        # cannot fire after — and shadow — this release render.  The release
        # path itself is unchanged: it emits `params_changed` directly.
        self._debouncer.cancel()
        self.params_changed.emit(self.values())

    def _reset_defaults(self) -> None:
        """Reset every parameter to its default — works in both view modes."""
        defaults = {spec.name: spec.default for spec in self._specs}
        for spec in self._specs:
            slider = self._sliders[spec.name]
            slider.blockSignals(True)
            slider.setValue(pg.value_to_tick(spec.default, spec))
            slider.blockSignals(False)
            self._value_labels[spec.name].setText(pg.format_value(spec.default, spec))
        # Keep the grid panel in sync so a later toggle shows correct values.
        if pg.grid_enabled(self._specs):
            self._grid_panel.set_values(defaults)
        self.params_changed.emit(self.values())

    # ------------------------------------------------------------------
    # Grid-mode wiring
    # ------------------------------------------------------------------

    def _slider_values(self) -> dict[str, float]:
        """The current {name: value} dict as read from the slider stack."""
        return {spec.name: self._slider_to_value(spec) for spec in self._specs}

    def _sync_sliders_to(self, values: dict[str, float]) -> None:
        """Push *values* into the slider widgets without emitting."""
        for spec in self._specs:
            if spec.name not in values:
                continue
            slider = self._sliders.get(spec.name)
            if slider is None:
                continue
            slider.blockSignals(True)
            slider.setValue(pg.value_to_tick(values[spec.name], spec))
            slider.blockSignals(False)
            self._value_labels[spec.name].setText(
                pg.format_value(values[spec.name], spec)
            )

    def _apply_view_mode(self) -> None:
        """Show the slider stack or the grid panel per the toggle state."""
        grid_on = self._grid_toggle.isChecked()
        # Slider rows live in _content_layout; hide/show them as a group.
        for i in range(self._content_layout.count()):
            w = self._content_layout.itemAt(i).widget()
            if w is not None and w is not self._empty_label:
                w.setVisible(not grid_on)
        self._grid_panel.setVisible(grid_on and bool(self._specs))

    def _on_grid_toggled(self, checked: bool) -> None:
        """Toggle between slider and grid view, preserving current values."""
        if checked:
            # Hand the slider values to the grid so the dot starts in place.
            self._grid_panel.set_values(self._slider_values())
        else:
            # Adopt the grid's values back into the sliders.
            self._sync_sliders_to(self._grid_panel.values())
        self._apply_view_mode()

    def _on_grid_params_changed(self, values: dict) -> None:
        """Relay a grid dot-release into the panel's single params_changed.

        Keeping the sliders synced means the two views never diverge, and
        re-using ``params_changed`` means the grid funnels through the same
        ``_computing``-guarded render path in app.py — no second render path.
        """
        self._sync_sliders_to(values)
        self.params_changed.emit(dict(values))

    def _on_grid_params_preview_changed(self, values: dict) -> None:
        """Relay a grid debounced drag-tick into ``params_preview_changed``.

        e2-s2 (CAND-8): the grid's continuous-drag preview funnels through the
        same drag-tick signal as the slider stack, so app.py's speed-routed
        handler sees one signal regardless of which view emitted it.  The
        hidden slider stack is kept in sync so toggling back mid-session
        starts coherent — `_sync_sliders_to` blocks slider signals, so this
        relay never feeds back into the debouncer.
        """
        self._sync_sliders_to(values)
        self.params_preview_changed.emit(dict(values))

    # ----- value <-> tick conversion (slider stores integer ticks) ----
    #
    # The value<->tick mapping and the readout format both live in the
    # Qt-free ``parameter_grid`` module so the slider stack and the grid
    # panel's residual sliders share one source of truth (no drift).

    def _slider_to_value(self, spec: ParamSpec) -> float:
        return pg.tick_to_value(self._sliders[spec.name].value(), spec)
