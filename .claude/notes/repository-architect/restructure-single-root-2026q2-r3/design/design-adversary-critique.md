# Design adversary critique — restructure-single-root-2026q2-r3

**Reviewed:** PLAN.md @ HEAD=c1dcf89, symbol-map.json @ HEAD=c1dcf89
**Axes walked:** 12
**Verdict:** PROCEED-WITH-CONDITIONS

Three HIGH findings must be addressed in PLAN.md before Phase 3 executes.
No CRITICAL findings. The core design is sound.

---

## Findings by severity

### HIGH — B4 commit decomposition is ambiguous: 5 steps, "3 commits", no mapping

**Axis:** 10. Sequencing safety
**Where:** PLAN.md §9, B4 row: "(a) Verify THREADING_LAYER…; (b) LibCST rewrite 21 sites; (c) Manually refactor 2 bare-import sites; (d) Run -W error pytest; (e) git rm surfaces.py" — listed as "3 commits"

**Why it matters:** B4 is the highest-risk batch (current-state audit §1: "B4 is the highest-risk batch"). Five steps are described but no mapping tells the executor which steps are commits versus intermediate verifications. An implementer under time pressure may reasonably group (b)+(c)+(e) into a single commit, meaning surfaces.py is deleted in the same commit as the LibCST rewrites — with no intermediate green-suite checkpoint between the rewrite and the deletion. If the rewrite is partial or the -W error run is skipped in that grouping, the rollback cost doubles.

The refactor-pattern-scout Topic 1 exit criterion requires the DeprecationWarning pytest (-W error) to pass BEFORE git rm surfaces.py — this must be its own verified checkpoint, ideally a separate commit. Three separate commits would be: commit-1 = LibCST rewrites (b+c), commit-2 = none (verification checkpoint only, not a commit but a gate), commit-3 = git rm surfaces.py.

**Suggested fix:** Add a sentence to B4's description that maps: "commit 1 = (b)+(c) LibCST + manual rewrites; gate = (d) -W error pytest MUST pass before any commit proceeds to commit 2; commit 2 = (e) git rm surfaces.py. Verification step (a) is pre-flight, not a commit." This makes the 3-commit claim mean: pre-flight + rewrite-commit + delete-commit (or even just 2 source commits if verification is not committed separately).

---

### HIGH — test_import_smoke.py parametrize scope silently contradicts refactor-pattern-scout AI-2 guidance

**Axis:** 8. Test parity risk / AI-2 conflict
**Where:** PLAN.md §5 B5 row: "Cyclic-import smoke for `app`, `varieties`, `render`, `_qt`, `cross_section`"; §7 row 10: "parametrize over `varieties`, `render`, `_qt`, `cross_section`, `app`". Also: refactor-patterns Topic 3 (p. 241): "DO NOT include `app`, `_qt`, or any panel module in this smoke test — they require a QApplication and will fail under offscreen QPA on most CI setups."

**Why it matters:** There is a textual contradiction between the PLAN and the scout brief. The scout explicitly flags `app` and `_qt` as unsafe for the subprocess import smoke test because they require a QApplication. The PLAN includes both without explaining why they are safe in AVC's case. Verified: `app.py` wraps QApplication construction inside `main()`, which is guarded by `if __name__ == "__main__"`, so `import app` in a subprocess is in fact safe. Verified: `_qt/__init__.py` is a docstring-only init with no imports, so `import _qt` is also safe. However, the PLAN asserts these are safe by implication only — it does not cite the subprocess-safe evidence. A future executor reading both documents will see the contradiction and may eliminate `app`/`_qt` from the smoke test, silently weakening coverage.

**Suggested fix:** Add a note in B5 or §6 (AI-invariant table) explicitly confirming that `import app` is subprocess-safe because QApplication construction is inside `main()` (not at module scope), and `import _qt` is subprocess-safe because `_qt/__init__.py` has no imports. Cite PLAN.md §6 AI-2 row as the rationale. This resolves the contradiction against the scout's warning.

---

### HIGH — Tier 2 rollback uses `git log --grep` pattern matching — fragile per r1 lesson

**Axis:** 6. Rollback feasibility
**Where:** PLAN.md §8 "Tier 2 — partial revert": `git log --oneline --grep="restructure-single-root-2026q2-r3 batch <N>"`

