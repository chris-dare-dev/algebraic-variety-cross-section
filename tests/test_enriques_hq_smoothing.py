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
    assert 'QCheckBox("Double-pass smooth")' not in src, (
        "appearance_panel.py constructs QCheckBox('Double-pass smooth') — "
        "F-M2 regression.  Must use QPushButton(checkable=True) per "
        "CONTEXT.md §8.15."
    )

    # Positive assertions: the new pattern is present.
    # hq-smoothing-label-rename-2026q3-e1 (F-L1 closure): user-visible
    # label renamed from "HQ smoothing" → "Double-pass smooth".  Internal
    # symbol names (_hq_smoothing_cb, hq_smoothing_changed) STAY.
    assert 'QPushButton("Double-pass smooth")' in src, (
        "appearance_panel.py is missing QPushButton('Double-pass smooth') — "
        "the opt-in toggle from enriques-hq-smoothing-2026q3-e1, relabeled "
        "by hq-smoothing-label-rename-2026q3-e1."
    )

    # The mesh-vs-actor signal pattern: hq_smoothing_changed Signal must
    # exist (NOT a direct plotter.render() call in the slot handler).
    assert "hq_smoothing_changed = Signal(bool)" in src, (
        "appearance_panel.py is missing the hq_smoothing_changed Signal — "
        "without it the toggle would call plotter.render() directly, "
        "re-rendering the STALE mesh (silent visual no-op).  See "
        "CONTEXT.md §4 + §8.16 for the mesh-regeneration discipline."
    )


def test_hq_smoothing_frozensets_stay_in_sync_with_varieties_registry() -> None:
    """The two frozensets in app.py (`_HQ_SMOOTHING_ELIGIBLE_SUBTYPES`
    and `_HQ_SMOOTHING_ELIGIBLE_GENERATORS`) must stay in 1-to-1
    correspondence with the VARIETIES registry entries they gate.
    Without this guard, a developer adding "Enriques Fig. 5" to one
    frozenset but forgetting the other gets no test feedback — the
    button silently breaks for the new subtype.

    Asserts:
      (a) every subtype string in `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES`
          exists as a key in `VARIETIES["Enriques surface"]`, AND
      (b) for each such key, the registered surface's `generate`
          callable is exactly the corresponding member of
          `_HQ_SMOOTHING_ELIGIBLE_GENERATORS`.

    Added in enriques-hq-smoothing-2026q3-e1 rect (adversary M2):
    closes the frozenset-sync maintenance trap.
    """
    # Import the constants from app.py without instantiating MainWindow
    # (which would require QApplication and violate AI-2).  Module-level
    # `_HQ_SMOOTHING_*` constants are evaluated at import time.
    import importlib
    app_module = importlib.import_module("app")
    eligible_subtypes = app_module._HQ_SMOOTHING_ELIGIBLE_SUBTYPES
    eligible_generators = app_module._HQ_SMOOTHING_ELIGIBLE_GENERATORS

    from surfaces import VARIETIES

    enriques_subtypes = VARIETIES["Enriques surface"]

    # (a) Every eligible subtype string exists in the registry.
    for subtype_name in eligible_subtypes:
        assert subtype_name in enriques_subtypes, (
            f"_HQ_SMOOTHING_ELIGIBLE_SUBTYPES contains {subtype_name!r} but "
            f"VARIETIES['Enriques surface'] has no such key.  Either fix "
            f"the string typo or add the missing subtype to the registry."
        )
        # (b) The registered surface's generate is in the eligible-generators set.
        registered_generator = enriques_subtypes[subtype_name].generate
        assert registered_generator in eligible_generators, (
            f"VARIETIES['Enriques surface'][{subtype_name!r}].generate "
            f"({registered_generator.__name__}) is NOT in "
            f"_HQ_SMOOTHING_ELIGIBLE_GENERATORS — the two frozensets drifted. "
            f"Both must enumerate the same set of (subtype-name, generator) "
            f"pairs for the per-subtype UI gate to align with the kwarg-"
            f"injection runtime gate."
        )

    # Symmetric check: every generator in the eligible-generators set has at
    # least one corresponding subtype string in the eligible-subtypes set
    # (catches the "added a generator but forgot the dropdown string" case).
    generators_with_subtype = {
        enriques_subtypes[n].generate for n in eligible_subtypes
    }
    drifted_generators = eligible_generators - generators_with_subtype
    assert not drifted_generators, (
        f"_HQ_SMOOTHING_ELIGIBLE_GENERATORS contains "
        f"{[g.__name__ for g in drifted_generators]!r} that has no "
        f"corresponding subtype string in _HQ_SMOOTHING_ELIGIBLE_SUBTYPES. "
        f"The UI gate would never enable HQ for those generators."
    )


