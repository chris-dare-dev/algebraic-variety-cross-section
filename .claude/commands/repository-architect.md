---
description: Run the 5-phase repository-restructure pipeline (Audit -> Design -> Pre-flight -> Execute -> Critique+Rectify) on the AVC repo to drive the tree toward Tree-Structure Principle (TSP-1..TSP-11) compliance — root thinness, responsibility-named subpackages, single-direction import DAG, call-graph-aligned module tree, AND entry-point scripts that read as pseudocode (delegating to high-level factory functions and orchestrators in subpackages, never carrying business logic at root). Use when the user invokes /repository-architect, says "restructure the repo", "audit and propose a new layout", "reorganize for AI-agent navigability", or asks to safely move/split/rename source files. This is the HIGHLY DISRUPTIVE pipeline — runs rarely (quarter-cadence at most), demands five user gates, and never auto-executes moves. Skip for single-file moves (just `git mv`) or for non-source-tree changes (use other pipelines).
argument-hint: "<id> [--brief \"...\"] [--audit-only] [--design-only] [--resume]"
---

# /repository-architect — 5-phase safe-restructure pipeline

Run the canonical 5-phase AVC repository-restructure pipeline:
**Audit -> Design -> Pre-flight -> Execute -> Critique+Rectify**

The pipeline's NORTH STAR is the **Tree-Structure Principle (TSP-1..TSP-11)** in the dedicated section below.  Every phase is graded against TSP.  Process discipline (gates, parity checks, shims, anchors) is in service of an architectural goal: drive the repo toward a tree-shaped Python package where (a) the bulk of source lives in responsibility-named, importable subpackages, (b) only 1-2 entry-point scripts remain at the root, and (c) those entry points read as pseudocode — composed of calls to high-level factory functions and orchestrators that themselves live in the subpackage tree.  A restructure that closes every CRITICAL finding but leaves the tree mis-shaped, or leaves a root script bloated with business logic, is a FAILURE.

This pipeline is the formalization of the safe-large-refactor playbook
documented in `.claude/notes/repository-architect-design/scout-c-safe-refactor.md`
combined with the orchestration patterns from `/milestone-pipeline`.  It
extends the 4-phase milestone shape with an explicit **Pre-flight** gate
(Phase 3) because the blast radius of an unverified restructure is much
higher than the blast radius of an unverified milestone fix.

> NOTE: prior-run notes under `.claude/notes/repository-architect-design/` pre-date the TSP north star.  Their safe-refactor mechanics remain load-bearing; their architectural framing does not.

**Arguments:** $ARGUMENTS — parse as `<id> [--brief "..."] [--audit-only] [--design-only] [--resume]`

- `<id>` — required; restructure-shaped id, convention `restructure-<scope>-<YYYYqN>-r<N>`, e.g. `restructure-panels-2026q3-r1`, `restructure-surfaces-split-2026q4-r1`, `restructure-ai-navigability-2026q3-r1`.  If omitted, STOP and ask: "What is the restructure id?  (Expected: `restructure-<scope>-<YYYYqN>-r<N>`.)"
- `--brief "..."` — use the given string verbatim as the restructure brief.  Persisted into `state.restructure_brief`.
- `--audit-only` — stop after Phase 1.  Used for "I just want to know what's broken" runs.
- `--design-only` — stop after Phase 2 (Design + design-adversary).  Useful for proposing a restructure plan without committing to execution.
- `--resume` — re-enter the pipeline at the phase determined by the resume routing table below.

---

## When to invoke / When NOT to invoke

**Invoke `/repository-architect` when:**
- User runs `/repository-architect <id>` or `/repository-architect <id> --brief "..."`.
- User says "restructure the repo", "propose a new layout", "split surfaces.py", "introduce a panels subpackage", "reorganize for AI-agent navigability".
- A /capability-scout or /roadmap output identifies a restructure as a foundational opportunity (then the operator dispatches /repository-architect against the proposed scope).
- The repo has crossed a navigability threshold: file >2000 LOC, >15 top-level .py files, or AI-agent context-rot incidents.

**Current AVC tree-shape context (post-r3, 2026-05):** root holds only `app.py` (~1900 LOC).  Four source subpackages exist (`_qt/`, `render/`, `cross_section/`, `varieties/`) with layer direction enforced by 2 import-linter contracts.  Status against TSP: **TSP-1 PASS** (count), **TSP-11 FAIL** (`app.py` is a monolith, not a pseudocode entry point) — `app.py` decomposition is the highest-priority open restructure target.  Full AVC-specific TSP application (CLAUDE.md §2 historical-note override, AI-9 migration shape, r1-r3 deferral chronology, AI-2 flat-tests carve-out) lives in `.claude/references/repository-architect/avc-tsp-status.md` — read at Phase 1, Phase 2, and Phase 5 entries.

**TSP-triggered invocation cases (see TSP section below):**
- Root has >2 top-level `.py` files containing logic (not counting `__init__.py`, `conftest.py`, `setup.py`) — TSP-1.
- Any internal import cycle exists (`pydeps --show-cycles` non-empty) — TSP-3.
- `lint-imports` reports a KEPT-violated contract, or a new sibling cross-import has been merged without a corresponding contract update — TSP-2.
- Any module's call graph shows it calling >5 distinct internal modules — that's an orchestration layer, and it should be promoted to a parent with its callees demoted to children — TSP-8.
- A subpackage contains a `utils.py` / `helpers.py` / `common.py` / `misc.py` / `lib.py` / `core.py` (the responsibility-name banlist) — TSP-5.
- The `app.py` retention justification under TSP-7 has materially changed (e.g. AI-9 re-entrancy was lifted, or a Qt main-window decomposition pattern proven elsewhere in AVC) — the carve-out needs re-evaluation.

