
## Lesson from restructure-full-audit-2026q2-r1 batch 1 (2026-05-23)
- Shim quirk: Batch 1 has zero shims (no file moves) — skip shim template lookup entirely for addition-only batches
- AVC-specific gotcha: `.claude/notes/` and `.claude/agent-memory/` modified files in git status are non-blocking for pre-flight; they are outside source scope
- LibCST rewrite surprise: N/A for batch 1 (no import rewrites)
- Tests-per-commit wall-clock: ~6.6 s for 499 tests on macOS Apple Silicon (Python 3.12, Numba cold cache already warm)
- README stale-fact: the badge URL encoding uses `%20` for spaces — edit the badge text directly, not the URL separately
- CONTEXT.md §12 is also duplicated in the "Last updated" header line at the top of the file — both must be updated when fixing stale stats
- .venv path on this repo is `.venv/bin/python` (macOS), NOT `.venv/Scripts/python.exe` (Windows) — the phase-4-execute.md template uses the Windows path; always use `.venv/bin/python` for this project

## Lesson from restructure-full-audit-2026q2-r1 batch 2 (2026-05-23)
- Shim quirk: Batch 2 has zero shims (no file moves, only additions) — skip shim template lookup entirely for addition-only batches
- AVC-specific gotcha: macOS allows `ln -s AGENTS.md CLAUDE.md` without admin rights; the relative symlink (mode 120000) is tracked by git natively — no fallback prose file needed
- LibCST rewrite surprise: N/A for batch 2 (no import rewrites)
- Tests-per-commit wall-clock: ~6.5-7.5 s for 499 tests (consistent with batch 1 timing)
- pyproject.toml build-backend: use `setuptools.backends.legacy:build` not `setuptools.build_meta` — the former is the PyPA 2026 canonical form; both work but legacy:build is the setuptools >=68 preference
- AGENTS.md line count: 143 lines achieved the "~150 target" from the plan; wc -l is the fast check before committing

## Lesson from restructure-full-audit-2026q2-r1 batch 3 (2026-05-23)
- Shim quirk: Batch 3 has zero shims (no file moves, only in-place fixes) — skip shim template lookup entirely for in-place-fix batches
- AVC-specific gotcha: QGraphicsView inline setStyleSheet() for background color MUST pair the fix with a new _render_stylesheet() role selector; also must carry over border: none from the original rule or the view gets a visible frame
- LibCST rewrite surprise: N/A for batch 3 (no import rewrites; only removed one unused import from import block manually)
- Tests-per-commit wall-clock: ~6.5-7.3 s for 499 tests (consistent with batches 1-2)
- Guard tuple pattern: test_no_inline_color_styles_in_panel_files forbidden tuple only flags 3 specific legacy constants (MUTED_TEXT_STYLE, VALUE_MONO_STYLE, RANGE_LABEL_STYLE); SMALL_LABEL_STYLE is font-only and NOT in the forbidden tuple — adding a file to the guard tuple is safe even if SMALL_LABEL_STYLE is used in that file

