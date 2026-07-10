# Algebraic Variety Viewer design-system inventory (read this BEFORE proposing changes)

**Purpose:** anchor every proposed UI upgrade to what the app *actually* has today. Without this,
scouts propose a dark-mode toggle that already shipped, or tooltip-rich dropdowns that
`varieties/tooltips.py` already delivers.

Loaded by **every scout at Phase 1 start** and by the **synthesizer at Phase 2 start**. Cite specific
entries here when surfacing a proposal.

**Verified against the tree on 2026-07-10** (`app.py`, `_qt/styles.py`, `_qt/panels/*`, `varieties/*`,
`render/worker.py`, `cross_section/clip.py`, `requirements.txt`, `pyproject.toml`). Line numbers drift —
re-read the source at the Phase 1 read and treat the code, not this file, as authoritative. If you find
divergence, say so in your brief.

> **Restructure note.** The flat `styles.py` / `view_panel.py` / `parameters_panel.py` /
> `appearance_panel.py` / `surfaces.py` modules **no longer exist**. They moved to `_qt/` and
> `varieties/` in the `restructure-feature-subpackages-2026q2-r2` batch (see `MOVES.md`). A proposal
> citing an old path is citing a file that is not there.

---

## 1. Stack snapshot (verify against `requirements.txt` at Phase 1 read)

| Layer | What | Why it constrains proposals |
|---|---|---|
| GUI framework | PySide6 ≥ 6.6, < 7 (LGPL) | **AI-1**: never propose PyQt6 (GPL surface change) |
| 3D widget | `pyvistaqt.QtInteractor` ≥ 0.11.4, < 0.12 — VTK render window in `QMainWindow` | **AI-1**: native VTK trackball; do NOT swap for matplotlib, Plotly, k3d, Mayavi, or raw VTK |
| Geometry engine | PyVista ≥ 0.46, < 0.49 + VTK (transitively) | **AI-4 / AI-5 / AI-6**: `clip_scalar` (NOT `clip_box`), `scalars=` kwarg required |
| Implicit surfacing | **`vtkFlyingEdges3D`** via `varieties/_marching.py::_marching_cubes_to_polydata` (`grid.contour(method=...)`) | **scikit-image is GONE.** Do not propose `skimage.measure.marching_cubes`. Flying Edges has different vertex ordering than skimage; `_marching.py` documents the difference. *(Until 2026-07-10 the module still carried a vestigial module-level `from skimage import measure` — unused, and declared in neither `requirements.txt` nor `pyproject.toml`. It survived only because a stale `skimage` sat in the local `.venv`; a clean install would have raised `ImportError`. Removed.)* |
| Field kernels | **numba ≥ 0.65, < 0.66** — `@njit` kernels in `varieties/_kernels.py` | **LANDMINE:** `numba.config.THREADING_LAYER = "workqueue"` MUST appear at the TOP of that module, *before* `from numba import njit`. The setting is process-global and cached at numba import; setting it after is a silent no-op. The default `omp` layer is incompatible with VTK's threading on macOS. |
| Icons | **qtawesome ≥ 1.4.2, < 2** — `_qt/icons.py` is the single `QIcon` source | **LANDMINE:** qtawesome is **lazy-imported** (a `_qta` sentinel stays `None` until first use) because populating its icon-font cache costs ~150–200 ms at import. A test enforces that `_qt/icons.py` does not import qtawesome at module load. Don't hoist the import. |
| Numerics | NumPy ≥ 1.26, < 3 | Plain ndarray scalar fields; no JAX, no PyTorch, no CuPy |
| Architecture gates | `import-linter`, `libcst`, `pydeps`, `coverage` | Layer boundaries between `_qt/`, `varieties/`, `render/`, `cross_section/` are lint-enforced. A proposal that has a panel import a variety kernel directly will fail CI. |
| Test runner | pytest (Qt-free), `pytest.ini` → `testpaths = tests` | **AI-2**: no `pytest-qt`; tests are pure-NumPy / pure-PyVista / static-math |
| Python | `requires-python = ">=3.12"` | 3.10+ union syntax (`X \| Y`) is used throughout |
| Stylesheet | **`_qt/styles.py`** (~708 lines) — `PALETTE_LIGHT` + `PALETTE_DARK` dicts (28 tokens each), `VARIETY_DEFAULT_COLOR` / `_DARK`, and a QSS builder | All call-site styling references named constants (`HEADING_STYLE`, `MUTED_TEXT_STYLE`, `VALUE_MONO_STYLE`, `RANGE_LABEL_STYLE`). Don't reintroduce hex literals at call sites. |
| Window chrome | `QMainWindow` + **menu bar** (`&File`, `Theme`) + 3 `QDockWidget` ("View" left, "Appearance" + "Parameters" right) + central `QtInteractor` | Docks are movable + floatable. Window default 1200×800 (`app.py:115`), restored from `QSettings` (§6). |
| Rendering | **`QThreadPool` + `QRunnable`** — `render/worker.py::MeshWorker` + `WorkerSignals` | It is **not** a `QThread`. Results return on `finished = Signal(object)` carrying a `MeshResult`, delivered by `QueuedConnection`. |
| Re-entrancy | `_computing` **+ `_pending_render`** queue-latest guard in `app.py` | **AI-9**: a request arriving mid-render sets `_pending_render` rather than being dropped. Any new `processEvents()` must respect the guard. |
| Status feedback | `QStatusBar.showMessage(...)`; warnings prefixed `⚠` | **AI-14**: RuntimeWarning → soft signal, ValueError → hard error. A `_render_busy_spinner` widget exists precisely because `showMessage` fires on *every* render event and would obscure a transient busy message. |
| Domain clipping | `cross_section/clip.py` — sphere (Euclidean) and cube (Chebyshev), both via `clip_scalar(scalars="_domain_dist", invert=True)` | **AI-4 / AI-5**: scalar clipping only; `clip_box` invert semantics are broken on PolyData |

