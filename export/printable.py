"""Printable-mesh pipeline: variety cross-section -> watertight STL solid.

Design notes
------------
A 3-D printer needs a **watertight, manifold** triangle mesh whose interior is
unambiguous (the slicer fills the enclosed volume). Two facts about AVC meshes
shape this module:

1. **Implicit surfaces are already printable.** Every implicit generator
   (Fermat, Kummer, Enriques, Dwork, Fano) extracts its level set with VTK
   Flying Edges, which emits a watertight shared-vertex triangle mesh
   (``varieties/_marching.py``). So the *unclipped* export of an implicit
   surface is just "call the generator and write the STL" — no repair needed.
   The Fermat quartic ``x**4 + y**4 + z**4 = 1`` is the canonical example: it
   is a closed surface bounding a rounded-cube solid in ``[-1, 1]**3``.

   (Note on "compactified so that ``|x**4 + y**4 + z**4| = 1``": the left side
   is a sum of even powers, hence ``>= 0`` everywhere, so ``|.| = 1`` is the
   same locus as ``= 1`` — i.e. ``fermat_quartic(c=1.0)`` at defaults. It is
   already compact; nothing extra to do.)

2. **Clipping to a sphere/cube must stay watertight.** The app's live
   ``clip_to_domain`` cuts the surface mesh and leaves *open* boundary loops
   where the surface crosses the clip shape — fine on screen, not printable.
   To honour "print it in a spherical pattern" we instead do the clip in the
   **scalar field** before iso-surfacing: the printable solid is the CSG
   intersection of the variety solid ``{f <= 0}`` with the domain solid
   ``{g <= 0}``, whose boundary is the zero level set of ``max(f, g)``. One
   Flying-Edges pass on ``max(f, g)`` yields a watertight solid with genuine
   spherical / cubic caps — by the same guarantee that makes the base surface
   watertight. This needs the analytic field ``f`` (see ``FIELD_PROVIDERS``);
   it is wired for the surfaces whose field is simple and stable (the K3
   family). Other implicit surfaces are extensible the same way.

Parametric (Hanson Calabi-Yau) cross-sections are *open* 2-surfaces in R3, not
solids, so they have no "inside". They export as an open shell (Bambu Studio
can thicken via "make solid" / a shell modifier) but cannot be CSG-clipped.

This module is Qt-free (AI-2) and reuses only public ``varieties`` API.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import numpy as np
import pyvista as pv

from varieties.registry import VARIETIES


# ---------------------------------------------------------------------------
# Clip modes
# ---------------------------------------------------------------------------


class ClipMode(str, enum.Enum):
    """How to bound the printed solid. Mirrors the app's Clip Region shapes."""

    NONE = "none"
    SPHERE = "sphere"
    CUBE = "cube"


# ---------------------------------------------------------------------------
# Build-volume model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BuildVolume:
    """A printer's usable build volume, in millimetres (x, y, z)."""

    x_mm: float
    y_mm: float
    z_mm: float

    @property
    def min_mm(self) -> float:
        return min(self.x_mm, self.y_mm, self.z_mm)

    def fits(self, extent_mm: tuple[float, float, float], margin_mm: float = 0.0) -> bool:
        return (
            extent_mm[0] <= self.x_mm - 2 * margin_mm
            and extent_mm[1] <= self.y_mm - 2 * margin_mm
            and extent_mm[2] <= self.z_mm - 2 * margin_mm
        )


#: Bambu Lab H2S — 340 x 320 x 340 mm usable build volume.
BAMBU_H2S = BuildVolume(340.0, 320.0, 340.0)


# ---------------------------------------------------------------------------
# Analytic implicit fields (for CSG clipping)
# ---------------------------------------------------------------------------
#
# Each provider returns the variety's defining scalar field f(x, y, z) sampled
# on the cube grid ``g`` (g = linspace(-R, R, n)), with the convention
# f < 0 INSIDE the solid. These are faithful transcriptions of the generator
# formulae in varieties/k3.py; tests/test_stl_export.py parity-checks them
# against the live generators so a formula drift is caught.


