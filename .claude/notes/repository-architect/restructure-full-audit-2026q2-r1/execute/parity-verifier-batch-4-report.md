# Parity verifier report — restructure-full-audit-2026q2-r1 batch 4

**Run at:** 2026-05-23T00:00:00Z (approx)
**Verdict:** DEGRADED

## Check results

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Test collection diff | PASS | Count: baseline=499, post=503, delta=+4 (all 4 are new tests/test_panels_shims.py; zero drops) |
| 2 | Coverage diff | INFORMATIONAL/SKIPPED | baseline.coverage.xml absent — pyvistaqt internal-path issue prevents coverage xml (known, all batches) |
| 3 | Pydeps cycle diff | INFORMATIONAL/SKIPPED | pydeps produces identical empty-graph error: repo name 'algebraic-variety-cross-section' is not a valid Python module name (known, all batches) |
| 4 | Import-time diff | PASS | Baseline: 752.9 ms (752,943 µs), post warm-cache run3: 693.7 ms (693,714 µs), delta: -7.9% (within ±20%) |
| 5 | Shim validation | DEGRADED | validate-shims.py exits 2 (4 FAIL) — script uses `import <module>` for kind=module entries, but shims use __getattr__ (Template 2) which only fires on attribute access, not bare import. All 4 pytest shim tests (tests/test_panels_shims.py) PASS — shims are functionally correct. Script is mismatched to this shim pattern. |
| 6 | Star-imports | PASS | New star-imports: 0. Diff shows only path prefix (relative→absolute) and line-ordering change — same 3 constant-string occurrences in .claude/scripts files, no new star-imports in package source. |

## Special Batch 4 checks

| Check | Result | Detail |
|---|---|---|
| `python -c "import app; print('OK')"` | PASS | Prints OK — no cyclic-import error |
| MOVES.md at repo root | PASS | Exists with all 4 batch-4 entries, move SHAs, import guide, and file-path reference guide |
| panels/ subpackage | PASS | __init__.py + 4 files: appearance.py, parameter_grid_panel.py, parameters.py, view.py |

## Regressions

None. No test IDs disappeared. No new cycles. No new star-imports. `import app` clean.

## Degradations (informational)

### Check 5 — validate-shims.py script/shim pattern mismatch

**What happened:** validate-shims.py reports 4 FAILs because for `kind=module` symbol-map entries it runs `import <module>` under `-W error::DeprecationWarning`. The shims in this batch use Python 3 `__getattr__` (Template 2), which only fires when a *symbol is accessed* on the module — NOT on bare `import module`. Bare module import exits 0 with no warning.

**Why this is not a functional regression:** All 4 pytest tests in tests/test_panels_shims.py exercise the shims correctly via `from <module> import <Symbol>` and assert DeprecationWarning with the new panels.* path. All 4 pass.

**Suggested fix direction (for validate-shims.py, not shim files):** For symbol-map entries with `kind=module` and `symbol=null`, the validator should test `from <old_mod> import <primary_symbol>` rather than `import <old_mod>`. The primary symbol could be inferred from `to` (e.g. `panels.appearance` → try to import the public class name) or the symbol-map could be extended to include a `probe_symbol` field for `__getattr__`-style shims. This is a tooling gap, not a parity failure.

### Import-time

-7.9% improvement (752.9 ms → 693.7 ms, warm cache). Delta inside tolerance, direction is positive. Likely warm OS disk cache from same-day batch runs.

### Test collection timing

499→503 tests; collection time dropped from 2.67s to 1.45s (warm cache). Not a regression.

### panels/ naming clarification

The batch description said "names unchanged" but 3 of 4 moved files had `_panel` suffix stripped (appearance_panel→appearance, view_panel→view, parameters_panel→parameters). Only parameter_grid_panel.py retained its name. This matches MOVES.md and symbol-map.json (v2), so there is no inconsistency in the actual implementation — the batch description was imprecise.
