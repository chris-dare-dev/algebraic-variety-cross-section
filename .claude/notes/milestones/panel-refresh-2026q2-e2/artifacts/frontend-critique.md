# Frontend UX Critique — panel-refresh-2026q2-e2 (UPL-1 palette tokenization)

**Milestone:** panel-refresh-2026q2-e2
**Commit range:** dc328d7..be2b2b9
**Critic agent:** milestone-frontend-ux-critic
**Date:** 2026-05-20
**Files in diff:** `styles.py`, `appearance_panel.py`, `app.py`, `tests/test_styles_palette.py` (new)

---

## Executive Summary

This diff is a foundational palette tokenization refactor (UPL-1). It introduces `PALETTE_LIGHT` as the single source of truth, adds backward-compat named exports, converts `appearance_panel.py` and `app.py` to use tokens instead of inline literals, and ships an 8-test regression suite. The refactor is structurally clean and the test suite passes (173/173).

Two residual inline hex literals were found in `app.py` — the "empty-clip" code path at line 364 was not updated and still uses the raw `"#888888"` string even though `COLOR_WIREFRAME_OVERLAY` was imported and is used in the adjacent normal-render path. This is a token-discipline inconsistency that breaks the exhaustive-tokenization invariant the refactor sets up for UPL-4 and UPL-5.

One MEDIUM finding: two palette comment annotations overstate / understate contrast ratios vs the measured values, which will mislead UPL-4 dark-mode authors who rely on those annotations to select dark-surface text colors.

One LOW finding: `FOCUS_RING` token's palette comment says ">= 3:1 vs adjacent widget bg" but the actual ratio against `BG_PANEL` is 2.60:1 — below the WCAG AA non-text threshold. Not a regression (the token pre-existed the refactor), but now that the token is in the documented palette it deserves an accurate annotation.

Axes 1-6, 8 (AI-13), 9 (AI-11), 10 (AI-9), 11 (keyboard shortcuts) are clean.

---

## CRITICAL findings

None.

---

## HIGH findings

### HIGH — Residual raw `"#888888"` in empty-clip branch bypasses `COLOR_WIREFRAME_OVERLAY` token

**Where:** `app.py:364`
**Evidence:** The diff correctly replaces the wireframe color in the normal-render path (line 386: `color=COLOR_WIREFRAME_OVERLAY`). The empty-clip branch at line 361-369 handles the case where `clipped.n_points == 0` and still shows the domain outline. This branch was not updated: it retains `color="#888888"` as a raw string literal flowing directly into `plotter.add_mesh(color=...)`. The imported `COLOR_WIREFRAME_OVERLAY` token is not used here. Both paths render the same wireframe overlay actor but only one uses the token, creating a two-source-of-truth situation for the same visual element. If UPL-4 swaps `PALETTE_LIGHT["COLOR_WIREFRAME_OVERLAY"]` to a lighter value for dark mode, the empty-clip path will show the wrong color.
**Why it matters:** The entire purpose of UPL-1 is to make `PALETTE_LIGHT` the exhaustive single source of truth so that UPL-4 dark mode swap works by editing only `styles.py`. A surviving inline literal in a PyVista-bound call site breaks that contract. It is also an AI-13 adjacency issue: `#888888` is a 6-digit hex (technically compliant), but its presence as a raw string outside the palette undermines the token discipline.
**Suggested fix:** Replace `color="#888888"` at `app.py:364` with `color=COLOR_WIREFRAME_OVERLAY` — identical to the fix already applied at `app.py:386`.

---

## MEDIUM findings

### MEDIUM — Two palette comment contrast ratios are inaccurate

**Where:** `styles.py:57, 60`
**Evidence:** The palette comments annotate:
- `TEXT_MUTED` (`#5a5a5a`): "~5.4:1 on BG_PANEL" — measured value is **6.05:1**
- `TEXT_RESET_BTN` (`#5a3a3a` on `#f5e8e8`): "~6.1:1" — measured value is **8.37:1**

