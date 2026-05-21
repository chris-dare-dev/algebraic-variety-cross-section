# Synthesis — 2026q2-graph-and-window

**Date:** 2026-05-21
**Discover briefs:** 4 (visual, library, inspiration, current-state-critic — all completed)
**Renders inspected:** 20 PNGs (8 surface + 12 panel-chrome)
**Phase:** synthesize

---

## 1. Executive Summary

29 modernization candidates surfaced from the 4 discover briefs. The dominant theme is **incomplete visual coherence between the dark VTK canvas and the light Qt chrome** — surfaced as a HIGH gap by both the current-state-critic (H-2) and the visual-scout (H-2 / capture artifact), as the top library candidate by the library-scout (pyqtdarktheme-fork), and as inspiration PC-10 + theme A by the inspiration-scout. All four briefs converged on this single foundational gap. The secondary theme is **color discipline as a research-credibility signal**: every surface today renders in the same `#9aa6c8` slate (visual M-1, inspiration PC-1 / PC-6, design-system's explicit `VARIETY_DEFAULT_COLOR = {}` stub).

Categories dominate as: **Color/theme** (5 candidates), **Library/dependency** (3 candidates with 6+ downstream applications), **Camera/viewport** (5 candidates), **Accessibility** (4 candidates).  The catalog has 2 **foundational** candidates that other candidates depend on — these are flagged in Section 3 and must sequence first.

Top tension across briefs: the visual-scout flags the white-bg off-screen renders as a HIGH gap, but it's a capture-pipeline artifact, not a product bug (the app's intended viewport is dark). This is captured separately as a tooling candidate (UPL-28) rather than misclassified as a product gap.

---

## 2. Triangulation Strength

| Triangulation | Count | Note |
|---|---|---|
| 4-brief (all scouts surfaced it) | 1 candidate | UPL-1 dark-mode stylesheet — strongest signal in the catalog |
| 3-brief | 3 candidates | UPL-4 qtawesome icons, UPL-5 superqt collapsible, UPL-2 variety palette |
| 2-brief | 6 candidates | UPL-3, UPL-7, UPL-8, UPL-10, UPL-15, UPL-17 |
| 1-brief | 19 candidates | Mostly inspiration-only patterns and visual-only paper-cuts — flag for challenger scrutiny |

The 4-brief candidate (UPL-1) is the strongest single signal and is one of the two foundational candidates. The 1-brief tail is large (66%) but mostly low-effort polish — none of the 1-brief candidates are L-effort.

---

## 3. Foundational Candidates

Surfaced FIRST because other candidates depend on them. Phase 4 must sequence these ahead of dependents.

### UPL-1 — Add APP_STYLESHEET_DARK + PALETTE_DARK (fill UPL-4 placeholder)

**Category:** Color/theme
**Size:** M
**Evidence triangulation:** 4 briefs (visual ✓ H-2, library ✓ B1, inspiration ✓ PC-10, current-state-critic ✓ H-2)
**Interaction primitives:** [INT-94 dark-mode-stylesheet]
**Foundational:** YES — UPL-10/11/12/13 (chrome-polish accessibility fixes) all need dark-token equivalents; UPL-2 (variety palette) tokens should be defined in both palettes; UPL-3 (color-map preset picker) should respect theme.

**What it is:** Add `PALETTE_DARK: dict[str, str]` parallel to `PALETTE_LIGHT` in `styles.py` (keys identical, dark-appropriate values), generate `APP_STYLESHEET_DARK` from it, expose a theme-switch toggle. Wire `MainWindow.__init__` to apply the dark stylesheet **by default** since the viewport is already dark — the dark chrome is the coherent baseline, not the optional variant. Light remains available as a toggle.

**Why it matters:** Today the dark `#2f2f2f` viewport meets the light `#f0f0f0` panels at a hard chrome edge with no transition — the current-state-critic's words: "a dark rectangle surrounded by white panels — a contrast boundary that reads as two different applications sharing a window." No peer VTK app (ParaView 5.x, Blender 4.x, 3D Slicer 5.x, Mathematica) ships this split. Closing this is the single highest-leverage visual change available.

**Sources:**
- Visual scout: H-2 — render-loop & app default mismatch
- Library scout: B1 pyqtdarktheme-fork (MIT, PySide6 demo code) — adopt-as-import
- Inspiration scout: PC-10 dark-mode stylesheet — Quanta / 3Blue1Brown register
- Current-state critic: H-2 — top HIGH finding

**Closest existing app analog today:** `styles.py:110–113` — explicit `UPL-4 placeholder marker`; `styles.py:62–63` already notes `TEXT_MUTED = #5a5a5a` fails on dark bg (1.94:1) and flags it for UPL-4.

**Render evidence:** Every panel PNG (panel chrome is light) + every surface PNG (with the H-2 caveat that surface renders should be against `#2f2f2f`, not white). Particularly stark: `renders/panels/appearance-light-populated-default.png` vs `renders/calabi-yau-3-fold-hanson-quintic-default.png`.

**Sketch:** Two-track implementation. **Track A (do-it-ourselves, 1-2 days):** Define `PALETTE_DARK` in `styles.py` with key-identical structure to `PALETTE_LIGHT`; derive `APP_STYLESHEET_DARK` from the same template (the styles.py UPL-1 note already prepares the QSS template to be palette-agnostic); add `set_theme(name: str)` helper; call from `MainWindow.__init__`. **Track B (adopt pyqtdarktheme-fork, 0.5 day):** `pip install pyqtdarktheme-fork`; `qdarktheme.setup_theme("dark"); app.setStyleSheet(qdarktheme.load_stylesheet("dark") + APP_STYLESHEET_OVERRIDES)` where overrides keep the app's resetDefaultsBtn pink, dock header style, etc. The fork is MIT, actively maintained (2026-03-04 release), Python 3.14 supported.  Track B is faster but mixes vendor QSS with our own; Track A keeps full control. Picking is a Phase 4 decision.  Either way, **AI-12 audit required**: every text token must re-verify WCAG AA on the dark background — the current `TEXT_MUTED = #5a5a5a` fails on `#1e1e1e` (1.94:1) per styles.py:62–63 and needs a dark-mode `TEXT_MUTED_DARK = #a0a0a0` or similar.

**Open questions:**
- Track A vs Track B (build vs adopt) — Phase 4 sequencing call
- Apply as default or as toggle? Recommendation: default to dark (viewport-coherent), toggle to light in Help menu later

---

### UPL-2 — Variety-family color tokens (fill UPL-5 placeholder)