## 2. Colour palette (in `_qt/styles.py`)

**The app launches DARK.** `app.py:293` sets `self._active_theme = "dark"`. The `Theme` menu offers
**Dark / Light / Follow system** (a `QActionGroup`). Two full palettes exist: `PALETTE_LIGHT` (`:64`)
and `PALETTE_DARK` (`:242`), 28 tokens each.

**`BG_VIEWPORT` is `#2f2f2f` in BOTH palettes.** The 3-D viewport never lightens. The *chrome* themes;
the specimen does not. This is the mechanical basis of the §9 "specimen-first" invariant — a proposal
that lightens the viewport contradicts the house thesis.

| Token | Light | Dark | Purpose |
|---|---|---|---|
| `BG_VIEWPORT` | `#2f2f2f` | `#2f2f2f` | 3-D viewport — identical in both themes |
| `BG_PANEL` | `#f0f0f0` | `#252526` | Dock / panel body |
| `TEXT_MUTED` | `#5a5a5a` | `#a0a0a0` | Muted secondary text |
| `TEXT_VALUE` | `#333333` | `#e0e0e0` | Monospace value readouts |
| `FOCUS_RING` | `#3c82c4` | `#5b9bd5` | Keyboard focus outline — **per-theme**, not a single constant |
| `BORDER_SWATCH` | `#333333` | `#888888` | Colour-swatch border (`_border_for_theme`) |

**Contrast, computed rather than copied** (WCAG 2.1 relative luminance, text on `BG_PANEL`):

| Pair | Ratio | AA |
|---|---|---|
| light `TEXT_MUTED` `#5a5a5a` on `#f0f0f0` | **6.05:1** | pass |
| light `TEXT_VALUE` `#333333` on `#f0f0f0` | **11.09:1** | pass |
| dark `TEXT_MUTED` `#a0a0a0` on `#252526` | **5.86:1** | pass |
| dark `TEXT_VALUE` `#e0e0e0` on `#252526` | **11.60:1** | pass |
| the retired `#888` on `#f0f0f0` | **3.11:1** | **fail** |

