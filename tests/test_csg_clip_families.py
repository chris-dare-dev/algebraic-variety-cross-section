"""CSG-clip coverage tests for ALL implicit variety families. Qt-free (AI-2).

These tests guard the field providers added to ``export.printable`` that extend
watertight sphere/cube CSG clipping from the K3 family to every implicit
surface (9 Enriques/Dwork/Fano providers + the 2 pre-existing K3 providers).

The strongest guard is the ANTI-DRIFT block: each provider's numpy field is
compared, after the same ``np.clip(±N)`` the kernel applies, against the live
Numba kernel in ``varieties._kernels`` at many random points AND many random
parameter values drawn from the registry ParamSpec ranges. A formula or
pre-compute drift between the export provider and the generator's kernel is
caught at rtol=atol=1e-9.
"""

from __future__ import annotations

import numpy as np
import pytest

from varieties.registry import VARIETIES
from varieties import _kernels as K
from export.printable import (
    FIELD_PROVIDERS,
    ClipMode,
    clip_for_print,
    supports_csg_clip,
    _enriques_fig1_field,
    _enriques_fig2_field,
    _enriques_fig3_field,
    _enriques_fig4_field,
    _dwork_field,
    _klein_cubic_field,
    _segre_cubic_field,
    _two_quadrics_field,
    _sextic_double_solid_field,
)


SEED = 20260620


# ---------------------------------------------------------------------------
# Kernel-call adapters
# ---------------------------------------------------------------------------
#
# Each entry maps a (variety, subtype) provider to:
#   * the export field provider fn
#   * a closure that fills a fresh F via the matching Numba kernel using the
#     SAME scalar pre-computes the generator computes
#   * the kernel's clip bound N (provider field is clipped to ±N before compare)
# The kernel pre-computes are transcribed from the generators (k3/enriques/
# calabi_yau/fano) so the comparison is provider-vs-kernel, end to end.


def _kernel_enriques_fig1(g, params):
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._enriques_fig1_field_kernel(g, params.get("c", 1.0), F)
    return F


def _kernel_enriques_fig2(g, params):
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._enriques_fig2_field_kernel(
        g, params.get("lam0", 1.0), params.get("lam3", 2.0), params.get("c", 1.0), F
    )
    return F


def _kernel_enriques_fig3(g, params):
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._enriques_fig3_field_kernel(g, params.get("k", 16.0), F)
    return F


def _kernel_enriques_fig4(g, params):
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    phi2 = phi * phi
    one_plus_2phi = 1.0 + 2.0 * phi
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._enriques_fig4_field_kernel(g, params.get("tau", 0.18), phi2, one_plus_2phi, F)
    return F


def _kernel_dwork(g, params):
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._dwork_field_kernel(g, params.get("psi", 0.5), F)
    return F


def _kernel_klein(g, params):
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._klein_cubic_field_kernel(g, params.get("z0", 0.4), F)
    return F


def _kernel_segre(g, params):
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._segre_cubic_field_kernel(g, params.get("a", 0.3), params.get("b", -0.4), F)
    return F


def _kernel_two_quadrics(g, params):
    lam = (-0.5, 0.0, 0.5, 1.0, 1.5)
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._two_quadrics_field_kernel(
        g,
        params.get("p", 0.3),
        params.get("q", -0.2),
        params.get("mu", 0.5),
        params.get("eps", 0.18),
        lam[0], lam[1], lam[2], lam[3], lam[4],
        F,
    )
    return F


def _kernel_sextic(g, params):
    R = params.get("R", 1.2)
    r2 = R * R
    r6 = r2 * r2 * r2
    F = np.empty((g.size,) * 3, dtype=np.float64)
    K._sextic_double_solid_field_kernel(g, params.get("alpha", 0.0), r6, F)
    return F


