"""Background-thread mesh worker for the realtime render pipeline.

realtime-variety-render-e4 (CAND-4): moves ``surface.generate()`` off the Qt
GUI thread onto a ``QThreadPool`` worker so the parameter sliders and the grid
stay responsive during the ~0.5-1.5 s implicit-surface compute. Before this
epic the GUI thread blocked inside ``surface.generate()`` and a
``QApplication.processEvents()`` workaround was needed to keep the status bar
repainting; that workaround (and its AI-9 re-entrancy hazard) is now gone.

Threading contract — validated by the e3 spike
(``.claude/notes/roadmaps/realtime-variety-render/spike-cand4-thread-safety.md``):

  * ``surface.generate()`` is pure NumPy + VTK *data* construction (field
    sampling, Flying Edges isocontouring, Taubin smoothing). It touches no
    OpenGL and no shared Qt state, so it is safe to run on a worker thread.
  * ALL VTK GL operations (``plotter.add_mesh`` / ``render`` / ``reset_camera``)
    stay on the GUI thread — ``MainWindow`` performs those in the result slot,
    never here.
  * VTK GitLab #18782: a ``pv.PolyData`` built on a worker thread must keep a
    live Python reference across the cross-thread hand-off, or Python's cyclic
    GC can crash VTK's SMP layer. ``MeshWorker.run`` retains ``self._result``;
    the ``MainWindow`` slot retains the mesh as its very first statement.

This module is import-safe without a running ``QApplication`` — it only
*defines* the worker classes. ``is_stale_result`` and ``MeshResult`` are pure
Python and are exercised by the Qt-free test suite (AI-2); the live
``QThreadPool`` dispatch and ``QueuedConnection`` delivery cannot be tested
without ``pytest-qt`` (see CONTEXT.md §9).
"""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass
from typing import Callable

import pyvista as pv
from PySide6.QtCore import QObject, QRunnable, Signal


def is_stale_result(result_generation: int, current_generation: int) -> bool:
    """Return ``True`` when a worker result belongs to a superseded job.

    The render dispatch tags every job with a monotonically increasing
    *generation* id. A result whose generation id is not the current one was
    superseded by a later request and must be discarded by the result slot
    rather than rendered — rendering it would flash an out-of-date surface
    after the user has already moved on.

    Extracted as a Qt-free free function (mirroring ``clipped_cache_is_valid``
    in ``app.py`` and ``should_render_on_drag`` in ``surfaces.py``) so the
    supersede-discard rule has a unit test under the AI-2 Qt-free suite.

    Note: while the ``MainWindow._computing`` single-flight guard holds, at
    most one worker is ever in flight and the slot's generation always matches
    the current one — so this check is *defensive* idempotency insurance, not
    a hot path. If a future change lifts the single-flight guard (e.g. to
    dispatch a worker per drag tick), this function becomes load-bearing and
    the cursor/`_computing` ownership in the slot must be revisited.
    """
    return result_generation != current_generation


@dataclass
class MeshResult:
    """Payload handed from the worker thread back to the GUI thread.

    Carries everything the result slot needs so the GUI thread never has to
    reach back into worker-thread state. Exactly one of ``mesh`` /
    ``error_message`` is meaningful, selected by ``ok``.

    Fields:
      generation        — the job's generation id (see :func:`is_stale_result`).
      ok                — ``True`` if ``surface.generate()`` succeeded.
      mesh              — the generated ``pv.PolyData`` (``None`` when not ok).
      gen_ms            — measured ``surface.generate()`` wall time, ms
                          (CAND-12 telemetry).
      warning_text      — first ``RuntimeWarning`` text raised during generate
                          (e.g. the Dwork conifold warning at ψ≈1); ``""`` if
                          none. Captured on BOTH the success and failure
                          paths — a generator may warn and then raise.
      error_message     — ``str(exc)`` when not ok; ``""`` otherwise. Note
                          this can be ``""`` even on a real failure (e.g. a
                          bare ``MemoryError``) — the slot falls back to
                          ``error_type`` so the status bar is never blank.
      error_type        — ``type(exc).__name__`` when not ok; ``""`` otherwise.
      error_is_value_error — ``True`` when the failure was a ``ValueError``
                          (AI-14 "no real zero set" / parameter-range case),
                          ``False`` for any other exception. Lets the slot
                          reproduce the original status-bar message prefixes.
                          (``_on_mesh_ready`` additionally substring-matches
                          ``error_message`` for ``"No real zero set"`` — see
                          that slot for the worker↔slot text contract.)
      is_coarse         — ``True`` when this result is a coarse-preview LOD
                          render (realtime-variety-render-e4b / CAND-3): the
                          worker was dispatched with ``params["n"] =
                          surface.coarse_n``. The slot uses this flag to
                          switch the status-bar message to the AI-15
                          ``"Preview  ·  {label}{hq_label}  ·  NNN ms"`` badge
                          (with ``{hq_label}`` interpolated as ``" [HQ]"``
                          when applicable, and an optional ``"⚠ {warning}  |  "``
                          prefix for RuntimeWarning surfaces such as the
                          Dwork conifold) and skip the verts/faces/bbox
                          readout — those numbers would be misleadingly
                          precise on a transient low-resolution mesh. The
                          worker stays mode-agnostic — it carries the tag
                          verbatim from ``MeshWorker.__init__``. The
                          authoritative badge contract lives in CONTEXT.md
                          §8.19; this docstring mirrors it.
    """

    generation: int
    ok: bool
    mesh: pv.PolyData | None = None
    gen_ms: float = 0.0
    warning_text: str = ""
    error_message: str = ""
    error_type: str = ""
    error_is_value_error: bool = False
    is_coarse: bool = False


