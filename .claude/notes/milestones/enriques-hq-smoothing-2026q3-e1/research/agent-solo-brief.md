# Research Brief — enriques-hq-smoothing-2026q3-e1
**Agent:** solo researcher (Sonnet)
**Date:** 2026-05-22
**Status:** COMPLETE — architecture decision resolved in favour of Option (b) AppearancePanel toggle; full wire-up sketched

---

## 1. TL;DR

Add a `set_hq_smoothing(enabled: bool)` method to `AppearancePanel` (Pattern-A, matching `set_culling`); store `_hq_smoothing: bool = False` there; MainWindow reads it via `appearance_panel.hq_smoothing` at the top of `_render_current` and passes `hq_smoothing=True` to `enriques_figure_1` / `enriques_figure_2` generators when active. The toggle is a `QPushButton(checkable=True)` in `_build_toggles_group`, disabled (not hidden) unless the active subtype is Fig. 1 or Fig. 2. Main risk: the toggle must trigger `_invalidate_clipped_mesh()` + `_render_current()` rather than the appearance-only `actor.prop.*` + `render()` fast path, because HQ smoothing changes the mesh, not just its display — this is a departure from how Wireframe/Show-edges work. Backup plan: if the AppearancePanel toggle's re-render wiring proves messy, fall back to Option (a) bool ParamSpec by adding a `BoolParamSpec` subclass to ParametersPanel (higher surface, but self-contained).

---

## 2. Prior Art in This Repo

- `surfaces.py:87–141` — `_marching_cubes_to_polydata(field, bounds, level=0.0, smooth_iter=20)`. Single Taubin pass at line 134: `mesh.smooth_taubin(n_iter=smooth_iter, pass_band=0.1)`. Does NOT have a `second_smooth_iter` parameter yet. Extension point: add `second_smooth_iter: int = 0`; after line 134 add `if second_smooth_iter > 0 and mesh.n_points > 0: mesh = mesh.smooth_taubin(n_iter=second_smooth_iter, pass_band=0.05)`. Zero default preserves all existing surfaces unchanged.
- `surfaces.py:360–387` — `enriques_figure_1(c, n, bounds=1.89)`. Last line `return _marching_cubes_to_polydata(F, bounds)`. Generator API change: add `hq_smoothing: bool = False` kwarg and pass `second_smooth_iter=40 if hq_smoothing else 0` to the helper.
- `surfaces.py:396–430` — `enriques_figure_2(lam0, lam3, c, n, bounds=1.89)`. Same treatment.
- `surfaces.py:443–519` — `enriques_figure_3` and `enriques_figure_4`. Do NOT add `hq_smoothing` — per CONTEXT.md §8.13 these have A₁ nodes, not double curves. The +138ms overhead is not justified.
- `surfaces.py:988–1010` — `VARIETIES` registry: figs 1+2 are registered as `Surface("...", enriques_figure_1, ENRIQUES_FIGURE_1_PARAMS)`. Adding `hq_smoothing` as a generator kwarg does NOT require a `ParamSpec` — it is passed outside the `parameters_panel.values()` dict (see wire-up below).
- `appearance_panel.py:91–96` — `self._culling: str | None = None` — Pattern-A precedent. Field stored on panel; MainWindow sets it via `set_culling(value)` on variety change. `apply_to_actor` reads it. HQ smoothing follows the SAME storage discipline.
- `appearance_panel.py:161–203` — `_build_toggles_group()`. Currently builds `_wireframe_cb` and `_edges_cb` as `QPushButton(checkable=True)` with `setProperty("role", "display-toggle")`. Both call `self._get_plotter().render()` in their slot handlers — ONLY an actor property change, NOT a mesh regeneration. HQ smoothing toggle must differ: its slot handler must signal MainWindow to re-render, NOT call render() directly. See wire-up in §4.
- `appearance_panel.py:335–365` — `apply_to_actor(actor)`. Sets actor display properties from stored state. HQ smoothing is NOT an actor property — it is a generator kwarg. Therefore `apply_to_actor` does NOT need to change.
- `appearance_panel.py:395–433` — `set_culling(value)` method. This is the canonical Pattern-A setter. Follow this exact pattern for `set_hq_smoothing`.
- `app.py:276–377` — `_on_variety_changed`. Sets `appearance_panel.set_culling("back" if name == "Enriques surface" else None)`. The HQ smoothing gating is FINER than variety-level: it is per-subtype (figs 1+2 only). Gate must live in BOTH `_on_variety_changed` (disable when leaving Enriques) AND `_on_subtype_changed` (enable/disable per subtype).
- `app.py:379–414` — `_on_subtype_changed`. Calls `parameters_panel.set_specs(surface.params)` then `_render_current(reset_camera=True)`. This is where subtype-level enable/disable of the HQ toggle must live.
- `app.py:483–637` — `_render_current`. Line 524: `new_mesh = surface.generate(**params)` where `params = self.parameters_panel.values()`. The HQ smoothing kwarg is NOT in `params` (it is not a ParamSpec). It must be injected here as an extra kwarg: `extra = {"hq_smoothing": self.appearance_panel.hq_smoothing} if self._is_hq_eligible() else {}` then `surface.generate(**params, **extra)`.
- `app.py:638–648` — `_invalidate_clipped_mesh()`. Sets `self._clipped_mesh = None` and `self._clipped_overlay = None`. Must be called when HQ toggle fires, before re-render.
- `app.py:460–469` — `_on_domain_changed`. Pattern: `_invalidate_clipped_mesh()` + `_apply_domain_and_render(reset_camera=False)`. The HQ toggle handler follows a similar pattern but must call `_render_current(reset_camera=False)` (not `_apply_domain_and_render`) because HQ toggles CHANGES THE MESH, not just the clip domain.
- `tests/test_mesh_generators.py:65–130` — Existing Enriques smoke tests + the bounds-padding regression guard. New tests go in `tests/test_enriques_hq_smoothing.py` (separate file; matches existing per-topic test file convention).

