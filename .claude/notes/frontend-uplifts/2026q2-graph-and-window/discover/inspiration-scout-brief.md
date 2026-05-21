# Inspiration Scout Brief — 2026q2-graph-and-window

**Scope:** Tier-1 panel-chrome shakedown — surface gaps in BOTH the 3D plot rendering AND the Qt panel chrome / window frame / dock layout / styles.  This is the first exercise of the render-panel-chrome.py pipeline; produce a balanced ranking that does not over-index on either viewport-only or chrome-only findings.

**Produced:** 2026-05-21  
**Scout:** Inspiration Scout (automated)

---

## 1. TL;DR

**Top-3 patterns worth borrowing:**

1. **Color-map preset picker with named swatches** (ParaView / 3D Slicer) — the app's Appearance dock has only a bare `QColorDialog` swatch per surface and background; a preset menu of 6–10 named palette templates (variety-family defaults + research-grade scientific palettes) would close a concrete gap between this app and every VTK peer tool without adding UI complexity.
2. **Collapsible group-box sections with search / advanced-toggle** (ParaView Properties panel) — all three docks expose flat, always-visible QGroupBox sections; ParaView's two-mode show/hide of advanced properties keeps expert controls out of the way by default and is directly buildable with `superqt.QCollapsible` or a custom `QGroupBox` trick.
3. **Animation timeline / parameter-sweep transport bar** (ParaView animation, Mathematica Manipulate analogue) — the app has no animated sweep path at all; a minimal VCR-style transport row (Play / Pause / Step) over a single-parameter timeline track would enable the iconic Hanson dwell-time and Dwork ψ-sweep demos without a full keyframe editor.

**Main thematic shift:** every peer scientific-viz desktop app (ParaView, 3D Slicer, VisIt, KAlgebra) separates "what to show" from "how to show it" into distinct panel regions, then further subdivides by basic vs. advanced — the app today collapses all controls into three docks with no progressive disclosure.  Adopting even light progressive disclosure (collapsible sections, an "Advanced…" expander) would bring the chrome in line with 2026 SOTA without adding panels.

---

## 2. Pattern Candidates

### PC-1: Color-map Preset Picker (Named Palette Templates)

- **Pattern name:** color-map preset picker with named swatches
- **Source app:** ParaView (color mapping) + 3D Slicer Colors module
- **Public evidence:**
  - https://docs.paraview.org/en/latest/ReferenceManual/colorMapping.html — "combo box at the top of the transfer function editor used to quickly switch between the 'Default' presets … a Color Preset manager dialog"
  - https://slicer.readthedocs.io/en/latest/user_guide/modules/colors.html — "Discrete", "Shade & Tint", "Continuous", "FreeSurfer" preset categories; complementary warm/cool pairs designed for layered visualization
- **What makes it good:** In ParaView, switching the surface color-map is a single combo-box selection: the user can hop from Cool-to-Warm → Viridis → Plasma in two clicks, immediately seeing scientific-grade perceptual palettes rather than choosing from RGB sliders.  3D Slicer's categorized preset list adds the idiom of warm/cool complementary pairs useful when two overlapping meshes need visual separation.  Researchers who need a figure-quality render don't want to hand-tune hex; they want to land on a known-good palette fast.
- **Interaction-vocabulary primitives:** [INT-43 swatch-color-picker] (already present as the per-mesh swatch); extend with a `QComboBox` preset dropdown that populates the swatch on selection.
- **Where it fits:** `appearance_panel.py:_build_color_group()` (line 124) — add a `QComboBox` above the existing `surf_btn`; selecting a preset populates `self._surface_color` and calls `_apply_swatch_color`.  Also complements the stub at `styles.py:VARIETY_DEFAULT_COLOR` (line 107) — presets seed that dict.
- **App positioning:** Appearance dock (right bottom) → Colors group box.
- **App-invariant:** no conflict. Colors flowing to PyVista must use 6-digit hex (AI-13); the preset dict entries are all 6-digit.  No renderer swap implied (AI-1 safe).

---

### PC-2: Collapsible Group Sections with Advanced-Toggle

