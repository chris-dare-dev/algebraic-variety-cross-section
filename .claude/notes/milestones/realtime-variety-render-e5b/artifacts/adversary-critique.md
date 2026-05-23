# Adversary critique — Numba JIT field kernels v1 (e5b)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-23 | **Subject:** realtime-variety-render-e5b / 9df4a4f..73bbc1c

---

## Executive summary

The highest-severity code finding is MEDIUM: `_dwork_ref` and `_segre_cubic_ref` in `tests/test_numba_field_kernels.py` are not verbatim copies of the pre-e5b NumPy expressions as both the module docstring and the section header claim — they use the explicit `x2*x2*x` / `x*x*x` multiply chain matching the kernel rather than the original `X**5` / `X**3` operators. The research brief (agent-a-brief.md line 77) explicitly required the reference to use `X**5` to make the test independent; the implementation inverted this. The `atol=1e-9` tolerance happens to paper over the ULP gap, so all tests pass — but the "verbatim" contract in the test docstring is false, and a future maintainer who reads it as a spec will be misled. Zero CRITICALs. One process HIGH (auto diff-size, non-waivable). Three MEDIUMs, three LOWs. Foundation is technically sound: all AI invariants hold, all 11 implicit generators are correctly JIT-compiled, and numerical parity with the pre-e5b NumPy code is established at `rtol=atol=1e-9`. Safe to ship after MEDIUMs are addressed.

---

## Critical findings

None.

---

## High findings

### HIGH — Diff size exceeds 400-LOC review-quality threshold (auto-finding)

**Where:** no specific file (cross-cutting)
**Evidence:** `git diff 9df4a4f..73bbc1c | wc -l` produces 1548 lines. The 400-LOC threshold is the Cisco/LinearB defect-detection boundary; above it, human and agent review quality degrades measurably.
**Why it matters:** A single commit of this size makes atomic rollback impractical. The implementation plan explicitly specified "Commit ≤200 LOC each — likely 3 commits: (a) 4-5 kernels + generator rewrites, (b) remaining 4-5, (c) tests + CONTEXT.md"; that constraint was not followed. Reviewers cannot isolate a kernel-specific regression.
**Suggested fix:** No code change required for this commit. For future kernel-batch milestones, follow the plan's split: (a) first 4-5 kernels + generator rewrites, (b) remaining kernels, (c) tests + CONTEXT.md. The finding is non-waivable by policy.
**Regression-guard test:** Enforce the commit-size constraint procedurally in the milestone gate, not as a code test.

---

## Medium findings

### MEDIUM — `_dwork_ref` and `_segre_cubic_ref` are not verbatim pre-e5b expressions

**Where:** `tests/test_numba_field_kernels.py:318` (`_dwork_ref`) and `tests/test_numba_field_kernels.py:333` (`_segre_cubic_ref`)
**Evidence:** The pre-e5b `calabi_yau_dwork` used `F = X**5 + Y**5 + Z**5 + 2.0 - 5.0 * psi * X * Y * Z` (confirmed at `git show 9df4a4f:surfaces.py:993`). The test's `_dwork_ref` instead uses `X2*X2*X` (matching the kernel's explicit chain, not the original operator). Similarly, pre-e5b `fano_segre_cubic` used `X**3 + Y**3 + Z**3 + a**3 + b**3 - s**3` (old `:1089`), but `_segre_cubic_ref` uses `X3 = X*X*X`. The module docstring (line 14) and the section header (line 253) both say "which is reproduced verbatim below as the reference." The research brief (agent-a-brief.md line 77) explicitly specified: "NumPy reference in the test MUST also use `X**5` exactly as the pre-e5b form (NOT explicit multiplies) so the test pins the contract independently." IEEE-754 shows `x**5 != x2*x2*x` for typical `float64` values (difference ~3.5e-15 at `|x|=1.8`, comfortably within `atol=1e-9` at the field level, so tests pass). A transitive bug: if the kernel ever regresses to a wrong explicit multiply (e.g., `x2*x4` instead of `x4*x`), both kernel and reference would agree while diverging from the original — the test provides weaker guarantees than claimed.
**Why it matters:** The "verbatim reference" design is the whole point of the test: it should be an independent oracle, not an adaptation of the kernel's own strategy. CONTEXT.md §3 also says "NumPy reference verbatim from the pre-JIT generator body" — that claim is now false for two of nine new kernels.
**Suggested fix:** Restore `_dwork_ref` to use `X**5 + Y**5 + Z**5` (the original `X**5` form). Restore `_segre_cubic_ref` to use `X**3`, `a**3`, `b**3` (the original `X**3` operator form). The `atol=1e-9` tolerance is already wide enough to absorb the explicit-multiply→operator ULP gap, so the tests will still pass while actually being independent of the kernel's expand strategy.
**Regression-guard test:** `assert "_dwork_ref" in open("tests/test_numba_field_kernels.py").read()` is not sufficient. Add a sentinel comment or grep check: `grep "X\*\*5" tests/test_numba_field_kernels.py` must return a match.

