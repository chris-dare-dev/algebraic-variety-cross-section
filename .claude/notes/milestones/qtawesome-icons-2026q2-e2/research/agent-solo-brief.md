# Research Brief — qtawesome-icons-2026q2-e2

**Researcher:** solo
**Date:** 2026-05-22
**Milestone:** Close UPL-4 v1 — camera-preset icons + display-toggle icons; defer spinner
**Status:** complete

---

## 1. TL;DR

Extend `icons.py` with 9 new factory functions (7 camera-preset + 2 display-toggle) using the exact
same Pattern-A architecture from e1: lazy `_get_qta()`, `_icon_color(theme)`, per-function
factory, panel `refresh_icons(theme)` method called from MainWindow's 3 attach points.
The camera-preset buttons in `view_panel.py` are constructed in a loop in `_make_view_presets_group`
and NOT stored as instance attributes — the implementer must restructure this to store a dict
`self._preset_btns: dict[str, QPushButton]` keyed by label ("+X", "-X", etc.) plus
`self._iso_btn`. The Wireframe + Show-edges checkboxes in `appearance_panel.py` are `QCheckBox`
widgets that already inherit `setIcon()` from `QAbstractButton` — no QToolButton migration needed;
the icon appears to the left of the text label (between the check-square and the text). The spinner
is correctly deferred: the `_computing` guard and `processEvents()` call in `_render_current` make
a spinner a re-entrancy minefield (AI-9); it warrants its own focused follow-up milestone.

**Main risk:** The `_make_view_presets_group` loop creates 6 buttons as scoped locals — the
implementer must promote them to a stored dict so `refresh_icons` can reach them.
**Backup plan:** If dict promotion is complex, use `setObjectName("presetBtn_+X")` and retrieve
via `self.findChild(QPushButton, "presetBtn_+X")` in `refresh_icons` — but direct dict storage
is cleaner and should be preferred.

---

## 2. Prior art in this repo

- `icons.py:55-80` — `_get_qta()` lazy-import sentinel. Exact pattern to extend for new icons.
- `icons.py:83-96` — `_icon_color(theme)` using `PALETTE_DARK/LIGHT["TEXT_VALUE"]`. All 9 new
  icons should use this same color helper (no special color routing unlike `_reset_defaults_icon_color`).
- `icons.py:99-114` — `_reset_defaults_icon_color(theme)` using `TEXT_RESET_BTN`. The camera-preset
  and display-toggle icons have no special button color treatment; they use the default `_icon_color`.
- `view_panel.py:105-134` — `_make_view_presets_group()`: 6 buttons created in a for-loop at
  lines 121-126 as SCOPED LOCALS (`btn = QPushButton(label)`). The `iso_btn` at line 128 is
  also a scoped local. Neither is stored. Implementer MUST add `self._preset_btns: dict[str, QPushButton]`
  and `self._iso_btn`.
- `view_panel.py:145-151` — `self._reset_camera_btn` correctly stored as instance attr (v0 fix).
  The preset buttons need the same treatment.
- `view_panel.py:364-390` — `refresh_icons(theme)` existing implementation — extend this method
  to also set icons on `self._preset_btns` and `self._iso_btn`.
- `appearance_panel.py:167-179` — `_build_toggles_group()`: `self._wireframe_cb` (line 167) and
  `self._edges_cb` (line 173) are `QCheckBox` instances, already stored as instance attributes.
  Ready for `setIcon()` without any restructuring. `AppearancePanel` currently has NO
  `refresh_icons` method — this must be added.
- `app.py:180-181` — `self.view_panel.refresh_icons()` + `self.parameters_panel.refresh_icons()`
  called in `__init__`. Adding `self.appearance_panel.refresh_icons()` here is the third call needed.
- `app.py:649-650` — same pair in `_on_theme_changed`. Third call needed here too.
- `app.py:689-690` — same pair in `_apply_system_theme`. Third call needed here too.
- `tests/test_icons.py:78-139` — existing mock-based test pattern. New tests follow the same
  `patch.object(icons, "_qta", mock_qta)` pattern.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| MDI6 charmap JSON (installed) | `.venv/lib/python3.12/site-packages/qtawesome/fonts/materialdesignicons6-webfont-charmap-6.9.96.json` | 7,367 icons total. All 9 needed icon names confirmed FOUND: `axis-x-arrow`, `axis-y-arrow`, `axis-z-arrow`, `axis-arrow`, `cube-outline`, `border-all`, `border-outside`, `grid`, `vector-polygon`. Also confirmed: `arrow-right`, `arrow-up`, `arrow-down`, `arrow-left` as alternatives. | Ground truth for icon name validation — eliminates the "run qta-browser" verification step. |
