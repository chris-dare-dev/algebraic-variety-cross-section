"""Numerical-equivalence tests for the realtime-variety-render-e5/e5b Numba kernels.

Qt-free (AI-2): pure NumPy + Numba, no QApplication, no pyvista, no Qt.

e5 (CAND-2 v0) replaced the NumPy meshgrid-broadcasting field evaluation in
``fermat_quartic`` and ``enriques_figure_1`` with ``@njit(parallel=True)``
kernels.  e5b (CAND-2 v1) extends the same pattern to the remaining 9
implicit generators: ``kummer_surface``, ``enriques_figure_2/3/4``,
``calabi_yau_dwork``, ``fano_klein_cubic``, ``fano_segre_cubic``,
``fano_two_quadrics``, ``fano_sextic_double_solid``.

These tests pin the contract: each kernel must produce a field array
numerically identical (to floating-point tolerance) to the *exact former
NumPy expression* — which is reproduced verbatim below as the reference,
so the test is independent of the post-e5/e5b generator code.

Tolerance: ``rtol=atol=1e-9``. The kernel transcribes the polynomial in the
identical operator order, so per-voxel evaluation should be near bit-exact;
1e-9 leaves margin for any IEEE-754 op-fusion / arm-vs-x86 ULP drift while
still failing loudly on a real transcription bug (a wrong sign, a dropped
term, or a swapped parameter shifts the field by orders of magnitude).

Axis-mapping note: most of the field expressions are *fully symmetric* under
permutations of (x, y, z) — a value-comparison test therefore CANNOT detect
an ``(i, j, k) -> (g[k], g[j], g[i])`` axis-transposition bug for those
kernels.  This is not a coverage hole: a transposed evaluation of a symmetric
field contours to the exact same isosurface, so the bug is harmless by
construction.  The asymmetric kernels — ``_klein_cubic_field_kernel`` (Klein
cubic threefold slice, ``x + x²y + y²z + z₀z² + z₀²``) and
``_sextic_double_solid_field_kernel`` (where ``Z²`` plays a different role
than ``X⁶``/``Y⁶``) — *would* surface an axis-swap bug under their
parametrize blocks, providing implicit coverage for the whole family.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from surfaces import (
    _dwork_field_kernel,
    _enriques_fig1_field_kernel,
    _enriques_fig2_field_kernel,
    _enriques_fig3_field_kernel,
    _enriques_fig4_field_kernel,
    _fermat_field_kernel,
    _klein_cubic_field_kernel,
    _kummer_field_kernel,
    _segre_cubic_field_kernel,
    _sextic_double_solid_field_kernel,
    _two_quadrics_field_kernel,
)


# ---------------------------------------------------------------------------
# NumPy reference expressions — verbatim copies of the pre-e5 surfaces.py
# field blocks. Do NOT "simplify" these: they are the contract the kernels
# must reproduce.
# ---------------------------------------------------------------------------

def _fermat_ref(g, alpha, beta, gamma, c):
    """Pre-e5 NumPy field expression from ``fermat_quartic``."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    F = (
        X2 * X2 + Y2 * Y2 + Z2 * Z2
        + alpha * (X2 * Y2 + Y2 * Z2 + Z2 * X2)
        + beta * (X * Y * Z) * (X + Y + Z)
        + gamma * (X2 + Y2 + Z2)
        - c
    )
    return np.clip(F, -200.0, 200.0)


