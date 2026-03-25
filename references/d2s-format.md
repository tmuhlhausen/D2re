# D2 Stat IDs Reference

Stat IDs are defined in `D2Common.dll` and correspond to rows in `itemstatcost.txt`.
The `WORD wStatId` field in `StatEx` uses these values.

## Encoding Notes

- **Fixed-point stats:** Many stats use 8-bit or 4-bit fractional encoding. The `*Divide*`
  and `*Multiply*` columns in `itemstatcost.txt` define the conversion. E.g., HP stored as
  `value * 256`, display as `value / 256`.
- **Signed vs unsigned:** Resistance stats are signed `int` (can be negative). Damage stats
  are unsigned `DWORD`.
- **Per-level stats:** Stats with "perlevel" in their name encode a value per character level.

---

## Core Vital Stats (0x00–0x0F)

| ID | Hex | Name | Notes |
|---|---|---|---|
| 0 | 0x00 | Strength | Base stat |
| 1 | 0x01 | Energy | |
| 2 | 0x02 | Dexterity | |
| 3 | 0x03 | Vitality | |
| 4 | 0x04 | Statpts | Unspent stat points |
| 5 | 0x05 | Newskills | Unspent skill points |
| 6 | 0x06 | Hitpoints | Current HP — divide by 256 for display |
| 7 | 0x07 | Maxhp | Max HP — divide by 256 |
| 8 | 0x08 | Mana | Current mana — divide by 256 |
| 9 | 0x09 | Maxmana | Max mana — divide by 256 |
| 10 | 0x0A | Stamina | Current stamina — divide by 256 |
| 11 | 0x0B | Maxstamina | Max stamina — divide by 256 |
| 12 | 0x0C | Level | Character level |
| 13 | 0x0D | Experience | Total XP |
| 14 | 0x0E | Gold | Carried gold |
| 15 | 0x0F | Goldbank | Stash gold |

---

## Offense Stats (0x10–0x2F)

| ID | Hex | Name | Notes |
|---|---|---|---|
| 16 | 0x10 | Item_Armor | Defense rating |
| 17 | 0x11 | Item_MaxDamage | Max physical damage |
| 18 | 0x12 | Item_MinDamage | Min physical damage |
| 19 | 0x13 | Item_Attackrating | Attack rating |
| 20 | 0x14 | Item_BlockChance | Block % |
| 21 | 0x15 | Item_Tohit | Bonus to attack rating |
| 22 | 0x16 | Item_Velocitypercent | Run/walk speed % |
| 23 | 0x17 | Item_Attackspeed | IAS (increased attack speed) |
| 24 | 0x18 | Item_Passiveattackspeed | Passive IAS |
| 31 | 0x1F | Item_Tohit_Percent | % bonus attack rating |
| 32 | 0x20 | Item_Damagemodifier | % enhanced damage |

---

## Defense / Resistance Stats (0x27–0x3B)

| ID | Hex | Name | Notes |
|---|---|---|---|
| 36 | 0x24 | Item_Resistfire | Fire resist (signed) |
| 37 | 0x25 | Item_Resistcold | Cold resist (signed) |
| 38 | 0x26 | Item_Resistlightning | Lightning resist (signed) |
| 39 | 0x27 | Item_Resistpoison | Poison resist (signed) |
| 40 | 0x28 | Item_Absorbfire | Fire absorb |
| 41 | 0x29 | Item_Absorbcold | Cold absorb |
| 42 | 0x2A | Item_Absorblightning | Lightning absorb |
| 43 | 0x2B | Item_Absorbpoison | Poison absorb (rare) |
| 44 | 0x2C | Item_Absorbfire_Percent | % fire absorb |
| 45 | 0x2D | Item_Absorbcold_Percent | % cold absorb |
| 46 | 0x2E | Item_Absorblightning_Percent | % lightning absorb |
| 48 | 0x30 | Item_Maxresfire | +max fire resist |
| 49 | 0x31 | Item_Maxrescold | +max cold resist |
| 50 | 0x32 | Item_Maxreslightning | +max lightning resist |
| 51 | 0x33 | Item_Maxrespoison | +max poison resist |

---

## Elemental Damage Stats (0x34–0x6F)

| ID | Hex | Name | Notes |
|---|---|---|---|
| 52 | 0x34 | Item_Firedamage_Min | Min fire damage |
| 53 | 0x35 | Item_Firedamage_Max | Max fire damage |
| 54 | 0x36 | Item_Lightdamage_Min | Min lightning |
| 55 | 0x37 | Item_Lightdamage_Max | Max lightning |
| 56 | 0x38 | Item_Magicaldamage_Min | Min magic |
| 57 | 0x39 | Item_Magicaldamage_Max | Max magic |
| 58 | 0x3A | Item_Colddamage_Min | Min cold |
| 59 | 0x3B | Item_Colddamage_Max | Max cold |
| 60 | 0x3C | Item_Colddamage_Length | Cold duration (frames) |
| 61 | 0x3D | Item_Poisondamage_Min | Poison dmg/sec × 256 |
| 62 | 0x3E | Item_Poisondamage_Max | |
| 63 | 0x3F | Item_Poisondamage_Length | Duration in frames |

