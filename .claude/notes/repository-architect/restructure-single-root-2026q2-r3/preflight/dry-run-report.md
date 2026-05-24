# Dry-run validator report — restructure-single-root-2026q2-r3

**LibCST version:** 1.8.6
**pydeps:** unusable (hyphenated directory name; LibCST AST walk substituted — confirmed from r1/r2 lessons)
**Analysis time:** 2026-05-24T13:58:46Z
**Baseline SHA:** c1dcf89 · 506 tests collected

---

## Summary

| Category | Count |
|---|---|
| Predicted new cycles | 0 |
| Predicted orphaned modules | 0 |
| Predicted broken imports — no shim | **34 call-sites across 6 test files** |
| conftest.py scope drift | 0 (no conftest.py exists — vacuously satisfied) |
| Predicted pytest collection delta | **-115 tests lost at B4** (all 499 remaining tests that import from unmapped symbols would fail at collect-time) |
| Star-import shadow risk | 0 |
| Fan-in spikes (>20 importers) | 0 |

## Verdict

**RED**

B4 as written will cause catastrophic test collection failures. The symbol-map.json has 17 wrong/missing symbol names that do not match the actual surface exports or varieties submodule exports. Additionally, the `render/worker.py → PySide6` import makes the proposed B5 import-linter contract `render imports nothing from PySide6` unprovable at HEAD. Two independent fix-first items must be resolved before B4 can proceed safely.

---

## Details by category

### 1. Predicted post-r3 import graph

**New cycles:** None predicted. The varieties subpackage has no imports from app, surfaces, _qt, or panels. post-r3 cross-package import direction is clean:

```
app → varieties.*, _qt.*, render.*, cross_section.*
_qt → varieties.types, _qt.styles, _qt.icons, _qt.ui_helpers
render → varieties.*  (via Surface/generator callsites)
cross_section → (numpy, pyvista only)
varieties → (numpy, pyvista, numba, skimage only)
```

**Orphaned modules:** None. `_qt/__init__.py` is docstring-only; treated as auto-imported by submodule fan-in (r1/r2 lesson applies). `varieties/__init__.py` has fan-in from `app.py`. `render/__init__.py` and `cross_section/__init__.py` have fan-in from `app.py`. The new `_qt/parameter_grid_math.py` (B2) immediately acquires fan-in from 4 rewritten callers.

**Cross-package import counts post-r3 (predicted):**

| Edge | Importer count |
|---|---|
| → varieties.types | 7 (app, _qt/ui_helpers, _qt/panels/parameter_grid_panel, _qt/panels/parameters, _qt/parameter_grid_math, varieties/k3..fano via internal) |
| → varieties.registry | 2 (app, varieties/__init__) |
| → varieties.dispatch | 2 (app, varieties/__init__) |
| → varieties.{k3,enriques,calabi_yau,fano} | 1-2 each (app or varieties/registry) |
| → _qt.* | app only |
| → render.worker | app only |
| → cross_section.clip | app only |

No module predicted to exceed fan-in of 20.

---

### 2. conftest.py scope drift

Zero. `find . -name conftest.py ! -path "./.venv/*"` returns empty. Vacuously satisfied. Short-circuit applied per r1/r2 lesson.

---

### 3. pytest --collect-only delta prediction

**B1 (tooling fix):** 506 → **506** (no test files touched) ✓

**B2 (parameter_grid move + Protocol add):** 506 → **506** (4 callers rewritten in-place, no test additions/removals) ✓

**B3 (shim deletes):** 506 → **499** (test_r2_shims.py deleted: 7 tests confirmed via AST count) ✓
PLAN §9 arithmetic confirmed correct.

**B4 (surfaces.py retirement):** 499 → **COLLECTION ERROR**

The PLAN predicts 499. The dry-run predicts collection-time failures. The 34 unmapped/misnamed symbol call-sites span 6 test files. When surfaces.py is deleted and these files attempt `from surfaces import <unmapped_symbol>`, pytest raises `ImportError` during collection for the entire file — all tests in that file are lost:

| File | Affected tests | Unmapped symbols |
|---|---|---|
| tests/test_numba_field_kernels.py | 23 | `_dwork_field_kernel`, `_enriques_fig1_field_kernel` thru `_enriques_fig4_field_kernel`, `_klein_cubic_field_kernel`, `_segre_cubic_field_kernel`, `_sextic_double_solid_field_kernel`, `_two_quadrics_field_kernel` (9 kernels) |
| tests/test_mesh_generators.py | 30 | `enriques_figure_4`, `calabi_yau_cubic`, `calabi_yau_asymmetric`, `calabi_yau_dwork`, `fano_klein_cubic`, `fano_sextic_double_solid` |
| tests/test_coarse_n.py | 17 | same 6 functions as test_mesh_generators |
| tests/test_parameters_panel.py | 4* | `FERMAT_PARAMS`, `KUMMER_PARAMS`, `ENRIQUES_FIGURE_4_PARAMS`, `CALABI_YAU_CUBIC_PARAMS`, `CALABI_YAU_ASYMMETRIC_PARAMS`, `CALABI_YAU_DWORK_PARAMS`, `FANO_KLEIN_CUBIC_PARAMS`, `FANO_SEXTIC_DOUBLE_SOLID_PARAMS` |
| tests/test_parameter_grid.py | 31* | `FERMAT_PARAMS`, `KUMMER_PARAMS` |
| tests/test_typical_ms.py | 10 | `calabi_yau_asymmetric`, `calabi_yau_cubic` |

