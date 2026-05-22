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
import warnings

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from render_worker import MeshResult, MeshWorker, is_stale_result


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


# ---------------------------------------------------------------------------
# MeshWorker._compute — the off-thread compute body
#
# These call `_compute()` directly (NOT `run()`, which emits a Qt signal).
# `_compute` is pure Python — it runs the supplied generator, captures
# warnings, and packages a MeshResult. Constructing a MeshWorker creates a
# WorkerSignals QObject, which is allowed without a QApplication (QObjects,
# unlike QWidgets, do not require one). No event loop, no GL — AI-2 safe.
# ---------------------------------------------------------------------------

def _compute(generate, params=None):
    """Run MeshWorker._compute with a stand-in generator."""
    return MeshWorker(generate, params or {}, generation=1)._compute()


def test_compute_success_returns_mesh():
    """A generator that returns a mesh yields ok=True with gen_ms timed."""
    sentinel = object()  # _compute does not inspect the mesh object
    r = _compute(lambda: sentinel)
    assert r.ok is True
    assert r.mesh is sentinel
    assert r.gen_ms >= 0.0
    assert r.error_message == "" and r.error_type == ""


def test_compute_captures_warning_on_success():
    """A RuntimeWarning emitted during a successful generate is captured."""
    def gen():
        warnings.warn("conifold-ish degeneracy", RuntimeWarning)
        return object()
    r = _compute(gen)
    assert r.ok is True
    assert "conifold-ish degeneracy" in r.warning_text


def test_compute_captures_warning_emitted_before_raise():
    """Regression guard for realtime-variety-render-e4 adversary HIGH-2:
    a generator that emits a RuntimeWarning and THEN raises must still have
    its warning captured — the catch_warnings scan runs on every path, not
    just the success fall-through."""
    def gen():
        warnings.warn("degeneracy detected", RuntimeWarning)
        raise ValueError("No real zero set in the sampling box")
    r = _compute(gen)
    assert r.ok is False
    assert r.error_is_value_error is True
    assert "degeneracy detected" in r.warning_text, (
        "a warning emitted before the raise must not be dropped"
    )


def test_compute_value_error_payload():
    """A ValueError flags error_is_value_error and records the type name."""
    def gen():
        raise ValueError("mu² must be > 1/3")
    r = _compute(gen)
    assert r.ok is False and r.mesh is None
    assert r.error_is_value_error is True
    assert r.error_type == "ValueError"
    assert "mu²" in r.error_message


def test_compute_generic_exception_not_flagged_value_error():
    """A non-ValueError failure leaves error_is_value_error False."""
    def gen():
        raise RuntimeError("unexpected")
    r = _compute(gen)
    assert r.ok is False
    assert r.error_is_value_error is False
    assert r.error_type == "RuntimeError"


def test_compute_captures_error_type_on_empty_message():
    """Regression guard for the empty-message status-bar finding: an
    exception whose str() is empty must still yield a nameable error_type so
    the slot can render 'Error: <Type>' instead of a content-free 'Error:'."""
    def gen():
        raise MemoryError()  # str(MemoryError()) == ""
    r = _compute(gen)
    assert r.ok is False
    assert r.error_message == ""
    assert r.error_type == "MemoryError"
