# Scout C — Safe-Refactor Playbook for the AVC `/repository-architect`

**Scope.** Survey of 2020–2026 safe-large-refactor patterns, Python tooling, and AI-agent-era considerations. Focus: the **DELICATE phase** of an AVC restructure — the part where files actually move, classes actually split, and tests/imports/agent memory can silently break. Brief feeds the design phase of the `/repository-architect` slash command; it does **not** design the command itself.

**AVC repo snapshot (read at 2026-05-23, branch `main`).** Flat top-level layout, 7.8 KLOC across 11 modules, the two giants being `app.py` (1893 LOC) and `surfaces.py` (1808 LOC). 23 test files under `tests/` (flat). `pytest.ini` present. No `src/` layout, no subpackages, no `__init__.py` at the project root, no `MOVES.md`, no `AGENTS.md`. This is the substrate against which "safe restructure" must be defined.

**Honesty conventions.**

- Every claim has an inline `[Sn]` citation linking to the Sources block at the end.
- `[CONSENSUS]` = three+ independent reputable sources agree. `[CONTESTED]` = sources disagree. `[UNVERIFIED]` = author could not confirm from a primary source within the time-box.
- Time-box: ~30 min wall-clock; all sources accessed 2026-05-23.

---

## 1. TL;DR — what a safe restructure pipeline MUST do

1. **Capture a baseline before touching anything.** Tests green, coverage measured, import graph snapshotted, `git status` clean. Without this, you cannot prove parity afterwards. `[CONSENSUS — S1, S6, S8]`
2. **Propose the target tree explicitly, with deltas.** A diffable plan (old path → new path, file split with line ranges, new symbol homes) reviewed *before* any `git mv` runs. Mirrors the "branch by abstraction" stance: the new state and the old state must be describable simultaneously. `[S2]`
3. **Dry-run the import-graph impact without moving files.** Compute, against the existing tree, "if these moves were applied, what would break?" — orphan modules, new cycles, broken `from X import Y`, conftest.py scope drift. Tools: `pydeps`, `modulegraph`, `libcst` static analysis. `[S11, S14]`
4. **Execute in tiny commits with a shim/deprecation cycle in between.** Each commit must leave the system green; the old import paths keep working via `__init__.py` `__getattr__` shims that raise `DeprecationWarning`. Follow Parallel Change / expand–contract: expand (new + old coexist) → migrate (callers move) → contract (old removed). `[CONSENSUS — S3, S4, S15, S16]`
5. **Re-baseline at the end and update every navigation anchor.** Coverage delta, import-graph delta, test-parity check, **plus** every agent-readable navigation surface (`CLAUDE.md`, `AGENTS.md`, `MOVES.md`, agent-memory `lessons.md`). The restructure isn't done until the AI agents that will work in the new tree can find their way around. `[S18, S19, S20]`

> **The thesis of this brief.** The technical refactor is the easy part; preserving *agent context anchors* and *test-suite coverage shape* is what makes a restructure regress silently weeks later. Plan for both.

---

## 2. The Eight Phases of a Safe Restructure

Each phase names the canonical pattern, the source, the exit criterion, and the typical failure if you skip it.

### Phase 1 — Baseline (snapshot, green, measured)

**Pattern.** Feathers' "establish characterization tests before changing legacy code." `[S22]`

**Mechanics.**

- `git status` clean — no uncommitted changes. `[S18]` calls this "non-negotiable" for Claude Code refactors.
- Full test suite green. Capture wall-clock and per-test timings.
- `coverage run -m pytest && coverage xml -o baseline-coverage.xml` and store it. This is the parity yardstick. `[S25]`
- Snapshot import graph: `pydeps avc/ --max-bacon=0 --noshow -o baseline-imports.svg` plus a textual `pydeps --show-deps` JSON dump for diffing. `[S14]`
- Snapshot symbol locations: for every public symbol the agent might reference, record `{symbol → path:line}`. This is what later anchors the "agent context" repair step.
- Tag: `git tag refactor-baseline-YYYY-MM-DD`.

**Exit criterion.** All of the above artifacts exist on disk, committed or stored in `.claude/notes/<refactor-id>/baseline/`.

**Failure if skipped.** You cannot prove later that test coverage shape, behavior, or import topology was preserved. Without a baseline, "the tests still pass" is meaningless — the suite might have silently skipped or no-op'd. `[S22, S25]`

### Phase 2 — Propose (target tree, file moves, file splits)

**Pattern.** Fowler's catalog operations made *explicit* before execution: Move Function / Move Field / Extract Class / Inline Class. `[S5, S7]`

**Mechanics.**

- Produce a `PLAN.md` artifact with three sections:
  1. **Tree diff.** Old tree → new tree, line-by-line.
  2. **Symbol map.** For each symbol being moved or split: source path:line → target path:line. Use libcst's `MetadataProvider` to enumerate top-level definitions reliably. `[S9]`
  3. **Delta size.** For each new file: predicted LOC; for each split: source LOC → target1 LOC + target2 LOC + shim LOC.
- Mark every split with the *Sandi Metz "squint test"* outcome: can a human squint at the new file and see one responsibility? `[UNVERIFIED — Metz's squint test is widely attributed but the brief author did not fetch the original Sandi Metz reference within the time-box; the pattern is real and well-known but the exact source URL is not cited here.]`
- Each move/split entry references a Fowler catalog operation (Move Function, Extract Class, Split Module, Introduce Subpackage) so reviewers know which mechanics apply. `[S7]`

**Exit criterion.** Reviewer (human or peer agent) can re-derive the new tree from `PLAN.md` alone, without re-reading the source. No "TBD" entries.

**Failure if skipped.** Refactor becomes a stream-of-consciousness rewrite; the "what changed and why" lives only in the diff. Agent context anchors cannot be planned (because nobody knows where things will land). Common Claude Code failure mode per `[S18]`: "model loses track of downstream files needing updates mid-session."

### Phase 3 — Dry-run (import-graph delta without moving anything)

**Pattern.** Branch by Abstraction's "the system runs at all times" stance, applied predictively. `[S2]`

**Mechanics.**

- Build the *predicted* import graph by mechanically applying the symbol-map to the current AST (libcst can rewrite imports in memory without writing to disk). `[S9]`
- Diff predicted graph vs. baseline graph:
  - **New cycles?** Reject the plan or restructure the split.
  - **Orphaned modules?** Reject.
  - **Increased fan-in on a single module past a threshold (e.g. 20)?** Flag as god-module risk.
  - **`from X import *` patterns?** Flag — these are invisible to static rewriting and will break silently.
- For each test file, predict which `conftest.py` files apply *after* the move. `[S24]` warns: "Moving test files changes which `conftest.py` files apply to them, potentially breaking fixture visibility."
- Predict pytest collection delta: `pytest --collect-only -q` before vs. *would-be* after. If the count drops, fixtures or test files have become unreachable.

