"""Regression guards for the qtawesome icon factory (UPL-4).

These tests verify three behaviours that together protect against the
documented qtawesome footguns:

1. **Lazy-import deferral** — ``icons.py`` must NOT import qtawesome at
   module load.  qtawesome's icon-font cache fires on first ``qta.icon()``
   call (~150-200ms); deferring it past app launch keeps startup snappy.

2. **Theme-aware color routing** — ``_icon_color(theme)`` must resolve
   to ``PALETTE_DARK["TEXT_VALUE"]`` for "dark" and
   ``PALETTE_LIGHT["TEXT_VALUE"]`` for "light".  Routing through a
   module-level mutable would be a regression (panels would lose
   decoupling from theme state).

3. **Icon name + color wiring** — each icon factory must call
   ``qta.icon()`` with the right MDI 6 icon name AND the active theme's
   color.  Mocked at the qta boundary so the test stays AI-2 compliant
   (no QApplication).

Test 4 (full QIcon construction) requires a QApplication and is guarded
with ``pytest.skip`` if one can't be created in the test environment.
"""
from __future__ import annotations

import importlib
import re
import sys

import pytest

import styles


HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_icons_module_does_not_import_qtawesome_at_module_load() -> None:
    """``icons.py`` lazy-imports qtawesome on first icon function call.
    The module-level ``_qta`` sentinel must remain ``None`` at import time
    so app launch doesn't pay the ~150-200ms font-cache cold-boot cost.
    """
    # Force a fresh import to test the just-loaded state.
    sys.modules.pop("icons", None)
    icons_mod = importlib.import_module("icons")
    assert icons_mod._qta is None, (
        "icons._qta must be None at module load — the lazy-import sentinel "
        "indicates qtawesome has not yet been touched.  If you see this fail, "
        "an `import qtawesome` snuck into module scope; move it back into "
        "_get_qta()."
    )


def test_icon_color_for_theme_routes_to_correct_palette_token() -> None:
    """``_icon_color`` resolves the right palette's TEXT_VALUE per theme.
    Both values must be 6-digit hex (AI-13) and theme-distinct."""
    import icons

    assert icons._icon_color("dark") == styles.PALETTE_DARK["TEXT_VALUE"], (
        "icons._icon_color('dark') must read from PALETTE_DARK"
    )
    assert icons._icon_color("light") == styles.PALETTE_LIGHT["TEXT_VALUE"], (
        "icons._icon_color('light') must read from PALETTE_LIGHT"
    )
    # 6-digit hex guard (AI-13)
    assert HEX6.match(icons._icon_color("dark"))
    assert HEX6.match(icons._icon_color("light"))
    # The two themes must use different colors (light/dark distinction is the
    # whole point of theme-aware icon coloring).
    assert icons._icon_color("dark") != icons._icon_color("light"), (
        "Dark and light themes must use different icon colors"
    )
    # Unknown theme names fall through to dark (matches the launch default
    # established in dark-mode-2026q2-e1).
    assert icons._icon_color("unknown-future-theme") == icons._icon_color("dark")


