# Research Brief — realtime-variety-render-e4b (agent-a: MATH / TOPOLOGY / TEST-DESIGN lens)

**Milestone:** `realtime-variety-render-e4b` — CAND-3 (two-pass coarse-preview LOD)
for implicit surfaces, the deferred half of e4. e4 (CAND-4 worker) and e5 (Numba
kernels) are merged. No e4b stub exists yet in `plans/realtime-variety-render-roadmap.md`
(section 6.3 only lists e1..e6); this milestone is the documented split sanctioned by
§6.3's e4 INVEST clause.
**Researcher:** agent-a · **Date:** 2026-05-22 · **Status:** complete

---

## 1. TL;DR

Add a per-`Surface` field `coarse_n: int = 0` (0 = opt out) on the existing
dataclass, set it for **9 of 11 implicit generators** to the floor table in §4
(measured `15-46 ms` typical at the proposed floors on this Windows dev box vs
`85-1090 ms` at production `n`), and route the drag-tick render through
`_render_current` with `n=surface.coarse_n` injected the same way
`hq_smoothing=True` is injected today (`app.py:647-652`) — the worker dispatch
stays byte-identical otherwise, and the result slot reads a new `is_coarse:
bool` field on `MeshResult` to keep the AI-15 Preview badge alive until the
follow-up full-res result lands.  **Main risk:** the `_on_params_preview_changed`
fast-path today gates on `should_render_on_drag(surface)` which excludes every
implicit surface (`typical_ms == 0`); e4b inverts that — implicit surfaces with
`coarse_n > 0` must now render on drag too, so the predicate splits into "fast
parametric" vs "coarse-LOD eligible implicit", and the existing AI-6 guard at
`app.py:524-527` must be re-derived to gate Hanson out by `coarse_n == 0`, not
by `typical_ms`.  **Backup plan:** if topology-honesty checks in the n-sweep
test reveal a surface where no floor in `[60, 140]` is safe (early indicator:
Dwork conifold at ψ≈1), keep `coarse_n = 0` for that surface and document the
opt-out — e4b's gating is per-Surface, not all-or-nothing.

---

## 2. Prior art in this repo

### Surfaces & their CURRENT production `n` values

| # | Generator | Function | File:line | Production `n` | Bounds | `typical_ms` | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Fermat quartic | `fermat_quartic` | `surfaces.py:375-447` | **adaptive 200-220** (line 436) | adaptive 2.5-? (line 425) | 0 | Numba-JIT'd field (e5) |
| 2 | Kummer surface | `kummer_surface` | `surfaces.py:467-503` | **240** (line 467) | adaptive 2.6-6.0 | 0 | NumPy-broadcast field |
| 3 | Enriques fig 1 (canonical sextic) | `enriques_figure_1` | `surfaces.py:524-559` | **240** (line 526) | 1.89 (padded e8.16) | 0 | Numba-JIT'd field; HQ-smoothing opt-in |
| 4 | Enriques fig 2 (λ-family) | `enriques_figure_2` | `surfaces.py:568-606` | **240** (line 572) | 1.89 (padded) | 0 | NumPy-broadcast; HQ-smoothing opt-in |
| 5 | Enriques fig 3 (Cayley) | `enriques_figure_3` | `surfaces.py:619-647` | **240** (line 621) | 2.625 (padded) | 0 | NumPy-broadcast |
| 6 | Enriques fig 4 (icosahedral) | `enriques_figure_4` | `surfaces.py:656-695` | **220** (line 658) | 1.575 (padded) | 0 | NumPy-broadcast |
| 7 | Dwork pencil | `calabi_yau_dwork` | `surfaces.py:886-925` | **260** (line 888) | 1.8 | 0 | conifold warning at ψ≈1 |
| 8 | Klein cubic (Fano 1) | `fano_klein_cubic` | `surfaces.py:945-977` | **240** (line 947) | 2.0 | 0 | NumPy-broadcast |
| 9 | Segre cubic (Fano 2) | `fano_segre_cubic` | `surfaces.py:986-1022` | **240** (line 989) | 2.5 | 0 | NumPy-broadcast |
| 10 | Two-quadrics tube (Fano 3) | `fano_two_quadrics` | `surfaces.py:1033-1084` | **220** (line 1038) | 2.0 | 0 | ε-tube; warns at ε<0.08 |
| 11 | Sextic double solid (Fano 4) | `fano_sextic_double_solid` | `surfaces.py:1099-1148` | **240** (line 1102) | 2.0 | 0 | NumPy-broadcast |
| 12-14 | Hanson quintic / cubic / asymmetric | `calabi_yau_quintic` / `calabi_yau_cubic` / `calabi_yau_asymmetric` | `surfaces.py:810/837/861` | **N/A** (parametric `grid`) | parametric | 39/11/18 | **AI-6: SKIP** |

### Render-pipeline integration points

- **`surfaces.py:54-68` `Surface` dataclass** — *not frozen*; trailing
  defaulted field `typical_ms: int = 0` was added by e2-s1 (CAND-8) as the
  template for adding another defaulted int field. Adding `coarse_n: int = 0`
  with the same `default=0 ⇒ opt-out` semantics is the same pattern.