def test_set_hq_smoothing_eligible_blocks_signals_around_setchecked() -> None:
    """Regression guard for the M1 double-render bug
    (adversary rect, enriques-hq-smoothing-2026q3-e1):
    `set_hq_smoothing_eligible(False)` must `blockSignals(True)`
    around `setChecked(False)` so programmatic state resets do NOT
    fire `hq_smoothing_changed` → MainWindow → `_render_current` on
    the stale (pre-variety-switch) mesh.

    Without the signal-block, switching variety while HQ was enabled
    triggered a redundant ~449 ms render of the OLD surface before
    the new variety's render even started.  The blockSignals pattern
    cleanly separates "programmatic clear" (silent) from "direct user
    interaction" (emits the signal).

    Source-text grep (AI-2 compliant — testing the signal-blocking
    behavior would require a live QApplication + connected slot).
    """
    import pathlib
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")

    # Find the set_hq_smoothing_eligible method body.
    method_idx = src.find("def set_hq_smoothing_eligible")
    assert method_idx > 0, (
        "appearance_panel.py is missing set_hq_smoothing_eligible method"
    )
    # Slice up to the next top-level `def ` (next method) or end-of-file.
    # The docstring + body together can exceed 2000 chars after the M1
    # rectification expanded the docstring; using next-def as the
    # boundary is robust to future docstring growth.
    after_def = src[method_idx + len("def set_hq_smoothing_eligible"):]
    next_def_offset = after_def.find("\n    def ")
    if next_def_offset > 0:
        method_body = src[method_idx:method_idx + len("def set_hq_smoothing_eligible") + next_def_offset]
    else:
        method_body = src[method_idx:]

    # The blockSignals(True)/blockSignals(False) pair MUST be present in
    # this method body — without it the signal chain fires on
    # programmatic setChecked(False) calls during variety/subtype switches.
    assert "blockSignals(True)" in method_body, (
        "set_hq_smoothing_eligible is missing blockSignals(True) — without "
        "it, programmatic setChecked(False) emits the toggled signal which "
        "fires hq_smoothing_changed → MainWindow → _render_current on the "
        "stale mesh.  Double-render regression from rect M1; see "
        "CONTEXT.md §4.3a for the architecture rationale."
    )
    assert "blockSignals(False)" in method_body, (
        "set_hq_smoothing_eligible has blockSignals(True) but no matching "
        "blockSignals(False) — signals would stay blocked forever after "
        "the first ineligible call, suppressing all subsequent legitimate "
        "user-driven toggle events."
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
    # hq-smoothing-label-rename-2026q3-e1 (F-L1 closure): label is
    # "Double-pass smooth" (not "HQ smoothing").
    hq_block_idx = src.find('QPushButton("Double-pass smooth")')
    assert hq_block_idx > 0, (
        "Double-pass smooth button not found in source — F-L1 regression: "
        "the user-visible label must be 'Double-pass smooth'."
    )
    # Check the next ~600 chars (the button construction block) for
    # setEnabled(False).
    hq_block = src[hq_block_idx:hq_block_idx + 600]
    assert "setEnabled(False)" in hq_block, (
        "Double-pass-smooth button is missing setEnabled(False) in its "
        "construction block — without it the toggle is enabled at launch "
        "before any Enriques subtype is selected, allowing the user to "
        "click it for K3 / CY3 / Fano (where the kwarg isn't accepted "
        "and would raise TypeError)."
    )


# ---------------------------------------------------------------------------
# hq-smoothing-label-rename-2026q3-e1 (F-L1 closure) regression guards
# ---------------------------------------------------------------------------


def test_appearance_panel_uses_double_pass_smooth_label() -> None:
    """The Display & Quality group's third button must read 'Double-pass
    smooth' (not 'HQ smoothing').  F-L1 closure: marketing-tone label
    replaced with a descriptive name that names the implementation
    (two Taubin passes total).  Group renamed Render Mode → Display &
    Quality by appearance-panel-render-mode-split-2026q3-e3.
    """
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")
    assert 'QPushButton("Double-pass smooth")' in src, (
        "appearance_panel.py is missing QPushButton('Double-pass smooth') — "
        "the relabeled opt-in toggle from hq-smoothing-label-rename-2026q3-e1."
    )


def test_appearance_panel_does_not_use_old_hq_smoothing_label() -> None:
    """Regression guard: the old user-visible label 'HQ smoothing' must
    NOT appear anywhere in appearance_panel.py as a QPushButton arg.
    Internal symbol names like `_hq_smoothing_cb` are unaffected — this
    test specifically guards the user-rendered label string.
    """
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")
    assert 'QPushButton("HQ smoothing")' not in src, (
        "appearance_panel.py still contains QPushButton('HQ smoothing') — "
        "regression: the F-L1 label rename to 'Double-pass smooth' did not "
        "apply.  Internal symbol names (_hq_smoothing_cb, etc.) are NOT "
        "tested here — only the user-visible button label string."
    )


def test_app_status_bar_uses_double_pass_suffix() -> None:
    """The status-bar attribution suffix must read '[Double-pass]' (not
    '[HQ]') when the toggle is active.  Threaded through both the
    'Computing…' message and the success-message in _on_mesh_ready
    via the `_hq_label` variable (variable name retained per F-L1 brief).
    """
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "app.py"
    ).read_text(encoding="utf-8")
    assert '" [Double-pass]"' in src, (
        "app.py is missing the ' [Double-pass]' status-bar suffix string — "
        "hq-smoothing-label-rename-2026q3-e1 must update _hq_label."
    )