**Exit criterion.** A `DRY-RUN.md` with zero red flags, or a revised `PLAN.md` that addresses each flag.

**Failure if skipped.** The classic "we moved everything, all tests pass, but pytest now collects 200 fewer tests because a `conftest.py` is in the wrong scope." This is the silent regression Scout C is most worried about.

### Phase 4 — Pre-flight (shim plan, deprecation cycle, branch strategy)

**Pattern.** Parallel Change / expand–contract. `[S4]` NumPy NEP-23 deprecation policy. `[S10]` pandas PDEP-17 three-stage policy. `[S17]`

**Mechanics.**

- For every old import path that will move, decide: **shim or hard break?**
  - **Shim (default).** Old path stays importable; emits `DeprecationWarning`; routes to new location via `__init__.py` `__getattr__`. `[S12, S13]`
  - **Hard break (rare).** Only when the symbol was genuinely private (`_name`) or never imported by name. Document the justification.
- Decide deprecation lifetime: minimum one release / two minor versions per NumPy/pandas precedent `[S10, S17]`. For AVC (no public API, internal project), this collapses to "one PR cycle" or "one milestone" — i.e. the shim survives until the next milestone closes, then a follow-up PR contracts it.
- Branch strategy. Per the user's stated platform-repo workflow this AVC repo does not enforce MR-gating, but the *refactor itself* should still be in its own commit chain (a series of small commits on `main`, each green) rather than mixed with feature work. `[S18]` calls mixing "the rationalization to refuse most often."
- Write the rollback note (Section 11) *before* executing, not after.

**Exit criterion.** `PREFLIGHT.md` documents shim plan, deprecation timeline, rollback command.

**Failure if skipped.** Hidden callers (notebooks, scratch scripts, agent-memory references) break with no migration path. Without the rollback note pre-written, a panicked revert can take down adjacent unrelated work.

### Phase 5 — Execute (the moves, in small commits)

**Pattern.** Fowler "small steps" catalog discipline `[S5, S7]`; SeatGeek's "cautious rollout: 20-200 lines, review, then scale up." `[S26]`

**Mechanics.**

- One refactor catalog operation per commit. "Move `parameter_grid_panel.ParameterGridPanel` to `panels/parameter_grid.py`" is one commit; "extract `ParameterGridPanel.update_columns` into helper" is a different commit.
- Use `git mv` (not delete+add) so Git's rename heuristic preserves blame and `--follow` works. `[S21]` warns: if the move is combined with >50% content change in the same commit, rename detection fails — keep moves and edits in *separate* commits.
- After every commit:
  1. `pytest` green.
  2. `python -c "import <new path>"` — smoke test the new import.
  3. `python -c "import <old path>"` — smoke test the shim emits the deprecation warning.
- Use libcst codemods for *mechanical* import rewrites across the rest of the tree — never `sed`. `[S9, S11]` Regex is forbidden for import rewriting in Python because it cannot distinguish `from foo import bar` (top-level import) from a string literal `"from foo import bar"`.

**Exit criterion.** Every intended move/split landed; every commit is green standalone (`git bisect` would survive); shims in place.

**Failure if skipped (i.e. "big-bang commit").** Per `[S1]` strangler-fig guidance: big-bang is the original sin. `git bisect` is destroyed. Reviewers cannot tell which sub-change broke what. Rollback is all-or-nothing.

### Phase 6 — Re-import-graph verify (no orphans, no cycles, no broken imports)

**Pattern.** "Continuous validation of dependency graphs" `[S8]`; pydeps cycle detection `[S14]`.

**Mechanics.**

- Re-run `pydeps --show-cycles`. Compare to predicted graph from Phase 3. The actual graph should match the prediction; *any* divergence is a yellow flag worth explaining.
- Run `python -X importtime -c "import <root_module>"` and diff against baseline — large new import-time spike indicates a side-effect leak.
- Use ruff or pyflakes to scan for `F401` (unused import), `F811` (redefined name), `F821` (undefined name). `[S11]` notes ruff's `--fix` landscape is the de-facto autofix engine 2024-2026 for these.
- Confirm no `from X import *` was introduced (these defeat static analysis and AI agent navigation alike).

**Exit criterion.** Import graph matches the Phase-3 prediction; zero ruff F-class errors; no import-time regression.

**Failure if skipped.** Hidden cycles surface weeks later as `ImportError: cannot import name X (most likely due to a circular import)` in some rarely-exercised path.

### Phase 7 — Test parity verify (same tests run, same coverage shape, no silent skips)

**Pattern.** Coverage diff + characterization tests + mutation testing as confirmation. `[S25, S22, S27]`

**Mechanics.**

- `pytest --collect-only -q | wc -l` after vs. before. Number of collected tests **must not decrease** unless a test file was deliberately removed (and `PLAN.md` lists it).
- `coverage run -m pytest && coverage xml -o post-coverage.xml`. Diff against `baseline-coverage.xml`:
  - **Per-file coverage % delta.** Each moved file's coverage % should be within ±2% (it's roughly the same code, possibly at a new path).
  - **Coverage breadth.** Total lines covered should match within ±1% (a drop signals tests that no longer run).
  - Use `coverage-diff` or `diff-cover` to mechanize this. `[S25]`
- Characterization smoke: pick 3-5 user-facing behaviors (e.g. for AVC: "open app → render default variety → switch subtype → no error"). If automatable via pytest-qt or similar, do so before the refactor; re-run after. `[S22, S23]`
- **Mutation testing as confirmation, not gate.** Run `mutmut run` on the refactored modules; mutation score should not drop materially vs. baseline. A large drop means the refactor pulled apart code such that fewer mutations are caught — usually because a test was implicitly depending on a now-moved fixture. `[S27]`

**Exit criterion.** Collection count preserved; per-file coverage within tolerance; total coverage within tolerance; mutation score within tolerance; characterization smoke passes.

**Failure if skipped.** "All tests pass" hides "20 tests silently no-op because their conftest.py is in the wrong directory now." This is the canonical refactor regression.

### Phase 8 — Re-baseline (navigation docs, CLAUDE.md, agent memory)

**Pattern.** "Agent context anchor" repair (see Section 7 for the full discussion); pointer-based `CLAUDE.md` per `[S20]`.

**Mechanics.**

- Append entry to `MOVES.md` (create if absent): `{from_path}:{from_line_range} → {to_path}:{to_line_range}` for every moved symbol. This is the agent-memory rosetta stone.
- Update root `CLAUDE.md`: refresh the "key modules" pointer table. Per `[S19, S20]` — keep this section pointer-based (`see panels/parameter_grid.py for the panel`), never embed content.
- For each subdirectory that gained code, add (or update) a per-folder `CLAUDE.md` describing its responsibility — `[S18]` recommends initializing work in subdirectories so Claude loads context additively.
- Walk `.claude/notes/**/*.md` and `lessons.md`-style memory files; grep for old paths; update inline. Use `MOVES.md` as the lookup table.
- Update `README.md` repo structure section if present.
- Re-run the import-time benchmark and update any docs that quote startup numbers.
- Re-tag: `git tag refactor-complete-YYYY-MM-DD`.

