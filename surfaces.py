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

numba.config.THREADING_LAYER = "workqueue"
from numba import njit, prange  # noqa: E402 — must follow the config set above


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
    # realtime-variety-render-e2-s1 (CAND-8): measured typical generation
    # time in ms at the surface's default parameters.  0 means "unmeasured /
    # not fast" — every implicit (marching-cubes) generator keeps this default.
    # The three Hanson parametric generators carry their measured values so
    # `app.py`'s continuous-drag fast-path (see `should_render_on_drag`) can
    # speed-route them: a surface with 0 < typical_ms <= 80 renders at every
    # debounced drag tick; everything else stays release-only.  Defaulted
    # field placed after `params` so the dataclass contract stays clean
    # (AI-8 — the dataclass is not frozen; a trailing defaulted field is safe).
    typical_ms: int = 0
    # realtime-variety-render-e4b (CAND-3): coarse-preview-LOD floor for the
    # marching-cubes grid `n`.  0 means "no coarse-LOD" — the safe default for
    # any surface not explicitly opted in:
    #   * Hanson parametric generators (typical_ms > 0): always render full;
    #     they never go through marching cubes, so a coarse `n` is meaningless
    #     (AI-6 — three-layer guard, this default is the second layer).
    #   * Implicit generators whose topology is fragile at any practical
    #     coarse floor (e.g. fano_two_quadrics's ε-tube): stay opt-out so
    #     drag-time renders preserve mathematical honesty.
    # Implicit generators that DO opt in carry a per-surface `coarse_n` value
    # validated by tests/test_coarse_n.py's n-sweep — the floor is
    # the smallest `n` at which the surface's defining topological features
    # (Kummer's 16 nodes, Enriques double curves, etc.) survive the sweep.
    # Mutually exclusive in use with `typical_ms`: a Surface with
    # `typical_ms > 0` is parametric; a Surface with `coarse_n > 0` is
    # implicit-LOD-eligible.
    coarse_n: int = 0

    def defaults(self) -> dict[str, float]:
        return {p.name: p.default for p in self.params}


# realtime-variety-render-e2-s2 (CAND-8): the continuous-drag fast-path
# threshold, in ms.  A surface whose measured `typical_ms` falls in
# (0, FAST_RENDER_THRESHOLD_MS] is "fast enough" to regenerate at every
# debounced drag tick (~80 ms cadence) without the GUI feeling sluggish;
# anything slower stays release-only until the e4 coarse-LOD path lands.
FAST_RENDER_THRESHOLD_MS = 80


def should_render_on_drag(surface: "Surface | None") -> bool:
    """Pure speed-routing predicate for the continuous-drag fast-path.

    Returns ``True`` when *surface* is fast enough to regenerate on every
    debounced drag tick — i.e. it carries a measured ``typical_ms`` in the
    half-open range ``(0, FAST_RENDER_THRESHOLD_MS]``.  Returns ``False`` for
    ``None`` and for any surface with ``typical_ms == 0`` (unmeasured /
    implicit marching-cubes generators), which therefore stay release-only
    exactly as before this epic.

    Extracted as a free function (no Qt, no ``QApplication``) so the routing
    decision is unit-testable under the Qt-free AI-2 suite.  ``MainWindow``
    calls this from its drag-tick handler; the panels do not — they have no
    visibility into the current surface's ``typical_ms``.
    """
    return (
        surface is not None
        and 0 < surface.typical_ms <= FAST_RENDER_THRESHOLD_MS
    )


