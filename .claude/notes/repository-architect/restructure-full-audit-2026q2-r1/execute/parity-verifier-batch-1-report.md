# Parity verifier report — restructure-full-audit-2026q2-r1 batch 1

**Run at:** 2026-05-23T00:00:00Z
**Verdict:** PASS

## Check results

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Test collection diff | PASS | Count: baseline=499, post=499, delta=0. Only diff is wall-clock timing line ("2.67s" vs "0.82s") — not a regression |
| 2 | Coverage diff | INFORMATIONAL/SKIPPED | baseline.coverage.xml absent (pyvistaqt internal path issue per PREFLIGHT.md obs 2); per-file % check deferred to manual review |
| 3 | Pydeps cycle diff | INFORMATIONAL/SKIPPED | pydeps v3.0.6 cannot analyse this repo (directory name contains hyphens, not a valid Python identifier). Baseline and post produce identical empty-graph error — no new cycles introduced |
| 4 | Import-time diff | PASS | Baseline: 752,943 us, post: 802,977 us, delta: +50,034 us (+6.6%). Within ±20% tolerance |
| 5 | Shim validation | PASS | 0 shim entries for batch 1 (symbol-map is empty for batches < 4); validate-shims.py exited 0 |
| 6 | Star-imports | PASS | Sorted content identical to baseline (3 lines, all in third-party / .claude scripts). Raw diff showed line-order swap only — no new star-imports introduced |

## Regressions (if any)

None.

## Tolerable deltas (informational)

**Check 2 — coverage.xml absent at baseline:** Per PREFLIGHT.md observation 2, pyvistaqt emits an internal path error that prevents `coverage xml` from completing. This is a pre-existing condition, not introduced by batch 1. Coverage parity remains a manual review item for the full restructure.

**Check 3 — pydeps not usable on this repo:** The repo root directory name `algebraic-variety-cross-section` contains hyphens, which pydeps rejects as an invalid Python identifier. Baseline.imports.json records the identical stderr error. Cycle detection via pydeps is structurally impossible until pydeps is pointed at a valid importable package path (e.g. `pydeps app`). This does not represent a regression introduced by batch 1; it was the same state at baseline.

**Check 4 — import time +6.6%:** Well inside the ±20% tolerance. Batch 1 contained zero Python source changes; the variance is attributable to normal OS-level caching fluctuation between the two measurement runs.

**Check 6 — star-import file ordering:** `grep` returned lines in a different filesystem traversal order compared to baseline. Sorted comparison confirms zero new or removed star-import lines.

## Batch 1 scope confirmation

Batch 1 (5 commits, e980da8..79fb0e0) was zero-risk additions and stale-fact edits:
- op 1/5: added MIT LICENSE
- op 2/5: added CHANGELOG.md
- op 3/5: added `.pytest_cache/` to .gitignore
- op 4/5: fixed CONTEXT.md §12 stale statistics
- op 5/5: fixed README.md stale LOC figures

No file moves, no import rewrites, no shims, no Python source changes. All zero-delta expectations confirmed.
