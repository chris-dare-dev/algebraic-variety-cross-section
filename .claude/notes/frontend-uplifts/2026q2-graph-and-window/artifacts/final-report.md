# Final Report — 2026q2-graph-and-window

**Date:** 2026-05-21
**Pipeline:** discover (4 agents) → synthesize (29 candidates) → challenge (0 BLOCKER / 6 MAJOR / 8 MINOR / 15 NONE) → prioritize
**Status:** complete
**Source artifacts:** [synthesis.md](.claude/notes/frontend-uplifts/2026q2-graph-and-window/artifacts/synthesis.md) · [challenge.md](.claude/notes/frontend-uplifts/2026q2-graph-and-window/artifacts/challenge.md) · 4 discover briefs · 20 PNG renders

---

## 1. Executive Summary

The Algebraic Variety Viewer is a polished PySide6+PyVista app with WCAG AA-clean text contrast, rich math-honest tooltips, and a centralized stylesheet — the discover scouts found zero CRITICAL gaps and zero shippable BLOCKERs. The headline finding is the same across all four briefs: **the dark VTK viewport meets the light Qt chrome at a hard edge that no peer scientific-viz desktop tool ships**. The single highest-leverage product change is `UPL-1 — add an `APP_STYLESHEET_DARK` and apply it by default` (4-brief triangulation, foundational).

A surprise result: the three top-ranked candidates by adjusted RICE are all **XS-effort tooling/lighting fixes** (UPL-9 ambient/diffuse VTK lighting tune; UPL-27 dock-wrapped panel captures; UPL-28 dark-bg surface renders), each at RICE 12.0. These cost a single morning together and either multiply every future uplift's evidence quality or visibly improve every surface render. Phase 4 strongly recommends shipping them in a single sprint-0 PR before any product-level work.

After the sprint-0 tooling pass, the two foundational candidates (UPL-2 variety palette → UPL-1 dark mode) are the right next step. Dark mode is M-effort with an invisible AI-12 re-audit sub-task surfaced by the challenger; variety palette is S-effort and gates the downstream UPL-3 color-map preset picker. Sequencing UPL-2 ahead of UPL-1 means palette tokens are defined for both light and dark from day one.

**Caveat:** scout-run confidence ceiling is 4-brief triangulation on UPL-1 + 3-brief on UPL-2/4/5. The 19 single-brief candidates (most of the long tail) should be treated as "worth doing, low-evidence" rather than "speculative — discard." None of them duplicate existing work.

---

## 2. Quick-Glance Ranking Table

RICE = R × I × C / E. Challenger penalty: MAJOR −25%, MINOR/NONE 0%. Foundational +30%.

