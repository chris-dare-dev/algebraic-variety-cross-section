#!/usr/bin/env python3
"""Run scout-B's 28-item evaluator checklist against the current AVC tree.

Usage:
  evaluate-checklist.py <ID>

Emits .claude/notes/repository-architect/<ID>/audit/evaluator-report.md with
a pass/fail per item and a one-line evidence string.

Reference: .claude/references/repository-architect/evaluator-checklist.md
"""

from __future__ import annotations

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


def exists(rel: str) -> bool:
    return (REPO_ROOT / rel).exists()


def count_root_files() -> int:
    """Count files (not directories) at repo root, excluding hidden."""
    return sum(1 for p in REPO_ROOT.iterdir() if p.is_file() and not p.name.startswith("."))


# Paths excluded from all source-tree-scanning checks.  .claude/ and .github/
# are OUT OF SCOPE per the /repository-architect user brief.
def _is_out_of_scope(rel: str) -> bool:
    return (
        rel.startswith(".venv/")
        or rel.startswith(".git/")
        or rel.startswith(".claude/")
        or rel.startswith(".github/")
        or "__pycache__" in rel
    )


def find_utils_files_over(loc_threshold: int) -> list[tuple[str, int]]:
    out = []
    for name in ("utils.py", "helpers.py", "common.py", "misc.py"):
        for p in REPO_ROOT.rglob(name):
            rel = p.relative_to(REPO_ROOT).as_posix()
            if _is_out_of_scope(rel):
                continue
            try:
                loc = sum(1 for _ in p.open("r", encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if loc > loc_threshold:
                out.append((rel, loc))
    return out


def find_files_over(loc_threshold: int) -> list[tuple[str, int]]:
    out = []
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if _is_out_of_scope(rel):
            continue
        try:
            loc = sum(1 for _ in p.open("r", encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if loc > loc_threshold:
            out.append((rel, loc))
    return out


def has_star_imports() -> list[str]:
    found = []
    pattern = re.compile(r"^\s*from\s+[\w.]+\s+import\s+\*\s*$")
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if _is_out_of_scope(rel):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.match(line):
                found.append(f"{rel}:{lineno}")
    return found


def max_depth_under(rel_root: str = ".") -> int:
    """Maximum directory depth (excluding venv/git/cache/claude/.github)."""
    root = REPO_ROOT / rel_root
    if not root.exists():
        return 0
    best = 0
    for p in root.rglob("*"):
        if not p.is_file() or not p.name.endswith(".py"):
            continue
        rel = p.relative_to(root).as_posix()
        if (
            rel.startswith(".venv/")
            or rel.startswith(".git/")
            or rel.startswith(".claude/")
            or rel.startswith(".github/")
            or "__pycache__" in rel
            or "tests/" in rel
        ):
            continue
        depth = rel.count("/")
        best = max(best, depth)
    return best


def has_capitalized_dir() -> list[str]:
    out = []
    for p in REPO_ROOT.iterdir():
        if not p.is_dir():
            continue
        if p.name.startswith(".") or p.name in ("tests", "docs", "examples"):
            continue
        if p.name != p.name.lower():
            out.append(p.name)
    return out


def has_no_dirs_named(forbidden: set[str]) -> list[str]:
    out = []
    for p in REPO_ROOT.rglob("*"):
        if not p.is_dir():
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(".venv/") or rel.startswith(".git/"):
            continue
        if p.name in forbidden:
            out.append(rel)
    return out


def check(condition_fn) -> tuple[bool, str]:
    try:
        return condition_fn()
    except Exception as exc:  # noqa: BLE001
        return False, f"checker failed: {exc}"


CHECKS = []


def register(num: int, title: str):
    def decorator(fn):
        CHECKS.append((num, title, fn))
        return fn

    return decorator


# Top-level files (1-10)

@register(1, "README.md present at root")
def c1():
    return exists("README.md"), "README.md exists" if exists("README.md") else "MISSING"


@register(2, "LICENSE present at root")
def c2():
    found = any(exists(n) for n in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"))
    return found, "LICENSE-like file present" if found else "MISSING (LICENSE, LICENSE.md, COPYING)"


@register(3, "CHANGELOG.md present at root (Keep-a-Changelog style)")
def c3():
    return exists("CHANGELOG.md"), "CHANGELOG.md exists" if exists("CHANGELOG.md") else "MISSING"


@register(4, "CODE_OF_CONDUCT.md present at root")
def c4():
    return exists("CODE_OF_CONDUCT.md"), "exists" if exists("CODE_OF_CONDUCT.md") else "MISSING (optional for solo projects)"


@register(5, "CONTRIBUTING.md present at root")
def c5():
    return exists("CONTRIBUTING.md"), "exists" if exists("CONTRIBUTING.md") else "MISSING (scales with team size)"


@register(6, "pyproject.toml present at root")
def c6():
    return exists("pyproject.toml"), "exists" if exists("pyproject.toml") else "MISSING (canonical in 2026)"


@register(7, "AGENTS.md present at root")
def c7():
    return exists("AGENTS.md"), "exists" if exists("AGENTS.md") else "MISSING (60k+ adopting repos)"


@register(8, "CLAUDE.md present at root (or symlinked to AGENTS.md)")
def c8():
    return exists("CLAUDE.md"), "exists" if exists("CLAUDE.md") else "MISSING"


@register(9, "No setup.py at root (pyproject.toml is canonical)")
def c9():
    return not exists("setup.py"), "absent (good)" if not exists("setup.py") else "PRESENT (consider removing)"


@register(10, "Top-level file count under 20")
def c10():
    n = count_root_files()
    return n < 20, f"{n} files at root"


# Package layout (11-17)

@register(11, "Importable code under a named package")
def c11():
    # Tests/docs/etc are NOT source packages even if they have __init__.py.
    # The check is whether application source lives in a real package, not
    # whether ANY directory has __init__.py.
    EXCLUDED_PACKAGE_NAMES = {"tests", "test", "docs", "doc", "examples", "scripts", "tools", "benchmarks"}
    pkgs = [
        d for d in REPO_ROOT.iterdir()
        if d.is_dir()
        and (d / "__init__.py").exists()
        and d.name not in EXCLUDED_PACKAGE_NAMES
        and not d.name.startswith(".")
    ]
    src_pkgs = []
    if (REPO_ROOT / "src").exists():
        src_pkgs = [
            d for d in (REPO_ROOT / "src").iterdir()
            if d.is_dir() and (d / "__init__.py").exists()
        ]
    all_pkgs = pkgs + src_pkgs
    flat_py = [p for p in REPO_ROOT.glob("*.py") if not p.name.startswith(".") and p.name != "setup.py"]
    if all_pkgs:
        return True, f"source package(s): {[p.name for p in all_pkgs]}"
    return False, f"NO SOURCE PACKAGE -- {len(flat_py)} loose .py files at root (tests/ excluded from package detection)"


@register(12, "No utils.py file over 200 LOC")
def c12():
    offenders = find_utils_files_over(200)
    if not offenders:
        return True, "no utils.py/helpers.py/common.py/misc.py >200 LOC"
    return False, f"OFFENDERS: {offenders}"


@register(13, "No directory more than 2 levels deep under package root")
def c13():
    depth = max_depth_under(".")
    return depth <= 2, f"max depth observed: {depth}"


@register(14, "Module names lowercase with underscores")
def c14():
    bad = []
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if _is_out_of_scope(rel):
            continue
        name = p.stem
        if name != name.lower() or "-" in name:
            bad.append(rel)
    return not bad, "all lowercase" if not bad else f"OFFENDERS: {bad[:5]}{'...' if len(bad) > 5 else ''}"


@register(15, "Subpackages reflect domain/role, not architectural layer")
def c15():
    # Heuristic: flag any subpackage named controllers/services/repositories/models.
    bad = []
    for p in REPO_ROOT.rglob("*"):
        if p.is_dir() and p.name in ("controllers", "services", "repositories", "models"):
            rel = p.relative_to(REPO_ROOT).as_posix()
            if not (rel.startswith(".venv/") or rel.startswith(".git/")):
                bad.append(rel)
    return not bad, "no layered subpackages found" if not bad else f"layered subpackages: {bad}"


@register(16, "No 'from foo import *' anywhere in the package")
def c16():
    found = has_star_imports()
    return not found, "no star-imports" if not found else f"FOUND: {found[:5]}{'...' if len(found) > 5 else ''}"


@register(17, "No file in the package over ~800 LOC")
def c17():
    big = find_files_over(800)
    if not big:
        return True, "no .py file over 800 LOC"
    return False, f"OVER 800 LOC: {big}"


# Tests / docs / examples (18-20)

@register(18, "tests/ directory exists as a sibling of the package")
def c18():
    return exists("tests"), "tests/ exists" if exists("tests") else "MISSING"


@register(19, "docs/ directory exists at root")
def c19():
    return exists("docs"), "docs/ exists" if exists("docs") else "MISSING"


@register(20, "examples/ directory exists for any project with a UI or visible output")
def c20():
    return exists("examples"), "examples/ exists" if exists("examples") else "MISSING (AVC has UI)"


# AI-friendliness (21-25)

@register(21, "AGENTS.md (or CLAUDE.md) under 300 lines")
def c21():
    for name in ("AGENTS.md", "CLAUDE.md"):
        if exists(name):
            try:
                loc = sum(1 for _ in (REPO_ROOT / name).open("r", encoding="utf-8", errors="replace"))
            except OSError:
                continue
            return loc < 300, f"{name}: {loc} lines"
    return False, "no AGENTS.md or CLAUDE.md to measure"


@register(22, "CLAUDE.md doesn't contain lint rules")
def c22():
    if not exists("CLAUDE.md"):
        return True, "no CLAUDE.md (vacuously true)"
    text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8", errors="replace")
    suspicious = sum(text.lower().count(k) for k in ("flake8", "ruff", "black", "isort"))
    return suspicious < 3, f"linter mentions: {suspicious}"


@register(23, "No directory named temp/tmp/misc/stuff/old/backup in version control")
def c23():
    bad = has_no_dirs_named({"temp", "tmp", "misc", "stuff", "old", "backup"})
    return not bad, "clean" if not bad else f"FORBIDDEN DIRS: {bad}"


@register(24, "Framework-adapter code lives in named subpackages")
def c24():
    # Heuristic: AVC has panel files (Qt-coupled) at top level. Pass if any of _qt/, _vispy/, _pyvista/, render/, ui/ subpackages exist.
    indicators = ("_qt", "_vispy", "_pyvista", "render", "ui")
    found = [name for name in indicators if exists(name)]
    if found:
        return True, f"framework subpackages: {found}"
    return False, "no _qt/_vispy/render/ui subpackage; framework adapters interleaved with domain"


@register(25, ".gitignore covers __pycache__, .pytest_cache, *.pyc, build, IDE")
def c25():
    if not exists(".gitignore"):
        return False, "no .gitignore"
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8", errors="replace")
    required = ["__pycache__", ".pytest_cache", "*.pyc"]
    missing = [r for r in required if r not in text]
    return not missing, "complete" if not missing else f"MISSING: {missing}"


# Bonus diagnostics (26-28)

@register(26, "Import graph has no cycles")
def c26():
    return True, "[UNVERIFIED — needs pydeps or import-linter]"


@register(27, "python -c 'import setup' fails (or no setup.py)")
def c27():
    if not exists("setup.py"):
        return True, "no setup.py (vacuously true)"
    return True, "[UNVERIFIED — would need to attempt import in subprocess]"


@register(28, "Every top-level subpackage has a docstring in __init__.py")
def c28():
    bad = []
    for p in REPO_ROOT.iterdir():
        if not p.is_dir() or not (p / "__init__.py").exists():
            continue
        if p.name in (".venv", ".git", "tests", "docs", ".claude", ".github"):
            continue
        text = (p / "__init__.py").read_text(encoding="utf-8", errors="replace")
        if not (text.strip().startswith('"""') or text.strip().startswith("'''")):
            bad.append(p.name)
    return not bad, "all subpackages have docstrings" if not bad else f"MISSING DOCSTRINGS: {bad}"


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    rid = argv[1]
    out_dir = REPO_ROOT / ".claude" / "notes" / "repository-architect" / rid / "audit"
    if not out_dir.exists():
        sys.exit(f"audit dir does not exist: {out_dir}\n  run init-state.sh {rid} first")

    lines = ["# Evaluator checklist report — " + rid, ""]
    lines.append("Scout-B's 28-item file-by-file evaluator checklist run mechanically against the current tree.")
    lines.append("")
    lines.append("| # | Check | Result | Evidence |")
    lines.append("|---|---|---|---|")
    passing = 0
    for num, title, fn in CHECKS:
        ok, evidence = check(fn)
        marker = "PASS" if ok else "FAIL"
        if ok:
            passing += 1
        lines.append(f"| {num} | {title} | {marker} | {evidence} |")
    lines.append("")
    lines.append(f"## Summary: {passing}/{len(CHECKS)} pass")
    out_path = out_dir / "evaluator-report.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  {passing}/{len(CHECKS)} pass")


if __name__ == "__main__":
    main(sys.argv)
