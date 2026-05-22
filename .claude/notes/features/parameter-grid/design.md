# Parameter-Grid Mode — Design Decision Document

Feature: a 2D/3D grid parameter-adjustment mode for the Parameters dock, with a
draggable dot whose motion drives the mapped parameters exactly as the sliders do.

---

## 1. Codebase examination findings

- **`parameters_panel.py`** — `ParametersPanel(QWidget)` exposes `params_changed =
  Signal(dict)`. `set_specs(specs)` rebuilds on variety switch; `values()` returns
  `{name: value}`. Per-param slider state lives in `_sliders` / `_value_labels`
  dicts keyed by `ParamSpec.name`. The render discipline is deliberate
  (CONTEXT §8.5, AI-9, INT-NO-1):
  - `slider.valueChanged` → `_on_value_changed` → updates the **readout label only**.
  - `slider.sliderReleased` → `_on_slider_released` → emits `params_changed` →
    one mesh re-render in `app.py`.
- **`app.py`** — `params_changed` is wired to `_on_params_changed` (app.py:129/245),
  which calls `_render_current(reset_camera=False)`. The `_computing` re-entrancy
  guard (app.py:91/277/340) wraps the whole render path; `processEvents()` is
  called once inside it. `Qt.AA_ShareOpenGLContexts` is set in `main()`.
- **`surfaces.py`** — `ParamSpec(name,label,minimum,maximum,default,step,suffix,
  description)` frozen dataclass. `Surface.params: list[ParamSpec]`. Param counts
  across the registry: most varieties have 1 param; `enriques_figure_2` has 3;
  `fano_two_quadrics` has 4; **`fermat_quartic` (Fermat quartic K3) has 4**
  (`c, alpha, beta, gamma`). So both the 3-axis path and the 4+-param residual-slider
  split are exercised by the existing registry.
- **`styles.py`** — `PALETTE_LIGHT` token dict is the single source of truth.
  `tests/test_styles_palette.py` enforces 6-digit hex on every token, asserts no
  raw `color="#..."` literal in `app.py`/`appearance_panel.py`, and asserts
  `APP_STYLESHEET` contains only palette hex. New colors MUST be added as named
  tokens here.
- **`tests/test_parameters_panel.py`** — Qt-free: it re-implements the tick↔value
  formulas as module-level helpers and parametrizes over the real `ParamSpec`
  lists. The panel widget is never instantiated. New tests follow this shape.

## 2. Library decision — ZERO new dependencies

Respecting AI-1 (PySide6 + PyVista + pyvistaqt only) and the LGPL-redistribution
lens. No new dependency is added.

### 2D grid — `QGraphicsView` + `QGraphicsScene` (pure Qt)

A `QGraphicsScene` holds gridlines (`QGraphicsLineItem`), axis labels
(`QGraphicsSimpleTextItem`) and a draggable `QGraphicsEllipseItem` dot. This is
pure PySide6 — zero new dependency, full mouse-drag control, trivial to label.
Confirmed: no blocker. **Chosen.**

### 3D grid — secondary `pyvistaqt.QtInteractor` with `add_sphere_widget()` — REJECTED in favor of option (c)

Three options were evaluated for the 3D grid:

- **(a)** A secondary `QtInteractor` showing a unit cube with PyVista's
  `add_sphere_widget()` (a draggable 3D sphere with a move callback). Stays inside
  AI-1. **Rejected** for this milestone: a second live `QtInteractor` is a second
  VTK GL context. `Qt.AA_ShareOpenGLContexts` mitigates but does not eliminate
  context-teardown ordering hazards (the existing `closeEvent` only closes the
  primary plotter). It also makes the pure-logic/Qt split leakier — the sphere
  widget's callback fires continuously during drag and would need its own
  throttle to honor INT-NO-1. Higher risk, more surface area.
- **(b)** Three linked 2D projections. Workable but the UX of three half-size
  panels is cramped and the "which dot is canonical" question is confusing.
- **(c)** A single `QGraphicsView` rendering an **isometric projection** of a
  3-axis box, with the dot constrained to drag **on one axis-plane at a time**
  (the user picks the active drag-plane via a small selector). This reuses the
  exact same 2D `QGraphicsView` machinery, keeps ALL coordinate math in the pure
  module, and adds **zero** new GL context. The depth ambiguity inherent to
  "drag a 3D point with a 2D mouse" is resolved honestly by making the
  constraint explicit and user-controlled rather than guessed.

**Chosen: (c).** It is the lowest-risk choice that stays within AI-1, adds no
dependency, and keeps the testable math in one Qt-free module. The known
limitation (drag-plane must be chosen explicitly) is documented in §6.

## 3. UX shape — a toggle button, NOT a tab

The brief mentioned both "toggle button" and "new tab". Chosen: **a toggle
button** (`QPushButton` with `setCheckable(True)`) at the top of the Parameters
dock labelled "Grid mode". Rationale:

- A `QTabWidget` would imply two independent pages of state; the feature is
  explicitly *one* source of parameter truth viewed two ways. A toggle
  communicates "same data, different control surface" correctly.
- The dock is narrow; a tab bar steals vertical space permanently. A single
  checkable button is one row.
