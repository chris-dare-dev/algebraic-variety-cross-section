"""ui_helpers — shared Qt widget builders for the Parameters dock.

Factored out so :class:`parameters_panel.ParametersPanel` (the slider stack)
and :class:`parameter_grid_panel.ParameterGridPanel` (residual sliders shown
alongside the grid) build *identical* label+slider+range rows from one place.
Before this factory the two panels each had a near-verbatim ``_build_row`` /
``_build_residual_row``, so any layout change had to be made twice.

The two-phase render discipline (INT-NO-1: live numeric readout on
``valueChanged``, mesh re-render only on ``sliderReleased``) is preserved —
the factory wires caller-supplied callbacks for each phase.

Theme discipline: colour-bearing labels use the QSS ``role`` property
(``muted`` / ``value-mono`` / ``range-label``) so the active theme's
stylesheet (``APP_STYLESHEET`` / ``APP_STYLESHEET_DARK``) cascades the colour.
Only the font-size-only ``SMALL_LABEL_STYLE`` is applied inline, because it
carries no colour and is therefore theme-safe.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

import parameter_grid as pg
from styles import SMALL_LABEL_STYLE
from surfaces import ParamSpec


def build_slider_row(
    spec: ParamSpec,
    current: float,
    *,
    on_value_changed: Callable[[ParamSpec], None],
    on_released: Callable[[], None],
    include_description: bool = True,
) -> tuple[QWidget, QSlider, QLabel]:
    """Build one parameter row: header (name + value), slider, range labels.

    Parameters
    ----------
    spec:
        The :class:`~surfaces.ParamSpec` this row controls.
    current:
        The value the slider should start at (``spec.default`` for a fresh
        panel, or the live value when rebuilding mid-session).
    on_value_changed:
        Called with *spec* on every ``slider.valueChanged``.  The caller must
        only live-update its numeric readout here and MUST NOT trigger a mesh
        re-render — that is the INT-NO-1 two-phase discipline.
    on_released:
        Called with no arguments on ``slider.sliderReleased``.  The caller
        emits its params-changed signal here; this is the single render
        trigger.
    include_description:
        Whether to append the spec's ``description`` as a wrapped muted
        label.  The slider stack passes ``True``; the grid panel's residual
        rows pass ``False`` to stay compact beside the grid.

    Returns
    -------
    (row_widget, slider, value_label)
        The caller registers *slider* and *value_label* into its own lookup
        dicts (keyed by ``spec.name``) so it can sync them later.

    Notes
    -----
    The slider's tick range and the initial tick come from
    :func:`parameter_grid.tick_count` / :func:`parameter_grid.value_to_tick`,
    both of which guard a degenerate ``step <= 0`` — so a ``ParamSpec`` built
    with ``step=0`` produces a single-tick slider instead of a
    ``ZeroDivisionError``.
    """
    row = QWidget()
    outer = QVBoxLayout(row)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(2)

    # Header: parameter name on the left, current value on the right.
    header = QHBoxLayout()
    header.setContentsMargins(0, 0, 0, 0)
    name_lbl = QLabel(spec.label)
    name_lbl.setStyleSheet(SMALL_LABEL_STYLE)  # font-only — theme-safe
    name_lbl.setToolTip(spec.description or spec.label)
    header.addWidget(name_lbl)
    header.addStretch(1)
    value_lbl = QLabel(pg.format_value(current, spec))
    value_lbl.setProperty("role", "value-mono")  # theme-driven colour
    value_lbl.setToolTip("Current value")
    header.addWidget(value_lbl)
    outer.addLayout(header)

    # Slider — stores integer ticks; tick k == spec.minimum + k * spec.step.
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, pg.tick_count(spec))
    slider.setValue(pg.value_to_tick(current, spec))
    slider.setToolTip(
        f"{spec.label}\n"
        f"Range: {spec.minimum:g} - {spec.maximum:g}  |  Step: {spec.step:g}"
    )
    slider.valueChanged.connect(lambda _v, s=spec: on_value_changed(s))
    slider.sliderReleased.connect(on_released)
    outer.addWidget(slider)

    # Min / max range labels flanking below the slider.
    range_row = QHBoxLayout()
    range_row.setContentsMargins(0, 0, 0, 0)
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

    if include_description and spec.description:
        desc = QLabel(spec.description)
        desc.setProperty("role", "muted")
        desc.setWordWrap(True)
        outer.addWidget(desc)

    return row, slider, value_lbl
