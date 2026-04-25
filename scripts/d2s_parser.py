#!/usr/bin/env python3
"""
d2s_parser.py — Full Diablo II .d2s save file parser
Handles v1.10–v1.14d format (version 96 / 0x60)

Usage:
    python d2s_parser.py <path/to/char.d2s>
    python d2s_parser.py <path/to/char.d2s> --json
    python d2s_parser.py <path/to/char.d2s> --items
"""

import struct, sys, json, argparse
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

# ─────────────────────────────────────────────────────────────────────────────
# Bit reader (D2 uses LSB-first bit packing throughout save files)
# ─────────────────────────────────────────────────────────────────────────────

class BitReader:
    def __init__(self, data: bytes, bit_offset: int = 0):
        self.data = data
        self.pos  = bit_offset  # current bit position

    def read(self, n: int) -> int:
        """Read n bits, LSB first."""
        val = 0
        for i in range(n):
            byte_idx = self.pos >> 3
            bit_idx  = self.pos & 7
            if byte_idx >= len(self.data):
                raise EOFError(f"BitReader: out of data at bit {self.pos}")
            val |= ((self.data[byte_idx] >> bit_idx) & 1) << i
            self.pos += 1
        return val

    def read_str(self, n_chars: int, bits_per_char: int = 7) -> str:
        """Read a packed character string."""
        chars = []
        for _ in range(n_chars):
            c = self.read(bits_per_char)
            if c == 0: break
            chars.append(chr(c))
        return "".join(chars)

    @property
    def byte_pos(self) -> int:
        return self.pos >> 3

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

CHAR_CLASSES = ["Amazon", "Necromancer", "Barbarian", "Sorceress",
                "Paladin", "Druid", "Assassin"]

ITEM_QUALITIES = {
    1: "Inferior", 2: "Normal", 3: "Superior", 4: "Magic",
    5: "Set", 6: "Rare", 7: "Unique", 8: "Crafted"
}

BODY_LOCS = {
    0: "None", 1: "Head", 2: "Neck", 3: "Torso",
    4: "RHand", 5: "LHand", 6: "RRing", 7: "LRing",
    8: "Belt", 9: "Feet", 10: "Gloves", 11: "RHand2", 12: "LHand2"
}

STORE_LOCS = {0: "None", 1: "Inventory", 2: "Belt", 3: "?", 4: "Cube", 5: "Stash"}

# CSvBits from itemstatcost.txt — bit widths for each stat
STAT_BITS: Dict[int, int] = {
    0: 10, 1: 10, 2: 10, 3: 10,    # str/ene/dex/vit
    4: 10, 5: 8,                     # stat pts / skill pts
    6: 21, 7: 21,                    # hp/maxhp
    8: 21, 9: 21,                    # mana/maxmana
    10: 21, 11: 21,                  # stamina/maxstamina
    12: 7,                           # level
    13: 32,                          # experience
    14: 25,                          # gold
    15: 25,                          # stash gold
}

STAT_NAMES: Dict[int, str] = {
    0: "Strength", 1: "Energy", 2: "Dexterity", 3: "Vitality",
    4: "StatPoints", 5: "SkillPoints",
    6: "HP", 7: "MaxHP", 8: "Mana", 9: "MaxMana",
    10: "Stamina", 11: "MaxStamina",
    12: "Level", 13: "Experience", 14: "Gold", 15: "GoldBank",
}

# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class D2Header:
    magic: int
    version: int
    file_size: int
    checksum: int
    active_slot: int
    name: str
    status: int
    progression: int
    char_class: int
    char_class_name: str
    level: int
    created: int
    last_played: int
    skill_hotkeys: List[int]
    left_skill: int
    right_skill: int
    left_skill_sw: int
    right_skill_sw: int
    difficulty: bytes
    map_seed: int
    merc_dead: int
    merc_guid: int
    merc_name_idx: int
    merc_type: int
    merc_xp: int

    @property
    def is_hardcore(self) -> bool:
        return bool(self.status & 0x04)

    @property
    def is_expansion(self) -> bool:
        return bool(self.status & 0x20)

    @property
    def is_dead(self) -> bool:
        return bool(self.status & 0x08)

@dataclass
class D2Item:
    identified: bool
    socketed: bool
    ethereal: bool
    personalized: bool
    runeword: bool
    is_ear: bool
    simple: bool
    location: int
    panel: int
    col: int
    row: int
    body_loc: int
    base_code: str
    num_sockets: int
    item_id: int
    ilvl: int
    quality: int
    quality_name: str
    magic_prefix: int = 0
    magic_suffix: int = 0
    rare_prefix: int = 0
    rare_suffix: int = 0
    set_id: int = 0
    unique_id: int = 0
    runeword_id: int = 0
    personalized_name: str = ""
    ear_player: str = ""
    ear_class: int = 0
    ear_level: int = 0
    stats: Dict[int, int] = field(default_factory=dict)
    socketed_items: List["D2Item"] = field(default_factory=list)

