# Refactor-Pattern Brief — restructure-feature-subpackages-2026q2-r2

**Scout.** REFACTOR-PATTERN SCOUT (Phase 1 agent)
**Restructure.** restructure-feature-subpackages-2026q2-r2 — Feature-subpackage decomposition of AVC
**Authored.** 2026-05-23
**Seed briefs.** `.claude/notes/repository-architect-design/scout-c-safe-refactor.md` (design-phase original) and `.claude/notes/repository-architect/restructure-full-audit-2026q2-r1/audit/refactor-pattern-brief.md` (r1 brief — used as verified starting cache)
**Time-box.** ~30 min wall-clock
**Prior lessons incorporated.** `.claude/agent-memory/repository-architect-refactor-pattern-scout/lessons.md` (r1 lessons and CORRECTION block); `.claude/agent-memory/repository-architect-implementer/lessons.md` (batch-4 bisect-redness CORRECTION)

## Honesty conventions

- `[CONSENSUS]` = three+ independent reputable sources agree.
- `[CONTESTED]` = sources disagree.
- `[UNVERIFIED]` = author could not confirm from a primary source within the time-box.
- Every claim has an `[Sn]` citation. Sources listed at the end.

---

## AVC substrate (read from cache at 2026-05-23, post-r1)

From `.claude/notes/repository-architect/restructure-feature-subpackages-2026q2-r2/cache/loc.csv` and `tree.txt`:

**Current state after r1:** r1 (restructure-full-audit-2026q2-r1) has fully landed. The panels/ subpackage is in place with 4 moved files and 4 root-level shims. The repo now has:

- `panels/` subpackage: `appearance.py` (738), `parameter_grid_panel.py` (719), `view.py` (503), `parameters.py` (368), `__init__.py` (13)
- Root-level shims: `appearance_panel.py` (18), `parameter_grid_panel.py` (18), `parameters_panel.py` (18), `view_panel.py` (18)
- Still at root: `app.py` (1900), `surfaces.py` (1811), `icons.py` (373), `parameter_grid.py` (362), `render_worker.py` (225), `ui_helpers.py` (264), `styles.py` (708)
- Top-level navigation: `AGENTS.md` (5683 bytes), `CLAUDE.md` (5683 bytes, symlink to AGENTS.md), `CONTEXT.md` (84344 bytes), `MOVES.md` (2122 bytes)

**r2 scope per restructure_brief:**
1. `varieties/` subpackage extracted from `surfaces.py` — per-family submodules (`k3`, `enriques`, `calabi_yau`, `fano`), `_kernels.py` for 11 Numba @njit kernels, `_marching.py` for marching-cubes helpers, `varieties/registry.py` for `VARIETIES` dict + tooltips
2. `render/` subpackage: `render_worker.py` → `render/worker.py`
3. `cross_section/` subpackage: `view_panel.ViewPanel.clip_to_domain` → `cross_section.clip_to_domain`
4. `_qt/` subpackage: RENAME `panels/` → `_qt/panels/` PLUS move `icons.py`, `ui_helpers.py`, `styles.py` inside as `_qt/icons.py`, `_qt/helpers.py`, `_qt/styles.py`
5. `app.py` stays at root, no Extract Class in this restructure
6. `parameter_grid.py` stays at root or designer moves to `varieties/parameter_grid.py`

**Key import-graph facts** (from `imports-rough.json`):
- `surfaces.py` has no Qt/PySide6 imports — pure math + numba + numpy + pyvista. Clean seam.
- `render_worker.py` imports PySide6, dataclasses, pyvista, warnings. No surfaces import. Clean seam.
- `icons.py` imports PySide6, qtawesome, styles. Qt-only.
- `ui_helpers.py` imports PySide6, parameter_grid, styles, surfaces, typing. NOTABLE: imports `surfaces` — a move to `_qt/helpers.py` drags a dependency on surfaces into the `_qt/` tree.
- `styles.py` self-imports (circular?): `imports-rough.json` lists `"styles.py": ["styles"]` — this may be a self-reference artifact from the JSON snapshot; verify before planning.
- `parameter_grid.py` imports surfaces. If it moves to `varieties/parameter_grid.py`, the cycle `varieties/ → varieties/parameter_grid → varieties/` must be checked.
- Tests importing `surfaces` directly: `test_numba_field_kernels.py`, `test_mesh_generators.py`, `test_enriques_hq_smoothing.py`, `test_status_bar_bbox.py`, `test_grid_helpers.py`, `test_coarse_n.py`, `test_typical_ms.py`, `test_parameters_panel.py`, `test_parameter_grid.py`, `test_mesh_export.py` (via `pathlib` only), `test_styles_palette.py`

**AI-1..AI-15 invariants (inviolable — see `.claude/references/app-invariants.md`):**
- AI-2: test suite Qt-free (no pytest-qt). All characterization tests via `pv.OFF_SCREEN = True` (AI-3).
- AI-6: marching cubes for implicit surfaces only; parametric surfaces (Hanson) never go through marching cubes.
- AI-7: Hanson normals: `cell_normals=True, consistent_normals=False, auto_orient_normals=False`
- AI-8: `Surface`/`ParamSpec` dataclass contract (frozen registry) — `VARIETIES` dict must remain importable via `from varieties.registry import VARIETIES` (or `from surfaces import VARIETIES` via shim)
- AI-9: re-entrancy guard `self._computing` — travels with any render-path method
- AI-14: generator function contract: returns `pv.PolyData` or raises `ValueError`
- AI-15: math claim honesty — all docstrings must remain co-located with their generators

---

## 1. TL;DR — what a safe restructure pipeline MUST do

1. **Capture a baseline before touching anything.** Tests green, coverage measured, import graph snapshotted, `git status` clean. Without this you cannot prove parity afterwards. `[CONSENSUS — S1, S6, S8]`
2. **Propose the target tree explicitly, with deltas.** A diffable plan (old path → new path, file split with line ranges, new symbol homes) reviewed *before* any `git mv` runs. For r2, this means fully resolving the `_qt/` shim chain problem (see §5.6) and the `varieties/` family split before execution begins. `[S2]`
3. **Dry-run the import-graph impact without moving files.** Compute, against the existing tree, "if these moves were applied, what would break?" — orphan modules, new cycles, broken `from X import Y`, conftest scope drift. NOTE: `ui_helpers.py` imports `surfaces` — if it becomes `_qt/helpers.py`, that introduces a `_qt` → `varieties` edge; must be checked for cycles. `[S11, S14]`
4. **Execute in tiny commits with LibCST rewrite in the SAME commit as the `git mv`.** This is the r1 bisect-redness lesson: `git mv` alone leaves intermediate commits red. The `git mv + LibCST rewrite` is one logical unit. Each logical unit must leave tests green. Follow Parallel Change / expand–contract. `[CONSENSUS — S3, S4, S15, S16]` + `[r1-lesson-batch4-correction]`
5. **Re-baseline at the end and update every navigation anchor.** Coverage delta, import-graph delta, test-parity check, **plus** every agent-readable surface (`AGENTS.md`, `CLAUDE.md`, `MOVES.md`, `CONTEXT.md`, agent-memory `lessons.md`). The restructure is not done until agents working in the new tree can find their way around. `[S18, S19, S20]`

> **The thesis.** The technical refactor is the easy part. For r2, the distinctive risks are: (a) the `_qt/` rename of `panels/` and its interaction with the 4 existing r1 shims; (b) the `surfaces.py` god-module split across family lines, where 11 @njit kernels must remain importable by the test suite's `from surfaces import _<name>_field_kernel` pattern; (c) the recursive shim chain problem when panels/ moves to `_qt/panels/`.

---

## 2. The eight phases of a safe restructure

### Phase 1 — Baseline (snapshot, green, measured)

**Pattern.** Feathers' "establish characterization tests before changing legacy code." `[S22]`

**Mechanics.**
- `git status` clean — non-negotiable for source files. `.claude/notes/` and `.claude/agent-memory/` modifications are non-blocking per r1 lessons. `[S18]`
- Full test suite green. `pytest` exit 0.
- `coverage run -m pytest && coverage xml -o baseline-coverage.xml` — store under `.claude/notes/restructure-feature-subpackages-2026q2-r2/baseline/`.
- Snapshot import graph: `pydeps . --max-bacon=0 --noshow` plus `--show-deps` JSON dump. `[S14]`
- Snapshot symbol locations: for each public symbol in `surfaces.py`, `render_worker.py`, `icons.py`, `styles.py`, `ui_helpers.py`, `panels/*`: record `{symbol → path:line}`.
- `pytest --collect-only -q > baseline.collect.txt` — the test count must be preserved exactly through r2.
- Tag: `git tag refactor-r2-baseline-2026-05-23`.

**Exit criterion.** All artifacts exist on disk under the baseline directory. Tag is created.

**Failure if skipped.** Cannot prove test coverage shape, behavior, or import topology was preserved. "The tests still pass" is meaningless without a baseline. `[S22, S25]`

---

### Phase 2 — Propose (target tree, file moves, file splits)

**Pattern.** Fowler's catalog operations made explicit before execution. `[S5, S7]`

**Mechanics.**
- Produce `PLAN.md` with three sections:
  1. **Tree diff.** Old tree → new tree. For r2, this covers: `surfaces.py` → `varieties/` subpackage (7 new files); `render_worker.py` → `render/worker.py` (1 move); `icons.py` → `_qt/icons.py` (1 move); `ui_helpers.py` → `_qt/helpers.py` (1 move); `styles.py` → `_qt/styles.py` (1 move); `panels/` → `_qt/panels/` (subpackage rename); `clip_to_domain` extraction; `parameter_grid.py` decision.
  2. **Symbol map.** For each symbol being moved or split: source `path:line` → target `path:line`. Use LibCST `MetadataProvider` to enumerate top-level definitions reliably. `[S9]`
  3. **Delta size.** Predicted LOC per new file; split ratios for `surfaces.py`.

- **R2-specific decisions that must be explicit (no TBDs):**
  - Does `parameter_grid.py` stay at root or move to `varieties/parameter_grid.py`? The import-graph shows it imports `surfaces` — if it moves to `varieties/`, the intra-package dependency is `varieties.parameter_grid → varieties` (OK). If it stays at root, callers update from `parameter_grid` to `parameter_grid` (no change). Designer must decide and document.
  - Does `ui_helpers.py` → `_qt/helpers.py` create a `_qt → varieties` cycle? `ui_helpers` imports `surfaces`. After the move, `_qt/helpers.py` would import `varieties` (the new home). That is OK — `_qt` may depend on `varieties` without creating a cycle as long as `varieties` does not import `_qt`. Verify in Phase 3.
  - What is the canonical import path for `VARIETIES` after r2? The brief says `from varieties.registry import VARIETIES`. The shim must forward `from surfaces import VARIETIES` to this.