### MEDIUM — CONTEXT.md §3 "verbatim" claim for Dwork and Segre references is false

**Where:** `CONTEXT.md:61` (the numba bullet, in the sentence "Numerical equivalence is pinned at `rtol=atol=1e-9` by `tests/test_numba_field_kernels.py` (45 tests; one parametrize block + clip-bounds assertion per kernel, NumPy reference verbatim from the pre-JIT generator body).")
**Evidence:** The "NumPy reference verbatim" phrase in CONTEXT.md is false for `_dwork_ref` and `_segre_cubic_ref` — both were adapted to use explicit multiply chains rather than the original `**5` / `**3` operators. This is the same root cause as the test-contract finding above but at the institutional-memory level.
**Why it matters:** CONTEXT.md is the agent-readable contract. A future agent reading "verbatim" will assume the reference independently validates the kernel; if the Dwork or Segre kernels are later rewritten, the agent will trust the test more than it should.
**Suggested fix:** Change "NumPy reference verbatim from the pre-JIT generator body" to "NumPy reference term-for-term from the pre-JIT generator body; powers **N>2 use the same explicit-multiply chain as the kernel for IEEE-754 op-order parity." This is honest about the adaptation.

### MEDIUM — Single commit violates implementation plan's "≤200 LOC each" discipline

**Where:** commit `20fa7ba` (all three files changed in a single commit: `surfaces.py` +437/-29, `tests/test_numba_field_kernels.py` +573/-47, `CONTEXT.md` +2/-2)
**Evidence:** The implementation plan (`.claude/notes/milestones/realtime-variety-render-e5b/artifacts/implementation-plan.md:55`) explicitly states "Commit ≤200 LOC each — likely 3 commits: (a) 4-5 kernels + generator rewrites, (b) remaining 4-5, (c) tests + CONTEXT.md." The single commit ships all three phases in one. The plan constraint exists to enable atomic rollback: if the Segre cubic kernel produces unexpected Numba codegen on arm64, the entire test+source commit must be reverted rather than just the one kernel.
**Why it matters:** Process discipline for multi-kernel batch milestones. The research brief (line 9) acknowledged the "fallback: ship the other 8 and leave that one on NumPy" strategy — a single commit makes that fallback expensive.
**Suggested fix:** No code change possible after the fact. Record in CONTEXT.md §8 or the milestone state that this was a single-commit delivery for e5b; future kernel batch milestones should split per the plan.

---

## Low findings

### LOW — Axis-symmetry coverage claim for sextic double solid is subtly overstated

**Where:** `tests/test_numba_field_kernels.py:35-37` (the axis-mapping note in the module docstring)
**Evidence:** The docstring says `_sextic_double_solid_field_kernel` "would surface an axis-swap bug" because "Z² plays a different role than X⁶/Y⁶." Numerical verification confirms this: `F(0.5, 0.3, 0.7) != F(0.7, 0.3, 0.5)` (diff ~0.14 at `alpha=0`, `r6=1`). The claim is correct. However the docstring also implies this makes it a full guard for the family — but at `alpha=0`, the field is symmetric in `X` and `Y` (since `X⁶ + Y⁶ = Y⁶ + X⁶`), so an `i<->j` (x<->y) transposition would NOT be caught by the equivalence test. Only an `i<->k` (x<->z) or `j<->k` (y<->z) swap is detectable. The docstring overstates "axis-swap bug" as if all three swaps are covered.
**Why it matters:** Documentation precision for future kernel authors. Not a bug — the actual implemented loop order (`i→x, j→y, k→z`) is correct.
**Suggested fix:** Qualify the axis-mapping note: "A `(k<->i)` or `(k<->j)` transposition would surface; a pure `(i<->j)` transposition is invisible at `alpha=0` (field is symmetric in x,y at that value) but the kernel's `i→x, j→y, k→z` order is visible at `alpha≠0` test points."

### LOW — `_enriques_fig3_field_kernel` docstring comment slightly imprecise about shadowing risk

