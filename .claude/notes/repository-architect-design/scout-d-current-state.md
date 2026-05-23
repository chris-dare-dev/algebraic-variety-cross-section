# Scout D: Current-State Repository Audit
## Algebraic Variety Cross-Section (AVC)

**Execution date:** 2026-05-23  
**Scope:** Target system reconnaissance for `/repository-architect` command design  
**Mission:** Audit existing AVC repo structure. NO restructuring proposals — only honest assessment of what's there, where the seams are, and what's already good.

---

## 1. TL;DR

- **Flat repo layout.** 11 Python files at root (no `src/` subdir). Max file size 1,893 LOC (app.py); three critical hotspots >500 LOC (app.py, surfaces.py, parameter_grid_panel.py).
- **Biggest monolith:** surfaces.py (1,808 LOC). Contains 11 generator functions (implicit) + 3 Hanson parametric, Numba kernels, dataclass registry, and helper grid functions all glued together. Natural split lines exist between implicit-surface pipeline vs. parametric, and between generators vs. shared infrastructure.
- **Test-to-source ratio:** 6,425 LOC tests / 7,849 LOC source = **81.8%** (tests are nearly as large as source). 22 test files, 2 with >1,100 LOC (test_styles_palette.py: 1,179). **No conftest.py** — all fixtures are inline or via plain imports.
- **Typical file size:** 340 LOC median (panel files: 366–713 LOC). Skew is high: 3 files >500 LOC, rest tightly bunched 200–373 LOC.
- **Quick wins:** (a) surfaces.py has clear subsection boundaries (Numba kernels isolated; grid helpers at the tail); (b) panel files are single-class-per-file (ParametersPanel, AppearancePanel, ViewPanel) with clean signal/slot wiring; (c) tests are well-organized by subsystem (test_mesh_generators.py, test_icons.py, test_styles_palette.py). No obvious trash files at root; all tracked files have a clear purpose.

---

## 2. Repo Top-Level Tree (Annotated)

```
algebraic-variety-cross-section/
├── .claude/                    [OUT OF SCOPE — standard Claude Code tool folder]
├── .github/                    [OUT OF SCOPE — standard GitHub folder]
├── .git/                       [Git repository metadata]
├── .gitignore                  Tracks: .venv/, __pycache__/, .claude/, etc.
├── .pytest_cache/              [Generated — gitignored]
├── __pycache__/                [Generated — gitignored]
├── .venv/                      Python 3.12 virtualenv
├── CONTEXT.md                  82 KB; comprehensive architecture + decisions doc
├── README.md                   18 KB; user-facing quick-start + project structure
├── requirements.txt            Pinned deps: PySide6, pyvista, numpy, scikit-image, numba
├── pytest.ini                  testpaths = tests/
│
├── [MAIN APP LAYER]
├── app.py                      1,893 LOC — MainWindow, render dispatch, dock wiring
├── render_worker.py            225 LOC — QThreadPool worker, MeshResult, background dispatch
│
├── [SURFACE GENERATION]
├── surfaces.py                 1,808 LOC — Generators, VARIETIES registry, Numba kernels
│
├── [UI PANELS]
├── parameters_panel.py         368 LOC — Dynamic slider panel (ParamSpec → QSliders)
├── parameter_grid.py           362 LOC — ParamSpec ↔ slider tick/value math
├── parameter_grid_panel.py     713 LOC — RichParametersPanel + BusyLabel (newer iteration)
├── appearance_panel.py         666 LOC — AppearancePanel: color, opacity, shading, bg
├── view_panel.py               503 LOC — ViewPanel: camera, clipping, scene aids, screenshot
├── ui_helpers.py               264 LOC — Shared helpers (debounce, tooltip, etc.)
├── icons.py                    373 LOC — qtawesome icon wrappers + lazy init
├── styles.py                   674 LOC — Centralized stylesheet, palettes (light + dark)
│
├── [TEST SUITE]
├── tests/                      22 test files, 6,425 LOC total
│   ├── test_mesh_generators.py         358 LOC — smoke tests for all 14 generators
│   ├── test_numba_field_kernels.py     708 LOC — Numba kernel equivalence (45 tests)
│   ├── test_styles_palette.py         1,179 LOC — WCAG contrast, text role rendering
│   ├── test_parameter_grid.py          321 LOC — Slider tick math
│   ├── test_parameters_panel.py        343 LOC — ParamSpec validation across registry
│   ├── test_render_worker.py           236 LOC — is_stale_result, MeshResult (Qt-free)
│   ├── test_clip_domain.py             157 LOC — Pure-function clipping (sphere/cube)
│   ├── test_grid_helpers.py            119 LOC — _grid_to_polydata, _concat_polydata
│   ├── test_mesh_export.py             451 LOC — STL/OBJ/PLY save paths
│   ├── test_enriques_hq_smoothing.py   441 LOC — Double-pass Taubin opt-in
│   ├── test_coarse_n.py                323 LOC — LOD preview per-surface floors
│   ├── [+14 more, each 100–286 LOC]
│
└── plans/                      [Scratchpad directories from skill runs]
```

