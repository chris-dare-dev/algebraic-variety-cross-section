# Algebraic Variety Viewer design-system inventory (read this BEFORE proposing changes)

**Purpose:** anchor every proposed UI upgrade to what the app *actually* has today.  Without this, scouts propose dark-mode toggles when the app is light-theme by deliberate choice, or propose tooltip-rich dropdowns when `VARIETY_TOOLTIPS` / `SUBTYPE_TOOLTIPS` already deliver that.

Loaded by **every scout at Phase 1 start** and by the **synthesizer at Phase 2 start**.  Cite specific entries here when surfacing a proposal.

This file is curated by hand from `CONTEXT.md`, `README.md`, `styles.py`, `app.py`, and the three panel modules.  When those change, update here.  Drift is expected after milestone deliveries — flag in your brief if you find divergence.

---

## 1. Stack snapshot (verify against `requirements.txt` at Phase 1 read)

| Layer | What | Why it constrains proposals |
|---|---|---|
| GUI framework | PySide6 ≥ 6.6, < 7 (LGPL) | **AI-1**: never propose PyQt6 (GPL surface change) |
| 3D widget | `pyvistaqt.QtInteractor` ≥ 0.11.4, < 0.12 — VTK render window in `QMainWindow` | **AI-1**: native VTK trackball; do NOT swap for matplotlib mpl_toolkits, Plotly, k3d, Mayavi, or raw VTK |
| Geometry engine | PyVista ≥ 0.46, < 0.49 + VTK (transitively) | **AI-4 / AI-5 / AI-6**: clip_scalar (NOT clip_box), `scalars=` kwarg required, marching-cubes pipeline for implicit / `_grid_to_polydata` for parametric |
| Implicit surfacing | scikit-image ≥ 0.22, < 0.27 — `measure.marching_cubes` | Gradient-direction normals are seeded BEFORE Taubin smoothing; `compute_normals()` rederives after smoothing |
| Numerics | NumPy ≥ 1.26, < 3 | Plain ndarray scalar fields; no JAX, no PyTorch, no CuPy |
| Test runner | pytest (Qt-free) | **AI-2**: no pytest-qt; tests are pure-NumPy / pure-PyVista / static-math |
| Python | 3.12 (3.10+ should work) | Type hints use 3.10+ syntax (`X \| Y`); generator functions in `surfaces.py` already use this |
| Stylesheet | Single `styles.py` module — palette constants + `APP_STYLESHEET` QSS string | All inline `setStyleSheet` calls reference the named constants (`HEADING_STYLE`, `MUTED_TEXT_STYLE`, `VALUE_MONO_STYLE`, `RANGE_LABEL_STYLE`).  Don't reintroduce hex literals at call sites. |
| Window chrome | `QMainWindow` + 3 `QDockWidget` (View left, Parameters right-top, Appearance right-bottom) + central `QtInteractor` | Docks are movable + floatable (Qt drag-handles).  Window default 1200×800. |
| Status feedback | `QStatusBar.showMessage(...)`; warnings prefixed with `⚠` via `warnings.catch_warnings(record=True)` | **AI-14**: surface RuntimeWarning soft signals (Dwork conifold), ValueError hard errors (no real zero set) |
| Re-entrancy | `self._computing` boolean guard in `_render_current` | **AI-9**: any new `processEvents()` call must respect this |
| Domain clipping | Sphere (Euclidean distance) and cube (Chebyshev) modes; both via `clip_scalar(scalars="_dist", value=r, invert=True)` | **AI-4 / AI-5**: scalar clipping only; `clip_box` is reversed/unreliable |

## 2. Color palette (in `styles.py`)

App is **light-themed** today.  The palette is curated for WCAG AA contrast on a `#f0f0f0`-ish background (the Qt default light-mode chrome).  No dark-mode QSS exists.

