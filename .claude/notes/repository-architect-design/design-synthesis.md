# `/repository-architect` — Design Synthesis

**Source briefs:** scout-a-pipeline-blueprint.md (clone target), scout-b-best-practices.md (28-item checklist), scout-c-safe-refactor.md (8-phase safe-refactor playbook + 20-item rubric), scout-d-current-state.md (AVC current state, AI-1..AI-15 constraints).

**Constitutional constraint:** the user explicitly said this pipeline is highly disruptive and runs rarely. Lock in: exhaustive logging, plenty of gates, NEVER auto-pushes, NEVER auto-executes moves without explicit `[y]` from the user.

---

## Phase shape — 5 phases (vs milestone-pipeline's 4)

`/repository-architect` extends the milestone-pipeline shape with an explicit Dry-run / Pre-flight gate because the cost of an unverified restructure is much higher than the cost of an unverified milestone fix.

```
init
  ↓
audit-running    → audit-complete   [Phase 1: parallel scouts]
  ↓
design-running   → design-complete  [Phase 2: synthesize PLAN.md + adversary pre-execution review]
  ↓
preflight-running → preflight-complete [Phase 3: baseline snapshot + import-graph dry-run + user [y] gate]
  ↓
execute-running  → execute-complete  [Phase 4: parallel implementers + parity verifier + anchor updater]
  ↓
rectify-running  → complete          [Phase 5: critique fan-out + main-session rectification]
```

State machine enforced by `checkpoint.py` (forward-only, single-step, ISO 8601 UTC timestamps).

---

## Agent set — 10 agents, each with its own `.claude/agent-memory/<name>/lessons.md`

| # | Agent | Phase | Job |
|---|---|---|---|
| 1 | `repository-architect-current-state-auditor` | 1 | Map current tree, hotspots, AI-1..AI-15 constraints, README extension path. Reads `cache/audit-snapshot/` if present (hook precaches). |
| 2 | `repository-architect-best-practices-scout` | 1 | Web research 2024-2026 best practices; runs scout-B's 28-item checklist mechanically. |
| 3 | `repository-architect-refactor-pattern-scout` | 1 | Web research safe-refactor playbooks; pre-loads LibCST / pydeps / coverage tooling notes. |
| 4 | `repository-architect-design-adversary` | 2 | **Pre-execution adversary.** Critiques the proposed PLAN.md *before* any moves. Pushes back on hallucinated patterns, over-engineering, AI-1..AI-15 conflicts, AI-15 honesty problems ("are we really splitting because the code needs it or because the agent likes splits?"). |
| 5 | `repository-architect-dry-run-validator` | 3 | Computes predicted import-graph delta via LibCST without moving files. Reports cycles, orphans, conftest.py scope drift, pytest collection delta. |
| 6 | `repository-architect-implementer` | 4 | Heavy mover. Executes PLAN.md operations one-catalog-operation-per-commit. Uses `git mv`, writes shims, never bundles content edits with moves. |
| 7 | `repository-architect-parity-verifier` | 4 | After each implementer batch: re-runs `pytest --collect-only`, coverage diff, mutmut (optional), confirms shim warnings. |
| 8 | `repository-architect-anchor-updater` | 4 | Phase 8 mechanics: appends to `MOVES.md`, updates root `CLAUDE.md`/CONTEXT.md pointers, walks `.claude/notes/**` and agent-memory `lessons.md`, fixes stale paths. |
| 9 | `repository-architect-execution-critic` | 5 | Post-execution adversary. Reads the actual diff range, runs scout-C's 20-item rubric mechanically, emits CRITICAL/HIGH/MEDIUM/LOW findings. |
| 10 | `repository-architect-test-suggester` | 5 | Proposes new cross-suite tests (scout-C section 8: seam tests, GUI integration, VTK pipeline, cyclic-import-under-entrypoint smoke). Does NOT write the tests — emits suggestions for the rectifier to consider. |

**Adversary fires TWICE** — once before execution (catch bad designs) and once after (catch bad executions). This is the key delta from milestone-pipeline, where adversary only fires post-implementation.

---

## Scripts — `.claude/scripts/repository-architect/`

Modeled exactly on milestone-pipeline's scripts; the new repetitive-task savers are bold.

