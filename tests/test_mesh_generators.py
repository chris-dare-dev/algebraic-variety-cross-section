"""Tests for the surface mesh generators in surfaces.py.

No Qt or GUI code is required — the generators are pure NumPy field
evaluation plus VTK Flying Edges isocontouring (no on-screen rendering).
"""

from __future__ import annotations

import numpy as np
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


def _assert_consistent_winding(mesh) -> None:
    """Assert the mesh is an all-triangle surface with globally consistent
    triangle winding.

    Regression guard for realtime-variety-render-e6 (VTK Flying Edges). The
    isocontour swap originally ran a ``clean()`` pass, which merged
    near-coincident vertices, collapsed incident triangles into zero-area
    degenerate cells (breaking the all-triangle invariant), and split the
    mesh into orientation islands — half the surface shaded inside-out.

    A consistently wound surface traverses every directed edge ``(a, b)`` at
    most once: an interior edge is shared by exactly two triangles that walk
    it in opposite directions, so ``(a, b)`` and ``(b, a)`` each occur once.
    A duplicated directed edge means two adjacent triangles wind the same
    way — i.e. an inside-out facet.
    """
    assert mesh.is_all_triangles, (
        "Flying Edges output must stay all-triangle — a clean()/degenerate-"
        "cell pass would break this and the normal-orientation walk"
    )
    faces = mesh.faces.reshape(-1, 4)[:, 1:]
    big = np.int64(mesh.n_points + 1)
    directed = np.concatenate([
        faces[:, 0] * big + faces[:, 1],
        faces[:, 1] * big + faces[:, 2],
        faces[:, 2] * big + faces[:, 0],
    ])
    _, counts = np.unique(directed, return_counts=True)
    assert counts.max() == 1, (
        f"{(counts > 1).sum()} directed edge(s) traversed more than once — "
        "triangle winding is inconsistent, shading would be inside-out"
    )


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
# Flying Edges winding / orientation regression guards (e6)
# ---------------------------------------------------------------------------

def test_enriques_figure_1_consistent_winding():
    """The Enriques canonical sextic is the e6 regression case: a clean()
    pass on the Flying Edges output split it into orientation islands."""
    _assert_consistent_winding(enriques_figure_1())


def test_kummer_surface_consistent_winding():
    """Kummer (16 nodes, high curvature) — Flying Edges winding guard."""
    _assert_consistent_winding(kummer_surface())


def test_fermat_quartic_consistent_winding():
    """Fermat quartic — Flying Edges winding guard."""
    _assert_consistent_winding(fermat_quartic())


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


def test_fano_two_quadrics_low_eps_warns():
    """eps < 0.08 is near the voxel-resolution limit; must emit a RuntimeWarning."""
    with pytest.warns(RuntimeWarning, match="voxel resolution limit"):
        fano_two_quadrics(eps=0.07)


def test_fano_sextic_double_solid_two_sheets():
    """The sextic double solid is a closed compact surface — verify the mesh
    spans both positive and negative z (the upper and lower domes joined at the
    sextic branch curve x⁶+y⁶+α·x²y²(x²+y²) = R⁶)."""
    mesh = fano_sextic_double_solid()
    z_coords = mesh.points[:, 2]
    assert z_coords.min() < 0, "Missing negative-z sheet (lower dome)"
    assert z_coords.max() > 0, "Missing positive-z sheet (upper dome)"


def test_fano_sextic_double_solid_alpha_zero_is_octahedral():
    """At α=0 the equator is the Fermat sextic x⁶+y⁶=R⁶, which has 4-fold
    rotational symmetry. Spot-check by verifying the mesh extent is symmetric
    in x and y to within sampling noise."""
    mesh = fano_sextic_double_solid(R=1.2, alpha=0.0)
    pts = mesh.points
    x_extent = pts[:, 0].max() - pts[:, 0].min()
    y_extent = pts[:, 1].max() - pts[:, 1].min()
    assert abs(x_extent - y_extent) < 0.05, (
        f"α=0 should give x↔y symmetric extents; got x_extent={x_extent:.3f}, "
        f"y_extent={y_extent:.3f}"
    )
