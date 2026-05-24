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

