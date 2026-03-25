# Ghidra Scripts for D2 Reverse Engineering
# All scripts are Python (Ghidra's GhidraScript API via Jython/Python bridge)
# Place in ~/ghidra_scripts/ and run from Ghidra Script Manager

---

## D2_ImportSymbols.py
# Imports a JSON symbol table and labels all known functions/globals

```python
# D2_ImportSymbols.py
# Usage: Run in Ghidra against D2Common.dll or Diablo II.exe
# Requires: d2_symbols_v113c.json in same directory

import json, os
from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import Function

SYMBOL_FILE = os.path.join(os.path.dirname(getSourceFile().absolutePath),
                            "d2_symbols_v113c.json")

def run():
    with open(SYMBOL_FILE) as f:
        syms = json.load(f)

    listing   = currentProgram.getListing()
    symTable  = currentProgram.getSymbolTable()
    base      = currentProgram.getImageBase()
    applied   = 0

    for s in syms:
        addr = base.add(int(s["offset"], 16))

        # Label the address
        symTable.createLabel(addr, s["name"], SourceType.USER_DEFINED)

        # If it's a function, rename and set signature
        func = listing.getFunctionAt(addr)
        if func is None and s.get("is_function"):
            func = listing.createFunction(s["name"], addr,
                                           createAddressSet(addr, addr.add(1)),
                                           SourceType.USER_DEFINED)
        if func:
            func.setName(s["name"], SourceType.USER_DEFINED)
            if s.get("comment"):
                listing.setComment(addr, 0, s["comment"])  # EOL comment
        applied += 1

    print(f"[D2_ImportSymbols] Applied {applied} symbols")

run()
```

---

## D2_FindUnitAny.py
# Scans the binary and annotates all UnitAny* dereferences

```python
# D2_FindUnitAny.py
# Finds all references to UnitAny field offsets and annotates them

from ghidra.program.model.data import StructureDataType, PointerDataType, DWordDataType, WordDataType
from ghidra.program.model.mem import MemoryAccessException

# UnitAny field offsets to tag
UNIT_FIELDS = {
    0x00: ("dwType",     "DWORD"),
    0x04: ("dwClassId",  "DWORD"),
    0x08: ("dwMode",     "DWORD"),
    0x0C: ("dwUnitId",   "DWORD"),
    0x10: ("dwAct",      "DWORD"),
    0x14: ("pAct",       "PTR"),
    0x48: ("pStatList",  "PTR"),
    0x4C: ("pInventory", "PTR"),
    0x50: ("pPath",      "PTR"),
    0xC8: ("dwFlags",    "DWORD"),
    0xE8: ("pListNext",  "PTR"),
}

def run():
    listing = currentProgram.getListing()
    refMgr  = currentProgram.getReferenceManager()
    count   = 0

    for field_off, (name, _) in UNIT_FIELDS.items():
        # Search for: mov eax, [ecx + field_off]  patterns
        # x86: 8B 81 XX XX 00 00  (mov eax, [ecx + imm32])
        pattern_bytes = bytes([0x8B, 0x81]) + field_off.to_bytes(4, 'little')
        found = findBytes(currentProgram.getMinAddress(), pattern_bytes, 200)
        for addr in found:
            listing.setComment(addr, 0, f"UnitAny.{name} (+0x{field_off:02X})")
            count += 1

    print(f"[D2_FindUnitAny] Tagged {count} UnitAny field accesses")

run()
```

---

## D2_MapPacketHandlers.py
# Locates and labels the client/server packet dispatch tables

```python
# D2_MapPacketHandlers.py
# Identifies packet handler tables and labels each handler

KNOWN_CMDS = {
    # Client -> Server
    0x01: "C_WalkToLocation",
    0x02: "C_RunToLocation",
    0x03: "C_WalkToEntity",
    0x04: "C_RunToEntity",
    0x05: "C_LeftSkillOnLocation",
    0x06: "C_LeftSkillOnEntity",
    0x07: "C_LeftSkillOnEntityEx",
    0x08: "C_LeftSkillOnEntityEx2",
    0x09: "C_LeftSkillOnEntityEx3",
    0x0A: "C_LeftSkillOnEntityEx4",
    0x0C: "C_RightSkillOnLocation",
    0x0D: "C_RightSkillOnEntity",
    0x13: "C_PickupItem",
    0x16: "C_DropItem",
    0x17: "C_ItemToCursor",
    0x18: "C_UnshiftItem",
    0x19: "C_PickupGroundItem",
    0x1A: "C_DropGoldItem",
    0x1C: "C_UseInventoryItem",
    0x1D: "C_BeltPotion",
    0x1F: "C_InsertItem",
    0x21: "C_CubeTransmute",
    0x2C: "C_IdentifyItem",
    0x30: "C_SelectSkill",
    0x3E: "C_SelectQuestItem",
    0x3F: "C_UseSpecialItem",
    0x46: "C_NPCBuy",
    0x47: "C_NPCSell",
    0x48: "C_NPCRepair",
    0x4A: "C_TradeAccept",
    0x4B: "C_TradeCancel",
    0x4F: "C_Respawn",
    0x50: "C_WaypointActivate",
    0x58: "C_UseSkillOnItem",
    0x59: "C_InitAct",
    0x5D: "C_Ping",
    0x68: "C_OpenParty",
    0x6B: "C_NPCInteract",
    0x6D: "C_NPCStop",
    0x6F: "C_StartChat",
    0x70: "C_StopChat",
    0x71: "C_SetDifficulty",
    0x77: "C_HireHenchman",
    0x7A: "C_SendPartyRelation",
}

def run():
    listing  = currentProgram.getListing()
    symTable = currentProgram.getSymbolTable()
    base     = currentProgram.getImageBase()
    labeled  = 0

    for cmd, name in KNOWN_CMDS.items():
        sym = symTable.getSymbols(name)
        if not sym.hasNext():
            # Try to find by pattern: functions preceded by packet size byte
            pass  # Would need signature scan here
        else:
            s = sym.next()
            listing.setComment(s.getAddress(), 0, f"Packet handler cmd=0x{cmd:02X}")
            labeled += 1

    print(f"[D2_MapPacketHandlers] Labeled {labeled} packet handlers")

run()
```