**Where:** `surfaces.py:464-466` (`_enriques_fig3_field_kernel` docstring, lines: "Loop variable `k` shadows the conventional name; the kernel param is named `k_coef` to avoid the collision.")
**Evidence:** The shadowing is real — the inner `for k in range(n)` loop variable would shadow a parameter named `k`. The fix (`k_coef`) is correct. However the generator call site (`_enriques_fig3_field_kernel(g, k, F)`) passes the generator's local parameter `k` (a `float`) positionally — this is fine. The docstring could note that the renaming is a kernel-only concern; callers pass their `k` float positionally and are unaffected. Minor precision gap only.
**Why it matters:** Future author debugging why the kernel parameter isn't called `k` might be confused about whether the generator's `k` is correctly forwarded.
**Suggested fix:** Append to the docstring line: "callers pass their `k` float positionally and are unaffected by the rename."

### LOW — Dwork kernel docstring has a parenthetical typo (unclosed parenthesis)

**Where:** `surfaces.py:526` (the Dwork kernel docstring: "the only v1 kernel with **5 (the explicit x2 -> x4 -> x5 multiply chain preserves IEEE-754 op-order parity...")
**Evidence:** The docstring reads "with **5 (the explicit..." — the `**5` is the Markdown-escaped power operator but reads as a raw asterisk sequence in plain text. The open parenthesis on line 526 is closed many lines later (line 530) making the sentence hard to parse. This is the docstring in the production source, not the test file.
**Why it matters:** Cosmetic only; affects docstring readability.
**Suggested fix:** Rewrite: "the only v1 kernel using a 5th-power (the explicit x2→x4→x5 multiply chain preserves IEEE-754 op-order parity with the NumPy reference)."

---

## What was done well

- **Mechanical fidelity across all 9 kernels.** Every kernel follows the canonical `prange` outer-i / `range` j/k inner structure, hoists loop-invariant expressions correctly (`x2 = x*x` in the i-loop, `y2 = y*y` in the j-loop, etc.), and passes scalar pre-computes (`lam`, `sqrt2` for Kummer; `phi2`, `one_plus_2phi` for Enriques fig 4; `a3`, `b3` for Segre cubic; `p2`, `q2`, `eps2` for two-quadrics; `r6` for sextic double solid) so the kernels see only `float64` scalars and the 1-D `g` axis — matching the e5 v0 template precisely.

- **AI-14 preserved across all generators with pre-checks.** Kummer's pole/no-zero-set `ValueError` guards (lines ~855-859), Dwork's conifold `RuntimeWarning` (~1287-1296), and two-quadrics' voxel-resolution `RuntimeWarning` (~1459-1466) all fire in the generator BEFORE the kernel call. The block comment annotation on each generator correctly documents this invariant explicitly, making it auditable without running the code.

- **`k_coef` naming decision is correctly documented.** The kernel uses `k_coef` to avoid shadowing the `for k in range(n)` inner loop variable, and both the commit message and the docstring explain this. The generator call site `_enriques_fig3_field_kernel(g, k, F)` correctly passes the generator's float `k` positionally.

- **Powers `**N > 2` written as explicit multiply chains throughout.** The `x2*x2*x` chain for Dwork's quintic, `x*x*x` for Segre's cubic, and `x2*x2*x2` for sextic double solid's sixth power are all correct and match the explicit-multiply policy from the implementation plan. These are the only powers the e5 v0 templates never exercised, so getting them right first-time is notable.

- **Scalar pre-computes correctly placed for Numba.** In `_two_quadrics_field_kernel`, `p2 = p * p; q2 = q * q; eps2 = eps * eps` are pre-computed before the `prange` block — they execute once sequentially and are shared read-only across threads, which is both correct and slightly more efficient than recomputing per-voxel.

- **`int(round(n))` coercion added to all three Enriques fig 2/3/4 generators.** This brings fig 2/3/4 into parity with fig 1 (which already had the coercion from e5) — a defensive AI-8 hygiene fix that the implementation plan called out explicitly and the implementation delivers.

- **All 9 kernels include the `@njit(parallel=True, cache=True)` decorator.** Verified by inspection: lines 392, 426, 459, 484, 517, 553, 579, 611, 648 in `surfaces.py` each carry the decorator. No kernel was accidentally left as plain Python.

- **Axis-asymmetry coverage correctly identifies Klein cubic as the strongest guard.** The test module docstring correctly identifies `_klein_cubic_field_kernel` as the asymmetric kernel whose parametrize block genuinely catches axis-transposition bugs, and the numerical verification confirms `F(1,0,0) = 1.16 ≠ F(0,0,1) = 0.56 ≠ F(0,1,0) = 0.16` at `z0=0.4`.

- **Zero-crossing test updated for all 9 new kernels.** The `test_kernels_have_a_zero_crossing_at_defaults` function now covers all 11 kernels with realistic default-parameter grids. This is the downstream contract test that proves `_marching_cubes_to_polydata` will not raise `ValueError("No real zero set...")` at the kernels' default parameter values — a meaningful integration-flavoured assertion within the kernel-only test file.

