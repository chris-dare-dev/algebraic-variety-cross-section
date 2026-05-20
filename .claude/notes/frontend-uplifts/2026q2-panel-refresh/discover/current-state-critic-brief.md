# Current-State Critic Brief — 2026 Q2 Panel Refresh

**Agent:** current-state-critic
**Date:** 2026-05-20
**Scope:** broad survey, strict app-invariant adherence (AI-1..AI-15), triangulation bias

---

## 1. Executive Summary

The Algebraic Variety Viewer is a well-engineered PySide6 + PyVista desktop app with clean architecture, honest math disclaimers, and genuine WCAG AA contrast compliance throughout. Against 2026 scientific-viz desktop-tool standards, four gaps stand out. First, every one of the 14 surfaces ships with the identical steel-blue default color (`#b0c4de`) — no per-family visual cue — making the gallery feel monotone and erasing the only ambient signal about variety family. Second, the app is light-theme-only with no dark-mode toggle, a gap that peers (ParaView, Blender, 3D Slicer) all close and that the math-research audience (3Blue1Brown, Quanta) expects. Third, the Fano 3-fold context banner is absent: when the user selects "Fano 3-fold (ρ=1)", `app.py` sets `parameters_panel.set_context_hint(...)` with the 6-dimensional disclaimer, but this warning is absent from the status bar's initial message in the same code path (it correctly says "each figure is a 2D real slice" but the Parameters dock hint is populated only after the variety changes — the CY3 and Fano paths mirror each other, so both are wired). On close visual inspection, a fourth gap shows: parameter-value direct entry is absent, forcing researchers to coerce exact values like ψ = 1.0001 through discrete slider steps.

---

## 2. Critical Gaps

None. The app has no on-launch crashes, no generator-default that produces an empty mesh at default params, and no load-bearing contrast failure.

---

## 3. High Gaps

### H-1 — No dark-mode toggle

**Severity:** HIGH

**Affected files / panels:** `styles.py` (entire palette; no dark variant exists), `appearance_panel.py:74–75` (hardcoded dark background `#2f2f2f` for the 3D viewport — a half-measure: the VTK canvas is dark, the Qt chrome surrounding it is bright light-grey), `app.py:427` (`app.setStyleSheet(APP_STYLESHEET)` — single stylesheet, no toggle)

**App-invariant / accessibility conflicts:** AI-12 applies to any new dark-palette text tokens — must clear 4.5:1 against the dark background. No existing rule forbids a dark mode.

**What 2026 SOTA expects:** ParaView (5.x), Blender (4.x), 3D Slicer (5.x), and Mathematica all ship a first-class dark mode. The math-research audience that this app targets (Quanta Magazine aesthetic, 3Blue1Brown, arxiv-sourced screencasts) overwhelmingly prefers dark chrome around geometric visualization. The `design-system.md §2` explicitly calls this out as a candidate surface and notes it is RECONSIDERABLE. The interaction vocabulary names it `[INT-94 dark-mode-stylesheet]`.

**What a credible v1 fill-in looks like:** Add `STYLESHEET_DARK` to `styles.py` alongside `APP_STYLESHEET`, defining a parallel palette (`COLOR_BG_DARK = "#1e1e1e"`, `COLOR_PANEL_DARK = "#252525"`, dark dock-header variant). Add a `QCheckBox` or `QAction` (Help menu) to toggle between light and dark; on toggle, call `QApplication.instance().setStyleSheet(STYLESHEET_DARK if dark else APP_STYLESHEET)` and `plotter.set_plot_theme("dark"/"document")`. The VTK canvas already defaults dark (`#2f2f2f`); the Qt chrome just needs to match. Total surface: `styles.py` + a one-liner in `app.py` + the toggle widget.

**Why this hasn't been fixed yet:** Explicitly scoped out — single-developer cadence; the design-system.md notes it as a "sizable candidate" (full palette parallel variant required). No single PR has been the right moment.

---

### H-2 — Uniform single default surface color across all 14 surfaces

**Severity:** HIGH

**Affected files / panels:** `appearance_panel.py:74` (`self._surface_color = QColor("#b0c4de")` — a single hardcoded default applied to every surface regardless of variety family), confirmed by visual inspection of four render images (K3 Fermat quartic, K3 Kummer, Enriques sextic, CY3 Hanson quintic — all ship the same steel-blue).

**App-invariant / accessibility conflicts:** None — this is a convention gap, not a rule violation. Colors flowing into PyVista must be 6-digit hex (AI-13), which any per-variety palette would continue to satisfy.