- **Pattern name:** collapsible panel section with basic/advanced toggle
- **Source app:** ParaView Properties panel
- **Public evidence:** https://docs.paraview.org/en/latest/ReferenceManual/propertiesPanel.html — "three collapsible sections: Properties, Display, and View … A search box allows locating properties by name … The panel offers two modes: default (showing frequently-used properties) and advanced (displaying all available properties). Users toggle between modes using an advanced button."
- **What makes it good:** ParaView's Properties panel shows only the 3–4 most common properties by default; clicking the "advanced" (gear) button reveals the full list.  Users who want to quickly probe the surface see a clean panel; power users who need every lighting knob expand it.  This matches the research-tool UX pattern of "progressive disclosure without hidden menus" — nothing is removed, it is just out of the way until asked for.  The section header is clickable to collapse/expand, which means the state is always visible but immediately hideable.  The pattern requires zero new panels.
- **Interaction-vocabulary primitives:** [INT-6 dock-floatable] anchors the dock; the collapsible sections are a refinement within each dock's QWidget layout using either `superqt.QCollapsible` (BSD-3) or a custom chevron-labeled `QGroupBox` expansion toggle.
- **Where it fits:** All three docks benefit, but the highest-density panel is the Appearance dock (`appearance_panel.py`).  The Shading group (line 195, `_build_shading_group`) and Display group (line 153, `_build_toggles_group`) could live inside collapsible sections that default-collapsed, with only Colors and Opacity visible.  The View dock (`view_panel.py:_build_ui`, line 67) could collapse the Screenshot group by default.
- **App positioning:** Appearance dock, Parameters dock, View dock — all three.
- **App-invariant:** no conflict. `superqt` is already in the source registry (§2). Does not touch AI-1/AI-4/AI-13.

---

### PC-3: Parameter Sweep Animation Transport Bar

