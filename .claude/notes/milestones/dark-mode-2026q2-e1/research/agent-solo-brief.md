# Research Brief — dark-mode-2026q2-e1 (UPL-1 Dark Mode Stylesheet)

**Agent:** solo  
**Date:** 2026-05-22  
**Milestone:** Close UPL-1 — add `PALETTE_DARK` + `APP_STYLESHEET_DARK`, wire Theme menu, apply dark by default.

---

## 1. TL;DR

**Recommended approach:** Refactor `styles.py` to a `_render_stylesheet(palette: dict) -> str` function that renders the QSS template against either palette; add `PALETTE_DARK` as a key-identical companion dict to `PALETTE_LIGHT`; add a Theme menu to `app.py`'s menu bar (newly created) with Light / Dark / Follow-system; apply dark as launch default; extend `tests/test_styles_palette.py` with parallel dark twins.

**Main risk:** The AI-12 re-audit work is real and invisible in the initial M sizing — every text token must be numerically verified against `BG_PANEL_DARK`, not just stated in a comment. The challenger's MAJOR finding specifically called this out: existing test coverage is light-palette-only and must be extended. Skipping or abbreviating the WCAG verification pass will ship an AI-12 violation.

**Backup plan:** If the `_render_stylesheet` refactor hits an unexpected QSS f-string scoping issue, fall back to duplicating the template as `APP_STYLESHEET_DARK` with explicit `PALETTE_DARK[...]` subscripts — higher drift risk but mechanically simpler. Use this only if the function approach breaks.

---

## 2. Prior art in this repo

- `styles.py:54–101` — `PALETTE_LIGHT` dict (18 tokens); the dark parallel must be key-identical.
- `styles.py:145–157` — Explicit `UPL-4 placeholder marker` comment with exact naming convention for `APP_STYLESHEET_DARK` and the `getattr(styles, "APP_STYLESHEET_DARK", None)` detection in `render-panel-chrome.py`.
- `styles.py:226–297` — `APP_STYLESHEET` f-string using `PALETTE_LIGHT[...]` subscripts mixed with named constants. The template must be extracted into `_render_stylesheet(palette)`.
- `styles.py:169–183` — Backward-compat named exports (`COLOR_MUTED`, `BG_VIEWPORT`, etc.) computed from `PALETTE_LIGHT` at module load. After refactor, these remain reading from `PALETTE_LIGHT` only (not the active theme); the theme switch goes through `_render_stylesheet` call, not through named constants.
- `styles.py:62–63` — Explicit comment: `TEXT_MUTED = #5a5a5a` fails 1.94:1 on dark — the comment names `UPL-4` as owner. This is the canonical example of the AI-12 debt.
- `styles.py:104–143` — `VARIETY_DEFAULT_COLOR` dict with Unicode keys. Must be mirrored as `VARIETY_DEFAULT_COLOR_DARK` with identical keys (copy-paste to avoid U+2013/U+03C1 drift — `styles.py:132–133` are the canonical key values).
- `app.py:30–35` — Current imports from styles; `VARIETY_DEFAULT_COLOR` and `BG_SURFACE_DEFAULT` are imported. After this milestone, `APP_STYLESHEET_DARK` and `VARIETY_DEFAULT_COLOR_DARK` will also need importing.
- `app.py:193–201` — `_on_variety_changed` calls `self.appearance_panel.set_default_color(VARIETY_DEFAULT_COLOR.get(name, BG_SURFACE_DEFAULT))`. This call must become theme-aware.
- `app.py:260–262` — `_on_subtype_changed` also calls `set_default_color`. Same theme-awareness update needed.
- `app.py:474–484` — `main()` function: `app.setStyleSheet(APP_STYLESHEET)`. This must become `app.setStyleSheet(APP_STYLESHEET_DARK)` for the dark default. No `QMainWindow` menu bar is currently constructed — must be added.
- `app.py:475` — `QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)` — pre-existing AI-11 violation (unqualified enum); document as out-of-scope pre-existing issue, do not fix in this PR (risk of contaminating scope).
- `appearance_panel.py:323–349` — `set_default_color(hex_str: str)` — current signature. Must become theme-aware (see Pattern A vs B analysis in §4).
- `tests/test_styles_palette.py:26–41` — `_luminance` and `_ratio` helpers already module-level; dark tests reuse them directly.
- `tests/test_styles_palette.py:44–55` — `test_palette_light_has_minimum_tokens` — needs dark twin.
- `tests/test_styles_palette.py:59–70` — `test_every_palette_value_is_six_digit_hex` — needs dark twin.
- `tests/test_styles_palette.py:292–306` — `test_critical_text_tokens_meet_wcag_aa_on_bg_panel` — needs dark twin against `BG_PANEL_DARK`.
- `tests/test_styles_palette.py:190–204` — `test_variety_default_color_wcag_on_bg_viewport` — shared between themes (BG_VIEWPORT is shared); `VARIETY_DEFAULT_COLOR_DARK` reuses same values, test passes unchanged.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Qt 6 QStyleHints docs | https://doc.qt.io/qt-6/qstylehints.html | `colorScheme()` property added Qt 6.5, `colorSchemeChanged` signal, returns `Qt::ColorScheme` enum | Follow-system detection: PySide6 ≥ 6.6 (our pin is `>=6.6`) supports this natively — no `darkdetect` dep needed |
| darkdetect PyPI | https://pypi.org/project/darkdetect/ | BSD-3-Clause, 9 KB wheel, no extra deps, last release Dec 2022 | Fallback option if `QStyleHints.colorScheme()` proves insufficient; license is compatible but adds a dep |
| final-report.md UPL-1 | repo-local | MAJOR from challenger: AI-12 audit invisible in M sizing; Track A endorsed; Track B (pyqtdarktheme-fork) rejected | Confirms Track A, names the invisible sub-task |
| challenge.md UPL-1 | repo-local | "every text token in PALETTE_LIGHT must be re-audited against dark background; existing test_styles_palette.py tests text contrast for light palette only" | Exact scope of the AI-12 sub-task and test extension |
| synthesis.md UPL-1 | repo-local | "render-panel-chrome.py auto-detects `APP_STYLESHEET_DARK` via `getattr(styles, 'APP_STYLESHEET_DARK', None)`" | Naming convention is load-bearing — must honor `APP_STYLESHEET_DARK` exactly |

