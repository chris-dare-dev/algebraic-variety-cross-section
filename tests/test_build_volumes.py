"""Qt-free unit tests for export.build_volumes (presets + sizing resolution).

These tests touch NO Qt — all sizing/validation logic lives in the pure module
under test (AI-2). A subset writes real STLs via the CLI (covered in
tests/test_print_options.py); here we stay purely in the resolution layer.
"""

from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from export.build_volumes import (
    DEFAULT_PRINTER,
    PRINTER_PRESETS,
    build_export_kwargs,
    custom_build_volume,
    get_build_volume,
    list_presets,
    resolve_build_volume,
)
from export.printable import BuildVolume


# ---------------------------------------------------------------------------
# Preset registry
# ---------------------------------------------------------------------------

def test_required_presets_present():
    for name in (
        "Bambu Lab H2S",
        "Bambu Lab X1C",
        "Bambu Lab P1S",
        "Bambu Lab A1",
        "Bambu Lab A1 mini",
    ):
        assert name in PRINTER_PRESETS
        assert isinstance(PRINTER_PRESETS[name], BuildVolume)


@pytest.mark.parametrize(
    "name, dims",
    [
        ("Bambu Lab H2S", (340.0, 320.0, 340.0)),
        ("Bambu Lab X1C", (256.0, 256.0, 256.0)),
        ("Bambu Lab P1S", (256.0, 256.0, 256.0)),
        ("Bambu Lab A1", (256.0, 256.0, 256.0)),
        ("Bambu Lab A1 mini", (180.0, 180.0, 180.0)),
    ],
)
def test_preset_dimensions(name, dims):
    bv = PRINTER_PRESETS[name]
    assert (bv.x_mm, bv.y_mm, bv.z_mm) == dims


def test_default_printer_is_h2s():
    assert DEFAULT_PRINTER == "Bambu Lab H2S"
    assert DEFAULT_PRINTER in PRINTER_PRESETS


def test_list_presets_order_and_default_first():
    presets = list_presets()
    assert presets[0] == DEFAULT_PRINTER
    assert presets == list(PRINTER_PRESETS)


# ---------------------------------------------------------------------------
# get_build_volume
# ---------------------------------------------------------------------------

def test_get_build_volume_valid():
    assert get_build_volume("Bambu Lab A1 mini") is PRINTER_PRESETS["Bambu Lab A1 mini"]


def test_get_build_volume_unknown_raises():
    with pytest.raises(KeyError) as ei:
        get_build_volume("Nonexistent Printer")
    assert "Nonexistent Printer" in str(ei.value)


# ---------------------------------------------------------------------------
# custom_build_volume
# ---------------------------------------------------------------------------

def test_custom_build_volume_valid():
    bv = custom_build_volume(200, 210, 220)
    assert (bv.x_mm, bv.y_mm, bv.z_mm) == (200.0, 210.0, 220.0)


@pytest.mark.parametrize(
    "x, y, z",
    [
        (0, 100, 100),
        (100, 0, 100),
        (100, 100, 0),
        (-1, 100, 100),
        (100, -5, 100),
        (100, 100, -10),
    ],
)
def test_custom_build_volume_rejects_nonpositive(x, y, z):
    with pytest.raises(ValueError):
        custom_build_volume(x, y, z)


# ---------------------------------------------------------------------------
# resolve_build_volume (preset XOR dims)
# ---------------------------------------------------------------------------

def test_resolve_preset_only():
    bv = resolve_build_volume("Bambu Lab X1C", None)
    assert bv == PRINTER_PRESETS["Bambu Lab X1C"]


def test_resolve_dims_only():
    bv = resolve_build_volume(None, (150.0, 160.0, 170.0))
    assert (bv.x_mm, bv.y_mm, bv.z_mm) == (150.0, 160.0, 170.0)


def test_resolve_both_raises():
    with pytest.raises(ValueError):
        resolve_build_volume("Bambu Lab H2S", (200.0, 200.0, 200.0))