def _fermat_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Fermat-quartic family field (varieties.k3.fermat_quartic)."""
    alpha = params.get("alpha", 0.0)
    beta = params.get("beta", 0.0)
    gamma = params.get("gamma", 0.0)
    c = params.get("c", 1.0)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    return (
        X2 * X2 + Y2 * Y2 + Z2 * Z2
        + alpha * (X2 * Y2 + Y2 * Z2 + Z2 * X2)
        + beta * (X * Y * Z) * (X + Y + Z)
        + gamma * (X2 + Y2 + Z2)
        - c
    )


def _kummer_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Kummer-quartic field (varieties.k3.kummer_surface).

    Raises ValueError on the same degenerate parameters as the generator so
    the CSG path reports the AI-14 cases identically.
    """
    mu_squared = params.get("mu_squared", 1.3)
    if abs(mu_squared - 3.0) < 1e-6:
        raise ValueError("mu^2 = 3 is a pole of lambda(mu); choose another value.")
    if mu_squared <= 1.0 / 3.0:
        raise ValueError(
            f"mu^2 must be > 1/3 (lambda=0 at mu^2=1/3, no zero set); got {mu_squared:.3f}"
        )
    lam = (3.0 * mu_squared - 1.0) / (3.0 - mu_squared)
    sqrt2 = np.sqrt(2.0)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    p = 1.0 - Z - sqrt2 * X
    q = 1.0 - Z + sqrt2 * X
    r = 1.0 + Z + sqrt2 * Y
    s = 1.0 + Z - sqrt2 * Y
    base = X * X + Y * Y + Z * Z - mu_squared
    return base * base - lam * p * q * r * s


# ---------------------------------------------------------------------------
# Enriques sextic family (varieties/enriques.py)
# ---------------------------------------------------------------------------
#
# Each provider is a faithful numpy transcription of the generator's formula
# (which the generator evaluates via a Numba kernel in varieties/_kernels.py).
# Sign convention f < 0 INSIDE the solid. Scalar pre-computes (φ², 1+2φ, λ
# tuples, R⁶, …) are reproduced exactly the way the generator computes them.
# Default params come from the registry ParamSpec defaults.


def _enriques_fig1_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Canonical Enriques sextic field (varieties.enriques.enriques_figure_1).

    f = X²Y² + X²Z² + Y²Z² + X²Y²Z² + c·XYZ·(1+X²+Y²+Z²).
    """
    c = params.get("c", 1.0)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    return (
        X2 * Y2 + X2 * Z2 + Y2 * Z2 + X2 * Y2 * Z2
        + c * (X * Y * Z) * (1.0 + X2 + Y2 + Z2)
    )


def _enriques_fig2_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Diagonal Enriques λ-family field (varieties.enriques.enriques_figure_2).

    f = λ₀·X²Y²Z² + Y²Z² + X²Z² + λ₃·X²Y² + c·XYZ·(1+X²+Y²+Z²).
    The middle two terms carry the generator's literal ``1.0 *`` factor.
    """
    lam0 = params.get("lam0", 1.0)
    lam3 = params.get("lam3", 2.0)
    c = params.get("c", 1.0)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    return (
        lam0 * X2 * Y2 * Z2
        + 1.0 * Y2 * Z2
        + 1.0 * X2 * Z2
        + lam3 * X2 * Y2
        + c * (X * Y * Z) * (1.0 + X2 + Y2 + Z2)
    )


def _enriques_fig3_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Cayley quartic symmetroid field (varieties.enriques.enriques_figure_3).

    s = X+Y+Z+XY+XZ+YZ ; f = s² − k·XYZ.
    """
    k = params.get("k", 16.0)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    s = X + Y + Z + X * Y + X * Z + Y * Z
    return s * s - k * X * Y * Z


def _enriques_fig4_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Endrass-icosahedral sextic field (varieties.enriques.enriques_figure_4).

    P = 4·(φ²X²−Y²)(φ²Y²−Z²)(φ²Z²−X²) ; Q = (1+2φ)·(X²+Y²+Z²−1)² ;
    f = P − τ·Q. φ = (1+√5)/2 (golden ratio); φ² and 1+2φ are the
    generator's scalar pre-computes, reproduced here verbatim.
    """
    tau = params.get("tau", 0.18)
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
    return P - tau * Q