These are not rounding errors; they are off by 12% and 37% respectively. The comments were inherited from a prior pass and not re-verified against the new 6-digit palette entries. For `TEXT_RESET_BTN` the discrepancy is large enough that a UPL-4 author choosing a dark-mode equivalent guided by "~6.1:1" would select a color with significant headroom to spare.
**Why it matters:** The palette doc comments are the primary guidance for UPL-4 (dark mode). Incorrect contrast ratios cause future authors to calibrate dark-surface text colors against wrong baseline numbers, potentially producing tokens that "look similar to the 6.1 ratio" but actually fail WCAG AA.
**Suggested fix:** Re-run the WCAG luminance formula (already in `test_styles_palette.py`) for every annotated text token and update comment figures. Accept ~1% tolerance for the "~" prefix.

### MEDIUM — `FOCUS_RING` palette comment claims ">= 3:1 vs adjacent widget bg" but actual ratio is 2.60:1

**Where:** `styles.py:63`
**Evidence:** `PALETTE_LIGHT["FOCUS_RING"]` = `#5b9bd5`. Against `BG_PANEL` (`#f0f0f0`), measured contrast ratio is **2.60:1**, below the WCAG AA 3:1 threshold for non-text UI components (focus indicators). The comment reads: "keyboard focus outline (>=3:1 vs adjacent widget bg)" — this is aspirational, not empirical.
**Why it matters:** This token is now in the documented palette with an incorrect specification. WCAG 2.1 Success Criterion 1.4.11 (Non-text Contrast) requires 3:1 for focus indicators. Any accessibility audit will flag this. Now that UPL-1 has made the palette the single source of truth, the annotation is the spec; it needs to be accurate. Note: this token pre-existed the diff, so this is not a regression introduced by UPL-1, but its inclusion in `PALETTE_LIGHT` with a false claim is a UPL-1 artifact.
**Suggested fix:** Either (a) darken `FOCUS_RING` to achieve 3:1 (e.g., `#3c82c4` gives ~3.1:1 on `#f0f0f0`) and update the comment, or (b) update the comment to reflect the measured ratio and file a separate UPL issue for the WCAG fix. Option (a) is a one-line palette change; option (b) keeps UPL-1 surface-minimal and flags it for UPL-4's accessibility pass.

### MEDIUM — `PALETTE_LIGHT` lacks a token for `QSS` status-bar text color; `APP_STYLESHEET` references `COLOR_MUTED` (an alias), not the palette key directly

**Where:** `styles.py:232-234` (status bar QSS rule)
**Evidence:** The `APP_STYLESHEET` status-bar rule uses `{COLOR_MUTED}` (the backward-compat alias). Every other QSS rule in the updated stylesheet was migrated to use `PALETTE_LIGHT[...]` subscripts directly. The status bar rule was not. This is inconsistent with the "no raw literals in APP_STYLESHEET" invariant the test `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` guards. The test passes because `COLOR_MUTED == PALETTE_LIGHT["TEXT_MUTED"]` — the value is the same — but the authoring pattern is inconsistent.
**Why it matters:** In UPL-4, if dark mode requires `TEXT_MUTED_DARK` for the status bar specifically, the author must remember to patch this rule separately because it references the alias rather than a key lookup. The other rules read `PALETTE_LIGHT["KEY"]` and will be trivially found by a sed/grep sweep. This one requires reading the backward-compat section too.
**Suggested fix:** Replace `{COLOR_MUTED}` with `{PALETTE_LIGHT["TEXT_MUTED"]}` in the status bar QSS rule to make all QSS palette references stylistically uniform.

---

## LOW findings

### LOW — `VARIETY_DEFAULT_COLOR` stub docstring lists a non-matching key for Calabi-Yau 3-fold

**Where:** `styles.py:90-94`
**Evidence:** The `VARIETY_DEFAULT_COLOR` docstring example comment lists `"Calabi-Yau 3-fold"` (ASCII hyphen) as a sample key, but `surfaces.py`'s `VARIETIES` dict uses `"Calabi–3-fold"` (Unicode en-dash, U+2013). If UPL-5 follows the stub comment verbatim, the dict lookup will silently miss and the per-variety default will not apply.
**Why it matters:** Low impact now (the dict is empty), but the wrong key in the comment seeds a copy-paste bug in UPL-5.
**Suggested fix:** Update the comment to use the en-dash form `"Calabi–3-fold"` or note that keys must match `VARIETIES` dict verbatim.

### LOW — `BG_PANEL` token is present in `PALETTE_LIGHT` but has no named export and no QSS usage

