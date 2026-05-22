# Adversary critique — dark-mode-2026q2-e1

**Reviewer:** milestone-adversary-critic (read-only)
**Date:** 2026-05-21
**Subject:** dark-mode-2026q2-e1 / commit range `f909093..c76fb28`
**Diff stats:** 735 lines total diff; 4 files changed, 520 insertions, 60 deletions
**Test suite:** 192 passed (was 180; +12 new)

---

## Executive summary

The most severe finding is HIGH H1: the three module-level inline-style constants — `MUTED_TEXT_STYLE`, `VALUE_MONO_STYLE`, and `RANGE_LABEL_STYLE` in `styles.py` — are computed once at import time from `PALETTE_LIGHT` values and applied to individual widgets via `widget.setStyleSheet()` across `appearance_panel.py`, `view_panel.py`, and `parameters_panel.py`. In dark mode, these per-widget calls override the `QApplication`-level dark stylesheet, leaving numeric readouts (`VALUE_MONO_STYLE`: `#333333` on `#252526` = 1.21:1 — near-invisible) and hint text (`MUTED_TEXT_STYLE`: `#5a5a5a` on `#252526` = 2.22:1 — AI-12 fail) in dark-on-dark illegibility. There are two HIGHs (the inline-style problem and the auto-flagged diff-size), two MEDIUMs, and three LOWs. No CRITICALs. All WCAG ratios in `PALETTE_DARK` itself verified independently and correct; the AI-12 gap lives in the layer above — the widget-level style strings the diff did not update. Safe to merge after H1 rectifies; H2 is process-only.

---

## Critical findings

None.

---

## High findings

### HIGH — Inline-style constants hardcode PALETTE_LIGHT colors, overriding dark QSS on ~18 widgets

**Where:** `styles.py:282-288` (constants); `appearance_panel.py:193`, `view_panel.py:84,179,199,201`, `parameters_panel.py:44,55,141,163,166,176` (call sites)
**Evidence:** Three module-level constants are f-strings computed once at import from `PALETTE_LIGHT` values:
- `MUTED_TEXT_STYLE = f"color: {COLOR_MUTED}; ..."` → `color: #5a5a5a`
- `VALUE_MONO_STYLE = f"... color: {COLOR_VALUE};"` → `color: #333333`
- `RANGE_LABEL_STYLE = f"... color: {COLOR_MUTED};"` → `color: #5a5a5a`

