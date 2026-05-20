#!/usr/bin/env python3
"""Validate the MoSCoW Must cap for a roadmap.

Hard rule: Musts <= 60% of total epic count (DSDM Consortium 2014, S10.4).

Usage:
  score-moscow.py <slug>             # parse plans/<slug>-roadmap.md
  score-moscow.py --example          # print canned example (passes)
  score-moscow.py --example-fail     # print canned example (75% Must -- fails)
  score-moscow.py --from <tsv>       # epic\\ttag TSV
  score-moscow.py --allow-must-overflow ...  # warn, exit 0 (emergency only)

Roadmap format expected: section 7.1 with table rows
  `| <slug>-eN | Must | rationale |` (or Should/Could/Won't)

Exit codes:
  0 cap satisfied
  1 cap violated (or no rows found)
  2 usage error
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stdout/stderr so any non-ASCII content does not crash on Windows
# default cp1252 codepage.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

CAP = 0.60  # 60% -- DSDM S10.4

VALID_TAGS = {"Must", "Should", "Could", "Won't"}


def find_repo_root(flag: str | None) -> Path:
    if flag:
        return Path(flag).resolve()
    env = os.environ.get("REPO_ROOT")
    if env:
        return Path(env).resolve()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(out.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    d = Path(__file__).resolve().parent
    for p in [d, *d.parents]:
        if (p / ".git").exists():
            return p
    sys.exit("error: cannot find repo root")


def parse_rows(text: str) -> list[tuple[str, str]]:
    """Return [(epic, tag), ...]. Both pulled from section 7.1 MoSCoW table."""
    rows: list[tuple[str, str]] = []
    section_re = re.compile(
        r"<!--\s*ROADMAP:section:sequence\s*-->.*?(?=<!--\s*ROADMAP:section:|\Z)",
        re.DOTALL,
    )
    m = section_re.search(text)
    if not m:
        return rows
    body = m.group(0)
    # Match: | `slug-e1` | Must | rationale |
    row_re = re.compile(r"\|\s*`([^`]+)`\s*\|\s*(Must|Should|Could|Won't)\s*\|", re.IGNORECASE)
    for rm in row_re.finditer(body):
        epic, tag = rm.groups()
        tag_norm = tag.capitalize() if tag.lower() != "won't" else "Won't"
        rows.append((epic, tag_norm))
    return rows


def parse_tsv(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            sys.exit(f"error: TSV line {ln}: expected epic\\ttag")
        epic, tag = parts
        if tag not in VALID_TAGS:
            sys.exit(f"error: TSV line {ln}: tag '{tag}' not in {VALID_TAGS}")
        rows.append((epic, tag))
    return rows


def evaluate(rows: list[tuple[str, str]], allow_overflow: bool) -> int:
    if not rows:
        print("error: no MoSCoW rows found in section 7.1", file=sys.stderr)
        return 1
    total = len(rows)
    must_count = sum(1 for _, t in rows if t == "Must")
    pct = must_count / total
    print(f"Total epics:  {total}")
    print(f"Musts:        {must_count} ({pct:.0%})")
    print(f"Cap:          {int(CAP * 100)}%")
    by_tag: dict[str, int] = {}
    for _, t in rows:
        by_tag[t] = by_tag.get(t, 0) + 1
    print("Distribution: " + ", ".join(f"{k}={v}" for k, v in sorted(by_tag.items())))
    if pct <= CAP:
        print(f"OK -- cap satisfied ({must_count}/{total} = {pct:.0%}).")
        return 0
    print()
    print(f"VIOLATION -- Musts {must_count}/{total} = {pct:.0%} exceeds {int(CAP * 100)}% cap.")
    print("Action: re-tag the lowest-RICE Musts as Should until cap holds.")
    must_epics = [e for e, t in rows if t == "Must"]
    print("Currently Must: " + ", ".join(must_epics))
    if allow_overflow:
        print()
        print("WARNING: --allow-must-overflow set; exiting 0 despite violation.")
        print("This bypasses a load-bearing prioritization invariant. Document why.")
        return 0
    return 1


def example_ok(allow_overflow: bool = False) -> int:
    rows = [
        ("enriques-mesh-quality-e1", "Must"),
        ("enriques-mesh-quality-e2", "Must"),
        ("enriques-mesh-quality-e3", "Should"),
        ("enriques-mesh-quality-e4", "Should"),
        ("enriques-mesh-quality-e5", "Could"),
    ]
    return evaluate(rows, allow_overflow=allow_overflow)


def example_fail(allow_overflow: bool = False) -> int:
    rows = [
        ("dark-mode-palette-refresh-e1", "Must"),
        ("dark-mode-palette-refresh-e2", "Must"),
        ("dark-mode-palette-refresh-e3", "Must"),
        ("dark-mode-palette-refresh-e4", "Should"),
    ]
    return evaluate(rows, allow_overflow=allow_overflow)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--example", action="store_true")
    ap.add_argument("--example-fail", action="store_true")
    ap.add_argument("--from", dest="from_tsv")
    ap.add_argument("--allow-must-overflow", action="store_true", help="warn-only mode (emergency)")
    ap.add_argument("--repo-root")
    args = ap.parse_args(argv)

    if args.example:
        return example_ok(allow_overflow=args.allow_must_overflow)
    if args.example_fail:
        return example_fail(allow_overflow=args.allow_must_overflow)

    if not args.slug and not args.from_tsv:
        ap.print_usage()
        return 2

    if args.from_tsv:
        rows = parse_tsv(Path(args.from_tsv))
    else:
        repo = find_repo_root(args.repo_root)
        roadmap = repo / "plans" / f"{args.slug}-roadmap.md"
        if not roadmap.exists():
            print(f"error: {roadmap} not found", file=sys.stderr)
            return 1
        rows = parse_rows(roadmap.read_text(encoding="utf-8"))

    return evaluate(rows, allow_overflow=args.allow_must_overflow)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
