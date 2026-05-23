# agent-b research brief — realtime-variety-render-e5b

**Milestone:** realtime-variety-render-e5b — Numba JIT field-evaluation kernel v1 (extend CAND-2 to the remaining 9 implicit generators)
**Lens:** integration / perf / test-design / JIT-cache-stacking
**Date:** 2026-05-23

---

## 1. TL;DR

Mechanically transcribe each of the 9 remaining implicit generators' NumPy meshgrid + broadcast-polynomial + `np.clip` blocks into a per-generator `@njit(parallel=True, cache=True)` out-fill kernel that mirrors `_fermat_field_kernel` / `_enriques_fig1_field_kernel` (`surfaces.py:314-374`) verbatim — same `prange` outer i, plain `range` j/k, scalar `g[i]/g[j]/g[k]`, term-by-term operator-order-identical formula, clip folded into per-voxel `if/elif`. The headline integration risk is **CONTEXT.md §8.20 `workqueue` single-flight obligation**: 11 kernels stack the SAME constraint (no concurrent parallel-kernel dispatch) but do NOT widen it — the `_computing` guard at `app.py:613-756` still serializes every `surface.generate()` call across the e4 worker pool, and the e4b `_pending_render`/`_pending_is_coarse` queue-latest semantics ensure at most one worker is in flight even under coarse-mode drag-tick bursts. Fallback: if any one of the 9 generators surfaces an unexpected per-kernel Numba issue (e.g. `**5` in Dwork is the one operator the e5 v0 kernels never used — see Risk R2), ship the other 8 and revert that generator to its NumPy form for v1; the JIT mechanics are per-kernel-independent.

---

## 2. Prior art in this repo

### The two e5-shipped kernel templates the 9 v1 kernels copy verbatim
- **`surfaces.py:314-344` `_fermat_field_kernel`** — the canonical out-fill pattern. `@njit(parallel=True, cache=True)`; signature `(g, alpha, beta, gamma, c, out)`; outer `for i in prange(n)` with `x = g[i]; x2 = x*x` hoisted; inner `for j in range(n)` / `for k in range(n)` with the scalar polynomial + folded clip (`if val < -200.0: val = -200.0; elif val > 200.0: val = 200.0`); writes `out[i,j,k] = val`. Operator order is term-by-term identical to the former NumPy expression (e5 lessons line 159 in milestone-researcher memory).
- **`surfaces.py:347-374` `_enriques_fig1_field_kernel`** — same structure with `(g, c, out)` signature and ±10 clip caps.

### The 9 v1 targets — each with file:line, params, clip caps, special preconditions
1. **`surfaces.py:532-568` `kummer_surface(mu_squared, n)`**.
   - Pre-checks (lines 546-551): `abs(mu_squared - 3.0) < 1e-6` → ValueError (lambda pole); `mu_squared <= 1.0/3.0` → ValueError (no zero set). **Both fire BEFORE any kernel call** — AI-14 contract preserved. `lam` is computed in the generator (`:552`), so the kernel only ever sees finite scalars.
   - Adaptive `bounds` (`:555-556`).
   - Current field (`:558-567`): `s2 = sqrt(2.0)` SCALAR pre-computed; meshgrid X,Y,Z; `p_,q_,r_,s_ = (1-Z-s2*X), (1-Z+s2*X), (1+Z+s2*Y), (1+Z-s2*Y)`; `F = (X*X+Y*Y+Z*Z-mu_squared)**2 - lam*p_*q_*r_*s_`; clip ±50.
   - Kernel signature: `_kummer_field_kernel(g, mu_squared, lam, out)`. `sqrt(2.0)` as a Numba module-level constant or literal inside the kernel (both compile fine; literal is cleaner per the e5 template).
