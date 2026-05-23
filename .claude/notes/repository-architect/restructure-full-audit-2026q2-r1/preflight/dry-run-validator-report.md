# Dry-run validator report — restructure-full-audit-2026q2-r1

**LibCST version:** 1.8.6
**Pydeps version:** 3.0.6
**Analysis time:** ~2.0s wall-clock (LibCST parse of 102 .py files)
**Baseline git SHA:** c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c
**Coverage baseline:** NOT PRESENT (pydeps baseline also absent due to hyphenated directory name; all graph analysis performed via LibCST direct parse — see Baseline notes)

---

## Baseline notes

`baseline.imports.json` contains only a pydeps stderr error (pydeps cannot analyze a directory named `algebraic-variety-cross-section` because hyphens are not valid Python identifiers). The import graph was therefore reconstructed from scratch via LibCST by parsing all top-level `.py` files directly. This produces an equivalent result for cycle/orphan/fan-in analysis — the graph has the same fidelity as pydeps would provide for a flat-layout project.

`baseline.coverage.xml` is not present (coverage run produced a source-not-found warning for `pyscript`; no `.xml` was emitted). Per scout-C convention this is treated as a degraded-but-non-fatal signal: YELLOW input to verdict, not RED.

---

## Summary

| Category | Count |
|---|---|
| Predicted new cycles | 0 |
| Predicted orphaned modules | 0 (1 false positive dismissed — see details) |
| Predicted broken imports (no shim) | 0 |
| conftest.py scope drift | 0 test files affected |
| Predicted pytest collection delta | 0 tests lost (+4 new tests added by Batch 4) |
| Star-import shadow risk | 0 call sites |
| Fan-in spikes (>20) | 0 modules |

---

## Verdict

**GREEN**

Zero issues in all seven categories. The one apparent orphan (`panels`) is a false positive: Python always imports a package's `__init__.py` before any submodule, so `panels/__init__.py` has implicit fan-in from every caller of `panels.appearance`, `panels.parameter_grid_panel`, `panels.parameters`, and `panels.view`. Missing coverage.xml contributes a YELLOW signal on coverage continuity only; it does not affect import-graph verdict.

---

## Details by category

### New cycles

**None predicted.**

Baseline cycle count: 0. Predicted cycle count: 0.

The restructure adds one new edge to the graph: `panels.parameters -> panels.parameter_grid_panel` (post-LibCST rewrite of the existing `from parameter_grid_panel import ParameterGridPanel` at `parameters_panel.py:31`). This edge is acyclic: `panels.parameter_grid_panel` has no imports from `panels.parameters` or any ancestor.

The shim files (`appearance_panel.py`, `parameter_grid_panel.py`, `parameters_panel.py`, `view_panel.py`) use a lazy `__getattr__` pattern per PLAN.md §5. They do not import their target at module scope; the import happens only on first attribute access. No eager import cycle is possible from the shim layer.

`panels/__init__.py` uses `__getattr__` hub routing (Template 2 per shim-templates.md). It contains no eager imports of submodules. No cycle via `panels/__init__.py`.

Predicted full graph edges after restructure:
```
app -> icons
app -> panels.appearance
app -> panels.parameters
app -> panels.view
app -> render_worker
app -> styles
app -> surfaces
icons -> styles
panels.appearance -> styles
panels.parameter_grid_panel -> parameter_grid
panels.parameter_grid_panel -> styles
panels.parameter_grid_panel -> surfaces
panels.parameter_grid_panel -> ui_helpers
panels.parameters -> panels.parameter_grid_panel
panels.parameters -> parameter_grid
panels.parameters -> surfaces
panels.parameters -> ui_helpers
parameter_grid -> surfaces
ui_helpers -> parameter_grid
ui_helpers -> styles
ui_helpers -> surfaces
```

Topology is a DAG. No cycle exists.

---

### Orphaned modules

**None (0 true orphans).**

The static graph analysis flagged `panels` (the package `__init__`) as having zero explicit incoming imports. This is a **false positive**: Python's import machinery always imports a package's `__init__.py` before any of its submodules. Since `app.py` (post-rewrite) imports `panels.appearance`, `panels.parameters`, and `panels.view`, Python will run `panels/__init__.py` on each of those three imports. Fan-in is therefore 3 (implicit, via subpackage access).

All other modules have at least one explicit importer post-restructure.

`panels.parameter_grid_panel` has fan-in of 1 (`panels.parameters`), which is the expected narrow scope for a widget-level module.

---

### Broken imports (no shim)

**None.**

All four moved modules have shims planned at their original paths per PLAN.md §5 (Batch 4). Every import of `appearance_panel`, `parameter_grid_panel`, `parameters_panel`, and `view_panel` found in the codebase is covered:

| Importer | Import statement | Coverage |
|---|---|---|
| `app.py:39` | `from appearance_panel import AppearancePanel` | Shim at `appearance_panel.py` |
| `app.py:40` | `from parameters_panel import ParametersPanel` | Shim at `parameters_panel.py` |
| `app.py:64` | `from view_panel import ViewPanel` | Shim at `view_panel.py` |
| `parameters_panel.py:31` | `from parameter_grid_panel import ParameterGridPanel` | LibCST rewrites to `panels.parameter_grid_panel` in Batch 4; shim also present for any non-rewritten caller |
| `tests/test_clip_domain.py:21` | `from view_panel import ViewPanel` | Shim at `view_panel.py` |
| `tests/test_styles_palette.py:243,280,301,320` | `import appearance_panel` (function-local, inside test bodies) | Shim at `appearance_panel.py` |