**Why it matters:** The r1 design-adversary lessons.md explicitly flags this pattern: "git log --grep on an uncommitted commit message pattern is fragile — the grep pattern must match exactly, and commit message formats drift. Prefer tag-based Tier-3 rollback: tag after each batch, revert from tag." AVC's conventional-commit format uses `refactor(restructure-single-root-2026q2-r3): ...` subject lines, not `restructure-single-root-2026q2-r3 batch <N>`. The grep pattern in §8 would return zero results for commits using the actual commit message style, leaving an executor with no easy way to identify the B4 commit range during a panic revert.

**Suggested fix:** Replace Tier 2's `git log --grep` with a tag-based lookup: "each batch ends with `git tag refactor-r3-bN-end <sha>`; Tier 2 revert is `git revert refactor-r3-b(N-1)-end..refactor-r3-bN-end`." This matches the tags used in r2 (e.g. `refactor-r2-batch4-end`) which are already documented in MOVES.md and provide a stable anchor.

---

## Findings by severity (continued)

### MEDIUM — PLAN's test count arithmetic has two errors (506→505 is wrong; "500-ish" understates)

**Axis:** 8. Test parity risk (effort honesty)
**Where:** PLAN.md §9, last paragraph: "506 passed (or 505 after B3 deletes `test_r2_shims.py`'s 7 tests = 499; or +1 after B5 adds `test_import_smoke.py` = 500-ish)"

**Why it matters:** The per-batch verification statement contains two errors that will produce false parity failures or confusion when the parity-verifier runs:

1. "506 → 505 after B3" is wrong. `test_r2_shims.py` has exactly 7 tests (confirmed against baseline.collect.txt: 7 entries under `test_r2_shims.py`). 506 - 7 = **499**, not 505. The "= 499" parenthetical is correct but the "505" leading figure is wrong.

2. "500-ish" after B5 is underspecified for a parity-verifier. `test_import_smoke.py` will add one test per parametrize entry. The PLAN claims "parametrize over varieties, render, _qt, cross_section, app" = **5 modules**. 499 + 5 = **504**, not ~500. "500-ish" suggests the implementer has not committed to a specific count, which makes the parity gate ambiguous.

**Suggested fix:** Correct the statement to: "499 after B3 (7 shim tests deleted); 499 → 504 after B5 adds `test_import_smoke.py` with 5 parametrize entries. Expected final count: 504 collected."

---

### MEDIUM — B5 import-linter onboarding skips "zero-contracts baseline" step

**Axis:** 5. Shim-cycle correctness (import-linter brownfield risk)
**Where:** PLAN.md §9 B5 description: "(a) Add import-linter to requirements; add `[tool.importlinter]` to pyproject.toml; (d) Verify `lint-imports` exits 0"

**Why it matters:** Refactor-patterns scout Topic 5 (brownfield onboarding) states: "Run `lint-imports` with zero contracts first to confirm tooling works. Add one contract. Run `lint-imports`. If violations appear, they must ALL be fixed before merging." The PLAN adds the full contract set in a single step and immediately verifies. If any of the proposed contracts catches a pre-existing violation (e.g. a `render/` module that accidentally imports `PySide6` via an undocumented path), B5 will block on a violation the executor did not create. The fix requires diagnosing a pre-existing issue under the pressure of an in-flight batch. The risk is LOW for well-maintained code, but the scout's brownfield protocol exists precisely for this scenario. It costs one additional pre-flight command.

**Suggested fix:** Add a step 0 to B5: "Run `lint-imports` with an empty `[[tool.importlinter.contracts]]` list to verify tooling installation. Confirm exit 0 before adding any contracts." This takes ~30 seconds and eliminates the ambiguity between a tooling configuration error and a real layer violation.

---

### MEDIUM — Axis-12 self-check is too quick on best-practices §7's "primary monolith" language

**Axis:** 12. Under-engineering relative to scout evidence
**Where:** PLAN.md §10, axis-12 self-check: "No audit brief used stronger-than-neutral language for any deferred item."

**Why it matters:** Best-practices-scout §7 (p. 415) writes: "app.py at 1900 LOC is still the **primary monolith risk**. r3's focus is not app.py decomposition — that remains deferred." The phrase "primary monolith risk" is stronger-than-neutral language by the axis-12 definition ("primary monolith" is explicitly listed as a trigger phrase). The PLAN's §10 deferral row for app.py states "Out of scope per brief; this is a God Object refactor, not a folder restructure" with the citation "current-state §3 monolith table (KEEP)." However, the PLAN does not explicitly address the scout's "primary monolith risk" framing — it cites the current-state audit (which says KEEP), not the best-practices-scout language.

