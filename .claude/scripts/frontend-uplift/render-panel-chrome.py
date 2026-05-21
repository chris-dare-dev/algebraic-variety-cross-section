#!/usr/bin/env python3
"""Capture panel-chrome PNGs under QT_QPA_PLATFORM=offscreen.

Tier-1 companion to the visual-scout's off-screen surface renders.  The three
panel widgets — AppearancePanel, ViewPanel, ParametersPanel — are pure-Qt
QWidgets that DO NOT instantiate `QtInteractor`.  They can therefore be
constructed under `QT_QPA_PLATFORM=offscreen` without triggering the macOS
Qt+VTK GL segfault that AI-3 forbids.  This lets the visual scout obtain
pixel-truth on slider rails, group-box headers, button states, focus rings,
and overall QSS-rendered chrome — none of which the surface-only off-screen
renders surface.

The forbidden combination remains forbidden: never instantiate `MainWindow()`
under `QT_QPA_PLATFORM=offscreen`.  See `.claude/references/app-invariants.md`
AI-3 for the full lock.

For each panel we capture:
  • -empty.png — panel right after construction (no surface selected)
  • -populated.png — panel after a realistic surface load (sliders bound, etc.)
At two resolutions per state:
  • default  — the dock's nominal size (~320×720)
  • 2x      — same content rendered into a 2x pixmap for HiDPI scrutiny

Outputs (relative to <out-dir>):
  appearance-light-empty-default.png       appearance-light-empty-2x.png
  appearance-light-populated-default.png   appearance-light-populated-2x.png
  view-light-empty-default.png             view-light-empty-2x.png
  view-light-populated-default.png         view-light-populated-2x.png
  parameters-light-empty-default.png       parameters-light-empty-2x.png
  parameters-light-populated-default.png   parameters-light-populated-2x.png

Dark-theme variants are gated on `styles.APP_STYLESHEET_DARK` existing —
emitted automatically once UPL-4 lands an `APP_STYLESHEET_DARK` export
alongside its `PALETTE_DARK` placeholder (see the marker in `styles.py`).
Today only the LIGHT theme is captured.

Note on `-2x` captures: these resize the WIDGET to twice its nominal size and
grab at device-pixel-ratio 1 — they exercise layout breathing room at a wider
dock, NOT true HiDPI / Retina rendering.  True DPR-2 captures would require a
headed macOS session (`screencapture -l <window-id>` honors DPR); see the
Tier 2 design notes in `.claude/references/frontend-uplift/source-registry.md`
§4b for the planned approach.

Usage:
  .venv/bin/python .claude/scripts/frontend-uplift/render-panel-chrome.py <out-dir>

Exits:
  0 — success (all 12+ PNGs captured)
  1 — panel construction / grab failure (human-readable diagnostic to stderr)
  2 — usage error (wrong argument count)

After capturing, the script self-verifies that each panel's populated PNG
differs from its empty PNG (sha256).  A pair that hashes identically is
flagged as a non-fatal WARNING to stderr — this catches the failure mode
where a panel's private setter attribute name drifts and `hasattr` silently
swallows the miss.  Always check stderr for `[render-panel-chrome] WARNING:`
lines after a run.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Set BEFORE importing PySide6 — Qt freezes the platform choice at first
# QApplication import.  No-op if already set.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Suppress Qt's font/platform debug noise on stdout — `qt.qpa.fonts: Populating
# font family aliases…` and `This plugin does not support propagateSizeHints()`
# pollute the success output the slash command surfaces to the user.  These
# warnings are environmental and do not affect the captured pixels.
os.environ.setdefault(
    "QT_LOGGING_RULES",
    "qt.qpa.fonts=false;qt.qpa.plugin.debug=false;*.debug=false",
)

# Repo root — script lives at <root>/.claude/scripts/frontend-uplift/.  Insert
# the root onto sys.path so `surfaces`, `styles`, and the three panel modules
# import cleanly regardless of cwd.
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT))


def _usage() -> "tuple[int, str]":
    return 2, (
        "usage: render-panel-chrome.py <out-dir>\n"
        "  <out-dir>  Directory to write the panel PNGs into.  Created if missing."
    )


def _err(msg: str) -> None:
    sys.stderr.write(f"[render-panel-chrome] {msg}\n")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        code, msg = _usage()
        _err(msg)
        return code
    out_dir = Path(argv[1]).resolve()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except (FileExistsError, NotADirectoryError):
        _err(f"out-dir '{argv[1]}' exists as a file, not a directory")
        return 1
    except PermissionError as e:
        _err(f"out-dir '{argv[1]}' not writable: {e}")
        return 1
    # Probe writability — directory creation can succeed on NFS / read-only
    # bind mounts where individual files cannot be written.
    probe = out_dir / ".write_probe"
    try:
        probe.touch()
        probe.unlink()
    except OSError as e:
        _err(f"out-dir '{out_dir}' is not writable: {e}")
        return 1

    # ----- Qt + repo imports (must happen after QT_QPA_PLATFORM is set) -----
    try:
        from PySide6.QtCore import QSize, Qt, qInstallMessageHandler
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import (
            QApplication,
            QDockWidget,
            QMainWindow,
            QWidget,
        )
    except ImportError as e:  # pragma: no cover - environment-only branch
        _err(f"PySide6 import failed: {e}.  Install requirements.txt first.")
        return 1

    # Install a Qt message-handler filter to silence offscreen-platform noise
    # that QT_LOGGING_RULES can't reach (in particular "This plugin does not
    # support propagateSizeHints()" from QPlatformWindow's default impl, which
    # fires on every show()).  We let through anything that doesn't match the
    # known-noise patterns so a real platform error would still surface.
    _NOISE_PATTERNS = (
        "propagateSizeHints",
        "Populating font family aliases",
    )

    def _qt_message_filter(msg_type, context, message):  # noqa: ARG001
        if any(pat in message for pat in _NOISE_PATTERNS):
            return
        # Fall through to stderr for non-noise so real errors stay visible.
        sys.stderr.write(f"[qt:{int(msg_type)}] {message}\n")

    qInstallMessageHandler(_qt_message_filter)

    try:
        import styles  # noqa: F401 — verified by attribute access below
        from appearance_panel import AppearancePanel
        from parameters_panel import ParametersPanel
        from surfaces import VARIETIES
        from view_panel import ViewPanel
    except Exception as e:
        _err(f"app module import failed: {e}")
        return 1

    # ----- QApplication (one instance per process) -------------------------
    app = QApplication.instance() or QApplication(sys.argv[:1])

    # ----- Themes to capture ------------------------------------------------
    # PALETTE_DARK is a placeholder in styles.py today (UPL-4).  We auto-detect
    # to forward-port without code change when it lands.
    themes: list[tuple[str, str]] = [("light", getattr(styles, "APP_STYLESHEET", ""))]
    dark_qss = getattr(styles, "APP_STYLESHEET_DARK", None)
    if dark_qss:
        themes.append(("dark", dark_qss))

    # ----- Realistic populated-state source --------------------------------
    # Pick a surface with a moderate parameter count so the Parameters panel
    # renders multiple sliders (slider stacking + spacing is itself something
    # the visual scout critiques).  K3 / Fermat quartic has 4 params
    # (c, alpha, beta, gamma) — a representative load for the populated view.
    try:
        populated_specs = list(VARIETIES["K3 surface"]["Fermat quartic"].params)
    except KeyError:
        # Fall back to any surface with non-empty params.
        populated_specs = []
        for variety, models in VARIETIES.items():
            for model_name, surf in models.items():
                if surf.params:
                    populated_specs = list(surf.params)
                    break
            if populated_specs:
                break
    if not populated_specs:
        _err("no surface with parameters found in VARIETIES — cannot render populated state")
        return 1

    # ----- Capture loop -----------------------------------------------------
    # Panel dock width comes from app.py's dock construction (RIGHT and LEFT
    # docks land at ~320 px nominal width on first paint).  Height is chosen
    # to surface the full content without scrolling.
    DEFAULT_SIZE = QSize(320, 720)
    HIRES_SIZE = QSize(640, 1440)  # 2x linear → 4x pixels

    captured: list[Path] = []

    def _grab(widget: QWidget, size: QSize, dest: Path) -> None:
        widget.resize(size)
        widget.show()
        # Drain the event queue twice — `AppearancePanel` wraps its content
        # in a `QScrollArea` whose deferred layout pass may not complete on
        # the first drain.  Two cycles is empirically sufficient and cheap.
        app.processEvents()
        widget.adjustSize()
        app.processEvents()
        # UPL-28: clear focus AFTER the layout pass has settled, otherwise
        # Qt re-assigns focus to the first tab-stop child during the second
        # processEvents() pass.  Clear from `QApplication.focusWidget()` (the
        # actual focus holder — typically a child button), not from `widget`
        # itself: `widget.clearFocus()` only releases focus FROM widget; if
        # focus is on a child, that call is a no-op.  Drain once more after
        # the clear so the `:focus` paint event fully unwinds.
        focused = QApplication.focusWidget()
        if focused is not None:
            focused.clearFocus()
            app.processEvents()
        # QWidget.grab() renders the widget into a QPixmap at the widget's
        # current logical size.  `-2x.png` here means "widget resized to 2x
        # nominal" — NOT device-pixel-ratio 2.  True HiDPI capture requires
        # a headed session; see Tier 2 in source-registry §4b.
        pix: QPixmap = widget.grab()
        if pix.isNull() or pix.width() == 0:
            raise RuntimeError(f"grab() returned a null/empty pixmap for {dest.name}")
        if not pix.save(str(dest)):
            raise RuntimeError(f"failed to save PNG: {dest}")
        widget.hide()
        captured.append(dest)

    def _grab_in_dock(panel: QWidget, dock_title: str, size: QSize, dest: Path) -> None:
        """UPL-27: wrap a panel in a `QDockWidget` hosted by a vanilla
        ``QMainWindow`` and grab the host window.

        Why the QMainWindow host: a bare ``QDockWidget`` outside any parent
        floats as a top-level window.  In that mode the title bar is rendered
        by the OS window manager — which is absent under
        ``QT_QPA_PLATFORM=offscreen``, so the offscreen capture shows no
        title bar at all (probed: a bare floating dock grabs at 320x21 — just
        the content area, no chrome).  Docking into a vanilla ``QMainWindow``
        flips the dock into "docked" mode, where Qt itself paints the title
        bar and the ``styles.py:APP_STYLESHEET`` ``QDockWidget::title`` rule
        applies.

        AI-3 compliance: ``MainWindow`` (the app's class) is what AI-3 bans
        under offscreen — because it hosts a ``QtInteractor``.  A vanilla
        ``QMainWindow`` here has NO ``QtInteractor`` and NO VTK context, so
        the QApplication tree contains zero ``QtInteractor`` instances —
        which is the AI-3 one-line rule's safe-under-offscreen condition.
        See ``.claude/references/app-invariants.md`` AI-3.

        ``dock_title`` must match the production dock title in ``app.py``:
        "Appearance" / "View" / "Parameters".
        """
        host = QMainWindow()
        dock = QDockWidget(dock_title)
        dock.setWidget(panel)
        # Hide the host's empty central widget so the dock fills the captured
        # area; without this the central area paints a default-coloured strip.
        host.setCentralWidget(QWidget())
        host.centralWidget().setMaximumSize(0, 0)
        host.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        try:
            _grab(host, size, dest)
        finally:
            # `QDockWidget.setWidget()` transferred C++ ownership of `panel`
            # to `dock` (which is owned by `host`); when `host` goes out of
            # scope, Qt would delete the entire subtree including `panel` —
            # crashing the *next* call that reuses the same Python `panel`
            # reference (e.g. the HIRES capture after the DEFAULT capture).
            #
            # Re-parent the panel to None before host teardown.  PySide6
            # `QDockWidget` has no `takeWidget()` (unlike
            # `QMainWindow.takeCentralWidget()`), so do it manually.  The
            # panel's Python reference (held by the caller) keeps it alive.
            panel.setParent(None)

    for theme_name, qss in themes:
        app.setStyleSheet(qss)

        # ----- AppearancePanel ---------------------------------------------
        # Empty state: panel right after construction (no actor, no plotter
        # actually used — both callables are stubs).
        appearance_empty = AppearancePanel(
            get_actor=lambda: None,
            get_plotter=lambda: MagicMock(),
        )
        _grab_in_dock(
            appearance_empty,
            "Appearance",
            DEFAULT_SIZE,
            out_dir / f"appearance-{theme_name}-empty-default.png",
        )
        _grab_in_dock(
            appearance_empty,
            "Appearance",
            HIRES_SIZE,
            out_dir / f"appearance-{theme_name}-empty-2x.png",
        )

        # Populated state: AppearancePanel currently has no setter-based
        # population pattern — all its state is internal (color, opacity,
        # shading).  The "populated" capture exercises a non-default opacity
        # + wireframe-on + show-edges so the slider + both checkboxes appear
        # in their active styling.  These are private-attribute pokes, fine
        # for a capture harness (no signals fire because no actors are wired).
        #
        # Attribute names verified against appearance_panel.py — if a panel
        # refactor renames these, the post-capture hash check at the end of
        # this script will warn ("populated identical to empty").  Do NOT
        # silently use `hasattr` guards here; an unconditional access turns
        # rename-drift into a loud AttributeError instead of stale captures.
        appearance_populated = AppearancePanel(
            get_actor=lambda: None,
            get_plotter=lambda: MagicMock(),
        )
        appearance_populated._opacity_slider.setValue(72)
        appearance_populated._wireframe_cb.setChecked(True)
        appearance_populated._edges_cb.setChecked(True)
        _grab_in_dock(
            appearance_populated,
            "Appearance",
            DEFAULT_SIZE,
            out_dir / f"appearance-{theme_name}-populated-default.png",
        )
        _grab_in_dock(
            appearance_populated,
            "Appearance",
            HIRES_SIZE,
            out_dir / f"appearance-{theme_name}-populated-2x.png",
        )

        # ----- ViewPanel ---------------------------------------------------
        # Empty state: ViewPanel takes the plotter directly (not a callable);
        # a MagicMock satisfies the attribute access without rendering.
        view_empty = ViewPanel(MagicMock())
        _grab_in_dock(
            view_empty,
            "View",
            DEFAULT_SIZE,
            out_dir / f"view-{theme_name}-empty-default.png",
        )
        _grab_in_dock(
            view_empty,
            "View",
            HIRES_SIZE,
            out_dir / f"view-{theme_name}-empty-2x.png",
        )

        # Populated state: flip on a domain clip + bbox + axes overlay so
        # the domain combo, the clip outline checkbox, and the scene-aid
        # checkboxes render in their active styling.  Uses public domain-mode
        # constants on ViewPanel.
        #
        # Attribute names verified against view_panel.py.  See the same note
        # on AppearancePanel above — these are unconditional accesses; if a
        # panel refactor renames them this script fails loudly rather than
        # silently producing stale captures.
        view_populated = ViewPanel(MagicMock())
        # Select "Sphere" — index 1 in the (Off, Sphere, Cube) sequence.
        view_populated._domain_mode.setCurrentText(view_populated.DOMAIN_SPHERE)
        view_populated._bbox_cb.setChecked(True)
        view_populated._axes_cb.setChecked(True)
        _grab_in_dock(
            view_populated,
            "View",
            DEFAULT_SIZE,
            out_dir / f"view-{theme_name}-populated-default.png",
        )
        _grab_in_dock(
            view_populated,
            "View",
            HIRES_SIZE,
            out_dir / f"view-{theme_name}-populated-2x.png",
        )

        # ----- ParametersPanel --------------------------------------------
        # Empty state: no specs loaded → the "(no parameters for this
        # surface)" placeholder + disabled reset button.
        params_empty = ParametersPanel()
        _grab_in_dock(
            params_empty,
            "Parameters",
            DEFAULT_SIZE,
            out_dir / f"parameters-{theme_name}-empty-default.png",
        )
        _grab_in_dock(
            params_empty,
            "Parameters",
            HIRES_SIZE,
            out_dir / f"parameters-{theme_name}-empty-2x.png",
        )

        # Populated state: load the K3/Fermat quartic ParamSpec list — 4
        # params (c, α, β, γ) with mixed step / suffix / description coverage.
        # The 4-slider stack lets the scout critique multi-control spacing in
        # addition to per-slider styling.
        params_populated = ParametersPanel()
        params_populated.set_specs(populated_specs)
        params_populated.set_context_hint(
            "Each parameter sweep alters the variety's geometry. Release "
            "the slider to re-extract the level set."
        )
        _grab_in_dock(
            params_populated,
            "Parameters",
            DEFAULT_SIZE,
            out_dir / f"parameters-{theme_name}-populated-default.png",
        )
        _grab_in_dock(
            params_populated,
            "Parameters",
            HIRES_SIZE,
            out_dir / f"parameters-{theme_name}-populated-2x.png",
        )

    # ----- Post-capture integrity check ------------------------------------
    # Each panel's populated capture MUST differ from its empty capture — if
    # the populated-state setup silently failed (e.g. a private-attribute name
    # drifted and an unguarded access raised, or a future refactor used the
    # wrong setter), the populated PNG ends up byte-identical to the empty
    # PNG and the visual scout would fabricate evidence of active states that
    # don't exist.  Hash-check each pair and emit a non-fatal WARNING.
    import hashlib

    drift_warnings: list[str] = []
    for panel in ("appearance", "view", "parameters"):
        for theme_name, _ in themes:
            empty_path = out_dir / f"{panel}-{theme_name}-empty-default.png"
            populated_path = out_dir / f"{panel}-{theme_name}-populated-default.png"
            if empty_path.exists() and populated_path.exists():
                empty_hash = hashlib.sha256(empty_path.read_bytes()).digest()
                populated_hash = hashlib.sha256(populated_path.read_bytes()).digest()
                if empty_hash == populated_hash:
                    drift_warnings.append(f"{panel}/{theme_name}")
    if drift_warnings:
        _err(
            "WARNING: populated capture IDENTICAL to empty for: "
            + ", ".join(drift_warnings)
            + ".  Likely a panel attribute name drifted; check the populated-"
            "state setup in this script against the actual panel class."
        )

    sys.stdout.write(
        f"[ok] captured {len(captured)} panel-chrome PNGs into {out_dir}\n"
    )
    # List each PNG by its name relative to out_dir (not relative to its parent
    # — that path arithmetic mis-handles `out_dir == /tmp` and similar shallow
    # paths where `out_dir.parent` is in every captured path's `.parents`).
    for path in captured:
        sys.stdout.write(f"  {path.relative_to(out_dir)}\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except RuntimeError as e:
        _err(str(e))
        raise SystemExit(1)
