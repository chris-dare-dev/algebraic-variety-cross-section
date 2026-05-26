#!/bin/bash
# check-banlist.sh — TSP-5 responsibility-name banlist check.
# Prints any banlist filename found in the repo (excluding .venv and historical notes).
# Empty output = PASS; any line of output = FAIL.
#
# Banlist canonical source: .claude/references/repository-architect/anti-patterns.md (R19)
# Used by: .claude/references/repository-architect/verification-rubric.md (item 23)

set -euo pipefail

find . -type f \
  \( -name 'utils.py' \
  -o -name 'helpers.py' \
  -o -name 'common.py' \
  -o -name 'misc.py' \
  -o -name 'lib.py' \
  -o -name 'core.py' \
  -o -name 'manager.py' \
  -o -name 'services.py' \
  -o -name 'controllers.py' \) \
  -not -path './.venv/*' \
  -not -path './.git/*' \
  -not -path './.claude/notes/repository-architect-design/*' \
  -not -path './.claude/worktrees/*'
