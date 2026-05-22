# Adversary critique — Enriques bounds-padding (Path B spike outcome)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** `enriques-taubin-spike-2026q2-e1`, commit `51b0a17..b4226bd`

---

## Executive summary

No CRITICALs or MEDIUMs. One process HIGH (auto-finding: 901 LOC diff size) with no code action required — 71% of the diff is documentation, artifacts, and research briefs. Three LOWs: the spike timing log's single-pass label says "bounds=1.8" but the measurement was run against the production generator after the default was already changed to 1.89 (the Path B conclusion is robust regardless — 87.5 ms margin); a misleading comment in the test about why `abs_tol=1e-9` is needed (the math is correct, the justification conflates computed vs stored literals); and the test name could reference the spike outcome more directly. The functional change is 51 LOC (8 production, 43 test), all four bounds defaults are correct, AI-14 spacing arithmetic verifies exactly, and the Path B deferral is honest and well-documented. The bounds-padding change is safe to ship.

Severity counts: **0 CRITICAL, 1 HIGH (process auto-finding), 0 MEDIUM, 3 LOW.**

---

## Verdict

SHIP-WITH-FIXES is not warranted — the LOWs are cosmetic. **SHIP.** The functional change is a correct 4-line default adjustment backed by a sound regression guard. The Path B timing outcome is honest, the deferral rationale is specific and actionable, and all AI-1..AI-15 invariants are clean. Rectify the three LOWs at maintainer discretion before the HQ-smoothing follow-on milestone opens.

---

## Critical findings

None.

---

## High findings

### HIGH — Diff size exceeds 400-line review-quality threshold

**Where:** no specific file (cross-cutting, process finding)
**Evidence:** `git diff 51b0a17..HEAD | wc -l` = 901 lines, exceeding the 400-line defect-detection threshold documented in the adversary-checklist (Cisco / LinearB research). Breakdown: 8 LOC production code, 43 LOC test code, 206 LOC spike script, 644 LOC documentation and artifacts (71% of total).
**Why it matters:** diffs above 400 LOC statistically show reduced defect detection per-reviewer; however, when the overwhelming majority of lines are non-code artifacts, the per-reviewer load on the logic delta (51 LOC) remains within safe bounds. No code action is required.
**Suggested fix:** No code change needed. For future spike milestones, consider committing the timing artifact and research brief in a separate chore commit to keep the functional delta reviewable in isolation.
**Regression-guard test:** N/A — this is a process finding, not a defect in the implementation.

---

## Medium findings

None.

---

## Low findings

### LOW — Timing log labels single-pass baseline as "bounds=1.8" but measurement may reflect bounds=1.89

**Where:** `.claude/scripts/enriques-taubin-spike.py:132–134` and `.claude/notes/milestones/enriques-taubin-spike-2026q2-e1/artifacts/timing-log.txt:8`
**Evidence:** The spike script calls `surfaces.enriques_figure_1(c=1.0)` with no explicit `bounds=` kwarg for the single-pass baseline. The production default was changed from 1.8 to 1.89 in the same commit that committed the timing log. If the spike was run after the default was changed (the common case when all changes land in one commit), the "Single-pass (production, bounds=1.8)" label in the timing log misattributes the bounds. Both the 449.3 ms and 587.5 ms figures are correct measurements of whatever bounds were active at run time; the Path B conclusion (587.5 > 500 ms, 87.5 ms margin) is robust to the ~1–3 ms difference between bounds=1.8 and bounds=1.89 single-pass times.
**Why it matters:** A future `enriques-hq-smoothing-2026q3-e1` implementer reading this log to establish a baseline may mis-attribute the 449.3 ms figure to bounds=1.8 and then be confused when re-running against the current codebase (which uses 1.89) produces a similar number. The confusion is cosmetic but could waste investigation time.
**Suggested fix:** Update the spike script's print string and the timing log comment to say `"Single-pass (production, bounds=DEFAULT_AT_TIME_OF_MEASUREMENT)"`, or add an inline note: `# bounds default at measurement time: see git log for surfaces.py at commit b4226bd`.

---