**Exit criterion.** Reviewer can re-derive the new tree from `PLAN.md` alone. No "TBD" entries. The designer has resolved the `parameter_grid.py` location and the `ui_helpers` import chain.

**Failure if skipped.** Agent loses track of downstream files mid-session. The `_qt/` shim chain problem (Section 5.6) cannot be planned without an explicit PLAN. `[S18]`

---

### Phase 3 — Dry-run (import-graph delta without moving anything)

**Pattern.** Branch by Abstraction's "the system runs at all times," applied predictively. `[S2]`

**Mechanics.**
- Build the *predicted* import graph by mechanically applying the symbol-map to the current AST (LibCST can rewrite imports in memory without writing to disk). `[S9]`
- Diff predicted vs. baseline graph — check for:
  - **New cycles?** Particularly: `varieties/ → varieties/parameter_grid → varieties/` (if parameter_grid moves); `_qt/helpers → varieties` (already exists as `ui_helpers → surfaces`, so this edge is preserved, not new).
  - **Orphaned modules?** After `panels/` renames to `_qt/panels/`, the root-level shims (`appearance_panel.py` etc.) forward to `panels.X` — if `panels/` no longer exists as a top-level package, these shims break. This is the critical r2 dry-run check. See Section 5.6.
  - **`from surfaces import _<name>_field_kernel` in test files.** `test_numba_field_kernels.py` uses `from surfaces import _fermat_field_kernel` etc. After `surfaces.py` moves to `varieties/`, the root-level `surfaces.py` shim must forward these private names. Private names (`_` prefix) in `__getattr__` shims require explicit enumeration — they are NOT imported by `from X import *`.
  - **Fan-in > 20 on any single module?** Flag as god-module risk.
- For each test file, predict which `conftest.py` files apply after the move. `[S24]`
- Predict pytest collection delta: `pytest --collect-only -q` before vs. would-be after.

**Exit criterion.** A `DRY-RUN.md` with zero red flags, or a revised `PLAN.md` that addresses each flag. The `_qt/` shim chain and the `_field_kernel` forwarding problem must be explicitly resolved.

**Failure if skipped.** The `panels/` rename to `_qt/panels/` silently orphans the 4 existing r1 shims, causing `appearance_panel.py` to forward to a module that no longer exists. This is an invisible regression.

---

### Phase 4 — Pre-flight (shim plan, deprecation cycle, branch strategy)

**Pattern.** Parallel Change / expand–contract. `[S4]` NumPy NEP-23. `[S10]` pandas PDEP-17. `[S17]`

**Mechanics.**
- For every old import path that will move, decide: **shim or hard break?**
  - **Shim (default).** Old path stays importable; emits `DeprecationWarning`; routes to new location via `__init__.py __getattr__`. `[S12, S13]`
  - **Hard break (rare).** Only for genuinely private symbols (`_name`) never imported by name outside the package. EXCEPTION for r2: `test_numba_field_kernels.py` uses `from surfaces import _<name>_field_kernel` — these private symbols ARE imported by name in tests; the shim MUST forward them. Document this explicitly.

- **R2 shim inventory (full list, with template recommendation — see Section 5):**

  | Old path / symbol | New home | Template | Notes |
  |---|---|---|---|
  | `surfaces.py` (module shim at root) | `varieties/__init__.py` re-exports | Template 1 hub | Must forward all public AND the 11 `_*_field_kernel` private names for `test_numba_field_kernels.py` |
  | `render_worker.py` (module shim at root) | `render/worker.py` | Template 2 per-file | Standard move |
  | `icons.py` (module shim at root) | `_qt/icons.py` | Template 2 per-file | Standard move |
  | `ui_helpers.py` (module shim at root) | `_qt/helpers.py` | Template 2 per-file | Standard move; old name `ui_helpers`, new name `helpers` — shim must still be at `ui_helpers.py` |
  | `styles.py` (module shim at root) | `_qt/styles.py` | Template 2 per-file | Standard move |
  | `appearance_panel.py` (existing r1 shim) | Update forward target from `panels.appearance` → `_qt.panels.appearance` | Template 2 in-place update | r1 shim was: `from panels.appearance import ...`. After `panels/` moves to `_qt/panels/`, must change to `from _qt.panels.appearance import ...`. |
  | `view_panel.py` (existing r1 shim) | Update forward from `panels.view` → `_qt.panels.view` | Template 2 in-place update | Same as above |
  | `parameters_panel.py` (existing r1 shim) | Update forward from `panels.parameters` → `_qt.panels.parameters` | Template 2 in-place update | Same |
  | `parameter_grid_panel.py` (existing r1 shim) | Update forward from `panels.parameter_grid_panel` → `_qt.panels.parameter_grid_panel` | Template 2 in-place update | Same |
  | `panels/` package (OLD root; re-export shim) | `_qt/panels/` | Template 1 hub at `panels/__init__.py` (kept as shim) | After `git mv panels/ _qt/panels/`, leave `panels/__init__.py` as a shim that forwards `_qt.panels.*` for one milestone |

- **Deprecation timeline.** One milestone (M+1 after this restructure). `DeprecationWarning` only. Removal commit is separate, references this restructure's HEAD commit hash.
- Write rollback note in `PREFLIGHT.md` before executing.

**Exit criterion.** `PREFLIGHT.md` documents the full shim inventory, which shims are new vs. updated, the recursive shim chain resolution, and the rollback command.

**Failure if skipped.** The `_qt/` rename orphans the 4 existing shims silently. The `test_numba_field_kernels.py` `_field_kernel` forwarding is missed and tests fail.

---

### Phase 5 — Execute (the moves, in small commits)

**Pattern.** Fowler "small steps" discipline `[S5, S7]`; **r1 batch-4 bisect-redness lesson applied.** `[r1-lesson-batch4-correction]`

**Mechanics — CRITICAL RULE FROM R1.**

> **Each `git mv` must land in the same commit as its LibCST import rewrite.** A `git mv` alone is NOT a complete logical unit. Intermediate commits with moved files but unrewritten imports are bisect-red. The "one Fowler op per commit" rule means one user-visible refactor unit, not one mechanical action. `[r1-lesson-batch4-correction]`

Specifically for r2:
- `git mv surfaces.py varieties/_temp.py` (rename step 1) + create `varieties/__init__.py` + `varieties/k3.py` etc. + shim at `surfaces.py` + LibCST rewrite of all `from surfaces import X` → `from varieties.X import X` calls — ALL in one commit per family-file extracted OR all in a single large commit if the family splits are coupled.
- After every commit: (1) `pytest` exit 0; (2) `python -c "from surfaces import VARIETIES"` smoke test; (3) `python -c "from surfaces import _fermat_field_kernel"` smoke test the `_field_kernel` shim.

**R2 suggested batch sequence (low-risk-first, per design-adversary axis 10):**

| Batch | Operation | Risk | Shims created/updated |
|---|---|---|---|
| 1 | `render/` subpackage: `git mv render_worker.py render/worker.py` + LibCST rewrite + shim at `render_worker.py` | Low | 1 new (Template 2) |
| 2 | `cross_section/` subpackage: Extract `ViewPanel.clip_to_domain` as free function + `cross_section/__init__.py` | Low-Medium | 0 (new symbol, backward compat shim optional) |
| 3 | `varieties/` subpackage: Split `surfaces.py` → `varieties/` (7 files) + shim at `surfaces.py` (Template 1 hub with `_field_kernel` forwarding) | Medium-High | 1 new complex (Template 1 hub) |
| 4 | `_qt/icons`, `_qt/helpers`, `_qt/styles`: move 3 files + shims | Medium | 3 new (Template 2) |
| 5 | `_qt/panels/`: rename `panels/` → `_qt/panels/` + update 4 r1 shims + add `panels/` re-export shim + LibCST rewrite all `from panels.X` → `from _qt.panels.X` | Medium-High | 1 new hub + 4 r1 shim updates |
| 6 | `_qt/` package root `__init__.py` + AGENTS.md / CONTEXT.md / MOVES.md anchor update | Low | 0 |

**Use LibCST codemods for import rewrites — never `sed`.** `[S9, S11]`

**Exit criterion.** Every intended move/split landed; every commit is green standalone (`git bisect` survives); shims in place; `test_panels_shims.py` extended to cover all new shims.

**Failure if skipped (big-bang commit).** Per `[S1]`: big-bang is the original sin. `git bisect` is destroyed. Rollback is all-or-nothing.

---

### Phase 6 — Re-import-graph verify (no orphans, no cycles, no broken imports)

**Pattern.** "Continuous validation of dependency graphs." `[S8]` pydeps cycle detection. `[S14]`

**Mechanics.**
- Re-run `pydeps --show-cycles`. Compare to Phase-3 prediction. Any divergence is a yellow flag.
- Run `python -X importtime -c "import app"` and diff against baseline — large import-time spike indicates side-effect leak. **AVC-specific:** Numba's `workqueue` threading layer is set at `surfaces.py` import time (currently). After the move to `varieties/`, this side effect will fire when `varieties/__init__.py` imports from `varieties/_kernels.py`. Verify the threading-layer assignment still runs before the first kernel call.
- Run ruff for `F401` (unused import), `F811` (redefined), `F821` (undefined). `[S11]`
- Confirm no `from X import *` was introduced. (Current evaluator check 16: PASS — zero star-imports. Must remain PASS.)
- **AVC-specific `_field_kernel` check.** Run: `python -c "from surfaces import _fermat_field_kernel, _kummer_field_kernel, _enriques_fig1_field_kernel"` — these must still be importable from `surfaces` (via shim) for `test_numba_field_kernels.py`.

**Exit criterion.** Import graph matches Phase-3 prediction; zero ruff F-class errors; no import-time regression; Numba threading layer still set correctly; `_field_kernel` symbols importable from `surfaces` shim.

**Failure if skipped.** Numba threading-layer side effect moves to a later import and causes race conditions between VTK's SMP pool and Numba's thread pool (documented in CONTEXT.md §3).

---

### Phase 7 — Test parity verify (same tests run, same coverage shape, no silent skips)

**Pattern.** Coverage diff + characterization tests + mutation testing as confirmation. `[S25, S22, S27]`

**Mechanics.**
- `pytest --collect-only -q | wc -l` after vs. before. Count **must not decrease** unless a test file was deliberately removed (listed in PLAN.md).
- `coverage run -m pytest && coverage xml -o post-coverage.xml`. Diff against baseline:
  - Per-file coverage % delta: within ±2% for moved files.
  - Total lines covered: within ±1% of baseline.
  - Use `diff-cover` or `coverage-diff`. `[S25]`
