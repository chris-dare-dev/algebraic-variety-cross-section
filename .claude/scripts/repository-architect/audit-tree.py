#!/usr/bin/env python3
"""Single-shot repository audit for /repository-architect Phase 1.

Emits the precached snapshot files the auditor agent reads instead of
re-running 30 grep/wc/find calls.  Idempotent; cheap to re-run.

Usage:
  audit-tree.py <ID>

Outputs (under .claude/notes/repository-architect/<ID>/cache/):
  - tree.txt              annotated top-level tree
  - loc.csv               file,loc for every tracked .py file (excluding .venv, .claude/worktrees)
  - imports-rough.json    {file: [imported modules]} from grep '^import|^from'
  - ai-invariants-card.md AI-1..AI-15 single-line summaries from app-invariants.md

Repo root: parents[3] from this file.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


REPO_ROOT = Path(__file__).resolve().parents[3]
# .claude/ and .github/ are OUT OF SCOPE per the /repository-architect user brief
# (standard tool folders that the pipeline must not touch).
EXCLUDE_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", ".claude", ".github"}
EXCLUDE_PATH_FRAGMENTS = (".claude/", ".github/")


def cache_dir(rid: str) -> Path:
    return REPO_ROOT / ".claude" / "notes" / "repository-architect" / rid / "cache"


def write_tree(out_dir: Path) -> None:
    """Annotated top-level tree (one level deep)."""
    lines = ["# Top-level tree (depth=1) for AVC repo"]
    for entry in sorted(REPO_ROOT.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if entry.name in EXCLUDE_DIRS:
            continue
        if entry.is_dir():
            count = sum(1 for _ in entry.rglob("*") if _.is_file())
            lines.append(f"{entry.name}/    [{count} files]")
        else:
            try:
                size = entry.stat().st_size
                lines.append(f"{entry.name}    [{size} bytes]")
            except OSError:
                lines.append(f"{entry.name}    [stat-failed]")
    (out_dir / "tree.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_loc(out_dir: Path) -> None:
    """CSV: file,loc for every tracked .py file (excluding .venv, .claude/worktrees, tests/test_*.py grouped)."""
    rows = []
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if any(rel.startswith(d + "/") for d in EXCLUDE_DIRS):
            continue
        if any(frag in rel for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        try:
            with p.open("r", encoding="utf-8", errors="replace") as f:
                loc = sum(1 for _ in f)
        except OSError:
            loc = -1
        rows.append((rel, loc))
    rows.sort(key=lambda r: (-r[1], r[0]))
    csv_path = out_dir / "loc.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "loc"])
        w.writerows(rows)


_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)


def write_imports(out_dir: Path) -> None:
    """JSON: {file: [imported top-level modules]} from grep."""
    result: dict[str, list[str]] = {}
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if any(rel.startswith(d + "/") for d in EXCLUDE_DIRS):
            continue
        if any(frag in rel for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        mods = set()
        for m in _IMPORT_RE.finditer(text):
            module = m.group(1) or m.group(2)
            if module:
                top = module.split(".")[0]
                mods.add(top)
        result[rel] = sorted(mods)
    (out_dir / "imports-rough.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )


def write_ai_invariants(out_dir: Path) -> None:
    """Extract one-line summaries of AI-1..AI-15 from app-invariants.md."""
    src = REPO_ROOT / ".claude" / "references" / "app-invariants.md"
    if not src.exists():
        (out_dir / "ai-invariants-card.md").write_text(
            "# AI-1..AI-15 quick card\n\nERROR: app-invariants.md not found at " + str(src) + "\n",
            encoding="utf-8",
        )
        return
    text = src.read_text(encoding="utf-8", errors="replace")
    out_lines = ["# AI-1..AI-15 quick card (extracted from app-invariants.md)\n"]
    # Match patterns like "## AI-1" or "### AI-1" or "AI-1:" at line start.
    for i in range(1, 30):
        marker = f"AI-{i}"
        # Find the first line that starts with the marker (allowing leading # or whitespace).
        pattern = re.compile(rf"^[#\s\*]*{re.escape(marker)}\b.*$", re.MULTILINE)
        m = pattern.search(text)
        if not m:
            continue
        header = m.group(0).strip("# *\n").strip()
        # First non-empty line after the header is the one-line summary.
        tail = text[m.end():m.end() + 800]
        summary = ""
        for line in tail.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                break
            summary = stripped[:200]
            break
        out_lines.append(f"- **{header}** — {summary}")
    (out_dir / "ai-invariants-card.md").write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    rid = argv[1]
    out_dir = cache_dir(rid)
    if not out_dir.exists():
        sys.exit(f"cache dir does not exist: {out_dir}\n  run init-state.sh {rid} first")
    write_tree(out_dir)
    write_loc(out_dir)
    write_imports(out_dir)
    write_ai_invariants(out_dir)
    print(f"audit cache written to {out_dir}")
    for name in ("tree.txt", "loc.csv", "imports-rough.json", "ai-invariants-card.md"):
        p = out_dir / name
        print(f"  - {name}  [{p.stat().st_size} bytes]")


if __name__ == "__main__":
    main(sys.argv)