### LOW — `abs_tol=1e-9` comment conflates computed vs stored literals

**Where:** `tests/test_mesh_generators.py:893`
**Evidence:** The comment reads: `# math.isclose with a small absolute tolerance to handle / # floating-point representation (1.5 * 1.05 = 1.5750000000000002)`. The test never computes `1.5 * 1.05`; it compares `inspect.signature`-extracted defaults (stored Python float literals from `surfaces.py`) against hardcoded float literals in the test tuple. Both sides are the same stored object so the comparison is exact (diff = 0). The `abs_tol=1e-9` would be needed only if a future maintainer changed `surfaces.py` to compute the default as `1.5 * 1.05` at module level rather than storing the literal `1.575`. The tolerance is correct and future-safe; the comment's framing misleads current readers into thinking there is a floating-point representation problem that needs handling now.
**Why it matters:** The next maintainer reading this test comment may incorrectly infer that Python's float representation of `1.575` is imprecise and unnecessarily propagate defensive tolerance patterns elsewhere. No bug; purely a documentation clarity issue.
**Suggested fix:** Rewrite the comment to: `# abs_tol handles future refactors where the default is computed (e.g., 1.5 * 1.05) # rather than stored as a literal; two stored literals compare exactly (diff=0).`

---

### LOW — Test name does not reference spike outcome or Path B disposition

**Where:** `tests/test_mesh_generators.py:856`
**Evidence:** The test is named `test_enriques_figures_have_padded_bounds_defaults`. The docstring mentions "Path B (bounds-padding only; second Taubin pass deferred over-budget)" but the function name itself carries no signal that this guards against undoing a spike-decided default. A future maintainer who sees only the test name in a failing CI run has no immediate context that this is a spike-outcome guard.
**Why it matters:** When this test fires in a future refactor, the first-line triage ("what is this test for?") is served better by a name that says `test_enriques_bounds_padded_by_spike_path_b` or simply `test_enriques_padded_bounds_defaults_path_b`. Pure cosmetic; no functional impact.
**Suggested fix:** Rename to `test_enriques_figures_padded_bounds_spike_path_b` and keep the docstring. One word is enough to anchor future readers to the spike context.

---

## What was done well

- **Honest Path B disposition.** The timing log is committed verbatim with all seven raw measurements, the median, the overhead, and the budget headroom. Future maintainers can verify the decision without re-running the spike. The commit message explicitly names the pre-committed threshold and why Path B was triggered.

- **Spike script self-containment.** `enriques-taubin-spike.py` is a standalone, importable harness placed under `.claude/scripts/` (not `tests/`), correctly separated from the AI-2-gated test suite. The exit code mirrors the A/B outcome for optional CI integration.

- **Double-pass formula fidelity.** `_enriques_double_pass` in the spike script exactly mirrors `enriques_figure_1`'s field definition (`F = X2*Y2 + X2*Z2 + Y2*Z2 + X2*Y2*Z2 + c*(X*Y*Z)*(1.0+X2+Y2+Z2)`), the clip bounds (`±10`), the clean step, the first Taubin pass (`n_iter=20, pass_band=0.1`), and the `compute_normals` kwargs. The spike measured what production would actually have shipped.

- **N=7 median methodology.** Using seven runs and taking the median (not mean) to filter warm-up noise is the correct approach for a 0.4–0.6 s workload where one outlier run can bias a mean by 5–10%. The methodology is documented in the timing log header.

- **AI-14 spacing arithmetic is correct.** Verified: `2 × 1.89 / 239 = 0.01582` (Fig. 1), `2 × 2.625 / 239 = 0.02197` (Fig. 3), `2 × 1.575 / 219 = 0.01438` (Fig. 4) — all well above the practical marching-cubes floor. CONTEXT.md §8.16's claims are accurate to 5 significant figures.

- **Regression test uses `inspect.signature` over mesh extent.** Asserting on function defaults rather than mesh bounds is the correct design: mesh extent is parameter-dependent, but the sampling-box default is a static property. The test will fire on any future revert to the pre-spike defaults regardless of parameter value.

