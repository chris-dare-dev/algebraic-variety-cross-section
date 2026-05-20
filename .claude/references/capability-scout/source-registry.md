# Capability-scout source registry

**Purpose:** the curated list of sources each scout reaches for first.  Update here when a new venue / publication / repo proves valuable.

This file is loaded by individual scouts at Phase 1 start (NOT by the main session at slash-command load time).  Keep entries one-line-per-source so a scout can grep this file for relevant rows when it has a narrow topic.

---

## Competitive landscape — peer scientific-viz / algebraic-geometry desktop apps

| App / platform | URL | Why it matters | Notable patterns to study |
|---|---|---|---|
| ParaView | https://www.paraview.org/ | The industry-standard VTK desktop app; direct architectural peer | Dock organization, view-preset grid, animation timeline, color-map preset menus, multi-viewport layouts, screenshot/export menus |
| 3D Slicer | https://www.slicer.org/ | Qt + VTK medical imaging; dense scientific UI with pluggable modules | Module-switcher sidebar, scene-tree treeview, color-map widgets, status-bar idioms, plugin architecture |
| VisIt | https://visit-dav.github.io/visit-website/ | DOE-grade VTK desktop viz | View-window management, expression editor, plot-attributes panel |
| Surfer / Imaginary.org | https://imaginary.org/program/surfer | Closest direct peer — real-time algebraic-surface plotter | Equation entry, parameter sliders, math typography, "tour" of preset surfaces, social-share affordances |
| Surfex | https://imaginary.org/program/surfex | Algebraic-geometry real-locus visualizer (Cinderella-derived) | Renderer pipeline, parameter UI, equation parser |
| GeoGebra 3D | https://www.geogebra.org/3d | Research+education hybrid math software | Tooltip discipline, parameter-slider polish, color-coded object hierarchy |
| Mathematica Manipulate | https://reference.wolfram.com/language/ref/Manipulate.html | Reference for parameter-driven exploration UX | `Manipulate[Plot3D[...], {a,...}]` is the conceptual template; reference for high-fidelity rendered math labels |
| Maple plots | https://www.maplesoft.com/products/maple/ | Symbolic-math desktop with high-fidelity 3D output | Plot-options inspector, lighting controls, color schemes |
| SageMath three.js notebook viewer | https://www.sagemath.org/ | Open-source symbolic / numerical math | Camera presets, axis labels, mesh export options |
| Magma calculator (online algebraic-geometry tool) | http://magma.maths.usyd.edu.au/calc/ | Web-based algebraic-geometry computation | Reference for what algebraic-geometers expect to compute, even if UI is bare |
| KAlgebra (KDE) | https://apps.kde.org/kalgebra/ | KDE Plasma math-plotter | Reference Qt-stack math UI in 2024+ |
| MeshLab | https://www.meshlab.net/ | Qt mesh-focused desktop tool | Mesh-info panel, filter dialog discipline, smoothing-parameter sliders |
| Blender | https://www.blender.org/ | DCC reference for 3D UI density | Outliner / properties / viewport overlays — also a warning about UI density gone too far |
| Cinderella | http://www.cinderella.de/ | Interactive geometry desktop | Real-locus rendering, parameter tuning, reference for the Imaginary.org tooling family |
| Inkscape / Krita / Scribus | https://inkscape.org/ | Mature Qt/desktop apps with mature dock+toolbar UX | Dock state restoration, customizable toolbars, palette templates |
| Cura / OpenSCAD | https://ultimaker.com/software/ultimaker-cura/ , https://openscad.org/ | Qt-stack technical desktop apps | UI patterns for parameter-driven generative output |
| 3Blue1Brown's manim ecosystem | https://www.3blue1brown.com/ , https://www.manim.community/ | Animation-as-explanation reference | Visual identity for math content; what "good math visuals" look like |
| Quanta Magazine | https://www.quantamagazine.org/ | High-end editorial science writing | Color palettes for math content; figure-caption discipline |
| Distill.pub (archived) | https://distill.pub/ | Interactive ML papers | Reactive figures, hover citations, side-by-side equation+code |