- **AI-2 constraint.** Test suite is Qt-free (no pytest-qt). Characterization tests use `pv.OFF_SCREEN = True` (AI-3). Do not add Qt event-loop characterization tests.
- Characterization smoke: launch default variety → render (headless via `pv.OFF_SCREEN = True`); switch variety; toggle HQ smoothing; export STL. `[S22, S23]`
- Mutation testing: run `mutmut run` on `surfaces.py` equivalent modules (`varieties/k3.py`, `varieties/enriques.py` etc.) as *confirmation*, not gate. Score drop > 2% on a touched module warrants investigation. `[S27]`
- **Validate-shims.py gap.** The existing `validate-shims.py` script uses `import <mod>` for module-kind entries, which does NOT trigger `__getattr__` shims. Shim behavior must be verified via the test recipe (`from <mod> import <Symbol>` with `warnings.catch_warnings`) rather than via the script for module-kind shims. Extend `tests/test_shims.py` (or `test_panels_shims.py`) to cover all new r2 shims using the `catch_warnings(record=True)` pattern. `[r1-lesson-validate-shims-gap]`

**Exit criterion.** Collection count preserved; per-file coverage within tolerance; total coverage within tolerance; mutation score within tolerance; characterization smoke passes; all new shims covered in `test_shims.py`.

**Failure if skipped.** "All tests pass" hides "20 tests silently no-op because their conftest.py is in the wrong directory now." Also hides the validate-shims.py gap: `import surfaces` succeeds (the shim file exists) but `from surfaces import VARIETIES` silently returns `None` if the `__getattr__` hub is broken.

---

### Phase 8 — Re-baseline (navigation docs, AGENTS.md/CLAUDE.md, agent memory)

**Pattern.** "Agent context anchor" repair; pointer-based `CLAUDE.md` per `[S20]`.

**Mechanics.**
- Append entry to `MOVES.md`: `{from_path}:{from_line_range} → {to_path}:{to_line_range}` for every moved symbol. For r2, this is ~15-20 new entries.
- Update root `AGENTS.md` (and `CLAUDE.md` symlink): refresh the "key modules" pointer table. Per `[S19, S20]`: keep this pointer-based, never embed content. Specifically update:
  - `surfaces.py` pointer → `varieties/` package pointer
  - `render_worker.py` pointer → `render/worker.py`
  - `icons.py`, `ui_helpers.py`, `styles.py` pointers → `_qt/` paths
  - `panels/` pointer → `_qt/panels/` pointer
- For each new subpackage, add a per-folder `CLAUDE.md` describing responsibility, key entrypoints (by symbol name, not line number), cross-references, and any inviolable invariants.
  - `varieties/CLAUDE.md` must note AI-6 (marching cubes for implicit only), AI-7 (Hanson normals), AI-8 (VARIETIES registry contract), AI-14 (generator return contract), AI-15 (math claim honesty).
  - `render/CLAUDE.md` must note AI-9 (re-entrancy guard travels with render path).
  - `_qt/CLAUDE.md` must note AI-2 (no pytest-qt), AI-9 (re-entrancy guard), AI-11 (fully-qualified Qt enums), AI-12 (WCAG AA contrast), AI-13 (6-digit hex only).
  - `cross_section/CLAUDE.md` must note AI-4 (`clip_scalar` not `clip_box`), AI-5 (scalars= keyword), AI-10 (raw mesh cached).
- Walk `.claude/notes/**/*.md` and agent-memory files; grep for old paths; update using `MOVES.md` as lookup table.
- Update `CONTEXT.md` repo structure section (authorized for r2 per restructure_brief).
- Update `README.md` repo structure section.
- Re-tag: `git tag refactor-r2-complete-2026-05-23`.

**Exit criterion.** Grep for any old path across all `.md` files in the repo returns zero hits (except inside `MOVES.md` itself, which is the intended sink). Per-folder `CLAUDE.md` present for each new subpackage.

**Failure if skipped.** Future agent sessions will load stale `AGENTS.md`/`CLAUDE.md` pointers and try to `Read` paths that no longer exist. Per `[S19]`: "stale path references will actively mislead agents."

---

## 3. Tooling matrix

| Tool | Language | What it does | Install footprint | License | AVC r2 applicability |
|------|----------|--------------|-------------------|---------|----------------------|
| **LibCST 1.8.6** | Python | Concrete syntax tree; preserves formatting; de-facto choice for import rewriting and codemods. Supports Python 3.0–3.14 (including 3.14 free-threaded). Active. `[S9, S26, S28]` | `pip install libcst` (native extension; pure Python fallback available) | MIT | **Primary.** All import rewriting, symbol renames, file splits. For r2: rewriting all `from surfaces import X` callers, all `from panels.X import Y` callers, all `from icons/ui_helpers/styles/render_worker import Z` callers. |
| **Rope 1.14.0** | Python | Project-wide refactor library: rename, move, extract, inline. Active (Jan 2026). `[S30]` | `pip install rope` | LGPL-3.0+ | Secondary. Useful for interactive `clip_to_domain` Move Method step. Less ergonomic than LibCST for bulk codemods. |
| **Bowler** | Python | Facebook's earlier safe-refactor tool. **Archived August 8, 2025 — CONFIRMED DEAD.** Maintainers explicitly recommend LibCST. `[S11]` | n/a — do not adopt | Apache-2.0 | **SKIP. Dead.** Gate note: any prior brief citing Bowler must be updated. |
| **ruff** | Python | Linter + autofix. `--fix` covers F401 (unused import), F811 (redefined), I001 (sort/dedupe imports), plus 700+ rules. De-facto 2026 standard. `[S11]` | `pip install ruff` (Rust binary) | MIT | **Primary verification.** Run after every commit during Execute phase. |
| **ast (stdlib)** | Python | Abstract syntax tree; does NOT preserve formatting. `[S9]` | stdlib | PSF | **Analysis only.** Use for pre-plan symbol enumeration (count symbols per family in `surfaces.py`). Never for rewriting. |
| **pydeps** | Python | Module dependency graph generator; `--show-cycles`; bytecode analysis. `[S14]` | `pip install pydeps` (graphviz for rendering) | BSD-2-Clause | **Primary** for Phase 3 dry-run and Phase 6 verify. Critical for detecting `varieties/ ↔ parameter_grid` cycle and `_qt → varieties` edge. |
| **coverage.py** | Python | Line + branch coverage; XML output diff-able with `diff-cover`. `[S25]` | `pip install coverage` | Apache-2.0 | **Primary** for Phase 7 parity. Likely already in AVC via pytest setup. |
| **diff-cover / coverage-diff** | Python | Mechanize the "what lines changed?" coverage comparison. `[S25]` | `pip install diff-cover` | varies | Run after Phase 7 to diff XML snapshots. |
| **mutmut** | Python | Mutation testing; flags tests that pass despite mutations. Slow. `[S27]` | `pip install mutmut` | BSD | **Confirmation tool** in Phase 7. Run selectively on `varieties/*.py` (the most complex split). |
| **pytest --collect-only** | Python | Lists tests without running them. `[S24]` | builtin to pytest | MIT | Free; every Phase 3 / Phase 7 run. |
| **git mv** | Git | Rename with `--follow`-friendly history. `[S21]` | builtin | GPL | **Required for every move.** Pair with LibCST rewrite in the SAME commit. |
| **validate-shims.py** | Python | AVC-specific script in `.claude/scripts/`. Validates shims emit `DeprecationWarning` via `from <mod> import <symbol>` subprocess calls. **KNOWN GAP:** for module-kind entries (`kind == "module"`), it uses `import <mod>` which cannot trigger `__getattr__` shims. `[r1-lesson-validate-shims-gap]` | local | MIT | Use for named-symbol shims. Do NOT rely on it for module-level shim validation — use `test_shims.py` pattern instead. |

**Net AVC r2 recommendation.** LibCST + ruff + pydeps + coverage.py + pytest. Optional: mutmut on `varieties/` modules. All MIT/Apache/BSD/PSF.

---

## 4. Pattern catalogue (r2-specific focus)

### 4.1 Move Function (free function relocation)

**When.** A free function is called more from module B than from its home module A. `[S5]`

**Mechanics.** Define the function in B with the same signature. Replace the body in A with a delegating call to B. Run tests. Update callers. Delete or shim the A version. `[S5]`

**Failure modes.**
- Function had implicit access to module-level state in A (a module-level constant).
- Function referenced by `getattr(module_a, "fn_name")` or by string — static analysis misses it.

**R2 example.** `_marching_cubes_to_polydata`, `_grid_to_polydata`, `_concat_polydata` in `surfaces.py` → `varieties/_marching.py`. These are helpers called by family generators. Move them to `_marching.py` FIRST before splitting the generators. All three are private (`_` prefix) but are tested indirectly via generator tests.

---

### 4.2 Move Method (extracting a method into a free function)

**When.** A method `Foo.bar()` is more naturally a free function with no `self` dependencies, or it interacts more with entities outside `Foo`. `[S5]`

**Mechanics (Fowler).** Add `bar` as a free function (possibly in a new module). Either turn `Foo.bar` into a delegating one-liner or remove it and update callers. `[S5]`

**Failure modes.** `self` references inside the method that don't trivially translate to parameters. Mocks/spies tied to `Foo.bar` in tests now miss.

**R2 example: `ViewPanel.clip_to_domain` → `cross_section.clip_to_domain`.**
- `ViewPanel.clip_to_domain` must be a pure function (no Qt state, no `self` reference to Qt widgets). Verify before moving.
- If `self` is only used to access `self._raw_mesh` (AI-10 — the raw mesh cache), the function must be promoted with `raw_mesh` as an explicit argument.
- The old `ViewPanel.clip_to_domain` becomes a one-liner delegating call: `return cross_section.clip_to_domain(self._raw_mesh, ...)`.
- Test in `tests/test_clip_domain.py`: verify it still imports correctly and passes.
- AI-4 invariant: `clip_scalar` not `clip_box` — must travel with the function.
- AI-5 invariant: `scalars=` keyword — must travel.

**Note on Fowler's "Extract Function".** When a method is extracted into a free function in another module, this is a combination of Fowler's *Extract Function* `[S7a]` followed by *Move Function* `[S7]`. Both must happen atomically in r2 to avoid a two-step bisect-red window.

---

### 4.3 Split Module (god-module decomposition by domain family)

**When.** A `.py` file has crossed the "two cognitive responsibilities" line; multiple domain families cohabitate. AVC's `surfaces.py` (1811 LOC) has K3, Enriques, Calabi–Yau (3-fold), and Fano families as distinct mathematical domains. The "squint test" fails. `[S31]` `[UNVERIFIED — primary Sandi Metz source not confirmed within time-box; pattern is real]`

**The "splitting by domain family" pattern.** This is a specialization of Split Module where the cohesion criterion is mathematical family, not merely code-level responsibility. Applicable when:
- Generators of one family never call generators of another family directly.
- Each family has its own set of `@njit` kernels.
- The families are named in the `VARIETIES` registry as distinct top-level keys.

This matches Domain-Driven Design's "bounded context" concept — each family is a bounded context within the `surfaces.py` god-module. `[S36]`