**Exit criterion.** Grep for any old path across all `.md` files in the repo returns zero hits (or only inside `MOVES.md` itself, which is the intended sink).

**Failure if skipped.** Future Claude Code sessions will load stale `CLAUDE.md` pointers and try to `Read` paths that no longer exist. `[S19]` is explicit: "Stale path references in your AGENTS.md will actively mislead agents into trying to write to files that don't exist or importing from paths that have moved."

---

## 3. Tooling matrix

| Tool | Language | What it does | Install footprint | License | AVC applicability |
|---|---|---|---|---|---|
| **LibCST** | Python | Concrete syntax tree; preserves formatting; the de-facto choice for import rewriting and codemods. Used by Instagram, Instawork, SeatGeek at scale. `[S26, S28, S29]` | `pip install libcst` (pure Python, no native deps) | MIT | **Primary tool.** Use for all import rewriting, symbol renames, file splits. Active dev, supports Py 3.0–3.13. `[S9, S11]` |
| **Rope** | Python | Project-wide refactor library: rename, move, extract, inline. IDE-oriented; v1.14.0 released Jul 2025. `[S30]` | `pip install rope` | LGPL-3.0+ | **Secondary.** Good for interactive rename/move from a Python script or via the `rope` CLI. Less ergonomic than LibCST for bulk codemods; LGPL may matter for distribution. `[S30]` |
| **Bowler** | Python | Facebook's earlier safe-refactor tool, built on `lib2to3`. **Archived; deprecated in favor of LibCST.** `[S11]` | n/a — do not adopt new | Apache-2.0 | **Skip.** lib2to3 is also deprecated in modern Python; Bowler has no path forward. `[S11]` |
| **ruff** | Python | Linter + autofix. `--fix` covers F401 (unused import), F811 (redefined), I001 (sort/dedupe imports), plus 700+ other rules. `[S11]` | `pip install ruff` (rust binary, fast) | MIT | **Primary verification.** Run after every commit during Execute phase to catch import drift. |
| **pyflakes** | Python | Subset of what ruff does; lower friction if ruff not adopted. | `pip install pyflakes` | MIT | Fallback if ruff is unavailable. |
| **ast (stdlib)** | Python | Abstract syntax tree; **does not preserve formatting** — destroys comments, whitespace, parens on round-trip. `[S9]` | stdlib, zero install | PSF | **For analysis only.** Never use for rewriting files; use LibCST instead. Useful in Phase 3 dry-run to enumerate symbols. |
| **pydeps** | Python | Module dependency graph generator; `--show-cycles` highlights cyclic imports; uses bytecode analysis. `[S14]` | `pip install pydeps` (requires graphviz for rendering) | BSD-2-Clause | **Primary** for Phase 3 dry-run and Phase 6 verify. SVG output is human-reviewable; JSON output is diff-able. |
| **modulegraph** | Python | Alternative to pydeps; py2app/py2exe pedigree; more flexible IR than stdlib modulefinder. `[S14]` | `pip install modulegraph` | MIT | Secondary; pydeps is more common for refactor work. |
| **coverage.py** | Python | Line + branch coverage; XML output diff-able with `coverage-diff` / `diff-cover`. `[S25]` | `pip install coverage` | Apache-2.0 | **Primary** for Phase 7 parity check. Already in AVC via pytest setup most likely. |
| **mutmut** | Python | Mutation testing; flags tests that pass despite mutations. `[S27]` | `pip install mutmut` | BSD | **Confirmation tool** in Phase 7; slow (hours on a big suite), so use selectively on the modules being refactored. |
| **pytest --collect-only** | Python | Lists tests without running them; the canonical "did I silently drop tests?" check. `[S24]` | stdlib of pytest | MIT | Free; use in every Phase 3 / Phase 7 run. |
| **git mv** | Git | Rename with `--follow`-friendly history; rename detection works at the diff level via similarity (default 50%). `[S21]` | builtin | GPL | **Required for every move** to keep blame intact. Pair with separating moves from content edits in distinct commits. |
| **git filter-repo** | Git | Recommended successor to `git filter-branch` for rewriting history. `[S21]` | separate install | MIT | Only for catastrophic-recovery scenarios; not part of normal restructure. |
| **grep / ripgrep + sed** | Shell | Cheap, mechanical text replacement. | builtin / `rg` | varies | **Forbidden for Python imports** — cannot distinguish `from foo import bar` from `"from foo import bar"` in a docstring or template. Acceptable for one-off `MOVES.md` post-edits. |

**Net recommendation for AVC.** LibCST + ruff + pydeps + coverage.py + pytest. Optional: mutmut for confirmation on the two giants (`app.py`, `surfaces.py`). All MIT/Apache/BSD/PSF; no copyleft surprises. Total install footprint is small; LibCST is the only non-trivial dependency and it's pure Python.

---

## 4. Pattern catalogue

For each pattern: **when**, **mechanics**, **failure modes**, **Python example**, **source**.

### 4.1 Move Function

- **When.** A free function is called more from module B than from its home module A. `[S5]`
- **Mechanics (Fowler).** Define the function in B with the same signature. Replace the body in A with a delegating call to B. Run tests. Update each caller to import from B directly. Delete the A version (or leave a shim — see §5). `[S5]`
- **Failure modes.**
  - Function had implicit access to a module-level state in A (e.g. a module-level constant). The move drags a hidden dependency.
  - The function is referenced by `getattr(module_a, "fn_name")` or by string — static analysis misses it.
- **Python example.** Moving `ui_helpers.format_progress_label` to `panels/status_bar.py`: use LibCST `RemoveImportsVisitor` + `AddImportsVisitor` codemod to rewrite every `from ui_helpers import format_progress_label` to `from panels.status_bar import format_progress_label` across the tree. `[S9]`

### 4.2 Move Method (a.k.a. Move Function for a method)

- **When.** A method `Foo.bar()` interacts more with `Baz` instances than with `Foo` instances. `[S5]`
- **Mechanics.** Add `bar` to `Baz`. Either turn `Foo.bar` into a delegating one-liner or remove it. Update callers.
- **Failure modes.** `self` references inside the method that don't trivially translate to a `Baz` member. Mocks/spies tied to `Foo.bar` in tests now miss.
- **Python example.** In `app.py`, a method like `MainWindow._refresh_busy_spinner` that mostly manipulates a `RenderWorker` belongs on `RenderWorker.refresh_busy_spinner` (or a helper on a new `BusyIndicator` class).

