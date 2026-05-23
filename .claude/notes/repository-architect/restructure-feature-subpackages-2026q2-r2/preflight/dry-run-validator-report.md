# Dry-run validator report — restructure-feature-subpackages-2026q2-r2

**LibCST version:** 1.8.6
**Pydeps version:** N/A (unusable; repo dir name `algebraic-variety-cross-section` has hyphens — not a valid Python identifier; direct LibCST parse substituted per r1 lesson)
**Analysis time:** ~1.8 s wall-clock (39 .py files parsed; 0 parse errors)

---

## Summary

- Predicted new cycles: 0
- Predicted orphaned modules: 0
- Predicted broken imports (no shim): **3** (symbol-map naming mismatch: `fano_segre` vs `fano_segre_cubic`)
- conftest.py scope drift: 0 (AVC has no conftest.py; vacuously satisfied)
- Predicted pytest collection delta: **+1** (B1 removes 4 tests; B9 adds 5; net +1 vs baseline 503 → 504)
- Star-import shadow risk: 0 (zero star-imports pre- and post-restructure)
- Fan-in spikes: 0 (all predicted fan-in counts well below 20)

---

## Verdict

**YELLOW**

One category has an issue (3 broken imports from a symbol-map naming error). Each has a documented mitigation (correct the symbol-map entries). No blocking cycle, orphan, collection loss, or conftest regression is predicted. The restructure is go pending the 2-entry symbol-map correction and one PLAN prose correction.

---

## Details by category

### 1. New cycles

**Predicted: 0 new cycles.**

Graph analysis of all 39 source files and the predicted post-restructure topology:

- `panels/__init__.py` hub shim → `_qt.panels.view` — no reverse edge. `_qt/panels/view.py` only imports `icons` (via shim or canonical), never back to `panels.*`. The Batch 3 Commit 2 LibCST rewrite of `_qt/panels/*` internal cross-imports removes the only pre-existing `panels.parameter_grid_panel` reference and replaces it with `_qt.panels.parameter_grid_panel`. No cycle introduced.
- `varieties/__init__.py` → `varieties._kernels` → `numba` (stdlib only). No reverse arrow. `varieties.types` and `varieties.dispatch` import only stdlib. `varieties.dispatch` → `varieties.types` (one-way). No cycle.
- `surfaces.py` hub shim uses `importlib.import_module()` lazily (only on `__getattr__` access). `surfaces.py` has NO module-level import from `varieties.*`. `varieties.*` has NO import from `surfaces`. No mutual cycle.
- `render/worker.py` → production code only. `render/__init__.py` re-exports from `render.worker`. No cycle.
- `cross_section/clip.py` → pyvista + stdlib. `_qt/panels/view.py` → `cross_section.clip` (one-way). No cycle.

Baseline import graph had zero cycles; predicted graph has zero cycles.

### 2. Orphaned modules

**Predicted: 0.**

All new modules have documented incoming import paths:

| New module | Incoming import source |
|---|---|
| `render/worker.py` | `render_worker.py` shim (`from render import worker`) + `app.py` after B2 LibCST rewrite |
| `render/__init__.py` | Implicitly loaded when shim does `from render import worker` |
| `_qt/icons.py` | `icons.py` shim + `_qt/panels/*.py` after B3 Commit 4 LibCST rewrite |
| `_qt/styles.py` | `styles.py` shim + `_qt/panels/*.py` after B3 Commit 4 LibCST rewrite |
| `_qt/ui_helpers.py` | `ui_helpers.py` shim + `_qt/panels/*.py` after B3 Commit 4 LibCST rewrite |
| `_qt/panels/view.py` | `panels/__init__.py` hub shim (on attribute access) |
| `_qt/panels/appearance.py` | `panels/__init__.py` hub shim (on `import panels.appearance`) |
| `cross_section/clip.py` | `_qt/panels/view.py` after B4 (`from cross_section.clip import clip_to_domain`) |
| `varieties/types.py` | `varieties/__init__.py` + `varieties/dispatch.py` + 4 LibCST-rewritten files |
| `varieties/dispatch.py` | `varieties/__init__.py` + `surfaces.py` shim on-demand |
| `varieties/_kernels.py` | `varieties/__init__.py` (eager) + `varieties/k3.py` etc. + `surfaces.py` shim on-demand |
| `varieties/_marching.py` | `varieties/k3.py` (implicit pipeline) + `varieties/calabi_yau.py` etc. |
| `varieties/k3.py` | `surfaces.py` shim on-demand + any new-style caller |
| `varieties/enriques.py` | `surfaces.py` shim on-demand |
| `varieties/calabi_yau.py` | `surfaces.py` shim on-demand |
| `varieties/fano.py` | `surfaces.py` shim on-demand |
| `varieties/registry.py` | `surfaces.py` shim on-demand |
| `varieties/tooltips.py` | `surfaces.py` shim on-demand |

