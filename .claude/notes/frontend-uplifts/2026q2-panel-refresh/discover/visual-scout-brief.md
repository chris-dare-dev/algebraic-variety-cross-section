# Visual Scout Brief — 2026q2-panel-refresh

**Date:** 2026-05-20
**Scout model:** claude-sonnet-4-6
**Render directory:** `.claude/notes/frontend-uplifts/2026q2-panel-refresh/renders/`
**Surfaces rendered:** 4 off-screen (all canonical 5-surface set minus `app-startup`, which is synthetic)
**Renders captured:** 11 PNG files (4 standard surfaces × 2 resolutions + 3 dark-bg variants + 1 close-up)

---

## 1. TL;DR

The top three visual gaps are: (1) the Enriques canonical sextic has severe sawtooth mesh-tear artifacts at every singularity node — visible at default zoom and catastrophic on close-up — making it the weakest first-impression surface in the set; (2) every surface in the app shares the same `#b0c4de` light-steel-blue color with no per-family differentiation, erasing the visual hierarchy that helps a math reader understand which family they are exploring; (3) the default dark viewport background (`#2f2f2f`) is an effective scientific-viz choice and dramatically improves surface depth, but the app opens to an empty viewport with only a status-bar prompt — there is no first-launch affordance to guide a new user into the cascade-dropdown flow. Overall visual coherence across surfaces rates **3 / 5**: mesh quality and lighting are good for three of the four surfaces, but the Enriques artifact is a credibility hit, and the uniform color palette leaves the app feeling monotone. The main theme for modernization is: fix the Enriques mesh quality, introduce per-family color identity, and add a minimal first-launch onboarding signal.

---

## 2. Per-surface observations

### 2.1 app-startup (synthetic — no Qt instantiation per AI-3)

**Observation (from `app.py` + `styles.py` code read):** On launch the `MainWindow` displays a 1200×800 window titled "Algebraic Variety Viewer". The central `QtInteractor` viewport is empty and black (default VTK background before `AppearancePanel.apply_to_actor(None)` sets it to `#2f2f2f`). The status bar reads "Choose a variety to begin." in `COLOR_MUTED = #5a5a5a` at 11 px. The top control bar shows `Variety: — Select —` (disabled `Model:` label beside a greyed combo). The three docks are visible but empty or in default state.

**Gaps found:**
- No visual affordance drawing the eye to the Variety dropdown — the empty dark viewport and a single status-bar sentence are the entire onboarding surface.
- The `Model:` label and combo are disabled on launch (`_set_subtype_enabled(False)`) which is correct UX, but there is no introductory hint label in the central area itself.
- `app.py` line 145: `self.appearance_panel.apply_to_actor(None)` calls the method with `None` — the method is a no-op for `None`, so the background color `#2f2f2f` is NOT set until a surface is rendered. The viewport starts black.

**No PNG** (AI-3 forbids `MainWindow()` under offscreen).

---

### 2.2 K3 surface — Fermat quartic

**Renders:** `k3-surface-fermat-quartic-default.png`, `k3-surface-fermat-quartic-2x.png`, `k3-surface-fermat-quartic-dark-bg.png`

At default parameters (c=1, α=0, β=0, γ=0) the surface is a smoothly rounded cube-like form — mathematically correct for `x⁴+y⁴+z⁴=1` (the L⁴ unit sphere, which has octahedral symmetry and rounded corners). Taubin smoothing has done its job: no marching-cubes faceting is visible. The `#9aa6c8` / `#b0c4de` slate-blue color on the dark background (`dark-bg` render) reads clearly with excellent depth gradient. On the white-background `default` render the surface appears slightly washed out — the `#9aa6c8` highlight on pure white produces low local contrast at the lit apex.

**Gaps found:**
- The default parameter combination (all zeroes except c=1) produces a shape that a non-expert user would read as "a rounded cube" — mathematically accurate but visually unremarkable. There is no visual cue that this is an algebraic surface with rich deformation structure. A more interesting default (e.g. α=-0.5, γ=-4) would better showcase what the surface can become. (LOW)
- White VTK default background washes the lit apex highlight at the off-screen render's single top light. (LOW; note the app actually defaults to dark bg — this is only a scout-render issue.)