class WorkerSignals(QObject):
    """Signal carrier for :class:`MeshWorker`.

    A ``QRunnable`` is not a ``QObject`` and cannot emit signals itself, so the
    worker owns a ``QObject`` carrier. ``finished`` carries a :class:`MeshResult`
    (both the success and failure cases — the slot branches on ``result.ok``).
    """

    finished = Signal(object)  # carries a MeshResult


class MeshWorker(QRunnable):
    """Runs ``surface.generate()`` off the GUI thread; emits a :class:`MeshResult`.

    The worker performs the *entire* former synchronous render-compute body:
    the ``warnings.catch_warnings`` capture, the ``perf_counter`` timing
    bracket (CAND-12), and the ``ValueError`` / ``Exception`` capture. An
    exception raised on the worker thread cannot be caught by a main-thread
    ``try``/``except`` — so every failure mode is captured here and shipped
    back inside the ``MeshResult`` instead of propagating.
    """

    def __init__(
        self,
        generate: Callable[..., pv.PolyData],
        params: dict[str, float],
        generation: int,
        is_coarse: bool = False,
    ) -> None:
        super().__init__()
        self._generate = generate
        self._params = params
        self._generation = generation
        # realtime-variety-render-e4b (CAND-3): the coarse-vs-full mode tag.
        # The worker is mode-agnostic — it does NOT lower `n` itself; the
        # dispatcher (`app.py:_render_current`) injects `params["n"] =
        # surface.coarse_n` before constructing the worker.  This flag just
        # round-trips back to the slot inside `MeshResult.is_coarse` so the
        # AI-15 Preview-badge state machine can branch on it.
        self._is_coarse = is_coarse
        self.signals = WorkerSignals()
        # VTK #18782: an explicit Python ref to the output mesh, retained from
        # just before the signal is emitted until this worker object itself is
        # released. MainWindow holds the worker alive (`_active_worker`) until
        # its slot has retained the mesh into `_raw_mesh`.
        self._result: pv.PolyData | None = None

    def run(self) -> None:  # noqa: D102 — QRunnable override
        result = self._compute()
        # VTK #18782 mitigation: retain the mesh ref BEFORE emitting, so its
        # Python refcount stays > 0 across the cross-thread hand-off.
        self._result = result.mesh
        self.signals.finished.emit(result)

    def _compute(self) -> MeshResult:
        """Run the generator and package the outcome as a :class:`MeshResult`.

        The ``warnings.catch_warnings`` block wraps the ``try``/``except`` so
        the ``caught`` list is scanned on EVERY path — a generator can emit a
        ``RuntimeWarning`` and then raise (e.g. a future generator that warns
        about a degeneracy and then finds the field empty). Scanning only the
        success path, as the pre-e4 synchronous code did, would silently drop
        that warning.
        """
        gen = self._generation
        t0 = time.perf_counter()
        mesh: pv.PolyData | None = None
        error_message = ""
        error_type = ""
        error_is_value_error = False
        # catch_warnings is not thread-shared — it MUST wrap the generate()
        # call here, on the worker thread.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                mesh = self._generate(**self._params)
            except ValueError as exc:
                error_message, error_type = str(exc), type(exc).__name__
                error_is_value_error = True
            except Exception as exc:  # noqa: BLE001 — surfaced to the status bar
                error_message, error_type = str(exc), type(exc).__name__
        gen_ms = (time.perf_counter() - t0) * 1000.0
        # Scan for a RuntimeWarning regardless of success/failure (e.g. the
        # Dwork conifold warning at ψ≈1) so the slot can surface it.
        warning_text = ""
        for w in caught:
            if issubclass(w.category, RuntimeWarning):
                warning_text = str(w.message)
                break
        if mesh is None and error_type:
            return MeshResult(
                generation=gen, ok=False,
                gen_ms=gen_ms, warning_text=warning_text,
                error_message=error_message, error_type=error_type,
                error_is_value_error=error_is_value_error,
                is_coarse=self._is_coarse,
            )
        return MeshResult(
            generation=gen, ok=True, mesh=mesh,
            gen_ms=gen_ms, warning_text=warning_text,
            is_coarse=self._is_coarse,
        )