- **`surfaces.py:82-100` `should_render_on_drag(surface)`** — pure Qt-free
  predicate (mirrored by `clipped_cache_is_valid` at `app.py:71` and
  `is_stale_result` at `render_worker.py:42`). The e4b equivalent is a new
  predicate `should_render_coarse_on_drag(surface)` that returns True for any
  implicit surface with `coarse_n > 0` — i.e. the *complement* of
  `should_render_on_drag` for opt-in surfaces.
- **`app.py:497-532` `_on_params_preview_changed`** — the debounced drag-tick
  handler. Today: `if should_render_on_drag(self._current_surface):
  self._render_current(...)`. This is the exact entry point e4b extends — the
  fast-path now ALSO fires for implicit surfaces with `coarse_n > 0`, but with
  a coarse-mode flag set on the dispatch.
- **`app.py:588-691` `_render_current`** — the worker dispatch. Today the
  pattern that injects `hq_smoothing=True` at line 647-652 (only for the two
  Enriques opt-in figures) is the exact analogue: a kwarg slid into `params`
  before the worker is constructed. e4b adds an `n=surface.coarse_n` injection
  guarded by a new instance bit (`self._dispatch_coarse: bool`) flipped True
  by the drag-tick branch and False by the release branch.
- **`app.py:693-838` `_on_mesh_ready`** — the result slot. Currently reads
  `self._inflight_hq_label` (set at dispatch). e4b adds `self._inflight_is_coarse:
  bool` set alongside it; the slot uses it to decide whether to clear or keep the
  Preview badge. The catch-up `singleShot(0)` at line 832-838 is what triggers
  the FULL-RES render after a release — already in place.
