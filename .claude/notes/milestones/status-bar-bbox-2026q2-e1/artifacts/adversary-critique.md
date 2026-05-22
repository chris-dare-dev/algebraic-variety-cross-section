# Adversary critique — status-bar bbox readout

**Reviewer:** milestone-adversary-critic (read-only)
**Date:** 2026-05-22
**Subject:** status-bar-bbox-2026q2-e1 · `0e2e8105..HEAD` (1 commit)
**Diff stats:** 8 files changed, 365 insertions (+0 deletions) — 429 total diff lines

---

## Executive summary

No CRITICALs. No HIGHs on the code path. One mandatory HIGH is logged for the 429-line diff total (Cisco / LinearB review-quality-at-risk threshold is 400 LOC; not waivable per checklist), though ~271 of those lines are documentation artifacts with no execution risk. One MEDIUM for a factual count error in CONTEXT.md (claims "12 implicit-surface generators" but the registry contains 11 symmetric implicit generators and 3 Hanson parametric generators — 14 total). One MEDIUM for a test coverage gap on the Hanson generators (the documented "approximate" case for ±max framing has no bbox-format regression test). One LOW for a misleading docstring in `test_bbox_max_extents_are_positive_for_symmetric_generator`. All AI invariants (AI-9, AI-10, AI-14, AI-2) are confirmed clean by direct code inspection.

**Verdict: SHIP-WITH-FIXES.** The two MEDIUMs are low-risk but correctable: a one-word count fix in CONTEXT.md and one new test case. No blocker on the core implementation.

---

## Critical findings

None.

---

## High findings

### HIGH — review-quality-at-risk: diff exceeds 400-LOC threshold

**Where:** no specific file (cross-cutting)
**Evidence:** `git diff 0e2e8105..HEAD | wc -l` returns 429 lines, exceeding the 400-line defect-detection threshold documented in the checklist (Cisco / LinearB research). Of the 429 lines, approximately 271 are milestone documentation artifacts (research brief 203 lines, state.json 50 lines, implementation plan 16 lines, dispatch log 2 lines); the code-change surface is ~87 lines (app.py +10, tests/ +75, CONTEXT.md +2).
**Why it matters:** The checklist mandates this finding regardless of cause. At-a-glance, the large diff size may compress per-line attention during review, but in practice the artifact lines carry no execution risk — this finding's empirical severity is LOW for this particular commit.
**Suggested fix:** No code change required. Document in the rectification record that the LOC overage is dominated by documentation artifacts. For future milestones, consider a `.gitignore` or pipeline filter that excludes research-brief content from the commit diff that passes through adversarial review gates.

**Regression-guard test:** Not applicable — this is a pipeline-process finding, not a code defect.

---

## Medium findings

### MEDIUM — incorrect generator count in CONTEXT.md forward-maintenance note

**Where:** `CONTEXT.md:137`
**Evidence:** The new paragraph states "the 12 implicit-surface generators in the live registry (all use symmetric `np.linspace(-bounds, bounds, n)` sampling boxes)". Direct count from `surfaces.py` (confirmed by `grep -n "^def " surfaces.py` and `grep -n "linspace" surfaces.py`): there are 11 symmetric implicit-surface generators (fermat_quartic, kummer_surface, enriques_figure_1–4, calabi_yau_dwork, fano_klein_cubic, fano_segre_cubic, fano_two_quadrics, fano_sextic_double_solid) and 3 Hanson parametric generators (calabi_yau_quintic, calabi_yau_cubic, calabi_yau_asymmetric) — 14 total, not "12 of 13". The same off-by-one error appears in the commit message body ("12 of 13 generators") and the research brief.
**Why it matters:** CONTEXT.md is the institutional-memory contract read by future milestone agents. An agent reading "12 implicit-surface generators" would miscount by one when auditing the registry, potentially concluding a new generator was added or one was removed. The forward-maintenance guidance ("if a future generator uses a non-centered sampling domain...") is sound; only the count is wrong.
**Suggested fix:** Replace "12 implicit-surface generators" with "11 implicit-surface generators" in `CONTEXT.md:137`. No code change needed. The commit message body ("12 of 13") is already committed and immutable; no action required there.