(An earlier revision of this file quoted 5.4:1 and 3.5:1 for the first and last rows. Both were wrong.)

**Focus ring** is emitted by the QSS builder as `outline: 2px solid {palette["FOCUS_RING"]}` at
`_qt/styles.py:673 / :679 / :685` — applied to `QAbstractButton:focus`, `QComboBox:focus`,
`QSlider:focus`. Don't strip it from a custom widget without restoring an equivalent (**AI-12**).

**Per-variety surface colours** (`VARIETY_DEFAULT_COLOR`, `:180`; dark variant `:200`) — a *measured
identity cue*, the one sanctioned use of chroma:

| Variety | Colour | Contrast on the `#2f2f2f` viewport |
|---|---|---|
| K3 surface | `#8e9ed4` periwinkle | 5.09:1 |
| Enriques surface | `#c4a882` ochre | 5.91:1 |
| Calabi–Yau 3-fold | `#85b5d0` teal-cobalt | 6.07:1 |
| Fano 3-fold (ρ=1) | `#8fbe85` sage | 6.29:1 |

All clear 5:1 against the viewport. Colour that carries no meaning — family identity, state,
provenance — does not ship (§9).

**Legacy flat aliases.** `COLOR_MUTED`, `COLOR_VALUE`, `COLOR_DOCK_HEADER_BG`, `BG_VIEWPORT`, … still
exist from `_qt/styles.py:336` onward, but they simply alias **`PALETTE_LIGHT`**. They are a
compatibility shim, not the theme source. Read the palette dicts.

**AI-13 reminder:** colours flowing into PyVista (`add_mesh(color=...)`, `set_plot_theme`) must be
6-digit hex. PyVista's parser rejects short hex.

## 3. Typography (in `_qt/styles.py`)

| Class / token | Value | Purpose |
|---|---|---|
| `HEADING_STYLE` | `font-weight: bold; font-size: 13px; padding: 2px 0;` | Panel section headings |
| `LABEL_STYLE` | `font-size: 12px;` | Default slider / checkbox labels |
| `SMALL_LABEL_STYLE` | `font-size: 11px;` | Small descriptive / help text |
| `MUTED_TEXT_STYLE` | `color: {TEXT_MUTED}; font-size: 10px;` | Subtitles, descriptions |
| `VALUE_MONO_STYLE` | `font-family: monospace; font-size: 11px; color: {TEXT_VALUE};` | Numeric value readouts |
| `RANGE_LABEL_STYLE` | `font-family: monospace; font-size: 9px; color: {TEXT_MUTED};` | Min/max range markers under sliders |
| `QStatusBar` (QSS) | `font-size: 11px;` | Status bar text |
| `QGroupBox` (QSS) | `font-size: 11px; font-weight: bold;` | Group-box titles |

There is still no math-typography stack (no KaTeX, no MathJax). Equations live in plain-text tooltips
with unicode super/subscripts. A rendered-math tooltip remains a candidate (§7).

## 4. Component primitives (current inventory)

### Menu bar (`app.py`)
- **`&File`** → `Export Mesh…` (`Ctrl+Shift+E`, `app.py:1391–1414`)
- **`Theme`** → Dark / Light / Follow system (`app.py:1703`, `QActionGroup`). Swapping the theme
  re-invokes `refresh_icons(theme)` on all three icon-bearing panels.

### Top control bar (`app.py`)
- `Variety:` / `Model:` `QComboBox` — placeholder `— Select —` (`app.py:64`, `_PLACEHOLDER`)
- Both carry rich tooltips (equations + symmetry + references) from `varieties/tooltips.py`

### Central 3-D viewport (`app.py`)
- `pyvistaqt.QtInteractor` — VTK trackball rotate / scroll zoom / Shift-drag pan; the widget's own
  tooltip spells out the mouse bindings. Background is `BG_VIEWPORT` in **both** themes.

### View dock (`_qt/panels/view.py::ViewPanel`)
- Camera presets: Front / Top / Side / Isometric, each followed by a forced `render()` (**INT-23** —
  a camera-state change without a follow-up `render()` is the canonical bug)
