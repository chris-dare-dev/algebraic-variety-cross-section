# Rectify summary — restructure-single-root-2026q2-r3

**Authored:** 2026-05-24 main session (inline rectifier)
**Inputs:** execution-critic-critique.md (0C/0H/1M/3L) + test-suggester-suggestions.md (5 suggestions, all DEFERRED)
**Verdict:** PROCEED-TO-COMPLETE after one rectify commit closing MED-1 + LOW-3 inline.

---

## Execution-critic disposition

| Finding | Severity | Disposition | Action |
|---|---|---|---|
| MED-1: stale docstrings in varieties/registry.py:13 + varieties/tooltips.py:13 | MEDIUM | **FIXED inline** | Both docstrings updated to remove the false "still works via hub-shim re-export" claim; replaced with a note stating surfaces.py was retired in r3 B4 |
| LOW-1: B4 mandatory `-W error::DeprecationWarning` gate command not logged verbatim in B4.md | LOW | **DEFERRED** | Auditability gap only. Live re-run today confirms the gate passes (504 tests, zero DeprecationWarning). Future implementers should paste the verbatim command output into batch logs. No source fix needed at HEAD. |
| LOW-2: `refactor-r3-b5-end` tag points to cabf688, not final SHA 1419d03 (MOVES.md SHA-finalization commit) | LOW | **ACCEPTED AS RESIDUE** | Force-tag move requires user approval. Tier 2 rollback of B5 would miss the 1-line MOVES.md fixup commit; cost is one extra commit to revert. Acceptable cost. Suggest documenting in lessons.md: "tag the FINAL commit of the batch, including any in-batch metadata fixups." |
| LOW-3: root `__pycache__/` contains stale .pyc files for 10 deleted modules | LOW | **FIXED inline** | All 10 stale .pyc files removed (`appearance_panel.cpython-312.pyc`, `render_worker.cpython-312.pyc`, `styles.cpython-312.pyc`, `surfaces.cpython-312.pyc`, `parameter_grid_panel.cpython-312.pyc`, `parameter_grid.cpython-312.pyc`, `view_panel.cpython-312.pyc`, `parameters_panel.cpython-312.pyc`, `ui_helpers.cpython-312.pyc`, `icons.cpython-312.pyc`). Numba caches (.nbc/.nbi) left alone — regenerating is expensive and they are still valid for `surfaces` symbol names that now live at `varieties.X`. `__pycache__/` is gitignored so this is dev-environment cleanliness only. |

---

## Test-suggester disposition

All 5 suggestions DEFERRED to a follow-on `repository-architect-post-r3-test-hardening-2026q3-e1` milestone, per scout-C §10.1 ("writing tests in the same restructure violates separation of concerns").

| # | Suggestion | Priority | Effort | Rationale for deferral |
|---|---|---|---|---|
| 1 | Numba THREADING_LAYER subprocess assertion | HIGH | S (~15 LOC) | The `_kernels.py` docstring documents this as a macOS-crash invariant; zero tests currently verify the actual value. r3's test_import_smoke.py validates `import varieties._kernels` succeeds but does NOT read `numba.config.THREADING_LAYER`. The seam is real and exposed. |
| 2 | varieties.registry consistency + VarietyGenerator Protocol conformance | HIGH | M (~40 LOC) | Two seams: (a) B3 deleted test_r2_shims.py which had transitive coverage of the registry→generator seam; (b) B2 added VarietyGenerator Protocol but no test exercises `isinstance(s.generate, VarietyGenerator)` against every registered surface. |
| 3 | import-linter contracts run inside pytest | MEDIUM | S (~20 LOC) | `lint-imports` was verified manually in B5 but is not run by `pytest`; a future `from PySide6 import X` in `varieties/` would not fail CI. |
| 4 | Single-root invariant test | LOW-MEDIUM | S (~15 LOC) | A 15-LOC `Path.glob("*.py")` check directly guards r3's hard-won `ls *.py == app.py` state. Cheap insurance for a hard-won architectural invariant. |
| 5 | VarietyGenerator Protocol structural conformance | (subsumed by #2) | — | Covered by Suggestion 2. |

**r2 deferrals carried forward:**
- r2 Suggestion 1 (Numba threading-layer smoke) — re-issued as r3 Suggestion 1 (same priority HIGH, same effort S).
- r2 Suggestion 2 (cyclic-import smoke) — **LANDED** as r3 B5 `tests/test_import_smoke.py` (5 parametrized subprocess tests).
- r2 Suggestion 3 (registry consistency) — re-issued as r3 Suggestion 2 (now MORE exposed since B3 deleted test_r2_shims.py which had transitive coverage).

---

## What the rectify commit lands

1. **MED-1 fix**: `varieties/registry.py:13` and `varieties/tooltips.py:13` docstrings updated.
2. **LOW-3 fix**: stale .pyc files removed from `__pycache__/` (no repo change — gitignored — but dev-env clean).
3. **rectify-summary.md** (this file) — disposition for all 8 findings (1M + 3L + 5 test suggestions).

## What r3 ships

| Metric | Baseline (c1dcf89) | HEAD post-rectify |
|---|---|---|
| Root .py files | 7 | **1** (app.py only) ✅ |
| Surface .py files retired | 0 | 6 (surfaces.py + 5 shims) |
| Tests passing | 506 | **504** (-7 r2 shim tests + 5 new smoke tests) |
| import-linter contracts | 0 | **2** (varieties + cross_section, both PASS at HEAD) |
| Layer-direction enforcement | none | pyproject.toml `[tool.importlinter]` |
| New protocols | 0 | 1 (VarietyGenerator in varieties/types.py, additive) |
| Cyclic-import smoke coverage | none | 5 modules (varieties, render, _qt, cross_section, app) |
| Batch-end rollback tags | 0 | **5** (refactor-r3-b{1,2,3,4,5}-end) |
| MOVES.md rosetta cycles | r1 + r2 | **r1 + r2 + r3** |
| Anchor docs updated | (r2 state) | CLAUDE.md, README.md, MOVES.md, CONTEXT.md all current |

## Recommended follow-on milestones

1. **`repository-architect-post-r3-test-hardening-2026q3-e1`** — 4 new tests (~95 LOC total) closing the 4 unique test-suggester findings.
2. **`repository-architect-post-r3-tooling-hardening-2026q3-e2`** (optional) — fold in r2's deferred MED-1 (rewrite-imports.py partial-rewrite bug — RESOLVED in r3 B1) + r2's LOW-3 path-string scanner companion for tests (B3 test_icons.py deviation reproduces this class of issue) + r2's LOW-4 inline-execution drift documentation.

---

*Phase 5 rectify complete. r3 ships as the cleanest restructure in the AVC pipeline series: zero CRITICAL findings caught after execution; the dry-run validator caught the 3 RED blockers BEFORE any code moved; the design-adversary's 3 HIGH and 3 MEDIUM were all addressed inline in PLAN.md before Phase 4 began.*
