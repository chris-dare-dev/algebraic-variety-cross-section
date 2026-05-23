
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)

- **False positive pattern — package __init__ orphan:** The static graph analysis flagged `panels` (the new package `__init__.py`) as an orphan because no file contains an explicit `import panels` statement. In reality, Python's import machinery always runs a package's `__init__.py` before any submodule access. Any `from panels.appearance import X` implicitly imports `panels` first. Filter package `__init__` nodes from the orphan check (or treat them as always having fan-in >= the count of their submodule importers).

- **conftest drift gotcha:** AVC has zero conftest.py files. When the project has no conftest.py at any level, the conftest scope drift check is vacuously satisfied and can be short-circuited immediately after a `find` confirms absence. Only `.venv` site-package conftest files will appear in a global find — those are always out of scope.

- **pydeps unusable when directory name has hyphens:** The repo directory is named `algebraic-variety-cross-section`. pydeps fails with "not a valid Python module name" because hyphens are not valid Python identifiers. For any flat-layout repo in a hyphenated directory, substitute direct LibCST parse of all `.py` files for the pydeps graph. The result is equivalent for flat-layout projects. Record this in baseline.imports.json comment or companion log so future agents don't retry pydeps.

- **LibCST version note:** 1.8.6 (installed). `libcst.__version__` raises AttributeError; use `libcst._version.__version__` instead. No parse quirks observed on this codebase (Python 3.12 syntax, PySide6, Numba). Analysis of 102 files completed in ~0.14s.

- **Test guard weakening pattern (non-blocking):** Tests that read source files by absolute path (e.g. `repo_root / "appearance_panel.py"`) become guards on the SHIM rather than the moved content after a module-level move. These tests will still PASS (shims are clean), but they no longer cover the new location. Flag this as a Phase 5 test-suggester item rather than a dry-run failure. It is a test-quality observation, not a correctness regression.

- **Star-import baseline.starimports.txt false positives:** The baseline starimports grep can match the `.claude/scripts/` files (which contain `import *` in grep command strings and comments). Always exclude `.claude/` when scanning for star-imports in production code. The correct production star-import count for AVC is zero.

## Lesson from restructure-feature-subpackages-2026q2-r2 (2026-05-23)

- **False positive pattern — package __init__ orphan (confirmed from r1):** The `panels/__init__.py` hub shim has implicit fan-in from test files that use `from panels.X import Y`. Package `__init__` nodes must always be excluded from orphan checks. Applies doubly when the `__init__` is itself a backward-compat hub shim.

- **Symbol-map naming typo pattern:** `fano_segre` vs `fano_segre_cubic` — the symbol-map used a truncated alias for the function that doesn't match the actual `surfaces.py` definition. Root cause: the PLAN's human-readable Batch 7 table had the wrong name, which propagated to the JSON. **Lesson:** before writing the symbol-map, grep the actual source for each symbol entry to verify exact spelling. `grep -n "^def fano_"` or similar is a 5-second check that prevents a blocking dry-run finding.

- **rewrite-imports.py last-wins bug for symbol_renames:** When multiple symbol-kind entries in a batch have the same `"from"` module (e.g., all Batch 5 symbols come from `"surfaces"`), the `symbol_renames` dict overwrites on each entry — only the last symbol-to-module mapping is retained. This is a latent defect. In r2 it is not triggered because: (a) Batch 5 LibCST rewrite targets only import `ParamSpec` from `surfaces`, (b) test files are NOT rewritten by LibCST, (c) the hub shim is built manually. But warn Phase 4 implementers never to run `rewrite-imports.py` with symbol-kind Batch 5-8 entries on test files.

- **conftest drift gotcha (re-confirmed):** AVC still has zero conftest.py files. Short-circuit remains valid. Check remains O(1) via find.

- **LibCST 1.8.6 traversal API:** Use `tree.visit(v)` (not `tree.walk(v)` which raises AttributeError). The `visit()` method returns the (potentially modified) tree. `CSTVisitor` subclass with `visit_ImportFrom` and `visit_Import` methods works correctly with `tree.visit(v)`. Attribute nodes: use a recursive `dotted_name(node)` helper walking `Attribute.value` → `Attribute.attr.value`. ImportStar must be checked as `isinstance(node.names, cst.ImportStar)`.

- **r2 verdict: YELLOW** (3 broken imports from symbol-map typo; 2-entry fix unblocks it). No new cycles, no orphans, no collection loss, no conftest drift, no star-imports.

## CORRECTION 2026-05-23 (restructure-full-audit-2026q2-r1 batch 4)
Panel file locations changed. Old path → new path:
- `appearance_panel.py` (root) → `panels/appearance.py`; module `appearance_panel` → `panels.appearance`
- `view_panel.py` (root) → `panels/view.py`; module `view_panel` → `panels.view`
- `parameters_panel.py` (root) → `panels/parameters.py`; module `parameters_panel` → `panels.parameters`
- `parameter_grid_panel.py` (root) → `panels/parameter_grid_panel.py`; module `parameter_grid_panel` → `panels.parameter_grid_panel`
The "test guard weakening" lesson from dry-run: the fix was applied — tests now read `panels/appearance.py` etc.
Root-level shims contain only 18-line __getattr__ forwarders. See MOVES.md.
