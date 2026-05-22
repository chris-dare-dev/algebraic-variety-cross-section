# Adversary critique — Status-bar size readout (bbox → full-extent switch)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** `status-bar-bbox-2026q2-e2` / `269f38f..cc11a18`

---

## Header

- **Critic:** milestone-adversary-critic
- **Commit range:** `269f38ffbea5ed3578fe07d17b2a04ab75bdbdcb..cc11a18cb0f1940cc6684f9ffaec92c2283d147b`
- **Generated:** 2026-05-22
- **Diff stats:** 585 LOC total; ~9 LOC code delta in `app.py`, ~70 LOC code delta in `tests/test_status_bar_bbox.py`, 1 line changed in `CONTEXT.md`. Remainder (~505 LOC) is milestone artifacts: `research/agent-solo-brief.md` (162 LOC), `state.json` files, `dispatch.log`, `implementation-plan.md`, researcher `lessons.md` entry.

---

## Executive summary

The dominant finding is the auto-triggered HIGH for diff size (585 LOC > 400 threshold), but the actual code delta is approximately 80 LOC — well under the research-quality-degradation threshold; the arithmetic finding is correct by rule but requires no code action. One MEDIUM documents a Hanson family coverage gap in the test suite (only the quintic is tested; the asymmetric generator, which has the largest z-extent deviation at defaults, is absent). One LOW covers a prose typo in CONTEXT.md §4.3 (`bounds[0]` drops the `self._raw_mesh.` prefix inconsistently in a descriptive expression). Zero CRITICALs. Zero code-path HIGHs. All AI-1..AI-15 invariants are clean. The math is correct: the full-extent computation `b[1]-b[0]` is algebraically exact for all 14 generators by construction. Safe to merge after noting the MEDIUM gap.

Severity counts: 0 CRITICAL, 1 HIGH (process / auto-finding), 1 MEDIUM, 1 LOW.

---

## Verdict

SHIP-WITH-FIXES. The one HIGH is a non-waivable process finding (diff-size auto-rule) with no code action required — the high LOC count is entirely artifact inflation. The MEDIUM (Hanson asymmetric coverage gap) is the only genuine code-quality gap; it is a forward risk, not a present bug. The LOW (CONTEXT.md prose typo) is cosmetic. Recommend adding one test for `calabi_yau_asymmetric` (MEDIUM) and fixing the documentation typo (LOW) before closing the milestone.

---

## Critical findings

None.

---

## High findings

### HIGH — Diff-size review-quality-at-risk (auto-finding)

**Where:** no specific file (diff-level metric)
**Evidence:** `git diff 269f38f..cc11a18 | wc -l` = 585 lines, exceeding the 400-LOC threshold documented in the adversary-critique-checklist (Cisco / LinearB defect-detection research).
**Why it matters:** Per checklist policy this finding is non-waivable regardless of cause. In this specific case the code delta is approximately 80 LOC; the remaining ~505 LOC are milestone artifact files (`research/agent-solo-brief.md`, `dispatch.log`, `state.json` x2, `implementation-plan.md`, `lessons.md` update). No code action is required — the artifact inflation is expected and the actual review surface is well within the low-risk range.
**Suggested fix:** No change to code needed. Disposition: artifact inflation confirmed; no defect-detection risk on the actual code delta. Note the breakdown in rectification notes.

**Regression-guard test:** Not applicable — this is a process finding, not a code defect.

---

## Medium findings

### MEDIUM — Hanson asymmetric generator absent from size-format test suite

**Where:** `tests/test_status_bar_bbox.py:100` (the Hanson test function covers only `calabi_yau_quintic`)
**Evidence:** `test_size_format_matches_regex_on_hanson_quintic` calls `surfaces.calabi_yau_quintic()` only. The commit message documents independently-verified outputs for all three Hanson generators: quintic `2.257 × 2.257 × 3.043`, cubic `2.449 × 2.449 × 3.016`, **asymmetric `2.257 × 2.449 × 3.343`**. The asymmetric generator is the only one that produces visibly different extents in all three axes (x ≠ y ≠ z), making it the highest-value regression target. A NaN or degenerate-bounds regression in `calabi_yau_asymmetric` would not be caught by the existing suite.
**Why it matters:** The format contract claims to be exact for "all 14 generators by construction"; the test suite covers 4 of 14 (Fermat quartic, Kummer surface, Hanson quintic, and the ValueError path). The Hanson asymmetric generator is the most structurally distinct case and the one most likely to expose a future regression in `_hanson_cross_section`. The e1 lesson specifically flagged this gap pattern ("Hanson test-coverage gap pattern: any test file for a status-bar or format-contract feature should include at least one Hanson generator call").
**Suggested fix:** Add a fifth Hanson test mirroring `test_size_format_matches_regex_on_hanson_quintic` but calling `surfaces.calabi_yau_asymmetric()`, asserting all 6 bounds indices are finite and the `SIZE_REGEX` matches. The `math.isfinite` loop pattern for all 6 indices from the quintic test should be reused verbatim.

