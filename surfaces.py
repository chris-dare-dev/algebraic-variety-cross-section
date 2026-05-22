"""Mesh generators for K3, Enriques, and Calabi–Yau (3-fold) surfaces.

Each surface is a `Surface` carrying a generator function and a list of
`ParamSpec` describing its tunable parameters. Implicit surfaces are
extracted via marching cubes on a sampled scalar field. Parametric
surfaces (used for the Hanson-style Calabi–Yau cross-sections) are
built directly from a 2D parameter grid via `_grid_to_polydata`.
"""

from __future__ import annotations

import warnings
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
            "No real zero set in the sampling box for these parameters "
            f"(field range [{field.min():.3g}, {field.max():.3g}]). "
            "Try adjusting the sliders to a different parameter combination."
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


def _grid_to_polydata(X: np.ndarray, Y: np.ndarray, Z: np.ndarray) -> pv.PolyData:
    """Build a triangulated PolyData from a 2D grid of (X, Y, Z) values.

    Each adjacent (i,j)-(i+1,j+1) cell becomes two triangles. Used by the
    parametric CY3 cross-section generators.
    """
    if X.shape != Y.shape or X.shape != Z.shape or X.ndim != 2:
        raise ValueError("X, Y, Z must be 2D arrays of the same shape")
    M, N = X.shape
    vertices = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

    i, j = np.mgrid[0:M - 1, 0:N - 1]
    v00 = (i * N + j).ravel()
    v01 = (i * N + j + 1).ravel()
    v11 = ((i + 1) * N + j + 1).ravel()
    v10 = ((i + 1) * N + j).ravel()

    n_quads = v00.size
    faces = np.empty((n_quads * 2, 4), dtype=np.int64)
    faces[::2, 0] = 3
    faces[::2, 1] = v00
    faces[::2, 2] = v01
    faces[::2, 3] = v11
    faces[1::2, 0] = 3
    faces[1::2, 1] = v00
    faces[1::2, 2] = v11
    faces[1::2, 3] = v10

    return pv.PolyData(vertices, faces.ravel())


def _concat_polydata(meshes: list[pv.PolyData]) -> pv.PolyData:
    """Concatenate a list of PolyData into one, remapping face indices.

    Assumes every input mesh has triangle-only faces (``[3, i0, i1, i2]`` per
    face). Call ``mesh.triangulate()`` first if your meshes have quad/poly faces.
    """
    if not meshes:
        return pv.PolyData()
    all_verts = []
    all_faces = []
    offset = 0
    for m in meshes:
        if m.n_points == 0:
            continue
        all_verts.append(m.points)
        assert len(m.faces) % 4 == 0, (
            f"_concat_polydata expects triangle faces; got faces array of length {len(m.faces)}"
        )
        faces_arr = m.faces.reshape(-1, 4).copy()
        faces_arr[:, 1:] += offset
        all_faces.append(faces_arr.ravel())
        offset += m.n_points
    if not all_verts:
        return pv.PolyData()
    return pv.PolyData(np.vstack(all_verts), np.concatenate(all_faces))


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
    # mesh quality doesn't degrade as the box grows. Cap at 220 to keep
    # marching cubes responsive on slider drag while producing a smooth
    # triangulation.  realtime-variety-render-e1-s3 (CAND-13): the cap was
    # lowered 260 -> 220 — the Fermat quartic field is smooth with no
    # near-singularities, so n=220 (~10.6M voxels) is topologically identical
    # to n=260 (~17.6M) at viewport zoom; the higher resolution is reserved
    # for the screenshot/export path where latency does not matter.
    if n is None:
        n = int(np.clip(round(220 * bounds / 2.5), 200, 220))

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
    n: int = 220,
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
# Calabi–Yau 3-fold cross-sections
#
# A Calabi–Yau 3-fold is 6-real-dimensional and cannot be embedded in R^3.
# The visualization tradition collapses to a single canonical convention:
# Hanson's parametric cross-section (Notices of the AMS 41(9), 1994) of the
# Fermat quintic, plus parametric variants. We implement three Hanson-style
# parametric figures plus one implicit Dwork-pencil real slice.
# ---------------------------------------------------------------------------


