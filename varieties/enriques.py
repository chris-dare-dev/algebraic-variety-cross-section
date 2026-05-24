"""AVC ENRIQUES variety generators.

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