| Constant | Value | Purpose | Notes |
|---|---|---|---|
| `COLOR_MUTED` | `#5a5a5a` | Muted secondary text — slider descriptions, status-bar default | **AI-12**: 5.4:1 contrast on `#f0f0f0` (AA pass).  Replaces the former `#888` (3.5:1 — AA fail). |
| `COLOR_VALUE` | `#333333` | Monospace value readouts — slider current value | High contrast; not competing with primary labels |
| `COLOR_DOCK_HEADER_BG` | `#e8edf2` | Dock title-bar background — subtle blue-gray | Visually distinct from panel body |
| `COLOR_DOCK_HEADER_BORDER` | `#c5cdd8` | Dock title-bar bottom border | 1px |
| `COLOR_RESET_BTN_BG` | `#f5e8e8` | Reset-to-defaults button BG | Reads as "secondary / destructive" relative to primary buttons |
| `COLOR_RESET_BTN_BORDER` | `#d4b4b4` | Reset-to-defaults border | |
| `COLOR_RESET_BTN_HOVER_BG` | `#f0d0d0` | Reset-to-defaults hover | |
| (focus ring color in QSS) | `#5b9bd5` | Keyboard focus ring `outline` | Visible on `QAbstractButton:focus`, `QComboBox:focus`, `QSlider:focus` |

**AI-13 reminder:** colors flowing into PyVista (`Plotter.add_mesh(color=...)`, `set_plot_theme`) must be 6-digit hex.  Qt stylesheet hex (above) is a separate surface — short hex would also work there but consistency is preferred.

**On theming as a convention, not invariant:** the app's "light theme by default" is a CONVENTION, not an invariant — adding a dark mode is on the candidate-surface (§7).  Unlike app-invariants AI-1 through AI-15, there's no rule against alternative palettes; a parallel dark `STYLESHEET_DARK` is fair game.

## 3. Typography (in `styles.py`)

| Class / token | Purpose | Notes |
|---|---|---|
| `HEADING_STYLE` | `font-weight: bold; font-size: 13px; padding: 2px 0;` | Panel section headings, group-box alternatives |
| `LABEL_STYLE` | `font-size: 12px;` | Default slider/checkbox labels |
| `SMALL_LABEL_STYLE` | `font-size: 11px;` | Small descriptive / help text |
| `MUTED_TEXT_STYLE` | `color: #5a5a5a; font-size: 10px;` | Subtitles, descriptions |
| `VALUE_MONO_STYLE` | `font-family: monospace; font-size: 11px; color: #333333;` | Numeric value readouts |
| `RANGE_LABEL_STYLE` | `font-family: monospace; font-size: 9px; color: #5a5a5a;` | Min/max range markers under sliders |
| `QStatusBar` (in QSS) | `font-size: 11px; color: #5a5a5a;` | Status bar text |
| `QGroupBox` (in QSS) | `font-size: 11px; font-weight: bold;` | Group-box titles inside panels |

There is no math typography stack (no KaTeX, no MathJax — equations live in plain-text tooltips with unicode super/subscripts).  Adding a rendered-math tooltip / overlay is a candidate-surface (§7).

## 4. Component primitives (current inventory)

### Top control bar (in `app.py`)
- `Variety:` QComboBox — outer keys of `VARIETIES`; placeholder `— Select —`
- `Model:`  QComboBox — inner keys; rebuilt when variety changes
- Both combos carry **rich tooltips** with equations + symmetry + references (from `VARIETY_TOOLTIPS` / `SUBTYPE_TOOLTIPS`)

### Central 3D viewport (in `app.py`)
- `pyvistaqt.QtInteractor` — VTK trackball rotate / scroll-wheel zoom / Shift-drag pan
- Tooltip on the widget itself spells out the mouse bindings

### View dock (left, in `view_panel.py`)
- Camera-preset grid: Reset / Front / Top / Side / Isometric (each followed by a forced `render()`)
- Domain-clip: Off / Sphere / Cube + radius slider; an outline overlay visualizes the clip region
- Scene aids: bounding box, world-axes triad, grid axes (toggle checkboxes)
- Screenshot: PNG with chooser dialog