**Regression-guard test:** `test_size_format_matches_regex_on_hanson_asymmetric` — `mesh = surfaces.calabi_yau_asymmetric(); b = mesh.bounds; [assert math.isfinite(b[i]) for i in range(6)]; assert SIZE_REGEX.fullmatch(_format_size(mesh))`.

---

## Low findings

### LOW — CONTEXT.md §4.3 prose typo: `bounds[0]` missing `self._raw_mesh.` prefix

**Where:** `CONTEXT.md:137`
**Evidence:** The sentence reads `Lx = self._raw_mesh.bounds[1] - bounds[0]`, `Ly = bounds[3] - bounds[2]`, `Lz = bounds[5] - bounds[4]`. The first term consistently names `self._raw_mesh.bounds[1]` but the subtracted term drops the object prefix to just `bounds[0]`. The Ly and Lz terms use the bare `bounds` reference throughout — implying a different local variable `bounds` exists, which it does not in `_render_current` (the variable is always `_b = self._raw_mesh.bounds`). The actual code at `app.py:586` uses `_b` correctly; the typo is documentation-only.
**Why it matters:** A reader scanning CONTEXT.md §4.3 for the variable reference to audit the computation will see `self._raw_mesh.bounds[1] - bounds[0]` and may wonder whether `bounds` is a different binding (e.g., the generator's sampling bounds parameter). This creates a micro-ambiguity in the institutional memory contract.
**Suggested fix:** Rewrite the description to use a consistent local-variable shorthand, e.g., `Lx = _b[1] - _b[0]`, `Ly = _b[3] - _b[2]`, `Lz = _b[5] - _b[4]` (matching `app.py:585` exactly), or use `bounds[1] - bounds[0]` consistently throughout all three terms.

---

## What was done well

- **`\d{3}` quantifier in SIZE_REGEX enforces the `.3f` contract precisely.** The prior `\d+` regex (BBOX_REGEX in e1) would have silently accepted `.2f` or `.4f` regressions; the curly-brace quantifier ensures the test fails loudly on any precision drift. This is the correct application of the format-contract-regex pattern documented in the e1 lessons.

- **Hanson `math.isfinite` guard extended from 3 to all 6 bounds indices.** The v1 test only checked `b[1]`, `b[3]`, `b[5]`; the full-extent computation subtracts `b[0]`, `b[2]`, `b[4]`, so a NaN in those positions would corrupt the output silently. Extending the loop to `for i, axis in enumerate(("xmin", "xmax", ...))` with labeled error messages is a materially stronger guard.

- **`_format_size` helper mirrors the app.py f-string exactly without importing `app.py`.** The `SIZE_FORMAT.format(a=b[1]-b[0], b=b[3]-b[2], c=b[5]-b[4])` mirrors `f"size: {_b[1]-_b[0]:.3f} × {_b[3]-_b[2]:.3f} × {_b[5]-_b[4]:.3f}"` at `app.py:587` identically. The BBOX_FORMAT mirroring pattern from e1 is correctly carried forward, and the helper now uses the same arithmetic to avoid drift between the test contract and the production code.

- **`bbox_suffix` → `size_suffix` rename is complete and consistent.** All three consumption sites in `app.py` (`app.py:586`, `app.py:594`, `app.py:607`) were updated. No stale `bbox_suffix` reference remains in the production code paths.

- **The e1 future-extension note (`xmin..xmax × ymin..ymax × zmin..zmax`) was correctly removed.** The note anticipated a need to switch to full-range display for non-centered domains; since e2 implements exactly that, the forward-reference is now obsolete and its removal avoids confusing future readers into thinking additional work remains.

- **view_panel.py `_bbox_actor` / `_bbox_cb` intentionally NOT renamed.** These identifiers refer to the VTK bounding box overlay actor (an entirely separate UI feature). Renaming them to `_size_actor` would be semantic malpractice. The diff correctly leaves them untouched; no stale-reference confusion arises because the feature semantics are visually distinct (overlay wireframe vs. status-bar text).

- **Test count held at 336 (5 in-place rewrites, zero net additions).** The commit message claim (`336 total, same count as before — 5 in-place rewrites`) was verified against `pytest --collect-only -q` output. All 5 tests pass in the project venv.

- **`SIZE_REGEX` × character (U+00D7, `0xc3 0x97`) matches the `app.py` f-string.** Binary inspection confirms both use the same Unicode multiplication sign; no divergence between the regex literal and the production string that would cause fullmatch to silently fail.

- **Warning-path priority order preserved.** The Dwork conifold hoist (`f"⚠ {_surface_warning}  ·  {size_suffix}"`) was updated from `bbox_suffix` to `size_suffix` at `app.py:607` with no change to the logic ordering. The critical design choice (hoist size before the label/verts/faces content on the warning path) survives the rename intact.

- **CONTEXT.md generator count claim verified at 14.** `grep -n "^def " surfaces.py` with helper-exclusion filter returns exactly 14 generator functions: 4 Enriques + 4 Fano + 1 Fermat + 1 Kummer + 1 Dwork + 3 Hanson = 14. The e1 lesson (wrong count of 12 was a MEDIUM) is not repeated here.

---

## Recommended rectification order

1. **Add `test_size_format_matches_regex_on_hanson_asymmetric` (MEDIUM).** This is the only genuine code-quality gap. Mirror the structure of `test_size_format_matches_regex_on_hanson_quintic` exactly, substituting `calabi_yau_asymmetric()`. One additional test, no production code changes required.

2. **Fix the CONTEXT.md §4.3 prose typo (LOW).** Change `self._raw_mesh.bounds[1] - bounds[0]`, `bounds[3] - bounds[2]`, `bounds[5] - bounds[4]` to use consistent shorthand (`_b[1] - _b[0]`, `_b[3] - _b[2]`, `_b[5] - _b[4]`) matching `app.py:585-589`.

3. **Process HIGH (diff-size auto-finding) — no code action.** Note the breakdown (80 LOC code, 505 LOC artifacts) in the milestone state and close.

---

*End of critique. Mandatory rectification: H1 has no code action. M1 (Hanson asymmetric test) is the only blocking item before milestone close. L1 is cosmetic.*

---

## Frontend UI/UX findings

*Merged from `frontend-critique.md`. Qt-panel critic emitted 0 CRITICAL, 0 HIGH, 1 MEDIUM, 1 LOW. Severity-ids prefixed with `F-`.*

### MEDIUM — F-M1: `"size:"` drops the AABB qualifier; peer tools all qualify explicitly

**Where:** `app.py:587` (`size_suffix` f-string literal) and `app.py:607` (warning-path hoist)
**Evidence:** Peer tool audit: MeshLab API `dim_x()/dim_y()/dim_z()` documented as "the X size of the Bounding Box" — qualifier "Bounding Box" always present. ParaView Information panel uses `Bounds` and `X Range: min to max`. Blender Properties / status bar uses `Dimensions:` which conventionally implies bounding-box extent. **None of the three peers uses bare `size:` without a type qualifier.** A researcher seeing `size: 6.400 × 6.400 × 6.400` for an algebraic surface could legitimately interpret "size" as surface area (an integral over the manifold), volume (for closed surfaces), or true geometric diameter (which for non-convex shapes exceeds the AABB extent). All three are distinct quantities from what's actually reported (AABB extent in user-coordinate space).
**Why it matters:** Research tools accumulate credibility through precision. The e2 change is a data-accuracy improvement (full-extent vs half-extent for Hanson) but the label change introduced a measurement-type ambiguity that didn't exist in v1's `bbox ±…` (where "bbox" explicitly named the AABB measurement). Character cost of `bbox:` vs `size:` is zero (both 5 chars including colon).
**Suggested fix:** Change `size:` → `bbox:` at both call sites. Preserves v1's measurement-type qualifier AND the e2 full-extent / .3f improvements. The variable name `size_suffix` can stay (it captures the readout's semantic role) OR rename back to `bbox_suffix` for consistency with the user-visible label — recommend the latter for coherence.

