# PREFLIGHT.md — restructure-full-audit-2026q2-r1

**Phase 3 wall-clock:** ~7 min (baseline snapshot 2 min + dry-run-validator 5.5 min)
**Verdict:** GREEN — all 7 dry-run categories scored zero; 2 non-blocking observations
**Pipeline state:** preflight-running (will advance to preflight-complete after this artifact lands)

## Baseline (pre-restructure snapshot)

| Signal | Value |
|---|---|
| Git SHA | `c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c` (refactor-baseline-restructure-full-audit-2026q2-r1) |
| Tests collected | 499 |
| Tests passing | 499 (wall-clock 7.95s) |
| Symbols indexed | 517 top-level def/class |
| Star-imports | 3 (all in third-party / generated code, none in AVC source) |
| pydeps cycles | (see baseline.imports.json) |
| coverage.xml | ⚠️ NOT generated — pyvistaqt internal path issue ("No source for code: '<repo>/pyscript'"); per-file coverage % parity check will degrade to informational in Phase 4 |
| importtime | captured in baseline.importtime.log (~114 KB; parser will compute totals at parity time) |

## Dry-run validator results

Verdict: **GREEN**. The predicted post-restructure import graph is a clean DAG.

| # | Category | Result |
|---|---|---|
| 1 | New cycles | 0 |
| 2 | Orphans | 0 true (1 false positive dismissed — `panels/__init__.py` has implicit fan-in via every `from panels.X import Y`) |
| 3 | Broken imports | 0 — all 4 moved modules have planned shims; 6 production+test import sites verified to resolve via shim chain |
| 4 | conftest.py scope drift | 0 — AVC has no conftest.py |
| 5 | Pytest collection delta | +4 (Batch 4 adds tests/test_panels_shims.py with 4 tests); zero existing tests lost |
| 6 | Star-import shadow risk | 0 — no `from X import *` anywhere in production or tests |
| 7 | Fan-in spikes | 0 — max fan-in is 5 (`styles`, `surfaces`), well below threshold of 20 |

## Non-blocking observations to bake into Phase 4

These were surfaced by the dry-run validator as YELLOW signals — not GREEN-blocking, but worth handling proactively:

### Observation 1: inline-style guard test path weakening after Batch 4

`tests/test_styles_palette.py` contains `test_no_inline_color_styles_in_panel_files`, which currently scans 3 panel files (and 4 after Batch 3 adds parameter_grid_panel.py). After Batch 4 moves the panel files into `panels/`, the OLD paths (appearance_panel.py, view_panel.py, parameters_panel.py, parameter_grid_panel.py) become tiny `__getattr__` shims with no `setStyleSheet` calls. The guard tests will PASS trivially because they scan the shim files, not the moved source.

**Phase 4 action:** Batch 4's implementer MUST update the tuple in `test_styles_palette.py` from old flat-paths to new `panels/*` paths AS PART OF the panel move commit (NOT a separate content edit — this is the same-batch "the move requires this update" exception, narrowly scoped to the file-path strings inside the test, no logic change).

### Observation 2: missing baseline coverage.xml

Per-file coverage % parity check (rubric item 4 from scout-C verification rubric) requires a baseline XML. Phase 4 parity-verifier will report this check as `informational/skipped`, NOT FAIL — coverage parity becomes a manual review item.

## Pipeline state at Phase 3 end

- `restructure_base = c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c`
- `baseline_dir = .claude/notes/repository-architect/restructure-full-audit-2026q2-r1/preflight/`
- Git tag created: `refactor-baseline-restructure-full-audit-2026q2-r1`
- `dry_run_verdict = GREEN`
- Ready to advance to `preflight-complete` and surface GATE 3.