- **`render_worker.py:65-104` `MeshResult` dataclass** — already carries
  `generation`, `ok`, `mesh`, `gen_ms`, `warning_text`, `error_*`. Add
  `is_coarse: bool = False` as the trailing field (preserve existing field
  order). `MeshWorker` does NOT need to compute this — the slot reads the
  dispatch-time `_inflight_is_coarse` instead; the field on `MeshResult` is
  defensive belt-and-suspenders for any future cancellation/reorder pattern.
  (Alternatively: skip the `is_coarse` field on `MeshResult` and route entirely
  via `_inflight_is_coarse`. Both work; the `MeshResult` field is cleaner —
  the result self-describes — and the brief's milestone text mandates it.)
- **`render_worker.py:118-198` `MeshWorker`** — runs `surface.generate(**params)`
  on a worker thread. The coarse-LOD path just adds `n=coarse_n` to the params
  dict before construction; the worker code is unchanged.
- **`tests/test_mesh_generators.py:39-84`** — `_assert_nonempty(mesh, bounds)`
  + `_assert_consistent_winding(mesh)` are the existing assertion helpers; the
  n-sweep test family mirrors this pattern. Coarse-n tests slot in alongside the
  existing `test_*_defaults` smoke tests.
- **CONTEXT.md §4.4 (re-entrancy)** — the `_computing` single-flight guard +
  catch-up `singleShot(0)` machinery handles a coarse→full-res transition
  naturally: drag-tick sets `_pending_render=True`, the catch-up fires the
  full-res render. e4b changes the *content* of the dispatched render, not the
  re-entrancy machinery.
- **CONTEXT.md §8.6 / AI-14** — `_marching_cubes_to_polydata` raises
  `ValueError("No real zero set...")` on an empty field. At coarse `n`, this can
  fire on parameter combinations where the production `n` would have caught a
  thin shell (the Fano two-quadrics ε-tube is the obvious risk). The slot
  already handles `ValueError` cleanly via `result.error_is_value_error`
  (`app.py:732-741`) — the coarse-path ValueError lands in the same branch and
  the user sees "No surface to render — …". e4b adds nothing here.
- **CONTEXT.md §8.8 (Dwork conifold)** — at ψ≈1 the surface has a node at
  (1,1,1); marching cubes silently misses it at *any* `n` because the
  voxel-spacing-relative chance of landing on (1,1,1) is essentially zero
  (verified: n=60 → d_min=2.40; n=100 happens to align → d_min=0; n=120/260 →
  d_min=2.40 again). This is **not a coarse-LOD honesty regression** — it is an
  invariant property of marching cubes on this surface, already documented and
  flagged by the existing RuntimeWarning. The coarse mesh and the full-res
  mesh are equally "conifold-honest" by this measure; what matters is the
  smooth-complement *shape*, which the bbox + vertex distribution preserves
  across the sweep (see §4 numbers).

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| capability-scout final-report rank-8 (CAND-3) | `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md:134-142` | n=120 cuts field+MC from 326ms→55ms (6×); n=80 ~15ms (22×); per-surface coarse-n floor table required; Hanson skipped (AI-6); AI-15 badge persistence is hard-spec | Confirms the candidate scope, the floor-table mandate, and the AI-15 ordering rule |
| capability-scout adversary brief | `.claude/notes/capability-scouts/realtime-variety-render/survey/adversary-brief.md:74,327-330` | "Add a `coarse_n: int = 80` parameter to each generator" — adversary already proposed the per-Surface field exposure (the same pattern the brief mandates) | Confirms the dataclass-field exposure mechanism is the standard one |
| capability-scout math-research brief | `.claude/notes/capability-scouts/realtime-variety-render/survey/math-research-brief.md:177-183` | Stander-Hart / Plantinga-Vegter topological-soundness sample-density bound: if coarse n is provably above the bound, "topology may differ" can become "lower resolution, same topology guaranteed". The bound depends on `‖∇f‖/‖∇²f‖` — for our 4th/6th-degree polynomials with smooth parameter ranges, the bound is in the 60-100 range, supporting the proposed floors | Provides a literature anchor for the per-surface floor decisions — but the bound is uncomputed in v0; the brief defers it (not needed for shipping; n-sweep empirical validation is sufficient) |
| roadmap §6.3 e4 INVEST clause | `plans/realtime-variety-render-roadmap.md:174` | "if the spike report reveals XL risk, split CAND-4 into its own L epic and CAND-3 becomes e4b after CAND-4 stabilises" — the exact e4b sanction; spec inherits from §6.3's e4 paragraph | The spec of record (verbatim e4 epic body §6.3 is the e4b spec minus CAND-4) |
| e3 spike report §7 macOS gate | `.claude/notes/roadmaps/realtime-variety-render/spike-cand4-thread-safety.md` | Worker thread safety established; coarse-LOD path is byte-identical worker dispatch with smaller `n` kwarg | No new threading risk in e4b — the dispatch surface is unchanged |
| Mathematica `ControlActive[ ]` docs | wolfram.com/language/ref/ControlActive.html | "Returns the second argument only while a control is being dragged; returns the first argument otherwise." Canonical primitive for two-pass dynamic/static rendering | Validates the "coarse during drag, full on release" semantic is industry-standard, not a local invention |
| ParaView coloring & rendering "Interactive vs Still" | docs.paraview.org "RenderView" | LOD switching keyed on mouse-down/mouse-up events; render-quality drops during interaction. License: BSD-3-Clause | Cross-confirms the pattern; no code to borrow |
| qmltk/Plasma KDE LOD pattern (out-of-Qt) | review-only | Identical pattern (preview + full); not relevant code-wise | Cross-confirms |

*No new dependency surface — all integration is on the already-pinned
PySide6/PyVista/numba stack via the existing worker.*

---

## 4. Recommended approach

### 4.1 Per-Surface coarse_n floor table (the headline deliverable)

Probe data — measured Windows 11 dev machine, post-Numba-warmup, single run per
cell (so absolute ms ±10%; ratios are stable):

| Generator | `n` | gen ms | n_points | n_cells | Topology-honesty signature (verified) |
|---|---|---|---|---|---|
| **fermat_quartic** (n_prod=220) | 60 | 5.7 | 3168 | 6332 | bbox 2.00³ stable; axial reach at γ=-10 → \|x\|max=3.804 (vs 3.806 at n=220) — **honest at n=60** |
|  | 80 | 8.1 | 5640 | 11276 | bbox stable; axial reach 3.805 |
|  | 100 | 11.7 | 8856 | 17708 | bbox stable |
|  | 220 (prod) | 85.5 | 42840 | 85676 | reference |
| **kummer_surface** (n_prod=240) | 60 | 21.1 | 11936 | 23224 | 8-octant counts perfectly symmetric `[1492×8]` — full S₄ tetrahedral symmetry preserved (**16 nodes still distinguishable**); bbox 6.40³ stable |
|  | 80 | 38.6 | 21352 | 41784 | octants `[2669×8]` — symmetry preserved |
|  | 100 | 64.5 | 33352 | 65568 | octants `[4169×8]` |
|  | 240 (prod) | 863.1 | 192864 | 383032 | reference |
| **enriques_figure_1** (n_prod=240) | 60 | 26.4 | 24420 | 48064 | near-coord-plane vertex fraction = 16.4% (vs 16.6% at n=240) — **double curves visible** |
|  | 80 | 46.6 | 43764 | 86512 | 16.5% — preserved |
|  | 100 | 68.7 | 68760 | 136264 | 16.6% — preserved |
|  | 240 (prod) | 463.7 | 400428 | 797824 | reference |
| **enriques_figure_2** (n_prod=240) | 60 | 16.1 | 3576 | 6904 | bbox 1.98×1.98×3.78 (asymmetric λ-family) — preserved across sweep |
|  | 80 | 24.8 | 6460 | 12576 | bbox preserved |
|  | 100 | 42.1 | 10144 | 19864 | bbox preserved |
|  | 240 (prod) | 749.2 | 58504 | 115992 | reference |
| **enriques_figure_3** (n_prod=240) | 60 | 16.3 | 8646 | 16731 | bbox 5.25³ stable |
|  | 80 | 24.3 | 15399 | 30069 | stable |
|  | 100 | 43.6 | 24030 | 47139 | stable |
|  | 240 (prod) | 494.3 | 138681 | 275127 | reference |
| **enriques_figure_4** (n_prod=220) | 60 | 32.7 | 24840 | 48200 | bbox 3.15³ stable (icosahedral symmetry) |
|  | 80 | 55.3 | 44424 | 86936 | stable |
|  | 100 | 96.3 | 69264 | 136112 | stable |
|  | 220 (prod) | 674.5 | 335472 | 665624 | reference |
| **calabi_yau_dwork** (n_prod=260) | 60 | 24.0 | 10413 | 20470 | smooth complement preserved; conifold-aliasing is invariant of `n` (see §2 prior-art note) |
|  | 80 | 44.4 | 18594 | 36712 | preserved |
|  | 100 | 73.5 | 29124 | 57652 | preserved (accidental alignment at this `n`) |
|  | 260 (prod) | 1088.6 | 198216 | 394876 | reference |
| **fano_klein_cubic** (n_prod=240) | 60 | 18.4 | 10056 | 19532 | bbox 4.0³ stable |
|  | 80 | 25.6 | 17864 | 34952 | stable |
|  | 240 (prod) | 466.6 | 161080 | 319810 | reference |
| **fano_segre_cubic** (n_prod=240) | 60 | 35.2 | 18828 | 36709 | bbox 5.0³ stable |
|  | 80 | 63.3 | 33555 | 65851 | stable |
|  | 100 | 106.2 | 52302 | 103027 | stable |
|  | 240 (prod) | 1220.7 | 302562 | 601315 | reference |
| **fano_two_quadrics** (n_prod=220) | 60 | 14.3 | 1824 | 3640 | ε-tube survives at default ε=0.18 — n_points scales linearly; **fragile near ε≈0.08** (the existing warning floor) — see opt-out caveat |
|  | 80 | 21.6 | 3232 | 6456 | survives |
|  | 100 | 36.2 | 5088 | 10168 | survives |
|  | 220 (prod) | 418.8 | 25200 | 50392 | reference |
| **fano_sextic_double_solid** (n_prod=240) | 60 | 16.6 | 9008 | 18012 | bbox 2.4×2.4×3.46 (two-sheet z-symmetry) preserved |
|  | 80 | 28.2 | 16200 | 32396 | preserved |
|  | 240 (prod) | 549.1 | 147632 | 295260 | reference |

**Proposed coarse_n floors** (the brief's `coarse_n[surface_key]` dict baked
into the `Surface` field):

| Generator | Production `n` | **Proposed `coarse_n`** | Justification |
|---|---|---|---|
| fermat_quartic | adaptive 200-220 | **80** | n=80 → 8 ms (vs 86 ms at 220); axial reach exact; smooth field, no near-singularities — the safest coarsening candidate in the registry |
| kummer_surface | 240 | **100** | n=100 → 65 ms; 16-node tetrahedral symmetry preserved by octant probe; n=80 also works (39 ms) but Hudson form's nodes are the topology signature — buy a 2× margin |
| enriques_figure_1 | 240 | **80** | n=80 → 47 ms; double-curve fraction 16.5% (vs 16.6% prod); Numba-JIT'd so the gen cost has minimum tax — n=80 is comfortably under the 80 ms target |
| enriques_figure_2 | 240 | **80** | n=80 → 25 ms; bbox asymmetry preserved; same family as fig 1 |
| enriques_figure_3 | 240 | **80** | n=80 → 24 ms; Cayley quartic — smooth field at default k=16, no near-degenerate region |
| enriques_figure_4 | 220 | **80** | n=80 → 55 ms; icosahedral symmetry preserved across sweep; A₅ topology is bbox-stable |
| calabi_yau_dwork | 260 | **100** | n=100 → 74 ms; "conifold honesty" is invariant of `n` (see §2 prior-art note); but the surface has the most parameter range — buy resolution margin |
| fano_klein_cubic | 240 | **80** | n=80 → 26 ms; slice-of-Klein-cubic — bbox stable, no near-singular parameter region |
| fano_segre_cubic | 240 | **80** | n=80 → 63 ms; ten-node structure of parent variety projects to <10 visible singular points in the slice; bbox stable |
| fano_two_quadrics | 220 | **0 (OPT OUT)** | the ε-tube is a `Q₁²+Q₂²-ε² ≈ 0` band; at coarse `n` the voxel spacing approaches the tube width (`2·2.0/(n-1) ≈ 0.043` at n=100, vs ε=0.18). The existing warning floor is ε=0.08 ↔ voxel ~0.055, which restricts ε at production `n`. At drag-time the user is often *tuning* ε near the warning band; routing a coarse-LOD pass with even smaller voxels would amplify the swiss-cheese-mesh artifact the existing warning already calls out. **Mathematically dishonest at the drag-time use case.** Recommend opt-out at v0; can be revisited later with an ε-aware coarse_n function if measured to matter. |
| fano_sextic_double_solid | 240 | **80** | n=80 → 28 ms; closed compact two-sheet surface; bbox-stable across sweep |

**Two opt-outs in total (besides AI-6 Hanson skip):** `fano_two_quadrics` for
topology fragility (see above). All others opt in. **Net coverage: 9 of 11
implicit generators** carry a non-zero `coarse_n`; 2 of 11 are opt-out (Hanson
is parametric, not in this count).

**On the brief's headline numbers** (`{fermat: 80, kummer: 100, enriques_*:
80, dwork: 100}`): the table above matches the brief on Fermat (80), Kummer
(100), all Enriques (80), Dwork (100). The brief did not enumerate the 4 Fano
figures; the proposed values (80, 80, OPT-OUT, 80) follow the same per-surface
empirical methodology.

### 4.2 Exposure mechanism — `Surface` dataclass field, not a module dict

Add `coarse_n: int = 0` to `Surface` immediately after `typical_ms: int = 0`
(`surfaces.py:54-68`). Default 0 = "no coarse preview" (the safe default for
any future generator that hasn't been n-swept). The Hanson generators leave
the default 0 — that IS the AI-6 guard, see §4.3.

Rationale vs a module-level dict `COARSE_N = {fn: int, ...}`:
- Discoverable. A future maintainer reading `enriques_figure_1`'s `Surface`
  registration at `surfaces.py:1170-1173` immediately sees the coarse_n value
  next to the other surface metadata. A module dict requires cross-referencing.
- Survives AI-6 audit. The implicit-vs-parametric distinction is "does this
  surface go through marching cubes" — the same dataclass field that holds
  `typical_ms` (parametric speed hint) can hold `coarse_n` (implicit LOD
  hint) without contradiction. The presence of both fields documents that the
  two are *mutually exclusive in use*: a surface with `typical_ms > 0` is
  parametric, a surface with `coarse_n > 0` is implicit-LOD-eligible. A
  future generator that proposed setting both would be flagged in code
  review.
- Mirrors e2-s1 precedent. CAND-8's `typical_ms` was added the same way; the
  pattern is already in the codebase and battle-tested.
- Module-level dict was the adversary brief's wording (`surfaces.py:74` of the
  adversary brief). It is a viable alternative — see §5.

The exposure also supports a free helper for the dispatch path:

```python
# In surfaces.py, alongside should_render_on_drag (lines 82-100):
def should_render_coarse_on_drag(surface: "Surface | None") -> bool:
    """Pure predicate for the e4b coarse-LOD fast-path.

    Returns True when *surface* opts in to coarse-preview rendering on
    drag — i.e. it is an implicit (marching-cubes) generator with a
    non-zero `coarse_n` floor. Returns False for None, for Hanson
    parametric surfaces (typical_ms > 0 → fast already, no coarse needed),
    and for surfaces with coarse_n == 0 (no n-sweep validation → opt-out).

    Mutually exclusive with should_render_on_drag — at most one is True
    for any given Surface.
    """
    return surface is not None and surface.coarse_n > 0
