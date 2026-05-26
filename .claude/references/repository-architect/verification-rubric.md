# Verification rubric (26 items: scout-C's 20 + TSP-shape items 21-25 + TSP-11 item 26)

Post-execution rubric run by the execution-critic in Phase 5 Step 1 and partially by the parity-verifier after each batch in Phase 4 Step 4b. Each item is binary (PASS/FAIL) with a concrete command to check.

Items 1-20 are scout-C's original safe-refactor rubric (process discipline: tests, coverage, cycles, shims, anchors).  **Items 21-25 are the TSP-shape rubric** — they grade whether the restructure achieved the architectural goal of a thinner-rooted, deeper, responsibility-named tree.  **Item 26 is the TSP-11 entry-point pseudocode rubric** — it grades whether every root entry point reads as pseudocode (function-call density ≥70%, no business logic in body, post-state LOC under the advisory budget).  A restructure that passes 1-20 but fails 21-26 has executed a safe move that didn't improve the architecture — that's a TSP-10 / TSP-11 failure and a HIGH finding.

## The 26 items

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
| 21 | **TSP-1 root-py count did not regress** | `find . -maxdepth 1 -name '*.py' -not -name 'conftest.py' -not -name 'setup.py' \| wc -l` post-count ≤ pre-count (AVC's pre-count is 1: `app.py`); regression = HIGH | 5 |
| 22 | **TSP-2/3 import contracts + cycles still green** | `lint-imports` reports both forbidden contracts KEPT; `pydeps --show-cycles` outputs empty set | 4 + 5 |
| 23 | **TSP-5 responsibility-name banlist clean** | `bash .claude/scripts/repository-architect/check-banlist.sh` returns empty (banlist canonical: see `anti-patterns.md` R19) | 5 |
| 24 | **TSP-8 call-graph alignment** | For every new module in the post-state tree, walk `audit/call-graph.json` (pre) and confirm the source symbols in this module formed a call-cluster (no orphan-grouped symbols, no cluster-splitting across siblings) | 5 |
| 25 | **TSP-10 tree-shape improved or non-regressed** | `rectify/tsp-scorecard-diff.md` shows post-state grade ≥ pre-state grade; depth/fan-out either improved or held; any TSP-N regression has an explicit PLAN.md justification | 5 |
| 26 | **TSP-11 entry-point pseudocode** | AST: call-density ≥70% AND no business-logic patterns (formula eval, panel ctor, parsing, Qt enums, file I/O) AND LOC ≤500.  Full methodology: `.claude/references/repository-architect/tsp-11-computation.md` (consumed identically by auditor + execution-critic).  Severity per the Severity-mapping table below. | 4 (when entry point touched) + 5 |

## How phases consume the rubric

- **Phase 3** uses item 20 once (rollback rehearsal in a worktree).
- **Phase 4 parity-verifier** runs items 1, 2, 4, 5, 6, 8, 10, 11, 14, 17, 19, 22 per batch.  (Item 22 is cheap per-batch — `lint-imports` and `pydeps --show-cycles` both run fast.)
- **Phase 5 execution-critic** re-walks the FULL 26 items against the final diff. Items 13, 16, 21, 23, 24, 25, 26 are unique to Phase 5 (except item 26 which Phase 4 parity-verifier also runs whenever the entry point is touched in a batch).  The TSP-shape items (21-26) feed `rectify/tsp-scorecard-post.md` and `rectify/tsp-scorecard-diff.md` (with `audit/tsp-scorecard-pre.md` as the diff baseline).

## Severity mapping

| Item failure | Severity |
|---|---|
| 1, 2, 3, 6, 7, 9, 10, 11, 13, 14, 17, 22, 26 (when entry point touched and LOC grew) | CRITICAL (blocks ship) |
| 4, 5, 8 (within 2x tolerance), 21, 23, 24, 25, 26 (entry-point density/business-logic regression without LOC growth) | HIGH |
| 4, 5, 8 (within 5x tolerance) | MEDIUM |
| 12, 15, 18 | MEDIUM |
| 16, 19, 20 | LOW |

## Anti-pattern guard

Per scout-C §10.2 ("the tests will catch any regression"): items 1 alone is NOT sufficient. Items 2-11 must also pass. The execution-critic enforces this — a green pytest with FAILing items 2-11 is still a CRITICAL.

Per TSP-10 ("LOC is a signal, not a goal") + TSP-11 ("entry points read as pseudocode"): items 1-20 alone are NOT sufficient.  A restructure that passes process-discipline items 1-20 but fails tree-shape items 21-25 has moved files safely WITHOUT improving the architecture.  A restructure that passes 1-25 but fails item 26 has improved the subpackage tree while leaving the root entry point monolithic — also a failure.  The execution-critic flags both as HIGH and surfaces them in the Phase 5 final summary's `TSP grade` line.
