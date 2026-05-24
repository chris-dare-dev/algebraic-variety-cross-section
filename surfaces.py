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

# realtime-variety-render-e5 (CAND-2): Numba JIT field-evaluation kernels.
# numba is a pure compute dependency (BSD-2-Clause) — no renderer, AI-1 clean.
# THREADING_LAYER MUST be set before the first parallel kernel is *called*;
# module-import time is the safe, spike-proven placement (kernels are only
# called at generate() time, long after import).  `workqueue` is Numba's
# always-available, dependency-free layer — it keeps Numba's thread pool
# separate from VTK's SMP pool so a kernel and a Flying Edges contour running
# back-to-back in the e4 worker do not contend (e5 Numba arm64 spike §6).
#
# NOTE — intentional process-global side-effect: assigning
# `numba.config.THREADING_LAYER` mutates Numba's *process-wide* config.
# Importing `surfaces` therefore pins the threading layer for the whole
# process.  This is benign and desired here — `surfaces` is imported only by
# the AVC app and its test suite, both of which want `workqueue` — but a
# future in-process embedding that also uses Numba with a different layer
# expectation would have its choice silently decided by import order.  See
# CONTEXT.md §3.
import numba

# B6: numba threading-layer + @njit import removed -- now lives in varieties/_kernels.py
# which is imported below; the threading-layer side effect fires before any @njit
# decorated function in this module is referenced.


# Per restructure-feature-subpackages-2026q2-r2 Batch 5: ParamSpec and Surface
# moved to varieties/types.py; should_render_on_drag, dispatch_mode, and
# FAST_RENDER_THRESHOLD_MS moved to varieties/dispatch.py. Re-exported here for
# backward-compatibility (existing `from surfaces import ParamSpec` keeps working).
from varieties.types import ParamSpec, Surface
from varieties.dispatch import (
    should_render_on_drag,
    dispatch_mode,
    FAST_RENDER_THRESHOLD_MS,
)

# Per restructure-feature-subpackages-2026q2-r2 Batch 6: marching pipeline helpers
# and 11 Numba kernels moved to varieties/_marching.py and varieties/_kernels.py.
# Re-exported here for backward compatibility.  CRITICAL: importing _kernels eagerly
# ensures `numba.config.THREADING_LAYER = "workqueue"` fires before any generator
# below uses @njit-decorated functions.
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






# ---------------------------------------------------------------------------
# Numba JIT field-evaluation kernels (realtime-variety-render-e5 / CAND-2)
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


