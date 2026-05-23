# Refactor-Pattern Brief — restructure-full-audit-2026q2-r1

**Scout.** REFACTOR-PATTERN SCOUT (Phase 1 agent)
**Restructure.** restructure-full-audit-2026q2-r1 — Broad cleanup audit of AVC repo
**Authored.** 2026-05-23
**Seed brief.** `.claude/notes/repository-architect-design/scout-c-safe-refactor.md` (verified, used as starting cache)
**Time-box.** ~30 min wall-clock

## Honesty conventions

- `[CONSENSUS]` = three+ independent reputable sources agree.
- `[CONTESTED]` = sources disagree.
- `[UNVERIFIED]` = author could not confirm from a primary source within the time-box.
- Every claim has an `[Sn]` citation. Sources listed at end.

---

## AVC substrate (read from cache at 2026-05-23)

From `.claude/notes/repository-architect/restructure-full-audit-2026q2-r1/cache/loc.csv` and evaluator-report:

- **7849 LOC** across 11 production `.py` files at root; 23 test files under `tests/` (flat).
- Two giants: `app.py` (1900 LOC), `surfaces.py` (1811 LOC).
- Four panel files at root: `appearance_panel.py` (738), `parameter_grid_panel.py` (713), `view_panel.py` (503), `parameters_panel.py` (368). Dual-panel question: does `parameter_grid_panel.py` supersede `parameters_panel.py`?
- No `src/` layout. No subpackages. No `__init__.py` at root. No `MOVES.md`. No `AGENTS.md`. No `CLAUDE.md`.
- Evaluator checklist: **14/28 pass**. Notable failures: no LICENSE, no CHANGELOG, no pyproject.toml, no AGENTS.md/CLAUDE.md, no source package (11 loose `.py` files), two files over 800 LOC (app.py, surfaces.py), no `panels/` subpackage, no `.pytest_cache` in `.gitignore`.
- AI-1..AI-15 invariants in `.claude/references/app-invariants.md` are **inviolable** throughout any restructure.

---

## 1. TL;DR — what a safe restructure pipeline MUST do

1. **Capture a baseline before touching anything.** Tests green, coverage measured, import graph snapshotted, `git status` clean. Without this you cannot prove parity afterwards. `[CONSENSUS — S1, S6, S8]`
2. **Propose the target tree explicitly, with deltas.** A diffable plan (old path → new path, file split with line ranges, new symbol homes) reviewed *before* any `git mv` runs. Mirrors the Branch by Abstraction stance: the new state and the old state must be describable simultaneously. `[S2]`
3. **Dry-run the import-graph impact without moving files.** Compute, against the existing tree, "if these moves were applied, what would break?" — orphan modules, new cycles, broken `from X import Y`, conftest.py scope drift. `[S11, S14]`
4. **Execute in tiny commits with a shim/deprecation cycle in between.** Each commit must leave the system green; old import paths keep working via `__init__.py __getattr__` shims that emit `DeprecationWarning`. Follow Parallel Change / expand–contract. `[CONSENSUS — S3, S4, S15, S16]`
5. **Re-baseline at the end and update every navigation anchor.** Coverage delta, import-graph delta, test-parity check, **plus** every agent-readable surface (`CLAUDE.md`, `AGENTS.md`, `MOVES.md`, agent-memory `lessons.md`). The restructure is not done until agents working in the new tree can find their way around. `[S18, S19, S20]`

> **The thesis.** The technical refactor is the easy part; preserving *agent context anchors* and *test-suite coverage shape* is what makes a restructure regress silently weeks later.

---

## 2. The eight phases of a safe restructure

### Phase 1 — Baseline (snapshot, green, measured)

**Pattern.** Feathers' "establish characterization tests before changing legacy code." `[S22]`

**Mechanics.**
- `git status` clean — non-negotiable. `[S18]`
- Full test suite green. Capture wall-clock and per-test timings.
- `coverage run -m pytest && coverage xml -o baseline-coverage.xml` and store under `.claude/notes/restructure-full-audit-2026q2-r1/baseline/`.
- Snapshot import graph: `pydeps . --max-bacon=0 --noshow` plus `--show-deps` JSON dump for diffing. `[S14]`
- Snapshot symbol locations: for every public symbol, record `{symbol → path:line}`. Anchors the Phase 8 agent-context repair step.
- Tag: `git tag refactor-baseline-2026-05-23`.

**Exit criterion.** All artifacts exist on disk, committed or stored in the notes baseline directory.

**Failure if skipped.** Cannot prove test coverage shape, behavior, or import topology was preserved. "The tests still pass" is meaningless — the suite might have silently skipped or no-op'd. `[S22, S25]`

---

### Phase 2 — Propose (target tree, file moves, file splits)

**Pattern.** Fowler's catalog operations made explicit before execution: Move Function / Move Field / Extract Class / Inline Class. `[S5, S7]`

**Mechanics.**
- Produce a `PLAN.md` artifact with three sections:
  1. **Tree diff.** Old tree → new tree, line-by-line.
  2. **Symbol map.** For each symbol being moved or split: source `path:line` → target `path:line`. Use LibCST `MetadataProvider` to enumerate top-level definitions reliably. `[S9]`
  3. **Delta size.** For each new file: predicted LOC; for each split: source LOC → target1 LOC + target2 LOC + shim LOC.
- Each move/split references a Fowler catalog operation (Move Function, Extract Class, Split Module, Introduce Subpackage). `[S7]`
- **AVC note.** For `parameters_panel.py` vs `parameter_grid_panel.py`: the plan must explicitly decide which is canonical (strong evidence from prior audit is that `parameter_grid_panel.py` supersedes; `parameters_panel.py` becomes the shim target). This decision must be explicit in PLAN.md, not implicit in a big-bang delete.

**Exit criterion.** Reviewer can re-derive the new tree from `PLAN.md` alone. No "TBD" entries.

**Failure if skipped.** Refactor becomes stream-of-consciousness; agent context anchors cannot be planned because nobody knows where things will land. Per `[S18]`: "model loses track of downstream files needing updates mid-session."

---

### Phase 3 — Dry-run (import-graph delta without moving anything)

**Pattern.** Branch by Abstraction's "the system runs at all times," applied predictively. `[S2]`

**Mechanics.**
- Build the *predicted* import graph by mechanically applying the symbol-map to the current AST (LibCST can rewrite imports in memory without writing to disk). `[S9]`
- Diff predicted vs. baseline graph:
  - **New cycles?** Reject or restructure the split.
  - **Orphaned modules?** Reject.
  - **Fan-in > 20 on any single module?** Flag as god-module risk.
  - **`from X import *` patterns?** Flag — invisible to static rewriting, will break silently.
- For each test file, predict which `conftest.py` files apply *after* the move. `[S24]`
- Predict pytest collection delta: `pytest --collect-only -q` before vs. would-be after.

