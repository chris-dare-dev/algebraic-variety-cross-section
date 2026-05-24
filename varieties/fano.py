"""AVC FANO variety generators.

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


