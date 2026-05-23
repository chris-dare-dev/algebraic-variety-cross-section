# Design adversary critique — restructure-full-audit-2026q2-r1

**Reviewed:** PLAN.md @ e1f9bba (HEAD), symbol-map.json @ e1f9bba (HEAD)
**Axes walked:** 11
**Verdict:** PROCEED-WITH-CONDITIONS

---

## Findings by severity

### HIGH — Batch 5 violates the "conservative bias" brief framing (Axis 4 + Axis 2)

**Axis:** 4. Over-engineering relative to repo size / 2. AI-15 honesty of design rationale
**Where:** PLAN.md section 1: "Evaluator FAIL #17 (surfaces.py >800 LOC, partial address) + current-state §4.2 (Numba kernels = cleanest seam) → Batch 5"

**Why it matters:** The user brief explicitly says "conservative bias." The evaluator report records FAIL #17 as a size/monolith flag; it does NOT mandate extraction of a specific subsection in this restructure. The 11 Numba kernels being "the cleanest seam" is a scout-A observation about future extractability, not a finding that requires action now. Scout-A §13 (already good / don't fix) explicitly says "Numba kernels in surfaces.py are already well-organized … They don't need urgent extraction unless surfaces.py is being split." The PLAN inverts this: it uses the kernel extraction as the partial response to FAIL #17, but FAIL #17 was already being noted as deferred for the larger monolith work. The only genuine justification for Batch 5 in THIS restructure is LOC reduction on surfaces.py; 401 LOC moved to a private module reduces surfaces.py from 1811 to ~1410 LOC — still well above the 800-LOC flag, closing nothing on the checklist. No evaluator FAIL item requires kernel extraction. The synthesis is performing the extraction because it can, not because the brief or evaluator requires it now.

**Suggested fix:** Demote Batch 5 from the current restructure to a design note in PLAN.md's "Explicitly NOT addressed" section (alongside FAIL #11 and FAIL #17 app.py). Mark it "DEFERRED — requires its own surfaces-split milestone to be meaningful; a partial 401-LOC extraction leaves surfaces.py at 1410 LOC and closes zero checklist items." The restructure closes 6 evaluator FAILs cleanly in Batches 1-4; Batch 5 adds medium risk without closing a FAIL.

---

### HIGH — Batch 5 threading-layer ordering guarantee is asserted, not verified (Axis 1 / AI-6)

**Axis:** 1. AI-1..AI-15 conflicts
**Where:** PLAN.md section 5 (Batch 5 shim): "Because `surfaces.py` imports `_field_kernels` first thing, the side-effect runs before any generator is called — AI-6 / AI-21 invariant preserved."

