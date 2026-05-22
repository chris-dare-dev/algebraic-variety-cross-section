# Final Report — realtime-variety-render

**Date:** 2026-05-22
**Scout id:** `realtime-variety-render`
**Pipeline:** /capability-scout (5 parallel scouts → synthesize → challenge → prioritize)
**Total candidates:** 13 (CAND-1 … CAND-13; CAND-10 conditionally parked)
**Challenger severity:** 0 BLOCKER · 3 MAJOR · 4 MINOR · 6 NONE
**Scoring:** RICE-light (R × I × C / E) − challenger penalty (−25% per MAJOR)

---

## 1. Executive summary

The five scouts converged hard: the ~0.5–1.45 s latency that forces render-on-release is **entirely inside `surface.generate()`** — VTK rendering (`add_mesh`+`render`) costs ~9 ms. The cost splits ≈ field-evaluation 41–45% / marching-cubes 45% / smoothing+clean+normals ~10% (adversary scout's measured timing table). The top-3 by adjusted RICE are **CAND-5** (re-entrancy guard drop→queue-latest, 32.0 — a 2-line CRITICAL correctness fix), **CAND-12** (render timing telemetry, 20.0) and **CAND-13** (grid-resolution-cap hygiene, 20.0) — all XS quick wins. But RICE's effort-divisor deliberately rewards cheap wins, and the **destination** is three higher-effort candidates: **CAND-3** (coarse-preview LOD, 7.5), **CAND-4** (background-thread worker, 2.81), and **CAND-2** (Numba JIT field eval, 6.75). Those three are what actually deliver a continuously-updating surface during drag; the cheap top-rankers are the scaffolding and one genuine special case (**CAND-8**, Hanson fast-path, 18.0 — an entire variety family that is *already* 27–38 ms and can support continuous drag today with zero compute optimization).

**Main recommendation:** sequence by the DAG, not raw RICE. Ship the XS scaffolding first (CAND-12 → CAND-13 → CAND-5 → CAND-6), then the free win CAND-8, then the architectural arc (spike CAND-4 → CAND-4 → CAND-3 → CAND-2). **Honest caveat:** every speedup number in this report (Flying Edges "1–2 orders of magnitude", Numba "10–30×", coarse-n "6–22×") is a literature/peer claim — none has been measured *on this app's macOS Apple-Silicon target*. CAND-12 (telemetry) exists precisely to convert those claims into measured fact, which is why it is foundational #0 despite being XS.

---

## 2. Quick-glance ranking table

| Rank | Cand | Title | Category | Size | R | I | C | E | Penalty | RICE | Challenger |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CAND-5 | Re-entrancy guard: drop → queue-latest | Interaction/UI | XS | 10 | 1 | 0.8 | 0.25 | — | **32.0** | NONE |
| 2 | CAND-12 | Render-pipeline timing instrumentation | Performance | XS | 10 | 1 | 0.5 | 0.25 | — | **20.0** | NONE |
| 3 | CAND-13 | Grid-resolution-cap + skip-render hygiene | Performance | XS | 10 | 1 | 0.5 | 0.25 | — | **20.0** | NONE |
| 4 | CAND-8 | Hanson parametric fast-path (continuous drag) | Interaction/UI | XS | 3 | 3 | 0.5 | 0.25 | — | **18.0** | MINOR |
| 5 | CAND-11 | Clipped-mesh cache | Performance | XS | 10 | 0.5 | 0.5 | 0.25 | — | **10.0** | NONE |
| 6 | CAND-1 | VTK Flying Edges (replace skimage MC) | Performance | S | 10 | 1 | 0.9 | 1 | — | **9.0** | MINOR |
| 7 | CAND-6 | Debounce slider/grid `valueChanged` | Interaction/UI | S | 10 | 1 | 0.8 | 1 | — | **8.0** | NONE |
| 8 | CAND-3 | Two-pass coarse-preview LOD | Performance | M | 10 | 3 | 1.0 | 3 | −25% | **7.5** | MAJOR |
| 9 | CAND-2 | Numba JIT field-evaluation kernel | Performance | M | 10 | 3 | 0.9 | 3 | −25% | **6.75** | MAJOR |
| 10 | CAND-4 | Background-thread mesh-generation worker | Performance | L | 10 | 3 | 1.0 | 8 | −25% | **2.81** | MAJOR |
| 11 | CAND-7 | LRU parameter-tuple mesh cache | State/persistence | S | 3 | 1 | 0.8 | 1 | — | **2.4** | MINOR |
| 12 | CAND-9 | In-place mesh update (`mapper.SetInputData`) | Rendering/mesh | S | 10 | 0.5 | 0.3 | 1 | — | **1.5** | MINOR |
| — | CAND-10 | Field sub-expression cache | Performance | M | — | — | — | — | parked | **park** | conditional |

CAND-10 is parked per challenger CC-1 / synthesis tension #3: it is redundant with CAND-2 (Numba). Revive only if CAND-2 is abandoned.

---

## 3. Top-10 in detail

### Rank 1 — CAND-5 — Re-entrancy guard: drop → queue-latest · RICE 32.0 · Challenger NONE

**Synthesis:** Change the `_computing` guard from a pure DROP to "queue the latest": when a render is requested while one is in flight, set `_pending_render = True`; in the `finally` block, schedule one catch-up render via `QTimer.singleShot(0, …)`.

**Why it matters:** Today (adversary C-2, CRITICAL) a fast drag-and-release fires N events; every event after the first hits `if self._computing: return` and is discarded — the slider's **final resting position is never rendered**. This is a correctness bug independent of any optimization.

**Challenger (NONE):** "XS, no AI conflict, ~2-line change, well-specified. Correctness fix that ships standalone."

**RICE:** R=10 (every drag-release path), I=1 (fixes a confirmed bug), C=0.8 (2-brief + code-anchored CRITICAL), E=0.25 (XS). 10×1×0.8/0.25 = **32.0**. No penalty. Rank 1 — highest because it is a near-free fix to a real bug and a prerequisite for any continuous-drag mode.

**DAG:** Foundational. Ships standalone or folds into CAND-4.

---

### Rank 2 — CAND-12 — Render-pipeline timing instrumentation · RICE 20.0 · Challenger NONE

**Synthesis:** `time.perf_counter()` brackets around `surface.generate()` (optionally per sub-step), surface the ms in the status bar. The "~0.5 s" figure in CONTEXT.md is informal; the adversary measured 0.66–1.45 s.

**Why it matters:** Foundational #0 — every other candidate's impact claim needs a measured before/after, and regression detection needs a baseline. The adversary scout had to write its own probe because the app has no telemetry.

**Challenger (NONE):** "XS, no AI conflict, foundational for every other candidate's before/after claim. Pure telemetry."

**RICE:** R=10, I=1 (unblocks measurement of everything else), C=0.5 (1-brief, code-anchored), E=0.25. 10×1×0.5/0.25 = **20.0**.

**DAG:** Foundational #0 — do this first so CAND-1/2/3 speedups are measured, not assumed.

---

### Rank 3 — CAND-13 — Grid-resolution-cap + skip-render hygiene · RICE 20.0 · Challenger NONE

**Synthesis:** Three small fixes: lower the Fermat-quartic adaptive `n` cap 260→~220 for the interactive path (260³≈17.6M voxels, measured 1.45 s); lower Enriques Fig 4's hardcoded `n=260`→~220 (smooth field, no near-singularities); add a `_render_dirty` flag to skip redundant `plotter.render()` calls.

**Why it matters:** Pure tuning, no architecture change. Reserves the 260-resolution grids for the screenshot/export path where quality matters and latency does not. The `surfaces.py:223` comment ("~1 s") is already wrong.

**Challenger (NONE):** "XS, no AI conflict. The adversary L-1/L-2/L-3 findings are well-specified."

**RICE:** R=10, I=1, C=0.5 (2-brief), E=0.25. **20.0**.

**Open question (Phase 4 surfaces):** confirm the n=220-vs-260 quality delta is imperceptible at viewport zoom with a spot-check render.

---

### Rank 4 — CAND-8 — Hanson parametric fast-path · RICE 18.0 · Challenger MINOR

**Synthesis:** The Calabi–Yau Hanson parametric surfaces regenerate in 27–38 ms — 20–50× faster than the implicit pipeline. Tag each `Surface` with a speed hint; for fast surfaces, wire the debounced `valueChanged` straight to a render with NO coarse-LOD path needed.

**Why it matters:** The adversary calls this "the easiest win in the entire roadmap." Genuine continuous drag for an entire variety family with **zero compute optimization** — pure UI signal-routing. Also a clean proving ground for the continuous-drag discipline before the hard implicit-pipeline work.

**Challenger (MINOR):** Prefer `typical_ms: int = 0` over `fast: bool` (a bare bool drifts as surfaces are added). Confirm the `Surface` dataclass field-addition pattern against `surfaces.py` first (it is not frozen, so the addition is clean).

**RICE:** R=3 (Hanson family only), I=3 (transformative for those surfaces — true continuous drag), C=0.5 (1-brief, code-anchored), E=0.25. 3×3×0.5/0.25 = **18.0**.

**DAG:** Ships after CAND-5 + CAND-6; does NOT depend on CAND-4 (challenger CC-3 correction — the synthesis implied a CAND-4 dependency it does not have).

---

### Rank 5 — CAND-11 — Clipped-mesh cache · RICE 10.0 · Challenger NONE

**Synthesis:** Cache `_clipped_mesh` alongside `_raw_mesh`; invalidate only on raw-mesh change OR domain-settings change. Today `_apply_domain_and_render` re-runs `clip_to_domain` (a full `mesh.copy()` + scalar-tag + clip) on every render even when only an appearance setting changed.

**Challenger (NONE):** "XS, no AI conflict, natural extension of the existing AI-10 single-slot cache."

**RICE:** R=10, I=0.5 (removes a copy+clip on the common path — small), C=0.5 (1-brief), E=0.25. **10.0**.

---

### Rank 6 — CAND-1 — VTK Flying Edges · RICE 9.0 · Challenger MINOR

**Synthesis:** Replace `skimage.measure.marching_cubes` with `vtkFlyingEdges3D` via `pv.ImageData.contour([0.0], method='flying_edges')` — SMP-threaded, 1–2 orders of magnitude faster per Kitware benchmarks, zero new dependencies, mathematically identical output.

**Challenger (MINOR):** (a) Flying Edges drops scikit-image's analytic gradient normals — CONTEXT.md §3 documents those as a deliberate quality choice; add an off-screen visual comparison on Kummer + Enriques sextic to the acceptance criteria. (b) The "1–2 orders of magnitude" is a Kitware Intel x86 benchmark — the oss-trends scout's "2–4× single-thread" is the right calibration for Apple Silicon. Measure with CAND-12 before advertising a speedup.

**RICE:** R=10, I=1, C=0.9 (4-brief), E=1 (S). **9.0**.

**Scope adjustment:** ship as described; add the Kummer/Enriques visual-comparison gate; measure the real speedup with CAND-12 in place.

---

### Rank 7 — CAND-6 — Debounce slider/grid `valueChanged` · RICE 8.0 · Challenger NONE

**Synthesis:** Gate drag-time render requests through a 50–150 ms debounce (hand-rolled `QTimer` single-shot, or `superqt.@qdebounced` BSD-3-Clause). The release path bypasses the debounce as the full-res trigger.

**Challenger (NONE):** "S, no AI conflict, QTimer form requires no new dep. Hand-rolled QTimer preferable if CAND-4 is deferred; superqt acceptable once superqt is pulled for CAND-4."

**RICE:** R=10, I=1, C=0.8 (3-brief), E=1. **8.0**.

**DAG:** Interaction-discipline prerequisite for CAND-8 and CAND-3. Recommend the QTimer form (zero new dep); share one debounce util between `ParametersPanel` and `ParameterGridPanel` (a `ui_helpers` addition).

---

### Rank 8 — CAND-3 — Two-pass coarse-preview LOD · RICE 7.5 · Challenger MAJOR

**Synthesis:** During a drag, regenerate the implicit surface on a coarse grid (n≈60–120 vs production 220–260) with smoothing/clean/normals skipped; snap to full resolution + quality on release. Adversary timing: n=120 cuts field+MC from 326 ms to 55 ms (6×); n=80 to ~15 ms (~22×). This is the universal peer pattern (Mathematica `ControlActive`, ParaView interactive/still, Surfer, Desmos) and the technique that actually delivers a continuously-moving surface.

**Challenger (MAJOR):** (a) **AI-15 disclaimer must be in the v0 spec, not deferred** — the "coarse preview — true surface on release" badge must persist until the *full-res* mesh is confirmed received, never clear on the coarse render completing. (b) The CAND-4 dependency is **strict, not soft** — without a worker thread a 55 ms coarse render still blocks the GUI thread; CAND-3 alone gives a slider that stutters at 55 ms intervals (better than 650 ms, but not "continuous"). (c) The topology-misrepresentation floor is unmeasured — need a per-surface coarse-n table (the smallest n at which Kummer's 16 nodes / the Dwork conifold stay honest).

**RICE:** R=10, I=3 (the destination technique), C=1.0 (5-brief), E=3 (M). 10×3×1.0/3 = 10 ×0.75 (MAJOR) = **7.5**.

**Scope adjustment:** v0 spec must include disclaimer wording + hide-logic, a per-surface coarse-n floor table from an off-screen n-sweep, and coarse-path-disabled for Hanson surfaces.

---

### Rank 9 — CAND-2 — Numba JIT field-evaluation kernel · RICE 6.75 · Challenger MAJOR

**Synthesis:** Replace NumPy-broadcasting polynomial field evaluation with `@njit(parallel=True)` kernels — loop fusion + AVX SIMD + multi-core. Field eval is the single largest cost (41–45%); math-research estimates 10–30× speedup. Numba is BSD-2-Clause, arm64 macOS wheels confirmed.

**Challenger (MAJOR):** (a) **8 distinct implicit generators** each need a separate hand-restructured kernel — the degree-6 Enriques surfaces are error-prone, and the existing smoke tests do NOT numerically check field values, so a transcription error would ship a mathematically-wrong-but-plausible surface (AI-15). (b) First-call JIT latency (8 × 200–400 ms = 1.6–3.2 s) needs an explicit warm-up strategy. (c) Apple-Silicon `parallel=True` threading-layer must be pinned (`workqueue`, not unguarded TBB, to avoid interacting with CAND-4's VTK SMP).

**RICE:** R=10, I=3, C=0.9 (4-brief), E=3 (M). 10×3×0.9/3 = 9.0 ×0.75 = **6.75**.

**Scope adjustment:** v0 = `@njit` for the two highest-cost generators only (Fermat + Enriques canonical sextic = 460 ms of the worst-case budget) + per-generator numerical spot-check tests + macOS `workqueue` layer + measured <500 ms warm-up. v1 = remaining 6 generators.

---

### Rank 10 — CAND-4 — Background-thread mesh-generation worker · RICE 2.81 · Challenger MAJOR

**Synthesis:** Move `surface.generate()` off the Qt GUI thread onto a `QRunnable`/`QThread` worker; the worker hands the finished `pv.PolyData` back via a `Qt.QueuedConnection` signal; the main thread does `add_mesh`/`render`. The `_computing` guard becomes "worker in flight"; the `processEvents()` re-entrancy workaround is removed.

**Why it matters:** The adversary calls this "the single highest-leverage change — every other optimization builds on it." It is the architectural unlock for continuous drag. Its low RICE is purely the L effort-divisor, NOT low value — read the DAG, not the number.

**Challenger (MAJOR):** (a) **Effort honesty** — sized L by the synthesis, realistically L+/XL once the macOS spike is priced in. (b) The `PySide6 >=6.6,<7` pin *includes* 6.10, and pyvistaqt issue #793 reports a macOS hang on PySide6 ≥ 6.10 — a **live** risk; tighten to `<6.10` as a pre-flight action. (c) VTK GitLab #18782: SMP + Python GC crash on macOS — mitigation (retain explicit Python refs to output meshes) must be in the implementation brief. (d) **AI-2 test gap** — worker lifecycle / cancel-resubmit needs a live `QApplication` to test; pytest-qt is an AI-2 BLOCKER, so this logic ships with no automated regression guard.

**RICE:** R=10, I=3, C=1.0 (5-brief), E=8 (L). 10×3×1.0/8 = 3.75 ×0.75 = **2.81**.

**Scope adjustment:** v0 = a mandatory 1–2 day **spike** (reproduce pyvistaqt #793 on the dev machine, tighten the PySide6 pin, confirm VTK+QThread safety with a minimal off-screen `pv.PolyData`-round-trip-via-signal test, no plotter). v1 = full implementation, only if the spike passes.

---

## 4. Recommended next steps

### 4.1 Feed to CONTEXT.md §6's 5-phase pipeline first (1–2 candidates)

1. **CAND-12 (timing telemetry)** — XS, NONE, foundational #0. Implement first; every subsequent candidate's speedup becomes a measured fact instead of a literature claim. Trivial §6 run.
2. **CAND-8 (Hanson parametric fast-path)** — XS, MINOR, RICE 18.0. The single highest value-per-effort capability: continuous drag for the entire Calabi–Yau Hanson family with zero compute work. Ships after CAND-5 + CAND-6. This is the candidate that gives the user a *visible* "real-time" result fastest.

Bundle the four XS quick-wins (CAND-12 → CAND-13 → CAND-5 → CAND-6) as a single §6 pass — together ~3–4 person-days, all NONE/MINOR, and they are the scaffolding the rest stands on.

### 4.2 Spike before implementation (1 candidate)

**CAND-4 (background-thread worker)** — do NOT enter §6 implementation cold. Run the challenger's prescribed 1–2 day spike first: (a) reproduce pyvistaqt #793 on the dev machine; (b) tighten `requirements.txt` to `PySide6 <6.10` if confirmed; (c) prove VTK+`QThread` safety on macOS arm64 with a minimal off-screen `pv.PolyData`-via-signal round-trip. CAND-3 and CAND-2 both sit downstream of this spike's outcome.

### 4.3 The destination arc (after the spike)

CAND-4 → CAND-3 (coarse LOD) → CAND-2 (Numba) is the sequence that actually delivers continuously-updating implicit surfaces. CAND-1 (Flying Edges) can land any time after CAND-12 (it is independent and low-risk — measure its real speedup once telemetry exists).

### 4.4 Park

- **CAND-10 (field sub-expression cache)** — parked; redundant with CAND-2. Revive only if CAND-2 is abandoned (e.g., Numba arm64 instability).
- **CAND-9 (in-place mesh update)** — deferred, not parked; revisit after CAND-3 + CAND-4 land, when its real win-rate (fraction of frames with matching vertex count) can be measured. Current value density too thin.
- **CAND-7 (LRU mesh cache)** — viable (RICE 2.4) but lower priority; pairs naturally with CAND-11 and with idle-time neighbor pre-rendering (the user's "preloading" idea) as a v2.
- Parking-lot from synthesis: parameter-space mesh interpolation (AI-15 violation), GPU isosurfacing/raycasting (AI-1/AI-3 conflict), span-space, dual contouring, incremental MC.

---

## 5. Honest limitations

- Each scout had a ~15-minute budget; the GPU-isosurfacing trajectory and the topology-guarantee literature (Stander-Hart / Plantinga-Vegter) are under-explored.
- Triangulation across 5 briefs is strong evidence but not infallible — five scouts can share a blind spot.
- **Every speedup figure in this report is a literature or peer-benchmark claim, not a measurement on this app's macOS Apple-Silicon target.** Flying Edges "1–2 orders of magnitude" is Kitware's Intel x86 number; Numba "10–30×" and coarse-n "6–22×" are estimates. CAND-12 exists to convert these to measured fact — treat the RICE Impact scores as provisional until it lands.
- The adversary scout's timing table was measured on Windows 11 (its stated platform), not macOS Apple Silicon — absolute numbers will shift on the primary target.
- Effort t-shirts → person-weeks carry ±50% accuracy at this stage; CAND-4's L is the least trustworthy (challenger argues L+/XL).
- The challenger evaluated against current AI-1…AI-15; if invariants evolve (e.g., AI-2 relaxes to allow `pytest-qt` once the macOS offscreen segfault is fixed), CAND-4's test-gap objection weakens.
- macOS Qt+VTK threading is the highest-uncertainty axis; Linux/Windows threading footguns were not probed.

---

## 6. Cross-reference index

| Cand | Title | competitive | math-research | oss-trends | desktop-platform | adversary |
|---|---|---|---|---|---|---|
| CAND-1 | Flying Edges | C-1 | T-3 | ✓ | ✓ | — |
| CAND-2 | Numba JIT | C-10 | T-2 | ✓ | ✓ | — |
| CAND-3 | Coarse-preview LOD | C-2/C-6 | T-1/T-9 | ✓ | ✓ | H-1/M-1/M-2/M-3 |
| CAND-4 | Background-thread worker | C-4/C-11 | T-4 | ✓ | ✓ | C-1 |
| CAND-5 | Queue-latest guard | C-3 ctx | — | — | — | C-2 |
| CAND-6 | Debounce | C-3 | — | ✓ | ✓ | — |
| CAND-7 | LRU mesh cache | C-5 | — | ✓ | ✓ | — |
| CAND-8 | Hanson fast-path | — | Theme E | — | — | H-3 |
| CAND-9 | In-place mesh update | — | — | — | — | H-4 |
| CAND-10 | Field sub-expr cache (parked) | — | — | — | — | H-2 |
| CAND-11 | Clipped-mesh cache | — | — | — | — | M-4 |
| CAND-12 | Timing telemetry | — | — | — | — | M-5 |
| CAND-13 | Resolution-cap hygiene | — | §5 | — | — | L-1/L-2/L-3 |

Artifacts: `survey/{competitive,math-research,oss-trends,desktop-platform,adversary}-brief.md` · `artifacts/synthesis.md` · `artifacts/challenge.md` · this report.

---

## Handoff offer

The top-3 candidates all clear RICE ≥ 3.0 (32.0 / 20.0 / 20.0), so per the capability-scout contract this report offers — but does **not** auto-invoke — a follow-on implementation pass.

**To ship the recommended first bundle via CONTEXT.md §6's 5-phase implementation pipeline:**

1. **Quick-wins bundle** — run `CAND-12 → CAND-13 → CAND-5 → CAND-6` as one §6 cycle (all XS/S, all NONE/MINOR, ~3–4 person-days). Math-research Phase 1 is N/A (no new math); go straight to implementation.
2. **CAND-8 (Hanson fast-path)** — a second small §6 cycle right after; it is the fastest route to a visible "real-time" result.
3. **CAND-4 spike** — run the 1–2 day discovery spike (§4.2) as a standalone investigation BEFORE committing CAND-4 to a §6 implementation cycle.
4. **Destination arc** — CAND-4 → CAND-3 → CAND-2, each its own §6 cycle, sequenced after the spike clears.

`/capability-scout` never auto-invokes an implementation pipeline. The next move is yours — say the word to start the quick-wins bundle, or to run the CAND-4 spike first.

*Final report written by the main session reading synthesis + challenge end-to-end. RICE-light scored; −25% per MAJOR applied; 0 BLOCKERs so no halving. The ranking rewards cheap wins by construction — §4's DAG, not the raw RICE column, is the recommended execution order.*
