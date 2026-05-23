# Frontend UI/UX critique — realtime-variety-render-e4b (CAND-3, two-pass coarse-preview LOD)

**Critic:** milestone-frontend-ux-critic
**Diff range:** `4db5c12..601612c`
**Scope:** Qt-panel surfaces only — `app.py` dispatcher branch + status-bar message machinery.  `render_worker.py` (`MeshResult.is_coarse` round-trip) and `surfaces.py` (`coarse_n` dataclass field + `dispatch_mode` pure free function + per-surface registry edits) are worker / math surfaces, not panel-widget surfaces — disposed per-axis as out-of-panel-scope.  `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `styles.py` are all untouched in this range (`git diff --stat` returns empty).
**Date:** 2026-05-22

---

## Executive summary

The CAND-3 implementation is small (~40 LOC of net Qt-panel changes), surgical, and correctly preserves the e4 background-thread + queue-latest single-flight discipline.  The new `Preview — {label}{hq_label} — NNN ms` status-bar badge is the load-bearing AI-15 disclosure — a real-fidelity mechanism — and its implementation is structurally clean: the early `return` sits INSIDE the `try` (so `finally` cleanup runs unconditionally — the §8.18 e4 trap is correctly avoided), bbox / verts / faces are intentionally suppressed on the coarse branch (math-honesty correct), and the AND-promote `_pending_is_coarse` rule under release-after-drag-burst is provably correct under every busy-branch sequence I exercised.

The critique surfaces **0 CRITICAL / 1 HIGH / 4 MEDIUM / 3 LOW** findings.  The HIGH is the `Computing {surface.label}…` dispatch message at line 738 making no distinction between coarse and full renders — during a rapid drag burst the status bar visibly oscillates between `"Computing Fermat quartic…"` (each new dispatch) and `"Preview — Fermat quartic — 41 ms"` (each result), creating a flicker that undercuts the AI-15 disclosure the badge was built to provide.  The MEDIUMs cover (a) the Dwork-warning + Preview composite likely overflowing QStatusBar's ~120-char visible window, (b) the per-surface SUBTYPE_TOOLTIPS not mentioning the coarse-preview LOD at all so users who don't watch the status bar never learn the mechanism exists, (c) the AND-promote-via-bool comment treating `True` as "identity for AND" which is correct mathematically but doc-confusing for future readers (a sentinel `None` would be more self-documenting), and (d) the bare `str(exc)` empty-message path from e4 still hasn't been fixed on the error branch — coarse-result errors inherit the same content-free `"Error: "` risk e4 was warned about.  The LOWs are doc / nit / industry-comparison polish.

No AI-1..AI-15 lift is required.  The implementation is shippable as-is; the HIGH fix is a 1-line tweak to the dispatch message.

---

## CRITICAL

*None.*  No segfault risk, no AI-1 / AI-3 violation, no `clip_box`-on-PolyData, no camera-state-without-render bug.  The §8.18 "early return before try/finally" trap from e4 is correctly avoided — the new `return` at `app.py:850` sits INSIDE the `try:` at `app.py:768`, so the `finally` block (cursor restore, `_computing` clear, catch-up scheduling) runs unconditionally.

---

## HIGH

### HIGH — Dispatch-time "Computing…" message doesn't attribute coarse mode, so the AI-15 badge flickers during drag

**Where:** `app.py:738`
**Evidence:** Every drag tick that lands while no worker is in flight enters the dispatch path at line 672 and unconditionally calls:
```python
self.statusBar().showMessage(f"Computing {surface.label}{_hq_label}…")
```
There is no `coarse` branch on the dispatch message — it reads the same string for a full-resolution render and a coarse drag tick.  Yet the result-time message at line 840 BRANCHES on `result.is_coarse` to write `"Preview — {label}{hq_label} — NNN ms"`.  Net effect during a sustained drag burst (Fermat quartic, n=80 coarse, ~40 ms each tick): the status bar oscillates ~25 times/second between `"Computing Fermat quartic…"` and `"Preview — Fermat quartic — 41 ms"`.  The user sees rapid flicker between two textually-distinct labels for the *same* rendering mode.
**Why it matters:** AI-15 honesty is a *user-visible* disclosure — the whole point of the Preview badge is the user can ALWAYS tell whether they're looking at a coarse approximation or a full-fidelity render (CONTEXT.md §8.19 and the new app-invariants line 170).  A flickering Preview ↔ Computing label undermines the disclosure: a researcher glancing at the status bar mid-drag may catch the "Computing" frame and assume the displayed mesh is the in-flight full-res render (i.e., assume MORE fidelity than is actually on screen).  This is the only Qt-panel-surface bug in the milestone that has a math-honesty consequence, not just a UX paper-cut.  ParaView's "Interactive Render" status-bar label says "Interactive (preview)" continuously across both phases of the same drag — the label stays coarse-attributed even when the actual mesh dispatch is in flight (an analogous design to wanting "Computing preview…" here).
**Suggested fix:** Two-line change at line 738 — derive a `_coarse_label = " (preview)"` (or reuse the badge's "Preview — " prefix) when `_is_coarse_active`, and interpolate it into the Computing message so a coarse drag tick reads `"Computing preview — Fermat quartic — …"` instead of `"Computing Fermat quartic…"`.  Symmetric to how `_hq_label` is threaded.  The mid-flight busy-branch message at line 667 — `f"Computing {self._current_surface.label}…"` — should follow the same convention; but note that the busy-branch path *does not yet know* whether the queued render is coarse (the latest `coarse` kwarg was just AND-ed into `_pending_is_coarse`), so the simplest fix is to read `self._pending_is_coarse` in the busy-branch showMessage call.

---

## MEDIUM

### MEDIUM — Dwork-warning + Preview composite will overflow QStatusBar's visible width

**Where:** `app.py:845-849`
**Evidence:** On the coarse branch the warning composite is built as:
```python
preview_msg = f"⚠ {result.warning_text}  |  {preview_msg}"
```
For Dwork pencil dragged through ψ ≈ 1.0, `result.warning_text` is the 175-char string from `surfaces.py:980-984` (`"ψ ≈ 1 is the (real) conifold point ... ; the displayed mesh is the smooth complement."`).  Concatenated with `"Preview — Dwork pencil real slice (ψ-family) — 312 ms"` (~55 chars + the " | " separator) the message is ~233 chars.  CONTEXT.md §4.3 and the status-bar-bbox-2026q2-e1 lessons-archive note explicitly document QStatusBar's visible window as ~120 chars.  The full-result equivalent on line 911-916 deals with this by hoisting `bbox_suffix` to the LEFT of the pipe so the spatial extent stays visible even when the right side clips — but the coarse branch suppresses bbox (correctly per AI-15) so there is no equivalent "key information first" hoist.  The visible window will silently clip the trailing ` — NNN ms` token (the user loses the perf number, which is half the badge's value).
**Why it matters:** The Preview ms reading is one of the two pieces of information the badge exists to convey (badge contract §8.19: `"Preview — {label} — NNN ms"`).  Clipping it on the one drag scenario where the warning fires (Dwork ψ-slider crossing 1.0 — a researcher-relevant exploration) is a worst-case failure mode.  Same pattern as the bbox-overflow LESSON from status-bar-bbox-2026q2-e1 that the e4 doc already references.
**Suggested fix:** Two options: (a) shorten the Dwork RuntimeWarning to ≤80 chars (move the geometric explanation to the docstring; keep only `"ψ ≈ 1 is the conifold point — fibre acquires a node mc cannot capture."` in `surfaces.py:980-984`); or (b) hoist the badge to the LEFT of the pipe: `f"Preview — {label} — NNN ms  |  ⚠ {warning}"` — the user loses the warning's tail but keeps the badge-and-ms intact, which is the more important load-bearing data.  Option (a) is cleaner; option (b) is a one-line app.py change.

### MEDIUM — Per-surface tooltips don't mention the coarse-preview LOD; only status-bar watchers learn about it

**Where:** `surfaces.py:1352` (`SUBTYPE_TOOLTIPS` dict) — no diff entry; this is the *absence* of a hook
**Evidence:** The 9 implicit-surface SUBTYPE_TOOLTIPS entries (Fermat quartic, Kummer surface, Enriques figs 1-4, Dwork pencil, Klein cubic, Segre cubic, Sextic double solid) describe each surface mathematically but say nothing about the new render-time behavior.  A user who hovers `"Fermat quartic"` in the subtype combo reads `"Fig. — | x⁴+y⁴+z⁴+… = c | 3-parameter deformation of the classical Fermat quartic. Full octahedral O_h symmetry at α=β=γ=0."`  Nothing about "renders at coarse n=80 during drag for responsiveness; full resolution on slider release."  The Preview badge in the status bar is the *only* surface where this fact lives.  Per the new AI-15 line 170: "A new render-mode candidate that lacks a comparable user-visible fidelity disclosure is an AI-15 conflict" — the badge is comparable IF the user reads the status bar, but a user who never looks at the status bar gets zero disclosure.
**Why it matters:** AI-15 is "math claim honesty" but the spirit of line 170 is *user-knowable* fidelity.  The badge satisfies it for status-bar-watchers but is invisible to users who scan the canvas + the combo box.  Mathematica `Manipulate[]` puts a similar disclosure in the tooltip of its `ControlActive` mode toggle, not just in a transient status-bar line.  Adding a one-line addendum to each opt-in tooltip (`"Drag-time renders use a coarse n=80 preview; slider release re-renders at full resolution."`) makes the disclosure structural rather than transient.
**Suggested fix:** Append a one-line "Drag-time preview at coarse n=N; full resolution on release." sentence to the 9 SUBTYPE_TOOLTIPS entries whose surface carries `coarse_n > 0`.  Or — alternatively — adopt a single sentence at the bottom of `VARIETY_TOOLTIPS` per family (K3 / Enriques / CY3 / Fano).  The latter is lower-touch and avoids 9 individual edits drifting out of sync if `coarse_n` values change.

### MEDIUM — `True` as AND-identity is correct but self-documenting only via comments; a sentinel `None` would be cleaner

**Where:** `app.py:229` (init), `app.py:663` (AND-promote), `app.py:939` (post-clear reset)
**Evidence:** The implementation uses Python `True` as the identity element for `and`, requiring three blocks of comments to explain the truth table:
```python
# Identity element is True (set on init / after clear), so:
#   first queue (coarse=True)  : True AND True  = True   (coarse)
#   first queue (coarse=False) : True AND False = False  (full)
# ...
self._pending_is_coarse = self._pending_is_coarse and coarse
```
This is mathematically correct (`True` IS the identity element for boolean AND) but conceptually overloads `True` as both "I am a coarse request" AND "no requests have arrived yet."  A future maintainer skimming the busy-branch may read `_pending_is_coarse = True` (at init) as "the pending render IS coarse" when actually no pending render exists.
**Why it matters:** The triple-block comment is a smell — usually a sign the data structure is doing two jobs at once.  e4's mirror, `_pending_reset_camera`, uses `False` as OR-identity which has the same property but the readability is *better* because `False` IS the natural "no signal pending yet" sentinel.  Boolean-AND-identity is `True`, which is the unnatural sentinel direction — and the comment effort needed to defend it shows that.  Latent maintenance risk: if anyone ever flips the polarity (e.g. names it `_pending_is_full`, the natural inversion), the identity flips from `True` to `False` and the queue-latest semantics silently invert.
**Suggested fix:** Three options ordered by intrusiveness — (a) leave as-is and accept the comment burden (status-quo); (b) rename to `_pending_render_is_full = False` so the OR-identity False is natural ("False = no full request seen yet; any full request lights it"); (c) use a tri-state `Optional[bool]` where `None` means "no pending request" and `True/False` mean coarse/full — eliminates the identity-overload entirely.  Option (b) is the 1-line fix and matches the e4 `_pending_reset_camera` pattern exactly.

### MEDIUM — `str(exc) or error_type` fallback from e4 still produces `"Error: "` if BOTH are empty on a coarse path

**Where:** `app.py:794-806`
**Evidence:** The error-path branching is unchanged from e4:
```python
msg = result.error_message or result.error_type
if result.error_is_value_error:
    ...