def test_icon_functions_call_qta_icon_with_correct_args() -> None:
    """Each icon factory calls ``qta.icon()`` with the right MDI 6 icon
    name AND the active theme's color.  Mocked at the qta boundary so this
    runs without a QApplication (AI-2 compliant).

    Covers BOTH themes for every icon function (rect adv M2 — the prior
    pass only tested one theme per function, leaving a coverage gap where
    a wrong-branch refactor in either ``_icon_color`` or
    ``_reset_defaults_icon_color`` could slip past mock-only tests).

    Reset Defaults uses a DIFFERENT color helper
    (``_reset_defaults_icon_color`` returns TEXT_RESET_BTN, not TEXT_VALUE)
    so the button-glyph color matches the red-family text label (rect
    frontend-ux M1).  This test asserts that distinction explicitly.
    """
    from unittest.mock import MagicMock, patch
    import icons

    mock_qta = MagicMock()
    mock_qta.icon.return_value = MagicMock(name="QIcon")

    # Patch the cached qtawesome module so _get_qta() returns the mock.
    with patch.object(icons, "_qta", mock_qta):
        # Reset Camera — mdi6.fit-to-screen — TEXT_VALUE color, both themes
        for theme in ("dark", "light"):
            mock_qta.icon.reset_mock()
            icons.reset_camera_icon(theme)
            mock_qta.icon.assert_called_with(
                "mdi6.fit-to-screen",
                color=(
                    styles.PALETTE_DARK["TEXT_VALUE"]
                    if theme == "dark"
                    else styles.PALETTE_LIGHT["TEXT_VALUE"]
                ),
            )

        # Screenshot — mdi6.camera — TEXT_VALUE color, both themes
        for theme in ("dark", "light"):
            mock_qta.icon.reset_mock()
            icons.screenshot_icon(theme)
            mock_qta.icon.assert_called_with(
                "mdi6.camera",
                color=(
                    styles.PALETTE_DARK["TEXT_VALUE"]
                    if theme == "dark"
                    else styles.PALETTE_LIGHT["TEXT_VALUE"]
                ),
            )

        # Reset Defaults — mdi6.restore — TEXT_RESET_BTN color (red-family,
        # NOT TEXT_VALUE — see _reset_defaults_icon_color rationale).
        for theme in ("dark", "light"):
            mock_qta.icon.reset_mock()
            icons.reset_defaults_icon(theme)
            mock_qta.icon.assert_called_with(
                "mdi6.restore",
                color=(
                    styles.PALETTE_DARK["TEXT_RESET_BTN"]
                    if theme == "dark"
                    else styles.PALETTE_LIGHT["TEXT_RESET_BTN"]
                ),
            )


def test_icons_return_valid_qicons_with_qapplication() -> None:
    """When a QApplication is running, each icon function returns a
    non-null QIcon.  Skipped if a QApplication can't be created in this
    environment (some CI sandboxes block Qt platform plugins).

    This is the smoke-test that catches missing fonts or invalid icon
    names in the MDI 6 catalog — the mocked test above can't detect
    those because ``qta.icon`` is replaced entirely.
    """
    import os

    # Set offscreen platform BEFORE QApplication construction.  AI-3 is
    # satisfied because icons.py creates no QtInteractor — only QIcons,
    # which are pure data widgets with no VTK context.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        pytest.skip("PySide6 not available")

    app = QApplication.instance()
    if app is None:
        try:
            app = QApplication(sys.argv)
        except Exception as exc:  # pragma: no cover - environment-specific
            pytest.skip(f"Cannot create QApplication: {exc}")

    # Fresh import so the _qta sentinel test above doesn't dirty this one.
    sys.modules.pop("icons", None)
    import icons

    targets = (
        (icons.reset_camera_icon, "reset_camera_icon"),
        (icons.screenshot_icon, "screenshot_icon"),
        (icons.reset_defaults_icon, "reset_defaults_icon"),
        # qtawesome-icons-2026q2-e2 (UPL-4 v1) — camera presets
        (icons.preset_plus_x_icon, "preset_plus_x_icon"),
        (icons.preset_minus_x_icon, "preset_minus_x_icon"),
        (icons.preset_plus_y_icon, "preset_plus_y_icon"),
        (icons.preset_minus_y_icon, "preset_minus_y_icon"),
        (icons.preset_plus_z_icon, "preset_plus_z_icon"),
        (icons.preset_minus_z_icon, "preset_minus_z_icon"),
        (icons.preset_isometric_icon, "preset_isometric_icon"),
        # qtawesome-icons-2026q2-e2 (UPL-4 v1) — display toggles
        (icons.wireframe_icon, "wireframe_icon"),
        (icons.show_edges_icon, "show_edges_icon"),
        # enriques-hq-smoothing-2026q3-e1 (UPL-18-followup) — opt-in
        # second-Taubin display-toggle icon.
        (icons.hq_smoothing_icon, "hq_smoothing_icon"),
    )
    for fn, name in targets:
        for theme in ("dark", "light"):
            icon = fn(theme)
            assert not icon.isNull(), (
                f"{name}({theme!r}) returned a null QIcon — either the MDI 6 "
                f"icon name is wrong or the qtawesome font failed to load."
            )