def test_resolve_neither_raises():
    with pytest.raises(ValueError):
        resolve_build_volume(None, None)


def test_resolve_unknown_preset_raises():
    with pytest.raises(KeyError):
        resolve_build_volume("Bogus", None)


def test_resolve_bad_dims_length_raises():
    with pytest.raises(ValueError):
        resolve_build_volume(None, (200.0, 200.0))


# ---------------------------------------------------------------------------
# build_export_kwargs — the core mapping
# ---------------------------------------------------------------------------

def test_kwargs_default_uses_h2s_and_target_120_when_no_inputs():
    kw = build_export_kwargs(target_mm=120.0)
    assert kw["build"] == PRINTER_PRESETS[DEFAULT_PRINTER]
    assert kw["target_mm"] == 120.0
    assert kw["margin_mm"] == 5.0
    assert kw["binary"] is True


def test_kwargs_preset():
    kw = build_export_kwargs(printer="Bambu Lab A1 mini", target_mm=100.0)
    assert kw["build"] == PRINTER_PRESETS["Bambu Lab A1 mini"]
    assert kw["target_mm"] == 100.0


def test_kwargs_custom_dims():
    kw = build_export_kwargs(dims=(200.0, 200.0, 200.0), target_mm=90.0)
    assert (kw["build"].x_mm, kw["build"].y_mm, kw["build"].z_mm) == (200.0, 200.0, 200.0)


def test_kwargs_fit_to_plate_maps_target_to_none():
    kw = build_export_kwargs(printer="Bambu Lab H2S", fit_to_plate=True)
    assert kw["target_mm"] is None


def test_kwargs_fit_to_plate_with_target_raises():
    with pytest.raises(ValueError):
        build_export_kwargs(fit_to_plate=True, target_mm=100.0)


def test_kwargs_missing_target_without_fit_raises():
    with pytest.raises(ValueError):
        build_export_kwargs(printer="Bambu Lab H2S")


@pytest.mark.parametrize("bad", [0.0, -1.0, -50.0])
def test_kwargs_nonpositive_target_raises(bad):
    with pytest.raises(ValueError):
        build_export_kwargs(target_mm=bad)


def test_kwargs_oversize_target_is_allowed_for_clamping():
    # An oversize target is NOT rejected here — export_to_stl clamps it down.
    kw = build_export_kwargs(printer="Bambu Lab A1 mini", target_mm=5000.0)
    assert kw["target_mm"] == 5000.0
    assert kw["build"].min_mm == 180.0  # smaller than the requested target


@pytest.mark.parametrize("margin", [0.0, 1.0, 12.5])
def test_kwargs_valid_margins(margin):
    kw = build_export_kwargs(target_mm=100.0, margin_mm=margin)
    assert kw["margin_mm"] == margin


@pytest.mark.parametrize("margin", [-0.1, -5.0])
def test_kwargs_negative_margin_raises(margin):
    with pytest.raises(ValueError):
        build_export_kwargs(target_mm=100.0, margin_mm=margin)


@pytest.mark.parametrize("binary", [True, False])
def test_kwargs_binary_flag(binary):
    kw = build_export_kwargs(target_mm=100.0, binary=binary)
    assert kw["binary"] is binary


def test_kwargs_both_printer_and_dims_raises():
    with pytest.raises(ValueError):
        build_export_kwargs(
            printer="Bambu Lab H2S", dims=(200.0, 200.0, 200.0), target_mm=100.0
        )


def test_kwargs_unknown_printer_raises():
    with pytest.raises(KeyError):
        build_export_kwargs(printer="Not A Printer", target_mm=100.0)


def test_kwargs_keys_exactly_match_export_to_stl_contract():
    kw = build_export_kwargs(target_mm=100.0)
    assert set(kw) == {"build", "target_mm", "margin_mm", "binary"}