### LOW — F-L1: `.3f` trailing zeros on round values read as false precision

**Where:** `app.py:587`
**Evidence:** Kummer's `2 * 3.2 = 6.4` renders as `6.400` (numerically exact, but a user accustomed to short readouts may read three decimal places as "measured to 0.001 accuracy" rather than "the sampling domain is exactly 6.4 wide"). The `.3f` rationale (avoiding false equalities at sub-1.0 extents) is sound; this is paper-cut not regression.
**Suggested fix:** Defer. The critic explicitly recommends no action — current rationale is correct. If a future iteration wants to suppress trailing zeros, `:.4g` would give `6.4` for round values and `0.5300` for sub-1.0 with adequate precision. Not blocking.

---

## Combined rectification order

1. **F-M1 (frontend MEDIUM)** — Change `size:` → `bbox:` in app.py (2 sites: success-path assignment + warning-path hoist). Rename `size_suffix` → `bbox_suffix` for coherence with the new user-visible label. Update SIZE_FORMAT → BBOX_FORMAT, SIZE_REGEX → BBOX_REGEX, `_format_size` → `_format_bbox`, and the 5 test function names (test_size_* → test_bbox_*) in tests/test_status_bar_bbox.py — restores naming continuity with the v1 era. The CONTEXT.md §4.3 paragraph header changes from "Status-bar size readout" to "Status-bar bbox readout (full-extent)" since "size" is the wrong noun. ~20 LOC.

