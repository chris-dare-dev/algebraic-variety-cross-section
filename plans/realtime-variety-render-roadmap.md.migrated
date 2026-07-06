# Realtime Variety Render — Roadmap

> **Slug:** `realtime-variety-render` · **Created:** 2026-05-22 · **Status:** scaffold (Phase 0)

<!-- ROADMAP:section:meta -->
## 0. Meta

- **Author:** chris.dare@nalej.com
- **Brief source:** --brief flag  *(one of: `--brief` arg | conversation summary | unspecified)*
- **Execution handoff:** CONTEXT.md section 6 — the 5-phase implementation pipeline (Math research / code archeology → Implementation + off-screen render verify → Adversarial review → Remediation → UI/UX)
- **Issue tracker:** GitHub Issues *(populated only if `--gh-issues` was passed; orchestrator resolves `owner/repo` at gate time via `gh repo view --json nameWithOwner`)*
- **Repo invariants:** AI-1 .. AI-15 — `.claude/references/app-invariants.md`

<!-- ROADMAP:section:refine -->
## 1. Brief

Translate the capability-scout final report at .claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md into an executable Now/Next/Later roadmap of tangible milestones. The report ranks 13 candidates (CAND-1..CAND-13) for making the algebraic variety update in real time as a parameter slider or grid-dot is dragged. Key facts: (1) the ~0.5-1.45s latency is entirely inside surface.generate() -- field-eval 41-45% / marching-cubes 45% / post-processing ~10%; (2) the universal fix is two-pass LOD (coarse preview during drag, full-res snap on release); (3) 0 BLOCKERs, 3 MAJOR (CAND-2 Numba, CAND-3 coarse-LOD, CAND-4 background-thread), 4 MINOR, 6 NONE. Recommended execution order (DAG, not raw RICE): FIRST a quick-wins bundle CAND-12 (render timing telemetry) -> CAND-13 (grid-resolution-cap hygiene) -> CAND-5 (re-entrancy guard drop->queue-latest, fixes a CRITICAL correctness bug) -> CAND-6 (debounce slider/grid valueChanged); THEN CAND-8 (Hanson parametric fast-path -- continuous drag for the Calabi-Yau Hanson family with zero compute optimization); THEN a mandatory 1-2 day spike on CAND-4 (background-thread worker -- macOS pyvistaqt issue #793 hang risk on PySide6>=6.10); THEN the destination arc CAND-4 -> CAND-3 (coarse-preview LOD, needs AI-15 disclaimer + per-surface coarse-n floor table) -> CAND-2 (Numba JIT field eval, v0 = two heaviest generators only). CAND-1 (VTK Flying Edges) is independent, lands any time after CAND-12. CAND-11 (clipped-mesh cache) is a cheap standalone. Parked: CAND-10, CAND-9, CAND-7. Hard constraints AI-1, AI-2, AI-3, AI-9, AI-15. Hand off cleanly to CONTEXT.md section 6's 5-phase implementation pipeline.

## 2. How-Might-We

How might we **progressively reduce surface-regeneration latency from >0.5 s to imperceptible during slider/grid-dot drag** so that **a researcher exploring the algebraic variety families** can **observe the surface morphing in real time without releasing the control**?

## 3. Sharpening answers

- **Who:** The researcher driving the GUI — specifically the person dragging a parameter slider or grid-dot to explore how an algebraic variety deforms across parameter space.  Secondary beneficiary: the future-Claude session re-entering via CONTEXT.md, which needs a documented DAG of interdependent candidates rather than a flat list.
- **Success looks like:** A researcher drags any Hanson-family slider and the surface updates fluidly at every tick (no release required). For implicit surfaces (Fermat, Kummer, Enriques, Dwork), a coarse-preview mesh follows the drag within ~80 ms intervals and the final full-resolution surface snaps into place on release — with a visible status-bar "Preview" badge throughout the coarse phase. Both behaviors are observable without instrumentation.
- **Constraints:**
  - AI-1 (`.claude/references/app-invariants.md`): PySide6 + PyVista + pyvistaqt only — no alternative renderers.
  - AI-2 (`.claude/references/app-invariants.md`): test suite is Qt-free; `pytest-qt` is prohibited until the macOS Qt+VTK offscreen segfault is resolved — the worker lifecycle (CAND-4) cannot have automated regression tests.
  - AI-3 (`.claude/references/app-invariants.md`): never construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen`; all render-verification uses `pv.OFF_SCREEN = True`.
  - AI-6 (`.claude/references/app-invariants.md`): Hanson parametric surfaces must NOT pass through Taubin smoothing or marching cubes — the coarse-LOD path (CAND-3) must be disabled for the parametric pipeline.
  - AI-9 (`.claude/references/app-invariants.md`): any new `processEvents()` must be guarded by `self._computing`; CAND-5 extends this guard to queue-latest semantics rather than drop.
  - AI-10 (`.claude/references/app-invariants.md`): domain-clip changes must NOT regenerate the mesh — CAND-11 (clipped-mesh cache) must preserve this invariant.
  - AI-15 (`.claude/references/app-invariants.md`): coarse-preview LOD (CAND-3) is an honest "approximate" render — the AI-15 disclaimer badge must show from coarse-preview start and persist until the full-resolution mesh is confirmed received by `_apply_domain_and_render`, not cleared on the coarse render completing.
  - macOS Apple Silicon primary target; PySide6 pin `>=6.6,<7` includes 6.10 where pyvistaqt issue #793 reports a macOS hang — a live risk requiring a pre-flight spike.
  - Single-developer "commit to main" cadence (CONTEXT.md §12); test suite budget ~4 s / 120 tests.
  - CONTEXT.md §9 explicit deferral: no QSettings state persistence, no pytest-qt, no first-launch auto-render — none of these are in scope.
- **Prior art:**
  - CONTEXT.md §4.4 (re-entrancy guard `_computing`, `processEvents()` at ~line 339-341 of `app.py`) — the existing DROP semantics that CAND-5 will upgrade to queue-latest.
  - CONTEXT.md §8.5 (re-entrancy from `processEvents` — the documented bug that AI-9 guards against).
  - CONTEXT.md §9 ("No tests for app.py / MainWindow" — AI-2 constraint on threading tests explicitly documented as a known gap).
  - `.claude/notes/capability-scouts/realtime-variety-render/artifacts/synthesis.md` §6: INT-2 (render-on-release is the deliberate current discipline) — the candidates augment it, not replace it.
  - `.claude/notes/capability-scouts/realtime-variety-render/artifacts/synthesis.md` §5 tension #1: AI-15 honesty vs continuous-update fidelity — coarse-grid previews need visible disclaimers.
  - `.claude/notes/capability-scouts/realtime-variety-render/artifacts/synthesis.md` §5 tension #2: parameter-space mesh interpolation is AI-15-prohibited (parked, not in scope).
  - `.claude/notes/capability-scouts/realtime-variety-render/artifacts/challenge.md` §3 MAJOR-CAND-4: VTK GitLab #18782 GC-crash-under-SMP on macOS — explicit Python ref retention required in the worker implementation brief.
- **Why now:** The `/capability-scout` final report landed 2026-05-22 at `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` with a fully-ranked 13-candidate catalog, adversary critique, and a recommended DAG. CAND-5 is a 2-line CRITICAL correctness fix (the slider's final resting position is never rendered on a fast drag-and-release — adversary C-2) that should ship immediately regardless of the larger optimization arc. The quick-wins bundle is fully specified and can enter CONTEXT.md §6's pipeline without further research.

## 4. Assumptions

- `[MUST]` pyvistaqt issue #793 does NOT hang on the current dev machine's installed PySide6 version, OR the `requirements.txt` pin can be tightened to `PySide6 <6.10` without breaking other functionality (spike: e3 macOS thread-safety spike) — *reproduce the hang on dev machine before any CAND-4 implementation work (<=2 days); CAND-3 and CAND-2 are both downstream of CAND-4, so this gates the entire destination arc*
- `[MUST]` VTK + `QThread` are safe to use concurrently on macOS arm64 (spike: e3 macOS thread-safety spike) — i.e., `pv.PolyData` objects can be constructed on a worker thread and handed to the main thread via a `Qt.QueuedConnection` signal without a GC-triggered crash (VTK GitLab #18782) — *prove with a minimal off-screen `pv.PolyData`-via-signal round-trip test on the dev machine, no plotter; explicit Python ref retention is the documented mitigation*
- `[MUST]` Numba `@njit(parallel=True)` is available and stable on macOS arm64 (Numba 0.60+) with the `workqueue` threading layer (spike: e5 Numba arm64 spike) — *install and verify before CAND-2 implementation; Apple-Silicon wheels confirmed on PyPI but not validated against this specific app's deps*
- `[SHOULD]` The quality delta between n=220 and n=260 grid resolution is imperceptible at viewport zoom for Fermat quartic and Enriques Fig 4 — *fallback: keep n=260 for both if a spot-check off-screen render reveals visible degradation, accepting slightly higher latency on the interactive path*
- `[SHOULD]` The coarse-preview n=80 floor is topologically honest for Kummer (16 nodes remain visually distinct) and Dwork conifold at ψ≈1 — *fallback: raise the floor to n=100 or n=120 for affected surfaces; must be validated via an off-screen n-sweep before CAND-3 ships*
- `[SHOULD]` Flying Edges (CAND-1) produces visually equivalent surface quality to skimage marching cubes for all 8 implicit generators on macOS Apple Silicon — specifically, the loss of analytic gradient normals does not produce visible shading degradation on Enriques sextic or Kummer high-curvature regions — *fallback: keep skimage MC if off-screen Kummer+Enriques comparison renders show visible shading regression; Flying Edges is independent of the destination arc and can be deferred without blocking anything*
- `[SHOULD]` Numba first-call JIT latency for the initial 2-generator v0 scope (Fermat + Enriques canonical sextic) stays under 500 ms total with a startup warm-up strategy — *fallback: move warm-up to background thread at first surface selection rather than eager app startup*
- `[MIGHT]` A single hand-rolled `QTimer`-based debounce utility shared between `ParametersPanel` and `ParameterGridPanel` (a `ui_helpers` addition) is the cleanest CAND-6 implementation — *defer: if `superqt` is already pulled in by CAND-4's worker pattern, `@qdebounced` is equally valid; decide at implementation time*
- `[MIGHT]` `typical_ms: int = 0` is a cleaner `Surface` dataclass field than `fast: bool` for CAND-8's speed-routing — *defer: decide at CAND-8 implementation time; challenger CC-3 prefers `typical_ms` but either is valid*
- `[MIGHT]` CAND-11 (clipped-mesh cache) delivers a measurable latency reduction on the appearance-only-change path — *defer: confirm with CAND-12 telemetry after it ships*

## 5. Objective and Key Results

**Objective:** By 2026-09-30, a researcher can drag any Calabi–Yau Hanson-family slider and watch the surface update continuously (no release required), and dragging an implicit-surface slider shows a coarse-but-valid preview in motion with the final full-resolution surface snapping into place on release — all without the slider freezing or the final drag position being silently dropped.

**Key Results:**
1. CAND-5 ships: every fast drag-and-release on an implicit surface correctly renders the slider's final resting position — confirmed by off-screen render at the default parameter + a manual drag-release smoke check (the current CRITICAL correctness bug is eliminated).
2. CAND-12 ships: the status bar displays a measured render time in ms for every surface generation call, providing a before/after baseline for all subsequent performance candidates.
3. CAND-8 ships: the Calabi–Yau Hanson surfaces (3 parametric figures) update visibly at every slider tick during a drag without requiring release — confirmed by a `typical_ms` measurement ≤ 80 ms on the dev machine.
4. CAND-3 + CAND-4 ship: implicit surfaces show a coarse-preview mesh updating during drag (with "Preview" status-bar badge) and snap to full resolution on release — CAND-4 spike passes first.

**Won't:**
- No `pytest-qt` UI tests for the threading worker lifecycle or signal-slot path (AI-2 / CONTEXT.md §9 — macOS Qt+VTK offscreen segfault prohibits this until the environment constraint changes).
- No parameter-space mesh interpolation / morphing between cached meshes (AI-15 violation per synthesis tension #2 — the interpolated mesh corresponds to no algebraic equation and will misrepresent topology at intermediate values; parking-lotted permanently for a math-education tool).
- No GPU isosurfacing or raycasting path (AI-1 / AI-3 conflict — produces a rasterized image, not `pv.PolyData`; breaks domain clipping AI-4 and Hanson normals AI-7; macOS Metal VTK backend still experimental as of 2026).
- No new variety families or additional figures in this roadmap (out of scope — the 5-phase pipeline for new varieties is CONTEXT.md §6's own purview; this roadmap is exclusively the latency/interactivity arc for the existing 8 generators).
- No QSettings persistence of slider values, surface selection, or window layout (CONTEXT.md §9 explicit deferral — out of scope for this roadmap).

<!-- ROADMAP:section:decompose -->
## 6. Epics

### 6.1 Decomposition technique

Vertical slicing + enabler stories (default). Each epic cuts from `surfaces.py` / `app.py` render pipeline through to observable status-bar or drag-feedback behaviour. The CAND-4 spike (e3) is an exception: it is an `[ENABLER]` whose sole deliverable is a go/no-go decision artifact — it earns its own epic because its outcome gates two downstream value epics (e4, e5) and the INVEST Estimable letter cannot be satisfied without running it first.

### 6.2 Dependency graph

| Epic | Depends on |
|---|---|
| `realtime-variety-render-e1` | — |
| `realtime-variety-render-e2` | e1 |
| `realtime-variety-render-e3` | e1 |
| `realtime-variety-render-e4` | e3 |
| `realtime-variety-render-e5` | e4 |
| `realtime-variety-render-e6` | e1 |

### 6.3 Epics

#### `realtime-variety-render-e1` — Quick-wins scaffolding bundle `[VALUE]`

**Goal:** Ship CAND-12 (render timing telemetry), CAND-13 (grid-resolution-cap hygiene), CAND-5 (re-entrancy guard drop→queue-latest), CAND-6 (debounce slider/grid valueChanged), and CAND-11 (clipped-mesh cache) as a single coordinated pass — eliminating the CRITICAL correctness bug (final drag position silently dropped), establishing a measured ms baseline in the status bar, and hardening the interaction discipline that every subsequent epic builds on.

**Slice:** `app.py` (`_render_current`, `_computing`/`_pending_render` guard, `processEvents` call site, `_apply_domain_and_render` clip-cache extension); `surfaces.py` (Fermat quartic adaptive `n` cap 260→220, Enriques Fig 4 `n=260`→220, `_render_dirty` flag); optional new `ui_helpers.py` module (shared `QTimer`-based debounce util for `ParametersPanel` + `ParameterGridPanel`); `tests/` (pure-NumPy spot-checks for the grid-cap constants and clip-cache invalidation logic — no pytest-qt).

**INVEST:** 6/6. Independent (all five candidates are NONE-challenger, no external dependencies); Negotiable (CAND-11 can drop if clip-cache logic is contested; debounce timer interval 50–150 ms adjustable); Valuable (status-bar ms readout, final-position correctness fix, and debounce are all directly observable by the researcher); Estimable (all XS/S, adversary-specified to 2-line precision for CAND-5); Small (S: combined ≤1 week); Testable (off-screen render confirms CAND-5 by rendering at a shifted parameter value after a simulated queue-latest cycle; CAND-12 confirmed by reading the status-bar ms string; CAND-13 confirmed by an off-screen n=220 vs n=260 visual spot-check).

**Specialist hints:**
- AI-9 (re-entrancy): CAND-5 extends the `self._computing` guard — the `_pending_render` flag and `QTimer.singleShot(0, ...)` catch-up must live inside the same `finally` block structure documented in CONTEXT.md §4.4; any new `processEvents()` call must be audited for re-entrancy per AI-9. Read `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` §3 rank-1 (CAND-5) for the 2-line spec.
- AI-10 (raw-mesh cache): CAND-11 is a direct extension of the existing single-slot `_raw_mesh` cache pattern — add `_clipped_mesh` alongside it and invalidate only on raw-mesh change OR domain-settings change; AI-10 invariant (no mesh regeneration on domain-radius slider) must be preserved.

**T-shirt:** S (≤1 week)

**Predecessors:** —

**Acceptance signals:**
- CAND-5: an off-screen render triggered at the final parameter position after a simulated fast-drag produces a non-empty `pv.PolyData` (the correctness bug is gone — the final position is rendered, not dropped).
- CAND-12: the status bar displays a `NNN ms` string after every `_render_current` call; a before-vs-after timing log is captured to `/tmp/cand12-baseline.txt` for use as the reference against all subsequent performance candidates.
- CAND-13: off-screen renders of Fermat quartic and Enriques Fig 4 at n=220 vs n=260 show no perceptible quality regression (spot-check PNG saved to "/tmp/cand13-n220-fermat.png" and "/tmp/cand13-n220-enriques4.png"); `[MUST]` assumption §4 "quality delta imperceptible" is confirmed or the cap is raised to n=240.
- CAND-6: a single shared debounce utility (QTimer-based, 80 ms default) is wired to both `ParametersPanel` and `ParameterGridPanel`; the release-path bypass (direct full-res trigger, no debounce delay) is confirmed by a manual smoke-check or a pure-Python unit test of the timer logic.

---

#### `realtime-variety-render-e2` — Hanson parametric continuous-drag fast-path `[VALUE]`

**Goal:** Wire the Calabi-Yau Hanson family's 27-38 ms generation time directly to a continuous-drag render path — adding a `typical_ms: int = 0` field to the `Surface` dataclass and routing "fast" surfaces through the debounce's direct-fire channel — so that a researcher dragging any Hanson-family slider sees the surface update at every tick without releasing the control, with a measured round-trip ≤80 ms on the dev machine.

**Slice:** `surfaces.py` (`Surface` dataclass — add `typical_ms: int = 0` field; set `typical_ms` for the 3 Hanson parametric generators; all other generators default to 0); `app.py` (render-dispatch logic — check `surface.typical_ms > 0` and `surface.typical_ms <= <threshold>` to bypass the coarse-LOD path and fire direct; the coarse-LOD path (CAND-3, e4) must explicitly skip Hanson per AI-6); `tests/` (verify the `typical_ms` field exists on the three Hanson surfaces and defaults to 0 on all implicit generators — pure-Python dataclass test, no Qt).

**INVEST:** 6/6. Independent (depends on e1's debounce discipline but not on any partial e4 work; challenger CC-3 confirmed CAND-8 does NOT depend on CAND-4); Negotiable (`typical_ms` threshold value adjustable; `fast: bool` alternative acceptable — decide at implementation time per §4 `[MIGHT]`); Valuable (visible continuous drag for an entire variety family — the fastest route to a "real-time" result for a researcher); Estimable (XS per final-report; adversary calls it "the easiest win in the entire roadmap"); Small (S: ≤1 week); Testable (CAND-12 telemetry confirms round-trip ≤80 ms on the dev machine; off-screen render produces non-empty PolyData at a mid-drag parameter value without waiting for release).

**Specialist hints:**
- AI-6 (implicit vs parametric pipeline): the `typical_ms`-based fast-path dispatch must NOT enable the coarse-LOD path for Hanson surfaces — those surfaces already skip marching cubes and Taubin smoothing; routing them through a LOD grid would violate the parametric pipeline invariant. When e4's CAND-3 is implemented, its coarse-path guard must check `surface.typical_ms > 0` (or equivalent) and skip. Read `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` §3 rank-4 (CAND-8) for the speed-routing spec and challenger CC-3 correction on the CAND-4 dependency.
- AI-8 (Surface/ParamSpec dataclass contract): adding `typical_ms: int = 0` to the non-frozen `Surface` dataclass is clean (the dataclass is not frozen); confirm the field-addition pattern against `surfaces.py` before implementing; all three Hanson generators (quintic, cubic torus, asymmetric) get `typical_ms` set from their measured generation times.

**T-shirt:** S (≤1 week)

**Predecessors:** realtime-variety-render-e1

**Acceptance signals:**
- CAND-8: a live drag on any Hanson-family slider produces a new surface render at each tick (no release required); CAND-12 telemetry confirms round-trip latency ≤80 ms on the dev machine.
- The `Surface` dataclass has a `typical_ms: int = 0` field; all 3 Hanson generators have non-zero values; all implicit generators default to 0 — confirmed by a pure-Python dataclass unit test.
- Off-screen render at a non-default Hanson parameter value produces a non-empty, visually correct `pv.PolyData` (Hanson normals use `cell_normals=True, consistent_normals=False, auto_orient_normals=False` per AI-7 — no regression).

---

#### `realtime-variety-render-e3` — CAND-4 macOS background-thread spike `[ENABLER]`

**Goal:** Execute the mandatory 1-2 day spike for CAND-4 (background-thread worker) to determine whether pyvistaqt issue #793 (macOS PySide6 >=6.10 hang) affects the dev machine, whether the `requirements.txt` pin must be tightened to `PySide6 <6.10`, and whether `pv.PolyData`-via-QThread signal round-trips are safe on macOS arm64 under VTK GitLab #18782 — producing a go/no-go decision artifact that gates e4 and e5.

**Slice:** `requirements.txt` (potential pin tightening: `PySide6 <6.10`); a standalone spike script (e.g., `spike/cand4-thread-safety.py`) that constructs a `pv.PolyData` on a `QThread`, hands it to the main thread via `Qt.QueuedConnection` signal, and confirms no hang/crash — no plotter, off-screen only; a plain-text spike report at `/tmp/cand4-spike-report.txt` documenting the outcome; `tests/` not applicable (AI-2 prohibits pytest-qt for worker lifecycle tests).

**INVEST:** 5/6. The V letter is ENABLER (no direct user-observable change) but is justified because e4 and e5 deliver the destination arc — the spike is the prerequisite that makes them Estimable; without it CAND-4 is XL/unknown. Independent (requires only e1's merge to be complete — the queue-latest guard is a prerequisite for the worker pattern); Negotiable (scope is fixed: reproduce the hang, tighten pin if needed, prove signal safety — nothing more); Estimable (1-2 days hard cap); Small (S: ≤3 days); Testable (spike script runs to completion without hang on the dev machine; spike report documents the PySide6 version installed and the test outcome).

**Specialist hints:**
- AI-1 (PySide6 + pyvistaqt stack): the spike must stay within the PySide6 + pyvistaqt constraint — no switch to PyQt6 or raw VTK threading; the pin tightening (`PySide6 <6.10`) is the documented mitigation for pyvistaqt issue #793. Read `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` §3 rank-10 (CAND-4) challenger points (a), (b), (c) for the three specific spike objectives.
- AI-2 (Qt-free test suite): the spike script is NOT a pytest test — it is a standalone script run manually on the dev machine (no `QT_QPA_PLATFORM=offscreen` + `QtInteractor`); the spike report is the acceptance artifact, not a test suite entry. VTK GitLab #18782 mitigation (explicit Python ref retention on output meshes) must be confirmed in the spike script and documented in the report.

**T-shirt:** S (1-2 days; hard cap at 3 days — if the spike cannot confirm safety in 3 days, escalate the risk and reassess e4 scope before proceeding)

**Predecessors:** realtime-variety-render-e1

**Acceptance signals:**
- Spike script runs to completion (no hang, no crash) on the dev machine with the installed PySide6 version; the script constructs a non-trivial `pv.PolyData` on a `QThread` and successfully delivers it to the main thread via `Qt.QueuedConnection` signal.
- Spike report at `/tmp/cand4-spike-report.txt` documents: (1) PySide6 version on the dev machine, (2) whether pyvistaqt #793 was reproduced or absent, (3) final `requirements.txt` pin recommendation (`PySide6 <6.10` or unchanged), (4) VTK GitLab #18782 mitigation (explicit ref retention) confirmed or not required.
- Either e4 is green-lit (spike passed, VTK+QThread safe) or the risk is escalated with a documented scope-adjustment recommendation for e4.

---

#### `realtime-variety-render-e4` — Background-thread worker + coarse-preview LOD `[VALUE]`

**Goal:** Move `surface.generate()` off the Qt GUI thread onto a `QRunnable`/`QThread` worker (CAND-4) and implement the two-pass coarse-preview LOD pipeline (CAND-3) for implicit surfaces — delivering a continuously-updating coarse-grid preview during drag (with a persistent "Preview" status-bar badge per AI-15) and a full-resolution snap on release — completing the destination arc for implicit surfaces (Fermat, Kummer, Enriques, Dwork).

**Slice:** `app.py` (worker dispatch replaces direct `surface.generate()` call; `_computing` guard becomes "worker in flight"; `processEvents()` workaround removed; coarse-path triggered on drag with `n=coarse_n[surface_key]`; `_apply_domain_and_render` receives worker result via `Qt.QueuedConnection` signal; AI-15 "Preview" badge logic in status bar — persists until full-res mesh confirmed received, not cleared on coarse render); `surfaces.py` (per-surface `coarse_n` floor table validated by an off-screen n-sweep, e.g. `{fermat_quartic: 80, kummer: 100, enriques_*: 80, dwork: 100}`; coarse-path guard checks `surface.typical_ms > 0` and skips Hanson); spike script from e3 is retired once full implementation is in place; `tests/` (off-screen n-sweep confirms topology honesty at the coarse-n floors for Kummer 16-node visibility and Dwork conifold structure — pure PyVista, no pytest-qt).

**INVEST:** 6/6. Independent (depends on e3 spike pass; fully self-contained once the spike artifacts are in hand); Negotiable (coarse-n floors are per-surface and can be raised or lowered based on topology-honesty off-screen sweep; CAND-3 can ship before CAND-4 is fully stress-tested if the worker lifecycle is stable); Valuable (the destination technique — continuously-moving implicit surface during drag, the core KR3+KR4 outcome); Estimable (L — challenger rated CAND-4 as L+/XL, but with the spike pre-flight scoped separately in e3, this epic's remaining risk is bounded); Small (L: ≤6 weeks; if the spike report reveals XL risk, split CAND-4 into its own L epic and CAND-3 becomes e4b after CAND-4 stablises); Testable (off-screen render in both coarse and full-res modes; topology-honesty check at coarse-n floor; AI-15 badge confirmed by reading status-bar state from the render pipeline).

**Specialist hints:**
- AI-9 (re-entrancy) + AI-15 (math honesty): the `_computing` guard semantics change from blocking to "worker in flight" — re-entrancy analysis must be re-done for the new worker dispatch path; the AI-15 "Preview" badge must appear from the first coarse render and persist until `_apply_domain_and_render` confirms the *full-res* mesh received — not cleared when the coarse render completes. Read `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` §3 rank-8 (CAND-3) challenger MAJOR objections (a) disclaimer timing, (b) CAND-4 strict dependency, (c) topology-misrepresentation floor table — all three must be in the v0 spec.
- AI-2 (Qt-free tests) + AI-6 (parametric pipeline guard): the worker lifecycle / cancel-resubmit has no automated regression guard (AI-2 prohibits pytest-qt) — this is a known gap documented in CONTEXT.md §9; the coarse-LOD path must explicitly skip `surface.typical_ms > 0` surfaces (Hanson) to preserve AI-6. VTK GitLab #18782 mitigation (explicit Python ref retention on output meshes) confirmed in the spike must be replicated in the full worker implementation.

**T-shirt:** L (≤6 weeks; hard prerequisite: e3 spike report shows go)

**Predecessors:** realtime-variety-render-e3

**Acceptance signals:**
- Off-screen render in "coarse mode" (n=coarse_n floor) produces a non-empty, topologically-honest `pv.PolyData` for Kummer (16 nodes visible), Dwork (conifold at ψ≈1 honest), Fermat quartic, and Enriques Fig 4 — confirmed by saving PNGs to `/tmp/e4-coarse-*.png`.
- Off-screen render in "full-res mode" (n=220) produces a visually complete surface for all 4 implicit generators above; the coarse→full-res transition is confirmed by two sequential off-screen renders at the same parameter value.
- AI-15 "Preview" badge: the status bar reads "Preview — NNN ms" during coarse-mode render and the badge is only cleared when the full-res mesh is confirmed received by `_apply_domain_and_render` (not on coarse render completing) — confirmed by reading the status-bar string state in the render pipeline.
- Hanson surfaces are unaffected: off-screen render of each of the 3 Hanson generators at a non-default parameter produces a non-empty PolyData with correct normals (AI-7 — cell normals, not consistent normals).

---

#### `realtime-variety-render-e5` — Numba JIT field-evaluation kernel v0 `[VALUE]`

**Goal:** Replace NumPy-broadcasting field evaluation for the two highest-cost implicit generators (Fermat quartic + Enriques canonical sextic) with `@njit(parallel=True)` kernels (Numba ≥0.60, macOS arm64 `workqueue` threading layer) — targeting a measured ≥5× field-eval speedup and total generate() latency reduction visible in CAND-12 telemetry — with per-generator numerical spot-check tests and a startup warm-up strategy to bound first-call JIT latency to ≤500 ms.

**Slice:** `surfaces.py` (two new `@njit(parallel=True)` kernel functions replacing the NumPy broadcasting in `fermat_quartic_generate` and `enriques_canonical_sextic_generate`; macOS arm64 `workqueue` threading-layer pin via `numba.set_num_threads` or env var; startup warm-up call at first surface selection); `requirements.txt` (add `numba>=0.60,<0.62` with a comment linking to the arm64 wheel confirmation); `tests/` (per-generator numerical spot-check: Numba kernel output vs NumPy reference at a grid of parameter values — pure NumPy/Numba, no Qt; tests must pass within the 4s / 120-test budget).

**INVEST:** 6/6. Independent (the Numba kernels are a pure `surfaces.py` computation change — they slot into the worker thread (e4) without changing the worker dispatch API; the warm-up strategy is independent of the LOD path); Negotiable (v0 scope is Fermat + Enriques canonical only; remaining 6 generators are v1; warm-up can be background-thread if eager startup latency is unacceptable); Valuable (field eval is 41-45% of total generate() latency — Numba cuts the single largest cost component, reducing coarse-mode latency further and full-res latency meaningfully); Estimable (M — Challenger MAJOR points are well-specified and scoped to 2 generators); Small (M: ≤3 weeks); Testable (CAND-12 telemetry before/after Numba shows measurable latency reduction; numerical spot-check tests confirm the kernels are mathematically identical to the NumPy reference for Fermat and Enriques canonical).

**Specialist hints:**
- AI-15 (math honesty) + AI-6 (implicit pipeline): each `@njit` kernel is a manual restructuring of the degree-4 / degree-6 polynomial — a transcription error would produce a visually plausible but mathematically-wrong surface (the existing smoke tests do NOT numerically check field values). The implementation must include per-generator numerical spot-checks against the NumPy reference at ≥3 parameter points each (Fermat quartic: vary `n` exponent; Enriques canonical: vary the sextic coefficients). Read `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` §3 rank-9 (CAND-2) challenger MAJOR objections (a) transcription risk, (b) JIT warm-up, (c) threading-layer pin — all three must be in the v0 spec.
- AI-2 (Qt-free tests): the numerical spot-check tests are pure NumPy + Numba — no Qt, no pyvistaqt, no `MainWindow`. The macOS `workqueue` threading-layer must be confirmed before enabling `parallel=True` to avoid interacting with CAND-4's VTK SMP threading (per challenger CAND-2 objection (c)). First-call JIT latency warm-up must be implemented as a background call at first surface selection (not eager app startup) if the total warm-up exceeds 500 ms.

**T-shirt:** M (≤3 weeks)

**Predecessors:** realtime-variety-render-e4

**Acceptance signals:**
- CAND-12 telemetry shows a measured latency reduction in `surface.generate()` for Fermat quartic and Enriques canonical sextic (target: ≥5× field-eval speedup; total generate() reduction visible in before/after log at `/tmp/e5-numba-timing.txt`).
- Numerical spot-check tests pass: Numba kernel output matches NumPy reference to within floating-point tolerance at ≥3 parameter points each for Fermat quartic and Enriques canonical sextic.
- First-call JIT warm-up ≤500 ms (confirmed by timing the first `surface.generate()` call in the worker thread after warm-up); all subsequent calls show the full speedup.
- `requirements.txt` includes `numba>=0.60,<0.62`; the macOS arm64 `workqueue` threading layer is explicitly set in the implementation; all existing 120 tests still pass within the 4s budget.

---

#### `realtime-variety-render-e6` — VTK Flying Edges marching-cubes replacement `[VALUE]`

**Goal:** Replace `skimage.measure.marching_cubes` with `vtkFlyingEdges3D` via `pv.ImageData.contour([0.0], method='flying_edges')` for all 8 implicit generators — measuring the real Apple-Silicon speedup with CAND-12 telemetry and confirming visual equivalence (including Kummer 16-node shading and Enriques sextic high-curvature regions) via off-screen PNG comparison.

**Slice:** `surfaces.py` (`_marching_cubes_to_polydata` helper — replace `skimage.measure.marching_cubes` call with `pv.ImageData.contour` + `method='flying_edges'`; retain Taubin smoothing + `compute_normals` post-steps; update `requirements.txt` comment if skimage becomes optional); `tests/` (off-screen visual spot-check renders of Kummer + Enriques sextic at default parameters — compare PNG to a skimage-reference baseline saved at `/tmp/e6-baseline-*.png`; pure PyVista, no Qt).

**INVEST:** 6/6. Independent (CAND-1 is explicitly independent of the destination arc — can land any time after e1 provides the telemetry baseline; does not depend on e3/e4/e5); Negotiable (if Kummer or Enriques sextic visual comparison reveals shading regression, revert to skimage MC for that generator only and defer; the epic scope can shrink to N-of-8 generators); Valuable (all 8 implicit surfaces benefit; measured speedup replaces the unverified "1-2 orders of magnitude" Kitware claim with an Apple-Silicon measurement); Estimable (S — adversary scope-adjusted to include visual comparison gate); Small (S: ≤1 week); Testable (CAND-12 telemetry before/after Flying Edges; off-screen PNG visual comparison for Kummer + Enriques sextic saved to `/tmp/e6-flyingedges-*.png`).

**Specialist hints:**
- AI-6 (implicit pipeline) + AI-15 (math honesty): Flying Edges drops scikit-image's analytic gradient normals — the post-step `compute_normals()` call must remain in `_marching_cubes_to_polydata` to restore per-vertex normals via VTK's angle-weighted scheme; confirm via off-screen render that Kummer 16-node shading and Enriques sextic curvature regions are visually equivalent (save comparison PNGs, read them). The oss-trends scout's "2–4× single-thread on Apple Silicon" is the right calibration — do not advertise the Kitware "1–2 orders of magnitude" Intel x86 figure. Read `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` §3 rank-6 (CAND-1) challenger MINOR objections (a) normal quality, (b) benchmark calibration for the full acceptance spec.
- AI-3 (off-screen render verification): visual comparison uses `pv.OFF_SCREEN = True`; do NOT construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen`; save comparison PNGs to `/tmp/` and read them to confirm visual equivalence before the implementation is committed.

**T-shirt:** S (≤1 week)

**Predecessors:** realtime-variety-render-e1

**Acceptance signals:**
- Off-screen renders of all 8 implicit generators at default parameters using Flying Edges produce non-empty `pv.PolyData`; Kummer and Enriques sextic PNG spot-checks show no visible shading regression vs the skimage-MC baseline (`/tmp/e6-baseline-*.png` vs `/tmp/e6-flyingedges-*.png`).
- CAND-12 telemetry shows a measured marching-cubes speedup for ≥1 implicit surface (absolute ms reduction documented at `/tmp/e6-flyingedges-timing.txt`); the Apple-Silicon measurement replaces the unverified Kitware claim in the CAND-12 baseline log.
- All 120 existing tests still pass; `skimage.measure.marching_cubes` is no longer called in `surfaces.py` (or is gated behind a fallback flag if any generator regresses).

<!-- ROADMAP:section:sequence -->
## 7. Prioritization

### 7.1 MoSCoW

| Epic | Tag | Rationale |
|---|---|---|
| `realtime-variety-render-e1` | Must | Eliminates the CRITICAL correctness bug (CAND-5: final drag position silently dropped), establishes the ms telemetry baseline every subsequent epic needs (CAND-12), and hardens the interaction discipline (CAND-13/6/11) — KR1 + KR2 are directly met; this is the dependency root of the entire DAG. |
| `realtime-variety-render-e2` | Must | KR3 explicitly names continuous drag for the Hanson family; S effort; no compute work required (27-38 ms is already fast enough); the fastest route to a visible real-time result — the adversary calls it "the easiest win in the entire roadmap". |
| `realtime-variety-render-e3` | Must | ENABLER that gates e4 and e5 (the destination arc for KR4); without the spike resolving pyvistaqt #793 + VTK #18782, the background-thread epic cannot be sized or safely started; a 0.5-week spike that unlocks L+M downstream work. |
| `realtime-variety-render-e4` | Should | Delivers KR4 (continuously-updating implicit surfaces during drag) but is gated by e3; L effort; high value, but the spike outcome determines feasibility — shape for Next, not Now. |
| `realtime-variety-render-e5` | Should | Cuts the single largest cost component (field eval 41-45%) via Numba JIT; M effort; downstream of e4; important for the full destination arc but not needed for the minimum viable Objective. |
| `realtime-variety-render-e6` | Could | Flying Edges is independent and S effort, but not named in any KR and delivers a measured speedup only after CAND-12 telemetry lands; nice-to-have that can slip without blocking the Objective. |

**Must cap:** 3/6 = 50% (cap: 60%) — *script-validated*

### 7.2 RICE rank (Musts only)

| Rank | Epic | R | I | C | E | RICE |
|---|---|---|---|---|---|---|
| 1 | `realtime-variety-render-e3` | 10 | 3 | 80 | 0.5 | 48.00 |
| 2 | `realtime-variety-render-e1` | 10 | 2 | 80 | 1 | 16.00 |
| 3 | `realtime-variety-render-e2` | 3 | 3 | 50 | 1 | 4.50 |

*Confidence defaults to 50% where no evidence exists. Defaults: e2 (RICE C=50% — final-report explicitly prices CAND-8 at C=0.5; 1 brief, no off-screen measurement).*

<!-- ROADMAP:section:lanes -->
## 8. Now / Next / Later

### Now (fully spec'd)

#### `realtime-variety-render-e1` — Quick-wins scaffolding bundle

**Stories:**

**`realtime-variety-render-e1-s1` — Add perf_counter telemetry and surface ms in status bar** (S)

Given the app is running and any surface is selected,
When `_render_current` completes a `surface.generate()` call,
Then the status bar displays a string matching `NNN ms` (e.g. `342 ms`) and a `time.perf_counter()` log line is written to stdout containing the surface name and elapsed ms — confirmed by an off-screen render that reads `plotter.renderer` state and checks the status-bar text is non-empty and ends with `ms`.

Specialist: AI-9 (re-entrancy guard) — the timing probe must be placed outside the `self._computing` guard block so it fires on every completed render, not only on the first of a burst; read CONTEXT.md §4.4 for the existing `_computing` + `processEvents` call site before placing the bracket.

**`realtime-variety-render-e1-s2` — Upgrade re-entrancy guard to queue-latest semantics** (XS)

Given the app is running and an implicit surface is selected,
When two rapid `_render_current` calls arrive while the first render is in flight (simulated by calling `_render_current` twice in quick succession in an off-screen test harness),
Then the second call sets `_pending_render = True` and a `QTimer.singleShot(0, ...)` catch-up fires after the first render completes — confirmed by an off-screen render at the final parameter value showing a non-empty `pv.PolyData` (i.e., the final drag position is NOT silently dropped).

Specialist: AI-9 (re-entrancy) — the `_pending_render` flag and the `QTimer.singleShot(0, ...)` catch-up must live inside the same `finally` block structure documented in CONTEXT.md §4.4; read the final-report §3 rank-1 (CAND-5) 2-line spec verbatim before implementing.

**`realtime-variety-render-e1-s3` — Lower Fermat quartic and Enriques Fig 4 interactive grid caps to n=220** (XS)

Given `surfaces.py` is the target file,
When the adaptive `n` cap for Fermat quartic is lowered from 260 to 220 and the Enriques Fig 4 hardcoded `n=260` is changed to `n=220`,
Then off-screen renders of both surfaces at default parameters saved to `/tmp/cand13-n220-fermat.png` and `/tmp/cand13-n220-enriques4.png` show no perceptible quality regression vs the n=260 baseline (spot-check: both PNGs are non-empty and visually complete surfaces), AND the `[MUST]` assumption from §4 ("quality delta imperceptible at viewport zoom") is confirmed or the cap is raised to n=240 with a note.

Specialist: AI-15 (math honesty) — confirm the n=220 surface is topologically identical to the n=260 surface for Fermat quartic (smooth field, no near-singularities) before committing; the spot-check PNG read is the acceptance gate, not a subjective call.

**`realtime-variety-render-e1-s4` — Wire shared QTimer debounce to ParametersPanel and ParameterGridPanel** (S)

Given a new `ui_helpers.py` module (or inline utility) provides a shared `QTimer`-based debounce with an 80 ms default interval,
When a `valueChanged` signal fires on any slider in `ParametersPanel` or any grid-dot drag in `ParameterGridPanel`,
Then the debounce absorbs intermediate ticks and the full-res render fires at most once per 80 ms during continuous drag — confirmed by a pure-Python unit test of the timer logic that shows 10 rapid calls produce exactly 1 deferred callback — AND the release path bypasses the debounce and fires a direct full-res render immediately.

Specialist: AI-9 (re-entrancy) — verify that the `QTimer.singleShot` used in s2's catch-up and the debounce timer in s4 do not interfere; both must respect the `self._computing` guard; read CONTEXT.md §8.5 (re-entrancy from `processEvents`) before wiring.

**`realtime-variety-render-e1-s5` — Add clipped-mesh cache alongside _raw_mesh** (XS)

Given `_apply_domain_and_render` currently re-runs `clip_to_domain` (a full mesh copy + scalar-tag + clip) on every render call even when only an appearance setting changed,
When a `_clipped_mesh` slot is added alongside `_raw_mesh` and invalidated only on raw-mesh change OR domain-settings change,
Then an off-screen render of Fermat quartic at default parameters with a domain-radius change followed by an appearance-only change confirms `clip_to_domain` is NOT re-called on the appearance-only render — confirmed by a pure-Python unit test asserting the clip-call count stays at 1 for two sequential renders where only the color changes.

Specialist: AI-10 (raw-mesh cache invariant) — the new `_clipped_mesh` cache must NOT regenerate the raw mesh on domain-radius slider change (AI-10 invariant); invalidation logic must be symmetric with the existing `_raw_mesh` single-slot cache; read CONTEXT.md §4.4 clip-cache pattern before implementing.

---

#### `realtime-variety-render-e2` — Hanson parametric continuous-drag fast-path

**Stories:**

**`realtime-variety-render-e2-s1` — Add typical_ms field to Surface dataclass and set values for Hanson generators** (XS)

Given `surfaces.py` contains the `Surface` dataclass (not frozen),
When a `typical_ms: int = 0` field is added and the three Hanson parametric generators (quintic, cubic torus, asymmetric) have their measured generation times set (e.g. 27, 33, 38 ms respectively),
Then a pure-Python dataclass unit test confirms: all 3 Hanson generators have `typical_ms > 0`; all implicit generators (Fermat, Kummer, Enriques x4, Dwork) have `typical_ms == 0`; the field addition has not broken any of the 120 existing tests.

Specialist: AI-8 (Surface/ParamSpec dataclass contract) — confirm the field-addition pattern against `surfaces.py` before implementing; verify `typical_ms: int = 0` default does not clash with any existing field; read final-report §3 rank-4 (CAND-8) challenger CC-3 note on `typical_ms` vs `fast: bool` preference.

**`realtime-variety-render-e2-s2` — Wire typical_ms fast-path to bypass debounce and render at every tick** (S)

Given `realtime-variety-render-e1` has shipped (debounce utility and queue-latest guard are in place) and `typical_ms` fields are set on the 3 Hanson generators,
When a researcher drags any Hanson-family slider (any of the 3 generators),
Then the render dispatch checks `surface.typical_ms > 0` and `surface.typical_ms <= 80` and fires a direct render at every `valueChanged` tick without waiting for debounce timeout — confirmed by an off-screen render at a non-default Hanson parameter value (e.g. quintic with `n=5`) that produces a non-empty, visually correct `pv.PolyData` with correct normals (`cell_normals=True, consistent_normals=False, auto_orient_normals=False` per AI-7), AND the CAND-12 telemetry log shows round-trip ≤ 80 ms.

Specialist: AI-6 (implicit vs parametric pipeline guard) — the `typical_ms`-based fast-path dispatch must NOT enable the coarse-LOD path for Hanson surfaces (those surfaces already skip marching cubes and Taubin smoothing); when e4's CAND-3 is implemented later, its coarse-path guard must check `surface.typical_ms > 0` and skip; read final-report §3 rank-4 (CAND-8) and challenger CC-3 correction on the CAND-4 dependency (CAND-8 does NOT depend on CAND-4).

### Next (shaped)

#### `realtime-variety-render-e4` — Background-thread worker + coarse-preview LOD

Move `surface.generate()` off the Qt GUI thread onto a `QRunnable`/`QThread` worker (CAND-4) and implement the two-pass coarse-preview LOD pipeline (CAND-3) — delivering a continuously-updating coarse-grid preview during drag with a persistent "Preview" status-bar badge (AI-15) and a full-resolution snap on release. Prerequisite: e3 spike report shows go. T-shirt L (≤6 weeks). Predecessors: e3 (spike).

Full epic body including INVEST check, specialist hints (AI-9 re-entrancy semantics change, AI-15 badge timing, AI-2 test gap, AI-6 coarse-path guard), and acceptance signals is in section 6.3. No story decomposition at this horizon.

#### `realtime-variety-render-e6` — VTK Flying Edges marching-cubes replacement

Replace `skimage.measure.marching_cubes` with `vtkFlyingEdges3D` via `pv.ImageData.contour([0.0], method='flying_edges')` for all 8 implicit generators — measuring the real Apple-Silicon speedup with CAND-12 telemetry and confirming visual equivalence via off-screen PNG comparison on Kummer + Enriques sextic. Independent of e3/e4/e5 spike path; can ship any time after e1's telemetry baseline is in place. T-shirt S (≤1 week). Predecessors: e1.

Full epic body including INVEST check, specialist hints (AI-6 + AI-15 normal quality, AI-3 off-screen verification), and acceptance signals is in section 6.3. No story decomposition at this horizon.

### Later (outcomes only)

- `realtime-variety-render-e5` — Replace NumPy field evaluation for Fermat quartic + Enriques canonical sextic with `@njit(parallel=True)` Numba kernels targeting ≥5× field-eval speedup, with per-generator numerical spot-check tests and a macOS arm64 `workqueue` threading-layer pin; v0 scope only (2 of 8 generators). Prerequisite: e4 ships and Numba arm64 spike passes.

<!-- ROADMAP:section:spikes -->
## 9. Spike lane

- **Spike: macOS background-thread safety (pyvistaqt #793 + VTK #18782)** (≤3 days) — validates `[MUST]` from section 4: "pyvistaqt issue #793 does NOT hang on the current dev machine's installed PySide6 version, OR the requirements.txt pin can be tightened to PySide6 <6.10 without breaking other functionality" AND "VTK + QThread are safe to use concurrently on macOS arm64 — pv.PolyData objects can be constructed on a worker thread and handed to the main thread via a Qt.QueuedConnection signal without a GC-triggered crash (VTK GitLab #18782)". Output: spike report at `.claude/notes/roadmaps/realtime-variety-render/spike-cand4-thread-safety.md` documenting PySide6 version, hang reproduction outcome, requirements.txt pin recommendation, and VTK #18782 mitigation confirmation. Blocks: `realtime-variety-render-e4`.

- **Spike: Numba arm64 availability and stability** (≤2 days) — validates `[MUST]` from section 4: "Numba @njit(parallel=True) is available and stable on macOS arm64 (Numba 0.60+) with the workqueue threading layer (not unguarded TBB) — Apple-Silicon wheels confirmed on PyPI but not validated against this specific app's deps". Output: spike report at `.claude/notes/roadmaps/realtime-variety-render/spike-numba-arm64.md` documenting the installed Numba version, a minimal `@njit(parallel=True)` kernel run against a small polynomial grid, first-call JIT latency measured, and threading-layer confirmation. Blocks: `realtime-variety-render-e5`.

<!-- ROADMAP:section:tracking -->
## 10. Tracking

*Populated by `--gh-issues` flag in Phase 4.*

| Epic / Story | GH Issue | Status |
|---|---|---|

<!-- ROADMAP:section:handoff -->
## 11. Execution handoff

First Now-lane epic: `realtime-variety-render-e1`.

Handoff target: **CONTEXT.md section 6 — the 5-phase implementation pipeline**:

1. **Math research / code archeology** — two parallel Opus agents (research-A: equations / sources / cross-verified references; research-B: visual / code-archeology / library options). Output: a concrete report keyed to this epic's specialist hints.
2. **Implementation + off-screen render verify** — synthesize 4 figures (or equivalent unit of work for non-variety epics), implement, render with `pv.OFF_SCREEN = True` to `/tmp/*.png`, Read the images. Single commit on `main`.
3. **Adversarial review** — Sonnet, six categories (libraries, engineering, gaps, docs, bugs, testing). Read-only; aim for ~10 findings.
4. **Remediation** — Sonnet, grouped MUST FIX / SHOULD FIX / SKIP. Single commit; new tests for new behavior.
5. **UI/UX pass** — Sonnet, two-phase brief (critique 5-10 findings THEN implement 4-7 of them). All existing tests still pass before committing.

Per-epic artifacts produced by the pipeline land under `.claude/notes/` (not in this roadmap doc); commits are direct to `main` per the single-developer cadence documented in CONTEXT.md section 12. This roadmap is the source of truth for *what to build*; the implementation pipeline is the source of truth for *how it landed*.

---

*This roadmap was produced by `/roadmap`. Update directly with edits; for major restructures, re-invoke `/roadmap realtime-variety-render` and the orchestrator will resume at the first unpopulated section.*