# id -> (variety, subtype, provider, kernel_adapter, clip_N)
PROVIDERS = {
    "enriques_fig1": (
        "Enriques surface", "Canonical sextic  [Fig. 1]",
        _enriques_fig1_field, _kernel_enriques_fig1, 10.0,
    ),
    "enriques_fig2": (
        "Enriques surface", "Diagonal λ-family  [Fig. 2]",
        _enriques_fig2_field, _kernel_enriques_fig2, 10.0,
    ),
    "enriques_fig3": (
        "Enriques surface", "Cayley symmetroid  [Fig. 3]",
        _enriques_fig3_field, _kernel_enriques_fig3, 50.0,
    ),
    "enriques_fig4": (
        "Enriques surface", "Icosahedral sextic  [Fig. 4]",
        _enriques_fig4_field, _kernel_enriques_fig4, 20.0,
    ),
    "dwork": (
        "Calabi–Yau 3-fold", "Dwork pencil  [Fig. 4]",
        _dwork_field, _kernel_dwork, 100.0,
    ),
    "klein": (
        "Fano 3-fold (ρ=1)", "Klein cubic  [Fig. 1]",
        _klein_cubic_field, _kernel_klein, 50.0,
    ),
    "segre": (
        "Fano 3-fold (ρ=1)", "Segre cubic  [Fig. 2]",
        _segre_cubic_field, _kernel_segre, 1000.0,
    ),
    "two_quadrics": (
        "Fano 3-fold (ρ=1)", "Two-quadrics CI tube  [Fig. 3]",
        _two_quadrics_field, _kernel_two_quadrics, 200.0,
    ),
    "sextic": (
        "Fano 3-fold (ρ=1)", "Sextic double solid  [Fig. 4]",
        _sextic_double_solid_field, _kernel_sextic, 200.0,
    ),
}

ALL_IMPLICIT = [
    ("K3 surface", "Fermat quartic"),
    ("K3 surface", "Kummer surface"),
] + [(v, s) for (v, s, *_rest) in PROVIDERS.values()]

HANSON_SUBTYPES = [
    ("Calabi–Yau 3-fold", "Hanson quintic  [Fig. 1]"),
    ("Calabi–Yau 3-fold", "Hanson cubic torus  [Fig. 2]"),
    ("Calabi–Yau 3-fold", "Hanson asymmetric (5,3)  [Fig. 3]"),
]


def _param_ranges(variety, subtype):
    """ParamSpec (name, min, max) tuples for a registry subtype."""
    surface = VARIETIES[variety][subtype]
    return [(p.name, p.minimum, p.maximum) for p in surface.params]


def _random_params(rng, variety, subtype):
    """A dict of params sampled uniformly inside each ParamSpec range."""
    out = {}
    for name, lo, hi in _param_ranges(variety, subtype):
        out[name] = float(rng.uniform(lo, hi))
    return out


# ---------------------------------------------------------------------------
# 1. ANTI-DRIFT: provider field == kernel field (clipped to ±N) everywhere
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pid", list(PROVIDERS))
def test_provider_matches_kernel_random_points_and_params(pid):
    """For many random param sets, the provider's clipped field must equal the
    live Numba kernel on a shared random grid, at rtol=atol=1e-9."""
    variety, subtype, provider, kernel_adapter, clip_n = PROVIDERS[pid]
    rng = np.random.default_rng(SEED + hash(pid) % 9973)

    for _trial in range(12):
        params = _random_params(rng, variety, subtype)
        # Random asymmetric grid covering positive+negative coords (the Klein
        # cubic is asymmetric in x,y,z, so a symmetric grid would hide a
        # transpose bug — keep distinct, unsorted-but-1D sample coords).
        g = rng.uniform(-2.5, 2.5, size=7).astype(np.float64)

        provided = provider(g, params)
        clipped = np.clip(provided, -clip_n, clip_n)
        expected = kernel_adapter(g, params)
        np.testing.assert_allclose(
            clipped, expected, rtol=1e-9, atol=1e-9,
            err_msg=f"{pid} provider drifted from kernel at params={params}",
        )


@pytest.mark.parametrize("pid", list(PROVIDERS))
def test_provider_matches_kernel_at_registry_defaults(pid):
    """Same comparison, pinned at the exact ParamSpec defaults (the value the
    GUI uses on first load)."""
    variety, subtype, provider, kernel_adapter, clip_n = PROVIDERS[pid]
    defaults = VARIETIES[variety][subtype].defaults()
    g = np.linspace(-2.0, 2.0, 11)
    provided = np.clip(provider(g, defaults), -clip_n, clip_n)
    expected = kernel_adapter(g, defaults)
    np.testing.assert_allclose(provided, expected, rtol=1e-9, atol=1e-9)