---

## 3. Source Module Inventory (Sorted by LOC)

| File | LOC | Sections | Purpose | Reads-from | Written-by |
|---|---|---|---|---|---|
| **app.py** | 1,893 | 8 | MainWindow, render pipeline, dock wiring, theme menu | surfaces, all panels, render_worker | Opus research agents, frontend-uplift CAND-4,3,5 |
| **surfaces.py** | 1,808 | 6 | 14 generators, Numba kernels (11), VARIETIES registry, grid helpers | numpy, pyvista, numba, scikit-image | Opus agents, realtime-variety-render e5/e6, CAND-2 |
| **styles.py** | 674 | 5 | Stylesheet template, palettes (PALETTE_LIGHT, PALETTE_DARK), tokens | (static constants) | dark-mode-2026q2-e1, focus-ring-contrast, UPL-1,2 |
| **parameter_grid_panel.py** | 713 | 4 | RichParametersPanel + BusyLabel (newer iteration) | parameter_grid, ui_helpers | frontend-uplift UPL-4 |
| **appearance_panel.py** | 666 | 6 | AppearancePanel: color picker, opacity, style, shading, HQ-smooth opt-in | icons, styles, ui_helpers | appearance-panel-layout-pass, enriques-hq-smoothing |
| **parameter_grid.py** | 362 | 3 | Pure tick ↔ value math, ParamSpec.step dispatch | (static / dataclass) | Opus agents |
| **view_panel.py** | 503 | 5 | ViewPanel: presets, domain clip, scene aids, screenshot, status-bar bbox | icons, styles, ui_helpers, surfaces | view-panel rewrites, status-bar-bbox e1/e2 |
| **parameters_panel.py** | 368 | 3 | ParametersPanel: slider rebuild per Surface, "Reset defaults" button | parameter_grid, ui_helpers | Opus agents, refactored in frontend-uplift |
| **icons.py** | 373 | 2 | qtawesome icon wrappers, lazy-init, Spin animation factory | qtawesome, (Qt on demand) | qtawesome-icons-2026q2-e1,e2 |
| **ui_helpers.py** | 264 | 5 | Debounce, tooltip, style enums, shared helpers | (utilities) | Opus agents, incremental |
| **render_worker.py** | 225 | 3 | MeshWorker, MeshResult, is_stale_result, catch_warnings wrapper | surfaces, render_worker | realtime-variety-render-e4 (CAND-4) |
| **TOTAL** | **7,849** | — | — | — | — |

### Monolith Candidates (>500 LOC)

- **app.py (1,893)**: MainWindow is the singular monolith. Contains render dispatch, three dock integrations, theme menu, status-bar updates, and QSettings persistence. Natural split lines exist between render orchestration vs. theme/persistence vs. status-bar formatting — but the three dock wiring points make it load-bearing as-is.
- **surfaces.py (1,808)**: Second monolith. Contains 14 distinct generator functions (11 implicit + 3 Hanson parametric + 1 Dwork pencil implicit), 11 Numba field kernels (isolated block), grid helpers (_grid_to_polydata, _concat_polydata), and the VARIETIES registry. Seams exist: implicit vs. parametric pipelines, Numba kernels vs. generators, helpers vs. registry. See §4 for detail.
- **parameter_grid_panel.py (713)**: Newest parameter panel. Contains RichParametersPanel class + BusyLabel helper. Coexists with older ParametersPanel (368 LOC) — frontend-uplift iterated toward a richer slider widget. Suggest one is newer, one is superseded; audit which is live before restructure.
- **styles.py (674)**: Large but not a monolith — it's a data file. Single `_render_stylesheet(palette)` function + palette dicts + token constants. Dense but well-organized (WCAG test coverage in tests/test_styles_palette.py anchors every token).

---

## 4. surfaces.py Deep Dive

**Structural breakdown (1,808 LOC across ~1,555 LOC code + ~250 LOC docstrings/comments):**

