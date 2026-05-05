"""Tests for the six surface mesh generators in surfaces.py.

No Qt or GUI code is required — all generators are pure NumPy/scikit-image.
"""

from __future__ import annotations

import pytest
import sys
import os

# Ensure the project root is importable when running tests from any cwd.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from surfaces import (
    fermat_quartic,
    kummer_surface,
    enriques_figure_1,
    enriques_figure_2,
    enriques_figure_3,
    enriques_figure_4,
    calabi_yau_quintic,
    calabi_yau_cubic,
    calabi_yau_asymmetric,
    calabi_yau_dwork,
    fano_klein_cubic,
    fano_segre_cubic,
    fano_two_quadrics,
    fano_sextic_double_solid,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _assert_nonempty(mesh, bounds: float = 10.0) -> None:
    """Assert mesh has vertices and faces, and that all vertices are within
    [-bounds, +bounds] on each axis."""
    assert mesh.n_points > 0, "Mesh has no vertices"
    assert mesh.n_cells > 0, "Mesh has no faces"
    pts = mesh.points
    assert pts[:, 0].min() >= -bounds and pts[:, 0].max() <= bounds, \
        f"x vertices out of [-{bounds}, {bounds}]"
    assert pts[:, 1].min() >= -bounds and pts[:, 1].max() <= bounds, \
        f"y vertices out of [-{bounds}, {bounds}]"
    assert pts[:, 2].min() >= -bounds and pts[:, 2].max() <= bounds, \
        f"z vertices out of [-{bounds}, {bounds}]"


# ---------------------------------------------------------------------------
# Default-parameter smoke tests
# ---------------------------------------------------------------------------

def test_fermat_quartic_defaults():
    mesh = fermat_quartic()
    _assert_nonempty(mesh)


def test_kummer_surface_defaults():
    mesh = kummer_surface()
    _assert_nonempty(mesh)


def test_enriques_figure_1_defaults():
    mesh = enriques_figure_1()
    _assert_nonempty(mesh)


def test_enriques_figure_2_defaults():
    mesh = enriques_figure_2()
    _assert_nonempty(mesh)


def test_enriques_figure_3_defaults():
    mesh = enriques_figure_3()
    _assert_nonempty(mesh)


def test_enriques_figure_4_defaults():
    mesh = enriques_figure_4()
    _assert_nonempty(mesh)


# ---------------------------------------------------------------------------
# ValueError for invalid kummer_surface parameters
# ---------------------------------------------------------------------------

def test_kummer_surface_pole_raises():
    """mu_squared = 3 is a pole of lambda(mu); must raise ValueError."""
    with pytest.raises(ValueError, match="pole"):
        kummer_surface(mu_squared=3.0)


def test_kummer_surface_no_zero_set_raises():
    """mu_squared <= 1/3 gives lambda <= 0; no real zero set exists."""
    with pytest.raises(ValueError, match="no zero set"):
        kummer_surface(mu_squared=0.2)


# ---------------------------------------------------------------------------
# fermat_quartic at slider extremes
# ---------------------------------------------------------------------------

def test_fermat_quartic_c_low():
    """c = 0.1 (slider minimum) should still produce a non-empty mesh."""
    mesh = fermat_quartic(c=0.1)
    _assert_nonempty(mesh)


def test_fermat_quartic_c_high():
    """c = 30.0 (slider maximum) should still produce a non-empty mesh."""
    mesh = fermat_quartic(c=30.0)
    _assert_nonempty(mesh)


# ---------------------------------------------------------------------------
# Calabi–Yau 3-fold smoke tests
# ---------------------------------------------------------------------------

def test_calabi_yau_quintic_defaults():
    """Default parameters should produce a non-empty mesh."""
    mesh = calabi_yau_quintic()
    assert mesh.n_points > 0, "calabi_yau_quintic: no vertices"
    assert mesh.n_cells > 0, "calabi_yau_quintic: no faces"


