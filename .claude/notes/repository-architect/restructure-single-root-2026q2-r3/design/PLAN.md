# PLAN.md — restructure-single-root-2026q2-r3

**Authored:** 2026-05-24 main session (synthesis phase)
**Baseline:** 506 tests collected; HEAD = `c1dcf89`
**Brief:** make `app.py` the ONLY .py file at the repo root; tree-like dependency structure with import-linter enforcement.

---

## 1. Restructure goal

After r2, the repo has 7 root .py files (`app.py`, `parameter_grid.py`, plus 5 M+1-due shims) and a `surfaces.py` re-export hub that masquerades as a canonical module. r3 closes the M+1 deprecation cycle, moves the one remaining real-code root file (`parameter_grid.py`) into its consumer subpackage, retires `surfaces.py` entirely by rewriting all 23 active import sites to their canonical `varieties.*` paths, and locks in the layer-direction architecture with an import-linter contract. Target end-state: `ls *.py | wc -l == 1`.

Traceable to:
- current-state-auditor §9 "Tracked-but-misplaced files": 6 of the 7 root .py files flagged HIGH severity
- best-practices-scout focus area 5: napari's `_qt/` precedent confirmed HIGH for `_qt/parameter_grid_math.py`
- r2 design-adversary axis-12 patch: "PLAN must address scout evidence head-on" — the surfaces.py retirement is the direct follow-through on r2's deferral of full hub deletion
- r2 execution-critic MED-1: `rewrite-imports.py` partial-attribute-rewrite bug must be fixed BEFORE the next restructure (B1 of r3)

---

## 2. Tree diff (old → new)

```
BEFORE r3 (HEAD = c1dcf89, 7 root .py files):           AFTER r3 (target, 1 root .py file):
.                                                       .
├── app.py                              KEEP            ├── app.py
├── icons.py                            DELETE (B3)     ├── _qt/
├── parameter_grid.py                   MOVE (B2)       │   ├── __init__.py
├── render_worker.py                    DELETE (B3)     │   ├── icons.py
├── styles.py                           DELETE (B3)     │   ├── parameter_grid_math.py    ★ NEW (B2)
├── surfaces.py                         DELETE (B4)     │   ├── styles.py
├── ui_helpers.py                       DELETE (B3)     │   ├── ui_helpers.py
├── panels/                                             │   └── panels/
│   └── __init__.py                     DELETE (B3)     │       ├── __init__.py     (docstring updated B3)
├── _qt/                                MODIFY (B2)     │       ├── appearance.py
│   ├── __init__.py                                     │       ├── parameter_grid_panel.py
│   ├── icons.py                                        │       ├── parameters.py
│   ├── styles.py                                       │       └── view.py
│   ├── ui_helpers.py            ── rewrite import      ├── render/
│   └── panels/                                         │   ├── __init__.py
│       ├── __init__.py          ── docstring update    │   └── worker.py
│       ├── appearance.py                               ├── cross_section/
│       ├── parameter_grid_panel.py ── rewrite import   │   ├── __init__.py
│       ├── parameters.py        ── rewrite import      │   └── clip.py
│       └── view.py                                     ├── varieties/
├── render/                                             │   ├── __init__.py
│   ├── __init__.py                                     │   ├── types.py    ★ ADD VarietyGenerator Protocol (B2)
│   └── worker.py                                       │   ├── dispatch.py
├── cross_section/                                      │   ├── _kernels.py
│   ├── __init__.py                                     │   ├── _marching.py
│   └── clip.py                                         │   ├── k3.py
├── varieties/                          MODIFY (B2)     │   ├── enriques.py
│   ├── __init__.py                                     │   ├── calabi_yau.py
│   ├── types.py                 ── add Protocol        │   ├── fano.py
│   ├── dispatch.py                                     │   ├── registry.py
│   ├── _kernels.py                                     │   └── tooltips.py
│   ├── _marching.py                                    ├── tests/
│   ├── k3.py                                           │   ├── ...22 test files...
│   ├── enriques.py                                     │   └── test_import_smoke.py     ★ NEW (B5)
│   ├── calabi_yau.py                                   ├── pyproject.toml      ── add [tool.importlinter] (B5)
│   ├── fano.py                                         ├── MOVES.md            ── append r3 rosetta (B5)
│   ├── registry.py                                     ├── README.md           ── remove back-compat note (B5)
│   └── tooltips.py                                     ├── CONTEXT.md          ── update §4 module map (B5)
└── tests/                                              ├── CLAUDE.md           ── update "Where things live" (B5)
    ├── ...22 test files...                             └── requirements.txt    ── add import-linter (B5)
    └── test_r2_shims.py        DELETE (B3)             [zero test_r2_shims.py reference anywhere]
```

