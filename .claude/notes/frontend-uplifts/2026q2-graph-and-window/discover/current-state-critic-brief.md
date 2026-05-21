# Current-State Critic Brief — 2026 Q2 Graph and Window

**Agent:** current-state-critic
**Date:** 2026-05-21
**Scope:** Tier-1 panel-chrome shakedown — balanced critique of 3D plot rendering AND Qt panel chrome / window frame / dock layout / styles. Primary evidence: panel PNGs captured via `render-panel-chrome.py` + off-screen surface renders from the `2026q2-panel-refresh` render archive + full codebase read.

---

## 1. Executive Summary

The Algebraic Variety Viewer is a carefully engineered PySide6 + PyVista app with genuine WCAG AA compliance, rich math-honest tooltips, and a clean centralized stylesheet. Against 2026 scientific-viz desktop-tool standards, six gaps stand out. On the **3D plot side**: the Fermat quartic default render shows a generic rounded cube — at default parameters (α=β=γ=0, c=1) the surface is visually indistinguishable from a superellipsoid and gives no geometric "hook" to engage the viewer; and the Enriques canonical sextic node-closeup reveals severe white zipper seam artifacts at double-curve intersections that render the surface's most mathematically interesting feature (its singular locus) as a visual defect rather than a structural cue. On the **panel chrome side**: every panel in the off-screen PNGs has no dock header — only the group-box level of hierarchy is visible in isolation, which means the dock title bars that the `styles.py` QSS carefully styles (`COLOR_DOCK_HEADER_BG = #e8edf2`, 1px border) are completely invisible in the panel PNGs and therefore unverifiable as critique targets without a live session; the View panel's disabled controls in the Off/clip state (greyed Radius slider, greyed "Show clip outline") are barely distinguishable from their enabled peers; the "Reset all to defaults" button is visually separated from the sliders it controls by a layout gap that makes the affordance ambiguous on first inspection; and the entire app has no dark-mode stylesheet despite the VTK canvas already defaulting to dark grey — a mismatched chrome that ships every session.

---

## 2. Critical Gaps

None. At all default parameter values, every generator in `VARIETIES` produces a non-empty mesh, no load-bearing contrast token fails WCAG AA, and no dock is broken or unreachable. The threshold for CRITICAL is a credibility failure on first launch; the gaps below erode quality but none prevent use.

---

## 3. High Gaps

### H-1 — 3D Viewport: default Fermat quartic render is visually uninformative at α=β=γ=0

**Severity:** HIGH

**Affected files / panels:** `surfaces.py:243–252` (`FERMAT_PARAMS` — all four sliders default to zero deformation: `alpha=0.0, beta=0.0, gamma=0.0, c=1.0`). `app.py:374–379` (no post-render camera hint or annotation). The off-screen render `k3-surface-fermat-quartic-default.png` confirms: the first-launch surface is a featureless rounded cube with no axes-arms, no distinctive K3 geometry, and no visual cue that mathematical structure exists.

**App-invariant / accessibility conflicts:** None — the generator is correct. This is a UX default-parameter gap, not a pipeline bug. AI-8 (Surface/ParamSpec contract) is intact.

**What 2026 SOTA expects:** Mathematica's `Manipulate` examples, MathMod's gallery, and 3D Slicer's sample-data browser all default to a configuration that immediately communicates the object's character. For a K3 surface, the mathematically expressive regime starts at `gamma ≈ -5` (where the six axial arms extend visibly) or `c=8` (larger rounded octahedron revealing the corner puckers). The `Elegant Universe`-adjacent Calabi–Yau image on first launch (`calabi-yau-3-fold-hanson-quintic-default.png`) shows exactly this — a complex, immediately arresting geometry. The Fermat quartic default is a missed opportunity to communicate the variety's richness.

