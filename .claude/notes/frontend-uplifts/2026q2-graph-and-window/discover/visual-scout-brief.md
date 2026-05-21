# Visual Scout Brief — 2026q2-graph-and-window
**Run date:** 2026-05-21  
**Uplift scope:** Tier-1 panel-chrome shakedown — surface gaps in BOTH the 3D plot rendering AND the Qt panel chrome / window frame / dock layout / styles.  
**Surfaces rendered:** 4 (default 5-surface set minus synthetic app-startup)  
**Panel PNGs inspected:** 12 (3 panels × empty/populated × default/2x, LIGHT theme only)  
**Render directory:** `.claude/notes/frontend-uplifts/2026q2-graph-and-window/renders`  

---

## 1. TL;DR

The three highest-priority visual gaps are: (1) every surface shares the same uniform `#9aa6c8` / `#b0c4de` slate — no variety-family color cue — making the Fermat quartic render visually indistinguishable from the Hanson quintic until you read the status bar; (2) the Enriques canonical sextic carries visible sawtooth tear-artifacts along its internal singular node lines at default parameters and camera, a marching-cubes resolution deficit that reads as a broken render on first view; (3) the viewport renders against a pure-white PyVista default background in the off-screen captures, which severely undercuts depth and depth-of-field legibility — the app's intended dark viewport (`#2f2f2f`) is a major visual upgrade that this run's renders do not reflect. Overall visual-coherence rating across surfaces: **6 / 10** — the geometry is mathematically correct and smoothly lit for 3 of 4 surfaces, but the flat color palette and the Enriques artifact pull the suite below a "polished scientific tool" baseline. The main theme is: **color differentiation and background contrast are the two highest-leverage improvements** that affect every surface equally.

---

## 2. Per-Surface Observations

### 2.1 app-startup (synthetic — no render captured)

**First-launch state (from `app.py:_PLACEHOLDER` + `styles.py:APP_STYLESHEET`):**  
The app opens with a window title "Algebraic Variety Viewer" at 1200×800. The central `QtInteractor` widget is empty, background color `#2f2f2f` (dark grey — applied by `appearance_panel.apply_background()` in `MainWindow.__init__` after UPL-3). The status bar shows "Choose a variety to begin." in `COLOR_MUTED = #5a5a5a` at 11px. The variety combo shows `— Select —`; the model combo is disabled. The three docks are populated but the Parameters dock shows "(no parameters for this surface)" with a disabled "Reset all to defaults" button.

**Gaps found:**
- The `— Select —` cascade has no first-launch affordance directing attention to the dropdowns. An empty dark viewport with no label annotation provides no entry-point for a first-time user. (design-system.md §7 "First-launch tour" candidate)
- The "Choose a variety to begin." status-bar text is small (`11px`, `#5a5a5a`) and placed at the very bottom edge of a 1200×800 window — low discoverability.

---

### 2.2 K3 surface / Fermat quartic

**Renders:** `renders/k3-surface-fermat-quartic-default.png`, `renders/k3-surface-fermat-quartic-2x.png`

At default parameters (α=0, β=0, γ=0, c=1) the surface is a smooth, rounded cube-like shape — correct for the zero-parameter Fermat quartic deformation `x⁴+y⁴+z⁴=1`. Taubin smoothing is effective: the rounded-octahedron topology is visible and well-formed, no stray triangles. The `#9aa6c8` slate with Phong shading reads clearly against white background; the specular highlight on the top face is natural. The 2x render confirms clean edge anti-aliasing.

**Visual concerns:**
- The shape is visually indistinct from a generic rounded cube — no topology annotation (corner count, symmetry group label) on the canvas helps the user connect "Fermat quartic" to "cubic symmetry." This is expected design scope, not a bug.
- Against white background the surface reads well, but the intended app context is `#2f2f2f` dark background — on dark bg the `#9aa6c8` slate performs better (higher luminance contrast). The off-screen render with white bg is not a faithful representation of the app's default look.
- No camera-angle orientation is shown (no world-axes triad, no reference lines). The default isometric camera is reasonable but unnamed.

**Gaps found:**
- Uniform slate color — same hue as all other surfaces (MEDIUM — cross-surface pattern)
- White background in off-screen render does not reflect dark-bg default (LOW — capture artifact, not a product bug)

---

### 2.3 K3 surface / Kummer surface

