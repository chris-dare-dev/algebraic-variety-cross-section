# Evaluator checklist (scout-B's 28 items)

Mechanically run by `scripts/repository-architect/evaluate-checklist.py` against the current AVC tree in Phase 1 step 2. Each item is binary (PASS/FAIL) with a one-line evidence string.

The checklist is the OPERATIONAL deliverable from scout-B's brief — designed to be runnable against AVC or any peer project.  The **TSP-N column** maps each item to the Tree-Structure Principle it feeds (TSP-1..TSP-11 are defined verbatim in `.claude/commands/repository-architect.md`).  A FAIL on an item with a TSP-N mapping is also a TSP-N FAIL — these flow into the TSP pre-state scorecard at `audit/tsp-scorecard-pre.md`.

**TSP-11 (entry-point pseudocode)** has no item in this 28-item checklist — it requires AST-level analysis of each root entry-point file (function-call density, business-logic pattern detection) that the static 28-item list can't express.  The auditor agent and the execution-critic compute TSP-11 directly against `app.py` (and any other root entry point) and write the result into the TSP scorecard.

## Top-level files (1-10)

| # | Item | TSP-N | Source |
|---|---|---|---|
| 1 | README.md present at root | — | CONSENSUS — all sources |
| 2 | LICENSE present at root | — | CONSENSUS |
| 3 | CHANGELOG.md present at root (Keep-a-Changelog style) | — | pyOpenSci |
| 4 | CODE_OF_CONDUCT.md present at root | — | pyOpenSci (optional for solo) |
| 5 | CONTRIBUTING.md present at root | — | pyOpenSci (scales with team) |
| 6 | pyproject.toml present at root | — | PyPA, universal 2026 |
| 7 | AGENTS.md present at root | — | agents.md spec, 60k+ adopting repos |
| 8 | CLAUDE.md present at root (or symlinked to AGENTS.md) | — | HumanLayer, deployhq |
| 9 | No setup.py unless stated reason | — | CONSENSUS |
| 10 | Top-level file count under 20 (and ≤2 logic `.py` files) | TSP-1 | OPINION — modern trend; tightened for TSP-1 |

## Package layout (11-17)

| # | Item | TSP-N | Source |
|---|---|---|---|
| 11 | Importable code under a named package (src/<pkg>/ or <pkg>/) | TSP-6 | PyPA, pyOpenSci |
| 12 | No TSP-5 banlist names anywhere (canonical list: `anti-patterns.md` R19; mechanical check: `check-banlist.sh`) | TSP-5 | Lehtinen "Dunghill", Hitchhiker's Guide |
| 13 | No directory more than 3 levels deep under package root (AVC's tree shape allows 3) | TSP-2, TSP-10 | Software Carpentry |
| 14 | Module names lowercase with underscores, no hyphens | TSP-5 | Software Carpentry, Hitchhiker's Guide |
| 15 | Subpackages reflect domain/role, not architectural layer | TSP-5 | Sahibinden Tech, Kraken EuroPython |
| 16 | No `from foo import *` anywhere in the package | — | Hitchhiker's Guide, quantifiedcode |
| 17 | No file in the package over ~800 LOC (>500 LOC is a TSP-4 early warning; >800 LOC is the alarm; oversize files must carry a TSP-7 annotation with a named follow-up restructure-id — open-ended retentions FAIL) | TSP-4, TSP-7 | CONTESTED but converging |

## Tests / docs / examples (18-20)

| # | Item | TSP-N | Source |
|---|---|---|---|
| 18 | tests/ directory exists as sibling of the package | TSP-9 | pyOpenSci |
| 19 | docs/ directory exists at root | — | pyOpenSci, Scientific Python |
| 20 | examples/ directory exists (for projects with UI/visible output) | — | PyVista, napari |

## AI-friendliness (21-25)

| # | Item | TSP-N | Source |
|---|---|---|---|
| 21 | AGENTS.md (or CLAUDE.md) under 300 lines | — | HumanLayer |
| 22 | CLAUDE.md doesn't contain lint rules a linter could enforce | — | HumanLayer |
| 23 | No directory named temp/tmp/misc/stuff/old/backup in VC | TSP-5 | OPINION — common-sense |
| 24 | Framework-adapter code lives in named subpackages (_qt/, _vispy/, _pyvista/) | TSP-5 | napari precedent |
| 25 | .gitignore covers __pycache__/, .pytest_cache/, *.pyc, build, IDE | — | CONSENSUS |

## Bonus diagnostics (26-28)

| # | Item | TSP-N | Source |
|---|---|---|---|
| 26 | Import-graph has no cycles | TSP-3 | Kraken, scipy |
| 27 | `python -c "import setup"` fails (or no setup.py) | — | ionelmc, PyPA |
| 28 | Every top-level subpackage has a one-paragraph docstring in `__init__.py` | TSP-5 | SPEC-ish, pandas, scipy |

## Downstream consumption

Two consumers read this checklist's output:

- **PLAN.md design phase:** item FAILs matching the user's restructure brief → PLAN.md §1 goals; out-of-brief FAILs → PLAN.md appendix only (do NOT pull into scope unless the user asks).
- **TSP scorecards:** items with a TSP-N mapping aggregate into `audit/tsp-scorecard-pre.md` (auditor, Phase 1) and `rectify/tsp-scorecard-post.md` (execution-critic, Phase 5).  A TSP-N principle is graded PASS only if ALL items mapped to it PASS; one FAIL drops the whole principle to FAIL.  The auditor and critic additionally compute TSP-11 directly via AST (methodology: `.claude/references/repository-architect/tsp-11-computation.md`), since no static-list item captures pseudocode-density.  Phase 5 final summary reports `<pass>/11 principles satisfied`.

## Honest acknowledgements

Per scout-B §8, some items are CONTESTED:
- src vs flat for apps (item 11 accepts either).
- Tests inside vs outside the package (item 18 accepts either with stated reason).
- File-size hard limit (item 17 is informal practice, not a hard rule).
- CLAUDE.md line cap (item 21 is empirical).

The script's FAIL on a CONTESTED item is INFORMATIONAL — the designer decides whether to act.

## See also

- `scripts/repository-architect/evaluate-checklist.py` — runs the checklist.
- `verification-rubric.md` — the 20-item POST-execution rubric (different scope).