- `Reset Camera`
- Domain clip: Off / Sphere / Cube + radius slider + `Show clip outline`
- Scene aids: bounding box, world-axes triad, grid axes
- `Screenshot` (PNG chooser)
- **`Export STL…`** — print-ready and clip-aware; disabled until a mesh exists
  (`set_export_stl_enabled`), emits `export_stl_requested` for `MainWindow._on_export_stl_print`
- Icons are qtawesome, refreshed per theme via `refresh_icons(theme)`

### Parameters dock (`_qt/panels/parameters.py::ParametersPanel`)
- Sliders rebuilt on every surface switch from each `ParamSpec`; label, monospace current value,
  min/max markers, unit suffix, `description` tooltip
- Render fires on **`sliderReleased` only**, never `valueChanged` (**INT-2**) — a debounced callback
  can never shadow the release render
- `Reset all to defaults` — object name `resetDefaultsBtn`
- **Generic context-hint banner** — `set_context_hint(text)`. It is *not* CY3-specific: `app.py:575`
  supplies the Calabi–Yau "2-D shadows, Hanson-1994 tradition" note, `app.py:586` the Fano ρ=1 "real
  2-D slice of a 6-dimensional variety — novel renderings" note, and `""` hides it for K3/Enriques.
- **Grid mode toggle** — swaps the slider stack for `ParameterGridPanel`
  (`_qt/panels/parameter_grid_panel.py`): a `QGraphicsScene` with a `_DraggableDot` plus residual
  sliders. Its math lives in `_qt/parameter_grid_math.py`; drag-time helpers in `_qt/ui_helpers.py`.

### Appearance dock (`_qt/panels/appearance.py::AppearancePanel`)
- Surface colour swatch (`QColorDialog`); the swatch border is theme-aware (`_border_for_theme`)
- Opacity slider; style radios (solid / wireframe / surface-with-edges); lighting toggles; background

### Status bar (`app.py`)
- Default: surface label + vertex / face counts + current parameter values
- `ValueError` from a generator → displayed verbatim (hard error)
- `RuntimeWarning` → extracted and prefixed `⚠` (**AI-14**, soft signal)
- A `_render_busy_spinner` exists because `showMessage` is called on every render event

### Keyboard shortcuts (`app.py`) — four, not three
- `Ctrl+R` reset camera · `Ctrl+Shift+S` screenshot · `Ctrl+D` reset parameters ·
  `Ctrl+Shift+E` export mesh

## 5. Accessibility constraints (non-negotiable)

### Text contrast (AI-12)
Every text colour clears WCAG 2.1 AA in **both** themes — see the measured table in §2. Never
reintroduce `#888` (3.11:1) or any token below 4.5:1.

### Focus visibility (AI-12)
`outline: 2px solid {palette["FOCUS_RING"]}` on `QAbstractButton:focus`, `QComboBox:focus`,
`QSlider:focus`. Per-theme (`#3c82c4` light, `#5b9bd5` dark). Restore an equivalent on any custom widget.

### Slider-release feedback (INT-2)
Release-only render is intentional — a live render during drag would saturate the marching-cubes
pipeline. Propose `sliderReleased`, never `valueChanged`.

### Tooltip discipline
Dropdown items carry `Qt.ItemDataRole.ToolTipRole` from `varieties/tooltips.py`; sliders carry
`ParamSpec.description`. Don't add an affordance without a tooltip. Tooltip honesty (**AI-15**) is
load-bearing: the CY3 / Fano context hints exist so a 2-D slice is never implied to be the variety.

### Keyboard + screen-reader surface — **known debt**
Four shortcuts (§4). Tab order is Qt's default derivation. **`setAccessibleName` /
`setAccessibleDescription` are used exactly 0 times in the entire codebase** (verified). Screen-reader
labelling is real, unpaid a11y debt and belongs in Phase 4's mandatory `a11y-safety-debt` lane — it is
not a "polish" candidate.

## 6. Patterns already considered and rejected (DON'T re-propose)