**Renders:** `renders/k3-surface-kummer-surface-default.png`, `renders/k3-surface-kummer-surface-2x.png`

The Kummer surface at default μ²=1.5 shows four conical singularity nodes (the "double points") meeting at a central region, with four saddle wings extending outward. This matches the expected Hudson tetrahedral form: four pointed cones with concave inner faces connecting at the center. Phong shading picks out the concave surfaces very well — dark inner faces contrast with brighter wing surfaces, giving depth. The 2x render confirms smooth normals on the wing faces; no triangulation artifacts visible at 2x.

**Visual concerns:**
- The central crossing region where four nodes meet shows some self-intersection visual noise — small dark slivers where inner surfaces intersect. This is geometrically expected (the surface is genuinely singular there) but visually reads as a render artifact to a non-expert.
- The slate color `#9aa6c8` works slightly less well here than on the Fermat quartic: the concave faces get very dark under default lighting, losing detail in those regions. A warmer or slightly more saturated hue would maintain detail on concave faces.

**Gaps found:**
- Concave-face shading loss under default lighting (LOW — lighting setup is a cross-surface issue)
- Uniform slate — same color as Fermat quartic, no variety-family distinction even within K3 (MEDIUM — cross-surface pattern)

---

### 2.4 Enriques surface / Canonical sextic [Fig. 1]

**Renders:** `renders/enriques-surface-canonical-sextic-default.png`, `renders/enriques-surface-canonical-sextic-2x.png`

The canonical sextic at default c=0 renders with three-fold symmetry — a flat triangular dish with three concave triangular "cells" separated by internal edge lines and three exterior pointed wings. The overall shape matches the expected canonical sextic geometry (Enriques 1896 / Cossec–Dolgachev). However, the internal seams carry severe sawtooth tearing artifacts: along the lines where the level-set has near-zero gradient (the node loci), the marching-cubes triangulation produces jagged saw-tooth edges clearly visible in both default and 2x renders. The 2x render (`.../enriques-surface-canonical-sextic-2x.png`) shows the artifacts more clearly — white zigzag lines along what should be smooth internal creases, plus dark pixel "dots" along the outer perimeter of each wing.

**Gaps found:**
- Sawtooth/zigzag artifacts along internal singularity node lines (HIGH — geometry defect visible at default view)
- Outer wing perimeter shows dark pixel dots from marching-cubes boundary — the mesh hits the sampling box boundary leaving open polygon edges visible (MEDIUM)
- No visual indication that this is a "degree-6 real shadow birational to Enriques" vs. a degree-6 surface in P³ — the relationship is only in the tooltip, not the canvas (LOW — educational scope)

---

### 2.5 Calabi–Yau 3-fold / Hanson quintic [Fig. 1]

**Renders:** `renders/calabi-yau-3-fold-hanson-quintic-default.png`, `renders/calabi-yau-3-fold-hanson-quintic-2x.png`

The Hanson quintic at default parameters (α=0, ξ_max=0.9, grid=41) shows 25 parametric patch lobes arranged in a 5×5 radial flower/spiky-ball pattern — the iconic image from the *Elegant Universe* cover. Phong shading over the parametric patches works well: the convex lobes are bright, the concave inter-lobe cusps are dark, giving excellent three-dimensional read. The 25 patches are correctly assembled with `cell_normals=True, consistent_normals=False` (AI-7) — no per-patch lighting flips are visible in this view.

**Visual concerns:**
- The patch boundaries between adjacent lobes are visible as thin seam lines in the 2x render. These are expected (25 disconnected PolyData components) but read as stitching seams. In 1x they're nearly invisible; at 2x they become a texture-like fine grid overlay.
- Same uniform slate `#9aa6c8` — no CY3-family color distinction from K3 or Enriques.
- The camera view from the default isometric angle shows the full ball-of-spikes, but the most visually striking angles (looking down a 5-fold axis, or at 45° elevation) are not the default. A math-savvy user will find this by rotating; a newcomer may not.

**Gaps found:**
- Patch seam lines visible at 2x (LOW — expected geometry; `cell_normals=False` fix already applied, AI-7)
- Uniform slate — no CY3-family color distinction (MEDIUM — cross-surface pattern)
- Default camera does not reveal 5-fold axial symmetry — the icosahedral-style view would be more informative (LOW — camera-default quality of life)

---

## 3. Critical Gaps

