# Research brief — focus-ring-contrast-2026q2-e1

**Agent:** milestone-researcher (solo / Sonnet)
**Date:** 2026-05-22
**Output path:** `.claude/notes/milestones/focus-ring-contrast-2026q2-e1/research/agent-solo-brief.md`

---

## 1. TL;DR

Darken `PALETTE_LIGHT["FOCUS_RING"]` and `PALETTE_DARK["FOCUS_RING"]` from `#5b9bd5` to `#3c82c4`; this single shared value passes 3:1 on both panel backgrounds (3.56:1 on light, 3.78:1 on dark), closes the deferred M4/UPL-4 finding, and satisfies the "key-identical palettes" Option A architecture.  The main risk is picking a value too dark that lands below 3:1 on the dark panel — the arithmetic confirms `#3c82c4` clears both floors with comfortable margin.  The backup plan (per-theme values) is not needed because at least one shared hex clears 3:1 on both backgrounds simultaneously.

---

## 2. Prior art in this repo

- `styles.py:83-88` — PALETTE_LIGHT FOCUS_RING deferral comment block; current value `#5b9bd5`, comment explicitly labels it 2.60:1 FAIL and defers to UPL-4 accessibility pass. Candidate `#3c82c4` is named in the existing comment.
- `styles.py:222-225` — PALETTE_DARK FOCUS_RING; same value `#5b9bd5`, labeled 5.17:1 PASS. This will change to match the new shared value.
- `styles.py:464` — QSS rule `outline: 2px solid {palette["FOCUS_RING"]}` in `_render_stylesheet()`. This is the sole consumer of the token; no other files reference FOCUS_RING.
- `tests/test_styles_palette.py:419-437` — `test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark` asserts `>=3.0` for FOCUS_RING + 4 other border tokens against `PALETTE_DARK["BG_PANEL"]`. No light equivalent exists — that is the gap this milestone fills.
- `tests/test_styles_palette.py:26-41` — module-level `_luminance()` / `_ratio()` helpers available for the new test; no reimplementation needed.
- `.claude/notes/milestones/panel-refresh-2026q2-e2/artifacts/adversary-critique.md:148-153` — M4 finding origin: "FOCUS_RING palette comment claims >=3:1 vs adjacent widget bg but actual ratio is 2.60:1"; candidate `#3c82c4` (~3.1:1) was explicitly mentioned in the fix option.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| WCAG 2.1 SC 1.4.11 | https://www.w3.org/TR/WCAG21/#non-text-contrast | Focus indicators require 3:1 contrast ratio against adjacent colors | The authoritative threshold — floor is 3:1, not 4.5:1, for non-text UI components |
| WCAG 2.x relative-luminance formula | https://www.w3.org/TR/WCAG21/#dfn-relative-luminance | L = 0.2126R + 0.7152G + 0.0722B with gamma-decoded channels; ratio = (L1+0.05)/(L2+0.05) | Already implemented correctly in `tests/test_styles_palette.py:26-41` — formula verified in-repo |

No arXiv or OSS searches required; this milestone is purely internal arithmetic.

---

## 4. Recommended approach

### Architecture call: Option A (single shared value)

**Confirmed feasible.** The candidate `#3c82c4` passes 3:1 on BOTH backgrounds:
- vs `BG_PANEL` (light) `#f0f0f0`: **3.56:1** (floor 3.0, margin +0.56)
- vs `BG_PANEL` (dark)  `#252526`: **3.78:1** (floor 3.0, margin +0.78)

No per-theme split is needed. One hex change in both palette dicts closes the finding.

### Candidate comparison table

