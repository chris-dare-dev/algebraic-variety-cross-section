#!/usr/bin/env python3
"""Snapshot pre- or post-restructure baseline for /repository-architect Phase 3 + 4.

Usage:
  snapshot-baseline.py <ID>              # writes baseline.* into preflight/
  snapshot-baseline.py <ID> --post       # writes post.* into execute/

Captures (best-effort — skips missing tools with a documented warning):
  - pytest --collect-only -q        -> {prefix}.collect.txt
  - pytest + coverage (if installed) -> {prefix}.coverage.xml + summary
  - pydeps JSON (if installed)      -> {prefix}.imports.json
  - python -X importtime            -> {prefix}.importtime.log
  - star-import grep                -> {prefix}.starimports.txt
  - git rev-parse HEAD              -> {prefix}.git_sha.txt
  - per-symbol location index       -> {prefix}.symbols.json

Repo root: parents[3] from this file.
"""

from __future__ import annotations

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


def venv_python() -> str:
    for cand in (
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv" / "bin" / "python",
    ):
        if cand.exists():
            return str(cand)
    return "python3"


def run_capture(cmd: list[str], out_file: Path, timeout: int = 600) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        combined = result.stdout + (("\n--- stderr ---\n" + result.stderr) if result.stderr else "")
        out_file.write_text(combined, encoding="utf-8")
        return result.returncode, ""
    except FileNotFoundError as exc:
        msg = f"WARNING: command not found: {cmd[0]} ({exc})"
        out_file.write_text(msg + "\n", encoding="utf-8")
        return 127, msg
    except subprocess.TimeoutExpired:
        msg = f"WARNING: timeout after {timeout}s: {' '.join(cmd)}"
        out_file.write_text(msg + "\n", encoding="utf-8")
        return 124, msg


def capture_star_imports(out_file: Path) -> None:
    """Grep for 'import *' across .py files, excluding venv / .git / claude worktrees."""
    pattern = re.compile(r"import\s+\*")
    lines = []
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(".venv/") or rel.startswith(".git/") or ".claude/worktrees/" in rel:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                lines.append(f"{rel}:{lineno}:{line.rstrip()}")
    out_file.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")


_DEF_RE = re.compile(r"^(def|class)\s+(\w+)", re.MULTILINE)


def capture_symbols(out_file: Path) -> None:
    """Per-symbol location index: {symbol_name: [file:line, ...]}.

    Best-effort regex (does not handle nested defs / decorators perfectly);
    sufficient for the parity-verifier symbol-move check.
    """
    index: dict[str, list[str]] = {}
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(".venv/") or rel.startswith(".git/") or ".claude/worktrees/" in rel:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _DEF_RE.finditer(text):
            name = m.group(2)
            line = text[: m.start()].count("\n") + 1
            index.setdefault(name, []).append(f"{rel}:{line}")
    out_file.write_text(json.dumps(index, indent=2), encoding="utf-8")


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    rid = argv[1]
    post_mode = "--post" in argv[2:]
    prefix = "post" if post_mode else "baseline"
    out_subdir = "execute" if post_mode else "preflight"
    out_dir = REPO_ROOT / ".claude" / "notes" / "repository-architect" / rid / out_subdir
    if not out_dir.exists():
        sys.exit(f"output dir does not exist: {out_dir}\n  run init-state.sh {rid} first")

    py = venv_python()

    print(f"Snapshotting {prefix} into {out_dir}/")

    # 1. pytest collect-only
    print(f"  pytest --collect-only -q  ->  {prefix}.collect.txt")
    run_capture([py, "-m", "pytest", "--collect-only", "-q"], out_dir / f"{prefix}.collect.txt", timeout=300)

    # 2. Coverage (best-effort — needs coverage installed)
    print(f"  coverage run + xml         ->  {prefix}.coverage.xml")
    rc, _ = run_capture(
        [py, "-m", "coverage", "run", "-m", "pytest", "-q"],
        out_dir / f"{prefix}.coverage.run.log",
        timeout=600,
    )
    if rc == 0 or rc == 1:  # pytest exits 0/1 normally
        run_capture(
            [py, "-m", "coverage", "xml", "-o", str(out_dir / f"{prefix}.coverage.xml")],
            out_dir / f"{prefix}.coverage.xml.log",
            timeout=120,
        )

    # 3. pydeps JSON (best-effort)
    print(f"  pydeps --show-deps         ->  {prefix}.imports.json")
    run_capture(
        [py, "-m", "pydeps", ".", "--show-deps", "--noshow", "--max-bacon=0"],
        out_dir / f"{prefix}.imports.json",
        timeout=120,
    )

    # 4. import-time
    print(f"  python -X importtime app   ->  {prefix}.importtime.log")
    run_capture(
        [py, "-X", "importtime", "-c", "import app"],
        out_dir / f"{prefix}.importtime.log",
        timeout=60,
    )

    # 5. star-imports
    print(f"  grep 'import *'            ->  {prefix}.starimports.txt")
    capture_star_imports(out_dir / f"{prefix}.starimports.txt")

    # 6. git HEAD
    print(f"  git rev-parse HEAD         ->  {prefix}.git_sha.txt")
    run_capture(["git", "rev-parse", "HEAD"], out_dir / f"{prefix}.git_sha.txt", timeout=10)

    # 7. symbol index
    print(f"  symbol index               ->  {prefix}.symbols.json")
    capture_symbols(out_dir / f"{prefix}.symbols.json")

    print(f"Done.  Snapshot written to {out_dir}/")


if __name__ == "__main__":
    main(sys.argv)
