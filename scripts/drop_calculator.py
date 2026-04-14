#!/usr/bin/env python3
"""
drop_calculator.py — Monte Carlo drop estimator for Diablo II treasure classes.

Examples:
    python scripts/drop_calculator.py --tc "Act 5 Super C" --runs 100000
    python scripts/drop_calculator.py --tc "Act 5 Super C" --item armo87 --runs 250000
    python scripts/drop_calculator.py --tc "Mephisto (N)" --item weap87 --top 15 --json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
from collections import Counter
from typing import Any, Dict

from tools.item_roller_impl import DropSimulator

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data_tables")
DEFAULT_TC_TREE = os.path.join(DATA_DIR, "tc_tree.json")


def load_tc_tree(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Treasure class tree not found at {path}. "
            "Generate it first with: python scripts/mpq_extract.py --all-mpqs <D2 dir> --tc-tree"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def runs_for_confidence(p: float, confidence: float) -> int | None:
    """Return runs needed for at least one success at the requested confidence."""
    if p <= 0:
        return None
    if p >= 1:
        return 1
    return math.ceil(math.log(1 - confidence) / math.log(1 - p))


def simulate(tc_tree: Dict[str, Any], tc_name: str, runs: int, seed: int | None = None) -> Dict[str, Any]:
    sim = DropSimulator(tc_tree)
    if seed is not None:
        sim._rng.seed(seed)
    counts: Counter[str] = Counter()
    nodrop = 0
    for _ in range(runs):
        item = sim.resolve_tc(tc_name)
        if item is None:
            nodrop += 1
        else:
            counts[item] += 1
    return {
        "runs": runs,
        "nodrop_count": nodrop,
        "drop_counts": dict(counts.most_common()),
    }


def print_top(result: Dict[str, Any], top: int) -> None:
    runs = result["runs"]
    nodrop_count = result["nodrop_count"]
    print(f"Runs:        {runs}")
    print(f"NoDrop:      {nodrop_count} ({(nodrop_count / runs) * 100:.3f}%)")
    print()
    print("Top observed items:")
    for item, count in list(result["drop_counts"].items())[:top]:
        pct = (count / runs) * 100
        print(f"  {item:<24} {count:>8}  ({pct:>7.4f}%)")


def print_target(item: str, result: Dict[str, Any]) -> None:
    runs = result["runs"]
    count = result["drop_counts"].get(item, 0)
    p = count / runs if runs else 0.0
    print(f"Target item: {item}")
    print(f"Observed:    {count} / {runs}")
    print(f"Per-run p:   {p:.8f}")
    if p <= 0:
        print("Confidence runs: target was not observed in the simulation.")
        return
    for conf in (0.50, 0.90, 0.99):
        needed = runs_for_confidence(p, conf)
        print(f"Runs for {int(conf * 100)}% confidence: {needed}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Monte Carlo drop estimator for Diablo II treasure classes")
    ap.add_argument("--tree", default=DEFAULT_TC_TREE, help="Path to tc_tree.json")
    ap.add_argument("--tc", required=True, help="Treasure class name to simulate")
    ap.add_argument("--item", help="Optional item code to analyze specifically")
    ap.add_argument("--runs", type=int, default=100000, help="Number of simulated drops")
    ap.add_argument("--seed", type=int, help="Optional RNG seed for reproducible simulations")
    ap.add_argument("--top", type=int, default=20, help="Number of top rows to print")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of plain text")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    tc_tree = load_tc_tree(args.tree)
    result = simulate(tc_tree, args.tc, args.runs, seed=args.seed)
    result["tc"] = args.tc

    if args.item:
        count = result["drop_counts"].get(args.item, 0)
        p = count / args.runs if args.runs else 0.0
        result["target"] = {
            "item": args.item,
            "count": count,
            "probability": p,
            "runs_for_50": runs_for_confidence(p, 0.50),
            "runs_for_90": runs_for_confidence(p, 0.90),
            "runs_for_99": runs_for_confidence(p, 0.99),
        }

    if args.json:
        top_counts = dict(list(result["drop_counts"].items())[: args.top])
        payload = dict(result)
        payload["drop_counts"] = top_counts
        print(json.dumps(payload, indent=2))
        return

    print_top(result, args.top)
    if args.item:
        print()
        print_target(args.item, result)


if __name__ == "__main__":
    main()
