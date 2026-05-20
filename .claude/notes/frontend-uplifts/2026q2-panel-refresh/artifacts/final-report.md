# Final Report — 2026q2-panel-refresh

**Date:** 2026-05-20
**Uplift id:** `2026q2-panel-refresh`
**Pipeline:** /frontend-uplift (4 parallel scouts → synthesis → challenger → prioritize)
**Total candidates:** 23 (UPL-1 … UPL-23)
**Challenger severity counts:** 0 BLOCKER · 5 MAJOR · 9 MINOR · 9 NONE
**Scoring:** RICE-light (R × I × C / E) + challenger penalty + foundational +30% bonus

---

## 1. Executive summary

The top-3 by adjusted RICE are: **UPL-5** (per-variety default surface color, 30.0), **UPL-3** (decouple plotter background init from `apply_to_actor`, 26.0), and **UPL-13** (status-bar mesh-extent readout, 16.0) — two of the three are XS/S, none requires new dependencies, and all three are ship-ready today with no challenger objections more serious than MINOR. The dominant theme is **"the highest-leverage modernization moves are inside `styles.py`, `app.py`, and `appearance_panel.py` — and most of them are foundational refactors or one-line bug fixes that have been deferred under the single-developer cadence."** Honest caveat: the challenger flagged five MAJOR cost-underestimations (UPL-9 KaTeX, UPL-15 QSettings, UPL-22 parameter sweep, UPL-18 Enriques resolution, UPL-8 collapsible panels) — these are the candidates Phase 4 deprioritized; treat them as second-wave only after the foundational + top-RICE first wave lands. **The Enriques sawtooth (UPL-18) is the only CRITICAL render-quality finding in the catalog**; the challenger's v0 scope-cut (second Taubin pass + bounds padding, ~2 lines) is the recommended ship path, paired with UPL-19 (back-face culling) which can land independently with no risk.

---

## 2. Quick-glance ranking table

| Rank | Cand id | Title | Category | Size | R | I | C | E | Penalty | Adj-RICE | Challenger |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | UPL-5 | Per-variety default surface color | Color/theme | S | 10 | 3 | 1.0 | 1 | NONE | **30.0** | MINOR |
| 2 | UPL-3 ⭐ | Initialize plotter bg in `MainWindow.__init__` | Color/theme | XS | 10 | 1 | 0.5 | 0.25 | +30% (foundational) | **26.0** | NONE |
| 3 | UPL-13 | Status-bar mesh-extent + bbox readout | Status/feedback | XS | 10 | 0.5 | 0.8 | 0.25 | NONE | **16.0** | NONE |
| 4 | UPL-18 | Enriques sextic: sawtooth tear mitigation | Camera/viewport | S (v0) | 10 | 3 | 0.5 | 1 | −25% (MAJOR) | **11.25** | MAJOR |
| 5 | UPL-1 ⭐ | Refactor `styles.py` into named palette tokens | Cross-cutting | S | 10 | 1 | 0.8 | 1 | +30% (foundational) | **10.4** | NONE |
| 6 | UPL-4 | Dark-mode toggle + parallel `STYLESHEET_DARK` | Color/theme | M | 10 | 3 | 1.0 | 3 | NONE | **10.0** | MINOR |
| 7 | UPL-20 | HiDPI baked into `app.py:main()` | Accessibility | XS | 10 | 0.5 | 0.5 | 0.25 | NONE | **10.0** | MINOR |
| 8 | UPL-7 | Spin-box companion alongside parameter sliders | Interaction | S | 10 | 1 | 0.8 | 1 | NONE | **8.0** | MINOR |
| 9 | UPL-23 | Widen pyvista pin to `<0.50` | Library/dep | XS | 10 | 0.5 | 0.3 | 0.25 | NONE | **6.0** | NONE |
| 10 | UPL-10 | Help menu with About + shortcuts + citations | Layout | S | 10 | 1 | 0.5 | 1 | NONE | **5.0** | NONE |
| 11 | UPL-11 | First-launch viewport hint overlay | Status/feedback | S | 10 | 1 | 0.5 | 1 | NONE | **5.0** | MINOR |
| 12 | UPL-19 | Enriques sextic: back-face culling toggle | Camera/viewport | XS | 3 | 1 | 0.3 | 0.25 | NONE | **3.6** | MINOR |
| 13 | UPL-2 ⭐ | Adopt `superqt` + `qtawesome` dep base | Library/dep | S | 10 | 0.5 | 0.5 | 1 | +30% (foundational) | **3.25** | MINOR |
| 14 | UPL-16 | Three-point lighting rig | Camera/viewport | S | 10 | 1 | 0.3 | 1 | NONE | **3.0** | NONE |
| 15 | UPL-17 | Iconic camera presets + reset-with-margin | Camera/viewport | XS | 3 | 0.5 | 0.5 | 0.25 | NONE | **3.0** | MINOR |
| 16 | UPL-14 | Mesh export (STL/OBJ/PLY) | Export/persistence | S | 3 | 1 | 0.8 | 1 | NONE | **2.4** | NONE |
| 17 | UPL-21 | AI-11 + AI-13 cleanup sweep | Accessibility | XS | 3 | 0.5 | 0.3 | 0.25 | NONE | **1.8** | MINOR |
| 18 | UPL-6 | Named color-map preset menu | Color/theme | S | 3 | 1 | 0.5 | 1 | NONE | **1.5** | MINOR |
| 19 | UPL-15 | QSettings cross-launch state persistence | Export/persistence | M | 10 | 1 | 0.5 | 3 | −25% (MAJOR) | **1.25** | MAJOR |
| 20 | UPL-22 | Parameter sweep play button | Interaction | M | 10 | 1 | 0.3 | 3 | −25% (MAJOR) | **0.75** | MAJOR |
| 21 | UPL-9 | KaTeX equation tooltip popover | Tooltips/typography | M | 3 | 1 | 0.8 | 3 | −25% (MAJOR) | **0.6** | MAJOR |
| 22 | UPL-8 | Collapsible group boxes in docks | Layout | S | 3 | 0.5 | 0.5 | 1 | −25% (MAJOR) | **0.56** | MAJOR |
| 23 | UPL-12 | Persistent surface-warning badge | Status/feedback | S | 3 | 0.5 | 0.3 | 1 | NONE | **0.45** | NONE |

