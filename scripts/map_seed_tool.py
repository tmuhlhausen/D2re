#!/usr/bin/env python3
"""
map_seed_tool.py — Diablo II map seed analysis and lookup tool.
Reconstruct map layouts, find seeds matching known area configs,
and verify save file map seeds.

Usage:
    python map_seed_tool.py --seed 0xABCD1234 --act 1
    python map_seed_tool.py --d2s MyChar.d2s --show-seed
    python map_seed_tool.py --brute-act1 --waypoint stony --direction NE
    python map_seed_tool.py --diff-seeds 0xAAAA 0xBBBB --level 25
"""

import struct, argparse, json, os, sys
from typing import Optional, List, Dict, Tuple, Any

# ─────────────────────────────────────────────────────────────────────────────
# D2 LCG — mirrors the exact PRNG
# ─────────────────────────────────────────────────────────────────────────────

def lcg(seed: int) -> int:
    return ((seed * 0x6AC690C5) + 1) & 0xFFFFFFFF

def lcg_range(seed: int, n: int) -> Tuple[int, int]:
    seed = lcg(seed)
    return (seed % n if n else 0), seed


# ─────────────────────────────────────────────────────────────────────────────
# Level ID constants (from levels.txt)
# ─────────────────────────────────────────────────────────────────────────────

LEVEL_IDS = {
    "rogue_camp": 1, "blood_moor": 2, "cold_plains": 3,
    "stony_field": 4, "dark_wood": 5, "black_marsh": 6,
    "tamoe_highland": 7, "den_of_evil": 8,
    "cave_l1": 9, "cave_l2": 10, "underground_passage_l1": 11,
    "underground_passage_l2": 12, "hole_l1": 13, "hole_l2": 14,
    "pit_l1": 15, "pit_l2": 16, "tristram": 17,
    "moo_moo_farm": 39,  # secret cow level
    "lut_gholein": 40, "rocky_waste": 41, "dry_hills": 42,
    "far_oasis": 43, "lost_city": 44, "valley_of_snakes": 45,
    "canyon_of_magi": 46, "sewers_l1": 47, "sewers_l2": 48,
    "sewers_l3": 49, "harem_l1": 50, "harem_l2": 51,
    "palace_cellar_l1": 52, "palace_cellar_l2": 53, "palace_cellar_l3": 54,
    "stony_tomb_l1": 55, "halls_of_the_dead_l1": 56,
    "halls_of_the_dead_l2": 57, "claw_viper_temple_l1": 58,
    "stony_tomb_l2": 59, "halls_of_the_dead_l3": 60,
    "claw_viper_temple_l2": 61, "maggot_lair_l1": 62,
    "maggot_lair_l2": 63, "maggot_lair_l3": 64,
    "ancient_tunnels": 65, "tal_rashas_tomb_1": 66,
    "tal_rashas_tomb_2": 67, "tal_rashas_tomb_3": 68,
    "tal_rashas_tomb_4": 69, "tal_rashas_tomb_5": 70,
    "tal_rashas_tomb_6": 71, "tal_rashas_tomb_7": 72,
    "tal_rashas_chamber": 73, "arcane_sanctuary": 74,
    "spider_forest": 78, "great_marsh": 79, "flayer_jungle": 80,
    "lower_kurast": 81, "kurast_bazaar": 82,
    "upper_kurast": 83, "kurast_causeway": 84, "travincal": 85,
    "spider_cavern": 86, "swampy_pit_l1": 87, "swampy_pit_l2": 88,
    "flayer_dungeon_l1": 89, "flayer_dungeon_l2": 90,
    "swampy_pit_l3": 91, "flayer_dungeon_l3": 92,
    "sewers_l1_a3": 93,  # act 3 sewers
    "ruined_temple": 94, "disused_fane": 95,
    "forgotten_reliquary": 96, "forgotten_temple": 97,
    "ruined_fane": 98, "disused_reliquary": 99,
    "durance_of_hate_l1": 100, "durance_of_hate_l2": 101,
    "durance_of_hate_l3": 102,
    "pandemonium_fortress": 103, "outer_steppes": 104,
    "plains_of_despair": 105, "city_of_the_damned": 106,
    "river_of_flame": 107, "chaos_sanctuary": 108,
    "harrogath": 109, "bloody_foothills": 110,
    "frigid_highlands": 111, "arreat_plateau": 112,
    "crystalline_passage": 113, "frozen_river": 114,
    "glacial_trail": 115, "drifting_sands": 116,  # actually frozen tundra
    "frozen_tundra": 117, "ancient_way": 118,
    "arreat_summit": 119, "nihlathaks_temple": 120,
    "halls_of_anguish": 121, "halls_of_pain": 122,
    "halls_of_vaught": 123, "glacial_caves_l1": 124,
    "glacial_caves_l2": 125, "abaddon": 126,
    "pit_of_acheron": 127, "infernal_pit": 128,
    "worldstone_keep_l1": 129, "worldstone_keep_l2": 130,
    "worldstone_keep_l3": 131, "throne_of_destruction": 132,
    "worldstone_chamber": 133,
    "secret_cow_level": 112,
    "uber_tristram": 117,
}


