# Parity verifier report — restructure-feature-subpackages-2026q2-r2 batch 1

**Run at:** 2026-05-23T00:00:00Z (approx; system date 2026-05-23)
**Verdict:** PASS

## Check results

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Test collection diff | PASS | Count: baseline=503, post=499, delta=-4 (deliberate: tests/test_panels_shims.py deleted) |
| 2 | Coverage diff | INFORMATIONAL/SKIPPED | No baseline.coverage.xml — pyvistaqt internal-path blocks coverage xml on this repo (known permanent, see lessons.md) |
| 3 | Pydeps cycle diff | INFORMATIONAL/SKIPPED | pydeps cannot analyse this repo: directory name `algebraic-variety-cross-section` contains hyphens, not a valid Python identifier. Both baseline and post produce identical empty-graph error. Known permanent tooling gap. |
| 4 | Import-time diff | PASS | Baseline: 661.2 ms, post: 700.9 ms, delta: +6.0% (within ±20% tolerance) |
| 5 | Shim validation | PASS | validate-shims.py reported "no symbol-map entries for batch 1 -- nothing to validate"; exit 0 |
| 6 | Star-imports | PASS | Unsorted diff showed a line-ordering change only (same 3 entries pre and post; sorted diff exit 0). New star-imports: 0 |

## Regressions

None.

## Check 1 detail — test collection diff

The 4 removed test IDs are all from `tests/test_panels_shims.py`, which was deliberately deleted as part of batch 1 (M+1 shim cleanup). These tests validated the r1 root-level panel shims (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py`), which were also deleted in this batch. The removal is intentional and expected; no test ID disappeared without a corresponding source deletion.

Diff summary:
```
< tests/test_panels_shims.py::test_appearance_panel_shim_emits_deprecation
< tests/test_panels_shims.py::test_view_panel_shim_emits_deprecation
< tests/test_panels_shims.py::test_parameters_panel_shim_emits_deprecation
< tests/test_panels_shims.py::test_parameter_grid_panel_shim_emits_deprecation
```
Timing line changed from "503 tests collected in 1.36s" to "499 tests collected in 1.37s" — not a regression.

## Check 4 detail — import-time diff

Baseline cumulative (from baseline.importtime.log): 661,173 µs = 661.2 ms  
Post cumulative (from /tmp/post.importtime.log): 700,882 µs = 700.9 ms  
Delta: +39.7 ms (+6.0%)  
Tolerance band: ±20% → ±132.2 ms. Well within tolerance. Normal OS cache fluctuation.

## Check 6 detail — star-imports

Unsorted diff showed line 2 in baseline and line 3 in post pointing to the same file and line:
```
.claude/scripts/repository-architect/snapshot-baseline.py:164:    print(f"  grep 'import *'            ->  {prefix}.starimports.txt")
```
This is a single entry that appears in both files at different grep-output line positions (3 entries total in each). Sorted diff confirms zero content difference. Not a new star-import.

## Tolerable deltas (informational)

- Import time +6.0% vs baseline — within tolerance, consistent with prior-batch OS cache variance patterns (see lessons.md batch 1 note: +6.6% observed with zero source changes).
- Coverage check permanently skipped until pyvistaqt upstream path issue is resolved.
- Pydeps check permanently skipped until repo directory is renamed to a valid Python identifier or `pydeps app` workaround is adopted.
