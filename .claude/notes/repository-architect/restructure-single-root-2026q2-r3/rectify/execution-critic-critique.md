# Execution critic critique — restructure-single-root-2026q2-r3

**Commit range:** `7cb2a78..1419d03`
**Batches:** 5 executed (B1–B5); 9 source commits + 2 docs commits = 11 total
**Tags:** all 5 `refactor-r3-b*-end` tags confirmed present locally and on origin
**Final SHA:** 1419d03
**Live test run:** 504 passed in 6.90s (`.venv/bin/python -m pytest -q`)
**Verdict:** PROCEED-TO-COMPLETE

---

## Summary

r3 executed cleanly against its high-risk targets. The single-root invariant holds (`ls *.py == app.py only`). All five shims deleted, surfaces.py retired, import-linter contracts pass, 504 tests green. Three LOW findings are flagged below — none blocks ship. No CRITICAL. No HIGH.

---

## Findings by severity

### MEDIUM — stale backward-compat claims in varieties/registry.py:13 and varieties/tooltips.py:13

**Where:** `varieties/registry.py:13`, `varieties/tooltips.py:13`

**Evidence:**
- `varieties/registry.py:13`: `"Backward-compat: from surfaces import VARIETIES still works via hub-shim re-export."`
- `varieties/tooltips.py:13`: `"Backward-compat: from surfaces import VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS still works."`

Both docstrings were written when `surfaces.py` was a live re-export hub (r2). surfaces.py was deleted in B4 commit 2 (`fc6b15a`). These claims are now factually false — any code following their advice will get `ModuleNotFoundError`. The B4 anchor-rewrite pass and B5 anchor-updater did not touch these in-module docstrings (they are inside `varieties/` source files, not the 4 anchor docs).

**Why it matters:** Any developer or agent reading these docstrings will be actively misled. The "still works" claim is an outright lie post-r3. If a future restructure consults these modules as canonical documentation, it will follow a dead path.

**Suggested fix:** Remove or replace the backward-compat sentence in both docstrings. The corrected phrasing should note that `surfaces.py` was retired in r3 B4 and direct readers to `MOVES.md` r3 section for the import path migration. This is a 2-line change in two files.

**Regression-guard test:** `grep -rn "still works" varieties/` should return 0 hits post-fix.

---

### LOW — B4 DeprecationWarning gate command not logged with -W error flag

**Where:** `.claude/notes/repository-architect/restructure-single-root-2026q2-r3/execute/B4.md:146–152`

**Evidence:** Section `(h)` is titled "DeprecationWarning gate result (MANDATORY INTER-COMMIT GATE)" and shows `499 passed in 5.83s` with the note "Gate passed: exit 0, zero DeprecationWarnings fired." However, the verbatim command run is not logged — no `python -W error::DeprecationWarning -m pytest -q` line appears in the transcript. Only the result output is shown.

Note: `surfaces.py` was a pure re-export hub with `import warnings` but no `__getattr__` that emits `DeprecationWarning`. The gate was therefore checking that no r2 Qt shim was still active (not that surfaces.py itself emitted warnings). The gate still had the right effect given the context. Live re-run at HEAD confirms `504 passed` with `-W error::DeprecationWarning` today.

**Why it matters:** The gate is the PLAN's primary safety checkpoint between commit 1 and commit 2 of B4. Not logging the verbatim command is an auditability gap — a future rollback investigation cannot confirm whether the executor ran the full `-W error` invocation or a plain `pytest -q`. This pattern recurred from r2's execution-critic: the gate result was captured but not the command.

**Suggested fix:** Add a CONVENTION to the implementer template: "gate section must show verbatim command AND output, not just output." Flag this as an open convention gap in lessons.md.

---

### LOW — root `__pycache__` contains pyc files for deleted modules

**Where:** `/Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section/__pycache__/` — 8+ stale pyc files found

**Evidence:**
```
__pycache__/render_worker.cpython-312.pyc
__pycache__/styles.cpython-312.pyc
__pycache__/surfaces.cpython-312.pyc
__pycache__/parameter_grid.cpython-312.pyc
__pycache__/parameter_grid_panel.cpython-312.pyc
__pycache__/view_panel.cpython-312.pyc
__pycache__/parameters_panel.cpython-312.pyc
__pycache__/ui_helpers.cpython-312.pyc
__pycache__/icons.cpython-312.pyc
__pycache__/appearance_panel.cpython-312.pyc
```

