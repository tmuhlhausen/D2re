#!/usr/bin/env python3
"""
item_roller.py — Simulate Diablo II item generation from seeds.
Reproduces the server-side item gen pipeline to predict affix outcomes.
Requires extracted data tables (run mpq_extract.py first).

Usage:
    python item_roller.py --seed 0xDEADBEEF --base swrd --ilvl 80 --mf 300
    python item_roller.py --brute --base phase --ilvl 87 --target "Breath of the Dying"
    python item_roller.py --tc "Wraith TC84" --mlvl 85 --mf 400 --runs 100000
"""

import argparse, json, os, random
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────────────────────
# LCG — mirrors D2's actual PRNG (verified from RE)
# ─────────────────────────────────────────────────────────────────────────────

def lcg_next(seed: int) -> int:
    """D2 Linear Congruential Generator — D2Common.dll+0x1B1A0 (v1.13c)."""
    return ((seed * 0x6AC690C5) + 1) & 0xFFFFFFFF

def lcg_range(seed: int, max_val: int) -> Tuple[int, int]:
    """Return (result, new_seed). Result in [0, max_val)."""
    seed = lcg_next(seed)
    if max_val == 0:
        return 0, seed
    return seed % max_val, seed

# ─────────────────────────────────────────────────────────────────────────────
# Data loader
# ─────────────────────────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data_tables")

