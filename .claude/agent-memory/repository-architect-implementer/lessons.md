
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