| Rank | ID | Title | Cat | Size | R | I | C | E | Penalty | Adj-RICE | Challenger |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | UPL-9 | VTK ambient/diffuse lighting tune | Camera/viewport | XS | 10 | 1 | 0.3 | 0.25 | 0% | **12.0** | NONE |
| 1 | UPL-27 | Capture harness: dock-wrapped panels | Refactor (tooling) | XS | 10 | 1 | 0.3 | 0.25 | 0% | **12.0** | NONE |
| 1 | UPL-28 | Capture harness: dark-bg renders + focus-clear | Refactor (tooling) | XS | 10 | 1 | 0.3 | 0.25 | 0% | **12.0** | NONE |
| 4 | UPL-2 | **Variety-family color tokens** (FOUNDATIONAL) | Color/theme | S | 10 | 1 | 0.8 | 1 | +30% | **10.4** | MINOR |
| 5 | UPL-1 | **Dark mode stylesheet** (FOUNDATIONAL) | Color/theme | M | 10 | 3 | 1.0 | 3 | +30% / −25% | **9.75** | MAJOR |
| 6 | UPL-4 | Adopt qtawesome icons | Library/dep | S | 10 | 1 | 0.8 | 1 | 0% | **8.0** | MINOR |
| 7 | UPL-17 | KaTeX tooltip (v0: QToolTip CSS font override) | Tooltips | XS | 10 | 0.5 | 0.5 | 0.25 | −25% | **7.5** | MAJOR |
| 8 | UPL-7 | Enriques backface culling | Camera/viewport | XS | 1 | 3 | 0.5 | 0.25 | 0% | **6.0** | NONE |
| 8 | UPL-8 | Featured-view preset (Fermat aesthetic on-ramp) | Camera/viewport | XS | 3 | 1 | 0.5 | 0.25 | 0% | **6.0** | MINOR |
| 8 | UPL-12 | Group-box border WCAG 1.4.11 fix | Accessibility | XS | 10 | 0.5 | 0.3 | 0.25 | 0% | **6.0** | NONE |
| 8 | UPL-13 | Focus ring contrast darken | Accessibility | XS | 10 | 0.5 | 0.3 | 0.25 | 0% | **6.0** | NONE |
| 8 | UPL-23 | Surface-with-edges 3-way mode (radios) | Interaction | XS | 10 | 0.5 | 0.3 | 0.25 | 0% | **6.0** | NONE |
| 8 | UPL-29 | Fix `Qt.AA_ShareOpenGLContexts` qualified enum | Accessibility (AI-11) | XS | 10 | 0.5 | 0.3 | 0.25 | 0% | **6.0** | NONE |
| 14 | UPL-3 | Color-map preset picker | Interaction | S | 10 | 1 | 0.5 | 1 | 0% | **5.0** | MINOR |
| 14 | UPL-15 | Mesh export button (STL/OBJ/PLY) | Export | S | 10 | 1 | 0.5 | 1 | 0% | **5.0** | NONE |
| 16 | UPL-10 | Disabled QSlider QSS rule | Accessibility | XS | 3 | 0.5 | 0.5 | 0.25 | 0% | **3.0** | NONE |
| 16 | UPL-18 | Orientation cube gizmo | Camera/viewport | S | 10 | 1 | 0.3 | 1 | 0% | **3.0** | NONE |
| 16 | UPL-20 | Surface history navigation | Interaction | S | 10 | 1 | 0.3 | 1 | 0% | **3.0** | MINOR |
| 16 | UPL-22 | Viewport text overlay (empty/launch states) | Status/feedback | S | 10 | 1 | 0.3 | 1 | 0% | **3.0** | NONE |
| 16 | UPL-25 | Dock state persistence (QSettings) | Export/persist | S | 10 | 1 | 0.3 | 1 | 0% | **3.0** | MINOR |
| 21 | UPL-6 | superqt QLabeledSlider (throttle dropped) | Library/dep | XS | 3 | 0.5 | 0.5 | 0.25 | −25% | **2.25** | MAJOR |
| 21 | UPL-26 | Camera transition interpolation | Camera/viewport | S | 10 | 1 | 0.3 | 1 | −25% | **2.25** | MAJOR |
| 23 | UPL-5 | superqt QCollapsible (animated=False v0) | Library/dep | M | 10 | 1 | 0.8 | 3 | −25% | **2.0** | MAJOR |
| 24 | UPL-24 | Empty Parameters panel guidance copy | Tooltips | XS | 3 | 0.5 | 0.3 | 0.25 | 0% | **1.8** | NONE |
| 25 | UPL-16 | Parameter sweep VCR transport bar | Interaction | M | 3 | 3 | 0.5 | 3 | −25% | **1.13** | MAJOR |
| 26 | UPL-19 | Status-bar warning badge persistence | Status | S | 3 | 1 | 0.3 | 1 | 0% | **0.9** | MINOR |
| 26 | UPL-21 | Spinbox per parameter (standalone) | Interaction | S | 3 | 1 | 0.3 | 1 | 0% | **0.9** | NONE |
| 28 | UPL-11 | Reset-button separator (Parameters) | Layout | XS | 1 | 0.5 | 0.3 | 0.25 | 0% | **0.6** | MINOR |
| 28 | UPL-14 | Opacity slider min/max range labels | Layout | XS | 1 | 0.5 | 0.3 | 0.25 | 0% | **0.6** | NONE |

29 ranked. 6 above RICE 6.0 (the natural "must ship" threshold); 8 in the 3.0–6.0 zone ("should ship"); 15 below 3.0 ("backlog").

---

## 3. Foundational Candidates

These unblock downstream candidates. **Sequence them ahead of dependents.**

### UPL-2 — Variety-family color tokens (RICE 10.4, rank #4)

**Why foundational:** UPL-3 (color-map preset picker) seeds its variety-family group from this dict. UPL-1 (dark mode) needs both `VARIETY_DEFAULT_COLOR_LIGHT` and `_DARK` defined for chrome coherence. Land first.