No CRITICAL gaps found. All four generators returned valid meshes at default parameters. No segfault, no empty mesh, no ValueError at default parameters.

---

## 4. High Gaps

### H-1: Enriques canonical sextic — sawtooth tear artifacts along internal node lines

**Gap name:** Sawtooth marching-cubes tear artifacts at singularity loci

**Surface(s) affected:** Enriques surface / Canonical sextic [Fig. 1]

**Render evidence:** `renders/enriques-surface-canonical-sextic-default.png`, `renders/enriques-surface-canonical-sextic-2x.png`

**What the user sees:** When the Enriques canonical sextic is selected, the three internal "cell junction" lines — where adjacent face patches of the level set nearly coincide (the equation `x²y²+x²z²+y²z²+x²y²z²+c·xyz·(1+x²+y²+z²)=0` at c=0 has very shallow gradient near the three internal ridges) — render as jagged sawtooth white-zigzag seams. These run for roughly 1/3 of the total visible surface width. The 2x render makes these look like torn paper edges; at 1x they look like aliasing, which many users will interpret as a broken renderer rather than an expected mathematical feature of a surface with a triple-point node locus. Additionally, the outer perimeter of each of the three triangular wing tips shows dark pixel dots — mesh triangles whose edges touch the sampling box boundary and are left as open polygons.

**What a 2026 SOTA scientific-viz app would do:** ParaView and 3D Slicer both apply adaptive surface refinement near detected high-curvature regions; Mathematica's `RegionPlot3D` uses implicit-function-aware marching cubes with a narrower band near the zero crossing. For this app the near-term upgrade is to increase the marching-cubes grid resolution specifically for the Enriques sextic (or to add a RuntimeWarning like Dwork-conifold: [INT-70 status-warning-prefix]) so the user understands the artifact is a sampling limitation, not a renderer bug. A VTK canvas text overlay annotation [INT-74 empty-clip-status-message] at the seam locations ("Node locus — marching cubes resolution limited here") would be the aspirational approach.

**Severity:** HIGH

**Closest existing app pattern:** `app.py:287–296` — RuntimeWarning capture and status-bar surfacing for the Dwork conifold warning. The same pattern can be applied to the Enriques sextic when c ≈ 0 (the singular locus is near maximum sharpness at c=0).

---

### H-2: No dark viewport background in surface renders — white background severely undercuts visual quality

**Gap name:** Off-screen renders use white PyVista default background instead of dark `#2f2f2f`

**Surface(s) affected:** All 4 surfaces (K3 Fermat, K3 Kummer, Enriques sextic, CY3 Hanson)

**Render evidence:** `renders/k3-surface-fermat-quartic-default.png`, `renders/k3-surface-kummer-surface-default.png`, `renders/enriques-surface-canonical-sextic-default.png`, `renders/calabi-yau-3-fold-hanson-quintic-default.png`

**What the user sees:** In the actual app, the viewport background is `#2f2f2f` (dark grey), set by `appearance_panel.apply_background()` called from `MainWindow.__init__` (UPL-3 fix). The slate `#9aa6c8` surface against dark grey gives 3.7:1 luminance contrast — readable, with natural depth cues. However, these off-screen renders used PyVista's white default background — the scout render script does not call `p.set_background(BG_VIEWPORT)`. This produces a fundamentally different visual experience: on white, the lighter regions of each surface (specular highlights, normal-facing areas) wash into the background, and the slate color reads as flat. The Kummer surface especially loses its concave-surface contrast on white. This is partly a scout-pipeline gap (renders should add `p.set_background("#2f2f2f")`) and partly a UPL issue: if any researcher screenshots or embeds these renders, they diverge from the real app appearance.

**What a 2026 SOTA scientific-viz app would do:** ParaView's default background is a medium-dark blue-grey specifically chosen for algebraic surface legibility; Blender's default render uses a neutral dark grey. The app already has the right default — the scout pipeline must match it. Adding [INT-80 solid-color-bg] `p.set_background(BG_VIEWPORT)` to the scout render loop is the one-line fix.

**Severity:** HIGH (for the scout pipeline; MEDIUM for the product if users find the white-bg option and use it)

**Closest existing app pattern:** `styles.py:BG_VIEWPORT = PALETTE_LIGHT["BG_VIEWPORT"] = "#2f2f2f"` and `appearance_panel.py:298–299` `self._get_plotter().set_background(self._bg_color.name())`.