**Mechanics.**
1. Start with the SHARED infrastructure: extract `_marching.py` (marching-cubes helpers) and `_kernels.py` (all 11 @njit kernels) FIRST. These are depended-on by every family generator — extracting them first means the family splits can import from `varieties._marching` and `varieties._kernels` without creating intra-family cycles.
2. Convert `surfaces.py` → `varieties/` package in one commit: `git mv surfaces.py varieties/surfaces_temp.py` then create `varieties/__init__.py`. This preserves git blame via rename detection.
3. Extract one family at a time into dedicated submodules:
   - `varieties/k3.py`: `fermat_quartic`, `kummer_surface` + their `FERMAT_PARAMS`, `KUMMER_PARAMS` constants (~200 LOC of generators + params)
   - `varieties/enriques.py`: 4 enriques generators + params (~400 LOC)
   - `varieties/calabi_yau.py`: `calabi_yau_quintic`, `calabi_yau_cubic`, `calabi_yau_asymmetric`, `calabi_yau_dwork` + params + `_hanson_cross_section` helper (~400 LOC)
   - `varieties/fano.py`: 4 fano generators + params (~400 LOC)
   - `varieties/registry.py`: `VARIETIES`, `VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS` (~256 LOC)
   - `varieties/__init__.py`: re-exports all public names so `from surfaces import VARIETIES` (via shim) still works
4. The root `surfaces.py` shim (Template 1 hub) must forward ALL public names AND the 11 `_*_field_kernel` private names.

**Failure modes.**
- The `@njit` kernels have a process-global side effect: `numba.config.THREADING_LAYER = "workqueue"` is set at module import time in `surfaces.py`. After the move to `varieties/_kernels.py`, this assignment must be at the TOP of `_kernels.py` before any `@njit` decorator. If it is omitted, the threading layer may default to a different value and cause VTK/Numba SMP contention (CONTEXT.md §3).
- `test_numba_field_kernels.py` uses `from surfaces import _fermat_field_kernel` etc. These are private names. The Template 1 hub `__getattr__` shim must explicitly list all 11 `_*_field_kernel` names in its `_RENAMES` dict (or handle the `_` prefix in the dispatch logic). **Private names are NOT re-exported by `from X import *`.** They must be explicitly enumerated in the shim.
- `test_typical_ms.py` and `test_coarse_n.py` use `from surfaces import Surface, VARIETIES`. These are public names and will be forwarded by the standard `__getattr__` hub.
- Star-imports: if any caller does `from surfaces import *` (none currently per evaluator check), those would become unreliable. Verify with ruff F405. Currently zero — must stay zero.
- The file→directory conversion must happen in a single commit with git mv so rename detection survives (same as the r1 lesson for file splits). `[r1-lesson-batch4-correction]`

**Python example for the hub shim at root `surfaces.py`:**

```python
# surfaces.py — backward-compat shim, remove in milestone M+1
# Forwards ALL public names AND the 11 Numba @njit field kernels that
# tests/test_numba_field_kernels.py imports by private name.
_PUBLIC_NAMES = {
    # dataclasses / public API
    "ParamSpec": "varieties.ParamSpec",
    "Surface": "varieties.Surface",
    "should_render_on_drag": "varieties.should_render_on_drag",
    "dispatch_mode": "varieties.dispatch_mode",
    "FAST_RENDER_THRESHOLD_MS": "varieties.FAST_RENDER_THRESHOLD_MS",
    # registry
    "VARIETIES": "varieties.registry.VARIETIES",
    "VARIETY_TOOLTIPS": "varieties.registry.VARIETY_TOOLTIPS",
    "SUBTYPE_TOOLTIPS": "varieties.registry.SUBTYPE_TOOLTIPS",
    # generators (representative sample; full list in PLAN.md)
    "fermat_quartic": "varieties.k3.fermat_quartic",
    "kummer_surface": "varieties.k3.kummer_surface",
    "enriques_figure_1": "varieties.enriques.enriques_figure_1",
    # ... (all generators)
}
_PRIVATE_NAMES = {
    # These are imported by name in tests/test_numba_field_kernels.py
    "_fermat_field_kernel": "varieties._kernels._fermat_field_kernel",
    "_kummer_field_kernel": "varieties._kernels._kummer_field_kernel",
    "_enriques_fig1_field_kernel": "varieties._kernels._enriques_fig1_field_kernel",
    "_enriques_fig2_field_kernel": "varieties._kernels._enriques_fig2_field_kernel",
    "_enriques_fig3_field_kernel": "varieties._kernels._enriques_fig3_field_kernel",
    "_enriques_fig4_field_kernel": "varieties._kernels._enriques_fig4_field_kernel",
    "_dwork_field_kernel": "varieties._kernels._dwork_field_kernel",
    "_klein_cubic_field_kernel": "varieties._kernels._klein_cubic_field_kernel",
    "_segre_cubic_field_kernel": "varieties._kernels._segre_cubic_field_kernel",
    "_two_quadrics_field_kernel": "varieties._kernels._two_quadrics_field_kernel",
    "_sextic_double_solid_field_kernel": "varieties._kernels._sextic_double_solid_field_kernel",
    # helpers (private but may be referenced in tests)
    "_marching_cubes_to_polydata": "varieties._marching._marching_cubes_to_polydata",
    "_grid_to_polydata": "varieties._marching._grid_to_polydata",
    "_concat_polydata": "varieties._marching._concat_polydata",
}
_ALL_RENAMES = {**_PUBLIC_NAMES, **_PRIVATE_NAMES}

def __getattr__(name: str):
    import importlib
    import warnings
    target = _ALL_RENAMES.get(name)
    if target is None:
        raise AttributeError(f"module 'surfaces' has no attribute {name!r}")
    module_path, _, attr = target.rpartition(".")
    warnings.warn(
        f"surfaces.{name} is deprecated; import from {target} instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module(module_path), attr)
```

**Why `_PRIVATE_NAMES` must be explicit.** Python's `__getattr__` is called for any attribute access that fails normal lookup — including `_`-prefixed names. But the `from new import *` shortcut CANNOT be used in the shim body because `*` by definition skips `_`-prefixed names. The explicit enumeration is load-bearing for `test_numba_field_kernels.py`. `[CONSENSUS — Python data model; S32]`

---

### 4.4 Rename Subpackage (panels/ → _qt/panels/)

**When.** A subpackage's logical grouping has changed; the new parent makes the purpose clearer. `[S5]`

**Mechanics.**
- `git mv panels/ _qt/panels/` (Git treats directory renames as a set of file renames).
- Create `_qt/__init__.py` if not already present.
- Create `panels/__init__.py` as a re-export shim that forwards to `_qt.panels.*` (Template 1 hub form).
- Update the 4 existing r1 root-level shims (`appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py`) to forward to `_qt.panels.*` instead of `panels.*`.
- LibCST rewrite all `from panels.X import Y` → `from _qt.panels.X import Y` in `app.py` and tests.

**Failure modes.**
- **Existing r1 shims break silently.** The r1 shims at `appearance_panel.py` etc. forward to `panels.appearance` etc. After `panels/` moves to `_qt/panels/`, `panels.appearance` no longer exists — the shims raise `ModuleNotFoundError`. These shims MUST be updated in the SAME commit as the `git mv`. This is the single most dangerous operation in r2. `[r1-lesson-batch4-correction applied to shim chain problem]`
- **`panels/__init__.py` disappears.** When `git mv panels/ _qt/panels/` executes, Git moves all files including `panels/__init__.py` to `_qt/panels/__init__.py`. You must explicitly create a NEW `panels/__init__.py` as the re-export shim. If you forget this step, any caller of `from panels import X` gets `ModuleNotFoundError` immediately.
- **`tests/test_panels_shims.py` still tests the old r1 shims.** After r2, the old shims (`appearance_panel.py` etc.) now forward to `_qt.panels.*` not `panels.*`. Update the shim test to verify the double-hop chain: `appearance_panel` → `_qt.panels.appearance`.

---

### 4.5 Introduce Subpackage (render/, cross_section/, varieties/, _qt/)

**When.** Flat top-level layout has accumulated > 8–10 modules and a thematic grouping is obvious. `[S31]`

**Mechanics.** Create the subpackage directory with `__init__.py`. Move relevant modules in. Update imports. Shim each moved module's old path for one cycle.

**AVC r2 example — `render/` subpackage (low risk, good warm-up):**
- `git mv render_worker.py render/worker.py`
- Create `render/__init__.py` (module docstring, no re-exports needed unless callers import from `render` directly)
- Create root-level shim `render_worker.py` (Template 2)
- LibCST rewrite: `from render_worker import RenderWorker` → `from render.worker import RenderWorker` in `app.py`

**AVC r2 `_qt/` subpackage — underscore-prefix convention:**

The napari project (`github.com/napari/napari`) uses `_qt/` as the private Qt-implementation subpackage and `qt/` as the public Qt-interface package. `[S34, S35]` For AVC, which has no public API and uses Qt only internally, a single `_qt/` with no public `qt/` sibling is the appropriate pattern. This matches PEP 8's "single leading underscore = internal use" convention applied at the package level. `[S32, S33]`

**Community position on `_qt/` vs `private/` (2026).** `[UNVERIFIED — no definitive 2025/2026 PEP or community statement found; the napari precedent is real and influential in the scientific Python space]`
- `private/` is more verbose but loses the `_`-prefix's "not imported by `from X import *`" semantics (for packages, `import *` obeys `__all__` not prefix conventions, so this distinction is moot for packages).
- `_qt/` is shorter and signals "Qt framework adapter" more semantically.
- **Recommendation for AVC:** use `_qt/` following the napari precedent. Document the choice in `_qt/CLAUDE.md`.

---

### 4.6 Inline Class (not applicable in r2 — deferred from r1)

r2's brief explicitly excludes Extract Class on `app.py:MainWindow`. Inline Class (the inverse) is also not in scope.

---

### 4.7 Move Module

**When.** A module's logical home has changed. `[S5]`

**R2 applications:** `icons.py` → `_qt/icons.py`; `ui_helpers.py` → `_qt/helpers.py`; `styles.py` → `_qt/styles.py`. All standard Template 2 moves.

**Failure mode specific to `ui_helpers.py → _qt/helpers.py`:** The new module name is `helpers`, not `ui_helpers`. The shim at the old path `ui_helpers.py` must forward to the new module. LibCST rewrite must update `from ui_helpers import X` → `from _qt.helpers import X`. The `tests/test_debounce.py` imports `ui_helpers` directly — verify it is updated.

---

## 5. Shim / deprecation cycle

### 5.1 Canonical Python shim (Template 1 — hub pattern)

For packages where multiple symbols from multiple submodules need to be accessible at the old flat path. Derived from `[S12, S13]`. `[CONSENSUS]`

