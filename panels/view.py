"""ViewPanel — left-side camera / scene-aid control panel.

Exported symbol: ViewPanel(QWidget)

Construction::

    panel = ViewPanel(plotter)   # plotter is a pyvistaqt.QtInteractor

After each surface switch, call::

    panel.re_apply_overlays()

to re-attach bounding-box and grid actors to the newly generated mesh.
"""

from __future__ import annotations

import logging
import numpy as np
import pyvista as pv
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

# MUTED_TEXT_STYLE / RANGE_LABEL_STYLE / VALUE_MONO_STYLE deprecated in
# dark-mode-2026q2-e1 — call sites use setProperty("role", X) so QSS role
# selectors handle theme-aware color cascade.  No import needed here.


class ViewPanel(QWidget):
    """Left-side panel providing view presets and scene-aid toggles."""

    # Emitted whenever the domain mode, radius, or overlay toggle changes.
    # MainWindow listens and re-clips the cached mesh without regenerating it.
    domain_changed = Signal()

    # Domain mode constants
    DOMAIN_NONE = "Off"
    DOMAIN_SPHERE = "Sphere"
    DOMAIN_CUBE = "Cube"

    def __init__(self, plotter) -> None:
        super().__init__()
        self._plotter = plotter

        # Overlay state
        self._bbox_actor = None   # vtkActor returned by add_bounding_box()
        self._grid_actor = None   # CubeAxesActor returned by show_grid()

        # qtawesome-icons-2026q2-e2 (UPL-4 v1): camera-preset buttons stored
        # as instance attrs so `refresh_icons(theme)` can re-apply icons on
        # theme switch.  Previously the 6 ortho preset buttons + iso button
        # were loop-locals in `_make_view_presets_group`, which made later
        # icon attachment from outside the constructor impossible (same
        # issue the v0 milestone fixed for `_reset_camera_btn`).  Keys are
        # the button text labels ("+X", "-X", "+Y", "-Y", "+Z", "-Z").
        self._preset_btns: dict[str, "QPushButton"] = {}
        self._iso_btn: "QPushButton | None" = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(8)

        root.addWidget(self._make_view_presets_group())
        root.addWidget(self._make_camera_group())
        root.addWidget(self._make_domain_group())
        root.addWidget(self._make_scene_aids_group())
        root.addWidget(self._make_screenshot_group())

        # Mouse-controls help — as a compact tooltip-style label at the bottom
        help_label = QLabel(
            "Left-drag: rotate  |  Scroll/Right-drag: zoom  |  Shift-drag: pan"
        )
        help_label.setWordWrap(True)
        help_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        # dark-mode-2026q2-e1 rect: QSS role property (was MUTED_TEXT_STYLE inline).
        help_label.setProperty("role", "muted")
        help_label.setToolTip(
            "Mouse controls for the 3D viewport:\n"
            "  Left-drag      — rotate\n"
            "  Scroll         — zoom in/out\n"
            "  Right-drag     — zoom (alternative)\n"
            "  Shift + drag   — pan\n\n"
            "Keyboard shortcuts:\n"
            "  Ctrl+R         — Reset Camera\n"
            "  Ctrl+Shift+S   — Screenshot\n"
            "  Ctrl+D         — Reset parameters to defaults"
        )
        root.addWidget(help_label)

        root.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    def _make_view_presets_group(self) -> QGroupBox:
        group = QGroupBox("View Presets")
        group.setToolTip("Snap the camera to a standard orthographic viewpoint")
        grid = QGridLayout(group)
        grid.setSpacing(4)

        # (label, row, col, plotter method name, tooltip)
        presets = [
            ("+X", 0, 0, "view_yz",   "Look along the +X axis (shows YZ plane)"),
            ("-X", 0, 1, "view_zy",   "Look along the -X axis (shows ZY plane)"),
            ("+Y", 1, 0, "view_xz",   "Look along the +Y axis (shows XZ plane)"),
            ("-Y", 1, 1, "view_zx",   "Look along the -Y axis (shows ZX plane)"),
            ("+Z", 2, 0, "view_xy",   "Look along the +Z axis (shows XY plane)"),
            ("-Z", 2, 1, "view_yx",   "Look along the -Z axis (shows YX plane)"),
        ]

        for label, row, col, method, tip in presets:
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.setToolTip(tip)
            btn.clicked.connect(self._make_view_callback(method))
            grid.addWidget(btn, row, col)
            # qtawesome-icons-2026q2-e2 (UPL-4 v1): store for refresh_icons.
            self._preset_btns[label] = btn

        self._iso_btn = QPushButton("Isometric")
        self._iso_btn.setFixedHeight(26)
        self._iso_btn.setToolTip("Switch to a standard isometric (perspective) view")
        self._iso_btn.clicked.connect(self._make_view_callback("view_isometric"))
        grid.addWidget(self._iso_btn, 3, 0, 1, 2)

        return group

    def _make_camera_group(self) -> QGroupBox:
        group = QGroupBox("Camera")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)

        # qtawesome-icons-2026q2-e1 (UPL-4): stored as instance attr so
        # refresh_icons(theme) can re-apply the icon on theme switch.
        # Previously a local variable, which made later icon attachment
        # impossible from outside this method.
        self._reset_camera_btn = QPushButton("Reset Camera")
        # Object name lets the app stylesheet give this button a distinct style
        self._reset_camera_btn.setObjectName("resetCameraBtn")
        self._reset_camera_btn.setToolTip("Fit the camera to the current surface (Ctrl+R)")
        self._reset_camera_btn.clicked.connect(self._on_reset_camera)
        layout.addWidget(self._reset_camera_btn)

        return group

    def _make_domain_group(self) -> QGroupBox:
        group = QGroupBox("Clip Region")
        group.setToolTip(
            "Clip the visible surface to a sphere or cube centered on the origin.\n"
            "'Off' shows the full surface without clipping."
        )
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Mode selector
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Shape:"))
        self._domain_mode = QComboBox()
        self._domain_mode.addItems([self.DOMAIN_NONE, self.DOMAIN_SPHERE, self.DOMAIN_CUBE])
        self._domain_mode.setCurrentText(self.DOMAIN_NONE)
        self._domain_mode.setToolTip(
            "Off — no clipping\n"
            "Sphere — clip to a sphere of the given radius\n"
            "Cube   — clip to a cube of the given half-side length"
        )
        self._domain_mode.currentTextChanged.connect(self._on_domain_mode_changed)
        mode_row.addWidget(self._domain_mode, stretch=1)
        layout.addLayout(mode_row)

        # Radius / half-side slider
        radius_header = QHBoxLayout()
        self._radius_label = QLabel("Radius")
        self._radius_label.setStyleSheet("font-size: 11px;")
        radius_header.addWidget(self._radius_label)
        radius_header.addStretch(1)
        self._radius_value = QLabel("2.50")
        # dark-mode-2026q2-e1 rect: QSS role property (was VALUE_MONO_STYLE inline).
        self._radius_value.setProperty("role", "value-mono")
        self._radius_value.setToolTip("Current clip radius / half-side length")
        radius_header.addWidget(self._radius_value)
        layout.addLayout(radius_header)

        # Slider stores radius * 100 (range 0.10 .. 10.00, step 0.05)
        self._radius_slider = QSlider(Qt.Orientation.Horizontal)
        self._radius_slider.setRange(10, 1000)
        self._radius_slider.setSingleStep(5)
        self._radius_slider.setPageStep(50)
        self._radius_slider.setValue(250)
        self._radius_slider.setToolTip("Adjust the clip radius (0.10 – 10.00)")
        self._radius_slider.valueChanged.connect(self._on_radius_value_changed)
        self._radius_slider.sliderReleased.connect(self._emit_domain_changed)
        layout.addWidget(self._radius_slider)

        # Range labels
        range_row = QHBoxLayout()
        range_row.setContentsMargins(0, 0, 0, 0)
        # dark-mode-2026q2-e1 rect: QSS role property (was RANGE_LABEL_STYLE inline).
        _min_lbl = QLabel("0.10")
        _min_lbl.setProperty("role", "range-label")
        _max_lbl = QLabel("10.00")
        _max_lbl.setProperty("role", "range-label")
        _max_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        range_row.addWidget(_min_lbl)
        range_row.addStretch(1)
        range_row.addWidget(_max_lbl)
        layout.addLayout(range_row)

        # Show overlay
        self._domain_overlay_cb = QCheckBox("Show clip outline")
        self._domain_overlay_cb.setToolTip(
            "Overlay a wireframe sphere or cube to show the clip boundary"
        )
        self._domain_overlay_cb.setChecked(True)
        self._domain_overlay_cb.toggled.connect(lambda _: self._emit_domain_changed())
        layout.addWidget(self._domain_overlay_cb)

        self._update_domain_controls_enabled()
        return group

    def _make_scene_aids_group(self) -> QGroupBox:
        group = QGroupBox("Scene Aids")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self._axes_cb = QCheckBox("Show axes")
        self._axes_cb.setToolTip("Toggle the XYZ orientation widget in the corner of the viewport")
        self._axes_cb.setChecked(False)
        self._axes_cb.toggled.connect(self._on_axes_toggled)
        layout.addWidget(self._axes_cb)

        self._bbox_cb = QCheckBox("Show bounding box")
        self._bbox_cb.setToolTip("Overlay a wireframe bounding box around the current surface")
        self._bbox_cb.setChecked(False)
        self._bbox_cb.toggled.connect(self._on_bbox_toggled)
        layout.addWidget(self._bbox_cb)

        self._grid_cb = QCheckBox("Show grid")
        self._grid_cb.setToolTip("Show annotated axis grid lines around the surface")
        self._grid_cb.setChecked(False)
        self._grid_cb.toggled.connect(self._on_grid_toggled)
        layout.addWidget(self._grid_cb)

        return group

    def _make_screenshot_group(self) -> QGroupBox:
        group = QGroupBox("Export")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)

        # qtawesome-icons-2026q2-e1 (UPL-4): stored as instance attr so
        # refresh_icons(theme) can re-apply the icon on theme switch.
        self._shot_btn = QPushButton("Screenshot…")
        self._shot_btn.setToolTip("Save a PNG screenshot of the 3D viewport (Ctrl+Shift+S)")
        self._shot_btn.clicked.connect(self._on_screenshot)
        layout.addWidget(self._shot_btn)

        return group

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _make_view_callback(self, method_name: str):
        """Return a slot that calls self._plotter.<method_name>() and re-renders."""
        def _slot():
            getattr(self._plotter, method_name)()
            self._plotter.render()
        return _slot

    def _on_reset_camera(self) -> None:
        self._plotter.reset_camera()
        self._plotter.render()

    def _on_axes_toggled(self, checked: bool) -> None:
        if checked:
            self._plotter.show_axes()
        else:
            self._plotter.hide_axes()
        self._plotter.render()

    def _on_bbox_toggled(self, checked: bool) -> None:
        if checked:
            self._bbox_actor = self._plotter.add_bounding_box()
        else:
            self._remove_bbox()
        self._plotter.render()

    def _on_grid_toggled(self, checked: bool) -> None:
        if checked:
            self._grid_actor = self._plotter.show_grid()
        else:
            self._remove_grid()
        self._plotter.render()

    def _on_domain_mode_changed(self, _mode: str) -> None:
        self._update_domain_controls_enabled()
        self._emit_domain_changed()

    def _on_radius_value_changed(self, tick: int) -> None:
        # Live-update the readout while dragging; emit only on release.
        self._radius_value.setText(f"{tick / 100.0:.2f}")

    def _emit_domain_changed(self) -> None:
        self.domain_changed.emit()

    def _update_domain_controls_enabled(self) -> None:
        active = self._domain_mode.currentText() != self.DOMAIN_NONE
        self._radius_slider.setEnabled(active)
        self._radius_value.setEnabled(active)
        self._radius_label.setEnabled(active)
        self._domain_overlay_cb.setEnabled(active)
        # Update radius label to match shape (radius vs half-side)
        if self._domain_mode.currentText() == self.DOMAIN_CUBE:
            self._radius_label.setText("Half-side")
        else:
            self._radius_label.setText("Radius")

    def _on_screenshot(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            "screenshot.png",
            "PNG Images (*.png)",
        )
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            self._plotter.screenshot(path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _remove_bbox(self) -> None:
        """Remove the bounding box actor if present."""
        try:
            self._plotter.remove_bounding_box()
        except Exception as exc:
            logging.getLogger(__name__).warning("Could not remove bounding box: %s", exc)
        self._bbox_actor = None

    def _remove_grid(self) -> None:
        """Remove the grid actor if present."""
        try:
            self._plotter.remove_bounds_axes()
        except Exception as exc:
            logging.getLogger(__name__).warning("Could not remove bounds axes: %s", exc)
        self._grid_actor = None

    # ------------------------------------------------------------------
    # Public API — theme-aware icons (qtawesome-icons-2026q2-e1 / UPL-4)
    # ------------------------------------------------------------------

    def refresh_icons(self, theme: str = "dark") -> None:
        """Re-apply qtawesome icons with the active theme's color.

        Called by ``MainWindow.__init__`` (initial paint, after widget
        construction so ``QApplication`` is alive) and by
        ``MainWindow._on_theme_changed`` / ``_apply_system_theme`` (so
        icons re-render with the new color on theme swap).  Must NOT be
        called from ``_build_ui()`` — at that point ``QApplication`` is
        not yet fully active and ``qta.icon()`` silently returns an empty
        ``QIcon``.

        Sets an explicit 16x16 icon size on both buttons so the rendered
        size is platform-independent (Qt's PM_ButtonIconSize varies
        between Aqua-native 22px and Fusion-style 16px; a 16x16 fixed
        size keeps the View dock's vertical rhythm consistent with the
        26px-fixed-height preset grid — frontend-ux critic LOW-1).
        """
        # Lazy import — keeps `from view_panel import ViewPanel` cheap if
        # the caller never invokes refresh_icons (e.g. headless tests).
        import icons
        from PySide6.QtCore import QSize

        _ICON_SIZE = QSize(16, 16)

        # v0 (qtawesome-icons-2026q2-e1): Reset Camera + Screenshot
        self._reset_camera_btn.setIconSize(_ICON_SIZE)
        self._reset_camera_btn.setIcon(icons.reset_camera_icon(theme))
        self._shot_btn.setIconSize(_ICON_SIZE)
        self._shot_btn.setIcon(icons.screenshot_icon(theme))

        # v1 (qtawesome-icons-2026q2-e2): 6 ortho preset buttons +
        # isometric.  Map button label → factory function so the wiring
        # is data-driven and matches the preset definitions in
        # _make_view_presets_group.  Plain `setIcon` is synchronous (no
        # event drain) so AI-9 is undisturbed.  Both `_preset_btns` and
        # `_iso_btn` are populated unconditionally by `__init__` →
        # `_build_ui` → `_make_view_presets_group`; direct indexing is
        # correct (KeyError or AttributeError loudly signals a future
        # refactor that broke the constructor invariant, vs a silent
        # no-op that would hide the drift).  Axis-10 scope discipline
        # per CONTEXT.md §12: trust internal code.
        _PRESET_ICON_FACTORIES = {
            "+X": icons.preset_plus_x_icon,
            "-X": icons.preset_minus_x_icon,
            "+Y": icons.preset_plus_y_icon,
            "-Y": icons.preset_minus_y_icon,
            "+Z": icons.preset_plus_z_icon,
            "-Z": icons.preset_minus_z_icon,
        }
        for label, icon_fn in _PRESET_ICON_FACTORIES.items():
            btn = self._preset_btns[label]
            btn.setIconSize(_ICON_SIZE)
            btn.setIcon(icon_fn(theme))
        self._iso_btn.setIconSize(_ICON_SIZE)
        self._iso_btn.setIcon(icons.preset_isometric_icon(theme))

    # ------------------------------------------------------------------
    # Public API — domain clipping
    # ------------------------------------------------------------------

    def domain_settings(self) -> dict:
        return {
            "mode": self._domain_mode.currentText(),
            "radius": self._radius_slider.value() / 100.0,
            "show_overlay": self._domain_overlay_cb.isChecked(),
        }

    def clip_to_domain(self, mesh: pv.PolyData) -> tuple[pv.PolyData, pv.PolyData | None]:
        """Apply the user-chosen domain clip to *mesh*.

        Returns ``(clipped_mesh, overlay_mesh_or_None)``. The overlay is the
        wireframe sphere/cube to draw alongside the clipped surface, or
        ``None`` if the user disabled the overlay or selected mode ``Off``.
        """
        s = self.domain_settings()
        mode = s["mode"]
        if mode == self.DOMAIN_NONE or mesh.n_points == 0:
            return mesh, None

        r = s["radius"]
        # Both clips use the same scalar-clipping approach for reliable
        # behavior on PolyData surfaces: tag every vertex with a "domain
        # function" (radial distance for the sphere, Chebyshev / max-coord
        # distance for the cube), then keep only verts where that function
        # is <= the threshold.
        work = mesh.copy()
        if mode == self.DOMAIN_SPHERE:
            work.point_data["_domain_dist"] = np.linalg.norm(work.points, axis=1)
            overlay = (
                pv.Sphere(radius=r, center=(0.0, 0.0, 0.0),
                          theta_resolution=48, phi_resolution=24)
                if s["show_overlay"] else None
            )
        else:  # DOMAIN_CUBE
            work.point_data["_domain_dist"] = np.max(np.abs(work.points), axis=1)
            overlay = pv.Box(bounds=(-r, r, -r, r, -r, r)) if s["show_overlay"] else None

        clipped = work.clip_scalar(scalars="_domain_dist", value=r, invert=True)
        return clipped, overlay

    # ------------------------------------------------------------------
    # Public API — called by MainWindow after each surface switch
    # ------------------------------------------------------------------

    def re_apply_overlays(self) -> None:
        """Re-attach overlays after the mesh has been replaced.

        When the user picks a new surface, `_render_surface` clears and
        re-adds the main actor.  The bounding-box and grid actors are tied
        to the renderer bounds of the *previous* mesh, so they must be
        removed and re-added against the new mesh's bounds.

        Axes orientation widget and camera state are handled by the plotter
        itself and survive mesh switches without re-application.
        """
        # Bounding box
        if self._bbox_cb.isChecked():
            self._remove_bbox()
            self._bbox_actor = self._plotter.add_bounding_box()

        # Grid
        if self._grid_cb.isChecked():
            self._remove_grid()
            self._grid_actor = self._plotter.show_grid()

        # Axes orientation widget
        if self._axes_cb.isChecked():
            self._plotter.show_axes()
