
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
