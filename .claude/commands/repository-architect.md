---
description: Run the 5-phase repository-restructure pipeline (Audit -> Design -> Pre-flight -> Execute -> Critique+Rectify) on the AVC repo. Use when the user invokes /repository-architect, says "restructure the repo", "audit and propose a new layout", "reorganize for AI-agent navigability", or asks to safely move/split/rename source files. This is the HIGHLY DISRUPTIVE pipeline — runs rarely (quarter-cadence at most), demands five user gates, and never auto-executes moves. Skip for single-file moves (just `git mv`) or for non-source-tree changes (use other pipelines).
argument-hint: "<id> [--brief \"...\"] [--audit-only] [--design-only] [--resume]"
---

# /repository-architect — 5-phase safe-restructure pipeline

Run the canonical 5-phase AVC repository-restructure pipeline:
**Audit -> Design -> Pre-flight -> Execute -> Critique+Rectify**

This pipeline is the formalization of the safe-large-refactor playbook
documented in `.claude/notes/repository-architect-design/scout-c-safe-refactor.md`
combined with the orchestration patterns from `/milestone-pipeline`.  It
extends the 4-phase milestone shape with an explicit **Pre-flight** gate
(Phase 3) because the blast radius of an unverified restructure is much
higher than the blast radius of an unverified milestone fix.

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

