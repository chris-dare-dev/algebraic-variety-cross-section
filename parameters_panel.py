"""ParametersPanel — dynamic slider panel driven by a Surface's ParamSpec list.

Repopulated each time the user picks a different surface. Emits ``params_changed``
when a slider is released, carrying the current parameter dict. The signal fires
on release rather than continuously to avoid thrashing the marching-cubes call.
"""

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from styles import MUTED_TEXT_STYLE, RANGE_LABEL_STYLE, SMALL_LABEL_STYLE, VALUE_MONO_STYLE
from surfaces import ParamSpec


class ParametersPanel(QWidget):
    params_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sliders: dict[str, QSlider] = {}
        self._value_labels: dict[str, QLabel] = {}
        self._specs: list[ParamSpec] = []

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

        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(10)
        self._root.addLayout(self._content_layout)

        # dark-mode-2026q2-e1 rect: QSS role property (was MUTED_TEXT_STYLE inline).
        self._empty_label = QLabel("(no parameters for this surface)")
        self._empty_label.setProperty("role", "muted")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(self._empty_label)

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
        """Rebuild the panel for a new surface's parameter spec list."""
        self._clear_content()
        self._specs = list(specs)

        if not self._specs:
            self._empty_label.show()
            self._content_layout.addWidget(self._empty_label)
            self._reset_btn.setEnabled(False)
            return

        self._empty_label.hide()
        for spec in self._specs:
            self._content_layout.addWidget(self._build_row(spec))
        self._reset_btn.setEnabled(True)

    def values(self) -> dict[str, float]:
        return {spec.name: self._slider_to_value(spec) for spec in self._specs}

    def refresh_icons(self, theme: str = "dark") -> None:
        """Re-apply the qtawesome icon on the Reset Defaults button with
        the active theme's color.  Called by ``MainWindow.__init__``
        after panel construction and by ``MainWindow._on_theme_changed``
        / ``_apply_system_theme`` on theme swap.  See ``icons.py`` for the
        full QApplication-availability discipline this method respects
        (qtawesome-icons-2026q2-e1 / UPL-4).
        """
        import icons

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
        row = QWidget()
        outer = QVBoxLayout(row)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        # Header: parameter name on the left, current value on the right
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        name_lbl = QLabel(spec.label)
        name_lbl.setStyleSheet(SMALL_LABEL_STYLE)
        name_lbl.setToolTip(spec.description or spec.label)
        header.addWidget(name_lbl)
        header.addStretch(1)
        # dark-mode-2026q2-e1 rect: QSS role property (was VALUE_MONO_STYLE inline).
        value_lbl = QLabel(self._format_value(spec.default, spec))
        value_lbl.setProperty("role", "value-mono")
        value_lbl.setToolTip("Current value")
        header.addWidget(value_lbl)
        outer.addLayout(header)

        # Slider
        slider = QSlider(Qt.Orientation.Horizontal)
        ticks = max(1, int(round((spec.maximum - spec.minimum) / spec.step)))
        slider.setRange(0, ticks)
        slider.setValue(self._value_to_tick(spec.default, spec))
        slider.setToolTip(
            f"{spec.label}\n"
            f"Range: {spec.minimum:g} – {spec.maximum:g}  |  Step: {spec.step:g}"
        )
        slider.valueChanged.connect(lambda _v, s=spec: self._on_value_changed(s))
        slider.sliderReleased.connect(self._on_slider_released)
        outer.addWidget(slider)

        # Min / max range labels flanking below the slider
        range_row = QHBoxLayout()
        range_row.setContentsMargins(0, 0, 0, 0)
        # dark-mode-2026q2-e1 rect: QSS role property (was RANGE_LABEL_STYLE inline).
        min_lbl = QLabel(f"{spec.minimum:g}{spec.suffix}")
        min_lbl.setProperty("role", "range-label")
        min_lbl.setToolTip("Minimum value")
        max_lbl = QLabel(f"{spec.maximum:g}{spec.suffix}")
        max_lbl.setProperty("role", "range-label")
        max_lbl.setToolTip("Maximum value")
        max_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        range_row.addWidget(min_lbl)
        range_row.addStretch(1)
        range_row.addWidget(max_lbl)
        outer.addLayout(range_row)

        if spec.description:
            # dark-mode-2026q2-e1 rect: QSS role property (was MUTED_TEXT_STYLE inline).
            desc = QLabel(spec.description)
            desc.setProperty("role", "muted")
            desc.setWordWrap(True)
            outer.addWidget(desc)

        self._sliders[spec.name] = slider
        self._value_labels[spec.name] = value_lbl
        return row

    def _on_value_changed(self, spec: ParamSpec) -> None:
        # Live-update the readout, but don't regenerate until release.
        v = self._slider_to_value(spec)
        self._value_labels[spec.name].setText(self._format_value(v, spec))

    def _on_slider_released(self) -> None:
        self.params_changed.emit(self.values())

    def _reset_defaults(self) -> None:
        for spec in self._specs:
            slider = self._sliders[spec.name]
            slider.blockSignals(True)
            slider.setValue(self._value_to_tick(spec.default, spec))
            slider.blockSignals(False)
            self._value_labels[spec.name].setText(self._format_value(spec.default, spec))
        self.params_changed.emit(self.values())

    # ----- value <-> tick conversion (slider stores integer ticks) ----

    @staticmethod
    def _value_to_tick(value: float, spec: ParamSpec) -> int:
        return int(round((value - spec.minimum) / spec.step))

    def _slider_to_value(self, spec: ParamSpec) -> float:
        tick = self._sliders[spec.name].value()
        return spec.minimum + tick * spec.step

    @staticmethod
    def _format_value(value: float, spec: ParamSpec) -> str:
        # Format with enough precision to reflect the step size.
        if spec.step >= 1:
            text = f"{value:.0f}"
        elif spec.step >= 0.1:
            text = f"{value:.2f}"
        else:
            text = f"{value:.3f}"
        return f"{text}{spec.suffix}"
