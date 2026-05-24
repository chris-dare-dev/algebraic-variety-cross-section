"""Numba @njit field kernels for AVC implicit-surface generators.

Per restructure-feature-subpackages-2026q2-r2 Batch 6: extracted from surfaces.py
(originally lines L201-L572, 11 kernels for the 11 implicit varieties).

IMPORTANT INVARIANT (per design-adversary v2 HIGH-2 + refactor-pattern brief §5.1):
`numba.config.THREADING_LAYER = "workqueue"` MUST appear at the TOP of this module,
BEFORE `from numba import njit, prange`. The threading-layer setting is process-global
and is cached at numba import time; setting it AFTER `from numba import njit` is a
no-op. The workqueue layer is required for AVC because the default `omp` layer is
incompatible with VTK's threading on macOS.

This invariant is the reason this module is self-contained on its threading config.
Any future restructure that touches imports here MUST preserve this ordering.
"""

from __future__ import annotations

import numba

# CRITICAL: must precede `from numba import njit, prange`. See module docstring.
numba.config.THREADING_LAYER = "workqueue"

from numba import njit, prange  # noqa: E402 — must follow the config set above
import numpy as np  # noqa: E402


# ---------------------------------------------------------------------------
#
# Scalar-field evaluation is 41-45% of total surface.generate() latency.  For
# the two highest-cost implicit generators these kernels replace NumPy
# meshgrid-broadcasting (which allocates several n^3 temporaries — X2, Y2, Z2,
# every product term) with a single fused `prange` loop that reads the 1-D
# linspace axis `g` and writes one scalar per voxel.
#
# `@njit(parallel=True, cache=True)`:
#   * parallel=True  — `prange` over the outer i-axis; every `out[i,j,k]` write
#     is independent (no cross-iteration reduction), so parallel execution is
#     bit-identical to serial — no summation-order risk.
#   * cache=True     — the compiled kernel is persisted to disk, so the
#     first-call JIT cost is paid once per machine, not once per process.
#
# JIT-latency note: the first Fermat/Enriques render after a cold cache pays
# the ~400-800 ms compile.  That call runs inside the e4 background-thread
# worker (render_worker.MeshWorker), so it is OFF the GUI thread — the UI does
# not freeze.  No eager startup warm-up is used (e5 Numba arm64 spike §4/§8).
#
# Numeric identity: each kernel is a term-by-term transcription of the
# generator's former NumPy expression, in the IDENTICAL operator order, so the
# per-voxel IEEE-754 op sequence matches NumPy's elementwise evaluation.  The
# `np.clip` post-step is folded in as a scalar min/max.  Guarded by
# tests/test_numba_field_kernels.py (kernel vs NumPy reference, rtol=atol=1e-9).


@njit(parallel=True, cache=True)
def _fermat_field_kernel(g, alpha, beta, gamma, c, out):
    """Fill *out* with the Fermat-quartic scalar field on the ``g`` grid.

    Transcribes ``fermat_quartic``'s former NumPy expression term-for-term:
    ``X2*X2 + Y2*Y2 + Z2*Z2 + alpha*(X2*Y2+Y2*Z2+Z2*X2)
    + beta*(X*Y*Z)*(X+Y+Z) + gamma*(X2+Y2+Z2) - c``, then ``np.clip(F, ±200)``.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        for j in range(n):
            y = g[j]
            y2 = y * y
            for k in range(n):
                z = g[k]
                z2 = z * z
                val = (
                    x2 * x2 + y2 * y2 + z2 * z2
                    + alpha * (x2 * y2 + y2 * z2 + z2 * x2)
                    + beta * (x * y * z) * (x + y + z)
                    + gamma * (x2 + y2 + z2)
                    - c
                )
                # np.clip(F, -200.0, 200.0) — scalar form.
                if val < -200.0:
                    val = -200.0
                elif val > 200.0:
                    val = 200.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _enriques_fig1_field_kernel(g, c, out):
    """Fill *out* with the canonical Enriques-sextic scalar field.

    Transcribes ``enriques_figure_1``'s former NumPy expression term-for-term:
    ``X2*Y2 + X2*Z2 + Y2*Z2 + X2*Y2*Z2 + c*(X*Y*Z)*(1+X2+Y2+Z2)``, then
    ``np.clip(F, ±10)``.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        for j in range(n):
            y = g[j]
            y2 = y * y
            for k in range(n):
                z = g[k]
                z2 = z * z
                val = (
                    x2 * y2 + x2 * z2 + y2 * z2 + x2 * y2 * z2
                    + c * (x * y * z) * (1.0 + x2 + y2 + z2)
                )
                # np.clip(F, -10.0, 10.0) — scalar form.
                if val < -10.0:
                    val = -10.0
                elif val > 10.0:
                    val = 10.0
                out[i, j, k] = val


