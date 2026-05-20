# Frontend-uplift source registry

**Purpose:** the curated list of sources each scout reaches for first.  Update here when a new tool / library / pattern proves valuable.  Loaded by individual scouts at Phase 1 start.

Keep entries one-line-per-source so a scout can grep this file for relevant rows when narrowing focus.

---

## 1. Visual / interaction / UX inspiration (2026 SOTA — scientific viz + desktop math software)

Studied by the **inspiration-scout** (and skimmed by the **visual-scout** when looking for "what does *good* look like in 2026 for a scientific-visualization desktop app").

| App / platform | URL | Why it matters | Notable patterns to study |
|---|---|---|---|
| ParaView | https://www.paraview.org/ | Industry-standard VTK-based scientific viz; the reference Qt + VTK desktop app | Dock organization, view-preset grid, animation timeline, color-map picker, multi-viewport layouts, screenshot/export menus |
| 3D Slicer | https://www.slicer.org/ | Qt + VTK medical imaging — dense scientific UI, pluggable modules | Module-switcher sidebar, scene-tree treeview, advanced color-map widgets, status-bar idioms |
| VisIt | https://visit-dav.github.io/visit-website/ | DOE-grade VTK desktop viz; alternative to ParaView | View-window management, expression editor, plot-attributes panel |
| Surfer (Mathematica.com) | https://imaginary.org/program/surfer | The closest existing app to algebraic-variety-cross-section — real-time algebraic-surface plotter from Imaginary.org | Equation entry, parameter sliders, math typography in the UI, the "tour" of preset surfaces — directly comparable |
| GeoGebra 3D | https://www.geogebra.org/3d | Approachable mathematics visualization — research+education hybrid | Tooltip discipline on every tool, parameter-slider polish, color-coded object hierarchy |
| Mathematica Manipulate (notebook UI) | https://reference.wolfram.com/language/ref/Manipulate.html | Reference for parameter-driven exploration UX | `Manipulate[Plot3D[...], {a,...}, {b,...}]` is the conceptual template for this app's dropdown+sliders |
| Maple 3D plotter | https://www.maplesoft.com/products/maple/ | Symbolic-math desktop app with high-fidelity 3D output | Plot-options inspector, lighting controls, color schemes |
| SageMath notebook 3D viewer | https://www.sagemath.org/ | Open-source symbolic / numerical math with three.js-driven 3D | Camera presets, axis labels, mesh export options |
| MeshLab | https://www.meshlab.net/ | Mesh-focused desktop tool (Qt) | Mesh-info panel, filter dialog discipline, smoothing-parameter sliders |
| Blender (math-viz subset) | https://www.blender.org/ | The DCC reference for 3D UI density | Outliner panel, properties-editor panel, viewport overlays — but Blender is also a warning about UI density gone too far |
| KAlgebra (KDE) | https://apps.kde.org/kalgebra/ | KDE/Plasma math-plotter desktop app | Reference Qt-stack math UI in 2024+ |
| Cinderella / surfex | http://www.cinderella.de/ , https://imaginary.org/program/surfex | Algebraic-geometry desktop tools | Equation input, real-locus rendering, parameter tuning |
| Inkscape / Krita / Scribus | https://inkscape.org/ | Established Qt/desktop apps with mature dock+toolbar UX | Dock state restoration, customizable toolbars, palette templates |
| JetBrains IDEs (PyCharm, IntelliJ) | https://www.jetbrains.com/ | Best-in-class IDE UX as a reference for "dense desktop app done right" | Settings-search discipline, recent files, find-anywhere, status-bar density |
| VS Code | https://code.visualstudio.com/ | Editor reference for command-palette + status-bar polish | Command palette (`Ctrl+Shift+P`), status-bar message zones, breadcrumbs |
| Linear / Notion / Figma (desktop apps) | https://linear.app/ , https://notion.so/ , https://figma.com/ | Modern desktop-app chrome and dark/light themes | Token-driven theming, focus rings, settle-on-state animations |
| Manim / Manim Community gallery | https://www.manim.community/ | Animation-as-explanation reference; 3Blue1Brown's tooling | Visual identity for math content; what "good math visuals" look like |
| Quanta Magazine | https://www.quantamagazine.org/ | High-end editorial science writing | Color palettes that suit math content; figure-caption discipline; restrained color usage |
| Stripe Press / Distill.pub (archived) | https://press.stripe.com/ , https://distill.pub/ | Editorial design for math/CS content | Drop-caps, typography rhythm, illustrated diagrams |
| 3Blue1Brown's blog | https://www.3blue1brown.com/ | Personal site of the manim-creator; calibrated for math-curious lay readers | Color tokens, animation tempo, math-typography choices |