**What a credible v1 fill-in looks like:** Change the Fermat quartic `FERMAT_PARAMS` defaults from `(alpha=0, beta=0, gamma=0, c=1)` to a more visually distinctive starting configuration, such as `(alpha=-0.5, beta=0.0, gamma=-3.0, c=1.5)` — this produces the classic six-armed K3-family star shape immediately recognizable from the algebraic-geometry literature (Beauville) without any slider movement. Alternatively, retain the mathematically canonical α=β=γ=0 defaults but add a "Featured view" preset to the View panel that snaps to the expressive configuration. Either path is ~2 lines in `surfaces.py`. The second approach respects the "research tool is not prescriptive" principle more cleanly.

**Why this hasn't been fixed yet:** The FERMAT_PARAMS defaults were set during the initial math-correctness phase (Opus research agent, commit 1–3) where the primary concern was parameter-range validity, not first-impression aesthetics. The adversarial reviewer and UX passes focused on correctness gaps; no agent was tasked with "does the first-launch render communicate the surface's character?"

---

### H-2 — Qt chrome / dark-mode mismatch: VTK canvas is dark, Qt panels are light

**Severity:** HIGH

**Affected files / panels:** `styles.py:51` (`"BG_VIEWPORT": "#2f2f2f"` — VTK canvas is dark grey by explicit palette choice, applied in `appearance_panel.py:299`). `styles.py:183–254` (`APP_STYLESHEET` — dock headers, group boxes, labels, sliders, and the status bar are all styled for a light `#f0f0f0` Qt background). `app.py:427` (`app.setStyleSheet(APP_STYLESHEET)` — single light stylesheet). The panel PNGs confirm: the Qt chrome (white/light-grey panels, white group-box backgrounds, grey-on-white sliders) is starkly mismatched against the dark `#2f2f2f` VTK canvas. On screen the result is a dark rectangle surrounded by white panels — a contrast boundary that reads as two different applications sharing a window.

**App-invariant / accessibility conflicts:** AI-12 — any dark-mode text tokens must clear 4.5:1 on the dark background. `styles.py:62–63` already documents `TEXT_MUTED = #5a5a5a` fails on `BG_VIEWPORT` dark ground (measured 1.94:1) and flags it for UPL-4. No existing rule forbids adding a dark stylesheet.

**What 2026 SOTA expects:** ParaView (5.x), Blender (4.x), 3D Slicer (5.x), and Mathematica all present a unified dark chrome when their viewport background is dark. The viewport-dark / chrome-light split that the app currently ships is not the standard for any peer tool. `design-system.md §2` explicitly identifies this as a RECONSIDERABLE candidate and names `[INT-94 dark-mode-stylesheet]`.

**What a credible v1 fill-in looks like:** Add `APP_STYLESHEET_DARK` to `styles.py` alongside `APP_STYLESHEET`, providing a parallel palette (`BG_PANEL_DARK = "#1e1e1e"`, `BG_DOCK_HEADER_DARK = "#252525"`, `BORDER_DOCK_HEADER_DARK = "#3a3a3a"`, `TEXT_MUTED_DARK = "#a0a0a0"` which clears 4.5:1 on `#1e1e1e`). Apply it as the **default** stylesheet (not a toggle) since the viewport is already dark — the dark chrome is the coherent baseline, not the "optional" variant. A light-mode toggle in a future Help menu can flip back. This is the most bang-per-line change available: one `app.setStyleSheet(APP_STYLESHEET_DARK)` call in `main()` unifies the visual language immediately.

**Why this hasn't been fixed yet:** `styles.py:110–113` contains an explicit `UPL-4 placeholder marker` note deferring `PALETTE_DARK` to its own milestone. The single-developer cadence means the viewport-dark decision and the Qt-chrome-light decision were made at different times without a cross-panel reconciliation pass.

---

### H-3 — Enriques canonical sextic: white zipper seam artifacts at double curves are unaddressed

**Severity:** HIGH

**Affected files / panels:** `surfaces.py:317–344` (`enriques_figure_1` — the `F = x²y² + x²z² + y²z² + x²y²z² + c·xyz·(1+r²) = 0` surface has genuine double-curve singularities where two sheets approach zero separation). `app.py:374` (`plotter.add_mesh(clipped, smooth_shading=True, specular=0.3, specular_power=15)` — no `backface_culling` argument). The `enriques-surface-canonical-sextic-node-closeup.png` renders confirm: at the singular locus, marching cubes produces two facing near-degenerate triangles that render as alternating front/back faces under Phong shading, generating the jagged white zipper seam visible in both the default and 2x renders.