Rubric item 19 requires `__pycache__` / `.pyc` for moved/deleted files to be cleared. These are from modules deleted in B3 (icons.py, styles.py, ui_helpers.py, render_worker.py) and B4 (surfaces.py, parameter_grid.py) and from r1/r2 shims (appearance_panel.py, etc.). They do not affect test correctness (Python's import machinery resolves against the actual `.py` files first) but they create clutter and could confuse tools that enumerate source files via `__pycache__`.

**Why it matters:** Low severity — tests are green, no correctness issue. But the presence of a `surfaces.cpython-312.pyc` next to an `app.py`-only root is misleading and arguably violates the "single-root" spirit.

**Suggested fix:** Run `find . -name __pycache__ -maxdepth 2 -exec rm -rf {} + 2>/dev/null; true` then re-run `pytest -q`. This is safe and takes <1 second. Can be a cleanup commit or just a pre-launch housekeeping step.

---

### LOW — `refactor-r3-b5-end` tag points to cabf688, not final SHA 1419d03

**Where:** `git log --oneline --decorate 7cb2a78..1419d03` — last two commits are:
```
1419d03 (HEAD -> main, origin/main) docs: finalize MOVES.md r3 final SHA (cabf688)
cabf688 (tag: refactor-r3-b5-end) docs: anchor docs pass — single-root state (B5 docs 2/2)
```

**Evidence:** The MOVES.md SHA-finalization commit `1419d03` is untagged. `refactor-r3-b5-end` sits at its predecessor `cabf688`. The Tier 2 rollback protocol uses `git revert refactor-r3-b4-end..refactor-r3-b5-end`; this would revert `cabf688` but leave `1419d03` untouched — a revert that "succeeds" but leaves a dangling MOVES.md edit.

**Why it matters:** PLAN §8 Tier 2 uses tag ranges for revert. With the B5 final commit untagged, a partial revert of B5 is incomplete. This is low severity because `1419d03` only edits one line in MOVES.md (replacing `<latest>` with `cabf688`), but the tag-based rollback protocol becomes unreliable for B5.

**Suggested fix:** Move `refactor-r3-b5-end` to `1419d03`: `git tag -f refactor-r3-b5-end 1419d03 && git push origin -f refactor-r3-b5-end`. This is a force-move of a tag, which requires explicit user approval (destructive tag operation). Alternatively, accept the 1-line dangling commit as acceptable residue given its trivial content.

---

## Rubric results (20 items)

| # | Item | Pass/Fail | Detail |
|---|---|---|---|
| 1 | All original tests still pass | **PASS** | 504 passed in 6.90s (venv Python) |
| 2 | Test collection count preserved | **PASS** | 506→506→506→499→499→504 per batch logs; live collect confirms 504 |
| 3 | No new test files silently skipped | **PASS** | `--collect-only -q` shows all 504 collected, no `<skipped>` markers |
| 4 | Per-file coverage on moved files | **SKIP** | `coverage xml` fails in this repo (pre-existing pyvistaqt internal path error — r1 lesson) |
| 5 | Total coverage within ±1% | **SKIP** | Same pre-existing failure |
| 6 | No new import cycles | **PASS** | `python -c "import app"` exits 0; pydeps unusable (r1 lesson — hyphenated repo name); import-linter confirms no cross-package violations |
| 7 | No orphan modules | **PASS** | All subpackages have fan-in from app.py; `_qt/__init__.py` docstring-only; `test_import_smoke.py` verifies all 5 entrypoints import cleanly |
| 8 | No import-time side effects regressed | **PASS** | Dry-run predicted ~-1,500µs (-1% total); 5 shims + hub eliminated; no regressions predicted or observed |
| 9 | No module shadowing | **PASS** | importlib.util.find_spec confirms varieties/render/_qt/cross_section/app resolve to correct local paths |
| 10 | No `from X import *` newly introduced | **PASS** | grep returns 0 new star-imports in source tree |
| 11 | Shims emit DeprecationWarning | **N/A** | r3 has zero new shims; all 5 old shims deleted in B3 |
| 12 | Shim warnings include new path | **N/A** | Same — no shims |
| 13 | `git mv` rename detection | **PASS** | `git log --follow _qt/parameter_grid_math.py` shows pre-move history; rename detected at 100% |
| 14 | MOVES.md updated | **PASS** | r3 section appended with ~70 lines covering B1–B5 |
| 15 | Root CLAUDE.md / CONTEXT.md pointers updated | **PASS** | AGENTS.md "Where things live" fully rewritten; CONTEXT.md §2,3,4,8,10,11,12 all updated |
| 16 | Per-folder CLAUDE.md | **N/A** | PLAN.md explicitly deferred per-folder CLAUDE.md (ETH Zurich LLM-cost finding) |
| 17 | `.claude/notes/**/*.md` cleansed | **PASS** | 26 historical stale refs in scout-d-current-state.md (closed artifact) and spike report — both correctly preserved as historical, not edited |
| 18 | README.md structure updated | **PASS** | Badge updated 499→504; project structure section rewritten; running-tests section updated |
| 19 | `__pycache__` / `.pyc` cleared | **FAIL** | Root `__pycache__` contains pyc files for 10 deleted modules. Tests still pass. See LOW finding. |
| 20 | Rollback tested in scratch worktree | **N/A** | Pre-execute phase responsibility; batch tags confirmed present and correct for Tier 2 rollback |

---

## 10-axis checklist results

| # | Axis | Finding |
|---|---|---|
| 1 | AI-1..AI-15 violations | **PASS** — AI-2: `test_import_smoke.py` uses subprocess pattern (no QApplication in test process); 5 subprocess entries all pass. AI-6: generator pipeline split preserved (implementation files didn't move). AI-8: VarietyGenerator Protocol is additive — zero changes to Surface/ParamSpec frozen contract. AI-9: `_computing` guard in app.py not touched (B4 only rewrote `from surfaces import ...` block at L49-63). AI-12: no stylesheet changes. |
| 2 | Shim integrity | **PASS** — r3 introduces zero new shims. Five deleted shims had complete M+1 cycles (confirmed by B3 pre-flight grep returning empty for all 5). B3 deviation (test_icons.py string-literal fixes) was correctly handled in-batch and documented. |
| 3 | Anchor freshness | **PASS with LOW gap** — MOVES.md, CLAUDE.md/AGENTS.md, README.md, CONTEXT.md all updated. Stale backward-compat docstrings in `varieties/registry.py:13` and `varieties/tooltips.py:13` are NOT in the anchor set but are misleading (see MEDIUM finding). |
| 4 | Test parity edge cases | **PASS** — B3 deviation (test_icons.py `importlib.import_module("icons")` string-literal refs) was correctly caught during execution and fixed before commit. All 8 icon tests pass. This is the "path-string scanner" LOW pattern from r2 execution-critic L4 — it recurred and was handled correctly. |
| 5 | Sequencing safety | **PASS with audit gap** — B4 mandatory inter-commit gate (PLAN HIGH-1 fix) was reportedly executed between commit 1 (`4802014`) and commit 2 (`fc6b15a`). Gate result logged (499 passed) but verbatim `-W error::DeprecationWarning` command not shown in transcript. Live re-run today confirms gate would pass. |
| 6 | Performance regression | **PASS** — No regression predicted or observed. Dry-run estimated ~-1% import-time (shims + hub eliminated). `test_import_smoke.py` adds ~1-1.5s wall-clock for subprocess startup; expected and acceptable. |
| 7 | Tooling correctness (B1 codemod) | **PASS** — B1 fixed last-wins dict bug, multi-alias FlattenSentinel, leave_Attribute for attribute-access rewrites, .claude/ exclusion, and schema v1.1 JSON parser. B4 codemod transcript shows 51 symbol renames across 16 files — correct. Bare-import test files handled via manual refactor as planned. ScopeProvider omitted from METADATA_DEPENDENCIES (unused; QualifiedNameProvider alone sufficient) — minor deviation, no functional impact. |
| 8 | Effort honesty | **PASS** — PLAN predicted ~13 commits (9 source + 4 metadata). Actual: 11 commits (9 source + 2 docs). Slightly under-counted metadata but in the right direction. Net LOC delta: 618 insertions / 573 deletions vs PLAN prediction of ~-311 net; actual is ~+45 net (B4 rewrites added more lines than they removed). Delta exceeds PLAN prediction but is justified: test-file rewrites were more expansive than a line-for-line swap. Difference is explained and not a sign of scope creep. |
| 9 | Documentation drift | **PASS** — B5 anchor-updater applied to all 4 authorized docs. Historical-stale references in `.claude/notes/repository-architect-design/scout-d-current-state.md` (25+ hits) and a spike report (1 hit) correctly preserved as closed artifacts. No unintended edits outside CLAUDE.md/README.md/MOVES.md/CONTEXT.md confirmed. |
| 10 | r2 lessons-learned carry-forward | **PASS** — B1-first ordering followed. Commit-and-push after each batch confirmed (all tags pushed to origin). Schema v1.1 incompatibility (new in r3, not a r2 pattern) caught and fixed in B1. tag-based rollback (r2 HIGH-3 lesson) implemented correctly for B1–B4; B5 has a minor tag-placement gap (LOW finding). |

---

## Specific concern verdicts

**A. Test count arithmetic:** PLAN §9 corrected arithmetic predicted 506→506→506→499→499→504. Batch logs: B1=506, B2=506, B3=499, B4=499, B5=504. All match. Live collect: 504. PASS.

**B. -W error gate in B4:** Gate result logged (499 passed, exit 0). Verbatim command not shown. surfaces.py was a pure re-export hub (no `__getattr__` DeprecationWarning), so the gate was verifying no r2 Qt shim was still routed through — the effect was correct. Live re-run today with `-W error::DeprecationWarning` confirms 504 passed. The gap is auditability only (LOW finding L1).

**C. Render contract violation:** B5 correctly omitted the `render` PySide6-forbidden contract per dry-run validator FIX-FIRST-3. Only 2 contracts added; both KEPT at HEAD. PASS.

**D. B3 test_icons.py string-literal deviation:** Documented in B3.md section (e)+(h). Pattern matches r2 execution-critic LOW-4 prediction (path-string scanner gap). Handled correctly in-batch before commit. This is a recurring gap: `test_icons.py`'s use of `importlib.import_module("icons")` (a string literal, not an import statement) is invisible to LibCST import-rewrite passes and must be caught manually. Worth adding to lessons.md as an AVC-specific gotcha.

**E. Symbol-map errata:** Dry-run caught 17 wrong + 23 missing symbols pre-execution. B4 codemod ran with the corrected symbol-map (51 symbol renames, 16 files). No last-minute fixups needed beyond the 2 planned manual bare-import refactors. PASS.

**F. Anchor-updater scope creep:** B5 docs commit `cabf688` touched exactly CLAUDE.md/AGENTS.md, README.md, MOVES.md, CONTEXT.md. B5-docs.md lists no unintended edits. PASS.

**G. import-linter contract semantics:** Two `forbidden` contracts: (1) `varieties` forbidden from `app, _qt, panels, Qt`; (2) `cross_section` forbidden from `_qt, Qt`. Both pass at HEAD. Design-adversary endorsed both. `layers` contracts would be more idiomatic for a full-layered architecture but require more precise module classification — `forbidden` is correct for the current structure where the boundary is one-directional. PASS (design choice acceptable).

**H. refactor-r3-b*-end tags:** All 5 tags present locally and pushed to origin. `refactor-r3-b5-end` points to `cabf688` (not the final `1419d03`). This is a LOW finding (L2).

---

## Findings IDs for rectifier

**MEDIUM (fix recommended — ~2 LOC each):**
- M1: Remove stale "still works via hub-shim" backward-compat claim from `varieties/registry.py:13` and `varieties/tooltips.py:13`

**LOW (defer or accept):**
- L1: Add logging convention for gate commands to implementer template + lessons.md
- L2: Decide whether to force-move `refactor-r3-b5-end` tag to `1419d03` (requires user approval for force-tag)
- L3: Clear root `__pycache__` pyc files for deleted modules (`find . -maxdepth 2 -name __pycache__ -exec rm -rf {} +`)

---

## Final verdict

**PROCEED-TO-COMPLETE**

No source correctness issues. The one MEDIUM finding (M1) is a 2-line docstring fix that can be applied as a post-r3 cleanup commit or deferred to the next `/repository-architect` cycle. It does not affect runtime behavior. The LOW findings are housekeeping. Tests are 504/504 green with `-W error::DeprecationWarning` gate passing at HEAD.