- **45-test count in CONTEXT.md is arithmetically correct.** 2 kernels × 3 parametrize points + 2 clip tests + 1 zero-crossing (e5 v0) + 9 kernels × 3 parametrize points + 9 clip tests (e5b v1) + zero-crossing additions to the shared test = 45. The commit message's "+36 tests" is also correct (45 − 9 pre-existing = 36).

---

## Recommended rectification order

1. **Fix the MEDIUM test-reference inaccuracy (M1) and its CONTEXT.md companion (M2) in one pass.** Restore `_dwork_ref` in `tests/test_numba_field_kernels.py` to use `X**5 + Y**5 + Z**5` (the original operator form). Restore `_segre_cubic_ref` to use `X**3`, `a**3`, `b**3`. Update CONTEXT.md §3's "NumPy reference verbatim" to "NumPy reference term-for-term (powers **N>2 use the same explicit-multiply chain as the kernels for IEEE-754 op-order parity)." Run `pytest tests/test_numba_field_kernels.py -q` — all 45 tests should still pass since `atol=1e-9` bridges the ULP gap.

2. **Record the single-commit process deviation (M3).** Add a one-line note to the e5b milestone state or CONTEXT.md §8: "e5b shipped as a single commit for expediency; future kernel-batch milestones should follow the ≤200 LOC / 3-commit split specified in the implementation plan." No code change needed.

3. **Address the LOWs at the maintainer's discretion.** The sextic double solid axis-symmetry docstring clarification (L1), the `k_coef` docstring addition (L2), and the Dwork docstring parenthetical fix (L3) are cosmetic and should not block the milestone gate.

4. **The HIGH (auto diff-size) requires no code action.** Disposition: "no code action required — artifact inflation from single-commit delivery." Note the breakdown: ~437 LOC production code (surfaces.py), ~573 LOC tests, ~2 LOC CONTEXT.md, remainder chore commit.

---

*End of critique. Mandatory rectification: MEDIUMs M1, M2 (test reference + CONTEXT.md honesty). M3 is process-only — note it and move on. HIGH is auto-finding with no code action. LOWs are optional.*

---

## Rectification status (2026-05-23, Phase 4)

**Fixed (code change landed in the rect commit):**
- **M1** — ``tests/test_numba_field_kernels.py``: restored ``_dwork_ref`` to use ``X ** 5 + Y ** 5 + Z ** 5`` and ``_segre_cubic_ref`` to use ``X ** 3 + Y ** 3 + Z ** 3 + a ** 3 + b ** 3 - s ** 3`` (verbatim operator forms from the pre-e5b NumPy generator bodies, not the explicit-multiply chains the kernels use).  Docstrings updated to spell out the "independent oracle" rationale.  Tolerance ``atol=1e-9`` absorbs the ~3.5e-15 ULP gap; all 45 kernel-equivalence tests still pass.
- **L1** — module docstring axis-mapping note corrected: clarified that ``_sextic_double_solid_field_kernel``'s X-Y symmetry is invariant across all parameter values (the ``α·X²Y²·(X²+Y²)`` term is also symmetric in X<->Y, not just the ``X⁶+Y⁶`` term), so ``(i<->j)`` swap coverage is delegated to Klein cubic.
- **L2** — ``surfaces.py``: appended one sentence to ``_enriques_fig3_field_kernel`` docstring explaining the ``k_coef`` rename is kernel-internal-only and callers forward their float ``k`` positionally without effect.
- **L3** — ``surfaces.py``: rewrote the awkward parenthetical in ``_dwork_field_kernel`` docstring ("the only v1 kernel with **5 (the explicit...") into two clean sentences.

**Invalidated transitively:**
- **M2** — CONTEXT.md §3's "NumPy reference verbatim from the pre-JIT generator body" claim is now true (M1 fix restored the operator forms).  No CONTEXT.md change required.

**Acknowledged-process, no code action:**
- **H1** — Diff-size 1548 lines exceeds the 400-LOC review-quality threshold.  Auto-finding, non-waivable by policy; recorded for future kernel-batch milestones (split per the implementation plan's a/b/c commit boundaries).
- **M3** — Single-commit delivery violated the implementation plan's "≤200 LOC each / likely 3 commits" guidance.  Acknowledged in the rect commit body; no code change possible after the fact.  The same a/b/c split applies to future kernel-batch milestones.

**Test run:** ``.venv/Scripts/python.exe -m pytest tests/ -q`` → 446 passed (unchanged from Phase 2).