```
surfaces.py structure:
├── Imports + config (lines 1–40)
│   └── numba.config.THREADING_LAYER = "workqueue"  [LOAD-BEARING for e5 Numba kernels]
│
├── Dataclasses (lines 42–97)
│   ├── ParamSpec (frozen) — slider metadata  [CORE: used by all 14 generators]
│   └── Surface — generator + params list
│
├── Helper predicates (lines 99–172)
│   ├── should_render_on_drag(surface) — dispatcher predicate
│   └── dispatch_mode(surface, in_drag) — three-state router (coarse/full/skip)
│
├── SHARED IMPLICIT PIPELINE (lines 173–313)
│   └── _marching_cubes_to_polydata(field, bounds)  [CORE: used by 11 implicit generators]
│       ├── Pre-validates zero-crossing
│       ├── Contours via VTK Flying Edges (replaced scikit-image in e6)
│       ├── Taubin smoothing (n_iter=20, pass_band=0.1)
│       ├── compute_normals() — refresh after smoothing
│       └── AI-15: handles "No real zero set" errors + warnings catch
│
├── NUMBA KERNELS (11 × ~30–40 LOC each, lines 315–683)
│   └── @njit(parallel=True, cache=True) field evaluators for:
│       ├── Fermat quartic (_fermat_field_kernel)
│       ├── Kummer surface (_kummer_field_kernel)
│       ├── Enriques Figs 1,2,3,4 (_enriques_fig*_field_kernel)
│       ├── Dwork pencil (_dwork_field_kernel)
│       ├── Fano Klein cubic (_klein_cubic_field_kernel)
│       ├── Fano Segre cubic (_segre_cubic_field_kernel)
│       ├── Fano two-quadrics (_two_quadrics_field_kernel)
│       └── Fano sextic double solid (_sextic_double_solid_field_kernel)
│       [NOTES: Each kernel produces (n,n,n) float64 array fed to _marching_cubes_to_polydata]
│       [NOTES: AI-21 constraint: numba.config.THREADING_LAYER pinned at import; thread-safety critical]
│
├── SHARED PARAMETRIC PIPELINE (lines 686–747)
│   ├── _grid_to_polydata(X, Y, Z) — triangulates (X,Y,Z) 2D grids
│   └── _concat_polydata(meshes) — glues N disconnected patches together
│       [NOTES: AI-6: Hanson trio INTENTIONALLY skips Taubin (C² already)]
│       [NOTES: AI-7: Hanson uses cell_normals=True, consistent_normals=False for per-patch winding]
│
├── GENERATOR FUNCTIONS (14 × 50–200 LOC each, lines 749–1554)
│   ├── [K3 FAMILY]
│   │   ├── fermat_quartic(α, β, γ, c, n) → implicit via _marching_cubes_to_polydata
│   │   └── kummer_surface(μ², n) → implicit
│   │
│   ├── [ENRIQUES FAMILY]
│   │   ├── enriques_figure_1(c, n, hq_smoothing=False) → implicit + opt-in double-Taubin
│   │   ├── enriques_figure_2(λ₀, λ₃, c, n, hq_smoothing=False) → implicit + opt-in
│   │   ├── enriques_figure_3(k, n) → implicit (no HQ kwarg — not double-curve)
│   │   └── enriques_figure_4(τ, φ, n) → implicit (no HQ kwarg)
│   │
│   ├── [CALABI–YAU FAMILY]
│   │   ├── calabi_yau_quintic(grid, n) → parametric, 25 patches (Hanson)
│   │   ├── calabi_yau_cubic(grid, n) → parametric, 9 patches (Hanson)
│   │   ├── calabi_yau_asymmetric(grid, n) → parametric, 15 patches (Hanson 5,3)
│   │   └── calabi_yau_dwork(ψ, n) → implicit (only CY3 implicit figure)
│   │
│   └── [FANO 3-FOLD FAMILY]
│       ├── fano_klein_cubic(z₀, n) → implicit
│       ├── fano_segre_cubic(a, b, n) → implicit
│       ├── fano_two_quadrics(p, q, μ, ε, n) → implicit
│       └── fano_sextic_double_solid(α, r₆, n) → implicit
│
├── PARAMETRIC HELPER (lines 1087–1180)
│   └── _hanson_cross_section(n₁, n₂, ξ_max, α, grid) — shared Hanson projection logic
│       [NOTES: Called by the 3 CY3 parametric generators + mapped to ℝ³ projection]
│
└── VARIETIES REGISTRY (lines 1555–1800+)
    ├── VARIETIES: dict[str, dict[str, Surface]]
    │   └── Nested keys: variety → subtype → Surface(label, generate, params)
    ├── VARIETY_TOOLTIPS: dict[str, str]
    └── SUBTYPE_TOOLTIPS: dict[str, str]
```

### Natural Split Lines in surfaces.py

1. **Implicit vs. Parametric pipelines** (line 173 implicit, line 686 parametric) — separate helper blocks, distinct contract (scalar field → grid-based vs. 2D array → triangulated).
2. **Numba kernels block** (lines 315–683, ~370 LOC) — 11 isolated @njit functions with no dependencies within this range. All feed the same _marching_cubes_to_polydata.
3. **Generators cluster** (lines 749–1554) — 14 functions grouped by family (K3, Enriques, CY3, Fano). Each generator is self-contained; dependencies are only on the two pipeline helpers (_marching_cubes_to_polydata or _grid_to_polydata).
4. **Registry segment** (lines 1555+) — purely data; could live separately but would require import-time Surface instantiation in a separate module.

### Import Dependencies (surfaces.py reads-from)

- **numpy, pyvista** — mesh construction, scalar-field ops
- **numba** — @njit kernel decorators, parallel tracing
- **scikit-image.measure.marching_cubes** — LEGACY; replaced by VTK Flying Edges in e6 but may still be imported (grep to verify)
- **Internal:** None (self-contained)

---

## 5. The Four Panel Files Deep Dive

### parameters_panel.py (368 LOC, **OLDER ITERATION**)

