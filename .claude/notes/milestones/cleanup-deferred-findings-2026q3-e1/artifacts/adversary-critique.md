# Adversary critique — batch deferred-findings cleanup

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-23 | **Subject:** cleanup-deferred-findings-2026q3-e1 / `969bdd1..ca6120f`

**Diff stats:** 1018 total lines (793 insertions, 225 deletions — but ~591 of those lines are
milestone artifacts: `.claude/notes/` research brief, dispatch log, state.json; functional
code delta is ~427 lines across `app.py` +63, `styles.py` +57, `surfaces.py` +38,
`tests/test_styles_palette.py` +173).

---

## Executive summary

The dominant finding is a latent dark-mode regression introduced by Item 1: the per-palette
`BORDER_SWATCH` split was correctly applied to `PALETTE_LIGHT` and `PALETTE_DARK` dicts, but
the module-level `BORDER_SWATCH` constant at `styles.py:349` is permanently frozen to the
`PALETTE_LIGHT` value (`#333333`). `appearance_panel.py` imports this constant at module scope
and uses it for ALL themes — meaning dark-mode swatch borders render as `#333333` on
`BG_PANEL_DARK #252526` = 1.21:1, an invisible border that is worse than the pre-fix state
(1.35:1). This is a HIGH regression introduced by the very fix meant to close MF1. One MEDIUM
documents documentation drift from the Item 5 separator change not propagated to
`CONTEXT.md` / `render_worker.py`. One additional MEDIUM flags the dark-swatch test being
incomplete (it does not check the dark border vs variety fills, the same dimension the light
test correctly guards). Two LOWs cover comment precision and the auto-finding. Total: 1
CRITICAL (none), 1 HIGH, 2 MEDIUMs, 2 LOWs. Do not ship until the HIGH is rectified.

---

## Verdict: SHIP-WITH-FIXES

The high is a concrete dark-mode regression (not a hypothetical) that would make dark-mode
swatch borders invisible — worse than before the fix. Rectifying it requires either making
`_apply_swatch_color` theme-aware (passing the active palette) or adding a `BORDER_SWATCH_DARK`
module-level export. The separator documentation drift (MEDIUM) can be batched with the HIGH
rectification pass. All 7 new regression tests pass and the fix's core logic in
`PALETTE_LIGHT` is correct — the problem is narrow.

---

## Critical findings

None.

---

## High findings

### HIGH — BORDER_SWATCH module-level export frozen to PALETTE_LIGHT; dark-mode swatch border invisible

