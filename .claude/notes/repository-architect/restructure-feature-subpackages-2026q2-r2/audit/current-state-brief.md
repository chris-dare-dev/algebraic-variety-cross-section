# Current-State Audit Brief
## Restructure ID: restructure-feature-subpackages-2026q2-r2
## Phase 1 — Auditor output
## Date: 2026-05-23

---

## 1. TL;DR

- **surfaces.py is the dominant monolith** at 1811 LOC, containing 7 distinct logical concerns: dataclasses/dispatch, pipeline helpers, 11 Numba @njit kernels (401 LOC — cleanest seam), 807 LOC of generators across 4 variety families, the VARIETIES registry, per-variety PARAMS constants, and 160 LOC of tooltips.
- **r1 left 4 root-level shim files** (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py` — each 18 LOC) pointing into `panels/`. The brief designates this as M+1 (i.e., r2 removes them after updating callers). app.py already uses the `panels.*` canonical paths; only `tests/test_panels_shims.py` still exercises the shims.
- **clip_to_domain is NOT a pure function** — it reads `self._domain_mode`, `self._radius_slider`, `self._domain_overlay_cb` via `self.domain_settings()`, making it a method, not a standalone callable. Extracting it requires extracting a plain-data config struct first.
- **Three Qt-coupled root files** (`icons.py` 373 LOC, `ui_helpers.py` 264 LOC, `styles.py` 708 LOC) are candidates for `_qt/` but each has hidden coupling: `icons.py` does lazy-import qtawesome with a guard test; `ui_helpers.py` imports `parameter_grid` and `surfaces.ParamSpec`; `styles.py` is pure data but is consumed by all panel code.
- **503 tests pass** (project venv Python 3.12). The `test_numba_field_kernels.py` imports 11 kernel names directly from `surfaces` via `from surfaces import _fermat_field_kernel …` — these paths are test-contract locks that need shims if kernels move.

---

## 2. Repo Top-Level Tree (annotated, post-r1)

| Entry | Bytes | Purpose | Tracked | Notes |
|---|---|---|---|---|
| `app.py` | 102 479 | MainWindow entry point | yes | 1900 LOC monolith; NOT in this restructure's scope (brief §5) |
| `surfaces.py` | 78 147 | All variety generators + dataclasses + registry + tooltips | yes | **1811 LOC — primary r2 target** |
| `CONTEXT.md` | 84 344 | Architecture documentation | yes | ~84 KB; authorized for Batch 4+ rewrites |
| `styles.py` | 36 540 | QSS stylesheet + palette constants | yes | 708 LOC; Qt-coupled; `_qt/` candidate |
| `panels/` | dir (8 files) | UI panel subpackage (r1 output) | yes | 10 files per cache tree.txt; see §5 |
| `tests/` | dir (26 files) | Test suite | yes | 503 tests; see §6 |
| `AGENTS.md` | 5 683 | Agent instructions | yes | CLAUDE.md is a symlink to this |
| `README.md` | 18 503 | User-facing docs | yes | authorized for Batch 4+ rewrites |
| `icons.py` | 17 628 | qtawesome icon factories (lazy-import) | yes | 373 LOC; Qt-coupled; `_qt/` candidate |
| `parameter_grid.py` | 13 096 | Pure-math parameter-grid transforms | yes | 362 LOC; no Qt; imports `surfaces.ParamSpec` |
| `render_worker.py` | 11 180 | QRunnable mesh worker | yes | 225 LOC; Qt-coupled; `render/` candidate |
| `ui_helpers.py` | 10 429 | Debouncer + slider-row builder | yes | 264 LOC; Qt-coupled; imports `parameter_grid` + `surfaces.ParamSpec` |
| `MOVES.md` | 2 122 | Restructure history rosetta stone | yes | r1 panel moves documented here |
| `pyproject.toml` | 778 | Build metadata + deps | yes | no `[project.scripts]`; `python app.py` invocation preserved |
| `appearance_panel.py` | 624 | **Shim** → `panels/appearance.py` | yes | 18 LOC; r1 artifact; M+1 removal |
| `parameters_panel.py` | 624 | **Shim** → `panels/parameters.py` | yes | 18 LOC; r1 artifact; M+1 removal |
| `view_panel.py` | 582 | **Shim** → `panels/view.py` | yes | 18 LOC; r1 artifact; M+1 removal |
| `parameter_grid_panel.py` | 669 | **Shim** → `panels/parameter_grid_panel.py` | yes | 18 LOC; r1 artifact; M+1 removal |
| `CHANGELOG.md` | 851 | Release notes | yes | r1 added this |
| `LICENSE` | 1 067 | License file | yes | r1 added this |
| `pytest.ini` | 27 | `testpaths = tests` | yes | minimal |
| `requirements.txt` | 461 | Pinned deps | yes | NOT `pyproject.toml` extras |
| `plans/` | dir (2 files) | Historical plan artifacts | yes | read-only context |
| `.github/` | dir | CI workflows | yes | OUT OF SCOPE |
| `.claude/` | dir (433 tracked files) | Agent tooling + memory | yes | OUT OF SCOPE per brief |
| `.venv/` | dir | Python virtualenv | gitignored | |
| `__pycache__/` | dir | Bytecode cache | gitignored | |
| `.coverage` | 69 632 | Coverage data | gitignored | |

---

## 3. Source Module Inventory (sorted by LOC descending)

| File | LOC | Sections | Purpose | Reads-from | Written-by |
|---|---|---|---|---|---|
| `app.py` | 1900 | ~9 | MainWindow (entry point, full app state) | `panels.*`, `render_worker`, `styles`, `surfaces`, `icons` | user drag/click events; `render_worker` signal |
| `surfaces.py` | 1811 | 13 (see §4) | Variety generators + registry + dataclasses + Numba kernels | stdlib + numpy + pyvista + numba only | nothing in-repo |
| `styles.py` | 708 | 4 | QSS palettes, color constants, stylesheet renderer | self (docstring only) | `icons`, `app`, `panels/appearance`, `panels/parameter_grid_panel`, `ui_helpers` |
| `panels/appearance.py` | 738 | ~6 | AppearancePanel widget | `PySide6`, `icons`, `styles` | app.py |
| `panels/parameter_grid_panel.py` | 719 | ~8 | ParameterGridPanel widget | `PySide6`, `parameter_grid`, `styles`, `surfaces`, `ui_helpers` | app.py |
| `panels/view.py` | 503 | ~7 | ViewPanel widget (incl. clip_to_domain) | `PySide6`, `icons`, `numpy`, `pyvista` | app.py |
| `panels/parameters.py` | 368 | ~5 | ParametersPanel widget | `PySide6`, `icons`, `panels`, `parameter_grid`, `surfaces`, `ui_helpers` | app.py |
| `icons.py` | 373 | 2 | qtawesome icon factories (lazy-import) | `PySide6`, `styles` (lazy: `qtawesome`) | `app`, `panels/view`, `panels/parameters`, `panels/appearance` |
| `parameter_grid.py` | 362 | ~10 | Pure-math param-grid transforms + AxisAssignment | `surfaces.ParamSpec` (dataclasses only) | `ui_helpers`, `panels/parameter_grid_panel`, `panels/parameters` |
| `ui_helpers.py` | 264 | 3 | DebounceCounter, Debouncer, build_slider_row | `PySide6`, `parameter_grid`, `styles.SMALL_LABEL_STYLE`, `surfaces.ParamSpec` | `panels/parameter_grid_panel`, `panels/parameters` |
| `render_worker.py` | 225 | 4 | MeshWorker (QRunnable), MeshResult, is_stale_result | `PySide6.QtCore`, `pyvista`, stdlib | `app.py` |
| `appearance_panel.py` | 18 | 1 | **Shim** (M+1 removal) | `panels.appearance` (on demand) | `tests/test_panels_shims.py` |
| `view_panel.py` | 18 | 1 | **Shim** (M+1 removal) | `panels.view` (on demand) | `tests/test_panels_shims.py` |
| `parameters_panel.py` | 18 | 1 | **Shim** (M+1 removal) | `panels.parameters` (on demand) | `tests/test_panels_shims.py` |
| `parameter_grid_panel.py` | 18 | 1 | **Shim** (M+1 removal) | `panels.parameter_grid_panel` (on demand) | `tests/test_panels_shims.py` |
| `panels/__init__.py` | 13 | 1 | Package docstring + canonical import paths | `panels.*` | external callers |

**Files exceeding 500 LOC (monolith candidates):** `app.py` (1900), `surfaces.py` (1811), `styles.py` (708), `panels/appearance.py` (738), `panels/parameter_grid_panel.py` (719), `panels/view.py` (503).

---

## 4. Monolith Deep Dive

### 4.1 surfaces.py — 1811 LOC

**Primary r2 extraction target.** All 7 concerns are separated by `# -----` banners; seam quality varies.

| Section | Lines | LOC | Cleanliness | Notes |
|---|---|---|---|---|
| Imports + numba config | L1–L41 | 41 | — | `numba.config.THREADING_LAYER = "workqueue"` is a **process-global side effect at import time**. MUST travel with kernels if kernels move — or stay in `surfaces.py` which re-exports. |
| `ParamSpec` + `Surface` dataclasses + dispatch helpers | L42–L167 | 126 | Very clean | `should_render_on_drag`, `dispatch_mode` read only `Surface` fields. No external state. Extraction-ready. |
| Pipeline helpers (`_marching_cubes_to_polydata`) | L168–L284 | 117 | Clean | Uses `numpy`, `pyvista` only. No Numba. But `_marching_cubes_to_polydata` calls `smooth_taubin` + `compute_normals` — AI-6 contract owner. |
| **Numba kernels** (11 `@njit` functions) | L285–L685 | **401** | **Cleanest seam** | 11 standalone `@njit(parallel=True, cache=True)` functions. Each takes only `g: np.ndarray` + scalar params + `out: np.ndarray`. **No imports from repo, no calls to other local functions.** Extraction blocker: the `numba.config.THREADING_LAYER` side-effect at L38 must co-locate with kernels or surface the side-effect explicitly at import in `surfaces.py` after extraction. |
| `_grid_to_polydata` + `_concat_polydata` | L686–L742 | 57 | Clean | PyVista-only helpers for parametric pipeline. AI-6 contract: Hanson generators MUST use these. |
| **Fermat quartic generator** | L743–L835 | 93 | Clean | Calls `_fermat_field_kernel` + `_marching_cubes_to_polydata`. Defines `FERMAT_PARAMS`. |
| **Kummer surface generator** | L836–L886 | 51 | Clean | Calls `_kummer_field_kernel`. Defines `KUMMER_PARAMS`. |
| **Enriques generators** (4 fns) | L887–L1075 | 189 | Clean | Figs 1–4 use kernels + marching cubes. Fig 1 and Fig 2 have `hq_smoothing` kwarg (AI-link: AppearancePanel). Defines `ENRIQUES_FIGURE_[1-4]_PARAMS`. |
| **Calabi-Yau generators** (4 fns) | L1076–L1316 | 241 | Moderate | Quintic/Cubic/Asymmetric are Hanson parametric (use `_grid_to_polydata`). Dwork uses kernel + marching cubes. _hanson_cross_section at L1087 is an internal shared helper. Defines `CALABI_YAU_*_PARAMS`. |
| **Fano generators** (4 fns) | L1317–L1549 | 233 | Clean | Klein/Segre/Two-quadrics/Sextic use kernels + marching cubes. Two-quadrics has `coarse_n=0` opt-out. Defines `FANO_*_PARAMS`. |
| `VARIETIES` registry | L1550–L1651 | 102 | Moderate | Dict of dicts. **AI-8 load-bearing: must remain importable at a stable path.** Brief specifies `from varieties.registry import VARIETIES` as the new stable path. |
| Tooltips (`VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS`) | L1652–L1811 | 160 | Clean | Three render-mode note constants + two tooltip dicts. `SUBTYPE_TOOLTIPS` imported by `tests/test_styles_palette.py:L1251`. |

**Generator-by-family grouping for extraction:**

| Target module (proposed) | LOC | Generators | Kernels called |
|---|---|---|---|
| `varieties/k3.py` | ~144 | `fermat_quartic`, `kummer_surface` | `_fermat_field_kernel`, `_kummer_field_kernel` |
| `varieties/enriques.py` | ~189 | `enriques_figure_1..4` | `_enriques_fig[1-4]_field_kernel` |
| `varieties/calabi_yau.py` | ~241 | `calabi_yau_quintic/cubic/asymmetric/dwork` | `_dwork_field_kernel`; Hanson helpers |
| `varieties/fano.py` | ~233 | `fano_klein_cubic/segre/two_quadrics/sextic_double_solid` | `_klein/segre/two_quadrics/sextic_double_solid_field_kernel` |

**Hidden coupling warnings for surfaces.py extraction:**

1. `numba.config.THREADING_LAYER = "workqueue"` at L38 is a process-global side effect. If `_kernels.py` becomes a submodule, this side effect must fire on `import varieties._kernels`, or `surfaces.py` (now a shim) must set it before `from varieties._kernels import …`. Documented in `CONTEXT.md §3` and lessons.md.
2. `_PARAMS` constants (e.g., `FERMAT_PARAMS = [...]` at L824) are imported by `tests/test_parameters_panel.py` and `tests/test_parameter_grid.py` via `from surfaces import FERMAT_PARAMS`. Every `_PARAMS` list must be re-exported via `surfaces.py` shim or tests must be updated.
3. `should_render_on_drag` is exported for backward compat (app.py no longer imports it but the test `test_typical_ms.py` does via `from surfaces import should_render_on_drag`).
4. `dispatch_mode` is imported by `app.py` (`from surfaces import dispatch_mode`). Must be re-exported.
5. The `hq_smoothing` kwarg on `enriques_figure_1` and `enriques_figure_2` is test-checked by `test_enriques_hq_smoothing.py` via `import surfaces; sig = inspect.signature(surfaces.enriques_figure_1)` — the module must remain importable as `surfaces`.

### 4.2 app.py — 1900 LOC

NOT in this restructure's scope (brief §5: "do NOT Extract Class on it in this restructure"). Documented here for completeness only. app.py imports at L39–L64:

```python
from panels.appearance import AppearancePanel    # canonical post-r1
from panels.parameters import ParametersPanel    # canonical post-r1
from panels.view import ViewPanel                # canonical post-r1
from render_worker import MeshResult, MeshWorker, is_stale_result
from styles import (APP_STYLESHEET, APP_STYLESHEET_DARK, ...)
from surfaces import (VARIETIES, VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS, Surface, dispatch_mode,
                      enriques_figure_1, enriques_figure_2)
```

app.py does NOT import `ui_helpers`, `parameter_grid`, or the shim files. All panel imports already use canonical `panels.*` paths.

### 4.3 styles.py — 708 LOC

Structural breakdown (from grep inspection):
- L1–L83: Module docstring + `PALETTE_LIGHT` dict (all light-theme hex tokens)
- L84–L200: `PALETTE_DARK` dict + `get_variety_default_colors(theme)`
- L201–L330: Backward-compat named exports (`BG_VIEWPORT = PALETTE_LIGHT["BG_VIEWPORT"]`, etc.)
- L331–L418: `_render_stylesheet(palette)` — large f-string QSS template
- L419–L708: `APP_STYLESHEET`, `APP_STYLESHEET_DARK` (two module-level rendered constants)

Qt coupling: the module itself has no PySide6 imports. It is pure Python string/dict. However, it is QSS data authored for Qt's CSS engine — every symbol has a downstream Qt consumer. Classifying as "Qt-coupled" is accurate for structural placement purposes.

---

## 5. Panel/Widget Files Deep Dive

**panels/ subpackage** (introduced in r1, currently at root with `_qt/panels/` as the proposed r2 target):

| File | LOC | Qt coupling | Key outbound API | Key imports |
|---|---|---|---|---|
| `panels/__init__.py` | 13 | none | docstring only | nothing |
| `panels/appearance.py` | 738 | heavy (QWidget subclass) | `apply_to_actor(actor)`, `set_default_color(hex)`, `hq_smoothing` property, `hq_smoothing_changed` Signal | `PySide6`, `icons`, `styles` |
| `panels/parameter_grid_panel.py` | 719 | heavy (QWidget subclass, QGraphicsView scene) | `ParameterGridPanel` widget | `PySide6`, `parameter_grid`, `styles`, `surfaces`, `ui_helpers` |
| `panels/view.py` | 503 | heavy (QWidget subclass) | `clip_to_domain(mesh)`, `domain_settings()`, `re_apply_overlays()` | `PySide6`, `icons`, `numpy`, `pyvista` |
| `panels/parameters.py` | 368 | heavy (QWidget subclass) | `values()`, `reset_to_defaults()` | `PySide6`, `icons`, `panels`, `parameter_grid`, `surfaces`, `ui_helpers` |

**clip_to_domain purity assessment** (brief §3 item, r1 §5.4 claim):

`panels/view.py:L443` defines `clip_to_domain(self, mesh)`. It calls `self.domain_settings()` (L450, L436) which reads:
- `self._domain_mode.currentText()` (QComboBox)
- `self._radius_slider.value() / 100.0` (QSlider)
- `self._domain_overlay_cb.isChecked()` (QCheckBox)

**Verdict: NOT a pure function.** It is a method that reads three widget states. Extracting the geometry-only computation (`clip_scalar` logic) as a standalone pure function requires first extracting a `DomainSettings(mode, radius, show_overlay)` dataclass and having `clip_to_domain` accept that struct, with `ViewPanel.clip_to_domain()` as a thin wrapper. The pure inner function would then be extractable to `cross_section/clip.py` or equivalent.

**Shim files at old paths** (r1 artifact, M+1 removal in r2):

| Shim file | LOC | Points to | Emits |
|---|---|---|---|
| `appearance_panel.py` | 18 | `panels.appearance` | `DeprecationWarning` mentioning `panels.appearance` |
| `view_panel.py` | 18 | `panels.view` | `DeprecationWarning` mentioning `panels.view` |
| `parameters_panel.py` | 18 | `panels.parameters` | `DeprecationWarning` mentioning `panels.parameters` |
| `parameter_grid_panel.py` | 18 | `panels.parameter_grid_panel` | `DeprecationWarning` mentioning `panels.parameter_grid_panel` |

Caller audit:
- `app.py` already imports from `panels.*` canonical paths — NOT from shims.
- `tests/test_panels_shims.py` imports all 4 via old paths intentionally (shim regression guard).
- No other files import from shim paths (confirmed by grep).

**r2 renaming scope:** Brief proposes renaming `panels/` to `_qt/panels/`. This requires:
1. Moving directory: `panels/` → `_qt/panels/`
2. Updating `app.py` imports (`from panels.*` → `from _qt.panels.*`)
3. Updating shim re-export targets (if shims survive into r2)
4. Updating `tests/test_panels_shims.py` expected DeprecationWarning strings
5. Updating `tests/test_clip_domain.py:L21` (`from panels.view import ViewPanel`)
6. Updating `tests/test_styles_palette.py` (imports `panels` module)
7. Updating `panels/__init__.py` docstring paths

---

## 6. Test Layout

**Test runner:** `pytest` (`.venv/bin/python -m pytest`); `testpaths = tests`; **503 tests collected** as of 2026-05-23.

**No `conftest.py`** at root or in `tests/` directory. No `pytest-qt`. AI-2 enforced.

**Test file inventory** (sorted by LOC descending):

| File | LOC | Domain | Key imports |
|---|---|---|---|
| `test_styles_palette.py` | 1262 | QSS/color/WCAG | `styles`, `panels`, `surfaces.VARIETIES`, `surfaces.SUBTYPE_TOOLTIPS` |
| `test_numba_field_kernels.py` | 708 | Numba kernel parity | `surfaces._*_field_kernel` (11 symbols) |
| `test_mesh_export.py` | 451 | Export (STL/OBJ/PLY) | `pathlib` |
| `test_enriques_hq_smoothing.py` | 441 | HQ smoothing | `surfaces` (bare), `surfaces.VARIETIES` |
| `test_mesh_generators.py` | 358 | All generators | `surfaces.*` (all 14 generators) |
| `test_icons.py` | 347 | Icon factories | `icons`, `styles` |
| `test_qsettings_persistence.py` | 343 | QSettings | `pathlib` |
| `test_coarse_n.py` | 323 | coarse_n/LOD | `surfaces.*` (all 14 generators + `VARIETIES`, `Surface`, `dispatch_mode`) |
| `test_parameter_grid.py` | 321 | Parameter math | `surfaces.ParamSpec`, `surfaces.*_PARAMS` (5 families), `parameter_grid.*` |
| `test_render_busy_spinner.py` | 286 | Spinner icon | `icons`, `pathlib` |
| `test_hq_disable_toast.py` | 246 | HQ disable toast | `pathlib` |
| `test_render_worker.py` | 236 | Worker payload | `render_worker.MeshResult`, `.MeshWorker`, `.is_stale_result` |
| `test_status_bar_bbox.py` | 172 | BBox format | `surfaces` (bare: `surfaces.fermat_quartic()` etc.) |
| `test_debounce.py` | 157 | Debouncer | `ui_helpers.Debouncer`, `ui_helpers.DebounceCounter` |
| `test_clip_domain.py` | 147 | Domain clip | `panels.view.ViewPanel` |
| `test_render_queue_latest.py` | 140 | Queue-latest | stdlib only |
| `test_clip_cache.py` | 137 | Clip cache | `app` (whole module) |
| `test_typical_ms.py` | 135 | typical_ms | `surfaces.FAST_RENDER_THRESHOLD_MS`, `.VARIETIES`, `.Surface`, `.should_render_on_drag`, `.calabi_yau_*`, `.fermat_quartic` |
| `test_grid_helpers.py` | 119 | Mesh helpers | `surfaces._grid_to_polydata`, `surfaces._concat_polydata` |
| `test_parameters_panel.py` | 110 | ParamSpec ranges | `surfaces.*_PARAMS` (14 PARAMS constants) |
| `test_panels_shims.py` | 97 | Shim DeprecationWarning | 4 shim modules at old paths |
| `test_marching_cubes_empty.py` | 69 | Empty-mesh guard | `surfaces._marching_cubes_to_polydata`, `surfaces.kummer_surface` |

**Fixture / parametrize patterns:**
- No `conftest.py` fixtures — all fixtures are inline `pytest.fixture` decorators within each test file.
- Heavy use of `@pytest.mark.parametrize` in `test_parameter_grid.py`, `test_mesh_generators.py`, `test_numba_field_kernels.py`.
- `test_clip_cache.py` imports the whole `app` module (L8: `import app`) — this is the one test with a full-module import dependency.

**Critical path locks for r2 (tests that will break on extraction without shims):**

| Test file | Lock | Symbol imported | Required action |
|---|---|---|---|
| `test_numba_field_kernels.py` | **HARD** | `from surfaces import _fermat_field_kernel, ...` (11 names) | shim in `surfaces.py` OR update test to `from varieties._kernels import ...` |
| `test_grid_helpers.py` | HARD | `from surfaces import _grid_to_polydata, _concat_polydata` | shim or update |
| `test_marching_cubes_empty.py` | HARD | `from surfaces import _marching_cubes_to_polydata, kummer_surface` | shim or update |
| `test_parameters_panel.py` | HARD | `from surfaces import FERMAT_PARAMS, ...` (14 `_PARAMS` names) | shim or update |
| `test_parameter_grid.py` | HARD | `from surfaces import FERMAT_PARAMS, ..., ParamSpec` | shim or update |
| `test_typical_ms.py` | HARD | `from surfaces import should_render_on_drag, FAST_RENDER_THRESHOLD_MS` | shim or update |
| `test_coarse_n.py` | HARD | `from surfaces import dispatch_mode, Surface, VARIETIES, ...` (18 names) | shim or update |
| `test_clip_domain.py` | medium | `from panels.view import ViewPanel` | update if `panels/` → `_qt/panels/` |
| `test_styles_palette.py` | medium | `from panels import ...` | update if `panels/` → `_qt/panels/` |
| `test_render_worker.py` | medium | `from render_worker import ...` | update if `render_worker.py` → `render/worker.py` |
| `test_panels_shims.py` | meta | shim DeprecationWarning text | update expected strings if `panels/` renames |

---

## 7. Import Graph

**DAG (in-repo modules only; leaf → hub direction):**

```
surfaces.py
    ↑ (ParamSpec)
parameter_grid.py
    ↑ (parameter_grid + ParamSpec)
ui_helpers.py
    ↑                     ↑
panels/parameters.py   panels/parameter_grid_panel.py

styles.py
    ↑                    ↑
icons.py           panels/appearance.py
                         ↑
                   panels/parameters.py (also via icons)
                   panels/parameter_grid_panel.py (also)

render_worker.py  [no in-repo imports]
    ↑
app.py

panels/view.py    [no in-repo imports beyond numpy/pyvista]
    ↑
app.py

app.py
  → panels.appearance, panels.parameters, panels.view
  → render_worker
  → styles
  → surfaces (VARIETIES, VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS, Surface, dispatch_mode,
               enriques_figure_1, enriques_figure_2)
  → icons
```

**Hub modules** (most imported): `surfaces.py` (imported by 14 test files + `parameter_grid.py` + `ui_helpers.py` + all panel files + `app.py`), `styles.py` (imported by `icons`, `ui_helpers`, `app`, 3 panel files, 2 test files).

**Leaf modules** (import nothing in-repo): `surfaces.py`, `render_worker.py`, `styles.py`, `panels/view.py`.

**Cycles:** NONE detected. The import graph is acyclic. (`styles.py` shows `styles` in the cache `imports-rough.json` but this is the module's own docstring example, confirmed by inspection — no actual `import styles` at module scope in `styles.py`.)

**Cross-package coupling that r2 must handle if `_qt/` subpackage is introduced:**

- `ui_helpers.py` imports `surfaces.ParamSpec` — creates a `_qt/ → varieties/` cross-package dependency if ui_helpers moves to `_qt/`.
- `panels/parameters.py` imports `surfaces` (for generator kwargs) — same cross-package arrow.
- `panels/parameter_grid_panel.py` imports `parameter_grid` and `surfaces` — same pattern.

This is expected and acceptable (Qt adapter layer depending on the domain layer), matching the napari `_qt/ imports domain` pattern.

---

## 8. Tracked-but-Misplaced Files

**Flagged (conservative — only clear cases):**

1. **`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py`** — 4 root-level shim files whose canonical homes are now `panels/`. These are deliberately misplaced by design (M+1 removal contract from r1). Removal is in r2 scope per brief ("every old import path gets a `__getattr__` shim for one milestone").

2. **`render_worker.py`** — A `QRunnable`-based worker that is not an entry point and not a domain module. The brief flags it as a candidate for `render/worker.py`. However it has no other render helpers alongside it today — so the `render/` subpackage would have exactly one file plus `__init__.py`. Low structural justification currently; judgement call.

**Not flagged:**
- `parameter_grid.py` at root — brief calls this a judgement call. It is pure math (no Qt), imports only `surfaces.ParamSpec`. It could live at `varieties/parameter_grid.py` (semantically appropriate) or `root/` (current). The import in `ui_helpers.py` as `import parameter_grid as pg` and `panels/parameters.py` as `import parameter_grid` would require updating.
- `plans/` at root — historical artifacts, not misplaced, not in scope.

---

## 9. `.claude/` Surface Review (scope guard only)

`.claude/` contains **433 tracked files** (confirmed: `git ls-files .claude/ | wc -l`). Note: `.gitignore` only excludes `.claude/worktrees/` and `.claude/scheduled_tasks.lock`; the rest is tracked.

Governance note (from lessons.md): CONTEXT.md:47 says "Don't commit `.claude/`" but .gitignore only excludes `worktrees/` and `scheduled_tasks.lock` — this discrepancy was flagged in r1 and is a documentation gap, not r2 scope.

**This directory is OUT OF SCOPE for r2.** No proposals, no changes.

Relevant subdirectories for context (read-only observation):
- `.claude/references/app-invariants.md` — the AI-1..AI-15 source of truth
- `.claude/notes/repository-architect/` — all restructure outputs land here
- `.claude/agent-memory/` — persistent agent memory

---

## 10. AI-1..AI-15 Inventory

Quotes from `.claude/references/app-invariants.md`. Items flagged with `[R2 AFFECTED]` where r2 restructure must actively preserve them.

**AI-1 — PySide6 + PyVista + pyvistaqt (LGPL-friendly stack)**
> "GUI is PySide6 (LGPL, friendlier than PyQt6's GPL for redistribution). The 3D viewport is `pyvistaqt.QtInteractor`… any candidate that proposes switching to PyQt6 (GPL surface change) or to a non-VTK renderer … is an AI-1 conflict."
> **Compute dependencies are NOT AI-1 conflicts.** `numba` is AI-1 clean.
*r2 impact: NEUTRAL. Moving Numba kernels to `varieties/_kernels.py` does not touch the rendering stack.*

**AI-2 — Test suite is Qt-free (pure NumPy / PyVista / scikit-image)**
> "All 120 tests under `tests/` exercise pure NumPy / PyVista / scikit-image code paths. There is no `pytest-qt`."
*r2 impact: `[R2 AFFECTED]`. Any new test files for `varieties/`, `render/`, `cross_section/` must be Qt-free. Adding pytest-qt to test clip_to_domain extraction is an AI-2 violation. The current `test_clip_domain.py` is already Qt-free (it mocks the widget state via `ViewPanel` construction with offscreen-safe inputs).*

**AI-3 — Render verification is off-screen via `pv.OFF_SCREEN = True`**
> "NEVER construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen`"
*r2 impact: NEUTRAL. No new MainWindow construction proposed.*

**AI-4 — Domain clipping uses `clip_scalar`, not `clip_box`**
> "Both sphere and cube clip modes in `view_panel.py:clip_to_domain` use the scalar-clipping approach"
*r2 impact: `[R2 AFFECTED]`. If `clip_to_domain` logic is extracted to `cross_section/`, the `clip_scalar` pattern must be preserved verbatim. AI-4 + AI-5 are contract owners for any cross_section/ extraction.*

**AI-5 — PyVista 0.46+ `clip_scalar` requires `scalars=` keyword**
> "`mesh.clip_scalar(scalars='_dist', value=r, invert=True)` — RIGHT"
*r2 impact: `[R2 AFFECTED]`. Any extraction of clip logic must preserve the keyword form.*

**AI-6 — Implicit surfaces use marching cubes; parametric surfaces do NOT**
> "Implicit surface generators… call `_marching_cubes_to_polydata(field, bounds)`. Parametric surfaces… call `_grid_to_polydata(X, Y, Z)` + `_concat_polydata(meshes)`. Hanson cross-sections **intentionally skip Taubin smoothing**."
*r2 impact: `[R2 AFFECTED]`. If `_marching_cubes_to_polydata`, `_grid_to_polydata`, `_concat_polydata` move to `varieties/_marching.py`, each generator module must import from the new path. The `numba.config` side effect must travel with kernels.*

**AI-7 — Hanson normals: `cell_normals=True, consistent_normals=False, auto_orient_normals=False`**
> "Hanson cross-sections are 9–25 disconnected components… use `cell_normals=True, consistent_normals=False, auto_orient_normals=False`"
*r2 impact: NEUTRAL. Normal handling stays inside the Hanson generator functions; extraction doesn't change the kwarg values.*

**AI-8 — `Surface` / `ParamSpec` dataclass contract (frozen registry)**
> "All surfaces enter the GUI through the `VARIETIES` registry in `surfaces.py`… `VARIETIES: dict[str, dict[str, Surface]] = { ... }`"
> "Two parallel tooltip dicts (`VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS`) are also exported from `surfaces.py`"
*r2 impact: `[R2 AFFECTED — HIGH PRIORITY]`. Brief specifies: "must remain importable via `from varieties.registry import VARIETIES`". But `app.py` currently uses `from surfaces import VARIETIES, VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS` and this must continue to work (shim required in `surfaces.py`). AI-8 says "stable path" — it does not say "must stay in surfaces.py" — so moving to `varieties/registry.py` with a shim in `surfaces.py` satisfies AI-8.*

**AI-9 — Re-entrancy guard `self._computing` around `processEvents()`**
> "`_render_current` is *submit-only* and returns immediately. There is **no `QApplication.processEvents()` call anymore**"
*r2 impact: NEUTRAL. The guard pattern lives in `app.py` which is not in scope.*

**AI-10 — Raw mesh cached; domain clip doesn't regenerate**
> "`self._raw_mesh` is the un-clipped mesh. `_on_domain_changed` calls `_apply_domain_and_render` directly without regenerating the mesh"
*r2 impact: NEUTRAL. Cache pattern lives in `app.py`.*

**AI-11 — Fully-qualified Qt enums**
> "PySide6 prefers fully-qualified enum forms: `Qt.AlignmentFlag.AlignLeft`, `QSizePolicy.Policy.Expanding`"
*r2 impact: `[R2 AFFECTED]`. Any new Qt code in `_qt/` subpackage or helpers must use fully-qualified forms.*

**AI-12 — WCAG AA text-contrast on all visible text**
> "`COLOR_MUTED = #5a5a5a` on `#f0f0f0` ≈ 5.4:1 (WCAG AA pass)"
*r2 impact: NEUTRAL. Structural moves don't change color values.*

**AI-13 — 6-digit hex only (PyVista color parser)**
*r2 impact: NEUTRAL.*

**AI-14 — Generator function contract: `pv.PolyData` or `ValueError`**
> "Every generator returns a `pv.PolyData`. Implicit generators raise `ValueError('No real zero set...')` when the field has no zero crossing."
*r2 impact: `[R2 AFFECTED]`. Moving generators to `varieties/*.py` must preserve the `ValueError` contract. The `_marching_cubes_to_polydata` zero-crossing guard must remain co-located with its callers.*

**AI-15 — Math claim honesty: ≥2 sources + honest "real shadow" disclaimers**
*r2 impact: NEUTRAL for structural moves. Moving tooltip strings to `varieties/registry.py` doesn't change their content.*

---

## 11. CONTEXT.md Sections Quoted

### Section 4 (Architecture conventions) — key extracts

**§4.1 The Surface dataclass + VARIETIES registry:**
> "All surfaces are uniform from the GUI's POV… `VARIETIES: dict[str, dict[str, Surface]]` … Two parallel tooltip dicts — `VARIETY_TOOLTIPS` and `SUBTYPE_TOOLTIPS` — are also exported from `surfaces.py` and consumed by `app.py`"

**§4.2 Generator function contract:**
> "Every generator returns a `pyvista.PolyData`. Implicit generators use `_marching_cubes_to_polydata(field, bounds)`… Parametric generators… use `_grid_to_polydata(X, Y, Z)` + `_concat_polydata(meshes)`"
> "Hanson cross-sections **intentionally skip Taubin smoothing**"

**§4.3 MainWindow render pipeline:**
> ```
> panels.view.clip_to_domain(self._raw_mesh)  → (clipped, overlay)
>   ↓
> plotter.add_mesh(clipped) → self._actor
> ```

**§4.3b Theme system:**
> "Panel files must NEVER do `label.setStyleSheet(MUTED_TEXT_STYLE | VALUE_MONO_STYLE | RANGE_LABEL_STYLE)` — those constants hardcode `PALETTE_LIGHT` colors and OVERRIDE the dark QSS cascade"

**§4.4 Re-entrancy guard (post e4):**
> "`_render_current(reset_camera=…)` — if `self._computing` (a worker is in flight), records `_pending_render`… **All VTK GL calls stay on the GUI thread — the worker only touches `surface.generate()` data construction.**"

**§4.5 Domain clipping:**
> "`panels/view.py` exposes `clip_to_domain(mesh) -> (clipped_mesh, overlay_mesh_or_None)`. Both modes use the same scalar-clipping approach… Don't use `clip_box`"

### Section 9 (Things explicitly NOT done)

> "No tests for app.py / MainWindow. The test suite is all pure-NumPy / pure-PyVista / static-math tests. Adding `pytest-qt` would let us test the dropdown wiring and dock layout, but Qt+VTK segfaults under offscreen on macOS prevent end-to-end smoke tests in CI."
> "No automated test for the background-thread worker lifecycle … The `QThreadPool` dispatch, the `QueuedConnection` signal delivery, the `_computing` queue-latest coalescing … all need a running `QApplication` event loop, i.e. `pytest-qt` — an AI-2 BLOCKER."

### Section 12 (Final state at handoff)

> "113+ commits on `main` … 499 tests passing in ~7 s [note: currently 503 post-r1] … Four varieties live: K3 (2 subtypes), Enriques (4 figures), Calabi–Yau (4 figures), Fano 3-fold (4 figures) … Numba JIT field kernels for all 11 implicit generators (workqueue threading layer)"

---

## 12. README Extension Path Quoted

From `README.md` "Extending the app" section (lines 308–326):

> **Adding a new model to an existing variety** is straightforward:
>
> 1. Write a generator function in `surfaces.py` that returns a `pv.PolyData`. Implicit generators sample a scalar field on a cubic grid and call `_marching_cubes_to_polydata(field, bounds)`. Parametric generators build `(X, Y, Z)` 2D arrays and call `_grid_to_polydata(X, Y, Z)`.
> 2. Define a `<NAME>_PARAMS` list of `ParamSpec(name, label, minimum, maximum, default, step, suffix, description)` — one per slider.
> 3. Add `Surface(label, generator, params)` to the appropriate inner dict of `VARIETIES`. Use a `[Fig. N]` suffix in the dropdown key for consistency.
> 4. Add tooltip entries to `SUBTYPE_TOOLTIPS` (and `VARIETY_TOOLTIPS` if introducing a new family).
> 5. Add at least a smoke test in `tests/test_mesh_generators.py` and a parameter-range entry in `tests/test_parameters_panel.py`.
>
> **Adding a whole new variety family** is a larger effort — see Section 6 of `CONTEXT.md` for the 5-phase pipeline.

**r2 impact on this path:** After r2, step 1 will say "write a generator function in `varieties/<family>.py`" and step 3 will say "add to `VARIETIES` in `varieties/registry.py`". The README is authorized for Batch 4+ rewrite. The extension path must continue to work — any new generator must be registerable without touching `app.py` or `surfaces.py` directly.

---

## 13. Honest Assessment

### Already good (don't fix)

1. **panels/ subpackage structure from r1.** The 4 panel files are cleanly extracted with `__init__.py` and proper docstrings. The `panels/` directory is a solid foundation for the `_qt/panels/` rename.
2. **app.py already uses canonical `panels.*` imports.** The r1 import update was done correctly — no cleanup needed there.
3. **503 tests, Qt-free.** The test suite is comprehensive for the non-Qt surfaces. `test_numba_field_kernels.py` at 708 LOC provides strong kernel extraction safety net.
4. **surfaces.py section banners.** The `# ------` banners already demarcate the 7 logical sections. The seams are real, not cosmetic — each section has a single responsibility.
5. **numba.config side-effect documentation.** The 18-line comment at L19–L36 in `surfaces.py` explicitly documents the process-global side effect. This is the right level of documentation for an extraction risk.
6. **AI-invariants.md is comprehensive and up-to-date.** All 15 invariants are well-documented with file:line references.
7. **MOVES.md rosetta stone pattern.** The r1 move table is clean. r2 should extend it.

### Clearly bad (genuine quick wins)

1. **4 shim files at root (appearance_panel.py etc.)** — These are M+1 artifacts. r2 is M+1. Remove after confirming only `test_panels_shims.py` uses them (confirmed). Single-step removal: delete 4 files + update `test_panels_shims.py` to import from new canonical paths directly.
2. **`parameter_grid_panel.py` naming inside `panels/`.** The file is `panels/parameter_grid_panel.py` — it should be `panels/parameter_grid.py` (a widget for the parameter grid) but was kept as `parameter_grid_panel.py` for historical consistency with the shim. r2 rename opportunity: `panels/parameter_grid_panel.py` → `_qt/panels/parameter_grid.py` (both rename steps happen in same batch).
3. **surfaces.py Numba kernels section (L285–L685, 401 LOC)** — These 11 functions have zero in-repo imports, take only numpy arrays, and have no side effects beyond computation. Extracting to `varieties/_kernels.py` is mechanically straightforward. The only blocker is the `numba.config.THREADING_LAYER` side-effect which must be preserved in `surfaces.py` import order or moved to `varieties/__init__.py`.

### Debatable (context-dependent)

1. **`parameter_grid.py` placement.** Currently at root, imports only `surfaces.ParamSpec`. Three candidate locations:
   - Stay at root (current) — simplest, no import changes except in new `varieties/` code.
   - `varieties/parameter_grid.py` — semantically correct (it's math for variety parameters), but creates `varieties → varieties.parameter_grid` self-reference awkwardness.
   - `_qt/parameter_grid.py` — wrong; it has no Qt coupling at all.
   The root-or-varieties question is a design decision. Evidence for varieties/: it imports ParamSpec which will be in varieties/. Evidence for root/: it's consumed by ui_helpers and panels (UI layer, not variety layer) — keeping it at root avoids a `_qt/ → varieties/` cross-package dep.

2. **`render/` subpackage for render_worker.py alone.** A subpackage with 1 file + `__init__.py` is minimal overhead but adds import path distance. Counter-argument: naming the subpackage `render/` is forward-compatible if render helpers emerge. The current 225-LOC file is fully standalone.

3. **`clip_to_domain` extraction to `cross_section/`.** The brief identifies this as a "PURE function" but the code analysis shows it reads widget state. To make it extractable as a pure function, a `DomainSettings` dataclass would need to be introduced first. That's a two-step, not a one-step move. Design decision: is a `cross_section/` subpackage worth the 2-step cost for a 30-LOC geometry function? The test `test_clip_domain.py` currently tests `ViewPanel.clip_to_domain()` directly — keeping the method in `panels/view.py` (or `_qt/panels/view.py`) with the geometry factored into an internal helper would achieve the same testability.

4. **`_qt/` underscore-prefix convention.** Napari-style underscore-prefix signals "framework adapter, don't import directly." This is a documentation signal more than an import barrier (Python doesn't enforce it). Whether AVC needs this convention is a design call — it adds clarity but also adds friction for people extending the app (they have to know to look in `_qt/`).

5. **`styles.py` in `_qt/`.** `styles.py` is pure Python strings/dicts with no PySide6 imports. It is "Qt-coupled" only by content. Placing it in `_qt/styles.py` is semantically honest but makes `from _qt.styles import …` odd for the WCAG contrast tests and any future non-Qt consumers.

---

## 14. Files the Restructure CANNOT Touch Without Lifting an Invariant

| File | Line/Reference | Invariant | Why it Cannot Be Changed |
|---|---|---|---|
| `surfaces.py` (numba config block) | L19–L39; CONTEXT.md §3 | AI-6, process contract | `numba.config.THREADING_LAYER = "workqueue"` is a process-global side effect documented as intentional. ANY extraction of Numba kernels must either keep this in `surfaces.py` (re-exporting) or move it to the first-imported module of the new `varieties/` package (`varieties/__init__.py`). Cannot silently remove it. |
| `surfaces.py` (ParamSpec/Surface dataclasses) | L42–L98; app-invariants.md AI-8 | AI-8 | `Surface` and `ParamSpec` must remain co-importable from a stable path. `from surfaces import Surface, ParamSpec` is the current contract. Any move requires a `surfaces.py` re-export shim. |
| `surfaces.py` (`VARIETIES`, `VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS`) | L1555, L1652, L1720; app-invariants.md AI-8 | AI-8 | `app.py:L49–L63` imports these by name from `surfaces`. Brief allows relocation to `varieties/registry.py` only if `surfaces.py` re-exports them. Do NOT rename or remove these symbols. |
| `tests/test_numba_field_kernels.py:L53–L65` | tests/test_numba_field_kernels.py:53 | AI-2, brief hard constraint | Brief explicitly: "tests/test_numba_field_kernels.py specifically uses `from surfaces import _<name>_field_kernel` — preserve this." Cannot update this test to use new paths without a shim at `surfaces.py`. |
| `panels/view.py:L443–L477` (`clip_to_domain`) | panels/view.py:443; CONTEXT.md §4.5; AI-4, AI-5 | AI-4, AI-5 | The `clip_scalar(scalars=…)` pattern is an invariant. Cannot be replaced with `clip_box`. The `scalars=` keyword form is mandatory (AI-5). Any extraction must preserve both. |
| `panels/appearance.py` (hq_smoothing pattern) | panels/appearance.py; CONTEXT.md §4.3a | AI-6 | `enriques_figure_1` / `enriques_figure_2` have special `hq_smoothing` kwarg coupling to `AppearancePanel`. The signal/slot pattern (`hq_smoothing_changed → _on_hq_smoothing_changed → _render_current`) cannot be broken by moving panels. |
| `app.py` (`_computing` guard, `_render_current`, `_on_mesh_ready`) | app.py; CONTEXT.md §4.4; AI-9 | AI-9 | Re-entrancy guard. NOT in scope for r2 but must not be broken by changes to modules app.py imports. |
| `render_worker.py` (`VTK #18782` comment, `self._result` retention) | render_worker.py:L165–L175 | AI-9, VTK compat | `self._result = result.mesh` retention prevents VTK GC crash. Cannot be removed when moving to `render/worker.py`. |
| `styles.py` (role-property QSS selectors) | styles.py; CONTEXT.md §4.3b; AI-12 | AI-12 | All dark-mode QSS role selectors (`[role="muted"]`, `[role="value-mono"]`, etc.) must remain in the rendered stylesheet. Moving `styles.py` to `_qt/styles.py` cannot break these. |
| `pyproject.toml` | root | explicit scope exclusion | Brief and CONTEXT.md: do not modify `requirements.txt` or `pyproject.toml` during restructure. |
| `pytest.ini` | root | explicit scope exclusion | `testpaths = tests` must remain. |
| `.github/` | root | explicit scope exclusion | CI workflows are out of scope. |

---

*Brief written by repository-architect-current-state-auditor for restructure-feature-subpackages-2026q2-r2.*
*All LOC counts from `wc -l` on current working tree; all line ranges verified via grep/sed.*
*503 tests confirmed passing (project venv `.venv/bin/python -m pytest`, 2026-05-23).*
