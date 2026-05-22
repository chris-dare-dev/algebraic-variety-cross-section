# Research Brief — variety-palette-2026q2-e1
**Agent:** solo
**Date:** 2026-05-21
**Status:** complete

---

## 1. TL;DR

Populate the four-entry `VARIETY_DEFAULT_COLOR` dict in `styles.py` with WCAG-verified 6-digit hex values, add a `set_default_color(hex_str)` method to `AppearancePanel`, wire it in `app.py`'s `_on_variety_changed` and `_on_subtype_changed` handlers, and add four contrast-check test functions to `tests/test_styles_palette.py`. The main risk is that the existing stub-guard test (`test_variety_default_color_is_stub_for_upl5`) asserts `== {}` and must be replaced, not supplemented. The backup plan for any color that proves hard to calibrate is to use the computed WCAG-safe values below verbatim — all four have been numerically verified.

---

## 2. Prior Art in This Repo

- `styles.py:99-107` — `VARIETY_DEFAULT_COLOR: dict[str, str] = {}` stub with comment specifying key format and AI-13 constraint. The comment at line 102 explicitly warns: "Verify the exact spelling against surfaces.py before adding entries; a mismatched key silently misses the lookup."
- `styles.py:49-96` — `PALETTE_LIGHT` dict is the pattern to mirror; every value is 6-digit hex with inline WCAG annotations.
- `styles.py:110-123` — `PALETTE_DARK` placeholder comment. The forward-compat note for UPL-4 says to add a parallel `PALETTE_DARK` with identical keys. The brief should recommend a parallel `VARIETY_DEFAULT_COLOR_DARK` marker at the same location — not populated in this milestone, just the comment hook.
- `appearance_panel.py:57-91` — `AppearancePanel.__init__` initializes `self._surface_color = QColor(BG_SURFACE_DEFAULT)` at line 83. The `set_default_color` method inserts here.
- `appearance_panel.py:301-319` — `apply_to_actor` reads `self._surface_color.name()` at line 313 to color the actor. `set_default_color` must update `self._surface_color` AND refresh `self._surf_swatch` so the color chip in the UI reflects the family default on switch.
- `appearance_panel.py:227-239` — `_pick_surface_color` is the existing method that mutates `self._surface_color` and updates `self._surf_swatch`. The `set_default_color` implementation mirrors this pattern (set field, call `_apply_swatch_color`) without triggering a render — the caller (`_on_subtype_changed`) already calls `_render_current` which calls `apply_to_actor`.
- `app.py:175-221` — `_on_variety_changed`. The wire point is after line 187 (`self._set_subtype_enabled(True)`) for each `if name in VARIETIES` branch. Use `VARIETY_DEFAULT_COLOR.get(name, BG_SURFACE_DEFAULT)`.
- `app.py:223-243` — `_on_subtype_changed`. The wire point is after line 234 (`surface = VARIETIES[variety][name]`), before `parameters_panel.set_specs`. The variety key is `variety = self.variety_combo.currentText()`.
- `app.py:399` — `self.appearance_panel.apply_to_actor(self._actor)` — this is where the color already flows to the actor. No change needed here; `set_default_color` updates `_surface_color` ahead of this call so `apply_to_actor` reads the new value automatically.
- `tests/test_styles_palette.py:133-138` — `test_variety_default_color_is_stub_for_upl5`. This test asserts `styles.VARIETY_DEFAULT_COLOR == {}`. IT MUST BE REPLACED (not supplemented) by the new tests that assert the four keys and their contrast ratios.
- `tests/test_styles_palette.py:141-169` — `test_critical_text_tokens_meet_wcag_aa_on_bg_panel` — contains the canonical `luminance()` and `ratio()` helpers. Copy these verbatim into the new test functions (or extract into a module-level helper at the top of the test file; extraction is cleaner and avoids duplication).
- `surfaces.py:945-986` — `VARIETIES` dict outer keys. VERBATIM keys confirmed:
  - `"K3 surface"` (line 946)
  - `"Enriques surface"` (line 950)
  - `"Calabi–Yau 3-fold"` (line 968) — NOTE: this uses the Unicode en-dash `–` (U+2013), NOT an ASCII hyphen. The comment in `styles.py:102` says "ASCII hyphen" but that is WRONG — the actual key uses U+2013. Copy from surfaces.py, do not retype.
  - `"Fano 3-fold (ρ=1)"` (line 986) — NOTE: `ρ` is U+03C1 (Greek small letter rho), not the ASCII `p`.