**Effort:** S (~1 day). Concrete blocker: challenger noted that 2 of the proposed 4 hex values (`#b89878`, `#5e7fb8`) fail WCAG 4.5:1 on the `#2f2f2f` viewport background — re-audit and lighten to e.g. `#c4a888` and `#7a96c8` before commit. Add a `test_styles_palette.py` entry for each variety color against viewport background.

**DAG:** depends on nothing. UPL-3 depends on it. UPL-1 should consume it.

**Scope adjustments:** none beyond the AI-12 re-audit. Synthesis entry is otherwise sound.

---

### UPL-1 — Dark-mode stylesheet (RICE 9.75, rank #5)

**Why foundational:** UPL-10, UPL-11, UPL-12, UPL-13, UPL-22 all reference dark-mode token equivalents in their sketches. UPL-4 icons need palette-aware coloring. Without UPL-1 these candidates ship as "light-only v0 with TODO debt."

**Effort:** M (~5–6 days), challenger-adjusted from synthesis's M because of the invisible AI-12 re-audit sub-task: every text token in `PALETTE_LIGHT` must be verified against the dark background, and the existing `test_styles_palette.py` is light-only.

**Challenger constraint:** ship Track A (build-ourselves `PALETTE_DARK` + `APP_STYLESHEET_DARK`) for v0, not Track B (pyqtdarktheme-fork) — the override-on-top maintenance surface is real. Track B can be evaluated in a follow-up.

**DAG:** depends on UPL-2 (so palette tokens are dark/light-aware from day one). Unblocks UPL-10/11/12/13/22 dark-variants.

---

## 4. Top-10 in Detail

### Tier A: XS-effort, immediate ship (ranks 1–3)

#### #1 — UPL-9 (RICE 12.0, NONE)

**What:** Add `ambient=0.15, diffuse=0.85` to the `plotter.add_mesh(...)` call in `app.py:_render_current`.

**Why:** Current-state-critic M-5 — Fermat quartic at default parameters has shallow shading under VTK scene defaults. The K3 surface family especially benefits.

**RICE breakdown:** R=10 (every surface), I=1, C=0.3 (1 brief), E=0.25. 10 × 1 × 0.3 / 0.25 = 12.0.

**Render evidence:** [k3-surface-fermat-quartic-default.png](.claude/notes/frontend-uplifts/2026q2-graph-and-window/renders/k3-surface-fermat-quartic-default.png).

**Challenger:** NONE — 2-parameter addition to existing call, no invariant interaction, XS.

**DAG:** depends on nothing. Sequence in sprint 0.

---

#### #1 (tie) — UPL-27 (RICE 12.0, NONE)

**What:** Extend `render-panel-chrome.py` to wrap each panel in a bare `QDockWidget` before grabbing. AI-3 still respected: `QDockWidget` outside `QMainWindow` does not host any `QtInteractor`.

**Why:** Current-state-critic M-4 — `styles.py:APP_STYLESHEET` carefully styles `QDockWidget::title` but panel PNGs today show no dock title bar. Without dock wrapping, dock-chrome critique is impossible.

