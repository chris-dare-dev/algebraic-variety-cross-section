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

    Rectified in the milestone's rect commit: wraps the lazy import in a
    ``try/except ImportError`` that re-raises with a clear install hint.
    The unhelpful "No module named 'qtawesome'" stack trace from a missing
    requirement was the adversary critic's MEDIUM-1 finding.
    """
    global _qta
    if _qta is None:
        try:
            import qtawesome as _qtawesome
        except ImportError as e:
            raise RuntimeError(
                "qtawesome is required for app icons but was not found in the "
                "Python environment.  Install the project requirements:\n"
                "    pip install -r requirements.txt\n"
                "(qtawesome>=1.4.2,<2 — MIT-licensed icon-font wrapper.)"
            ) from e
        _qta = _qtawesome
    return _qta


def _icon_color(theme: str) -> str:
    """Return the 6-digit hex icon color for the given theme.

    Uses ``TEXT_VALUE`` from the active palette — the highest-contrast
    text token (11.09:1 on ``BG_PANEL`` light, 11.60:1 on ``BG_PANEL`` dark).
    Icons styled this way are legible in both themes without requiring a
    separate icon-color token.

    AI-12 / AI-13 compliant: 6-digit hex from a tested palette.  Any theme
    name other than ``"light"`` resolves to the dark palette (matching the
    launch default established in dark-mode-2026q2-e1).
    """
    palette = styles.PALETTE_LIGHT if theme == "light" else styles.PALETTE_DARK
    return palette["TEXT_VALUE"]


def _reset_defaults_icon_color(theme: str) -> str:
    """Return the 6-digit hex icon color for the Reset Defaults button.

    The Reset Defaults button has a distinct red-family visual identity
    (``BG_RESET_BTN`` pink/wine + ``TEXT_RESET_BTN`` rose text).  Using the
    neutral ``TEXT_VALUE`` for the icon glyph would make it look like a
    stray grey/white icon on the red-family button — inconsistent with the
    button's intentional color coding.  This helper routes the icon color
    through ``TEXT_RESET_BTN`` so the icon participates in the button's
    visual identity rather than fighting it.  (Frontend-ux critic MEDIUM-1.)

    Both values are pre-verified to clear WCAG 3:1 non-text contrast on the
    matching ``BG_RESET_BTN`` background (8.37:1 light, 9.32:1 dark).
    """
    palette = styles.PALETTE_LIGHT if theme == "light" else styles.PALETTE_DARK
    return palette["TEXT_RESET_BTN"]


def reset_camera_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Reset Camera button (``mdi6.fit-to-screen``).

    Two diagonal corner brackets pointing inward — semantically "fit /
    frame the surface in the viewport".  Replaces the original
    ``mdi6.camera-retake`` pick to disambiguate from the Screenshot
    button's camera glyph at small icon sizes (frontend-ux critic
    MEDIUM-2: both icons shared a camera-body anchor that became
    indistinguishable at the 16-22px default macOS icon size).  This
    matches the 3D Slicer convention for the "reset / center view" action.
    """
    return _get_qta().icon("mdi6.fit-to-screen", color=_icon_color(theme))


def screenshot_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Screenshot button (``mdi6.camera``).

    Classic photograph camera — universally recognized "take a photo".
    Now that Reset Camera uses ``mdi6.fit-to-screen``, the camera glyph
    is unambiguously the screenshot action.
    """
    return _get_qta().icon("mdi6.camera", color=_icon_color(theme))


def reset_defaults_icon(theme: str = "dark") -> QIcon:
    """Return a QIcon for the Reset Defaults button (``mdi6.restore``).

    Counterclockwise circular arrow — universally recognized "restore to
    prior state".  Color is routed through ``_reset_defaults_icon_color``
    (TEXT_RESET_BTN) so the icon glyph matches the button's red-family
    text label, preserving the button's color-coded visual identity
    (frontend-ux critic MEDIUM-1).
    """
    return _get_qta().icon(
        "mdi6.restore",
        color=_reset_defaults_icon_color(theme),
    )