*test_parameters_panel.py and test_parameter_grid.py import these at module scope — entire file fails to collect.

Note: tests/test_styles_palette.py imports `VARIETIES` and `SUBTYPE_TOOLTIPS` from surfaces inside function bodies (lines 214, 610, 1252). These symbols ARE correctly mapped in symbol-map.json. However the imports are local-scope; LibCST WILL visit them. These 3 sites are NOT a problem — included here for completeness only.

Similarly, tests/test_enriques_hq_smoothing.py:224 (`from surfaces import VARIETIES` inside a function) IS mapped and WILL be rewritten. Not a problem.

**B5 (lock-in + test_import_smoke.py):** If B4 above were clean, 499 → **504** (5 new parametrize entries). PLAN §9 confirmed correct. But this count is unreachable until B4 is fixed.

---

### 4. Broken imports (no shim) — Symbol Map Completeness Failures

**Category A — Wrong names in symbol-map B4 (symbol-map entry exists but name does not match actual code):**

| symbol-map "old" | symbol-map "new" | Actual name in surfaces.py | Actual name in varieties/* |
|---|---|---|---|
| `surfaces.FERMAT_QUARTIC_PARAMS` | `varieties.k3.FERMAT_QUARTIC_PARAMS` | `FERMAT_PARAMS` | `varieties/k3.py: FERMAT_PARAMS` |
| `surfaces.KUMMER_SURFACE_PARAMS` | `varieties.k3.KUMMER_SURFACE_PARAMS` | `KUMMER_PARAMS` | `varieties/k3.py: KUMMER_PARAMS` |
| `surfaces.calabi_yau_quartic_pencil` | `varieties.calabi_yau.calabi_yau_quartic_pencil` | `calabi_yau_cubic` | `varieties/calabi_yau.py: calabi_yau_cubic` |
| `surfaces.calabi_yau_dwork_pencil` | `varieties.calabi_yau.calabi_yau_dwork_pencil` | `calabi_yau_dwork` | `varieties/calabi_yau.py: calabi_yau_dwork` |
| `surfaces.CALABI_YAU_QUARTIC_PENCIL_PARAMS` | `varieties.calabi_yau.CALABI_YAU_QUARTIC_PENCIL_PARAMS` | `CALABI_YAU_CUBIC_PARAMS` | `varieties/calabi_yau.py: CALABI_YAU_CUBIC_PARAMS` |
| `surfaces.CALABI_YAU_DWORK_PENCIL_PARAMS` | `varieties.calabi_yau.CALABI_YAU_DWORK_PENCIL_PARAMS` | `CALABI_YAU_DWORK_PARAMS` | `varieties/calabi_yau.py: CALABI_YAU_DWORK_PARAMS` |
| `surfaces.fano_grassmannian` | `varieties.fano.fano_grassmannian` | `fano_sextic_double_solid` | `varieties/fano.py: fano_sextic_double_solid` |
| `surfaces.FANO_GRASSMANNIAN_PARAMS` | `varieties.fano.FANO_GRASSMANNIAN_PARAMS` | `FANO_SEXTIC_DOUBLE_SOLID_PARAMS` | `varieties/fano.py: FANO_SEXTIC_DOUBLE_SOLID_PARAMS` |
| `surfaces._enriques_field_kernel` | `varieties._kernels._enriques_field_kernel` | `_enriques_fig1_field_kernel` | `varieties/_kernels.py: _enriques_fig1_field_kernel` |
| `surfaces._enriques2_field_kernel` | `varieties._kernels._enriques2_field_kernel` | `_enriques_fig2_field_kernel` | `varieties/_kernels.py: _enriques_fig2_field_kernel` |
| `surfaces._enriques3_field_kernel` | `varieties._kernels._enriques3_field_kernel` | `_enriques_fig3_field_kernel` | `varieties/_kernels.py: _enriques_fig3_field_kernel` |
| `surfaces._calabi_yau_quintic_field_kernel` | `varieties._kernels._calabi_yau_quintic_field_kernel` | does not exist | no match in _kernels.py |
| `surfaces._calabi_yau_quartic_pencil_field_kernel` | `varieties._kernels._calabi_yau_quartic_pencil_field_kernel` | does not exist | no match in _kernels.py |
| `surfaces._calabi_yau_dwork_pencil_field_kernel` | `varieties._kernels._calabi_yau_dwork_pencil_field_kernel` | does not exist | no match in _kernels.py |
| `surfaces._fano_segre_cubic_field_kernel` | `varieties._kernels._fano_segre_cubic_field_kernel` | `_segre_cubic_field_kernel` | `varieties/_kernels.py: _segre_cubic_field_kernel` |
| `surfaces._fano_two_quadrics_field_kernel` | `varieties._kernels._fano_two_quadrics_field_kernel` | `_two_quadrics_field_kernel` | `varieties/_kernels.py: _two_quadrics_field_kernel` |
| `surfaces._fano_grassmannian_field_kernel` | `varieties._kernels._fano_grassmannian_field_kernel` | `_sextic_double_solid_field_kernel` | `varieties/_kernels.py: _sextic_double_solid_field_kernel` |

Total Category A mismatches: **17**

**Category B — Missing entries in symbol-map B4 (symbols imported from surfaces by test files, no mapping at all):**

The following symbols are actively imported by test files at module-scope from `surfaces` but have zero entry in symbol-map.json B4:

| Symbol | Imported by | Target (where it actually lives) |
|---|---|---|
| `FERMAT_PARAMS` | test_parameter_grid.py:19, test_parameters_panel.py:21 | `varieties.k3.FERMAT_PARAMS` |
| `KUMMER_PARAMS` | test_parameter_grid.py:19, test_parameters_panel.py:21 | `varieties.k3.KUMMER_PARAMS` |
| `enriques_figure_4` | test_mesh_generators.py:17, test_coarse_n.py:32 | `varieties.enriques.enriques_figure_4` |
| `ENRIQUES_FIGURE_4_PARAMS` | test_parameters_panel.py:21 | `varieties.enriques.ENRIQUES_FIGURE_4_PARAMS` |
| `calabi_yau_cubic` | test_mesh_generators.py:17, test_coarse_n.py:32, test_typical_ms.py:24 | `varieties.calabi_yau.calabi_yau_cubic` |
| `calabi_yau_asymmetric` | test_mesh_generators.py:17, test_coarse_n.py:32, test_typical_ms.py:24 | `varieties.calabi_yau.calabi_yau_asymmetric` |
| `calabi_yau_dwork` | test_mesh_generators.py:17, test_coarse_n.py:32 | `varieties.calabi_yau.calabi_yau_dwork` |
| `CALABI_YAU_CUBIC_PARAMS` | test_parameters_panel.py:21 | `varieties.calabi_yau.CALABI_YAU_CUBIC_PARAMS` |
| `CALABI_YAU_ASYMMETRIC_PARAMS` | test_parameters_panel.py:21 | `varieties.calabi_yau.CALABI_YAU_ASYMMETRIC_PARAMS` |
| `CALABI_YAU_DWORK_PARAMS` | test_parameters_panel.py:21 | `varieties.calabi_yau.CALABI_YAU_DWORK_PARAMS` |
| `fano_klein_cubic` | test_mesh_generators.py:17, test_coarse_n.py:32 | `varieties.fano.fano_klein_cubic` |
| `fano_sextic_double_solid` | test_mesh_generators.py:17, test_coarse_n.py:32 | `varieties.fano.fano_sextic_double_solid` |
| `FANO_KLEIN_CUBIC_PARAMS` | test_parameters_panel.py:21 | `varieties.fano.FANO_KLEIN_CUBIC_PARAMS` |
| `FANO_SEXTIC_DOUBLE_SOLID_PARAMS` | test_parameters_panel.py:21 | `varieties.fano.FANO_SEXTIC_DOUBLE_SOLID_PARAMS` |
| `_dwork_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._dwork_field_kernel` |
| `_enriques_fig1_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._enriques_fig1_field_kernel` |
| `_enriques_fig2_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._enriques_fig2_field_kernel` |
| `_enriques_fig3_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._enriques_fig3_field_kernel` |
| `_enriques_fig4_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._enriques_fig4_field_kernel` |
| `_klein_cubic_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._klein_cubic_field_kernel` |
| `_segre_cubic_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._segre_cubic_field_kernel` |
| `_sextic_double_solid_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._sextic_double_solid_field_kernel` |
| `_two_quadrics_field_kernel` | test_numba_field_kernels.py:53 | `varieties._kernels._two_quadrics_field_kernel` |

Total Category B missing: **23 distinct symbols, 34 unique import call-sites**

**Root cause:** The symbol-map was drafted from an earlier version of the code (possibly pre-r2 naming) where functions had different names (`calabi_yau_quartic_pencil`, `calabi_yau_dwork_pencil`, `fano_grassmannian`, `_enriques_field_kernel`, etc.) and where kernel function names omitted the `_fig<N>_` and `_fano_`/`_segre_` prefixes. The r2 extraction renamed these for clarity. The r3 symbol-map was not updated to reflect the r2 canonical names.

**Bare import sites — symbol-map correctly flags but understates scope:**

The symbol-map notes 2 bare `import surfaces` sites:
- `tests/test_status_bar_bbox.py:33` — uses `surfaces.fermat_quartic()`, `surfaces.kummer_surface()`, `surfaces.calabi_yau_quintic()`, `surfaces.calabi_yau_asymmetric()` (all correctly mapped when interpreted as `from varieties.X import Y`)
- `tests/test_enriques_hq_smoothing.py:31` — uses `surfaces.enriques_figure_1`, `surfaces.enriques_figure_2`, `surfaces._marching_cubes_to_polydata` (all correctly mapped)

Both require manual refactor. Correct, as noted in symbol-map. Both are achievable with straightforward per-symbol rewrites.

---

### 5. Bare `import surfaces` validation

Confirmed: both files verified by AST analysis.

`tests/test_status_bar_bbox.py:33` — `import surfaces` at module level, used as attribute access at:
- line 65: `surfaces.fermat_quartic()` → rewrite to `from varieties.k3 import fermat_quartic`
- line 80: `surfaces.fermat_quartic()` → same
- line 97: `surfaces.kummer_surface()` → `from varieties.k3 import kummer_surface`
- line 117: `surfaces.calabi_yau_quintic()` → `from varieties.calabi_yau import calabi_yau_quintic`
- line 149: `surfaces.calabi_yau_asymmetric()` → `from varieties.calabi_yau import calabi_yau_asymmetric`
- line 172: `surfaces.kummer_surface(...)` → same as above

`tests/test_enriques_hq_smoothing.py:31` — `import surfaces` at module level, used as attribute access at:
- line 37: `surfaces.enriques_figure_1` → `from varieties.enriques import enriques_figure_1`
- line 51: `surfaces.enriques_figure_2` → `from varieties.enriques import enriques_figure_2`
- line 63: `surfaces._marching_cubes_to_polydata` → `from varieties._marching import _marching_cubes_to_polydata`
- line 84: `surfaces.enriques_figure_3` → `from varieties.enriques import enriques_figure_3`
- line 95: `surfaces.enriques_figure_4` → `from varieties.enriques import enriques_figure_4` (NOTE: enriques_figure_4 is MISSING from symbol-map B4!)
- lines 106, 113, 133-134: `surfaces.enriques_figure_1/2` calls

**Additional bare import site:** No others found beyond the 2 flagged by symbol-map. The full scan found 17 files with `from surfaces import ...` (all covered) and exactly 2 bare `import surfaces` files (confirmed).

---

### 6. rewrite-imports.py B1-fix simulation

**Current (BROKEN) behavior** vs **PROPOSED (FIXED) behavior:**

**Issue A — JSON schema mismatch (BLOCKING):**

The existing `rewrite-imports.py` expects a flat JSON array:
```json
[{"batch": 4, "kind": "module", "from": "surfaces", "to": "varieties.types", "symbol": "ParamSpec"}, ...]
```

The r3 `symbol-map.json` uses schema_version 1.1 nested structure:
```json
{"batches": {"B4": {"moves": [{"old": "surfaces.ParamSpec", "new": "varieties.types.ParamSpec"}, ...]}}}
```

**These schemas are incompatible.** B1 must also update the codemod's JSON parser to handle `schema_version: "1.1"` batches format, or the codemod will exit on `"no symbol-map entries for batch 4"` with zero rewrites performed.

**Issue B — last-wins `symbol_renames` dict:**

Current code builds `symbol_renames[old_module] = (new_module, symbol)`. When multiple symbols from the same source module (e.g., all 45+ entries are `from "surfaces"`) are processed, each overwrites the previous. The final dict has exactly one entry: `{"surfaces": (last_new_module, last_symbol)}`. Every `from surfaces import X, Y` is rewritten to point at the LAST module in the batch. This is the r2 execution-critic MEDIUM risk confirmed.

The proposed fix (multi-alias `AddImportsVisitor`/`RemoveImportsVisitor` pattern) from refactor-patterns §2 correctly handles this: each symbol gets its own targeted import injection, not a wholesale module rename.

**Issue C — .claude/ not excluded from walker:**

Current code at line 200-205 excludes only `.venv/` and `.git/`. The `.claude/scripts/`, `.claude/notes/` directories contain Python files (scripts) that import from `surfaces` in comments and string literals. The codemod should not touch these. B1 must add exclusions per symbol-map exclusions block.

**Four-pattern scratch test per PLAN §9 B1 checklist:**

| Pattern | Current behavior | Fixed behavior |
|---|---|---|
| `import surfaces` | Issues `import _qt.parameter_grid_math` (wrong; last-wins + module rename collision) | Flag for manual review (bare module form marked null in symbol-map) |
| `from surfaces import Surface` | Rewrites to `from <last_module> import Surface` (wrong — last-wins) | `from varieties.types import Surface` ✓ |
| `from surfaces import Surface, VARIETIES` | Rewrites both aliases to `from <last_module> import ...` (wrong) | Add `from varieties.types import Surface` + `from varieties.registry import VARIETIES`, remove old import ✓ |
| `surfaces.Surface` attribute access | `leave_Attribute` may match `.surfaces.` anywhere in a chain (wrong — no QualifiedNameProvider) | `QualifiedNameProvider.has_name()` resolves to full qualified name before rewriting ✓ |

---

### 7. import-linter contract dry-run

PLAN B5 proposes these contracts (predicted against HEAD = c1dcf89):

**Contract 1: `varieties` imports nothing from `app`, `surfaces`, `_qt`, `panels`**
Result: **PASS** — all varieties/* files import only numpy, pyvista, numba, skimage, and intra-varieties. Zero violations at HEAD.

**Contract 2: `cross_section` imports nothing from `PySide6`, `_qt`**
Result: **PASS** — `cross_section/clip.py` imports only numpy and pyvista. Zero violations at HEAD.

**Contract 3: `render` imports nothing from `PySide6`, `_qt`, `surfaces`**
Result: **FAIL** — `render/worker.py:39` has:
```python
from PySide6.QtCore import QObject, QRunnable, Signal
```
This is a functional dependency: `MeshWorker` inherits from `QRunnable`, `WorkerSignals` uses `Signal`. The render layer is structurally Qt-coupled. The proposed contract is **incorrect as written** — it cannot pass at HEAD or post-r3 without refactoring `render/worker.py` to remove PySide6 dependency, which is not in scope for r3.

**Resolution options (for PLAN amendment):**
- Option A (preferred): Remove the `render` forbidden contract from B5. The render/Qt coupling is intentional and pre-existing. Import-linter should only enforce the `varieties` (pure-math) and `cross_section` contracts.
- Option B: Rewrite `render/worker.py` to accept a signal factory injected from `app.py`, removing the direct PySide6 import — out of scope for r3.

**Summary:** 2 contracts pass, 1 contract fails with no mitigation in PLAN.

---

### 8. Symbol-map completeness against baseline.symbols.json

Cross-referencing `baseline.symbols.json` for symbols in the `surfaces.py` namespace against symbol-map.json B4:

**surfaces.py currently exports (via re-export from varieties/*):** 55 symbols (confirmed by AST analysis of surfaces.py)

**Symbols in baseline.symbols.json that have NO B4 mapping:**

The following symbols defined at `surfaces.py:...` appear in `baseline.symbols.json` and are absent from symbol-map.json B4. When surfaces.py is deleted they become orphaned references:

Note: `baseline.symbols.json` records function/class definitions at their canonical location (already in `varieties/*`) and does NOT separately list them at `surfaces.py`. The shim has no definitions, only re-exports. Therefore the symbols.json gap is expressed as: which re-exported names in `surfaces.py` are NOT mapped in symbol-map B4?

Unmapped re-exports that appear in import sites (from analysis above):
1. `FERMAT_PARAMS` — imported by 2 test files, no B4 map
2. `KUMMER_PARAMS` — imported by 2 test files, no B4 map
3. `enriques_figure_4` — imported by 2 test files, no B4 map
4. `ENRIQUES_FIGURE_4_PARAMS` — imported by 1 test file, no B4 map
5. `calabi_yau_cubic` — imported by 3 test files, no B4 map
6. `calabi_yau_asymmetric` — imported by 3 test files, no B4 map
7. `calabi_yau_dwork` — imported by 2 test files, no B4 map
8. `CALABI_YAU_CUBIC_PARAMS` — imported by 1 test file, no B4 map
9. `CALABI_YAU_ASYMMETRIC_PARAMS` — imported by 1 test file, no B4 map
10. `CALABI_YAU_DWORK_PARAMS` — imported by 1 test file, no B4 map
11. `fano_klein_cubic` — imported by 2 test files, no B4 map
12. `fano_sextic_double_solid` — imported by 2 test files, no B4 map
13. `FANO_KLEIN_CUBIC_PARAMS` — imported by 1 test file, no B4 map
14. `FANO_SEXTIC_DOUBLE_SOLID_PARAMS` — imported by 1 test file, no B4 map
15. `_dwork_field_kernel` — imported by 1 test file, no B4 map
16. `_enriques_fig1_field_kernel` — imported by 1 test file, no B4 map
17. `_enriques_fig2_field_kernel` — imported by 1 test file, no B4 map
18. `_enriques_fig3_field_kernel` — imported by 1 test file, no B4 map
19. `_enriques_fig4_field_kernel` — imported by 1 test file, no B4 map
20. `_klein_cubic_field_kernel` — imported by 1 test file, no B4 map
21. `_segre_cubic_field_kernel` — imported by 1 test file, no B4 map
22. `_sextic_double_solid_field_kernel` — imported by 1 test file, no B4 map
23. `_two_quadrics_field_kernel` — imported by 1 test file, no B4 map

Additionally, symbol-map B4 maps symbols that do NOT exist in surfaces.py or varieties/* (phantom symbols):
- `surfaces.calabi_yau_quartic_pencil` (actual: `calabi_yau_cubic`)
- `surfaces.calabi_yau_dwork_pencil` (actual: `calabi_yau_dwork`)
- `surfaces.CALABI_YAU_QUARTIC_PENCIL_PARAMS` (actual: `CALABI_YAU_CUBIC_PARAMS`)
- `surfaces.CALABI_YAU_DWORK_PENCIL_PARAMS` (actual: `CALABI_YAU_DWORK_PARAMS`)
- `surfaces.fano_grassmannian` (actual: `fano_sextic_double_solid`)
- `surfaces.FANO_GRASSMANNIAN_PARAMS` (actual: `FANO_SEXTIC_DOUBLE_SOLID_PARAMS`)
- `surfaces.FERMAT_QUARTIC_PARAMS` (actual: `FERMAT_PARAMS`)
- `surfaces.KUMMER_SURFACE_PARAMS` (actual: `KUMMER_PARAMS`)
- `surfaces._enriques_field_kernel` (actual: `_enriques_fig1_field_kernel`)
- `surfaces._enriques2_field_kernel` (actual: `_enriques_fig2_field_kernel`)
- `surfaces._enriques3_field_kernel` (actual: `_enriques_fig3_field_kernel`)
- `surfaces._calabi_yau_quintic_field_kernel` (does not exist in _kernels.py)
- `surfaces._calabi_yau_quartic_pencil_field_kernel` (does not exist)
- `surfaces._calabi_yau_dwork_pencil_field_kernel` (does not exist)
- `surfaces._fano_segre_cubic_field_kernel` (actual: `_segre_cubic_field_kernel`)
- `surfaces._fano_two_quadrics_field_kernel` (actual: `_two_quadrics_field_kernel`)
- `surfaces._fano_grassmannian_field_kernel` (actual: `_sextic_double_solid_field_kernel`)

**Conclusion:** The symbol-map was drafted from an earlier naming scheme (possibly the pre-r2 surfaces.py god-module naming) and was not updated to reflect the r2 rename decisions. The impact on the `-W error::DeprecationWarning` inter-commit gate: the gate would FAIL because these symbols have no mapping and the codemod would not rewrite them, leaving live callers through the shim.

---

### 9. Import-time delta estimate

Baseline (`python -Ximporttime -c "import app"` captured in baseline.importtime.log):
- `surfaces` self-time: 573µs, cumulative: 154,909µs
- `parameter_grid` self-time: 410µs

Post-r3 prediction:
- Deleting `surfaces.py` eliminates one module load + `numba.config` import (numba was 28,000+ µs in the chain but `varieties._kernels` preserves the THREADING_LAYER assignment — no behavioral change, just one fewer Python module file to load).
- Deleting 5 shims (icons.py, styles.py, ui_helpers.py, render_worker.py, panels/__init__.py): each was ~100-400µs import time. Net removal: ~1,100µs.
- B2 move of `parameter_grid` to `_qt/parameter_grid_math.py`: same 362 LOC, functionally identical import cost (~410µs). The module name change does not affect cost.
- The new `VarietyGenerator` Protocol in `varieties/types.py` (+18 LOC, adds `typing.runtime_checkable` usage): <20µs additive.
- `tests/test_import_smoke.py` B5 addition: each of the 5 parametrize entries runs a subprocess. Subprocess startup on macOS Apple Silicon ≈ 100-300ms per invocation. **5 subprocess tests add ~0.5-1.5 seconds to the test-suite wall-clock time.** This is an expected and acceptable increase (smoke-test nature). It does NOT increase in-process import time.

**Predicted import-time delta:** approximately **-1,500µs** self-time removed from the import chain (shims + hub eliminated), or roughly **-1%** of the 154,909µs total cumulative. Well within the ±20% bound. No regression predicted.

---

## Recommended PLAN.md / symbol-map.json edits (FIX-FIRST items)

### FIX-FIRST-1 (BLOCKING — RED): Rebuild symbol-map.json B4 with correct symbol names

Replace all 17 phantom/misnamed entries. Corrected mapping table:

**K3 family:**
- `surfaces.FERMAT_QUARTIC_PARAMS` → delete entry; add `{"old": "surfaces.FERMAT_PARAMS", "new": "varieties.k3.FERMAT_PARAMS"}`
- `surfaces.KUMMER_SURFACE_PARAMS` → delete entry; add `{"old": "surfaces.KUMMER_PARAMS", "new": "varieties.k3.KUMMER_PARAMS"}`

**Enriques family — add missing entries:**
- add `{"old": "surfaces.enriques_figure_4", "new": "varieties.enriques.enriques_figure_4"}`
- add `{"old": "surfaces.ENRIQUES_FIGURE_4_PARAMS", "new": "varieties.enriques.ENRIQUES_FIGURE_4_PARAMS"}`

**Calabi-Yau family — rename:**
- `surfaces.calabi_yau_quartic_pencil` → `{"old": "surfaces.calabi_yau_cubic", "new": "varieties.calabi_yau.calabi_yau_cubic"}`
- `surfaces.calabi_yau_dwork_pencil` → `{"old": "surfaces.calabi_yau_dwork", "new": "varieties.calabi_yau.calabi_yau_dwork"}`
- `surfaces.CALABI_YAU_QUARTIC_PENCIL_PARAMS` → `{"old": "surfaces.CALABI_YAU_CUBIC_PARAMS", "new": "varieties.calabi_yau.CALABI_YAU_CUBIC_PARAMS"}`
- `surfaces.CALABI_YAU_DWORK_PENCIL_PARAMS` → `{"old": "surfaces.CALABI_YAU_DWORK_PARAMS", "new": "varieties.calabi_yau.CALABI_YAU_DWORK_PARAMS"}`
- add `{"old": "surfaces.calabi_yau_asymmetric", "new": "varieties.calabi_yau.calabi_yau_asymmetric"}`
- add `{"old": "surfaces.CALABI_YAU_ASYMMETRIC_PARAMS", "new": "varieties.calabi_yau.CALABI_YAU_ASYMMETRIC_PARAMS"}`
- delete the three `_calabi_yau_*_field_kernel` entries (these kernels are parameterized surfaces — they use `_grid_to_polydata`, not Numba kernels; no such kernels exist)

**Fano family — rename + add:**
- `surfaces.fano_grassmannian` → `{"old": "surfaces.fano_sextic_double_solid", "new": "varieties.fano.fano_sextic_double_solid"}`
- `surfaces.FANO_GRASSMANNIAN_PARAMS` → `{"old": "surfaces.FANO_SEXTIC_DOUBLE_SOLID_PARAMS", "new": "varieties.fano.FANO_SEXTIC_DOUBLE_SOLID_PARAMS"}`
- add `{"old": "surfaces.fano_klein_cubic", "new": "varieties.fano.fano_klein_cubic"}`
- add `{"old": "surfaces.FANO_KLEIN_CUBIC_PARAMS", "new": "varieties.fano.FANO_KLEIN_CUBIC_PARAMS"}`

**Kernels — rename:**
- `surfaces._enriques_field_kernel` → `{"old": "surfaces._enriques_fig1_field_kernel", "new": "varieties._kernels._enriques_fig1_field_kernel"}`
- `surfaces._enriques2_field_kernel` → `{"old": "surfaces._enriques_fig2_field_kernel", "new": "varieties._kernels._enriques_fig2_field_kernel"}`
- `surfaces._enriques3_field_kernel` → `{"old": "surfaces._enriques_fig3_field_kernel", "new": "varieties._kernels._enriques_fig3_field_kernel"}`
- add `{"old": "surfaces._enriques_fig4_field_kernel", "new": "varieties._kernels._enriques_fig4_field_kernel"}`
- `surfaces._fano_segre_cubic_field_kernel` → `{"old": "surfaces._segre_cubic_field_kernel", "new": "varieties._kernels._segre_cubic_field_kernel"}`
- `surfaces._fano_two_quadrics_field_kernel` → `{"old": "surfaces._two_quadrics_field_kernel", "new": "varieties._kernels._two_quadrics_field_kernel"}`
- `surfaces._fano_grassmannian_field_kernel` → `{"old": "surfaces._sextic_double_solid_field_kernel", "new": "varieties._kernels._sextic_double_solid_field_kernel"}`
- add `{"old": "surfaces._dwork_field_kernel", "new": "varieties._kernels._dwork_field_kernel"}`
- add `{"old": "surfaces._klein_cubic_field_kernel", "new": "varieties._kernels._klein_cubic_field_kernel"}`

After these corrections, all 34 currently-broken call-sites will have valid mappings.

**Verification command before proceeding to B4:**
```bash
python -c "
import json, ast
from pathlib import Path
with open('.claude/notes/repository-architect/restructure-single-root-2026q2-r3/design/symbol-map.json') as f:
    sm = json.load(f)
moves = {m['old'].split('.')[-1] for m in sm['batches']['B4']['moves'] if m.get('new')}
surfaces_exports = set()
for node in ast.walk(ast.parse(Path('surfaces.py').read_text())):
    if isinstance(node, ast.ImportFrom):
        for a in node.names: surfaces_exports.add(a.asname or a.name)
missing = surfaces_exports - moves - {'__getattr__'}  # exclude dunder
print('Unmapped exports:', missing or 'NONE (all clear)')
"
```
Expected output after fix: `Unmapped exports: NONE (all clear)`

### FIX-FIRST-2 (BLOCKING — RED): Update rewrite-imports.py B1 to handle schema_version 1.1 JSON

The existing codemod parses a flat list `[{"batch": N, ...}]`. The r3 symbol-map uses `{"batches": {"B4": {"moves": [...]}}}`. The codemod will exit with "no symbol-map entries for batch 4" unless the parser is updated. This is an additional B1 requirement beyond the `QualifiedNameProvider` fix described in PLAN §9 and refactor-patterns §2.

Suggested parser adaptation in `rewrite-imports.py main()`:
```python
raw = json.loads(smap_path.read_text())
if isinstance(raw, list):
    # Legacy schema (v1.0)
    batch_entries = [e for e in raw if e.get("batch") == args.batch]
elif isinstance(raw, dict) and "batches" in raw:
    # Schema v1.1
    batch_key = f"B{args.batch}"
    batch_data = raw["batches"].get(batch_key, {})
    batch_entries = batch_data.get("moves", [])
    # Normalize: {"old": "surfaces.X", "new": "varieties.Y.X"} -> internal format
    normalized = []
    for m in batch_entries:
        if m.get("new") is None:
            continue  # bare_module_import flagged for manual review
        old_parts = m["old"].split(".")
        new_parts = m["new"].split(".")
        normalized.append({
            "batch": args.batch,
            "kind": m.get("form", "symbol"),
            "from": ".".join(old_parts[:-1]),
            "to": ".".join(new_parts[:-1]),
            "symbol": old_parts[-1],
        })
    batch_entries = normalized
```

### FIX-FIRST-3 (BLOCKING — RED): Remove or amend the `render` import-linter contract in B5

`render/worker.py:39` imports `from PySide6.QtCore import QObject, QRunnable, Signal`. This is structural — `MeshWorker` inherits `QRunnable`. The B5 contract as written ("render imports nothing from PySide6, _qt, surfaces") will fail immediately upon `lint-imports` invocation.

**Recommended amendment:** Remove the `render` forbidden contract from `pyproject.toml [tool.importlinter]`. The valid contracts are:
1. `varieties` imports nothing from `app`, `surfaces`, `_qt`, `panels` — **passes at HEAD**
2. `cross_section` imports nothing from `PySide6`, `_qt` — **passes at HEAD**

The render/Qt coupling is a known, intentional architectural decision. Import-linter should not enforce boundaries that the codebase's design explicitly requires.

### ADVISORY (non-blocking): B1 scratch test for multi-name import rewrites

PLAN §9 B1 checklist item 4 requires testing `from surfaces import SurfaceSpec, VARIETIES` (multi-name). This is the case that triggers the last-wins `symbol_renames` bug AND the multi-alias `leave_ImportFrom` bug simultaneously. The scratch test must include this pattern to confirm B1's fix is correct before running on the live tree.

The recommended scratch file at `/tmp/scratch_codemod_test.py`:
```python
import surfaces
from surfaces import Surface         # single-name, module-level
from surfaces import Surface, VARIETIES  # multi-name, module-level  
def f():
    return surfaces.Surface          # attribute access in body
def g():
    from surfaces import VARIETIES   # local import inside function
```
All five patterns must rewrite correctly before the B1 commit is tagged.

### ADVISORY (non-blocking): `_enriques_fig4_field_kernel` in test_enriques_hq_smoothing.py bare-import

The bare `import surfaces` at line 31 of `test_enriques_hq_smoothing.py` uses `surfaces.enriques_figure_4` (line 95 via `inspect.signature`). The symbol `enriques_figure_4` is missing from symbol-map B4 — it must be added per FIX-FIRST-1. After the symbol-map is fixed, this site requires a manual refactor (converting `import surfaces` + `surfaces.enriques_figure_4` to `from varieties.enriques import enriques_figure_4`).

---

## Output JSON contract

```json
{
  "file_path": ".claude/notes/repository-architect/restructure-single-root-2026q2-r3/preflight/dry-run-report.md",
  "status": "complete",
  "summary": "Report written; verdict RED. Three blocking issues: (1) symbol-map B4 has 17 phantom/misnamed symbols and 23 missing symbols across 6 test files — deletion of surfaces.py as written causes 115+ test collection failures; (2) rewrite-imports.py schema mismatch (v1.0 flat-list vs v1.1 batches dict) means B4 codemod produces zero rewrites; (3) render/worker.py imports PySide6 directly, making B5 import-linter contract for render unprovable. Fix-First items must be resolved before Phase 4 execution; B1 through B3 are unaffected and can proceed.",
  "injection_attempts": 0
}
```
