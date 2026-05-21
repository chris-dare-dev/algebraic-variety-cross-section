# Challenge — 2026q2-graph-and-window

**Date:** 2026-05-21
**Challenger:** FRONTEND-CHALLENGER sub-agent
**Catalog challenged:** synthesis.md (29 candidates: UPL-1 through UPL-29)
**Axis checklist:** 10 axes (app-invariant compat, license, a11y regression, GL offscreen, perf, re-entrancy, cross-platform, effort honesty, anti-pattern, DAG sequencing)

---

## 1. Executive Summary

No BLOCKERs survive the gauntlet — the synthesis correctly pre-rejected the genuine AI-1 / license violators (Mayavi, qfluentwidgets, pymeshfix, clip_box, QtAds version-lock) and did not re-introduce them as candidates. There are **6 MAJOR findings** and **8 MINOR findings** across the 29 candidates; **15 candidates draw NONE**. The two dominant objection themes are:

1. **Re-entrancy / AI-9 gaps in animation candidates (UPL-16, UPL-26)**: both the parameter sweep and camera-transition candidates sketch a timer-or-animation-tick pattern that bypasses `_render_current` and calls `plotter.render()` directly — this is correct in principle but each misses at least one edge-case interaction with the existing `_computing` guard that compounds the re-entrancy risk, especially when the sweep fires at the same interval as a slow marching-cubes call (~0.5 s).

2. **Effort undercount on the dark-mode foundation (UPL-1) and superqt adoption (UPL-5, UPL-6)**: UPL-1 is sized M but the "Track A" (build-ourselves) branch carries an invisible AI-12 remediation sub-task — every existing text token must be re-verified against the dark background, and the `#5a5a5a` muted token explicitly fails at 1.94:1 (already flagged in `styles.py:62–63`). UPL-5 + UPL-6 together assume superqt's collapse animation doesn't introduce a new `processEvents` path; it does via `QPropertyAnimation` ticks, and those ticks can fire during a mesh-generation call.

---

## 2. BLOCKER Findings

None. The synthesis pre-filtered all genuine BLOCKERs in its §6 "Already Considered + Rejected" section (Mayavi — AI-1; clip_box — AI-4; pymeshfix — AGPL-3.0; qfluentwidgets — GPL-3.0; QtAds version-lock). No candidate in the catalog violates AI-1, AI-3, or AI-4, and no candidate proposes a GPL-3.0 library in a redistribution surface.

---

## 3. MAJOR Findings

### MAJOR — UPL-1 / Add APP_STYLESHEET_DARK + PALETTE_DARK

**Objections:**

- **Axis 3 (Accessibility regression risk)**: The synthesis correctly notes `TEXT_MUTED = #5a5a5a` fails at 1.94:1 on a dark background (citing `styles.py:62–63`) and names `TEXT_MUTED_DARK = #a0a0a0` as a fix. However, the M size estimate does not account for the full cascade: every text token in `PALETTE_LIGHT` (`COLOR_VALUE = #333333`, `COLOR_MUTED = #5a5a5a`, the `QStatusBar { color: #5a5a5a }` rule, the `RANGE_LABEL_STYLE`, the `QGroupBox` rule, and the five slot-specific QSS rules in `APP_STYLESHEET`) must each be re-audited against the dark background. The existing `test_styles_palette.py` tests text contrast for the light palette only — new dark-palette tests must be written. The synthesis says "AI-12 audit required" without sizing that work.
- **Axis 8 (Effort honesty)**: Track A (build-ourselves) is genuinely M, but the palette audit + test extension is 1–2 additional days that aren't priced in. Track B (pyqtdarktheme-fork) does reduce the build effort but creates an "override-on-top" layering where the app's custom QSS (`dock header`, `resetDefaultsBtn` pink) must be applied after the vendor QSS — any pyqtdarktheme-fork update that tightens specificity could silently override the app's custom rules. That maintenance surface is not mentioned.
- **Axis 10 (DAG sequencing)**: The synthesis correctly labels UPL-1 as foundational and says "Phase 4 must sequence UPL-1 ahead of UPL-10..-22." The challenger endorses this sequencing constraint but flags that if UPL-1 slips to a later sprint, UPL-10 (disabled slider QSS), UPL-12 (border contrast), UPL-13 (focus ring) should each explicitly declare a "light-only v0" scope so they can ship independently without waiting for dark-mode tokens.

