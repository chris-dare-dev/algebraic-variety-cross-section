"""Tests for the export/ STL pipeline. Qt-free (AI-2)."""

from __future__ import annotations

import numpy as np
import pytest

from export.printable import (
    BAMBU_H2S,
    FIELD_PROVIDERS,
    BuildVolume,
    ClipMode,
    clip_for_print,
    export_to_stl,
    fit_to_build_volume,
    generate_surface_mesh,
    save_stl,
)


def _open_edges(mesh):
    return mesh.extract_feature_edges(
        boundary_edges=True, feature_edges=False,
        manifold_edges=False, non_manifold_edges=False,
    ).n_points


# ---------------------------------------------------------------------------
# Unclipped generation
# ---------------------------------------------------------------------------


def test_fermat_default_is_watertight():
    """x^4+y^4+z^4=1 is closed -> directly printable, no clip needed."""
    mesh = generate_surface_mesh("K3 surface", "Fermat quartic", {"c": 1.0})
    assert mesh.n_points > 0
    assert mesh.is_all_triangles
    assert _open_edges(mesh) == 0


def test_generate_merges_defaults():
    """Omitted params fall back to the ParamSpec defaults."""
    mesh = generate_surface_mesh("K3 surface", "Fermat quartic")  # all defaults
    assert mesh.n_points > 0


def test_unknown_variety_and_subtype_raise():
    with pytest.raises(KeyError):
        generate_surface_mesh("not a variety")
    with pytest.raises(KeyError):
        generate_surface_mesh("K3 surface", "not a subtype")


# ---------------------------------------------------------------------------
# CSG clipping stays watertight
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", [ClipMode.SPHERE, ClipMode.CUBE])
def test_clip_is_watertight_and_bounded(mode):
    radius = 0.85
    solid = clip_for_print(
        "K3 surface", "Fermat quartic", {"c": 1.0},
        mode=mode, radius=radius, n=96,
    )
    assert solid.n_points > 0
    assert _open_edges(solid) == 0  # watertight after CSG cap
    # Nothing escapes the clip box.
    xmin, xmax, ymin, ymax, zmin, zmax = solid.bounds
    assert max(abs(xmin), abs(xmax), abs(ymin), abs(ymax), abs(zmin), abs(zmax)) <= radius + 1e-6


def test_clip_unsupported_surface_raises():
    # Parametric Hanson Calabi-Yau cross-sections are open 2-surfaces (no
    # enclosed solid), so they have no field provider and cannot be CSG-clipped.
    # (Every IMPLICIT surface is now clip-capable — see test_csg_clip_families.)
    with pytest.raises(NotImplementedError):
        clip_for_print("Calabi–Yau 3-fold", "Hanson quintic  [Fig. 1]",
                       mode=ClipMode.SPHERE, radius=2.0)


def test_clip_rejects_none_and_bad_radius():
    with pytest.raises(ValueError):
        clip_for_print("K3 surface", "Fermat quartic", mode=ClipMode.NONE, radius=1.0)
    with pytest.raises(ValueError):
        clip_for_print("K3 surface", "Fermat quartic", mode=ClipMode.SPHERE, radius=0.0)


# ---------------------------------------------------------------------------
# Anti-drift: export field providers must match the live generators
# ---------------------------------------------------------------------------


def test_fermat_field_matches_generator_extent():
    """A sphere clip whose radius exceeds the Fermat surface must reproduce
    the full surface (sphere cuts nothing) — guarding against the export field
    formula drifting from varieties.k3.fermat_quartic. The Fermat generator's
    sampling box (bounds 2.5) fully contains the c=1 surface ([-1,1]), so the
    extents are directly comparable (unlike Kummer, which the generator crops
    at its own adaptive box)."""
    full = generate_surface_mesh("K3 surface", "Fermat quartic", {"c": 1.0})
    clipped = clip_for_print("K3 surface", "Fermat quartic", {"c": 1.0},
                             mode=ClipMode.SPHERE, radius=1.6, n=160)
    fx, cx = full.bounds, clipped.bounds
    for a, b in [(fx[1] - fx[0], cx[1] - cx[0]),
                 (fx[3] - fx[2], cx[3] - cx[2]),
                 (fx[5] - fx[4], cx[5] - cx[4])]:
        assert abs(a - b) < 0.1, f"extent drift {a:.3f} vs {b:.3f}"


