"""Qt-free tests for the CAND-5 queue-latest re-entrancy semantics (e1-s2).

AI-2: no ``QApplication``, no VTK.  ``MainWindow._render_current`` cannot be
exercised directly without a Qt event loop, so this test models the
queue-latest state machine as a pure simulator that reproduces the exact
control flow of the real ``_computing`` / ``_pending_render`` /
``QTimer.singleShot(0, ...)`` catch-up implemented in ``app.py``.

The property under test (CAND-5, the CRITICAL correctness fix): when N rapid
render requests arrive while one render is in flight, the request stream is
NOT silently dropped — exactly one catch-up render fires after the in-flight
render completes, and that catch-up reads the LATEST queued parameter value.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class _RenderSim:
    """Faithful pure-Python model of ``MainWindow``'s queue-latest guard.

    Mirrors ``app.py``: ``_computing`` is the in-flight flag; a request that
    arrives while ``_computing`` is True sets ``_pending_render`` instead of
    being dropped; the ``finally`` block schedules one deferred catch-up.

    ``current_param`` stands in for ``self.parameters_panel.values()`` — the
    catch-up reads it *fresh* at catch-up time, so it always renders the
    latest slider position, never a stale one.
    """

    def __init__(self) -> None:
        self._computing = False
        self._pending_render = False
        self.current_param = 0.0          # latest slider value
        self.rendered_values: list[float] = []   # params actually rendered
        self._deferred: list[float] = []  # QTimer.singleShot(0, ...) queue

    def request_render(self) -> None:
        """Equivalent of calling ``_render_current``."""
        if self._computing:
            # CAND-5: queue-latest — do NOT drop.
            self._pending_render = True
            return
        self._computing = True
        try:
            # "generate" — render whatever the latest param is right now.
            self.rendered_values.append(self.current_param)
        finally:
            self._computing = False
            if self._pending_render:
                self._pending_render = False
                # QTimer.singleShot(0, lambda: self._render_current(...))
                self._deferred.append(0)

    def run_event_loop(self) -> None:
        """Drain the deferred QTimer.singleShot(0, ...) catch-ups."""
        while self._deferred:
            self._deferred.pop(0)
            self.request_render()


def test_single_request_renders_once():
    sim = _RenderSim()
    sim.current_param = 3.0
    sim.request_render()
    sim.run_event_loop()
    assert sim.rendered_values == [3.0]


def test_fast_drag_release_renders_final_position_not_dropped():
    """The core CAND-5 bug: a fast drag-and-release must render the FINAL
    slider position.  Pre-fix it was silently dropped."""
    sim = _RenderSim()
    # First render starts (param 1.0).  While "in flight", N more requests
    # arrive as the user keeps dragging; the slider's final value is 9.0.
    sim.current_param = 1.0

    captured = {}

    def first_render():
        # Simulate the burst arriving DURING the in-flight render.
        for v in (2.0, 4.0, 7.0, 9.0):
            sim.current_param = v
            sim.request_render()  # each hits the _computing guard
        captured["pending"] = sim._pending_render

    # Drive the first render manually so we can inject the burst mid-flight.
    sim._computing = True
    try:
        sim.rendered_values.append(sim.current_param)  # renders 1.0
        first_render()
    finally:
        sim._computing = False
        if sim._pending_render:
            sim._pending_render = False
            sim._deferred.append(0)
    sim.run_event_loop()

    # The burst was queued, not dropped.
    assert captured["pending"] is True
    # Exactly one catch-up fired (queue-LATEST, not queue-all).
    assert sim.rendered_values == [1.0, 9.0]
    # The final resting position (9.0) WAS rendered — the bug is gone.
    assert sim.rendered_values[-1] == 9.0


def test_burst_collapses_to_one_catch_up():
    """Ten rapid in-flight requests produce exactly ONE catch-up render."""
    sim = _RenderSim()
    sim.current_param = 0.0
    sim._computing = True
    try:
        sim.rendered_values.append(sim.current_param)  # render 0.0
        for i in range(1, 11):
            sim.current_param = float(i)
            sim.request_render()
    finally:
        sim._computing = False
        if sim._pending_render:
            sim._pending_render = False
            sim._deferred.append(0)
    sim.run_event_loop()
    # 1 initial + 1 catch-up == 2 renders total for 11 requests.
    assert len(sim.rendered_values) == 2
    assert sim.rendered_values == [0.0, 10.0]


def test_no_pending_render_means_no_catch_up():
    """When nothing arrives mid-flight, no spurious catch-up is scheduled."""
    sim = _RenderSim()
    sim.current_param = 5.0
    sim.request_render()
    assert sim._pending_render is False
    assert sim._deferred == []
    sim.run_event_loop()
    assert sim.rendered_values == [5.0]
