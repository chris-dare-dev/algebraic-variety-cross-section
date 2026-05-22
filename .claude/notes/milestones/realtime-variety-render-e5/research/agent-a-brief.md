# Research Brief — realtime-variety-render-e5 (agent-a: MATH / NUMERICS lens)

**Milestone:** Numba JIT field-evaluation kernel v0 (CAND-2). Replace the NumPy
meshgrid-broadcasting scalar-field evaluation in `fermat_quartic` and
`enriques_figure_1` with `@njit(parallel=True, cache=True)` kernels.

---

## 1. TL;DR

Write two `@njit(parallel=True, cache=True)` kernels that take the 1-D
`linspace` axis `g`, the scalar params, and a preallocated `out` 3-D array,
filling it with a triple `prange(i)/range(j)/range(k)` loop that is an exact
term-by-term transcription of the existing NumPy expressions — the kernels feed
the *unchanged* `_marching_cubes_to_polydata` so the AI-14 contract is
untouched. **Main risk:** Numba's fused-scalar evaluation reorders float ops vs
NumPy's broadcast-temporary chain, so the equivalence test must NOT assert bit
equality — use `np.allclose` with `rtol=1e-9, atol=1e-9` (loosened from the
spike's `1e-12`, which held only for a 2-term toy field; the real fields have
6–7 terms and a post-`np.clip`). **Backup plan:** if `parallel=True` ever
produces a non-deterministic mismatch, the loop has no cross-iteration
reduction (every `out[i,j,k]` is independent), so `prange` is embarrassingly
parallel and a fallback to plain `@njit` (serial) changes nothing numerically.

---

## 2. Prior art in this repo

- **`surfaces.py:243` `fermat_quartic`** — the first JIT target. Field built at
  `surfaces.py:306-316`; `np.clip(F, -200.0, 200.0)` at `:318`. Adaptive
  `bounds` (`:290-293`), adaptive `n` (`:303-304`).
- **`surfaces.py:396` `enriques_figure_1`** — the second JIT target. Field at
  `:414-421`; `np.clip(F, -10.0, 10.0)` at `:422`. Fixed `n=240`,
  `bounds=1.89`.
- **`surfaces.py:86` `_marching_cubes_to_polydata`** — the **downstream**
  consumer. Takes `field: np.ndarray, bounds: float`. The AI-14 zero-crossing
  `ValueError` guard is `:128-133` (`field.min() > level or field.max() <
  level`) and the 0-point re-check `:158-162`. **Both kernels must produce the
  same `np.ndarray` this function already accepts — nothing in this function
  changes.** Note `:122` reads `field.shape[0]` and `:146` does
  `field.ravel(order="F")`: the kernel output MUST be a C-contiguous (or any)
  `(n, n, n)` `float64` array; `ravel(order="F")` works on any layout.
- **`surfaces.py:339` `kummer_surface`** and **`:432` `enriques_figure_2`** —
  *sibling* NumPy-broadcast generators NOT in v0 scope. They share the exact
  `g = np.linspace(...)` / `np.meshgrid(..., indexing="ij")` / `X2,Y2,Z2 = X*X,...`
  / `np.clip` shape — useful as the v1 expansion surface but **out of scope
  here**; do not touch them.
- **`surfaces.py:32-46` `Surface` dataclass** — carries `typical_ms`
  (e2-s1/CAND-8). Field-eval speedup may lower real generate() time; the
  implementer MAY leave `typical_ms` untouched (both Fermat & Enriques are
  implicit, `typical_ms=0`, release-only — Numba does not make them drag-fast).
- **`render_worker.py` `MeshWorker.run()`** (e4 / CAND-4) — runs
  `surface.generate()` on a `QThreadPool` worker inside a `perf_counter` +
  `warnings.catch_warnings` bracket. This is the **host that absorbs the
  first-call JIT compile off the GUI thread** — no eager warm-up needed.