---

## D2_ExportOffsets.py
# Exports all user-defined symbols to a JSON file for use with other tools

```python
# D2_ExportOffsets.py
# Exports all labeled functions to d2_offsets_export.json

import json, os
from ghidra.program.model.symbol import SourceType

def run():
    symTable = currentProgram.getSymbolTable()
    base     = currentProgram.getImageBase()
    listing  = currentProgram.getListing()
    output   = []

    syms = symTable.getAllSymbols(True)
    while syms.hasNext():
        sym = syms.next()
        if sym.getSource() == SourceType.USER_DEFINED:
            addr   = sym.getAddress()
            offset = addr.subtract(base)
            func   = listing.getFunctionAt(addr)
            entry  = {
                "name": sym.getName(),
                "offset": f"0x{offset:X}",
                "is_function": func is not None,
            }
            if func:
                entry["calling_convention"] = func.getCallingConventionName()
            output.append(entry)

    out_path = os.path.join(os.path.expanduser("~"), "d2_offsets_export.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[D2_ExportOffsets] Exported {len(output)} symbols to {out_path}")

run()
```

---

## D2_AnnotateStatEngine.py
# Finds all GetUnitStat/SetUnitStat calls and annotates with stat names

```python
# D2_AnnotateStatEngine.py

STAT_NAMES = {
    0x00: "STAT_STRENGTH",      0x01: "STAT_ENERGY",
    0x02: "STAT_DEXTERITY",     0x03: "STAT_VITALITY",
    0x06: "STAT_HITPOINTS",     0x07: "STAT_MAXHP",
    0x08: "STAT_MANA",          0x09: "STAT_MAXMANA",
    0x0B: "STAT_STAMINA",       0x0C: "STAT_MAXSTAMINA",
    0x0D: "STAT_LEVEL",         0x0E: "STAT_EXPERIENCE",
    0x0F: "STAT_GOLD",          0x10: "STAT_GOLDBANK",
    0x11: "STAT_ENHANCEDDEFENSE", 0x12: "STAT_ENHANCEDDAMAGE",
    0x13: "STAT_ATTACKRATING",  0x15: "STAT_ARMOR",
    0x16: "STAT_MAXDMG_MIN",    0x17: "STAT_MAXDMG_MAX",
    0x18: "STAT_SECONDARYMINDMG", 0x19: "STAT_SECONDARYMAXDMG",
    0x1B: "STAT_MANAAFTERKILL",
    0x1C: "STAT_LIFLEAFTERKILL",
    0x1F: "STAT_VELOCITY",      0x20: "STAT_RUNSPEED",
    0x21: "STAT_MAGICDAMAGEDREDUCED",
    0x22: "STAT_DMGREDUCED",    0x23: "STAT_DMGPERCENTREDUCED",
    0x24: "STAT_FIRERESIST",    0x25: "STAT_MAXFIRERESIST",
    0x26: "STAT_LIGHTRESIST",   0x27: "STAT_MAXLIGHTRESIST",
    0x28: "STAT_COLDRESIST",    0x29: "STAT_MAXCOLDRESIST",
    0x2A: "STAT_POISRESIST",    0x2B: "STAT_MAXPOISRESIST",
    # ... etc per stat-ids.md
}

def run():
    listing = currentProgram.getListing()
    base = currentProgram.getImageBase()

    # Find all 'push <stat_id_const>' before a call to GetUnitStat
    get_stat_addr = base.add(0x63990)  # v1.13c
    refs = currentProgram.getReferenceManager().getReferencesTo(get_stat_addr)

    for ref in refs:
        call_addr = ref.getFromAddress()
        # Walk backwards up to 3 instructions to find 'push imm' for stat ID
        instr = listing.getInstructionAt(call_addr)
        for _ in range(6):
            instr = listing.getInstructionBefore(instr.address)
            if instr and instr.getMnemonicString() == "PUSH":
                ops = instr.getDefaultOperandRepresentation(0)
                try:
                    stat_id = int(ops, 16) if ops.startswith("0x") else int(ops)
                    if stat_id in STAT_NAMES:
                        listing.setComment(call_addr, 0,
                            f"GetUnitStat({STAT_NAMES[stat_id]})")
                        break
                except: pass

    print("[D2_AnnotateStatEngine] Annotated GetUnitStat call sites")

run()
```

---

## D2_FindVersionString.py
# Quickly identifies D2 binary version from PE resources

```python
# D2_FindVersionString.py

def run():
    mem = currentProgram.getMemory()
    # Search for version string pattern "1.1" in .rsrc section
    rsrc = mem.getBlock(".rsrc")
    if rsrc:
        addr = rsrc.getStart()
        end  = rsrc.getEnd()
        pattern = bytes([0x31, 0x2E]) # "1."
        found = findBytes(addr, pattern, 50)
        for a in found:
            try:
                # Read next 6 bytes for version
                buf = getBytes(a, 12)
                ver = "".join(chr(b) for b in buf if 0x20 <= b < 0x7F)
                if ver.startswith("1."):
                    print(f"[D2_FindVersionString] Version: {ver} at {a}")
                    break
            except: pass

run()
```