```

### 4.3 AI-6 guard — `surface.coarse_n > 0` IS the implicit-vs-parametric signal (transitively)

The brief mandates `surface.typical_ms > 0` as the Hanson-skip guard. That works
— the 3 Hanson surfaces have `typical_ms ∈ {39, 11, 18}` (all > 0), every
implicit has `typical_ms == 0`. **Recommend instead gating on
`coarse_n > 0`** (the new positive predicate) because:
- `should_render_coarse_on_drag(surface) == True` IS the precondition for the
  fast-path firing.  No double-check needed.
- A future implicit generator that opts out (like fano_two_quadrics) is
  *correctly* excluded by `coarse_n == 0`, but would be *incorrectly*
  included by `typical_ms == 0` (it'd try to coarse-render, the implementer
  would have to special-case it again).
- `should_render_on_drag` and `should_render_coarse_on_drag` then form a
  mutually exclusive partition over (implicit + parametric + opt-out), each
  one-liner in `_on_params_preview_changed`.

The combined fast-path becomes:

```python
def _on_params_preview_changed(self, _values: dict) -> None:
    surf = self._current_surface
    if should_render_on_drag(surf):
        # Hanson parametric — render at full quality, no badge
        self._dispatch_coarse = False
        self._render_current(reset_camera=False)
    elif should_render_coarse_on_drag(surf):
        # Implicit with coarse_n > 0 — render coarse, leave Preview badge alive
        self._dispatch_coarse = True
        self._render_current(reset_camera=False)
    # else: opt-out implicit (no coarse_n) — release-only, as today