**Sections:**
- Imports + setup (lines 1–30)
- `ParametersPanel` class: ~300 LOC
  - `__init__`: builds slider grid from `Surface.params` (ParamSpec list)
  - `_build_ui`: layout + GridLayout + label/slider pairs
  - `rebuild_from_surface(surface)`: dynamic rebuild on subtype change (clears old, re-populates from new Surface.params)
  - `values()`: returns kwargs dict ready for `surface.generate(**kwargs)`
  - `reset_to_defaults()`: slot that resets all sliders to ParamSpec.default

**Architecture:** Single-class, **stateful slider storage** in the panel itself. Layout is tight GridLayout with no RichParametersPanel-like affordances. Used by app.py as `self._parameters_panel`. 

**Signal wiring:** `value_changed = Signal(bool)` fires on release (not drag, per AI-10 cache comment).

---

### parameter_grid_panel.py (713 LOC, **NEWER ITERATION**)

**Sections:**
- Imports (lines 1–50)
- `RichParametersPanel` class (~500 LOC)
  - `__init__`: grid layout + "Reset all to defaults" button + busy-label indicator
  - `_build_ui`: richer layout with labels, ranges, descriptions (per ParamSpec)
  - `_build_header`, `_build_label_with_description`: modular layout helpers
  - `refresh_range_label`: updates min/max display as slider moves
  - `rebuild_from_surface`: dynamic rebuild
  - `values()`: returns kwargs dict
  - `reset_to_defaults()`: slot
  - Multiple helper methods for visual affordances
- `BusyLabel` class (~40 LOC)
  - `QLabel` subclass that dims/un-dims during computation
  - Signals: `setEnabled(False)` during compute, `True` on result

**Architecture:** Single "mega-panel" class with a helper inner class. Adds "busy" visual feedback (BusyLabel) — a newer affordance not in the older ParametersPanel. Has richer per-parameter UI (descriptions, range bounds visible).

**Signal wiring:** Same `value_changed` signal pattern as older; emits on release.

---

### appearance_panel.py (666 LOC)

**Sections:**
- Imports (lines 1–50)
- `AppearancePanel` class (~600 LOC)
  - `__init__`: set up color picker, opacity slider, style toggles, shading buttons, background, display & quality group
  - `_build_ui`: modular layout with GroupBox sections
  - `_build_surface_color_group`: color picker + swatch
  - `_build_opacity_group`: opacity slider
  - `_build_style_group`: solid / wireframe / edges toggles (checkable QPushButton per AI-15)
  - `_build_shading_group`: flat / smooth / Phong toggles
  - `_build_background_group`: background color + gradient toggle
  - `_build_toggles_group`: Display & Quality (Wireframe, Show-edges, Double-pass smooth)
  - `apply_to_actor(actor)`: pushes all state to the VTK actor's properties
  - `apply_background()`: sets plotter background
  - `set_default_color(hex_str)`: seeds surface-color swatch from variety palette
  - `set_culling(value)`: Enriques variety-gated back-face culling (AI-13 gating)
  - `set_hq_smoothing_eligible(bool)`: enables/disables Double-pass toggle (Enriques figs 1+2 only)
  - `refresh_icons(theme)`: re-renders qtawesome icons for theme changes

**Architecture:** Single monolithic class with 6 GroupBox sections. Heavy use of `setProperty("role", "...")` for theme-aware QSS (ai-11 anti-pattern). Per-group signal wiring: color changes → `_on_surface_color_changed` → status bar + swatch update; opacity/style/shading/bg changes → `_on_*_changed` → `apply_to_actor()` + `plotter.render()` (AI-10 safe — re-render only, no regenerate); HQ smoothing toggle → `hq_smoothing_changed` signal → MainWindow handles full regenerate.

---

### view_panel.py (503 LOC)

**Sections:**
- Imports (lines 1–40)
- `ViewPanel` class (~480 LOC)
  - `__init__`: set up all docks and factory-generated camera preset buttons
  - `_build_ui`: GroupBox layout (Camera Presets, Domain Clip, Scene Aids, Screenshot)
  - `_make_view_callback(name)`: factory that builds a camera-preset slot (calls plotter method + render())
  - `clip_to_domain(mesh)`: **PURE FUNCTION** — scalar-clips mesh to sphere or cube domain, returns (clipped, overlay)
  - `_on_domain_mode_changed`, `_on_domain_radius_changed`: slots that call clip_to_domain and re-render
  - `_on_screenshot`: file dialog + plotter.screenshot() + save PNG
  - `_on_toggle_*`: scene aids (axes, bounding box, grid)
  - `refresh_icons(theme)`: re-render qtawesome preset icons for theme swaps

**Architecture:** Single class; 4 GroupBox sections. The `clip_to_domain` method is the crown jewel — a **pure function** (no side effects) that takes mesh + domain mode/radius and returns clipped mesh + overlay. Calls in `_apply_domain_and_render` in app.py. Signal wiring: preset buttons → camera state → render(); domain sliders → clip_to_domain() call + re-render(); screenshot button → file dialog + save.

---

## 6. Test Layout

**22 test files, 6,425 LOC, no conftest.py.**