**Where:** `styles.py:52`
**Evidence:** `PALETTE_LIGHT["BG_PANEL"]` (`#f0f0f0`) is the WCAG contrast anchor documented in all text-token comments, and is referenced by the test suite. However it is not exported as a named constant and does not appear in `APP_STYLESHEET`. It is the implicit panel ground color Qt inherits from the OS theme — but it is not set explicitly anywhere in the app. If Qt's default changes on a future platform, the token will diverge from reality without any test catching it.
**Why it matters:** Cosmetically low risk on today's Qt default, but when UPL-4 adds an explicit dark-panel background, the symmetric light-panel token should also be wired (or documented as "OS-provided, not set explicitly").
**Suggested fix:** Add a brief comment to the `BG_PANEL` entry: "Qt platform default — not set explicitly by the app; update if a future Qt platform skin changes this." No code change required.

---

## What was done well

- **Exhaustive 6-digit hex discipline (AI-13):** Every value in `PALETTE_LIGHT` is 6-digit hex. The test `test_every_palette_value_is_six_digit_hex` is a strong regression guard. The `BORDER_SWATCH` fix (`#888` → `#888888` in `_apply_swatch_color`) is applied correctly at `appearance_panel.py:53`.
- **Backward-compat exports are live aliases, not copies:** The pattern `COLOR_MUTED = PALETTE_LIGHT["TEXT_MUTED"]` (and all analogous exports) ensures that changing the palette dict automatically propagates to all existing call sites. The test suite verifies this at import time.
- **UPL-4 readiness of key vocabulary:** The token names (`BG_VIEWPORT`, `BG_PANEL`, `BG_SURFACE_DEFAULT`, `TEXT_MUTED`, `TEXT_VALUE`, `TEXT_DISABLED`, `FOCUS_RING`) are semantically role-based rather than value-based, which is exactly the vocabulary a dark-mode swap needs. Adding `PALETTE_DARK` with identical keys will be a clean parallel addition.
- **PyVista-bound token annotation:** `BG_VIEWPORT`, `BG_SURFACE_DEFAULT`, and `COLOR_WIREFRAME_OVERLAY` are explicitly flagged "flows into PyVista" in the palette comments. This is the correct way to document the AI-13 risk surface for future contributors.
- **Zero regression in rendered colors or dock sizes:** The pre- and post-refactor color values for every token match the prior inline literals (`#b0c4de`, `#2f2f2f`, `#888888`, `#5a5a5a`, `#333333`, `#e8edf2`, `#c5cdd8`, `#f5e8e8`, `#d4b4b4`, `#f0d0d0`). The off-screen render at `/tmp/check-e2-palette.png` confirms `BG_VIEWPORT` and `BG_SURFACE_DEFAULT` are preserved.
- **First-launch behavior preserved (CONTEXT.md §9.3):** The refactor touches no render-trigger paths. `MainWindow.__init__` still opens to the `-- Select --` placeholder. No auto-render was introduced.
- **No AI-9, AI-10, AI-11 regressions:** No new `processEvents()` calls. No mesh regeneration on domain changes. No shorthand Qt enum forms (`Qt.AlignLeft` etc.) appear in the changed files.
- **Keyboard shortcuts (`Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D`) untouched:** The refactor is stylesheet-only; no action wiring was changed.

---

## Recommended rectification order

1. **(HIGH — must fix before UPL-4)** `app.py:364`: replace `color="#888888"` with `color=COLOR_WIREFRAME_OVERLAY`. One-line fix; eliminates the only remaining PyVista-bound inline literal.
2. **(MEDIUM)** `styles.py:57,60`: update palette comment contrast ratios to measured values (`6.05:1` for `TEXT_MUTED`, `8.37:1` for `TEXT_RESET_BTN`).
3. **(MEDIUM)** `styles.py:63`: either darken `FOCUS_RING` to achieve 3:1 or correct the comment. Flag as a UPL-4 candidate if color change is deferred.
4. **(MEDIUM)** `styles.py:232-234`: replace `{COLOR_MUTED}` alias reference in status-bar QSS with `{PALETTE_LIGHT["TEXT_MUTED"]}` for authoring consistency.
5. **(LOW)** `styles.py:92`: correct `"Calabi-Yau 3-fold"` to `"Calabi–3-fold"` in the `VARIETY_DEFAULT_COLOR` docstring comment.
6. **(LOW)** `styles.py:52`: add "OS-provided, not set explicitly" note to `BG_PANEL` comment.