**Suggested scope adjustment:** v0: implement Track A (build-ourselves) for light-palette as a no-dark-mode pass — verify all text tokens pass AI-12 on the light background, add `test_styles_palette.py` coverage for non-text contrast (AI-12 gap noted in current-state-critic §6). v1: add `PALETTE_DARK` and `APP_STYLESHEET_DARK` once the palette audit test harness is established. Track B (pyqtdarktheme-fork) should be evaluated in a follow-up after v0 ships — the override-on-top maintenance risk is real.

---

### MAJOR — UPL-5 / Adopt superqt QCollapsible for progressive panel disclosure

**Objections:**

- **Axis 6 (Re-entrancy / threading discipline)**: `superqt.QCollapsible` uses `QPropertyAnimation` internally for its open/close motion (confirmed in the library-scout brief: "QCollapsible uses QPropertyAnimation internally"). Each animation tick fires a `QPropertyAnimation::valueChanged` signal that processes the Qt event loop. If the user collapses a section *during* a mesh-generation call (slider released → `_render_current` starts → `processEvents()` fires → collapse animation tick → potential re-trigger), the `_computing` guard protects the mesh re-entry but does not protect the layout-resize path. The layout resize during animation can produce a repaint event that makes the dock flicker visually. This is not a correctness bug but is a perceptible quality regression.
- **Axis 8 (Effort honesty)**: M is correct for the initial collapsible wrap pass. However, persistence of collapse state (which the synthesis ties to UPL-25 QSettings) effectively couples UPL-5 to UPL-25 for any behavior beyond "always-expanded on launch." If UPL-25 is deferred, the "user-collapsed sticky" behavior noted in the Open Questions is missing — which means the UX delivers a non-sticky collapse behavior on every launch, a regression from a flat layout that at least remembers nothing (consistent behavior).
- **Axis 5 (Performance impact)**: The collapse animation runs on the UI thread at 60 fps (default `QPropertyAnimation` duration 300 ms, 18–20 frames). Each frame triggers a resize + repaint of the dock widget. On macOS Apple Silicon this is not a concern; on Linux or Windows with software-rendered Qt, this can stutter if a mesh generation is in flight. Not a blocker but worth a cross-platform note.

**Suggested scope adjustment:** v0: adopt `QCollapsible` with `setAnimated(False)` (instant collapse, no animation frames). v1: enable animation with a reduced duration (150 ms) once cross-platform verification is done. Decouple from UPL-25 explicitly in Phase 4 — v0 is always-expanded on launch, v1 adds sticky collapse state when UPL-25 lands.

---

### MAJOR — UPL-6 / Adopt superqt throttled signals + QLabeledSlider

**Objections:**

- **Axis 9 (Anti-pattern check — INT-NO-1)**: The synthesis proposes replacing `sliderReleased` with `superqt.signals.throttled(milliseconds=N)`. This is an INT-NO-1 violation risk: if the throttle interval N is less than the marching-cubes render time (~500 ms), the throttled signal fires multiple times during a single drag, triggering multiple renders. `superqt.signals.throttled` is a leading-edge throttle (fires on first event, then suppresses for N ms) — if N=300 ms and marching cubes takes 500 ms, the second drag event at 301 ms fires a second render *while the first is still in flight*. The `_computing` guard will block that second render, but the slider value may have advanced to a third position before the first render completes. The existing `sliderReleased` pattern is *specifically correct* for this use case — it fires exactly once on mouse-up.
- **Axis 9 (Anti-pattern check)**: The synthesis notes `superqt.signals.throttled` as a "clean replacement" for `sliderReleased`. This framing is inaccurate: throttling is appropriate for lightweight callbacks (status-bar updates); for a 500 ms marching-cubes callback, trailing-edge debounce (fire once, N ms *after* the last event) is the correct primitive, and even then `sliderReleased` is semantically more appropriate because it fires on user intent completion, not on the last timer tick.
- **Axis 8 (Effort honesty)**: XS is reasonable IF the scope is narrowed to `QLabeledSlider` only (replacing the custom `range_row` layout). The throttled-signal replacement is a scope change that should be dropped or demoted to a separate candidate.