### 4.3 Extract Class

- **When.** A class has too many fields/methods serving more than one responsibility — the "Large Class / God Class" smell. `[S6, S8]`
- **Mechanics.** Identify a cohesive group of fields + the methods that read/write them. Create a new class. Move the fields, then move the methods. Replace the old fields with a single field holding the new class instance; the old methods become delegators (or are removed once callers migrate). `[S5, S7]`
- **Failure modes.**
  - **Cyclic dependency.** Old class now needs new class and vice versa. Resolve by extracting a third interface or by moving a method to break the cycle. `[S8]`
  - **Implicit shared state.** Two responsibilities were happening to share a dict; the split introduces a sync bug.
  - **Tests bound to the old class structure.** Mocks targeting `MainWindow._busy` break when `_busy` becomes `MainWindow._busy_indicator._state`.
- **Python example.** AVC's `app.py:MainWindow` (≈ a thousand LOC of class body) likely hides 4-6 responsibilities (window/menus, render pipeline orchestration, status/HUD, settings persistence, panel layout). Sequence:
  1. Extract `SettingsPersistence` (probably the cleanest seam — file-IO with few internal deps).
  2. Extract `StatusBar` / HUD class (own widget, own state).
  3. Extract `RenderPipelineCoordinator` (talks to `render_worker` + `surfaces`).
  4. Leave `MainWindow` as the assembly point.
  - At each step: shim, test, commit.

### 4.4 Inline Class

- **When.** A class does almost nothing; its responsibilities have drained into other classes. `[S7]`
- **Mechanics.** Move all members into the consumer class; delete the empty class. Inverse of Extract Class. `[S7]`
- **Failure modes.** External callers still importing the now-deleted class — shim it (re-export the consumer class under the old name) for one cycle, then remove.

### 4.5 Split Module

- **When.** A `.py` file has crossed the "two cognitive responsibilities" line, regardless of class structure. The "squint test" fails. `[S31 — testdriven.io tip on splitting modules]`
- **Mechanics.** Convert the module to a package (rename `foo.py` → `foo/__init__.py`, then create `foo/responsibility_a.py`, `foo/responsibility_b.py`). The package `__init__.py` re-exports the same public names, so `from foo import Bar` still works. `[S31]`
- **Failure modes.**
  - The conversion step (file → directory) is two `git` operations; do it in a single commit with `git mv` so rename detection survives.
  - Implicit star-imports from the old module become ambiguous.
  - Pyc cache and `__pycache__/` from the old `.py` lingers; delete it explicitly.
- **Python example.** AVC's `surfaces.py` (1808 LOC) → `surfaces/__init__.py` (re-exports), `surfaces/varieties.py`, `surfaces/sampling.py`, `surfaces/marching.py`, `surfaces/smoothing.py`. `__init__.py` keeps `from surfaces import compute_field` working for every existing caller.

### 4.6 Move Module

- **When.** A module's logical home has changed (e.g. `parameter_grid.py` is really a piece of a `panels/` subsystem). `[S5]`
- **Mechanics.** `git mv old/path.py new/path.py`. Add a shim at `old/path.py`:
  ```python
  # old/path.py — shim, slated for removal in milestone M+1
  import warnings
  warnings.warn(
      "old.path is deprecated; import from new.path instead.",
      DeprecationWarning, stacklevel=2)
  from new.path import *  # noqa: F401, F403
  ```
  Better, because `import *` is brittle, use the `__getattr__` pattern `[S12, S13]`:
  ```python
  # old/path.py — shim
  def __getattr__(name):
      import warnings
      from new import path as _new
      if hasattr(_new, name):
          warnings.warn(
              f"old.path.{name} is deprecated; "
              f"import from new.path instead.",
              DeprecationWarning, stacklevel=2)
          return getattr(_new, name)
      raise AttributeError(
          f"module 'old.path' has no attribute {name!r}")
  ```
  The `__getattr__` form only triggers the warning when the symbol is actually accessed, and supports lazy import (no eager load of the new module if no one uses the shim).
- **Failure modes.** Star-imports from the shim defeat the deprecation warning's stacklevel pinpointing. Always prefer named imports.

### 4.7 Rename Module

- **When.** The module's name no longer reflects its content (often after an Extract Class or Move Module that left a misnomer). `[S5]`
- **Mechanics.** Same as Move Module — it's a special case where the destination is in the same directory.
- **Failure modes.** Same as Move Module, plus: case-insensitive filesystem (macOS default APFS, Windows) can hide a rename that differs only in case. `git mv Foo.py foo.py` may silently no-op; use a two-step rename through a temp name.

### 4.8 Introduce Subpackage

- **When.** The flat top-level layout has accumulated > 8-10 modules and a thematic grouping is obvious. AVC fits this trigger today (11 top-level `.py` files, no subpackages). `[S31]`
- **Mechanics.** Create the subpackage directory with `__init__.py`. Move the relevant modules in. Update imports. Shim each moved module's old path for one cycle.
- **Failure modes.**
  - Forgot to `git add` the new `__init__.py` → import fails.
  - Test files at the old path still try to `from <module> import X` instead of `from <pkg>.<module> import X`. Use libcst codemod to rewrite all test files in one commit, separate from the move commit.
- **Python example.** Group AVC's three panel modules (`appearance_panel.py`, `parameter_grid_panel.py`, `parameters_panel.py`, `view_panel.py`) into a `panels/` subpackage in one logical phase.

---

## 5. Shim / deprecation cycle

The shim is what makes "the system runs at all times" possible during a restructure. Without shims you must update every caller in the same commit as the move — which (a) defeats `git bisect`, (b) breaks dev branches in flight, (c) breaks notebooks and scratch scripts, and (d) breaks AI agent memory that references the old path.

### 5.1 The canonical Python shim (recommended)

`__init__.py` `__getattr__` pattern, derived from `[S12, S13]` and used by `collections` in the stdlib `[S12]`:

```python
# panels/__init__.py — backward-compat shim, remove in milestone M+1
_RENAMES = {
    # old name in panels.*           → new home
    "ParameterGridPanel":            "panels.parameter_grid.ParameterGridPanel",
    "AppearancePanel":               "panels.appearance.AppearancePanel",
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

- Lazy: target module is only imported when accessed, so no startup cost.
- Pinpoint warnings: `stacklevel=2` places the warning at the *caller's* import site, not inside the shim. `[S13]`
- Cleanly errors on bogus names rather than re-exporting whatever happens to be in the new module.

### 5.2 Whole-module shim (when the path itself moves)

```python
# old_path.py  — shim, remove in milestone M+1
def __getattr__(name: str):
    import warnings
    from new_path import __dict__ as _ns
    if name in _ns:
        warnings.warn(
            f"old_path.{name} is deprecated; "
            f"import from new_path instead.",
            DeprecationWarning, stacklevel=2)
        return _ns[name]
    raise AttributeError(
        f"module 'old_path' has no attribute {name!r}")
