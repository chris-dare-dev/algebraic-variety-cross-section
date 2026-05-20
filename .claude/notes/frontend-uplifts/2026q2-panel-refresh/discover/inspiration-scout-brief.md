# Inspiration Scout Brief — 2026 Q2 Panel Refresh
**Date:** 2026-05-20  
**Scout:** inspiration-scout  
**Session:** algebraic-variety-cross-section / frontend-uplift / 2026q2-panel-refresh

---

## 1. TL;DR

**Top-3 patterns worth borrowing:**
1. **Color-map preset menu** (ParaView / 3D Slicer) — every peer VTK-based tool exposes a named preset menu alongside the raw color picker; the app today has only a bare `QColorDialog` swatch with no presets at all.
2. **Dark-mode chrome with Manim/3B1B-grade deep-navy palette** — the math-research audience (Quanta, 3Blue1Brown, Manim community) expects a low-luminance environment that lets surface colors pop; the app is light-only today with no dark palette candidate.
3. **Collapsible panel sections with per-variety color templates** (GeoGebra 3D / Blender) — collapsing panel groups reduces cognitive load when exploring unfamiliar varieties; pairing with per-variety default color tokens gives instant visual family recognition.

**Main thematic shift:** the app's chrome is currently closer to a generic Qt form than to a scientific-visualization tool. The 2026 SOTA in peer tools shares three signals — a dark or deep-navy canvas, named color-map presets, and a data-probe / status-bar that surfaces mesh metadata continuously — all of which are absent or underdeveloped in this app. Moving toward these signals requires no architectural change; every gap can be closed by editing `styles.py`, `appearance_panel.py`, and the status bar idiom.

---

## 2. Pattern Candidates

### P-01 — Named color-map preset menu

**Pattern name:** Color-map preset dropdown paired with swatch picker  
**Source app/platform:** ParaView (Color Map Editor panel)  
**Public evidence:** https://docs.paraview.org/en/latest/ReferenceManual/colorMapping.html  
**What makes it good:** ParaView's Color Map Editor surfaces a combo box at the top of the editor that lets the user instantly apply named presets (Cool-to-Warm, Viridis, Plasma, Inferno, Rainbow, Grey, Cold-and-Hot, and others accessible via a "Favorites" preset manager dialog). The user sees a small colored gradient swatch in the dropdown row, selects a name, and the surface updates immediately — no raw RGB entry required. For a math-research audience this is pedagogically meaningful: "Viridis" is the standard perceptually-uniform choice for numeric data, "Cool-to-Warm" is the standard diverging choice. These are vocabulary the target audience shares, and surfacing them by name removes the need to hand-tune RGB for a good result.  
**Interaction-vocabulary primitives:** `[INT-43 swatch-color-picker]` extended with a `QComboBox` preset selector above it; each preset could apply a `pyvista` named colormap (Viridis, Inferno, Plasma, Cool-to-Warm, Magma, Rainbow, Greyscale) instead of a flat color.  
**Where it fits in the app:** `appearance_panel.py:_build_color_group()` — currently lines 115–142 build a flat-color swatch + picker button. A second "Color map" group (or extension of the existing Colors group) would house the preset combo plus a "Use colormap" checkbox. When checked, PyVista's `add_mesh(cmap=...)` is used instead of `color=`.  
**App positioning:** Appearance dock.  
**App-invariant check:** Respects AI-1 (PyVista add_mesh cmap kwarg is native); AI-13 requires 6-digit hex only for flat `color=` — colormap names are strings so no conflict.

---

### P-02 — Dark-mode canvas with deep-navy viewport palette

