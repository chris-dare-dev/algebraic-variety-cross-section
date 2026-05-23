
## Lesson from restructure-full-audit-2026q2-r1 batch 1 (2026-05-23)
- Shim quirk: Batch 1 has zero shims (no file moves) — skip shim template lookup entirely for addition-only batches
- AVC-specific gotcha: `.claude/notes/` and `.claude/agent-memory/` modified files in git status are non-blocking for pre-flight; they are outside source scope
- LibCST rewrite surprise: N/A for batch 1 (no import rewrites)
- Tests-per-commit wall-clock: ~6.6 s for 499 tests on macOS Apple Silicon (Python 3.12, Numba cold cache already warm)
- README stale-fact: the badge URL encoding uses `%20` for spaces — edit the badge text directly, not the URL separately
- CONTEXT.md §12 is also duplicated in the "Last updated" header line at the top of the file — both must be updated when fixing stale stats
- .venv path on this repo is `.venv/bin/python` (macOS), NOT `.venv/Scripts/python.exe` (Windows) — the phase-4-execute.md template uses the Windows path; always use `.venv/bin/python` for this project