def _hanson_cross_section(
    n: int,
    n2: int,
    alpha: float,
    grid: float,
    xi_max: float,
) -> pv.PolyData:
    """Hanson's parametric cross-section of  z₁ⁿ + z₂ⁿ₂ = 1  in C².

    Parameterization (Hanson 1994, Eqs. 5–7):

        z₁(θ, ξ, k₁) = exp(2πi·k₁/n ) · cosh(ξ + iθ)^(2/n)
        z₂(θ, ξ, k₂) = exp(2πi·k₂/n₂) · (-i·sinh(ξ + iθ))^(2/n₂)

    with θ ∈ [0, π/2], ξ ∈ [-ξ_max, ξ_max], and (k₁, k₂) ∈ {0..n−1}×{0..n₂−1}
    indexing the n·n₂ patches that tile the surface.

    Projection to R³:

        (X, Y, Z) = (Re z₁, Re z₂, cos α · Im z₁ + sin α · Im z₂)

    The α slider rotates between the two suppressed imaginary axes (α = π/4
    is the canonical Hanson choice).

    Args:
        n: exponent for z₁.
        n2: exponent for z₂ (= n₂ in the parameterization above).
        alpha: projection angle in radians.
        grid: number of sample points per patch axis (odd preferred; see below).
              If grid is even, it is silently coerced to grid + 1 (Hanson 1994
              p. 6: surface must pass through fixed points along ξ = 0).
        xi_max: ξ-extent of each patch.

    What the user sees: a real 2-surface in R⁴, projected to R³ — a
    2-slice of the complex curve z₁ⁿ + z₂ⁿ₂ = 1, which is itself a
    2-slice of the projective Fermat hypersurface in CP^N. For (n, n₂) =
    (5, 5) this is the iconic image associated with Calabi–Yau 3-folds.
    """
    # Hanson's tip (paper p. 6): xiSteps must be odd for the surface to pass
    # through the fixed points along ξ = 0. Coerce slider float → int.
    grid = int(round(grid))
    if grid % 2 == 0:
        grid += 1

    xi = np.linspace(-xi_max, xi_max, grid)
    theta = np.linspace(0.0, np.pi / 2, grid)
    XI, TH = np.meshgrid(xi, theta, indexing="ij")
    z = XI + 1j * TH

    # u₁ = cosh(z), u₂ = -i·sinh(z) — satisfy u₁² + u₂² = 1.
    # Both lie in the closed right half-plane for (ξ, θ) ∈ [-ξ_max, ξ_max] × [0, π/2],
    # so np.power's principal-branch fractional exponent is continuous on each patch;
    # the Z_n × Z_n₂ phase factors then cover the remaining branches.
    u1 = np.cosh(z)
    u2 = -1j * np.sinh(z)
    u1_pow = u1 ** (2.0 / n)
    u2_pow = u2 ** (2.0 / n2)

    cos_a = float(np.cos(alpha))
    sin_a = float(np.sin(alpha))

    patches: list[pv.PolyData] = []
    for k1 in range(n):
        phase1 = np.exp(2j * np.pi * k1 / n)
        z1 = phase1 * u1_pow
        for k2 in range(n2):
            phase2 = np.exp(2j * np.pi * k2 / n2)
            z2 = phase2 * u2_pow

            X = z1.real
            Y = z2.real
            Z = cos_a * z1.imag + sin_a * z2.imag

            patches.append(_grid_to_polydata(X, Y, Z))

    merged = _concat_polydata(patches)
    if merged.n_points > 0:
        # Note: smooth_taubin is intentionally omitted here. The parametric grid
        # already defines a C² surface; smoothing would smear patch boundaries
        # without quality benefit and would multiply the cost on dense grids.
        #
        # We use cell_normals=True with consistent_normals=False because the
        # 25 patches from _concat_polydata are disconnected components.
        # consistent_normals=True cannot orient normals coherently across
        # components and causes per-patch lighting flips. Cell normals derived
        # from triangle winding are correct within each patch and PyVista uses
        # them correctly under default lighting.
        merged = merged.compute_normals(
            cell_normals=True, point_normals=True,
            consistent_normals=False, auto_orient_normals=False,
            split_vertices=False,
        )
    return merged