Note: `panels/__init__.py` (hub shim) is a package `__init__` and is excluded from orphan checking per r1 lesson. It has implicit fan-in from every `from panels.X import Y` or `import panels.X` call in `tests/test_clip_domain.py` (1 site) and `tests/test_styles_palette.py` (4 sites).

### 3. Broken imports (no shim) — THE BLOCKING ISSUE

**Predicted: 3 broken imports.** All from the same root cause: the symbol-map uses `fano_segre` and `FANO_SEGRE_PARAMS` but `surfaces.py` defines `fano_segre_cubic` and `FANO_SEGRE_CUBIC_PARAMS`.

| File | Import site | Symbol in code | Symbol in symbol-map | Status |
|---|---|---|---|---|
| `tests/test_coarse_n.py:45` | `from surfaces import fano_segre_cubic` | `fano_segre_cubic` | `fano_segre` (WRONG) | BROKEN |
| `tests/test_mesh_generators.py:29` | `from surfaces import fano_segre_cubic` | `fano_segre_cubic` | `fano_segre` (WRONG) | BROKEN |
| `tests/test_parameters_panel.py:~` | `from surfaces import FANO_SEGRE_CUBIC_PARAMS` | `FANO_SEGRE_CUBIC_PARAMS` | `FANO_SEGRE_PARAMS` (WRONG) | BROKEN |

**Root cause:** The symbol-map JSON (Batch 7, Fano entry 2) has:
```json
{"batch": 7, "operation": "varieties/fano: fano_segre", "kind": "symbol", "from": "surfaces", "to": "varieties.fano", "symbol": "fano_segre"},
{"batch": 7, "operation": "varieties/fano: FANO_SEGRE_PARAMS", "kind": "symbol", "from": "surfaces", "to": "varieties.fano", "symbol": "FANO_SEGRE_PARAMS"},
```

But the actual symbol names in `surfaces.py` are `fano_segre_cubic` (line 1371) and `FANO_SEGRE_CUBIC_PARAMS` (line 1411). The function is also used in the `VARIETIES` registry (line 1627) as `fano_segre_cubic`.

**Effect:** If the implementer builds `varieties/fano.py` with a function named `fano_segre` and the surfaces.py hub shim re-exports `fano_segre`, the three tests that do `from surfaces import fano_segre_cubic` will get `AttributeError: module 'surfaces' has no attribute 'fano_segre_cubic'` because `fano_segre_cubic` is not in `_PUBLIC_NAMES`.

**Suggested fixes for symbol-map.json:**
```json
{"batch": 7, "operation": "varieties/fano: fano_segre_cubic", "kind": "symbol", "from": "surfaces", "to": "varieties.fano", "symbol": "fano_segre_cubic"},
{"batch": 7, "operation": "varieties/fano: FANO_SEGRE_CUBIC_PARAMS", "kind": "symbol", "from": "surfaces", "to": "varieties.fano", "symbol": "FANO_SEGRE_CUBIC_PARAMS"},
```

**Suggested fix for PLAN.md §3 Batch 7 table** — update the row:
```
| `surfaces.fano_segre_cubic` + `FANO_SEGRE_CUBIC_PARAMS` | `varieties.fano.*` | symbol (each) |
```
(currently reads `fano_segre` and `FANO_SEGRE_PARAMS`)

**Also fix the hub shim template in PLAN.md §5** — `_PUBLIC_NAMES` must list `fano_segre_cubic` and `FANO_SEGRE_CUBIC_PARAMS`, not the truncated names.

### 4. conftest.py scope drift

**Predicted: 0 test files affected.**

