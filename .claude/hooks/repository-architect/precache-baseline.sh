#!/usr/bin/env bash
# Phase 3 precache hook for /repository-architect.
#
# Wraps snapshot-baseline.py.  If a fresh baseline already exists (<1h old),
# skips re-snapshot.  Otherwise captures pre-restructure state: pytest collect,
# coverage XML, pydeps JSON, import-time, star-imports, git SHA, symbols.
#
# Usage: precache-baseline.sh <restructure-id>
#
# Exit codes:
#   0 success (baseline exists, either freshly captured or pre-existing)
#   1 failure (snapshot-baseline.py errored; Phase 3 may need to retry)
#   2 usage error

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: precache-baseline.sh <restructure-id>" >&2
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

PREFLIGHT="$REPO_ROOT/.claude/notes/repository-architect/$ID/preflight"
if [[ ! -d "$PREFLIGHT" ]]; then
  echo "preflight dir does not exist: $PREFLIGHT" >&2
  echo "  run init-state.sh first" >&2
  exit 1
fi

# Freshness check (1 hour).
FRESH=true
for f in baseline.collect.txt baseline.git_sha.txt baseline.starimports.txt baseline.symbols.json; do
  if [[ ! -f "$PREFLIGHT/$f" ]]; then
    FRESH=false
    break
  fi
  if [[ -z "$(find "$PREFLIGHT/$f" -mmin -60 2>/dev/null)" ]]; then
    FRESH=false
    break
  fi
done

if [[ "$FRESH" == "true" ]]; then
  echo "baseline snapshot is fresh (<1h old); skipping"
  exit 0
fi

echo "Capturing baseline snapshot for $ID..."
if "$PY" "$REPO_ROOT/.claude/scripts/repository-architect/snapshot-baseline.py" "$ID"; then
  exit 0
else
  echo "ERROR: snapshot-baseline.py failed" >&2
  exit 1
fi