⭐ = foundational candidate (synthesis Section 3). Two of the three foundational candidates (UPL-1, UPL-3) land in the top 5; UPL-2 (the `superqt`+`qtawesome` dep base) is rank 13 by RICE but is a strict prerequisite for five downstream candidates (UPL-7, UPL-8, UPL-10, UPL-14, UPL-16) — so its sequencing weight is higher than its RICE alone suggests.

---

## 3. Foundational candidates (detail FIRST so the DAG is visible)

These three unblock the rest of the catalog. Sequence them in this order regardless of their individual RICE; the downstream candidates each become 30–50% cheaper once foundationals are in place.

---

### ⭐ UPL-3 — Initialize plotter background in `MainWindow.__init__` (foundational)

**Adj-RICE: 26.0 · Rank 2 · Challenger: NONE · Size: XS · Foundational bonus: +30%**

**Synthesis sketch:** Move the `plotter.set_background(...)` call from inside `AppearancePanel.apply_to_actor()` (no-op when called with `None` at startup) to `MainWindow.__init__()` right after the plotter widget is constructed. This eliminates the light-grey-to-dark-grey background flash on first surface render.

**Why foundational:** UPL-4 (dark-mode toggle), UPL-5 (per-variety surface color), and UPL-11 (first-launch overlay) all assume a stable, intended viewport background at startup. Without this fix they layer atop a known flash.

**Render evidence:** `renders/k3-surface-fermat-quartic-default.png` vs `renders/k3-surface-fermat-quartic-dark-bg.png` — the difference is exactly what the user sees on the first ~500ms of launch today.

**Challenger objections:** None. "Two-line fix with well-understood scope. The implementation note (use the existing `#2f2f2f` literal if UPL-1 hasn't landed yet) is correct."

**RICE breakdown:** R=10 (every launch), I=1 (noticeable polish — no flash), C=0.5 (2-source: visual scout GAP-H1 + current-state critic), E=0.25 (XS, 2 lines). Base = 10×1×0.5÷0.25 = 20. Foundational +30% = **26.0**.

**DAG note:** Land standalone, no dependencies. Can ship before UPL-1.

---

### ⭐ UPL-1 — Refactor `styles.py` into named palette tokens (foundational)

**Adj-RICE: 10.4 · Rank 5 · Challenger: NONE · Size: S · Foundational bonus: +30%**

**Synthesis sketch:** Extract every hex literal in `styles.py` and `appearance_panel.py` into named palette tokens (`BG_VIEWPORT`, `BG_PANEL`, `TEXT_VALUE`, `TEXT_MUTED`, `FOCUS_RING`, `VARIETY_COLOR["K3 surface"]`, etc.). Maintain the current light palette as the existing behavior; reserve dark and per-variety dicts for follow-on candidates (UPL-4, UPL-5) to populate without touching the structure.

