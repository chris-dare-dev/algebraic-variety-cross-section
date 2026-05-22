# Implementation plan — enriques-backface-2026q2-e1

**Inline path. ~26 LOC across 3 files.** Per-variety gating via `apply_to_actor` (Option B from the research brief).  The researcher proved global `culling='back'` breaks Enriques (wing-loss), Hanson (AI-7 catastrophic patch-loss), and Kummer (mild) — culling MUST be Enriques-only.

1. **appearance_panel.py** — Add `self._culling: str | None = None` to `__init__`; add `set_culling(value)` public method (Pattern-A — mirrors `set_default_color` / `refresh_icons` from the last 3 milestones); update `apply_to_actor` to push `actor.prop.culling = self._culling or 'none'`.  ~8 LOC.

2. **app.py** — In `_on_variety_changed`, call `self.appearance_panel.set_culling('back' if name == 'Enriques surface' else None)` alongside the existing `set_default_color` call.  Variety-level gate covers all 4 Enriques subtypes (canonical sextic, λ-family, Cayley symmetroid, icosahedral sextic) without per-subtype branching.  ~4 LOC.

3. **CONTEXT.md** — Add §8.13 "Enriques double-curve singularities require back-face culling" entry explaining: (a) the double-curve topology — sheets approach zero separation, marching cubes makes alternating front/back triangles, Phong lighting shows them as zipper noise; (b) why culling helps ONLY Enriques (K3 nodes are point-conical not double-curve; CY3 Hanson has AI-7 disconnected-patch normals that culling fights); (c) the per-variety gate at the `set_culling` call site so a future maintainer doesn't "helpfully" remove the conditional.  ~15 LOC.

4. **Verify** — Off-screen renders per CONTEXT.md §10:
   - Enriques canonical sextic at default `c=1.0` BEFORE / AFTER → confirm zipper seams disappear
   - K3 Fermat / K3 Kummer / CY3 Hanson at defaults AFTER → confirm no regression (culling only applies when variety is Enriques, so these should look identical)
   - Enriques figures 2/3/4 (λ-family, Cayley, icosahedral) at defaults → confirm variety-level gate is correct (no regression vs no-culling baseline; ideally improvement)
   - `pytest tests/ -q` stays at 200.

5. **Commit** — `feat(enriques-backface-2026q2-e1): apply backface culling per-variety for Enriques families`.
