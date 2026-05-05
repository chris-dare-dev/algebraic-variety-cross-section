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
    n: int = 160,
) -> pv.PolyData:
    """Real affine slice of a 3-parameter family of quartic-level-set surfaces:

        x^4 + y^4 + z^4
          + alpha · (x^2 y^2 + y^2 z^2 + z^2 x^2)
          + beta  · x y z (x + y + z)
          + gamma · (x^2 + y^2 + z^2)
          = c

    At (alpha, beta, gamma, c) = (0, 0, 0, 1) this is the classical
    Fermat-style real quartic x^4 + y^4 + z^4 = 1. The two degree-4
    perturbation terms (alpha, beta) are independent symmetric quartic
    invariants; together with the Fermat power-sum they span the natural
    degree-4 deformation directions, giving a family of (generically smooth)
    quartic surfaces in P^3 — a family of K3 surfaces in the projective
    completion. The gamma term adds a quadratic "deflation" knob that carves
    the central body out, lengthening the six axial arms toward an
    octahedral-arm K3 shape.

    All three perturbation sliders are restricted to non-positive values
    (alpha, gamma) or symmetric (beta) ranges so that no slider direction
    drives the surface toward a sphere:
      - alpha > 0 pushes toward (x^2+y^2+z^2)^2 = c (sphere at alpha=2)
      - gamma > 0 inflates the central body toward sphericity
    Both are bounded at zero from above for that reason.
    """
    # Generous box: with strong negative alpha/gamma the six axial arms can
    # reach close to ±2. 2.5 captures that comfortably.
    bounds = 2.5

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
    # Clip range scaled to the wider box; x^4 alone reaches ~39 at the corners.
    F = np.clip(F, -50.0, 50.0)
    return _marching_cubes_to_polydata(F, bounds)


FERMAT_PARAMS = [
    ParamSpec("c", "Level c", 0.1, 5.0, 1.0, 0.05,
              description="RHS of  x⁴+y⁴+z⁴ + … = c"),
    ParamSpec("alpha", "α  (mixed-square)", -3.0, 0.0, 0.0, 0.05,
              description="coeff of (x²y² + y²z² + z²x²) — sharpens cube into octahedral star"),
    ParamSpec("beta", "β  (tetrahedral)", -3.0, 3.0, 0.0, 0.05,
              description="coeff of xyz(x+y+z) — breaks octahedral to tetrahedral symmetry"),
    ParamSpec("gamma", "γ  (quadratic carve)", -5.0, 0.0, 0.0, 0.05,
              description="coeff of (x²+y²+z²) — carves central body, extends six axial arms"),
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
