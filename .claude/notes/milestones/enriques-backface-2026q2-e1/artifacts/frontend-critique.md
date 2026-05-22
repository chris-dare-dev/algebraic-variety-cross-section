# Frontend UX Critique — enriques-backface-2026q2-e1

**Milestone:** enriques-backface-2026q2-e1
**Commit range:** 8e5c30c..4a9530a
**Critic:** milestone-frontend-ux-critic (Claude Sonnet 4.6)
**Date:** 2026-05-22

---

## Executive Summary

The diff is narrow and well-scoped: 3 files changed (`CONTEXT.md`, `app.py`,
`appearance_panel.py`), adding per-variety back-face culling gated on
`"Enriques surface"`.  No new colors, no new Qt enums, no `processEvents` calls,
no panel layout changes.  The implementation is architecturally clean.

The primary UX gap is **discoverability**: culling is silently active when
Enriques is selected — the Appearance dock shows no indicator, and the status
bar gives no signal.  A secondary UX gap is the **wireframe + culling
interaction**: with culling active, switching to Wireframe mode on Enriques
hides back-facing edges, creating a visually inconsistent wireframe compared
to every other variety.  Neither is a regression relative to the pre-milestone
state (the white-zipper seam was worse), but both will confuse advanced users.

**Severity counts:** 0 CRITICAL, 0 HIGH, 2 MEDIUM, 3 LOW.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM-1 — No discoverability signal that back-face culling is silently active

**Where:** `app.py:254` (`set_culling` call in `_on_variety_changed`) and
`appearance_panel.py:337` (`apply_to_actor`)

**Evidence:**
When the user selects "Enriques surface", the status bar message is:
`"Variety: Enriques surface. Now choose a model."` — no mention of culling.
The Appearance dock shows no checkbox, no badge, no muted annotation.
`self._culling` is set to `"back"` silently.  A user who opens the
Appearance dock while on Enriques sees identical controls to K3 or CY3.
They have no affordance to discover that culling is engaged or to turn
it off if they want to inspect the double-curve geometry directly.

