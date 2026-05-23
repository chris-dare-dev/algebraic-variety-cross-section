# Phase 1 — Audit

**Goal:** map the current AVC repo state, survey 2024-2026 best practices, and load the safe-refactor playbook BEFORE proposing a new layout.

## Step 0 — Precache hook fires

```bash
bash .claude/hooks/repository-architect/precache-audit-snapshot.sh {ID}
```

Populates `{ID}/cache/`. If already fresh (<1h), no-op. If fails, agents fall back to fresh derivation.

## Step 1 — Dispatch 3 auditors in ONE assistant turn

| Agent | Output |
|---|---|
| `repository-architect-current-state-auditor` | `audit/current-state-brief.md` |
| `repository-architect-best-practices-scout` | `audit/best-practices-brief.md` |
| `repository-architect-refactor-pattern-scout` | `audit/refactor-pattern-brief.md` |

Each receives `{ID}`, `{RESTRUCTURE_BRIEF}` verbatim from state, output path, `{CACHE_PATH}`.

Append dispatch.log lines on dispatch + return:
```
2026-05-23T15:00:00Z | repository-architect-current-state-auditor | current-state | dispatched
2026-05-23T15:18:32Z | repository-architect-current-state-auditor | current-state | returned | 18m32s | status=complete
```

## Step 2 — Wait for all three; run evaluator

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/evaluate-checklist.py {ID}
```

Writes `audit/evaluator-report.md`: scout-B's 28-item checklist run mechanically. Stores PASS/FAIL per item with one-line evidence.

## Step 3 — Record briefs into state

```bash
for brief in current-state-brief best-practices-brief refactor-pattern-brief; do
  .venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
      --append audit_briefs="\".claude/notes/repository-architect/{ID}/audit/$brief.md\""
done
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set evaluator_report='".claude/notes/repository-architect/{ID}/audit/evaluator-report.md"'
```

## Step 4 — Advance + summarize

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} audit-complete
bash .claude/hooks/repository-architect/summarize-phase.sh {ID} audit-complete
```

## Step 5 — GATE 1

Surface to user:
```
Audit complete for {ID}.
- Current state: <N> source files, <total-LOC> LOC, <M> monolith candidates (>500 LOC).
- Best practices: <K> patterns recommended, <J> anti-patterns detected.
- Evaluator: <pass>/28 checklist items pass.
- AI-invariant risk: <Q> constraints flagged.
Continue to Design? [y/n]
```

Record user response in `user_gate_history`. If `state.stop_after_phase == "audit"`, stop here.

## Phase wall-clock budget

Soft cap 30 min for the full 3-agent fan-out, hard cap 60 min. Poll `status.sh` every 5 min.

## Transient failure handling

If an agent returns with no output file: re-dispatch ONCE. Two consecutive failures = surface gate-required.

## Anti-patterns to refuse

- Sequential dispatch of the 3 auditors (defeats parallelism).
- Skipping the evaluator script (the auditor's narrative is no substitute for the mechanical 28-item check).
- Auto-advancing past GATE 1 without user `[y]`.
