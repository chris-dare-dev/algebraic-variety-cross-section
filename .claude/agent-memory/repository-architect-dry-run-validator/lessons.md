
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)

- **False positive pattern — package __init__ orphan:** The static graph analysis flagged `panels` (the new package `__init__.py`) as an orphan because no file contains an explicit `import panels` statement. In reality, Python's import machinery always runs a package's `__init__.py` before any submodule access. Any `from panels.appearance import X` implicitly imports `panels` first. Filter package `__init__` nodes from the orphan check (or treat them as always having fan-in >= the count of their submodule importers).

- **conftest drift gotcha:** AVC has zero conftest.py files. When the project has no conftest.py at any level, the conftest scope drift check is vacuously satisfied and can be short-circuited immediately after a `find` confirms absence. Only `.venv` site-package conftest files will appear in a global find — those are always out of scope.

- **pydeps unusable when directory name has hyphens:** The repo directory is named `algebraic-variety-cross-section`. pydeps fails with "not a valid Python module name" because hyphens are not valid Python identifiers. For any flat-layout repo in a hyphenated directory, substitute direct LibCST parse of all `.py` files for the pydeps graph. The result is equivalent for flat-layout projects. Record this in baseline.imports.json comment or companion log so future agents don't retry pydeps.

- **LibCST version note:** 1.8.6 (installed). `libcst.__version__` raises AttributeError; use `libcst._version.__version__` instead. No parse quirks observed on this codebase (Python 3.12 syntax, PySide6, Numba). Analysis of 102 files completed in ~0.14s.

- **Test guard weakening pattern (non-blocking):** Tests that read source files by absolute path (e.g. `repo_root / "appearance_panel.py"`) become guards on the SHIM rather than the moved content after a module-level move. These tests will still PASS (shims are clean), but they no longer cover the new location. Flag this as a Phase 5 test-suggester item rather than a dry-run failure. It is a test-quality observation, not a correctness regression.

- **Star-import baseline.starimports.txt false positives:** The baseline starimports grep can match the `.claude/scripts/` files (which contain `import *` in grep command strings and comments). Always exclude `.claude/` when scanning for star-imports in production code. The correct production star-import count for AVC is zero.