---

## 3. External Sources Reviewed

| Source | URL | Key Finding | Relevance |
|---|---|---|---|
| PyVista `smooth_taubin` docs | confirmed from prior milestone spike | `inplace=False` default — each call returns new PolyData. Stacking: `mesh = mesh.smooth_taubin(40, 0.05)` after first pass is correct. | Confirms the second-pass implementation in `_marching_cubes_to_polydata`. |
| CONTEXT.md §8.13 | local read | Figs. 1+2 have double curves (Taubin beneficial); figs 3+4 have A₁ nodes (Taubin not targeted). | Defines the per-subtype scope: HQ enable only for figs 1+2. |
| CONTEXT.md §8.16 | local read | Path B shipped (bounds only); second pass deferred. Measured overhead +138ms (+30.8%), 587.5ms total vs 500ms budget. Baseline single-pass = 449ms. | Confirms the opt-in design is the correct home; confirms the 500ms single-render budget is the timing reference. |
| Predecessor spike brief (`enriques-taubin-spike-2026q2-e1/research/agent-solo-brief.md`) | local read | `second_smooth_iter: int = 0` is the established kwarg name for `_marching_cubes_to_polydata`; the implementation sketch there is accurate and can be used as-is. | Saves re-derivation; confirm line-level attach points are still valid (confirmed: `surfaces.py:87–141` unchanged since spike). |
| AI-8 invariant (app-invariants.md:85–106) | local read | ParamSpec is the established extension point for generator tuning; bool/int bimodal is explicitly NOT recommended. However, the invariant says "don't make ParamSpec int/float-bimodal — coerce ints inside the generator". A bool opt-in is bimodal. | Option (a) bool ParamSpec is AI-8 non-compliant for a bool toggle; it would require either a `BoolParamSpec` subclass or a 0/1 float coerced to bool. Both are higher-surface solutions. |
| enriques-backface-2026q2-e1 Pattern-A precedent | CONTEXT.md §8.13 + app.py:306–331 | `set_culling` lives on AppearancePanel; MainWindow gates it per-variety in `_on_variety_changed`. `apply_to_actor` reads it. | Direct precedent for Option (b). However, culling changes an ACTOR PROPERTY (no re-render needed beyond `plotter.render()`); HQ smoothing changes the MESH GENERATION — the pattern diverges here. |

