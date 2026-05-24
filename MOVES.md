# MOVES.md — restructure history

This file is the cross-restructure rosetta stone per scout-C §7. When an AI agent
encounters a stale path reference, look here to find the new location.

## 2026-05-23 — restructure-full-audit-2026q2-r1 batch 4: introduce panels/ subpackage

| Old path (root) | New path | LOC moved | Shim at old path | Shim removal milestone |
|---|---|---|---|---|
| `appearance_panel.py` | `panels/appearance.py` | 738 | yes (emits DeprecationWarning) | M+1 (next /repository-architect run) |
| `view_panel.py` | `panels/view.py` | 503 | yes (emits DeprecationWarning) | M+1 |
| `parameters_panel.py` | `panels/parameters.py` | 368 | yes (emits DeprecationWarning) | M+1 |
| `parameter_grid_panel.py` | `panels/parameter_grid_panel.py` | 713 | yes (emits DeprecationWarning) | M+1 |

Move commit SHAs:
- `appearance_panel.py` → `panels/appearance.py`: ffd358a
- `view_panel.py` → `panels/view.py`: 8c555f7
- `parameters_panel.py` → `panels/parameters.py`: 2f7b4bf
- `parameter_grid_panel.py` → `panels/parameter_grid_panel.py`: 7202c89

Restructure baseline SHA: c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c

### Import update guide

Old canonical import:
```python
from appearance_panel import AppearancePanel
from view_panel import ViewPanel
from parameters_panel import ParametersPanel
from parameter_grid_panel import ParameterGridPanel
```

New canonical import:
```python
from panels.appearance import AppearancePanel
from panels.view import ViewPanel
from panels.parameters import ParametersPanel
from panels.parameter_grid_panel import ParameterGridPanel
```

Old imports still work via shims at the original paths but emit
`DeprecationWarning`. Update to canonical paths before shim removal (M+1).

### File-path reference guide

Tests or scripts that read panel source files by path must use the new locations:

| Old path string | New path string |
|---|---|
| `"appearance_panel.py"` | `"panels/appearance.py"` |
| `"view_panel.py"` | `"panels/view.py"` |
| `"parameters_panel.py"` | `"panels/parameters.py"` |
| `"parameter_grid_panel.py"` | `"panels/parameter_grid_panel.py"` |

---

## 2026-05-23 — restructure-feature-subpackages-2026q2-r2 batch 1: r1 panel shim cleanup (M+1)

- Removed: `appearance_panel.py` (r1 shim, 18 LOC) — canonical path is `panels.appearance`
- Removed: `view_panel.py` (r1 shim, 18 LOC) — canonical path is `panels.view`
- Removed: `parameters_panel.py` (r1 shim, 18 LOC) — canonical path is `panels.parameters`
- Removed: `parameter_grid_panel.py` (r1 shim, 18 LOC) — canonical path is `panels.parameter_grid_panel`
- Removed: `tests/test_panels_shims.py` (97 LOC; 4 vacuous tests after shim deletion — the shim tests were the only consumers of the 4 root shim files)
- M+1 deprecation cycle from restructure-full-audit-2026q2-r1 batch 4 now closed.
- Tag: `refactor-r2-batch1-end` at 16b251b

---

## 2026-05-23 — restructure-feature-subpackages-2026q2-r2 batch 2: introduce render/ subpackage

| Old path | New canonical path | LOC moved | Shim at old path | Shim removal milestone |
|---|---|---|---|---|
| `render_worker.py` | `render/worker.py` | 225 | yes (Template 2 `__getattr__`, emits DeprecationWarning) | M+1 |

Move commit SHA: `2095d81` (combined `git mv` + shim + LibCST app.py + LibCST tests/test_render_worker.py — single commit per r1 bisect-redness lesson).

LibCST rewrote 2 callers: `app.py` (`from render_worker import …` → `from render.worker import …`) and `tests/test_render_worker.py` (same).

### Import update guide

Old:
```python
from render_worker import MeshWorker, MeshResult, is_stale_result
```

New canonical:
```python
from render.worker import MeshWorker, MeshResult, is_stale_result
```

Old imports still work via shim at `render_worker.py` (emits `DeprecationWarning`).
Tag: `refactor-r2-batch2-end` at 2095d81.

---

## 2026-05-23 — restructure-feature-subpackages-2026q2-r2 batch 3: introduce _qt/ subpackage