---

## 3. External Sources Reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Prior frontier-uplift challenge.md | repo-local | `#5e7fb8` fails 4.5:1 (3.4:1 measured), `#b89878` borderline (4.5:1), `#7a92b8` marginal (4.7:1), `#7ba872` at 3.7:1; challenger demands re-audit. | Direct input to hex selection |
| Prior frontier-uplift synthesis.md | repo-local | UPL-2 = variety family color tokens; UPL-4 dark-mode adds `VARIETY_DEFAULT_COLOR_DARK`; forward-compat structure stated explicitly | Confirms scope and dark-mode hook |
| CONTEXT.md §4.3 render pipeline | repo-local | `_apply_domain_and_render` calls `appearance_panel.apply_to_actor(self._actor)` at `app.py:399` after `add_mesh` | Confirms color flows through `apply_to_actor` — no second color-apply path exists |
| WCAG 2.1 §1.4.3 / §1.4.11 | W3C spec (from AI-12 invariant) | Text contrast ≥4.5:1; non-text UI ≥3:1. Status-bar surface name renders in the actor color — it IS text → 4.5:1 threshold applies | Determines which threshold to use |

No arXiv or GitHub OSS searches were needed — this milestone is a pure palette/wiring task with no novel math or new visualization library requirements.

---

## 4. Recommended Approach

### 4A. Final hex values (numerically verified)

All four computed against `BG_VIEWPORT = #2f2f2f`:

| Variety | Hex | WCAG ratio | Hue (HSV) | Character |
|---|---|---|---|---|
| `"K3 surface"` | `#8e9ed4` | 5.09:1 PASS | 226 deg (periwinkle) | Cool blue-violet — steely, mathematical |
| `"Enriques surface"` | `#c4a882` | 5.91:1 PASS | 35 deg (warm amber) | Warm ochre — classical geometry register |
| `"Calabi–Yau 3-fold"` | `#85b5d0` | 6.07:1 PASS | 202 deg (teal-cobalt) | Elegant Universe teal — Hanson tradition |
| `"Fano 3-fold (ρ=1)"` | `#8fbe85` | 6.29:1 PASS | 109 deg (sage green) | Sage green — distinct from all three blues |

Pairwise hue separations: K3-Enr 168 deg, K3-CY3 25 deg, K3-Fan 117 deg, Enr-CY3 167 deg, Enr-Fan 75 deg, CY3-Fan 92 deg. All separations are ≥25 degrees — perceptually distinct even for mild color-vision deficiencies.

Note on K3 vs CY3: the 25-degree separation is the smallest but is the most acceptable pair, because K3 (warm purple-blue, periwinkle direction) and CY3 (teal-blue, ocean direction) are semantically the most different varieties in the registry and the hue lean is visually obvious at normal viewing distances.

### 4B. styles.py changes (lines 99-107)

Replace the empty dict with four entries. Keep the existing comment block. Add a forward-compat comment for `VARIETY_DEFAULT_COLOR_DARK` immediately after (parallel to the `PALETTE_DARK` placeholder at line 110-123). Do NOT add the dark dict — just a comment hook.

Exact key spelling: copy keys from `surfaces.py:946,950,968,986` character-for-character. The en-dash in "Calabi–Yau" and the rho in "Fano 3-fold (ρ=1)" must be the Unicode characters, not ASCII substitutes.

### 4C. appearance_panel.py — add set_default_color

Add a public method at the end of the Public API section (after line 319, before EOF):

```
def set_default_color(self, hex_str: str) -> None:
    """Seed the surface color from the variety-family default.

    Called by MainWindow on variety / subtype switch.  The user's subsequent
    override via the 'Surface...' swatch still wins — this only sets the
    starting point.  Does NOT trigger a render; the caller is responsible for
    calling _render_current or apply_to_actor after switching surfaces.
    """
    color = QColor(hex_str)
    if not color.isValid():
        return
    self._surface_color = color
    _apply_swatch_color(self._surf_swatch, color)
```

No `get_plotter().render()` call — the caller (`_on_variety_changed` / `_on_subtype_changed`) flows naturally into `_render_current` → `apply_to_actor`.

### 4D. app.py wiring — two call sites