AVC has zero `conftest.py` files at any directory level (confirmed by `find` during analysis). No fixtures exist to drift. The conftest scope drift check is vacuously satisfied and is short-circuited per the r1 lesson.

Shim files at root (`panels/__init__.py`, `render_worker.py`, `icons.py`, `styles.py`, `ui_helpers.py`) and under `panels/` are not in `tests/` and contain no `def test_` or `class Test` definitions. pytest does not collect them.

### 5. Predicted pytest collection delta

**Predicted: +1 test (503 → 504 at end of restructure).**

| Batch | Change | Running count |
|---|---|---|
| Baseline | — | 503 |
| B1 | `tests/test_panels_shims.py` deleted (4 tests) | 499 |
| B2–B8 | No test file changes | 499 |
| B9 | `tests/test_r2_shims.py` added (5 tests) | 504 |

No test files are moved into unreachable paths. All test files remain in `tests/` (flat layout unchanged). pytest collection under `tests/` is not affected by any module move.

Shim files confirmed not collected by pytest: they are in root or under source subpackages (`panels/`, etc.), which are not in pytest's configured test path.

### 6. Star-import shadow risk

**Predicted: 0 call sites.**

Baseline star-import count: 0 (confirmed by `baseline.starimports.txt` — the 3 grep matches in that file are all within `.claude/scripts/` comment strings, not production code).

Post-restructure: PLAN explicitly refuses Template 3 (star-import shims). The `_PRIVATE_NAMES` dict pattern is used instead to handle `_`-prefixed kernel names. All new `__init__.py` files use explicit named re-exports. Zero new star-imports predicted.

### 7. Fan-in spikes

**Predicted: 0 modules over threshold (>20 importers).**

Pre-restructure `surfaces.py` had the highest fan-in: 16 files. Post-restructure, `surfaces.py` becomes a thin hub shim but retains the same 16-file fan-in (all tests continue to import via `from surfaces import X` through the shim). The actual `varieties/*` modules receive new fan-in from the shim (1 importer each for dispatch/on-demand, or 1–6 direct importers for `varieties/types.py`). No module in the predicted tree approaches 20 importers.

---

## Additional analysis (per-prompt items)

### Recursive shim chain (Batch 3 `panels/__init__.py` hub → `_qt.panels.view`)

**Verdict: No recursive shim chain. Correctly one-hop.**

Post-Batch-3 path for `from panels.view import ViewPanel`:
1. `panels/__init__.py` hub shim fires `__getattr__('view')` (for `import panels.view`) or Python resolves `panels.view` as a submodule.
2. Hub shim returns `_qt.panels.view` as the target.
3. `_qt/panels/view.py` is the canonical file; it does NOT import from `panels.*` (Batch 3 Commit 2 LibCST rewrites remove the pre-existing `panels.parameter_grid_panel` cross-import and replace it with `_qt.panels.parameter_grid_panel`).

No second-hop through another shim occurs. The `panels.parameter_grid_panel` import inside `_qt/panels/parameters.py` is rewritten in Commit 2, so no two-hop shim chain exists.

**One subtlety to flag for implementer:** The current `panels/__init__.py` is a docstring-only file (not yet a hub shim). The hub shim is added in Batch 3 Commit 2. Until that commit lands, `from panels.view import ViewPanel` still resolves directly because `panels/` is still the canonical location (before the `git mv`). After `git mv panels _qt/panels` + adding the hub shim + LibCST rewrites, the chain works correctly. The commit ordering in v2 MED-4 is correctly specified.

### 8 module-kind entries for Batch 3: parent-subpackage vs submodule handling

The `rewrite-imports.py` transformer handles `panels` (the parent subpackage, kind=module) and `panels.appearance` (the submodule, kind=module) as two separate module_renames entries. The `leave_Attribute` handler uses longest-prefix-first matching to distinguish `panels.appearance.AppearancePanel` from `panels.AppearancePanel`. This is correct.

The `leave_ImportFrom` handler rewrites `from panels.appearance import X` → `from _qt.panels.appearance import X`. It also rewrites `from panels import X` → `from _qt.panels import X`. Both paths are correct.