### Parameters dock (right top, in `parameters_panel.py`)
- Dynamically rebuilt every time you switch surfaces — sliders generated from each `Surface.params` `ParamSpec` list
- Each slider: label, current value (monospace), min/max range markers, suffix unit if any, tooltip with `description`
- Slider value emits on **release only** (NOT during drag) to keep marching cubes responsive
- "Reset all to defaults" button — object name `resetDefaultsBtn` — styled distinctly via `styles.py` QSS
- CY3 banner: when the variety is Calabi–Yau 3-fold, a context label reminds the user that figures are 2D shadows

### Appearance dock (right bottom, in `appearance_panel.py`)
- Surface color: `QColorDialog` swatch
- Opacity: 0–100% slider
- Style: solid / wireframe / surface-with-edges (radio or toggle)
- Lighting: flat / smooth / Phong shading toggles
- Background: solid color picker, gradient on/off

### Status bar (in `app.py`)
- Default: surface label + vertex count + face count + current parameter values
- Errors: `ValueError` from generator → message displayed verbatim
- Warnings: RuntimeWarning extracted and prefixed `⚠` (currently the Dwork conifold soft warning)

### Keyboard shortcuts (in `app.py`)
- `Ctrl + R` — reset camera (via `QShortcut(QKeySequence...)`)
- `Ctrl + Shift + S` — screenshot
- `Ctrl + D` — reset all parameter sliders to defaults

## 5. Accessibility constraints (non-negotiable)

### Text contrast (AI-12)
Every text color must clear WCAG 2.1 AA.  The current `COLOR_MUTED = #5a5a5a` on `#f0f0f0` is 5.4:1 — clean.  Don't reintroduce `#888` or lower-contrast tokens.

### Focus visibility (AI-12)
`APP_STYLESHEET`'s `outline: 2px solid #5b9bd5; outline-offset: 1px;` is applied to `QAbstractButton:focus`, `QComboBox:focus`, `QSlider:focus`.  Don't strip this from custom widgets without restoring an equivalent.

### Slider-release feedback (INT-2)
The slider-release-only render policy is intentional — real-time render during drag would saturate marching cubes (~0.5s per call).  Don't propose `valueChanged` (every tick) — propose `sliderReleased` (one event).

### Tooltip discipline
Every dropdown item carries `Qt.ItemDataRole.ToolTipRole` (set in `app.py` from `VARIETY_TOOLTIPS` / `SUBTYPE_TOOLTIPS`).  Sliders carry `description` text from `ParamSpec`.  Don't add UI affordances without tooltips.

### Keyboard surface
Currently 3 shortcuts (§4).  Tab order is Qt's default derivation.  Expanding the shortcut surface is a candidate (§7).

## 6. Patterns that have already been considered and rejected (CONTEXT.md §9 — DON'T re-propose)

| Pattern | Why rejected |
|---|---|
| State persistence (last surface, slider values, window layout via `QSettings`) | Discussed in CONTEXT.md §9 — explicitly considered, skipped (every launch starts fresh is the current convention).  RECONSIDERABLE if scope is clean. |
| First-launch auto-render of a default surface | UX agent concluded "presumptuous in a research tool"; opens to `— Select —` placeholder.  RECONSIDERABLE for power-user mode. |
| Confirmation dialog on Reset to Defaults | Action is non-destructive; the dialog interrupts flow.  Don't re-propose. |
| `pytest-qt` UI end-to-end tests | **AI-2**: macOS Qt+VTK GL context segfaults under offscreen.  Don't re-propose without a macOS workaround. |
| Constructing `MainWindow()` under `QT_QPA_PLATFORM=offscreen` | **AI-3**: segfaults during VTK GL context creation.  Hard fail. |
| 3D mesh export (STL / OBJ / PLY) | One-line addition (`mesh.save("file.stl")`).  Was explicitly noted as a missing feature in §9 — UNDERDEVELOPED candidate, not rejected. |
| `clip_box(invert=...)` on PolyData | **AI-4**: invert semantics broken; commit `b68456f` worked around this with scalar clipping. |
| `auto_orient_normals=True` on Hanson cross-sections | **AI-7**: disconnected patches can't be coherently oriented; commit `f58ee05`. |
| Short hex (`#888`) in colors flowing to PyVista | **AI-13**: PyVista's parser rejects short hex. |

