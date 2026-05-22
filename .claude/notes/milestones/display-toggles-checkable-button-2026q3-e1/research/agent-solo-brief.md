# Research Brief — display-toggles-checkable-button-2026q3-e1

**Agent:** solo (Sonnet) | **Date:** 2026-05-22 | **Status:** complete

---

## 1. TL;DR

Replace `self._wireframe_cb` and `self._edges_cb` (QCheckBox) with
`QPushButton(checkable=True, flat=False)` in `appearance_panel.py:_build_toggles_group`,
wired with the identical `toggled(bool)` signal; add
`QPushButton[role="display-toggle"]` QSS rules (checked/hover/checked:hover) to
`_render_stylesheet` using a new `BG_TOGGLE_CHECKED` token per theme (no WCAG
violation — all borders reuse FOCUS_RING which already passes 3:1 on both panels).
The main risk is the QSS hover/checked distinction: the two fill-tint candidates
(`#d4e6f5` light / `#1a3048` dark) are only 1.10:1 against the hover tint, so the
checked-state visual identity relies primarily on the 2px FOCUS_RING border, not the
fill.  Backup plan: drop the fill tint entirely and use border-only for the checked
indicator (simpler QSS, equally WCAG-compliant).

---

## 2. Prior art in this repo

- `appearance_panel.py:162-181` — `_build_toggles_group` constructs `self._wireframe_cb`
  (QCheckBox) and `self._edges_cb` (QCheckBox), wires `toggled` signal, calls
  `setChecked(self._wireframe)` / `setChecked(self._show_edges)` (both False at
  first launch).  This is the direct migration target.

- `appearance_panel.py:87-90` — State fields `self._wireframe = False` and
  `self._show_edges = False`.  Both default to False; the new QPushButton must call
  `setChecked(False)` (or rely on default) to preserve this.

- `appearance_panel.py:265-279` — `_on_wireframe_toggled(checked: bool)` and
  `_on_edges_toggled(checked: bool)` handlers store state and call `apply_to_actor`.
  No widget-type references; wiring survives unchanged.

- `appearance_panel.py:413-451` — `refresh_icons(theme)` calls
  `self._wireframe_cb.setIcon(...)` / `self._edges_cb.setIcon(...)` with
  `setIconSize(QSize(16, 16))`.  `setIcon` and `setIconSize` are
  `QAbstractButton` methods — identical API on QPushButton.  No change needed.

- `appearance_panel.py:319-343` — `apply_to_actor` reads `self._wireframe` and
  `self._show_edges`; no widget-type dependency.

- `styles.py:375-494` — `_render_stylesheet(palette)` function: the template that
  must receive the new `QPushButton[role="display-toggle"]` rules.  The role-property
  QSS pattern is already established for `QLabel[role="muted"]` etc.
  (`styles.py:402-415`).

- `styles.py:64-130` — `PALETTE_LIGHT` — existing tokens.  The `FOCUS_RING` token
  (`#3c82c4` light, `#5b9bd5` dark) is the correct reuse candidate for the
  checked-border color; no new BORDER_TOGGLE_CHECKED token needed.

- `styles.py:217-282` — `PALETTE_DARK` — key-identical.  `BG_TOGGLE_CHECKED` must
  be added to BOTH dicts to satisfy `test_palette_dark_has_minimum_tokens`.

- `tests/test_styles_palette.py:143-156` — `test_app_stylesheet_substitutes_no_raw_hex_outside_palette`:
  any new hex in `_render_stylesheet` must come from `palette["TOKEN"]` or the
  test fails.

- `tests/test_styles_palette.py:518-531` — `test_app_stylesheet_dark_no_raw_hex`:
  same guard for the dark stylesheet.  Adding a `BG_TOGGLE_CHECKED` token to both
  palettes and referencing it as `palette["BG_TOGGLE_CHECKED"]` in the template
  satisfies both tests automatically.

