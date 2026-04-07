# D2 Save File Format — Complete Bit-Stream Reference
# .d2s v96 (v1.10–1.14d) — Verified against community analysis and source RE

---

## Header (0x00–0x14B, fixed-size)

```
Off   Size  Field                    Notes
────────────────────────────────────────────────────────────────────────────
0x00  4     Magic                    0xAA55AA55 — validation
0x04  4     Version                  96 (0x60) for v1.10+; 71 for v1.09
0x08  4     File size                Total byte length of file
0x0C  4     Checksum                 Sum of all bytes, with this field = 0
0x10  4     Active weapon slot       0 = primary, 1 = switch
0x14  16    Name                     ASCII, null-padded, max 15 chars + null
0x24  1     Status flags
                bit 0: ladder
                bit 1: expansion (Lord of Destruction)
                bit 2: unused
                bit 3: hardcore
                bit 4: died (hardcore death flag; char survives if bit4 set w/o bit3)
                bit 5: expansion (duplicate of bit 1)
                bit 6: unused
                bit 7: unused
0x25  1     Progression              Quest stage in furthest unlocked act
0x26  2     Unknown                  Usually 0x0000
0x28  1     Character class
                0 = Amazon
                1 = Necromancer
                2 = Barbarian
                3 = Sorceress
                4 = Paladin
                5 = Druid (expansion only)
                6 = Assassin (expansion only)
0x29  2     Unknown                  0x1010
0x2B  1     Level                    Current character level (1–99)
0x2C  4     Created                  Unix timestamp of creation
0x30  4     Last played              Unix timestamp of last session
0x34  4     Unknown                  0xFFFFFFFF
0x38  64    Skill hotkeys            16 × DWORD skill IDs (0xFFFF = unassigned)
0x78  4     Left mouse skill         Skill ID
0x7C  4     Right mouse skill        Skill ID
0x80  4     Left skill (switch)      Skill ID for weapon swap slot
0x84  4     Right skill (switch)     Skill ID for weapon swap slot
0x88  32    Appearance data          Menu char appearance selections
0xA8  3     Difficulty               One byte per difficulty:
                                       Normal, Nightmare, Hell
                                       Bit 7 = active (currently on this diff)
                                       Bits 0–2 = act reached (0–4)
0xAB  4     Map seed                 Deterministic map generation seed
0xAF  2     Mercenary dead           0 = alive, 1 = dead (costs gold to revive)
0xB1  4     Mercenary GUID           Unit ID of merc (0 = no merc)
0xB5  2     Mercenary name index     Index into hireling names table
0xB7  2     Mercenary type           Encodes act + combat style + difficulty
0xB9  4     Mercenary experience     Total XP (not level — level derived from XP)
0xBD  144   Padding / unknown        All zeros in standard saves
```

---

## Quest Data Section (variable, after 0x14C)

Magic header: `57 6F 6F 21` ("Woo!")

```
Off   Size  Field
────────────────────────────────────────────
0x00  2     Magic: 0x6677 ("Woo!" start)  — actually 0x576F6F21 as DWORD
0x04  2     Version: 6
0x06  2     Length: 298 bytes

Quest flags for each act × difficulty:
  3 difficulties × (Act1=6 quests + Act2=6 + Act3=6 + Act4=3 + Act5=6) = 3×27 = 81 quest entries
  Each quest = 2 bytes bitmask:
    bit 0:  quest log acknowledged
    bit 1:  quest complete step 1
    bit 2:  quest complete step 2
    ...
    bit 12: quest complete (fully done)
    bit 13: quest rewarded (reward taken)
```

### Quest IDs (Act 1)
| ID | Name | Reward |
|---|---|---|
| 0 | Den of Evil | Skill point, +1 to all resistances |
| 1 | Sisters' Burial Grounds | NPC revival (Blood Raven) |
| 2 | Tools of the Trade | Horadric Malus (socketed item) |
| 3 | The Search for Cain | Deckard Cain joins |
| 4 | The Forgotten Tower | Countess drops runes |
| 5 | Sisters to the Slaughter | Andariel → Act 2 |

---

## Waypoint Section (variable)

Magic: `57 53 00 00` ("WS\0\0")

```
0x00  2     Magic: 0x5753
0x02  2     Version: 1
0x04  2     Length: 81 bytes

3 difficulties × 5 acts × max 9 waypoints each
= 3 × 9 bytes (one bit per waypoint per act)
Each byte = waypoint activation bitmask within that act
Bit 0 of first byte = Act1 WP1 (town), always active
```

---

## NPC Introduction Flags (variable)

Magic: `01 77`

```
0x00  1     Magic: 0x01
0x01  1     Magic: 0x77
0x02  2     Version: 0x0031 (49)
0x04  122   Introduction flags (one bit per NPC per difficulty)
```

---

## Stats Section — Bit-Stream Encoded

Magic: `67 66` ("gf")

All stats are stored as variable-width bit fields, LSB first.
Each entry: 9-bit stat ID + N-bit value (N from itemstatcost.txt "CSvBits").
Ends with ID = 0x1FF (all 9 bits set).

