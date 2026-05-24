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
