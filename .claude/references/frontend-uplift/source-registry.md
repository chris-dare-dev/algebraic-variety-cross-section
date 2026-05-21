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

## 4b. Canonical panel-chrome capture set

The visual scout needs pixel-truth on the Qt panel chrome — slider rails, group-box headers, button states, QSS-rendered colors — not just the 3D surfaces.  Phase 1a' of `/frontend-uplift` runs `.claude/scripts/frontend-uplift/render-panel-chrome.py` which captures each panel widget directly via `QT_QPA_PLATFORM=offscreen` + `QWidget.grab()`.  This is safe under AI-3 (clarifying paragraph) because the three panel classes — `AppearancePanel`, `ViewPanel`, `ParametersPanel` — host no `QtInteractor` and therefore create no VTK GL context.

For each panel the script captures two states at two resolutions per theme:

| Panel | Empty state | Populated state |
|---|---|---|
| **AppearancePanel** | default colors, opacity 100%, Phong, no wireframe | opacity 72%, wireframe on (exercises active slider + active checkbox styling) |
| **ViewPanel** | domain Off, no overlays | domain Sphere, bbox overlay on (exercises active combo + checkbox styling) |
| **ParametersPanel** | "(no parameters for this surface)" placeholder + disabled reset button | K3 / Fermat quartic's 4 ParamSpecs (`c`, `α`, `β`, `γ`) + context hint banner + enabled reset button |

PNG names: `<panel>-<theme>-<state>-<resolution>.png` — e.g. `parameters-light-populated-2x.png`.

Themes captured:
- **light** — always emitted (`styles.APP_STYLESHEET`)
- **dark** — auto-emitted only if `styles.APP_STYLESHEET_DARK` exists (UPL-4 forward-compat; not present in 2026-05 baseline)

Outputs land under `{RENDER_DIR}/panels/` alongside the surface renders.  Total capture count today: **12 PNGs** (3 panels × 2 states × 2 resolutions × 1 theme).  When UPL-4 lands the dark theme adds another 12 with no slash-command edit.

**When the script breaks at construction:** the most common drift is a panel constructor signature changing (e.g. `AppearancePanel` adding a required argument).  The preflight `ensure-render-up.sh` probes `AppearancePanel(get_actor, get_plotter)` specifically so signature drift surfaces at preflight, not deep inside the visual scout.  When that happens, edit `render-panel-chrome.py` to match the new signature in the same PR as the panel change.

**When a panel's private setter attribute is renamed:** the populated-state setup pokes private attributes (`_opacity_slider`, `_wireframe_cb`, `_domain_mode`, `_bbox_cb`, `_axes_cb`).  These are *unconditional* accesses — if a panel rename ships, the script fails loudly with `AttributeError` (correct).  The script ALSO performs a post-capture sha256 check of every empty/populated pair and emits a stderr WARNING (`populated capture IDENTICAL to empty`) if any pair hashes the same.  This catches a related failure mode: the access succeeded but the setter call has no visual effect (e.g. signals were blocked, theme didn't repaint, etc.).  Always check stderr for these warnings after a run.

**Two-resolution captures are NOT HiDPI captures.**  The `-2x.png` files are the widget resized to 2× nominal at device-pixel-ratio 1 — they test layout at a wider dock, not Retina sub-pixel rendering.  True DPR-2 captures require a headed macOS session (`screencapture -l <window-id>` honors DPR) — see Tier 2 design notes below.

### §4b.1 — Tier 2 design notes (proposed integrated-window capture)

Tier 2 has not been implemented.  When it is, the chat-message proposal needs the following refinements (lessons from the Tier 1 adversary review):

- **Window-finder strategy.**  The original sketch used `osascript -e 'tell app "System Events" to id of window 1 of (first process whose frontmost is true)'`.  This grabs whichever app happens to be frontmost — likely the terminal that launched the subprocess, NOT `app.py`.  Use PID-based lookup instead: `tell app "System Events" to id of window 1 of (first process whose unix id is <PID>)` where `<PID>` is the just-launched `app.py` subprocess id.

- **Readiness gating.**  The original sketch used a fixed `sleep 1.8` before `screencapture`.  VTK GL context + shader compilation on first `show()` can take 3–5 s on a loaded system; the capture would frame the empty placeholder.  Use a watchfile readiness signal instead: `app.py` writes `.avc_ready` after the first surface render completes; the capture script polls (with a generous timeout) for the file to appear, then captures, then deletes it.

