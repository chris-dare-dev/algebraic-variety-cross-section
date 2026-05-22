"""Icon factory for Algebraic Variety Viewer (qtawesome-icons-2026q2-e1, UPL-4).

Single source of truth for the application's `QIcon`s.  Adopting qtawesome
gives the toolbar buttons (Reset Camera / Screenshot / Reset Defaults)
visual anchors that reduce cognitive load — researchers can locate the
right button by icon shape before reading the label.

Lazy-import discipline
----------------------
``qtawesome``'s icon-font cache takes ~150-200ms to populate on first use
(the SIL Open Font License MaterialDesign font is loaded into Qt's font
database).  To keep ``app.py`` import fast, this module DOES NOT import
``qtawesome`` at module load — the ``_qta`` sentinel stays ``None`` until
the first icon function is invoked.  The library-scout's institutional
memory documents this cost; the test
``test_icons_module_does_not_import_qtawesome_at_module_load`` enforces it.

QApplication requirement
------------------------
``qta.icon()`` requires a running ``QApplication`` — without one, it
silently returns an empty ``QIcon`` and emits a ``UserWarning``.  Panels
MUST NOT call icon functions from ``_build_ui()`` constructors (which run
before ``MainWindow.__init__`` completes).  Instead, ``MainWindow.__init__``
calls each panel's ``refresh_icons(theme)`` method AFTER widget
construction, at which point the ``QApplication`` is fully active.  The
same ``refresh_icons(theme)`` call is invoked from ``_on_theme_changed``
and ``_apply_system_theme`` so icon color re-resolves on theme swap.

Theme-aware color
-----------------
Icon color resolves from the active palette's ``TEXT_VALUE`` token
(highest-contrast text on the panel ground: 11.09:1 light, 11.60:1 dark).
``_icon_color(theme)`` returns the right hex string given a theme name —
no module-level mutable state.  This mirrors ``styles.get_variety_default_colors(theme)``.

Icons
-----
``mdi6.camera-retake``   Reset Camera — camera body + circular refresh arrow
``mdi6.camera``          Screenshot   — classic photograph camera
``mdi6.restore``         Reset Defaults — counterclockwise undo arrow
"""
from __future__ import annotations

from PySide6.QtGui import QIcon

import styles

# Module-level sentinel.  Stays None until the first icon function is called,
# at which point _get_qta() imports qtawesome and assigns the module here.
# Tests rely on this attribute being publicly inspectable (verified by
# test_icons_module_does_not_import_qtawesome_at_module_load).
_qta = None


def _get_qta():
    """Lazy-import qtawesome on first call.

    Subsequent calls reuse the cached module reference.  This defers the
    ~150-200ms font-load cost from app launch to the first icon
    construction (which happens inside ``MainWindow.__init__`` after the
    panels are built, not during module import).
    """
    global _qta
    if _qta is None:
        import qtawesome as _qtawesome

        _qta = _qtawesome
    return _qta


def _icon_color(theme: str) -> str:
    """Return the 6-digit hex icon color for the given theme.

    Uses ``TEXT_VALUE`` from the active palette — the highest-contrast
    text token (11.09:1 on ``BG_PANEL`` light, 11.60:1 on ``BG_PANEL`` dark).
    Icons styled this way are equally legible in both themes without
    requiring a separate icon-color token.

    AI-12 / AI-13 compliant: 6-digit hex from a tested palette.  Any theme
    name other than ``"light"`` resolves to the dark palette (matching the
    launch default established in dark-mode-2026q2-e1).
    """
    palette = styles.PALETTE_LIGHT if theme == "light" else styles.PALETTE_DARK
    return palette["TEXT_VALUE"]


def reset_camera_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Reset Camera button (``mdi6.camera-retake``).

    Camera body with circular refresh arrow — semantically "reset the
    camera to its default position".  Researcher-validated as the best
    MaterialDesign candidate over ``camera-control`` (pan/navigate
    semantic) and ``camera-marker`` (geotagging).
    """
    return _get_qta().icon("mdi6.camera-retake", color=_icon_color(theme))


def screenshot_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Screenshot button (``mdi6.camera``).

    Classic photograph camera — universally recognized "take a photo".
    """
    return _get_qta().icon("mdi6.camera", color=_icon_color(theme))


def reset_defaults_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Reset Defaults button (``mdi6.restore``).

    Counterclockwise circular arrow — universally recognized "restore to
    prior state".  Preferred over ``fa6s.rotate-left`` (partial rotation)
    because the full circle communicates "undo all" rather than "rotate".
    """
    return _get_qta().icon("mdi6.restore", color=_icon_color(theme))