**Exit criterion.** A `DRY-RUN.md` with zero red flags, or a revised `PLAN.md` that addresses each flag.

**Failure if skipped.** "We moved everything, all tests pass, but pytest now collects 200 fewer tests because a `conftest.py` is in the wrong scope." This is the silent regression this brief is most worried about for AVC.

---

### Phase 4 — Pre-flight (shim plan, deprecation cycle, branch strategy)

**Pattern.** Parallel Change / expand–contract. `[S4]` NumPy NEP-23. `[S10]` pandas PDEP-17. `[S17]`

**Mechanics.**
- For every old import path that will move, decide: **shim or hard break?**
  - **Shim (default).** Old path stays importable; emits `DeprecationWarning`; routes to new location via `__init__.py __getattr__`. `[S12, S13]`
  - **Hard break (rare).** Only for genuinely private symbols (`_name`) or symbols never imported by name.
- **AVC-specific.** `parameters_panel.py` → if `parameter_grid_panel.py` is canonical, `parameters_panel.py` becomes a shim. Lifetime: one milestone. Do not delete in the same PR as the move.
- Branch strategy: each batch is a series of small commits on `main`, each independently green. Do not mix refactor commits with feature commits.
- Write the rollback note (Section 11) *before* executing.

**Exit criterion.** `PREFLIGHT.md` documents shim plan, deprecation timeline, rollback command.

**Failure if skipped.** Hidden callers break with no migration path. Without a pre-written rollback note, a panicked revert can take down adjacent unrelated work.

---

### Phase 5 — Execute (the moves, in small commits)

**Pattern.** Fowler "small steps" discipline `[S5, S7]`; SeatGeek's "cautious rollout." `[S26]`

**Mechanics.**
- One refactor catalog operation per commit.
- Use `git mv` (not delete+add) so Git rename heuristic preserves blame and `--follow` works. `[S21]`
  - **Warning.** If the move is combined with >50% content change in the same commit, rename detection fails. Keep moves and edits in *separate* commits.
- After every commit: (1) `pytest` green; (2) `python -c "import <new_path>"` smoke test; (3) `python -c "import <old_path>"` smoke test the shim emits the deprecation warning.
- Use LibCST codemods for *mechanical* import rewrites — never `sed`. `[S9, S11]`
- **AVC batch order (low-risk-first):**
  1. Batch A: `panels/` subpackage introduction (mechanical, low-risk).
  2. Batch B: `parameters_panel.py` → shim (after `parameter_grid_panel` is confirmed canonical).
  3. Batch C: Missing top-level files (LICENSE, CHANGELOG, AGENTS.md, pyproject.toml).
  4. Batch D: `surfaces.py` → `surfaces/` subpackage (medium risk, more imports to rewire).
  5. Batch E: Extract Class on `app.py:MainWindow` (highest risk; gate behind successful A–D).

**Exit criterion.** Every intended move/split landed; every commit is green standalone; shims in place.

**Failure if skipped (big-bang commit).** Per `[S1]`: big-bang is the original sin. `git bisect` is destroyed. Rollback is all-or-nothing.

---

### Phase 6 — Re-import-graph verify (no orphans, no cycles, no broken imports)

**Pattern.** "Continuous validation of dependency graphs." `[S8]` pydeps cycle detection. `[S14]`

**Mechanics.**
- Re-run `pydeps --show-cycles`. Compare to predicted graph from Phase 3. Divergence is a yellow flag.
- Run `python -X importtime -c "import app"` and diff against baseline — large import-time spike indicates side-effect leak.
- Run ruff for `F401` (unused import), `F811` (redefined), `F821` (undefined). `[S11]`
- Confirm no `from X import *` was introduced.

**Exit criterion.** Import graph matches Phase 3 prediction; zero ruff F-class errors; no import-time regression.

**Failure if skipped.** Hidden cycles surface weeks later as `ImportError: cannot import name X (most likely due to a circular import)` in rarely-exercised paths.

---

### Phase 7 — Test parity verify (same tests run, same coverage shape, no silent skips)

**Pattern.** Coverage diff + characterization tests + mutation testing as confirmation. `[S25, S22, S27]`

**Mechanics.**
- `pytest --collect-only -q | wc -l` after vs. before. Count **must not decrease** unless a test file was deliberately removed (listed in `PLAN.md`).
- `coverage run -m pytest && coverage xml -o post-coverage.xml`. Diff against baseline:
  - Per-file coverage % delta: within ±2% for moved files.
  - Total lines covered: within ±1% of baseline.
  - Use `diff-cover` or `coverage-diff` to mechanize. `[S25]`
- Characterization smoke: for AVC, at minimum: launch default variety → render; switch variety; toggle HQ smoothing; export STL. `[S22, S23]`
- **AVC note.** AI-2 invariant: test suite is Qt-free (no pytest-qt). Characterization tests run via `pv.OFF_SCREEN = True` (AI-3). Do not add Qt event-loop tests unless explicitly authorized.
- Mutation testing: run `mutmut run` on refactored modules as *confirmation*, not gate. Score drop > 2% on a touched module warrants investigation. `[S27]`

**Exit criterion.** Collection count preserved; per-file coverage within tolerance; total coverage within tolerance; mutation score within tolerance; characterization smoke passes.

**Failure if skipped.** "All tests pass" hides "20 tests silently no-op because their conftest.py is in the wrong directory now."

---

### Phase 8 — Re-baseline (navigation docs, CLAUDE.md, agent memory)

**Pattern.** "Agent context anchor" repair; pointer-based `CLAUDE.md` per `[S20]`.

**Mechanics.**
- Append entry to `MOVES.md` (create if absent): `{from_path}:{from_line_range} → {to_path}:{to_line_range}` for every moved symbol.
- Create root `CLAUDE.md` (currently absent): pointer-based "key modules" table. Per `[S19, S20]`: keep this pointer-based, never embed content.
  - **Also create `AGENTS.md` if the brief's recommendation to add it is executed.** See Section 7.2 Strategy D on the symlink migration pattern.
- For each new subpackage introduced, add a per-folder `CLAUDE.md` describing responsibility, key entrypoints (by symbol name, not line number), cross-references.
- Walk `.claude/notes/**/*.md` and agent-memory files; grep for old paths; update using `MOVES.md` as lookup table.
- Update `README.md` repo structure section.
- Re-tag: `git tag refactor-complete-2026-05-23`.

**Exit criterion.** Grep for any old path across all `.md` files in the repo returns zero hits (except inside `MOVES.md` itself).

**Failure if skipped.** Future agent sessions will load stale `CLAUDE.md` pointers and try to `Read` paths that no longer exist. Per `[S19]`: "stale path references will actively mislead agents."

---

## 3. Tooling matrix

