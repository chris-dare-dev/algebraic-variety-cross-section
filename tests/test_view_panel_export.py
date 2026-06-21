"""Qt-free guards for the View dock's Export STL… wiring (stl-print-export).

AI-2 compliant: asserts the public API surface via CLASS-attribute
introspection only — never constructs a QApplication or instantiates the
QWidget (importing the module is fine; building a widget is not).
"""

from __future__ import annotations

import inspect


def test_view_panel_exposes_export_stl_signal_and_enabler():
    from PySide6.QtCore import Signal
    from _qt.panels.view import ViewPanel

    # The signal MainWindow connects to (View dock → Export STL…).
    assert isinstance(ViewPanel.export_stl_requested, Signal)
    # The enable/disable hook MainWindow drives in lockstep with the
    # File → Export Mesh… action.
    assert callable(ViewPanel.set_export_stl_enabled)


def test_mainwindow_handler_and_connection_exist():
    """The handler exists and the signal is connected to it.

    Parsed from source (no QApplication / no MainWindow construction — AI-3
    forbids MainWindow under offscreen because it hosts a QtInteractor).
    """
    import app

    assert hasattr(app.MainWindow, "_on_export_stl_print")
    assert callable(app.MainWindow._on_export_stl_print)

    src = inspect.getsource(app.MainWindow)
    # The View panel's signal is wired to the print-export handler.
    assert "export_stl_requested.connect(self._on_export_stl_print)" in src
    # The handler honors the live Clip Region (sphere/cube CSG) and respects
    # the AI-9 single-flight guard rather than generating concurrently.
    assert "domain_settings()" in src
    assert "self._computing" in src
