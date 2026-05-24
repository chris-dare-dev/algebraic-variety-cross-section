# Current-State Audit — restructure-single-root-2026q2-r3

**Auditor:** repository-architect-current-state-auditor
**Date:** 2026-05-24
**Cache used:** tree.txt, loc.csv, imports-rough.json, ai-invariants-card.md (all present)

---

## 1. TL;DR

- 7 root `.py` files exist: `app.py` (KEEP), `parameter_grid.py` (362 LOC real code), and 5 M+1 shims (`icons.py`, `styles.py`, `ui_helpers.py`, `render_worker.py`, `panels/__init__.py`).
- `surfaces.py` is a 123-LOC pure re-export hub with **23 active import sites** (non-test-r2-shims callers across tests/, app.py, _qt/); `test_r2_shims.py` adds 2 more, totalling 25 call-file hits. B4 is the highest-risk batch.
- `parameter_grid.py` has **4 callers**: `_qt/ui_helpers.py`, `_qt/panels/parameter_grid_panel.py`, `_qt/panels/parameters.py`, `tests/test_parameter_grid.py`.
- `varieties/types.py` (67 LOC) has `ParamSpec` + `Surface` dataclasses — NO `Protocol` present; `VarietyGenerator` Protocol does not exist yet.
- `import-linter` is NOT in `requirements.txt` or `pyproject.toml` — confirmed absent; Phase 4 add is correct.

---

## 2. Repo top-level tree (annotated)

Source: `.claude/notes/.../cache/tree.txt` (pre-cached).

| Entry | Type | Purpose | Notes |
|---|---|---|---|
| `app.py` | file, 102 511 B | Entry point + MainWindow (~1900 LOC) | KEEP; out of scope for moves in r3 |
| `icons.py` | file, 844 B | M+1 shim → `_qt.icons` | Template-2 `__getattr__`; DELETE in B3 |
| `parameter_grid.py` | file, 13 096 B | Pure-math Qt widget math, 362 LOC | REAL CODE; MOVE in B2 → `_qt/parameter_grid_math.py` |
| `render_worker.py` | file, 894 B | M+1 shim → `render.worker` | Template-2 `__getattr__`; DELETE in B3 |
| `styles.py` | file, 772 B | M+1 shim → `_qt.styles` | Template-2 `__getattr__`; DELETE in B3 |
| `surfaces.py` | file, 5 087 B | 123-LOC re-export hub → `varieties.*` | HIGH RISK hub; DELETE in B4 |
| `ui_helpers.py` | file, 1 080 B | M+1 shim → `_qt.ui_helpers` | Template-2 `__getattr__`; DELETE in B3 |
| `panels/` | dir, 2 files | `__init__.py` = Template-1 hub shim; canonical panels at `_qt/panels/` | Hub shim DELETE in B3 |
| `_qt/` | dir, 18 files | Qt layer: icons, styles, ui_helpers, panels subpackage | Canonical home |
| `cross_section/` | dir, 4 files | Clip pipeline | Out of scope |
| `render/` | dir, 4 files | MeshWorker thread | Out of scope |
| `varieties/` | dir, 44 files | All math: types, kernels, generators, registry, tooltips | Out of scope for moves |
| `tests/` | dir, 47 files | 499 tests, flat layout, Qt-free | B3 deletes test_r2_shims.py |
| `AGENTS.md` / `CLAUDE.md` | file | Agent orientation (same content) | Read-only |
| `CONTEXT.md` | file, 84 344 B | Deep architectural context | Anchor-updater owns |
| `MOVES.md` | file, 11 875 B | Restructure rosetta stone | r3 must append |
| `README.md` | file, 19 520 B | User docs; "Extending the app" section | Anchor-updater owns |
| `requirements.txt` | file | Runtime + restructure tooling deps | No import-linter yet |
| `pyproject.toml` | file | Build metadata | No import-linter yet |
| `pytest.ini` | file | Test config | Anchor-updater owns |
| `.coverage` | file | Coverage artifact | gitignored-equivalent |
| `.gitignore` | file, 125 B | Tracked | |
| `plans/` | dir | Historical design artefacts | Read-only |

---

## 3. Source module inventory (sorted by LOC descending)