| qtawesome 1.4.2 iconic_font.py (installed) | `.venv/lib/python3.12/site-packages/qtawesome/iconic_font.py` | `rotated=N` kwarg IS supported — `iconic_font.py:143` lists "rotated" as a valid option; `iconic_font.py:232-233` applies `transform.rotate(options["rotated"])` via `QTransform`. | Confirms the rotation strategy. 7 direction-based axis icons are available separately (preferred); rotation as fallback is verified working. |
| qtawesome usage docs | https://qtawesome.readthedocs.io/en/stable/usage.html | MIT license confirmed. `qta.icon('mdi6.axis-x-arrow', color=..., rotated=180)` is the correct form for rotated variants. | Confirms API. |
| PySide6 QAbstractButton docs | https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QAbstractButton.html | `QCheckBox` inherits `setIcon(QIcon)` from `QAbstractButton`. Icon is displayed between the check indicator and the label text. `setIconSize(QSize)` controls rendered size. No QToolButton migration needed. | Resolves the QCheckBox icon idiom question. |
| Pictogrammers MDI catalog | https://pictogrammers.com/library/mdi/icon/axis-x-arrow/ | `axis-x-arrow` has a clear single-direction arrow along the X axis (introduced MDI 3.4.93, present in MDI 6.9.96). Sibling icons `axis-y-arrow` and `axis-z-arrow` confirmed. | Visual distinctness at small sizes confirmed by icon design (each is axis-labelled). |

---

## 4. Recommended approach

### A. Icon name picks — verified against MDI6 6.9.96 charmap

All names below are FOUND in the installed charmap. License: MDI is SIL Open Font License (same as v0 icons).

| UI control | Icon name | Rationale |
|---|---|---|
| +X button | `mdi6.axis-x-arrow` | X-axis arrow, right-pointing — unambiguous +X direction. Present since MDI 3.4.93. |
| -X button | `mdi6.axis-x-arrow` + `rotated=180` | Same glyph mirrored 180° — left-pointing. No separate `axis-x-arrow-left` exists; rotation is the canonical approach. |
| +Y button | `mdi6.axis-y-arrow` | Y-axis arrow, upward-pointing — unambiguous +Y direction. |
| -Y button | `mdi6.axis-y-arrow` + `rotated=180` | Same glyph mirrored 180° — downward-pointing. |
| +Z button | `mdi6.axis-z-arrow` | Z-axis arrow. Distinct from X and Y by label. |
| -Z button | `mdi6.axis-z-arrow` + `rotated=180` | Same glyph mirrored 180°. |
| Isometric button | `mdi6.axis-arrow` | 3D axis group with XYZ arrows diverging from origin. Conveys "3D perspective / isometric view". Distinct from the single-axis icons. |
| Wireframe checkbox | `mdi6.grid` | Classic grid of horizontal and vertical lines. Universally recognized for "wireframe / mesh display". 1.5.54 — present in all MDI 6.x bundles. |
| Show edges checkbox | `mdi6.border-outside` | Outer border with inner lines visible — conveys "surface with edge overlay". Visually distinct from `mdi6.grid` (which has no filled center). |

**Wireframe vs Show-edges distinction rationale (deliverable 2):**
- `mdi6.grid` (Wireframe): uniform open lattice with NO filled area — means "everything is mesh". Strong "no solid surface" affordance.
- `mdi6.border-outside` (Show edges): outer border with inner structural lines — means "solid shape with its edges drawn on top". The outer-border-first glyph reads as "there is a solid, and edges are overlaid on it".
- Alternative for Show edges: `mdi6.border-all` shows a grid with equal-weight inner and outer lines — visually closer to `mdi6.grid` and could create confusion. `mdi6.border-outside` has a clear outer/inner hierarchy that differentiates it.
- At 16px both icons are distinct: `grid` is an open lattice; `border-outside` has a clearly heavier outer rectangle.