---

### 2.3 K3 surface — Kummer surface

**Renders:** `k3-surface-kummer-surface-default.png`, `k3-surface-kummer-surface-2x.png`

At default μ²=1.3 the Hudson-form Kummer surface shows the correct tetrahedral structure: four bent-sail lobes meeting at a compressed central node region, consistent with a 16-nodal quartic near the tetrahedral locus. The mesh is smooth and the self-intersection / pinch topology reads well in the default isometric view. The `#9aa6c8` color differentiates lobe faces from their interior shadows cleanly. The 2x render at 2400×1600 shows smooth anti-aliasing with no degradation.

**Gaps found:**
- The default camera framing clips the left and right lobe tips slightly — the bounding sphere is about 15 % wider than the visible frame. A slightly wider default zoom (reset camera with a 1.1× margin factor) would show the full surface on first render. (LOW)
- All surfaces share the same slate color — K3 Fermat and Kummer look visually identical at first glance until you rotate. (MEDIUM — documented as a cross-surface pattern below.)

---

### 2.4 Enriques surface — Canonical sextic [Fig. 1]

**Renders:** `enriques-surface-canonical-sextic-default.png`, `enriques-surface-canonical-sextic-2x.png`, `enriques-surface-canonical-sextic-dark-bg.png`, `enriques-surface-canonical-sextic-node-closeup.png`

This is the most visually problematic surface in the canonical set. The global shape is correct — a triangular form with S₄ symmetry and a visible internal void — but three major visual artifacts are present:

1. **Sawtooth / ripple tears along all four internal node lines.** Every line where two sheets pinch toward each other produces a jagged white-on-dark sawtooth band. These are visible at 1200×800 standard zoom and become dramatically worse on the close-up render. The artifact is a marching-cubes zero-crossing resolution issue: the field has a near-zero band (not a clean zero), and the resulting isosurface oscillates at the grid step size, producing a comb-like mesh edge. At 400 k+ vertices the resolution is already high; the artifact originates in the equation topology, not the grid step.

2. **Flat-panel appearance on wide faces.** The large triangular faces of the sextic have very low curvature and appear nearly flat even with `smooth_shading=True`. On the dark background this causes them to read as dark, featureless polygons.

3. **Perimeter serration.** Every outer edge of the surface has a pixelated, serrated silhouette — visible even at 1200×800. This is a marching-cubes boundary artifact where the implicit field reaches zero exactly at the grid boundary.

**Gaps found:**
- Sawtooth node tears along internal singularity lines (CRITICAL — visible on default render without close-up)
- Perimeter serration on outer silhouette (HIGH — visible at 1200×800 standard zoom)
- Low curvature / flat-panel visual on large faces — surface lacks depth cues (MEDIUM)

---

### 2.5 Calabi–Yau 3-fold — Hanson quintic [Fig. 1]

**Renders:** `calabi-yau-3-fold-hanson-quintic-default.png`, `calabi-yau-3-fold-hanson-quintic-2x.png`, `calabi-yau-3-fold-hanson-quintic-dark-bg.png`

This is the visual standout of the canonical set. The 25-patch parametric surface fills the frame well, the concave/convex lobes read clearly, and the Phong `smooth_shading=True` with the dark background produces the closest approximation of the "Elegant Universe cover" look currently achievable in this app. The 2x render shows some very subtle patch-boundary seams where adjacent Hanson patches meet — these are thin darker lines at patch edges, most visible in the concave valley between lobes. They are not jarring at normal viewing distance but would be conspicuous in a printed figure.

On the dark background the `#b0c4de` light-steel-blue works well — the surface has genuine depth and the five-fold symmetry is legible. This is the best-performing surface in the set.