**Mining heuristic:** for desktop scientific apps, prefer the actual app screenshots + documentation + UI guides — these are mostly public.  For web sources, WebFetch the production pages (Quanta, 3Blue1Brown) and study color/spacing/typography.  Avoid auth-walled UI screenshots; cite public assets.  Several open-source apps (ParaView, 3D Slicer, KAlgebra) have public design guidelines worth more than the homepage.

---

## 2. Modern PySide6 / Qt / PyVista / VTK libraries + plugins

Studied by the **library-scout**.  License + Qt6 compatibility + maintenance signal cited per project.

### PySide6 + Qt ecosystem

| Library | URL | License | Why study it | Positioning |
|---|---|---|---|---|
| QtAds (advanced docking system) | https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System | LGPL-2.1 | Replaces Qt's built-in dock system with richer floating / tabbed docking | Drop-in replacement candidate for `QDockWidget`; LGPL is fine with PySide6 |
| PyQt-Fluent-Widgets / qfluentwidgets | https://github.com/zhiyiYo/PyQt-Fluent-Widgets | GPL-3.0 (or commercial) | Fluent-Design widget set (Win11 / Mica-style chrome) | Study-only because of GPL; vendor-copy small primitives if license-compatible |
| qtawesome | https://github.com/spyder-ide/qtawesome | MIT | FontAwesome / Material icons as `QIcon`s | Cheap icon win for toolbar buttons |
| pyqtdarktheme / qdarktheme | https://github.com/5yutan5/PyQtDarkTheme | MIT | Modern dark + light Qt themes via QSS | Direct dark-mode candidate (INT-94) |
| qt-material | https://github.com/UN-GCPDS/qt-material | BSD-2-Clause | Material Design styling for PySide6/PyQt6 | Alternative theme engine |
| QScintilla | https://riverbankcomputing.com/software/qscintilla/ | GPL-3.0 (or commercial) | Code-editor widget | Only relevant if equation entry becomes a future surface |
| superqt | https://github.com/pyapp-kit/superqt | BSD-3-Clause | Quality-of-life Qt widgets — collapsible group box, throttled signals, range slider | High-value lift for slider polish + collapsible panels |
| PyQtGraph | https://www.pyqtgraph.org/ | MIT | Scientific 2D plotting on Qt — fast OpenGL backed | Only if a 2D companion plot (e.g. parameter-sweep) is added |
| qframelesswindow | https://github.com/zhiyiYo/PyQt-Frameless-Window | LGPL-3.0 / GPL-3.0 | Frameless main window with native title bar feel | Aesthetic candidate; license check matters |

### PyVista / VTK ecosystem

| Library | URL | License | Why study it | Positioning |
|---|---|---|---|---|
| PyVista (pinned to <0.49 in requirements) | https://github.com/pyvista/pyvista | MIT | Track PyVista releases for new mesh ops, plotter features, MarchingCubes alternatives | Existing dep; watch for >=0.49 breaking changes |
| pyvistaqt (pinned <0.12) | https://github.com/pyvista/pyvistaqt | MIT | `QtInteractor` widget — the central viewport | Existing dep |
| trame | https://kitware.github.io/trame/ | Apache-2.0 | Kitware's modern web+desktop framework on top of VTK | Heavy; only relevant if you're considering a web companion app |
| MeshIO | https://github.com/nschloe/meshio | MIT | Cross-format mesh I/O (STL / OBJ / PLY / VTU / …) | Pairs with INT-93 mesh-export candidate |
| MeshFix / pymeshfix | https://github.com/pyvista/pymeshfix | GPL-2.0+ | Mesh repair for non-manifold cleanup | License-watch; GPL-2.0+ is import-blocking |
| numpy-stl | https://github.com/wolph/numpy-stl | BSD-3-Clause | Pure-numpy STL writer | Lightweight alternative to MeshIO for STL-only export |

