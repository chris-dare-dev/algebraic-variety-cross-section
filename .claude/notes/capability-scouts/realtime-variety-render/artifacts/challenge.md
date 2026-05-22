# Challenge — realtime-variety-render

**Role:** CHALLENGER (Phase 3)
**Date:** 2026-05-22
**Inputs:** synthesis.md (13 candidates), CONTEXT.md, app-invariants.md AI-1..AI-15, critique-format.md, requirements.txt, 5 survey briefs
**Method:** 10-axis adversarial evaluation per candidate

---

## 1. Executive Summary

13 candidates evaluated. **0 BLOCKERs, 3 MAJORs, 4 MINORs, 6 NONEs.** No candidate is an AI-1-through-AI-15 hard conflict that requires killing; the catalog is well-scoped. The two dominant objection themes are **(1) effort honesty on CAND-4**: the synthesis sizes it at L, which is itself an undercount once macOS Apple Silicon arm64 threading risk, the pyvistaqt/PySide6≥6.10 hang (issue #793), and the VTK SMP GC crash report (VTK GitLab #18782) are folded in — CAND-4 should be treated as L-with-mandatory-spike, not a straight L; and **(2) redundancy collapse of CAND-10**: field sub-expression caching is a bespoke M-effort item that Numba (CAND-2) makes redundant if CAND-2 lands first, and the synthesis itself acknowledges the overlap without drawing a firm conclusion — the challenger does: demote CAND-10 to a conditional parking lot unless CAND-2 is deprioritized.

---

## 2. BLOCKER Findings

*None.* No candidate violates a non-negotiable AI invariant in a way that requires dropping or fundamental architectural replacement. The GPU isosurfacing pattern and mesh interpolation are correctly parked by the synthesis and are not in the catalog.

---

## 3. MAJOR Findings

### MAJOR — CAND-4 / Background-thread mesh-generation worker

**Objections:**

- **Effort honesty (axis 8):** The synthesis sizes CAND-4 as L. That is itself optimistic when macOS threading risk is fully priced in. The synthesis flags pyvistaqt issue #793 (PySide6 ≥ 6.10 hang on macOS) but does not propagate it into the effort rating. The requirements pin is `PySide6 >=6.6,<7` — PySide6 6.10 is *inside that range*, meaning the hang is a live risk on the current pinned range, not a hypothetical. A mandatory spike to (a) reproduce the issue on the development machine, (b) determine whether tightening to `PySide6 <6.10` is safe, and (c) confirm VTK+QThread safety on arm64 adds 1–3 days before the main L work begins. CAND-4 is realistically L+ or XL in total elapsed calendar time on a single-developer cadence.

- **macOS Qt+VTK threading risk (axis 7):** Desktop-platform scout C-9 cites VTK GitLab issue #18782 (2024): occasional crashes under heavy SMP on macOS when the Python GC fires concurrently on a VTK `vtkObjectBase` object. The synthesis does not mention this crash report. Mitigation requires retaining explicit Python references to all output meshes until the GUI-thread callback consumes them — a non-obvious discipline that must be part of the implementation brief, not discovered post-merge.

- **AI-2 test impact (axis 4):** Threading workers that carry `pv.PolyData` across a signal boundary require non-trivial test coverage for the cancel/resubmit path, the stale-job guard, and the GIL-release behavior. All of these tests require a live `QApplication` (they test signal emission and slot invocation). AI-2 prohibits pytest-qt until the macOS Qt+VTK offscreen segfault is addressed. Concretely: the worker lifecycle logic cannot be covered by the existing test suite. This leaves a regression surface with no automated guard. The synthesis doesn't mention this gap.

- **Value density (axis 9):** CAND-4 is genuinely the architectural unlock — the synthesis is correct that everything else builds on it. The objection here is not to ship it, but to treat it honestly as "spike first, then implement" rather than a straight L.

**Suggested scope adjustment (v0/v1 cut-line):** v0 = spike (1–2 days): reproduce pyvistaqt #793 on the dev machine, tighten PySide6 pin if needed, confirm VTK+QThread safety with a minimal off-screen test (pure `pv.PolyData` round-trip via signal, no plotter). v1 = full implementation: `QRunnable` worker + signal delivery, cancel/resubmit, GUI-thread render boundary. Do not attempt v1 without passing the v0 spike.

---

### MAJOR — CAND-3 / Two-pass coarse-preview LOD

**Objections:**

- **AI-15 honesty — disclaimer adequacy (axis 2 and axis 1):** The synthesis correctly mandates a "Preview — coarse resolution; true surface on release" status-bar badge as mandatory per AI-15. However, it leaves the wording and trigger logic unspecified enough that a developer implementing CAND-3 could reasonably ship without the disclaimer, or with a disclaimer that clears too early (before the full-res render completes). The synthesis says this is "mandatory" but defers the wording to a v2. The challenger upgrades this: the disclaimer wording and hide-logic must be defined as part of the v0 spec, not deferred. Specifically, the badge must persist until the full-resolution mesh is confirmed received by `_apply_domain_and_render`, not cleared on the coarse preview render completing. An "auto-hide on release" pattern that hides before the full-res render arrives would be an AI-15 violation. This is an underspecified acceptance criterion, not a fatal flaw — hence MAJOR not BLOCKER.

- **Sequencing dependency is strict, not soft (axis 10):** The synthesis flags that CAND-3 "depends on CAND-4" and is a "downstream candidate." This is correct but understates the coupling. Without CAND-4, a coarse render on the GUI thread still blocks the slider for ~15–55 ms (see adversary §8.4: n=80 ~15 ms, n=120 ~55 ms). At 80 ms of debounce (CAND-6), a 55 ms synchronous coarse render fires back-to-back with almost no dead time — but it *still blocks the GUI thread*. This means CAND-3 without CAND-4 produces a slider that visually stutters at 55 ms intervals rather than the current 650+ ms intervals. That is an improvement, but the synthesis presents CAND-3 as delivering "a continuously-moving surface during drag" — which is only true if CAND-4 is also in place. The synthesis's DAG `CAND-12 → {CAND-4, 5, 6} → CAND-3` already encodes this, but the CAND-3 description does not make the dependency hard enough.

- **Topology misrepresentation floor is unknown (axis 2):** The synthesis acknowledges that n=80 "may merge Kummer nodes / miss the Dwork conifold" and lists the coarse-n floor as an open question. The adversary brief §8.4 gives n=80 ~6,000 verts for Fermat quartic — but gives no data for Kummer (16 nodes) or Enriques canonical sextic (400K-vert full-res mesh). Before CAND-3 can ship honestly, the minimum n at which Kummer's 16 nodes remain visually distinct needs a one-time measurement. This is a per-surface characterization task, not a blocker, but it must happen before merging.

**Suggested scope adjustment:** v0 spec must include: (a) disclaimer wording + trigger logic (show on coarse-preview start, hide only after full-res `_apply_domain_and_render` completes); (b) per-surface coarse-n floor table driven by an off-screen n-sweep comparison; (c) coarse path disabled for Hanson parametric surfaces (they don't need it per CAND-8 — AI-6 separation is already clean).

---

### MAJOR — CAND-2 / Numba JIT-compile the implicit-field evaluation kernel

**Objections:**

- **Effort honesty (axis 8):** The synthesis sizes CAND-2 as M. This is borderline. The synthesis itself notes "Numba's NumPy subset may force restructuring vectorized expressions into explicit loops — per-generator effort varies (degree-6 Enriques is the heaviest)." The adversary brief confirms the Enriques canonical sextic field evaluation is 305 ms (29% of 1.056 s total) and is a degree-6 polynomial with product terms that include `lam0 * x²y²z²` — i.e., a 6-way mixed monomial that Numba can fuse but the restructuring from NumPy broadcasting to explicit `prange` loops is non-trivial for the developer to verify correct. There are 8 distinct implicit generators in `surfaces.py` (Fermat, Kummer, 4 Enriques figures, Dwork, plus any future additions). Each needs a separate `@njit` kernel. Per-generator work × 8 = M effort, but the risk of introducing subtle field-evaluation errors (wrong exponent, wrong variable assignment) on the degree-6 surfaces is HIGH. The existing smoke tests in `tests/test_mesh_generators.py` only check that the output is a non-empty PolyData and that vertex counts are in expected ranges — they do not compare field values numerically. A Numba kernel with a transcription error could produce a visually plausible but mathematically wrong surface (AI-15 violation) and the tests would not catch it.

- **First-call JIT latency UX risk (axis 5):** The synthesis lists first-call latency management as an open question and sketches a startup warm-up. The risk: if warm-up fires during app startup and each of the 8 generators compiles for 200–400 ms, that is 1.6–3.2 s of additional startup time before the window appears. `cache=True` mitigates on subsequent launches but the first-launch experience is poor. The synthesis does not specify the warm-up sequencing (eager on import vs lazy on first surface select vs background thread at startup). This is a UX-visible risk that needs a resolution before implementation.

- **Test coverage gap (axis 4):** Numba JIT'd functions are Qt-free and testable (no AI-2 conflict) but the current smoke tests do not perform numerical field-value spot-checks. A regression guard for CAND-2 should add per-generator algebraic spot-checks (evaluate field at known point, compare to analytic value) to `tests/test_mesh_generators.py`. This is additional test work not mentioned in the synthesis.

- **Apple-Silicon `parallel=True` threading-layer stability (axis 7):** The oss-trends brief confirms `workqueue` is the safest fallback on macOS without an explicit OpenMP runtime, but notes that `tbb` is the default. An unguarded `@njit(parallel=True)` that silently picks the TBB layer may interact poorly with the same VTK SMP threading described in CAND-4's risk. The implementation brief should specify `numba.set_num_threads(N)` or explicitly request the `workqueue` layer on macOS.

**Suggested scope adjustment:** v0: implement `@njit` for the two highest-cost generators only (Fermat quartic + Enriques canonical sextic, together accounting for 460 ms of the worst-case budget), add numerical spot-check tests for those two generators, confirm startup warm-up adds <500 ms total, verify on macOS arm64 with `workqueue` layer. v1: extend to remaining 6 generators.

---

## 4. MINOR Findings

### MINOR — CAND-1 / Replace scikit-image marching cubes with VTK Flying Edges

**Objections:**

- **Normal quality regression — disclosure gap (axis 3):** The synthesis correctly notes that Flying Edges does not return scikit-image's analytic gradient normals. CONTEXT.md §3 explicitly states "Gradient-based normals from marching_cubes are far smoother than face-averaged ones near high-curvature regions" — this is a documented quality rationale, not an incidental detail. The synthesis notes this as a "minor shading-quality change" but does not specify which surfaces are most affected. Enriques canonical sextic (400K faces) and Kummer surface (192K faces) have the most high-curvature regions. The Challenger is not blocking on this — Taubin smoothing post-Flying Edges produces acceptable normals — but the acceptance criterion should include an off-screen visual comparison on Kummer and Enriques sextic before merging to confirm "minor" is accurate in practice.

- **SMP speedup on macOS Apple Silicon is uncertain (axis 5):** The synthesis correctly flags this as an open question but the competitive brief's claim of "1–2 orders of magnitude faster even in single-thread mode" is a Kitware benchmark on an Intel x86 dataset (CT-Angio), not on Apple Silicon with the STDThread backend. The oss-trends brief's more cautious "2–4× single-thread" is the right calibration. CAND-12 (timing telemetry) is the correct prerequisite for knowing the actual speedup — CAND-1 should be measured with CAND-12 in place before advertising a speedup claim.

**Suggested scope adjustment:** Implement as described; add visual comparison criterion for Kummer/Enriques to the acceptance checklist; measure speedup with CAND-12 before updating CONTEXT.md's informal "~0.5 s" estimate.

---

### MINOR — CAND-7 / LRU parameter-tuple mesh cache

**Objections:**

- **Rounding precision is user-visible (axis 3):** The synthesis flags the key-rounding precision as an open question. This is underspecified and has a subtle failure mode: if the rounding precision is too coarse (e.g., 1 decimal place for a slider with step=0.01), the cache may return a mesh computed at `c=1.0` when the slider is at `c=1.04` — a silent approximation that violates AI-15 (the rendered surface does not correspond to the displayed parameter). The key must be formed from values rounded to the slider's own `ParamSpec.step` precision, not an arbitrary fixed decimal count. The `ParamSpec` already has `step` — use it.

- **Memory cap sizing (axis 8):** The synthesis proposes 8–16 entries at ~50–160 MB. The adversary §8.1 timing table shows Enriques canonical sextic is ~400K verts, Fermat quartic at large bounds is ~343K verts. A `pv.PolyData` at 400K verts / 800K faces is approximately 50–80 MB. 16 entries of that size = 800 MB–1.3 GB. On a 16 GB MacBook that is not catastrophic but may trigger memory pressure on lower-end machines. A per-entry size gate (evict if total cache > 200 MB) is safer than a flat entry count.

- **Thread safety on CAND-4 arrival (axis 10):** The synthesis notes "if CAND-4 lands, the worker writes results back on the main thread only (no cross-thread cache writes)." This is correct — but only if the worker is disciplined about it. The implementation brief for CAND-7 should explicitly state that `self._mesh_cache` is only read/written on the GUI thread and that the CAND-4 worker must not write to it directly.

**Suggested scope adjustment:** Use `ParamSpec.step`-derived rounding for cache key precision. Implement a total-size eviction gate (not just entry count). Document the GUI-thread-only write discipline in the implementation comment.

---

### MINOR — CAND-8 / Fast-pipeline differentiation for Hanson surfaces

**Objections:**

- **AI-8 frozen-dataclass footprint (axis 1):** The synthesis proposes adding `fast: bool = False` to `Surface`. `Surface` is `@dataclass` (not frozen) but `ParamSpec` is `@dataclass(frozen=True)`. The field addition to `Surface` is clean (it is not frozen). However, the synthesis notes this as an open question referencing the `recommends_backface_culling` discussion. This prior addition is not visible in the current `CONTEXT.md` or `app-invariants.md`, so the challenger cannot confirm the pattern is established. If the `Surface` dataclass has other fields added post-initial-definition, the prior art exists. If not, this is the first field addition and should follow the same validation as the one mentioned. The effort is genuinely XS once this is confirmed — the concern is non-existent if the `recommends_backface_culling` addition is already in `surfaces.py`.

- **`fast: bool` is fragile as surfaces get added (axis 9):** A `fast: bool` flag with no quantitative threshold will drift: a future Hanson variant that takes 200 ms (not fast for continuous drag) could be mislabeled `fast=True` by a developer who assumes all parametric surfaces are fast. `typical_ms: int = 0` (where 0 = "unmeasured") is slightly more honest. The synthesis already offers this alternative and it pairs naturally with CAND-12 (telemetry).

**Suggested scope adjustment:** Confirm the `Surface` dataclass field-addition pattern against `surfaces.py` before implementation. Prefer `typical_ms: int = 0` over `fast: bool` so the threshold is explicit.

---

### MINOR — CAND-9 / In-place mesh update via `mapper.SetInputData`

**Objections:**

- **Value density conditional on CAND-3+CAND-4 (axis 9):** The synthesis already notes that CAND-9 only helps within a single LOD level — coarse↔full LOD swaps always differ in vertex count, so the in-place path fires only for small parameter perturbations *at the same LOD level*. Without CAND-3+CAND-4, there is only one LOD level and the vertex count changes on every parameter update (different `n` → different extraction) unless the resolution is fixed. The adversary §8.5 confirms `add_mesh` costs only 9 ms — the in-place save is at most 9 ms per frame. At 80 ms debounce intervals, this is <11% of the frame budget. The Challenger recommends deferring CAND-9 until CAND-3 and CAND-4 are in place, at which point its actual win rate (fraction of frames where vertex count matches) can be measured.

- **`actor.mapper.SetInputData` API stability in PyVista (axis 3):** PyVista's public API for in-place mesh update is not formally documented in the stable API surface — it relies on accessing `actor.mapper` as a `vtkPolyDataMapper` and calling VTK's C++ `SetInputData`. This works in current PyVista 0.46–0.48 (as confirmed by PyVista's own animation examples) but is a private VTK binding that could change without a PyVista semver bump. A guard like `if hasattr(self._actor, 'mapper') and hasattr(self._actor.mapper, 'SetInputData')` with a fallback to the full remove+add path is required.

**Suggested scope adjustment:** Defer to a v1 milestone after CAND-3+CAND-4. Add an API guard with fallback. Before implementing, measure what fraction of real parameter-drag sequences produce same-vertex-count consecutive meshes (CAND-12 telemetry + CAND-3 LOD in place).

---

## 5. Clean Candidates (NONE)

The following candidates survive all 10 challenger axes without objection. They are well-specified, appropriately sized, and have no AI conflicts or material costs not surfaced by the synthesis.

- **CAND-5** — Re-entrancy guard drop → queue-latest. XS, no AI conflict, ~2-line change, well-specified. Correctness fix that ships standalone.
- **CAND-6** — Debounce slider/grid `valueChanged`. S, no AI conflict, QTimer form requires no new dep. The superqt option (BSD-3-Clause) is acceptable once superqt is pulled for CAND-4; hand-rolled QTimer is preferable if CAND-4 is deferred.
- **CAND-10** — Field sub-expression cache. *Conditional* NONE: if CAND-2 (Numba) is on the roadmap and lands first, CAND-10 is redundant and should be dropped (the synthesis acknowledges this; see §6 cross-cutting concern #1). NONE only if CAND-2 is deprioritized — see §6.
- **CAND-11** — Clipped-mesh cache. XS, no AI conflict, natural extension of the existing AI-10 single-slot cache. The adversary M-4 finding is well-specified.
- **CAND-12** — Render-pipeline timing instrumentation. XS, no AI conflict, foundational for every other candidate's before/after claim. Pure telemetry.
- **CAND-13** — Grid-resolution-cap hygiene. XS, no AI conflict. The adversary L-1/L-2/L-3 findings are well-specified. The comment at `surfaces.py:223` already acknowledges this as a tuning task ("~1 s" comment is now wrong).

---

## 6. Cross-Cutting Concerns

### CC-1 — CAND-10 redundancy with CAND-2 (Numba) — resolve the parking-lot ambiguity

The synthesis notes the overlap but defers to the challenger. The challenger's verdict: **CAND-10 is a conditional parking-lot item.** If CAND-2 is in the Now-lane (recommended), CAND-10 should be explicitly marked "do not implement unless CAND-2 is abandoned." CAND-10 is M effort, covers only the field-eval step for surfaces that factor additively (not all do), and requires per-generator bespoke work that becomes dead code the moment CAND-2 lands. The sequencing DAG should read `CAND-2 → (park CAND-10)`.

If CAND-2 is deprioritized (e.g., Numba arm64 threading layer proves unstable on the target hardware), CAND-10 is a viable fallback — but it should not be started concurrently with CAND-2.

### CC-2 — PySide6 pin is currently too permissive for CAND-4

The current requirements pin is `PySide6 >=6.6,<7`. The oss-trends brief recommends tightening to `<6.10` until pyvistaqt issue #793 is resolved. The synthesis notes this as a constraint on CAND-4, but this is a change to `requirements.txt` that should happen *before* any threading work begins — not as part of CAND-4's implementation. This is a **pre-flight action for CAND-4's spike**, independent of the CAND-4 implementation work itself.

### CC-3 — The synthesis DAG is mostly correct; one correction

The synthesis proposes `CAND-12 → {CAND-4, 5, 6} → CAND-3 → rest`. The challenger agrees with the spine. Corrections and additions:

- CAND-8 (Hanson fast path) does NOT depend on CAND-4. It depends only on CAND-5 (queue-latest) and CAND-6 (debounce). CAND-8 can and should move earlier — it is the "easiest win in the entire roadmap" (adversary H-3) and can ship after CAND-12 + CAND-5 + CAND-6, independently of the threading work.
- CAND-10 should be removed from the DAG entirely (parked) once CAND-2 is confirmed for the Now-lane.
- CAND-9 should be explicitly post-CAND-3 and post-CAND-4, not a peer of CAND-11.

Corrected minimal DAG:
```
CAND-12 (telemetry — foundational #0)
  → CAND-13 (resolution-cap hygiene — free win, no deps)
  → CAND-5  (queue-latest guard — correctness fix)
  → CAND-6  (debounce — interaction discipline)
  → CAND-8  (Hanson fast path — easiest win, ships here)
  → CAND-11 (clipped-mesh cache — low-risk optimization)
  → CAND-7  (LRU mesh cache — pairs with CAND-11)
  → CAND-1  (Flying Edges — measure speedup with CAND-12 in place)
  → CAND-4 [spike first] (threading worker)
  → CAND-3  (coarse LOD — depends on CAND-4)
  → CAND-2  (Numba — high-effort, high-impact, after LOD)
  → CAND-9  (in-place mesh update — defer until CAND-3+4 in place)
  (CAND-10 → park if CAND-2 confirmed)
```

### CC-4 — No candidate touches AI-11 (enum forms) or AI-12/AI-13 (color/contrast) — no concern

None of the 13 candidates touches UI color, text, or Qt enum usage. AI-11 through AI-13 are inapplicable here.

### CC-5 — CAND-4's `QApplication.processEvents()` removal is load-bearing, not incidental

The synthesis correctly notes that CAND-4 can remove the `QApplication.processEvents()` call at `app.py:349`. This is desirable because `processEvents()` is the source of AI-9 re-entrancy risk. However, `processEvents()` currently serves as the "keep the status bar alive" mechanism during the synchronous compute. If CAND-4 is implemented *without* removing `processEvents()` (e.g., as a first cut), the re-entrancy risk persists. The CAND-4 implementation brief must explicitly include `processEvents()` removal and replacement with a `statusBar().showMessage()` call that fires before the worker is dispatched — this is the correct async equivalent.

---

## 7. Recommended Kill List

**None.** No candidate should be killed outright. The parking-lot candidates are:
- **CAND-10** — conditional park (park if CAND-2 ships; revive only if CAND-2 is abandoned)
- **CAND-9** — not killed, but deferred to post-CAND-3+CAND-4 (current value density is too thin to justify now)

---

*Challenge written by the CHALLENGER sub-agent. 0 BLOCKERs / 3 MAJORs / 4 MINORs / 6 NONEs. Top objection theme: effort honesty on threading candidates and CAND-10 redundancy resolution.*