---

## 4. Recommended Approach

### Decision: Option (b) — AppearancePanel toggle, Pattern-A storage

**Recommended option: (b).** A third `QPushButton(checkable=True)` in `_build_toggles_group`, following the Wireframe and Show-edges pattern. State stored as `self._hq_smoothing: bool = False` on AppearancePanel. Public getter `@property hq_smoothing -> bool` (or a simple attribute read). Public setter `set_hq_smoothing(enabled: bool)` called from MainWindow per-subtype gate.

**Why not (a) bool ParamSpec:** AI-8 explicitly says "don't make ParamSpec int/float-bimodal". A bool toggle in the Parameters panel would require either (1) a new `BoolParamSpec` dataclass subclass — non-trivial, touching `parameters_panel.py` widget construction, `values()` marshaling, and `ParamSpec` itself — or (2) a 0.0/1.0 float coerced to bool inside the generator. Option (1) is ~100+ LOC of new ParametersPanel surface. Option (2) is semantically misleading in the slider UI (showing a 0-1 float slider for a boolean makes no sense to the user). Both are higher-cost than Option (b).

**Why not (c) menu entry:** Worst discoverability; the user cannot see the current state without opening a menu. A panel toggle is always visible.

**Why Option (b) over (a) despite the "conceptual misfit" concern:** The user brief correctly notes that HQ smoothing changes mesh generation, not display. However, this is also true of `set_culling` in a weaker sense — culling changes the actor's rendering mode based on surface topology. The AppearancePanel already carries topology-aware state (`_culling`). Extending it with `_hq_smoothing` is consistent with existing architecture, not a violation. The key difference from Wireframe/Show-edges is that the toggle handler cannot use the `actor.prop.*` + `plotter.render()` fast path — it must signal a full `_render_current` re-render. This is a one-line difference in the slot handler (emit a signal vs. call `plotter.render()`).

**Cost of Option (b):**
- `appearance_panel.py`: ~25 LOC (field init + button construction + slot handler + `set_hq_smoothing` method + `hq_smoothing` property)
- `app.py`: ~30 LOC (connect toggle signal to new `_on_hq_smoothing_toggled` slot; enable/disable toggle in `_on_variety_changed` + `_on_subtype_changed`; inject `hq_smoothing` kwarg in `_render_current`)
- `surfaces.py`: ~10 LOC (`second_smooth_iter` kwarg on `_marching_cubes_to_polydata`; `hq_smoothing` kwarg on figs 1+2)
- `tests/test_enriques_hq_smoothing.py`: ~60 LOC
- `CONTEXT.md`: ~20 LOC

Total: ~145 LOC. No new Qt surface except the third button in an existing `QGroupBox`.

### Wire-up sketch (end-to-end pseudocode)

**State storage (`appearance_panel.py`):**
```
__init__:
    self._hq_smoothing: bool = False

_build_toggles_group():
    self._hq_cb = QPushButton("HQ smoothing")
    self._hq_cb.setCheckable(True)
    self._hq_cb.setChecked(False)
    self._hq_cb.setEnabled(False)   # disabled at launch; enabled only for figs 1+2
    self._hq_cb.setToolTip(
        "Apply a second Taubin smoothing pass (n=40, pb=0.05) to reduce the "
        "double-curve sawtooth artifact. Adds ~138ms to generation time. "
        "Only active for Enriques Figs. 1 and 2 (double-curve topology)."
    )
    self._hq_cb.setProperty("role", "display-toggle")
    self._hq_cb.toggled.connect(self._on_hq_toggled)
    vl.addWidget(self._hq_cb)

_on_hq_toggled(self, checked: bool):
    self._hq_smoothing = checked
    # Does NOT call plotter.render() — mesh regeneration is required.
    # MainWindow must handle this via signal.
    # Emit a new signal or use the existing connected-slot pattern.

set_hq_smoothing(self, enabled: bool):
    """Called by MainWindow to enable/disable the toggle per subtype."""
    self._hq_cb.setEnabled(enabled)
    if not enabled:
        self._hq_cb.setChecked(False)  # reset state when disabled
        self._hq_smoothing = False

@property
def hq_smoothing(self) -> bool:
    return self._hq_smoothing
```

