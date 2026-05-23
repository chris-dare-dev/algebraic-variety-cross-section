#!/usr/bin/env python3
"""Diff pre/post baselines for /repository-architect Phase 4 final parity report.

Usage:
  diff-baselines.py <ID>

Reads:
  - .claude/notes/repository-architect/<ID>/preflight/baseline.{collect,coverage.xml,imports.json,importtime.log,starimports.txt,git_sha.txt,symbols.json}
  - .claude/notes/repository-architect/<ID>/execute/post.{...same...}

Emits to stdout (orchestrator redirects to parity-diff.md):
  Markdown report with collection diff, coverage delta, cycle delta,
  import-time delta, star-import diff, symbol-move audit.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


REPO_ROOT = Path(__file__).resolve().parents[3]


def read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def read_json(p: Path) -> object | None:
    s = read_text(p)
    if s is None:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def collection_diff(pre: Path, post: Path) -> list[str]:
    pre_lines = (read_text(pre) or "").splitlines()
    post_lines = (read_text(post) or "").splitlines()
    pre_set = {ln.strip() for ln in pre_lines if "::" in ln}
    post_set = {ln.strip() for ln in post_lines if "::" in ln}
    return [
        f"baseline tests: {len(pre_set)}",
        f"post     tests: {len(post_set)}",
        f"delta:          {len(post_set) - len(pre_set)}",
        f"removed (in pre, not post): {len(pre_set - post_set)}",
        f"added   (in post, not pre): {len(post_set - pre_set)}",
    ]


def coverage_total(p: Path) -> tuple[int, int] | None:
    s = read_text(p)
    if not s or "<coverage" not in s:
        return None
    try:
        root = ET.fromstring(s)
        # Coverage.py XML has <coverage line-rate="0.81" lines-valid="N" lines-covered="N"/> on root.
        valid = int(root.attrib.get("lines-valid", 0))
        covered = int(root.attrib.get("lines-covered", 0))
        return covered, valid
    except (ET.ParseError, ValueError):
        return None


def coverage_diff(pre: Path, post: Path) -> list[str]:
    pre_t = coverage_total(pre)
    post_t = coverage_total(post)
    if pre_t is None:
        return ["baseline coverage XML missing or unparseable"]
    if post_t is None:
        return ["post coverage XML missing or unparseable"]
    pre_pct = 100.0 * pre_t[0] / pre_t[1] if pre_t[1] else 0.0
    post_pct = 100.0 * post_t[0] / post_t[1] if post_t[1] else 0.0
    return [
        f"baseline: {pre_t[0]}/{pre_t[1]}  ({pre_pct:.2f}%)",
        f"post:     {post_t[0]}/{post_t[1]}  ({post_pct:.2f}%)",
        f"delta:    {post_pct - pre_pct:+.2f} percentage points",
    ]


def importtime_total(p: Path) -> float | None:
    s = read_text(p)
    if not s:
        return None
    # importtime output ends with a 'self' column; total = last self entry of root import.
    # Simpler heuristic: take total of all 'self' microseconds across the log.
    total_us = 0
    for line in s.splitlines():
        # Format: "import time:    self [us] | cumulative | module"
        parts = line.split("|")
        if len(parts) >= 3 and "import time:" in parts[0]:
            try:
                self_us = int(parts[0].split(":")[-1].strip())
                total_us += self_us
            except ValueError:
                continue
    return total_us / 1000.0 if total_us else None  # ms


def importtime_diff(pre: Path, post: Path) -> list[str]:
    pre_ms = importtime_total(pre)
    post_ms = importtime_total(post)
    if pre_ms is None or post_ms is None:
        return ["import-time log missing or unparseable"]
    delta_pct = 100.0 * (post_ms - pre_ms) / pre_ms if pre_ms else 0.0
    return [
        f"baseline: {pre_ms:.1f} ms",
        f"post:     {post_ms:.1f} ms",
        f"delta:    {delta_pct:+.1f}%",
    ]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    rid = argv[1]
    pre = REPO_ROOT / ".claude" / "notes" / "repository-architect" / rid / "preflight"
    post = REPO_ROOT / ".claude" / "notes" / "repository-architect" / rid / "execute"
    if not pre.exists() or not post.exists():
        sys.exit(f"missing preflight or execute dir for {rid}")

    print(f"# Parity diff report — {rid}\n")

    print("## Test collection diff")
    for line in collection_diff(pre / "baseline.collect.txt", post / "post.collect.txt"):
        print(f"  - {line}")
    print()

    print("## Coverage diff (totals)")
    for line in coverage_diff(pre / "baseline.coverage.xml", post / "post.coverage.xml"):
        print(f"  - {line}")
    print()

    print("## Import-time diff")
    for line in importtime_diff(pre / "baseline.importtime.log", post / "post.importtime.log"):
        print(f"  - {line}")
    print()

    print("## Star-imports diff")
    pre_si = set((read_text(pre / "baseline.starimports.txt") or "").splitlines())
    post_si = set((read_text(post / "post.starimports.txt") or "").splitlines())
    new_si = post_si - pre_si
    removed_si = pre_si - post_si
    print(f"  - new star-imports introduced: {len(new_si)}")
    for s in sorted(new_si):
        print(f"    + {s}")
    print(f"  - star-imports removed:        {len(removed_si)}")
    print()

    print("## Symbol relocation audit (top-level def/class only)")
    pre_sym = read_json(pre / "baseline.symbols.json") or {}
    post_sym = read_json(post / "post.symbols.json") or {}
    moved = []
    lost = []
    for name, locs in pre_sym.items():
        new_locs = post_sym.get(name, [])
        if not new_locs:
            lost.append(name)
        elif sorted(locs) != sorted(new_locs):
            moved.append((name, locs, new_locs))
    print(f"  - symbols whose location changed: {len(moved)}")
    for name, old, new in moved[:50]:
        print(f"    ~ {name}: {old} -> {new}")
    if len(moved) > 50:
        print(f"    ... and {len(moved) - 50} more")
    print(f"  - symbols lost entirely (present in pre, absent in post): {len(lost)}")
    for name in lost[:50]:
        print(f"    - {name}")
    if len(lost) > 50:
        print(f"    ... and {len(lost) - 50} more")


if __name__ == "__main__":
    main(sys.argv)