**What 2026 SOTA expects:** Every major scientific-viz tool (ParaView color-by-field, Mathematica's `Manipulate` surface palettes, MathMod's material catalog) assigns visually distinct defaults to different object families. The `design-system.md §7` explicitly lists "Variety-family color theming" and `[INT-96 palette-template-per-variety]` as candidates. A math reader switching between K3 and Calabi–Yau gets no ambient visual cue to orient them; everything looks like the same steel-blue blob.

**What a credible v1 fill-in looks like:** Add a `VARIETY_DEFAULT_COLORS: dict[str, str]` mapping in `surfaces.py` or `styles.py` (e.g., K3 → `"#a8c8e8"` cool blue, Enriques → `"#c8b8d8"` mauve, CY3 → `"#7090c0"` deeper cobalt, Fano → `"#c0a870"` warm gold). In `app.py._on_subtype_changed`, after `self.parameters_panel.set_specs(...)`, call `self.appearance_panel.set_default_color(VARIETY_DEFAULT_COLORS[variety])` — a new one-liner method on `AppearancePanel` that sets `_surface_color`, updates the swatch, and re-applies to any live actor. The existing `apply_to_actor` path stays unchanged; the only change is the starting color when a new surface loads.

**Why this hasn't been fixed yet:** A single-developer app optimized for correctness first; visual theming per-variety would require coordinating palette choices with math-family intuitions (cool for K3/complex geometry, warm for Fano/index theory) — a design decision that was deferred while the variety count was small. Now at 14 surfaces across 4 families, the uniform color is a real quality-of-life gap.

---

### H-3 — No parameter direct-entry (spin-box) alongside sliders

**Severity:** HIGH

**Affected files / panels:** `parameters_panel.py:126–182` (`_build_row` builds only a `QSlider` + value readout label; no `QDoubleSpinBox`), `surfaces.py` DWORK_PARAMS (`psi` step=0.02 means ψ=1.0001 is unreachable by slider; the conifold at ψ=1 is documented as scientifically important but the slider can only reach ψ=1.00 or ψ=0.98).

**App-invariant / accessibility conflicts:** None — `[INT-2 slider-release-render]` governs the render trigger, not the input widget. A spin box's `editingFinished` signal is the natural analog to `sliderReleased`.

**What 2026 SOTA expects:** Mathematica's `Manipulate`, ParaView's filter-parameter panels, and 3D Slicer's volume-rendering controls all pair sliders with editable numeric fields. The `design-system.md §7` names this `[INT-97 parameter-spin-box-alternative]` as an underdeveloped candidate. For a research tool — where probing ψ = 1.0001 to see the conifold complement is a real workflow — this is not cosmetic.

**What a credible v1 fill-in looks like:** Replace the `value_lbl: QLabel` readout in `_build_row` with a `QDoubleSpinBox` whose range / step / decimals are derived from `spec`. Connect `spinBox.editingFinished` to emit `params_changed` (same signal). Keep the `QSlider` as the primary coarse control; wire `sliderValueChanged → update spinBox.setValue(...)` and `spinBoxValueChanged → update slider.setValue(...)`. The two widgets stay synchronized; the render trigger fires only on `sliderReleased` or `spinBox.editingFinished`. This resolves the conifold-unreachable-by-slider issue for the Dwork pencil and makes the α slider on Hanson cross-sections usable for fine-grained projection-angle tuning.

**Why this hasn't been fixed yet:** Explicitly listed in `design-system.md §7` as an underdeveloped candidate; "single-developer cadence" and the slider-only pattern was sufficient for the first three variety passes. The conifold issue was documented (CONTEXT.md §8.8) but the fix was a `RuntimeWarning` rather than a better input control.

---

## 4. Medium Gaps

### M-1 — No first-launch affordance (empty viewport, "— Select —" placeholder)

**Severity:** MEDIUM

**Affected files / panels:** `app.py:55` (`self.variety_combo.addItem(_PLACEHOLDER)` where `_PLACEHOLDER = "— Select —"`), `app.py:86` (`self.statusBar().showMessage("Choose a variety to begin.")`) — no visual cue in the viewport itself, no highlighted first step, no skeleton state.

**App-invariant / accessibility conflicts:** None — design-system.md §6 notes "first-launch auto-render of a default surface" is RECONSIDERABLE (not hard-rejected). A hint overlay is distinct from auto-render.