## Lesson from restructure-full-audit-2026q2-r1 batch 4 (2026-05-23)
- Shim quirk: Template-2 __getattr__ shims work perfectly; stacklevel=2 correctly places DeprecationWarning at the caller's site. The _reload_shim()/sys.modules.pop() pattern is required in test_panels_shims.py to get a fresh import (without it, catch_warnings gets a no-op because the module is already cached without a warning)
- AVC-specific gotcha: rewrite-imports.py rglobs ALL .py files including .claude/scripts/ — these must be manually reverted after the LibCST run (hard rule: never modify .claude/scripts/). The script's filter only excludes .venv/, .git/, and .claude/worktrees/
- LibCST rewrite surprise: LibCST rewrites `import appearance_panel` -> `import panels.appearance` but DOES NOT update `patch.object(appearance_panel, ...)` references because those are attribute accesses on a name, not import statements. These must be fixed manually in the same commit (2 occurrences in test_styles_palette.py: the patch.object call uses the old module variable name which is now undefined)
- LibCST rewrite surprise 2: LibCST does NOT rewrite string literals. Tests that use `parent.parent / "appearance_panel.py"` as a file-path string to READ panel source code (not import it) will fail with FileNotFoundError after git mv. These must be manually updated to `panels/appearance.py` etc. — 5 in test_styles_palette.py, 6 in test_enriques_hq_smoothing.py
- AVC-specific gotcha 2: tests that READ panel files as text (for source-grep assertions) are affected by the git mv in a way that shims CANNOT fix — the shim is a new 18-line file at the old path, not the original content. Always check for `read_text()` / `.readlines()` patterns on old panel paths when planning a module move
- PLAN Op ordering note: the inline-style guard tuple retargeting (PLAN Op 4 / commit 8) MUST happen in the same commit as the LibCST rewrite (Op 6), because the guard reads the files as text and will fail with FileNotFoundError before shims are written. Bundling path-string fixes with LibCST import fixes in Op 6 is correct
- Tests-per-commit wall-clock: ~6.1-7.2 s for 499-503 tests (consistent with batches 1-3; the 4 new shim tests add negligible overhead at ~0.36 s)

## CORRECTION 2026-05-23 (restructure-full-audit-2026q2-r1 batch 4)
Panel file locations changed. Old path → new path:
- `appearance_panel.py` (root) → `panels/appearance.py`; module `appearance_panel` → `panels.appearance`
- `view_panel.py` (root) → `panels/view.py`; module `view_panel` → `panels.view`
- `parameters_panel.py` (root) → `panels/parameters.py`; module `parameters_panel` → `panels.parameters`
- `parameter_grid_panel.py` (root) → `panels/parameter_grid_panel.py`; module `parameter_grid_panel` → `panels.parameter_grid_panel`
Any lesson referencing `parent.parent / "appearance_panel.py"` etc. as a file path: those test fixtures were
updated to `panels/appearance.py` etc. in the batch 4 LibCST rewrite. Root-level shims remain but contain
only the 18-line __getattr__ forwarder — source grep tests must use the panels/ paths. See MOVES.md.

## Lesson from restructure-full-audit-2026q2-r1 Batch 4 rectify (2026-05-23)

**Bisect-redness from delayed LibCST rewrite.**  When introducing a subpackage via 4 sequential `git mv` commits followed by a LibCST import rewrite (Batch 4 of the full-audit-r1 restructure, commits ffd358a..0e51719), the 4 intermediate commits are bisect-red because the moved modules still exist at old paths but `app.py` references the NEW package-qualified paths only after the rewrite lands.  Tests like `tests/test_clip_cache.py` that import via `from app import ...` would fail with `ModuleNotFoundError` if `git bisect` landed on one of those 4 SHAs.

**Lesson for future restructures:** the LibCST rewrite should land in the SAME commit as the corresponding `git mv` (one rewrite per move, four total), OR all 5 ops should be a SINGLE commit if rename detection survives (verify with `git diff --find-renames` before committing).  The "one Fowler op per commit" rule from phase-4-execute.md does NOT mean "one mechanical action per commit" — it means "one user-visible refactor unit per commit."  A `git mv` without its accompanying import rewrite is not a complete unit.

