
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)
- Tooling drift since last run: Bowler was archived by its owner on 2025-08-08. The GitHub README explicitly redirects to LibCST codemods. Any prior brief citing Bowler as an alternative must be flagged as gate-required and updated. LibCST is now at 1.8.6 (Nov 2025), supports Python 3.0-3.14, MIT licensed. Rope 1.14.0 (Jul 2025) remains actively maintained (Jan 2026 activity). ruff is the de-facto 2026 linter/formatter replacing flake8+isort+black.
- Shim quirk encountered in AVC: AI-9 re-entrancy guard (self._computing) is an implicit shared state across multiple MainWindow methods. Any Extract Class operation that touches the render path must carry this guard or establish equivalent mutual exclusion. The guard is invisible to static analysis — must be tracked manually during moves.
- New 2025-2026 pattern worth tracking: The AGENTS.md open standard is being adopted alongside CLAUDE.md (Hivetrail article; ~60k adopting repos as of 2026). The recommended migration is `mv CLAUDE.md AGENTS.md && ln -s AGENTS.md CLAUDE.md`. For new projects without an existing CLAUDE.md (like AVC today), creating AGENTS.md with a CLAUDE.md symlink is cleaner than the reverse. Do not combine AGENTS.md creation with code restructure in the same commit.
- AVC-specific: The seed brief at scout-c-safe-refactor.md is high-quality and can be used directly as starting cache for future runs on this repo. The per-restructure brief at the BRIEF_PATH incorporates AVC-specific LOC data from the cache directory and the evaluator report. Always pull loc.csv and evaluator-report.md from the cache at the start of a run to ground the brief in actual measurements.
- AVC-specific: AI-2 invariant means no pytest-qt and no Qt event-loop tests. All characterization tests must use pv.OFF_SCREEN = True (AI-3). This is a hard constraint on Section 7 and Section 6.3 of any refactor-pattern brief for AVC.
- AVC-specific: The four panel files (appearance_panel.py, parameter_grid_panel.py, view_panel.py, parameters_panel.py) are the lowest-risk first batch for a panels/ subpackage introduction. The dual-panel question (parameters_panel vs parameter_grid_panel) must be resolved explicitly in PLAN.md before any move commits — do not leave it as a TBD.

## Lesson from restructure-feature-subpackages-2026q2-r2 (2026-05-23)
- Tooling drift since last run: No new tooling changes vs r1. Bowler remains archived (Aug 2025). LibCST 1.8.6 confirmed at Python 3.14 + free-threaded. napari uses _qt/ for private Qt implementation (private Qt code in napari/_qt; public Qt interface in napari/qt) — confirmed by search as the canonical real-world precedent for the _qt/ subpackage pattern.
- Shim quirk encountered in AVC: Recursive shim chains are a r2-specific trap. When panels/ renames to _qt/panels/, the 4 existing r1 shims (appearance_panel.py etc.) which forward to panels.appearance etc. silently break — they must be updated in the SAME commit as `git mv panels/ _qt/panels/`. Option A (direct-target update) is the only correct approach; Option B (two-hop chain via panels/__init__.py hub) produces double-warning noise and should be rejected.
- Shim quirk 2: The surfaces.py hub shim MUST explicitly enumerate all 11 _*_field_kernel private names in _PRIVATE_NAMES (not in the normal _PUBLIC_NAMES dict, but still in the __getattr__ dispatch table). Star-import shims (`from varieties._kernels import *`) would silently skip _-prefixed names, breaking test_numba_field_kernels.py. This is a load-bearing distinction.
- New 2025-2026 pattern worth tracking: "splitting by domain family" is a specialization of Split Module where cohesion criterion is mathematical domain (bounded context per DDD terminology). For surfaces.py's 1811 LOC, the correct first step is to extract shared infrastructure (_kernels.py, _marching.py) BEFORE splitting the family modules — this avoids cross-family import cycles at the split boundary.
- validate-shims.py gap persists: module-kind entries use `import <mod>` which cannot trigger __getattr__. This gap was documented in r1 and confirmed as a persistent design issue. Per-symbol (named) shim validation still works correctly. The preferred remedy is test_shims.py tests with catch_warnings pattern.
- AVC-specific: The numba.config.THREADING_LAYER = "workqueue" process-global side effect is currently in surfaces.py at import time. When surfaces.py becomes a shim, this assignment must be preserved in varieties/_kernels.py (at the TOP, before any @njit decorator). Omitting it causes VTK/Numba SMP contention (CONTEXT.md §3). This is invisible to static analysis — must be tracked manually.