```python
# surfaces.py — backward-compat shim (Template 1 hub), remove in milestone M+1
# See varieties/__init__.py for the new home of all surface generators.
# NOTE: _PRIVATE_NAMES are explicitly enumerated because `_`-prefixed names
# cannot be forwarded via `import *`. Required for test_numba_field_kernels.py.
_RENAMES = {
    "ParamSpec": "varieties.ParamSpec",
    "Surface": "varieties.Surface",
    "VARIETIES": "varieties.registry.VARIETIES",
    "VARIETY_TOOLTIPS": "varieties.registry.VARIETY_TOOLTIPS",
    "SUBTYPE_TOOLTIPS": "varieties.registry.SUBTYPE_TOOLTIPS",
    "fermat_quartic": "varieties.k3.fermat_quartic",
    "kummer_surface": "varieties.k3.kummer_surface",
    # ... (complete list in PLAN.md symbol-map)
    # Private names explicitly enumerated (not re-exported by import *):
    "_fermat_field_kernel": "varieties._kernels._fermat_field_kernel",
    "_kummer_field_kernel": "varieties._kernels._kummer_field_kernel",
    "_enriques_fig1_field_kernel": "varieties._kernels._enriques_fig1_field_kernel",
    # ... (all 11 kernels + _marching helpers)
}

def __getattr__(name: str):
    import importlib
    import warnings
    target = _RENAMES.get(name)
    if target is None:
        raise AttributeError(f"module 'surfaces' has no attribute {name!r}")
    module_path, _, attr = target.rpartition(".")
    warnings.warn(
        f"surfaces.{name} is deprecated; use {target} instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module(module_path), attr)
```

**Use Template 1 when:** many symbols from many submodules need to be accessible at one old path. Apply to: `surfaces.py` shim, `panels/__init__.py` re-export shim (after rename to `_qt/panels/`).

### 5.2 Whole-module shim (Template 2 — per-file forwarder)

For single-file moves where the old path forwarded to one new path. `[S12, S13]`

```python
# render_worker.py — shim, remove in milestone M+1
def __getattr__(name: str):
    import warnings
    from render import worker as _new
    if hasattr(_new, name):
        warnings.warn(
            f"render_worker.{name} is deprecated; "
            f"import from render.worker instead.",
            DeprecationWarning, stacklevel=2)
        return getattr(_new, name)
    raise AttributeError(
        f"module 'render_worker' has no attribute {name!r}")
```

**Use Template 2 when:** a single module moved to a single new path with no name change. Apply to: `render_worker.py`, `icons.py`, `ui_helpers.py`, `styles.py`.

### 5.3 Updating existing shims (r1 shim chain problem)

This is the most AVC-specific pattern in r2. The r1 shims at `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py` currently forward to `panels.appearance`, `panels.view`, `panels.parameters`, `panels.parameter_grid_panel` respectively. After `panels/` renames to `_qt/panels/`, those targets no longer exist.

**Option A — Direct-target update (recommended).**
Update the r1 shims in the SAME commit as the `panels/` rename:

```python
# appearance_panel.py — shim (updated in r2 to forward via _qt.panels), remove in milestone M+1
def __getattr__(name: str):
    import warnings
    from _qt.panels import appearance as _new  # UPDATED from: panels.appearance
    if hasattr(_new, name):
        warnings.warn(
            f"appearance_panel.{name} is deprecated; "
            f"import from _qt.panels.appearance instead.",
            DeprecationWarning, stacklevel=2)
        return getattr(_new, name)
    raise AttributeError(
        f"module 'appearance_panel' has no attribute {name!r}")
```

**Option B — Recursive/chain shim (NOT recommended).**
Leave the r1 shims as-is; instead, add a `panels/__init__.py` hub shim that forwards `panels.X` → `_qt.panels.X`. This creates a two-hop chain: `appearance_panel` → `panels.appearance` → `_qt.panels.appearance`. The `__getattr__` mechanism does NOT automatically traverse multi-hop chains. Each hop is a separate `importlib.import_module()` + `getattr()` call. A two-hop chain means TWO DeprecationWarnings per access — one at each hop. This is confusing and violates the "pinpoint warning at the caller's site" intent of `stacklevel=2`. `[S13]`

**Decision: use Option A.** Update the 4 r1 shims directly in the same commit as the `panels/` rename. Option B (recursive chain) is technically possible but produces double-warning noise and should not be adopted. `[CONSENSUS from PEP 562 guidance; S32]`

### 5.4 `panels/__init__.py` re-export shim

After `git mv panels/ _qt/panels/`, create a NEW `panels/__init__.py` at the root level as a hub forwarder. This handles code that imports `from panels import AppearancePanel` (which was valid after r1 since panels/__init__.py had a hub).

```python
# panels/__init__.py — hub shim after panels/ → _qt/panels/ rename, remove in milestone M+1
_RENAMES = {
    "AppearancePanel": "_qt.panels.appearance.AppearancePanel",
    "ViewPanel": "_qt.panels.view.ViewPanel",
    "ParametersPanel": "_qt.panels.parameters.ParametersPanel",
    "ParameterGridPanel": "_qt.panels.parameter_grid_panel.ParameterGridPanel",
}

def __getattr__(name: str):
    import importlib
    import warnings
    target = _RENAMES.get(name)
    if target is None:
        raise AttributeError(f"module 'panels' has no attribute {name!r}")
    module_path, _, attr = target.rpartition(".")
    warnings.warn(
        f"panels.{name} is deprecated; use {target} instead.",
        DeprecationWarning, stacklevel=2,
    )
    return getattr(importlib.import_module(module_path), attr)
```

### 5.5 AVC deprecation timeline

- **Release cycle equivalent = "milestone."** Shim lives for one milestone after the move milestone.
- **`DeprecationWarning` only.** AVC has no end-user-facing import surface that would warrant `FutureWarning`. `[S10, S17]`
- **Removal commit is separate** from the move commit, lands in milestone M+1, references the move's commit hash.
- **R2 shim removal plan (for M+1 after r2 closes):** remove `surfaces.py` (hub shim); remove `render_worker.py`, `icons.py`, `ui_helpers.py`, `styles.py` (Template 2 shims); remove updated `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py` (updated r1 shims); remove `panels/__init__.py` (hub re-export shim). That is 9 shim files total.

### 5.6 Warning category cheat sheet `[S13]`

| Category | When |
|----------|------|
| `DeprecationWarning` | "You should change your code." Ignored by default except in `__main__`. Devs running tests will see it. **Use this for all r2 shims.** |
| `FutureWarning` | Behavior is changing (not a rename). Visible by default. Not needed for r2. |
| `PendingDeprecationWarning` | "This will be deprecated soon." Ignored by default. Rarely the right choice. |
| `UserWarning` | Default category. Avoid for refactor shims — use deprecation classes for searchability. |

### 5.7 Testing the shims

```python
# tests/test_shims.py — extend with these patterns for r2
import sys
import warnings
import pytest

def _reload_shim(module_name: str):
    """Clear module from sys.modules so catch_warnings gets a fresh import."""
    for k in list(sys.modules.keys()):
        if k == module_name or k.startswith(module_name + "."):
            del sys.modules[k]

def test_surfaces_shim_public_symbol():
    """surfaces.VARIETIES still accessible via shim."""
    _reload_shim("surfaces")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from surfaces import VARIETIES  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "surfaces.VARIETIES" in str(w.message)
        for w in caught
    )

def test_surfaces_shim_private_kernel():
    """Private _field_kernel symbols accessible via shim (test_numba_field_kernels.py guard)."""
    _reload_shim("surfaces")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from surfaces import _fermat_field_kernel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        for w in caught
    )
    assert _fermat_field_kernel is not None

def test_render_worker_shim():
    _reload_shim("render_worker")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from render_worker import RenderWorker  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "render_worker" in str(w.message)
        for w in caught
    )

def test_panels_chain_still_works_after_rename():
    """appearance_panel shim still resolves after panels/ → _qt/panels/ rename."""
    _reload_shim("appearance_panel")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from appearance_panel import AppearancePanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "_qt.panels.appearance" in str(w.message)
        for w in caught
    )
```

**Critical note.** The `_reload_shim()` / `sys.modules.pop()` pattern is required in the test to get a fresh import. Without it, `catch_warnings` gets a no-op because the module is already cached in `sys.modules` from a prior import (without the warning firing again). This is the r1 batch-4 shim testing lesson. `[r1-lesson-batch4-shimtest]`

**validate-shims.py gap.** The AVC-specific `validate-shims.py` script uses `import <mod>` for module-kind entries. This form does NOT trigger `__getattr__` because `import <mod>` calls `importlib.import_module()` on the module object directly — it succeeds as long as the shim file exists, without accessing any attribute. The `__getattr__` hook is only called when accessing an attribute on an already-imported module (i.e. `from <mod> import <symbol>` or `import <mod>; <mod>.symbol`). **Therefore:** validate-shims.py's PASS result for a module-kind shim means only "the file exists and is importable," NOT "the `__getattr__` shim correctly forwards attributes." Always supplement with `test_shims.py` tests. `[r1-lesson-validate-shims-gap]`

---

## 6. Test parity verification

### 6.1 Two-snapshot pattern

1. **Pre-snapshot.** Tag `refactor-r2-baseline`. Persist:
   - `pytest --collect-only -q > baseline.collect.txt`
   - `coverage xml -o baseline.coverage.xml`
   - `mutmut run` baseline on `surfaces.py` (optional; before the split)
2. **Execute restructure (all batches).**
3. **Post-snapshot.** Same artifacts at `refactor-r2-complete`.
4. **Diff.**
   - **Collection diff.** Test IDs in pre but not post → either deliberately removed (must be in PLAN.md) or silently lost (regression).
   - **Coverage diff per file.** `diff-cover` or `coverage-diff`. `[S25]`
   - **Mutation diff.** Score drop > 2% on `varieties/*.py` vs. baseline `surfaces.py` → investigate.

### 6.2 Coverage tolerances

| Signal | Tolerance | Interpretation |
|--------|-----------|----------------|
| Total LOC covered | ±1% | > 1% drop = tests no longer reaching previously-covered code. |
| Per-file coverage % | ±2% on moved files | Mechanical move shouldn't change coverage shape. |
| Branch coverage | ±2% | Same logic. |
| Test collection count | 0 | Must be exactly preserved unless PLAN.md removes specific tests. |

### 6.3 Characterization tests (Feathers) `[S22, S23]`

Write *before* the refactor, run *before and after*. For AVC:
- Launch app, default variety renders within N seconds (headless via `pv.OFF_SCREEN = True`, AI-3).
- Switch variety V1 → V2: status-bar updates, no crash.
- Toggle HQ smoothing: render queue handles the change.
- Export mesh STL/OBJ/PLY: file written, file readable.

**AI-2 constraint.** Test suite is Qt-free (no pytest-qt). Characterization tests must use pure NumPy/PyVista paths.