def test_field_provider_signs_are_analytic():
    """Exact field-value checks: the providers must reproduce the documented
    formulae (sign convention f<0 inside). Independent of meshing, so this is
    the true anti-drift guard for the wired providers."""
    from export.printable import _fermat_field, _kummer_field

    # A single-value grid evaluates at the diagonal point (t,t,t).
    # Fermat: f(0,0,0) = -c ; f(2,2,2) = 3*2^4 - c = 47 at c=1.
    g0 = np.array([0.0])
    assert _fermat_field(g0, {"c": 1.0})[0, 0, 0] == pytest.approx(-1.0)
    g2 = np.array([2.0])
    assert _fermat_field(g2, {"c": 1.0})[0, 0, 0] == pytest.approx(3 * 16.0 - 1.0)

    # Kummer at origin: (0 - mu^2)^2 - lambda*(1*1*1*1) = mu^4 - lambda.
    mu2 = 1.3
    lam = (3 * mu2 - 1) / (3 - mu2)
    assert _kummer_field(g0, {"mu_squared": mu2})[0, 0, 0] == pytest.approx(mu2 * mu2 - lam)

    # Kummer degenerate-parameter guards mirror the generator (AI-14).
    with pytest.raises(ValueError):
        _kummer_field(g0, {"mu_squared": 3.0})
    with pytest.raises(ValueError):
        _kummer_field(g0, {"mu_squared": 0.1})


# ---------------------------------------------------------------------------
# Build-volume fitting
# ---------------------------------------------------------------------------


def test_fit_scales_longest_axis_to_target():
    mesh = generate_surface_mesh("K3 surface", "Fermat quartic", {"c": 1.0})
    fit = fit_to_build_volume(mesh, BAMBU_H2S, target_mm=100.0)
    assert max(fit.extent_mm) == pytest.approx(100.0, abs=0.5)
    assert not fit.clamped


def test_fit_clamps_oversized_target():
    mesh = generate_surface_mesh("K3 surface", "Fermat quartic", {"c": 1.0})
    fit = fit_to_build_volume(mesh, BAMBU_H2S, target_mm=10_000.0, margin_mm=5.0)
    assert fit.clamped
    assert BAMBU_H2S.fits(fit.extent_mm, margin_mm=0.0)


def test_buildvolume_fits():
    bv = BuildVolume(100, 100, 100)
    assert bv.fits((80, 80, 80), margin_mm=5)
    assert not bv.fits((95, 10, 10), margin_mm=5)


# ---------------------------------------------------------------------------
# End-to-end STL write
# ---------------------------------------------------------------------------


def test_export_to_stl_roundtrip(tmp_path):
    out = tmp_path / "fermat.stl"
    result = export_to_stl(str(out), clip="none", target_mm=120.0)
    assert out.exists()
    assert out.stat().st_size > 0
    assert result.watertight
    assert max(result.extent_mm) == pytest.approx(120.0, abs=1.0)


def test_export_sphere_clip_roundtrip(tmp_path):
    out = tmp_path / "ball.stl"
    result = export_to_stl(
        str(out), clip="sphere", radius=0.85, n=96, target_mm=90.0,
    )
    assert out.exists()
    assert result.watertight
    assert result.clip == "sphere"


def test_save_stl_appends_extension(tmp_path):
    mesh = generate_surface_mesh("K3 surface", "Fermat quartic", {"c": 1.0})
    base = tmp_path / "noext"
    save_stl(mesh, str(base))
    assert (tmp_path / "noext.stl").exists()