**Do NOT invoke when:**
- **Single-file move or rename** — just `git mv` it.  The 5-phase overhead is not worth it for a one-file change.
- **Adding a new variety or feature** — use `/milestone-pipeline` (the repository structure is fine; you're adding content).
- **Touching only `.claude/` or `.github/`** — these are OUT OF SCOPE per the user's restructure brief.  Edit them directly.
- **Pure documentation reorganization** (CONTEXT.md sections, README.md headings) — write directly, no pipeline.
- **Touching the test suite Qt-policy (AI-2)** — that's a separate decision that needs its own roadmap milestone.
- **A previous `/repository-architect` run is `execute-running` or `rectify-running`** — finish it first, do not start a parallel restructure.
- **Splitting only reduces LOC without improving tree shape (TSP-10)** — if the result isn't a TREE (deeper, dependency-ordered, sibling-import-free), don't restructure; file it as tech-debt and move on.
- **The existing tree IS already shallow and the user wants to add a feature** — use `/milestone-pipeline`; restructure isn't a substitute for feature work.

---

## The Tree-Structure Principle (TSP) — the load-bearing contract

This section is the **SINGLE SOURCE OF TRUTH** for the 11 principles — other reference files cite TSP-N by number; the verbatim text lives here.

The TSP framework expresses one conviction: **a Python repository should be a TREE of importable modules.** Branches are responsibility-named subpackages; leaves are pure modules; the root is reserved for 1-2 thin entry points.  AVC enforces the layer-direction half mechanically with import-linter; the rest (responsibility naming, decomposition depth, call-graph alignment, entry-point pseudocode) is enforced by this pipeline.

**TSP-1. Root is thin — both in count AND in content.**  A healthy Python repo root contains AT MOST 1-2 executable entry-point scripts (e.g. `app.py`, `cli.py`, or one `pyproject.toml`-declared console-script).  Everything else is in subpackages.  **Triggers a restructure if root has >2 top-level `.py` files containing logic (not counting `__init__.py`, `conftest.py`, `setup.py`).**  Thinness is BOTH a file-count constraint (this principle) AND a per-file content constraint (see TSP-11 below): a single 1900-LOC root script is no more "TSP-1 compliant" than four 500-LOC root scripts — the count check is necessary, the pseudocode check (TSP-11) is sufficient.  AVC's current post-r3 state passes TSP-1's count check (`app.py` only) but FAILS TSP-11's content check.

**TSP-2. Subpackages are dependency-ordered.**  The package tree is a DAG where leaves are pure utilities/types with no internal deps, mid-layer is domain logic, root is orchestration.  Imports flow UP the tree only.  **Sibling cross-imports are forbidden** — siblings communicate via a parent or via a shared lower layer.  In AVC, this is enforced mechanically by import-linter's two forbidden contracts in `pyproject.toml`; PLAN.md MUST keep those contracts green (or propose a contract update with explicit user gate).

**TSP-3. No internal import cycles.**  A cycle is a CRITICAL finding in any phase.  `pydeps --show-cycles` must report an empty set both pre- and post-restructure.

**TSP-4. Each module has a single responsibility.**  File LOC is a SIGNAL of multi-responsibility, not the cause.  `>500 LOC` is the early warning, `>800 LOC` is the alarm (per evaluator checklist item 17).  Every module that exceeds the alarm threshold MUST either be decomposed in the current restructure OR carry a TSP-7 annotation (a one-paragraph justification AND a named follow-up restructure-id — open-ended retentions are rejected).  AVC's `app.py` is the canonical example: it has exceeded both thresholds for cycles r1-r3 without a named follow-up, so it currently FAILS TSP-4 and TSP-7 simultaneously — the next restructure run that touches `app.py` must address this.

**TSP-5. Module names describe RESPONSIBILITY, not present implementation or architectural layer.**  Concrete names: `panels/`, `varieties/`, `cross_section/`, `render/`, `appearance/`, `clip/`, `tooltips/`.  Banned names (auto-FAIL): `utils.py`, `helpers.py`, `common.py`, `misc.py`, `lib.py`, `core.py`, `manager.py`, `services.py`, `controllers.py`.  A subpackage may use `_kernels.py` / `_marching.py` style underscore-prefixed names for implementation-detail modules INSIDE a responsibility-named subpackage (e.g. `varieties/_kernels.py`) — that's an existing AVC pattern and remains allowed.

**TSP-6. Scripts at root are replaced with subpackages + thin entry points.**  When TSP-1 fires (root grows past 1-2 logic files) or a subpackage grows a monolith module that needs splitting, the decomposition target is:
```
<name>/                       # subpackage (was: <name>.py)
+-- __init__.py               # thin re-export shim for back-compat (emits DeprecationWarning per shim-templates.md)
+-- _entry.py or cli.py       # thin entry point if any (argparse + dispatch); for AVC GUI apps, the Qt main-window class belongs here
+-- <topic-1>.py              # extracted responsibility 1
+-- <topic-2>.py              # extracted responsibility 2
+-- <topic-3>/                # if topic 1+2 share, they get a sub-subpackage
```
The root-level `<name>.py` becomes a 3-line shim that imports from `<name>.<entry>` and re-exports for back-compat (one milestone shim window per `shim-templates.md`).  AVC precedent: r2 retired `panels.py`, `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py` into `_qt/panels/` following exactly this shape — see MOVES.md.

**What "thin entry point" means concretely** (see TSP-11 for the full specification): the entry-point file's body is composed of CALLS to factory functions and orchestrators that live in subpackages — it does not itself contain business logic, math, parsing, I/O, validation, or panel/widget construction code.  For AVC's `app.py` specifically, the TSP-11-compliant target shape is roughly:
```python
# app.py — TSP-11-compliant target (~10-200 LOC, pseudocode-style)
from PySide6.QtWidgets import QApplication
from _qt.main_window import MainWindow   # MainWindow + AI-9 _computing guard live here

def main() -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
```
Everything else — `MainWindow` class, panel construction, computation orchestration, AI-9 re-entrancy guard, formula evaluation, signal/slot wiring — lives in subpackages.

**TSP-7. Future-proofing: every script must justify NOT decomposing — and retentions are TIME-BOUNDED.**  When the PLAN evaluates a root script or a >500-LOC module, the default is decompose.  The burden of proof is on KEEPING it monolithic, not on splitting it.  PLAN.md section "Tree-structure compliance" must list every root-level `.py` file AND every module >500 LOC with one of two annotations:

- (a) "decomposed in batch N — see symbol-map.json", OR
- (b) "retained AS-IS FOR THIS RESTRUCTURE — justification: <one paragraph explaining why decomposing it within THIS restructure's scope is unsafe>; decomposition target: <`restructure-<scope>-<YYYYqN>-r<N>` of the follow-up that WILL address it> (or 'next restructure cycle' if this is itself a stepping-stone)".

**Retention is always temporary.**  A retention without a named follow-up restructure-id is NOT a valid TSP-7 annotation — it's the chronic-deferral anti-pattern (R20) in disguise.  The design-adversary REJECTS open-ended retentions.

**AVC-specific application:** `app.py` has been deferred across r1, r2, and r3.  That deferral has expired — chronic deferral across cycles is not principled retention.  Any future PLAN.md that retains `app.py` AS-IS must (a) name the specific follow-up restructure-id that will decompose it AND (b) justify why this restructure's scope can't absorb at least one decomposition batch (e.g. "extract MainWindow into `_qt/main_window.py` as the first batch").  The CLAUDE.md §2 note ("God Object, do not Extract Class here") is HISTORICAL and out of date with this TSP framework; the next `app.py` restructure must propose an anchor-updater edit to that note.  AI-9 is a constraint on WHERE the `_computing` guard lives (it moves WITH `MainWindow`), not a retention reason.

**TSP-8. The current call-stack IS the future tree.**  Every "function A calls function B" relationship in the current monolith points to a "module X imports module Y" relationship in the future tree.  The Phase 1 auditor MUST MAP THE CALL STACK as a directed graph (`call-graph.json` artifact, produced via Python's `ast` module — see phase-1-audit.md); the Phase 2 designer MUST align the proposed tree's import graph with that call graph (one direction only — calls flow up; imports flow up).  Misaligned decompositions (e.g. splitting along arbitrary section comments rather than call-cluster boundaries) FAIL this principle and are caught by the design-adversary's TSP axis.

**TSP-9. Tests mirror the tree — adapted for AVC's flat-tests convention.**  The general principle is: `tests/test_<module>.py` for each `<package>/<module>.py`, with test moves batched WITH the corresponding source move (no test-relocation follow-ups).  **AVC-specific carve-out:** AVC keeps `tests/` flat (504 Qt-free tests) per AI-2 — flat layout makes the "is this Qt-free?" check obvious at a glance and avoids `tests/_qt/...` confusion.  The carve-out applies to LAYOUT only: a new module added in a restructure batch MUST gain its corresponding `tests/test_<module>.py` IN THE SAME BATCH (the file lives in flat `tests/`, but it must exist).  Any moved test (e.g. when a module is renamed) moves WITH its source.  Cross-suite seam tests for new module boundaries are SUGGESTED by Phase 5 test-suggester and written in a follow-up milestone (per scout-C §10.1).

**TSP-10. The restructure is NEVER about LOC alone.**  Splitting a 1900-LOC file into three 600-LOC siblings is yak-shaving if the result isn't a TREE.  A successful restructure is judged on tree shape — `tree -L 3` output, import-DAG depth, fan-out per node, sibling-import count, responsibility-name conformance — not on file size.  LOC is a signal for which modules to LOOK AT; tree shape is the success metric.

**TSP-11. Entry-point scripts read as pseudocode.**  A root-level entry point (`app.py`, `cli.py`, `main.py`, anything declared as a `pyproject.toml` console-script entry) is the OUTERMOST orchestration layer of the application.  Its body MUST be composed primarily of calls to high-level factory functions, orchestrators, and dispatch helpers that live in the subpackage tree.  A reader walking the entry point top-to-bottom should be able to understand the application's high-level flow without descending into implementation details — the script reads as pseudocode.

Concrete tests (mechanical, run by the auditor and execution-critic):

- (a) **Function-call density** ≥70%.  Of all non-blank, non-comment, non-import statements in the entry point, at least 70% must be call expressions (or one-liners that delegate to a call — e.g. `result = factory(...)` counts).  Loops, conditionals, and assignments are permitted only when they orchestrate calls — not when they implement business logic.
- (b) **No business logic at root.**  Numeric constants beyond CLI-default sentinels, formula evaluation, data transformations, parsing, validation, file I/O, signal/slot wiring, panel/widget construction, Qt enum-handling, palette-color computation, math kernels — all of this lives in subpackages and is exposed via a factory function or method.  The entry point CALLS the factory; it does not contain the implementation.
- (c) **LOC budget (advisory).**  An entry point that grows past ~200 LOC is almost always carrying business logic; surface it for decomposition.  ~500 LOC is the alarm.  AVC's `app.py` at ~1900 LOC is a current TSP-11 FAIL and the highest-priority open restructure target (see TSP-7 for the time-bounded retention rule).
- (d) **Class-construction pattern.**  If the entry point constructs a class (e.g. a Qt main window), the class itself MUST live in a subpackage; only the construction call (and minimal pre/post wiring like `app = QApplication([]); window = MainWindow(); window.show(); sys.exit(app.exec())`) stays at root.

**Why this principle exists separately from TSP-1, TSP-4, TSP-6:** TSP-1 caps file count (one big root file still PASSES); TSP-4 flags >500-LOC files (but a 200-LOC business-logic root script slips under); TSP-6 names the decomposition TARGET shape but not the per-line constraint on the resulting root file.  TSP-11 is the load-bearing per-line content rule for entry points — without it, "thin entry point" remains vague and the pipeline produces 1900-LOC `app.py` files because every individual check passed.

Every phase of this pipeline is graded against TSP-1..TSP-11.  A restructure that closes all CRITICAL/HIGH findings but leaves the tree mis-shaped — OR leaves a root entry point carrying business logic — is a FAILURE.

---

## Step 0 — Initialize state

```bash
bash .claude/scripts/repository-architect/init-state.sh <ID> [--brief "<verbatim user brief>"] [--audit-only|--design-only] [--resume]
```

`init-state.sh` persists every flag into `state.json`:
- `--brief "..."` -> `state.restructure_brief`
- `--audit-only` -> `state.stop_after_phase = "audit"`
- `--design-only` -> `state.stop_after_phase = "design"`
- (default) -> `state.stop_after_phase = null` (run all 5 phases)

- If `state.json` already exists, `init-state.sh` is idempotent (prints `state already exists ... -- resuming`, exits 0); jump to the Resume routing table at the bottom of this file.

```bash
bash .claude/scripts/repository-architect/status.sh <ID>
```

Read `.claude/references/repository-architect/state-schema.md` only if you
need to inspect or write a field that isn't covered by the scripts.

### Step 0.5 — Precache audit snapshot (hook fires here)

Phase 1 entry triggers the precache hook (cheap, idempotent):

```bash
bash .claude/hooks/repository-architect/precache-audit-snapshot.sh <ID>
```

This populates `.claude/notes/repository-architect/<ID>/cache/` with
`tree.txt`, `loc.csv`, `imports-rough.json`, and `ai-invariants-card.md`.
The Phase 1 auditor agent reads from this cache instead of re-deriving
the data 30 times.  If the hook fails (non-zero exit), proceed without
the cache — agents will fall back to fresh derivation.

---

## Phase 1 — Audit (PARALLEL dispatch — 3 agents)

Read `.claude/references/repository-architect/phase-1-audit.md` AND `.claude/references/repository-architect/avc-tsp-status.md` at phase entry.

**Advance state BEFORE dispatch** so `status.sh` wall-clock per phase is accurate:

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> audit-running
```

### Dispatch matrix (ALL three in ONE assistant turn)

| Agent | Output path |
|---|---|
| `repository-architect-current-state-auditor` | `.claude/notes/repository-architect/<ID>/audit/current-state-brief.md` |
| `repository-architect-best-practices-scout` | `.claude/notes/repository-architect/<ID>/audit/best-practices-brief.md` |
| `repository-architect-refactor-pattern-scout` | `.claude/notes/repository-architect/<ID>/audit/refactor-pattern-brief.md` |

Each agent receives: `{ID}`, `{RESTRUCTURE_BRIEF}` verbatim from `state.restructure_brief`, output path, and `{CACHE_PATH}=.claude/notes/repository-architect/<ID>/cache/`.

**Fire all three agents in ONE assistant turn** — sequential dispatch defeats the parallelism point entirely.

Agents have `memory: project` set — do not block or override their memory writes at task completion.

**Observability:** at each dispatch, append a line to `.claude/notes/repository-architect/<ID>/dispatch.log` (format: `<iso-ts> | <agent> | <role> | dispatched|returned | [duration] | [status=...]`).  The user can `tail -f` this log to see pipeline progress.

**Transient failure handling:** if an agent returns with no output file (network blip, WebFetch timeout), re-dispatch ONCE before failing the phase.  Two consecutive empty returns is a real failure — surface gate-required to the user.

**Phase wall-clock budget:** Soft cap 30 min for the full fan-out, hard cap 60 min.  Poll `status.sh` every 5 minutes; surface gate-required if exceeded.

### After all 3 agents return

Run the mechanical evaluator checklist:

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/evaluate-checklist.py <ID>
```

Writes `.claude/notes/repository-architect/<ID>/audit/evaluator-report.md` containing scout-B's 28-item checklist run mechanically against the current tree.

Record each returned brief into state:

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --append audit_briefs='".claude/notes/repository-architect/<ID>/audit/current-state-brief.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --append audit_briefs='".claude/notes/repository-architect/<ID>/audit/best-practices-brief.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --append audit_briefs='".claude/notes/repository-architect/<ID>/audit/refactor-pattern-brief.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --set evaluator_report='".claude/notes/repository-architect/<ID>/audit/evaluator-report.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> audit-complete
bash .claude/hooks/repository-architect/summarize-phase.sh <ID> audit-complete
```

### GATE 1: surface to user

```
Audit complete for <ID>.
- Current state: <N> source files, <total-LOC> LOC, <M> monolith candidates (>500 LOC).
- Best practices: <K> patterns recommended, <J> anti-patterns detected.
- Evaluator: <pass>/28 checklist items pass.
- AI-invariant risk: <Q> constraints flagged.
Briefs: .claude/notes/repository-architect/<ID>/audit/
Continue to Design? [y/n]
```

If `state.stop_after_phase == "audit"`, stop here.  Otherwise wait for explicit `[y]` before advancing.

---

## Phase 2 — Design (synthesis + pre-execution adversary)

Read `.claude/references/repository-architect/phase-2-design.md` AND `.claude/references/repository-architect/avc-tsp-status.md` at phase entry.

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> design-running
```

### Step 1: main session synthesizes PLAN.md

Read all three audit briefs end-to-end.  Write `.claude/notes/repository-architect/<ID>/design/PLAN.md` with these mandatory sections (per `.claude/references/repository-architect/phase-2-design.md`):

1. **Restructure goal** — one paragraph, traceable to scout-B's checklist failures or scout-A's monolith candidates.
2. **Tree diff** — old tree -> new tree, line by line.
3. **Symbol map** — for each symbol moving or splitting: source `path:line` -> target `path:line`.  Persist parallel JSON to `.claude/notes/repository-architect/<ID>/design/symbol-map.json` (consumed by rewrite-imports.py in Phase 4).
4. **Delta size table** — per new/changed file: predicted LOC; per split: source LOC -> target1+target2+shim LOC.
5. **Shim plan** — per moved/renamed symbol: shim path, deprecation message, removal milestone (e.g. "shim survives until next milestone closes").
6. **AI-invariant impact** — per AI-1..AI-15: does this restructure touch it?  If yes, cite the invariant text and either (a) explain why the new layout still satisfies it or (b) flag for user lift decision.
7. **Cross-suite test gaps** — per scout-C section 8: which categories does this restructure introduce (seam tests, GUI integration, VTK pipeline, cyclic-import-under-entrypoint)?
8. **Rollback plan** — Tier 1 / Tier 2 / Tier 3 from scout-C section 11.

Record:

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --set plan_path='".claude/notes/repository-architect/<ID>/design/PLAN.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --set symbol_map_path='".claude/notes/repository-architect/<ID>/design/symbol-map.json"'
```

### Step 2: dispatch design-adversary

```
Agent: repository-architect-design-adversary
Inputs: {ID}, {PLAN_PATH}, {SYMBOL_MAP_PATH}, {ADVERSARY_PATH}=.claude/notes/repository-architect/<ID>/design/design-adversary-critique.md
```

The design-adversary critiques the PLAN.md *before* any moves.  Uses the canonical critique format (`### CRITICAL`/`### HIGH`/`### MEDIUM`/`### LOW`).  Specifically pushes back on:
- Hallucinated patterns (e.g. "let's split into MVC because that's the right pattern" — refuses if scout-B flagged layered architecture as an AI anti-pattern).
- AI-15-style honesty problems ("are we splitting because the code genuinely needs it or because the agent likes splits?").
- AI-1..AI-15 conflicts not explicitly addressed in PLAN.md section 6.
- **TSP-1..TSP-11 conformance** (axis 13 — the load-bearing tree-shape check, now including TSP-11 entry-point pseudocode; see `phase-2-design.md` for the per-principle table required in PLAN.md).
- Over-engineering relative to TSP-appropriate depth: introducing a 3-deep nest for a 200-LOC concern is yak-shaving; the goal is a tree shaped to the call-graph, not a tree shaped to look "enterprise-y".  Equally, refusing to decompose a >500-LOC monolith because "the existing flat layout is fine" violates TSP-4/TSP-7's burden of proof — every retention needs an explicit paragraph, not a default.

**Transient failure handling:** re-dispatch ONCE if no output file.  Two consecutive failures -> gate-required.

After return:

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --set design_adversary_path='".claude/notes/repository-architect/<ID>/design/design-adversary-critique.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> design-complete
bash .claude/hooks/repository-architect/summarize-phase.sh <ID> design-complete
```

### GATE 2: surface design + adversary to user

```
Design complete for <ID>.
PLAN.md: .claude/notes/repository-architect/<ID>/design/PLAN.md
Design adversary: <C> CRITICAL, <H> HIGH, <M> MEDIUM, <L> LOW findings.
  -> All CRITICAL/HIGH findings MUST be addressed in PLAN.md before advancing.
  -> MEDIUM/LOW may be deferred.

Continue to Pre-flight? [y/n]
```

If any CRITICAL/HIGH findings are unaddressed in PLAN.md, the orchestrator MUST loop back to Step 1 (revise PLAN.md) before surfacing the gate as approvable.

If `state.stop_after_phase == "design"`, stop here.

---

## Phase 3 — Pre-flight (baseline snapshot + dry-run + user gate)

Read `.claude/references/repository-architect/phase-3-preflight.md` at phase entry.

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> preflight-running
bash .claude/hooks/repository-architect/precache-baseline.sh <ID>
```

The precache hook calls `snapshot-baseline.py` UNLESS a fresh baseline already exists (<1h old).

### Step 1: baseline capture

`snapshot-baseline.py` writes:
- `.claude/notes/repository-architect/<ID>/preflight/baseline.collect.txt` — `pytest --collect-only -q` output.
- `.claude/notes/repository-architect/<ID>/preflight/baseline.coverage.xml` — coverage XML from `coverage run -m pytest`.
- `.claude/notes/repository-architect/<ID>/preflight/baseline.imports.json` — pydeps JSON dump.
- `.claude/notes/repository-architect/<ID>/preflight/baseline.symbols.json` — symbol-location index.
- `.claude/notes/repository-architect/<ID>/preflight/baseline.git_sha.txt` — `git rev-parse HEAD`.

Capture `restructure_base` (the pre-restructure HEAD) into state — Phase 4 needs it as the diff base AND Phase 5's critic needs it as the commit range start:

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --set restructure_base="\"$(git rev-parse HEAD)\""
```

If `git status` is not clean, ABORT with:
```
ERROR: working tree has uncommitted changes.
Restructure requires a clean baseline.  Commit or stash, then re-run.
```
This is the non-negotiable cleanliness gate from scout-C §1.

### Step 2: dispatch dry-run-validator

```
Agent: repository-architect-dry-run-validator
Inputs: {ID}, {PLAN_PATH}, {SYMBOL_MAP_PATH}, {BASELINE_DIR}, {DRY_RUN_PATH}=.claude/notes/repository-architect/<ID>/preflight/dry-run-validator-report.md
```

The dry-run validator uses LibCST + pydeps to predict the post-restructure import graph WITHOUT moving any files.  Reports:
- New import cycles introduced.
- Orphaned modules (in the predicted tree but no incoming imports).
- conftest.py scope drift (per scout-C §3 — moved tests may lose fixture visibility).
- Predicted `pytest --collect-only` count delta.

After return, the orchestrator writes `DRY-RUN.md` and `PREFLIGHT.md` summaries combining baseline + validator output, plus `ROLLBACK.md` (the rollback plan from PLAN.md section 8, restated as a standalone runnable artifact).

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --set dry_run_report_path='".claude/notes/repository-architect/<ID>/preflight/dry-run-validator-report.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> preflight-complete
bash .claude/hooks/repository-architect/summarize-phase.sh <ID> preflight-complete
```

### GATE 3: surface dry-run to user

```
Pre-flight complete for <ID>.
Baseline:
  - tests:  <N> collected, <N> passed (<wall-clock>)
  - coverage: <X>% lines, <Y>% branches
  - import graph: <M> modules, <K> cycles
  - git SHA: <restructure_base>
Dry-run:
  - new cycles: <delta>
  - orphans:    <delta>
  - conftest scope drift: <list-of-affected-tests>
  - predicted collection delta: <delta>
Rollback plan: ROLLBACK.md  (Tier 1 cmd: git revert --no-commit <base>..HEAD)

Continue to Execute? [y/n]
```

If any of (new cycles > 0, orphans > 0, collection-delta != 0) and user says `[y]`, log the override in dispatch.log so the post-hoc adversary has visibility.

---

## Phase 4 — Execute (PARALLEL — implementer + parity-verifier + anchor-updater)

Read `.claude/references/repository-architect/phase-4-execute.md` at phase entry.

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> execute-running
```

This phase is **batched**.  Each batch is one Fowler-catalog-operation worth of work (e.g. "extract panels subpackage" or "split surfaces.py"); the three agents run sequentially WITHIN a batch but the batches themselves are sequenced per PLAN.md.

### Per-batch loop

For each batch in PLAN.md:

#### Step 4a: implementer dispatch

```
Agent: repository-architect-implementer
Inputs: {ID}, {PLAN_PATH}, {SYMBOL_MAP_PATH}, {BATCH_NUMBER}, {BATCH_OPERATION}, {RESTRUCTURE_BASE}, {OUTPUT_PATH}=.claude/notes/repository-architect/<ID>/execute/implementer-batch-{N}-log.md
```

The implementer:
- Executes ONE Fowler-catalog operation per commit (Move Function / Move Method / Extract Class / Split Module / Move Module / Rename Module / Introduce Subpackage).
- Uses `git mv` for every file move (preserves blame).
- NEVER bundles content edits with moves (scout-C §10.5).
- Writes shims per `.claude/references/repository-architect/shim-templates.md`.
- Uses `rewrite-imports.py` (LibCST wrapper) for bulk import rewrites — NEVER `sed`.
- After every commit: `pytest -q` must pass.
- Returns when the batch is fully landed.

**This is the heavy-mover agent — DELEGATED implementation (not main session)** because the per-batch token cost is large and the main session needs to stay clean to orchestrate.  The implementer's output log captures every git command run + every file change.

#### Step 4b: parity-verifier dispatch

```
Agent: repository-architect-parity-verifier
Inputs: {ID}, {BATCH_NUMBER}, {BASELINE_DIR}, {OUTPUT_PATH}=.claude/notes/repository-architect/<ID>/execute/parity-verifier-batch-{N}-report.md
```

After each batch, the parity verifier:
- Runs `pytest --collect-only -q`; diffs against `baseline.collect.txt`.
- Runs `coverage run -m pytest && coverage xml`; diffs per-file % deltas (tolerance ±2%) and total LOC covered (tolerance ±1%).
- Runs `pydeps --show-cycles`; confirms cycle set unchanged from baseline.
- Runs `python -X importtime -c "import <root_module>"`; confirms import-time within ±20% of baseline.
- Runs `bash .claude/scripts/repository-architect/validate-shims.py` to confirm shims emit DeprecationWarning correctly.

If ANY parity check fails, the verifier emits a `gate-required` status and the orchestrator surfaces:
```
PARITY FAILURE in batch <N>:
  - <which check> failed: <details>
Roll back to before batch <N>?  [y/n]
```

#### Step 4c: anchor-updater dispatch

```
Agent: repository-architect-anchor-updater
Inputs: {ID}, {BATCH_NUMBER}, {SYMBOL_MAP_PATH}, {RESTRUCTURE_BASE}, {PLAN_PATH}, {OUTPUT_PATH}=.claude/notes/repository-architect/<ID>/execute/anchor-updater-batch-{N}-report.md
```

Failing to substitute `{OUTPUT_PATH}` results in literal `anchor-updater-batch-{N}-report.md` filenames — a clear regression signal. Failing to substitute `{PLAN_PATH}` makes the anchor-updater unable to check Section 6 of PLAN.md for CONTEXT.md / README.md edit authorization.

After each batch, the anchor-updater:
- Appends to repo-root `MOVES.md` (creates it if absent).  Format: `## YYYY-MM-DD — <batch operation>\n- old/path.py:line -> new/path.py:line (moved X LOC)`.
- Updates root `CLAUDE.md` (if exists) pointers — replaces stale `file:line` references.
- Walks `.claude/notes/**/*.md` and `.claude/agent-memory/**/lessons.md` for stale paths from this batch; greps + reports (does NOT auto-edit unless the user has approved a `--auto-update-anchors` flag in a future version).
- Updates `CONTEXT.md` section 4 (architecture conventions) ONLY if PLAN.md section 6 explicitly authorized it.
- Updates `README.md` "Extending the app" section ONLY if PLAN.md explicitly authorized it.

Verify anchors are clean:
```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/verify-anchors.py <ID>
```

### After ALL batches complete

```bash
# Persist commit range for Phase 5 critic.
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --set execute_commit_range="\"$(.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --get restructure_base)..$(git rev-parse HEAD)\""
# Append each commit sha (load-bearing for status.sh and Phase 5 critic).
for SHA in $(git log --format=%H $(.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --get restructure_base)..HEAD); do
  .venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --append execute_commits="\"$SHA\""
done

# Capture POST baseline for Phase 5 final parity report.
.venv/Scripts/python.exe .claude/scripts/repository-architect/snapshot-baseline.py <ID> --post
.venv/Scripts/python.exe .claude/scripts/repository-architect/diff-baselines.py <ID> > .claude/notes/repository-architect/<ID>/execute/parity-diff.md

.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> execute-complete
bash .claude/hooks/repository-architect/summarize-phase.sh <ID> execute-complete
```

---

## Phase 5 — Critique + Rectify (PARALLEL critics + MAIN-SESSION rectify)

Read `.claude/references/repository-architect/phase-5-rectify.md` AND `.claude/references/repository-architect/avc-tsp-status.md` at phase entry.

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> rectify-running
```

### Step 1: fan-out critics (in ONE assistant turn)

```
Agent: repository-architect-execution-critic
Inputs: {ID}, {EXECUTE_COMMIT_RANGE}, {BASELINE_DIR}, {PLAN_PATH}, {OUTPUT_PATH}=.claude/notes/repository-architect/<ID>/rectify/execution-critic-critique.md

Agent: repository-architect-test-suggester
Inputs: {ID}, {EXECUTE_COMMIT_RANGE}, {PLAN_PATH}, {OUTPUT_PATH}=.claude/notes/repository-architect/<ID>/rectify/test-suggester-suggestions.md
```

The execution critic walks scout-C's 20-item rubric mechanically against the diff range + parity-diff.md.  Emits CRITICAL/HIGH/MEDIUM/LOW findings.

The test-suggester proposes new cross-suite tests per scout-C section 8 (seam tests, GUI integration, VTK pipeline, cyclic-import smoke).  Emits SUGGESTIONS only — does NOT write tests (writing them in the same restructure violates scout-C §10.1).

### Step 2: rectification (MAIN SESSION — not delegated)

The rectifier is the main session.  Do NOT delegate Phase 5 step 2 to a sub-agent.  Re-verification (read each cited `file:line` ±30 surrounding lines), fix CRITICAL/HIGH findings, defer MEDIUM/LOW with explicit severity-ids.

Single rectification commit, NOT amended onto Phase 4:
```
rect-restructure({ID}): close C1, H1, H2; defer M1, L1
```

Body lists fixed / deferred / invalidated severity-ids.

If invalidation rate exceeds 40%, surface gate-required: the critic prompt is likely broken or was fed a stale diff.

### Step 3: final summary

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> --set rectification_commit="\"$(git rev-parse HEAD)\""
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py <ID> complete
bash .claude/hooks/repository-architect/summarize-phase.sh <ID> complete
```

Print a 9-line final summary:
```
Restructure: <ID>
Batches:     <N> executed
Commits:     <N> (range <base>..<HEAD>)
Findings:    C<critical> H<high> M<medium> L<low> (total <N>)
Resolved:    fixed=<n> deferred=<n> invalidated=<n>
Parity:      collection delta=<n>, coverage delta=<%>, cycles delta=<n>
MOVES.md:    updated with <N> entries
TSP shape:   depth=<N>-><M>, root-py=<P>-><Q>, root-entry-LOC=<L1>-><L2>, cycles=<R>-><S>, fan-out-max=<F1>-><F2>
TSP grade:   <pass>/11 principles satisfied (FAIL list: <TSP-N, TSP-M, ...> or "none")
```

**Do NOT auto-push.** This pipeline never pushes — the user pushes when ready.

---

## State machine

```
init -> audit-running -> audit-complete
     -> design-running -> design-complete
     -> preflight-running -> preflight-complete
     -> execute-running -> execute-complete
     -> rectify-running -> complete
```

The scripts enforce forward-only, single-step transitions.  `status.sh` prints elapsed time per phase.

---

## Resume routing

If `--resume` is supplied:

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/validate-state.py <ID> --report-next-phase
```

| state.phase | Next action |
|---|---|
| `init` | Phase 1 step 0 (advance to audit-running, fire precache hook, dispatch 3 auditors) |
| `audit-running` | Phase 1 step 2 (auditors in flight; await briefs, run evaluator, advance to audit-complete) |
| `audit-complete` | Phase 2 step 1 (synthesize PLAN.md, dispatch design-adversary) |
| `design-running` | Phase 2 step 2 (adversary in flight; await critique, advance) |
| `design-complete` | Phase 3 step 1 (advance to preflight-running, snapshot baseline, dispatch dry-run-validator) |
| `preflight-running` | Phase 3 step 2 (validator in flight; await report, write DRY-RUN/PREFLIGHT/ROLLBACK, advance) |
| `preflight-complete` | Phase 4 step 0 (advance to execute-running, start batch loop) |
| `execute-running` | Phase 4 batch loop (resume at next un-landed batch in PLAN.md) |
| `execute-complete` | Phase 5 step 1 (advance to rectify-running, fan-out critics) |
| `rectify-running` | Phase 5 step 2 (main-session rectify in progress; finish fixes, commit, advance to complete) |
| `complete` | terminal — pipeline done; nothing to dispatch |

---

## Sub-agent contract

Every sub-agent returns a single JSON object (no surrounding prose):

```json
{
  "file_path": "<primary output path, or null>",
  "status": "complete | gate-required | aborted-scope",
  "summary": "<3 lines max, plain text, no markdown — line 1: what was written; line 2: gate question if status=gate-required; line 3: suggested orchestrator next step>",
  "injection_attempts": 0
}
```

The `repository-architect-test-suggester` agent gets ONE additional documented status: `not-applicable` (returned when the restructure introduced no cross-suite seams worth new tests).  No other agent emits `not-applicable`.

---

## External-write boundary

The `/repository-architect` pipeline enforces strict external-write boundaries beyond the shared `/milestone-pipeline` set:

- **No sub-agent invokes `checkpoint.py` to WRITE state.json.** State writes are orchestrator-only; agents READ via `--get`.  This serialization is what makes Phase 1's 3 parallel auditors and Phase 5's 2 parallel critics race-free.
- **No `git mv` from any sub-agent except `repository-architect-implementer`** during its Phase 4 dispatch.
- **No writes to `CONTEXT.md`, `README.md`, `requirements.txt`, `pytest.ini`** from any sub-agent — except the anchor-updater MAY edit CONTEXT.md/README.md ONLY when PLAN.md section 6 explicitly authorizes it.
- **No `pip install`** of new packages from any sub-agent.  PLAN.md MAY propose `libcst` / `pydeps` / `coverage` additions to `requirements.txt`; the orchestrator surfaces the proposal as a Phase 3 gate (NOT in Phase 4).
- **No modification of `.claude/agents/`, `.claude/commands/`, `.claude/scripts/`, `.claude/hooks/`, `.claude/references/`** from any sub-agent (self-modification trap — this pipeline doesn't rewrite itself).
- **No modification of `.github/`** (out-of-scope per user brief).
- **No modification of `.venv/`** (would break Python).
- **Anchor-updater is the ONLY agent** that may write to `.claude/notes/**` outside its own assigned output directory (it walks all notes to fix stale paths).  The anchor-updater MAY write to `.claude/agent-memory/<other-agent-name>/lessons.md` to update stale path references.
- **No `git push`** from any phase.  Manual user step.
- **No `gh issue create` / `gh pr create`** from sub-agents.  Phase 5 may surface a "should we open follow-ups for deferred findings?" gate; the orchestrator runs `gh` after explicit `[y]`.

---

## User gates (mandatory)

This is a FIVE-gate pipeline by design.  Restructures are not auto-executable.

| Gate | After | Surface |
|---|---|---|
| 1 | Phase 1 complete | "Continue to Design? [y/n]" + audit summary |
| 2 | Phase 2 design-adversary returns | "Continue to Pre-flight? [y/n]" + adversary findings, blocking on unaddressed CRITICAL/HIGH |
| 3 | Phase 3 dry-run validator returns | "Continue to Execute? [y/n]" + baseline/dry-run/rollback summary |
| 4 | (Per batch) batch parity FAILS | "Roll back batch <N>? [y/n]" + failure details |
| 5 | Phase 5 critique returns | "Rectify? [y/n]" + finding counts |

Skipping any of gates 1-3-5 violates the pipeline contract.  Gate 2 and Gate 4 are conditional (Gate 2 only blocks on CRITICAL/HIGH; Gate 4 only fires on parity failure).

---

## Common rationalizations (anti-pattern guard)

Inline summary below; full table (R1-R23) lives in `.claude/references/repository-architect/anti-patterns.md` and is read by the design-adversary, execution-critic, and implementer at dispatch time.

| Tempting belief | Reality |
|---|---|
| "We can refactor and add features in the same PR." | Defeats `git bisect`, breaks rollback. Land restructure; merge; land features in follow-up. |
| "Sed will be fine for these import rewrites." | Regex cannot distinguish `from foo import bar` from `"from foo import bar"`. LibCST only (`rewrite-imports.py`). |
| "Skipping the design-adversary saves time." | Pre-execution adversary is the cheapest safety gate; post-execution rollback is far more expensive. |
| "Splitting surfaces.py into 4 smaller files at root is good enough." | Splitting WITHOUT a subpackage multiplies TSP-1 violations and skips TSP-5. Split INTO a subpackage (TSP-6, anti-pattern R16). |
| "Sibling cross-imports are fine if they're rare." | Forbidden by TSP-2 and enforced mechanically by import-linter. Even one erodes the tree (R18). |
| "We can defer `app.py` decomposition one more cycle — TSP-7 allows retention." | TSP-7 retentions are TIME-BOUNDED and require a named follow-up restructure-id. `app.py` deferral across r1/r2/r3 is expired (R20). |
| "The root script can keep its helper functions at the bottom of the file." | TSP-11: helpers belong in subpackages; the entry point's body is call expressions. "Helpers at the bottom" is how 1900-LOC root scripts accrete (R22). |
| "AI-9's `_computing` guard means `app.py` can't be decomposed." | AI-9 constrains WHERE the guard lives (with `MainWindow`), not the file path. Move `MainWindow` → `_qt/main_window.py`; guard moves with it (R23). |

---

## Don'ts

- **Don't run Phase 5 step 2 as a sub-agent** — needs full repo access, user review, commit auth.  Sub-agents return one bundle and can't pause for user input.
- **Don't let the implementer write the critique** — critic and implementer are deliberately different agents.
- **Don't bypass `init-state.sh`** — state directory naming is load-bearing for status and checkpoint.
- **Don't auto-dispatch a follow-up restructure** — at `complete`, surface the summary and stop.

---

## Sub-agent memory

All `repository-architect-*` agents have `memory: project` in their frontmatter.  Their memory accumulates under `.claude/agent-memory/<agent-name>/` across runs.  Do NOT clear or overwrite these directories — they carry institutional memory from prior restructure runs.

Each agent appends to `lessons.md` per the protocol documented in `.claude/references/repository-architect/memory-update-protocol.md`.

The auditor and the implementer benefit most from memory accumulation:
- Auditor learns AVC-specific monolith hotspots over time.
- Implementer learns AVC-specific shim quirks (e.g. circular-import gotchas with VTK).

---

## References

Phase references (`phase-1-audit.md`, `phase-2-design.md`, `phase-3-preflight.md`, `phase-4-execute.md`, `phase-5-rectify.md`) are surfaced INLINE at their phase entries above.  Cross-cutting references:

- `.claude/references/repository-architect/state-schema.md` — `state.json` field reference
- `.claude/references/repository-architect/anti-patterns.md` — full R1-R23 anti-pattern table (R16-R23 are the TSP-specific rows; R20/R22/R23 are the user-locked carve-outs)
- `.claude/references/repository-architect/evaluator-checklist.md` — scout-B's 28-item checklist (with TSP-N mapping column)
- `.claude/references/repository-architect/verification-rubric.md` — 26-item post-execution rubric (items 1-20 process discipline + 21-26 TSP-shape)
- `.claude/references/repository-architect/shim-templates.md` — canonical `__getattr__` shim patterns
- `.claude/references/repository-architect/agent-prompts.md` — pre-substituted agent dispatch templates
- `.claude/references/repository-architect/agent-boilerplate.md` — shared memory-bootstrap / scope-bounds / output-JSON / memory-append for all `repository-architect-*` agents
- `.claude/references/repository-architect/avc-tsp-status.md` — AVC-specific TSP application (CLAUDE.md §2 override, AI-9 migration shape, r1-r3 deferral chronology, AI-2 flat-tests carve-out)
- `.claude/references/repository-architect/tsp-11-computation.md` — AST methodology for the TSP-11 pseudocode grade; consumed identically by auditor + execution-critic
- `.claude/references/repository-architect/memory-update-protocol.md` — sub-agent memory append protocol
- `.claude/references/critique-format.md` — canonical severity language (shared)
- `.claude/references/app-invariants.md` — AI-1..AI-15 architectural locks
- `CONTEXT.md` — root doc
- `.claude/notes/repository-architect-design/` — design briefs and synthesis from the design phase that produced this pipeline

Files written under `.claude/notes/repository-architect/<ID>/`: `state.json`, `dispatch.log`, `cache/`, plus one subdir per phase (`audit/`, `design/`, `preflight/`, `execute/`, `rectify/`).

Agent memory: `.claude/agent-memory/repository-architect-*/lessons.md` (one dir per agent; names match the dispatch matrices above).

Repo root: `MOVES.md` (cross-restructure rosetta stone).
