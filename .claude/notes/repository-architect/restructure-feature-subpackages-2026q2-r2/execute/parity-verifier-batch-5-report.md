# Parity-verifier report — restructure-feature-subpackages-2026q2-r2 batch 5

**Run at:** 2026-05-24T00:05:00Z (inline)
**Verdict:** PASS

## Mechanical checks

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Test collection | PASS | 499 collected, 0 delta vs B4 |
| 2 | Coverage XML | INFORMATIONAL/SKIPPED | persistent |
| 3 | Pydeps cycles | INFORMATIONAL/SKIPPED | persistent |
| 4 | Import-time | PASS (informal) | `import app` succeeds; varieties/ subpackage import path now exists |
| 5 | Shim validation | PASS | NO shims added in B5 — used the RE-EXPORT pattern instead (surfaces.py adds `from varieties.types import ParamSpec, Surface` + `from varieties.dispatch import …` at top). All existing `from surfaces import ParamSpec` paths continue to work transparently with NO deprecation warning (the warning fires in B8 when surfaces.py becomes a full hub shim). |
| 6 | Star-imports | PASS | 3 pre-existing, unchanged |

## Notes

Single clean commit (45fd9b8). 5 symbols moved: ParamSpec, Surface, dispatch_mode, should_render_on_drag, FAST_RENDER_THRESHOLD_MS — all to varieties/types or varieties/dispatch.

surfaces.py shrunk by 125 LOC (1811 → 1686). 4 callers continue to use the legacy `from surfaces import ParamSpec` path (parameter_grid.py, _qt/ui_helpers.py, _qt/panels/parameters.py, _qt/panels/parameter_grid_panel.py); app.py also continues with `from surfaces import ... Surface, dispatch_mode, ...`. All work transparently via re-export.

**No LibCST rewrite needed** — the re-export approach is cleaner for symbol-only extractions where the original module still exists and is still authoritative for the rest of its content.

Tag refactor-r2-batch5-end at 45fd9b8. Tree at 5/9 batches landed; 499 tests passing.