**What 2026 SOTA expects:** ParaView shows a blank-canvas helper text ("Open a file to begin" or equivalent); Mathematica's `Manipulate` opens with rendered output. For a cascading-dropdown UX (two steps required before anything renders), visitors routinely stall on the blank viewport. The `design-system.md §7` names this gap explicitly.

**What a credible v1 fill-in looks like:** Add a VTK text actor or Qt overlay label in the central viewport area that reads "Select a variety and model to begin rendering" in `COLOR_MUTED` style — cleared when `_render_current` succeeds. This requires no auto-render and respects the "research tool doesn't presume" convention while providing the onboarding cue. A single `QLabel` absolutely positioned over the `QtInteractor` widget (parented to `central`, shown/hidden by render success) is the simplest path.

**Why this hasn't been fixed yet:** Explicitly discussed and deferred in CONTEXT.md §9 ("The UI/UX agent considered auto-selecting the first surface and decided it would feel presumptuous"). A canvas hint (not auto-render) is a different proposal that wasn't independently evaluated.

---

### M-2 — No 3D mesh export (STL / OBJ / PLY)

**Severity:** MEDIUM

**Affected files / panels:** `view_panel.py:246–256` (`_make_screenshot_group` — only PNG screenshot offered), `app.py:88` (`self._raw_mesh = None` — raw mesh is cached and available for export at any time).

**App-invariant / accessibility conflicts:** None. AI-10 (raw mesh cached) actually makes this easy: `self._raw_mesh.save(path)` at any time after a successful render.

**What 2026 SOTA expects:** Every major 3D viz tool (ParaView, Blender, MeshLab, VTK) exports to at least STL and OBJ. The math-research workflow of generating a surface and loading it in Blender for a polished render, or in GeoGebra for student demonstrations, is blocked without export. CONTEXT.md §9 notes this as a one-liner (`mesh.save("file.stl")`).

**What a credible v1 fill-in looks like:** Add a "Export mesh…" button to the `_make_screenshot_group` in `view_panel.py`, opening a `QFileDialog.getSaveFileName` with filters for STL / OBJ / PLY. On accept, call `self._main_window._raw_mesh.save(path)` (or expose a `get_raw_mesh` callback like `get_actor`). The `Export` group box becomes "Export" rather than just "Screenshot". The only arch consideration is that `view_panel.py` currently doesn't hold a reference to the main window's raw mesh; add a `get_mesh` callback on construction alongside `get_actor`.

**Why this hasn't been fixed yet:** CONTEXT.md §9 explicitly lists it as "one line" but skipped — never the priority item in a variety-feature-focused development cadence.

---

### M-3 — Missing `⚠` node-seam visual artifact in Enriques sextic default render (render quality gap, not a crash)

**Severity:** MEDIUM

**Affected files / panels:** The visual render of `enriques-surface-canonical-sextic-default.png` shows pronounced white "zipper" artifacts along the self-intersection curves where the six coordinate tetrahedron edges meet — bright white seams contrast sharply against the steel-blue surface. This is because the Enriques sextic `F = x²y² + x²z² + y²z² + x²y²z² + c·xyz·(1+x²+y²+z²)` has genuine singular double-points where two sheets meet at a near-zero field; the marching cubes level set at 0 produces two thin facing sheets joined by a near-degenerate cell row. The seams are visually distracting at the default parameter and background combination. `surfaces.py:317–344` (`enriques_figure_1` generator), `app.py:370–375` (no back-face culling or special handling for self-intersecting surfaces).

**App-invariant / accessibility conflicts:** AI-6 applies — the marching cubes pipeline is correct for this surface; this is a rendering quality issue, not a pipeline bug.

**What 2026 SOTA expects:** Scientific-viz tools (ParaView, VisIt) handle self-intersecting surfaces by default with back-face culling to eliminate inside-facing geometry at self-intersections. PyVista supports `actor.GetProperty().BackfaceCullingOn()` (or `plotter.add_mesh(..., backface_culling=True)`). For the Enriques sextic specifically, enabling back-face culling eliminates the bright seam artifacts without changing the surface geometry.

**What a credible v1 fill-in looks like:** Pass `backface_culling=True` in `app.py:_apply_domain_and_render` when calling `self.plotter.add_mesh(clipped, ...)`, OR expose a "Back-face culling" toggle in the Appearance dock's "Display" group (`appearance_panel.py:144–162`). The toggle approach is more general and lets users turn it on/off as pedagogically needed. The toggle should default to `True` and be wired through `apply_to_actor`.