## Lesson from restructure-feature-subpackages-2026q2-r2 batch 1 (2026-05-23)
- Shim quirk: Batch 1 has zero shims (deletion-only batch) — skip shim template lookup entirely
- AVC-specific gotcha: `refactor-batch1-end` tag already existed from r1 restructure; for r2 use `refactor-r2-batch{N}-end` naming convention to avoid tag collision across restructure generations
- Deletion sequence: ALWAYS delete the test file that imports the shims FIRST (before deleting the shims themselves). If shims are deleted first, the test file fails to collect (ModuleNotFoundError) → bisect-red intermediate commits. Test-file-first keeps every commit bisect-green.
- LOC estimate accuracy: test_panels_shims.py was 97 LOC (actual), not ~40 LOC as PLAN.md estimated — the _reload_shim helper + full docstrings add ~57 LOC overhead. Plan estimates for test file sizes should add 2-3x multiplier over "N tests × avg test body".
- Tests-per-commit wall-clock: ~7-8 s for 499 tests on macOS Apple Silicon (consistent with r1; slightly slower than r1 batch 1's 6.6 s probably due to test suite warmup variance)

## CORRECTION 2026-05-23 (restructure-feature-subpackages-2026q2-r2 batch 1)
The 4 root-level r1 panel shim files and their test file have been deleted (M+1 cycle closed):
- `appearance_panel.py` (root shim) → DELETED. Canonical: `panels/appearance.py`
- `view_panel.py` (root shim) → DELETED. Canonical: `panels/view.py`
- `parameters_panel.py` (root shim) → DELETED. Canonical: `panels/parameters.py`
- `parameter_grid_panel.py` (root shim) → DELETED. Canonical: `panels/parameter_grid_panel.py`
- `tests/test_panels_shims.py` → DELETED (97 LOC; vacuous after shim removal).
Prior CORRECTION block statement "Root-level shims remain but contain only the 18-line __getattr__ forwarder" is now false — root shims do NOT remain. Source grep tests continue using panels/ paths; no shim fallback.
Tag: `refactor-r2-batch1-end` at 16b251b.

## Lesson from restructure-single-root-2026q2-r3 batch 1 (2026-05-24)
- Shim quirk: B1 is tooling-only (no shims, no file moves) — skip shim template lookup entirely
- AVC-specific gotcha: rewrite-imports.py symbol_renames was dict[old_module, (new_mod, sym)] which silently overwrites all-but-last symbol when multiple symbols from same source module map to different destinations. Fixed to dict[(old_module, symbol_name), new_module]. This would have caused ALL B4 symbols to be wrong — only _hanson_cross_section would have been correctly routed.
- LibCST rewrite surprise: leave_ImportFrom cannot return FlattenSentinel (multiple nodes). Multi-alias splitting MUST be done in leave_SimpleStatementLine which can return FlattenSentinel. This is the correct hook for one-statement-to-many expansion.
- LibCST rewrite surprise 2: MetadataWrapper(tree).visit(transformer) is required (not tree.visit(transformer)) when METADATA_DEPENDENCIES is declared. QualifiedNameProvider.has_name() is callable from leave_Name etc. only after wrapping.
- LibCST rewrite surprise 3: ScopeProvider is NOT needed alongside QualifiedNameProvider for has_name() — omitting it saves parse time per file with no functional cost.
- Walker exclusion: the old .claude/worktrees/ exclusion was too narrow — the codemod was walking all of .claude/scripts/. Extended to .claude/ prefix (catches scripts/, notes/, agent-memory/, hooks/, commands/).
- Tests-per-commit wall-clock: ~7.16s for 506 tests (consistent with prior batches; no source changes)

## Lesson from restructure-single-root-2026q2-r3 batch 2 (2026-05-24)
- Shim quirk: B2 has zero shims (no back-compat shim for parameter_grid; all callers are in-tree and rewritten by LibCST)
- AVC-specific gotcha: varieties/types.py already has `from __future__ import annotations` AND `import pyvista as pv` — adding a @runtime_checkable Protocol referencing pv.PolyData requires NO forward-ref string and NO new pyvista import. Only add `from typing import Protocol, runtime_checkable`.
- LibCST rewrite surprise: module-rename codemod (kind=module, batch=2) ran cleanly on all 4 alias-form callers with zero false positives. The B1 codemod fix (dict[(old_mod, sym)] key schema) is required even for batch=2 module-level renames because the codemod walks ALL batches' symbol entries — the B4 entries would have corrupted output without the fix.
- Tests-per-commit wall-clock: ~5.70-6.50s for 506 tests (consistent with prior batches)

## Lesson from restructure-single-root-2026q2-r3 batch 3 (2026-05-24)
- Shim quirk: B3 is deletion-only (zero new shims) — skip shim template lookup entirely
- AVC-specific gotcha: When deleting a root-level shim (e.g. `icons.py`), scan ALL test files for `importlib.import_module("<shim-name>")` string literals — LibCST does NOT rewrite these and the pre-flight grep only catches `^import` / `^from` at line-start. The `test_icons.py` file had `importlib.import_module("icons")` that was missed by the pre-flight scan.
- AVC-specific gotcha 2: `patch.object(module_alias, attr, mock)` breaks after `sys.modules.pop(module_name, None)` because the alias still points to the OLD module object. The test-function's local `import _qt.icons` gets the NEW re-loaded module from sys.modules. These two objects diverge. Fix: use the string form `patch("_qt.icons._qta", mock)` which resolves via sys.modules at patch-entry time.
- LibCST rewrite surprise: N/A for batch 3 (no import rewrites; deletions only)
- Tests-per-commit wall-clock: ~5.75s for 499 tests (consistent with prior batches)

## Lesson from restructure-single-root-2026q2-r3 batch 4 (2026-05-24)
- Shim quirk: B4 introduces zero new shims (surfaces.py is deleted, not shimmed) — skip shim template lookup entirely
- AVC-specific gotcha: For bare `import surfaces` sites, the LibCST codemod rewrites the body attribute-accesses `surfaces.X.Y` → `varieties.X.Y` but leaves the bare `import surfaces` statement behind (no matching `from surfaces import` pattern). Manual fix: replace `import surfaces` with `import varieties.X` statements for each sub-module referenced in the body via dotted access.
- LibCST rewrite surprise: The codemod's attribute-access rewrite converts `surfaces.enriques.enriques_figure_1` → `varieties.enriques.enriques_figure_1`, treating the dotted chain as an attribute-access on a module alias. This creates dangling `varieties.X.Y` references without any corresponding `import varieties.X`. After the manual fix (`import varieties.enriques`, `import varieties.k3`, etc.), the `varieties.X.Y()` calls resolve correctly via Python's package sub-module access.
- DeprecationWarning gate: The mandatory `-W error::DeprecationWarning -m pytest -q` gate between commit 1 and commit 2 passed cleanly (499 passed, exit 0). No caller was still routing through surfaces.py's `__getattr__` shim after the LibCST rewrite + manual fixes.
- Tests-per-commit wall-clock: ~5.78-6.10s for 499 tests (consistent with prior B3 timing)
- Single-root target achieved: `ls *.py` outputs only `app.py` after B4 commit 2.

## Lesson from restructure-single-root-2026q2-r3 batch 5 (2026-05-24)
- Shim quirk: B5 is lock-in only (zero new shims, zero file moves) — skip shim template lookup entirely
- AVC-specific gotcha: import-linter 2.x requires `include_external_packages = true` in `[tool.importlinter]` for `forbidden_modules` entries that name third-party packages (PySide6, PyQt5, PyQt6). Without this flag, lint-imports silently ignores external-package names in the forbidden list.
- import-linter quirk: empty contracts list (`Contracts: 0 kept, 0 broken`) is a valid step-0 confirmation that tooling is installed and working — do not skip this no-op run, it catches misconfigured root_packages before adding real contracts.
- subprocess smoke pattern: `app` and `_qt` are subprocess-safe for the parametrize list because `app.py` guards `QApplication()` inside `if __name__ == "__main__": main()` and `_qt/__init__.py` is docstring-only. The scout's warning "DO NOT include app/_qt" applies only to packages that eagerly instantiate Qt at module scope.
- Tests-per-commit wall-clock: ~7.21s for 504 tests (5 new smoke tests add ~1.66s; subprocess timeout=30 is generous, actual per-test wall clock ~0.33s each)