---

### MEDIUM — no bbox-format regression test for Hanson parametric generators

**Where:** `tests/test_status_bar_bbox.py` (no specific line — gap, not a line-level bug)
**Evidence:** The four tests in `test_status_bar_bbox.py` cover `fermat_quartic` (twice) and `kummer_surface` (once), plus the `ValueError` path. None of the three Hanson parametric generators (`calabi_yau_quintic`, `calabi_yau_cubic`, `calabi_yau_asymmetric`) are exercised. These three generators are the documented "approximate" case for ±max framing (theta ∈ [0, π/2]). If a future change to `_hanson_cross_section` produced NaN vertex coordinates (e.g., a degenerate phase configuration), `mesh.bounds` would return `nan` and the status bar would display `bbox ±nan × ±nan × ±nan`. This would not be caught by the current test suite.
**Why it matters:** The Hanson generators are the only cases where the ±max display is an over-approximation — exactly the class of generators most likely to expose format-contract drift. The CONTEXT.md note says "Format-contract guard: `tests/test_status_bar_bbox.py`" but the guard only covers symmetric implicit generators.
**Suggested fix:** Add a fifth test `test_bbox_format_matches_regex_on_hanson_quintic` that calls `calabi_yau_quintic()` at defaults and asserts `BBOX_REGEX.fullmatch(_format_bbox(mesh))`. This is Qt-free (AI-2 compliant) and runs in <1 s. Optionally add assertions that `mesh.bounds[1]`, `mesh.bounds[3]`, `mesh.bounds[5]` are all finite (not NaN/Inf) to guard the over-approximation assumption.

**Regression-guard test:** `assert math.isfinite(b[1]) and math.isfinite(b[3]) and math.isfinite(b[5])` in the new Hanson test ensures bounds are finite, catching any future NaN-producing change to `_hanson_cross_section`.

---

## Low findings

### LOW — test docstring overclaims coverage ("all 12 implicit-surface generators")

**Where:** `tests/test_status_bar_bbox.py:40–46`
**Evidence:** The docstring for `test_bbox_max_extents_are_positive_for_symmetric_generator` reads: "All 12 implicit-surface generators in the live registry produce strictly positive max-extents at defaults." The test body only calls `fermat_quartic()` — one of the 11 (not 12) symmetric generators. A future reader cannot rely on the docstring claim without running the other 10 generators.
**Why it matters:** Docstring overclaims are a slow-poison pattern: a future agent reading this test assumes 12 generators were verified, but only 1 was. The count error also propagates the incorrect "12" figure.
**Suggested fix:** Change "All 12 implicit-surface generators" to "A representative symmetric-sampling-box generator (Fermat quartic)" in the docstring. Alternatively, parameterize the test across all 11 symmetric generators using `@pytest.mark.parametrize`, but that may be out of scope for a LOW.

---

## What was done well

- **AI-9 compliance is airtight.** The `_b = self._raw_mesh.bounds` read at `app.py:439` is a pure O(1) VTK attribute access — no I/O, no `processEvents()`, no re-entrancy window. The existing `_computing` guard at `app.py:377–379` was not disturbed.

- **AI-10 compliance is structurally correct.** The bounds read occurs at `app.py:439`, which is after `_apply_domain_and_render` has already returned at line 418. `self._raw_mesh` is the un-clipped raw mesh (set at line 395); the domain clip operates on a separate `clipped` variable inside `_apply_domain_and_render`. The status bar therefore reports the spatial extent of the full mathematical surface, not the viewport slice — the intended semantics.