**App-invariant / accessibility conflicts:** AI-6 (implicit surface pipeline via marching cubes) — the geometry extraction is correct; this is a rendering-quality issue, not a pipeline bug. No invariant prevents adding `backface_culling=True` to `add_mesh`.

**What 2026 SOTA expects:** ParaView and VisIt both enable back-face culling by default on implicit surface renders, eliminating the inside-facing geometry at self-intersections. The Enriques sextic's S₄ symmetry group — the surface's defining mathematical property — is beautifully visible in the `k3-surface-kummer-surface-default.png` style of render; the white zippers erase that readability and replace the double curves (mathematically: the six edges of the coordinate tetrahedron) with visual noise. The 2026 SOTA reviewer would read these as rendering bugs rather than surface features.

**What a credible v1 fill-in looks like:** Pass `backface_culling=True` in `app.py:374`'s `plotter.add_mesh(...)` call. Alternatively (and more flexibly), expose a "Back-face culling" toggle checkbox in `appearance_panel.py`'s "Display" group (`appearance_panel.py:153–172`), defaulting to `True`. Wire through `apply_to_actor`. The toggle allows pedagogical use — turning off back-face culling to expose the sheet structure — while shipping a clean default. The toggle approach adds ~15 lines to `appearance_panel.py` and 2 lines to `apply_to_actor`.

**Why this hasn't been fixed yet:** The adversarial reviewer and remediation agent focused on parameter correctness and normal-vector consistency (AI-7 Hanson normals). The render quality of self-intersecting surfaces (Enriques is the only one in the gallery with genuine double curves) was not a review target. CONTEXT.md §9 does not list this gap.

---

## 4. Medium Gaps

### M-1 — View panel: disabled-state controls are visually ambiguous in "Clip Off" mode

**Severity:** MEDIUM

**Affected files / panels:** `view_panel.py:305–315` (`_update_domain_controls_enabled` — when domain mode is "Off", `self._radius_slider`, `self._radius_value`, `self._radius_label`, and `self._domain_overlay_cb` are all `setEnabled(False)`). The panel PNG `view-light-empty-default.png` confirms: the greyed Radius slider, label, and checkbox are present but the contrast between enabled and disabled states is subtle — the Qt platform's default disabled-text color (`#aaaaaa` per `styles.py:64` `TEXT_DISABLED`) is visible but the slider rail itself barely changes and the checkbox border remains the same.

**App-invariant / accessibility conflicts:** AI-12 — `TEXT_DISABLED = #aaaaaa` on `#f0f0f0` is 2.32:1 (intentionally below WCAG AA per the `styles.py:64` comment: "intentional low contrast per WCAG exception"). This exception is documented and defensible for disabled widgets. However the *slider rail* has no explicit disabled styling in `APP_STYLESHEET` — it falls back to the Qt platform default, which on macOS renders as a nearly-identical blue gradient.

**What 2026 SOTA expects:** ParaView and 3D Slicer use both opacity reduction AND a visual indicator (e.g. a "requires X to activate" tooltip or a subdued icon) to signal that a control group is conditionally active. The View panel in "Clip Off" mode shows active-looking slider rail chrome alongside disabled-looking text labels — a mixed signal that a first-time user may interpret as a bug ("why can't I drag this?").

**What a credible v1 fill-in looks like:** Add a `QSlider:disabled` rule to `APP_STYLESHEET` in `styles.py` that explicitly desaturates the slider groove: `QSlider:disabled::groove:horizontal { background: #d0d0d0; }`. This ensures the disabled rail is visually consistent with the disabled label text and checkbox. Alternatively, collapse the radius slider's entire layout row to zero height when domain mode is "Off" (show/hide rather than enable/disable). The show/hide approach is cleaner for a control that is genuinely not applicable, but requires restructuring the `_update_domain_controls_enabled` method slightly.