**Import change at line 31:**
```python
from styles import APP_STYLESHEET, COLOR_WIREFRAME_OVERLAY, VARIETY_DEFAULT_COLOR, BG_SURFACE_DEFAULT
```
(Add `VARIETY_DEFAULT_COLOR` and `BG_SURFACE_DEFAULT` to the import.)

**In `_on_variety_changed` (around line 187), after `self._set_subtype_enabled(True)` and before the CY3/Fano `if name ==` block:**
```python
self.appearance_panel.set_default_color(
    VARIETY_DEFAULT_COLOR.get(name, BG_SURFACE_DEFAULT)
)
```
This seeds the panel's color when the variety combo changes, before a subtype is selected. It is safe to call even before any actor exists — `set_default_color` only mutates `_surface_color` and the swatch label.

**In `_on_subtype_changed` (around line 234), after `surface = VARIETIES[variety][name]`:**
```python
self.appearance_panel.set_default_color(
    VARIETY_DEFAULT_COLOR.get(variety, BG_SURFACE_DEFAULT)
)
```
This re-seeds on every subtype switch, implementing the V0 scope: "when the user switches K3 → Enriques → back to K3, K3 re-seeds from family default, not from any prior user-override."

**AI-9 safety:** Both call sites are outside `_render_current`. `_on_variety_changed` does not call `_render_current` (it only populates the subtype combo). `_on_subtype_changed` calls `_render_current` at line 243 AFTER the wiring point — `set_default_color` updates `_surface_color` before `apply_to_actor` reads it at line 399, so the render picks up the new color automatically.

### 4E. tests/test_styles_palette.py

Replace `test_variety_default_color_is_stub_for_upl5` (lines 133-138) with four new test functions. Extract `luminance()` and `ratio()` from `test_critical_text_tokens_meet_wcag_aa_on_bg_panel` into module-level helpers at the top of the test file to avoid duplication.

New tests:

```
def test_variety_default_color_has_all_four_families() -> None:
    """UPL-5: VARIETY_DEFAULT_COLOR must have exactly the four family keys."""
    expected = {"K3 surface", "Enriques surface", "Calabi–Yau 3-fold", "Fano 3-fold (ρ=1)"}
    assert set(styles.VARIETY_DEFAULT_COLOR.keys()) == expected

def test_variety_default_color_all_six_digit_hex() -> None:
    """AI-13: all variety colors must be 6-digit hex."""
    ...

def test_variety_default_color_wcag_on_bg_viewport() -> None:
    """AI-12: all variety colors must clear 4.5:1 against BG_VIEWPORT (text threshold,
    because the surface name appears in the status bar in this color)."""
    bg = styles.PALETTE_LIGHT["BG_VIEWPORT"]
    for variety, color in styles.VARIETY_DEFAULT_COLOR.items():
        r = ratio(color, bg)
        assert r >= 4.5, f"{variety} ({color}) fails 4.5:1 on BG_VIEWPORT: {r:.2f}:1"

def test_variety_default_color_keys_match_surfaces_varieties() -> None:
    """Keys in VARIETY_DEFAULT_COLOR must be present in surfaces.VARIETIES."""
    from surfaces import VARIETIES
    for key in styles.VARIETY_DEFAULT_COLOR:
        assert key in VARIETIES, f"{key!r} not in VARIETIES — key mismatch"
```

The fourth test (`test_variety_default_color_keys_match_surfaces_varieties`) is a forward-compat guard: any future variety rename that mismatches the dict key will be caught immediately.

### 4F. Forward-compat hook for UPL-1 dark mode

Add to `styles.py` immediately after the populated `VARIETY_DEFAULT_COLOR` dict, before the PALETTE_DARK comment block:

```python
# UPL-4 dark-mode parallel: VARIETY_DEFAULT_COLOR_DARK will live here with
# key-identical entries tuned for a dark panel background (BG_PANEL_DARK).
# Do NOT add it in this milestone — populate in UPL-4 alongside PALETTE_DARK.
# The same set_default_color(hex_str) call site in app.py reads from whichever
# dict is active; the only change UPL-4 needs is to route the .get() call
# through the active theme dict rather than the hardcoded VARIETY_DEFAULT_COLOR.
```

This is comment-only. The implementer does NOT add the dark dict.

---

## 5. Alternatives Considered

