"""AVC K3 variety generators.

Per restructure-feature-subpackages-2026q2-r2 Batch 7: extracted from surfaces.py.

Each generator function returns a ``pv.PolyData`` or raises ``ValueError``.
Generator imports come from varieties._kernels (Numba field kernels) and
varieties._marching (pipeline helpers).  PARAM lists carry the slider metadata
the GUI consumes via the VARIETIES registry (now in varieties.registry).
"""

from __future__ import annotations

import warnings

import numpy as np
import pyvista as pv

from varieties.types import ParamSpec
from varieties._marching import (
    _marching_cubes_to_polydata,
    _grid_to_polydata,
    _concat_polydata,
    _hanson_cross_section,
)
from varieties._kernels import (
    _fermat_field_kernel,
    _kummer_field_kernel,
    _enriques_fig1_field_kernel,
    _enriques_fig2_field_kernel,
    _enriques_fig3_field_kernel,
    _enriques_fig4_field_kernel,
    _dwork_field_kernel,
    _klein_cubic_field_kernel,
    _segre_cubic_field_kernel,
    _two_quadrics_field_kernel,
    _sextic_double_solid_field_kernel,
)


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
    Fermat-style real quartic x^4 + y^4 + z^4 = 1.  alpha and beta are
    independent symmetric degree-4 invariants; together with the Fermat
    power-sum they span the natural degree-4 deformation directions.

    **K3 connection (projective completion only).**  The *homogeneous
    quartic part* x^4 + y^4 + z^4 + alpha·(x^2 y^2 + y^2 z^2 + z^2 x^2)
    + beta·xyz(x+y+z) defines a quartic surface in P^3 that is generically
    a K3 surface in the sense of algebraic geometry.  The gamma·(x^2+y^2+z^2)
    term is a non-projective degree-2 perturbation; it modifies the affine
    real slice but not the projective completion's K3 type.  The surface
    displayed here is the *real affine zero set* of the full equation, not
    the projective K3 itself.

    Compactness constraints:
    - alpha >= -1 is required to keep the leading quartic form positive
      definite along the body diagonal (alpha < -1 makes the surface
      non-compact).
    - |beta| <= 3 keeps the tetrahedral perturbation from opening
      non-compact channels.

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
    # mesh quality doesn't degrade as the box grows. Cap at 220 to keep
    # marching cubes responsive on slider drag while producing a smooth
    # triangulation.  realtime-variety-render-e1-s3 (CAND-13): the cap was
    # lowered 260 -> 220 — the Fermat quartic field is smooth with no
    # near-singularities, so n=220 (~10.6M voxels) is topologically identical
    # to n=260 (~17.6M) at viewport zoom; the higher resolution is reserved
    # for the screenshot/export path where latency does not matter.
    if n is None:
        n = int(np.clip(round(220 * bounds / 2.5), 200, 220))

    # realtime-variety-render-e5 (CAND-2): the field is evaluated by a Numba
    # JIT kernel (`_fermat_field_kernel`) writing directly into `F` — it
    # replaces the NumPy meshgrid + X2/Y2/Z2 + broadcast-polynomial + np.clip
    # block, which allocated ~half a dozen n^3 temporaries.  `n` is already
    # int-coerced above (AI-8); the kernel only sees the float `g` axis and the
    # float params.  The clip (±200) is folded into the kernel.
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _fermat_field_kernel(g, alpha, beta, gamma, c, F)
    return _marching_cubes_to_polydata(F, bounds)


FERMAT_PARAMS = [
    ParamSpec("c", "Level c", 0.1, 30.0, 1.0, 0.1,
              description="RHS of  x⁴+y⁴+z⁴ + … = c"),
    ParamSpec("alpha", "α  (mixed-square)", -1.0, 0.0, 0.0, 0.05,
              description="coeff of (x²y² + y²z² + z²x²) — alpha < -1 makes surface non-compact"),
    ParamSpec("beta", "β  (tetrahedral)", -3.0, 3.0, 0.0, 0.1,
              description="coeff of xyz(x+y+z) — breaks octahedral to tetrahedral symmetry; |β|>3 opens non-compact channels"),
    ParamSpec("gamma", "γ  (quadratic carve)", -15.0, 0.0, 0.0, 0.1,
              description="coeff of (x²+y²+z²) — carves central body, extends axial arms"),
]


# ---------------------------------------------------------------------------
# Kummer surface
# ---------------------------------------------------------------------------


def kummer_surface(mu_squared: float = 1.3, n: int = 240) -> pv.PolyData:
    """Kummer quartic in standard tetrahedral form (Hudson; MathWorld).

        (x^2 + y^2 + z^2 - mu^2)^2  -  lambda * p*q*r*s  =  0
        lambda(mu) = (3*mu^2 - 1) / (3 - mu^2)

    mu^2 = 3 is a pole.  mu^2 <= 1/3 gives lambda <= 0, meaning the
    biquadratic dominates everywhere and there is no real zero set.
    The classic 16-nodal Kummer regime is 1 < mu^2 < 3.

    Raises ValueError for mu^2 = 3 (pole) or mu^2 <= 1/3 (no zero set).
    The sampling bounds are chosen adaptively from mu_squared so the
    surface fits comfortably inside the marching-cubes box.
    """
    if abs(mu_squared - 3.0) < 1e-6:
        raise ValueError("mu^2 = 3 is a pole of lambda(mu); choose another value.")
    if mu_squared <= 1.0 / 3.0:
        raise ValueError(
            f"mu² must be > 1/3 (lambda=0 at mu²=1/3, no zero set); got {mu_squared:.3f}"
        )
    lam = (3.0 * mu_squared - 1.0) / (3.0 - mu_squared)

    # Adaptive bounds: the surface grows as mu_squared increases beyond 1.
    bounds = max(2.6, 2.6 + 2.0 * (mu_squared - 1.0))
    bounds = min(bounds, 6.0)

    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_kummer_field_kernel` (see the e5b kernel block in the
    # Helpers section).  λ and √2 are scalar pre-computes that stay here in
    # the generator -- the kernel only sees the float `g` axis + float
    # scalars.  Pole and no-zero-set ValueErrors above fire BEFORE the
    # kernel runs (AI-14 preserved).
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    sqrt2 = np.sqrt(2.0)
    F = np.empty((n, n, n), dtype=np.float64)
    _kummer_field_kernel(g, mu_squared, lam, sqrt2, F)
    return _marching_cubes_to_polydata(F, bounds)


KUMMER_PARAMS = [
    ParamSpec("mu_squared", "μ²", 0.40, 2.95, 1.3, 0.05,
              description="μ²≤1/3 gives no zero set · μ²=3 is a pole · classic 16-node regime: 1<μ²<3"),
]


# ---------------------------------------------------------------------------
# Enriques surfaces — four representative figures
#
# Background: the Enriques surface is a smooth complex projective surface with
# 2K_X = 0 and Euler number 12. Its canonical embeddings live in P^5 and have
# empty real locus, so — just like the Fermat K3 — visualizing requires
# plotting the *real shadows of degree-6 surfaces in P^3 that are birational to
# Enriques surfaces*. The "Enriques sextic" family below is exactly Enriques'
# original 1896 construction.
# ---------------------------------------------------------------------------


