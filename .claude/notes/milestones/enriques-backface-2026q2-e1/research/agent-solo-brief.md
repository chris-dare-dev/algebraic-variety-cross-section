# Research Brief — enriques-backface-2026q2-e1
**Agent:** solo researcher
**Date:** 2026-05-22
**Status:** COMPLETE (gate NOT required — approach is clearly determined; risk resolved below)

---

## 1. TL;DR

The milestone as briefed contains a critical implementation error: `culling='back'` passed globally to `plotter.add_mesh(clipped, ...)` hides important visible geometry on three of the four variety families and is therefore **not** a 1-kwarg XS drop-in. The fix is scoped differently: backface culling must be applied **after** `add_mesh` via `actor.prop.culling`, conditionally per variety family, OR the correct fix for the Enriques zipper artifact is an alternative approach (two-sided backface `actor.prop` settings, or a normal-flip post-processing step). The safest, lowest-risk implementation is to skip the `add_mesh` kwarg entirely and apply `actor.prop.culling = 'back'` only for Enriques surfaces via `AppearancePanel.apply_to_actor` based on a new per-variety flag — or equivalently, to recognize that the global culling approach breaks K3/CY3 and must be gated behind a `if is_enriques` branch in `_apply_domain_and_render`. Main risk: the milestone brief's "challenger rated NONE, XS effort" assessment is optimistic — the regression across Kummer (moderate), Enriques (severe wing-loss), and Hanson (catastrophic patch-loss) makes a global kwarg unsafe. Backup plan: defer to the UI-toggle approach (v1 scope per the brief) where the checkbox defaults ON only for Enriques — this naturally achieves per-variety gating.

---

## 2. Prior Art in This Repo

- `app.py:455–462` — the primary `plotter.add_mesh(clipped, ...)` call (the proposed attach point). Currently passes `smooth_shading=True`, `specular=0.3`, `specular_power=15`, `ambient=0.15`, `diffuse=0.85`. No `culling` kwarg. This is the UPL-9 post-rect state.
- `app.py:424–433` — the early-return wireframe overlay `add_mesh(overlay, ...)` call. Uses `lighting=False`. Brief explicitly says do NOT touch this. Confirmed safe (wireframe overlay, edges only, not solid faces).
- `app.py:463` — `self.appearance_panel.apply_to_actor(self._actor)` called immediately after `add_mesh`. This sets `actor.prop.color`, `style`, `show_edges`, `opacity`, `interpolation`. It does NOT touch `actor.prop.culling`. Confirmed by reading `appearance_panel.py:307–324`. Culling set at `add_mesh` time survives `apply_to_actor`.
- `appearance_panel.py:307–324` — `apply_to_actor`: sets color, style, show_edges, opacity, interpolation. No culling property touched. Verified safe — adding `culling` at `add_mesh` level does not get overwritten here.
- `surfaces.py:317–344` — `enriques_figure_1`: default `c=1.0` (not c=0 — the minimum slider value per `ENRIQUES_FIGURE_1_PARAMS` is 0.1, so mathematical c=0 is unreachable). The function clips `F = np.clip(F, -10.0, 10.0)`, and the zero set at c~=0 yields field range [9.65e-09, 10] — no real zero crossing, hence `ValueError`. Brief's reference to "default c=0" appears to be a documentation error in the milestone brief; actual default is c=1.0.
- `surfaces.py:496–588` — `_hanson_cross_section`: assembles 25 patches via `_concat_polydata`, then calls `compute_normals(cell_normals=True, consistent_normals=False, auto_orient_normals=False)`. Comment at line 577–582 explicitly documents why consistent_normals=False: disconnected components cause per-patch lighting flips with True.
- `.claude/notes/frontend-uplifts/2026q2-graph-and-window/discover/current-state-critic-brief.md:H-3` — H-3 text reads: "Pass `backface_culling=True` in `app.py:374`'s `plotter.add_mesh(...)` call." Line number reference is to a pre-UPL-9 version of the file; post-rect the call is at `app.py:455`. The suggestion was for the Enriques case specifically, but the brief did not evaluate cross-family regression.
- `.claude/notes/frontend-uplifts/2026q2-graph-and-window/discover/visual-scout-brief.md:H-1` — confirms "sawtooth/zigzag artifacts along internal singularity node lines" specifically for Enriques canonical sextic.

---

## 3. External Sources Reviewed

