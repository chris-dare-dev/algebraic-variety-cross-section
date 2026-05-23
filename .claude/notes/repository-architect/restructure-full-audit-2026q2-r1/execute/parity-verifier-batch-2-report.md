# Parity verifier report — restructure-full-audit-2026q2-r1 batch 2

**Run at:** 2026-05-23T00:00:00Z
**Verdict:** PASS

## Check results

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Test collection diff | PASS | Count: baseline=499, post=499, delta=0. Only diff was wall-clock timing line (2.67s → 0.69s). No test IDs added, removed, or path-changed. |
| 2 | Coverage diff | INFORMATIONAL/SKIPPED | baseline.coverage.xml absent (pyvistaqt internal-path issue prevents `coverage xml` from completing). Known quirk from batch 1 lessons — not a FAIL. |
| 3 | Pydeps cycle diff | INFORMATIONAL/SKIPPED | Both baseline and post produce identical empty-graph error: directory name `algebraic-variety-cross-section` is not a valid Python identifier. Known quirk from batch 1 lessons — not a FAIL. No new cycles possible. |
| 4 | Import-time diff | PASS | Baseline: 752.9 ms, post: 657.0 ms, delta: -12.7%. Within ±20% tolerance. Improvement likely OS cache warm from prior Batch 1 verification run. |
| 5 | Shim validation | PASS | Script reported "no symbol-map entries for batch 2 -- nothing to validate", exit 0. Correct — batch 2 added only AGENTS.md, CLAUDE.md symlink, and pyproject.toml; no Python module moves, no shims required. |
| 6 | Star-imports | PASS | New star-imports: 0. Post file identical to baseline (3 lines, all in .claude/scripts/, not in production package). |

## Regressions (if any)

None.

## Tolerable deltas (informational)

- **Import time -12.7%:** A 95 ms improvement vs baseline. Negative delta (faster) is within tolerance and consistent with OS disk cache being warm from the Batch 1 verification run the same day. Not a concern.
- **Coverage and pydeps checks remain SKIPPED:** Both are pre-existing environmental constraints documented in batch 1 lessons. Batch 2 added zero Python source changes so these checks carry no additional risk even while skipped.