### 6.4 Conftest.py fixture parity gotcha `[S24]`

Moving test files changes which `conftest.py` files apply to them. AVC tests currently all live in `tests/` (flat, no subdirectories). After r2, no test files are moved — only source files. This means the conftest scope drift risk is LOW for r2. However, after a source move, any test that was indirectly exercising `surfaces.py` via a transitive import chain (e.g. `test_clip_domain.py` imports `panels.view` which eventually imports `surfaces`) must still reach the right module. Verify via `python -X importtime` diff.

### 6.5 Mutation testing as confirmation `[S27]`

Run `mutmut run` selectively on `varieties/*.py` after the split. A material drop in mutation score vs. baseline `surfaces.py` score indicates a test now no-ops — likely because a test was indirectly depending on some `surfaces.py` module-level state that no longer fires at import time.

### 6.6 AVC-specific: `_field_kernel` access pattern in `test_numba_field_kernels.py`

`test_numba_field_kernels.py` imports private kernel functions by name: `from surfaces import _fermat_field_kernel`. After the shim is in place, this pattern still works via `__getattr__`. But it also means that running the test WILL trigger a DeprecationWarning per kernel import. This is expected behavior and should not be treated as a test failure. If the test suite has `-W error` configured in `pytest.ini`, it will fail when the shim emits the warning. Verify `pytest.ini` warning filters before r2 executes — if `-W error::DeprecationWarning` is active, you must either:
- Add a `filterwarnings = ignore::DeprecationWarning:surfaces` marker to `pytest.ini`, OR
- Update `test_numba_field_kernels.py` to import from `varieties._kernels` directly (the canonical path).

The second option is better long-term but requires the shim to be in place first, then the test to be updated in a separate commit.

---

## 7. The AI agent context-anchor problem

### 7.1 What breaks when r2 lands

R2 moves approximately 8-10 source modules and introduces 5 new subpackages. All of the following become stale simultaneously:

- `AGENTS.md` / `CLAUDE.md` pointers (e.g. "see `surfaces.py` for the variety functions" → now in `varieties/`)
- `CONTEXT.md` (84KB — extensive cross-references to `surfaces.py` by file and line number)
- `.claude/notes/**/*.md` files (scout reports, design docs, evaluator reports from prior runs)
- `.claude/agent-memory/repository-architect-*/lessons.md` files
- Skill prompts and subagent definitions that say "edit `surfaces.py`" or "see `render_worker.py`"
- Per `[S19]`: "Stale path references in your AGENTS.md will actively mislead agents into trying to write to files that don't exist or importing from paths that have moved."

### 7.2 Five strategies (same as r1, with r2-specific notes)

**Strategy A — Path-to-symbol indirection.**
Instead of `see surfaces.py:1234 for compute_field`, write `see compute_field (use grep)`. Recommended for `AGENTS.md`, `lessons.md`, skill prompts. `[S19, S20]`

**Strategy B — `MOVES.md` as rosetta stone.**
Append to `MOVES.md` at the repo root. For r2, expected entries include:

```markdown
## 2026-05-XX — Feature subpackage decomposition (r2)
- surfaces.py:1-1811 → varieties/ subpackage
  - surfaces.py:1-100 → varieties/__init__.py (public re-exports + dataclasses)
  - surfaces.py:295-684 → varieties/_kernels.py (11 @njit field kernels)
  - surfaces.py:686-748 → varieties/_marching.py (_marching_cubes_to_polydata, _grid_to_polydata, _concat_polydata)
  - surfaces.py:749-879 → varieties/k3.py (fermat_quartic, kummer_surface)
  - surfaces.py:899-1082 → varieties/enriques.py (4 enriques generators)
  - surfaces.py:1087-1320 → varieties/calabi_yau.py (3 Hanson generators + dwork + _hanson_cross_section)
  - surfaces.py:1328-1555 → varieties/fano.py (4 fano generators)
  - surfaces.py:1555-1811 → varieties/registry.py (VARIETIES, VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS)
  - Root shim surfaces.py remains; emits DeprecationWarning; removal in M+1.
- render_worker.py → render/worker.py (225 LOC)
  - Root shim render_worker.py remains; removal in M+1.
- icons.py → _qt/icons.py (373 LOC)
- ui_helpers.py → _qt/helpers.py (264 LOC) [NOTE: module renamed to helpers]
- styles.py → _qt/styles.py (708 LOC)
- panels/ → _qt/panels/ (rename)
  - Root-level panels/__init__.py re-export shim added; removal in M+1.
  - 4 r1 root-level shims updated to forward to _qt.panels.* instead of panels.*
- cross_section/clip_to_domain extracted from panels/view.ViewPanel.clip_to_domain
  - Old method becomes a delegating one-liner; full function at cross_section/clip_to_domain.
```

**Strategy C — Update agent-memory in the same restructure PR.**
Grep `.claude/notes/**` and `lessons.md`-style files for every moved path. Use the symbol-map to drive the substitution. This is Phase 8.

**Strategy D — AGENTS.md / CLAUDE.md symlink (already in place after r1).**
AVC already has `AGENTS.md` with `CLAUDE.md` as a symlink (r1 batch 2). Do not change this.

**Strategy E — Pointer style, not content style.**
Per `[S20]`: when you must include a path in a pointer file, include only one — and make sure Phase 8 updates it.

### 7.3 Per-folder CLAUDE.md for r2 new subpackages

Each new subpackage introduced in r2 must get a short `CLAUDE.md`:

- `varieties/CLAUDE.md`: responsibility ("math generators for K3, Enriques, CY3, Fano varieties"), key entrypoints (`VARIETIES`, `Surface`, family generator functions), CRITICAL invariants (AI-6, AI-7, AI-8, AI-14, AI-15), note about Numba threading layer side effect at import time.
- `render/CLAUDE.md`: responsibility ("async render worker; PySide6 signals; debounced queue"), key entrypoints (`RenderWorker`), CRITICAL invariant (AI-9 re-entrancy guard `_computing` must travel with any render-path method).
- `_qt/CLAUDE.md`: responsibility ("Qt/PySide6 UI adapter layer; everything in this package depends on Qt"), note (AI-2 — no pytest-qt; AI-11 — fully-qualified enums; AI-12 — WCAG AA contrast; AI-13 — 6-digit hex only).
- `cross_section/CLAUDE.md`: responsibility ("domain clipping pure functions; Qt-free"), CRITICAL invariants (AI-4 — clip_scalar not clip_box; AI-5 — scalars= keyword; AI-10 — raw mesh cached).

Per `[S18]`: "Initialize work in subdirectories rather than the repo root, allowing Claude to load context additively while walking up the directory tree."

---

## 8. Cross-suite test gaps specific to AVC r2

1. **Conftest scope drift.** AVC tests are flat under `tests/` — LOW risk for r2 since no test files move. Verify: `pytest --fixtures-per-test` diff is a no-op.

2. **Implicit fixture sharing.** Same — LOW risk for r2.

3. **Import-time side effects.** **HIGH risk for r2.** `surfaces.py` has a deliberate module-level side effect: `numba.config.THREADING_LAYER = "workqueue"`. After the move to `varieties/_kernels.py`, this must fire at the same point in the import chain. Verify: `python -X importtime -c "import app"` diff — the `varieties._kernels` import time should appear at roughly the same position as `surfaces` did before.

4. **Plugin discovery.** LOW risk — no `pytest_plugins` declarations affected by r2.

5. **Seam tests between newly-split modules.** **MEDIUM risk.** When `surfaces.py` splits into 7 files, the interaction across boundaries (e.g. `varieties.calabi_yau` calling `varieties._marching._marching_cubes_to_polydata`) is now a cross-module call instead of a same-module call. The old tests covered these implicitly. Consider adding at least one explicit "seam test" that instantiates a generator from each family module and calls `varieties._marching._marching_cubes_to_polydata` on its output directly.

6. **VTK pipeline wiring (AI-3, AI-4, AI-6, AI-7).** MEDIUM risk — `_hanson_cross_section` in `calabi_yau.py` calls `_grid_to_polydata` and `_concat_polydata`. After the split, these calls go to `varieties._marching` (cross-module). Add an explicit headless smoke test if not already present.

7. **Qt signal wiring (AI-9, AI-11).** LOW-MEDIUM risk for r2. The `_qt/panels/` rename changes the fully-qualified class names used in `app.py`'s signal wiring. After LibCST rewrite, all `from panels.X import Y` → `from _qt.panels.X import Y` calls must be complete. **AI-2 constraint applies:** no pytest-qt. The existing `test_clip_domain.py` which imports `panels.view.ViewPanel` must be updated to `_qt.panels.view.ViewPanel`.

8. **Settings persistence boundary (AI-10, AI-12).** LOW risk for r2 — `tests/test_qsettings_persistence.py` does not import from `surfaces`, `render_worker`, `icons`, `ui_helpers`, or `styles`. It should be unaffected.

9. **Star-import shadowing.** Currently zero star-imports (evaluator check PASS). Must remain zero after r2. Catch: `ruff check --select F405 .`

10. **Cyclic imports under production entrypoint.** **HIGH risk for r2.** The introduction of 5 new subpackages creates many new import edges. Run `python -c "import app"` after each batch to catch entrypoint-specific cycles. Specifically watch: `_qt.helpers` imports `varieties` (via the old `ui_helpers → surfaces` edge, now `_qt.helpers → varieties`); `_qt.panels.parameters` imports `varieties` (via `parameter_grid → surfaces`); `varieties.registry` imports nothing else in varieties. Run `pydeps --show-cycles` explicitly after r2 execute phase.

---

## 9. Verification rubric (20 items)

A post-execution checklist. Each item is binary (pass/fail) with a fast command.