---

## 5. Medium Gaps

### M-1: All surfaces share the same uniform `#b0c4de` / `#9aa6c8` slate — no variety-family color cue

**Gap name:** Uniform default surface color across all variety families

**Surface(s) affected:** All 4 surfaces

**Render evidence:** `renders/k3-surface-fermat-quartic-default.png`, `renders/k3-surface-kummer-surface-default.png`, `renders/enriques-surface-canonical-sextic-default.png`, `renders/calabi-yau-3-fold-hanson-quintic-default.png`

**What the user sees:** Every surface across K3, Enriques, and Calabi–Yau renders in the same cold steel-blue slate. Switching from the Kummer surface to the Hanson quintic produces no color change — the user's only cue that they've switched variety families is the dropdown text and the status bar message. In a research context where a user may be comparing two families visually (even just in memory between two navigation steps), the identical color erases one of the most immediate visual differentiators. The design-system.md §7 already names this as "UNDERDEVELOPED" and `styles.py` has `VARIETY_DEFAULT_COLOR: dict[str, str] = {}` as the ready placeholder for UPL-5.

**What a 2026 SOTA scientific-viz app would do:** Mathematica's built-in surface plots use a distinct color ramp per function family; 3Blue1Brown's manim library uses color explicitly as a mathematical identity signal. [INT-96 palette-template-per-variety] would give K3 surfaces a cool blue, Enriques surfaces a warm amber/ochre, CY3 Hanson a cobalt/teal, and Fano a deep violet — matching the math community's visual intuitions (K3 = mirror-symmetric cool; CY3 = Elegant Universe iconic).

**Severity:** MEDIUM

**Closest existing app pattern:** `styles.py:VARIETY_DEFAULT_COLOR = {}` (UPL-5 placeholder, `appearance_panel.py:82–83` `self._surface_color = QColor(BG_SURFACE_DEFAULT)`).

---

### M-2: Parameters panel — description text wrapping produces irregular row heights, compounding with multiple sliders

**Gap name:** Per-slider description text causes unequal row heights, making panel feel cluttered

**Surface(s) affected:** Parameters panel (all surfaces with description-bearing ParamSpec entries — K3 Fermat quartic visible in populated render)

**Render evidence:** `renders/panels/parameters-light-populated-default.png`, `renders/panels/parameters-light-populated-2x.png`

**What the user sees:** In the populated Parameters panel (K3 Fermat quartic, 4 sliders), each slider row contains: label + value readout → slider rail → min/max range labels → wrapped description text. The description lines for α ("coeff of (x²y²+y²z²+z²x²) — alpha < -1 makes surface non-compact") and β ("coeff of xyz(x+y+z) — breaks octahedral to tetrahedral symmetry; |β|>3 opens non-compact channels") are both long enough to wrap to two lines at 320px dock width. This produces rows with heights of 3+ lines while the Level c row (shorter description) is only 2 lines — giving the panel an uneven rhythm. The visual hierarchy is also compressed: description text uses `MUTED_TEXT_STYLE = font-size: 10px; color: #5a5a5a` and appears directly below the min/max labels (9px monospace), making the two look the same size in practice.

**What a 2026 SOTA scientific-viz app would do:** ParaView collapses parameter descriptions behind a "?" tooltip icon per control rather than always-visible text. [INT-7 tooltip-rich] is already used on slider `setToolTip(spec.description)`; the description text visible inline is redundant with the tooltip. Removing the always-visible description label (or making it a collapsed "?" disclosure button) would tighten vertical spacing by roughly 30% per described parameter, letting more sliders be visible without scrolling.

**Severity:** MEDIUM

**Closest existing app pattern:** `parameters_panel.py:174–179` — `if spec.description: desc = QLabel(spec.description)` always-visible block; `parameters_panel.py:150–153` — slider already has `setToolTip(f"{spec.label}\nRange: ...")` but not `spec.description`.

---

### M-3: View panel — "Reset Camera" button visually competes with preset-grid buttons due to inconsistent button styling

**Gap name:** Reset Camera button styling inconsistency vs. camera preset grid

**Surface(s) affected:** View panel (all surfaces)

**Render evidence:** `renders/panels/view-light-empty-default.png`, `renders/panels/view-light-populated-default.png`