In dark mode (`BG_PANEL_DARK = #252526`), each `widget.setStyleSheet(MUTED_TEXT_STYLE)` call overrides the `QApplication`-level dark stylesheet (widget-level rules win over application-level rules in Qt's style cascade). Independently verified contrast: `#333333` on `#252526` = **1.21:1** (`VALUE_MONO_STYLE`), `#5a5a5a` on `#252526` = **2.22:1** (`MUTED_TEXT_STYLE` / `RANGE_LABEL_STYLE`). Both are below the WCAG AA 4.5:1 body-text floor (AI-12). Affected widgets: opacity readout (`appearance_panel.py:193`), domain-radius readout and range min/max (`view_panel.py:179,199,201`), all per-parameter value readouts and range labels (`parameters_panel.py:141,163,166`), hint/empty/description labels (`parameters_panel.py:44,55,176`).

**Why it matters:** The dark mode launch default ships with numerals that are near-invisible (1.21:1 contrast). These are the primary interactive readouts — opacity %, domain radius, and parameter values. Users relying on keyboard navigation or low-vision settings see blank panels where values should appear. This is the exact AI-12 body-text WCAG failure the milestone was commissioned to resolve for dark mode.
**Suggested fix:** Replace the three constants with theme-aware functions (or a theme-resolver pattern analogous to `get_variety_default_colors`) so the call sites pass the active theme and receive the correct text color. Alternative: drop the `color:` from the inline style strings and let `QApplication.setStyleSheet` handle color inheritance for these widgets.

**Regression-guard test:** Add `test_inline_style_text_constants_are_theme_neutral` in `tests/test_styles_palette.py`: assert that `styles.MUTED_TEXT_STYLE`, `styles.VALUE_MONO_STYLE`, and `styles.RANGE_LABEL_STYLE` contain no `color:` property (or, if they must, that the embedded color string passes 4.5:1 against both `BG_PANEL` and `BG_PANEL_DARK`). This catches any future re-introduction of hardcoded text colors in widget-level inline styles.

---

### HIGH — Diff size 735 LOC exceeds the 400-line review-quality threshold

**Where:** no specific file (cross-cutting)
**Evidence:** `git diff f909093..c76fb28 | wc -l` = 735. The Cisco / LinearB defect-detection research used by this pipeline sets 400 LOC as the ceiling above which per-reviewer defect escape rate rises materially.
**Why it matters:** The per-axis checklist mandates an automatic HIGH at > 400 LOC regardless of actual defect density; the finding is process-level, not a code bug. This milestone's 520 net insertions span four files; the full-diff read conducted here took dedicated per-file attention.
**Suggested fix:** For future milestones of comparable scope, consider splitting the QSS refactor (PALETTE_DARK + `_render_stylesheet`) from the app wiring (theme menu + signal management) into separate commits or milestones to keep each reviewable unit under 400 LOC.

---

## Medium findings

### MEDIUM — Inline-style limitation not documented in CONTEXT.md §4.3b or AI-12 guidance

**Where:** `CONTEXT.md:143-160` (§4.3b addition); `.claude/references/app-invariants.md:130-134` (AI-12)
**Evidence:** §4.3b documents the dual-palette pattern, `_render_stylesheet`, and V0 scope exclusions (`QSettings`, persistent theme choice). It does not mention that `MUTED_TEXT_STYLE`, `VALUE_MONO_STYLE`, and `RANGE_LABEL_STYLE` remain PALETTE_LIGHT-sourced and therefore produce illegible text in dark mode — this is a first-class V0 limitation that will confuse the next milestone author working in this area. AI-12 in `app-invariants.md` still describes only the light-palette `#5a5a5a` → `#888` correction; it does not reference BG_PANEL_DARK or the inline-style override hazard.
**Why it matters:** Undocumented V0 scope gaps compound. The next maintainer landing a UPL or appearance fix will see 192 green tests and assume dark mode is complete, missing that the panel readouts are dark-on-dark by design omission rather than by tested choice.
**Suggested fix:** Add a "known limitation" callout to §4.3b listing the three inline-style constants as light-mode-only; add a note to AI-12's implication block stating that `widget.setStyleSheet()` calls with explicit `color:` props bypass the dark QSS cascade and must use theme-aware values.

---

### MEDIUM — No regression guard for inline-style dark contrast failures

**Where:** `tests/test_styles_palette.py:538-736` (new tests)
**Evidence:** The 12 new tests verify `PALETTE_DARK` dict values, `APP_STYLESHEET_DARK` hex provenance, and `VARIETY_DEFAULT_COLOR_DARK` WCAG ratios — all correct and well-structured. However, none tests whether the string values exported as `MUTED_TEXT_STYLE`, `VALUE_MONO_STYLE`, or `RANGE_LABEL_STYLE` contain hardcoded colors that fail against `BG_PANEL_DARK`. The existing `test_critical_text_tokens_meet_wcag_aa_on_bg_panel` (light mode) has no dark twin for inline styles.
**Why it matters:** The current test suite passes 192/192 while the dark-mode numeric readouts are at 1.21:1 contrast. The green suite is misleading: it validates the palette dictionaries but not the widget-level style constants that actually reach the screen.
**Suggested fix:** Add a test asserting either that the inline-style constants contain no `color:` property (preferred, forces inheriting from QSS) or that any embedded color clears 4.5:1 against both `BG_PANEL` and `BG_PANEL_DARK`. A simple `assert "color:" not in styles.VALUE_MONO_STYLE` would have caught H1 immediately.

---

## Low findings

### LOW — `try/except` in `_on_theme_changed` around a disconnect that's already guarded

**Where:** `app.py:552-558`
**Evidence:**
```python
if self._system_theme_connection is not None:
    try:
        style_hints.colorSchemeChanged.disconnect(self._system_theme_connection)
    except (RuntimeError, TypeError):
        pass  # already disconnected; safe to ignore
    self._system_theme_connection = None
```
The `if self._system_theme_connection is not None` outer guard already ensures the connection object exists before entering the block. The `styleHints()` singleton is a global PySide6 object that cannot be destroyed during app lifetime, eliminating the `RuntimeError` path. The `TypeError` path would require passing the wrong type to `disconnect()`, which cannot happen given the stored `QMetaObject.Connection` object. The `try/except` is defensive coding around scenarios that cannot occur.
**Why it matters:** Mild Axis-10 scope-discipline violation: the CONTEXT.md §12 convention explicitly discourages "defensive error handling for scenarios that can't happen". Not a functional bug.
**Suggested fix:** Remove the `try/except`; keep the outer `is not None` guard. If a future PySide6 version changes disconnect semantics, the exception will surface informatively rather than being swallowed silently.

---

### LOW — `closeEvent` does not disconnect `colorSchemeChanged` in "Follow system" mode

**Where:** `app.py:609-611`
**Evidence:** `closeEvent` calls `self.plotter.close()` and `super().closeEvent(event)` but does not disconnect `self._system_theme_connection`. When the user closes the window while in "Follow system" mode, the lambda `lambda s: self._apply_system_theme(s)` (which captures `self`) remains registered against `QGuiApplication.styleHints().colorSchemeChanged` until the process exits. For the current single-window `main()`-loop pattern this is harmless (process exits immediately after `app.exec()` returns). However, the reference keeps the lambda and its `self` reference alive longer than MainWindow's Python lifetime.
**Why it matters:** Not a user-visible bug in the current architecture. Risk surfaces if the app ever gains a headless mode, a test harness that instantiates multiple MainWindow instances, or a session-restore pattern that creates a new window before the old one is fully garbage-collected.
**Suggested fix:** Add a `closeEvent` disconnection: `if self._system_theme_connection is not None: style_hints.colorSchemeChanged.disconnect(self._system_theme_connection)` before the `super().closeEvent(event)` call.

---

### LOW — `test_variety_default_color_dark_wcag_on_bg_viewport` references `PALETTE_LIGHT` for a dark-mode assertion

**Where:** `tests/test_styles_palette.py:671`
**Evidence:** `bg = styles.PALETTE_LIGHT["BG_VIEWPORT"]  # shared between themes`. The comment is correct (both palettes share `BG_VIEWPORT = #2f2f2f`), but a dark-mode test reading from `PALETTE_LIGHT` is confusing. If `BG_VIEWPORT` were ever intentionally diverged between themes (e.g., a slightly lighter dark variant), this test would still pass despite the mismatch.
**Why it matters:** Readability and future-maintainer safety. Not a bug today — the values are identical.
**Suggested fix:** Replace `styles.PALETTE_LIGHT["BG_VIEWPORT"]` with `styles.PALETTE_DARK["BG_VIEWPORT"]` in this test. Add a companion `test_palette_dark_pyvista_bound_tokens_match_light` assertion (which already exists at `styles_palette.py:569`) as the guard against accidental divergence.

---

## What was done well

- **`_render_stylesheet(palette)` template abstraction is architecturally correct.** Extracting the QSS from a module-level f-string into a function parameterized on `palette` is exactly the right design for two-theme support. Single source of truth for the template; both `APP_STYLESHEET` and `APP_STYLESHEET_DARK` rendered at import time so runtime switching is a trivial `setStyleSheet` call with no re-render.

- **WCAG verification is precise and independently confirmed.** Every token in `PALETTE_DARK` carries an inline contrast ratio comment. All ratios independently verified by this reviewer's WCAG 2.x relative-luminance computation: `TEXT_VALUE` 11.60:1 ✓, `TEXT_MUTED` 5.86:1 ✓, `BORDER_DOCK_HEADER` 3.05:1 ✓, `BORDER_GROUP_BOX` 3.42:1 ✓, `FOCUS_RING` 5.17:1 ✓, `BORDER_CAMERA_BTN` 3.72:1 ✓, `BORDER_RESET_BTN` 3.28:1 ✓. Researcher's figures matched to two decimal places.

- **VARIETY_DEFAULT_COLOR_DARK swatch-chip contrast independently confirmed.** All four variety colors clear 3:1 (non-text) and 4.5:1 (text) on `BG_PANEL_DARK`: K3 5.83:1, Enriques 6.76:1, CY3 6.94:1, Fano 7.20:1. The deferred MF1 finding from `variety-palette-2026q2-e1` is genuinely closed by these numbers.

- **Signal management is idiomatically correct for PySide6.** `signal.connect()` returns a `QMetaObject.Connection` object; `signal.disconnect(connection_obj)` is the supported PySide6 idiom. The lazy connect / explicit disconnect on "Follow system" entry/exit prevents the override-conflict described in the research brief. The `_system_theme_connection = None` sentinel correctly tracks disconnected state.

- **`Qt.ColorScheme.Light` is the fully-qualified enum form** (not the deprecated `Qt.Light` alias). The `_on_theme_changed` and `_apply_system_theme` handlers both use `Qt.ColorScheme.Light` correctly, satisfying AI-11 for new code.

- **AI-9 re-entrancy is clean.** `QApplication.setStyleSheet` is synchronous and does not call `processEvents`. Neither `_on_theme_changed` nor `_apply_system_theme` calls `processEvents`, and there is no path from these methods into `_render_current`. The AI-9 guard is untouched and the new code paths are safe from re-entrancy.

- **The `get_variety_default_colors()` default-dark fallback is the correct V0 choice.** Unknown theme names fall through to the dark dict, matching the launch default. The four tests covering the accessor (identity checks via `is`, unknown-name fallback, default-arg default) are comprehensive for a pure-Python pure-data function with no Qt dependencies — a good AI-2-compliant test.

- **Track B rejection is well-justified in the commit message.** The pyqtdarktheme-fork approach would have silently overridden the custom `resetDefaultsBtn` pink and dock-header rules. The commit message calls this out by name, giving the next maintainer a documented reason not to revisit that candidate.

- **`PALETTE_DARK` key-set parity with `PALETTE_LIGHT` is enforced by test.** `test_palette_dark_has_minimum_tokens` fails immediately if a key is added to one palette but not the other, preventing the "template works for light but crashes for dark" failure mode.

---

## Recommended rectification order

1. **Fix H1 (inline-style text constants).** This is the blocking user-visible defect. Drop the `color:` property from `MUTED_TEXT_STYLE`, `VALUE_MONO_STYLE`, and `RANGE_LABEL_STYLE` in `styles.py:282-288` so the `QApplication`-level dark stylesheet controls text color for these widgets (inheriting from `QWidget` color rules set via the QSS). Alternatively, refactor these into a `get_muted_text_style(theme)` callable — but the simpler path (remove the `color:` property and rely on QSS cascade) fixes all 18 affected call sites in one edit. Add the regression guard test from the finding simultaneously.

2. **Address H2 (diff size) as a process note for future milestones.** No code fix required; this is a planning reminder.

3. **Update documentation (M1 + LOW L3 are co-located).** Add the inline-style limitation callout to `CONTEXT.md §4.3b` and update `.claude/references/app-invariants.md` AI-12's implication block to reference `BG_PANEL_DARK` and the widget-level style cascade hazard. Both changes are in documentation only — batch them as one commit.

4. **Add the regression test for M2** (`test_inline_style_text_constants_are_theme_neutral`). Can be done alongside step 1 as part of the same rectification commit.

5. **LOWs at maintainer's discretion:** remove the gratuitous `try/except` (L1), add `closeEvent` disconnect guard (L2), fix the `PALETTE_LIGHT` reference in the dark-mode test (L3). None block merge.

---

*End of critique. Mandatory rectification: H1 (inline-style dark contrast failure). H2 is process-only, non-blocking. M1 and M2 are strongly recommended before milestone close. LOWs are optional.*
