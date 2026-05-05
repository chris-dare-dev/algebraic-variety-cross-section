"""Tests for _grid_to_polydata and _concat_polydata helpers in surfaces.py.

No Qt or GUI code is required.
"""

from __future__ import annotations

import sys
import os

import numpy as np
import pyvista as pv
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from surfaces import _grid_to_polydata, _concat_polydata


# ---------------------------------------------------------------------------
# _grid_to_polydata
# ---------------------------------------------------------------------------

def test_grid_to_polydata_2x2_shape():
    """A 2×2 flat grid should produce 4 vertices and 2 triangles."""
    X = np.array([[0.0, 1.0], [0.0, 1.0]])
    Y = np.array([[0.0, 0.0], [1.0, 1.0]])
    Z = np.zeros((2, 2))
    mesh = _grid_to_polydata(X, Y, Z)
    assert mesh.n_points == 4, f"Expected 4 vertices, got {mesh.n_points}"
    assert mesh.n_cells == 2, f"Expected 2 triangles, got {mesh.n_cells}"


def test_grid_to_polydata_3x3_shape():
    """A 3×3 grid should produce 9 vertices and 8 triangles (=2*(3-1)*(3-1))."""
    x = np.linspace(0.0, 1.0, 3)
    y = np.linspace(0.0, 1.0, 3)
    X, Y = np.meshgrid(x, y, indexing="ij")
    Z = np.zeros((3, 3))
    mesh = _grid_to_polydata(X, Y, Z)
    assert mesh.n_points == 9, f"Expected 9 vertices, got {mesh.n_points}"
    assert mesh.n_cells == 8, f"Expected 8 triangles (2*(3-1)*(3-1)), got {mesh.n_cells}"


def test_grid_to_polydata_wrong_shape_raises():
    """Mismatched X/Y/Z shapes should raise ValueError."""
    X = np.zeros((2, 2))
    Y = np.zeros((2, 3))
    Z = np.zeros((2, 2))
    with pytest.raises(ValueError):
        _grid_to_polydata(X, Y, Z)


def test_grid_to_polydata_1d_raises():
    """1D arrays should raise ValueError."""
    X = np.zeros(4)
    Y = np.zeros(4)
    Z = np.zeros(4)
    with pytest.raises(ValueError):
        _grid_to_polydata(X, Y, Z)


# ---------------------------------------------------------------------------
# _concat_polydata
# ---------------------------------------------------------------------------

def _make_2x2_grid(x_offset: float = 0.0) -> pv.PolyData:
    """Return a 2×2 flat grid PolyData, optionally shifted in x."""
    X = np.array([[0.0, 1.0], [0.0, 1.0]]) + x_offset
    Y = np.array([[0.0, 0.0], [1.0, 1.0]])
    Z = np.zeros((2, 2))
    return _grid_to_polydata(X, Y, Z)


def test_concat_polydata_empty_list():
    """_concat_polydata([]) should return an empty PolyData."""
    result = _concat_polydata([])
    assert isinstance(result, pv.PolyData)
    assert result.n_points == 0
    assert result.n_cells == 0


def test_concat_polydata_two_grids_vertex_count():
    """Two disjoint 2×2 grids should concatenate to 8 vertices."""
    m1 = _make_2x2_grid(x_offset=0.0)
    m2 = _make_2x2_grid(x_offset=10.0)
    result = _concat_polydata([m1, m2])
    assert result.n_points == 8, f"Expected 8 vertices, got {result.n_points}"


def test_concat_polydata_two_grids_face_count():
    """Two disjoint 2×2 grids should concatenate to 4 triangles."""
    m1 = _make_2x2_grid(x_offset=0.0)
    m2 = _make_2x2_grid(x_offset=10.0)
    result = _concat_polydata([m1, m2])
    assert result.n_cells == 4, f"Expected 4 triangles, got {result.n_cells}"


def test_concat_polydata_face_indices_offset():
    """The second mesh's face vertex indices should all be >= 4 (correctly offset)."""
    m1 = _make_2x2_grid(x_offset=0.0)
    m2 = _make_2x2_grid(x_offset=10.0)
    result = _concat_polydata([m1, m2])
    # faces array layout: [3, i0, i1, i2, 3, j0, j1, j2, ...]
    faces = result.faces.reshape(-1, 4)  # shape (4, 4): count + 3 indices per face
    # The first two faces belong to m1 (indices 0-3), the last two to m2 (indices >=4)
    second_mesh_faces = faces[2:]
    vertex_indices = second_mesh_faces[:, 1:]  # columns 1,2,3 are the vertex indices
    assert vertex_indices.min() >= 4, (
        f"Second mesh face indices should all be >= 4, got min={vertex_indices.min()}"
    )


def test_concat_polydata_single_mesh():
    """Concatenating a single mesh should return an equivalent PolyData."""
    m = _make_2x2_grid()
    result = _concat_polydata([m])
    assert result.n_points == m.n_points
    assert result.n_cells == m.n_cells