**What the user sees:** The View panel has two visually distinct button groups: (a) the 7-button camera-preset grid (+X, -X, +Y, -Y, +Z, -Z, Isometric) using default `QPushButton` styling, and (b) the "Reset Camera" button which has `objectName("resetCameraBtn")` and is styled with a blue-grey border and transparent background (`BORDER_CAMERA_BTN = #b0bec5`, `BG_CAMERA_BTN_HOVER = #e8f0f5`). In the rendered panel, the "+X" button in the preset grid renders with a focus-ring blue outline (`FOCUS_RING = #5b9bd5`, 2px) — the focus state is sticky from the first `show()` call in the capture harness. This makes "+X" look like a "selected" preset (it is not), and the Reset Camera button's lighter border reads as a secondary or disabled control. A naive user may not perceive "Reset Camera" and the +X/+Y/+Z grid as sibling camera-preset actions.

**What a 2026 SOTA scientific-viz app would do:** ParaView groups camera presets under a single segmented-button row or toolbar with icons (front-view icon, top-view icon, etc.) and clearly separates "reset to default" from "set to named view." [INT-23 camera-preset-fire-and-render] is the right pattern; adding distinct button icons (even text glyphs like ↑ ↗ → ↘ ↓ for views) would reinforce grouping. The Reset Camera button belongs visually closer to the preset grid — or labeled as "Reset / Home" with a clear distinct background (not just a border).

**Severity:** MEDIUM

**Closest existing app pattern:** `view_panel.py` `_make_view_presets_group()` and `_make_camera_group()` are in separate `QGroupBox` sections; `styles.py:APP_STYLESHEET` — `QPushButton#resetCameraBtn` rule.

---

### M-4: Appearance panel — Opacity slider has no min/max range labels; opacity group is visually inconsistent with Parameters panel sliders

**Gap name:** Opacity slider lacks range-endpoint labels flanking the rail

**Surface(s) affected:** Appearance panel (all surfaces)

**Render evidence:** `renders/panels/appearance-light-empty-default.png`, `renders/panels/appearance-light-populated-default.png`

**What the user sees:** In the Parameters panel, every slider shows min/max range labels in 9px monospace below the rail (`RANGE_LABEL_STYLE`), flanking left and right — e.g. "0.1" left and "30" right for the Level c slider. The Appearance panel's Opacity slider shows only a centered "100%" (or "72%") value label below the rail, with no flanking range labels. A user switching back and forth between the two panels encounters different slider affordances and must infer that the Opacity slider goes from 0–100 (it is not labeled). The tick marks every 25 units provide a hint but no textual anchor.

**What a 2026 SOTA scientific-viz app would do:** Consistency is the minimal fix — add "0%" on the left and "100%" on the right below the rail, matching the RANGE_LABEL_STYLE used in ParametersPanel. This is a one-widget change. Alternatively, make the opacity slider a labeled `QDoubleSpinBox`-style control ([INT-97 parameter-spin-box-alternative]).

**Severity:** MEDIUM

**Closest existing app pattern:** `appearance_panel.py:180–193` `_build_opacity_group()` — `self._opacity_label = QLabel(f"{self._opacity}%")` is centered below the slider, no `RANGE_LABEL_STYLE` min/max labels. Contrast with `parameters_panel.py:160–170` which uses `range_row` with left/right QLabels.

---

### M-5: Parameters panel — empty-state "(no parameters for this surface)" is small, centered muted text; Reset button disabled — provides no next-action guidance

**Gap name:** Empty Parameters panel gives no affordance guidance

**Surface(s) affected:** Parameters panel — surfaces with no parameters (not in the default 5-surface set, but reached via the Fano 3-fold or any zero-param surface)

**Render evidence:** `renders/panels/parameters-light-empty-default.png`

**What the user sees:** The empty Parameters panel shows only "(no parameters for this surface)" in 10px muted text, centered, with a greyed-out "Reset all to defaults" button below. There is no label identifying which surface is displayed, no link to where parameters live (e.g. "Use the Appearance panel to change color and shading"), and no hint that this state is expected (as opposed to an error). The empty state occupies approximately 90% blank space.

**What a 2026 SOTA scientific-viz app would do:** Notion, Figma, and Linear all use "zero-state" panels with an icon + paragraph + action-button in the empty region. For this panel, a two-line copy such as "This surface has fixed geometry — use the Appearance panel to change color, opacity, and shading." would orient the user. This aligns with [INT-7 tooltip-rich] discipline and the CY3 context-hint banner pattern [INT-42 cy3-context-banner] already used.