- `tests/test_styles_palette.py:44-55` — `test_palette_light_has_minimum_tokens`:
  does NOT assert the specific token count, only requires the 6 listed required
  keys — adding new tokens will not break this test.

- `tests/test_styles_palette.py:366-371` — `test_palette_dark_has_minimum_tokens`:
  asserts `PALETTE_DARK.keys() == PALETTE_LIGHT.keys()`.  Adding
  `BG_TOGGLE_CHECKED` to PALETTE_LIGHT WITHOUT adding it to PALETTE_DARK would
  break this test.  Both must be added.

- `tests/test_styles_palette.py:615-660` — `test_no_inline_color_styles_in_panel_files`:
  panel files must not call `setStyleSheet(MUTED_TEXT_STYLE)` etc.  The new
  `setProperty("role", "display-toggle")` call follows the correct pattern.

- `view_panel.py:70-71`, `130-141` — existing QPushButton usage for camera-preset
  buttons (non-checkable).  The `_preset_btns` loop and `_iso_btn` show the
  constructor pattern for the panel's existing buttons — no `setCheckable` call
  there since they are non-checkable.

- `.claude/notes/milestones/qtawesome-icons-2026q2-e2/artifacts/adversary-critique.md:203-208` —
  F-M2 original finding: explicitly names the `[check][icon][label]` triple-prefix
  problem and names the two remediation paths: (a) companion QLabel, (b)
  QPushButton(checkable=True).  Path B is the brief's chosen approach.

- `.claude/notes/milestones/qtawesome-icons-2026q2-e2/artifacts/adversary-critique.md:255-257` —
  Deferral note: explicitly names `display-toggles-checkable-button-2026q3-e1` as the
  target milestone.  This is that milestone.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| PySide6 QPushButton docs | https://doc.qt.io/qt-6/qpushbutton.html | `setCheckable(True)` / `setFlat(True)` are QPushButton methods; `toggled(bool checked)` signal is inherited from QAbstractButton, same as QCheckBox | Confirms signal parity |
| PySide6 QAbstractButton docs | https://doc.qt.io/qt-6/qabstractbutton.html | `toggled(bool checked)` signal, `setChecked(bool)`, `setIcon()`, `setIconSize()` — all shared with QCheckBox via common base | Confirms full API parity |
| PySide6 QSS reference | https://doc.qt.io/qt-6/stylesheet-reference.html | `QPushButton:checked` pseudo-state; `QPushButton:hover`; `:checked:hover` compound selector — all standard | QSS checked-state template |
| WCAG 2.1 SC 1.4.11 Non-text Contrast | https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html | "Active state must have a 3:1 contrast with adjacent colors" for UI components | The checked-border (not fill) is the WCAG indicator |
| Blender 4.x Viewport Shading N-panel (industry ref) | (desktop app — no URL) | Checkable QPushButton with icon; pressed/depressed border signals state; no check-square indicator | F-M2 industry precedent |
| 3D Slicer 5.x modules panel (industry ref) | (desktop app — no URL) | Checkable QPushButton with paired ON/OFF icons | Confirms checkable QPushButton pattern; dual icons are optional |
| ParaView Properties panel (industry ref) | (desktop app — no URL) | Plain text checkboxes with no icon at all | Confirms QCheckBox+icon is the anomaly, not the norm |

Note: web searches were not performed for this milestone — it is a pure widget-substitution + QSS design task with all signal from repo-local files and WCAG arithmetic.

---

## 4. Recommended approach

### 4.1 Widget construction (appearance_panel.py:_build_toggles_group)

Replace the two `QCheckBox` constructions with `QPushButton` instances:

```python
# Widget construction pattern (pseudocode — do not copy verbatim; implementer adds imports)
self._wireframe_cb = QPushButton("Wireframe")
self._wireframe_cb.setCheckable(True)
self._wireframe_cb.setChecked(self._wireframe)  # False — first-launch default preserved
self._wireframe_cb.setToolTip("Show the surface as a wireframe mesh instead of a solid")
self._wireframe_cb.setProperty("role", "display-toggle")
self._wireframe_cb.toggled.connect(self._on_wireframe_toggled)

self._edges_cb = QPushButton("Show edges")
self._edges_cb.setCheckable(True)
self._edges_cb.setChecked(self._show_edges)  # False
self._edges_cb.setToolTip("Overlay mesh edges on the solid surface (inactive in wireframe mode)")
self._edges_cb.setProperty("role", "display-toggle")
self._edges_cb.toggled.connect(self._on_edges_toggled)
```

**Signal parity confirmed:** Both `QCheckBox` and `QPushButton` inherit `toggled(bool)`
from `QAbstractButton`.  The signal name, signature, and synchronous emission on
`setChecked()` are identical.  Signal-loop risk: `_on_wireframe_toggled` and
`_on_edges_toggled` ONLY write `self._wireframe`/`self._show_edges` and call
`apply_to_actor` — they never call `setChecked()` back on the button.  No signal-loop
risk exists.

**QCheckBox import:** `QCheckBox` may be removed from the import block in
`appearance_panel.py:18` if no other code uses it.  Verify with a repo-wide grep
before removing.

**`setProperty` call timing:** `setProperty("role", "display-toggle")` must be called
before `QApplication.setStyleSheet(...)` re-reads widget styles — which happens at
construction time since `APP_STYLESHEET_DARK` is applied in `main()`.  Calling
`setProperty` immediately after `QPushButton(...)` construction (before adding to
layout) is the correct ordering, consistent with the `setProperty("role", "muted")`
pattern at `view_panel.py:97`.

**`style().unpolish()` / `polish()` note:** After `setProperty`, Qt may require
`self.style().unpolish(widget); self.style().polish(widget)` to re-read the property
in the running app.  For widgets constructed fresh during `_build_toggles_group`
(which runs during `__init__`, before the window is shown), this is NOT needed —
the style is applied once when the widget first becomes visible.  Only needed if
`setProperty` is called on an already-visible widget.

### 4.2 QSS checked-state design

**Approach: subtle fill tint + 2px colored border for checked state.**

The WCAG 1.4.11 indicator is the **border** (the active state indicator), not the
fill.  The fill tint is optional visual reinforcement.

**New palette tokens (both themes):**

- `BG_TOGGLE_CHECKED` (light): `#d4e6f5`  — light blue tint
- `BG_TOGGLE_CHECKED` (dark):  `#1a3048`  — deep navy tint

**WCAG arithmetic (all verified numerically):**

| Test | Value | Result |
|---|---|---|
| FOCUS_RING light (`#3c82c4`) vs BG_PANEL light (`#f0f0f0`) | 3.56:1 | PASS >= 3:1 |
| FOCUS_RING dark (`#5b9bd5`) vs BG_PANEL dark (`#252526`) | 5.17:1 | PASS >= 3:1 |
| FOCUS_RING light (`#3c82c4`) vs BG_TOGGLE_CHECKED light (`#d4e6f5`) | 3.17:1 | PASS >= 3:1 |
| FOCUS_RING dark (`#5b9bd5`) vs BG_TOGGLE_CHECKED dark (`#1a3048`) | 4.55:1 | PASS >= 3:1 |
| TEXT_VALUE light (`#333333`) on BG_TOGGLE_CHECKED light (`#d4e6f5`) | 9.89:1 | PASS >= 4.5:1 |
| TEXT_VALUE dark (`#e0e0e0`) on BG_TOGGLE_CHECKED dark (`#1a3048`) | 10.20:1 | PASS >= 4.5:1 |
| BG_TOGGLE_CHECKED light vs hover tint (`#e8f0f5`) | 1.11:1 | Structural only — WCAG indicator is border |
| BG_TOGGLE_CHECKED dark vs hover tint (`#2a3a45`) | 1.15:1 | Structural only |