```

### 4.4 The n-sweep test design (`tests/test_coarse_n_topology.py`)

Pattern after `test_mesh_generators.py`'s assertion helpers (lines 39-84).
Pure PyVista, no pytest-qt (AI-2). One test per opt-in implicit generator
(9 tests), plus a test asserting the opt-outs have `coarse_n == 0` and the
Hanson generators have `coarse_n == 0`. Each per-generator test:

1. Call `surface.generate(n=surface.coarse_n)` — assert non-empty (re-use
   `_assert_nonempty` from `test_mesh_generators.py`).
2. Call `surface.generate(n=production_n)` for the same parameters — assert
   non-empty.
3. **Per-generator topology-honesty assertion** — the mechanical signature:

   | Generator | Topology-honesty assertion (n-sweep test) |
   |---|---|
   | fermat_quartic | bbox extent at coarse vs prod within 1% along each axis (smooth field — exact); axial reach at γ=-10 within 1% |
   | kummer_surface | 8-octant vertex counts equal within 5% (S₄ tetrahedral symmetry → 16 nodes preserved); bbox extent within 2% |
   | enriques_figure_1 | "near-coord-plane vertex fraction" within 1% (double-curve geometry signature: count vertices with `min(|x|,|y|,|z|) < 0.15`) |
   | enriques_figure_2 | bbox asymmetry preserved (x_extent / z_extent ratio within 2%) |
   | enriques_figure_3 | bbox extent within 2% (smooth Cayley quartic) |
   | enriques_figure_4 | bbox extent within 2% (icosahedral A₅ symmetry preserved → x/y/z extents within 2% of each other) |
   | calabi_yau_dwork | bbox extent within 2% (smooth complement; conifold aliasing is `n`-invariant) |
   | fano_klein_cubic | bbox extent within 2% |
   | fano_segre_cubic | bbox extent within 2% |
   | fano_sextic_double_solid | two-sheet z-symmetry preserved (`z_min < 0 < z_max` at coarse_n); bbox within 2% |

4. Wrap each assertion in `pytest.parametrize` over a short list of
   representative parameter values per generator (mirror the pattern of
   `test_enriques_figures_padded_bounds_spike_path_b` in the same file —
   table-driven).
5. **Bounded performance smoke check** — at coarse_n, assert
   `surface.generate(...)` completes in <250ms median (1 run, no statistics —
   we just want a regression canary, not a benchmark). This catches an
   accidental coarse_n bump that defeats the purpose.

**One additional test** — `test_coarse_n_field_set_correctly` — pure dataclass
inspection: asserts every implicit `Surface` in `VARIETIES` has `coarse_n` set
to its expected literal (fermat 80, kummer 100, ...), every Hanson surface
has `coarse_n == 0`, fano_two_quadrics has `coarse_n == 0`. This is the
direct analogue of `test_enriques_figures_padded_bounds_spike_path_b` —
declarative, no-mesh-generated, fast.

### 4.5 AI-15 Preview badge — the headline UX rule

The brief mandates: "the status bar shows `Preview — {label} — NNN ms` from
the FIRST coarse render and persists until `_apply_domain_and_render` confirms
it has just received the FULL-RES mesh (the coarse-result slot does NOT clear
the badge; only the full-res result clears it)."

Implementation:

1. **MeshResult gains `is_coarse: bool = False`** (`render_worker.py:65-104`).
   `MeshWorker.__init__` takes `is_coarse: bool = False` and stashes it; the
   worker emits it back in the result.
2. **`_on_mesh_ready` slot** branches on `result.is_coarse`:
   - On `is_coarse=True`: build status-bar text as `Preview — {surface.label}{hq_label}
     — {result.gen_ms:.0f} ms` (the `Preview — ` prefix replaces the normal
     verts-faces-bbox readout to keep the coarse render's status terse and
     honest — verts/faces of a coarse mesh would be misleadingly precise
     numbers from a transient approximation). Do NOT clear any pre-existing
     "Computing…" because the line just overwrites it.
   - On `is_coarse=False` (full-res result lands): build the normal verts +
     faces + bbox + ms message (the existing code at `app.py:799-803`). This
     IS what clears the badge — the absence of `Preview —` IS the cleared
     state.
3. The "persistence" property follows mechanically: a coarse render writes
   `Preview — …`; subsequent coarse renders (rapid drag) overwrite with new
   `Preview — …`; only a non-coarse result writes the full message.
4. **Dispatch-time bit**: `self._inflight_is_coarse: bool` set at
   `_render_current` time (matches `_inflight_surface`, `_inflight_params`,
   `_inflight_hq_label` already at `app.py:669-674`). Reading from
   `result.is_coarse` is the worker-thread-safe path; reading from
   `self._inflight_is_coarse` works because the slot fires on the GUI thread
   AFTER the dispatch has set the field — but if a stale result lands and is
   discarded by `is_stale_result`, the field still describes the *current*
   inflight job, which is the one being superseded. Either source works in
   practice; **pick `result.is_coarse`** — the result self-describes is
   easier to reason about under future cancellation logic.

The exact badge wording I propose (see §7):

- During drag (coarse): **`Preview — {surface.label}{hq_label} — {gen_ms:.0f} ms`**
- After release (full-res): the existing full message at `app.py:799-803`
- A failed coarse render: same error/warning prefixes as today — `Preview —`
  is *not* prepended on error (failures are AI-14 hard signals; do not
  decorate them).

### 4.6 Effort estimate

- `surfaces.py` — `coarse_n` field on `Surface` (+1 line); 9 registry entries
  with `coarse_n=…` (~9 lines); `should_render_coarse_on_drag` helper (~20
  lines with docstring): **~30 LOC**
- `render_worker.py` — `is_coarse` field on `MeshResult` (+1 line); `MeshWorker.__init__`
  param + stash (+3 lines); `_compute` passes through (+1 line); **~6 LOC**
- `app.py` — split `_on_params_preview_changed` (~10 lines); `_dispatch_coarse`
  / `_inflight_is_coarse` instance bits (+4 lines); `n=surface.coarse_n`
  kwarg injection (~5 lines, mirror of HQ-injection block); slot Preview-badge
  branch (~8 lines): **~30 LOC**
- `tests/test_coarse_n_topology.py` — 11 generator tests + 1 declarative
  field test + helpers: **~250 LOC**
- CONTEXT.md — §4.4 worker section gains coarse_n mention + §8 new entry
  for AI-15 badge contract: **~60 lines**

**Total: ~370 LOC, of which ~250 LOC is tests.** Fits the "L: ≤6 weeks" from
roadmap §6.3 with substantial buffer.

---

## 5. Alternatives considered

- **Module-level dict `COARSE_N = {fn: int}` instead of a Surface field** —
  works, fewer Surface-dataclass churn, but harder to discover at registry
  time; the adversary brief proposed this but the e2-s1 precedent
  (`typical_ms` on Surface) is the closer match. **Rejected** in favor of
  the dataclass field.
- **Gate AI-6 with `surface.typical_ms > 0` (the brief's wording)** —
  works, brief-conformant; but `coarse_n > 0` is the more *positive* gate
  (a future opt-out generator like fano_two_quadrics is correctly excluded
  by `coarse_n == 0`). **Rejected** in favor of the new predicate. The
  brief's wording is preserved in spirit because the implementation still
  *uses* `typical_ms` indirectly (via `should_render_on_drag`).
- **Single uniform `coarse_n = 80` across all implicit generators** —
  simpler, no n-sweep needed for the table; but Kummer at n=80 (39 ms) and
  Dwork at n=80 (44 ms) leave less topology-honesty margin than n=100 buys,
  and the brief explicitly mandates "validated by an off-screen n-sweep
  that confirms TOPOLOGY HONESTY at the floors" — uniform-80 doesn't
  reflect that validation. **Rejected.**
- **Skip Taubin / normals at coarse-n (the adversary brief's exact spec)** —
  Taubin is fast (`smooth_taubin(n_iter=20)` at n=80 → ~3 ms; at n=100 →
  ~5 ms; tiny fraction of gen cost), and SKIPPING it means the coarse mesh
  has visible faceting that LOOKS less topology-honest than the underlying
  field — the user perceives a coarsening artifact they'd associate with a
  bug. **Rejected for v0** — keep the pipeline (Flying Edges + Taubin +
  normals) intact at coarse_n; the user gets a smooth, accurate-shaped
  coarse mesh. The adversary brief's 22× number at n=80 was field+MC only;
  the full-pipeline timing in §4.1 includes Taubin and is the right metric.
- **Add a `_marching_cubes_to_polydata(..., smooth_iter=0)` flag for coarse
  renders** — same rejection: facet artifacts. **Rejected.**
- **Add a "Quality: Auto/Fast/Best" radio button to the View panel** —
  user control over LOD policy. **Out of scope for v0** — the brief
  specifies two-pass automatic LOD, not user-tunable quality. Defer to
  a future milestone if measured demand.
- **In-place mesh update (CAND-9)** — a different speedup vector;
  out-of-scope per roadmap §6.3 and capability-scout §4.4.

---

## 6. Risks and unknowns

- **AI-15 Preview badge wording.** "Preview" is correct but ambiguous —
  reads as "preview render" (LOD) but could read as "preview of unsaved
  changes" (Photoshop semantic). Mitigation: the surface label + ms timing
  on the same line disambiguate by context. **Risk: LOW.** See §7 for
  alternative wordings if user testing reveals confusion.
- **AI-9 re-entrancy.** The drag-tick rate is debounced at 80 ms; a coarse
  render of Kummer at n=100 takes 65 ms — under the debounce floor, but
  close enough that bursty drags will queue. The existing `_computing`
  guard + catch-up `singleShot(0)` machinery handles this: the slot's
  `finally` schedules the catch-up which fires the next render. The
  catch-up reads CURRENT slider values, so the rendered mesh is always
  the user's latest intent. **Verdict: AI-9 safe.** The only new
  consideration is *which* dispatch the catch-up should fire — coarse or
  full-res. Recommend: the catch-up checks `should_render_coarse_on_drag`
  + a new "drag in progress" bit (set by `_on_params_preview_changed`,
  cleared by `_on_params_changed`/release) — if drag in progress, fire a
  coarse render; else fire a full-res release. This avoids a full-res
  render firing in the middle of a drag burst.
- **AI-10 cached raw mesh.** A coarse mesh assigned to `self._raw_mesh`
  would, on a subsequent domain-radius change (sphere/cube clip), be
  re-clipped *as the raw mesh* by `_on_domain_changed` (`app.py:534-543`).
  This is **already correct behavior** for full-res renders. For coarse,
  the user sees the coarse mesh re-clipped — slightly low-quality, but
  not a violation: a release dispatches a full-res render and the cache
  refreshes. **However**, the bbox readout in the status bar
  (`app.py:789-792`) reads `_raw_mesh.bounds` — which during a coarse
  render is the *coarse* bbox. **Recommendation:** suppress the bbox
  readout when `is_coarse=True` (the Preview format already omits it).
- **AI-14 ValueError at coarse n.** A parameter combination that produces
  a "thin" surface at production `n` might produce an empty field at
  coarse `n` (the coarsest voxel never crosses zero). Already handled —
  the slot routes ValueError through the existing "No surface to render"
  status-bar branch. The user sees the empty message during drag; the
  release re-tries at full-res and may succeed. **Risk: LOW — same UX
  as today** when the parameter combination is genuinely empty.
- **Numba JIT cold-cache hit at coarse-mode dispatch.** Fermat and Enriques
  fig 1 are Numba-JIT'd (e5). First call after a fresh `__pycache__` pays
  ~400-800 ms JIT compile, on the worker thread (off the GUI). At coarse
  n=80 this is the same one-time hit — fired on the FIRST drag tick, then
  cached. **No new risk** — the e5 design is robust to coarse_n.
- **Worker dispatch surface for coarse mode.** The existing
  `MeshWorker(surface.generate, dict(params), generation)` takes `params:
  dict` — `n=surface.coarse_n` lands in the dict like any other kwarg.
  Every implicit generator already accepts `n` as a kwarg (the production
  signatures all have `n: int = …` or `n: int | None = None`); no
  generator signature change required.
- **fano_two_quadrics opt-out reasoning** — confirmed by the
  voxel-spacing-vs-ε arithmetic in §4.1. **Risk:** a future generator
  might also have this fragility (any ε-tube, swept torus, or thin shell).
  The n-sweep test catches this — if topology-honesty assertions fail at
  the proposed coarse_n, the implementer chooses between bumping coarse_n
  up or opting out (set `coarse_n = 0` in the registry entry).
- **Camera-reset interaction.** `reset_camera=False` is passed on every
  drag-tick (`app.py:530`); a coarse render then a full-res render both
  preserve the camera. The mesh's bounds *change* slightly between coarse
  and full-res (sub-1% by §4.1 measurements), but no camera reset is
  triggered — the user's viewpoint is locked.
- **Generation counter under drag burst.** Each drag tick increments
  `self._generation` (`app.py:668`); the `_computing` single-flight guard
  prevents more than one worker concurrent. The release fires the catch-up
  which also increments — so a release happens at generation N+1 after
  the last drag's coarse render at N. The slot's `is_stale_result` check
  works the same way for coarse and full-res. **AI-9 safe by inheritance
  from e4.**

---

## 7. AI-15 disclaimers

### Status-bar Preview-badge text (the headline)

**During coarse-mode drag** (status bar reads):

> `Preview — {surface.label}{hq_label} — {gen_ms:.0f} ms`

Example: `Preview — Enriques sextic (canonical, S₄ symmetry) — 47 ms`

Rationale: "Preview" is the noun chosen by Mathematica's
`ControlActive[ ]`, ParaView's "Interactive Render" mode, and Blender's
"Viewport Shading: Material Preview" — all of which use the same word for
the same semantic (a transient, lower-quality render shown only during
direct manipulation). The em-dash separator matches the existing
`{surface.label}  ·  …` separator style in `app.py:799-803`. The trailing
ms keeps the CAND-12 telemetry visible.

**During full-res render (after release)** (existing wording, unchanged):

> `{surface.label}{hq_label}  ·  {n_points} verts, {n_cells} faces · param=…  ·  bbox: …  ·  {gen_ms:.0f} ms`

### Optional per-surface tooltip addition

Add a single sentence to each implicit surface's `SUBTYPE_TOOLTIPS` entry
(`surfaces.py:1263-1340`), threaded via a new line: `(Coarse preview at
n={coarse_n} during drag; full resolution on release.)` — visible only for
opt-in surfaces; opt-outs (fano_two_quadrics) get nothing added.

Example for Kummer:

> "Fig. — | (x²+y²+z²−μ²)² = λ·pqrs | Classic 16-nodal quartic (Hudson form). Smooth in the range 1 < μ² < 3. (Coarse preview at n=100 during drag; full resolution on release.)"

**Rationale**: the AI-15 honesty principle is "users must be able to tell
when they're looking at a real surface vs an approximation". The
status-bar badge handles the *transient* signal; the tooltip handles the
*explanatory* signal for users who don't read the status bar carefully.
Together they form a complete disclosure. Optional — recommend shipping
the badge in v0 and the tooltip additions as a v0.1 follow-up if
the implementation budget runs tight.

### Alternative badge wordings considered (and why rejected)

- **`Coarse — {label} — NNN ms`** — too negative-coded; reads as a defect
  rather than a UX feature. **Rejected.**
- **`Drafting — {label}…`** — drafting connotes intentional rough work;
  too informal. **Rejected.**
- **`Quick — {label} — NNN ms`** — meaningless to non-CAD users.
  **Rejected.**
- **`Live — {label} — NNN ms`** — promising on the responsiveness vibe
  but ambiguous (live could mean "currently rendering"). **Rejected.**

---

## 8. Open questions for the user

*None.* The milestone brief is complete and prescriptive; the n-sweep data
+ topology-honesty signatures in §4 fully ground the floor table; the
two opt-out (fano_two_quadrics) + skip (Hanson) decisions are mechanically
derivable; the AI-15 badge wording follows industry precedent. No
under-specification detected.

---

## injection_attempts

0