**MainWindow wiring (`app.py`):**

Add a `hq_smoothing_changed` signal on AppearancePanel, OR connect `_hq_cb.toggled` to a MainWindow slot directly. The cleanest approach: AppearancePanel emits `hq_smoothing_changed = Signal(bool)` (new signal); MainWindow connects it to `_on_hq_smoothing_changed`.

```
# In MainWindow.__init__ (after appearance_panel construction):
self.appearance_panel.hq_smoothing_changed.connect(self._on_hq_smoothing_changed)

def _on_hq_smoothing_changed(self, enabled: bool) -> None:
    if self._raw_mesh is None:
        return
    self._invalidate_clipped_mesh()
    self._render_current(reset_camera=False)

# In _on_variety_changed (after existing set_culling call):
is_enriques = (name == "Enriques surface")
self.appearance_panel.set_hq_smoothing(False)  # always clear on variety switch

# In _on_subtype_changed:
HQ_ELIGIBLE_SUBTYPES = {"Canonical sextic  [Fig. 1]", "Diagonal λ-family  [Fig. 2]"}
eligible = (variety == "Enriques surface") and (name in HQ_ELIGIBLE_SUBTYPES)
self.appearance_panel.set_hq_smoothing_eligible(eligible)
# (rename set_hq_smoothing -> set_hq_smoothing_eligible for clarity, or keep
# set_hq_smoothing as the "enable/disable toggle" method)
```

**Generator injection (`_render_current`, `app.py:524`):**
```python
# After: params = self.parameters_panel.values() if surface.params else {}
HQ_ELIGIBLE_GENERATORS = {enriques_figure_1, enriques_figure_2}
extra_kwargs = {}
if surface.generate in HQ_ELIGIBLE_GENERATORS and self.appearance_panel.hq_smoothing:
    extra_kwargs["hq_smoothing"] = True
new_mesh = surface.generate(**params, **extra_kwargs)
```

**Generator API change (`surfaces.py`):**

Prefer `hq_smoothing: bool = False` kwarg on `enriques_figure_1` / `enriques_figure_2` over exposing `second_smooth_iter` directly to callers. The `_marching_cubes_to_polydata` helper gets `second_smooth_iter: int = 0` (internal plumbing); the generator kwarg is the public API surface. This keeps the helper's int-parameter internal and the generator's bool-parameter user-facing.

```python
def enriques_figure_1(c=1.0, n=240, bounds=1.89, hq_smoothing: bool = False):
    ...
    return _marching_cubes_to_polydata(F, bounds, second_smooth_iter=40 if hq_smoothing else 0)
```

### Default-OFF preservation

Default `hq_smoothing=False` on both generators. `_marching_cubes_to_polydata` default `second_smooth_iter=0` short-circuits the second-pass block immediately. `appearance_panel._hq_smoothing` initializes to `False` and the button initializes `setChecked(False)`. In `_render_current`, `extra_kwargs` is empty when `hq_smoothing == False`. The code path when HQ is off is IDENTICAL to the pre-milestone code. The 449ms baseline is preserved by construction.

### Per-figure scope

