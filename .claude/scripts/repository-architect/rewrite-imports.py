#!/usr/bin/env python3
"""LibCST-based import + call-site rewriter for /repository-architect Phase 4.

Usage:
  rewrite-imports.py --symbol-map <path> --batch <N> --operation "<label>" [--dry-run]

Reads a symbol-map JSON (output of Phase 2 design) and rewrites BOTH:
  1. import statements (`from old import X` -> `from new import X`,
     `import old` -> `import new`, `import old as alias` -> `import new as alias`)
  2. attribute-access call sites (`old.X(args)` -> `new.X(args)`,
     `old.SUBMOD.X` -> `new.SUBMOD.X`)

across the tree.  Uses a hand-rolled cst.CSTTransformer (not the
Remove/Add visitor pair, which would silently no-op because the symbol
is still in use).

Symbol-map JSON shape (one record per moved symbol or module):

  [
    {
      "batch": 1,
      "operation": "Introduce panels/ subpackage",
      "kind": "module",                  # "module" | "symbol"
      "from": "appearance_panel",        # source module dotted path
      "to":   "panels.appearance",       # target module dotted path
      "symbol": null                      # only for kind=symbol (e.g. "AppearancePanel")
    },
    ...
  ]

INTENTIONALLY conservative: if LibCST is not installed, exit 2 with a
clear message rather than falling back to regex (per scout-C anti-pattern
R6: sed/regex are forbidden for Python import rewrites).

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


def _dotted_to_attribute(cst_mod, dotted: str):
    """Convert a dotted string like 'panels.appearance' to a CST Attribute/Name node."""
    parts = dotted.split(".")
    node = cst_mod.Name(parts[0])
    for part in parts[1:]:
        node = cst_mod.Attribute(value=node, attr=cst_mod.Name(part))
    return node


def _attribute_dotted_path(node) -> str | None:
    """Read back a CST Name/Attribute chain into a dotted path string.

    Returns None if the node is not a pure name/attribute chain.
    """
    parts = []
    while True:
        if hasattr(node, "attr") and hasattr(node, "value"):
            parts.append(node.attr.value)
            node = node.value
        elif hasattr(node, "value") and isinstance(node.value, str):
            parts.append(node.value)
            return ".".join(reversed(parts))
        else:
            return None


def _build_transformer(cst_mod, module_renames: dict[str, str], symbol_renames: dict[str, tuple[str, str]]):
    """Build a CSTTransformer that rewrites imports + attribute-access call sites.

    Args:
        cst_mod: the imported `libcst` module.
        module_renames: {old_dotted: new_dotted} — for kind=module entries.
        symbol_renames: {old_dotted_module: (new_dotted_module, symbol)} —
            for kind=symbol entries.  Maps source-module -> (target-module, symbol).
    """

    class Rewriter(cst_mod.CSTTransformer):
        def leave_ImportFrom(self, original_node, updated_node):
            # `from <module> import X, Y, Z`
            mod_path = _attribute_dotted_path(updated_node.module) if updated_node.module else None
            if mod_path is None:
                return updated_node

            # Whole-module rename: from old -> from new
            if mod_path in module_renames:
                new_mod = module_renames[mod_path]
                return updated_node.with_changes(module=_dotted_to_attribute(cst_mod, new_mod))

            # Per-symbol rename: from old import X -> from new import X
            if mod_path in symbol_renames:
                new_mod, _expected_symbol = symbol_renames[mod_path]
                return updated_node.with_changes(module=_dotted_to_attribute(cst_mod, new_mod))

            return updated_node

        def leave_Import(self, original_node, updated_node):
            # `import old`, `import old as alias`, `import old.sub`
            new_names = []
            changed = False
            for alias in updated_node.names:
                mod_path = _attribute_dotted_path(alias.name)
                if mod_path is None:
                    new_names.append(alias)
                    continue
                if mod_path in module_renames:
                    new_mod = module_renames[mod_path]
                    new_names.append(alias.with_changes(name=_dotted_to_attribute(cst_mod, new_mod)))
                    changed = True
                else:
                    new_names.append(alias)
            if changed:
                return updated_node.with_changes(names=new_names)
            return updated_node

        def leave_Attribute(self, original_node, updated_node):
            # `old.X` -> `new.X` (call-site rewrite for module-rename case).
            # This catches `appearance_panel.AppearancePanel(parent)` etc.
            #
            # We only rewrite the LEAF of the attribute chain to avoid stomping
            # on nested rewrites (the visitor walks bottom-up).
            chain = _attribute_dotted_path(updated_node)
            if chain is None:
                return updated_node
            # Try longest prefix first (so 'panels.appearance.X' wins over 'panels.X').
            for old, new in sorted(module_renames.items(), key=lambda kv: -len(kv[0])):
                if chain == old or chain.startswith(old + "."):
                    suffix = chain[len(old):]  # includes leading "." or empty
                    new_chain = new + suffix
                    return _dotted_to_attribute(cst_mod, new_chain)
            return updated_node

    return Rewriter()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--symbol-map", required=True)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        import libcst as cst
    except ImportError:
        print("ERROR: libcst is not installed.", file=sys.stderr)
        print("  Please add `libcst` to requirements.txt and re-run.", file=sys.stderr)
        print("  Per scout-C anti-pattern R6: sed/regex are forbidden for Python import rewrites.", file=sys.stderr)
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

    # Partition entries by kind.
    module_renames: dict[str, str] = {}
    symbol_renames: dict[str, tuple[str, str]] = {}
    for e in batch_entries:
        kind = e.get("kind")
        if kind == "module":
            module_renames[e["from"]] = e["to"]
        elif kind == "symbol":
            old_module = e["from"]
            new_module = e["to"]
            symbol = e.get("symbol")
            if not symbol:
                print(f"  WARN: kind=symbol entry missing 'symbol' key; skipping: {e}", file=sys.stderr)
                continue
            symbol_renames[old_module] = (new_module, symbol)
        else:
            print(f"  WARN: unknown kind {kind!r} in symbol-map entry; skipping", file=sys.stderr)

    print(f"Rewriting imports + call sites for batch {args.batch}: {args.operation}")
    print(f"  Module renames: {len(module_renames)}, symbol renames: {len(symbol_renames)}")
    if args.dry_run:
        print("  [DRY RUN -- no files will be modified]")

    targets = []
    for p in REPO_ROOT.rglob("*.py"):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(".venv/") or rel.startswith(".git/") or ".claude/worktrees/" in rel:
            continue
        # Don't rewrite the shim files themselves (they live at the OLD paths and
        # are SUPPOSED to reference the NEW path explicitly).
        if rel in module_renames.values():
            continue
        targets.append(p)

    modified = 0
    transformer = _build_transformer(cst, module_renames, symbol_renames)
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

        try:
            new_tree = tree.visit(transformer)
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