| Test File | LOC | Coverage | Notes |
|---|---|---|---|
| test_styles_palette.py | 1,179 | styles.py, theme logic | WCAG contrast checks (light + dark), role selectors, token validation |
| test_numba_field_kernels.py | 708 | surfaces.py (11 kernels) | Equivalence tests: Numba vs. NumPy reference (45 parametrize blocks) |
| test_mesh_export.py | 451 | surfaces.py, export path | STL/OBJ/PLY save format tests |
| test_enriques_hq_smoothing.py | 441 | surfaces.py (enriques_fig_1,2 only) | HQ-smoothing opt-in: double-pass, vertex-move guard |
| test_mesh_generators.py | 358 | all 14 generators | Smoke tests (non-null PolyData at defaults), edge cases (no zero-set) |
| test_coarse_n.py | 323 | render_worker.py (dispatch_mode), surfaces.py | LOD preview floors per surface, dispatch routing |
| test_parameter_grid.py | 321 | parameter_grid.py | Slider tick ↔ value math (all 4 modes: linear, log, power, sqrt) |
| test_parameters_panel.py | 343 | ParametersPanel + ParamSpec | ParamSpec validation across all 14 generators |
| test_render_worker.py | 236 | render_worker.py (Qt-free parts) | is_stale_result predicate, MeshResult payload |
| test_icons.py | 347 | icons.py | qtawesome icon wrapper tests, Spin animation |
| test_clip_domain.py | 157 | view_panel.py | Pure-function clipping (sphere/cube scalar modes) |
| test_grid_helpers.py | 119 | surfaces.py grid helpers | _grid_to_polydata, _concat_polydata |
| [11 more] | 1,445 | various | test_qsettings_persistence, test_render_busy_spinner, test_status_bar_bbox, test_hq_disable_toast, test_render_queue_latest, test_clip_cache, test_debounce, test_typical_ms, test_marching_cubes_empty |

### Key test properties:

- **Qt-free** (AI-2): All 22 tests pure NumPy/PyVista/scikit-image. No pytest-qt, no QApplication in tests (blocks macOS offscreen segfault risk).
- **No conftest.py**: Fixtures and imports are inline per test file. Simple, transparent, few shared state hazards.
- **Parametrize-heavy**: test_numba_field_kernels.py uses @pytest.mark.parametrize for 45 combinations (kernel × parameters).
- **Pure-function focus**: test_clip_domain.py, test_grid_helpers.py, test_parameter_grid.py all test deterministic mathematical functions in isolation.
- **Coverage depth**: test_styles_palette.py has ~50+ contrast assertions (light + dark themes); test_mesh_generators.py covers all 14 generators + boundary edge cases (no-zero-set, singularities).

---

## 7. Import Graph (Best-Effort)

```
IMPORT ANALYSIS (grep -r "^from|^import" surfaces.py, app.py, panels)

Hub modules (imported by many):
  ✓ surfaces.py — imported by app.py (VARIETIES, generators), tests (all 14 generators + helpers)
  ✓ styles.py — imported by app.py, appearance_panel.py, all panels for COLOR_* tokens
  ✓ ui_helpers.py — imported by appearance_panel.py, view_panel.py, parameters_panel.py
  ✓ icons.py — imported by appearance_panel.py, view_panel.py, parameters_panel.py (icon refresh)
  ✓ parameter_grid.py — imported by parameters_panel.py (ParamSpec math)

Leaf modules (imported by few or none):
  ✓ render_worker.py — imported by app.py ONLY (background thread dispatch)
  ✓ parameter_grid_panel.py — imported by app.py ONLY (newer param panel, may coexist)

Cycles:
  ✗ NONE DETECTED. DAG structure clean (app.py at top, panels/surfaces at mid, helpers/styles at bottom)

Qt dependency tree:
  Top-level: app.py (QMainWindow)
    └── render_worker.py (QThreadPool/QRunnable — no GUI, signals only)
    └── appearance_panel.py (QDockWidget + QPushButton + QColorDialog)
        └── ui_helpers.py (pure utilities)
        └── icons.py (qtawesome — triggers QApplication initialization)
    └── view_panel.py (QDockWidget + buttons + QSlider)
        └── ui_helpers.py
        └── icons.py
    └── parameters_panel.py or parameter_grid_panel.py (QDockWidget + QSliders)
        └── parameter_grid.py (pure math, NO Qt)
        └── ui_helpers.py
    └── surfaces.py (NO Qt; pure NumPy/PyVista)
        └── render_worker.py uses surfaces.generate()

Cross-module signal flow:
  app.py ← appearance_panel (hq_smoothing_changed signal) → app.py._on_hq_smoothing_changed
  app.py ← view_panel (plotter reference via constructor) → clip_to_domain calls
  app.py ← parameters_panel (value_changed signal on release) → app.py._on_params_changed
```

**Assessment:** Clean DAG. surfaces.py at the root (pure compute). All panels depend on styles + ui_helpers but not on each other. render_worker bridges GUI and surfaces. No circular deps.

---

## 8. Tracked-but-Organizationally-Misplaced Files

Audit of root-level Python files for potential mis-organization:

- **app.py** ✓ CORRECT — main executable entry point; belongs at root
- **surfaces.py** ✓ CORRECT — central registry VARIETIES; imported by app.py and all tests
- **render_worker.py** ✓ CORRECT — tight dependency with app.py render orchestration
- **all panel files** ✓ CORRECT — single QDockWidget per file; imported by app.py
- **icons.py** ✓ CORRECT — tight coupling to panel files (refresh_icons calls)
- **styles.py** ✓ CORRECT — imported by 5+ modules; belongs at root for centralization
- **parameter_grid.py** ✓ CORRECT — pure math, tight coupling with parameters_panel.py
- **ui_helpers.py** ✓ CORRECT — shared utilities across panels

**Verdict:** No misplaced files. Everything at root has a clear reason. Repo is intentionally flat for small team iteration speed.

---

## 9. .claude/ Surface Review (Scope Guard)

**OUT OF SCOPE per the brief.** Cataloged below for awareness; will not be touched by `/repository-architect`:

```
.claude/
├── agent-memory/         [Claude memory snapshots; ~22 files, state tracking]
├── agents/               [Agent definitions for capability-scout, frontend-uplift, etc.]
├── commands/             [Claude Code custom slash commands]
├── notes/                [Roadmap artifacts, spike reports, adversary critiques, plans]
├── references/           [app-invariants.md, capability-scout/, frontend-uplift/, milestone-pipeline/]
├── scripts/              [Helper scripts for roadmap/milestone/scout phases]
├── settings.local.json   [User-local Claude Code config]
└── worktrees/            [Git worktrees from active skill runs]
```

These are standard Claude Code tool folders. The restructure command explicitly excludes `.claude/` and `.github/`.

---

## 10. AI-1..AI-15 Invariants (from app-invariants.md)

Listed verbatim, one-line summaries to flag constraints on restructure:

| Invariant | Summary | Restructure Impact |
|---|---|---|
| **AI-1** | PySide6 + PyVista + pyvistaqt (LGPL-friendly stack); no PyQt6/Mayavi/Plotly | LOCKS: cannot change Qt framework or 3D renderer |
| **AI-2** | Test suite is Qt-free (pure NumPy/PyVista); no pytest-qt (macOS offscreen segfault) | LOCKS: tests/ cannot add Qt fixtures or pytest-qt |
| **AI-3** | Render verification offscreen via `pv.OFF_SCREEN = True`, NOT `QT_QPA_PLATFORM=offscreen` | LOCKS: cannot construct MainWindow offscreen |
| **AI-4** | Domain clipping uses `clip_scalar`, NOT `clip_box` (clip_box invert semantics broken) | LOCKS: view_panel.clip_to_domain scalar-clip contract |
| **AI-5** | PyVista 0.46+ `clip_scalar` requires `scalars=` kwarg | LOCKS: clipping code must use kwarg form |
| **AI-6** | Implicit surfaces use marching cubes; parametric (Hanson) do NOT | LOCKS: cannot mix implicit + parametric pipelines in surfaces.py |
| **AI-7** | Hanson normals: `cell_normals=True, consistent_normals=False, auto_orient_normals=False` | LOCKS: Hanson normal handling in surfaces.py |
| **AI-8** | Surface/ParamSpec frozen dataclass contract + VARIETIES registry | LOCKS: cannot break dataclass or registry structure |
| **AI-9** | Re-entrancy guard `self._computing` around worker dispatch; no processEvents() re-entrance | LOCKS: app.py render pipeline re-entrancy guard |
| **AI-10** | Raw mesh cached; domain clip doesn't regenerate | LOCKS: view_panel._apply_domain_and_render must not regenerate |
| **AI-11** | Fully-qualified Qt enums (Qt.AlignmentFlag.AlignLeft, not Qt.AlignLeft) | SOFT: new code uses qualified form, existing code may drift |
| **AI-12** | WCAG AA text-contrast (≥4.5:1 body, ≥3:1 large text) on all visible text | LOCKS: styles.py palette tokens must meet contrast (test_styles_palette.py guards) |
| **AI-13** | 6-digit hex only (PyVista color parser rejects short `#888`) | SOFT: colors flowing into PyVista must be 6-digit; Qt stylesheet accepts both |
| **AI-14** | Generator function contract: `pv.PolyData` or `ValueError` | LOCKS: all 14 generators must return PolyData; no `print()` or `SystemExit` |
| **AI-15** | Math claim honesty: ≥2 sources + honest "real shadow" disclaimers for non-R³ varieties | LOCKS: tooltips + docstrings in surfaces.py + CONTEXT.md; Preview badge for LOD |

**Restructure-critical invariants:**
- **AI-1, AI-2, AI-3** — stack locks (no Qt/3D renderer changes)
- **AI-4, AI-5, AI-6, AI-7, AI-10** — algorithm locks (clipping, marching cubes, caching)
- **AI-9** — app.py re-entrancy guard (untouchable)
- **AI-12** — styles.py palette (WCAG guarded)

---

## 11. CONTEXT.md Sections Relevant to Restructure

### Section 4 — Architecture Conventions