- **Use BG_SURFACE_DEFAULT (#b0c4de) for all families and leave VARIETY_DEFAULT_COLOR empty** — rejected: the stub exists precisely to give per-family identity; the visual scout's M-1 gap was "identical color erases visual differentiation."
- **Derive color from VARIETIES on-demand in app.py instead of a static dict** — rejected: the static dict in styles.py is already reserved and documented; on-demand derivation requires app.py to know about color logic, violating the centralized-palette invariant.
- **Wire set_default_color only in _on_subtype_changed, not _on_variety_changed** — rejected: when the user opens the variety combo and pauses (no subtype selected), the swatch should already reflect the incoming family's color. Wiring both handlers is correct.
- **Persist the family default as the user's color (no re-seed on switch-back)** — explicitly out of scope per the brief: "K3 should re-seed from the family default, not the user's prior red override." V0 intentionally does not persist user overrides.
- **Use lighter colors (higher luminance) to get more margin above 4.5:1** — rejected: the brief specifies "research-credible, restrained scientific palette, not marketing-grade saturation." Going much lighter produces washed-out pastels that lose the 3Blue1Brown / Quanta register. All four chosen values are within 1.3 contrast units of the 4.5:1 floor — deliberately restrained.

---

## 6. Risks and Unknowns

**AI-12 (text contrast threshold):** The status-bar surface name is rendered text, not a non-text UI element. This means 4.5:1 (not 3:1) applies against `BG_VIEWPORT = #2f2f2f`. All four proposed colors clear 4.5:1 with margin (5.09, 5.91, 6.07, 6.29 respectively). The status-bar text color is set by the `QStatusBar { color: ... }` rule in `APP_STYLESHEET` using `TEXT_MUTED`, but the surface name itself is not in the status bar color — it's in the actor color used on the 3D mesh. The concern from the challenger is specifically that the status-bar line reads "`Hanson quintic CY cross-section...`" using the same color that the mesh uses on the dark viewport. Confirmed: the mesh color (`actor.prop.color`) does NOT flow into the status-bar text color. The text in the status bar uses `TEXT_MUTED = #5a5a5a` on `BG_PANEL = #f0f0f0` (6.05:1 — passing). The 4.5:1 requirement against `BG_VIEWPORT` applies only to the mesh surface color as it appears on the dark canvas. All four pass at this threshold.

**AI-13 (6-digit hex):** All four proposed values are 6-digit. The test `test_every_palette_value_is_six_digit_hex` does NOT cover `VARIETY_DEFAULT_COLOR` — only `PALETTE_LIGHT`. The new test `test_variety_default_color_all_six_digit_hex` closes this gap.

**AI-9 (re-entrancy):** `set_default_color` must NOT call `get_plotter().render()`. Confirmed: the implementation above does not. The render flows from `_on_subtype_changed` → `_render_current` → `apply_to_actor` in the normal call chain. No additional `processEvents()` call is introduced.

**Unicode key mismatch risk:** "Calabi–Yau 3-fold" uses U+2013 (en-dash), not U+002D (hyphen). "Fano 3-fold (ρ=1)" uses U+03C1 (rho). Both must be copy-pasted from `surfaces.py:968,986`, not retyped. A silent lookup miss returns `BG_SURFACE_DEFAULT` (the fallback), which is hard to detect at runtime. The test `test_variety_default_color_keys_match_surfaces_varieties` catches this at test time.

**Stub test replacement:** `test_variety_default_color_is_stub_for_upl5` at `tests/test_styles_palette.py:133-138` asserts `== {}`. If the implementer adds the new tests WITHOUT removing this one, the test suite will have a contradiction (the stub test fails, new tests pass). The stub test must be deleted and replaced.

**BG_SURFACE_DEFAULT import in app.py:** Currently `app.py:31` imports `APP_STYLESHEET` and `COLOR_WIREFRAME_OVERLAY` from styles. `BG_SURFACE_DEFAULT` is already exported from styles (line 146) but is not yet imported in app.py. Adding it to the import line is required for the `VARIETY_DEFAULT_COLOR.get(name, BG_SURFACE_DEFAULT)` fallback.

**set_default_color when _surf_swatch not yet created:** `_build_ui()` is called from `__init__` before any external code can call `set_default_color`, so `self._surf_swatch` will always exist when `set_default_color` is called from app.py. No guard needed.

---

## 7. AI-15 Disclaimers

This milestone does not propose any new variety or figure. It only assigns colors to existing families. No AI-15 obligation arises.

---

## 8. Open Questions for the User

None. The brief is fully specified. All hex values are numerically verified, all file:line attach points are confirmed, and the test strategy is unambiguous.