@dataclass
class D2Save:
    header: D2Header
    stats: Dict[str, Any]
    skills: List[int]          # 30 values
    items: List[D2Item]
    corpse_items: List[D2Item]
    merc_items: List[D2Item]
    waypoints: bytes
    quests: bytes

# ─────────────────────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────────────────────

class D2SaveParser:
    def __init__(self, path: str):
        with open(path, "rb") as f:
            self.data = f.read()
        self.offset = 0

    def u8(self) -> int:
        v = self.data[self.offset]; self.offset += 1; return v
    def u16(self) -> int:
        v = struct.unpack_from("<H", self.data, self.offset)[0]; self.offset += 2; return v
    def u32(self) -> int:
        v = struct.unpack_from("<I", self.data, self.offset)[0]; self.offset += 4; return v
    def bytes_n(self, n: int) -> bytes:
        v = self.data[self.offset:self.offset+n]; self.offset += n; return v
    def str_n(self, n: int) -> str:
        return self.bytes_n(n).rstrip(b"\x00").decode("ascii", errors="replace")

    def parse_header(self) -> D2Header:
        self.offset = 0
        magic       = self.u32()
        version     = self.u32()
        file_size   = self.u32()
        checksum    = self.u32()
        active_slot = self.u32()
        name        = self.str_n(16)
        status      = self.u8()
        progression = self.u8()
        self.bytes_n(2)  # unknown
        char_class  = self.u8()
        self.bytes_n(2)  # 0x1010
        level       = self.u8()
        created     = self.u32()
        last_played = self.u32()
        self.bytes_n(4)  # 0xFFFFFFFF
        hotkeys     = [self.u32() for _ in range(16)]
        left_skill  = self.u32()
        right_skill = self.u32()
        left_sw     = self.u32()
        right_sw    = self.u32()
        self.bytes_n(32) # appearance
        difficulty  = self.bytes_n(3)
        map_seed    = self.u32()
        merc_dead   = self.u16()
        merc_guid   = self.u32()
        merc_name   = self.u16()
        merc_type   = self.u16()
        merc_xp     = self.u32()
        self.bytes_n(144) # padding

        return D2Header(
            magic=magic, version=version, file_size=file_size, checksum=checksum,
            active_slot=active_slot, name=name, status=status, progression=progression,
            char_class=char_class,
            char_class_name=CHAR_CLASSES[char_class] if char_class < len(CHAR_CLASSES) else "Unknown",
            level=level, created=created, last_played=last_played,
            skill_hotkeys=hotkeys, left_skill=left_skill, right_skill=right_skill,
            left_skill_sw=left_sw, right_skill_sw=right_sw,
            difficulty=difficulty, map_seed=map_seed, merc_dead=merc_dead,
            merc_guid=merc_guid, merc_name_idx=merc_name, merc_type=merc_type,
            merc_xp=merc_xp
        )

    def find_section(self, magic: bytes) -> int:
        """Find a section by its magic bytes."""
        idx = self.data.find(magic)
        if idx == -1:
            raise ValueError(f"Section {magic!r} not found")
        return idx

    def parse_quests(self) -> bytes:
        idx = self.find_section(b"Woo!")
        return self.data[idx:idx+298]

    def parse_waypoints(self) -> bytes:
        idx = self.find_section(b"WS\x00\x00")
        return self.data[idx:idx+83]

    def parse_stats(self) -> Dict[str, Any]:
        idx = self.find_section(b"gf")
        reader = BitReader(self.data, (idx + 2) * 8)
        result = {}
        while True:
            stat_id = reader.read(9)
            if stat_id == 0x1FF:
                break
            bits  = STAT_BITS.get(stat_id, 32)
            value = reader.read(bits)
            name  = STAT_NAMES.get(stat_id, f"stat_{stat_id}")
            # Convert fixed-point stats
            if stat_id in (6, 7, 8, 9, 10, 11):
                result[name] = value / 256.0
            else:
                result[name] = value
        return result

    def parse_skills(self) -> List[int]:
        idx = self.find_section(b"if")
        return list(self.data[idx+2:idx+32])

    def parse_items(self, offset: int) -> List[D2Item]:
        """Parse an item list starting at byte offset (after 'JM' magic)."""
        reader = BitReader(self.data, offset * 8)
        magic  = reader.read(16)
        if magic != 0x4D4A:
            return []
        count  = reader.read(16)
        items  = []
        for _ in range(count):
            item = self._parse_single_item(reader)
            if item:
                items.append(item)
        return items

    def _parse_single_item(self, r: BitReader) -> Optional[D2Item]:
        # JM header
        jm = r.read(16)
        if jm != 0x4D4A:
            return None

        r.read(4)                          # unknown
        identified  = bool(r.read(1))
        r.read(6)                          # unknown
        socketed    = bool(r.read(1))
        r.read(1)                          # unknown (new item flag)
        is_new      = bool(r.read(1))
        r.read(2)
        is_ear      = bool(r.read(1))
        starter     = bool(r.read(1))
        r.read(3)
        simple      = bool(r.read(1))
        ethereal    = bool(r.read(1))
        r.read(1)
        personalized = bool(r.read(1))
        r.read(1)
        runeword    = bool(r.read(1))
        r.read(5)

        version     = r.read(8)
        r.read(2)
        location    = r.read(3)
        panel       = r.read(4)
        col         = r.read(4)
        row         = r.read(4)
        body_loc    = r.read(4)

        # Base item code: 4 chars × 6 bits (custom A-Z0-9 + space encoding)
        base_code = ""
        for _ in range(4):
            c = r.read(6)
            # D2 uses offset 32 for printable ASCII
            base_code += chr(c + 32) if c + 32 < 128 else " "
        base_code = base_code.rstrip()

        if is_ear:
            ear_class = r.read(3)
            ear_level = r.read(7)
            ear_name  = r.read_str(16, 7)
            return D2Item(
                identified=True, socketed=False, ethereal=False,
                personalized=False, runeword=False, is_ear=True, simple=True,
                location=location, panel=panel, col=col, row=row,
                body_loc=body_loc, base_code="ear", num_sockets=0,
                item_id=0, ilvl=0, quality=2, quality_name="Normal",
                ear_player=ear_name, ear_class=ear_class, ear_level=ear_level
            )

        if simple:
            return D2Item(
                identified=identified, socketed=socketed, ethereal=ethereal,
                personalized=personalized, runeword=runeword, is_ear=False,
                simple=True, location=location, panel=panel, col=col, row=row,
                body_loc=body_loc, base_code=base_code, num_sockets=0,
                item_id=0, ilvl=0, quality=2, quality_name="Normal"
            )

        num_sockets = r.read(3)
        item_id     = r.read(32)
        ilvl        = r.read(7)
        quality     = r.read(4)

        has_multi_pic = bool(r.read(1))
        if has_multi_pic:
            r.read(3)

        has_class_affix = bool(r.read(1))
        if has_class_affix:
            r.read(11)

        # Quality-specific data
        magic_prefix = magic_suffix = 0
        rare_prefix = rare_suffix = 0
        set_id = unique_id = runeword_id = 0
        personalized_name = ""
        rare_affixes = []

        if quality == 1 or quality == 3:  # inferior/superior
            r.read(3)
        elif quality == 4:  # magic
            magic_prefix = r.read(11)
            magic_suffix = r.read(11)
        elif quality == 5:  # set
            set_id = r.read(12)
        elif quality == 6 or quality == 8:  # rare/craft
            rare_prefix = r.read(8)
            rare_suffix = r.read(8)
            for _ in range(6):
                present = r.read(1)
                if present:
                    rare_affixes.append(r.read(11))
        elif quality == 7:  # unique
            unique_id = r.read(12)

        if runeword:
            runeword_id = r.read(16)
            r.read(4)  # runeword padding

        if personalized:
            personalized_name = r.read_str(16, 7)

        # Tome of ID/TP: extra byte
        if base_code in ("ibk", "tbk"):
            r.read(5)

        # Stats section
        stats = {}
        if not simple:
            while True:
                sid = r.read(9)
                if sid == 0x1FF:
                    break
                # Get bit width from itemstatcost.txt (simplified subset)
                bits = STAT_BITS.get(sid, 32)
                stats[STAT_NAMES.get(sid, f"stat_{sid}")] = r.read(bits)

        item = D2Item(
            identified=identified, socketed=socketed, ethereal=ethereal,
            personalized=personalized, runeword=runeword, is_ear=False,
            simple=False, location=location, panel=panel, col=col, row=row,
            body_loc=body_loc, base_code=base_code, num_sockets=num_sockets,
            item_id=item_id, ilvl=ilvl, quality=quality,
            quality_name=ITEM_QUALITIES.get(quality, "Unknown"),
            magic_prefix=magic_prefix, magic_suffix=magic_suffix,
            rare_prefix=rare_prefix, rare_suffix=rare_suffix,
            set_id=set_id, unique_id=unique_id, runeword_id=runeword_id,
            personalized_name=personalized_name,
            stats=stats
        )

        # Parse socketed items
        for _ in range(num_sockets):
            sub = self._parse_single_item(r)
            if sub:
                item.socketed_items.append(sub)

        return item

    def parse(self) -> D2Save:
        header = self.parse_header()
        quests = self.parse_quests()
        wps    = self.parse_waypoints()
        stats  = self.parse_stats()
        skills = self.parse_skills()

        # Find main items section (JM after "if" skills)
        items_idx = self.find_section(b"JM")
        items = self.parse_items(items_idx)

        # Corpse and merc sections (subsequent JM blocks)
        try:
            corpse_idx = self.data.find(b"JM", items_idx + 2)
            corpse_items = self.parse_items(corpse_idx) if corpse_idx != -1 else []
        except:
            corpse_items = []

        try:
            merc_jf_idx = self.data.find(b"jf")
            merc_jm_idx = self.data.find(b"JM", merc_jf_idx) if merc_jf_idx != -1 else -1
            merc_items = self.parse_items(merc_jm_idx) if merc_jm_idx != -1 else []
        except:
            merc_items = []

        return D2Save(
            header=header, stats=stats, skills=skills,
            items=items, corpse_items=corpse_items, merc_items=merc_items,
            waypoints=wps, quests=quests
        )