# ---------------------------------------------------------------------------
# realtime-variety-render-e5b (CAND-2 v1) — Numba field kernels for the 9
# remaining implicit generators.  Mechanical extension of the e5 v0 pattern
# above (_fermat_field_kernel / _enriques_fig1_field_kernel): same
# @njit(parallel=True, cache=True), same prange-outer-i / range j/k loop
# structure, term-by-term operator-order-identical transcription of the
# generator's former NumPy expression, np.clip folded as scalar if/elif.
# Powers ≥3 are written as explicit multiplies (x*x*x, x2 = x*x; x4 = x2*x2;
# x5 = x4*x, x2*x2*x2) to keep per-voxel IEEE-754 op order reproducible
# against the NumPy reference at rtol=atol=1e-9 (e5 spike § R1, R2).
# Every ValueError / RuntimeWarning these kernels' callers rely on fires in
# the generator BEFORE the kernel call — AI-14 preserved.
# ---------------------------------------------------------------------------


@njit(parallel=True, cache=True)
def _kummer_field_kernel(g, mu_squared, lam, sqrt2, out):
    """Fill *out* with the Kummer-quartic scalar field on the ``g`` grid.

    Transcribes ``kummer_surface``'s NumPy expression term-for-term:
    ``(X² + Y² + Z² − μ²)² − λ · p · q · r · s`` with
    ``p,q,r,s = 1∓Z∓√2X, 1±Z±√2Y``, then ``np.clip(F, ±50)``.
    ``λ`` and ``√2`` are scalar pre-computes that stay in the generator.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        sqrt2_x = sqrt2 * x
        for j in range(n):
            y = g[j]
            y2 = y * y
            sqrt2_y = sqrt2 * y
            for k in range(n):
                z = g[k]
                z2 = z * z
                p_ = 1.0 - z - sqrt2_x
                q_ = 1.0 - z + sqrt2_x
                r_ = 1.0 + z + sqrt2_y
                s_ = 1.0 + z - sqrt2_y
                base = x2 + y2 + z2 - mu_squared
                val = base * base - lam * p_ * q_ * r_ * s_
                if val < -50.0:
                    val = -50.0
                elif val > 50.0:
                    val = 50.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _enriques_fig2_field_kernel(g, lam0, lam3, c, out):
    """Fill *out* with the Enriques fig 2 (Dolgachev λ-family) field.

    Transcribes ``enriques_figure_2``'s NumPy expression term-for-term:
    ``λ₀·X²Y²Z² + 1·Y²Z² + 1·X²Z² + λ₃·X²Y² + c·(XYZ)·(1+X²+Y²+Z²)``,
    then ``np.clip(F, ±10)``.  The literal ``1.0 *`` factors on the middle
    two terms are preserved verbatim for IEEE-754 op-order parity.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        for j in range(n):
            y = g[j]
            y2 = y * y
            for k in range(n):
                z = g[k]
                z2 = z * z
                val = (
                    lam0 * x2 * y2 * z2
                    + 1.0 * y2 * z2
                    + 1.0 * x2 * z2
                    + lam3 * x2 * y2
                    + c * (x * y * z) * (1.0 + x2 + y2 + z2)
                )
                if val < -10.0:
                    val = -10.0
                elif val > 10.0:
                    val = 10.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _enriques_fig3_field_kernel(g, k_coef, out):
    """Fill *out* with the Cayley quartic symmetroid field (Enriques fig 3).

    Transcribes ``enriques_figure_3``'s NumPy expression term-for-term:
    ``s = X+Y+Z+XY+XZ+YZ;  F = s² − k·X·Y·Z``, then ``np.clip(F, ±50)``.
    Loop variable ``k`` shadows the conventional name; the kernel param is
    named ``k_coef`` to avoid the collision.  Callers (the generator)
    forward their own float ``k`` positionally and are unaffected by the
    rename — the param-name divergence is kernel-internal only.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        for j in range(n):
            y = g[j]
            for k in range(n):
                z = g[k]
                s = x + y + z + x * y + x * z + y * z
                val = s * s - k_coef * x * y * z
                if val < -50.0:
                    val = -50.0
                elif val > 50.0:
                    val = 50.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _enriques_fig4_field_kernel(g, tau, phi2, one_plus_2phi, out):
    """Fill *out* with the Endrass-icosahedral sextic field (Enriques fig 4).

    Transcribes ``enriques_figure_4``'s NumPy expression term-for-term:
    ``P = 4·(φ²X² − Y²)(φ²Y² − Z²)(φ²Z² − X²);  Q = (1+2φ)·(X²+Y²+Z²−1)²;
    F = P − τ·Q``, then ``np.clip(F, ±20)``.  Scalar constants ``φ²`` and
    ``1+2φ`` are pre-computed in the generator and passed in.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        for j in range(n):
            y = g[j]
            y2 = y * y
            for k in range(n):
                z = g[k]
                z2 = z * z
                t0 = phi2 * x2 - y2
                t1 = phi2 * y2 - z2
                t2 = phi2 * z2 - x2
                P = 4.0 * t0 * t1 * t2
                inner = x2 + y2 + z2 - 1.0
                Q = one_plus_2phi * inner * inner
                val = P - tau * Q
                if val < -20.0:
                    val = -20.0
                elif val > 20.0:
                    val = 20.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _dwork_field_kernel(g, psi, out):
    """Fill *out* with the Dwork-pencil quintic real-affine-slice field.

    Transcribes ``calabi_yau_dwork``'s NumPy expression: ``X⁵ + Y⁵ + Z⁵ + 2
    − 5ψ·XYZ``, then ``np.clip(F, ±100)``.  Powers of 5 are written as
    explicit multiplies via the ``x2 → x4 → x5`` chain to keep per-voxel
    IEEE-754 op order reproducible against the NumPy reference.  This is
    the only new kernel in v1 that uses a 5th power — a width the e5 v0
    templates never exercised.  The ψ ≈ 1 conifold ``RuntimeWarning`` fires
    in the generator BEFORE this kernel runs — AI-14 preserved.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        x4 = x2 * x2
        x5 = x4 * x
        for j in range(n):
            y = g[j]
            y2 = y * y
            y4 = y2 * y2
            y5 = y4 * y
            for k in range(n):
                z = g[k]
                z2 = z * z
                z4 = z2 * z2
                z5 = z4 * z
                val = x5 + y5 + z5 + 2.0 - 5.0 * psi * x * y * z
                if val < -100.0:
                    val = -100.0
                elif val > 100.0:
                    val = 100.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _klein_cubic_field_kernel(g, z0, out):
    """Fill *out* with the Klein cubic threefold slice field (Fano fig 1).

    Transcribes ``fano_klein_cubic``'s NumPy expression term-for-term:
    ``X + X²Y + Y²Z + z₀·Z² + z₀²``, then ``np.clip(F, ±50)``.  This is the
    one v1 kernel whose field is asymmetric in (x,y,z) — an axis-transpose
    bug would be detected by the equivalence test.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        for j in range(n):
            y = g[j]
            y2 = y * y
            for k in range(n):
                z = g[k]
                val = x + x2 * y + y2 * z + z0 * z * z + z0 * z0
                if val < -50.0:
                    val = -50.0
                elif val > 50.0:
                    val = 50.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _segre_cubic_field_kernel(g, a, b, out):
    """Fill *out* with the Segre cubic slice field (Fano fig 2).

    Transcribes ``fano_segre_cubic``'s NumPy expression term-for-term:
    ``s = X+Y+Z+a+b;  F = X³ + Y³ + Z³ + a³ + b³ − s³``, then
    ``np.clip(F, ±1000)``.  Cubes are written as explicit multiplies.
    The ``s`` left-to-right add order ``x + y + z + a + b`` matches NumPy
    elementwise evaluation exactly.
    """
    a3 = a * a * a
    b3 = b * b * b
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x3 = x * x * x
        for j in range(n):
            y = g[j]
            y3 = y * y * y
            for k in range(n):
                z = g[k]
                z3 = z * z * z
                s = x + y + z + a + b
                s3 = s * s * s
                val = x3 + y3 + z3 + a3 + b3 - s3
                if val < -1000.0:
                    val = -1000.0
                elif val > 1000.0:
                    val = 1000.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _two_quadrics_field_kernel(g, p, q, mu, eps,
                               lam0, lam1, lam2, lam3, lam4, out):
    """Fill *out* with the two-quadrics ε-tube field (Fano fig 3).

    Transcribes ``fano_two_quadrics``'s NumPy expression term-for-term:
    ``Q₁ = X² + Y² + Z² + p² + q² − 1;  Q₂ = λ₀X² + λ₁Y² + λ₂Z² + λ₃p² +
    λ₄q² − μ;  F = Q₁² + Q₂² − ε²``, then ``np.clip(F, ±200)``.  The 5 λ
    coefficients are the hard-coded ``(-0.5, 0.0, 0.5, 1.0, 1.5)`` tuple
    from the generator; passed in as scalar args for parameterization.
    The ε < 0.08 ``RuntimeWarning`` fires in the generator BEFORE this
    kernel runs — AI-14 preserved.
    """
    p2 = p * p
    q2 = q * q
    eps2 = eps * eps
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        for j in range(n):
            y = g[j]
            y2 = y * y
            for k in range(n):
                z = g[k]
                z2 = z * z
                Q1 = x2 + y2 + z2 + p2 + q2 - 1.0
                Q2 = (lam0 * x2 + lam1 * y2 + lam2 * z2
                      + lam3 * p2 + lam4 * q2 - mu)
                val = Q1 * Q1 + Q2 * Q2 - eps2
                if val < -200.0:
                    val = -200.0
                elif val > 200.0:
                    val = 200.0
                out[i, j, k] = val


@njit(parallel=True, cache=True)
def _sextic_double_solid_field_kernel(g, alpha, r6, out):
    """Fill *out* with the sextic double solid two-sheet branch field
    (Fano fig 4).

    Transcribes ``fano_sextic_double_solid``'s NumPy expression
    term-for-term: ``Z² + X⁶ + Y⁶ + α·X²Y²·(X²+Y²) − R⁶``, then
    ``np.clip(F, ±200)``.  Sixth powers are written as ``x²·x²·x²``
    (matches the NumPy reference's literal ``X2*X2*X2``).  ``R⁶`` is a
    scalar pre-compute that stays in the generator.
    """
    n = g.shape[0]
    for i in prange(n):
        x = g[i]
        x2 = x * x
        x6 = x2 * x2 * x2
        for j in range(n):
            y = g[j]
            y2 = y * y
            y6 = y2 * y2 * y2
            for k in range(n):
                z = g[k]
                val = (
                    z * z
                    + x6
                    + y6
                    + alpha * x2 * y2 * (x2 + y2)
                    - r6
                )
                if val < -200.0:
                    val = -200.0
                elif val > 200.0:
                    val = 200.0
                out[i, j, k] = val


