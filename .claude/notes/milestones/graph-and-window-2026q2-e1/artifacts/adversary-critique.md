# Adversary critique — graph-and-window-2026q2-e1 (UPL-9 / UPL-27 / UPL-28)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-21 | **Subject:** d9e4c0f..4236b89 — Sprint 0 bundle: VTK ambient/diffuse tune, dock-wrapped panel captures, capture-pipeline correctness

---

## Executive summary

No CRITICALs and no HIGHs. The dominant finding is a MEDIUM in the visual scout template: `agent-prompts.md` was updated to set the viewport background (`#2f2f2f` — UPL-28) but not the new ambient/diffuse lighting values (`ambient=0.15, diffuse=0.85` — UPL-9), meaning future scout renders will still be systematically under-lit relative to the live app. One LOW on agent-prompts.md hardcoding the background literal instead of importing `BG_VIEWPORT`, and one LOW on the missing CONTEXT.md §8.11 entry for the load-bearing `QDockWidget` ownership workaround. Zero CRITICALs, zero HIGHs, one MEDIUM, two LOWs. Safe to merge after the MEDIUM rectifies.

---

## Critical findings

None.

---

## High findings

None.

---

## Medium findings

### MEDIUM — Visual scout template missing UPL-9 ambient/diffuse lighting params

**Where:** `.claude/references/frontend-uplift/agent-prompts.md:48`
**Evidence:** The updated template reads `p.add_mesh(mesh, color="#9aa6c8", smooth_shading=True)` — no `ambient`, `diffuse`, or `specular` params. `app.py:380-387` now calls `plotter.add_mesh(..., specular=0.3, specular_power=15, ambient=0.15, diffuse=0.85)`. UPL-28 correctly added `p.set_background("#2f2f2f")` to the same template, but UPL-9's lighting delta was not mirrored.
**Why it matters:** Scout renders produced by this template will show surfaces with VTK's default ambient=0.0/diffuse=1.0 against the correct dark background. The shading depth will still read as "too flat" even after UPL-9 fixes the live app — future frontend-uplift scouts will produce lighting findings that the live app has already resolved, wasting a review cycle or (worse) an uplift candidate that re-opens the lighting question.
**Suggested fix:** Add `specular=0.3, specular_power=15, ambient=0.15, diffuse=0.85` to the `p.add_mesh()` call in the embedded template. Also add a comment `# UPL-9: match app.py:_apply_domain_and_render lighting` so the next maintainer knows to keep these in sync.

**Regression-guard test:** After the fix, run a grep: `grep -A3 "add_mesh" .claude/references/frontend-uplift/agent-prompts.md | grep "ambient"` — must produce a match. This can be a CI lint step or a manual pre-commit check.

---

## Low findings

### LOW — agent-prompts.md background literal hardcoded instead of referencing token

**Where:** `.claude/references/frontend-uplift/agent-prompts.md:47`
**Evidence:** `p.set_background("#2f2f2f")` — the literal is the current value of `PALETTE_LIGHT["BG_VIEWPORT"]` in `styles.py:51`, but the template does not import `styles.py`. The comment on line 43 correctly names the source (`styles.py:BG_VIEWPORT`), but the code doesn't consume it.
**Why it matters:** If `BG_VIEWPORT` is ever updated (e.g., dark palette work in UPL-4), the scout template will silently render against the old background color. The comment makes the intent traceable, but the link is prose-only.
**Suggested fix:** The template is executed as a standalone snippet; a practical fix is to have the snippet import `BG_VIEWPORT` from `styles` and use it: `from styles import BG_VIEWPORT; p.set_background(BG_VIEWPORT)`. Alternatively, keep the literal and add a `# keep in sync with styles.py PALETTE_LIGHT["BG_VIEWPORT"]` inline comment so a grep on BG_VIEWPORT finds both sites.

---

### LOW — CONTEXT.md §8 missing entry for QDockWidget ownership / no-takeWidget workaround

