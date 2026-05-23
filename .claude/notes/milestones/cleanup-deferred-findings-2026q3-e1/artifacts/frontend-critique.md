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