**Note on arXiv / OSS:** This is a pure stylesheet/wiring milestone with no new mathematical content. arXiv and OSS web searches were skipped per the lessons.md pattern for pure palette/wiring milestones.

---

## 4. Recommended approach

### A. PALETTE_DARK token list

Anchor: `BG_PANEL_DARK = #252526` (VS Code sidebar register — dark but not pitch-black; leaves room for the dock header to differentiate). All ratios computed against `#252526` using the WCAG 2.x relative-luminance formula (identical to the formula in `test_styles_palette.py:26–41`).

**Tokens shared between themes (no `_DARK` variant needed):**

| Token | Value | Note |
|---|---|---|
| `BG_VIEWPORT` | `#2f2f2f` | Canvas always dark — shared; no variant |
| `BG_SURFACE_DEFAULT` | `#b0c4de` | Flows to PyVista; same in both themes |
| `BORDER_SWATCH` | `#888888` | Same in both themes |
| `COLOR_WIREFRAME_OVERLAY` | `#888888` | Same in both themes; 4.32:1 vs `#252526` PASS |

**`PALETTE_DARK` dict (key-identical to `PALETTE_LIGHT`, dark-tuned values):**

| Token | Proposed dark value | WCAG ratio | Threshold | Status | Notes |
|---|---|---|---|---|---|
| `BG_PANEL` | `#252526` | — | anchor | — | Dark panel anchor |
| `TEXT_VALUE` | `#e0e0e0` | 11.60:1 vs BG_PANEL | 4.5:1 text | PASS | Replaces `#333333` |
| `TEXT_MUTED` | `#a0a0a0` | 5.86:1 vs BG_PANEL | 4.5:1 text | PASS | Was 1.94:1 on dark — flagged at `styles.py:62–63` |
| `TEXT_DISABLED` | `#6b6b6b` | 2.87:1 vs BG_PANEL | WCAG disabled exception | exception | Intentionally low per §1.4.3 |
| `TEXT_RESET_BTN` | `#ffc0c0` | 9.32:1 vs `BG_RESET_BTN` dark | 4.5:1 text | PASS | Light pink on dark wine |
| `FOCUS_RING` | `#5b9bd5` | 5.17:1 vs BG_PANEL | 3:1 non-text | PASS | Reuse light value — already dark-compatible |
| `BG_DOCK_HEADER` | `#313132` | structural | — | structural | Title TEXT_VALUE is 9.84:1 vs this |
| `BORDER_DOCK_HEADER` | `#6f6f6f` | 3.05:1 vs BG_PANEL | 3:1 separator | PASS | Separator line between header and content |
| `BORDER_GROUP_BOX` | `#777777` | 3.42:1 vs BG_PANEL | 3:1 non-text | PASS | |
| `BG_SURFACE_DEFAULT` | `#b0c4de` | shared | — | shared | |
| `BORDER_SWATCH` | `#888888` | shared | — | shared | |
| `BG_RESET_BTN` | `#4a1a1a` | structural (dark wine) | — | structural | BORDER carries 3:1 component boundary |
| `BORDER_RESET_BTN` | `#c05050` | 3.28:1 vs BG_PANEL | 3:1 component boundary | PASS | Provides the AI-12-compliant boundary |
| `BG_RESET_BTN_HOVER` | `#5a2020` | structural hover | — | structural | Hover state; rest-state BORDER carries contrast |
| `BG_RESET_BTN_DISABLED` | `#333333` | WCAG disabled exception | — | exception | |
| `BORDER_RESET_BTN_DISABLED` | `#444444` | WCAG disabled exception | — | exception | |
| `BORDER_CAMERA_BTN` | `#6a8090` | 3.72:1 vs BG_PANEL | 3:1 non-text | PASS | |
| `BG_CAMERA_BTN_HOVER` | `#2a3a45` | structural hover | — | structural | |
| `BG_VIEWPORT` | `#2f2f2f` | shared | — | shared | |
| `COLOR_WIREFRAME_OVERLAY` | `#888888` | 4.32:1 vs BG_PANEL | 3:1 non-text | PASS | |