- **AI-14 compliance is verified by both code inspection and a dedicated test.** The `except ValueError` (line 400) and `except Exception` (line 413) branches both set `self._raw_mesh = None` and `return` before the `base_msg` block at line 440. `test_valueerror_path_cannot_produce_bbox` in the new test file closes the loop by confirming `kummer_surface(mu_squared=0.2)` raises `ValueError` before any mesh is built — a clean generator-contract guard.

- **AI-2 compliance is solid.** `tests/test_status_bar_bbox.py` imports only `re`, `pytest`, and `surfaces` — no Qt, no `MainWindow`, no `QApplication`. The comment in the docstring ("No `MainWindow`, no `QApplication`") explicitly documents the AI-2 rationale, which is good institutional memory hygiene.

- **The BBOX_FORMAT / BBOX_REGEX mirroring is the right pattern.** By defining `BBOX_FORMAT` as a str.format template in the test (mirroring the app.py f-string), the test verifies the format contract without importing app.py (which would pull in PySide6 and break AI-2). This is the same defensive pattern used by `test_styles_palette.py` — consistent with the codebase's test architecture.

- **CONTEXT.md forward-maintenance note is thorough.** The single paragraph at line 137 documents (a) the format string, (b) which generators are exact vs. approximate, (c) the fallback format for future asymmetric generators, (d) the AI-10 and AI-14 invariant compliance, and (e) a pointer to the test file. A future implementer adding a non-centered generator can follow the upgrade path without reading the diff.

- **The Hanson over-approximation is honestly named.** Rather than silently using ±max for all generators, the implementation documents the approximation in the source comment at `app.py:431–438` and in CONTEXT.md §4.3. The phrase "honest over-approximation" is the correct epistemic framing (AI-15 spirit applied to a display convention).

- **The `_b` local variable avoids calling `.bounds` twice.** The bounds tuple is cached in `_b` at line 439 before being indexed three times in the f-string at line 443. This is a minor performance courtesy and also makes the f-string readable at a glance.

---

## Recommended rectification order

1. **Fix the MEDIUM generator count** in `CONTEXT.md:137` — one-word change: "12" → "11". Also apply the same fix to the `test_bbox_max_extents_are_positive_for_symmetric_generator` docstring (LOW M1 shares the same root cause — batch both in one pass).

2. **Add the Hanson bbox-format regression test** — add `test_bbox_format_matches_regex_on_hanson_quintic` to `tests/test_status_bar_bbox.py` calling `calabi_yau_quintic()` with BBOX_REGEX assertion and `math.isfinite` bounds guard. This closes the MEDIUM coverage gap and doubles as the regression-guard test for the approximate-±max path.

3. **HIGH review-quality-at-risk** — no code action required; log the disposition in the milestone state.json as "resolved-no-code-change / doc-artifacts inflated total".

---

*End of critique. Mandatory rectification: the HIGH (process disposition only) and both MEDIUMs. The LOW is optional but efficient to batch with M1.*

---

## Frontend UI/UX findings

*Merged from `frontend-critique.md` (milestone-frontend-ux-critic). The Qt-panel critic emitted 0 CRITICAL, 0 HIGH, 2 MEDIUM, 2 LOW. Severity-ids prefixed with `F-` to disambiguate from the adversary's findings above.*

### MEDIUM — F-M1: status-bar Dwork warning path overflows at ~294 chars

