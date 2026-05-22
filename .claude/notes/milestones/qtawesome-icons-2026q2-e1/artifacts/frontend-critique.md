# Frontend UI/UX Critique — qtawesome-icons-2026q2-e1

**Milestone:** qtawesome-icons-2026q2-e1 (UPL-4)
**Commit range:** `fbbae5ce..e2e1ba58`
**Date:** 2026-05-21
**Critic:** milestone-frontend-ux-critic (claude-sonnet-4-6)
**Files in scope:** `app.py`, `view_panel.py`, `parameters_panel.py`, `icons.py` (new)

---

## Executive summary

This milestone adds qtawesome icons to three buttons (Reset Camera, Screenshot, Reset Defaults)
via a new `icons.py` factory and `refresh_icons(theme)` methods on two panels. The implementation
is technically sound: icons are applied after `QApplication` is live, before `win.show()`,
and re-rendered on theme swap. AI-9, AI-11, AI-12, AI-13 are all clean for the new code.

Two MEDIUM findings merit rectification before the next milestone: (1) the Reset Defaults icon
uses the neutral `TEXT_VALUE` color while the button's text label uses the intentional
`TEXT_RESET_BTN` red-family token — the icon is a grey/white blob on a red-family background
rather than a co-themed glyph; and (2) the two camera-family icons (`mdi6.camera-retake` for
Reset Camera and `mdi6.camera` for Screenshot) occupy separate group boxes but share a body
glyph that becomes ambiguous at the 16–22 px default icon size on macOS. One LOW finding covers
icon-size non-determinism (no `setIconSize` call).

Zero CRITICAL findings. One pre-existing LOW (dead deprecated-style imports) is called out in scope
so it does not block this milestone's landing.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM-1 — Reset Defaults icon color breaks the button's red-family visual coding

**Where:** `icons.py:106-113` / `parameters_panel.py:113-123`
**Evidence:** `_icon_color(theme)` returns `PALETTE_LIGHT["TEXT_VALUE"] = #333333` (light) or
`PALETTE_DARK["TEXT_VALUE"] = #e0e0e0` (dark) for every icon, including the one on the
`#resetDefaultsBtn`. The QSS for that button explicitly overrides `color:` to
`TEXT_RESET_BTN = #5a3a3a` (light) or `#ffc0c0` (dark), creating a deliberate red-family
visual identity. The icon glyph (the only truly new visual element on this button) ignores that
identity: in light theme it renders as dark neutral grey; in dark theme it renders as near-white,
while the button text is salmon pink. Both `mdi6.restore` glyphs are contrast-safe (10.58:1 light
and 10.94:1 dark on respective button backgrounds — well above the 3:1 WCAG non-text floor), but
the icon and the label text are two visually unrelated colors on the same widget.
**Why it matters:** The `#resetDefaultsBtn` is the only button in the app with a distinct
color-coded identity (pink/wine-red = "destructive-ish / restore"). Industry convention (Blender 4.x
destructive-action buttons, e.g. the Delete button, render their icon in the same hue family as the
button text — a red icon on a red-tinted button). Rendering a grey/white icon on the red-family
button makes it look like an error in icon assignment rather than intentional design.
**Suggested fix:** Add a dedicated `reset_defaults_icon_color(theme)` helper in `icons.py` that
returns `PALETTE_LIGHT["TEXT_RESET_BTN"]` or `PALETTE_DARK["TEXT_RESET_BTN"]` instead of
`TEXT_VALUE`. Pass that color to `qta.icon("mdi6.restore", color=...)`. Both values are 6-digit
hex already (AI-13 safe); contrast ratios on the button background remain well above 3:1 (8.37:1
light, 9.32:1 dark — pre-verified).

---

### MEDIUM-2 — Two camera-family icons in adjacent panel sections are ambiguous at default icon size