def dispatch_mode(surface: "Surface | None", in_drag: bool) -> str:
    """Return the e4b speed-routing decision for a render request.

    Three outcomes (the names are stable — `app.py` keys on them):

    - ``"full"`` — render at full resolution.  Fired (a) on slider RELEASE
      for every surface; (b) on slider DRAG for Hanson parametric surfaces
      (already fast enough — the e2 continuous-drag fast-path).
    - ``"coarse"`` — render at the surface's per-surface ``coarse_n`` floor
      (realtime-variety-render-e4b / CAND-3).  Fired only on slider DRAG
      for implicit (marching-cubes) generators with ``coarse_n > 0``; the
      release path then re-renders at full resolution.
    - ``"skip"`` — do nothing.  Fired on slider DRAG for opt-out implicit
      generators (``coarse_n == 0``, e.g. ``fano_two_quadrics`` whose
      ε-tube is too fragile for any practical coarse floor) and for
      ``None`` (no surface selected).

    AI-6 (three-layer Hanson skip):
      1. This function returns ``"full"`` (NOT ``"coarse"``) for Hanson
         because ``typical_ms > 0`` is checked before ``coarse_n``.
      2. Hanson surfaces' ``coarse_n == 0`` default — even if a future bug
         called for coarse mode on Hanson, the dispatch ``params["n"]``
         injection in ``app.py`` skips when ``coarse_n == 0``.
      3. The worker (``render_worker.MeshWorker``) is mode-agnostic — it
         passes ``params`` through to ``surface.generate`` unmodified, so
         a Hanson generator never sees an unwanted ``n`` override.

    Extracted as a free function (no Qt, no ``QApplication``) so the
    routing decision is unit-testable under the Qt-free AI-2 suite — same
    pattern as ``should_render_on_drag`` (this module) and
    ``clipped_cache_is_valid`` (``app.py``).
    """
    if surface is None:
        return "skip"
    if not in_drag:
        # Release path is always full-resolution.
        return "full"
    if surface.typical_ms > 0:
        # Hanson parametric surfaces are already fast enough; render full at
        # every drag tick.  (AI-6 layer 1: positive Hanson signal.)
        return "full"
    if surface.coarse_n > 0:
        # Implicit surface with a validated coarse-LOD floor.
        return "coarse"
    # Implicit, opt-out (coarse_n == 0): no drag render.
    return "skip"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _marching_cubes_to_polydata(
    field: np.ndarray,
    bounds: float,
    level: float = 0.0,
    smooth_iter: int = 20,
    second_smooth_iter: int = 0,
) -> pv.PolyData:
    """Extract the level set of *field* as a smooth PolyData.

    Pipeline:
      1. ``vtkFlyingEdges3D`` (via ``pv.ImageData.contour(method=
         'flying_edges')``) on the sampled scalar field. Flying Edges is
         VTK's modern, SMP-threaded isocontouring algorithm — geometrically
         identical to classic marching cubes to machine precision but
         ~3-4× faster on the isocontour step at production resolutions
         (measured n=240: 298 ms → 98 ms; realtime-variety-render-e6 /
         CAND-1). ``compute_normals=True``
         seeds gradient-based normals from the scalar field; they are
         re-derived in step 3 after smoothing anyway, so this is only a
         convenience seed.
      2. ``smooth_taubin()`` for *volume-preserving* smoothing. Plain
         Laplacian smoothing shrinks the surface; Taubin's twin-coefficient
         scheme lets us iterate ~20× without losing scale or features.
      3. Optional **second** Taubin pass with a lower pass-band
         (``n_iter=second_smooth_iter, pass_band=0.05``) STACKING on top
         of the first — used only when callers pass ``second_smooth_iter > 0``
         (AI-6: stacks, does NOT replace the first pass).  This second
         pass attenuates double-curve sawtooth-ridge artifacts on the
         Enriques figs 1+2 family at the cost of ~138ms (spike measured
         in enriques-taubin-spike-2026q2-e1); see CONTEXT.md §8.16 for
         the budget rationale and per-figure scope.  Default ``0``
         preserves the existing single-pass behavior for all other
         generators (K3, Hanson CY3, Dwork, Fano, Enriques figs 3+4).
      4. ``compute_normals()`` re-derives normals after smoothing so
         shading stays consistent with the new vertex positions.

    Note: unlike ``skimage.measure.marching_cubes``, ``vtkFlyingEdges3D``
    already emits a watertight, shared-vertex triangle mesh — there are no
    duplicate vertices to merge, so no ``clean()`` pass is run. A ``clean()``
    here would actually *regress* shading: merging the handful of
    near-coincident points it finds collapses incident triangles to
    zero-area degenerate cells, and ``vtkPolyDataNormals``' orientation walk
    cannot cross a degenerate cell — the mesh splits into orientation
    islands and half the surface shades inside-out (verified MC-vs-FE
    off-screen comparison on the Enriques canonical sextic,
    realtime-variety-render-e6).
    """
    n = field.shape[0]
    spacing_val = 2 * bounds / (n - 1)
    # Detect the case where the field has no zero-crossing before calling the
    # contour filter.  vtkFlyingEdges3D returns an EMPTY mesh (not an error)
    # when no isosurface exists, so this explicit guard is what upholds the
    # AI-14 ``ValueError`` contract for the no-real-zero-set case.
    if field.min() > level or field.max() < level:
        raise ValueError(
            "No real zero set in the sampling box for these parameters "
            f"(field range [{field.min():.3g}, {field.max():.3g}]). "
            "Try adjusting the sliders to a different parameter combination."
        )
    # realtime-variety-render-e6 (CAND-1): VTK Flying Edges replaces
    # skimage.measure.marching_cubes.  The field grid is built with
    # ``np.meshgrid(..., indexing="ij")`` (x is the first/slowest NumPy axis),
    # but VTK ImageData stores points with i (=x) as the FASTEST-varying
    # index — so the scalar array MUST be raveled in Fortran order.  A C-order
    # ravel silently transposes the x and z axes of the isosurface with no
    # error (it would pass the non-empty/bounds smoke tests undetected).
    grid = pv.ImageData(
        dimensions=(n, n, n),
        spacing=(spacing_val, spacing_val, spacing_val),
        origin=(-bounds, -bounds, -bounds),  # replaces the old ``verts -= bounds``
    )
    grid.point_data["field"] = field.ravel(order="F")
    mesh = grid.contour(
        [level],
        scalars="field",
        method="flying_edges",
        compute_normals=True,
        compute_scalars=False,
    )
    # vtkFlyingEdges3D returns a 0-point mesh (not an error) for a degenerate
    # field whose range collapses exactly onto the contour level
    # (field.min() == field.max() == level) — the strict-inequality pre-check
    # above cannot catch that case.  Re-assert the AI-14 ValueError contract.
    if mesh.n_points == 0:
        raise ValueError(
            "No real zero set in the sampling box for these parameters. "
            "Try adjusting the sliders to a different parameter combination."
        )
    # No clean()/triangulate() pass: vtkFlyingEdges3D is contractually an
    # all-triangle, shared-vertex, watertight extractor — there is nothing to
    # merge or re-triangulate. Adding clean() here regresses shading (see the
    # docstring note); triangulate() would be a pure no-op.
    if smooth_iter > 0 and mesh.n_points > 0:
        # Taubin (lambda > 0, mu < 0) is volume-preserving — unlike vanilla
        # Laplacian which shrinks the surface every iteration.
        mesh = mesh.smooth_taubin(n_iter=smooth_iter, pass_band=0.1)
    if second_smooth_iter > 0 and mesh.n_points > 0:
        # enriques-hq-smoothing-2026q3-e1: optional second Taubin pass
        # with a lower pass-band (more aggressive low-frequency smoothing).
        # STACKS on top of the first pass per AI-6 — do NOT replace.
        # Caller controls activation via the opt-in kwarg in the generator
        # (see enriques_figure_1 / enriques_figure_2 hq_smoothing param).
        mesh = mesh.smooth_taubin(n_iter=second_smooth_iter, pass_band=0.05)
    if mesh.n_points > 0:
        mesh = mesh.compute_normals(
            cell_normals=False, point_normals=True,
            consistent_normals=True, auto_orient_normals=False,
            split_vertices=False,
        )
    return mesh


# ---------------------------------------------------------------------------
# Numba JIT field-evaluation kernels (realtime-variety-render-e5 / CAND-2)
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