## CORRECTION 2026-05-23 (restructure-full-audit-2026q2-r1 batch 4)
Panel file locations changed. The "four panel files at root" have been moved:
- `appearance_panel.py` (root) → `panels/appearance.py`; module `appearance_panel` → `panels.appearance`
- `view_panel.py` (root) → `panels/view.py`; module `view_panel` → `panels.view`
- `parameters_panel.py` (root) → `panels/parameters.py`; module `parameters_panel` → `panels.parameters`
- `parameter_grid_panel.py` (root) → `panels/parameter_grid_panel.py`; module `parameter_grid_panel` → `panels.parameter_grid_panel`
Root-level shims remain at old paths (emit DeprecationWarning; removal milestone M+1). See MOVES.md.

## CORRECTION 2026-05-23 (restructure-feature-subpackages-2026q2-r2 batch 1)
The 4 root-level r1 panel shim files have been deleted (M+1 cycle closed):
- `appearance_panel.py` (root shim) → DELETED.
- `view_panel.py` (root shim) → DELETED.
- `parameters_panel.py` (root shim) → DELETED.
- `parameter_grid_panel.py` (root shim) → DELETED.
Lesson correction for Batch 3 implementers: "Recursive shim chains are a r2-specific trap — the 4 r1 shims must be updated in the SAME commit as `git mv panels/ _qt/panels/`" is OBSOLETE. The 4 r1 shims are already deleted before Batch 3 begins. Batch 3 DOES NOT need to update them. The trap no longer exists.
Prior CORRECTION block statement "Root-level shims remain at old paths (emit DeprecationWarning; removal milestone M+1)" is now false.
Tag: `refactor-r2-batch1-end` at 16b251b.

## Lesson from restructure-single-root-2026q2-r3 (2026-05-24)
- Tooling drift since last run: No new tooling changes. LibCST 1.8.6 confirmed. Bowler remains archived (Aug 2025). import-linter 2.x stable. RenameCommand in LibCST main branch confirmed to use QualifiedNameProvider + ScopeProvider as METADATA_DEPENDENCIES — the correct pattern for attribute-chain rewrites.
- Shim quirk encountered in AVC: The leave_Attribute partial-rewrite bug is confirmed as the key LibCST pitfall for r3 B1. The fix is: use QualifiedNameProvider.has_name() instead of string-matching node.value.value. Multi-alias leave_ImportFrom must NOT rewrite the module path in-place — use AddImportsVisitor + RemoveImportsVisitor per alias instead.
- AVC-specific (hub retirement): The numba.config.THREADING_LAYER="workqueue" side effect must be confirmed in varieties/_kernels.py BEFORE surfaces.py is deleted in B4. This is the single highest-risk invisible side effect of the hub retirement.
- AVC-specific (import-linter): pyproject.toml is the correct config file for import-linter in AVC (already has pyproject.toml; avoid setup.cfg proliferation). Contracts should be added AFTER B4 surfaces.py deletion as regression guardrails, not before.
- AVC-specific (Protocol): @runtime_checkable Protocol introduction is safe for existing Surface dataclasses because they use plain fields (no @property). CPython issue #102433 (isinstance side effects with @property) does NOT apply. Recommend skipping runtime isinstance checks entirely — use Protocol for type-checker narrowing only.
- New 2025-2026 pattern worth tracking: The subprocess-isolated import smoke test (subprocess.run([sys.executable, "-c", f"import {module}"])) is the canonical pattern for detecting cyclic imports that pytest conftest.py pollution can hide. Add as tests/test_import_smoke.py in B4 for Qt-free modules only (AI-2 constraint).