**Why this hasn't been fixed yet:** The disabled-state styling is inherited from the Qt platform default, which is "good enough" on most themes. The `styles.py` QSS only explicitly styles enabled states; disabled states were not part of the UPL-1 palette audit scope.

---

### M-2 — Parameters panel: "Reset all to defaults" button placement is ambiguous

**Severity:** MEDIUM

**Affected files / panels:** `parameters_panel.py:60–67` (`self._reset_btn` is added to `self._root` directly after `self._content_layout` spacer, at the bottom of the panel). `parameters_panel.py:69–71` (an expanding `QSpacerItem` is added AFTER the reset button). The populated panel PNG `parameters-light-populated-default.png` confirms: the "Reset all to defaults" button sits flush below the last slider's description text with no visual separator. The button is visually at the same depth as the slider rows — a user cannot immediately tell it is a panel-level action rather than a per-slider action.

**App-invariant / accessibility conflicts:** None. AI-9 (re-entrancy guard) — the `_reset_defaults` call resets all sliders and emits `params_changed`; the existing guard handles the re-render correctly.

**What 2026 SOTA expects:** Mathematica's `Manipulate` and ParaView's filter parameter panels separate "reset all" actions from per-parameter controls using either a visual separator line, a distinct button row with horizontal padding, or a placement inside a labeled section. The current layout buries the reset button in the flow of slider rows, violating the standard grouping heuristic (group controls by scope of action).

**What a credible v1 fill-in looks like:** Add a `QFrame` separator (`setFrameShape(QFrame.Shape.HLine)`, `setFrameShadow(QFrame.Shadow.Sunken)`) above the reset button in `parameters_panel.py:_build_ui`, placed between `self._content_layout` and `self._reset_btn`. This visually scopes "everything above = per-parameter" vs. "below = panel-level action". Alternatively, increase the margin above the reset button via `self._reset_btn.setContentsMargins(0, 12, 0, 0)` for a lighter touch. The separator approach more clearly communicates scope to a first-time user.

**Why this hasn't been fixed yet:** The reset button placement was established during the initial ParametersPanel build (before the UX pass) and was not independently critiqued. The UX agent pass (CONTEXT.md §6 Phase 5) focused on first-launch flow and parameter label clarity rather than within-panel action scoping.

---

### M-3 — View panel: "Export" group contains only "Screenshot..." — no mesh export affordance

**Severity:** MEDIUM

**Affected files / panels:** `view_panel.py:246–256` (`_make_screenshot_group` — returns a `QGroupBox("Export")` containing only a single `QPushButton("Screenshot…")`). The panel PNG `view-light-populated-default.png` confirms: a group box labeled "Export" with a single button is an underdelivered promise — the group name implies a broader set of export capabilities that don't exist.

**App-invariant / accessibility conflicts:** None. AI-10 (raw mesh is cached in `MainWindow._raw_mesh`) — mesh export is as simple as `self._raw_mesh.save(path)` at any time after a render. CONTEXT.md §9 explicitly notes "Adding STL/OBJ/PLY export is one line: `mesh.save('file.stl')`".

**What 2026 SOTA expects:** ParaView, MeshLab, and Blender all expose geometry export as a first-class action alongside screenshot. For a research tool, exporting the mesh to STL/OBJ for use in Blender renders, GeoGebra, or 3D printing is a common researcher workflow. The one-word "Export" group box title sets an expectation the single Screenshot button doesn't meet. Either rename the group to "Screenshot" or populate it with a mesh export button.

**What a credible v1 fill-in looks like:** Add an "Export mesh…" button to `_make_screenshot_group` alongside the screenshot button. Wire via a `get_mesh` callback on `ViewPanel.__init__` (matching the `get_actor` / `get_plotter` pattern already on `AppearancePanel`). On click: `QFileDialog.getSaveFileName` with "STL / OBJ / PLY" filter → `mesh.save(path)`. If the mesh callback returns `None` (no surface rendered yet), disable the button. Total new code: ~20 lines in `view_panel.py` + 2 lines in `app.py` to pass the `get_mesh=lambda: self._raw_mesh` callback.