**§4.1 Surface dataclass + VARIETIES registry:** Locked. ParamSpec and Surface are frozen dataclasses; VARIETIES is the central registry. Any restructure must preserve this contract.

**§4.2 Generator function contract:** Every generator returns `pv.PolyData` or raises `ValueError`. Implicit generators use `_marching_cubes_to_polydata`; parametric use `_grid_to_polydata` + `_concat_polydata`. AI-6 enforces separation.

**§4.3 MainWindow render pipeline:** Locked. The async worker dispatch + catch-up queue coalescing + `_computing` guard are AI-9-critical. Cannot change without re-architecting the entire render orchestration.

**§4.4 Re-entrancy guard:** Locked. `self._computing` single-flight guard (AI-9) is load-bearing. Lifting it requires numba threading-layer change (AI-21 footnote).

**§4.4a Session persistence:** QSettings-based. V1 persists window geometry + dock state + last variety/subtype. V2/V3 (out-of-scope) would add per-subtype slider values, theme preference, etc.

**§4.5 Domain clipping:** Locked to scalar-clipping approach (AI-4, AI-5). Both sphere and cube modes use the same underlying mechanism.

### Section 9 — Things Explicitly NOT Done (and Why)

- **Mesh export** — shipped in mesh-export-stl-obj-ply-2026q3-e1. Exports `_raw_mesh` (unclipped) via PyVista.PolyData.save().
- **Render-busy spinner** — shipped in render-busy-spinner-2026q3-e1. Uses qtawesome Spin animation on a `QPushButton(flat=True)` added via `addPermanentWidget()` to status bar.
- **No first-launch auto-render** — intentional (research tool presumption).
- **No confirmation on Reset to Defaults** — intentional (non-destructive, avoid friction).
- **No end-to-end UI tests** — pytest-qt blocked by AI-2 (macOS offscreen segfault).
- **No automated background-thread lifecycle tests** — Qt+VTK not testable in CI; manual gate + spike script.

---

## 12. README.md "How to Extend" Section

**Verbatim (README.md §Extending the app):**

> **Adding a new model to an existing variety** is straightforward:
> 
> 1. Write a generator function in `surfaces.py` that returns a `pv.PolyData`. Implicit generators sample a scalar field on a cubic grid and call `_marching_cubes_to_polydata(field, bounds)`. Parametric generators build `(X, Y, Z)` 2D arrays and call `_grid_to_polydata(X, Y, Z)`.
> 2. Define a `<NAME>_PARAMS` list of `ParamSpec(name, label, minimum, maximum, default, step, suffix, description)` — one per slider.
> 3. Add `Surface(label, generator, params)` to the appropriate inner dict of `VARIETIES`. Use a `[Fig. N]` suffix in the dropdown key for consistency.
> 4. Add tooltip entries to `SUBTYPE_TOOLTIPS` (and `VARIETY_TOOLTIPS` if introducing a new family).
> 5. Add at least a smoke test in [tests/test_mesh_generators.py](tests/test_mesh_generators.py) and a parameter-range entry in [tests/test_parameters_panel.py](tests/test_parameters_panel.py).
> 
> **Adding a whole new variety family** is a larger effort — see Section 6 of [CONTEXT.md](CONTEXT.md) for the 5-phase pipeline (math research → implementation → adversarial review → remediation → UX pass) used for the existing four families.

**Implications for restructure:** The documented extension path assumes `surfaces.py` is the single entry point for generators + VARIETIES registry. A restructure must not break this path; if surfaces.py is split, the registry must remain accessible at the documented location.

---

## 13. Honest Assessment

### Already Good (Don't Fix)

1. **surfaces.py organization** — Despite 1,808 LOC, the internal structure is clean: imports, dataclasses, helpers, Numba kernels block, generators (grouped by family), grid helpers, registry. Each section is isolated. Monolith is justified (tight coupling on field → mesh pipeline).
2. **Test coverage** — 6,425 LOC tests covering 7,849 LOC source (81.8% ratio). No conftest.py means no fixtures to maintain, but comprehensive per-subsystem test files. WCAG contrast checks are exemplary.
3. **Panel architecture** — Single-class-per-file (ParametersPanel, AppearancePanel, ViewPanel). Clean signal/slot wiring. AppearancePanel's "Display & Quality" group separation shows thoughtful distinction (display props vs. mesh-changing props).
4. **Stylesheet centralization** — styles.py is a single source of truth. Palette tokens are theme-aware (light + dark dicts); WCAG validation is automated.
5. **Dataclass contracts** — Surface + ParamSpec + VARIETIES registry are load-bearing; changing them breaks the entire extension path. Current design is sound.
6. **Async render dispatch** — realtime-variety-render-e4 moved surface.generate() to a background worker thread. AI-9 re-entrancy guard is well-designed. Catch-up queue coalescing is correct.

### Clearly Bad (Genuine Quick Wins)