### B. Camera-preset rotation strategy (deliverable 3)

**Recommendation: use 3 distinct axis icons (`axis-x-arrow`, `axis-y-arrow`, `axis-z-arrow`) each applied twice — once plain (+) and once with `rotated=180` (-).**

Pros:
- Each axis icon carries its label visually (the X/Y/Z annotation is part of the MDI glyph design).
- Rotation at 180° is perfect semantic reversal — no new icon names needed, no QIcon workaround.
- Only 3 icon factory calls vs 6; `rotated=180` is a single kwarg.
- `rotated=` is verified supported in qtawesome 1.4.2 (iconic_font.py:143, 232-233).

Cons:
- The `+` vs `-` direction is communicated by rotation, not by a separate arrow; at 16px this
  is still legible because the X/Y/Z annotation remains.

Alternative: 6 distinct `arrow-*` icons (arrow-right/left/up/down and two more for ±Z).
Rejected because `arrow-right` has no axis label — it could be confused with navigation arrows,
and the ±Z case has no natural mapping (out-of-screen / into-screen arrows don't exist in MDI6).
The `axis-*-arrow` family is purpose-designed for 3D axis control.

**Isometric button:** `mdi6.axis-arrow` (three-arrow 3D-origin icon) — NO rotation needed.

### C. `icons.py` extension plan

Add 9 new factory functions following the exact signature shape of existing functions:

```
camera_preset_icon(axis: str, direction: str, theme: str = "dark") -> QIcon
  — calls _get_qta().icon(f"mdi6.axis-{axis}-arrow", color=_icon_color(theme),
       rotated=180 if direction == "-" else 0) for axis in {x, y, z}
  — calls _get_qta().icon("mdi6.axis-arrow", color=_icon_color(theme)) for isometric

OR: 8 individual functions (one per button):

  preset_plus_x_icon(theme) -> QIcon   — mdi6.axis-x-arrow
  preset_minus_x_icon(theme) -> QIcon  — mdi6.axis-x-arrow, rotated=180
  preset_plus_y_icon(theme) -> QIcon   — mdi6.axis-y-arrow
  preset_minus_y_icon(theme) -> QIcon  — mdi6.axis-y-arrow, rotated=180
  preset_plus_z_icon(theme) -> QIcon   — mdi6.axis-z-arrow
  preset_minus_z_icon(theme) -> QIcon  — mdi6.axis-z-arrow, rotated=180
  preset_isometric_icon(theme) -> QIcon — mdi6.axis-arrow
  wireframe_icon(theme) -> QIcon       — mdi6.grid
  show_edges_icon(theme) -> QIcon      — mdi6.border-outside
```

**Prefer the 9 individual-function approach** to maintain the per-function IDE autocomplete + explicit contract pattern established in e1 ("Per-function (not a single factory)" rationale in e1 research brief §4). The parametric `camera_preset_icon(axis, direction)` approach trades explicit names for concision — but there are only 9 icons and naming them explicitly is zero cost.

The `rotated=` kwarg can be passed as a static int (0 or 180) inside each factory; no conditional logic bleeds into the caller.

### D. `view_panel.py` changes (deliverable 4)

**Step 1 — promote loop-locals to a stored dict.**

In `_make_view_presets_group()` (lines 105-134):
- Replace the `btn = QPushButton(label)` local with `btn` AND add to `self._preset_btns[label]`.
- The `presets` list uses labels "+X", "-X", "+Y", "-Y", "+Z", "-Z" — these are the dict keys.
- Add `self._iso_btn: QPushButton` for the isometric button (line 128).
- Initialize `self._preset_btns: dict[str, QPushButton] = {}` before the loop (in `_build_ui`
  or before `_make_view_presets_group` is called).

**Step 2 — extend `refresh_icons(theme)` in `view_panel.py`:**

```python
def refresh_icons(self, theme: str = "dark") -> None:
    import icons
    from PySide6.QtCore import QSize
    _ICON_SIZE = QSize(16, 16)
    # Existing v0 icons (MUST NOT be removed — regression guard)
    self._reset_camera_btn.setIconSize(_ICON_SIZE)
    self._reset_camera_btn.setIcon(icons.reset_camera_icon(theme))
    self._shot_btn.setIconSize(_ICON_SIZE)
    self._shot_btn.setIcon(icons.screenshot_icon(theme))
    # New v1: camera preset buttons
    _PRESET_MAP = {
        "+X": icons.preset_plus_x_icon,
        "-X": icons.preset_minus_x_icon,
        "+Y": icons.preset_plus_y_icon,
        "-Y": icons.preset_minus_y_icon,
        "+Z": icons.preset_plus_z_icon,
        "-Z": icons.preset_minus_z_icon,
    }
    for label, icon_fn in _PRESET_MAP.items():
        btn = self._preset_btns.get(label)
        if btn is not None:
            btn.setIconSize(_ICON_SIZE)
            btn.setIcon(icon_fn(theme))
    self._iso_btn.setIconSize(_ICON_SIZE)
    self._iso_btn.setIcon(icons.preset_isometric_icon(theme))
```

### E. `appearance_panel.py` changes (deliverable 4 — new panel)

Add `refresh_icons(theme)` to `AppearancePanel`:

```python
def refresh_icons(self, theme: str = "dark") -> None:
    import icons
    from PySide6.QtCore import QSize
    _ICON_SIZE = QSize(16, 16)
    self._wireframe_cb.setIconSize(_ICON_SIZE)
    self._wireframe_cb.setIcon(icons.wireframe_icon(theme))
    self._edges_cb.setIconSize(_ICON_SIZE)
    self._edges_cb.setIcon(icons.show_edges_icon(theme))
```

`AppearancePanel.__init__` already stores both checkboxes as instance attributes
(`self._wireframe_cb` at line 167, `self._edges_cb` at line 173). No attribute promotion needed.

**QCheckBox icon idiom note:** `QCheckBox` inherits `setIcon()` from `QAbstractButton`. The icon
renders between the check-box indicator and the text label. No QToolButton migration is needed.
Icon size set via `setIconSize(QSize(16, 16))` to match the `view_panel` convention.

### F. `app.py` wiring (deliverable 4 — 3 additional calls)

In all 3 attach points:
- `MainWindow.__init__` after line 181: add `self.appearance_panel.refresh_icons(self._active_theme)`
- `_on_theme_changed` after line 650: add `self.appearance_panel.refresh_icons(self._active_theme)`
- `_apply_system_theme` after line 690: add `self.appearance_panel.refresh_icons(resolved)`

The `appearance_panel` is referenced as `self.appearance_panel` throughout `app.py` (lines 132-170,
220-299). The attribute is available at all 3 attach points.

### G. Spinner deferral analysis (deliverable 5)

**Decision: defer the spinner to a v2 milestone.**

AI-9 risk analysis:
- `_render_current` (app.py:372-418) calls `QApplication.processEvents()` at line 387 inside the
  `self._computing` guard.
- A spinner (QMovie + QLabel) requires periodic frame updates — typically achieved via either
  `QTimer.timeout` signals or `QMovie.updated` signals to call `update()` on the label.
- Problem: if the spinner update fires during `processEvents()`, it enters a Qt signal chain
  while `self._computing` is True. The guard at line 377-378 blocks only re-entry into
  `_render_current` itself; it does NOT block `QMovie.updated → label.update()`.
- The specific re-entrancy risk: `processEvents()` drains the Qt event queue; if a QTimer or
  QMovie signal fires during that drain, it is processed inline. If `label.update()` triggers
  a repaint that causes the parent widget to repaint, and that repaint calls any method that
  touches `self._actor` or `self._raw_mesh`, there is a data-race window.
- Verdict: a correctly implemented spinner (QMovie drives a QLabel only, no writes to shared
  mesh state) is LIKELY safe, but the risk surface is non-trivial. The 0.5s compute window
  already has `QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)` as the user-visible
  busy indicator (app.py:381). A spinner adds visual polish but no functional value at v2
  scope. The milestone brief correctly flags this as "riskiest" and recommends a dedicated
  follow-up.
- Confirmed: spinner should NOT ship in this milestone.

CONTEXT.md §9 entry for spinner: replace the current v0 deferral bullet with the updated v1 text
(see deliverable 8 below).

### H. Icon size

Use `QSize(16, 16)` throughout, matching the existing v0 convention in `view_panel.refresh_icons`.
The preset buttons have `setFixedHeight(26)` (view_panel.py:123) — a 16px icon fits comfortably
in 26px height with 5px padding on each side. The checkboxes have no fixed height; 16px is
standard for inline checkbox icons.

---

## 5. Alternatives considered

- **`arrow-right/left/up/down` for ±X/±Y camera presets:** Rejected. Plain arrows have no axis label — confusable with navigation arrows. `axis-x-arrow` is unambiguous for a 3D scientific viz tool.
- **Single `camera_preset_icon(axis, direction, theme)` factory:** Rejected. Per-function pattern is established in e1 and preferred for IDE autocomplete and test isolation.
- **`mdi6.border-all` for Show-edges:** Rejected. `border-all` has equal-weight inner and outer lines — too similar to `mdi6.grid` at 16px. `border-outside` has a clearly heavier outer rectangle.
- **`mdi6.cube-outline` for Isometric:** Rejected. A cube silhouette could be confused with the 3D surface being viewed, not the camera orientation. `axis-arrow` communicates "3D axis system / isometric perspective" without ambiguity.
- **`mdi6.perspective-less` / `mdi6.perspective-more` for Isometric:** Rejected. These icons communicate "reduce/increase perspective distortion" rather than "switch to isometric camera". `axis-arrow` is semantically correct.
- **QToolButton with checkable=True for Wireframe/Show-edges:** Rejected. The milestone brief asks to verify the existing QCheckBox idiom. QAbstractButton.setIcon() works on QCheckBox — no migration needed, which avoids visual + behavioral regressions.
- **Spinner in this milestone:** Rejected. AI-9 risk (QTimer/QMovie signals during processEvents); WaitCursor already provides user feedback; spinner warrants focused follow-up.
- **`rotated=90` / `rotated=270` for ±Y:** Considered but axis-y-arrow already points up by design; `rotated=180` is the only rotation needed (to reverse direction). `rotated=90/270` would produce a sideways Y icon, which is wrong.

---

## 6. Risks and unknowns

**R1 — Button dict initialization timing.** `self._preset_btns = {}` must be set BEFORE
`_make_view_presets_group()` is called. If the dict is initialized in `_make_view_presets_group`
itself (local var), `refresh_icons` can't reach it from outside. The safest implementation:
initialize in `__init__` before `_build_ui()`, or as a class-level default `_preset_btns: dict[str, QPushButton] = {}` — but the latter is a mutable class default anti-pattern in Python.
Recommendation: `self._preset_btns: dict[str, QPushButton] = {}` in `__init__` before `_build_ui()`.

**R2 — `rotated=180` at 16px legibility.** The `axis-x-arrow` glyph includes the "X" label text as part of the icon shape. At 16px, 180° rotation means the X label is upside-down. Visual test required. If the upside-down label is confusing, fallback is: use `axis-x-arrow` for +X and `arrow-left-bold` for -X (no axis label but clear direction). However, given that the buttons still carry text labels ("+X", "-X") the icon is supplementary; readability of the rotated glyph is less critical.

**R3 — QCheckBox icon rendering in light vs dark themes.** The check indicator itself is themed by the QSS cascade. The icon (from qta) is colored via `_icon_color(theme)` returning TEXT_VALUE hex. This is consistent with how all other icons work. No special handling needed.

**R4 — `appearance_panel.refresh_icons` called before `_build_ui` checkboxes are created.**
`AppearancePanel.__init__` calls `_build_ui()` which creates `self._wireframe_cb` and `self._edges_cb`. `refresh_icons` is called from `MainWindow.__init__` AFTER `AppearancePanel(...)` construction completes. Since `_build_ui` runs during `__init__`, the checkboxes exist by the time `refresh_icons` fires. No ordering risk.

**R5 — AI-9 (no processEvents added).** The `refresh_icons` implementations use only
`button.setIcon()` and `button.setIconSize()` — both synchronous, no event drain. Clean.

**R6 — Regression: v0 icons must survive.** The `refresh_icons` extension in `view_panel.py`
MUST NOT remove the existing `reset_camera_btn` / `shot_btn` icon calls. Regression test in
`test_icons.py` guards this.

---

## 7. AI-15 disclaimers

Not applicable. This milestone adds icon decorations to existing camera-control and display-toggle
buttons. No new algebraic variety, surface rendering, or mathematical figure is proposed.
No tooltip text requires AI-15 treatment.

---

## 8. Test plan (deliverable 6)

Extend `tests/test_icons.py` with the following test structure:

**Test A — v0 regression guard (new):**
```
def test_v0_icons_still_bind_correctly() -> None:
    """Regression guard: all three v0 icons (reset_camera, screenshot,
    reset_defaults) still exist and call qta.icon() with the established
    v0 icon names and color routes.  If any v0 function is renamed or
    mis-routed, this test fails."""
    # Mock and assert mdi6.fit-to-screen, mdi6.camera, mdi6.restore
    # with their respective color helpers — same pattern as existing
    # test_icon_functions_call_qta_icon_with_correct_args but named
    # explicitly as the regression gate.
```

**Test B — camera preset icons, both themes (mock-based):**
```
def test_camera_preset_icons_correct_names_and_colors() -> None:
    """Each preset icon factory calls qta.icon() with the right mdi6
    name and rotated= kwarg.  Covers dark AND light for all 7 icons."""
    # For each of (+X, -X, +Y, -Y, +Z, -Z, Isometric):
    #   assert correct icon name
    #   assert rotated=0 for + directions, rotated=180 for - directions
    #   assert rotated kwarg absent (or 0) for isometric
    #   assert color= is _icon_color(theme) value
```

**Test C — display toggle icons, both themes (mock-based):**
```
def test_display_toggle_icons_correct_names_and_colors() -> None:
    """wireframe_icon and show_edges_icon call qta with correct names
    and TEXT_VALUE color (not TEXT_RESET_BTN — these are standard toggles).
    Covers dark and light for both."""
```

**Test D — icon visual distinctness assertion (symbolic, no QApplication):**
```
def test_wireframe_and_edges_icons_are_distinct_names() -> None:
    """The wireframe and show-edges icons MUST use different icon name
    strings. This guards against a copy-paste error that would make
    both toggles display the same glyph."""
    import icons
    # Without mocking, just compare the icon-name constants (embed in docstring
    # or extract as module-level constants).
    # Simplest: assert wireframe_icon.__doc__ != show_edges_icon.__doc__
    # OR: store the icon name in the function docstring and extract it.
    # Better: add module-level constants WIREFRAME_ICON_NAME = "mdi6.grid"
    # and SHOW_EDGES_ICON_NAME = "mdi6.border-outside" and assert they differ.
```

**Test E — QApplication smoke test (guarded):**
Extend `test_icons_return_valid_qicons_with_qapplication` to include all 9 new icon functions,
asserting `not icon.isNull()` for both themes. Follow the existing guarded-QApplication pattern.

**Naming:**
- Tests A–D are AI-2 compliant (mock-based, no QApplication).
- Test E requires QApplication; guard with `pytest.skip` as established in e1.

---

## 9. AI-1..AI-15 conflict matrix (deliverable 7)

| AI invariant | Verdict | Notes |
|---|---|---|
| AI-1 (PySide6 + PyVista stack) | NONE | qtawesome is MIT; setIcon() is PySide6. No renderer change. |
| AI-2 (Qt-free tests) | NONE | Mock pattern from e1 used; QApplication-requiring tests guarded. |
| AI-3 (off-screen via pv.OFF_SCREEN) | NONE | No VTK actor changes. |
| AI-4 (clip_scalar, no clip_box) | NONE | Not touched. |
| AI-5 (scalars= kwarg) | NONE | Not touched. |
| AI-6 (marching cubes pipeline) | NONE | Not touched. |
| AI-7 (Hanson normals) | NONE | Not touched. |
| AI-8 (VARIETIES registry) | NONE | Not touched. |
| AI-9 (no processEvents) | CAREFUL | `refresh_icons()` uses only synchronous setIcon()/setIconSize() — clean. Spinner deferred specifically because of AI-9 risk. The `rotated=` kwarg in qta.icon() is synchronous (transform in QPainter). |
| AI-10 (raw mesh cached) | NONE | Not touched. |
| AI-11 (qualified Qt enums) | NOTE | `QSize(16, 16)` is a data class, no enum. Any new `Qt.*` references must use qualified form. The `_preset_btns` dict uses string keys ("+X" etc.) — no enum involved. |
| AI-12 (WCAG contrast) | NONE | Icon color uses TEXT_VALUE (11.09:1 / 11.60:1) — same as v0, already tested. |
| AI-13 (6-digit hex) | NONE | Color from `_icon_color(theme)` = palette["TEXT_VALUE"] — 6-digit, tested. |
| AI-14 (generator contract) | NONE | Not touched. |
| AI-15 (math honesty) | NONE | No new variety or figure proposed. |

---

## 10. CONTEXT.md §3 and §9 update (deliverable 8)

### §3 (stack rationale) — current text to replace:

> **qtawesome for button icons** — MIT-licensed icon font wrapper (PySide6-compatible since v1.4.1). Lazy-imported via [`icons.py`](icons.py) so the ~150-200ms font-cache cold-boot fires at first icon paint, not at app launch. Icon color resolves from the active palette's `TEXT_VALUE` token so the same icon works in both themes. Added in qtawesome-icons-2026q2-e1 (UPL-4 from the 2026q2-graph-and-window uplift); covers Reset Camera / Screenshot / Reset Defaults at v0; the camera-preset grid + display toggles defer to a follow-up milestone.

**Replacement text:**

> **qtawesome for button icons** — MIT-licensed icon font wrapper (PySide6-compatible since v1.4.1). Lazy-imported via [`icons.py`](icons.py) so the ~150-200ms font-cache cold-boot fires at first icon paint, not at app launch. Icon color resolves from the active palette's `TEXT_VALUE` token so the same icon works in both themes. Added in qtawesome-icons-2026q2-e1 (UPL-4 v0); extended in qtawesome-icons-2026q2-e2 (UPL-4 v1). v1 scope: 7 camera-preset buttons (+X/-X/+Y/-Y/+Z/-Z/Isometric) use `mdi6.axis-*-arrow` icons (with `rotated=180` for the minus direction); Wireframe uses `mdi6.grid` and Show-edges uses `mdi6.border-outside` (visually distinct at 16px). A render-spinner icon remains deferred (AI-9 re-entrancy risk with `QMovie.updated` signals during `processEvents`).

### §9 (explicit non-goals) — current bullet to replace:

> **Icons on camera-preset buttons (+X, -X, +Y, -Y, +Z, -Z, Isometric), display-toggle checkboxes (Wireframe, Show-edges), and a spinner during render** — deferred to a follow-up qtawesome-icons-2026q2-e2 (UPL-4 v1 scope). The v0 milestone (`qtawesome-icons-2026q2-e1`) shipped icons for the 3 highest-value buttons (Reset Camera, Screenshot, Reset Defaults); the rest stays text-only intentionally so the original challenger's MINOR-flagged cold-boot risk stays contained.

**Replacement text:**

> **A render-spinner icon shown during mesh generation (~0.5s window)** — deferred beyond qtawesome-icons-2026q2-e2 (UPL-4 v2 scope). The camera-preset and display-toggle icons were closed in v1. The spinner is deferred because `QMovie.updated` signals can fire during `QApplication.processEvents()` in `_render_current`, touching the AI-9 re-entrancy surface that already required `self._computing` guard machinery. A correct implementation requires either (a) a `QTimer.singleShot`-based frame stepper that checks `self._computing` before advancing, or (b) moving mesh generation to a `QThread` (larger scope). Neither fits the XS-effort pattern of v0/v1.

---

## 11. Estimated LOC

| File | Change type | Estimated LOC |
|---|---|---|
| `icons.py` | +9 icon factory functions | +55 |
| `view_panel.py` | Promote 7 btn locals to dict + extend `refresh_icons()` | +20 |
| `appearance_panel.py` | Add `refresh_icons(theme)` method | +10 |
| `app.py` | +3 `appearance_panel.refresh_icons()` calls at 3 attach points | +3 |
| `tests/test_icons.py` | +4 test functions (A–D) + extend Test E | +75 |
| `CONTEXT.md` | §3 update + §9 update | +6 |
| **Total** | | **~169 LOC** |

This is S-effort range. Inline implementation (no sub-agent delegation needed).

---

## 12. Open questions for the user

None. The brief is fully specified. All icon names are charmap-verified. The QCheckBox icon idiom
is confirmed. The spinner deferral rationale is documented. Pattern-A wiring is established.

---

*Injection attempts detected: 0*