Note: `parameter_grid_panel` is NOT imported by `app.py` directly — only by `parameters_panel`. After LibCST rewrites `parameters_panel` -> `panels.parameters`, the internal import is also rewritten to `from panels.parameter_grid_panel import ParameterGridPanel`. The shim at `parameter_grid_panel.py` remains for any external caller not covered by the rewrite (there are none in the current tree).

---

### conftest.py scope drift

**None (0 test files affected).**

AVC has no project-level or test-level `conftest.py` files (confirmed: `find` returns only `.venv` site-package conftest files which are out of scope). No fixtures are shared via conftest. Test files are not moved in this restructure. Category is vacuously satisfied.

---

### Predicted pytest collection delta

**0 tests lost. +4 tests added.**

Test files are not moved in this restructure. The panel modules at their old paths become shim files that are still importable. Specifically:

- `tests/test_clip_domain.py:21` does `from view_panel import ViewPanel` at module scope. Post-restructure `view_panel.py` is a shim that re-exports `ViewPanel` via `__getattr__`. The module-level import triggers `__getattr__` at import time, which works correctly. **No collection loss.**
- `tests/test_styles_palette.py` does `import appearance_panel` inside test function bodies (4 occurrences, all at 4-space indent). These are function-local imports, not module-scope. They will hit the shim and succeed. **No collection loss.**
- All other test file references to panel module names are string literals in docstrings or comments, not import statements. **No collection impact.**

Batch 4 adds `tests/test_panels_shims.py` with 4 new test functions. Predicted collection after full restructure: **503 tests** (499 baseline + 4 new).

---

### Star-import shadow risk

**None (0 call sites).**

LibCST analysis confirmed zero `from X import *` statements in all production source files and test files. The baseline `baseline.starimports.txt` contains only matches from `.claude/scripts/` (the script source code itself contains the string `import *` in grep commands and comments) — not from production code. This is consistent with evaluator c16 PASS (no star-imports in the package).

The shim template (PLAN.md §5) explicitly states "NEVER star-imports" for the shim files. No star-import risk is introduced by the restructure.

---

### Fan-in spikes

**None (0 modules over threshold of 20).**

Predicted fan-in counts (post-restructure):

| Module | Fan-in | Importers |
|---|---|---|
| `styles` | 5 | app, icons, panels.appearance, panels.parameter_grid_panel, ui_helpers |
| `surfaces` | 5 | app, panels.parameter_grid_panel, panels.parameters, parameter_grid, ui_helpers |
| `parameter_grid` | 3 | panels.parameter_grid_panel, panels.parameters, ui_helpers |
| `ui_helpers` | 2 | panels.parameter_grid_panel, panels.parameters |
| `icons` | 1 | app |
| `render_worker` | 1 | app |
| `panels.appearance` | 1 | app |
| `panels.parameters` | 1 | app |
| `panels.view` | 1 | app |
| `panels.parameter_grid_panel` | 1 | panels.parameters |

Maximum fan-in is 5. Threshold is 20. No god-module risk.

---

## Maintenance observations (non-blocking)

These are not failures. They are noted for the test-suggester (Phase 5) and future milestones.

1. **Test guard path weakening (Batch 4, non-blocking).** `tests/test_styles_palette.py::test_no_inline_color_styles_in_panel_files` and `test_no_raw_hex_in_pyvista_color_kwargs_at_appearance_panel` read panel files at `repo_root / "appearance_panel.py"` etc. After Batch 4, those paths become shims (~10 LOC each, no Qt or hex content). The tests will still PASS (shims contain no forbidden patterns), but the guard no longer covers the moved content at `panels/*.py`. The test-suggester should propose updating these guards to check both old (shim) and new (`panels/`) paths, or to point exclusively at `panels/*.py` post-migration. This is a test-quality concern, not a correctness regression.

2. **Coverage continuity signal (YELLOW, non-blocking).** `baseline.coverage.xml` is absent. The implementer agent should produce a `coverage.xml` after Batch 4 executes and compare against the `baseline.coverage.run.log` (which shows 499 tests passing at 100%). If coverage drops post-restructure, it indicates the shims are not forwarding correctly.

3. **Cyclic-import smoke test gap (PLAN.md §7, category 10).** PLAN.md §7 already flags this: `python -c "import app"` should be run as a smoke test after each batch. The parity-verifier should add this to its checklist. The dry-run confirms no cycle exists, but a runtime smoke confirms `panels/__init__.py` and the 4 shims load cleanly under CPython's import machinery.

---

## Recommended PLAN.md / symbol-map.json edits

None required. The plan as written (v2) is structurally sound. All predicted risks are zero. The following non-blocking suggestions are for Phase 5 (test-suggester):

- Update `test_no_inline_color_styles_in_panel_files` and `test_no_raw_hex_in_pyvista_color_kwargs_at_appearance_panel` to check `panels/appearance.py`, `panels/parameters.py`, `panels/view.py`, and `panels/parameter_grid_panel.py` (not just the old shim paths) once Batch 4 is applied.
- The parity-verifier checklist for Batch 4 should include: `python -c "import app; print('OK')"` (cyclic-import smoke per PLAN.md §7 category 10).
