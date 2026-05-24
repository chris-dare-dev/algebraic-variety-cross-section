"""Tests for the CAND-6 shared debounce utility (e1-s4).

The coalescing *contract* is tested Qt-free via :class:`ui_helpers.DebounceCounter`
(AI-2 — pure-Python, no ``QApplication``).  The real :class:`ui_helpers.Debouncer`
wraps a live ``QTimer`` and is exercised in a separate, clearly-isolated test
that spins a minimal ``QCoreApplication`` (NOT ``QApplication``, NOT
``MainWindow`` — no VTK/GL context, so the macOS Qt+VTK offscreen segfault
that motivates AI-2 cannot occur).  That test ``skip``s cleanly if PySide6 is
unavailable so the Qt-free suite stays green everywhere.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from _qt.ui_helpers import DEBOUNCE_INTERVAL_MS, DebounceCounter


# ---------------------------------------------------------------------------
# Pure Qt-free coalescing contract — DebounceCounter
# ---------------------------------------------------------------------------

def test_ten_rapid_requests_collapse_to_one_callback():
    """The headline CAND-6 property: 10 rapid drag ticks -> 1 deferred fire."""
    c = DebounceCounter()
    for _ in range(10):
        c.request()
    # Still armed, nothing fired yet — the window is open.
    assert c.armed is True
    assert c.fired == 0
    # The drag pauses; the QTimer times out once.
    c.fire()
    assert c.requests == 10
    assert c.fired == 1


def test_first_request_arms_subsequent_absorbed():
    c = DebounceCounter()
    assert c.request() is True       # first request arms the timer
    assert c.request() is False      # absorbed
    assert c.request() is False      # absorbed
    assert c.requests == 3


def test_separate_windows_each_fire_once():
    """Two distinct drag bursts produce two callbacks (one per window)."""
    c = DebounceCounter()
    for _ in range(5):
        c.request()
    c.fire()
    for _ in range(7):
        c.request()
    c.fire()
    assert c.requests == 12
    assert c.fired == 2


def test_fire_when_not_armed_is_noop():
    c = DebounceCounter()
    c.fire()                         # no armed window
    assert c.fired == 0


def test_flush_bypasses_and_cancels_pending_debounce():
    """Release path (flush) fires immediately and disarms — so a trailing
    debounced fire() cannot double-render."""
    c = DebounceCounter()
    for _ in range(4):
        c.request()                  # mid-drag ticks, timer armed
    assert c.armed is True
    c.flush()                        # release: fire now, cancel pending
    assert c.flushed == 1
    assert c.armed is False
    c.fire()                         # the cancelled debounce window no-ops
    assert c.fired == 0              # NOT double-fired


def test_flush_without_pending_still_fires():
    """A release with no preceding drag still fires immediately."""
    c = DebounceCounter()
    c.flush()
    assert c.flushed == 1


def test_default_interval_is_80ms():
    assert DEBOUNCE_INTERVAL_MS == 80


# ---------------------------------------------------------------------------
# Real QTimer Debouncer — isolated, minimal QCoreApplication harness.
#
# This is the ONE test that needs a Qt event loop.  It uses QCoreApplication
# (event loop only — no widgets, no GL, no QtInteractor), so it does not hit
# the macOS Qt+VTK offscreen segfault behind AI-2.  It skips if PySide6 is
# missing so the rest of the suite is unaffected.
# ---------------------------------------------------------------------------

def _qt_available() -> bool:
    try:
        import PySide6  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _qt_available(), reason="PySide6 not installed")
def test_real_debouncer_coalesces_rapid_requests():
    """10 rapid Debouncer.request() calls -> exactly 1 timeout callback."""
    from PySide6.QtCore import QCoreApplication, QTimer, QEventLoop

    app = QCoreApplication.instance() or QCoreApplication([])

    from _qt.ui_helpers import Debouncer

    calls = {"n": 0}
    deb = Debouncer(lambda: calls.__setitem__("n", calls["n"] + 1),
                    interval_ms=30)

    # Fire 10 requests back-to-back in the same event-loop tick.
    for _ in range(10):
        deb.request()

    # Pump the event loop long enough for the single-shot timer to fire.
    loop = QEventLoop()
    QTimer.singleShot(150, loop.quit)
    loop.exec()

    assert calls["n"] == 1, f"expected 1 coalesced callback, got {calls['n']}"


@pytest.mark.skipif(not _qt_available(), reason="PySide6 not installed")
def test_real_debouncer_flush_fires_immediately_and_cancels():
    """flush() fires now; a pending debounced callback does not double-fire."""
    from PySide6.QtCore import QCoreApplication, QTimer, QEventLoop

    app = QCoreApplication.instance() or QCoreApplication([])

    from _qt.ui_helpers import Debouncer

    calls = {"n": 0}
    deb = Debouncer(lambda: calls.__setitem__("n", calls["n"] + 1),
                    interval_ms=30)

    deb.request()        # arm the debounce
    deb.flush()          # release-path: fire now, cancel the armed timer
    assert calls["n"] == 1

    # Let the (cancelled) timer interval elapse — it must NOT fire again.
    loop = QEventLoop()
    QTimer.singleShot(150, loop.quit)
    loop.exec()
    assert calls["n"] == 1, "cancelled debounce must not double-fire"