2. **`surfaces.py:633-671` `enriques_figure_2(lam0, lam3, c, n, bounds, hq_smoothing)`**.
   - No pre-checks (clean polynomial). HQ-smoothing path at `:669-671` is downstream of the kernel — `_marching_cubes_to_polydata(F, bounds, second_smooth_iter=40 if hq_smoothing else 0)`. The kernel only fills `F`; HQ logic does NOT enter the kernel.
   - Current field (`:660-666`): `F = lam0*X2*Y2*Z2 + 1.0*Y2*Z2 + 1.0*X2*Z2 + lam3*X2*Y2 + c*(X*Y*Z)*(1+X2+Y2+Z2)`; clip ±10.
   - Kernel signature: `_enriques_fig2_field_kernel(g, lam0, lam3, c, out)`.
3. **`surfaces.py:684-712` `enriques_figure_3(k, n, bounds)`**.
   - No pre-checks. Current field (`:706-711`): `s = X+Y+Z+X*Y+X*Z+Y*Z; F = s*s - k*X*Y*Z`; clip ±50.
   - Kernel signature: `_enriques_fig3_field_kernel(g, k, out)`. Note: this is the Cayley quartic symmetroid — degree-4, NOT a determinant. Per milestone brief: confirmed `(x+y+z+xy+xz+yz)**2 - k*x*y*z`, not a sextic.
4. **`surfaces.py:721-760` `enriques_figure_4(tau, n, bounds)`**.
   - No pre-checks. `phi = (1+sqrt(5))/2` and `one_plus_2phi = 1+2*phi` are scalar pre-computed in the generator (`:748-750`) — pass to the kernel or recompute as literals inside `@njit`. Current field (`:752-759`): `P = 4*(phi2*X2-Y2)*(phi2*Y2-Z2)*(phi2*Z2-X2)`; `Q = one_plus_2phi*(X2+Y2+Z2-1)**2`; `F = P - tau*Q`; clip ±20.
   - Kernel signature: `_enriques_fig4_field_kernel(g, tau, phi2, one_plus_2phi, out)` (pass the precomputed scalars in; cleaner than recomputing).
5. **`surfaces.py:951-995` `calabi_yau_dwork(psi, n, bounds)`**.
   - **`warnings.warn(...RuntimeWarning)` at `:979-990`** fires BEFORE the field-build block (`:991-995`), so the warning is captured by `render_worker.MeshWorker._compute`'s `warnings.catch_warnings` (render_worker.py:196) regardless of whether the kernel even runs. **AI-14 contract preserved** — warning is generator-level, kernel is pure compute.
   - Current field (`:991-994`): `F = X**5 + Y**5 + Z**5 + 2.0 - 5.0*psi*X*Y*Z`; clip ±100.
   - Kernel signature: `_dwork_field_kernel(g, psi, out)`. **The only v1 kernel using `**5`** (degree-5). Numba `@njit` compiles `x**5` to a chain of multiplies internally; per the e5 lesson on numeric identity, the kernel form should explicitly write `x*x*x*x*x` (or hoist `x2=x*x; x4=x2*x2; x5=x4*x`) to keep the per-voxel IEEE-754 op sequence reproducible across architectures. Test will catch any drift.
6. **`surfaces.py:1015-1047` `fano_klein_cubic(z0, n)`**.
   - No pre-checks. `bounds = 2.0` hard-coded. Current field (`:1043-1046`): `F = X + X*X*Y + Y*Y*Z + z0*Z*Z + z0*z0`; clip ±50.
   - Kernel signature: `_klein_cubic_field_kernel(g, z0, out)`. Note: `z0*z0` is a precomputed scalar (no `np.empty` shape change), pass it pre-squared or recompute inside.
7. **`surfaces.py:1056-1092` `fano_segre_cubic(a, b, n)`**.
   - No pre-checks. `bounds = 2.5` hard-coded. Current field (`:1086-1091`): `s = X+Y+Z+a+b; F = X**3+Y**3+Z**3+a**3+b**3 - s**3`; clip ±1000.
   - Kernel signature: `_segre_cubic_field_kernel(g, a, b, out)`. `a**3` and `b**3` are scalar precomputables. The `**3` per-voxel is `x*x*x` for op-order-identity.
