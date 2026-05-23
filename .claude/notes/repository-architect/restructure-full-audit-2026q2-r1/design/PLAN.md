# PLAN.md — restructure-full-audit-2026q2-r1

**Synthesized:** 2026-05-23 (Phase 2, main session)
**Revised:** 2026-05-23 v2 — addresses design-adversary HIGH-1 + HIGH-2 + MEDIUM-1 + MEDIUM-2 + MEDIUM-3 + LOW-3
**Input briefs:** `audit/current-state-brief.md`, `audit/best-practices-brief.md`, `audit/refactor-pattern-brief.md`, `audit/evaluator-report.md`
**Brief verbatim:** state.restructure_brief (Broad cleanup audit, conservative bias)

## Revision log (v1 → v2 after design-adversary)

- **HIGH-1 + HIGH-2 (both collapse):** Batch 5 (Numba kernel extraction) DEFERRED to a dedicated surfaces-split milestone — would leave surfaces.py at ~1410 LOC (still above 800 flag), closes zero evaluator FAIL items, scout-A §13 explicitly classifies kernels as "already well-organized; don't need urgent extraction". Removing Batch 5 also removes the threading-layer ordering ambiguity entirely.
- **MEDIUM-2:** Dropped `parameter_grid_panel.py → panels/parameter_grid_widget.py` rename. Move as `panels/parameter_grid_panel.py` (name unchanged). Symmetric shims across all 4 panel moves.
- **MEDIUM-3:** Added `+ MOVES.md` to Batch 4 tree diff. Created by anchor-updater on Batch 4's run.
- **MEDIUM-1:** Added Qt-import pre-flight grep requirement to AI-2 row.
- **LOW-3:** Added CONTEXT.md §10 smoke-test command to Batch 4's explicit anchor list.
- **LOW-1, LOW-2, MEDIUM-4:** Now moot (LOW-1 is checked at Phase 3 preflight regardless; LOW-2 + MEDIUM-4 were Batch-5-specific).

---

## 1. Restructure goal