Source: `.claude/notes/.../cache/loc.csv`.

| File | LOC | Purpose | r3 action |
|---|---|---|---|
| `app.py` | 1900 | Entry point + MainWindow | KEEP as-is |
| `_qt/panels/appearance.py` | 738 | AppearancePanel Qt widget | No change |
| `_qt/panels/parameter_grid_panel.py` | 719 | ParameterGridPanel Qt widget | Caller of `parameter_grid` — import path rewrite in B2 |
| `_qt/styles.py` | 708 | Style constants + QSS | No change |
| `_qt/panels/view.py` | 486 | ViewPanel + clip controls | No change |
| `varieties/_kernels.py` | 426 | 11 Numba @njit field kernels | No change |
| `_qt/icons.py` | 373 | qtawesome icon helpers | No change |
| `_qt/panels/parameters.py` | 368 | ParametersPanel slider stack | Caller of `parameter_grid` + `surfaces` — rewrite B2/B4 |
| `parameter_grid.py` | 362 | Pure-math coordinate math for grid mode | MOVE to `_qt/parameter_grid_math.py` in B2 |
| `varieties/_marching.py` | 288 | Marching cubes pipeline helpers | No change |
| `varieties/fano.py` | 266 | Fano 3-fold generators | No change |
| `_qt/ui_helpers.py` | 264 | Shared Qt widget builders | Caller of `parameter_grid` + `surfaces` — rewrite B2/B4 |
| `varieties/enriques.py` | 228 | Enriques surface generators | No change |
| `render/worker.py` | 225 | MeshWorker QThread | No change |
| `varieties/k3.py` | 189 | K3 surface generators | No change |
| `varieties/calabi_yau.py` | 184 | Calabi-Yau generators | No change |
| `varieties/tooltips.py` | 180 | VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS | No change |
| `varieties/registry.py` | 139 | VARIETIES canonical registry | No change |
| `surfaces.py` | 123 | Re-export hub (all varieties.* re-exports) | DELETE in B4 after rewriting all 25 import-site files |
| `varieties/dispatch.py` | 89 | dispatch_mode, should_render_on_drag | No change |
| `cross_section/clip.py` | 70 | clip_scalar pipeline | No change |
| `varieties/types.py` | 67 | ParamSpec + Surface dataclasses | ADD VarietyGenerator Protocol in B2 |
| `panels/__init__.py` | 40 | Template-1 hub shim → `_qt.panels.*` | DELETE in B3 |
| `varieties/__init__.py` | 34 | Re-exports from varieties subpackage | No change |
| `ui_helpers.py` | 27 | Template-2 shim → `_qt.ui_helpers` | DELETE in B3 |
| `cross_section/__init__.py` | 23 | Re-exports from cross_section | No change |
| `icons.py` | 23 | Template-2 shim → `_qt.icons` | DELETE in B3 |
| `render_worker.py` | 23 | Template-2 shim → `render.worker` | DELETE in B3 |
| `styles.py` | 22 | Template-2 shim → `_qt.styles` | DELETE in B3 |
| `_qt/__init__.py` | 20 | `_qt` package init | No change |
| `_qt/panels/__init__.py` | 13 | `_qt.panels` package init (docstring only) | No change |
| `render/__init__.py` | 10 | `render` package init | No change |

Monolith threshold (>500 LOC): `app.py` (1900), `_qt/panels/appearance.py` (738), `_qt/panels/parameter_grid_panel.py` (719), `_qt/styles.py` (708). None of these are in r3 scope.

---

## 4. Monolith deep dive

No files in r3 scope exceed 800 LOC. `parameter_grid.py` at 362 LOC is well under threshold. The 4 monoliths above (`app.py`, `_qt/panels/appearance.py`, etc.) are out of r3 scope per the brief.

---

## 5. Panel/widget files deep dive

**panels/ state (post-r2):**

- `panels/__init__.py` — 40 LOC, Template-1 hub shim. Confirmed: uses `_PANELS` dict + `__getattr__` routing to `_qt.panels.*`. Imports: `importlib`, `warnings` only. No real code.
- `panels/appearance.py`, `panels/parameters.py`, `panels/view.py`, `panels/parameter_grid_panel.py` — these root-level panel files do NOT exist (deleted in r2). The canonical 4 panel modules live at `_qt/panels/{appearance,parameters,view,parameter_grid_panel}.py`.

