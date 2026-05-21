#!/usr/bin/env bash
# Initialize milestone state directory and state.json for /milestone-pipeline
# on the algebraic-variety-cross-section repo.
#
# Usage: init-state.sh <milestone-id> [--brief "verbatim user brief"]
#
# Idempotent: if state.json exists, prints current phase and exits 0
# without modifying anything.  The orchestrator uses that as the resume signal.
#
# Repo root resolution: prefers git rev-parse, falls back to walking up from
# the script directory looking for .git.
#
# Python interpreter resolution: prefers .venv/Scripts/python.exe (Windows),
# then .venv/bin/python (POSIX), then bare python3.
#
# Exit codes:
#   0 success (including idempotent resume)
#   1 user-actionable failure (no repo root, etc.)
#   2 input/usage error

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: init-state.sh <milestone-id> [--brief \"...\"]" >&2
  exit 2
fi

ID="$1"
shift

BRIEF=""
RESEARCH_MODE="standard"
OSS_SCOUT_REQUESTED="false"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --brief)
      # Strip leading/trailing whitespace so --brief "   " is treated as empty.
      BRIEF="$(echo "${2:-}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
      shift 2
      ;;
    --single)
      RESEARCH_MODE="single"
      shift
      ;;
    --deep)
      RESEARCH_MODE="deep"
      shift
      ;;
    --oss-scout)
      OSS_SCOUT_REQUESTED="true"
      shift
      ;;
    --resume)
      # --resume is a no-op at init time; the orchestrator handles resume
      # routing by reading state.phase via validate-state.py.  Accepted here
      # so init-state.sh can be called with the full argv from the slash
      # command without dropping flags.
      shift
      ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

# Milestone id shape: starts with a letter, allows alphanumeric segments
# separated by SINGLE dashes (no double-dashes, no trailing dash), <=60 chars.
# Tighter than the previous ^[a-zA-Z][a-zA-Z0-9-]{0,59}$ to reject obviously
# bad shapes like 'a--b' or 'e--1' while still accepting valid epic-shaped ids
# from /roadmap (`<slug>-eN[a-z]?`).
if ! [[ "$ID" =~ ^[a-zA-Z][a-zA-Z0-9]*(-[a-zA-Z0-9]+)*$ ]] || (( ${#ID} > 60 )); then
  echo "error: invalid milestone id '$ID' -- must be 1-60 chars, alphanumeric segments separated by single dashes, starting with a letter" >&2
  echo "examples: panel-refresh-2026q2-e1, enriques-mesh-quality-e2, fano-3folds-e3" >&2
  exit 2
fi

# Repo root resolution.
if REPO_ROOT_TRY=$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null); then
  REPO_ROOT="$REPO_ROOT_TRY"
else
  d="$(cd "$(dirname "$0")" && pwd)"
  while [[ "$d" != "/" && ! -d "$d/.git" ]]; do d="$(dirname "$d")"; done
  if [[ -d "$d/.git" ]]; then
    REPO_ROOT="$d"
  else
    echo "error: cannot find repo root (no .git ancestor)" >&2
    exit 1
  fi
fi

# Prefer the .venv interpreter so we never accidentally hit a stale system python3.
PY="$REPO_ROOT/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then
  PY="$REPO_ROOT/.venv/bin/python"
fi
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi

DIR="$REPO_ROOT/.claude/notes/milestones/$ID"
STATE="$DIR/state.json"

if [[ -f "$STATE" ]]; then
  PHASE=$("$PY" - "$STATE" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["phase"])
PY
  )
  echo "state already exists at $STATE (phase=$PHASE) -- resuming"
  exit 0
fi

mkdir -p "$DIR/research" "$DIR/artifacts"

NOW=$("$PY" -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))")

"$PY" - "$STATE" "$ID" "$NOW" "$BRIEF" "$RESEARCH_MODE" "$OSS_SCOUT_REQUESTED" <<'PY'
import json, os, sys
state_path, mid, now, brief, research_mode, oss_scout_requested = sys.argv[1:7]
state = {
    "id": mid,
    "created_at": now,
    "updated_at": now,
    "phase": "init",
    "phase_history": [{"phase": "init", "at": now}],
    "milestone_brief": brief,
    "research_mode": research_mode,
    "oss_scout_requested": oss_scout_requested == "true",
    "research_briefs": [],
    "research_synthesis": None,
    "implementation_path": None,
    "implementation_plan": None,
    "implementation_base": None,
    "implementation_commit_range": None,
    "implementation_commits": [],
    "implementation_branch": None,
    "critique_path": None,
    "critics_run": [],
    "critique_finding_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "rectification_commit": None,
    "fixed_findings": [],
    "deferred_findings": [],
    "invalidated_findings": [],
    "regression_tests_added": [],
}
tmp = state_path + ".json.tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2)
os.replace(tmp, state_path)
PY

if [[ -n "$BRIEF" ]]; then
  # printf '%s' avoids the trailing newline that 'echo' adds (off-by-one in wc -c).
  BRIEF_NOTE="set ($(printf '%s' "$BRIEF" | wc -c | tr -d ' ') chars)"
else
  BRIEF_NOTE="(empty -- pass --brief to populate)"
fi

echo "initialized $STATE"
echo "  brief: $BRIEF_NOTE"
echo "  phase: init"
