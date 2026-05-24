# Execution critic critique — restructure-feature-subpackages-2026q2-r2

**Commit range:** `2bfc6c8..89cb525` (19 source commits + 4 metadata commits via Phase-4-step-end chores)
**Batches:** 9 executed (B1-B9)
**Verdict:** PROCEED-TO-RECTIFY (1 MEDIUM, 4 LOW findings; no CRITICAL/HIGH)

**Authored:** 2026-05-24 main session (inline per agent-timeout fallback pattern documented across the run)

---

## Summary

r2 successfully decomposed the 1811-LOC `surfaces.py` monolith into a 123-LOC hub shim (93% reduction) plus 8 stable canonical-path submodules under `varieties/`, plus 3 sibling feature subpackages (`render/`, `_qt/`, `cross_section/`). 506 tests pass at HEAD. All historical `from surfaces import X` imports continue to work via re-exports.

**Caught early (good):** the 12-axis design-adversary caught 3 real PLAN bugs (HIGH-1 panels.* test imports, HIGH-2 FAST_RENDER_THRESHOLD_MS missing, HIGH-3 _hanson_cross_section placement contradiction) PLUS the dry-run validator caught 1 more (fano_segre vs fano_segre_cubic naming). The axis-12 patch is paying off.

**Real downsides surfaced during execution:**

### MEDIUM — `rewrite-imports.py` partial-attribute-rewrite bug (recorded for follow-up tooling milestone)

**Where:** `.claude/scripts/repository-architect/rewrite-imports.py` `cst.CSTTransformer.leave_Attribute`
**Why it matters:** Caused 11 test failures in B3 that required ~30 min of manual fixup across 5 test files. The script rewrites SOME `module.X` references to `_qt.module.X` but leaves others, creating inconsistent namespaces. Recovery cost was high.
**Suggested fix (deferred):** redesign the LibCST transformer to either (a) consistently rewrite ALL attribute chains starting with a moved module, OR (b) rewrite ONLY imports and let humans/IDE handle attribute access. A dedicated tooling-hardening milestone should address this BEFORE the next `/repository-architect` invocation.

### LOW — Sub-agent socket timeouts (transient infrastructure issue)

**Where:** B1 anchor-updater (43m timeout), B2 implementer (21m, 5 tool uses)
**Why it matters:** Forced the user to choose "Continue inline" path. The work was still completed, but main-session execution is slower per token and inherently context-bounded.
**Suggested fix (deferred):** This appears to be transient infrastructure rather than a pipeline bug. If it recurs in r3, may warrant investigation of the agent's reading patterns (B1 anchor-updater spent 43 min walking the agent-memory tree exhaustively).

### LOW — `rewrite-imports.py` doesn't exclude `.claude/scripts/`

**Where:** rewrite-imports.py walks `.claude/scripts/frontend-uplift/render-panel-chrome.py` and rewrote 1 import there in B3
**Why it matters:** Per pipeline external-write boundary, `.claude/scripts/` should be untouched. The script was already broken from r2 B1's panel-shim deletion; the additional rewrite is correct in isolation but represents a scope violation by the tooling.
**Suggested fix (deferred):** add `.claude/scripts/` and `.claude/notes/` to the rewrite-imports.py exclusion list.

### LOW — Test path-string references not LibCST-rewritable

**Where:** 5 test files in B3 (`test_styles_palette.py`, `test_enriques_hq_smoothing.py`, `test_render_busy_spinner.py`) had `"panels"/"appearance.py"`-style path-string Path() constructions that LibCST cannot rewrite (it operates on AST imports, not string literals)
**Why it matters:** Required manual sed/Edit fixups in B3. Foreseeable in future restructures that move files referenced via path-strings in tests.
**Suggested fix (deferred):** consider a path-string scanner companion to `rewrite-imports.py` that flags path-string literals matching moved file paths. Run as part of Phase 3 dry-run validator.

### LOW — Inline-execution drift from PLAN.md sequence

**Where:** B3 PLAN.md specified 4-commit sequence; execution collapsed to 2 commits (clean per pytest at each step); B6 + B7 + B8 used the inline-execution Python extraction script approach rather than per-PLAN.md commit-per-Fowler-op
**Why it matters:** The PLAN was a useful target; the execution adapted to the reality that inline workflow lets you verify at every step. Net positive (fewer commits, same safety), but worth documenting that "PLAN.md says N commits per batch" became "PLAN.md says approximately N commits, plus adaptation."
**Suggested fix:** the PLAN.md template's commit count is honest as a "credible upper bound" rather than a strict contract. Documented for future restructures.

---

## Re-verification by main-session rectifier

- MEDIUM (`rewrite-imports.py` partial-rewrite): CONFIRMED. All 5 fix-up sites needed are documented in MOVES.md B3 section. Tool fix DEFERRED to a dedicated tooling milestone (per design-adversary v2 axis-12 — this would itself be a high-ROI fix per scout-C 1.5; consider for a `repository-architect-post-r2-tooling-hardening-2026q3-r3` milestone).
- LOW-1 (timeouts): transient; not actionable in this rectify pass.
- LOW-2 (.claude/scripts/ scope): a 1-line tooling fix; defer with LOW-1.
- LOW-3 (path-string scanner): nice-to-have; defer with LOW-1.
- LOW-4 (inline vs plan): documentation only; defer.

All 5 findings are DEFERRED. No source-edit rectification needed at HEAD.

---

## Final rectification

Documentation footer only (no source edits at HEAD). The rectification commit is the next commit which records this critique + the deferred-finding list.