**Why this hasn't been fixed yet:** CONTEXT.md §9 explicitly lists this as a one-liner skip — it was never the priority item in any development pass, and the single-screenshot-in-an-Export-group is an inconsistency that accumulated during the initial View panel build.

---

### M-4 — Panel chrome: dock title bars are completely absent from panel PNG critique evidence

**Severity:** MEDIUM

**Affected files / panels:** `styles.py:183–196` (`APP_STYLESHEET` — `QDockWidget::title { background: #e8edf2; border-bottom: 1px solid #c5cdd8; padding: 4px 8px; font-weight: bold; font-size: 12px; text-align: left; }`). The `render-panel-chrome.py` script captures the three panel widgets in isolation — `AppearancePanel`, `ViewPanel`, `ParametersPanel` — but NOT inside `QDockWidget` wrappers. Therefore the panel PNGs show no dock title bar, no drag handle, no float/undock button. The carefully tokenized dock header styling is opaque to panel-PNG critique.

**App-invariant / accessibility conflicts:** This is a critique-coverage gap, not an application bug. AI-3 (no `MainWindow()` under offscreen) is the root constraint preventing a full-window capture; the `render-panel-chrome.py` design correctly stays within AI-3's bounds.

**What 2026 SOTA expects:** A Tier-1 panel-chrome shakedown that claims to assess dock chrome must actually see dock chrome. The `QDockWidget::title` rule is load-bearing visual identity — it is the only branded visual separator between the dock's tab (title) and its content panel. A critique that cannot see this rule in pixel form cannot verify it.

**What a credible v1 fill-in looks like:** Extend `render-panel-chrome.py` to wrap each panel widget in a `QDockWidget` before grabbing: `dock = QDockWidget("View"); dock.setWidget(view_empty); dock.resize(DEFAULT_SIZE); dock.show(); pix = dock.grab()`. Under `QT_QPA_PLATFORM=offscreen`, a bare `QDockWidget` (not embedded in `QMainWindow`) can be shown and grabbed without triggering AI-3's VTK GL segfault. This adds ~5 lines per panel to the capture script and produces dock-title-bar-inclusive PNGs. The fix is in `render-panel-chrome.py`, not in the application code.

**Why this hasn't been fixed yet:** The `render-panel-chrome.py` script was written in Phase 1a' of this uplift as a new artefact. The AI-3 constraint was correctly respected (no `MainWindow()`), but wrapping individual panels in bare `QDockWidget` wrappers was not considered as an intermediate option. This is a first-pass limitation of the capture harness.

---

### M-5 — 3D plot: single default VTK lighting setup shows poor surface differentiation on the Fermat quartic at default parameters

**Severity:** MEDIUM

**Affected files / panels:** `app.py:374–379` (`plotter.add_mesh(clipped, smooth_shading=True, specular=0.3, specular_power=15)` — the only lighting parameters set are `smooth_shading`, `specular`, and `specular_power`; no ambient/diffuse override, no multi-light rig). The `k3-surface-fermat-quartic-default.png` and `k3-surface-fermat-quartic-dark-bg.png` both show a surface with shallow, poorly differentiated shading — the dark-bg render is especially flat. The `calabi-yau-3-fold-hanson-quintic-default.png` by contrast is dramatically more legible under the same lighting because its geometry has strong curvature variation.

**App-invariant / accessibility conflicts:** None. PyVista's `add_mesh` supports `ambient`, `diffuse`, `specular` coefficients and multi-light rigs. The current call sets only `specular=0.3, specular_power=15` — ambient and diffuse default to VTK's global scene defaults.

**What 2026 SOTA expects:** ParaView and 3D Slicer both tune ambient + diffuse + specular per-material type. For a convex or near-convex surface like the Fermat quartic at default parameters, a slightly elevated ambient (0.15–0.20) + full diffuse (0.85) produces much better surface legibility than the default. The `appearance_panel.py` panel exposes Phong vs Flat shading toggle but no ambient/diffuse tuning — the researcher has no path to fix poor shading legibility from the UI.

