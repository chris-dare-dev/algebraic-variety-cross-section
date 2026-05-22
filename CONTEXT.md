# CONTEXT — Algebraic Variety Viewer

**Audience.** This file is a handoff document for a future Claude session that may continue this project. It captures the *why* behind decisions, the conventions in use, and the failure modes encountered, so a fresh session can be productive immediately. Read this end-to-end before editing.

**Last updated.** End of the third "variety pass" — Calabi–Yau 3-folds added on top of K3 + Enriques. 13 commits on `main`. 120 tests passing.

---

## 1. What this app is

A **PySide6 + PyVista** desktop app that lets a user pick an algebraic variety from cascading dropdowns and renders it in an interactive 3D widget. The user can rotate / zoom / pan natively (VTK trackball), tune surface-specific parameter sliders, change colors / wireframe / opacity, clip to a spherical or cubic region, and screenshot.

**Three varieties currently supported, each with multiple subtypes / figures:**

| Variety | Subtypes | Pipeline |
|---|---|---|
| K3 surface | Fermat quartic, Kummer surface | implicit (marching cubes) |
| Enriques surface | 4 figures: Canonical sextic, Diagonal λ-family, Cayley symmetroid, Icosahedral sextic | implicit |
| Calabi–Yau 3-fold | 4 figures: Hanson quintic, Hanson cubic torus, Hanson asymmetric (5,3), Dwork pencil | **3 parametric** + 1 implicit |

The Calabi–Yau pass is the only one with a non-implicit pipeline — the three Hanson cross-sections are parametric immersions (param grid → triangulated PolyData), since CY3 visualization tradition is fundamentally Hanson-1994 parametric, not implicit.

---

## 2. Repo layout

```
algebraic-variety-cross-section/
├── app.py              MainWindow — dropdowns, three docks, plotter wiring, async render dispatch
├── render_worker.py    Background-thread mesh worker (QThreadPool/QRunnable) — realtime-variety-render-e4
├── surfaces.py         All mesh generators + Surface/ParamSpec dataclasses + VARIETIES registry (~840 LOC)
├── parameters_panel.py Dynamic slider panel; rebuilds from each Surface's ParamSpec list (~220 LOC)
├── appearance_panel.py Color / wireframe / opacity / shading panel (right dock) (~300 LOC)
├── view_panel.py       View presets, camera, scene aids, domain clip, screenshot (left dock) (~420 LOC)
├── styles.py           Centralized stylesheet constants (palette, typography, dock-header CSS) (~140 LOC)
├── tests/              pytest suite — pure NumPy/PyVista, no Qt fixtures (AI-2)
│   ├── test_mesh_generators.py     smoke tests for every generator + edge cases
│   ├── test_parameters_panel.py    static slider tick↔value math
│   ├── test_clip_domain.py         ViewPanel.clip_to_domain pure-function tests
│   ├── test_marching_cubes_empty.py raises on empty fields
│   ├── test_render_worker.py       is_stale_result + MeshResult (Qt-free worker units)
│   └── test_grid_helpers.py         _grid_to_polydata + _concat_polydata
├── requirements.txt    Pinned dep ranges with upper bounds (PySide6 <7, pyvista <0.49, etc.)
└── .venv/              Python 3.12 virtualenv — use `.venv/bin/python` and `.venv/bin/pytest`
```

Don't commit `.claude/` — it's in `.gitignore` along with `.venv/`, `__pycache__/`, etc.

---

## 3. Stack rationale (decisions baked in)

These choices were made early by an Opus research agent. Don't relitigate them without good reason.

- **PySide6** over PyQt6 — LGPL is friendlier than GPL for redistribution. API is identical.
- **PyVista + pyvistaqt** — `QtInteractor` widget drops a real VTK render window into a `QMainWindow`, native trackball rotate/zoom/pan come for free. Toggling wireframe / colors / background is one-line property assignments.
- **VTK Flying Edges (`vtkFlyingEdges3D`)** for implicit surfaces — `pv.ImageData(...).contour([level], method="flying_edges")`. SMP-threaded, ~3-4× faster than `skimage.measure.marching_cubes` on the isocontour step (measured n=240: 298 ms → 98 ms), mathematically identical. Replaced scikit-image in realtime-variety-render-e6 / CAND-1; scikit-image is no longer a dependency.
- **Adaptive bounds** for the Fermat quartic family — the box is computed from `c` and `γ` so axial arms always fit. Don't hard-code box sizes for new generators with wide parameter ranges.
- **Taubin smoothing post-isocontour** — `mesh.smooth_taubin(n_iter=20, pass_band=0.1)` is volume-preserving; vanilla Laplacian shrinks geometry.
- **Gradient-based normals seeded by the contour** — `contour(..., compute_normals=True)` seeds analytic gradient normals from the scalar field; `compute_normals()` rederives per-vertex normals after Taubin smoothing for shading consistency.
- **Numba JIT for the hottest field kernels** — `@njit(parallel=True, cache=True)` kernels in `surfaces.py` (`_fermat_field_kernel`, `_enriques_fig1_field_kernel`) evaluate the scalar field for the two highest-cost implicit generators (Fermat quartic, Enriques canonical sextic), measured ~200-370× faster than NumPy meshgrid-broadcasting (realtime-variety-render-e5 / CAND-2; field eval was 41-45% of `generate()` latency). numba is BSD-2-Clause — a pure *compute* dependency, not a renderer, so AI-1-clean. **Process-global side-effect:** `surfaces.py` import sets `numba.config.THREADING_LAYER = "workqueue"` (keeps Numba's thread pool off VTK's SMP pool); this is a process-wide write — importing `surfaces` pins the layer for the whole process. `cache=True` persists compiled kernels to `__pycache__/` (gitignored; keyed by a source hash so a kernel edit auto-invalidates); the first cold-cache Fermat/Enriques render pays the ~400-800 ms JIT compile **on the e4 worker thread** (off the GUI thread — no freeze), so no eager startup warm-up is used. v0 scope is these 2 of 8 implicit generators; the rest are a future v1.
- **qtawesome for button icons** — MIT-licensed icon font wrapper (PySide6-compatible since v1.4.1). Lazy-imported via [`icons.py`](icons.py) so the ~150-200ms font-cache cold-boot fires at first icon paint, not at app launch. Icon color resolves from the active palette's `TEXT_VALUE` token so the same icon works in both themes. Added in qtawesome-icons-2026q2-e1 (UPL-4 v0 from the 2026q2-graph-and-window uplift, covering Reset Camera / Screenshot / Reset Defaults); extended in qtawesome-icons-2026q2-e2 (UPL-4 v1) to the 7 View-panel camera presets (`mdi6.axis-{x,y,z}-arrow` with `rotated=180` for the minus directions, `mdi6.axis-arrow` for Isometric) and the 2 Appearance-panel display toggles (`mdi6.grid` for Wireframe, `mdi6.border-outside` for Show-edges — perceptually distinct at 16px). The render-busy spinner remains deferred to a future v2 milestone — it is simply not yet built. (Its original AI-9 deferral rationale, `QMovie.updated` firing during `QApplication.processEvents()` in `_render_current`, was mooted by realtime-variety-render-e4: that milestone moved `surface.generate()` onto a background-thread worker and removed the `processEvents()` call entirely, so the re-entrancy surface the spinner once risked no longer exists.)

**Avoid:**
- matplotlib mpl_toolkits.mplot3d — painter's-algorithm artifacts on self-intersecting surfaces, slow.
- Mayavi — broken on Apple Silicon as of 2025.
- Plotly / k3d — Jupyter-first, awkward in Qt.
- raw VTK — verbose; PyVista is the right level.

---

## 4. Architecture conventions

### 4.1 The Surface dataclass + VARIETIES registry

All surfaces are uniform from the GUI's POV:

```python
@dataclass(frozen=True)
class ParamSpec:
    name: str        # kwarg name passed to the generator
    label: str       # human-readable slider label
    minimum: float
    maximum: float
    default: float
    step: float = 0.01
    suffix: str = ""
    description: str = ""

@dataclass
class Surface:
    label: str       # status-bar friendly name; can include math symbols
    generate: Callable[..., pv.PolyData]
    params: list[ParamSpec]

VARIETIES: dict[str, dict[str, Surface]] = {
    "K3 surface": { ... },
    "Enriques surface": { ... },
    "Calabi–Yau 3-fold": { ... },
}
```

The dropdown shows the **outer keys** (variety) → **inner keys** (subtype). The inner key is what you see in the dropdown ("Hanson quintic  [Fig. 1]"); the `Surface.label` is what appears in the status bar after rendering. This split lets us include a `[Fig. N]` tag in the dropdown that matches the user's "Figure 1, Figure 2..." mental model from the original brief, while the more academic full label appears in the status bar.

**Two parallel tooltip dicts** — `VARIETY_TOOLTIPS` and `SUBTYPE_TOOLTIPS` — are also exported from `surfaces.py` and consumed by `app.py` to attach `Qt.ItemDataRole.ToolTipRole` to each combo item.

### 4.2 Generator function contract

Every generator returns a `pyvista.PolyData`. Implicit generators use `_marching_cubes_to_polydata(field, bounds)` which:
1. Validates the field has a zero-crossing (raises `ValueError("No real zero set...")` if not), and re-asserts that contract after contouring (a 0-point mesh also raises).
2. Contours via VTK Flying Edges — `pv.ImageData(...).contour([level], method="flying_edges")` (realtime-variety-render-e6 / CAND-1; replaced `skimage.measure.marching_cubes`). The scalar field is raveled in **Fortran order** because `np.meshgrid(..., indexing="ij")` and VTK `ImageData` disagree on axis order.
3. `mesh.smooth_taubin(n_iter=20, pass_band=0.1)` for volume-preserving smoothing. **No `clean()` pass** — Flying Edges already emits a watertight shared-vertex mesh, and a `clean()` here regresses shading (see §8.17).
4. `mesh.compute_normals(...)` to refresh after smoothing.

Parametric generators (CY3 Hanson family) skip this and use `_grid_to_polydata(X, Y, Z)` + `_concat_polydata(meshes)` to assemble triangulated patches directly. Note: Hanson cross-sections **intentionally skip Taubin smoothing** — the parametric grid is already C², and smoothing would smear patch boundaries.

### 4.3 The MainWindow render pipeline

```
_on_subtype_changed  → _render_current(reset_camera=True)
                                ↓
              parameters_panel.values()  → kwargs
                                ↓
              surface.generate(**kwargs)  → self._raw_mesh
                                ↓
              _apply_domain_and_render(reset_camera)
                                ↓
              view_panel.clip_to_domain(self._raw_mesh)  → (clipped, overlay)
                                ↓
              plotter.add_mesh(clipped) → self._actor
                                ↓
              appearance_panel.apply_to_actor(self._actor)
                                ↓
              plotter.render()
```

Critical: **the raw mesh is cached**. `_on_domain_changed` (sphere/cube clip slider release) calls `_apply_domain_and_render` directly without regenerating the mesh — only the clip is recomputed. This makes the radius slider snappy.

**Status-bar bbox readout — full-extent (status-bar-bbox-2026q2-e1 + -e2, UPL-13).** After every successful render the status bar appends `bbox: Lx × Ly × Lz` to the `{N_verts} verts, {N_faces} faces` line, where `_b = self._raw_mesh.bounds` and `Lx = _b[1] - _b[0]`, `Ly = _b[3] - _b[2]`, `Lz = _b[5] - _b[4]` — the **full extent** (diameter) along each axis. Read from `_raw_mesh` (not the domain-clipped copy) so researchers see the spatial extent of the mathematical surface, not the current viewport slice. The full-extent format is **exact for all 14 generators** in the live registry — including the 3 Hanson parametric generators (calabi_yau_quintic, calabi_yau_cubic, calabi_yau_asymmetric) whose theta sweeps `[0, π/2]` produce asymmetric bounds; `_b[1]-_b[0]` reports the actual diameter regardless of centering. This is the e2 format; the e1 format used `±max` half-extents (`bbox ±a × ±b × ±c`) which was exact for the 11 implicit-surface generators (symmetric `np.linspace(-bounds, bounds, n)` sampling) but an honest over-approximation for Hanson — the e2 full-extent format eliminates that asymmetry by construction. The label `bbox:` is preserved across both milestones because peer tools all qualify the measurement type explicitly: MeshLab `dim_x()` is documented as "the X size of the Bounding Box"; ParaView's Information panel uses `Bounds` / `X Range:`; Blender uses `Dimensions:`. A bare "size:" label would be ambiguous for algebraic surfaces since "size" could legitimately mean surface area, volume, or true geometric diameter — all distinct from the AABB extent reported here. Precision is `.3f` (3 decimal places) — `.2f` rounded adjacent surfaces with extents 0.53 and 0.54 to the same display, a false-equality risk in a research tool. **Warning path:** on the conifold-warning render path (Dwork ψ ≈ 1), the bbox suffix is hoisted to immediately follow the `⚠ {warning}` prefix and the verbose `{label} verts, faces` content moves to the trailing position, because the combined warning + base_msg can exceed `QStatusBar`'s ~120-char clip width; this preserves the bbox readout on the one render path where spatial extent is most informative. AI-10 safe — the read is inside the success branch of `_render_current` only; the `except ValueError` / `except Exception` paths set `_raw_mesh = None` and return before reaching the format line (AI-14). Format-contract guard: `tests/test_status_bar_bbox.py` (covers Fermat quartic, Kummer surface, **both** Hanson quintic and Hanson asymmetric — the latter has visibly different extents along all three axes (x ≠ y ≠ z) at defaults, making it the strongest regression canary — each with `math.isfinite` guard on **all 6** bounds indices since full-extent subtracts `b[0]`/`b[2]`/`b[4]`, plus the ValueError path).

### 4.3a AppearancePanel public API

`AppearancePanel` exposes two outbound entry points:

- `apply_to_actor(actor)` — invoked at the end of every render path (see §4.3 above). Sets `actor.prop.color`, `style`, `show_edges`, `opacity`, `interpolation` from stored panel state. Also unconditionally calls `apply_background()` to push the chosen viewport background. Safe to call with `actor=None` (background-only path; used on first launch before any mesh).
- `set_default_color(hex_str)` — invoked from `_on_variety_changed` and `_on_subtype_changed` on every variety/subtype switch (variety-palette-2026q2-e1 / UPL-2). Seeds `_surface_color` from `styles.VARIETY_DEFAULT_COLOR[variety]` and refreshes the swatch chip in the Appearance dock. **Does NOT trigger a render** — the caller flows naturally into `_render_current` → `apply_to_actor` which reads the updated color. AI-9 safe (no `processEvents`). The user's subsequent override via the "Surface…" swatch wins for the rest of the session, but switching surfaces re-seeds from the family default (V0 scope; sticky overrides are UPL-25's home).
- `hq_smoothing` property + `set_hq_smoothing_eligible(eligible: bool)` + `hq_smoothing_changed = Signal(bool)` (enriques-hq-smoothing-2026q3-e1) — the opt-in second-Taubin-pass toggle.  Pattern-A storage on the panel; `MainWindow._on_subtype_changed` calls `set_hq_smoothing_eligible(True)` ONLY when the active variety is "Enriques surface" AND the active subtype is Fig. 1 or Fig. 2 (the two double-curve subtypes per §8.13).  Disabled state at launch + on every variety switch.  **Critical architecture distinction vs Wireframe / Show-edges:** those toggles change actor *display properties* (`actor.prop.style`, `actor.prop.show_edges`) and call `_get_plotter().render()` directly in their slot handlers — the apply_to_actor + render fast path.  HQ smoothing changes the **mesh** (the second Taubin pass moves every vertex by ~0.0015 units mean displacement at default params), so its slot handler emits `hq_smoothing_changed = Signal(bool)` instead, and `MainWindow._on_hq_smoothing_changed` calls `_invalidate_clipped_mesh()` + `_render_current(reset_camera=False)` — the full regenerate path.  Calling `render()` directly would re-render the *stale* mesh and silently produce a visual no-op.  This is the only Render Mode-group toggle that regenerates rather than re-renders; the distinction is load-bearing.  See §8.16 for the spike timing log + per-subtype scope rationale.