**Severity:** MEDIUM

**Closest existing app pattern:** `parameters_panel.py:53–57` `self._empty_label = QLabel("(no parameters for this surface)")` — minimal empty state with no guidance. Contrast with `parameters_panel.py:44–47` `self._hint_label` (context-hint banner) which is the right pattern to extend.

---

## 6. Low Gaps

### L-1: Enriques canonical sextic — mesh hits sampling-box boundary, leaving visible open-edge dots on wing perimeters

**Gap name:** Mesh clips at sampling-box boundary, leaving open-edge artifacts on wing tips

**Surface(s) affected:** Enriques surface / Canonical sextic [Fig. 1]

**Render evidence:** `renders/enriques-surface-canonical-sextic-default.png` (outer wing-tip perimeters), `renders/enriques-surface-canonical-sextic-2x.png` (clearly visible dark dots)

**What the user sees:** The three wing tips of the canonical sextic extend to the edge of the marching-cubes sampling box. At the boundary, triangles that would continue beyond the box are left as open polygons — their exposed edges render as dark pixel rows (not true boundary curves, but silhouette edges from the truncated mesh). At 1x this looks like rough, pixelated wing-tip edges. At 2x the dots become individually visible triangular edge endpoints.

**What a 2026 SOTA scientific-viz app would do:** Expand the sampling box bounds by 10–15% for the Enriques sextic so the surface never clips, or apply PyVista `mesh.fill_holes(hole_size=1.0)` as a post-processing step. The adaptive-bounds pattern (already used for the Fermat quartic) should be extended to the Enriques models.

**Severity:** LOW (visible at 2x; at 1x it reads as a rough but tolerable edge)

**Closest existing app pattern:** `surfaces.py` — Fermat quartic uses adaptive bounds: `bounds = max(2.5, 1.15*sqrt(...) + 0.3)`. The Enriques generators use fixed bounds.

---

### L-2: View panel — Clip Region slider is not disabled when Shape is "Off"

**Gap name:** Radius slider visually active even when clip is off

**Surface(s) affected:** View panel — all surfaces

**Render evidence:** `renders/panels/view-light-empty-default.png` (radius slider shows thumb at 2.50 but the label "Radius" is greyed-out text)

**What the user sees:** In the empty View panel with Shape = "Off", the Radius slider shows a thumb at 2.50 with a grey-styled but still interactive-looking rail, while the label text "Radius" and "Show clip outline" checkbox are greyed out (disabled). The slider rail itself does not visually communicate disabled state — it retains the full blue accent track color. A user clicking the rail in this state gets no feedback (the slider value updates but has no effect). This is a minor inconsistency: the label is disabled but the widget itself is not.

**What a 2026 SOTA scientific-viz app would do:** Disable the slider widget itself (`slider.setEnabled(False)`) when clip mode is "Off" so the rail's platform-native disabled style applies (typically lighter, lower-contrast rail). [INT-2 slider-release-render] policy still applies — only the enabled/disabled state needs alignment.

**Severity:** LOW

**Closest existing app pattern:** `view_panel.py` `_on_domain_mode_changed()` — sets `self._radius_slider.setEnabled(...)` and `self._outline_cb.setEnabled(...)` but visual confirmation of slider rail disabled state depends on platform QSS.

---

### L-3: Focus ring on "+X" view-preset button in panel capture

**Gap name:** First view-preset button carries persistent focus ring in panel capture

**Surface(s) affected:** View panel chrome capture (capture harness artifact, not a product bug)

**Render evidence:** `renders/panels/view-light-empty-default.png`, `renders/panels/view-light-populated-default.png` — "+X" button has blue outline

**What the user sees:** In the view panel captures, the "+X" button shows a 2px blue outline (`FOCUS_RING = #5b9bd5`). This is the first focusable button in tab order and receives focus from `QWidget.show()` in the capture harness. The capture instruction notes this correctly (focus rings cannot be assessed from static captures). Assessing the focus ring from QSS: `QAbstractButton:focus { outline: 2px solid #5b9bd5; outline-offset: 1px; }` — the color `#5b9bd5` on panel background `#f0f0f0` is 2.60:1, which is below WCAG AA 3:1 for non-text UI components. This is a real product accessibility gap, surfaced here via the QSS source-of-truth fallback.