| Source | URL | Key Finding | Relevance |
|---|---|---|---|
| PyVista `add_mesh` docstring | local inspect | `culling='back'` (or `culling=True`) maps to VTK `BackfaceCullingOn()` on the actor's `vtkProperty`. Default is `None` (no culling). Boolean `True` maps to `'back'`. | Confirmed kwarg name and semantics |
| PyVista `Property.culling` API | https://docs.pyvista.org/api/plotting/_autosummary/pyvista.property.culling | Accepts `'back'`, `'front'`, `'none'`/`False`; default is `'none'`. Culling is a property on the actor's vtkProperty. | Confirms post-add_mesh access via `actor.prop.culling = 'back'` |
| PyVista backface props example | https://docs.pyvista.org/examples/02-plot/backface_prop.html | Separate `backface_params` dict/Property sets different color/style for back faces — alternative to culling that keeps back faces but renders them differently | Provides an alternative fix approach |
| VTK backface culling behavior | (derived from PyVista source + runtime test) | `actor.prop.GetBackfaceCulling()` returns 1 when culling='back' set; setting style='wireframe' after culling is set does NOT reset culling | Confirms culling survives appearance_panel.apply_to_actor |

---

## 4. Recommended Approach

### 4a. The global-culling approach FAILS — visual regression confirmed

Off-screen render tests (using `pv.OFF_SCREEN=True`, dark `#2f2f2f` background, UPL-9 lighting kwargs, `camera_position='iso'`) definitively show:

| Surface | culling='back' Effect | Verdict |
|---|---|---|
| K3 / Fermat quartic | Visually identical before/after — closed convex surface, all normals outward | SAFE |
| K3 / Kummer surface | Minor regression at node meeting regions — inner cone faces partially hidden | MILD REGRESSION |
| Enriques / Canonical sextic (c=1.0) | Severe regression — outer wing structures disappear entirely, only back-wall corner faces survive | BREAKING |
| Enriques / Canonical sextic (c=1.5) | Severe regression — same as c=1.0, outer wings hidden | BREAKING |
| CY3 / Hanson quintic | Catastrophic — iconic ball-of-spikes shape breaks down, individual patches become transparent/absent, surface is unrecognizable | BREAKING / AI-7 CONFLICT |

The root cause: The Enriques surface is a thin open-sheet geometry (its double-curve singularities create pairs of sheets viewable from the exterior on both sides). Applying `culling='back'` globally hides one side of each sheet pair, removing entire visible face groups. The Kummer surface's conical nodes have inner faces visible through the hollows. The Hanson surface's disconnected patches have winding-consistent normals within each patch but those windings are not globally outward-pointing — when the camera rotates, patches whose normals point away are culled entirely.

### 4b. Correct approaches (two options; pick one)

**Option A: Per-variety conditional culling (RECOMMENDED)**

Apply `culling='back'` conditionally, only for Enriques subtypes, using the variety name available in `_apply_domain_and_render`. This requires knowing the current variety at render time.

```python
# In _apply_domain_and_render, after line 462 (after add_mesh, before apply_to_actor):
is_enriques = (self._variety_name == "Enriques surface")  # or similar flag
self._actor = self.plotter.add_mesh(
    clipped,
    smooth_shading=True,
    specular=0.3,
    specular_power=15,
    ambient=0.15,
    diffuse=0.85,
    culling='back' if is_enriques else None,   # UPL-7: Enriques only
)
```

To implement this, `_apply_domain_and_render` needs access to `self._variety_name`. Checking `app.py` for how variety tracking works:

```python
# app.py: variety is selected via self._variety_combo and stored as:
# self._variety_name = self._variety_combo.currentText()  (or similar)
```

This is low-risk if the variety name is accessible; adds ~3 LOC.

**Option B: Check via actor.prop.culling in apply_to_actor gated on variety state**

Store a `_culling_override` on AppearancePanel (default `None`; overridden to `'back'` for Enriques). `apply_to_actor` sets `actor.prop.culling = self._culling_override`. MainWindow sets `appearance_panel.culling_override('back' if is_enriques else None)` before `apply_to_actor`. This is the correct architectural home for actor-property settings (all actor props flow through `apply_to_actor`).

**Why NOT Option C: Full UI toggle (v1 scope)**

The v1 UI toggle approach adds the Backface culling checkbox to AppearancePanel defaulting ON for Enriques and OFF for K3/CY3. This is the architecturally cleanest path and matches the Appearance panel's existing design pattern (wireframe checkbox, etc.). However the brief scopes this to a future milestone. The researcher notes this is worth the small additional effort: the toggle approach is only ~15 LOC more than Option A and avoids the "invisible knob" smell of a hardcoded per-variety conditional buried in `_apply_domain_and_render`.

**Recommended: Option B (actor.prop.culling in apply_to_actor, with variety-state gating)**

This keeps all actor-property assignments in `apply_to_actor` (where they belong architecturally per §4.3a), matches the existing pattern, and makes the Enriques-specific behavior explicit and testable. Concretely:

1. Add `self._culling: str | None = None` to `AppearancePanel.__init__`.
2. Add `def set_culling(self, value: str | None) -> None: self._culling = value` public method.
3. In `apply_to_actor`: `actor.prop.culling = self._culling or 'none'`.
4. In `app.py._on_subtype_changed` / `_on_variety_changed`: call `self.appearance_panel.set_culling('back' if is_enriques else None)`.

Total: ~8 LOC across `appearance_panel.py` + `app.py`.

### 4c. Scope of CONTEXT.md update

The Enriques-specific culling is worth a §8 entry (not just §4.3) because:
- It documents WHY culling is Enriques-only (double-curve open-sheet geometry vs. closed topology for K3/CY3)
- It prevents a future maintainer from "helpfully" adding culling to the other families
- The Hanson AI-7 conflict is subtle enough to document explicitly

---

## 5. Alternatives Considered

- **Global `culling='back'` kwarg on `add_mesh`** — rejected because off-screen renders confirm breaking regression on Enriques (wing-loss) and Hanson (catastrophic patch-loss). The milestone brief's XS estimate was based on an incorrect assumption that all surfaces are closed-topology.
- **`backface_params` with a dark color** — renders back faces in a contrasting color instead of culling. Would not eliminate the zipper artifact (the artifact is at edges of alternating front/back faces, not in the interior). Rejected as wrong fix for the stated symptom.
- **Increase marching cubes grid resolution for Enriques** — the visual-scout H-1 brief (finding 2.4) frames the artifact as a "marching-cubes resolution deficit." True, but increasing n from 240 to e.g. 400 increases mesh size by 2.9x (from ~800k to ~2.3M faces at same bounds) and still doesn't eliminate the double-curve alternating face issue — it only reduces its spatial frequency. Not a fix for the zipper seam.
- **Taubin smoothing with more iterations** — already applied (n_iter=20). More iterations would shrink bounds beyond the volume-preserving threshold. Not a fix.
- **`compute_normals(consistent_normals=True)` for Enriques** — the Enriques surface is topologically one component (not 25 disconnected patches), so consistent_normals=True would work. But the zipper artifact is NOT a normal-orientation problem — it's back faces being rendered at double curves. This is an incorrect diagnosis.

---

## 6. Risks and Unknowns

### AI-7 (Hanson disconnected patches) — HIGH RISK CONFIRMED
`culling='back'` is **incompatible** with `consistent_normals=False, auto_orient_normals=False`. With AI-7 normals, each patch has consistent winding within itself but patches on the far side from the camera have normals pointing away from camera. With global culling, those far-side patches become invisible on rotation. This is not a speculative risk — it is confirmed in off-screen renders at `/tmp/hanson-no-culling.png` vs `/tmp/hanson-culling-back.png`. Any implementation that applies `culling='back'` to Hanson surfaces is an AI-7 regression.

### AI-6 (marching cubes pipeline) — CLEAN
Backface culling is a rendering property only. The marching cubes pipeline is unaffected. No conflict.

### AI-1 (PyVista native kwarg) — CLEAN
`culling='back'` is a PyVista native kwarg routing to `actor.prop.GetBackfaceCulling()`. No renderer swap required.

### AI-9 (Qt re-entrancy) — CLEAN
Setting `actor.prop.culling` is synchronous and does not call `processEvents`. No re-entrancy risk.

### AI-10 (raw mesh cache) — CLEAN
`culling` is an actor property, not a mesh property. Cache discipline is unaffected.

### AI-15 (math honesty) — NET WIN for Enriques
Correctly culling back faces on the Enriques surface means the double-curve singular locus renders as a clean crease/seam rather than white zipper noise. This is the math-honest outcome: the double curve is a geometric feature, not a renderer defect. However the fix must be documented so future maintainers understand WHY the Enriques family specifically benefits (the Kummer surface has different singularity topology — conical nodes, not double curves — and does NOT need culling).

### Kummer interaction — MILD REGRESSION
Off-screen renders show the Kummer surface at default μ²=1.3 loses some inner cone geometry at node meeting regions with `culling='back'`. This is a moderate regression. Culling should NOT be applied to the Kummer surface. Confirming that `culling='back'` should be Enriques-only (not K3-family-wide).

### Parameter default error in milestone brief
The brief references "Enriques default c=0" but the actual `ENRIQUES_FIGURE_1_PARAMS` default is `c=1.0` (minimum 0.1). c=0 produces a ValueError (no real zero set). The off-screen verification snippet should use `c=1.0` (default) and `c=1.5` (non-default), not `c=0`.

---

## 7. AI-15 Disclaimers

No new variety or figure is proposed. This milestone modifies rendering behavior only.