**Where:** `view_panel.py:377-378` / `icons.py:87-103`
**Evidence:** `mdi6.camera-retake` (camera body + small circular arrow) and `mdi6.camera` (plain
camera body) are assigned to Reset Camera and Screenshot respectively. These two glyphs share the
same large-camera-body anchor. At the Qt default `PM_ButtonIconSize` on macOS (approximately
16–22 px with the Fusion-style QSS override), the circular arrow in `camera-retake` is rendered
at roughly 3–5 px — below the 7 px threshold at which detail glyphs are reliably distinguishable
for users with mild refractive error. The two buttons are in separate group boxes ("Camera" and
"Export"), which provides some semantic separation, but a user reading icons without labels would
see two nearly identical camera silhouettes in the same panel.
**Why it matters:** Industry comparison — ParaView 5.12 separates its reset-camera and
screenshot actions categorically: reset-camera uses a reset/home-style glyph (not a camera), while
screenshot uses a camera or film-strip glyph. This iconographic separation makes the two actions
unambiguous even when the icon is the only affordance visible (e.g. on a narrow dock). The current
choice conflates both into the camera semantic. Blender 4.x similarly distinguishes "center view"
(a dot-in-circle / target) from "render image" (a camera body).
**Suggested fix:** Replace `mdi6.camera-retake` with `mdi6.camera-flip-outline` (arrow-and-camera
composition with more visible arrow at small sizes) OR switch to a non-camera semantic for Reset
Camera, such as `mdi6.fit-to-screen` or `mdi6.arrow-expand-all` (which 3D Slicer uses for
"reset/center view"). Either change eliminates the same-glyph-family collision. The icon-name
change is a single-line edit in `icons.py:95`.

---

## LOW

### LOW-1 — No explicit `setIconSize` call; icon dimensions are platform-dependent

**Where:** `view_panel.py:362-378` / `parameters_panel.py:113-123` / `icons.py` (module)
**Evidence:** Neither `refresh_icons()` method calls `btn.setIconSize(QSize(w, h))` before
`btn.setIcon(...)`. Qt resolves the displayed size from `QStyle::PM_ButtonIconSize`, which on
macOS varies by platform style: approximately 22 px under native Aqua, approximately 16 px under
the Fusion style activated by `QApplication.setStyleSheet`. The view-preset grid buttons have
`setFixedHeight(26)` while `_reset_camera_btn` has no fixed height — a 22 px icon in a 28 px
button produces a correct result, but a 22 px icon with 3 px padding in a button that auto-sizes
to 30+ px can produce inconsistent heights between the preset grid and the Camera group button.
This is a manual-verification item only; it cannot be confirmed without running the app on the
target platform (AI-2 / AI-3 prevent automated Qt+VTK headless testing on macOS).
**Why it matters:** Visual rhythm between adjacent control groups (View Presets vs Camera) is
disrupted if Reset Camera is noticeably taller than the 26 px preset buttons above it. Users
parsing the panel height-to-importance mentally interpret taller buttons as primary actions —
which is correct for Reset Camera but creates a visual discontinuity with the compact preset grid.
**Suggested fix:** Add `self._reset_camera_btn.setIconSize(QSize(16, 16))` (and analogously for
`_shot_btn` and `_reset_btn`) before `setIcon()`. `QSize` is already imported in PySide6.QtCore.
A 16 px icon fits comfortably in a `fixedHeight=26` button and avoids the Aqua vs Fusion size
discrepancy.

---

### LOW-2 — `mdi6.restore` may be misread as "Undo last action" by first-time users

**Where:** `icons.py:106-113` / `parameters_panel.py:113-123`
**Evidence:** `mdi6.restore` is a counterclockwise full-circle arrow — the same gestalt as the
universal Ctrl+Z undo icon used by every major desktop application (macOS standard,
Windows standard, Blender, ParaView). The `resetDefaultsBtn` resets all sliders to their default
values, which is not the same action as "undo the last slider change." The tooltip text is
correct ("Reset all parameter sliders to their default values (Ctrl+D)"), but the icon sets up a
false expectation for first-time users before they hover.
**Why it matters:** Mathematica's `Manipulate[]` UI uses a distinct "rewind to beginning"
double-arrow icon for parameter reset (not the single-arrow undo glyph) to signal "go back to
initial state" vs "undo one step." SURFER (Imaginary.org) shows no reset icon — it relies on
labeled buttons. The absence of a clear "reset all" convention in this icon family means the
designer must work harder to differentiate from undo. The tooltip is the only correct signal here,
and tooltip-dependent design is fragile.
**Suggested fix:** Consider `mdi6.restore-clock` (clockwise restore with a clock face inset —
implies "back to saved state"), or `mdi6.playlist-remove` (too niche), or simply accept that
`mdi6.restore` paired with the button label "Reset all to defaults" is unambiguous enough. If the
button label and tooltip are trusted as the primary affordance, this LOW can be deferred. Flag for
user-testing feedback in any future UX round.