**What a 2026 SOTA scientific-viz app would do:** Darken the focus ring to `#3c82c4` (~3.1:1 on `#f0f0f0`) or `#2e75b6` (~4.1:1) to clear WCAG AA for UI components (3:1 required). This is already flagged in `styles.py:73` ("Flagged for UPL-4 / accessibility pass to darken to e.g. #3c82c4"). [INT-82 focus-ring-on-controls] — the ring is present but below contrast threshold.

**Severity:** LOW (accessibility gap; pre-flagged in palette commentary)

**Closest existing app pattern:** `styles.py:PALETTE_LIGHT["FOCUS_RING"] = "#5b9bd5"` and its comment "2.60:1 on BG_PANEL — see note."

---

### L-4: K3 Fermat quartic at defaults looks like a generic rounded cube — no visual topology cue

**Gap name:** Default-parameter Fermat quartic reads as a generic rounded cube, not an algebraic K3

**Surface(s) affected:** K3 surface / Fermat quartic

**Render evidence:** `renders/k3-surface-fermat-quartic-default.png`

**What the user sees:** At α=0, β=0, γ=0, c=1 the surface is an octahedral "puffed cube" with eight smooth faces and twelve rounded edges. There is nothing visually connecting it to K3 topology or the algebraic geometry concept — it could be any rounded cube. A researcher arriving at this app expecting the iconic K3 surface visuals (patterned like a torus, or complex cross-sectional structure) will be confused. The Kummer surface (which shares the K3 variety family) is more visually compelling and mathematically legible.

**What a 2026 SOTA scientific-viz app would do:** Set the default parameters to a more visually interesting default — for example α=-0.5 or β=1.0 introduces tetrahedral symmetry breaking that makes the surface look distinctly non-cubic. This is a `ParamSpec.default` change in `surfaces.py`. Alternatively, a status-bar annotation [INT-4 status-bar-feedback] could note "At default parameters, the Fermat quartic is equivalent to x⁴+y⁴+z⁴=1 (octahedral symmetry) — move sliders to explore deformations."

**Severity:** LOW (cosmetic; mathematical correctness is fine)

**Closest existing app pattern:** `surfaces.py` — Fermat quartic `ParamSpec` defaults (α=0, β=0, γ=0, c=1).

---

### L-5: Appearance panel — no "Surface with edges" display mode (only Wireframe / edges checkbox)

**Gap name:** Missing explicit "Surface + edges" named mode — edges toggle is a checkbox not a radio

**Surface(s) affected:** Appearance panel — all surfaces

**Render evidence:** `renders/panels/appearance-light-populated-default.png` — shows "Wireframe" checkbox checked and "Show edges" checkbox checked (two separate controls, not a three-way mode)

**What the user sees:** The Display group has two checkboxes: "Wireframe" and "Show edges." These are independent booleans in `appearance_panel.py:158–172`, meaning a user can check "Wireframe" and separately toggle "Show edges" (which is documented as inactive in wireframe mode). The intended three-way choice ("solid / wireframe / surface-with-edges") is not obvious from the two checkboxes; a user may attempt "Wireframe" + "Show edges" expecting a "wireframe with filled faces" (which is "surface-with-edges"). The current implementation silently ignores "Show edges" in wireframe mode (`if not self._wireframe: actor.prop.show_edges = checked`).