- **All four Enriques figures padded consistently.** The ×1.05 padding is universal (not topology-selective), matching the research brief's reasoning: wing-tip truncation is a sampling-bounds artifact independent of node topology. The second Taubin pass (deferred) is topology-selective; the bounds padding is not.

- **CONTEXT.md §8.16 deferral path is specific and actionable.** The provisional follow-on milestone id (`enriques-hq-smoothing-2026q3-e1`), the mechanism (opt-in slider in Parameters panel), and the tradeoff framing ("power users get quality, default keeps 449 ms baseline") are all present. This is the minimum needed for a future implementer to pick up the work without re-litigating the deferral.

- **No call-site breakage.** Grep confirms zero explicit `bounds=1.8 / 2.5 / 1.5` call sites in app.py, tests, or scripts that would now silently behave differently with the updated defaults. The only occurrence is a code comment on surfaces.py line 837 (Segre cubic, unrelated).

- **Test count reported accurately.** Commit message says "338 passed (337 baseline + 1 new)" — the test addition is incremental and the count is checkable against a clean run.

---

## Recommended rectification order

1. **No blocking fixes.** The three LOWs are all documentation/naming improvements; none block merge.
2. **LOW L1 (timing log label):** Update spike script print strings to acknowledge the bounds ambiguity; add a one-line note to timing-log.txt header. This protects the future HQ-smoothing milestone's author from confusion.
3. **LOW L2 (test comment):** Rewrite the `abs_tol` comment in `test_enriques_figures_have_padded_bounds_defaults` to clarify the prospective vs current semantics.
4. **LOW L3 (test name):** Optional rename before the HQ-smoothing milestone opens, so CI failure messages are self-describing.

---

*End of critique. No mandatory rectification. All findings are LOWs plus one non-actionable process HIGH.*

---

## Rectification status (orchestrator, 2026-05-22)

**Fixed in rect commit:** all three LOWs (documentation-clarity batch).

- **L1 (timing-log bounds-ambiguity)**: The spike script now resolves the current `enriques_figure_1.bounds` default via `inspect.signature` at print time and labels the baseline accordingly — re-running the spike post-Path-B will say `bounds=1.89` instead of misattributing to `bounds=1.8`. Additionally added a clarifying note to the committed `timing-log.txt` explaining that the captured numbers reflect the pre-Path-B production state (bounds=1.8), and that re-running post-Path-B against bounds=1.89 would produce a ~1-3 ms swing — negligible vs the 87.5 ms margin to the 500 ms budget, so the Path B conclusion stays robust. Future HQ-smoothing milestone authors reading this log now get the right context.

- **L2 (test comment `abs_tol` framing)**: Rewrote the `math.isclose(abs_tol=1e-9)` comment to clarify the prospective-vs-current semantics. The previous comment implied a current floating-point problem (`1.5 * 1.05 = 1.5750000000000002`) but the test never computes `1.5 * 1.05` — both sides are stored literals, the comparison is exact (diff = 0). The new comment explicitly frames the tolerance as forward-protection: if a future refactor changes the default to a computed value, the test still passes. No false-positive defensive-pattern propagation.

- **L3 (test name)**: Renamed `test_enriques_figures_have_padded_bounds_defaults` → `test_enriques_figures_padded_bounds_spike_path_b` so a future CI failure message immediately signals "this guards the spike-Path-B outcome" rather than just "default got changed." The docstring already explained the context; the function name now matches.

**Deferred:** none — all three LOWs fixed.

**Process-only:**
- **H1 (901-LOC diff)**: ~71% milestone documentation + spike artifacts. No code action.

**Invalidated:** none — all three LOW findings re-verified present before fixing.

**Test suite:** 338 passed (unchanged — the rename was applied in-place; the test count stays at 338, with the renamed test still firing under its new name).

**Architecture lesson recorded:** the spike script's `inspect.signature`-based baseline-label resolution is the right pattern for any future spike harness that may be re-run after its decision lands — never assume the production default that was active at first measurement is still active at re-measurement. This pattern is now reusable for the future `enriques-hq-smoothing-2026q3-e1` milestone's own timing harness if/when it opens.
