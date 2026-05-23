"""Regression guards for the PALETTE_LIGHT token dict (UPL-1).

These tests are Qt-free (AI-2) — they import only the ``styles`` module
which has no Qt dependencies until its constants are consumed by Qt
widgets.  ``styles.py`` itself is a plain Python module of string
constants and an f-string.
"""
from __future__ import annotations

import re

import styles


HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")


# --- WCAG contrast helpers (module-level so multiple tests share them) -------
# Extracted from test_critical_text_tokens_meet_wcag_aa_on_bg_panel during
# variety-palette-2026q2-e1 so the new VARIETY_DEFAULT_COLOR tests below can
# use the same canonical implementation.  The local nested copy in that test
# is left in place for backward-compat readability of its self-contained
# fixture; this module-level pair is the source of truth for new callers.


def _luminance(hex_color: str) -> float:
    """WCAG 2.x relative luminance (0.0 .. 1.0) from a 6-digit hex color."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _ratio(fg: str, bg: str) -> float:
    """WCAG 2.x contrast ratio between two 6-digit hex colors (>=1.0)."""
    l1, l2 = _luminance(fg), _luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def test_palette_light_has_minimum_tokens() -> None:
    """UPL-1 brief requires at least 6 named tokens covering the core roles."""
    required = {
        "BG_VIEWPORT",
        "BG_PANEL",
        "TEXT_VALUE",
        "TEXT_MUTED",
        "FOCUS_RING",
        "BG_SURFACE_DEFAULT",
    }
    missing = required - set(styles.PALETTE_LIGHT)
    assert not missing, f"PALETTE_LIGHT missing required tokens: {missing}"
    assert len(styles.PALETTE_LIGHT) >= 6


def test_every_palette_value_is_six_digit_hex() -> None:
    """AI-13 — PyVista (and the codebase convention) require 6-digit hex.

    No 3-digit short hex (#888) and no named-color shorthand (red, blue)
    are permitted in the palette dict.
    """
    offenders = {
        token: value
        for token, value in styles.PALETTE_LIGHT.items()
        if not HEX6.match(value)
    }
    assert not offenders, (
        f"PALETTE_LIGHT contains non-6-digit-hex values: {offenders}"
    )


def test_pyvista_bound_tokens_are_present() -> None:
    """Tokens flowing into ``plotter.set_background`` / ``add_mesh(color=)`` /
    ``actor.prop.color =`` must exist so the call sites can import them."""
    pyvista_bound = {"BG_VIEWPORT", "BG_SURFACE_DEFAULT", "COLOR_WIREFRAME_OVERLAY"}
    missing = pyvista_bound - set(styles.PALETTE_LIGHT)
    assert not missing, (
        f"PyVista-bound tokens missing from PALETTE_LIGHT: {missing}"
    )


def test_backward_compat_named_constants_match_palette() -> None:
    """The legacy named constants (``COLOR_MUTED`` etc.) must be aliases
    that read from PALETTE_LIGHT — not stale copies of the prior values.
    """
    assert styles.COLOR_MUTED == styles.PALETTE_LIGHT["TEXT_MUTED"]
    assert styles.COLOR_VALUE == styles.PALETTE_LIGHT["TEXT_VALUE"]
    assert styles.COLOR_DOCK_HEADER_BG == styles.PALETTE_LIGHT["BG_DOCK_HEADER"]
    assert styles.COLOR_DOCK_HEADER_BORDER == styles.PALETTE_LIGHT["BORDER_DOCK_HEADER"]
    assert styles.COLOR_RESET_BTN_BG == styles.PALETTE_LIGHT["BG_RESET_BTN"]
    assert styles.COLOR_RESET_BTN_BORDER == styles.PALETTE_LIGHT["BORDER_RESET_BTN"]
    assert styles.COLOR_RESET_BTN_HOVER_BG == styles.PALETTE_LIGHT["BG_RESET_BTN_HOVER"]


def test_new_named_exports_match_palette() -> None:
    """New named exports added in UPL-1 must also be live aliases."""
    assert styles.BG_VIEWPORT == styles.PALETTE_LIGHT["BG_VIEWPORT"]
    assert styles.BG_SURFACE_DEFAULT == styles.PALETTE_LIGHT["BG_SURFACE_DEFAULT"]
    assert styles.BORDER_SWATCH == styles.PALETTE_LIGHT["BORDER_SWATCH"]
    assert styles.COLOR_WIREFRAME_OVERLAY == styles.PALETTE_LIGHT["COLOR_WIREFRAME_OVERLAY"]


def test_no_raw_hex_in_pyvista_color_kwargs_at_app_py() -> None:
    """Regression guard for the e2 rectify-loop finding (M1/Frontend-HIGH):

    The app.py:364 orphan slipped through UPL-1's first pass because the
    original regression test only scanned APP_STYLESHEET, not the actual
    PyVista call sites in app.py.  This test reads app.py as source text
    and asserts no ``color="#xxxxxx"`` literal appears — every PyVista
    color argument must go through the palette tokens.

    See ``.claude/notes/milestones/panel-refresh-2026q2-e2/artifacts/adversary-critique.md``
    M1 / Frontend-HIGH for the original finding.
    """
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    source = (repo_root / "app.py").read_text(encoding="utf-8")
    # Match any color="#xxx" or color="#xxxxxx" literal in app.py source.
    raw_color_re = re.compile(r'color\s*=\s*"#[0-9a-fA-F]{3,6}"')
    leaks = raw_color_re.findall(source)
    assert not leaks, (
        f"app.py contains raw hex literals in color= kwargs: {leaks}. "
        f"Route all PyVista color args through PALETTE_LIGHT tokens."
    )


def test_no_raw_hex_in_pyvista_color_kwargs_at_appearance_panel() -> None:
    """Same guard for appearance_panel.py — the other PyVista call surface."""
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    source = (repo_root / "appearance_panel.py").read_text(encoding="utf-8")
    raw_color_re = re.compile(r'color\s*=\s*"#[0-9a-fA-F]{3,6}"')
    leaks = raw_color_re.findall(source)
    assert not leaks, (
        f"appearance_panel.py contains raw hex literals in color= kwargs: "
        f"{leaks}. Route all PyVista color args through PALETTE_LIGHT tokens."
    )


def test_app_stylesheet_substitutes_no_raw_hex_outside_palette() -> None:
    """APP_STYLESHEET must contain only hex values that appear in PALETTE_LIGHT.

    This catches drift where a future contributor adds a new QSS rule
    with an inline hex literal instead of going through the palette.
    """
    # Find every #xxxxxx or #xxx in the rendered stylesheet
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,6}\b")
    found = hex_pattern.findall(styles.APP_STYLESHEET)
    permitted = {v.lower() for v in styles.PALETTE_LIGHT.values()}
    leaked = [h for h in found if h.lower() not in permitted]
    assert not leaked, (
        f"APP_STYLESHEET contains raw hex outside PALETTE_LIGHT: {leaked}"
    )


def test_variety_default_color_has_all_four_families() -> None:
    """variety-palette-2026q2-e1: dict must have exactly the four family keys
    matching surfaces.VARIETIES outer keys verbatim (Unicode included).

    Unicode key risk: "Calabi–Yau 3-fold" uses U+2013 (en-dash), and
    "Fano 3-fold (ρ=1)" uses U+03C1 (Greek small rho).  Retyping with ASCII
    substitutes (hyphen-minus, lowercase "p") would silently miss the lookup
    in app.py's VARIETY_DEFAULT_COLOR.get() call.  Asserting equality on the
    key set catches that drift immediately.
    """
    expected = {
        "K3 surface",
        "Enriques surface",
        "Calabi–Yau 3-fold",
        "Fano 3-fold (ρ=1)",
    }
    assert set(styles.VARIETY_DEFAULT_COLOR.keys()) == expected, (
        f"VARIETY_DEFAULT_COLOR keys mismatch.  Got "
        f"{sorted(styles.VARIETY_DEFAULT_COLOR.keys())!r}, expected "
        f"{sorted(expected)!r}."
    )


def test_variety_default_color_all_six_digit_hex() -> None:
    """AI-13: all variety colors must be 6-digit hex (PyVista requires this)."""
    for variety, color in styles.VARIETY_DEFAULT_COLOR.items():
        assert HEX6.match(color), (
            f"VARIETY_DEFAULT_COLOR[{variety!r}] = {color!r} is not 6-digit hex"
        )


def test_variety_default_color_wcag_on_bg_viewport() -> None:
    """AI-12: each variety color must clear >=4.5:1 contrast against
    BG_VIEWPORT (#2f2f2f).  The surface fills enough of the dark canvas to
    function as text-level contrast for the family-identity cue, not just
    non-text decoration — the prior frontend-uplift challenger MINOR
    specifically called this out, requiring re-audit of any borderline
    candidate.
    """
    bg = styles.PALETTE_LIGHT["BG_VIEWPORT"]
    for variety, color in styles.VARIETY_DEFAULT_COLOR.items():
        r = _ratio(color, bg)
        assert r >= 4.5, (
            f"VARIETY_DEFAULT_COLOR[{variety!r}] = {color} fails 4.5:1 against "
            f"BG_VIEWPORT ({bg}): measured {r:.2f}:1.  Lighten the value."
        )


def test_variety_default_color_keys_match_surfaces_varieties() -> None:
    """Forward-compat guard: keys in VARIETY_DEFAULT_COLOR must be present in
    surfaces.VARIETIES.  Any future variety rename that mismatches the dict
    will be caught here before the silent BG_SURFACE_DEFAULT fallback masks
    the bug in production.
    """
    from surfaces import VARIETIES
    for key in styles.VARIETY_DEFAULT_COLOR:
        assert key in VARIETIES, (
            f"VARIETY_DEFAULT_COLOR has key {key!r} that is not present in "
            f"surfaces.VARIETIES (keys: {sorted(VARIETIES.keys())!r}).  "
            f"Either the variety was renamed or this dict is out of date."
        )


# ---------------------------------------------------------------------------
# AppearancePanel.set_default_color() direct unit tests
# ---------------------------------------------------------------------------
#
# These tests exercise the pure-Python logic of set_default_color() without
# instantiating a QApplication, by calling the unbound method against a
# lightweight shim that mimics the relevant attributes.  This keeps the
# tests AI-2 compliant (no pytest-qt, no QApplication required) — QColor is
# a pure data type from QtGui and does not require an event loop.
#
# Rectifies adversary critique M1 for variety-palette-2026q2-e1: the four
# tests above exercise the dict as data, but the new public API method that
# consumes the dict had no direct coverage.  These tests close that gap.


def test_set_default_color_updates_surface_color() -> None:
    """Calling set_default_color with a valid hex updates _surface_color and
    invokes _apply_swatch_color to refresh the chip.
    """
    from unittest.mock import MagicMock, patch
    from PySide6.QtGui import QColor
    import appearance_panel

    # Lightweight shim that mimics the AppearancePanel attributes
    # set_default_color reads/writes — no full panel construction needed.
    class _Shim:
        def __init__(self) -> None:
            self._surface_color = QColor("#000000")  # prior color
            self._surf_swatch = MagicMock()

    shim = _Shim()
    with patch.object(appearance_panel, "_apply_swatch_color") as mock_apply:
        appearance_panel.AppearancePanel.set_default_color(shim, "#8e9ed4")

    assert shim._surface_color.name() == "#8e9ed4", (
        "_surface_color should be updated to the new hex"
    )
    mock_apply.assert_called_once()
    # Verify the swatch was refreshed with the new color (not the old one)
    call_args = mock_apply.call_args
    swatch_arg, color_arg = call_args[0]
    assert swatch_arg is shim._surf_swatch
    assert color_arg.name() == "#8e9ed4"


def test_set_culling_stores_back_value() -> None:
    """enriques-backface-2026q2-e1 (UPL-7): set_culling('back') updates
    AppearancePanel._culling.  Uses the unbound-method shim pattern
    established by test_set_default_color — no QApplication, no PyVista,
    AI-2 compliant.  Guards against a future rename of self._culling
    breaking the variety-routing logic at app.py:_on_variety_changed
    without touching the test suite.
    """
    import appearance_panel

    class _Shim:
        def __init__(self) -> None:
            self._culling = None

    shim = _Shim()
    appearance_panel.AppearancePanel.set_culling(shim, "back")
    assert shim._culling == "back", (
        f"set_culling('back') should store 'back', got {shim._culling!r}"
    )


def test_set_culling_clears_to_none() -> None:
    """enriques-backface-2026q2-e1 (UPL-7): set_culling(None) clears any
    prior culling state.  This is the path the variety-switch gate uses
    when leaving the Enriques family to clear the back-cull setting
    before entering K3 / CY3 / Fano (where culling would BREAK the
    render).  A regression that left _culling stuck at 'back' would
    cause AI-7 conflicts the next time a Hanson surface renders.
    """
    import appearance_panel

    class _Shim:
        def __init__(self) -> None:
            self._culling = "back"  # simulate prior Enriques state

    shim = _Shim()
    appearance_panel.AppearancePanel.set_culling(shim, None)
    assert shim._culling is None, (
        f"set_culling(None) should clear to None, got {shim._culling!r}"
    )


def test_set_default_color_ignores_invalid_hex() -> None:
    """Invalid hex strings (failed QColor.isValid()) silently preserve the
    existing color rather than corrupting _surface_color.
    """
    from unittest.mock import MagicMock, patch
    from PySide6.QtGui import QColor
    import appearance_panel

    class _Shim:
        def __init__(self) -> None:
            self._surface_color = QColor("#abc123")  # valid prior color
            self._surf_swatch = MagicMock()

    shim = _Shim()
    prior_name = shim._surface_color.name()

    with patch.object(appearance_panel, "_apply_swatch_color") as mock_apply:
        appearance_panel.AppearancePanel.set_default_color(shim, "not-a-hex")

    assert shim._surface_color.name() == prior_name, (
        "Invalid hex should leave _surface_color unchanged"
    )
    mock_apply.assert_not_called()


def test_critical_text_tokens_meet_wcag_aa_on_bg_panel() -> None:
    """TEXT_MUTED and TEXT_VALUE must clear >=4.5:1 contrast on BG_PANEL
    for WCAG AA normal-text compliance (AI-12).

    Uses the module-level ``_ratio`` helper (single source of truth for the
    WCAG 2.x formula).  TEXT_DISABLED is intentionally low (per WCAG
    exception for disabled UI state) and skipped here.
    """
    bg = styles.PALETTE_LIGHT["BG_PANEL"]
    assert _ratio(styles.PALETTE_LIGHT["TEXT_MUTED"], bg) >= 4.5, (
        "TEXT_MUTED on BG_PANEL fails WCAG AA (need >=4.5:1)"
    )
    assert _ratio(styles.PALETTE_LIGHT["TEXT_VALUE"], bg) >= 4.5, (
        "TEXT_VALUE on BG_PANEL fails WCAG AA (need >=4.5:1)"
    )


# ---------------------------------------------------------------------------
# PALETTE_DARK regression guards (dark-mode-2026q2-e1 / UPL-1)
# ---------------------------------------------------------------------------
#
# Parallel coverage to the light-palette tests above.  Every text token in
# PALETTE_DARK must clear 4.5:1 against BG_PANEL_DARK; every non-text UI
# border must clear 3:1.  The TEXT_DISABLED and BG_DOCK_HEADER tokens are
# intentionally below the threshold per the WCAG §1.4.3 disabled exception
# and the structural-contrast pattern (the BORDER_DOCK_HEADER separator at
# 3.05:1 carries the §1.4.11 boundary) — skipped here, same as light.
#
# Named constants (COLOR_MUTED, COLOR_VALUE, etc.) remain PALETTE_LIGHT
# aliases per the brief; no dark twin needed for the backward-compat tests.


def test_palette_dark_has_minimum_tokens() -> None:
    """PALETTE_DARK must be key-identical to PALETTE_LIGHT."""
    assert set(styles.PALETTE_DARK.keys()) == set(styles.PALETTE_LIGHT.keys()), (
        "PALETTE_DARK keys must match PALETTE_LIGHT exactly so the same QSS "
        "template (_render_stylesheet) renders against either palette."
    )


def test_palette_dark_every_value_is_six_digit_hex() -> None:
    """AI-13: every PALETTE_DARK value must be 6-digit hex (PyVista hard
    requirement; convention extended to QSS for consistency).
    """
    for key, value in styles.PALETTE_DARK.items():
        assert HEX6.match(value), (
            f"PALETTE_DARK[{key!r}] = {value!r} is not 6-digit hex"
        )


def test_palette_dark_pyvista_bound_tokens_match_light() -> None:
    """Tokens flowing into PyVista (BG_VIEWPORT, BG_SURFACE_DEFAULT,
    COLOR_WIREFRAME_OVERLAY) are intentionally identical across themes —
    the VTK canvas is always dark, so its background never changes, and the
    default mesh color reads on either chrome.  Verify they match so a
    drifted dark value can't silently change PyVista behavior.
    """
    shared = {"BG_VIEWPORT", "BG_SURFACE_DEFAULT", "COLOR_WIREFRAME_OVERLAY"}
    for key in shared:
        assert styles.PALETTE_DARK[key] == styles.PALETTE_LIGHT[key], (
            f"PALETTE_DARK[{key!r}] = {styles.PALETTE_DARK[key]!r} differs "
            f"from PALETTE_LIGHT[{key!r}] = {styles.PALETTE_LIGHT[key]!r}; "
            f"PyVista-bound tokens must be theme-shared."
        )


def test_dark_text_tokens_meet_wcag_aa_on_bg_panel_dark() -> None:
    """AI-12: TEXT_MUTED_DARK and TEXT_VALUE_DARK must clear >=4.5:1 on
    BG_PANEL_DARK.  The original challenger MAJOR finding for UPL-1
    specifically called out that the light TEXT_MUTED = #5a5a5a fails on
    dark at 1.94:1 — this test guards the dark replacement.
    """
    bg = styles.PALETTE_DARK["BG_PANEL"]
    assert _ratio(styles.PALETTE_DARK["TEXT_MUTED"], bg) >= 4.5, (
        f"PALETTE_DARK[TEXT_MUTED] on BG_PANEL_DARK fails WCAG AA "
        f"(measured {_ratio(styles.PALETTE_DARK['TEXT_MUTED'], bg):.2f}:1; "
        f"need >=4.5:1)"
    )
    assert _ratio(styles.PALETTE_DARK["TEXT_VALUE"], bg) >= 4.5, (
        f"PALETTE_DARK[TEXT_VALUE] on BG_PANEL_DARK fails WCAG AA "
        f"(measured {_ratio(styles.PALETTE_DARK['TEXT_VALUE'], bg):.2f}:1; "
        f"need >=4.5:1)"
    )


def test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark() -> None:
    """WCAG 2.1 §1.4.11 non-text UI components must clear >=3:1.  Covers
    BORDER_GROUP_BOX, BORDER_DOCK_HEADER, BORDER_CAMERA_BTN, BORDER_RESET_BTN,
    and the FOCUS_RING (which serves as a non-text UI affordance).
    """
    bg = styles.PALETTE_DARK["BG_PANEL"]
    non_text_tokens = (
        "BORDER_GROUP_BOX",
        "BORDER_DOCK_HEADER",
        "BORDER_CAMERA_BTN",
        "BORDER_RESET_BTN",
        "FOCUS_RING",
    )
    for token in non_text_tokens:
        r = _ratio(styles.PALETTE_DARK[token], bg)
        assert r >= 3.0, (
            f"PALETTE_DARK[{token!r}] = {styles.PALETTE_DARK[token]} fails "
            f"non-text 3:1 against BG_PANEL_DARK ({bg}): measured {r:.2f}:1"
        )


def test_light_structural_borders_intentionally_below_3_1() -> None:
    """Machine-readable companion to the docstring caveat in
    ``test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel``: the four
    structural border tokens in PALETTE_LIGHT (BORDER_GROUP_BOX,
    BORDER_DOCK_HEADER, BORDER_CAMERA_BTN, BORDER_RESET_BTN) are
    INTENTIONALLY low-contrast (<3:1) on BG_PANEL_LIGHT — they are internal
    structural separators, not user-interface component boundaries against
    the panel ground subject to WCAG 2.1 §1.4.11.  Their dark twins in
    PALETTE_DARK were intentionally darkened to clear 3:1 on dark
    (BORDER_GROUP_BOX dark is #777777 → 3.42:1), but the light values were
    kept at their original soft-separator values (~1.1-1.4:1).

    This test exists to PREVENT well-intentioned-but-wrong "harmonization"
    of the light test with the dark test.  If a future maintainer
    "completes" the light WCAG suite by widening the assertion set in the
    sibling test, they will then see these four tokens fail and may try to
    fix them by darkening PALETTE_LIGHT["BORDER_*"] values.  That would
    silently degrade the intentional soft-separator chrome.  This test
    fires LOUDLY on any such attempt: if PALETTE_LIGHT["BORDER_*"] is
    darkened to clear 3:1, this test fails with a message naming the
    architectural intent, forcing a deliberate design decision.

    Added in focus-ring-contrast-2026q2-e1 (rectify pass, F-L2).
    """
    bg = styles.PALETTE_LIGHT["BG_PANEL"]
    structural_tokens = (
        "BORDER_GROUP_BOX",
        "BORDER_DOCK_HEADER",
        "BORDER_CAMERA_BTN",
        "BORDER_RESET_BTN",
    )
    for token in structural_tokens:
        r = _ratio(styles.PALETTE_LIGHT[token], bg)
        assert r < 3.0, (
            f"PALETTE_LIGHT[{token!r}] = {styles.PALETTE_LIGHT[token]} now "
            f"measures {r:.2f}:1 vs BG_PANEL ({bg}) — clearing the WCAG 3:1 "
            f"floor.  This token is INTENTIONALLY a soft structural "
            f"separator (~1.1-1.4:1) on the light panel and should not have "
            f"been darkened.  If the design intent has changed, lift this "
            f"test deliberately; do not silently degrade panel chrome."
        )


def test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel() -> None:
    """WCAG 2.1 §1.4.11 — FOCUS_RING must clear >=3:1 on the light BG_PANEL
    (#f0f0f0).  Symmetric guard to
    ``test_dark_non_text_borders_meet_wcag_aa_on_bg_panel_dark`` but
    deliberately scoped to FOCUS_RING only — see the docstring caveat below
    for why the four structural border tokens are NOT included.

    Closes the deferred M4 finding from panel-refresh-2026q2-e2
    (variety-palette / UPL-1 adversary critique): FOCUS_RING was 2.60:1 on
    BG_PANEL_LIGHT — below the WCAG 1.4.11 non-text 3:1 floor for focus
    indicators.  Fixed by focus-ring-contrast-2026q2-e1 by darkening to
    ``#3c82c4`` (3.56:1 on light, 3.78:1 on dark — single shared value).

    Caveat on token scope (do NOT widen this assertion set):  the dark twin
    above includes BORDER_GROUP_BOX, BORDER_DOCK_HEADER, BORDER_CAMERA_BTN,
    and BORDER_RESET_BTN because their PALETTE_DARK values were intentionally
    darkened to clear 3:1 against BG_PANEL_DARK.  The PALETTE_LIGHT values
    of those same tokens are intentionally LOWER-contrast (#d0d0d0,
    #c5cdd8, #b0bec5, #d4b4b4 — ~1.1-1.4:1 on #f0f0f0) because on light
    they serve as structural internal separators, not user-interface
    component boundaries against the panel ground.  Asserting 3:1 on those
    light values would be a false-positive regression — they were never
    designed to clear that threshold.  Only FOCUS_RING bears WCAG 1.4.11
    on the light panel.
    """
    bg = styles.PALETTE_LIGHT["BG_PANEL"]
    r = _ratio(styles.PALETTE_LIGHT["FOCUS_RING"], bg)
    assert r >= 3.0, (
        f"PALETTE_LIGHT['FOCUS_RING'] = {styles.PALETTE_LIGHT['FOCUS_RING']} "
        f"fails non-text 3:1 against BG_PANEL ({bg}): measured {r:.2f}:1.  "
        f"Darken FOCUS_RING to at least #3c82c4 (3.56:1) — see "
        f"focus-ring-contrast-2026q2-e1."
    )


def test_app_stylesheet_dark_no_raw_hex() -> None:
    """APP_STYLESHEET_DARK must use only hex values from PALETTE_DARK — no
    inline literals.  Parallels test_app_stylesheet_substitutes_no_raw_hex_outside_palette
    for the dark output.
    """
    qss = styles.APP_STYLESHEET_DARK
    found = set(re.findall(r"#[0-9a-fA-F]{6}", qss))
    allowed = set(styles.PALETTE_DARK.values())
    extra = found - allowed
    assert not extra, (
        f"APP_STYLESHEET_DARK contains hex values not in PALETTE_DARK: {extra}.  "
        f"Every hex should come from a palette[\"TOKEN\"] reference in "
        f"_render_stylesheet()."
    )


# --- VARIETY_DEFAULT_COLOR_DARK tests --------------------------------------


def test_variety_default_color_dark_has_all_four_families() -> None:
    """VARIETY_DEFAULT_COLOR_DARK must have the same Unicode keys as
    VARIETY_DEFAULT_COLOR.  The dark dict reuses the same hex values (all
    four clear 3:1 on BG_PANEL_DARK), so the key set must match exactly.
    """
    assert set(styles.VARIETY_DEFAULT_COLOR_DARK.keys()) == set(
        styles.VARIETY_DEFAULT_COLOR.keys()
    ), (
        "VARIETY_DEFAULT_COLOR_DARK keys must match VARIETY_DEFAULT_COLOR "
        "(both Unicode en-dash U+2013 and Greek rho U+03C1 must be present)."
    )


def test_variety_default_color_dark_all_six_digit_hex() -> None:
    """AI-13: every VARIETY_DEFAULT_COLOR_DARK value is 6-digit hex."""
    for variety, color in styles.VARIETY_DEFAULT_COLOR_DARK.items():
        assert HEX6.match(color), (
            f"VARIETY_DEFAULT_COLOR_DARK[{variety!r}] = {color!r} not 6-digit hex"
        )


def test_variety_default_color_dark_wcag_on_bg_viewport() -> None:
    """AI-12: dark-theme variety colors must clear >=4.5:1 against
    BG_VIEWPORT (shared between themes — the canvas is always dark).  Same
    threshold as the light dict because the surface fills enough of the dark
    canvas to function as a text-level identity cue.

    Reads BG_VIEWPORT from PALETTE_DARK (not PALETTE_LIGHT) — the values are
    intentionally identical (verified by test_palette_dark_pyvista_bound_tokens_match_light),
    but reading from the theme-correct dict makes intent explicit and would
    surface a meaningful failure if the two were ever intentionally diverged.
    (dark-mode-2026q2-e1 rect L3.)
    """
    bg = styles.PALETTE_DARK["BG_VIEWPORT"]
    for variety, color in styles.VARIETY_DEFAULT_COLOR_DARK.items():
        r = _ratio(color, bg)
        assert r >= 4.5, (
            f"VARIETY_DEFAULT_COLOR_DARK[{variety!r}] = {color} fails 4.5:1 "
            f"against BG_VIEWPORT ({bg}): measured {r:.2f}:1"
        )


def test_variety_default_color_dark_swatch_chip_vs_bg_panel_dark() -> None:
    """Closes the deferred MF1 finding from variety-palette-2026q2-e1: the
    swatch chip contrast against the panel background was below WCAG
    §1.4.11's 3:1 non-text threshold in light mode (1.87-2.31:1 vs
    BG_PANEL_LIGHT).  In dark mode the same colors pass at 5+:1 against the
    dark panel — verify this is still true if either dict or BG_PANEL_DARK
    is ever changed.
    """
    bg = styles.PALETTE_DARK["BG_PANEL"]
    for variety, color in styles.VARIETY_DEFAULT_COLOR_DARK.items():
        r = _ratio(color, bg)
        assert r >= 3.0, (
            f"VARIETY_DEFAULT_COLOR_DARK[{variety!r}] = {color} fails 3:1 "
            f"swatch-chip contrast against BG_PANEL_DARK ({bg}): "
            f"measured {r:.2f}:1.  This re-opens the MF1 finding; lighten "
            f"the value or darken BG_PANEL_DARK."
        )


def test_variety_default_color_dark_keys_match_surfaces_varieties() -> None:
    """Forward-compat guard: keys in VARIETY_DEFAULT_COLOR_DARK must be
    present in surfaces.VARIETIES (same guard as the light dict's parallel
    test).  Catches any future variety rename before the silent
    BG_SURFACE_DEFAULT fallback masks the bug.
    """
    from surfaces import VARIETIES
    for key in styles.VARIETY_DEFAULT_COLOR_DARK:
        assert key in VARIETIES, (
            f"VARIETY_DEFAULT_COLOR_DARK has key {key!r} not in "
            f"surfaces.VARIETIES (keys: {sorted(VARIETIES.keys())!r})"
        )


# --- get_variety_default_colors() accessor tests ---------------------------


def test_no_inline_color_styles_in_panel_files() -> None:
    """dark-mode-2026q2-e1 rect M2: panel files (appearance_panel.py,
    view_panel.py, parameters_panel.py) must NOT call
    `widget.setStyleSheet(MUTED_TEXT_STYLE)` /
    `setStyleSheet(VALUE_MONO_STYLE)` /
    `setStyleSheet(RANGE_LABEL_STYLE)` — these inline styles hardcode
    PALETTE_LIGHT colors and override the dark QSS cascade, producing
    near-invisible text (1.21-2.22:1) when the user is in Dark theme.

    All call sites were migrated to ``widget.setProperty("role", X)`` in
    this milestone; the QSS role selectors in ``_render_stylesheet``
    handle color + font for both themes via theme-aware cascade.  This
    test catches any future re-introduction of the inline-style pattern.

    The legacy constants (MUTED_TEXT_STYLE, VALUE_MONO_STYLE,
    RANGE_LABEL_STYLE) remain in styles.py as backward-compat exports
    only — they are not consumed in-repo after this rectification.
    """
    from pathlib import Path
    forbidden = (
        "setStyleSheet(MUTED_TEXT_STYLE)",
        "setStyleSheet(VALUE_MONO_STYLE)",
        "setStyleSheet(RANGE_LABEL_STYLE)",
    )
    repo_root = Path(__file__).resolve().parent.parent
    panel_files = (
        "appearance_panel.py",
        "view_panel.py",
        "parameters_panel.py",
    )
    for panel_name in panel_files:
        panel_path = repo_root / panel_name
        # Scan line-by-line, skipping Python comments — comments that
        # discuss the deprecated pattern (as the migrated call sites do)
        # are legitimate documentation, not actual calls.
        for ln_num, raw_line in enumerate(
            panel_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            line = raw_line.split("#", 1)[0]  # strip Python comment
            for pattern in forbidden:
                assert pattern not in line, (
                    f"{panel_name}:{ln_num} contains inline-style call "
                    f"{pattern!r} (non-comment code).  Replace with "
                    f"`widget.setProperty(\"role\", X)` so the QSS role "
                    f"selector handles theme-aware color cascade."
                )


def test_dark_stylesheet_includes_role_selectors() -> None:
    """dark-mode-2026q2-e1 rect M2: APP_STYLESHEET_DARK must include the
    role-property selectors that replace the inline-style constants.
    Without these rules, panel labels with `setProperty("role", "muted")`
    etc. would get no color/font override and fall back to QPalette
    defaults — re-opening the AI-12 dark-on-dark failure.

    Extended in display-toggles-checkable-button-2026q3-e1: also asserts
    the `QPushButton[role="display-toggle"]` selector + its `:checked`
    pseudo-state are present in both stylesheets.  Without these rules,
    the Wireframe + Show-edges QPushButton(checkable=True) instances
    would render as plain push buttons with no checked-state indicator,
    re-introducing the visual-ambiguity bug that F-M2 closed.
    """
    required_selectors = (
        'QLabel[role="muted"]',
        'QLabel[role="value-mono"]',
        'QLabel[role="range-label"]',
        # display-toggles-checkable-button-2026q3-e1 (F-M2 closure):
        'QPushButton[role="display-toggle"]',
        # appearance-panel-layout-pass-2026q3-e2 (F-M2 closure):
        # text-align: left rule for the Colors-group color-picker
        # buttons — closes the cross-group alignment fracture.
        'QPushButton[role="colors-button"]',
    )
    for sel in required_selectors:
        assert sel in styles.APP_STYLESHEET_DARK, (
            f"APP_STYLESHEET_DARK missing role selector {sel!r}; "
            f"_render_stylesheet must emit this rule so role-property "
            f"labels render correctly in dark mode."
        )
        assert sel in styles.APP_STYLESHEET, (
            f"APP_STYLESHEET missing role selector {sel!r}; "
            f"light theme also depends on it."
        )
    # Additionally verify the :checked pseudo-state rule is present
    # (this is what carries the WCAG-compliant active-state indicator).
    for qss, name in (
        (styles.APP_STYLESHEET, "APP_STYLESHEET"),
        (styles.APP_STYLESHEET_DARK, "APP_STYLESHEET_DARK"),
    ):
        assert 'QPushButton[role="display-toggle"]:checked' in qss, (
            f"{name} missing the :checked pseudo-state rule for the "
            f"display-toggle role — without it, Wireframe + Show-edges "
            f"buttons have no visual indication of their active state."
        )
        # appearance-panel-layout-pass-2026q3-e2 rect M3: verify the
        # `colors-button` rule actually carries `text-align: left` and
        # `background: transparent` in its rule body — not just that
        # the selector exists in the stylesheet.  A future refactor
        # could hollow out the rule (delete the body declarations while
        # keeping the selector) and the basic presence check would not
        # catch it.  Substring scan starting at the selector index
        # captures the rule body up to the closing brace (~150 chars
        # is enough for our 4-declaration rule).
        sel_idx = qss.index('QPushButton[role="colors-button"]')
        rule_body = qss[sel_idx:sel_idx + 200]
        assert 'text-align: left' in rule_body, (
            f"{name}: QPushButton[role='colors-button'] rule body is "
            f"missing `text-align: left` — the functional payload of "
            f"the F-M2 alignment fix.  Selector alone is not enough."
        )
        assert 'background: transparent' in rule_body, (
            f"{name}: QPushButton[role='colors-button'] rule body is "
            f"missing `background: transparent` — the macOS Aqua paint-"
            f"mode trigger (rect F-M1).  Without it the alignment is a "
            f"silent no-op on Aqua-style platforms."
        )


def test_bg_toggle_checked_token_is_six_digit_hex_in_both_palettes() -> None:
    """display-toggles-checkable-button-2026q3-e1 (F-M2 closure, AI-13 guard):
    the new BG_TOGGLE_CHECKED token must be present in BOTH palettes (the
    key-identical pattern enforced by test_palette_dark_has_minimum_tokens)
    and must be 6-digit hex in each.  The token is a decorative fill for
    the :checked pseudo-state; the WCAG indicator is the FOCUS_RING border
    (already guarded separately).
    """
    for palette_name, palette in (
        ("PALETTE_LIGHT", styles.PALETTE_LIGHT),
        ("PALETTE_DARK", styles.PALETTE_DARK),
    ):
        assert "BG_TOGGLE_CHECKED" in palette, (
            f"{palette_name} missing BG_TOGGLE_CHECKED token — the "
            f"display-toggle :checked QSS rule will reference an "
            f"undefined palette key and the stylesheet template raises."
        )
        value = palette["BG_TOGGLE_CHECKED"]
        assert HEX6.match(value), (
            f"{palette_name}['BG_TOGGLE_CHECKED'] = {value!r} is not "
            f"6-digit hex (AI-13)."
        )
    # The two themes must use different values — light gets a light tint,
    # dark gets a dark tint.  Sharing the same value would produce a
    # near-invisible :checked state in one of the two themes.
    assert (
        styles.PALETTE_LIGHT["BG_TOGGLE_CHECKED"]
        != styles.PALETTE_DARK["BG_TOGGLE_CHECKED"]
    ), (
        "BG_TOGGLE_CHECKED is identical across themes; per-theme values "
        "are required so the :checked fill tint reads naturally on each "
        "panel background."
    )


def test_bg_toggle_checked_value_appears_in_both_stylesheets() -> None:
    """display-toggles-checkable-button-2026q3-e1: the rendered stylesheets
    must each contain their theme's BG_TOGGLE_CHECKED hex value — verifies
    that ``_render_stylesheet`` actually consumes the new token rather than
    declaring it dead.  A dead palette token is a token without a
    corresponding QSS rule, which would silently leave the :checked state
    visually identical to the :unchecked state.
    """
    assert (
        styles.PALETTE_LIGHT["BG_TOGGLE_CHECKED"] in styles.APP_STYLESHEET
    ), (
        f"APP_STYLESHEET does not contain "
        f"PALETTE_LIGHT['BG_TOGGLE_CHECKED'] "
        f"({styles.PALETTE_LIGHT['BG_TOGGLE_CHECKED']}) — the new token "
        f"is declared but not consumed by any QSS rule."
    )
    assert (
        styles.PALETTE_DARK["BG_TOGGLE_CHECKED"] in styles.APP_STYLESHEET_DARK
    ), (
        f"APP_STYLESHEET_DARK does not contain "
        f"PALETTE_DARK['BG_TOGGLE_CHECKED'] "
        f"({styles.PALETTE_DARK['BG_TOGGLE_CHECKED']}) — the new token "
        f"is declared but not consumed by any QSS rule."
    )


def test_appearance_panel_colors_buttons_have_colors_button_role() -> None:
    """appearance-panel-layout-pass-2026q3-e2 (F-M2 closure): the
    Surface… and Background… color-picker buttons in `_build_color_group`
    must each carry ``setProperty("role", "colors-button")`` so the QSS
    rule `QPushButton[role="colors-button"] { text-align: left; ... }`
    picks them up.  Without the role tag the buttons fall back to Qt's
    platform-default center-alignment, re-introducing the cross-group
    vertical-rhythm fracture between the Colors and Display & Quality
    groups that this milestone closed.  (Group renamed Render Mode →
    Display & Quality by appearance-panel-render-mode-split-2026q3-e3.)

    Source-text grep (AI-2 compliant — testing the alignment under a
    real QApplication would require Qt, which AI-2 bans).
    """
    import pathlib
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")

    # Must see exactly 2 occurrences — one for surf_btn, one for bg_btn.
    # Count-based (not single `in`) so a half-migration regression where
    # only one button carries the role fires loudly with a precise
    # diagnostic (parallels the M1 lesson from
    # display-toggles-checkable-button-2026q3-e1).
    role_count = src.count('setProperty("role", "colors-button")')
    assert role_count >= 2, (
        f"appearance_panel.py contains fewer than 2 "
        f"setProperty('role', 'colors-button') calls — both Surface… "
        f"AND Background… color-picker buttons must carry the role.  "
        f"Found {role_count}; expected >=2.  Check for a half-migration "
        f"regression."
    )

    # Neither button should be checkable — they are action buttons that
    # open a QColorDialog, not stateful toggles.  Guard against a future
    # refactor accidentally adding setCheckable to them.
    # (The Display group's setCheckable(True) calls are NOT counted here
    # because they're on a different code block; this test only fires if
    # someone explicitly writes `surf_btn.setCheckable(...)` or
    # `bg_btn.setCheckable(...)`.)
    for btn_name in ("surf_btn", "bg_btn"):
        assert f"{btn_name}.setCheckable" not in src, (
            f"appearance_panel.py contains {btn_name}.setCheckable(...) — "
            f"the Colors group buttons are action buttons (open a "
            f"QColorDialog) NOT toggles.  Adding setCheckable would "
            f"change their semantics."
        )


def test_appearance_panel_display_and_quality_group_header() -> None:
    """appearance-panel-render-mode-split-2026q3-e3 (F-M2 closure): the
    display-toggles group's QGroupBox header is "Display && Quality" —
    note the double `&` is the Qt literal-ampersand escape; a single `&`
    would underline `Q` and bind it as an Alt+Q accelerator on the group
    box, which is unintended.  Path (a) from the F-M2 deferred finding:
    single QGroupBox stays, label acknowledges both axes (Wireframe /
    Show edges = display-pipeline toggles; Double-pass smooth = quality
    toggle that changes mesh fidelity).

    Lineage of renames on this group:
        display-toggles-checkable-button-2026q3-e1: QGroupBox("Display")
        appearance-panel-layout-pass-2026q3-e2     : QGroupBox("Render Mode")
        appearance-panel-render-mode-split-2026q3-e3: QGroupBox("Display && Quality")

    Source-text grep (AI-2 compliant — verifying the QGroupBox label
    under a real QApplication would require Qt, which AI-2 bans).
    """
    import pathlib
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")

    # Positive: the new header is present.
    assert 'QGroupBox("Display && Quality")' in src, (
        "appearance_panel.py is missing QGroupBox('Display && Quality') — "
        "the display-toggles-group header rename from F-M2 "
        "(appearance-panel-render-mode-split-2026q3-e3).  Note the `&&` "
        "is REQUIRED: Qt interprets a single `&` as a mnemonic, so "
        "QGroupBox('Display & Quality') would bind Alt+Q (unintended)."
    )
    # Negative: the immediately-prior "Render Mode" header must NOT remain.
    assert 'QGroupBox("Render Mode")' not in src, (
        "appearance_panel.py still contains QGroupBox('Render Mode') — "
        "regression: appearance-panel-render-mode-split-2026q3-e3 renamed "
        "it to 'Display && Quality' (F-M2 closure).  Internal symbol names "
        "(_build_toggles_group, 'display-toggle' role property) are NOT "
        "tested here — only the user-visible group-box header."
    )
    # Negative: the even-older generic "Display" header must NOT appear
    # either.  Catches the case where someone reverts past the prior
    # F-L2 milestone too.
    assert 'QGroupBox("Display")' not in src, (
        "appearance_panel.py contains QGroupBox('Display') — the "
        "appearance-panel-layout-pass-2026q3-e2 milestone renamed it "
        "away from 'Display' (F-L2), and appearance-panel-render-mode-"
        "split-2026q3-e3 superseded it again with 'Display && Quality'.  "
        "If a future group genuinely needs to be called 'Display', pick "
        "a more specific name."
    )


def test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox() -> None:
    """display-toggles-checkable-button-2026q3-e1 (F-M2 closure): the
    Wireframe + Show-edges toggles in `appearance_panel.py` must be
    constructed as ``QPushButton(checkable=True)``, NOT ``QCheckBox``.

    Source-text grep guard (AI-2 compliant — QPushButton construction
    requires a live QApplication, which AI-2 bans from the test suite).
    The guard is weaker than a behavioral test but sufficient to catch
    a regression where a future palette/widget refactor reverts to
    QCheckBox.

    The QCheckBox+setIcon idiom produces a ``[check-square][icon][label]``
    triple-prefix that no peer scientific-viz app uses (Blender N-panel
    + 3D Slicer modules panel both use checkable QPushButton; ParaView
    uses plain text checkboxes without icon).  See CONTEXT.md §8.15
    and qtawesome-icons-2026q2-e2 finding F-M2 for the migration
    rationale.
    """
    import pathlib
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")

    # Negative assertions: no QCheckBox construction for these two
    # specific toggle labels.
    assert 'QCheckBox("Wireframe")' not in src, (
        "appearance_panel.py constructs QCheckBox('Wireframe') — F-M2 "
        "regression.  Migrate to QPushButton(checkable=True) per "
        "CONTEXT.md §8.15."
    )
    assert 'QCheckBox("Show edges")' not in src, (
        "appearance_panel.py constructs QCheckBox('Show edges') — F-M2 "
        "regression.  Migrate to QPushButton(checkable=True) per "
        "CONTEXT.md §8.15."
    )

    # Positive assertions: count-based (NOT single-occurrence `in`) so a
    # half-migration regression — where one of the two toggles reverts
    # while the other retains the sentinel string — fails loudly instead
    # of silently passing.  See the adversary critique M1 (rect pass):
    # `in` would let a single surviving `setCheckable(True)` from the
    # un-reverted button mask the regression on the other.
    assert src.count("setCheckable(True)") >= 2, (
        "appearance_panel.py contains fewer than 2 setCheckable(True) "
        "calls — both Wireframe AND Show-edges display toggles must "
        f"opt into checkable behavior.  Found {src.count('setCheckable(True)')}; "
        f"expected >=2.  Check for a half-migration regression."
    )
    # Count once into a local — a backslash inside an f-string expression
    # part is a SyntaxError on Python 3.11 (only allowed from 3.12); the
    # repo's venv is 3.11.9, so the escaped-quote `src.count("...")` call
    # must live outside the f-string.
    _role_count = src.count('setProperty("role", "display-toggle")')
    assert _role_count >= 2, (
        "appearance_panel.py contains fewer than 2 "
        "setProperty('role', 'display-toggle') calls — both toggles "
        "must carry the role so the QSS :checked rules target them.  "
        f"Found {_role_count}; "
        f"expected >=2.  Check for a half-migration regression."
    )


def test_dark_stylesheet_dock_title_has_explicit_color() -> None:
    """dark-mode-2026q2-e1 rect HIGH-1: QDockWidget::title must set color:
    explicitly in the dark stylesheet — otherwise Qt falls back to
    QPalette.WindowText (near-black on light OS) and the dark dock header
    background renders dock titles at ~1.62:1.
    """
    # The rendered CSS will contain `color: <hex>;` inside the
    # `QDockWidget::title` block.  Match permissively (any whitespace).
    assert (
        'QDockWidget::title' in styles.APP_STYLESHEET_DARK
        and 'color:' in styles.APP_STYLESHEET_DARK.split('QDockWidget::title')[1].split('}')[0]
    ), "QDockWidget::title block in APP_STYLESHEET_DARK must set `color:` explicitly"


def test_dark_stylesheet_statusbar_has_explicit_background() -> None:
    """dark-mode-2026q2-e1 rect HIGH-2: QStatusBar must set background:
    explicitly so the dark text doesn't render on the platform's light
    QPalette.Window on light-OS systems (would be #a0a0a0 on ~#ececec ≈
    2.21:1, an AI-12 fail).
    """
    statusbar_block = (
        styles.APP_STYLESHEET_DARK.split('QStatusBar')[1].split('}')[0]
        if 'QStatusBar' in styles.APP_STYLESHEET_DARK else ''
    )
    assert 'background:' in statusbar_block, (
        "QStatusBar block in APP_STYLESHEET_DARK must set `background:` "
        "explicitly so dark text is legible on light-OS platforms"
    )


def test_get_variety_default_colors_returns_correct_dict() -> None:
    """The theme-aware accessor must return the right dict for each theme.
    AppearancePanel's decoupling from theme state depends on this — the
    call site in app.py uses this accessor instead of importing both dicts.
    Unknown theme names fall through to the dark dict (the launch default).
    """
    assert styles.get_variety_default_colors("light") is styles.VARIETY_DEFAULT_COLOR, (
        "get_variety_default_colors('light') must return VARIETY_DEFAULT_COLOR"
    )
    assert styles.get_variety_default_colors("dark") is styles.VARIETY_DEFAULT_COLOR_DARK, (
        "get_variety_default_colors('dark') must return VARIETY_DEFAULT_COLOR_DARK"
    )
    # Unknown / unexpected theme name → dark fallback (launch default)
    assert styles.get_variety_default_colors("unknown") is styles.VARIETY_DEFAULT_COLOR_DARK, (
        "Unknown theme name must fall through to VARIETY_DEFAULT_COLOR_DARK"
    )
    # Default argument is "dark"
    assert styles.get_variety_default_colors() is styles.VARIETY_DEFAULT_COLOR_DARK, (
        "get_variety_default_colors() (no arg) must default to dark dict"
    )