| # | Item | Command / check |
|---|------|-----------------|
| 1 | All original tests still pass | `pytest` exit 0 |
| 2 | Test collection count preserved | `diff <(pytest --collect-only -q) baseline.collect.txt` empty (or only additions; no removals unless in PLAN.md) |
| 3 | No new test files silently skipped | `pytest --collect-only` shows no `<skipped>` markers not present at baseline |
| 4 | Per-file coverage within ±2% on moved files | `coverage-diff` or manual XML diff |
| 5 | Total coverage within ±1% | `coverage report` total line vs baseline |
| 6 | No new import cycles | `pydeps --show-cycles` output identical to baseline cycle set |
| 7 | No orphan modules | `pydeps` reachability from `app.py` covers every `.py` in the new tree |
| 8 | No import-time side effects regressed | `python -X importtime -c "import app" 2> import_after.log` — total time within ±20% of baseline; `numba.config.THREADING_LAYER` assignment still fires |
| 9 | No module shadowing | No two modules in the new tree have the same `__name__` from any import path |
| 10 | No `from X import *` newly introduced | `ruff check --select F405 .` returns same set as baseline (currently: zero) |
| 11 | New shims emit `DeprecationWarning` for every renamed/moved symbol | `tests/test_shims.py` passes for all r2 new shims |
| 12 | Updated r1 shims still emit `DeprecationWarning` with UPDATED new path | `tests/test_panels_shims.py` passes; messages reference `_qt.panels.*` not `panels.*` |
| 13 | `_field_kernel` private symbols accessible via `surfaces` shim | `from surfaces import _fermat_field_kernel` + catch_warnings passes |
| 14 | `git mv` rename detection succeeded | `git log --follow --oneline <new_path>` shows pre-move history for each moved file |
| 15 | `MOVES.md` updated with r2 restructure entries | New section present with date and old→new entries for all 10+ moves |
| 16 | Root `AGENTS.md` / `CLAUDE.md` pointers updated | Grep old paths in `AGENTS.md`: returns 0 (or only in `MOVES.md`) |
| 17 | Per-folder `CLAUDE.md` present for each new subpackage | `find . -path './<new_pkg>/CLAUDE.md'` returns files for `varieties/`, `render/`, `_qt/`, `cross_section/` |
| 18 | `.claude/notes/**/*.md` cleansed of stale paths | `grep -rn 'surfaces\.py\|render_worker\.py\|ui_helpers\.py\|icons\.py\|styles\.py' .claude/notes/` returns 0 (except MOVES.md) |
| 19 | `CONTEXT.md` structure section reflects new tree | manual diff — `CONTEXT.md` is authorized for r2 per restructure_brief |
| 20 | Rollback command tested in a scratch worktree | Document command + confirm it returns to `refactor-r2-baseline` tag cleanly |

**Additional r2-specific checks (items 21-25):**

| # | Item | Command / check |
|---|------|-----------------|
| 21 | `from varieties.registry import VARIETIES` works (AI-8 invariant) | `python -c "from varieties.registry import VARIETIES; print(list(VARIETIES.keys()))"` — should print 4 family keys |
| 22 | `test_numba_field_kernels.py` passes using `from surfaces import _field_kernel` path | `pytest tests/test_numba_field_kernels.py -v` exit 0 |
| 23 | Numba threading layer set correctly after `varieties` import | `python -c "import varieties; import numba; assert numba.config.THREADING_LAYER == 'workqueue'"` |
| 24 | No test imports `panels.X` instead of `_qt.panels.X` (after r2 LibCST rewrite) | `grep -rn "from panels\." tests/ --include='*.py'` returns 0 |
| 25 | `validate-shims.py` passes for all symbol-kind (non-module-kind) entries | `.venv/bin/python .claude/scripts/repository-architect/validate-shims.py restructure-feature-subpackages-2026q2-r2 --batch <N>` for each batch N |

---

## 10. Common rationalizations to refuse (r2-specific additions)

### 1. "We can refactor and add features in the same PR."
- Violates: small-step discipline (Fowler), one-thing-per-commit (Feathers), `git bisect` survivability. `[S5, S22]`
- Refusal: "Land the restructure; merge; then land the feature in a follow-up."

### 2. "The tests will catch any regression."
- Violates: parity verification requires more than green tests — collection count, coverage shape, fixture visibility. `[S22, S24, S25]`
- Refusal: "Tests prove the suite still passes. They don't prove the suite is still exercising the same paths."

### 3. "We can fix the imports later."
- Violates: "the system runs at all times" (Branch by Abstraction). `[S2]`
- Refusal: "Every commit must be green. Imports are part of green."

### 4. "Let's just delete the old files, no shims needed."
- Violates: expand–contract (Parallel Change). `[S4]`
- R2-specific cost: `test_numba_field_kernels.py` would immediately fail with `ModuleNotFoundError` because it still imports `from surfaces import _fermat_field_kernel`. The shim is NOT optional for this restructure.
- Refusal: "The test suite imports from the old paths by name. Shim it for one milestone."

### 5. "Let's do it in one big-bang commit."
- Violates: strangler-fig "small, lower-risk replacements." `[S1]`
- Violates: `git bisect` discipline.
- Refusal: "Reviewers see the whole thing via PLAN.md and the commit chain. A single commit is unreviewable and unbisectable."

### 6. "Sed will be fine for these import rewrites."
- Violates: Python lexical structure (string literals vs imports indistinguishable to regex). `[S9, S11]`
- Refusal: "Use LibCST. Sed cannot tell `from surfaces import X` apart from a string containing that phrase in a docstring."

### 7. "Star-imports keep the shim shorter."
- Violates: `stacklevel`-based pinpoint deprecation. `[S13]`
- R2-specific violation: `from varieties._kernels import *` would NOT export `_fermat_field_kernel` (star-import skips `_`-prefixed names). The test suite would break silently.
- Refusal: "Use the explicit `__getattr__` shim with named entries. Star-import shims skip private names."

### 8. "We don't need a rollback plan; we have git."
- Violates: every major incident playbook. `[S15]`
- Refusal: "Write the rollback command in PREFLIGHT.md before executing. Test it in a scratch worktree."

### 9. "The AGENTS.md/CLAUDE.md/CONTEXT.md updates can wait."
- Violates: `[S19]` "stale path references will actively mislead agents."
- Refusal: "Phase 8 is part of the restructure. CONTEXT.md is explicitly authorized for r2 updates. Otherwise next session's agent corrupts the new tree."

### 10. "The existing r1 shims don't need to be updated when panels/ renames."
- This is the r2-specific trap. The r1 shims forward to `panels.appearance` which will no longer exist after the rename. Leaving them un-updated is not "no change" — it is "silent breakage."
- Refusal: "The r1 shims must be updated in the SAME commit as the `git mv panels/ _qt/panels/`. An r1 shim forwarding to a moved package is broken by definition."

---

## 11. Rollback plan

Every restructure must have a documented rollback. Three tiers.

### Tier 1 — Single-revert rollback (preferred)

Possible only if the entire restructure is a contiguous chain of small commits with no feature commits interleaved.

```bash
git revert --no-commit refactor-r2-baseline..refactor-r2-complete
git commit -m "revert: roll back restructure-feature-subpackages-2026q2-r2"
```

**Pre-conditions.**
- The chain `refactor-r2-baseline..refactor-r2-complete` contains ONLY refactor commits.
- Each commit was independently green (bisect survives).
- No production state outside git was migrated.

**Tested in scratch worktree on YYYY-MM-DD: PASS / FAIL.** (Fill in before executing r2.)

### Tier 2 — Branch-by-abstraction toggle rollback

Not applicable to AVC's current Python source-only restructure.

### Tier 3 — Shim-only rollback (partial)

Useful when the new structure is mostly working but one batch misbehaves.

```bash
# Example: restore surfaces.py as the canonical implementation (revert batch 3 only)
git checkout refactor-r2-baseline -- surfaces.py
# Remove the varieties/ directory (all files)
git rm -r varieties/
# Restore the original surfaces.py content (it was at refactor-r2-baseline)
git commit -m "revert: partial rollback of varieties/ split in r2"
```

**Batch-level rollback tags (r2 protocol).** Each batch must be tagged at completion: `refactor-r2-batch1-end`, `refactor-r2-batch2-end`, etc. This enables cherry-pick-based partial rollback:

```bash
# Revert batch 5 (_qt/panels/ rename) while keeping batches 1-4:
git revert --no-commit refactor-r2-batch4-end..refactor-r2-batch5-end
git commit -m "revert: partial rollback of batch 5 (_qt/panels/ rename) in r2"
```

### Rollback document template

Store at `.claude/notes/restructure-feature-subpackages-2026q2-r2/ROLLBACK.md`:

```markdown
# Rollback plan — restructure-feature-subpackages-2026q2-r2

**Baseline tag.** refactor-r2-baseline-2026-05-XX
**Complete tag.** refactor-r2-complete-2026-05-XX
**Commit range.** refactor-r2-baseline..refactor-r2-complete (N commits)
**Batch tags.** refactor-r2-batch1-end .. refactor-r2-batch6-end

**Tier 1 (whole-restructure revert).**
  git revert --no-commit refactor-r2-baseline..refactor-r2-complete
  git commit -m "revert: roll back restructure-feature-subpackages-2026q2-r2"
  Tested in scratch worktree on YYYY-MM-DD: PASS / FAIL.

**Tier 3 partial (per-batch).**
  git revert --no-commit refactor-r2-batch{N-1}-end..refactor-r2-batch{N}-end
  git commit -m "revert: partial rollback of batch {N} in r2"

**What rollback does NOT restore.**
  - MOVES.md entries (manual revert).
  - AGENTS.md / CLAUDE.md / CONTEXT.md edits (manual revert).
  - Agent-memory entries updated in Phase 8:
    git checkout refactor-r2-baseline -- .claude/agent-memory/
```

---

## 12. AVC r2-specific application sketch

A non-prescriptive ordering for the designer. Structural moves before semantic extractions before content edits, per design-adversary axis 10.

### Batch 1 — `render/` subpackage (structural move, lowest risk)
- `git mv render_worker.py render/worker.py` + LibCST rewrite all `from render_worker import` → `from render.worker import` in `app.py` and tests + shim at `render_worker.py` (Template 2) — ALL in one commit.
- Expected: 1 shim created; ~5 import rewrites in `app.py`.
- Tag: `refactor-r2-batch1-end`

### Batch 2 — `cross_section/` subpackage (Move Method extraction, low-medium risk)
- Verify `ViewPanel.clip_to_domain` is pure (no `self` Qt state access beyond `_raw_mesh`).
- Create `cross_section/__init__.py` with `clip_to_domain` as a free function.
- Update `panels/view.ViewPanel.clip_to_domain` to delegate: `return cross_section.clip_to_domain(self._raw_mesh, ...)`.
- AI-4 and AI-5 invariants travel with the function body.
- LibCST rewrite callers of `ViewPanel.clip_to_domain` if any are outside `app.py` (check imports-rough.json — none found; `clip_to_domain` appears to be called only from within `panels/view.py` itself or `app.py`).
- Tag: `refactor-r2-batch2-end`

### Batch 3 — `varieties/` subpackage (surfaces.py split, medium-high risk)
- This is the highest-LOC operation. Proceed in sub-steps:
  1. Create `varieties/_kernels.py` with all 11 @njit kernels AND the Numba threading-layer config. Commit standalone (no git mv yet — just a new file).
  2. Create `varieties/_marching.py` with `_marching_cubes_to_polydata`, `_grid_to_polydata`, `_concat_polydata`. Commit standalone.
  3. Create `varieties/k3.py`, `varieties/enriques.py`, `varieties/calabi_yau.py`, `varieties/fano.py` with generator functions (importing from `varieties._kernels` and `varieties._marching`). Commit standalone.
  4. Create `varieties/registry.py` with `VARIETIES`, `VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS`. Commit standalone.
  5. Create `varieties/__init__.py` with public re-exports. Commit standalone.
  6. In ONE commit: `git mv surfaces.py surfaces_DELETED.py` (keeps blame) + write new root `surfaces.py` as Template 1 hub shim (with `_PRIVATE_NAMES` for 11 kernels) + LibCST rewrite all `from surfaces import X` → `from varieties.X import X` in ALL callers (app.py, tests, parameter_grid.py, panels/) + `rm surfaces_DELETED.py` (git rm).
     - NOTE: steps 1-5 are "pre-populate" commits that are green because they create NEW files not yet imported. They are low-risk. Step 6 is the atomic switch.
