"""Tests for the realtime-variety-render-e4 background-thread worker module.

Qt-free (AI-2): these exercise only the pure-Python pieces of
``render_worker`` — the :func:`is_stale_result` supersede predicate and the
:class:`MeshResult` payload dataclass. Importing ``render_worker`` imports
``PySide6.QtCore`` (to *define* the worker classes) but constructs no
``QApplication``, no event loop, and no ``QtInteractor`` — so it does not
trip the macOS Qt+VTK offscreen segfault that AI-2 guards against.

What is deliberately NOT covered here (and cannot be, under AI-2): the live
``QThreadPool`` dispatch, the ``QueuedConnection`` signal delivery, the
worker-in-flight cancel-and-resubmit timing, and ``closeEvent`` teardown.
Those need a running ``QApplication`` + ``pytest-qt``. The e3 spike script
``.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py`` is the
manual regression harness for the live path — see CONTEXT.md §9.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from render_worker import MeshResult, is_stale_result


# ---------------------------------------------------------------------------
# is_stale_result — the supersede-discard predicate
# ---------------------------------------------------------------------------

def test_is_stale_result_same_generation_is_fresh():
    """A result whose generation matches the current job is NOT stale."""
    assert is_stale_result(5, 5) is False


def test_is_stale_result_older_generation_is_stale():
    """A result from an earlier (superseded) job IS stale."""
    assert is_stale_result(3, 7) is True


def test_is_stale_result_newer_generation_is_stale():
    """A mismatch in either direction is stale — the predicate is pure
    inequality, not an ordering check (defensive against any id skew)."""
    assert is_stale_result(9, 4) is True


def test_is_stale_result_zero_initial_generation():
    """Generation ids start at 0; the first dispatched job is generation 1.
    A 0-vs-0 comparison (no job yet dispatched) is treated as fresh."""
    assert is_stale_result(0, 0) is False


# ---------------------------------------------------------------------------
# MeshResult — the worker→GUI payload dataclass
# ---------------------------------------------------------------------------

def test_mesh_result_success_defaults():
    """A success payload carries the mesh and leaves the error fields empty."""
    sentinel = object()  # stand-in for a pv.PolyData — dataclass is type-blind
    r = MeshResult(generation=2, ok=True, mesh=sentinel, gen_ms=123.4)
    assert r.ok is True
    assert r.mesh is sentinel
    assert r.gen_ms == pytest.approx(123.4)
    assert r.warning_text == ""
    assert r.error_message == ""
    assert r.error_is_value_error is False


def test_mesh_result_value_error_payload():
    """A ValueError failure flags `error_is_value_error` so the result slot
    can reproduce the 'No real zero set' / 'Parameter out of range' prefixes."""
    r = MeshResult(
        generation=4, ok=False,
        error_message="No real zero set in the sampling box",
        error_is_value_error=True,
    )
    assert r.ok is False
    assert r.mesh is None
    assert r.error_is_value_error is True
    assert "No real zero set" in r.error_message


def test_mesh_result_generic_error_payload():
    """A non-ValueError failure leaves `error_is_value_error` False so the
    slot routes it to the generic 'Error: ...' branch."""
    r = MeshResult(
        generation=6, ok=False,
        error_message="something unexpected",
        error_is_value_error=False,
    )
    assert r.ok is False
    assert r.error_is_value_error is False


def test_mesh_result_carries_warning_text():
    """The Dwork conifold RuntimeWarning is captured on the worker thread and
    shipped in the payload (a main-thread catch_warnings cannot see it)."""
    r = MeshResult(
        generation=8, ok=True, mesh=object(), gen_ms=10.0,
        warning_text="conifold singularity at psi approximately 1",
    )
    assert "conifold" in r.warning_text