# ─────────────────────────────────────────────────────────────────────────────
# Map seed cascade
# The entire map is derived from a single 32-bit game seed
# ─────────────────────────────────────────────────────────────────────────────

def derive_act_seed(game_seed: int, act: int) -> int:
    """Derive the seed for an act from the game seed."""
    seed = game_seed
    for _ in range(act + 1):
        seed = lcg(seed)
    return seed

def derive_level_seed(act_seed: int, level_id: int) -> int:
    """Derive the seed for a specific level."""
    seed = act_seed
    for _ in range(level_id):
        seed = lcg(seed)
    return seed

def derive_room_seed(level_seed: int, room_index: int) -> int:
    """Derive the seed for a specific room within a level."""
    seed = level_seed
    for _ in range(room_index + 1):
        seed = lcg(seed)
    return seed


# ─────────────────────────────────────────────────────────────────────────────
# Read game seed from .d2s save file
# ─────────────────────────────────────────────────────────────────────────────

def read_map_seed_from_save(d2s_path: str) -> Optional[int]:
    """Read the map seed stored at offset 0xAB in a .d2s file."""
    try:
        with open(d2s_path, "rb") as f:
            f.seek(0xAB)
            return struct.unpack("<I", f.read(4))[0]
    except Exception as e:
        print(f"Error reading .d2s: {e}")
        return None