**What a credible v1 fill-in looks like:** Set `ambient=0.15, diffuse=0.85` (alongside the existing `specular=0.3, specular_power=15`) in the `app.py:374` `add_mesh` call. This is a 2-parameter addition that noticeably improves the K3 surface legibility under the default dark viewport. Alternatively, expose an "Ambient" slider in the Appearance panel's Shading group — analogous to the existing opacity slider — to let the researcher tune the ratio. The hardcoded-default approach is lower risk (no new UI surface) and immediately improves first-launch quality.

**Why this hasn't been fixed yet:** The `add_mesh` call parameters were set in the initial architecture and not revisited during UX passes. Lighting tuning was not a target of any adversarial or remediation pass.

---

## 5. Low Gaps

### L-1 — View panel: "+X" button in preset grid has a focus outline visible in the panel PNG (first-tab-stop artifact)

**Severity:** LOW

**Affected files / panels:** `view_panel.py:119–123` (the `+X` button is constructed first in the preset grid and therefore receives keyboard focus on panel construction). `view-light-empty-default.png` confirms: the `+X` button is visually highlighted with a focus ring (visible as a blue outline on the button border) in the "empty" state capture — this is the Qt platform's default focus-on-first-interactive-widget behavior. The `APP_STYLESHEET` focus ring (`outline: 2px solid #5b9bd5`) is applied correctly, but in an off-screen capture context where no user has interacted with the panel, the first-focus-stop rendering gives the `+X` button a visually "selected" appearance that it would not have in normal app flow (where the dropdown combos receive initial focus).

**App-invariant / accessibility conflicts:** AI-12 — the focus ring is correct accessibility behavior. This is a capture-context artifact, not an application bug.

**What a credible v1 fill-in looks like:** In `render-panel-chrome.py`, after constructing `ViewPanel`, call `view_empty.setFocusPolicy(Qt.FocusPolicy.NoFocus)` on the panel (or call `view_empty.clearFocus()` before grabbing) to produce a focus-neutral capture. This is a one-line fix in the capture harness, not the application.

**Why this hasn't been fixed yet:** The capture harness is new; this is a first-pass artifact of how `_grab` calls `widget.show()` which triggers Qt's default focus assignment.

---

### L-2 — Appearance panel: color swatch for "Background" is black but viewport default is dark grey (#2f2f2f), not pure black

**Severity:** LOW

**Affected files / panels:** `appearance_panel.py:132–149` (`self._bg_swatch = _make_swatch(self._bg_color)` where `self._bg_color = QColor(BG_VIEWPORT)` and `BG_VIEWPORT = "#2f2f2f"`). `appearance-light-empty-default.png` confirms: the Background color swatch renders as a near-black square. At 20×20 pixels, the difference between `#2f2f2f` (dark grey) and `#000000` (pure black) is imperceptible — the swatch reads as black and a user who opens the color picker for the first time may be surprised that the starting color is dark grey rather than pure black.

**App-invariant / accessibility conflicts:** AI-13 (`#2f2f2f` is correctly 6-digit hex). AI-12 — the swatch does not display text, so contrast requirements do not apply.

**What a credible v1 fill-in looks like:** Add a tooltip to `self._bg_swatch` that reads `"Current background: {color_hex}"`, updated when `_bg_color` changes. The tooltip makes the exact color value discoverable without requiring the user to open the picker. Alternatively, add a small hex label below the swatch row — but that adds layout complexity. The tooltip is a 1-liner per swatch.

**Why this hasn't been fixed yet:** Swatches in color-picker UIs conventionally rely on the color itself as the affordance; no existing peer tool adds a hex label inline. This is genuinely minor.

---

### L-3 — Parameters panel description text runs very long at 320 px width, causing layout compression

**Severity:** LOW