# ---------------------------------------------------------------------------
# Calabi–Yau 3-fold — the only IMPLICIT subtype (Dwork pencil)
# ---------------------------------------------------------------------------
#
# The other 3 CY subtypes are parametric Hanson surfaces (open 2-surfaces, no
# enclosed solid) — they have NO field provider, so clip_for_print raises
# NotImplementedError for them by construction.


def _dwork_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Dwork-pencil quintic real-slice field (varieties.calabi_yau.calabi_yau_dwork).

    f = X⁵ + Y⁵ + Z⁵ + 2 − 5ψ·XYZ.
    """
    psi = params.get("psi", 0.5)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X5 = X * X * X * X * X
    Y5 = Y * Y * Y * Y * Y
    Z5 = Z * Z * Z * Z * Z
    return X5 + Y5 + Z5 + 2.0 - 5.0 * psi * X * Y * Z


# ---------------------------------------------------------------------------
# Fano 3-fold (ρ=1) family (varieties/fano.py)
# ---------------------------------------------------------------------------


def _klein_cubic_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Klein cubic threefold slice field (varieties.fano.fano_klein_cubic).

    f = X + X²Y + Y²Z + z₀·Z² + z₀². Asymmetric in (X,Y,Z).
    """
    z0 = params.get("z0", 0.4)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2 = X * X, Y * Y
    return X + X2 * Y + Y2 * Z + z0 * Z * Z + z0 * z0


def _segre_cubic_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Segre cubic slice field (varieties.fano.fano_segre_cubic).

    s = X+Y+Z+a+b ; f = X³ + Y³ + Z³ + a³ + b³ − s³.
    """
    a = params.get("a", 0.3)
    b = params.get("b", -0.4)
    a3 = a * a * a
    b3 = b * b * b
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X3 = X * X * X
    Y3 = Y * Y * Y
    Z3 = Z * Z * Z
    s = X + Y + Z + a + b
    s3 = s * s * s
    return X3 + Y3 + Z3 + a3 + b3 - s3


def _two_quadrics_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Two-quadrics ε-tube field (varieties.fano.fano_two_quadrics).

    Q₁ = X²+Y²+Z²+p²+q²−1 ; Q₂ = λ₀X²+λ₁Y²+λ₂Z²+λ₃p²+λ₄q²−μ ;
    f = Q₁² + Q₂² − ε². λ = (-0.5, 0.0, 0.5, 1.0, 1.5) is the generator's
    hard-coded pencil tuple.
    """
    p = params.get("p", 0.3)
    q = params.get("q", -0.2)
    mu = params.get("mu", 0.5)
    eps = params.get("eps", 0.18)
    lam0, lam1, lam2, lam3, lam4 = (-0.5, 0.0, 0.5, 1.0, 1.5)
    p2 = p * p
    q2 = q * q
    eps2 = eps * eps
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z
    Q1 = X2 + Y2 + Z2 + p2 + q2 - 1.0
    Q2 = lam0 * X2 + lam1 * Y2 + lam2 * Z2 + lam3 * p2 + lam4 * q2 - mu
    return Q1 * Q1 + Q2 * Q2 - eps2