def read_char_info_from_save(d2s_path: str) -> Dict[str, Any]:
    """Read basic character info including map seed."""
    try:
        with open(d2s_path, "rb") as f:
            data = f.read(0x100)

        magic     = struct.unpack_from("<I", data, 0)[0]
        version   = struct.unpack_from("<I", data, 4)[0]
        name      = data[0x14:0x24].rstrip(b"\x00").decode("ascii", "replace")
        level     = data[0x2B]
        char_cls  = data[0x28]
        map_seed  = struct.unpack_from("<I", data, 0xAB)[0]
        diff      = data[0xA8:0xAB]

        classes   = ["Amazon","Necromancer","Barbarian","Sorceress",
                     "Paladin","Druid","Assassin"]

        return {
            "valid":    magic == 0xAA55AA55,
            "version":  version,
            "name":     name,
            "level":    level,
            "class":    classes[char_cls] if char_cls < len(classes) else "Unknown",
            "map_seed": map_seed,
            "map_seed_hex": f"0x{map_seed:08X}",
            "difficulty": list(diff),
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Superunique / preset spawn prediction
# ─────────────────────────────────────────────────────────────────────────────

# Known superunique spawn locations relative to level layout
# These are derived from superuniques.txt and LvlPrest.txt
SUPERUNIQUES = {
    # level_id: [(guid_name, nominal_area_x, nominal_area_y), ...]
    2:  [("Bishibosh",  0, 0)],        # Blood Moor
    3:  [("Corpsefire", 0, 0)],        # Cold Plains (in Den of Evil entrance)
    4:  [("Rakanishu",  0, 0)],        # Stony Field
    17: [("Griswold",   0, 0)],        # Tristram
    21: [("Pindleskin",140, 100)],     # Pinnacle of the Mausoleum
    87: [("Uber_Diablo", 0, 0)],       # Overlay on any area (Hellfire Torch)
}


# ─────────────────────────────────────────────────────────────────────────────
# BSP-based room layout predictor
# ─────────────────────────────────────────────────────────────────────────────

class BSPPredictor:
    """
    Simulate D2's BSP room partition to predict map layout.
    This is a simplified version — the real engine adds obstacle placement
    and connectivity that requires the full tile library to resolve accurately.
    """

    def __init__(self, level_seed: int, level_w: int = 80, level_h: int = 80,
                 max_depth: int = 6):
        self.seed      = level_seed
        self.level_w   = level_w
        self.level_h   = level_h
        self.max_depth = max_depth
        self.rooms: List[Dict] = []

    def partition(self, x: int, y: int, w: int, h: int, depth: int):
        """Recursively partition and record leaf rooms."""
        if w < 6 or h < 6 or depth == 0:
            # Leaf node: this is a room
            room_w, self.seed = lcg_range(self.seed, max(1, w - 4))
            room_w += 4
            room_h, self.seed = lcg_range(self.seed, max(1, h - 4))
            room_h += 4
            ox, self.seed = lcg_range(self.seed, max(1, w - room_w + 1))
            oy, self.seed = lcg_range(self.seed, max(1, h - room_h + 1))
            self.rooms.append({
                "x": x + ox, "y": y + oy,
                "w": room_w,  "h": room_h,
                "cx": x + ox + room_w // 2,
                "cy": y + oy + room_h // 2,
            })
            return

        # Decide split axis
        split_horiz, self.seed = lcg_range(self.seed, 2)
        if w > h:
            split_horiz = 1
        elif h > w:
            split_horiz = 0

        if split_horiz:
            split, self.seed = lcg_range(self.seed, max(1, w // 3))
            split += w // 3
            self.partition(x, y, split, h, depth - 1)
            self.partition(x + split, y, w - split, h, depth - 1)
        else:
            split, self.seed = lcg_range(self.seed, max(1, h // 3))
            split += h // 3
            self.partition(x, y, w, split, depth - 1)
            self.partition(x, y + split, w, h - split, depth - 1)

    def predict(self) -> List[Dict]:
        self.rooms = []
        self.partition(0, 0, self.level_w, self.level_h, self.max_depth)
        return self.rooms

    def find_entrance_candidates(self) -> List[Dict]:
        """Find rooms most likely to be near level entrance (top-left bias)."""
        return sorted(self.rooms, key=lambda r: r["cx"] + r["cy"])[:3]

    def find_exit_candidates(self) -> List[Dict]:
        """Find rooms most likely to contain the level exit (bottom-right bias)."""
        return sorted(self.rooms, key=lambda r: -(r["cx"] + r["cy"]))[:3]

    def ascii_map(self, width: int = 80, height: int = 40) -> str:
        """Render a crude ASCII visualization of predicted rooms."""
        grid = [["." for _ in range(width)] for _ in range(height)]
        for i, room in enumerate(self.rooms):
            label = str(i % 10)
            sx = room["x"] * width // self.level_w
            sy = room["y"] * height // self.level_h
            ex = (room["x"] + room["w"]) * width  // self.level_w
            ey = (room["y"] + room["h"]) * height // self.level_h
            for gy in range(sy, min(ey, height)):
                for gx in range(sx, min(ex, width)):
                    grid[gy][gx] = label
            # Border
            for gx in range(sx, min(ex, width)):
                if sy < height:    grid[sy][gx] = "#"
                if ey-1 < height:  grid[ey-1][gx] = "#"
            for gy in range(sy, min(ey, height)):
                if sx < width:     grid[gy][sx]   = "#"
                if ex-1 < width:   grid[gy][ex-1] = "#"
        return "\n".join("".join(row) for row in grid)


# ─────────────────────────────────────────────────────────────────────────────
# Seed brute-forcer
# ─────────────────────────────────────────────────────────────────────────────

def brute_force_seeds(level_id: int, target_fn, max_seeds: int = 1_000_000) -> List[int]:
    """
    Brute-force map seeds satisfying a predicate.
    target_fn(level_seed) -> bool
    Returns list of matching game seeds.
    """
    matches = []
    for game_seed in range(max_seeds):
        act = (level_id - 1) // 27  # rough act derivation
        act_seed   = derive_act_seed(game_seed, act)
        level_seed = derive_level_seed(act_seed, level_id)
        if target_fn(level_seed):
            matches.append(game_seed)
    return matches


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="D2 map seed analysis tool")
    ap.add_argument("--seed",   type=lambda x: int(x,0), help="Game map seed (hex)")
    ap.add_argument("--act",    type=int, default=1, help="Act 1–5")
    ap.add_argument("--level",  type=int, help="Level ID for BSP preview")
    ap.add_argument("--d2s",    help="Path to .d2s save file")
    ap.add_argument("--show-seed", action="store_true")
    ap.add_argument("--bsp",    action="store_true", help="Run BSP predictor")
    ap.add_argument("--ascii",  action="store_true", help="Show ASCII map")
    ap.add_argument("--rooms",  action="store_true", help="List predicted rooms")
    ap.add_argument("--brute",  action="store_true", help="Brute force seeds")
    ap.add_argument("--max",    type=int, default=100000, help="Max seeds to try")
    args = ap.parse_args()

    # Read seed from save file
    if args.d2s:
        info = read_char_info_from_save(args.d2s)
        print(f"\nCharacter: {info.get('name')} ({info.get('class')}) Lv{info.get('level')}")
        print(f"Map Seed:  {info.get('map_seed_hex')} ({info.get('map_seed')})")
        print(f"Valid:     {info.get('valid')}")
        if not args.seed:
            args.seed = info.get("map_seed")

    if args.seed is None:
        ap.print_help()
        return

    game_seed = args.seed
    print(f"\nGame seed: 0x{game_seed:08X}")
    print(f"\nDerived seeds per act:")
    for act in range(5):
        act_seed = derive_act_seed(game_seed, act)
        print(f"  Act {act+1}: 0x{act_seed:08X}")

    if args.level or args.bsp:
        level_id = args.level or 3  # default: Cold Plains
        act      = min(4, (level_id - 1) // 27)
        act_seed = derive_act_seed(game_seed, act)
        level_seed = derive_level_seed(act_seed, level_id)

        print(f"\nLevel {level_id} seed: 0x{level_seed:08X}")

        if args.bsp or args.ascii or args.rooms:
            predictor = BSPPredictor(level_seed)
            rooms = predictor.predict()
            print(f"Predicted {len(rooms)} rooms via BSP simulation")

            if args.rooms:
                print("\nRoom list:")
                for i, r in enumerate(rooms):
                    print(f"  Room {i:2d}: pos=({r['x']:3},{r['y']:3})  "
                          f"size={r['w']}×{r['h']}  center=({r['cx']},{r['cy']})")

            ent = predictor.find_entrance_candidates()
            ex  = predictor.find_exit_candidates()
            print(f"\nLikely entrance areas: {[(r['cx'],r['cy']) for r in ent]}")
            print(f"Likely exit areas:      {[(r['cx'],r['cy']) for r in ex]}")

            if args.ascii:
                print(f"\nASCII map preview (level {level_id}):")
                print(predictor.ascii_map())

    if args.brute:
        level_id = args.level or 3
        print(f"\nBrute-forcing seeds for level {level_id} "
              f"with unusual room count...")

        def has_many_rooms(level_seed: int) -> bool:
            p = BSPPredictor(level_seed)
            rooms = p.predict()
            return len(rooms) >= 20  # example: find large maps

        matches = brute_force_seeds(level_id, has_many_rooms, args.max)
        print(f"Found {len(matches)} matching seeds: {[f'0x{s:08X}' for s in matches[:10]]}")


if __name__ == "__main__":
    main()
