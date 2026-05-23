# ROLLBACK.md — restructure-full-audit-2026q2-r1

**Baseline tag:** `refactor-baseline-restructure-full-audit-2026q2-r1`
**Baseline SHA:** `c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c`
**Created:** 2026-05-23 (Phase 3 Step 4 per phase-3-preflight.md v2 fix)

## Tier 1 — whole-restructure revert (preferred)

After the restructure completes (or partially completes), to roll back ALL of it:

```bash
# Tag-based form (preferred — easier to remember weeks later):
git revert --no-commit refactor-baseline-restructure-full-audit-2026q2-r1..HEAD
git commit -m "revert: roll back restructure-full-audit-2026q2-r1"
```

```bash
# SHA-based equivalent (if tag is gone for any reason):
git revert --no-commit c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c..HEAD
git commit -m "revert: roll back restructure-full-audit-2026q2-r1"
```

**Pre-conditions:**
- The chain `c7b2bd8..HEAD` contains ONLY restructure commits (the pipeline enforces this via Phase 4's "one Fowler op per commit" rule + Phase 4 dedicated branch on `main`).
- Each commit was independently green (parity-verifier returned PASS for each batch).
- No production state outside git was migrated (this is a Python source restructure — holds).

**Tested:** to be rehearsed in a scratch worktree before Phase 4 begins (PLAN.md §8 requires this). Status: PENDING (to be filled in by the user before GATE 3 approval, or auto-rehearsed by a future rollback-rehearser agent).

## Tier 2 — branch-by-abstraction toggle

Not applicable. This is a Python source restructure, not a runtime swap.

## Tier 3 — per-batch partial rollback

The Phase 4 implementer creates per-batch end-of-batch tags after each batch's parity-verifier returns PASS:
- `refactor-batch1-end` (after Batch 1: LICENSE + CHANGELOG + gitignore + stale-fact fixes)
- `refactor-batch2-end` (after Batch 2: AGENTS.md + CLAUDE.md + pyproject.toml)
- `refactor-batch3-end` (after Batch 3: dark-mode fix)
- `refactor-batch4-end` (after Batch 4: panels/ subpackage)

To roll back ONLY Batch 4 (and any partial work after it):
```bash
git revert --no-commit refactor-batch3-end..HEAD
git commit -m "revert: partial rollback of Batch 4 (panels/ subpackage)"
```

To roll back Batch 3 + 4:
```bash
git revert --no-commit refactor-batch2-end..HEAD
git commit -m "revert: partial rollback of Batches 3 + 4"
```

Pattern: revert from `refactor-batch{N-1}-end..HEAD` to undo Batch N forward.

## What rollback does NOT restore

The following are NOT covered by `git revert` and require separate restoration:

- **MOVES.md entries** — manual revert via `git checkout refactor-baseline-restructure-full-audit-2026q2-r1 -- MOVES.md` (or simply delete the new section if MOVES.md is otherwise untouched).
- **CLAUDE.md, CONTEXT.md, README.md edits** — each may have been edited by Batch 1 stale-fact fixes AND Batch 4 panel-path updates. Revert per file via `git checkout refactor-baseline-restructure-full-audit-2026q2-r1 -- <path>`.
- **Agent-memory CORRECTION blocks** — appended to other agents' `lessons.md` by the anchor-updater. Manual revert via `git checkout refactor-baseline-restructure-full-audit-2026q2-r1 -- .claude/agent-memory/`.

## Rollback rehearsal (REQUIRED before Phase 4 — per PLAN.md §8)

Before approving GATE 3, the user should rehearse the Tier 1 revert in a scratch worktree:

```bash
# Create scratch worktree
git worktree add /tmp/avc-rollback-test refactor-baseline-restructure-full-audit-2026q2-r1
cd /tmp/avc-rollback-test

# Verify it matches the baseline state
git rev-parse HEAD  # should print c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c
.venv/bin/python -m pytest -q  # should report 499 passed

# Clean up
cd /Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section
git worktree remove /tmp/avc-rollback-test
```

If the worktree's HEAD matches and `pytest -q` returns 499 passed, the Tier 1 baseline is valid and the rollback can be performed safely if needed.

## Recovery if rollback itself fails

If `git revert` produces conflicts (it shouldn't for a clean restructure chain, but defensively):

1. `git revert --abort` to back out the revert attempt.
2. Inspect: `git log --oneline refactor-baseline-restructure-full-audit-2026q2-r1..HEAD` — confirm chain contains only restructure commits.
3. If chain is contaminated with feature work, the contaminating commit(s) must be cherry-picked separately AFTER the revert lands. Document in the revert commit body which commits were preserved.