### 4.3b Theme system (dark-mode-2026q2-e1, UPL-1)

The app ships two palettes — `PALETTE_LIGHT` and `PALETTE_DARK` in [styles.py](styles.py) — with key-identical entries.  Both render through a single `_render_stylesheet(palette: dict) -> str` template function to produce `APP_STYLESHEET` (light) and `APP_STYLESHEET_DARK` (dark) as module-level constants at import time.  Future QSS changes land in one place; both themes automatically pick them up.  Per-variety surface colors live in two parallel dicts (`VARIETY_DEFAULT_COLOR` light, `VARIETY_DEFAULT_COLOR_DARK` dark — currently identical values because all four clear 3:1 on both panel backgrounds) with a `get_variety_default_colors(theme)` accessor so `AppearancePanel` stays decoupled from theme state.

**Dark is the launch default.**  `main()` calls `app.setStyleSheet(APP_STYLESHEET_DARK)` because the VTK viewport is always `#2f2f2f` — dark chrome is the coherent baseline, not the optional variant.  A Theme menu in the main-window menu bar exposes Light / Dark / Follow-system as mutually-exclusive `QAction`s; `_on_theme_changed(name)` swaps the `QApplication` stylesheet synchronously (AI-9 safe — no `processEvents` involved) and re-seeds the active variety's color from the theme-aware dict.  "Follow system" connects `QGuiApplication.styleHints().colorSchemeChanged` (Qt 6.5+ native — no `darkdetect` dep needed) and listens for live OS theme changes; switching to an explicit Light or Dark choice disconnects the signal so the override sticks.

**V0 scope, intentionally narrow:**
- No `QSettings` persistence — every launch returns to dark.  Persisting the user's theme + dock layout is UPL-25's territory.
- "Follow system" on macOS uses Qt's `colorScheme()` enum; high-contrast or other non-Light/Dark values map to Dark as a safe fallback.
- The named constants (`COLOR_MUTED`, `BG_VIEWPORT`, etc.) remain `PALETTE_LIGHT` aliases for backward-compat — the theme swap goes through `_render_stylesheet`, not through these constants.

**Theme-aware label styling — use QSS role properties, NOT `setStyleSheet(MUTED_TEXT_STYLE)`:**