def calabi_yau_quintic(
    alpha: float = np.pi / 4,
    grid: float = 61,
    xi_max: float = 1.0,
) -> pv.PolyData:
    """**Figure 1** — Hanson's quintic cross-section (the canonical CY3 image).

    n₁ = n₂ = 5. The exponent that makes this *the* Calabi–Yau cross-section:
    a 2-slice of the Fermat quintic z₁⁵+z₂⁵+z₃⁵+z₄⁵+z₅⁵ = 0 in CP⁴, which
    is the simplest projective Calabi–Yau 3-fold.

    Reference: Hanson, A. J. "A Construction for Computer Visualization of
    Certain Complex Curves," Notices of the AMS 41(9):1156–1163 (1994).
    """
    return _hanson_cross_section(n=5, n2=5, alpha=alpha, grid=grid, xi_max=xi_max)


CALABI_YAU_QUINTIC_PARAMS = [
    ParamSpec("alpha", "α (projection)", 0.0, np.pi / 2, np.pi / 4, 0.02,
              description="rotation between suppressed imaginary axes; α=π/4 is canonical"),
    ParamSpec("grid", "grid (per patch)", 21.0, 81.0, 41.0, 2.0,
              description="(odd) sample points per patch axis; higher = smoother"),
    ParamSpec("xi_max", "ξ range", 0.5, 2.0, 1.0, 0.05,
              description="ξ-extent of each patch; larger = more of the surface visible"),
]


def calabi_yau_cubic(
    alpha: float = np.pi / 4,
    grid: float = 51,
    xi_max: float = 1.0,
) -> pv.PolyData:
    """**Figure 2** — Hanson cross-section with n = 3 (torus).

    Same construction with the lower exponent n₁ = n₂ = 3 — the resulting
    surface has genus 1 (a torus) rather than the higher-genus quintic.
    Pedagogically useful: same code path, dramatically different topology.
    """
    return _hanson_cross_section(n=3, n2=3, alpha=alpha, grid=grid, xi_max=xi_max)


CALABI_YAU_CUBIC_PARAMS = [
    ParamSpec("alpha", "α (projection)", 0.0, np.pi / 2, np.pi / 4, 0.02,
              description="rotation between suppressed imaginary axes"),
    ParamSpec("grid", "grid (per patch)", 21.0, 81.0, 33.0, 2.0,
              description="(odd) sample points per patch axis"),
    ParamSpec("xi_max", "ξ range", 0.5, 2.0, 1.0, 0.05,
              description="ξ-extent of each patch"),
]


def calabi_yau_asymmetric(
    alpha: float = np.pi / 4,
    grid: float = 53,
    xi_max: float = 1.0,
) -> pv.PolyData:
    """**Figure 3** — Hanson's asymmetric construction with (n₁, n₂) = (5, 3).

    Hanson's own extension (1994 paper, Eqs. 10–12): allow distinct
    exponents on z₁ and z₂. Breaks the visual five-fold symmetry of the
    quintic into a 5×3 patch lattice. Demonstrates that the construction
    is more general than the n₁ = n₂ = 5 advertisement.
    """
    return _hanson_cross_section(n=5, n2=3, alpha=alpha, grid=grid, xi_max=xi_max)


CALABI_YAU_ASYMMETRIC_PARAMS = [
    ParamSpec("alpha", "α (projection)", 0.0, np.pi / 2, np.pi / 4, 0.02,
              description="rotation between suppressed imaginary axes"),
    ParamSpec("grid", "grid (per patch)", 21.0, 81.0, 35.0, 2.0,
              description="(odd) sample points per patch axis"),
    ParamSpec("xi_max", "ξ range", 0.5, 2.0, 1.0, 0.05,
              description="ξ-extent of each patch"),
]


