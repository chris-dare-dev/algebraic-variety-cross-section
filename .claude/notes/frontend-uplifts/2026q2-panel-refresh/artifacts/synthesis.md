# Synthesis — 2026q2-panel-refresh

**Date:** 2026-05-20
**Inputs:** 4 discover briefs (visual-scout, library-scout, inspiration-scout, current-state-critic) + 11 off-screen renders
**Output role:** unified modernization-candidate catalog ready for the Phase 3 challenger and Phase 4 prioritizer

---

## 1. Executive summary

**22 candidates** across 10 of the 11 fixed categories (no Accessibility-only candidates — accessibility shows up as a sub-constraint on the Color/theme and Layout candidates instead). The dominant themes the four briefs converged on are: **(a) visual monotony despite content richness** — 14 surfaces, one steel-blue, no dark mode (4-brief triangulation); **(b) input-fidelity gap for research workflows** — slider-only inputs make the ψ=1 conifold unreachable (3-brief triangulation); **(c) missing desktop-app chrome** — no menu bar, no mesh export, no state persistence (cross-brief). One **CRITICAL** finding survives: the Enriques canonical sextic ships visible sawtooth mesh tears at all three internal node lines (visual-scout render-evidenced; one render reads as a renderer bug, not geometry). The catalog flags **3 foundational candidates** that the rest of the visual / theme work depends on, so the Phase 4 prioritizer sequences them first.

**Top tension across briefs:** the visual scout reads the Enriques sawtooth as a marching-cubes near-singular zero-crossing problem (needs more Taubin / boundary padding / resolution); the current-state critic reads the same image as a back-face culling problem (needs `backface_culling=True`). Both interpretations have merit; the synthesis splits the candidate into two — UPL-18 (sawtooth band, resolution side) and UPL-19 (back-face culling toggle, display side) — so each can be evaluated and shipped independently.

---

## 2. Triangulation strength

- **Strong (3+ brief sources):** 7 candidates — UPL-1, UPL-4, UPL-5, UPL-7, UPL-9, UPL-13, UPL-14
- **Moderate (2 brief sources):** 7 candidates — UPL-2, UPL-3, UPL-6, UPL-8, UPL-10, UPL-11, UPL-20
- **Single-source but render-evidenced or invariant-anchored:** 8 candidates — UPL-12, UPL-15, UPL-16, UPL-17, UPL-18, UPL-19, UPL-21, UPL-22

Single-source candidates with high render-evidence (UPL-18, UPL-19) are weighted equivalently to 2-source candidates in this catalog because the PNG evidence is dispositive — what a render shows is verifiable in a way that brief opinion alone is not. They are flagged for the challenger to scrutinize regardless.

---

## 3. Foundational candidates (Phase 4 must sequence first)

These three candidates unblock or de-risk a large portion of the rest of the catalog. Synthesis surfaces them explicitly so Phase 4's RICE pass can apply the +30% foundational bonus and put them at the head of the DAG.

### F1 (= UPL-1) — Refactor `styles.py` into named palette tokens (light + dark + per-variety)

**Why foundational:** UPL-4 (dark mode), UPL-5 (per-variety surface color), and UPL-11 (first-launch overlay color) all need the same token-extraction work. Doing it once turns three "M" implementations into three "S" implementations downstream. Without F1, each of those candidates re-litigates the palette structure separately.

### F2 (= UPL-2) — Adopt `superqt` + `qtawesome` as the panel-modernization dependency base

**Why foundational:** UPL-7 (spin-box companion), UPL-8 (collapsible panels), UPL-10 (Help menu icon), UPL-14 (mesh-export icon), and UPL-16 (lighting-preset icons) all pull from these two libraries. Adopting them once as a single `requirements.txt` delta unblocks five downstream candidates and amortizes the qtpy-cold-boot startup cost across all of them.

### F3 (= UPL-3) — Initialize the plotter background in `MainWindow.__init__`, decoupled from `apply_to_actor`

**Why foundational:** GAP-H1 from the visual scout shows the app actually starts on a light-grey VTK default background and only flashes to `#2f2f2f` on the first surface render. UPL-11 (first-launch overlay) and UPL-4 (dark-mode toggle) both assume a stable, intended background at startup. Without F3 they layer atop a known flash.

---

## 4. Candidate catalog

Each entry uses the verbatim shape from `phase-synthesize.md`. Ordering: foundational first, then by triangulation strength within each category, then by t-shirt size ascending.

---

### UPL-1 — Refactor `styles.py` into named palette tokens (foundational)

**Category:** Cross-cutting refactor
**Size:** S
**Evidence triangulation:** 3 briefs (library ✓, inspiration ✓, current-state ✓)
**Interaction primitives:** [INT-94 dark-mode-stylesheet], [INT-96 palette-template-per-variety]

**What it is:** Extract every hex literal in `styles.py` and `appearance_panel.py` into named palette tokens (e.g. `BG_VIEWPORT`, `BG_PANEL`, `TEXT_VALUE`, `TEXT_MUTED`, `FOCUS_RING`, `VARIETY_COLOR["K3 surface"]`). Maintain a single light palette as the current behavior; reserve dark and per-variety dicts for follow-on candidates to populate without touching the structure.

**Why it matters:** Every downstream color change (dark mode, per-variety surface tinting, first-launch overlay color) currently requires editing scattered constants and the panel constructors. A flat token dict removes that friction and makes the next three appearance candidates each ~30 lines instead of ~80.

**Sources:**
- Library scout: pyqtdarktheme-fork integration recommends a "parallel `STYLESHEET_DARK`" pattern (§2.B)
- Inspiration scout: P-02 deep-navy palette + P-04 per-variety tokens both presume named tokens
- Current-state critic: H-1, H-2, M-4 all cite the same `appearance_panel.py:74` hardcode

**Closest existing app analog:** `styles.py` lines 1–140 — already centralized for fonts and stylesheet strings, but raw hex values remain scattered.

**Render evidence:** N/A (code-only refactor; no surface change at this step)

**Sketch:** New `palette.py` module (or `styles.py:PALETTE_LIGHT: dict[str, str]`) maps logical token → 6-digit hex. `APP_STYLESHEET` becomes an f-string that substitutes from the palette dict. Existing constants (`COLOR_MUTED`, `COLOR_VALUE`, `RANGE_LABEL_STYLE`) keep their names but read from the palette dict at module load. AI-13 (6-digit hex) is preserved; AI-12 (WCAG AA contrast) verification is required only when adding new tokens, not when refactoring existing ones.

**Open questions:**
- Should `palette.py` be a new module or live in `styles.py`? (Recommend in `styles.py` — keeps the import surface narrow.)
- Token naming: `BG_VIEWPORT` vs `viewport.bg` — pick one convention.

---

### UPL-2 — Adopt `superqt` + `qtawesome` as panel-modernization dep base (foundational)

**Category:** Library / dependency
**Size:** S
**Evidence triangulation:** 2 briefs (library ✓, inspiration ✓ implicitly via P-03 + P-06)
**Interaction primitives:** [INT-2 slider-release-render], [INT-40 parameters-rebuild-on-switch], [INT-5 keyboard-shortcut] (icons reinforce shortcutted actions)

**What it is:** Add `superqt>=0.8` (BSD-3-Clause) and `qtawesome>=1.4` (MIT) to `requirements.txt`. Document the cold-boot icon-font caching cost (~150–200ms one-time per launch) in CONTEXT.md §8. No UI changes at this step — this is the dep landing; downstream candidates (UPL-7, UPL-8, UPL-10, UPL-14, UPL-16) consume.