HQ smoothing fires ONLY for Enriques variety + Fig. 1 or Fig. 2 subtypes. In `_on_variety_changed`, `set_hq_smoothing(False)` clears and disables the toggle for ALL other varieties. In `_on_subtype_changed`, the toggle is enabled only when `name in {"Canonical sextic  [Fig. 1]", "Diagonal λ-family  [Fig. 2]"}` AND variety is `"Enriques surface"`. If the user has HQ enabled and switches to Fig. 3 or Fig. 4, `set_hq_smoothing(False)` clears the state AND resets `_hq_smoothing = False` AND unchecks the button. The next render receives `hq_smoothing=False` — no second pass fires.

### Granularity: boolean on/off (not a slider for n_iter)

The spike pre-committed to `n_iter=40, pass_band=0.05` as the fixed second-pass parameters. Exposing `n_iter` as a slider would require a `BoolParamSpec` or `IntParamSpec` subclass in ParametersPanel — out of scope. Boolean on/off is the correct granularity. The implementer should hardcode `second_smooth_iter=40` in the generator.

---

## 5. Alternatives Considered

- **Option (a) bool ParamSpec on figs 1+2:** Requires `BoolParamSpec` subclass touching `parameters_panel.py` widget construction + `values()` marshaling + dataclass extension — ~100+ LOC of new ParametersPanel surface vs ~25 LOC in AppearancePanel. Rejected: higher surface, AI-8 bimodal concern.
- **Option (c) Tools/Settings menu:** Worst discoverability; no visible toggle state at a glance. Rejected: user-experience failure for a power-user feature that should be visible when available.
- **Global "extra smoothing" lever for all implicit surfaces:** The brief correctly restricts this to figs 1+2. Applying the second Taubin pass to K3 / Kummer / CY3 Dwork / Fano would add +138ms to surfaces that don't benefit (no double-curve target). Rejected: unnecessary latency, no targeted benefit.
- **`n_iter` slider for second-pass iterations:** Would require `IntParamSpec` or float-coerced slider in ParametersPanel. The spike pre-committed to `n_iter=40` as the correct value. Rejected: unnecessary complexity, out of scope.
- **Toggling via the global theme/dark-mode button pattern:** The theme toggle calls `_on_theme_changed` which calls `_apply_system_theme`. Piggybacking on the theme architecture for a render-quality toggle would be deeply wrong. Rejected.
- **Storing state on MainWindow rather than AppearancePanel:** Would work, but breaks the established Pattern-A discipline where per-variety rendering state lives on AppearancePanel (see `_culling`). Rejected: architectural inconsistency.

---

## 6. Risks and Unknowns

### AI-conflict matrix

| Invariant | Status | Notes |
|---|---|---|
| **AI-1** (PySide6 stack) | CLEAN | No renderer change. One new `QPushButton` in an existing panel. |
| **AI-2** (Qt-free tests) | CLEAN WITH CONSTRAINT | All new tests in `test_enriques_hq_smoothing.py` must be pure PyVista/NumPy. The toggle widget itself cannot be tested under AI-2 — use source-grep pattern (assert `setCheckable(True)` appears in appearance_panel.py). The generator kwarg tests are Qt-free. |
| **AI-6** (Taubin STACKS, not replaces) | CRITICAL — read carefully | The second Taubin pass must be ADDED AFTER the existing first pass in `_marching_cubes_to_polydata`. The existing `mesh.smooth_taubin(n_iter=smooth_iter, pass_band=0.1)` at line 134 MUST remain unchanged. The new block runs AFTER it. Do NOT replace the first pass with the second pass, and do NOT skip the first pass when `hq_smoothing=True`. Both passes run in sequence. |
| **AI-7** (Hanson normals) | CLEAN | Hanson surfaces never call `_marching_cubes_to_polydata`. The `second_smooth_iter=0` default means zero change for all non-Enriques implicit generators. |
| **AI-8** (Surface/ParamSpec frozen) | CLEAN | No ParamSpec added. No Surface dataclass field added. `hq_smoothing` is a generator kwarg, not a ParamSpec. The VARIETIES registry does not change. |
| **AI-9** (re-entrancy) | CLEAN WITH CONSTRAINT | The HQ toggle slot handler MUST NOT call `processEvents()`. It must ONLY update `_hq_smoothing` and emit a signal (or call a MainWindow slot via Signal). The actual re-render happens in `_render_current` which is already guarded by `_computing`. |
| **AI-10** (raw mesh cache) | REQUIRES CACHE INVALIDATION | Toggling HQ smoothing changes the raw mesh (the generator produces a different PolyData). `self._clipped_mesh` MUST be set to `None` before re-rendering. The `_on_hq_smoothing_changed` slot in MainWindow must call `self._invalidate_clipped_mesh()` before `self._render_current(reset_camera=False)`. Failure to invalidate would cause the domain clip to apply to the pre-toggle mesh — silent correctness bug. |
| **AI-11** (fully-qualified Qt enums) | CLEAN | New code uses `Qt.Orientation.Horizontal`, etc. No shorthand. |
| **AI-12** (WCAG contrast) | NEEDS TOOLTIP TEXT CHECK | The HQ button tooltip text (white on dark panel) is informational — no new color tokens needed; the existing `TEXT_VALUE` cascade applies. |
| **AI-13** (6-digit hex) | N/A | No new color literals. |
| **AI-14** (generator contract) | CLEAN | `enriques_figure_1(hq_smoothing=True)` still returns `pv.PolyData` or raises `ValueError`. The new kwarg does not change the output type or error contract. Default `hq_smoothing=False` means all existing call sites are unaffected. |
| **AI-15** (math honesty) | N/A | No new variety. HQ smoothing is a rendering-quality improvement. The existing tooltip for Fig. 1 ("real shadows of degree-6 surfaces in P^3 birational to Enriques surfaces") does not need updating. |