def load_table(name: str) -> List[Dict[str, str]]:
    """Load a CSV data table."""
    import csv
    path = os.path.join(DATA_DIR, f"{name}.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ─────────────────────────────────────────────────────────────────────────────
# Quality determination
# ─────────────────────────────────────────────────────────────────────────────

ITEM_QUAL_INFERIOR  = 1
ITEM_QUAL_NORMAL    = 2
ITEM_QUAL_SUPERIOR  = 3
ITEM_QUAL_MAGIC     = 4
ITEM_QUAL_SET       = 5
ITEM_QUAL_RARE      = 6
ITEM_QUAL_UNIQUE    = 7
ITEM_QUAL_CRAFT     = 8

QUAL_NAMES = {
    1: "Inferior", 2: "Normal", 3: "Superior", 4: "Magic",
    5: "Set", 6: "Rare", 7: "Unique", 8: "Crafted"
}

def effective_mf(raw_mf: int, quality: int) -> int:
    """Apply diminishing returns to MF% for high-tier quality checks."""
    if quality == ITEM_QUAL_UNIQUE:
        return (raw_mf * 250) // (raw_mf + 250)
    elif quality == ITEM_QUAL_SET:
        return (raw_mf * 500) // (raw_mf + 500)
    elif quality == ITEM_QUAL_RARE:
        return (raw_mf * 600) // (raw_mf + 600)
    return raw_mf

def determine_quality(seed: int, ilvl: int, raw_mf: int,
                       unique_ratio: int = 1200, set_ratio: int = 800,
                       rare_ratio: int = 600, magic_ratio: int = 200) -> Tuple[int, int]:
    """
    Determine item quality using D2's cascading roll system.
    Returns (quality, new_seed).

    Ratios are per-item from items.txt columns:
      unique_ratio = 1024 / (1 + chance_for_unique)
    """
    # Unique check
    eff_mf = effective_mf(raw_mf, ITEM_QUAL_UNIQUE)
    threshold = unique_ratio * (eff_mf + 250) // 1024
    roll, seed = lcg_range(seed, 1024)
    if roll < threshold:
        return ITEM_QUAL_UNIQUE, seed

    # Set check
    eff_mf = effective_mf(raw_mf, ITEM_QUAL_SET)
    threshold = set_ratio * (eff_mf + 500) // 1024
    roll, seed = lcg_range(seed, 1024)
    if roll < threshold:
        return ITEM_QUAL_SET, seed

    # Rare check
    eff_mf = effective_mf(raw_mf, ITEM_QUAL_RARE)
    threshold = rare_ratio * (eff_mf + 600) // 1024
    roll, seed = lcg_range(seed, 1024)
    if roll < threshold:
        return ITEM_QUAL_RARE, seed

    # Magic check
    threshold = magic_ratio * (raw_mf + 1) // 1024
    roll, seed = lcg_range(seed, 1024)
    if roll < threshold:
        return ITEM_QUAL_MAGIC, seed

    # Superior check (10% of remaining)
    roll, seed = lcg_range(seed, 100)
    if roll < 10:
        return ITEM_QUAL_SUPERIOR, seed

    return ITEM_QUAL_NORMAL, seed


# ─────────────────────────────────────────────────────────────────────────────
# Magic affix rolling
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AffixRoll:
    quality: int
    quality_name: str
    prefix_id: int
    prefix_name: str
    suffix_id: int
    suffix_name: str
    ilvl: int
    seed_used: int

def roll_magic_affixes(seed: int, ilvl: int,
                        prefixes: List[Dict], suffixes: List[Dict]) -> AffixRoll:
    """Roll magic item affixes for a given iLvl."""

    # Filter eligible affixes by level
    elig_pre = [p for p in prefixes if p.get("Name") and
                int(p.get("level", "0") or "0") <= ilvl]
    elig_suf = [s for s in suffixes if s.get("Name") and
                int(s.get("level", "0") or "0") <= ilvl]

    prefix_id = prefix_name = 0
    suffix_id = suffix_name = 0

    # 50% chance for prefix (but at least one affix required)
    roll, seed = lcg_range(seed, 2)
    if roll == 0 and elig_pre:
        idx, seed = lcg_range(seed, len(elig_pre))
        prefix_id   = idx
        prefix_name = elig_pre[idx].get("Name", "")

    # 50% chance for suffix (unless no prefix was rolled)
    roll, seed = lcg_range(seed, 2)
    if (roll == 0 or not prefix_name) and elig_suf:
        idx, seed = lcg_range(seed, len(elig_suf))
        suffix_id   = idx
        suffix_name = elig_suf[idx].get("Name", "")

    return AffixRoll(
        quality=ITEM_QUAL_MAGIC, quality_name="Magic",
        prefix_id=prefix_id, prefix_name=prefix_name,
        suffix_id=suffix_id, suffix_name=suffix_name,
        ilvl=ilvl, seed_used=seed
    )


# ─────────────────────────────────────────────────────────────────────────────
# Item level calculations
# ─────────────────────────────────────────────────────────────────────────────

def calc_monster_ilvl(mlvl: int, alvl: int, is_boss: bool = False,
                       is_champion: bool = False) -> int:
    """Calculate item level for a monster drop."""
    mlvl_adj = mlvl
    if is_boss:     mlvl_adj += 3
    if is_champion: mlvl_adj += 2
    return min(mlvl_adj, alvl * 2)

def calc_gambling_ilvl(clvl: int) -> Tuple[int, int]:
    """Return (min_ilvl, max_ilvl) for gambling at a given character level."""
    return max(1, clvl - 5), min(99, clvl + 4)

def calc_crafting_ilvl(clvl: int, ingredient_ilvl: int) -> int:
    """Calculate iLvl for a crafted item."""
    return min(99, clvl // 2 + ingredient_ilvl // 2)


# ─────────────────────────────────────────────────────────────────────────────
# TC resolution (simplified drop simulator)
# ─────────────────────────────────────────────────────────────────────────────

class DropSimulator:
    """Simulate monster drops from a Treasure Class."""

    def __init__(self, tc_tree: Dict[str, Any]):
        self.tc_tree = tc_tree
        self._rng = random.Random()

    def resolve_tc(self, tc_name: str, depth: int = 0) -> Optional[str]:
        """Recursively resolve a TC to a final item code."""
        if depth > 20:
            return None  # prevent infinite loops

        if tc_name not in self.tc_tree:
            return tc_name  # base item code

        node = self.tc_tree[tc_name]
        entries = node["entries"]
        nodrop  = node["nodrop"]

        total = nodrop + sum(e["prob"] for e in entries)
        roll  = self._rng.randint(0, total - 1)

        if roll < nodrop:
            return None  # NoDrop

        roll -= nodrop
        for entry in entries:
            if roll < entry["prob"]:
                return self.resolve_tc(entry["item"], depth + 1)
            roll -= entry["prob"]

        return None

    def simulate_drops(self, tc_name: str, runs: int,
                        mf: int = 0) -> Dict[str, int]:
        """Run N simulations and count item code frequencies."""
        counts: Dict[str, int] = {}
        for _ in range(runs):
            item = self.resolve_tc(tc_name)
            if item:
                counts[item] = counts.get(item, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="D2 item generation simulator")
    ap.add_argument("--seed",   type=lambda x: int(x, 0), help="Item seed (hex or dec)")
    ap.add_argument("--base",   help="Base item code (e.g. 'swrd', '7cf')")
    ap.add_argument("--ilvl",   type=int, default=80)
    ap.add_argument("--mf",     type=int, default=0, help="Magic Find percent")
    ap.add_argument("--mlvl",   type=int, default=85, help="Monster level")
    ap.add_argument("--alvl",   type=int, default=85, help="Area level")
    ap.add_argument("--tc",     help="Treasure class name to simulate")
    ap.add_argument("--runs",   type=int, default=10000)
    ap.add_argument("--brute",  action="store_true", help="Disabled: planned brute-force seed search")
    ap.add_argument("--target", help="Disabled: planned target item for brute-force search")
    ap.add_argument("--affix",  action="store_true", help="Roll magic affixes")
    args = ap.parse_args()

    if args.brute or args.target:
        print("item_roller: brute-force seed search is temporarily disabled.")
        print("The flags are kept in place so the feature can be implemented incrementally.")
        print("Use --seed, --base, --tc, --runs, and --affix for currently supported workflows.")
        return 2

    # Treasure class simulation
    if args.tc:
        tc_path = os.path.join(DATA_DIR, "tc_tree.json")
        if not os.path.exists(tc_path):
            print(f"TC tree not found at {tc_path}. Run mpq_extract.py --tc-tree first.")
            return 1
        with open(tc_path) as f:
            tc_tree = json.load(f)
        sim = DropSimulator(tc_tree)
        print(f"Simulating {args.runs} drops from TC: {args.tc}")
        results = sim.simulate_drops(args.tc, args.runs, args.mf)
        print(f"\nTop 20 results:")
        for code, count in list(results.items())[:20]:
            pct = count * 100.0 / args.runs
            bar = "█" * int(pct / 2)
            print(f"  {code:6}  {count:6}  ({pct:5.2f}%)  {bar}")
        return 0

    # Single seed quality roll
    if args.seed is not None:
        seed = args.seed
        ilvl = args.ilvl
        mf   = args.mf
        quality, new_seed = determine_quality(seed, ilvl, mf)
        print(f"\nSeed:    0x{seed:08X}")
        print(f"iLvl:    {ilvl}")
        print(f"MF:      {mf}%  (eff. {effective_mf(mf, quality)}%)")
        print(f"Quality: {QUAL_NAMES[quality]}")
        print(f"New seed after roll: 0x{new_seed:08X}")

        if args.affix and quality == ITEM_QUAL_MAGIC:
            prefixes = load_table("magicprefix")
            suffixes = load_table("magicsuffix")
            if prefixes or suffixes:
                roll = roll_magic_affixes(new_seed, ilvl, prefixes, suffixes)
                print(f"\nMagic Affixes:")
                print(f"  Prefix: {roll.prefix_name or '(none)'}")
                print(f"  Suffix: {roll.suffix_name or '(none)'}")
        return 0

    # Quick simulation: roll N random seeds and tally quality distribution
    if args.base:
        print(f"\nSimulating {args.runs} drops for base '{args.base}' "
              f"(ilvl={args.ilvl}, MF={args.mf}%)")
        tally = {q: 0 for q in range(1, 9)}
        for _ in range(args.runs):
            seed = random.randint(0, 0xFFFFFFFF)
            q, _ = determine_quality(seed, args.ilvl, args.mf)
            tally[q] = tally.get(q, 0) + 1

        print(f"\nQuality distribution over {args.runs} runs:")
        for q in range(7, 0, -1):
            count = tally.get(q, 0)
            pct   = count * 100.0 / args.runs
            bar   = "█" * max(1, int(pct))
            if count > 0:
                print(f"  {QUAL_NAMES[q]:10} {count:6}  ({pct:6.3f}%)  {bar}")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