**Implementation note on `BG_DOCK_HEADER`:** In light mode, `#e8edf2` on `#f0f0f0` is 1.03:1 — already below 3:1 (a pre-existing issue that UPL-12 addresses). In dark mode, the dock header is similarly structural: it exists as a labeled region, not as a UI component requiring 3:1 vs the panel. The `BORDER_DOCK_HEADER` line (`#6f6f6f`, 3.05:1) is the structural separator that enables WCAG 1.4.11 compliance for the header region. This matches the light-mode pattern precisely.

**Implementation note on `TEXT_DISABLED`:** `#6b6b6b` at 2.87:1 on `BG_PANEL_DARK` is intentionally below 4.5:1. WCAG 2.1 §1.4.3 explicitly exempts disabled UI state from the minimum contrast requirement. Same design decision as `TEXT_DISABLED = #aaaaaa` in light mode (`styles.py:69`). Do NOT flag this as a bug in the test suite.

### B. APP_STYLESHEET_DARK derivation — approach (i): `_render_stylesheet(palette)` refactor

Extract the f-string template from `styles.py:226–297` into:

```python
def _render_stylesheet(palette: dict[str, str]) -> str:
    return f"""
/* --- Dock widget title bars ... */
QDockWidget {{ font-size: 12px; }}
QDockWidget::title {{
    background: {palette["BG_DOCK_HEADER"]};
    border-bottom: 1px solid {palette["BORDER_DOCK_HEADER"]};
    ...
}}
...
"""
```

Then at module level:

```python
APP_STYLESHEET = _render_stylesheet(PALETTE_LIGHT)
APP_STYLESHEET_DARK = _render_stylesheet(PALETTE_DARK)
```

This is approach (i) from the milestone brief. The `getattr(styles, "APP_STYLESHEET_DARK", None)` detection in `render-panel-chrome.py` (noted at `styles.py:151–157`) requires this module-level constant to exist with exactly this name.