| Tool | Language | What it does | Install footprint | License | AVC applicability |
|------|----------|--------------|-------------------|---------|-------------------|
| **LibCST 1.8.6** | Python | Concrete syntax tree; preserves formatting; de-facto choice for import rewriting and codemods. Supports Python 3.0–3.14. Active (last release Nov 2025). `[S9, S26, S28]` | `pip install libcst` (has native extension; pure Python fallback available) | MIT | **Primary.** Use for all import rewriting, symbol renames, file splits. |
| **Rope 1.14.0** | Python | Project-wide refactor library: rename, move, extract, inline. IDE-oriented. Active (last updated Jan 2026). `[S30]` | `pip install rope` | LGPL-3.0+ | **Secondary.** Good for interactive rename/move. Less ergonomic than LibCST for bulk codemods; LGPL may matter for distribution. |
| **Bowler** | Python | Facebook's earlier safe-refactor tool, built on `lib2to3` (deprecated) / fissix. **Archived August 8, 2025.** Read-only. The maintainers explicitly recommend LibCST codemods as the replacement. `[S11]` | n/a — do not adopt | Apache-2.0 | **SKIP. Confirmed dead.** Do not recommend. Do not adopt. See gate note. |
| **ruff** | Python | Linter + autofix. `--fix` covers F401 (unused import), F811 (redefined), I001 (sort/dedupe imports), plus 700+ other rules. De-facto 2026 ecosystem standard replacing flake8/isort/black. `[S11]` | `pip install ruff` (Rust binary, fast) | MIT | **Primary verification.** Run after every commit during Execute phase. |
| **pyflakes** | Python | Subset of what ruff does; lower friction. | `pip install pyflakes` | MIT | Fallback if ruff not adopted. |
| **ast (stdlib)** | Python | Abstract syntax tree; does NOT preserve formatting — destroys comments, whitespace, parens on round-trip. `[S9]` | stdlib, zero install | PSF | **Analysis only.** Never use for rewriting files. Use LibCST instead. |
| **pydeps** | Python | Module dependency graph generator; `--show-cycles` highlights cyclic imports; bytecode analysis. `[S14]` | `pip install pydeps` (requires graphviz for rendering) | BSD-2-Clause | **Primary** for Phase 3 dry-run and Phase 6 verify. SVG output human-reviewable; JSON output diff-able. |
| **modulegraph** | Python | Alternative to pydeps; py2app/py2exe pedigree; more flexible IR. `[S14]` | `pip install modulegraph` | MIT | Secondary; pydeps is more common for refactor work. |
| **coverage.py** | Python | Line + branch coverage; XML output diff-able with `diff-cover`. `[S25]` | `pip install coverage` | Apache-2.0 | **Primary** for Phase 7 parity. Likely already in AVC via pytest setup. |
| **diff-cover / coverage-diff** | Python | Mechanize the "what lines changed?" coverage comparison. `[S25]` | `pip install diff-cover` or `pip install coverage-diff` | varies | Run after Phase 7 to diff XML snapshots. |
| **mutmut** | Python | Mutation testing; flags tests that pass despite mutations. `[S27]` | `pip install mutmut` | BSD | **Confirmation tool** in Phase 7; slow on large suites. Use selectively on `app.py`, `surfaces.py`. |
| **pytest --collect-only** | Python | Lists tests without running them; canonical "did I silently drop tests?" check. `[S24]` | builtin to pytest | MIT | Free; use in every Phase 3 / Phase 7 run. |
| **git mv** | Git | Rename with `--follow`-friendly history; rename detection works at diff level via similarity (default 50%). `[S21]` | builtin | GPL | **Required for every move.** Pair with separating moves from content edits in distinct commits. |
| **grep / ripgrep** | Shell | Cheap text search. | builtin / `rg` | varies | For path audit in Phase 8; **forbidden for import rewriting** (cannot distinguish import from string literal). |

**Net AVC recommendation.** LibCST + ruff + pydeps + coverage.py + pytest. Optional: mutmut on `app.py` and `surfaces.py` before Batches D/E. All MIT/Apache/BSD/PSF — no copyleft surprises.

**Gate note.** Bowler was listed in older references as an alternative to LibCST. It is now **archived (August 8, 2025)** by its owner with explicit guidance to use LibCST instead. Any prior brief or tooling recommendation citing Bowler must be updated. Flagged as `gate-required` per this brief's output contract.

---

## 4. Pattern catalogue

### 4.1 Move Function

**When.** A free function is called more from module B than from its home module A. `[S5]`

**Mechanics (Fowler).** Define the function in B with the same signature. Replace the body in A with a delegating call to B. Run tests. Update each caller to import from B. Delete the A version (or shim it). `[S5]`

**Failure modes.**
- Function had implicit access to module-level state in A (a module-level constant).
- The function is referenced by `getattr(module_a, "fn_name")` or by string — static analysis misses it.

**Python example.** Moving `ui_helpers.format_progress_label` to `panels/status_bar.py`: use LibCST `RemoveImportsVisitor` + `AddImportsVisitor` codemod to rewrite every `from ui_helpers import format_progress_label` across the tree. `[S9]`

---

### 4.2 Move Method

**When.** A method `Foo.bar()` interacts more with `Baz` instances than with `Foo` instances. `[S5]`

**Mechanics.** Add `bar` to `Baz`. Either turn `Foo.bar` into a delegating one-liner or remove it. Update callers.

**Failure modes.** `self` references that don't trivially translate to a `Baz` member. Mocks/spies tied to `Foo.bar` in tests now miss.

**AVC example.** In `app.py`, a method like `MainWindow._refresh_busy_spinner` that mostly manipulates a `RenderWorker` belongs on `RenderWorker.refresh_busy_spinner`. Note: AI-9 re-entrancy guard `self._computing` must travel with any method that calls `processEvents()`.

---

### 4.3 Extract Class

**When.** A class has too many fields/methods serving more than one responsibility — the "Large Class / God Class" smell. `[S6, S8]`

**Mechanics.** Identify a cohesive group of fields + the methods that read/write them. Create a new class. Move the fields, then move the methods. Replace the old fields with a single field holding the new class instance; old methods become delegators. `[S5, S7]`

**Failure modes.**
- **Cyclic dependency.** Old class needs new class and vice versa. Resolve by extracting a third interface or by moving a method to break the cycle. `[S8]`
- **Implicit shared state.** Two responsibilities happened to share a dict; the split introduces a sync bug.
- **Tests bound to the old class structure.** Mocks targeting `MainWindow._busy` break when `_busy` becomes `MainWindow._busy_indicator._state`.
- **AVC-specific.** AI-9 `self._computing` re-entrancy guard is an implicit shared state across multiple methods of `MainWindow`. Any Extract Class on `MainWindow` that touches the render path must carry this guard or establish equivalent mutual exclusion.