**Pattern name:** Deep-navy / off-black canvas palette ("math-research dark")  
**Source app/platform:** Manim Community (visual identity), 3Blue1Brown (lesson page palette), Quanta Magazine (figure ground colors)  
**Public evidence:**  
- https://www.manim.community/ (dark background, vibrant surface colors on near-black ground)  
- https://www.3blue1brown.com/ (white/near-white site on lesson pages but iconic deep-navy video frames)  
- https://www.quantamagazine.org/ (minimal white editorial ground with high-contrast figures)  
**What makes it good:** The canonical Manim video frame is near-black (`#1C1C2E`, deep navy) with high-saturation surface geometry — this is the visual grammar that the app's audience (Quanta readers, 3B1B viewers, math-curious researchers) has internalized for "this is a serious mathematical visualization." The app's current dark grey default background (`#2f2f2f` in `appearance_panel.py:self._bg_color`) is close but untuned: it sits between "dark app chrome" and "display background" without committing to either. A deliberate dark-mode palette — deep navy `#0a0e1a` viewport background, charcoal dock chrome `#1e222e`, muted-blue text `#a8b4c8` — would snap the app visually into the same family as Manim and make surface colors read more vividly. This is a pure palette delta, not an architectural change.  
**Interaction-vocabulary primitives:** `[INT-94 dark-mode-stylesheet]` (already identified as underdeveloped candidate); pairs with `[INT-80 solid-color-bg]` / `[INT-81 gradient-bg]` for the viewport background.  
**Where it fits in the app:** `styles.py` — add a parallel `STYLESHEET_DARK` with dark palette constants; `appearance_panel.py` — update default `self._bg_color = QColor("#0a0e1a")` and default surface color to a vivid accent (cobalt `#4a90d9` or Manim-esque teal `#58c4dd`); `app.py:main()` — accept `--dark` flag or a `QSettings`-driven toggle.  
**App positioning:** Global (all docks + viewport) — this is a theme-level change.  
**App-invariant check:** No conflict with AI-1 through AI-15. The existing `COLOR_MUTED` / `COLOR_VALUE` constants would gain dark counterparts; WCAG AA must be verified for new tokens (target ≥ 4.5:1 on dark chrome). Dark-mode is explicitly noted as a convention (not an invariant) in design-system.md §2.

---

### P-03 — Collapsible panel sections

**Pattern name:** Collapsible QGroupBox / QCollapsible sections in docks  
**Source app/platform:** superqt (`QCollapsible` widget, BSD-3-Clause), Blender (N-panel collapsible categories)  
**Public evidence:** https://pyapp-kit.github.io/superqt/ (documents `QCollapsible`)  
**What makes it good:** The Appearance dock currently exposes four `QGroupBox` sections (Colors, Display, Opacity, Shading) at all times. When the user is focusing on parameter exploration, these groups compete for attention. superqt's `QCollapsible` adds a disclosure-arrow header; clicking toggles the content. Blender's properties panel uses exactly this pattern: all categories are collapsed by default except the one most recently expanded. For a math-research user who has set up their preferred appearance and wants to focus on parameter space, collapsing the Appearance dock to just the "Colors" header reduces the panel height dramatically. This is additive — no existing functionality is removed, only made dismissible.  
**Interaction-vocabulary primitives:** `[INT-45 dock-header-tinted]` (headers already styled); `[INT-6 dock-floatable]` — collapsible groups preserve floatability.  
**Where it fits in the app:** `appearance_panel.py:_build_ui()` (line 87) — replace the four `QGroupBox` widgets with `QCollapsible` containers wrapping the same content. Also applicable to `view_panel.py:_build_ui()` (line 67), where View Presets, Camera, Clip Region, Scene Aids, and Export are five always-visible groups.  
**App positioning:** Appearance dock; View dock.  
**App-invariant check:** `QCollapsible` is from superqt (BSD-3-Clause) — compatible license. No AI conflict.

---

### P-04 — Per-variety color template presets