The refactor is mechanical: the f-string becomes a function body; every `PALETTE_LIGHT["TOKEN"]` and `COLOR_*` named constant becomes `palette["TOKEN"]`. Named constants like `COLOR_DOCK_HEADER_BG` used inside the f-string must be inlined as `palette["BG_DOCK_HEADER"]` within the function body (or the function must accept them as local variables). The simplest approach: replace all `palette["TOKEN"]` subscripts consistently throughout the template, using the canonical token keys from `PALETTE_LIGHT`.

**Exact scope:** `styles.py:226–297` becomes the function body. The 8 named constants (`COLOR_DOCK_HEADER_BG`, etc.) used in the existing f-string become `palette["BG_DOCK_HEADER"]` etc. inside the function.

### C. VARIETY_DEFAULT_COLOR_DARK — reuse all four light-mode values

The four light-mode variety colors were verified against both surfaces:

| Variety | Color | vs BG_VIEWPORT (#2f2f2f) | vs BG_PANEL_DARK (#252526) | Swatch 3:1? |
|---|---|---|---|---|
| K3 surface (`#8e9ed4`) | `#8e9ed4` | 5.09:1 PASS | 5.83:1 PASS | YES |
| Enriques surface | `#c4a882` | 5.91:1 PASS | 6.76:1 PASS | YES |
| Calabi–Yau 3-fold | `#85b5d0` | 6.07:1 PASS | 6.94:1 PASS | YES |
| Fano 3-fold (ρ=1) | `#8fbe85` | 6.29:1 PASS | 7.20:1 PASS | YES |

**All four light-mode values clear 3:1 against `BG_PANEL_DARK` for the swatch chip.** `VARIETY_DEFAULT_COLOR_DARK` is identical to `VARIETY_DEFAULT_COLOR` — reuse verbatim. This also closes the deferred MF1 finding from variety-palette-2026q2-e1: the swatch chip contrast is confirmed adequate in dark mode. The Unicode keys (U+2013 en-dash in "Calabi–Yau 3-fold", U+03C1 ρ in "Fano 3-fold (ρ=1)") must be copy-pasted from `styles.py:132–133`, not retyped.

### D. Theme-toggle wiring strategy

**Menu bar attach point:** `app.py` currently has no menu bar. Create one in `MainWindow.__init__` after `self.setStatusBar()` (around `app.py:91`):

```python
# Theme menu — no existing menuBar; create one
theme_menu = self.menuBar().addMenu("Theme")
```

Use `QAction` (import via `from PySide6.QtGui import QAction`) with `setCheckable(True)` and a `QActionGroup` for mutual exclusion. Three actions: "Dark" (default checked), "Light", "Follow system". All enum references must use qualified form (AI-11): `Qt.AlignmentFlag.*`, `QActionGroup`, etc.

**Handler signature:** `_on_theme_changed(self, name: str) -> None`. Store `self._active_theme: str = "dark"` in `__init__`. Handler calls `QApplication.setStyleSheet(APP_STYLESHEET if name == "light" else APP_STYLESHEET_DARK)` — this is synchronous, no `processEvents` needed (AI-9 safe).

**`set_default_color` theme-awareness — Pattern A (recommended):**

Add to `styles.py`:
```python
def get_variety_default_colors(theme: str = "dark") -> dict[str, str]:
    return VARIETY_DEFAULT_COLOR_DARK if theme == "dark" else VARIETY_DEFAULT_COLOR
```

`app.py` calls: `self.appearance_panel.set_default_color(get_variety_default_colors(self._active_theme).get(name, BG_SURFACE_DEFAULT))`. `AppearancePanel.set_default_color` signature stays unchanged — it receives the resolved hex string, not the theme.

**Pattern A vs Pattern B trade-off:** Pattern A keeps `AppearancePanel` decoupled from theme state (it knows nothing about themes; it just receives a hex string). Pattern B (`set_default_color(hex_str, theme_dict=None)`) leaks theme semantics into AppearancePanel and requires the panel to know about the dict structure. Pattern A wins on decoupling. The `get_variety_default_colors()` accessor lives in `styles.py` alongside the dicts — single source of truth.

**System theme detection:** Use `QGuiApplication.styleHints().colorScheme()` (available in Qt 6.5+; our pin is `>=6.6` so it's guaranteed). Returns `Qt.ColorScheme.Dark` or `Qt.ColorScheme.Light`. Connect `QGuiApplication.styleHints().colorSchemeChanged` signal to `_on_theme_changed` when the user selects "Follow system". **No `darkdetect` dependency needed.** Import: `from PySide6.QtGui import QGuiApplication`. Limitation to document: if the user overrides the system theme via the menu (Dark/Light), the `colorSchemeChanged` signal must be disconnected to avoid override conflicts. Re-connect when "Follow system" is re-selected.

**Theme application sequence in `main()`:** Change `app.setStyleSheet(APP_STYLESHEET)` → `app.setStyleSheet(APP_STYLESHEET_DARK)` at `app.py:477`. This sets the launch default to dark.

### E. Test extension plan

**Parallel dark twins (mirror the existing light tests):**

| Existing test | New dark twin |
|---|---|
| `test_palette_light_has_minimum_tokens` | `test_palette_dark_has_minimum_tokens` |
| `test_every_palette_value_is_six_digit_hex` | `test_palette_dark_every_value_is_six_digit_hex` |
| `test_pyvista_bound_tokens_are_present` | `test_palette_dark_pyvista_bound_tokens_are_present` (BG_VIEWPORT, BG_SURFACE_DEFAULT, COLOR_WIREFRAME_OVERLAY are shared — test they match PALETTE_LIGHT values) |
| `test_backward_compat_named_constants_match_palette` | No dark twin — named constants remain light-palette aliases |
| `test_new_named_exports_match_palette` | No dark twin — named exports remain light-palette aliases |
| `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` | `test_app_stylesheet_dark_no_raw_hex` — verify `APP_STYLESHEET_DARK` hex values are all in `PALETTE_DARK` |
| `test_critical_text_tokens_meet_wcag_aa_on_bg_panel` | `test_dark_text_tokens_meet_wcag_aa_on_bg_panel_dark` — `TEXT_VALUE` and `TEXT_MUTED` against `PALETTE_DARK["BG_PANEL"]` |

**New tests for `VARIETY_DEFAULT_COLOR_DARK`:**

- `test_variety_default_color_dark_has_all_four_families` — exact key set match (Unicode safety)
- `test_variety_default_color_dark_all_six_digit_hex` — AI-13 guard
- `test_variety_default_color_dark_wcag_on_bg_viewport` — 4.5:1 against `#2f2f2f` (shared viewport)
- `test_variety_default_color_dark_swatch_chip_vs_bg_panel_dark` — 3:1 against `PALETTE_DARK["BG_PANEL"]` (closes MF1 deferred finding)
- `test_variety_default_color_dark_keys_match_surfaces_varieties` — forward-compat guard

**`set_default_color` test extension:**

The existing `test_set_default_color_updates_surface_color` and `test_set_default_color_ignores_invalid_hex` tests exercise the method signature which stays unchanged (it still receives a hex string). No signature change → no test extension needed for these two. However, add one integration-style test:

- `test_get_variety_default_colors_returns_correct_dict` — calls `styles.get_variety_default_colors("dark")` and `styles.get_variety_default_colors("light")` and asserts the returns are the expected dict objects.

**No new helpers needed.** The existing `_luminance` and `_ratio` module-level helpers are sufficient for all new tests.

### F. CONTEXT.md addition

Insert as **§4.3b** (after §4.3a `AppearancePanel public API` at line 136, before §4.4 `Re-entrancy guard`). Outline:

> **§4.3b Theme system (dark-mode-2026q2-e1, UPL-1)**
>
> The app ships two palettes: `PALETTE_LIGHT` and `PALETTE_DARK` in `styles.py`, each with identical keys. Both render through `_render_stylesheet(palette)` to produce `APP_STYLESHEET` (light) and `APP_STYLESHEET_DARK` (dark). The launch default is dark (`app.setStyleSheet(APP_STYLESHEET_DARK)` in `main()`), because the VTK viewport is always dark (`BG_VIEWPORT = #2f2f2f`) and dark chrome is the coherent baseline.
>
> A Theme menu (Light / Dark / Follow system) in the menu bar calls `_on_theme_changed(name)` which swaps the `QApplication` stylesheet synchronously (no `processEvents` — AI-9 safe). `styles.get_variety_default_colors(theme)` returns the active variety-color dict; app.py calls it on every `_on_variety_changed` / `_on_subtype_changed` to seed `set_default_color`.
>
> Tokens shared between themes: `BG_VIEWPORT`, `BG_SURFACE_DEFAULT`, `BORDER_SWATCH`, `COLOR_WIREFRAME_OVERLAY`. The dark variant re-uses identical values.
>
> V0 scope: no QSettings persistence (that's UPL-25). Theme choice resets to dark on every launch.

---

## 5. Alternatives considered

- **Track B: pyqtdarktheme-fork.** Rejected per challenger MAJOR finding: override-on-top maintenance risk where any fork update could silently override `resetDefaultsBtn` pink and dock header custom QSS. Track A (build-ourselves) endorsed by the challenger explicitly.
- **Duplicate the f-string as `APP_STYLESHEET_DARK`.** Rejected: any future template change must be mirrored to the dark copy. Approach (i) `_render_stylesheet(palette)` has zero drift risk.
- **darkdetect dependency for Follow-system.** Rejected: `QGuiApplication.styleHints().colorScheme()` (available Qt 6.5+, our pin `>=6.6`) provides native system-theme detection with a `colorSchemeChanged` signal. `darkdetect` adds a dep and offers no signal (polling only). Pure-Qt native approach wins.
- **Pattern B for set_default_color (pass theme_dict to the method).** Rejected: leaks theme semantics into AppearancePanel, breaking its clean decoupling. Pattern A (`styles.get_variety_default_colors(theme)` at the call site in `app.py`) keeps AppearancePanel oblivious to theme state.
- **PALETTE_DARK_OVERRIDES (merge dict) instead of key-identical parallel dict.** Rejected: the milestone brief explicitly requires key-identical structure, and `render-panel-chrome.py`'s `getattr(styles, "APP_STYLESHEET_DARK", None)` detection requires the full standalone constant.
- **Lighter `BG_PANEL_DARK` (e.g., `#3c3f41` IntelliJ-style).** Rejected: at `#3c3f41` the BG_VIEWPORT (#2f2f2f) is only 1.17:1 vs the panel — the hard-edge problem would persist for the viewport boundary. `#252526` gives 1.18:1 viewport-to-panel (same order), but the overall dark register is more coherent since both are very dark. The Quanta/3Blue1Brown dark-panel reference (`#1e1e1e`–`#252526` range) confirms this is the correct dark register.

---

## 6. Risks and unknowns

**AI-12 (WCAG text contrast re-audit):** Every text token must be numerically verified against `BG_PANEL_DARK`. The computations in this brief show all text tokens pass. Implementer must run the dark WCAG tests before committing — this is the invisible sub-task the challenger called out.

**AI-9 (re-entrancy):** `QApplication.setStyleSheet()` is synchronous and does not call `processEvents`. Theme swap is safe. The `colorSchemeChanged` signal from `QStyleHints` fires on the GUI thread outside any render call — also safe. No re-entrancy risk.

**AI-11 (qualified Qt enums):** Any new menu / `QAction` / `QActionGroup` code must use fully qualified enums: `Qt.AlignmentFlag.*`, `Qt.ColorScheme.Dark`, `Qt.ColorScheme.Light`, etc. Import `QAction` from `PySide6.QtGui`, not from `PySide6.QtWidgets` (deprecated in Qt 6). Import `QActionGroup` from `PySide6.QtGui`.

**AI-13 (6-digit hex):** All 19 tokens in `PALETTE_DARK` are 6-digit — verified computationally. The test `test_palette_dark_every_value_is_six_digit_hex` will guard this at runtime.

**TEXT_DISABLED_DARK potential confusion:** `#6b6b6b` at 2.87:1 on `BG_PANEL_DARK` is intentionally below the 4.5:1 threshold. Document in the dict comment (same as `styles.py:69`) that WCAG §1.4.3 disabled exception applies. Do NOT write a dark-WCAG test for this token.

**BG_DOCK_HEADER structural contrast:** `#313132` on `#252526` is 1.18:1 — below 3:1. This is intentional and mirrors the light-mode pattern (`#e8edf2` on `#f0f0f0` is 1.03:1). The `BORDER_DOCK_HEADER` separator line (`#6f6f6f`, 3.05:1) is the WCAG-compliant boundary. Do not write a test asserting 3:1 for `BG_DOCK_HEADER` vs panel — that would be a false failure.

**QStyleHints.colorScheme() on macOS:** Available Qt 6.5+. On macOS, it reads the system appearance setting and emits `colorSchemeChanged` when the user changes it in System Settings. No polling required. The `follow_system` path should connect this signal to `_on_theme_changed`. Limitation: if the user has a custom macOS appearance that Qt doesn't map cleanly to Light/Dark (e.g., high-contrast mode), `Qt.ColorScheme.Unknown` may be returned — document this as a V0 limitation and treat Unknown as Dark.

**Render-panel-chrome.py compatibility:** The `styles.py:151–157` comment explicitly states that `render-panel-chrome.py` auto-detects `APP_STYLESHEET_DARK` via `getattr(styles, "APP_STYLESHEET_DARK", None)`. The naming convention is load-bearing. Do NOT name it `DARK_STYLESHEET`, `STYLESHEET_DARK_MODE`, or anything other than `APP_STYLESHEET_DARK`.

**Import chain:** `app.py` will need to add `APP_STYLESHEET_DARK`, `VARIETY_DEFAULT_COLOR_DARK`, and `get_variety_default_colors` to its import from `styles`. The current import block is at `app.py:30–35`.

---

## 7. AI-15 disclaimers

This milestone introduces no new varieties or mathematical figures. AI-15 is not applicable. No tooltip disclaimers needed.

---

## 8. Estimated LOC

| File | LOC estimate | Nature |
|---|---|---|
| `styles.py` | ~75 LOC | `PALETTE_DARK` dict (~20 LOC) + `VARIETY_DEFAULT_COLOR_DARK` dict (~7 LOC) + `_render_stylesheet()` extraction from f-string (~10 LOC refactor) + `get_variety_default_colors()` function (~5 LOC) + module-level constant assignments + comments (~33 LOC) |
| `app.py` | ~55 LOC | Menu bar + `QAction` imports + Theme menu + `_on_theme_changed()` (~20 LOC) + `_active_theme` state + `_on_variety_changed`/`_on_subtype_changed` update + `main()` default + Follow-system `colorSchemeChanged` wiring (~35 LOC) |
| `appearance_panel.py` | ~5 LOC | `set_default_color` signature stays unchanged; no code change needed. Any theme-awareness is handled by the caller (app.py via `get_variety_default_colors`). `appearance_panel.py` imports no new symbols from `styles`. |
| `tests/test_styles_palette.py` | ~110 LOC | 7 dark twins + 5 VARIETY_DEFAULT_COLOR_DARK tests + 1 `get_variety_default_colors` test + comments |
| `CONTEXT.md` | ~25 LOC | §4.3b prose block |

**Total: ~270 LOC across 5 files.** This is within the inline path threshold (≤500 LOC, ≤5 files). The challenger's "M is correct only if AI-12 audit + test extension is properly accounted for" caveat is satisfied by the ~110 LOC test extension being explicitly scoped and priced.

**Files the implementer does NOT touch:** `parameters_panel.py`, `view_panel.py`, `surfaces.py` — zero scope for this milestone.

---

## Open questions for the user

None. The milestone brief is fully specified. All design choices (Track A, dark-as-default, Pattern A for accessor, `_render_stylesheet` refactor, `QStyleHints.colorScheme()` for follow-system) have clear rationale and no credible alternatives left standing. No gate required.
