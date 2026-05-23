#!/usr/bin/env python3
"""LibCST-based import rewriter for /repository-architect Phase 4.

Usage:
  rewrite-imports.py --symbol-map <path> --batch <N> --operation "<label>" [--dry-run]

Reads a symbol-map JSON (output of Phase 2 design) and rewrites imports
across the tree to point at new locations.  Uses LibCST so formatting
and comments are preserved.

Symbol-map JSON shape (one record per moved symbol or module):

  [
    {
      "batch": 1,
      "operation": "Introduce panels/ subpackage",
      "kind": "module",                  # "module" | "symbol"
      "from": "appearance_panel",        # module path or symbol fully-qualified
      "to":   "panels.appearance",
      "symbol": null                      # only for kind=symbol (e.g. "AppearancePanel")
    },
    ...
  ]

This script is INTENTIONALLY conservative — if LibCST is not installed,
it exits 2 with a clear message rather than falling back to regex (per
scout-C §10.6: "Sed will be fine for these import rewrites" is refused).

Use --dry-run to preview without modifying files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


REPO_ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--symbol-map", required=True)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        import libcst as cst  # noqa: F401  (verifying presence; codemod imports below)
        from libcst.codemod import CodemodContext
        from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
    except ImportError:
        print("ERROR: libcst is not installed.", file=sys.stderr)
        print("  Please add `libcst` to requirements.txt and re-run.", file=sys.stderr)
        print("  Per scout-C anti-pattern table: sed/regex are forbidden for Python import rewrites.", file=sys.stderr)
        sys.exit(2)

    smap_path = Path(args.symbol_map)
    if not smap_path.is_absolute():
        smap_path = REPO_ROOT / smap_path
    if not smap_path.exists():
        sys.exit(f"symbol-map not found: {smap_path}")

    full_map = json.loads(smap_path.read_text(encoding="utf-8"))
    batch_entries = [e for e in full_map if e.get("batch") == args.batch]
    if not batch_entries:
        sys.exit(f"no symbol-map entries for batch {args.batch}")

    print(f"Rewriting imports for batch {args.batch}: {args.operation}")
    print(f"  Entries to apply: {len(batch_entries)}")
    if args.dry_run:
        print("  [DRY RUN — no files will be modified]")

    # Walk every .py file in the tree (excluding venv, git, claude worktrees).
    targets = []
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(".venv/") or rel.startswith(".git/") or ".claude/worktrees/" in rel:
            continue
        targets.append(p)

    modified = 0
    for tgt in targets:
        try:
            src_text = tgt.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"  SKIP {tgt}: {exc}")
            continue

        try:
            tree = cst.parse_module(src_text)
        except cst.ParserSyntaxError as exc:
            print(f"  SKIP {tgt} (parse error): {exc}")
            continue

        # Apply each batch entry as remove+add via LibCST codemod visitors.
        ctx = CodemodContext()
        for e in batch_entries:
            if e["kind"] == "module":
                # Remove `import <from>` and `from <from> import X`; add `import <to>` for the same X.
                RemoveImportsVisitor.remove_unused_import(ctx, e["from"])
                AddImportsVisitor.add_needed_import(ctx, e["to"])
            elif e["kind"] == "symbol":
                old_module = e["from"]
                new_module = e["to"]
                symbol = e["symbol"]
                RemoveImportsVisitor.remove_unused_import(ctx, old_module, symbol)
                AddImportsVisitor.add_needed_import(ctx, new_module, symbol)
            else:
                print(f"  WARN: unknown kind {e['kind']!r} in symbol-map entry; skipping", file=sys.stderr)

        try:
            new_tree = RemoveImportsVisitor(ctx).transform_module(tree)
            new_tree = AddImportsVisitor(ctx).transform_module(new_tree)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR rewriting {tgt}: {exc}", file=sys.stderr)
            continue

        if new_tree.code == src_text:
            continue

        if not args.dry_run:
            tgt.write_text(new_tree.code, encoding="utf-8")
        modified += 1
        rel = tgt.relative_to(REPO_ROOT).as_posix()
        print(f"  {'[dry] ' if args.dry_run else ''}rewrote: {rel}")

    print(f"Done. {modified} files {'would be ' if args.dry_run else ''}modified.")


if __name__ == "__main__":
    main()