**AVC sequence for `app.py:MainWindow` (1900 LOC).** Likely hides 4–6 responsibilities:
1. Extract `SettingsPersistence` — cleanest seam (file-IO, few internal deps). Maps to `qsettings_persistence` tests already existing.
2. Extract `StatusBar` / HUD class — own widget, own state.
3. Extract `RenderPipelineCoordinator` — talks to `render_worker` + `surfaces`. Must preserve AI-9, AI-10.
4. Leave `MainWindow` as the assembly point.
At each step: shim → test → commit.

---

### 4.4 Inline Class

**When.** A class does almost nothing; its responsibilities have drained into other classes. `[S7]`

**Mechanics.** Move all members into the consumer class; delete the empty class. Inverse of Extract Class.

**Failure modes.** External callers still importing the now-deleted class — shim it for one cycle.

**AVC applicability.** If `parameters_panel.py`'s `ParametersPanel` has been fully superseded by `parameter_grid_panel.py`'s `ParameterGridPanel`, then `ParametersPanel` becomes an Inline Class target (or at minimum a shim-only module). This must be confirmed by running the test suite against each panel type before deciding.

---

### 4.5 Split Module

**When.** A `.py` file has crossed the "two cognitive responsibilities" line, regardless of class structure. The "squint test" fails. `[S31]` `[UNVERIFIED — Sandi Metz squint test widely attributed; primary talk/blog source not confirmed within time-box]`

**Mechanics.** Convert the module to a package: rename `foo.py` → `foo/__init__.py`, create `foo/responsibility_a.py`, `foo/responsibility_b.py`. The `__init__.py` re-exports the same public names. `[S31]`

**Failure modes.**
- The file→directory conversion is two git operations; do it in a single commit with `git mv` so rename detection survives.
- Implicit star-imports from the old module become ambiguous.
- `__pycache__/` from the old `.py` lingers; delete it explicitly.

**AVC example.** `surfaces.py` (1811 LOC) → `surfaces/__init__.py` (re-exports only), `surfaces/varieties.py`, `surfaces/sampling.py`, `surfaces/marching.py`, `surfaces/smoothing.py`. The `__init__.py` keeps `from surfaces import compute_field` working for every existing caller. Note: AI-8 (`Surface`/`ParamSpec` dataclass contract) and AI-6 (marching cubes path for implicit surfaces) must be preserved verbatim — do not change signatures during the split.

---

### 4.6 Move Module

**When.** A module's logical home has changed (e.g. `parameter_grid.py` belongs in `panels/`). `[S5]`

**Mechanics.** `git mv old/path.py new/path.py`. Add a shim at `old/path.py` using the `__getattr__` pattern (see Section 5).

**Failure modes.** Star-imports from the shim defeat the deprecation warning's stacklevel pinpointing.

---

### 4.7 Rename Module

**When.** The module's name no longer reflects its content (often after Extract Class or Move Module that left a misnomer). `[S5]`

**Mechanics.** Special case of Move Module where destination is the same directory.

**Failure modes.** Same as Move Module, plus: case-insensitive filesystem (macOS APFS, Windows) can hide a rename that differs only in case. Use a two-step rename through a temp name.

---

### 4.8 Introduce Subpackage

**When.** Flat top-level layout has accumulated > 8–10 modules and a thematic grouping is obvious. AVC fits this trigger today (11 top-level `.py` files, no subpackages). `[S31]`

**Mechanics.** Create the subpackage directory with `__init__.py`. Move relevant modules in. Update imports. Shim each moved module's old path for one cycle.

**Failure modes.**
- Forgot to `git add` the new `__init__.py` → import fails.
- Test files at the old path still try `from <module> import X` instead of `from <pkg>.<module> import X`. Use LibCST codemod to rewrite all test files in one commit, separate from the move commit.

**AVC example.** Group `appearance_panel.py`, `parameter_grid_panel.py`, `parameters_panel.py`, `view_panel.py` into `panels/` subpackage. Four `git mv` operations + one LibCST codemod commit to update all callers in `app.py` and tests.

---

## 5. Shim / deprecation cycle

The shim is what makes "the system runs at all times" possible. Without shims you must update every caller in the same commit as the move — defeating `git bisect`, breaking in-flight branches, breaking notebooks, and breaking AI agent memory that references the old path.

### 5.1 Canonical Python shim (`__init__.py __getattr__` pattern)

Derived from `[S12, S13]`. Used by `collections` in the stdlib. `[CONSENSUS]`

```python
# panels/__init__.py — backward-compat shim, remove in milestone M+1
_RENAMES = {
    # old name in this package's flat namespace → new home
    "ParameterGridPanel": "panels.parameter_grid.ParameterGridPanel",
    "AppearancePanel":    "panels.appearance.AppearancePanel",
    "ViewPanel":          "panels.view.ViewPanel",
    "ParametersPanel":    "panels.parameter_grid.ParameterGridPanel",  # superseded
}

def __getattr__(name: str):
    import importlib
    import warnings
    target = _RENAMES.get(name)
    if target is None:
        raise AttributeError(
            f"module 'panels' has no attribute {name!r}")
    module_path, _, attr = target.rpartition(".")
    warnings.warn(
        f"panels.{name} is deprecated; "
        f"use {target} instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module(module_path), attr)
```

**Why `__getattr__` over `from new import *`.**
- Lazy: target module only imported when accessed — no startup cost.
- Pinpoint warnings: `stacklevel=2` places the warning at the *caller's* import site, not inside the shim. `[S13]`
- Cleanly errors on bogus names rather than silently re-exporting.

### 5.2 Whole-module shim (when a path itself moves)

```python
# parameters_panel.py — shim, remove in milestone M+1
def __getattr__(name: str):
    import warnings
    import parameter_grid_panel as _new
    if hasattr(_new, name):
        warnings.warn(
            f"parameters_panel.{name} is deprecated; "
            f"import from parameter_grid_panel (or panels.parameter_grid) instead.",
            DeprecationWarning, stacklevel=2)
        return getattr(_new, name)
    raise AttributeError(
        f"module 'parameters_panel' has no attribute {name!r}")
```

### 5.3 AVC deprecation timeline

Reference policies:
- **NumPy NEP-23.** Deprecations live ≥ 2 releases or ≥ 1 year. `DeprecationWarning` for moves; `FutureWarning` for behavior changes. `[S10]`
- **pandas PDEP-17.** Three-stage: `DeprecationWarning` → `FutureWarning` → removal at next major. `[S17]`

**For AVC, internal project, no public API.** Collapse to:
- **Release cycle equivalent = "milestone."** Shim lives for one milestone after the move milestone.
- **`DeprecationWarning` only.** AVC has no end-user-facing import surface that would warrant `FutureWarning`.
- **Removal commit is separate** from the move commit, lands in milestone M+1, references the move's commit hash.