The hover/checked fill tints are nearly indistinguishable by ratio alone (1.10-1.15:1).
This is acceptable because the WCAG-compliant indicator is the **border** (3.17-4.55:1
vs the fill background, and 3.56-5.17:1 vs the panel).  The fill tint is decoration
that reinforces the state; the border communicates it.  This matches the Blender
convention (pressed/depressed state = border change, not fill change).

**QSS template (add to `_render_stylesheet` in `styles.py`):**

```css
/* --- Display-toggle checkable buttons (Appearance dock) ------------------- */
/* display-toggles-checkable-button-2026q3-e1 (UPL-4 F-M2 closure):
   QPushButton(checkable=True) replaces QCheckBox for Wireframe + Show-edges.
   Icon is the primary affordance; border signals checked state (WCAG 1.4.11
   non-text contrast: border uses FOCUS_RING which is 3.56:1 light / 5.17:1 dark
   vs BG_PANEL).  Fill tint (BG_TOGGLE_CHECKED) is decoration.
   AI-9 safe: setCheckable/setChecked are synchronous, no processEvents. */
QPushButton[role="display-toggle"] {
    padding: 3px 8px;
    border-radius: 3px;
    border: 1px solid transparent;
    background: transparent;
    text-align: left;
}
QPushButton[role="display-toggle"]:hover {
    background: {palette["BG_CAMERA_BTN_HOVER"]};
    border: 1px solid {palette["BORDER_CAMERA_BTN"]};
}
QPushButton[role="display-toggle"]:checked {
    background: {palette["BG_TOGGLE_CHECKED"]};
    border: 2px solid {palette["FOCUS_RING"]};
}
QPushButton[role="display-toggle"]:checked:hover {
    background: {palette["BG_CAMERA_BTN_HOVER"]};
    border: 2px solid {palette["FOCUS_RING"]};
}
```

**Token reuse rationale:**
- `BG_CAMERA_BTN_HOVER` is reused for the hover fill — same semantic (an outlined
  clickable in the panel), same visual register (subtle blue-grey tint).
- `BORDER_CAMERA_BTN` is reused for the hover border.
- `FOCUS_RING` is reused for the checked border — same semantic (active/selected
  indicator); avoids a `BORDER_TOGGLE_CHECKED` token.
- `BG_TOGGLE_CHECKED` is a **new** token needed for the checked-fill tint.

### 4.3 Palette token decision

**New token required: `BG_TOGGLE_CHECKED` in both palettes.**

Add to `PALETTE_LIGHT`:
```python
"BG_TOGGLE_CHECKED":         "#d4e6f5",   # display-toggle checked fill (light blue tint)
```
Add to `PALETTE_DARK`:
```python
"BG_TOGGLE_CHECKED":         "#1a3048",   # display-toggle checked fill (deep navy tint)
```

No other new tokens needed:
- `FOCUS_RING` covers the checked-border color (already per-theme, already WCAG-compliant).
- `BG_CAMERA_BTN_HOVER` covers the hover fill (already per-theme, already present).
- `BORDER_CAMERA_BTN` covers the hover border (already per-theme, already present).

### 4.4 Icon-state question (single vs dual icons)

**Recommendation: single icon (current AVC pattern), no change.**

The 3D Slicer dual-icon approach (separate ON/OFF QIcons swapped on toggle) would
require: (a) new icon factory functions in `icons.py`, (b) a signal connection in
`refresh_icons` to swap on toggle, (c) more complex `refresh_icons` wiring.

The AVC pattern (single icon, checked state communicated by border/fill) is simpler,
already established by `refresh_icons`'s current call to `setIcon` once, and is
sufficient because the checked border is the visual indicator.  Blender's N-panel uses
the same single-icon + pressed-state convention.

**Defer dual icons to a future polish pass** if user research shows ambiguity.