**One risk:** `import panels.appearance` (as in `tests/test_styles_palette.py` lines 243, 280, 301, 320) is an `import` statement (not `from`). The `leave_Import` handler rewrites `import panels.appearance` to `import _qt.panels.appearance` via module_renames. HOWEVER — the PLAN explicitly does NOT rewrite these test files (tests use the hub shim, not canonical paths). The LibCST Batch 3 Commit 4 rewrite targets are `app.py` and `_qt/panels/*.py`, NOT the test files. The test files continue to use `import panels.appearance` which routes through the hub shim. This is correct as specified.

### 52 symbol-kind entries: multi-symbol `from surfaces import` handling

The `rewrite-imports.py` `symbol_renames` dict has a **last-wins collision bug** for multiple symbol entries from the same source module (`surfaces`). Lines 184–191 overwrite `symbol_renames['surfaces']` on each new entry, so only the last one is stored.

**Assessment:** This bug is NOT triggered in r2 because the PLAN does not use `rewrite-imports.py` for the symbol-kind entries. The Batches 5–8 symbol moves are applied by:
1. Manually constructing `varieties/*.py` files with the moved content.
2. Manually extending `surfaces.py`'s `_PUBLIC_NAMES` and `_PRIVATE_NAMES` hub shim dicts.
3. LibCST rewrites in Batch 5 only target files importing a single symbol from `surfaces` (`ParamSpec` only), so the last-wins issue does not fire.
4. Tests are NOT rewritten by LibCST (they rely on the hub shim).

**Latent risk:** If a future implementer runs `rewrite-imports.py --batch 7` expecting it to rewrite test files that use `from surfaces import fermat_quartic, fano_segre_cubic`, the tool will incorrectly rewrite all such imports to the last-mapped destination. Flag for Phase 4 implementer note: do NOT run `rewrite-imports.py` for Batches 5–8 symbol moves on test files.

### Threading-layer side effect (LOW-2 / §7 category 3)

**Verdict: YELLOW — documented gap, no blocking breakage.**

`varieties/__init__.py` eager `import varieties._kernels` correctly ensures that:
- Any `from varieties import X` (canonical new path) triggers the numba threading-layer config.
- Any `from surfaces import _fermat_field_kernel` (via shim) triggers `importlib.import_module('varieties._kernels')` which sets the threading layer.

Edge case (documented in PLAN §7 cat.3): `from surfaces import VARIETIES` → shim imports `varieties.registry` only, NOT `varieties._kernels`. If a caller accesses VARIETIES before any kernel, the threading layer is not set. This is NOT a test-breaking scenario (no test accesses kernels after a bare `from surfaces import VARIETIES` without first triggering a kernel import). The PLAN acknowledges this and defers to Phase 5 test-suggester.

---

## Recommended PLAN.md / symbol-map.json edits

1. **[BLOCKING] symbol-map.json Batch 7:** Change `"symbol": "fano_segre"` to `"symbol": "fano_segre_cubic"` and `"symbol": "FANO_SEGRE_PARAMS"` to `"symbol": "FANO_SEGRE_CUBIC_PARAMS"`. Update the `"operation"` strings to match. This fixes the 3 predicted broken imports.

2. **[BLOCKING] PLAN.md §3 Batch 7 table:** Update the row `| surfaces.fano_segre + FANO_SEGRE_PARAMS |` → `| surfaces.fano_segre_cubic + FANO_SEGRE_CUBIC_PARAMS |`.

3. **[BLOCKING] PLAN.md §5 hub shim `_PUBLIC_NAMES` template:** Update the fano entry to use `"fano_segre_cubic"` and `"FANO_SEGRE_CUBIC_PARAMS"` in the dict literal.

4. **[NON-BLOCKING / informational] PLAN.md §4 or §5:** Add a note to the Batch 3 Commit 2 spec warning implementer NOT to run `rewrite-imports.py --batch 7` on test files. The symbol-kind entries are for manual hub-shim construction, not for automated test-file rewriting.

5. **[NON-BLOCKING / informational] PLAN.md §3 Batch 3:** The claim "No shim is added at root `panels/`" is inaccurate in the current v2 text (line 171 of PLAN.md says this, but the v2 HIGH-1 fix explicitly adds `panels/__init__.py` as a hub shim). This is an internal inconsistency in the PLAN prose. The tree diff (§2) and shim plan (§5) are correct; only this one sentence in §3 is stale. Recommend removing or correcting it to avoid implementer confusion.
