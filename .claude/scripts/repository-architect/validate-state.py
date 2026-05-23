#!/usr/bin/env python3
"""Validate restructure state.json and report the next phase entrypoint.

Usage:
  validate-state.py <ID>                     # print summary, exit 0 if valid
  validate-state.py <ID> --check             # exit 0 if valid, 2 if corrupted
  validate-state.py <ID> --report-next-phase # print canonical Phase-N-step-Y entrypoint

Repo root: parents[3] from this file (.claude/scripts/repository-architect/validate-state.py).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

PHASE_ORDER = [
    "init",
    "audit-running",
    "audit-complete",
    "design-running",
    "design-complete",
    "preflight-running",
    "preflight-complete",
    "execute-running",
    "execute-complete",
    "rectify-running",
    "complete",
]

REQUIRED_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "phase",
    "phase_history",
    "restructure_brief",
    "stop_after_phase",
    "audit_briefs",
    "evaluator_report",
    "plan_path",
    "symbol_map_path",
    "design_adversary_path",
    "design_adversary_finding_counts",
    "restructure_base",
    "baseline_dir",
    "dry_run_report_path",
    "dry_run_verdict",
    "execute_batches_planned",
    "execute_batches_landed",
    "execute_commit_range",
    "execute_commits",
    "parity_verifier_reports",
    "anchor_updater_reports",
    "execution_critic_path",
    "test_suggester_path",
    "critique_finding_counts",
    "rectification_commit",
    "fixed_findings",
    "deferred_findings",
    "invalidated_findings",
    "user_gate_history",
}

NEXT_PHASE_ENTRYPOINT = {
    "init":              "Phase 1 step 0 (advance to audit-running, fire precache hook, dispatch 3 auditors)",
    "audit-running":     "Phase 1 step 2 (auditors in flight; await briefs, run evaluator, advance to audit-complete)",
    "audit-complete":    "Phase 2 step 1 (synthesize PLAN.md, dispatch design-adversary)",
    "design-running":    "Phase 2 step 2 (adversary in flight; await critique, advance to design-complete)",
    "design-complete":   "Phase 3 step 1 (advance to preflight-running, snapshot baseline, dispatch dry-run-validator)",
    "preflight-running": "Phase 3 step 2 (validator in flight; await report, write DRY-RUN/PREFLIGHT/ROLLBACK, advance)",
    "preflight-complete":"Phase 4 step 0 (advance to execute-running, start batch loop)",
    "execute-running":   "Phase 4 batch loop (resume at next un-landed batch in PLAN.md)",
    "execute-complete":  "Phase 5 step 1 (advance to rectify-running, fan-out critics)",
    "rectify-running":   "Phase 5 step 2 (main-session rectify; finish fixes, commit, advance to complete)",
    "complete":          "(terminal -- pipeline done; nothing to dispatch)",
}


def _state_path(rid: str) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / ".claude" / "notes" / "repository-architect" / rid / "state.json"


def validate(rid: str) -> tuple[dict, list[str]]:
    sp = _state_path(rid)
    if not sp.exists():
        return {}, [f"state.json not found at {sp}"]
    try:
        state = json.loads(sp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"state.json is invalid JSON: {exc}"]
    errors = []
    missing = REQUIRED_FIELDS - set(state.keys())
    if missing:
        errors.append(f"missing required fields: {sorted(missing)}")
    if state.get("phase") not in PHASE_ORDER:
        errors.append(f"invalid phase: {state.get('phase')!r}")
    if not isinstance(state.get("phase_history"), list) or not state["phase_history"]:
        errors.append("phase_history must be a non-empty list")
    return state, errors


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    rid = argv[1]
    mode = argv[2] if len(argv) > 2 else None
    state, errors = validate(rid)
    if mode == "--check":
        if errors:
            for e in errors:
                print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)
    if mode == "--report-next-phase":
        if errors:
            for e in errors:
                print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(2)
        phase = state["phase"]
        print(NEXT_PHASE_ENTRYPOINT.get(phase, f"(no entrypoint for phase {phase!r})"))
        return
    # Default: summary
    if errors:
        print("state.json INVALID:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(2)
    print(f"state.json valid: id={state['id']}, phase={state['phase']}")
    print(f"next: {NEXT_PHASE_ENTRYPOINT.get(state['phase'])}")


if __name__ == "__main__":
    main(sys.argv)
