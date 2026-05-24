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

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

import _qt.parameter_grid_math as pg
from _qt.styles import SMALL_LABEL_STYLE
from surfaces import ParamSpec

# realtime-variety-render-e1-s4 (CAND-6): default debounce interval, ms.
# The roadmap specifies 80 ms; the INVEST note allows 50-150 ms if tuning
# proves necessary.  One named constant so both panels share it.
DEBOUNCE_INTERVAL_MS = 80


class DebounceCounter:
    """Pure (Qt-free) model of the debounce coalescing contract.

    The :class:`Debouncer` below wraps a real ``QTimer``; this class captures
    *only* the counting semantics so they can be unit-tested without a
    ``QApplication`` (AI-2 — the test suite is Qt-free).

    Contract: every ``request()`` while the timer is "armed" is absorbed —
    it does not schedule an additional deferred callback.  Exactly one
    deferred callback ``fire()`` is produced per armed window, regardless of
    how many ``request()`` calls landed in it.  ``flush()`` models the
    release-path bypass: it fires immediately and disarms, so the pending
    debounced callback (if any) is cancelled rather than double-firing.

    Invariant verified by tests: N rapid ``request()`` calls followed by one
    ``fire()`` yield exactly 1 callback (``fired == 1``), and ``requests``
    counts all N.
    """

    def __init__(self) -> None:
        self.requests = 0   # total request() calls seen
        self.fired = 0      # total deferred callbacks emitted
        self.flushed = 0    # total immediate (release-path) fires
        self._armed = False

    def request(self) -> bool:
        """Record a debounced request.

        Returns ``True`` if this request *armed* the timer (i.e. it is the
        first of a new window and a real ``QTimer`` should be (re)started),
        ``False`` if it was absorbed into an already-armed window.
        """
        self.requests += 1
        if self._armed:
            return False
        self._armed = True
        return True

    def fire(self) -> None:
        """Model the QTimer timeout — emit exactly one deferred callback."""
        if not self._armed:
            return
        self._armed = False
        self.fired += 1

    def flush(self) -> None:
        """Model the release-path bypass — fire immediately, disarm.

        Any armed debounced window is cancelled (its ``fire()`` will no-op),
        so the release render is not duplicated by a trailing debounced one.
        """
        self._armed = False
        self.flushed += 1

    @property
    def armed(self) -> bool:
        return self._armed


class Debouncer(QObject):
    """Shared ``QTimer``-based debounce for slider / grid-dot drag ticks.

    realtime-variety-render-e1-s4 (CAND-6).  A single instance is wired into
    both :class:`parameters_panel.ParametersPanel` and
    :class:`parameter_grid_panel.ParameterGridPanel` so the drag-time
    coalescing discipline lives in exactly one place.

    Usage::

        deb = Debouncer(on_timeout=self._do_debounced_render)
        # ... on a drag tick (valueChanged / drag-move):
        deb.request()          # coalesces — at most 1 callback per interval
        # ... on release (sliderReleased / dot-release):
        deb.flush()            # bypass — fires immediately, cancels pending

    AI-9 (re-entrancy): the timer is single-shot.  ``request()`` (re)starts
    it; intermediate ``request()`` calls inside the armed window only restart
    the same timer — at most one ``timeout`` is delivered per window.  The
    callback runs on the Qt event loop, never inside ``processEvents`` and
    never inside ``_render_current``'s ``_computing`` window — so it composes
    with the ``_computing`` guard and the s2 ``QTimer.singleShot(0, ...)``
    catch-up without re-entrancy.  ``flush()`` stops the timer first, so the
    release path can never be shadowed by a trailing debounced callback.

    **e1 scope (dormant):** the debounce machinery is shipped and wired into
    the panels' signal plumbing, but the panels do NOT connect ``request()``
    to a render on ``valueChanged`` — render-on-drag is gated to e2
    (``typical_ms`` speed routing) / e4 (coarse-LOD).  The release path
    (``sliderReleased`` → ``params_changed``) is unchanged and fully working.
    """

    def __init__(
        self,
        on_timeout: Callable[[], None],
        *,
        interval_ms: int = DEBOUNCE_INTERVAL_MS,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_timeout = on_timeout
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._handle_timeout)

    def request(self) -> None:
        """Schedule a debounced callback.

        Restarts the single-shot timer; rapid successive calls collapse to a
        single ``on_timeout`` invocation once the drag pauses for the
        interval.
        """
        self._timer.start()

    def flush(self) -> None:
        """Release-path bypass — cancel any pending debounce and fire now."""
        self._timer.stop()
        self._on_timeout()

    def cancel(self) -> None:
        """Drop any pending debounced callback without firing."""
        self._timer.stop()

    def is_active(self) -> bool:
        """Whether a debounced callback is currently pending."""
        return self._timer.isActive()

    def _handle_timeout(self) -> None:
        self._on_timeout()


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
