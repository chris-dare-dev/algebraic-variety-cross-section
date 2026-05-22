"""Appearance panel for the Algebraic Variety Viewer.

Provides surface and background appearance controls in a self-contained
QWidget that can be docked on the right side of the main window.

All settings persist when the user switches surfaces: call
``apply_to_actor(new_actor)`` after each new mesh is added to the plotter.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from styles import (
    BG_SURFACE_DEFAULT,
    BG_VIEWPORT,
    BORDER_SWATCH,
    VALUE_MONO_STYLE,
)


def _make_swatch(color: QColor, size: int = 20) -> QLabel:
    """Return a QLabel styled as a solid color swatch."""
    swatch = QLabel()
    swatch.setFixedSize(size, size)
    swatch.setFrameShape(QFrame.Shape.Box)
    swatch.setFrameShadow(QFrame.Shadow.Sunken)
    _apply_swatch_color(swatch, color)
    return swatch


def _apply_swatch_color(swatch: QLabel, color: QColor) -> None:
    hex_color = color.name()
    swatch.setStyleSheet(
        f"background-color: {hex_color}; border: 1px solid {BORDER_SWATCH};"
    )


class AppearancePanel(QWidget):
    """Vertical panel of surface appearance controls.

    Parameters
    ----------
    get_actor:
        Zero-argument callable returning the current VTK actor (or None).
    get_plotter:
        Zero-argument callable returning the pyvistaqt QtInteractor.
    """

    def __init__(
        self,
        get_actor: Callable,
        get_plotter: Callable,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._get_actor = get_actor
        self._get_plotter = get_plotter

        # --- stored appearance state (persists across mesh switches) ----------
        # Default colors come from the central palette tokens (UPL-1):
        #   BG_SURFACE_DEFAULT — lightsteelblue mesh fill
        #   BG_VIEWPORT        — dark grey viewport background
        # On variety/subtype switch, MainWindow calls self.set_default_color()
        # (added in variety-palette-2026q2-e1) to seed _surface_color from
        # styles.VARIETY_DEFAULT_COLOR — see the method below.  User overrides
        # via the "Surface…" swatch still win for the rest of the session.
        self._surface_color = QColor(BG_SURFACE_DEFAULT)
        self._bg_color = QColor(BG_VIEWPORT)
        self._wireframe = False
        self._show_edges = False
        self._opacity = 100          # 0-100 integer (maps to 0.0-1.0)
        self._shading = "Phong"      # "Phong" or "Flat"
        # enriques-backface-2026q2-e1 (UPL-7): per-variety back-face culling.
        # Defaults to None (no culling — the safe default for closed-topology
        # K3, point-singular Kummer, and AI-7-disconnected Hanson surfaces).
        # MainWindow sets it to "back" only for the Enriques family on variety
        # switch — see set_culling() below + the per-variety gate in app.py.
        self._culling: str | None = None

        self._build_ui()

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Use minimum width instead of fixed width so the dock is resizable
        # on HiDPI displays and when the user manually widens it.
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        # Scroll area so the panel still works on small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll, stretch=1)

        inner = QWidget()
        scroll.setWidget(inner)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        layout.addWidget(self._build_color_group())
        layout.addWidget(self._build_toggles_group())
        layout.addWidget(self._build_opacity_group())
        layout.addWidget(self._build_shading_group())
        layout.addStretch(1)

    def _build_color_group(self) -> QGroupBox:
        box = QGroupBox("Colors")
        vl = QVBoxLayout(box)
        vl.setSpacing(6)

        # Surface color row
        surf_row = QHBoxLayout()
        surf_row.setSpacing(6)
        self._surf_swatch = _make_swatch(self._surface_color)
        surf_btn = QPushButton("Surface…")
        surf_btn.setToolTip("Choose the surface fill color")
        surf_btn.clicked.connect(self._pick_surface_color)
        surf_row.addWidget(self._surf_swatch)
        surf_row.addWidget(surf_btn, stretch=1)
        vl.addLayout(surf_row)

        # Background color row
        bg_row = QHBoxLayout()
        bg_row.setSpacing(6)
        self._bg_swatch = _make_swatch(self._bg_color)
        bg_btn = QPushButton("Background…")
        bg_btn.setToolTip("Choose the viewport background color")
        bg_btn.clicked.connect(self._pick_bg_color)
        bg_row.addWidget(self._bg_swatch)
        bg_row.addWidget(bg_btn, stretch=1)
        vl.addLayout(bg_row)

        return box

    def _build_toggles_group(self) -> QGroupBox:
        box = QGroupBox("Display")
        vl = QVBoxLayout(box)
        vl.setSpacing(4)

        self._wireframe_cb = QCheckBox("Wireframe")
        self._wireframe_cb.setChecked(self._wireframe)
        self._wireframe_cb.setToolTip("Show the surface as a wireframe mesh instead of a solid")
        self._wireframe_cb.toggled.connect(self._on_wireframe_toggled)
        vl.addWidget(self._wireframe_cb)

        self._edges_cb = QCheckBox("Show edges")
        self._edges_cb.setChecked(self._show_edges)
        self._edges_cb.setToolTip(
            "Overlay mesh edges on the solid surface (inactive in wireframe mode)"
        )
        self._edges_cb.toggled.connect(self._on_edges_toggled)
        vl.addWidget(self._edges_cb)

        return box

    def _build_opacity_group(self) -> QGroupBox:
        box = QGroupBox("Opacity")
        vl = QVBoxLayout(box)
        vl.setSpacing(4)

        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(0, 100)
        self._opacity_slider.setValue(self._opacity)
        self._opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._opacity_slider.setTickInterval(25)
        self._opacity_slider.setToolTip("Surface opacity: 0% = fully transparent, 100% = opaque")
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        vl.addWidget(self._opacity_slider)

        self._opacity_label = QLabel(f"{self._opacity}%")
        self._opacity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # dark-mode-2026q2-e1 rect: use QSS role property so the active theme's
        # color cascades from APP_STYLESHEET / APP_STYLESHEET_DARK (was
        # `setStyleSheet(VALUE_MONO_STYLE)` which hardcoded the light color).
        self._opacity_label.setProperty("role", "value-mono")
        vl.addWidget(self._opacity_label)

        return box

    def _build_shading_group(self) -> QGroupBox:
        box = QGroupBox("Shading")
        vl = QVBoxLayout(box)
        vl.setSpacing(4)

        self._shading_group = QButtonGroup(self)
        self._smooth_rb = QRadioButton("Smooth (Phong)")
        self._smooth_rb.setToolTip(
            "Phong interpolation: smooth normals produce a glossy, rounded appearance"
        )
        self._flat_rb = QRadioButton("Flat")
        self._flat_rb.setToolTip(
            "Flat shading: each triangle has a uniform color — accentuates the mesh structure"
        )
        self._shading_group.addButton(self._smooth_rb, 0)
        self._shading_group.addButton(self._flat_rb, 1)

        if self._shading == "Phong":
            self._smooth_rb.setChecked(True)
        else:
            self._flat_rb.setChecked(True)

        self._smooth_rb.toggled.connect(self._on_shading_changed)
        vl.addWidget(self._smooth_rb)
        vl.addWidget(self._flat_rb)

        return box

    # -----------------------------------------------------------------------
    # Slot handlers
    # -----------------------------------------------------------------------

    def _pick_surface_color(self) -> None:
        color = QColorDialog.getColor(
            self._surface_color,
            self,
            "Choose surface color",
        )
        if color.isValid():
            self._surface_color = color
            _apply_swatch_color(self._surf_swatch, color)
            actor = self._get_actor()
            if actor is not None:
                actor.prop.color = color.name()
                self._get_plotter().render()

    def _pick_bg_color(self) -> None:
        color = QColorDialog.getColor(
            self._bg_color,
            self,
            "Choose background color",
        )
        if color.isValid():
            self._bg_color = color
            _apply_swatch_color(self._bg_swatch, color)
            self._get_plotter().set_background(color.name())
            self._get_plotter().render()

    def _on_wireframe_toggled(self, checked: bool) -> None:
        self._wireframe = checked
        actor = self._get_actor()
        if actor is not None:
            actor.prop.style = "wireframe" if checked else "surface"
            self._get_plotter().render()

    def _on_edges_toggled(self, checked: bool) -> None:
        self._show_edges = checked
        actor = self._get_actor()
        if actor is not None:
            # Edges are only meaningful in surface style
            if not self._wireframe:
                actor.prop.show_edges = checked
            self._get_plotter().render()

    def _on_opacity_changed(self, value: int) -> None:
        self._opacity = value
        self._opacity_label.setText(f"{value}%")
        actor = self._get_actor()
        if actor is not None:
            actor.prop.opacity = value / 100.0
            self._get_plotter().render()

    def _on_shading_changed(self, checked: bool) -> None:
        # toggled fires for both the button being checked AND unchecked;
        # we only care about the one that becomes checked.
        if not checked:
            return
        self._shading = "Phong" if self._smooth_rb.isChecked() else "Flat"
        actor = self._get_actor()
        if actor is not None:
            actor.prop.interpolation = self._shading
            self._get_plotter().render()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def apply_background(self) -> None:
        """Apply the stored background color to the plotter.

        Independent of actor state — safe to call before any mesh has been
        added (e.g. from ``MainWindow.__init__`` to set the launch background
        before the first surface renders, eliminating the VTK-default-bg flash).
        """
        self._get_plotter().set_background(self._bg_color.name())

    def apply_to_actor(self, actor) -> None:
        """Re-apply all stored appearance settings.

        Background color is applied unconditionally (independent of actor).
        Actor-specific properties (color, wireframe, opacity, shading) are
        applied only when *actor* is not ``None``.
        """
        self.apply_background()

        if actor is None:
            return

        actor.prop.color = self._surface_color.name()
        actor.prop.style = "wireframe" if self._wireframe else "surface"
        if not self._wireframe:
            actor.prop.show_edges = self._show_edges
        actor.prop.opacity = self._opacity / 100.0
        actor.prop.interpolation = self._shading
        # enriques-backface-2026q2-e1 (UPL-7) rect MEDIUM-2: apply per-variety
        # culling, BUT suppress it in wireframe mode.  Culling is a shading
        # concern (kills the white zipper at Enriques double curves under
        # Phong lighting), not a topology-display concern — in wireframe mode
        # the user is inspecting mesh edges and expects to see all of them,
        # not have back-facing edges silently hidden as the camera rotates.
        # Mathematica's ContourPlot3D follows the same convention: the
        # Mesh -> True overlay is rendered two-sided regardless of the body
        # shading mode.  The set_culling state (self._culling) is preserved
        # across toggles — when the user turns wireframe back off, culling
        # re-engages.
        effective_culling = "none" if self._wireframe else (self._culling or "none")
        actor.prop.culling = effective_culling

    def set_default_color(self, hex_str: str) -> None:
        """Seed the surface color from the variety-family default (UPL-2).

        Called by ``MainWindow`` on variety / subtype switch — see
        ``app.py:_on_variety_changed`` and ``_on_subtype_changed`` for the
        wire points.  The user's subsequent override via the "Surface…"
        swatch still wins for the rest of that surface session; this only
        sets the starting point so each family is visually distinct on
        first render.

        Does NOT trigger a render: the caller flows naturally into
        ``_render_current`` → ``apply_to_actor`` which reads
        ``self._surface_color`` on the next pass.  This keeps the method
        safe to call before any actor exists (first launch) and free of
        AI-9 re-entrancy concerns.

        Invalid hex strings (failed ``QColor.isValid()``) are silently
        ignored; the existing colour is preserved.  A future invalid value
        from ``VARIETY_DEFAULT_COLOR`` would be caught by
        ``test_variety_default_color_all_six_digit_hex`` before reaching
        runtime.
        """
        color = QColor(hex_str)
        if not color.isValid():
            return
        self._surface_color = color
        _apply_swatch_color(self._surf_swatch, color)

    def set_culling(self, value: str | None) -> None:
        """Set the back-face culling policy for the next actor render
        (enriques-backface-2026q2-e1 / UPL-7).

        Accepts ``"back"``, ``"front"``, ``"none"`` (or ``None`` for the
        default no-culling state).  Called by ``MainWindow._on_variety_changed``
        with ``"back"`` ONLY when the active variety is "Enriques surface"
        — see the per-variety gate at that call site.  Other varieties
        receive ``None`` to clear any stale Enriques setting.

        Why not universal: the Enriques family has double-curve
        singularities (Figs. 1, 2 of the sextic family) where two sheets
        approach zero separation; marching cubes produces alternating
        front/back triangles at those ridges, and Phong lighting renders
        them as zipper noise.  Back-face culling removes the
        inward-facing half cleanly.  The same setting BREAKS:
          - Hanson CY3 — AI-7's ``consistent_normals=False`` patches
            have non-globally-oriented normals; culling hides whole
            patches as the camera rotates (catastrophic loss).
          - Kummer K3 — point-conical nodes have inner cone faces
            viewable through hollows; culling hides them (moderate).

        Note: Enriques wing-tip truncation at the viewport edge is a
        sampling-bounds artifact (the surface extends past the
        marching-cubes grid), NOT a culling effect.  Culling and bounds
        clipping are orthogonal; removing culling would not restore the
        wing tips.

        See CONTEXT.md §8.13 for the per-figure topology audit (Figs. 1+2
        have double curves; Fig. 3 / Cayley symmetroid has ordinary A₁
        nodes — culling is a no-op there; Fig. 4 has A₁ nodes with
        marching-cubes resolution high enough that culling still helps).

        Does NOT trigger a render — the caller flows into the existing
        ``_render_current`` → ``apply_to_actor`` chain, which reads
        ``self._culling`` and sets ``actor.prop.culling`` on the next
        pass.  AI-9 safe (no ``processEvents``).
        """
        self._culling = value

    def refresh_icons(self, theme: str = "dark") -> None:
        """Re-apply qtawesome icons to the Wireframe + Show-edges display
        toggles with the active theme's color
        (qtawesome-icons-2026q2-e2 / UPL-4 v1).

        Called by ``MainWindow.__init__`` (initial paint, after widget
        construction so ``QApplication`` is alive) and by
        ``MainWindow._on_theme_changed`` / ``_apply_system_theme`` (so
        icons re-render with the new color on theme swap).  Must NOT be
        called from ``_build_toggles_group()`` — at that point
        ``QApplication`` is not yet fully active and ``qta.icon()``
        silently returns an empty ``QIcon`` (CONTEXT.md §8.12 footgun).

        Why these two checkboxes get icons:
        - ``self._wireframe_cb`` (Wireframe) — ``mdi6.grid`` (open lattice)
        - ``self._edges_cb`` (Show edges) — ``mdi6.border-outside``
          (solid + outer border)

        The two icons are intentionally chosen to be visually distinct at
        16px since the two toggles produce visually similar VTK effects
        — see ``icons.WIREFRAME_ICON_NAME`` / ``SHOW_EDGES_ICON_NAME``
        and the ``test_wireframe_and_edges_icons_are_distinct_names``
        regression guard.

        ``QCheckBox`` inherits ``setIcon()`` from ``QAbstractButton``;
        the icon renders between the check-square indicator and the
        text label.  No QToolButton migration required.  Sets a fixed
        ``QSize(16, 16)`` to match the view-panel preset-button
        convention so the Appearance dock's vertical rhythm aligns.
        AI-9 safe (synchronous ``setIcon`` / ``setIconSize`` calls).
        """
        import icons
        from PySide6.QtCore import QSize

        _ICON_SIZE = QSize(16, 16)
        self._wireframe_cb.setIconSize(_ICON_SIZE)
        self._wireframe_cb.setIcon(icons.wireframe_icon(theme))
        self._edges_cb.setIconSize(_ICON_SIZE)
        self._edges_cb.setIcon(icons.show_edges_icon(theme))