def calabi_yau_dwork(
    psi: float = 0.5,
    n: int = 260,
    bounds: float = 1.8,
) -> pv.PolyData:
    """**Figure 4** — Real affine slice of the Dwork-pencil quintic.

    Dehomogenizing the projective Dwork pencil
        z₁⁵ + z₂⁵ + z₃⁵ + z₄⁵ + z₅⁵ - 5ψ·z₁z₂z₃z₄z₅ = 0
    by setting z₄ = z₅ = 1 yields the implicit real surface

        f(x, y, z) = x⁵ + y⁵ + z⁵ + 2 - 5·ψ·x·y·z = 0.

    ψ is the canonical Dwork-pencil modulus: ψ = 0 reduces to the Fermat
    quintic shadow (no cross-coupling); ψ = 1 is the (real) conifold point;
    the five conifold points in ℂ are the fifth roots of unity, at which the
    projective fibre acquires 125 nodal singularities. The +2 constant arises
    from dehomogenizing with z₄ = z₅ = 1; the conventional 'Fermat quintic
    shadow' x⁵+y⁵+z⁵=1 is topologically equivalent under (x,y,z)→(−x,−y,−z).
    Dragging ψ across the slider moves the user through a one-parameter
    family of Calabi–Yau 3-folds — the family parameter has direct
    geometric meaning even though we only see a 2D real shadow.

    References:
    - P. Candelas et al., "A pair of Calabi–Yau manifolds as an exactly
      soluble superconformal theory," Nucl. Phys. B 359 (1991), 21–74.
    - Wikipedia, "Dwork family."
    """
    if abs(psi - 1.0) < 0.01:
        warnings.warn(
            "ψ ≈ 1 is the (real) conifold point of the Dwork pencil. "
            "The fibre acquires a node at (1,1,1) that marching cubes will not "
            "capture; the displayed mesh is the smooth complement.",
            category=RuntimeWarning,
        )
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    F = X**5 + Y**5 + Z**5 + 2.0 - 5.0 * psi * X * Y * Z
    F = np.clip(F, -100.0, 100.0)
    return _marching_cubes_to_polydata(F, bounds)


CALABI_YAU_DWORK_PARAMS = [
    ParamSpec("psi", "ψ (Dwork modulus)", -2.5, 2.5, 0.5, 0.02,
              description="One-parameter CY₃ family; ψ=1 is the (real) conifold point; the five conifold points in ℂ are the fifth roots of unity"),
]


# ---------------------------------------------------------------------------
# Fano 3-folds of Picard rank 1
#
# Smooth Fano 3-folds with ρ(X) = 1 form a finite list (Iskovskikh 1977,
# Mori–Mukai 1982), indexed by the index r and degree.  They are
# 6-real-dimensional, so each figure below is a *real-2D slice* of an
# explicit projective model — fix one or two ambient coordinates, then
# render the resulting implicit surface.
# ---------------------------------------------------------------------------


def fano_klein_cubic(
    z0: float = 0.4,
    n: int = 240,
) -> pv.PolyData:
    """**Figure 1** — Real slice of the **Klein cubic threefold** V_3.

    The Klein cubic in P^4 with [V:W:X:Y:Z]:

        V²W + W²X + X²Y + Y²Z + Z²V = 0

    is a smooth Fano 3-fold of index 2 with automorphism group PSL₂(11)
    of order 660 — the unique cubic 3-fold with this symmetry.

    To land in R³ we dehomogenize V = 1 and slice by fixing Z = z₀.
    Renaming (W, X, Y) → (x, y, z) for plotting:

        f(x, y, z) = x + x²·y + y²·z + z₀·z² + z₀²

    z₀ controls the slice.  At z₀=0 the slice degenerates to the cubic
    surface V²W + W²X + X²Y = 0 in the hyperplane Z=0 of P⁴ — still a
    valid 2D surface, but lower-dimensional than the threefold slice.

    References:
    - Wikipedia, "Klein cubic threefold."
    - Adler, "On the automorphism group of a certain cubic threefold,"
      arXiv:math/0102079.
    """
    bounds = 2.0
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    F = X + X * X * Y + Y * Y * Z + z0 * Z * Z + z0 * z0
    F = np.clip(F, -50.0, 50.0)
    return _marching_cubes_to_polydata(F, bounds)


FANO_KLEIN_CUBIC_PARAMS = [
    ParamSpec("z0", "z₀ (slice)", -1.0, 1.0, 0.4, 0.02,
              description="fixed value of the suppressed projective coordinate; z₀=0 gives a special cubic-surface slice"),
]


