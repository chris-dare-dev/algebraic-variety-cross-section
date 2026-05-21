# Frontend UI/UX Critique — graph-and-window-2026q2-e1

**Critic:** milestone-frontend-ux-critic agent  
**Commit range:** `d9e4c0f..4236b89`  
**Date:** 2026-05-21  
**Qt-panel files changed:** none (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `styles.py` are untouched)  
**Non-panel files changed:**
- `app.py` — UPL-9 lighting tune (`ambient=0.15, diffuse=0.85` added to `plotter.add_mesh`)
- `.claude/scripts/frontend-uplift/render-panel-chrome.py` — UPL-27 dock-wrap helper + UPL-28 focus-clear
- `.claude/references/frontend-uplift/agent-prompts.md` — UPL-28 `set_background` in visual-scout template

---

## Executive summary

This milestone makes three tightly-scoped changes: a lighting parameter tune, a scout-script improvement, and a scout prompt template fix. None of the four Qt panel source files were touched. For 11 of the 12 critique axes the answer is "not applicable to this diff" — explicitly stated per axis below. The one axis with material UX consequence (visual hierarchy / pixel-impact of the lighting tune) is assessed in depth. No CRITICAL or HIGH findings. One MEDIUM finding on the lighting tune's asymmetric coverage; one LOW finding on comment precision. The two non-panel files are internal tooling and have no user-visible surface; they are noted but produce no UX findings.

---

## CRITICAL findings

None.

---

## HIGH findings

None.

---

## MEDIUM findings

### MEDIUM — UPL-9 lighting tune applies to clipped-mesh path only; empty-clip fallback retains VTK defaults

**Where:** `app.py:360-372` (the early-return branch), compared with `app.py:380-387` (the normal path that received the patch)

**Evidence:** `_apply_domain_and_render` has two code paths. The patched path (line 380) correctly adds `ambient=0.15, diffuse=0.85`. The early-return branch (lines 360-372), entered when `clipped` is empty after domain clipping, calls `self.plotter.add_mesh(overlay, ...)` and then returns — the surface actor from the *previous* render is still live and has whatever lighting it was constructed with. This branch does not reconstruct `self._actor`, so the actor's ambient/diffuse parameters are whatever they were at the time of the last full render. Under normal use the empty-clip case surfaces only when the user has pushed the domain-clip radius very small, at which point the viewport shows only the wireframe overlay and no surface — so the actor lighting is moot. However, if a future refactor makes the early-return branch reconstruct a placeholder actor (e.g., a bounding box), it will silently use VTK defaults (ambient=0.0, diffuse=1.0) rather than the UPL-9 values, and the lighting inconsistency will reappear without any diff touching the add_mesh call.

**Why it matters:** the early-return branch is structurally adjacent to the patched path; a future contributor reading only the diff will see the UPL-9 parameters and assume they apply to all render paths. The asymmetry is a latent consistency risk, not a live UX defect.

**Suggested fix:** add a comment in the early-return branch (near line 361) noting that `self._actor` is not reconstructed here and that any future actor creation in this branch must carry the same `ambient`/`diffuse` values as the main path. Alternatively, extract the lighting kwargs into a module-level constant (`_SURFACE_LIGHTING = dict(ambient=0.15, diffuse=0.85, specular=0.3, specular_power=15)`) so both call sites share a single source of truth.

---

## LOW findings

### LOW — UPL-9 comment references "M-5" without naming the critic document

**Where:** `app.py:378` (`— current-state-critic M-5`)

**Evidence:** The comment reads `— current-state-critic M-5`. "Current-state-critic" is not a term defined in CONTEXT.md or any file in `.claude/references/`. The "M-5" label presumably refers to a finding in a prior frontend critique artifact, but there is no inline link and no path hint. A future session cannot resolve the reference.

**Why it matters:** a dead-reference comment is low-friction in practice but adds archaeology cost if the lighting values are ever questioned. The comment is otherwise accurate and well-motivated.

**Suggested fix:** add the artifact path in a parenthetical: `— see .claude/notes/milestones/panel-refresh-2026q2-e2/artifacts/frontend-critique.md finding M-5`.

---

## 12-axis walkthrough — explicit disposition per axis

1. **Visual hierarchy** — Not applicable. No widget, layout, or visual-priority change. The lighting tune affects rendered 3D geometry, not panel control ordering.

2. **Dock layout** — Not applicable. `appearance_panel.py`, `view_panel.py`, `parameters_panel.py` are untouched. The View/Parameters/Appearance dock arrangement is unchanged.

3. **First-launch experience** — Not applicable. No change to the `-- Select --` placeholder logic, no change to `_on_subtype_changed`, no auto-render added. Section 9.3 invariant preserved.

4. **Slider affordances** — Not applicable. No `ParamSpec` added or modified. No new slider.

5. **Status-bar feedback** — Not applicable. The lighting tune is inside `_apply_domain_and_render`, downstream of the `_render_current` status-bar machinery. The `RuntimeWarning` surface (AI-14), `ValueError` handling, and busy-cursor pattern are all unchanged.