## 7. What's UNDERDEVELOPED (candidate surface)

The discover scouts will likely converge on a subset of these — surface them prominently if your scan finds confirming evidence.

- **Dark-mode toggle** — current app is light-only; a dark color palette would suit the math-research audience (3Blue1Brown / Quanta-style chrome).  Note: this is a sizable candidate; the entire `styles.py` palette would gain a parallel dark variant.
- **State persistence via `QSettings`** — last-used surface, slider values, dock layout, color choices.  CONTEXT.md §9 noted as an open opportunity.
- **3D mesh export (STL / OBJ / PLY)** — `mesh.save("file.stl")` one-liner.  Researchers often want to load surfaces in Blender / Meshmixer / GeoGebra.
- **Math-typography tooltip / overlay** — equations currently render as plain-text unicode; a rendered KaTeX/MathJax tooltip popover would dramatically lift fidelity.
- **Empty-clip overlay annotation** — when domain radius is set so small that the surface vanishes, the status bar says so but the canvas is silent.  A VTK text overlay would help.
- **Variety-family color theming** — every K3 model shares a default surface color, every Enriques another, etc.  Currently they all get the same `#9aa6c8` slate.  Cheap visual cue for the math reader.
- **First-launch tour / "click any variety" hint** — empty viewport on launch with `— Select —` placeholder; visitors don't always realize the cascading-dropdown UX.
- **Animated parameter sweep** — slider-driven scrubber that animates a parameter from min → max over N seconds; great for teaching the deformation visually.  Hanson dwell time / Dwork ψ sweep would be the iconic demos.
- **Side-by-side surface comparison** — two viewports, one model each; useful for K3 ↔ Kummer or Enriques figure family comparison.
- **HiDPI / Retina scaling polish** — README notes "Run with `QT_AUTO_SCREEN_SCALE_FACTOR=1`" as a workaround for jumpy sliders.  Wrapping this into `app.py`'s `if __name__ == "__main__"` is a polish candidate.
- **Status-bar warning badge persistence** — current warnings show once and disappear when the next render writes.  A small persistent badge (`⚠ N warnings`) clickable to a transient sheet would help.
- **Parameter min/max field input** — sliders force discrete steps; some researchers want to type an exact ψ = 1.0001 to probe the conifold.  A spin-box alternative per slider is a UX surface.
- **Bounding-box / scene-aid color tokens** — currently white-ish on the light background; harder to see than ideal.  Subtle desaturated tokens would help.
- **Tooltip equation rendering: at minimum, format-preserving** — the existing tooltip text uses unicode subscripts (`n₁`, `n₂`) and Greek (φ, ψ, λ); some platforms render these poorly without an explicit `QToolTip` font CSS override.
- **Help menu / About dialog with mathematical citations** — currently no menu bar at all; tooltips carry the citations but there's no central reference card.
- **`prefers-reduced-motion`-style toggle for VTK camera transitions** — VTK doesn't animate by default, but if camera transitions are added (smooth view-preset interpolation), they should be optional.
- **Per-Variety palette templates in `Appearance`** — saved "K3-default" / "Hanson-iconic" presets you can pick from a combo.

## 8. How to anchor a proposal to this file

Every candidate in the synthesis catalog must cite ONE of:

- A specific source file:line that's the closest existing implementation (cite `app.py`, `surfaces.py`, `view_panel.py`, `parameters_panel.py`, `appearance_panel.py`, or `styles.py`)
- A named constant or class from `styles.py` to be applied / extended (`HEADING_STYLE`, `COLOR_MUTED`, …)
- An app invariant (AI-1 … AI-15 in `app-invariants.md`) that the proposal must honor
- A pattern in §7 above (the "underdeveloped" list)
- A specific interaction primitive from `interaction-vocabulary.md` (cite `[INT-N]`)

If none of those apply, the proposal is probably not Algebraic-Variety-Viewer-shaped — push back at synthesis.

---

## §9 — House thesis

