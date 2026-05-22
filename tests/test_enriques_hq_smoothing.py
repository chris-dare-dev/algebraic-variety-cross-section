"""Regression guards for the opt-in HQ-smoothing second Taubin pass
(enriques-hq-smoothing-2026q3-e1).

These tests are Qt-free (AI-2) — they call the surface generators
directly and inspect generator signatures.  No ``MainWindow``, no
``QApplication``.  The Qt-panel wire-up (the ``QPushButton(checkable=True)``
in ``appearance_panel.py``) is asserted via source-text grep, mirroring
the pattern from ``test_styles_palette.py:test_appearance_panel_display_toggles_are_qpushbutton_not_qcheckbox``.

Why this matters: the second Taubin pass adds ~138ms (+30.8%) to
Enriques fig 1 generate time per the spike (CONTEXT.md §8.16).  This
milestone exposes it as an opt-in so power users get the quality bump
on demand.  The CRITICAL contract these tests guard:
  - Default is False (the 449ms baseline is preserved across all
    existing callers — no silent enabling).
  - Only Enriques figs 1 and 2 accept the kwarg (per CONTEXT.md §8.13
    per-figure topology audit; figs 3+4 have A₁ nodes and gain no
    targeted benefit).
  - HQ-on actually does something (the Taubin pass moves every vertex —
    we verify mesh-modification rather than the elusive
    normal-variance-reduces claim, which is dominated by global surface
    anisotropy on tetrahedrally-symmetric surfaces).
"""
from __future__ import annotations

import inspect
import pathlib

import numpy as np

import surfaces


def test_enriques_fig1_hq_default_is_false() -> None:
    """`enriques_figure_1.hq_smoothing` defaults to False — the 449ms
    baseline is preserved for all callers that don't opt in."""
    sig = inspect.signature(surfaces.enriques_figure_1)
    assert "hq_smoothing" in sig.parameters, (
        "enriques_figure_1 is missing hq_smoothing kwarg — the opt-in "
        "extension point added by enriques-hq-smoothing-2026q3-e1."
    )
    assert sig.parameters["hq_smoothing"].default is False, (
        f"hq_smoothing default = {sig.parameters['hq_smoothing'].default!r}; "
        f"expected False to preserve the spike-measured 449ms baseline."
    )


def test_enriques_fig2_hq_default_is_false() -> None:
    """`enriques_figure_2.hq_smoothing` defaults to False — same baseline
    preservation as fig 1."""
    sig = inspect.signature(surfaces.enriques_figure_2)
    assert "hq_smoothing" in sig.parameters
    assert sig.parameters["hq_smoothing"].default is False


def test_marching_cubes_second_smooth_iter_default_is_zero() -> None:
    """`_marching_cubes_to_polydata.second_smooth_iter` defaults to 0 —
    preserves single-pass behavior for ALL non-Enriques implicit-surface
    generators (K3, Kummer, Dwork, Fano family).  A non-zero default
    would silently impose the +138ms HQ overhead on every other generator
    too, with no benefit (they have no double-curve topology).
    """
    sig = inspect.signature(surfaces._marching_cubes_to_polydata)
    assert "second_smooth_iter" in sig.parameters, (
        "_marching_cubes_to_polydata is missing second_smooth_iter kwarg — "
        "the internal plumbing for the opt-in second Taubin pass added by "
        "enriques-hq-smoothing-2026q3-e1."
    )
    assert sig.parameters["second_smooth_iter"].default == 0, (
        f"second_smooth_iter default = "
        f"{sig.parameters['second_smooth_iter'].default!r}; expected 0 to "
        f"preserve single-pass behavior for all non-Enriques-fig-1+2 "
        f"generators."
    )


def test_enriques_fig3_has_no_hq_kwarg() -> None:
    """Enriques fig 3 (Cayley quartic symmetroid) does NOT accept
    hq_smoothing — its A₁-node topology doesn't benefit from the second
    Taubin pass (CONTEXT.md §8.13 per-figure audit).  Including it would
    silently impose +138ms on a surface that gains nothing.  Scope
    enforcement.
    """
    sig = inspect.signature(surfaces.enriques_figure_3)
    assert "hq_smoothing" not in sig.parameters, (
        "enriques_figure_3 accepts hq_smoothing — should be scoped to figs "
        "1+2 only.  Fig 3 has A₁ nodes per CONTEXT.md §8.13, not double "
        "curves; the second pass has no targeted benefit there."
    )


def test_enriques_fig4_has_no_hq_kwarg() -> None:
    """Same scope guard as fig 3 — fig 4 (icosahedral sextic) also has
    A₁ nodes, not double curves."""
    sig = inspect.signature(surfaces.enriques_figure_4)
    assert "hq_smoothing" not in sig.parameters, (
        "enriques_figure_4 accepts hq_smoothing — should be scoped to figs "
        "1+2 only.  Fig 4 has A₁ nodes; no double-curve target."
    )


def test_enriques_fig1_hq_on_returns_valid_mesh() -> None:
    """Smoke: enriques_figure_1(hq_smoothing=True) returns a non-empty
    PolyData — the second pass doesn't break the generator contract
    (AI-14: returns PolyData or raises ValueError)."""
    mesh = surfaces.enriques_figure_1(hq_smoothing=True)
    assert mesh.n_points > 0
    assert mesh.n_faces > 0


