"""Tests for the print-options CLI flags + the PrintOptionsDialog widget.

Three layers:
  * CLI — calls export.__main__.main([...]) directly, writes real STLs into
    tmp_path, and reads them back to verify the chosen build volume is honoured
    / clamped. Error paths assert nonzero exit (SystemExit from argparse error).
  * Dialog (Qt-free) — the option-extraction logic via build_export_kwargs.
  * Dialog (headless offscreen) — construct PrintOptionsDialog under an
    offscreen QApplication (mirroring tests/test_clip_domain.py), drive its
    widgets, and assert options()/export_kwargs(). NEVER constructs MainWindow.
  * Source-parse — app.py's _on_export_stl_print wiring (no widget built).
"""

from __future__ import annotations

import inspect
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from export import __main__ as cli
from export.build_volumes import PRINTER_PRESETS, build_export_kwargs


# ===========================================================================
# CLI
# ===========================================================================

def _read_extent_mm(path):
    import pyvista as pv

    mesh = pv.read(str(path))
    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
    return (xmax - xmin, ymax - ymin, zmax - zmin)


def test_cli_list_printers_exits_zero_no_file(tmp_path, capsys):
    rc = cli.main(["--list-printers"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Bambu Lab H2S" in out
    assert "Bambu Lab A1 mini" in out
    # No STL written.
    assert not list(tmp_path.glob("*.stl"))


def test_cli_preset_a1_mini_fits_volume(tmp_path):
    out = tmp_path / "a1mini.stl"
    rc = cli.main([
        "--out", str(out),
        "--printer", "Bambu Lab A1 mini",
        "--size", "100",
    ])
    assert rc == 0
    assert out.exists()
    ext = _read_extent_mm(out)
    # Longest axis ~100 mm (target), comfortably inside 180^3.
    assert max(ext) <= 180.0
    assert max(ext) == pytest.approx(100.0, abs=2.0)


def test_cli_custom_printer_dims(tmp_path):
    out = tmp_path / "custom.stl"
    rc = cli.main([
        "--out", str(out),
        "--printer-dims", "200", "200", "200",
        "--size", "150",
    ])
    assert rc == 0
    ext = _read_extent_mm(out)
    assert max(ext) <= 200.0
    assert max(ext) == pytest.approx(150.0, abs=2.0)


def test_cli_size_zero_fills_plate(tmp_path):
    out = tmp_path / "fill.stl"
    rc = cli.main([
        "--out", str(out),
        "--printer", "Bambu Lab A1 mini",
        "--size", "0",
    ])
    assert rc == 0
    ext = _read_extent_mm(out)
    # Filling 180^3 minus 5 mm/side margin -> ~170 mm usable on the longest axis.
    assert max(ext) <= 170.0 + 1e-3
    assert max(ext) > 100.0  # genuinely filling, not the 120 mm default


def test_cli_oversize_size_is_clamped(tmp_path):
    out = tmp_path / "oversize.stl"
    rc = cli.main([
        "--out", str(out),
        "--printer", "Bambu Lab A1 mini",
        "--size", "5000",
    ])
    assert rc == 0
    ext = _read_extent_mm(out)
    # Clamped down into the 180^3 build volume minus margin.
    assert max(ext) <= 170.0 + 1e-3


def test_cli_unknown_printer_errors(tmp_path):
    out = tmp_path / "x.stl"
    with pytest.raises(SystemExit) as ei:
        cli.main(["--out", str(out), "--printer", "Bogus Printer"])
    assert ei.value.code != 0
    assert not out.exists()


def test_cli_printer_and_dims_mutually_exclusive(tmp_path):
    out = tmp_path / "x.stl"
    with pytest.raises(SystemExit) as ei:
        cli.main([
            "--out", str(out),
            "--printer", "Bambu Lab H2S",
            "--printer-dims", "200", "200", "200",
        ])
    assert ei.value.code != 0
    assert not out.exists()


def test_cli_default_printer_when_no_flag(tmp_path):
    out = tmp_path / "default.stl"
    rc = cli.main(["--out", str(out), "--size", "120"])
    assert rc == 0
    ext = _read_extent_mm(out)
    assert max(ext) == pytest.approx(120.0, abs=2.0)


# ===========================================================================
# Dialog option-extraction logic (Qt-free, via build_export_kwargs)
# ===========================================================================

def test_dialog_logic_preset_path():
    kw = build_export_kwargs(printer="Bambu Lab X1C", target_mm=120.0, binary=True)
    assert kw["build"] == PRINTER_PRESETS["Bambu Lab X1C"]
    assert kw["target_mm"] == 120.0


def test_dialog_logic_custom_and_fit():
    kw = build_export_kwargs(dims=(150.0, 150.0, 150.0), fit_to_plate=True)
    assert kw["target_mm"] is None
    assert kw["build"].x_mm == 150.0


# ===========================================================================
# Dialog widget (headless offscreen) — mirrors tests/test_clip_domain.py
# ===========================================================================

def _ensure_qapp():
    from PySide6.QtWidgets import QApplication

    if QApplication.instance() is None:
        QApplication(["test", "--platform", "offscreen"])


def test_dialog_default_options():
    _ensure_qapp()
    from _qt.dialogs.print_options_dialog import PrintOptionsDialog

    dlg = PrintOptionsDialog(printer="Bambu Lab H2S", target_mm=120.0)
    opts = dlg.options()
    assert opts["printer"] == "Bambu Lab H2S"
    assert opts["dims"] is None
    assert opts["target_mm"] == 120.0
    assert opts["fit_to_plate"] is False
    assert opts["binary"] is True
    kw = dlg.export_kwargs()
    assert kw["build"] == PRINTER_PRESETS["Bambu Lab H2S"]
    assert kw["target_mm"] == 120.0


def test_dialog_custom_entry_reveals_dims():
    _ensure_qapp()
    from _qt.dialogs.print_options_dialog import CUSTOM_ENTRY, PrintOptionsDialog

    dlg = PrintOptionsDialog()
    # Initially a preset is selected -> dims row hidden, printer is a preset.
    assert dlg.options()["printer"] is not None
    dlg._printer_combo.setCurrentText(CUSTOM_ENTRY)
    dlg._dim_x.setValue(200.0)
    dlg._dim_y.setValue(210.0)
    dlg._dim_z.setValue(220.0)
    opts = dlg.options()
    assert opts["printer"] is None
    assert opts["dims"] == (200.0, 210.0, 220.0)
    kw = dlg.export_kwargs()
    assert (kw["build"].x_mm, kw["build"].y_mm, kw["build"].z_mm) == (200.0, 210.0, 220.0)


def test_dialog_fit_to_plate_disables_size():
    _ensure_qapp()
    from _qt.dialogs.print_options_dialog import PrintOptionsDialog

    dlg = PrintOptionsDialog(target_mm=120.0)
    assert dlg._size_spin.isEnabled() is True
    dlg._fit_check.setChecked(True)
    assert dlg._size_spin.isEnabled() is False
    kw = dlg.export_kwargs()
    assert kw["target_mm"] is None


def test_dialog_ascii_format_selection():
    _ensure_qapp()
    from _qt.dialogs.print_options_dialog import PrintOptionsDialog

    dlg = PrintOptionsDialog(binary=False)
    assert dlg.options()["binary"] is False
    assert dlg.export_kwargs()["binary"] is False


def test_dialog_custom_dims_row_visibility_toggles():
    _ensure_qapp()
    from _qt.dialogs.print_options_dialog import CUSTOM_ENTRY, PrintOptionsDialog

    dlg = PrintOptionsDialog()
    # Hidden for a preset selection. isVisibleTo(parent) reflects the local
    # visibility flag without requiring the (never-shown) dialog to be mapped.
    assert dlg._dims_row.isVisibleTo(dlg) is False
    dlg._printer_combo.setCurrentText(CUSTOM_ENTRY)
    assert dlg._dims_row.isVisibleTo(dlg) is True


# ===========================================================================
# Source-parse: app.py _on_export_stl_print wiring (no MainWindow construction)
# ===========================================================================

def test_app_handler_constructs_dialog_and_passes_kwargs():
    import app

    src = inspect.getsource(app.MainWindow._on_export_stl_print)
    # Opens the dialog and forwards its resolved kwargs into export_to_stl.
    assert "PrintOptionsDialog" in src
    assert "export_kwargs" in src
    assert "**export_kwargs" in src
    # Preserves the AI-9 single-flight guard + the NotImplementedError fallback.
    assert "self._computing" in src
    assert "NotImplementedError" in src
    # Persists last-used choices via QSettings LastSession keys.
    assert "LastSession/print" in src