| Pattern | Status |
|---|---|
| First-launch auto-render of a default surface | **Rejected** — "presumptuous in a research tool". Opens to the `— Select —` placeholder. Reconsiderable only for an explicit power-user mode. |
| Confirmation dialog on Reset to Defaults | **Rejected** — the action is non-destructive; the dialog interrupts flow. |
| `pytest-qt` UI end-to-end tests | **Rejected — AI-2.** macOS Qt+VTK GL context segfaults under offscreen. |
| Constructing `MainWindow()` under `QT_QPA_PLATFORM=offscreen` | **Rejected — AI-3.** Hard segfault in VTK GL context creation. |
| `clip_box(invert=...)` on PolyData | **Rejected — AI-4.** Invert semantics broken; commit `b68456f` worked around it with scalar clipping. |
| `auto_orient_normals=True` on Hanson cross-sections | **Rejected — AI-7.** Disconnected patches cannot be coherently oriented; commit `f58ee05`. |
| Short hex (`#888`) in colours flowing to PyVista | **Rejected — AI-13.** PyVista's parser rejects short hex. |
| `skimage.measure.marching_cubes` | **Removed.** The dependency is gone; implicit surfacing is `vtkFlyingEdges3D` (§1). |

### Shipped since this section was first written — do NOT list these as candidates

| Was | Now |
|---|---|
| "State persistence via `QSettings`" | **Shipped, partially.** Persisted keys: `LastSession/variety`, `LastSession/subtype`, the four `LastSession/print*` options, and `Window/geometry` + `Window/state` + `Window/schema_version` (`restoreGeometry` / `restoreState` on launch). **Still NOT persisted: slider values, and the active theme** — see §7. |
| "Dark-mode toggle" | **Shipped.** Dark is the launch default; `Theme` menu offers Dark / Light / Follow system. |
| "3D mesh export (STL / OBJ / PLY)" | **Shipped as STL.** `File → Export Mesh…` (`Ctrl+Shift+E`) and the View dock's `Export STL…` (print-ready, clip-aware). The `export/` package (`build_volumes.py`, `printable.py`) backs it, with a print-options dialog (`_qt/dialogs/print_options_dialog.py`). |
| "Variety-family colour theming" | **Shipped.** `VARIETY_DEFAULT_COLOR` — see the measured table in §2. |
| "Help menu / no menu bar at all" | **Partially shipped.** A menu bar exists (`&File`, `Theme`). A `Help` / `About` menu with citations does not — still a candidate (§7). |

## 7. What's UNDERDEVELOPED (candidate surface)

Verified open as of 2026-07-10. The discover scouts will likely converge on a subset — surface them
prominently if your scan finds confirming evidence.

**a11y-safety-debt lane (mandatory, ranked first — §9 / phase-prioritize):**
- **`setAccessibleName` on every interactive widget** — currently 0 occurrences codebase-wide.
- **Explicit tab-order derivation** — Qt's default ordering has never been audited against the
  dock layout.

**Foundations:**
- **Theme is not persisted** — `QSettings` stores the last variety, subtype, print options and the
  window geometry/state, but the active theme resets to `dark` on every launch. Cheap, and it
  removes a daily papercut for a light-theme user.
- **Slider values are not persisted** — the parameter state of the last session is lost.
- **Reduced-motion toggle** — a `QSettings`-backed switch. Note there is currently **no Qt animation
  anywhere in the codebase** (0 `QPropertyAnimation` / `QVariantAnimation` / `QTimeLine`), so this is
  a *precondition* for animated camera-preset interpolation, not a fix for existing motion.
- **Bounding-box / scene-aid colour tokens** — currently light-ish; harder to read against the dark
  viewport than ideal.

**Workflow:**
- **Parameter min/max field input** — sliders force discrete steps; typing an exact ψ = 1.0001 to
  probe the Dwork conifold is not possible today. A spin-box alternative per slider.
- **Empty-clip overlay annotation** — when the domain radius shrinks the surface to nothing, the
  status bar says so but the canvas is silent. A VTK text overlay would carry the message.
