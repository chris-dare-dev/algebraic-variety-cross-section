# Evaluator checklist (scout-B's 28 items)

Mechanically run by `scripts/repository-architect/evaluate-checklist.py` against the current AVC tree in Phase 1 step 2. Each item is binary (PASS/FAIL) with a one-line evidence string.

The checklist is the OPERATIONAL deliverable from scout-B's brief — designed to be runnable against AVC or any peer project.

## Top-level files (1-10)

| # | Item | Source |
|---|---|---|
| 1 | README.md present at root | CONSENSUS — all sources |
| 2 | LICENSE present at root | CONSENSUS |
| 3 | CHANGELOG.md present at root (Keep-a-Changelog style) | pyOpenSci |
| 4 | CODE_OF_CONDUCT.md present at root | pyOpenSci (optional for solo) |
| 5 | CONTRIBUTING.md present at root | pyOpenSci (scales with team) |
| 6 | pyproject.toml present at root | PyPA, universal 2026 |
| 7 | AGENTS.md present at root | agents.md spec, 60k+ adopting repos |
| 8 | CLAUDE.md present at root (or symlinked to AGENTS.md) | HumanLayer, deployhq |
| 9 | No setup.py unless stated reason | CONSENSUS |
| 10 | Top-level file count under 20 | OPINION — modern trend |

## Package layout (11-17)

| # | Item | Source |
|---|---|---|
| 11 | Importable code under a named package (src/<pkg>/ or <pkg>/) | PyPA, pyOpenSci |
| 12 | No utils.py file over 200 LOC (utils/ package OK) | Lehtinen "Dunghill", Hitchhiker's Guide |
| 13 | No directory more than 2 levels deep under package root | Software Carpentry |
| 14 | Module names lowercase with underscores, no hyphens | Software Carpentry, Hitchhiker's Guide |
| 15 | Subpackages reflect domain/role, not architectural layer | Sahibinden Tech, Kraken EuroPython |
| 16 | No `from foo import *` anywhere in the package | Hitchhiker's Guide, quantifiedcode |
| 17 | No file in the package over ~800 LOC | CONTESTED but converging |

## Tests / docs / examples (18-20)

| # | Item | Source |
|---|---|---|
| 18 | tests/ directory exists as sibling of the package | pyOpenSci |
| 19 | docs/ directory exists at root | pyOpenSci, Scientific Python |
| 20 | examples/ directory exists (for projects with UI/visible output) | PyVista, napari |

## AI-friendliness (21-25)

| # | Item | Source |
|---|---|---|
| 21 | AGENTS.md (or CLAUDE.md) under 300 lines | HumanLayer |
| 22 | CLAUDE.md doesn't contain lint rules a linter could enforce | HumanLayer |
| 23 | No directory named temp/tmp/misc/stuff/old/backup in VC | OPINION — common-sense |
| 24 | Framework-adapter code lives in named subpackages (_qt/, _vispy/, _pyvista/) | napari precedent |
| 25 | .gitignore covers __pycache__/, .pytest_cache/, *.pyc, build, IDE | CONSENSUS |

## Bonus diagnostics (26-28)

| # | Item | Source |
|---|---|---|
| 26 | Import-graph has no cycles | Kraken, scipy |
| 27 | `python -c "import setup"` fails (or no setup.py) | ionelmc, PyPA |
| 28 | Every top-level subpackage has a one-paragraph docstring in `__init__.py` | SPEC-ish, pandas, scipy |

## How items affect PLAN.md

A FAIL on item N is NOT automatically a restructure goal — many fails are out of scope for a given restructure (e.g. item 19 docs/ isn't worth a restructure unless the user asked for it). The PLAN.md design phase uses the checklist as input:

- Item FAILs that match the user's brief -> include as restructure goals (PLAN.md §1).
- Item FAILs OUTSIDE the user's brief -> note in PLAN.md's appendix but do NOT pull into scope.

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