> **Status note (2026-07):** §1–§8 above were authored 2026-05 and predate the r3 single-root restructure, the dark-theme launch default, the Fano 3-fold family, the parameter-grid panel, and the QThread render worker (`render/worker.py`).  Treat §1–§8 as an inventory in need of a refresh (real paths are now `app.py`, `_qt/styles.py`, `_qt/panels/*`, `varieties/`).  **§9 is ground-truthed against the current code** and is the load-bearing house-thesis contract per `frontend-design-language.md` §9.

**This section fills in `frontend-design-language.md` §9 for this repo.**  The canon is product-neutral and written in web mechanics; this overlay is the one place the Algebraic Variety Viewer's thesis, anti-references, and surface map live — translated to PySide6/Qt (tokens → `_qt/styles.py` `PALETTE_LIGHT`/`PALETTE_DARK` + `.qss`; motion → `QPropertyAnimation` + `[INT-N]`; reduced-motion → a QSettings toggle, not a media query; perf → startup-render + camera frame time; a11y → focus/tab order + `.qss` WCAG-AA contrast).  The `frontend-uplift-art-direction-scout` MUST read this before proposing a thesis or directions.

### Visual thesis (one sentence — swap-test-passing)

> **The Algebraic Variety Viewer is a darkroom for algebraic geometry: the cross-section is the luminous specimen, the Qt chrome is the recessive instrument around it, and every colour, contrast, and readout is a measured, sourced claim about the mathematics — never decoration.**

*Swap-test:* substitute a general-purpose 3-D viewer (ParaView, Blender, a generic mesh tool) and the sentence collapses — none of them makes a "measured, sourced claim about the mathematics," and none is anchored to *algebraic geometry* as its subject.  It holds specifically for this app, so it is a thesis, not a category description.

**Invariants the thesis protects** (these are the binding part — NOT a page silhouette or style recipe; a run may satisfy them through any `frontend-design-language.md` §8 direction seed or a genuinely new one, but cloning a specific shell is BAN-15):

1. **Specimen-first.**  The rendered surface, in the dark `#2f2f2f` viewport (`_qt/styles.py:BG_VIEWPORT`), is always the brightest, most saturated thing on screen.  Chrome stays achromatic and recessive; no panel, accent, or icon competes with the geometry.  Dark is the launch default *because* the viewport is always dark — the chrome frames the specimen, it is not a mood.
2. **Honest instrumentation** (AI-14, AI-15).  The app never implies a render is more than a cross-section or a projected shadow.  The Calabi–Yau "this is a 2-D shadow, not the 6-D variety" banner (`[INT-42]`), the vertex/face counts, the `⚠` warning prefix (`[INT-70]`), and the math-cited tooltips (`[INT-7]`) are load-bearing, not optional dressing.
3. **Measured, not styled** (AI-12, AI-13).  Every colour and contrast is numerically justified in BOTH themes (`_qt/styles.py` carries per-token WCAG ratios).  Colour that carries no meaning — variety-family identity, state, provenance — does not ship.  The four per-variety surface colours (K3 periwinkle `#8e9ed4`, Enriques ochre `#c4a882`, CY3 teal-cobalt `#85b5d0`, Fano sage `#8fbe85`; ≥24° hue-separated, each ≥5:1 on the viewport) are a *measured identity cue* — the exception that proves the rule, not licence for decorative colour.
4. **Calm at repeat-use.**  This is a long-session research instrument.  Motion is functional feedback only — busy-cursor (`[INT-3]`), status (`[INT-4]`), slider-release render (`[INT-2]`), camera-fire-and-render (`[INT-23]`) — never spectacle, never motion for its own sake.  There is no marketing surface to animate.
5. **Keyboard-and-contrast reachable** (AI-11, AI-12).  Every control is tab-reachable with a visible focus ring in both themes; qualified Qt enums throughout; WCAG AA text.  Accessibility is debt that ships first (the Phase 4 `a11y-safety-debt` lane), never a candidate to rank away.

### Named anti-references (what this app must never become)

The canon's anti-reference is the web "generic AI dashboard" (navy + neon).  Its *native Qt* analogues — the plausible failure modes for THIS app — each mapped to the BAN token it exemplifies:

| Anti-reference (Qt-native) | What it looks like | BAN-N |
|---|---|---|
| **The neon sci-fi HUD viewer** | Glowing cyan/green wireframes, gradient-filled or glassmorphic docks, accent-glow borders "energising" the dark theme, an accent-coloured icon chip on every button. | BAN-1, BAN-3, BAN-8 |
| **The ParaView property-wall** | Every control at equal weight in an undifferentiated grey scroll of collapsible trees — no focal element, no lede, the viewport no longer the subject; uniform medium density everywhere. | BAN-5, BAN-14 |
| **The rainbow-colormap chrome** | A jet/rainbow colormap or a different saturated hue applied to every widget so the palette becomes decoration; the `⚠`/error semantic colours diluted by decorative colour elsewhere. | BAN-6, BAN-11 |
| **The template "welcome" launcher** | A first-run splash — "Welcome to Algebraic Variety Viewer," quick-action tiles, a KPI-style stat row — replacing the honest `— Select —` empty state. | BAN-10, BAN-13 |
| **Status-bar badge soup** | Coloured status pills scattered across the status bar / panels instead of one honest line (label + vertex/face counts + `⚠`). | BAN-7 |
| **Borrowed-shell syndrome** | Recreating the canon's own *web* house look (ink + violet wash + Space Grotesk + numbered eyebrows), or another repo's dashboard shell, as this native Qt app's identity. | BAN-15 |

*Concrete "never again" baseline:* the app's own pre-2026q2 chrome — the former `#888` muted text (AA-failing at ~3.5:1), the flat undifferentiated single-`#9aa6c8`-slate-on-every-variety look, and the un-themed light-only palette — is kept as the baseline this thesis steers away from.

### Surface map (every view is S-2 / tool)

There is **no S-1 or S-1m surface** in this app: no marketing, landing, hero, login, or onboarding exists.  The whole product is a native Qt tool.  This is why experiential motion is INERT here and the `frontend-uplift-experiential-scout` is not dispatched by default (`frontend-design-language.md` §3 / motion-vocabulary §0).

| Surface | Class | Direction / discipline |
|---|---|---|
| Startup / empty state (`— Select —` + empty dark viewport, `app.py:_PLACEHOLDER`) | **S-2** | The single first-impression moment (closest analogue to S-1m, but governed by S-2 discipline).  An *honest* empty-state affordance — a quiet hint to pick a variety — is defensible; a spectacle splash is BAN-10/13 and BLOCKED. |
| Central 3-D viewport (`_qt/panels/view.py` → `QtInteractor`) | **S-2** | The work surface and the sole focal element.  Specimen-first.  VTK trackball; any camera-preset transition is optional + reduced-motion-gated (QSettings), and every camera state change ends in `render()` (`[INT-23]`). |
| View dock (camera presets, domain clip, scene aids, screenshot, mesh export) | **S-2** | Recessive instrument panel; authored density; achromatic chrome. |
| Parameters dock (dynamic sliders, reset-to-defaults, CY3 banner) | **S-2** | Instrument panel; tabular-mono readouts; slider-release render (`[INT-2]`). |
| Parameter-grid panel (`_qt/panels/parameter_grid_panel.py`, `QGraphicsScene` draggable dot) | **S-2** | The one bespoke direct-manipulation canvas; the same measured-token discipline applies (drawn with `GRID_*` palette tokens). |
| Appearance dock (surface/background colour, opacity, style toggles, shading) | **S-2** | Instrument panel; colour choices route through the measured `PALETTE_*` tokens (6-digit hex, AI-13). |
| Status bar + menu bar (Theme menu: Light / Dark / Follow system) | **S-2** | One honest status line; recessive chrome; theme-aware via the `.qss` role cascade. |

**Chosen default direction:** a `frontend-design-language.md` §8 **D-A "Precision Instrument"** core — quiet dark material, hairline structure, mono data voice, near-zero decoration, recognizability from typographic discipline and the measured per-variety identity colours — is the standing default for every S-2 surface here.  There are no threshold/marketing surfaces, so D-C/experiential craft has nowhere to land.  A run may argue a different direction from the frame, but never by importing spectacle onto the tool surface (BAN-12).