def test_provider_passes_empty_params_uses_defaults():
    """An empty params dict must fall back to ParamSpec defaults (the
    clip_for_print path passes ``params or {}``)."""
    # Spot-check a provider whose default differs from the numeric placeholder.
    g = np.linspace(-1.5, 1.5, 9)
    variety, subtype = "Fano 3-fold (ρ=1)", "Sextic double solid  [Fig. 4]"
    defaults = VARIETIES[variety][subtype].defaults()
    np.testing.assert_allclose(
        _sextic_double_solid_field(g, {}),
        _sextic_double_solid_field(g, defaults),
        rtol=1e-12, atol=1e-12,
    )


# ---------------------------------------------------------------------------
# 2. WATERTIGHT + MANIFOLD CSG clip, both sphere AND cube, every implicit
# ---------------------------------------------------------------------------


def _boundary_edges(mesh):
    return mesh.extract_feature_edges(
        boundary_edges=True, feature_edges=False,
        manifold_edges=False, non_manifold_edges=False,
    ).n_points


def _non_manifold_edges(mesh):
    return mesh.extract_feature_edges(
        boundary_edges=False, feature_edges=False,
        manifold_edges=False, non_manifold_edges=True,
    ).n_points


# (variety, subtype, params, radius) tuned so each surface has a non-empty
# zero set inside the clip box at modest resolution.
_CLIP_CASES = {
    ("K3 surface", "Fermat quartic"): ({"c": 1.0}, 0.85),
    ("K3 surface", "Kummer surface"): ({"mu_squared": 1.3}, 2.2),
    ("Enriques surface", "Canonical sextic  [Fig. 1]"): ({"c": 1.0}, 1.4),
    ("Enriques surface", "Diagonal λ-family  [Fig. 2]"): ({}, 1.4),
    ("Enriques surface", "Cayley symmetroid  [Fig. 3]"): ({"k": 16.0}, 2.0),
    ("Enriques surface", "Icosahedral sextic  [Fig. 4]"): ({"tau": 0.18}, 1.4),
    ("Calabi–Yau 3-fold", "Dwork pencil  [Fig. 4]"): ({"psi": 0.5}, 1.5),
    ("Fano 3-fold (ρ=1)", "Klein cubic  [Fig. 1]"): ({"z0": 0.4}, 1.8),
    ("Fano 3-fold (ρ=1)", "Segre cubic  [Fig. 2]"): ({"a": 0.3, "b": -0.4}, 2.0),
    ("Fano 3-fold (ρ=1)", "Two-quadrics CI tube  [Fig. 3]"): (
        {"p": 0.3, "q": -0.2, "mu": 0.5, "eps": 0.30}, 1.4
    ),
    ("Fano 3-fold (ρ=1)", "Sextic double solid  [Fig. 4]"): (
        {"R": 1.2, "alpha": 0.0}, 1.4
    ),
}


@pytest.mark.parametrize("key", list(_CLIP_CASES))
@pytest.mark.parametrize("mode", [ClipMode.SPHERE, ClipMode.CUBE])
def test_csg_clip_watertight_manifold_bounded(key, mode):
    variety, subtype = key
    params, radius = _CLIP_CASES[key]
    solid = clip_for_print(
        variety, subtype, params, mode=mode, radius=radius, n=80, smooth_iter=8,
    )
    assert solid.n_points > 0, f"{key} {mode} produced empty mesh"
    assert _boundary_edges(solid) == 0, f"{key} {mode} not watertight"
    assert _non_manifold_edges(solid) == 0, f"{key} {mode} non-manifold"
    xmin, xmax, ymin, ymax, zmin, zmax = solid.bounds
    assert (
        max(abs(xmin), abs(xmax), abs(ymin), abs(ymax), abs(zmin), abs(zmax))
        <= radius + 1e-6
    ), f"{key} {mode} escaped clip box"


# ---------------------------------------------------------------------------
# 3. ANALYTIC SIGN + reference-value checks per provider
# ---------------------------------------------------------------------------