**Where:** `app.py` (the `f"⚠ {_surface_warning}  |  {base_msg}"` line on the warning path)
**Evidence:** Empirical: the Dwork conifold `RuntimeWarning` text is ~145 chars; combined with `base_msg` including the new bbox suffix the full string reaches ~294 chars. A default Qt window at ~1000 px with an 11 px monospace font fits roughly 120–130 chars before `QStatusBar` silently clips the trailing content. The new bbox suffix is therefore never visible on the one render path where the user is most likely to want it (conifold mesh is geometrically unusual).
**Why it matters:** The warning path is exactly where spatial extent is most informative — a hidden bbox suffix defeats the milestone goal on that path. Status-bar clipping is silent (no ellipsis), so the loss is invisible to the user as well as the developer.
**Suggested fix:** Move the bbox suffix BEFORE the warning text on the warning path so the most-likely-clipped content is the warning prose, not the bbox: `f"⚠ {warning}  ·  {label} · verts/faces · bbox …  ·  params"`. Alternatively shorten warning text with an ellipsis at 80 chars. Either keeps the bbox visible at default window widths. Rectification scope: 2–4 lines in `app.py:_render_current`.

### MEDIUM — F-M2: Hanson `±max` framing silently over-approximates user-visible asymmetry

**Where:** `app.py` bbox format line
**Evidence:** At default params (`alpha=π/4, grid=41, xi_max=2.0`), Hanson quintic has `xmin=-1.0670, xmax=1.1895` — ~0.12 unit asymmetry. The display shows `±1.19`, implying bilateral symmetry that does not hold. CONTEXT.md §4.3 documents this as an "honest over-approximation" but the disclosure is maintainer-only — users see `±1.19` and may assume a centered mesh.
**Why it matters:** Researchers comparing surfaces or positioning clip planes will see a reported `±1.19` that doesn't match the actual x-range visible in the VTK viewport. For a tool aimed at mathematical rigour the silent over-approximation contradicts the documented goal.
**Suggested fix:** Three options ordered by ambition: (a) Switch to full-extent widths `size: Lx × Ly × Lz` using `bounds[1]-bounds[0]` etc. — peer-aligned (see F-L1), eliminates asymmetry caveat, removes the misleading `±` token. (b) Add a parenthetical `(approx.)` on the Hanson rows only — minimal UX impact, makes the disclosure user-visible. (c) Per-generator format flag on `Surface` (e.g. `symmetric_bounds: bool`) — most thorough but breaks the existing `Surface` dataclass shape. **V1 recommendation: option (a) full-extent format, combined with F-L1.**

### LOW — F-L1: `bbox` vocabulary diverges from peer tools

**Where:** `app.py` bbox format line
**Evidence:** ParaView shows `X Range: -1.000 to 1.000` per axis; MeshLab shows `X: 2.000  Y: 2.000  Z: 2.000` (full extents); Blender shows `Dimensions: X: 2.00 m  Y: 2.00 m  Z: 2.00 m` (full extents). All three peers use full-extent widths and avoid the `±` half-extent convention. AVC's `bbox ±1.19 × ±1.19 × ±1.52` is the outlier — both in label (`bbox` vs `Dimensions`/`size`/`X Range`) and in convention (half-extent vs full-extent).
**Why it matters:** Researchers cross-tool habit will mentally double the `±` value to recover the full extent they're used to. Minor friction but consistent across peer tools, so consistency has real value.
**Suggested fix:** Adopt `size: {Lx:.2f} × {Ly:.2f} × {Lz:.2f}` (full extents). Solves F-M2 simultaneously. Single-line change.

### LOW — F-L2: `.2f` precision can produce false equalities at sub-1.0 extents

**Where:** `app.py` bbox format line
**Evidence:** Two-quadrics CI tube at defaults shows `±0.53 × ±0.76 × ±0.99` — `0.53` is 2 sig figs. Adjacent surfaces with extents 0.53 and 0.54 both display as `0.53`. `.3f` would give consistent 3-sig-fig precision (`±0.530`).
**Why it matters:** Cosmetic at current slider granularities but a research tool that quietly rounds adjacent values to the same display is a small honesty risk.
**Suggested fix:** `:.2f` → `:.3f`. Costs 9 chars in worst-case message length, which interacts with F-M1's overflow concern. Defer pending F-M1 decision.

---

## Combined rectification order

