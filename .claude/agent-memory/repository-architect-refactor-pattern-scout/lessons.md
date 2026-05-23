
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)
- Tooling drift since last run: Bowler was archived by its owner on 2025-08-08. The GitHub README explicitly redirects to LibCST codemods. Any prior brief citing Bowler as an alternative must be flagged as gate-required and updated. LibCST is now at 1.8.6 (Nov 2025), supports Python 3.0-3.14, MIT licensed. Rope 1.14.0 (Jul 2025) remains actively maintained (Jan 2026 activity). ruff is the de-facto 2026 linter/formatter replacing flake8+isort+black.
- Shim quirk encountered in AVC: AI-9 re-entrancy guard (self._computing) is an implicit shared state across multiple MainWindow methods. Any Extract Class operation that touches the render path must carry this guard or establish equivalent mutual exclusion. The guard is invisible to static analysis — must be tracked manually during moves.
- New 2025-2026 pattern worth tracking: The AGENTS.md open standard is being adopted alongside CLAUDE.md (Hivetrail article; ~60k adopting repos as of 2026). The recommended migration is `mv CLAUDE.md AGENTS.md && ln -s AGENTS.md CLAUDE.md`. For new projects without an existing CLAUDE.md (like AVC today), creating AGENTS.md with a CLAUDE.md symlink is cleaner than the reverse. Do not combine AGENTS.md creation with code restructure in the same commit.
- AVC-specific: The seed brief at scout-c-safe-refactor.md is high-quality and can be used directly as starting cache for future runs on this repo. The per-restructure brief at the BRIEF_PATH incorporates AVC-specific LOC data from the cache directory and the evaluator report. Always pull loc.csv and evaluator-report.md from the cache at the start of a run to ground the brief in actual measurements.
- AVC-specific: AI-2 invariant means no pytest-qt and no Qt event-loop tests. All characterization tests must use pv.OFF_SCREEN = True (AI-3). This is a hard constraint on Section 7 and Section 6.3 of any refactor-pattern brief for AVC.
- AVC-specific: The four panel files (appearance_panel.py, parameter_grid_panel.py, view_panel.py, parameters_panel.py) are the lowest-risk first batch for a panels/ subpackage introduction. The dual-panel question (parameters_panel vs parameter_grid_panel) must be resolved explicitly in PLAN.md before any move commits — do not leave it as a TBD.

## CORRECTION 2026-05-23 (restructure-full-audit-2026q2-r1 batch 4)
Panel file locations changed. The "four panel files at root" have been moved:
- `appearance_panel.py` (root) → `panels/appearance.py`; module `appearance_panel` → `panels.appearance`
- `view_panel.py` (root) → `panels/view.py`; module `view_panel` → `panels.view`
- `parameters_panel.py` (root) → `panels/parameters.py`; module `parameters_panel` → `panels.parameters`
- `parameter_grid_panel.py` (root) → `panels/parameter_grid_panel.py`; module `parameter_grid_panel` → `panels.parameter_grid_panel`
Root-level shims remain at old paths (emit DeprecationWarning; removal milestone M+1). See MOVES.md.
