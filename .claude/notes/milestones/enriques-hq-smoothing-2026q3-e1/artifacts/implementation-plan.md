# Implementation plan — enriques-hq-smoothing-2026q3-e1

**Inline path. ~145 LOC across 5 files.** Expose the deferred second Taubin pass (n_iter=40, pass_band=0.05) as an opt-in "HQ smoothing" QPushButton(checkable=True) in the Appearance panel's Display group. Pattern-A storage, per-subtype gating, default OFF so the 449ms baseline is preserved. Only fires for Enriques figs 1+2 (double-curve topology).

1. **surfaces.py** — Add `second_smooth_iter: int = 0` to `_marching_cubes_to_polydata` signature; after the existing first `smooth_taubin` call at line 134, add `if second_smooth_iter > 0 and mesh.n_points > 0: mesh = mesh.smooth_taubin(n_iter=second_smooth_iter, pass_band=0.05)` (the second pass STACKS per AI-6; does NOT replace). Add `hq_smoothing: bool = False` kwarg to `enriques_figure_1` and `enriques_figure_2`; each passes `second_smooth_iter=40 if hq_smoothing else 0` to the helper. Figs 3+4 unchanged (A₁ node topology, no double-curve benefit). ~12 LOC.

2. **appearance_panel.py** — Add `self._hq_smoothing: bool = False` in `__init__`. Add a new `QPushButton("HQ smoothing")` to `_build_toggles_group` with `setCheckable(True)`, `setChecked(False)`, `setEnabled(False)` (disabled at launch — enabled per-subtype by MainWindow), `setProperty("role", "display-toggle")` (picks up the existing checkable-button QSS), tooltip explaining +138ms cost and per-figure scope. New `hq_smoothing_changed = Signal(bool)` declared on the class. Slot `_on_hq_toggled(checked)` stores state AND emits the signal (does NOT call render — see §3 below). Public API: `hq_smoothing` property (read), `set_hq_smoothing_eligible(eligible: bool)` method (called by MainWindow on variety/subtype change — disables and resets the toggle when not eligible). The icon-refresh path (`refresh_icons`) is extended to set an icon on the new button. ~40 LOC.

3. **app.py** — Connect `appearance_panel.hq_smoothing_changed` to a new `_on_hq_smoothing_changed(enabled)` handler in `MainWindow.__init__`. The handler calls `self._invalidate_clipped_mesh()` then `self._render_current(reset_camera=False)` — critical: HQ smoothing changes the MESH (re-generates), unlike Wireframe/Show-edges which only change actor properties (so the apply_to_actor + render() fast path is wrong here). In `_on_variety_changed` add `self.appearance_panel.set_hq_smoothing_eligible(False)` (clear on variety switch). In `_on_subtype_changed` define `HQ_ELIGIBLE_SUBTYPES = {"Canonical sextic  [Fig. 1]", "Diagonal λ-family  [Fig. 2]"}` and call `set_hq_smoothing_eligible(variety == "Enriques surface" and name in HQ_ELIGIBLE_SUBTYPES)`. In `_render_current` after `params = self.parameters_panel.values()`, build `extra_kwargs = {"hq_smoothing": True} if (surface.generate in HQ_ELIGIBLE_GENERATORS and self.appearance_panel.hq_smoothing) else {}` and call `surface.generate(**params, **extra_kwargs)`. Import the two Enriques generator functions to populate `HQ_ELIGIBLE_GENERATORS`. ~50 LOC.

4. **tests/test_enriques_hq_smoothing.py** — New AI-2-compliant test file:
   - `test_enriques_fig1_hq_default_is_false` / `test_enriques_fig2_hq_default_is_false` — `inspect.signature` checks
   - `test_marching_cubes_second_smooth_iter_default_is_zero` — preserves all non-Enriques generator behavior
   - `test_enriques_fig3_has_no_hq_kwarg` / `test_enriques_fig4_has_no_hq_kwarg` — scope enforcement
   - `test_enriques_fig1_hq_on_returns_valid_mesh` / `test_enriques_fig2_hq_on_returns_valid_mesh` — smoke
   - `test_enriques_fig1_hq_on_has_lower_normal_variance` — **quantitative quality guard**: the whole point of the second pass is to reduce normal variance at the double-curve ridges; this test verifies the pass actually does something
   - `test_enriques_hq_button_is_checkable_qpushbutton_in_appearance_panel` — source-text grep guard (AI-2 compliant) verifying the new toggle uses the established `QPushButton(checkable=True)` pattern (not QCheckBox — would re-introduce the F-M2 triple-prefix bug from display-toggles-checkable-button)
   - Skip the timing-overhead test the researcher proposed — it would be flaky on slow CI and adds little value over the spike script that already lives at `.claude/scripts/enriques-taubin-spike.py`
   ~70 LOC.

5. **CONTEXT.md** — Two updates:
   - §8.16 append: "Deferral closed by enriques-hq-smoothing-2026q3-e1" paragraph documenting the opt-in toggle, the per-subtype gating, and the mesh-vs-actor distinction (why this milestone needs `_invalidate_clipped_mesh()` + `_render_current()` instead of the Wireframe/Show-edges `apply_to_actor() + render()` fast path).
   - §4 (after the `apply_to_actor` discussion): new paragraph documenting the HQ-smoothing wire-up architecture so a future maintainer reading appearance_panel.py finds the integration story.
   ~15 LOC.

6. **Verify** —
   - `pytest tests/ -q` reaches 338 + 8 = 346.
   - Off-screen render verification: render Enriques canonical sextic at default `c=1.0` with HQ off vs HQ on to `/tmp/check-enriques-hq-{off,on}.png` and visually confirm the double-curve sawtooth attenuation.
   - `.claude/scripts/enriques-taubin-spike.py` continues to run (the timing harness is independent of the new toggle and remains useful for re-measurement).

7. **Commit** — `feat(enriques-hq-smoothing-2026q3-e1): expose second Taubin pass as opt-in HQ toggle for Enriques figs 1+2`.
