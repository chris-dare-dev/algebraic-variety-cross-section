#!/usr/bin/env bash
# Initialize restructure state directory and state.json for /repository-architect
# on the algebraic-variety-cross-section repo.
#
# Usage: init-state.sh <restructure-id> [--brief "verbatim user brief"]
#                                       [--audit-only | --design-only]
#                                       [--resume]
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
  echo "usage: init-state.sh <restructure-id> [--brief \"...\"] [--audit-only|--design-only] [--resume]" >&2
  exit 2
fi

ID="$1"
shift

BRIEF=""
STOP_AFTER_PHASE="null"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --brief)
      BRIEF="$(echo "${2:-}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
      shift 2
      ;;
    --audit-only)
      STOP_AFTER_PHASE="\"audit\""
      shift
      ;;
    --design-only)
      STOP_AFTER_PHASE="\"design\""
      shift
      ;;
    --resume)
      # --resume is a no-op at init time; orchestrator handles resume routing
      # by reading state.phase via validate-state.py.  Accepted here so
      # init-state.sh can be called with the full argv from the slash command
      # without dropping flags.
      shift
      ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

# Restructure id shape: starts with a letter, alphanumeric segments separated
# by single dashes (no double-dashes, no trailing dash), <=80 chars (slightly
# wider than milestone ids because restructure ids encode scope).
if ! [[ "$ID" =~ ^[a-zA-Z][a-zA-Z0-9]*(-[a-zA-Z0-9]+)*$ ]] || (( ${#ID} > 80 )); then
  echo "error: invalid restructure id '$ID' -- must be 1-80 chars, alphanumeric segments separated by single dashes, starting with a letter" >&2
  echo "examples: restructure-panels-2026q3-r1, restructure-surfaces-split-2026q4-r1" >&2
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

PY="$REPO_ROOT/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then
  PY="$REPO_ROOT/.venv/bin/python"
fi
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi

DIR="$REPO_ROOT/.claude/notes/repository-architect/$ID"
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

# Pre-flight deps check (closes adversary CRITICAL #3: libcst/pydeps/coverage
# missing surfaces at minute 40 instead of second 1).  Non-fatal in --resume
# mode (already gated above), but for a fresh restructure we ABORT here so
# the user can install before any agent work begins.
if ! bash "$(dirname "$0")/check-deps.sh"; then
  echo >&2
  echo "ABORT: required deps missing.  Install and re-run." >&2
  exit 1
fi

mkdir -p "$DIR/cache" "$DIR/audit" "$DIR/design" "$DIR/preflight" "$DIR/execute" "$DIR/rectify"

NOW=$("$PY" -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))")

"$PY" - "$STATE" "$ID" "$NOW" "$BRIEF" "$STOP_AFTER_PHASE" <<'PY'
import json, os, sys
state_path, rid, now, brief, stop_after_phase_json = sys.argv[1:6]
stop_after_phase = json.loads(stop_after_phase_json)  # None | "audit" | "design"
state = {
    "id": rid,
    "created_at": now,
    "updated_at": now,
    "phase": "init",
    "phase_history": [{"phase": "init", "at": now}],
    "restructure_brief": brief,
    "stop_after_phase": stop_after_phase,
    # Phase 1 fields
    "audit_briefs": [],
    "evaluator_report": None,
    # Phase 2 fields
    "plan_path": None,
    "symbol_map_path": None,
    "design_adversary_path": None,
    "design_adversary_finding_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    # Phase 3 fields
    "restructure_base": None,
    "baseline_dir": None,
    "dry_run_report_path": None,
    "dry_run_verdict": None,  # GREEN | YELLOW | RED
    # Phase 4 fields
    "execute_batches_planned": 0,
    "execute_batches_landed": 0,
    "execute_commit_range": None,
    "execute_commits": [],
    "parity_verifier_reports": [],
    "anchor_updater_reports": [],
    # Phase 5 fields
    "execution_critic_path": None,
    "test_suggester_path": None,
    "critique_finding_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "rectification_commit": None,
    "fixed_findings": [],
    "deferred_findings": [],
    "invalidated_findings": [],
    "user_gate_history": [],  # list of {gate: N, at: iso, response: "y"|"n"}
}
tmp = state_path + ".json.tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2)
os.replace(tmp, state_path)
PY

if [[ -n "$BRIEF" ]]; then
  BRIEF_NOTE="set ($(printf '%s' "$BRIEF" | wc -c | tr -d ' ') chars)"
else
  BRIEF_NOTE="(empty -- pass --brief to populate)"
fi

echo "initialized $STATE"
echo "  brief:            $BRIEF_NOTE"
echo "  stop_after_phase: $STOP_AFTER_PHASE"
echo "  phase:            init"
