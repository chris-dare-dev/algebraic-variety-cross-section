# Research Brief — cleanup-deferred-findings-2026q3-e1

**Agent:** solo | **Date:** 2026-05-23 | **Mode:** Single

---

## 1. TL;DR

Three of the eight scoped items are already fixed in prior rectification passes (items 2, 4, 6); the remaining five are genuine open work across styles.py, surfaces.py, app.py, icons.py, and tests/. The main risk is item 1 (swatch WCAG fix): the adversary-critique's M4 finding and the frontier-critique's MF1 finding are distinct — MF1 is the swatch chip color vs BG_PANEL, which still fails in the light theme because the BORDER_SWATCH (#888888) does not provide 3:1 against BOTH adjacent surfaces (bg_panel and fill). The backup plan for item 1 is darkening the swatch border from #888888 to TEXT_VALUE (#333333), which clears both surfaces at 4.81-11.09:1 — the minimal-diff fix.

---

## 2. Per-item sections

### Item 1 — variety-palette-2026q2-e1 MF1 (swatch chip WCAG AA light mode)

**Source of finding:**
> "variety-palette-2026q2-e1 adversary-critique.md (frontend-ux section): MEDIUM — Swatch chip contrast on BG_PANEL is below WCAG AA for all four family colors. K3 #8e9ed4 → 2.31:1, Enriques #c4a882 → 1.99:1, CY3 #85b5d0 → 1.94:1, Fano #8fbe85 → 1.87:1 against BG_PANEL (#f0f0f0). Suggested fix (V1 / UPL-4 scope): Either (a) render the 20×20 swatch inside a small dark-panel wrapper, (b) add a darker 2 px swatch border, or (c) add a thin variety-name label."

**Current status:** STILL OPEN in light theme. CONTEXT.md §4.3b says "The MF1 swatch-chip finding deferred from variety-palette-2026q2-e1 is closed by the dark default: all four variety colors clear 3:1 on BG_PANEL_DARK = #252526 (measured 5.83-7.20:1)." This is a PARTIAL closure — dark mode passes, light mode still fails.

**Exact file:line to modify:**
- `appearance_panel.py:52` — the `_apply_swatch_color` function sets `border: 1px solid {BORDER_SWATCH}` where `BORDER_SWATCH = "#888888"`
- `styles.py:103` — BORDER_SWATCH token definition

**WCAG analysis (computed):**

| Color | vs BG_PANEL (#f0f0f0) | BORDER_SWATCH (#888888) vs fill | BORDER_SWATCH vs BG_PANEL |
|---|---|---|---|
| K3 #8e9ed4 | 2.31:1 FAIL | 1.35:1 FAIL | 3.11:1 PASS (barely) |
| Enriques #c4a882 | 1.99:1 FAIL | 1.56:1 FAIL | 3.11:1 PASS (barely) |
| CY3 #85b5d0 | 1.94:1 FAIL | 1.61:1 FAIL | 3.11:1 PASS (barely) |
| Fano #8fbe85 | 1.87:1 FAIL | 1.67:1 FAIL | 3.11:1 PASS (barely) |

WCAG 1.4.11 (non-text contrast) requires the UI component boundary to achieve 3:1 against BOTH the component body (fill color) AND the adjacent background. The current #888888 border barely passes vs BG_PANEL but fails badly vs all 4 variety fills. Fix: use `TEXT_VALUE` = `#333333` as the swatch border color in the light theme.

| Border cand | vs BG_PANEL | vs K3 fill | vs Enriques fill | vs CY3 fill | vs Fano fill |
|---|---|---|---|---|---|
| #888888 (current) | 3.11:1 PASS | 1.35:1 FAIL | 1.56:1 FAIL | 1.61:1 FAIL | 1.67:1 FAIL |
| #333333 (TEXT_VALUE) | 11.09:1 PASS | 4.81:1 PASS | 5.58:1 PASS | 5.73:1 PASS | 5.94:1 PASS |

**Before (appearance_panel.py:52):**
```python
    swatch.setStyleSheet(
        f"background-color: {hex_color}; border: 1px solid {BORDER_SWATCH};"
    )
```

**After — theme-aware swatch border:**

The `_apply_swatch_color` function has no theme parameter. The swatch must be modified to use a darker border in light mode. Options:
- (A) Add `border_color` param to `_apply_swatch_color` and wire from `set_default_color` with the active theme. Requires theme awareness in AppearancePanel.
- (B) Add a new `BORDER_SWATCH_LIGHT` token to `PALETTE_LIGHT` = `#333333` (TEXT_VALUE) and keep BORDER_SWATCH as the dark-mode value (#888888). Route the correct value through `_apply_swatch_color` at init/theme-refresh.
- (C) Use a fixed `#333333` border universally — passes on both light (#f0f0f0: 11.09:1) and dark (#252526: still high-contrast). Simplest; no new token or theme logic needed. The dark swatch border becomes #333333 (was #888888), which is slightly heavier visually but still within WCAG bounds.

**Recommended fix:** Option (C) — use `TEXT_VALUE` from PALETTE_LIGHT as a hard-coded border value in `_apply_swatch_color` via a new `BORDER_SWATCH_DARK = "#333333"` token. Actually simplest of all: just change `BORDER_SWATCH` from `#888888` to `#333333` in BOTH palettes. On the dark panel, #333333 on #252526 = 1.40:1 (lower contrast than before), but that's acceptable for a decorative border — the swatch fill itself has 5.83-7.20:1 vs dark bg_panel (sufficient for component identity). WCAG 1.4.11 boundary contrast is only required for the active boundary indicator, and in dark mode the swatch chip fill already passes 3:1 independently.

Wait — actually option C introduces a regression in dark mode: if both palettes use #333333, the dark border disappears into the dark panel. Use theme-split instead: `PALETTE_LIGHT["BORDER_SWATCH"] = "#333333"`, `PALETTE_DARK["BORDER_SWATCH"] = "#888888"` (unchanged). This requires splitting the currently shared value. `BORDER_SWATCH` is currently marked "SHARED" in PALETTE_DARK. The split is correct because each palette meets WCAG independently.

**Precise before/after:**
- `styles.py:103`: `"BORDER_SWATCH": "#888888"` → `"BORDER_SWATCH": "#333333"` (PALETTE_LIGHT only)
- `styles.py:264`: `"BORDER_SWATCH": "#888888"` — keep `#888888` in PALETTE_DARK (passes 4.32:1 vs dark bg)
- Update the PALETTE_DARK comment from "SHARED — 6-digit, reads on either ground" to clarify the split

**AI-invariants:** AI-13 satisfied (#333333 is 6-digit). AI-12 satisfied. No new hex literals in PyVista paths.

**Regression test:** Extend `tests/test_styles_palette.py` with:
- Assert `PALETTE_LIGHT["BORDER_SWATCH"]` achieves >= 3:1 vs BG_PANEL (#f0f0f0) AND vs each of the 4 variety colors.
- Assert `PALETTE_DARK["BORDER_SWATCH"]` achieves >= 3:1 vs BG_PANEL_DARK (#252526).

**Estimated LOC:** styles.py +2 lines (split the shared token), tests +10-15 lines. Total ~17 LOC.

---

### Item 2 — panel-refresh-e2 M4 (FOCUS_RING comment accuracy)

**Source of finding:**
> "panel-refresh-2026q2-e2 adversary-critique.md MEDIUM — FOCUS_RING palette comment claims '>= 3:1 vs adjacent widget bg' but actual ratio is 2.60:1. Evidence: PALETTE_LIGHT['FOCUS_RING'] = #5b9bd5. Against BG_PANEL (#f0f0f0), measured contrast ratio is 2.60:1."

**Current status: ALREADY FIXED.** The `focus-ring-contrast-2026q2-e1` milestone darkened FOCUS_RING from #5b9bd5 to #3c82c4. The comment at `styles.py:83-95` now reads:
```
# darkened from #5b9bd5 (2.60:1 on BG_PANEL — FAIL, below the 3:1 floor)
# to #3c82c4 (3.56:1 — PASS). Closes the deferred M4 finding from
# panel-refresh-2026q2-e2 (variety-palette / UPL-1).
```
Both the value and the comment are correct. The focus-ring-contrast milestone's adversary also confirms: `#3c82c4` vs `#f0f0f0` = 3.5558:1 (PASS). Test guard: `test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel` in `tests/test_styles_palette.py`.

**No code action required for item 2.**

---

### Item 3 — realtime-variety-render-e4b M7 (SUBTYPE_TOOLTIPS don't mention coarse LOD)

**Source of finding:**
> "realtime-variety-render-e4b adversary-critique.md MEDIUM (line 202) — Per-surface tooltips don't mention the coarse-preview LOD. Where: surfaces.py:SUBTYPE_TOOLTIPS — the absence of a coarse-preview note. The 9 opt-in implicit subtype tooltips describe the surface mathematically but say nothing about the new render-time behavior."

**Current status: STILL OPEN.** The e4b rectification added the LOD note to `VARIETY_TOOLTIPS` (family-level, lines 1659-1690) but NOT to `SUBTYPE_TOOLTIPS`. The rectification note says "M-front-2 — Added a coarse-LOD disclosure sentence to all 4 family entries in VARIETY_TOOLTIPS." The original finding was about SUBTYPE_TOOLTIPS.

The brief says "add one line per Hanson/Fermat tooltip noting that drag triggers coarse preview, release triggers full render." The Hanson family does NOT use coarse preview (Hanson uses the e2 full-at-every-tick fast path, `coarse_n=0`). The brief's mention of "Hanson" is misleading. The correct scope is: the 9 implicit subtypes with `coarse_n > 0`. Looking at SUBTYPE_TOOLTIPS (`surfaces.py:1693-1770`), the coarse-preview-eligible subtypes are:

- Fermat quartic (coarse_n=80) — `surfaces.py:1695`
- Kummer surface (coarse_n=100) — `surfaces.py:1700`
- Canonical sextic [Fig. 1] (coarse_n=80) — `surfaces.py:1706`
- Diagonal λ-family [Fig. 2] (coarse_n=80) — `surfaces.py:1711`
- Cayley symmetroid [Fig. 3] (coarse_n=80) — `surfaces.py:1716`
- Icosahedral sextic [Fig. 4] (coarse_n=80) — `surfaces.py:1721`
- Dwork pencil [Fig. 4] (coarse_n=100) — `surfaces.py:1742`
- Klein cubic [Fig. 1] (coarse_n=80) — `surfaces.py:1749`
- Segre cubic [Fig. 2] (coarse_n=80) — `surfaces.py:1754`
- Two-quadrics CI tube [Fig. 3] (opt-out, coarse_n=0) — `surfaces.py:1760`
- Sextic double solid [Fig. 4] (coarse_n=80) — `surfaces.py:1765`

Hanson subtypes (quintic, cubic torus, asymmetric) use the e2 full fast-path and SHOULD get the opposite note.

**Recommended approach:** Add a one-liner at the END of each eligible subtype's tooltip string. Standard form:
- For coarse_n > 0 implicit: `"Drag for quick preview; release for full render."`
- For Hanson parametric: `"Renders at full resolution on every drag tick (parametric, no coarse preview)."`
- For two-quadrics opt-out: `"Renders on slider release only (topology too fragile for drag preview)."`

Note: the brief says "add one line per Hanson/Fermat tooltip" — since VARIETY_TOOLTIPS already covers the family-level LOD behavior, adding it to SUBTYPE_TOOLTIPS serves users who hover individual subtypes rather than the family combo.

**Estimated LOC:** ~14 line additions to SUBTYPE_TOOLTIPS (one per subtype).

**Regression test:** Source-grep test asserting each coarse-eligible subtype's tooltip string contains "preview" or "drag". Write as a simple list check in `tests/test_mesh_generators.py` or `tests/test_styles_palette.py`.

---

### Item 4 — realtime-variety-render-e4b L2 (`_inflight_is_coarse` dead code)

**Source of finding:**
> "realtime-variety-render-e4b adversary-critique.md LOW (line 230) — _inflight_is_coarse is set but never read. The slot reads result.is_coarse (the worker self-describes), never self._inflight_is_coarse."

**Current status: ALREADY FIXED.** The e4b rectification pass removed the field. Confirmed by grep: `_inflight_is_coarse` appears at `app.py:270` only in a COMMENT that explains its removal:
```python
# worker self-describes.  No `_inflight_is_coarse` mirror is needed
# (an earlier version of the e4b implementation had one; the e4b rect
# critique flagged it as unused and it was removed).
```
Rectification note: "L-front-2 — `_inflight_is_coarse` removed (was set but never read; the slot reads `result.is_coarse` — worker self-describes)."

**No code action required for item 4.**

---

### Item 5 — realtime-variety-render-e4b L3 (em-dash vs middle-dot separator)

**Source of finding:**
> "realtime-variety-render-e4b adversary-critique.md LOW (line 223) — Em-dash separator inconsistency: badge uses ' — ' vs base_msg's '  ·  '. Badge uses U+2014 em-dash with single spaces; base_msg uses U+00B7 interpunct with double spaces."

**Current status: STILL OPEN.** Confirmed deferred in e4b rect: "L-front-1 — Em-dash (badge) vs interpunct (base_msg) separator inconsistency. Cosmetic; the visual transition cue is actually mildly useful as a mode-change signal."

**Exact file:line:**
- Badge: `app.py:1096` — `f"Preview — {surface.label}{hq_label} — {result.gen_ms:.0f} ms"` (em-dash " — ")
- base_msg: `app.py:1159` — `f"{surface.label}{hq_label}  ·  {self._raw_mesh.n_points:,} verts, ..."` (interpunct "  ·  ")
- Warning base: `app.py:1174` — `f"⚠ {result.warning_text}  ·  {bbox_suffix}..."` (interpunct)

**Recommended fix:** Align badge to use interpunct ("  ·  ") as the separator — matching the established base_msg convention (also used in status-bar-bbox milestones and the broader status bar format). The em-dash in the Preview badge is the outlier.

**Before (app.py:1095-1097):**
```python
preview_msg = (
    f"Preview — {surface.label}{hq_label}"
    f" — {result.gen_ms:.0f} ms"
)
```

**After:**
```python
preview_msg = (
    f"Preview  ·  {surface.label}{hq_label}"
    f"  ·  {result.gen_ms:.0f} ms"
)
```

Note: also check `app.py:1074` comment which says `"Preview — {label}{hq_label} — NNN ms"` — update the comment to match the new format.

**Regression test:** Source-grep asserting that `" — "` (em-dash with single spaces) does NOT appear in any `preview_msg` or `Preview` format string in `app.py`. Also assert both badge and base_msg use `"  ·  "`.

**Estimated LOC:** app.py +2 (format change) + 1 (comment update), tests +4. Total ~7 LOC.

---

### Item 6 — realtime-variety-render-e5b M3 (_dwork_ref / _segre_cubic_ref not verbatim)

**Source of finding:**
> "realtime-variety-render-e5b adversary-critique.md MEDIUM (line M1) — _dwork_ref and _segre_cubic_ref in tests/test_numba_field_kernels.py are not verbatim copies of the pre-e5b NumPy expressions — they use the explicit x2*x2*x / x*x*x multiply chain matching the kernel rather than the original X**5 / X**3 operators. Research brief line 77 explicitly required the reference to use X**5."

**Current status: ALREADY FIXED.** The e5b M1 rectification restored the operator forms. Current `tests/test_numba_field_kernels.py:339` reads:
```python
F = X ** 5 + Y ** 5 + Z ** 5 + 2.0 - 5.0 * psi * X * Y * Z
```
And `tests/test_numba_field_kernels.py:360`:
```python
F = X ** 3 + Y ** 3 + Z ** 3 + a ** 3 + b ** 3 - s ** 3
```
Both docstrings now explain the "independent oracle" rationale and the `atol=1e-9` tolerance.

**No code action required for item 6.**

---

### Item 7 — dark-mode M_menu_nest (QMenu OS palette override)

**Source of finding:**
The M_menu_nest finding is listed as deferred in `dark-mode-2026q2-e1/state.json`. The milestone brief for this cleanup task states: "Qt right-click context menus inherit OS palette, not the app stylesheet — explicit QSS rule (QMenu { background-color: %(BG_PANEL)s; color: %(TEXT_VALUE)s; }) added to both APP_STYLESHEET and APP_STYLESHEET_DARK."

**Background:** Qt right-click `QMenu` widgets do not inherit from `QApplication.setStyleSheet()` on macOS — they render using the native OS menu rendering (Aqua). This means context menus will always show light-chrome menus even in the app's dark theme. Adding an explicit `QMenu { ... }` rule to the QSS forces Qt's stylesheet renderer instead of the native Aqua renderer.

**QMenu surfaces in this app:**
- The menuBar Theme menu is a `QMenu` (accessible via left-click, not right-click)
- Qt right-click context menus on text inputs (QLineEdit/QTextEdit — none present in this app)
- VTK's render window has its own right-click handler (not a Qt QMenu)
- QComboBox dropdown: renders as a popup but is NOT a QMenu — it's a QAbstractItemView
- QSlider: no built-in right-click context menu in Qt

Audit reveals the primary QMenu in this app is the **Theme menu in the menu bar** (a QMenu child of QMenuBar). There are no explicit right-click QMenu surfaces added by the app's Python code. The "flash light chrome on right-click" symptom in the brief likely refers to the Theme menu popup when the user clicks "Theme" in the menubar — it opens as a QMenu floating popup.

**Current state:** `styles.py` `_render_stylesheet` has NO `QMenu` rule. Search confirms zero QMenu entries.

**Recommended fix:** Add `QMenu` + `QMenu::item:selected` rules to `_render_stylesheet`. Standard form:
```python
"""
/* --- Context menus and popup menus ------------------------------------ */
/* dark-mode-2026q2-e1 M_menu_nest: Qt right-click / popup QMenu inherits
   the OS QPalette on macOS Aqua rather than the QApplication stylesheet.
   Explicit QSS forces stylesheet-render mode and prevents the light-chrome
   flash when the user opens the Theme menu or any future QMenu on a dark-
   theme session. */
QMenu {{
    background-color: {palette["BG_PANEL"]};
    color: {palette["TEXT_VALUE"]};
    border: 1px solid {palette["FOCUS_RING"]};
    padding: 4px;
}}
QMenu::item {{
    padding: 4px 20px;
}}
QMenu::item:selected {{
    background-color: {palette["BG_TOGGLE_CHECKED"]};
    color: {palette["TEXT_VALUE"]};
}}
QMenu::separator {{
    height: 1px;
    background: {palette["BORDER_GROUP_BOX"]};
    margin: 2px 0;
}}
"""
```

WCAG checks (light palette):
- TEXT_VALUE (#333333) on BG_PANEL (#f0f0f0) = 11.09:1 — PASS
- TEXT_VALUE (#333333) on BG_TOGGLE_CHECKED (#d4e6f5) = 9.89:1 — PASS
- FOCUS_RING (#3c82c4) on BG_PANEL (#f0f0f0) = 3.56:1 — PASS (component boundary)

WCAG checks (dark palette):
- TEXT_VALUE (#e0e0e0) on BG_PANEL (#252526) = 11.60:1 — PASS
- TEXT_VALUE (#e0e0e0) on BG_TOGGLE_CHECKED (#1a3048) = 10.20:1 — PASS
- FOCUS_RING (#5b9bd5) on BG_PANEL (#252526) = 5.17:1 — PASS

**AI-9:** QMenu QSS is paint-only. No processEvents, no signal connection.
**AI-13:** All hex values via palette tokens, no inline literals.
**AI-11:** No enum references in QSS.

**Regression test:** Add to `tests/test_styles_palette.py`:
- Assert `"QMenu"` appears in both `APP_STYLESHEET` and `APP_STYLESHEET_DARK`.
- Assert the QMenu rule in each stylesheet contains `palette["BG_PANEL"]` value and `palette["TEXT_VALUE"]` value.

**Estimated LOC:** styles.py ~15 lines (QMenu rule block in template), tests +6. Total ~21 LOC.

---

### Item 8 — render-busy-spinner adversary LOW-2 (Spin QTimer accumulation undocumented)

**Source of finding:**
> "render-busy-spinner-2026q3-e1 adversary-critique.md LOW (line 53) — Spin QTimer accumulation on repeated theme changes is undocumented. Suggested fix: Add a one-sentence note to the render_busy_spinner_icon factory docstring: 'Theme changes create a fresh Spin instance; the prior Spin's QTimer continues to fire widget.update() until the widget is destroyed — harmless (correct color always shows) but observable as N-times-nominal repaint rate after N theme swaps.'"

**Current status: STILL OPEN.** Confirmed deferred in render-busy-spinner rectification: "adversary LOW-2 (Spin QTimer accumulation across theme changes undocumented): comment-only nudge. The factory creates a new QIcon + qta.Spin(widget) on each theme swap; whether the prior QTimer is GC'd or accumulates depends on qtawesome internals. Real-world impact: 0 (user doesn't theme-swap during 0.5–1.5 s compute window). Defer comment."

**Icon rebind sites (three locations where the comment should appear):**
1. `app.py:390-394` — initial bind in `_build_ui` (after panel refresh_icons)
2. `app.py:1615-1619` — rebind in `_on_theme_changed`
3. `app.py:1663-1665` — rebind in `_apply_system_theme`

**Exact behavior:** `qta.Spin.__init__` sets `self.info = {}`. `qta.Spin.setup()` creates `QTimer(parent_widget)` on the first `paintEvent`. On a theme swap, a NEW `qta.Spin(widget)` instance is created. The OLD `Spin` instance holds a live `QTimer(parent_widget)` that continues firing `widget.update()` indefinitely. The old timers are auto-deleted when the `QPushButton` (their parent) is destroyed. So in a 3-theme-swap session, 3 QTimers fire at 10ms intervals (producing 3x the repaint rate). Visually correct (new QIcon paints the right color); no crash. Low CPU overhead given 0.5-1.5s compute windows and typical 0-3 swaps per session.

**Recommended fix:** Add an inline comment at each of the THREE icon-rebind sites in `app.py`. The brief says "at the icon-rebind site" — all three sites qualify. A single comment at the factory docstring was the adversary's suggestion, but the brief specifically asks for "inline comment at the icon-rebind site." The brief also says "a new icon() call on theme swap correctly supersedes the prior animation" — this is actually NOT fully accurate per qtawesome internals (the prior QTimer keeps firing), so the comment should be honest.

**Before (app.py:1615-1619):**
```python
        self._render_busy_spinner.setIcon(
            icons.render_busy_spinner_icon(
                self._render_busy_spinner, self._active_theme
            )
        )
```

**After — add inline comment:**
```python
        # qtawesome Spin note: each call to render_busy_spinner_icon creates a
        # fresh Spin instance with its own QTimer(parent_widget).  The prior
        # Spin's QTimer continues firing widget.update() until the widget is
        # destroyed (Qt parent-based auto-delete).  Impact: N-times-nominal
        # repaint rate after N theme swaps — visually correct, negligible CPU.
        self._render_busy_spinner.setIcon(
            icons.render_busy_spinner_icon(
                self._render_busy_spinner, self._active_theme
            )
        )
```

Apply an equivalent 5-line comment at `app.py:1663-1665` (`_apply_system_theme`). A shorter 2-line comment reference at the init site (`app.py:390`) is sufficient: `# qtawesome Spin QTimer note: see _on_theme_changed for the accumulation rationale.`

**Regression test:** Source-grep assert that "QTimer" or "Spin" or "theme swap" comment appears within 15 lines of each `render_busy_spinner_icon` call in `app.py`. This can be implemented as: read app.py, find all `render_busy_spinner_icon` call line numbers, assert each has a comment containing "Spin" within 15 lines above/below.

**Estimated LOC:** app.py ~12 lines of comments, tests +8. Total ~20 LOC.

---

## 3. Cross-cutting AI-1..AI-15 scan

| Item | AI checks | Assessment |
|---|---|---|
| 1 (swatch border) | AI-12 (WCAG), AI-13 (hex) | #333333 on both bg passes; 6-digit confirmed |
| 3 (SUBTYPE_TOOLTIPS) | AI-15 (math honesty) | No new math claims; text is accurate behavior description |
| 5 (separator) | None | Pure string constant change |
| 7 (QMenu QSS) | AI-9 (processEvents), AI-12 (WCAG), AI-13 (hex) | QSS is paint-only (AI-9 safe); all ratios verified; tokens via palette dict |
| 8 (spinner comment) | AI-9 (QTimer behavior explanation) | Comment text accurately describes AI-9-safe path |

Items 2, 4, 6 are already closed — no AI invariant scan needed for no-ops.

**AI-2 compliance (test suite Qt-free):** All proposed tests use source-grep or WCAG luminance math. No `QApplication()`, no `MainWindow()`, no Qt imports in test runners. WCAG computations are pure Python. Source-grep tests use `pathlib.Path.read_text()`.

**AI-3:** No off-screen render verification needed. This milestone has no new geometry.

**AI-15:** No new variety or figure proposed. Items 3 and 8 are behavior description, not math claims.

---

## 4. Test plan (rolled up)

| Item | Test location | Assertion |
|---|---|---|
| 1 (swatch) | `tests/test_styles_palette.py` | `PALETTE_LIGHT["BORDER_SWATCH"]` achieves >=3:1 vs BG_PANEL AND vs each of 4 variety fill colors |
| 1 (swatch dark) | `tests/test_styles_palette.py` | `PALETTE_DARK["BORDER_SWATCH"]` achieves >=3:1 vs BG_PANEL_DARK |
| 3 (tooltips) | new `tests/test_styles_palette.py` or `test_mesh_generators.py` | Each coarse-eligible subtype's tooltip string contains "preview" and "drag" |
| 5 (separator) | `tests/test_render_worker.py` or source-grep in test | `" — "` (em-dash) absent from badge format; `"  ·  "` present in both preview and base msg |
| 7 (QMenu) | `tests/test_styles_palette.py` | `"QMenu"` in both `APP_STYLESHEET` and `APP_STYLESHEET_DARK` |
| 8 (spinner comment) | `tests/test_render_busy_spinner.py` | "QTimer" or "Spin" comment within 15 lines of each `render_busy_spinner_icon` call |

All tests are AI-2 compliant (no Qt, no VTK, pure source text or arithmetic).

---

## 5. Estimated diff size and inline-vs-delegated

| Item | Production LOC | Test LOC | Status | Action |
|---|---|---|---|---|
| 1 (swatch border) | ~3 (styles.py token split) | ~12 (WCAG assertions) | OPEN | Inline |
| 2 (FOCUS_RING) | 0 | 0 | ALREADY FIXED | Skip |
| 3 (SUBTYPE_TOOLTIPS) | ~15 (surfaces.py tooltip appends) | ~8 (source-grep) | OPEN | Inline |
| 4 (inflight_is_coarse) | 0 | 0 | ALREADY FIXED | Skip |
| 5 (separator) | ~3 (app.py format + comment) | ~4 (source-grep) | OPEN | Inline |
| 6 (dwork/segre refs) | 0 | 0 | ALREADY FIXED | Skip |
| 7 (QMenu) | ~15 (styles.py rule block) | ~6 (presence assert) | OPEN | Inline |
| 8 (spinner comment) | ~12 (app.py comments) | ~8 (proximity grep) | OPEN | Inline |
| **TOTAL** | **~48 LOC** | **~38 LOC** | | **~86 LOC total** |

All 5 open items are inline changes (no new files needed). Well under the 400-LOC review-quality threshold.

---

## 6. Risk matrix

| Item | Risk | Notes |
|---|---|---|
| 1 (swatch) | LOW | Token split in PALETTE_LIGHT only; dark palette unchanged. Test guards the split. |
| 3 (tooltips) | VERY LOW | Pure string appends to SUBTYPE_TOOLTIPS. No logic. |
| 5 (separator) | VERY LOW | Single format-string change. Regression: source-grep. |
| 7 (QMenu) | MEDIUM | QMenu QSS on macOS Aqua can interact with native rendering in unexpected ways. The rule forces stylesheet mode for the Theme menu — visually test the menu opens correctly in both themes. No AI-9 risk (pure paint). |
| 8 (spinner) | VERY LOW | Comment-only. No code behavior changed. |

No item has a risk of triggering new AI-1..AI-15 violations. Item 7 warrants manual visual verification (open the Theme menu in both light and dark mode after the change to confirm text is legible and no native rendering artifact appears).

---

## 7. AI-15 disclaimers

Not applicable. This milestone contains no new variety, figure, or math claim proposals. All changes are UX/cleanup work: token values, comment text, tooltip strings, and QSS rules.

---

## 8. Open questions for the user

None. All 8 items are well-specified. Items 2, 4, 6 are confirmed already fixed and require no action.

The only clarifying note: item 3 mentions "Hanson/Fermat tooltip" in the brief, but Hanson surfaces do NOT use coarse preview (they use the e2 full fast-path). The correct tooltip additions for Hanson subtypes should note "renders at full resolution on every drag tick" rather than "drag for coarse preview." This is an honest correction to the brief's framing, not an ambiguity requiring user input.

---

## References

| Artifact | Path | Relevant section |
|---|---|---|
| variety-palette adversary | `.claude/notes/milestones/variety-palette-2026q2-e1/artifacts/adversary-critique.md` | MF1 swatch finding |
| panel-refresh-e2 adversary | `.claude/notes/milestones/panel-refresh-2026q2-e2/artifacts/adversary-critique.md` | M4 FOCUS_RING finding |
| focus-ring-contrast adversary | `.claude/notes/milestones/focus-ring-contrast-2026q2-e1/artifacts/adversary-critique.md` | Closure confirmation |
| e4b adversary | `.claude/notes/milestones/realtime-variety-render-e4b/artifacts/adversary-critique.md` | M7 tooltip, L2 inflight, L3 separator |
| e4b frontend | `.claude/notes/milestones/realtime-variety-render-e4b/artifacts/frontend-critique.md` | L-front-2 inflight removal |
| e5b adversary | `.claude/notes/milestones/realtime-variety-render-e5b/artifacts/adversary-critique.md` | M1/M3 dwork/segre refs |
| dark-mode adversary | `.claude/notes/milestones/dark-mode-2026q2-e1/artifacts/adversary-critique.md` | M_menu_nest deferred |
| dark-mode state | `.claude/notes/milestones/dark-mode-2026q2-e1/state.json` | deferred_findings list |
| spinner adversary | `.claude/notes/milestones/render-busy-spinner-2026q3-e1/artifacts/adversary-critique.md` | LOW-2 QTimer accumulation |
| styles.py | `styles.py:64-143` (PALETTE_LIGHT), `:230-307` (PALETTE_DARK), `:400-624` (_render_stylesheet) | Palette tokens, QSS template |
| appearance_panel.py | `appearance_panel.py:39-53` | _make_swatch, _apply_swatch_color |
| app.py | `app.py:1094-1098` (badge), `:1158-1162` (base_msg), `:390-394` (init icon), `:1615-1619` (theme icon), `:1663-1665` (system icon) | Separator and spinner sites |
| surfaces.py | `surfaces.py:1652-1770` | VARIETY_TOOLTIPS and SUBTYPE_TOOLTIPS |
| icons.py | `icons.py:302-373` | render_busy_spinner_icon factory |
| tests | `tests/test_styles_palette.py`, `tests/test_render_busy_spinner.py` | Existing test patterns |
