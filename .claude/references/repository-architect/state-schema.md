# `/repository-architect` state.json schema

`scripts/repository-architect/init-state.sh`, `checkpoint.py`, `status.sh`, and `validate-state.py` all read/write `.claude/notes/repository-architect/{ID}/state.json`. This file defines the schema.

## Path layout

```
.claude/notes/repository-architect/{ID}/
+-- state.json                          # this schema
+-- dispatch.log                        # phase + agent dispatch log
+-- cache/                              # precache-audit-snapshot.sh hook output
|   +-- tree.txt
|   +-- loc.csv
|   +-- imports-rough.json
|   +-- ai-invariants-card.md
+-- audit/                              # Phase 1
|   +-- current-state-brief.md
|   +-- best-practices-brief.md
|   +-- refactor-pattern-brief.md
|   +-- evaluator-report.md
+-- design/                             # Phase 2
|   +-- PLAN.md
|   +-- symbol-map.json
|   +-- design-adversary-critique.md
+-- preflight/                          # Phase 3
|   +-- baseline.collect.txt
|   +-- baseline.coverage.xml
|   +-- baseline.imports.json
|   +-- baseline.importtime.log
|   +-- baseline.starimports.txt
|   +-- baseline.symbols.json
|   +-- baseline.git_sha.txt
|   +-- dry-run-validator-report.md
|   +-- DRY-RUN.md
|   +-- PREFLIGHT.md
|   +-- ROLLBACK.md
+-- execute/                            # Phase 4
|   +-- implementer-batch-{N}-log.md
|   +-- parity-verifier-batch-{N}-report.md
|   +-- anchor-updater-batch-{N}-report.md
|   +-- post.collect.txt
|   +-- post.coverage.xml
|   +-- post.imports.json
|   +-- post.importtime.log
|   +-- post.starimports.txt
|   +-- post.symbols.json
|   +-- parity-diff.md
+-- rectify/                            # Phase 5
    +-- execution-critic-critique.md
    +-- test-suggester-suggestions.md
```

The repo-root `MOVES.md` is the cross-restructure rosetta stone (NOT under `.claude/`). Every `/repository-architect` run appends a section to it.

## Schema

```json
{
  "id": "restructure-panels-2026q3-r1",
  "created_at": "2026-05-23T15:00:00Z",
  "updated_at": "2026-05-23T18:00:00Z",
  "phase": "execute-complete",
  "phase_history": [
    {"phase": "init", "at": "..."},
    ...
  ],
  "restructure_brief": "Introduce panels/ subpackage for the four panel files",
  "stop_after_phase": null,

  "audit_briefs": [
    ".claude/notes/repository-architect/.../audit/current-state-brief.md",
    ...
  ],
  "evaluator_report": ".claude/notes/repository-architect/.../audit/evaluator-report.md",

  "plan_path": ".claude/notes/repository-architect/.../design/PLAN.md",
  "symbol_map_path": ".claude/notes/repository-architect/.../design/symbol-map.json",
  "design_adversary_path": ".claude/notes/repository-architect/.../design/design-adversary-critique.md",
  "design_adversary_finding_counts": {"critical": 0, "high": 1, "medium": 2, "low": 4},

  "restructure_base": "abc1234...",
  "baseline_dir": ".claude/notes/repository-architect/.../preflight/",
  "dry_run_report_path": ".claude/notes/repository-architect/.../preflight/dry-run-validator-report.md",
  "dry_run_verdict": "GREEN",

  "execute_batches_planned": 3,
  "execute_batches_landed": 3,
  "execute_commit_range": "abc1234..def5678",
  "execute_commits": ["abc1234", "...", "def5678"],
  "parity_verifier_reports": [".../parity-verifier-batch-1-report.md", ...],
  "anchor_updater_reports": [".../anchor-updater-batch-1-report.md", ...],

  "execution_critic_path": ".claude/notes/repository-architect/.../rectify/execution-critic-critique.md",
  "test_suggester_path": ".claude/notes/repository-architect/.../rectify/test-suggester-suggestions.md",
  "critique_finding_counts": {"critical": 0, "high": 2, "medium": 4, "low": 5},
  "rectification_commit": "ef901ab",
  "fixed_findings": ["H1", "H2"],
  "deferred_findings": ["M1", "M2", "L1", "L2", "L3"],
  "invalidated_findings": [],
  "user_gate_history": [
    {"gate": 1, "at": "...", "response": "y"},
    {"gate": 2, "at": "...", "response": "y"},
    {"gate": 3, "at": "...", "response": "y"},
    {"gate": 5, "at": "...", "response": "y"}
  ]
}
```

## Field reference (selected)

| Field | Type | Set by | Notes |
|---|---|---|---|
| `id` | string | init-state.sh | Restructure id. Convention: `restructure-<scope>-<YYYYqN>-r<N>`. |
| `phase` | enum | every checkpoint | One of: `init`, `audit-running`, `audit-complete`, `design-running`, `design-complete`, `preflight-running`, `preflight-complete`, `execute-running`, `execute-complete`, `rectify-running`, `complete`. |
| `restructure_brief` | string | init-state.sh (from `--brief`) | Verbatim user ask. Don't paraphrase. |
| `stop_after_phase` | null \| "audit" \| "design" | init-state.sh (from `--audit-only`/`--design-only`) | If set, the pipeline halts after the named phase. |
| `restructure_base` | sha | Phase 3 step 1 | Pre-restructure HEAD; load-bearing for Phase 4 diff range and Phase 5 critic. |
| `execute_batches_planned` | int | Phase 4 step 0 (orchestrator extracts from PLAN.md) | Used by status.sh progress line. |
| `execute_batches_landed` | int | Phase 4 per-batch | Incremented after parity-verifier returns PASS. |
| `user_gate_history` | array | Orchestrator at each gate | Append-only; records `{gate: N, at: iso, response: "y"|"n"}`. |

## State machine

```
init -> audit-running -> audit-complete
     -> design-running -> design-complete
     -> preflight-running -> preflight-complete
     -> execute-running -> execute-complete
     -> rectify-running -> complete
```

Forward-only, single-step. `checkpoint.py` refuses backward or skipped transitions.

## Reading and writing state

```bash
# Read a field:
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} --get plan_path

# Set a field (JSON-parsed; quote strings with literal "):
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} --set plan_path='".claude/notes/repository-architect/{ID}/design/PLAN.md"'

# Append to a list field:
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} --append audit_briefs='".claude/notes/repository-architect/{ID}/audit/current-state-brief.md"'

# Advance phase:
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} audit-complete
```

On POSIX, the path is `.venv/bin/python` — both forms documented in CONTEXT.md section 10.
