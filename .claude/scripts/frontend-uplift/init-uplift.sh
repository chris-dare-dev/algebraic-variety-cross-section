#!/usr/bin/env bash
# Initialize frontend-uplift state directory and state.json.
#
# Usage: init-uplift.sh <uplift-id> [--brief "verbatim user brief"] [--surfaces "csv,of,surface-keys"]
#
# Idempotent: if state.json exists, prints current phase and exits 0.
#
# <uplift-id> is a free-form slug.  Typical convention: date-tagged scope,
# e.g. "2026q2-panel-refresh" or "calabi-yau-hero-experience-v1".
#
# --surfaces is an optional CSV of `Variety/Subtype` keys the visual scout
# should off-screen render.  Default (empty): the visual scout renders the
# canonical 5-surface set documented in references/frontend-uplift/phase-discover.md.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: init-uplift.sh <uplift-id> [--brief \"...\"] [--surfaces \"csv\"]" >&2
  exit 2
fi

ID="$1"
shift

BRIEF=""
SURFACES=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --brief)
      BRIEF="${2:-}"
      shift 2
      ;;
    --surfaces)
      SURFACES="${2:-}"
      shift 2
      ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
DIR="$REPO_ROOT/.claude/notes/frontend-uplifts/$ID"
STATE="$DIR/state.json"

if [[ -f "$STATE" ]]; then
  PHASE=$(python3 -c "import json; print(json.load(open('$STATE'))['phase'])")
  echo "state already exists at $STATE (phase=$PHASE) — resuming"
  exit 0
fi

mkdir -p "$DIR/discover" "$DIR/renders" "$DIR/artifacts"

NOW=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))")

python3 - "$STATE" "$ID" "$NOW" "$BRIEF" "$SURFACES" <<'PY'
import json, os, sys
state_path, sid, now, brief, surfaces_csv = sys.argv[1:6]
surfaces = [s.strip() for s in surfaces_csv.split(",") if s.strip()] if surfaces_csv else []
state = {
    "id": sid,
    "kind": "frontend-uplift",
    "created_at": now,
    "updated_at": now,
    "phase": "init",
    "phase_history": [{"phase": "init", "at": now}],
    "uplift_brief": brief,
    # Phase 1
    "discover_mode": None,        # "standard" (4 agents) | "lean" (visual + current-state-critic only)
    "surfaces_to_render": surfaces,  # user override; empty → canonical 5-surface set
    "agents_dispatched": [],
    "agents_returned": [],
    "discover_briefs": [],
    "render_dir": f".claude/notes/frontend-uplifts/{sid}/renders",
    # Phase 2
    "synthesis_path": None,
    "candidate_count": 0,
    # Phase 3
    "challenge_path": None,
    "challenge_finding_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    # Phase 4
    "final_report_path": None,
    "ranked_candidates": [],
}
tmp = state_path + ".tmp"
with open(tmp, "w") as f:
    json.dump(state, f, indent=2)
os.replace(tmp, state_path)
PY

echo "initialized $STATE"
echo "  brief:    $(if [[ -n "$BRIEF" ]]; then echo "set ($(echo "$BRIEF" | wc -c | tr -d ' ') chars)"; else echo "(empty — pass --brief to populate)"; fi)"
echo "  surfaces: $(if [[ -n "$SURFACES" ]]; then echo "$SURFACES"; else echo "(default — canonical 5-surface set)"; fi)"
echo "  phase:    init"
