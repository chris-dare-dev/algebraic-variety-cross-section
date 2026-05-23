#!/usr/bin/env bash
# Phase-transition hook for /repository-architect.
#
# Called after every checkpoint.py advance.  Appends a 5-line phase summary
# block to .claude/notes/repository-architect/<ID>/dispatch.log so the user
# can `tail -f` it to see pipeline progress.
#
# Usage: summarize-phase.sh <restructure-id> <new-phase>
#
# Exit codes:
#   0 success
#   1 dispatch.log dir missing
#   2 usage error

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: summarize-phase.sh <restructure-id> <new-phase>" >&2
  exit 2
fi

ID="$1"
PHASE="$2"

if REPO_ROOT_TRY=$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null); then
  REPO_ROOT="$REPO_ROOT_TRY"
else
  d="$(cd "$(dirname "$0")" && pwd)"
  while [[ "$d" != "/" && ! -d "$d/.git" ]]; do d="$(dirname "$d")"; done
  REPO_ROOT="$d"
fi

DIR="$REPO_ROOT/.claude/notes/repository-architect/$ID"
LOG="$DIR/dispatch.log"

if [[ ! -d "$DIR" ]]; then
  echo "restructure dir does not exist: $DIR" >&2
  exit 1
fi

NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Compute a one-line summary based on the phase.
case "$PHASE" in
  audit-complete)
    BRIEFS=$(find "$DIR/audit" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
    SUMMARY="audit complete: $BRIEFS brief(s) written; evaluator report at audit/evaluator-report.md"
    ;;
  design-complete)
    SUMMARY="design complete: PLAN.md + symbol-map.json + design-adversary-critique.md written"
    ;;
  preflight-complete)
    BASE=""
    if [[ -f "$DIR/preflight/baseline.git_sha.txt" ]]; then
      BASE=$(head -c 12 "$DIR/preflight/baseline.git_sha.txt" 2>/dev/null || echo "")
    fi
    SUMMARY="preflight complete: baseline captured at $BASE; dry-run report written"
    ;;
  execute-complete)
    COMMITS=$(git -C "$REPO_ROOT" log --oneline HEAD 2>/dev/null | wc -l | tr -d ' ' || echo "?")
    SUMMARY="execute complete: $COMMITS commit(s) since baseline; parity-diff.md written"
    ;;
  complete)
    SUMMARY="rectify complete: pipeline done"
    ;;
  *)
    SUMMARY="phase advanced"
    ;;
esac

{
  echo "================================================================"
  echo "$NOW | PHASE -> $PHASE"
  echo "  $SUMMARY"
  echo "  next: bash .claude/scripts/repository-architect/status.sh $ID"
  echo "================================================================"
} >> "$LOG"

echo "summary appended to $LOG"
