#!/usr/bin/env python3
"""Rank Must-tagged epics by RICE.

Usage:
  score-rice.py <slug>             # parse plans/<slug>-roadmap.md, rank Musts
  score-rice.py --example          # print canned example output (smoke test)

RICE = (Reach * Impact * Confidence) / Effort
- Reach:      integer, users/agents/runs per cycle
- Impact:     0.25 / 0.5 / 1 / 2 / 3
- Confidence: 0.0-1.0 (default 0.5 when unstated)
- Effort:     person-weeks (float, must be > 0)

Confidence default surfacing: if any input row has Confidence=0.5 from
default (not explicitly stated), the script prints a "DEFAULTED" warning
listing those epics so the orchestrator can confirm with the user.

Roadmap format expected: section 7.2 RICE rank table where rows have the
form `| 1 | \`<slug>-eN\` | R | I | C | E | RICE |`. To populate from 7.1
MoSCoW + a separate input file, use `--from <path>` (TSV: epic\\tR\\tI\\tC\\tE).

Repo root detection: --repo-root flag -> $REPO_ROOT env -> git rev-parse ->
walk up from script dir.

Exit codes:
  0 success
  1 parse/IO failure
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

# Pre-extracted format strings to avoid f-string-with-backslash gotchas.
HDR_FMT = "{:>4} {:<32} {:>6} {:>6} {:>6} {:>6} {:>8}"
ROW_FMT = "{:>4} {:<32} {:>6} {:>6} {:>6.0%} {:>6} {:>8.2f}"
SEP = "-" * 78


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


def parse_rice_rows(text: str) -> list[dict]:
    """Parse section 7.2 RICE rank table rows from a roadmap markdown body."""
    rows: list[dict] = []
    section_re = re.compile(
        r"<!--\s*ROADMAP:section:sequence\s*-->.*?(?=<!--\s*ROADMAP:section:|\Z)",
        re.DOTALL,
    )
    m = section_re.search(text)
    if not m:
        return rows
    body = m.group(0)
    # Match: | 1 | `slug-e1` | 100 | 2 | 80% | 1 | 160 |
    row_re = re.compile(
        r"\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)%?\s*\|\s*([\d.]+)\s*\|\s*[\d.]+\s*\|"
    )
    for m2 in row_re.finditer(body):
        epic, r, i, c, e = m2.groups()
        c_val = float(c)
        if c_val > 1.0:
            c_val = c_val / 100.0  # accept 80% form
        rows.append(
            {
                "epic": epic,
                "reach": float(r),
                "impact": float(i),
                "confidence": c_val,
                "effort": float(e),
                "defaulted_confidence": False,
            }
        )
    return rows


def parse_tsv(path: Path) -> list[dict]:
    rows: list[dict] = []
    for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            sys.exit(f"error: TSV line {ln}: expected epic\\tR\\tI\\tC?\\tE, got {len(parts)} fields")
        epic = parts[0]
        try:
            reach = float(parts[1])
            impact = float(parts[2])
            if len(parts) == 4:
                # epic R I E (Confidence omitted -> default 0.5)
                confidence = 0.5
                effort = float(parts[3])
                defaulted = True
            else:
                c_raw = parts[3].strip()
                if c_raw == "":
                    confidence = 0.5
                    defaulted = True
                else:
                    confidence = float(c_raw)
                    if confidence > 1.0:
                        confidence /= 100.0
                    defaulted = False
                effort = float(parts[4])
        except ValueError as exc:
            sys.exit(f"error: TSV line {ln}: {exc}")
        if effort <= 0:
            sys.exit(f"error: TSV line {ln}: effort must be > 0")
        rows.append(
            {
                "epic": epic,
                "reach": reach,
                "impact": impact,
                "confidence": confidence,
                "effort": effort,
                "defaulted_confidence": defaulted,
            }
        )
    return rows


def rank(rows: list[dict]) -> list[dict]:
    for r in rows:
        r["rice"] = (r["reach"] * r["impact"] * r["confidence"]) / r["effort"]
    rows.sort(key=lambda r: r["rice"], reverse=True)
    return rows


def render(rows: list[dict]) -> str:
    if not rows:
        return "(no Must epics to rank -- populate section 7.2 first)"
    out: list[str] = []
    out.append(SEP)
    out.append(HDR_FMT.format("Rank", "Epic", "R", "I", "C", "E", "RICE"))
    out.append(SEP)
    for i, r in enumerate(rows, 1):
        out.append(
            ROW_FMT.format(i, r["epic"], int(r["reach"]), r["impact"], r["confidence"], r["effort"], r["rice"])
        )
    out.append(SEP)
    defaulted = [r["epic"] for r in rows if r["defaulted_confidence"]]
    if defaulted:
        out.append("")
        out.append("DEFAULTED Confidence (=0.5) for:")
        for d in defaulted:
            out.append(f"  - {d}")
        out.append("-> Surface to the user before accepting the rank.")
    return "\n".join(out)


def example() -> None:
    rows = [
        {
            "epic": "enriques-mesh-quality-e1",
            "reach": 10,
            "impact": 3,
            "confidence": 0.5,
            "effort": 1,
            "defaulted_confidence": True,
        },
        {
            "epic": "enriques-mesh-quality-e2",
            "reach": 10,
            "impact": 2,
            "confidence": 0.8,
            "effort": 2,
            "defaulted_confidence": False,
        },
        {
            "epic": "dark-mode-palette-refresh-e1",
            "reach": 10,
            "impact": 1,
            "confidence": 1.0,
            "effort": 1,
            "defaulted_confidence": False,
        },
        {
            "epic": "hanson-camera-presets-e1",
            "reach": 3,
            "impact": 2,
            "confidence": 0.5,
            "effort": 0.5,
            "defaulted_confidence": True,
        },
    ]
    print(render(rank(rows)))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?", help="roadmap slug (matches plans/<slug>-roadmap.md)")
    ap.add_argument("--example", action="store_true", help="print canned example and exit")
    ap.add_argument("--from", dest="from_tsv", help="parse from TSV file instead of roadmap doc")
    ap.add_argument("--repo-root", help="explicit repo root path")
    args = ap.parse_args(argv)

    if args.example:
        example()
        return 0

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
        rows = parse_rice_rows(roadmap.read_text(encoding="utf-8"))

    print(render(rank(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