**Do NOT invoke when:**
- **Single-file move or rename** — just `git mv` it.  The 5-phase overhead is not worth it for a one-file change.
- **Adding a new variety or feature** — use `/milestone-pipeline` (the repository structure is fine; you're adding content).
- **Touching only `.claude/` or `.github/`** — these are OUT OF SCOPE per the user's restructure brief.  Edit them directly.
- **Pure documentation reorganization** (CONTEXT.md sections, README.md headings) — write directly, no pipeline.
- **Touching the test suite Qt-policy (AI-2)** — that's a separate decision that needs its own roadmap milestone.
- **A previous `/repository-architect` run is `execute-running` or `rectify-running`** — finish it first, do not start a parallel restructure.

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

- If `state.json` already exists, the script prints `state already exists at <path> (phase=X) -- resuming` and exits 0.
- If resuming: jump to the routing table at the bottom of this file ("Resume routing").

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

Read `.claude/references/repository-architect/phase-1-audit.md` at phase entry.

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

Read `.claude/references/repository-architect/phase-2-design.md` at phase entry.

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
- Over-engineering relative to repo size (scout-D notes the flat layout is appropriate for 7849 LOC; pushing src/ on a 7-file project is yak-shaving).

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

Read `.claude/references/repository-architect/phase-5-rectify.md` at phase entry.

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

Print a 7-line final summary:
```
Restructure: <ID>
Batches:     <N> executed
Commits:     <N> (range <base>..<HEAD>)
Findings:    C<critical> H<high> M<medium> L<low> (total <N>)
Resolved:    fixed=<n> deferred=<n> invalidated=<n>
Parity:      collection delta=<n>, coverage delta=<%>, cycles delta=<n>
MOVES.md:    updated with <N> entries
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

`init-state.sh` is idempotent — it prints `state already exists at <path> (phase=X) -- resuming` and exits 0 when state already exists.

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

The `/repository-architect` pipeline enforces strict external-write boundaries.  In addition to the shared boundaries from `/milestone-pipeline`:

- **No sub-agent may invoke `checkpoint.py` to write state.json.** State writes are orchestrator-only. Sub-agents READ state via `checkpoint.py --get` when needed but never WRITE. This is the load-bearing rule that makes Phase 1 (3 parallel auditors) and Phase 5 (2 parallel critics) race-free; the orchestrator serializes appends in its own turn after agents return.


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

See `.claude/references/repository-architect/anti-patterns.md` for the full table (scout-C §10).  The restructure-specific rows worth keeping inline:

| Tempting belief | Reality |
|---|---|
| "We can refactor and add features in the same PR." | Defeats `git bisect`, breaks rollback.  Land restructure; merge; then land features in follow-up. |
| "The tests will catch any regression." | Green tests prove the suite still passes — not that it still exercises the same paths.  Run the Phase 4 parity check after every batch. |
| "Let's just delete the old file, no shim needed." | Breaks `.claude/notes/**` references, agent memory, in-flight feature branches.  One milestone of shim is the cost of safety. |
| "Big-bang commit so reviewers see the whole thing." | Unreviewable and unbisectable.  Reviewers see the whole thing via PLAN.md + commit-by-commit chain. |
| "Sed will be fine for these import rewrites." | Python lexical structure — regex cannot distinguish `from foo import bar` from `"from foo import bar"`.  LibCST only (`rewrite-imports.py`). |
| "Star-imports keep the shim shorter." | Defeats stacklevel-based DeprecationWarning pinpointing.  Use the `__getattr__` shim from `shim-templates.md`. |
| "We don't need a rollback plan; we have git." | Without a pre-documented and pre-tested rollback, a panicked revert can take down adjacent work.  ROLLBACK.md is mandatory in Phase 3. |
| "The CLAUDE.md / .claude/notes update can wait." | Stale path references will actively mislead the next agent session.  Phase 4 step 4c is part of every batch, not a follow-up. |
| "We're internal-only; no deprecation needed." | Internal-only != no callers.  Notebooks, scratch scripts, agent memory, in-flight branches all count.  One milestone of shim. |
| "Skipping the design-adversary saves time." | The design-adversary catches hallucinated patterns BEFORE execution; this is far cheaper than rollback after. |

---

## Don'ts

- **Don't run Phase 5 step 2 as a sub-agent** by default.  It needs full repo access, the user's review surface, and the ability to commit.  Sub-agents return one bundle and can't pause for user input.
- **Don't let the implementer write the critique.**  Critic and implementer are deliberately different agents.
- **Don't skip the design-adversary.**  Pre-execution adversary is the cheapest safety gate.
- **Don't auto-execute Phase 4** — Gate 3 is a hard user [y].
- **Don't bypass `init-state.sh`.**  State directory naming is load-bearing for status and checkpoint.
- **Don't auto-dispatch a follow-up restructure.**  At `complete`, surface the summary and stop.  The user chooses what's next.
- **Don't modify `.claude/agents/`, `.claude/commands/`, `.claude/scripts/`, `.claude/hooks/`, `.claude/references/`** during a restructure run.  The pipeline does not modify itself.

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
- `.claude/references/repository-architect/anti-patterns.md` — restructure-specific anti-pattern table (scout-C §10)
- `.claude/references/repository-architect/evaluator-checklist.md` — scout-B's 28-item checklist
- `.claude/references/repository-architect/verification-rubric.md` — scout-C's 20-item post-execution rubric
- `.claude/references/repository-architect/shim-templates.md` — canonical `__getattr__` shim patterns
- `.claude/references/repository-architect/agent-prompts.md` — pre-substituted agent dispatch templates
- `.claude/references/repository-architect/memory-update-protocol.md` — sub-agent memory append protocol
- `.claude/references/critique-format.md` — canonical severity language (shared)
- `.claude/references/app-invariants.md` — AI-1..AI-15 architectural locks
- `CONTEXT.md` — root doc
- `.claude/notes/repository-architect-design/` — design briefs and synthesis from the design phase that produced this pipeline

Files this command writes to (and the only places sub-agents may write):

```
.claude/notes/repository-architect/<ID>/
+-- state.json
+-- dispatch.log
+-- cache/                              # hook outputs
+-- audit/                              # Phase 1
+-- design/                             # Phase 2
+-- preflight/                          # Phase 3
+-- execute/                            # Phase 4
+-- rectify/                            # Phase 5

.claude/agent-memory/
+-- repository-architect-current-state-auditor/lessons.md
+-- repository-architect-best-practices-scout/lessons.md
+-- repository-architect-refactor-pattern-scout/lessons.md
+-- repository-architect-design-adversary/lessons.md
+-- repository-architect-dry-run-validator/lessons.md
+-- repository-architect-implementer/lessons.md
+-- repository-architect-parity-verifier/lessons.md
+-- repository-architect-anchor-updater/lessons.md
+-- repository-architect-execution-critic/lessons.md
+-- repository-architect-test-suggester/lessons.md

Repo root (cross-restructure rosetta stone):
+-- MOVES.md
```
