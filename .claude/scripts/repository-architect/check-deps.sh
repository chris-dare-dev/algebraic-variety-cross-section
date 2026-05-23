#!/usr/bin/env bash
# Pre-flight dependency check for /repository-architect.
#
# Verifies that libcst, pydeps, and coverage are installed in the project venv.
# Called by init-state.sh at second 1 of every restructure run so the user
# discovers missing deps BEFORE burning ~40 min of agent work.
#
# Usage: check-deps.sh
#
# Exit codes:
#   0 all required deps present
#   1 one or more required deps missing (stderr lists which + install hint)
#   2 venv interpreter not found

set -euo pipefail

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
  echo "ERROR: no venv interpreter found at $REPO_ROOT/.venv/" >&2
  echo "  Create the venv first: python3 -m venv .venv && pip install -r requirements.txt" >&2
  exit 2
fi

# Required packages (per phase scripts: rewrite-imports.py, snapshot-baseline.py,
# diff-baselines.py, parity-verifier agent).
REQUIRED=("libcst" "pydeps" "coverage")

MISSING=()
for pkg in "${REQUIRED[@]}"; do
  if ! "$PY" -c "import $pkg" 2>/dev/null; then
    MISSING+=("$pkg")
  fi
done

if [[ ${#MISSING[@]} -eq 0 ]]; then
  echo "deps check: all $((${#REQUIRED[@]})) required packages present"
  exit 0
fi

echo "ERROR: /repository-architect requires $((${#MISSING[@]})) missing package(s):" >&2
for pkg in "${MISSING[@]}"; do
  echo "  - $pkg" >&2
done
echo >&2
echo "Install with:" >&2
echo "  $PY -m pip install ${MISSING[*]}" >&2
echo >&2
echo "Or add to requirements.txt and re-install." >&2
echo >&2
echo "Why each is needed:" >&2
echo "  - libcst:   Phase 4 import rewrites (rewrite-imports.py); regex is forbidden (scout-C R6)" >&2
echo "  - pydeps:   Phase 3 dry-run import-graph delta; Phase 4 cycle parity check" >&2
echo "  - coverage: Phase 3 baseline coverage XML; Phase 4 per-batch coverage diff (±2% per file)" >&2
exit 1