**Affected files / panels:** `parameters_panel.py:174–178` (`if spec.description: desc = QLabel(spec.description); desc.setWordWrap(True)`). `parameters-light-populated-default.png` confirms: the `beta` description ("coeff of xyz(x+y+z) — breaks octahedral to tetrahedral symmetry; |β|>3 opens non-compact channels") wraps to 3 lines at 320px, and the `alpha` description ("alpha < -1 makes surface non-compact") wraps to 2 lines. At 320 px width, a 4-parameter surface takes ~520 px of panel height — taller than the initial dock sizing. On small screens, a 6-parameter surface (like the Fano two-quadrics CI tube with 4 params) would require scrolling before the reset button is visible.

**App-invariant / accessibility conflicts:** None. The `QScrollArea` wrapper in `appearance_panel.py:107–115` handles overflow correctly on the Appearance dock, but `ParametersPanel` has no `QScrollArea` wrapper — its `self._root` layout is not wrapped. On small screens with many parameters, the reset button could be pushed below the viewable area.

**What a credible v1 fill-in looks like:** Wrap `self._content_layout` in a `QScrollArea` in `ParametersPanel._build_ui` (analogous to the approach in `AppearancePanel._build_ui:107–115`). Alternatively, truncate description text to 80 chars with an ellipsis and show the full description in a tooltip (`desc.setToolTip(spec.description)`). The scroll-area approach is the robust fix for arbitrary parameter counts; the truncate approach is simpler but loses information.

**Why this hasn't been fixed yet:** At 4 parameters (K3/Fermat) the panel fits within 720 px — the current dock default. The issue only manifests with longer descriptions or more parameters. No surface currently exceeds 5 parameters, so this hasn't been triggered in practice.

---

### L-4 — Panel chrome: group-box borders and background are visually identical to the panel body at the default Qt light theme

**Severity:** LOW

**Affected files / panels:** `styles.py:197–210` (`QGroupBox { border: 1px solid #d0d0d0; border-radius: 4px; }` applied globally). `PALETTE_LIGHT["BG_PANEL"] = #f0f0f0`. The panel PNGs confirm: `QGroupBox` borders (`#d0d0d0` on `#f0f0f0` background) have very low contrast — the group-box hierarchy is visible but subtle. On a physical monitor with any display backlight variation or ICC profile shift, the borders may disappear entirely. The group-box title (bold, 11px) is the dominant visual cue rather than the border.

**App-invariant / accessibility conflicts:** AI-12 — WCAG AA applies to text, not to non-text UI elements like group-box borders. For non-text UI components, WCAG 2.1 §1.4.11 (Non-text Contrast) requires 3:1 minimum. `#d0d0d0` on `#f0f0f0` is ~1.3:1 — a Non-text Contrast fail under WCAG 2.1 §1.4.11 (AA). Note: `app-invariants.md AI-12` cites WCAG 2.1 AA text contrast; the non-text contrast requirement is a separate standard that has not been audited.

**What a credible v1 fill-in looks like:** Darken `BORDER_GROUP_BOX` in `PALETTE_LIGHT` from `#d0d0d0` to `#b8b8b8` or `#aaaaaa`. `#aaaaaa` on `#f0f0f0` is ~2.7:1 — still below 3:1 but noticeably more legible. To clear 3:1, use `#999999` on `#f0f0f0` (3.00:1 exactly). This is a one-token change in `styles.py:77`.

**Why this hasn't been fixed yet:** The `tests/test_styles_palette.py` WCAG audit covers text-contrast tokens only (per `styles.py:58–59` comments). Non-text contrast (WCAG §1.4.11) was not in scope when the palette was written.

---

## 6. App-Invariant / Accessibility Conflicts Found in Code

- **AI-11 drift — `app.py:429`:** `QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)`. The fully-qualified form is `Qt.ApplicationAttribute.AA_ShareOpenGLContexts`. The shorthand works via backward-compat alias but emits a PySide6 deprecation warning. (Also caught by the `2026q2-panel-refresh` critic — still present in the worktree codebase.)

- **WCAG 2.1 §1.4.11 Non-text Contrast gap — `styles.py:77`:** `BORDER_GROUP_BOX = #d0d0d0` on `BG_PANEL = #f0f0f0` is ~1.3:1 — below the 3:1 minimum for non-text UI components. Not covered by the AI-12 text-contrast invariant or the existing `test_styles_palette.py` suite.