1. **Two parameter panel implementations coexist** (parameters_panel.py + parameter_grid_panel.py, 368 + 713 LOC). One appears to supersede the other. Audit which is live; consolidate or remove.
2. **Import *from* parameter_grid_panel by reference** — if parameter_grid_panel.py is the newer iteration, surfaces.py/app.py should import RichParametersPanel, not ParametersPanel. Verify app.py instantiation.
3. **Numba field kernels in surfaces.py** — 11 isolated @njit functions (370 LOC) could move to a `_numba_kernels.py` without breaking imports. Would improve readability but is not urgent (all kernels are internal helpers).

### Debatable (Context-Dependent)

1. **Flat repo vs. `src/` layout** — At 7,849 LOC, the flat root is still reasonable for a single-module app. If the app grows to 15+ files, moving to `src/` or `avc/` with subpackages becomes valuable. Current size does not justify it.
2. **Icon lazy-init timing** — icons.py defers qtawesome cold-boot to first icon paint (~150–200 ms) rather than app startup. This is good for perception but defers the hiccup. Acceptable trade-off; not a quick win.
3. **parameter_grid.py as a separate file** — Pure math (tick ↔ value conversion) is 362 LOC. Could be inlined into parameters_panel.py, but it's cleaner separate. Keep as-is.
4. **Styles.py monolith** — 674 LOC, but it's a data file + single template function. Not a code smell; centralization is the point.

### What the Restructure CANNOT Touch

- **AI-1, AI-2, AI-3:** Stack locks (Qt framework, test suite, offscreen rendering)
- **AI-4, AI-5, AI-6, AI-7, AI-10:** Algorithm locks (clipping, marching cubes, caching, Hanson normals, raw-mesh caching)
- **AI-8:** Surface/ParamSpec dataclass contract + VARIETIES registry structure
- **AI-9:** app.py re-entrancy guard (`self._computing`)
- **AI-12:** styles.py palette tokens (WCAG-locked values)

---

## 14. Files the Restructure CANNOT TOUCH WITHOUT LIFTING AN INVARIANT

| File:Line | Invariant | Reason |
|---|---|---|
| **surfaces.py:54–97** | AI-8 | Surface + ParamSpec dataclasses — frozen contract |
| **surfaces.py:1555+** | AI-8 | VARIETIES registry structure + keys |
| **surfaces.py:173–313** | AI-6 | _marching_cubes_to_polydata — implicit pipeline lock |
| **surfaces.py:686–747** | AI-6 | _grid_to_polydata + _concat_polydata — parametric lock |
| **view_panel.py:clip_to_domain** | AI-4, AI-5 | Scalar-clipping implementation (clip_scalar with scalars= kwarg) |
| **app.py:render dispatch logic** | AI-9, AI-10 | Re-entrancy guard + raw-mesh caching pattern |
| **styles.py:palette dicts** | AI-12 | WCAG-compliant token values (guarded by test_styles_palette.py) |
| **app.py:_computing guard** | AI-9 | Single-flight check; critical for re-entrancy safety |

---

## 15. Final Summary

**AVC Repository State (as of 2026-05-23):**

- **7,849 LOC source** + **6,425 LOC tests** in a **flat, 11-file root layout** (no `src/` subdirs).
- **3 monoliths >500 LOC:** app.py (1,893 — render orchestration), surfaces.py (1,808 — 14 generators + kernels), parameter_grid_panel.py (713 — newer param panel).
- **Biggest hotspot:** surfaces.py contains 11 Numba field kernels, 14 generator functions (grouped by variety family), shared pipeline helpers, and the central VARIETIES registry. Natural split lines exist between implicit vs. parametric pipelines, but no partition is urgent.
- **Second hotspot:** app.py is the MainWindow monolith. Contains render dispatch (async worker + catch-up queue), dock wiring, theme menu, status-bar updates, and QSettings persistence. Split lines exist (render vs. theme vs. persistence) but are tightly coupled via shared state.
- **All architecture locked by AI-1..AI-15 invariants.** Any substantial restructure must preserve: Qt framework (AI-1), test Qt-free design (AI-2), dataclass + registry contracts (AI-8), re-entrancy guard (AI-9), raw-mesh caching (AI-10), clipping algorithm (AI-4, AI-5).
- **No circular dependencies.** Clean DAG: surfaces.py at root (pure compute), panels depend on styles + ui_helpers, app.py orchestrates all.
- **Test suite exemplary:** 22 files, 6,425 LOC, Qt-free, parametrize-heavy, WCAG-validated. No conftest.py; fixtures inline.
- **Quick wins:** (a) consolidate parameter panel implementations (one may be dead code); (b) audit app.py instantiation (parameters_panel vs. parameter_grid_panel).
- **DO NOT TOUCH:** AI-9 re-entrancy guard, AI-10 caching pattern, AI-4/AI-5 clipping algorithm, AI-8 dataclass contracts, AI-12 palette values.

**Recommendation:** The flat layout is appropriate for the current codebase size. If a future roadmap introduces 10+ new features or splits surfaces.py into per-family modules, then `src/algebraic_variety_viewer/` subpackage structure becomes justified. Until then, the current organization is clean and permits rapid iteration.

---

*Scout D audit complete.*  
*Generation: 2026-05-23T11:45:00Z*  
*Status: Ready for `/repository-architect` design phase.*

