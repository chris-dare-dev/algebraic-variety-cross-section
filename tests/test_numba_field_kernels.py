"""Numerical-equivalence tests for the realtime-variety-render-e5 Numba kernels.

Qt-free (AI-2): pure NumPy + Numba, no QApplication, no pyvista, no Qt.

e5 (CAND-2) replaced the NumPy meshgrid-broadcasting field evaluation in
``fermat_quartic`` and ``enriques_figure_1`` with ``@njit(parallel=True)``
kernels. These tests pin the contract: each kernel must produce a field
array numerically identical (to floating-point tolerance) to the *exact
former NumPy expression* — which is reproduced verbatim below as the
reference, so the test is independent of the post-e5 generator code.

Tolerance: ``rtol=atol=1e-9``. The kernel transcribes the polynomial in the
identical operator order, so per-voxel evaluation should be near bit-exact;
1e-9 leaves margin for any IEEE-754 op-fusion / arm-vs-x86 ULP drift while
still failing loudly on a real transcription bug (a wrong sign, a dropped
term, or a swapped parameter shifts the field by orders of magnitude).
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from surfaces import _enriques_fig1_field_kernel, _fermat_field_kernel


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