- **No explicit `QSlider:disabled` styling — `styles.py:183–254`:** The `APP_STYLESHEET` does not provide a disabled-state rule for `QSlider`, leaving the disabled clip-radius slider's groove appearance platform-dependent. On macOS the groove remains visually active-looking (blue rail), confusing the enabled/disabled signal.

No other invariant violations found. AI-2, AI-4/AI-5, AI-6, AI-7, AI-9, AI-10, AI-12 (text), AI-13, AI-14, and AI-15 are all clean in the current worktree codebase.

---

## 7. What the App Does Well Visually

- **Panel PNGs confirm the design-system discipline holds end-to-end.** Every group-box title, slider label, value readout, and range label uses the correct style token (`HEADING_STYLE`, `VALUE_MONO_STYLE`, `RANGE_LABEL_STYLE`). No scattered inline hex values appear in the offscreen-rendered panels. The UPL-1 palette tokenization from the prior milestone is structurally sound.

- **The Calabi–Yau Hanson quintic default render is immediately arresting and communicates complex topology on first view.** The `calabi-yau-3-fold-hanson-quintic-default.png` and dark-bg variant show a surface with clear multi-patch structure, visible concavities, and interesting silhouette — exactly the kind of visual hook that makes a research tool memorable. This is the app's best first-impression surface.

- **Slider layout in the populated Parameters panel is clean at 320 px.** The 4-slider K3/Fermat quartic layout (`parameters-light-populated-default.png`) shows consistent vertical rhythm, readable range-label min/max markers, and a legible value readout. The `MUTED_TEXT_STYLE` description text is correctly subordinated beneath the slider — the visual hierarchy within each slider row is well executed.

- **The "Reset all to defaults" button is correctly styled as a secondary-destructive action.** The pink `BG_RESET_BTN = #f5e8e8` background with dark-reddish `TEXT_RESET_BTN = #5a3a3a` clearly signals "this resets state" without the alarm-red of a primary destructive button. The 8.37:1 contrast ratio exceeds WCAG AA. This is a design detail that many research tool UIs get wrong.

- **The View panel's domain-clip group degrades gracefully.** When domain mode is "Off" (`view-light-empty-default.png`), the disabled Radius slider and "Show clip outline" checkbox are visually subdued without disappearing — the user can see what controls exist before activating them. This is preferable to the common anti-pattern of hiding inactive controls entirely.

- **The Enriques surface renders at non-default parameters demonstrate sophisticated geometry.** The `enriques-surface-canonical-sextic-default.png` full-frame render shows a surface with genuine self-intersecting sheet structure and clear tetrahedral symmetry — even with the white seam artifact noted in H-3, the geometric content is legible and compelling to a math-educated viewer.

---

## 8. Themes

The dominant theme across both the 3D plot and chrome gaps is **incomplete visual coherence between the VTK canvas and the Qt chrome**: the viewport is dark by deliberate choice, but the surrounding Qt panels remain light-themed, creating a split-personality chrome that no peer tool (ParaView, Blender, 3D Slicer) ships. H-2 and H-1 together make the case that the app's first-launch impression — a feature-neutral rounded cube floating in a dark frame surrounded by white panels — is the weakest moment of an otherwise strong tool.

The second theme is **render quality gaps at mathematically interesting features**: the Enriques white-seam artifact (H-3) and the Fermat quartic default-parameter flatness (H-1) both concern the app's handling of exactly the surfaces where mathematical structure is richest. The app's most faithful renders (CY3 Hanson quintic, Kummer surface) happen to have geometry that renders well under default parameters; the surfaces that need the most rendering care (Enriques singular locus, Fermat arms) get the least.

The third theme is **chrome gaps that are one-layer beneath critique reach**: the dock title bars (M-4) and disabled-state slider styling (M-1) are both places where the `APP_STYLESHEET` has correct intent but either the capture harness or the Qt platform defaults leave a verification gap. These are low-risk to fix but require extending the audit surface to catch.