Counts: 7 root .py → 1 root .py. 5 shims deleted (4 root + 1 hub). 1 file moved (parameter_grid). 1 file retired (surfaces). 1 file added (`_qt/parameter_grid_math.py`). 1 protocol added in-place to existing file (`varieties/types.py`). 1 test file added (`tests/test_import_smoke.py`).

---

## 3. Symbol map

### B1 (tooling) — no symbol moves; bug fix only
| Symbol | From | To | Note |
|---|---|---|---|
| (CodemodCommand class) | `.claude/scripts/repository-architect/rewrite-imports.py` | (same) | Refactor to use `QualifiedNameProvider.has_name()` instead of string-matching; add `METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)`; guard multi-alias `leave_ImportFrom`; exclude `.claude/scripts/` and `.claude/notes/` from walk |

### B2 (parameter_grid move + Protocol add)
| Symbol | From | To | Caller-impact |
|---|---|---|---|
| Module `parameter_grid` (362 LOC, pure-math) | `parameter_grid.py` | `_qt/parameter_grid_math.py` | 4 callers (all alias-form `import parameter_grid as pg`) |
| Class `VarietyGenerator` (Protocol) | (new) | `varieties/types.py:69+` (after existing `Surface` dataclass) | Additive — zero existing callers |

### B3 (shim deletes) — no symbol moves
| Action | File | Reason |
|---|---|---|
| `git rm` | `icons.py` | M+1 cycle complete (re-export pointed at `_qt.icons`) |
| `git rm` | `styles.py` | M+1 cycle complete (re-export pointed at `_qt.styles`) |
| `git rm` | `ui_helpers.py` | M+1 cycle complete (re-export pointed at `_qt.ui_helpers`) |
| `git rm` | `render_worker.py` | M+1 cycle complete (re-export pointed at `render.worker`) |
| `git rm` | `panels/__init__.py` + `rmdir panels/` | M+1 cycle complete (hub shim pointed at `_qt.panels.*`) |
| `git rm` | `tests/test_r2_shims.py` | Tests cover shims that no longer exist |
| edit | `_qt/panels/__init__.py` | Update docstring to remove stale `from panels.X` examples (audit §5 finding) |

### B4 (surfaces.py retirement — 23 import sites)
| Symbol | From | To |
|---|---|---|
| `ParamSpec`, `Surface` | `surfaces` | `varieties.types` |
| `VARIETIES` | `surfaces` | `varieties.registry` |
| `VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS` | `surfaces` | `varieties.tooltips` |
| `dispatch_mode`, `should_render_on_drag`, `FAST_RENDER_THRESHOLD_MS` | `surfaces` | `varieties.dispatch` |
| `fermat_quartic`, `kummer_surface` (K3 generators) | `surfaces` | `varieties.k3` |
| `enriques_figure_1`, `enriques_figure_2`, … | `surfaces` | `varieties.enriques` |
| `calabi_yau_quintic`, `calabi_yau_*` (3 fns) | `surfaces` | `varieties.calabi_yau` |
| `fano_segre_cubic`, `fano_two_quadrics`, `fano_grassmannian` | `surfaces` | `varieties.fano` |
| 14 `*_PARAMS` constants | `surfaces` | `varieties.{k3,enriques,calabi_yau,fano}` (same family as their generator) |
| 11 `_<name>_field_kernel` private symbols | `surfaces` | `varieties._kernels` |
| `_marching_cubes_to_polydata`, `_grid_to_polydata`, `_concat_polydata`, `_hanson_cross_section` | `surfaces` | `varieties._marching` |
| Bare `import surfaces` (2 test files) | (module ref) | Refactor to specific `from varieties.X import Y` per use-site |
| `git rm` | `surfaces.py` | Hub retired |