Panel files must NEVER do `label.setStyleSheet(MUTED_TEXT_STYLE | VALUE_MONO_STYLE | RANGE_LABEL_STYLE)` — those constants hardcode `PALETTE_LIGHT` colors and OVERRIDE the dark QSS cascade (widget-level styles win over `QApplication`-level rules in Qt's style cascade).  Use the canonical Qt theme-aware pattern instead:

```python
label.setProperty("role", "muted")        # was: setStyleSheet(MUTED_TEXT_STYLE)
label.setProperty("role", "value-mono")   # was: setStyleSheet(VALUE_MONO_STYLE)
label.setProperty("role", "range-label")  # was: setStyleSheet(RANGE_LABEL_STYLE)
button.setProperty("role", "display-toggle")  # checkable QPushButton — display-toggles-checkable-button-2026q3-e1
button.setProperty("role", "colors-button")   # left-aligned action button — appearance-panel-layout-pass-2026q3-e2
```

The QSS role selectors in `_render_stylesheet` handle color + font for both themes via theme-aware cascade.  This was the H1 finding in this milestone's rectification pass — without it, dark-mode numeric readouts dropped to 1.21:1 contrast.  The legacy `MUTED_TEXT_STYLE` / `VALUE_MONO_STYLE` / `RANGE_LABEL_STYLE` constants remain in `styles.py` as backward-compat exports but are not consumed in-repo after `dark-mode-2026q2-e1`'s rectification commit.  The `test_no_inline_color_styles_in_panel_files` test in `tests/test_styles_palette.py` guards against re-introduction.  `test_dark_stylesheet_includes_role_selectors` enforces that every role selector in this list emits a rule in BOTH stylesheets (light + dark).

**macOS Aqua trigger note.** `QPushButton` role rules MUST include at least one explicit `background:` property (commonly `background: transparent`) to force QSS paint mode on macOS Aqua — Aqua's native button renderer ignores `text-align` regardless of box-model properties because it draws labels at a hardcoded position inside a pre-composited native bead.  Padding + border-radius alone are sufficient on Fusion but NOT Aqua.  Both `display-toggle` and `colors-button` rules set `background: transparent` for this reason.

WCAG verification is per-token, per-theme.  `tests/test_styles_palette.py` carries a dark twin for every text-contrast assertion and a parallel non-text contrast suite for the dark panel borders, focus ring, and reset button.  The MF1 swatch-chip finding deferred from variety-palette-2026q2-e1 is closed by the dark default: all four variety colors clear 3:1 on `BG_PANEL_DARK = #252526` (measured 5.83-7.20:1).

### 4.4 Re-entrancy guard

**realtime-variety-render-e4 (CAND-4) rewrote this.** `surface.generate()` now runs on a `QThreadPool` worker (`render_worker.py`), so `_render_current` is *submit-only* and returns immediately. There is **no `QApplication.processEvents()` call anymore** — the old workaround (and its re-entrancy hazard, §8.5) is gone, because the event loop is naturally free while the worker computes off-thread.

The async render path:
1. `_render_current(reset_camera=...)` — if `self._computing` (a worker is in flight), records `_pending_render` + `_pending_reset_camera` and returns (the e1-s2 queue-latest guard, unchanged). Otherwise it sets `_computing = True`, increments the monotonic `_generation` id, captures `_inflight_surface` / `_inflight_params` / `_inflight_reset_camera`, pushes the wait cursor, builds a `MeshWorker`, holds it in `_active_worker`, and `QThreadPool.start()`s it.
2. `MeshWorker.run()` (worker thread) runs `surface.generate()` inside the `warnings.catch_warnings` + `perf_counter` bracket, packages a `MeshResult`, retains `self._result = mesh` (VTK #18782), and emits `finished`.
3. `_on_mesh_ready(result)` (`@Slot`, **`Qt.QueuedConnection` → GUI thread**) retains the mesh as its first statement, discards the result if `is_stale_result(result.generation, self._generation)`, then does the error/warning branching, `_apply_domain_and_render`, status-bar build, and — in its `finally` — restores the cursor, clears `_computing` / `_active_worker`, and fires the one `QTimer.singleShot(0, ...)` catch-up if `_pending_render` was set.

Re-entrancy analysis (AI-9): `_on_mesh_ready` runs on the GUI thread via `QueuedConnection`, so it is serialized with every other GUI event — it cannot re-enter itself. The catch-up `singleShot(0)` runs on a later event-loop turn with `_computing` already `False`, so it enters `_render_current` cleanly. With the `_computing` single-flight guard at most one worker is in flight and at most one catch-up is queued; the `_generation` counter is *defensive* idempotency insurance on top. **All VTK GL calls (`add_mesh` / `render` / `reset_camera`) stay on the GUI thread — the worker only touches `surface.generate()` data construction.** If you add a code path that dispatches a worker outside `_render_current`, or lift the `_computing` guard, re-do this analysis.

### 4.5 Domain clipping (sphere / cube)

`view_panel.py` exposes `clip_to_domain(mesh) -> (clipped_mesh, overlay_mesh_or_None)`. Both modes use the same scalar-clipping approach: tag every vertex with a "domain function" (Euclidean distance for sphere, Chebyshev `max(|x|,|y|,|z|)` for cube), then `clip_scalar(invert=True)` keeps the interior. **Don't use `clip_box`** — its `invert` semantics on PolyData are unreliable in current PyVista (see commit `b68456f`).

### 4.6 Warning surfacing

`render_worker.MeshWorker` wraps `surface.generate()` in `warnings.catch_warnings(record=True)` **on the worker thread** (`catch_warnings` is not thread-shared — a main-thread context manager cannot see a worker-thread warning). Any `RuntimeWarning` text is captured into `MeshResult.warning_text`, shipped back across the `QueuedConnection` signal, and `_on_mesh_ready` prefixes it with `⚠` in the status bar. Currently used by `calabi_yau_dwork` to flag `|ψ−1| < 0.01` (the conifold point, where marching cubes silently misses the singularity).

---

## 5. Mathematical conventions per variety

These are non-obvious and were established by Opus research agents cross-referencing primary sources.

### 5.1 K3 surfaces

**Fermat quartic.** The genuine projective Fermat K3 `x⁴+y⁴+z⁴+w⁴=0` has empty real locus. We plot its **real shadow** `x⁴+y⁴+z⁴ = c` (the dehomogenization w=1 with sign flip), generalized to a 3-parameter family:

  `x⁴+y⁴+z⁴ + α(x²y²+y²z²+z²x²) + β·xyz·(x+y+z) + γ·(x²+y²+z²) = c`

- α ∈ [-1, 0] — sharpens cube into octahedral star. **α < -1 makes the surface non-compact** (the "K3" claim fails). Never let the slider go below -1.
- β ∈ [-3, 3] — tetrahedral perturbation. **|β| > 3 opens non-compact channels.**
- γ ∈ [-15, 0] — quadratic carve, extends six axial arms. Restricted to non-positive values so the surface never tends toward a sphere (positive γ inflates).
- c ∈ [0.1, 30] — RHS scale.
- Bounds are adaptive: `bounds = max(2.5, 1.15·sqrt((-γ + sqrt(γ² + 4c))/2) + 0.3)`.

**Kummer surface** (Hudson's tetrahedral form):

  `(x²+y²+z²−μ²)² − λ(μ)·p·q·r·s = 0`

with the four tetrahedral planes and `λ(μ) = (3μ²−1)/(3−μ²)`.

- μ² ∈ [0.40, 2.95]. **μ² ≤ 1/3 → λ ≤ 0 → no real zero set** (raises ValueError).
- **μ² = 3 is a pole** of λ (raises ValueError).
- Bounds adaptive: `max(2.6, 2.6 + 2(μ²−1))` clamped to ≤ 6.0.

### 5.2 Enriques surfaces

A genuine Enriques surface is the quotient of a K3 by a fixed-point-free involution. Its projective canonical embeddings have empty real locus. We plot **degree-6 surfaces in P^3 birational to Enriques surfaces** — exactly Enriques' 1896 construction.

| Figure | Equation | Reference |
|---|---|---|
| 1: Canonical sextic | `x²y² + x²z² + y²z² + x²y²z² + c·xyz·(1+x²+y²+z²) = 0` | Wikipedia, MathWorld, Cossec–Dolgachev |
| 2: Diagonal λ-family | Same but with independent coefficients λ₀, λ₁=1, λ₂=1, λ₃ on the four "missing-one-variable" sextic monomials | Dolgachev Kyoto13 lecture notes |
| 3: Cayley quartic symmetroid | `(x+y+z+xy+xz+yz)² = k·xyz` (degree 4, NOT 6) | Cossec; arXiv:1906.01445 |
| 4: Barth-style icosahedral sextic | `4(φ²x²−y²)(φ²y²−z²)(φ²z²−x²) − τ(1+2φ)(x²+y²+z²−1)² = 0` (Endrass-normalized, NOT Barth's classical surface) | Barth 1996; Endrass 1997 |

**Pitfall fixed mid-build.** The Figure 4 docstring originally claimed `τ=1` is Barth's classical 65-nodal sextic. The adversarial reviewer caught that this is incorrect — Barth uses `(x²+y²+z²)²` not `(r²−1)²`. Docstring was rewritten to honestly describe this as the Endrass-normalized variant. **Don't repeat that misattribution if you add more figures.**

### 5.3 Calabi–Yau 3-folds

A CY3 is **6-real-dimensional**. It cannot live in R³. The visualization tradition collapses to **Hanson 1994** parametric cross-sections of the Fermat quintic, plus parametric variants. There is no canonical implicit-surface representation.

**Hanson construction** (Notices of the AMS 41(9), 1994, Eqs. 5–7):

  `z₁(θ, ξ, k₁) = exp(2πi·k₁/n₁) · cosh(ξ + iθ)^(2/n₁)`
  `z₂(θ, ξ, k₂) = exp(2πi·k₂/n₂) · (-i·sinh(ξ + iθ))^(2/n₂)`
  Project to R³: `(Re z₁, Re z₂, cos α · Im z₁ + sin α · Im z₂)`

with θ ∈ [0, π/2], ξ ∈ [-ξ_max, ξ_max], and (k₁,k₂) ∈ {0..n₁−1}×{0..n₂−1} indexing n₁·n₂ patches.

| Figure | (n₁, n₂) | Patches | Notes |
|---|---|---|---|
| 1: Hanson quintic | (5, 5) | 25 | The iconic CY3 image (Elegant Universe cover) |
| 2: Hanson cubic torus | (3, 3) | 9 | Genus 1 (torus) |
| 3: Hanson asymmetric | (5, 3) | 15 | Hanson's own (n₁≠n₂) extension |

**Important Unicode correctness.** The docstring uses `n₂` (U+2082, SUBSCRIPT TWO) for the second exponent — NOT `n²` (U+00B2, SUPERSCRIPT TWO, which reads as n-squared). The adversarial reviewer caught a `(n, n²) = (5, 5)` line that implied 5²=5. If you copy or extend these docstrings, use `n₁`/`n₂` subscripts only.

**Hanson grid parity.** The `grid` parameter must be ODD for the surface to pass through fixed points along ξ=0 (Hanson 1994 p. 6). The function silently coerces even → odd via `if grid % 2 == 0: grid += 1`. ParamSpec `step=2.0, minimum=21.0` keeps slider-reachable values odd.

**Hanson normals — be careful.** The 25 patches glued by `_concat_polydata` are 25 **disconnected components** — `consistent_normals=True` cannot orient them coherently and produces per-patch lighting flips. The fix in commit `f58ee05` was to use `cell_normals=True, consistent_normals=False` so per-triangle winding drives shading. **Don't change this back.**

**Figure 4 — Dwork pencil real slice** (the only implicit CY3 figure):

  `x⁵ + y⁵ + z⁵ + 2 = 5·ψ·xyz`

(Dehomogenizing `z₁⁵+...+z₅⁵ - 5ψz₁z₂z₃z₄z₅ = 0` with z₄=z₅=1.)

- ψ ∈ [-2.5, 2.5]. **ψ = 1 is the (real) conifold** — surface acquires a node at (1,1,1). All five 5th roots of unity in ℂ are conifold points; `|ψ|=1` is NOT all conifolds (e.g., ψ=i is smooth). The docstring is precise about this.
- At ψ ≈ 1, marching cubes silently misses the singular point. The generator emits a `RuntimeWarning` that MainWindow's `catch_warnings` surfaces in the status bar.

---

## 6. The 5-phase pipeline pattern (USED FOR EACH NEW VARIETY)

The user has used this pattern **three times** (K3 — informally; Enriques — formally; Calabi–Yau — formally) and it produces strong results. **Use it for any future varieties.**

```
Phase 1: Two parallel Opus research agents (run with run_in_background=True)
   - Agent A: math research — equations, parameter conventions, sources, cross-verified references
   - Agent B: visual / code archeology — find existing implementations, image references, library options
   
Phase 2: Synthesize 4 figures, implement them, verify with off-screen renders
   - Use pv.OFF_SCREEN = True and pv.Plotter(off_screen=True).show(screenshot=...) — Qt+VTK GUI segfaults under offscreen on macOS
   - Render each figure to /tmp/<name>.png and Read the image to check it
   - Commit
   
Phase 3: Adversarial Sonnet (run_in_background=True)
   - Brief it as a hostile reviewer, scope it to the NEW work only
   - Six categories: libraries, engineering, gaps, docs, bugs, testing
   - Output format: numbered findings with severity / file:line / problem / impact / fix
   - Aim for ~10 findings; quality over quantity
   - Read-only — explicitly forbid commits
   
Phase 4: Remediation Sonnet (run_in_background=True)
   - Hand it the previous review verbatim, plus instructions on which findings to fix
   - Group into MUST FIX (high) / SHOULD FIX (medium) / SKIP (cosmetic)
   - Require new tests for any new behavior
   - Single commit at end with each finding addressed by number
   
Phase 5: UI/UX Sonnet (run_in_background=True)
   - Two-phase brief: critique (5–10 findings) THEN implement 4–7 of them
   - Focus on first-launch UX, status feedback, parameter labels, tooltips
   - Don't relitigate prior UX passes — scope to the NEW variety
   - All existing tests must still pass before committing
```

**Wakeup pattern.** After dispatching each agent, schedule a `ScheduleWakeup` with delay 240–420 s to check on it. Don't poll — the agent runtime sends a completion notification. If you get the wakeup before the notification, just respond "still running" and wait for the formal notification.

**Stale-wakeup pattern.** Sometimes the wakeup fires after the agent completes and after I've already moved on. Recognize this and just acknowledge briefly without redoing work.

---

## 7. Sample prompts that worked well

### 7.1 Math research agent (Opus, parallel A)

> I'm building a Python desktop app that visualizes K3 surfaces. The first two surfaces I need to render are the **Kummer surface** and the **Fermat quartic**. I need you to do deep research — including searching the web for example code, MathWorld/Wikipedia/arXiv references, and existing Python/Mathematica/SageMath examples — and return a concrete report I can hand to a developer.
>
> For EACH of the two surfaces, provide: (1) defining equations in real-3D, (2) recommended numerical approach (marching cubes), (3) grid bounds + resolution + numerical pitfalls, (4) a working code snippet using only numpy and scikit-image, (5) cite your sources — link to web pages, papers, or repositories. The math must be right — double-check against multiple sources before committing to them.

### 7.2 Visual / code research agent (Opus, parallel B)

> I am extending a Python desktop algebraic-surface visualizer to plot Calabi–Yau 3-folds. A sister agent is doing pure math research; your job is the complementary practical / visual / code-archeology angle.
>
> Search the web extensively for: (1) Hanson's original CY3 visualization, (2) major image galleries with Calabi-Yau images, (3) concrete code in any language, (4) GitHub repositories, (5) Python libraries explicitly supporting CY3.
>
> Be honest about what's well-established vs. what's a single-paper one-off.

### 7.3 Adversarial reviewer (Sonnet)

> You are an adversarial code reviewer. Your goal is to find as many real, substantive defects as possible. Don't be polite — be specific, technical, and harsh. But every claim you make must be grounded in a real file/line, not invented.
>
> Cover six categories: libraries, engineering, gaps, docs, bugs, testing. For each finding give: file/line, problem, impact, the smallest concrete fix.
>
> Be ruthless. The goal is to give the remediation agent a tightly-scoped punch list.

### 7.4 Remediation engineer (Sonnet)

> You are the remediation engineer. An adversarial reviewer just produced a punch list of 11 findings. Work through them and harden the codebase.
>
> [Findings grouped into MUST FIX / SHOULD FIX / SKIP, each with concrete fix instructions]
>
> All existing tests must pass. Single commit at the end with each finding addressed by number.

### 7.5 UI/UX expert (Sonnet)

> You are a senior UI/UX and frontend-design engineer auditing — and then fixing — a desktop scientific-visualization app.
>
> Phase 1: Walk the codebase and produce a structured Markdown critique covering: information architecture, typography, affordances, feedback, layout, onboarding, accessibility, polish. Aim for 12–20 findings.
>
> Phase 2: After critiquing, **make the actual changes**. Pick the most impactful 6–10 findings.

---

## 8. Bugs caught and fixed (worth knowing)

### 8.1 Reset Camera button did nothing (commit 1)

`view_panel.py:_on_reset_camera` originally called `self._plotter.reset_camera()` without a follow-up `self._plotter.render()`. VTK queues the camera change but doesn't redraw. Same bug existed for view presets and "Show axes" toggle. Fix: every camera state change must be followed by `self._plotter.render()`. The `_make_view_callback` factory now appends `render()` automatically.

### 8.2 PyVista `clip_box` invert semantics are reversed/unreliable

When implementing the cube domain clip, `mesh.clip_box(bounds, invert=False)` returned 0 vertices and `invert=True` returned the full mesh (unchanged) — both wrong. **Workaround in `view_panel.py:clip_to_domain`**: use the same scalar-clipping approach as the sphere clip, with a Chebyshev `max(|x|, |y|, |z|)` distance scalar. Don't use `clip_box` on PolyData.

### 8.3 PyVista doesn't accept short hex `#888`

PyVista's color parser requires either named colors, full 6-digit hex `#888888`, or RGB tuples. **Always use 6-digit hex.**

### 8.4 PyVista 0.46+ deprecation: `clip_scalar` requires `scalars=` keyword

```python
# WRONG (silently warns):  mesh.clip_scalar("_dist", value=r, invert=True)
# RIGHT:                    mesh.clip_scalar(scalars="_dist", value=r, invert=True)
```

### 8.5 Re-entrancy from QApplication.processEvents

**Resolved by realtime-variety-render-e4 (CAND-4) — kept here as institutional memory.** The original synchronous `_render_current` called `QApplication.processEvents()` to keep the status bar repainting during the ~0.5 s blocking generate; that `processEvents` drained the Qt event queue and could re-enter `_render_current` via slider-release events, leading to dangling actors and stale `_raw_mesh`. It was guarded by the `self._computing` bool. e4 moved `surface.generate()` onto a `QThreadPool` worker — the GUI thread is now free during the compute, so the `processEvents` call was **removed entirely**. The `_computing` guard survives (now spanning the async worker round-trip — see §4.4). There is no `processEvents` call anywhere in the render path today; **do not reintroduce one** — if you need the GUI responsive during a long compute, dispatch a worker, do not pump the event queue.

### 8.6 marching_cubes raises cryptically on all-positive fields

A field with no zero crossing produces no isosurface. We pre-check `field.min() > level or field.max() < level` and raise our own `ValueError("No real zero set in the sampling box for these parameters. ...")` with the actual field range. VTK Flying Edges (unlike the old `skimage.measure.marching_cubes`, which raised `ValueError: Surface level must be within volume data range`) returns a **silent 0-point mesh** instead of erroring — including for a degenerate uniform field that slips past the strict-inequality pre-check — so `_marching_cubes_to_polydata` also raises on `mesh.n_points == 0` after contouring. The MainWindow `except ValueError` catches this and shows it in the status bar; **and clears `self._raw_mesh = None`** so subsequent domain clips don't apply to a stale mesh.

### 8.7 Hanson disconnected-patch lighting

`compute_normals(consistent_normals=True)` on a mesh with N disconnected components cannot consistently orient them. Each Hanson cross-section has 9–25 disjoint patches. Original code looked partially dark / lit weirdly. Fix: `cell_normals=True, consistent_normals=False, auto_orient_normals=False` — per-triangle winding drives shading correctly under default lighting.

### 8.8 Conifold singularity silently missed

At ψ=1 in the Dwork pencil, the surface has a node at (1,1,1). With grid spacing ~0.016, no sample point lands on (1,1,1) and the field is strictly positive in a tiny neighborhood. Marching cubes returns a smooth complement. Fix: emit `RuntimeWarning` when `|ψ−1| < 0.01`; MainWindow surfaces it in the status bar.

### 8.9 Qt enum and QSizePolicy deprecation

PySide6 prefers fully-qualified enum forms:
- `Qt.AlignLeft` → `Qt.AlignmentFlag.AlignLeft`
- `QSizePolicy.Expanding` → `QSizePolicy.Policy.Expanding`

The shorthand still works via backward-compat aliases but emits warnings. Use the qualified form everywhere.

### 8.10 Float slider → int generator parameter

`ParamSpec` is all-float (minimum/maximum/default/step). The Hanson `grid` param expects an int count of samples, so the function does `grid = int(round(grid))` and `if grid % 2 == 0: grid += 1`. **If you add an int-typed generator parameter, coerce inside the function.** Don't make ParamSpec int/float-bimodal.

### 8.11 `QDockWidget` has no `takeWidget()` — use `setParent(None)` to detach

PySide6's `QDockWidget.setWidget(panel)` transfers C++ ownership of `panel` to the dock; when the dock is garbage-collected, Qt deletes `panel`'s C++ object. The obvious analogue to `QMainWindow.takeCentralWidget()` does NOT exist on `QDockWidget` (verified: PySide6 6.6+ `QDockWidget` exposes only `setWidget()` and `widget()`). If you need to reuse the same panel across multiple dock containers (the panel-chrome capture script does this for the DEFAULT + HIRES grabs of the same panel), call `panel.setParent(None)` in a `finally:` block before the dock goes out of scope. This re-parents the panel to None, restoring Python's reference as the keep-alive — without it, the next grab crashes with `libshiboken: Internal C++ object (AppearancePanel) already deleted`. The capture script's `_grab_in_dock` helper at [`.claude/scripts/frontend-uplift/render-panel-chrome.py`](.claude/scripts/frontend-uplift/render-panel-chrome.py) documents this in-line.

### 8.12 `qtawesome.icon()` silently returns an empty QIcon without a live QApplication

qtawesome's `qta.icon()` checks `if QApplication.instance() is not None` and falls back to an empty `QIcon` + `UserWarning` when no app is running.  Calling it from a panel's `_build_ui()` constructor — which runs during `MainWindow.__init__` before the QApplication has fully come up in some test contexts — produces invisible icons with no exception.  Fix: each icon-bearing panel exposes a public `refresh_icons(theme)` method (see [`view_panel.py:refresh_icons`](view_panel.py), [`parameters_panel.py:refresh_icons`](parameters_panel.py), and [`appearance_panel.py:refresh_icons`](appearance_panel.py) — the third panel added by qtawesome-icons-2026q2-e2 for the Wireframe + Show-edges toggles), and `MainWindow.__init__` calls them AFTER the panels are constructed — same call is repeated in `_on_theme_changed` and `_apply_system_theme` so theme swaps re-render with the new color.  The capture script `render-panel-chrome.py` mirrors this discipline (calls `refresh_icons` after each panel construction — verify the appearance_panel call lives at lines ~302 and ~331; missing it produces panel-chrome PNGs that lie about the live app's checkbox icons) so panel-chrome PNGs reflect the live app.  See [`icons.py`](icons.py) docstring + [qtawesome issue #144](https://github.com/spyder-ide/qtawesome/issues/144) for the canonical prior art on this footgun.

### 8.13 Back-face culling helps the Enriques family but BREAKS K3 / CY3 — gate per-variety

The Enriques canonical sextic (`x²y² + x²z² + y²z² + x²y²z² + c·xyz·(1+r²) = 0`) has **double-curve singularities** along the six edges of the coordinate tetrahedron: two sheets of the surface approach zero separation along these curves.  Marching cubes produces near-degenerate alternating front/back triangle pairs at those ridges; Phong lighting then renders them as white zipper-seam noise.  Setting `actor.prop.culling = "back"` cleanly hides the inward-facing half, leaving the math-honest singular crease visible (UPL-7 / `enriques-backface-2026q2-e1`).

The same setting **breaks** every other variety family in the catalog:

- **CY3 Hanson quintic** (catastrophic): AI-7 prescribes `cell_normals=True, consistent_normals=False, auto_orient_normals=False` for the 25 disconnected parametric patches.  Per-patch winding is locally consistent but NOT globally outward-pointing.  With `culling="back"`, patches whose normals happen to point away from the camera at the current angle become invisible — the iconic ball-of-spikes shape breaks down as the camera rotates.
- **K3 Kummer surface** (moderate): the 16 A₁ nodes are point-conical (not double-curve).  The inner cone faces are visible through the node hollows; culling hides them.
- **K3 Fermat quartic** (no effect): closed convex topology with all normals outward; culling is safe-but-pointless.

The fix is therefore **variety-level gated**, not universal.  `AppearancePanel.set_culling(value)` is the storage point; `MainWindow._on_variety_changed` sets it to `"back"` only when the active variety is `"Enriques surface"`, `None` otherwise (clears any stale Enriques state when switching families).

### 8.14 `FOCUS_RING` failed WCAG 1.4.11 on the light panel — fix is per-theme, not single-shared

The `FOCUS_RING` token shipped originally as `#5b9bd5`, measured at 2.60:1 against `BG_PANEL = #f0f0f0` (light) — **below the WCAG 2.1 §1.4.11 non-text 3:1 floor** for focus indicators.  The same value measured 5.17:1 on `BG_PANEL_DARK = #252526` (PASS), so the failure was light-only.  The `panel-refresh-2026q2-e2` (variety-palette / UPL-1) milestone surfaced the violation in adversary critique M4 but deferred the fix to preserve "every existing rendered color" per that milestone's acceptance signal.

Closed by `focus-ring-contrast-2026q2-e1` with a per-theme split: `PALETTE_LIGHT["FOCUS_RING"] = #3c82c4` (3.56:1 — PASS, narrow margin), `PALETTE_DARK["FOCUS_RING"] = #5b9bd5` (5.17:1 — preserved).  The initial implementation proposed a single shared `#3c82c4` for both themes — clean architecturally but eroded the dark headroom from 5.17 to 3.78 (still PASSING but only 26% above floor instead of 72%); the frontend-ux critic flagged the regression and the rectify pass reverted PALETTE_DARK to the original value.  The "key-identical palettes" pattern from `dark-mode-2026q2-e1` means **same KEYS, values may differ** when contrast demands — same logic as `TEXT_VALUE`, `TEXT_MUTED`, `BORDER_GROUP_BOX`, all of which differ between light and dark.

**Test guards:** `tests/test_styles_palette.py` ships both `test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel` (FOCUS_RING-only assertion against light BG_PANEL) and `test_light_structural_borders_intentionally_below_3_1` (machine-readable negative guard against well-intentioned-but-wrong "harmonization" of the test with the dark twin — the four structural light border tokens measure ~1.1-1.4:1 by design and should not be darkened).

### 8.15 `QCheckBox + setIcon()` creates a triple-prefix affordance — use `QPushButton(checkable=True)` for icon-bearing toggles

`QCheckBox.setIcon()` (inherited from `QAbstractButton`) renders the icon between the platform-drawn check-square indicator and the text label, producing a `[☐][icon][label]` triple prefix.  No peer scientific-viz app uses this pattern: Blender 4.x N-panel viewport-shading section uses checkable `QPushButton` with icon (no check-square indicator); 3D Slicer 5.x modules panel uses checkable `QPushButton` with paired ON/OFF icons; ParaView's Properties panel uses plain text checkboxes (no icon).  The triple prefix creates visual ambiguity — a user is unsure whether to click the check-square or the icon, since both signal interactive affordance.

The fix shipped in `display-toggles-checkable-button-2026q3-e1` (closing F-M2 from `qtawesome-icons-2026q2-e2`): migrate icon-bearing toggles to `QPushButton(checkable=True)` + a QSS `:checked` pseudo-state rule keyed by the `setProperty("role", "display-toggle")` dynamic-property pattern.  The entire button becomes the affordance; the active state is communicated by a 2px `FOCUS_RING`-colored border (the same token already meeting WCAG 1.4.11 3:1 non-text contrast in both themes — 3.56:1 light, 5.17:1 dark) plus an optional `BG_TOGGLE_CHECKED` fill tint for visual reinforcement.

**Rule:** For icon-bearing display toggles, use `QPushButton(checkable=True)` + QSS role-property targeting.  Use plain `QCheckBox` (no icon) only for text-only toggles where the check-square IS the intended affordance.

**Implementation pattern:**
- `btn = QPushButton("Label")`
- `btn.setCheckable(True)` + `btn.setChecked(initial_state)`
- `btn.setProperty("role", "display-toggle")` to pick up the QSS rules
- `btn.toggled.connect(handler)` — identical signal name and signature as QCheckBox (`toggled(bool)`), inherited from `QAbstractButton`
- Icons via `setIcon(...)` / `setIconSize(QSize(16, 16))` — same API as QCheckBox (also `QAbstractButton`); no API change in `icons.py`
- Do NOT call `setFlat(True)` — keep the unchecked-state visual in QSS (`border: transparent; background: transparent`) so the palette controls all chrome

**Checked-state QSS design (WCAG 1.4.11 compliant):** the active-state indicator is a 2px `FOCUS_RING`-colored border.  The fill (`BG_TOGGLE_CHECKED`, a new per-theme token: `#d4e6f5` light, `#1a3048` dark) is decorative reinforcement only — its contrast vs the hover tint is ~1.1:1 by design.  WCAG passes because the BORDER carries the obligation against the panel ground, not the fill against the hover tint.  Text on the checked fill clears 4.5:1 (9.89:1 light, 10.20:1 dark with `TEXT_VALUE`).

**Test guards:** `test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox` (source-text grep — AI-2 compliant; QPushButton construction requires QApplication which AI-2 bans), `test_dark_stylesheet_includes_role_selectors` (asserts both `QPushButton[role="display-toggle"]` and its `:checked` pseudo-state are emitted in both stylesheets), `test_bg_toggle_checked_token_is_six_digit_hex_in_both_palettes`, `test_bg_toggle_checked_value_appears_in_both_stylesheets`.  Canonical example: `appearance_panel.py:_build_toggles_group`.

The four Enriques subtypes do NOT all share double-curve topology — be precise:

- **Fig. 1 (canonical sextic)** + **Fig. 2 (Diagonal λ-family)** — degree-6 surfaces with genuine double-curve singularities along the coordinate-tetrahedron edges.  Culling is **beneficial**: removes the white zipper noise from alternating front/back triangles at the near-degenerate ridge (verified: Fig. 1 96627B → 82864B; Fig. 2 46020B → 41433B in off-screen renders).
- **Fig. 3 (Cayley quartic symmetroid)** — a degree-4 surface with up to 10 ordinary A₁ nodes (ordinary double points, ODPs), NOT double curves.  Culling is a **no-op** here (verified: 40222B → 40222B — pixel-identical).
- **Fig. 4 (Icosahedral sextic)** — sextic with point-conical A₁ nodes; the marching-cubes resolution is high enough that some alternating front/back triangles still appear at the nodes, so culling is empirically **beneficial** (98034B → 91398B).

The variety-level gate is correct anyway because culling is **harmless across all 4 figures** and beneficial on 3 of 4.  Applying it at the variety level (`name == "Enriques surface"`) avoids per-subtype branching while producing the right result for every figure.  **If you add a new Enriques figure, verify its singularity type — culling is safe at the topology types in the catalog today (double curves + ordinary A₁ nodes), but a future figure with different singularities (e.g., cusp loci, non-isolated singularities) deserves a fresh render comparison before you trust the gate.  If you add a new K3 / CY3 / Fano figure, do NOT add a variety-level culling branch — the topology guard is the only reason this works.**

Also note: the Enriques wing-tip truncation visible at the edge of the rendered viewport is a sampling-bounds artifact (surface extends past the marching-cubes grid), not a culling effect.  Culling is orthogonal to bounds-clipping.

The user's `apply_to_actor` path pushes `actor.prop.culling = self._culling or "none"` so Wireframe / Show-edges / Flat-shading toggles in the Appearance dock don't fight the culling state (the cull persists across appearance changes within the same surface session).

### 8.16 Enriques bounds padded by 5% to capture wing tips; second Taubin pass deferred over-budget

The Enriques canonical sextic (Fig. 1) and the three sibling Enriques figures all use symmetric `np.linspace(-bounds, bounds, n)` sampling around the origin.  At the original `bounds` defaults (1.8 / 1.8 / 2.5 / 1.5 for Figs. 1–4), the marching-cubes grid clips the three "wing tips" of the surface where it extends past the sampling box — visible as flat truncated edges at the wing extremes, especially the bottom wing of Fig. 1.

The original `panel-refresh-2026q2` roadmap epic e4 (UPL-18) proposed two related fixes: (a) a second Taubin smoothing pass (`n_iter=40, pass_band=0.05`) on top of the existing single pass, to attenuate the double-curve sawtooth-ridge artifact; (b) a 5% bounds-padding multiplier (`bounds * 1.05`) to capture the missing wing geometry.  The roadmap pre-committed to a spike: ship the second pass only if median generate time stayed under ~500ms per CONTEXT.md §4.4.

Spike result (`enriques-taubin-spike-2026q2-e1` — see `.claude/notes/milestones/enriques-taubin-spike-2026q2-e1/artifacts/timing-log.txt`):
- Single-pass median (production baseline at `enriques_figure_1(c=1.0)`, n=240, N=7 runs): **449.3 ms**
- Double-pass median (proposed: existing pass + second `n_iter=40, pass_band=0.05`): **587.5 ms**
- Second-pass overhead: +138.2 ms (+30.8%)
- Budget headroom: −87.5 ms (17.5% over the 500 ms threshold)

**Decision: Path B (over-budget) — ship bounds-padding only; defer the second Taubin pass.**

The bounds-padding (`bounds * 1.05`) shipped universally across all four Enriques figures:
- `enriques_figure_1`: 1.8 → 1.89
- `enriques_figure_2`: 1.8 → 1.89
- `enriques_figure_3`: 2.5 → 2.625
- `enriques_figure_4`: 1.5 → 1.575

Off-screen render verification (`/tmp/check-enriques-{before,after}*.png`) confirms the wing tips now resolve to clean tapering points instead of truncated flat edges; the double-curve sawtooth artifact along the central crease is unchanged (the deferred second pass would have addressed that).  Mesh extent on Fig. 1 grew from 3.60 × 3.60 × 3.60 to 3.78 × 3.78 × 3.78; vertex count +0.52% (399,507 → 401,592), face count +0.48% — negligible perf impact vs the wing-tip visual win.

AI-14 verification: the 5% pad doesn't degrade marching-cubes resolution.  Voxel spacing at the new defaults: Fig. 1 = 2 × 1.89 / 239 ≈ 0.01582 (was 0.01506 at 1.8); Fig. 3 = 2 × 2.625 / 239 ≈ 0.02197; Fig. 4 = 2 × 1.575 / 219 ≈ 0.01438.  All well above the practical floor (~0.003) below which marching cubes produces unusable meshes.

**Deferral closed by `enriques-hq-smoothing-2026q3-e1`.** The second Taubin pass shipped as an opt-in "HQ smoothing" `QPushButton(checkable=True)` in the Appearance dock's Render Mode group (renamed from "Display" by `appearance-panel-layout-pass-2026q3-e2`) — same checkable-button pattern as Wireframe / Show-edges (CONTEXT.md §8.15) but with a critical wire-up difference: toggling it changes the **mesh**, not just actor properties.  The button is disabled (greyed out) at launch and enabled per-subtype by `MainWindow._on_subtype_changed` ONLY when the active variety is "Enriques surface" AND the active subtype is "Canonical sextic  [Fig. 1]" or "Diagonal λ-family  [Fig. 2]" (the double-curve targets — figs 3+4 have A₁ nodes and gain no targeted benefit per §8.13).  Default OFF preserves the 449 ms baseline; enabling adds ~138 ms per the spike measurement.  Generator API: `enriques_figure_1` and `enriques_figure_2` gain `hq_smoothing: bool = False` kwarg; `_marching_cubes_to_polydata` gains internal `second_smooth_iter: int = 0` plumbing.  Regression guards: `tests/test_enriques_hq_smoothing.py` covers default-False, scope-to-figs-1+2 (figs 3+4 have no kwarg), HQ-on returns valid PolyData, HQ-on actually moves vertices (mean displacement >1e-5 — guards against the toggle silently no-op'ing), and the QPushButton-not-QCheckBox source-grep + `setEnabled(False)`-at-launch guards on the Qt-panel surface.  See §4 for the mesh-vs-actor architecture distinction.

### 8.17 `clean()` after VTK Flying Edges collapses cells → inside-out shading

When `_marching_cubes_to_polydata` was switched from `skimage.measure.marching_cubes` to VTK Flying Edges (`realtime-variety-render-e6` / CAND-1), an interim version kept a `mesh.clean()` pass for vertex-merge hygiene. It regressed shading badly: `clean()` merges the handful of near-coincident points Flying Edges emits, which **collapses incident triangles into zero-area degenerate cells**. `vtkPolyDataNormals`' orientation-consistency walk cannot cross a degenerate cell, so the mesh splits into orientation islands — half the Enriques canonical sextic shaded inside-out (large black patches in off-screen renders). The fix is simply **no `clean()`**: `vtkFlyingEdges3D` is contractually a watertight, shared-vertex, all-triangle extractor with nothing to merge. Guarded by `test_mesh_generators.py::test_*_consistent_winding` (every directed edge traversed at most once). **Do not re-add `clean()` to the Flying Edges path.**

### 8.18 Worker-result slot: the stale-result discard must run inside the `try`

In `realtime-variety-render-e4` (CAND-4) an interim `_on_mesh_ready` placed the `is_stale_result` supersede check (a bare `return`) *above* the `try`/`finally`. Both Phase-3 critics flagged it: a stale result would skip the `finally` that restores the wait cursor, clears `_computing`, and fires the catch-up — leaving the app in a **permanent soft-freeze** (override cursor stuck on, `_computing` pinned `True`, so every later `_render_current` short-circuits into `_pending_render` and no surface ever renders again). The path is *unreachable today* — the `_computing` single-flight guard means a slot invocation is always for the current generation — but it was a latent landmine for any future change that lifts single-flight (the coarse-LOD / per-tick-dispatch direction `render_worker.is_stale_result`'s docstring explicitly anticipates). Fix: the `is_stale_result` discard now lives **inside** the `try`, so the `finally` cleanup runs on every exit including a superseded result. **Any new early `return` in a worker-result slot must sit inside the `try` so the guard-state cleanup is unconditional.**

---

## 9. Things explicitly NOT done (and why)

Logged as adversarial findings in the most recent reviews but skipped. Future maintainers can pick these up.

- **No state persistence.** App doesn't save window layout, last-used surface, slider values, or color choices via `QSettings`. Every launch starts fresh.
- **No 3D mesh export.** Only PNG screenshot is supported. Adding STL/OBJ/PLY export is one line: `mesh.save("file.stl")`.
- **A render-busy spinner icon shown during mesh generation (~0.5s window)** — deferred beyond `qtawesome-icons-2026q2-e2` (UPL-4 v2 scope).  The camera-preset and display-toggle icons closed in v1 (`qtawesome-icons-2026q2-e2`); v0 (`qtawesome-icons-2026q2-e1`) covered Reset Camera / Screenshot / Reset Defaults.  The spinner is deferred because `QMovie.updated` signals can fire during `QApplication.processEvents()` in `_render_current`, touching the AI-9 re-entrancy surface that already required the `self._computing` guard machinery.  A correct implementation requires either (a) a `QTimer.singleShot`-based frame stepper that checks `self._computing` before advancing, or (b) moving mesh generation to a `QThread` — neither fits the XS-effort pattern of v0/v1.  The existing `QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)` at `_render_current` line 381 already provides user-visible busy feedback; a spinner adds visual polish but no functional value at v2 scope.
- **No first-launch auto-render.** App opens to a `— Select —` placeholder and an empty plotter. The UI/UX agent considered auto-selecting the first surface and decided it would feel presumptuous in a research tool.
- **No confirmation dialog on Reset to Defaults.** The action is non-destructive (the surface re-renders with default sliders); a confirm dialog would interrupt flow.
- **No keyboard navigation beyond the three shortcuts** (`Ctrl+R` reset camera, `Ctrl+Shift+S` screenshot, `Ctrl+D` reset defaults). Tab order is whatever PySide6 derives by default.
- **No empty-clip overlay annotation.** When the domain radius is set so small that the surface vanishes, the status bar says "Domain is smaller than the surface — no geometry to display" but the canvas itself shows nothing. A VTK text overlay would be nicer but tightly couples to the render pipeline.
- **No tests for app.py / MainWindow.** The test suite is all pure-NumPy / pure-PyVista / static-math tests. Adding `pytest-qt` would let us test the dropdown wiring and dock layout, but Qt+VTK segfaults under offscreen on macOS prevent end-to-end smoke tests in CI. Manual launch is the only true verification.
- **No automated test for the background-thread worker lifecycle (realtime-variety-render-e4 / CAND-4).** The *pure* pieces of `render_worker.py` — the `is_stale_result` supersede predicate and the `MeshResult` payload — are covered Qt-free by `tests/test_render_worker.py`. The *live* path cannot be: the `QThreadPool` dispatch, the `QueuedConnection` signal delivery, the `_computing` worker-in-flight queue-latest coalescing, the rapid cancel-and-resubmit supersede, and `closeEvent` thread drain all need a running `QApplication` event loop, i.e. `pytest-qt` — an AI-2 BLOCKER. The substitute regression harness is the e3 spike script `.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py` (re-runnable on demand) plus the spike report's §7 **macOS on-device verification checklist** (`.claude/notes/roadmaps/realtime-variety-render/spike-cand4-thread-safety.md`) — a documented pre-ship manual gate that cannot run on the Windows dev machine.

---

## 10. How to verify changes in this environment

```bash
# Static checks
.venv/bin/python -c "import app, surfaces, view_panel, parameters_panel, appearance_panel; print('OK')"

# Test suite
.venv/bin/pytest tests/ -v          # 120 tests, ~4 s

# Render verification (off-screen — Qt+VTK GUI segfaults under offscreen)
.venv/bin/python -c "
import pyvista as pv
pv.OFF_SCREEN = True
from surfaces import VARIETIES
m = VARIETIES['Calabi–Yau 3-fold']['Hanson quintic  [Fig. 1]'].generate()
p = pv.Plotter(off_screen=True, window_size=(440, 380))
p.add_mesh(m, color='#9aa6c8', smooth_shading=True)
p.show(screenshot='/tmp/check.png')
"
# Then Read /tmp/check.png to visually verify

# Real GUI (only on a real desktop)
.venv/bin/python app.py
```

**Do not** try to construct `MainWindow()` with `QT_QPA_PLATFORM=offscreen` — it will segfault during VTK GL context creation. This is a documented limitation, not a bug to fix.

---

## 11. Adding a new variety: checklist

If a future user asks for a fourth variety (Severi varieties, abelian surfaces, Fano threefolds, etc.):

1. **Run the 5-phase pipeline** from §6.
2. **Add tooltip dict entries** in `surfaces.py` (`VARIETY_TOOLTIPS` and `SUBTYPE_TOOLTIPS`). The user expects honest disclaimers if the genuine variety can't live in R³.
3. **Add to `VARIETIES`** with `[Fig. N]` tags in the dropdown keys for consistency.
4. **Cross-verify equations against ≥2 sources.** Wikipedia + MathWorld + arXiv + classical text is the bar.
5. **Render off-screen and visually verify.** A correct equation can still produce a visually disappointing surface; iterate on parameters.
6. **Add tests:** at minimum a smoke test in `tests/test_mesh_generators.py` and parameter-range entries in `tests/test_parameters_panel.py:ALL_PARAM_SPECS`.
7. **Adversarial → remediation → UI/UX**, in that order. Don't skip phases.
8. **Single commit per phase.** Commit messages should list findings addressed by number.

---

## 12. Final state at handoff

- 13 commits on `main`
- 120 tests passing in ~4 s
- Three varieties live: K3 (2 subtypes), Enriques (4 figures), Calabi–Yau (4 figures)
- Three docks: View (left), Parameters (right top), Appearance (right bottom)
- Domain clipping with sphere/cube modes and adjustable radius
- Adaptive bounds, Taubin smoothing, gradient normals throughout
- Tooltips, keyboard shortcuts, busy cursor, status-bar feedback
- Centralized stylesheet with WCAG AA-compliant text contrast