**Where:** `styles.py:349` (export site) and `appearance_panel.py:34,52` (import and use site)
**Evidence:** `styles.py:349` reads `BORDER_SWATCH = PALETTE_LIGHT["BORDER_SWATCH"]` — frozen to `#333333` regardless of active theme. `appearance_panel.py:34` imports this constant at module scope. `appearance_panel.py:52` uses it unconditionally in `_apply_swatch_color`: `f"background-color: {hex_color}; border: 1px solid {BORDER_SWATCH};"`. In dark mode (default app mode), this applies a `#333333` border to the swatch on `BG_PANEL_DARK = #252526`. Independently verified: `#333333` vs `#252526` = 1.2121:1 — an invisible border, below the pre-fix state of `#888888` at 4.32:1. The per-palette dict split at `styles.py:112` and `styles.py:281` is correct; the module-level export was not updated to serve the dark value.
**Why it matters:** The app defaults to dark mode. Every dark-mode user will see a swatch border that has zero visible contrast against the panel background — actually worse than the `#888888` that was there before this fix. The MF1 finding was a light-mode WCAG gap; this fix inadvertently introduced a dark-mode regression.
**Suggested fix:** Export both values explicitly: add `BORDER_SWATCH_DARK = PALETTE_DARK["BORDER_SWATCH"]` alongside the existing `BORDER_SWATCH = PALETTE_LIGHT["BORDER_SWATCH"]` at `styles.py:349`. Update `appearance_panel.py`'s import to include `BORDER_SWATCH_DARK`, and pass the active theme into `_apply_swatch_color` (or wire the correct token via `refresh_icons`). Alternatively, make `_apply_swatch_color` accept a `border_color` parameter defaulting to `BORDER_SWATCH` and have `refresh_icons` call `_apply_swatch_color(swatch, fill, BORDER_SWATCH_DARK if theme == "dark" else BORDER_SWATCH)`.
**Regression-guard test:** Extend `test_border_swatch_dark_wcag_3_to_1_against_bg_panel` to also assert that the dark swatch border is not identical to `PALETTE_LIGHT["BORDER_SWATCH"]` when the app is in dark mode — and add a separate assertion that the value actually used by `_apply_swatch_color` in dark mode is `PALETTE_DARK["BORDER_SWATCH"]` (source-grep: `BORDER_SWATCH_DARK` must appear within 5 lines of `_apply_swatch_color`'s call site in `refresh_icons`).

---

## Medium findings

### MEDIUM — Item 5 separator change not propagated to CONTEXT.md and render_worker.py docstring

**Where:** `CONTEXT.md:62`, `CONTEXT.md:541`, `CONTEXT.md:567`, `render_worker.py:100`
**Evidence:** The commit updated `app.py` to use `"Preview  ·  {label}"` (interpunct), but the following locations still quote the old em-dash format: `CONTEXT.md:62` (`"Preview — {label} — NNN ms"`), `CONTEXT.md:541` (`"Preview — {label}{hq_label} — NNN ms"`), `CONTEXT.md:567` (`"Preview — Fermat quartic — NNN ms"` in the manual verification checklist description), and `render_worker.py:100` (docstring: `"Preview — {label}{hq_label} — NNN ms"` badge). CONTEXT.md is the institutional memory contract; a future agent reading the badge format specification will implement the wrong separator.
**Why it matters:** CONTEXT.md §8.20 is the load-bearing reference for the Preview badge contract and is explicitly cited by the milestone pipeline's AI-15 checklist. The discrepancy between the contract text and the implementation creates a documentation drift that compounds over subsequent milestones that reference the badge format.
**Suggested fix:** Replace all four occurrences of `" — "` used as badge separators (not generic em-dashes in prose) with `"  ·  "` in CONTEXT.md (lines 62, 541, 567) and render_worker.py (line 100). The manual verification checklist at line 567 specifically describes the drag-preview badge behavior — this is the one a future developer will follow when re-validating the drag UX.

### MEDIUM — Dark-theme swatch-border test does not check contrast against variety fills

**Where:** `tests/test_styles_palette.py` (new `test_border_swatch_dark_wcag_3_to_1_against_bg_panel` function)
**Evidence:** The dark test only asserts `PALETTE_DARK["BORDER_SWATCH"]` vs `BG_PANEL_DARK` (4.32:1, PASS). It does NOT assert the dark border vs the 4 variety fill colors (the light test correctly does both). Since `VARIETY_DEFAULT_COLOR_DARK = dict(VARIETY_DEFAULT_COLOR)` (same hex values as light), the dark border `#888888` vs variety fills computes to 1.35:1 (K3), 1.56:1 (Enriques), 1.61:1 (CY3), 1.67:1 (Fano) — all failing WCAG 1.4.11's 3:1 floor for the swatch chip's interior boundary. The test passes today but silently leaves the fill-side contrast gap undetected for the dark palette.
**Why it matters:** WCAG 1.4.11 requires the boundary indicator to achieve 3:1 against BOTH adjacent surfaces (background AND component interior). The light test was correctly written to cover both; the dark companion test was only half-complete. A future palette change that moves dark variety fills could fail silently. This is the same dimension the original MF1 finding was caught on.
**Suggested fix:** Extend `test_border_swatch_dark_wcag_3_to_1_against_bg_panel` to loop over `styles.VARIETY_DEFAULT_COLOR_DARK.items()` (or equivalently `VARIETY_DEFAULT_COLOR` since they are identical) and assert `_ratio(border, fill) >= 3.0` for each fill — mirroring the light test's structure. If the dark BORDER_SWATCH (#888888) cannot clear 3:1 vs all fills, a different dark-mode token should be selected (note: this test will fail until either a different dark border token is chosen OR VARIETY_DEFAULT_COLOR_DARK is updated to darker fills).

---

## Low findings

### LOW — Item 8 comment suggests calling `qta.Spin.stop()` on the prior Spin without retaining a reference

**Where:** `app.py:1647`
**Evidence:** The comment reads "a future render-busy-spinner-v3 milestone could call `qta.Spin.stop()` on the prior animation explicitly if benchmarks ever flag it." However, `qta.Spin.stop()` requires a reference to the specific `Spin` instance (confirmed: `animation.py:44` — `stop()` calls `self.info[self.parent_widget][0].stop()`). The current code does not retain the prior `Spin` object after `setIcon()` replaces the QIcon — the `Spin` object is created inside `icons.render_busy_spinner_icon()` and only referenced via the animation state inside `self.info`. Without retaining the prior `Spin` reference, the suggested "future fix" is not directly callable; a future v3 milestone would need to restructure the factory to return the Spin object alongside the QIcon.
**Why it matters:** The comment is institutional memory; a future maintainer who reads it and searches for `Spin.stop()` in the `icons.py` factory will not find the hook they need. The suggestion is directionally correct but architecturally incomplete.
**Suggested fix:** Amend the comment to note that calling `stop()` would require the factory to return the `Spin` instance alongside the `QIcon` (or a `stop` callable), and the icon rebind site would need to call `prior_spin.stop()` before `setIcon()`. One sentence added to the existing comment block.

### LOW — Diff size auto-finding (1018 LOC; >400 threshold — non-waivable)

**Where:** no specific file
**Evidence:** `git diff 969bdd1..ca6120f | wc -l` = 1018 lines, exceeding the 400-LOC review-quality threshold (Cisco / LinearB defect-detection research: review effectiveness degrades above ~400 LOC). Breakdown: `.claude/notes/` research brief + dispatch log + state.json ≈ 471 lines of milestone artifact; `app.py` +63 / `styles.py` +57 / `surfaces.py` +38 / `tests/test_styles_palette.py` +173 = ~331 functional production+test lines; `milestone-researcher/lessons.md` ≈ 7 lines. The functional code surface is below 400 LOC; no code action is required for this finding. The finding is logged per policy (non-waivable) but the artifact inflation accounts for the overage.
**Why it matters:** Surfaced for pipeline completeness. The actual code diff (331 LOC) is well within the effective review band.
**Suggested fix:** No code action required. Recorded for pipeline log.

---

## What was done well

- **PALETTE_LIGHT BORDER_SWATCH split is technically correct.** `#333333` achieves 4.81–5.94:1 vs all 4 variety fills AND 11.09:1 vs BG_PANEL — both correctly computed and independently verified in this critique. The WCAG 1.4.11 dual-surface test logic and the cited ratios in the styles.py comment are accurate.

- **Per-palette split documentation is thorough.** The inline comment block at `styles.py:101-112` explains the pre-fix failure (1.35–1.67:1 vs fills), the fix value, and the rationale for the theme-split (dark mode needs #888888 to avoid the inverse problem). The comment at `styles.py:228-233` explicitly retracts the old "SHARED" designation and explains the split. This is precisely the level of institutional-memory documentation the pipeline expects for WCAG changes.

- **LOD note constants are named and documented.** Defining `_LOD_NOTE_COARSE`, `_LOD_NOTE_HANSON`, `_LOD_NOTE_RELEASE_ONLY` as named module-level constants with a block comment explaining the three-class taxonomy (`surfaces.py:1693-1716`) is the correct approach — it makes the vocabulary explicit and keeps tooltip strings DRY. A future maintainer adding a new surface type can see exactly which class applies.

- **Tooltip assignment correctness verified.** Each surface's coarse_n value in the registry matches its assigned LOD note: all 11 implicit surfaces with `coarse_n > 0` receive `_LOD_NOTE_COARSE`; the 3 Hanson parametric surfaces with `typical_ms > 0` (39ms, 11ms, 18ms) receive `_LOD_NOTE_HANSON`; the two-quadrics CI tube with `coarse_n=0` receives `_LOD_NOTE_RELEASE_ONLY`. The assignment logic is correct.

- **QMenu WCAG ratios independently verified.** All six cited ratios in `styles.py:493-499` (TEXT_VALUE on BG_PANEL = 11.09/11.60:1; TEXT_VALUE on BG_TOGGLE_CHECKED = 9.89/10.20:1; FOCUS_RING on BG_PANEL = 3.56/5.17:1) were independently computed and match to 4 decimal places. The cited values in the comment are accurate.

- **Item 8 qtawesome analysis is technically honest and precise.** The comment correctly identifies the `QTimer(self.parent_widget)` creation in `setup()` (not `__init__`), correctly explains the widget-parented auto-delete semantics, correctly characterizes the impact (N-times-nominal repaint rate, visually correct), and correctly notes the zero real-world impact. The `_update` vs `setup` distinction is accurate per `animation.py` source. The cross-reference between the three rebind sites (full comment at `_on_theme_changed`, abbreviated note at `_apply_system_theme`, init-site cross-reference) is the correct level of detail graduation.

- **AI-2 test hygiene is exemplary.** All 7 new regression tests use only `pathlib.Path.read_text()`, direct `styles.PALETTE_*` dict access, and pure Python WCAG arithmetic. No QApplication, no QSettings, no Qt imports — fully AI-2 compliant. The `_ratio()` helper from the existing test infrastructure is reused correctly.

- **Scope discipline is clean.** None of the explicitly deferred items (L_macos_native, enriques-backface adv_L1/front_L3, focus-ring-contrast L1, hq-smoothing-label-rename findings, render-busy-spinner LOW-3/frontend findings) crept into this milestone. The commit is tightly bounded to the 5 declared open items.

- **Items 2, 4, 6 verification.** The researcher correctly confirmed these three items as already closed by prior rect passes and produced no spurious code changes. The source-cited evidence for each closure (focus-ring-contrast milestone's FOCUS_RING value, `app.py:270` historical comment on `_inflight_is_coarse`, `tests/test_numba_field_kernels.py`'s `X**5` / `X**3` operator forms) is accurate.

---

## Recommended rectification order

1. **Fix the HIGH first (BORDER_SWATCH dark-mode regression).** Add `BORDER_SWATCH_DARK = PALETTE_DARK["BORDER_SWATCH"]` export to `styles.py` and update `appearance_panel.py` to use it in dark mode (pass theme through `_apply_swatch_color` or wire via `refresh_icons`). This is the blocking regression from Item 1. Write a regression test that asserts the value flowing into `_apply_swatch_color` in dark mode is `#888888` (not `#333333`).

2. **Batch the two MEDIUMs.** Update `CONTEXT.md:62`, `CONTEXT.md:541`, `CONTEXT.md:567`, and `render_worker.py:100` to replace the old `"Preview — "` badge format with the new `"Preview  ·  "` convention (Item 5 documentation drift). Then extend `test_border_swatch_dark_wcag_3_to_1_against_bg_panel` to also assert the dark BORDER_SWATCH clears 3:1 vs all 4 variety fills (or document why the dark fill-side gap is acceptable — the dark fills are identical to light fills, so #888888 still fails 1.35–1.67:1 there). Both changes are small and can be a single commit.

3. **Address the LOWs at discretion.** The `qta.Spin.stop()` comment precision fix (LOW) can be batched with any future `render_worker` or spinner touch. The diff-size auto-finding (LOW) requires no action.

---

*End of critique. Mandatory rectification: HIGH (items 1 and the BORDER_SWATCH_DARK export gap). MEDIUMs recommended before milestone close.*
## Frontend UI/UX findings

_Merged from milestone-frontend-ux-critic._

# Frontend UX Critique — cleanup-deferred-findings-2026q3-e1

**Critic:** milestone-frontend-ux-critic
**Commit range:** `969bdd1524891000555f6196f5735dbf64f33f55..ca6120f`
**Date:** 2026-05-23
**Files changed:** `app.py`, `styles.py`, `surfaces.py`, `tests/test_styles_palette.py`
**Panel files changed:** none (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py` untouched)

---

## Executive summary

0 CRITICAL · 0 HIGH · 3 MEDIUM · 3 LOW

The five deferred items are mechanically correct and close their respective source findings. The BORDER_SWATCH theme-split (item 1) satisfies WCAG 1.4.11 in light mode. The QMenu QSS block (item 7) applies consistent palette chrome to the Theme menu. The separator unification (item 5) is clean. The LOD suffix additions (item 3) provide honest per-subtype render-mode disclosure.

Three MEDIUM findings emerge from gaps in the new work: (1) the `QMenu::item:checked` pseudo-state is absent from the new QMenu QSS block, leaving the QActionGroup checkmark indicator in the Theme menu without explicit styling on the custom background — the "Dark" checkmark may be invisible or OS-native-colored against the dark panel; (2) `_LOD_NOTE_HANSON` says "every drag tick" but the signal fires on an 80ms debounced tick — the phrasing implies a higher frequency than the actual contract; (3) the `_LOD_NOTE_COARSE / _RELEASE_ONLY / _HANSON` constants live in `surfaces.py` but are prefixed `_` (module-private), yet the regression test in `test_styles_palette.py` references them as `surfaces._LOD_NOTE_COARSE` — the private-by-convention name leaks into a test assertion.

No AI-9/AI-11/AI-12/AI-13 new violations. No dock layout regression. No first-launch regression. No panel file touched.

---

## CRITICAL findings

None.

---

## HIGH findings

None.

---

## MEDIUM findings

### MEDIUM-1 — QMenu::item:checked rule absent; QActionGroup checkmark may be invisible on custom background

**Where:** `styles.py:504–521` (the new QMenu QSS block)

**Evidence:** The QMenu block adds `QMenu`, `QMenu::item`, `QMenu::item:selected`, and `QMenu::separator` rules, but no `QMenu::item:checked` rule. The Theme menu uses `QActionGroup(setExclusive=True)` with three `QAction(checkable=True)` entries. When the user opens the Theme menu, the active theme (e.g., "Dark") has its checkbox indicator drawn by Qt's `PE_IndicatorMenuCheckMark` primitive. Without an explicit `QMenu::item:checked` rule on the custom-background QMenu, Qt falls back to either (a) the OS-native checkmark rendered against the stylesheet background — which on macOS renders a white Aqua checkmark on `BG_PANEL = #252526` (invisible, as white-on-white fails against the dark panel when the menu background is overridden), or (b) no visible indicator at all if the stylesheet renderer takes over but has no checked-state sub-rule. The only QMenu surface in the app is the Theme menu; this means the user cannot visually confirm which theme is active from the menu.

**Why it matters:** The active theme selection is the sole purpose of the Theme menu. A user who cannot see the checkmark on the active item must dismiss the menu and observe the app chrome to determine the current theme. This is a task-completion regression: the menu fails at its primary function of communicating selection state. ParaView and GIMP both provide explicit checked-state styling on their custom-styled menus for exactly this reason.

**Suggested fix:** Add `QMenu::item:checked { font-weight: bold; color: {palette["FOCUS_RING"]}; }` (or equivalent: a `QMenu::indicator:checked` rule that sets a visible color for the checkmark glyph). The FOCUS_RING color achieves 3.56:1 on BG_PANEL light and 5.17:1 on BG_PANEL dark — WCAG-passing for both themes without a new token.

---

### MEDIUM-2 — `_LOD_NOTE_HANSON` claims "every drag tick" but signal fires at 80ms debounce intervals

**Where:** `surfaces.py:1712` (`_LOD_NOTE_HANSON = " · Renders full on every drag tick (parametric)."`)

**Evidence:** The `params_preview_changed` signal fires from `Debouncer._on_debounced_tick` at most once per 80ms during a continuous drag (`parameters_panel.py:263`: "Fires at most once per debounce interval (80 ms)"). For Hanson surfaces, `dispatch_mode` returns `"full"` and `_render_current(coarse=False)` is dispatched on each of those debounced ticks. "Every drag tick" implies a mouse-move-level granularity (typically 4–16ms) that does not match the 80ms debounce reality. A researcher who reads the tooltip and then drags slowly will see renders at approximately the debounce rate, not continuously. `VARIETY_TOOLTIPS["Calabi–Yau 3-fold"]` uses the more precise phrasing: "Hanson parametric figures render at full resolution every drag tick" — the same inaccuracy is present there too, but this milestone introduces it fresh in `_LOD_NOTE_HANSON`.

**Why it matters:** AI-15 (tooltip honesty) requires that tooltip disclosures accurately reflect actual render behavior. "Every drag tick" overpromises: a researcher optimizing for smooth interactive feedback may be surprised that renders are gated at 80ms intervals, not per-pixel-drag. The two-quadrics note ("topology too fragile") sets a strong honest-tone standard; the Hanson note undercuts it with imprecision.

**Suggested fix:** Replace `"every drag tick"` with `"every ~80 ms while dragging"` or `"at each debounced drag step (~80 ms)"`. The parenthetical `(parametric)` is well-chosen and should be retained — it's a math-register term researchers recognize. Example: `" · Renders full resolution at each drag step (~80 ms debounce; parametric)."` This is consistent with the `parameters_panel.py` docstring's own language.

---

### MEDIUM-3 — `_LOD_NOTE_*` constants are module-private but the test accesses them directly; name leakage

**Where:** `tests/test_styles_palette.py:1172–1183` (the `test_subtype_tooltips_have_lod_disclosure` test) and `surfaces.py:1711–1715` (the private constant definitions)

**Evidence:** The three LOD note constants are named `_LOD_NOTE_COARSE`, `_LOD_NOTE_HANSON`, `_LOD_NOTE_RELEASE_ONLY` — the leading underscore signals module-private by Python convention. The test file (based on the test block added in this diff) does not import or access these directly (it uses source-grep to count "preview" and "drag" occurrences in tooltip strings), so the test itself avoids the name leak. However, the constants are publicly reachable as `surfaces._LOD_NOTE_COARSE` by any caller — the underscore is a convention, not enforcement. The deeper concern: if these strings need future revision (e.g., updating "80 ms" to reflect a changed debounce interval), the change must propagate to both `surfaces.py` and `VARIETY_TOOLTIPS` (which uses freehand prose, not these constants). The constants are not shared with `VARIETY_TOOLTIPS`, which duplicates the semantic intent with different wording. `VARIETY_TOOLTIPS["Calabi–Yau 3-fold"]` says "render at full resolution every drag tick" while `_LOD_NOTE_HANSON` says "Renders full on every drag tick" — near-identical but not identical, so a future wording fix requires two edits.

**Why it matters:** The LOD wording is currently inaccurate (MEDIUM-2 above). When it is corrected, a maintainer must find both the constant definition AND the VARIETY_TOOLTIPS prose variant. Single-source-of-truth is a micro-maintenance discipline that prevents drift; the current split creates a 2-location correction burden for what should be a one-line update. Industry analogue: GIMP's and ParaView's tooltip strings are typically defined in single `.po`/`.ui` sources; the AVC hand-composed tooltip approach means this discipline must be enforced manually.

**Suggested fix:** Expose the constants as public (remove leading underscore → `LOD_NOTE_COARSE`, etc.) OR make `VARIETY_TOOLTIPS` entries reference the same constants via f-string composition. Either eliminates the drift risk. Public names also allow `test_styles_palette.py` to assert exact string membership without source-grep fallback. This is a LOW-effort refactor (renaming + wiring), not a behavior change.

---

## LOW findings

### LOW-1 — QMenu::item `padding: 4px 20px` is substantially tighter than Apple HIG recommended menu-item height

**Where:** `styles.py:511` (`QMenu::item { padding: 4px 20px; }`)

**Evidence:** At a 13pt (~17px) system font on macOS Sequoia, the total item height with `padding: 4px` top/bottom is `4 + 17 + 4 = 25px`. Apple HIG recommends 22pt (~29px) for standard menu items in macOS. The difference is ~4px per item. For the Theme menu's three items ("Dark", "Light", "Follow system"), the total menu height is `3 × 25 + 2 × 1 + 2 × 4 = 85px` versus Apple's `3 × 29 + 2 × 1 + 2 × 4 = 97px`. The 12px height deficit makes the Theme menu visually denser than native macOS menus. This is especially noticeable because the adjacent macOS system menu bar opens native-height menus; the AVC Theme menu will appear shorter than its neighbors.

**Why it matters:** On macOS, the Theme menu sits in the same menu bar as the macOS system menus. Users comparing it to a neighboring native menu will notice the height discrepancy. The tightness is likely intentional for consistency with the app's dock/panel density, but it is not documented as a deliberate choice. Mathematica's `Manipulate` and SageMath's Jupyter widget menus both adopt system-native sizing; only web-ported apps typically override menu item height.

**Suggested fix:** Either increase `QMenu::item` padding to `6px 20px` to approach HIG height, or add a comment to `styles.py` noting that the compact density is intentional (matching the app's 3px/8px QPushButton padding convention). The latter is zero-code-change and sufficient to prevent a future maintainer from widening it unnecessarily.

---

### LOW-2 — `_LOD_NOTE_RELEASE_ONLY` says "topology too fragile"; "precision-sensitive" is more accurate

**Where:** `surfaces.py:1713–1715` (`_LOD_NOTE_RELEASE_ONLY = " · Release-only render (topology too fragile for drag preview)."`)

**Evidence:** The two-quadrics CI tube uses `coarse_n=0` because `f = Q₁²+Q₂²−ε²` degenerates under a coarse marching-cubes grid — the very thin tube topology requires fine resolution to remain connected. The word "fragile" connotes structural instability (a surface that crashes or generates incorrect normals), whereas the actual issue is precision-sensitivity: at low `n`, the marching cubes grid is too coarse to resolve the thin tube, and the surface either disappears or has large holes. `VARIETY_TOOLTIPS["Fano 3-fold (ρ=1)"]` says "its topology is too fragile for any practical coarse floor" — same phrasing, same ambiguity. A researcher reading "fragile" may think the surface itself is numerically unstable, not that the coarse-preview grid is too low-resolution to capture the geometry.

**Why it matters:** AI-15 honesty: the tooltip should describe the actual phenomenon (resolution-limited preview) rather than an anthropomorphized quality ("fragile") that misleads about the mathematical nature of the surface. This is a LOW-impact word-choice issue because the behavior (release-only) is correct and the user's workflow is unaffected; the concern is specifically that a math researcher may form an incorrect model of the geometry's stability.

**Suggested fix:** Replace "topology too fragile for drag preview" with "tube too thin to resolve at coarse grid" or "coarse grid too low-res to capture the ε-tube." One example: `" · Release-only render (ε-tube too thin for coarse-preview grid)."` This is accurate, concise, and uses vocabulary (ε-tube) already established in the tooltip body.

---

### LOW-3 — Spinner comment at init site (item 8) cross-references `_on_theme_changed` by name but does not state the accumulated QTimer count semantics locally

**Where:** `app.py:391–399` (item 8 init-site comment)

**Evidence:** The init-site comment says "See the matching comment block in `_on_theme_changed` for the QTimer lifetime + theme-swap accumulation semantics — this site is the initial bind so the accumulation story doesn't apply yet (single Spin instance)." The `_on_theme_changed` comment is comprehensive (13 lines, covering accumulation, N-timers-nominal, and the mitigation rationale). The init-site is intentionally abbreviated. However, the cross-reference by method name is fragile: if `_on_theme_changed` is refactored or split, the cross-reference becomes a dead link that misleads a maintainer about where the authoritative comment lives.

**Why it matters:** The adversary's LOW-2 finding specifically requested documentation at each rebind site. The current implementation satisfies the letter of that request (a comment is present), but the two shorter sites defer to a single authoritative comment rather than standing alone. Future refactors of `_on_theme_changed` may silently orphan the cross-references. The `_apply_system_theme` site carries a one-line "mirror of the comment in _on_theme_changed above" reference — the same fragility applies. This is a documentation debt concern, not a runtime issue.

**Suggested fix:** Add one sentence to each abbreviated site describing the concrete N-timers accumulation outcome: `"Impact: N theme-swaps leave N QTimers firing widget.update() at the nominal rate — visually correct, negligible CPU."` Five words to this effect would make each site self-contained without duplicating the full rationale.

---

## What was done well

**Item 1 (BORDER_SWATCH theme-split):** The per-palette split is the minimal-diff fix; the dark palette correctly retains `#888888` (4.32:1 vs dark `BG_PANEL`) to avoid the inverse collapse (`#333333` on `#252526` = 1.21:1). The regression tests (`test_border_swatch_light_wcag_3_to_1_against_all_variety_fills`, `test_border_swatch_dark_wcag_3_to_1_against_bg_panel`, `test_border_swatch_light_and_dark_diverge`) cover all three failure modes — border-vs-fill, border-vs-bg, and accidental re-merge of the split.

**Item 3 (LOD suffix module-level constants):** Factoring the three LOD note strings into `_LOD_NOTE_COARSE`, `_LOD_NOTE_HANSON`, and `_LOD_NOTE_RELEASE_ONLY` constants prevents copy-paste drift across 14 tooltip entries. The three-class taxonomy (coarse / full-parametric / release-only) correctly mirrors the `dispatch_mode` return values and accurately categorizes each subtype. The Dwork pencil correctly receives `_LOD_NOTE_COARSE` despite being in the CY3 family alongside the Hanson parametrics — accurate because the Dwork is an implicit surface with `coarse_n=100`.

**Item 5 (separator unification):** The separator change is clean and the associated comment block explains the vocabulary rationale and the prior em-dash's origin without being polemical. The regression test guards both the positive form (`f"Preview  ·  "` present) and the negative form (`f"Preview — "` absent).

**Item 7 (QMenu QSS):** All four WCAG ratio assertions are documented inline at the rule site. AI-13 compliance is explicit (all values via palette tokens, no inline literals noted in the comment). The `QMenu::separator` rule uses `BORDER_GROUP_BOX` for the 1px line — consistent with the group-box separator token rather than introducing a new one.

**Item 8 (spinner comments):** The `_on_theme_changed` comment is thorough — 13 lines that explain the mechanism, the N-timers accumulation, the visual correctness (always most-recent QIcon), and the "no real-world impact" rationale with a forward-pointer to a hypothetical v3 cleanup. This level of institutional-memory documentation is the right call for a subtle qtawesome lifecycle edge case that would otherwise mystify a future contributor.

---

## Recommended rectification order

1. **MEDIUM-1 first (QMenu::item:checked)** — functional gap: the Theme menu cannot confirm its selection state to the user. Single-line addition to `styles.py`. Run `test_qmenu_rule_present_in_both_stylesheets` after to confirm the QMenu block is intact.

2. **MEDIUM-2 next (Hanson "drag tick" phrasing)** — AI-15 honesty correction. Update `_LOD_NOTE_HANSON` in `surfaces.py:1712` and the VARIETY_TOOLTIPS CY3 entry which uses the same phrase (`surfaces.py:1678`). The subtype test will need updating if it asserts exact string content; more likely the source-grep proxy test passes unchanged.

3. **MEDIUM-3 (constant naming + VARIETY_TOOLTIPS parity)** — can be batched with MEDIUM-2 since both touch `surfaces.py`. Expose constants as public names and wire `VARIETY_TOOLTIPS` to reference them, eliminating the prose-drift risk.

4. **LOW-1 and LOW-2** — comment-only or single word-substitution, defer to the next cleanup pass.

5. **LOW-3** — amend the abbreviated spinner-site comments to be self-contained; defer to the next cleanup pass.

---

## Rectification status — 2026-05-23

**Fixed (in-scope, this rect commit):**
- `adversary HIGH` (BORDER_SWATCH module-level export frozen to PALETTE_LIGHT — dark-mode swatch border invisible): added explicit `BORDER_SWATCH_DARK` export to `styles.py`; `appearance_panel.py` imports it and routes the active-theme value via a new `_border_for_theme(theme)` helper; `_apply_swatch_color` now takes a `border` kwarg routed from all 4 call sites (2 construction + 2 live `_pick_*_color` repaints + 1 `set_default_color`); `refresh_icons(theme)` now also stores `self._active_theme = theme` and repaints both existing swatches with the new theme's border so theme swaps don't leave stale-color borders. Without this rect, the item-1 fix would have introduced a dark-mode regression worse than the original MF1 — `#333333` on `BG_PANEL_DARK #252526` = 1.21:1, an INVISIBLE border. The Phase 3 adversary critic caught this within the same critique cycle that closed the original finding.
- `adversary MEDIUM` (separator drift in CONTEXT.md + render_worker.py): updated all 4 cited badge-format references (`CONTEXT.md:62`, `CONTEXT.md:541`, `CONTEXT.md:567`, `render_worker.py:100`) from `"Preview — {label} — NNN ms"` (em-dash) to `"Preview  ·  {label}  ·  NNN ms"` (interpunct). Documentation contract now matches implementation.
- `adversary MEDIUM` (dark-test fill-coverage gap): extended `test_border_swatch_dark_wcag_3_to_1_against_bg_panel` to also assert each dark variety fill achieves ≥3:1 vs `BG_PANEL_DARK` — anchors the WCAG 1.4.11 reasoning behind why the dark test does NOT require strict dual-surface vs the border (the fills themselves provide boundary contrast). Added inline docstring section explaining the principled asymmetry between light and dark tests.
- `frontend MEDIUM-1` (QMenu::item:checked rule absent): added explicit `QMenu::item:checked { font-weight: bold; background-color: ... }` rule to `_render_stylesheet`. The Theme menu's QActionGroup checkmark now uses font-weight as the active-selection indicator rather than depending on the OS-native checkmark glyph (which would not paint reliably against the custom dark-theme background).
- `frontend MEDIUM-2` (`_LOD_NOTE_HANSON` "every drag tick" honesty gap): reworded to `"Renders full at every debounced drag tick (~80 ms; parametric)"` — surfaces the debounce interval honestly so the user understands a fast drag may not see every-frame render.
- `frontend LOW-2` ("topology too fragile" → "precision-sensitive"): reworded `_LOD_NOTE_RELEASE_ONLY` to `"Release-only render (topology precision-sensitive; coarse drag preview would degrade the mesh)"` — names the actual mechanism (coarse marching cubes precision floor) rather than vague "fragile".
- `adversary LOW-1` (Spin.stop() comment architecturally incomplete): amended the `_on_theme_changed` spinner-comment block to clarify that the suggested v3 hook requires (a) refactoring `icons.render_busy_spinner_icon` to return the `Spin` instance alongside the `QIcon`, and (b) retaining that reference at the rebind site so `prior_spin.stop()` is callable. Without this clarification, a future maintainer reading the comment would search for an immediately-callable hook that doesn't exist.

Added regression-guard test `test_border_swatch_dark_export_wired_through_appearance_panel` — anchors all 3 wires of the HIGH fix: (a) `BORDER_SWATCH_DARK` export exists, (b) `appearance_panel.py` imports it, (c) `_border_for_theme` is called ≥5 times across all swatch-paint sites.

**Invalidated:**
- `frontend MEDIUM-3` (`_LOD_NOTE_*` constants module-private but test accesses them): verified — `grep -rn _LOD_NOTE tests/` returns 0 hits. The test only checks substrings (`"preview"`, `"drag tick"`, `"Release-only"`) inside SUBTYPE_TOOLTIPS values; it does NOT import the underscored constants. The critic's claim of "name leakage" was incorrect. Marked invalidated.

**Deferred (out-of-scope or cosmetic):**
- `adversary LOW-2` (process / diff-size auto-finding): 1018 lines, 471 of which are milestone artifacts; functional ~331 LOC sits squarely in the well-reviewed band. No code action.
- `frontend LOW-1` (QMenu padding tighter than Apple HIG): cosmetic; the 4px padding produces a compact menu density consistent with the rest of the app's chrome (no looser-padding peer to align against). Defer.
- `frontend LOW-3` (init-site spinner comment terse vs comprehensive `_on_theme_changed` comment): the init-site cross-reference is intentional — the comprehensive comment lives where it's most needed (the accumulation rationale only applies on the SECOND+ rebind, not the initial bind). Defer.

**Test count:** 499 pass (was 491 pre-cleanup, +8 in the feat commit, +1 net here: the new `test_border_swatch_dark_export_wired_through_appearance_panel` regression guard; the existing `test_set_default_color_updates_surface_color` shim was extended with `_active_theme` to match the new API).