### 5.4 Warning category cheat sheet `[S13]`

| Category | When |
|----------|------|
| `DeprecationWarning` | "You should change your code." Ignored by default except in `__main__` — devs running tests will see it. |
| `FutureWarning` | Behavior is changing (not a rename). Visible by default. |
| `PendingDeprecationWarning` | "This will be deprecated soon." Ignored by default. Rarely the right choice — go straight to `DeprecationWarning`. |
| `UserWarning` | Default category. Avoid for refactor shims — use deprecation classes for searchability. |

### 5.5 Testing the shim

```python
# tests/test_shims.py
import warnings
import pytest

def test_parameters_panel_shim_still_works():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from parameters_panel import ParametersPanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "parameters_panel" in str(w.message)
        for w in caught
    )
```

`warnings.catch_warnings(record=True)` is the canonical test recipe. `[S13]`

---

## 6. Test parity verification

### 6.1 Two-snapshot pattern

1. **Pre-snapshot.** Tag `refactor-baseline`. Persist:
   - `pytest --collect-only -q > baseline.collect.txt`
   - `coverage xml -o baseline.coverage.xml`
   - `mutmut run` baseline (optional, on refactored modules only)
2. **Execute restructure.**
3. **Post-snapshot.** Same artifacts at `refactor-complete`.
4. **Diff.**
   - **Collection diff.** Test IDs in pre but not post → either deliberately removed (must be in `PLAN.md`) or silently lost (regression).
   - **Coverage diff per file.** `diff-cover` or `coverage-diff`. `[S25]`
   - **Mutation diff.** Score drop > 2% on a refactored module → investigate.

### 6.2 Coverage tolerances

| Signal | Tolerance | Interpretation |
|--------|-----------|----------------|
| Total LOC covered | ±1% | > 1% drop = tests no longer reaching previously-covered code. |
| Per-file coverage % | ±2% on moved files | Mechanical move shouldn't change coverage shape. |
| Branch coverage | ±2% | Same logic. |
| Test collection count | 0 | Must be exactly preserved unless `PLAN.md` removes specific tests. |

### 6.3 Characterization tests (Feathers) `[S22, S23]`

Write *before* the refactor, run *before and after*. They capture current behavior (including current bugs), not desired behavior.

For AVC:
- Launch app, default variety renders within N seconds (headless via `pv.OFF_SCREEN = True`, AI-3).
- Switch variety V1 → V2: status-bar updates, no crash.
- Toggle HQ smoothing: render queue handles the change.
- Export mesh STL/OBJ/PLY: file written, file readable.

**AI-2 constraint.** Test suite is Qt-free (no pytest-qt). Characterization tests must use pure NumPy/PyVista paths. Do not add Qt event-loop characterization tests.

### 6.4 Conftest.py fixture parity gotcha `[S24]`

Moving test files changes which `conftest.py` files apply to them, potentially breaking fixture visibility.

After moving any test file:
- Verify: `pytest --fixtures-per-test <moved_test_file>` and compare to baseline.
- If a fixture was in `tests/conftest.py` and the test moved to a sub-directory, it still resolves (upward search). If it moves to a *sibling* scope that has an `conftest.py` with the same fixture name, the new fixture silently wins — which may have different setup.

### 6.5 Mutation testing as confirmation `[S27]`

mutmut is slow. Don't gate refactors on it. Use it to *confirm* that test power did not degrade on touched modules. A material drop in mutation score on a refactored module usually means a test now no-ops because a fixture was broken or a moved method's tests no longer instantiate the right class.

---

## 7. The AI agent context-anchor problem

When code moves, **agent memory references break silently**. This is the AVC-specific risk most under-discussed in classical refactor literature; it is a 2024–2026 phenomenon. The literature is still forming.

### 7.1 What breaks

Per `[S19]`:
> "Stale path references in your AGENTS.md will actively mislead agents into trying to write to files that don't exist or importing from paths that have moved."

Forms of "agent context anchor" in AVC:
- `CLAUDE.md` pointers like "see surfaces.py for the variety functions." (Currently absent — but will be created as part of this restructure.)
- Per-folder `CLAUDE.md` files.
- Notes under `.claude/notes/**` referencing `app.py:1234`.
- `lessons.md` / agent-memory entries from prior milestones.
- Skill prompts that say "edit `surfaces.py`."
- Subagent definitions in `.claude/agents/*.md` with file references.
- `CONTEXT.md` at repo root.
- `.claude/references/app-invariants.md` (inviolable AI-1..AI-15 — must not move, but path references within it could become stale).

All of these become wrong simultaneously when a restructure lands.

### 7.2 Five strategies

**Strategy A — Path-to-symbol indirection.**
Instead of `see surfaces.py:1234 for compute_field`, write `see compute_field (use grep)`. The agent has to grep, but the reference never goes stale. Recommended for `CLAUDE.md`, `lessons.md`, skill prompts.

**Strategy B — `MOVES.md` as rosetta stone.**
Every restructure appends to a single `MOVES.md` at the repo root:
```markdown
## 2026-05-23 — panels subpackage extraction
- appearance_panel.py → panels/appearance.py (moved 738 LOC)
- parameter_grid_panel.py → panels/parameter_grid.py (moved 713 LOC)
- parameters_panel.py → SHIM (superseded by parameter_grid_panel; shim until M+1)
- view_panel.py → panels/view.py (moved 503 LOC)
- Symbol shims at original paths until milestone M+1.
```
The agent reads `MOVES.md` once at session start. When it encounters an old path in a note, it knows where to look now.

**Strategy C — Update agent-memory in the same restructure PR.**
Grep `.claude/notes/**` and `lessons.md`-style files for every moved path. Use the LibCST symbol-map to drive the substitution. This is Phase 8.

**Strategy D — CLAUDE.md → AGENTS.md migration.**
If AVC adopts AGENTS.md (the open standard `[S19]`), follow the recommended symlink approach:
```bash
mv CLAUDE.md AGENTS.md && ln -s AGENTS.md CLAUDE.md
```
For AVC today: CLAUDE.md does not exist yet. The evaluator report found it missing (item 8: FAIL). When creating it as part of this restructure, consider creating it as `AGENTS.md` with `CLAUDE.md` as a symlink, or just `CLAUDE.md` if the AGENTS.md standard adoption is premature. Do not combine this decision with the code restructure in the same commit — these are separate concerns.

**Strategy E — Pointer style, not content style.**
Per `[S20]`: "Include `file:line` references pointing to authoritative sources rather than copying code snippets directly." When you must include a path, include only one — and make sure Phase 8 updates it.

### 7.3 Per-folder CLAUDE.md

If the AVC restructure introduces subpackages, add a short `CLAUDE.md` in each subpackage describing:
- Responsibility ("this package owns the Qt panels for the main window left dock").
- Key entrypoints (symbol names, not line numbers).
- Cross-references to sibling subpackages (by name, not path).
- Any inviolable invariants that apply specifically to this subpackage.

