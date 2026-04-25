#!/usr/bin/env python3
"""Wrapper for the packet sniffer implementation.
Adds a compatibility shim for PacketDef.notes so demo mode works.
"""
packet_sniffer.py — Diablo II network packet capture, decoder, and annotator.

Captures D2 TCP traffic (ports 4000 / 6112) and produces human-readable
explanations of every packet in real time — what it means in game terms,
what triggered it, what its field values signify, and what to watch for.

Requirements:
    pip install scapy colorama

Run as administrator / root for raw socket capture.

Usage:
    python packet_sniffer.py --interface eth0 --live
    python packet_sniffer.py --interface eth0 --live --verbose
    python packet_sniffer.py --interface eth0 --live --filter 0x0C
    python packet_sniffer.py --interface eth0 --live --no-color --output log.json
    python packet_sniffer.py --pcap capture.pcap --decode --verbose
    python packet_sniffer.py --pcap capture.pcap --filter 0x95 --hex
    python packet_sniffer.py --generate-structs
    python packet_sniffer.py --list
    python packet_sniffer.py --demo          # decode sample packets, no network needed
"""

import struct, sys, argparse, json, textwrap
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# Terminal color helpers (gracefully degrades if colorama not installed)
# ─────────────────────────────────────────────────────────────────────────────

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAVE_COLOR = True
except ImportError:
    HAVE_COLOR = False
    class Fore:
        RED = YELLOW = GREEN = CYAN = MAGENTA = BLUE = WHITE = LIGHTBLACK_EX = ""
    class Style:
        RESET_ALL = BRIGHT = DIM = ""

USE_COLOR = True  # toggled by --no-color

def c(text: str, color: str, bright: bool = False) -> str:
    if not USE_COLOR or not HAVE_COLOR:
        return text
    b = Style.BRIGHT if bright else ""
    return f"{b}{color}{text}{Style.RESET_ALL}"

def c2s_color(text: str) -> str:
    return c(text, Fore.CYAN, bright=True)

def s2c_color(text: str) -> str:
    return c(text, Fore.GREEN, bright=True)

def field_color(text: str) -> str:
    return c(text, Fore.WHITE)

def val_color(text: str) -> str:
    return c(text, Fore.YELLOW)

def explain_color(text: str) -> str:
    return c(text, Fore.LIGHTBLACK_EX)

def warn_color(text: str) -> str:
    return c(text, Fore.RED, bright=True)

def header_color(text: str) -> str:
    return c(text, Fore.MAGENTA, bright=True)

# ─────────────────────────────────────────────────────────────────────────────
# Game lookup tables for contextual field explanations
# ─────────────────────────────────────────────────────────────────────────────

UNIT_TYPES = {
    0: "Player", 1: "Monster", 2: "Object",
    3: "Missile", 4: "Item", 5: "Tile"
}

CHAR_CLASSES = {
    0: "Amazon", 1: "Necromancer", 2: "Barbarian",
    3: "Sorceress", 4: "Paladin", 5: "Druid", 6: "Assassin"
}

UNIT_MODES_PLAYER = {
    0: "Death", 1: "Knockout", 2: "Neutral/Idle", 3: "Walk",
    4: "Run", 5: "GetHit", 6: "TownIdle", 7: "TownWalk",
    8: "Attack1", 9: "Attack2", 10: "Block", 11: "Cast",
    12: "Throw", 13: "Kick", 14: "Sequence", 15: "Dead"
}

UNIT_MODES_MONSTER = {
    0: "Death", 1: "Sequence", 2: "Walk", 3: "GetHit",
    4: "Attack1", 5: "Attack2", 6: "Block", 7: "Cast",
    8: "Skill1", 9: "Skill2", 10: "Skill3", 11: "Skill4",
    12: "Dead", 13: "Knockback", 14: "Stun", 15: "Stand/Idle",
    16: "Spawn", 17: "Run", 18: "Retreat", 19: "Resurrect"
}

STAT_NAMES = {
    0x00: "Strength",         0x01: "Energy",
    0x02: "Dexterity",        0x03: "Vitality",
    0x04: "Stat Points",      0x05: "Skill Points",
    0x06: "HP (cur×256)",     0x07: "MaxHP (×256)",
    0x08: "Mana (cur×256)",   0x09: "MaxMana (×256)",
    0x0A: "Stamina (×256)",   0x0B: "MaxStamina (×256)",
    0x0C: "Level",            0x0D: "Experience",
    0x0E: "Gold",             0x0F: "Stash Gold",
    0x11: "Enhanced Damage%", 0x12: "Attack Rating",
    0x15: "Defense/Armor",
    0x24: "Fire Resist",      0x26: "Lightning Resist",
    0x28: "Cold Resist",      0x2A: "Poison Resist",
    0x34: "Fire Damage Min",  0x35: "Fire Damage Max",
    0x48: "Faster Run/Walk",  0x49: "Faster Attack Speed",
    0x4B: "Faster Hit Recovery",
    0x4C: "Faster Block Rate", 0x4F: "Faster Cast Rate",
    0x52: "Magic Find",       0x53: "Gold Find",
    0x7D: "+All Skills",      0xAB: "Life Steal",
    0xAC: "Mana Steal",
}

# Selected well-known skill IDs for inline display
SKILL_NAMES = {
    0:  "Magic Arrow",     1:  "Fire Arrow",      3:  "Critical Strike",
    4:  "Jab",             5:  "Cold Arrow",       6:  "Multiple Shot",
    9:  "Poison Javelin",  14: "Lightning Bolt",  15: "Ice Arrow",
    16: "Guided Arrow",   18: "Charged Strike",   19: "Plague Javelin",
    20: "Strafe",          26: "Lightning Fury",  27: "Valkyrie",
    36: "Fire Bolt",       37: "Warmth",           38: "Charged Bolt",
    39: "Ice Bolt",        40: "Frozen Armor",    41: "Inferno",
    42: "Static Field",   43: "Telekinesis",      44: "Frost Nova",
    45: "Ice Blast",       46: "Blaze",            47: "Fire Ball",
    48: "Nova",            49: "Lightning",        50: "Shiver Armor",
    51: "Fire Wall",       52: "Enchant",          53: "Chain Lightning",
    54: "Teleport",        55: "Glacial Spike",    56: "Meteor",
    57: "Thunder Storm",   58: "Energy Shield",    59: "Blizzard",
    60: "Chilling Armor",  61: "Frozen Orb",       62: "Cold Mastery",
    63: "Fire Mastery",    64: "Lightning Mastery",
    65: "Sacrifice",       66: "Smite",            67: "Might (aura)",
    68: "Prayer",          69: "Resist Fire (aura)",
    71: "Defiance (aura)", 74: "Holy Bolt",        78: "Zeal",
    79: "Charge",          80: "Blessed Hammer",
    91: "Holy Fire",       92: "Holy Freeze",      93: "Holy Shock",
    96: "Fist of the Heavens",
    97: "Bash",            98: "Leap",             99: "Double Swing",
    100:"Stun",            101:"Double Throw",     102:"Leap Attack",
    103:"Concentrate",     104:"Iron Skin (pass)",
    105:"Whirlwind",       106:"Berserk",           107:"Frenzy",
    108:"Find Potion",     109:"Find Item",
    116:"Bone Armor",      117:"Raise Skeleton",   118:"Clay Golem",
    119:"Corpse Explosion",120:"Iron Golem",        121:"Amp Damage",
    122:"Weaken",          123:"Life Tap",          124:"Terror",
    125:"Lower Resist",    126:"Confuse",           127:"Attract",
    128:"Dim Vision",      129:"Blood Golem",       130:"Raise Skeletal Mage",
    131:"Decrepify",       132:"Fire Golem",        133:"Revive",
    134:"Teeth",           135:"Bone Spear",        136:"Bone Spirit",
    137:"Poison Dagger",   138:"Poison Explosion",  139:"Poison Nova",
    # D/T skills
    150:"Fire Trap",       151:"Death Sentry",      152:"Wake of Fire",
    153:"Blade Sentinel",  154:"Blade Fury",         155:"Blade Shield",
    156:"Burst of Speed",  157:"Weapon Block",       158:"Claw Mastery",
    159:"Psychic Hammer",  160:"Tiger Strike",       161:"Dragon Talon",
    162:"Shadow Warrior",  163:"Cobra Strike",       164:"Cloak of Shadows",
    165:"Dragon Claw",     166:"Fade",               167:"Shadow Master",
    168:"Dragon Tail",     169:"Mind Blast",         170:"Dragon Flight",
    171:"Death Sentry",
}

WAYPOINT_NAMES = {
    0:  "Rogue Encampment",     1:  "Cold Plains",       2:  "Stony Field",
    3:  "Dark Wood",            4:  "Black Marsh",       5:  "Outer Cloister",
    6:  "Jail Level 1",        7:  "Inner Cloister",    8:  "Catacombs Level 2",
    9:  "Lut Gholein",         10: "Sewers Level 2",    11: "Dry Hills",
    12: "Halls of the Dead L2",13: "Far Oasis",         14: "Lost City",
    15: "Palace Cellar L1",    16: "Arcane Sanctuary",  17: "Canyon of the Magi",
    18: "Kurast Docks",        19: "Spider Forest",     20: "Great Marsh",
    21: "Flayer Jungle",       22: "Lower Kurast",      23: "Kurast Bazaar",
    24: "Upper Kurast",        25: "Travincal",         26: "Durance of Hate L2",
    27: "Pandemonium Fortress",28: "City of the Damned",29: "River of Flame",
    30: "Harrogath",           31: "Frigid Highlands",  32: "Arreat Plateau",
    33: "Crystalline Passage", 34: "Glacial Trail",     35: "Halls of Pain",
    36: "Frozen Tundra",       37: "Ancient's Way",     38: "Worldstone Keep L2",
}

ITEM_QUALITIES = {
    1: "Inferior", 2: "Normal", 3: "Superior", 4: "Magic",
    5: "Set", 6: "Rare", 7: "Unique", 8: "Crafted"
}

PLAYER_RELATION_TYPES = {
    0: "Hostility declared",
    1: "Hostility cancelled",
    2: "Party invite sent",
    3: "Party invite accepted",
    4: "Party invite rejected",
    5: "Kicked from party",
    6: "Left party",
}

ITEM_ACTION_TYPES = {
    0x00: "Pickup from ground",
    0x01: "Drop to ground",
    0x02: "Move inside inventory",
    0x03: "Put in socket",
    0x04: "Destroyed (used/sold)",
    0x0B: "Moved to stash",
    0x0C: "Moved to cube",
    0x15: "Vendor bought from player",
    0x17: "Vendor sold to player",
    0x1A: "Gambled",
}

STATE_IDS = {
    0x04: "Frozen",          0x05: "Slowed",
    0x06: "Chilled",         0x08: "Cursed (Amplify Damage)",
    0x0A: "Poison Sickness", 0x0C: "Iron Maiden",
    0x0E: "Life Tap",        0x10: "Attract",
    0x12: "Confuse",         0x14: "Decrepit",
    0x17: "Lower Resist",    0x18: "Dim Vision",
    0x19: "Terror",          0x1A: "Bleed",
    0x20: "Holy Fire",       0x21: "Holy Freeze",
    0x22: "Holy Shock",      0x24: "Fanaticism",
    0x25: "Conviction",      0x26: "Meditation",
    0x28: "Redemption",      0x2A: "Vigor",
    0x41: "Bone Armor",      0x42: "Cyclone Armor",
    0x43: "Energy Shield",   0x4A: "Shiver Armor",
    0x4B: "Chilling Armor",  0x4C: "Frozen Armor",
    0x60: "Teleporting",     0x62: "Running",
    0x79: "Corpse (dead)",   0x7E: "Dodge",
    0x7F: "Avoid",           0x80: "Evade",
}

# ─────────────────────────────────────────────────────────────────────────────
# Packet definitions — now with rich 'explain' text
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PacketDef:
    cmd: int
    direction: str           # "C2S" or "S2C"
    name: str
    fixed_size: Optional[int]
    fields: List[tuple]      # (name, format_char, short_desc)
    explain: str = ""        # plain-English description of when/why this fires
    category: str = ""       # movement / combat / item / skill / ui / network / state

# Format codes: B=u8, H=u16, I=u32, Q=u64, b=i8, h=i16, i=i32
# Special: 'rest' = remainder of packet as hex

C2S_PACKETS: Dict[int, PacketDef] = {

    # ── Movement ──────────────────────────────────────────────────────────────
    0x01: PacketDef(0x01, "C2S", "WalkToLocation", 5,
        [("cmd","B",""), ("x","H","dest X tile"), ("y","H","dest Y tile")],
        explain="Sent when the player left-clicks a walkable tile. The client sends "
                "this immediately on click; the server validates the path and begins "
                "moving the unit. If the destination is blocked the server silently ignores it.",
        category="movement"),

    0x02: PacketDef(0x02, "C2S", "RunToLocation", 5,
        [("cmd","B",""), ("x","H","dest X tile"), ("y","H","dest Y tile")],
        explain="Same as WalkToLocation but with run speed enabled. Sent when "
                "the player right-clicks a tile or the run toggle is active. "
                "Running prevents blocking and increases stamina drain.",
        category="movement"),

    0x03: PacketDef(0x03, "C2S", "WalkToEntity", 9,
        [("cmd","B",""), ("type","I","unit type (0=player,1=monster,2=obj,4=item)"),
         ("guid","I","unit GUID")],
        explain="Sent when the player walks toward a specific unit — usually "
                "clicking on an NPC, item, or object to interact with it. The server "
                "will move the player and then fire the interaction when in range.",
        category="movement"),

    0x04: PacketDef(0x04, "C2S", "RunToEntity", 9,
        [("cmd","B",""), ("type","I","unit type"), ("guid","I","unit GUID")],
        explain="Run variant of WalkToEntity. Typically seen when running toward "
                "a monster to attack or an item to pick up.",
        category="movement"),

    # ── Skills ────────────────────────────────────────────────────────────────
    0x05: PacketDef(0x05, "C2S", "LeftSkillOnLocation", 13,
        [("cmd","B",""), ("x","H","target X"), ("y","H","target Y"),
         ("unk","I",""), ("unk2","I","")],
        explain="Left mouse skill cast on a map tile. Sent continuously while "
                "the left button is held (e.g. sustained Inferno, Blizzard, Fire Wall). "
                "The server rate-limits repeated casts via skill cooldown checks.",
        category="skill"),

    0x0C: PacketDef(0x0C, "C2S", "RightSkillOnLocation", 9,
        [("cmd","B",""), ("unk","H","skill slot flags"), ("unk2","B",""),
         ("x","H","target X tile"), ("y","H","target Y tile")],
        explain="Right mouse skill cast aimed at a tile coordinate. Fired on "
                "right-click for area skills: Teleport, Blizzard, Meteor, Frozen Orb, "
                "Bone Spirit, etc. Coordinates are tile-space, not pixel-space.",
        category="skill"),

    0x0D: PacketDef(0x0D, "C2S", "RightSkillOnEntity", 9,
        [("cmd","B",""), ("type","I","target unit type"), ("guid","I","target GUID")],
        explain="Right mouse skill aimed directly at a specific unit — e.g. "
                "Holy Bolt targeting an undead, Guided Arrow tracking a monster, "
                "or Corpse Explosion on a corpse (unit type 1 mode 12/15).",
        category="skill"),

    0x06: PacketDef(0x06, "C2S", "LeftSkillOnEntity", 9,
        [("cmd","B",""), ("type","I","target unit type"), ("guid","I","target GUID")],
        explain="Left mouse skill aimed at a unit. Typical for melee: the client "
                "sends this when clicking a monster with an attack skill selected. "
                "The server runs the attack resolution (AR vs DEF roll).",
        category="skill"),

    0x30: PacketDef(0x30, "C2S", "SelectSkill", 9,
        [("cmd","B",""), ("skill_id","H","skill ID (see skills.txt)"),
         ("hand","B","0=right,1=left"), ("unk","H",""), ("unk2","I","")],
        explain="Player changed which skill is assigned to a mouse button. "
                "Sent when clicking a skill icon in the skill tree or using F-key "
                "hotkeys. The server updates the player's active skill slots.",
        category="skill"),

    # ── Items ─────────────────────────────────────────────────────────────────
    0x13: PacketDef(0x13, "C2S", "PickupItem", 5,
        [("cmd","B",""), ("guid","I","item GUID")],
        explain="Player clicked on a ground item to pick it up. The server checks "
                "if the item still exists and the player is close enough, then "
                "transfers ownership and removes it from the world.",
        category="item"),

    0x16: PacketDef(0x16, "C2S", "DropItem", 5,
        [("cmd","B",""), ("guid","I","item GUID")],
        explain="Player dropped an item from their inventory to the ground. "
                "The server places the item at the player's current tile and "
                "broadcasts S2C ItemActionWorld to all nearby clients.",
        category="item"),

    0x17: PacketDef(0x17, "C2S", "ItemToCursor", 13,
        [("cmd","B",""), ("unk","I",""), ("guid","I","item GUID"), ("unk2","I","")],
        explain="Player picked up an item into the cursor (grabbed it from "
                "inventory without dropping). Used as the first step of "
                "inventory rearrangement before placing it elsewhere.",
        category="item"),

    0x19: PacketDef(0x19, "C2S", "PickupGroundItem", 5,
        [("cmd","B",""), ("guid","I","item GUID")],
        explain="Alternative pickup path — sent when using the auto-pickup key "
                "or when the client confirms a WalkToEntity interaction results "
                "in picking up a ground item.",
        category="item"),

    0x1A: PacketDef(0x1A, "C2S", "DropGoldItem", 5,
        [("cmd","B",""), ("amount","I","gold amount to drop")],
        explain="Player dropped a specific amount of gold from their carried gold. "
                "Typically seen in trade setups. Server verifies the player has "
                "sufficient gold and creates a gold pile on the ground.",
        category="item"),

    0x1C: PacketDef(0x1C, "C2S", "UseInventoryItem", 9,
        [("cmd","B",""), ("guid","I","item GUID"), ("unk","I","")],
        explain="Player used an item directly from inventory — typically a "
                "Town Portal Tome, Identify Scroll, or Horadric Cube activation.",
        category="item"),

    0x1D: PacketDef(0x1D, "C2S", "UseScrollOrPot", 9,
        [("cmd","B",""), ("guid","I","item GUID"), ("unk","I","")],
        explain="Player drank a potion from their belt or used a scroll. "
                "Healing/mana potions apply their effect server-side; "
                "Identify/TP scrolls trigger their respective actions.",
        category="item"),

    0x1F: PacketDef(0x1F, "C2S", "InsertItemIntoSocket", 9,
        [("cmd","B",""), ("cube_guid","I","socketed item GUID"),
         ("gem_guid","I","gem/rune GUID")],
        explain="Player inserted a gem, jewel, or rune into a socketed item. "
                "The server validates the socket count and item type compatibility, "
                "then applies the socketed item's stats to the host item.",
        category="item"),

    0x21: PacketDef(0x21, "C2S", "CubeTransmute", 1,
        [("cmd","B","")],
        explain="Player clicked the Transmute button in the Horadric Cube. "
                "The server checks cube contents against cubemain.txt recipes. "
                "If a valid recipe matches, the output item is generated and "
                "the ingredients are consumed.",
        category="item"),

    # ── NPCs ──────────────────────────────────────────────────────────────────
    0x6B: PacketDef(0x6B, "C2S", "NPCInteract", 9,
        [("cmd","B",""), ("type","I","unit type (usually 1=monster)"),
         ("guid","I","NPC unit GUID")],
        explain="Player opened interaction with an NPC (shopkeeper, quest NPC, "
                "mercenary hireling). The server responds with the NPC's dialog "
                "or shop inventory. Triggers on left-click when in NPC range.",
        category="npc"),

    0x6D: PacketDef(0x6D, "C2S", "NPCStop", 9,
        [("cmd","B",""), ("type","I",""), ("guid","I","NPC GUID")],
        explain="Player closed the NPC interaction window. Sent on pressing Esc "
                "or clicking outside the dialog. The server marks the NPC as "
                "no longer engaged with this player.",
        category="npc"),

    0x46: PacketDef(0x46, "C2S", "NPCBuy", None,
        [("cmd","B",""), ("npc_guid","I",""), ("item_guid","I",""),
         ("buy_cost","I","cost in gold")],
        explain="Player bought an item from an NPC shop. The server deducts gold, "
                "transfers item ownership, and updates the NPC's stock. "
                "If the item was repaired/recharged rather than bought, a "
                "separate repair packet fires instead.",
        category="npc"),

    0x47: PacketDef(0x47, "C2S", "NPCSell", None,
        [("cmd","B",""), ("npc_guid","I",""), ("item_guid","I",""),
         ("sell_value","I","gold received")],
        explain="Player sold an item to an NPC. The server adds the gold, "
                "removes the item from inventory, and adds it to the NPC's "
                "buyback list (available to repurchase at original price until the game ends).",
        category="npc"),

    0x77: PacketDef(0x77, "C2S", "HireHenchman", 9,
        [("cmd","B",""), ("type","I",""), ("guid","I","hireling GUID")],
        explain="Player hired a mercenary from an NPC (Kashya for Act 1 rogues, "
                "Greiz for Act 2 desert warriors, etc.). The server spawns the "
                "hireling unit and links it to the player.",
        category="npc"),

    # ── World ─────────────────────────────────────────────────────────────────
    0x50: PacketDef(0x50, "C2S", "WaypointActivate", 13,
        [("cmd","B",""), ("waypoint_id","B","waypoint table index"),
         ("unk","H",""), ("unk2","I",""), ("unk3","I","")],
        explain="Player selected a destination from the waypoint UI. "
                "Sent after opening a waypoint shrine and clicking a destination. "
                "The server validates the waypoint is unlocked for this character "
                "and teleports the player to the target area.",
        category="world"),

    0x3F: PacketDef(0x3F, "C2S", "UseSpecialItem", 9,
        [("cmd","B",""), ("type","I",""), ("guid","I","item/object GUID")],
        explain="Player used a special-purpose item or activated a special object: "
                "Tome of Town Portal, the Altar of the Butcher, Cairn Stones, "
                "quest triggers. Also fires for Uber keys.",
        category="world"),

    0x59: PacketDef(0x59, "C2S", "InitAct", 9,
        [("cmd","B",""), ("act","B","act 0–4"), ("unk","I",""),
         ("unk2","I","")],
        explain="Sent on game join or after using a waypoint. Tells the server "
                "which act and area the client needs loaded. The server responds "
                "with the level data, room geometry, and unit assignments for "
                "everything in the client's visible area.",
        category="world"),

    # ── Network / Misc ────────────────────────────────────────────────────────
    0x4F: PacketDef(0x4F, "C2S", "Respawn", 1,
        [("cmd","B","")],
        explain="Player pressed the Respawn button after death on Normal/NM/Hell. "
                "The server revives the character at the nearest town with "
                "reduced XP (5% NM, 10% Hell) and transfers corpse items back.",
        category="network"),

    0x5D: PacketDef(0x5D, "C2S", "Ping", 9,
        [("cmd","B",""), ("tick","I","client game tick counter"),
         ("unk","I","")],
        explain="Heartbeat sent roughly every 4 seconds. The server echoes it "
                "back as S2C Pong (0x9C). The round-trip time is the in-game "
                "latency shown in the ESC menu. If pings stop the server "
                "disconnects the client after ~60 seconds.",
        category="network"),

    0x68: PacketDef(0x68, "C2S", "PartyRequest", 9,
        [("cmd","B",""), ("action","I","0=invite,1=accept,2=reject,3=kick"),
         ("target_guid","I","target player GUID")],
        explain="Party management action. Includes sending invites, accepting, "
                "rejecting, or kicking players. The server broadcasts the "
                "result to all affected party members via S2C PlayerRelationship.",
        category="network"),

    0x2C: PacketDef(0x2C, "C2S", "DeclareHostile", 5,
        [("cmd","B",""), ("target_guid","I","player GUID")],
        explain="Player declared hostility against another player. Enables PvP "
                "combat after a 30-second warning. The server notifies both "
                "players and sets the hostile flag in the game's relation matrix.",
        category="network"),
}

S2C_PACKETS: Dict[int, PacketDef] = {

    # ── Game State ────────────────────────────────────────────────────────────
    0x01: PacketDef(0x01, "S2C", "GameDataLoad", None, [],
        explain="The first packet on game join. Contains the full serialized game "
                "state: player stats, inventory, act data, difficulty. This is "
                "the largest packet in the protocol — variable length, can be "
                "several KB for a well-geared character.",
        category="state"),

    0x02: PacketDef(0x02, "S2C", "GameFlags", 5,
        [("cmd","B",""), ("flags","I","game mode flags")],
        explain="Communicates game-level flags: expansion enabled, hardcore mode, "
                "ladder game, nightmare/hell difficulty. Sent once on join.",
        category="state"),

    # ── Unit Movement / Position ──────────────────────────────────────────────
    0x05: PacketDef(0x05, "S2C", "ReassignPlayer", 13,
        [("cmd","B",""), ("type","I","unit type"), ("guid","I","unit GUID"),
         ("x","H","new X tile"), ("y","H","new Y tile"),
         ("unk","B","")],
        explain="Hard teleport / position correction. Sent when the server "
                "overrides the client's predicted position — e.g. after using "
                "Teleport, entering a new area, or the server detecting a "
                "desync. The client snaps the unit to the new coordinates.",
        category="movement"),

    0x67: PacketDef(0x67, "S2C", "NPCMove", 13,
        [("cmd","B",""), ("guid","I","unit GUID"), ("type","I",""),
         ("x","H","dest X"), ("y","H","dest Y"), ("unk","H","")],
        explain="An NPC / monster started moving toward a new tile. Sent to all "
                "clients that have this unit in range. The client smoothly "
                "animates the unit walking or running to the destination.",
        category="movement"),

    0x69: PacketDef(0x69, "S2C", "NPCStop", 17,
        [("cmd","B",""), ("guid","I","unit GUID"), ("type","I",""),
         ("x","H","final X"), ("y","H","final Y"),
         ("life","H","current HP × 128 / MaxHP"), ("unk","I","")],
        explain="An NPC / monster stopped moving and is now idle at the given "
                "coordinates. The encoded life value lets clients display the "
                "health bar without a separate stat update — decode with: "
                "hp_pct = life / 128.0",
        category="movement"),

    0x15: PacketDef(0x15, "S2C", "WalkVerify", 5,
        [("cmd","B",""), ("x","H","confirmed X"), ("y","H","confirmed Y")],
        explain="Server confirmed the player's movement to these coordinates. "
                "Sent after validating a C2S WalkToLocation or RunToLocation. "
                "If the client is out of sync the server will send "
                "ReassignPlayer (0x05) instead.",
        category="movement"),

    # ── Vitals ────────────────────────────────────────────────────────────────
    0x0F: PacketDef(0x0F, "S2C", "HpMpUpdate", 5,
        [("cmd","B",""), ("hp_pct","H","HP fraction: value/32768 = pct"),
         ("mp_pct","H","Mana fraction: value/32768 = pct")],
        explain="Compact vitals update sent every time HP or MP changes. "
                "Values are fractional: displayed_hp = (hp_pct / 32768) × MaxHP. "
                "This fires on every hit taken, potion used, regeneration tick, "
                "or aura heal. High-frequency — expect many per second in combat.",
        category="combat"),

    # ── Stats ─────────────────────────────────────────────────────────────────
    0x19: PacketDef(0x19, "S2C", "SetStatByte", 6,
        [("cmd","B",""), ("stat_id","B","stat ID"), ("value","I","new value")],
        explain="Updates a single stat that fits in a byte — e.g. Level, "
                "Skill Points, a resistance value. The client applies it "
                "immediately to the player's stat sheet.",
        category="state"),

    0x1A: PacketDef(0x1A, "S2C", "SetStatWord", 7,
        [("cmd","B",""), ("stat_id","B","stat ID"), ("value","I","new value"),
         ("sub","H","sub-index (for skill stats)")],
        explain="16-bit stat update — used for stats like Attack Rating, Defense, "
                "resistances, or skill-level bonuses. Sub-index identifies "
                "per-skill bonus stats.",
        category="state"),

    0x1D: PacketDef(0x1D, "S2C", "SetStatDWord", 9,
        [("cmd","B",""), ("stat_id","H","stat ID"),
         ("value","I","new value"), ("sub","H","sub-index")],
        explain="32-bit stat update. Used for large stats: HP (×256 fixed-point), "
                "Mana, Stamina, Gold, Experience, and damage ranges. "
                "Divide HP/Mana/Stamina values by 256 to get the displayed number.",
        category="state"),

    # ── Combat & States ───────────────────────────────────────────────────────
    0x17: PacketDef(0x17, "S2C", "SetState", None,
        [("cmd","B",""), ("type","I","unit type"), ("guid","I","unit GUID"),
         ("state","B","state ID"), ("buf","rest","state-specific data")],
        explain="Applied a status effect / aura / buff / debuff to a unit. "
                "The state ID maps to conditions: frozen, poisoned, cursed, "
                "under Conviction, Energy Shield active, etc. "
                "The 'buf' remainder encodes duration or intensity data.",
        category="combat"),

    0x18: PacketDef(0x18, "S2C", "RemoveState", 9,
        [("cmd","B",""), ("type","I","unit type"), ("guid","I","unit GUID"),
         ("state","B","state ID")],
        explain="Removed a status effect from a unit — cured by a Cleansing "
                "aura, a Thawing Potion, the antidote potion, or simply "
                "because the duration expired.",
        category="combat"),

    0x27: PacketDef(0x27, "S2C", "SetUnitMode", 13,
        [("cmd","B",""), ("type","I","unit type"),
         ("guid","I","unit GUID"), ("mode","B","animation mode")],
        explain="Changed a unit's animation state. This drives all visual "
                "transitions: monster starts walking, player begins casting, "
                "unit enters death animation. Client uses this to select the "
                "correct DCC animation clip.",
        category="combat"),

    # ── Items ─────────────────────────────────────────────────────────────────
    0x47: PacketDef(0x47, "S2C", "ItemActionWorld", None, [],
        explain="An item appeared on the ground or was removed from it. "
                "Fires when a monster drops loot, a player drops an item, "
                "or an item despawns. Contains the full item bit-stream "
                "(same format as .d2s items section). Variable length.",
        category="item"),

    0x4F: PacketDef(0x4F, "S2C", "ItemActionOwned", None, [],
        explain="An item in a player's possession changed state: picked up, "
                "moved between inventory slots, equipped, unequipped, sold, "
                "transmuted, or socketed. Contains the full item data. "
                "This is the most information-dense packet in the game.",
        category="item"),

    0x34: PacketDef(0x34, "S2C", "GoldPickup", 9,
        [("cmd","B",""), ("amount","I","gold picked up"),
         ("new_total","I","new carried gold total")],
        explain="Player picked up a gold pile. The server auto-picks gold within "
                "range. 'amount' is the pile value; 'new_total' is carried gold "
                "after pickup (does not include stash).",
        category="item"),

    # ── Units ─────────────────────────────────────────────────────────────────
    0x95: PacketDef(0x95, "S2C", "UnitAssign", None, [],
        explain="A new non-player unit (monster, object, missile, item) entered "
                "the client's visible area. Contains the unit type, class ID, "
                "GUID, position, HP, and unit-specific data. The client creates "
                "the unit in its local unit hash table. Variable length.",
        category="state"),

    0x96: PacketDef(0x96, "S2C", "UnitRemove", 9,
        [("cmd","B",""), ("type","I","unit type"), ("guid","I","unit GUID")],
        explain="A unit left the client's visible area or was permanently "
                "destroyed. The client removes it from its local unit table. "
                "Fired when a monster goes out of range, dies and finishes the "
                "death animation, or a missile reaches its target.",
        category="state"),

    0xAC: PacketDef(0xAC, "S2C", "UnitAssignPlayer", None, [],
        explain="Another player entered the client's visible area. Contains "
                "the player's name, class, level, position, appearance data, "
                "and all equipped items visible to other players. Variable length.",
        category="state"),

    0x81: PacketDef(0x81, "S2C", "MercenaryGuid", 9,
        [("cmd","B",""), ("player_guid","I","player's GUID"),
         ("merc_guid","I","mercenary unit GUID")],
        explain="Links a mercenary to its owning player. Sent when a merc "
                "enters the client's area so the client can display the "
                "merc's health bar and name above their player's portrait.",
        category="state"),

    # ── World ─────────────────────────────────────────────────────────────────
    0xA7: PacketDef(0xA7, "S2C", "LevelEntry", 1,
        [("cmd","B","")],
        explain="Tells the client to load a new area (level). The client "
                "transitions the screen, loads the map tile data, and then "
                "sends C2S InitAct to request all the units in the new area. "
                "The brief black screen during area transitions corresponds to this.",
        category="world"),

    0xAE: PacketDef(0xAE, "S2C", "QuestItemState", 13,
        [("cmd","B",""), ("unk","I",""), ("unk2","I",""), ("unk3","I","")],
        explain="Updates a quest-item related state — typically quest completion "
                "acknowledgment or a quest object becoming active. Also fires "
                "for the Horadric Cube quest and scroll-of-inifuss reveals.",
        category="world"),

    0x59: PacketDef(0x59, "S2C", "EvilFogState", 9,
        [("cmd","B",""), ("unk","I",""), ("enable","I","1=enable fog")],
        explain="Enables or disables the 'evil fog' mechanic — the black shroud "
                "covering unexplored areas. Sent on area entry and lifted as "
                "the player explores. Also controls Nihlathak's fog in "
                "Halls of Vaught.",
        category="world"),

    # ── Social / Multiplayer ──────────────────────────────────────────────────
    0x26: PacketDef(0x26, "S2C", "PlaySound", 13,
        [("cmd","B",""), ("type","I","unit type"), ("guid","I","unit GUID"),
         ("sound_id","H","sound table index")],
        explain="Plays a sound attached to a specific unit — monster death "
                "sounds, NPC speech, skill sound effects, shrine activations. "
                "The client looks up the sound file from sounds.txt.",
        category="world"),

    0x2C: PacketDef(0x2C, "S2C", "PlayerRelationship", 7,
        [("cmd","B",""), ("player_guid","I","affected player"),
         ("relation_type","B","relation change type")],
        explain="Broadcasts a social state change to all players in the game: "
                "hostility declared/cancelled, party invite sent/accepted/rejected, "
                "player kicked from party. All clients update their social panels.",
        category="network"),

    # ── Network ───────────────────────────────────────────────────────────────
    0x2A: PacketDef(0x2A, "S2C", "GameHandshake", 1,
        [("cmd","B","")],
        explain="Initial connection handshake acknowledgment. Sent by the server "
                "immediately after the TCP connection is established, before "
                "any authentication. The client must receive this before "
                "sending any game packets.",
        category="network"),

    0x9C: PacketDef(0x9C, "S2C", "Pong", 9,
        [("cmd","B",""), ("tick","I","echoed client tick"),
         ("server_tick","I","server's own tick counter")],
        explain="Response to C2S Ping (0x5D). Echo of the client's tick plus "
                "the server's own counter. The difference between server_tick "
                "and the current client tick is an upper bound on one-way latency. "
                "Bots use this to synchronize game tick timing.",
        category="network"),

    0x51: PacketDef(0x51, "S2C", "DelayedStateChange", 13,
        [("cmd","B",""), ("unk","I",""), ("unit_id","I",""),
         ("unk2","I","")],
        explain="Schedules a state change to occur on a future tick — used for "
                "effects with a built-in delay: Bone Armor shatter, Shiver Armor "
                "freeze, Conviction aura settling. The client buffers it and "
                "applies it on the indicated future tick.",
        category="combat"),
}


# ─────────────────────────────────────────────────────────────────────────────
# Live game-state tracker — follows session context for richer annotations
# ─────────────────────────────────────────────────────────────────────────────

class GameStateTracker:
    """Tracks a rolling snapshot of the observed game session."""

    def __init__(self):
        self.player_guid: Optional[int] = None
        self.player_hp_pct: float       = 100.0
        self.player_mp_pct: float       = 100.0
        self.active_right_skill: int    = 0
        self.active_left_skill: int     = 0
        self.known_units: Dict[int, Dict] = {}  # guid → {type, last_mode}
        self.last_level: Optional[int]  = None
        self.ping_tick: Optional[int]   = None
        self.packet_counts: Dict[str, int] = {}
        self.start_time = datetime.now()
        self.suspicious: List[str]      = []

    def note(self, direction: str, cmd: int, name: str):
        key = f"{direction}_{name}"
        self.packet_counts[key] = self.packet_counts.get(key, 0) + 1

    def update_from_packet(self, cmd: int, direction: str,
                            data: bytes, fields: Dict) -> List[str]:
        """Return contextual annotations based on current tracked state."""
        notes = []

        if direction == "S2C" and cmd == 0x0F:
            # HpMpUpdate — track vitals, warn on sudden drops
            hp = fields.get("hp_pct", {}).get("value", 0)
            mp = fields.get("mp_pct", {}).get("value", 0)
            new_hp = hp / 327.68
            new_mp = mp / 327.68
            drop = self.player_hp_pct - new_hp
            if drop > 30:
                notes.append(warn_color(f"⚠  Large HP drop: {drop:.1f}% in one hit"))
            if new_hp < 10:
                notes.append(warn_color(f"⚠  CRITICAL HP: {new_hp:.1f}%"))
            self.player_hp_pct = new_hp
            self.player_mp_pct = new_mp
            notes.append(explain_color(
                f"   → HP: {new_hp:.1f}%  MP: {new_mp:.1f}%"))

        elif direction == "C2S" and cmd == 0x30:
            # SelectSkill
            sid = fields.get("skill_id", {}).get("value", 0)
            hand = fields.get("hand", {}).get("value", 0)
            sname = SKILL_NAMES.get(sid, f"skill #{sid}")
            slot = "left" if hand else "right"
            notes.append(explain_color(f"   → Assigned '{sname}' to {slot} mouse button"))
            if hand:
                self.active_left_skill = sid
            else:
                self.active_right_skill = sid

        elif direction == "C2S" and cmd in (0x0C, 0x05):
            # Skill on location — annotate with current active skill name
            sname = SKILL_NAMES.get(self.active_right_skill,
                                     f"skill #{self.active_right_skill}")
            notes.append(explain_color(f"   → Active right-hand skill: {sname}"))

        elif direction == "C2S" and cmd == 0x50:
            # WaypointActivate
            wp_id = fields.get("waypoint_id", {}).get("value", 0)
            wp_name = WAYPOINT_NAMES.get(wp_id, f"waypoint #{wp_id}")
            notes.append(explain_color(f"   → Traveling to: {wp_name}"))

        elif direction == "S2C" and cmd == 0x27:
            # SetUnitMode
            utype = fields.get("type", {}).get("value", 0)
            mode  = fields.get("mode", {}).get("value", 0)
            if utype == 0:
                mname = UNIT_MODES_PLAYER.get(mode, f"mode {mode}")
            else:
                mname = UNIT_MODES_MONSTER.get(mode, f"mode {mode}")
            notes.append(explain_color(
                f"   → Unit entering mode: {mname}"))

        elif direction == "S2C" and cmd in (0x19, 0x1A, 0x1D):
            # SetStat variants — annotate with stat name
            sid = fields.get("stat_id", {}).get("value", 0)
            val = fields.get("value", {}).get("value", 0)
            sname = STAT_NAMES.get(sid, f"stat 0x{sid:02X}")
            if sid in (0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B):
                display = f"{val / 256:.1f}"
            else:
                display = str(val)
            notes.append(explain_color(f"   → {sname} = {display}"))

        elif direction == "S2C" and cmd in (0x17, 0x18):
            # SetState / RemoveState
            sid = fields.get("state", {}).get("value", 0)
            sname = STATE_IDS.get(sid, f"state 0x{sid:02X}")
            action = "Applied" if cmd == 0x17 else "Removed"
            notes.append(explain_color(f"   → {action}: {sname}"))

        elif direction == "C2S" and cmd == 0x5D:
            # Ping
            tick = fields.get("tick", {}).get("value", 0)
            if self.ping_tick is not None:
                interval = tick - self.ping_tick
                notes.append(explain_color(
                    f"   → Tick interval since last ping: {interval} ticks ({interval/25:.1f}s)"))
            self.ping_tick = tick

        elif direction == "S2C" and cmd == 0x9C:
            # Pong
            c_tick = fields.get("tick", {}).get("value", 0)
            s_tick = fields.get("server_tick", {}).get("value", 0)
            if s_tick and c_tick:
                drift = abs(s_tick - c_tick)
                notes.append(explain_color(
                    f"   → Tick drift: {drift} ({drift/25*1000:.0f}ms est. one-way)"))

        elif direction == "C2S" and cmd in (0x03, 0x04, 0x06, 0x0D):
            # Targeting a unit — show type name
            utype = fields.get("type", {}).get("value", 0)
            guid  = fields.get("guid", {}).get("value", 0)
            tname = UNIT_TYPES.get(utype, f"type {utype}")
            notes.append(explain_color(f"   → Targeting {tname} GUID=0x{guid:08X}"))

        elif direction == "S2C" and cmd == 0x2C:
            # PlayerRelationship
            rt = fields.get("relation_type", {}).get("value", 0)
            rname = PLAYER_RELATION_TYPES.get(rt, f"relation type {rt}")
            notes.append(explain_color(f"   → Event: {rname}"))

        # Suspicious pattern detection
        c2s_count = self.packet_counts.get(f"C2S_RightSkillOnLocation", 0)
        if c2s_count > 0 and c2s_count % 500 == 0:
            self.suspicious.append(f"High RightSkillOnLocation rate ({c2s_count})")
            notes.append(warn_color(
                f"⚠  High skill-cast rate ({c2s_count}) — possible bot/macro activity"))

        return notes


# ─────────────────────────────────────────────────────────────────────────────
# Core packet decoder
# ─────────────────────────────────────────────────────────────────────────────

def decode_packet(data: bytes, direction: str) -> Dict[str, Any]:
    if not data:
        return {"error": "empty", "fields": {}}

    cmd   = data[0]
    table = C2S_PACKETS if direction == "C2S" else S2C_PACKETS
    defn  = table.get(cmd)

    result: Dict[str, Any] = {
        "cmd":       f"0x{cmd:02X}",
        "direction": direction,
        "name":      defn.name if defn else f"UNKNOWN_0x{cmd:02X}",
        "explain":   defn.explain if defn else "Unknown packet — not in protocol table.",
        "category":  defn.category if defn else "unknown",
        "raw_hex":   data.hex(" "),
        "length":    len(data),
        "fields":    {},
        "notes":     defn.notes if defn else "",
    }

    if defn and defn.fields:
        offset = 0
        for fname, fmt, desc in defn.fields:
            if fmt == "rest":
                result["fields"][fname] = {
                    "value": data[offset:].hex(" "), "desc": "remaining bytes"
                }
                break
            size = struct.calcsize(f"<{fmt}")
            if offset + size <= len(data):
                val = struct.unpack_from(f"<{fmt}", data, offset)[0]
                result["fields"][fname] = {"value": val, "desc": desc}
                offset += size

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Pretty printer
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_COLORS = {
    "movement": Fore.CYAN,
    "combat":   Fore.RED,
    "skill":    Fore.MAGENTA,
    "item":     Fore.YELLOW,
    "state":    Fore.GREEN,
    "world":    Fore.BLUE,
    "network":  Fore.WHITE,
    "npc":      Fore.CYAN,
    "unknown":  Fore.LIGHTBLACK_EX,
}

def print_packet(decoded: Dict, context_notes: List[str],
                  verbose: bool, show_hex: bool, ts: str,
                  src: str, dst: str):

    direction = decoded["direction"]
    name      = decoded["name"]
    length    = decoded["length"]
    category  = decoded.get("category", "unknown")
    cat_color = CATEGORY_COLORS.get(category, Fore.WHITE)

    dir_str = c2s_color("C→S") if direction == "C2S" else s2c_color("S→C")
    name_str = c(f"{name}", cat_color, bright=True)
    ts_str   = c(ts, Fore.LIGHTBLACK_EX)
    src_str  = c(src, Fore.WHITE)
    cmd_str  = c(decoded["cmd"], Fore.YELLOW)

    # ── Header line ──
    print(f"{ts_str}  {dir_str}  {cmd_str}  {name_str}  "
          f"{c(f'{length}B', Fore.LIGHTBLACK_EX)}  "
          f"{c(f'[{category}]', cat_color)}")
    print(f"  {c(src, Fore.LIGHTBLACK_EX)} → {c(dst, Fore.LIGHTBLACK_EX)}")

    # ── Fields ──
    for fname, fdata in decoded.get("fields", {}).items():
        if isinstance(fdata, dict):
            val  = fdata["value"]
            desc = fdata.get("desc", "")
            # Enrich specific fields
            if fname == "type":
                desc = UNIT_TYPES.get(val, desc)
            elif fname == "skill_id":
                desc = SKILL_NAMES.get(val, f"skill #{val}")
            elif fname == "stat_id":
                desc = STAT_NAMES.get(val, desc)
            elif fname == "waypoint_id":
                desc = WAYPOINT_NAMES.get(val, desc)
            elif fname == "state":
                desc = STATE_IDS.get(val, desc)
            elif fname == "relation_type":
                desc = PLAYER_RELATION_TYPES.get(val, desc)
            elif fname == "mode":
                desc = UNIT_MODES_MONSTER.get(val, UNIT_MODES_PLAYER.get(val, desc))
            val_str = val_color(f"0x{val:08X}") if isinstance(val, int) and val > 0xFFFF \
                      else val_color(str(val))
            desc_str = explain_color(f"  ← {desc}") if desc else ""
            print(f"  {field_color(f'{fname:<18}')} {val_str}{desc_str}")
        else:
            print(f"  {field_color(f'{fname:<18}')} {val_color(str(fdata))}")

    # ── Hex dump ──
    if show_hex:
        print(f"  {explain_color('hex: ' + decoded['raw_hex'])}")

    # ── Explanation ──
    explain = decoded.get("explain", "")
    if explain and verbose:
        wrapped = textwrap.fill(explain, width=72,
                                initial_indent="  ╰─ ",
                                subsequent_indent="     ")
        print(explain_color(wrapped))

    # ── Context notes from tracker ──
    for note in context_notes:
        print(f"  {note}")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# Live capture
# ─────────────────────────────────────────────────────────────────────────────

def live_capture(interface: str, output_file: Optional[str],
                  filter_cmd: Optional[int], verbose: bool,
                  show_hex: bool):
    try:
        from scapy.all import sniff, TCP, IP, Raw
    except ImportError:
        print("scapy required: pip install scapy")
        return

    tracker  = GameStateTracker()
    captures = []

    print(header_color("═" * 65))
    print(header_color(f"  D2 Packet Sniffer — Interface: {interface}"))
    print(header_color(f"  Ports: 4000 (game) / 6112 (Battle.net relay)"))
    print(header_color(f"  Verbose: {'ON' if verbose else 'OFF'}  "
                       f"Hex: {'ON' if show_hex else 'OFF'}"
                       + (f"  Filter: 0x{filter_cmd:02X}" if filter_cmd else "")))
    print(header_color("═" * 65))
    print()

    def handle_packet(pkt):
        if not pkt.haslayer(TCP) or not pkt.haslayer(Raw):
            return
        sport = pkt[TCP].sport
        dport = pkt[TCP].dport
        if 4000 not in (sport, dport) and 6112 not in (sport, dport):
            return

        direction = "C2S" if dport in (4000, 6112) else "S2C"
        payload   = bytes(pkt[Raw].load)
        if not payload:
            return
        if filter_cmd is not None and payload[0] != filter_cmd:
            return

        decoded = decode_packet(payload, direction)
        tracker.note(direction, payload[0], decoded["name"])
        notes   = tracker.update_from_packet(
                      payload[0], direction, payload, decoded["fields"])

        ts  = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        src = f"{pkt[IP].src}:{sport}"
        dst = f"{pkt[IP].dst}:{dport}"

        print_packet(decoded, notes, verbose, show_hex, ts, src, dst)

        if output_file:
            captures.append({
                "ts": ts, "src": src, "dst": dst,
                "direction": direction,
                "cmd": decoded["cmd"],
                "name": decoded["name"],
                "fields": {k: v["value"] if isinstance(v, dict) else v
                           for k, v in decoded["fields"].items()},
                "explain": decoded.get("explain", ""),
            })

    try:
        sniff(iface=interface,
              filter="tcp port 4000 or tcp port 6112",
              prn=handle_packet, store=False)
    except KeyboardInterrupt:
        elapsed = (datetime.now() - tracker.start_time).seconds
        total   = sum(tracker.packet_counts.values())
        print(header_color(f"\n{'═'*65}"))
        print(header_color(f"  Session summary — {elapsed}s elapsed, {total} packets"))
        print()
        for k, v in sorted(tracker.packet_counts.items(), key=lambda x: -x[1])[:15]:
            print(f"  {k:<40} {val_color(str(v))}")
        if tracker.suspicious:
            print(warn_color("\n  Suspicious activity detected:"))
            for s in tracker.suspicious:
                print(warn_color(f"    • {s}"))
        if output_file and captures:
            with open(output_file, "w") as f:
                json.dump(captures, f, indent=2)
            print(f"\n  Saved {len(captures)} packets → {output_file}")


# ─────────────────────────────────────────────────────────────────────────────
# PCAP file reader
# ─────────────────────────────────────────────────────────────────────────────

def read_pcap(pcap_path: str, filter_cmd: Optional[int],
              verbose: bool, show_hex: bool):
    try:
        from scapy.all import rdpcap, TCP, Raw, IP
    except ImportError:
        print("scapy required: pip install scapy")
        return

    tracker = GameStateTracker()
    packets = rdpcap(pcap_path)
    count   = 0

    for pkt in packets:
        if not pkt.haslayer(TCP) or not pkt.haslayer(Raw):
            continue
        sport = pkt[TCP].sport
        dport = pkt[TCP].dport
        if 4000 not in (sport, dport) and 6112 not in (sport, dport):
            continue
        payload = bytes(pkt[Raw].load)
        if not payload:
            continue
        if filter_cmd is not None and payload[0] != filter_cmd:
            continue

        direction = "C2S" if dport in (4000, 6112) else "S2C"
        decoded   = decode_packet(payload, direction)
        tracker.note(direction, payload[0], decoded["name"])
        notes     = tracker.update_from_packet(
                        payload[0], direction, payload, decoded["fields"])

        ts  = pkt.time if hasattr(pkt, "time") else "??"
        src = f"{pkt[IP].src}:{sport}" if pkt.haslayer(IP) else f"?:{sport}"
        dst = f"{pkt[IP].dst}:{dport}" if pkt.haslayer(IP) else f"?:{dport}"

        print_packet(decoded, notes, verbose, show_hex, str(ts), src, dst)
        count += 1

    print(f"\n{count} packets decoded from {pcap_path}")


# ─────────────────────────────────────────────────────────────────────────────
# C struct generator
# ─────────────────────────────────────────────────────────────────────────────

FORMAT_TO_C = {"B": "BYTE", "H": "WORD", "I": "DWORD", "Q": "QWORD",
               "b": "CHAR", "h": "SHORT", "i": "INT"}

def generate_c_structs():
    for direction, table in [("Client→Server", C2S_PACKETS),
                              ("Server→Client", S2C_PACKETS)]:
        print(f"\n/* {'═'*60} */")
        print(f"/* {direction} Packets                                         */")
        print(f"/* {'═'*60} */\n")
        for cmd, defn in sorted(table.items()):
            if not defn.fields or defn.fixed_size is None:
                continue
            print(f"/* 0x{cmd:02X} — {defn.name} ({defn.fixed_size} bytes) */")
            if defn.explain:
                for line in textwrap.wrap(defn.explain, 70):
                    print(f"/* {line} */")
            print("#pragma pack(push, 1)")
            print(f"typedef struct {defn.name} {{")
            for fname, fmt, desc in defn.fields:
                c_type  = FORMAT_TO_C.get(fmt, "BYTE")
                comment = f"  /* {desc} */" if desc else ""
                print(f"    {c_type:<12} {fname};{comment}")
            print(f"}} {defn.name};")
            print("#pragma pack(pop)\n")


# ─────────────────────────────────────────────────────────────────────────────
# Demo mode — no network required
# ─────────────────────────────────────────────────────────────────────────────

DEMO_PACKETS = [
    # WalkToLocation
    ("C2S", bytes([0x01, 0x40, 0x01, 0x80, 0x01])),
    # RightSkillOnLocation (Teleport)
    ("C2S", bytes([0x0C, 0x36, 0x00, 0x00, 0x60, 0x01, 0x40, 0x01, 0x00])),
    # SelectSkill (Blizzard = skill 59)
    ("C2S", bytes([0x30, 0x3B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
    # WaypointActivate (Outer Cloister)
    ("C2S", bytes([0x50, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
    # Ping
    ("C2S", bytes([0x5D, 0xE8, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
    # HpMpUpdate (75% HP, 50% MP)
    ("S2C", bytes([0x0F, 0x00, 0x60, 0x00, 0x40])),
    # SetStatDWord (HP × 256 = 2048 → displayed 8.0... small demo)
    ("S2C", bytes([0x1D, 0x06, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00])),
    # SetState (Frozen applied to unit)
    ("S2C", bytes([0x17, 0x01, 0x00, 0x00, 0x00, 0xAB, 0xCD, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00])),
    # SetUnitMode (monster entering attack)
    ("S2C", bytes([0x27, 0x01, 0x00, 0x00, 0x00, 0xAB, 0xCD, 0x00, 0x00, 0x04])),
    # Pong
    ("S2C", bytes([0x9C, 0xE8, 0x03, 0x00, 0x00, 0x10, 0x27, 0x00, 0x00])),
    # PlayerRelationship (hostility)
    ("S2C", bytes([0x2C, 0xAB, 0xCD, 0x12, 0x34, 0x00, 0x00])),
    # UnitRemove
    ("S2C", bytes([0x96, 0x01, 0x00, 0x00, 0x00, 0xDE, 0xAD, 0xBE, 0xEF])),
    # GoldPickup
    ("S2C", bytes([0x34, 0xE8, 0x03, 0x00, 0x00, 0xD0, 0x07, 0x00, 0x00])),
]


def run_demo(verbose: bool):
    tracker = GameStateTracker()
    print(header_color("═" * 65))
    print(header_color("  D2 Packet Sniffer — DEMO MODE (no network required)"))
    print(header_color("═" * 65))
    print()

    for direction, payload in DEMO_PACKETS:
        decoded = decode_packet(payload, direction)
        tracker.note(direction, payload[0], decoded["name"])
        notes   = tracker.update_from_packet(
                      payload[0], direction, payload, decoded["fields"])
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print_packet(decoded, notes, verbose=verbose, show_hex=True,
                     ts=ts, src="127.0.0.1:12345",
                     dst="127.0.0.1:4000" if direction == "C2S" else "127.0.0.1:12345")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Diablo II packet sniffer with live explanations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              sudo python packet_sniffer.py --interface eth0 --live --verbose
              sudo python packet_sniffer.py --interface eth0 --live --filter 0x0C
              python packet_sniffer.py --pcap session.pcap --decode --verbose
              python packet_sniffer.py --generate-structs > d2_packets.h
              python packet_sniffer.py --demo --verbose
        """))

    ap.add_argument("--interface",        help="Network interface for live capture")
    ap.add_argument("--live",             action="store_true")
    ap.add_argument("--pcap",             help="Read from .pcap file")
    ap.add_argument("--decode",           action="store_true")
    ap.add_argument("--filter",           type=lambda x: int(x, 0),
                                          help="Only show this command byte (hex ok: 0x0C)")
    ap.add_argument("--hex",              action="store_true", help="Show hex dump")
    ap.add_argument("--verbose",          action="store_true",
                                          help="Show full packet explanations")
    ap.add_argument("--no-color",         action="store_true")
    ap.add_argument("--output",           help="Write decoded log as JSON")
    ap.add_argument("--generate-structs", action="store_true",
                                          help="Print C structs for all packets")
    ap.add_argument("--list",             action="store_true",
                                          help="List all known packets")
    ap.add_argument("--demo",             action="store_true",
                                          help="Decode sample packets (no network)")
    args = ap.parse_args()

    global USE_COLOR
    USE_COLOR = not args.no_color

    if args.generate_structs:
        generate_c_structs()
        return

    if args.list:
        print(header_color("C→S Packets:"))
        for cmd, d in sorted(C2S_PACKETS.items()):
            print(f"  {val_color(f'0x{cmd:02X}')}  {c(d.name, Fore.CYAN):<30} "
                  f"{explain_color(f'[{d.category}]')}")
        print(header_color("\nS→C Packets:"))
        for cmd, d in sorted(S2C_PACKETS.items()):
            print(f"  {val_color(f'0x{cmd:02X}')}  {c(d.name, Fore.GREEN):<30} "
                  f"{explain_color(f'[{d.category}]')}")
        return

    if args.demo:
        run_demo(verbose=args.verbose)
        return

    if args.live and args.interface:
        live_capture(args.interface, args.output,
                     args.filter, args.verbose, args.hex)
        return

    if args.pcap:
        read_pcap(args.pcap, args.filter, args.verbose, args.hex)
        return

    ap.print_help()

if not hasattr(PacketDef, "notes"):
    PacketDef.notes = ""

if __name__ == "__main__":
    main()