def fano_segre_cubic(
    a: float = 0.3,
    b: float = -0.4,
    n: int = 240,
) -> pv.PolyData:
    """**Figure 2** — Real slice of the **Segre cubic** in P^5.

    The Segre cubic threefold is the locus in P^5 cut out by

        Σ x_i = 0   and   Σ x_i³ = 0     (i = 0, …, 5)

    It is the unique cubic 3-fold with the maximum number (10) of nodes
    over ℂ; carries the full S_6 symmetric-group action.

    Eliminating x_5 = -(x_0+…+x_4) reduces to a single cubic in five
    variables.  Slicing by fixing (x_3, x_4) = (a, b) and renaming
    (x_0, x_1, x_2) → (x, y, z):

        f(x, y, z) = x³ + y³ + z³ + a³ + b³ - (x + y + z + a + b)³

    The 10 nodes of the parent surface project down to a smaller number
    of visible singular points in the slice.

    References:
    - Wikipedia, "Segre cubic."
    - Hunt, "The Geometry of Some Special Arithmetic Quotients," LNM 1637.
    """
    # bounds=2.5 (vs 2.0 elsewhere): the Segre cubic real zero set reaches r ≈ 2.1 from
    # the origin at default (a, b); a 2.0 box clips the outer lobes.
    bounds = 2.5
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    s = X + Y + Z + a + b
    F = X**3 + Y**3 + Z**3 + a**3 + b**3 - s**3
    # cubic field grows as ~(2a+2b+5)³ ≈ 800 at slider extremes; ±1000 covers all reachable corners.
    F = np.clip(F, -1000.0, 1000.0)
    return _marching_cubes_to_polydata(F, bounds)


FANO_SEGRE_CUBIC_PARAMS = [
    ParamSpec("a", "a (slice x₃)", -1.0, 1.0, 0.3, 0.02,
              description="value of the fixed coordinate x₃ in the (x₃, x₄) slice"),
    ParamSpec("b", "b (slice x₄)", -1.0, 1.0, -0.4, 0.02,
              description="value of the fixed coordinate x₄"),
]


def fano_two_quadrics(
    p: float = 0.3,
    q: float = -0.2,
    mu: float = 0.5,
    eps: float = 0.18,
    n: int = 220,
) -> pv.PolyData:
    """**Figure 3** — Sum-of-squares "tube" around the intersection of two
    quadrics in P^5 — the smooth Fano 3-fold V_4 of index 2.

    Diagonal pencil model (Hassett–Tschinkel):

        Q_1(x) = Σ x_i² - 1
        Q_2(x) = Σ λ_i · x_i² - μ

    with λ = (-0.5, 0.0, 0.5, 1.0, 1.5) chosen pairwise distinct so the
    pencil is smooth.  Slicing by fixing (x_3, x_4) = (p, q) and rendering
    the **eps-tube**

        f(x, y, z) = Q_1² + Q_2² - eps²

    gives a thickened approximation to the codimension-2 real slice; the
    user-controlled eps is the tube width.  ``eps`` smaller than ~3× the
    voxel spacing produces a swiss-cheese mesh.

    References:
    - Reid, "Young Person's Guide to Canonical Singularities."
    - Hassett & Tschinkel, "Rationality of complete intersections of two
      quadrics over nonclosed fields."
    """
    bounds = 2.0
    # Warn when eps is near the voxel-spacing limit so the status bar gives the
    # user a hint before they see a swiss-cheese mesh. Voxel spacing is
    # 2*bounds/(n-1) ≈ 0.018; three voxels ≈ 0.055.
    if eps < 0.08:
        warnings.warn(
            f"ε={eps:.3f} is close to the voxel resolution limit (~0.055). "
            "The tube mesh may have holes; increase ε or reduce n for a cleaner surface.",
            category=RuntimeWarning,
        )
    # Smoothness: λ values pairwise distinct.
    # lam[1]=0: Q₂ has no Y² term, so Q₂=0 is a cylinder in (X,Z) extended in Y;
    # the tube wraps a Y-symmetric band rather than an isolated curve.
    lam = (-0.5, 0.0, 0.5, 1.0, 1.5)
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    Q1 = X * X + Y * Y + Z * Z + p * p + q * q - 1.0
    Q2 = (lam[0] * X * X + lam[1] * Y * Y + lam[2] * Z * Z
          + lam[3] * p * p + lam[4] * q * q - mu)
    F = Q1 * Q1 + Q2 * Q2 - eps * eps
    F = np.clip(F, -200.0, 200.0)
    return _marching_cubes_to_polydata(F, bounds)