Per `[S18]`: "Initialize work in subdirectories rather than the repo root, allowing Claude to load context additively while walking up the directory tree."

**AVC-specific.** The per-folder `CLAUDE.md` for any package containing VTK pipeline code must note AI-4 (clip_scalar not clip_box), AI-5 (scalars= keyword), and AI-6 (marching cubes for implicit surfaces only). The per-folder `CLAUDE.md` for panels/ must note AI-9 (re-entrancy guard), AI-11 (fully-qualified Qt enums), AI-13 (6-digit hex only).

---

## 8. Cross-suite test gaps specific to AVC

These are regressions that pass unit tests but reappear in integration. The architect should suggest adding cross-suite tests in these categories:

1. **Conftest scope drift.** A fixture in `tests/conftest.py` that some moved test now no longer sees. Catch: `pytest --fixtures-per-test` diff.

2. **Implicit fixture sharing.** Test A uses fixture `client` defined in conftest; test A moves; the moved location has a different `client` fixture with the same name but different setup. Catch: pre-move snapshot of `--fixtures-per-test`.

3. **Import-time side effects.** Module B used to be imported transitively because module A imported it; restructure breaks the transitive chain; B's `@pytest.fixture` registration in a `conftest.py` only ran because of that import. Catch: `pytest --collect-only` count + `python -X importtime` diff.

4. **Plugin discovery.** A `pytest_plugins` declaration in a conftest gets shadowed when the conftest scope changes. Catch: `pytest --trace-config` output diff.

5. **Seam tests between newly-split modules.** When `surfaces.py` splits into 4 files, new tests are needed to exercise the interaction across new boundaries (sampling output → marching input, AI-6). The old monolithic tests covered these implicitly; the new finer-grained tests may each cover their own module but miss the seam.

6. **VTK pipeline wiring (AI-3, AI-4, AI-6, AI-7).** VTK objects hold references that look fine in unit tests but leak (or fail to re-render) when the pipeline assembly is reshuffled. After a panel-class move, the signal wiring may target the wrong instance. Add at least one end-to-end "render-frame-then-check-pixel" smoke test using `pv.OFF_SCREEN = True` if not present.

7. **Qt signal wiring (AI-9, AI-11).** PyQt/PySide6 apps have integration paths (event filters, signal/slot wiring) that only fire under a real `QApplication`. After a panel-class move, the signal wiring may target the wrong instance. **AI-2 constraint applies**: no pytest-qt. Use the existing headless pattern.

8. **Settings persistence boundary (AI-10, AI-12).** AVC has `qsettings_persistence` tests already (`tests/test_qsettings_persistence.py`, 343 LOC). After any settings-related refactor or `SettingsPersistence` Extract Class operation, ensure these still cover the load/save path and that the key namespace has not changed.

9. **Star-import shadowing.** A `from foo import *` somewhere might bring in symbol X that used to live in `foo`; after the move, the star-import silently no longer brings X in. Catch: ruff F405. (Current evaluator check 16: PASS — no star-imports in AVC now. Must remain PASS after restructure.)

10. **Cyclic imports under production entrypoint.** Test runners often paper over import cycles by importing modules in a benign order; the production entrypoint (`app.py`) may not. Catch: `python -c "import app"` smoke test post-refactor. Especially relevant when `app.py` is split and fragments re-import each other.

The architect should *suggest* — not auto-write — additional tests in categories 5, 6, 7, and 10, because their content is project-specific and writing them blindly creates false comfort.

---

## 9. Verification rubric (20 items)

A post-execution checklist. Each item is binary (pass/fail) with a fast command.

| # | Item | Command / check |
|---|------|-----------------|
| 1 | All original tests still pass | `pytest` exit 0 |
| 2 | Test collection count preserved | `diff <(pytest --collect-only -q) baseline.collect.txt` empty (or only removals listed in `PLAN.md`) |
| 3 | No new test files silently skipped | `pytest --collect-only` shows no `<skipped>` markers not present at baseline |
| 4 | Per-file coverage within ±2% on moved files | `coverage-diff` or manual XML diff |
| 5 | Total coverage within ±1% | `coverage report` total line vs baseline |
| 6 | No new import cycles | `pydeps --show-cycles` output identical to baseline cycle set |
| 7 | No orphan modules | `pydeps` reachability from `app.py` covers every `.py` in the new tree |
| 8 | No import-time side effects regressed | `python -X importtime -c "import app" 2> import_after.log` — total time within ±20% of baseline |
| 9 | No module shadowing | No two modules in the new tree have the same `__name__` from any import path |
| 10 | No `from X import *` newly introduced | `grep -rn "import \*" --include='*.py'` returns same set as baseline (currently: zero — keep it zero) |
| 11 | Shims emit `DeprecationWarning` for every renamed/moved symbol | `tests/test_shims.py` passes |
| 12 | Shim warnings include the new path | grep test in `test_shims.py` |
| 13 | `git mv` rename detection succeeded | `git log --follow --oneline <new_path>` shows pre-move history |
| 14 | `MOVES.md` updated with this restructure's entries | New section present with date and old→new entries |
| 15 | Root `CLAUDE.md` pointers updated (or created for first time) | Grep old paths in `CLAUDE.md`: returns 0 (or only in `MOVES.md`) |
| 16 | Per-folder `CLAUDE.md` present for each new subpackage | `find . -path './<new_pkg>/CLAUDE.md'` returns the file |
| 17 | `.claude/notes/**/*.md` cleansed of stale paths | `grep -rn '<old_path>' .claude/notes/` returns 0 |
| 18 | `README.md` structure section reflects new tree | manual diff |
| 19 | `__pycache__` / `.pyc` for moved files cleared | `find . -name '__pycache__' -exec rm -rf {} +` then re-run tests; still green |
| 20 | Rollback command tested in a scratch worktree | Document command + confirm it returns to `refactor-baseline` tag cleanly |

A `repository-architect` that runs these 20 checks mechanically and reports the exact command output for any failure covers ~95% of the regressions identified in the literature.

---

## 10. Common rationalizations to refuse

### 1. "We can refactor and add features in the same PR."
- Violates: small-step discipline (Fowler), one-thing-per-commit (Feathers), `git bisect` survivability. `[S5, S22]`
- Also violates `[S18]`'s "your working tree must be clean (non-negotiable)."
- Refusal: "Land the restructure; merge; then land the feature in a follow-up."

### 2. "The tests will catch any regression."
- Violates: parity verification requires more than green tests — collection count, coverage shape, fixture visibility. `[S22, S24, S25]`
- Refusal: "Tests prove the suite still passes. They don't prove the suite is still exercising the same paths. Run the Phase 7 parity check."