# =============================================================================
# qtawesome-icons-2026q2-e2 (UPL-4 v1) — camera presets + display toggles
# =============================================================================


def test_v0_icons_still_bind_correctly() -> None:
    """Regression guard for the v0 icon factories (qtawesome-icons-2026q2-e1).

    All three original v0 icons (Reset Camera, Screenshot, Reset Defaults)
    must continue to call ``qta.icon()`` with the original MDI 6 icon names.
    The v1 milestone (qtawesome-icons-2026q2-e2) extends ``icons.py`` with 9
    additional factories — this test fails loudly if a v1 refactor renames,
    re-routes, or accidentally removes any v0 icon binding.

    Mocked at the qta boundary (AI-2 compliant).
    """
    from unittest.mock import MagicMock, patch
    import icons

    mock_qta = MagicMock()
    mock_qta.icon.return_value = MagicMock(name="QIcon")

    v0_bindings = (
        # (factory, expected mdi6 name, expected color helper)
        (icons.reset_camera_icon, "mdi6.fit-to-screen", "_icon_color"),
        (icons.screenshot_icon, "mdi6.camera", "_icon_color"),
        (icons.reset_defaults_icon, "mdi6.restore", "_reset_defaults_icon_color"),
    )

    with patch.object(icons, "_qta", mock_qta):
        for factory, expected_name, color_helper_name in v0_bindings:
            for theme in ("dark", "light"):
                mock_qta.icon.reset_mock()
                factory(theme)
                expected_color = getattr(icons, color_helper_name)(theme)
                mock_qta.icon.assert_called_with(expected_name, color=expected_color)


def test_camera_preset_icons_correct_names_and_colors() -> None:
    """v1: each of the 7 camera-preset factories calls ``qta.icon()`` with
    the right ``mdi6.axis-*-arrow`` name, the right ``rotated=`` value
    (0/absent for + directions, 180 for - directions), and the TEXT_VALUE
    color routed through ``_icon_color(theme)``.  Covers BOTH themes.

    Mocked (AI-2 compliant).
    """
    from unittest.mock import MagicMock, patch
    import icons

    mock_qta = MagicMock()
    mock_qta.icon.return_value = MagicMock(name="QIcon")

    # (factory, expected mdi6 name, expected rotated kwarg or None)
    preset_bindings = (
        (icons.preset_plus_x_icon,    "mdi6.axis-x-arrow", None),
        (icons.preset_minus_x_icon,   "mdi6.axis-x-arrow", 180),
        (icons.preset_plus_y_icon,    "mdi6.axis-y-arrow", None),
        (icons.preset_minus_y_icon,   "mdi6.axis-y-arrow", 180),
        (icons.preset_plus_z_icon,    "mdi6.axis-z-arrow", None),
        (icons.preset_minus_z_icon,   "mdi6.axis-z-arrow", 180),
        (icons.preset_isometric_icon, "mdi6.axis-arrow",   None),
    )

    with patch.object(icons, "_qta", mock_qta):
        for factory, expected_name, expected_rotated in preset_bindings:
            for theme in ("dark", "light"):
                mock_qta.icon.reset_mock()
                factory(theme)
                expected_color = icons._icon_color(theme)
                if expected_rotated is None:
                    mock_qta.icon.assert_called_with(expected_name, color=expected_color)
                else:
                    mock_qta.icon.assert_called_with(
                        expected_name, color=expected_color, rotated=expected_rotated
                    )