Mirrored to `symbol-map.json` for the rewrite-imports.py codemod (flat-array schema with `{batch, operation, kind, from, to, symbol}` records per the existing codemod contract — 46 records: 1 for B2 + 45 for B4. Symbol names verified against `varieties/{k3,enriques,calabi_yau,fano,_kernels,_marching}.py` at HEAD c1dcf89 — the dry-run validator's initial pass caught 17 pre-r2 stale names + 23 missing entries against the original draft; these are corrected in the committed symbol-map.json).

### B5 (verify + lock-in) — no symbol moves
| Action | File | Purpose |
|---|---|---|
| anchor-updater | `CLAUDE.md`, `README.md`, `MOVES.md`, `CONTEXT.md` | Reflect single-root state + remove surfaces back-compat note |
| add | `pyproject.toml` `[tool.importlinter]` section | Layer-direction enforcement |
| add | `requirements.txt` `import-linter>=2.0,<3` | Tooling pin |
| add | `tests/test_import_smoke.py` | Cyclic-import smoke for `app`, `varieties`, `render`, `_qt`, `cross_section` (r2 test-suggester Suggestion 2) |
| verify | `ls *.py | wc -l == 1` | Single-root invariant |
| verify | `python -W error::DeprecationWarning -m pytest -q` | No live caller still routed through any shim |
| verify | `lint-imports` exits 0 | Layer-direction contract holds |

---

## 4. Delta size table

| File | Before LOC | After LOC | Delta | Notes |
|---|---|---|---|---|
| `parameter_grid.py` | 362 | 0 | -362 | Moved to `_qt/parameter_grid_math.py` |
| `_qt/parameter_grid_math.py` | 0 | 362 | +362 | New canonical home |
| `varieties/types.py` | 67 | ~85 | +18 | Add VarietyGenerator Protocol |
| `icons.py` | 23 | 0 | -23 | DELETE shim |
| `styles.py` | 22 | 0 | -22 | DELETE shim |
| `ui_helpers.py` | 27 | 0 | -27 | DELETE shim |
| `render_worker.py` | 23 | 0 | -23 | DELETE shim |
| `panels/__init__.py` | 40 | 0 | -40 | DELETE hub shim |
| `surfaces.py` | 123 | 0 | -123 | DELETE re-export hub |
| `_qt/panels/__init__.py` | 13 | ~10 | -3 | Docstring cleanup |
| `tests/test_r2_shims.py` | 108 | 0 | -108 | DELETE (shims gone) |
| `tests/test_import_smoke.py` | 0 | ~40 | +40 | New cyclic-import smoke |
| Call-site rewrites (19 files in B4, 4 in B2) | n/a | n/a | ~±0 | LibCST rewrites: each `from surfaces import X` → `from varieties.Y import X` is same line count |
| `pyproject.toml` | (no `[tool.importlinter]`) | +importlinter section | +~25 | Layers + forbidden contracts |
| `requirements.txt` | (no import-linter) | +1 line | +1 | `import-linter>=2.0,<3` |

**Net source-LOC delta:** approximately `-362 -23 -22 -27 -23 -40 -123 -3 -108 + 362 +18 +40 = -311 LOC` (removing ~311 lines of shim + hub + dead test for the same functional capability).

**Root-level .py count:** 7 → 1 (target).

---

## 5. Shim plan

**r3 introduces ZERO new shims.** All five existing shims are being deleted (`icons.py`, `styles.py`, `ui_helpers.py`, `render_worker.py`, `panels/__init__.py`) as the M+1 deprecation cycle closes per scout-B focus area 4 (NumPy NEP 29 + Django internal-API analog both satisfied — one minor cycle elapsed since r2).

### Why no new shim for `parameter_grid` → `_qt/parameter_grid_math`?

The four callers of `parameter_grid` are 100% in-tree:
- `_qt/ui_helpers.py:27`
- `_qt/panels/parameter_grid_panel.py:35`
- `_qt/panels/parameters.py:30`
- `tests/test_parameter_grid.py:18`

All four are rewritten by LibCST in B2. There are zero out-of-tree callers (no notebooks, no scratch scripts on the user's filesystem reference `parameter_grid`). A back-compat shim would be a deprecation surface for a name nobody outside this repo uses. Per scout-B focus area 4, deprecation cycles are for **public** APIs; `parameter_grid` is private-by-position (the script lived at the repo root only because it predated the `_qt/` subpackage). Direct move + LibCST rewrite is the correct technique.

### Why no new shim for `surfaces.py` retirement?

The 123-LOC `surfaces.py` shim has been live since r2 (one M+1 cycle complete). Per Phase 0 → Phase 3 sequence from refactor-pattern-scout Topic 1:

```
Phase 0 (r2) — surfaces.py reduced 1811 → 123 LOC as a hub shim
Phase 1 (r3 B4) — LibCST rewrites all 23 import sites to varieties.*
Phase 2 (r3 B4) — verify `python -W error::DeprecationWarning -m pytest -q` passes
Phase 3 (r3 B4) — git rm surfaces.py
```

After Phase 2 succeeds, no caller goes through the shim and the shim itself is dead code. Deletion is mandatory, not optional, per refactor-pattern-scout Topic 1's exit criterion.

### Shim deletion verification (run after each B3 + B4 step)

```bash
# After B3:
ls icons.py styles.py ui_helpers.py render_worker.py panels/__init__.py 2>&1 | grep -c "No such file" # expect 5
grep -r "import icons\|import styles\|import ui_helpers\|import render_worker" . --include="*.py" | grep -v "_qt/" | grep -v "render/" # expect empty

# After B4:
test ! -e surfaces.py
grep -r "import surfaces\|from surfaces" . --include="*.py" # expect empty
```

---

## 6. AI-invariant impact

| # | Invariant | r3 touch? | Mitigation |
|---|---|---|---|
| AI-1 | LGPL stack (PySide6/PyVista/Numba) | No | — |
| AI-2 | Qt-free tests | YES (B3) | Deleting `test_r2_shims.py` is compliant; new `test_import_smoke.py` uses subprocess pattern (no QApplication in current process). **Subprocess-safety evidence for `app` and `_qt` parametrize entries** (resolving the textual contradiction with refactor-patterns Topic 3's "DO NOT include app/_qt" warning): `app.py` is subprocess-safe because `QApplication()` is constructed inside `main()` guarded by `if __name__ == "__main__"` — `import app` in a child Python process does NOT instantiate Qt. `_qt/__init__.py` is subprocess-safe because it is docstring-only with zero import statements. Both confirmed by source inspection on c1dcf89. The scout's warning applies generically to subpackages that eagerly import Qt at module scope — AVC's `_qt/` is structured to defer Qt imports to leaf modules. |
| AI-3 | Headless render uses `pv.OFF_SCREEN = True` | No | — |
| AI-4 | Clip uses `clip_scalar` not `clip_box` | No | — |
| AI-5 | `clip_scalar(scalars=...)` | No | — |
| AI-6 | Implicit→marching cubes; parametric→structured grid | YES (B4) | All generator functions stay in `varieties/{k3,enriques,calabi_yau,fano}.py` which already segregate the pattern. Pipeline split is preserved because the implementation files don't move. |
| AI-7 | Hanson normals options | No | — |
| AI-8 | Surface/ParamSpec frozen dataclass + VARIETIES contract | YES (B2 + B4) | B2: VarietyGenerator Protocol is ADDITIVE — zero changes to Surface or ParamSpec fields. B4: callers move from `surfaces.VARIETIES` to `varieties.registry.VARIETIES` — registry shape unchanged. |
| AI-9 | `self._computing` re-entrancy guard in app.py | NO (adjacent) | Only `app.py`'s `from surfaces import ...` block at L49-63 is rewritten by LibCST. The guard logic is not touched. |
| AI-10 | Raw mesh cached in `self._raw_mesh` | No | — |
| AI-11 | Fully-qualified Qt enums | No (no new Qt code) | — |
| AI-12 | WCAG AA contrast | No | — |
| AI-13 | 6-digit hex for PyVista | No | — |
| AI-14 | Generators return PolyData or raise ValueError | No | — |
| AI-15 | Math-honest tooltips | No | — |

**Subtlety — numba.config side effect (refactor-pattern-scout Topic 1 final paragraph):** r2 confirmed `numba.config.THREADING_LAYER = "workqueue"` lives at the top of `varieties/_kernels.py` (verified by `test_r2_shims.py:test_surfaces_private_kernel_reexport_works` identity check). When `surfaces.py` is deleted in B4, the side effect remains because `_kernels.py` still runs the assignment at module import. B4 pre-flight check: `grep -n "THREADING_LAYER" varieties/_kernels.py` MUST return a hit at the top of the file.

---

## 7. Cross-suite test gaps

Per scout-C §8 ten-category catalog:

| # | Category | r3 introduces? | Handled where |
|---|---|---|---|
| 1 | conftest scope drift | No | No conftest.py in tests/ |
| 2 | fixture sharing | No | No new fixtures |
| 3 | import-time side effects | YES | Numba `THREADING_LAYER` assignment side effect (covered by `varieties._kernels` import in test_import_smoke.py) |
| 4 | plugin discovery | No | — |
| 5 | seam tests | YES | Surface→varieties registry boundary; tested by `test_import_smoke.py` plus existing `test_mesh_generators.py` |
| 6 | pytest-qt | No (AI-2 blocks) | — |
| 7 | VTK pipeline | No (r2 already covered) | — |
| 8 | settings persistence | No | — |
| 9 | star-import shadow | No (no star imports in production code) | — |
| 10 | cyclic-import-under-entrypoint smoke | YES | `tests/test_import_smoke.py` added in B5 — parametrize over `varieties`, `render`, `_qt`, `cross_section`, `app` |

The deferral list from r2 test-suggester Suggestion 1 (Numba threading-layer side-effect smoke) and Suggestion 3 (registry consistency) are NOT addressed by r3 PLAN — they remain deferred to a follow-on `repository-architect-post-r3-test-hardening` milestone. Suggestion 2 (cyclic-import smoke) IS landed by B5.

---

## 8. Rollback plan

### Tier 1 — full revert (preferred)

```bash
git revert <r3-merge-commit-sha> -m 1   # if merged via squash to a single commit
# OR for a sequence of batch commits:
git reset --hard c1dcf89                 # known-good HEAD before r3
git push --force-with-lease origin main  # only if the user explicitly approves
```

### Tier 2 — partial revert (single batch) — TAG-BASED (per r1 lesson)

Each batch ends with a git tag of the form `refactor-r3-bN-end <sha>` (consistent with r2's `refactor-r2-batchN-end` pattern documented in MOVES.md). This provides a stable anchor for partial revert without depending on commit-message grep:

```bash
# List all r3 batch-end tags:
git tag -l 'refactor-r3-b*-end'
# Revert a single batch (e.g. undo B4 only):
git revert refactor-r3-b3-end..refactor-r3-b4-end
# Revert a range (e.g. undo B3 + B4):
git revert refactor-r3-b2-end..refactor-r3-b4-end
```

**Why tag-based, not `git log --grep`:** r1 design-adversary lessons.md explicitly flagged the grep pattern as fragile — AVC's conventional-commit style (`refactor(restructure-single-root-2026q2-r3): ...`) does not match a naive `--grep="batch <N>"` query, leaving an executor with no easy way to identify commits during a panic revert. Tags are stable, human-readable, and survive commit-message format drift.

### Tier 3 — per-module restore template

```bash
# Example: restore parameter_grid.py at root (undo B2)
git checkout c1dcf89 -- parameter_grid.py
git rm _qt/parameter_grid_math.py
# Manually undo the 4 LibCST-rewritten callers:
git checkout c1dcf89 -- _qt/ui_helpers.py _qt/panels/parameters.py _qt/panels/parameter_grid_panel.py tests/test_parameter_grid.py
```

```bash
# Example: restore surfaces.py shim (undo B4)
git checkout c1dcf89 -- surfaces.py
# Re-revert the 19 callers (use git log + git revert for the B4 commit)
```

### Tier-4 — abort during execution (mid-batch failure)

```bash
git reset --hard HEAD~1   # discard the in-progress batch commit
# Re-run baseline tests; expected count depends on which batches have completed:
python -m pytest -q
#  - if abort fires during B1 or B2:    expect 506 PASS
#  - if abort fires during B3:           expect 506 PASS (if pre-shim-delete) OR 499 PASS (if post-shim-delete commit landed)
#  - if abort fires during B4 (the most likely abort scenario): expect 499 PASS (B3 has completed, test_r2_shims.py is gone)
#  - if abort fires during B5:           expect 499 PASS (B3 + B4 completed, smoke-test not yet added)
```

---

## 9. Execution sequence (5 batches, ordered by risk + dependency)

| Batch | Risk | Files touched | Commits | Description |
|---|---|---|---|---|
| **B1** | LOW (tooling) | `.claude/scripts/repository-architect/rewrite-imports.py` | 1 | Fix LibCST partial-attribute-rewrite bug per refactor-pattern-scout Topic 2 checklist (QualifiedNameProvider.has_name() + METADATA_DEPENDENCIES + multi-alias guard); add `.claude/scripts/` and `.claude/notes/` to walker exclusion list. **MANDATORY pre-commit scratch test (per scout §3 checklist item 4):** before landing the B1 commit, verify the fixed codemod against `/tmp/scratch_codemod_test.py` containing all four import patterns: `import surfaces`; `from surfaces import SurfaceSpec`; `from surfaces import SurfaceSpec, VARIETIES`; `surfaces.SurfaceSpec` attribute access in a function body. All four must rewrite correctly. End-of-batch tag: `git tag refactor-r3-b1-end <sha>`. |
| **B2** | LOW-MED | `parameter_grid.py` → `_qt/parameter_grid_math.py` + 4 callers + `varieties/types.py` | 2 | (a) `git mv` + LibCST rewrite 4 alias-form callers; (b) ADD `@runtime_checkable VarietyGenerator(Protocol)` to `varieties/types.py`. End-of-batch tag: `git tag refactor-r3-b2-end <sha>`. |
| **B3** | LOW (cleanup) | 5 shim file deletes + `tests/test_r2_shims.py` delete + `_qt/panels/__init__.py` docstring | 1 | `git rm` icons.py, styles.py, ui_helpers.py, render_worker.py, panels/__init__.py, panels/ dir, tests/test_r2_shims.py; edit `_qt/panels/__init__.py` docstring. End-of-batch tag: `git tag refactor-r3-b3-end <sha>`. |
| **B4** | **HIGH** | ~16 live import-site files + ~20 live import lines (audit's 19/23 includes 3 docstring-only hits in varieties/{tooltips,registry}.py — not live imports) + `surfaces.py` delete | 2 source commits + 1 inter-commit gate | (a) **pre-flight** Verify `THREADING_LAYER` present in `varieties/_kernels.py` (not a commit); (b)+(c) **commit 1** = LibCST rewrite of `from surfaces import X` sites + manual rewrite of 2 bare-import sites in `test_status_bar_bbox.py` + `test_enriques_hq_smoothing.py`; (d) **mandatory inter-commit gate** = `python -W error::DeprecationWarning -m pytest -q` MUST exit 0 before commit 2 — if any DeprecationWarning fires, fix the missed caller and re-run; (e) **commit 2** = `git rm surfaces.py`. End-of-batch tag: `git tag refactor-r3-b4-end <sha>` |
| **B5** | LOW (lock-in) | `pyproject.toml`, `requirements.txt`, `tests/test_import_smoke.py`, `CLAUDE.md`, `README.md`, `MOVES.md`, `CONTEXT.md` | 2 | **(step 0 brownfield pre-flight)** Install `import-linter`; run `lint-imports` with empty `[[tool.importlinter.contracts]]` list to confirm tooling installation (expect exit 0); (a) Add `import-linter>=2.0,<3` to `requirements.txt`; add `[tool.importlinter]` section to `pyproject.toml` with the **2 contracts that pass at HEAD** per dry-run validator FIX-FIRST-3: (i) `varieties` forbidden from importing `app`, `surfaces`, `_qt`, `panels`, `PySide6`, `PyQt5`, `PyQt6`; (ii) `cross_section` forbidden from importing `_qt`, `PySide6`, `PyQt5`, `PyQt6`. **DO NOT add a `render` PySide6-forbidden contract** — `render/worker.py:39` legitimately imports `QObject, QRunnable, Signal` from PySide6.QtCore (MeshWorker inherits QRunnable; this is intentional architecture, not a violation). (b) Add `tests/test_import_smoke.py` parametrized over `varieties`, `render`, `_qt`, `cross_section`, `app` (5 entries — see §6 AI-2 row for subprocess-safety evidence); (c) anchor-updater pass; (d) Verify `ls *.py \| wc -l == 1` AND `lint-imports` exits 0 AND `python -m pytest -q` reports 504 collected. End-of-batch tag: `git tag refactor-r3-b5-end <sha>` |

**Total commits:** 9 source commits + 4 metadata commits (per-batch Phase-4-step-end checkpoints) = ~13 commits.

**Per-batch verification (corrected arithmetic):** after each batch, `python -m pytest -q` must report:

- After B1 (tooling fix only): **506 passed** (no test files changed)
- After B2 (parameter_grid move + Protocol add): **506 passed** (existing tests use rewritten import paths)
- After B3 (delete `tests/test_r2_shims.py` — 7 tests removed): **499 passed**
- After B4 (surfaces.py retired — no test files added/removed): **499 passed**
- After B5 (add `tests/test_import_smoke.py` with 5 parametrize entries: varieties, render, _qt, cross_section, app): **504 passed**

**Expected final count: 504 collected.** The parity-verifier reconciles each step's delta against this table.

---

## 10. Explicitly NOT addressed in r3

| Deferral | Reason | Scout citation |
|---|---|---|
| `app.py` 1900 LOC extraction | Out of scope per brief; this is a God Object refactor, not a folder restructure | current-state §3 monolith table (KEEP) |
| `_qt/panels/appearance.py` 738 LOC extraction | Out of scope per brief; no audit brief flagged this as r3-critical | current-state §4 |
| `_qt/styles.py` 708 LOC extraction | Out of scope per brief; no audit brief flagged this as r3-critical | current-state §4 |
| Test reorganization (flat → mirrored tests/varieties/, tests/_qt/, etc.) | Per CONTEXT.md §9 "Don't create new top-level test packages" + r2 test-suggester §10.1 | current-state §13 + r2 test-suggester |
| Numba threading-layer side-effect smoke test (r2 test-suggester Suggestion 1) | Deferred to follow-on `post-r3-test-hardening` milestone; covered indirectly by `test_import_smoke.py` importing `varieties._kernels` | r2 test-suggester §1 |
| varieties.registry consistency test (r2 test-suggester Suggestion 3) | Deferred to follow-on `post-r3-test-hardening` milestone | r2 test-suggester §3 |
| Per-folder CLAUDE.md / AGENTS.md | Per ETH Zurich finding (cited by best-practices-scout): adding context files has LLM-cost | best-practices-scout §1 |

**Axis-12 self-check (under-engineering relative to scout evidence):** every deferral above either (a) was explicitly out of scope per the user brief, or (b) is a downstream test-hardening item that doesn't block r3's primary goal. **Explicit scout-citation check for the one trigger-phrase usage:** best-practices-scout §7 (p. 415) does write "app.py at 1900 LOC is still the **primary monolith risk**" — "primary monolith" IS a trigger phrase under axis-12. However, the SAME scout sentence also explicitly endorses the deferral: "r3's focus is not app.py decomposition — that remains deferred." The PLAN accepts the scout's own self-deferral. All other r3 deferrals (test reorganization, threading-layer side-effect smoke, registry consistency test, per-folder CLAUDE.md) use only neutral language in their source audit briefs. All "highest-priority" findings that did use stronger language (surfaces.py retirement, parameter_grid move, M+1 shim closure, import-linter contract) ARE in r3 scope as B2/B3/B4/B5.
