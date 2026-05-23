# lessons — roadmap-refiner

Accumulates 2-5-bullet lessons per roadmap run.  Appended via heredoc, never overwritten.  Compact only when exceeding 200 lines.

## panel-refresh-2026q2 (2026-05-20)
- **HMW for "translate uplift catalog into roadmap" briefs:** The brief is instruction-shaped — the beneficiary (researcher) and observable outcome (first-impression polish, no flash, no sawtooth) are directly stated in the upstream final-report.md. No HMW fork needed; reframe around the first-wave observable outcomes verbatim from the catalog.
- **Prior-art grep pattern:** For frontend-uplift roadmaps, grep `CONTEXT.md` for the specific panel files (`styles.py`, `appearance_panel.py`, `app.py`) AND grep `CONTEXT.md §9` (things explicitly NOT done) — both surfaces appear in sharpening Q4 and shape the Won't list.
- **MUST vs SHOULD for performance-gated fixes:** When the challenger provides an explicit v0 scope-cut (e.g., UPL-18 MAJOR → "second Taubin pass + bounds padding only"), the MUST assumption is the performance gate ("does the fix stay under 500ms?"), not the fix itself. Tag the spike as [MUST] gating.
- **AI-N-touching assumptions are almost always MUST:** AI-8 (frozen dataclass field addition) and AI-9 (re-entrancy cascade in state-restore) are both MUST-level because getting either wrong silently breaks the registry or produces no-render on restore.
- **First-wave Won't list for uplift roadmaps:** The three most tempting items to include (but must NOT) are: QSettings persistence (CONTEXT.md §9 explicit deferral + MAJOR challenger penalty), new dep landing (superqt/qtawesome — zero-dep-change constraint for first wave), and dark-mode toggle (depends on foundation that first wave only lays).

## realtime-variety-render (2026-05-22)
- **HMW for "translate capability-scout report into roadmap" briefs:** The beneficiary is always the researcher dragging a control, not "the app" or "the pipeline". The observable outcome is the specific interaction change (continuous update during drag, no dropped final position). No HMW fork arises when the brief already contains the DAG — reframe around the first-wave observable outcome from the report's §4 "Recommended next steps".
- **MUST assumption pattern for threading epics:** Any epic touching QThread + VTK on macOS arm64 spawns two MUST assumptions: (1) the pyvistaqt/PySide6 version pin does not introduce a hang, (2) VTK+QThread GC safety on arm64. Both are spike-gated — the downstream architecture arc cannot be entered without them. Tag both [MUST] and make their spike the first entry in the spike lane.
- **MUST assumption for Numba on Apple Silicon:** Treat Numba `parallel=True` arm64 availability as [MUST] even when PyPI wheels are confirmed — the threading layer (workqueue vs TBB) interaction with VTK SMP needs a separate validation. Do not downgrade to [SHOULD] based on wheel availability alone.
- **Won't list for performance roadmaps:** The three most tempting no-gos are parameter-space mesh interpolation (AI-15 prohibition — mathematically fraudulent), GPU isosurfacing (AI-1/AI-3 — rasterized image, not PolyData), and pytest-qt worker tests (AI-2 — macOS segfault). These three appear in the capability-scout tension analysis and should be pre-checked for any latency/interactivity roadmap in this repo.
- **Prior-art grep for performance roadmaps:** Check CONTEXT.md §4.4 (re-entrancy guard), §8.5 (processEvents re-entrancy bug), §9 (explicit not-done list), and synthesis.md §6 (what's already in flight) before writing the prior-art section — these four locations together cover all relevant prior attempts and explicit deferrals.

## CORRECTION 2026-05-23 (restructure-full-audit-2026q2-r1 batch 4)
Panel file locations changed. Lessons referencing grep patterns for `appearance_panel.py`:
- `appearance_panel.py` (root) → `panels/appearance.py`; module `appearance_panel` → `panels.appearance`
- `view_panel.py` (root) → `panels/view.py`; module `view_panel` → `panels.view`
- `parameters_panel.py` (root) → `panels/parameters.py`; module `parameters_panel` → `panels.parameters`
- `parameter_grid_panel.py` (root) → `panels/parameter_grid_panel.py`; module `parameter_grid_panel` → `panels.parameter_grid_panel`
Update any grep patterns: e.g. "grep CONTEXT.md for `appearance_panel.py`" → use `panels/appearance.py`.
Root-level shims remain at old paths. See MOVES.md.
