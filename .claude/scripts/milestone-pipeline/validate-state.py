#!/usr/bin/env python3
"""Validate a milestone state.json and report the next-phase entrypoint.

Usage:
  validate-state.py <ID>                        # print state summary + exit 0
  validate-state.py <ID> --report-next-phase    # print canonical Phase-N-step-Y entrypoint
  validate-state.py <ID> --check                # exit 0 if valid, non-zero if corrupted

This is the milestone-pipeline analogue of
`.claude/scripts/roadmap/validate-roadmap.py --report-first-unpopulated`.
It is used by the orchestrator when `/milestone-pipeline <id> --resume` is
invoked to determine which phase / step to re-enter.

Exit codes:
  0  state is valid; output printed
  1  state.json missing / unreadable
  2  schema corruption (unknown phase, missing required field, etc.)

Repo root: parents[3] from this file (.claude/scripts/milestone-pipeline/validate-state.py).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Force UTF-8 stdout/stderr so non-ASCII brief content never crashes on
# Windows's default cp1252 codepage.  Script output itself is ASCII-only.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# Mirror PHASE_ORDER from checkpoint.py.  Single source of truth would be
# nicer; this is small enough that drift risk is low and importing across
# script dirs adds packaging complexity.
PHASE_ORDER = [
    "init",
    "research-running",
    "research-complete",
    "implement-running",
    "implement-complete",
    "critique-running",
    "critique-complete",
    "rectify-running",
    "complete",
]

# Phase -> canonical Phase-N-step-Y entrypoint string the orchestrator
# should jump to.  Mirrors the "Resume routing table" in
# .claude/commands/milestone-pipeline.md.
NEXT_PHASE_ENTRYPOINT = {
    "init":               "Phase 1 step 0 (run-from-start: advance to research-running then dispatch researchers)",
    "research-running":   "Phase 1 step 2 (researchers in flight; await brief files, then advance to research-complete)",
    "research-complete":  "Phase 2 step 0 (capture implementation_base, advance to implement-running, then implement)",
    "implement-running":  "Phase 2 step 4 (implementation in flight; await commits, then advance to implement-complete)",
    "implement-complete": "Phase 3 step 0 (advance to critique-running, detect Qt panels, dispatch critics)",
    "critique-running":   "Phase 3 step 3 (critics in flight; await critique files, then dedupe and advance to critique-complete)",
    "critique-complete":  "Phase 4 step 0 (advance to rectify-running, then run re-verification)",
    "rectify-running":    "Phase 4 step 5 (rectification in progress; finish fixes, commit, advance to complete)",
    "complete":           "(terminal -- pipeline already complete; nothing to dispatch)",
}

REQUIRED_FIELDS = {
    "id", "created_at", "updated_at", "phase", "phase_history",
    "milestone_brief", "research_mode", "oss_scout_requested",
    "research_briefs", "research_synthesis", "implementation_path",
    "implementation_plan", "implementation_base",
    "implementation_commit_range", "implementation_commits",
    "implementation_branch", "critique_path", "critics_run",
    "critique_finding_counts", "rectification_commit", "fixed_findings",
    "deferred_findings", "invalidated_findings", "regression_tests_added",
}


def _state_path(mid: str) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / ".claude" / "notes" / "milestones" / mid / "state.json"


def _load(state_path: Path) -> dict:
    if not state_path.exists():
        print(f"state.json not found at {state_path} -- run init-state.sh first", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"state.json at {state_path} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)


def _validate_schema(state: dict) -> list[str]:
    """Return list of schema problems (empty list = ok)."""
    problems: list[str] = []
    missing = REQUIRED_FIELDS - set(state.keys())
    if missing:
        problems.append(f"missing fields: {sorted(missing)}")
    phase = state.get("phase")
    if phase not in PHASE_ORDER:
        problems.append(f"unknown phase {phase!r}; must be one of {PHASE_ORDER}")
    hist = state.get("phase_history")
    if not isinstance(hist, list) or not hist:
        problems.append("phase_history must be a non-empty list")
    return problems


def _summary(state: dict) -> str:
    lines = [
        f"id:    {state['id']}",
        f"phase: {state['phase']}",
        f"hist:  {len(state.get('phase_history', []))} entries",
    ]
    counts = state.get("critique_finding_counts") or {}
    if any(counts.values()):
        parts = " ".join(f"{k[0].upper()}{counts.get(k, 0)}" for k in ("critical", "high", "medium", "low"))
        lines.append(f"finds: {parts}")
    if state.get("rectification_commit"):
        lines.append(f"rect:  {state['rectification_commit']}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    mid = argv[1]
    flag = argv[2] if len(argv) > 2 else None

    state = _load(_state_path(mid))
    problems = _validate_schema(state)
    if problems:
        for p in problems:
            print(f"schema problem: {p}", file=sys.stderr)
        return 2

    if flag == "--report-next-phase":
        phase = state["phase"]
        entry = NEXT_PHASE_ENTRYPOINT.get(phase, "(unknown phase -- cannot route)")
        print(entry)
        return 0
    if flag == "--check":
        # Schema validated; print compact ok-line and exit.
        print(f"{mid}: ok (phase={state['phase']})")
        return 0
    # Default: print summary.
    print(_summary(state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