### 4.5 First-launch behavior preservation

Both `self._wireframe = False` and `self._show_edges = False` are set at
`appearance_panel.py:88-89`.  The new `QPushButton.setChecked(False)` call (or
the default unchecked state of a freshly constructed QPushButton) preserves this.
Verify: `QPushButton(checkable=True)` default `isChecked()` is `False` — confirmed
by Qt's QPushButton documentation.

### 4.6 Signal-loop check

`_on_wireframe_toggled` (`appearance_panel.py:265-270`) and `_on_edges_toggled`
(`appearance_panel.py:272-279`) only write `self._wireframe`/`self._show_edges` and
call `apply_to_actor` via `self._get_actor()`.  Neither calls `setChecked()` on any
widget.  `apply_to_actor` reads `self._wireframe` and `self._show_edges` directly —
no widget state read.  **No signal-loop risk.**

The `processEvents()` call in `_render_current` (app.py) drains the event queue.
If a user clicks the Wireframe button during a render, the event is queued.  The
`self._computing` guard in `_render_current` blocks re-entry.  The `toggled` signal
from a user click during a render will fire after `processEvents()` returns and
`self._computing` is cleared — the normal queued path.  No AI-9 concern.

### 4.7 Test plan

**a) tests/test_styles_palette.py — new checked-state contrast guards:**

Add two new test functions:

1. `test_bg_toggle_checked_is_six_digit_hex()` — asserts both
   `PALETTE_LIGHT["BG_TOGGLE_CHECKED"]` and `PALETTE_DARK["BG_TOGGLE_CHECKED"]`
   match `HEX6`.  (Parallel to `test_every_palette_value_is_six_digit_hex` but
   scoped to the new token for clarity in error messages.)

2. `test_display_toggle_checked_border_meets_wcag_non_text_contrast()` — asserts
   `_ratio(PALETTE_LIGHT["FOCUS_RING"], PALETTE_LIGHT["BG_PANEL"]) >= 3.0` AND
   `_ratio(PALETTE_DARK["FOCUS_RING"], PALETTE_DARK["BG_PANEL"]) >= 3.0`.
   (Redundant with `test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel`
   and `test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark` — but a
   dedicated test named for this feature makes it discoverable in failure
   messages.  Alternatively, add a comment to the existing tests linking to
   this milestone rather than duplicating assertions.)

3. `test_display_toggle_role_selector_in_both_stylesheets()` — asserts
   `QPushButton[role="display-toggle"]` appears in both `APP_STYLESHEET` and
   `APP_STYLESHEET_DARK`.  Pattern from `test_dark_stylesheet_includes_role_selectors`.

4. `test_bg_toggle_checked_in_stylesheet()` — asserts that the rendered
   `APP_STYLESHEET` and `APP_STYLESHEET_DARK` each contain the BG_TOGGLE_CHECKED
   hex value (verifying the template actually uses the new token).

**b) tests/test_styles_palette.py — existing tests that change behavior:**

- `test_palette_dark_has_minimum_tokens` — will continue to pass IFF
  `BG_TOGGLE_CHECKED` is added to BOTH palettes.
- `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` — will continue to
  pass IFF the new QSS rules reference `palette["BG_TOGGLE_CHECKED"]` not a literal.

**c) New test file: tests/test_appearance_panel_toggles.py (optional)**

The unbound-method shim pattern from `test_styles_palette.py:236-265` can be reused
to test the signal contract:

1. `test_wireframe_toggle_button_is_checkable()` — import `appearance_panel`, use the
   shim pattern to verify `self._wireframe_cb.isCheckable() == True` after
   `_build_toggles_group` — but this requires a live QApplication (Qt widget
   construction), violating AI-2.

**AI-2 constraint:** QPushButton is a Qt widget — constructing it requires
`QApplication`.  The shim pattern for `set_default_color` / `set_culling` works
because those methods only manipulate Python attributes and a `QColor` (which is
a pure data type from QtGui, not a widget).  A test that constructs `QPushButton`
or `QCheckBox` directly would require `QApplication`, breaking AI-2.