**How to mine these:** for desktop apps, WebFetch their official documentation / user guides / screenshot galleries (most are public, no auth).  Cite the actual production UI pattern with a screenshot path or doc-section reference, not vague "it has nice tooling."

---

## Math-research venues — algebraic-surface visualization literature

| Venue | URL pattern | Coverage |
|---|---|---|
| arXiv math.AG (algebraic geometry) | https://arxiv.org/list/math.AG/ | Primary source for new variety constructions, real-locus papers, classification updates |
| arXiv math.NA + math.CO | https://arxiv.org/list/math.NA/ , https://arxiv.org/list/math.CO/ | Numerical / combinatorial aspects of variety visualization |
| Wikipedia (math + algebraic-geometry) | https://en.wikipedia.org/ | Reference for variety definitions; cite verbatim section anchors |
| MathWorld | https://mathworld.wolfram.com/ | Cross-reference for equations + tooltip drafting |
| Cossec-Dolgachev "Enriques Surfaces I" | https://www.math.lsa.umich.edu/~idolga/EnriquesOne.pdf | Authoritative reference for Enriques constructions |
| Iskovskikh-Prokhorov "Algebraic Geometry V: Fano Varieties" | https://link.springer.com/book/10.1007/978-3-662-03276-3 | Authoritative reference for Fano 3-folds (next variety per README) |
| Hanson 1994 "A construction for computer visualization of certain complex curves" | https://www.ams.org/notices/199409/199409FullIssue.pdf | The CY3 parametric cross-section foundation (Notices of the AMS 41(9)) |
| Endrass 1997 dissertation + Barth 1996 | (Cite from Wikipedia / Cossec) | Icosahedral sextic / Enriques figure 4 sources |
| Hudson "Kummer's Quartic Surface" | (Classical text) | Kummer surface canonical reference |
| Dolgachev "A Brief Introduction to Enriques Surfaces" (Kyoto 2013) | https://www.math.lsa.umich.edu/~idolga/kyoto13.pdf | Modern survey of Enriques figures |
| arXiv:1906.01445 (Cayley quartic symmetroid context) | https://arxiv.org/abs/1906.01445 | Modern context for Enriques figure 3 |
| Manim Community gallery | https://docs.manim.community/en/stable/examples.html | Reference for what good math visualization looks like |
| MathOverflow + Math StackExchange | https://mathoverflow.net/ , https://math.stackexchange.com/ | High-signal Q&A on variety-specific visualization choices |
| Imaginary.org gallery (Surfer / surfex output) | https://imaginary.org/gallery | Visual reference for what algebraic-surface visualization looks like |
| SageMath docs (algebraic geometry) | https://doc.sagemath.org/html/en/reference/schemes/ | Reference algebra over varieties |
| Macaulay2 docs (Algebraic Geometry package) | http://www2.macaulay2.com/Macaulay2/doc/Macaulay2-1.22/share/doc/Macaulay2/AlgebraicGeometry/html/index.html | Reference computational AG |

**Time-window discipline:** scouts cite work from the **last 24 months** by default for tooling / technique trends.  For variety mathematics, classical references are foundational and always allowed (Cossec-Dolgachev, Iskovskikh-Prokhorov, Hanson 1994).

---

## OSS / GitHub trends — scientific Python + Qt + PyVista ecosystem

