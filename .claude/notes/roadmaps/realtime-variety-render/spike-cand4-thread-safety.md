# Spike Report: e3 -- macOS Background-Thread Safety
## pyvistaqt #793 + VTK #18782

**Spike:** `realtime-variety-render-e3`
**Date:** 2026-05-22
**Dev machine:** Windows 11 Home 10.0.26200 (x86-64)
**Primary target:** macOS Apple Silicon (arm64)

---

## 1. Verdict

| Assumption | Verdict |
|---|---|
| **[MUST-A]** pyvistaqt #793 does NOT hang on the dev machine's installed PySide6, OR the pin can be tightened to `PySide6 <6.10` without breaking other functionality | **VALIDATED-WITH-CAVEAT** |
| **[MUST-B]** VTK + QThread are safe to use concurrently -- `pv.PolyData` built on a worker thread and handed to the main thread via `Qt.QueuedConnection` signal without a GC crash (VTK #18782) | **VALIDATED-WITH-CAVEAT** |

**Overall: e4 is cleared to proceed, with the listed mitigations applied and the macOS on-device verification checklist completed before shipping.**

### Verdict rationale

**MUST-A:** The installed pyvistaqt is **0.11.4**, which contains the exact fix for #793 (PR #810, merged 2026-04-03). The hang was a macOS-only `QtInteractor` event-loop interaction with PySide6 >= 6.10; the fix is already present in this venv. The `requirements.txt` pin `pyvistaqt>=0.11.4,<0.12` is already tight enough to guarantee the fix. The PySide6 pin does not need tightening. Caveat: the macOS Cocoa behavior cannot be reproduced on Windows; on-device verification of `QtInteractor` startup under PySide6 6.11.x is still required before e4 ships.

**MUST-B:** All three empirical stress variants (sequential GC, rapid cancel-and-resubmit, simultaneous hold-and-drop) passed on Windows in 4.5 s wall clock with no crash, hang, or assertion. The explicit Python ref retention pattern (the VTK #18782 mitigation) was exercised throughout. Caveat: this was run on Windows without a GL context; macOS arm64 with the Cocoa/Metal-GL render path requires on-device verification.

---

## 2. Environment

| Package | Version | Notes |
|---|---|---|
| PySide6 | **6.11.1** | In the #793-affected range (>= 6.10) |
| pyvista | 0.48.4 | |
| vtk | 9.6.2 | |
| pyvistaqt | **0.11.4** | Contains the #793 fix (PR #810) |
| Python | 3.x (Windows 11) | |

**PySide6 6.11.1 is >= 6.10** -- the version range flagged by pyvistaqt issue #793. However, pyvistaqt 0.11.4 contains the fix for that issue. The fix was merged 2026-04-03 in PR #810, and the current `requirements.txt` already pins `pyvistaqt>=0.11.4,<0.12`, ensuring the fix is present.

---

## 3. Issue Research

### 3.1 pyvistaqt issue #793 -- "Not compatible with Qt 6.10+ on macOS"

**URL:** https://github.com/pyvista/pyvistaqt/issues/793

**What is reported:**
Issue opened 2026-02-02. On macOS (Darwin 26.2), pyvistaqt 0.11.3 with PySide6 6.10.x produces a display freeze in interactive mode. The reporter confirmed PySide6 6.9.x worked; the same code with 6.10 hangs. A related pyvista issue (#8285: https://github.com/pyvista/pyvista/issues/8285) reports that `BackgroundPlotter` hangs entirely under PySide6 6.10 on macOS 26.2 + Python 3.14.2 + pyvistaqt 0.11.3 + VTK 9.5.2.

**Affected versions:**
- pyvistaqt: 0.11.3 (and earlier)
- PySide6: >= 6.10.x
- OS: macOS only (confirmed macOS-specific; Linux unaffected)
- Type of hang: Interactive mode freeze / `BackgroundPlotter` hang, specifically on `QtInteractor` event-loop interaction with the macOS Cocoa backend

**Fix:**
PR #810 (https://github.com/pyvista/pyvistaqt/pull/810), merged 2026-04-03, landed in **pyvistaqt 0.11.4**. The fix is a conditional workaround at the `QtInteractor` level that sets a rendering property to `False` only when running on macOS AND Qt version >= 6.10. It is based on VTK merge request https://gitlab.kitware.com/vtk/vtk/-/merge_requests/12956. The initial simpler fix caused tab-switching glitches; the final approach uses a `__doPaintEvent` workaround tested on macOS and Linux.

**Status:** Closed / resolved in pyvistaqt 0.11.4. The current venv (`pyvistaqt==0.11.4`) contains the fix. No backport needed.

**macOS-only?** Yes. The hang is a Cocoa event-loop interaction; Linux and Windows are unaffected.

---

### 3.2 VTK GitLab issue #18782

**URL:** https://gitlab.kitware.com/vtk/vtk/-/issues/18782

**Access status:** The GitLab page returned an "Access Denied" error (error code b3728715388cb593) from the Kitware CDN. The issue content could not be fetched directly. Research is based on secondary sources and the challenge report in `.claude/notes/capability-scouts/realtime-variety-render/artifacts/challenge.md`.

**What is reported (from secondary sources and challenge report):**
The issue describes a crash in the VTK SMP (symmetric-multiprocessing) subsystem triggered by Python garbage collection when `pv.PolyData` objects constructed on a worker thread are released. The mechanism: VTK's internal reference-counting interacts with Python's GC cycle-collector; when a `PolyData` built on a non-main thread is dropped and Python's GC runs, the VTK SMP threading layer can call back into VTK object cleanup from a context that VTK's internal thread-safety model did not anticipate, producing a segfault or assertion failure. The crash is most reliably triggered on macOS arm64 but is a fundamentally Python-GC + VTK refcount issue, not purely platform-specific.

**Mitigation (well-established pattern; confirmed by pyvista discussion #4006):**
The accepted safe pattern from the pyvista community (https://github.com/pyvista/pyvista/discussions/4006) is:
1. Build `pv.PolyData` on the worker thread.
2. Retain an **explicit Python reference** to the output mesh in the worker object (`self._result = mesh`) before emitting the signal.
3. Emit via `Qt.QueuedConnection` so the main-thread slot receives the mesh safely.
4. The worker object (and thus `self._result`) stays alive until after the signal is delivered.
5. All rendering (`add_mesh`, `render`) happens only on the GUI/main thread.

This pattern prevents the GC-triggered crash because the mesh's Python refcount stays above zero throughout the cross-thread handoff. The worker's `self._result` ref is only dropped after the main thread has received and retained the mesh.

**VTK version status:** VTK 9.6.2 (installed) is recent. The issue was reported against earlier VTK versions; no specific "fixed in VTK X.Y.Z" information was found in accessible sources. The mitigation pattern is the operative control regardless of VTK version.

---

### 3.3 State of the art: worker-builds-PolyData / main-thread-renders split

Source: pyvista/pyvista discussion #4006 (https://github.com/pyvista/pyvista/discussions/4006).

The pyvista maintainers confirm the pattern: **data generation (mesh construction, marching cubes, field evaluation) can safely run on background threads; all rendering (VTK GL calls, `add_mesh`, `render`) must run on the GUI/main thread.** The split proposed by e4 (worker builds `pv.PolyData`; main thread calls `add_mesh` + `render`) is precisely the accepted community pattern.

Rendering from a background thread causes OpenGL context conflicts ("wglMakeCurrent failed", shader VAO errors). The e4 design avoids this entirely by keeping all GL operations on the main thread.

---

## 4. Empirical Test Results

**Test script:** `.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py`

**Setup:**
- `QCoreApplication` (no GL context, no `QtInteractor`, no `MainWindow` -- AI-3 compliant)
- `QRunnable` worker calling `kummer_surface(mu_squared=1.3, n=50)` (real generator from `surfaces.py`)
- Signal emission via `Qt.QueuedConnection`
- Explicit `self._result = mesh` retention before emit (VTK #18782 mitigation)
- 120 s wall-clock watchdog (exit code 2 on trigger)

**Variant A -- sequential 30 jobs, `gc.collect()` between each:**
PASS. All 30 meshes valid (`n_points > 0`), no errors, `gc.collect()` survived each cycle.

**Variant B -- rapid cancel-and-resubmit (~30 cycles, 80 ms submit interval):**
PASS. Submitted 30 jobs with 80 ms overlap; received 30 valid meshes; concurrent `PolyData` construction + GC survived.

**Variant C -- hold 10 meshes simultaneously, drop all + `gc.collect()` x2:**
PASS. Held 10 concurrent `PolyData` objects; all valid; `.bounds`, `.n_points`, `.n_faces` accessed on each; drop-all + `gc.collect()` x2 survived.

**Wall clock:** 4.5 s total.

**Windows-not-macOS caveat:** These tests ran on Windows 11 x86-64, with no GL context and no `QtInteractor`. The VTK #18782 GC-crash mechanism is fundamentally a Python refcount / VTK SMP issue (not OpenGL-specific), so the Windows PASS is strong evidence the mitigation pattern is sound. It is not conclusive proof for macOS arm64 with the Cocoa/Metal-GL path active -- that requires on-device verification (see Section 7).

---

## 5. requirements.txt Pin Recommendation

**Recommendation: (a) -- keep `PySide6>=6.6,<7` unchanged.**

Justification:
- The #793 issue is fixed in pyvistaqt 0.11.4, which is already the minimum pinned version (`pyvistaqt>=0.11.4,<0.12`).
- Tightening the PySide6 pin to `<6.10` would be overly conservative and would require users to downgrade PySide6 to obtain a version with fewer features / security updates, with no functional benefit now that the #793 fix is in place.
- The installed PySide6 6.11.1 + pyvistaqt 0.11.4 combination is the resolved state; the fix handles the Cocoa event-loop issue conditionally.

**Note:** This recommendation is proposed, not applied. The e4 implementation epic owns the final `requirements.txt` edit, if any is needed after on-device macOS verification.

---

## 6. VTK #18782 Mitigation

The concrete mitigation the e4 implementation brief must include:

**In the `QRunnable.run()` method of the mesh worker:**
```python
def run(self) -> None:
    mesh = surface.generate(**params)
    self._result = mesh          # REQUIRED: explicit Python ref retention
    self.signals.finished.emit(mesh)
    # self._result keeps refcount > 0 until after the signal is delivered
```

**In the receiving main-thread slot:**
```python
@Slot(object)
def _on_mesh_ready(self, mesh: pv.PolyData) -> None:
    self._current_mesh = mesh    # Main thread retains ref before worker drops theirs
    self._apply_domain_and_render(mesh)
```

**Rule:** The worker must retain `self._result` until the `QRunnable` object itself is released (i.e., until the `QThreadPool` has finished with it and no Python code holds the worker reference). In practice, keeping `self._result` as an instance attribute satisfies this requirement because `QThreadPool` holds the worker alive until `run()` returns, and the signal delivery is guaranteed to have happened before the next Python GC cycle can reach the mesh.

**Additional requirement for rapid supersede (cancel-and-resubmit) path:**
When a new job supersedes an in-flight job, the main thread must not release its reference to the previous mesh until the new mesh signal has been received and stored. The `_computing` guard and `_pending_render` flag (e1's queue-latest semantics) must be extended to cover the worker-in-flight state.

---

## 7. Residual macOS Verification

The following checklist must be completed on actual macOS Apple Silicon hardware (arm64) before e4 ships:

1. **pyvistaqt #793 fix confirmation:** Launch `QtInteractor` under PySide6 6.10+ (any 6.10.x or 6.11.x) on macOS and confirm no hang or freeze occurs on `BackgroundPlotter` instantiation, tab switching, and window resizing. Specifically test pyvistaqt 0.11.4 + PySide6 6.11.x on macOS arm64.

2. **Worker + `QtInteractor` coexistence:** Run the spike test script on macOS (replacing `QCoreApplication` with `QApplication`, or running as-is) to confirm the `QRunnable` + `QueuedConnection` + `pv.PolyData` pattern produces no GC crash with the Cocoa event loop active.

3. **Full `add_mesh` + `render` path:** Add a `plotter.add_mesh(mesh)` + `plotter.render()` call in the main-thread slot (using `pv.OFF_SCREEN = True`) to confirm the VTK GL state is clean when a worker-produced mesh is added to a `QtInteractor`-backed plotter on macOS.

4. **Rapid supersede stress under Cocoa:** Run Variant B (30 rapid cancel-and-resubmit cycles) on macOS with a `QApplication` and a visible (or offscreen) `QtInteractor` to stress the combined pyvistaqt + VTK SMP path.

5. **VTK SMP threading layer on arm64:** Confirm that VTK 9.6.x on macOS arm64 uses the `STDThread` SMP backend (not TBB) and that the `kummer_surface` marching-cubes path does not trigger VTK's own internal threading in a way that conflicts with the Python GIL. Check `vtk.vtkSMPTools.GetBackend()` on the macOS machine.

6. **PySide6 event-loop drain under load:** Confirm that `processEvents()` calls inside the worker-in-flight guard do not re-enter the worker dispatch (AI-9 invariant) under macOS's Cocoa run-loop semantics, which differ from Windows's message pump.

---

## 8. Recommendation for e4

**Proceed with listed mitigations.**

The spike evidence supports moving forward with e4 (background-thread worker + coarse-preview LOD) under the following conditions:

1. **Apply VTK #18782 mitigation** (Section 6) in the worker implementation: `self._result = mesh` before emit, main-thread slot retains ref immediately.

2. **Do not tighten the PySide6 pin** -- pyvistaqt 0.11.4 already contains the #793 fix; `PySide6>=6.6,<7` is safe.

3. **Complete the macOS on-device verification checklist** (Section 7) as the first task within e4, before writing production worker code. The checklist is a 1-day exercise on actual Apple Silicon hardware; it gates the GL-path confidence.

4. **Keep all VTK GL operations on the GUI thread**: `add_mesh`, `render`, `plotter.*` calls must never be called from the `QRunnable.run()` method.

5. **Document the worker lifecycle gap** in CONTEXT.md §9: AI-2 prohibits pytest-qt worker-lifecycle tests; the on-device manual verification checklist is the substitute acceptance gate.

The empirical result (3/3 stress variants PASS, 4.5 s, no crash) combined with the research finding that pyvistaqt 0.11.4 resolves #793, gives sufficient confidence to proceed. The residual macOS verification is bounded (1 day) and is a prerequisite gate, not a blocker to starting e4 implementation work on Windows.