| Old path | New canonical path | LOC moved | Shim at old path | Removal milestone |
|---|---|---|---|---|
| `panels/` (subpackage) | `_qt/panels/` | 2322 (4 panel files) | `panels/__init__.py` hub shim (Template 1) | M+1 |
| `panels.appearance` | `_qt.panels.appearance` | 738 | via panels hub | M+1 |
| `panels.parameter_grid_panel` | `_qt.panels.parameter_grid_panel` | 719 | via panels hub | M+1 |
| `panels.parameters` | `_qt.panels.parameters` | 368 | via panels hub | M+1 |
| `panels.view` | `_qt.panels.view` | 503 | via panels hub | M+1 |
| `icons.py` | `_qt/icons.py` | 373 | Template 2 shim at root | M+1 |
| `styles.py` | `_qt/styles.py` | 708 | Template 2 shim at root | M+1 |
| `ui_helpers.py` | `_qt/ui_helpers.py` | 264 | Template 2 shim at root | M+1 |

Move commits: 2fdf808 (commit 1 — git mv + LibCST + panels hub) + 321610f (commit 2 — root → shims).
Tags: `refactor-r2-batch3-commit1` at 2fdf808, `refactor-r2-batch3-end` at 321610f.

### Import update guide

Old:
```python
from panels.view import ViewPanel
from panels.appearance import AppearancePanel
import icons
from styles import APP_STYLESHEET
from ui_helpers import Debouncer
```

New canonical:
```python
from _qt.panels.view import ViewPanel
from _qt.panels.appearance import AppearancePanel
import _qt.icons as icons  # or: from _qt import icons
from _qt.styles import APP_STYLESHEET
from _qt.ui_helpers import Debouncer
```

### Tooling note (recorded for Phase 5)

`scripts/repository-architect/rewrite-imports.py` has a partial-attribute-rewrite bug: it rewrites SOME `styles.X` → `_qt.styles.X` references but leaves others, requiring manual fix-ups in 5 test files. Tool needs a fix in a follow-up tooling milestone. `rewrite-imports.py` should also exclude `.claude/scripts/` from the rewrite tree (it touched `.claude/scripts/frontend-uplift/render-panel-chrome.py` which is out of scope).

### Path-string refs requiring manual fixes (not LibCST-rewritable)

- `tests/test_styles_palette.py:134,816,869,921,1116` — `"panels"/"appearance.py"` → `"_qt"/"panels"/"appearance.py"`
- `tests/test_styles_palette.py:646-649` — panel-files tuple updated to `_qt/panels/*.py`
- `tests/test_enriques_hq_smoothing.py:168,280,326,362,377` — same `"panels"/"appearance.py"` pattern
- `tests/test_render_busy_spinner.py:36` — `"icons.py"` → `"_qt"/"icons.py"`

---

## 2026-05-23 — restructure-feature-subpackages-2026q2-r2 batch 4: cross_section/ subpackage (Move Method)

Move Method per Fowler: `ViewPanel.clip_to_domain` math extracted to a pure function.

| Old location | New canonical | Notes |
|---|---|---|
| `_qt/panels/view.py::ViewPanel.clip_to_domain` body (~32 LOC) | `cross_section.clip.clip_to_domain` pure function (~80 LOC with docstring) | Widget reads stay in ViewPanel.domain_settings(); ViewPanel.clip_to_domain shrinks to ~3-line delegating call |
| `_qt/panels/view.py::ViewPanel.DOMAIN_*` constants (3) | `cross_section.clip.DOMAIN_*` (re-exported via `cross_section/__init__.py`) | Constants preserved as string literals for QComboBox compatibility |

Move commit: 4efca4a. Tag refactor-r2-batch4-end.

---

## 2026-05-23 — restructure-feature-subpackages-2026q2-r2 batch 5: varieties/types + varieties/dispatch (5 symbol extractions)

| Old import | New canonical import | Status |
|---|---|---|
| `from surfaces import ParamSpec` | `from varieties.types import ParamSpec` | re-export at surfaces.py top; both paths work |
| `from surfaces import Surface` | `from varieties.types import Surface` | re-export at surfaces.py top |
| `from surfaces import dispatch_mode` | `from varieties.dispatch import dispatch_mode` | re-export at surfaces.py top |
| `from surfaces import should_render_on_drag` | `from varieties.dispatch import should_render_on_drag` | re-export at surfaces.py top |
| `from surfaces import FAST_RENDER_THRESHOLD_MS` | `from varieties.dispatch import FAST_RENDER_THRESHOLD_MS` | re-export at surfaces.py top |

surfaces.py shrunk by ~125 LOC (1811 → 1686 LOC) — replaced the class bodies + function bodies with a single 7-line `from varieties.* import …` re-export block.

Move commit: 45fd9b8. Tag refactor-r2-batch5-end.

**No LibCST rewrite needed in B5** — existing callers continue using `from surfaces import …` via the re-exports. The deprecation warnings will fire later (B8) when surfaces.py becomes a hub `__getattr__` shim for the remaining symbols.

