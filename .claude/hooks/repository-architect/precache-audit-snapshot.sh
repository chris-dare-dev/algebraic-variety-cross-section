#!/usr/bin/env bash
# Phase 1 precache hook for /repository-architect.
#
# Pre-computes the audit snapshot artifacts the auditor agent reads instead
# of re-running 30 grep/wc/find calls.  Cheap, idempotent.
#
# Usage: precache-audit-snapshot.sh <restructure-id>
#
# Outputs (under .claude/notes/repository-architect/<ID>/cache/):
#   - tree.txt              annotated top-level tree
#   - loc.csv               file,loc for every tracked .py file
#   - imports-rough.json    {file: [imported modules]}
#   - ai-invariants-card.md AI-1..AI-15 single-line summaries
#
# Exit codes:
#   0 success (cache populated; or cache fresh and no work needed)
#   1 failure (orchestrator continues without cache — agents fall back to fresh derivation)
#   2 usage error

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: precache-audit-snapshot.sh <restructure-id>" >&2
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

CACHE_DIR="$REPO_ROOT/.claude/notes/repository-architect/$ID/cache"
if [[ ! -d "$CACHE_DIR" ]]; then
  echo "cache dir does not exist: $CACHE_DIR" >&2
  echo "  run init-state.sh first" >&2
  exit 1
fi

# Freshness check: if all cache files exist and are <1h old, skip.
FRESH=true
for f in tree.txt loc.csv imports-rough.json ai-invariants-card.md; do
  if [[ ! -f "$CACHE_DIR/$f" ]]; then
    FRESH=false
    break
  fi
  # File age in seconds (portable: find with mtime).
  if [[ -z "$(find "$CACHE_DIR/$f" -mmin -60 2>/dev/null)" ]]; then
    FRESH=false
    break
  fi
done

if [[ "$FRESH" == "true" ]]; then
  echo "audit cache is fresh (<1h old); skipping"
  exit 0
fi

echo "Pre-caching audit snapshot for $ID..."
if "$PY" "$REPO_ROOT/.claude/scripts/repository-architect/audit-tree.py" "$ID"; then
  echo "audit cache populated"
  exit 0
else
  echo "WARNING: audit-tree.py failed; auditor agent will fall back to fresh derivation" >&2
  exit 1
fi