1. **CONTEXT.md generator count fix + LOW-1 test docstring** (M1 + L1, ~2-LOC) — one-pass batch, no behavioral change.
2. **Hanson bbox regression test** (M2, ~10 LOC) — add `test_bbox_format_matches_regex_on_hanson_quintic` with `math.isfinite` bounds guard.
3. **F-M1 status-bar overflow on Dwork warning path** (~4 LOC) — re-order the warning-path `showMessage` so bbox precedes warning prose; clip-tolerant.
4. **F-M2 + F-L1 combined: switch to full-extent format** (`size: Lx × Ly × Lz`, ~3 LOC + comment update + CONTEXT.md note adjustment) — eliminates the Hanson over-approximation, aligns with peer vocabulary, removes the misleading `±` token. **Optional V0 / mandatory V1.** Decision belongs to the orchestrator (and indirectly to the user): the `±max` framing was the explicit roadmap spec, so swapping format mid-milestone is a scope question, not a defect closure.
5. **F-L2 precision** — defer pending decision on F-L1 (precision interacts with format choice).
6. **HIGH (diff LOC overage)** — process disposition only; no code change.

---

## Rectification status (orchestrator, 2026-05-22)

**Fixed in rect commit (single batch):**
- **M1** — CONTEXT.md §4.3 generator count `12` → `11` implicit, with explicit family enumeration (fermat_quartic, kummer_surface, enriques_figure_1..4, calabi_yau_dwork, fano_klein_cubic, fano_segre_cubic, fano_two_quadrics, fano_sextic_double_solid); Hanson parametric block enumerated separately (3 generators). Source comment in app.py also updated.
- **L1** — `test_bbox_max_extents_are_positive_for_symmetric_generator` docstring softened to "A representative symmetric-sampling-box generator (Fermat quartic)"; the all-11-generators claim moved to CONTEXT.md §4.3 (the right home for institutional contracts).
- **M2** — New `test_bbox_format_matches_regex_on_hanson_quintic` exercises `calabi_yau_quintic()` at defaults, asserts `BBOX_REGEX.fullmatch` plus `math.isfinite` on `bounds[1]`/`[3]`/`[5]`. Closes the format-contract gap for the approximate-`±max` path and guards against future NaN-producing changes to `_hanson_cross_section`.
- **F-M1** — Warning path refactored: bbox suffix hoisted to immediately follow the `⚠ {warning}` prefix; verbose `{label} verts, faces{params}` moved to trailing position. Preserves bbox visibility on the Dwork conifold render path where it is most informative. Comment block in app.py and CONTEXT.md §4.3 both document the priority rationale.

**Deferred:**
- **F-M2** + **F-L1** — Switch from `±max` half-extent to `size: Lx × Ly × Lz` full-extent format. Compelling on the merits (peer-aligned with ParaView/MeshLab/Blender vocabulary, eliminates the Hanson over-approximation honestly rather than just documenting it), but it deviates from the explicit roadmap-locked `±a × ±b × ±c` spec in `plans/panel-refresh-2026q2-roadmap.md` §8 `panel-refresh-2026q2-e5-s1`. Mid-milestone scope change is the wrong sequencing — open as `status-bar-bbox-2026q2-e2` (or roll into a broader UPL-13-v2 with hover readouts) where the format choice can be evaluated on its own merits against industry vocabulary. Disposition: defer-for-followup.
- **F-L2** — `.2f` → `.3f` precision bump. Defer pending F-L1 decision (precision interacts with format choice).

**Invalidated:** none — all four code findings (M1, L1, M2, F-M1) re-verified present in source before fixing.

**Process-only:**
- **H1** — diff-LOC overage (429 lines). Dominated by 271 lines of milestone documentation artifacts (research brief, state.json, dispatch log, implementation plan). No code action required. Disposition: resolved-no-code-change / doc-artifacts inflated total.

**Test suite:** 295 passed (290 baseline + 5 bbox tests). No regressions.