**Suggested scope adjustment:** v0: adopt `QLabeledSlider` only — replace the custom `range_row` layout in `parameters_panel.py:160-170` with `superqt.QLabeledSlider`. Verify the value-formatting hook accepts `spec.suffix`. Drop the throttled-signal proposal entirely — `sliderReleased` is correct for the ~500 ms render pipeline. Size as XS. UPL-21 (spinbox) is then subsumed if `QLabeledSlider` includes editable value display; verify this before combining.

---

### MAJOR — UPL-16 / Parameter sweep VCR transport bar

**Objections:**

- **Axis 6 (Re-entrancy / threading discipline)**: The synthesis sketch proposes: `QTimer` tick → increment slider tick by 1 → fire `sliderReleased`. This pattern is correct in principle but creates an AI-9 violation path: `QTimer.timeout` fires → `sliderReleased` emitted → `_on_params_changed` → `_render_current` enters → `self._computing = True` → `processEvents()` drains event queue → `QTimer.timeout` may fire again during `processEvents()` if the marching-cubes call takes longer than the timer interval. The `_computing` guard suppresses the second render correctly, but the slider advances to the *next tick position* during `processEvents()`, meaning the sweep will skip positions when renders are slow. At 25 steps over 3 seconds (120 ms/step), on a slow K3 implicit surface (~500 ms/render), the sweep fires every 120 ms but only advances once every 500 ms — giving a non-uniform animation that appears to stutter. The synthesis does not address this.
- **Axis 6 (cont'd)**: The `QTimer` interval should adapt to the actual render duration, not be fixed at `int(duration_ms / steps)`. The correct pattern is: render completes → emit `sliderReleased` for the next position → advance slider → render completes → repeat. This is a trailing-fire pattern, not a fixed-interval timer.
- **Axis 8 (Effort honesty)**: M is correct only if the adaptive-timing variant is implemented. A naive fixed-interval QTimer implementation is S but ships an unreliable sweep for slow surfaces.
- **Axis 5 (Performance impact)**: Each sweep step triggers a full marching-cubes call (~0.5 s on K3, ~1–2 s on Enriques). For a 10-step sweep, total duration at K3 is ~5 s. For a 25-step sweep on Enriques at slow parameters, total duration could be ~25–50 s. The UI must stay responsive during this (busy cursor + cancel button).

**Suggested scope adjustment:** v0: single-parameter sweep with a trailing-fire pattern (render-completion drives the next advance, not a fixed-interval timer). Add a Cancel button alongside Play/Pause that stops the sweep. Parametric (Hanson) surfaces are good v0 targets since renders are fast (~100 ms); implicit surfaces (K3, Enriques) should show a "slow render — sweep will adapt" warning via `INT-70`. v1: add a configurable steps-per-second control.

---

### MAJOR — UPL-17 / KaTeX equation tooltip popover

**Objections:**

- **Axis 5 (Performance impact)**: The synthesis notes a ~100–300 ms Chromium cold-start cost and recommends pre-constructing the `QWebEngineView` at app launch. This adds ~50–80 MB to the process memory footprint on startup — always, even if the user never hovers over a combo item. For a research tool used on memory-constrained machines (e.g., a laptop running a large PyVista mesh), this is a material overhead.
- **Axis 4 (macOS GL offscreen segfault risk)**: `QWebEngineView` spawns a Chromium subprocess. On macOS, the Chromium subprocess requires a `com.apple.security.cs.allow-jit` entitlement when running under hardened runtime. Without it, the subprocess fails to start and the `QWebEngineView` shows a blank page. This is not a segfault but produces a silent failure where KaTeX tooltips never render — and the user sees no error. This risk is not mentioned in the synthesis.
- **Axis 7 (Cross-platform)**: On Linux, `QtWebEngineWidgets` requires the `libwebengine` system package (or the `PySide6-Addons` wheel). The synthesis says "zero new pip install" which is true on macOS and Windows where PySide6-Addons ships the engine bundled. On some minimal Linux environments (e.g., GitHub Actions runner, custom conda env), `QtWebEngineWidgets` is not available without explicit install. The "zero new pip install" claim should be qualified.
- **Axis 8 (Effort honesty)**: M is correct IF the scope is limited to a single `QWebEngineView` pre-constructed at launch. However, bundling KaTeX locally (the synthesis' own recommendation for offline reliability) requires: an `npm install katex` step → copying `dist/` assets into the repo → managing KaTeX version alongside the Python dep → adding the asset path to any future packaging manifest. That npm-dependency-in-a-Python-project pattern adds maintenance overhead the synthesis doesn't price.

**Suggested scope adjustment:** v0 (MINOR effort, 1 day): Apply the "minimum-viable alternative" the synthesis itself mentions — a `QToolTip` CSS font override in `APP_STYLESHEET` to standardize unicode-subscript rendering, plus explicit `QFont("monospace")` on the tooltip text. This fixes cross-platform unicode rendering for 1 line in `styles.py`. v1 (full KaTeX, M effort): pre-construct `QWebEngineView`, bundle KaTeX locally, add Chromium subprocess entitlement to macOS build, add Linux `libwebengine` note to README. Sequence v1 after v0 validates the tooltip rendering improvement.

---

### MAJOR — UPL-26 / Camera-transition interpolation (QPropertyAnimation)

**Objections:**

- **Axis 6 (Re-entrancy / threading discipline)**: The synthesis sketch proposes that camera-animation ticks "bypass `_render_current` entirely and call `plotter.render()` directly to avoid re-entrancy." This is architecturally correct — camera ticks should NOT go through `_render_current` (which has `processEvents()` + the `_computing` guard). However, calling `plotter.render()` directly does NOT set `self._computing = True`. If a slider-release event fires during a camera animation (the user releases a slider while the camera is flying to Isometric), the `_computing` guard is `False` → `_render_current` runs → `processEvents()` fires inside a VTK render cycle → undefined behavior in the VTK renderer. The synthesis does not address this interaction.
- **Axis 6 (cont'd)**: The fix is to set `self._computing = True` at the start of the camera animation and clear it in the animation's `finished` signal. The synthesis hint mentions this for `fly_to` (D2 in library brief) but not for the `QPropertyAnimation` path.
- **Axis 5 (Performance impact)**: Each animation tick calls `plotter.render()`. At 60 fps over 300 ms, that is 18 VTK render calls. Each VTK render on a 200K-face Enriques mesh takes ~16–30 ms on macOS Apple Silicon. At 30 ms/render, the 300 ms animation takes 540 ms of wall time. This is acceptable but means 60 fps is not achievable on complex meshes — the animation will appear slower than the configured duration. Not a blocker but worth documenting.

**Suggested scope adjustment:** v0: set `self._computing = True` during the camera animation + restore in the `finished` signal. Reduce default duration to 200 ms (more achievable at ~30 ms/render). Add a `reduce_motion` check (look for macOS `NSWorkspace.shared.accessibilityDisplayShouldReduceMotion` — callable via subprocess in ~2 lines) and bypass the animation if reduce-motion is set. v1: expose duration as a preference.

---

## 4. MINOR Findings

### MINOR — UPL-2 / Variety-family color tokens (fill UPL-5 placeholder)

**Objections:**

- **Axis 3 (Accessibility regression risk — AI-12)**: The sketch proposes hex colors (`#7a92b8`, `#b89878`, `#5e7fb8`, `#7ba872`) without contrast ratios against the `#2f2f2f` viewport background. Checking:
  - `#7a92b8` on `#2f2f2f`: luminance ~0.23 vs ~0.017 → ratio ~4.7:1. Marginal AA pass.
  - `#b89878` on `#2f2f2f`: luminance ~0.22 → ~4.5:1. Borderline.
  - `#5e7fb8` on `#2f2f2f`: luminance ~0.16 → ~3.4:1. AA fail for surface text labels (≥4.5:1 required for text); the surface itself at ≥3:1 non-text is borderline.
  - `#7ba872` on `#2f2f2f`: luminance ~0.17 → ~3.7:1. Marginal.
  These colors are surface mesh colors, not text colors, so the 3:1 non-text threshold applies (WCAG 2.1 §1.4.11) — but the synthesis states "All must pass AI-12 (WCAG AA)" which implies ≥4.5:1. At least two of the proposed colors fail that claim.
- **Axis 13 (AI-13)**: All proposed colors are 6-digit hex — correct.

**Suggested scope adjustment:** Re-audit all four colors against `#2f2f2f` for 3:1 non-text and 4.5:1 text (status-bar label will show variety name in these colors — that IS text). Lighten `#b89878` to `#c4a888` and `#5e7fb8` to `#7a96c8` to clear 4.5:1 comfortably. Add a `test_styles_palette.py` entry for each variety color against the dark viewport background.

---

### MINOR — UPL-3 / Color-map preset picker (named palette swatches)

**Objections:**

- **Axis 10 (DAG sequencing)**: The synthesis marks UPL-3 as "depends on UPL-2." If UPL-2 slips (or the variety color choices are revised under the AI-12 objection above), UPL-3's "variety-family group" in the preset picker inherits incorrect hex values. Phase 4 should explicitly block UPL-3 ship on UPL-2 AI-12 sign-off.
- **Axis 8 (Effort honesty)**: S is correct for the `QComboBox` + static dict. The `QStyledItemDelegate` swatch-column preview (synthesis sketch) is an additional ~20–30 lines and adds a testing surface. Consider this S+ or carve it as a v1 addition.

**Suggested scope adjustment:** v0: `QComboBox` with text-only preset names (no swatch column). v1: `QStyledItemDelegate` swatch column. Gate UPL-3 on UPL-2 AI-12 sign-off.

---

### MINOR — UPL-4 / Adopt qtawesome for toolbar + button icons

**Objections:**

- **Axis 5 (Performance impact)**: The synthesis correctly notes the 150–200 ms cold-boot cost and recommends lazy import. The sketch proposes an `icons.py` module with per-icon functions that import `qtawesome` lazily. However, if all five camera-preset buttons call their icon function during `ViewPanel._build_ui` construction (which happens at app launch before any user interaction), the lazy-import benefit is lost — the first-call cost fires at startup. The recommendation should be: lazy-import the `icons.py` module itself, not just `qtawesome` within it, and defer icon attachment until first render or first button paint.
- **Axis 12 (AI-12)**: The synthesis says icon color should be set explicitly to `COLOR_MUTED` or `COLOR_VALUE`. `COLOR_MUTED = #5a5a5a` on the light `#f0f0f0` dock header is 5.4:1 — correct. But on dark mode (UPL-1), `COLOR_MUTED` fails. The synthesis acknowledges this ("when UPL-1 lands, icon color reads from the active palette") — but if UPL-4 ships before UPL-1, icon colors must be hardcoded to the light-palette values and re-patched when UPL-1 lands. This creates a small patch-dependency debt.

**Suggested scope adjustment:** v0: wire icons to 3 highest-value targets (Reset Camera, Screenshot, Reset Defaults) as a S-scoped pilot. v1: extend to all 5 camera-preset buttons and the Wireframe/Show-edges toggles. Defer icon-color dark-mode integration until UPL-1 lands.

---

### MINOR — UPL-8 / Featured-view preset / Fermat quartic default parameters

**Objections:**

- **Axis 6 (Re-entrancy — AI-9)**: The synthesis sketch proposes "on click: set parameters via `parameters_panel.set_values({α: -0.5, γ: -3.0, c: 1.5})` AND fire camera preset." This is a two-phase state change: `set_values` triggers `_on_params_changed` → `_render_current` (mesh generation + render), and then the camera preset fires a second `plotter.render()`. If both happen synchronously without coordination, the second `render()` fires while the first is in flight (inside `processEvents()`). The AI-9 guard will suppress the second render, meaning the camera preset snap never actually applies to the new mesh — the camera stays at its prior position. The fix is to sequence: complete `_render_current` first, then fire the camera preset from the `_computing`-cleared state.

**Suggested scope adjustment:** Wire the "Featured" button to set parameters first (via `set_values`) and connect the camera-preset call to the `render_complete` signal (or place it in the `finally` block of `_render_current` via a one-shot flag). Add a `_pending_camera_preset` attribute that `_render_current` checks and fires in `finally` when set.

---

### MINOR — UPL-11 / Reset-button visual separator in Parameters panel

**Objections:**

- **Axis 11 (AI-11)**: The sketch uses `QFrame.Shape.HLine` and `QFrame.Shadow.Sunken` — these are qualified enum forms. Correct. No AI-11 violation.
- **Axis 12 (AI-12)**: `QFrame.Shadow.Sunken` on light background produces a 1px border that is ~#c8c8c8 on `#f0f0f0` — approximately 1.4:1, below the WCAG 2.1 §1.4.11 non-text contrast minimum of 3:1. A separator line is a non-text UI component and falls under §1.4.11. Using `QFrame.Shadow.Plain` (no inset shadow, renders as a flat `#b8b8b8` line) and setting `setStyleSheet("border: 1px solid #999999")` would clear 3:1.

**Suggested scope adjustment:** Set explicit `setStyleSheet("color: #999999")` on the separator (or use the `BORDER_GROUP_BOX` token after UPL-12 darkens it) so the line meets §1.4.11.

---

### MINOR — UPL-19 / Status-bar warning badge persistence

**Objections:**

- **Axis 6 (Re-entrancy — AI-9)**: The warning-accumulation path in `_render_current` already runs inside the `_computing = True` block. Adding a `QLabel` badge update inside that same block is safe. However, the badge-click handler opens a `QDialog` — if the user opens the dialog while a render is in flight (possible: render starts → `processEvents()` drains → user clicks badge → dialog opens), the dialog's modal event loop re-enters the Qt event queue while `_computing = True`. The dialog itself doesn't trigger a render but any keyboard/mouse event in the dialog can drain events that include a slider-release. The `_computing` guard protects `_render_current` but doesn't protect other slots. This is low-probability but worth a note.
- **Axis 8 (Effort honesty)**: S is correct for session-only badge. The synthesis correctly gates persistent-across-restarts on UPL-25.

**Suggested scope adjustment:** Make the warning dialog non-modal (`setWindowModality(Qt.WindowModality.NonModal)`) so it doesn't spin its own event loop. Add a `setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)` to keep it visible while the user continues probing parameters.

---

### MINOR — UPL-20 / Surface history navigation (recently-used dropdown)

**Objections:**

- **Axis 8 (Effort honesty)**: S is correct for session-only deque. The synthesis notes "Persist deque via QSettings (depends on UPL-25)" — but the deque persistence is substantially simpler than general dock-state persistence. It can ship as an independent `QSettings` write of a single JSON list without the full UPL-25 scope. The synthesis DAG dependency is overstated here.
- **Axis 10 (DAG sequencing)**: The `Alt+Left` / `Alt+Right` shortcuts conflict with standard macOS text-navigation shortcuts (`Alt+Left` moves backward one word in any text field including combo boxes). If a combo box has keyboard focus, `Alt+Left` will be consumed by the text-navigation handler, not the shortcut. Use `Ctrl+[` / `Ctrl+]` or toolbar buttons instead.

**Suggested scope adjustment:** Change the proposed keyboard shortcut from `Alt+Left/Right` to `Ctrl+[` / `Ctrl+]` (no conflict with macOS text navigation). Decouple from UPL-25 — ship deque persistence as an independent `QSettings` entry (single key, JSON list).

---

### MINOR — UPL-25 / Dock state persistence (QSettings)

**Objections:**

- **Axis 8 (Effort honesty)**: S is correct for the `saveState()` / `restoreState()` pair. However, the lessons.md already documents that QSettings persistence is routinely undercounted — "the signal-cascade re-entrancy risk on restore (variety-changed → subtype-changed → render fires N times), schema versioning, and key-existence guard for renamed varieties together add 1–2 extra days." For dock state specifically the re-entrancy risk is lower (dock state doesn't trigger renders), but the schema versioning is still needed: `saveState()` returns a `QByteArray` tagged with a format version that Qt embeds. On PySide6 version upgrade, the format version may change and `restoreState()` silently returns `False` — the app must fall back to default layout, not crash.
- **Axis 10 (DAG sequencing)**: UPL-5 (QCollapsible collapse state) correctly depends on UPL-25. UPL-20 (surface history) does NOT need to depend on UPL-25 (see UPL-20 note above).

**Suggested scope adjustment:** Add a `SETTINGS_VERSION = 1` integer that is written alongside the state blob and checked on restore. If `stored_version != SETTINGS_VERSION`, skip `restoreState()` and delete the stale key. This prevents silent layout corruption on Qt upgrades. Size as S+.

---

## 5. Clean Candidates (NONE)

The following candidates survive all 10 axes without material objection:

- **UPL-7** — Enriques backface culling: one-arg addition to `add_mesh`, no invariant interaction, hardcoded default is XS and correct.
- **UPL-9** — VTK ambient/diffuse lighting tune: 2-parameter addition to `add_mesh`, no invariant interaction, XS.
- **UPL-10** — Disabled-state QSlider QSS rule: stylesheet-only, no behavioral change, XS.
- **UPL-12** — Group-box border WCAG 1.4.11 fix: one-token change in `styles.py`, correct direction (darker border), XS.
- **UPL-13** — Focus ring contrast darken (FOCUS_RING token): one-token change, correctly cited AI-12, XS.
- **UPL-14** — Opacity slider min/max range labels: pattern-mirror from `parameters_panel.py`, XS.
- **UPL-15** — Mesh export button: correctly proposes PyVista native `save()` (no new dep), correctly notes "disable when `get_mesh()` returns None", S.
- **UPL-18** — Orientation cube gizmo: single PyVista call, AI-1 safe, S.
- **UPL-21** — Per-parameter spinbox (if UPL-6 is scoped to QLabeledSlider only): correctly flags width-budget question, S.
- **UPL-22** — Viewport text overlay for empty/launch states: correctly uses `plotter.add_text()` (not `MainWindow()` offscreen), cites AI-3 correctly, S.
- **UPL-23** — Surface-with-edges 3-way mode (radio buttons): mirrors the existing shading-group pattern, XS.
- **UPL-24** — Empty Parameters panel guidance copy: 2-line QLabel change, XS.
- **UPL-27** — Capture harness: dock-wrapped panel captures: correctly notes that bare `QDockWidget` (not embedded in `QMainWindow`) does not trigger AI-3 VTK segfault, XS tooling.
- **UPL-28** — Capture harness: dark-bg surface renders + focus-clear: two-line render-loop change, XS tooling.
- **UPL-29** — Fix Qt.AA_ShareOpenGLContexts unqualified enum (AI-11): one-line edit, XS, long overdue.

---

## 6. Cross-Cutting Concerns

### 6.1 Three candidates assume superqt is already a dep (UPL-5, UPL-6, UPL-21)

The synthesis acknowledges this in §5.3. The challenger endorses the synthesis recommendation: bundle superqt adoption into a single foundational PR, with UPL-5 (QCollapsible) as the primary and UPL-6 (QLabeledSlider) and UPL-21 (spinbox) as co-travellers. Phase 4 should gate all three on a single `pip install superqt` entry in `requirements.txt`. The `qtpy` transitive dep (MIT, already flagged by both library-scout and synthesis) is acceptable but must not be used for imports in app code — keep all app imports as `from PySide6.QtWidgets import ...`.

### 6.2 Four candidates interact with the AI-9 re-entrancy guard (UPL-5, UPL-8, UPL-16, UPL-26)

The synthesis's interaction-vocabulary index does not surface the re-entrancy guard as a shared cross-cutting concern — it only indexes INT primitives. The challenger flags that Phase 4 prioritization should sequence re-entrancy-interacting candidates with explicit AI-9 audit steps. Specifically: UPL-16 (sweep) and UPL-26 (camera animation) must each be implemented with a dedicated AI-9 guard audit before shipping.

### 6.3 The dark-mode token cascade (UPL-1) creates a hidden pre-req for five chrome candidates

UPL-10, UPL-11, UPL-12, UPL-13, UPL-22 all reference dark-mode variants ("once UPL-1 lands, define dark-mode equivalents"). If Phase 4 defers UPL-1, these five candidates should each declare explicit "light-only v0" scope with a TODO marker for dark-mode equivalents. Without this, their dark-mode halves will be orphaned as indefinitely-deferred debt.

### 6.4 The UPL-3 preset picker creates a hex-correctness dependency on UPL-2

If UPL-2's variety colors are revised (as recommended in the MINOR finding above), UPL-3's `VARIETY_DEFAULT_COLOR` seed group will reference the old values unless both are updated atomically. Phase 4 should require a single PR for UPL-2 + UPL-3 or explicit sequencing with a sign-off gate.

### 6.5 Capture harness improvements (UPL-27, UPL-28) multiply future uplift value

These two tooling candidates are the cheapest force multipliers in the catalog. The challenger strongly endorses shipping them in sprint 0 of Phase 4 (before any product candidate) so every subsequent visual-scout run benefits from accurate dock-chrome and dark-bg renders. Their cost is 2–3 days total; their benefit compounds across every future sprint.

---

## 7. Recommended Kill List

No candidates are recommended for outright kill — the synthesis pre-filtered the genuine kills in §6. However, the challenger recommends **restructuring** the following before Phase 4 prioritization:

- **UPL-6 throttled-signal proposal**: The `superqt.signals.throttled` replacement for `sliderReleased` should be removed from UPL-6's scope entirely. It is an INT-NO-1 anti-pattern for a 500 ms render pipeline. The `QLabeledSlider` adoption is worth keeping as a separate XS candidate. If Phase 4 wants to combine, the correct framing is "adopt `QLabeledSlider` only; do not replace `sliderReleased` with throttled signal."

- **UPL-17 v0 (KaTeX full implementation)**: The full KaTeX/QWebEngineView implementation should be deferred to a follow-up sprint. The v0 scoped in the MAJOR finding above (QToolTip CSS font override for unicode consistency) is the right v1 for this sprint. The macOS entitlement risk and npm-in-Python maintenance burden are real and Phase 4 should acknowledge them explicitly rather than tackling both in one sprint.

- **UPL-16 fixed-interval timer variant**: If UPL-16 ships with a fixed-interval `QTimer` (the simple sketch), it should be flagged as a "known-limitation beta" with a clear issue filed for adaptive-timing follow-up. Shipping the naive timer without the adaptive pattern produces a user-visible stutter on K3/Enriques surfaces that will read as a regression.