**Pattern name:** Per-variety default surface color palette ("variety-family color tokens")  
**Source app/platform:** GeoGebra 3D (color-coded object hierarchy); 3D Slicer (named color lookup tables per data type: FreeSurfer, PET-Heat, WarmShade, etc.)  
**Public evidence:** https://slicer.readthedocs.io/en/latest/user_guide/modules/colors.html (3D Slicer color module, lists named presets per modality)  
**What makes it good:** 3D Slicer organizes ~30 named color tables into semantic groups (imaging modality, anatomical use) so users never stare at a generic blue surface wondering if the color is meaningful. The algebraic variety app has an equivalent semantic grouping: K3 surfaces (complex-geometry heritage, cool slate tones), Enriques surfaces (classical 19th-century algebraic geometry, warm amber), Calabi–Yau 3-folds (the iconic Hanson cobalt-blue), Fano 3-folds (a newer family with no established palette — good candidate for a bold accent). Shipping default per-family palette tokens costs one dictionary in `styles.py` and three lines in `appearance_panel.py:apply_to_actor()`. The user would still be free to override via the color picker, but first-launch would be immediately more visually communicative.  
**Interaction-vocabulary primitives:** `[INT-96 palette-template-per-variety]` (already identified in INT vocabulary as a candidate); `[INT-43 swatch-color-picker]` for user override.  
**Where it fits in the app:** `styles.py` — new dict `VARIETY_DEFAULT_COLOR = {"K3 surface": "#8ab4d4", "Enriques surface": "#d4a574", "Calabi–Yau 3-fold": "#4a90d9", "Fano 3-fold (ρ=1)": "#7ec8a0"}` (tokens, not hard-codes); `app.py:_on_subtype_changed()` (line 219) or `appearance_panel.py:apply_to_actor()` — apply variety family color as the initial surface color when a new variety is selected.  
**App positioning:** Appearance dock + top control bar wiring.  
**App-invariant check:** Colors flowing to PyVista must be 6-digit hex (AI-13) — the proposed tokens above are 7-char 6-digit hex, compliant.

---

### P-05 — Parameter sweep / animation timeline

**Pattern name:** Keyframe-driven parameter sweep with timeline slider  
**Source app/platform:** ParaView (Time Manager / Animation panel)  
**Public evidence:** https://docs.paraview.org/en/latest/UsersGuide/animation.html (Time Manager, keyframe dialog, parameter track system)  
**What makes it good:** ParaView's Animation panel reduces a parameter sweep to three steps: (1) add a track for a source property, (2) enter two keyframes (min value at t=0, max value at t=1), (3) hit Play — the timeline slider then smoothly sweeps the parameter and the viewport updates. For the algebraic variety app, the equivalent is a "Sweep" button beside each slider that animates the parameter from its minimum to its maximum over N seconds with periodic off-screen snapshots. The Dwork ψ sweep through the conifold singularity (ψ approaching 1) and the Hanson dwell-time animation are the two iconic demos this would enable. Note: a simplified version (no full timeline UI, just a Play button + speed spinner) is sufficient for V1 and avoids the full ParaView complexity.  
**Interaction-vocabulary primitives:** `[INT-90 parameter-sweep-animation]` (explicitly flagged as aspirational in INT vocabulary); `[INT-3 busy-cursor]` during the sweep; `[INT-2 slider-release-render]` policy governs each step.  
**Where it fits in the app:** `parameters_panel.py:_build_row()` (line 126) — add a small "▶" play button beside each slider row; clicking it triggers a sweep coroutine. A global "Sweep speed" control (1×, 2×, 0.5×) in the same panel.  
**App positioning:** Parameters dock.  
**App-invariant check:** Respects INT-NO-1 (real-time render during drag is forbidden — sweep fires per-keyframe, not on `valueChanged`); respects AI-9 (`self._computing` guard must wrap each sweep step).

---

### P-06 — Spinbox companion for exact parameter entry

**Pattern name:** `QDoubleSpinBox` + slider pairing for exact value entry  
**Source app/platform:** ParaView Properties panel (numeric spinboxes beside every numeric slider); GeoGebra 3D (direct value editing in algebra panel)  
**Public evidence:** https://docs.paraview.org/en/latest/UsersGuide/introduction.html (Properties panel — "Display properties" — sliders are accompanied by direct numeric input fields)  
**What makes it good:** ParaView places a text-edit spinbox alongside every slider so users can type `1.0001` directly instead of dragging to a specific tick. For this app, the most compelling use case is the Dwork ψ parameter: ψ = 1.0 is the conifold singularity, and the slider's discrete step (0.05 or 0.1) can never reach it exactly. A `QDoubleSpinBox` beside the slider lets the researcher probe exact values — essential for the "boundary effects" description in `ParamSpec`. The spinbox fires `editingFinished` → triggers the same render path as `sliderReleased`, respecting INT-2.  
**Interaction-vocabulary primitives:** `[INT-97 parameter-spin-box-alternative]` (explicitly in INT vocabulary); `[INT-2 slider-release-render]` (spinbox `editingFinished` maps to the same release trigger).  
**Where it fits in the app:** `parameters_panel.py:_build_row()` (line 126) — replace the `value_lbl` (read-only `QLabel`) on the right of the header row with a `QDoubleSpinBox` that both displays the current value and accepts typed input; the slider and spinbox stay in sync via bidirectional signals.  
**App positioning:** Parameters dock.  
**App-invariant check:** No AI conflicts. Respects INT-NO-1 (spinbox `editingFinished` fires on Enter/tab-out, not on every keystroke).