---

## Life/Mana/Stamina Modifiers (0x70–0x8F)

| ID | Hex | Name | Notes |
|---|---|---|---|
| 74 | 0x4A | Item_Maxhp_Percent | +% max life |
| 75 | 0x4B | Item_Maxmana_Percent | +% max mana |
| 76 | 0x4C | Item_Maxstamina_Percent | +% max stamina |
| 77 | 0x4D | Item_Tohit_Perlevel | Attack rating per level |
| 78 | 0x4E | Item_Tohitpercent_Perlevel | |
| 79 | 0x4F | Item_Cold_Perlevel | Cold dmg per level |
| 80 | 0x50 | Item_Fire_Perlevel | Fire dmg per level |
| 81 | 0x51 | Item_Ltng_Perlevel | Lightning per level |
| 82 | 0x52 | Item_Pois_Perlevel | Poison per level |
| 83 | 0x53 | Item_Resall_Perlevel | All resist per level |
| 84 | 0x54 | Item_Absorb_Perlevel | Absorb per level |

---

## Life/Mana Leech & Regen (0x60–0x6F)

| ID | Hex | Name | Notes |
|---|---|---|---|
| 96 | 0x60 | Item_Dmg_Percent | +% enhanced damage |
| 97 | 0x61 | Item_Manasteal | Mana stolen per hit (÷2 = %) |
| 98 | 0x62 | Item_Lifesteal | Life stolen per hit |
| 99 | 0x63 | Item_Stam_Regen | Stamina regen |
| 104 | 0x68 | Item_Replenish_Life | Life regen per second |
| 105 | 0x69 | Item_Replenish_Mana | Mana regen per second |
| 106 | 0x6A | Item_Maxdurability | Item max durability |
| 107 | 0x6B | Item_Durability | Item current durability |

---

## Character Modifier Stats (0x80–0xAF)

| ID | Hex | Name | Notes |
|---|---|---|---|
| 138 | 0x8A | Item_Addskill_Tab | +skills to tab (sub=tab id) |
| 139 | 0x8B | Item_Addallskills | +all skills |
| 140 | 0x8C | Item_Addclassskills | +class skills (sub=class) |
| 141 | 0x8D | Item_Singleskill | +N to skill X (sub=skill id) |
| 155 | 0x9B | Item_Crushingblow | Crushing blow chance % |
| 156 | 0x9C | Item_Openwounds | Open wounds chance % |
| 157 | 0x9D | Item_Kick | Kick damage |
| 158 | 0x9E | Item_Deadlystrike | Deadly strike % |
| 159 | 0x9F | Item_Ignore_Target_Ac | Ignore target defense |
| 160 | 0xA0 | Item_Prevent_Heal | Prevent monster healing |
| 161 | 0xA1 | Item_Halffreezeduration | Half freeze duration |
| 162 | 0xA2 | Item_Tohit_Demon | +attack vs demons |
| 163 | 0xA3 | Item_Tohit_Undead | +attack vs undead |
| 164 | 0xA4 | Item_Dmg_Demon | +% damage vs demons |
| 165 | 0xA5 | Item_Dmg_Undead | +% damage vs undead |

---

## Charges and Procs (0xB0–0xCF)

| ID | Hex | Name | Notes |
|---|---|---|---|
| 204 | 0xCC | Item_Charged | Charged skill — sub=skill id; value = (maxcharges<<8)\|curcharges |
| 195 | 0xC3 | Item_Skillonskill | Skill-on-skill-use proc; sub=trigger skill, value=(chance<<8)\|cast skill |
| 196 | 0xC4 | Item_Skillonattack | On-attack proc |
| 197 | 0xC5 | Item_Skillonhit | On-hit proc |
| 198 | 0xC6 | Item_Skillondeath | On-death proc |

---

## Socket and Special Stats

| ID | Hex | Name | Notes |
|---|---|---|---|
| 214 | 0xD6 | Item_Numsockets | Number of sockets |
| 215 | 0xD7 | Item_Pierce_Cold | Pierce cold resist % |
| 216 | 0xD8 | Item_Pierce_Fire | Pierce fire resist % |
| 217 | 0xD9 | Item_Pierce_Ltng | Pierce lightning resist % |
| 218 | 0xDA | Item_Pierce_Pois | Pierce poison resist % |
| 219 | 0xDB | Item_Damage_Bonus | Damage bonus (bow mastery) |
| 220 | 0xDC | Item_Kick_Damage | Kick damage (Assassin) |