8. **`surfaces.py:1103-1154` `fano_two_quadrics(p, q, mu, eps, n)`**.
   - **`warnings.warn(...RuntimeWarning)` at `:1137-1142`** for `eps < 0.08` — fires BEFORE the field block (`:1146-1153`). AI-14 preserved.
   - Current field (`:1149-1153`): `Q1 = X*X+Y*Y+Z*Z+p*p+q*q-1.0`; `Q2 = lam[0]*X*X+lam[1]*Y*Y+lam[2]*Z*Z+lam[3]*p*p+lam[4]*q*q-mu`; `F = Q1*Q1 + Q2*Q2 - eps*eps`; clip ±200.
   - Kernel signature: `_two_quadrics_field_kernel(g, p, q, mu, eps, lam0, lam1, lam2, lam3, lam4, out)` — the `lam` tuple from line 1146 should be unpacked into 5 scalar args (Numba does support typed tuples but scalar args are simpler and match the e5 template's "only scalar params" style). Alternative: hard-code the constants `-0.5, 0.0, 0.5, 1.0, 1.5` as literals inside the kernel since they're never user-tunable; the brief is consistent with this. **Note: this surface is `coarse_n=0` (opt-out) per registry (`:1308-1318`)** — Numba speedup still helps full-resolution release renders.
9. **`surfaces.py:1169-1218` `fano_sextic_double_solid(R, alpha, n)`**.
   - No pre-checks. `bounds = 2.0`. Current field (`:1207-1217`): `X2,Y2 = X*X, Y*Y; F = Z*Z + X2*X2*X2 + Y2*Y2*Y2 + alpha*X2*Y2*(X2+Y2) - R**6`; clip ±200.
   - Kernel signature: `_sextic_double_solid_field_kernel(g, R, alpha, R6, out)` where `R6 = R**6` precomputed (or pass `R` and compute `R*R*R*R*R*R` inside the kernel as a hoisted scalar — Numba folds scalar invariants out of the prange loop automatically).

### Downstream pipeline contract (file:line proof it's downstream of every kernel)
- **`surfaces.py:173-282` `_marching_cubes_to_polydata`** — every generator hands it the `F: np.ndarray` array. The AI-14 ValueError guard is at `:226-231` (`field.min() > level or field.max() < level`); the post-contour 0-point re-guard is at `:256-260`. **Both run downstream of the kernel** — kernel is pure compute; contract surface is preserved.
- **`render_worker.py:171-176` `MeshWorker.run` + `:196-199` `_compute`** — `surface.generate(**params)` invocation. `warnings.catch_warnings(record=True)` wraps the call (`:196`); the RuntimeWarnings from Dwork/two_quadrics surface via `MeshResult.warning_text` (`:208-212`). **No worker code change needed** for e5b — the kernels are inside `surface.generate`, so all the e4 plumbing applies as-is.
- **`app.py:613-768` `_render_current`** — `params["n"] = surface.coarse_n` injection at `:709`, `MeshWorker(surface.generate, dict(params), self._generation, is_coarse=_is_coarse_active)` at `:765-768`. **No app code change needed.**

### Existing test pattern to extend
- **`tests/test_numba_field_kernels.py`** — the e5 file. Pattern: a NumPy reference function copy-pasted from the pre-e5 generator (`_fermat_ref`, `_enriques_ref` at `:48-70`), `@pytest.mark.parametrize` over a 3-tuple parameter list (`_FERMAT_POINTS` at `:83-87`, `_ENRIQUES_C` at `:116`), `np.allclose(out, ref, rtol=_RTOL, atol=_ATOL)` with `_RTOL = _ATOL = 1e-9` at `:73-74`, `_N = 32` at `:75`. Each kernel also gets a clip-bounds test (`test_*_respects_clip_bounds`). v1 extends this with 9 more reference functions + 9 parametrize blocks + 9 clip-bounds tests + 9 additions to `test_kernels_have_a_zero_crossing_at_defaults`. **The symmetry-bug coverage note at `:18-26`** applies to all 9 v1 kernels too — they are all symmetric under coordinate permutations in `(x,y,z)`, so an axis-transpose bug is undetectable but harmless.

### Registry + coarse-LOD interaction
- **`surfaces.py:1234-1325` VARIETIES**: coarse_n values — Fermat=80 (`:1246`), Kummer=100 (`:1249`), Enriques×4 = all 80 (`:1255, 1259, 1263, 1267`), Dwork=100 (`:1296`), Klein/Segre/SextSDS = 80/80/80 (`:1302, 1306, 1322`), two_quadrics = 0 (opt-out, `:1308-1318`). **6 of the 9 new v1 kernels run at coarse_n during drag** (Kummer + Enriques 2/3/4 + Dwork + Klein/Segre/sexticDS — actually 7 of 9 if we count carefully: kummer, enr2, enr3, enr4, dwork, klein, segre, sexticDS = 8; not 7 — let me recount). Counting: of the 9 new v1 kernels, `fano_two_quadrics` is coarse_n=0 (no coarse path), the other 8 carry coarse_n > 0. **So 8 of the 9 new kernels run at coarse_n on drag and full n on release.**

### CONTEXT.md sections directly affected
- **§3 numba bullet** (CONTEXT.md:61): "v0 scope is these 2 of 8 implicit generators; the rest are a future v1" → update to "v0+v1 covers all 11 implicit generators". The "2" → "11" change is the only substantive edit. The "8" was wrong even at e5 time per the milestone-researcher memory's e6 lesson (the repo has 11 implicit generators, not 8); e5b should both extend coverage AND correct the count.
- **§8.20 workqueue caveat** (CONTEXT.md:511-513): UNCHANGED. The single-flight obligation already covers any number of `@njit(parallel=True)` kernels; e5b stacks 9 more kernels but the same `_computing` guard serializes them.
- **§9 AI-2 gap bullet** (CONTEXT.md:529): UNCHANGED. No new threading / worker code; the e4 + e4b state machine carries through unchanged. (No new bullet in §8.x is expected either — e5b is purely an extension of §3's existing numba bullet.)

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Numba caching docs | numba.readthedocs.io/en/stable/developer/caching.html | Each `@njit(cache=True)` function gets its OWN `.nbi/.nbc` pair in `surfaces.py`'s `__pycache__`. Cache key includes function source hash, numba version, llvmlite version, CPU features (target_cpu). 11 kernels = 22 cache files; no cross-kernel collision risk because each file is keyed by qualified function name + source hash. | Confirms 11-kernel cache stacking is mechanically safe; per-kernel-independent. |
| Numba parallel docs | numba.readthedocs.io/en/stable/user/parallel.html | `prange` outer-loop with disjoint `out[i,...]` writes is bit-identical to serial (no reduction, no race). The 9 new v1 kernels all follow this pattern verbatim from the e5 template. | Confirms no per-kernel parallel-correctness audit needed; the proven Fermat/Enriques pattern transfers. |
| Numba power-operator behavior | numba.readthedocs.io/en/stable/reference/pysupported.html#operators | `x ** N` for integer N is lowered to a chain of multiplies internally (`x**5` ≈ `x*x*x*x*x` with intermediate fusion). For numeric-identity-with-NumPy, explicit `x*x*x*x*x` is the safer choice — guarantees the per-voxel op sequence matches the reference. | Specifically applies to Dwork (`**5`), Segre cubic (`**3`), sextic double solid (`**6` via `X2*X2*X2`). |
| e5 spike (this repo) | `.claude/notes/roadmaps/realtime-variety-render/spike-numba-arm64.md` | Per-kernel first-call JIT compile: ~300-400 ms for a typical `@njit(parallel=True)` polynomial kernel; ~700-1500 ms for the first kernel of a process (cold LLVM init dominates). 9 new v1 kernels = ~2.7-3.6 s additional cold-cache cost, paid lazily on each surface's first render off-thread on the e4 worker. With `cache=True` this is once-per-machine. Spike §4 and §6. | Bounds the v1 first-touch JIT-stacking cost; confirms it composes with the e4 worker (off-GUI-thread). |
| e5 implementation plan (this repo) | `.claude/notes/milestones/realtime-variety-render-e5/artifacts/implementation-plan.md` | The v0 pattern: kernel signature with `out` array, scalar params only; `prange` outer i; clip folded as scalar `if/elif`; rtol=atol=1e-9 in tests. v1 follows this verbatim — no architectural deviation. | The implementation template e5b should clone. |

(External research budget intentionally small per memory lesson: a pure mechanical-transcription milestone with a passed predecessor draws all signal from repo-local file:line attach points and the predecessor spike, not arXiv triangulation.)

## 4. Recommended approach

**Per-generator transcription.** For each of the 9 remaining implicit generators, follow the exact e5 pattern (the e5 implementation plan, item 2-3) without architectural deviation:

1. Add a module-level `@njit(parallel=True, cache=True) def _<surface>_field_kernel(g, <scalar params>, out)` in `surfaces.py` in the **Helpers section** (after `_enriques_fig1_field_kernel`, ~`surfaces.py:374`). The 9 kernel signatures are listed in §2 above.
2. The kernel body is a verbatim transcription of the generator's NumPy field expression in IDENTICAL operator order — `prange` outer i with `x = g[i]; x2 = x*x` hoisted (where reused), plain `range` j/k, scalar per-voxel polynomial, clip folded as `if val < lo: val = lo; elif val > hi: val = hi`. **Use explicit multiplies for `**N` operators** (e.g. `x*x*x` not `x**3`; `x2 = x*x; x4 = x2*x2; x5 = x4*x` for Dwork's `**5`; `x2*x2*x2` for sextic double solid's `**6`). The e5 kernels use explicit multiplies (`x2*x2` not `x**4`); v1 stays consistent.
3. Rewrite the generator's field block: keep `g = np.linspace(...)`, delete the `np.meshgrid + X2,Y2,Z2 + F = (...) + np.clip` block, replace with `F = np.empty((n, n, n), dtype=np.float64); _<surface>_field_kernel(g, <args>, F); return _marching_cubes_to_polydata(F, bounds[, second_smooth_iter=...])`. **Preserve every `int(round(n))` coercion** (AI-8) — for Enriques figs 2/3/4 that have `n` as a plain int kwarg, the existing `np.linspace`/`np.empty` calls already work; for Dwork/Kummer/etc. that pass `n` directly, no change needed. The kernel only sees `g` (float array) and float params.
4. **Preserve every ValueError pre-check and RuntimeWarning** (AI-14): Kummer's pole + no-zero-set guards at `surfaces.py:546-551` stay in the generator BEFORE the kernel call; Dwork's RuntimeWarning at `:979-990` stays BEFORE the kernel call; two_quadrics' RuntimeWarning at `:1137-1142` stays BEFORE the kernel call. The kernel never raises and never warns — it is pure compute.
5. **No worker / app / VARIETIES change.** The e4 + e4b plumbing is mode-agnostic. The 8 coarse-eligible new kernels (Kummer, Enriques 2/3/4, Dwork, fano_klein/segre/sexticDS) are invoked from inside `_marching_cubes_to_polydata` which is downstream of `params["n"] = surface.coarse_n` injection — composes mechanically. `fano_two_quadrics` (coarse_n=0) still benefits at full-res release.
6. **Tests.** Extend `tests/test_numba_field_kernels.py` with 9 new NumPy reference functions (verbatim copy-paste of each pre-e5b field expression), 9 `@pytest.mark.parametrize` blocks at ≥3 parameter points each (slider defaults, mixed interior, slider extremes — same structure as `_FERMAT_POINTS`), 9 clip-bounds tests (`test_<surface>_field_kernel_respects_clip_bounds`), and 9 additions to `test_kernels_have_a_zero_crossing_at_defaults`. Estimated test-budget impact: ~27 new test rows × ~10-30 ms each post-JIT-warmup ≈ +0.5-1.5 s. Total suite well under the 4 s CONTEXT.md §10 target.
7. **requirements.txt: NO CHANGE.** `numba>=0.65,<0.66` already pinned (line 5).
8. **CONTEXT.md §3 numba bullet:** edit "v0 scope is these 2 of 8 implicit generators; the rest are a future v1" → "v0+v1 covers all 11 implicit generators (Fermat, Kummer, Enriques figs 1-4, Dwork, Klein cubic, Segre cubic, two-quadrics tube, sextic double solid)". No other CONTEXT.md edits needed (§8.20, §9 unchanged).

**Off-screen verification (AI-3).** Per-generator post-edit render at slider defaults: `pv.OFF_SCREEN = True; gen = VARIETIES[variety][subtype].generate(); plotter.show(screenshot=...)`. Read the PNGs and compare against pre-e5b baseline screenshots (a short shell loop over the 9 subtypes; budget ~30 s once kernels are JIT'd).

Word count ~510.

## 5. Alternatives considered

- **Single generic `_polynomial_field_kernel(g, coeffs, out)`** with the polynomial parameterized as a coefficient table — rejected: hides the per-generator math behind a generic interface, breaks the "term-by-term transcription" numeric-identity discipline e5 chose for ease of audit, and complicates testing (the reference function would also need parameterization, doubling drift surface).
- **Numba-ize all 9 in one mega-PR vs. drip-feed 1-by-1** — recommended: ship all 9 in a single milestone (this is e5b's stated scope). The transcription discipline is mechanical and the e5 template is proven; serializing across 9 milestones would 9× the CONTEXT.md edits and merge cost for zero engineering benefit.
- **`@guvectorize` instead of `@njit(parallel=True)`** — rejected: e5 already chose `@njit(parallel=True)`; v1 must use the same machinery for consistency with §8.20's `workqueue` analysis.
- **Lift `np.clip` outside the kernel** — rejected (e5 lesson 159, 152): re-introduces a full-array NumPy temp pass, defeats fusion, AND breaks numeric-identity tests. The scalar `if/elif` clip is the proven pattern.
- **Cache the JITs eagerly at import** — rejected (e5 lesson, spike §4/§8): unnecessary; the e4 worker absorbs first-touch JIT cost off the GUI thread, `cache=True` makes it once-per-machine. Eager warm-up is dead code per the spike.
- **Cap `numba.set_num_threads(...)` for the new kernels** — rejected: e5 chose no cap; the rationale (single-flight + workqueue + e4 sequential kernel-vs-FlyingEdges) still holds, and capping would erode the v1 perf gain for no thread-safety win.
- **Skip `fano_two_quadrics` (it's coarse_n=0)** — rejected: full-resolution release renders still benefit from kernel speedup; the per-generator JIT cost is identical to any other kernel; no reason to opt out.

## 6. Risks and unknowns

- **R1 — `workqueue` single-flight constraint stacking** (the headline integration risk, CONTEXT.md §8.20). The constraint is ALREADY satisfied by the `_computing` single-flight guard at `app.py:613` and the `_pending_render`/`_pending_is_coarse` queue-latest semantics (`app.py:228, 662-672`). e5b stacks 9 more `@njit(parallel=True)` kernels but does NOT widen the constraint: only one kernel can ever run at a time process-wide (because only one `MeshWorker` is ever in flight). **No code change needed**; the §8.20 caveat literally already covers this. Mitigation: do not lift `_computing` without revisiting §8.20.
- **R2 — Dwork's `**5` operator** (the only e5b kernel using a fractional-not-perfect-power form): Numba lowers `x**5` to a chain of multiplies but the exact fold sequence is internal. The numeric-identity test (`np.allclose rtol=atol=1e-9`) catches any drift, but the **safer transcription** writes `x2 = x*x; x4 = x2*x2; x5 = x4*x; F = x5 + y5 + z5 + 2.0 - 5.0*psi*x*y*z`. Same applies to Segre's `**3` (`x*x*x`) and sextic double solid's `**6` (already written as `X2*X2*X2` in NumPy form `:1212-1213` — copy that pattern). **Action:** the implementer must NOT write `x**5` inside the Dwork kernel; explicit multiplies only.
- **R3 — Cold-cache JIT stacking cost** (~2.7-3.6 s spread across 9 first-touches): paid lazily off the GUI thread on the e4 worker, never on the GUI thread, once-per-machine via `cache=True`. **Not a blocker; not even a user-visible regression** because each generator's first-touch is ~300-400 ms which is INSIDE the surface's typical generate budget already (e.g. Enriques at 449 ms baseline absorbs the first compile invisibly). 9 cold-cache compiles will never happen in one session (no user clicks all 9 surfaces in one app launch); the typical user pays maybe 1-2 cold compiles per session, the rest hit the disk cache.
- **R4 — Numeric-identity drift at the ULP level on arm64** (e5 R3 still applies). `np.allclose(rtol=1e-9, atol=1e-9)` is the right tolerance; tighter tolerances (1e-12 from spike) would over-constrain on real generator kernels where reorderings happen. Per e5 lesson, 1e-9 is loose enough for IEEE-754 fused-vs-broadcast drift and tight enough that a sign error or dropped term fails loudly.
- **R5 — Per-kernel cache key invalidation**: editing any kernel's source auto-invalidates only that kernel's cache. Other 10 kernels' caches remain valid. No cross-kernel cache pollution. The `__pycache__/_*_field_kernel*.nbi/.nbc` files are gitignored (per CONTEXT.md §3 bullet).
- **R6 — Test-budget impact**: e5 was 14 tests in ~0.32 s (~22 ms per test, mostly JIT warmup amortized). v1 adds ~27 new test rows (9 generators × 3 parameter points) + 9 clip-bounds tests + 9 zero-crossing rows = ~45 new test cases. Marginal cost is low because the JITs warm up on the first call and subsequent calls are sub-ms. Estimated +0.5-1.5 s total test-suite latency. Total suite stays well under the 4 s CONTEXT.md §10 budget.
- **R7 — AI conflicts.** AI-1 numba already sanctioned (already a compute dep per e5). AI-2 tests are pure NumPy/Numba (no Qt). AI-3 off-screen verification only. AI-6 kernels stay downstream of `_marching_cubes_to_polydata`; Hanson parametric trio untouched. AI-8 `int(round(n))` coercions preserved in generators (Enriques fig 1 already has `n = int(round(n))` at `:614`; the others use plain int kwargs that don't need coercion but the pattern is safe to add for consistency). AI-14 every ValueError pre-check and RuntimeWarning preserved BEFORE the kernel call. **No new AI conflicts.**
- **R8 — Coarse-LOD interaction at coarse_n** (e4b composition). 8 of 9 new kernels run at coarse_n during drag (Kummer=100, Enriques 2/3/4=80, Dwork=100, Klein/Segre/sexticDS=80). The kernel is invoked from inside `_marching_cubes_to_polydata` which is downstream of any specific `n`; the worker stays mode-agnostic per CONTEXT.md §4.4. **No code change to the e4 worker or e4b coarse-LOD path needed in e5b.** Composes mechanically.
- **R9 — macOS arm64 residual** (carries forward from e5 spike §7): unchanged. The kernels are pure compute; the arm64-vs-x86 numeric drift risk is the same across all 11 kernels. The macOS on-device gate from e5 stays open until exercised on real Apple Silicon hardware — not an e5b blocker but a documented pre-ship checklist item.

## 7. AI-15 disclaimers

N/A. e5b adds no new variety, figure, or tooltip — it only changes *how* the 9 remaining implicit generators' scalar field arrays are computed (NumPy meshgrid-broadcasting → Numba JIT). The mathematical objects, their docstrings, the `VARIETIES` registry, `VARIETY_TOOLTIPS`, and `SUBTYPE_TOOLTIPS` are unchanged. The existing "real shadow / birational / parametric cross-section" disclaimers in each generator's docstring require no edit. The Preview-badge contract from CONTEXT.md §8.19 / AI-15 is preserved unchanged — the kernel is invoked at coarse_n during drag exactly the same as the NumPy form is today.

## 8. Open questions for the user

None — the milestone brief, the e5 implementation plan, the e5 research briefs, and the spike-numba-arm64 report fully specify the slice. The only genuinely-open items (macOS arm64 on-device checks from e5 spike §7) carry forward unchanged from e5; they are documented pre-ship gates, not e5b implementation ambiguities.
