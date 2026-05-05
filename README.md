# Algebraic Variety Viewer

An interactive desktop application for exploring **algebraic varieties** — K3 surfaces, Enriques surfaces, Calabi–Yau 3-folds, and Fano 3-folds — through real-3D cross-sections, projections, and shadows. The app pairs a live 3D viewport (rotate, zoom, pan with the mouse) with parameter sliders that let you sweep the defining equations and watch the geometry deform in real time.

Built with **PySide6** (Qt) and **PyVista** (VTK), it renders implicit surfaces via marching cubes and parametric surfaces via direct triangulation.

![architecture](https://img.shields.io/badge/python-3.12-blue) ![ui](https://img.shields.io/badge/ui-PySide6-green) ![3d](https://img.shields.io/badge/3d-PyVista%2FVTK-orange) ![tests](https://img.shields.io/badge/tests-120%20passing-brightgreen)

---

## Table of Contents

- [What this app does](#what-this-app-does)
- [Mathematical scope](#mathematical-scope)
- [Quick start](#quick-start)
- [Using the application](#using-the-application)
- [The four panels](#the-four-panels)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Project structure](#project-structure)
- [How rendering works](#how-rendering-works)
- [Running the tests](#running-the-tests)
- [Extending the app](#extending-the-app)
- [Troubleshooting](#troubleshooting)
- [Further reading](#further-reading)

---

## What this app does

Algebraic varieties — the zero loci of polynomial equations — are central objects in modern geometry, mirror symmetry, and string theory. Most of them live in dimensions too high to draw directly: a complex K3 is 4-real-dimensional, a Calabi–Yau 3-fold is **6-real-dimensional**, and a Fano 3-fold likewise sits in 6 real dimensions.

This app lets you **see them anyway**, by plotting their real shadows, slices, and parametric cross-sections in ℝ³.

You can:

- Pick a variety family (K3, Enriques, Calabi–Yau, or Fano) and a specific model from cascading dropdowns.
- **Rotate / zoom / pan** the surface with the mouse via VTK's native trackball.
- **Tune the defining equation in real time** with parameter sliders (each slider has a meaningful range, default, and tooltip).
- **Clip the surface** to a sphere or cube of adjustable radius to expose interior structure.
- **Restyle** — change surface color, opacity, wireframe, lighting / shading, background.
- **Camera presets** — front, top, side, isometric — plus reset, axes overlay, and bounding box.
- **Export** — save high-resolution PNG screenshots.

The app is intentionally **research-oriented**: there are no demo modes, no tutorials, no animations — just the geometry, exposed as cleanly as possible, with the math labels and citations attached to every model.

---

## Mathematical scope

Four families ship out of the box. Each entry is a `Surface` — a generator function plus a list of named parameter sliders.

### K3 surface (2 models)

A K3 surface is a compact complex surface with trivial canonical bundle and `b₁ = 0` — the 2-dimensional analogue of an elliptic curve, central to mirror symmetry.

| Model | Equation | Notes |
|---|---|---|
| **Fermat quartic** | `x⁴+y⁴+z⁴ + α(x²y²+y²z²+z²x²) + β·xyz·(x+y+z) + γ·(x²+y²+z²) = c` | 3-parameter deformation. Adaptive sampling box. |
| **Kummer surface** | `(x²+y²+z²−μ²)² = λ(μ)·p·q·r·s` (Hudson form) | 16-nodal classic. Smooth for `1 < μ² < 3`. |

### Enriques surface (4 figures)

The quotient of a K3 by a fixed-point-free involution; Euler number 12, `2K = 0`.

| Figure | Equation | Reference |
|---|---|---|
| 1 — **Canonical sextic** | `x²y²+x²z²+y²z²+x²y²z² + c·xyz·(1+x²+y²+z²) = 0` | Enriques 1896 / Cossec–Dolgachev |
| 2 — **Diagonal λ-family** | Same with independent weights `(λ₀, λ₂, λ₃)` | Dolgachev Kyoto13 |
| 3 — **Cayley quartic symmetroid** | `(x+y+z+xy+xz+yz)² = k·xyz` | Reye 1882 / Cayley |
| 4 — **Icosahedral sextic** | `4(φ²x²−y²)(φ²y²−z²)(φ²z²−x²) − τ(1+2φ)(x²+y²+z²−1)² = 0` | Endrass-normalized variant of Barth |

### Calabi–Yau 3-fold (4 figures)

A CY3 is **6-real-dimensional** and cannot live in ℝ³. The figures here are 2D real shadows in the **Hanson 1994** parametric tradition (the iconic image on the cover of *The Elegant Universe*), plus one implicit Dwork-pencil slice.

| Figure | Construction | Notes |
|---|---|---|
| 1 — **Hanson quintic** | `z₁⁵ + z₂⁵ = 1` projected to ℝ³, 25 patches | The iconic CY3 cross-section |
| 2 — **Hanson cubic torus** | `z₁³ + z₂³ = 1`, 9 patches | Genus 1 |
| 3 — **Hanson asymmetric (5,3)** | `z₁⁵ + z₂³ = 1`, 15 patches | Hanson's `n₁ ≠ n₂` extension |
| 4 — **Dwork pencil** | `x⁵+y⁵+z⁵+2 = 5ψ·xyz` (implicit) | `ψ = 1` is the real conifold point |

### Fano 3-fold, ρ = 1 (4 figures)

A smooth Fano 3-fold of Picard rank 1 (Iskovskikh's "prime Fano threefold"), also 6-real-dimensional.

| Figure | Construction |
|---|---|
| 1 — **Klein cubic** `V₃` | `V²W+W²X+X²Y+Y²Z+Z²V = 0` sliced by `Z = z₀`. PSL₂(11), order-660 symmetry. |
| 2 — **Segre cubic** | `Σxᵢ = 0 ∧ Σxᵢ³ = 0` in ℙ⁵, sliced by `(x₃,x₄)=(a,b)`. S₆ symmetry, 10 nodes. |
| 3 — **Two-quadrics tube** `V₄` | `f = Q₁² + Q₂² − ε²` — sum-of-squares thickening of the codim-2 intersection. |
| 4 — **Sextic double solid** `V₁` | `z² = x⁶+y⁶+t⁶+1` — branched double cover of ℙ³ along a Fermat sextic. |

Every model has a tooltip in the dropdown explaining the equation, symmetry group, and primary reference.

---

## Quick start

### Prerequisites

- **Python 3.12** (3.10+ should also work; 3.12 is what the project ships with)
- A real desktop session — the app uses VTK's GL context, which **cannot run headless / over SSH without an X server**. (Off-screen rendering works for tests, but not for the GUI.)
- ~600 MB free disk for dependencies (VTK is the bulk).

Tested on **macOS (Apple Silicon)**. Linux and Windows are supported by all underlying libraries but not regularly verified by the maintainer.

### Install

```bash
# 1. Clone
git clone https://github.com/chris-dare-dev/algebraic-variety-cross-section.git
cd algebraic-variety-cross-section

# 2. Create a virtual environment (Python 3.12 recommended)
python3.12 -m venv .venv
source .venv/bin/activate              # macOS / Linux
# .venv\Scripts\activate                # Windows (PowerShell)

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` pins these ranges:

```
PySide6>=6.6,<7
pyvista>=0.46,<0.49
pyvistaqt>=0.11.4,<0.12
numpy>=1.26,<3
scikit-image>=0.22,<0.27
```

### Run

```bash
python app.py
```

A window titled **"Algebraic Variety Viewer"** should open at 1200×800. The status bar prompts: *"Choose a variety to begin."*

### Smoke-test the install (no GUI)

```bash
# Verify imports
python -c "import app, surfaces, view_panel, parameters_panel, appearance_panel; print('OK')"

# Run the test suite (~4 seconds, 120 tests, no Qt window required)
pytest tests/ -v
```

---

## Using the application

The first time you launch, the viewport is empty. The two-step flow is:

1. **Pick a variety family** from the top-left dropdown (`Variety:` — K3, Enriques, Calabi–Yau, Fano).
2. **Pick a specific model** from the second dropdown that activates beside it (e.g., *Fermat quartic*, *Hanson quintic [Fig. 1]*).

The surface is computed and rendered immediately. From there:

- **Drag with the left mouse button** to rotate.
- **Scroll wheel or right-drag** to zoom.
- **Shift + drag** to pan.
- Move the **parameter sliders** in the right-hand *Parameters* dock — the surface re-renders when you release each slider (release-only, to keep the marching-cubes pipeline responsive).
- Use the **Appearance** dock to recolor, switch to wireframe, change opacity, or pick a different background.
- Use the **View** dock to apply camera presets, toggle axes / bounding box, clip the domain, or save a screenshot.
- The **status bar** shows the current model name, vertex / face counts, and current parameter values. Warnings (e.g. the Dwork conifold near `ψ ≈ 1`) appear here prefixed with ⚠.

---

## The four panels

### 1. Top control bar — variety selection

Cascading dropdowns. Each option carries a rich tooltip describing the equation, symmetry, and source.

### 2. Parameters dock (right, top)

Dynamically rebuilt every time you switch models — each slider is generated from the surface's `ParamSpec` list (name, label, min, max, default, step, suffix). A **Reset all to defaults** button restores the published defaults. For Calabi–Yau 3-folds, a context banner reminds you that the figures are 2D shadows, not the 6D variety itself.

### 3. Appearance dock (right, below Parameters)

- **Surface color** — color picker with swatch
- **Opacity** — 0–100 % slider
- **Style** — solid / wireframe / surface-with-edges
- **Lighting** — flat / smooth / Phong shading toggles
- **Background** — solid color picker, gradient on/off

All settings persist when you change surfaces.

### 4. View dock (left)

- **Camera presets** — Reset, Front, Top, Side, Isometric (each followed by a forced `render()` so the viewport actually updates)
- **Domain clip** — Off / Sphere / Cube with a radius slider; an outline overlay shows the clip region
- **Scene aids** — toggle bounding box, world-axes triad, grid axes
- **Screenshot** — save PNG with chooser dialog

The docks are all **movable and floatable** (Qt drag-handles). Dragging a dock between the left and right edges, or floating it onto a second monitor, works as expected.

---

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + R` | Reset camera to default isometric view |
| `Ctrl + Shift + S` | Save screenshot (PNG) |
| `Ctrl + D` | Reset all parameter sliders to defaults |

Mouse-camera bindings (VTK trackball, no rebinding):

| Mouse | Action |
|---|---|
| Left-drag | Rotate |
| Scroll / Right-drag | Zoom |
| Shift + drag | Pan |

---

## Project structure

```
algebraic-variety-cross-section/
├── app.py                  Main window — dropdowns, three docks, plotter wiring (~415 LOC)
├── surfaces.py             Mesh generators + Surface/ParamSpec dataclasses + VARIETIES registry (~1,070 LOC)
├── parameters_panel.py     Dynamic slider panel (rebuilds per surface)
├── appearance_panel.py     Color / wireframe / opacity / shading panel (right dock)
├── view_panel.py           Camera presets, domain clipping, scene aids, screenshot (left dock)
├── styles.py               Centralized stylesheet constants (palette, typography)
├── requirements.txt        Pinned dependency ranges
├── pytest.ini              testpaths = tests
├── tests/                  120-test pytest suite (~4 s, pure NumPy / PyVista, no Qt fixture)
│   ├── test_mesh_generators.py        Smoke tests for every generator + edge cases
│   ├── test_parameters_panel.py       Slider tick ↔ value math
│   ├── test_clip_domain.py            ViewPanel.clip_to_domain pure-function tests
│   ├── test_marching_cubes_empty.py   Empty-field ValueError propagation
│   └── test_grid_helpers.py           _grid_to_polydata + _concat_polydata
└── CONTEXT.md              Developer handoff document — read before contributing
```

`.gitignore` excludes `.venv/`, `__pycache__/`, `.idea/`, `.vscode/`, and `.claude/` build artefacts.

---

## How rendering works

The render pipeline in [app.py](app.py) is short and linear:

```
_on_subtype_changed   ──►  _render_current(reset_camera=True)
                                    │
                                    ▼
                  parameters_panel.values()  →  kwargs
                                    │
                                    ▼
                      surface.generate(**kwargs)  →  self._raw_mesh   (cached)
                                    │
                                    ▼
                _apply_domain_and_render(reset_camera)
                                    │
                                    ▼
                view_panel.clip_to_domain(self._raw_mesh)  →  (clipped, overlay)
                                    │
                                    ▼
                      plotter.add_mesh(clipped)  →  self._actor
                                    │
                                    ▼
              appearance_panel.apply_to_actor(self._actor)
                                    │
                                    ▼
                              plotter.render()
```

Two implementation details worth knowing:

- **The raw mesh is cached.** Adjusting the domain-clip radius re-clips the cached `_raw_mesh` without regenerating it — so the clip slider is snappy.
- **Implicit surfaces** (everything except the three Hanson CY3 figures) go through `_marching_cubes_to_polydata`, which validates that the field has a zero crossing, calls `skimage.measure.marching_cubes`, attaches gradient-based normals, welds duplicates, applies volume-preserving Taubin smoothing, and re-derives normals.
- **Parametric surfaces** (Hanson) are built from a 2D parameter grid via `_grid_to_polydata`, then concatenated patch-by-patch with `_concat_polydata`. They intentionally **skip Taubin smoothing** — the parametric grid is already C².

Read [CONTEXT.md](CONTEXT.md) for the full architecture rationale, the 5-phase development pattern used to add each variety, the 10+ bugs caught and fixed, and conventions for adding a new variety.

---

## Running the tests

```bash
pytest tests/ -v             # 120 tests, ~4 s
```

The suite is **Qt-free** — every test exercises pure NumPy / PyVista / scikit-image, so it runs in CI without a display server. There are no end-to-end UI tests; Qt + VTK does not run reliably under offscreen platforms on macOS, so manual launch is the verification path for the GUI itself.

The tests cover:

- Every generator in `surfaces.py` produces a non-degenerate mesh at default parameters
- Edge-case parameter values (boundary of valid range, no-zero-crossing fields)
- Slider tick ↔ value conversion math
- Sphere and cube domain clipping
- `_grid_to_polydata` / `_concat_polydata` helpers

---

## Extending the app

**Adding a new model to an existing variety** is straightforward:

1. Write a generator function in `surfaces.py` that returns a `pv.PolyData`. Implicit generators sample a scalar field on a cubic grid and call `_marching_cubes_to_polydata(field, bounds)`. Parametric generators build `(X, Y, Z)` 2D arrays and call `_grid_to_polydata(X, Y, Z)`.
2. Define a `<NAME>_PARAMS` list of `ParamSpec(name, label, minimum, maximum, default, step, suffix, description)` — one per slider.
3. Add `Surface(label, generator, params)` to the appropriate inner dict of `VARIETIES`. Use a `[Fig. N]` suffix in the dropdown key for consistency.
4. Add tooltip entries to `SUBTYPE_TOOLTIPS` (and `VARIETY_TOOLTIPS` if introducing a new family).
5. Add at least a smoke test in [tests/test_mesh_generators.py](tests/test_mesh_generators.py) and a parameter-range entry in [tests/test_parameters_panel.py](tests/test_parameters_panel.py).

**Adding a whole new variety family** is a larger effort — see Section 6 of [CONTEXT.md](CONTEXT.md) for the 5-phase pipeline (math research → implementation → adversarial review → remediation → UX pass) used for the existing four families.

---

## Troubleshooting

**The app launches but the viewport is black.**
You likely don't have a working OpenGL context. On Linux make sure `mesa-utils` / `libgl1` is installed; in WSL/SSH, use a real X server (or run the app on the desktop, not over SSH).

**`ImportError: ... PySide6` after install.**
Some Linux distros ship `python3` as 3.10 but `pip` resolves PySide6 wheels for 3.12. Use `python3 -m venv .venv` from the **same** Python that pip uses, then `pip install -r requirements.txt`.

**The status bar says "No real zero set in the sampling box for these parameters."**
This is expected behavior — the current parameter combination produces an equation with no real solutions in the sampled region. Move the offending slider back into a valid range. The tooltip on each parameter lists its valid range and the boundary effects.

**A `⚠` warning shows up in the status bar.**
Currently used by the Dwork pencil at `ψ ≈ 1` (the real conifold point — marching cubes silently misses the singularity). It's informational, not an error.

**Sliders feel jumpy on a Retina display.**
That's a Qt high-DPI scaling artefact. Run with `QT_AUTO_SCREEN_SCALE_FACTOR=1 python app.py`.

**Tests fail with VTK / segfault on CI.**
Don't try to construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen` — Qt + VTK GL context creation is unstable on macOS in offscreen mode. The 120 tests already avoid Qt entirely; keep new tests pure-NumPy / pure-PyVista.

---

## Further reading

The code is liberally annotated with citations and equations. Primary references for the four variety families:

- **K3.** Beauville, *Complex Algebraic Surfaces*. Hudson, *Kummer's Quartic Surface*. Wikipedia: K3 surface, Kummer surface.
- **Enriques.** Cossec–Dolgachev, *Enriques Surfaces I*. Dolgachev, *A Brief Introduction to Enriques Surfaces* (Kyoto 2013). Barth, "Two projective surfaces with many nodes" (1996). Endrass dissertation (1997).
- **Calabi–Yau.** Hanson, "A construction for computer visualization of certain complex curves," *Notices of the AMS* 41 (9), 1994. The Dwork pencil: any reference on mirror symmetry of the quintic.
- **Fano 3-folds.** Iskovskikh–Prokhorov, *Algebraic Geometry V: Fano Varieties*. Klein, *Vorlesungen über das Ikosaeder*. Segre's classical work on cubic threefolds.

The app is intended as a tool for exploring this literature, not a replacement for it.

---

## License

Not yet specified — this repository was initialized for personal research use. If you intend to redistribute or build on it, open an issue first.