### scientific Python / surrounding stack

| Library | URL | License | Why study it |
|---|---|---|---|
| scikit-image (pinned <0.27) | https://scikit-image.org/ | BSD-3-Clause | Existing — track marching_cubes API stability |
| SymPy | https://www.sympy.org/ | BSD-3-Clause | Symbolic math; could power equation-typography rendering or symbolic parameter validation |
| matplotlib | https://matplotlib.org/ | BSD-3-Clause-like | NOT for 3D (AI-1 anti) but the matplotlib-mathtext renderer could provide rendered equation tooltips |
| KaTeX (via PyQt WebEngineView) | https://katex.org/ | MIT | Rendered-math tooltip / overlay (INT-95) candidate — requires `QtWebEngineWidgets` |
| MathJax v4 | https://www.mathjax.org/ | Apache-2.0 | Heavier alternative to KaTeX; usually overkill |
| imageio / Pillow | https://imageio.readthedocs.io/ , https://python-pillow.org/ | BSD-2-Clause / MIT-CMU | Image post-processing for off-screen renders; Pillow already transitively present |

### Animation / motion (sparing — desktop apps lean less on motion than web)

| Library | URL | License | Why study it |
|---|---|---|---|
| Qt's `QPropertyAnimation` + `QParallelAnimationGroup` | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QPropertyAnimation.html | LGPL | Built into PySide6; the right answer for INT-24 camera transitions and INT-90 parameter sweeps |
| pyvista's `Plotter.fly_to(...)` | https://docs.pyvista.org/api/plotting/_autosummary/pyvista.Plotter.fly_to.html | MIT | Limited camera-interpolation primitive |

### Build / packaging / DX

| Tool | URL | License | Why study it |
|---|---|---|---|
| PyInstaller | https://www.pyinstaller.org/ | GPL-2.0 (with import exception — OK for end-user redistribution) | Bundling the app as a single executable; relevant if distribution becomes a candidate |
| Briefcase (BeeWare) | https://briefcase.readthedocs.io/ | BSD-3-Clause | Alternative packager — cross-platform .app / .msi / .dmg |
| uv / Poetry | https://docs.astral.sh/uv/ , https://python-poetry.org/ | Apache-2.0 / MIT | Modern Python deps; uv is fast — relevant if `requirements.txt` evolves to `pyproject.toml` |
| pre-commit | https://pre-commit.com/ | MIT | Lint/format hooks; ruff + black orientation worth checking |
| ruff | https://github.com/astral-sh/ruff | MIT | Fast Python linter; worth surfacing as a candidate if the repo lacks lint config |

---

## 3. Algebraic Variety Viewer codebase orientation (read first by every scout)

| Path | What it is |
|---|---|
| `/CONTEXT.md` | The authoritative developer handoff — §3 stack rationale, §4 architecture, §5 math conventions per variety, §6 the 5-phase pipeline, §8 bugs caught and fixed, §9 things explicitly NOT done |
| `/README.md` | User-facing description; covers what each variety is, install, the four panels, project structure, troubleshooting |
| `/.claude/references/app-invariants.md` | AI-1 .. AI-15 architectural locks |
| `/.claude/references/frontend-uplift/design-system.md` | This pipeline's design-system inventory; underdeveloped surfaces in §7 |
| `/.claude/references/frontend-uplift/interaction-vocabulary.md` | [INT-N] primitives every scout cites |
| `/app.py` | `MainWindow` — dropdowns, three docks, plotter wiring, status-bar, render pipeline.  ~415 LOC. |
| `/surfaces.py` | All generators + `Surface` / `ParamSpec` dataclasses + `VARIETIES` registry + tooltips.  ~840–1070 LOC. |
| `/parameters_panel.py` | Dynamic slider panel; rebuilds from `ParamSpec` list per surface |
| `/appearance_panel.py` | Color / wireframe / opacity / shading panel (right dock) |
| `/view_panel.py` | View presets, camera, scene aids, domain clip, screenshot (left dock) |
| `/styles.py` | Centralized stylesheet constants (palette, typography, dock-header CSS, focus ring) |
| `/requirements.txt` | Pinned dependency ranges; check this BEFORE proposing a new dep |
| `/tests/` | 120 tests, ~4s, pure-NumPy / pure-PyVista / static-math (NO Qt fixtures) |
| `/tests/test_mesh_generators.py` | Smoke tests for every generator + edge cases |
| `/tests/test_parameters_panel.py` | Static slider tick ↔ value math |
| `/tests/test_clip_domain.py` | ViewPanel.clip_to_domain pure-function tests |
| `/tests/test_marching_cubes_empty.py` | Empty-field `ValueError` propagation |
| `/tests/test_grid_helpers.py` | `_grid_to_polydata` + `_concat_polydata` |