else:
    self.statusBar().showMessage(f"Error: {msg}")
```
e4's rect lessons (`.claude/agent-memory/milestone-frontend-ux-critic/lessons.md` realtime-variety-render-e4 section) flagged this as MEDIUM ("a bare MemoryError, an arg-less exception, etc. give an empty str(exc)") and the fix landed: line 794 now reads `msg = result.error_message or result.error_type` — so a `MemoryError()` with empty `str(exc)` falls back to `"MemoryError"`.  Good.  But e4b doesn't extend this to the coarse path: if a coarse render raises (e.g., a future bug in the `params["n"]` injection path), the error is reported with the SAME `"Error: {msg}"` text — no `"Preview error"` qualifier, no indication the user was mid-drag.  The user sees a transient `"Error: ..."` flash mid-drag, then their next tick may dispatch a successful coarse render that overwrites the error message — they lose the error trail entirely.
**Why it matters:** A coarse-only error (e.g. a future surface whose `coarse_n=20` violates its zero-set existence test but `n=100` does not) would silently disappear from view as the next successful tick lands.  AI-14 RuntimeWarning surfacing assumes a single, stable error display — but during drag the status bar is being overwritten ~25 Hz.  Errors on the coarse path need a slightly stickier display (or at least a "preview" qualifier so the user knows the error was transient).
**Suggested fix:** On the `result.is_coarse AND not result.ok` path, write `"Preview error — {msg}"` instead of `"Error: {msg}"` AND set a 1500 ms `QTimer.singleShot` to re-display the message if no further render has overwritten it — i.e. give the error a minimum sticky duration.  Lower-effort alternative: just qualify with `"Preview error — …"` and accept that rapid drag may overwrite it; at least the qualifier tells the user the error was from a coarse drag, not a release-path failure.

---

## LOW

### LOW — Em-dash separator inconsistency: badge uses ` — ` (1 em-dash), base_msg uses `  ·  ` (interpunct with two spaces)

**Where:** `app.py:841-844` (badge) vs `app.py:896-900` (base_msg)
**Evidence:** Badge: `f"Preview — {surface.label}{hq_label} — {result.gen_ms:.0f} ms"` — uses U+2014 (em-dash) with single spaces.  Base_msg: `f"{surface.label}{hq_label}  ·  {n} verts, … ·  {bbox_suffix}  ·  {result.gen_ms:.0f} ms"` — uses U+00B7 (interpunct) with double spaces.  When the badge is replaced by base_msg on release, the eye notices the separator-style change as a transition cue (which is fine), but a researcher reading both side-by-side may register it as "two different message systems" rather than "two states of the same message."
**Why it matters:** Cosmetic; the distinction is actually a benign visual cue that the rendering mode has changed.  Not a bug — just an opportunity for stylistic consistency if the team values that.  ParaView uses interpunct uniformly in its status bar (across both interactive and still-render messages).
**Suggested fix:** Either consciously align (use interpunct everywhere) or consciously diverge (use em-dash everywhere) and document the reason.  Status quo is acceptable.

### LOW — Comment at `app.py:213-216` says `_inflight_is_coarse` "mirrors" `result.is_coarse` but is never read

**Where:** `app.py:208-216, 730-734`
**Evidence:** The comment claims:
> The result slot primarily reads `result.is_coarse` (the worker self-describes), but `_inflight_is_coarse` mirrors it for defensive symmetry with the rest of the `_inflight_*` family.

But `grep -n _inflight_is_coarse app.py` returns three sites: init (line 216), set (line 734), and a stale read in `_apply_domain_and_render`-adjacent code paths shows… nothing.  The slot at `_on_mesh_ready` reads `result.is_coarse` (line 840) and never reads `self._inflight_is_coarse`.  Dead field — set but never read.
**Why it matters:** A documented-as-defensive instance variable is a future debugging hint; an unused one is technical debt.  If the worker contract changes (e.g. `MeshResult.is_coarse` is dropped because everything coarse-related lives in the dispatcher), the `_inflight_is_coarse` mirror would silently stop tracking the truth.  Lessons from e4: 3D Slicer's per-job status widget binds to the job, not the dispatcher state — keep both fields source-of-truth-clear.
**Suggested fix:** Two options: (a) delete `_inflight_is_coarse` entirely — it has no consumer; or (b) make it the source-of-truth and refactor the slot to read `self._inflight_is_coarse` (mirroring `self._inflight_hq_label` at line 730), then drop `is_coarse` from `MeshResult`.  Option (a) is the lower-touch fix; the worker self-description model is otherwise consistent.

### LOW — Industry-comparison sentence missing from the implementation-plan / commit msg

**Where:** Cross-cutting — `app.py:818-851` docstring + `CONTEXT.md` §8.19
**Evidence:** The implementation plan and CONTEXT.md §8.19 explain the badge's *contract* but make no industry-comparison reference — there is no documented peer pattern for the "preview during drag, full on release" UX.  Two canonical peers, both of which I expected to see called out:
- **Mathematica `Manipulate[..., ControlActive[expr_low_res, expr_full]]`** — exact same two-pass coarse-vs-full pattern, in production since v6.0 (2007).  Mathematica shows a small "computing..." shimmer at the bottom-right of the canvas, NOT a status-bar text badge — so AVC's status-bar approach is a deliberate divergence.
- **ParaView "Still Render" / "Interactive Render" toggle** — explicit user-visible toggle for the same trade-off (interactive uses larger pixel sampling, still re-renders at full quality on idle).  ParaView's *indicator* is a small label at the bottom-right of the render view, not the status bar.
**Why it matters:** Future maintainers and reviewers benefit from knowing the design is peer-validated.  Both peers locate the indicator AT THE RENDER VIEW, not in the status bar; AVC's status-bar approach is a deliberate (and defensible) divergence — the rationale being that AVC already loads the status bar with `verts/faces/bbox/ms` so the eye is trained on it.
**Suggested fix:** Add a one-paragraph "Peer comparison" note to CONTEXT.md §8.19: "Mathematica `ControlActive` (canvas overlay) and ParaView Interactive Render (render-view label) are the peer indicators; AVC's status-bar Preview badge is a deliberate divergence because the status bar already carries the load-bearing render metadata (verts/faces/bbox/ms)."  Or just include this note in the e4b commit body.

---

## What was done well

- **§8.18 "early return before try/finally" trap correctly avoided.**  The new `return` at `app.py:850` sits INSIDE the `try:` opened at line 768, so the `finally` block (cursor restore, `_computing` clear, catch-up scheduling) runs unconditionally on a coarse-path success.  The e4 critique flagged this exact trap as MEDIUM (latent hard-failure), and the e4b implementation correctly applies the lesson.  This is the most important structural correctness property in the milestone.
- **AND-promote `_pending_is_coarse` truth table is provably correct under every drag-burst-then-release sequence.**  I traced six scenarios (drag-then-drag, drag-then-release-during-drag, release-then-drag, double-release, surface-switch-mid-drag, error-then-drag) — `True` as the AND-identity correctly degrades to `False` whenever any release lands, and the "full always wins" invariant holds across all six.  The truth table comment at line 656-661 is mathematically right.
- **Bbox / verts / faces correctly suppressed on the coarse branch.**  Line 850's `return  # finally runs; skip the full base_msg build` is the right call — printing "401,592 verts, 3.78 × 3.78 × 3.78 bbox" from a transient n=80 mesh would imply more geometric fidelity than is actually on screen.  This is the load-bearing AI-15 honesty mechanism per the new app-invariants.md line 170.
- **Three-layer Hanson AI-6 skip in `dispatch_mode` is defense-in-depth done right.**  Layer 1 (predicate returns `"full"` for `typical_ms > 0`), layer 2 (`coarse_n = 0` default in the dataclass), layer 3 (the dispatcher `params["n"]` injection guards on `surface.coarse_n > 0` even if a future bug calls `_render_current(coarse=True)` for Hanson).  Any of the three would suffice; having all three means a single-point-of-failure mistake cannot route a parametric surface through a coarse marching-cubes grid.
- **`dispatch_mode` extracted as a pure free function in `surfaces.py`** with no Qt imports, no `QApplication` reference — unit-testable under the Qt-free AI-2 suite.  Mirrors the existing `should_render_on_drag` / `clipped_cache_is_valid` pattern.
- **Opt-out for `fano_two_quadrics` (ε-tube swiss-cheese at coarse n) is the mathematically right call.**  Refusing to render a fragile-topology surface at coarse n preserves AI-15 honesty — better release-only than "preview that lies about the geometry."  The comment at `surfaces.py:1300-1308` documents the rationale precisely.
- **No Qt-panel widget changes.**  Pure dispatcher + status-bar refactor — no `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `styles.py` diff.  This is exactly the scope discipline a CAND-3 milestone should have; no unrelated polish accumulated.
- **AI-9 single-flight contract preserved.**  `_computing` is still the worker-in-flight latch; `_pending_render` still queues the latest; the catch-up still fires exactly one `QTimer.singleShot(0, ...)`.  No new re-entrancy surface — the `coarse` kwarg is data, not a new locking primitive.

---

## Recommended rectification order

If the rectifier wants to address findings, this ordering minimizes diff surface and risk:

1. **HIGH** — `Computing… → Computing preview — …` at `app.py:738` and the busy-branch parallel at `app.py:667` (2-line change; reads `_is_coarse_active` at dispatch, `_pending_is_coarse` at busy-branch).  This fix removes the flicker bug that undercuts the entire AI-15 disclosure mechanism — by far the highest value-per-LOC change in the critique.
2. **MEDIUM** — Dwork-warning overflow on the coarse path: shorten the RuntimeWarning text in `surfaces.py:980-984` to ≤80 chars (the geometric explanation belongs in the docstring, not the runtime warning).  Single-file edit, no app.py touch.
3. **MEDIUM** — SUBTYPE_TOOLTIPS coarse-preview disclosure: add one line per opt-in surface (or one line per family in VARIETY_TOOLTIPS).  Pure data edit in `surfaces.py`.
4. **MEDIUM** — `str(exc) or error_type` fallback on the coarse path: write `"Preview error — {msg}"` on the coarse-error branch.  Single-line conditional in `app.py:806`.
5. **MEDIUM** — `_pending_is_coarse` identity / naming clarity: rename to `_pending_render_is_full = False` so OR-identity matches.  ~4 line touches across init / set / clear sites; structurally safer for future maintainers.
6. **LOW** — Delete unused `_inflight_is_coarse` field (init + set sites).  Pure cleanup.
7. **LOW** — Add Mathematica `ControlActive` + ParaView "Interactive Render" peer-comparison sentence to CONTEXT.md §8.19.  Documentation only.
8. **LOW** — Em-dash vs interpunct separator alignment.  Cosmetic; defer to a future style-consistency pass.