FANO_TWO_QUADRICS_PARAMS = [
    ParamSpec("p", "p (slice x₃)", -1.0, 1.0, 0.3, 0.02,
              description="fixed projective coordinate x₃; large |p| shrinks the tube"),
    ParamSpec("q", "q (slice x₄)", -1.0, 1.0, -0.2, 0.02,
              description="fixed projective coordinate x₄; large |q| shrinks the tube"),
    ParamSpec("mu", "μ (RHS of Q₂)", -1.5, 1.5, 0.5, 0.02,
              description="constant term of the second quadric Q₂"),
    ParamSpec("eps", "ε (tube width)", 0.06, 0.40, 0.18, 0.01,
              description="tube half-thickness; small ε → thin shell, large ε → fat blob; below ~0.06 the mesh develops holes"),
]


def fano_sextic_double_solid(
    R: float = 1.2,
    alpha: float = 0.0,
    n: int = 240,
) -> pv.PolyData:
    """**Figure 4** — Real slice of a **sextic double solid** V_1.

    Standard model in weighted P(1,1,1,1,3) with [x_0:x_1:x_2:x_3:w]:

        w² = f_6(x_0, x_1, x_2, x_3)

    is the simplest Fano 3-fold of index 1, genus 2 (Iskovskikh family 1-1).

    The Fermat-symmetric branch f_6 = Σ x_i⁶ has only positive values in any
    affine chart, so its real locus is two non-intersecting parallel sheets
    — visually uninteresting.  We use a **sign-flipped Fermat-style branch**

        f_6 = R⁶ - x_0⁶ - x_1⁶ - x_2⁶ - α · x_0²·x_1²·(x_0²+x_1²)

    which takes both signs in any affine chart, so the two sheets z = ±√f_6
    actually meet on the sextic branch curve f_6 = 0.  Slicing by setting
    x_2 = 0 and x_3 = 1, then renaming (x_0, x_1, w) → (x, y, z), gives the
    plotted equation

        f(x, y, z) = z² + x⁶ + y⁶ + α · x²y²(x²+y²) - R⁶ = 0,

    a closed compact sextic surface — two domes joined along the sextic
    curve z = 0, x⁶ + y⁶ + α·x²y²(x²+y²) = R⁶.

    R controls the overall size; α deforms the equator's sextic branch curve
    along the (x = ±y) diagonals.  At α = 0 the surface has the full
    octahedral symmetry of x⁶+y⁶; α ≠ 0 breaks it to D₂.

    References:
    - Iskovskikh & Prokhorov, *Fano Varieties*, Encyclopaedia of Math. Sci. 47.
    - Fanography, family 1-1 (sextic double solid).
    """
    bounds = 2.0
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2 = X * X, Y * Y
    F = (
        Z * Z
        + X2 * X2 * X2
        + Y2 * Y2 * Y2
        + alpha * X2 * Y2 * (X2 + Y2)
        - R**6
    )
    F = np.clip(F, -200.0, 200.0)
    return _marching_cubes_to_polydata(F, bounds)