Apply the lowest-risk evaluator-report fixes that close 6 of the 14 FAIL items (LICENSE, CHANGELOG, AGENTS.md, CLAUDE.md, pyproject.toml, framework-adapter subpackage), plus one concrete dark-mode regression caught by the current-state auditor, while staying strictly conservative: NO `src/avcs/` migration (the audit's `[CONTESTED for apps]` note + the README smoke-test command + 11 test files with implicit flat-path imports = too much blast radius for this restructure). NO `app.py` Extract Class (genuine God Object per current-state §4.1 — extraction risks AI-9 re-entrancy guard). NO partial surfaces.py extraction in this restructure (per design-adversary HIGH-1 v2 revision: 401 LOC kernel-only move leaves surfaces.py at ~1410 LOC, still above the 800 flag, closes zero evaluator FAILs; belongs in a dedicated surfaces-split milestone). The two MONOLITH FAIL items (#17: surfaces.py 1811 LOC, app.py 1900 LOC) are fully deferred to follow-up milestones.

Traceability:
- Evaluator FAIL #2 (LICENSE) → Batch 1
- Evaluator FAIL #3 (CHANGELOG) → Batch 1
- Evaluator FAIL #6 (pyproject.toml) → Batch 2
- Evaluator FAIL #7 (AGENTS.md) → Batch 2
- Evaluator FAIL #8 (CLAUDE.md) → Batch 2
- Evaluator FAIL #21 (AGENTS/CLAUDE.md sizing) → Batch 2 (kept under 200 lines per Anthropic 2026)
- Evaluator FAIL #25 (.pytest_cache in .gitignore) → Batch 1
- Current-state §13.4 (parameter_grid_panel BG_GRID_SCENE dark-mode gap, §5.3) → Batch 3
- Evaluator FAIL #24 (framework-adapter subpackage) + current-state §5.2 (panels/ candidates) → Batch 4

Explicitly NOT addressed (with reasons):
- FAIL #4 CODE_OF_CONDUCT.md (solo project; pyOpenSci flags as optional) — deferred
- FAIL #5 CONTRIBUTING.md (solo project) — deferred
- FAIL #11 source package (`avcs/` at root) — deferred (high blast radius; current-state §13.2 notes README smoke-test command + every test import is flat-path; warrants its own restructure with full deprecation cycle)
- FAIL #17 app.py 1900 LOC — deferred (current-state §4.1: genuine God Object with shared mutable state across `_render_current` / `_on_mesh_ready`; Extract risks AI-9)
- FAIL #17 surfaces.py 1811 LOC — DEFERRED (design-adversary v2: a partial 401-LOC kernel extraction in this restructure would leave surfaces.py at ~1410 LOC, still above the 800 flag, while closing zero evaluator FAILs; scout-A §13 explicitly classifies kernels as "already well-organized; don't need urgent extraction"; extraction belongs in a dedicated surfaces-split milestone whose scope is to take surfaces.py < 800 LOC, not a token reduction)
- FAIL #17 tests/test_styles_palette.py 1261 LOC — deferred (test files are not subject to the 800-LOC norm in scout-B; intentional comprehensive coverage)
- FAIL #19 docs/ directory — deferred (single-developer project; CONTEXT.md + README cover doc needs today)
- FAIL #20 examples/ directory — deferred (defer to a milestone that intends to add runnable demos)

---

## 2. Tree diff (old → new)

Notation: `+` = new file, `-` = deleted file (none in this restructure — shims preserve all old paths), `~` = modified file, `→` = moved file (with shim left at old path).

```
algebraic-variety-cross-section/
+ AGENTS.md                                   [Batch 2; pointer to CONTEXT.md]
+ CHANGELOG.md                                [Batch 1; Keep-a-Changelog header + initial entry]
+ CLAUDE.md → AGENTS.md                       [Batch 2; symlink per HumanLayer + agents.md spec]
+ LICENSE                                     [Batch 1; MIT — LGPL-stack compatible]
+ pyproject.toml                              [Batch 2; minimal [project] metadata, no entry-points]
+ MOVES.md                                    [Batch 4; created by anchor-updater on Batch 4's run;
                                               cross-restructure rosetta stone per scout-C §7]
+ panels/                                     [Batch 4; new subpackage]
+   __init__.py                                [shim hub: __getattr__ routes to panels.*]
+   appearance.py         (← appearance_panel.py)
+   parameter_grid_panel.py
                           (← parameter_grid_panel.py — name unchanged per v2 MEDIUM-2;
                            symmetric with other 3 panel moves)
+   parameters.py         (← parameters_panel.py)
+   view.py               (← view_panel.py)

~ .gitignore                                  [Batch 1; add .pytest_cache/]
~ CONTEXT.md                                  [Batch 1: fix stale §12; Batch 4: update §4 panel paths
                                               AND §10 smoke-test invocation (per v2 LOW-3)]
~ README.md                                   [Batch 1: fix stale LOC figures;
                                               Batch 4: update "Project structure" + smoke-test command + "Extending the app" paths]
~ tests/test_styles_palette.py                [Batch 3; add parameter_grid_panel.py to inline-style guard tuple]

(SHIMS LEFT AT OLD PATHS — these files keep old import paths working with DeprecationWarning):
~ appearance_panel.py                         [Batch 4 shim → panels.appearance]
~ parameter_grid_panel.py                     [Batch 4 shim → panels.parameter_grid_panel]
~ parameters_panel.py                         [Batch 4 shim → panels.parameters]
~ view_panel.py                               [Batch 4 shim → panels.view]
```

**Unchanged (load-bearing, intentionally left alone):**
- `app.py` — God Object per current-state §4.1; Extract Class deferred
- `surfaces.py` — deferred per v2 HIGH-1 (kernel extraction belongs in dedicated surfaces-split milestone)
- `icons.py`, `render_worker.py`, `styles.py`, `parameter_grid.py`, `ui_helpers.py` — well-isolated, no restructure value
- `tests/__init__.py`, `pytest.ini` — flat test layout preserved (mirroring panel moves into `tests/panels/` is deferred; the test imports work via the panel shims for one milestone)
- `tests/test_numba_field_kernels.py` — unchanged (Batch 5 deferred per v2)
- `requirements.txt` — already includes libcst/pydeps/coverage from prior commit
- All `.claude/`, `.github/`, `plans/` — OUT OF SCOPE per user brief

---

## 3. Symbol map

See `symbol-map.json` for the machine-readable form consumed by `scripts/repository-architect/rewrite-imports.py` in Phase 4.

Human-readable summary (only modules with import-graph impact):

### Batch 4 — panels/ subpackage

| Old path | New path | Kind |
|---|---|---|
| `appearance_panel` (module) | `panels.appearance` | module |
| `parameter_grid_panel` (module) | `panels.parameter_grid_panel` | module |
| `parameters_panel` (module) | `panels.parameters` | module |
| `view_panel` (module) | `panels.view` | module |

Symbols moved (re-exported from new locations):
- `appearance_panel.AppearancePanel` → `panels.appearance.AppearancePanel`
- `parameter_grid_panel.ParameterGridPanel` → `panels.parameter_grid_panel.ParameterGridPanel`
- `parameter_grid_panel._DraggableDot` → `panels.parameter_grid_panel._DraggableDot` (private; not in shim)
- `parameters_panel.ParametersPanel` → `panels.parameters.ParametersPanel`
- `view_panel.ViewPanel` → `panels.view.ViewPanel`

Per v2 MEDIUM-2: all 4 panel moves are directory-only — name unchanged. Symmetric shim shape.

Batch 5 (Numba kernel extraction) DEFERRED per v2 HIGH-1. See Section 1 "Explicitly NOT addressed".

Batches 1, 2, 3 have NO file moves and NO symbol relocations — they are additions / in-place fixes only. Their symbol-map.json entries are empty arrays.

---

## 4. Delta size table

| Batch | Operation | New files (LOC) | Modified files (LOC delta) | Shim LOC | Total LOC delta |
|---|---|---|---|---|---|
| 1 | Zero-risk additions + stale-fact fixes | LICENSE (~20), CHANGELOG.md (~30) | .gitignore +1, CONTEXT.md ±20 (fix §12), README.md ±30 (fix LOC figures) | 0 | +~100 |
| 2 | AI-navigability infrastructure | AGENTS.md (~120), CLAUDE.md (symlink, 0), pyproject.toml (~40) | 0 | 0 | +~160 |
| 3 | Dark-mode regression fix | 0 | parameter_grid_panel.py ±10 (replace BG_GRID_SCENE hardcode with QSS role), tests/test_styles_palette.py +5 (add file to guard tuple), styles.py +0 to +15 (preflight check whether `_render_stylesheet` already contains a BG_GRID_SCENE-equivalent role selector; if not, +10–15 for two new role blocks per v2 LOW-1) | 0 | +~10–25 net |
| 4 | Introduce `panels/` subpackage | MOVES.md (~30), panels/__init__.py (~50 shim), panels/appearance.py (= moved 738 LOC), panels/parameter_grid_panel.py (= moved 713 LOC), panels/parameters.py (= moved 368 LOC), panels/view.py (= moved 503 LOC), tests/test_panels_shims.py (~40 LOC, 4 tests) | app.py imports +0 (LibCST rewrite), CONTEXT.md ±15 (panel path refs + §10 smoke-test per v2 LOW-3), README.md ±15 (project-structure + smoke-test + extending sections) | 4 shim files (~10 LOC each = 40 LOC) | +~160 LOC net (the 2322 LOC of moved files is conserved; only shims + __init__ + MOVES.md + shim-tests add LOC) |

**Net delta:** ~+330 LOC of new files + shims + new metadata; ~2322 LOC of source code MOVED (preserving git blame via `git mv`). Total commits: ~9 (one Fowler op per commit across 4 batches).

---

## 5. Shim plan

Shims use the canonical `__getattr__` pattern from `.claude/references/repository-architect/shim-templates.md` (Template 1 + Template 2). NEVER star-imports.

### Batch 4 shims (4 module-level files at old paths)

Per moved panel file, the OLD path becomes a Template-2 whole-module shim:

```python
# appearance_panel.py — shim, removal milestone: M+1 (next /repository-architect run)

def __getattr__(name: str):
    import warnings
    from panels.appearance import __dict__ as _ns
    if name in _ns:
        warnings.warn(
            f"appearance_panel.{name} is deprecated; "
            f"import from panels.appearance instead.",
            DeprecationWarning, stacklevel=2)
        return _ns[name]
    raise AttributeError(
        f"module 'appearance_panel' has no attribute {name!r}")
```

Identical shape for `parameter_grid_panel.py` (→ `panels.parameter_grid_panel`), `parameters_panel.py` (→ `panels.parameters`), `view_panel.py` (→ `panels.view`). All four shims forward to same-named-module-under-panels per v2 MEDIUM-2.

**Removal milestone:** the next `/repository-architect` run (probably `restructure-app-py-extract-2026q3-r1` or similar). Removal commit subject: `refactor: remove <old-path>.py shim (deprecated since <Batch-4-sha>)`.

**Test recipe per shim** (added in Batch 4, NOT Batch 5):
```python
# tests/test_panels_shims.py — Qt-free; verifies DeprecationWarning emission
import warnings


def test_appearance_panel_shim_emits_deprecation():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from appearance_panel import AppearancePanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "panels.appearance" in str(w.message)
        for w in caught
    )

# ... 3 more identical-shape tests for view_panel, parameters_panel, parameter_grid_panel
```

Note: this 1 test file (4 tests) is added INSIDE Batch 4 because the shim IS the batch's protection mechanism — `scripts/repository-architect/validate-shims.py` would catch a broken shim, but the in-test verification gives the parity-verifier additional ground truth. This is the ONE exception to scout-C §10.1 ("don't add features in the same PR as the refactor"); the shim-tests ARE the refactor's safety net, not a new feature.

### Batch 5 — DEFERRED

Numba kernel extraction (`surfaces.py` → `_field_kernels.py`) is DEFERRED per v2 HIGH-1 / HIGH-2 resolution. See Section 1 "Explicitly NOT addressed".

### Batches 1, 2, 3 — no shims

Zero file moves means zero shims. The dark-mode fix in Batch 3 is an in-place behavior fix (replacing one stylesheet rule with another); old behavior was buggy, so no backward-compat needed.

---

## 6. AI-invariant impact (per AI-1..AI-15)

| Invariant | Touched? | Per-batch detail | Resolution |
|---|---|---|---|
| **AI-1** GUI = PySide6 + PyVista + pyvistaqt | NO | — | No renderer or stack swap |
| **AI-2** Tests are Qt-free | YES (Batch 4) | The shim tests in `tests/test_panels_shims.py` import via the OLD path. The old path's shim re-exports symbols including `AppearancePanel` (a QWidget subclass). Importing the *class* does NOT construct it — no QApplication needed. Test asserts the warning and discards the class. **Pre-flight confirmation required (per v2 MEDIUM-1):** grep panel module top-levels for `QApplication`, `QWidget(`, `QDialog(`, or `QCoreApplication.instance()` construction at module scope; expected: zero hits. The implementer agent runs this check before adding the shim tests. | Preserved. Shim test is import-only, never instantiates the class. Pre-flight grep documented. |
| **AI-3** Off-screen via `pv.OFF_SCREEN=True` | NO | — | No render verification in this restructure |
| **AI-4** `clip_scalar` not `clip_box` | NO | — | `view_panel.clip_to_domain` body is unchanged; only the module path moves |
| **AI-5** `clip_scalar(scalars=...)` kwarg | NO | — | Same as AI-4 |
| **AI-6** Implicit pipeline → marching cubes; parametric → grid; never mix | NO (Batch 5 deferred per v2) | — | Unchanged. |
| **AI-7** Hanson normals (`cell_normals=True, ...`) | NO | — | `_grid_to_polydata` stays in `surfaces.py`; not touched by kernel extraction |
| **AI-8** `Surface`/`ParamSpec` dataclasses + `VARIETIES` registry | NO (Batch 5 deferred per v2) | The dataclasses + VARIETIES + tooltips remain in `surfaces.py`. README "Extending the app" §1 says "Write a generator function in `surfaces.py`" — still true. | Unchanged. |
| **AI-9** Re-entrancy guard `self._computing` | NO | — | `app.py` is not modified except for import paths in Batch 4 (LibCST rewrites only — no logic changes) |
| **AI-10** Raw mesh cached; domain change skips regeneration | NO | — | `view_panel.clip_to_domain` body unchanged |
| **AI-11** Fully-qualified Qt enums | YES (Batch 4) | Any NEW code (shim files, `panels/__init__.py`) must use fully-qualified Qt enums where applicable. The shim files contain no Qt code. `panels/__init__.py` is shim-only. | Preserved by construction. |
| **AI-12** WCAG AA contrast on visible text | YES (Batch 3 PROACTIVE FIX) | Current `parameter_grid_panel.py:L232` does `self._view.setStyleSheet(f"background: {BG_GRID_SCENE}...")` where `BG_GRID_SCENE` is a PALETTE_LIGHT alias. In dark mode, the grid background stays light — a real AI-12 adjacent regression. | Batch 3 explicitly FIXES this BEFORE Batch 4 moves the file to `panels/`, so the panels-grouping doesn't carry the bug forward. |
| **AI-13** 6-digit hex for PyVista colors | NO | — | No color changes |
| **AI-14** Generators return `pv.PolyData` or raise `ValueError` | NO | — | Generator function signatures and bodies untouched |
| **AI-15** Math honesty: tooltips + sources | NO (Batch 5 deferred per v2) | — | Unchanged. |

**Summary:** No invariant LIFT requested. AI-12 gets a PROACTIVE FIX (Batch 3) for a real regression discovered by the audit. All other invariants are preserved by construction.

---

## 7. Cross-suite test gaps (per scout-C §8 — 10 categories)

For each category, judge whether this restructure introduces or makes more visible the gap. Test-suggester (Phase 5) will propose tests for the GAPs flagged YES.

| # | Category | YES/NO | Why |
|---|---|---|---|
| 1 | conftest.py scope drift | NO | AVC has no conftest.py. The flat `tests/` directory is preserved (panel test files are NOT moved into `tests/panels/` in this restructure). |
| 2 | Implicit fixture sharing | NO | No conftest, no shared fixtures. |
| 3 | Import-time side effects | NO (Batch 5 deferred per v2) | — |
| 4 | Plugin discovery | NO | No pytest plugins in use. |
| 5 | Seam tests between newly-split modules | NO (Batch 5 deferred per v2) | — |
| 6 | GUI / Qt event-loop integration | NO | AI-2 blocks pytest-qt; no integration tests today, none added. Panel files moved but their classes are unchanged. |
| 7 | VTK pipeline wiring | NO | No VTK code is touched. |
| 8 | Settings persistence boundary | NO | QSettings code in `app.py` is unchanged. Key namespace unchanged. |
| 9 | Star-import shadow | NO | Audit confirmed zero star-imports in production code (evaluator c16 PASS). |
| 10 | Cyclic-import-under-entrypoint smoke | YES (Batch 4) | `python -c "import app"` must succeed. New `panels/` subpackage + shim files = new import-path graph. A smoke-test that does `python -c "import app; print('OK')"` after each batch would catch a cycle introduced by shim recursion or by `panels/__init__.py` importing something that imports back to a shim. |

**Test-suggester deliverables (Phase 5):** seam test for category 10 only (the cyclic-import smoke). Categories 3 + 5 are no longer in scope (Batch 5 deferred). The test-suggester agent will draft the category-10 test; the user decides whether to write it in a follow-up milestone.

---

## 8. Rollback plan

### Tier 1 — whole-restructure revert (preferred)

**Pre-condition:** the entire restructure is a contiguous chain of small commits on `main`, no feature work interleaved. This pipeline enforces this via Phase 4's "one Fowler op per commit" rule.

**Command** (will be re-stated in `preflight/ROLLBACK.md` with the actual baseline SHA + tag):
```bash
git revert --no-commit refactor-baseline-restructure-full-audit-2026q2-r1..HEAD
git commit -m "revert: roll back restructure-full-audit-2026q2-r1"
```

Or via tag (easier to remember weeks later, created by Phase 3 Step 4):
```bash
git revert --no-commit refactor-baseline-restructure-full-audit-2026q2-r1..HEAD
git commit -m "revert: roll back restructure-full-audit-2026q2-r1 (via tag)"
```

### Tier 2 — branch-by-abstraction toggle

Not applicable. This is a Python source restructure, not a runtime swap.

### Tier 3 — per-batch partial rollback

If a specific batch misbehaves but earlier batches are stable, revert from that batch's first commit forward. Use the **tag-based form** (preferred per v2 LOW-2 — avoids fragile grep on commit subjects):

```bash
# Phase 4 implementer creates a per-batch end-of-batch tag (e.g. refactor-batch3-end)
# after each batch's parity-verifier returns PASS.
git revert --no-commit refactor-batch3-end..HEAD
git commit -m "revert: partial rollback of Batch 4 (panels/ subpackage)"
```

The implementer MUST create these tags per batch; if a tag is missing, fall back to the baseline tag for Tier-1 whole-restructure revert.

### What rollback does NOT restore

- MOVES.md entries (manual revert via `git checkout refactor-baseline-restructure-full-audit-2026q2-r1 -- MOVES.md`).
- CLAUDE.md / CONTEXT.md / README.md edits (manual revert per file).
- Agent-memory CORRECTION blocks (manual revert via `git checkout refactor-baseline-restructure-full-audit-2026q2-r1 -- .claude/agent-memory/`).

### Rollback rehearsal

Per scout-C §10.8 ("we don't need a rollback plan; we have git"): the Tier 1 command will be tested in a scratch worktree BEFORE Phase 4 begins. The test result (PASS/FAIL) is recorded in `preflight/ROLLBACK.md`. If Tier 1 rehearsal FAILS, the pipeline must NOT proceed past GATE 3.

---

## Batch sequencing (low-risk-first, per design-adversary axis 10)

| Batch | Risk | Operations | Dependencies | Estimated time |
|---|---|---|---|---|
| 1 | TRIVIAL | Add LICENSE + CHANGELOG.md + .gitignore line + CONTEXT.md/README.md stale-fact edits | None | 5 min |
| 2 | LOW | Add AGENTS.md + CLAUDE.md symlink + pyproject.toml | Batch 1 done | 10 min |
| 3 | LOW | Fix parameter_grid_panel.py L232 BG_GRID_SCENE hardcoding + add to inline-style guard tuple | Batch 2 done (so test_styles_palette tuple update lands cleanly) | 15 min |
| 4 | MEDIUM | Introduce panels/ subpackage: 4× git mv (same-name) + panels/__init__.py + 4 shim files + MOVES.md creation + LibCST import rewrites in app.py + README/CONTEXT (incl. §10 smoke) updates + tests/test_panels_shims.py | Batch 3 done (so the moved parameter_grid_panel.py is clean BEFORE the move) | 45 min |

**Total estimated wall-clock:** ~75 min (1.25 h, down from ~105 min in v1 after Batch 5 deferral). Each batch is independently revertable via Tier-3 rollback (tag-based per v2 LOW-2).

**Per-batch implementer agent dispatch:** one `repository-architect-implementer` invocation per batch. Each dispatches parity-verifier + anchor-updater per phase-4-execute.md. Implementer creates an end-of-batch tag (`refactor-batch{N}-end`) immediately after each batch's parity-verifier returns PASS.

**Per-batch user gate:** GATE 4 fires only on parity-verifier FAIL (not pre-commit). Each batch must have its parity-verifier return PASS before the next batch dispatches.

---

## Effort honesty (per design-adversary axis 11)

- This PLAN.md (v2) proposes 4 batches; ~9 total commits; ~+330 LOC additions + ~2322 LOC moved.
- The total LOC moved seems large because the panel files together are 2322 LOC and they're being shifted as a unit. The CODE inside them is not edited (the implementer agent's rule: never bundle content edits with moves).
- The hardest batch is Batch 4 (4 file moves + 4 shims + LibCST import rewrites in `app.py` + 3 doc updates + 1 new test file + MOVES.md creation). 45 min is optimistic if the LibCST rewrite reveals edge cases; could stretch to 90 min.
- Batches 1-3 are ~30 min combined; defensibly proposed even if Batch 4 is deferred at GATE 3.
- Total restructure cost is ~1.25 h of agent wall-clock + the user's gate-approval time. This is appropriate for a quarter-cadence restructure.

---

## Approval gates pending in this pipeline

- GATE 2 (after design-adversary): user reviews this PLAN.md + the adversary's findings
- GATE 3 (after dry-run validator): user reviews baseline + dry-run verdict + rollback plan
- GATE 4 (per batch, conditional): user reviews parity-verifier FAIL and approves rollback
- GATE 5 (after execution-critic): user reviews critique and authorizes rectify

**This PLAN.md is the input to GATE 2. After the design-adversary critiques it, the orchestrator will surface GATE 2 to the user.**