Per axis-12: a strongly-flagged deferral must name the audit citation it is overruling AND acknowledge the cost of not acting. Here: the brief is explicit that r3's goal is the single-root goal (not monolith extraction), and the best-practices scout itself says "r3's focus is not app.py decomposition — that remains deferred," making this a self-referencing deferral (the scout agrees with the deferral). The PLAN's axis-12 self-check is therefore not factually wrong, but it is imprecise in not naming the best-practices §7 citation explicitly.

**Suggested fix:** Amend the §10 axis-12 self-check to add: "best-practices-scout §7 uses 'primary monolith risk' for app.py but ALSO states 'r3's focus is not app.py decomposition — that remains deferred' — the scout itself endorses the deferral. The PLAN accepts this endorsement." This makes the reasoning transparent rather than implicitly relying on the scout's own deferral language.

---

### LOW — B4 description says "21 from surfaces import X sites" but actual live count is ~18-20

**Axis:** 11. Effort honesty
**Where:** PLAN.md §9 B4 description: "(b) LibCST rewrite 21 `from surfaces import X` sites"; §3 B4 table header: "23 import sites"

**Why it matters:** Independent grep of the live codebase (`grep -rln "from surfaces import|import surfaces"`) finds 19 unique callers (excluding surfaces.py itself), of which 2 (varieties/tooltips.py:13 and varieties/registry.py:13) are docstring-only mentions and do NOT contain live import statements. After subtracting test_r2_shims.py (deleted in B3), the actual live count for B4 is ~16 files with ~20 import lines (not 19 files / 23 import lines). The overcounting comes from the current-state audit including docstring-only grep matches in its file count. This inflates the apparent scope of B4 by ~15%, which is harmless for safety but misleads the effort estimate. The parity-verifier will not catch this; it only verifies test counts.

**Suggested fix:** Update the B4 description's site count to "~20 live import lines across ~16 live files" and add a parenthetical: "(the 19-file count in the audit includes 3 docstring-only hits in varieties/tooltips.py, varieties/registry.py — these are not live imports)."

---

### LOW — Tier-4 rollback says "expect 506 PASS" but B3 may have already removed 7 tests

**Axis:** 6. Rollback feasibility
**Where:** PLAN.md §8 Tier-4: "Re-run baseline tests: python -m pytest -q # expect 506 PASS (no shim changes from preceding completed batches)"

**Why it matters:** If Tier-4 abort fires during B4 (the most likely abort scenario), B3 will have already completed and test_r2_shims.py will be gone. The expected count at that point is 499, not 506. The comment "no shim changes from preceding completed batches" is internally inconsistent — B3 IS a shim-change batch.

**Suggested fix:** Amend the Tier-4 comment to: "expect ~499 PASS if B3 is complete (test_r2_shims.py deleted), or 506 PASS if aborting during B1/B2/B3."

---

### LOW — B1 does not specify a scratch-file test for the fixed codemod before live-tree run

**Axis:** 1. AI-invariant conflicts (codemod correctness — adjacent to AI-9)
**Where:** PLAN.md §9 B1 description: "Fix LibCST partial-attribute-rewrite bug per refactor-pattern-scout Topic 2 checklist"

**Why it matters:** Refactor-patterns scout §3 checklist item 4 explicitly requires: "Test the codemod on a scratch file with all four import patterns before running on the live tree." The PLAN's B1 description does not include this verification step, meaning the executor may proceed directly to B4's live rewrite without validating that the B1 fix actually addresses all four import patterns (bare `import surfaces`, `from surfaces import X`, `from surfaces import X, Y`, `surfaces.X` attribute access). A partially-fixed codemod that still mis-handles multi-alias statements is the exact r2 failure the PLAN cites as the reason for B1.

**Suggested fix:** Add a bullet to B1's description: "Verify the fixed codemod against a scratch file containing all four import patterns (per refactor-patterns §3 checklist) before landing the B1 commit."

---

## Axes with NONE findings

