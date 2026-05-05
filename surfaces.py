"""Mesh generators for K3 surfaces.

Each surface is a `Surface` carrying a generator function and a list of
`ParamSpec` describing its tunable parameters. Implicit surfaces are
extracted via marching cubes on a sampled scalar field.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pyvista as pv
from skimage import measure


@dataclass(frozen=True)
class ParamSpec:
    name: str        # kwarg name passed to the generator
    label: str       # human-readable label for the slider
    minimum: float
    maximum: float
    default: float
    step: float = 0.01
    suffix: str = ""
    description: str = ""


@dataclass
class Surface:
    label: str
    generate: Callable[..., pv.PolyData]
    params: list[ParamSpec] = field(default_factory=list)

    def defaults(self) -> dict[str, float]:
        return {p.name: p.default for p in self.params}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _marching_cubes_to_polydata(
    field: np.ndarray, bounds: float, level: float = 0.0
) -> pv.PolyData:
    n = field.shape[0]
    spacing = (2 * bounds / (n - 1),) * 3
    verts, faces, _normals, _ = measure.marching_cubes(field, level=level, spacing=spacing)
    verts -= bounds
    n_faces = faces.shape[0]
    pv_faces = np.empty((n_faces, 4), dtype=np.int64)
    pv_faces[:, 0] = 3
    pv_faces[:, 1:] = faces
    return pv.PolyData(verts, pv_faces.ravel())


# ---------------------------------------------------------------------------
# Fermat quartic — generalized to the Lamé / superquadric family
# ---------------------------------------------------------------------------


def fermat_quartic(
    alpha: float = 0.0,
    beta: float = 0.0,
    gamma: float = 0.0,
    c: float = 1.0,
    n: int | None = None,
) -> pv.PolyData:
    """Real affine slice of a 3-parameter family of quartic-level-set surfaces:

        x^4 + y^4 + z^4
          + alpha · (x^2 y^2 + y^2 z^2 + z^2 x^2)
          + beta  · x y z (x + y + z)
          + gamma · (x^2 + y^2 + z^2)
          = c

    At (alpha, beta, gamma, c) = (0, 0, 0, 1) this is the classical
    Fermat-style real quartic x^4 + y^4 + z^4 = 1. alpha and beta are
    independent symmetric degree-4 invariants; together with the Fermat
    power-sum they span the natural degree-4 deformation directions,
    giving a family of (generically smooth) quartic surfaces in P^3 — a
    family of K3 surfaces in the projective completion. The gamma term
    is a quadratic "carve" that lengthens the six axial arms toward the
    octahedral-arm K3 shape.

    alpha and gamma are bounded from above at zero so no slider direction
    drives the surface toward a sphere (alpha=2 collapses the equation to
    (x²+y²+z²)²=c; positive gamma inflates the central body).

    Sampling bounds are chosen adaptively from c and gamma so the six
    axial arms always fit inside the marching-cubes box even at extreme
    parameter values.
    """
    # Adaptive sampling box: along an axis (y=z=0) the surface root is at
    # x² = (-gamma + sqrt(gamma² + 4c))/2 (taking the outer root). Add a
    # 15% buffer and a floor of 2.5 for the default-parameters case.
    g_neg = max(-gamma, 0.0)
    c_pos = max(c, 0.05)
    axial_x2 = 0.5 * (g_neg + np.sqrt(g_neg * g_neg + 4.0 * c_pos))
    bounds = max(2.5, 1.15 * float(np.sqrt(axial_x2)) + 0.3)

    # Adaptive resolution: hold per-unit sample density roughly constant so
    # mesh quality doesn't degrade as the box grows. Cap at 200 to keep
    # marching cubes responsive on slider drag (single ~0.5 s budget).
    if n is None:
        n = int(np.clip(round(160 * bounds / 2.5), 150, 200))

    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z

    F = (
        X2 * X2 + Y2 * Y2 + Z2 * Z2
        + alpha * (X2 * Y2 + Y2 * Z2 + Z2 * X2)
        + beta * (X * Y * Z) * (X + Y + Z)
        + gamma * (X2 + Y2 + Z2)
        - c
    )
    # Clip wide enough to cover the corner values at the larger bounds.
    F = np.clip(F, -200.0, 200.0)
    return _marching_cubes_to_polydata(F, bounds)


FERMAT_PARAMS = [
    ParamSpec("c", "Level c", 0.1, 30.0, 1.0, 0.1,
              description="RHS of  x⁴+y⁴+z⁴ + … = c"),
    ParamSpec("alpha", "α  (mixed-square)", -10.0, 0.0, 0.0, 0.1,
              description="coeff of (x²y² + y²z² + z²x²) — sharpens cube into octahedral star"),
    ParamSpec("beta", "β  (tetrahedral)", -10.0, 10.0, 0.0, 0.1,
              description="coeff of xyz(x+y+z) — breaks octahedral to tetrahedral symmetry"),
    ParamSpec("gamma", "γ  (quadratic carve)", -15.0, 0.0, 0.0, 0.1,
              description="coeff of (x²+y²+z²) — carves central body, extends axial arms"),
]


# ---------------------------------------------------------------------------
# Kummer surface
# ---------------------------------------------------------------------------


def kummer_surface(mu_squared: float = 1.3, n: int = 170, bounds: float = 2.6) -> pv.PolyData:
    """Kummer quartic in standard tetrahedral form (Hudson; MathWorld).

        (x^2 + y^2 + z^2 - mu^2)^2  -  lambda * p*q*r*s  =  0
        lambda(mu) = (3*mu^2 - 1) / (3 - mu^2)

    mu^2 = 3 is a pole. mu^2 ∈ {1/3, 2/3, 1} are degenerate cases.
    The classic 16-nodal Kummer regime is 1 < mu^2 < 3.
    """
    if abs(mu_squared - 3.0) < 1e-6:
        raise ValueError("mu^2 = 3 is a pole of lambda(mu); choose another value.")
    lam = (3.0 * mu_squared - 1.0) / (3.0 - mu_squared)

    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    s2 = np.sqrt(2.0)
    p_ = 1.0 - Z - s2 * X
    q_ = 1.0 - Z + s2 * X
    r_ = 1.0 + Z + s2 * Y
    s_ = 1.0 + Z - s2 * Y

    F = (X * X + Y * Y + Z * Z - mu_squared) ** 2 - lam * p_ * q_ * r_ * s_
    F = np.clip(F, -50.0, 50.0)
    return _marching_cubes_to_polydata(F, bounds)


KUMMER_PARAMS = [
    ParamSpec("mu_squared", "μ²", 0.05, 2.95, 1.3, 0.05,
              description="μ²=1/3, 2/3, 1 are degenerate · μ²=3 is a pole"),
]


# ---------------------------------------------------------------------------
# Registry — keys appear in the GUI dropdowns
# ---------------------------------------------------------------------------


VARIETIES: dict[str, dict[str, Surface]] = {
    "K3 surface": {
        "Fermat quartic": Surface("Fermat quartic", fermat_quartic, FERMAT_PARAMS),
        "Kummer surface": Surface("Kummer surface", kummer_surface, KUMMER_PARAMS),
    },
}