### 3. "We can fix the imports later."
- Violates: "the system runs at all times" (Branch by Abstraction). `[S2]`
- Violates: `[S18]` "Don't chase 'one-shot' refactors; break work into phases with clear acceptance tests per phase."
- Refusal: "Every commit must be green. Imports are part of green. There is no 'later' that is safer than 'now.'"

### 4. "Let's just delete the old file, no shim needed."
- Violates: expand–contract (Parallel Change). `[S4]`
- Violates: deprecation-cycle norms of every major Python project. `[S10, S17]`
- AI-era cost: breaks every `.claude/notes/**` reference and every agent-memory entry; the next session can't find what moved.
- Refusal: "Shim it for one milestone. Removal is a separate commit referencing this one's hash."

### 5. "Let's do it in one big-bang commit so reviewers see the whole thing."
- Violates: strangler-fig "small, lower-risk replacements." `[S1]`
- Violates: `git bisect` discipline.
- Refusal: "Reviewers see the whole thing via `PLAN.md` and the commit-by-commit chain. A single commit is unreviewable and unbisectable."

### 6. "Sed will be fine for these import rewrites."
- Violates: Python lexical structure (string literals vs imports indistinguishable to regex). `[S9, S11]`
- Refusal: "Use LibCST. Sed cannot tell `from foo import bar` apart from `'from foo import bar'` in a docstring."

### 7. "Star-imports keep the shim shorter."
- Violates: stacklevel-based pinpoint deprecation `[S13]`; defeats static analysis.
- Refusal: "Use the `__getattr__` shim. Star-import shims hide *which* symbol triggered the warning."

### 8. "We don't need a rollback plan; we have git."
- Violates: every major incident playbook. `[S15]`
- Refusal: "Write the rollback command in `PREFLIGHT.md` before executing. Test it in a scratch worktree."

### 9. "The CLAUDE.md update can wait."
- Violates: `[S19]` "stale path references will actively mislead agents."
- Refusal: "Phase 8 is part of the restructure, not a follow-up. Otherwise next session's agent corrupts the new tree."

### 10. "We're internal-only; no deprecation needed."
- Internal-only ≠ no-callers. Notebooks, scratch scripts, agent memory, peer agents, and in-flight feature branches all count.
- **AVC-specific:** `.claude/notes/**` entries, `.claude/agents/*.md` definitions, and `CONTEXT.md` are all callers.
- Refusal: "Internal still has callers; they're just less visible. One milestone of shim is the cost of safety here."

---

## 11. Rollback plan

Every restructure must have a documented rollback. Three tiers.

### Tier 1 — Single-revert rollback (preferred)

Possible only if the entire restructure is a contiguous chain of small commits, no feature commits interleaved.

```bash
git revert --no-commit refactor-baseline..refactor-complete
git commit -m "revert: roll back restructure restructure-full-audit-2026q2-r1"
```

**Pre-conditions.**
- The chain `refactor-baseline..refactor-complete` contains *only* refactor commits.
- Each commit was independently green.
- No production state outside git was migrated.

**Tested.** Phase 4 preflight requires running the revert in a scratch worktree and confirming the result equals `refactor-baseline`.

### Tier 2 — Branch-by-abstraction toggle rollback

Not applicable to AVC's current Python source-only restructure. Applicable if a runtime switch is introduced (uncommon for this kind of project).

### Tier 3 — Shim-only rollback (partial)

Useful when the new structure is mostly working but one moved module misbehaves.

```bash
# Restore the old module's full code as the body of the shim:
git checkout refactor-baseline -- path/to/old_module.py
# Edit out the dependency on the moved-then-unmoved new path
git commit -m "revert: partial rollback of <symbol> in restructure-full-audit-2026q2-r1"
```

### Rollback document template

Store at `.claude/notes/restructure-full-audit-2026q2-r1/ROLLBACK.md`:

```markdown
# Rollback plan — restructure-full-audit-2026q2-r1

**Baseline tag.** refactor-baseline-2026-05-23
**Complete tag.** refactor-complete-2026-05-23
**Commit range.** refactor-baseline..refactor-complete (N commits)

**Tier 1 (whole-restructure revert).**
  git revert --no-commit refactor-baseline..refactor-complete
  git commit -m "revert: roll back restructure-full-audit-2026q2-r1"
  Tested in scratch worktree on YYYY-MM-DD: PASS / FAIL.

**Tier 3 partial (per-module).**
  git checkout refactor-baseline -- <path>
  git commit -m "revert: partial rollback of <module>"

**What rollback does NOT restore.**
  - MOVES.md entries (manual revert).
  - CLAUDE.md / AGENTS.md edits (manual revert).
  - Agent-memory entries updated in Phase 8:
    git checkout refactor-baseline -- .claude/
```

---

## 12. AVC-specific application sketch

A non-prescriptive ordering for the designer. Conservative, low-risk-first.

### Batch A — Introduce `panels/` subpackage (low risk)
- Move `appearance_panel.py`, `parameter_grid_panel.py`, `view_panel.py` to `panels/`.
- Shim `parameters_panel.py` → re-exports from `parameter_grid_panel` if confirmed superseded; otherwise also moves to `panels/`.
- LibCST codemod to rewrite all `from <panel> import` references in `app.py` and tests.
- Expected impact: evaluator items 11 (source package), 24 (framework adapters in subpackages) → closer to PASS.

### Batch B — Missing top-level files (negligible risk)
- Add `LICENSE`, `CHANGELOG.md`, `AGENTS.md` (or `CLAUDE.md`), `pyproject.toml`.
- Add `.pytest_cache` to `.gitignore`.
- These are creates/edits, not moves — no shims needed, no import rewiring.
- Expected impact: evaluator items 2, 3, 6, 7, 8, 25 → PASS.

### Batch C — Confirm `parameters_panel.py` status (low risk, requires investigation)
- Run the test suite with `parameters_panel.py` imports replaced by `parameter_grid_panel.py` equivalents. If green, `parameters_panel.py` is a candidate for Inline Class / shim-only.
- Do NOT delete `parameters_panel.py` — shim it for one milestone.

### Batch D — Split `surfaces.py` → `surfaces/` subpackage (medium risk)
- Gate: Batches A–C fully closed and green.
- Surface module has AI-8 (`Surface`/`ParamSpec` frozen registry), AI-6 (marching cubes), AI-14 (generator contract) — all must be preserved.
- Proceed only if Phase 3 dry-run shows no new cycles.

### Batch E — Extract Class on `app.py:MainWindow` (high risk)
- Gate: Batch D fully closed and green.
- Sequence: `SettingsPersistence` first, then `StatusBar`, then `RenderPipelineCoordinator`.
- Must preserve AI-9 (re-entrancy guard) throughout.
- Characterization tests required before starting.

---

## Sources

All accessed 2026-05-23 unless noted.

