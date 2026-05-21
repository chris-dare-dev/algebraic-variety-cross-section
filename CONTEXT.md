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
├── app.py              MainWindow — dropdowns, three docks, plotter wiring (~415 LOC)
├── surfaces.py         All mesh generators + Surface/ParamSpec dataclasses + VARIETIES registry (~840 LOC)
├── parameters_panel.py Dynamic slider panel; rebuilds from each Surface's ParamSpec list (~220 LOC)
├── appearance_panel.py Color / wireframe / opacity / shading panel (right dock) (~300 LOC)
├── view_panel.py       View presets, camera, scene aids, domain clip, screenshot (left dock) (~420 LOC)
├── styles.py           Centralized stylesheet constants (palette, typography, dock-header CSS) (~140 LOC)
├── tests/              pytest suite — 120 tests, ~4 s, pure NumPy/PyVista (no Qt fixtures)
│   ├── test_mesh_generators.py     smoke tests for every generator + edge cases
│   ├── test_parameters_panel.py    static slider tick↔value math
│   ├── test_clip_domain.py         ViewPanel.clip_to_domain pure-function tests
│   ├── test_marching_cubes_empty.py raises on empty fields
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
- **scikit-image's `measure.marching_cubes`** for implicit surfaces — proven, fast, returns vertices + faces + analytic gradient normals.
- **Adaptive bounds** for the Fermat quartic family — the box is computed from `c` and `γ` so axial arms always fit. Don't hard-code box sizes for new generators with wide parameter ranges.
- **Taubin smoothing post-marching-cubes** — `mesh.smooth_taubin(n_iter=20, pass_band=0.1)` is volume-preserving; vanilla Laplacian shrinks geometry.
- **Gradient-based normals from marching_cubes** — the analytic normals are far smoother than face-averaged ones near high-curvature regions. We attach them BEFORE Taubin smoothing as a seed, then `compute_normals()` rederives after smoothing.

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
1. Validates the field has a zero-crossing (raises `ValueError("No real zero set...")` if not).
2. Calls `skimage.measure.marching_cubes`, captures gradient normals.
3. `mesh.clean()` to weld duplicate vertices.
4. `mesh.smooth_taubin(n_iter=20, pass_band=0.1)` for volume-preserving smoothing.
5. `mesh.compute_normals(...)` to refresh after smoothing.

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

### 4.4 Re-entrancy guard

`_render_current` calls `QApplication.processEvents()` (to keep the status bar responsive during ~0.5 s mesh generation). This drains the Qt event queue, which can re-enter via slider release → `_on_params_changed` → `_render_current`. Guarded by `self._computing: bool` set at the top of `_render_current` and cleared in a `finally` block. **If you add another `processEvents` call elsewhere, audit re-entrancy.**

### 4.5 Domain clipping (sphere / cube)

`view_panel.py` exposes `clip_to_domain(mesh) -> (clipped_mesh, overlay_mesh_or_None)`. Both modes use the same scalar-clipping approach: tag every vertex with a "domain function" (Euclidean distance for sphere, Chebyshev `max(|x|,|y|,|z|)` for cube), then `clip_scalar(invert=True)` keeps the interior. **Don't use `clip_box`** — its `invert` semantics on PolyData are unreliable in current PyVista (see commit `b68456f`).

### 4.6 Warning surfacing

`MainWindow._render_current` wraps `surface.generate()` in `warnings.catch_warnings(record=True)`. Any `RuntimeWarning` is extracted and prefixed with `⚠` in the status bar. Currently used by `calabi_yau_dwork` to flag `|ψ−1| < 0.01` (the conifold point, where marching cubes silently misses the singularity).

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

See section 4.4. Without a guard, `processEvents` during status-bar update can re-enter `_render_current` via slider-release events, leading to dangling actors and stale `_raw_mesh`.

### 8.6 marching_cubes raises cryptically on all-positive fields

`skimage.measure.marching_cubes` raises `ValueError: Surface level must be within volume data range` if the field has no zero crossing. We pre-check `field.min() > level or field.max() < level` and raise our own `ValueError("No real zero set in the sampling box for these parameters. ...")` with the actual field range. The MainWindow `except ValueError` catches this and shows it in the status bar; **and clears `self._raw_mesh = None`** so subsequent domain clips don't apply to a stale mesh.

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

---

## 9. Things explicitly NOT done (and why)

Logged as adversarial findings in the most recent reviews but skipped. Future maintainers can pick these up.

- **No state persistence.** App doesn't save window layout, last-used surface, slider values, or color choices via `QSettings`. Every launch starts fresh.
- **No 3D mesh export.** Only PNG screenshot is supported. Adding STL/OBJ/PLY export is one line: `mesh.save("file.stl")`.
- **No first-launch auto-render.** App opens to a `— Select —` placeholder and an empty plotter. The UI/UX agent considered auto-selecting the first surface and decided it would feel presumptuous in a research tool.
- **No confirmation dialog on Reset to Defaults.** The action is non-destructive (the surface re-renders with default sliders); a confirm dialog would interrupt flow.
- **No keyboard navigation beyond the three shortcuts** (`Ctrl+R` reset camera, `Ctrl+Shift+S` screenshot, `Ctrl+D` reset defaults). Tab order is whatever PySide6 derives by default.
- **No empty-clip overlay annotation.** When the domain radius is set so small that the surface vanishes, the status bar says "Domain is smaller than the surface — no geometry to display" but the canvas itself shows nothing. A VTK text overlay would be nicer but tightly couples to the render pipeline.
- **No tests for app.py / MainWindow.** The 120 tests are all pure-NumPy / pure-PyVista / static-math tests. Adding `pytest-qt` would let us test the dropdown wiring and dock layout, but Qt+VTK segfaults under offscreen on macOS prevent end-to-end smoke tests in CI. Manual launch is the only true verification.

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