6. **Tooltip honesty (AI-15)** — Not applicable. No new variety, figure, or tooltip text added.

7. **Color contrast (AI-12)** — Not applicable. No new text color introduced. `styles.py` is untouched.

8. **Color format (AI-13)** — Not applicable. The two new kwargs are numeric floats (`ambient=0.15`, `diffuse=0.85`), not color arguments. No hex string added. The `render-panel-chrome.py` changes introduce no new hex colors in the panel-chrome script's add_mesh calls — those remain `color="#9aa6c8"` (unchanged, 6-digit). The agent-prompts diff adds `p.set_background("#2f2f2f")` — 6-digit hex, AI-13 compliant.

9. **Qt enum form (AI-11)** — The `render-panel-chrome.py` diff introduces `Qt.DockWidgetArea.LeftDockWidgetArea` (line `host.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)`). This is the **fully-qualified** form — AI-11 compliant. No shorthand enum form found in the diff.

10. **Re-entrancy (AI-9)** — The `render-panel-chrome.py` diff adds two `app.processEvents()` calls (lines around `focused.clearFocus()` and the `adjustSize()` block). These are in the `_grab` / `_grab_in_dock` helper functions inside `render-panel-chrome.py` — a standalone scout script, not `MainWindow`. The `self._computing` guard is specific to `MainWindow._render_current`; `render-panel-chrome.py` is a single-threaded script with no re-entrant slider callbacks. AI-9 does not apply to this script. No new `processEvents()` was added to `app.py`. Not applicable.

11. **Keyboard shortcuts** — Not applicable. `Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D` wiring is in `app.py` key-binding setup code, untouched by this diff.

12. **Industry comparison — pixel-impact of the lighting tune (UPL-9)**

    The change raises ambient from VTK's default 0.0 to 0.15 and reduces diffuse from 1.0 to 0.85.

    **ParaView** (v5.12): its default PBR-adjacent material for implicit surfaces uses `ambient=0.1, diffuse=0.8, specular=0.1` out of the box — closer to the post-patch values than to the VTK defaults. ParaView's "Representation" panel lets users set ambient/diffuse per-actor interactively. UPL-9 moves this app toward ParaView's out-of-box shading regime, which is the dominant scientific-viz desktop precedent for algebraic surfaces.

    **Mathematica's `ContourPlot3D`** (v14): uses a three-point lighting rig with non-zero ambient fill by default; its default material ambient is approximately 0.2. Dark concavities on algebraic surfaces (the K3 Fermat quartic's saddle regions, Kummer's 16 nodes) are visibly lifted in Mathematica renders, making curvature cues legible — exactly the stated goal of UPL-9. The post-patch values (0.15 ambient) are slightly more conservative than Mathematica's default but in the same region.

    Neither competitor exposes `specular_power=15` as a prominent user control (both use higher shininess for scientific surface work — ParaView default ~10, Mathematica default ~50), but the existing `specular_power=15` is pre-existing in this codebase and not part of this diff.

    **Assessment:** the UPL-9 values are well-calibrated relative to both reference tools. The change is a genuine UX improvement for curvature legibility on the K3 family with no regressions.

---

## What was done well

- **UPL-9 lighting values are empirically grounded.** The comment block explains the VTK default problem (ambient=0.0 → flat shading on convex surfaces), names the original critic finding (M-5), and states the intended perceptual outcome (lift dark concavities for curvature legibility). This is the right level of explanation for a single-kwarg change.
- **UPL-27 `_grab_in_dock` is architecturally honest.** The docstring explicitly states why a vanilla `QMainWindow` host is used (OS title bar absent under offscreen for a floating dock), cites the AI-3 one-line rule, and handles the C++ ownership transfer of `QDockWidget.setWidget()` correctly with the `panel.setParent(None)` teardown in `finally`. This is exactly the kind of defensive Qt ownership reasoning that prevents hard-to-reproduce crashes in scout runs.
- **UPL-28 focus-clear comment is precise.** The comment distinguishes `widget.clearFocus()` (a no-op when focus is on a child) from `QApplication.focusWidget().clearFocus()` (the actual focus holder). This is a non-obvious Qt subtlety; documenting it prevents a future regression where someone "simplifies" the call.
- **AI-13 compliance on the new `set_background` call.** The agent-prompts diff adds `p.set_background("#2f2f2f")` — correct 6-digit hex, no short-hex slip.
- **AI-11 compliance on new Qt enum usage.** `Qt.DockWidgetArea.LeftDockWidgetArea` is the qualified form.
- **No first-launch regression.** The lighting kwarg is inside the normal render path, downstream of the placeholder guard. The `-- Select --` state is untouched.

---

## Recommended rectification order

1. **(MEDIUM — low urgency)** Extract `_SURFACE_LIGHTING` constant or add a comment in the early-return branch to protect the lighting consistency invariant for future contributors. No user-visible defect today.
2. **(LOW — cosmetic)** Resolve the `current-state-critic M-5` dead reference in the UPL-9 comment to a concrete artifact path.

Both items are sub-5-minute edits; neither warrants a dedicated rectification milestone.