def enriques_figure_1(
    c: float = 1.0,
    n: int = 240,
    bounds: float = 1.89,
    hq_smoothing: bool = False,
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
    # realtime-variety-render-e5 (CAND-2): field evaluated by the Numba JIT
    # kernel `_enriques_fig1_field_kernel` (see the helpers section) — replaces
    # the NumPy meshgrid-broadcasting block; the clip (±10) is folded in.
    # AI-8: coerce `n` to int in-generator so a caller passing a computed
    # float `n` (e.g. a future screenshot/export path) does not reach
    # `np.linspace` / `np.empty` as a float.
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _enriques_fig1_field_kernel(g, c, F)
    # enriques-hq-smoothing-2026q3-e1: opt-in second Taubin pass for the
    # double-curve sawtooth artifact.  hq_smoothing=False keeps the baseline;
    # hq_smoothing=True activates the +138ms quality bump.  Gated upstream by
    # MainWindow (only fires for Enriques fig 1+2).
    return _marching_cubes_to_polydata(
        F, bounds, second_smooth_iter=40 if hq_smoothing else 0
    )


ENRIQUES_FIGURE_1_PARAMS = [
    ParamSpec("c", "c (mixing)", 0.1, 5.0, 1.0, 0.05,
              description="coefficient of the wxyz·(w²+x²+y²+z²) term"),
]


def enriques_figure_2(
    lam0: float = 1.0,
    lam3: float = 2.0,
    c: float = 1.0,
    n: int = 240,
    bounds: float = 1.89,
    hq_smoothing: bool = False,
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
    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_enriques_fig2_field_kernel`.  HQ-smoothing pass-through
    # stays at the generator level (kernel only fills F).  AI-8: defensive
    # int(round(n)) coercion (mirrors enriques_figure_1).
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _enriques_fig2_field_kernel(g, lam0, lam3, c, F)
    # enriques-hq-smoothing-2026q3-e1: see enriques_figure_1 for the rationale.
    return _marching_cubes_to_polydata(
        F, bounds, second_smooth_iter=40 if hq_smoothing else 0
    )


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
    bounds: float = 2.625,
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
    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_enriques_fig3_field_kernel` (Cayley quartic symmetroid).
    # AI-8: defensive int(round(n)) coercion.
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _enriques_fig3_field_kernel(g, k, F)
    return _marching_cubes_to_polydata(F, bounds)


ENRIQUES_FIGURE_3_PARAMS = [
    ParamSpec("k", "k (RHS)", 5.0, 35.0, 16.0, 0.5,
              description="(x+y+z+xy+xz+yz)² = k·xyz — avoid k=4 and k=36 (degenerate)"),
]


def enriques_figure_4(
    tau: float = 0.18,
    n: int = 220,
    bounds: float = 1.575,
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
    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_enriques_fig4_field_kernel`.  φ² and 1+2φ are scalar
    # pre-computes that stay here in the generator and pass into the kernel.
    # AI-8: defensive int(round(n)) coercion.
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    phi2 = phi * phi
    one_plus_2phi = 1.0 + 2.0 * phi

    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _enriques_fig4_field_kernel(g, tau, phi2, one_plus_2phi, F)
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
        # realtime-variety-render-e4b rect M-front-1: trimmed to ≤80 chars so
        # the status-bar composite stays inside QStatusBar's ~120-char visible
        # window even when prefixed by the Preview badge during a coarse drag
        # (CONTEXT.md §8.19).  The full conifold explanation lives in the
        # function docstring above; the warning is a UI-surfaced signal, not
        # a tutorial.
        warnings.warn(
            "ψ ≈ 1 is the conifold point; node at (1,1,1) missed — "
            "displayed mesh is the smooth complement.",
            category=RuntimeWarning,
        )
    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_dwork_field_kernel` -- the only v1 kernel with **5 (the
    # explicit x2 -> x4 -> x5 multiply chain preserves IEEE-754 op-order
    # parity with the NumPy reference at rtol=atol=1e-9).  The conifold
    # RuntimeWarning above fires BEFORE this kernel runs -- AI-14
    # preserved.  AI-8: defensive int(round(n)).
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _dwork_field_kernel(g, psi, F)
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
    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_klein_cubic_field_kernel`.  AI-8: defensive int(round(n)).
    bounds = 2.0
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _klein_cubic_field_kernel(g, z0, F)
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
    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_segre_cubic_field_kernel`.  Cubes are explicit multiplies.
    # AI-8: defensive int(round(n)).
    # bounds=2.5 (vs 2.0 elsewhere): the Segre cubic real zero set reaches r ≈ 2.1 from
    # the origin at default (a, b); a 2.0 box clips the outer lobes.
    bounds = 2.5
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _segre_cubic_field_kernel(g, a, b, F)
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
    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_two_quadrics_field_kernel`.  The 5 λ coefficients pass
    # in as scalar args (matches the e5 template's "only scalar params"
    # style; Numba supports typed tuples but scalars are simpler).  The
    # ε < 0.08 RuntimeWarning above fires BEFORE this kernel runs (AI-14).
    # AI-8: defensive int(round(n)).
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    F = np.empty((n, n, n), dtype=np.float64)
    _two_quadrics_field_kernel(
        g, p, q, mu, eps,
        lam[0], lam[1], lam[2], lam[3], lam[4], F,
    )
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
    # realtime-variety-render-e5b (CAND-2 v1): field evaluated by the Numba
    # JIT kernel `_sextic_double_solid_field_kernel`.  R⁶ is a scalar
    # pre-compute that stays here in the generator.  AI-8: defensive
    # int(round(n)).
    bounds = 2.0
    n = int(round(n))
    g = np.linspace(-bounds, bounds, n)
    r2 = R * R
    r6 = r2 * r2 * r2
    F = np.empty((n, n, n), dtype=np.float64)
    _sextic_double_solid_field_kernel(g, alpha, r6, F)
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
    # realtime-variety-render-e4b (CAND-3): per-surface `coarse_n` floors set
    # below opt 9 of 11 implicit generators into the drag-time coarse-preview
    # LOD path.  Values measured by agent-a's empirical n-sweep on the dev
    # machine (see .claude/notes/milestones/realtime-variety-render-e4b/
    # research/agent-a-brief.md §4.1); each floor is validated by
    # tests/test_coarse_n.py.  Two implicit surfaces stay opt-out:
    # `fano_two_quadrics` (ε-tube width ≈ voxel spacing at coarse n — see the
    # brief's §4.1 opt-out justification).  Hanson generators leave coarse_n=0
    # (AI-6 layer 2 — the worker dispatch's coarse-injection is a no-op).
    "K3 surface": {
        "Fermat quartic": Surface(
            "Fermat quartic", fermat_quartic, FERMAT_PARAMS, coarse_n=80,
        ),
        "Kummer surface": Surface(
            "Kummer surface", kummer_surface, KUMMER_PARAMS, coarse_n=100,
        ),
    },
    "Enriques surface": {
        "Canonical sextic  [Fig. 1]": Surface(
            "Enriques sextic (canonical, S₄ symmetry)",
            enriques_figure_1, ENRIQUES_FIGURE_1_PARAMS, coarse_n=80,
        ),
        "Diagonal λ-family  [Fig. 2]": Surface(
            "Enriques sextic (diagonal λ-family)",
            enriques_figure_2, ENRIQUES_FIGURE_2_PARAMS, coarse_n=80,
        ),
        "Cayley symmetroid  [Fig. 3]": Surface(
            "Cayley quartic symmetroid (Reye cover)",
            enriques_figure_3, ENRIQUES_FIGURE_3_PARAMS, coarse_n=80,
        ),
        "Icosahedral sextic  [Fig. 4]": Surface(
            "Barth-style icosahedral sextic (A₅ symmetry)",
            enriques_figure_4, ENRIQUES_FIGURE_4_PARAMS, coarse_n=80,
        ),
    },
    "Calabi–Yau 3-fold": {
        # realtime-variety-render-e2-s1 (CAND-8): typical_ms values measured
        # off-screen on the dev machine (pv.OFF_SCREEN=True, time.perf_counter,
        # median of 7 runs at the ParamSpec default parameters): quintic ~39 ms,
        # cubic torus ~11 ms, asymmetric ~18 ms.  All well under the 80 ms
        # fast-path threshold, so all three render continuously during drag.
        # AI-6 (e4b): Hanson generators MUST keep `coarse_n=0` (the default) —
        # they are parametric and never go through marching cubes; a coarse
        # `n` would be meaningless.
        "Hanson quintic  [Fig. 1]": Surface(
            "Hanson quintic CY cross-section (n=5)",
            calabi_yau_quintic, CALABI_YAU_QUINTIC_PARAMS,
            typical_ms=39,
        ),
        "Hanson cubic torus  [Fig. 2]": Surface(
            "Hanson cross-section (n=3, torus)",
            calabi_yau_cubic, CALABI_YAU_CUBIC_PARAMS,
            typical_ms=11,
        ),
        "Hanson asymmetric (5,3)  [Fig. 3]": Surface(
            "Hanson cross-section (n₁=5, n₂=3)",
            calabi_yau_asymmetric, CALABI_YAU_ASYMMETRIC_PARAMS,
            typical_ms=18,
        ),
        "Dwork pencil  [Fig. 4]": Surface(
            "Dwork pencil real slice (ψ-family)",
            calabi_yau_dwork, CALABI_YAU_DWORK_PARAMS, coarse_n=100,
        ),
    },
    "Fano 3-fold (ρ=1)": {
        "Klein cubic  [Fig. 1]": Surface(
            "Klein cubic threefold V₃ (PSL₂(11) symmetry)",
            fano_klein_cubic, FANO_KLEIN_CUBIC_PARAMS, coarse_n=80,
        ),
        "Segre cubic  [Fig. 2]": Surface(
            "Segre cubic (S₆ symmetry, max-nodal)",
            fano_segre_cubic, FANO_SEGRE_CUBIC_PARAMS, coarse_n=80,
        ),
        "Two-quadrics CI tube  [Fig. 3]": Surface(
            # OPT-OUT (coarse_n=0): the ε-tube width (default ε=0.18) is
            # close to the voxel spacing at any practical coarse floor — at
            # n=100 the spacing is ~0.04, which produces swiss-cheese
            # artifacts the existing ε<0.08 RuntimeWarning already calls out
            # at production `n`.  Coarse-LOD would render a topologically
            # misleading drag preview here, so this surface stays release-
            # only (e4b agent-a brief §4.1).
            "Two-quadrics CI tube V₄ (ε-tube around Q₁∩Q₂, not the actual CI)",
            fano_two_quadrics, FANO_TWO_QUADRICS_PARAMS,
        ),
        "Sextic double solid  [Fig. 4]": Surface(
            "Sextic double solid V₁ (sign-flipped Fermat branch)",
            fano_sextic_double_solid, FANO_SEXTIC_DOUBLE_SOLID_PARAMS,
            coarse_n=80,
        ),
    },
}

# ---------------------------------------------------------------------------
# Tooltips for the variety / subtype dropdowns (used by the GUI)
# ---------------------------------------------------------------------------

VARIETY_TOOLTIPS: dict[str, str] = {
    # realtime-variety-render-e4b (CAND-3): each family's tooltip closes with
    # a single sentence about the drag-time coarse-preview LOD behavior — the
    # AI-15 disclosure for users who hover the variety combo before/instead of
    # watching the status-bar Preview badge (CONTEXT.md §8.19).  Hanson CY3
    # surfaces use the e2 fast-path (full at every tick); the K3, Enriques,
    # Dwork, and Fano implicit subtypes use the e4b coarse-preview LOD.
    "K3 surface": (
        "A K3 surface is a compact complex surface with trivial canonical bundle "
        "and first Betti number 0. K3 surfaces are the 2-dimensional analogue of "
        "elliptic curves and play a central role in mirror symmetry. "
        "Drag-time renders use a coarse preview (n≈80–100); slider release "
        "re-renders at full resolution."
    ),
    "Enriques surface": (
        "An Enriques surface is the quotient of a K3 surface by a fixed-point-free "
        "involution. It has Euler number 12 and 2K=0. Four representative real "
        "affine models are provided here. "
        "Drag-time renders use a coarse preview (n=80); slider release re-renders "
        "at full resolution."
    ),
    "Calabi–Yau 3-fold": (
        "A Calabi–Yau 3-fold is a 6-real-dimensional space — it cannot be embedded "
        "in ℝ³. Each entry below is a 2D shadow, slice, or projection (in the "
        "Hanson-1994 tradition that produced the iconic 'Elegant Universe' image), "
        "not the 3-fold itself. "
        "Hanson parametric figures render at full resolution every drag tick; "
        "the Dwork pencil uses a coarse preview (n=100) during drag."
    ),
    "Fano 3-fold (ρ=1)": (
        "A smooth Fano 3-fold of Picard rank 1 (Iskovskikh's 'prime Fano "
        "threefold') is 6-real-dimensional. Each entry below is a 2D real "
        "slice obtained by fixing one or two ambient projective coordinates. "
        "The visualization tradition is essentially nonexistent — these are "
        "novel renderings. "
        "Most figures use a coarse preview (n=80) during drag and re-render "
        "at full resolution on release; the two-quadrics ε-tube is release-"
        "only (its topology is too fragile for any practical coarse floor)."
    ),
}

# cleanup-deferred-findings-2026q3-e1 item 3 (M7 closure): per-subtype
# tooltip render-mode disclosures.  Three classes per the realtime-
# variety-render-e4b LOD architecture:
#   _LOD_NOTE_COARSE        — implicit surfaces with coarse_n > 0 (the
#                              default).  Drag fires a coarse-preview
#                              render at the lower grid (n=80 or n=100);
#                              release fires the full-resolution render.
#                              AI-15 Preview badge surfaces the fidelity
#                              state in the status bar.
#   _LOD_NOTE_HANSON        — Hanson parametric family.  The e2 typical_ms
#                              fast-path renders at full resolution on
#                              every debounced tick (no coarse preview —
#                              parametric meshes are too cheap to need
#                              an LOD downgrade).
#   _LOD_NOTE_RELEASE_ONLY  — Two-quadrics CI tube only (coarse_n=0
#                              opt-out per CONTEXT.md §4.4a — the f =
#                              Q₁²+Q₂²−ε² tube degenerates fast under
#                              coarse marching cubes).
_LOD_NOTE_COARSE = " · Drag = coarse preview; release = full render."
_LOD_NOTE_HANSON = (
    " · Renders full at every debounced drag tick (~80 ms; parametric)."
)
_LOD_NOTE_RELEASE_ONLY = (
    " · Release-only render (topology precision-sensitive; coarse drag "
    "preview would degrade the mesh)."
)

SUBTYPE_TOOLTIPS: dict[str, str] = {
    # K3
    "Fermat quartic": (
        "Fig. — | x⁴+y⁴+z⁴+… = c | "
        "3-parameter deformation of the classical Fermat quartic. "
        "Full octahedral O_h symmetry at α=β=γ=0."
        + _LOD_NOTE_COARSE
    ),
    "Kummer surface": (
        "Fig. — | (x²+y²+z²−μ²)² = λ·pqrs | "
        "Classic 16-nodal quartic (Hudson form). "
        "Smooth in the range 1 < μ² < 3."
        + _LOD_NOTE_COARSE
    ),
    # Enriques
    "Canonical sextic  [Fig. 1]": (
        "Figure 1 · S₄ tetrahedral symmetry | "
        "The Enriques 1896 canonical sextic: "
        "x²y²+x²z²+y²z²+x²y²z² + c·xyz·(1+x²+y²+z²) = 0."
        + _LOD_NOTE_COARSE
    ),
    "Diagonal λ-family  [Fig. 2]": (
        "Figure 2 · S₄→S₃ symmetry breaking | "
        "Dolgachev's λ-family: independent weights on the four "
        "'missing-one-variable' degree-6 monomials."
        + _LOD_NOTE_COARSE
    ),
    "Cayley symmetroid  [Fig. 3]": (
        "Figure 3 · Reye congruence model | "
        "Cayley quartic symmetroid: (x+y+z+xy+xz+yz)² = k·xyz. "
        "Historically the first Enriques surface (Reye 1882)."
        + _LOD_NOTE_COARSE
    ),
    "Icosahedral sextic  [Fig. 4]": (
        "Figure 4 · A₅ icosahedral symmetry | "
        "Endrass-normalized variant of Barth's 65-nodal sextic; "
        "τ≈0.18 gives Enriques-compatible node count."
        + _LOD_NOTE_COARSE
    ),
    # Calabi–Yau 3-fold
    "Hanson quintic  [Fig. 1]": (
        "Figure 1 · Hanson 1994, Z₅×Z₅ symmetry | "
        "The iconic CY₃ cross-section: z₁⁵ + z₂⁵ = 1 in C², projected to ℝ³. "
        "This is the image on the cover of 'The Elegant Universe.'"
        + _LOD_NOTE_HANSON
    ),
    "Hanson cubic torus  [Fig. 2]": (
        "Figure 2 · Hanson n=3 (torus) | "
        "z₁³ + z₂³ = 1, same construction with lower exponent. "
        "Genus 1 — visually a 9-patch torus."
        + _LOD_NOTE_HANSON
    ),
    "Hanson asymmetric (5,3)  [Fig. 3]": (
        "Figure 3 · Hanson asymmetric construction | "
        "z₁⁵ + z₂³ = 1 — Hanson's own (n₁ ≠ n₂) extension. "
        "Breaks the visual symmetry of the quintic."
        + _LOD_NOTE_HANSON
    ),
    "Dwork pencil  [Fig. 4]": (
        "Figure 4 · Implicit Dwork-pencil real slice | "
        "x⁵+y⁵+z⁵+2 = 5ψ·xyz. The ψ slider sweeps the canonical "
        "one-parameter CY₃ family; ψ=1 is the (real) conifold point; "
        "the five conifold points in ℂ are the fifth roots of unity."
        + _LOD_NOTE_COARSE
    ),
    # Fano 3-folds (Picard rank 1)
    "Klein cubic  [Fig. 1]": (
        "Figure 1 · PSL₂(11) symmetry, index 2 | "
        "Klein cubic V₃: V²W+W²X+X²Y+Y²Z+Z²V=0. Slice by Z=z₀. "
        "The unique smooth cubic 3-fold with order-660 symmetry."
        + _LOD_NOTE_COARSE
    ),
    "Segre cubic  [Fig. 2]": (
        "Figure 2 · S₆ symmetry of the parent (broken in the slice) | "
        "Σxᵢ=0 ∧ Σxᵢ³=0 in P⁵, eliminating x₅ and slicing by (x₃,x₄)=(a,b). "
        "Maximally nodal cubic 3-fold (10 nodes in the parent variety; "
        "visible singular points in the slice depend on (a,b))."
        + _LOD_NOTE_COARSE
    ),
    "Two-quadrics CI tube  [Fig. 3]": (
        "Figure 3 · Sum-of-squares tube of V₄, index 2 | "
        "f = Q₁²+Q₂²−ε² approximates the codim-2 intersection. "
        "Diagonal pencil with 5 distinct λ values."
        + _LOD_NOTE_RELEASE_ONLY
    ),
    "Sextic double solid  [Fig. 4]": (
        "Figure 4 · Index 1, genus 2 (Iskovskikh family 1-1) | "
        "z² + x⁶+y⁶+α·x²y²(x²+y²) = R⁶. Sign-flipped Fermat branch "
        "gives a closed compact double cover; α deforms the sextic equator."
        + _LOD_NOTE_COARSE
    ),
}