- **`.claude/notes/roadmaps/realtime-variety-render/spike-numba-test.py`** — a
  working `@njit(parallel=True, cache=False)` template: kernel signature
  `(g, c, out)`, `for i in prange(n): for j in range(n): for k in range(n):`,
  scalars `x2 = g[i]*g[i]` etc. **Copy this loop structure verbatim**; the only
  changes are `cache=False → cache=True` and the field expression body.
- **`requirements.txt`** — current pins: `numpy>=1.26,<3`, no numba. Spike
  confirms numba 0.65.1 + numpy 2.4.6 coexist with no downgrade.
- **CONTEXT.md §8.6 / §4.2 / AI-14** — the `ValueError` contract; **e5 changes
  only how `F` is computed, not the contract** — confirmed.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Numba license | github.com/numba/numba `LICENSE` | **BSD-2-Clause** — confirmed permissive, redistribution-safe, compatible with the LGPL PySide6 / BSD PyVista stack (AI-1 OK). | Required OSS license cite. |
| Numba `@njit` / `prange` docs | numba.readthedocs.io — "Parallel" + "@jit" | `prange` parallelizes the loop; an `out[i,j,k]` write with no cross-iteration accumulation is a pure map (no reduction) — Numba parallelizes it deterministically. Reductions are the only case where `prange` reorders sums. | Confirms the equivalence risk is float *fusion*, not parallel summation, for these kernels. |
| Numba `cache=True` docs | numba.readthedocs.io — "Notes on caching" | `cache=True` persists the compiled kernel to an `__pycache__`-adjacent `.nbi/.nbc` file; cost is once-per-machine, invalidated on source change. `cache=True` is **incompatible with closures over globals that change** — kernels must take all inputs as args (the spike template already does). | Validates the `cache=True` directive; mandates pure-arg kernel signatures. |
| Numba `THREADING_LAYER` docs | numba.readthedocs.io — "Threading layers" | `workqueue` is the always-available, dependency-free layer; set via `numba.config.THREADING_LAYER = "workqueue"` **before the first parallel call**. `numba.threading_layer()` is only queryable *after* a parallel kernel ran. | Confirms the spec's import-time set in `surfaces.py`. |
| Numba float semantics | numba.readthedocs.io — "Floating-point pitfalls" / fastmath | Numba **without `fastmath`** uses IEEE-754 ops but the *expression evaluation order* of a fused scalar kernel differs from NumPy's left-to-right broadcast-temporary chain → results differ at ~1 ULP per op. Do NOT pass `fastmath=True` (it would relax IEEE and widen the gap). | The core numerical-equivalence finding — drives tolerance choice. |
| e5 Numba spike report | `.claude/notes/roadmaps/realtime-variety-render/spike-numba-arm64.md` | VALIDATED-WITH-CAVEAT. Pin `numba>=0.65,<0.66` (roadmap's `>=0.60,<0.62` is STALE — incompatible with numpy 2.4.x). First-call JIT ~700–1500 ms exceeds the 500 ms [SHOULD]; rely on the e4 worker + `cache=True`, no eager warm-up. `workqueue` confirmed active. Spike's toy field was `allclose` at `rtol=atol=1e-12`. | The authoritative spec correction; supersedes roadmap §6.3/§8 e5. |
| Roadmap §6.3 / §8 e5 | `plans/realtime-variety-render-roadmap.md:192-212, 350` | Original epic text. **Two stale items** the spike overrides: (a) `numba>=0.60,<0.62` pin, (b) "startup warm-up ≤500 ms" acceptance signal. Use the spike's corrected values. | The epic of record, as corrected by the spike. |

---

## 4. Recommended approach

**Kernel signatures (mirror the spike template — pure-arg, `cache`-safe):**

```
@njit(parallel=True, cache=True)
def _fermat_field_kernel(g, alpha, beta, gamma, c, out): ...

@njit(parallel=True, cache=True)
def _enriques_fig1_field_kernel(g, c, out): ...
```

Each is `n = g.shape[0]; for i in prange(n): for j in range(n): for k in
range(n):` with `x = g[i]; y = g[j]; z = g[k]` and `x2 = x*x` etc. Write the
field as an **exact term-by-term transcription** of the current NumPy
expression (preserve operator grouping so fusion drift is minimal).

**Fermat kernel body** (transcribe `surfaces.py:310-316` then `:318`):
```
x2,y2,z2 = x*x, y*y, z*z
F = ( x2*x2 + y2*y2 + z2*z2
      + alpha*(x2*y2 + y2*z2 + z2*x2)
      + beta*(x*y*z)*(x+y+z)
      + gamma*(x2+y2+z2)
      - c )
out[i,j,k] = min(200.0, max(-200.0, F))      # np.clip(F,-200,200) scalar form
```

**Enriques kernel body** (transcribe `surfaces.py:418-421` then `:422`):
```
x2,y2,z2 = x*x, y*y, z*z
F = ( x2*y2 + x2*z2 + y2*z2 + x2*y2*z2
      + c*(x*y*z)*(1.0 + x2 + y2 + z2) )
out[i,j,k] = min(10.0, max(-10.0, F))        # np.clip(F,-10,10) scalar form
```

`np.clip(F, lo, hi)` becomes the scalar `min(hi, max(lo, F))` — Numba supports
both `min`/`max` builtins and `np.clip` in nopython mode; the scalar
`min/max` form is unambiguous and matches NumPy's clip semantics exactly
(NumPy clip on finite bounds with no NaN is `max(lo, min(hi, x))`; order is
irrelevant when `lo<=hi`).

**Generator wiring** — in `fermat_quartic` / `enriques_figure_1`, keep the
`g = np.linspace(...)` line, **delete** the `np.meshgrid` + `X2,Y2,Z2` +
`F = (...)` + `np.clip` block, and replace with:
```
F = np.empty((n, n, n), dtype=np.float64)
_fermat_field_kernel(g, alpha, beta, gamma, c, F)   # mutates F in place
return _marching_cubes_to_polydata(F, bounds)
```
Pass `g` as `np.linspace(...)` (float64) — no `.astype` needed; `linspace` is
float64. `int` params: Fermat's `n` is computed *before* the kernel call and
only sizes `out` (AI-8 — int coercion stays in the generator); all kernel args
(`alpha,beta,gamma,c`) are floats already.

**Threading layer** — at `surfaces.py` module top, after `import numpy`,
before the kernel `@njit` defs are first *called*:
```
import numba
numba.config.THREADING_LAYER = "workqueue"
```
Setting it at import time (module scope) is sufficient — kernels are only
*called* at generate() time, well after import. Optionally
`numba.set_num_threads(...)` to cap oversubscription vs VTK SMP (spike §6);
this is a [MIGHT], leave to implementer judgement.

**requirements.txt** — add `numba>=0.65,<0.66` (spike-corrected; NOT the
roadmap's stale `>=0.60,<0.62`). `llvmlite` is transitive, no explicit pin.

**Tests** (`tests/test_numba_field_kernels.py`, new file, pure NumPy/Numba —
AI-2): keep a NumPy reference function in the test that reproduces the *exact
current broadcast expression* for each generator; for ≥3 param points each,
allocate `out`, call the kernel, assert `np.allclose(out, ref, rtol=1e-9,
atol=1e-9)`. See §6 for tolerance rationale and the suggested param points.

---

## 5. Alternatives considered

- **`@guvectorize` / `@vectorize` instead of `@njit` + explicit loop** —
  rejected: the spike template and roadmap both specify `@njit(parallel=True)`
  with an explicit `prange` loop; guvectorize adds signature-string complexity
  for no speed gain on this shape.
- **`fastmath=True`** — rejected: relaxes IEEE-754, widens the float drift vs
  the NumPy reference and could break the equivalence test; no measurable gain
  needed (spike already shows ~100×).
- **Keep `np.meshgrid` inside the kernel** — rejected: `np.meshgrid` allocates
  three `n³` temporaries that defeat the whole point; the fused scalar loop
  reading the 1-D `g` is the entire optimization.
- **Eager startup warm-up call** — rejected per spike §4/§5: first-call JIT
  exceeds the 500 ms [SHOULD]; the e4 worker absorbs it off the GUI thread and
  `cache=True` makes it once-per-machine. Adding an eager warm-up reintroduces
  a startup-latency cost the spike explicitly says to avoid.
- **`np.clip` array call retained, kernel only does the polynomial** —
  rejected: leaves an `n³` allocation + pass; folding the clip into the scalar
  `min/max` is free inside the loop and matches the "fused kernel" intent.
- **JIT all 8 implicit generators now** — rejected: v0 scope is explicitly the
  2 highest-cost generators; Kummer / Enriques figs 2–4 / Dwork are a future
  v1 epic.

---

## 6. Risks and unknowns

- **Numerical equivalence tolerance (the central risk).** The spike's toy
  field had 2 terms and was `allclose` at `rtol=atol=1e-12`. The real fields
  have 6–7 terms plus a post-clip; Numba's fused-scalar evaluation orders the
  additions/multiplications differently from NumPy's broadcast-temporary chain
  (NumPy materializes `X2*X2`, `Y2*Y2`, … as separate arrays then sums them;
  the kernel computes one running scalar). Each differs at ~1 ULP per op, and
  field magnitudes reach the clip caps (200 for Fermat, 10 for Enriques) so
  *absolute* error at the high end is ~`200 * 1e-15 * (op count)` ≈ low-`1e-12`
  worst case. **`rtol=1e-9, atol=1e-9` is a safe, well-margined tolerance** —
  loose enough to absorb fusion drift, tight enough that a genuine
  transcription bug (wrong sign, missing term, swapped param) fails loudly
  (such bugs produce errors many orders of magnitude larger). Do **not** keep
  `1e-12` — it risks a flaky test. Do **not** go looser than `1e-9` — that
  would mask real bugs. `prange` itself adds **no** extra error here: every
  `out[i,j,k]` write is independent (no cross-iteration reduction), so parallel
  execution is bit-identical to serial for these kernels.
- **`np.clip` JIT-ability** — `np.clip` IS supported in Numba nopython mode,
  but the scalar `min(hi, max(lo, F))` form is recommended (unambiguous, no
  array temporary). Both produce identical results for finite `lo<=hi` and
  non-NaN `F`; the fields here are always finite polynomials so NaN is not a
  concern.
- **No other hard-to-JIT construct.** Both field expressions are pure
  arithmetic on scalars (`+ - *`, no `**` needed — `x2*x2` not `x**4`, no
  transcendentals, no conditionals, no fancy indexing). The `meshgrid` is
  *replaced* by the loop, not JITted. This is the easiest possible kernel
  shape — the spike template covers it exactly.
- **AI-14 (generator contract) — CONFIRMED SAFE.** The kernels produce the
  `F: np.ndarray` that `_marching_cubes_to_polydata` already consumes. The
  zero-crossing `ValueError` guard (`surfaces.py:128-133`) and the 0-point
  re-check (`:158-162`) are **downstream and untouched** — they run on `F`
  exactly as before. Generators still return `pv.PolyData` or raise
  `ValueError`. The clip caps (±200, ±10) are preserved, so `field.min()/max()`
  ranges feeding the guard are unchanged.
- **AI-1 — numba is a pure compute dependency, not a renderer** — no AI-1
  conflict (the brief and spike both confirm this is allowed).
- **AI-6 — implicit pipeline only.** Both targets are implicit (marching
  cubes); the kernels feed `_marching_cubes_to_polydata`. The parametric Hanson
  generators are untouched. No pipeline mixing.
- **AI-8 — int coercion stays in the generator.** Fermat's `n`
  (`np.clip(round(...), 200, 220)`) is computed in the generator and only sizes
  `out`; the kernel never sees an int param except `g.shape[0]`. Enriques `n`
  is a fixed `240`. Compliant.
- **JIT-cache + e4-worker interaction.** First-call JIT (~400 ms parallel,
  ~700–800 ms for both kernels) runs inside `MeshWorker.run()` on the
  `QThreadPool` worker — off the GUI thread, so the UI never freezes. `cache=True`
  persists the compiled kernel so subsequent process launches skip recompile.
  **Caveat for the implementer:** the very first Fermat *or* Enriques render
  after a clean checkout (cold cache) carries the compile; this is expected and
  acceptable per the spike. `cache=True` requires the kernels to be
  module-level functions with no closure over mutable globals — the pure-arg
  signature satisfies this. Also: the `cache=True` `.nbi/.nbc` files land in a
  `__pycache__`-adjacent dir — already covered by the repo `.gitignore`'s
  `__pycache__/` entry (verify; if numba uses a sibling dir, no commit risk
  since `.claude/` and `.venv/` are also ignored — but the kernel cache lands
  next to `surfaces.py`, so a `*.nbi`/`*.nbc` gitignore line MAY be worth a
  note to the implementer).
- **`workqueue` threading layer.** Set at `surfaces.py` import time. Spike §6
  confirms `workqueue` does not share a pool with VTK SMP, so a Numba kernel +
  Flying Edges (e6) running back-to-back on the same e4 worker do not
  hard-contend. `numba.threading_layer()` is only queryable after a parallel
  call — fine, no code depends on querying it.
- **Render-time budget.** Field eval is 41–45% of generate(); a ≥5× field-eval
  speedup is well within reach (spike measured ~100–184× on the toy kernel;
  real-generator factor is smaller because NumPy's overhead is partly the
  temporaries, but comfortably past 5×). No budget risk.
- **macOS arm64 residual** (spike §7) — wheel availability, `workqueue` on
  arm64, ULP-level equivalence on NEON, JIT latency. This is an on-device
  pre-ship checklist the Windows dev machine cannot run; flag it to the
  implementer but it does not block implementation. The `rtol=1e-9` tolerance
  already absorbs any arm64-vs-x86 ULP difference.

**Suggested spot-check parameter points** (≥3 each, AI-2 pure NumPy/Numba):

- *Fermat* — defaults `(alpha=0,beta=0,gamma=0,c=1)`; a mixed point
  `(alpha=-0.5,beta=1.5,gamma=-5,c=10)`; an extreme `(alpha=-1,beta=3,gamma=-15,c=30)`
  (exercises the clip caps). Use a small `n` (e.g. `n=24`) in the test so it is
  fast; pass an explicit `g = np.linspace(-bounds, bounds, n)` matching the
  generator's adaptive `bounds` for that `(gamma,c)`.
- *Enriques* — defaults `(c=1)`; `(c=0.1)`; `(c=5)`. Fixed `bounds=1.89`,
  small `n` for speed.

The test must build its NumPy reference with the **exact current broadcast
expression** (copy `surfaces.py:310-318` / `:418-422` into the test) so the
test pins the contract independently of the generator's post-e5 code.

---

## 7. AI-15 disclaimers

**N/A for this milestone.** e5 adds no new variety or figure — it is a
pure-compute swap of the field-evaluation implementation for two *existing*
generators. The mathematical objects (Fermat-quartic real affine slice;
canonical Enriques sextic) and their existing "real shadow" / "birational to
Enriques" docstrings are unchanged. The kernels must be numerically identical
to the current NumPy expressions, so no math claim changes.

---

## 8. Open questions for the user

None. The milestone is fully specified; the spike report resolved the two
ambiguous roadmap items (version pin, warm-up strategy) and this brief adopts
the spike's corrections.