| Project | URL | License | Why it matters |
|---|---|---|---|
| PyVista | https://github.com/pyvista/pyvista | MIT | The base mesh-handling lib — track releases for new mesh ops, plotter features |
| pyvistaqt | https://github.com/pyvista/pyvistaqt | MIT | The `QtInteractor` widget — central viewport |
| VTK | https://github.com/Kitware/VTK | BSD-3-Clause | Foundation; PyVista wraps it.  Direct VTK use is verbose but sometimes necessary |
| scikit-image | https://github.com/scikit-image/scikit-image | BSD-3-Clause | `measure.marching_cubes` provider |
| PySide6 / Qt for Python | https://wiki.qt.io/Qt_for_Python | LGPL-3 | The GUI framework |
| qtawesome | https://github.com/spyder-ide/qtawesome | MIT | FontAwesome / Material icons as `QIcon` |
| superqt | https://github.com/pyapp-kit/superqt | BSD-3-Clause | Quality-of-life Qt widgets (collapsible group box, throttled signals, range slider) |
| PyQtDarkTheme | https://github.com/5yutan5/PyQtDarkTheme | MIT | Modern dark + light Qt themes |
| QtAds | https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System | LGPL-2.1 | Advanced docking system; superset of `QDockWidget` |
| pyqtgraph | https://github.com/pyqtgraph/pyqtgraph | MIT | Fast scientific 2D plotting; complement to 3D viewport |
| MeshIO | https://github.com/nschloe/meshio | MIT | Cross-format mesh I/O (STL / OBJ / PLY) — pairs with mesh-export candidate |
| numpy-stl | https://github.com/wolph/numpy-stl | BSD-3-Clause | Lightweight pure-numpy STL writer |
| SymPy | https://github.com/sympy/sympy | BSD-3-Clause | Symbolic math; could power LaTeX-equation tooltips or symbolic parameter validation |
| trame | https://github.com/Kitware/trame | Apache-2.0 | Kitware's modern web+desktop framework on top of VTK; relevant only if a web companion becomes a candidate |
| polyscope | https://github.com/nmwsharp/polyscope | MIT | Alternative C++ 3D viewer with Python bindings; sometimes lighter than VTK |
| napari | https://github.com/napari/napari | BSD-3-Clause | Qt-based scientific imaging viewer (multidim arrays); reference for what dense-research-tool UX looks like in Qt+Python |
| Spyder IDE | https://github.com/spyder-ide/spyder | MIT | Reference Qt+Python desktop app (the qtawesome creators) |
| manim / manim-community | https://github.com/3b1b/manim , https://github.com/ManimCommunity/manim | MIT | Animation-of-math reference |
| imaginary-org `Surfer` source (if available) | https://github.com/imaginary-org | varied | Direct peer source to mine |
| matplotlib | https://github.com/matplotlib/matplotlib | BSD-style | mathtext renderer for rendered-equation surfaces |
| Pillow / imageio | https://github.com/python-pillow/Pillow , https://github.com/imageio/imageio | MIT-CMU / BSD-2 | Post-processing for off-screen renders |
| ruff | https://github.com/astral-sh/ruff | MIT | Fast Python linter — worth checking if the repo lacks lint config |
| pytest | https://github.com/pytest-dev/pytest | MIT | Track features (already in use) |
| hypothesis | https://github.com/HypothesisWorks/hypothesis | MPL-2.0 | Property-based testing — useful for testing generator-parameter ranges |
| numba | https://github.com/numba/numba | BSD-2-Clause | JIT-compile heavy NumPy code — relevant only if marching cubes becomes a bottleneck |
| JAX | https://github.com/jax-ml/jax | Apache-2.0 | GPU-accelerated linear algebra; very heavy dep — overkill for current scope |
| sympy.geometry | https://docs.sympy.org/latest/modules/geometry/ | BSD-3-Clause | Symbolic curve / surface descriptions |

**License discipline:** every OSS reference cites license verbatim.  GPL/AGPL is a non-import flag for the redistributable binary (PySide6 LGPL stack) — fine to study, NOT fine to vendor.  LGPL-* is generally fine if dynamically linked.

---

## Desktop-platform sources — Qt6 / VTK / OpenGL features + cross-platform desktop standards

