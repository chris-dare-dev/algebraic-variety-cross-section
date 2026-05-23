# Verification rubric (scout-C's 20 items)

Post-execution rubric run by the execution-critic in Phase 5 Step 1 and partially by the parity-verifier after each batch in Phase 4 Step 4b. Each item is binary (PASS/FAIL) with a concrete command to check.

## The 20 items

| # | Item | Command / check | Phase |
|---|---|---|---|
| 1 | All original tests still pass | `pytest -q` exit 0 | 4 (every batch) |
| 2 | Test collection count preserved | `diff <(pytest --collect-only -q) baseline.collect.txt` empty (or only removals listed in PLAN.md) | 4 + 5 |
| 3 | No new test files silently skipped | `pytest --collect-only` shows no `<skipped>` markers not present at baseline | 5 |
| 4 | Per-file coverage within ±2% on moved files | coverage XML diff | 4 + 5 |
| 5 | Total coverage within ±1% | `coverage report` total line vs baseline | 4 + 5 |
| 6 | No new import cycles | `pydeps --show-cycles` identical to baseline cycle set | 4 + 5 |
| 7 | No orphan modules | `pydeps` reachability from `app.py` covers every `.py` | 5 |
| 8 | No import-time side effects regressed | `python -X importtime -c "import app"` total within ±20% | 4 + 5 |
| 9 | No module shadowing | No two modules share `__name__` from any import path | 5 |
| 10 | No `from X import *` newly introduced | `grep -rn 'import \*'` set unchanged | 4 (every batch) |
| 11 | Shims emit DeprecationWarning for every renamed/moved symbol | `validate-shims.py` passes | 4 (every batch) |
| 12 | Shim warnings include the new path | grep test in `test_shims.py` (or in validate-shims.py output) | 4 |
| 13 | `git mv` rename detection succeeded | `git log --follow --oneline <new_path>` shows pre-move history | 5 |
| 14 | MOVES.md updated with this restructure's entries | New section present with date + entries | 4 (every batch via anchor-updater) |
| 15 | Root CLAUDE.md / CONTEXT.md pointers updated | grep old paths returns 0 (or only in MOVES.md) | 4 + 5 |
| 16 | Per-folder CLAUDE.md present for each new subpackage | `find . -path './<new_pkg>/CLAUDE.md'` returns the file | 5 (if PLAN.md authorized) |
| 17 | `.claude/notes/**/*.md` cleansed of stale paths (or noted as historical) | `verify-anchors.py` PASS | 4 (every batch) |
| 18 | README.md structure section reflects new tree | manual diff | 5 (if PLAN.md authorized) |
| 19 | `__pycache__` / `.pyc` for moved files cleared | `find . -name __pycache__ -exec rm -rf {} +` then re-run tests; green | 4 (every batch) |
| 20 | Rollback command tested in a scratch worktree | Tier 1 cmd from ROLLBACK.md returns to baseline cleanly | 3 (pre-execute) |

## How phases consume the rubric

- **Phase 3** uses item 20 once (rollback rehearsal in a worktree).
- **Phase 4 parity-verifier** runs items 1, 2, 4, 5, 6, 8, 10, 11, 14, 17, 19 per batch.
- **Phase 5 execution-critic** re-walks the FULL 20 items against the final diff. Item 13 (`git --follow` history) and item 16 (per-folder CLAUDE.md) are unique to Phase 5.

## Severity mapping

| Item failure | Severity |
|---|---|
| 1, 2, 3, 6, 7, 9, 10, 11, 13, 14, 17 | CRITICAL (blocks ship) |
| 4, 5, 8 (within 2x tolerance) | HIGH |
| 4, 5, 8 (within 5x tolerance) | MEDIUM |
| 12, 15, 18 | MEDIUM |
| 16, 19, 20 | LOW |

## Anti-pattern guard

Per scout-C §10.2 ("the tests will catch any regression"): items 1 alone is NOT sufficient. Items 2-11 must also pass. The execution-critic enforces this — a green pytest with FAILing items 2-11 is still a CRITICAL.
