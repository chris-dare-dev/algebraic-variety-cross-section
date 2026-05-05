"""ParametersPanel — dynamic slider panel driven by a Surface's ParamSpec list.

Repopulated each time the user picks a different surface. Emits ``params_changed``
when a slider is released, carrying the current parameter dict. The signal fires
on release rather than continuously to avoid thrashing the marching-cubes call.
"""

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

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

        self._title = QLabel("Parameters")
        self._title.setStyleSheet("font-weight: bold; font-size: 13px;")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._root.addWidget(self._title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        self._root.addWidget(sep)

        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(8)
        self._root.addLayout(self._content_layout)

        self._empty_label = QLabel("(no parameters)")
        self._empty_label.setStyleSheet("color: #888;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(self._empty_label)

        self._reset_btn = QPushButton("Reset to defaults")
        self._reset_btn.clicked.connect(self._reset_defaults)
        self._reset_btn.setEnabled(False)
        self._root.addWidget(self._reset_btn)

        self._root.addStretch(1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        name_lbl = QLabel(spec.label)
        name_lbl.setStyleSheet("font-size: 11px;")
        header.addWidget(name_lbl)
        header.addStretch(1)
        value_lbl = QLabel(self._format_value(spec.default, spec))
        value_lbl.setStyleSheet("font-family: monospace; font-size: 11px; color: #444;")
        header.addWidget(value_lbl)
        outer.addLayout(header)

        slider = QSlider(Qt.Orientation.Horizontal)
        ticks = max(1, int(round((spec.maximum - spec.minimum) / spec.step)))
        slider.setRange(0, ticks)
        slider.setValue(self._value_to_tick(spec.default, spec))
        slider.valueChanged.connect(lambda _v, s=spec: self._on_value_changed(s))
        slider.sliderReleased.connect(self._on_slider_released)
        outer.addWidget(slider)

        if spec.description:
            desc = QLabel(spec.description)
            desc.setStyleSheet("color: #888; font-size: 10px;")
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