| Script | Purpose |
|---|---|
| `init-state.sh` | Initialize state directory + state.json (idempotent). Clone of milestone-pipeline pattern. |
| `checkpoint.py` | Forward-only phase advance; `--get`/`--set`/`--append` for fields. |
| `status.sh` | Human-readable state inspection (ASCII-only, Windows-safe). |
| `validate-state.py` | Schema validation + `--report-next-phase` resume routing. |
| **`audit-tree.py`** | Single-shot repo audit: top-level files, LOC per file, import graph dump, AI-1..AI-15 quick-card. Saves auditor agent from re-running 30 grep/wc/find calls. |
| **`snapshot-baseline.py`** | Captures pre-refactor baseline: `pytest --collect-only -q`, coverage XML, pydeps JSON, symbol-location index. Used twice (pre + post). |
| **`diff-baselines.py`** | Diffs pre/post baselines, emits parity report (collection delta, coverage delta, import-graph delta). |
| **`evaluate-checklist.py`** | Runs scout-B's 28-item evaluator checklist mechanically. Outputs `evaluator-report.md`. |
| **`rewrite-imports.py`** | Thin LibCST wrapper: takes `symbol-map.json` (old→new), rewrites imports across the tree. Phase 4 mechanical bulk operation. |
| **`validate-shims.py`** | Verifies all shims emit `DeprecationWarning` with correct stacklevel + new-path message. |
| **`verify-anchors.py`** | Greps `.claude/notes/**`, `CLAUDE.md`, `CONTEXT.md`, `README.md`, agent-memory `lessons.md` for old paths from MOVES.md. Phase 4 anchor verification. |

---

## References — `.claude/references/repository-architect/`

| File | Purpose |
|---|---|
| `state-schema.md` | state.json shape (clone milestone-pipeline pattern + restructure-specific fields). |
| `phase-1-audit.md` | Phase 1 procedures. |
| `phase-2-design.md` | Phase 2 procedures + adversary dispatch protocol. |
| `phase-3-preflight.md` | Phase 3 procedures + baseline snapshot + user-gate template. |
| `phase-4-execute.md` | Phase 4 procedures + per-commit checklist + shim verification cadence. |
| `phase-5-rectify.md` | Phase 5 procedures + critique fan-out + rectification rules (main session, never delegated). |
| `anti-patterns.md` | Restructure-specific rationalizations to refuse (scout-C section 10). |
| `evaluator-checklist.md` | Scout-B's 28-item checklist as a structured reference. |
| `verification-rubric.md` | Scout-C's 20-item post-execution rubric. |
| `shim-templates.md` | Canonical `__getattr__` shim patterns + test recipe. |
| `agent-prompts.md` | Per-agent dispatch templates with substitution variables. |
| `memory-update-protocol.md` | When/how lessons.md gets compacted. |

Shared (already exists, do NOT duplicate): `app-invariants.md`, `critique-format.md`.

---

## Hooks — `.claude/hooks/repository-architect/`

Project-local shell scripts the pipeline invokes at strategic points to **precompute cached artifacts** so agents read disk instead of recomputing.

| Hook | Trigger | Output |
|---|---|---|
| `precache-audit-snapshot.sh` | Phase 1 entry | Writes `tree.txt`, `loc.csv`, `imports-rough.json`, `ai-invariants-card.md` into `.claude/notes/repository-architect/<ID>/cache/`. Auditor agent reads cache instead of re-deriving. |
| `precache-baseline.sh` | Phase 3 entry | Wraps `snapshot-baseline.py`; if baseline already exists and is <1h old, no-op. |
| `summarize-phase.sh` | Every phase transition | Appends 5-line phase summary to `dispatch.log` for human grep-ability. |

These are NOT Claude Code hook events (no `settings.json` mutation). They are pipeline-internal scripts named "hooks" because they fire at hook-shaped events (phase boundaries).

---

## Notes / output layout — `.claude/notes/repository-architect/<ID>/`

```
.claude/notes/repository-architect/<ID>/
├── state.json
├── dispatch.log
├── cache/                              # hook outputs (precomputed, agents read from here)
│   ├── tree.txt
│   ├── loc.csv
│   ├── imports-rough.json
│   └── ai-invariants-card.md
├── audit/                              # Phase 1 outputs
│   ├── current-state-brief.md
│   ├── best-practices-brief.md
│   ├── refactor-pattern-brief.md
│   └── evaluator-report.md
├── design/                             # Phase 2 outputs
│   ├── PLAN.md
│   ├── symbol-map.json
│   └── design-adversary-critique.md
├── preflight/                          # Phase 3 outputs
│   ├── baseline.collect.txt
│   ├── baseline.coverage.xml
│   ├── baseline.imports.json
│   ├── baseline.symbols.json
│   ├── dry-run-validator-report.md
│   ├── DRY-RUN.md
│   ├── PREFLIGHT.md
│   └── ROLLBACK.md
├── execute/                            # Phase 4 outputs
│   ├── implementer-batch-{N}-log.md
│   ├── parity-verifier-batch-{N}-report.md
│   ├── anchor-updater-batch-{N}-report.md
│   ├── post.collect.txt
│   ├── post.coverage.xml
│   └── parity-diff.md
└── rectify/                            # Phase 5 outputs
    ├── execution-critic-critique.md
    ├── test-suggester-suggestions.md
    └── rectification-summary.md
```