**Why it matters:**
Research users and mathematicians studying the double-curve locus may
want to toggle culling off to see both sheets of the singularity — exactly
the use-case where a "hidden knob" is most harmful.  An expert who knows
to look at `actor.prop.culling` via a Python REPL has the power; a GUI user
does not.  ParaView 5.13 exposes "Cull Backface" as an explicit checkbox
under Properties > Backface Styling (see https://docs.paraview.org/en/v5.13.3/UsersGuide/displayingData.html)
— its default is OFF; users must opt in.  AVC does the opposite: silently
opts in on variety selection.  Blender's Eevee renderer follows the same
convention (per-material "Backface Culling" checkbox, defaults OFF).
The AVC's hardcoded-on-for-Enriques choice is bespoke relative to both
conventions and deprives the user of the control both competitors provide.

The V0 scope rationale (no UI toggle) is valid as a deferral, but a minimal
status-bar note on Enriques variety selection ("Back-face culling active — hides
zipper seam at double-curve singularity") costs one line and gives the expert
user a diagnostic signal without requiring a new dock widget.

**Suggested fix (V0 minimal):**
In the `else:` branch of `_on_variety_changed` at `app.py:283`, the
`"Enriques surface"` case falls through to
`f"Variety: {name}. Now choose a model."` — specialize it:
```python
elif name == "Enriques surface":
    self.statusBar().showMessage(
        "Enriques surface — back-face culling active to suppress "
        "double-curve zipper seam. Now choose a model."
    )
```
V1 fix (deferred): add a read-only QLabel badge ("Culling: back") under
the Shading group in AppearancePanel that is shown/hidden by `set_culling`.

---

### MEDIUM-2 — Wireframe mode + back-face culling: back-facing edges silently hidden on Enriques

**Where:** `appearance_panel.py:326-337` (`apply_to_actor`, wireframe +
culling assignment order)

**Evidence:**
In `apply_to_actor`, the code sets:
```python
actor.prop.style = "wireframe" if self._wireframe else "surface"
# ...
actor.prop.culling = self._culling or "none"
```
In VTK, `culling="back"` applies at the face level regardless of the
`style` flag.  In wireframe mode, each edge is owned by a face; if that
face's normal points away from the camera, VTK culls the edge.  The result
on Enriques wireframe: some edges vanish as the camera rotates (the same
topology that makes `consistent_normals=False` hazardous for CY3 in solid
mode).  Non-Enriques wireframe shows all edges at all camera angles.  The
same toggle in the same dock panel produces different behavior depending on
which variety is active — with no indicator to explain why.

A user on Enriques in wireframe mode who rotates the camera will see edges
appearing and disappearing.  They may interpret this as a mesh defect (a
genuine double-curve artifact) rather than an intentional culling effect —
the inverse of what we intend.

**Why it matters:**
The wireframe view is the most common way to inspect mesh topology.
Hiding edges on culling makes the topology inspection misleading for the
one family where topology inspection is most scientifically interesting
(the double-curve singularity is exactly what the user would want to trace
in wireframe).  Mathematica's `ContourPlot3D[..., Mesh -> True]` does NOT
apply back-face culling to the mesh overlay — the mesh overlay is rendered
two-sided regardless of the body shading mode.  This is the correct
separation of concerns: culling is a shading concern, not a topology-display
concern.

**Suggested fix:**
In `apply_to_actor`, suppress culling when wireframe mode is active:
```python
# Culling is meaningful in surface mode; in wireframe it hides topology edges.
effective_culling = "none" if self._wireframe else (self._culling or "none")
actor.prop.culling = effective_culling
```
This preserves the anti-seam benefit in solid+Phong mode (where it was
designed) and restores full-edge visibility in wireframe mode.

---

## LOW

### LOW-1 — `set_culling` docstring has a misleading bullet about "wing tips"

**Where:** `appearance_panel.py:388-390`

**Evidence:**
The docstring includes:
```
- Enriques wing tips also get clipped at the marching-cubes
  box, but the math-honest singular-locus rendering is the
  net win.
```
The marching-cubes box clip is a sampling-domain artifact (the surface
extends past the `bounds` grid), not a culling effect.  Wing tips are
clipped regardless of whether `culling="back"` or `culling="none"`.  A
future maintainer reading this bullet will reasonably infer that culling
causes the wing-tip clip — the "but the net win" framing reinforces
that impression.

**Why it matters:**
If a maintainer is debugging a report of "Enriques wing tips missing" and
reads this bullet, they may remove culling to fix it — only to find the
clip persists (because it's the bounds, not the culling).  The misleading
bullet is a documentation debt that will cost debugging time.

**Suggested fix:**
Remove the bullet or rewrite it to:
```
- Note: wing-tip truncation on Enriques is a sampling-bounds artifact
  (surface extends past the marching-cubes grid), not a culling effect.
  Culling is orthogonal to this.
```

---

### LOW-2 — Topology homogeneity claim for all 4 Enriques figures is unverified in-code

**Where:** `app.py:252-253` and `appearance_panel.py:380-383`

**Evidence:**
Both comments state: "all 4 Enriques figures share the double-curve topology."
The Cayley quartic symmetroid (Fig. 3: `(x+y+z+xy+xz+yz)² = k·xyz`) is
degree 4, not 6, and is a quartic with isolated nodal singularities
(ordinary double points, ODPs) rather than the sextic's double-curve locus.
Phase 2 verification renders showed 40222→40222 byte-size identity for the
Cayley figure — culling has no visible effect — which is consistent with it
not having the same double-curve topology.  The claim in the comments
over-asserts; the correct claim is "culling is harmless for all 4 Enriques
figures, and beneficial for those with double-curve singularities."

**Why it matters:**
This is an AI-15 precision concern: math claims in code comments should be
honest about what we know.  If a contributor adds an Enriques Fig. 5 with
a different singularity type (e.g., a cusp locus rather than a double-curve
locus), the comment suggests they should apply culling without investigation.
The gate is safe (culling is harmless on the Cayley figure), but the
justification is imprecise.

**Suggested fix:**
Amend the comment to: "culling is beneficial for Enriques figures with
double-curve singularities (Fig. 1, 2, 4); harmless for Fig. 3 (Cayley
symmetroid, ODP singularities).  If adding a new Enriques figure, verify
its singularity type before assuming culling applies."

---

### LOW-3 — No Enriques-specific status-bar message after subtype render (AI-15 context gap)

**Where:** `app.py:413-421` (`_render_current` status-bar update at the end of render)

**Evidence:**
After a successful render, the status bar shows:
`"{surface.label} · N verts, M faces · param=value, ..."`
For Enriques canonical sextic, `surface.label` is
`"Enriques canonical sextic"` — no reminder that culling is engaged or
what the double-curve singularity is.  The CY3 family gets explicit
context in the status bar AND a Parameters dock banner explaining that
CY3 figures are 2D real shadows (see `app.py:262-270`).  The Enriques
family gets the same rendering-quality fix (culling) but no status-bar
context for the user who wonders why the seam looks clean.

This is a gap relative to AI-15 (math-honesty / honest "real shadow"
disclaimers): the Enriques figures are "degree-6 surfaces in P³ birational
to Enriques surfaces" per CONTEXT.md §5.2, and culling is an AI-15-adjacent
rendering decision (hiding the mathematical artifact of the double-curve).
A one-line addition after the normal render message would make the math
visible to the user.

**Why it matters:**
A low-friction user who notices the seam is gone in v0 but was present in
a prior screenshot cannot discover why without reading the source.
Consistency with the CY3 pattern (explicit disclaimer) suggests Enriques
deserves a similar signal.

**Suggested fix (LOW; deferrable to v1):**
After rendering any Enriques subtype, append a muted status note like:
`" | culling active — hides double-curve seam"`.  This mirrors the
Dwork conifold RuntimeWarning pattern: informational but not alarming.

---

## What was done well

1. **The variety-level gate architecture is correct and defensively documented.**
   The gate comment in `app.py:237-256` is unusually thorough — it names
   the specific failure mode for each non-Enriques variety (CY3 AI-7 patch
   flip, Kummer node hollows, Fermat no-op) and points to `CONTEXT.md §8.13`.
   A future contributor who adds a variety can read exactly why the gate
   exists before deciding whether their new variety needs culling.

2. **`set_culling` follows the established Pattern-A correctly.**
   The method stores state, does not trigger a render, and lets the normal
   `apply_to_actor` chain push the value through.  This is identical in
   structure to `set_default_color` (UPL-2) and `refresh_icons` (UPL-4) —
   consistent with prior milestones.  AI-9 safe (no `processEvents`).

3. **Re-establishment on Enriques→K3→Enriques is correct by construction.**
   `_on_variety_changed` calls `set_culling` on every variety switch without
   QSettings persistence.  Switching back to Enriques re-calls
   `set_culling("back")` unconditionally.  No stale-state bug.

4. **The `CONTEXT.md §8.13` entry is comprehensive.**
   It documents the topology rationale, the failure modes per family, the
   "new Enriques figure" guidance, and the "new K3/CY3 figure" anti-guidance.
   This is the definitive discoverable entry point for this feature.

5. **No token-discipline issues.**
   No new colors, no short-hex, no shorthand Qt enums, no new `processEvents`,
   no first-launch regression.  Diff is surgically scoped.

---

## Industry comparison notes (Axis 12)

- **ParaView 5.13:** Exposes "Cull Backface" as an explicit opt-in checkbox
  under Properties > Backface Styling (defaults OFF, user-controlled per actor).
  The AVC's variety-gated auto-on-for-Enriques is bespoke; it matches no
  ParaView convention.  The implication: expert users expect to find culling in
  the Properties panel, not to have it silently applied.  MEDIUM-1 above is the
  concrete finding from this comparison.
  Source: https://docs.paraview.org/en/v5.13.3/UsersGuide/displayingData.html

- **Blender Eevee:** Per-material "Backface Culling" checkbox, defaults OFF in
  solid mode, ON only in final render mode.  Same convention as ParaView —
  explicit, per-object, user-controlled.

- **Mathematica `ContourPlot3D`:** Mesh overlay (`Mesh -> True`) renders all
  edges two-sided regardless of body shading mode.  Culling does not propagate
  to the mesh overlay.  This is the correct behavior model for MEDIUM-2:
  culling belongs to shading, not to the wireframe topology display.

---

## Recommended rectification order

1. **MEDIUM-2 (wireframe + culling):** One-line fix in `apply_to_actor`.
   High-impact / low-effort.  Prevents topology-inspection confusion on the
   variety where topology is most scientifically relevant.

2. **MEDIUM-1 (status-bar discoverability):** One-line fix in
   `_on_variety_changed`.  Gives expert users a diagnostic signal.

3. **LOW-1 (misleading wing-tip bullet):** Docstring edit, no behavior change.

4. **LOW-2 (topology homogeneity claim):** Comment precision edit.

5. **LOW-3 (post-render status note):** Deferrable to v1; consistent with
   CY3 context-hint pattern.
