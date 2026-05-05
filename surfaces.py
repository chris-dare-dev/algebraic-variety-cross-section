"""Mesh generators for K3 surfaces.

Each generator returns a pyvista.PolyData mesh ready to add to a plotter.
Implicit surfaces are extracted via marching cubes on a sampled scalar field.
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
from skimage import measure


def _marching_cubes_to_polydata(
    field: np.ndarray, bounds: float, level: float = 0.0
) -> pv.PolyData:
    n = field.shape[0]
    spacing = (2 * bounds / (n - 1),) * 3
    verts, faces, _normals, _ = measure.marching_cubes(field, level=level, spacing=spacing)
    verts -= bounds  # recenter to [-bounds, bounds]^3
    # PyVista face format: [3, i0, i1, i2, 3, i0, i1, i2, ...]
    n_faces = faces.shape[0]
    pv_faces = np.empty((n_faces, 4), dtype=np.int64)
    pv_faces[:, 0] = 3
    pv_faces[:, 1:] = faces
    return pv.PolyData(verts, pv_faces.ravel())


def fermat_quartic(n: int = 150, bounds: float = 1.25) -> pv.PolyData:
    """Real Fermat-style quartic: x^4 + y^4 + z^4 = 1.

    The genuine projective Fermat quartic x^4+y^4+z^4+w^4=0 has empty real locus,
    so we plot its standard real shadow, the unit degree-4 superquadric.
    """
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    F = X**4 + Y**4 + Z**4 - 1.0
    F = np.clip(F, -10.0, 10.0)
    return _marching_cubes_to_polydata(F, bounds)


def kummer_surface(mu_squared: float = 1.3, n: int = 180, bounds: float = 2.6) -> pv.PolyData:
    """Kummer quartic in standard tetrahedral form (Hudson; MathWorld).

        (x^2 + y^2 + z^2 - mu^2)^2  -  lambda * p*q*r*s  =  0

    where p, q, r, s are the four tetrahedral planes and
    lambda(mu) = (3*mu^2 - 1) / (3 - mu^2).

    mu^2 = 3 is a pole; mu^2 = 1 and 1/3 are reducible/degenerate cases.
    Recommended demo value: mu_squared = 1.3 (16 real nodes, classic shape).
    """
    if abs(mu_squared - 3.0) < 1e-6:
        raise ValueError("mu^2 = 3 is a pole of lambda(mu); choose another value.")
    lam = (3.0 * mu_squared - 1.0) / (3.0 - mu_squared)

    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    s2 = np.sqrt(2.0)
    p = 1.0 - Z - s2 * X
    q = 1.0 - Z + s2 * X
    r = 1.0 + Z + s2 * Y
    s = 1.0 + Z - s2 * Y

    F = (X * X + Y * Y + Z * Z - mu_squared) ** 2 - lam * p * q * r * s
    F = np.clip(F, -50.0, 50.0)
    return _marching_cubes_to_polydata(F, bounds)


# Registry of available surfaces. Keys appear in the GUI dropdowns.
VARIETIES = {
    "K3 surface": {
        "Fermat quartic": fermat_quartic,
        "Kummer surface": kummer_surface,
    },
}