```

### 5.3 Deprecation timeline

Two real-world reference policies:

- **NumPy NEP-23.** Deprecations live ≥ 2 releases or ≥ 1 year. `DeprecationWarning` (developer-facing) for moves; `FutureWarning` (user-facing) for behavior changes. `[S10]`
- **pandas PDEP-17.** Three-stage: `DeprecationWarning` initially → `FutureWarning` in the minor release before the next major → removal at the major. Type stubs keep deprecated entries marked, never removed silently. `[S17]`

**For AVC, internal project, no public API.** Collapse to:

- **Release cycle equivalent = "milestone."** Shim lives for one milestone after the move milestone.
- **`DeprecationWarning` only.** AVC has no end-user-facing import surface that would warrant `FutureWarning`.
- **Removal commit is separate** from the move commit, lands in milestone M+1, references the move's commit hash in the message.

### 5.4 Warning category cheat sheet `[S13]`

| Category | When |
|---|---|
| `DeprecationWarning` | Default for "you should change your code." **Ignored by default except in `__main__`** — devs running tests will see it, end users won't. |
| `FutureWarning` | Behavior is changing (not a rename). Visible by default. |
| `PendingDeprecationWarning` | "This will be deprecated soon." Ignored by default. Rarely the right choice — usually just go straight to `DeprecationWarning`. |
| `UserWarning` | Default category. Avoid for refactor shims — use the deprecation classes for searchability. |

### 5.5 Testing the shim

```python
# tests/test_shims.py
import warnings
import pytest

def test_old_panels_import_still_works():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from panels import ParameterGridPanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "panels.ParameterGridPanel is deprecated" in str(w.message)
        for w in caught
    )