**Why this hasn't been fixed yet:** Render quality of self-intersecting surfaces wasn't the focus of the adversarial reviewer or UX passes, which concentrated on parameter correctness, normals, and contrast. The visual artifact is subtle in small screenshots but glaring on a real monitor.

---

### M-4 — Appearance panel surface-color default ignores variety context

**Severity:** MEDIUM

**Affected files / panels:** `appearance_panel.py:74` (hardcoded `#b0c4de` — identical to the "visual renders all look the same" observation in H-2; listed separately because this is the panel-code root cause). The Appearance dock's "Surface…" button launches a color picker initialized to `#b0c4de` for every single surface — no memory of a per-variety previous color either, since `_surface_color` is a single field and reset only when the user explicitly opens the picker.

**App-invariant / accessibility conflicts:** AI-12 — any new default color must pass WCAG AA contrast. AI-13 — 6-digit hex to PyVista.

**What 2026 SOTA expects:** Mathematica's `Manipulate`, ParaView surface-coloring, and 3D Slicer material assignments all maintain per-object or per-family color memory. The `design-system.md §7` names `[INT-96 palette-template-per-variety]` as a candidate.

**What a credible v1 fill-in looks like:** This is the implementation twin of H-2 — a `set_default_color(hex: str)` method on `AppearancePanel` that `MainWindow._on_subtype_changed` calls with the variety's palette entry. The appearance panel's internal `_surface_color` gets updated and the swatch re-paints. Only a few lines of new code; the design decision is the palette mapping (handled in H-2's sketch).

**Why this hasn't been fixed yet:** Same as H-2 — deferred during variety-content-focused development passes.

---

### M-5 — Status-bar warning persistence: one-render lifespan only

**Severity:** MEDIUM

**Affected files / panels:** `app.py:329–333` — the `⚠ {_surface_warning}` prefix is prepended to the status bar message for exactly one render cycle. The next time any slider releases and triggers a re-render (even with ψ still near 1.0), the message is silently overwritten by the fresh status bar string. The `⚠` conifold warning is informational but disappears as soon as the user adjusts opacity or changes background color (neither of which triggers a re-render, so actually the warning persists — but any slider release wipes it).

**App-invariant / accessibility conflicts:** AI-14 — warning surfacing is correctly implemented for the moment of render; the persistence gap is a UX quality issue, not an invariant conflict.

**What 2026 SOTA expects:** ParaView, 3D Slicer, and Blender all maintain a persistent "warnings/errors" panel or badge that persists until explicitly dismissed. The `design-system.md §7` names "Status-bar warning badge persistence" as a candidate.

**What a credible v1 fill-in looks like:** Store `_last_surface_warning: str = ""` alongside `_raw_mesh` in `MainWindow`. When `_apply_domain_and_render` writes the status bar, re-prefix the warning if `_last_surface_warning` is non-empty. Clear `_last_surface_warning` only when the surface changes (in `_on_subtype_changed`). This is a ~5-line patch to `app.py` that ensures the conifold warning stays visible through clip/opacity/camera adjustments.

**Why this hasn't been fixed yet:** Single-render warning lifetime is an emergent property of the "status bar reflects current render state" pattern; the warning code was added per-render and persistence wasn't independently considered.

---

### M-6 — No menu bar (no Help, no keyboard shortcut reference, no citations card)

**Severity:** MEDIUM

**Affected files / panels:** `app.py` has no `QMenuBar`, no `menuBar()` call anywhere. The three keyboard shortcuts (`Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D`) are documented in the View dock's help label and in the README, but there is no in-app reference card. The `design-system.md §7` lists "Help menu / About dialog with mathematical citations" as a candidate.

**App-invariant / accessibility conflicts:** None. A menu bar is a standard QMainWindow component; it doesn't interact with AI-1 through AI-15.

**What 2026 SOTA expects:** Every mature desktop app (ParaView, Blender, Mathematica, GeoGebra) has at minimum a "Help" menu with "About" (credits + citations), "Keyboard shortcuts", and "Report issue". The absence of a menu bar feels unfinished to a 2026 desktop user, especially one who arrives from a paper reference and wants to verify the citation.

**What a credible v1 fill-in looks like:** Add a `QMenuBar` with two menus: "View" (toggle dark mode — H-1 fills this) and "Help" (About dialog with variety citations + keyboard shortcuts table). The About dialog's citation list is already available in `SUBTYPE_TOOLTIPS` and the README's "Further reading" section — it's a formatting task, not a research task.

**Why this hasn't been fixed yet:** Single-developer app focused on math content; menu bar infrastructure felt like ceremony until now. `design-system.md §7` acknowledges it.

---

## 5. Low Gaps

### L-1 — `Qt.AA_ShareOpenGLContexts` uses the pre-qualified shorthand (AI-11 drift)

**Severity:** LOW

**Affected files / panels:** `app.py:425` — `QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)`. The qualified form is `Qt.ApplicationAttribute.AA_ShareOpenGLContexts` (PySide6 fully-qualified enum). The unqualified form still works via backward-compat aliases but emits a PySide6 deprecation warning.

**App-invariant / accessibility conflicts:** AI-11 — new UI code should use the qualified enum form everywhere.

**What 2026 SOTA expects:** The rest of the codebase is clean (`Qt.AlignmentFlag.AlignLeft`, `Qt.Orientation.Horizontal`, `QSizePolicy.Policy.Expanding` all appear in qualified form). This single `Qt.AA_ShareOpenGLContexts` is the only survivor of the earlier unqualified drift.

**What a credible v1 fill-in looks like:** One-line fix: `QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)`.

**Why this hasn't been fixed yet:** The attribute was likely added before the AI-11 audit was codified; the line works and emits no user-visible warning at runtime (the deprecation warning appears in the process stderr, not in the Qt UI).

---

### L-2 — `#888` short hex in `appearance_panel.py` swatch border (minor AI-13 adjacency)

**Severity:** LOW

**Affected files / panels:** `appearance_panel.py:48` — `f"background-color: {hex_color}; border: 1px solid #888;"`. This is a Qt stylesheet string (not a PyVista color argument), so PyVista's parser never sees it. AI-13 technically applies only to colors flowing into PyVista. However, the codebase convention is "always 6-digit hex" across both surfaces (per design-system.md §2 "consistency is preferred"). The `CONTEXT.md §8.3` note explicitly calls this out.

**App-invariant / accessibility conflicts:** Technically not an AI-13 violation (Qt accepts short hex). Cosmetically inconsistent with the rest of the palette.

**What a credible v1 fill-in looks like:** Change `#888` → `#888888` in `appearance_panel.py:48`. One character.

**Why this hasn't been fixed yet:** Qt accepts short hex silently; this line predates the AI-13 convention being written down as a project rule.

---

### L-3 — HiDPI / Retina workaround documented in README but not baked into `app.py`

**Severity:** LOW

**Affected files / panels:** `README.md:334` documents "Run with `QT_AUTO_SCREEN_SCALE_FACTOR=1 python app.py`" as a workaround for jumpy sliders on Retina displays. `app.py:424–430` (`main()`) doesn't set this env var or call `QApplication.setHighDpiScaleFactorRoundingPolicy`. The `design-system.md §7` names "HiDPI / Retina scaling polish" as a candidate.

**App-invariant / accessibility conflicts:** None.

**What a credible v1 fill-in looks like:** Add `os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")` before `QApplication(sys.argv)` in `main()`, or call `QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)` — the latter being the PySide6 6.6+ idiomatic form. This eliminates the README workaround.

**Why this hasn't been fixed yet:** Workaround documented as "known issue, fix not yet baked in" per CONTEXT.md §9 (not explicitly listed but implied by README note). Requires testing on Retina vs non-Retina to verify no regressions.

---

### L-4 — Clip-region empty-canvas has no viewport text overlay

**Severity:** LOW

**Affected files / panels:** `app.py:350–368` (`_apply_domain_and_render` when `clipped.n_points == 0`) — the status bar says "Clip region is smaller than the surface — reduce the radius or change the clip shape to see geometry" but the VTK viewport itself shows nothing. CONTEXT.md §9 explicitly lists this as "A VTK text overlay would be nicer but tightly couples to the render pipeline." The `design-system.md §7` names it "Empty-clip overlay annotation."

**App-invariant / accessibility conflicts:** AI-9 (re-entrancy guard) — adding a VTK text actor during the `_apply_domain_and_render` path is safe as long as it's inside the `_computing = True` window.

**What a credible v1 fill-in looks like:** In `_apply_domain_and_render`'s empty-mesh branch, call `self.plotter.add_text("No geometry — reduce clip radius", position="upper_left", font_size=10, color="#5a5a5a")` as a transient actor stored in a `_empty_clip_text_actor` member, cleared at the top of each `_apply_domain_and_render` call. Text color `#5a5a5a` matches `COLOR_MUTED`. Requires confirming `plotter.add_text` color accepts 6-digit hex (AI-13).

**Why this hasn't been fixed yet:** CONTEXT.md §9 explicitly notes the coupling concern; it was left as a "nicer but not critical" item.

---

## 6. App-Invariant / Accessibility Conflicts Found in Code

- **AI-11 drift — `app.py:425`:** `Qt.AA_ShareOpenGLContexts` uses the unqualified pre-PySide6-6 form. Should be `Qt.ApplicationAttribute.AA_ShareOpenGLContexts`. (See L-1.)

- **AI-13 adjacency — `appearance_panel.py:48`:** `border: 1px solid #888;` is short hex in a Qt stylesheet string. Qt accepts it, but it violates the project-wide "always 6-digit hex" convention. Not a runtime error; cosmetic inconsistency. (See L-2.)

No other invariant violations found. The codebase is clean on AI-2 (no pytest-qt), AI-4/AI-5 (scalar clipping, `scalars=` kwarg correctly used in `view_panel.py:390`), AI-6 (implicit vs parametric pipelines respected), AI-7 (Hanson normals `consistent_normals=False` in `surfaces.py:583`), AI-9 (re-entrancy guard present in `app.py:271–273`), AI-12 (all text tokens in `styles.py` clear WCAG AA), AI-13 (all colors into PyVista are 6-digit hex in `app.py:360,382`), AI-14 (generator contract uniformly respected), AI-15 (honest "real shadow" disclaimers in all tooltips including Fano 3-fold novelty disclaimer).

---

## 7. What the App Does Well Visually

- **Rich tooltip discipline across all 14 surfaces.** Every dropdown item carries `Qt.ItemDataRole.ToolTipRole` set from `VARIETY_TOOLTIPS` / `SUBTYPE_TOOLTIPS` in `app.py:179–182`. Tooltips include the defining equation (unicode super/subscripts), symmetry group, and primary reference — a level of math-rigor that peers like GeoGebra and MathMod rarely match in their UIs.

- **Honest "real shadow" disclaimers where the genuine variety can't live in ℝ³.** The CY3 and Fano 3-fold panels each show a context banner (via `parameters_panel.set_context_hint`) explaining that figures are 2D parametric or real-slice shadows of 6-real-dimensional manifolds — not the varieties themselves. This is exactly what AI-15 requires and what most visualization tools omit.

- **WCAG AA contrast on every text token in `styles.py`.** `COLOR_MUTED = #5a5a5a` (5.4:1 on `#f0f0f0`), `COLOR_VALUE = #333333` (high contrast), focus ring `#5b9bd5` visible. The earlier `#888` (3.5:1 — AA fail) was explicitly replaced.

- **Busy cursor + status-bar pipeline feedback.** `[INT-3 busy-cursor]` and `[INT-4 status-bar-feedback]` are both implemented: `QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)` in `app.py:275` + status bar showing mesh stats (vertex/face count + current parameter values) after every render. This is a 2026 standard that many research tools skip.

- **Centralized stylesheet with no scattered inline hex.** `styles.py` exports named constants (`HEADING_STYLE`, `MUTED_TEXT_STYLE`, `VALUE_MONO_STYLE`, `RANGE_LABEL_STYLE`) that all panel files import. No panel file hard-codes a color value (only the two noted AI-13/AI-11 anomalies). This is a maintenance quality that survives theming changes.

- **Adaptive sampling bounds per generator.** The Fermat quartic, Kummer surface, and other implicit surfaces all compute their marching-cubes box adaptively from the current parameter values (`surfaces.py:214–218`, `surfaces.py:283–284`) so arms and features always fit — a detail most academic Python surface renderers omit, leaving users with clipped-off geometry.

---

## 8. Themes

The dominant theme is **visual monotony despite content richness**: 14 mathematically distinct surfaces from four variety families all launch with the same steel-blue color and white background, making the gallery feel like one surface in fourteen poses rather than four mathematically distinct families. A per-variety color palette (H-2) and dark-mode toggle (H-1) together would transform the first-launch impression.

The second theme is **input fidelity vs. research workflow**: the slider-only parameter input (H-3) makes the app comfortable for exploration but awkward for reproducibility (exact parameter values matter in papers — ψ = 1.0001 is not ψ = 1.0). A spin-box alongside each slider is a low-complexity, high-value upgrade.

The third theme is **missing desktop-app chrome**: no menu bar (M-6), no mesh export (M-2), no dark mode (H-1) — three gaps that are individually small but together signal "research prototype" to a 2026 desktop-app user accustomed to ParaView or Blender. Each is a well-scoped addition that doesn't touch the core render pipeline.