**Axis 1 — AI-1..AI-15 conflicts:** PLAN §6 correctly identifies all touched invariants (AI-2, AI-6, AI-8, AI-9). Mitigations are sound: VarietyGenerator Protocol is explicitly additive (no Surface/ParamSpec field changes); THREADING_LAYER side effect is verified present in varieties/_kernels.py (confirmed by live grep: line 22); generator pipeline split preserved (implementations don't move in B4). No AI-invariant violation found.

**Axis 2 — AI-15 honesty applied to the design:** Every proposed move in PLAN §3 traces to a specific scout finding (surfaces.py retirement ← current-state §9 HIGH; parameter_grid move ← best-practices §5 napari precedent; shim deletions ← current-state §9 HIGH; import-linter ← best-practices §3; Protocol ← best-practices §2). No split proposed without traceable justification.

**Axis 3 — Hallucinated patterns:** No anti-patterns from scout-B §5 (12 patterns) or scout-C §10 (10 rationalizations) are present. No star-imports in shims. No package-by-layer naming. No utils.py re-introduction. No capitalized directory names. No src-layout for a 7-file flat app. No `plugins/` without a plugin contract.

**Axis 4 — Over-engineering relative to repo size:** The changes are proportionate. The 5 batches address exactly the scout-identified misplacements. The Protocol addition is 18 LOC. The import-linter config is ~25 LOC. No three-deep nesting proposed. No `api/` subpackage. The design does not exceed the scope of a 7849 LOC flat repo.

**Axis 5 — Shim-cycle correctness:** r3 introduces zero new shims. The five deleted shims (icons.py, styles.py, ui_helpers.py, render_worker.py, panels/__init__.py) all have complete M+1 cycles documented in MOVES.md with DeprecationWarning patterns. The parameter_grid move skips a shim correctly (all 4 callers are in-tree and rewritten by LibCST — no external consumers exist, consistent with R4 exception for internal restructures).

**Axis 7 — Anchor coverage:** PLAN §3 B5 and §9 B5 both explicitly list CLAUDE.md, README.md, MOVES.md, and CONTEXT.md for anchor-updater update. MOVES.md is called out in §3 B5: "append r3 rosetta." All four anchor surfaces are covered. The README back-compat note referencing surfaces.py is explicitly scheduled for removal in B5.

**Axis 9 — Cross-suite test gaps:** §7 walks all 10 scout-C categories. Seam tests for the varieties/registry boundary are covered by existing test_mesh_generators.py and the new test_import_smoke.py. Numba THREADING_LAYER side effect is addressed (indirectly via test_import_smoke importing varieties._kernels). No conftest.py scope drift (no conftest.py exists).

**Axis 10 — Sequencing safety (batch ordering):** Batches are ordered correctly: B1 (tooling fix) → B2 (low-risk move) → B3 (shim deletes, no import rewrites) → B4 (high-risk hub retirement) → B5 (lock-in). Low-risk batches precede high-risk ones. B3 clears test_r2_shims.py before B4 runs to eliminate the 2 shim-test import sites from B4's scope.

---

## Specific r3 concern verdicts (per task brief)

**A. B1 fix completeness:** The PLAN's B1 description explicitly lists all three refactor-pattern-scout Topic 2 checklist items: QualifiedNameProvider.has_name(), METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider), and multi-alias guard for leave_ImportFrom. The description is complete. Gap: B1 does not mandate a scratch-file pre-test (see LOW finding above).

**B. B4 ordering risk:** The ordering within B4 is correct (verify → rewrite → manual fix → -W error pytest → git rm). The concern is that the 3-commit mapping is ambiguous (see HIGH finding above). If the executor commits rewrite + delete together, the intermediate green checkpoint is lost.

**C. Bare `import surfaces` handling — is "manual" honest?** Yes. Both bare-import sites (`test_status_bar_bbox.py:33` and `test_enriques_hq_smoothing.py:31`) access attributes as `surfaces.SOMETHING` throughout their test bodies. Mechanically resolving these requires enumerating every attribute-access call site and mapping each to its canonical `varieties.*` home — this is exactly what QualifiedNameProvider does with the `leave_Attribute` pattern. The LibCST RenameCommand source (scout Topic 2) handles `import X; X.attr` patterns via `QualifiedNameProvider.has_name()` on the attribute node, not just import lines. The PLAN's claim that LibCST "cannot mechanically rewrite these" is incorrect — LibCST CAN handle `import surfaces; surfaces.VARIETIES` via `leave_Attribute`. However, the conservative "manual" designation is safe (it errs toward caution); it just understates what LibCST can do. The effort label "manual" is honest about what the PLAN's current codemod will do (since it may not yet implement `leave_Attribute`); it is only misleading if it implies LibCST fundamentally cannot handle it. This is a MINOR framing issue, not a blocker.

**D. Protocol additive claim:** The PLAN states "VarietyGenerator Protocol is ADDITIVE — zero changes to Surface or ParamSpec fields." The best-practices scout §2 notes that `Surface.generate: Callable[..., pv.PolyData]` COULD be narrowed to `Surface.generate: VarietyGenerator`. PLAN §3 B2 does NOT propose narrowing the type annotation of `Surface.generate`. This is correct — narrowing `Callable[..., pv.PolyData]` to `VarietyGenerator` would be a backward-incompatible change to the frozen dataclass contract (any caller constructing `Surface(label, fn, params)` where `fn` is `Callable[..., pv.PolyData]` but not technically `VarietyGenerator` would fail mypy). The PLAN correctly keeps the Protocol additive (as a new name in `varieties/types.py` with zero changes to existing fields). The "point of adding the Protocol" is to give type checkers and agents a named interface; it does NOT require re-typing `Surface.generate`. This is a defensible design choice. No issue.

**E. Import-linter brownfield risk:** The PLAN does not include a "run lint-imports with zero contracts" pre-step (see MEDIUM finding above). The risk is low given AVC's clean structure, but the scout's brownfield protocol explicitly requires it. The gap is real.

**F. MOVES.md anchor coverage:** Confirmed present. PLAN §3 B5 action table explicitly lists "anchor-updater | CLAUDE.md, README.md, MOVES.md, CONTEXT.md." MOVES.md is also cited in §3 B4 symbol table ("Mirrored to symbol-map.json") and in §5 shim plan ("Shim deletion verification"). The MOVES.md update in B5 will add r3 entries (parameter_grid move, surfaces.py retirement, shim deletions). PASS.

**G. Test count arithmetic:** The PLAN's arithmetic is wrong in two places (see MEDIUM finding above). 506 - 7 = 499 (not 505). 499 + 5 = 504 (not ~500). These need correction before the parity-verifier runs.

**H. Axis-12 self-check honesty:** The best-practices scout §7 uses "primary monolith risk" for app.py, which is a trigger phrase under axis-12. The PLAN's axis-12 self-check says "no audit brief used stronger-than-neutral language" — this claim is too broad. The scout DID use stronger language but the scout ALSO endorsed the deferral in the same sentence. The self-check should acknowledge the scout citation and the scout's own endorsement of deferral (see MEDIUM finding above). This is not a blocker because the scout's endorsement is present; it is a transparency issue in the self-check reasoning.

---

## Recommended PLAN.md edits before Phase 3

1. **§9 B4 row:** Add a sentence mapping the 5 sub-steps to 2 source commits and 1 mandatory inter-commit verification gate: "commit 1 = steps (b)+(c); gate = (d) must pass before commit 2; commit 2 = step (e)."

2. **§5 or §6 AI-2 row:** Add a note confirming `import app` is subprocess-safe (QApplication in `main()`, not at module scope) and `import _qt` is subprocess-safe (`_qt/__init__.py` is docstring-only). Resolves the contradiction with refactor-patterns Topic 3's "DO NOT include app/_qt" warning.

3. **§8 Tier 2:** Replace `git log --grep` with tag-based rollback: `git revert refactor-r3-b(N-1)-end..refactor-r3-bN-end`. Add tag-creation step to the end of each batch's execution notes.

4. **§9 last paragraph:** Correct test count to "499 after B3; 504 after B5" (not "505" and not "500-ish").

5. **§9 B5 description:** Add a zero-contracts pre-flight step: "step 0: install import-linter, run `lint-imports` with empty contracts section, confirm exit 0."

6. **§10 axis-12 self-check:** Amend to acknowledge best-practices §7 "primary monolith risk" language and cite the scout's own deferral endorsement in the same paragraph.

---

*Adversary walk complete. 0 CRITICAL, 3 HIGH, 3 MEDIUM, 3 LOW findings. All HIGH findings are addressable with PLAN.md text edits — none require design changes. The core sequence (B1 tooling fix → B2 move → B3 shim deletes → B4 hub retirement → B5 lock-in) is sound.*
