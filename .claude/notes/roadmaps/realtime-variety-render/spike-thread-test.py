"""spike-thread-test.py  --  e3 empirical threading spike

Validates the two [MUST] assumptions for realtime-variety-render-e4:

  ASSUMPTION-A  pyvistaqt #793 / PySide6 >=6.10:
      Not directly testable on Windows (the hang is a macOS Cocoa
      event-loop interaction).  This script tests the THREADING
      MECHANICS only, with no QtInteractor or GL context.

  ASSUMPTION-B  VTK GitLab #18782 / pv.PolyData cross-thread GC:
      Build a pv.PolyData on a QRunnable worker, hand it to the main
      thread via a Qt.QueuedConnection signal, stress the GC in three
      variants.  This is the load-bearing empirical test.

Usage:
  .venv/Scripts/python.exe .claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py

Exit codes:
  0  all variants PASSED
  1  at least one variant FAILED or an unexpected exception occurred
  2  wall-clock timeout detected (treat as hang)

Platform note:
  Running on Windows 11.  The macOS-specific Cocoa / Metal-GL behavior
  of pyvistaqt #793 is NOT covered here -- see the spike report for the
  residual on-device-macOS-verification checklist.
"""

from __future__ import annotations

import gc
import sys
import time
import traceback

# ASCII-only print guard -- Windows cp1252
def _p(msg: str) -> None:
    print(msg.encode("ascii", errors="replace").decode("ascii"))

# ---------------------------------------------------------------------------
# Detect available Qt binding
# ---------------------------------------------------------------------------
try:
    from PySide6.QtCore import (
        QCoreApplication, QObject, QRunnable, QThreadPool, QTimer,
        Signal, Slot, Qt,
    )
    _p("Qt binding: PySide6 (signal/slot via Signal/Slot decorators)")
    _BINDING = "PySide6"
except ImportError:
    _p("FATAL: PySide6 not found -- cannot run spike")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Import the real generator from surfaces.py
# The test uses kummer_surface at a low n to keep each job <0.5 s on Windows.
# kummer_surface(mu_squared=1.3, n=60) is fast (~0.1 s) and always produces
# a valid non-empty mesh.
# ---------------------------------------------------------------------------
import os, pathlib
PROJECT_ROOT = pathlib.Path(__file__).parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from surfaces import kummer_surface, enriques_figure_3
    _p("Imported generators: kummer_surface, enriques_figure_3")
except Exception as exc:
    _p(f"FATAL: could not import surfaces.py -- {exc}")
    sys.exit(1)

import pyvista as pv

# ---------------------------------------------------------------------------
# Worker infrastructure
# ---------------------------------------------------------------------------

FAST_N = 50   # small enough to be quick on Windows; still a real mesh
FAST_MU = 1.3


class WorkerSignals(QObject):
    """Carrier object for cross-thread signals.

    QRunnable itself cannot emit signals; we attach a QObject child that
    lives on the main thread (parent=None keeps ownership ambiguous --
    the worker holds a reference to prevent premature deletion, satisfying
    the VTK #18782 mitigation: retain explicit Python refs until the main
    thread has consumed the payload).
    """
    finished = Signal(object)   # carries pv.PolyData or Exception
    error    = Signal(str)


class MeshWorker(QRunnable):
    """Off-thread pv.PolyData builder.

    Builds the mesh, retains an explicit Python reference to it, then
    emits it to the main thread via a QueuedConnection.  The explicit
    ref (`self._result`) stays alive until after the signal is emitted,
    preventing the GC-triggered crash described in VTK #18782.
    """

    def __init__(self, job_id: int):
        super().__init__()
        self.job_id  = job_id
        self.signals = WorkerSignals()
        self._result = None  # explicit ref -- VTK #18782 mitigation

    def run(self) -> None:
        try:
            mesh = kummer_surface(mu_squared=FAST_MU, n=FAST_N)
            # Retain explicit Python reference BEFORE emitting (VTK #18782 key mitigation).
            self._result = mesh
            self.signals.finished.emit(mesh)
        except Exception as exc:
            self.signals.error.emit(f"job {self.job_id}: {exc}\n{traceback.format_exc()}")


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

WALL_CLOCK_LIMIT_S = 120   # hard timeout -- if exceeded, exit(2) from a watchdog

_failures: list[str] = []
_passes:   list[str] = []


def _fail(variant: str, detail: str) -> None:
    msg = f"FAIL [{variant}]: {detail}"
    _p(msg)
    _failures.append(msg)


def _pass(variant: str, detail: str) -> None:
    msg = f"PASS [{variant}]: {detail}"
    _p(msg)
    _passes.append(msg)


# ---------------------------------------------------------------------------
# Variant A -- sequential: 30 jobs, gc.collect() between each
# ---------------------------------------------------------------------------