def _enriques_ref(g, c):
    """Pre-e5 NumPy field expression from ``enriques_figure_1``."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    F = (
        X2 * Y2 + X2 * Z2 + Y2 * Z2 + X2 * Y2 * Z2
        + c * (X * Y * Z) * (1.0 + X2 + Y2 + Z2)
    )
    return np.clip(F, -10.0, 10.0)


_RTOL = 1e-9
_ATOL = 1e-9
_N = 32  # small grid — keeps the JIT-warm test fast


# ---------------------------------------------------------------------------
# Fermat quartic kernel — defaults, a mixed interior point, an extreme point
# ---------------------------------------------------------------------------

# (alpha, beta, gamma, c) — the 3rd point drives the field past the ±200 clip.
_FERMAT_POINTS = [
    (0.0, 0.0, 0.0, 1.0),       # slider defaults
    (-0.5, 1.5, -5.0, 10.0),    # mixed interior point
    (-1.0, 3.0, -15.0, 30.0),   # slider extremes — exercises the clip caps
]


@pytest.mark.parametrize("alpha,beta,gamma,c", _FERMAT_POINTS)
def test_fermat_field_kernel_matches_numpy(alpha, beta, gamma, c):
    """The Numba Fermat kernel reproduces the pre-e5 NumPy field exactly."""
    g = np.linspace(-2.5, 2.5, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _fermat_field_kernel(g, alpha, beta, gamma, c, out)
    ref = _fermat_ref(g, alpha, beta, gamma, c)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Fermat kernel diverges from the NumPy reference at "
        f"(alpha={alpha}, beta={beta}, gamma={gamma}, c={c}); "
        f"max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_fermat_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-200, 200]."""
    g = np.linspace(-2.5, 2.5, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _fermat_field_kernel(g, -1.0, 3.0, -15.0, 30.0, out)
    assert out.min() >= -200.0 and out.max() <= 200.0


# ---------------------------------------------------------------------------
# Enriques canonical sextic kernel — default + both slider extremes
# ---------------------------------------------------------------------------

_ENRIQUES_C = [1.0, 0.1, 5.0]  # default, slider min-ish, slider max


@pytest.mark.parametrize("c", _ENRIQUES_C)
def test_enriques_fig1_field_kernel_matches_numpy(c):
    """The Numba Enriques kernel reproduces the pre-e5 NumPy field exactly."""
    g = np.linspace(-1.89, 1.89, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig1_field_kernel(g, c, out)
    ref = _enriques_ref(g, c)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Enriques kernel diverges from the NumPy reference at c={c}; "
        f"max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_enriques_fig1_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-10, 10]."""
    g = np.linspace(-1.89, 1.89, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig1_field_kernel(g, 5.0, out)
    assert out.min() >= -10.0 and out.max() <= 10.0


def test_kernels_have_a_zero_crossing_at_defaults():
    """Sanity: at default params each field straddles 0 (a real surface
    exists), so the downstream _marching_cubes_to_polydata ValueError guard
    is not tripped — the kernels feed a non-degenerate field."""
    gf = np.linspace(-2.5, 2.5, _N)
    of = np.empty((_N, _N, _N), dtype=np.float64)
    _fermat_field_kernel(gf, 0.0, 0.0, 0.0, 1.0, of)
    assert of.min() < 0.0 < of.max()

    ge = np.linspace(-1.89, 1.89, _N)
    oe = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig1_field_kernel(ge, 1.0, oe)
    assert oe.min() < 0.0 < oe.max()

    # Kummer at the classic 16-nodal default mu²=1.3.
    gk = np.linspace(-2.6, 2.6, _N)
    ok = np.empty((_N, _N, _N), dtype=np.float64)
    lam_def = _kummer_lambda(1.3)
    _kummer_field_kernel(gk, 1.3, lam_def, np.sqrt(2.0), ok)
    assert ok.min() < 0.0 < ok.max()

    # Enriques figure 2 (Dolgachev λ-family) defaults.
    g2 = np.linspace(-1.89, 1.89, _N)
    o2 = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig2_field_kernel(g2, 1.0, 2.0, 1.0, o2)
    assert o2.min() < 0.0 < o2.max()

    # Enriques figure 3 (Cayley quartic) at k=16.0.
    g3 = np.linspace(-2.625, 2.625, _N)
    o3 = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig3_field_kernel(g3, 16.0, o3)
    assert o3.min() < 0.0 < o3.max()

    # Enriques figure 4 (Endrass icosahedral) at τ=0.18.
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    phi2 = phi * phi
    one_plus_2phi = 1.0 + 2.0 * phi
    g4 = np.linspace(-1.575, 1.575, _N)
    o4 = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig4_field_kernel(g4, 0.18, phi2, one_plus_2phi, o4)
    assert o4.min() < 0.0 < o4.max()

    # Dwork pencil at ψ=0.5 (well away from the ψ≈1 conifold warning).
    gd = np.linspace(-1.8, 1.8, _N)
    od = np.empty((_N, _N, _N), dtype=np.float64)
    _dwork_field_kernel(gd, 0.5, od)
    assert od.min() < 0.0 < od.max()

    # Klein cubic slice at z₀=0.4.
    gkc = np.linspace(-2.0, 2.0, _N)
    okc = np.empty((_N, _N, _N), dtype=np.float64)
    _klein_cubic_field_kernel(gkc, 0.4, okc)
    assert okc.min() < 0.0 < okc.max()

    # Segre cubic at (a, b)=(0.3, -0.4).
    gs = np.linspace(-2.5, 2.5, _N)
    os_ = np.empty((_N, _N, _N), dtype=np.float64)
    _segre_cubic_field_kernel(gs, 0.3, -0.4, os_)
    assert os_.min() < 0.0 < os_.max()

    # Two-quadrics ε-tube at defaults (eps=0.18, comfortably above the
    # ε<0.08 voxel-resolution warning floor).
    g2q = np.linspace(-2.0, 2.0, _N)
    o2q = np.empty((_N, _N, _N), dtype=np.float64)
    _two_quadrics_field_kernel(
        g2q, 0.3, -0.2, 0.5, 0.18,
        -0.5, 0.0, 0.5, 1.0, 1.5, o2q,
    )
    assert o2q.min() < 0.0 < o2q.max()

    # Sextic double solid at (R, α)=(1.2, 0.0); r6 pre-computed.
    g6 = np.linspace(-2.0, 2.0, _N)
    o6 = np.empty((_N, _N, _N), dtype=np.float64)
    r2_def = 1.2 * 1.2
    r6_def = r2_def * r2_def * r2_def
    _sextic_double_solid_field_kernel(g6, 0.0, r6_def, o6)
    assert o6.min() < 0.0 < o6.max()


# ===========================================================================
# realtime-variety-render-e5b (CAND-2 v1) — 9 remaining implicit kernels
# ===========================================================================
#
# Pattern repeats e5 v0: NumPy reference verbatim from the pre-e5b generator
# body, three slider-realistic parameter points (default / mid / extreme),
# `np.allclose` at rtol=atol=1e-9, plus per-kernel clip-bounds assertion.
#
# Bounds match the generator's own `bounds=…` argument so the test grid
# spans the same range the production code samples on.  Kernel-side
# `_N=32` keeps the JIT-cold cost of each parametrize point ≲ 0.1 s
# (the kernels reuse the e5 cache infrastructure — `_kummer_field_kernel`
# etc. each compile once per machine, then load from `__pycache__/*.nbc`).


# ---------------------------------------------------------------------------
# NumPy reference expressions — verbatim copies of the pre-e5b surfaces.py
# field blocks. Do NOT "simplify" these: they are the contract the kernels
# must reproduce.
# ---------------------------------------------------------------------------

def _kummer_lambda(mu_squared):
    """λ(μ²) = (3μ² − 1) / (3 − μ²) — the canonical Hudson coupling."""
    return (3.0 * mu_squared - 1.0) / (3.0 - mu_squared)


def _kummer_ref(g, mu_squared, lam, sqrt2):
    """Pre-e5b NumPy field expression from ``kummer_surface``."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    sqrt2_X = sqrt2 * X
    sqrt2_Y = sqrt2 * Y
    p_ = 1.0 - Z - sqrt2_X
    q_ = 1.0 - Z + sqrt2_X
    r_ = 1.0 + Z + sqrt2_Y
    s_ = 1.0 + Z - sqrt2_Y
    base = X2 + Y2 + Z2 - mu_squared
    F = base * base - lam * p_ * q_ * r_ * s_
    return np.clip(F, -50.0, 50.0)


def _enriques_fig2_ref(g, lam0, lam3, c):
    """Pre-e5b NumPy field expression from ``enriques_figure_2``."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    F = (
        lam0 * X2 * Y2 * Z2
        + 1.0 * Y2 * Z2
        + 1.0 * X2 * Z2
        + lam3 * X2 * Y2
        + c * (X * Y * Z) * (1.0 + X2 + Y2 + Z2)
    )
    return np.clip(F, -10.0, 10.0)


def _enriques_fig3_ref(g, k):
    """Pre-e5b NumPy field expression from ``enriques_figure_3`` (Cayley)."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    s = X + Y + Z + X * Y + X * Z + Y * Z
    F = s * s - k * X * Y * Z
    return np.clip(F, -50.0, 50.0)


def _enriques_fig4_ref(g, tau):
    """Pre-e5b NumPy field expression from ``enriques_figure_4`` (Endrass)."""
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    phi2 = phi * phi
    one_plus_2phi = 1.0 + 2.0 * phi
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    t0 = phi2 * X2 - Y2
    t1 = phi2 * Y2 - Z2
    t2 = phi2 * Z2 - X2
    P = 4.0 * t0 * t1 * t2
    inner = X2 + Y2 + Z2 - 1.0
    Q = one_plus_2phi * inner * inner
    F = P - tau * Q
    return np.clip(F, -20.0, 20.0)


def _dwork_ref(g, psi):
    """Pre-e5b NumPy field expression from ``calabi_yau_dwork``."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    X4, Y4, Z4 = X2 * X2, Y2 * Y2, Z2 * Z2
    X5, Y5, Z5 = X4 * X, Y4 * Y, Z4 * Z
    F = X5 + Y5 + Z5 + 2.0 - 5.0 * psi * X * Y * Z
    return np.clip(F, -100.0, 100.0)


def _klein_cubic_ref(g, z0):
    """Pre-e5b NumPy field expression from ``fano_klein_cubic``."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2 = X * X, Y * Y
    F = X + X2 * Y + Y2 * Z + z0 * Z * Z + z0 * z0
    return np.clip(F, -50.0, 50.0)


def _segre_cubic_ref(g, a, b):
    """Pre-e5b NumPy field expression from ``fano_segre_cubic``."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X3 = X * X * X
    Y3 = Y * Y * Y
    Z3 = Z * Z * Z
    a3 = a * a * a
    b3 = b * b * b
    s = X + Y + Z + a + b
    s3 = s * s * s
    F = X3 + Y3 + Z3 + a3 + b3 - s3
    return np.clip(F, -1000.0, 1000.0)


def _two_quadrics_ref(g, p, q, mu, eps, lam0, lam1, lam2, lam3, lam4):
    """Pre-e5b NumPy field expression from ``fano_two_quadrics``."""
    p2 = p * p
    q2 = q * q
    eps2 = eps * eps
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    Q1 = X2 + Y2 + Z2 + p2 + q2 - 1.0
    Q2 = (lam0 * X2 + lam1 * Y2 + lam2 * Z2
          + lam3 * p2 + lam4 * q2 - mu)
    F = Q1 * Q1 + Q2 * Q2 - eps2
    return np.clip(F, -200.0, 200.0)


def _sextic_double_solid_ref(g, alpha, r6):
    """Pre-e5b NumPy field expression from ``fano_sextic_double_solid``."""
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2 = X * X, Y * Y
    X6 = X2 * X2 * X2
    Y6 = Y2 * Y2 * Y2
    F = (
        Z * Z
        + X6
        + Y6
        + alpha * X2 * Y2 * (X2 + Y2)
        - r6
    )
    return np.clip(F, -200.0, 200.0)


# ---------------------------------------------------------------------------
# Kummer kernel — defaults, low-μ², high-μ² near pole
# ---------------------------------------------------------------------------

# (mu_squared,) — slider domain is (1/3, 3) with 1<μ²<3 the 16-nodal regime.
# μ²=0.5 sits in the small-μ regime; μ²=2.9 drives lam=77 → heavy clipping.
_KUMMER_POINTS = [1.3, 0.5, 2.9]


@pytest.mark.parametrize("mu_squared", _KUMMER_POINTS)
def test_kummer_field_kernel_matches_numpy(mu_squared):
    """The Numba Kummer kernel reproduces the pre-e5b NumPy field exactly."""
    g = np.linspace(-2.6, 2.6, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    lam = _kummer_lambda(mu_squared)
    sqrt2 = np.sqrt(2.0)
    _kummer_field_kernel(g, mu_squared, lam, sqrt2, out)
    ref = _kummer_ref(g, mu_squared, lam, sqrt2)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Kummer kernel diverges from the NumPy reference at "
        f"mu_squared={mu_squared} (lam={lam:.3f}); "
        f"max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_kummer_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-50, 50]."""
    g = np.linspace(-2.6, 2.6, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    # μ²=2.9 puts lam at ~77, which dominates the biquadratic and saturates
    # the clip caps across most of the box — the strongest stressor in the
    # slider domain.
    _kummer_field_kernel(g, 2.9, _kummer_lambda(2.9), np.sqrt(2.0), out)
    assert out.min() >= -50.0 and out.max() <= 50.0


# ---------------------------------------------------------------------------
# Enriques figure 2 (Dolgachev λ-family) kernel
# ---------------------------------------------------------------------------

# (lam0, lam3, c) — default / slider-min-ish / slider-max corners.
_ENRIQUES_FIG2_POINTS = [
    (1.0, 2.0, 1.0),   # slider defaults
    (0.1, 0.1, 0.1),   # all-minimum corner
    (4.0, 4.0, 5.0),   # all-maximum corner — exercises the ±10 clip
]


@pytest.mark.parametrize("lam0,lam3,c", _ENRIQUES_FIG2_POINTS)
def test_enriques_fig2_field_kernel_matches_numpy(lam0, lam3, c):
    """The Numba Enriques fig 2 kernel reproduces the pre-e5b NumPy field."""
    g = np.linspace(-1.89, 1.89, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig2_field_kernel(g, lam0, lam3, c, out)
    ref = _enriques_fig2_ref(g, lam0, lam3, c)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Enriques fig 2 kernel diverges from the NumPy reference at "
        f"(lam0={lam0}, lam3={lam3}, c={c}); "
        f"max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_enriques_fig2_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-10, 10]."""
    g = np.linspace(-1.89, 1.89, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig2_field_kernel(g, 4.0, 4.0, 5.0, out)
    assert out.min() >= -10.0 and out.max() <= 10.0


# ---------------------------------------------------------------------------
# Enriques figure 3 (Cayley quartic symmetroid) kernel
# ---------------------------------------------------------------------------

# k slider range is 5.0–35.0, default 16.0 (k=4 and k=36 are degenerate;
# both sit outside the slider domain).  8 and 30 bracket the smooth-look
# range.
_ENRIQUES_FIG3_K = [16.0, 8.0, 30.0]


@pytest.mark.parametrize("k", _ENRIQUES_FIG3_K)
def test_enriques_fig3_field_kernel_matches_numpy(k):
    """The Numba Cayley quartic kernel reproduces the pre-e5b NumPy field."""
    g = np.linspace(-2.625, 2.625, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig3_field_kernel(g, k, out)
    ref = _enriques_fig3_ref(g, k)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Cayley quartic kernel diverges from the NumPy reference at k={k}; "
        f"max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_enriques_fig3_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-50, 50]."""
    g = np.linspace(-2.625, 2.625, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig3_field_kernel(g, 30.0, out)
    assert out.min() >= -50.0 and out.max() <= 50.0


# ---------------------------------------------------------------------------
# Enriques figure 4 (Endrass-icosahedral sextic) kernel
# ---------------------------------------------------------------------------

# τ slider range 0.05–1.0, default 0.18 (Enriques-compatible node count).
_ENRIQUES_FIG4_TAU = [0.18, 0.05, 1.0]


@pytest.mark.parametrize("tau", _ENRIQUES_FIG4_TAU)
def test_enriques_fig4_field_kernel_matches_numpy(tau):
    """The Numba Endrass sextic kernel reproduces the pre-e5b NumPy field."""
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    phi2 = phi * phi
    one_plus_2phi = 1.0 + 2.0 * phi
    g = np.linspace(-1.575, 1.575, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig4_field_kernel(g, tau, phi2, one_plus_2phi, out)
    ref = _enriques_fig4_ref(g, tau)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Endrass sextic kernel diverges from the NumPy reference at "
        f"tau={tau}; max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_enriques_fig4_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-20, 20]."""
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    phi2 = phi * phi
    one_plus_2phi = 1.0 + 2.0 * phi
    g = np.linspace(-1.575, 1.575, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _enriques_fig4_field_kernel(g, 1.0, phi2, one_plus_2phi, out)
    assert out.min() >= -20.0 and out.max() <= 20.0


# ---------------------------------------------------------------------------
# Dwork-pencil quintic kernel (the only v1 kernel with explicit **5)
# ---------------------------------------------------------------------------

# ψ slider range -2.5..2.5, default 0.5.  Skip ψ ≈ 1 to avoid the conifold
# RuntimeWarning during pure-kernel equivalence checks (the warning fires
# in the generator, not the kernel — but we test the kernel in isolation
# here, so avoiding the parameter is just cleaner).
_DWORK_PSI = [0.5, 0.0, 2.5]


@pytest.mark.parametrize("psi", _DWORK_PSI)
def test_dwork_field_kernel_matches_numpy(psi):
    """The Numba Dwork kernel reproduces the pre-e5b NumPy field exactly."""
    g = np.linspace(-1.8, 1.8, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _dwork_field_kernel(g, psi, out)
    ref = _dwork_ref(g, psi)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Dwork kernel diverges from the NumPy reference at psi={psi}; "
        f"max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_dwork_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-100, 100]."""
    g = np.linspace(-1.8, 1.8, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _dwork_field_kernel(g, 2.5, out)
    assert out.min() >= -100.0 and out.max() <= 100.0


# ---------------------------------------------------------------------------
# Klein cubic threefold slice kernel — the only ASYMMETRIC kernel in v1
# (so this parametrize block also implicitly covers axis-transposition bugs).
# ---------------------------------------------------------------------------

# z₀ slider range -1.0..1.0, default 0.4.
_KLEIN_Z0 = [0.4, -1.0, 1.0]


@pytest.mark.parametrize("z0", _KLEIN_Z0)
def test_klein_cubic_field_kernel_matches_numpy(z0):
    """The Numba Klein-cubic kernel reproduces the pre-e5b NumPy field."""
    g = np.linspace(-2.0, 2.0, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _klein_cubic_field_kernel(g, z0, out)
    ref = _klein_cubic_ref(g, z0)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Klein cubic kernel diverges from the NumPy reference at z0={z0}; "
        f"max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_klein_cubic_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-50, 50]."""
    g = np.linspace(-2.0, 2.0, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _klein_cubic_field_kernel(g, 1.0, out)
    assert out.min() >= -50.0 and out.max() <= 50.0


# ---------------------------------------------------------------------------
# Segre cubic slice kernel
# ---------------------------------------------------------------------------

# (a, b) — defaults plus the diagonal (1,1) corner that drives the s³ term
# hardest, plus the (0,0) special slice.
_SEGRE_POINTS = [
    (0.3, -0.4),   # slider defaults
    (0.0, 0.0),    # both slices at the origin
    (1.0, 1.0),    # both at slider max — heaviest s³ contribution
]


@pytest.mark.parametrize("a,b", _SEGRE_POINTS)
def test_segre_cubic_field_kernel_matches_numpy(a, b):
    """The Numba Segre cubic kernel reproduces the pre-e5b NumPy field."""
    g = np.linspace(-2.5, 2.5, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _segre_cubic_field_kernel(g, a, b, out)
    ref = _segre_cubic_ref(g, a, b)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Segre cubic kernel diverges from the NumPy reference at "
        f"(a={a}, b={b}); max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_segre_cubic_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-1000, 1000]."""
    g = np.linspace(-2.5, 2.5, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    _segre_cubic_field_kernel(g, 1.0, 1.0, out)
    assert out.min() >= -1000.0 and out.max() <= 1000.0


# ---------------------------------------------------------------------------
# Two-quadrics ε-tube kernel (Fano V_4)
# ---------------------------------------------------------------------------

# (p, q, mu, eps) — slider domain.  All ε values stay ≥ 0.08 to avoid the
# voxel-resolution RuntimeWarning (the warning fires in the generator BEFORE
# the kernel runs, but the kernel itself is well-defined for ε≥0).
_TWO_QUADRICS_POINTS = [
    (0.3, -0.2, 0.5, 0.18),   # slider defaults
    (0.0, 0.0, 0.0, 0.10),    # all slices at origin, thin tube near floor
    (1.0, 1.0, 1.5, 0.40),    # all at slider max — heaviest stressor
]


@pytest.mark.parametrize("p,q,mu,eps", _TWO_QUADRICS_POINTS)
def test_two_quadrics_field_kernel_matches_numpy(p, q, mu, eps):
    """The Numba two-quadrics kernel reproduces the pre-e5b NumPy field."""
    g = np.linspace(-2.0, 2.0, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    # Same hard-coded λ tuple as the generator.
    lam = (-0.5, 0.0, 0.5, 1.0, 1.5)
    _two_quadrics_field_kernel(
        g, p, q, mu, eps,
        lam[0], lam[1], lam[2], lam[3], lam[4], out,
    )
    ref = _two_quadrics_ref(
        g, p, q, mu, eps,
        lam[0], lam[1], lam[2], lam[3], lam[4],
    )
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Two-quadrics kernel diverges from the NumPy reference at "
        f"(p={p}, q={q}, mu={mu}, eps={eps}); "
        f"max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_two_quadrics_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-200, 200]."""
    g = np.linspace(-2.0, 2.0, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    lam = (-0.5, 0.0, 0.5, 1.0, 1.5)
    _two_quadrics_field_kernel(
        g, 1.0, 1.0, 1.5, 0.40,
        lam[0], lam[1], lam[2], lam[3], lam[4], out,
    )
    assert out.min() >= -200.0 and out.max() <= 200.0


# ---------------------------------------------------------------------------
# Sextic double solid kernel (Fano V_1 branch)
# ---------------------------------------------------------------------------

# (R, alpha) — defaults plus shrink-the-equator and large-α stressor.
_SEXTIC_POINTS = [
    (1.2, 0.0),    # slider defaults, full octahedral symmetry at α=0
    (0.6, -2.0),   # small R, asymmetric α
    (2.0, 2.0),    # large R + α — exercises the ±200 clip cap on lobes
]


@pytest.mark.parametrize("R,alpha", _SEXTIC_POINTS)
def test_sextic_double_solid_field_kernel_matches_numpy(R, alpha):
    """The Numba sextic double solid kernel reproduces the pre-e5b NumPy field."""
    g = np.linspace(-2.0, 2.0, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    r2 = R * R
    r6 = r2 * r2 * r2
    _sextic_double_solid_field_kernel(g, alpha, r6, out)
    ref = _sextic_double_solid_ref(g, alpha, r6)
    assert np.allclose(out, ref, rtol=_RTOL, atol=_ATOL), (
        f"Sextic double solid kernel diverges from the NumPy reference at "
        f"(R={R}, alpha={alpha}); max|err|={np.max(np.abs(out - ref)):.3e}"
    )


def test_sextic_double_solid_field_kernel_respects_clip_bounds():
    """The kernel's folded-in clip never lets a value escape [-200, 200]."""
    g = np.linspace(-2.0, 2.0, _N)
    out = np.empty((_N, _N, _N), dtype=np.float64)
    r2 = 2.0 * 2.0
    r6 = r2 * r2 * r2  # R=2 → R⁶=64
    _sextic_double_solid_field_kernel(g, 2.0, r6, out)
    assert out.min() >= -200.0 and out.max() <= 200.0
