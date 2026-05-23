
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