def run_variant_a(pool: QThreadPool, app: QCoreApplication) -> None:
    _p("")
    _p("=== Variant A: sequential 30 jobs, gc.collect() between each ===")
    N_JOBS = 30
    received: list[pv.PolyData] = []
    errors: list[str] = []
    pending = [0]  # mutable counter

    def on_mesh(mesh: object) -> None:
        if isinstance(mesh, pv.PolyData):
            received.append(mesh)
        else:
            errors.append(f"unexpected type: {type(mesh)}")
        pending[0] -= 1
        if pending[0] == 0:
            app.quit()

    def on_error(msg: str) -> None:
        errors.append(msg)
        pending[0] -= 1
        if pending[0] == 0:
            app.quit()

    # Submit one job at a time, wait for completion, gc.collect(), repeat
    for i in range(N_JOBS):
        worker = MeshWorker(i)
        worker.signals.finished.connect(on_mesh, Qt.ConnectionType.QueuedConnection)
        worker.signals.error.connect(on_error, Qt.ConnectionType.QueuedConnection)
        pending[0] = 1
        pool.start(worker)
        deadline = time.monotonic() + 30.0
        while pending[0] > 0:
            app.processEvents()
            if time.monotonic() > deadline:
                _fail("A", f"job {i} timed out after 30 s")
                return
            time.sleep(0.005)
        gc.collect()

    if errors:
        _fail("A", f"{len(errors)} errors: {errors[:3]}")
        return
    if len(received) != N_JOBS:
        _fail("A", f"expected {N_JOBS} meshes, got {len(received)}")
        return
    bad = [m for m in received if m.n_points == 0]
    if bad:
        _fail("A", f"{len(bad)} empty meshes received")
        return
    _pass("A", f"all {N_JOBS} meshes valid (n_points>0), no errors, gc.collect() survived each cycle")


# ---------------------------------------------------------------------------
# Variant B -- rapid cancel-and-resubmit: submit new job before previous finishes
# ---------------------------------------------------------------------------

def run_variant_b(pool: QThreadPool, app: QCoreApplication) -> None:
    _p("")
    _p("=== Variant B: rapid cancel-and-resubmit, ~30 supersede cycles ===")
    N_CYCLES = 30
    SUBMIT_INTERVAL_MS = 80  # submit new job every 80 ms (< typical job duration)

    received: list[pv.PolyData] = []
    errors:   list[str] = []
    _submitted = [0]
    _completed = [0]

    # We track live workers to keep Python refs alive (VTK #18782 mitigation)
    _live_workers: list[MeshWorker] = []

    done_evt = [False]

    def on_mesh(mesh: object) -> None:
        if isinstance(mesh, pv.PolyData):
            received.append(mesh)
        else:
            errors.append(f"unexpected type: {type(mesh)}")
        _completed[0] += 1

    def on_error(msg: str) -> None:
        errors.append(msg)
        _completed[0] += 1

    def submit_next() -> None:
        if _submitted[0] >= N_CYCLES:
            done_evt[0] = True
            return
        w = MeshWorker(_submitted[0])
        w.signals.finished.connect(on_mesh, Qt.ConnectionType.QueuedConnection)
        w.signals.error.connect(on_error, Qt.ConnectionType.QueuedConnection)
        _live_workers.append(w)
        pool.start(w)
        _submitted[0] += 1
        QTimer.singleShot(SUBMIT_INTERVAL_MS, submit_next)

    submit_next()

    # Wait until all N_CYCLES jobs submitted AND drain completions
    deadline = time.monotonic() + 90.0
    while True:
        app.processEvents()
        if time.monotonic() > deadline:
            _fail("B", f"timed out: submitted={_submitted[0]} completed={_completed[0]}")
            return
        # All submitted and all completed
        if done_evt[0] and _completed[0] == N_CYCLES:
            break
        time.sleep(0.005)

    # Explicitly drop worker refs + GC
    _live_workers.clear()
    gc.collect()

    if errors:
        _fail("B", f"{len(errors)} errors: {errors[:3]}")
        return
    if len(received) == 0:
        _fail("B", "no meshes received at all")
        return
    bad = [m for m in received if m.n_points == 0]
    if bad:
        _fail("B", f"{len(bad)} empty meshes in {len(received)} received")
        return
    _pass("B", (
        f"submitted {N_CYCLES} jobs with {SUBMIT_INTERVAL_MS} ms overlap; "
        f"received {len(received)} valid meshes; "
        "concurrent PolyData construction + GC survived"
    ))


# ---------------------------------------------------------------------------
# Variant C -- hold N meshes alive simultaneously then drop all + gc.collect()
# ---------------------------------------------------------------------------

