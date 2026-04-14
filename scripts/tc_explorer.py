#!/usr/bin/env python3
"""
tc_explorer.py — Explore Diablo II treasure class trees.

Examples:
    python scripts/tc_explorer.py --tc "Act 5 Super C"
    python scripts/tc_explorer.py --tc "Act 5 Super C" --resolve --top 25
    python scripts/tc_explorer.py --reverse armo87
    python scripts/tc_explorer.py --list-prefix Mephisto
    python scripts/tc_explorer.py --tc "Act 5 Super C" --resolve --json
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data_tables")
DEFAULT_TC_TREE = os.path.join(DATA_DIR, "tc_tree.json")


def load_tc_tree(path: str) -> Dict[str, Any]:
    """Load a treasure class tree JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Treasure class tree not found at {path}. "
            "Generate it first with: python scripts/mpq_extract.py --all-mpqs <D2 dir> --tc-tree"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def immediate_summary(tc_tree: Dict[str, Any], tc_name: str) -> Dict[str, Any]:
    """Return the direct entries for one treasure class."""
    if tc_name not in tc_tree:
        raise KeyError(f"Treasure class not found: {tc_name}")
    node = tc_tree[tc_name]
    entries = node.get("entries", [])
    total_prob = int(node.get("nodrop", 0)) + sum(int(e.get("prob", 0)) for e in entries)
    summarized = []
    for entry in entries:
        prob = int(entry.get("prob", 0))
        share = (prob / total_prob) if total_prob else 0.0
        summarized.append(
            {
                "item": entry.get("item", ""),
                "prob": prob,
                "share": share,
                "is_sub_tc": entry.get("item", "") in tc_tree,
            }
        )
    return {
        "name": tc_name,
        "picks": int(node.get("picks", 1)),
        "nodrop": int(node.get("nodrop", 0)),
        "total_prob": total_prob,
        "entries": summarized,
    }


def resolve_terminals(
    tc_tree: Dict[str, Any],
    tc_name: str,
    weight: float = 1.0,
    depth: int = 0,
    max_depth: int = 20,
    stack: Optional[Set[str]] = None,
) -> Dict[str, float]:
    """Resolve a TC into expected terminal shares.

    The returned values are expected terminal shares per TC invocation.
    For TCs with picks > 1, shares can sum to more than 1.0 because they
    represent expected drop counts, not strict mutually-exclusive probabilities.
    """
    if stack is None:
        stack = set()
    if depth > max_depth:
        return {"<max-depth>": weight}
    if tc_name in stack:
        return {f"<cycle:{tc_name}>": weight}
    if tc_name not in tc_tree:
        return {tc_name: weight}

    node = tc_tree[tc_name]
    picks = max(1, int(node.get("picks", 1) or 1))
    nodrop = int(node.get("nodrop", 0) or 0)
    entries = node.get("entries", [])
    total = nodrop + sum(int(e.get("prob", 0) or 0) for e in entries)
    if total <= 0:
        return {"<empty>": weight}

    out: Dict[str, float] = defaultdict(float)
    next_stack = set(stack)
    next_stack.add(tc_name)

    if nodrop:
        out["<NoDrop>"] += weight * picks * (nodrop / total)

    for entry in entries:
        item = entry.get("item", "")
        prob = int(entry.get("prob", 0) or 0)
        if prob <= 0:
            continue
        child_weight = weight * picks * (prob / total)
        for child_item, child_share in resolve_terminals(
            tc_tree, item, child_weight, depth + 1, max_depth, next_stack
        ).items():
            out[child_item] += child_share
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def reverse_lookup(tc_tree: Dict[str, Any], target_item: str, max_depth: int = 20) -> List[Tuple[str, float]]:
    """Find all TCs that can resolve into a target item."""
    hits: List[Tuple[str, float]] = []
    for tc_name in tc_tree:
        resolved = resolve_terminals(tc_tree, tc_name, max_depth=max_depth)
        share = resolved.get(target_item, 0.0)
        if share > 0:
            hits.append((tc_name, share))
    return sorted(hits, key=lambda kv: (-kv[1], kv[0]))


def list_prefix(tc_tree: Dict[str, Any], prefix: str) -> List[str]:
    """List TC names beginning with a prefix, case-insensitive."""
    p = prefix.lower()
    return sorted(name for name in tc_tree if name.lower().startswith(p))


def print_summary(summary: Dict[str, Any]) -> None:
    print(f"TC:      {summary['name']}")
    print(f"Picks:   {summary['picks']}")
    print(f"NoDrop:  {summary['nodrop']}")
    print(f"Entries: {len(summary['entries'])}")
    print()
    for entry in summary["entries"]:
        kind = "TC" if entry["is_sub_tc"] else "ITEM"
        print(f"  {entry['item']:<35} {entry['prob']:>6}  {entry['share']*100:>6.2f}%  [{kind}]")


def print_resolved(tc_name: str, resolved: Dict[str, float], top: int) -> None:
    print(f"Resolved terminals for: {tc_name}")
    print("Values are expected terminal shares per TC invocation.")
    print()
    for item, share in list(resolved.items())[:top]:
        print(f"  {item:<35} {share:>10.6f}")


def print_reverse(target: str, hits: List[Tuple[str, float]], top: int) -> None:
    print(f"Treasure classes that can resolve into: {target}")
    print("Values are expected terminal shares per TC invocation.")
    print()
    for tc_name, share in hits[:top]:
        print(f"  {tc_name:<40} {share:>10.6f}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Explore Diablo II treasure class trees")
    ap.add_argument("--tree", default=DEFAULT_TC_TREE, help="Path to tc_tree.json")
    ap.add_argument("--tc", help="Treasure class name to inspect")
    ap.add_argument("--resolve", action="store_true", help="Resolve a TC into terminal items")
    ap.add_argument("--reverse", help="Find all TCs that can resolve into the given item code")
    ap.add_argument("--list-prefix", help="List treasure classes starting with a prefix")
    ap.add_argument("--max-depth", type=int, default=20, help="Maximum recursion depth")
    ap.add_argument("--top", type=int, default=20, help="Rows to print for resolved/reverse output")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of plain text")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    tc_tree = load_tc_tree(args.tree)

    if args.list_prefix:
        matches = list_prefix(tc_tree, args.list_prefix)
        if args.json:
            print(json.dumps({"prefix": args.list_prefix, "matches": matches}, indent=2))
        else:
            for name in matches:
                print(name)
        return

    if args.reverse:
        hits = reverse_lookup(tc_tree, args.reverse, max_depth=args.max_depth)
        if args.json:
            print(json.dumps({"target": args.reverse, "hits": [{"tc": n, "share": s} for n, s in hits]}, indent=2))
        else:
            print_reverse(args.reverse, hits, args.top)
        return

    if not args.tc:
        raise SystemExit("Provide one of: --tc, --reverse, or --list-prefix")

    if args.resolve:
        resolved = resolve_terminals(tc_tree, args.tc, max_depth=args.max_depth)
        if args.json:
            print(json.dumps({"tc": args.tc, "resolved": resolved}, indent=2))
        else:
            print_resolved(args.tc, resolved, args.top)
        return

    summary = immediate_summary(tc_tree, args.tc)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_summary(summary)


if __name__ == "__main__":
    main()
