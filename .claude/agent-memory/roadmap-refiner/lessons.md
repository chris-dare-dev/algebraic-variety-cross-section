# lessons — roadmap-refiner

Accumulates 2-5-bullet lessons per roadmap run.  Appended via heredoc, never overwritten.  Compact only when exceeding 200 lines.

## panel-refresh-2026q2 (2026-05-20)
- **HMW for "translate uplift catalog into roadmap" briefs:** The brief is instruction-shaped — the beneficiary (researcher) and observable outcome (first-impression polish, no flash, no sawtooth) are directly stated in the upstream final-report.md. No HMW fork needed; reframe around the first-wave observable outcomes verbatim from the catalog.
- **Prior-art grep pattern:** For frontend-uplift roadmaps, grep `CONTEXT.md` for the specific panel files (`styles.py`, `appearance_panel.py`, `app.py`) AND grep `CONTEXT.md §9` (things explicitly NOT done) — both surfaces appear in sharpening Q4 and shape the Won't list.
- **MUST vs SHOULD for performance-gated fixes:** When the challenger provides an explicit v0 scope-cut (e.g., UPL-18 MAJOR → "second Taubin pass + bounds padding only"), the MUST assumption is the performance gate ("does the fix stay under 500ms?"), not the fix itself. Tag the spike as [MUST] gating.
- **AI-N-touching assumptions are almost always MUST:** AI-8 (frozen dataclass field addition) and AI-9 (re-entrancy cascade in state-restore) are both MUST-level because getting either wrong silently breaks the registry or produces no-render on restore.
- **First-wave Won't list for uplift roadmaps:** The three most tempting items to include (but must NOT) are: QSettings persistence (CONTEXT.md §9 explicit deferral + MAJOR challenger penalty), new dep landing (superqt/qtawesome — zero-dep-change constraint for first wave), and dark-mode toggle (depends on foundation that first wave only lays).
