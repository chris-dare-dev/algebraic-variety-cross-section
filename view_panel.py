"""ViewPanel — left-side camera / scene-aid control panel.

Exported symbol: ViewPanel(QWidget)

Construction::

    panel = ViewPanel(plotter)   # plotter is a pyvistaqt.QtInteractor

After each surface switch, call::

    panel.re_apply_overlays()

to re-attach bounding-box and grid actors to the newly generated mesh.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class ViewPanel(QWidget):
    """Left-side panel providing view presets and scene-aid toggles."""

    def __init__(self, plotter) -> None:
        super().__init__()
        self._plotter = plotter

        # Overlay state
        self._bbox_actor = None   # vtkActor returned by add_bounding_box()
        self._grid_actor = None   # CubeAxesActor returned by show_grid()

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
        root.addWidget(self._make_scene_aids_group())
        root.addWidget(self._make_screenshot_group())

        # Help line at the bottom
        help_label = QLabel(
            "Left-drag to rotate\n"
            "Scroll or Right-drag to zoom\n"
            "Shift-drag to pan"
        )
        help_label.setWordWrap(True)
        help_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        help_label.setStyleSheet("color: #888888; font-size: 10px;")
        root.addWidget(help_label)

        root.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

    def _make_view_presets_group(self) -> QGroupBox:
        group = QGroupBox("View Presets")
        grid = QGridLayout(group)
        grid.setSpacing(4)

        # (label, row, col, plotter method name)
        presets = [
            ("+X", 0, 0, "view_yz"),   # looking down +X axis shows YZ plane
            ("-X", 0, 1, "view_zy"),   # opposite
            ("+Y", 1, 0, "view_xz"),   # looking down +Y axis shows XZ plane
            ("-Y", 1, 1, "view_zx"),   # opposite
            ("+Z", 2, 0, "view_xy"),   # looking down +Z axis shows XY plane
            ("-Z", 2, 1, "view_yx"),   # opposite
        ]

        for label, row, col, method in presets:
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.clicked.connect(self._make_view_callback(method))
            grid.addWidget(btn, row, col)

        iso_btn = QPushButton("Isometric")
        iso_btn.setFixedHeight(26)
        iso_btn.clicked.connect(lambda: self._plotter.view_isometric())
        grid.addWidget(iso_btn, 3, 0, 1, 2)

        return group

    def _make_camera_group(self) -> QGroupBox:
        group = QGroupBox("Camera")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)

        reset_btn = QPushButton("Reset Camera")
        reset_btn.clicked.connect(lambda: self._plotter.reset_camera())
        layout.addWidget(reset_btn)

        return group

    def _make_scene_aids_group(self) -> QGroupBox:
        group = QGroupBox("Scene Aids")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self._axes_cb = QCheckBox("Show axes")
        self._axes_cb.setChecked(False)
        self._axes_cb.toggled.connect(self._on_axes_toggled)
        layout.addWidget(self._axes_cb)

        self._bbox_cb = QCheckBox("Show bounding box")
        self._bbox_cb.setChecked(False)
        self._bbox_cb.toggled.connect(self._on_bbox_toggled)
        layout.addWidget(self._bbox_cb)

        self._grid_cb = QCheckBox("Show grid")
        self._grid_cb.setChecked(False)
        self._grid_cb.toggled.connect(self._on_grid_toggled)
        layout.addWidget(self._grid_cb)

        return group

    def _make_screenshot_group(self) -> QGroupBox:
        group = QGroupBox("Export")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)

        shot_btn = QPushButton("Screenshot…")
        shot_btn.clicked.connect(self._on_screenshot)
        layout.addWidget(shot_btn)

        return group

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _make_view_callback(self, method_name: str):
        """Return a slot that calls self._plotter.<method_name>()."""
        def _slot():
            getattr(self._plotter, method_name)()
        return _slot

    def _on_axes_toggled(self, checked: bool) -> None:
        if checked:
            self._plotter.show_axes()
        else:
            self._plotter.hide_axes()

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
        except Exception:
            pass
        self._bbox_actor = None

    def _remove_grid(self) -> None:
        """Remove the grid actor if present."""
        try:
            self._plotter.remove_bounds_axes()
        except Exception:
            pass
        self._grid_actor = None

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
