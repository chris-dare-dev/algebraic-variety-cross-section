"""Marching-cubes + parametric pipeline helpers for AVC variety generators.

Per restructure-feature-subpackages-2026q2-r2 Batch 6: extracted from surfaces.py
(originally lines L60-L170 + L573-L630 + the _hanson_cross_section helper).

AI-6 contract: implicit generators use _marching_cubes_to_polydata; parametric
(Hanson) use _grid_to_polydata + _concat_polydata. Each generator picks ONE pipeline.

AI-7: _concat_polydata sets compute_normals(cell_normals=True, consistent_normals=False,
auto_orient_normals=False) for Hanson — preserved verbatim from the original.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence

import numpy as np
import pyvista as pv


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

