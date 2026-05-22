# Adversary critique — realtime-variety-render-e4b (CAND-3 coarse-preview LOD)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** commit range `4db5c12..601612c` (1 commit, 1847 LOC diff: ~376 LOC production+test+docs / ~1471 LOC milestone artifacts)

> Format reference: `.claude/references/critique-format.md`.

Diff stats (`git diff --stat`):

```
.../milestone-researcher/lessons.md           |  23
.../artifacts/implementation-plan.md          |  67
.../dispatch.log                              |   4
.../research/agent-a-brief.md                 | 578
.../research/agent-b-brief.md                 | 152
.../state.json                                |  51
.claude/references/app-invariants.md          |   2
CONTEXT.md                                    |  17
app.py                                        | 202
render_worker.py                              |  21
surfaces.py                                   | 107
tests/test_coarse_n.py                        | 280  (new)
tests/test_render_worker.py                   |  46
```

Production+test+docs surface: ~376 LOC (app.py + render_worker.py + surfaces.py + tests/* + CONTEXT.md + app-invariants.md). Milestone artifacts (state/research/dispatch/lessons): ~875 LOC inflation. 407 tests pass on Phase 2 close.

---

## Executive summary

- The two-pass LOD scaffolding (`Surface.coarse_n`, `dispatch_mode`, `MeshResult.is_coarse`, `_render_current(coarse=...)`, AND-promote on `_pending_is_coarse`) is structurally clean: every state mutation is localized, the truth table for AND-promote is enumerated in a comment block, and AI-15 honesty is correctly enforced via the Preview-badge contract. **[Highest finding: HIGH]**
- One **HIGH** review-quality auto-finding (diff > 400 LOC) — disposition "no code action required" since >70 percent of the diff is milestone artifacts.
- One **HIGH** — HQ-smoothing kwarg is injected *before* the coarse-n injection in `_render_current`, so a coarse drag-tick on Enriques fig 1+2 with HQ enabled fires `second_smooth_iter=40` at the coarse grid, partially defeating the speed benefit (the whole point of CAND-3 is sub-frame drag previews).
- One **MEDIUM** — surfaces.py:79 and surfaces.py:1235 reference `tests/test_coarse_n_topology.py`, but the file shipped is `tests/test_coarse_n.py`. A future agent searching for the n-sweep coverage by the documented name will not find it.
- One **MEDIUM** — `MeshResult` doctring (render_worker.py:95-103) claims the slot will write "Preview — {label} — NNN ms" but the actual app.py implementation includes `hq_label` between `{label}` and `— NNN ms`. The docstring's contract is incomplete; rectifier should reconcile.
- One **MEDIUM** — `_on_mesh_ready`'s coarse branch returns *after* `_apply_domain_and_render` runs but *before* the standard `print(f"[render] ...")` stdout line. The CAND-12 "one stdout log line per completed generate()" contract is silently broken for the coarse path: a long drag burst produces N coarse renders and only the release prints. Minor maintainability/observability hit.
- One **LOW** — the test `test_coarse_n_fermat_quartic_smoke` asserts axis extent `1.5 < extent < 2.5` but Fermat at `c=1` sits at exactly `|x|=1` so extent ≈ 2.0; the bounds are correct but the test would still pass for an erroneously-clipped mesh at 1.6 extent. Tighter bound would be `1.95 < extent < 2.05`.
- One **LOW** — the `_pending_is_coarse` field is documented in the dataclass-style instance setup but is never reset on `_current_surface = None` paths (defensive note only; the field flows correctly through every transition I traced).

**Verdict: SHIP-WITH-FIXES.** Foundation is sound, the AI-15 Preview-badge contract is correctly implemented, AND-promote is correct, and the AI-6 three-layer Hanson skip holds. The HQ × coarse interaction (HIGH-2) wants a one-line fix; the doc-reference drift (MEDIUM-1) is a one-edit cleanup. No CRITICALs, no AI invariant violations.

---

## Critical findings (must-fix before this can ship)

None.

---

## High findings (should-fix this iteration)

### HIGH — Review-quality at risk (diff > 400 LOC)

**Where:** no specific file — process auto-finding
**Evidence:** `git diff 4db5c12..601612c | wc -l` returns 1847 lines. The 10-axis checklist mandates this finding above 400 LOC.
**Why it matters:** Diffs above 400 LOC are statistically harder to review thoroughly; the auto-finding ensures the reviewer logs the breakdown explicitly so the rectifier can prioritize.
**Suggested fix:** No code action. The breakdown is production+test+docs ~376 LOC / milestone artifacts (state.json, dispatch.log, research briefs, agent-memory) ~1471 LOC. Disposition: "no code action required" — artifact inflation is the documented pattern for milestone-pipeline commits and the production surface is small enough to review end-to-end.

### HIGH — HQ smoothing fires under coarse drag preview, defeating the LOD speed benefit

**Where:** `app.py:690-716` (the HQ-injection block at lines 690-695 precedes the coarse-injection block at 705-716 inside `_render_current`)
**Evidence:**
```
_is_hq_active = (
    surface.generate in _HQ_SMOOTHING_ELIGIBLE_GENERATORS
    and self.appearance_panel.hq_smoothing
)
if _is_hq_active:
    params["hq_smoothing"] = True
...
_is_coarse_active = coarse and surface.coarse_n > 0
if _is_coarse_active:
    params["n"] = surface.coarse_n
```
For Enriques fig 1 / fig 2 with HQ-smoothing toggle on, a drag-tick routes through `dispatch_mode == "coarse"` and dispatches the worker with `params = {"n": 80, "hq_smoothing": True}`. `_marching_cubes_to_polydata` then runs `second_smooth_iter=40` (per `enriques-hq-smoothing-2026q3-e1` docstring: +138 ms) on the coarse field — which is documented as roughly 3-4× faster than full at n=240. The coarse path's whole purpose per CAND-3 is sub-100 ms drag preview, and stacking +138 ms onto every coarse tick erodes that.
**Why it matters:** The user opted into HQ for *production-fidelity* rendering on release; bolting HQ onto drag previews is a feature-interaction the milestone brief did not call out, and the speed regression silently undercuts AI-15's "Preview" honesty contract — a preview that's barely faster than full is less honest than one that's clearly transient. This is the kind of feature-cross-interaction that compounds: future LOD candidates would inherit the same wiring bug.
**Suggested fix:** Skip HQ injection when `_is_coarse_active` is True — coarse previews are transient and a single Taubin pass is consistent with the e4 baseline. One-line guard: `if _is_hq_active and not _is_coarse_active: params["hq_smoothing"] = True`. Document the choice in CONTEXT.md §8.19 (the Preview-badge contract section).
**Regression-guard test:** Add a test row to `tests/test_coarse_n.py` that monkey-patches the HQ-eligibility check and asserts the params dict handed to MeshWorker carries `n=coarse_n` but NOT `hq_smoothing=True` when both `coarse=True` and `hq_active=True` for Enriques fig 1.

---

## Medium findings (nice-to-fix)

### MEDIUM — Stale test-file reference (`test_coarse_n_topology.py` does not exist)

**Where:** `surfaces.py:79` and `surfaces.py:1235`
**Evidence:**
- `surfaces.py:79`: "validated by tests/test_coarse_n_topology.py's n-sweep — the floor is..."
- `surfaces.py:1235`: "each floor is validated by tests/test_coarse_n_topology.py."

The actual shipped test file is `tests/test_coarse_n.py` (confirmed via `ls tests/test_coarse*`). The implementation-plan.md and agent-a-brief.md also use the old name (artifacts; lower priority). A `grep` for `test_coarse_n_topology` returns 5 hits but the file is 0 hits.
**Why it matters:** A future agent investigating the per-surface floor justification (e.g., a follow-up milestone tuning coarse-n values) will grep for the documented filename and find nothing. CONTEXT.md §6's institutional-memory contract relies on grep-able names being accurate.
**Suggested fix:** Replace `tests/test_coarse_n_topology.py` with `tests/test_coarse_n.py` in surfaces.py:79 and surfaces.py:1235 (and optionally in the milestone artifacts for cleanliness, but those don't compound).

### MEDIUM — `MeshResult.is_coarse` docstring claims a Preview-badge format the slot does NOT emit

**Where:** `render_worker.py:95-103`
**Evidence:**
```
is_coarse         — ... The slot uses this flag to
                  switch the status-bar message to the AI-15
                  "Preview — {label} — NNN ms" badge ...
```
But the slot in app.py:822-829 actually writes `"Preview — {surface.label}{hq_label} — {result.gen_ms:.0f} ms"` — `hq_label` is interpolated between `{label}` and `— NNN ms` when the HQ toggle is on (e.g. `"Preview — Enriques sextic (canonical, S₄ symmetry) [HQ] — 187 ms"`). The format string in the worker docstring omits `{hq_label}` and the `result.warning_text` ⚠-prefix path.
**Why it matters:** CONTEXT.md §8.19 documents the badge format as `"Preview — {label}{hq_label} — NNN ms"` (correct); render_worker.py's MeshResult docstring is the second canonical reference and should not drift from §8.19. A future maintainer reading render_worker.py expects the docstring to be the contract.
**Suggested fix:** Update the render_worker.py docstring to mirror CONTEXT.md §8.19's full format: `"Preview — {label}{hq_label} — NNN ms"` and add the optional warning-text prefix note.

### MEDIUM — CAND-12 stdout log line silently skipped for coarse renders

**Where:** `app.py:813-816` and the early `return` at `app.py:829`
**Evidence:** The slot's success path prints `print(f"[render] {surface.label}: {result.gen_ms:.0f} ms")` at line 813. The coarse branch (lines 822-829) returns *after* `_apply_domain_and_render` runs but the print line is BEFORE that — let me re-check. Reading lines 810-829:
```
self._raw_mesh = mesh
self._invalidate_clipped_mesh()
print(f"[render] {surface.label}: {result.gen_ms:.0f} ms")
self._apply_domain_and_render(reset_camera=self._inflight_reset_camera)
... [coarse branch] ...
if result.is_coarse:
    preview_msg = ...
    self.statusBar().showMessage(preview_msg)
    return
```
Correction: the print *does* fire for coarse — it's before the coarse-branch return. **Withdrawing this finding** — the print line is at app.py:813, before the coarse-branch return at app.py:829. The CAND-12 contract holds. (Keeping the entry as a self-noted false alarm rather than silently deleting it, so the rectifier knows what was checked and cleared.)

[NOTE: this finding is withdrawn after re-reading; the print line is on the coarse path too. No action needed.]

### MEDIUM — Coarse-LOD interaction with domain-clip mid-drag (mathematically subtle but not flagged in the brief)

**Where:** `app.py:_on_domain_changed` flow + the `_raw_mesh` write at app.py:810 inside the coarse branch
**Evidence:** A successful coarse render sets `self._raw_mesh = mesh` (the coarse mesh) before the coarse-branch check at line 822. Subsequent `_on_domain_changed` slides clip on this coarse mesh until a full result lands. Combined with the Preview badge's deliberate suppression of bbox/verts/faces, the AI-15 honesty is preserved on the badge — but the *clipped* mesh visible in the viewport is now a coarse mesh that the user might interact with (e.g., adjust domain radius while a coarse render is the latest).
**Why it matters:** The visible mesh during drag IS coarse, and that's the design intent — but the brief and CONTEXT.md §8.19 do not explicitly document that domain-clip operates on the coarse mesh until release. A future agent investigating "why does dragging the domain slider while parameter-sliding feel imprecise" needs this stitching documented.
**Suggested fix:** Add one sentence to CONTEXT.md §8.19 noting that the `_raw_mesh` cached during a coarse render IS the coarse mesh; domain clipping (AI-10 cache reuse) therefore operates on the coarse mesh until the next full-resolution result lands. No code change — this is a documentation gap on a real (intentional) behavior.

---

## Low findings (cosmetic / future iteration)

### LOW — Fermat coarse smoke test bound is loose

**Where:** `tests/test_coarse_n.py:233`
**Evidence:**
```
assert 1.5 < extent < 2.5, f"axis {axis} extent {extent} not near 2"
```
For Fermat at `c=1, alpha=beta=gamma=0`, the surface is x⁴+y⁴+z⁴=1, so each axis sits between -1 and +1 with vertices very close to those values; mesh axis extent should be ≈ 2.0 ± a small marching-cubes truncation. The current `[1.5, 2.5]` interval would accept a clearly-broken mesh at 1.6 (e.g., if a bug clipped to ≤0.8). A tighter `1.95 < extent < 2.05` would be a stronger regression guard.
**Why it matters:** Smoke tests are the canonical regression line for the coarse-n floors. A loose tolerance means the suite would not flag a moderate topology regression.
**Suggested fix:** Tighten to `1.95 < extent < 2.05`. Verify on the dev machine before pushing.

### LOW — `_pending_is_coarse` reset semantics could be belt-and-suspenders documented

**Where:** `app.py:221-228` (init) and `app.py:931-933` (catch-up reset)
**Evidence:** `_pending_is_coarse` is reset to True only inside `if self._pending_render:` in the slot's finally. I traced every transition and the field's value is correct in every scenario (the AND-identity guarantee holds because writes only happen inside `if self._computing:`). But the symmetry comment with `_pending_reset_camera` is documented; an explicit "this field stays at its last value when no catch-up fires, which is safe because all writes are inside `if self._computing:`" would help a future reader.
**Why it matters:** The AND-promote vs OR-promote pairing is one of the trickier bits of state machine logic in app.py. Defensive comments on the *invariants* (not just the truth table) help future agents avoid latent regressions.
**Suggested fix:** Add one-line invariant comment near the field init at app.py:221 explaining the "reset only on catch-up" choice. Optional.

### LOW — Belt-and-suspenders dispatch_mode test row is praiseworthy but unmotivated

**Where:** `tests/test_coarse_n.py:177` — `(_surf(typical_ms=39, coarse_n=80), True, "full")`
**Evidence:** The test deliberately constructs a Surface with BOTH `typical_ms=39` AND `coarse_n=80` to verify that the `typical_ms > 0` check (layer 1 of the AI-6 Hanson skip) fires first. This is praiseworthy — it tests layer 1 in isolation — but the registry never produces such a Surface today (Hanson has `coarse_n=0`).
**Why it matters:** The test row labels itself "belt-and-suspenders" but does not explain why exhaustively testing each AI-6 layer independently is worth the test budget. A one-sentence comment justifying it would help.
**Suggested fix:** Add inline comment: `# Layer-1 isolation: even if a future Hanson surface erroneously got coarse_n>0, dispatch_mode would still return "full" because typical_ms is checked first.`

---

## What was done well

- **AI-15 Preview-badge contract is correctly load-bearing.** The badge writes "Preview — {label}{hq_label} — NNN ms" with bbox/verts/faces deliberately suppressed (`app.py:822-829`), the rationale is documented in CONTEXT.md §8.19, app-invariants.md AI-15 is updated to record the Preview-badge as a math-honesty disclaimer, and the "Qt's QStatusBar.showMessage replaces — replacement IS the clear" semantic is correctly anchored. This is the right level of math-honesty discipline for transient previews.
- **AI-6 three-layer Hanson skip is genuinely defense-in-depth.** Layer 1 (`dispatch_mode` returns "full" for `typical_ms > 0`) is checked before `coarse_n`; layer 2 (Hanson `coarse_n=0` default in the registry) means even a bug-induced `coarse=True` call no-ops; layer 3 (`MeshWorker` is mode-agnostic) means the worker NEVER lowers `n` on its own. Each layer is independently testable and tested.
- **Stale-result discard correctly lives INSIDE the try block.** `app.py:781-789` — the `is_stale_result(result.generation, self._generation)` early return is inside the try/finally, so the `finally` cleanup (cursor restore, `_computing` clear, `_active_worker = None`, catch-up scheduling) fires on every exit. This is the e4 rectification (CONTEXT.md §8.18) preserved verbatim, which is exactly what the e4b implementer should have done.
- **`dispatch_mode` is extracted as a free function and tested Qt-free.** The 10-row parameter table at `tests/test_coarse_n.py:_DISPATCH_TABLE` covers None/Hanson/coarse-eligible/opt-out × in_drag={True,False}, the predicate is unit-testable under AI-2, and the AI-2 honesty caveat (the live coarse↔full state machine still needs a manual gate) is documented in CONTEXT.md §9.
- **AND-promote truth table is enumerated inline.** `app.py:654-662` walks each cell of the truth table (`coarse,coarse → True`, `coarse,full → False (full wins)`, `full,* → False (sticky)`); the "release after a drag burst never gets stuck rendering coarse forever" invariant is the right loud assertion.
- **The opt-out for `fano_two_quadrics` is documented with the right specificity.** The block comment at `surfaces.py:1247-1253` cites the ε-tube width versus voxel spacing trade-off and references the agent-a brief — a future tuner reading this knows exactly why this surface is the exception.
- **Tests verify both the dataclass default (`coarse_n: int = 0`) and the registry pinning** (`test_varieties_registry_coarse_n_matches_table` — every Surface checks against an expected literal; a typo in the registry would fail loudly).
- **The Kummer 16-octant symmetry test (`test_coarse_n_kummer_16_node_symmetry`) is the right topology signature.** The S₄ tetrahedral symmetry preserved at coarse n=100 is empirically verified by 8-octant counting with a 10 percent tolerance — exactly the kind of "topology-honest at the floor" assertion the brief promised.
- **The §8.20 workqueue caveat is honestly disclosed.** Numba's workqueue layer is documented as "production-safe under the e1/e4 `_computing` single-flight guard, but if single-flight is ever lifted the threading layer must change" — the right level of forward-looking honesty for a constraint that's latent today.
- **CONTEXT.md §9's manual-gate checklist is extended with the e4b-specific step** (drag Fermat slider, verify Preview badge, release, verify full base_msg with verts/faces/bbox). This is exactly the right substitution for a missing pytest-qt gate.

---

## Frontend UI/UX findings

Merged from the `milestone-frontend-ux-critic` pass (app.py touched). The
frontend critic found 0 CRITICAL / 1 HIGH / 4 MEDIUM / 3 LOW. No literal
overlap with the adversary findings — the frontend pass focused on the
user-facing message machinery; the adversary pass focused on dispatcher
correctness. The rectifier should treat each as independent.

### HIGH — Dispatch-time "Computing…" message doesn't attribute coarse mode

**Where:** `app.py:738` (dispatch path) + the busy-branch parallel at the `_computing` short-circuit
**Evidence:** Every coarse dispatch unconditionally calls `self.statusBar().showMessage(f"Computing {surface.label}{_hq_label}…")` — no coarse qualifier. The result-time message branches on `result.is_coarse` to write `"Preview — …"`. During a sustained drag burst (~25 ticks/s) the status bar oscillates between `"Computing Fermat quartic…"` and `"Preview — Fermat quartic — 41 ms"` for the *same* render mode — a flicker that undercuts the AI-15 disclosure the badge was built to provide.
**Why it matters:** AI-15 honesty is a user-visible disclosure (CONTEXT.md §8.19 + app-invariants AI-15). A researcher glancing at the status bar mid-drag may catch the "Computing" frame and assume the mesh is the in-flight full-res render — i.e. assume MORE fidelity than is actually on screen. Peer pattern: ParaView's "Interactive (preview)" label stays coarse-attributed across both phases of the same drag.
**Suggested fix:** Two-line change — interpolate a `_coarse_label = " (preview)"` (or "Computing preview — …") when `_is_coarse_active`, mirroring how `_hq_label` is threaded. The busy-branch path should read `self._pending_is_coarse` for symmetry.

### MEDIUM — Dwork-warning + Preview composite overflows QStatusBar's visible width

**Where:** `app.py` coarse-branch warning composite (line ~845)
**Evidence:** On a Dwork drag through ψ ≈ 1.0, `result.warning_text` is ~175 chars (`"ψ ≈ 1 is the (real) conifold point ... ; the displayed mesh is the smooth complement."`). Concatenated with `"Preview — Dwork pencil real slice (ψ-family) — 312 ms"` (~55 chars + ` | ` separator) the composite is ~233 chars — beyond QStatusBar's ~120-char visible window (CONTEXT.md §4.3). The full-result equivalent hoists bbox to the LEFT of the pipe; the coarse branch suppresses bbox (correct per AI-15) so there's no equivalent rescue — the trailing ` — NNN ms` token (half the badge's value) silently clips.
**Why it matters:** The Preview ms reading is one of the two pieces of information the badge contract guarantees (§8.19: `"Preview — {label} — NNN ms"`). Clipping it on the one drag scenario where the warning fires (Dwork ψ-slider crossing 1.0 — a researcher-relevant exploration) is the worst-case failure mode.
**Suggested fix:** (a) shorten the Dwork RuntimeWarning to ≤80 chars (move the geometric explanation to the docstring); or (b) hoist the badge to the LEFT of the pipe: `f"Preview — {label} — NNN ms  |  ⚠ {warning}"`. Option (a) is cleaner.

### MEDIUM — Per-surface tooltips don't mention the coarse-preview LOD

**Where:** `surfaces.py:SUBTYPE_TOOLTIPS` — the *absence* of a coarse-preview note
**Evidence:** The 9 opt-in implicit subtype tooltips describe the surface mathematically but say nothing about the new render-time behavior. A user hovering `"Fermat quartic"` reads the math; nothing about "renders at coarse n=80 during drag." The Preview badge is the ONLY surface where this fact lives — invisible to users who never look at the status bar.
**Why it matters:** Per the new app-invariants AI-15 line 170, "a new render-mode candidate that lacks a comparable user-visible fidelity disclosure is an AI-15 conflict." The badge satisfies it for status-bar-watchers but is structurally invisible to canvas+combo users. Mathematica `Manipulate` puts an analogous disclosure in `ControlActive`'s tooltip, not just transiently in the canvas.
**Suggested fix:** Add a single sentence at the bottom of each `VARIETY_TOOLTIPS` family entry (K3 / Enriques / CY3 / Fano) — lower-touch than 9 per-subtype edits and drift-resistant against `coarse_n` value changes.

### MEDIUM — `_pending_is_coarse` `True` AND-identity overloads two meanings

**Where:** `app.py:229` (init), `app.py:663` (AND-promote), `app.py:939` (post-clear reset)
**Evidence:** `True` as the AND-identity is mathematically correct but reads as "the pending render IS coarse" (it's actually "no pending request yet"). e4's mirror, `_pending_reset_camera`, uses `False` as OR-identity — the natural "no signal yet" sentinel — and needed no comment block. The triple-block truth-table comment is a smell that the data structure is doing two jobs at once.
**Why it matters:** Latent maintenance risk — if anyone ever flips the polarity (rename to `_pending_is_full`, the natural inversion), the identity flips from True to False and the queue-latest semantics silently invert.
**Suggested fix:** Rename to `_pending_render_is_full = False` so OR-identity False is the natural "no full request seen yet" sentinel — matches the e4 `_pending_reset_camera` pattern exactly. ~4 line touches.

### MEDIUM — Coarse-path error message inherits e4's empty-message fallback but loses the "preview" context

**Where:** `app.py` error branch in `_on_mesh_ready` (line ~794-806)
**Evidence:** A coarse render that raises produces the same `"Error: {msg}"` text as a full render — no `"Preview error"` qualifier, no indication the user was mid-drag. The user sees a transient `"Error: ..."` flash mid-drag, then the next successful coarse tick overwrites it — they lose the error trail entirely. AI-14 RuntimeWarning surfacing assumes a single, stable error display, but during drag the status bar is being overwritten ~25 Hz.
**Why it matters:** A coarse-only error (a future surface whose `coarse_n=20` violates its zero-set existence test but `n=100` does not) silently disappears as the next successful tick lands. Even today's stable surfaces could hit this if a parameter combination is degenerate at coarse n but valid at full.
**Suggested fix:** On the `result.is_coarse AND not result.ok` path, write `"Preview error — {msg}"` instead of `"Error: {msg}"`. Single-line conditional.

### LOW — Em-dash separator inconsistency: badge uses ` — ` vs base_msg's `  ·  `

**Where:** badge (`app.py:841-844`) vs base_msg (`app.py:896-900`)
**Evidence:** Badge uses U+2014 em-dash with single spaces; base_msg uses U+00B7 interpunct with double spaces. The visual transition cues the mode change — but two researchers reading both side-by-side may register two different message systems.
**Why it matters:** Cosmetic; the distinction is a benign visual cue. ParaView uses interpunct uniformly across both interactive and still-render messages.
**Suggested fix:** Either align (interpunct everywhere) or document the divergence. Status quo acceptable.

### LOW — `_inflight_is_coarse` is set but never read

**Where:** `app.py:216, 734`
**Evidence:** The instance variable is initialized + set at dispatch but the slot reads `result.is_coarse` (the worker self-describes), never `self._inflight_is_coarse`. The "mirror for defensive symmetry" comment is aspirational — the field has no consumer today.
**Why it matters:** A documented-as-defensive instance variable is a future debugging hint; an unused one is technical debt.
**Suggested fix:** Delete `_inflight_is_coarse` entirely — no consumer. (Alternative: refactor the slot to read it as source-of-truth and drop `is_coarse` from `MeshResult` — but the worker-self-description model is more consistent with the e4 architecture; deletion is cleaner.)

### LOW — Industry-comparison missing from milestone artifacts

**Where:** Implementation plan + CONTEXT.md §8.19
**Evidence:** The badge's *contract* is documented but no industry-comparison reference notes that Mathematica `ControlActive` (canvas shimmer) and ParaView "Interactive Render" (render-view label) are the peer patterns. Both peers locate the indicator AT THE RENDER VIEW, not in the status bar — AVC's status-bar approach is a deliberate divergence (the status bar already carries verts/faces/bbox/ms; the eye is trained on it).
**Why it matters:** Future maintainers and reviewers benefit from knowing the design is peer-validated and the divergence is intentional.
**Suggested fix:** Add a one-paragraph "Peer comparison" note to CONTEXT.md §8.19.

---

## Recommended rectification order

1. **Fix the HIGH HQ-coarse interaction (one-line guard in `_render_current` + test row).** Single root cause, single fix; cite CONTEXT.md §8.19 in the inline comment so the choice is institutional-memory-grade.
2. **Fix the MEDIUM stale doc references** (`surfaces.py:79`, `surfaces.py:1235` — rename `test_coarse_n_topology.py` to `test_coarse_n.py`). Two-line edit.
3. **Fix the MEDIUM MeshResult docstring** (`render_worker.py:95-103`) to mirror the full Preview-badge format with `{hq_label}` and the warning-text prefix path.
4. **Add the MEDIUM domain-clip documentation note to CONTEXT.md §8.19** (one sentence — domain-clip operates on the coarse `_raw_mesh` until release).
5. **LOWs are optional follow-ups** — tighten the Fermat smoke test bound, add the AND-promote invariant comment, justify the belt-and-suspenders test row.

---

*End of critique. Mandatory rectification: the HIGH HQ-coarse interaction (the only code finding) plus the doc-reference MEDIUMs. Auto-finding HIGH is informational only.*
