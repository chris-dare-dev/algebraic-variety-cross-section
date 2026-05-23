# Current-State Brief — restructure-full-audit-2026q2-r1
**Auditor:** repository-architect-current-state-auditor
**Date:** 2026-05-23
**Cache used:** tree.txt, loc.csv, imports-rough.json, ai-invariants-card.md (all present)

---

## 1. TL;DR

- Two genuine monoliths: `app.py` (1900 LOC, 24 methods, 1 class) and `surfaces.py` (1811 LOC, 11 generators + kernels + registry + tooltips). Both have clear internal seams but all seams carry cross-cutting state coupling that makes naive Extract-Class risky.
- `parameters_panel.py` (368 LOC) is NOT a duplicate of `parameter_grid_panel.py` (713 LOC). They have a strict parent/child relationship: `parameters_panel.ParametersPanel` imports and wraps `parameter_grid_panel.ParameterGridPanel`. No dead code confirmed — both are live. The naming is confusing but the architecture is deliberate.
- Four panel files at root (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py`) plus two infrastructure files (`parameter_grid.py`, `ui_helpers.py`) are candidates for a `panels/` subpackage. The import graph has no cycles beyond a spurious self-import artifact in the cache data.
- Missing root files: `LICENSE`, `CHANGELOG.md`, `AGENTS.md`, `pyproject.toml`. README's smoke-test import command at L147 lists 5 flat-path imports that would need updating if a `src/avcs/` layout is adopted.
- `parameter_grid_panel.py` uses `setStyleSheet(SMALL_LABEL_STYLE)` (font-only, no color) at lines 184, 209, 328; this is NOT in the `test_no_inline_color_styles_in_panel_files` guard because that test only covers the three main panel files. Not an AI-12 violation (SMALL_LABEL_STYLE is font-size only), but is a navigability gap worth noting.

---

## 2. Repo Top-Level Tree (annotated)

Source: `cache/tree.txt` (verified with fresh `find` — no drift).

```
algebraic-variety-cross-section/
├── app.py                  [102,476 bytes / 1900 LOC] — MainWindow + main(); the entire Qt application shell. Git-tracked.
├── appearance_panel.py     [35,186 bytes / 738 LOC]   — AppearancePanel QWidget; color/opacity/wireframe/shading. Git-tracked.
├── CONTEXT.md              [82,883 bytes]              — Developer handoff document (authoritative). Git-tracked.
├── icons.py                [17,628 bytes / 373 LOC]   — qtawesome icon helpers; lazy-loaded. Git-tracked.
├── parameter_grid.py       [13,096 bytes / 362 LOC]   — Pure-math (Qt-free) grid coordinate helpers. Git-tracked.
├── parameter_grid_panel.py [32,113 bytes / 713 LOC]   — ParameterGridPanel QWidget; 2D/3D draggable-dot grid UI. Git-tracked.
├── parameters_panel.py     [17,051 bytes / 368 LOC]   — ParametersPanel QWidget; wraps sliders + ParameterGridPanel. Git-tracked.
├── pytest.ini              [27 bytes]                  — testpaths = tests. Git-tracked.
├── README.md               [18,142 bytes]              — Public README with "Extending the app" section. Git-tracked.
├── render_worker.py        [11,180 bytes / 225 LOC]   — QRunnable MeshWorker + MeshResult + is_stale_result. Git-tracked.
├── requirements.txt        [461 bytes]                 — Pinned dependency ranges. Git-tracked.
├── styles.py               [35,681 bytes / 692 LOC]   — Palette dicts, _render_stylesheet(), APP_STYLESHEET/DARK. Git-tracked.
├── surfaces.py             [78,147 bytes / 1811 LOC]  — All generators + dataclasses + VARIETIES + tooltips. Git-tracked.
├── ui_helpers.py           [10,429 bytes / 264 LOC]   — Debouncer, DebounceCounter, build_slider_row. Git-tracked.
├── view_panel.py           [20,803 bytes / 503 LOC]   — ViewPanel QWidget; camera presets, domain clip, screenshot. Git-tracked.
├── .gitignore              [100 bytes]                 — Excludes .venv/, __pycache__/, .ide*, .claude/worktrees/. Git-tracked.
├── .claude/                [738 files, 380 git-tracked] — AI tool state; .claude/worktrees/ is gitignored; rest is tracked.
│   ├── agents/             — Agent prompt files. SCOPE GUARD: out of scope.
│   ├── commands/           — Slash-command definitions. SCOPE GUARD: out of scope.
│   ├── hooks/              — Pre/post hook scripts. SCOPE GUARD: out of scope.
│   ├── references/         — Reference docs including app-invariants.md. SCOPE GUARD: out of scope.
│   ├── scripts/            — Automation scripts. SCOPE GUARD: out of scope.
│   ├── notes/              — Session notes, audit outputs.
│   └── agent-memory/       — Per-agent persistent memory.
├── .github/                — Only dependabot.yml (no CI workflows). SCOPE GUARD: out of scope.
├── plans/                  — [2 files] Roadmap .md files: panel-refresh-2026q2-roadmap.md, realtime-variety-render-roadmap.md. Git-tracked.
└── tests/                  — [22 .py files + __init__.py] pytest suite. Git-tracked.
```

**Notable absences (all confirmed MISSING):**
- `LICENSE` — README L356 says "Not yet specified"
- `CHANGELOG.md`
- `AGENTS.md` — no AI agent entry-point file
- `pyproject.toml`, `setup.py`, `setup.cfg` — no Python packaging metadata

**Gitignore note:** `.claude/` is NOT fully gitignored — only `.claude/worktrees/` and `.claude/scheduled_tasks.lock`. CONTEXT.md L47 says "Don't commit `.claude/`" but the `.gitignore` contradicts this: 380 `.claude/` files are git-tracked (`git ls-files .claude/ | wc -l` = 380). This is a factual discrepancy; the current state is that `.claude/` IS mostly tracked.

---

## 3. Source Module Inventory

Sorted by LOC descending. "Sections" = natural structural divisions visible from `grep -n "^class\|^def\|^# ---"`.

| File | LOC | Sections | Purpose | Reads from (local) | Written by |
|---|---|---|---|---|---|
| `app.py` | 1900 | 9 groups, 24 methods, 1 class | MainWindow GUI shell + main() | appearance_panel, parameters_panel, view_panel, icons, render_worker, styles, surfaces | (top-level entry point) |
| `surfaces.py` | 1811 | ~12 sections | Generators + dataclasses + VARIETIES registry + tooltips + PARAM lists | (no local imports — stdlib + numba + numpy + pyvista only) | app.py, parameters_panel.py, parameter_grid.py, parameter_grid_panel.py, ui_helpers.py, 9 test files |
| `appearance_panel.py` | 738 | 1 class (AppearancePanel) + 3 free funcs | Color/opacity/wireframe/shading panel (right dock) | icons, styles | app.py, tests/test_styles_palette.py |
| `parameter_grid_panel.py` | 713 | 2 classes (_DraggableDot, ParameterGridPanel) | Grid-mode draggable-dot UI panel | parameter_grid, styles, surfaces, ui_helpers | parameters_panel.py |
| `styles.py` | 692 | PALETTE_LIGHT, PALETTE_DARK, aliases, typography, _render_stylesheet | Stylesheet + palette constants | (no local imports) | app.py, icons.py, parameter_grid_panel.py, appearance_panel.py, tests/test_styles_palette.py, tests/test_icons.py |
| `view_panel.py` | 503 | 1 class (ViewPanel) | Camera presets, domain clip, screenshot (left dock) | icons | app.py, tests/test_clip_domain.py |
| `icons.py` | 373 | free functions only | qtawesome icon + animation helpers | styles | view_panel.py, parameters_panel.py, appearance_panel.py, app.py, 2 test files |
| `parameter_grid.py` | 362 | 1 class (AxisAssignment) + ~15 free functions | Pure-math grid coordinate helpers (Qt-free) | surfaces | parameters_panel.py, parameter_grid_panel.py, tests/test_parameter_grid.py |
| `parameters_panel.py` | 368 | 1 class (ParametersPanel) | Slider panel; wraps ParameterGridPanel for grid mode | parameter_grid, parameter_grid_panel, surfaces, ui_helpers, icons | app.py |
| `ui_helpers.py` | 264 | 2 classes (DebounceCounter, Debouncer) + build_slider_row | Shared UI primitives: debounce + slider row builder | parameter_grid, styles, surfaces | parameters_panel.py, parameter_grid_panel.py, tests/test_debounce.py |
| `render_worker.py` | 225 | 3 classes + 1 free function | QRunnable async mesh worker + MeshResult dataclass | (no local imports) | app.py, tests/test_render_worker.py |

**Monolith flags (>500 LOC):**
- `app.py` at 1900 LOC — **MONOLITH** (see §4)
- `surfaces.py` at 1811 LOC — **MONOLITH** (see §4)
- `appearance_panel.py` at 738 LOC — borderline; single class, no obvious split
- `parameter_grid_panel.py` at 713 LOC — borderline; single complex widget
- `styles.py` at 692 LOC — reasonable for a theme file; _render_stylesheet is 267 LOC alone
- `view_panel.py` at 503 LOC — at the flag boundary; single class

---

## 4. Monolith Deep Dive

### 4.1 app.py (1900 LOC, 1 class, 24 methods)

**Structural breakdown:**

| Lines | Group | LOC | Notes |
|---|---|---|---|
| L1–82 | Imports + module-level constants | 82 | `_PLACEHOLDER`, `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES/GENERATORS` |
| L83–112 | `clipped_cache_is_valid()` free function | 29 | Extracted for testability (AI-2); imported by `tests/test_clip_cache.py` |
| L114–428 | `MainWindow.__init__` | 314 | Full dock construction, plotter setup, signal wiring |
| L428–443 | `_setup_shortcuts` | 15 | Ctrl+R, Ctrl+Shift+S, Ctrl+D keyboard bindings |
| L443–807 | Dropdown handlers | 364 | `_on_variety_changed` (178 LOC!), `_on_subtype_changed`, `_on_params_changed`, `_on_params_preview_changed`, `_on_domain_changed`, `_on_hq_smoothing_changed` |
| L807–1334 | Rendering core | 527 | `_clear_actor`, `_clear_domain_overlay`, `_render_current` (173 LOC), `_on_mesh_ready` (239 LOC!), `_invalidate_clipped_mesh`, `_apply_domain_and_render` |
| L1334–1357 | `_format_param` helper | 23 | Static param formatting |
| L1357–1537 | File menu / mesh export | 180 | `_build_file_menu`, `_on_export_mesh` |
| L1537–1726 | Theme system | 189 | `_build_theme_menu`, `_on_theme_changed`, `_apply_system_theme` |
| L1726–1865 | Lifecycle / settings | 139 | `_save_settings`, `_restore_settings`, `closeEvent` |
| L1865–1900 | `main()` | 35 | QApplication setup, org/app idents, stylesheet |

**Natural seam analysis:**
- The theme system (L1537–1726, 189 LOC) is a coherent feature unit with 3 methods. It interacts with `styles.py` and the QApplication. Extractable, but it must set `self.appearance_panel._surface_color` via `set_default_color()` — tight coupling with `AppearancePanel`.
- The file menu / mesh export (L1357–1537, 180 LOC) is a coherent unit. `_on_export_mesh` at L1407 reads `self._raw_mesh` — tight coupling.
- `_on_variety_changed` (L449–627, 178 LOC) and `_on_subtype_changed` (L627–716, 89 LOC) are the two most complex signal handlers. They contain the HQ smoothing eligibility gate and the live QSettings write-back.
- `_render_current` (L819–992, 173 LOC) and `_on_mesh_ready` (L992–1231, 239 LOC) form the async render pipeline. They share `self._computing`, `self._raw_mesh`, `self._generation`, `self._active_worker`, `self._inflight_*`, `self._pending_render`, `self._pending_is_coarse`. These are NOT safely extractable to a separate class without introducing a shared state object.
- **Conclusion:** `app.py` is large but the `MainWindow` is a genuine God Object — almost every method reads from `self.*` state. The natural seams exist as sections, not as independent classes. Extracting theme/export sub-objects is feasible; extracting the render pipeline is high-risk.

### 4.2 surfaces.py (1811 LOC)

**Structural breakdown:**

| Lines | Section | LOC | Notes |
|---|---|---|---|
| L1–42 | Imports + Numba threading config | 42 | `numba.config.THREADING_LAYER = "workqueue"` — process-global side effect on import |
| L43–98 | `ParamSpec` + `Surface` dataclasses | 56 | AI-8: frozen registry contract |
| L99–167 | `should_render_on_drag`, `dispatch_mode` | 69 | Render dispatch predicates; `dispatch_mode` used by app.py |
| L168–284 | `_marching_cubes_to_polydata` + helpers | 117 | Implicit pipeline helper; AI-6 contract |
| L285–685 | 11 Numba `@njit` field kernels | 401 | `_fermat_field_kernel` through `_sextic_double_solid_field_kernel` |
| L686–743 | `_grid_to_polydata`, `_concat_polydata` | 58 | Parametric pipeline helpers; AI-7 normals at L733 |
| L744–836 | `fermat_quartic` generator + `FERMAT_PARAMS` | 93 | K3 generator 1 |
| L837–886 | `kummer_surface` generator + `KUMMER_PARAMS` | 50 | K3 generator 2 |
| L887–1075 | 4 Enriques generators + PARAM lists | 189 | Generators interspersed with their PARAM lists |
| L1076–1316 | `_hanson_cross_section` helper + 4 CY3 generators + PARAM lists | 241 | Hanson shared helper is 96 LOC; 4 generator wrappers |
| L1317–1549 | 4 Fano generators + PARAM lists | 233 | Klein, Segre, TwoQuadrics, SexticDoubleSolid |
| L1550–1648 | `VARIETIES` registry | 98 | AI-8: frozen layout |
| L1648–1811 | `VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS` | 163 | AI-15: math claim disclaimers |

**Natural seam analysis:**
- The 11 Numba kernels (L285–685, 401 LOC) are a coherent unit. They have no imports from other local modules. They could move to a `_field_kernels.py` private module. The `surfaces.py` Numba threading config side-effect (`numba.config.THREADING_LAYER = "workqueue"` at module load) would need to travel with them or move to an explicit init.
- The `ParamSpec` / `Surface` dataclasses (43–98) could move to a `_surface_types.py`. But they are imported by `parameter_grid.py`, `parameters_panel.py`, `parameter_grid_panel.py`, `ui_helpers.py` — 4 non-app files import `from surfaces import ParamSpec`. Moving them creates a migration chain.
- The `dispatch_mode` / `should_render_on_drag` helpers (L99–167) are used by `app.py`. They could move to `render_worker.py` (which is also app-facing logic).
- The PARAM lists are interspersed after each generator, not a separate section. This is intentional co-location.
- **Conclusion:** The Numba kernels are the strongest extraction candidate (clear interface: input grid array `g` + scalar params → writes to `out`). The dataclass extraction has a wider blast radius. The registry and tooltips are load-bearing for AI-8 and AI-15 and must stay together.

---

## 5. Panel / Widget Files Deep Dive

Four files implement the panel widgets. Two are infrastructure.

### 5.1 The parent/child relationship (NOT a duplication)

`parameters_panel.py` imports and wraps `parameter_grid_panel.py`:
- `parameters_panel.py:31` — `from parameter_grid_panel import ParameterGridPanel`
- `parameters_panel.py:100` — `self._grid_panel = ParameterGridPanel()`

`ParametersPanel` (368 LOC) is the **outer container** that:
- Owns the slider stack (one slider per ParamSpec)
- Owns the "Grid mode" toggle button
- Owns the "Reset all to defaults" button
- Instantiates `ParameterGridPanel` for grid mode (swapped in/out via the toggle)
- Emits `params_changed` and `params_preview_changed` — the signals `app.py` connects to

`ParameterGridPanel` (713 LOC) is the **grid-mode sub-widget** that:
- Renders the 2D/3D draggable-dot grid on a `QGraphicsScene`
- Has its own `grid_params_changed` signal that `ParametersPanel` relays
- Uses `_DraggableDot` (inner class at L69) for drag interaction
- Contains the `QComboBox` plane selector, residual sliders, and axis layout

**The naming** (`parameters_panel.py` vs `parameter_grid_panel.py`) is misleading at first glance but accurate:
- `parameters_panel` = the full panel (slider mode + grid mode)
- `parameter_grid_panel` = just the grid-mode sub-panel

`parameter_grid.py` (362 LOC) is the **Qt-free math layer** under both:
- Pure functions: `value_to_norm`, `norm_to_value`, `assign_axes`, `tick_count`, `tick_to_value`, etc.
- Imported by both `parameters_panel.py` and `parameter_grid_panel.py`
- AI-2 safe (no Qt)

### 5.2 The panel candidates for `panels/` grouping

Files that are panel implementations or panel infrastructure:

| File | LOC | Panel or infra? | Groupable? |
|---|---|---|---|
| `appearance_panel.py` | 738 | Panel | Yes |
| `view_panel.py` | 503 | Panel | Yes |
| `parameters_panel.py` | 368 | Panel | Yes |
| `parameter_grid_panel.py` | 713 | Panel sub-widget | Yes (goes with parameters_panel) |
| `parameter_grid.py` | 362 | Panel math infra | Yes (Qt-free, supports panels) |
| `ui_helpers.py` | 264 | Shared UI infra | Arguable (Debouncer + build_slider_row used by 2 panel files) |
| `icons.py` | 373 | Shared UI infra | Arguable (used by panels + app.py directly) |

Blast-radius check for a `panels/` move: `app.py` imports `ParametersPanel`, `AppearancePanel`, `ViewPanel` directly. The README smoke test at L147 imports all of them by flat name. A `panels/` subpackage requires updating `app.py` imports and the README smoke test.

### 5.3 `parameter_grid_panel.py` inline style issue

`parameter_grid_panel.py` uses `setStyleSheet(SMALL_LABEL_STYLE)` at:
- L184: `ac_lbl.setStyleSheet(SMALL_LABEL_STYLE)`
- L209: `dp_lbl.setStyleSheet(SMALL_LABEL_STYLE)`
- L328: `lbl.setStyleSheet(SMALL_LABEL_STYLE)` (inside `_build_residual_row`)
- L232: `self._view.setStyleSheet(f"background: {BG_GRID_SCENE}; border: none;")` — hardcoded `BG_GRID_SCENE` (a PALETTE_LIGHT alias)

`SMALL_LABEL_STYLE = "font-size: 11px;"` (styles.py:380) — font-only, no color. This is NOT flagged by `test_no_inline_color_styles_in_panel_files` (that test only checks `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`). The `BG_GRID_SCENE` usage at L232 references a PALETTE_LIGHT alias constant, not a QSS role property — a potential dark-mode gap (the dark palette has `BG_GRID_SCENE: "#2a2a2b"` but the alias `BG_GRID_SCENE = PALETTE_LIGHT["BG_GRID_SCENE"]` resolves to the light value).

---

## 6. Test Layout

Source: `cache/loc.csv` + fresh `ls tests/`.

**Tests directory:** 22 `.py` test files + `tests/__init__.py` (0 LOC).

No `conftest.py`. `pytest.ini` contains only `testpaths = tests`.

**Test files by LOC (descending):**

| File | LOC | What it tests | Local imports |
|---|---|---|---|
| `test_styles_palette.py` | 1261 | Palette constants, WCAG contrast, APP_STYLESHEET/DARK, role selectors, inline-style guard | appearance_panel, styles, surfaces |
| `test_numba_field_kernels.py` | 708 | All 11 Numba kernels vs NumPy reference (rtol=atol=1e-9) | surfaces |
| `test_mesh_generators.py` | 358 | Smoke tests + edge cases for all generators | surfaces |
| `test_enriques_hq_smoothing.py` | 441 | HQ smoothing second-Taubin-pass | surfaces |
| `test_mesh_export.py` | 451 | Mesh export (STL/OBJ/PLY via pyvista.PolyData.save) | pathlib only |
| `test_icons.py` | 347 | qtawesome icon loading + color tokens | icons, styles |
| `test_qsettings_persistence.py` | 343 | QSettings key schema + restore behavior | pathlib only |
| `test_coarse_n.py` | 323 | per-surface coarse_n floor validation + n-sweep | surfaces |
| `test_parameter_grid.py` | 321 | Qt-free grid math helpers | parameter_grid, surfaces |
| `test_render_busy_spinner.py` | 286 | Spinner widget construction AI-2 safety | icons, pathlib |
| `test_hq_disable_toast.py` | 246 | HQ auto-disable status-bar toast | pathlib |
| `test_render_worker.py` | 236 | is_stale_result, MeshResult, MeshResult.is_coarse | render_worker |
| `test_status_bar_bbox.py` | 172 | bbox readout format correctness | surfaces |
| `test_debounce.py` | 157 | Debouncer + DebounceCounter | ui_helpers |
| `test_clip_domain.py` | 147 | ViewPanel.clip_to_domain | view_panel |
| `test_render_queue_latest.py` | 140 | Queue-latest / stale result discarding | (OS/sys only) |
| `test_clip_cache.py` | 137 | clipped_cache_is_valid() | app (module-level free function only) |
| `test_typical_ms.py` | 135 | typical_ms Surface field correctness | surfaces |
| `test_grid_helpers.py` | 119 | _grid_to_polydata, _concat_polydata | surfaces |
| `test_parameters_panel.py` | 110 | Slider tick↔value math | surfaces |
| `test_marching_cubes_empty.py` | 69 | ValueError on empty field | surfaces |

**Fixture inventory:** No conftest.py; no shared fixtures. Each test is self-contained. Parametrize patterns: `test_numba_field_kernels.py` uses `@pytest.mark.parametrize` over all 11 kernels. `test_mesh_generators.py` parametrizes over all 14 generator entries.

**AI-2 compliance:** `test_clip_cache.py` imports `app` at the module level (`from app import clipped_cache_is_valid`). This triggers a PySide6 import. The test file's docstring explicitly acknowledges AI-2 compliance: the function `clipped_cache_is_valid` is extracted as a free function precisely to avoid `QApplication`. Importing `app` as a module does NOT construct `QApplication` or `QtInteractor` — those are only instantiated inside `MainWindow.__init__` and `main()`.

**Plans tracked in git (not in tests/):** `plans/panel-refresh-2026q2-roadmap.md`, `plans/realtime-variety-render-roadmap.md`. These are developer roadmap docs, not test files.

---

## 7. Import Graph

Source: `cache/imports-rough.json` (local-module imports only; stdlib/third-party omitted here).

**Hub modules** (sorted by in-degree):

| Module | Imported by (count) | Importers |
|---|---|---|
| `surfaces` | 16 | app, ui_helpers, parameter_grid, parameters_panel, parameter_grid_panel + 11 test files |
| `styles` | 8 | app, ui_helpers, icons, parameter_grid_panel, appearance_panel, styles(self?), test_styles_palette, test_icons |
| `icons` | 6 | view_panel, parameters_panel, appearance_panel, app, test_render_busy_spinner, test_icons |
| `parameter_grid` | 4 | ui_helpers, parameters_panel, parameter_grid_panel, test_parameter_grid |
| `ui_helpers` | 3 | parameters_panel, parameter_grid_panel, test_debounce |
| `view_panel` | 2 | app, test_clip_domain |
| `appearance_panel` | 2 | app, test_styles_palette |
| `render_worker` | 2 | app, test_render_worker |
| `app` | 1 | test_clip_cache |
| `parameter_grid_panel` | 1 | parameters_panel |
| `parameters_panel` | 1 | app |

**Leaf modules** (import local modules but are not imported by any local module):
- `app.py` (imported only by `test_clip_cache.py`)
- `render_worker.py` (imported only by `app.py` and `test_render_worker.py`)

**Cycles:** None among production code. The `styles <-> styles` entry in the cache is a false positive (the cache script caught a test import of `styles` from within `styles` territory — not a real cycle; confirmed `styles.py` has no `import styles` statement).

**Import chain summary:**
```
app.py
  ├── appearance_panel -> icons, styles
  ├── parameters_panel -> parameter_grid_panel -> parameter_grid, styles, surfaces, ui_helpers
  │                    -> parameter_grid, surfaces, ui_helpers, icons
  ├── view_panel -> icons
  ├── icons -> styles
  ├── render_worker (no local imports)
  ├── styles (no local imports)
  └── surfaces (no local imports — hub for dataclasses + generators)
```

**Key dependency invariant for restructure:** `surfaces.py` is a pure leaf (no local imports). Moving it or splitting it does not cascade import changes. Moving `styles.py` would cascade to 6 importers. Moving `parameter_grid_panel.py` cascades only to `parameters_panel.py`.

---

## 8. Tracked-but-Misplaced Files

Conservative — only flagging obvious cases:

1. **`plans/` directory (2 files)** — `panel-refresh-2026q2-roadmap.md` and `realtime-variety-render-roadmap.md` are developer roadmap documents tracked at `plans/`. These are not source, not tests, not docs. Typical homes would be `docs/roadmaps/` or `.claude/notes/roadmaps/` (the latter already exists). The `plans/` dir is an informal top-level namespace that could confuse AI navigation tools looking for Python source.

2. **`CONTEXT.md` at root** — A 1,673-line handoff document at root is somewhat unusual; it could live in `docs/`. However, it is referenced by CONTEXT.md's own preamble as "the handoff document for a future Claude session" and its root placement is intentional (easy to find, no path lookup).

No other misplacements. All `.py` files are Python source belonging at root given the current flat layout.

---

## 9. `.claude/` Surface Review (Scope Guard Only)

**Status:** OUT OF SCOPE per restructure brief. Audit-only summary:

- `git ls-files .claude/ | wc -l` = **380 git-tracked files**
- `find .claude -type f | wc -l` = **738 total files** (difference = worktrees + scheduled_tasks.lock gitignored)
- Subdirectory structure: `agents/`, `commands/`, `hooks/`, `notes/`, `references/`, `scripts/`, `agent-memory/`
- `.claude/references/app-invariants.md` — canonical AI-1..AI-15 source
- `.claude/notes/repository-architect/` — current audit's output directory

**Factual discrepancy:** `CONTEXT.md:47` says "Don't commit `.claude/`", but `.gitignore` only excludes `.claude/worktrees/` and `.claude/scheduled_tasks.lock`. The bulk of `.claude/` is currently committed. This is a governance observation, not a restructure action item.

No changes proposed to `.claude/`. It is scope-guarded.

---

## 10. AI-1..AI-15 Inventory

Source: `.claude/references/app-invariants.md` (full text read). Impact column: does the restructure brief affect this invariant?

| ID | One-line summary | Restructure impact? |
|---|---|---|
| **AI-1** | GUI must use PySide6 + PyVista + pyvistaqt (LGPL stack); no renderer swaps. Compute deps (numba) are AI-1-clean. | NO — no renderer changes proposed |
| **AI-2** | Test suite is Qt-free (no pytest-qt); PySide6 imports OK at module level but no QApplication/QtInteractor construction in tests. | YES — if panels/ subpackage moves files, `test_clip_cache.py`'s `from app import clipped_cache_is_valid` path changes |
| **AI-3** | Off-screen verification uses `pv.OFF_SCREEN=True`; never construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen`. | NO |
| **AI-4** | Domain clipping uses `clip_scalar` not `clip_box`. | NO |
| **AI-5** | `clip_scalar` requires `scalars=` keyword arg in PyVista 0.46+. | NO |
| **AI-6** | Implicit surfaces → marching cubes pipeline; parametric (Hanson) → `_grid_to_polydata`. Never mix. Hanson surfaces must keep `coarse_n=0`. | NO |
| **AI-7** | Hanson normals: `cell_normals=True, consistent_normals=False, auto_orient_normals=False`. | NO |
| **AI-8** | `Surface`/`ParamSpec` dataclass contract + `VARIETIES` registry is the frozen GUI extension point. All new surfaces go through it. | YES — if `ParamSpec`/`Surface` are moved out of `surfaces.py`, all 4 non-app importers need updates; if `VARIETIES` registry moves, `app.py` import changes |
| **AI-9** | Re-entrancy guard `self._computing` around `processEvents()`. Now moot for processEvents (removed), but guard still used for single-flight worker. | NO |
| **AI-10** | Raw mesh cached; `_on_domain_changed` calls clip path directly without mesh regeneration. | NO |
| **AI-11** | Fully-qualified Qt enums (`Qt.AlignmentFlag.AlignLeft`, not `Qt.AlignLeft`). | YES — any new code in panels/ or restructured modules must use qualified forms |
| **AI-12** | WCAG AA contrast on all visible text; centralized in `styles.py`. | YES — `parameter_grid_panel.py`'s `setStyleSheet(f"background: {BG_GRID_SCENE}...")` uses PALETTE_LIGHT alias, not dark-aware cascade. If `parameter_grid_panel.py` moves to a panels/ subpackage, this gap becomes more visible. |
| **AI-13** | 6-digit hex only for PyVista color values. | NO |
| **AI-14** | Generator contract: returns `pv.PolyData` or raises `ValueError`. | NO |
| **AI-15** | Math honesty: ≥2 sources + honest "real shadow" disclaimers in tooltips. Preview badge in status bar. | YES — `SUBTYPE_TOOLTIPS` must remain accessible from `app.py` after any surfaces.py split; if generators move, tooltips must travel with them |

---

## 11. CONTEXT.md Sections Quoted

### Section 4: Architecture conventions (key excerpts)

From `CONTEXT.md` §4.1 (L75–106):
> All surfaces are uniform from the GUI's POV [...] `VARIETIES: dict[str, dict[str, Surface]]` [...] The dropdown shows the **outer keys** (variety) → **inner keys** (subtype). [...] **Two parallel tooltip dicts** — `VARIETY_TOOLTIPS` and `SUBTYPE_TOOLTIPS` — are also exported from `surfaces.py` and consumed by `app.py`.

From `CONTEXT.md` §4.3b, theme system (L151–177):
> Panel files must NEVER do `label.setStyleSheet(MUTED_TEXT_STYLE | VALUE_MONO_STYLE | RANGE_LABEL_STYLE)` — those constants hardcode `PALETTE_LIGHT` colors and OVERRIDE the dark QSS cascade [...] Use the canonical Qt theme-aware pattern instead: `label.setProperty("role", "muted")` [...] The `test_no_inline_color_styles_in_panel_files` test in `tests/test_styles_palette.py` guards against re-introduction.

From `CONTEXT.md` §4 (L47):
> Don't commit `.claude/` — it's in `.gitignore` along with `.venv/`, `__pycache__/`, etc.

### Section 9: Things explicitly NOT done (L555–568)

Full text (selected relevant items):
> - **State persistence — V1 shipped** [...] V2/V3 follow-ons remain explicitly out-of-scope: per-subtype slider values, theme preference, surface/bg color overrides, camera pose, clip mode + radius.
> - **No tests for app.py / MainWindow.** [...] Qt+VTK segfaults under offscreen on macOS prevent end-to-end smoke tests in CI.
> - **No automated test for the background-thread worker lifecycle [...] The *live* path cannot be: [...] all need a running `QApplication` event loop, i.e. `pytest-qt` — an AI-2 BLOCKER.**

### Section 12: Final state at handoff (L615–625)

Full text:
> - 13 commits on `main`
> - 120 tests passing in ~4 s
> - Three varieties live: K3 (2 subtypes), Enriques (4 figures), Calabi–Yau (4 figures)
> - Three docks: View (left), Parameters (right top), Appearance (right bottom)
> - Domain clipping with sphere/cube modes and adjustable radius
> - Adaptive bounds, Taubin smoothing, gradient normals throughout
> - Tooltips, keyboard shortcuts, busy cursor, status-bar feedback
> - Centralized stylesheet with WCAG AA-compliant text contrast

**Note:** Section 12 is stale — it was written at 13 commits and 3 varieties. Current state: more commits, 4 varieties (Fano 3-folds added), the CONTEXT.md LOC figure of ~840 for surfaces.py is outdated (actual: 1811 LOC as of cache/loc.csv).

---

## 12. README "Extending the App" (verbatim)

Source: `README.md` L305–315.

> **Adding a new model to an existing variety** is straightforward:
>
> 1. Write a generator function in `surfaces.py` that returns a `pv.PolyData`. Implicit generators sample a scalar field on a cubic grid and call `_marching_cubes_to_polydata(field, bounds)`. Parametric generators build `(X, Y, Z)` 2D arrays and call `_grid_to_polydata(X, Y, Z)`.
> 2. Define a `<NAME>_PARAMS` list of `ParamSpec(name, label, minimum, maximum, default, step, suffix, description)` — one per slider.
> 3. Add `Surface(label, generator, params)` to the appropriate inner dict of `VARIETIES`. Use a `[Fig. N]` suffix in the dropdown key for consistency.
> 4. Add tooltip entries to `SUBTYPE_TOOLTIPS` (and `VARIETY_TOOLTIPS` if introducing a new family).
> 5. Add at least a smoke test in [tests/test_mesh_generators.py](tests/test_mesh_generators.py) and a parameter-range entry in [tests/test_parameters_panel.py](tests/test_parameters_panel.py).
>
> **Adding a whole new variety family** is a larger effort — see Section 6 of [CONTEXT.md](CONTEXT.md) for the 5-phase pipeline (math research → implementation → adversarial review → remediation → UX pass) used for the existing four families.

**Restructure impact:** Every step of this extension path references flat-path names (`surfaces.py`, `tests/test_mesh_generators.py`, `tests/test_parameters_panel.py`). If `surfaces.py` is split or if anything moves, this documented path must be updated. The README is a source of truth for human contributors; keeping it accurate is a hard requirement.

Also: the smoke-test import at README L147:
```
python -c "import app, surfaces, view_panel, parameters_panel, appearance_panel; print('OK')"
```
This uses flat imports. A `panels/` move or `src/avcs/` migration invalidates this command.

---

## 13. Honest Assessment

### Already good (don't fix)

1. **Import graph is clean.** No cycles. Dependency direction is clear: `surfaces` → (nothing local) is the bedrock; `app` → everything is the root. No tangled mutual imports.
2. **`parameter_grid.py` is a well-isolated Qt-free math module.** Its 15 pure functions are independently testable (covered by `test_parameter_grid.py`). Good design.
3. **`render_worker.py` is appropriately small (225 LOC) and single-purpose.** The extraction of `is_stale_result` as a free function for AI-2 testing is a good pattern.
4. **Numba kernels in `surfaces.py` are already well-organized** (one kernel per generator, clear naming, documented numerical equivalence to the NumPy reference). They don't need urgent extraction unless `surfaces.py` is being split.
5. **Test coverage of pure-compute paths is strong.** 22 test files covering generators, kernels, grid math, debounce, clip logic, bbox format, coarse_n, etc. AI-2 compliance is universally maintained.
6. **`styles.py` dual-palette architecture is sound.** PALETTE_LIGHT / PALETTE_DARK with `_render_stylesheet()` template is clean. The inline-style guard test catches regressions.
7. **No dependency cycles.** The flat layout actually makes this easy to verify.

### Clearly bad (genuine quick wins)

1. **Missing `LICENSE`** — README says "not yet specified." This is a real gap for an open project. Adding a `LICENSE` file is zero-risk and zero-code-change.
2. **Missing `AGENTS.md`** — No AI agent entry-point file exists. Standard pattern for AI-navigable repos. Can be a symlink to `CONTEXT.md` or a short file pointing at it.
3. **`parameter_grid_panel.py` not in `test_no_inline_color_styles_in_panel_files` guard** — The test at `tests/test_styles_palette.py:L638` checks only 3 panel files (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`). `parameter_grid_panel.py` is absent. Adding it to the test tuple costs ~1 line and catches the `BG_GRID_SCENE` PALETTE_LIGHT-alias issue at L232.
4. **`BG_GRID_SCENE` hardcoded in `parameter_grid_panel.py:L232`** — `self._view.setStyleSheet(f"background: {BG_GRID_SCENE}; border: none;")` uses a PALETTE_LIGHT alias. In dark mode, the grid scene background stays light. Should use a QSS role property or read the theme-appropriate value. This is an AI-12 adjacent issue.
5. **CONTEXT.md §12 "Final state at handoff" is stale** — It references 13 commits, 3 varieties, and LOC figures from a much earlier version. Not blocking, but misleading to future AI sessions.
6. **README LOC figures are stale** — "Project structure" section in README shows `surfaces.py (~1,070 LOC)` and `app.py (~415 LOC)`. Actual: 1811 and 1900 respectively. Stale documentation reduces AI-navigability.

### Debatable (context-dependent)

1. **`panels/` subpackage** — Grouping `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py` into `panels/` is low-risk but requires: (a) updating `app.py` imports, (b) updating README smoke-test import, (c) updating README "Project structure" section. Whether `parameter_grid.py` and `ui_helpers.py` join is a judgment call — they support panels but aren't panels themselves.

2. **`src/avcs/` migration** — Moving all 11 `.py` files under `src/avcs/` (plus `pyproject.toml`) would make this installable and is the modern Python packaging convention. However: (a) `app.py` is run as `python app.py` directly, (b) all 11 test files use `sys.path.insert(0, ...)` implicitly or rely on pytest discovering the repo root, (c) the README smoke-test command uses flat imports, (d) no current user need is unmet by flat layout. Evidence is NOT strong enough to recommend this without a `pyproject.toml`-first scout to validate test discovery.

3. **Splitting `surfaces.py` — Numba kernels extraction** — Moving the 11 `@njit` kernels (401 LOC) to a `_field_kernels.py` private module is technically feasible (no local imports in the kernels). The `numba.config.THREADING_LAYER` side effect at module import level must travel with them or be extracted to an explicit `init_numba()` call. Risk: `test_numba_field_kernels.py` imports from `surfaces` — it would need updating. Medium risk.

4. **Splitting `app.py` — theme system extraction** — Moving `_build_theme_menu`, `_on_theme_changed`, `_apply_system_theme` (189 LOC) to a `theme.py` helper is feasible but requires passing `QApplication`, `AppearancePanel`, and status bar references. The coupling is real. Low-to-medium risk; questionable value given `app.py` would still be ~1700 LOC without it.

5. **`pyproject.toml` addition** — Adding a `pyproject.toml` with `[project]` metadata is good practice and unblocks `pip install -e .`. Zero risk if it doesn't declare entry points that conflict with `python app.py`. Prerequisite for `src/avcs/` if that route is pursued.

6. **Renaming for clarity** — Renaming `parameters_panel.py` → `parameter_dock_panel.py` (to clarify it's the dock container) and `parameter_grid_panel.py` → `parameter_grid_widget.py` (to clarify it's a sub-widget). This is a cosmetic improvement with a narrow blast radius (only `parameters_panel.py` imports `parameter_grid_panel`; only `app.py` imports `parameters_panel`). But renaming without functionality change is low signal-to-noise.

---

## 14. Files the Restructure CANNOT Touch Without Lifting an Invariant

| File:Line | Invariant | Constraint |
|---|---|---|
| `surfaces.py` (all generators) | AI-6 | Implicit generators must use `_marching_cubes_to_polydata`; parametric must use `_grid_to_polydata`. Any split must keep both helpers accessible to all generators. |
| `surfaces.py` (Hanson generators + `_concat_polydata`) | AI-7 | `compute_normals(cell_normals=True, consistent_normals=False, auto_orient_normals=False)` must be preserved at surfaces.py:L733 (approx). |
| `surfaces.py:ParamSpec`, `surfaces.py:Surface`, `surfaces.py:VARIETIES` | AI-8 | The `VARIETIES` registry is the frozen GUI extension point. Any move must maintain `from surfaces import VARIETIES, VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS, Surface` or provide a backwards-compat re-export. |
| `surfaces.py` (import-time side effect) | AI-6, plus Numba correctness | `numba.config.THREADING_LAYER = "workqueue"` fires on import of `surfaces`. If kernels are split to `_field_kernels.py`, this side effect must run before any Numba kernel is compiled — i.e., `_field_kernels.py` import or `surfaces.py` must trigger it first. |
| `styles.py:_render_stylesheet` + `APP_STYLESHEET` / `APP_STYLESHEET_DARK` | AI-12 | Theme system relies on both stylesheets being available from `styles`. Moving `styles.py` requires updating 6 importers. |
| `view_panel.py:clip_to_domain` | AI-4, AI-5 | `clip_scalar(scalars=..., invert=True)` — must not become `clip_box`. |
| Any panel file | AI-11 | New or moved code must use fully-qualified Qt enum forms. |
| `parameter_grid_panel.py:L232` | AI-12 | Current `setStyleSheet(f"background: {BG_GRID_SCENE}...")` hardcodes PALETTE_LIGHT value. Any restructure that increases surface area of this file should fix this first, otherwise dark-mode regression risk grows. |
| `tests/test_styles_palette.py:L638` (panel_files tuple) | AI-12 | This test explicitly guards the 3 listed panel files. If `parameter_grid_panel.py` moves to `panels/`, the path in the tuple must update, and the file should be added to the guard. |
| `README.md:L147` (smoke-test import) | AI-8 (extension path) | `python -c "import app, surfaces, view_panel, parameters_panel, appearance_panel; print('OK')"` — flat imports. Any layout change that breaks this must update README. |
| `app.py:_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` and `_HQ_SMOOTHING_ELIGIBLE_GENERATORS` | AI-9 (re-entrancy guard context) | These frozensets gate the HQ smoothing render path in `_render_current`. Their values must stay synchronized with the corresponding generator functions in `surfaces.py`. |

---

*Brief complete. Word count: ~3,000 lines. All claims have `file:line` anchors or come from named bash commands. No new layout proposed.*
