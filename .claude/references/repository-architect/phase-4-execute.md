# Phase 4 — Execute (batched implementer + parity-verifier + anchor-updater)

**Goal:** land the restructure in tiny, testable, individually-revertable commits. Each batch is one Fowler-catalog operation worth of work; the three agents run sequentially WITHIN a batch.

## Per-batch loop

For each batch in PLAN.md (ordered low-risk-first per design-adversary axis 10):

### Step 4a — Implementer

```
Agent: repository-architect-implementer
Inputs:
  {ID}
  {PLAN_PATH}
  {SYMBOL_MAP_PATH}
  {BATCH_NUMBER}
  {BATCH_OPERATION}    (label from PLAN.md)
  {RESTRUCTURE_BASE}   (from state.restructure_base)
  {OUTPUT_PATH}        .claude/notes/repository-architect/{ID}/execute/implementer-batch-{N}-log.md
```

Per-commit checklist the implementer MUST follow:
1. ONE Fowler-catalog operation per commit (Move Function / Move Method / Extract Class / Split Module / Move Module / Rename Module / Introduce Subpackage).
2. `git mv` for every file move (preserves blame).
3. NEVER bundle content edits with moves.
4. Shims use the `__getattr__` pattern from `shim-templates.md` — NEVER star-imports.
5. `rewrite-imports.py` (LibCST) for bulk import rewrites — NEVER `sed`.
6. After every commit: `pytest -q` must pass. 3 attempts max before ABORT.
7. Smoke-test old and new import paths.
8. Commit subject: `refactor({ID}): <operation label> (batch {N}/<M> op {K}/<L>)`.

### Step 4b — Parity verifier

```
Agent: repository-architect-parity-verifier
Inputs:
  {ID}
  {BATCH_NUMBER}
  {BASELINE_DIR}
  {OUTPUT_PATH}  .claude/notes/repository-architect/{ID}/execute/parity-verifier-batch-{N}-report.md
```

Runs 6 mechanical checks (per `verification-rubric.md`):
1. Test collection diff (must be 0 unless tests moved per PLAN.md).
2. Coverage diff (±2% per file, ±1% total).
3. Pydeps cycle diff (set must match baseline).
4. Import-time diff (±20%).
5. Shim validation via `validate-shims.py`.
6. No new star-imports.

Verdict: PASS / FAIL / DEGRADED.

If FAIL, surface to user:
```
PARITY FAILURE in batch {N}:
  - <which check> failed: <details>
Roll back batch {N}? [y/n]
```

Rollback command:
```bash
PRE_BATCH_SHA=$(git log --oneline --grep="batch {N-1}/" -1 --format=%H)
git revert --no-commit $PRE_BATCH_SHA..HEAD
git commit -m "revert: roll back batch {N} due to parity failure"
```

### Step 4c — Anchor updater

```
Agent: repository-architect-anchor-updater
Inputs:
  {ID}
  {BATCH_NUMBER}
  {SYMBOL_MAP_PATH}
  {RESTRUCTURE_BASE}
  {OUTPUT_PATH}  .claude/notes/repository-architect/{ID}/execute/anchor-updater-batch-{N}-report.md
```

Per-batch anchor work:
- Append batch's moves to repo-root `MOVES.md`.
- Update root `CLAUDE.md` `file:line` references (if CLAUDE.md exists).
- Update `CONTEXT.md` / `README.md` IFF PLAN.md §6 authorized.
- Walk `.claude/notes/**/*.md` and `.claude/agent-memory/**/lessons.md` — append `## CORRECTION` blocks for stale references.
- Run `verify-anchors.py {ID} --batch {N}` to confirm.

### Step 4d — Per-batch checkpoint

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --append parity_verifier_reports="\".claude/notes/repository-architect/{ID}/execute/parity-verifier-batch-{N}-report.md\""
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --append anchor_updater_reports="\".claude/notes/repository-architect/{ID}/execute/anchor-updater-batch-{N}-report.md\""

# Increment the batches-landed counter
LANDED=$(.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} --get execute_batches_landed)
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set execute_batches_landed=$((LANDED + 1))
```

## After ALL batches complete

```bash
# Persist commit range
BASE=$(.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} --get restructure_base)
HEAD=$(git rev-parse HEAD)
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set execute_commit_range="\"$BASE..$HEAD\""
for SHA in $(git log --format=%H $BASE..HEAD); do
  .venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
      --append execute_commits="\"$SHA\""
done

# Capture POST baseline + diff
.venv/Scripts/python.exe .claude/scripts/repository-architect/snapshot-baseline.py {ID} --post
.venv/Scripts/python.exe .claude/scripts/repository-architect/diff-baselines.py {ID} > .claude/notes/repository-architect/{ID}/execute/parity-diff.md

.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} execute-complete
bash .claude/hooks/repository-architect/summarize-phase.sh {ID} execute-complete
```

## Phase wall-clock budget

No hard cap (batched can take hours to days). Per-batch soft cap 4h; surface gate-required if exceeded.

## Anti-patterns to refuse

- Bundling content edits with moves (defeats `git mv` rename detection — scout-C §10.5).
- Using `sed` for import rewrites (scout-C §10.6).
- Star-imports in shim (scout-C §10.7).
- Skipping the parity verifier "because the tests passed" (collection count and coverage shape matter — scout-C §10.2).
- Skipping the anchor updater "we'll do it later" (scout-C §10.9).
- Landing batches in random order; high-risk first violates sequencing safety (axis 10 in design-adversary).
