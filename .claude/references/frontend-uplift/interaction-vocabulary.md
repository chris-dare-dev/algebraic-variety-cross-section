# Interaction + visual-effect vocabulary

**Purpose:** a curated reference so every scout speaks the same language when proposing interaction / animation / panel-layout / camera upgrades to the Algebraic Variety Viewer.  Cite by name (e.g. `[INT-3 busy-cursor]`) in briefs and synthesis catalogs.

This file is loaded by scouts and by the synthesizer at phase start.  It is NOT a tutorial — it's a vocabulary table.

The app context here is a PySide6 + PyVista + VTK desktop application.  Interactions are mouse + keyboard, not touch.  Animations are mostly cosmetic (VTK camera transitions, status-bar feedback, slider release feedback) — there is no scroll-driven or fade-up pattern surface because there's no scroll.

---

## 1. Selection / dispatch primitives

| ID | Name | Description | When to use | Caveats |
|---|---|---|---|---|
| INT-1 | `dropdown-cascade` | Variety → Model two-step dropdown selection | Adding a new variety family | Each combo carries rich tooltips via `Qt.ItemDataRole.ToolTipRole` |
| INT-2 | `slider-release-render` | Slider fires `valueChanged` continuously but render triggers only on `sliderReleased` | Any parameter slider that drives a >100ms compute (marching cubes, big grids) | Direct `valueChanged` would saturate the pipeline.  Currently used in `parameters_panel.py`. |
| INT-3 | `busy-cursor` | `QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)` while a render is in flight | Renders > ~250ms (any marching-cubes generator) | Pair with INT-4 status feedback for sub-second renders too |
| INT-4 | `status-bar-feedback` | `statusBar().showMessage(...)` with surface label + vertex/face count + parameter values | Every successful render | Warnings prefixed `⚠`; errors verbatim (no prefix) |
| INT-5 | `keyboard-shortcut` | `QShortcut(QKeySequence("Ctrl+R"), ...)` for common actions | Reset camera, screenshot, reset defaults | Currently 3 shortcuts; expanding surface is a candidate |
| INT-6 | `dock-floatable` | `QDockWidget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable \| DockWidgetFeature.DockWidgetFloatable)` | Default for every dock | Users can drag docks between left/right edges or float onto a second monitor |
| INT-7 | `tooltip-rich` | `setToolTip("equation\nsymmetry\nsource")` on every interactive control | Variety dropdown items, sliders, panel headers | The vehicle for surfacing math-rigor without cluttering the canvas |

## 2. Camera / viewport interaction

| ID | Name | Description | Implementation | When to use |
|---|---|---|---|---|
| INT-20 | `vtk-trackball-rotate` | Left-drag rotates the camera; the default `QtInteractor` style | Already wired in `app.py` | Never override unless adding a competing interaction mode |
| INT-21 | `scroll-wheel-zoom` | Scroll up zooms in, scroll down zooms out | VTK default | Pair with right-drag zoom |
| INT-22 | `shift-drag-pan` | Shift + drag pans the camera | VTK default | Reserved gesture; don't shadow it |
| INT-23 | `camera-preset-fire-and-render` | A view-preset button calls `_plotter.reset_camera()` / `view_xy()` / etc. and then `_plotter.render()` | `view_panel.py:_make_view_callback` factory | CONTEXT.md §8.1 — every camera state change MUST be followed by `render()` or VTK queues the change without redrawing |
| INT-24 | `camera-transition-interp` | Smooth interpolation between camera states over ~300ms (NOT in the app today) | Custom VTK interpolation or pyvista's `plotter.fly_to(...)` (limited) | Candidate-surface; pair with optional reduced-motion toggle |
| INT-25 | `axes-overlay-toggle` | Show/hide world-axes triad, bounding box, grid axes via checkboxes | `view_panel.py` | Each toggle is an INT-23 (must end in `render()`) |
| INT-26 | `domain-clip-cached-recompute` | Sphere/cube clip slider re-clips the cached `_raw_mesh` without regenerating | `app.py:_on_domain_changed` → `_apply_domain_and_render(reset_camera=False)` | AI-10 invariant.  Don't propose UI that "rerenders everything" on clip change. |
| INT-27 | `clip-outline-overlay` | When domain clip is on, an outline mesh visualizes the clip region | `view_panel.py:clip_to_domain` returns `(clipped, overlay)` | Cosmetic but load-bearing for users to see what's being hidden |

## 3. Panel / dock layout