def test_app_status_bar_does_not_use_old_hq_suffix() -> None:
    """Regression guard: the old status-bar suffix literal ' [HQ]' must
    NOT appear in app.py.  The variable name `_hq_label` is exempt
    (internal symbol); only the user-rendered string literal is tested.
    """
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "app.py"
    ).read_text(encoding="utf-8")
    assert '" [HQ]"' not in src, (
        "app.py still contains the ' [HQ]' status-bar string literal — "
        "regression: the F-L1 suffix rename to ' [Double-pass]' did not "
        "apply.  Variable name `_hq_label` is exempt; only string literals "
        "guarded here."
    )


def test_double_pass_smooth_tooltip_uses_imperative_verb() -> None:
    """Regression guard for hq-smoothing-label-rename-2026q3-e1 rect MEDIUM-1.

    The Double-pass-smooth tooltip must open with the imperative verb
    ``Apply`` (not the third-person-singular ``Applies``).  Qt and Apple
    HIG both specify imperative-or-noun-phrase form for tooltips, and
    every other tooltip in ``appearance_panel.py`` already follows the
    imperative pattern.
    """
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")
    # The tooltip first phrase must use the imperative "Apply".
    assert '"Apply a second Taubin smoothing pass' in src, (
        "appearance_panel.py is missing the imperative tooltip phrase "
        '\'"Apply a second Taubin smoothing pass\' — rect MEDIUM-1 regression: '
        "the Qt / Apple HIG convention requires imperative verbs in tooltips."
    )
    # And must NOT use the third-person-singular "Applies".
    assert '"Applies a second Taubin smoothing pass' not in src, (
        "appearance_panel.py contains the third-person-singular tooltip "
        'phrase \'"Applies a second Taubin smoothing pass\' — rect MEDIUM-1 '
        "regression: revert to the imperative \"Apply\" form."
    )