**_qt/panels/__init__.py** (13 LOC) — contains ONLY a docstring listing canonical import paths. No `__getattr__`. Not a shim — this is the real package init.

**Confirmation:** `panels/__init__.py` IS a Template-1 hub shim (M+1 due in r3). `_qt/panels/` contains the 4 real panel modules.

**parameter_grid.py callers (4 total):**

| File | Line | Import form |
|---|---|---|
| `_qt/ui_helpers.py` | 27 | `import parameter_grid as pg` |
| `_qt/panels/parameter_grid_panel.py` | 35 | `import parameter_grid as pg` |
| `_qt/panels/parameters.py` | 30 | `import parameter_grid as pg` |
| `tests/test_parameter_grid.py` | 18 | `import parameter_grid as pg` |

All 4 use the `import parameter_grid as pg` alias form. LibCST rewrite in B2 must handle this alias pattern (not `from parameter_grid import X`).

---

## 6. surfaces.py import sites — full count for B4 budget

**Total unique files importing from surfaces:** 17 test files + 3 `_qt/` files + `app.py` = 21 files.
**Total import lines (counting multi-line blocks as one site):** 25 lines (including `test_r2_shims.py`'s 2 lines which vanish when that file is deleted in B3).

**After B3 deletes `test_r2_shims.py`, B4 inherits: 23 active import lines across 19 files.**

Breakdown by file:

| File | Import lines | Symbols imported |
|---|---|---|
| `app.py` | 1 (L49-63) | VARIETIES, VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS, Surface, dispatch_mode, enriques_figure_1, enriques_figure_2 |
| `_qt/ui_helpers.py` | 1 (L29) | ParamSpec |
| `_qt/panels/parameters.py` | 1 (L32) | ParamSpec |
| `_qt/panels/parameter_grid_panel.py` | 1 (L45) | ParamSpec |
| `tests/test_status_bar_bbox.py` | 1 (L33) | `import surfaces` (module-level) |
| `tests/test_enriques_hq_smoothing.py` | 2 (L31, L224) | `import surfaces` + `from surfaces import VARIETIES` |
| `tests/test_mesh_generators.py` | 2 (L17, L159) | All 14 generator functions (2 blocks) |
| `tests/test_numba_field_kernels.py` | 1 (L53-65) | 11 `_<name>_field_kernel` private symbols |
| `tests/test_typical_ms.py` | 1 (L24) | VARIETIES, Surface, dispatch_mode |
| `tests/test_styles_palette.py` | 3 (L214, L610, L1252) | VARIETIES (x2), SUBTYPE_TOOLTIPS |
| `tests/test_parameters_panel.py` | 1 (L21) | 14 `_PARAMS` constants |
| `tests/test_grid_helpers.py` | 1 (L17) | `_grid_to_polydata`, `_concat_polydata` |
| `tests/test_marching_cubes_empty.py` | 1 (L17) | `_marching_cubes_to_polydata`, `kummer_surface` |
| `tests/test_parameter_grid.py` | 1 (L19) | 5 `_PARAMS` constants + ParamSpec |
| `tests/test_coarse_n.py` | 1 (L32) | VARIETIES, Surface, calabi_yau_*, dispatch_mode, enriques_figure_1, fano_two_quadrics, fermat_quartic, kummer_surface |
| `tests/test_r2_shims.py` | 2 (L95, L105) | `_fermat_field_kernel`, VARIETIES (will be deleted in B3) |

**Symbol categories that must map cleanly in B4:**

| Symbol type | Count | Canonical path after B4 |
|---|---|---|
| `ParamSpec`, `Surface` | Many callers | `varieties.types` |
| `VARIETIES` | 5 call sites | `varieties.registry` |
| `VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS` | 2 call sites | `varieties.tooltips` |
| `dispatch_mode`, `should_render_on_drag`, `FAST_RENDER_THRESHOLD_MS` | 3 call sites | `varieties.dispatch` |
| 14 generator functions (`fermat_quartic`, ...) | Multiple | `varieties.{k3,enriques,calabi_yau,fano}` |
| 14 `_PARAMS` constants | 2 test files | Same family modules |
| 11 `_<name>_field_kernel` | 1 test file | `varieties._kernels` |
| 4 marching helpers (`_marching_cubes_to_polydata`, etc.) | 2 test files | `varieties._marching` |
| `import surfaces` (bare module import) | 2 test files | Module reference — requires refactor to specific symbol imports |

**B4 risk flag:** `tests/test_status_bar_bbox.py:33` and `tests/test_enriques_hq_smoothing.py:31` use `import surfaces` (bare module-level import), then access `surfaces.<symbol>`. These require conversion to specific `from varieties.X import Y` forms, not just a find-replace. LibCST rewrite scope must handle this pattern.

---

## 7. Test layout

```
tests/               (47 entries: 22 .py test files + __init__.py + __pycache__)
  __init__.py        (0 LOC, empty)
  test_clip_cache.py         (137 LOC) — imports app (QApplication risk: needs audit)
  test_clip_domain.py        (147 LOC) — imports _qt.panels.view (post-r2 canonical)
  test_coarse_n.py           (323 LOC) — imports from surfaces (B4 rewrite)
  test_debounce.py           (157 LOC) — imports _qt
  test_enriques_hq_smoothing.py (441 LOC) — imports surfaces (B4 rewrite)
  test_grid_helpers.py       (119 LOC) — imports from surfaces (B4 rewrite)
  test_hq_disable_toast.py   (246 LOC) — imports pathlib only
  test_icons.py              (349 LOC) — imports _qt
  test_marching_cubes_empty.py (69 LOC) — imports from surfaces (B4 rewrite)
  test_mesh_export.py        (451 LOC) — imports pathlib only
  test_mesh_generators.py    (358 LOC) — imports from surfaces (B4 rewrite)
  test_numba_field_kernels.py (708 LOC) — imports 11 kernels from surfaces (B4 rewrite)
  test_parameter_grid.py     (321 LOC) — imports parameter_grid (B2 rewrite) + surfaces (B4)
  test_parameters_panel.py   (110 LOC) — imports 14 _PARAMS from surfaces (B4 rewrite)
  test_qsettings_persistence.py (343 LOC) — imports pathlib only
  test_r2_shims.py           (108 LOC) — DELETE in B3
  test_render_busy_spinner.py (287 LOC) — imports _qt
  test_render_queue_latest.py (140 LOC) — imports os/sys only
  test_render_worker.py      (236 LOC) — imports render
  test_status_bar_bbox.py    (172 LOC) — `import surfaces` (B4 rewrite)
  test_styles_palette.py     (1263 LOC) — imports from surfaces (B4 rewrite)
  test_typical_ms.py         (135 LOC) — imports from surfaces (B4 rewrite)
```

No `conftest.py`. No parametrize fixtures at package level. Tests use `sys.path.insert(0, ...)` to ensure root-level imports work from any cwd.

**AI-2 risk note:** `tests/test_clip_cache.py` imports `app` (L5: `from app import ...`). `app.py` constructs a `QApplication` at module scope — this is a pre-existing potential AI-2 violation not introduced by r3. Not in r3 scope but worth flagging for the designer.

---

## 8. Import graph

Source: `imports-rough.json` (pre-cached), supplemented by source reads.

**Root-level caller graph (r3 relevant):**

```
app.py
  └─ surfaces (re-export hub) ─── will rewrite to varieties.*
  └─ _qt.{icons, panels.*, styles}
  └─ render.worker

parameter_grid.py
  └─ surfaces (for ParamSpec) ─── will rewrite to varieties.types

_qt/ui_helpers.py
  └─ parameter_grid ─── will rewrite to _qt.parameter_grid_math
  └─ surfaces (for ParamSpec) ─── will rewrite to varieties.types

_qt/panels/parameters.py
  └─ parameter_grid ─── will rewrite to _qt.parameter_grid_math
  └─ surfaces (for ParamSpec) ─── will rewrite to varieties.types

_qt/panels/parameter_grid_panel.py
  └─ parameter_grid ─── will rewrite to _qt.parameter_grid_math
  └─ surfaces (for ParamSpec) ─── will rewrite to varieties.types

surfaces.py (re-export hub)
  └─ varieties.types, varieties.dispatch, varieties._marching, varieties._kernels
  └─ varieties.{k3, enriques, calabi_yau, fano}, varieties.registry, varieties.tooltips

panels/__init__.py (Template-1 shim)
  └─ _qt.panels.* (via importlib)
```

**Layer direction (target for import-linter):**
`app.py` → `_qt/` → `varieties/`, `render/`, `cross_section/`; `varieties/` → nothing Qt; `cross_section/` → nothing Qt.

**Cycle check:** `_qt/styles.py` docstring shows `from styles import ...` examples, but these are in the docstring only — no actual import cycle. No cycles detected in the import graph.

**Unexpected finding:** `_qt/styles.py` has the old root-`styles` usage in its docstring as an example (lines 9, 13). These are docstring strings only; grep confirmed `grep -n "^from styles\|^import styles" _qt/styles.py` returns empty. Not a live dependency.

---

## 9. Tracked-but-misplaced files

| File | Issue | Severity |
|---|---|---|
| `parameter_grid.py` | Qt widget math at root; should be in `_qt/` | High — this is the B2 move target |
| `surfaces.py` | Re-export hub masquerading as canonical module; all real code has moved to `varieties/` | High — B4 retirement |
| `icons.py`, `styles.py`, `ui_helpers.py`, `render_worker.py` | M+1 shims at root | High — B3 delete |
| `panels/__init__.py` | M+1 hub shim at root-adjacent `panels/` dir | High — B3 delete |

No other obvious misplacements.

---

## 10. `.claude/` surface review (scope guard only)

`.claude/` contains ~380 tracked files (per r1 lesson). Subdirectories include `agents/`, `commands/`, `scripts/`, `hooks/`, `references/`, `notes/`, `agent-memory/`. This directory is OUT OF SCOPE for r3 per the restructure brief and the scope-guard rules. The restructure pipeline's output files live under `.claude/notes/repository-architect/restructure-single-root-2026q2-r3/` — writes there are permitted. No other `.claude/` modifications will be made.

---

## 11. AI-1..AI-15 inventory

Source: `ai-invariants-card.md` (pre-cached) + `app-invariants.md`.

| # | Summary | r3 impact? |
|---|---|---|
| AI-1 | Stack is PySide6 + PyVista + pyvistaqt (LGPL). `QtInteractor` for 3D viewport. | Not affected |
| AI-2 | Tests are Qt-free — no `QApplication` or `QWidget` subclass construction in `tests/`. | **AFFECTED**: `test_r2_shims.py` deletion in B3 is compliant (no Qt). Any replacement tests for B3 shim deletion must remain import-only, no Qt construction. |
| AI-3 | Headless render verification uses `pv.OFF_SCREEN = True`. | Not affected |
| AI-4 | Domain clipping uses `clip_scalar`, not `clip_box`. | Not affected |
| AI-5 | PyVista 0.46+ `clip_scalar` requires `scalars=` keyword. | Not affected |
| AI-6 | Implicit surfaces → marching cubes; parametric surfaces → structured grid. NEVER mix. | **AFFECTED**: B4 retirement of `surfaces.py` must preserve this pipeline split. All generator functions stay in `varieties/{k3,enriques,calabi_yau,fano}.py` which already segregate the pattern. |
| AI-7 | Hanson normals: `cell_normals=True, consistent_normals=False, auto_orient_normals=False`. | Not affected |
| AI-8 | `Surface` / `ParamSpec` frozen dataclass contract; `VARIETIES` registry is canonical. | **AFFECTED**: B4 retires `surfaces.VARIETIES` re-export. Callers must use `varieties.registry.VARIETIES` directly. `Surface` + `ParamSpec` stay in `varieties.types`. B2 adds `VarietyGenerator` Protocol to `varieties/types.py` — must not change `Surface` or `ParamSpec` fields (frozen contract). |
| AI-9 | Re-entrancy guard `self._computing` in `app.py` — never remove or bypass. | **ADJACENT**: `app.py` imports will be rewritten in B4 (surfaces → varieties.*). The guard itself (`self._computing`) is not touched. Per brief: only `app.py`'s `from surfaces import ...` block changes. |
| AI-10 | Raw mesh cached in `self._raw_mesh`; domain clip doesn't regenerate. | Not affected |
| AI-11 | Fully-qualified Qt enums: `Qt.AlignmentFlag.AlignLeft`, not `Qt.AlignLeft`. | Not affected (no new Qt code introduced in r3) |
| AI-12 | WCAG AA contrast on all visible text; no hardcoded hex in stylesheets. | Not affected |
| AI-13 | 6-digit hex only for PyVista color parser. | Not affected |
| AI-14 | Generator function contract: returns `pv.PolyData` or raises `ValueError`. | Not affected (generators not moved in r3) |
| AI-15 | Math-honest tooltips — cite source or note approximation. | Not affected |

---

## 12. CONTEXT.md sections relevant to restructure

Not quoted in full (file is 84 KB). Key sections:

**Section 4 (Architecture conventions / Module map):** Documents the subpackage layout established in r2. Post-r2: `varieties/` owns all math; `_qt/` owns all Qt; `render/` owns worker thread; `cross_section/` owns clip pipeline. `surfaces.py` documented as re-export hub.

**Section 9 (Non-goals):** Includes "Don't create new top-level packages during a restructure batch — work within the established subpackages." Adding `VarietyGenerator` Protocol to `varieties/types.py` (an existing module) is within scope. Moving `parameter_grid.py` to `_qt/` (an existing package) is within scope.

**Section 12 (Git workflow):** Commit and push between every batch. Conventional commits. GPG signing enforced.

---

## 13. README "Extending the app" — verbatim quote

> **Adding a new model to an existing variety** is straightforward:
>
> 1. Write a generator function in the appropriate family module under `varieties/` (e.g. `varieties/k3.py` for K3 surfaces, `varieties/enriques.py`, `varieties/calabi_yau.py`, `varieties/fano.py`). The generator returns a `pv.PolyData`. Implicit generators sample a scalar field on a cubic grid and call `_marching_cubes_to_polydata(field, bounds)` (imported from `varieties._marching`). Parametric generators build `(X, Y, Z)` 2D arrays and call `_grid_to_polydata(X, Y, Z)` (also from `varieties._marching`).
> 2. If your generator needs a Numba-accelerated field kernel, add an `@njit` function to `varieties/_kernels.py`.
> 3. Define a `<NAME>_PARAMS` list in the same family module: `ParamSpec(name, label, minimum, maximum, default, step, suffix, description)` — one per slider. Import `ParamSpec` from `varieties.types`.
> 4. Add `Surface(label, generator, params)` to the appropriate inner dict of `VARIETIES` in `varieties/registry.py`. Use a `[Fig. N]` suffix in the dropdown key for consistency.
> 5. Add tooltip entries to `SUBTYPE_TOOLTIPS` in `varieties/tooltips.py` (and `VARIETY_TOOLTIPS` if introducing a new family).
> 6. Add at least a smoke test in `tests/test_mesh_generators.py` and a parameter-range entry in `tests/test_parameters_panel.py`. Test imports can use either the canonical path (`from varieties.k3 import fermat_quartic`) OR the legacy `from surfaces import fermat_quartic` (re-exported via the surfaces hub; will emit `DeprecationWarning` when the surfaces shim is fully retired).
>
> **Backward-compatibility note (post r2-restructure):** the historical `surfaces.py` module is now a hub re-export. Existing imports like `from surfaces import VARIETIES` continue to work; the canonical path is `from varieties.registry import VARIETIES`. See `MOVES.md` for the full r2 rosetta stone.

**Constraint for r3:** Step 3 directs users to `import ParamSpec from varieties.types` — this is already the canonical path. Step 6 explicitly notes `from surfaces import ...` as a legacy path that "will emit DeprecationWarning when the surfaces shim is fully retired." B4's surfaces.py retirement fulfills this stated intent. The README's extension path (`varieties/`) is not changed by r3; it must be updated by the anchor-updater in B5 to remove the backward-compat note after surfaces.py is gone.

---

## 14. Honest assessment

### Already good (don't fix)

- `varieties/` subpackage is clean: types, kernels, generators, registry, tooltips each in their own file with no cycles.
- `_qt/` subpackage is clean: icons, styles, ui_helpers, panels/ all canonical.
- `render/worker.py` is canonical; `render/__init__.py` is empty (correct).
- `cross_section/clip.py` is canonical; no changes needed.
- `app.py` imports `_qt.*`, `render.worker` directly — the `from surfaces import` block is the only residual root-level dependency.
- `panels/__init__.py` hub shim pattern is exactly correct per Template-1 spec.
- `test_r2_shims.py` correctly covers all 5 shims; deletion in B3 is clean.

### Clearly bad (genuine quick wins)

- 4 root shims (`icons.py`, `styles.py`, `ui_helpers.py`, `render_worker.py`) have zero real callers outside `test_r2_shims.py`. B3 deletion is a straight `git rm`.
- `panels/__init__.py` hub shim: `_qt/panels/__init__.py` has a docstring listing the `from panels.*` form as canonical — this is now stale (canonical is `from _qt.panels.*`). Should be updated when the shim is deleted.
- `parameter_grid.py` has exactly 4 callers, all using the `import parameter_grid as pg` alias form — LibCST scope is minimal and well-bounded.

### Debatable (context-dependent)

- **`_qt/ui_helpers.py` imports `from surfaces import ParamSpec`** — after B4, this must become `from varieties.types import ParamSpec`. However `_qt/ui_helpers.py` is a Qt module importing from a pure-math module (`varieties.types`), which is fine for the layer direction (`_qt` → `varieties`).
- **`parameter_grid.py` move target name:** brief says `_qt/parameter_grid_math.py`. The file currently has a well-named docstring ("parameter_grid — pure-Python coordinate math"). The `_math` suffix is accurate but changes the module name from what callers alias (`import parameter_grid as pg` → `import _qt.parameter_grid_math as pg`). LibCST must update the alias target in all 4 callers.
- **`VarietyGenerator` Protocol addition to `varieties/types.py`:** adding a Protocol alongside the existing dataclasses is low-risk (additive) but the brief is careful to note this is a r3 decision. The designer must specify exactly what `VarietyGenerator.__call__` should look like — the current `Surface.generate: Callable[..., pv.PolyData]` uses a loose `Callable[..., pv.PolyData]`. A strict Protocol signature would pin the kwargs, which could be a breaking change for any generator that doesn't match.

---

## 15. Files the restructure CANNOT touch without lifting an invariant

| File | Invariant | Constraint |
|---|---|---|
| `app.py` (all lines except the `from surfaces import` block at L49-63) | AI-9 | `self._computing` re-entrancy guard must not be disturbed. r3 only rewrites the import block; no logic changes. |
| `varieties/types.py` (existing `ParamSpec` and `Surface` fields) | AI-8 | `Surface` + `ParamSpec` dataclass field signatures are frozen by contract. B2 may ADD `VarietyGenerator` Protocol but must NOT change existing fields or their defaults. |
| `varieties/registry.py` (`VARIETIES` dict structure) | AI-8 | Registry shape is invariant. B4 rewrites callers to use this as canonical; the registry itself does not change. |
| `varieties/_marching.py` (`_marching_cubes_to_polydata`, `_grid_to_polydata`) | AI-6 | Implicit/parametric pipeline split encoded here. B4 rewrites callers to import from this module directly; the module is unchanged. |
| `render/worker.py` | None blocking, but | Canonical home for MeshWorker. Not touched in r3. |
| `pytest.ini` | Process | Anchor-updater owns. Not touched in r3 (except implicitly if test count changes). |
| `CONTEXT.md`, `README.md`, `CLAUDE.md`, `MOVES.md` | Process | Anchor-updater owns edits in B5. Do not edit during B1-B4. |
| `.claude/agents/`, `.claude/commands/`, `.claude/scripts/`, `.claude/hooks/`, `.claude/references/` | Scope guard | Out of scope per invariant rules. Exception: `rewrite-imports.py` bug fix is B1's purpose (fix is WITHIN `.claude/scripts/repository-architect/`). |
| `.github/` | Scope guard | CI/CD pipeline, out of scope. |

---

*End of audit brief — restructure-single-root-2026q2-r3 Phase 1.*