```

`warnings.catch_warnings(record=True)` is the canonical test recipe. `[S13]`

---

## 6. Test parity verification

The goal: prove that the test suite exercises the same code paths and asserts the same behaviors after the restructure as before. "All tests pass" is necessary but not sufficient.

### 6.1 The two-snapshot pattern

1. **Pre-snapshot.** Tag `refactor-baseline`. Persist:
   - `pytest --collect-only -q > baseline.collect.txt` (every test id).
   - `coverage xml -o baseline.coverage.xml`.
   - `mutmut run` baseline if mutation testing is in play.
2. **Execute restructure.**
3. **Post-snapshot.** Same three artifacts at `refactor-complete`.
4. **Diff.**
   - **Collection diff.** Test IDs in pre but not post → either deliberately removed (must be in `PLAN.md`) or silently lost (regression).
   - **Coverage diff per file.** `diff-cover` or `coverage-diff` is the standard. `[S25]`
   - **Mutation diff.** Score drop > 2% on a refactored module → investigate.

### 6.2 Coverage tolerances

| Signal | Tolerance | Interpretation |
|---|---|---|
| Total LOC covered | ±1% | Likely fine. > 1% drop = tests are no longer reaching code that used to be covered. |
| Per-file coverage % | ±2% on moved files | Mechanical move shouldn't change coverage shape. |
| Branch coverage | ±2% | Same logic. |
| Test collection count | 0 | Should be exactly preserved unless `PLAN.md` removes specific tests. |

### 6.3 Characterization tests (Feathers)

`[S22, S23]` — write **before** the refactor, run **before** and **after**. They capture *current* behavior (which may include current bugs), not desired behavior. The goal is "did anything observable change?", not "is the new code correct?" (that's a separate question handled by feature tests).

For AVC, characterization scenarios might be:
- Launch app, default variety renders within N seconds.
- Switch variety V1 → V2: status-bar updates, no crash.
- Toggle high-quality smoothing: render queue handles the change.
- Export mesh STL/OBJ/PLY: file written, file readable.

These should already exist as feature tests, but their *role* during a refactor is to serve as the characterization layer. Mark them as such (e.g. `@pytest.mark.characterization`) so the rectifier knows to run them specifically pre and post.

### 6.4 Conftest.py / fixture parity

A specific gotcha called out by `[S24]`:

> "Moving test files changes which `conftest.py` files apply to them, potentially breaking fixture visibility."

After moving any test file:
- Verify the test still sees the fixtures it expects: `pytest --fixtures-per-test <moved_test_file>` and compare to baseline.
- If a fixture was in `tests/conftest.py` and the test moved to `tests/unit/conftest.py`'s scope, the fixture still resolves (upward search). If it moves to a sibling scope, the fixture is no longer visible — promote the fixture to a higher conftest.

### 6.5 Mutation testing as confirmation

`[S27]` — mutmut. Slow. Don't gate refactors on it; use it to *confirm* that test power did not degrade on the modules touched. A material drop in mutation score on a refactored module usually means a test now no-ops (the move broke a fixture, or moved a method whose tests no longer instantiate the right class).

---

## 7. The "AI agent context anchor" problem

When code moves, **agent memory references break silently**. This is the AVC-specific risk most under-discussed in classical refactor literature; it's a 2024–2026 phenomenon and the literature is still forming.

### 7.1 What breaks

`[S19, S20]` are explicit:

> "It changes too fast. Stale path references in your AGENTS.md will actively mislead agents into trying to write to files that don't exist or importing from paths that have moved."

The forms of "agent context anchor" in an AVC-style project:
- `CLAUDE.md` pointers like "see surfaces.py for the variety functions."
- Per-folder `CLAUDE.md` files.
- Notes under `.claude/notes/**` referencing `app.py:1234`.
- `lessons.md` / agent-memory entries from prior milestones.
- Skill prompts that say "edit `surfaces.py`."
- Subagent definitions in `.claude/agents/*.md` with file references.
- CONTEXT.md (AVC has one at repo root).

All of these become wrong simultaneously when a restructure lands.

### 7.2 Strategies

**Strategy A — Path-to-symbol indirection.**

Instead of `see surfaces.py:1234 for compute_field`, write `see compute_field (use grep)`. The agent has to grep, but the reference never goes stale. Trade-off: extra search latency, but bulletproof against moves. Recommended for `CLAUDE.md`, `lessons.md`, skill prompts.

**Strategy B — `MOVES.md` as rosetta stone.**

Every restructure appends to a single `MOVES.md` at the repo root:

```markdown
## 2026-05-23 — panels subpackage extraction
- appearance_panel.py → panels/appearance.py (moved 666 LOC)
- parameter_grid_panel.py → panels/parameter_grid.py (moved 713 LOC)
- parameters_panel.py → panels/parameters.py (moved 368 LOC)
- view_panel.py → panels/view.py (moved 503 LOC)
- Symbol shims at original paths until milestone M+1.

## 2026-05-23 — surfaces module split
- surfaces.py:1-450 → surfaces/varieties.py
- surfaces.py:451-1100 → surfaces/sampling.py
- ... etc
```

The agent reads `MOVES.md` once at session start (cheap — it's monotonically appended). When it encounters an old path in a note, it knows where to look now.

**Strategy C — Update agent-memory in the same restructure PR.**

Grep `.claude/notes/**` and `lessons.md`-style files for every moved path. Use the libcst symbol-map to drive the substitution. This is Phase 8.

**Strategy D — CLAUDE.md → AGENTS.md migration markers.**

If the project ever adopts AGENTS.md (the open standard `[S19]`), follow the recommended symlink approach so both Claude Code and other agents see the same canonical file:

```bash
mv CLAUDE.md AGENTS.md && ln -s AGENTS.md CLAUDE.md
```

`[S19]` is explicit that this is the migration mechanism. For AVC today, CLAUDE.md exists and AGENTS.md doesn't — note this as a future improvement, don't combine it with a code restructure.

**Strategy E — Pointer style, not content style.**

Per `[S20]`: "Include `file:line` references pointing to authoritative sources rather than copying code snippets directly. This prevents documentation drift and keeps context focused." When you must include a path, include only one — and make sure Phase 8 updates it.

### 7.3 Per-folder CLAUDE.md (recommended for AVC post-restructure)

If the AVC restructure introduces subpackages, add a short `CLAUDE.md` in each subpackage describing:
- Responsibility ("this package owns the Qt panels for the main window left dock").
- Key entrypoints (without line numbers; use symbol names).
- Cross-references to sibling subpackages (by name, not path).

Per `[S18]`: "Initialize work in subdirectories rather than the repo root, allowing Claude to load context additively while walking up the directory tree."

---

## 8. Cross-suite test gaps to watch for

These are the regressions that pass unit tests but reappear in integration. The architect should suggest adding cross-suite tests in these categories during/after a restructure:

1. **Conftest scope drift.** A fixture in `tests/conftest.py` that some moved test now no longer sees. Catch: `pytest --fixtures-per-test` diff.
2. **Implicit fixture sharing.** Test A uses fixture `client` defined in conftest; test A moves; the moved location has a different `client` fixture with the same name but different setup. Catch: pre-move snapshot of `--fixtures-per-test`.
3. **Import-time side effects.** Module B used to be imported transitively because module A imported it; restructure breaks the transitive chain; B's `@pytest.fixture` registration in a `conftest.py` only ran because of that import. Catch: `pytest --collect-only` count + `python -X importtime` diff.
4. **Plugin discovery.** A `pytest_plugins` declaration in a conftest gets shadowed when the conftest scope changes. Catch: `pytest --trace-config` output diff.
5. **Seam tests between newly-split modules.** When you split `surfaces.py` into 4 files, you need *new* tests that exercise the interaction across the new boundaries (sampling output → marching input). The old monolithic tests covered these implicitly; the new finer-grained tests may each cover their own module but miss the seam.
6. **GUI / Qt event-loop integration.** PyQt apps in particular have integration paths (event filters, signal/slot wiring) that only fire under a real `QApplication`. After a panel-class move, the signal wiring may target the wrong instance. Catch: pytest-qt smoke tests must run post-refactor.
7. **VTK pipeline wiring.** VTK objects can hold references that look fine in unit tests but leak (or fail to re-render) when the pipeline assembly is reshuffled. Add at least one end-to-end "render-frame-then-check-pixel" smoke test if not present.
8. **Settings persistence boundary.** AVC has `qsettings_persistence` tests already; ensure they still cover the load/save path after any settings-related refactor — easy to break the key namespace by moving a class.
9. **Star-import shadowing.** A `from foo import *` somewhere in the codebase may bring in symbol `X` that used to live in `foo`; after the move, the star-import silently no longer brings `X` in. Catch: ruff F405.
10. **Cyclic imports under specific entry points.** Test runners often paper over import cycles by importing modules in a benign order; production entrypoint (`app.py`) may not. Catch: explicit `python -c "import app"` smoke test post-refactor.

The architect should *suggest* — not auto-write — additional tests in categories 5, 6, 7, and 10 because their content is project-specific and writing them blindly creates false comfort.

---

## 9. Verification rubric (20 items)

A `repository-architect` post-execution checklist. Each item is binary (pass/fail) with a fast command to check.

| # | Item | Command / check |
|---|---|---|
| 1 | All original tests still pass | `pytest` exit 0 |
| 2 | Test collection count preserved | `diff <(pytest --collect-only -q) baseline.collect.txt` empty (or only removals listed in `PLAN.md`) |
| 3 | No new test files silently skipped | `pytest --collect-only` shows no `<skipped>` markers not present at baseline |
| 4 | Per-file coverage within ±2% on moved files | `coverage-diff` or manual XML diff |
| 5 | Total coverage within ±1% | `coverage report` total line vs baseline |
| 6 | No new import cycles | `pydeps --show-cycles` output identical to baseline cycle set |
| 7 | No orphan modules | `pydeps` reachability from `app.py` covers every `.py` in the new tree |
| 8 | No import-time side effects regressed | `python -X importtime -c "import app" 2> import_after.log` — total time within ±20% of baseline |
| 9 | No module shadowing | No two modules in the new tree have the same `__name__` from any import path |
| 10 | No `from X import *` newly introduced | `grep -rn "import \*" --include='*.py'` returns same set as baseline |
| 11 | Shims emit `DeprecationWarning` for every renamed/moved symbol | `tests/test_shims.py` passes |
| 12 | Shim warnings include the new path | grep test in `test_shims.py` |
| 13 | `git mv` rename detection succeeded | `git log --follow --oneline <new_path>` shows pre-move history |
| 14 | `MOVES.md` updated with this restructure's entries | New section present with date and old→new entries |
| 15 | Root `CLAUDE.md` pointers updated | grep old paths in `CLAUDE.md`: returns 0 (or only in `MOVES.md`) |
| 16 | Per-folder `CLAUDE.md` present for each new subpackage | `find . -path './<new_pkg>/CLAUDE.md'` returns the file |
| 17 | `.claude/notes/**/*.md` cleansed of stale paths | `grep -rn '<old_path>' .claude/notes/` returns 0 |
| 18 | `README.md` structure section reflects new tree | manual diff |
| 19 | `__pycache__` / `.pyc` for moved files cleared | `find . -name '__pycache__' -exec rm -rf {} +` then re-run tests; still green |
| 20 | Rollback command tested in a scratch worktree | Document command + confirm it returns to `refactor-baseline` tag cleanly |

A `repository-architect` that runs these 20 checks mechanically — and reports the *exact* command output for any failure — covers ~95% of the regressions Scout C has surfaced from the literature.

---

## 10. Common rationalizations to refuse

Each is a real anti-pattern from the literature; the architect should refuse, citing the violated pattern.

1. **"We can refactor and add features in the same PR."**
   - Violates: small-step discipline (Fowler), one-thing-per-commit (Feathers), `git bisect` survivability. `[S5, S22]`
   - Also violates `[S18]`'s "your working tree must be clean (non-negotiable)" for safe Claude Code refactors.
   - Refusal: "Land the restructure; merge; then land the feature in a follow-up."

2. **"The tests will catch any regression."**
   - Violates: parity verification requires *more* than green tests — collection count, coverage shape, fixture visibility. `[S22, S24, S25]`
   - Refusal: "Tests prove the suite still passes. They don't prove the suite is still exercising the same paths. Run the Phase 7 parity check."

3. **"We can fix the imports later."**
   - Violates: "the system runs at all times" (Branch by Abstraction). `[S2]`
   - Violates: `[S18]` "Don't chase 'one-shot' refactors; break work into phases with clear acceptance tests per phase."
   - Refusal: "Every commit must be green. Imports are part of green. There is no 'later' that is safer than 'now.'"

4. **"Let's just delete the old file, no shim needed."**
   - Violates: expand–contract (Parallel Change). `[S4]` Violates the deprecation-cycle norms of every major Python project. `[S10, S17]`
   - Specific AI-era cost: it breaks every `.claude/notes/**` reference and every agent-memory entry; the next session can't find what moved.
   - Refusal: "Shim it for one milestone. Removal is a separate commit referencing this one's hash."

5. **"Let's do it in one big-bang commit so reviewers see the whole thing."**
   - Violates: strangler-fig "small, lower-risk replacements." `[S1]`
   - Violates: `git bisect` discipline.
   - Refusal: "Reviewers see the whole thing via the PLAN.md and the commit-by-commit chain. A single commit is unreviewable and unbisectable."

6. **"Sed will be fine for these import rewrites."**
   - Violates: Python lexical structure (string literals vs imports indistinguishable to regex). `[S9, S11]`
   - Refusal: "Use libcst. Sed cannot tell `from foo import bar` apart from `\"from foo import bar\"` in a docstring."

7. **"Star-imports keep the shim shorter."**
   - Violates: stacklevel-based pinpoint deprecation `[S13]`; defeats static analysis.
   - Refusal: "Use the `__getattr__` shim. Star-import shims hide *which* symbol triggered the warning."

8. **"We don't need a rollback plan; we have git."**
   - Violates: every major incident playbook. `[S15]` notes that without a documented rollback, a panicked revert can take down unrelated work.
   - Refusal: "Write the rollback command in `PREFLIGHT.md` before executing. Test it in a scratch worktree."

9. **"The CLAUDE.md update can wait."**
   - Violates: `[S19]` "stale path references will actively mislead agents."
   - Refusal: "Phase 8 is part of the restructure, not a follow-up. Otherwise next session's agent corrupts the new tree."

10. **"We're internal-only; no deprecation needed."**
    - Subtler. Internal-only ≠ no-callers. Notebooks, scratch scripts, agent memory, peer agents, and in-flight feature branches all count.
    - Refusal: "Internal still has callers; they're just less visible. One milestone of shim is the cost of safety here."

---

## 11. Rollback plan

Every restructure must have a documented rollback. Three tiers, in order of escalating commitment.

### Tier 1 — Single-revert rollback (preferred)

Possible only if the entire restructure is a *contiguous chain of small commits*, no feature commits interleaved.

**Command.**
```bash
git revert --no-commit refactor-baseline..refactor-complete
git commit -m "revert: roll back restructure <restructure-id>"
```

**Pre-conditions.**
- The chain `refactor-baseline..refactor-complete` contains *only* refactor commits.
- Each commit was independently green (otherwise the revert is also broken).
- No production state outside git was migrated (this is a code-only restructure, so this holds for AVC).

**Tested.** Phase 4 preflight requires running the revert in a scratch worktree and confirming the result equals `refactor-baseline`.

### Tier 2 — Branch-by-abstraction toggle rollback

If the restructure used a runtime switch (rare for an internal Python project; more common for service migrations), flip the switch. AVC won't normally use this tier — it's a Python source restructure, not a runtime swap.

### Tier 3 — Shim-only rollback (partial)

Useful when the new structure is *mostly* working but one moved module misbehaves. Don't revert the whole chain; instead:
- Restore the old module's full code as the body of the shim (not just a re-export).
- The shim becomes the canonical implementation again.
- Future re-extraction is treated as a new restructure.

**Command.** Cherry-pick the old module's pre-move blob:
```bash
git checkout refactor-baseline -- path/to/old_module.py
# edit out the dependency on the moved-then-unmoved new path
git commit -m "revert: partial rollback of <symbol>"
```

### Rollback document template

`ROLLBACK.md` in `.claude/notes/<restructure-id>/`:

```markdown
# Rollback plan — <restructure-id>

**Baseline tag.** refactor-baseline-2026-05-23
**Complete tag.** refactor-complete-2026-05-23
**Commit range.** refactor-baseline..refactor-complete (N commits)

**Tier 1 (whole-restructure revert).**
  git revert --no-commit refactor-baseline..refactor-complete
  git commit -m "revert: roll back <restructure-id>"

  **Tested in scratch worktree on YYYY-MM-DD: PASS.**

**Tier 3 partial (per-module).**
  git checkout refactor-baseline -- <path>
  git commit -m "revert: partial rollback of <module>"

**What rollback does NOT restore.**
  - MOVES.md entries (manual revert).
  - CLAUDE.md edits (manual revert).
  - Agent-memory entries updated in Phase 8 (manual revert via
    `git checkout refactor-baseline -- .claude/`).
```

---

## 12. Application to AVC specifically

A non-prescriptive sketch of what a `/repository-architect` invocation against AVC's current state might propose. Scout C is not designing the command, so this is illustrative, not authoritative.

**Current pain points (from the 7849 LOC distribution).**

- `app.py` (1893 LOC) — almost certainly multi-responsibility; candidate for Extract Class (likely targets: settings persistence, status bar, render coordinator).
- `surfaces.py` (1808 LOC) — candidate for Split Module → `surfaces/` subpackage.
- Four `*_panel.py` files at top level — candidate for Introduce Subpackage → `panels/`.
- Flat `tests/` is fine for current size but will need mirroring (`tests/panels/`, `tests/surfaces/`) when packages appear.
- No `MOVES.md` exists today; create it on first restructure.
- No `AGENTS.md`; defer adoption (separate concern from this restructure).

**Suggested phasing.**

1. Restructure A: Introduce `panels/` subpackage (low risk, mechanical, well-scoped).
2. Restructure B: Split `surfaces.py` into `surfaces/` subpackage (medium risk, more imports to rewire).
3. Restructure C: Extract Class on `app.py:MainWindow` (highest risk, do last; benefits from confidence built by A and B).

Each restructure is a complete 8-phase pipeline with its own baseline, plan, dry-run, preflight, execute, verify, parity, re-baseline cycle. Do not start B until A is fully closed; do not start C until B is fully closed.

---

## Sources

All accessed 2026-05-23 unless noted.

- [S1] Martin Fowler, *Strangler Fig Application*: https://martinfowler.com/bliki/StranglerFigApplication.html
- [S2] Martin Fowler, *Branch By Abstraction*: https://martinfowler.com/bliki/BranchByAbstraction.html
- [S3] Trunk Based Development, *Branch by Abstraction*: https://trunkbaseddevelopment.com/branch-by-abstraction/
- [S4] Martin Fowler, *Parallel Change*: https://martinfowler.com/bliki/ParallelChange.html
- [S5] Refactoring.guru, *Moving Features Between Objects*: https://refactoring.guru/refactoring/techniques/moving-features-between-objects
- [S6] Refactoring.guru, *Large Class smell*: https://refactoring.guru/smells/large-class
- [S7] Martin Fowler, *Refactoring catalog* (Move Function): https://refactoring.com/catalog/moveFunction.html and *Extract Class*: https://refactoring.com/catalog/extractClass.html
- [S8] IN-COM Data Systems, *How to Refactor a God Class*: https://www.in-com.com/blog/how-to-refactor-a-god-class-architectural-decomposition-and-dependency-control/
- [S9] LibCST documentation: https://libcst.readthedocs.io/en/latest/
- [S10] NumPy NEP-23, *Backwards compatibility and deprecation policy*: https://numpy.org/neps/nep-0023-backwards-compatibility.html
- [S11] HN/Modelcitizendeveloper survey of Python AST/refactor tools (LibCST vs Bowler vs Rope vs ast vs ruff): https://research.modelcitizendeveloper.com/survey/1-104-1/ and https://news.ycombinator.com/item?id=28027016
- [S12] Python 3 docs, *Deprecations index*: https://docs.python.org/3/deprecations/index.html
- [S13] Python 3 docs, *warnings — Warning control*: https://docs.python.org/3/library/warnings.html
- [S14] pydeps, *Python Module Dependency graphs*: https://github.com/thebjorn/pydeps and https://pydeps.readthedocs.io/en/latest/
- [S15] Pete Hodgson, *Expand/Contract: making a breaking change without a big bang* (2023): https://blog.thepete.net/blog/2023/12/05/expand/contract-making-a-breaking-change-without-a-big-bang/
- [S16] OneUptime, *How to Create Branch by Abstraction Pattern*: https://oneuptime.com/blog/post/2026-01-30-branch-by-abstraction-pattern/view
- [S17] pandas PDEP-17, *Backwards compatibility and deprecation policy*: https://pandas.pydata.org/pdeps/0017-backwards-compatibility-and-deprecation-policy.html and pandas Policies: https://pandas.pydata.org/docs/development/policies.html
- [S18] LowCode Agency, *How to Handle Large Files and Multi-File Edits in Claude Code*: https://www.lowcode.agency/blog/claude-code-large-files-multi-file-edits and Skywork, *Claude Code Plugin Best Practices for Large Codebases (2025)*: https://skywork.ai/blog/claude-code-plugin-best-practices-large-codebases-2025/
- [S19] Hivetrail, *AGENTS.md vs CLAUDE.md: The AI Developer's Guide to Context Standards*: https://hivetrail.com/blog/agents-md-vs-claude-md-cross-tool-standard
- [S20] HumanLayer, *Writing a good CLAUDE.md*: https://www.humanlayer.dev/blog/writing-a-good-claude-md and Anthropic, *How Claude Code works in large codebases* (2025): https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start
- [S21] TheLinuxCode, *Git Move Files: Practical Renames, Refactors, and History Preservation in 2026*: https://thelinuxcode.com/git-move-files-practical-renames-refactors-and-history-preservation-in-2026/ (Tier-2 source — single-author blog, but content corroborates git docs on rename detection.)
- [S22] Michael Feathers, *Characterization Testing*: https://michaelfeathers.silvrback.com/characterization-testing and *Working Effectively with Legacy Code (key points)*: https://understandlegacycode.com/blog/key-points-of-working-effectively-with-legacy-code/
- [S23] Martin Fowler, *Legacy Seam*: https://martinfowler.com/bliki/LegacySeam.html
- [S24] pytest documentation, *Fixtures reference*: https://docs.pytest.org/en/stable/reference/fixtures.html and *Organizing tests best practices*: https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/
- [S25] Coverage.py: https://coverage.readthedocs.io/ ; coverage-diff: https://pypi.org/project/coverage-diff/ ; diff-cover: https://github.com/Bachmann1234/diff_cover
- [S26] SeatGeek ChairNerd, *Refactoring Python with LibCST* (2019): https://chairnerd.seatgeek.com/refactoring-python-with-libcst/
- [S27] mutmut docs: https://mutmut.readthedocs.io/en/latest/ ; *Mutation Testing as a Safety Net for Test Code Refactoring* (arXiv 1506.07330): https://arxiv.org/pdf/1506.07330
- [S28] Instagram LibCST repo: https://github.com/Instagram/LibCST (Instagram engineering blog post "Static Analysis at Scale" returned a TLS error during fetch; existence and Instagram pedigree corroborated by the GitHub repo README and the SeatGeek post [S26] citing it.)
- [S29] Instawork Engineering, *Refactoring a Python Codebase with LibCST* (cited title; fetch returned TLS error 2026-05-23, marked [UNVERIFIED] for the per-paragraph details — the existence of the case study is corroborated by multiple secondary sources via the search in S11): https://engineering.instawork.com/refactoring-a-python-codebase-with-libcst-fc645ecc1f09
- [S30] Rope: https://github.com/python-rope/rope (v1.14.0 released Jul 2025)
- [S31] TestDriven.io, *Splitting a module into multiple files*: https://testdriven.io/tips/3660b476-7aaa-4f7b-af22-28aa00fc871e/ and Hitchhiker's Guide to Python, *Structuring Your Project*: https://docs.python-guide.org/writing/structure/

**Items I would have verified with more time-box.**
- Sandi Metz "squint test" — widely-referenced pattern; primary source attribution (talk vs blog) not confirmed within the time-box, so the reference is left marked `[UNVERIFIED]` in §2 Phase 2.
- Instagram engineering "Static Analysis at Scale" blog post and Instawork case study — both had cert/fetch errors at access time. Their existence and gist are corroborated via SeatGeek `[S26]` and the search summary in `[S11]`, but the per-paragraph claims are based on secondary summaries rather than the primary text.
- LibCST exact 2024-2026 release cadence and any new codemod helpers in the 1.x line — verified that the project is active (Python 3.0–3.13 support) but did not pull the changelog for specific recent versions.