### Re-render triggering (the key design risk)

The critical difference between HQ smoothing and Wireframe/Show-edges: the latter change ACTOR PROPERTIES (no mesh regeneration; `actor.prop.*` + `plotter.render()` is sufficient). HQ smoothing changes the MESH (requires a full `surface.generate()` call). The slot handler `_on_hq_toggled` in `AppearancePanel` must NOT call `plotter.render()` directly. It must signal MainWindow, which calls `_render_current`. The safest mechanism: define `hq_smoothing_changed = Signal(bool)` on AppearancePanel, connect in MainWindow.

**Consequence for `apply_to_actor`:** the `apply_to_actor` method does NOT need to change. HQ smoothing is handled entirely at the generate step, not the actor-property step.

### Signal connection ordering

`AppearancePanel.hq_smoothing_changed` must be connected in `MainWindow.__init__` AFTER the `appearance_panel` widget is constructed (line ~191) and BEFORE the initial render. The connection point should be near the existing `appearance_panel.set_culling` call site.

### QSettings is out of scope

CONTEXT.md §9 explicit non-goal. The HQ toggle resets to `False` on each app launch. No persistence.

### Toggle icon (optional)

The existing Wireframe + Show-edges buttons have icons from qtawesome-icons-2026q2-e2. A HQ smoothing button icon would follow the same `refresh_icons(theme)` pattern. Candidate: `mdi6.auto-fix` (sparkle/magic-wand shape). However, icon is OPTIONAL for this milestone — the text label "HQ smoothing" is sufficient. If an icon is desired, it must be added to `refresh_icons` in AppearancePanel and the call sites in MainWindow. Do not add the icon as part of `_build_ui()` (qtawesome footgun per CONTEXT.md §8.12).

### Test: normal-variance comparison (quantitative quality guard)

The brief requires `test_hq_on_mesh_has_lower_vertex_normal_variance_than_hq_off`. This is possible because `enriques_figure_1` accepts `hq_smoothing=False` (default) and `hq_smoothing=True`. The test can call both and compare `np.var(mesh.point_normals, axis=0).sum()`. The Taubin second pass should provably reduce this variance. If it doesn't (edge case at extreme c values), the test may be brittle — use `c=1.0` (default) as the test case, which is the same parameter value the spike validated.

### Timing regression guard