**Where:** `CONTEXT.md` (no existing entry for this bug class)
**Evidence:** The `_grab_in_dock` implementation in `render-panel-chrome.py:271-282` documents a 3-iteration discovery: (1) ownership crash on reuse, (2) non-existent `QDockWidget.takeWidget()` method, (3) `panel.setParent(None)` as the correct workaround. The docstring captures the "why" but CONTEXT.md §8's running list of "bugs caught and fixed" has no entry for this.
**Why it matters:** If a future maintainer refactors `_grab_in_dock` without reading the full docstring, they may attempt `QDockWidget.takeWidget()` (it's the obvious analogue to `QMainWindow.takeCentralWidget()`) and discover the crash again. A §8.11 entry makes the pitfall findable before the next iteration, matching the precedent set by §8.1–§8.10.
**Suggested fix:** Add `### 8.11 QDockWidget has no takeWidget() — use setParent(None)` to CONTEXT.md §8 with a one-paragraph explanation matching the pattern of §8.2.

---

## Frontend UI/UX findings

(Merged from `frontend-critique.md` — the frontend-ux critic walked the 12-axis UI/UX checklist; 11/12 axes were not applicable to this milestone's diff.  The two findings below cover the one MEDIUM and one LOW the critic surfaced.  The full 12-axis walkthrough remains in `frontend-critique.md` for reference.)

### MEDIUM — UPL-9 lighting applies to clipped-mesh path only; empty-clip fallback retains VTK defaults

**Where:** `app.py:360-372` (early-return branch) vs `app.py:380-387` (patched path)
**Evidence:** `_apply_domain_and_render` has two code paths. The patched path correctly adds `ambient=0.15, diffuse=0.85`. The early-return branch (entered when `clipped` is empty after domain clipping) calls `self.plotter.add_mesh(overlay, ...)` and returns without reconstructing `self._actor`. The surface actor from the previous render is still live with whatever lighting it was constructed with. Today this is moot — the empty-clip case shows only the wireframe overlay, no surface actor — but a future refactor that reconstructs a placeholder actor here would silently use VTK defaults (ambient=0.0, diffuse=1.0).
**Why it matters:** Latent consistency risk. A future contributor reading only the patched line will assume the UPL-9 parameters apply to all render paths. Structural symmetry between the two paths is invisible without a guard.
**Suggested fix:** Add a comment near `app.py:361` noting that `self._actor` is not reconstructed in this branch and that any future actor creation here must carry the same `ambient`/`diffuse` values as the main path. Alternatively, extract a module-level constant `_SURFACE_LIGHTING = dict(ambient=0.15, diffuse=0.85, specular=0.3, specular_power=15)` so both call sites share one source of truth.

### LOW — UPL-9 comment references "current-state-critic M-5" without naming the artifact

**Where:** `app.py:378` — `— current-state-critic M-5`
**Evidence:** The comment cites finding ID `M-5` but provides no path. "Current-state-critic" is not defined in `CONTEXT.md` or any `.claude/references/` file; the finding lives in `.claude/notes/frontend-uplifts/2026q2-graph-and-window/discover/current-state-critic-brief.md`. A future session cannot resolve the reference.
**Why it matters:** Dead-reference comments add archaeology cost if the lighting values are ever questioned. Otherwise accurate and well-motivated.
**Suggested fix:** Append the artifact path: `— see .claude/notes/frontend-uplifts/2026q2-graph-and-window/discover/current-state-critic-brief.md finding M-5`.

---

## What was done well

- **AI-3 compliance reasoning is explicit and correct.** The `_grab_in_dock` docstring at `render-panel-chrome.py:250-256` correctly identifies that the AI-3 ban targets `MainWindow` (which hosts `QtInteractor`), states that the vanilla `QMainWindow` host here contains zero `QtInteractor` instances, and cites `app-invariants.md AI-3` by name. This is textbook invariant-awareness and will prevent a future reviewer from mis-flagging this as an AI-3 violation.

- **Ownership crash fix is both correct and well-documented.** The `finally:` block at `render-panel-chrome.py:271-282` uses `panel.setParent(None)` before the host/dock go out of scope. The multi-paragraph comment explains exactly why this is necessary (C++ ownership transfer on `setWidget`), why `takeWidget()` doesn't work (absent from `QDockWidget`), and what would happen without the fix (crash on the HIRES capture after the DEFAULT capture). Verified: `PySide6.QDockWidget` has only `setWidget()` and `widget()` in its API — no `takeWidget()`.

- **clearFocus fix targets the correct widget.** `render-panel-chrome.py:221-224` calls `QApplication.focusWidget()` to find the actual focus holder and clears focus from that widget, not from the panel itself (`widget.clearFocus()` would be a no-op when focus is on a child). The two-call sequence (`clearFocus` → `processEvents`) correctly drains the `:focus` paint event. The comment explains the failure mode it prevents.

- **Qt enum is fully qualified.** The new `Qt.DockWidgetArea.LeftDockWidgetArea` at `render-panel-chrome.py:268` uses the fully-qualified form (AI-11 compliant). No shorthand enum aliases introduced.

- **No 3-digit hex introduced.** Both `#2f2f2f` (agent-prompts.md:47) and `#9aa6c8` (agent-prompts.md:48) are 6-digit. AI-13 clean.

- **UPL-9 ambient/diffuse do not interact with `apply_to_actor`.** `appearance_panel.py:313-318` sets `color`, `style`, `show_edges`, `opacity`, and `interpolation` — but not `ambient` or `diffuse`. The new values are baked into the VTK actor on `add_mesh` and are never overwritten by subsequent `apply_to_actor` calls. The lighting improvement persists correctly through opacity, wireframe, and shading mode changes.

- **processEvents in `_grab` carries no re-entrancy risk.** `render-panel-chrome.py` runs no `QApplication.exec()`, has no `_render_current` slots, and holds no `_computing` state. The 3-call processEvents pattern in `_grab` (drain-layout → drain-focus → drain-focus-paint) is safe in this context. AI-9 does not apply.

- **Visual scout template background fix is accurate.** The `p.set_background("#2f2f2f")` addition to `agent-prompts.md:47` matches `PALETTE_LIGHT["BG_VIEWPORT"]` exactly as defined in `styles.py:51`, so future scout renders will correctly represent the app's dark viewport for all surface contrast / color legibility findings.

---


## Cross-critic agreement

The following findings cluster within 5 lines of each other in the same file. Multiple critics flagged the same area -- these are the strongest signals to fix first.

- **L1, M1** at `.claude/references/frontend-uplift/agent-prompts.md:47-48` (LOW): agent-prompts.md background literal hardcoded instead of referencing token; Visual scout template missing UPL-9 ambient/diffuse lighting params

## Recommended rectification order

1. **Fix the MEDIUM (M1) first.** Add `ambient=0.15, diffuse=0.85, specular=0.3, specular_power=15` to the `p.add_mesh()` call in `agent-prompts.md:48` and add a sync comment. This is a one-line change that prevents the next frontend-uplift scout from generating already-resolved lighting findings.
2. **Fix LOW L1 as a follow-on to M1.** While touching `agent-prompts.md` for M1, replace the `#2f2f2f` literal with `from styles import BG_VIEWPORT` + `p.set_background(BG_VIEWPORT)`, or add the sync comment. Same file, same edit session.
3. **Fix LOW L2 at milestone close.** Add CONTEXT.md §8.11 for the `QDockWidget` ownership / `takeWidget()` pitfall. This can be deferred to the milestone-close doc pass since it's a documentation gap, not a code correctness issue.

---

*End of critique. Mandatory rectification: M1 (scout lighting template parity). L1 and L2 are optional but recommended before milestone close.*