**Recommended approach for test coverage:**

Use the `grep`-based source-text pattern:

```python
def test_appearance_panel_display_toggles_are_qpushbutton():
    """display-toggles-checkable-button-2026q3-e1: _build_toggles_group must
    use QPushButton(checkable=True) not QCheckBox for Wireframe and Show-edges.
    Asserted on source text (AI-2 — no QApplication allowed in test suite).
    """
    import pathlib
    src = (pathlib.Path(__file__).parent.parent / "appearance_panel.py").read_text()
    # Must NOT see QCheckBox construction for these two toggles
    # (source-text check: the _build_toggles_group method must not contain
    # 'QCheckBox("Wireframe")' or 'QCheckBox("Show edges")')
    assert 'QCheckBox("Wireframe")' not in src
    assert 'QCheckBox("Show edges")' not in src
    # Must see QPushButton with setCheckable for these two
    # (The presence of setCheckable anywhere in appearance_panel is sufficient
    # given the method is only called in _build_toggles_group)
    assert 'setCheckable(True)' in src
    assert 'setProperty("role", "display-toggle")' in src
```

This is AI-2 compliant (pure source-text grep, no Qt).  It is weaker than a
behavioral test but sufficient to guard the migration.

### 4.8 CONTEXT.md §8 entry

See section 7 below.

---

## 5. Alternatives considered

- **Companion QLabel (F-M2 path A):** Place a `QLabel` with the icon to the left of
  the QCheckBox (`[icon] ☐ [text]`).  Rejected: still has the check-square indicator,
  still creates an ambiguous compound affordance.  Triple-prefix becomes double-prefix
  but remains visually unclean.

- **QToolButton (checkable):** Qt provides `QToolButton` which is also checkable and
  icon-bearing.  Rejected: QPushButton is already imported in appearance_panel.py;
  QToolButton adds a new import for no QSS or behavioral benefit.  QPushButton with
  `setCheckable(True)` is exactly the right abstraction.