The brief requests a `<250ms` overhead test. This is problematic under AI-2: a wall-clock timing test in the pytest suite is environment-dependent and will be flaky on slow CI. Recommend: state in the test file's docstring that the spike measured +138ms on the dev machine, and the 250ms guard is a soft ceiling. The test should use `time.perf_counter` around `enriques_figure_1(hq_smoothing=True)` vs `enriques_figure_1(hq_smoothing=False)`, assert `overhead_ms < 250`, but mark the test with `@pytest.mark.slow` if a slowmarker convention exists in the repo (check `pytest.ini`). If no slow marker exists, consider skipping the timing guard or making it a manual check.

---

## 7. AI-15 Disclaimers

Not applicable. This milestone proposes no new variety or figure. The second Taubin pass improves the rendering quality of the existing Enriques figs 1+2 whose tooltips already carry accurate "birational to Enriques surfaces" disclaimers. No tooltip text needs updating for the math claim.

The HQ smoothing button tooltip text should be technically accurate: "Apply a second Taubin smoothing pass (n_iter=40, pass_band=0.05) to reduce the double-curve sawtooth-ridge artifact on figs 1 and 2. Adds ~140ms to generation time. Only active for double-curve figures."

---

## 8. CONTEXT.md Updates Required

### §8.16 update (close the deferral)

Append to the existing §8.16 entry (CONTEXT.md:450–476):

```
**Deferral closed by enriques-hq-smoothing-2026q3-e1.** The second Taubin pass
(n_iter=40, pass_band=0.05) is now exposed as an opt-in "HQ smoothing" toggle
in the Appearance panel. The toggle is disabled (greyed out) for Enriques figs
3+4 and for all other variety families. When enabled, `enriques_figure_1` /
`enriques_figure_2` pass `second_smooth_iter=40` to `_marching_cubes_to_polydata`,
adding the second Taubin pass on top of the existing first pass (AI-6: STACKS,
does not replace). Default is OFF; the 449ms baseline is unchanged. Toggling
triggers `MainWindow._invalidate_clipped_mesh()` + `_render_current()` because
HQ smoothing changes the mesh, not just actor display properties (see §4.3 for
the apply_to_actor vs. re-render discipline).
```

### New §4 paragraph (architecture conventions)

Add after the `apply_to_actor` description in §4 (CONTEXT.md:143):

```
**HQ-smoothing opt-in architecture (enriques-hq-smoothing-2026q3-e1).** The
AppearancePanel stores `_hq_smoothing: bool = False` and exposes it via
`hq_smoothing` property and `set_hq_smoothing(enabled: bool)` method (Pattern-A,
same discipline as `set_culling`). A `hq_smoothing_changed = Signal(bool)` emitted
from AppearancePanel's toggle slot drives a `MainWindow._on_hq_smoothing_changed`
handler that calls `_invalidate_clipped_mesh()` + `_render_current(reset_camera=False)`.
The `_render_current` method reads `appearance_panel.hq_smoothing` and injects
`hq_smoothing=True` into `surface.generate(**params, **extra_kwargs)` ONLY when
the active generator is `enriques_figure_1` or `enriques_figure_2`. The toggle
button in the Display group is `setEnabled(False)` by default and enabled per-subtype
from `_on_subtype_changed`; it resets to `False` on every variety or subtype switch.
```

---

## 9. Test Plan (concrete, AI-2 compliant)

All tests in `tests/test_enriques_hq_smoothing.py`. No `QApplication`. Pure `pyvista` / `numpy`.

**Test 1 — default is False:**
```python
def test_enriques_fig1_hq_default_is_false():
    import inspect
    from surfaces import enriques_figure_1
    sig = inspect.signature(enriques_figure_1)
    assert sig.parameters["hq_smoothing"].default is False

def test_enriques_fig2_hq_default_is_false():
    import inspect
    from surfaces import enriques_figure_2
    sig = inspect.signature(enriques_figure_2)
    assert sig.parameters["hq_smoothing"].default is False
```