**Why foundational:** UPL-4, UPL-5, and UPL-11 all need the same token-extraction work. Doing it once turns three "M" implementations into three "S" implementations downstream.

**Challenger objections:** None. "Scope is well-defined, the risk is localized to `styles.py`, and it unblocks downstream candidates as stated."

**Cross-cutting concern (Challenger §6.2):** Every new dark-palette token needs a computed contrast ratio in the PR description before merge — the synthesis asserts AI-12 compliance for primary tokens but missed `COLOR_MUTED` on dark (fails ~2.5:1 / 2.9:1). When UPL-1 lands, include placeholder dark-mode tokens with WCAG-pre-computed values so UPL-4 doesn't re-litigate this.

**RICE breakdown:** R=10 (every panel uses styles), I=1 (indirect polish through downstream), C=0.8 (3-source triangulation), E=1 (S). Base = 10×1×0.8÷1 = 8.0. Foundational +30% = **10.4**.

**DAG note:** Prerequisite for UPL-4, UPL-5, UPL-11. Can land in parallel with UPL-3.

---

### ⭐ UPL-2 — Adopt `superqt` + `qtawesome` as panel-modernization dep base (foundational)

**Adj-RICE: 3.25 · Rank 13 · Challenger: MINOR · Size: S · Foundational bonus: +30%**

**Synthesis sketch:** Add `superqt>=0.8` (BSD-3-Clause) and `qtawesome>=1.4` (MIT) to `requirements.txt`. Document the cold-boot icon-font caching cost (~150–200ms one-time per launch) in CONTEXT.md §8. No UI changes at this step — this is the dep landing; downstream candidates consume.

**Why foundational despite low RICE:** UPL-7 (spinbox via `QLabeledDoubleSlider`), UPL-8 (collapsibles via `QCollapsible`), UPL-10 (Help menu icons), UPL-14 (mesh-export icon), and UPL-16 (lighting-preset icons) all depend on this dep base. RICE alone understates its load-bearing role; the foundational bonus partially compensates but the sequencing weight is what matters.

**Challenger objections:** MINOR — synthesis underdocuments the second cold-boot cost (qtpy backend detection adds another 50–100ms on first run); also recommends logging this in CONTEXT.md §8 explicitly.

**RICE breakdown:** R=10 (unlocks 5 downstream), I=0.5 (polish — pure dep landing, no immediate visible change), C=0.5 (2-source: library + inspiration scouts), E=1 (S). Base = 10×0.5×0.5÷1 = 2.5. Foundational +30% = **3.25**.

**DAG note:** Prerequisite for UPL-7, UPL-8, UPL-10 (icon), UPL-14 (icon), UPL-16 (icon), and UPL-22. If deprioritized, those five must either ship without `qtawesome` icons (degraded) or wait. **Recommend land in the same week as UPL-1 and UPL-3.**

---

## 4. Top-10 in detail

Foundational candidates above (UPL-3 / UPL-1 / UPL-2) are also in the top 10 — repeated here only briefly. Non-foundational top entries are detailed below.

---

### Rank 1 — UPL-5 — Per-variety default surface color

**Adj-RICE: 30.0 · Challenger: MINOR · Size: S**

**Synthesis sketch:** Add a `VARIETY_DEFAULT_COLOR: dict[str, str]` mapping in `styles.py` keyed by variety family. When the user picks a new variety, `AppearancePanel.set_default_color(VARIETY_DEFAULT_COLOR[variety])` updates `_surface_color`, repaints the swatch, and re-applies to the live actor. Palette proposal: K3 = `#8ab4d4`, Enriques = `#c8a880`, CY3 = `#4a90d9`, Fano = `#7ec8a0`.

**Why it ranks #1:** 4-brief triangulation (visual + library + inspiration + critic), transformative impact (3.0) on first-launch perception across all 14 surfaces, S effort, no challenger penalty. The single biggest cross-brief gripe ("all surfaces look identical at first launch") with a 1-day fix.

**Render evidence:** All four canonical renders confirm uniform hue: `renders/k3-surface-*-default.png`, `renders/enriques-surface-canonical-sextic-default.png`, `renders/calabi-yau-3-fold-hanson-quintic-default.png`.