# ─────────────────────────────────────────────────────────────────────────────
# Checksum verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_checksum(data: bytes) -> bool:
    stored = struct.unpack_from("<I", data, 0x0C)[0]
    patched = bytearray(data)
    patched[0x0C:0x10] = b"\x00\x00\x00\x00"
    computed = 0
    for b in patched:
        computed = ((computed << 1) | (computed >> 31)) & 0xFFFFFFFF
        computed = (computed + b) & 0xFFFFFFFF
    return computed == stored


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Diablo II .d2s save file parser")
    ap.add_argument("file", help="Path to .d2s file")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    ap.add_argument("--items", action="store_true", help="Show all items")
    ap.add_argument("--verify", action="store_true", help="Verify checksum only")
    args = ap.parse_args()

    with open(args.file, "rb") as f:
        raw = f.read()

    if args.verify:
        ok = verify_checksum(raw)
        print(f"Checksum: {'OK' if ok else 'INVALID'}")
        return

    parser = D2SaveParser(args.file)
    save   = parser.parse()
    h      = save.header

    if args.json:
        out = {
            "name": h.name,
            "class": h.char_class_name,
            "level": h.level,
            "hardcore": h.is_hardcore,
            "expansion": h.is_expansion,
            "map_seed": h.map_seed,
            "stats": save.stats,
            "item_count": len(save.items),
        }
        print(json.dumps(out, indent=2))
        return

    # Human-readable summary
    print(f"{'─'*50}")
    print(f"  Character: {h.name}")
    print(f"  Class:     {h.char_class_name}")
    print(f"  Level:     {h.level}")
    print(f"  Hardcore:  {'Yes' if h.is_hardcore else 'No'}")
    print(f"  Expansion: {'Yes' if h.is_expansion else 'No'}")
    print(f"  Map Seed:  0x{h.map_seed:08X}")
    print(f"  Checksum:  {'OK' if verify_checksum(raw) else '*** INVALID ***'}")
    print(f"{'─'*50}")
    print("  Stats:")
    for k, v in save.stats.items():
        display = f"{v:.1f}" if isinstance(v, float) else str(v)
        print(f"    {k:<16} {display}")
    print(f"{'─'*50}")
    print(f"  Items ({len(save.items)} total):")
    if args.items or True:
        for item in save.items[:30]:
            loc  = BODY_LOCS.get(item.body_loc, str(item.body_loc))
            flags = []
            if item.ethereal: flags.append("ETH")
            if item.socketed: flags.append(f"SOCK{item.num_sockets}")
            if item.runeword: flags.append("RW")
            flag_str = " ".join(flags)
            print(f"    [{item.quality_name:8}] {item.base_code:5}  "
                  f"ilvl={item.ilvl:3}  {loc:10}  {flag_str}")
        if len(save.items) > 30:
            print(f"    ... and {len(save.items)-30} more")
    if save.merc_items:
        print(f"  Merc Items ({len(save.merc_items)}):")
        for item in save.merc_items:
            print(f"    [{item.quality_name:8}] {item.base_code}")


if __name__ == "__main__":
    main()