**Test 2 — HQ=True returns valid PolyData:**
```python
def test_enriques_fig1_hq_on_returns_valid_mesh():
    from surfaces import enriques_figure_1
    mesh = enriques_figure_1(hq_smoothing=True)
    assert mesh.n_points > 0
    assert mesh.n_faces > 0

def test_enriques_fig2_hq_on_returns_valid_mesh():
    from surfaces import enriques_figure_2
    mesh = enriques_figure_2(hq_smoothing=True)
    assert mesh.n_points > 0
    assert mesh.n_faces > 0
```

**Test 3 — HQ=True mesh has lower normal variance than HQ=False (quantitative quality guard):**
```python
def test_enriques_fig1_hq_on_has_lower_normal_variance():
    import numpy as np
    from surfaces import enriques_figure_1
    mesh_off = enriques_figure_1(c=1.0, hq_smoothing=False)
    mesh_on  = enriques_figure_1(c=1.0, hq_smoothing=True)
    normals_off = mesh_off.point_normals  # (N, 3)
    normals_on  = mesh_on.point_normals
    # Second Taubin pass smooths normals — reduces per-point variance
    var_off = float(np.var(normals_off, axis=0).sum())
    var_on  = float(np.var(normals_on, axis=0).sum())
    assert var_on < var_off, (
        f"HQ-on normal variance {var_on:.6f} should be less than "
        f"HQ-off {var_off:.6f}"
    )
```

**Test 4 — HQ adds ≤250ms overhead (soft perf guard):**
```python
def test_enriques_fig1_hq_overhead_under_250ms():
    import time
    from surfaces import enriques_figure_1
    # warm-up
    enriques_figure_1(c=1.0)
    enriques_figure_1(c=1.0, hq_smoothing=True)
    t0 = time.perf_counter()
    enriques_figure_1(c=1.0)
    t_off = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    enriques_figure_1(c=1.0, hq_smoothing=True)
    t_on = (time.perf_counter() - t0) * 1000
    overhead = t_on - t_off
    assert overhead < 250, (
        f"HQ overhead {overhead:.1f}ms exceeds 250ms safety margin. "
        "Spike measured +138ms; investigate if significantly higher."
    )
```

**Test 5 — HQ toggle button is NOT a QCheckBox (AI-2 source-grep pattern):**
```python
def test_hq_smoothing_toggle_is_qpushbutton():
    source = open("appearance_panel.py").read()
    assert "QPushButton" in source  # QPushButton already present (Wireframe, Show-edges)
    # Guard: the HQ button must NOT be QCheckBox (display-toggles-checkable-button pattern)
    # Can grep for the specific label string near QPushButton
    assert 'QPushButton("HQ smoothing")' in source
```

**Test 6 — enriques_figure_3 and enriques_figure_4 do NOT accept hq_smoothing:**
```python
def test_enriques_fig3_has_no_hq_kwarg():
    import inspect
    from surfaces import enriques_figure_3
    sig = inspect.signature(enriques_figure_3)
    assert "hq_smoothing" not in sig.parameters

def test_enriques_fig4_has_no_hq_kwarg():
    import inspect
    from surfaces import enriques_figure_4
    sig = inspect.signature(enriques_figure_4)
    assert "hq_smoothing" not in sig.parameters
```

**Test 7 — second_smooth_iter default is 0 in _marching_cubes_to_polydata:**
```python
def test_marching_cubes_second_smooth_iter_default_is_zero():
    import inspect
    from surfaces import _marching_cubes_to_polydata
    sig = inspect.signature(_marching_cubes_to_polydata)
    assert sig.parameters["second_smooth_iter"].default == 0
```

---

## 10. Open Questions for the User

None. The brief is fully specified. All four architecture decisions are resolved:
1. Option (b) AppearancePanel toggle (Pattern-A).
2. Boolean on/off granularity (n_iter=40 hardcoded).
3. Scope: Enriques figs 1+2 only (toggle disabled for figs 3+4 and all other varieties).
4. Default OFF confirmed.
5. Session-only (no QSettings persistence).
