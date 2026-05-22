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
    )
    for fn, name in targets:
        for theme in ("dark", "light"):
            icon = fn(theme)
            assert not icon.isNull(), (
                f"{name}({theme!r}) returned a null QIcon — either the MDI 6 "
                f"icon name is wrong or the qtawesome font failed to load."
            )