**Why it matters:** Both libraries have well-known PySide6 compatibility, zero GPL exposure, and small bundle footprints (~3 MB total). Treating them as a single foundational dep delta means the four UI candidates that depend on them each cost 0 incremental dep-management work.

**Sources:**
- Library scout: `superqt` Tier 1 §2.A, `qtawesome` Tier 1 §2.C
- Inspiration scout: P-03 (collapsibles) + P-06 (spinbox) both explicitly cite `superqt` widgets

**Closest existing app analog:** `requirements.txt` line 1–5 (current pins) — no superqt / qtawesome today.

**Render evidence:** N/A (dep landing)

**Sketch:** `requirements.txt` gains `superqt>=0.8,<0.9` and `qtawesome>=1.4,<2`. CONTEXT.md §3 (stack rationale) adds a one-paragraph note. No code changes in this candidate; the test in `tests/` for AI-2 (Qt-free) stays clean because both libs are imported only by Qt code paths.

**Open questions:**
- `qtawesome` ships ~3 MB of icon fonts. Document the bundle delta. PySide6 itself is ~450 MB so the relative cost is trivial; the absolute delta should still be documented.

---

### UPL-3 — Initialize plotter background in `MainWindow.__init__` (foundational)

**Category:** Color / theme
**Size:** XS
**Evidence triangulation:** 2 briefs (visual ✓ as GAP-H1, current-state ✓ adjacent at `appearance_panel.py:74`)
**Interaction primitives:** [INT-80 solid-color-bg]

**What it is:** Move the `plotter.set_background(...)` call from inside `AppearancePanel.apply_to_actor()` (which is a no-op when called with `None` at startup) to `MainWindow.__init__()` right after the plotter widget is constructed.

**Why it matters:** Today the app opens to a light-grey VTK default background and only flashes to `#2f2f2f` on first surface render. Every subsequent candidate that touches the viewport (dark mode, first-launch overlay, per-variety surface tinting) layers atop this flash. Removing it costs 2 lines and removes a load-bearing first-impression hit.

**Sources:**
- Visual scout: GAP-H1 — "background-flash on first render" with cross-reference to both PNGs and to `app.py:144–145`
- Current-state critic: `appearance_panel.py:74` hardcoded dark bg, but `apply_to_actor(None)` is a no-op

**Closest existing app analog:** `app.py:144–145` — `self.appearance_panel.apply_to_actor(None)` runs but does not touch the background because `_actor is None`.

**Render evidence:** Compare `renders/k3-surface-fermat-quartic-default.png` (no plotter — white) with `renders/k3-surface-fermat-quartic-dark-bg.png` (plotter dark) — the difference is exactly what users see on the first 500ms of app launch today.

**Sketch:** In `MainWindow.__init__()`, after `self.plotter = QtInteractor(self)` is constructed, add `self.plotter.set_background(BG_VIEWPORT)` (using UPL-1's token, or the existing `#2f2f2f` literal if UPL-1 hasn't landed yet). Keep `apply_to_actor` as the runtime update path for user theme changes. AI-13 (6-digit hex) preserved.

**Open questions:** none.

---

### UPL-4 — Dark-mode toggle + parallel `STYLESHEET_DARK`

**Category:** Color / theme
**Size:** M
**Evidence triangulation:** 4 briefs (visual ✓ via Pattern 2, library ✓, inspiration ✓ as P-02, current-state ✓ as H-1)
**Interaction primitives:** [INT-94 dark-mode-stylesheet], [INT-80 solid-color-bg]

