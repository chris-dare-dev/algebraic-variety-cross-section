# Agent dispatch prompt templates

Pre-substituted dispatch templates for each `repository-architect-*` agent. The orchestrator copies these and substitutes `{ID}`, `{PLAN_PATH}`, etc.

The agent BODY (`.claude/agents/<name>.md`) is its own prompt — these templates show what INPUTS the orchestrator passes via the Task tool.

## Phase 1 dispatch (all 3 in ONE assistant turn)

### current-state-auditor

```
Inputs:
  {ID}                = <restructure-id>
  {RESTRUCTURE_BRIEF} = <verbatim from state.restructure_brief>
  {BRIEF_PATH}        = .claude/notes/repository-architect/<ID>/audit/current-state-brief.md
  {CACHE_PATH}        = .claude/notes/repository-architect/<ID>/cache/
```

### best-practices-scout

```
Inputs:
  {ID}                = <restructure-id>
  {RESTRUCTURE_BRIEF} = <verbatim>
  {BRIEF_PATH}        = .claude/notes/repository-architect/<ID>/audit/best-practices-brief.md
  {CACHE_PATH}        = .claude/notes/repository-architect/<ID>/cache/
```

### refactor-pattern-scout

```
Inputs:
  {ID}                = <restructure-id>
  {RESTRUCTURE_BRIEF} = <verbatim>
  {BRIEF_PATH}        = .claude/notes/repository-architect/<ID>/audit/refactor-pattern-brief.md
  {CACHE_PATH}        = .claude/notes/repository-architect/<ID>/cache/
```

## Phase 2 dispatch

### design-adversary

```
Inputs:
  {ID}                = <restructure-id>
  {PLAN_PATH}         = <from state.plan_path>
  {SYMBOL_MAP_PATH}   = <from state.symbol_map_path>
  {ADVERSARY_PATH}    = .claude/notes/repository-architect/<ID>/design/design-adversary-critique.md
```

## Phase 3 dispatch

### dry-run-validator

```
Inputs:
  {ID}                = <restructure-id>
  {PLAN_PATH}         = <from state.plan_path>
  {SYMBOL_MAP_PATH}   = <from state.symbol_map_path>
  {BASELINE_DIR}      = .claude/notes/repository-architect/<ID>/preflight/
  {DRY_RUN_PATH}      = .claude/notes/repository-architect/<ID>/preflight/dry-run-validator-report.md
```

## Phase 4 dispatch (per batch — 3 sequential agents per batch)

### implementer

```
Inputs:
  {ID}                = <restructure-id>
  {PLAN_PATH}         = <from state.plan_path>
  {SYMBOL_MAP_PATH}   = <from state.symbol_map_path>
  {BATCH_NUMBER}      = <integer, 1..N>
  {BATCH_OPERATION}   = <label from PLAN.md section X.batch.{N}.operation>
  {RESTRUCTURE_BASE}  = <from state.restructure_base>
  {OUTPUT_PATH}       = .claude/notes/repository-architect/<ID>/execute/implementer-batch-<N>-log.md
```

### parity-verifier

```
Inputs:
  {ID}                = <restructure-id>
  {BATCH_NUMBER}      = <integer>
  {BASELINE_DIR}      = .claude/notes/repository-architect/<ID>/preflight/
  {OUTPUT_PATH}       = .claude/notes/repository-architect/<ID>/execute/parity-verifier-batch-<N>-report.md
```

### anchor-updater

```
Inputs:
  {ID}                = <restructure-id>
  {BATCH_NUMBER}      = <integer>
  {SYMBOL_MAP_PATH}   = <from state.symbol_map_path>
  {RESTRUCTURE_BASE}  = <from state.restructure_base>
  {OUTPUT_PATH}       = .claude/notes/repository-architect/<ID>/execute/anchor-updater-batch-<N>-report.md
```

## Phase 5 dispatch (both critics in ONE assistant turn)

### execution-critic

```
Inputs:
  {ID}                   = <restructure-id>
  {EXECUTE_COMMIT_RANGE} = <from state.execute_commit_range>
  {BASELINE_DIR}         = .claude/notes/repository-architect/<ID>/preflight/
  {PLAN_PATH}            = <from state.plan_path>
  {PARITY_DIFF_PATH}     = .claude/notes/repository-architect/<ID>/execute/parity-diff.md
  {OUTPUT_PATH}          = .claude/notes/repository-architect/<ID>/rectify/execution-critic-critique.md
```

### test-suggester

```
Inputs:
  {ID}                   = <restructure-id>
  {EXECUTE_COMMIT_RANGE} = <from state.execute_commit_range>
  {PLAN_PATH}            = <from state.plan_path>
  {OUTPUT_PATH}          = .claude/notes/repository-architect/<ID>/rectify/test-suggester-suggestions.md
```

## Dispatch.log lines

Per dispatch + return:

```
2026-05-23T15:00:00Z | repository-architect-current-state-auditor | current-state | dispatched
2026-05-23T15:18:32Z | repository-architect-current-state-auditor | current-state | returned | 18m32s | status=complete
```

Format: `<iso-ts> | <agent-name> | <role-label> | <event> | [duration] | [status=...]`

The role-label is short — used for grep filtering. Examples: `current-state`, `best-practices`, `refactor-pattern`, `design-adversary`, `dry-run`, `implementer-{N}`, `parity-{N}`, `anchor-{N}`, `execution-critic`, `test-suggester`.

## Common substitution errors

- Failing to substitute `{ID}` -> agents try to write to `repository-architect/{ID}/...` literally; the path won't exist.
- Failing to substitute `{BATCH_NUMBER}` -> output filenames become `implementer-batch-{N}-log.md` literally (a clear regression signal).
- Failing to substitute `{RESTRUCTURE_BASE}` -> implementer can't compute the diff range from the right SHA.

All three render as obvious garbage when not substituted — the operator catches them fast.