FANO_SEXTIC_DOUBLE_SOLID_PARAMS = [
    ParamSpec("R", "R (size)", 0.6, 2.0, 1.2, 0.02,
              description="z²+x⁶+y⁶+… = R⁶ — controls the overall size of the closed sextic surface"),
    ParamSpec("alpha", "α (deformation)", -2.0, 2.0, 0.0, 0.05,
              description="coeff of x²y²(x²+y²) — breaks octahedral to D₂; pinches/bulges along x=±y"),
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
    "Calabi–Yau 3-fold": {
        "Hanson quintic  [Fig. 1]": Surface(
            "Hanson quintic CY cross-section (n=5)",
            calabi_yau_quintic, CALABI_YAU_QUINTIC_PARAMS,
        ),
        "Hanson cubic torus  [Fig. 2]": Surface(
            "Hanson cross-section (n=3, torus)",
            calabi_yau_cubic, CALABI_YAU_CUBIC_PARAMS,
        ),
        "Hanson asymmetric (5,3)  [Fig. 3]": Surface(
            "Hanson cross-section (n₁=5, n₂=3)",
            calabi_yau_asymmetric, CALABI_YAU_ASYMMETRIC_PARAMS,
        ),
        "Dwork pencil  [Fig. 4]": Surface(
            "Dwork pencil real slice (ψ-family)",
            calabi_yau_dwork, CALABI_YAU_DWORK_PARAMS,
        ),
    },
    "Fano 3-fold (ρ=1)": {
        "Klein cubic  [Fig. 1]": Surface(
            "Klein cubic threefold V₃ (PSL₂(11) symmetry)",
            fano_klein_cubic, FANO_KLEIN_CUBIC_PARAMS,
        ),
        "Segre cubic  [Fig. 2]": Surface(
            "Segre cubic (S₆ symmetry, max-nodal)",
            fano_segre_cubic, FANO_SEGRE_CUBIC_PARAMS,
        ),
        "Two-quadrics CI tube  [Fig. 3]": Surface(
            "Two-quadrics CI tube V₄ (ε-tube around Q₁∩Q₂, not the actual CI)",
            fano_two_quadrics, FANO_TWO_QUADRICS_PARAMS,
        ),
        "Sextic double solid  [Fig. 4]": Surface(
            "Sextic double solid V₁ (sign-flipped Fermat branch)",
            fano_sextic_double_solid, FANO_SEXTIC_DOUBLE_SOLID_PARAMS,
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
    "Calabi–Yau 3-fold": (
        "A Calabi–Yau 3-fold is a 6-real-dimensional space — it cannot be embedded "
        "in ℝ³. Each entry below is a 2D shadow, slice, or projection (in the "
        "Hanson-1994 tradition that produced the iconic 'Elegant Universe' image), "
        "not the 3-fold itself."
    ),
    "Fano 3-fold (ρ=1)": (
        "A smooth Fano 3-fold of Picard rank 1 (Iskovskikh's 'prime Fano "
        "threefold') is 6-real-dimensional. Each entry below is a 2D real "
        "slice obtained by fixing one or two ambient projective coordinates. "
        "The visualization tradition is essentially nonexistent — these are "
        "novel renderings."
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
    # Calabi–Yau 3-fold
    "Hanson quintic  [Fig. 1]": (
        "Figure 1 · Hanson 1994, Z₅×Z₅ symmetry | "
        "The iconic CY₃ cross-section: z₁⁵ + z₂⁵ = 1 in C², projected to ℝ³. "
        "This is the image on the cover of 'The Elegant Universe.'"
    ),
    "Hanson cubic torus  [Fig. 2]": (
        "Figure 2 · Hanson n=3 (torus) | "
        "z₁³ + z₂³ = 1, same construction with lower exponent. "
        "Genus 1 — visually a 9-patch torus."
    ),
    "Hanson asymmetric (5,3)  [Fig. 3]": (
        "Figure 3 · Hanson asymmetric construction | "
        "z₁⁵ + z₂³ = 1 — Hanson's own (n₁ ≠ n₂) extension. "
        "Breaks the visual symmetry of the quintic."
    ),
    "Dwork pencil  [Fig. 4]": (
        "Figure 4 · Implicit Dwork-pencil real slice | "
        "x⁵+y⁵+z⁵+2 = 5ψ·xyz. The ψ slider sweeps the canonical "
        "one-parameter CY₃ family; ψ=1 is the (real) conifold point; "
        "the five conifold points in ℂ are the fifth roots of unity."
    ),
    # Fano 3-folds (Picard rank 1)
    "Klein cubic  [Fig. 1]": (
        "Figure 1 · PSL₂(11) symmetry, index 2 | "
        "Klein cubic V₃: V²W+W²X+X²Y+Y²Z+Z²V=0. Slice by Z=z₀. "
        "The unique smooth cubic 3-fold with order-660 symmetry."
    ),
    "Segre cubic  [Fig. 2]": (
        "Figure 2 · S₆ symmetry of the parent (broken in the slice) | "
        "Σxᵢ=0 ∧ Σxᵢ³=0 in P⁵, eliminating x₅ and slicing by (x₃,x₄)=(a,b). "
        "Maximally nodal cubic 3-fold (10 nodes in the parent variety; "
        "visible singular points in the slice depend on (a,b))."
    ),
    "Two-quadrics CI tube  [Fig. 3]": (
        "Figure 3 · Sum-of-squares tube of V₄, index 2 | "
        "f = Q₁²+Q₂²−ε² approximates the codim-2 intersection. "
        "Diagonal pencil with 5 distinct λ values."
    ),
    "Sextic double solid  [Fig. 4]": (
        "Figure 4 · Index 1, genus 2 (Iskovskikh family 1-1) | "
        "z² + x⁶+y⁶+α·x²y²(x²+y²) = R⁶. Sign-flipped Fermat branch "
        "gives a closed compact double cover; α deforms the sextic equator."
    ),
}