---

### LOW-3 — Dead deprecated-style imports in `parameters_panel.py` and `view_panel.py` (pre-existing, not introduced by this milestone)

**Where:** `parameters_panel.py:24` / `view_panel.py:38`
**Evidence:** Both files import `MUTED_TEXT_STYLE`, `RANGE_LABEL_STYLE`, `VALUE_MONO_STYLE` at
the module level. These constants were deprecated in `dark-mode-2026q2-e1` — all call sites were
migrated to `setProperty("role", ...)` patterns, and `test_no_inline_color_styles_in_panel_files`
passes. The imports are now unused (dead). `SMALL_LABEL_STYLE = "font-size: 11px;"` (no color) is
still actively used at `parameters_panel.py:150` and is not a concern. This finding is
pre-existing; the qtawesome milestone did not introduce it and does not need to fix it. Calling it
out to avoid it being filed as a new finding in the next critique.
**Why it matters:** Unused imports of deprecated symbols create ambiguity for future authors who
may not know whether the import is intentional or forgotten. The test guard catches active misuse
but not dead imports.
**Suggested fix:** Remove `MUTED_TEXT_STYLE`, `RANGE_LABEL_STYLE`, `VALUE_MONO_STYLE` from both
import lines. Keep `SMALL_LABEL_STYLE` in `parameters_panel.py`. One-line change per file; no
behavior change.

---

## What was done well

1. **QApplication-availability discipline is correct.** `refresh_icons()` is called at the end of
   `MainWindow.__init__`, after all panel construction, and the module-level comment in `icons.py`
   is explicit about why it cannot be called from `_build_ui()`. This is the hardest part of icon
   initialization in a multi-panel Qt app and was handled correctly.

2. **Lazy-import pattern prevents cold-start regression.** Deferring the `qtawesome` import to the
   first `refresh_icons()` call (via `_get_qta()`) keeps module import cheap. The 150–200 ms
   font-cache cost fires during window construction — the UI is visible but not yet shown to the
   user — rather than at `import app`, which would delay every import-time static check.

3. **Theme-swap coverage is complete and AI-9 safe.** All three `refresh_icons()` call sites in
   `app.py` (`__init__`, `_on_theme_changed`, `_apply_system_theme`) are correctly placed after
   `setStyleSheet()` and contain no `processEvents()`. The "Follow system" path (OS-driven theme
   change) also receives icon updates. No re-entrancy risk.

4. **AI-12 / AI-13 compliance is clean.** Icon color resolves through `PALETTE_LIGHT/DARK["TEXT_VALUE"]`,
   which are 6-digit hex strings pre-verified by the test suite. Contrast ratios on every button
   background exceed 10:1 — comfortably above the 3:1 WCAG non-text floor. No short-hex anywhere
   in the new code.

5. **First-launch experience (CONTEXT.md §9.3) is preserved.** `refresh_icons()` does not touch
   dropdowns, does not select a variety, and does not call `_render_current`. The `-- Select --`
   placeholder and empty plotter are intact. Icons are visual chrome only.

6. **Instance-attribute promotion is minimal and justified.** Only `_reset_camera_btn` and
   `_shot_btn` in `ViewPanel` were promoted from local variables to instance attributes — the
   minimum needed for `refresh_icons()` to reach them. `_reset_btn` in `ParametersPanel` was
   already an instance attribute. No unnecessary scope leakage.

---

## Recommended rectification order

1. **MEDIUM-1 (Reset Defaults icon color):** Add `reset_defaults_icon_color(theme)` in `icons.py`
   returning `TEXT_RESET_BTN`. Single-line change to `icons.py:113` and `parameters_panel.py:123`.
   This is the most visible polish gap and is trivially fixable.

2. **MEDIUM-2 (camera-icon disambiguation):** Replace `mdi6.camera-retake` with a non-camera-body
   glyph for Reset Camera (`mdi6.fit-to-screen` or `mdi6.arrow-expand-all`). Single-line change in
   `icons.py:95`.

3. **LOW-1 (icon size):** Add `setIconSize(QSize(16, 16))` calls in `refresh_icons()` bodies.
   Requires manual verification on macOS after the change.

4. **LOW-2 and LOW-3:** Defer to next cleanup pass. LOW-2 requires user-testing data to act on
   with confidence. LOW-3 is a pre-existing issue below this milestone's scope.