def test_analytic_reference_values():
    """Exact field values at chosen points: interior (f<0) and a documented
    reference value. Independent of meshing — the pure anti-drift on math."""
    g0 = np.array([0.0])

    # Enriques fig1: f(0,0,0) = 0 (all terms vanish at the origin).
    assert _enriques_fig1_field(g0, {"c": 1.0})[0, 0, 0] == pytest.approx(0.0)
    # Off-origin interior point: pick (0.6,0.6,0.6) with c=1 — the XYZ mixing
    # term is positive there, but the diagonal interior of a single octant
    # lobe sits below zero for the canonical sextic at a small positive triple.
    pt = np.array([0.3])
    # f(0.3,0.3,0.3): X2Y2 terms = 3*(0.09*0.09)=0.0243; X2Y2Z2 = 0.09^3;
    # c*XYZ*(1+3*0.09) = 0.027*(1.27). Compute exactly to assert.
    x = 0.3
    x2 = x * x
    exact = 3 * x2 * x2 + x2 * x2 * x2 + 1.0 * (x * x * x) * (1.0 + 3 * x2)
    assert _enriques_fig1_field(pt, {"c": 1.0})[0, 0, 0] == pytest.approx(exact)

    # Enriques fig2 at origin = 0 likewise.
    assert _enriques_fig2_field(g0, {})[0, 0, 0] == pytest.approx(0.0)

    # Enriques fig3 (Cayley): s(0)=0 -> f(0,0,0) = 0.
    assert _enriques_fig3_field(g0, {"k": 16.0})[0, 0, 0] == pytest.approx(0.0)

    # Enriques fig4 (Endrass): at origin P=0, inner=-1, Q=(1+2φ)*1.
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    q0 = (1.0 + 2.0 * phi)
    assert _enriques_fig4_field(g0, {"tau": 0.18})[0, 0, 0] == pytest.approx(
        -0.18 * q0
    )
    # Interior of the central body: f(0,0,0) = -0.18*(1+2φ) < 0.
    assert _enriques_fig4_field(g0, {"tau": 0.18})[0, 0, 0] < 0

    # Dwork: f(0,0,0) = 2 (>0 -> origin is OUTSIDE the solid; the +2 const).
    assert _dwork_field(g0, {"psi": 0.5})[0, 0, 0] == pytest.approx(2.0)
    # A genuine interior point: along x=y=z=t large negative makes X5+Y5+Z5+2
    # dominate negative -> f<0. t=-1.2: 3*(-1.2)^5 + 2 - 5*0.5*(-1.2)^3.
    t = -1.2
    g = np.array([t])
    exact_dwork = 3 * t**5 + 2.0 - 5.0 * 0.5 * (t * t * t)
    assert _dwork_field(g, {"psi": 0.5})[0, 0, 0] == pytest.approx(exact_dwork)
    assert exact_dwork < 0  # interior

    # Klein cubic: f(0,0,0) = z0^2 at default z0=0.4 -> 0.16.
    assert _klein_cubic_field(g0, {"z0": 0.4})[0, 0, 0] == pytest.approx(0.16)
    # Interior point with x large negative makes f<0: x=-2,y=z=0 -> -2+0.16<0.
    gx = np.array([-2.0, 0.0])
    fld = _klein_cubic_field(gx, {"z0": 0.4})
    assert fld[0, 1, 1] == pytest.approx(-2.0 + 0.16)  # (x,y,z)=(-2,0,0)
    assert fld[0, 1, 1] < 0

    # Segre cubic: f(0,0,0) = a^3 + b^3 - (a+b)^3.
    a, b = 0.3, -0.4
    seg0 = a**3 + b**3 - (a + b) ** 3
    assert _segre_cubic_field(g0, {"a": a, "b": b})[0, 0, 0] == pytest.approx(seg0)

    # Two-quadrics: at origin Q1 = p2+q2-1, Q2 = lam3*p2+lam4*q2-mu.
    p, q, mu, eps = 0.3, -0.2, 0.5, 0.18
    Q1 = p * p + q * q - 1.0
    Q2 = 1.0 * (p * p) + 1.5 * (q * q) - mu
    tq0 = Q1 * Q1 + Q2 * Q2 - eps * eps
    assert _two_quadrics_field(g0, {"p": p, "q": q, "mu": mu, "eps": eps})[
        0, 0, 0
    ] == pytest.approx(tq0)
    # On the tube core (Q1=Q2=0 would give f=-eps^2<0); origin here is positive,
    # but the field genuinely dips below zero on the tube. Confirm an interior
    # point: choose where Q1 small. Just assert the analytic value matches.

    # Sextic double solid: f(0,0,0) = -R^6 (interior, f<0) at R=1.2.
    R = 1.2
    r6 = (R * R) ** 3
    assert _sextic_double_solid_field(g0, {"R": R, "alpha": 0.0})[
        0, 0, 0
    ] == pytest.approx(-r6)
    assert _sextic_double_solid_field(g0, {"R": R, "alpha": 0.0})[0, 0, 0] < 0