| Source | URL | What to look for |
|---|---|---|
| Qt 6 changelog | https://doc.qt.io/qt-6/whatsnew60.html | Qt6.5, 6.6, 6.7+ new widgets; touch / pen API; HiDPI improvements; theming additions |
| Qt for Python docs | https://doc.qt.io/qtforpython-6/ | PySide6-specific API + binding patterns |
| KDE Human Interface Guidelines | https://develop.kde.org/hig/ | Modern Linux/Qt desktop UX standards |
| GNOME HIG | https://developer.gnome.org/hig/ | Cross-reference for desktop UX expectations |
| Microsoft Fluent Design | https://www.microsoft.com/design/fluent/ | Windows 11 chrome reference — patterns translatable to Qt |
| Apple Human Interface Guidelines (macOS) | https://developer.apple.com/design/human-interface-guidelines/ | macOS desktop UX — relevant given the primary platform |
| VTK feature matrix / changelogs | https://gitlab.kitware.com/vtk/vtk | Track new rendering features (OpenGL backend updates, ray tracing) |
| OpenGL / WebGPU / Vulkan briefs | https://www.khronos.org/ | Future-rendering surface (only relevant if VTK upstream adopts) |
| Web platform features (CanIUse for any web-companion candidate) | https://caniuse.com/ | Only relevant if a trame / browser companion appears |
| QtAccessible API | https://doc.qt.io/qt-6/accessible.html | Qt accessibility surface — for screen-reader compatibility |
| WCAG 2.1 / 2.2 spec | https://www.w3.org/TR/WCAG21/ , https://www.w3.org/TR/WCAG22/ | Contrast ratio definitions, keyboard nav rules (AI-12) |
| Qt theming / styling | https://doc.qt.io/qt-6/qss-syntax.html | QSS syntax reference for `styles.py` evolution |
| HiDPI / Retina support in Qt | https://doc.qt.io/qt-6/highdpi.html | The `QT_AUTO_SCREEN_SCALE_FACTOR` workaround referenced in README |
| PEP 668 / Python packaging on Linux | https://peps.python.org/pep-0668/ | Distribution implications if PyInstaller / Briefcase becomes a candidate |

**Survey heuristic:** prioritize platform features documented as stable in Qt 6.5+ (Qt 6's LTS line).  Beta / preview APIs are parking-lot items.

---

## Algebraic Variety Viewer codebase orientation (read first by every scout)

| Path | What it is | Why a scout reads it |
|---|---|---|
| `/CONTEXT.md` | Top-level repo conventions, math conventions per variety, the 5-phase pipeline, bugs caught | App invariants context, math discipline, what's intentionally not done |
| `/README.md` | User-facing description | What the app claims to do — sometimes aspirational (Fano 3-fold §) vs CONTEXT.md ground truth |
| `/app.py` | `MainWindow` + dropdowns + 3 docks + plotter wiring | UI surface inventory |
| `/surfaces.py` | All generators + `Surface`/`ParamSpec` + `VARIETIES` | What surfaces exist; how new ones get added |
| `/parameters_panel.py` , `/appearance_panel.py` , `/view_panel.py` | The three docks | What's already built; what's underdeveloped (design-system.md §7) |
| `/styles.py` | Centralized stylesheet | Color tokens, typography, focus ring |
| `/requirements.txt` | Pinned deps | What's already a dep — don't re-propose adding it |
| `/tests/` | 120 tests, pure-NumPy / pure-PyVista / static-math | What's currently tested; what isn't (Qt-free constraint per AI-2) |
| `/.claude/references/app-invariants.md` | AI-1 .. AI-15 | Architectural locks for the Challenger |

The **adversary scout** (Phase 1 scout #5) is responsible for end-to-end traversal of these.  The other four scouts do quick orientation reads, then focus their attention externally.

---

## Hard rules (every scout)

- **License citation is mandatory** for every OSS reference.
- **Citation format:** for arXiv use `arXiv:NNNN.NNNNN` + year; for docs use URL + section anchor; for GitHub use URL + last-commit-date.
- **Time-window:** last 24 months for tooling/technique trends.  Classical math references (Cossec-Dolgachev, Iskovskikh-Prokhorov, Hanson 1994) are always allowed for variety mathematics.
- **No speculation about repo internals.**  Every "the app already does X" or "the app doesn't do X" claim has a `file:line` citation.
- **No vendor-blog hype.**  If a source's only evidence is its own marketing page, weight it accordingly.
- **Boundary respect:** scouts do NOT write code; they write briefs.
- **PySide6 (LGPL) redistribution awareness:** library candidates' licenses must be import-compatible (MIT / Apache-2.0 / BSD / LGPL) OR explicitly marked study-only (GPL-3.0 / AGPL).