def test_display_toggle_icons_correct_names_and_colors() -> None:
    """v1: ``wireframe_icon`` uses ``mdi6.grid`` and ``show_edges_icon`` uses
    ``mdi6.border-outside``, both with the TEXT_VALUE color (NOT
    TEXT_RESET_BTN — these are standard display toggles, not the
    destructive-action Reset Defaults variant).  Both themes covered.

    Mocked (AI-2 compliant).
    """
    from unittest.mock import MagicMock, patch
    import icons

    mock_qta = MagicMock()
    mock_qta.icon.return_value = MagicMock(name="QIcon")

    toggle_bindings = (
        (icons.wireframe_icon,  "mdi6.grid"),
        (icons.show_edges_icon, "mdi6.border-outside"),
        (icons.hq_smoothing_icon, "mdi6.auto-fix"),
    )

    with patch.object(icons, "_qta", mock_qta):
        for factory, expected_name in toggle_bindings:
            for theme in ("dark", "light"):
                mock_qta.icon.reset_mock()
                factory(theme)
                expected_color = icons._icon_color(theme)
                mock_qta.icon.assert_called_with(expected_name, color=expected_color)


def test_wireframe_and_edges_icons_are_distinct_names() -> None:
    """v1: the Wireframe and Show-edges toggles produce visually similar
    effects in the VTK viewport (both relate to surface edges); their icons
    MUST use different ``mdi6.*`` names so users can distinguish the two
    toggles at a glance.  This guards against a copy-paste error during
    future palette / icon refreshes.

    Asserts on the module-level ``WIREFRAME_ICON_NAME`` /
    ``SHOW_EDGES_ICON_NAME`` constants exposed for this purpose (rather
    than docstring scraping).
    """
    import icons

    assert icons.WIREFRAME_ICON_NAME != icons.SHOW_EDGES_ICON_NAME, (
        f"WIREFRAME_ICON_NAME ({icons.WIREFRAME_ICON_NAME!r}) and "
        f"SHOW_EDGES_ICON_NAME ({icons.SHOW_EDGES_ICON_NAME!r}) must use "
        f"different MDI 6 glyphs so the two display toggles are visually "
        f"distinct at 16px."
    )
    # Both must be non-empty mdi6.* strings (lightweight format guard).
    assert icons.WIREFRAME_ICON_NAME.startswith("mdi6."), (
        f"WIREFRAME_ICON_NAME ({icons.WIREFRAME_ICON_NAME!r}) is not mdi6.*"
    )
    assert icons.SHOW_EDGES_ICON_NAME.startswith("mdi6."), (
        f"SHOW_EDGES_ICON_NAME ({icons.SHOW_EDGES_ICON_NAME!r}) is not mdi6.*"
    )
    # enriques-hq-smoothing-2026q3-e1 (rect F-M3): HQ smoothing joins
    # the same Display group — its icon must be distinct from both
    # siblings so the three toggles are visually orthogonal at 16px.
    assert icons.HQ_SMOOTHING_ICON_NAME != icons.WIREFRAME_ICON_NAME, (
        f"HQ_SMOOTHING_ICON_NAME ({icons.HQ_SMOOTHING_ICON_NAME!r}) "
        f"must differ from WIREFRAME_ICON_NAME — three sibling display "
        f"toggles in the same group must use visually orthogonal glyphs."
    )
    assert icons.HQ_SMOOTHING_ICON_NAME != icons.SHOW_EDGES_ICON_NAME, (
        f"HQ_SMOOTHING_ICON_NAME ({icons.HQ_SMOOTHING_ICON_NAME!r}) "
        f"must differ from SHOW_EDGES_ICON_NAME."
    )
    assert icons.HQ_SMOOTHING_ICON_NAME.startswith("mdi6."), (
        f"HQ_SMOOTHING_ICON_NAME ({icons.HQ_SMOOTHING_ICON_NAME!r}) is not mdi6.*"
    )