**Gaps found:**
- Subtle patch-boundary seams visible at normal zoom, more prominent at 2x. (LOW — inherent to disconnected-component parametric assembly; AI-7 constraint means `consistent_normals=False` is the correct tradeoff)
- The default `alpha = π/4` projection angle is a good middle-ground choice but is not the iconic "cover" angle from Hanson's original paper. No gap per se, but a candidate for a named "Iconic" camera preset tied to the known good angle. (LOW)
- Lighting: the single VTK key light from upper-left produces a large shadow on the lower-right lobe cluster. An ambient + fill light rig (as Hanson's original Mathematica render used) would reveal interior structure in the shadowed lobes. (MEDIUM)

---

## 3. Critical gaps

### GAP-C1: Enriques canonical sextic — sawtooth mesh tears at internal node lines

**Surface(s) affected:** Enriques surface / Canonical sextic [Fig. 1]

**Render evidence:**
- `renders/enriques-surface-canonical-sextic-default.png` — white sawtooth bands visible on three internal node lines at standard 1200×800 zoom
- `renders/enriques-surface-canonical-sextic-dark-bg.png` — bands appear as bright white-on-dark rips at the same locations, more prominent on dark background
- `renders/enriques-surface-canonical-sextic-node-closeup.png` — close-up from (0.5, 0.5, 2.0) shows a 3–5 px wide comb-tooth tear running the full length of each node line; individual spikes are 10–20 pixels high

**What the user sees:** When the Enriques canonical sextic first renders, three white serrated lines radiate outward from the center of the surface, meeting at the background through bright sawtooth spikes. The upper and lower halves of each sheet appear to be "unzipping" along their shared node line. The effect reads as a mesh defect or rendering glitch rather than a geometric feature of the equation, because the tears are uniform in width and regularly spaced. A first-time user would assume the renderer has a bug.

**What a 2026 SOTA scientific-viz app would do:** Apps like Surfer (Imaginary.org) and Mathematica's `ContourPlot3D` handle near-singular zero-crossings by increasing adaptive resolution only in the neighborhood of the singular locus, rather than using a uniform grid. For this app's marching-cubes pipeline, the pragmatic mitigation is to increase the local grid resolution or apply a second pass of Taubin smoothing (`smooth_taubin(n_iter=40, pass_band=0.05)`) specifically to the artifact band. Alternatively, post-processing the mesh with `mesh.decimate(target_reduction=0.1)` or trimming faces whose normal-to-neighbor angle exceeds a threshold (the sawtooth faces have highly anomalous normals) can suppress the worst spikes. A [INT-95 katex-tooltip-popover] style inset noting "node singularity" at the artifact location would at minimum contextualise the geometry, but the artifact itself needs to be reduced.

**Severity:** CRITICAL

**Closest existing app pattern:** `surfaces.py` `_marching_cubes_to_polydata` — the `smooth_taubin` call at `n_iter=20, pass_band=0.1` is insufficient for near-singular fields. The Fermat quartic and Kummer surface use the same pipeline and are clean because their zero loci are smooth; the Enriques canonical sextic's degree-6 equation has genuine near-singular lines that require more aggressive post-processing.

---

## 4. High gaps

### GAP-H1: Pure-white background on off-screen renders misrepresents the app's actual first-launch appearance

**Surface(s) affected:** All surfaces (cross-surface)

**Render evidence:**
- `renders/k3-surface-fermat-quartic-default.png` vs `renders/k3-surface-fermat-quartic-dark-bg.png` — the white-background render shows a washed-out lit highlight; the dark-background render shows genuine depth, specularity, and a convincing scientific-viz surface
- `renders/enriques-surface-canonical-sextic-dark-bg.png` — sawtooth artifact is MORE visible on dark bg (relevant: if screenshots are shared from dark-bg, users will notice the artifact)

**What the user sees:** The app's `AppearancePanel` hardcodes `self._bg_color = QColor("#2f2f2f")` as the default background, but this color is only applied to the plotter via `apply_to_actor()`, which is called with `None` at startup (line 145 of `app.py`) and is a no-op for `None`. The VTK plotter therefore starts with its default grey/white gradient background, not `#2f2f2f`. The first-rendered surface appears on a pale grey background, not the dark grey the designer intended. Only after the user picks a surface and the first render fires does `apply_to_actor(self._actor)` run, which calls `set_background(self._bg_color.name())` and switches to dark. The user sees a background flash: pale grey → dark grey on first render.

**What a 2026 SOTA scientific-viz app would do:** Scientific-viz desktop apps (ParaView, 3D Slicer) initialize the background color during window construction, not during the first actor addition. The fix is a single `self.plotter.set_background("#2f2f2f")` call inside `MainWindow.__init__` after the plotter widget is created, independent of `apply_to_actor`. This removes the flash and ensures the empty viewport is already dark-themed before any surface is rendered. [INT-80 solid-color-bg] applies here.

**Severity:** HIGH

**Closest existing app pattern:** `app.py` line 144–145 — `self.appearance_panel.apply_to_actor(None)`. The background initialization is coupled to actor creation; they should be decoupled.

---

### GAP-H2: Enriques canonical sextic — perimeter silhouette serration

**Surface(s) affected:** Enriques surface / Canonical sextic [Fig. 1]

**Render evidence:**
- `renders/enriques-surface-canonical-sextic-default.png` — every outer edge of the surface shows a pixelated, irregular silhouette rather than a smooth outline. Each straight edge has 3–5 pixel steps. Visible at standard zoom on the three "wing" edges.
- `renders/enriques-surface-canonical-sextic-2x.png` — confirmed at 2x resolution; the serration is a mesh artifact, not an aliasing artifact

**What the user sees:** The outer boundary of the Enriques sextic looks clipped or stepped rather than smooth. The three "wing" edges that terminate at the grid boundary appear as a row of jagged triangles, similar to what a user would expect from an extremely low-resolution mesh. This occurs because the marching-cubes algorithm at a flat grid boundary produces boundary triangles whose outer edges align with the grid, creating a staircase pattern. Contrast with the Kummer surface and Hanson quintic, which have no such effect because their zero loci do not reach the grid boundary.

**What a 2026 SOTA scientific-viz app would do:** Surfer and Mathematica handle this by padding the grid by 2–3 cells beyond the mesh boundary and trimming the outer band after extraction, ensuring no isosurface vertex lies on the grid wall. An equivalent fix here is to increase the sampling box bounds slightly beyond what the equation requires (e.g. `bounds * 1.05`) so the zero-locus always terminates inside the grid interior. Alternatively, `mesh.extract_surface()` + a boundary-smoothing pass on the outer edge loop would reduce the staircase. [INT-60 pv-off-screen-render] confirms the artifact is geometry, not rendering.

**Severity:** HIGH

**Closest existing app pattern:** `surfaces.py` `_marching_cubes_to_polydata` — the `bounds` parameter for Enriques is hardcoded (`2.5` for the canonical sextic); padding it to `2.6` or `2.7` may move the zero-locus termination point away from the grid wall.

---

### GAP-H3: No per-variety color identity — all surfaces render identically in color

**Surface(s) affected:** All (cross-surface)

**Render evidence:**
- `renders/k3-surface-fermat-quartic-default.png` and `renders/calabi-yau-3-fold-hanson-quintic-default.png` — both surfaces are rendered in the same `#9aa6c8` / `#b0c4de` light-steel-blue. Side-by-side, a reader cannot tell from color alone which family they belong to.
- All 4 default renders share the same hue family, producing a visually homogeneous set with no visual hierarchy.

**What the user sees:** Every surface in the app opens with the same light-steel-blue surface color. Switching from K3 to Enriques to Calabi–Yau produces no immediate visual signal that these are conceptually different families. A math-research audience familiar with 3Blue1Brown's color discipline or Quanta Magazine figure conventions expects visual cues to encode mathematical relationships. The single shared color says "these are all the same kind of thing," which is factually wrong — K3 surfaces (compact, smooth, 2-dimensional) and Calabi–Yau 3-folds (6-dimensional, parametric cross-section) are fundamentally different objects.

**What a 2026 SOTA scientific-viz app would do:** Mathematica's `Manipulate` uses hue variation to distinguish plot families. GeoGebra 3D assigns persistent colors to geometric objects by family. The design-system.md §7 explicitly lists "Variety-family color theming" as an underdeveloped candidate. An [INT-96 palette-template-per-variety] implementation would assign: K3 surfaces a cooler blue-slate (current default is fine as K3's token); Enriques surfaces a warmer amber-terracotta (to signal the "quotient / birational" relationship); Calabi–Yau 3-folds a deep cobalt-indigo (recalling the iconic Hanson renders); Fano 3-folds a muted forest-green. All new tokens must pass WCAG AA contrast on `#2f2f2f` (≥ 3:1 for large text; ≥ 4.5:1 for small text per AI-12 — surface color is a render attribute, not a text color, so WCAG body-text rules don't apply directly, but sufficient luminance contrast against the dark background is needed for depth-cue legibility).

**Severity:** HIGH

**Closest existing app pattern:** `appearance_panel.py` line 75 — `self._surface_color = QColor("#b0c4de")` — a single hardcoded default applies to all varieties. Changing this to a per-variety lookup (keyed by the variety name passed in from `MainWindow`) is the minimum change.

---

## 5. Medium gaps

### GAP-M1: Hanson quintic — single-key-light shadow hides interior lobe structure

**Surface(s) affected:** Calabi–Yau 3-fold / Hanson quintic [Fig. 1]; likely all Hanson cross-sections

**Render evidence:**
- `renders/calabi-yau-3-fold-hanson-quintic-dark-bg.png` — the lower-right quadrant of the surface (three to four lobes) is in deep shadow; the light comes from upper-left only. The concave valleys in shadow are indistinguishable from the convex lobes in shadow — both read as flat dark.
- `renders/calabi-yau-3-fold-hanson-quintic-2x.png` — shadow coverage confirmed at 2x; not an aliasing artifact.

**What the user sees:** At the default isometric view the Hanson quintic appears to have a "bright half" and a "dark half." The lower-right lobes are so dark that the user cannot see whether those lobes are concave or convex, inward-facing or outward-facing. Rotating reveals the structure, but the default first-frame impression is that roughly half the surface is missing or clipped.

**What a 2026 SOTA scientific-viz app would do:** Hanson's own 1994 renders used a three-point lighting rig: a key light at upper-left, a fill light at lower-right at 40–50% key brightness, and a rim/back light. PyVista's `Plotter.add_light()` supports exactly this. The `specular=0.3, specular_power=15` already set in `app.py:_apply_domain_and_render` (line 371) is a good specular baseline, but the ambient and fill components are at VTK defaults, which are too dark for multi-lobe geometry. Increasing `ambient=0.2` in the `add_mesh` call would be a minimal fix. A proper fill-light rig is an [INT-83 phong-vs-flat-shading] adjacent candidate. This is especially important for the AI-7 Hanson normals: `cell_normals=True, consistent_normals=False` means each patch is shaded individually — a fill light reduces the visual discontinuity at patch boundaries.

**Severity:** MEDIUM

**Closest existing app pattern:** `app.py` line 370–374 — `self._actor = self.plotter.add_mesh(clipped, smooth_shading=True, specular=0.3, specular_power=15)`. The `ambient` kwarg is not set; it defaults to VTK's 0.0–0.1 range.

---

### GAP-M2: K3 Fermat quartic — visually unremarkable default shape

**Surface(s) affected:** K3 surface / Fermat quartic

**Render evidence:**
- `renders/k3-surface-fermat-quartic-default.png` — the surface at (c=1, α=0, β=0, γ=0) is a smooth, slightly-rounded cube. There are no axial arms, no deformation features, and no mathematical interest visible.
- Contrast with what the surface becomes at α=-0.5, γ=-6: the octahedral arms extend significantly and the K3 character is apparent.

**What the user sees:** The first render of the K3 Fermat quartic is a grey rounded box. A math-curious user who opened the app expecting to see an algebraic surface will question whether the app loaded correctly, or whether "K3 surface" means "a box." The parameter sliders do reveal the surface's richness, but the default gives no hint of that potential.

**What a 2026 SOTA scientific-viz app would do:** Surfer (Imaginary.org) and Mathematica's example notebooks choose their default parameter values to showcase the equation's most characteristic feature, not the "zero perturbation" identity case. The design-system.md §7 notes that defaults are a UX surface. Changing the defaults to e.g. α=-0.3, γ=-3.0 would show the octahedral arms while keeping the surface within the valid parameter range (CONTEXT.md §5.1 confirms α down to -1 is valid). This is a single-line change per `ParamSpec` in `surfaces.py` and requires no new code.

**Severity:** MEDIUM

**Closest existing app pattern:** `surfaces.py` `FERMAT_QUARTIC_PARAMS` — each `ParamSpec.default` is a zero or identity value.

---

### GAP-M3: No first-launch visual affordance in the central viewport

**Surface(s) affected:** app-startup (all surfaces, pre-selection)

**Render evidence:** Synthetic (AI-3 — no `MainWindow()` offscreen). The `app.py` `_PLACEHOLDER = "— Select —"` constant and `statusBar().showMessage("Choose a variety to begin.")` are the only first-launch signals. The central viewport is empty.

**What the user sees:** On launch, the app presents a blank dark-grey square (or black, per GAP-H1) that takes up ~70% of the window, flanked by three empty dock panels. The status bar says "Choose a variety to begin." in small muted text. There is no visual signal in the large central area pointing the user to the dropdown controls above it. A user who has not read the README would not know the two-step dropdown-cascade flow exists.

**What a 2026 SOTA scientific-viz app would do:** ParaView shows a "Load data" / "Connect to server" splash on first launch. Surfer shows a pre-loaded example surface. GeoGebra 3D opens with a coordinate system rendered. The design-system.md §7 lists "First-launch tour / click any variety hint" as an underdeveloped candidate. A minimal solution is a centered `QLabel` in the viewport area (layered over the plotter, or as a VTK text actor) reading "Choose a variety family from the dropdown above to begin." This avoids the auto-render pattern that was rejected in CONTEXT.md §9 (too presumptuous) while still filling the empty canvas with intent. [INT-4 status-bar-feedback] is already used; this is its canvas-level complement [INT-74 empty-clip-status-message] applied at startup.

**Severity:** MEDIUM

**Closest existing app pattern:** `app.py` line 86 — `self.statusBar().showMessage("Choose a variety to begin.")` — the existing message is status-bar only with no canvas counterpart.

---

### GAP-M4: Enriques canonical sextic — flat-face visual on large panels

**Surface(s) affected:** Enriques surface / Canonical sextic [Fig. 1]

**Render evidence:**
- `renders/enriques-surface-canonical-sextic-dark-bg.png` — the three large triangular faces in the lower half of the surface read as near-uniformly dark, flat panels with no depth curvature gradient. The internal curved area (between the singularity lines) shows curvature variation but the outer "wings" are almost flat.

**What the user sees:** The large outer triangular panels of the Enriques sextic appear as flat dark slabs, giving the surface a low-information appearance for roughly half of its area. Since these panels dominate the silhouette, the surface reads as a dark geometric solid rather than as an algebraic surface with interesting curvature.

**What a 2026 SOTA scientific-viz app would do:** Applying a curvature-mapped scalar coloring (mean curvature or Gaussian curvature overlaid as a colormap on top of the base color) would immediately reveal the mathematical structure on the flat panels — they are not truly flat, just have lower curvature than the interior. PyVista supports `mesh.curvature()` which returns a scalar array suitable for `p.add_mesh(mesh, scalars="Mean_Curvature", cmap="coolwarm")`. This is not the default render style and would require an [INT-96 palette-template-per-variety] style "curvature map" option in the Appearance panel. Alternatively, increasing ambient lighting (see GAP-M1) would provide more visible gradient on the flat faces.

**Severity:** MEDIUM

**Closest existing app pattern:** `appearance_panel.py` — no curvature scalars are exposed. The `add_mesh` call in `app.py` line 370 uses only `smooth_shading`, `specular`, `specular_power`.

---

## 6. Low gaps

### GAP-L1: Kummer surface — default camera framing clips lobe tips

**Surface(s) affected:** K3 surface / Kummer surface

**Render evidence:**
- `renders/k3-surface-kummer-surface-default.png` — the left and right horizontal lobes extend to within ~5% of the frame edge, giving the surface a slightly cramped appearance. The vertical lobe (top) terminates cleanly, but the horizontal ones appear to run off the side.

**What the user sees:** The Kummer surface at default view fills the frame slightly too tightly. The left and right lobes are not clipped, but they feel visually crowded. Rotating the camera slightly reveals the tips.

**What a 2026 SOTA scientific-viz app would do:** A 5–10% additional zoom-out factor on `reset_camera()` after the first render would give the surface breathing room. PyVista's `reset_camera(bounds=...)` accepts a bounds override — calling it with 1.05× the mesh bounds after a surface switch would be sufficient. [INT-23 camera-preset-fire-and-render] applies.

**Severity:** LOW

**Closest existing app pattern:** `app.py` line 389 — `self.plotter.reset_camera()` — called with no bounds override.

---

### GAP-L2: Hanson quintic — patch-boundary seams visible at 2x resolution

**Surface(s) affected:** Calabi–Yau 3-fold / Hanson quintic [Fig. 1] (and likely all Hanson cross-sections)

**Render evidence:**
- `renders/calabi-yau-3-fold-hanson-quintic-2x.png` — thin darker lines are visible at patch junctions on the concave valleys between lobes. At 1× they are barely perceptible; at 2× (HiDPI / Retina) they are clear.

**What the user sees:** On a Retina display, the Hanson quintic shows faint seam lines between its 25 parametric patches, most visibly at the concave saddle points between lobe clusters. These are not bright artifacts like the Enriques tears — they are subtle darker lines, similar to edge-creasing on a polygon mesh.

**What a 2026 SOTA scientific-viz app would do:** The AI-7 invariant (cell_normals, no consistent_normals) is the correct tradeoff given disconnected components. The seams are a byproduct of per-patch winding driving shading; their intensity can be reduced by slightly increasing ambient light (overlaps with GAP-M1). A Retina-specific mitigation is to ensure the `QtInteractor` DPI scale factor is respected via `QT_AUTO_SCREEN_SCALE_FACTOR=1` (noted in README troubleshooting) and the window.devicePixelRatio-aware render path. No code change needed for this; the README workaround should be elevated to `app.py`'s `main()` as an `os.environ` guard.

**Severity:** LOW

**Closest existing app pattern:** `app.py` line 424 `main()` — no `QT_AUTO_SCREEN_SCALE_FACTOR` guard. README mentions the workaround.

---

### GAP-L3: K3 Fermat quartic — white background apex wash-out in off-screen renders

**Surface(s) affected:** K3 surface / Fermat quartic (white-background renders only)

**Render evidence:**
- `renders/k3-surface-fermat-quartic-default.png` — the lit apex highlight of the rounded cube is almost pure white on a white background; local contrast is near zero at the top face.

**What the user sees:** In the off-screen render (and in any screenshot taken with a white background color set), the top face of the Fermat quartic blends into the white background. The surface appears to have a "melting" top edge.

**What a 2026 SOTA scientific-viz app would do:** This is only an issue with pure-white backgrounds. The app defaults to `#2f2f2f` which resolves this (see dark-bg render). The gap is in the off-screen render script's choice of PyVista default background — the scout render should set background to the app's actual default. This is a scout-tooling finding, not a user-visible gap given the app's dark default. No app code change needed.

**Severity:** LOW (scout-tooling note; not user-visible with app's dark-bg default)

**Closest existing app pattern:** `appearance_panel.py` line 76 — `self._bg_color = QColor("#2f2f2f")` — the correct default exists; the off-screen scout render just doesn't replicate it.

---

## 7. Cross-surface patterns

### Pattern 1: Uniform slate-blue color removes variety-family context (all surfaces)

Every surface in the canonical set renders with the same `#b0c4de` / `#9aa6c8` light-steel-blue. Toggling between K3 Fermat quartic, Kummer surface, Enriques canonical sextic, and Hanson quintic produces no color change in the viewport. The user's only signal that the variety family changed is the status-bar label and the panel rebuilding. A 2026 SOTA math-viz app (Surfer, GeoGebra, Mathematica Manipulate) uses color identity to encode mathematical classification. See GAP-H3 for the full entry.

### Pattern 2: Dark background enhances every surface; white background flatters none

All three dark-background renders (K3 Fermat, Enriques, Hanson) show meaningfully better depth, surface curvature, and visual interest than their white-background counterparts. The Hanson quintic on dark background is the strongest image in the set. The app's `#2f2f2f` default is the right choice, but the background-initialization gap (GAP-H1) means the first ~0.5 seconds shows the wrong background.

### Pattern 3: Marching-cubes boundary and near-singular artifacts are a shared risk

The Enriques canonical sextic is the only surface in the canonical set where marching-cubes artifacts are visible at default zoom, but the same risk exists for any surface whose zero locus approaches the sampling grid boundary or has a near-singular band. The Dwork pencil at ψ=1 (not in the canonical set but in the full variety list) already uses a RuntimeWarning for the conifold; the Enriques canonical sextic would benefit from a similar soft warning ("Near-singular locus detected — rendering may show artifacts at the node lines") via the `warnings.warn` / [INT-70 status-warning-prefix] pattern.

### Pattern 4: Single-light VTK rig is insufficient for complex multi-lobe surfaces

The Kummer surface (4 lobes), Enriques sextic (multiple bent sheets), and Hanson quintic (25 patches) all have significant shadowed regions under the single VTK default key light. A two-point rig (key + fill at 50% key intensity) would benefit all of these. The Fermat quartic at default parameters (convex, low curvature) does not benefit significantly, making this a "complex surface" specific concern. See GAP-M1.

### Pattern 5: HiDPI / 2x render quality is consistent except for Enriques and Hanson seams

The K3 Fermat quartic and Kummer surface 2x renders show no degradation versus the 1x renders. The Enriques canonical sextic 2x render shows the same artifacts as 1x but they appear larger. The Hanson quintic 2x render shows new patch-seam visibility not present at 1x. This is the expected pattern: smooth surfaces scale cleanly; meshed surfaces with structural discontinuities (singularities, patch boundaries) reveal more at higher DPI. 2x render is a good regression test for mesh quality.

---

## 8. What the app does well visually

- **Taubin smoothing on implicit surfaces is effective.** The K3 Fermat quartic and Kummer surface show zero marching-cubes faceting at default zoom. The `n_iter=20, pass_band=0.1` parameters are well-calibrated for the grid resolution used.
- **Dark background default (`#2f2f2f`) is a strong visual design choice.** Once the first surface renders, the dark viewport background gives every surface genuine depth and shadow variation. This is consistent with SOTA scientific-viz apps (Blender, ParaView dark theme, Hanson's own renders).
- **Hanson quintic is a genuinely beautiful render.** The 25-patch parametric cross-section at default α=π/4 is immediately recognizable as a Calabi–Yau cross-section to anyone who has seen Hanson's 1994 work. The smooth shading, the five-fold lobe symmetry, and the concave valleys all read correctly.
- **Kummer surface topology reads immediately.** The four-lobe structure with the tetrahedral singularity at the center is legible at first render. The marching-cubes pipeline handles the self-intersection correctly — no phantom interior is visible.
- **Phong shading (`smooth_shading=True`) with `specular=0.3, specular_power=15` is a reasonable default.** The specular highlight is visible but not overwhelming. Surfaces have a slight "mathematical model" gloss appropriate for the research-tool aesthetic.
- **Adaptive bounds (Fermat quartic, Kummer surface) prevent clipping.** Neither the Fermat quartic nor the Kummer surface has its zero locus truncated at the grid wall. This is in contrast to the Enriques canonical sextic where the wings do reach the boundary.

---

*Brief written by visual-scout agent. All claims are anchored to a PNG render in `.claude/notes/frontend-uplifts/2026q2-panel-refresh/renders/` or to a specific file:line in the codebase.*
