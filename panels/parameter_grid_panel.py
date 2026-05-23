"""ParameterGridPanel — the grid-mode control surface for the Parameters dock.

A draggable dot on a 2D (or isometric-3D) grid adjusts two or three mapped
parameters at once. Parameters not placed on a grid axis are shown as ordinary
residual sliders below the grid.

Render discipline (INT-NO-1 / AI-9): while the dot is being dragged only the
numeric readouts update — no signal is emitted, no mesh is regenerated. On
mouse-release the panel emits ``grid_params_changed`` exactly once, which
``ParametersPanel`` relays into its existing ``params_changed`` signal — the
single, ``_computing``-guarded render path in ``app.py``.

All coordinate math lives in the Qt-free :mod:`parameter_grid` module; this
file is the thin Qt layer over it.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QGraphicsEllipseItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import parameter_grid as pg
from styles import (
    GRID_AXIS_LABEL,
    GRID_AXIS_LINE,
    GRID_BOX_WIRE,
    GRID_DOT_BORDER,
    GRID_DOT_FILL,
    GRID_LINE,
    SMALL_LABEL_STYLE,
)
from surfaces import ParamSpec
from ui_helpers import Debouncer, build_slider_row

# QColor wrappers around the palette tokens. QPen / QBrush want a QColor, not a
# bare hex string; building these once here keeps the call sites clean and the
# colors still single-sourced from PALETTE_LIGHT via styles.py.
_COL_GRID_LINE = QColor(GRID_LINE)
_COL_AXIS_LINE = QColor(GRID_AXIS_LINE)
_COL_BOX_WIRE = QColor(GRID_BOX_WIRE)
_COL_DOT_FILL = QColor(GRID_DOT_FILL)
_COL_DOT_BORDER = QColor(GRID_DOT_BORDER)
_COL_AXIS_LABEL = QColor(GRID_AXIS_LABEL)

# Scene geometry, in scene units (== pixels at default 1:1 view transform).
_GRID_SIZE = 240.0          # side length of the square 2D drawing area
_DOT_RADIUS = 8.0           # draggable dot radius
_MARGIN = 28.0              # padding inside the view around the grid area
_GRID_DIVISIONS = 8         # minor gridline count per axis
# Isometric 3D box: the Z axis is drawn as a foreshortened diagonal.
_ISO_DX = 0.46              # x-shift per unit of Z (fraction of _GRID_SIZE)
_ISO_DY = -0.30             # y-shift per unit of Z (fraction of _GRID_SIZE)


class _DraggableDot(QGraphicsEllipseItem):
    """The grid dot. Reports drag-begin / drag-move / drag-release to the panel.

    The item is movable so Qt handles the mouse capture, but the panel — not
    the item — owns the value math, so the item just forwards events.
    """

    def __init__(self, panel: "ParameterGridPanel") -> None:
        super().__init__(-_DOT_RADIUS, -_DOT_RADIUS, 2 * _DOT_RADIUS, 2 * _DOT_RADIUS)
        self._panel = panel
        self.setBrush(QBrush(_COL_DOT_FILL))
        self.setPen(QPen(_COL_DOT_BORDER, 2.0))
        self.setZValue(10)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, False)
        # ItemSendsGeometryChanges makes itemChange() fire on every setPos /
        # drag step so the dot can be constrained to the grid square below.
        self.setFlag(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True
        )
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Drag to adjust the mapped parameters")

    def itemChange(self, change, value):  # noqa: N802 (Qt override)
        """Constrain the dot to the grid square so it never visually escapes.

        Without this, a brisk drag toward a corner lets the dot leave the
        ``[0, _GRID_SIZE]`` drawing area (the parameter value still clamps
        correctly, but the dot would sit in the margin and look broken).
        """
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            x = min(_GRID_SIZE, max(0.0, value.x()))
            y = min(_GRID_SIZE, max(0.0, value.y()))
            return QPointF(x, y)
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self._panel._on_drag_begin()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        super().mouseMoveEvent(event)
        # super() has moved the item (and itemChange clamped it); report the
        # new position so the panel can live-update the readouts.
        # NO render here — INT-NO-1 (render fires only on release).
        self._panel._on_drag_move(self.pos())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
        self._panel._on_drag_release(self.pos())


class ParameterGridPanel(QWidget):
    """Grid control surface. Emits ``grid_params_changed`` on dot-release.

    The panel does not own a parameter-value dict; it is given the current
    values by :class:`ParametersPanel` (``set_specs`` / ``set_values``) and
    reports back changes. This keeps a single source of parameter truth.
    """

    # Emitted once on dot-release or residual-slider release, carrying the
    # full {name: value} dict. ParametersPanel relays it into params_changed.
    grid_params_changed = Signal(dict)
    # realtime-variety-render-e2-s2 (CAND-8): emitted on a DEBOUNCED drag tick
    # during a continuous dot-drag (or residual-slider drag), carrying the
    # live {name: value} dict.  ParametersPanel relays it into
    # `params_preview_changed`; `app.py` speed-routes it.  Distinct from
    # `grid_params_changed` so a drag-tick is never mistaken for a release.
    grid_params_preview_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._specs: list[ParamSpec] = []
        self._values: dict[str, float] = {}
        self._axis_count = 0
        # Per-axis chosen parameter name; index 0=X, 1=Y, 2=Z.
        self._axis_names: list[str] = []
        # Z drag-plane: which 2D plane the dot moves in for the 3D grid.
        self._drag_plane = "XY"

        self._dot: _DraggableDot | None = None
        self._dragging = False

        # realtime-variety-render-e1-s4 (CAND-6): shared QTimer debounce for
        # grid-dot drag-move ticks, mirroring ParametersPanel.  DORMANT in
        # e1 — `_on_drag_move` / `_on_residual_value_changed` register ticks
        # via `request()` so the coalescing machinery is wired, but the
        # deferred callback does not render.  Render-on-drag is e2/e4 work;
        # the dot-release / residual-release paths stay the single render
        # trigger (INT-NO-1) and call `_debouncer.cancel()` so a trailing
        # debounced callback can never shadow the release emit.
        self._debouncer = Debouncer(self._on_debounced_tick)

        self._axis_combos: list[QComboBox] = []
        self._residual_sliders: dict[str, QSlider] = {}
        self._residual_value_labels: dict[str, QLabel] = {}

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(6, 6, 6, 6)
        self._root.setSpacing(8)

        self._build_static_ui()

    # ------------------------------------------------------------------
    # UI scaffolding
    # ------------------------------------------------------------------

    def _build_static_ui(self) -> None:
        # Axis-count selector (2D vs 3D) — only meaningful when >= 3 params.
        self._axis_count_row = QWidget()
        acr = QHBoxLayout(self._axis_count_row)
        acr.setContentsMargins(0, 0, 0, 0)
        ac_lbl = QLabel("Grid")
        ac_lbl.setStyleSheet(SMALL_LABEL_STYLE)
        acr.addWidget(ac_lbl)
        self._axis_count_combo = QComboBox()
        self._axis_count_combo.addItem("2D (2 axes)", 2)
        self._axis_count_combo.addItem("3D (3 axes)", pg.MAX_GRID_AXES)
        self._axis_count_combo.setToolTip(
            "Number of parameters mapped to grid axes.\n"
            "Remaining parameters stay as sliders below."
        )
        self._axis_count_combo.currentIndexChanged.connect(self._on_axis_count_changed)
        acr.addWidget(self._axis_count_combo, stretch=1)
        self._root.addWidget(self._axis_count_row)

        # Per-axis parameter selectors (X / Y / Z). Built lazily in _rebuild.
        self._axis_selector_box = QWidget()
        self._axis_selector_layout = QVBoxLayout(self._axis_selector_box)
        self._axis_selector_layout.setContentsMargins(0, 0, 0, 0)
        self._axis_selector_layout.setSpacing(3)
        self._root.addWidget(self._axis_selector_box)

        # Drag-plane selector — only shown for the 3D grid.
        self._drag_plane_row = QWidget()
        dpr = QHBoxLayout(self._drag_plane_row)
        dpr.setContentsMargins(0, 0, 0, 0)
        dp_lbl = QLabel("Drag plane")
        dp_lbl.setStyleSheet(SMALL_LABEL_STYLE)
        dp_lbl.setToolTip(
            "A 2D mouse cannot drag a 3D point unambiguously.\n"
            "Pick which plane the dot moves in; the third axis is held fixed."
        )
        dpr.addWidget(dp_lbl)
        self._drag_plane_combo = QComboBox()
        self._drag_plane_combo.addItems(["XY", "XZ", "YZ"])
        self._drag_plane_combo.setToolTip(
            "XY — move X and Y, hold Z\n"
            "XZ — move X and Z, hold Y\n"
            "YZ — move Y and Z, hold X"
        )
        self._drag_plane_combo.currentTextChanged.connect(self._on_drag_plane_changed)
        dpr.addWidget(self._drag_plane_combo, stretch=1)
        self._root.addWidget(self._drag_plane_row)

        # The grid drawing surface.
        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene)
        # Antialias the gridlines and the dot edge — without this the dot
        # renders visibly jagged at typical screen densities.
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # Theme-aware background via QSS role cascade.
        # restructure-full-audit-2026q2-r1 batch 3 (AI-12 fix): replaced
        # setStyleSheet(f"background: {BG_GRID_SCENE}; border: none;") which
        # hardcoded the PALETTE_LIGHT value and kept the grid background
        # light in Dark theme.  The QSS rule QGraphicsView[role="grid-scene"]
        # in _render_stylesheet() handles both background and border: none
        # for light and dark palettes via palette["BG_GRID_SCENE"].
        self._view.setProperty("role", "grid-scene")
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setFixedHeight(int(_GRID_SIZE + 2 * _MARGIN))
        self._view.setToolTip("Parameter grid — drag the dot to adjust parameters")
        self._root.addWidget(self._view)

        # Live readout of every parameter value (grid axes + residuals).
        # QSS role property so the active theme drives the colour (matches
        # the dark-mode-aware convention used across the other panels).
        self._readout_label = QLabel("")
        self._readout_label.setProperty("role", "value-mono")
        self._readout_label.setWordWrap(True)
        self._root.addWidget(self._readout_label)

        # Residual-slider area for params not on a grid axis.
        self._residual_box = QWidget()
        self._residual_layout = QVBoxLayout(self._residual_box)
        self._residual_layout.setContentsMargins(0, 4, 0, 0)
        self._residual_layout.setSpacing(8)
        self._root.addWidget(self._residual_box)

        self._root.addStretch(1)

    # ------------------------------------------------------------------
    # Public API — driven by ParametersPanel
    # ------------------------------------------------------------------

    def set_specs(self, specs: list[ParamSpec], values: dict[str, float]) -> None:
        """Rebuild the grid for a new surface's parameter set + current values."""
        self._specs = list(specs)
        self._values = dict(values)
        self._axis_count = pg.default_axis_count(self._specs)
        if self._axis_count >= 2:
            self._axis_names = pg.default_axis_names(self._specs, self._axis_count)
        else:
            self._axis_names = []
        # Sync the axis-count combo without re-triggering the rebuild.
        # Skip entirely for 0/1-param surfaces: the combo only holds 2 and 3,
        # so findData(0/1) would return -1 and leave the combo's currentData
        # inconsistent with self._axis_count.  The combo is hidden anyway when
        # axis_count < 2 (see _rebuild), so there is nothing to sync.
        self._axis_count_combo.blockSignals(True)
        if self._axis_count >= 2:
            idx = self._axis_count_combo.findData(self._axis_count)
            self._axis_count_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._axis_count_combo.blockSignals(False)
        self._rebuild()

    def set_values(self, values: dict[str, float]) -> None:
        """Adopt externally-changed values (e.g. after a slider drag or reset).

        Repositions the dot and refreshes residual sliders without emitting.
        """
        self._values = dict(values)
        self._sync_dot_to_values()
        self._sync_residual_sliders()
        self._refresh_readout()

    def values(self) -> dict[str, float]:
        """Return the current {name: value} dict."""
        return dict(self._values)

    # ------------------------------------------------------------------
    # Rebuild — axis selectors, scene, residual sliders
    # ------------------------------------------------------------------

    def _rebuild(self) -> None:
        # Axis-count row only matters when there is a choice (>= 3 params).
        self._axis_count_row.setVisible(len(self._specs) >= pg.MAX_GRID_AXES)
        self._drag_plane_row.setVisible(self._axis_count == pg.MAX_GRID_AXES)

        self._rebuild_axis_selectors()
        self._rebuild_scene()
        self._rebuild_residual_sliders()
        self._refresh_readout()

    def _rebuild_axis_selectors(self) -> None:
        # Clear old selector rows.
        while self._axis_selector_layout.count():
            item = self._axis_selector_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._axis_combos = []

        if self._axis_count < 2:
            return

        axis_labels = ["X axis", "Y axis", "Z axis"]
        for ax in range(self._axis_count):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(axis_labels[ax])
            lbl.setStyleSheet(SMALL_LABEL_STYLE)
            lbl.setFixedWidth(48)
            rl.addWidget(lbl)
            combo = QComboBox()
            for spec in self._specs:
                combo.addItem(spec.label, spec.name)
            combo.setCurrentIndex(
                max(0, combo.findData(self._axis_names[ax]))
            )
            combo.setToolTip(f"Parameter mapped to the grid's {axis_labels[ax]}")
            combo.currentIndexChanged.connect(
                lambda _i, a=ax: self._on_axis_param_changed(a)
            )
            rl.addWidget(combo, stretch=1)
            self._axis_combos.append(combo)
            self._axis_selector_layout.addWidget(row)

    def _rebuild_scene(self) -> None:
        self._scene.clear()
        self._dot = None
        if self._axis_count < 2:
            return

        rect = QRectF(0.0, 0.0, _GRID_SIZE, _GRID_SIZE)
        self._scene.setSceneRect(
            -_MARGIN, -_MARGIN, _GRID_SIZE + 2 * _MARGIN, _GRID_SIZE + 2 * _MARGIN
        )

        minor_pen = QPen(_COL_GRID_LINE, 1.0)
        axis_pen = QPen(_COL_AXIS_LINE, 1.6)

        if self._axis_count == pg.MAX_GRID_AXES:
            self._draw_iso_box(axis_pen, minor_pen)
        else:
            self._draw_2d_grid(rect, axis_pen, minor_pen)

        self._draw_axis_labels()

        self._dot = _DraggableDot(self)
        self._scene.addItem(self._dot)
        self._sync_dot_to_values()

    def _draw_2d_grid(self, rect: QRectF, axis_pen: QPen, minor_pen: QPen) -> None:
        for i in range(_GRID_DIVISIONS + 1):
            t = i / _GRID_DIVISIONS
            x = t * _GRID_SIZE
            y = t * _GRID_SIZE
            self._scene.addLine(x, 0.0, x, _GRID_SIZE, minor_pen)
            self._scene.addLine(0.0, y, _GRID_SIZE, y, minor_pen)
        self._scene.addRect(rect, axis_pen)

    def _draw_iso_box(self, axis_pen: QPen, minor_pen: QPen) -> None:
        """Draw a fixed isometric wireframe box for the 3D grid.

        The box geometry is static — it does not rotate.  The front face
        always carries the gridlines; the Z axis is drawn as a foreshortened
        diagonal so the user perceives depth.  The "Drag plane" selector
        controls which *parameter pair* the dot drives (see ``_drag_plane``
        and ``_draw_axis_labels``), NOT which face is rendered.
        """
        box_pen = QPen(_COL_BOX_WIRE, 1.4)
        dz_x = _ISO_DX * _GRID_SIZE
        dz_y = _ISO_DY * _GRID_SIZE

        # Front face corners (z = near).
        f = [
            QPointF(0.0, _GRID_SIZE),
            QPointF(_GRID_SIZE, _GRID_SIZE),
            QPointF(_GRID_SIZE, 0.0),
            QPointF(0.0, 0.0),
        ]
        # Back face corners (z = far) = front shifted by the iso vector.
        b = [QPointF(p.x() + dz_x, p.y() + dz_y) for p in f]

        # Front face (drawn with the lighter minor pen as the drag-plane grid).
        for i in range(_GRID_DIVISIONS + 1):
            t = i / _GRID_DIVISIONS
            self._scene.addLine(
                t * _GRID_SIZE, 0.0, t * _GRID_SIZE, _GRID_SIZE, minor_pen
            )
            self._scene.addLine(
                0.0, t * _GRID_SIZE, _GRID_SIZE, t * _GRID_SIZE, minor_pen
            )
        # Box edges.
        for i in range(4):
            j = (i + 1) % 4
            self._scene.addLine(f[i].x(), f[i].y(), f[j].x(), f[j].y(), axis_pen)
            self._scene.addLine(b[i].x(), b[i].y(), b[j].x(), b[j].y(), box_pen)
            self._scene.addLine(f[i].x(), f[i].y(), b[i].x(), b[i].y(), box_pen)

    def _draw_axis_labels(self) -> None:
        """Label the horizontal / vertical / held axes for the current plane.

        For the 3D grid the drag plane decides which parameter the horizontal
        and vertical *screen* axes drive (and which parameter is held fixed),
        so the labels are computed from :func:`parameter_grid.plane_axes` /
        :func:`parameter_grid.held_axis` — NOT from a fixed (X, Y, Z) order.
        ``_on_drag_plane_changed`` re-runs the scene rebuild so these labels
        stay correct when the drag plane changes.
        """
        labels = self._axis_label_text()
        if self._axis_count < 2 or len(labels) < self._axis_count:
            return
        ax_h, ax_v = pg.plane_axes(self._drag_plane, self._axis_count)
        # Horizontal-axis label — bottom centre.
        h_lbl = QGraphicsSimpleTextItem(labels[ax_h])
        h_lbl.setBrush(QBrush(_COL_AXIS_LABEL))
        h_lbl.setPos(_GRID_SIZE / 2 - h_lbl.boundingRect().width() / 2,
                     _GRID_SIZE + 6.0)
        self._scene.addItem(h_lbl)
        # Vertical-axis label — left centre.
        v_lbl = QGraphicsSimpleTextItem(labels[ax_v])
        v_lbl.setBrush(QBrush(_COL_AXIS_LABEL))
        v_lbl.setPos(-_MARGIN + 2.0, _GRID_SIZE / 2)
        self._scene.addItem(v_lbl)
        # Held (depth) axis label — 3D grid only; the param the dot is NOT
        # currently driving, marked "(held)" so the user is not misled.
        held = pg.held_axis(self._drag_plane, self._axis_count)
        if held is not None and held < len(labels):
            d_lbl = QGraphicsSimpleTextItem(f"{labels[held]} (held)")
            d_lbl.setBrush(QBrush(_COL_AXIS_LABEL))
            d_lbl.setPos(_GRID_SIZE + _ISO_DX * _GRID_SIZE * 0.5,
                         _ISO_DY * _GRID_SIZE * 0.5 - 4.0)
            self._scene.addItem(d_lbl)

    def _axis_label_text(self) -> list[str]:
        """Human-readable label for each axis, in axis order (X, Y, [Z])."""
        by_name = {s.name: s for s in self._specs}
        return [by_name[n].label for n in self._axis_names if n in by_name]

    def _rebuild_residual_sliders(self) -> None:
        while self._residual_layout.count():
            item = self._residual_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._residual_sliders.clear()
        self._residual_value_labels.clear()

        if self._axis_count < 2:
            self._residual_box.hide()
            return

        assignment = pg.assign_axes(self._specs, self._axis_names)
        if not assignment.residual:
            self._residual_box.hide()
            return

        self._residual_box.show()
        hdr = QLabel("Other parameters")
        hdr.setProperty("role", "muted")
        self._residual_layout.addWidget(hdr)
        for spec in assignment.residual:
            self._residual_layout.addWidget(self._build_residual_row(spec))

    def _build_residual_row(self, spec: ParamSpec) -> QWidget:
        """Build a residual-parameter slider row via the shared factory.

        Residual params are those not placed on a grid axis — they keep an
        ordinary slider.  The row layout comes from
        :func:`ui_helpers.build_slider_row` so it is byte-identical to the
        main slider stack (no drift), and inherits the factory's degenerate
        ``step <= 0`` guard.  ``include_description=False`` keeps the row
        compact beside the grid.
        """
        cur = self._values.get(spec.name, spec.default)
        row, slider, value_lbl = build_slider_row(
            spec,
            cur,
            on_value_changed=self._on_residual_value_changed,
            on_released=self._on_residual_released,
            include_description=False,
        )
        self._residual_sliders[spec.name] = slider
        self._residual_value_labels[spec.name] = value_lbl
        return row

    # ------------------------------------------------------------------
    # Dot <-> value synchronization
    # ------------------------------------------------------------------

    def _spec_by_name(self, name: str) -> ParamSpec:
        """Return the :class:`ParamSpec` named *name*, or raise ``ValueError``.

        Raising a domain ``ValueError`` (rather than letting ``next()`` leak a
        bare ``StopIteration`` — which converts to a confusing ``RuntimeError``
        inside generator contexts) makes a stale-axis-name bug debuggable.
        """
        spec = next((s for s in self._specs if s.name == name), None)
        if spec is None:
            raise ValueError(f"no ParamSpec named {name!r}")
        return spec

    def _plane_axes(self) -> tuple[int, int]:
        """The (horizontal, vertical) axis indices the dot's 2D motion drives.

        Thin wrapper over :func:`parameter_grid.plane_axes`; the mapping logic
        itself is Qt-free and unit-tested in the pure module.
        """
        return pg.plane_axes(self._drag_plane, self._axis_count)

    def _sync_dot_to_values(self) -> None:
        """Position the dot from the current values of the active plane axes."""
        if self._dot is None or self._axis_count < 2:
            return
        ax_x, ax_y = self._plane_axes()
        spec_x = self._spec_by_name(self._axis_names[ax_x])
        spec_y = self._spec_by_name(self._axis_names[ax_y])
        val_x = self._values.get(spec_x.name, spec_x.default)
        val_y = self._values.get(spec_y.name, spec_y.default)
        sx = pg.value_to_scene(val_x, spec_x, _GRID_SIZE)
        sy = pg.value_to_scene(val_y, spec_y, _GRID_SIZE, invert=True)
        # setPos triggers _DraggableDot.itemChange (ItemSendsGeometryChanges
        # is set), which only clamps the position to the grid square — it
        # emits no panel signal, so repositioning the dot here never triggers
        # a render.
        self._dot.setPos(QPointF(sx, sy))

    def _values_from_dot(self, pos: QPointF) -> dict[str, float]:
        """Compute the new values for the active plane axes from a dot position.

        Returns a fresh value dict (other params unchanged). Coordinates past
        the grid edge clamp to the parameter min/max via the pure module.
        """
        ax_x, ax_y = self._plane_axes()
        spec_x = self._spec_by_name(self._axis_names[ax_x])
        spec_y = self._spec_by_name(self._axis_names[ax_y])
        new_x = pg.scene_to_value(pos.x(), spec_x, _GRID_SIZE)
        new_y = pg.scene_to_value(pos.y(), spec_y, _GRID_SIZE, invert=True)
        updated = dict(self._values)
        updated[spec_x.name] = new_x
        updated[spec_y.name] = new_y
        return updated

    # ------------------------------------------------------------------
    # Drag event handlers — called by _DraggableDot
    # ------------------------------------------------------------------

    def _on_drag_begin(self) -> None:
        self._dragging = True

    def _on_drag_move(self, pos: QPointF) -> None:
        # Live-update readouts ONLY — no signal, no render (INT-NO-1 / AI-9).
        self._values = self._values_from_dot(pos)
        self._refresh_readout()
        # CAND-6 (e1-s4): register the drag-move tick with the shared
        # debounce.  Dormant in e1 — `_on_debounced_tick` does not render.
        self._debouncer.request()

    def _on_debounced_tick(self) -> None:
        """Debounced drag-tick callback (CAND-6 e1-s4, activated e2-s2).

        Fires at most once per debounce interval (80 ms) during a continuous
        dot drag or residual-slider drag.  e2-s2 (CAND-8): it now emits
        `grid_params_preview_changed` with the live collected values.
        `ParametersPanel` relays it into `params_preview_changed`, which
        `app.py` speed-routes — Hanson surfaces render at every tick, slow
        surfaces ignore it.  The dot/residual release paths
        (`grid_params_changed`) are unchanged for all surfaces.

        `_collect_values()` is used (not bare `self._values`) so a debounced
        residual-slider drag also reflects the latest residual values.
        """
        self.grid_params_preview_changed.emit(self._collect_values())

    def _on_drag_release(self, pos: QPointF) -> None:
        self._dragging = False
        # CAND-6 (e1-s4): cancel any pending debounced drag callback so it
        # cannot fire after — and shadow — this release emit.
        self._debouncer.cancel()
        self._values = self._values_from_dot(pos)
        # Snap the dot to the (step-quantized) value so it lands on a grid
        # point consistent with the slider's discrete value set.
        self._sync_dot_to_values()
        self._refresh_readout()
        # Emit exactly once -> ParametersPanel -> params_changed -> one render.
        self.grid_params_changed.emit(dict(self._values))

    # ------------------------------------------------------------------
    # Residual-slider handlers — mirror ParametersPanel's discipline
    # ------------------------------------------------------------------

    def _on_residual_value_changed(self, spec: ParamSpec) -> None:
        # Live readout only — same two-phase discipline as the main sliders.
        tick = self._residual_sliders[spec.name].value()
        v = pg.tick_to_value(tick, spec)
        self._values[spec.name] = v
        self._residual_value_labels[spec.name].setText(pg.format_value(v, spec))
        self._refresh_readout()
        # CAND-6 (e1-s4) / e2-s2 (CAND-8): register the residual-slider drag
        # tick with the shared debounce so a Hanson surface with residual
        # sliders also updates continuously on a residual drag (the debounced
        # callback emits `grid_params_preview_changed`; app.py speed-routes).
        self._debouncer.request()

    def _on_residual_released(self) -> None:
        # CAND-6 (e1-s4): cancel any pending debounced drag preview so it
        # cannot fire after — and shadow — this release emit.  Mirrors
        # `_on_drag_release` and `ParametersPanel._on_slider_released`.
        self._debouncer.cancel()
        self._values = self._collect_values()
        self.grid_params_changed.emit(dict(self._values))

    def _sync_residual_sliders(self) -> None:
        for name, slider in self._residual_sliders.items():
            spec = self._spec_by_name(name)
            cur = self._values.get(name, spec.default)
            slider.blockSignals(True)
            slider.setValue(pg.value_to_tick(cur, spec))
            slider.blockSignals(False)
            self._residual_value_labels[name].setText(pg.format_value(cur, spec))

    def _collect_values(self) -> dict[str, float]:
        """Read the current value of every parameter from grid + residuals."""
        out = dict(self._values)
        for name, slider in self._residual_sliders.items():
            spec = self._spec_by_name(name)
            out[name] = pg.tick_to_value(slider.value(), spec)
        return out

    # ------------------------------------------------------------------
    # Selector handlers
    # ------------------------------------------------------------------

    def _on_axis_count_changed(self, _idx: int) -> None:
        new_count = self._axis_count_combo.currentData()
        if new_count == self._axis_count:
            return
        self._axis_count = int(new_count)
        # Re-derive a non-conflicting default axis mapping for the new count.
        self._axis_names = pg.default_axis_names(self._specs, self._axis_count)
        self._drag_plane_row.setVisible(self._axis_count == pg.MAX_GRID_AXES)
        self._rebuild_axis_selectors()
        self._rebuild_scene()
        self._rebuild_residual_sliders()
        self._refresh_readout()

    def _on_axis_param_changed(self, axis: int) -> None:
        """An axis combo changed. Prevent the same param on two axes."""
        chosen = self._axis_combos[axis].currentData()
        if chosen == self._axis_names[axis]:
            # No-op selection (combo opened and closed on the same item) —
            # skip the expensive scene + residual-slider teardown/rebuild.
            return
        # If another axis already holds `chosen`, swap the two so no axis is
        # left unassigned (mutual exclusivity without an error dialog).
        for other, name in enumerate(self._axis_names):
            if other != axis and name == chosen:
                displaced = self._axis_names[axis]
                self._axis_names[other] = displaced
                self._axis_combos[other].blockSignals(True)
                self._axis_combos[other].setCurrentIndex(
                    max(0, self._axis_combos[other].findData(displaced))
                )
                self._axis_combos[other].blockSignals(False)
                break
        self._axis_names[axis] = chosen
        # Geometry of the grid is unchanged; only labels + dot mapping move.
        self._rebuild_scene()
        self._rebuild_residual_sliders()
        self._refresh_readout()

    def _on_drag_plane_changed(self, plane: str) -> None:
        """Change which parameter pair the dot drives.

        The axis labels depend on the drag plane (which axes are horizontal /
        vertical / held), so the whole scene is rebuilt — redrawing the
        labels and repositioning the dot for the new plane.  Just moving the
        dot would leave the labels lying about which parameter each axis
        drives.
        """
        self._drag_plane = plane
        self._rebuild_scene()
        self._refresh_readout()

    # ------------------------------------------------------------------
    # Readout
    # ------------------------------------------------------------------

    def _refresh_readout(self) -> None:
        parts = []
        for spec in self._specs:
            v = self._values.get(spec.name, spec.default)
            parts.append(f"{spec.label}: {pg.format_value(v, spec)}")
        self._readout_label.setText("    ".join(parts))