**Why it matters:** The PLAN relies entirely on import order at the `surfaces.py` module level to guarantee that `numba.config.THREADING_LAYER = "workqueue"` runs before any kernel compiles. The current code (surfaces.py:L38-39, verified) sets the config THEN imports `njit`/`prange` from numba in the same module. After Batch 5, the config write moves to `_field_kernels.py` and `surfaces.py` does `from _field_kernels import (...)`. This ordering works as long as `_field_kernels` is not imported independently before `surfaces` — but `test_numba_field_kernels.py` does exactly `from surfaces import _<name>_field_kernel`, which would correctly trigger the chain. However, nothing prevents a future test or IPython session importing `_field_kernels` directly (it's a discoverable private module), bypassing `surfaces.py` entirely and potentially hitting a kernel compile before the config write. This is not an invariant LIFT request — no existing test or caller does this — but the PLAN's claim "the side-effect runs before any generator is called" is true of `surfaces.py`-mediated access only, and there is no enforcement mechanism. The PLAN's section 6 AI-6 cell asserts preservation but does not address the direct-import bypass path. For a private module named `_field_kernels.py`, this is a medium-probability future footgun.

**Suggested fix:** If Batch 5 is retained after the HIGH-1 decision: place the `numba.config.THREADING_LAYER = "workqueue"` assignment at the TOP of `_field_kernels.py` (before the `from numba import njit, prange` line), exactly mirroring the current surfaces.py pattern. This makes `_field_kernels` self-contained on the threading config regardless of import path, and the `surfaces.py` re-export becomes purely structural. The current PLAN description implies this is already the intent ("import-time threading-layer config moves with them") but section 5 also says the config "moves WITH the kernels" without specifying it must precede the `from numba import ...` line in `_field_kernels.py` itself. Make that constraint explicit in the implementer-facing spec.

---

### MEDIUM — Batch 4 test file in same batch as refactor: rationalization accepted too easily (Axis 9 + Axis 8)

**Axis:** 9. Cross-suite test gaps / 8. Test parity risk
**Where:** PLAN.md section 5 (Batch 4 shim plan): "This is the ONE exception to scout-C §10.1 ('don't add features in the same PR as the refactor'); the shim-tests ARE the refactor's safety net, not a new feature."

**Why it matters:** The PLAN correctly distinguishes safety-net tests from feature tests; this is a real exception class. However, the rationalization deserves scrutiny: `scripts/repository-architect/validate-shims.py` already exists as a structural shim-integrity check. Adding four test functions in `tests/test_panels_shims.py` that each do `from <old_path> import <Class>` and assert a `DeprecationWarning` is genuinely load-bearing — if the `__getattr__` shim is broken (wrong stacklevel, wrong module path, typo in the forwarded attribute name), the validate-shims script catches structural absence but NOT a shim that exists but silently fails to emit the warning. So the exception is legitimate. The medium concern is narrower: the four new shim tests import `AppearancePanel` (a QWidget subclass) to verify the shim fires. This is import-only (the PLAN asserts no construction), which respects AI-2. But the PLAN's AI-2 analysis (section 6) says "Importing the class does NOT construct it — no QApplication needed." This is correct for `AppearancePanel.__init__` (which requires a parent widget), but PySide6 QWidget subclasses register their metaclass at import time via `Shiboken`, which does require `libshiboken` to be importable. In AVC's test environment this is already satisfied because `test_clip_cache.py` imports `app` at module level. But the PLAN does not verify whether any of the four panel modules perform module-level Qt calls (e.g., icon registration, `QCoreApplication.instance()` calls) that would fail without `QApplication`. Given `appearance_panel.py` imports `icons.py` which does `import qtawesome`, and `icons.py` does lazy loading, this is likely fine — but it is not confirmed in the PLAN.

**Suggested fix:** Add one sentence to PLAN.md section 6 AI-2 row: "Confirmed: none of the four panel module top-levels call `QApplication.instance()` or construct Qt objects at import time (grep for `QApplication`, `QWidget(`, `QDialog(` in each panel's module-level code — zero hits)." This documents the pre-flight check rather than leaving it implicit.

---

### MEDIUM — parameter_grid_panel.py rename is low signal-to-noise for this restructure (Axis 2 + Axis 11)

**Axis:** 2. AI-15 honesty of design rationale / 11. Effort honesty
**Where:** PLAN.md section 2 (tree diff): `panels/parameter_grid_widget.py (← parameter_grid_panel.py — renamed for clarity per current-state §13.6)`; symbol-map.json entry: `"from": "parameter_grid_panel", "to": "panels.parameter_grid_widget"`

**Why it matters:** Scout-D §13.6 (current-state-brief.md) explicitly categorized renaming `parameter_grid_panel.py → parameter_grid_widget.py` as "low signal-to-noise" and described it as a "cosmetic improvement." The PLAN cites this section as justification for the rename but that section's actual verdict was to flag it as debatable. The rename introduces an asymmetry in the symbol-map: all other three panel moves are module-only relocations (name unchanged, just moved into `panels/`); this one combines relocation with rename. That means the shim at `parameter_grid_panel.py` must forward to `panels.parameter_grid_widget`, a two-level difference (directory + name), while the other three shims forward to a directory-only move. It also means the `parameter_grid_panel.ParameterGridPanel` → `panels.parameter_grid_widget.ParameterGridPanel` chain in the symbol-map creates a longer-than-necessary entry that future maintainers reading `MOVES.md` must trace. Scout-C §10.1 anti-pattern R1 says "refactor and add features in the same PR" is refused; a rename bundled with a move is not R1 but it adds gratuitous surface to an already-medium-risk batch. The rename brings zero structural benefit that couldn't be deferred to the surfaces-split or app.py-extract milestone when the naming context is more stable.

**Suggested fix:** Drop the rename from this restructure. Move `parameter_grid_panel.py → panels/parameter_grid_panel.py` (name unchanged). Add a one-line PLAN note: "Rename to `parameter_grid_widget.py` deferred — low signal-to-noise per current-state §13.6; will be reconsidered when panels/ internal naming is stabilized post-app.py Extract Class." This reduces the symbol-map asymmetry and makes Batch 4's shim shape uniform (all four shims forward to same-named module under `panels/`).

---

### MEDIUM — MOVES.md not listed in anchor update plan (Axis 7)

**Axis:** 7. Anchor coverage
**Where:** PLAN.md section 8 (rollback plan): "What rollback does NOT restore: MOVES.md entries (manual revert via `git checkout refactor-baseline-restructure-full-audit-2026q2-r1 -- MOVES.md`)."

**Why it matters:** MOVES.md is listed only in the rollback plan, not in the affirmative anchor-update checklist. Scout-C §9 (Phase 8 mechanics) and refactor-pattern-brief.md §11 both specify that MOVES.md must be CREATED (it does not exist: `ls MOVES.md` returns MISSING) and updated with `{from_path} → {to_path}` entries for every moved symbol as a primary Phase 8 anchor. The PLAN section 2 (tree diff) lists no `+ MOVES.md` in the new files. The PLAN's batch sequencing section says "one `repository-architect-implementer` invocation per batch … each dispatches parity-verifier + anchor-updater" but does not confirm the anchor-updater creates MOVES.md on Batch 4's run. This is a gap: after execution, a future session's agent will encounter the panels/ shims and have no MOVES.md rosetta stone to consult.

**Suggested fix:** Add `+ MOVES.md` to the tree diff under Batch 4 (first batch with file moves). Explicitly state in section 2: "MOVES.md is created by the anchor-updater agent on Batch 4's run; subsequent batches append to it." Verify the anchor-updater's spec includes MOVES.md creation.

---

### MEDIUM — Batch 5 re-export "NOT a deprecation shim" distinction is semantically unsound (Axis 5)

**Axis:** 5. Shim-cycle correctness
**Where:** PLAN.md section 5: "The re-export inside surfaces.py is NOT a deprecation shim — it is a permanent re-export. AVC's internal-only test imports keep using `from surfaces import _<name>` for convenience."

**Why it matters:** The PLAN draws a sharp line between "deprecation shim" and "permanent re-export" to justify skipping the standard shim lifecycle (DeprecationWarning, removal milestone). But the functional difference is definitional rather than behavioral: both patterns keep an old import path working by forwarding to a new location. The practical problem is that calling this a "permanent re-export" removes it from any shim-removal tracking mechanism. If a future restructure removes the re-export (the PLAN acknowledges this: "If a future restructure removes the re-export, it's a separate decision"), that future session will have no MOVES.md entry, no DeprecationWarning, and no removal milestone to follow. The re-export is a shim by another name with the deprecation cycle removed. For INTERNAL-ONLY private symbols (all 11 are `_underscore`), the case for a full DeprecationWarning cycle is weak — but the case for a MOVES.md entry noting "these symbols now live in `_field_kernels.py` and are re-exported from `surfaces.py` for convenience" is strong.

**Suggested fix:** Relabel the re-export as "internal-convenience re-export (no deprecation cycle per R10 exception for underscore-private symbols)." Add a MOVES.md entry for each kernel noting its new authoritative location is `_field_kernels.<name>` with surfaces.py as a permanent convenience alias. This keeps the distinction honest without requiring a DeprecationWarning on purely internal private symbols.

---

### LOW — Batch 3 delta estimate understates styles.py change uncertainty (Axis 11)

**Axis:** 11. Effort honesty
**Where:** PLAN.md section 4 (delta size table): "styles.py +0 to +5 (may need new role rule)"

**Why it matters:** The Batch 3 fix replaces `setStyleSheet(f"background: {BG_GRID_SCENE}; border: none;")` with a QSS role property. Whether styles.py needs a new role rule depends on whether `BG_GRID_SCENE` as a themed background is already represented in `_render_stylesheet`. If it is not, a new role selector must be added to BOTH `APP_STYLESHEET` and `APP_STYLESHEET_DARK` (per CONTEXT.md §4.3b: "The QSS role selectors in `_render_stylesheet` handle color + font for both themes"). The PLAN says "+0 to +5" but does not confirm whether the role already exists. If it doesn't, the delta is closer to +10-15 (two new `[role="grid-scene-bg"]` blocks, one per stylesheet). This is a LOW because Batch 3 is trivially low-risk regardless of the exact LOC delta — it doesn't affect sequencing or correctness.

**Suggested fix:** Before writing the Phase 3 preflight, check whether `_render_stylesheet` already contains a `BG_GRID_SCENE`-equivalent role selector. If not, the delta table for Batch 3 should read "styles.py +10 to +15 (new role selector in both light + dark stylesheet blocks)."

---

### LOW — Rollback plan Tier-3 grep command has a fragile regex (Axis 6)

**Axis:** 6. Rollback feasibility
**Where:** PLAN.md section 8 (Batch 5 partial rollback): `BATCH5_BASE=$(git log --oneline --grep="batch 4/5" -1 --format=%H)`

**Why it matters:** The grep pattern `"batch 4/5"` relies on the Batch 5 first commit's message containing the literal string "batch 4/5". Phase 4's execution protocol says "one Fowler op per commit" and typically uses messages like `refactor: extract _field_kernels.py (batch 5/5)`. If the implementer writes "batch 5 of 5" or "batch5" or uses a different subject format, the grep silently returns empty, and the `git revert --no-commit ${BATCH5_BASE}..HEAD` command reverts the entire history from the beginning — a destructive mistake. The Tier 1 command (tag-based) is correct and robust; the Tier 3 command is fragile.

**Suggested fix:** Replace the grep-based SHA lookup with a tag-based lookup: `git revert --no-commit refactor-batch4-end..HEAD` where `refactor-batch4-end` is a tag that Phase 4's implementer creates after Batch 4 completes (symmetric with the baseline tag). Or document that the implementer MUST embed the exact string "batch 4/5" in the last Batch 4 commit message. One of these two — not both is fine.

---

### LOW — README "Extending the app" section path references will be stale after Batch 4 (Axis 7)

**Axis:** 7. Anchor coverage
**Where:** README.md "Extending the app" section (L307-315): step 1 says "Write a generator function in `surfaces.py`"; step 5 says "Add at least a smoke test in `tests/test_mesh_generators.py` and a parameter-range entry in `tests/test_parameters_panel.py`."

**Why it matters:** After Batch 4 moves panel files to `panels/`, the smoke-test import at README:L575 (`python -c "import app, surfaces, view_panel, parameters_panel, appearance_panel; print('OK')"`) will break because `view_panel`, `parameters_panel`, `appearance_panel` will no longer be importable at those flat paths — only shims remain. The PLAN section 2 lists `README.md ±15 (project-structure + smoke-test + extending sections)` under Batch 4's modified files, which is correct. This LOW is just confirming the specific stale references: (1) the smoke-test command at CONTEXT.md §10 uses the same flat imports and must ALSO be updated; (2) the "Extending the app" step 5 references `tests/test_parameters_panel.py` which imports from `surfaces` directly (not from `panels/*`) — this specific reference will stay valid since Batch 4 does not move `test_parameters_panel.py`. No action needed on step 5.

**Suggested fix:** The PLAN already lists README.md as modified in Batch 4. Add a note that CONTEXT.md §10 smoke-test command must be updated in the same batch (current PLAN only lists `CONTEXT.md ±10 (panel path refs)` without calling out the §10 smoke-test line explicitly). This prevents the implementer from updating "Project structure" while leaving the §10 invocation stale.

---

## Axes with NONE findings

**Axis 1 (AI-1..AI-15 conflicts):** All 15 invariants reviewed. AI-2 (Qt-free tests) is addressed in the PLAN's section 6 with an import-only analysis for the shim test. AI-6 threading-layer ordering is addressed (though with an implementation ambiguity captured in HIGH-2 above). AI-8 VARIETIES registry and ParamSpec/Surface dataclasses remain in surfaces.py untouched. AI-9 re-entrancy guard: app.py logic is unchanged — LibCST import-path rewrites only. AI-11 fully-qualified Qt enums: new code (shim files, panels/__init__.py) contains no Qt code by construction. AI-12 WCAG: Batch 3 proactively fixes the BG_GRID_SCENE regression. AI-7, AI-10, AI-13, AI-14, AI-15: all untouched by this restructure. No invariant lift is required.

**Axis 3 (Hallucinated patterns):** No anti-patterns from scout-B §5 or scout-C §10 are introduced. The `panels/` subpackage is a legitimate Introduce Subpackage operation with `__getattr__` shims (not star-imports). No `utils.py` grab-bag, no package-by-layer naming, no capitalized directories, no src-layout imposed on a flat app. The PLAN explicitly defers FAIL #11 (avcs/ named package) with honest justification.

**Axis 6 (Rollback feasibility):** Rollback plan is substantive. Tier 1 uses the correct `git revert --no-commit <tag>..HEAD` form. The pre-test-in-scratch-worktree requirement is stated. The Tier 3 command has a fragile grep (captured as LOW-2) but Tier 1 is always available and functionally correct.

**Axis 8 (Test parity risk):** Section 7 (cross-suite test gaps) explicitly documents categories 3 (import-time side effects), 5 (seam tests), and 10 (cyclic-import smoke), all raised by the restructure. Pre/post collection count expectation is implicit ("zero test-file moves in this restructure") but not stated as an explicit number. Minor gap; not blocking.

**Axis 10 (Sequencing safety):** Batch order is correct: trivial additions → AI-navigability infrastructure → behavior fix → structural file moves → semantic extraction. Each batch depends on the prior being complete. Mechanical moves (Batch 4) precede semantic extraction (Batch 5). Batch 3 fixing the BG_GRID_SCENE bug BEFORE Batch 4 moves the file is explicitly motivated and correct.

---

## Recommended PLAN.md edits before Phase 3

1. **Section 1 and section 2:** Move Batch 5 to "Explicitly NOT addressed" with note: "DEFERRED — 401 LOC extraction leaves surfaces.py at ~1410 LOC, closes zero evaluator FAILs; scout-A §13 explicitly flags kernels as 'already well-organized' and not urgently extractable; extraction belongs in a dedicated surfaces-split milestone." Remove Batch 5 from the delta table, symbol map section, AI-invariant impact table rows, and test gap table rows. Update estimated total commits to ~9 (not ~12) and estimated wall-clock to ~75 min.

2. **Section 5 (Batch 5 shim — if Batch 5 retained):** Add explicit constraint that `_field_kernels.py` must place `numba.config.THREADING_LAYER = "workqueue"` before the `from numba import njit, prange` line, mirroring the current surfaces.py pattern, so the module is self-contained regardless of import path.

3. **Section 2 (tree diff):** Change `panels/parameter_grid_widget.py (← parameter_grid_panel.py — renamed)` to `panels/parameter_grid_panel.py (← parameter_grid_panel.py)`. Update symbol-map.json `"to": "panels.parameter_grid_panel"` for this entry. Add a note: "Rename to `parameter_grid_widget` deferred per current-state §13.6 low-signal assessment."

4. **Section 2 (tree diff):** Add `+ MOVES.md [Batch 4; created by anchor-updater; subsequent batches append]` to the new files list.

5. **Section 6 (AI-2 row):** Add sentence: "Pre-flight confirmation required: grep panel module top-levels for QApplication/QWidget construction at module scope (expected: zero hits)."

6. **Section 4 (Batch 3 delta):** Update styles.py delta to "+10 to +15 if BG_GRID_SCENE role selector not already present in _render_stylesheet" after a pre-flight check.

7. **Section 8 (Tier-3 rollback):** Replace the `git log --grep` SHA lookup with a tag-based form: "create tag `refactor-batch4-end` immediately after Batch 4 completes; Tier-3 Batch-5 rollback uses `git revert --no-commit refactor-batch4-end..HEAD`."

8. **Section 8 (anchor list):** Ensure CONTEXT.md §10 smoke-test command is listed as a Batch 4 update target (alongside the existing `CONTEXT.md ±10 (panel path refs)` line).
