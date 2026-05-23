#!/usr/bin/env python3
"""Validate all shims added in a restructure batch emit DeprecationWarning correctly.

Usage:
  validate-shims.py <ID> --batch <N>

Reads .claude/notes/repository-architect/<ID>/design/symbol-map.json,
filters to batch <N>, and for each "from" path attempts:
  python -W error::DeprecationWarning -c "from <from-module> import <symbol>"

A correct shim raises DeprecationWarning, which `-W error` converts to an
exception — exit 1 = good shim, exit 0 = MISSING shim (regression).

Exit codes:
  0 all shims pass
  2 one or more shims fail validation
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


REPO_ROOT = Path(__file__).resolve().parents[3]


def venv_python() -> str:
    for cand in (
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv" / "bin" / "python",
    ):
        if cand.exists():
            return str(cand)
    return "python3"


def main(argv: list[str]) -> None:
    if len(argv) < 4 or "--batch" not in argv:
        print(__doc__)
        sys.exit(2)
    rid = argv[1]
    batch_idx = argv.index("--batch")
    if batch_idx + 1 >= len(argv):
        sys.exit("--batch requires a number")
    batch = int(argv[batch_idx + 1])

    smap = REPO_ROOT / ".claude" / "notes" / "repository-architect" / rid / "design" / "symbol-map.json"
    if not smap.exists():
        sys.exit(f"symbol-map not found: {smap}")

    entries = [e for e in json.loads(smap.read_text(encoding="utf-8")) if e.get("batch") == batch]
    if not entries:
        print(f"no symbol-map entries for batch {batch} -- nothing to validate")
        return

    py = venv_python()
    failures: list[tuple[str, str]] = []

    for e in entries:
        old_mod = e["from"]
        symbol = e.get("symbol")
        # Build an import that should trigger the shim.
        if e["kind"] == "module" or not symbol:
            stmt = f"import {old_mod}"
        else:
            stmt = f"from {old_mod} import {symbol}"

        try:
            result = subprocess.run(
                [py, "-W", "error::DeprecationWarning", "-c", stmt],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            failures.append((stmt, "TIMEOUT"))
            continue

        # Correct shim: -W error::DeprecationWarning converts the warning to an exception,
        # so returncode must be NON-ZERO with DeprecationWarning in stderr.
        if result.returncode == 0:
            failures.append((stmt, "no DeprecationWarning emitted (shim missing or silent)"))
        elif "DeprecationWarning" not in (result.stderr + result.stdout):
            failures.append((stmt, f"failed but not with DeprecationWarning: {result.stderr.strip()[:200]}"))
        else:
            print(f"  PASS  {stmt}")

    if failures:
        print(f"\n{len(failures)} shim(s) failed validation:")
        for stmt, reason in failures:
            print(f"  FAIL  {stmt}\n        -> {reason}")
        sys.exit(2)

    print(f"\nAll {len(entries)} shim(s) pass.")


if __name__ == "__main__":
    main(sys.argv)