def test_calabi_yau_cubic_defaults():
    """Default parameters should produce a non-empty mesh."""
    mesh = calabi_yau_cubic()
    assert mesh.n_points > 0, "calabi_yau_cubic: no vertices"
    assert mesh.n_cells > 0, "calabi_yau_cubic: no faces"


def test_calabi_yau_asymmetric_defaults():
    """Default parameters should produce a non-empty mesh."""
    mesh = calabi_yau_asymmetric()
    assert mesh.n_points > 0, "calabi_yau_asymmetric: no vertices"
    assert mesh.n_cells > 0, "calabi_yau_asymmetric: no faces"


def test_calabi_yau_dwork_defaults():
    """Default parameters (ψ=0.5) should produce a non-empty mesh."""
    mesh = calabi_yau_dwork()
    assert mesh.n_points > 0, "calabi_yau_dwork: no vertices"
    assert mesh.n_cells > 0, "calabi_yau_dwork: no faces"


def test_calabi_yau_dwork_psi_zero():
    """ψ=0 (Fermat quintic shadow) should produce a non-empty mesh."""
    mesh = calabi_yau_dwork(psi=0.0)
    assert mesh.n_points > 0, "calabi_yau_dwork(psi=0): no vertices"
    assert mesh.n_cells > 0, "calabi_yau_dwork(psi=0): no faces"


def test_calabi_yau_dwork_conifold_warns():
    """ψ≈1 (real conifold point) should emit a RuntimeWarning."""
    with pytest.warns(RuntimeWarning, match="conifold"):
        calabi_yau_dwork(psi=1.0)


# ---------------------------------------------------------------------------
# Fano 3-fold smoke tests
# ---------------------------------------------------------------------------

def test_fano_klein_cubic_default():
    """Default parameters should produce a non-empty mesh."""
    mesh = fano_klein_cubic()
    assert mesh.n_points > 0, "fano_klein_cubic: no vertices"
    assert mesh.n_cells > 0, "fano_klein_cubic: no faces"


def test_fano_segre_cubic_default():
    """Default parameters should produce a non-empty mesh."""
    mesh = fano_segre_cubic()
    assert mesh.n_points > 0, "fano_segre_cubic: no vertices"
    assert mesh.n_cells > 0, "fano_segre_cubic: no faces"


def test_fano_two_quadrics_default():
    """Default parameters should produce a non-empty mesh."""
    mesh = fano_two_quadrics()
    assert mesh.n_points > 0, "fano_two_quadrics: no vertices"
    assert mesh.n_cells > 0, "fano_two_quadrics: no faces"


def test_fano_sextic_double_solid_default():
    """Default parameters should produce a non-empty mesh."""
    mesh = fano_sextic_double_solid()
    assert mesh.n_points > 0, "fano_sextic_double_solid: no vertices"
    assert mesh.n_cells > 0, "fano_sextic_double_solid: no faces"


def test_fano_klein_cubic_z0_zero():
    """z₀=0.0 gives a special cubic-surface slice — should not crash."""
    mesh = fano_klein_cubic(z0=0.0)
    assert mesh.n_points > 0, "fano_klein_cubic(z0=0): no vertices"
    assert mesh.n_cells > 0, "fano_klein_cubic(z0=0): no faces"


def test_fano_two_quadrics_real_empty():
    """p=1.0, q=0.5, mu=0.5 forces Q₁ ≥ 0.25 everywhere; no real tube exists."""
    with pytest.raises(ValueError):
        fano_two_quadrics(p=1.0, q=0.5, mu=0.5)


def test_fano_sextic_double_solid_two_sheets():
    """The sextic double solid has two sheets: verify both positive and negative z
    are spanned by the mesh, confirming both sheets z = ±√(x⁶+y⁶+t⁶+1) are present."""
    mesh = fano_sextic_double_solid()
    z_coords = mesh.points[:, 2]
    assert z_coords.min() < 0, "Missing negative-z sheet"
    assert z_coords.max() > 0, "Missing positive-z sheet"
