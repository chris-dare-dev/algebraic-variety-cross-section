"""Qt-free tests for the parameter-grid coordinate math and assignment logic.

Mirrors the discipline of ``tests/test_parameters_panel.py`` (AI-2): exercises
the pure :mod:`parameter_grid` module directly — no ``QApplication``, no VTK
context. The Qt widget layer (``parameter_grid_panel.py``) is intentionally
*not* imported here.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import parameter_grid as pg
from surfaces import (
    CALABI_YAU_QUINTIC_PARAMS,
    ENRIQUES_FIGURE_2_PARAMS,
    FANO_TWO_QUADRICS_PARAMS,
    FERMAT_PARAMS,
    KUMMER_PARAMS,
    ParamSpec,
)

_LENGTH = 240.0  # representative scene-axis length


# ---------------------------------------------------------------------------
# value <-> scene round-trip
# ---------------------------------------------------------------------------

_ROUND_TRIP_SPECS = (
    FERMAT_PARAMS
    + KUMMER_PARAMS
    + CALABI_YAU_QUINTIC_PARAMS
    + ENRIQUES_FIGURE_2_PARAMS
    + FANO_TWO_QUADRICS_PARAMS
)


@pytest.mark.parametrize("spec", _ROUND_TRIP_SPECS, ids=lambda s: s.name)
@pytest.mark.parametrize("invert", [False, True], ids=["upright", "inverted"])
def test_value_scene_round_trip(spec: ParamSpec, invert: bool) -> None:
    """value -> scene -> value recovers the step-snapped value within step/2."""
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        value = spec.minimum + frac * (spec.maximum - spec.minimum)
        scene = pg.value_to_scene(value, spec, _LENGTH, invert=invert)
        recovered = pg.scene_to_value(scene, spec, _LENGTH, invert=invert)
        snapped = pg.snap_to_step(value, spec)
        assert abs(recovered - snapped) <= spec.step / 2 + 1e-9, (
            f"{spec.name}: value={value}, recovered={recovered}, snapped={snapped}"
        )


@pytest.mark.parametrize("spec", _ROUND_TRIP_SPECS, ids=lambda s: s.name)
def test_norm_endpoints(spec: ParamSpec) -> None:
    """minimum maps to norm 0, maximum maps to norm 1."""
    assert pg.value_to_norm(spec.minimum, spec) == pytest.approx(0.0)
    assert pg.value_to_norm(spec.maximum, spec) == pytest.approx(1.0)


def test_invert_flips_vertical_axis() -> None:
    """With invert=True the minimum sits at the bottom (scene Y == length)."""
    spec = FERMAT_PARAMS[0]
    assert pg.value_to_scene(spec.minimum, spec, _LENGTH, invert=True) == pytest.approx(_LENGTH)
    assert pg.value_to_scene(spec.maximum, spec, _LENGTH, invert=True) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# clamping at the grid edges
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spec", _ROUND_TRIP_SPECS, ids=lambda s: s.name)
def test_scene_past_edge_clamps_to_bounds(spec: ParamSpec) -> None:
    """Dragging the dot past either grid edge yields exactly min / max."""
    assert pg.scene_to_value(-100.0, spec, _LENGTH) == pytest.approx(spec.minimum)
    assert pg.scene_to_value(_LENGTH + 100.0, spec, _LENGTH) == pytest.approx(spec.maximum)
    # Inverted axis: low scene-Y == high value, high scene-Y == low value.
    assert pg.scene_to_value(-100.0, spec, _LENGTH, invert=True) == pytest.approx(spec.maximum)
    assert pg.scene_to_value(_LENGTH + 100.0, spec, _LENGTH, invert=True) == pytest.approx(spec.minimum)


def test_clamp_value_inside_and_outside() -> None:
    spec = FERMAT_PARAMS[0]  # c in [0.1, 30.0]
    assert pg.clamp_value(15.0, spec) == 15.0
    assert pg.clamp_value(-5.0, spec) == spec.minimum
    assert pg.clamp_value(999.0, spec) == spec.maximum


def test_snap_matches_slider_tick_set() -> None:
    """norm_to_value lands only on minimum + k*step, like the QSlider does."""
    spec = ParamSpec("t", "t", 0.0, 1.0, 0.0, step=0.1)
    for norm in (0.04, 0.12, 0.27, 0.51, 0.83, 0.99):
        v = pg.norm_to_value(norm, spec)
        ticks = round((v - spec.minimum) / spec.step)
        assert abs(v - (spec.minimum + ticks * spec.step)) < 1e-9


# ---------------------------------------------------------------------------
# enable / disable predicate
# ---------------------------------------------------------------------------


def test_grid_disabled_for_zero_or_one_param() -> None:
    assert pg.grid_enabled([]) is False
    assert pg.grid_enabled(KUMMER_PARAMS) is False  # exactly 1 param
    assert len(KUMMER_PARAMS) == 1


def test_grid_enabled_for_two_or_more_params() -> None:
    assert pg.grid_enabled(ENRIQUES_FIGURE_2_PARAMS) is True   # 3 params
    assert pg.grid_enabled(FERMAT_PARAMS) is True               # 4 params
    assert pg.grid_enabled(FANO_TWO_QUADRICS_PARAMS) is True    # 4 params


def test_default_axis_count() -> None:
    assert pg.default_axis_count([]) == 0
    assert pg.default_axis_count(KUMMER_PARAMS) == 0            # 1 param
    assert pg.default_axis_count(FANO_TWO_QUADRICS_PARAMS) == 3  # 4 -> capped at 3
    assert pg.default_axis_count(ENRIQUES_FIGURE_2_PARAMS) == 3  # 3 params
    assert pg.default_axis_count(FERMAT_PARAMS) == 3            # 4 -> capped at 3


def test_two_param_surface_gets_two_axes() -> None:
    """A hypothetical 2-param surface auto-assigns a 2D grid."""
    two = [
        ParamSpec("a", "A", 0.0, 1.0, 0.5),
        ParamSpec("b", "B", 0.0, 1.0, 0.5),
    ]
    assert pg.grid_enabled(two) is True
    assert pg.default_axis_count(two) == 2


# ---------------------------------------------------------------------------
# axis assignment + residual split
# ---------------------------------------------------------------------------


def test_assign_axes_2d_fermat_residual_split() -> None:
    """Fermat quartic (4 params), 2-axis grid -> 2 residual sliders."""
    a = pg.assign_axes(FERMAT_PARAMS, ["c", "alpha"])
    assert [s.name for s in a.axes] == ["c", "alpha"]
    assert [s.name for s in a.residual] == ["beta", "gamma"]


def test_assign_axes_3d_fermat_residual_split() -> None:
    """Fermat quartic (4 params), 3-axis grid -> 1 residual slider."""
    a = pg.assign_axes(FERMAT_PARAMS, ["c", "alpha", "beta"])
    assert [s.name for s in a.axes] == ["c", "alpha", "beta"]
    assert [s.name for s in a.residual] == ["gamma"]


def test_assign_axes_3d_exact_no_residual() -> None:
    """A 3-param surface on a 3-axis grid leaves no residual sliders."""
    a = pg.assign_axes(ENRIQUES_FIGURE_2_PARAMS, ["lam0", "lam3", "c"])
    assert len(a.axes) == 3
    # AxisAssignment fields are tuples (frozen-dataclass immutability).
    assert a.residual == ()


def test_assign_axes_fields_are_tuples() -> None:
    """AxisAssignment.axes / .residual are tuples, not lists — the frozen
    dataclass's immutability is genuine (a list field would still be
    mutable in place)."""
    a = pg.assign_axes(FERMAT_PARAMS, ["c", "alpha"])
    assert isinstance(a.axes, tuple)
    assert isinstance(a.residual, tuple)


def test_assign_axes_residual_preserves_registry_order() -> None:
    """Residual params keep their original ParamSpec order, not axis order."""
    a = pg.assign_axes(FERMAT_PARAMS, ["beta", "c"])
    # axes follow the chosen order; residual follows FERMAT_PARAMS order.
    assert [s.name for s in a.axes] == ["beta", "c"]
    assert [s.name for s in a.residual] == ["alpha", "gamma"]


def test_assign_axes_rejects_duplicate_param() -> None:
    with pytest.raises(ValueError, match="two axes"):
        pg.assign_axes(FERMAT_PARAMS, ["c", "c"])
    with pytest.raises(ValueError, match="two axes"):
        pg.assign_axes(FERMAT_PARAMS, ["c", "alpha", "c"])


def test_assign_axes_rejects_bad_axis_count() -> None:
    with pytest.raises(ValueError):
        pg.assign_axes(FERMAT_PARAMS, ["c"])             # too few axes
    with pytest.raises(ValueError):
        pg.assign_axes(FERMAT_PARAMS, ["c", "alpha", "beta", "gamma"])  # too many


def test_assign_axes_rejects_unknown_param() -> None:
    with pytest.raises(ValueError, match="unknown parameter"):
        pg.assign_axes(FERMAT_PARAMS, ["c", "nonexistent"])


def test_assign_axes_rejects_too_few_params() -> None:
    one = [ParamSpec("a", "A", 0.0, 1.0, 0.5)]
    with pytest.raises(ValueError):
        pg.assign_axes(one, ["a", "a"])


def test_default_axis_names_picks_registry_prefix() -> None:
    assert pg.default_axis_names(FERMAT_PARAMS, 2) == ["c", "alpha"]
    assert pg.default_axis_names(FERMAT_PARAMS, 3) == ["c", "alpha", "beta"]
    # The default mapping is always conflict-free (distinct names).
    names = pg.default_axis_names(FERMAT_PARAMS, 3)
    assert len(names) == len(set(names))


def test_default_axis_names_rejects_bad_count() -> None:
    with pytest.raises(ValueError):
        pg.default_axis_names(FERMAT_PARAMS, 4)
    with pytest.raises(ValueError):
        pg.default_axis_names(KUMMER_PARAMS, 2)  # only 1 param available


def test_assign_axes_rejects_too_few_params_for_three_axes() -> None:
    """A genuine too-few-params rejection: a 2-param surface cannot fill a
    3-axis grid.

    The older ``test_assign_axes_rejects_too_few_params`` passes ``["a","a"]``
    and actually trips the *duplicate* guard first; this case uses three
    distinct names so the count guard is the one that fires.
    """
    two = [
        ParamSpec("a", "A", 0.0, 1.0, 0.5),
        ParamSpec("b", "B", 0.0, 1.0, 0.5),
    ]
    with pytest.raises(ValueError, match="need at least 3 parameters"):
        pg.assign_axes(two, ["a", "b", "b_extra"])


# ---------------------------------------------------------------------------
# degenerate-input guards (maximum == minimum, step <= 0, zero scene length)
# ---------------------------------------------------------------------------


def test_value_to_norm_degenerate_span_returns_zero() -> None:
    """A ParamSpec with maximum == minimum has zero span; value_to_norm must
    return 0.0 rather than raise ZeroDivisionError."""
    degenerate = ParamSpec("x", "X", 0.5, 0.5, 0.5)
    assert pg.value_to_norm(0.5, degenerate) == 0.0
    assert pg.value_to_norm(99.0, degenerate) == 0.0


def test_snap_to_step_zero_step_clamps_without_raising() -> None:
    """snap_to_step with step <= 0 must clamp (not divide by zero)."""
    zero_step = ParamSpec("x", "X", 0.0, 1.0, 0.5, step=0.0)
    assert pg.snap_to_step(0.7, zero_step) == pytest.approx(0.7)
    assert pg.snap_to_step(-5.0, zero_step) == pytest.approx(0.0)   # clamped
    assert pg.snap_to_step(9.0, zero_step) == pytest.approx(1.0)    # clamped


def test_scene_to_norm_zero_length_returns_zero() -> None:
    """A zero-length scene axis (e.g. a view resized to nothing) must map to
    norm 0.0, not raise ZeroDivisionError."""
    assert pg.scene_to_norm(5.0, 0.0) == 0.0
    assert pg.scene_to_norm(5.0, 0.0, invert=True) == 0.0


def test_tick_helpers_guard_zero_step() -> None:
    """tick_count / value_to_tick guard a degenerate step <= 0."""
    zero_step = ParamSpec("x", "X", 0.0, 1.0, 0.5, step=0.0)
    assert pg.tick_count(zero_step) == 1            # single-tick slider
    assert pg.value_to_tick(0.7, zero_step) == 0
    # A normal spec still behaves as a value<->tick round-trip.
    normal = ParamSpec("y", "Y", 0.0, 1.0, 0.5, step=0.25)
    assert pg.tick_count(normal) == 4
    assert pg.value_to_tick(0.5, normal) == 2
    assert pg.tick_to_value(2, normal) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# value formatting (shared readout format)
# ---------------------------------------------------------------------------


def test_format_value_precision_keyed_to_step() -> None:
    """format_value picks decimal precision from the step size + appends suffix."""
    coarse = ParamSpec("a", "A", 0.0, 10.0, 5.0, step=1.0, suffix=" u")
    medium = ParamSpec("b", "B", 0.0, 1.0, 0.5, step=0.1)
    fine = ParamSpec("c", "C", 0.0, 1.0, 0.5, step=0.01)
    assert pg.format_value(5.0, coarse) == "5 u"
    assert pg.format_value(0.5, medium) == "0.50"
    assert pg.format_value(0.123, fine) == "0.123"


# ---------------------------------------------------------------------------
# 3D drag-plane axis mapping
# ---------------------------------------------------------------------------


def test_plane_axes_2d_always_zero_one() -> None:
    """For a 2-axis grid the dot drives axes (0, 1) for any plane string."""
    assert pg.plane_axes("XY", 2) == (0, 1)
    assert pg.plane_axes("ignored", 2) == (0, 1)


def test_plane_axes_3d_mapping() -> None:
    """For a 3-axis grid each drag plane maps to the right axis-index pair."""
    assert pg.plane_axes("XY", 3) == (0, 1)
    assert pg.plane_axes("XZ", 3) == (0, 2)
    assert pg.plane_axes("YZ", 3) == (1, 2)


def test_plane_axes_3d_rejects_unknown_plane() -> None:
    with pytest.raises(ValueError, match="unknown drag plane"):
        pg.plane_axes("ZZ", 3)


def test_held_axis() -> None:
    """held_axis returns the index NOT driven by the dot (None for 2D)."""
    assert pg.held_axis("XY", 2) is None
    assert pg.held_axis("XY", 3) == 2   # X,Y move -> Z held
    assert pg.held_axis("XZ", 3) == 1   # X,Z move -> Y held
    assert pg.held_axis("YZ", 3) == 0   # Y,Z move -> X held