**What a 2026 SOTA scientific-viz app would do:** Use three radio buttons: Solid | Wireframe | Solid+Edges, matching [INT-44 style-radio-or-toggle]. The three-option exclusive choice (like the Shading group's "Smooth (Phong) / Flat" radio pair) is the right mental model for a mutually-exclusive style choice.

**Severity:** LOW

**Closest existing app pattern:** `appearance_panel.py:154–172` `_build_toggles_group()` — two checkboxes instead of three radios. Contrast with `appearance_panel.py:195–222` `_build_shading_group()` — correctly uses `QRadioButton` for the mutually-exclusive Phong/Flat choice.

---

## 7. Cross-Surface Patterns

### 7.1 Uniform color palette fails variety-family identification

Every surface in this run renders at `#9aa6c8` / `#b0c4de` lightsteelblue-slate. Switching between K3 / Enriques / CY3 produces identical surface color with only shape change. For a research tool, color is a cheap, persistent family identifier. The `VARIETY_DEFAULT_COLOR = {}` stub in `styles.py` and the `BG_SURFACE_DEFAULT` default in `AppearancePanel.__init__` are both ready for UPL-5 to populate. This is the highest-leverage single change that simultaneously affects all 4+ surfaces.

### 7.2 White viewport background in off-screen renders diverges from dark-bg app default

All surface renders were produced against PyVista's default white background. The app's intended default is `#2f2f2f`. This is a scout-pipeline gap (the render loop must add `p.set_background("#2f2f2f")`). The previous uplift (2026q2-panel-refresh, Lesson 2 in lessons.md) already surfaced this and the previous scout added dark-bg variants manually. For this uplift run the surface renders stayed on white; the gap should be fixed in the render loop for the next run.

### 7.3 No canvas-level mathematical annotations

All four surfaces render with zero on-canvas text — no equation overlay, no symmetry group label, no parameter-value annotation. The status bar carries the current parameter values and the surface name, but these are off-canvas. SOTA scientific-viz tools (ParaView's annotation filter, Mathematica's `Labeled[...]`, Blender's text overlays) typically put at least a title or equation on or near the canvas when the math is the point. This is aspirational ([INT-95 katex-tooltip-popover]) but worth noting as a consistent absence.

### 7.4 Panel chrome is correctly structured and readable

All three panels pass a basic chrome audit. Group boxes with titles provide clear section structure. Labels and value readouts use `VALUE_MONO_STYLE` / `RANGE_LABEL_STYLE` consistently in the Parameters panel. The dock-header styling (`COLOR_DOCK_HEADER_BG = #e8edf2`, 1px border) from `APP_STYLESHEET` is applied and visible. The "Reset all to defaults" button's pink-rose styling (`COLOR_RESET_BTN_BG = #f5e8e8`) correctly signals its secondary/destructive role. The context-hint banner in the populated Parameters panel wraps cleanly at 320px width.

### 7.5 Hanson patch boundary seams vs. Enriques marching-cubes tears — different severity

Both the Enriques sextic (HIGH: tear artifacts from near-singular gradient) and the Hanson quintic (LOW: patch seam lines at 2x) show surface-junction artifacts. However, their causes and severities differ: the Enriques artifacts are a marching-cubes sampling deficit on a near-zero-crossing band (fixable by wider bounds or grid-density increase); the Hanson seams are an expected consequence of assembling 25 disconnected parametric patches (no fix needed; AI-7 already applies the correct normal policy). Don't conflate these two patterns in synthesis.

---

## 8. What the App Does Well Visually

- **Phong shading is tuned correctly for these surfaces.** Kummer surface concavity and Hanson quintic lobe curvature both read clearly under default VTK lighting. The `smooth_shading=True` call in the off-screen renders and the `actor.prop.interpolation = "Phong"` default produce gloss-appropriate highlights without looking plastic.

- **Taubin smoothing on implicit surfaces is effective.** The Fermat quartic and Kummer surface have no visible marching-cubes triangulation noise at 1x — the `smooth_taubin(n_iter=20, pass_band=0.1)` pass removes facet artifacts without volume shrinkage. This is superior to Laplacian smoothing which would shrink the geometry.

- **Panel chrome hierarchy is coherent.** Group box titles, slider labels (12px), value readouts (11px monospace), range labels (9px monospace), and description text (10px muted) form a clear size-weight descending hierarchy. The eye finds the slider name before the value before the range before the description — the right reading order.

- **Reset-to-defaults button is visually distinct.** The pink-rose `#f5e8e8` background for `#resetDefaultsBtn` reads as "secondary / potentially destructive" relative to the neutral default push buttons. Users accustomed to destructive-action conventions will pause before clicking, which is the right affordance for a "wipe all slider positions" action.

- **The Parameters panel populated state is information-dense but not overwhelming.** Four sliders with labels, value readouts, range markers, and descriptions fit in 320px × ~450px without clipping or requiring scroll at default dock height. The layout discipline (`SMALL_LABEL_STYLE`, `VALUE_MONO_STYLE`, `RANGE_LABEL_STYLE`, `MUTED_TEXT_STYLE`) prevents the panel from collapsing into visual noise.

- **Geometry correctness across all 4 surfaces at default parameters.** All four generators returned valid meshes (42K–400K faces) with no ValueError, no empty mesh, and no segfault. The mathematics is correctly implemented and the surfaces are topologically recognizable by an expert viewer.
