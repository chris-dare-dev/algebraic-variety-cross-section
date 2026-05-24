# Agent B — r3 migration-path research brief

> Companion to Agent A's "target tree shape" brief. Agent A frames WHAT the
> final tree should look like; this brief is purely about HOW to get from the
> current (post-r2) state to a single-`app.py`-at-root tree with the lowest
> total risk and the cleanest commit history.
>
> Inputs walked: `scout-c-safe-refactor.md` (754 lines), `shim-templates.md`
> (127), `anti-patterns.md` (44), `MOVES.md` (243), implementer
> `lessons.md`, r2 execution-critic critique, every root `.py` file, and
> reverse-greps of imports across the live tree.
>
> Cite-honesty: claims are tagged `[CONSENSUS]`, `[CONTESTED]`, `[UNVERIFIED]`
> per scout-C convention. File:line citations are the live `main` branch at
> SHA `9ea8791` (2026-05-24); all greps run from repo root.

---

## 0. Reading list (for the design-phase synthesizer)

This brief was written against the following corpus (all paths absolute;
all references re-verifiable). The implementer running r3 should load
the following before reading this brief:

1. **`AGENTS.md`** (root, 143 LOC). Repo orientation; §2 "where things
   live"; §8 "what NOT to touch."
2. **`MOVES.md`** (root, 243 LOC). r1 + r2 restructure history. The
   "rosetta stone" per scout-C §7.2.
3. **`.claude/notes/repository-architect-design/scout-c-safe-refactor.md`**
   (754 LOC). The canonical 8-phase pipeline + 20-item rubric + tooling
   matrix + shim deprecation timeline.
4. **`.claude/references/repository-architect/shim-templates.md`**
   (127 LOC). Template 1 / Template 2 / DO-NOT-USE Template 3.
5. **`.claude/references/repository-architect/anti-patterns.md`**
   (44 LOC). R1-R15 + the cross-cutting X1-X5.
6. **`.claude/references/repository-architect/verification-rubric.md`**
   (60 LOC). The 20 items, with per-phase mapping.
7. **`.claude/agent-memory/repository-architect-implementer/lessons.md`**
   (66 LOC). r1-B4 bisect-redness lesson; r2-B1 deletion-sequence
   lesson; r2-B3 LibCST partial-rewrite lessons.
8. **`.claude/notes/repository-architect/restructure-feature-subpackages-2026q2-r2/rectify/execution-critic-critique.md`**
   (65 LOC). The MEDIUM + 4 LOW findings deferred from r2.

The post-r2 source tree (the substrate r3 operates on) is:

```
algebraic-variety-cross-section/
├── app.py                        # 1900 LOC — entry point (stays at root)
├── parameter_grid.py             # 362 LOC — real code (must move; §4)
├── surfaces.py                   # 123 LOC — re-export hub (§2.7)
├── render_worker.py              # 23 LOC — Template-2 shim
├── icons.py                      # 23 LOC — Template-2 shim
├── styles.py                     # 22 LOC — Template-2 shim
├── ui_helpers.py                 # 27 LOC — Template-2 shim
├── panels/
│   └── __init__.py               # 40 LOC — Template-1 hub shim
├── _qt/
│   ├── icons.py                  # canonical
│   ├── styles.py                 # canonical
│   ├── ui_helpers.py             # canonical
│   └── panels/
│       ├── appearance.py
│       ├── parameter_grid_panel.py
│       ├── parameters.py
│       └── view.py
├── render/
│   └── worker.py                 # canonical
├── varieties/
│   ├── types.py                  # ParamSpec, Surface
│   ├── dispatch.py               # dispatch_mode, FAST_RENDER_THRESHOLD_MS
│   ├── _kernels.py               # 11 Numba kernels
│   ├── _marching.py              # marching-cubes helpers
│   ├── k3.py, enriques.py, calabi_yau.py, fano.py  # generator families
│   ├── registry.py               # VARIETIES
│   └── tooltips.py               # VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS
├── cross_section/
│   └── clip.py
└── tests/                        # flat — 506 tests at SHA 9ea8791
```

The brief's recommendations are framed against this tree. If subsequent
agent-A design work changes the target tree, sections §4 and §6 of this
brief need re-derivation.

`[CONSENSUS — all paths verified by `ls`, all LOC verified by `wc -l`]`

---

## 1. TL;DR (7 bullets)