2. **M1 (adversary MEDIUM)** — Add `test_size_format_matches_regex_on_hanson_asymmetric` (or `test_bbox_format_matches_regex_on_hanson_asymmetric` post-rename). Hanson asymmetric is the only generator with truly asymmetric extents (x≠y≠z = 2.257 × 2.449 × 3.343) — strongest regression canary. ~15 LOC.

3. **L1 (adversary LOW)** — CONTEXT.md §4.3 prose typo: `self._raw_mesh.bounds[1] - bounds[0]` is inconsistent (object prefix on first term, dropped on subsequent terms). Replace with consistent `_b[1] - _b[0]` shorthand matching app.py:587 (the local variable `_b = self._raw_mesh.bounds`). ~3 LOC.

4. **F-L1 (frontend LOW)** — Defer per critic's own recommendation. `.3f` rationale is correct; `:.4g` alternative can wait for a future cosmetic-polish milestone.

5. **H1 (adversary HIGH)** — Process-only; ~80 LOC code, ~505 LOC artifacts. No code action.

---

## Rectification status (orchestrator, 2026-05-22)

**Fixed in rect commit:**

- **F-M1 (frontend MEDIUM, label qualifier)**: Changed `size:` → `bbox:` in app.py at both call sites (success-path assignment + warning-path hoist). Renamed `size_suffix` → `bbox_suffix` for coherence with the user-visible label. Restored the test-file naming continuity with v1: `SIZE_FORMAT` → `BBOX_FORMAT`, `SIZE_REGEX` → `BBOX_REGEX`, `_format_size` → `_format_bbox`, and all 5 (now 6) test function names from `test_size_*` back to `test_bbox_*`. Updated the inline comment block in app.py and CONTEXT.md §4.3 to explain the peer-tool rationale (MeshLab "Bounding Box dim_x()", ParaView "Bounds / X Range:", Blender "Dimensions:") and why bare `size:` would be ambiguous for algebraic surfaces (could mean surface area, volume, or true geometric diameter — all distinct from AABB extent).

- **M1 (adversary MEDIUM, Hanson asymmetric coverage gap)**: Added `test_bbox_format_matches_regex_on_hanson_asymmetric` covering `surfaces.calabi_yau_asymmetric()`. This generator is the only one in the live registry with visibly different extents along all three axes at defaults (2.257 × 2.449 × 3.343), making it the strongest regression canary — a per-axis arithmetic bug (e.g. swapping `b[3]-b[2]` with `b[5]-b[4]`) would be visible in the output rather than masked by the symmetry of Fermat (2×2×2) or Kummer (6.4³). Mirrors the quintic test's `math.isfinite` loop covering all 6 bounds indices.

- **L1 (adversary LOW, CONTEXT.md §4.3 prose typo)**: Rewrote the bounds-arithmetic description from the inconsistent `Lx = self._raw_mesh.bounds[1] - bounds[0]`, `Ly = bounds[3] - bounds[2]`, `Lz = bounds[5] - bounds[4]` (object prefix only on first term) to consistent shorthand `_b = self._raw_mesh.bounds` and `Lx = _b[1] - _b[0]`, `Ly = _b[3] - _b[2]`, `Lz = _b[5] - _b[4]` matching app.py:585-589 exactly.

**Deferred:**
- **F-L1 (frontend LOW, `.3f` trailing zeros)**: The critic explicitly recommends no action (`current rationale is correct`). Defer to a future cosmetic-polish milestone if `:.4g` alternative becomes worth evaluating. The data is numerically exact; the trailing zeros are correct precision, not noise.

**Process-only:**
- **H1 (adversary HIGH, 585-LOC diff)**: ~80 LOC code, ~505 LOC milestone artifacts. No code action.

**Invalidated:** none — all three code-actionable findings (F-M1, M1, L1) re-verified present before fixing.

**Test suite:** 337 passed (336 baseline + 1 new Hanson asymmetric test). No regressions.

**Architecture lesson recorded:** the v2 implementation's `size:` label experiment is now a documented anti-pattern in CONTEXT.md §4.3. The lesson: when a v1 frontend-ux critic recommends a label change (here, "switch from `bbox ±` to `size:`"), the implementer must independently audit peer-tool labeling conventions — MeshLab/ParaView/Blender all qualify the measurement type (Bounding Box / Bounds / Dimensions), none use bare `size:`. The v1 critic's recommendation captured the half-extent → full-extent improvement correctly but the label transition was based on incomplete peer evidence. The rect-pass corrects this by preserving the v1 `bbox` qualifier alongside the e2 full-extent format — best of both worlds, character-neutral.