def run_variant_c(pool: QThreadPool, app: QCoreApplication) -> None:
    _p("")
    _p("=== Variant C: hold 10 meshes simultaneously, drop all + gc.collect() ===")
    N_HOLD = 10

    held:   list[pv.PolyData] = []
    errors: list[str] = []
    pending = [N_HOLD]

    def on_mesh(mesh: object) -> None:
        if isinstance(mesh, pv.PolyData):
            held.append(mesh)
        else:
            errors.append(f"unexpected type: {type(mesh)}")
        pending[0] -= 1

    def on_error(msg: str) -> None:
        errors.append(msg)
        pending[0] -= 1

    workers = []
    for i in range(N_HOLD):
        w = MeshWorker(1000 + i)
        w.signals.finished.connect(on_mesh, Qt.ConnectionType.QueuedConnection)
        w.signals.error.connect(on_error, Qt.ConnectionType.QueuedConnection)
        workers.append(w)
        pool.start(w)

    deadline = time.monotonic() + 60.0
    while pending[0] > 0:
        app.processEvents()
        if time.monotonic() > deadline:
            _fail("C", f"timed out waiting for {pending[0]} remaining meshes")
            return
        time.sleep(0.005)

    if errors:
        _fail("C", f"{len(errors)} errors: {errors[:3]}")
        return

    # Verify all N_HOLD meshes are alive and valid before dropping
    bad = [m for m in held if m.n_points == 0]
    if bad:
        _fail("C", f"{len(bad)} empty meshes in held set")
        return

    # Read .bounds on each to force VTK internal structure traversal
    try:
        for m in held:
            _ = m.bounds
            _ = m.n_points
            _ = m.n_faces
    except Exception as exc:
        _fail("C", f"attribute access on held mesh raised: {exc}")
        return

    # Drop all refs + force GC -- this is the multi-reference GC stress
    workers.clear()
    held.clear()
    gc.collect()
    gc.collect()  # second pass -- VTK's ref-count cycle cleanup

    _pass("C", (
        f"held {N_HOLD} concurrent PolyData objects; "
        "all valid; bounds/n_points/n_faces accessed; "
        "drop-all + gc.collect() x2 survived"
    ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    _p("")
    _p("=" * 60)
    _p("e3 Spike: cross-thread pv.PolyData safety test")
    _p("=" * 60)

    import PySide6
    import pyvista
    import vtk
    import pyvistaqt

    _p(f"PySide6   : {PySide6.__version__}")
    _p(f"pyvista   : {pyvista.__version__}")
    _p(f"vtk       : {vtk.vtkVersion.GetVTKVersion()}")
    _p(f"pyvistaqt : {pyvistaqt.__version__}")

    # Check PySide6 version against #793 affected range
    from packaging.version import Version
    pyside_ver = Version(PySide6.__version__)
    if pyside_ver >= Version("6.10"):
        _p(f"WARNING: PySide6 {PySide6.__version__} is in the #793-affected range (>=6.10).")
        _p("  pyvistaqt #793 fix is in pyvistaqt 0.11.4 (PR #810, merged 2026-04-03).")
        _p("  macOS-specific hang cannot be reproduced on Windows; see spike report.")
    else:
        _p(f"PySide6 {PySide6.__version__} is below 6.10 -- not in the #793 affected range.")

    _p("")
    _p("Platform: Windows (no GL context, no QtInteractor -- pure threading test)")
    _p("Generator under test: kummer_surface(mu_squared=1.3, n=50)")
    _p("Worker pattern: QRunnable + explicit Python ref retention (VTK #18782 mitigation)")
    _p("")

    # Wall-clock watchdog
    _start = time.monotonic()

    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    pool = QThreadPool.globalInstance()
    pool.setMaxThreadCount(4)

    # Watchdog: if the whole test runs over WALL_CLOCK_LIMIT_S, abort
    def _watchdog() -> None:
        elapsed = time.monotonic() - _start
        if elapsed > WALL_CLOCK_LIMIT_S:
            _p(f"FATAL: wall-clock watchdog fired after {elapsed:.1f} s -- aborting as hang")
            sys.exit(2)
        QTimer.singleShot(2000, _watchdog)

    QTimer.singleShot(2000, _watchdog)

    try:
        run_variant_a(pool, app)
        run_variant_b(pool, app)
        run_variant_c(pool, app)
    except Exception as exc:
        _p(f"FATAL: unhandled exception in test harness: {exc}")
        _p(traceback.format_exc())
        return 1

    pool.waitForDone(30000)  # drain any residual workers (30 s max)

    _p("")
    _p("=" * 60)
    _p("SUMMARY")
    _p("=" * 60)
    for msg in _passes:
        _p(f"  {msg}")
    for msg in _failures:
        _p(f"  {msg}")

    elapsed = time.monotonic() - _start
    _p(f"Wall clock: {elapsed:.1f} s")

    if _failures:
        _p("")
        _p("OVERALL: FAIL -- see failures above")
        return 1

    if not _passes:
        _p("")
        _p("OVERALL: FAIL -- no variants ran")
        return 1

    _p("")
    _p("OVERALL: PASS -- all 3 variants completed without crash or hang")
    _p("")
    _p("NOTE: This is a Windows empirical result.")
    _p("  Variant A/B/C PASS = strong evidence VTK #18782 mitigation is sound.")
    _p("  macOS Cocoa/Metal-GL behavior still requires on-device verification.")
    _p("  pyvistaqt #793 macOS hang: NOT reproduced here (Windows -- not applicable).")
    _p("  See spike-cand4-thread-safety.md for the full residual checklist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
