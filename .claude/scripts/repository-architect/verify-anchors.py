#!/usr/bin/env python3
"""Verify all agent context anchors are free of stale paths post-batch.

Usage:
  verify-anchors.py <ID> [--batch <N>]

Reads .claude/notes/repository-architect/<ID>/design/symbol-map.json (filters
to batch <N> if specified, else all batches), greps for each "from" path
across:
  - CLAUDE.md, CONTEXT.md, README.md, AGENTS.md at repo root
  - .claude/notes/repository-architect/<ID>/**/*.md (active restructure files)
  - .claude/agent-memory/**/lessons.md

Acceptable matches (NOT counted as stale):
  - The repo-root MOVES.md (intentional sink)
  - Files under .claude/notes/repository-architect-design/ (historical design briefs)
  - Files under .claude/notes/<other-pipeline>/<other-ID>/ (closed prior-work artifacts)
  - Files under .claude/notes/repository-architect/<other-ID>/ where state.json.phase == "complete"

Exit codes:
  0 no stale anchors found
  1 stale anchors found (report on stdout)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


REPO_ROOT = Path(__file__).resolve().parents[3]


def is_acceptable_match(file_path: Path, current_rid: str) -> bool:
    rel = file_path.relative_to(REPO_ROOT).as_posix()
    # MOVES.md at repo root — intentional sink.
    if rel == "MOVES.md":
        return True
    # Design briefs (historical).
    if rel.startswith(".claude/notes/repository-architect-design/"):
        return True
    # Closed prior-work artifacts (any pipeline, NOT the current restructure).
    if rel.startswith(".claude/notes/") and not rel.startswith(f".claude/notes/repository-architect/{current_rid}/"):
        # If it's another repository-architect run, check if it's complete.
        m = re.match(r"\.claude/notes/repository-architect/([^/]+)/", rel)
        if m:
            other_rid = m.group(1)
            state_path = REPO_ROOT / ".claude" / "notes" / "repository-architect" / other_rid / "state.json"
            if state_path.exists():
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                    return state.get("phase") == "complete"
                except (json.JSONDecodeError, OSError):
                    return False
            return False
        # Other pipelines — treat as closed (historical artifact).
        return True
    return False


def grep_path(needle: str, in_files: list[Path]) -> list[tuple[Path, int, str]]:
    hits = []
    pattern = re.compile(re.escape(needle))
    for f in in_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append((f, lineno, line.rstrip()[:200]))
    return hits


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    rid = argv[1]
    batch = None
    if "--batch" in argv:
        i = argv.index("--batch")
        if i + 1 < len(argv):
            batch = int(argv[i + 1])

    smap = REPO_ROOT / ".claude" / "notes" / "repository-architect" / rid / "design" / "symbol-map.json"
    if not smap.exists():
        sys.exit(f"symbol-map not found: {smap}")

    entries = json.loads(smap.read_text(encoding="utf-8"))
    if batch is not None:
        entries = [e for e in entries if e.get("batch") == batch]

    if not entries:
        print(f"no symbol-map entries (batch={batch}); nothing to verify")
        return

    # Build the set of paths/symbols to check.  We grep for the "from" string verbatim
    # (it might be a module path like "appearance_panel" or a fully-qualified symbol).
    needles = sorted({e["from"] for e in entries})

    # Build the file list to grep.
    files = []
    for root_file in ("CLAUDE.md", "CONTEXT.md", "README.md", "AGENTS.md"):
        p = REPO_ROOT / root_file
        if p.exists():
            files.append(p)
    # Active restructure notes.
    active = REPO_ROOT / ".claude" / "notes" / "repository-architect" / rid
    if active.exists():
        files.extend(active.rglob("*.md"))
    # Agent memory lessons.
    mem = REPO_ROOT / ".claude" / "agent-memory"
    if mem.exists():
        files.extend(mem.rglob("lessons.md"))

    stale = []
    historical = 0
    for needle in needles:
        for f, lineno, line in grep_path(needle, files):
            if is_acceptable_match(f, rid):
                historical += 1
                continue
            stale.append((needle, f.relative_to(REPO_ROOT).as_posix(), lineno, line))

    print(f"# verify-anchors report for {rid}" + (f" (batch {batch})" if batch else " (all batches)"))
    print(f"  Needles checked:        {len(needles)}")
    print(f"  Files scanned:          {len(files)}")
    print(f"  Stale anchors found:    {len(stale)}")
    print(f"  Historical (acceptable): {historical}")
    if stale:
        print()
        print("## Stale anchors")
        for needle, path, lineno, line in stale:
            print(f"  {path}:{lineno}  needle={needle!r}  line={line!r}")
        sys.exit(1)
    print()
    print("No stale anchors found.")


if __name__ == "__main__":
    main(sys.argv)
