"""Algebraic Variety Viewer — desktop GUI for plotting K3 surfaces.

PySide6 hosts a `pyvistaqt.QtInteractor` widget. The VTK render window inside
that widget provides native trackball-style rotate, zoom, and pan with the
mouse — no extra wiring required.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QThreadPool, QTimer, Slot
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QGuiApplication,
    QKeySequence,
    QShortcut,
)
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
from render_worker import MeshResult, MeshWorker, is_stale_result
from styles import (
    APP_STYLESHEET,
    APP_STYLESHEET_DARK,
    BG_SURFACE_DEFAULT,
    COLOR_WIREFRAME_OVERLAY,
    get_variety_default_colors,
)
from surfaces import (
    VARIETIES,
    VARIETY_TOOLTIPS,
    SUBTYPE_TOOLTIPS,
    Surface,
    should_render_on_drag,
)
from view_panel import ViewPanel

_PLACEHOLDER = "— Select —"


def clipped_cache_is_valid(
    cached_clip: object,
    raw_mesh_changed: bool,
    domain_changed: bool,
) -> bool:
    """Pure predicate for the CAND-11 clipped-mesh cache (e1-s5).

    Returns ``True`` when a previously cached clipped mesh may be reused for
    the current render — i.e. there *is* a cached clip and neither the raw
    mesh nor the domain settings have changed since it was computed.

    This is extracted as a free function (no ``QApplication``, no VTK) so the
    cache-invalidation logic is unit-testable under the Qt-free AI-2 suite.
    ``MainWindow`` realises the same logic imperatively: it sets
    ``self._clipped_mesh = None`` (``_invalidate_clipped_mesh``) on a
    raw-mesh change or a domain change, and otherwise reuses the slot — which
    is exactly ``cached_clip is not None and not raw_mesh_changed and not
    domain_changed``.

    AI-10: a domain-radius change sets ``domain_changed=True`` (cache miss,
    re-clip) but never implies a raw-mesh regeneration — the raw mesh is
    independent of this predicate.
    """
    return (
        cached_clip is not None
        and not raw_mesh_changed
        and not domain_changed
    )


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
        # realtime-variety-render-e1-s5 (CAND-11): clipped-mesh cache slot.
        # Holds the result of `view_panel.clip_to_domain(self._raw_mesh)` so an
        # appearance-only re-render (e.g. surface colour change) reuses it
        # instead of re-running the full `mesh.copy()` + scalar-tag + clip.
        # Invalidated (set back to None) ONLY when `_raw_mesh` changes OR the
        # domain settings change — see `_invalidate_clipped_mesh`.  AI-10:
        # this cache never causes a raw-mesh regeneration; a domain-radius
        # slider change still reuses the cached `_raw_mesh`.
        self._clipped_mesh = None
        self._clipped_overlay = None
        # realtime-variety-render-e4 (CAND-4): `surface.generate()` now runs on
        # a `QThreadPool` worker (see render_worker.py).  `_computing` is no
        # longer a synchronous in-method flag — it is the "worker in flight"
        # state and spans event-loop iterations from `_render_current`
        # (dispatch) to `_on_mesh_ready` (result slot).
        self._computing = False
        # realtime-variety-render-e1-s2 (CAND-5): queue-latest re-entrancy
        # semantics.  When a render is requested while one is in flight,
        # `_pending_render` is set True instead of the request being dropped;
        # the result slot `_on_mesh_ready` schedules one catch-up render via
        # `QTimer.singleShot(0, ...)`.  This fixes the CRITICAL correctness bug
        # where a fast drag-and-release silently discarded the slider's final
        # resting position.  e4: the catch-up scheduling moved from the old
        # synchronous `finally` block into the worker-result slot, because
        # "in flight" now ends when the worker signal arrives, not when the
        # dispatch function returns.
        self._pending_render = False
        # realtime-variety-render-e4 (CAND-4): monotonic job-generation id.
        # Every worker dispatch increments it; `_on_mesh_ready` discards any
        # result whose generation id is not current (`is_stale_result`).  With
        # the `_computing` single-flight guard at most one worker is in flight,
        # so this is defensive idempotency insurance — see render_worker.py.
        self._generation = 0
        # The worker currently in flight.  MainWindow holds this Python ref for
        # the worker's whole flight so the worker (and its `self._result` mesh
        # ref — VTK #18782) cannot be GC'd before the result slot has retained
        # the mesh.  Cleared in `_on_mesh_ready`, never at dispatch.
        self._active_worker = None
        # A dedicated QThreadPool for mesh workers — NOT the process-global
        # `QThreadPool.globalInstance()`.  Isolates `closeEvent`'s drain to
        # *this app's* render workers and keeps the worker accounting local.
        self._render_pool = QThreadPool()
        # The surface / params / reset_camera captured at dispatch time.  The
        # result slot uses THESE, not `_current_surface` / a fresh
        # `parameters_panel.values()` — the user may have changed the selection
        # or dragged a slider further while the worker was in flight, and the
        # slot must describe the surface that was actually generated.
        self._inflight_surface: Surface | None = None
        self._inflight_params: dict = {}
        self._inflight_reset_camera = False
        # The reset_camera flag the catch-up render should use.  A catch-up
        # is always a parameter re-tune (reset_camera=False); recorded here
        # so the catch-up does not have to guess.
        self._pending_reset_camera = False
        self._current_surface: Surface | None = None
        self._set_subtype_enabled(False)

        # dark-mode-2026q2-e1 (UPL-1): theme state + Theme menu.  The active
        # theme controls which palette `get_variety_default_colors()` returns
        # (consumed by `_on_variety_changed`/`_on_subtype_changed`) and which
        # stylesheet `QApplication.setStyleSheet` applies.  Launch default is
        # `dark` because the VTK viewport is always `#2f2f2f` — dark chrome
        # is the coherent baseline, not the optional variant.
        self._active_theme: str = "dark"
        self._build_theme_menu()

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
        # realtime-variety-render-e2-s2 (CAND-8): the debounced drag-tick
        # signal.  Distinct from `params_changed` (release) so the handler
        # can speed-route — fast (Hanson) surfaces render continuously during
        # a drag, slow surfaces ignore the preview and stay release-only.
        self.parameters_panel.params_preview_changed.connect(
            self._on_params_preview_changed
        )
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

        # qtawesome-icons-2026q2-e1 (UPL-4): apply icons AFTER widget
        # construction completes — qta.icon() requires a live QApplication
        # and panel _build_ui() methods run before MainWindow.__init__ is
        # ready.  Both panels expose a `refresh_icons(theme)` method that
        # MainWindow re-invokes from _on_theme_changed / _apply_system_theme
        # whenever the active theme swaps.  The lazy import of `qtawesome`
        # inside `icons.py` ensures the ~150-200ms font-load cost fires here
        # (during window setup, not module import).
        self.view_panel.refresh_icons(self._active_theme)
        self.parameters_panel.refresh_icons(self._active_theme)

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
            # UPL-2 (variety-palette-2026q2-e1): seed the surface color from
            # the family default so each variety has a visually distinct
            # identity cue.  UPL-1 (dark-mode-2026q2-e1): route through
            # `get_variety_default_colors(active_theme)` so the swatch
            # reflects the active theme's tuned color (light + dark dicts
            # currently share values, but the accessor is the right
            # abstraction for any future divergence).  Falls back to
            # BG_SURFACE_DEFAULT if the key is missing — the
            # test_variety_default_color_keys_match_surfaces_varieties guard
            # in tests/test_styles_palette.py prevents drift.  User's
            # subsequent override via the "Surface…" swatch still wins; this
            # only sets the starting point on switch.
            self.appearance_panel.set_default_color(
                get_variety_default_colors(self._active_theme).get(
                    name, BG_SURFACE_DEFAULT
                )
            )
            # UPL-7 (enriques-backface-2026q2-e1): apply back-face culling
            # ONLY for the Enriques family.  The Enriques canonical sextic
            # and its siblings have double-curve singularities where two
            # sheets approach zero separation; marching cubes produces
            # alternating front/back triangles at those ridges, and Phong
            # lighting renders them as white zipper noise.  Culling clears
            # this for the math-honest singular-locus rendering.  Other
            # families get None to clear any stale Enriques setting:
            #   - K3 / Kummer: 16 point-conical nodes have inner cone
            #     faces visible through hollows; culling hides them.
            #   - CY3 / Hanson quintic: AI-7's consistent_normals=False
            #     patches have non-globally-oriented normals; culling
            #     would hide whole patches as the camera rotates.
            #   - K3 / Fermat is closed and unaffected either way; we still
            #     clear culling for consistency.
            # Variety-level gate (not per-subtype) — culling is harmless on
            # all 4 Enriques figures and beneficial on 3 of 4.  Specifically:
            # Figs. 1+2 have double-curve singularities (culling kills the
            # zipper); Fig. 3 (Cayley quartic symmetroid) has ordinary A₁
            # nodes — culling is a verified no-op; Fig. 4 (icosahedral sextic)
            # has A₁ nodes but the marching-cubes resolution surfaces some
            # alternating triangles so culling still helps empirically.  See
            # CONTEXT.md §8.13 for the per-figure topology audit and the
            # forward-maintenance rule for adding new Enriques figures.
            self.appearance_panel.set_culling(
                "back" if name == "Enriques surface" else None
            )
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
            elif name == "Enriques surface":
                # UPL-7 (enriques-backface-2026q2-e1) rect MEDIUM-1: signal
                # that back-face culling is active so an expert user inspecting
                # the canonical sextic's double-curve singularity knows WHY
                # the seam reads clean (vs the pre-fix white zipper noise).
                # Mirrors the CY3 / Fano pattern of variety-specific context.
                self.statusBar().showMessage(
                    "Enriques surface — back-face culling active to suppress "
                    "the double-curve zipper seam.  Now choose a model."
                )
                self.parameters_panel.set_context_hint("")
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
        # UPL-2 (variety-palette-2026q2-e1): re-seed family default on every
        # subtype switch.  This implements the V0 "re-seed on switch-back"
        # semantic: if a user is on K3 (custom red override), switches to
        # Enriques, then back to K3, the K3 family default re-applies — we
        # don't carry the per-user override across surface switches in V0
        # (UPL-25 dock state persistence is the future home for sticky
        # overrides).  Symmetric with the wire in _on_variety_changed so
        # the swatch updates whether the user changes only Variety or also
        # picks a Subtype.  UPL-1 (dark-mode-2026q2-e1): theme-aware via
        # `get_variety_default_colors(active_theme)`.
        self.appearance_panel.set_default_color(
            get_variety_default_colors(self._active_theme).get(
                variety, BG_SURFACE_DEFAULT
            )
        )
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
        # tune parameters.  This release path is unchanged for ALL surfaces,
        # fast and slow — it is the full-render trigger for everything.
        self._render_current(reset_camera=False)

    def _on_params_preview_changed(self, _values: dict) -> None:
        """Debounced drag-tick handler — the continuous-drag fast-path.

        realtime-variety-render-e2-s2 (CAND-8).  Triggered (at most once per
        80 ms debounce window) while a slider or grid-dot is *still being
        dragged*.  The speed-routing decision lives HERE — not in the panels —
        because `self._current_surface` (and therefore its `typical_ms`) is
        only known to `MainWindow`.

        `should_render_on_drag` is a pure predicate: it returns True only for
        a surface with a measured `0 < typical_ms <= 80` (the 3 Hanson
        parametric figures).  Fast surfaces get a real render on every drag
        tick; slow (implicit, `typical_ms == 0`) surfaces ignore the preview
        entirely and stay release-only, exactly as before this epic.

        The render flows through the normal `_render_current` path, so it is
        covered by the e1 `_computing` + `_pending_render` queue-latest guard.
        AI-9: a drag-tick fires at most once per 80 ms; a Hanson generate
        round-trip is ~11-39 ms.  If a tick lands while a render is in flight
        (`_computing` True) it sets `_pending_render` and the `finally` block
        schedules one `QTimer.singleShot(0, ...)` catch-up that re-reads the
        LATEST values — so a fast burst coalesces to "render, then one
        catch-up", never an unbounded re-entrant stack.

        AI-6: a Hanson surface is parametric (`_grid_to_polydata` /
        `_concat_polydata`) — it already skips marching cubes and Taubin.
        The fast-path here only changes *when* `surface.generate()` is
        called, never *how*.  When e4 adds CAND-3's coarse-LOD path, that
        path's drag-tick branch MUST guard on `should_render_on_drag(surface)`
        / `surface.typical_ms > 0` and skip Hanson — routing a parametric
        surface through a coarse marching-cubes grid would violate AI-6.
        """
        if should_render_on_drag(self._current_surface):
            self._render_current(reset_camera=False)
        # else: slow / unmeasured surface — drag-tick is a no-op; the release
        # path (`_on_params_changed`) remains its sole render trigger.

    def _on_domain_changed(self) -> None:
        # Domain shape/radius/overlay-toggle changed — re-clip the cached raw
        # mesh without regenerating it. Camera preserved.
        # AI-10: the raw mesh is NOT regenerated here — only the clip is
        # recomputed.  CAND-11 (e1-s5): the domain changed, so the cached
        # clipped mesh is stale and must be invalidated before re-clipping.
        if self._raw_mesh is None:
            return
        self._invalidate_clipped_mesh()
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
        """Dispatch a background-thread render of the current surface.

        realtime-variety-render-e4 (CAND-4): this is now *submit-only*.
        ``surface.generate()`` runs on a ``QThreadPool`` worker
        (:class:`render_worker.MeshWorker`); the result is delivered back to
        the GUI thread by :meth:`_on_mesh_ready` via a ``QueuedConnection``
        signal.  The function returns immediately, so the GUI stays
        responsive during the ~0.5-1.5 s implicit-surface compute — and the
        old ``QApplication.processEvents()`` workaround (CONTEXT.md §8.5) is
        gone, along with its AI-9 re-entrancy hazard.

        Re-entrancy (AI-9): the e1 ``_computing`` / ``_pending_render``
        queue-latest guard is preserved — ``_computing`` is now the
        "worker in flight" state.  A render requested while a worker is in
        flight records ``_pending_render`` and returns; the *result slot*
        (not a ``finally`` here) schedules exactly one catch-up via
        ``QTimer.singleShot(0, ...)`` once the worker reports back.  At most
        one worker is ever in flight and at most one catch-up is queued, so a
        fast drag burst coalesces to "render, then one catch-up" — never an
        unbounded re-entrant stack.
        """
        if self._current_surface is None:
            return
        if self._computing:
            # A worker is in flight — record the LATEST request and return.
            # The result slot fires the catch-up, which re-reads the current
            # parameter values, so the slider's final resting position wins.
            self._pending_render = True
            # OR the reset flag so a queued `reset_camera=True` request (e.g. a
            # subtype switch) is never silently downgraded by a later
            # `reset_camera=False` slider tick landing in the same window.
            self._pending_reset_camera = self._pending_reset_camera or reset_camera
            # Keep the status-bar label tracking the user's LATEST intent — a
            # mid-flight surface switch would otherwise leave the bar naming
            # the superseded surface for the rest of the first worker's flight.
            self.statusBar().showMessage(
                f"Computing {self._current_surface.label}…"
            )
            return

        surface = self._current_surface
        params = self.parameters_panel.values() if surface.params else {}

        # Capture the job context on the instance.  The result slot uses THESE
        # — not `_current_surface` / a fresh `parameters_panel.values()` —
        # because the user may change the selection or drag a slider further
        # while the worker is in flight, and the slot must describe the
        # surface that was actually generated.
        self._computing = True
        self._generation += 1
        self._inflight_surface = surface
        self._inflight_params = params
        self._inflight_reset_camera = reset_camera

        # Busy cursor for the whole flight; restored in `_on_mesh_ready`.
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.statusBar().showMessage(f"Computing {surface.label}…")

        # Hand the worker its OWN copy of the params dict — it reads it on the
        # worker thread, so it must not alias a dict the GUI thread could
        # mutate.  `parameters_panel.values()` returns a fresh dict today, so
        # this is defensive, but it makes the thread boundary explicit.
        worker = MeshWorker(surface.generate, dict(params), self._generation)
        worker.signals.finished.connect(
            self._on_mesh_ready, Qt.ConnectionType.QueuedConnection
        )
        # Hold the worker ref for the whole flight (VTK #18782 — keeps the
        # worker's `_result` mesh ref alive until the slot has retained it).
        self._active_worker = worker
        self._render_pool.start(worker)

    @Slot(object)
    def _on_mesh_ready(self, result: MeshResult) -> None:
        """Receive a worker result on the GUI thread and render it.

        ``QueuedConnection`` guarantees this slot runs on the GUI thread, so
        every VTK GL call below (via ``_apply_domain_and_render``) is
        main-thread — the e3 spike's hard rule.  It is also serialized with
        all other GUI events, so it cannot re-enter itself (AI-9).
        """
        surface = self._inflight_surface
        params = self._inflight_params
        try:
            # Defensive supersede guard (see render_worker.is_stale_result).
            # It lives INSIDE the `try` so the `finally` cleanup (cursor
            # restore, `_computing` clear, catch-up) runs even on this branch
            # — a stale delivery must never leave the pipeline frozen.  With
            # the `_computing` single-flight guard the generation always
            # matches, so this is idempotency insurance, not a hot path; see
            # CONTEXT.md §8.16.
            if is_stale_result(result.generation, self._generation):
                return
            # VTK #18782: retain the mesh on the GUI thread before the
            # worker's `_result` ref can drop.  (`result` itself holds `.mesh`
            # for the whole slot; this named local just makes it explicit.)
            mesh = result.mesh
            if not result.ok:
                self._raw_mesh = None  # don't let a stale mesh be domain-clipped
                self._invalidate_clipped_mesh()
                # Fall back to the exception type name so the status bar is
                # never the content-free "Error: " (a bare MemoryError, an
                # arg-less exception, etc. give an empty str(exc)).
                msg = result.error_message or result.error_type
                if result.error_is_value_error:
                    # "No real zero set" means the parameter *combination*
                    # produces an empty field — not that any single slider is
                    # out of range.  Give a more actionable prefix.
                    if "No real zero set" in msg:
                        self.statusBar().showMessage(f"No surface to render — {msg}")
                    else:
                        self.statusBar().showMessage(
                            f"Parameter out of range — {msg}"
                        )
                else:
                    self.statusBar().showMessage(f"Error: {msg}")
                return

            # CAND-11: a successful generate() invalidates the clipped cache —
            # the raw mesh has changed.
            self._raw_mesh = mesh
            self._invalidate_clipped_mesh()
            # CAND-12: one stdout log line per completed generate().
            print(f"[render] {surface.label}: {result.gen_ms:.0f} ms")

            self._apply_domain_and_render(reset_camera=self._inflight_reset_camera)

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
            # Spatial extent readout — researchers want to see the bounding
            # box of the mathematical surface (not the domain-clipped slice).
            # `self._raw_mesh.bounds` returns (xmin, xmax, ymin, ymax, zmin, zmax);
            # indices [1]/[3]/[5] are the positive max-extents.  The ±max display
            # is exact for the 11 implicit-surface generators (symmetric
            # np.linspace(-bounds, bounds, n) sampling) and an honest
            # over-approximation for the 3 Hanson parametric generators at
            # default α=π/4 — see CONTEXT.md §4.3 (status-bar-bbox-2026q2-e1).
            _b = self._raw_mesh.bounds
            bbox_suffix = f"bbox ±{_b[1]:.2f} × ±{_b[3]:.2f} × ±{_b[5]:.2f}"
            # CAND-12 (realtime-variety-render-e1): append the measured
            # generate() time as a trailing "NNN ms" token after the bbox.
            base_msg = (
                f"{surface.label}  ·  {self._raw_mesh.n_points:,} verts, "
                f"{self._raw_mesh.n_cells:,} faces{param_str}"
                f"  ·  {bbox_suffix}  ·  {result.gen_ms:.0f} ms"
            )
            if result.warning_text:
                # Warning path: the Dwork conifold RuntimeWarning text alone
                # is ~175 chars; combined with base_msg the full string can
                # exceed QStatusBar's ~120-char clip width.  Hoist bbox right
                # after the warning so the spatial extent stays visible even
                # when the trailing `{label} verts, faces` content clips
                # silently — see CONTEXT.md §4.3 warning-path note.  This is
                # the one render path where researchers most need bbox: the
                # conifold mesh is geometrically unusual and verts/faces is
                # less informative.
                self.statusBar().showMessage(
                    f"⚠ {result.warning_text}  ·  {bbox_suffix}"
                    f"  |  {surface.label}  ·  {self._raw_mesh.n_points:,} verts, "
                    f"{self._raw_mesh.n_cells:,} faces{param_str}"
                    f"  ·  {result.gen_ms:.0f} ms"
                )
            else:
                self.statusBar().showMessage(base_msg)
        finally:
            QApplication.restoreOverrideCursor()
            self._computing = False
            self._active_worker = None
            # CAND-5: if a render was requested while this worker was in
            # flight, schedule exactly one catch-up.  `QTimer.singleShot(0, ...)`
            # defers it to the next event-loop iteration — `_computing` is
            # already False here, so the catch-up enters `_render_current`
            # cleanly (no re-entrancy).  `_render_current` re-reads the current
            # parameter values, so the catch-up renders the LATEST state.
            if self._pending_render:
                self._pending_render = False
                _catch_up_reset = self._pending_reset_camera
                self._pending_reset_camera = False
                QTimer.singleShot(
                    0, lambda: self._render_current(reset_camera=_catch_up_reset)
                )

    def _invalidate_clipped_mesh(self) -> None:
        """Drop the cached clipped mesh + overlay (CAND-11 / e1-s5).

        Called whenever the raw mesh changes (a new ``surface.generate()``)
        or the domain settings change (``_on_domain_changed``).  After this
        the next ``_apply_domain_and_render`` re-runs ``clip_to_domain`` and
        re-populates the cache; an appearance-only re-render in between reuses
        the still-valid cache.  See :func:`clipped_cache_is_valid` for the
        pure-function form of the validity predicate.
        """
        self._clipped_mesh = None
        self._clipped_overlay = None

    def _apply_domain_and_render(self, *, reset_camera: bool) -> None:
        """Clip the cached raw mesh per the View panel's domain settings,
        re-add the surface and (optional) domain-outline actors, and render.
        Called whenever either the mesh OR the domain settings change.

        CAND-11 (e1-s5): the clip result is cached in ``self._clipped_mesh`` /
        ``self._clipped_overlay``.  ``view_panel.clip_to_domain`` runs a full
        ``mesh.copy()`` + scalar-tag + ``clip_scalar`` — re-running it for an
        appearance-only re-render (no raw-mesh, no domain change) is pure
        waste.  The cache is invalidated by ``_invalidate_clipped_mesh`` on a
        raw-mesh change (new ``surface.generate()``) or a domain change
        (``_on_domain_changed``), so a populated cache here is always valid
        for the current raw mesh + domain settings.
        """
        if self._raw_mesh is None:
            return

        if self._clipped_mesh is None:
            clipped, overlay = self.view_panel.clip_to_domain(self._raw_mesh)
            self._clipped_mesh = clipped
            self._clipped_overlay = overlay
        else:
            clipped, overlay = self._clipped_mesh, self._clipped_overlay

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
                    color=COLOR_WIREFRAME_OVERLAY,
                    opacity=0.35,
                    line_width=1,
                    pickable=False,
                    lighting=False,
                )
            # Empty-clip branch: `self._actor` is NOT reconstructed here — the
            # previous render's actor is still live (or there is no actor on
            # first launch).  If a future refactor adds an actor in this
            # branch (e.g. a placeholder surface or bounding-box stand-in), it
            # MUST mirror the UPL-9 lighting (`ambient`, `diffuse`, `specular`,
            # `specular_power`) from the main path below, otherwise the actor
            # silently uses VTK scene defaults and visibly mismatches the rest
            # of the app.  Pulled out as a guard comment per the milestone's
            # frontend-ux critic MEDIUM finding.
            self.view_panel.re_apply_overlays()
            self.plotter.render()
            return

        # UPL-9 (graph-and-window-2026q2-e1): explicit ambient + diffuse so the
        # K3 surface family doesn't render flat against the dark viewport.  VTK
        # scene defaults (ambient=0.0, diffuse=1.0) under PyVista produce shallow
        # shading on convex surfaces — see finding M-5 in
        # `.claude/notes/frontend-uplifts/2026q2-graph-and-window/discover/current-state-critic-brief.md`.
        # Elevated ambient (0.15) + slightly-reduced diffuse (0.85) keep the
        # bright highlights but lift dark concavities so curvature variation
        # is legible.
        self._actor = self.plotter.add_mesh(
            clipped,
            smooth_shading=True,
            specular=0.3,
            specular_power=15,
            ambient=0.15,
            diffuse=0.85,
        )
        self.appearance_panel.apply_to_actor(self._actor)

        if overlay is not None:
            self._domain_overlay_actor = self.plotter.add_mesh(
                overlay,
                style="wireframe",
                color=COLOR_WIREFRAME_OVERLAY,
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

    # --- theme system ------------------------------------------------------

    def _build_theme_menu(self) -> None:
        """Construct the menu bar's Theme menu (Light / Dark / Follow system).

        Dark is the launch default (the viewport is always #2f2f2f, so dark
        chrome is the coherent baseline).  Theme choice is V0-scope only:
        the next launch returns to dark.  Persisting the user's pick is
        UPL-25's territory (QSettings dock + theme state).
        """
        theme_menu = self.menuBar().addMenu("Theme")
        # AI-11: fully qualified Qt enums.  QAction + QActionGroup live in
        # PySide6.QtGui in Qt 6 (deprecated in QtWidgets).
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)

        action_dark = QAction("Dark", self, checkable=True, checked=True)
        action_dark.triggered.connect(lambda: self._on_theme_changed("dark"))
        self._theme_group.addAction(action_dark)
        theme_menu.addAction(action_dark)

        action_light = QAction("Light", self, checkable=True)
        action_light.triggered.connect(lambda: self._on_theme_changed("light"))
        self._theme_group.addAction(action_light)
        theme_menu.addAction(action_light)

        action_follow = QAction("Follow system", self, checkable=True)
        action_follow.triggered.connect(lambda: self._on_theme_changed("follow"))
        self._theme_group.addAction(action_follow)
        theme_menu.addAction(action_follow)

        # Cache the actions for `_on_theme_changed` to manage the system-theme
        # signal connection on entry / exit of "Follow system" mode.
        self._action_dark = action_dark
        self._action_light = action_light
        self._action_follow = action_follow

        # The colorSchemeChanged signal is connected lazily when the user
        # selects "Follow system" and disconnected when they switch away —
        # avoids the override-conflict described in the research brief.
        self._system_theme_connection = None

    def _on_theme_changed(self, name: str) -> None:
        """Swap the application stylesheet + active theme state.

        `name` is one of: "dark", "light", "follow".  The "follow" path
        resolves the current system color scheme via
        ``QGuiApplication.styleHints().colorScheme()`` and applies the
        matching stylesheet, then connects to ``colorSchemeChanged`` so
        future system-theme changes propagate live.  Selecting "Dark" or
        "Light" disconnects that signal so the explicit choice sticks.

        AI-9 safe: ``QApplication.setStyleSheet`` is synchronous and does not
        call ``processEvents``.  No re-entry into the render pipeline.
        """
        style_hints = QGuiApplication.styleHints()

        # Disconnect any prior follow-system subscription before re-deciding.
        # No try/except: the `is not None` guard already ensures a live
        # connection object, and QGuiApplication.styleHints() is a process-
        # lifetime singleton — neither RuntimeError nor TypeError can occur.
        # (dark-mode-2026q2-e1 rect L1: simplified per the adversary critic.)
        if self._system_theme_connection is not None:
            style_hints.colorSchemeChanged.disconnect(self._system_theme_connection)
            self._system_theme_connection = None

        if name == "follow":
            # Resolve current system scheme; subscribe for future changes.
            scheme = style_hints.colorScheme()
            resolved = "light" if scheme == Qt.ColorScheme.Light else "dark"
            self._active_theme = resolved
            self._system_theme_connection = style_hints.colorSchemeChanged.connect(
                lambda s: self._apply_system_theme(s)
            )
        else:
            self._active_theme = name

        QApplication.instance().setStyleSheet(
            APP_STYLESHEET if self._active_theme == "light" else APP_STYLESHEET_DARK
        )

        # qtawesome-icons-2026q2-e1 (UPL-4): re-render icons with the new
        # theme's TEXT_VALUE color so the button glyphs match the new chrome.
        # Synchronous; AI-9 safe (no processEvents involved).
        self.view_panel.refresh_icons(self._active_theme)
        self.parameters_panel.refresh_icons(self._active_theme)

        # Re-seed the appearance panel's variety-default color from the active
        # theme's dict — without this, switching theme while a variety is
        # selected leaves the swatch on the old theme's default (visible
        # mismatch with the new chrome).  If no variety is selected yet, the
        # call is a no-op against BG_SURFACE_DEFAULT (the shared fallback).
        current_variety = self.variety_combo.currentText()
        if current_variety in VARIETIES:
            self.appearance_panel.set_default_color(
                get_variety_default_colors(self._active_theme).get(
                    current_variety, BG_SURFACE_DEFAULT
                )
            )
            # dark-mode-2026q2-e1 rect MEDIUM-3: push the new color through to
            # the live actor immediately so the viewport doesn't lag behind
            # the swatch on theme switch.  V0 light/dark colors are identical
            # so this is a no-op visual change today, but it establishes the
            # correct pattern for any future milestone that diverges the dark
            # variety palette (e.g. desaturating for depth perception).
            if self._actor is not None:
                self.appearance_panel.apply_to_actor(self._actor)
                self.plotter.render()

    def _apply_system_theme(self, scheme) -> None:
        """Handler for QStyleHints.colorSchemeChanged when 'Follow system'
        is active.  Maps the Qt.ColorScheme enum to our internal theme name
        and re-applies the stylesheet without disconnecting the signal.
        """
        resolved = "light" if scheme == Qt.ColorScheme.Light else "dark"
        if resolved == self._active_theme:
            return
        self._active_theme = resolved
        QApplication.instance().setStyleSheet(
            APP_STYLESHEET if resolved == "light" else APP_STYLESHEET_DARK
        )
        # qtawesome-icons-2026q2-e1 (UPL-4): mirror the refresh_icons call
        # from _on_theme_changed so OS-driven theme changes also re-render
        # icons.  Synchronous; AI-9 safe.
        self.view_panel.refresh_icons(resolved)
        self.parameters_panel.refresh_icons(resolved)
        current_variety = self.variety_combo.currentText()
        if current_variety in VARIETIES:
            self.appearance_panel.set_default_color(
                get_variety_default_colors(resolved).get(
                    current_variety, BG_SURFACE_DEFAULT
                )
            )
            # dark-mode-2026q2-e1 rect MEDIUM-3: mirror the actor-refresh in
            # _on_theme_changed so live-OS-theme-change also propagates to
            # the viewport without a user interaction.
            if self._actor is not None:
                self.appearance_panel.apply_to_actor(self._actor)
                self.plotter.render()

    # --- lifecycle ---------------------------------------------------------

    def closeEvent(self, event):
        # dark-mode-2026q2-e1 rect L2: disconnect the follow-system signal
        # if active.  Harmless in the current single-window main() pattern
        # (process exits after app.exec()), but the lambda captures `self` —
        # disconnecting before destruction prevents a dangling reference if
        # the app ever gains multi-window / session-restore behaviour.
        if self._system_theme_connection is not None:
            QGuiApplication.styleHints().colorSchemeChanged.disconnect(
                self._system_theme_connection
            )
            self._system_theme_connection = None
        # realtime-variety-render-e4 (CAND-4): drain any in-flight mesh worker
        # before the VTK render window is torn down.  A worker still building
        # a `pv.PolyData` while `plotter.close()` destroys the VTK context is
        # the exact cross-thread teardown hazard the e3 spike flagged.  This
        # drains `_render_pool` (this app's dedicated pool — not the global
        # instance), bounded: a single `surface.generate()` is ≲1.5 s; the
        # 30 s cap is a safety net, not an expected wait.
        self._render_pool.waitForDone(30000)
        self.plotter.close()
        super().closeEvent(event)


def main() -> int:
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    # dark-mode-2026q2-e1 (UPL-1): dark is the launch default because the
    # VTK viewport is always #2f2f2f.  Users can toggle to Light or Follow
    # system via the Theme menu in the main-window menu bar.
    app.setStyleSheet(APP_STYLESHEET_DARK)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