- The toggle is **disabled with an explanatory tooltip** for 0/1-param varieties
  ("Grid mode needs at least 2 parameters") — a disabled tab is an awkward
  affordance, a disabled button is idiomatic.

When the toggle is on, the slider stack is hidden and the grid panel
(`ParameterGridPanel`) is shown; when off, the reverse. Toggling preserves the
current values (see §5).

## 4. 4+-param varieties — grid axes vs residual sliders

A grid hosts 2 axes (2D) or 3 axes (3D). For the Fermat quartic (4 params):

- The user picks **how many axes** the grid has (2 or 3) via a small selector,
  and **which `ParamSpec` maps to each axis** via one `QComboBox` per axis.
- Params not assigned to any axis fall through to **residual sliders** rendered
  beneath the grid — ordinary slider rows reusing the existing `_build_row`
  logic.
- Same-param-on-two-axes is rejected: the axis combos are kept mutually
  exclusive (`assign_axes` in the pure module computes the legal split; the Qt
  layer re-syncs the combos after every change).
- 2-param varieties: 2D grid, both axes auto-assigned, no residual sliders.
  3-param varieties: default to 3D grid, all three auto-assigned, no residuals
  (the user may still drop to 2D, leaving one residual slider).

## 5. Data flow & render discipline (CRITICAL)

One logical source of truth per active view. In **slider mode** the
authoritative values are computed on demand from the `QSlider` tick
positions (`ParametersPanel._slider_to_value`). In **grid mode** the
authoritative store is `ParameterGridPanel._values` (a `dict[str, float]`);
`ParametersPanel.values()` delegates to `ParameterGridPanel.values()` while
the grid toggle is checked. Toggling the view pushes the outgoing view's
values into the incoming view (`_on_grid_toggled`) so the two never diverge
— `ParametersPanel` itself holds no standalone value dict.

```
ParameterGridPanel  (Qt widget, parameter_grid_panel.py)
  dot mouse-press                 → begin drag
  dot mouse-move (while dragging)  → pure-module: scene-coord → value (clamped)
                                   → update value readouts ONLY
                                   → (no signal, no re-render)   ← INT-NO-1
  dot mouse-release                → emit grid_params_changed(dict)
                                          │
ParametersPanel ──────────────────────────┤  (re-syncs sliders to new values,
  params_changed (existing Signal)  ◀──────┘   then re-emits its own signal)
          │
app.py:_on_params_changed → _render_current(reset_camera=False)
          │
   guarded by self._computing  (AI-9) — single render path, unchanged
```

The grid does **not** add a second render path. It funnels through the existing
`params_changed` → `_on_params_changed` route, so the existing `_computing`
guard covers it. No new `processEvents()` is introduced.

While dragging, only the live numeric readouts update (and, because the two
views share `ParametersPanel`'s value dict, the sliders are re-synced on
release too). This is the exact two-phase discipline the sliders already use.

## 6. Module split & testability (AI-2)

- **`parameter_grid.py`** — pure Python, NO `PySide6`/`pyvista` imports at module
  top level. Contains:
  - `value_to_norm(value, spec)` / `norm_to_value(norm, spec)` — value ↔ [0,1].
  - `norm_to_scene(norm, length)` / `scene_to_norm(scene, length)` — [0,1] ↔
    pixel coordinate along an axis (with Y-axis inversion handled by the caller).
  - `value_to_scene` / `scene_to_value` round-trip composites, with clamping to
    `[minimum, maximum]`.
  - `grid_enabled(specs)` — predicate: `len(specs) >= 2`.
  - `default_axis_count(specs)` — 2 for exactly-2-param, else 3 if >=3 (capped
    at 3); `min(3, len)`.
  - `assign_axes(specs, axis_names)` → `AxisAssignment(axes, residual)` — maps
    chosen `ParamSpec`s to axes and computes the residual list; raises on
    duplicate assignment.
  - `clamp_value(value, spec)`.
- **`parameter_grid_panel.py`** — the Qt widget layer (`QGraphicsView` scene,
  draggable dot, axis `QComboBox`es, residual slider rows). Imports from
  `parameter_grid.py`. This keeps `parameters_panel.py` from bloating.
- **`parameters_panel.py`** — gains the "Grid mode" toggle and a
  `ParameterGridPanel` instance; owns the shared value dict; relays
  `grid_params_changed` into its existing `params_changed` signal.
- **`styles.py`** — new `PALETTE_LIGHT` tokens for gridlines, dot fill, dot
  border, axis labels, grid background, isometric box wireframe.
- **`app.py`** — no wiring change needed (the grid funnels through the existing
  `params_changed` signal). Untouched unless a defect surfaces.

## 7. Tests (`tests/test_parameter_grid.py`, Qt-free)

- value↔scene round-trip for representative `ParamSpec`s (Fermat, Kummer, CY).
- `grid_enabled` predicate: 0/1 param → False; 2/3/4 param → True.
- `default_axis_count`: 2-param → 2; 3-param → 3; 4-param → 3.
- `assign_axes` for 2/3/4-param varieties; residual split for the 4-param
  Fermat quartic (2 axes → 2 residual sliders; 3 axes → 1 residual slider).
- duplicate-param-on-two-axes → raises.
- clamping: a dragged scene coordinate past either end maps to exactly
  `minimum` / `maximum`.