A `MOVES.md` file at the **repo root** (not under `.claude/`) is the cross-restructure rosetta stone — every `/repository-architect` run appends to it.

---

## External-write boundary (CRITICAL — restructure-specific)

Same as milestone-pipeline plus:
- **NO `git mv` outside Phase 4** (implementer-only).
- **NO writes to `CONTEXT.md`, `README.md`, `requirements.txt`, `pytest.ini`** from any sub-agent. The anchor-updater MAY update CONTEXT.md *only* under explicit instruction in Phase 4 step 3.
- **NO `pip install`** of new packages from any sub-agent. PLAN.md MAY propose adding `libcst`/`pydeps`/`coverage` to requirements.txt; the orchestrator surfaces the proposal as a Phase 3 gate.
- **NO modification of `.claude/agents/`, `.claude/commands/`** from any sub-agent (self-modification trap).
- **NO modification of `.github/`** (out-of-scope per user brief).
- **NO modification of the `.venv/` itself** (would break Python).
- **Anchor-updater is the ONLY agent that may write to** `.claude/notes/**` outside its own output directory (it walks all notes to fix stale paths).

---

## Resume routing

Identical pattern to milestone-pipeline. `validate-state.py --report-next-phase` returns the canonical entrypoint string the orchestrator jumps to on `--resume`.

---

## User gates (mandatory)

Five gates the pipeline MUST surface to the user:

1. **After Phase 1:** "Audit complete. Findings: <N> hotspots, <M> AI-invariant constraints. Continue to Design? [y/n]"
2. **After Phase 2 design-adversary:** "Design adversary returned <N> CRITICAL, <M> HIGH findings. Continue to Pre-flight? [y/n]"
3. **After Phase 3 dry-run:** "Dry-run found: <cycles> new cycles, <orphans> orphans, <collection-delta> collection change. Continue to Execute? [y/n]"
4. **Before Phase 4 implementer dispatch:** "About to execute <N> file moves and <M> splits. ROLLBACK plan: `<cmd>`. Proceed? [y/n]"
5. **After Phase 5 critique:** "Critique returned <C/H/M/L> findings. Rectify? [y/n]"

This is a five-gate pipeline by design — restructures are not auto-executable.

---

## Don'ts (restructure-specific, beyond shared anti-patterns)

| Don't | Why |
|---|---|
| Don't bundle restructure with feature work | Defeats `git bisect`, breaks rollback. Scout-C §10.1. |
| Don't skip the design-adversary | Pre-execution adversary catches hallucinated patterns; cheaper than post-execution rollback. |
| Don't auto-run Phase 4 without user [y] | Restructures are user-authorized, not orchestrator-authorized. |
| Don't ship without a `MOVES.md` entry | Anchor-updater MUST append before Phase 4 completes. |
| Don't delete the shim in the same commit as the move | Use two-milestone deprecation cycle. |
| Don't use `sed` for import rewrites | LibCST only. Scout-C §10.6. |
| Don't run the parity verifier on a different commit range than the implementer | Phase 4 step 2 must pin `implementation_base` like milestone-pipeline does. |

---

## Memory protocol

All 10 agents have `memory: project` and `.claude/agent-memory/<name>/lessons.md`. Compaction trigger: >200 lines. Archive pattern: `lessons-{DATE}.md` under `archive/` subdirectory.

The auditor and the implementer benefit most from memory accumulation:
- Auditor learns AVC-specific monolith hotspots over time.
- Implementer learns AVC-specific shim quirks (e.g. circular-import gotchas with VTK).

---

## What this pipeline does NOT do

Per user scope:
- Does NOT touch `.claude/` or `.github/` (standard tool folders).
- Does NOT `git push` (manual user step).
- Does NOT auto-open GitHub issues for deferred findings (Phase 5 may surface a "should we open follow-ups?" gate).
- Does NOT run on a schedule — explicit user invocation only.
- Does NOT modify the test pattern (Qt-free per AI-2) — would lift AI-2, which is a separate decision.