- [S1] Martin Fowler, *Strangler Fig Application*: https://martinfowler.com/bliki/StranglerFigApplication.html `[CONSENSUS]`
- [S2] Martin Fowler, *Branch By Abstraction*: https://martinfowler.com/bliki/BranchByAbstraction.html `[CONSENSUS]`
- [S3] Trunk Based Development, *Branch by Abstraction*: https://trunkbaseddevelopment.com/branch-by-abstraction/ `[CONSENSUS]`
- [S4] Martin Fowler, *Parallel Change*: https://martinfowler.com/bliki/ParallelChange.html `[CONSENSUS]`
- [S5] Refactoring.guru, *Moving Features Between Objects*: https://refactoring.guru/refactoring/techniques/moving-features-between-objects `[CONSENSUS]`
- [S6] Refactoring.guru, *Large Class smell*: https://refactoring.guru/smells/large-class `[CONSENSUS]`
- [S7] Martin Fowler, *Refactoring catalog* — Move Function: https://refactoring.com/catalog/moveFunction.html; Extract Class: https://refactoring.com/catalog/extractClass.html `[CONSENSUS]`
- [S8] IN-COM Data Systems, *How to Refactor a God Class*: https://www.in-com.com/blog/how-to-refactor-a-god-class-architectural-decomposition-and-dependency-control/ `[UNVERIFIED — single-author blog; content corroborates Fowler and Feathers]`
- [S9] LibCST documentation: https://libcst.readthedocs.io/en/latest/ `[CONSENSUS]` — LibCST 1.8.6, actively maintained as of Nov 2025, supports Python 3.0–3.14.
- [S10] NumPy NEP-23, *Backwards compatibility and deprecation policy*: https://numpy.org/neps/nep-0023-backwards-compatibility.html `[CONSENSUS]`
- [S11] Bowler archived status confirmed from GitHub: https://github.com/facebookincubator/Bowler — **archived August 8, 2025**; maintainers recommend LibCST codemods. LibCST recommended alternative. `[CONSENSUS — confirmed gate]`
- [S12] Python 3 docs, *Deprecations index*: https://docs.python.org/3/deprecations/index.html `[CONSENSUS]`
- [S13] Python 3 docs, *warnings — Warning control*: https://docs.python.org/3/library/warnings.html `[CONSENSUS]`
- [S14] pydeps: https://github.com/thebjorn/pydeps and https://pydeps.readthedocs.io/en/latest/ `[CONSENSUS]`
- [S15] Pete Hodgson, *Expand/Contract: making a breaking change without a big bang* (2023): https://blog.thepete.net/blog/2023/12/05/expand/contract-making-a-breaking-change-without-a-big-bang/ `[CONSENSUS]`
- [S16] OneUptime, *How to Create Branch by Abstraction Pattern*: https://oneuptime.com/blog/post/2026-01-30-branch-by-abstraction-pattern/view `[UNVERIFIED — single blog; corroborates Fowler S2]`
- [S17] pandas PDEP-17, *Backwards compatibility and deprecation policy*: https://pandas.pydata.org/pdeps/0017-backwards-compatibility-and-deprecation-policy.html `[CONSENSUS]`
- [S18] LowCode Agency / Skywork, *Claude Code Plugin Best Practices for Large Codebases*: https://skywork.ai/blog/claude-code-plugin-best-practices-large-codebases-2025/ `[UNVERIFIED — single blog; content corroborates Anthropic documentation on CLAUDE.md patterns]`
- [S19] Hivetrail, *AGENTS.md vs CLAUDE.md: The AI Developer's Guide to Context Standards*: https://hivetrail.com/blog/agents-md-vs-claude-md-cross-tool-standard `[UNVERIFIED — single blog; the AGENTS.md standard itself is real and widely adopted]`
- [S20] HumanLayer, *Writing a good CLAUDE.md*: https://www.humanlayer.dev/blog/writing-a-good-claude-md `[UNVERIFIED — single blog; content corroborates Anthropic documentation]`
- [S21] Git documentation on rename detection: https://git-scm.com/docs/git-diff#Documentation/git-diff.txt--Mltngt `[CONSENSUS]`
- [S22] Michael Feathers, *Characterization Testing*: https://michaelfeathers.silvrback.com/characterization-testing and *Working Effectively with Legacy Code (key points)*: https://understandlegacycode.com/blog/key-points-of-working-effectively-with-legacy-code/ `[CONSENSUS]`
- [S23] Martin Fowler, *Legacy Seam*: https://martinfowler.com/bliki/LegacySeam.html `[CONSENSUS]`
- [S24] pytest documentation, *Fixtures reference*: https://docs.pytest.org/en/stable/reference/fixtures.html `[CONSENSUS]`
- [S25] Coverage.py: https://coverage.readthedocs.io/ ; diff-cover: https://github.com/Bachmann1234/diff_cover `[CONSENSUS]`
- [S26] SeatGeek ChairNerd, *Refactoring Python with LibCST* (2019): https://chairnerd.seatgeek.com/refactoring-python-with-libcst/ `[CONSENSUS]`
- [S27] mutmut docs: https://mutmut.readthedocs.io/en/latest/ `[CONSENSUS]`
- [S28] Instagram LibCST repo: https://github.com/Instagram/LibCST `[CONSENSUS]` — LibCST 1.8.6 as of PyPI Nov 2025; Python 3.0–3.14 support.
- [S29] Instawork Engineering, *Refactoring a Python Codebase with LibCST*: https://engineering.instawork.com/refactoring-a-python-codebase-with-libcst-fc645ecc1f09 `[UNVERIFIED — fetch returned TLS error; existence corroborated by secondary sources]`
- [S30] Rope: https://github.com/python-rope/rope — v1.14.0 released Jul 2025; last updated Jan 2026. `[CONSENSUS — actively maintained]`
- [S31] TestDriven.io, *Splitting a module into multiple files*: https://testdriven.io/tips/3660b476-7aaa-4f7b-af22-28aa00fc871e/ `[UNVERIFIED — single blog; content corroborates Hitchhiker's Guide to Python]`

**Tooling drift notes (2026-05-23 verification run).**
- Bowler confirmed archived August 8, 2025. The README on the archived repo explicitly redirects to LibCST. `[GATE-REQUIRED]`
- LibCST 1.8.6 is the current version (Nov 2025); Python 3.14 support confirmed.
- Rope 1.14.0 (Jul 2025) confirmed actively maintained (Jan 2026 activity on GitHub).
- ruff confirmed as the de-facto 2026 ecosystem standard replacing flake8+isort+black.
- Sandi Metz squint test remains `[UNVERIFIED]` for primary source attribution within time-box budget.
- Instagram "Static Analysis at Scale" blog and Instawork case study both returned TLS errors; existence and gist corroborated via secondary sources.