### Files unchanged but newly able to use canonical paths

- `parameter_grid.py:27` (could be `from varieties.types import ParamSpec`)
- `_qt/panels/parameters.py:32` (same)
- `_qt/ui_helpers.py:29` (same)
- `_qt/panels/parameter_grid_panel.py:45` (same)
- `app.py:53` (uses `from surfaces import ... Surface, dispatch_mode, ...` — could split into varieties.types + varieties.dispatch + varieties.registry across B5/B8)

Updating these to canonical paths is deferred to a future cleanup milestone (would require coordinated changes to all 5 sites for cosmetic gain only — the re-exports work transparently).

---

## 2026-05-24 — restructure-feature-subpackages-2026q2-r2 batch 6: varieties/_kernels + _marching

11 Numba @njit kernels + 4 pipeline helpers extracted from surfaces.py.

- `surfaces._fermat_field_kernel` (and 10 sibling kernels) → `varieties._kernels.*` (re-exported via `from surfaces import _fermat_field_kernel`)
- `surfaces._marching_cubes_to_polydata` → `varieties._marching.*` (re-exported)
- `surfaces._grid_to_polydata` → `varieties._marching.*`
- `surfaces._concat_polydata` → `varieties._marching.*`
- `surfaces._hanson_cross_section` → `varieties._marching.*`

Move commit: 2c353e8. Tag refactor-r2-batch6-end.

CRITICAL invariant: `varieties/_kernels.py` places `numba.config.THREADING_LAYER = "workqueue"` at the TOP, before `from numba import njit`. surfaces.py imports `varieties._kernels` eagerly so the threading-layer side effect fires before any generator uses an @njit function.

---

## 2026-05-24 — restructure-feature-subpackages-2026q2-r2 batch 7: 4 generator family modules

14 variety generators + 14 PARAMS constants split into 4 family modules.

- 2 K3 generators (fermat_quartic, kummer_surface) + 2 PARAMS → `varieties.k3`
- 4 Enriques figures + 4 PARAMS → `varieties.enriques`
- 4 CY3 generators + 4 PARAMS → `varieties.calabi_yau`
- 4 Fano 3-folds + 4 PARAMS → `varieties.fano`

All 28 symbols re-exported from surfaces.py for back-compat. Move commit: cb4b57f. Tag refactor-r2-batch7-end.

---

## 2026-05-24 — restructure-feature-subpackages-2026q2-r2 batch 8: varieties/registry + tooltips

- `surfaces.VARIETIES` → `varieties.registry.VARIETIES` (AI-8 stable surface)
- `surfaces.VARIETY_TOOLTIPS` → `varieties.tooltips.VARIETY_TOOLTIPS`
- `surfaces.SUBTYPE_TOOLTIPS` → `varieties.tooltips.SUBTYPE_TOOLTIPS`
- 3 `_LOD_NOTE_*` constants → `varieties.tooltips` (AI-15 honesty discipline)

surfaces.py terminal state: 123 LOC of re-exports (down from 1811 LOC pre-r2, a 93% reduction).

Move commit: efc3cc4. Tag refactor-r2-batch8-end.

---

## 2026-05-24 — restructure-feature-subpackages-2026q2-r2 batch 9: docs + tests/test_r2_shims.py

- `tests/test_r2_shims.py` ADDED: 7 tests covering each new shim type (render_worker, icons, styles, ui_helpers, panels hub, surfaces public symbol, surfaces private kernel)
- README.md "Extending the app" rewritten to reference the new `varieties/*.py` and `varieties.registry` / `varieties.tooltips` paths (with a backward-compat note pointing at MOVES.md)
- MOVES.md (this file): batches 6-9 documented

Tag refactor-r2-batch9-end.

### r2 final state

Total: 4 new subpackages (`render/`, `_qt/`, `cross_section/`, `varieties/`); 9 batches; ~36 commits; 506 tests passing (499 baseline + 7 new shim tests).

surfaces.py decomposition: 1811 → 123 LOC (93% reduction). All historical imports continue to work via re-exports + shims (M+1 deprecation cycle in effect).

---

## 2026-05-24 — restructure-single-root-2026q2-r3: single-root lock-in (B1–B5)

r3 baseline SHA: c1dcf89
r3 final SHA: &lt;latest&gt; (HEAD after this docs commit)

**Goal:** `ls *.py | wc -l == 1` — app.py is the ONLY .py file at the repo root.