**RICE breakdown:** R=10 (every future uplift's evidence quality), I=1, C=0.3, E=0.25. 12.0.

**Challenger:** NONE — correctly identifies that bare QDockWidget outside MainWindow doesn't trigger AI-3, XS tooling.

**Force multiplier:** every subsequent uplift run benefits.

**DAG:** depends on nothing. Sequence in sprint 0.

---

#### #1 (tie) — UPL-28 (RICE 12.0, NONE)

**What:** Two render-loop changes: (1) `p.set_background("#2f2f2f")` in the visual-scout off-screen render template so surface renders match the app default; (2) `setFocusPolicy(Qt.FocusPolicy.NoFocus)` (or `clearFocus()` after show) in `render-panel-chrome.py` to eliminate the spurious first-button-focused capture artifact.

**Why:** Visual scout H-2 (white-bg renders) + L-3 (focus ring on +X button). The scout caught both as findings in its own run — both are tooling pipeline issues, not product bugs.

**RICE breakdown:** R=10 (every future uplift), I=1, C=0.3, E=0.25. 12.0.

**Challenger:** NONE — two-line render-loop change, XS tooling.

**DAG:** depends on nothing. Sequence in sprint 0 alongside UPL-27.

---

### Tier B: Foundational (ranks 4–5)

#### #4 — UPL-2 (RICE 10.4, MINOR — see §3 above)

#### #5 — UPL-1 (RICE 9.75, MAJOR — see §3 above)

---

### Tier C: High-value polish (ranks 6–13)

#### #6 — UPL-4 (RICE 8.0, MINOR)

**What:** `pip install qtawesome`; lazy-import via `icons.py` helper; add icons to 5 camera-preset buttons + Reset Camera + Screenshot + Reset Defaults + Wireframe/Show-edges toggles.

**Why:** Every button is text-only today. Icon shape lets the eye triangulate function before reading label. Library scout's top icon candidate; 3-brief triangulation via implicit applications.

**RICE breakdown:** R=10, I=1, C=0.8 (3 briefs), E=1. 8.0.

**Challenger:** MINOR — lazy-import in `icons.py` doesn't help if `_build_ui` calls icon functions at construction. Recommendation: defer icon attachment until first paint, OR scope v0 to the 3 highest-value targets (Reset Camera, Screenshot, Reset Defaults) and extend in v1.

**Phase 4 cut:** v0 = 3-icon pilot per challenger; v1 = full coverage after UPL-1 lands.

**DAG:** UPL-1 informs icon color tokens but UPL-4 can ship light-only first.

---

#### #7 — UPL-17 (RICE 7.5, MAJOR → restructure to v0 + v1)

**What (v0):** Apply `QToolTip` CSS font override in `APP_STYLESHEET` for consistent unicode-subscript rendering across platforms. **XS effort.**

**What (v1, deferred):** Full KaTeX/QWebEngineView popover with bundled assets. M effort; carries macOS hardened-runtime entitlement risk + Linux libwebengine dep + npm-in-Python maintenance burden the challenger surfaced.

**Why:** Current tooltips use unicode subscripts (`n₁`, `φ`, `ψ`) which render inconsistently across macOS/Windows/Linux. The minimum fix is a 1-line QSS change; the maximum is a publication-quality math typography surface.

**RICE breakdown (v0):** R=10, I=0.5, C=0.5, E=0.25 → 10.0. With MAJOR penalty for the catalog entry (full implementation) → 7.5.

**Challenger:** MAJOR — recommends scope v0 (CSS) ships; full KaTeX deferred to follow-up sprint.

**DAG:** v0 depends on nothing; v1 depends on a Chromium entitlement audit.

---

#### #8 (tie, 6 candidates at RICE 6.0)

| ID | Title | Note |
|---|---|---|
| UPL-7 | Enriques backface culling | 2-brief; fixes the white zipper seam artifact (visible in 2x render). Hardcoded default v0 is XS. |
| UPL-8 | Featured-view preset | 2-brief, severity tension HIGH vs LOW. Challenger requires AI-9 guard on the combined parameter + camera change. |
| UPL-12 | Group-box border WCAG 1.4.11 | One-token change `#d0d0d0` → `#999999`. Adds non-text contrast test coverage to `test_styles_palette.py`. |
| UPL-13 | Focus ring contrast darken | `#5b9bd5` → `#3c82c4` (3.1:1) per pre-flagged `styles.py:73` comment. |
| UPL-23 | Surface-with-edges 3-way mode | Replace 2 checkboxes with 3 radios. Mirror the existing shading-group `QButtonGroup` pattern. |
| UPL-29 | `Qt.AA_ShareOpenGLContexts` qualified enum | One-line AI-11 fix — long overdue (caught in prior uplift too). |

All 6 are XS, all NONE except UPL-8 (MINOR — re-entrancy sequencing). Bundle as a "chrome polish + correctness" sprint.

---

### Tier D: Mid-value (ranks 14–20)

| ID | Title | RICE | Note |
|---|---|---|---|
| UPL-3 | Color-map preset picker | 5.0 | MINOR — depends on UPL-2 sign-off |
| UPL-15 | Mesh export button | 5.0 | NONE — closes the "Export group has only Screenshot" gap; uses PyVista native `save()` |
| UPL-10 | Disabled QSlider QSS | 3.0 | NONE — fixes disabled-rail platform-default ambiguity |
| UPL-18 | Orientation cube gizmo | 3.0 | NONE — one PyVista call, in-viewport gizmo |
| UPL-20 | Surface history navigation | 3.0 | MINOR — change shortcut from Alt+Left to Ctrl+[ (macOS text-nav conflict) |
| UPL-22 | Viewport text overlay (empty/launch) | 3.0 | NONE — `plotter.add_text()`, AI-3 safe |
| UPL-25 | Dock state persistence | 3.0 | MINOR — add SETTINGS_VERSION schema |

---

### Tier E: Backlog (ranks 21+)

15 candidates below RICE 3.0. Mostly single-brief paper-cuts (UPL-11, UPL-14, UPL-24) and challenger-discounted candidates (UPL-5, UPL-6, UPL-16, UPL-26). Worth doing if a future uplift surfaces the same candidate independently.

---

## 5. Recommended Next Steps

### Sprint 0 — Tooling + lighting quick win (XS, 1 day)

**Bundle UPL-9 + UPL-27 + UPL-28 into a single PR.** Three XS-effort changes:
- UPL-9: `add_mesh(... ambient=0.15, diffuse=0.85)` — every surface renders better
- UPL-27: dock-wrapped panel captures — every future uplift gets dock-chrome evidence
- UPL-28: dark-bg surface renders + focus-clear — every future uplift's surface renders match the app default

Total cost: 1 day. Value: improves every render today + multiplies every future uplift's evidence quality.

**This is the right first action.** Sprint 0 ships before any product change.

### Sprint 1 — Foundational chrome (S+M, ~6–7 days)

1. **UPL-2 variety palette** (S, ~1 day). Re-audit hex against `#2f2f2f` per challenger MINOR; add to `test_styles_palette.py`.
2. **UPL-1 dark mode** (M, ~5–6 days). Track A build-ourselves. Re-audit every existing text token. Ship as new default (not toggle); light-mode toggle is v1.

**Sequence:** UPL-2 first so palette tokens are dual-defined; UPL-1 second consumes both.

### Sprint 2 — Chrome polish + correctness (XS×6, ~2 days)

Bundle the 6 Tier-C candidates at RICE 6.0:
- UPL-7 Enriques backface culling
- UPL-8 Featured-view preset
- UPL-12 group-box border WCAG
- UPL-13 focus ring darken
- UPL-23 surface-with-edges 3-way radio
- UPL-29 `Qt.AA_ShareOpenGLContexts` AI-11 fix

Total: 6 candidates × XS ≈ 2 days. All cleanly NONE or MINOR-with-fix. Most have explicit `styles.py` deferral comments from prior uplifts — long overdue.

### Sprint 3 — Discovery spike: superqt collapsible

Before committing to UPL-5 (RICE 2.0, MAJOR), run a 1-day **discovery spike**: install `superqt`, wrap one panel's `QGroupBox` in `QCollapsible`, verify the `setAnimated(False)` v0 behavior + the `QPropertyAnimation`-tick interaction with `_render_current` that the challenger flagged. If the spike clears, UPL-5 is shippable in sprint 4; if it doesn't, park UPL-5 and ship the dependent UPL-25 dock state persistence directly.

### Sprint 4+ — RICE-ranked sequential sprints

The remaining mid-value candidates (UPL-3, UPL-4, UPL-15, UPL-17 v0, UPL-18, UPL-20, UPL-22, UPL-25) at RICE 5.0–8.0. Sequence by RICE-rank within their respective categories. Most are S-effort and ship 1–2 per sprint.

### Parking lot (intentional deferrals)

- **UPL-17 v1 (full KaTeX)** — challenger flagged Chromium entitlement + npm-in-Python maintenance burden. Defer until v0 validates the tooltip improvement.
- **UPL-16 parameter sweep with adaptive timing** — challenger flagged INT-NO-1 risk on fixed-interval timer. Requires trailing-fire-on-render-complete pattern; defer to a dedicated sprint with explicit AI-9 audit.
- **UPL-26 camera transition** — requires `_computing = True` during animation + reduce-motion detection. Defer pending sprint dedicated to motion accessibility.
- **UPL-5 superqt QCollapsible** — gated on the Sprint 3 spike outcome.

---

## 6. Visual Evidence Index

PNG renders cited by candidate ID. All paths relative to `.claude/notes/frontend-uplifts/2026q2-graph-and-window/`.

| Render | Used by candidate(s) |
|---|---|
| `renders/k3-surface-fermat-quartic-default.png` | UPL-2, UPL-7 (cross-ref), UPL-8, UPL-9 |
| `renders/k3-surface-fermat-quartic-2x.png` | UPL-2, UPL-9 |
| `renders/k3-surface-kummer-surface-default.png` | UPL-2, UPL-9 |
| `renders/k3-surface-kummer-surface-2x.png` | UPL-2 |
| `renders/enriques-surface-canonical-sextic-default.png` | UPL-2, UPL-7 (zipper seams), UPL-22 (sampling-box dots) |
| `renders/enriques-surface-canonical-sextic-2x.png` | UPL-7 (2x makes seams clear) |
| `renders/calabi-yau-3-fold-hanson-quintic-default.png` | UPL-2 (color cue), UPL-9 (lighting) |
| `renders/calabi-yau-3-fold-hanson-quintic-2x.png` | UPL-7 cross-ref (Hanson seams ≠ Enriques tears) |
| `renders/panels/appearance-light-empty-default.png` | UPL-4 (no icons), UPL-14 (opacity slider) |
| `renders/panels/appearance-light-empty-2x.png` | UPL-14 |
| `renders/panels/appearance-light-populated-default.png` | UPL-14, UPL-23 (wireframe + show edges checkboxes) |
| `renders/panels/appearance-light-populated-2x.png` | UPL-14, UPL-23 |
| `renders/panels/view-light-empty-default.png` | UPL-10 (disabled slider), UPL-13 (+X focus ring), UPL-15 (Export underdelivers) |
| `renders/panels/view-light-empty-2x.png` | UPL-10, UPL-13 |
| `renders/panels/view-light-populated-default.png` | UPL-4 (no icons), UPL-10 |
| `renders/panels/view-light-populated-2x.png` | UPL-4, UPL-10 |
| `renders/panels/parameters-light-empty-default.png` | UPL-24 (empty-state guidance) |
| `renders/panels/parameters-light-empty-2x.png` | UPL-24 |
| `renders/panels/parameters-light-populated-default.png` | UPL-3, UPL-6, UPL-11 (reset placement), UPL-21 |
| `renders/panels/parameters-light-populated-2x.png` | UPL-3, UPL-6, UPL-11, UPL-21 |

20 PNGs total. Net-new candidates (UPL-1, UPL-16, UPL-17, UPL-18, UPL-19, UPL-20, UPL-22, UPL-25, UPL-26, UPL-27, UPL-28, UPL-29) reference no renders directly — they're net-new features or tooling fixes.

---

## 7. Honest Limitations

- **Scout budget:** each scout had a 15-minute budget; some surfaces (Fano 3-folds, Dwork pencil, Hanson asymmetric (5,3)) were not rendered in this run. The canonical 5-surface set covered K3/Fermat, K3/Kummer, Enriques/canonical-sextic, CY3/Hanson-quintic + the synthetic app-startup placeholder.
- **Triangulation strength:** 19 candidates have 1-brief triangulation (single source). The challenger did not BLOCKER any of these but Phase 4 should weight their RICE-confidence (0.3) honestly — they survived the gauntlet but are inherently lower-evidence.
- **Effort estimates:** t-shirts (XS / S / M / L) are ±50% accurate. Calendar-precise sizing happens in the §6 Phase 2 implementation pass.
- **Invariant snapshot:** challenger evaluated against AI-1..AI-15 as of 2026-05-21. If invariants evolve (e.g., a future PyVista 0.49 upgrade addresses the `clip_box` issue, lifting AI-4), some BLOCKERs in §6 of synthesis could flip to MAJOR or NONE.
- **macOS bias:** the Qt+VTK offscreen segfault and Chromium entitlement risk are macOS-specific. Linux + Windows have their own footguns the scouts did not probe in depth. Cross-platform validation lives in implementation phase, not in this report.
- **Worktree sync drift:** during this run, two of the four scouts (visual-scout, current-state-critic) wrote their briefs into their isolation worktrees rather than the main repo. The orchestrator detected and copied them back, but the operational drift is real — future runs should verify brief presence in the main `.claude/notes/` tree explicitly after each agent returns, or invest in a cleaner cross-worktree sync.

---

## 8. Cross-Reference Index

| Candidate | Discover briefs citing it | Render evidence |
|---|---|---|
| UPL-1 (dark mode, FOUNDATIONAL) | visual H-2, library B1, inspiration PC-10 + Theme A, critic H-2 | All 12 panel PNGs (chrome is light) + all 8 surface PNGs (white bg ≠ app default) |
| UPL-2 (variety palette, FOUNDATIONAL) | visual M-1, inspiration PC-1 + PC-6 | All 8 surface PNGs |
| UPL-3 (color-map preset) | inspiration PC-1, visual M-1 | parameters-light-populated-default.png (where preset combo would land) |
| UPL-4 (qtawesome) | library C1 (top icon), inspiration PC-3 / PC-11 implicit, visual M-3 (Reset button) | view-light-* / appearance-light-* / parameters-light-* (every button is text-only) |
| UPL-5 (QCollapsible) | library A1, inspiration PC-2, visual M-2 | All 3 populated panel PNGs (panels are flat / always-visible) |
| UPL-6 (QLabeledSlider) | library A1, visual M-4 | parameters-light-populated, appearance-light-populated |
| UPL-7 (Enriques backface) | visual H-1, critic H-3 | enriques-surface-canonical-sextic-default + -2x |
| UPL-8 (Featured-view preset) | visual L-4, critic H-1 | k3-surface-fermat-quartic-default |
| UPL-9 (VTK lighting) | critic M-5 | k3-surface-fermat-quartic-default + k3-surface-kummer-surface-default |
| UPL-10 (QSlider disabled) | visual L-2, critic M-1 | view-light-empty-default |
| UPL-11 (reset separator) | critic M-2 | parameters-light-populated-default |
| UPL-12 (border WCAG) | critic L-4 + §6 audit | All panel PNGs (group-box borders) |
| UPL-13 (focus ring darken) | visual L-3 | view-light-empty-default (+X focus ring) |
| UPL-14 (opacity range labels) | visual M-4 | appearance-light-populated-default |
| UPL-15 (mesh export) | library E1, critic M-3 | view-light-populated-default (Export group has only Screenshot) |
| UPL-16 (parameter sweep) | inspiration PC-3, library D1 | net-new |
| UPL-17 (KaTeX tooltip) | library F1, inspiration PC-12 | net-new |
| UPL-18 (orientation cube) | inspiration PC-11 | net-new |
| UPL-19 (warning badge) | inspiration PC-5 | net-new |
| UPL-20 (surface history) | inspiration PC-8 | net-new |
| UPL-21 (spinbox alongside slider) | inspiration PC-7 | parameters-light-populated-default |
| UPL-22 (viewport text overlay) | inspiration PC-9 | net-new |
| UPL-23 (3-way mode radios) | visual L-5 | appearance-light-populated-default |
| UPL-24 (empty-state copy) | visual M-5 | parameters-light-empty-default |
| UPL-25 (dock persistence) | inspiration PC-4 | net-new |
| UPL-26 (camera transition) | library D1 | net-new |
| UPL-27 (dock-wrapped capture) | critic M-4 | tooling fix; all 12 panel PNGs are dock-bar-less today |
| UPL-28 (dark-bg + focus-clear) | visual H-2, visual L-3 | tooling fix; all 8 surface PNGs are white-bg today |
| UPL-29 (AI-11 enum fix) | critic §6 audit | net-new code-quality fix |

---

## Handoff offers

The next step depends on what you want to do with these findings. Three concrete paths the user can pick:

### Path A — Ship Sprint 0 (XS, 1 day)

The three RICE-12.0 candidates (UPL-9 + UPL-27 + UPL-28) are cheap, additive, and unblock every future uplift. Single PR; can be done in this session if you say "ship sprint 0."

### Path B — Hand a single candidate to the 5-phase implementation pipeline

For any candidate at RICE ≥ 5.0, CONTEXT.md §6's 5-phase pipeline (Math research → Implementation → Adversarial review → Remediation → UI/UX) can take it. For UI candidates, Phase 1 (math research) is N/A and skipped. Recommended candidates if you want a single hand-off:

- **UPL-2** (foundational, S, MINOR, clean DAG) — variety palette fill
- **UPL-1** (foundational, M, MAJOR) — dark mode, but only after UPL-2

To run via the pipeline, invoke `/milestone-pipeline UPL-2` or `/milestone-pipeline UPL-1` (the slash command at `.claude/commands/milestone-pipeline.md`).

### Path C — Refine the catalog (next uplift)

Run `/frontend-uplift 2026q2-graph-and-window-v2 --surfaces "K3 surface/Fermat quartic,Calabi–Yau 3-fold/Dwork pencil"` to surface the gaps in surfaces not rendered in this run (especially Dwork pencil at ψ=1 for the conifold warning surface). Combine with the Sprint 0 tooling fixes shipped first so the next run gets better evidence.

---

**(Per frontend-uplift policy, NEVER auto-invoke any implementation pipeline. Offer-and-wait.)**
