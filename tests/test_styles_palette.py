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


def test_critical_text_tokens_meet_wcag_aa_on_bg_panel() -> None:
    """TEXT_MUTED and TEXT_VALUE must clear >=4.5:1 contrast on BG_PANEL
    for WCAG AA normal-text compliance (AI-12).

    Computes relative luminance per WCAG 2.x and the resulting contrast
    ratio.  TEXT_DISABLED is intentionally low (per WCAG exception for
    disabled UI state) and skipped here.
    """
    def luminance(hex_color: str) -> float:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

        def channel(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

    def ratio(fg: str, bg: str) -> float:
        l1, l2 = luminance(fg), luminance(bg)
        lighter, darker = max(l1, l2), min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    bg = styles.PALETTE_LIGHT["BG_PANEL"]
    assert ratio(styles.PALETTE_LIGHT["TEXT_MUTED"], bg) >= 4.5, (
        "TEXT_MUTED on BG_PANEL fails WCAG AA (need >=4.5:1)"
    )
    assert ratio(styles.PALETTE_LIGHT["TEXT_VALUE"], bg) >= 4.5, (
        "TEXT_VALUE on BG_PANEL fails WCAG AA (need >=4.5:1)"
    )
