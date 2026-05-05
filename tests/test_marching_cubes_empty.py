"""Tests that _marching_cubes_to_polydata raises ValueError when the field has
no zero crossing, and that kummer_surface propagates that as a ValueError.

No Qt or GUI code is required.
"""

from __future__ import annotations

import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from surfaces import _marching_cubes_to_polydata, kummer_surface


def test_all_positive_field_raises():
    """A field with no zero crossing (all-positive) must raise ValueError."""
    field = np.ones((10, 10, 10), dtype=float)
    with pytest.raises(ValueError, match="No real zero set"):
        _marching_cubes_to_polydata(field, bounds=1.0)


def test_all_negative_field_raises():
    """A field with no zero crossing (all-negative) must raise ValueError."""
    field = -np.ones((10, 10, 10), dtype=float)
    with pytest.raises(ValueError, match="No real zero set"):
        _marching_cubes_to_polydata(field, bounds=1.0)


def test_kummer_surface_no_zero_set_raises():
    """kummer_surface with mu_squared=0.2 (≤1/3) has no real zero set."""
    with pytest.raises(ValueError, match="no zero set"):
        kummer_surface(mu_squared=0.2)


def test_kummer_surface_below_one_third_boundary():
    """mu_squared = 1/3 is exactly the boundary — must also raise."""
    with pytest.raises(ValueError):
        kummer_surface(mu_squared=1.0 / 3.0)


def test_field_with_zero_crossing_does_not_raise():
    """A field that crosses zero should NOT raise ValueError."""
    # Simple plane: F[i,j,k] = i - n//2, zero crossing at the midplane
    n = 10
    field = np.zeros((n, n, n), dtype=float)
    for i in range(n):
        field[i, :, :] = i - n // 2  # crosses zero between i=4 and i=5
    # Should complete without raising
    mesh = _marching_cubes_to_polydata(field, bounds=1.0)
    assert mesh.n_points > 0
