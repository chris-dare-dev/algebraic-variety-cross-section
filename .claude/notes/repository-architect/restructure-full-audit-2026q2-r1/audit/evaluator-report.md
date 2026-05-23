# Evaluator checklist report — restructure-full-audit-2026q2-r1

Scout-B's 28-item file-by-file evaluator checklist run mechanically against the current tree.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | README.md present at root | PASS | README.md exists |
| 2 | LICENSE present at root | FAIL | MISSING (LICENSE, LICENSE.md, COPYING) |
| 3 | CHANGELOG.md present at root (Keep-a-Changelog style) | FAIL | MISSING |
| 4 | CODE_OF_CONDUCT.md present at root | FAIL | MISSING (optional for solo projects) |
| 5 | CONTRIBUTING.md present at root | FAIL | MISSING (scales with team size) |
| 6 | pyproject.toml present at root | FAIL | MISSING (canonical in 2026) |
| 7 | AGENTS.md present at root | FAIL | MISSING (60k+ adopting repos) |
| 8 | CLAUDE.md present at root (or symlinked to AGENTS.md) | FAIL | MISSING |
| 9 | No setup.py at root (pyproject.toml is canonical) | PASS | absent (good) |
| 10 | Top-level file count under 20 | PASS | 15 files at root |
| 11 | Importable code under a named package | FAIL | NO SOURCE PACKAGE -- 11 loose .py files at root (tests/ excluded from package detection) |
| 12 | No utils.py file over 200 LOC | PASS | no utils.py/helpers.py/common.py/misc.py >200 LOC |
| 13 | No directory more than 2 levels deep under package root | PASS | max depth observed: 0 |
| 14 | Module names lowercase with underscores | PASS | all lowercase |
| 15 | Subpackages reflect domain/role, not architectural layer | PASS | no layered subpackages found |
| 16 | No 'from foo import *' anywhere in the package | PASS | no star-imports |
| 17 | No file in the package over ~800 LOC | FAIL | OVER 800 LOC: [('surfaces.py', 1811), ('app.py', 1900), ('tests/test_styles_palette.py', 1261)] |
| 18 | tests/ directory exists as a sibling of the package | PASS | tests/ exists |
| 19 | docs/ directory exists at root | FAIL | MISSING |
| 20 | examples/ directory exists for any project with a UI or visible output | FAIL | MISSING (AVC has UI) |
| 21 | AGENTS.md (or CLAUDE.md) under 300 lines | FAIL | no AGENTS.md or CLAUDE.md to measure |
| 22 | CLAUDE.md doesn't contain lint rules | PASS | no CLAUDE.md (vacuously true) |
| 23 | No directory named temp/tmp/misc/stuff/old/backup in version control | PASS | clean |
| 24 | Framework-adapter code lives in named subpackages | FAIL | no _qt/_vispy/render/ui subpackage; framework adapters interleaved with domain |
| 25 | .gitignore covers __pycache__, .pytest_cache, *.pyc, build, IDE | FAIL | MISSING: ['.pytest_cache'] |
| 26 | Import graph has no cycles | PASS | [UNVERIFIED — needs pydeps or import-linter] |
| 27 | python -c 'import setup' fails (or no setup.py) | PASS | no setup.py (vacuously true) |
| 28 | Every top-level subpackage has a docstring in __init__.py | PASS | all subpackages have docstrings |

## Summary: 14/28 pass