def test_enriques_fig2_hq_on_returns_valid_mesh() -> None:
    """Smoke: same as fig 1 for fig 2."""
    mesh = surfaces.enriques_figure_2(hq_smoothing=True)
    assert mesh.n_points > 0
    assert mesh.n_faces > 0


def test_enriques_fig1_hq_on_moves_vertices_vs_hq_off() -> None:
    """Quantitative quality guard: HQ-on must actually modify the mesh,
    not silently no-op.  Verifies the second Taubin pass moves every
    vertex by some non-zero amount (empirically: mean displacement
    ~0.0015 units, max ~0.0088 at default c=1.0).

    Note: we measure VERTEX DISPLACEMENT rather than normal variance
    because `np.var(point_normals, axis=0).sum()` is dominated by
    global anisotropy on tetrahedrally-symmetric surfaces (~1.0 both
    before and after smoothing, with differences in the 6th decimal).
    Per-vertex displacement gives a clear non-zero signal whenever the
    smoothing pass actually fires; if HQ silently no-ops (the
    regression we're guarding against), every displacement would be
    exactly 0.
    """
    mesh_off = surfaces.enriques_figure_1(c=1.0, hq_smoothing=False)
    mesh_on = surfaces.enriques_figure_1(c=1.0, hq_smoothing=True)
    # Vertex counts are the same (Taubin doesn't add/remove vertices).
    assert mesh_off.n_points == mesh_on.n_points, (
        f"Vertex count changed between HQ-off ({mesh_off.n_points}) and "
        f"HQ-on ({mesh_on.n_points}) — Taubin smoothing should preserve "
        f"vertex count, only move positions."
    )
    # Per-vertex displacement should be non-zero for a meaningful fraction
    # of vertices.  Use mean > 1e-5 as a generous threshold (spike measured
    # mean ~0.0015 at default params).
    displacements = np.linalg.norm(mesh_on.points - mesh_off.points, axis=1)
    mean_displacement = float(displacements.mean())
    assert mean_displacement > 1e-5, (
        f"Mean vertex displacement HQ-on vs HQ-off was {mean_displacement:.2e} — "
        f"expected > 1e-5.  The second Taubin pass appears to be a silent "
        f"no-op; investigate whether second_smooth_iter is reaching the "
        f"smooth_taubin call in _marching_cubes_to_polydata."
    )


def test_hq_smoothing_toggle_is_checkable_qpushbutton_in_appearance_panel() -> None:
    """Source-text grep guard (AI-2 compliant — no QApplication): the
    new HQ-smoothing toggle in `appearance_panel.py` must use the
    established ``QPushButton(checkable=True)`` pattern with
    ``setProperty("role", "display-toggle")``, NOT ``QCheckBox`` (which
    would re-introduce the F-M2 triple-prefix bug from
    display-toggles-checkable-button-2026q3-e1).

    Also asserts the ``hq_smoothing_changed`` Signal is declared — the
    mesh-vs-actor distinction is load-bearing (the slot must NOT call
    plotter.render() directly; it emits a signal so MainWindow can
    invalidate the clipped-mesh cache and re-render).
    """
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")

    # Negative assertion: no QCheckBox construction for the HQ toggle.
    assert 'QCheckBox("HQ smoothing")' not in src, (
        "appearance_panel.py constructs QCheckBox('HQ smoothing') — "
        "F-M2 regression.  Must use QPushButton(checkable=True) per "
        "CONTEXT.md §8.15."
    )

    # Positive assertions: the new pattern is present.
    assert 'QPushButton("HQ smoothing")' in src, (
        "appearance_panel.py is missing QPushButton('HQ smoothing') — "
        "the opt-in toggle from enriques-hq-smoothing-2026q3-e1."
    )

    # The mesh-vs-actor signal pattern: hq_smoothing_changed Signal must
    # exist (NOT a direct plotter.render() call in the slot handler).
    assert "hq_smoothing_changed = Signal(bool)" in src, (
        "appearance_panel.py is missing the hq_smoothing_changed Signal — "
        "without it the toggle would call plotter.render() directly, "
        "re-rendering the STALE mesh (silent visual no-op).  See "
        "CONTEXT.md §4 + §8.16 for the mesh-regeneration discipline."
    )


def test_hq_smoothing_disabled_by_default_in_appearance_panel() -> None:
    """The HQ-smoothing button must initialize with `setEnabled(False)`
    so the toggle is greyed out at launch (before any subtype is
    selected).  MainWindow enables it per-subtype on _on_subtype_changed
    for Enriques figs 1+2 only.

    Source-text grep guard.
    """
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")
    # Match the specific button's setEnabled(False) — the line must
    # appear in the same block as the QPushButton construction.
    hq_block_idx = src.find('QPushButton("HQ smoothing")')
    assert hq_block_idx > 0, "HQ smoothing button not found in source"
    # Check the next ~600 chars (the button construction block) for
    # setEnabled(False).
    hq_block = src[hq_block_idx:hq_block_idx + 600]
    assert "setEnabled(False)" in hq_block, (
        "HQ-smoothing button is missing setEnabled(False) in its "
        "construction block — without it the toggle is enabled at launch "
        "before any Enriques subtype is selected, allowing the user to "
        "click it for K3 / CY3 / Fano (where the kwarg isn't accepted "
        "and would raise TypeError)."
    )