| ID | Name | Description | When to use | Caveats |
|---|---|---|---|---|
| INT-40 | `parameters-rebuild-on-switch` | When variety/model changes, parameters dock tears down and rebuilds slider widgets from the new `Surface.params` | `parameters_panel.py` | Inevitable given dynamic `ParamSpec` list shape |
| INT-41 | `reset-to-defaults-button` | "Reset all to defaults" — restores every slider to its `ParamSpec.default` | `parameters_panel.py`; object name `resetDefaultsBtn` styled via `styles.py` QSS | Non-destructive — no confirmation dialog |
| INT-42 | `cy3-context-banner` | When variety is Calabi–Yau 3-fold, a context label reminds the user the figure is a 2D shadow, not the 6D variety | `parameters_panel.py` | The honest "this isn't the variety itself" prompt; AI-15 honesty discipline |
| INT-43 | `swatch-color-picker` | `QColorDialog`-launched swatch button for surface and background color | `appearance_panel.py` | Use `QColor` → 6-digit hex (AI-13) before passing to PyVista |
| INT-44 | `style-radio-or-toggle` | Solid / Wireframe / Surface-with-edges as exclusive options | `appearance_panel.py` | Pair with `actor.GetProperty().SetRepresentation(...)` |
| INT-45 | `dock-header-tinted` | Dock title bars use `COLOR_DOCK_HEADER_BG = #e8edf2` + 1px border (`styles.py`) | Already universal | Don't propose hand-rolled per-dock colors |

## 4. Off-screen rendering / capture

| ID | Name | Description | When to use | Caveats |
|---|---|---|---|---|
| INT-60 | `pv-off-screen-render` | `pv.OFF_SCREEN = True; p = pv.Plotter(off_screen=True, window_size=(W, H)); p.add_mesh(...); p.show(screenshot=path)` | Tests, frontend-uplift visual scout, CI smoke checks | AI-3.  Must NOT be used with `QT_QPA_PLATFORM=offscreen` + QApplication — VTK GL segfaults on macOS |
| INT-61 | `screenshot-png-save` | `pyvistaqt.QtInteractor`-mode screenshot via `QFileDialog` + `plotter.screenshot(path)` | `view_panel.py` screenshot button | High-resolution dump for figures / sharing |
| INT-62 | `read-the-png-to-verify` | After an off-screen render, `Read` the PNG and visually inspect it | Adversarial verification of UI / mesh changes | The only true verification path for GUI rendering since AI-2 forbids pytest-qt |

## 5. Status / feedback / warning

| ID | Name | Description | When to use | Caveats |
|---|---|---|---|---|
| INT-70 | `status-warning-prefix` | `warnings.catch_warnings(record=True)` extracts RuntimeWarning from `surface.generate()` and prefixes `⚠` in status bar | `app.py:_render_current` | AI-14.  Soft signals — render succeeds, but something noteworthy happened (Dwork conifold) |
| INT-71 | `status-value-error` | `ValueError` from generator → status bar + `self._raw_mesh = None` | `app.py:_render_current` except path | AI-14 hard error.  No mesh to display; subsequent domain-clip calls do nothing |
| INT-72 | `parameter-suffix` | `ParamSpec(suffix="rad")` → slider shows "1.57 rad" not "1.57" | `parameters_panel.py` | Cheap clarity gain |
| INT-73 | `parameter-description-tooltip` | `ParamSpec.description` → slider tooltip | `parameters_panel.py` | Use for "boundary effects", "non-compact when β > 3", etc. |
| INT-74 | `empty-clip-status-message` | When domain clip empties the visible mesh, status bar says "Domain is smaller than the surface — no geometry to display" | `app.py:_apply_domain_and_render` | Candidate: add a VTK text overlay on the canvas itself (§7 in design-system.md) |
| INT-75 | `restart-prompt-on-fatal-segfault` | (Aspirational) catch SystemError / RuntimeError in render path and offer "Restart"; currently the app just crashes | Not implemented | Candidate-surface for stability hardening |

## 6. Decorative / cosmetic

| ID | Name | Description | When to use | Caveats |
|---|---|---|---|---|
| INT-80 | `solid-color-bg` | Plotter background set to a chosen color | `appearance_panel.py` | Use 6-digit hex (AI-13) |
| INT-81 | `gradient-bg` | Two-color vertical gradient background | `appearance_panel.py` toggle | Subtle; don't compete with the surface |
| INT-82 | `focus-ring-on-controls` | `outline: 2px solid #5b9bd5; outline-offset: 1px;` on `:focus` | `styles.py` `APP_STYLESHEET` | A11y baseline — don't strip |
| INT-83 | `phong-vs-flat-shading` | Smooth/Phong vs flat shading toggle | `appearance_panel.py` | Phong is the default; flat is for pedagogy of facet structure |
| INT-84 | `wireframe-style` | `actor.GetProperty().SetRepresentationToWireframe()` | `appearance_panel.py` | Useful pedagogy for the marching-cubes triangulation |

## 7. Aspirational primitives (not in the app today — candidate surface)