The **current-state-critic** owns end-to-end traversal of these.  Other scouts skim them, then focus externally.

---

## 4. Canonical 5-surface set for the visual scout

When `surfaces_to_render` is empty (the default), the visual scout renders these surfaces in order via `pv.OFF_SCREEN = True` and `pv.Plotter(off_screen=True, window_size=(1200, 800)).show(screenshot=...)`:

1. **`app-startup`** — capture the app at startup state (empty viewport + "Choose a variety to begin" status).  This is captured by introspecting `app.py` constants + `_PLACEHOLDER` rather than a live Qt screenshot (AI-3 forbids that).  The "render" here is a synthetic mockup: the visual scout describes what the user sees and notes the design-system surface in `app.py:setStatusBar(...)`.
2. **`k3-fermat`** — `VARIETIES["K3 surface"]["Fermat quartic"]` at default parameters
3. **`k3-kummer`** — `VARIETIES["K3 surface"]["Kummer surface"]` at default parameters
4. **`enriques-canonical`** — `VARIETIES["Enriques surface"]["Canonical sextic  [Fig. 1]"]` (or equivalent canonical) at defaults
5. **`cy-hanson-quintic`** — `VARIETIES["Calabi–Yau 3-fold"]["Hanson quintic  [Fig. 1]"]` at defaults (the iconic image)

For each surface the visual scout captures:
- **default-render** at 1200×800 → `{RENDER_DIR}/<slug>-default.png`
- **high-res render** at 2400×1600 → `{RENDER_DIR}/<slug>-2x.png` (tests rendering quality on HiDPI)

Optional sixth render — Dwork pencil at ψ = 1.0 — useful for testing the conifold-warning visual surface; capture only when the uplift brief mentions warnings / status-bar polish.

User override via `init-uplift.sh --surfaces "K3 surface/Fermat quartic,Enriques surface/Cayley quartic symmetroid"` replaces this list verbatim (stored in `state.surfaces_to_render` as `Variety/Subtype-key` pairs).

**Sample-surface rotation:** when a candidate involves Calabi–Yau-specific rendering (e.g., the Hanson normals fix, the Dwork conifold warning), prefer adding the Hanson asymmetric (5,3) and the Dwork pencil to the render set on a second pass.

---

## 5. Hard rules (every scout)

- **License citation is mandatory** for every library / OSS reference.  GPL/AGPL is study-only, never import.
- **Qt6 / PySide6 compatibility check** is non-negotiable for client-side libs — many PyQt5-era libraries don't have PySide6 equivalents.
- **App-invariant respect:** AI-1 (PySide6+PyVista stack), AI-2 (Qt-free tests), AI-3 (pv.OFF_SCREEN for headless render), AI-4 (clip_scalar, not clip_box), AI-13 (6-digit hex in PyVista).  Per `.claude/references/app-invariants.md`.
- **WCAG AA contrast** for any new text-color proposal — cite the ratio (`COLOR_MUTED = #5a5a5a` on `#f0f0f0` ≈ 5.4:1 is the baseline; aim ≥4.5:1 body / ≥3:1 large).
- **No vendor-blog hype.**  Weight a source by primary evidence (changelog, docs, GitHub release notes, app's actual UI).
- **No code in briefs.**  Scouts write briefs; implementation happens later.