def _sextic_double_solid_field(g: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Sextic double solid branch field (varieties.fano.fano_sextic_double_solid).

    f = Z² + X⁶ + Y⁶ + α·X²Y²·(X²+Y²) − R⁶. R⁶ is the generator's scalar
    pre-compute (r2 = R·R ; r6 = r2·r2·r2).
    """
    R = params.get("R", 1.2)
    alpha = params.get("alpha", 0.0)
    r2 = R * R
    r6 = r2 * r2 * r2
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2 = X * X, Y * Y
    X6 = X2 * X2 * X2
    Y6 = Y2 * Y2 * Y2
    return Z * Z + X6 + Y6 + alpha * X2 * Y2 * (X2 + Y2) - r6


#: (variety, subtype) -> field provider. Surfaces present here support CSG
#: clipping (sphere/cube) into a watertight solid. Add an entry to extend.
#: Covers ALL 11 implicit surfaces; the 3 parametric Hanson CY subtypes are
#: deliberately absent (open shells, no enclosed solid).
FIELD_PROVIDERS = {
    ("K3 surface", "Fermat quartic"): _fermat_field,
    ("K3 surface", "Kummer surface"): _kummer_field,
    ("Enriques surface", "Canonical sextic  [Fig. 1]"): _enriques_fig1_field,
    ("Enriques surface", "Diagonal λ-family  [Fig. 2]"): _enriques_fig2_field,
    ("Enriques surface", "Cayley symmetroid  [Fig. 3]"): _enriques_fig3_field,
    ("Enriques surface", "Icosahedral sextic  [Fig. 4]"): _enriques_fig4_field,
    ("Calabi–Yau 3-fold", "Dwork pencil  [Fig. 4]"): _dwork_field,
    ("Fano 3-fold (ρ=1)", "Klein cubic  [Fig. 1]"): _klein_cubic_field,
    ("Fano 3-fold (ρ=1)", "Segre cubic  [Fig. 2]"): _segre_cubic_field,
    ("Fano 3-fold (ρ=1)", "Two-quadrics CI tube  [Fig. 3]"): _two_quadrics_field,
    ("Fano 3-fold (ρ=1)", "Sextic double solid  [Fig. 4]"): _sextic_double_solid_field,
}


# ---------------------------------------------------------------------------
# Registry lookup + generation
# ---------------------------------------------------------------------------


def _resolve(variety: str, subtype: str | None):
    """Return (subtype, Surface) for a registry entry, with helpful errors."""
    if variety not in VARIETIES:
        raise KeyError(
            f"Unknown variety {variety!r}. Available: {sorted(VARIETIES)}"
        )
    subtypes = VARIETIES[variety]
    if subtype is None:
        subtype = next(iter(subtypes))  # first registered subtype
    if subtype not in subtypes:
        raise KeyError(
            f"Unknown subtype {subtype!r} for {variety!r}. "
            f"Available: {sorted(subtypes)}"
        )
    return subtype, subtypes[subtype]


def supports_csg_clip(variety: str, subtype: str | None = None) -> bool:
    """True iff a CSG field provider exists for the resolved (variety, subtype).

    Resolves *subtype* against the registry (None -> first registered subtype),
    then checks FIELD_PROVIDERS. Returns False for any unknown variety/subtype
    rather than raising, so a GUI can probe freely. The 3 parametric Hanson
    Calabi–Yau subtypes resolve to a real registry entry but have no provider,
    so they return False.
    """
    try:
        subtype, _surface = _resolve(variety, subtype)
    except KeyError:
        return False
    return (variety, subtype) in FIELD_PROVIDERS


def generate_surface_mesh(
    variety: str,
    subtype: str | None = None,
    params: dict[str, float] | None = None,
) -> pv.PolyData:
    """Call a registry generator with defaults merged under *params*.

    This is the *unclipped* path. For implicit surfaces it returns the
    watertight Flying-Edges mesh as-is; for parametric (Hanson) surfaces it
    returns the open shell.
    """
    subtype, surface = _resolve(variety, subtype)
    merged = surface.defaults()
    if params:
        merged.update(params)
    return surface.generate(**merged)


# ---------------------------------------------------------------------------
# Watertight CSG clipping (field-level)
# ---------------------------------------------------------------------------


def _domain_field(g: np.ndarray, mode: ClipMode, radius: float) -> np.ndarray:
    """Signed domain field g(x,y,z) <= 0 inside the clip shape.

    Sphere: radial distance ``r - R``. Cube: Chebyshev distance
    ``max(|x|,|y|,|z|) - R`` — the SAME metric the app's cube clip uses
    (cross_section.clip), so a CSG cube cap matches the on-screen cube clip.
    """
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    if mode is ClipMode.SPHERE:
        return np.sqrt(X * X + Y * Y + Z * Z) - radius
    if mode is ClipMode.CUBE:
        return np.maximum(np.maximum(np.abs(X), np.abs(Y)), np.abs(Z)) - radius
    raise ValueError(f"_domain_field called with non-clipping mode {mode!r}")


def _contour_watertight(
    field: np.ndarray, bounds: float, *, level: float = 0.0, smooth_iter: int = 15
) -> pv.PolyData:
    """Flying-Edges iso-surface of *field*, watertight, lightly Taubin-smoothed.

    Mirrors varieties/_marching.py's pipeline (incl. the Fortran-order ravel
    that keeps x as VTK's fastest index) and the AI-14 empty-field guard, but
    lives here so ``export`` stays decoupled from ``varieties`` internals.
    """
    n = field.shape[0]
    if field.min() > level or field.max() < level:
        raise ValueError(
            "No zero set in the clip region for these parameters "
            f"(field range [{field.min():.3g}, {field.max():.3g}]). "
            "Try a larger radius or different parameters."
        )
    spacing = 2 * bounds / (n - 1)
    grid = pv.ImageData(
        dimensions=(n, n, n),
        spacing=(spacing, spacing, spacing),
        origin=(-bounds, -bounds, -bounds),
    )
    grid.point_data["field"] = field.ravel(order="F")
    mesh = grid.contour(
        [level], scalars="field", method="flying_edges",
        compute_normals=True, compute_scalars=False,
    )
    if mesh.n_points == 0:
        raise ValueError("No zero set in the clip region for these parameters.")
    if smooth_iter > 0:
        mesh = mesh.smooth_taubin(n_iter=smooth_iter, pass_band=0.1)
    return mesh.compute_normals(
        cell_normals=False, point_normals=True,
        consistent_normals=True, auto_orient_normals=False, split_vertices=False,
    )


def clip_for_print(
    variety: str,
    subtype: str | None = None,
    params: dict[str, float] | None = None,
    *,
    mode: ClipMode | str = ClipMode.SPHERE,
    radius: float = 1.0,
    n: int = 200,
    smooth_iter: int = 15,
) -> pv.PolyData:
    """Return the variety solid intersected with a sphere/cube, watertight.

    Requires an analytic field provider (see ``FIELD_PROVIDERS``). The grid
    spans exactly the clip box ``[-radius, radius]**3`` — everything outside
    is removed by construction, so the generator's own sampling bounds are
    irrelevant here.
    """
    mode = ClipMode(mode)
    if mode is ClipMode.NONE:
        raise ValueError("clip_for_print needs a SPHERE or CUBE mode")
    if radius <= 0:
        raise ValueError(f"radius must be > 0, got {radius}")

    subtype, _surface = _resolve(variety, subtype)
    provider = FIELD_PROVIDERS.get((variety, subtype))
    if provider is None:
        raise NotImplementedError(
            f"CSG clipping is not wired for ({variety!r}, {subtype!r}). "
            f"Supported: {sorted(FIELD_PROVIDERS)}. "
            "Export unclipped, or add a field provider in export.printable."
        )

    g = np.linspace(-radius, radius, n)
    variety_field = provider(g, params or {})
    combined = np.maximum(variety_field, _domain_field(g, mode, radius))

    # Seal the outer voxel shell so the iso-surface is forced closed AT the
    # box boundary. This matters for the CUBE clip, whose cap coincides
    # exactly with the sampling box wall (Chebyshev radius == box half-side):
    # without a sealed shell Flying Edges leaves that cap as an open boundary
    # loop. For the SPHERE clip the boundary voxels are already outside the
    # sphere (positive), so sealing is a no-op there.
    seal = float(np.abs(combined).max()) + 1.0
    combined[0, :, :] = combined[-1, :, :] = seal
    combined[:, 0, :] = combined[:, -1, :] = seal
    combined[:, :, 0] = combined[:, :, -1] = seal

    return _contour_watertight(combined, radius, smooth_iter=smooth_iter)


# ---------------------------------------------------------------------------
# Scale + center into millimetres
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FitResult:
    """Outcome of fitting a mesh into a build volume."""

    mesh: pv.PolyData
    scale: float                       # math-units -> mm multiplier
    extent_mm: tuple[float, float, float]
    clamped: bool                      # True if target was reduced to fit
    note: str


def fit_to_build_volume(
    mesh: pv.PolyData,
    build: BuildVolume = BAMBU_H2S,
    *,
    target_mm: float | None = None,
    margin_mm: float = 5.0,
    center: bool = True,
) -> FitResult:
    """Uniformly scale (and optionally center) *mesh* into millimetres.

    ``target_mm`` is the desired size of the model's LONGEST axis. If omitted,
    the model is scaled to fill the build volume minus ``margin_mm`` on each
    side. A target that would overflow the build volume is clamped down (with
    ``clamped=True``) — never silently over-sized.
    """
    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
    extent = np.array([xmax - xmin, ymax - ymin, zmax - zmin], dtype=float)
    longest = float(extent.max())
    if longest <= 0:
        raise ValueError("Mesh has zero extent; nothing to scale.")

    # Largest uniform scale that still fits (longest axis vs the matching build
    # dimension is not assumed — be conservative against the smallest build dim
    # relative to each model axis).
    usable = np.array([build.x_mm, build.y_mm, build.z_mm]) - 2 * margin_mm
    max_scale = float(np.min(usable / extent))

    if target_mm is None:
        scale = max_scale
        clamped = False
    else:
        scale = target_mm / longest
        clamped = scale > max_scale
        if clamped:
            scale = max_scale

    out = mesh.copy()
    if center:
        cx, cy, cz = (xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2
        out.translate((-cx, -cy, -cz), inplace=True)
    out.scale(scale, inplace=True)

    extent_mm = tuple(round(float(e * scale), 2) for e in extent)
    if clamped:
        note = (
            f"Requested {target_mm} mm exceeds the build volume; "
            f"clamped to {extent_mm[int(np.argmax(extent))]} mm on the longest axis."
        )
    else:
        note = f"Longest axis {max(extent_mm)} mm; fits {build.x_mm}x{build.y_mm}x{build.z_mm} mm."
    return FitResult(out, scale, extent_mm, clamped, note)


# ---------------------------------------------------------------------------
# STL writing
# ---------------------------------------------------------------------------


def save_stl(mesh: pv.PolyData, path: str, *, binary: bool = True) -> None:
    """Write *mesh* to *path* as STL (binary by default — smaller files).

    The mesh is triangulated first if it carries any non-triangle faces
    (parametric shells are already triangles; this is a no-op for them).
    """
    if not path.lower().endswith(".stl"):
        path += ".stl"
    out = mesh if mesh.is_all_triangles else mesh.triangulate()
    out.save(path, binary=binary)


# ---------------------------------------------------------------------------
# One-call high-level API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExportResult:
    path: str
    n_points: int
    n_faces: int
    watertight: bool
    extent_mm: tuple[float, float, float]
    clip: str
    note: str


def _is_watertight(mesh: pv.PolyData) -> bool:
    edges = mesh.extract_feature_edges(
        boundary_edges=True, feature_edges=False,
        manifold_edges=False, non_manifold_edges=False,
    )
    return edges.n_points == 0


def export_to_stl(
    path: str,
    variety: str = "K3 surface",
    subtype: str | None = "Fermat quartic",
    params: dict[str, float] | None = None,
    *,
    clip: ClipMode | str = ClipMode.NONE,
    radius: float = 1.0,
    n: int = 200,
    build: BuildVolume = BAMBU_H2S,
    target_mm: float | None = 120.0,
    margin_mm: float = 5.0,
    binary: bool = True,
) -> ExportResult:
    """Generate a variety cross-section and write it to *path* as a print-ready STL.

    Mirrors the app's graph parameters: ``params`` are the slider values and
    ``clip``/``radius`` are the Clip Region shape + radius. With ``clip=sphere``
    the model is bounded by a sphere ("printed in a spherical pattern"); with
    ``clip=cube`` by a cube; with ``clip=none`` the full surface is exported.
    """
    clip = ClipMode(clip)
    if clip is ClipMode.NONE:
        mesh = generate_surface_mesh(variety, subtype, params)
    else:
        mesh = clip_for_print(
            variety, subtype, params, mode=clip, radius=radius, n=n
        )

    fit = fit_to_build_volume(
        mesh, build, target_mm=target_mm, margin_mm=margin_mm
    )
    save_stl(fit.mesh, path, binary=binary)
    final_path = path if path.lower().endswith(".stl") else path + ".stl"

    return ExportResult(
        path=final_path,
        n_points=fit.mesh.n_points,
        n_faces=fit.mesh.n_cells,
        watertight=_is_watertight(fit.mesh),
        extent_mm=fit.extent_mm,
        clip=clip.value,
        note=fit.note,
    )