- **`AVC_AUTO_PRESET` re-entrancy.**  `MainWindow._render_current` is wrapped in the AI-9 `self._computing` guard.  The env-var hook must set `_computing = False` *before* invoking the preset's render call, and must not re-fire while the first render is still in flight.  Schedule the auto-preset render via `QTimer.singleShot(0, ...)` after `__init__` returns so the constructor completes before the first render call lands.

- **Screen Recording permission.**  `screencapture -l <window-id>` requires macOS Screen Recording permission for the invoking process (Terminal / iTerm / Claude Code).  First-time use triggers a system permission prompt.  Document the one-time grant flow in the slash command's Tier 2 section; under SSH or in CI the prompt is suppressed and the capture fails silently — the script must `defaults read com.apple.universalaccess` (or equivalent) to detect the grant before attempting capture, and surface a clear "grant Screen Recording to <app> in System Settings" diagnostic otherwise.

- **`--live-chrome` flag propagation.**  The slash command's Phase 1a' block must read `state.tier2_live_chrome` (or accept the flag in the slash-command arg parser, persist into `state.json` via `init-uplift.sh`, and check it here).  Otherwise the flag can't reach the orchestrator's tool calls.

- **HiDPI behavior.**  `screencapture -l` on Retina captures at DPR 2 automatically — these ARE true HiDPI captures (unlike Tier 1's `-2x.png` files).  Document the resulting pixel dimensions clearly (e.g. `1600×1000` logical → `3200×2000` pixel on Retina) so the visual scout doesn't misread captures from different machines.

- **Cross-platform.**  Tier 2 is explicitly macOS-only.  On Linux / Windows, `--live-chrome` should silently fall back to Tier 1 (panel captures only) with an info-level message — never error.

These notes do NOT mandate the Tier 2 implementation — they are constraints to honor when it's built.

### §4b.2 — Tier 3 production-grade ceiling (capabilities Tier 1+2 still cannot provide)

Even with Tier 1 + Tier 2 fully implemented, a visual scout cannot see: interactive state transitions (slider drag, button hover, focus-on-tab), hover styles, focused-widget states (`:focus` rings), tooltip pixel evidence, modal dialogs (QColorDialog, QFileDialog), the viewport with parameters interactively varied, error/warning status-bar transitions, animation frames, or the accessibility tree.  The "real production-grade" follow-up would add:

- **Tier 3A — Programmatic interaction replay.**  Extend `render-panel-chrome.py` with `PySide6.QtTest.QTest.setFocus / mousePress / keyClick` calls between grabs to capture focused, hovered, and pressed control states.  Scope: ~1 day.
- **Tier 3B — Headed sequence capture.**  Tier 2 + a sequence of programmatic state changes (load surface → apply clip → toggle wireframe → toggle scene aids) with a capture per state.  Scope: ~2–3 days.
- **Tier 3C — Accessibility tree.**  Enumerate the widget tree via macOS' `NSAccessibility` (or Linux's AT-SPI2) to give the LLM tab order, role/state, and tooltip text as structured data complementing the pixels.  Scope: ~1 day per platform.

These are deferred to a future milestone.  Tier 1 (shipped) + Tier 2 (designed but not built) cover the high-value 80% — Tier 3 is the diminishing-returns refinement.

---

## 5. Hard rules (every scout)

- **License citation is mandatory** for every library / OSS reference.  GPL/AGPL is study-only, never import.
- **Qt6 / PySide6 compatibility check** is non-negotiable for client-side libs — many PyQt5-era libraries don't have PySide6 equivalents.
- **App-invariant respect:** AI-1 (PySide6+PyVista stack), AI-2 (Qt-free tests), AI-3 (pv.OFF_SCREEN for headless render), AI-4 (clip_scalar, not clip_box), AI-13 (6-digit hex in PyVista).  Per `.claude/references/app-invariants.md`.
- **WCAG AA contrast** for any new text-color proposal — cite the ratio (`COLOR_MUTED = #5a5a5a` on `#f0f0f0` ≈ 5.4:1 is the baseline; aim ≥4.5:1 body / ≥3:1 large).
- **No vendor-blog hype.**  Weight a source by primary evidence (changelog, docs, GitHub release notes, app's actual UI).
- **No code in briefs.**  Scouts write briefs; implementation happens later.