- **Status-bar warning-badge persistence** — a `⚠ N warnings` badge that survives the next render's
  `showMessage`. (Note the `_render_busy_spinner` already exists for the same underlying reason.)
- **Side-by-side surface comparison** — two viewports, one model each; K3 ↔ Kummer, or the Enriques
  figure family.
- **Animated parameter sweep** — scrub one parameter min → max over N seconds. The Hanson dwell time
  and the Dwork ψ sweep are the iconic demos. Gated on the reduced-motion toggle above.

**Polish / signature:**
- **Math-typography tooltip or overlay** — equations are plain-text unicode today; a rendered
  KaTeX/MathJax popover would lift fidelity substantially.
- **`QToolTip` font override** — the existing tooltips use unicode subscripts (`n₁`, `n₂`) and Greek
  (φ, ψ, λ); some platforms render these poorly without an explicit font CSS override.
- **Help / About dialog with mathematical citations** — the tooltips carry the citations; there is no
  central reference card.
- **First-launch hint** — the empty viewport + `— Select —` placeholder does not reveal the
  cascading-dropdown UX. An *honest* empty-state affordance only; a splash is BAN-10/13 (§9).
- **Per-variety palette presets in Appearance** — saved "K3-default" / "Hanson-iconic" combos.
- **HiDPI polish** — `app.py` sets `AA_ShareOpenGLContexts` but nothing else; the README's
  `QT_AUTO_SCREEN_SCALE_FACTOR=1` workaround is still a manual step.

## 8. How to anchor a proposal to this file

Every candidate in the synthesis catalog must cite ONE of:

- **A specific source `file:line`** that is the closest existing implementation. The real paths are
  `app.py`, `_qt/styles.py`, `_qt/panels/{view,parameters,appearance,parameter_grid_panel}.py`,
  `_qt/icons.py`, `_qt/parameter_grid_math.py`, `_qt/dialogs/print_options_dialog.py`,
  `varieties/{registry,tooltips,k3,enriques,calabi_yau,fano,_kernels,_marching}.py`,
  `render/worker.py`, `cross_section/clip.py`, `export/`.
- **A named token from `_qt/styles.py`** to be applied or extended — a `PALETTE_LIGHT` /
  `PALETTE_DARK` key, `VARIETY_DEFAULT_COLOR`, or a `*_STYLE` constant.
- **An app invariant** (`AI-1` … `AI-15`, `.claude/references/app-invariants.md`) the proposal honours.
- **A pattern in §7** (the underdeveloped list) — and say which lane it belongs to.
- **An interaction primitive** from `interaction-vocabulary.md` (cite `[INT-N]`; the vocabulary runs
  `INT-1` … `INT-98`).
- **A BAN token or the §10 rubric** from the synced canon
  `.claude/references/frontend-design-language.md`, plus the §9 house thesis below.

If none of those apply, the proposal is probably not Algebraic-Variety-Viewer-shaped — push back at
synthesis.

---

## §9 — House thesis

> **Ground-truthed 2026-07-10.** §1–§8 were re-verified against the tree after the
> `restructure-feature-subpackages-2026q2-r2` move, the dark-theme launch default, the Fano 3-fold
> family, the parameter-grid panel, and the `QThreadPool`/`QRunnable` render worker. §9 below is the
> load-bearing house-thesis contract per `frontend-design-language.md` §9.

**This section fills in `frontend-design-language.md` §9 for this repo.**  The canon is product-neutral and written in web mechanics; this overlay is the one place the Algebraic Variety Viewer's thesis, anti-references, and surface map live — translated to PySide6/Qt (tokens → `_qt/styles.py` `PALETTE_LIGHT`/`PALETTE_DARK` + `.qss`; motion → `QPropertyAnimation` + `[INT-N]` — note **no Qt animation exists in the codebase today**, so a reduced-motion toggle (QSettings, not a media query) is a *precondition* for adding any; perf → startup-render + camera frame time; a11y → focus/tab order + `.qss` WCAG-AA contrast).  The `frontend-uplift-art-direction-scout` MUST read this before proposing a thesis or directions.

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