- Tag: `refactor-r2-batch3-end`

### Batch 4 — `_qt/icons`, `_qt/helpers`, `_qt/styles` (structural moves, medium risk)
- Three Template 2 moves + three root-level shims + LibCST rewrites.
- The `ui_helpers.py → _qt/helpers.py` rename requires extra care: the module is now named `helpers`, not `ui_helpers`. LibCST must rewrite `from ui_helpers import X` → `from _qt.helpers import X`.
- `styles.py` self-import artifact: verify `styles.py` does not actually import itself (the `imports-rough.json` entry `"styles.py": ["styles"]` is likely a pydeps artifact from stylesheet string constants containing the word "styles"). Verify before planning.
- Tag: `refactor-r2-batch4-end`

### Batch 5 — `_qt/panels/` rename (panels/ → _qt/panels/, medium-high risk)
- This is the riskiest structural operation because it touches the 4 existing r1 shims.
- In ONE commit:
  1. `git mv panels/ _qt/panels/`
  2. Create new `panels/__init__.py` hub shim (forwards `panels.X` → `_qt.panels.X`)
  3. Update 4 r1 shims (`appearance_panel.py` etc.) to forward to `_qt.panels.*`
  4. LibCST rewrite all `from panels.X import Y` → `from _qt.panels.X import Y` in `app.py`, `tests/`, and any other callers
- Post-commit smoke tests: `python -c "from appearance_panel import AppearancePanel"` — should emit DeprecationWarning; `python -c "from _qt.panels.appearance import AppearancePanel"` — should work silently.
- Tag: `refactor-r2-batch5-end`

### Batch 6 — Anchor update (lowest risk)
- Update `AGENTS.md` / `CLAUDE.md`, `CONTEXT.md`, `README.md` to reflect new tree.
- Create per-folder `CLAUDE.md` for `varieties/`, `render/`, `_qt/`, `cross_section/`.
- Append r2 section to `MOVES.md`.
- Grep and update `.claude/notes/**/*.md` and agent-memory files.
- Tag: `refactor-r2-complete-YYYY-MM-DD`

---

## Sources

All accessed or verified 2026-05-23 unless noted.

- [S1] Martin Fowler, *Strangler Fig Application*: https://martinfowler.com/bliki/StranglerFigApplication.html `[CONSENSUS]`
- [S2] Martin Fowler, *Branch By Abstraction*: https://martinfowler.com/bliki/BranchByAbstraction.html `[CONSENSUS]`
- [S3] Trunk Based Development, *Branch by Abstraction*: https://trunkbaseddevelopment.com/branch-by-abstraction/ `[CONSENSUS]`
- [S4] Martin Fowler, *Parallel Change*: https://martinfowler.com/bliki/ParallelChange.html `[CONSENSUS]`
- [S5] Refactoring.guru, *Moving Features Between Objects*: https://refactoring.guru/refactoring/techniques/moving-features-between-objects `[CONSENSUS]`
- [S6] Refactoring.guru, *Large Class smell*: https://refactoring.guru/smells/large-class `[CONSENSUS]`
- [S7] Martin Fowler, *Move Function*: https://refactoring.com/catalog/moveFunction.html `[CONSENSUS]`
- [S7a] Martin Fowler, *Extract Function*: https://refactoring.com/catalog/extractFunction.html `[CONSENSUS]`
- [S8] IN-COM Data Systems, *How to Refactor a God Class*: https://www.in-com.com/blog/how-to-refactor-a-god-class-architectural-decomposition-and-dependency-control/ `[UNVERIFIED — single-author blog; content corroborates Fowler and Feathers]`
- [S9] LibCST documentation: https://libcst.readthedocs.io/en/latest/ `[CONSENSUS]` — LibCST 1.8.6, supports Python 3.0–3.14 including 3.14 free-threaded; verified 2026-05-23 via PyPI and GitHub.
- [S10] NumPy NEP-23, *Backwards compatibility and deprecation policy*: https://numpy.org/neps/nep-0023-backwards-compatibility.html `[CONSENSUS]`
- [S11] Bowler archived status: https://github.com/facebookincubator/Bowler — **confirmed archived August 8, 2025**; maintainers recommend LibCST. `[CONSENSUS — confirmed gate; do not use Bowler]`
- [S12] Python 3 docs, *Deprecations index*: https://docs.python.org/3/deprecations/index.html `[CONSENSUS]`
- [S13] Python 3 docs, *warnings — Warning control*: https://docs.python.org/3/library/warnings.html `[CONSENSUS]`
- [S14] pydeps: https://github.com/thebjorn/pydeps `[CONSENSUS]`
- [S15] Pete Hodgson, *Expand/Contract*: https://blog.thepete.net/blog/2023/12/05/expand/contract-making-a-breaking-change-without-a-big-bang/ `[CONSENSUS]`
- [S16] OneUptime, *Branch by Abstraction Pattern*: https://oneuptime.com/blog/post/2026-01-30-branch-by-abstraction-pattern/view `[UNVERIFIED — single blog; corroborates Fowler S2]`
- [S17] pandas PDEP-17, *Backwards compatibility and deprecation policy*: https://pandas.pydata.org/pdeps/0017-backwards-compatibility-and-deprecation-policy.html `[CONSENSUS]`
- [S18] Skywork, *Claude Code Plugin Best Practices*: https://skywork.ai/blog/claude-code-plugin-best-practices-large-codebases-2025/ `[UNVERIFIED — single blog; content corroborates Anthropic documentation on CLAUDE.md patterns]`
- [S19] Hivetrail, *AGENTS.md vs CLAUDE.md*: https://hivetrail.com/blog/agents-md-vs-claude-md-cross-tool-standard `[UNVERIFIED — single blog; the AGENTS.md standard itself is real and widely adopted]`
- [S20] HumanLayer, *Writing a good CLAUDE.md*: https://www.humanlayer.dev/blog/writing-a-good-claude-md `[UNVERIFIED — single blog; content corroborates Anthropic documentation]`
- [S21] Git documentation on rename detection: https://git-scm.com/docs/git-diff#Documentation/git-diff.txt--Mltngt `[CONSENSUS]`
- [S22] Michael Feathers, *Characterization Testing*: https://michaelfeathers.silvrback.com/characterization-testing `[CONSENSUS]`
- [S23] Martin Fowler, *Legacy Seam*: https://martinfowler.com/bliki/LegacySeam.html `[CONSENSUS]`
- [S24] pytest documentation, *Fixtures reference*: https://docs.pytest.org/en/stable/reference/fixtures.html `[CONSENSUS]`
- [S25] Coverage.py: https://coverage.readthedocs.io/ ; diff-cover: https://github.com/Bachmann1234/diff_cover `[CONSENSUS]`
- [S26] SeatGeek ChairNerd, *Refactoring Python with LibCST*: https://chairnerd.seatgeek.com/refactoring-python-with-libcst/ `[CONSENSUS]`
- [S27] mutmut docs: https://mutmut.readthedocs.io/en/latest/ `[CONSENSUS]`
- [S28] Instagram LibCST repo: https://github.com/Instagram/LibCST `[CONSENSUS]`
- [S29] Instawork Engineering, *Refactoring a Python Codebase with LibCST*: https://engineering.instawork.com/refactoring-a-python-codebase-with-libcst-fc645ecc1f09 `[UNVERIFIED — fetch returned TLS error; existence corroborated by secondary sources]`
- [S30] Rope: https://github.com/python-rope/rope — v1.14.0 released Jul 2025; last updated Jan 2026. `[CONSENSUS — actively maintained]`
- [S31] TestDriven.io, *Splitting a module into multiple files*: https://testdriven.io/tips/3660b476-7aaa-4f7b-af22-28aa00fc871e/ `[UNVERIFIED — single blog; content corroborates Hitchhiker's Guide to Python]`
- [S32] Python PEP 8, *Style Guide for Python Code — Naming Conventions*: https://peps.python.org/pep-0008/ `[CONSENSUS]`
- [S33] Dan Bader, *The Meaning of Underscores in Python*: https://dbader.org/blog/meaning-of-underscores-in-python `[UNVERIFIED — single blog; content corroborates PEP 8]`
- [S34] napari GitHub repository, *package structure*: https://github.com/napari/napari `[CONSENSUS]` — napari uses `_qt/` for private Qt implementation and `qt/` for public Qt interface; confirmed by DeepWiki napari analysis and napari docs.
- [S35] napari documentation, *Architecture overview*: https://napari.org/dev/ and DeepWiki napari architecture: https://deepwiki.com/napari/napari `[UNVERIFIED for specific _qt/ claim — confirmed by search summary; primary napari source fetch not performed within time-box]`
- [S36] Domain-Driven Design reference for "bounded context": https://martinfowler.com/bliki/BoundedContext.html `[CONSENSUS]`

**Non-source internal references used in this brief:**
- `[r1-lesson-batch4-correction]` — `.claude/agent-memory/repository-architect-implementer/lessons.md` CORRECTION block: bisect-redness from sequential `git mv` + delayed LibCST rewrite in r1 batch 4. Lesson: LibCST rewrite must land in the SAME commit as `git mv`.
- `[r1-lesson-validate-shims-gap]` — `.claude/agent-memory/repository-architect-refactor-pattern-scout/lessons.md` and tool gap observed: `validate-shims.py` uses `import <mod>` for module-kind entries, which cannot trigger `__getattr__` shims. Must verify shim behavior via `catch_warnings` test recipe instead.
- `[r1-lesson-batch4-shimtest]` — `.claude/agent-memory/repository-architect-implementer/lessons.md` batch-4 lesson: `_reload_shim()` / `sys.modules.pop()` is required in shim tests to get a fresh import; without it, `catch_warnings` is a no-op.

**Tooling drift notes (2026-05-23 verification run).**
- Bowler confirmed archived August 8, 2025. `[GATE-REQUIRED — confirmed]`
- LibCST 1.8.6 current version; Python 3.14 + free-threaded support confirmed.
- Rope 1.14.0 (Jul 2025) confirmed actively maintained.
- ruff confirmed as de-facto 2026 standard.
- Sandi Metz squint test remains `[UNVERIFIED]` for primary source attribution.
- napari `_qt/` convention confirmed by search summary; specific GitHub file structure not directly verified (marked `[UNVERIFIED for specific claim]`).