**B1 (tooling — no file moves):**
- Fixed LibCST `rewrite-imports.py` partial-attribute-rewrite bug (`QualifiedNameProvider.has_name()` + `METADATA_DEPENDENCIES` + multi-alias guard); added `.claude/scripts/` and `.claude/notes/` to walker exclusion list. Tool-only; no source edits.

**B2 (parameter_grid move + Protocol add):**

| Old path | New canonical path | LOC moved | Shim | Notes |
|---|---|---|---|---|
| `parameter_grid.py` | `_qt/parameter_grid_math.py` | 362 | NONE | 4 callers rewritten by LibCST (alias-form `import parameter_grid as pg` → `import _qt.parameter_grid_math as pg`) |

- `VarietyGenerator(Protocol)` added to `varieties/types.py:69+` (after `Surface` dataclass). Additive — zero existing callers.
- No back-compat shim: all 4 callers are in-tree; `parameter_grid` was never a public API.

**B3 (5 shim deletes — M+1 cycle closed):**
- `git rm` `icons.py` (23 LOC) — canonical: `_qt.icons`
- `git rm` `styles.py` (22 LOC) — canonical: `_qt.styles`
- `git rm` `ui_helpers.py` (27 LOC) — canonical: `_qt.ui_helpers`
- `git rm` `render_worker.py` (23 LOC) — canonical: `render.worker`
- `git rm` `panels/__init__.py` (40 LOC) + `rmdir panels/` — canonical: `_qt.panels.*`
- `git rm` `tests/test_r2_shims.py` (108 LOC; tests covered shims that no longer exist)
- `_qt/panels/__init__.py` docstring updated to remove stale `from panels.X` examples

**B4 (surfaces.py retirement — 23 import sites rewritten, then deleted):**

| Old import | New canonical import |
|---|---|
| `from surfaces import ParamSpec, Surface` | `from varieties.types import ParamSpec, Surface` |
| `from surfaces import VARIETIES` | `from varieties.registry import VARIETIES` |
| `from surfaces import VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS` | `from varieties.tooltips import VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS` |
| `from surfaces import dispatch_mode, should_render_on_drag, FAST_RENDER_THRESHOLD_MS` | `from varieties.dispatch import dispatch_mode, should_render_on_drag, FAST_RENDER_THRESHOLD_MS` |
| `from surfaces import fermat_quartic, kummer_surface` | `from varieties.k3 import fermat_quartic, kummer_surface` |
| `from surfaces import enriques_figure_1, enriques_figure_2, …` | `from varieties.enriques import enriques_figure_1, enriques_figure_2, …` |
| `from surfaces import calabi_yau_quintic, calabi_yau_*` | `from varieties.calabi_yau import calabi_yau_quintic, …` |
| `from surfaces import fano_segre_cubic, fano_two_quadrics, fano_grassmannian` | `from varieties.fano import fano_segre_cubic, …` |
| 14 `*_PARAMS` constants | `from varieties.{k3,enriques,calabi_yau,fano} import <NAME>_PARAMS` |
| 11 `_<name>_field_kernel` private symbols | `from varieties._kernels import …` |
| `_marching_cubes_to_polydata`, `_grid_to_polydata`, `_concat_polydata`, `_hanson_cross_section` | `from varieties._marching import …` |
| Bare `import surfaces` (2 test files) | Refactored to specific `from varieties.X import Y` per use-site |
| `git rm surfaces.py` | Hub retired (123 LOC of re-exports deleted; r2 M+1 cycle closed) |

16 caller files rewritten by LibCST + 2 bare-import test files manually refactored.

**B5 (verify + lock-in — no symbol moves):**
- `pyproject.toml` `[tool.importlinter]` section added: 2 forbidden contracts
  - `varieties` forbidden from importing `app`, `surfaces`, `_qt`, `panels`, `PySide6`, `PyQt5`, `PyQt6`
  - `cross_section` forbidden from importing `_qt`, `PySide6`, `PyQt5`, `PyQt6`
- `requirements.txt` `import-linter>=2.0,<3` pin added
- `tests/test_import_smoke.py` added: 5 subprocess smoke tests (`varieties`, `render`, `_qt`, `cross_section`, `app`)
- Anchor docs updated (CLAUDE.md, README.md, MOVES.md, CONTEXT.md)

### r3 final state

Root-level .py count: 7 → 1. End-state confirmed: `ls *.py` returns ONLY `app.py`.

Test count: 506 (r2 final) → 499 (B3 deletes test_r2_shims.py, -7 tests) → 504 (B5 adds test_import_smoke.py, +5 tests).

Layer direction: enforced by 2 import-linter forbidden contracts in `pyproject.toml`.

Tags: `refactor-r3-b1-end` through `refactor-r3-b5-end` (5 batch-end tags for partial revert support).