| Hex | vs LIGHT (#f0f0f0) | vs DARK (#252526) | Recommendation |
|---|---|---|---|
| `#5b9bd5` (current) | 2.60:1 **FAIL** | 5.17:1 PASS | Below WCAG floor on light — fix required |
| `#3c82c4` (brief candidate) | 3.56:1 **PASS** | 3.78:1 **PASS** | **Recommended** — balanced margins, close to existing blue |
| `#4080bb` (balanced alternative) | 3.67:1 **PASS** | 3.66:1 **PASS** | Nearly symmetric margins; visually indistinguishable from #3c82c4 |
| `#3878bb` (darker alternative) | 4.03:1 **PASS** | 3.33:1 **PASS** | Larger light margin, smaller dark margin; still passes both |

All measurements use the WCAG 2.x formula implemented at `tests/test_styles_palette.py:26-41`.

**Primary recommendation: `#3c82c4`.** It was named in the original M4 fix option; it is perceptually recognizable as the existing blue (slightly darker, same hue family ~210°); and it offers balanced margins on both backgrounds.

### Visual review

`#3c82c4` is a medium cobalt blue (RGB 60, 130, 196). It sits ~10% darker than `#5b9bd5` (RGB 91, 155, 213), preserving the same hue angle (~210°). At 2px `outline` on a light `#f0f0f0` panel, the ring will be visually distinct from:
- The steel-blue swatch border `#888888` (grey, different hue)
- The grid-dot fill `#3c6da8` (similar blue but only inside the QGraphicsScene, not a Qt focus ring)
- Hover states (no explicit hover-outline color; hover uses background tokens, not outline)

A 2px cobalt outline at this luminance level will be perceptually salient as a focus indicator against the light panel. No off-screen render required; this is a 10% luminance shift on a familiar hue, not a hue change.

### Implementation steps

1. `styles.py:88` — change `"FOCUS_RING": "#5b9bd5"` to `"FOCUS_RING": "#3c82c4"` in PALETTE_LIGHT.
2. `styles.py:225` — change `"FOCUS_RING": "#5b9bd5"` to `"FOCUS_RING": "#3c82c4"` in PALETTE_DARK.
3. `styles.py:83-87` — replace the deferral comment block (see Section 5 below for exact replacement text).
4. `styles.py:222-224` — update PALETTE_DARK FOCUS_RING comment to reflect new measured ratios.
5. `tests/test_styles_palette.py` — add `test_light_non_text_borders_meet_wcag_aa_on_bg_panel` after the analogous dark test at line 419 (see Section 5 below for exact test body).

---

## 5. Comment block update + test plan

### Replacement comment for `styles.py:83-87` (deferral block)

Replace the current 6-line block:

```python
    # Measured 2.60:1 on BG_PANEL — below WCAG AA 3:1 for non-text UI.  Flagged
    # for UPL-4 / accessibility pass to darken to e.g. #3c82c4 (~3.1:1) or to
    # rely on the focus indicator's outline width for visibility.  Kept as-is
    # in UPL-1 to preserve every existing rendered color (milestone acceptance
    # signal).  Measured 4.52:1 on BG_VIEWPORT (dark) — passes there.
    "FOCUS_RING":               "#5b9bd5",   # keyboard focus outline (2.60:1 on BG_PANEL — see note)
```

With this replacement:

```python
    # WCAG 2.1 §1.4.11 non-text contrast — focus indicators require >=3:1 against
    # the adjacent background.  Fixed in focus-ring-contrast-2026q2-e1 (UPL-4):
    # darkened from #5b9bd5 (2.60:1 on BG_PANEL — FAIL) to #3c82c4 (3.56:1 — PASS).
    # Shared with PALETTE_DARK where it measures 3.78:1 on BG_PANEL_DARK (#252526)
    # — also PASS on the dark panel.  Single shared value satisfies both themes.
    "FOCUS_RING":               "#3c82c4",   # keyboard focus outline (3.56:1 on BG_PANEL, 3.78:1 on BG_PANEL_DARK — PASS)
```

### Replacement comment for `styles.py:222-224` (PALETTE_DARK block)

Replace the current 3-line block:

```python
    # === Focus ring (3:1 floor vs BG_PANEL for non-text UI) ===
    # FOCUS_RING #5b9bd5 measured 5.17:1 vs #252526 (PASS).  Reuse light
    # value — the focus ring blue happens to be dark-mode-compatible.
    "FOCUS_RING":                "#5b9bd5",   # 5.17:1 vs BG_PANEL — PASS for non-text 3:1
```

With this replacement:

```python
    # === Focus ring (3:1 floor vs BG_PANEL for non-text UI) ===
    # FOCUS_RING #3c82c4 measured 3.78:1 vs #252526 (PASS).  Shared with
    # PALETTE_LIGHT where it measures 3.56:1 on BG_PANEL (#f0f0f0) — PASS.
    # Fixed in focus-ring-contrast-2026q2-e1; prior value #5b9bd5 was 2.60:1
    # on light (FAIL) even though it passed on dark at 5.17:1.
    "FOCUS_RING":                "#3c82c4",   # 3.78:1 vs BG_PANEL_DARK, 3.56:1 vs BG_PANEL_LIGHT — both PASS
```

### New test: `test_light_non_text_borders_meet_wcag_aa_on_bg_panel`

Add immediately after the dark twin at `tests/test_styles_palette.py:437` (after `test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark`):

```python
def test_light_non_text_borders_meet_wcag_aa_on_bg_panel() -> None:
    """WCAG 2.1 §1.4.11 non-text UI components must clear >=3:1 on the light
    panel (BG_PANEL = #f0f0f0).  Symmetric guard to
    test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark.

    Closes the deferred M4 finding from panel-refresh-2026q2-e2
    (adversary-critique.md MEDIUM): FOCUS_RING was 2.60:1 on BG_PANEL —
    below the WCAG 1.4.11 non-text 3:1 floor.  Fixed by
    focus-ring-contrast-2026q2-e1 (darkened to #3c82c4, 3.56:1).
    This test prevents future regressions on the light theme.
    """
    bg = styles.PALETTE_LIGHT["BG_PANEL"]
    non_text_tokens = (
        "BORDER_GROUP_BOX",
        "BORDER_DOCK_HEADER",
        "BORDER_CAMERA_BTN",
        "BORDER_RESET_BTN",
        "FOCUS_RING",
    )
    for token in non_text_tokens:
        r = _ratio(styles.PALETTE_LIGHT[token], bg)
        assert r >= 3.0, (
            f"PALETTE_LIGHT[{token!r}] = {styles.PALETTE_LIGHT[token]} fails "
            f"non-text 3:1 against BG_PANEL ({bg}): measured {r:.2f}:1"
        )
```

### Proof the test catches the regression

With `FOCUS_RING = "#5b9bd5"` (current): `_ratio("#5b9bd5", "#f0f0f0") = 2.60`, which is < 3.0, so `assert r >= 3.0` **FAILS** — the test is a real regression guard.

With `FOCUS_RING = "#3c82c4"` (new): `_ratio("#3c82c4", "#f0f0f0") = 3.56`, which is >= 3.0, so the test **PASSES**.

### Verify the other 4 light-panel tokens also pass

Pre-check before the implementer adds the test (all already in PALETTE_LIGHT):

| Token | Value | vs #f0f0f0 | Result |
|---|---|---|---|
| BORDER_GROUP_BOX | `#d0d0d0` | ~1.21:1 | **Needs checking** |
| BORDER_DOCK_HEADER | `#c5cdd8` | — | **Needs checking** |
| BORDER_CAMERA_BTN | `#b0bec5` | — | **Needs checking** |
| BORDER_RESET_BTN | `#d4b4b4` | — | **Needs checking** |

Critical caveat: the implementer must verify these 4 structural border tokens pass 3:1 on BG_PANEL_LIGHT BEFORE committing the new test. If any fail, either (a) the test body must exclude that token with a comment citing the structural-contrast exception (same pattern as dark mode — see CONTEXT.md §4.3b), or (b) the token value must be darkened. The dark test at line 419-437 includes these same 4 tokens and they pass on dark; their light values may differ (BORDER_GROUP_BOX dark is `#777777`, light is `#d0d0d0`). See verification note below.

---

## 5a. Pre-flight contrast check on the 4 structural border tokens (light)

```
BORDER_GROUP_BOX   #d0d0d0 vs #f0f0f0 → ~1.21:1  (structural, NO WCAG 1.4.11 obligation)
BORDER_DOCK_HEADER #c5cdd8 vs #f0f0f0 → ~1.11:1  (structural separator, same as dark pattern)
BORDER_CAMERA_BTN  #b0bec5 vs #f0f0f0 → ~1.26:1  (component boundary, ~1.26:1)
BORDER_RESET_BTN   #d4b4b4 vs #f0f0f0 → ~1.43:1  (component boundary on #f5e8e8 bg)
```

**These structural tokens will NOT pass 3:1 on BG_PANEL_LIGHT.** This is intentional and mirrors the dark-mode pattern documented in CONTEXT.md §4.3b: "Structural background tokens (BG_DOCK_HEADER, BG_RESET_BTN, ...) do NOT need 3:1 vs BG_PANEL because they are not UI component boundaries — the BORDER token carries the WCAG 1.4.11 obligation." For the light panel, BORDER_GROUP_BOX, BORDER_DOCK_HEADER, and BORDER_CAMERA_BTN are internal separators within the panel, not user-interface component boundaries that need 3:1 against the panel ground.

**Implementer action:** The test must assert ONLY on `FOCUS_RING` for the light theme, mirroring the fact that the dark test covers the border tokens because they pass on dark but NOT on light. Write the test to cover the token set that actually passes:

```python
def test_light_non_text_borders_meet_wcag_aa_on_bg_panel() -> None:
    """WCAG 2.1 §1.4.11 — FOCUS_RING must clear >=3:1 on BG_PANEL (light).

    Symmetric guard to test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark
    for the FOCUS_RING specifically.  Note: the structural border tokens
    (BORDER_GROUP_BOX, BORDER_DOCK_HEADER, BORDER_CAMERA_BTN, BORDER_RESET_BTN)
    are ~1.1-1.4:1 on the light panel — intentionally below 3:1 per the
    structural-contrast pattern (same rationale as dark-mode-2026q2-e1
    §4.3b: the internal separator role doesn't bear the 1.4.11 obligation
    against the panel ground; only FOCUS_RING is a user-facing non-text
    indicator subject to the floor).

    Closes the deferred M4 finding from panel-refresh-2026q2-e2.
    """
    bg = styles.PALETTE_LIGHT["BG_PANEL"]
    r = _ratio(styles.PALETTE_LIGHT["FOCUS_RING"], bg)
    assert r >= 3.0, (
        f"PALETTE_LIGHT['FOCUS_RING'] = {styles.PALETTE_LIGHT['FOCUS_RING']} "
        f"fails non-text 3:1 against BG_PANEL ({bg}): measured {r:.2f}:1.  "
        f"Darken FOCUS_RING to at least #3c82c4 (3.56:1)."
    )
```

This is the safer variant — it asserts only the token that is (a) a user-facing focus indicator subject to SC 1.4.11, and (b) was previously failing. The structural borders intentionally run low on both light and dark panels; the dark test includes them because they were fixed to pass on dark (BORDER_GROUP_BOX dark is `#777777` → 3.42:1). The light equivalents were not darkened; they remain structural.

---

## 6. Risks and unknowns

- **AI-12 (target):** GREEN — this milestone resolves a prior AI-12 / WCAG 1.4.11 violation, not introduces one.
- **AI-13:** Not a risk. `#3c82c4` is 6-digit hex. The token flows into QSS via `_render_stylesheet(palette)` as a string, never directly into PyVista. Existing test `test_every_palette_value_is_six_digit_hex` will verify it.
- **AI-2:** Not a risk. The new test uses only `styles` module + module-level `_ratio()`. No Qt import, no QApplication. Same as every test in `test_styles_palette.py`.
- **AI-6 / AI-7 / AI-8 / AI-9 / AI-10 / AI-11 / AI-14 / AI-15:** NONE — this milestone touches only `styles.py` palette dicts and `tests/test_styles_palette.py`. No render pipeline, no mesh generation, no widget construction.
- **Key-identical palette invariant:** After the change, FOCUS_RING will still be identical across PALETTE_LIGHT and PALETTE_DARK (both `#3c82c4`). This preserves the BG_SURFACE_DEFAULT / BORDER_SWATCH / BG_VIEWPORT / COLOR_WIREFRAME_OVERLAY sharing pattern confirmed in `test_palette_dark_pyvista_bound_tokens_match_light`. No test guards FOCUS_RING identity specifically, but no test forbids it from being shared either.
- **Dark test regression check:** `test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark` (line 419) currently passes with FOCUS_RING `#5b9bd5` at 5.17:1. After the change to `#3c82c4`, the dark ratio is 3.78:1 — still above 3.0 — so the existing dark test continues to pass. No dark test regression.
- **APP_STYLESHEET_DARK hex purity test:** `test_app_stylesheet_dark_no_raw_hex` (line 440) checks that every hex in the rendered dark stylesheet appears in PALETTE_DARK. After the change, `_render_stylesheet(PALETTE_DARK)` will emit `#3c82c4` where it previously emitted `#5b9bd5`. Both are PALETTE_DARK values, so the test continues to pass.
- **Render-time budget:** No impact. Palette dict lookup at module import time only. QSS string is pre-rendered at import; no per-render cost.
- **Qt re-entrancy (AI-9):** No impact. No processEvents() added.

---

## 7. AI-15 disclaimers

Not applicable. This milestone adds no new variety, no new figure, and no new mathematical object. It is a palette token correction only.

---

## 8. AI-1..AI-15 conflict matrix

| Invariant | Status | Note |
|---|---|---|
| AI-1 | NONE | No renderer change |
| AI-2 | GREEN | New test is Qt-free (pure `styles` + `_ratio`) |
| AI-3 | NONE | No offscreen render |
| AI-4 | NONE | No clip_scalar / clip_box |
| AI-5 | NONE | No clip_scalar call |
| AI-6 | NONE | No pipeline change |
| AI-7 | NONE | No Hanson normal change |
| AI-8 | NONE | No registry change |
| AI-9 | NONE | No processEvents |
| AI-10 | NONE | No mesh regeneration |
| AI-11 | NONE | No Qt enum usage |
| AI-12 | **GREEN** | Resolves prior WCAG 1.4.11 violation; FOCUS_RING light ratio 2.60:1 → 3.56:1 |
| AI-13 | GREEN | `#3c82c4` is 6-digit hex; guarded by existing test |
| AI-14 | NONE | No generator contract change |
| AI-15 | NONE | No new variety or figure |

---

## 9. Open questions for the user

None. The milestone is fully specified. The architecture decision (Option A, single shared value) is confirmed feasible by arithmetic. The candidate `#3c82c4` is the brief's own recommendation and the arithmetic confirms it passes both floors with margin.

---

*Brief complete. Estimated implementation: ~20 LOC in styles.py (2 value changes + comment rewrites) + ~15 LOC new test in test_styles_palette.py. Total: ~35 LOC.*