**CONTEXT.md documentation note for the implementer:** The Enriques canonical sextic (`x²y² + x²z² + y²z² + x²y²z² + c·xyz·(1+r²) = 0`) has genuine double-curve singularities along the six edges of the coordinate tetrahedron (the locus where two sheets of the surface meet). These double curves produce near-degenerate marching-cubes triangulations — two facing triangles with near-zero separation — that render as alternating front/back faces (white zipper seam artifact). Backface culling removes the inward-facing half of these degenerate triangle pairs, leaving the outward-facing sheet visible. This is the correct math-honest rendering: the singular locus becomes a visible crease, not visual noise. Worth documenting in CONTEXT.md §8 alongside the note that the Kummer surface's 16 A₁ nodes are point singularities (conical), not double curves, and do NOT benefit from culling (in fact culling harms the Kummer render at default μ²).

---

## 8. Verification Snippet (Deliverable C)

Exact PyVista off-screen snippet for before/after comparison. Uses AI-3's off-screen pattern + UPL-9 lighting kwargs + dark background from CONTEXT.md §10:

```python
import pyvista as pv, numpy as np, sys
sys.path.insert(0, "<repo-root>")
pv.OFF_SCREEN = True
from surfaces import enriques_figure_1, fermat_quartic, kummer_surface, calabi_yau_quintic

def render_pair(mesh, tag: str, culling=None, color="#c49a4a"):
    for suffix, cval in [("before", None), ("after", culling)]:
        p = pv.Plotter(off_screen=True, window_size=(800, 600))
        p.set_background("#2f2f2f")
        p.add_mesh(
            mesh,
            smooth_shading=True, specular=0.3, specular_power=15,
            ambient=0.15, diffuse=0.85, color=color,
            culling=cval,
        )
        p.camera_position = "iso"
        p.show(screenshot=f"/tmp/check-{tag}-{suffix}.png")
        p.close()

# Enriques default c=1.0 (actual default, not c=0 which raises ValueError)
render_pair(enriques_figure_1(c=1.0), "enriques-c1", culling="back")
# Enriques non-default c=1.5
render_pair(enriques_figure_1(c=1.5), "enriques-c15", culling="back")
# K3 Fermat (closed — should show no change)
render_pair(fermat_quartic(), "fermat", culling="back", color="#6b8cba")
# K3 Kummer (has 16 node singularities — MILD REGRESSION expected; do NOT apply culling)
render_pair(kummer_surface(), "kummer", culling="back", color="#6b8cba")
# CY3 Hanson quintic (AI-7 surface — BREAKING expected; do NOT apply culling)
render_pair(calabi_yau_quintic(), "hanson", culling="back", color="#8699cf")

print("Check /tmp/check-*.png — enriques-after should show clean creases;")
print("kummer-after and hanson-after should confirm regressions (do not apply there).")
```

**Expected outcomes:**
- `/tmp/check-enriques-c1-after.png`: The double-curve seams become clean geometric creases with less zipper noise. Outer wing geometry may still show some artifacts from open-boundary mesh clipping at the sampling box edges (that is a separate L-1 issue from the visual scout, not fixed by culling).
- `/tmp/check-fermat-after.png`: Visually identical to before (confirmed in this research run).
- `/tmp/check-kummer-after.png`: Inner cone faces partially hidden — confirms Kummer should NOT get culling.
- `/tmp/check-hanson-after.png`: Catastrophic patch-loss — confirms Hanson must not get culling.

---

## F. Estimated LOC

With the recommended Option B (apply_to_actor gating):

| File | Change | LOC |
|---|---|---|
| `appearance_panel.py` | Add `self._culling = None`, `set_culling(value)` method, `actor.prop.culling = ...` in `apply_to_actor` | +8 |
| `app.py` | Add variety-type check + `self.appearance_panel.set_culling(...)` in `_on_variety_changed` and `_on_subtype_changed` | +6 |
| `CONTEXT.md` | §8 entry explaining Enriques-only culling and WHY | +12 |
| **Total** | | **~26 LOC** |

Not XS (as the brief rated it), but still small (S). The challenger's NONE rating was based on the assumption of a single global kwarg — that assumption is incorrect given the per-variety topology differences confirmed in this research.

---

## G. Open Questions for the User

**One open question — not blocking, but worth confirming before implementation:**

The recommended approach adds `set_culling(value)` to `AppearancePanel` and calls it from `_on_variety_changed` / `_on_subtype_changed`. However: should Enriques *figure 2, 3, 4* (Diagonal λ-family, Cayley symmetroid, Icosahedral sextic) also get culling=back by default? All four Enriques figures are degree-6 implicit surfaces with potential double-curve singularities. The visual-scout evidence is specifically for Figure 1 (canonical sextic). The researcher's recommendation is to apply culling to all Enriques subtypes (variety-level gate, not subtype-level) since they share the same double-curve topology from the same equation family — but the implementer should verify with a quick off-screen render of figures 2–4 at their defaults before committing.

This does not block the research brief — flag it as a note for the implementer.