| ID | Name | Description | What it would enable |
|---|---|---|---|
| INT-90 | `parameter-sweep-animation` | Slider-bound parameter animates min → max over N seconds with snapshots | Hanson dwell-time animation; Dwork ψ-sweep through conifold |
| INT-91 | `side-by-side-comparison-mode` | Split central widget into two `QtInteractor` viewports | K3 ↔ Kummer comparison; Enriques figure family |
| INT-92 | `state-persistence-qsettings` | Save last-used surface + slider values + dock layout to `QSettings` | Cross-launch state continuity |
| INT-93 | `mesh-export-button` | `mesh.save("file.stl"/"file.obj"/"file.ply")` from a new view-panel button | Researcher workflows in Blender / Meshmixer |
| INT-94 | `dark-mode-stylesheet` | Parallel `STYLESHEET_DARK` in `styles.py` with dark-theme palette + Plotter `set_plot_theme('dark')` | Math-research-audience-friendly dim chrome |
| INT-95 | `katex-tooltip-popover` | Floating dialog with KaTeX-rendered equation (instead of unicode-only plain-text tooltip) | High-fidelity equation surface |
| INT-96 | `palette-template-per-variety` | Default surface color per variety family (K3 slate, Enriques warm, CY3 cobalt) | Visual cue for the math reader |
| INT-97 | `parameter-spin-box-alternative` | `QDoubleSpinBox` paired with each slider for exact numeric entry | Probe ψ = 1.0001 (conifold) without slider-step coercion |
| INT-98 | `help-menu-with-citations` | `QMenuBar` "Help" with About dialog containing all variety citations | Central reference card; menu bar doesn't exist today |

## 8. Anti-patterns (do NOT propose)

| ID | Name | Why it's an anti-pattern |
|---|---|---|
| INT-NO-1 | `real-time-render-during-drag` | Slider `valueChanged` → render would saturate marching cubes (~0.5s per call).  Use `sliderReleased` (INT-2). |
| INT-NO-2 | `pytest-qt-tests-of-mainwindow` | **AI-2**: Qt + VTK GL context segfaults under `QT_QPA_PLATFORM=offscreen` on macOS.  Tests stay Qt-free. |
| INT-NO-3 | `mainwindow-offscreen-construction` | **AI-3**: `MainWindow()` under `QT_QPA_PLATFORM=offscreen` segfaults during VTK GL init.  Use `pv.OFF_SCREEN = True` + `Plotter(off_screen=True)`. |
| INT-NO-4 | `clip-box-on-polydata` | **AI-4**: `clip_box(invert=...)` semantics are reversed/unreliable on PolyData.  Use scalar clipping. |
| INT-NO-5 | `short-hex-into-pyvista` | **AI-13**: PyVista rejects `#888`.  Always 6-digit. |
| INT-NO-6 | `unguarded-processEvents` | **AI-9**: Re-enters `_render_current` via slider-release → dangling actors + stale `_raw_mesh`.  Guard with `self._computing`. |
| INT-NO-7 | `auto-orient-normals-on-hanson` | **AI-7**: Disconnected patches can't be coherently oriented — produces per-patch lighting flips.  Use `cell_normals=True, consistent_normals=False, auto_orient_normals=False`. |
| INT-NO-8 | `forced-fullscreen-on-launch` | Single-developer-on-laptop convention; the windowed default at 1200×800 is intentional. |
| INT-NO-9 | `confirmation-dialog-on-reset-defaults` | Action is non-destructive (CONTEXT.md §9); the dialog interrupts flow. |
| INT-NO-10 | `matplotlib-mpl_toolkits-3d` | **AI-1**: painter's-algorithm artifacts on self-intersecting surfaces; slow.  Don't surface as alternative. |
| INT-NO-11 | `mayavi-as-alternative-renderer` | **AI-1**: broken on Apple Silicon as of 2025.  Don't surface. |
| INT-NO-12 | `plotly-or-k3d-in-qt` | **AI-1**: Jupyter-first; awkward in Qt.  Don't surface as alternative. |
| INT-NO-13 | `raw-vtk-bypassing-pyvista` | **AI-1**: verbose; PyVista is the right level.  Don't propose dropping to raw `vtk.vtkPolyDataMapper(...)` directly. |

---

## How to cite in a brief or candidate

In a scout brief, when proposing an upgrade that uses one of these primitives, cite it by ID + name:

> "On the Appearance dock, replace the discrete style-toggle with a `[INT-43 swatch-color-picker]`-style segmented control paired with `[INT-44 style-radio-or-toggle]` to make wireframe-vs-solid feel like one decision, not two."

In the Phase 2 synthesis catalog, each candidate's "Sketch" section calls out the interaction primitives it composes:

> **Sketch:** Add a `[INT-90 parameter-sweep-animation]` button beside each slider; when clicked, the slider animates from min → max over 3 seconds with off-screen `[INT-60 pv-off-screen-render]` snapshots saved to `~/Documents/sweeps/`.  Pair with `[INT-3 busy-cursor]` during the sweep; respect future `[INT-94 dark-mode-stylesheet]` token for the progress bar.

This shared vocabulary is the load-bearing thing that lets the synthesizer dedupe across briefs ("library-scout cites QPropertyAnimation; visual-scout cites *slider scrubber for Hanson dwell time*; both are pointing at `[INT-90 parameter-sweep-animation]`").
