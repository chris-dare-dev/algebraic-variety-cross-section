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
    """
    from unittest.mock import MagicMock, patch
    import icons

    mock_qta = MagicMock()
    mock_qta.icon.return_value = MagicMock(name="QIcon")

    # Patch the cached qtawesome module so _get_qta() returns the mock.
    with patch.object(icons, "_qta", mock_qta):
        # Reset Camera — mdi6.camera-retake — dark palette
        icons.reset_camera_icon("dark")
        mock_qta.icon.assert_called_with(
            "mdi6.camera-retake",
            color=styles.PALETTE_DARK["TEXT_VALUE"],
        )
        mock_qta.icon.reset_mock()

        # Screenshot — mdi6.camera — light palette
        icons.screenshot_icon("light")
        mock_qta.icon.assert_called_with(
            "mdi6.camera",
            color=styles.PALETTE_LIGHT["TEXT_VALUE"],
        )
        mock_qta.icon.reset_mock()

        # Reset Defaults — mdi6.restore — dark palette
        icons.reset_defaults_icon("dark")
        mock_qta.icon.assert_called_with(
            "mdi6.restore",
            color=styles.PALETTE_DARK["TEXT_VALUE"],
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
