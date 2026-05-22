# App invariants (AI-1 … AI-15)

Architectural locks specific to the algebraic-variety-cross-section repo. These are rules that, if violated, will either break the app silently (segfault, wrong geometry, no render) or compound debt that's expensive to unwind.

The Challenger sub-agent of `/capability-scout` evaluates every candidate against this list. The Challenger sub-agent of `/frontend-uplift` also references it (especially AI-1, AI-4, AI-5, AI-9, AI-10, AI-11, AI-12 for UI / panel / interaction proposals).

These are derived from `CONTEXT.md` §3 (stack rationale), §4 (architecture conventions), §8 (bugs caught and fixed), and `README.md` "Troubleshooting" / "Extending the app".

---

## AI-1 — PySide6 + PyVista + pyvistaqt (LGPL-friendly stack)

GUI is PySide6 (LGPL, friendlier than PyQt6's GPL for redistribution). The 3D viewport is `pyvistaqt.QtInteractor` — a real VTK render window dropped into `QMainWindow` so rotate / zoom / pan are native trackball-style.

**Implication:** any candidate that proposes switching to PyQt6 (GPL surface change) or to a non-VTK renderer (matplotlib mpl_toolkits, Plotly, k3d, Mayavi) is an AI-1 conflict.  See AI-1's anti-list at the bottom of §3 of CONTEXT.md.

**Compute dependencies are NOT AI-1 conflicts.** AI-1 locks the *rendering* stack, not the numerics. `numba` (BSD-2-Clause, JIT compiler) is a sanctioned in-tree compute dependency as of realtime-variety-render-e5 — it accelerates scalar-field evaluation in `surfaces.py` and is not a renderer. A future candidate proposing a pure-compute library (Numba, Cython, a BLAS-backed routine) is AI-1-clean as long as it does not touch the PySide6 / PyVista / pyvistaqt render path.

## AI-2 — Test suite is Qt-free (pure NumPy / PyVista / scikit-image)

All 120 tests under `tests/` exercise pure NumPy / PyVista / scikit-image code paths.  There is no `pytest-qt`.  Reason: Qt + VTK GL context creation is unstable under `QT_QPA_PLATFORM=offscreen` on macOS and segfaults in CI.

**Implication:** any candidate proposing pytest-qt-style UI tests must address the macOS Qt+VTK offscreen segfault or accept that the new tests can only run on real desktops (which CI typically isn't).

## AI-3 — Render verification is off-screen via `pv.OFF_SCREEN = True`

For headless render verification (CI, the frontend-uplift visual scout, ad-hoc Read-the-PNG checks), the pattern is:

```python
import pyvista as pv
pv.OFF_SCREEN = True
p = pv.Plotter(off_screen=True, window_size=(W, H))
p.add_mesh(mesh, ...)
p.show(screenshot="/tmp/out.png")
```

**NEVER** construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen` — VTK GL context creation segfaults during construction. CONTEXT.md §10 documents this.

**Implication:** the frontend-uplift visual scout MUST use `pv.OFF_SCREEN`, NOT a Qt offscreen platform.  See `.claude/scripts/frontend-uplift/ensure-render-up.sh` for the canonical smoke probe.

**Clarifying scope — what the AI-3 ban does NOT forbid:**

The forbidden combination is *specifically* `MainWindow()` (which hosts `pyvistaqt.QtInteractor`) under `QT_QPA_PLATFORM=offscreen`.  These adjacent patterns are explicitly **allowed**:

1. **Pure-Qt panel widgets under offscreen.**  `AppearancePanel`, `ViewPanel`, and `ParametersPanel` are `QWidget` subclasses that do not instantiate `QtInteractor` — they receive a plotter via constructor argument or callable but never construct VTK context themselves.  Instantiating them under `QT_QPA_PLATFORM=offscreen` and capturing their pixels via `QWidget.grab()` is safe and is the mechanism the frontend-uplift panel-chrome scout uses (`.claude/scripts/frontend-uplift/render-panel-chrome.py`).  See `.claude/references/frontend-uplift/source-registry.md` §4b for the capture set.

2. **Headed `MainWindow()` on a real desktop session.**  Launching `app.py` as a subprocess on the user's actual macOS window server (no `QT_QPA_PLATFORM=offscreen` override) is the normal app-run mode and is unaffected by this invariant.  Future tooling that captures the integrated MainWindow chrome should do so via headed launch + `screencapture` CLI, never via offscreen.

**One-line rule (macOS):** on macOS, offscreen is safe whenever the QApplication tree contains *zero* `QtInteractor` instances; the moment one is added, switch to a real window server.  On Linux with mesa/EGL or osmesa, `QtInteractor` *can* work under offscreen (this is how many Docker-based VTK CI flows run), but that path is outside this repo's tested surface — it is not currently exercised and should not be relied on without a CI matrix proving it.

## AI-4 — Domain clipping uses `clip_scalar`, not `clip_box`

PyVista's `clip_box(invert=...)` semantics on PolyData are reversed/unreliable (returned 0 vertices or the full mesh — both wrong; see CONTEXT.md §8.2 / commit `b68456f`).  Both sphere and cube clip modes in `view_panel.py:clip_to_domain` use the scalar-clipping approach:

- Sphere mode: tag every vertex with Euclidean distance from the origin.
- Cube mode: tag every vertex with Chebyshev `max(|x|, |y|, |z|)`.
- Both: `mesh.clip_scalar(scalars="_dist", value=r, invert=True)` keeps the interior.

**Implication:** any candidate proposing `clip_box` on PolyData is an AI-4 conflict.  Stick with scalar clipping.

## AI-5 — PyVista 0.46+ `clip_scalar` requires `scalars=` keyword

```python
# WRONG (silently warns / breaks in newer versions):
mesh.clip_scalar("_dist", value=r, invert=True)

# RIGHT:
mesh.clip_scalar(scalars="_dist", value=r, invert=True)
```

**Implication:** any code touching domain clipping must use the kwarg form.  The pinned range is `pyvista>=0.46,<0.49`; the kwarg is required across that range.

## AI-6 — Implicit surfaces use marching cubes; parametric surfaces do NOT

Implicit surface generators (Fermat, Kummer, all Enriques figures, Dwork pencil) sample a scalar field on a cubic grid and call `_marching_cubes_to_polydata(field, bounds)` which pre-validates the field has a zero crossing (raises `ValueError("No real zero set...")` if not, and again on a 0-point contour result), contours via VTK Flying Edges (`pv.ImageData(...).contour([level], method="flying_edges")` — replaced `skimage.measure.marching_cubes` in realtime-variety-render-e6), applies **Taubin smoothing** (`smooth_taubin(n_iter=20, pass_band=0.1)` — volume-preserving), then `compute_normals()` to refresh after smoothing. No `clean()` pass — Flying Edges emits a watertight shared-vertex mesh and a `clean()` regresses shading (CONTEXT.md §8.17).

How the *field array* is computed is an implementation detail of each generator and is NOT part of this pipeline contract: realtime-variety-render-e5 swapped the field evaluation in `fermat_quartic` and `enriques_figure_1` from NumPy meshgrid-broadcasting to `@njit(parallel=True)` Numba kernels. The kernel produces the same `(n, n, n)` `float64` array `_marching_cubes_to_polydata` already consumes — the implicit pipeline downstream of the field array is unchanged. A generator may evaluate its field by any means; it must still hand `_marching_cubes_to_polydata` a scalar-field array.

Parametric surfaces (Hanson cross-sections — quintic, cubic torus, asymmetric) skip marching cubes; they build `(X, Y, Z)` 2D arrays and call `_grid_to_polydata(X, Y, Z)` + `_concat_polydata(meshes)` to assemble triangulated patches directly.  Hanson cross-sections **intentionally skip Taubin smoothing** — the parametric grid is already C², and smoothing would smear patch boundaries.

**Implication:** new generators must declare which pipeline they're on and use the right helper.  Don't put Hanson-style parametric meshes through marching cubes; don't run Taubin on parametric grids.

## AI-7 — Hanson normals: `cell_normals=True, consistent_normals=False, auto_orient_normals=False`

Hanson cross-sections are 9–25 disconnected components glued by `_concat_polydata`.  `compute_normals(consistent_normals=True)` cannot coherently orient disconnected components and produces per-patch lighting flips.  Fix in commit `f58ee05`: use `cell_normals=True, consistent_normals=False, auto_orient_normals=False` so per-triangle winding drives shading.

**Implication:** any candidate that proposes "use `auto_orient_normals=True` everywhere for consistency" is an AI-7 regression on Hanson.  CONTEXT.md §5.3 and §8.7 document this in detail.

## AI-8 — `Surface` / `ParamSpec` dataclass contract (frozen registry)

All surfaces enter the GUI through the `VARIETIES` registry in `surfaces.py`:

```python
@dataclass(frozen=True)
class ParamSpec:
    name: str; label: str; minimum: float; maximum: float
    default: float; step: float = 0.01; suffix: str = ""; description: str = ""

@dataclass
class Surface:
    label: str
    generate: Callable[..., pv.PolyData]
    params: list[ParamSpec]

VARIETIES: dict[str, dict[str, Surface]] = { ... }
```

Two parallel tooltip dicts (`VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS`) are also exported from `surfaces.py` and consumed by `app.py`.

**Implication:** every new model must (a) be a `Surface` with a `ParamSpec` list, (b) be registered in `VARIETIES`, (c) carry a tooltip in `SUBTYPE_TOOLTIPS`, (d) have a `[Fig. N]` tag in its dropdown key for consistency.  Don't make `ParamSpec` int/float-bimodal — coerce ints inside the generator (`grid = int(round(grid))`).

## AI-9 — Re-entrancy guard `self._computing` around `processEvents()`

`MainWindow._render_current` calls `QApplication.processEvents()` to keep the status bar responsive during ~0.5 s mesh generation.  `processEvents` drains the Qt event queue, which can re-enter via slider-release → `_on_params_changed` → `_render_current`.  Guarded by `self._computing: bool` set at the top and cleared in a `finally`.

**Implication:** if you add another `processEvents` call elsewhere, audit re-entrancy.  Skipping the `_computing` guard corrupts `_raw_mesh` and dangles actors.

## AI-10 — Raw mesh cached; domain clip doesn't regenerate

`self._raw_mesh` is the un-clipped mesh.  `_on_domain_changed` (sphere/cube clip slider release) calls `_apply_domain_and_render(reset_camera=False)` directly without regenerating the mesh — only the clip is recomputed.  This makes the radius slider snappy.

**Implication:** any candidate that proposes "regenerate the surface every time any UI control changes" is an AI-10 regression.  The cached-raw-mesh + recompute-clip-only pattern is load-bearing.

## AI-11 — Fully-qualified Qt enums

PySide6 prefers fully-qualified enum forms:
- `Qt.AlignLeft` → `Qt.AlignmentFlag.AlignLeft`
- `QSizePolicy.Expanding` → `QSizePolicy.Policy.Expanding`

Backward-compat aliases work but emit deprecation warnings.

**Implication:** new UI code uses the qualified form everywhere.  Reviewing existing code for AI-11 drift is a routine candidate-surface.

## AI-12 — WCAG AA text-contrast on all visible text

`styles.py` is the centralized stylesheet.  `COLOR_MUTED = #5a5a5a` on `#f0f0f0` ≈ 5.4:1 (WCAG AA pass).  The earlier `#888` muted color (3.5:1 contrast — AA fail on small text) was explicitly fixed.

**Implication:** any new text-color proposal must cite the contrast ratio against its background.  Aim for ≥4.5:1 on body text, ≥3:1 on large text per WCAG 2.1 AA.

## AI-13 — 6-digit hex only (PyVista color parser)

PyVista's color parser requires named colors, full 6-digit hex (`#888888`), or RGB tuples.  Short hex (`#888`) is rejected with a cryptic error.

**Implication:** colors flowing into `pv.Plotter.add_mesh(color=...)` or `pv.set_plot_theme(...)` MUST be 6-digit.  Qt stylesheet hex (in `styles.py`) is a separate surface — Qt accepts short hex — but mixing short and long across the two surfaces is a smell.

## AI-14 — Generator function contract: `pv.PolyData` or `ValueError`

Every generator returns a `pv.PolyData`.  Implicit generators raise `ValueError("No real zero set in the sampling box for these parameters. ...")` when the field has no zero crossing (pre-checked before contouring, and re-checked on a 0-point Flying Edges result).  `MainWindow._render_current` catches `ValueError` and:

1. Surfaces the message in the status bar.
2. Sets `self._raw_mesh = None` so subsequent domain clips don't apply to a stale mesh.

`MainWindow._render_current` ALSO wraps `surface.generate()` in `warnings.catch_warnings(record=True)`; any `RuntimeWarning` is extracted and prefixed with ⚠ in the status bar (currently used by `calabi_yau_dwork` to flag `|ψ−1| < 0.01`).

**Implication:** new generators must follow this contract.  Don't `print()` or `raise SystemExit` — use `ValueError` (hard error) or `warnings.warn(..., RuntimeWarning)` (soft signal).

## AI-15 — Math claim honesty: ≥2 sources + honest "real shadow" disclaimers

Every variety's docstring + tooltip cross-references against ≥2 sources (Wikipedia + MathWorld + arXiv + classical text).  Where the genuine variety can't live in ℝ³ (Calabi–Yau 3-fold is 6-real-dimensional; projective Fermat K3 has empty real locus), the docstring is honest about what's being plotted:

- "real shadow" — Fermat K3's dehomogenized real-locus deformation
- "birational to Enriques" — Enriques' 1896 sextic construction, not the true canonical embedding
- "Hanson parametric cross-section" — 2D real shadow of CY3, not the variety itself
- "Endrass-normalized variant" of Barth's icosahedral sextic — NOT Barth's classical surface

A historical mis-attribution (Barth's 1996 surface ≠ his "classical 65-nodal" surface) was caught by the adversarial reviewer and corrected.  CONTEXT.md §5.2 documents this.

**Implication:** any new variety / figure proposal must declare what mathematical object is actually being plotted, not the abstract variety it's named after.  Tooltips must include honest disclaimers when the relationship to the named variety is "birational" / "real slice" / "parametric shadow", not "this is the variety".

**Fidelity disclaimers extend to transient previews.**  `realtime-variety-render-e4b` (CAND-3) added a coarse-preview LOD path for implicit surfaces during slider drag — the displayed mesh during a drag is a *lower-resolution approximation* of the true zero-set, not the production-resolution mesh.  AI-15 honesty requires the user can ALWAYS tell whether they're looking at a real-fidelity render or a preview: the status-bar **Preview badge** (`"Preview — {label} — NNN ms"`) is the load-bearing disclosure, persisting from the first coarse render until the full-resolution result replaces it (CONTEXT.md §8.19).  Suppress precise readouts (vertex / face counts, bbox extent) on the Preview branch — those values would be precise but transient, implying more fidelity than the rendered geometry has.  A new render-mode candidate that lacks a comparable user-visible fidelity disclosure is an AI-15 conflict.

---

## How the Challenger uses these

For every candidate in `/capability-scout`'s synthesis or `/frontend-uplift`'s synthesis, the Challenger walks AI-1 through AI-15 and flags any candidate that:

- proposes Mayavi / matplotlib-3D / Plotly / k3d / raw VTK as the renderer (AI-1)
- requires `pytest-qt` and ignores the macOS Qt+VTK offscreen segfault (AI-2)
- proposes constructing `MainWindow()` under `QT_QPA_PLATFORM=offscreen` (AI-3)
- proposes `clip_box` on PolyData (AI-4)
- forgets `scalars=` on `clip_scalar` (AI-5)
- mixes the implicit and parametric pipelines (AI-6) — e.g., runs Taubin on a Hanson surface
- regresses Hanson normal handling toward `consistent_normals=True` (AI-7)
- bypasses the `VARIETIES` registry or makes `ParamSpec` int/float-bimodal (AI-8)
- adds `processEvents()` without an AI-9 guard
- regenerates the mesh on domain-radius changes (AI-10)
- uses shorthand Qt enum forms (`Qt.AlignLeft`) in new code (AI-11)
- proposes a low-contrast text color (AI-12)
- uses short hex in code flowing into PyVista (AI-13)
- a generator that doesn't follow the `pv.PolyData` / `ValueError` contract (AI-14)
- a new variety / figure without ≥2 sources and honest "real shadow" disclaimer (AI-15)

A clean candidate that touches none of these gets `NONE` from the Challenger.  Padding objections erodes signal — calibrate honestly.