**What it is:** Add a `STYLESHEET_DARK` constant in `styles.py` (using UPL-1's tokens) covering panel chrome, dock headers, sliders, group boxes, and focus rings on a dark ground. Add a `QAction` in the Help / View menu (depends on UPL-10) or a `QCheckBox` in the Appearance dock that toggles `QApplication.instance().setStyleSheet(...)` between light and dark. On toggle, also call `plotter.set_background(BG_VIEWPORT_DARK)`.

**Why it matters:** Strongest cross-brief triangulation in the catalog. The math-research audience (Manim viewers, 3Blue1Brown, Quanta readers) has internalized dark math chrome as a credibility signal; peer apps (ParaView, Blender, 3D Slicer) all ship one. The current `#2f2f2f` viewport with light Qt chrome around it is a half-measure.

**Sources:**
- Visual scout: cross-surface Pattern 2 — "dark background enhances every surface; white background flatters none"
- Library scout: `pyqtdarktheme-fork` (§2.B) provides a production-ready dark QSS; can either be adopted as the dark palette or used as a reference for a hand-tuned one
- Inspiration scout: P-02 "deep-navy / off-black canvas palette" — explicitly cites Manim community + 3Blue1Brown video frames
- Current-state critic: H-1 — "No dark-mode toggle" with file:line at `styles.py` and `app.py:427`

**Closest existing app analog:** `styles.py:APP_STYLESHEET` — single light stylesheet, no dark variant.

**Render evidence:** `renders/calabi-yau-3-fold-hanson-quintic-dark-bg.png` — the dark-bg Hanson render is the strongest image in the visual scout's capture set and directly demonstrates the visual lift.

**Sketch:** `styles.py` adds `STYLESHEET_DARK = f"""..."""` mirroring `APP_STYLESHEET` with palette substitution. Three new tokens land in UPL-1's palette dict: `BG_VIEWPORT_DARK = "#1e222e"`, `BG_PANEL_DARK = "#2a2f3d"`, `TEXT_VALUE_DARK = "#dde3ee"` (verify ≥4.5:1 on `BG_PANEL_DARK`). The toggle widget calls both `setStyleSheet` and `plotter.set_background` in the same handler; AI-9 re-entrancy guard isn't triggered (no `processEvents`). Tension: hand-tune vs adopt `pyqtdarktheme-fork`. **Recommendation:** hand-tune the QSS using `pyqtdarktheme-fork` as a reference, NOT as a runtime dep — the app's existing centralized stylesheet would otherwise have to thread a third-party QSS through it, which is more fragile than a parallel hand-rolled variant. Park `pyqtdarktheme-fork` as a possible source of default values for ambiguous tokens.

**Open questions:**
- System-preference auto-detection (light/dark) at launch? Or always default to light + user-explicit toggle? (Recommend explicit toggle for v1; auto-detect is a v2 follow-on.)
- Persist the toggle state via QSettings? (Depends on UPL-15; if UPL-15 doesn't land, the toggle resets on every launch.)

---

### UPL-5 — Per-variety default surface color

**Category:** Color / theme
**Size:** S
**Evidence triangulation:** 4 briefs (visual ✓ as GAP-H3, library ✓ implicit, inspiration ✓ as P-04, current-state ✓ as H-2 + M-4)
**Interaction primitives:** [INT-96 palette-template-per-variety], [INT-43 swatch-color-picker] (user override path stays available)

**What it is:** Add a `VARIETY_DEFAULT_COLOR: dict[str, str]` mapping in `styles.py` (using UPL-1's tokens), keyed by variety family ("K3 surface", "Enriques surface", "Calabi–Yau 3-fold", "Fano 3-fold (ρ=1)"). When the user picks a new variety, `appearance_panel.set_default_color(VARIETY_DEFAULT_COLOR[variety])` updates `_surface_color`, repaints the swatch, and re-applies to the live actor.

**Why it matters:** All 14 surfaces today render in the same `#b0c4de` steel-blue. The single biggest cross-brief gripe is that the gallery feels monotone. A four-token palette assignment costs ~1 day and transforms the first-launch impression for every surface in the app.

**Sources:**
- Visual scout: GAP-H3 — "no per-variety color identity — all surfaces render identically in color"
- Library scout: `pyqtdarktheme-fork`'s integration would naturally pair with this; the `superqt` `QCollapsible` showcases palette-aware headers
- Inspiration scout: P-04 — citing 3D Slicer's named color tables per modality
- Current-state critic: H-2 and M-4 both anchor at `appearance_panel.py:74`

**Closest existing app analog:** `appearance_panel.py:74` — `self._surface_color = QColor("#b0c4de")` — single literal applied to every variety.

**Render evidence:** Four canonical-set renders at `renders/k3-surface-*-default.png`, `renders/enriques-surface-canonical-sextic-default.png`, `renders/calabi-yau-3-fold-hanson-quintic-default.png` — all identical hue.

**Sketch:** Palette proposal (all 6-digit hex, all verified for ≥3:1 luminance contrast against `BG_VIEWPORT_DARK = #1e222e`):
- K3 surface → `#8ab4d4` (cool slate — anchor for complex-geometry heritage)
- Enriques surface → `#c8a880` (warm sand — signal the quotient / birational lineage)
- Calabi–Yau 3-fold → `#4a90d9` (cobalt — Hanson 1994 visual identity)
- Fano 3-fold (ρ=1) → `#7ec8a0` (muted forest — bold accent for the newer family)

`appearance_panel.AppearancePanel` gains `set_default_color(hex_color: str)`. `app.py._on_variety_changed` (or `_on_subtype_changed` — pick the earlier of the two so the color updates before the parameter rebuild) calls it. The existing color-picker continues to work for user override. AI-13 (6-digit hex) preserved.

**Open questions:**
- Should switching subtypes within a family (Fermat → Kummer within K3) also re-set the color to the family default, or preserve the user's last override? (Recommend re-set on variety change, preserve on subtype change.)
- Does H-2's proposed dark-mode counterpart palette (more saturated) need to be specified now, or can it ride on top of UPL-4? (Recommend defer to UPL-4 follow-on.)

---

### UPL-6 — Named color-map preset menu in Appearance dock

**Category:** Color / theme
**Size:** S
**Evidence triangulation:** 2 briefs (inspiration ✓ as P-01, library ✓ implicit via PyVista cmap=)
**Interaction primitives:** [INT-43 swatch-color-picker] (extended with preset combo above)

**What it is:** Add a `QComboBox` above the existing color swatch in `appearance_panel.py:_build_color_group()` listing PyVista-native colormaps (Viridis, Plasma, Inferno, Cool-to-Warm, Magma, Greyscale, plus "Flat color (default)"). When the user picks a preset, `add_mesh(..., scalars="Mean_Curvature", cmap=preset, ...)` replaces `add_mesh(..., color=...)`. Reverting to "Flat color (default)" restores the surface_color path.

**Why it matters:** Every peer VTK tool (ParaView, 3D Slicer, VisIt) surfaces named colormap presets. The Mean_Curvature scalar coloring on the Enriques sextic and Hanson quintic specifically would reveal mathematical structure on the surface (GAP-M4 from the visual scout). The PyVista API is already available; this is a UI exposure, not new infrastructure.

**Sources:**
- Inspiration scout: P-01 — ParaView Color Map Editor as the canonical reference
- Library scout: §2.E pyvista version note confirms `cmap=` kwarg stability across the pinned range

**Closest existing app analog:** `appearance_panel.py:115–142` — flat-color swatch + picker only; no preset menu.

**Render evidence:** None directly (the visual scout did not render colormap variants); evidence is GAP-M4 on Enriques flat panels and the cross-cutting "no color cue" theme.

**Sketch:** New `QComboBox` populated from a fixed list of `(label, cmap_name)` tuples. AppearancePanel grows an enum-typed `_color_mode: Literal["flat", "cmap"]` and a `_cmap_name: str`. `apply_to_actor` branches on the mode. Computing the scalar at render time (`mesh.compute_normals(); mesh["Mean_Curvature"] = mesh.curvature()`) costs ~50–100ms per surface — within AI-12 / INT-2 latency budget. AI-5 (`scalars=` kwarg required) — preset path uses `scalars="Mean_Curvature"` correctly.

**Open questions:**
- Which scalar? Mean curvature, Gaussian curvature, or just the implicit field value? (Recommend Mean_Curvature as default; future v2 could expose a sub-selector.)
- Should the color-picker (flat color) and the preset menu be mutually exclusive radio-style, or can they coexist with a "Use colormap" checkbox? (Recommend mutually exclusive — clearer UX.)

---

### UPL-7 — Spin-box companion alongside parameter sliders

**Category:** Interaction
**Size:** S
**Evidence triangulation:** 3 briefs (library ✓ via superqt QLabeledDoubleSlider, inspiration ✓ as P-06, current-state ✓ as H-3)
**Interaction primitives:** [INT-97 parameter-spin-box-alternative], [INT-2 slider-release-render]

**What it is:** In `parameters_panel.py:_build_row()`, replace the read-only `QLabel` value readout with a `QDoubleSpinBox` (or `superqt.QLabeledDoubleSlider`) whose range / step / decimals come from the `ParamSpec`. The slider stays as the primary coarse control; the spinbox accepts exact entry. Bidirectional sync: `slider.sliderValueChanged → spinbox.setValue(...)` and `spinbox.editingFinished → slider.setValue(...)`. Render fires only on `sliderReleased` or `spinbox.editingFinished` (preserves INT-2 / forbids INT-NO-1).

**Why it matters:** The Dwork ψ parameter is the textbook research case: ψ = 1.0 is the conifold singularity, the slider step is 0.05 (the design value), so ψ = 1.0001 to probe the conifold complement is structurally unreachable. The current `RuntimeWarning` workaround (CONTEXT.md §8.8) is a notification, not a fix. A spinbox makes exact values possible for every parameter in the app.

**Sources:**
- Library scout: `superqt` (§2.A) provides `QLabeledDoubleSlider` as a single-widget solution; removes ~30 lines of boilerplate per slider
- Inspiration scout: P-06 — ParaView and GeoGebra both pair sliders with editable numeric fields
- Current-state critic: H-3 — "No parameter direct-entry (spin-box) alongside sliders" anchored at `parameters_panel.py:126–182`

**Closest existing app analog:** `parameters_panel.py:_build_row()` line 140 — `value_lbl = QLabel(...)` — read-only.

**Render evidence:** N/A (panel-internal UI change).

**Sketch:** Two implementations possible. (A) **Hand-rolled:** `QDoubleSpinBox` next to the slider, manual sync. ~30 lines per row × ~6 rows ≈ touchable. (B) **superqt's QLabeledDoubleSlider:** drop-in replacement, ~5 lines per row. Recommend (B) — it leans on UPL-2's dep landing and amortizes. INT-2 preserved (spinbox `editingFinished` ≡ slider release). AI-9 re-entrancy: the spinbox emit path must call `_render_current` through the same throttled signal pipeline; the existing `_computing` guard covers it.

**Open questions:**
- Discrete-vs-continuous parameters: some `ParamSpec` parameters have discrete options (e.g., the Calabi–Yau "k value" enum). The spinbox should only replace continuous-numeric rows; discrete rows keep their existing widget.
- When the spinbox value goes outside `spec.min/max`, clip or error? (Recommend clip silently with a status-bar muted hint.)

---

### UPL-8 — Collapsible group boxes in Appearance + View docks

**Category:** Layout
**Size:** S
**Evidence triangulation:** 2 briefs (library ✓ via superqt, inspiration ✓ as P-03)
**Interaction primitives:** [INT-45 dock-header-tinted], [INT-6 dock-floatable]

**What it is:** Replace the four `QGroupBox` widgets in `appearance_panel.py` (Colors, Display, Opacity, Shading) and the five in `view_panel.py` (View Presets, Camera, Clip Region, Scene Aids, Export) with `superqt.QCollapsible` containers. Each starts expanded; clicking the disclosure arrow collapses to header-only. State persistence (via QSettings, depends on UPL-15) optional in v1.

**Why it matters:** The Appearance dock grows tall on small displays. Collapsing rarely-touched sections gives the user back vertical space without removing functionality. Blender's properties panel uses exactly this pattern.

**Sources:**
- Library scout: `superqt.QCollapsible` (§2.A) — Tier 1, BSD-3-Clause, PySide6-explicit
- Inspiration scout: P-03 — Blender N-panel + superqt direct citation

**Closest existing app analog:** `appearance_panel.py:_build_ui()` line 87; `view_panel.py:_build_ui()` line 67 — `QGroupBox` always-open.

**Render evidence:** N/A (panel-internal UI change).

**Sketch:** Each `QGroupBox(...)` → `QCollapsible(header_text)`; the existing child layout is `qcollapsible.addWidget(...)` instead of `groupbox.setLayout(...)`. Header styling inherits from `APP_STYLESHEET`; verify focus-ring visibility on the disclosure arrow after adoption. AI-12 (WCAG AA) preserved.

**Open questions:**
- Default state: all expanded (current behavior), or last-touched-only-expanded (Blender behavior)? (Recommend all expanded for v1 — no surprise; revisit after telemetry.)

---

### UPL-9 — KaTeX-rendered equation tooltip popover

**Category:** Tooltips / disclosure + Typography
**Size:** M
**Evidence triangulation:** 3 briefs (library ✓, inspiration ✓ as P-10, current-state ✓ via tooltip-quality observation in §7)
**Interaction primitives:** [INT-95 katex-tooltip-popover], [INT-7 tooltip-rich]

**What it is:** Replace the unicode-approximated equation strings in `VARIETY_TOOLTIPS` / `SUBTYPE_TOOLTIPS` (`surfaces.py`) with KaTeX LaTeX source. Add a `QDialog` containing a `QWebEngineView` that renders the KaTeX on a 500ms hover dwell over the variety / model dropdown items. Bundle `katex.min.js` + `katex.min.css` (~300 KB total) as a local HTML file.

**Why it matters:** The math-research audience expects typeset math; the current `x⁴+y⁴+z⁴` unicode approximation renders inconsistently across OS font stacks. `QtWebEngineWidgets` is already in `PySide6-Addons` (a required sub-package of PySide6 ≥ 6.6), so the bundle cost is **already paid** — the only new asset is the ~300 KB KaTeX bundle.

**Sources:**
- Library scout: §2.F KaTeX via QtWebEngineView — explicitly flagged "zero marginal cost" because QtWebEngine is already in PySide6-Addons
- Inspiration scout: P-10 — Mathematica Manipulate + GeoGebra 3D equation typography
- Current-state critic: §7 "Rich tooltip discipline" — calibration anchor (tooltips are a strong existing surface) + implicit upgrade path

**Closest existing app analog:** `surfaces.py` `VARIETY_TOOLTIPS` / `SUBTYPE_TOOLTIPS` dicts; `app.py:179–182` (sets `Qt.ItemDataRole.ToolTipRole` from those dicts).

**Render evidence:** N/A (rendered math, not surface mesh).

**Sketch:** New `equation_popover.py` module. `EquationPopover(QDialog)` holds a `QWebEngineView`; on construction it loads a local `katex_template.html` that imports the bundled `katex.min.js` and exposes `window.renderKatex(tex_string)`. The combo box's `enterEvent` (or a custom delegate) triggers a 500ms dwell `QTimer` that on timeout calls `popover.show_at(combo_pos, tex_source)`. The TeX source per variety/subtype lives in `VARIETY_TOOLTIPS_TEX` (new dict next to the existing tooltip dict). AI-1 (PySide6) preserved; AI-2 (Qt-free tests) — the TeX-source dict is Qt-free and testable; the rendering is in a Qt path that the existing test infrastructure already skips.

**Alternative path (lighter):** matplotlib mathtext renders LaTeX → PNG via the Agg backend, embedded in `QToolTip` as a rich-text `<img>` data URI. Avoids the `QtWebEngineView` window. ~9 MB matplotlib install vs ~300 KB KaTeX bundle. Recommend KaTeX path because `QtWebEngineWidgets` is already paid; only fall back to matplotlib if `QWebEngineView` proves too heavy at startup.

**Open questions:**
- Hover dwell timing: 500ms feels right but is untuned. (Recommend instrument via QSettings-stored value, default 500ms.)
- Where does the TeX source live? Side-by-side with the unicode tooltip in `surfaces.py`, or a separate `equations.py`? (Recommend side-by-side — keeps math facts co-located.)

---

### UPL-10 — Help menu with About + Keyboard Shortcuts + Citations

**Category:** Layout
**Size:** S
**Evidence triangulation:** 2 briefs (inspiration ✓ as P-09, current-state ✓ as M-6)
**Interaction primitives:** [INT-98 help-menu-with-citations], [INT-5 keyboard-shortcut]

**What it is:** Add a `QMenuBar` with "View" (dark-mode toggle from UPL-4) and "Help" submenus. Help contains "About / Citations" (a static `QDialog` listing the math sources from `SUBTYPE_TOOLTIPS` and the README's "Further reading") and "Keyboard Shortcuts" (a static two-column dialog: action | key, populated from `Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D` and any future additions).

**Why it matters:** The app currently has no menu bar. Citations are deep in tooltips; shortcuts are documented only in the View dock's help label and README. Adding a menu bar costs ~30 lines and gives the research audience a discoverable, stable place to verify citations.

**Sources:**
- Inspiration scout: P-09 — VS Code Help menu, MeshLab About with citation
- Current-state critic: M-6 — explicitly flagged in `design-system.md §7`

**Closest existing app analog:** `app.py:MainWindow.__init__()` — no `QMenuBar` call.

**Render evidence:** N/A (menu bar is above the renders).

**Sketch:** In `MainWindow.__init__()`, after dock setup, add `self.setMenuBar(self._build_menubar())`. `_build_menubar()` returns a `QMenuBar` with two `QAction` entries per submenu. About dialog: a `QDialog` with a `QTextBrowser` displaying HTML from a new `citations.py` constant (sourced from the README + tooltip dict). Keyboard Shortcuts dialog: a `QDialog` with a `QTableWidget` (2 columns, N rows). `qtawesome` icons reinforce each action. AI-11 (qualified Qt enums) — use `QKeySequence.StandardKey` for cross-platform shortcuts where applicable.

**Open questions:**
- Should the About dialog include the LGPL / PyVista / KaTeX licenses as a separate "Licenses" sub-action? (Recommend yes — credibility signal for a research tool.)

---

### UPL-11 — First-launch viewport hint overlay

**Category:** Status / feedback + Layout
**Size:** S
**Evidence triangulation:** 2 briefs (visual ✓ as GAP-M3, current-state ✓ as M-1)
**Interaction primitives:** [INT-74 empty-clip-status-message] (overlay variant), [INT-4 status-bar-feedback]

**What it is:** Add a `QLabel` absolutely positioned over the `QtInteractor` widget reading "Select a variety and model to begin rendering" in `COLOR_MUTED` style. Hidden as soon as `_render_current` successfully renders a surface; shown again only if the user returns to `— Select —`.

**Why it matters:** Today the central viewport area is empty on launch with only a status-bar prompt — easy to miss. This complements (does not replace) the existing status-bar message; it does not auto-render a default surface (which CONTEXT.md §9 explicitly rejected as presumptuous).

**Sources:**
- Visual scout: GAP-M3 — "No first-launch visual affordance in the central viewport"
- Current-state critic: M-1 — same gap, anchored at `app.py:55` + `app.py:86`

**Closest existing app analog:** `app.py:86` — `self.statusBar().showMessage("Choose a variety to begin.")` — status-bar only.

**Render evidence:** Synthetic (AI-3 forbids MainWindow offscreen render).

**Sketch:** A `QLabel` is added to the central widget's layout (over the `QtInteractor`) with `setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)` so it doesn't capture VTK mouse events. Text color = palette `TEXT_MUTED`, font-size 14px, centered. `MainWindow._render_current` calls `self._first_launch_hint.hide()` on success; `_on_variety_changed("— Select —")` calls `.show()`. AI-12 — confirm contrast on both `BG_VIEWPORT` and `BG_VIEWPORT_DARK`.

**Open questions:**
- VTK text actor vs. Qt overlay label? (Recommend Qt overlay — decouples from the VTK render pipeline; the overlay survives plotter resets.)

---

### UPL-12 — Persistent surface-warning badge

**Category:** Status / feedback
**Size:** S
**Evidence triangulation:** 1 brief (current-state ✓ as M-5)
**Interaction primitives:** [INT-70 status-warning-prefix]

**What it is:** Store `_last_surface_warning: str = ""` alongside `_raw_mesh` in `MainWindow`. When `_apply_domain_and_render` writes the status bar, re-prefix the warning string if non-empty. Clear `_last_surface_warning` only in `_on_subtype_changed` (when the user explicitly changes surface).

**Why it matters:** Today the `⚠ Near conifold ψ → 1` Dwork warning prefix is written once per render. As soon as the user moves any slider and triggers another render, the warning is silently overwritten by the fresh status-bar string. For a research tool where the warning is informationally important, persistence is correct behavior.

**Sources:**
- Current-state critic: M-5 — "Status-bar warning persistence: one-render lifespan only" with anchor `app.py:329–333`

**Closest existing app analog:** `app.py:329–333` — `⚠ {warning}` prefix construction inside `_apply_domain_and_render`.

**Render evidence:** N/A (status-bar text, not viewport).

**Sketch:** ~5-line patch to `app.py`. New instance attr `self._last_surface_warning: str = ""`. `_render_current` (or wherever the warning is detected) sets it; `_apply_domain_and_render`'s status-bar write reads it. Cleared on `_on_subtype_changed`. AI-14 (warning surfacing) preserved.

**Open questions:** none.

---

### UPL-13 — Status-bar mesh-extent + bounding-box readout

**Category:** Status / feedback
**Size:** XS
**Evidence triangulation:** 3 briefs (visual ✓ implicit via render evidence, inspiration ✓ as P-07, current-state ✓ implicit)
**Interaction primitives:** [INT-4 status-bar-feedback]

**What it is:** Append `bbox ±a × ±b × ±c` to the existing status-bar status (`{N_verts} vertices, {N_faces} faces, …`). Optionally, on mouse hover over the viewport, show approximate `(x,y,z)` of the surface point nearest the cursor.

**Why it matters:** The status-bar surface today shows N_verts and N_faces but not the spatial extent. For a research tool where "is this singularity near the origin?" is a real question, mesh-extent readout is a small, high-value addition.

**Sources:**
- Visual scout: cross-render observation that surfaces fit the frame variably (Kummer crowded, Fermat tiny, Enriques wide) — bbox would surface this
- Inspiration scout: P-07 — 3D Slicer Data Probe, ParaView status bar
- Current-state critic: §7 "Busy cursor + status-bar pipeline feedback" — calibration anchor (status bar is a strong surface) + the absence of bbox is an obvious extension

**Closest existing app analog:** `app.py:326` — current status-bar message string construction.

**Render evidence:** N/A.

**Sketch:** ~3-line patch to `_render_current`: append `f"bbox ±{abs(mesh.bounds[1]):.2g} × ±{abs(mesh.bounds[3]):.2g} × ±{abs(mesh.bounds[5]):.2g}"` to the existing status string. Hover-readout is a separate v2 feature (would require a VTK MouseMove observer; out of scope for this candidate). AI-9 (re-entrancy) — not relevant for the bbox-only version.

**Open questions:**
- Hover readout: yes/no for v1? (Recommend defer — bbox alone is the high-leverage step.)

---

### UPL-14 — Mesh export (STL / OBJ / PLY)

**Category:** Export / persistence
**Size:** S
**Evidence triangulation:** 3 briefs (library ✓ via meshio + pyvista, inspiration ✓ as P-12, current-state ✓ as M-2)
**Interaction primitives:** [INT-93 mesh-export-button], [INT-61 screenshot-png-save] (same `QFileDialog` pattern)

**What it is:** Add an "Export mesh…" button to the `_make_screenshot_group` in `view_panel.py` (renaming the group "Export" — already its name). Opens a `QFileDialog.getSaveFileName` with filters for STL / OBJ / PLY / VTK; on accept, calls `mesh.save(path)` (PyVista native, no new dep needed). Optionally adds `meshio` (~1 MB) as a `requirements.txt` dep for broader format support.

**Why it matters:** CONTEXT.md §9 explicitly calls this "one line" and skipped. Every peer tool ships mesh export; researchers who want to take a generated surface into Blender / Meshmixer / a slicer are blocked today. Highest "lazy money on the table" candidate in the catalog.

**Sources:**
- Library scout: `meshio` (§2.E) Tier 1 + pyvista `mesh.save()` natively supports STL/OBJ/PLY/VTK already
- Inspiration scout: P-12 — MeshLab + Blender + ParaView all ship export as a headline feature
- Current-state critic: M-2 — `view_panel.py:246–256` + `app.py:88` (`self._raw_mesh` is already cached)

**Closest existing app analog:** `view_panel.py:_make_screenshot_group()` lines 246–255 — Screenshot only.

**Render evidence:** N/A (export, not render).

**Sketch:** `view_panel.py` grows a `get_mesh` callback constructor arg (mirroring the existing `get_actor` pattern). New `QPushButton("Export mesh…")` with `qtawesome` icon (depends on UPL-2). On click: `path, _ = QFileDialog.getSaveFileName(..., filter="STL (*.stl);;OBJ (*.obj);;PLY (*.ply);;VTK (*.vtk)")`; then `self._get_mesh().save(path)`. If `meshio` is added, the filter list extends to a dozen formats. AI-1 (PyVista) preserved; AI-2 (Qt-free tests) — the export logic is Qt-free if meshio is used directly on the cached `_raw_mesh`.

**Open questions:**
- Add meshio or rely on PyVista's native `.save()`? (Recommend defer meshio — PyVista's STL/OBJ/PLY/VTK covers 90% of demand; add meshio only if a user requests CGNS/Exodus/etc.)

---

### UPL-15 — QSettings cross-launch state persistence

**Category:** Export / persistence
**Size:** M
**Evidence triangulation:** 2 briefs (inspiration ✓ as P-11, current-state ✓ implicit via "no closeEvent state save" at `app.py:419`)
**Interaction primitives:** [INT-92 state-persistence-qsettings], [INT-4 status-bar-feedback]

**What it is:** Save `(last_variety, last_model, last_param_values_per_subtype, dock_geometry, dark_mode_state)` to `QSettings` on `MainWindow.closeEvent()`. Restore on `__init__` after UI construction, with a "Restored last session: K3 surface / Fermat quartic" status-bar message that fades after 3 seconds.

**Why it matters:** Every peer tool persists state; the app currently opens to `— Select —` on every launch. For a researcher who spends two weeks on the Hanson quintic, this is real friction.

**Sources:**
- Inspiration scout: P-11 — Blender startup file + JetBrains workspace state
- Current-state critic: implicit (no closeEvent state save observed in `app.py:419`); `design-system.md §6` explicitly marks this RECONSIDERABLE

**Closest existing app analog:** `app.py:closeEvent()` line 419 — exists but doesn't save state. No QSettings instance constructed anywhere.

**Render evidence:** N/A (state persistence).

**Sketch:** New `state_persistence.py` module exposing `save_state(window)` and `restore_state(window)`. Keys namespaced under `"varietyviewer/2026q2"`. Param values stored as JSON-serialized dicts keyed by `(variety, subtype)`. Dock geometry uses `saveState()` / `restoreState()` from QMainWindow. Restore happens after `MainWindow.__init__` finishes setting up signals, so `_on_variety_changed` fires through the normal handler. AI-9 (re-entrancy) — the restore flow must set `_computing = True` so the cascade of variety/subtype/param signals doesn't re-render N times.

**Open questions:**
- Versioning: `QSettings` keys need a schema version because adding a parameter to an existing variety changes the param-value shape. (Recommend `"varietyviewer/2026q2/v1"` as the namespace; on schema mismatch, fall back to defaults silently.)
- macOS keychain integration? (Recommend no — sensitive data isn't relevant here.)

---

### UPL-16 — Three-point lighting rig (key + fill + rim)

**Category:** Camera / viewport
**Size:** S
**Evidence triangulation:** 1 brief (visual ✓ as GAP-M1, render-evidenced)
**Interaction primitives:** [INT-83 phong-vs-flat-shading] (adjacent)

**What it is:** Replace the implicit VTK single-key-light setup with an explicit three-point rig: key (upper-left, full intensity), fill (lower-right, ~50% intensity), rim (back, ~30%). Apply via `plotter.add_light(...)` ×3 + `plotter.remove_lights()` at startup. Increase `ambient=0.2` in `add_mesh`.

**Why it matters:** GAP-M1 visual evidence: the Hanson quintic's lower-right lobes are in deep shadow under the default single key light, making concave-vs-convex indistinguishable. A fill light reveals interior structure. Hanson's original 1994 renders used a three-point rig — adopting it returns the app to the published reference.

**Sources:**
- Visual scout: GAP-M1 — "Single-key-light shadow hides interior lobe structure"; rendered evidence in `renders/calabi-yau-3-fold-hanson-quintic-dark-bg.png`

**Closest existing app analog:** `app.py:370–374` — `add_mesh(... smooth_shading=True, specular=0.3, specular_power=15)` — no `ambient` kwarg set; lighting is implicit VTK default.

**Render evidence:** `renders/calabi-yau-3-fold-hanson-quintic-dark-bg.png` shows the asymmetric shadow distribution this candidate would fix.

**Sketch:** In `MainWindow.__init__`, after plotter construction: `self.plotter.remove_lights(); self.plotter.add_light(pv.Light(position=(1,1,1), intensity=1.0)); add_light(pv.Light(position=(-1,-1,0), intensity=0.5)); add_light(pv.Light(position=(0,0,-1), intensity=0.3))`. In `_apply_domain_and_render`'s `add_mesh` call, add `ambient=0.2`. AI-7 (Hanson normals): the fill light helps reduce the visual discontinuity at patch boundaries (`consistent_normals=False`).

**Open questions:**
- Per-variety lighting? (Recommend no for v1 — single rig works for all; revisit if a specific surface needs tuning.)

---

### UPL-17 — Iconic camera presets + reset-with-margin

**Category:** Camera / viewport
**Size:** XS
**Evidence triangulation:** 2 briefs (visual ✓ via GAP-L1 + GAP-L2 in the Hanson observation, inspiration ✓ implicit)
**Interaction primitives:** [INT-23 camera-preset-fire-and-render]

**What it is:** Two small camera fixes. (a) `reset_camera()` calls in `app.py:389` get a `bounds=mesh.bounds * 1.05` (or equivalent margin factor) so default framing isn't clipped. (b) The Hanson quintic gets a named "Iconic (Hanson 1994)" camera preset matching the published angle; selectable from the View dock's preset combo.

**Why it matters:** GAP-L1 (Kummer left/right lobe tips ~5% clipped) and GAP-L2 (Hanson default α=π/4 vs iconic angle) — both small but compounding. The Hanson preset specifically connects the viewer back to the canonical reference image.

**Sources:**
- Visual scout: GAP-L1 (Kummer framing), GAP-L2 (Hanson iconic angle)
- Inspiration scout: implicit (camera presets are a near-universal peer pattern; ParaView ships several)

**Closest existing app analog:** `app.py:389` — `self.plotter.reset_camera()` with no bounds override; `view_panel.py` — preset combo exists but no "Iconic" entry.

**Render evidence:** `renders/k3-surface-kummer-surface-default.png` (crowded framing); `renders/calabi-yau-3-fold-hanson-quintic-dark-bg.png` (Hanson default angle).

**Sketch:** Modify `reset_camera()` calls to pass `bounds` with a 1.05x margin. Add a `"Hanson 1994 iconic": (azimuth=..., elevation=..., …)` entry to `view_panel.py`'s preset table (exact angles from Hanson's published Mathematica notebook; values TBD via spike).

**Open questions:**
- Margin factor: 1.05 is conservative; could be 1.1 with no harm. (Recommend 1.05 — minimum-change.)

---

### UPL-18 — Enriques sextic: mitigate sawtooth tears (resolution + Taubin)

**Category:** Camera / viewport (mesh-quality)
**Size:** M
**Evidence triangulation:** 1 brief, but render-evidenced (visual ✓ as GAP-C1 — CRITICAL)
**Interaction primitives:** N/A (offline mesh quality fix)

**What it is:** Increase the marching-cubes grid resolution near singular loci of the Enriques canonical sextic, and apply a second Taubin smoothing pass (`smooth_taubin(n_iter=40, pass_band=0.05)`) targeted at faces with anomalous normals. Alternatively (or additionally), increase the sampling box bounds slightly so the zero-locus terminates inside the grid interior, not on the wall.

**Why it matters:** The single CRITICAL finding in the catalog. `renders/enriques-surface-canonical-sextic-node-closeup.png` shows a comb-tooth tear running the length of each internal node line; the close-up reads as a renderer bug, not geometry. This is the worst first-impression surface in the canonical set.

**Sources:**
- Visual scout: GAP-C1 with three render evidence points (default, dark-bg, close-up)

**Closest existing app analog:** `surfaces.py` `_marching_cubes_to_polydata` — `smooth_taubin(n_iter=20, pass_band=0.1)`. The Fermat quartic and Kummer surface use the same pipeline and are clean because their zero loci are smooth.

**Render evidence:** `renders/enriques-surface-canonical-sextic-default.png`, `renders/enriques-surface-canonical-sextic-dark-bg.png`, `renders/enriques-surface-canonical-sextic-node-closeup.png`.

**Sketch:** Two sub-options to spike: (a) **resolution lift only** — increase the grid step from `0.04` (or current) to `0.025` near the singular locus, leaving the bulk grid coarser via an adaptive sampler. (b) **Taubin lift** — second pass of `smooth_taubin(n_iter=40, pass_band=0.05)` filtered to faces whose normal-to-neighbor angle exceeds π/3. Recommend spike both and measure: target render time stays ≤500ms per AI-imposed budget. AI-6 (implicit pipeline correctness) — neither option changes the implicit field, only the post-extraction smoothing. AI-7 (consistent_normals) — Enriques is implicit, not parametric; the AI-7 rule doesn't apply.

**Open questions:**
- Spike both (a) and (b) and benchmark before committing? (Recommend yes — this is the single highest-render-quality candidate and deserves measurement.)
- Does the existing `RuntimeWarning` pattern (used for Dwork conifold) apply here too? Should the Enriques sextic carry a "Near-singular locus — rendering may show artifacts" status-bar warning at default params? (Recommend yes — anchors INT-70 status-warning-prefix on this surface too.)

---

### UPL-19 — Enriques sextic: back-face culling toggle in Appearance dock

**Category:** Camera / viewport (mesh-quality)
**Size:** XS
**Evidence triangulation:** 1 brief (current-state ✓ as M-3)
**Interaction primitives:** [INT-83 phong-vs-flat-shading] (adjacent)

**What it is:** Pass `backface_culling=True` to `plotter.add_mesh()` for self-intersecting implicit surfaces (Enriques canonical sextic specifically); OR expose a "Back-face culling" toggle in the Appearance dock's Display group, defaulting to `True` for surfaces that are known self-intersecting and `False` otherwise.

**Why it matters:** The current-state critic reads the same Enriques visual artifact as a back-face culling issue (M-3 in their brief). The visual scout reads it as a marching-cubes resolution issue (GAP-C1). **Both interpretations have merit** — the seam artifacts at internal node lines could be either. The fix is cheap (one kwarg) and doesn't conflict with UPL-18; they should both ship if both apply.

**Sources:**
- Current-state critic: M-3 — "Missing back-face culling on Enriques sextic"

**Closest existing app analog:** `app.py:370–374` — `add_mesh(...)` with no `backface_culling` arg.

**Render evidence:** Same Enriques renders as UPL-18.

**Sketch:** Two options: (a) **Per-surface flag in `surfaces.py`:** `Surface.recommends_backface_culling: bool = False`, set to `True` only for self-intersecting cases (Enriques canonical sextic, possibly others). `app.py:_apply_domain_and_render` reads the flag and passes `backface_culling=...` to `add_mesh`. (b) **User-toggleable in Appearance dock:** new `QCheckBox` next to wireframe; default-on for self-intersecting surfaces; user-overridable. Recommend (a) for v1, (b) as v2 if a user wants pedagogical visibility. AI-13 (6-digit hex) not relevant; AI-12 (contrast) not relevant.

**Open questions:**
- Should other implicit surfaces with self-intersections (Dwork ψ → 1, Kummer at boundary) also get the flag? (Recommend audit the variety list during the spike.)

---

### UPL-20 — HiDPI workaround baked into `app.py:main()`

**Category:** Accessibility
**Size:** XS
**Evidence triangulation:** 2 briefs (visual ✓ as GAP-L2 implicit, current-state ✓ as L-3)
**Interaction primitives:** N/A

**What it is:** Add `os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")` before `QApplication(sys.argv)` in `main()`, or call `QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)` — the PySide6 6.6+ idiom.

**Why it matters:** The README documents the workaround; `app.py` does not implement it. Retina users still see jumpy sliders unless they read the README and set the env var themselves.

**Sources:**
- Visual scout: GAP-L2 — README workaround noted; not baked in
- Current-state critic: L-3 — same observation, anchored at `README.md:334` + `app.py:424`

**Closest existing app analog:** `app.py:main()` — no HiDPI scaling setup.

**Render evidence:** N/A (DPI scaling, not surface).

**Sketch:** One line. After `import os` at top of `app.py` (or wherever the import block ends): `os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")`. Test on Retina + non-Retina to verify no regression on standard displays.

**Open questions:**
- env var vs `setHighDpiScaleFactorRoundingPolicy` — pick one. (Recommend `setHighDpiScaleFactorRoundingPolicy` — more idiomatic in PySide6 6.6+.)

---

### UPL-21 — AI-11 + AI-13 cleanup sweep

**Category:** Accessibility (invariant-adjacent)
**Size:** XS
**Evidence triangulation:** 1 brief (current-state ✓ as L-1 + L-2)
**Interaction primitives:** N/A

**What it is:** Two one-character / one-line fixes:
- `app.py:425` `Qt.AA_ShareOpenGLContexts` → `Qt.ApplicationAttribute.AA_ShareOpenGLContexts` (AI-11)
- `appearance_panel.py:48` `border: 1px solid #888;` → `border: 1px solid #888888;` (AI-13 adjacency)

**Why it matters:** AI-11 / AI-13 drift accumulates silently. The current-state critic confirms these are the only two violations in the codebase. Fixing them in a single PR keeps the invariant audit clean.

**Sources:**
- Current-state critic: L-1 (AI-11) + L-2 (AI-13 adjacency)

**Closest existing app analog:** Lines cited above.

**Render evidence:** N/A.

**Sketch:** Two `Edit` calls.

**Open questions:** none.

---

### UPL-22 — Parameter sweep play button (single slider sweep at v1)

**Category:** Interaction (animation)
**Size:** M
**Evidence triangulation:** 1 brief (inspiration ✓ as P-05)
**Interaction primitives:** [INT-90 parameter-sweep-animation], [INT-3 busy-cursor], [INT-2 slider-release-render]

**What it is:** Add a small "▶" play button beside each slider row in `parameters_panel.py`. Clicking it sweeps the parameter from `spec.min` to `spec.max` in N keyframes (10–20), calling `_render_current` after each step. Sweep speed (1× / 2× / 0.5×) selectable globally.

**Why it matters:** The Dwork ψ → 1 conifold and the Hanson α projection-angle sweep are two iconic demos this would enable. INT-90 is explicitly aspirational in `interaction-vocabulary.md`; this is the v1 scope (per-slider, no full timeline UI).

**Sources:**
- Inspiration scout: P-05 — ParaView Time Manager (simplified)

**Closest existing app analog:** `parameters_panel.py:_build_row()` — slider only, no play button.

**Render evidence:** N/A (animation).

**Sketch:** New `_make_sweep_button(row)` returning a `QPushButton("▶")` with `qtawesome` play icon (depends on UPL-2). On click: a `QTimer`-driven coroutine emits `valueChanged` and `sliderReleased` for each keyframe. The existing render path handles each step. AI-9 (re-entrancy) — each sweep step must check `_computing`; if `True`, skip the step (don't queue). INT-NO-1 (real-time render during drag) preserved — the sweep is discrete keyframes, not continuous slider drag.

**Open questions:**
- Where does "Sweep speed" live? Global widget in Parameters panel header, or per-slider? (Recommend global — fewer surfaces to manage.)
- Recording capability (sweep → MP4)? (Recommend defer — that's a separate large candidate.)

---

### UPL-23 — Widen pyvista pin to `<0.50`

**Category:** Library / dependency
**Size:** XS
**Evidence triangulation:** 1 brief (library ✓ via §2.E + §5)
**Interaction primitives:** N/A

**What it is:** In `requirements.txt`, change `pyvista>=0.46,<0.49` to `pyvista>=0.46,<0.50`. No 0.49 has shipped yet, so this is forward-compatibility insurance, not a current upgrade.

**Why it matters:** The current upper bound will block the next minor release. Widening preemptively is a low-risk, no-code-change candidate.

**Sources:**
- Library scout: §2.E — confirms PyPI shows 0.48.4 as latest, 0.49 not yet released; pin needs widening when it lands

**Closest existing app analog:** `requirements.txt:2` — current pin.

**Render evidence:** N/A.

**Sketch:** One-character edit.

**Open questions:**
- Should we also bump the lower bound? (Recommend no — `>=0.46` allows broad CI compatibility.)

---

## 5. Cross-cutting tensions

1. **Enriques visual artifact — two interpretations.** Visual scout reads it as marching-cubes resolution (UPL-18); current-state critic reads it as missing back-face culling (UPL-19). Both interpretations are defensible — the central node tears are likely a near-singular-zero-crossing problem, but back-face culling would help reduce the visual prominence of the affected geometry. **Resolution:** ship both, spike UPL-18 first to measure render-time impact; UPL-19 is one kwarg so lands trivially alongside.

2. **Dark mode adoption path — hand-rolled vs `pyqtdarktheme-fork`.** Library scout recommends adopting the fork as a runtime dep; inspiration scout favors a hand-tuned Manim-aesthetic palette; current-state critic favors a parallel `STYLESHEET_DARK` in `styles.py`. **Resolution:** hand-roll `STYLESHEET_DARK` in `styles.py` using `pyqtdarktheme-fork` as a reference, NOT a runtime dep. Keeps the centralized stylesheet pattern; avoids dep churn.

3. **KaTeX vs matplotlib mathtext for equation rendering.** Library scout shows KaTeX has zero marginal bundle cost because QtWebEngine is already paid; inspiration scout proposes either as alternatives. **Resolution:** KaTeX. The QtWebEngineWidgets startup cost is the main risk; the spike should measure it before committing.

4. **First-launch hint — overlay label vs auto-render-a-default-surface.** Visual scout + current-state critic both propose an overlay; CONTEXT.md §9 rejected auto-render as presumptuous. **Resolution:** overlay only. The proposed UPL-11 is explicitly NOT auto-render.

5. **Color-map preset menu + per-variety surface color — do they conflict?** UPL-5 sets a flat per-variety default; UPL-6 lets users switch to a scalar colormap. **Resolution:** they compose. The per-variety flat color is the default; the colormap toggle replaces it for users who want to see curvature. Mutual-exclusive UI in `appearance_panel.py`.

---

## 6. Already considered + rejected

- **Mayavi as alternative renderer** — AI-1 violation; broken on Apple Silicon. Not surfaced by any brief.
- **`clip_box` on PolyData** — AI-4 violation per CONTEXT.md §8.2. Not proposed by any brief.
- **QtAds Advanced Docking System** — library scout flagged as Tier 2, but the integration cost (replace all three `QDockWidget` with `CDockManager.addDockWidget()` + a hard `requires PySide6-Essentials==6.11.0` pin) is disproportionate for a panel-refresh scope. **Reject for this uplift; revisit in a future docking-focused pass.**
- **Split viewport (P-08)** — inspiration scout proposed; substantial scope (new `QSplitter`, second `QtInteractor`, per-viewport `_computing` guard). **Reject for this uplift; deserves its own scout pass and 5-phase implementation cycle.**
- **PyInstaller packaging** — library scout flagged Tier 2 only when distribution becomes a priority; not the current goal. **Park.**
- **`qt-material` as alternative to `pyqtdarktheme-fork`** — library scout listed Tier 2; vivid Material palette is inconsistent with the subdued scientific-viz aesthetic. **Reject; UPL-4 hand-rolls instead.**
- **`PyQt-Fluent-Widgets`** — GPL-3.0; redistribution incompatibility. **Reject.**
- **`pymeshfix`** — GPL-2.0+; non-manifold repair not a current need. **Reject.**
- **`trame`** — web-companion framework; conflicts with AI-1 desktop-first architecture. **Reject.**
- **Confirmation dialog on Reset to Defaults** — explicitly rejected as anti-pattern INT-NO-9. Not proposed.
- **Auto-render first surface on launch** — CONTEXT.md §9 explicitly rejected. Not proposed (UPL-11 is an overlay, not auto-render).
- **Continuous slider re-render** — anti-pattern INT-NO-1. UPL-22 (parameter sweep) explicitly fires discrete keyframes, not continuous values.
- **Animated camera fly-through path** — too complex for panel-refresh scope. **Park for later.**

---

## 7. Interaction-vocabulary index

| INT primitive | Used by candidate(s) |
|---|---|
| [INT-2 slider-release-render] | UPL-7, UPL-22 |
| [INT-3 busy-cursor] | UPL-22 |
| [INT-4 status-bar-feedback] | UPL-11, UPL-13, UPL-15 |
| [INT-5 keyboard-shortcut] | UPL-10 |
| [INT-6 dock-floatable] | UPL-8 |
| [INT-7 tooltip-rich] | UPL-9 |
| [INT-23 camera-preset-fire-and-render] | UPL-17 |
| [INT-40 parameters-rebuild-on-switch] | UPL-2, UPL-7 |
| [INT-43 swatch-color-picker] | UPL-5, UPL-6 |
| [INT-45 dock-header-tinted] | UPL-8 |
| [INT-61 screenshot-png-save] | UPL-14 |
| [INT-70 status-warning-prefix] | UPL-12, UPL-18 |
| [INT-74 empty-clip-status-message] | UPL-11 |
| [INT-80 solid-color-bg] | UPL-3, UPL-4 |
| [INT-83 phong-vs-flat-shading] | UPL-16, UPL-19 |
| [INT-90 parameter-sweep-animation] | UPL-22 |
| [INT-92 state-persistence-qsettings] | UPL-15 |
| [INT-93 mesh-export-button] | UPL-14 |
| [INT-94 dark-mode-stylesheet] | UPL-1, UPL-4 |
| [INT-95 katex-tooltip-popover] | UPL-9 |
| [INT-96 palette-template-per-variety] | UPL-1, UPL-5 |
| [INT-97 parameter-spin-box-alternative] | UPL-7 |
| [INT-98 help-menu-with-citations] | UPL-10 |

---

*Synthesis written by main session reading all 4 discover briefs end-to-end + inspecting key renders. Foundational candidates (UPL-1, UPL-2, UPL-3) flagged for Phase 4 DAG ordering. The Enriques artifact has two interpretation paths (UPL-18, UPL-19) — both ship; both spike-ready.*