---

### P-07 — Inline data-probe / coordinate readout in status bar

**Pattern name:** Real-time coordinate + mesh-stat readout in status bar  
**Source app/platform:** 3D Slicer (Data Probe widget: coordinate + voxel value per cursor position); ParaView (status bar: current operation + selection info)  
**Public evidence:** https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html (Data Probe widget — shows RAS coordinates, voxel values, layer names on mouse hover)  
**What makes it good:** 3D Slicer's Data Probe shows live data at the mouse cursor — anatomical coordinates, the underlying value, the layer name — without any modal dialog. For an algebraic variety viewer this maps naturally: on mouse hover over the surface, the status bar could show the approximate (x, y, z) coordinate of the surface point nearest the cursor. This closes a real researcher need: "is this singularity near the origin?" or "what is the actual coordinate of this node?". The implementation uses VTK's cell/point picker which is already available via the `QtInteractor`. Even without hover (which adds event complexity), upgrading the post-render status bar to show `min/max extent ±a` alongside the vertex/face count would be a meaningful delta.  
**Interaction-vocabulary primitives:** `[INT-4 status-bar-feedback]` (status bar already used — this extends it with geometry metadata); `[INT-70 status-warning-prefix]` / `[INT-71 status-value-error]` (existing warning/error patterns are preserved, coordinate data appended in normal state).  
**Where it fits in the app:** `app.py:_render_current()` (line 266) — the status bar message (line 330) already reports vertex/face count and parameter values; extend it with mesh bounding box extents (`mesh.bounds` → `±x, ±y, ±z`). A full hover-picker upgrade would be wired at `app.py` level after `plotter` construction.  
**App positioning:** Status bar.  
**App-invariant check:** Respects AI-9 (no re-entrant `processEvents` in the hover handler — use VTK's `AddObserver("MouseMoveEvent", ...)` without calling `processEvents`).

---

### P-08 — Viewport split for side-by-side surface comparison

**Pattern name:** Horizontal viewport split for two simultaneous surfaces  
**Source app/platform:** ParaView (Split View controls top-right corner — vertical or horizontal split; views can be repositioned via drag); 3D Slicer (linked view groups with eye-icon visibility toggles)  
**Public evidence:** https://docs.paraview.org/en/latest/UsersGuide/displayingData.html (Multiple Views section — "Split View controls at the top-right corner"; views swap positions via "click and drag" on title bars)  
**What makes it good:** ParaView's split-view reduces to three clicks: split-horizontal button, choose new view type, drag to reorder. Each view has its own camera but views can be linked (synchronized rotation). For algebraic varieties the canonical use case is K3 Fermat quartic ↔ Kummer surface comparison (both come from the same family, and the difference in singularity structure is visually obvious side-by-side). A simplified V1 — just a horizontal split into two `QtInteractor` instances, each with its own dropdown — maps cleanly onto the existing architecture without a full pipeline-browser refactor.  
**Interaction-vocabulary primitives:** `[INT-91 side-by-side-comparison-mode]` (explicitly aspirational in INT vocabulary); `[INT-20 vtk-trackball-rotate]` in each viewport independently; `[INT-23 camera-preset-fire-and-render]` must call `render()` on the active viewport only.  
**Where it fits in the app:** `app.py` — net-new surface; `central` widget would become a `QSplitter` containing two `QtInteractor` instances. The top control bar would grow a second "Variety B / Model B" row, or a tabbed switcher (View A / View B).  
**App positioning:** Central viewport; top control bar.  
**App-invariant check:** AI-1 allows multiple `QtInteractor` instances; AI-9 (`self._computing`) guard must extend to a per-viewport flag. This is the largest scope item in this brief — appropriate for a separate phase deliverable.

---

### P-09 — Help menu with variety citations and keyboard shortcut reference

**Pattern name:** Menu bar "Help" with About dialog + shortcut cheat-sheet  
**Source app/platform:** VS Code (Help menu → Keyboard Shortcuts reference); JetBrains IDEs (Help → Find Action `Ctrl+Shift+A`); MeshLab (Help → About with citation)  
**Public evidence:** https://code.visualstudio.com/ (VS Code keyboard shortcut PDF linked from Help menu — a canonical reference); https://www.jetbrains.com/ (Settings search via `Ctrl+Shift+A`)  
**What makes it good:** The app currently has no menu bar. All citations and keyboard shortcuts live only in tooltips, which are invisible unless the user hovers. A minimal menu bar (`File > Screenshot… | Help > Keyboard Shortcuts | Help > About / Citations`) would cost ~30 lines and deliver two things the research audience needs: (1) a stable place to credit the math sources (COGITO, Hanson 1994, Imaginary.org SURFER) and (2) a discoverability surface for keyboard shortcuts. The JetBrains approach — "Find Action" search — is too heavy for this app, but a static two-column shortcut dialog (action | key) is exactly right.  
**Interaction-vocabulary primitives:** `[INT-98 help-menu-with-citations]` (explicitly aspirational in INT vocabulary); `[INT-5 keyboard-shortcut]` (extending the existing 3-shortcut surface).  
**Where it fits in the app:** `app.py` — net-new `QMenuBar`; `MainWindow.__init__()` gets `self.setMenuBar(...)` after dock setup. The "Screenshot…" action in File duplicates `view_panel._on_screenshot()` for discoverability.  
**App positioning:** Menu bar (net-new).  
**App-invariant check:** No AI conflicts. Adding a menu bar does not affect VTK rendering or the re-entrancy guard.

---

### P-10 — KaTeX-rendered equation tooltip popover

**Pattern name:** Floating KaTeX math-rendered equation display on variety/model hover  
**Source app/platform:** Mathematica Manipulate UI (equations rendered as proper LaTeX in panel labels); GeoGebra 3D (MathQuill / KaTeX in input bar)  
**Public evidence:** https://katex.org/ (MIT license, browser-side TeX rendering); https://www.geogebra.org/3d (equation bar renders LaTeX glyphs)  
**What makes it good:** The app currently renders equations as plain-text unicode in `QToolTip` strings (e.g. `x⁴+y⁴+z⁴-1=0`). Unicode super/subscripts render inconsistently across platforms — on Windows the default `QToolTip` font may not support combining modifiers. A `QtWebEngineView`-based KaTeX popover (shown on a 500ms hover dwell) would render `x^4+y^4+z^4=1` as proper math typography, signaling to the research audience that the tool takes the equations seriously. The `VARIETY_TOOLTIPS` / `SUBTYPE_TOOLTIPS` dicts in `surfaces.py` already contain the equation strings — the popover just needs a KaTeX renderer and a thin overlay widget.  
**Interaction-vocabulary primitives:** `[INT-95 katex-tooltip-popover]` (explicitly aspirational in INT vocabulary); `[INT-7 tooltip-rich]` (existing tooltip strings become the KaTeX input).  
**Where it fits in the app:** `app.py:variety_combo` and `subtype_combo` (lines 53, 69) — add a `enterEvent` handler or a custom `QAbstractItemDelegate` that shows a `QDialog` with a `QWebEngineView` rendering the KaTeX string. Alternatively, a simpler approach: use `matplotlib`'s mathtext renderer (`matplotlib.mathtext`) to generate a PNG and embed it in the tooltip as an `<img>` via `QToolTip`'s rich-text support — this avoids `QtWebEngineWidgets` overhead.  
**App positioning:** Top control bar (variety dropdown / model dropdown tooltips).  
**App-invariant check:** `matplotlib` is permitted for mathtext rendering (design-system.md notes `matplotlib-mathtext` as a candidate for "rendered equation tooltips") — it is specifically NOT forbidden, only `mpl_toolkits.mplot3d` for 3D rendering is forbidden (AI-1). `QtWebEngineWidgets` is a heavier dependency but adds no architectural conflict.

---

### P-11 — State persistence via QSettings

**Pattern name:** Cross-launch state persistence (last variety, slider values, dock geometry)  
**Source app/platform:** JetBrains IDEs (full workspace state restore including open files, window layout); VS Code (workspace-level settings); Blender (startup file stores last workspace layout)  
**Public evidence:** https://doc.qt.io/qtforpython-6/PySide6/QtCore/QSettings.html (PySide6 built-in; no external dep)  
**What makes it good:** Every peer app listed in the source registry persists state: Blender saves the last workspace to a startup `.blend` file, JetBrains IDEs remember every open file and panel size. The algebraic variety app currently opens to `— Select —` on every launch. For a researcher who spends two weeks exploring the Hanson quintic, re-selecting the variety and re-setting sliders on every launch is friction. `QSettings` is a PySide6 built-in (zero new deps), and the design-system.md §6 notes this was "considered but skipped" — it is explicitly RECONSIDERABLE. The minimal useful form: persist `(last_variety, last_model, last_param_values, dock_geometry)` and restore on next launch with a "Restore last session" status-bar message.  
**Interaction-vocabulary primitives:** `[INT-92 state-persistence-qsettings]` (explicitly aspirational); `[INT-4 status-bar-feedback]` for the restore confirmation message.  
**Where it fits in the app:** `app.py:closeEvent()` (line 419) — save state; `MainWindow.__init__()` (line 38) — restore state after UI construction. No new files needed.  
**App positioning:** App lifecycle (save/restore in `MainWindow`).  
**App-invariant check:** No AI conflicts. Design-system.md §6 explicitly marks this as RECONSIDERABLE.

---

### P-12 — Mesh export button (STL / OBJ / PLY)

**Pattern name:** One-click mesh export from the View/Export group  
**Source app/platform:** MeshLab (File > Export Mesh — all common formats); Blender (File > Export); ParaView (File > Export Scene)  
**Public evidence:** https://www.meshlab.net/ (export to STL/OBJ/PLY is a headline feature); https://docs.pyvista.org/ (`mesh.save()` supports `.stl`, `.obj`, `.ply`, `.vtk`)  
**What makes it good:** MeshLab, Blender, and ParaView all treat mesh export as a first-class action. For the algebraic variety app, researchers regularly want to import a K3 surface or Enriques surface into Blender, Meshmixer, or 3D printing software. The implementation is a single `mesh.save(path)` call (PyVista built-in) — design-system.md §7 explicitly flags this as UNDERDEVELOPED with the note "one-line addition." The only UX decision is where to surface it: extending the existing `Export` group in `view_panel.py` (lines 246–255) to include "Export Mesh…" beside "Screenshot…" is the minimal delta.  
**Interaction-vocabulary primitives:** `[INT-93 mesh-export-button]` (explicitly aspirational); `[INT-61 screenshot-png-save]` (same `QFileDialog` pattern).  
**Where it fits in the app:** `view_panel.py:_make_screenshot_group()` (line 246) — rename to "Export" (it already uses that name), add `QPushButton("Export mesh…")` wired to a `QFileDialog.getSaveFileName` with filter `"STL (*.stl);;OBJ (*.obj);;PLY (*.ply)"`, then `self._raw_mesh.save(path)`. The `_raw_mesh` reference is on `MainWindow` — use a callback pattern matching `get_actor` / `get_plotter` lambdas.  
**App positioning:** View dock (Export group).  
**App-invariant check:** PyVista `mesh.save()` is MIT and already a transitive dep. No AI conflicts.

---

## 3. Sources Reviewed

| App / Platform | URL | What was read | High-signal? |
|---|---|---|---|
| ParaView | https://docs.paraview.org/en/latest/UsersGuide/introduction.html | Dock organization, pipeline browser, Properties panel, status bar, toolbar patterns | Yes |
| ParaView | https://docs.paraview.org/en/latest/UsersGuide/displayingData.html | Multiple views (split-view controls), color mapping (scalar coloring, transfer function) | Yes |
| ParaView | https://docs.paraview.org/en/latest/UsersGuide/animation.html | Time Manager, keyframe animation, parameter sweep interaction model | Yes |
| ParaView | https://docs.paraview.org/en/latest/ReferenceManual/colorMapping.html | Color Map Editor detail: combo-box preset selector, "Favorites" dialog, transfer-function editor, scalar bar configuration | Yes |
| 3D Slicer | https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html | Module switcher, Data Probe widget, status bar pattern, subject hierarchy tree | Yes |
| 3D Slicer | https://slicer.readthedocs.io/en/latest/user_guide/modules/colors.html | Named color presets (FullRainbow, Grey, WarmShade/CoolShade, PET-Heat, FreeSurfer tables, 30+ entries) with dropdown selection | Yes |
| Surfer / Imaginary.org | https://imaginary.org/program/surfer | Page describes equation entry and gallery concept; no UI screenshots embedded; no manual PDF reachable at tried path | Partial |
| GeoGebra 3D | https://www.geogebra.org/3d | Toolbar hierarchy, math notation input, visual separation of structural vs. mathematical controls | Yes |
| Mathematica Manipulate | https://reference.wolfram.com/language/ref/Manipulate.html | 403 Forbidden — not retrievable | No (blocked) |
| Maple 3D plotter | https://www.maplesoft.com/support/help/maple/view.aspx?path=plot3d/option | Style options: surface/wireframe/contour/point; shading: xy/xyz/z/zhue; lightmodel: light1–light4; glossiness | Yes |
| MeshLab | https://www.meshlab.net/ | Homepage only — no UI pattern detail; export formats confirmed as headline feature | Partial |
| Blender | https://docs.blender.org/manual/en/latest/interface/window_system/workspaces.html | 403 Forbidden | No (blocked) |
| superqt | https://pyapp-kit.github.io/superqt/ | `QCollapsible`, `QRangeSlider`, throttle/debounce utilities; BSD-3-Clause confirmed | Yes |
| qtawesome | https://github.com/spyder-ide/qtawesome | 6 icon sets (FontAwesome, Material Design, Phosphor, Remix, Codicons); MIT license | Yes |
| Quanta Magazine | https://www.quantamagazine.org/ | Clean white + dark-text editorial palette; sans-serif; all-caps category tags; large hero images | Yes |
| Manim Community | https://www.manim.community/ | Vibrant palette on near-black background; LaTeX via `MathTex()`; animation as pedagogy reference | Yes |
| 3Blue1Brown | https://www.3blue1brown.com/ | White/near-white site; deep-navy video frames; clean card layout for lessons | Yes |
| Stripe Press | https://press.stripe.com/ | Restrained black-on-white editorial; credibility through minimalism; technical rigor through sparse design | Yes |
| VisIt | https://visit-dav.github.io/visit-website/ | Homepage only — no UI pattern detail accessible from homepage | No |
| KAlgebra | https://apps.kde.org/kalgebra/ | Page confirms console + 2D/3D plot; no UI detail | No |
| VS Code | https://code.visualstudio.com/ | Help menu pattern, keyboard shortcut reference approach (noted as design reference) | Partial |

---

## 4. Themes

**Theme 1 — Color-map preset menus are universal in VTK-based peers.** ParaView, 3D Slicer, and VisIt all surface named color-map presets (dropdown or dialog) alongside raw color pickers. The algebraic variety app has only a bare `QColorDialog` — a single widget swap from `appearance_panel.py:_build_color_group()` closes the gap. The named maps used across peers (Viridis, Plasma, Inferno, Cool-to-Warm, Rainbow, Grey) are all available as PyVista `cmap=` strings.

**Theme 2 — The math-research visual identity converges on dark, low-luminance canvas.** Manim, 3Blue1Brown, and the broader Quanta editorial aesthetic all point toward a deep-navy or off-black background against which surface colors are vivid and saturated. The app's current `#2f2f2f` default background is unstyled dark-grey, not deliberately deep-navy. Tuning three hex values in `styles.py` and `appearance_panel.py` would align the app with the visual grammar its audience already recognizes.

**Theme 3 — Dense parameter panels across peers use spinboxes, not read-only labels.** ParaView, GeoGebra 3D, and Maple's interactive plot builder all allow exact numeric entry alongside sliders. The app uses a read-only `QLabel` for the current value display — replacing it with a `QDoubleSpinBox` is the single highest-leverage change to the Parameters dock and costs ~10 lines.

**Theme 4 — State persistence and export are the two most universal research-workflow features that this app lacks.** Every peer tool (ParaView, 3D Slicer, MeshLab, Blender) persists session state and exports geometry. Both are explicitly flagged as UNDERDEVELOPED in design-system.md §7. They are also the two lowest-implementation-cost items: `QSettings` is a PySide6 built-in, and `mesh.save()` is a single PyVista call.

---

## 5. Cross-Reference to App

| Pattern | App location (file:line) or Net-new | Gap vs. today |
|---|---|---|
| P-01 Color-map preset menu | `appearance_panel.py:_build_color_group()` lines 115–142 | App has only flat color picker; no preset names, no colormap mode |
| P-02 Dark-mode canvas palette | `styles.py` (palette constants); `appearance_panel.py:__init__()` line 76 (`self._bg_color`) | Background default `#2f2f2f` is unstyled; no dark QSS variant exists |
| P-03 Collapsible panel sections | `appearance_panel.py:_build_ui()` line 87; `view_panel.py:_build_ui()` line 67 | All groups always visible; no disclosure affordance |
| P-04 Per-variety color templates | `styles.py` (new `VARIETY_DEFAULT_COLOR` dict); `app.py:_on_subtype_changed()` line 219 | All varieties share same `#b0c4de` default surface color |
| P-05 Parameter sweep | `parameters_panel.py:_build_row()` line 126 | No play/sweep control exists |
| P-06 Spinbox companion | `parameters_panel.py:_build_row()` line 140 (`value_lbl = QLabel(...)`) | Value display is read-only `QLabel`; no exact entry |
| P-07 Coordinate readout | `app.py:_render_current()` line 326 (status bar message) | Shows vertex/face count but not mesh bounding extents |
| P-08 Split viewport | `app.py:MainWindow.__init__()` line 78 (single `QtInteractor`) | Net-new; no split-view infrastructure today |
| P-09 Help menu / citations | `app.py:MainWindow.__init__()` — no `QMenuBar` exists | Net-new; no menu bar at all |
| P-10 KaTeX equation tooltip | `app.py:variety_combo` line 53; `subtype_combo` line 69 (tooltip strings) | Tooltips are plain-text unicode; no rendered math |
| P-11 State persistence | `app.py:closeEvent()` line 419 | No `QSettings` save/restore |
| P-12 Mesh export | `view_panel.py:_make_screenshot_group()` line 246 | Screenshot only; no mesh export action |

---

## 6. Out of Scope / Parking Lot

| Pattern | Reason not surfaced |
|---|---|
| Full ParaView pipeline browser (source/filter tree) | Way out of scope — the app has one surface at a time, not a multi-source pipeline |
| 3D Slicer subject-hierarchy tree | Same: single-mesh app; DICOM-oriented tree is not applicable |
| Blender workspace tabs (multiple named workspaces) | Overcomplicated for an app with 3 docks; the equivalent is dock-state persistence (P-11) |
| VisIt expression editor | The app uses `ParamSpec` for all inputs; an expression editor would require a symbolic math parser (SymPy) — out of scope for panel-refresh |
| Maple shading: `zhue` / `xyz` gradient coloring by coordinate | Interesting but requires adding a scalar field per vertex (x, y, or z value) as coloring data — outside panel-refresh scope; would interact with AI-6 (scalar field handling) |
| ParaView "Auto Apply" toggle | The app already has a better default (render on slider release only, INT-2); an explicit auto-apply toggle would be regressive |
| Animated camera fly-through path | ParaView supports this via keyframe camera animation; too complex for panel-refresh, should be a separate task |
| `distill.pub` interactive figure pattern | Distill is archived (2021); the interactive-figure paradigm requires WebAssembly / JS — not applicable to a Qt desktop app |
| Inkscape/Krita customizable toolbar | Toolbar customization (drag-to-add icons) requires a full toolbar action system; the app has no toolbar today — too large for panel-refresh |
| JetBrains "Find Action" command palette | The app has 3 shortcuts; a command palette is appropriate when shortcuts exceed ~20; parking for later |
| First-launch auto-render of a default surface | Rejected in CONTEXT.md §9 as "presumptuous in a research tool"; not re-proposed |
| Confirmation dialog on Reset to Defaults | Explicitly rejected (INT-NO-9); not re-proposed |