def test_two_quadrics_has_interior_point():
    """The ε-tube field must go negative somewhere inside its band (a true
    enclosed solid) — sample the grid and assert a negative voxel exists."""
    g = np.linspace(-1.2, 1.2, 41)
    F = _two_quadrics_field(g, {"p": 0.3, "q": -0.2, "mu": 0.5, "eps": 0.30})
    assert F.min() < 0, "two-quadrics tube has no interior (no f<0 voxel)"


# ---------------------------------------------------------------------------
# 4. Parametric Hanson subtypes raise NotImplementedError on clip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variety,subtype", HANSON_SUBTYPES)
def test_hanson_clip_raises_notimplemented(variety, subtype):
    with pytest.raises(NotImplementedError):
        clip_for_print(variety, subtype, mode=ClipMode.SPHERE, radius=1.5)


# ---------------------------------------------------------------------------
# 5. supports_csg_clip coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variety,subtype", ALL_IMPLICIT)
def test_supports_csg_clip_true_for_implicit(variety, subtype):
    assert supports_csg_clip(variety, subtype) is True


@pytest.mark.parametrize("variety,subtype", HANSON_SUBTYPES)
def test_supports_csg_clip_false_for_hanson(variety, subtype):
    assert supports_csg_clip(variety, subtype) is False


def test_supports_csg_clip_unknown_names():
    assert supports_csg_clip("not a variety") is False
    assert supports_csg_clip("K3 surface", "not a subtype") is False
    assert supports_csg_clip("K3 surface", None) is True  # first subtype = Fermat


def test_supports_csg_clip_counts():
    """Exactly 11 implicit (variety,subtype) pairs are wired; the 3 Hanson
    pairs are not."""
    assert len(FIELD_PROVIDERS) == 11
    for v, s in HANSON_SUBTYPES:
        assert (v, s) not in FIELD_PROVIDERS


# ---------------------------------------------------------------------------
# 6. Degenerate-parameter guards mirror the generators (AI-14)
# ---------------------------------------------------------------------------


def test_kummer_guards_still_raise():
    """The pre-existing Kummer provider keeps its AI-14 ValueErrors (regression
    guard alongside the new providers)."""
    from export.printable import _kummer_field

    g0 = np.array([0.0])
    with pytest.raises(ValueError):
        _kummer_field(g0, {"mu_squared": 3.0})       # pole
    with pytest.raises(ValueError):
        _kummer_field(g0, {"mu_squared": 0.1})       # no zero set


def test_clip_for_print_propagates_kummer_guard():
    """clip_for_print surfaces the provider's ValueError (not swallowed)."""
    with pytest.raises(ValueError):
        clip_for_print(
            "K3 surface", "Kummer surface", {"mu_squared": 3.0},
            mode=ClipMode.SPHERE, radius=2.0, n=48,
        )


def test_new_providers_have_no_spurious_guards():
    """The 9 new implicit families have no degenerate-parameter ValueError in
    their generators, so their providers must evaluate cleanly across their
    full ParamSpec ranges (smoke over endpoints)."""
    rng = np.random.default_rng(SEED)
    g = np.linspace(-1.0, 1.0, 5)
    for variety, subtype, provider, _k, _n in PROVIDERS.values():
        for name, lo, hi in _param_ranges(variety, subtype):
            for val in (lo, hi):
                # build a params dict at this endpoint, rest at default
                params = VARIETIES[variety][subtype].defaults()
                params[name] = val
                out = provider(g, params)
                assert np.all(np.isfinite(out)), (
                    f"{subtype} produced non-finite field at {name}={val}"
                )
