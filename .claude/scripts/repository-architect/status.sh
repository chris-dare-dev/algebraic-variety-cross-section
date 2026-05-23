#!/usr/bin/env bash
# Human-readable state inspection for /repository-architect.
#
# Usage: status.sh <restructure-id>
#
# ASCII-only output for Windows cp1252 compatibility.
#
# Exit codes:
#   0 success
#   1 missing state.json (run init-state.sh first)
#   2 usage error

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: status.sh <restructure-id>" >&2
  exit 2
fi

ID="$1"

if REPO_ROOT_TRY=$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null); then
  REPO_ROOT="$REPO_ROOT_TRY"
else
  d="$(cd "$(dirname "$0")" && pwd)"
  while [[ "$d" != "/" && ! -d "$d/.git" ]]; do d="$(dirname "$d")"; done
  REPO_ROOT="$d"
fi

PY="$REPO_ROOT/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then
  PY="$REPO_ROOT/.venv/bin/python"
fi
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi

STATE="$REPO_ROOT/.claude/notes/repository-architect/$ID/state.json"
if [[ ! -f "$STATE" ]]; then
  echo "no state.json for restructure '$ID' at $STATE" >&2
  echo "run: bash .claude/scripts/repository-architect/init-state.sh $ID" >&2
  exit 1
fi

"$PY" - "$STATE" "$ID" <<'PY'
import json, sys
from datetime import datetime, timezone

state_path, rid = sys.argv[1:3]
state = json.load(open(state_path, encoding="utf-8"))

def parse_iso(s):
    # Accept 'YYYY-MM-DDTHH:MM:SSZ'
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def fmt_elapsed(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds/60)}m"
    return f"{int(seconds/3600)}h{int((seconds%3600)/60)}m"

now = datetime.now(timezone.utc)
phase = state["phase"]
phase_start = parse_iso(state["phase_history"][-1]["at"])
elapsed = (now - phase_start).total_seconds()

print(f"Restructure: {rid}")
print(f"Phase:       {phase} (since {phase_start.strftime('%Y-%m-%dT%H:%M:%SZ')}, {fmt_elapsed(elapsed)} ago)")
print(f"Brief:       {state['restructure_brief'][:60]}{'...' if len(state['restructure_brief']) > 60 else ''}")
sap = state.get("stop_after_phase")
print(f"Stop after:  {sap if sap else '(none -- run all 5 phases)'}")
print()

print("Phase history:")
for i, entry in enumerate(state["phase_history"]):
    t = parse_iso(entry["at"])
    if i + 1 < len(state["phase_history"]):
        nxt = parse_iso(state["phase_history"][i+1]["at"])
        dur = fmt_elapsed((nxt - t).total_seconds())
        print(f"  {entry['phase']:<22} {entry['at']} +{dur:<6} -> {state['phase_history'][i+1]['phase']}")
    else:
        print(f"  {entry['phase']:<22} {entry['at']} (now)")
print()

# Phase 1 summary
if state.get("audit_briefs"):
    print(f"Audit briefs:    {len(state['audit_briefs'])}")
if state.get("evaluator_report"):
    print(f"Evaluator:       {state['evaluator_report']}")
# Phase 2 summary
if state.get("plan_path"):
    print(f"PLAN:            {state['plan_path']}")
if state.get("design_adversary_path"):
    fc = state.get("design_adversary_finding_counts", {})
    print(f"Design adversary: C{fc.get('critical',0)} H{fc.get('high',0)} M{fc.get('medium',0)} L{fc.get('low',0)}  ({state['design_adversary_path']})")
# Phase 3 summary
if state.get("restructure_base"):
    print(f"Restructure base: {state['restructure_base'][:12]}")
if state.get("dry_run_verdict"):
    print(f"Dry-run verdict: {state['dry_run_verdict']}")
# Phase 4 summary
if state.get("execute_batches_planned"):
    print(f"Batches:         {state.get('execute_batches_landed', 0)}/{state['execute_batches_planned']} landed")
if state.get("execute_commit_range"):
    print(f"Commit range:    {state['execute_commit_range']}")
    print(f"Commits:         {len(state.get('execute_commits', []))}")
# Phase 5 summary
if state.get("execution_critic_path"):
    fc = state.get("critique_finding_counts", {})
    print(f"Critique:        C{fc.get('critical',0)} H{fc.get('high',0)} M{fc.get('medium',0)} L{fc.get('low',0)}")
    print(f"                 ({state['execution_critic_path']})")
if state.get("rectification_commit"):
    print(f"Rect commit:     {state['rectification_commit'][:12]}")
    print(f"Resolved:        fixed={len(state.get('fixed_findings',[]))} deferred={len(state.get('deferred_findings',[]))} invalidated={len(state.get('invalidated_findings',[]))}")

# Next phase hint
NEXT_HINTS = {
    "init":              "Phase 1 step 0 (advance to audit-running, fire precache hook, dispatch 3 auditors)",
    "audit-running":     "Phase 1 step 2 (auditors in flight; await briefs, run evaluator)",
    "audit-complete":    "Phase 2 step 1 (synthesize PLAN.md, dispatch design-adversary)",
    "design-running":    "Phase 2 step 2 (adversary in flight; await critique)",
    "design-complete":   "Phase 3 step 1 (advance to preflight-running, snapshot baseline)",
    "preflight-running": "Phase 3 step 2 (validator in flight; await report)",
    "preflight-complete":"Phase 4 step 0 (advance to execute-running, start batch loop)",
    "execute-running":   "Phase 4 batch loop (resume at next un-landed batch)",
    "execute-complete":  "Phase 5 step 1 (advance to rectify-running, fan-out critics)",
    "rectify-running":   "Phase 5 step 2 (main-session rectify; finish fixes, commit)",
    "complete":          "(terminal -- pipeline done)",
}
print()
print(f"Next phase:  {NEXT_HINTS.get(phase, '(unknown phase)')}")
PY