**Challenger objections (MINOR):**
- Synthesis mis-applies WCAG AA (3:1 large-element rule) to surface color — surface color is not text. The four proposed tokens pass that threshold anyway (all ≥5.9:1), but the framing should be removed.
- Verify the four tokens visually against the light background too (for users who haven't enabled UPL-4 dark mode yet).

**RICE breakdown:** R=10 (every variety, every launch after first selection), I=3 (transformative — biggest first-impression delta), C=1.0 (4-source), E=1 (S). 10×3×1.0÷1 = **30.0**, no penalty.

**DAG note:** Depends on UPL-1 (palette tokens) for clean integration. Can ship after UPL-1.

---

### Rank 3 — UPL-13 — Status-bar mesh-extent + bbox readout

**Adj-RICE: 16.0 · Challenger: NONE · Size: XS**

**Synthesis sketch:** Append `bbox ±a × ±b × ±c` to the existing status-bar status (`{N_verts} vertices, {N_faces} faces, …`). Hover readout deferred to v2.

**Why it ranks #3:** Tiny effort (XS, ~3 lines), every render benefits, 3-source triangulation, NONE penalty. High-leverage researcher-quality-of-life addition.

**Challenger objections:** None. "~3-line patch. Hover readout correctly deferred to v2. No performance concern for the bbox-only version."

**RICE breakdown:** R=10 (every render), I=0.5 (polish — researcher convenience), C=0.8 (3-source), E=0.25 (XS). 10×0.5×0.8÷0.25 = **16.0**, no penalty.

**DAG note:** No dependencies. Can ship standalone.

---

### Rank 4 — UPL-18 — Enriques sextic: sawtooth tear mitigation

**Adj-RICE: 11.25 · Challenger: MAJOR · Size: S (challenger's v0)**

**Synthesis sketch:** Apply a second Taubin smoothing pass (`smooth_taubin(n_iter=40, pass_band=0.05)`) and pad the Enriques sampling box bounds (`bounds * 1.05`) so the zero-locus doesn't terminate on the grid wall.

**Why it ranks #4:** The **only CRITICAL** render-quality finding in the catalog. Render-evidenced at `renders/enriques-surface-canonical-sextic-node-closeup.png` (comb-tooth tear visible at default zoom). First-impression hit on the canonical-set Enriques surface.

**Render evidence:** `renders/enriques-surface-canonical-sextic-default.png`, `renders/enriques-surface-canonical-sextic-dark-bg.png`, `renders/enriques-surface-canonical-sextic-node-closeup.png`.

**Challenger objections (MAJOR):**
- Performance cost of sub-option (a) — uniform resolution increase — is undercosted (could push render time from ~500ms to 2–4 seconds).
- Sub-option (a) with adaptive sampling is L (>10 days), not M. Don't ship adaptive sampling in v0.
- **Suggested v0 (this is what the RICE row above prices):** Second Taubin pass + bounds padding only. ~2-line change. The two visual complaints (sawtooth bands + perimeter serration) both close without adaptive sampling.

**RICE breakdown (v0 scope):** R=10 (every Enriques opener — canonical set surface), I=3 (transformative — CRITICAL artifact fix), C=0.5 (1-source render-evidenced, bumped from 0.3 because the PNG is dispositive), E=1 (S in challenger's v0). 10×3×0.5÷1 = 15.0 × 0.75 (MAJOR penalty) = **11.25**.

**DAG note:** Ship **paired with UPL-19** (back-face culling). Per challenger §6.4: merge UPL-19 first (no risk), spike UPL-18 in parallel. Don't gate UPL-19 on UPL-18's spike outcome.

---

### Rank 6 — UPL-4 — Dark-mode toggle + parallel `STYLESHEET_DARK`

**Adj-RICE: 10.0 · Challenger: MINOR · Size: M**

**Synthesis sketch:** Add `STYLESHEET_DARK` to `styles.py` (hand-rolled using `pyqtdarktheme-fork` as a reference, NOT a runtime dep). Add a `QAction` (Help menu — depends on UPL-10) or a `QCheckBox` in the Appearance dock that toggles `QApplication.instance().setStyleSheet(...)` between light and dark. Also calls `plotter.set_background(BG_VIEWPORT_DARK)` on toggle.

**Why it ranks #6:** Strongest cross-brief triangulation (4 sources). Transformative impact (3.0). M effort is the main drag.

**Render evidence:** `renders/calabi-yau-3-fold-hanson-quintic-dark-bg.png` — the dark-bg Hanson render is the strongest image in the visual scout's capture set and directly demonstrates the lift.

**Challenger objections (MINOR):**
- **AI-12 missed token:** `COLOR_MUTED = #5a5a5a` fails ~2.9:1 on dark panel `#2a2f3d`. Must add `COLOR_MUTED_DARK` (e.g., `#9aabb8` for ~4.7:1) before ship.
- Toggle handler must check `_computing` and defer the plotter background change to next render cycle if a mesh is currently generating, to avoid a mid-render flash.

**RICE breakdown:** R=10 (app-wide), I=3 (transformative), C=1.0 (4-source), E=3 (M). 10×3×1.0÷3 = **10.0**, no penalty.

**DAG note:** Depends on UPL-1 (palette tokens) AND UPL-3 (background init fix). Naturally pairs with UPL-10 (Help menu hosts the toggle).

---

### Rank 7 — UPL-20 — HiDPI workaround baked into `app.py:main()`

**Adj-RICE: 10.0 · Challenger: MINOR · Size: XS**

**Synthesis sketch:** Call `QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)` before `QApplication(sys.argv)` in `main()`. Remove the README workaround paragraph once this lands.

**Why it ranks #7:** Every Retina user every launch benefits. Single-line fix.

**Challenger objections (MINOR):**
- Confirm `setHighDpiScaleFactorRoundingPolicy` is a static method that works before `QApplication` instantiation in PySide6 (it does, per docs).
- Prefer the API call over the env var path — the env var causes double-scaling on Wayland Linux.

**RICE breakdown:** R=10 (every launch on Retina), I=0.5 (polish), C=0.5 (2-source), E=0.25 (XS). 10×0.5×0.5÷0.25 = **10.0**, no penalty.

**DAG note:** No dependencies. Can ship standalone.

---

### Rank 8 — UPL-7 — Spin-box companion alongside parameter sliders

**Adj-RICE: 8.0 · Challenger: MINOR · Size: S**

**Synthesis sketch:** In `parameters_panel.py:_build_row()`, replace the read-only `QLabel` value readout with a `QDoubleSpinBox` (or `superqt.QLabeledDoubleSlider`). Bidirectional sync. Render fires only on `sliderReleased` or `spinbox.editingFinished` (preserves INT-2).

**Why it ranks #8:** Solves the textbook Dwork ψ=1.0001 conifold-research case. 3-source triangulation. S effort.

**Challenger objections (MINOR):**
- Signal-wiring care: `slider.setValue(...)` from spinbox sync must `blockSignals(True)` to avoid double-emit.
- Spike `QLabeledDoubleSlider` against one slider row before committing — verify it supports float step with `ParamSpec` range and correctly emits on edit-complete (not keypress).

**RICE breakdown:** R=10 (every parameter slider), I=1 (noticeably nicer + enables research workflow), C=0.8 (3-source), E=1 (S). 10×1×0.8÷1 = **8.0**, no penalty.

**DAG note:** Depends on UPL-2 (superqt dep base) if using `QLabeledDoubleSlider`. **Lands before UPL-22** (parameter sweep depends on stable spinbox endpoint). **Lands before UPL-15 v1** (param-value persistence) per challenger §6.3.

---

### Rank 9 — UPL-23 — Widen pyvista pin to `<0.50`

**Adj-RICE: 6.0 · Challenger: NONE · Size: XS**

**Synthesis sketch:** In `requirements.txt`, change `pyvista>=0.46,<0.49` to `pyvista>=0.46,<0.50`.

**Why it ranks #9:** Lazy-money forward-compat. Single-character edit. PyPI confirms 0.48.4 is latest, 0.49 not yet released — current pin will block the next minor when it ships.

**Challenger objections:** None.

**RICE breakdown:** R=10 (every future PyVista release), I=0.5 (polish), C=0.3 (1-source), E=0.25 (XS). 10×0.5×0.3÷0.25 = **6.0**, no penalty.

**DAG note:** No dependencies.

---

### Rank 10 — UPL-10 — Help menu with About + Keyboard Shortcuts + Citations

**Adj-RICE: 5.0 · Challenger: NONE · Size: S**

**Synthesis sketch:** Add a `QMenuBar` with "View" (hosts UPL-4 dark-mode toggle) and "Help" submenus. About dialog lists math sources from `SUBTYPE_TOOLTIPS` + README "Further reading"; Keyboard Shortcuts dialog is a 2-column action/key table.

**Why it ranks #10:** App-wide reach, S effort, 2-source triangulation, NONE penalty. Credibility surface for the research audience.

**Challenger objections:** None. "~30 lines, no AI conflicts, qtawesome dep is covered by UPL-2."

**RICE breakdown:** R=10 (app-wide menu bar), I=1 (noticeably nicer — credibility signal), C=0.5 (2-source), E=1 (S). 10×1×0.5÷1 = **5.0**, no penalty.

**DAG note:** Hosts UPL-4's toggle and benefits from UPL-2 icons. **Ships well-paired with UPL-4.**

---

## 5. Recommended next steps

### 5.1 The single foundational candidate to ship FIRST

**UPL-3** (decouple plotter background init from `apply_to_actor`) — 2-line fix, XS effort, foundational, NONE penalty, rank 2 by adjusted RICE. Removes the launch flash that every other appearance candidate has to layer atop. Ship today.

### 5.2 The 1–2 candidates ready to enter CONTEXT.md §6's 5-phase implementation pipeline NOW

**UPL-5** (per-variety default surface color) — rank 1, 4-source triangulation, S effort, MINOR challenger findings only. Hand the §6 Phase 2 implementation Sonnet the UPL-5 detail section + the AI invariants table + the four proposed hex tokens (`#8ab4d4`, `#c8a880`, `#4a90d9`, `#7ec8a0`). This is the highest-leverage 1-day investment in the catalog.

**UPL-13** (status-bar mesh-extent readout) — rank 3, XS effort, NONE penalty. ~3-line patch to `app.py:_render_current`. A perfect first-PR companion to UPL-3 since neither requires `superqt`/`qtawesome` to be in place.

### 5.3 The single spike candidate

**UPL-18** (Enriques sawtooth) — challenger flagged MAJOR with a v0 scope-cut (Taubin + bounds padding only). Run a spike day: measure render time before / after the second Taubin pass on the Enriques canonical sextic. If render time stays under the AI-imposed ~500ms budget, ship v0 alongside **UPL-19** (back-face culling — no spike needed). Defer the resolution-increase path (sub-option a) to v2.

### 5.4 Recommended first-wave bundle (5 candidates, ~2 weeks)

In this order:
1. **UPL-3** (XS, foundational, ship today)
2. **UPL-1** (S, foundational palette refactor — unblocks UPL-4 and UPL-5)
3. **UPL-5** (S, per-variety color — the rank-1 first-impression win)
4. **UPL-19** + **UPL-18 spike** (XS + S spike, Enriques visual fix — the CRITICAL finding)
5. **UPL-13** (XS, status-bar bbox — the easy researcher win)

Total effort: ~6 person-days. Touches `app.py`, `appearance_panel.py`, `styles.py`, `surfaces.py`. No new dependencies, no test scaffolding changes, no `superqt`/`qtawesome` integration risk. This wave clears all four major theme gripes (uniform color, background flash, Enriques artifact, no mesh metadata) without taking on any MAJOR-flagged candidates.

### 5.5 Recommended second-wave bundle (after first wave lands, ~2–3 weeks)

In this order:
6. **UPL-2** (S, foundational dep base — landings: `superqt`, `qtawesome`)
7. **UPL-7** (S, spinbox via QLabeledDoubleSlider — depends on UPL-2)
8. **UPL-20** (XS, HiDPI baked in)
9. **UPL-21** (XS, AI-11+AI-13 cleanup)
10. **UPL-23** (XS, pyvista pin widen)
11. **UPL-10** (S, Help menu — depends on UPL-2 for icons)
12. **UPL-4** (M, dark mode — depends on UPL-1, UPL-3, UPL-10)
13. **UPL-11** (S, first-launch overlay — depends on UPL-1 for `COLOR_MUTED_DARK`)

### 5.6 Parking lot (defer to a future uplift)

- **UPL-15** (QSettings) — MAJOR challenger penalty + cross-candidate coupling risk with UPL-7. Land only after UPL-7 ships and ParamSpec names are frozen.
- **UPL-22** (parameter sweep) — MAJOR challenger penalty (re-entrancy state machine, not the proposed `_computing` shorthand). Should be the LAST candidate to land; needs UPL-7 + UPL-15 stable first.
- **UPL-9** (KaTeX tooltip) — MAJOR challenger penalty (QtWebEngine cold-start latency). Spike-first; consider the matplotlib mathtext fallback if QWebEngineView adds >200ms to first hover.
- **UPL-8** (collapsible panels) — MAJOR challenger penalty (accessibility regression risk on disclosure-arrow focus ring). Spike accessibility verification before committing.
- **UPL-6** (color-map preset menu) — MINOR challenger penalty (`mesh.curvature()` on dense Enriques may add 150–300ms). Reasonable v2 candidate after lighting (UPL-16) clarifies whether flat-color-on-Enriques is acceptable.
- **UPL-14** (mesh export) — NONE penalty but low RICE (2.4) due to per-action reach. Genuinely a v2 quick-win; one-week project after the first wave lands. Ship as a standalone PR.
- **UPL-16** (three-point lighting) — Single-source (visual scout only). Solid candidate but waits behind the higher-impact color work.
- **UPL-17** (camera presets + reset-margin) — Split into the XS margin fix (ship in wave 2) and the S Hanson preset spike (defer to wave 3).
- **UPL-12** (persistent surface warning) — Low RICE (0.45), 1-source. Genuinely useful but tiny scope; can ride alongside UPL-18/UPL-19 since it touches `_apply_domain_and_render` similarly.
- **QtAds, split viewport, PyInstaller, `qt-material`, `PyQt-Fluent-Widgets`** — already in the synthesis "rejected" section. Not ranked.

---

## 6. Visual evidence index

| Render path | Candidates anchored on it |
|---|---|
| `renders/k3-surface-fermat-quartic-default.png` | UPL-3 (background flash demo), UPL-5 (uniform color), GAP-M2 (visually unremarkable default — UPL-17 follow-on) |
| `renders/k3-surface-fermat-quartic-2x.png` | UPL-5 |
| `renders/k3-surface-fermat-quartic-dark-bg.png` | UPL-3 (target state), UPL-4 (dark mode), UPL-5 |
| `renders/k3-surface-kummer-surface-default.png` | UPL-5, UPL-17 (Kummer framing clip) |
| `renders/k3-surface-kummer-surface-2x.png` | UPL-5 |
| `renders/enriques-surface-canonical-sextic-default.png` | **UPL-18 (CRITICAL)**, UPL-19, UPL-5 |
| `renders/enriques-surface-canonical-sextic-2x.png` | UPL-18, UPL-19 |
| `renders/enriques-surface-canonical-sextic-dark-bg.png` | UPL-18, UPL-19, UPL-4 |
| `renders/enriques-surface-canonical-sextic-node-closeup.png` | **UPL-18 (most dispositive)**, UPL-19 |
| `renders/calabi-yau-3-fold-hanson-quintic-default.png` | UPL-5, UPL-16 (lighting) |
| `renders/calabi-yau-3-fold-hanson-quintic-2x.png` | UPL-5 |
| `renders/calabi-yau-3-fold-hanson-quintic-dark-bg.png` | **UPL-4 (dark mode target image)**, UPL-5, UPL-16 |

---

## 7. Honest limitations

- **Scout budget was 15 minutes each.** Some surfaces (Fano 3-fold, additional CY3 figures, Dwork pencil at ψ=1) were not rendered — only the canonical 4 (Fermat quartic, Kummer surface, Enriques canonical sextic, Hanson quintic) appear in the visual scout's PNG capture. Findings about cross-variety patterns rely on inspection of the codebase + tooltip dict rather than render evidence for the un-rendered surfaces.
- **Triangulation across 4 briefs is strong but not infallible.** Two briefs interpreting the same evidence differently is genuine signal that the catalog surfaced (UPL-18 vs UPL-19 — Enriques artifact interpretation tension). One brief may have under-prioritized an issue another caught.
- **Effort estimates are t-shirt only (±50% accuracy is realistic).** XS/S/M/L map roughly to 0.25 / 1 / 3 / 8 person-days; the actual variance is wide. The challenger's MAJOR findings on UPL-9, UPL-15, UPL-22 specifically point at scope-creep risk.
- **Challenger evaluated against current app invariants (AI-1..AI-15) as of 2026-05-20.** If invariants evolve (e.g., AI-2 relaxes to allow `pytest-qt` once macOS GL footgun is fixed), some MAJOR objections may flip to NONE.
- **macOS Qt+VTK offscreen segfault is platform-specific.** Linux + Windows may have other footguns the scouts didn't probe (e.g., Wayland HiDPI scaling, Windows DPI awareness manifest bugs, Linux GLX context sharing).
- **RICE scoring is heuristic.** The Reach × Visual-Impact × Confidence ÷ Effort formula is fast but coarse; specifically, it under-weights candidates with strong narrative arguments that don't fit the four axes (UPL-14 mesh export is "lazy-money" by the library + critic accounts but scores only 2.4 because per-action reach is hard to capture in the R column).
- **The 30%-foundational bonus is a heuristic, not a measured DAG cost-saving.** If UPL-1 lands later than expected and three downstream candidates have already been hand-rolled with scattered hex literals, the bonus is illusory in retrospect.

---

## 8. Cross-reference index

| UPL-id | Visual | Library | Inspiration | Critic | Renders | Triangulation |
|---|---|---|---|---|---|---|
| UPL-1 | — | §2.B | P-02 | H-1, H-2, M-4 | none | 3 |
| UPL-2 | — | §2.A, §2.C | P-03, P-06 implicit | — | none | 2 |
| UPL-3 | GAP-H1 | — | — | — | k3-fermat default + dark-bg | 1 (+critic-adjacent) |
| UPL-4 | Pattern 2 | §2.B | P-02 | H-1 | hanson dark-bg | 4 |
| UPL-5 | GAP-H3 | implicit | P-04 | H-2, M-4 | all 4 canonical defaults | 4 |
| UPL-6 | — | implicit | P-01 | — | none direct | 2 |
| UPL-7 | — | §2.A | P-06 | H-3 | none | 3 |
| UPL-8 | — | §2.A | P-03 | — | none | 2 |
| UPL-9 | — | §2.F | P-10 | §7 implicit | none | 3 |
| UPL-10 | — | — | P-09 | M-6 | none | 2 |
| UPL-11 | GAP-M3 | — | — | M-1 | none | 2 |
| UPL-12 | — | — | — | M-5 | none | 1 |
| UPL-13 | implicit | — | P-07 | §7 implicit | none direct | 3 |
| UPL-14 | — | §2.E | P-12 | M-2 | none | 3 |
| UPL-15 | — | — | P-11 | implicit | none | 2 |
| UPL-16 | GAP-M1 | — | — | — | hanson dark-bg | 1 |
| UPL-17 | GAP-L1, GAP-L2 | — | implicit | — | kummer default + hanson dark-bg | 2 |
| UPL-18 | GAP-C1 | — | — | — | 3 Enriques renders | 1 (render-dispositive) |
| UPL-19 | — | — | — | M-3 | Enriques renders | 1 |
| UPL-20 | GAP-L2 implicit | — | — | L-3 | none | 2 |
| UPL-21 | — | — | — | L-1, L-2 | none | 1 |
| UPL-22 | — | — | P-05 | — | none | 1 |
| UPL-23 | — | §2.E + §5 | — | — | none | 1 |

---

## Handoff offers

### Single-candidate handoff (RICE ≥ 5)

Eleven candidates clear RICE ≥ 5 (UPL-3, UPL-1, UPL-5, UPL-13, UPL-18, UPL-4, UPL-20, UPL-7, UPL-23, UPL-10, UPL-11). To ship any of them via CONTEXT.md §6's 5-phase implementation pipeline:

1. Math research (Phase 1) is N/A for UI candidates — skip.
2. Implementation Sonnet (Phase 2): hand it the UPL-N detail section above + the AI invariants table + the synthesis sketch. Ask for a single commit at the end.
3. Adversarial Sonnet (Phase 3): scope to the new UI changes only.
4. Remediation Sonnet (Phase 4): work through the adversarial punch list.
5. UI/UX Sonnet (Phase 5): if the candidate touched cross-cutting affordances (UPL-4 dark mode, UPL-5 per-variety color, UPL-1 palette refactor).

### Multi-candidate program (first-wave bundle from §5.4)

For the recommended 5-candidate first wave (UPL-3 → UPL-1 → UPL-5 → UPL-19/18-spike → UPL-13), run them sequentially through Phase 2 → 5 of the §6 pipeline. Adversarial review is scoped per-candidate. Total expected calendar: ~2 weeks with single-developer cadence.

> **Note:** /frontend-uplift NEVER auto-invokes any implementation pipeline. The next step is yours to call.

---

*Final report written by main session reading synthesis + challenge end-to-end. Foundational candidates (UPL-1, UPL-2, UPL-3) flagged with ⭐ for DAG visibility. Challenger penalties applied per the documented schedule (BLOCKER halve / MAJOR -25% / MINOR no change / NONE no change). The 30% foundational bonus pushed UPL-3 to #2, UPL-1 to #5, and UPL-2 to #13 — only UPL-3 cleared the top-3, which the report calls out explicitly in §5.1.*
