"""Tests for the CAND-3 coarse-preview LOD surface (realtime-variety-render-e4b).

Three pure-Python (Qt-free, AI-2) surfaces are covered:

  * The `Surface.coarse_n` dataclass field: exists with a default of 0, every
    implicit-and-eligible generator in `VARIETIES` carries its expected
    measured floor (agent-a's n-sweep table); Hanson surfaces and the
    opt-out `fano_two_quadrics` stay at 0.
  * The `dispatch_mode(surface, in_drag)` free function — the AI-2-testable
    speed-routing predicate that replaced `should_render_on_drag` in
    `_on_params_preview_changed`. Three outcomes (`"coarse" | "full" |
    "skip"`) × four surface types (None, Hanson, coarse-eligible, opt-out)
    × in_drag ∈ {True, False}.
  * Per-surface coarse-`n` topology-honesty smoke tests — the floor for each
    opt-in generator produces a non-empty mesh that preserves its defining
    topological signature (bbox extent for smooth surfaces, octant symmetry
    for Kummer's 16 nodes, two-sheet symmetry for the sextic double solid).

No Qt, no `QApplication`, no `MainWindow` — pure NumPy / PyVista.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from surfaces import (
    VARIETIES,
    Surface,
    calabi_yau_asymmetric,
    calabi_yau_cubic,
    calabi_yau_dwork,
    calabi_yau_quintic,
    dispatch_mode,
    enriques_figure_1,
    enriques_figure_2,
    enriques_figure_3,
    enriques_figure_4,
    fano_klein_cubic,
    fano_segre_cubic,
    fano_sextic_double_solid,
    fano_two_quadrics,
    fermat_quartic,
    kummer_surface,
)


# ---------------------------------------------------------------------------
# Surface.coarse_n field — dataclass + registry contract
# ---------------------------------------------------------------------------

def test_surface_coarse_n_default_is_zero():
    """A new Surface with no `coarse_n` kwarg defaults to 0 (the "no
    coarse-LOD" sentinel — every Hanson generator and any future generator
    that hasn't been n-swept inherits this safe default)."""
    s = Surface("dummy", fermat_quartic, [])
    assert s.coarse_n == 0


# Expected per-surface coarse_n floors (agent-a's measured n-sweep table —
# see .claude/notes/milestones/realtime-variety-render-e4b/research/
# agent-a-brief.md §4.1). The test pins these literals so a typo or
# accidental edit in the VARIETIES registry fires loudly.
_EXPECTED_COARSE_N = {
    # opt-in (9 of 11 implicit generators)
    fermat_quartic: 80,
    kummer_surface: 100,
    enriques_figure_1: 80,
    enriques_figure_2: 80,
    enriques_figure_3: 80,
    enriques_figure_4: 80,
    calabi_yau_dwork: 100,
    fano_klein_cubic: 80,
    fano_segre_cubic: 80,
    fano_sextic_double_solid: 80,
    # opt-out — ε-tube fragility (fano_two_quadrics) + parametric (Hanson)
    fano_two_quadrics: 0,
    calabi_yau_quintic: 0,
    calabi_yau_cubic: 0,
    calabi_yau_asymmetric: 0,
}


def test_varieties_registry_coarse_n_matches_table():
    """Every Surface in the VARIETIES registry carries its expected coarse_n
    floor — pinning the table to a typo-resistant assertion."""
    for variety, subtypes in VARIETIES.items():
        for label, surf in subtypes.items():
            expected = _EXPECTED_COARSE_N[surf.generate]
            assert surf.coarse_n == expected, (
                f"{variety} / {label}: expected coarse_n={expected}, "
                f"got {surf.coarse_n}"
            )


def test_hanson_generators_have_coarse_n_zero():
    """AI-6 (layer 2): Hanson parametric surfaces MUST keep `coarse_n=0` —
    they never go through marching cubes, so a coarse `n` is meaningless and
    routing a parametric pipeline through it would silently produce wrong
    geometry (the `dispatch_mode` predicate returning "full" is layer 1; the
    worker's mode-agnosticism is layer 3)."""
    hanson_generators = (calabi_yau_quintic, calabi_yau_cubic, calabi_yau_asymmetric)
    for variety, subtypes in VARIETIES.items():
        for label, surf in subtypes.items():
            if surf.generate in hanson_generators:
                assert surf.coarse_n == 0, (
                    f"{variety} / {label} is Hanson parametric — "
                    f"coarse_n MUST be 0, got {surf.coarse_n}"
                )


def test_fano_two_quadrics_is_opt_out():
    """`fano_two_quadrics` is the documented opt-out (ε-tube fragility —
    voxel spacing approaches the tube width at any practical coarse floor;
    see agent-a brief §4.1 / VARIETIES comment block)."""
    for label, surf in VARIETIES["Fano 3-fold (ρ=1)"].items():
        if surf.generate is fano_two_quadrics:
            assert surf.coarse_n == 0
            return
    pytest.fail("fano_two_quadrics not found in the Fano 3-fold registry")


# ---------------------------------------------------------------------------
# dispatch_mode free function — the e4b speed-routing predicate
# ---------------------------------------------------------------------------

def _surf(typical_ms=0, coarse_n=0):
    """Build a minimal Surface for predicate testing (no generator call)."""
    return Surface("test", fermat_quartic, [], typical_ms=typical_ms, coarse_n=coarse_n)


# (surface, in_drag) -> expected mode
_DISPATCH_TABLE = [
    # None always skips (no surface selected)
    (None, True, "skip"),
    (None, False, "skip"),
    # Release path is always full
    (_surf(typical_ms=0, coarse_n=0),  False, "full"),
    (_surf(typical_ms=0, coarse_n=80), False, "full"),
    (_surf(typical_ms=30, coarse_n=0), False, "full"),
    # Drag path — Hanson (typical_ms > 0): full at every tick (e2 fast-path)
    (_surf(typical_ms=30, coarse_n=0),  True, "full"),
    (_surf(typical_ms=39, coarse_n=80), True, "full"),  # belt-and-suspenders
    # Drag path — implicit (typical_ms == 0): coarse iff coarse_n > 0
    (_surf(typical_ms=0, coarse_n=80),  True, "coarse"),
    (_surf(typical_ms=0, coarse_n=100), True, "coarse"),
    # Drag path — implicit opt-out (coarse_n == 0): skip
    (_surf(typical_ms=0, coarse_n=0),   True, "skip"),
]


@pytest.mark.parametrize("surface,in_drag,expected", _DISPATCH_TABLE)
def test_dispatch_mode(surface, in_drag, expected):
    # Layer-1 isolation note: the row `(_surf(typical_ms=39, coarse_n=80),
    # True, "full")` deliberately constructs a Surface with BOTH a Hanson
    # `typical_ms` AND a non-zero `coarse_n` (no such Surface exists in the
    # live registry today). It pins layer 1 of the AI-6 three-layer Hanson
    # skip: even if a future bug-induced Surface mis-configuration appeared,
    # `dispatch_mode` still returns "full" because `typical_ms > 0` is
    # checked before `coarse_n` — Hanson can never route to a coarse render.
    assert dispatch_mode(surface, in_drag) == expected


def test_dispatch_mode_real_surfaces():
    """Spot-check the predicate against the live registry — each variety's
    first subtype routes the way the e4b design expects."""
    # K3 Fermat — implicit with coarse_n=80
    fermat = VARIETIES["K3 surface"]["Fermat quartic"]
    assert dispatch_mode(fermat, in_drag=True) == "coarse"
    assert dispatch_mode(fermat, in_drag=False) == "full"

    # Hanson quintic — parametric with typical_ms=39
    hanson = VARIETIES["Calabi–Yau 3-fold"]["Hanson quintic  [Fig. 1]"]
    assert dispatch_mode(hanson, in_drag=True) == "full"   # e2 fast-path
    assert dispatch_mode(hanson, in_drag=False) == "full"

    # Two-quadrics — implicit opt-out (coarse_n=0)
    two_q = VARIETIES["Fano 3-fold (ρ=1)"]["Two-quadrics CI tube  [Fig. 3]"]
    assert dispatch_mode(two_q, in_drag=True) == "skip"
    assert dispatch_mode(two_q, in_drag=False) == "full"


# ---------------------------------------------------------------------------
# Per-surface topology-honesty smoke tests at the proposed coarse_n floor
# ---------------------------------------------------------------------------
#
# Pattern: render each opt-in surface at its `coarse_n` floor, assert
# non-empty + a per-generator topological signature.  These are smoke tests
# (one parameter point each — the registry default) — exhaustive sweeps
# would push past the 4 s suite budget.  See agent-a brief §4.4 for the
# signature taxonomy.

def _assert_nonempty(mesh) -> None:
    assert mesh.n_points > 0
    assert mesh.n_cells > 0


def test_coarse_n_fermat_quartic_smoke():
    """Fermat quartic at coarse_n=80: bbox extent ≈ 2 (smooth x⁴+y⁴+z⁴=1).

    Tight bound (1.95 < extent < 2.05) — Fermat at default params is smooth
    with no near-singular regions, so the coarse mesh's axial reach matches
    the production-n reach to within marching-cubes truncation noise. A
    looser bound (e.g. 1.5–2.5) would accept a clearly-broken mesh whose
    axial reach was clipped to 1.6, defeating the regression-guard purpose.
    """
    mesh = fermat_quartic(n=80)
    _assert_nonempty(mesh)
    _b = mesh.bounds
    # Default Fermat at c=1: |x|,|y|,|z| ≲ 1 → extent ≈ 2 in each axis.
    for axis, (lo, hi) in enumerate([(_b[0], _b[1]), (_b[2], _b[3]), (_b[4], _b[5])]):
        extent = hi - lo
        assert 1.95 < extent < 2.05, f"axis {axis} extent {extent} not near 2"


def test_coarse_n_kummer_16_node_symmetry():
    """Kummer at coarse_n=100: full S₄ tetrahedral symmetry preserved →
    8-octant vertex counts are equal within 10% (the 16 nodes lie at the
    tetrahedral vertices; their symmetric distribution IS the topology
    signature)."""
    mesh = kummer_surface(n=100)
    _assert_nonempty(mesh)
    pts = mesh.points
    # Count vertices per (sign(x), sign(y), sign(z)) octant.
    sx, sy, sz = (pts[:, 0] >= 0), (pts[:, 1] >= 0), (pts[:, 2] >= 0)
    octant_id = sx.astype(int) * 4 + sy.astype(int) * 2 + sz.astype(int)
    counts = np.bincount(octant_id, minlength=8)
    mean = counts.mean()
    # Tolerance: relative spread ≤ 10% — comfortably loose for coarse mesh
    # vertex assignment near octant boundaries.
    assert np.all(np.abs(counts - mean) / mean < 0.10), (
        f"Kummer 8-octant counts not symmetric within 10%: {counts.tolist()}"
    )


def test_coarse_n_enriques_figure_1_smoke():
    """Enriques canonical sextic at coarse_n=80: non-empty + bbox is the
    padded box (1.89·2 ≈ 3.78 each axis — clipping by sampling box, not by
    the actual surface — but the mesh fills the box symmetrically)."""
    mesh = enriques_figure_1(n=80)
    _assert_nonempty(mesh)
    _b = mesh.bounds
    for axis, (lo, hi) in enumerate([(_b[0], _b[1]), (_b[2], _b[3]), (_b[4], _b[5])]):
        extent = hi - lo
        assert 3.0 < extent < 4.0, f"Enriques fig 1 axis {axis} extent {extent}"


def test_coarse_n_enriques_figure_2_smoke():
    mesh = enriques_figure_2(n=80)
    _assert_nonempty(mesh)


def test_coarse_n_enriques_figure_3_smoke():
    mesh = enriques_figure_3(n=80)
    _assert_nonempty(mesh)


def test_coarse_n_enriques_figure_4_smoke():
    mesh = enriques_figure_4(n=80)
    _assert_nonempty(mesh)


def test_coarse_n_dwork_smoke():
    """Dwork at coarse_n=100, ψ=0.5 (default — well clear of the conifold)."""
    mesh = calabi_yau_dwork(n=100)
    _assert_nonempty(mesh)


def test_coarse_n_fano_klein_smoke():
    mesh = fano_klein_cubic(n=80)
    _assert_nonempty(mesh)


def test_coarse_n_fano_segre_smoke():
    mesh = fano_segre_cubic(n=80)
    _assert_nonempty(mesh)


def test_e4b_h2_hq_smoothing_gated_off_on_coarse_dispatches():
    """Regression guard for the e4b adversary HIGH-2 finding.

    HQ smoothing (`enriques-hq-smoothing-2026q3-e1`) adds a second Taubin
    pass (~138 ms at production n) to render. The CAND-3 coarse-LOD path
    fires the worker at `n=80` aiming for sub-100 ms drag previews; if HQ
    fires under coarse dispatches the +138 ms cost erodes the speed
    benefit AND undercuts the AI-15 Preview-badge honesty contract (a
    "Preview" render barely faster than full is misleading).

    The fix gates the HQ-eligibility expression on `not _is_coarse_active`
    in `app.py:_render_current`. AI-2 forbids driving the live dispatch
    Qt-free, so this is a source-text guard: assert the literal `and not
    _is_coarse_active` clause is present in the HQ-eligibility expression
    (the exact wording would only flip back to allowing HQ-on-coarse via a
    targeted regression — a typo wouldn't drop it silently).
    """
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    source = (repo_root / "app.py").read_text(encoding="utf-8")
    assert "and not _is_coarse_active" in source, (
        "app.py: the e4b HIGH-2 fix is missing — HQ-smoothing must be "
        "gated on `not _is_coarse_active` so coarse drag previews do not "
        "carry the second Taubin pass. Without this gate, every Enriques "
        "fig 1/2 drag tick with HQ enabled fires `second_smooth_iter=40` "
        "at coarse n, adding ~138 ms and defeating the LOD speed benefit."
    )


def test_coarse_n_fano_sextic_double_solid_two_sheets():
    """Sextic double solid at coarse_n=80: the two-sheet z-symmetry (upper
    and lower domes joined at the sextic equator) survives coarsening —
    the mesh spans both positive and negative z."""
    mesh = fano_sextic_double_solid(n=80)
    _assert_nonempty(mesh)
    z = mesh.points[:, 2]
    assert z.min() < 0 < z.max(), (
        f"Sextic double solid lost a sheet at coarse_n=80: "
        f"z range [{z.min():.3f}, {z.max():.3f}]"
    )
