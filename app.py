"""Algebraic Variety Viewer — desktop GUI for plotting K3 surfaces.

PySide6 hosts a `pyvistaqt.QtInteractor` widget. The VTK render window inside
that widget provides native trackball-style rotate, zoom, and pan with the
mouse — no extra wiring required.
"""

from __future__ import annotations

import sys
import warnings

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from appearance_panel import AppearancePanel
from parameters_panel import ParametersPanel
from styles import APP_STYLESHEET
from surfaces import VARIETIES, VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS, Surface
from view_panel import ViewPanel

_PLACEHOLDER = "— Select —"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Algebraic Variety Viewer")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        variety_lbl = QLabel("Variety:")
        controls.addWidget(variety_lbl)
        self.variety_combo = QComboBox()
        self.variety_combo.setMinimumWidth(180)
        self.variety_combo.addItem(_PLACEHOLDER)
        self.variety_combo.addItems(VARIETIES.keys())
        self.variety_combo.setToolTip(
            "Choose a family of algebraic surfaces.\n\n"
            + "\n\n".join(
                f"{name}:\n{tip}" for name, tip in VARIETY_TOOLTIPS.items()
            )
        )
        self.variety_combo.currentTextChanged.connect(self._on_variety_changed)
        controls.addWidget(self.variety_combo)

        self.subtype_label = QLabel("Model:")
        controls.addWidget(self.subtype_label)
        self.subtype_combo = QComboBox()
        self.subtype_combo.setMinimumWidth(220)
        self.subtype_combo.addItem(_PLACEHOLDER)
        self.subtype_combo.setToolTip("Choose a specific surface model within the selected family.")
        self.subtype_combo.currentTextChanged.connect(self._on_subtype_changed)
        controls.addWidget(self.subtype_combo)

        controls.addStretch(1)
        root.addLayout(controls)

        self.plotter = QtInteractor(central)
        self.plotter.setToolTip(
            "3D viewport\n"
            "Left-drag: rotate  |  Scroll / Right-drag: zoom  |  Shift-drag: pan"
        )
        root.addWidget(self.plotter.interactor, stretch=1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Choose a variety to begin.")

        self._actor = None
        self._domain_overlay_actor = None
        self._raw_mesh = None
        self._computing = False
        self._current_surface: Surface | None = None
        self._set_subtype_enabled(False)

        # --- View dock (left) ------------------------------------------------
        self.view_panel = ViewPanel(self.plotter)
        self.view_panel.domain_changed.connect(self._on_domain_changed)
        view_dock = QDockWidget("View", self)
        view_dock.setObjectName("ViewDock")
        view_dock.setWidget(self.view_panel)
        view_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        view_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, view_dock)

        # --- Appearance dock (right) -----------------------------------------
        self.appearance_panel = AppearancePanel(
            get_actor=lambda: self._actor,
            get_plotter=lambda: self.plotter,
        )
        appearance_dock = QDockWidget("Appearance", self)
        appearance_dock.setObjectName("AppearanceDock")
        appearance_dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        appearance_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        appearance_dock.setWidget(self.appearance_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, appearance_dock)

        # --- Parameters dock (right, above Appearance) -----------------------
        self.parameters_panel = ParametersPanel()
        self.parameters_panel.params_changed.connect(self._on_params_changed)
        params_dock = QDockWidget("Parameters", self)
        params_dock.setObjectName("ParametersDock")
        params_dock.setWidget(self.parameters_panel)
        params_dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        params_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, params_dock)
        # Stack Parameters above Appearance on the right.
        self.splitDockWidget(params_dock, appearance_dock, Qt.Orientation.Vertical)

        # Apply the launch background color BEFORE any surface renders, so
        # the user never sees the VTK default light-grey background flash on
        # the first frame.  Decoupled from apply_to_actor(None) which used to
        # silently no-op the background-init step.  See UPL-3 in
        # plans/panel-refresh-2026q2-roadmap.md.
        self.appearance_panel.apply_background()

        # --- Keyboard shortcuts ----------------------------------------------
        self._setup_shortcuts()

    # --- keyboard shortcuts ------------------------------------------------

    def _setup_shortcuts(self) -> None:
        # Ctrl+R — Reset Camera
        sc_reset = QShortcut(QKeySequence("Ctrl+R"), self)
        sc_reset.activated.connect(self.view_panel._on_reset_camera)

        # Ctrl+Shift+S — Screenshot
        sc_shot = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        sc_shot.activated.connect(self.view_panel._on_screenshot)

        # Ctrl+D — Reset Parameters to defaults
        sc_params = QShortcut(QKeySequence("Ctrl+D"), self)
        sc_params.activated.connect(self.parameters_panel._reset_defaults)

    # --- dropdown handlers -------------------------------------------------

    def _set_subtype_enabled(self, enabled: bool) -> None:
        self.subtype_combo.setEnabled(enabled)
        self.subtype_label.setEnabled(enabled)

    def _on_variety_changed(self, name: str) -> None:
        self.subtype_combo.blockSignals(True)
        self.subtype_combo.clear()
        self.subtype_combo.addItem(_PLACEHOLDER)
        if name in VARIETIES:
            subtypes = list(VARIETIES[name].keys())
            self.subtype_combo.addItems(subtypes)
            # Attach per-subtype tooltips
            for i, subtype in enumerate(subtypes, start=1):
                tip = SUBTYPE_TOOLTIPS.get(subtype, "")
                if tip:
                    self.subtype_combo.setItemData(i, tip, Qt.ItemDataRole.ToolTipRole)
            self._set_subtype_enabled(True)
            # For CY3 and Fano, include a brief contextual note in the status
            # bar AND in the Parameters dock banner so first-time users
            # understand they are viewing 2D shadows/slices, not the full
            # 6-dimensional manifold.
            if name == "Calabi–Yau 3-fold":
                self.statusBar().showMessage(
                    "Calabi–Yau 3-fold — each figure is a 2D real shadow of a "
                    "6-dimensional manifold.  Now choose a model."
                )
                self.parameters_panel.set_context_hint(
                    "A Calabi–Yau 3-fold is 6-real-dimensional and cannot live in ℝ³. "
                    "The figures here are 2D shadows in the Hanson-1994 tradition "
                    "(parametric cross-sections) and one implicit Dwork-pencil slice."
                )
            elif name == "Fano 3-fold (ρ=1)":
                self.statusBar().showMessage(
                    "Fano 3-fold (ρ=1) — each figure is a 2D real slice of a "
                    "6-dimensional variety.  Now choose a model."
                )
                self.parameters_panel.set_context_hint(
                    "Smooth Fano 3-folds of Picard rank 1 are 6-real-dimensional. "
                    "Each figure is a real 2D slice obtained by fixing one or two "
                    "projective coordinates. There is no established visualization "
                    "tradition — these are novel renderings."
                )
            else:
                self.statusBar().showMessage(f"Variety: {name}. Now choose a model.")
                self.parameters_panel.set_context_hint("")
        else:
            self._set_subtype_enabled(False)
            self._clear_actor()
            self.statusBar().showMessage("Choose a variety to begin.")
            self.parameters_panel.set_context_hint("")
        self.subtype_combo.blockSignals(False)

    def _on_subtype_changed(self, name: str) -> None:
        variety = self.variety_combo.currentText()
        if variety not in VARIETIES or name not in VARIETIES[variety]:
            self._current_surface = None
            self.parameters_panel.set_specs([])
            # Update subtype combo tooltip to the currently hovered item's tip
            self.subtype_combo.setToolTip(
                SUBTYPE_TOOLTIPS.get(name,
                    "Choose a specific surface model within the selected family.")
            )
            return
        surface = VARIETIES[variety][name]
        self._current_surface = surface
        # Update subtype combo tooltip with the selected model's description
        self.subtype_combo.setToolTip(
            SUBTYPE_TOOLTIPS.get(name,
                "Choose a specific surface model within the selected family.")
        )
        # Repopulate the parameters panel for the new surface.
        self.parameters_panel.set_specs(surface.params)
        self._render_current(reset_camera=True)

    def _on_params_changed(self, _values: dict) -> None:
        # Triggered when a slider is released (or Reset clicked).
        # Don't reset the camera so the user keeps their viewpoint as they
        # tune parameters.
        self._render_current(reset_camera=False)

    def _on_domain_changed(self) -> None:
        # Domain shape/radius/overlay-toggle changed — re-clip the cached raw
        # mesh without regenerating it. Camera preserved.
        if self._raw_mesh is None:
            return
        self._apply_domain_and_render(reset_camera=False)

    # --- rendering ---------------------------------------------------------

    def _clear_actor(self) -> None:
        if self._actor is not None:
            self.plotter.remove_actor(self._actor)
            self._actor = None

    def _clear_domain_overlay(self) -> None:
        if self._domain_overlay_actor is not None:
            self.plotter.remove_actor(self._domain_overlay_actor)
            self._domain_overlay_actor = None

    def _render_current(self, *, reset_camera: bool) -> None:
        if self._current_surface is None:
            return
        # Re-entrancy guard: QApplication.processEvents() below can cause a
        # second call via slider release → _on_params_changed → _render_current.
        if self._computing:
            return
        self._computing = True
        # Show busy cursor while the marching-cubes pipeline runs
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            surface = self._current_surface
            params = self.parameters_panel.values() if surface.params else {}

            self.statusBar().showMessage(f"Computing {surface.label}…")
            QApplication.processEvents()
            _surface_warning: str = ""
            try:
                # Capture RuntimeWarning (e.g. the Dwork conifold warning at
                # ψ≈1) so it appears in the status bar rather than vanishing
                # into stderr.
                with warnings.catch_warnings(record=True) as _caught:
                    warnings.simplefilter("always")
                    self._raw_mesh = surface.generate(**params)
                for _w in _caught:
                    if issubclass(_w.category, RuntimeWarning):
                        _surface_warning = str(_w.message)
                        break
            except ValueError as exc:
                self._raw_mesh = None  # don't let a stale mesh be domain-clipped
                msg = str(exc)
                # "No real zero set" means the parameter *combination* produces
                # an empty field — not that any single slider is out of range.
                # Give a more actionable prefix so the user knows what to do.
                if "No real zero set" in msg:
                    self.statusBar().showMessage(
                        f"No surface to render — {msg}"
                    )
                else:
                    self.statusBar().showMessage(f"Parameter out of range — {msg}")
                return
            except Exception as exc:
                self._raw_mesh = None
                self.statusBar().showMessage(f"Error: {exc}")
                return

            self._apply_domain_and_render(reset_camera=reset_camera)

            params = self.parameters_panel.values() if surface.params else {}
            param_str = (
                "  ·  " + ", ".join(
                    # Format each param with a precision that matches the slider
                    # display (step-derived) rather than :g (which gives more
                    # digits than the slider label, creating an inconsistency).
                    f"{k}={self._format_param(v, surface, k)}"
                    for k, v in params.items()
                )
                if params else ""
            )
            base_msg = (
                f"{surface.label}  ·  {self._raw_mesh.n_points:,} verts, "
                f"{self._raw_mesh.n_cells:,} faces{param_str}"
            )
            if _surface_warning:
                # Prepend a ⚠ marker so the warning stands out from the mesh stats.
                self.statusBar().showMessage(f"⚠ {_surface_warning}  |  {base_msg}")
            else:
                self.statusBar().showMessage(base_msg)
        finally:
            QApplication.restoreOverrideCursor()
            self._computing = False

    def _apply_domain_and_render(self, *, reset_camera: bool) -> None:
        """Clip the cached raw mesh per the View panel's domain settings,
        re-add the surface and (optional) domain-outline actors, and render.
        Called whenever either the mesh OR the domain settings change."""
        if self._raw_mesh is None:
            return

        clipped, overlay = self.view_panel.clip_to_domain(self._raw_mesh)

        self._clear_actor()
        self._clear_domain_overlay()

        if clipped.n_points == 0:
            # Domain is set smaller than the surface — show the outline only.
            self.statusBar().showMessage(
                "Clip region is smaller than the surface — reduce the radius "
                "or change the clip shape to see geometry."
            )
            if overlay is not None:
                self._domain_overlay_actor = self.plotter.add_mesh(
                    overlay,
                    style="wireframe",
                    color="#888888",
                    opacity=0.35,
                    line_width=1,
                    pickable=False,
                    lighting=False,
                )
            self.view_panel.re_apply_overlays()
            self.plotter.render()
            return

        self._actor = self.plotter.add_mesh(
            clipped,
            smooth_shading=True,
            specular=0.3,
            specular_power=15,
        )
        self.appearance_panel.apply_to_actor(self._actor)

        if overlay is not None:
            self._domain_overlay_actor = self.plotter.add_mesh(
                overlay,
                style="wireframe",
                color="#888888",
                opacity=0.35,
                line_width=1,
                pickable=False,
                lighting=False,
            )

        if reset_camera:
            self.plotter.reset_camera()
        self.view_panel.re_apply_overlays()
        self.plotter.render()

    # --- helpers -----------------------------------------------------------

    @staticmethod
    def _format_param(value: float, surface: Surface, key: str) -> str:
        """Format a parameter value using the same precision as the slider label.

        ParametersPanel._format_value uses step-derived precision:
          step >= 1   → 0 decimal places
          step >= 0.1 → 2 decimal places
          else        → 3 decimal places

        Using :g in the status bar would show ``alpha=0.785398`` while the
        slider label shows ``0.785`` — inconsistent. This matches them.
        """
        spec = next((p for p in surface.params if p.name == key), None)
        if spec is None:
            return f"{value:g}"
        if spec.step >= 1:
            return f"{value:.0f}"
        if spec.step >= 0.1:
            return f"{value:.2f}"
        return f"{value:.3f}"

    # --- lifecycle ---------------------------------------------------------

    def closeEvent(self, event):
        self.plotter.close()
        super().closeEvent(event)


def main() -> int:
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
