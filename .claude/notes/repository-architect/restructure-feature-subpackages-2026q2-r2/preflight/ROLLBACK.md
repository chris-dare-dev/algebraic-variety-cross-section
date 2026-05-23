# ROLLBACK.md — restructure-feature-subpackages-2026q2-r2

**Baseline tag:** `refactor-baseline-restructure-feature-subpackages-2026q2-r2`
**Baseline SHA:** `2bfc6c8038d57b931f6d4128fb03cd2bb9130645`
**Created:** 2026-05-23 (Phase 3 Step 4)
**Rehearsal:** TESTED 2026-05-23 — `git worktree add` to baseline tag succeeded; HEAD verified at 2bfc6c8. Rollback is valid.

## Tier 1 — whole-restructure revert (preferred)

```bash
# Tag-based form (preferred):
git revert --no-commit refactor-baseline-restructure-feature-subpackages-2026q2-r2..HEAD
git commit -m "revert: roll back restructure-feature-subpackages-2026q2-r2"
```

## Tier 2 — branch-by-abstraction toggle

Not applicable (Python source restructure, no runtime swap).

## Tier 3 — per-batch partial rollback

Implementer creates per-batch end-of-batch tags after each batch's parity-verifier returns PASS:
- `refactor-batch1-end` (after Batch 1: r1 shim cleanup)
- `refactor-batch2-end` (after Batch 2: render/)
- `refactor-batch3-end` (after Batch 3: _qt/)  ← biggest blast radius
- `refactor-batch4-end` (after Batch 4: cross_section/)
- `refactor-batch5-end` (after Batch 5: varieties/types + dispatch)
- `refactor-batch6-end` (after Batch 6: varieties/_kernels + _marching)
- `refactor-batch7-end` (after Batch 7: 4 generator family modules)
- `refactor-batch8-end` (after Batch 8: registry + tooltips)

To roll back batch N + everything after:
```bash
git revert --no-commit refactor-batch{N-1}-end..HEAD
git commit -m "revert: partial rollback of Batch {N}+"
```

## What rollback does NOT restore

- `MOVES.md` r2 entries
- `CONTEXT.md`, `README.md`, `AGENTS.md` r2 edits
- Agent-memory CORRECTION blocks
- The 4 r1 panel shims deleted in Batch 1 (would need separate restoration if rolling back through B1)

## Recovery if rollback itself fails

1. `git revert --abort` to back out the revert attempt
2. Verify the commit chain via `git log --oneline refactor-baseline-restructure-feature-subpackages-2026q2-r2..HEAD`
3. If chain is contaminated with feature work (it shouldn't be — the pipeline enforces clean baseline + batch-only commits), cherry-pick the contaminating commits after the revert lands

## Critical: do NOT push the revert without testing locally first

```bash
# After rollback locally:
.venv/bin/python -m pytest -q  # should report 503 passed (baseline state)
.venv/bin/python -c "import app; print('OK')"
.venv/bin/python -c "import surfaces; assert callable(surfaces.fermat_quartic); print('OK')"
.venv/bin/python -c "from panels.appearance import AppearancePanel; print('OK')"  # uses panels/__init__.py shim at HEAD (still present after partial rollback through B3+)
```

Only push after all 4 smoke tests pass.