**Category:** Color/theme
**Size:** S
**Evidence triangulation:** 3 briefs (visual ✓ M-1 [top gap], inspiration ✓ PC-1 + PC-6, current-state-critic — implicit via app's polish-bias)
**Interaction primitives:** [INT-96 palette-template-per-variety], [INT-43 swatch-color-picker]
**Foundational:** YES — UPL-3 (color-map preset picker) depends on having named palette templates to choose from.

**What it is:** Populate `styles.py:VARIETY_DEFAULT_COLOR: dict[str, str] = {}` with one 6-digit hex per variety family (`"K3 surface"`, `"Enriques surface"`, `"Calabi–Yau 3-fold"`, `"Fano 3-fold (ρ=1)"`). On surface switch, `appearance_panel.apply_to_actor` reads the dict and sets the actor color to the family default (user can still override via the swatch). When `UPL-1` ships, define both `VARIETY_DEFAULT_COLOR_LIGHT` and `VARIETY_DEFAULT_COLOR_DARK` parallel maps tuned for their respective backgrounds.

**Why it matters:** Every surface today is the same `#9aa6c8` slate — switching from Kummer to Hanson is a shape change with zero color cue. Visual M-1: "in a research context where a user may be comparing two families visually, the identical color erases one of the most immediate visual differentiators." For a research tool, color-as-family-identity is a cheap, persistent signal. The stub already exists.

**Sources:**
- Visual scout: M-1 — uniform `#9aa6c8` / `#b0c4de` across all variety families
- Inspiration scout: PC-1 color-map preset picker + PC-6 per-variety surface color presets
- Library scout: (implicit — qtawesome's color-tag idiom in MaterialDesign icons)

**Closest existing app analog today:** `styles.py:99-107` — `VARIETY_DEFAULT_COLOR: dict[str, str] = {}` explicitly stubbed for UPL-5 with comment "Keys MUST match the VARIETIES dict in surfaces.py VERBATIM."

**Render evidence:** All 4 surface PNGs at `renders/k3-surface-*.png`, `renders/enriques-surface-*.png`, `renders/calabi-yau-3-fold-*.png`.

**Sketch:** Suggested initial map (math-community-aligned hues):
```
"K3 surface": "#7a92b8"          (cool slate — current default)
"Enriques surface": "#b89878"     (warm amber/ochre)
"Calabi–Yau 3-fold": "#5e7fb8"   (Elegant Universe cobalt)
"Fano 3-fold (ρ=1)": "#7ba872"   (mathematical-green)
```
All must pass AI-12 (WCAG AA) against `#2f2f2f` viewport background (target ≥4.5:1 on text labels if any; ≥3:1 on the surface itself for legibility). All must be 6-digit hex (AI-13). On surface switch (`app.py:_on_variety_changed` / `_on_subtype_changed`), call `appearance_panel.set_default_color(VARIETY_DEFAULT_COLOR.get(variety_key, BG_SURFACE_DEFAULT))`.

**Open questions:**
- Final hex choice — needs design-credibility review (3Blue1Brown / Quanta register check)
- Should default-color override be sticky per-user (QSettings) or reset on every variety switch?

---

## 4. Candidate Catalog

Ordered: foundational already surfaced (UPL-1, UPL-2 above) → high-triangulation within category → t-shirt size ascending.

### 4.1 Color / theme

#### UPL-3 — Color-map preset picker (named palette swatches)

**Category:** Color/theme
**Size:** S
**Evidence triangulation:** 2 briefs (visual partial via M-1, inspiration ✓ PC-1)
**Interaction primitives:** [INT-43 swatch-color-picker]
**Foundational:** Depends on UPL-2.

**What it is:** Add a `QComboBox` above the existing Surface color swatch in the Appearance panel, populated with named palette presets (Cool-to-Warm, Viridis, Plasma, K3-family slate, Enriques amber, CY3 cobalt, Fano green). Selecting a preset populates the swatch + applies to actor.

**Why it matters:** ParaView, 3D Slicer, Mathematica all expose color-map presets as a first-class control; this app exposes only a raw `QColorDialog`. For a researcher who wants figure-quality output without hand-tuning hex, a named preset is the difference between 5 seconds and 5 minutes.

**Sources:** Inspiration PC-1 (ParaView Color Preset Manager + 3D Slicer Colors module); Visual M-1.

**Closest existing app analog today:** `appearance_panel.py:124` `_build_color_group()` — only the swatch + label "Surface…" exists.

**Sketch:** `QComboBox` populated from a static dict of palette-name → hex (or for scientific palettes, hex-list-for-scalar-mapping; out-of-scope until a scalar-field surface is added). UPL-2's `VARIETY_DEFAULT_COLOR` seeds the variety-family group. Add a small swatch column inside the combo for visual preview (Qt's `QStyledItemDelegate` lets us paint a color rect beside each item text).

**Open questions:** Combo vs grid of swatches (Imaginary.org Surfer has a flat grid)? Phase 4 / design call.

---

### 4.2 Library / dependency

#### UPL-4 — Adopt qtawesome for toolbar + button icons

**Category:** Library/dependency
**Size:** S
**Evidence triangulation:** 3 briefs (visual partial — multiple buttons; library ✓ C1 [top icon candidate]; inspiration partial — PC-3 / PC-11 implicit)
**Interaction primitives:** [INT-5 keyboard-shortcut] (icons reinforce shortcuts), [INT-3 busy-cursor] (spinner icon)

**What it is:** `pip install qtawesome`; lazy-import (per agent-memory lesson — 150–200 ms cold-boot otherwise); add icons to: 5 camera-preset buttons in View, Reset Camera button, Screenshot button, Reset Defaults button in Parameters, Wireframe/Show-edges toggles in Appearance.

**Why it matters:** Every button is text-only today. Researchers scanning the panel chrome have to read every button label; an icon row lets the eye triangulate function from icon shape before reading. MaterialDesign icons (`mdi6.*`) suit scientific-app vocabulary better than FontAwesome brands.

**Sources:** Library C1 (qtawesome 1.4.2, MIT, 930 stars, PySide6 6.8.x segfault fixed Jan 2026).

**Closest existing app analog today:** `view_panel.py` preset-button construction (no icons); `parameters_panel.py:60` reset button (no icon).

**Sketch:** Lazy-import in `app.py` or a small `icons.py` helper:
```
# icons.py — single source of truth for app icons
import qtawesome as qta  # lazy: import inside function on first use
def reset_camera_icon(): return qta.icon("mdi6.video-marker-outline", color=COLOR_VALUE)
```
Color-tied to `styles.py` tokens — when UPL-1 lands, icon color reads from the active palette.  AI-12 requires explicit icon color to match `COLOR_MUTED` or `COLOR_VALUE` rather than default theme foreground.

**Open questions:** Cold-boot mitigation — lazy import is the agent-memory lesson; alternative is to pre-warm at startup behind a 1-frame splash if 200 ms is acceptable.

---

#### UPL-5 — Adopt superqt QCollapsible for progressive panel disclosure

**Category:** Library/dependency
**Size:** M
**Evidence triangulation:** 3 briefs (visual partial via M-2 parameter-row clutter, library ✓ A1, inspiration ✓ PC-2 [top theme])
**Interaction primitives:** [INT-6 dock-floatable] (collapse refines the dock content; dock itself unchanged), [INT-7 tooltip-rich] (collapsed section header still carries tooltip)

**What it is:** `pip install superqt`. Wrap each currently-flat `QGroupBox` inside `superqt.QCollapsible` so users can collapse non-essential groups (Shading group, Display toggles, Screenshot/Export, Scene Aids). Default-expanded for high-traffic groups (Colors, Camera presets, Parameters sliders); default-collapsed for low-traffic (Shading details, Screenshot).

**Why it matters:** Inspiration's #1 theme: "progressive disclosure is universal in 2026 peer scientific-viz desktop apps (ParaView, 3D Slicer, GeoGebra) but entirely absent from this app's flat layout." The app currently shows every control all the time; users probing a surface for the first time see 12+ controls when they need 3.

**Sources:** Library A1 (superqt 0.8.2, BSD-3-Clause, 288 stars, released 2026-05-18 — 3 days before this survey); Inspiration PC-2 (ParaView Properties panel basic/advanced toggle).

**Closest existing app analog today:** `appearance_panel.py:153, 195` (Display + Shading groups always visible); `view_panel.py:67` (View Presets + Camera + Clip + Scene Aids + Export all visible); `parameters_panel.py:60` (Reset button always visible).

**Sketch:** Per-panel wrap pass. Example for Appearance: keep Colors + Opacity expanded by default; collapse Display toggles + Shading by default. Persistence: store collapse state via QSettings (depends on UPL-25 dock state persistence). `QCollapsible` uses `QPropertyAnimation` internally, so the open/close motion is smooth.  qtpy is a transitive dep (MIT, stable) — same indirection as qtawesome.

**Open questions:** Default collapse state per group — needs UX review (probably "expanded by default for all on first launch; user-collapsed sticky").

---

#### UPL-6 — Adopt superqt throttled signals + QLabeledSlider

**Category:** Library/dependency
**Size:** XS (paired with UPL-5; if UPL-5 lands, UPL-6 is a same-PR addition)
**Evidence triangulation:** 2 briefs (visual ✓ M-4 + cross-panel inconsistency; library ✓ A1)
**Interaction primitives:** [INT-2 slider-release-render] (throttle = clean replacement), [INT-97 parameter-spin-box-alternative]

**What it is:** Replace manual `sliderReleased` connections with `@superqt.signals.throttled(milliseconds=N)` decorators; replace per-slider custom min/max layout in `parameters_panel.py:160-170` with `superqt.QLabeledSlider` which renders the value label inline with the rail.

**Why it matters:** Reduces boilerplate; gives both Parameters and Appearance opacity sliders the same affordance (currently inconsistent — Parameters has min/max range labels, Appearance Opacity does not — visual M-4).

**Sources:** Library A1; Visual M-4 (opacity range labels).

**Closest existing app analog today:** `parameters_panel.py:156` `slider.sliderReleased.connect(...)` (manual); `parameters_panel.py:160-170` (custom `range_row` layout).

**Sketch:** Same import as UPL-5; in `parameters_panel.py:_build_row`, replace `QSlider` + `range_row` with `QLabeledSlider`. AI-2 safe (superqt has no Qt-in-tests assumption). AI-9 unchanged.

**Open questions:** Will `QLabeledSlider`'s value-formatting hook accept our `_format_value(spec.default, spec)` style? Verify before commit.

---

### 4.3 Camera / viewport

#### UPL-7 — Enriques sextic backface culling (fix white zipper seams)

**Category:** Camera/viewport
**Size:** XS
**Evidence triangulation:** 2 briefs (visual ✓ H-1, current-state-critic ✓ H-3)
**Interaction primitives:** None (rendering-pipeline tweak)

**What it is:** Pass `backface_culling=True` to `plotter.add_mesh(...)` in `app.py:_render_current`. Optionally expose a "Back-face culling" checkbox in Appearance's Display group for pedagogical override.

**Why it matters:** The Enriques canonical sextic at default `c=0` has near-degenerate triangles at its double-curve singularities that render as alternating front/back faces under Phong, producing visible white zipper seams (clearly seen in `renders/enriques-surface-canonical-sextic-2x.png`). The visual scout's H-1 and current-state-critic's H-3 independently identify this. ParaView, VisIt both enable back-face culling by default on implicit-surface renders.

**Sources:** Visual H-1 (sawtooth tear artifacts); Current-state-critic H-3 (backface culling unaddressed).

**Closest existing app analog today:** `app.py` `plotter.add_mesh(clipped, smooth_shading=True, specular=0.3, specular_power=15)` — no backface culling argument.

**Render evidence:** `renders/enriques-surface-canonical-sextic-default.png` (1x — visible white zigzag seams), `renders/enriques-surface-canonical-sextic-2x.png` (2x — torn-paper-edge artifacts very clear).

**Sketch:** One-arg change. Hardcoded default: pass `backface_culling=True`. UI-exposed: add `QCheckBox` to Appearance Display group + wire through `apply_to_actor`. The toggle approach (UI-exposed) is +15 lines and lets pedagogical use; hardcoded approach is 1 line.

**Open questions:** Hardcoded default vs UI toggle — Phase 4 call (hardcoded is XS; toggle is S).

---

#### UPL-8 — Featured-view preset / Fermat quartic default parameters

**Category:** Camera/viewport (default-state)
**Size:** XS
**Evidence triangulation:** 2 briefs (visual ✓ L-4, current-state-critic ✓ H-1 — different severity)
**Interaction primitives:** [INT-23 camera-preset-fire-and-render]

**What it is:** Either (a) change `FERMAT_PARAMS` defaults from `(α=0, β=0, γ=0, c=1)` to a visually expressive default like `(α=-0.5, γ=-3.0, c=1.5)`, OR (b) add a "Featured view" preset button to the View panel that snaps camera + parameters to a known-good first-impression configuration.

**Why it matters:** Severity tension across briefs: current-state-critic rates this HIGH (first-launch communicates app's character); visual scout rates it LOW (mathematical correctness is fine). The truth is in between — first impression matters for tool adoption, but changing math defaults risks breaking the "default is the canonical Fermat quartic x⁴+y⁴+z⁴=1" principle. The Featured-view option preserves that principle while giving researchers an aesthetic on-ramp.

**Sources:** Visual L-4 (default Fermat reads as rounded cube); Current-state-critic H-1 (first-launch render uninformative).

**Closest existing app analog today:** `surfaces.py:243–252` `FERMAT_PARAMS` defaults; `view_panel.py:_make_view_presets_group()` (preset grid where a "Featured" button would fit).

**Sketch:** Preferred — option (b). Add a "Featured" preset button alongside Isometric. On click: set parameters via `parameters_panel.set_values({α: -0.5, γ: -3.0, c: 1.5})` AND fire camera preset. Keeps math defaults canonical; gives researchers a one-click aesthetic on-ramp. AI-9 re-entrancy guard during the combined parameter + camera change.

**Open questions:** Which surfaces deserve their own Featured-view presets vs. defaulting to Isometric? Phase 4 scope question.

---

#### UPL-9 — VTK ambient/diffuse lighting tune

**Category:** Camera/viewport (rendering-pipeline)
**Size:** XS
**Evidence triangulation:** 1 brief (current-state-critic ✓ M-5)
**Interaction primitives:** None

**What it is:** Add `ambient=0.15, diffuse=0.85` to the `plotter.add_mesh(...)` call in `app.py:_render_current`. Optionally expose an "Ambient" slider in Appearance's Shading group.

**Why it matters:** The Fermat quartic at default parameters has shallow, poorly differentiated shading under the current default VTK lighting (which uses scene defaults). Elevated ambient (0.15-0.20) + full diffuse (0.85) noticeably improves K3 surface legibility — confirmed in current-state-critic's analysis of the `k3-surface-fermat-quartic-dark-bg.png` from the prior uplift's renders.

**Sources:** Current-state-critic M-5.

**Closest existing app analog today:** `app.py` `plotter.add_mesh(clipped, smooth_shading=True, specular=0.3, specular_power=15)` — ambient + diffuse default to VTK scene values.

**Sketch:** 2-parameter addition to the existing call. UI exposure (slider in Appearance) is a follow-up if researchers ask for tunability. AI-13 unaffected (no new colors); AI-1 unaffected (PyVista's `add_mesh` already in use).

**Open questions:** Tune values for each surface family vs single global default? Single global is the v1 cut.

---

#### UPL-10 — Disabled-state QSlider QSS rule

**Category:** Accessibility (chrome polish)
**Size:** XS
**Evidence triangulation:** 2 briefs (visual ✓ L-2, current-state-critic ✓ M-1)
**Interaction primitives:** None

**What it is:** Add a `QSlider:disabled` rule to `APP_STYLESHEET` that explicitly desaturates the slider groove when disabled (e.g. `background: #d0d0d0` on light, `#3a3a3a` on dark).

**Why it matters:** When domain mode is "Off", the radius slider's label and checkbox are correctly disabled (greyed) but the slider rail retains its blue accent. The mixed signal — "disabled label, enabled-looking rail" — confuses first-time users (current-state-critic M-1) and leaves a bug-suspect impression (visual L-2).

**Sources:** Visual L-2 (slider rail not visually disabled); Current-state-critic M-1 (disabled-state controls ambiguous in Off mode).

**Closest existing app analog today:** `styles.py:183–254` `APP_STYLESHEET` — no `QSlider:disabled` rule; relies on Qt platform default which is nearly identical to enabled on macOS.

**Sketch:** Add to `APP_STYLESHEET`:
```
QSlider:disabled::groove:horizontal { background: #d0d0d0; }
QSlider:disabled::handle:horizontal { background: #c0c0c0; }
```
When UPL-1 lands, dark-mode equivalents needed.  AI-12 safe (the rule deliberately reduces contrast for an inactive control — exception per WCAG).

**Open questions:** None — straightforward chrome polish.

---

### 4.4 Accessibility

#### UPL-11 — Reset-button visual separator in Parameters panel

**Category:** Layout / Accessibility
**Size:** XS
**Evidence triangulation:** 1 brief (current-state-critic ✓ M-2)
**Interaction primitives:** None

**What it is:** Add a `QFrame.Shape.HLine` separator above the "Reset all to defaults" button in `parameters_panel.py:_build_ui`, between `self._content_layout` and `self._reset_btn`. Scopes "per-slider action" vs "panel-level action" visually.

**Sources:** Current-state-critic M-2.

**Closest existing app analog today:** `parameters_panel.py:60–67` — button sits flush below the last slider's description with no separator.

**Sketch:** 3 lines:
```
sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setFrameShadow(QFrame.Shadow.Sunken)
self._root.addWidget(sep)
self._root.addWidget(self._reset_btn)
```

**Open questions:** None.

---

#### UPL-12 — Group-box border WCAG 1.4.11 non-text contrast fix

**Category:** Accessibility
**Size:** XS
**Evidence triangulation:** 1 brief (current-state-critic ✓ L-4 + §6 audit finding)
**Interaction primitives:** None

**What it is:** Darken `BORDER_GROUP_BOX` from `#d0d0d0` (1.3:1 on `#f0f0f0`) to `#999999` (3.00:1 — clears WCAG 2.1 §1.4.11 non-text contrast threshold).

**Why it matters:** WCAG 2.1 §1.4.11 requires 3:1 minimum for non-text UI components (group-box borders, separators, slider handles). The current `#d0d0d0` border on `#f0f0f0` panel is ~1.3:1 — well below threshold. AI-12 covers text contrast specifically; non-text contrast is a separate WCAG axis the existing palette audit doesn't cover (current-state-critic §6 explicitly notes this).

**Sources:** Current-state-critic L-4; current-state-critic §6 (WCAG 2.1 §1.4.11 audit gap).

**Closest existing app analog today:** `styles.py:77` `BORDER_GROUP_BOX = #d0d0d0`.

**Sketch:** One-token change. Add a `tests/test_styles_palette.py` extension that explicitly tests non-text contrast (border vs panel BG ≥ 3:1) alongside the existing text-contrast tests.

**Open questions:** Dark-mode equivalent — once UPL-1 lands, derive `BORDER_GROUP_BOX_DARK` against `BG_PANEL_DARK` with the same 3:1 minimum.

---

#### UPL-13 — Focus ring contrast darken (FOCUS_RING token)

**Category:** Accessibility
**Size:** XS
**Evidence triangulation:** 1 brief (visual ✓ L-3 [via QSS fallback])
**Interaction primitives:** [INT-82 focus-ring-on-controls]

**What it is:** Darken `FOCUS_RING` from `#5b9bd5` (2.60:1 on `BG_PANEL`) to `#3c82c4` (~3.1:1) or `#2e75b6` (~4.1:1) — clears WCAG AA non-text contrast threshold for UI components.

**Why it matters:** The focus ring at `#5b9bd5` on `#f0f0f0` is 2.60:1 — below the WCAG AA 3:1 requirement for non-text UI components. The current palette already flags this in `styles.py:73` comment: "Flagged for UPL-4 / accessibility pass to darken to e.g. #3c82c4."

**Sources:** Visual L-3 (focus ring assessed from QSS source — pre-flagged).

**Closest existing app analog today:** `styles.py:73` (palette entry with the deferral comment).

**Sketch:** One-token change. Dark-mode partner `FOCUS_RING_DARK` defined under UPL-1.

**Open questions:** None.

---

#### UPL-14 — Opacity slider min/max range labels

**Category:** Layout / Accessibility
**Size:** XS
**Evidence triangulation:** 1 brief (visual ✓ M-4)
**Interaction primitives:** None

**What it is:** Add "0%" left and "100%" right `QLabel`s flanking the Opacity slider in `appearance_panel.py:_build_opacity_group()`, matching the `RANGE_LABEL_STYLE` pattern from `parameters_panel.py:160-170`.

**Why it matters:** Cross-panel inconsistency: Parameters sliders have flanking min/max range labels; Appearance Opacity slider does not. A user switching between panels encounters different slider affordances.

**Sources:** Visual M-4.

**Closest existing app analog today:** `appearance_panel.py:179-191` `_build_opacity_group` — only a centered value label, no flanking range labels.

**Sketch:** Mirror the `range_row` pattern from `parameters_panel.py:160-170`.

**Open questions:** None (subsumed by UPL-6 if `superqt.QLabeledSlider` is adopted).

---

### 4.5 Export / persistence

#### UPL-15 — Mesh export button (STL / OBJ / PLY)

**Category:** Export/persistence
**Size:** S
**Evidence triangulation:** 2 briefs (library ✓ E1 MeshIO, current-state-critic ✓ M-3)
**Interaction primitives:** [INT-93 mesh-export-button]

**What it is:** Add an "Export mesh…" button to `view_panel.py:_make_screenshot_group()` alongside the existing Screenshot button. On click: `QFileDialog.getSaveFileName` with "STL / OBJ / PLY" filter → `pyvista.PolyData.save(path)` (which handles all three formats natively without a new dep).

**Why it matters:** The View panel has a "Export" group that currently contains only a Screenshot button — the group name overpromises. CONTEXT.md §9 explicitly notes "Adding STL/OBJ/PLY export is one line: `mesh.save('file.stl')`."

**Sources:** Library E1 (MeshIO; or zero-new-dep via PyVista's native `save`); Current-state-critic M-3.

**Closest existing app analog today:** `view_panel.py:246-256` `_make_screenshot_group` — single button in an "Export" group.

**Sketch:** Use PyVista's native `save()` for STL/OBJ/PLY — no new dep. Wire via a `get_mesh` callback on `ViewPanel.__init__` (matching the `get_actor` / `get_plotter` pattern). Disable the button when `get_mesh()` returns `None` (no surface rendered yet). ~20 lines.

**Open questions:** VTU export (volumetric)? Out of scope — algebraic varieties are surfaces, not volumes.

---

#### UPL-25 — Dock state persistence (QSettings)

**Category:** Export/persistence
**Size:** S
**Evidence triangulation:** 1 brief (inspiration ✓ PC-4)
**Interaction primitives:** [INT-92 state-persistence-qsettings], [INT-6 dock-floatable]

**What it is:** Use `QSettings` to persist `MainWindow.saveState()` / `restoreState()` so dock positions, sizes, and float/tab states survive across launches.

**Why it matters:** Researchers who customize their layout (e.g. floating the Parameters dock out for second-monitor use) lose that layout on every app restart.

**Sources:** Inspiration PC-4.

**Closest existing app analog today:** `app.py` `MainWindow.__init__` — no `QSettings` calls today; design-system §7 entry for state persistence is explicitly underdeveloped.

**Sketch:** Standard QSettings pattern; key `MainWindow/state` with format-version prefix for forward-compat. UPL-5 collapse states piggyback on the same `QSettings` instance once both ship.

**Open questions:** Settings org/app name — pick before commit.

---

### 4.6 Interaction

#### UPL-16 — Parameter sweep VCR transport bar

**Category:** Interaction
**Size:** M
**Evidence triangulation:** 2 briefs (library ✓ D1 QPropertyAnimation, inspiration ✓ PC-3)
**Interaction primitives:** [INT-90 parameter-sweep-animation], [INT-2 slider-release-render], [INT-3 busy-cursor]

**What it is:** Add a "Sweep" control row to `parameters_panel.py` with: a `QComboBox` selecting which parameter to sweep + Play / Pause / Step `QPushButton`s. On Play, a `QTimer` walks the selected slider from min to max over user-configurable N seconds; renders fire on each step (respecting AI-9 re-entrancy guard).

**Why it matters:** The iconic Dwork ψ → 1 conifold sweep demo, the Hanson dwell-time animation — these are the highest-value visual demonstrations of algebraic-variety parameter spaces. The app has no sweep path at all today; this is the largest capability gap vs 2026 SOTA peer tools (inspiration's Theme C).

**Sources:** Library D1 (QPropertyAnimation already in PySide6); Inspiration PC-3 (ParaView VCR + Mathematica Manipulate Play per slider).

**Closest existing app analog today:** None — net-new control row in `parameters_panel.py`.

**Sketch:** QTimer-driven; `interval=int(duration_ms / steps)`. Each tick: increment slider tick by 1, fire `sliderReleased`. AI-9 guard around the render call. Add icons via UPL-4 (Play `mdi6.play`, Pause `mdi6.pause`, Step `mdi6.skip-next`). Busy cursor (INT-3) during sweep.

**Open questions:** Per-parameter sweep vs multi-parameter (track editor)? V1: single-parameter only.

---

#### UPL-20 — Surface history navigation (recently-used dropdown)

**Category:** Interaction
**Size:** S
**Evidence triangulation:** 1 brief (inspiration ✓ PC-8)
**Interaction primitives:** [INT-1 dropdown-cascade], [INT-5 keyboard-shortcut] (Alt+← / Alt+→)

**What it is:** Add browser-style back/forward arrows + a "Recent surfaces" dropdown beside the Variety / Model combo cascade, populated from a `deque(maxlen=8)` of (variety, model) tuples.

**Why it matters:** Cascading Variety → Model takes 4 clicks to switch surfaces; for a researcher exploring multiple surfaces in a session, this compounds quickly. 3D Slicer's module-toolbar history pattern is the proven solution.

**Sources:** Inspiration PC-8.

**Closest existing app analog today:** `app.py` Variety + Model combo cascade (~lines 100-130) — no history.

**Sketch:** `QToolButton` with `setPopupMode(InstantPopup)` + `QMenu` populated from the deque. Persist deque via QSettings (depends on UPL-25). Keyboard shortcut `Alt+Left` / `Alt+Right`.

**Open questions:** Deque scope — per-session (lose on quit) or persistent (survive restarts)? Persistent is better; depends on UPL-25.

---

#### UPL-21 — Per-parameter spinbox alongside slider

**Category:** Interaction
**Size:** S
**Evidence triangulation:** 1 brief (inspiration ✓ PC-7)
**Interaction primitives:** [INT-97 parameter-spin-box-alternative]

**What it is:** Add a compact `QDoubleSpinBox` beside each slider in `parameters_panel.py` for exact numeric entry. Slider drag is approximate; spinbox is exact.

**Why it matters:** Probing the exact Dwork conifold at ψ = 1.0000 currently requires mouse micro-adjustments on the slider. ParaView and superqt's `QLabeledSlider` both provide paired text-entry fallback for precision.

**Sources:** Inspiration PC-7.

**Closest existing app analog today:** `parameters_panel.py:_build_row` — slider + label only, no spinbox.

**Sketch:** Subsumed by UPL-6 if `superqt.QLabeledSlider` is adopted (it integrates the value label as an editable spinbox). If superqt is not adopted, add `QDoubleSpinBox` manually beside the slider.

**Open questions:** Width-budget for spinbox in a 320 px dock — may need narrower slider; PC-7 trade-off review in design pass.

---

#### UPL-23 — Surface-with-edges 3-way mode (radio buttons)

**Category:** Interaction
**Size:** XS
**Evidence triangulation:** 1 brief (visual ✓ L-5)
**Interaction primitives:** [INT-44 style-radio-or-toggle]

**What it is:** Replace the two checkboxes (Wireframe, Show edges) in Appearance's Display group with three mutually-exclusive radio buttons: Solid | Wireframe | Solid+Edges.

**Why it matters:** The two-checkbox setup is conceptually a three-way mode but implemented as two booleans, with "Show edges" silently ignored in wireframe mode. The radio-button approach matches the Shading group's correct Phong/Flat radio pair.

**Sources:** Visual L-5.

**Closest existing app analog today:** `appearance_panel.py:154-172` `_build_toggles_group` — two checkboxes; contrast with `appearance_panel.py:195-222` `_build_shading_group` (correct radio pattern).

**Sketch:** Mirror the shading-group `QButtonGroup` + `QRadioButton` pattern.

**Open questions:** None.

---

### 4.7 Status / feedback

#### UPL-19 — Status-bar warning badge persistence

**Category:** Status/feedback
**Size:** S
**Evidence triangulation:** 1 brief (inspiration ✓ PC-5)
**Interaction primitives:** [INT-70 status-warning-prefix], [INT-4 status-bar-feedback]

**What it is:** Add a persistent warning-count badge (small `QLabel`, right-aligned) to the status bar. When a `RuntimeWarning` fires during `_render_current`, append to an in-memory list AND increment the badge count. Clicking the badge opens a small dialog listing all warnings since launch.

**Why it matters:** Today the Dwork conifold warning fires in the status bar (`⚠ Conifold singularity detected …`); switching to another surface overwrites it. Researchers lose the audit trail. 3D Slicer's status-bar-X-icon-with-count pattern is the established solution.

**Sources:** Inspiration PC-5.

**Closest existing app analog today:** `app.py:_render_current` warning-capture block; `app.py:setStatusBar(...)`.

**Sketch:** `QLabel` widget added to `QStatusBar` via `statusBar().addPermanentWidget(...)`. List stored on `MainWindow`. Click handler opens `QDialog` with `QListView`.

**Open questions:** Should the badge persist across app restarts (QSettings) or session-only? Session-only is the v1.

---

#### UPL-22 — Viewport text overlay for empty / launch states

**Category:** Status/feedback
**Size:** S
**Evidence triangulation:** 1 brief (inspiration ✓ PC-9)
**Interaction primitives:** [INT-74 empty-clip-status-message] (extends to viewport), [INT-4 status-bar-feedback] (companion)

**What it is:** Add a `vtkTextActor` to the central viewport that renders guidance text in-canvas: "Choose a variety to begin" on launch (hidden on first render), "Domain is smaller than the surface — try increasing the radius" on empty-clip detection.

**Why it matters:** The empty viewport shows a dark grey rectangle with no affordance — the "Choose a variety to begin" status-bar text is small and below the canvas. An in-canvas overlay puts the entry-point hint where the user's eye already is.

**Sources:** Inspiration PC-9.

**Closest existing app analog today:** `app.py:_PLACEHOLDER` + status bar (off-canvas).

**Sketch:** `plotter.add_text("Choose a variety to begin", position="upper_edge", font_size=18, color=COLOR_MUTED)`. AI-3 unchanged (text actor added at live plotter time, not under offscreen testing).

**Open questions:** Color of overlay text — must clear AI-12 on dark `#2f2f2f` (target `#a0a0a0` or lighter).

---

#### UPL-24 — Empty Parameters panel guidance copy

**Category:** Tooltips/disclosure
**Size:** XS
**Evidence triangulation:** 1 brief (visual ✓ M-5)
**Interaction primitives:** [INT-7 tooltip-rich], [INT-42 cy3-context-banner] (pattern to extend)

**What it is:** Replace "(no parameters for this surface)" with two-line guidance: "This surface has fixed geometry — use the Appearance panel to change color, opacity, and shading."

**Why it matters:** The empty-parameter state offers no next-action guidance; users may interpret the empty panel as an error.

**Sources:** Visual M-5.

**Closest existing app analog today:** `parameters_panel.py:53-57` `self._empty_label = QLabel("(no parameters for this surface)")`.

**Sketch:** Two-line `QLabel` with `setWordWrap(True)`; mirror styling of the existing context-hint banner pattern.

**Open questions:** None.

---

### 4.8 Tooltips / disclosure

#### UPL-17 — KaTeX equation tooltip popover

**Category:** Tooltips/disclosure
**Size:** M
**Evidence triangulation:** 2 briefs (library ✓ F1, inspiration ✓ PC-12)
**Interaction primitives:** [INT-95 katex-tooltip-popover], [INT-7 tooltip-rich]

**What it is:** When the user hovers over a variety/subtype name in the combo box, render the canonical equation in publication-quality typography via KaTeX in a small `QWebEngineView` popup.

**Why it matters:** Current tooltips use unicode subscripts (`n₁`, `φ`, `ψ`) which render inconsistently across platforms. KaTeX renders identically everywhere, matching the typography researchers expect from LaTeX figure captions. SURFER/Imaginary.org and GeoGebra both showcase the equation as a first-class UI element.

**Sources:** Library F1 (KaTeX via QtWebEngineWidgets — already shipped with PySide6-Addons, zero new pip install); Inspiration PC-12.

**Closest existing app analog today:** `app.py` combo-box tooltips set via `Qt.ItemDataRole.ToolTipRole`.

**Sketch:** Pre-construct one `QWebEngineView` at app launch (~100-300 ms Chromium cold-start). Hover triggers `QWebEngineView.setHtml(katex_template.format(equation=eq_latex))`. KaTeX bundled locally (one-time copy from `npm install katex`) for offline reliability. ~50 lines. Minimum-viable alternative: `QToolTip` CSS font override in `APP_STYLESHEET` to standardize unicode-subscript rendering — 1-line fix in `styles.py`.

**Open questions:** Bundle ~280 KB of KaTeX vs CDN? Local bundle is the right answer for offline research use.

---

### 4.9 Camera / viewport (additional)

#### UPL-18 — Orientation cube gizmo in viewport corner

**Category:** Camera/viewport
**Size:** S
**Evidence triangulation:** 1 brief (inspiration ✓ PC-11)
**Interaction primitives:** [INT-23 camera-preset-fire-and-render], [INT-25 axes-overlay-toggle]

**What it is:** Add `plotter.add_camera_orientation_widget()` after `QtInteractor` construction in `app.py:MainWindow.__init__`. Gives a clickable in-viewport gizmo for camera presets (clicking the gizmo's +X face fires the same callback as the View panel's +X button).

**Why it matters:** Camera-preset buttons today are in the View dock on the left — spatially disconnected from the viewport. ParaView, Blender, 3D Slicer all embed orientation cubes in the canvas.

**Sources:** Inspiration PC-11.

**Closest existing app analog today:** `view_panel.py:_make_view_presets_group()` — buttons; `app.py:MainWindow.__init__` post-plotter construction.

**Sketch:** Single PyVista call. AI-1 safe (PyVista native). Wire click events to the same callbacks as the View panel preset buttons.

**Open questions:** Widget styling colors — must coordinate with UPL-1 dark mode.

---

#### UPL-26 — Camera-transition interpolation (QPropertyAnimation)

**Category:** Camera/viewport
**Size:** S
**Evidence triangulation:** 1 brief (library ✓ D1)
**Interaction primitives:** [INT-24 camera-transition-interp]

**What it is:** Replace instantaneous `reset_camera()` / `view_xy()` calls with a `QPropertyAnimation` on a custom QObject mediator that interpolates VTK camera position over 300 ms. When user clicks Front/Top/Side/Isometric, camera smoothly flies rather than snapping.

**Sources:** Library D1.

**Closest existing app analog today:** `view_panel.py` preset callbacks fire `plotter.view_xy()` etc. — instant transitions.

**Sketch:** Thin `CameraAnimator(QObject)` wrapping `plotter.camera.position`, `.focal_point`, `.up`. `QPropertyAnimation(self, b"position", duration=300, easingCurve=QEasingCurve.OutCubic)`. Each tick writes to the camera + calls `plotter.render()` (not `_render_current` — bypasses the AI-9 guard since no mesh regenerate happens).

**Open questions:** 300 ms vs 200 ms vs configurable. 300 ms is the desktop-app standard; configurable adds preference surface complexity.

---

### 4.10 Cross-cutting refactor / capture harness

#### UPL-27 — Capture harness: dock-wrapped panel captures

**Category:** Cross-cutting refactor (capture pipeline)
**Size:** XS
**Evidence triangulation:** 1 brief (current-state-critic ✓ M-4)
**Interaction primitives:** None (tooling)

**What it is:** Extend `render-panel-chrome.py` to wrap each panel in a bare `QDockWidget` before grabbing, so the captures include the dock title bar, drag handle, and float button. AI-3 still respected: `QDockWidget` outside `QMainWindow` does not host any `QtInteractor`.

**Why it matters:** Panel PNGs today do not show the dock title bar — but `styles.py:APP_STYLESHEET` carefully styles `QDockWidget::title` (`COLOR_DOCK_HEADER_BG`, 1px border, bold 12px text). This styling is invisible to panel-PNG critique without dock wrapping. Critic M-4: "a Tier-1 panel-chrome shakedown that claims to assess dock chrome must actually see dock chrome."

**Sources:** Current-state-critic M-4.

**Closest existing app analog today:** `render-panel-chrome.py:_grab()` calls `widget.grab()` on the bare panel.

**Sketch:** 5 lines per panel:
```
dock = QDockWidget("View")
dock.setWidget(view_empty)
dock.resize(DEFAULT_SIZE + QSize(0, 28))  # +28 for dock title bar
dock.show()
app.processEvents()
pix = dock.grab()
```
Update post-capture integrity check to compare dock-wrapped pairs.

**Open questions:** Filename convention — `view-dock-light-empty-default.png` or replace existing? Recommendation: replace; the dock wrapping is the more honest critique surface.

---

#### UPL-28 — Capture harness: dark-bg surface renders + focus-clear

**Category:** Cross-cutting refactor (visual scout pipeline)
**Size:** XS
**Evidence triangulation:** 1 brief (visual ✓ H-2 + L-3 [focus ring capture artifact])
**Interaction primitives:** None (tooling)

**What it is:** Two changes to the visual scout's render loop (in `agent-prompts.md` and `phase-discover.md` render-loop template): (1) add `p.set_background("#2f2f2f")` so surface renders match the app's real default background; (2) before `widget.show()` in panel captures, set `setFocusPolicy(Qt.FocusPolicy.NoFocus)` (or call `clearFocus()` after show) so the first-button-focused artifact doesn't appear in the captures.

**Why it matters:** Visual scout's own H-2 finding caught the white-bg gap; visual L-3 documented the spurious `+X` focus ring as a capture artifact. Both are scout-pipeline issues, not product bugs. Fixing them improves the evidence base for every future uplift.

**Sources:** Visual H-2 (white-bg surface renders); Visual L-3 (focus-ring on first-tab-stop button).

**Closest existing app analog today:** `agent-prompts.md` visual-scout prompt render-loop template; `render-panel-chrome.py:_grab()`.

**Sketch:** Two-line render-loop change + two-line scout-prompt update. Document in `source-registry §4` so the canonical render set always uses the matching background.

**Open questions:** None.

---

#### UPL-29 — Fix Qt.AA_ShareOpenGLContexts unqualified enum (AI-11)

**Category:** Accessibility (AI-invariant correctness)
**Size:** XS
**Evidence triangulation:** 1 brief (current-state-critic ✓ §6 audit)
**Interaction primitives:** None

**What it is:** Replace `Qt.AA_ShareOpenGLContexts` at `app.py:429` with `Qt.ApplicationAttribute.AA_ShareOpenGLContexts`.

**Why it matters:** AI-11 mandates qualified Qt enums. The shorthand works via backward-compat alias but emits a PySide6 deprecation warning. Pre-flagged in the prior `2026q2-panel-refresh` uplift and still present.

**Sources:** Current-state-critic §6.

**Closest existing app analog today:** `app.py:429`.

**Sketch:** One-line edit.

**Open questions:** None.

---

## 5. Cross-Cutting Tensions

### 5.1 Visual scout's "white-bg renders" finding (H-2) is a tooling issue, not a product gap

The visual scout rated white-bg renders HIGH for the scout pipeline; the product itself uses `#2f2f2f` correctly (UPL-3 already shipped). UPL-28 captures this as a tooling fix; UPL-1 (dark mode) addresses the product side (chrome / viewport alignment). Don't conflate.

### 5.2 Fermat quartic default-parameter severity (HIGH vs LOW)

Current-state-critic rates this HIGH (first-launch credibility); visual-scout rates it LOW (math correctness fine). UPL-8 resolves via Featured-view preset (preserves canonical math defaults; gives aesthetic on-ramp). Phase 4 should weight UPL-8 closer to MEDIUM-leaning-HIGH (the credibility argument is real).

### 5.3 superqt adoption couples UPL-5 + UPL-6 + UPL-21

If superqt is adopted, UPL-5 (collapsible), UPL-6 (throttled + labeled slider), and UPL-21 (spinbox alongside slider) all share the same dependency add. Bundle these into one PR or sequence them tightly. The single library adoption pays for three candidates.

### 5.4 Dark-mode requires multiple downstream chrome candidates to take dark-tokens into account

UPL-1 is foundational because UPL-10, UPL-11, UPL-12, UPL-13, UPL-22 all need dark-mode token equivalents to ship coherently. Phase 4 must sequence UPL-1 ahead of these, OR explicitly defer the dark variants of UPL-10..-22 to a follow-up.

### 5.5 The capture harness improvements (UPL-27, UPL-28) feed back into every future uplift

These are tooling investments — they improve every subsequent visual-scout brief. Phase 4 should weight them by future-multiplier value, not just current-uplift impact.

---

## 6. Already Considered + Rejected

- **Mayavi / matplotlib-3D / Plotly / k3d alternative renderers** — AI-1 violation; explicitly out of scope (CONTEXT.md §9).
- **`clip_box` for cube domain clip** — AI-4 violation; commit b68456f worked around with scalar clipping (interaction-vocabulary §8 INT-NO-2).
- **pymeshfix for mesh repair** — AGPL-3.0 license; incompatible with LGPL PySide6 redistribution model.
- **qfluentwidgets** — GPL-3.0 community edition; redistribution-blocking.
- **QtAds (PySide6-QtAds)** — hard `PySide6-Essentials==6.11.0` pin conflicts with the app's `PySide6>=6.6,<7` range; do not adopt this sprint.
- **Side-by-side split viewport (two QtInteractor panels)** — heavy; creates two VTK GL contexts; out of scope for a chrome-focused shakedown.
- **Full keyframe animation editor (track editor, spline curves)** — overkill; simple VCR sweep (UPL-16) is the right resolution.
- **Pipeline browser / scene tree (3D Slicer-style)** — app shows one object at a time; tree would be empty 99% of the time.
- **Categorical / scalar-field color mapping (ParaView transfer-function editor)** — app colors by solid color, not scalar field; not applicable.
- **trame (Kitware web framework)** — Apache-2.0 but heavy; would require pivoting away from QMainWindow; out of scope.
- **`QScintilla` code editor for equation entry** — GPL-3.0 (import-blocking); equation entry not in scope.
- **`numpy-stl`** — redundant with PyVista's native `mesh.save("file.stl")`.

---

## 7. Interaction-Vocabulary Index

| Primitive | Candidates using it |
|---|---|
| [INT-1 dropdown-cascade] | UPL-20 |
| [INT-2 slider-release-render] | UPL-6, UPL-16 |
| [INT-3 busy-cursor] | UPL-4, UPL-16 |
| [INT-4 status-bar-feedback] | UPL-19, UPL-22 |
| [INT-5 keyboard-shortcut] | UPL-4, UPL-20 |
| [INT-6 dock-floatable] | UPL-5, UPL-25 |
| [INT-7 tooltip-rich] | UPL-5, UPL-17, UPL-24 |
| [INT-23 camera-preset-fire-and-render] | UPL-8, UPL-18 |
| [INT-24 camera-transition-interp] | UPL-26 |
| [INT-25 axes-overlay-toggle] | UPL-18 |
| [INT-42 cy3-context-banner] | UPL-24 |
| [INT-43 swatch-color-picker] | UPL-2, UPL-3 |
| [INT-44 style-radio-or-toggle] | UPL-23 |
| [INT-70 status-warning-prefix] | UPL-19 |
| [INT-74 empty-clip-status-message] | UPL-22 |
| [INT-82 focus-ring-on-controls] | UPL-13 |
| [INT-90 parameter-sweep-animation] | UPL-16 |
| [INT-92 state-persistence-qsettings] | UPL-25 |
| [INT-93 mesh-export-button] | UPL-15 |
| [INT-94 dark-mode-stylesheet] | UPL-1 |
| [INT-95 katex-tooltip-popover] | UPL-17 |
| [INT-96 palette-template-per-variety] | UPL-2 |
| [INT-97 parameter-spin-box-alternative] | UPL-6, UPL-21 |

23 distinct primitives surfaced across 29 candidates — high vocabulary coverage.

---

## Candidate count summary

- Total: **29 candidates**
- Foundational: **2** (UPL-1 dark mode, UPL-2 variety palette)
- By category: Color/theme 3, Library/dep 3, Camera/viewport 5, Accessibility 4, Layout 1 (UPL-11), Interaction 5, Status/feedback 3, Tooltips/disclosure 1, Export/persistence 2, Cross-cutting refactor 3 (capture-harness + AI-11 fix)
- By size: XS 13, S 12, M 4, L 0
- By triangulation: 4-brief 1, 3-brief 3, 2-brief 6, 1-brief 19