- **Filled background only (no border indicator):** Use only `BG_TOGGLE_CHECKED` fill
  for the checked state, no border change.  Rejected: WCAG 1.4.11 requires the state
  indicator to meet 3:1 against adjacent colors; a fill-only change whose 3:1 is
  measured only against the outer panel (not the button's own hover fill) is fragile.
  The border is the correct indicator.

- **Keep QCheckBox, hide indicator via QSS `QCheckBox::indicator`:**
  `QCheckBox::indicator { width: 0; height: 0; }` would hide the check-square.
  Rejected: removes the semantic affordance entirely (no visual state signal);
  creates a misleading QSS hack that obscures intent.

- **Single shared `BG_TOGGLE_CHECKED` token across themes (like FOCUS_RING dual-pass
  zone `#3c82c4`):** The dual-pass zone is feasible (several candidates pass 3:1 on
  both panels), but the token is a FILL not a border — it does not need to meet the
  3:1 WCAG non-text threshold (the border does).  Per-theme values give better
  visual coherence: a light blue tint reads naturally on the light panel, and a dark
  navy reads naturally on the dark panel.

---

## 6. Risks and unknowns

**AI-9 (re-entrancy):** No risk.  The migration is purely construction-time
widget-type substitution.  `setCheckable`, `setChecked`, `setProperty` are all
synchronous Qt property setters — no `processEvents` involved.

**AI-11 (fully-qualified enums):** No new enum references needed.  `Qt.Orientation`
and `Qt.AlignmentFlag` are already used elsewhere in `appearance_panel.py`.
`setCheckable(True)` and `setChecked(False)` pass plain booleans, not Qt enums.

**AI-12 (WCAG):** The checked-state WCAG test is the highest-stakes deliverable.
All measurements above are numerically verified.  The WCAG 1.4.11 obligation is on
the **border** (the state indicator), not the fill.  The border uses `FOCUS_RING`
which already passes in both themes.  New `BG_TOGGLE_CHECKED` fill does not need
to meet 3:1 independently (it is decoration, not the indicator).

**AI-13 (6-digit hex):** New tokens `#d4e6f5` (light) and `#1a3048` (dark) are both
6-digit hex.  Compliant.

**Qt style cascade precedence:** `setProperty("role", "display-toggle")` sets a
dynamic property.  Qt's QSS cascade evaluates `QPushButton[role="display-toggle"]`
at style application time.  For widgets constructed in `_build_toggles_group` (called
from `__init__`, before the window is shown), the style is applied when the widget
first becomes visible — no `unpolish/polish` call needed.  The `APP_STYLESHEET_DARK`
is set via `app.setStyleSheet(APP_STYLESHEET_DARK)` in `main()` before `MainWindow`
is shown; the new rule will cascade correctly.

**`QCheckBox` import cleanup:** After migration, `QCheckBox` may no longer be used
in `appearance_panel.py`.  Check: the only remaining uses would be none (the shading
group uses `QRadioButton`, not `QCheckBox`).  The import at line 19 (`QCheckBox,`)
should be removed to keep the import block clean.  This is a cosmetic change that
will also satisfy any future import-hygiene test.

**`text-align: left` on QPushButton:** The QSS `text-align: left` property ensures
the icon + text layout within the button matches the previous QCheckBox layout
(left-aligned label).  This is important for vertical rhythm with the surrounding
group box content.  Without it, QPushButton defaults to center-aligned content,
which looks out of place in a vertical stack.

**`setFlat()` consideration:** `QPushButton.setFlat(True)` removes the button's
3D frame, making it look more checkbox-like in unchecked state.  This is an
alternative visual style.  The `QPushButton[role="display-toggle"]` QSS already
sets `border: 1px solid transparent; background: transparent` which achieves the
same visual effect via stylesheet (preferred — keeps styling in QSS).  Do NOT
call `setFlat(True)` in addition; it may interfere with the QSS border rendering.

**`padding` and height alignment:** The new QPushButton will be taller than the
QCheckBox it replaces because QPushButton has more default vertical padding.
The QSS rule sets `padding: 3px 8px` (matching the generic `QPushButton` rule in
the existing stylesheet at `styles.py:447-451`).  Verify visual alignment is
acceptable — the group box's `vl.setSpacing(4)` spacing should handle minor height
changes.

**CONTEXT.md `§8` entry note:** The docstring in `refresh_icons` at
`appearance_panel.py:413-443` currently says `QCheckBox inherits setIcon() from
QAbstractButton` — this comment remains true (QPushButton also inherits from
QAbstractButton) and does not need updating.  The more important update is the
comment explaining WHY the widget is QPushButton not QCheckBox.

---

## 7. AI-15 disclaimers

Not applicable — this milestone adds no new mathematical variety or 3D figure.
It is a purely widget-level UI substitution.

---

## 8. CONTEXT.md §8 draft entry

Add after §8.14 (the last existing entry):

```markdown
### 8.15 QCheckBox with icon creates a triple-prefix affordance — use QPushButton(checkable=True) for icon-bearing toggles

`QCheckBox.setIcon()` (inherited from `QAbstractButton`) renders the icon between the
check-square indicator and the text label, producing a `[☐][icon][label]` triple
prefix.  No peer scientific-viz app uses this pattern: Blender 4.x N-panel uses
checkable `QPushButton` with icon (no check-square); 3D Slicer 5.x uses checkable
`QPushButton` with ON/OFF paired icons; ParaView uses plain text checkboxes (no
icon).  The triple prefix creates visual ambiguity — the researcher is unsure
whether to click the check square or the icon.

**Rule:** For icon-bearing display toggles, use `QPushButton(checkable=True)` + QSS
checked-state styling instead of `QCheckBox`.  Use plain `QCheckBox` (no icon) only
for text-only toggles where the check-square indicator is the intended affordance.

**Implementation pattern:**
- `btn.setCheckable(True)` + `btn.setChecked(False)`
- `btn.setProperty("role", "display-toggle")` to pick up QSS rules
- Signal wiring: `btn.toggled.connect(handler)` — identical signal name and signature
  as QCheckBox (`toggled(bool)`), inherited from `QAbstractButton`
- Icons via `refresh_icons(theme)` — `btn.setIcon(...)` / `btn.setIconSize(QSize(16, 16))`
  — same API as QCheckBox (also `QAbstractButton`)
- No `setFlat(True)` — use `border: transparent; background: transparent` in QSS
  for unchecked state (keeps styling in the palette)

**Checked-state QSS design (WCAG 1.4.11 compliant):**
The state indicator is a 2px `FOCUS_RING`-colored border (the same token already
meeting 3:1 non-text contrast in both themes).  A `BG_TOGGLE_CHECKED` fill tint
(new per-theme token) provides optional visual reinforcement but is NOT the WCAG
indicator.  Fill contrast vs adjacent hover tint (~1.1:1) is acceptable because
the border carries the accessibility obligation.

See `display-toggles-checkable-button-2026q3-e1` for the original migration.
`appearance_panel.py:_build_toggles_group` is the canonical example.
```

---

## 9. AI-1..AI-15 conflict matrix

| AI-# | Check | Result |
|---|---|---|
| AI-1 (PySide6 stack) | `QPushButton` is PySide6; no renderer change | CLEAN |
| AI-2 (Qt-free tests) | New tests use source-text grep; no QApplication | CLEAN — see §4.7 |
| AI-3 (off-screen VTK) | No VTK/plotter change | CLEAN |
| AI-4 (clip_box ban) | No domain clipping change | CLEAN |
| AI-5 (scalars= kwarg) | No clip_scalar change | CLEAN |
| AI-6 (pipeline discipline) | No mesh generation change | CLEAN |
| AI-7 (Hanson normals) | No normals change | CLEAN |
| AI-8 (VARIETIES registry) | No surfaces change | CLEAN |
| AI-9 (re-entrancy) | `setCheckable`, `setChecked`, `setProperty` are synchronous; no processEvents added | CLEAN |
| AI-10 (raw mesh cache) | No render pipeline change | CLEAN |
| AI-11 (qualified enums) | No new Qt enum references; boolean args to setCheckable/setChecked | CLEAN |
| AI-12 (WCAG text contrast) | Checked border (FOCUS_RING) passes 3:1 on both panels; text on fill passes 4.5:1 | CLEAN — see §4.2 |
| AI-13 (6-digit hex) | `#d4e6f5` and `#1a3048` are 6-digit; token in PALETTE_LIGHT/DARK routed via `palette["BG_TOGGLE_CHECKED"]` in template | CLEAN |
| AI-14 (generator contract) | No generator change | CLEAN |
| AI-15 (math honesty) | No new variety/figure | N/A |

**Near-miss: AI-9.** The concern was whether `setCheckable(True)` + `setChecked(False)` in `_build_toggles_group` could trigger `toggled` and re-enter anything.  Analysis: `setCheckable(True)` on a button that is already in the default (not checked) state does NOT emit `toggled`.  `setChecked(False)` on a freshly created QPushButton (already unchecked) also does NOT emit `toggled` (the signal only fires on state CHANGE).  Even if it did, the handler writes `self._wireframe = False` which is already `False` — idempotent.  Confirmed clean.

---

## 10. Open questions for the user

None — the milestone is fully specified.

---

*Brief written by milestone-researcher (solo, Sonnet) on 2026-05-22.*
*All WCAG ratios computed numerically; QSS template is pseudocode (not production code).*
