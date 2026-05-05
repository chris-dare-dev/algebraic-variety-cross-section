"""Mesh generators for K3 and Enriques surfaces.

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
    field: np.ndarray,
    bounds: float,
    level: float = 0.0,
    smooth_iter: int = 20,
) -> pv.PolyData:
    """Extract the level set of *field* as a smooth PolyData.

    Pipeline:
      1. ``skimage.measure.marching_cubes`` on the sampled scalar field. We
         keep the analytic gradient-based normals it returns — these are
         derived from the implicit-function gradient and are much smoother
         than face-averaged mesh normals, especially near regions of high
         curvature.
      2. ``clean()`` to merge duplicate vertices that marching cubes
         occasionally produces at cell boundaries.
      3. ``smooth_taubin()`` for *volume-preserving* smoothing. Plain
         Laplacian smoothing shrinks the surface; Taubin's twin-coefficient
         scheme lets us iterate ~20× without losing scale or features.
      4. ``compute_normals()`` re-derives normals after smoothing so
         shading stays consistent with the new vertex positions.
    """
    n = field.shape[0]
    spacing = (2 * bounds / (n - 1),) * 3
    # Detect the case where the field has no zero-crossing before calling
    # marching_cubes, which would otherwise raise a cryptic internal error.
    if field.min() > level or field.max() < level:
        raise ValueError(
            "No real zero set in the sampling box for these parameters. "
            f"Field range: [{field.min():.4g}, {field.max():.4g}], "
            f"level={level:.4g}, bounds={bounds:.4g}."
        )
    verts, faces, normals, _ = measure.marching_cubes(field, level=level, spacing=spacing)
    verts -= bounds
    n_faces = faces.shape[0]
    pv_faces = np.empty((n_faces, 4), dtype=np.int64)
    pv_faces[:, 0] = 3
    pv_faces[:, 1:] = faces
    mesh = pv.PolyData(verts, pv_faces.ravel())
    # Attach the gradient-based normals before smoothing so smooth_taubin's
    # output has them as the seed for compute_normals later.
    mesh.point_data["Normals"] = normals.astype(np.float32)

    mesh = mesh.clean()
    if smooth_iter > 0 and mesh.n_points > 0:
        # Taubin (lambda > 0, mu < 0) is volume-preserving — unlike vanilla
        # Laplacian which shrinks the surface every iteration.
        mesh = mesh.smooth_taubin(n_iter=smooth_iter, pass_band=0.1)
    if mesh.n_points > 0:
        mesh = mesh.compute_normals(
            cell_normals=False, point_normals=True,
            consistent_normals=True, auto_orient_normals=False,
            split_vertices=False,
        )
    return mesh


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
    # mesh quality doesn't degrade as the box grows. Cap at 260 to keep
    # marching cubes responsive on slider drag while producing a smooth
    # triangulation (~17M voxels worst-case, ~1 s).
    if n is None:
        n = int(np.clip(round(220 * bounds / 2.5), 200, 260))

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


def enriques_figure_1(
    c: float = 1.0,
    n: int = 240,
    bounds: float = 1.8,
) -> pv.PolyData:
    """**Figure 1** — Canonical Enriques sextic (Wikipedia / MathWorld form).

    Homogeneous (degree 6 in P^3):
        w²x²y² + w²x²z² + w²y²z² + x²y²z²  +  c · w·x·y·z · (w² + x² + y² + z²) = 0

    Affine chart w = 1:
        x²y² + x²z² + y²z² + x²y²z²  +  c · xyz · (1 + x² + y² + z²) = 0

    Carries the full S_4 (tetrahedral) symmetry group; double curves along the
    six edges of the coordinate tetrahedron. This is *the* Enriques sextic
    referenced across Wikipedia, MathWorld, HandWiki, and the Cossec–Dolgachev
    text.
    """
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z

    F = (
        X2 * Y2 + X2 * Z2 + Y2 * Z2 + X2 * Y2 * Z2
        + c * (X * Y * Z) * (1.0 + X2 + Y2 + Z2)
    )
    F = np.clip(F, -10.0, 10.0)
    return _marching_cubes_to_polydata(F, bounds)


ENRIQUES_FIGURE_1_PARAMS = [
    ParamSpec("c", "c (mixing)", 0.1, 5.0, 1.0, 0.05,
              description="coefficient of the wxyz·(w²+x²+y²+z²) term"),
]


def enriques_figure_2(
    lam0: float = 1.0,
    lam3: float = 2.0,
    c: float = 1.0,
    n: int = 240,
    bounds: float = 1.8,
) -> pv.PolyData:
    """**Figure 2** — Diagonal Enriques sextic (Dolgachev λ-family).

    Same homogeneous family as Figure 1 but with independent coefficients on
    each of the four "missing-one-variable" sextic monomials:

        λ₀·s₁²s₂²s₃² + λ₁·s₀²s₂²s₃² + λ₂·s₀²s₁²s₃² + λ₃·s₀²s₁²s₂²
            + s₀·s₁·s₂·s₃ · Q(s₀, s₁, s₂, s₃)  =  0,

    with Q = s₀² + s₁² + s₂² + s₃². In affine chart s₀ = 1, holding
    λ₁ = λ₂ = 1 fixed and exposing λ₀ (central monomial weight) and λ₃
    (a single asymmetry knob) as sliders. λ₀ = λ₃ = 1 recovers Figure 1.

    Reference: Dolgachev, *A Brief Introduction to Enriques Surfaces*,
    Kyoto 2013 lecture notes (arXiv:1412.7744), §3 "λ-family".
    """
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z

    F = (
        lam0 * X2 * Y2 * Z2
        + 1.0 * Y2 * Z2          # λ₁ = 1
        + 1.0 * X2 * Z2          # λ₂ = 1
        + lam3 * X2 * Y2
        + c * (X * Y * Z) * (1.0 + X2 + Y2 + Z2)
    )
    F = np.clip(F, -10.0, 10.0)
    return _marching_cubes_to_polydata(F, bounds)


ENRIQUES_FIGURE_2_PARAMS = [
    ParamSpec("lam0", "λ₀ (central)", 0.1, 4.0, 1.0, 0.05,
              description="weight of x²y²z² monomial — the 'central' degree-6 term"),
    ParamSpec("lam3", "λ₃ (asymmetry)", 0.1, 4.0, 2.0, 0.05,
              description="weight of x²y² monomial — breaks S_4 to S_3 when ≠ 1"),
    ParamSpec("c", "c (mixing)", 0.1, 5.0, 1.0, 0.05,
              description="coefficient of the xyz·(1+x²+y²+z²) cubic-quadratic term"),
]


def enriques_figure_3(
    k: float = 16.0,
    n: int = 240,
    bounds: float = 2.5,
) -> pv.PolyData:
    """**Figure 3** — Cayley quartic symmetroid (Reye-cover model).

        f(x, y, z) = (x + y + z + xy + xz + yz)²  −  k · xyz  =  0

    Affine chart of the homogeneous quartic
        (x₀x₁ + x₀x₂ + x₀x₃ + x₁x₂ + x₁x₃ + x₂x₃)²  =  k · x₀x₁x₂x₃,
    a degree-4 surface in P^3 with up to 10 ordinary nodes. Its étale double
    cover (the Reye congruence) is an Enriques surface — historically the
    *first* Enriques surface ever constructed (Reye 1882, predating Enriques
    1896 by 14 years).

    Avoid the degenerate values k = 4 and k = 36; recommended smooth-look
    range is roughly 8 ≤ k ≤ 30.

    References: Cossec, "Reye Congruences," Trans. AMS 280 (1983);
    Dolgachev–Keum, Trans. AMS 354 (2002).
    """
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")

    s = X + Y + Z + X * Y + X * Z + Y * Z
    F = s * s - k * X * Y * Z
    F = np.clip(F, -50.0, 50.0)
    return _marching_cubes_to_polydata(F, bounds)


ENRIQUES_FIGURE_3_PARAMS = [
    ParamSpec("k", "k (RHS)", 5.0, 35.0, 16.0, 0.5,
              description="(x+y+z+xy+xz+yz)² = k·xyz — avoid k=4 and k=36 (degenerate)"),
]


def enriques_figure_4(
    tau: float = 0.18,
    n: int = 260,
    bounds: float = 1.5,
) -> pv.PolyData:
    """**Figure 4** — Endrass-normalized icosahedral sextic (Barth-dial variant).

        P(x, y, z) = 4 · (φ²x² − y²)(φ²y² − z²)(φ²z² − x²)
        Q(x, y, z) = (1 + 2φ) · (x² + y² + z² − 1)²
        f(x, y, z) = P  −  τ · Q  =  0,

    where φ = (1+√5)/2 is the golden ratio.

    **Note on the Barth sextic.**  Barth's classical 65-nodal sextic uses
    Q = (1+2φ)·(x²+y²+z²)² (without the −1 shift).  The equation here uses
    (x²+y²+z²−1)² following Endrass's normalization, which shifts node
    positions relative to the classical Barth surface.  Consequently τ = 1
    here is *not* Barth's 65-nodal surface; it is the Endrass-normalized
    variant and produces a different (still icosahedrally symmetric) surface.

    At τ ≈ 0.18 the node count drops to Enriques-compatible levels.
    The full icosahedral A_5 symmetry is preserved for all τ, providing a
    visual contrast to the discrete-cubic symmetries of Figures 1–3.

    References: Barth, *J. Algebraic Geom.* 5 (1996); Endrass,
    *J. reine angew. Math.* 485 (1997).
    """
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    phi2 = phi * phi
    one_plus_2phi = 1.0 + 2.0 * phi

    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z

    P = 4.0 * (phi2 * X2 - Y2) * (phi2 * Y2 - Z2) * (phi2 * Z2 - X2)
    Q = one_plus_2phi * (X2 + Y2 + Z2 - 1.0) ** 2
    F = P - tau * Q
    F = np.clip(F, -20.0, 20.0)
    return _marching_cubes_to_polydata(F, bounds)


ENRIQUES_FIGURE_4_PARAMS = [
    ParamSpec("tau", "τ (Barth dial)", 0.05, 1.0, 0.18, 0.01,
              description="Endrass-normalized variant; τ≈0.18 gives Enriques-compatible node count"),
]


# ---------------------------------------------------------------------------
# Registry — keys appear in the GUI dropdowns
# ---------------------------------------------------------------------------


VARIETIES: dict[str, dict[str, Surface]] = {
    "K3 surface": {
        "Fermat quartic": Surface("Fermat quartic", fermat_quartic, FERMAT_PARAMS),
        "Kummer surface": Surface("Kummer surface", kummer_surface, KUMMER_PARAMS),
    },
    "Enriques surface": {
        "Canonical sextic  [Fig. 1]": Surface(
            "Enriques sextic (canonical, S₄ symmetry)",
            enriques_figure_1, ENRIQUES_FIGURE_1_PARAMS,
        ),
        "Diagonal λ-family  [Fig. 2]": Surface(
            "Enriques sextic (diagonal λ-family)",
            enriques_figure_2, ENRIQUES_FIGURE_2_PARAMS,
        ),
        "Cayley symmetroid  [Fig. 3]": Surface(
            "Cayley quartic symmetroid (Reye cover)",
            enriques_figure_3, ENRIQUES_FIGURE_3_PARAMS,
        ),
        "Icosahedral sextic  [Fig. 4]": Surface(
            "Barth-style icosahedral sextic (A₅ symmetry)",
            enriques_figure_4, ENRIQUES_FIGURE_4_PARAMS,
        ),
    },
}

# ---------------------------------------------------------------------------
# Tooltips for the variety / subtype dropdowns (used by the GUI)
# ---------------------------------------------------------------------------

VARIETY_TOOLTIPS: dict[str, str] = {
    "K3 surface": (
        "A K3 surface is a compact complex surface with trivial canonical bundle "
        "and first Betti number 0. K3 surfaces are the 2-dimensional analogue of "
        "elliptic curves and play a central role in mirror symmetry."
    ),
    "Enriques surface": (
        "An Enriques surface is the quotient of a K3 surface by a fixed-point-free "
        "involution. It has Euler number 12 and 2K=0. Four representative real "
        "affine models are provided here."
    ),
}

SUBTYPE_TOOLTIPS: dict[str, str] = {
    # K3
    "Fermat quartic": (
        "Fig. — | x⁴+y⁴+z⁴+… = c | "
        "3-parameter deformation of the classical Fermat quartic. "
        "Full octahedral O_h symmetry at α=β=γ=0."
    ),
    "Kummer surface": (
        "Fig. — | (x²+y²+z²−μ²)² = λ·pqrs | "
        "Classic 16-nodal quartic (Hudson form). "
        "Smooth in the range 1 < μ² < 3."
    ),
    # Enriques
    "Canonical sextic  [Fig. 1]": (
        "Figure 1 · S₄ tetrahedral symmetry | "
        "The Enriques 1896 canonical sextic: "
        "x²y²+x²z²+y²z²+x²y²z² + c·xyz·(1+x²+y²+z²) = 0."
    ),
    "Diagonal λ-family  [Fig. 2]": (
        "Figure 2 · S₄→S₃ symmetry breaking | "
        "Dolgachev's λ-family: independent weights on the four "
        "'missing-one-variable' degree-6 monomials."
    ),
    "Cayley symmetroid  [Fig. 3]": (
        "Figure 3 · Reye congruence model | "
        "Cayley quartic symmetroid: (x+y+z+xy+xz+yz)² = k·xyz. "
        "Historically the first Enriques surface (Reye 1882)."
    ),
    "Icosahedral sextic  [Fig. 4]": (
        "Figure 4 · A₅ icosahedral symmetry | "
        "Endrass-normalized variant of Barth's 65-nodal sextic; "
        "τ≈0.18 gives Enriques-compatible node count."
    ),
}
