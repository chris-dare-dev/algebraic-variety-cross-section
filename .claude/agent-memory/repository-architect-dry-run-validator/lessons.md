
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

## Lesson from restructure-single-root-2026q2-r3 (2026-05-24)

- **False positive pattern — none this run.** All 34 broken-import findings were genuine: the symbol-map was drafted from a pre-r2 naming scheme and not reconciled against the actual post-r2 symbol names in surfaces.py/varieties/*. False-positive risk was low because findings were cross-validated by AST-parsing both the source (surfaces.py re-exports) and the destination (varieties/ function defs), not just string-matching.

- **Symbol-map naming audit pattern:** Always cross-check symbol-map entries against BOTH (a) what the hub shim actually exports (surfaces.py re-export block) AND (b) what the target modules actually define (def/class lines in varieties/*). A mismatch at either end is a broken import. The r3 map had 17 wrong names referencing non-existent symbols. Root cause: map was drafted from an older design doc that named functions differently (e.g., `calabi_yau_quartic_pencil` vs actual `calabi_yau_cubic`, `fano_grassmannian` vs actual `fano_sextic_double_solid`, `_enriques_field_kernel` vs `_enriques_fig1_field_kernel`). Lesson: run `grep "^def \|^[A-Z_]*PARAMS" <target_module>` to verify every entry before committing the symbol-map.

- **JSON schema mismatch pattern:** The rewrite-imports.py codemod uses schema v1.0 (flat list with "batch", "kind", "from", "to", "symbol" keys). The r3 symbol-map uses schema v1.1 (nested dict: batches.B4.moves[] with "old", "new", "form" keys). These are incompatible — B1 must reconcile the parser OR the symbol-map must be reverted to v1.0 flat format. Flag any schema_version field in symbol-map as a mandatory B1 pre-check.

- **import-linter contract vs actual code pattern:** Always grep the proposed "forbidden" import targets against the actual source files before writing the contract. `render/worker.py` imports `from PySide6.QtCore import QObject, QRunnable, Signal` structurally (MeshWorker inherits QRunnable). The PLAN contract said "render imports nothing from PySide6" — false at HEAD. Check with: `grep -rn "^from PySide6\|^import PySide6" <layer_dir>/` before writing any forbidden-import contract for that layer.

- **conftest drift gotcha (re-confirmed):** AVC still has zero conftest.py files. Short-circuit remains valid.

- **LibCST version note:** 1.8.6 (unchanged from r1/r2). No new quirks. `tree.visit(v)` API confirmed working.

## CORRECTION 2026-05-23 (restructure-full-audit-2026q2-r1 batch 4)
Panel file locations changed. Old path → new path:
- `appearance_panel.py` (root) → `panels/appearance.py`; module `appearance_panel` → `panels.appearance`
- `view_panel.py` (root) → `panels/view.py`; module `view_panel` → `panels.view`
- `parameters_panel.py` (root) → `panels/parameters.py`; module `parameters_panel` → `panels.parameters`
- `parameter_grid_panel.py` (root) → `panels/parameter_grid_panel.py`; module `parameter_grid_panel` → `panels.parameter_grid_panel`
The "test guard weakening" lesson from dry-run: the fix was applied — tests now read `panels/appearance.py` etc.
Root-level shims contain only 18-line __getattr__ forwarders. See MOVES.md.