```python
# Stat bit widths (CSvBits from itemstatcost.txt)
STAT_BITS = {
    0:  10,   # Strength
    1:  10,   # Energy
    2:  10,   # Dexterity
    3:  10,   # Vitality
    4:  10,   # Unused stat points
    5:  8,    # Unused skill points
    6:  21,   # Current HP ×256 (fixed-point)
    7:  21,   # Max HP ×256
    8:  21,   # Current Mana ×256
    9:  21,   # Max Mana ×256
    10: 21,   # Current Stamina ×256
    11: 21,   # Max Stamina ×256
    12: 7,    # Level
    13: 32,   # Experience
    14: 25,   # Gold carried
    15: 25,   # Gold in stash
}

def read_stats_section(data: bytes, offset: int) -> dict:
    assert data[offset:offset+2] == b'gf'
    reader = BitReader(data, (offset + 2) * 8)
    stats = {}
    while True:
        stat_id = reader.read(9)
        if stat_id == 0x1FF:
            break
        bits = STAT_BITS.get(stat_id, 32)
        stats[stat_id] = reader.read(bits)
    return stats
```

---

## Skills Section

Magic: `69 66` ("if")

```
0x00  2     Magic: 0x6966 ("if")
0x02  30    Skill allocations: one byte per skill slot
            Slots 0–29 map to class-specific skill IDs
            Value = number of hard points allocated (0–20)
```

### Skill Slot → Skill ID Mapping

```c
/* Amazon skill slots (0–29) → skill IDs */
static const WORD AmazonSkills[30] = {
    0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27, -1,-1
};
/* Each class has its own 28-skill layout; last 2 slots unused */
```

---

## Items Section — Bit-Stream Packed

Magic: `4A 4D` ("JM")

```
0x00  2     Magic: 0x4A4D ("JM")
0x02  2     Item count
0x04  ...   Item records (variable-length, packed bit stream)
```

### Item Bit-Stream Layout

Each item is a packed bit record. Field widths from the game source:

```
Field              Bits  Notes
──────────────────────────────────────────────────────────────────────────
JM header          16    Must be 0x4D4A at start of each item
Unknown            4
Identified         1     1 = identified
Unknown            6
Socketed           1     1 = has sockets
Unknown            1
New                1     1 = recently picked up (glows)
Unknown            2
Ear                1     1 = this is a player ear
Starter item       1     1 = starting item (staff/tome)
Unknown            3
Simple item        1     1 = no extended data (e.g., gold, arrows)
Ethereal           1
Unknown            1
Personalized       1
Unknown            1
Runeword           1
Unknown            5
Version            8     0x00 = pre-1.08, 0x01 = 1.08+, 0x02 = expansion
Unknown            2
Location           3     0=inv 1=equip 2=belt 3=ground 4=vendor 5=socket 6=?
Panel              4     Which inventory panel (body/inv/stash/cube)
Column             4     Inventory column (0–9)
Row                4     Inventory row (0–3)
Type               4     BODYLOC if equipped
Base code          32    4-char item code (e.g., "swrd", "helm") as packed ASCII
── Compact items stop here if Simple==1 ──────────────────────────────────
Number of sockets  3
Item ID            32    Unique item GUID for this session
Item level         7     0–127 (iLvl)
Quality            4     ITEMQUAL_* enum
Multiple pictures  1     If 1: 3 extra bits for alt gfx index
Class specific     1     If 1: 11 extra bits for class affix
── Quality-specific data follows ─────────────────────────────────────────
  Inferior/Superior  3 bits: inferior/superior type index
  Magic prefix       11 bits
  Magic suffix       11 bits
  Set item           12 bits: set ID
  Unique item        12 bits: unique ID
  Rare/Craft:        8+8 bits: rare prefix + suffix name IDs
                     for 1–6 affixes: 1-bit present + 11-bit affix ID each
── Runeword flag ──────────────────────────────────────────────────────────
  Runeword ID        16 bits (if Runeword==1)
── Personalized name ──────────────────────────────────────────────────────
  Name               7×7 bits = 49 bits (7 chars × 7-bit ASCII offset)
── Ear data (if Ear==1) ───────────────────────────────────────────────────
  Player class       3 bits
  Player level       7 bits
  Player name        7×7=49 bits
── Extended stat properties ───────────────────────────────────────────────
  Properties encoded as: 9-bit prop ID + variable bits (from itemstatcost.txt)
  Terminated by 0x1FF (9 bits set)
── Socketed items ─────────────────────────────────────────────────────────
  N items follow immediately (where N = num_sockets_filled)
  Each is a complete item record (recursive)
```

---

## Checksum Algorithm

```
DWORD D2_CalcSaveChecksum(BYTE* pFile, DWORD dwSize) {
    DWORD checksum = 0;
    for (DWORD i = 0; i < dwSize; i++) {
        /* Rotate left by 1 bit, then add byte */
        checksum = (checksum << 1) | (checksum >> 31);
        checksum += pFile[i];
    }
    return checksum;
}

/* To verify: zero out bytes 0x0C–0x0F, recompute, compare to stored value */

| 219 | 0xDB | Item_Damage_Bonus | Damage bonus (bow mastery) |
| 220 | 0xDC | Item_Kick_Damage | Kick damage (Assassin) |