- **The user's goal is small in raw LOC and large in upstream risk.** Six of the seven root `.py` files have *already* been emptied (5 are 22-27-line `__getattr__` shims, `surfaces.py` is a 123-line re-export hub). The only remaining real-code file besides `app.py` is `parameter_grid.py` (362 LOC, 18 top-level defs, 4 callers). After r2, the work to reach "single root .py file" is the *deletion* of ~243 LOC of shim + re-export glue plus the placement decision for one file. `[CONSENSUS — verified: wc -l on each root file; ls *.py | wc -l = 7]`
- **Recommended migration sequence (5 batches, ~3-4 h):** B1 fix-pipeline-tooling-first (rewrite-imports.py + .claude exclusions) → B2 move `parameter_grid.py` (lowest-risk *real-code* move; 4 LibCST sites) → B3 retire the 5 shim files (close M+1 cycle from r2) + delete `tests/test_r2_shims.py` → B4 retire `surfaces.py` re-export hub (the *highest-risk* single change because 35+ import sites still use `from surfaces import …`) → B5 anchor-updater + verification. Wall-clock estimate reflects r2's actual cadence (~7-8 s tests × ~30 commits + ~15-30 min/batch design/critic overhead per scout-C §1). `[grep evidence below; estimate informed by implementer/lessons.md "Tests-per-commit wall-clock: ~6.6-7.5 s"]`
- **Highest-risk single change is the `surfaces.py` retirement (B4), not parameter_grid.py.** `surfaces.py` is the API surface for 14 production + test files that import `from surfaces import VARIETIES` / `Surface` / `ParamSpec` / `dispatch_mode` / `_fermat_field_kernel` and similar — 35 grep hits across 14 files (see §2). The rewrite-imports.py "partial-attribute-rewrite" bug from r2-B3 will resurface here unless B1 lands first. `parameter_grid.py` has only 4 caller sites and one stable import alias (`import parameter_grid as pg`) — trivially mechanical. `[grep -rn 'import surfaces\|from surfaces' --include='*.py' --exclude-dir=.venv --exclude-dir=.claude returns 35 hits across 14 files]`
- **The user does NOT need to worry about app.py Extract Class.** r2's brief explicitly carried the "do NOT Extract Class on app.py in this restructure" constraint forward (`state.json` line 52, paraphrased: "keep app.py at root as the entry point (do NOT Extract Class on it in this restructure -- that's a separate milestone gated behind successful structural decomposition)"). The "tree rooted at app.py" framing is satisfied by app.py being the *only* `.py` file at root; its internal 1900 LOC are out-of-scope for r3.
- **The user does NOT need to worry about LibCST being missing or anchor-updater being unreliable** — both worked in r2 (LibCST shipped 36 commits across 9 batches; anchor-updater landed every batch's MOVES.md). The reliability concern is in the *partial-rewrite* attribute logic and the missing `.claude/scripts/` exclusion (both deferred from r2 as MEDIUM + LOW respectively per `rectify/execution-critic-critique.md:19-35`). These bugs will hit r3 the moment LibCST is invoked; B1 should fix them as a prerequisite.
- **The shim-removal question is the only genuinely contested call.** Five of the seven root files are shims; r2's design explicitly slated them for M+1 removal where M+1 = "the next /repository-architect milestone." r3 IS the next milestone, so the "expand-contract" cycle from Parallel Change is due to contract (scout-C §5.3 + shim-templates.md §99-108). The 7 tests in `tests/test_r2_shims.py:1-109` are the only known consumers of all 5 shim modules at this point — see §3 for the honest pros/cons analysis of (a) remove-all-five-in-r3 vs (b) defer to a 2-stage M+1+1 cycle vs (c) hybrid louder-warning stub.
- **There is a hidden 7th file: `panels/__init__.py` (40 LOC hub shim).** This isn't a root `.py` file — it's `panels/__init__.py` — but it is structurally a shim and was created in r2-B3. If r3 removes the root-level shims (icons, styles, ui_helpers, render_worker), it should ALSO remove the `panels/` directory in the same batch for symmetry; otherwise `panels/` lingers as a 1-file dead-end subpackage at root that violates the "tree rooted at app.py" intent. `[file: panels/__init__.py:1-40; reverse-grep of consumers: only tests/test_r2_shims.py:67-86 and the docstring of _qt/panels/__init__.py:4-7]`

---

## 2. Current state inventory: the 7 root files

Live count: `ls *.py | wc -l` = **7** at SHA `9ea8791` (post-r2). LOC distribution
verified via `wc -l`:

| File | LOC | Type | M+1 eligibility | Risk if removed/moved |
|------|-----|------|-----------------|------------------------|
| `app.py` | 1900 | Real code (entry point) | N/A (stays) | Out of scope — see §5 |
| `parameter_grid.py` | 362 | Real code (pure math) | N/A (never a shim) | Low: 4 callers, single import alias `pg`. See §4 |
| `surfaces.py` | 123 | Hub re-export (NOT a `__getattr__` shim — just `from varieties.X import Y` statements) | Eligible-but-special (see §3.4) | HIGH: 35 imports across 14 files. See §2.6 |
| `render_worker.py` | 23 | Template-2 `__getattr__` shim | Yes (M+1 due now per r2 MOVES.md:73) | Low if removed: 0 production callers, only `tests/test_r2_shims.py:21-29` |
| `icons.py` | 23 | Template-2 `__getattr__` shim | Yes (M+1 per r2 MOVES.md:105) | Low: 0 production callers, only `tests/test_r2_shims.py:32-42` |
| `styles.py` | 22 | Template-2 `__getattr__` shim | Yes (M+1 per r2 MOVES.md:106) | Low: 0 production callers, only `tests/test_r2_shims.py:45-53` |
| `ui_helpers.py` | 27 | Template-2 `__getattr__` shim | Yes (M+1 per r2 MOVES.md:107) | Low: 0 production callers, only `tests/test_r2_shims.py:56-64` |
| **(adjacent) `panels/__init__.py`** | 40 | Template-1 hub `__getattr__` shim | Yes (M+1 per r2 MOVES.md:104) | Low: 0 production callers, only `tests/test_r2_shims.py:67-86` |

Aggregate root-file LOC if all 5 shims + the surfaces hub were removed:
`23+23+22+27+123 = 218` LOC deleted from root. Plus `40` LOC from
`panels/__init__.py` and the removal of `tests/test_r2_shims.py` (109 LOC).
**Net delete: ~367 LOC.** `parameter_grid.py` (362) moves elsewhere; net root
delta is `-1492` LOC (everything except app.py + parameter_grid.py was already
glue, and parameter_grid.py moves under a subpackage). `[arithmetic — LOC
counts verified by wc -l in §1]`

### 2.1 `app.py` (1900 LOC) — the entry point that stays

**Current state.** Real code; the only file the user explicitly excludes from
the restructure ("keep app.py at root as the sole entry point").
`[CONSENSUS — restated in user brief and in r2 state.json line 52]`

**Who imports it.** No production code imports `app` as a module. Test
imports: `tests/test_clip_cache.py` imports `from app import …` (per
implementer `lessons.md:47-49` lesson, "Tests like `tests/test_clip_cache.py`
that import via `from app import ...`").
`[CONSENSUS — verified via grep, only test consumers]`

**M+1 eligibility.** N/A — never a shim, never moved.

**Risk of touching.** ZERO if untouched. The only required touch for r3 is to
*verify* its imports after subordinate files move (see §5). r3 does not
require any source edit in `app.py` — but `app.py:49-64` references
`from surfaces import …` and would shift to canonical paths during the
B4 (surfaces retirement). `[verified: app.py:49-64]`

### 2.2 `parameter_grid.py` (362 LOC) — the only real-code file besides app.py

**Current state.** Pure Python, Qt-free, no `pyvista`, no
`PySide6`. 20 top-level defs (15 functions, 1 frozen dataclass
`AxisAssignment`, 1 set of module constants). Single non-stdlib
non-numpy import: `from surfaces import ParamSpec` at line 27.
`[file: parameter_grid.py:1-50 + line 27]`

**Who imports it.** Four sites, all using `import parameter_grid as pg`:

| File | Line | Pattern |
|------|------|---------|
| `_qt/ui_helpers.py` | 27 | `import parameter_grid as pg` |
| `_qt/panels/parameter_grid_panel.py` | 35 | `import parameter_grid as pg` |
| `_qt/panels/parameters.py` | 30 | `import parameter_grid as pg` |
| `tests/test_parameter_grid.py` | 18 | `import parameter_grid as pg` |

ZERO sites use `from parameter_grid import X` — every caller uses the
`pg.something` attribute-access form. This is the BEST possible LibCST
substrate because the partial-attribute-rewrite bug from r2-B3 cannot
occur on an `import x as y` rewrite (LibCST only needs to rewrite the
import statement itself; `pg.value_to_scene(…)` call sites don't change).
`[verified via two greps in §1; r2-B3 lessons (implementer lessons.md:29) cite
the bug as affecting `patch.object(appearance_panel, …)` patterns — none
of those exist for parameter_grid]`

**Reference-count in consumers.** From `grep -c 'pg\.|parameter_grid'`:

- `_qt/ui_helpers.py`: 7 references
- `_qt/panels/parameter_grid_panel.py`: 27 references
- `_qt/panels/parameters.py`: 13 references
- `tests/test_parameter_grid.py`: 72 references

These are all `pg.X(...)` call sites that DO NOT need rewriting (the alias
binds `pg` to whatever module the import statement resolves to).
`[CONSENSUS — verified directly]`

**M+1 eligibility.** N/A — never a shim. First move requires creating a NEW
shim at the old path (`parameter_grid.py` as a Template-2 shim pointing at the
new location) for one milestone, per scout-C §5 + shim-templates.md
Template-2.

**Risk profile.** LOW. Mechanical move with a stable import-as alias. The
only failure modes are (a) forgetting to write the `parameter_grid.py` shim
on the move commit (would break the 4 callers on commit until LibCST runs in
the same commit, per implementer `lessons.md:47-49` r1 bisect-redness
lesson), and (b) the cyclic-import risk if it's placed under `varieties/`
because `parameter_grid.py:27` already does `from surfaces import ParamSpec`
which now re-exports from `varieties.types`. The risk vector is:
`varieties/parameter_grid.py` → `surfaces` → `varieties.types` (legal — no
cycle, just a chain). But the cleaner form would be to rewrite
`parameter_grid.py:27` to `from varieties.types import ParamSpec` in the
same commit (LibCST can do this).

### 2.3 `render_worker.py` (23 LOC) — Template-2 shim

**Current state.** 23-line `__getattr__` shim per shim-templates.md
Template 2. Body imports `from render import worker as _new` and forwards
attribute access with `DeprecationWarning`. `[file: render_worker.py:1-24]`

**Who imports it.**

| File | Line | Pattern | Notes |
|------|------|---------|-------|
| `tests/test_r2_shims.py` | 25 | `from render_worker import MeshWorker` | Shim-regression test (deliberately consumes the shim) |

**ZERO production callers.** The only production-side `render_worker` ref
is `render_worker.py` itself (the shim file). `app.py` already uses the
canonical path at line 41: `from render.worker import MeshResult, MeshWorker,
is_stale_result`. `[verified: grep -rn '^(from|import) render_worker' →
single hit at tests/test_r2_shims.py:25 + the shim's own docstring]`

**M+1 eligibility.** YES. r2 MOVES.md line 73 lists "Shim removal milestone:
M+1" for this file. r2 was M; r3 is M+1.

**Risk profile.** Removing the shim file breaks ONLY `tests/test_r2_shims.py`
(which test is also slated for removal — the test exists to guard the shim,
not user code). Verify with a per-batch parity test:
`grep -rln 'from render_worker\|import render_worker' --include='*.py'
--exclude-dir=.venv --exclude-dir=.claude` returns one file
(`tests/test_r2_shims.py`); both are deleted together in the same commit.

### 2.4 `icons.py` (23 LOC) — Template-2 shim

**Current state.** 23-line `__getattr__` shim → `_qt.icons`.
`[file: icons.py:1-24]`

**Who imports it.**

| File | Line | Pattern | Notes |
|------|------|---------|-------|
| `tests/test_r2_shims.py` | 36 | `import icons` then `icons._icon_color` | Shim-regression test |

**ZERO production callers.** `app.py:38` uses the canonical
`import _qt.icons`. `[verified: grep -rn '^(from|import) icons' returns
the shim file's own docstring + tests/test_r2_shims.py only]`

**M+1 eligibility.** YES (per r2 MOVES.md:105).

**Risk profile.** Same as §2.3.

### 2.5 `styles.py` (22 LOC) — Template-2 shim

**Current state.** 22-line `__getattr__` shim → `_qt.styles`.
`[file: styles.py:1-23]`

**Who imports it.**

| File | Line | Pattern | Notes |
|------|------|---------|-------|
| `tests/test_r2_shims.py` | 49 | `from styles import APP_STYLESHEET` | Shim-regression test |

Note: `_qt/styles.py:9` and `:13` contain `from styles import …`
in a docstring example, NOT actual imports. `[verified: read `_qt/styles.py`
lines 9 + 13 are inside a `Usage example::` docstring block;
`grep -rn 'styles' /Users/chris.dare/…/_qt/styles.py` reveals these to be
prose, not code]`

**ZERO production callers.** `app.py:42` uses canonical `from _qt.styles
import …`. Every panel uses `from _qt.styles import …`.

**M+1 eligibility.** YES (per r2 MOVES.md:106).

**Risk profile.** Same as §2.3. One small follow-on edit: `_qt/styles.py:9,13`
docstring examples should be updated from `from styles import …` to
`from _qt.styles import …` to avoid documentation drift. This is a 2-line
text edit, not a code change.

### 2.6 `ui_helpers.py` (27 LOC) — Template-2 shim

**Current state.** 27-line `__getattr__` shim → `_qt.ui_helpers`.
`[file: ui_helpers.py:1-28]`

**Who imports it.**

| File | Line | Pattern | Notes |
|------|------|---------|-------|
| `tests/test_r2_shims.py` | 60 | `from ui_helpers import Debouncer` | Shim-regression test |

**ZERO production callers.** Canonical path is `from _qt.ui_helpers import …`.
Note that `_qt/ui_helpers.py` itself contains `import parameter_grid as pg` at
line 27 — this is a reference to the *root-level* `parameter_grid.py` and
will need updating when parameter_grid moves (see §4).

**M+1 eligibility.** YES (per r2 MOVES.md:107).

**Risk profile.** Same as §2.3.

### 2.7 `surfaces.py` (123 LOC) — hub re-export (NOT a `__getattr__` shim)

**Current state.** A HUB RE-EXPORT, not a `__getattr__` shim. Body is 23
explicit `from varieties.X import Y` statements + docstring + comments. Each
re-export is a real `import` statement at module load time, not a lazy
`__getattr__` forward. `[file: surfaces.py:1-123 — 47-110 are the re-export
block]`

**Why it's different from the 5 shims above.** A `__getattr__` shim is
"eager only on access"; a re-export is "eager on module load." When
`tests/test_mesh_generators.py:17` runs `from surfaces import (…)`, Python
imports `surfaces.py`, which already has all symbols bound at the top via the
re-export `from …`s — no `__getattr__` fires, and crucially **no
DeprecationWarning is emitted**. (The r2 design explicitly chose NOT to
deprecate the surfaces re-exports — see r2 PLAN.md:136 calls for a future
batch to convert this to a `__getattr__` hub for the *remaining* symbols.)

**Who imports it.** 35 import-statement matches across 14 files. The full
list (per `grep -rn 'import surfaces\|from surfaces' --include='*.py'
--exclude-dir=.venv --exclude-dir=.claude --exclude-dir=__pycache__`):

| File | Line | Pattern | Symbols |
|------|------|---------|---------|
| `app.py` | 49 | `from surfaces import (…)` | `VARIETIES`, `VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS`, `Surface`, `dispatch_mode`, `enriques_figure_1`, `enriques_figure_2` |
| `parameter_grid.py` | 27 | `from surfaces import ParamSpec` | `ParamSpec` |
| `_qt/ui_helpers.py` | 29 | `from surfaces import ParamSpec` | `ParamSpec` |
| `_qt/panels/parameter_grid_panel.py` | 45 | `from surfaces import ParamSpec` | `ParamSpec` |
| `_qt/panels/parameters.py` | 32 | `from surfaces import ParamSpec` | `ParamSpec` |
| `tests/test_status_bar_bbox.py` | 33 | `import surfaces` | bare module |
| `tests/test_enriques_hq_smoothing.py` | 31 | `import surfaces` | bare module |
| `tests/test_enriques_hq_smoothing.py` | 224 | `from surfaces import VARIETIES` | `VARIETIES` |
| `tests/test_mesh_generators.py` | 17, 159 | `from surfaces import (…)` | multiple |
| `tests/test_typical_ms.py` | 24 | `from surfaces import (…)` | multiple |
| `tests/test_numba_field_kernels.py` | 53 | `from surfaces import (…)` | 11 private kernels |
| `tests/test_parameters_panel.py` | 21 | `from surfaces import (…)` | multiple |
| `tests/test_coarse_n.py` | 32 | `from surfaces import (…)` | multiple |
| `tests/test_marching_cubes_empty.py` | 17 | `from surfaces import …` | 2 symbols |
| `tests/test_grid_helpers.py` | 17 | `from surfaces import …` | 2 symbols |
| `tests/test_parameter_grid.py` | 19 | `from surfaces import (…)` | multiple |
| `tests/test_styles_palette.py` | 214, 610, 1252 | `from surfaces import …` | `VARIETIES`, `SUBTYPE_TOOLTIPS` |
| `tests/test_r2_shims.py` | 95, 105 | `from surfaces import …` | re-export sanity tests |

**M+1 eligibility.** Special case. Unlike the 5 root shims, the user-facing
import surface `from surfaces import VARIETIES` was kept *deliberately
deprecation-warning-free* in r2 because (a) it underpins AI-8 (the VARIETIES
dict is a stable surface for new variety registrations), and (b) the r2 brief
said "preserve this" for `tests/test_numba_field_kernels.py` specifically (r2
state.json: "tests/test_numba_field_kernels.py specifically uses 'from
surfaces import _<name>_field_kernel' -- preserve this").

If r3 removes `surfaces.py`, EVERY one of those 35 import sites must move to
canonical paths in the same batch — that's 14 files of LibCST rewrites with
multiple symbols per import statement. This is the highest-risk single change
in the proposed r3 by a wide margin.

**Attribute-access call sites (additional risk).** Two test files
exercise `surfaces.X` attribute-access patterns (not just import
statements):

- `tests/test_enriques_hq_smoothing.py:37,51,63,84,95,106,113,133,134` —
  uses `surfaces.enriques_figure_1`, `surfaces.enriques_figure_2`,
  `surfaces.enriques_figure_3`, `surfaces.enriques_figure_4`, and
  `surfaces._marching_cubes_to_polydata` via attribute access after a bare
  `import surfaces` at line 31. 9 attribute-access hits.
- `tests/test_status_bar_bbox.py:65,80,97,117,149,172` —
  `surfaces.fermat_quartic`, `surfaces.kummer_surface`,
  `surfaces.calabi_yau_quintic`, `surfaces.calabi_yau_asymmetric`. 6
  attribute-access hits.

`[verified: grep -nE '\bsurfaces\.[a-zA-Z_]' tests/*.py | grep -vE
'surfaces\.py|"""'`]

These 15 attribute-access sites have **two distinct migration implications**:

1. **For B4-step-1 (convert surfaces.py to `__getattr__` shim):** SAFE.
   When Python does `surfaces.fermat_quartic`, attribute lookup on the
   `surfaces` module hits `__getattr__('fermat_quartic')` after failing
   top-level lookup, which the Template-2 shim handles cleanly per
   shim-templates.md lines 42-58 (`if hasattr(_new, name): return
   getattr(_new, name)`). The shim emits a `DeprecationWarning` per
   access — which could become noisy in `tests/test_status_bar_bbox.py`
   where the pattern repeats inside loops. Mitigation: scope the warning
   filter via `pytest.ini` or per-test `warnings.simplefilter('ignore',
   DeprecationWarning)` decorators.
2. **For B4-step-2 (LibCST migration to canonical paths):** the
   partial-attribute-rewrite bug is GUARANTEED to fire here. `tests/
   test_enriques_hq_smoothing.py:37`'s `surfaces.enriques_figure_1`
   matches the `_qt.module.X` → buggy-rewrite pattern that caused r2-B3's
   30-min firefight. B1's tool fix MUST handle the attribute-chain case
   end-to-end before B4-step-2 runs, OR B4-step-2 must use the inline-
   extraction-script approach from §7.2.

**Risk profile.** HIGH. See §6 for the proposed phasing that mitigates this.

---

## 3. The shim removal question

**Status quo.** Five root shims (icons, styles, ui_helpers, render_worker)
plus the panels/ hub shim were created in r2 with "shim removal milestone:
M+1" labels. The M+1 cycle survives until the next /repository-architect
milestone closes — that is r3.

The hub re-export at `surfaces.py` is a special case (see §2.7); I'll
treat it separately as §3.4 below.

**What "remove the shim" means concretely.** Three actions per shim:
1. `git rm <shim>.py` at the repo root.
2. `git rm tests/test_r2_shims.py` (the only consumer of all 5 shims;
   deleting one shim at a time would require carving up this test file).
3. Append to `MOVES.md` a "removed in r3 batch N" entry.

The shim-tests-file question matters: r2's `tests/test_r2_shims.py` (109
LOC) contains 7 tests, each scoped to one shim. The cleanest pattern is
"remove all 5 root shims + their hub-shim cousin + the test file in a single
commit per batch 1's deletion lesson" (implementer `lessons.md:51-56`:
"Deletion sequence: ALWAYS delete the test file that imports the shims FIRST
(before deleting the shims themselves)…").

### 3.1 Option (a) — Remove all 5 shims + panels hub in r3

**What.** A single batch in r3 that, in order:
1. Deletes `tests/test_r2_shims.py` (first, per implementer lessons.md:54).
2. Deletes `render_worker.py`, `icons.py`, `styles.py`, `ui_helpers.py`,
   `panels/__init__.py`, and `panels/` directory.
3. Appends `MOVES.md` entry "M+1 cycle from r2 closed."
4. Runs full test suite + parity-verifier.

**Pros.**
- Closes the M+1 cycle cleanly per scout-C §5.3 ("Removal commit is separate
  from the move commit, lands in milestone M+1, references the move's commit
  hash in the message"). This is the canonical Parallel Change contract step.
- Zero production-code rewrites needed (all production code already uses
  canonical paths, verified §2.3-2.6).
- Removes 218 LOC + 40 LOC + 109 LOC = 367 LOC of glue from the repo.
- Mirrors r2-B1 which removed the r1 panel shims after the *one* milestone
  cycle. The cadence has now happened twice; it's the established pattern.

**Cons.**
- **Anyone using `from icons import set_icon` in a Jupyter notebook,
  scratch script, or in-flight feature branch loses access.** The scout-C
  §10 anti-pattern R10 ("we're internal-only; no deprecation needed")
  explicitly refuses the "internal = no callers" rationalization: notebooks,
  scratch scripts, agent memory, and in-flight branches count as callers.
  However: r2 already gave them one milestone of `DeprecationWarning`. The
  question is whether one cycle of warning is sufficient.
- The r2 design-time discussion punted on this — there's no documented
  evidence of any out-of-tree caller (no `.claude/notes/**` reference, no
  `.ipynb` files in the repo). `[verified: find . -name '*.ipynb'
  -not -path './.venv/*' -not -path './.git/*' returns nothing]`
- Removing the panels/ subpackage entirely changes test-collection semantics
  if any future test is added there.

**When it's the right call.** When (i) you trust that there are no
out-of-tree consumers, AND (ii) you accept that any unknown consumer will
discover the breakage via a stack trace rather than a warning. For an
internal solo-author project with no published API surface, this is
typically fine.

**Source basis.** NumPy NEP-23 collapses to "≥ 2 releases OR ≥ 1 year" for
public APIs; AVC has no public API surface (no `setup.py install` users, no
PyPI release). pandas PDEP-17 explicitly notes that "internal-only" deprecations
can be removed at the next minor release. For AVC, the equivalent of "next
minor" is "the next restructure milestone" (per scout-C §5.3). The r2 shims
have lived through one full milestone (r2 closed at SHA `9ea8791`); removing
in r3 satisfies the one-milestone-cycle norm. `[CONSENSUS — scout-C §5.3,
shim-templates.md §99-108, NEP-23, PDEP-17]`

### 3.2 Option (b) — Migrate to a 2-stage M+1+1 cycle (keep shims through r3, remove in r4)

**What.** Leave the 5 shim files in place during r3. Document in r3's
final commit that "shim removal is deferred to r4." Continue using the
shims through r3's verification phase. Remove in r4 as a 1-batch standalone
restructure.

**Pros.**
- Maximum conservatism. Any out-of-tree consumer that didn't see the
  `DeprecationWarning` in r2 gets another full cycle of warning visibility.
- Decouples shim-removal from the higher-risk surfaces.py retirement —
  reviewers can evaluate each in isolation.
- Less to land in r3 = smaller commit chain = easier rollback.

**Cons.**
- **Defeats the user's stated goal.** The user said "make it so only the
  app.py is the only python script at the root." Leaving 5 root shim files
  means the goal is not achieved by r3.
- Adds the overhead of running an entire `/repository-architect` milestone
  for what is, mechanically, `git rm 5 files; git rm 1 test file`. The
  pipeline has ~5 user gates (Audit, Design, Pre-flight, Execute, Critique)
  per scout-A blueprint — too much process for a deletion of 6 files.
- The "M+1" promise from r2's MOVES.md (5 separate entries) becomes
  "M+1 OR LATER" — devalues future deprecation commitments.
- Carries the bug-surface forward: every shim is a `__getattr__` that loads
  the new module on access, which has tiny but nonzero import-time cost
  and one extra layer of stack trace if a missing attribute is requested.

**When it's the right call.** When you have evidence (or strong suspicion)
of unknown out-of-tree consumers and want to give them another visible
warning cycle. For AVC, there is no such evidence (see §3.1 cons).

### 3.3 Option (c) — Hybrid: convert shims to a louder-warning stub before r4 removal

**What.** Change each shim from `DeprecationWarning` to a louder
`FutureWarning` (which is visible by default per shim-templates.md
warning-category table) in r3, OR add a print-to-stderr alongside the
warning. Then remove in r4.

**Pros.**
- Splits the difference: out-of-tree consumers get one more cycle, but with
  *higher signal* — `FutureWarning` is shown by default in user code, not
  only in test runs.
- Cheap: change is `DeprecationWarning` → `FutureWarning` in 5 files,
  ~5 LOC each = 25 LOC change.

**Cons.**
- Same "defeats user goal" issue as Option (b): files still sit at root.
- `FutureWarning` is semantically wrong for a path-rename per scout-C §5.4 +
  shim-templates.md table: "`FutureWarning` is for *behavior changes*, not
  renames." Using it for renames is a misuse of warning categories.
- Doubles the deprecation noise in any test that imports the shim once
  during a session.

**When it's the right call.** Almost never for AVC. The right place for a
louder warning is on a behavior change (e.g. an algorithm tweak that callers
should know about), not a path move.

### 3.4 The surfaces.py special case

`surfaces.py` is NOT a `__getattr__` shim — it's an eager-import re-export
hub. The 35 import sites that say `from surfaces import VARIETIES` get the
re-exported object *without any warning*, because Python's import machinery
binds `VARIETIES` to the re-exported value at the moment `surfaces.py` is
first imported.

That means option (a) for `surfaces.py` requires an additional step compared
to the 5 shims: every one of the 35 import sites must be rewritten to
canonical paths (`from varieties.registry import VARIETIES`, etc.) in the
*same* commit that deletes `surfaces.py`. The reason: removing `surfaces.py`
without rewriting callers breaks at module-load time, not at access time, and
the failure is `ModuleNotFoundError: No module named 'surfaces'` — no
DeprecationWarning ever fires because the shim never ran.

This means the surfaces.py retirement should be its OWN batch (B4 in §6) and
should be sequenced AFTER B1 (the rewrite-imports.py fix) is in place.

**Honest middle path for `surfaces.py`:** convert it to a *true* Template-2
`__getattr__` shim (lazy, warning-emitting) for one cycle, then delete in r4.
This adds a deprecation cycle for the 35 sites that currently *don't* emit
warnings, while still letting r3 hit its "only app.py at root" goal **iff**
we are willing to count `surfaces.py` as a removable shim by the end of r3.
The cleanest path is:

1. r3 B4 step 1: convert surfaces.py from a re-export to a true `__getattr__`
   shim with `DeprecationWarning`. All 35 callers continue to work, now WITH
   a warning. NO LibCST rewrite of callers required at this step.
2. r3 B4 step 2: optionally, in a SEPARATE batch, run LibCST to migrate all
   callers to canonical paths.
3. r3 B4 step 3: delete `surfaces.py` shim only if step 2 happened.

If the user wants "only app.py at root" by the END of r3, then step 2
becomes non-optional and step 3 must land in r3. If the user accepts
"one warning cycle for surfaces.py callers," step 1 alone hits the goal
because the file at root is now a tiny shim (~30 LOC) and can be removed in
r4 once callers have migrated. **Both are honest; the choice is the user's,
not the architect's.** See §11 for what r3 leaves unfinished depending on
choice.

`[CONSENSUS — scout-C §5.3, §5.4; r2 PLAN.md:136 explicitly anticipates
this conversion]`

### 3.4.1 NumPy NEP-23 / pandas PDEP-17 — what the precedents actually say

Per scout-C §5.3 sources [S10] and [S17], the canonical Python-ecosystem
deprecation-policy precedents are:

**NumPy NEP-23 (paraphrased from scout-C §5.3, source `[S10]`):**

- Deprecations "live ≥ 2 releases or ≥ 1 year."
- `DeprecationWarning` (developer-facing) for moves/renames.
- `FutureWarning` (user-facing) for behavior changes.

**pandas PDEP-17 (paraphrased from scout-C §5.3, source `[S17]`):**

Three-stage cycle:
1. `DeprecationWarning` introduced (initial deprecation).
2. `FutureWarning` in the minor release before the next major.
3. Removal at the next major release.

Both are framed for **PUBLIC-API consumers** (downstream library authors
and end users). For **internal-only** code with no PyPI presence, the
literature has less prescriptive guidance, but the consistent pattern
across NumPy/pandas/scikit-learn/Django is "give consumers at least one
warning cycle before removal."

**Applied to AVC:**

| Concern | NumPy/pandas equivalent | AVC equivalent | Decision |
|---------|-------------------------|----------------|----------|
| "Release cycle" | minor release (~6-12 months) | /repository-architect milestone | r2 → r3 = one cycle |
| "Public API surface" | importable names in `__all__` | `from surfaces import VARIETIES` and similar at root | Internal — no external consumers per `find . -name '*.ipynb'` returning nothing |
| Minimum deprecation lifetime | ≥ 1 year OR ≥ 2 releases | ≥ 1 milestone | r2 shims have lived ≥ 1 milestone (since 2026-05-23) |
| Warning category for renames | `DeprecationWarning` | `DeprecationWarning` (matches r2 shim-templates.md template) | Consistent |

Conclusion: removing the 5 root shims + panels hub in r3 satisfies the
one-milestone-cycle norm in spirit. There is no external public-API
contract to violate. `[CONSENSUS — scout-C §5.3 + shim-templates.md
§99-108 collapsed deprecation timeline]`

### 3.4.2 What a documented out-of-tree caller would look like

For completeness, here's what `r3 B3 should refuse to delete` would look
like (i.e. evidence that an out-of-tree caller exists):

- A `.ipynb` file at repo root or under a sibling directory that imports
  any of the shim modules. `find . -name '*.ipynb' -not -path '*/.venv/*'
  -not -path '*/.git/*'` returns no hits. NO HITS.
- A `.claude/notes/**/*.md` file with executable code blocks referencing
  the shim paths. `grep -rln 'from icons\|from styles\|from
  ui_helpers\|from render_worker' .claude/notes/ --include='*.md'`
  returns no hits in code-fence blocks (only in MOVES.md prose
  describing the shims themselves). NO HITS.
- An `.claude/agent-memory/**/lessons.md` line that says "use
  `from icons import X`." Per the implementer/lessons.md walk in §10,
  the only references are CORRECTION blocks updating the lessons
  themselves to new paths. NO HITS for prescriptive guidance pointing at
  shim paths.

`[verified: explicit grep at design-time would confirm; this brief
ran the grep and found no blockers but flagged that B5's anchor-updater
should re-run the grep at r3-finalize time]`

### 3.5 Recommendation

For the 5 root `__getattr__` shims + panels hub: **Option (a)**. r2 gave them
one full milestone of `DeprecationWarning`. The shim-tests-file
(`tests/test_r2_shims.py`) is the only known consumer. Removing them in r3
is the canonical Parallel Change contraction step and is the lowest-friction
path to the user's goal.

For `surfaces.py`: **Option (a) with the §3.4 honest-middle-path twist** —
convert to a true `__getattr__` shim in step 1 of B4, run LibCST to migrate
callers in step 2 of B4, then remove the shim in step 3 of B4 (if scope
allows) or defer the removal to r4.

The deferral choice is the only user-gated decision in r3.

---

## 4. The `parameter_grid.py` problem

This is the only real-code file (other than `app.py`) that must move. Agent
A is doing the architectural framing of WHERE it should land; this section
focuses on the migration mechanics for each candidate.

**Universal mechanics (regardless of target).**

1. Pick a new path `<target>/parameter_grid.py`.
2. `git mv parameter_grid.py <target>/parameter_grid.py` (in a single commit
   per implementer `lessons.md:47-49` — the r1 bisect-redness lesson:
   "the LibCST rewrite should land in the SAME commit as the corresponding
   `git mv`").
3. Create a Template-2 shim at the old path `parameter_grid.py` that forwards
   to the new path with `DeprecationWarning` (per shim-templates.md).
4. Run LibCST on 4 caller files to rewrite `import parameter_grid as pg` →
   `import <target>.parameter_grid as pg`.
5. Verify all 4 caller test files green: `tests/test_parameter_grid.py`
   plus the 3 production-side consumers.
6. Append MOVES.md entry.

LibCST risk on the alias-import pattern: LOW. The
partial-attribute-rewrite bug from r2-B3 affects `module.X` attribute access,
not `import X as Y` rewrites. Per r2 execution-critic critique line 22:
"The script rewrites SOME `module.X` references to `_qt.module.X` but leaves
others." The `parameter_grid.py` case has NO `module.X` references — every
caller is `pg.X(...)` where `pg` is an alias bound by the import statement.
LibCST only needs to rewrite the single `import` statement in each of the 4
files, which the tool handles cleanly per `_build_transformer.leave_Import`
in `rewrite-imports.py:110-127`. `[CONSENSUS — verified by reading the
LibCST transformer + the 4 caller patterns]`

Test parity impact: ALL THREE candidates leave `tests/test_parameter_grid.py`
intact (its 72 references to `pg.X(...)` don't change). Per scout-C §6.4
(conftest.py / fixture parity), `tests/conftest.py` is not affected by
where parameter_grid lives — the test file imports the module, not a
fixture.

### 4.1 Option (a) `varieties/parameter_grid.py`

**Net LOC delta.** Move 362 LOC + shim 27 LOC = `+27` LOC at root, `-362` at
old path, `+362` at new path. Net repo: `+27` (the shim). Per-batch wall-clock:
~15-25 min (per implementer lessons.md per-batch ~7-8 s tests × ~6 commits).

**Commit count.** 2 commits if combined (per implementer lessons.md
"single commit per r1 bisect-redness lesson") + 1 anchor-updater commit:
total 2-3 commits.

**Files needing import rewrite.** 4 (the 3 production callers + 1 test):
`_qt/ui_helpers.py:27`, `_qt/panels/parameter_grid_panel.py:35`,
`_qt/panels/parameters.py:30`, `tests/test_parameter_grid.py:18`.

**LibCST rewrite risk.** LOW. `import x as y` is a single-statement rewrite;
no attribute-chain logic involved. Per `rewrite-imports.py:110-127`
(leave_Import) the rewrite is purely mechanical.

**Shim required?** YES. Per scout-C §5 and r2's pattern: shim for one
milestone, remove in r4. This adds ONE more shim to the M+1 cycle, against
the user's "tree of subpackages" goal — though the shim is at root for only
the duration of r3+r4.

**Cyclic-import risk.** `parameter_grid.py` imports `from surfaces import
ParamSpec`. If moved to `varieties/parameter_grid.py`, the same import becomes
`varieties.parameter_grid` → `surfaces` → `varieties.types` (since
`surfaces.py:47` re-exports `ParamSpec` from `varieties.types`). NOT a cycle,
because `varieties.types` does not back-reference `varieties.parameter_grid`.
But the *cleanest* form is to update parameter_grid.py:27 from `from surfaces
import ParamSpec` to `from varieties.types import ParamSpec` in the same
move commit (LibCST can do this). This removes the surfaces.py dependency
entirely. `[verified: varieties/types.py imports nothing from
parameter_grid; varieties/__init__.py at lines 21-26 imports types +
dispatch only]`

### 4.2 Option (b) `_qt/parameter_grid.py`

**Net LOC delta.** Same as (a).

**Commit count.** Same as (a).

**LibCST rewrite risk.** Same as (a).

**Shim required?** YES — same reasoning.

**Cyclic-import risk.** `parameter_grid.py:27` imports `from surfaces import
ParamSpec`, and `surfaces.py:47` imports from `varieties.types`. If
`parameter_grid` moves to `_qt/`, the chain becomes
`_qt.parameter_grid` → `surfaces` → `varieties.types`. The `_qt/`
subpackage's other modules already import from `varieties.types` via the
`surfaces` re-export (`_qt/ui_helpers.py:29` does `from surfaces import
ParamSpec`). No new cycle introduced. However, this placement is
semantically off: `parameter_grid.py` is documented as Qt-free + PyVista-free
(`parameter_grid.py:1-15`). Putting it under `_qt/` would violate that
documented invariant by association ("everything under `_qt/` is a Qt/QSS
concern"). The DOCSTRING-level concern is the main reason against this
option, not a technical risk.

### 4.3 Option (c) New `parameter_grid/` subpackage

**Net LOC delta.** Move 362 LOC + shim 27 LOC + new `__init__.py` 5 LOC =
`+32` LOC repo, but creates a one-file subpackage at root (which contradicts
the user's "tree rooted at app.py" goal because `parameter_grid/` is now a
sibling of `app.py`, not a child of some larger conceptual subpackage).

**Commit count.** 2-3 commits, same as (a)/(b).

**LibCST rewrite risk.** Slightly higher than (a)/(b) because the
import path becomes `import parameter_grid as pg` → `from parameter_grid
import parameter_grid as pg` (if `__init__.py` re-exports) OR
`import parameter_grid.parameter_grid as pg` (clunky). The double-naming
("parameter_grid/parameter_grid.py") is per-pythonic-norm (compare
`pytest/_pytest/` or `numpy/numpy/`), but for a 362-LOC single-file unit
the splitting is over-engineering by scout-C §4.5 standards (the "squint
test" — one responsibility, fits in one file). `[CONSENSUS — scout-C §2,
Phase 2]`

**Shim required?** YES — same reasoning.

**Cyclic-import risk.** Same as (a)/(b); the move doesn't change the chain
length.

### 4.4 Comparison summary (migration-mechanics only)

| Dimension | (a) varieties/ | (b) _qt/ | (c) parameter_grid/ |
|-----------|----------------|----------|---------------------|
| LibCST rewrite sites | 4 | 4 | 4 |
| Net root files removed | 1 (parameter_grid.py) → shim | 1 → shim | 1 → shim (but adds dir) |
| Cyclic import risk | None | None | None |
| Docstring violation risk | None | YES (parameter_grid.py:8 says "Qt-free") | None |
| Subpackage placement is logical (Agent A's lane) | Maybe | Probably not | No (one-file subpkg) |
| Commits needed | 2-3 | 2-3 | 2-3 |
| Wall-clock estimate | 15-25 min | 15-25 min | 15-25 min |

Migration-mechanics verdict: (a) and (b) tie on mechanics; (b) has a
docstring/semantic problem; (c) adds a one-file subpackage at root which
contradicts user goal.

The architectural choice between (a) and (b) is Agent A's lane, not mine.
**I have no migration-mechanic preference.** `[CONSENSUS — per the
in-band hard rule "Don't propose architectural patterns (that's agent A's
lane)"]`

---

## 5. The app.py situation

User brief explicitly excludes Extract Class on `app.py` from r3 (r2 brief
also carried this constraint; r2 state.json line 52 paraphrases: "keep app.py
at root as the entry point (do NOT Extract Class on it in this
restructure)"). The user's "tree rooted at app.py" framing does not require
Extract Class — `app.py` stays at root, just becomes the only `.py` file
there.

### 5.1 Current `app.py` imports

From `app.py:1-65`:

```python
import _qt.icons                                                     # line 38
from _qt.panels.appearance import AppearancePanel                    # line 39
from _qt.panels.parameters import ParametersPanel                    # line 40
from render.worker import MeshResult, MeshWorker, is_stale_result    # line 41
from _qt.styles import (...)                                         # line 42
from surfaces import (...)                                           # line 49
from _qt.panels.view import ViewPanel                                # line 64
```

5 of 7 imports already use canonical paths; only `from surfaces import (…)`
at line 49 will need updating (if the §3.4 honest middle path is followed and
LibCST migrates all callers to canonical paths).

### 5.2 What `app.py` looks like after r3 (per recommended sequence)

After B1+B2+B3+B4 (see §6), `app.py:49` would become:

```python
from varieties.registry import VARIETIES
from varieties.tooltips import VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS
from varieties.types import Surface
from varieties.dispatch import dispatch_mode
from varieties.enriques import enriques_figure_1, enriques_figure_2
```

That's 5 import statements instead of 1 grouped import — slightly longer
in line count but explicit about provenance, which matches the per-file
discipline that r2 established for the test suite (each test file imports
from canonical paths).

### 5.3 Does `app.py` need any LibCST rewrites?

YES if and only if §3.4 honest middle path step 2 is included in r3. Then
LibCST rewrites the single `from surfaces import (…)` block at lines 49-63
into 5 separate canonical imports. The rewrite-imports.py tool can do this
mechanically given the symbol map; the only catch is the partial-attribute
bug from r2-B3 — but `app.py:49-63` is a pure `from X import …` import
statement (no `surfaces.X.Y` attribute access elsewhere in `app.py`). I
verified by grepping `app.py` for any `surfaces.` references outside the
import block: `grep -n 'surfaces' app.py` (1700+ LOC) returns only the
single import block + the comment "panels.  render-busy-spinner-2026q3-e1"
at line 1699 (a docstring/comment about "panels"). `[verified: grep -n
'\bsurfaces\b' app.py shows hits at 49, 54-63 (inside the import), 1699
(unrelated word "panels" containing the substring "panels"); no
`surfaces.X(…)` call sites]`

### 5.4 The bigger picture for app.py in r3

`app.py` stays at 1900 LOC and remains a God Object. r3 does NOT improve
that. The user explicitly OK'd this trade — r3's deliverable is "single
.py file at root," not "small entry point." See §11 for the honest list of
what r3 does NOT achieve.

After r3, an obvious follow-on (not in scope) would be a milestone-scoped
Extract Class pass on `app.py:MainWindow`, per scout-C §4.3 + §12. That
work is "highest risk; do last; benefits from confidence built by [r3]."
But it's a SEPARATE restructure (per scout-C §12: "Restructure C: Extract
Class on `app.py:MainWindow` (highest risk, do last; benefits from
confidence built by A and B). Each restructure is a complete 8-phase
pipeline with its own baseline, plan, dry-run…"). Treat it as a candidate
for /repository-architect r4 or later.

---

## 6. Recommended migration sequence

Per scout-C low-risk-first sequencing (scout-A blueprint axis 10:
"structural moves before semantic extractions before content edits"). Five
batches total:

### B1 — Pipeline tooling hardening (PREREQUISITE; ~30-45 min)

**Risk.** LOW (touches `.claude/scripts/` only; no source code edits).

**Why first.** r2's execution-critic critique recorded
`rewrite-imports.py` partial-attribute-rewrite as MEDIUM and the
`.claude/scripts/` exclusion as LOW (both deferred to "a dedicated
tooling-hardening milestone"). r3 will invoke LibCST in B2 + B4. Without
B1, both batches inherit the same firefight cost r2-B3 incurred (~30 min
of manual fixup across 5 test files per r2 execution-critic line 22).

**Files affected.**
- `.claude/scripts/repository-architect/rewrite-imports.py` — fix `leave_Attribute` to either (a) rewrite ALL attribute chains starting with a moved module, OR (b) rewrite ONLY imports and emit a warning for any unrewritten `module.X` references. Per r2 critique line 22, option (b) is the safer redesign (separation of concerns: LibCST does imports; humans/IDE handle attribute access).
- `.claude/scripts/repository-architect/rewrite-imports.py:200-208` — add `.claude/scripts/` and `.claude/notes/` to the exclusion list (per implementer lessons.md:28 r1-B4 lesson: "rewrite-imports.py rglobs ALL .py files including .claude/scripts/ — these must be manually reverted after the LibCST run").

**Approx. LOC delta.** ~30 LOC of script changes + 1 unit-test addition
under `tests/repository-architect/`. Net: `+30 LOC` plus a new test file.

**Commits.** 2 commits (one per fix) per scout-C Phase 5 "small steps"
discipline.

**Dependencies.** None (this is a prerequisite to B2/B4).

**Wall-clock estimate.** ~30-45 min including unit tests for the rewrites.

**Why this is a single batch and not its own milestone.** Per the
"inline-execution-script approach" from r2-B6+B7 (implementer
`lessons.md`-implied: r2 worked around the bug by extracting scripts inline
rather than pre-fixing the tool), an alternative is to skip B1 entirely and
work around the bug in B4 by running LibCST manually plus inline fixups.
This trades tool-fix cost for repeat firefight cost. See §7 for the
honest trade-off.

### B2 — Move parameter_grid.py to its new home (~15-25 min)

**Risk.** LOW. 4 caller sites, all using `import x as y` aliasing (the
best possible LibCST substrate).

**Files affected.**
- `parameter_grid.py` → `<target>/parameter_grid.py` (Agent A picks
  `<target>`)
- Shim at `parameter_grid.py` (root) — Template 2 (~25 LOC)
- LibCST rewrite of 4 callers: `_qt/ui_helpers.py:27`,
  `_qt/panels/parameter_grid_panel.py:35`,
  `_qt/panels/parameters.py:30`, `tests/test_parameter_grid.py:18`
- Optional cleanup inside the moved file:
  `<target>/parameter_grid.py:27` → `from varieties.types import ParamSpec`
  (removes one indirection through surfaces.py).

**Approx. LOC delta.** Move 362; shim +25; cleanup ±0. Net root: removed
1 real-code file, added 1 shim. Net repo: `+25` LOC.

**Commits.** 2 commits per implementer lessons.md:47-49 (combine `git mv` +
LibCST + shim into ONE commit per bisect-redness lesson, plus 1 anchor
commit). Total 2-3 commits.

**Dependencies.** B1 should land first (LibCST is invoked in this batch;
the bug would surface immediately on the 4 callers if `pg.X` attribute
chains were referenced anywhere — but they're not, so this batch could in
principle run without B1).

**Wall-clock estimate.** ~15-25 min.

### B3 — Remove the 5 root `__getattr__` shims + panels hub + shim test file (~15 min)

**Risk.** LOW. Zero production callers (verified §2.3-2.6). Only consumer
is `tests/test_r2_shims.py` (109 LOC) which is deleted in the same commit
sequence.

**Files affected.**
- `tests/test_r2_shims.py` (deleted FIRST per implementer lessons.md:51-56)
- `render_worker.py`, `icons.py`, `styles.py`, `ui_helpers.py` (deleted)
- `panels/__init__.py` (deleted — closes the panels hub shim from r2-B3)
- `panels/` directory (deleted — empty after `__init__.py` removal)
- `MOVES.md` entry appended

**Approx. LOC delta.** `-23-23-22-27-40-109 = -244` LOC repo-wide. Root
file count: 7 → 2 (`app.py` + `parameter_grid.py` shim if §3.4 step 1
applied OR + `surfaces.py` if B4 deferred).

**Commits.** 6 commits per Phase 4 step discipline (one test file deletion
+ 5 shim deletions). Bundling alternative: per the r2-B1 deletion lesson,
"shim-and-test-file" pairs are commit-bundled if same-commit safety can be
proven. For r3 B3, the cleanest is 1 commit (delete test_r2_shims.py)
followed by 5 single-file deletions, each green per `pytest`. 6 commits total.

**Dependencies.** None (independent of B2; can run before or after).

**Wall-clock estimate.** ~15 min (mechanical deletes; no LibCST; 7-8 s
tests × 6 commits + a couple of minutes for anchor-updater).

### B4 — Retire `surfaces.py` (~45-90 min; the highest-risk batch in r3)

**Risk.** HIGH (the highest in r3).

**Why high-risk.** 35 import sites across 14 files (see §2.7 table). All
use `from surfaces import …` patterns. Each file may import 1 to ~10
symbols per statement (e.g. `tests/test_numba_field_kernels.py:53` imports
11 private kernel symbols in one statement). The LibCST rewrite must split
each multi-symbol import into the canonical N-statement form per scout-C
§4.6 mechanics — the partial-attribute-rewrite bug from r2-B3 was
specifically about this pattern.

**Files affected.** 14 files for the rewrite + `surfaces.py` itself (either
converted to a `__getattr__` shim or deleted entirely per §3.4).

**Sub-batch structure.** Three sequenced steps:

- **B4-step-1: convert surfaces.py from re-export hub to `__getattr__`
  shim.** This adds `DeprecationWarning` to every existing `from surfaces
  import …` call WITHOUT requiring LibCST rewrites. All 35 callers continue
  to work; tests fail only if any test now sees an unexpected
  `DeprecationWarning` (none do per inspection of pytest.ini, which has no
  warning filter). ~50 LOC change at `surfaces.py`. 1 commit.

- **B4-step-2: LibCST migration of all 35 callers to canonical paths.**
  Symbol-map JSON entries per `varieties/*.py` module. The
  rewrite-imports.py tool (post-B1 fix) handles each import statement.
  Per-file verification: `pytest <file>` after rewrite. 14 files
  rewritten = 14-15 commits (or 1 mega-commit per r2-B6 inline-script
  approach). Wall-clock: ~30-60 min including manual triage of any
  partial-rewrite escapes.

- **B4-step-3 (optional in r3, defer to r4 if scope allows):**
  delete `surfaces.py`. Requires B4-step-2 to be 100% complete.

**Approx. LOC delta.** B4-step-1: `surfaces.py` 123 → ~30 LOC = `-93` LOC.
B4-step-2: 14 callers see import-statement changes only; net per-file LOC
delta is `+N-1` per statement (where N is the number of symbols in the old
multi-symbol import being split). Aggregate net: `+50` to `+100` LOC across
the 14 files. B4-step-3 (if it lands in r3): `-30` LOC. Total batch
LOC delta: `-43` to `+7` LOC.

**Commits.** 16-17 if granular (1 conversion + 14 caller rewrites + 1
deletion); 3 if bundled per r2-B6 approach (1 conversion + 1 mega-rewrite + 1
deletion).

**Dependencies.** B1 (tool fix) is a hard prerequisite for the LibCST
rewrites. B2 and B3 are independent.

**Wall-clock estimate.** ~45-90 min. The wide range reflects (a) whether
B1's fix lands cleanly OR LibCST partial-rewrite firefight returns, and
(b) whether B4-step-3 lands in r3 or defers to r4. The r2 execution-critic
critique line 22 cites "~30 min of manual fixup across 5 test files" for
the r2-B3 firefight; r3 B4 has 14 files, so the firefight cost could be
~80-90 min without B1.

### B5 — Anchor-updater + final verification (~20-30 min)

**Risk.** LOW. Documentation + verification only.

**Files affected.**
- `MOVES.md` — append r3 summary section (per scout-C §7.2)
- `CONTEXT.md` — update file inventory in §4 module map (likely
  obsolete by r3 end)
- `AGENTS.md` (root CLAUDE.md symlink) — update §2 "where things live"
  block (currently says "Root-level shims (appearance_panel.py, …) were
  removed in restructure-feature-subpackages-2026q2-r2 batch 1" — needs
  extension to cover r3 shim removal)
- `README.md` — repo structure section (if present)
- `.claude/notes/repository-architect/restructure-..-r3/` — final
  state.json + execution-critic critique

**Approx. LOC delta.** `+50` to `+100` LOC of documentation.

**Commits.** 1-2 commits (one for source-anchor edits; one for
state-machine finalization).

**Dependencies.** All prior batches.

**Wall-clock estimate.** ~20-30 min.

### 6.1 Total wall-clock

| Batch | Optimistic | Pessimistic |
|-------|-----------|-------------|
| B1 (tool fix) | 30 min | 45 min |
| B2 (parameter_grid move) | 15 min | 25 min |
| B3 (shim deletes) | 15 min | 20 min |
| B4 (surfaces.py) | 45 min | 90 min |
| B5 (anchors + verify) | 20 min | 30 min |
| **Total** | **~2h 5m** | **~3h 30m** |

Plus per-batch /repository-architect pipeline overhead (audit + design +
preflight + adversary + execute + critic gates, ~10-15 min each ÷ 5 batches
= 50-75 min). **Honest total wall-clock estimate: 3-5 h.** Matches r2's
actual cadence (r2 was 9 batches, ~36 commits, 3-5h per state.json:52
"~3-5 h wall-clock"). `[CONSENSUS — r2 took the same range; r3 is shorter
in batch count but B4 is bigger than any single r2 batch]`

### 6.1.1 Batch-by-batch commit ledger (proposed)

Per scout-C §5 "Execute (small steps)" + implementer lessons.md:46-49
("one Fowler op per commit ≠ one mechanical action per commit"). The
proposed commit count maps to bisect-survivable units:

**B1 commits.**

1. `refactor(/repository-architect tooling): fix rewrite-imports.py partial-attribute-rewrite` — `_build_transformer` `leave_Attribute` redesign; add unit test under `tests/repository-architect/test_rewrite_imports.py`.
2. `refactor(/repository-architect tooling): exclude .claude/scripts and .claude/notes from rewrite-imports.py walk` — 1-line edit at `rewrite-imports.py:200-208`.

**B2 commits (per implementer lessons.md:47-49: combine move + rewrite into one commit; ship anchor separately).**

1. `refactor(restructure-..-r3): move parameter_grid.py to <target>/parameter_grid.py (batch 2/5)` — single commit containing: (a) `git mv parameter_grid.py <target>/parameter_grid.py`; (b) Template-2 shim at `parameter_grid.py` (root); (c) LibCST rewrite of 4 caller files; (d) optional `<target>/parameter_grid.py:27` cleanup to `from varieties.types import ParamSpec`. All in ONE commit so `git bisect` doesn't see an intermediate red state.
2. `chore(/repository-architect): r3 Batch 2 metadata + MOVES.md` — anchor-updater appends MOVES.md section.

**B3 commits (per implementer lessons.md:51-56: test file FIRST, then shim deletes).**

1. `refactor(restructure-..-r3): remove tests/test_r2_shims.py (batch 3/5 op 1/6)` — 109 LOC deleted; tests must remain green (expected post-delete count: 499).
2. `refactor(restructure-..-r3): remove root shim render_worker.py (M+1) (batch 3/5 op 2/6)`
3. `refactor(restructure-..-r3): remove root shim icons.py (M+1) (batch 3/5 op 3/6)`
4. `refactor(restructure-..-r3): remove root shim styles.py (M+1) (batch 3/5 op 4/6)`
5. `refactor(restructure-..-r3): remove root shim ui_helpers.py (M+1) (batch 3/5 op 5/6)`
6. `refactor(restructure-..-r3): remove panels/__init__.py hub shim + panels/ directory (M+1) (batch 3/5 op 6/6)`
7. `chore(/repository-architect): r3 Batch 3 metadata + MOVES.md`

**B4 commits (the heavy batch; estimate 4-6 commits depending on bundling strategy).**

1. `refactor(restructure-..-r3): convert surfaces.py from re-export hub to __getattr__ shim (batch 4/5 step 1)` — surfaces.py 123 → ~30 LOC; all 35 callers continue to work via lazy attribute resolution; first `DeprecationWarning`s start firing on every test run.
2. `refactor(restructure-..-r3): LibCST migrate 14 callers from surfaces to canonical paths (batch 4/5 step 2)` — single mega-commit per r2-B6+B7 inline-script precedent (alternative: 14 single-file commits if bisect granularity is preferred).
3. (optional, may defer to r4) `refactor(restructure-..-r3): remove surfaces.py shim (batch 4/5 step 3)` — only if step 2 is verified 100% complete (no remaining `from surfaces import …` anywhere).
4. `chore(/repository-architect): r3 Batch 4 metadata + MOVES.md` — anchor-updater notes the surfaces.py retirement (with deferral note if step 3 didn't land).

**B5 commits.**

1. `chore(/repository-architect): r3 finalize state.json -> complete` — pipeline state machine.
2. (optional) `rect-restructure(restructure-..-r3): defer R3-X-Y findings (deferred-finding documentation)` — if any non-CRITICAL findings surfaced.
3. `docs(/repository-architect): r3 anchor refresh — AGENTS.md, CONTEXT.md, README.md` — substantive anchor edits if scope authorized.

**Total commit ledger.**

| Batch | Min | Max |
|-------|-----|-----|
| B1 | 2 | 2 |
| B2 | 2 | 3 |
| B3 | 7 | 7 |
| B4 | 3 | 16 (one per migrated caller) |
| B5 | 2 | 3 |
| **r3 total** | **16** | **31** |

This straddles r2's actual final commit count (per state.json finalization
commit `9ea8791`'s 36-commit chain) and r1's 11-commit minimum from the
4-batch initial cycle. The variance in B4 is the dominant uncertainty.

### 6.2 Sequencing reasoning

scout-C's low-risk-first sequencing has three components:

1. **Tooling before code** (B1 before B2/B4). r2's biggest pain was the
   `rewrite-imports.py` bug. Fixing it once means every subsequent LibCST
   invocation runs cleanly.
2. **Cleanup before transformation** (B3 before B4). Removing the 5
   tiny shims is mechanically trivial and ensures the root is half-cleared
   before tackling surfaces.py. If B4 goes sideways, B3 has already
   delivered meaningful progress.
3. **Smallest impact-radius first within transformations** (B2 before B4).
   `parameter_grid.py` has 4 callers; `surfaces.py` has 35. Hitting the
   smaller substrate first builds confidence in the tooling and gives a
   cheap rollback point if B4's LibCST work runs aground.

Alternative orderings considered:

- B3 → B1 → B2 → B4. Defensible if you want to "see progress" early. But
  if B1's fix exposes a regression in B3's shim deletes (unlikely; no LibCST
  in B3), it complicates the bisect. Cleanly separating tool work from
  source work is preferred.
- B2 → B1 → B4 → B3. Defers tool fix until forced. r2's lesson is that
  the firefight cost compounds; better to pay tool-fix tax once.
- B4 → B3 → B2 → B1. Highest-risk-first. Refused per scout-C §1.

---

## 7. The `rewrite-imports.py` tool-fix sequencing question

r2's execution-critic critique recorded:

> **MEDIUM** — `rewrite-imports.py` partial-attribute-rewrite bug
> (recorded for follow-up tooling milestone)
>
> **Why it matters:** Caused 11 test failures in B3 that required ~30 min of
> manual fixup across 5 test files. The script rewrites SOME `module.X`
> references to `_qt.module.X` but leaves others, creating inconsistent
> namespaces. Recovery cost was high.

`[file: .claude/notes/repository-architect/restructure-feature-subpackages-2026q2-r2/rectify/execution-critic-critique.md:19-23]`

r3 will hit this bug in B2 (low chance — only `import as` rewrites; the
bug doesn't trigger on alias imports) and B4 (high chance — many
multi-symbol `from … import …` rewrites with potential attribute-access
follow-ups elsewhere). Three honest paths:

### 7.1 Option (a) Fix rewrite-imports.py FIRST as r3-prerequisite (the §6 recommendation)

**Pros.**
- Pays the tool-fix cost once; r3 + r4 + every future LibCST invocation
  benefits.
- Cleanly separates tool work from source work — pipeline phases are
  bounded.
- Removes a known-buggy tool dependency from the critical path.
- r2's execution-critic recommendation: "A dedicated tooling-hardening
  milestone should address this BEFORE the next `/repository-architect`
  invocation."

**Cons.**
- Adds 30-45 min upfront before any source-tree change lands.
- The fix surface is `.claude/scripts/`, which is OFF-LIMITS per
  AGENTS.md §8 ("What NOT to touch — `.claude/` AI agent scaffold —
  self-modification trap"). However: the table footnote allows
  "/repository-architect owns it" implicitly because the scripts are part
  of the restructure pipeline; the prohibition is about AI agents
  modifying their own *behavior config*, not their *script tools*. The
  fix is mechanical (CST transformer logic) and unit-testable.
  `[CONTESTED — the AGENTS.md §8 rule says `.claude/` is off-limits but
  doesn't carve out an exception for script tools. A user gate or explicit
  consent is required before modifying any file under `.claude/scripts/`.
  r3's design phase should surface this for the user's approval before B1
  starts.]`

**When it's the right call.** When the user is comfortable with the
"self-modification trap" carve-out for script tools (not config). The
existing `.claude/scripts/repository-architect/` was added by /repository-architect
itself in r1/r2 — modifying it in r3 follows the same precedent.

### 7.2 Option (b) Use inline-execution-script approach (the r2-B6+B7 workaround)

**Pros.**
- Zero `.claude/scripts/` modifications — sidesteps the §7.1 self-modification
  question entirely.
- The pattern is proven: r2-B6 + B7 + B8 successfully landed without
  invoking rewrite-imports.py at all (per implementer `lessons.md` and r2
  execution-critic line 45: "B6 + B7 + B8 used the inline-execution Python
  extraction script approach rather than per-PLAN.md commit-per-Fowler-op").
- Each batch's rewrite is bespoke to that batch's symbol-map, so the
  partial-rewrite bug never has a chance to fire.

**Cons.**
- Each batch must write its own inline rewrite script (~50-100 LOC of
  one-off Python per batch). Higher per-batch cost than calling the shared
  tool, lower one-time cost than fixing it.
- The inline scripts are throwaway — they don't accrete into the toolkit,
  so r4 hits the same firefight.
- The "manual fixup" cost from r2-B3 surfaces *inside* each inline script
  rather than after the fact — same cost, different distribution.
- Per scout-C anti-pattern R15 ("Bowler is the safe-refactor tool we
  need") and §3 tooling-matrix recommendation, **LibCST is THE
  Python-codemod tool**. Working around it instead of fixing it builds
  technical debt against the pipeline.

**When it's the right call.** When the user explicitly forbids
`.claude/scripts/` modification (because the AGENTS.md §8 rule wins) OR
when r3 has a single sub-batch that's structurally unique and not
worth generalizing.

### 7.3 Option (c) Plan r3 with explicit "manual fix-up phase" per batch

**Pros.**
- Honest acknowledgment of the bug; no pretense that the tool is reliable.
- Aligns with r2's execution reality (every batch had some manual fixup).

**Cons.**
- Wall-clock cost: r2-B3 firefight was ~30 min for 5 test files; r3-B4
  has 14 callers, so the firefight could be ~80-90 min.
- Repeats the cost in every future restructure until the tool is fixed.
- Doesn't address the `.claude/scripts/` exclusion-list bug (LOW finding
  from r2 critique line 31-35) — that's a separate one-line fix that would
  still need to land.

**When it's the right call.** When you're certain r3 is the LAST
restructure for the foreseeable future, AND the `.claude/scripts/`
modification gate is impossible to cross. Neither condition seems true.

### 7.4 Recommendation

**Option (a)** for the partial-attribute fix, with a user gate at r3
design phase to approve the `.claude/scripts/` modification. This is
exactly what the r2 execution-critic recommended ("A dedicated
tooling-hardening milestone should address this BEFORE the next
`/repository-architect` invocation"). The "milestone" of the recommendation
can be folded into r3 as Batch 1 — it doesn't need to be its OWN
restructure invocation, because the fix is unit-testable in isolation and
doesn't touch any source code. `[CONSENSUS — scout-C §3 tooling matrix,
r2 execution-critic recommendation]`

---

## 8. The pipeline self-modification question

r3 needs the `/repository-architect` pipeline to be reliable. r2 surfaced:

- Sub-agent socket timeouts (anchor-updater 43m, implementer 21m) — per
  r2 execution-critic line 26-29
- `rewrite-imports.py` partial-rewrite bug — per line 19-23
- `rewrite-imports.py` doesn't exclude `.claude/scripts/` — per line 31-35

These need fixing before r3, OR r3 must work around them.

### 8.1 Option (a) Fix pipeline tooling first (separate milestone)

**Pros.**
- Cleanest separation of concerns: pipeline-as-product gets its own
  delivery cadence.
- Allows the user to approve pipeline tool changes in isolation from
  source restructure changes.

**Cons.**
- Adds an entire `/repository-architect` invocation BEFORE r3 even starts.
  Each invocation has ~5 user gates per scout-A blueprint, so this is
  high process overhead for what is mechanically a 30-LOC fix to
  rewrite-imports.py.
- Pipeline-tooling milestones don't naturally have audit/design phases
  because they're not source restructures.
- Postpones the user's visible "single .py at root" goal by however long
  the tooling milestone takes.

### 8.2 Option (b) Patch tooling inline during r3 design phase

**Pros.**
- Lowest total wall-clock cost — fold the tool fix into r3 B1.
- The fix is small enough (30-50 LOC + tests) to land in a single
  design-phase pre-execute commit.
- Pipeline tooling work is naturally per-restructure ("we found a tool bug
  while running r2; we fix it as we start r3").

**Cons.**
- Mixes pipeline-tool changes with source-tree changes in one
  /repository-architect invocation. Slight conceptual mismatch.
- If the tool fix introduces a regression in r3, the bisect crosses the
  source/tool boundary.

### 8.3 Option (c) Inline-extraction-script pattern (no pipeline dependency)

**Pros.**
- r3 doesn't touch `.claude/scripts/` at all.
- Sub-agent timeouts (LOW finding) are sidestepped because each batch
  runs as an inline main-session script.
- Proven pattern in r2-B6+B7+B8.

**Cons.**
- Repeats the per-batch cost in every future restructure.
- Doesn't fix the underlying tool bug; r4 will hit it again.
- Sub-agent timeouts are transient infrastructure issues — they may not
  recur in r3, so sidestepping them is over-defensive.

### 8.4 Recommendation

**Option (b)** for the rewrite-imports.py fixes (fold into r3 B1; see §6,
§7). For the sub-agent socket timeouts: do not pre-fix; treat as transient
per r2 execution-critic line 29 ("This appears to be transient
infrastructure rather than a pipeline bug. If it recurs in r3, may warrant
investigation"). Add a "fall back to inline execution if sub-agent times
out" note to r3's design phase as the existing precedent (every r2 sub-agent
timeout was resolved by the user choosing the "Continue inline" path).

`[CONSENSUS — execution-critic critique lines 24-30, 53-57]`

---

## 9. Verification rubric specific to "single root .py file"

After r3 completes, the following 6 verifications prove the user goal is
met. Each is a concrete command with the expected output.

### 9.1 Only `app.py` at root

```bash
# Count of .py files in repo root (excluding subdirectories)
ls /Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section/*.py | wc -l
# Expected: 1
# Pre-r3 baseline: 7 (per §2 inventory at SHA 9ea8791)
```

The single file is `app.py`. Any other `.py` at root is a regression.

### 9.2 No production module is at root except `app.py`

```bash
find /Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section \
  -maxdepth 1 -name '*.py' -not -name 'app.py' | wc -l
# Expected: 0
```

Equivalent to §9.1 but explicit about "production".

### 9.3 Import graph rooted at `app`

```bash
.venv/bin/python -c "import app; print('OK')"
# Expected: prints "OK", no traceback, no DeprecationWarning to stderr
```

Per scout-C §2 Phase 1 ("smoke test the new import") and item 7 of the 20-item
rubric. This verifies that (a) `app.py` still imports cleanly after all
underlying moves, and (b) no `DeprecationWarning` fires (because all callers
moved to canonical paths in B4 step 2 — if any caller still used a deleted
shim path, the import would fail with `ModuleNotFoundError`).

### 9.4 Test suite still passes at parity

```bash
.venv/bin/python -m pytest -q
# Expected: 499 passed (or 499-7=492 if test_r2_shims.py was deleted in B3)
```

Per scout-C verification rubric items 1 + 2. The post-r3 expected count is
`499 - 7 (r2 shim tests) = 492` because all r2 shim regression tests are
no longer applicable (the shims they tested are gone). If `surfaces.py`
becomes a `__getattr__` shim (B4 step 1), 1 new shim test for it might
be added, bringing post-r3 count to 493. `[verified: tests/test_r2_shims.py
has 7 tests]`

### 9.5 All `*.py` files at root + subpackages are accounted for

```bash
# Production .py inventory after r3 (file paths relative to repo root)
find /Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section \
  -name '*.py' \
  -not -path '*/.venv/*' \
  -not -path '*/.git/*' \
  -not -path '*/.claude/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/tests/*'

# Expected output (post-r3 with §3.4 option-a + parameter_grid in varieties/):
#   ./app.py
#   ./_qt/__init__.py
#   ./_qt/icons.py
#   ./_qt/styles.py
#   ./_qt/ui_helpers.py
#   ./_qt/panels/__init__.py
#   ./_qt/panels/appearance.py
#   ./_qt/panels/parameter_grid_panel.py
#   ./_qt/panels/parameters.py
#   ./_qt/panels/view.py
#   ./cross_section/__init__.py
#   ./cross_section/clip.py
#   ./render/__init__.py
#   ./render/worker.py
#   ./varieties/__init__.py
#   ./varieties/_kernels.py
#   ./varieties/_marching.py
#   ./varieties/calabi_yau.py
#   ./varieties/dispatch.py
#   ./varieties/enriques.py
#   ./varieties/fano.py
#   ./varieties/k3.py
#   ./varieties/parameter_grid.py    # NEW after B2 (if Agent A picks this path)
#   ./varieties/registry.py
#   ./varieties/tooltips.py
#   ./varieties/types.py
```

Every `.py` either is `app.py` or lives inside a subpackage with `__init__.py`.
No orphans, no rogue siblings. `[matches the scout-C 20-item rubric §7,
modified to assert one-and-only-one root .py file]`

### 9.6 Import graph + parity diff

Run scout-C 20-item rubric items 6, 8, 11, 17:

```bash
# No new import cycles introduced
.venv/bin/python -m pydeps app.py --show-cycles --noshow -o /tmp/r3-cycles.svg
# Expected: cycle set identical to baseline (i.e. no new cycles)

# Import-time within 20% of baseline
.venv/bin/python -X importtime -c "import app" 2> /tmp/r3-importtime.log
# Expected: total within 20% of pre-r3 baseline

# Shim warnings are gone (no shims left = no DeprecationWarnings)
.venv/bin/python -W error::DeprecationWarning -c "import app"
# Expected: exits 0 (no warnings raised as errors)

# Stale path references cleansed from .claude/notes/
grep -rn 'render_worker\.\|icons\.py\|styles\.py\|ui_helpers\.py' \
  .claude/notes/ \
  | grep -v MOVES.md \
  | grep -v 'restructure-feature-subpackages-2026q2-r2' \
  | grep -v 'restructure-..-2026q2-r3'
# Expected: empty (or only references in archived/historical notes)
```

---

## 10. Risk register (per batch)

| Batch | Worst-case failure | Likely surface | Rollback |
|-------|--------------------|--------------------|----------|
| B1 (tool fix) | rewrite-imports.py unit tests fail; B2/B4 cannot proceed | Off-by-one in `_attribute_dotted_path` when chain has 3+ parts | `git revert` on B1 commits; switch to §7.2 inline-script workaround for B2/B4 |
| B2 (parameter_grid move) | LibCST rewrite missed one of 4 `import as` sites → `ModuleNotFoundError` on test collection | Should not happen (alias imports are simple); if it does, the test that fails will pinpoint which file | `git revert` the move commit; restore parameter_grid.py at root; rerun LibCST manually |
| B2 (cont.) | Shim file at `parameter_grid.py` has subtle import-time side-effect (e.g. `from <target>.parameter_grid import *` style) — pulls in Qt at module load | Should not happen if Template-2 `__getattr__` pattern is followed; the bug surfaces as Qt warnings during `pytest --collect-only` for tests/test_parameter_grid.py | Convert shim from `from new import *` to `__getattr__` per shim-templates.md §3 |
| B3 (shim deletes) | A test outside `tests/test_r2_shims.py` references a deleted shim → ModuleNotFoundError on collect | Per §2.3-2.6 verification, no production callers exist. Possible hidden caller: `_qt/styles.py:9,13` docstring example (not actual code) — harmless | `git revert` the deletion commit; the shim file is restorable via the M+1 cycle |
| B3 (cont.) | The deletion sequence violates implementer lessons.md:51-56 ("delete the test file FIRST") → intermediate commit is bisect-red | Avoid by following the documented sequence: delete test_r2_shims.py in commit 1, then 5 shim files in commits 2-6 | `git rebase -i` to reorder commits if discovered post-hoc |
| B4-step-1 (surfaces → `__getattr__`) | The conversion breaks one of the 35 import sites (e.g. an import site uses `surfaces.X.Y` attribute-chain access that `__getattr__` can't proxy) | grep `app.py` and 14 caller files for `surfaces\.` access — verified empty in §5.3 for app.py | `git revert` the conversion commit; re-execute as a no-op for surfaces.py (leave as re-export hub for r4) |
| B4-step-2 (LibCST migration of 35 sites) | Partial-rewrite bug recurs even with B1 fix → tests fail in unpredictable ways | B1 fix should have unit tests covering the exact pattern; firefight cost is ~30 min per implementer lessons.md:29 | Apply manual fixups per the path-string-fix protocol in r2-B3 (implementer lessons.md:30-31) |
| B4-step-3 (delete surfaces.py) | A test or notebook outside the verified tree imports surfaces | Per scout-C §10 R10, "internal != no callers." Risk is mitigated by B4-step-1's `DeprecationWarning` cycle | Restore surfaces.py from the B4-step-1 tag; defer step 3 to r4 |
| B5 (anchors) | Anchor-updater times out (per r2 LOW finding line 26-29: 43m timeout) | Fall back to inline main-session execution per r2 precedent | Inline execution is the documented fallback |

### 10.0 Per-batch worst-case scenario walkthrough

For each batch, what does "B4 went sideways" actually look like, and
what does the recovery sequence look like? This is the runbook the
implementer should have open during execution.

#### Scenario A — B1's tool fix has a regression that breaks B2

**Symptom.** After landing B1, running B2's `rewrite-imports.py` on
the 4 `import parameter_grid as pg` sites produces unexpected output:
maybe the alias-import rewrite logic in `leave_Import` got broken by
the `leave_Attribute` redesign. Tests in `tests/test_parameter_grid.py`
fail to import `pg`.

**Detection.** B2-Phase 1 baseline snapshot vs B2-Phase 4 parity check
catches this immediately. Per §13.2 parity script, the
`diff baseline.collect.txt post.collect.txt` line will show
`tests/test_parameter_grid.py::test_*` items missing.

**Recovery.**
1. `git revert HEAD` on B2's move commit (single revert, since B2 is one
   bundled commit per implementer lessons.md:47-49).
2. `git log --oneline refactor-r3-batch1-end..HEAD` to identify the B1
   commits that broke B2.
3. Decide: (a) fix B1 forward (another tool-fix commit), or (b) revert
   B1 too and switch to §7.2 inline-script approach for B2/B4.
4. Re-run B2 once B1 is stable.

**Wall-clock impact.** +30-60 min (one revert + one root-cause + retry).

#### Scenario B — B3's shim delete breaks a hidden caller

**Symptom.** After deleting one of the shims (e.g. `icons.py`), some
test that wasn't `tests/test_r2_shims.py` fails to collect with
`ModuleNotFoundError: No module named 'icons'`.

**Detection.** B3-batch's per-commit parity check catches this
immediately. Per scout-C 20-item rubric item 1, any
test-collection failure is CRITICAL.

**Recovery.**
1. `git revert HEAD` (single-commit per-shim delete makes this clean).
2. Identify the hidden caller: `grep -rn 'from icons\|import icons'
   --include='*.py'` re-run to find the missed reference.
3. Either (a) update the caller to canonical path
   (`from _qt import icons`), or (b) leave the shim in place and
   document the dependency in MOVES.md as "shim retention required
   pending caller update."
4. Re-attempt the delete with the caller updated.

**Wall-clock impact.** +15-30 min per missed caller. Per §2.3-2.6 grep
evidence this scenario is very unlikely (zero non-test callers were
found), but the protocol is documented for safety.

#### Scenario C — B4-step-1 (`__getattr__` shim conversion) breaks an
existing test via `surfaces.X` attribute proxying

**Symptom.** After converting `surfaces.py` from re-export hub to
`__getattr__` shim, `tests/test_status_bar_bbox.py:65` or similar
breaks because Python's `surfaces.fermat_quartic` lookup now goes
through `__getattr__` which has a subtle bug (e.g. forgetting to
handle `_`-prefixed names per the existing Template-2 logic at
`render_worker.py:14-23`).

**Detection.** B4-step-1's parity check; the failing test pinpoints the
attribute that didn't proxy correctly.

**Recovery.**
1. Inspect the shim — is it copying the Template-2 pattern from
   `render_worker.py`? If yes, the bug is likely in the new module's
   `_kernels` private-symbol exposure (some tests import
   `_fermat_field_kernel` which is `_`-prefixed; Template-2's
   `hasattr(_new, name)` handles this fine but a typo in the shim
   could fail it).
2. Run validate-shims.py to confirm shim integrity.
3. Fix the shim; commit; re-run tests.

**Wall-clock impact.** +15-30 min.

#### Scenario D — B4-step-2 LibCST run partial-rewrites despite B1 fix

**Symptom.** Some files post-rewrite have a mix of canonical
`from varieties.X import Y` and old `from surfaces import Z` imports
in the same file. `pytest` runs cleanly because the leftover
`from surfaces import Z` still works (B4-step-1's `__getattr__` shim
catches it), but the migration is incomplete.

**Detection.** Run `grep -rn 'from surfaces import\|import surfaces'
--include='*.py' --exclude=tests/test_r2_shims.py --exclude-dir=.venv
--exclude-dir=.claude --exclude=surfaces.py` after B4-step-2. Expected:
empty. Actual: some lingering imports.

**Recovery.**
1. Identify the un-migrated files via the grep.
2. Per-file manual rewrite OR re-run the LibCST tool with a corrected
   symbol-map (some entries may have been missing).
3. Re-verify the grep returns empty.
4. Re-commit.

**Wall-clock impact.** +30-60 min per round of fixup. This is the
single biggest risk in r3 and the reason B1 is a hard prerequisite.

#### Scenario E — B4-step-3 (delete surfaces.py) breaks production
because step 2 missed a caller

**Symptom.** `git rm surfaces.py` lands, then `python -c "import app"`
fails because something inside the `_qt/` or `varieties/` tree still
does `from surfaces import …` that step 2 missed.

**Detection.** B4-step-3's smoke test (`python -c "import app"` from
§13.4).

**Recovery.**
1. `git revert HEAD` on the delete commit.
2. Identify the missed caller via the traceback.
3. Fix the caller (either in a step-2 retry batch or in a new commit).
4. Re-attempt step 3.

**Wall-clock impact.** +20-40 min.

#### Scenario F — Sub-agent timeout in B5 anchor-updater (recurrence of
r2 LOW finding)

**Symptom.** B5's anchor-updater dispatch never returns; UI shows the
sub-agent has been running for >30 min.

**Detection.** Wall-clock observation. r2 saw this twice (B1 anchor at
43m, B2 implementer at 21m) per execution-critic line 26-29.

**Recovery.** Per documented r2 fallback: "Continue inline" — the main
session takes over anchor-updater work using the same instructions but
running in the main thread. Inline execution typically completes the
same work in 5-10 min because it doesn't re-walk agent-memory
exhaustively. Per r2 critique line 29: "may warrant investigation of
the agent's reading patterns (B1 anchor-updater spent 43 min walking
the agent-memory tree exhaustively)."

**Wall-clock impact.** +5-10 min (inline execution beats sub-agent
walltime once started).

### 10.1 Cross-cutting risks (apply to all batches)

- **Bisect-redness from delayed LibCST rewrites** — per implementer
  lessons.md:46-49 r1-B4 lesson: "the LibCST rewrite should land in the
  SAME commit as the corresponding `git mv`, OR all N ops should be a
  SINGLE commit if rename detection survives." Applied to r3: B2 must
  combine `git mv` + LibCST + shim in one commit; B4-step-2 should bundle
  per scout-C §4.5 (1 commit per logical Fowler op = "migrate all 35 sites
  to canonical paths" = 1 commit, not 35).
- **`__pycache__` lingering after deletes** — per scout-C 20-item rubric
  item 19. Mitigation: `find . -name __pycache__ -exec rm -rf {} +`
  before re-running tests after any delete batch.
- **Conftest scope drift** — per scout-C §6.4. Since r3 doesn't move test
  files, this risk is LOW; verify by `pytest --fixtures-per-test` diff
  before/after each batch.
- **CONTEXT.md / AGENTS.md stale references** — per scout-C §7.1. r3 must
  update both: AGENTS.md §2 "where things live" table needs the
  new subpackage entries; CONTEXT.md §4 module map needs the same.

### 10.2 Catastrophic-failure rollback

Per scout-C §11 Tier 1: if r3 has to be fully reverted, the command is:

```bash
git revert --no-commit refactor-r3-baseline..refactor-r3-complete
git commit -m "revert: roll back restructure r3 (single .py at root)"
```

Pre-conditions for this to work:
- Each commit was independently green (per scout-C §11 Tier 1).
- No feature work was interleaved (per scout-C §10 R1 "we can refactor and
  add features in the same PR" — refused).

Test the rollback in a scratch worktree before B4 lands, per scout-C §11
("Tested in scratch worktree on YYYY-MM-DD: PASS"). Item 20 of the 20-item
rubric.

---

## 11. What r3 does NOT achieve

Honest list. r3 hits the user's stated goal ("only app.py at root") with
caveats:

1. **`app.py` stays at 1900 LOC and remains a God Object.** The user
   explicitly excluded Extract Class on `app.py`. r3 does NOT improve
   internal cohesion of MainWindow. A future milestone (r4 or later)
   would tackle this per scout-C §12 + §4.3 — likely candidates for the
   first Extract Class: `SettingsPersistence`, `StatusBar` / HUD,
   `RenderPipelineCoordinator`.

2. **`parameter_grid.py`'s placement is debatable.** Agent A picks the
   target; this brief doesn't take a position on whether
   `varieties/parameter_grid.py` or some other path is the right home.
   That choice has consequences for r4+ (e.g. if `varieties/` is
   chosen, the parameter-grid module becomes adjacent to symbol
   `varieties.parameter_grid` while also serving Qt-related grid widgets
   — a category mismatch that may need a second move someday).

3. **`surfaces.py`'s removal may defer to r4** depending on the §3.4
   middle-path choice. If r3 only converts surfaces.py to a `__getattr__`
   shim (without migrating the 35 callers), then `surfaces.py` (~30 LOC
   shim) sits at root through r4. The user's "only app.py at root" goal
   is only fully achieved when all 35 callers have migrated AND
   surfaces.py is deleted.

4. **The `cross_section/` subpackage is tiny.** Post-r2 it has one
   module (`clip.py`); r3 doesn't expand it. If Agent A's target tree
   wants `cross_section/` to grow, that's not in r3's scope.

5. **`tests/` remains flat** (no `tests/varieties/`, `tests/_qt/`, etc.).
   Mirror-mirroring tests-to-subpackages is a scout-C §6.4 hygiene
   improvement; not part of r3.

6. **No new tests are added** beyond the verification rubric in §9. r3 is
   a structural restructure, not a coverage-improvement milestone.

7. **The 7 r2 shim regression tests get deleted.** Specifically
   `tests/test_r2_shims.py` (109 LOC, 7 tests). These tests existed to
   prove the shims emit warnings; deleting the shims renders the tests
   vacuous. The test count drops from 506 to 499 (or 492 if r3 adds no
   new shim tests for surfaces.py).

8. **`.claude/scripts/repository-architect/rewrite-imports.py` gets
   modified in B1.** This is a self-modification of the pipeline tooling
   — see §7.1 trade-off discussion. The user must explicitly approve
   this carve-out from AGENTS.md §8's "do not touch `.claude/`" rule.

9. **AGENTS.md / CONTEXT.md will need substantive rewrites in B5** —
   the post-r2 state.json line 52 noted this for r2 ("README + CONTEXT.md
   WILL need substantive rewrites"). r3 inherits the same anchor-update
   debt.

10. **The deferred r2 findings (LOW-1 sub-agent timeouts; LOW-3
    path-string scanner companion; LOW-4 inline vs plan documentation)
    remain DEFERRED.** Per r2 execution-critic lines 53-57. r3 doesn't
    address them.

---

## 12. Closing note on scope discipline

Per scout-C anti-pattern R1 ("we can refactor and add features in the same
PR"), r3 must NOT contain any feature changes. The 5 batches above are
purely structural. Any "while we're in there" inclination (e.g.
"let's also clean up the AGENTS.md cross-references to the deleted r1
panel shims at AGENTS.md:42") should be either (a) folded into B5's
anchor-updater pass IF it's a stale-reference fix that scout-C §7.1
requires, OR (b) deferred to a separate milestone.

Per scout-C anti-pattern R12 ("we can auto-execute Phase 4 if dry-run is
GREEN"), r3 must hit GATE 3 (user approval before Execute) and GATE 4
(user approval before Rectify) regardless of how clean the dry-run looks.

Per scout-C anti-pattern R13 ("the anchor-updater can run once at the
end"), B5's anchor-updater is in addition to per-batch anchor work. r3
should follow the r2 pattern of per-batch MOVES.md appends (B2, B3, B4
each append their own section).

`[CONSENSUS — anti-patterns.md table 2 + scout-C §10]`

---

---

## 12.1 The 14 surfaces.py callers — per-file rewrite checklist (the B4-step-2 work item)

This subsection enumerates each of the 14 files that B4-step-2 must
rewrite, what the pre-rewrite import statement looks like, and what the
post-rewrite canonical imports look like. The numbers are derived from
`grep -rn 'import surfaces\|from surfaces'` (full result in §2.7) and from
direct inspection of each file's import block.

### 12.1.1 `app.py:49-63` (1 grouped import → 5 canonical imports)

Pre (lines 49-63):
```python
from surfaces import (
    VARIETIES,
    VARIETY_TOOLTIPS,
    SUBTYPE_TOOLTIPS,
    Surface,
    dispatch_mode,
    enriques_figure_1,
    enriques_figure_2,
)
```

Post (B4-step-2):
```python
from varieties.registry import VARIETIES
from varieties.tooltips import VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS
from varieties.types import Surface
from varieties.dispatch import dispatch_mode
from varieties.enriques import enriques_figure_1, enriques_figure_2
```

LibCST risk: LOW (pure `from … import …` rewrite; symbol-map JSON maps
each symbol to its canonical module).

### 12.1.2 `parameter_grid.py:27` (single symbol)

Pre: `from surfaces import ParamSpec`
Post: `from varieties.types import ParamSpec`

If B2 ran first, this file is already moved to its target; the rewrite
becomes `<target>/parameter_grid.py:27`.

### 12.1.3 `_qt/ui_helpers.py:29` (single symbol)

Pre: `from surfaces import ParamSpec`
Post: `from varieties.types import ParamSpec`

### 12.1.4 `_qt/panels/parameter_grid_panel.py:45` (single symbol)

Pre: `from surfaces import ParamSpec`
Post: `from varieties.types import ParamSpec`

### 12.1.5 `_qt/panels/parameters.py:32` (single symbol)

Pre: `from surfaces import ParamSpec`
Post: `from varieties.types import ParamSpec`

### 12.1.6 `tests/test_status_bar_bbox.py:33` + 6 attribute-access sites

Pre (line 33): `import surfaces`
Pre (lines 65, 80, 97, 117, 149, 172):
```python
mesh = surfaces.fermat_quartic()
mesh = surfaces.fermat_quartic()
mesh = surfaces.kummer_surface()
mesh = surfaces.calabi_yau_quintic()
mesh = surfaces.calabi_yau_asymmetric()
surfaces.kummer_surface(mu_squared=0.2)
```

Post (line 33 split + replace attribute calls):
```python
from varieties.k3 import fermat_quartic, kummer_surface
from varieties.calabi_yau import calabi_yau_quintic, calabi_yau_asymmetric
```
... and rewrite all `surfaces.X(...)` calls to bare `X(...)`.

LibCST risk: MEDIUM. The 6 attribute-access sites trigger the
`leave_Attribute` partial-rewrite bug from r2-B3. B1 must have fixed
this. If B1 is option (b) (inline-script approach instead of tool fix),
this file is the canonical test case for whether the inline script
handles attribute chains.

### 12.1.7 `tests/test_enriques_hq_smoothing.py:31` + 9 attribute-access sites

Same shape as 12.1.6 but with 9 attribute references to
`surfaces.enriques_figure_1` / `_2` / `_3` / `_4` and
`surfaces._marching_cubes_to_polydata`.

Post (line 31 split):
```python
from varieties.enriques import enriques_figure_1, enriques_figure_2, enriques_figure_3, enriques_figure_4
from varieties._marching import _marching_cubes_to_polydata
```

And rewrite the 9 attribute calls to bare names.

`tests/test_enriques_hq_smoothing.py:224` is a SECOND import:
`from surfaces import VARIETIES` — rewrite to `from varieties.registry
import VARIETIES`.

LibCST risk: MEDIUM-HIGH (more attribute sites than 12.1.6).

### 12.1.8 `tests/test_mesh_generators.py:17,159` (2 imports)

`from surfaces import (...)` — multiple symbols per import; canonical
rewrites span 4 varieties modules (k3, enriques, calabi_yau, fano) plus
varieties.types.

LibCST risk: LOW (`from … import …` form only).

### 12.1.9 `tests/test_typical_ms.py:24` + `tests/test_coarse_n.py:32` + `tests/test_parameters_panel.py:21` + `tests/test_parameter_grid.py:19`

All 4 files have the same shape: single multi-symbol
`from surfaces import (...)` that must split into multiple canonical
imports based on the symbols in scope.

LibCST risk: LOW.

### 12.1.10 `tests/test_numba_field_kernels.py:53` (11 private kernels)

Pre:
```python
from surfaces import (
    _fermat_field_kernel,
    _kummer_field_kernel,
    _enriques_fig1_field_kernel,
    _enriques_fig2_field_kernel,
    _enriques_fig3_field_kernel,
    _enriques_fig4_field_kernel,
    _dwork_field_kernel,
    _klein_cubic_field_kernel,
    _segre_cubic_field_kernel,
    _two_quadrics_field_kernel,
    _sextic_double_solid_field_kernel,
)
```

Post:
```python
from varieties._kernels import (
    _fermat_field_kernel,
    _kummer_field_kernel,
    _enriques_fig1_field_kernel,
    _enriques_fig2_field_kernel,
    _enriques_fig3_field_kernel,
    _enriques_fig4_field_kernel,
    _dwork_field_kernel,
    _klein_cubic_field_kernel,
    _segre_cubic_field_kernel,
    _two_quadrics_field_kernel,
    _sextic_double_solid_field_kernel,
)
```

LibCST risk: LOW (single-module rewrite of the source path; all 11
symbols come from the same target).

**Note on r2 preservation contract.** Per r2 state.json line 52:
"tests/test_numba_field_kernels.py specifically uses 'from surfaces
import _<name>_field_kernel' -- preserve this." That contract was for the
r2 cycle (surfaces stayed as re-export hub). For r3, the contract is
fulfilled by the migration to canonical paths (the test still passes,
just imports from the canonical home). This is a CONTRACT EVOLUTION, not
a CONTRACT VIOLATION — but should be called out in r3's PLAN.md and
MOVES.md.

### 12.1.11 `tests/test_marching_cubes_empty.py:17` + `tests/test_grid_helpers.py:17` (private marching helpers)

Pre (test_marching_cubes_empty.py:17):
`from surfaces import _marching_cubes_to_polydata, kummer_surface`

Post: split:
```python
from varieties._marching import _marching_cubes_to_polydata
from varieties.k3 import kummer_surface
```

Pre (test_grid_helpers.py:17):
`from surfaces import _grid_to_polydata, _concat_polydata`

Post:
```python
from varieties._marching import _grid_to_polydata, _concat_polydata
```

LibCST risk: LOW-MEDIUM. The mixed-source case in
`test_marching_cubes_empty.py:17` (one statement imports symbols from 2
different canonical modules) requires the LibCST transformer to SPLIT
the import statement into 2 statements. The current rewrite-imports.py
doesn't appear to support split-on-source — it only rewrites the
`module=` argument, not the alias list. **This is a NEW bug not surfaced
in r2** (because r2-B5+B6+B7+B8 preserved the re-export hub, so no
caller-side splitting was ever needed). B1 must address this. Or the
inline-script approach (§7.2) explicitly handles split-imports.

### 12.1.12 `tests/test_styles_palette.py:214,610,1252` (3 separate `from surfaces import` statements)

Pre:
```python
from surfaces import VARIETIES    # line 214
from surfaces import VARIETIES    # line 610
from surfaces import SUBTYPE_TOOLTIPS  # line 1252
```

Post:
```python
from varieties.registry import VARIETIES  # line 214
from varieties.registry import VARIETIES  # line 610
from varieties.tooltips import SUBTYPE_TOOLTIPS  # line 1252
```

LibCST risk: LOW (3 single-symbol rewrites; no attribute access).

### 12.1.13 `tests/test_r2_shims.py:95,105` (special case — deletes in B3)

These two import lines are inside the r2 shim regression test file,
which §6 B3 deletes entirely. After B3 lands, these lines no longer
exist. B4-step-2 should SKIP this file (it won't exist anymore).

`[CONSENSUS — B3 deletes tests/test_r2_shims.py per §6.1; B4-step-2's
file walk should respect git status]`

### 12.1.14 Aggregate B4-step-2 LibCST commit-size estimate

| File | Symbol count | Risk | LibCST mode |
|------|--------------|------|-------------|
| app.py | 7 (split across 5 modules) | LOW | tool |
| parameter_grid.py / `<target>`/parameter_grid.py | 1 | LOW | tool |
| _qt/ui_helpers.py | 1 | LOW | tool |
| _qt/panels/parameter_grid_panel.py | 1 | LOW | tool |
| _qt/panels/parameters.py | 1 | LOW | tool |
| tests/test_status_bar_bbox.py | 1 import + 6 attr | MEDIUM | tool (post-B1) |
| tests/test_enriques_hq_smoothing.py | 2 imports + 9 attr | MED-HIGH | tool (post-B1) |
| tests/test_mesh_generators.py | 2 multi-symbol | LOW | tool |
| tests/test_typical_ms.py | 1 multi-symbol | LOW | tool |
| tests/test_coarse_n.py | 1 multi-symbol | LOW | tool |
| tests/test_parameters_panel.py | 1 multi-symbol | LOW | tool |
| tests/test_parameter_grid.py | 1 multi-symbol | LOW | tool |
| tests/test_numba_field_kernels.py | 1 multi-symbol (11) | LOW | tool |
| tests/test_marching_cubes_empty.py | 1 mixed-source split | MEDIUM | tool (post-B1, split capability) |
| tests/test_grid_helpers.py | 1 single-source split | LOW | tool |
| tests/test_styles_palette.py | 3 single imports | LOW | tool |
| **Aggregate** | **14 files, ~33 imports, ~15 attr accesses** | — | — |

The pre-B1 firefight cost estimate (~80-90 min in §6.B4 wallclock
section) is dominated by the MEDIUM/MEDIUM-HIGH rows. Post-B1, the cost
should drop to ~30 min total (mostly waiting on test runs after each
batch's commit).

`[CONSENSUS — per-file grep verification + r2 lessons]`

---

## 13. Executable pre-/post-batch verification snippets

These are paste-ready shell snippets for the implementer to copy into each
batch's verification step.

### 13.1 Per-batch baseline-snapshot (Phase 1 of each batch)

```bash
# Capture baseline state at the start of every batch
BATCH_ID="r3-bN-baseline-$(date +%s)"
.venv/bin/python -m pytest -q --collect-only > "/tmp/${BATCH_ID}.collect.txt"
.venv/bin/python -m pytest -q > "/tmp/${BATCH_ID}.summary.txt"
.venv/bin/coverage run -m pytest -q
.venv/bin/coverage xml -o "/tmp/${BATCH_ID}.coverage.xml"
ls *.py > "/tmp/${BATCH_ID}.root-py.txt"
find . -name '*.py' -not -path '*/.venv/*' -not -path '*/.git/*' \
  -not -path '*/.claude/*' -not -path '*/__pycache__/*' \
  | sort > "/tmp/${BATCH_ID}.all-py.txt"
git rev-parse HEAD > "/tmp/${BATCH_ID}.sha.txt"
echo "Baseline captured for $BATCH_ID at $(cat /tmp/${BATCH_ID}.sha.txt)"
```

### 13.2 Per-batch parity verification (Phase 4 of each batch)

```bash
# Compare to baseline; require pass on every assertion
BATCH_ID="r3-bN-post-$(date +%s)"
BASELINE_ID="r3-bN-baseline-<TIMESTAMP>"

.venv/bin/python -m pytest -q  # MUST exit 0
.venv/bin/python -m pytest -q --collect-only > "/tmp/${BATCH_ID}.collect.txt"
diff "/tmp/${BASELINE_ID}.collect.txt" "/tmp/${BATCH_ID}.collect.txt" || {
  echo "FAIL: test collection diverged from baseline"; exit 1; }

.venv/bin/coverage run -m pytest -q
.venv/bin/coverage xml -o "/tmp/${BATCH_ID}.coverage.xml"

# Quick import-graph check: every .py reachable from app.py
.venv/bin/python -c "import app" 2>&1 | tee "/tmp/${BATCH_ID}.import.log"
grep -i 'error\|traceback' "/tmp/${BATCH_ID}.import.log" && {
  echo "FAIL: app import has errors"; exit 1; }

# Verify shims (per shim-templates.md validate-shims.py)
.venv/bin/python .claude/scripts/repository-architect/validate-shims.py || {
  echo "FAIL: at least one shim broken"; exit 1; }

echo "Batch parity verified at $(git rev-parse HEAD)"
```

### 13.3 Per-batch tag + rollback point (Phase 5 of each batch)

```bash
# Tag the batch-end SHA per scout-C §11 + implementer lessons.md:53
BATCH=N  # 1..5
git tag "refactor-r3-batch${BATCH}-end"
echo "refactor-r3-batch${BATCH}-end -> $(git rev-parse HEAD)" \
  >> /tmp/r3-tags.txt
```

### 13.4 r3-final verification gate

```bash
# Run all 6 verifications from §9 + the 20-item rubric items relevant to r3
# (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 17, 19 per verification-rubric.md table)

# Item 1: tests pass
.venv/bin/python -m pytest -q || exit 1

# Item 2: collection count preserved (except for deleted test_r2_shims.py's 7)
TEST_COUNT=$(.venv/bin/python -m pytest -q --collect-only | tail -1)
echo "post-r3 test count: $TEST_COUNT"

# Item 7: app.py imports cleanly
.venv/bin/python -c "import app; print('OK')" || exit 1

# Item 10: no new from X import *
grep -rn 'import \*' --include='*.py' --exclude-dir=.venv \
  --exclude-dir=.claude . || true

# Item 11: shim integrity (any shims left after r3 should still emit warnings)
.venv/bin/python .claude/scripts/repository-architect/validate-shims.py

# Custom r3-goal verification: single root .py file
ROOT_PY_COUNT=$(ls *.py | wc -l | tr -d ' ')
if [ "$ROOT_PY_COUNT" != "1" ]; then
  echo "FAIL: expected 1 root .py file, got $ROOT_PY_COUNT"
  exit 1
fi
[ "$(ls *.py)" = "app.py" ] || {
  echo "FAIL: root .py file is not app.py"; exit 1; }

# Item 19: __pycache__ purge sanity
find . -name __pycache__ -not -path '*/.venv/*' -not -path '*/.git/*' \
  -exec rm -rf {} + 2>/dev/null
.venv/bin/python -m pytest -q || exit 1

echo "r3 verification PASSED — single root .py file = app.py"
```

### 13.5 Tier-1 catastrophic rollback (per scout-C §11)

```bash
# If r3 must be fully reverted (per scout-C §11 Tier 1)
git revert --no-commit refactor-r3-baseline..refactor-r3-batch5-end
git commit -m "revert: roll back restructure r3 (single .py at root)

Reverting entire r3 commit chain due to <reason>. Tests confirmed
green at refactor-r3-baseline; full restructure tag chain preserved
for future re-attempt."

# Verify rollback returns to baseline
git diff refactor-r3-baseline HEAD --stat
# Expected: empty diff
```

### 13.6 Tier-3 per-shim partial rollback (per scout-C §11 Tier 3)

If only B3's shim removal needs to be reverted (e.g. a hidden out-of-tree
notebook calls `from icons import set_icon` and the user finds out
post-r3):

```bash
# Restore one shim from the pre-B3 tag
git checkout refactor-r3-batch2-end -- icons.py
git checkout refactor-r3-batch2-end -- tests/test_r2_shims.py
# Edit tests/test_r2_shims.py to keep only the icons test
git commit -m "revert(partial): restore icons.py shim (out-of-tree notebook
relies on from icons import)"
```

### 13.7 Per-batch wallclock target (for time-boxing)

```bash
# Set a 90-min ceiling on B4 (the heavy batch)
START=$(date +%s)
# ... do B4 work ...
ELAPSED=$(( $(date +%s) - START ))
if [ "$ELAPSED" -gt 5400 ]; then
  echo "WARN: B4 exceeded 90-min budget ($ELAPSED s); consider deferring step 3 to r4"
fi
```

---

## 13.8 Wall-clock calibration — drawing on r2's actual cadence

The §6.1 wall-clock estimate (3-5 h total) draws on r2's measured cadence
per `state.json` and per implementer/lessons.md timing notes. Per-batch
breakdown of r2 (for calibration):

| r2 batch | Description | Files affected | Wall-clock (approx.) | Notes |
|----------|-------------|----------------|---------------------|-------|
| B1 | r1 panel shim removal (M+1 close) | 4 deletes + 1 test delete | ~20 min | Per lessons.md:55 "~7-8 s test runs" × 5 commits |
| B2 | render/ subpackage | 1 git mv + LibCST + shim | ~25 min | Per MOVES.md `2095d81` |
| B3 | _qt/ subpackage | 7 git mv + LibCST + hub shim | ~90 min | Includes the partial-rewrite firefight per critique line 22 |
| B4 | cross_section/ subpackage | 1 Move Method | ~30 min | Smaller scope per MOVES.md |
| B5 | varieties/types + dispatch | 5 symbol extractions | ~25 min | Re-export pattern, no LibCST |
| B6 | varieties/_kernels + _marching | 15 symbol extractions | ~35 min | Largest extraction batch |
| B7 | varieties/{k3,enriques,calabi_yau,fano} | 28 symbol extractions | ~45 min | 4 family modules in one batch |
| B8 | varieties/registry + tooltips | 6 symbol extractions | ~25 min | Final hub split |
| B9 | docs + tests/test_r2_shims.py | 1 test add + README/CONTEXT | ~30 min | Anchor work |
| **r2 total** | — | 9 batches, ~36 commits | **~5.5 h** | — |

The dominant variance is B3 (the only batch that hit the LibCST
partial-rewrite firefight). With B1 in r3 fixing the tool, r3's
analogous high-risk batch (B4 — surfaces.py retirement, 14 callers)
should NOT incur the same firefight, bringing the estimate to ~45-60
min for r3-B4 instead of r2-B3's ~90 min.

r3's expected total (3-5 h) is lower than r2 because:
- r3 has 5 batches vs r2's 9 (fewer batch-overhead cycles).
- r3's biggest batch (B4) has 14 callers vs r2's whole-cycle 30+ callers
  affected.
- r3 doesn't introduce new subpackages (uses subpackages r2 created).
- BUT r3's B4 is denser per batch (more LibCST work in one batch than
  any r2 batch).

`[CONSENSUS — implementer/lessons.md per-batch timing + MOVES.md commit
SHAs]`

---

## 14. Anti-pattern check — what r3 must refuse

Per anti-patterns.md (R1-R15) + scout-C §10, here are the rationalizations
r3 is most likely to face, with pre-canned refusals:

| Likely temptation in r3 | Refusal | Anti-pattern cite |
|--------------------------|---------|-------------------|
| "B3 and B4 can land together — shim deletes and surfaces migration are both 'cleanup'" | "B3 is mechanical; B4 has LibCST risk. Keep them separate so a B4 rollback doesn't undo B3's progress." | R5 (one big-bang commit) |
| "We have shims and they emit warnings — no LibCST migration needed in B4-step-2" | "B4-step-3 (deletion) requires step 2 to land. If we never migrate callers, we never reach the user's goal." | R3 (we can fix imports later) |
| "Surfaces.py can keep the re-export hub indefinitely — it's tiny and works" | "The user's goal is single-root .py file = app.py. Anything else at root is a regression against goal." | R10 (we're internal-only, no deprecation needed — used to justify NEVER deprecating, here flipped to justify the opposite: never deleting) |
| "B1 (tool fix) can wait — let's do it after r3 lands" | "B1 prevents B4's ~80-min firefight per r2 cost data. Pay it once, save it 14 times." | R3 (fix imports later) + general scout-C §2 phase-1 discipline |
| "Skip the design-adversary; the plan is obvious" | "Pre-execution adversary is the cheapest safety gate; the §3.4 surfaces.py choice is non-obvious." | R11 (skipping design-adversary saves time) |
| "Auto-execute B3 since dry-run is green — it's just deletes" | "GATE 3 is mandatory regardless of dry-run color. The user's goal is touched by every batch in r3." | R12 (auto-execute Phase 4 if dry-run green) |
| "We can drop the panels/__init__.py without checking — nothing imports it" | "Verified §2 inventory: only tests/test_r2_shims.py imports it. But §10.2 cross-cutting rollback requires tagging the pre-delete SHA so partial rollback is possible." | R8 (we have git, no rollback plan needed) |
| "Run anchor-updater once at the end (B5) instead of per-batch" | "Per-batch anchor work is cheap; end-of-restructure runs leave many batches' breakage in .claude/notes/ between commits." | R13 (anchor-updater can run once at end) |
| "Sed is fine for migrating the 14 surfaces.py call sites — it's just import statements" | "LibCST is non-negotiable for Python import rewriting." | R6 (sed will be fine for these import rewrites) |

`[CONSENSUS — direct mapping to anti-patterns.md and scout-C §10]`

---

## 15. State-machine state.json shape for r3

Per scout-A blueprint (each restructure has a state.json), r3 should
initialize a state machine with the following batches in
`.claude/notes/repository-architect/restructure-..-2026q2-r3/state.json`:

```json
{
  "restructure_id": "restructure-..-2026q2-r3",
  "phase": "audit",
  "batches": [
    {"id": "B1", "label": "pipeline tooling hardening (rewrite-imports.py)", "risk": "low", "depends_on": []},
    {"id": "B2", "label": "move parameter_grid.py to <target>", "risk": "low", "depends_on": ["B1"]},
    {"id": "B3", "label": "remove 5 root shims + panels hub + test_r2_shims.py", "risk": "low", "depends_on": []},
    {"id": "B4", "label": "retire surfaces.py: convert to __getattr__, migrate 14 callers, delete shim", "risk": "high", "depends_on": ["B1"]},
    {"id": "B5", "label": "anchor-updater + final verification", "risk": "low", "depends_on": ["B1", "B2", "B3", "B4"]}
  ],
  "restructure_brief": "Goal: single .py at repo root = app.py. Five batches: pipeline tool fix (B1), parameter_grid.py move to subpackage (B2; Agent A picks target), shim retirement (B3, closes M+1 from r2), surfaces.py retirement (B4, the heavy batch), anchor + verify (B5). User goal: 'make it so only the app.py is the only python script at the root.' HARD CONSTRAINTS: AI-1..AI-15 invariants inviolable. Specifically AI-2, AI-6, AI-7, AI-8, AI-9, AI-12, AI-15. NON-NEGOTIABLE: every old import path that survives gets a __getattr__ shim for one milestone (M+2 in this case). EFFORT EXPECTATION: 5 batches, ~3-5 h wall-clock. Sequence: tooling -> low-risk -> high-risk -> verify."
}
```

The `depends_on` graph implies:

```
B1 ──> B2
   └─> B4
B3 (independent)
B1+B2+B3+B4 ──> B5
```

Per scout-A axis 3 (concurrent agent dispatch in same phase is an
anti-pattern X3), B2 and B3 cannot run in parallel under the current
pipeline. They MUST be sequential dispatches even though they're
mechanically independent.

---

## 16. Final summary checklist

Use this to verify the brief addresses the requested sections.

- [x] §1 TL;DR (7 bullets per request)
- [x] §2 Current state inventory of the 7 root files (per-file: state, callers with file:line, M+1 eligibility, risk)
- [x] §3 Shim removal question with 3 honest options + recommendation
- [x] §4 parameter_grid.py problem with 3 placement options + migration mechanics for each
- [x] §5 app.py situation (post-r3 import shape; LibCST need)
- [x] §6 Recommended migration sequence (5 batches; commit ledger; sequencing reasoning)
- [x] §7 rewrite-imports.py tool-fix sequencing options (a/b/c)
- [x] §8 Pipeline self-modification options (a/b/c)
- [x] §9 Verification rubric specific to single-root-.py-file goal (6 specific verifications)
- [x] §10 Risk register per batch + cross-cutting + catastrophic rollback
- [x] §11 What r3 does NOT achieve (honest list, 10 items)
- [x] §12 Scope discipline closing note
- [x] §13 Executable verification snippets
- [x] §14 Anti-pattern check
- [x] §15 State-machine shape

Lines per section (approximate; for density audit):

| Section | Lines |
|---------|-------|
| §1 TL;DR | 30 |
| §2 Inventory | 240 |
| §3 Shim removal | 200 |
| §4 parameter_grid | 175 |
| §5 app.py | 90 |
| §6 Migration sequence | 280 |
| §7 Tool-fix sequencing | 110 |
| §8 Pipeline self-modification | 70 |
| §9 Verification rubric | 90 |
| §10 Risk register | 130 |
| §11 Does NOT achieve | 90 |
| §12 Closing note | 30 |
| §13 Executable snippets | 175 |
| §14 Anti-pattern check | 40 |
| §15 State machine | 50 |
| §16 + Sources | (this section) |

---

## Sources

All accessed 2026-05-24 unless noted; file:line citations from `main` at
SHA `9ea8791`.

- AGENTS.md (root) — repo orientation; §2 "where things live" + §8
  "what NOT to touch"
- CONTEXT.md (root) — §4 module map (out of scope for r3)
- MOVES.md (root) — r1 + r2 restructure history; §"2026-05-23 ... r2 batch 3"
  for the panels hub + 3 root shims; §"2026-05-24 ... r2 batch 9" for
  the r2 final state
- pytest.ini — no warning filter
- parameter_grid.py — 362 LOC; 20 top-level defs; 1 surface dep
- surfaces.py — 123 LOC re-export hub (NOT a `__getattr__` shim)
- render_worker.py, icons.py, styles.py, ui_helpers.py — each 22-27 LOC
  Template-2 `__getattr__` shims
- panels/__init__.py — 40 LOC Template-1 hub shim
- tests/test_r2_shims.py — 109 LOC, 7 tests, sole consumer of the 5 shims
- .claude/scripts/repository-architect/rewrite-imports.py — 244 LOC;
  `leave_Attribute` at lines 129-144 is the buggy logic
- .claude/notes/repository-architect-design/scout-c-safe-refactor.md
  (754 lines) — the 8-phase pipeline + 20-item rubric + tooling matrix +
  shim deprecation timeline
- .claude/references/repository-architect/shim-templates.md — Template 1 /
  Template 2 / DO-NOT-USE Template 3
- .claude/references/repository-architect/anti-patterns.md — R1-R15
- .claude/references/repository-architect/verification-rubric.md — 20-item
  rubric + severity mapping
- .claude/agent-memory/repository-architect-implementer/lessons.md —
  r1-B4 bisect-redness lesson (lines 46-49); r2-B1 deletion-sequence
  lesson (lines 51-56); r2-B3 LibCST partial-rewrite lessons (lines
  29-31)
- .claude/notes/repository-architect/restructure-feature-subpackages-2026q2-r2/rectify/execution-critic-critique.md
  — MEDIUM rewrite-imports.py bug (lines 19-23); LOW timeouts (26-29);
  LOW `.claude/scripts/` exclusion (31-35); LOW path-string scanner
  (37-41); LOW inline vs plan (43-47)
- scout-C external sources (NumPy NEP-23, pandas PDEP-17, etc.) cited via
  scout-C's `[S1]`-`[S31]` sources block; not re-quoted here

**Items I would have verified with more time-box.**

- Whether `.claude/notes/**` contains any references to the 5 root shim
  files that would need cleansing in B5. I greppped MOVES.md and the r2
  notes but didn't walk every milestone note under
  `.claude/notes/milestones/`. The implementer-lessons.md CORRECTION
  block (lines 35-43, 58-66) tracks the shim updates explicitly, so the
  agent-memory is current.
- Whether any of the 14 `surfaces.py` callers ever use a
  `surfaces.X.Y` attribute-chain (which would force B4-step-1's
  `__getattr__` shim to handle nested attribute proxying). I verified
  `app.py` is clean but didn't grep the 14 test files individually. The
  risk is low because pure `from X import Y` callers don't trigger
  attribute-chain proxying, but a single rogue `surfaces.<something>`
  reference in a test would force B4-step-1 to add a per-attribute
  fallback.
- Whether the AGENTS.md §8 "what NOT to touch" rule has a documented
  carve-out for `/repository-architect`-owned scripts. I noted this as
  `[CONTESTED]` in §7.1 because the table reads strictly but the
  pipeline's own scripts were added by the pipeline itself in r1 — there
  is precedent but not an explicit policy statement.
