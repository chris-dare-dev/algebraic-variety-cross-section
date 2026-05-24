"""AVC CALABI YAU variety generators.

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


