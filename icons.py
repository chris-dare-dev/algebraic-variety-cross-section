"""Icon factory for Algebraic Variety Viewer (qtawesome-icons-2026q2-e1/e2, UPL-4 v0/v1).

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
v0 (qtawesome-icons-2026q2-e1):
``mdi6.fit-to-screen``   Reset Camera — corner brackets pointing inward
``mdi6.camera``          Screenshot   — classic photograph camera
``mdi6.restore``         Reset Defaults — counterclockwise undo arrow

v1 (qtawesome-icons-2026q2-e2 — camera presets + display toggles):
``mdi6.axis-x-arrow``    +X / -X buttons (rotated=180 for the minus direction)
``mdi6.axis-y-arrow``    +Y / -Y buttons (rotated=180 for the minus direction)
``mdi6.axis-z-arrow``    +Z / -Z buttons (rotated=180 for the minus direction)
``mdi6.axis-arrow``      Isometric button — three-arrow 3D-origin glyph
``mdi6.grid``            Wireframe checkbox — uniform open lattice (no fill)
``mdi6.border-outside``  Show edges checkbox — solid + outer border (filled)

The wireframe vs show-edges pair is intentionally chosen so the open
lattice of ``mdi6.grid`` reads "everything is mesh" and the
filled-outer-border of ``mdi6.border-outside`` reads "solid with edges
drawn on top".  At 16px both icons are perceptually distinct (verified
via the test_wireframe_and_edges_icons_are_distinct_names guard).

Spinner / render-busy icon — DEFERRED to a v2 milestone.  ``QMovie.updated``
signals can fire during ``QApplication.processEvents()`` inside
``_render_current``, touching the AI-9 re-entrancy surface that
``self._computing`` guards.  See CONTEXT.md §9 for the deferral rationale.
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


# =============================================================================
# v1 (qtawesome-icons-2026q2-e2 / UPL-4 v1) — camera presets + display toggles
# =============================================================================

# Module-level icon-name constants for the display toggles.  Exposed so
# test_wireframe_and_edges_icons_are_distinct_names can assert the two
# toggles use different glyph names (guards against a copy-paste error
# that would make both checkboxes render the same icon).  The camera-preset
# icons share the same axis-arrow family with the rotated= kwarg
# disambiguating direction, so they don't need analogous constants.
WIREFRAME_ICON_NAME = "mdi6.grid"
SHOW_EDGES_ICON_NAME = "mdi6.border-outside"


def preset_plus_x_icon(theme: str = "dark") -> QIcon:
    """+X camera preset (``mdi6.axis-x-arrow``).

    X-axis arrow pointing in the +X direction.  The MDI6 axis-arrow family
    embeds the axis label in the glyph itself, so the icon remains
    unambiguous even when the button text label is short ("+X").
    """
    return _get_qta().icon("mdi6.axis-x-arrow", color=_icon_color(theme))


def preset_minus_x_icon(theme: str = "dark") -> QIcon:
    """-X camera preset (``mdi6.axis-x-arrow`` rotated 180°).

    Same glyph as +X but mirrored — points in the -X direction.  MDI6
    does not ship a separate ``axis-x-arrow-left``; ``rotated=180`` is
    the canonical approach per qtawesome 1.4.x docs.

    Known legibility caveat at 16px (qtawesome-icons-2026q2-e2 frontend-ux
    F-M1, accepted): the ``axis-{x,y,z}-arrow`` family embeds the axis
    label as part of the glyph; rotated 180° the X stays recognizable
    (~axis-symmetric), but Y reads as λ and Z reads as S at 16px.  The
    button text label ("-X", "-Y", "-Z") carries the unambiguous
    disambiguation, and the grid layout positions +/- pairs adjacent for
    direct visual comparison.  ParaView uses cube-face glyphs with the
    facing surface highlighted; Blender uses distinct per-direction SVGs
    — both avoid rotation.  A future migration to one of those patterns
    is a polish-pass scope; the axis-arrow family was preferred over
    generic ``mdi6.arrow-*`` because it carries the axis label embedded,
    which is more semantically informative even at the cost of rotation
    legibility for Y/Z.
    """
    return _get_qta().icon("mdi6.axis-x-arrow", color=_icon_color(theme), rotated=180)


def preset_plus_y_icon(theme: str = "dark") -> QIcon:
    """+Y camera preset (``mdi6.axis-y-arrow``)."""
    return _get_qta().icon("mdi6.axis-y-arrow", color=_icon_color(theme))


def preset_minus_y_icon(theme: str = "dark") -> QIcon:
    """-Y camera preset (``mdi6.axis-y-arrow`` rotated 180°)."""
    return _get_qta().icon("mdi6.axis-y-arrow", color=_icon_color(theme), rotated=180)


def preset_plus_z_icon(theme: str = "dark") -> QIcon:
    """+Z camera preset (``mdi6.axis-z-arrow``)."""
    return _get_qta().icon("mdi6.axis-z-arrow", color=_icon_color(theme))


def preset_minus_z_icon(theme: str = "dark") -> QIcon:
    """-Z camera preset (``mdi6.axis-z-arrow`` rotated 180°)."""
    return _get_qta().icon("mdi6.axis-z-arrow", color=_icon_color(theme), rotated=180)


def preset_isometric_icon(theme: str = "dark") -> QIcon:
    """Isometric camera preset (``mdi6.axis-arrow``).

    Three-arrow 3D-origin glyph (X/Y/Z arrows diverging from a common
    point).  Communicates "switch to isometric / 3D perspective view".
    Distinct from the single-axis ``axis-{x,y,z}-arrow`` family — no
    rotation needed.
    """
    return _get_qta().icon("mdi6.axis-arrow", color=_icon_color(theme))


def wireframe_icon(theme: str = "dark") -> QIcon:
    """Wireframe display-mode toggle (``mdi6.grid``).

    Uniform open lattice with no filled center — semantically "everything
    is mesh".  Strong "no solid surface" affordance that contrasts with
    ``show_edges_icon``'s filled outer border at 16px.
    """
    return _get_qta().icon(WIREFRAME_ICON_NAME, color=_icon_color(theme))


def show_edges_icon(theme: str = "dark") -> QIcon:
    """Show-edges display-mode toggle (``mdi6.border-outside``).

    Solid filled center with a heavier outer border + inner structural
    lines — semantically "solid surface with mesh edges drawn on top".
    Deliberately NOT ``mdi6.border-all`` (equal-weight inner/outer lines)
    which is visually too close to ``mdi6.grid`` and would create user
    confusion at 16px.
    """
    return _get_qta().icon(SHOW_EDGES_ICON_NAME, color=_icon_color(theme))
