"""Tests for the ParametersPanel slider tick ↔ value conversion.

We test the underlying math directly — the formulas are:
  tick  = round((value - spec.minimum) / spec.step)
  value = spec.minimum + tick * spec.step

These are the same formulas used by ParametersPanel._value_to_tick and
_slider_to_value.  Testing them here avoids instantiating a QApplication.
"""

from __future__ import annotations

import math
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from surfaces import (
    FERMAT_PARAMS,
    KUMMER_PARAMS,
    ENRIQUES_FIGURE_1_PARAMS,
    ENRIQUES_FIGURE_2_PARAMS,
    ENRIQUES_FIGURE_3_PARAMS,
    ENRIQUES_FIGURE_4_PARAMS,
    CALABI_YAU_QUINTIC_PARAMS,
    CALABI_YAU_CUBIC_PARAMS,
    CALABI_YAU_ASYMMETRIC_PARAMS,
    CALABI_YAU_DWORK_PARAMS,
    FANO_KLEIN_CUBIC_PARAMS,
    FANO_SEGRE_CUBIC_PARAMS,
    FANO_TWO_QUADRICS_PARAMS,
    FANO_SEXTIC_DOUBLE_SOLID_PARAMS,
    ParamSpec,
)


# ---------------------------------------------------------------------------
# Helpers mirroring ParametersPanel's static methods
# ---------------------------------------------------------------------------

def value_to_tick(value: float, spec: ParamSpec) -> int:
    return int(round((value - spec.minimum) / spec.step))


def tick_to_value(tick: int, spec: ParamSpec) -> float:
    return spec.minimum + tick * spec.step


# ---------------------------------------------------------------------------
# Round-trip: default → tick → value should be within step/2 of default
# ---------------------------------------------------------------------------

ALL_PARAM_SPECS = (
    FERMAT_PARAMS
    + KUMMER_PARAMS
    + ENRIQUES_FIGURE_1_PARAMS
    + ENRIQUES_FIGURE_2_PARAMS
    + ENRIQUES_FIGURE_3_PARAMS
    + ENRIQUES_FIGURE_4_PARAMS
    + CALABI_YAU_QUINTIC_PARAMS
    + CALABI_YAU_CUBIC_PARAMS
    + CALABI_YAU_ASYMMETRIC_PARAMS
    + CALABI_YAU_DWORK_PARAMS
    + FANO_KLEIN_CUBIC_PARAMS
    + FANO_SEGRE_CUBIC_PARAMS
    + FANO_TWO_QUADRICS_PARAMS
    + FANO_SEXTIC_DOUBLE_SOLID_PARAMS
)


@pytest.mark.parametrize("spec", ALL_PARAM_SPECS, ids=lambda s: s.name)
def test_default_round_trips(spec: ParamSpec):
    """Default value survives the tick round-trip within half a step."""
    tick = value_to_tick(spec.default, spec)
    recovered = tick_to_value(tick, spec)
    assert abs(recovered - spec.default) <= spec.step / 2 + 1e-9, (
        f"{spec.name}: default={spec.default}, tick={tick}, "
        f"recovered={recovered}, tolerance={spec.step / 2}"
    )


@pytest.mark.parametrize("spec", ALL_PARAM_SPECS, ids=lambda s: s.name)
def test_minimum_tick_is_zero(spec: ParamSpec):
    """The minimum value should always map to tick 0."""
    tick = value_to_tick(spec.minimum, spec)
    assert tick == 0, f"{spec.name}: minimum={spec.minimum} → tick={tick}, expected 0"


@pytest.mark.parametrize("spec", ALL_PARAM_SPECS, ids=lambda s: s.name)
def test_maximum_tick_is_positive(spec: ParamSpec):
    """The maximum value should map to a positive tick."""
    tick = value_to_tick(spec.maximum, spec)
    assert tick > 0, f"{spec.name}: maximum={spec.maximum} → tick={tick}"
    # And it should be within 1 of the expected value (rounding at extremes)
    expected_ticks = round((spec.maximum - spec.minimum) / spec.step)
    assert abs(tick - expected_ticks) <= 1, (
        f"{spec.name}: expected {expected_ticks} ticks, got {tick}"
    )


@pytest.mark.parametrize("spec", ALL_PARAM_SPECS, ids=lambda s: s.name)
def test_default_within_range(spec: ParamSpec):
    """Default must be within [minimum, maximum]."""
    assert spec.minimum <= spec.default <= spec.maximum, (
        f"{spec.name}: default={spec.default} not in "
        f"[{spec.minimum}, {spec.maximum}]"
    )