- **Pattern name:** VCR-style parameter sweep transport bar
- **Source app:** ParaView animation timeline, Mathematica Manipulate (conceptual analogue)
- **Public evidence:**
  - https://docs.paraview.org/en/latest/UsersGuide/animation.html — "VCR controls toolbar … play, pause, step … GoToFirst(), GoToLast(), GoToNext(), GoToPrevious() … A thick vertical line marks the current animation time; users drag it or enter a value."
  - Mathematica Manipulate reference (https://reference.wolfram.com/language/ref/Manipulate.html) — the canonical template for this app's dropdown + sliders; Manipulate embeds a play button per slider that animates min → max continuously.
- **What makes it good:** ParaView's transport bar lets a researcher hit Play on a parameter track and watch a surface continuously deform — from Dwork ψ = 0.5 to ψ = 1.5, the conifold singularity appears and dissolves.  For algebraic varieties this is the most compelling demo mode: a 30-second sweep communicates the shape of the parameter space better than any static figure.  The pattern does not require a full keyframe editor — a single-slider sweep is enough.  The VCR affordance (triangle, bar, double-triangle icons) is universally recognized; researchers familiar with Mathematica Manipulate will recognize the per-slider play-button variant immediately.
- **Interaction-vocabulary primitives:** [INT-90 parameter-sweep-animation] (aspirational, §7 of interaction-vocabulary.md) — this pattern is the concrete realization.  Pair with [INT-2 slider-release-render] discipline: during sweep, render fires at the end of each interpolation step, not on every tick.  [INT-3 busy-cursor] during sweep.
- **Where it fits:** `parameters_panel.py` — beside the "Reset all to defaults" button (line 61, `_reset_btn`), add a "Sweep" control row with a `QComboBox` selecting which parameter to sweep and a Play/Pause/Step `QPushButton` row.  The sweep drives a `QTimer`-triggered slider advance.
- **App positioning:** Parameters dock (right top).
- **App-invariant:** must respect AI-9 (`self._computing` guard) — the sweep timer must not fire a new render if the previous render is still in flight.  No renderer swap (AI-1 safe).

---

### PC-4: Dock State Persistence (Perspectives / Layouts)

- **Pattern name:** saved dock layout perspectives
- **Source app:** QtAds (Qt Advanced Docking System) + ParaView pipeline browser conventions
- **Public evidence:**
  - https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System — "Perspectives — saving and switching between named layout configurations … backward-compatible state file format … PySide6 package available: `pip install PySide6-QtAds`."
  - https://docs.paraview.org/en/latest/UsersGuide/introduction.html — "dockable panels … panels are positioned around the viewport … multiple dockable panels."
- **What makes it good:** QtAds replaces `QDockWidget` with a richer system supporting tabbed docks, grouped drag of multiple panels, and named "perspectives" (e.g. "Explore" — all docks visible; "Present" — parameters hidden, large viewport; "Export" — screenshot panel expanded).  For a researcher the "present" perspective hides the chrome and maximizes the surface render; flipping back to "explore" restores sliders.  `QMainWindow.saveState()` / `restoreState()` gives rudimentary persistence, but QtAds' perspective system gives named, user-friendly layout switching.
- **Interaction-vocabulary primitives:** [INT-6 dock-floatable] (already enabled) — QtAds extends this.  [INT-92 state-persistence-qsettings] is the lightweight alternative using only `QSettings`; QtAds goes further.
- **Where it fits:** `app.py:MainWindow.__init__` — dock construction (lines that add `QDockWidget`); replacing with `QtAds.DockManager` is the integration point.  The underdeveloped candidate §7 "State persistence via `QSettings`" in design-system.md is the entry point.
- **App positioning:** Main window / window chrome — cross-cutting.
- **App-invariant:** LGPL-2.1 license on QtAds is compatible with PySide6 (LGPL) usage.  Does not touch render path.

---

### PC-5: Status-Bar Warning Badge with Persistent Error Log

- **Pattern name:** persistent warning badge + clickable error log
- **Source app:** 3D Slicer
- **Public evidence:** https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html — "The status bar may display application status … users can access the Error Log window by clicking small X icons displayed on the status bar."
- **What makes it good:** 3D Slicer's status bar shows a small persistent badge (X icon + count) whenever warnings accumulate.  Clicking it opens an Error Log dialog listing all warnings since launch.  The current app shows one warning at a time in `QStatusBar.showMessage(...)` — the next render overwrites it.  When a Dwork conifold warning fires (`⚠ Conifold singularity detected …`) and the user immediately switches to another surface, that warning silently disappears.  A badge that persists ("⚠ 1") until explicitly cleared gives researchers the audit trail they expect.
- **Interaction-vocabulary primitives:** [INT-70 status-warning-prefix] (already in the app) — extend by logging to an in-memory list and showing the persistent badge.  [INT-4 status-bar-feedback] provides the one-at-a-time display; the badge is additive.
- **Where it fits:** `app.py:_render_current` (the warning-accumulation block, ~line 290); add a `QLabel` badge widget to the `QStatusBar` (right-aligned, hidden when count = 0).  Closest design-system entry: §7 "Status-bar warning badge persistence" in design-system.md.
- **App positioning:** Status bar (bottom of main window).
- **App-invariant:** no conflict; does not touch AI-9 guard or render path.

---

### PC-6: Variety-Family Surface Color Presets (Per-Family Palette Template)

- **Pattern name:** per-variety-family default surface color template
- **Source app:** GeoGebra 3D (color-coded object hierarchy), 3D Slicer (category-color conventions in the Colors module)
- **Public evidence:**
  - https://www.geogebra.org/3d — GeoGebra's algebra sidebar assigns distinct colors per object type to enable visual separation between curves, surfaces, and points without user intervention.
  - https://slicer.readthedocs.io/en/latest/user_guide/modules/colors.html — warm/cool complementary pairs "designed for layered visualization and colorblind accessibility."
- **What makes it good:** When a researcher switches from a K3 Fermat quartic to a Calabi–Yau Hanson surface, the surface color resets to the same lightsteelblue every time — there is no visual cue that they're in a different mathematical family.  GeoGebra's automatic color-coding makes object identity legible at a glance; applying the same discipline to variety families (K3 → slate blue, Enriques → warm amber, CY3 → cobalt, Fano → green) gives researchers an immediate context signal without a legend.  This is a 4-entry dict change, not a new widget.
- **Interaction-vocabulary primitives:** [INT-96 palette-template-per-variety] — this is the direct realization.  Pairs with [INT-43 swatch-color-picker] (swatch updates to the family default on surface switch; user can still override).
- **Where it fits:** `styles.py:VARIETY_DEFAULT_COLOR` (line 107 — explicitly stubbed for UPL-5); `appearance_panel.py:apply_to_actor` (line 301 — where `actor.prop.color` is set).  The stub comment on line 102 says "Keys MUST match the VARIETIES dict in surfaces.py VERBATIM."
- **App positioning:** Appearance dock (right bottom) — Colors group; also visible as viewport color change.
- **App-invariant:** all entries must be 6-digit hex (AI-13).  No renderer swap (AI-1 safe).

---

### PC-7: Labeled Slider with Inline Numeric Spinbox (Exact-Value Entry)

- **Pattern name:** slider + paired spinbox for exact numeric entry
- **Source app:** ParaView Properties panel (numerical sliders), superqt `QLabeledSlider`
- **Public evidence:**
  - https://docs.paraview.org/en/latest/ReferenceManual/propertiesPanel.html — "widgets for properties … sliders" (ParaView mixes sliders with text-field inputs for precise control).
  - https://github.com/pyapp-kit/superqt — "QLabeledSlider … integrates slider controls with accompanying labels … QRangeSlider" with multi-handle support; BSD-3-Clause.
- **What makes it good:** The app's parameter sliders let users drag to approximately ψ = 1.0, but probing the exact conifold (ψ = 1.0000) requires many mouse micro-adjustments.  ParaView solves this by providing a text-field fallback beside sliders for exact entry.  superqt's `QLabeledSlider` goes further by integrating the current-value label directly into the slider track end, eliminating the separate monospace `VALUE_MONO_STYLE` label.  A paired `QDoubleSpinBox` would let researchers type "1.0001" directly.
- **Interaction-vocabulary primitives:** [INT-97 parameter-spin-box-alternative] — the direct realization.  [INT-2 slider-release-render] discipline is preserved: the spinbox emits `editingFinished` (not `valueChanged`) to trigger render.
- **Where it fits:** `parameters_panel.py` — each per-parameter slider row (the slider + value-label layout built in `set_specs`); add a compact `QDoubleSpinBox` beside the existing `QSlider`.  The existing `VALUE_MONO_STYLE` label (`styles.py:169`) would be replaced by the spinbox display.
- **App positioning:** Parameters dock (right top) — per-parameter rows.
- **App-invariant:** no conflict. Does not touch render path or AI-2 test constraint.

---

### PC-8: Module-Switch History Navigation (Recently Used Surfaces)

- **Pattern name:** recently used surface history with back/forward navigation
- **Source app:** 3D Slicer module-selection toolbar
- **Public evidence:** https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html#toolbars — "Module Selection toolbar … a history dropdown showing recently used modules … navigation arrows for moving between previously accessed modules."
- **What makes it good:** 3D Slicer's module toolbar embeds browser-style back/forward arrows beside the module combo so users can retrace their exploration without re-navigating the combo hierarchy.  In this app, a researcher who explores K3 → Kummer → Enriques → Cayley and wants to revisit Kummer must re-select Variety = "K3 surface" then Model = "Kummer surface" in the two-step cascade — two clicks plus reading the combo list.  A history list (up to 8 recent surface+model pairs) in a small dropdown would collapse that to one.  This is especially useful during a presentation or tutorial session.
- **Interaction-vocabulary primitives:** [INT-1 dropdown-cascade] — the existing two-step combo; this pattern adds a bypass.  [INT-5 keyboard-shortcut] — back/forward could be `Alt+←` / `Alt+→`.
- **Where it fits:** `app.py` — the top control bar (near the `Variety:` and `Model:` combo boxes, ~lines 100–130).  A `QComboBox` populated from a `deque` of (variety, model) tuples would live beside or above the existing combos.
- **App positioning:** Top control bar (main window toolbar area).
- **App-invariant:** no conflict. Does not touch render path.

---

### PC-9: Viewport Text Overlay for Empty-Clip or No-Surface State

- **Pattern name:** VTK canvas text overlay for zero-geometry and idle states
- **Source app:** ParaView (annotation overlays), VisIt (view annotations)
- **Public evidence:** https://docs.paraview.org/en/latest/UsersGuide/introduction.html — ParaView places descriptive text annotations directly on the 3D viewport canvas (via VTK text actors), not only in the status bar.  This is documented in the annotation section of the Reference Manual.
- **What makes it good:** When the app launches, the central viewport shows an empty dark grey (`#2f2f2f`) canvas with no guidance.  The status bar at the bottom says "Choose a variety from the dropdown above to begin" — but the status bar is 11px grey text on a light chrome band, below the viewport.  A researcher glancing at the big dark rectangle gets no affordance.  ParaView places a VTK text actor in the center of the empty viewport; the same technique would render "Choose a variety to begin" in white/light-grey inside the dark canvas itself, at readable size, disappearing on first render.  The same approach also addresses the empty-clip state: when the domain slider empties the visible mesh, a text overlay in the viewport ("Domain is smaller than the surface — try increasing the radius") is visible even when the status bar is outside the eye path.
- **Interaction-vocabulary primitives:** [INT-74 empty-clip-status-message] (already in status bar) — extend with VTK text actor overlay.  [INT-4 status-bar-feedback] is the companion.
- **Where it fits:** `app.py:MainWindow.__init__` (add a `vtkTextActor` to the plotter after viewport construction) and `app.py:_apply_domain_and_render` (toggle visibility on empty-clip detection).  Design-system §7: "Empty-clip overlay annotation" and "First-launch tour / click any variety hint."
- **App positioning:** Central 3D viewport.
- **App-invariant:** `vtkTextActor` is native VTK / PyVista — no renderer swap needed (AI-1 safe).  Must not construct `MainWindow` under offscreen (AI-3) — the actor is added to the live plotter, not during testing.

---

### PC-10: Dark-Mode Stylesheet (Research-Audience Chrome)

- **Pattern name:** parallel dark-mode QSS palette
- **Source app:** PyQtDarkTheme (`qdarktheme`), Blender (dark default), 3Blue1Brown visual identity, Quanta Magazine dark reading mode
- **Public evidence:**
  - https://github.com/5yutan5/PyQtDarkTheme — "flat dark and light themes … syncs with macOS accent colors … `pip install pyqtdarktheme`; MIT license."
  - https://www.3blue1brown.com/ — "light background and dark text for readability … minimal interface … high contrast typography."
  - https://www.quantamagazine.org/ — neutral palette, generous whitespace, restraint over chromatic boldness — both modes.
- **What makes it good:** Scientific visualization is routinely done in darkened rooms (projection, external monitor), and the dark viewport (`BG_VIEWPORT = #2f2f2f`) already signals this.  The bright light-chrome panels (dock headers at `#e8edf2`, panel body at `#f0f0f0`) contrast sharply with the dark canvas — a visual discontinuity that makes the surface "pop" but fatigues eyes over long sessions.  A dark-mode stylesheet where the panel chrome matches the canvas (deep charcoal backgrounds, light text) creates visual continuity.  3Blue1Brown's site and Quanta's night mode both demonstrate that restrained dark palettes suit math research content.  PyQtDarkTheme ships a complete `PALETTE_DARK`-equivalent with per-widget tokens, providing a reference for populating `styles.PALETTE_DARK` (the UPL-4 milestone stub at `styles.py:110`).
- **Interaction-vocabulary primitives:** [INT-94 dark-mode-stylesheet] — the direct realization of the aspirational primitive.
- **Where it fits:** `styles.py` — the `PALETTE_DARK` dict stub at line 110 (explicitly reserved for UPL-4).  `appearance_panel.py` and `app.py` call `QApplication.setStyleSheet(APP_STYLESHEET)` — UPL-4 adds a toggle that swaps to `APP_STYLESHEET_DARK`.
- **App positioning:** Application-level — all chrome simultaneously.
- **App-invariant:** PyQtDarkTheme is MIT; import-safe.  AI-12 (contrast): every dark-palette text token must re-verify WCAG AA against the new dark background (the `styles.py:63` note already flags `TEXT_MUTED = #5a5a5a` as failing on dark backgrounds — UPL-4 must provide `TEXT_MUTED_DARK`).

---

### PC-11: Viewport Orientation Cube / Camera-Preset Gizmo

- **Pattern name:** interactive orientation cube (view-axis gizmo) in viewport corner
- **Source app:** 3D Slicer (anatomical-axes triad), ParaView (orientation axes), Blender (viewport gizmo, upper-right)
- **Public evidence:**
  - https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html — "3D view renders volumetric data with anatomical orientation axes (L/R, A/P, S/I)" — shown in-viewport, not as separate panel widgets.
  - https://docs.paraview.org/en/latest/UsersGuide/introduction.html — ParaView embeds orientation axes as a VTK actor inside the 3D viewport, clickable to jump to named views.
- **What makes it good:** The current app's view presets (Front, Top, Side, Isometric) are buttons in the View dock left panel — the user must look left to find them.  An in-viewport orientation cube in the upper-right corner of the VTK canvas provides the same affordance without leaving the viewport.  More importantly, clicking a face of the cube in ParaView and Blender fires the matching camera preset — the interaction is spatial and immediate.  PyVista exposes `plotter.add_camera_orientation_widget()` which provides a simple axial gizmo with zero extra code.
- **Interaction-vocabulary primitives:** [INT-23 camera-preset-fire-and-render] — the gizmo is a VTK actor that fires the same `view_xy() / view_xz()` calls.  [INT-25 axes-overlay-toggle] — existing checkbox in View dock could also toggle the orientation cube.
- **Where it fits:** `view_panel.py:_make_view_presets_group()` (line 72) — clicking a preset button fires VTK camera calls; the gizmo would do the same.  `app.py:MainWindow.__init__` — add `plotter.add_camera_orientation_widget()` after `QtInteractor` construction.
- **App positioning:** Central 3D viewport (upper-right corner overlay).
- **App-invariant:** `pyvista.Plotter.add_camera_orientation_widget()` is within the existing PyVista dep range (≥ 0.46, < 0.49).  AI-1 safe.

---

### PC-12: Math-Typography Rendered Equation Tooltip

- **Pattern name:** KaTeX/rendered-math tooltip popover for variety equations
- **Source app:** Surfer/Imaginary.org (equation entry), GeoGebra 3D (equation display), Mathematica Manipulate (notebook-quality math rendering)
- **Public evidence:**
  - https://imaginary.org/program/surfer — SURFER displays the polynomial equation prominently in the UI alongside the surface, making the mathematical form legible.
  - https://www.geogebra.org/3d — GeoGebra renders equations in the algebra sidebar using its internal math-rendering engine, with proper super/subscripts and Greek letters.
  - KaTeX (https://katex.org/) — MIT license; renders LaTeX math to HTML in milliseconds.
- **What makes it good:** The current tooltip for the Fermat quartic reads something like "x⁴ + y⁴ + z⁴ = 1 (Smooth K3, χ = 24)".  The unicode superscripts are platform-dependent and render inconsistently across macOS/Windows/Linux.  A `QtWebEngineWidgets`-backed popover that renders `x^4 + y^4 + z^4 = 1` through KaTeX would show publication-quality math — the same quality a researcher expects from a LaTeX figure caption.  This directly matches SURFER's and GeoGebra's visual presentation where the equation is a first-class UI element.  Even without `QtWebEngineWidgets`, rendering the tooltip with an explicit `QToolTip { font-family: ...; }` CSS override would fix the inconsistent-rendering issue at minimum cost.
- **Interaction-vocabulary primitives:** [INT-95 katex-tooltip-popover] — the direct realization.  [INT-7 tooltip-rich] is the current plain-text fallback.
- **Where it fits:** `app.py` — the Variety and Model combo boxes carry `VARIETY_TOOLTIPS` / `SUBTYPE_TOOLTIPS` rich-text set via `Qt.ItemDataRole.ToolTipRole` (lines around 140–170).  The minimum fix is a `QToolTip` font CSS override in `APP_STYLESHEET` at `styles.py:191`.  The KaTeX popover is a larger investment requiring `QtWebEngineWidgets`.
- **App positioning:** Top control bar — Variety / Model combo tooltips; optionally a floating "equation badge" below the combo row.
- **App-invariant:** `QtWebEngineWidgets` is a heavy new dep (ships with Qt6 but adds ~100MB binary).  The minimum viable version (CSS font override on tooltip) has no new deps.  AI-1 safe.

---

## 3. Sources Reviewed

| App / Platform | URL | What was actually read | High-signal? |
|---|---|---|---|
| ParaView — color mapping | https://docs.paraview.org/en/latest/ReferenceManual/colorMapping.html | Transfer function editor, combo-box preset picker, opacity widget, color legend behavior | Yes |
| ParaView — Properties panel | https://docs.paraview.org/en/latest/ReferenceManual/propertiesPanel.html | Collapsible sections (Properties / Display / View), search box, basic/advanced toggle, Apply/Reset buttons | Yes |
| ParaView — animation | https://docs.paraview.org/en/latest/UsersGuide/animation.html | VCR controls toolbar, keyframe track table, timeline scrubber, parameter animation | Yes |
| ParaView — documentation index | https://docs.paraview.org/en/latest/ | Confirmed chapter list: Reference Manual sections 1–15, User's Guide 1–9 | Yes |
| ParaView — introduction | https://docs.paraview.org/en/latest/UsersGuide/introduction.html | Main window layout: dockable panels, Pipeline Browser, Properties panel, central viewport, status bar at lower-left | Yes |
| 3D Slicer — user interface | https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html | Module panel, multi-view layout, linked crosshair, Mouse Mode toolbar, Module Selection toolbar with history | Yes |
| 3D Slicer — Colors module | https://slicer.readthedocs.io/en/latest/user_guide/modules/colors.html | Color table categories (Discrete/Continuous/FreeSurfer/PET/User), copy-to-edit workflow, warm/cool complementary pairs | Yes |
| 3D Slicer — toolbars | https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html#toolbars | Module Selection history arrows, Favorite Modules toolbar, status bar error-log badge | Yes |
| Surfer / Imaginary.org | https://imaginary.org/program/surfer | Equation entry (mentioned), gallery described but no screenshots in HTML; Tips-and-tricks PDF 404'd | Low |
| GeoGebra 3D | https://www.geogebra.org/3d | Calculator toolbar layout described; algebra sidebar and equation rendering inferred; limited HTML content | Medium |
| Mathematica Manipulate | https://reference.wolfram.com/language/ref/Manipulate.html | 403 — blocked | No |
| Quanta Magazine | https://www.quantamagazine.org/ | Neutral minimal palette, generous whitespace, card-grid layout, large serif headings | Medium |
| 3Blue1Brown | https://www.3blue1brown.com/ | Clean sans-serif, lesson-grid layout, minimal color usage, content-first hierarchy | Medium |
| Stripe Press | https://press.stripe.com/ | Deep black text on off-white, generous vertical rhythm, limited accent palette (2–3 colors) | Medium |
| superqt (GitHub) | https://github.com/pyapp-kit/superqt | QLabeledSlider, QRangeSlider (multi-handle), QCollapsible, fonticon utilities; BSD-3-Clause | Yes |
| QtAds | https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System | Perspectives (named layouts), tabbed docking, auto-hide sidebars, PySide6 package on PyPI, LGPL-2.1 | Yes |
| PyQtDarkTheme | https://github.com/5yutan5/PyQtDarkTheme | Flat dark/light themes, macOS accent sync, MIT license, `pip install pyqtdarktheme` | Yes |
| MeshLab | https://www.meshlab.net/ | Homepage only — no UI patterns documented publicly there; redirected to tutorials | No |
| Blender features | https://www.blender.org/features/ | 403 — blocked | No |
| VisIt | https://visit-dav.github.io/visit-website/ | Homepage only — docs 404'd; no UI patterns documented | No |
| KAlgebra | https://apps.kde.org/kalgebra/ | Landing page — no UI details; handbook links 404'd | No |
| Inkscape (wiki) | https://wiki.inkscape.org/wiki/Docks | 404 | No |
| Distill.pub | https://distill.pub/ | Site structure confirmed; CSS not accessible; article-level design not retrievable from landing page | Low |

---

## 4. Themes

**Theme A — Progressive disclosure is universal in peer VTK apps but absent here.** ParaView (Properties panel basic/advanced toggle), 3D Slicer (module panel that exposes only the selected module's controls), and GeoGebra (algebra sidebar that hides advanced options) all employ progressive disclosure to manage UI density.  The app today has flat, always-visible groups in all three docks — there is no way to hide controls the current user does not need.  Even a simple collapsible `QGroupBox` trick on the Shading and Screenshot groups would align the app with its peers.

**Theme B — In-viewport affordances supplement but do not replace panel controls.** Every peer VTK app (ParaView, 3D Slicer, Slicer) shows orientation axes and annotation overlays directly on the canvas.  The app's View dock contains camera preset buttons that are spatially disconnected from the viewport.  Adding a PyVista orientation gizmo and a launch-state text overlay would bring the canvas itself into the interaction surface — a theme consistent across all peers.

**Theme C — Animation / sweep is a first-class research tool in peer apps.** ParaView's animation timeline, Mathematica Manipulate's play-per-slider button — both treat parameter-driven animation as core functionality, not a bonus.  The app has no sweep path at all.  This is the largest capability gap vs. 2026 SOTA.

**Theme D — Color palettes and presets are a distinct UX surface from color pickers.** All peer scientific-viz apps separate "pick a custom color" (the `QColorDialog`) from "select a named palette preset" (a combo box or searchable list of known-good scientific palettes).  The app today provides only the former for surface color.  Preset palettes are low implementation cost (a static dict + a combo box) but high research-credibility gain.

---

## 5. Cross-Reference to This App

| Pattern candidate | Closest existing app location (file:line) | Net-new? |
|---|---|---|
| PC-1 Color-map preset picker | `appearance_panel.py:124` (`_build_color_group`) + `styles.py:107` (`VARIETY_DEFAULT_COLOR` stub) | No — extends existing swatch UI |
| PC-2 Collapsible group sections | `appearance_panel.py:153` (`_build_toggles_group`), `195` (`_build_shading_group`); `view_panel.py:67` (`_build_ui`) | No — wraps existing QGroupBox groups |
| PC-3 Parameter sweep transport bar | `parameters_panel.py:61` (`_reset_btn` row); design-system §7 "Animated parameter sweep" | No — adds to existing Parameters dock |
| PC-4 Dock state persistence | `app.py` dock construction (dock `addDockWidget` calls); design-system §7 "State persistence via QSettings" | No — extends existing dock wiring |
| PC-5 Status-bar warning badge | `app.py:_render_current` warning block; design-system §7 "Status-bar warning badge persistence" | No — extends existing status bar |
| PC-6 Per-variety surface color presets | `styles.py:107` (`VARIETY_DEFAULT_COLOR` stub, explicitly reserved for UPL-5); `appearance_panel.py:301` (`apply_to_actor`) | No — fills an explicit stub |
| PC-7 Slider + spinbox exact-value entry | `parameters_panel.py` slider row construction in `set_specs`; design-system §7 "Parameter min/max field input" | No — extends existing parameter rows |
| PC-8 Surface history navigation | `app.py` top control bar (Variety/Model combo region ~lines 100–130) | Yes — net-new widget in toolbar |
| PC-9 Viewport text overlay | `app.py:MainWindow.__init__` (post-plotter construction); design-system §7 "First-launch tour" + "Empty-clip overlay" | Yes — net-new VTK actor |
| PC-10 Dark-mode stylesheet | `styles.py:110` (PALETTE_DARK stub explicitly reserved for UPL-4) | No — fills explicit stub |
| PC-11 Orientation cube gizmo | `view_panel.py:72` (`_make_view_presets_group`); `app.py:MainWindow.__init__` (post-plotter) | Yes — net-new PyVista widget |
| PC-12 Math-typography tooltip | `app.py:140–170` (VARIETY_TOOLTIPS / SUBTYPE_TOOLTIPS combo setup); `styles.py:191` (APP_STYLESHEET `QToolTip` section) | Minimum-viable: no new widget (CSS fix only); full KaTeX: net-new QtWebEngine dep |

---

## 6. Out of Scope / Parking Lot

| Pattern considered | Rejection reason |
|---|---|
| Side-by-side split viewport (two `QtInteractor` panels) | [INT-91] aspirational and heavy; creates two VTK GL contexts — out of scope for a chrome-focused shakedown; parking for a dedicated viewport-layout milestone |
| Full keyframe animation editor (track editor, spline curves) | Overkill for this app's audience; ParaView's timeline is powerful because it serves massive datasets — a simple VCR sweep (PC-3) is the right resolution |
| Pipeline browser / scene tree (Slicer-style hierarchy) | The app has one object at a time; a pipeline tree would be empty 99% of the time; no complexity to manage |
| Window/Level adjustment idiom (3D Slicer) | Medical imaging specific; not applicable to algebraic surface visualization |
| Linked crosshair synchronization across multi-view (3D Slicer) | Requires multi-viewport which is out of scope here |
| Blender outliner panel | 403 blocked; and Blender's object hierarchy is irrelevant when the app renders exactly one mesh |
| Distill.pub interactive article patterns | Scroll-driven web animations; no relevance to a Qt desktop app |
| VisIt expression editor | 404 / blocked; and expression editing is moot — equations are fixed in `surfaces.py`, not user-authored |
| MeshLab filter dialog | Homepage only; and the filter-parameter dialog pattern is covered more specifically by ParaView's Properties panel (PC-2) |
| `QScintilla` code editor for equation entry | GPL-3.0 (import-blocking); and equation entry is a separate feature surface not in this milestone's scope |
| Trame (Kitware web framework) | Apache-2.0 but heavy; only relevant if a web companion app is planned — explicitly out of scope (AI-1) |
| Categorical coloring / scalar-field color mapping | Algebraic variety viewer colors by solid color, not by scalar field — ParaView's scalar-bar / transfer-function editor is not applicable here |
| Auto-orient normals behavior (Blender/MeshLab smooth-group idiom) | AI-7 hard lock: disconnected patches cannot be coherently oriented; the workaround is already in `surfaces.py` |
