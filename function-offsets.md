# D2 Combat Formulas — Complete Reference

All formulas verified against Jarulf's Guide v1.13 and community disassembly.

---

## Hit Chance (Physical Attack)

### PvM (Player vs Monster)

```
ChanceToHit% = AR / (AR + DEF) × 2 × aLvl / (aLvl + dLvl) × 100
Clamp result to [5%, 95%]

Where:
  AR   = attacker's total Attack Rating (STAT_ATTACKRATING)
  DEF  = defender's total Defense (STAT_ARMOR)
  aLvl = attacker's character level
  dLvl = defender's character level
```

### PvP (Player vs Player)

```
ChanceToHit% = AR / (AR + DEF) × 100
Clamp to [5%, 95%]

Note: Level difference is NOT used in PvP hit calculation.
```

### Blocking

```
Block% = (BlockRating × (dLvl + 15)) / 2 / dStrength
Clamp to [0%, 75%] for non-shield (Amazon passive shield),
         [0%, 75%] for shield

Block can only occur if:
  - Defender is not in a hit-stun state
  - Defender is in WALK or STAND mode (not running in 1.09+)
  - Block% roll succeeds: D2Game_Rand(100) < Block%
```

---

## Damage Calculation

### Physical Damage Pipeline

```
1. Roll raw damage: dmg = D2Game_Rand(maxDmg - minDmg + 1) + minDmg
2. Apply Enhanced Damage%: dmg = dmg × (100 + ED%) / 100
3. Apply Strength bonus (melee): dmg += dmg × StrBonus × Strength / 100 / 100
4. Apply Dexterity bonus (bows): dmg += dmg × DexBonus × Dexterity / 100 / 100
5. Deadly Strike (50% chance if DS available): dmg × 2
6. Crushing Blow (reduces target current HP by fraction):
     vs monsters: CB = current_hp / 4
     vs players:  CB = current_hp / 10
     vs act boss: CB = current_hp / 8
     (CB replaces additional damage, it is not additive)
7. Apply physical damage resistance: net_phys = dmg × (100 - DR%) / 100
     DR% capped at 50% in v1.10+ (was uncapped in 1.09)
```

### Elemental Damage

```
For each element E ∈ {Fire, Cold, Lightning, Poison, Magic}:
  raw_elemental = roll in [min_E, max_E]
  resist_E      = min(max_resist_E, STAT_RESIST_E) from StatList
  net_E         = raw_elemental × (100 - resist_E) / 100
  if net_E < 0: net_E = 0   ← negative resist (e.g., Conviction) is damage amplifier

  Exception — Poison:
    poison damage = (poisMin + rand(poisMax-poisMin)) × poisLen / 256 per frame
    total poison  = rate × frames (not all dealt at once)
```

### Open Wounds

```
Open Wounds deals physical damage over time:
Rate per frame (25 Hz) based on attacker's level:
  aLvl 1–15:   rate = 8 × aLvl / 25    per frame
  aLvl 16–30:  rate = 8 × (aLvl - 15) × 4 / 25 + 8 × 15 / 25
  aLvl 31–45:  ...  (progressive formula)
  
Duration: 8 seconds (200 frames)
Stacks: new OW proc resets the timer (does not stack)
```

---

## Defense and Damage Reduction

### Physical Damage Reduction

```
Damage Reduction % (DR%):
  Sources: item affixes, bone armor (Necro), cyclone armor (Druid), shout (Barb)
  Cap:     50% in v1.10+ (patch to fix damage reduction exploits)

Flat DR (absorb):
  Applied AFTER DR%
  net = max(0, (dmg × (100 - DR%) / 100) - flat_DR)
```

### Magic Damage Reduction (MDR)

```
Applies to magic damage only (not elemental, not physical)
No percentage form — only flat MDR from items
Item MDR cap: no cap, but items have maximum rolls
```

### Elemental Absorb

```
Applied in this order:
  1. Resistance reduces damage: E_after_res = E × (100 - res%) / 100
  2. Flat absorb heals: heal = min(flat_absorb, E_after_res)
     hp = min(maxhp, hp + heal)
     E_after_res -= heal
  3. Percent absorb heals: heal = E_after_res × absorb% / 100
     hp = min(maxhp, hp + heal)
     E_after_res -= heal
  Final damage = max(0, E_after_res)
```

---

## Attack Speed and Frame Rate

### Character Speed Formula

```
Frames per attack = ceil(256 / (IAS_product × base_weapon_speed))

Where IAS_product combines all IAS sources using the "breakpoint" table.
Each character class has a different frame rate table.

IAS soft cap: diminishing returns beyond ~75 IAS (class-dependent).
```

### Faster Hit Recovery (FHR) Breakpoints (Sorceress example)

| FHR% | Frames to recover |
|---|---|
| 0 | 15 |
| 5 | 14 |
| 9 | 13 |
| 14 | 12 |
| 20 | 11 |
| 30 | 10 |
| 42 | 9 |
| 60 | 8 |
| 86 | 7 |
| 142 | 6 |
| 280 | 5 |

### Faster Cast Rate (FCR) Breakpoints (Sorceress Lightning)

| FCR% | Cast frames |
|---|---|
| 0 | 19 |
| 9 | 18 |
| 20 | 17 |
| 37 | 16 |
| 63 | 15 |
| 105 | 14 |
| 200 | 13 |

---

## Life and Mana Calculations

### Displayed Life/Mana

```
displayed_HP = STAT_HITPOINTS / 256    (stat is stored fixed-point ×256)
displayed_MP = STAT_MANA / 256
displayed_ST = STAT_STAMINA / 256
```

### Life Per Level / Life from Vitality

```
Life from Vitality:
  Amazon:      3 life per vitality
  Necromancer: 2 life per vitality
  Barbarian:   4 life per vitality
  Sorceress:   2 life per vitality
  Paladin:     3 life per vitality
  Druid:       2.5 life per vitality (stored as 5/2 per 2 vit)
  Assassin:    3 life per vitality

Life per Level (from class data tables):
  Amazon: 2, Necro: 1.5, Barb: 2, Sorc: 1, Pala: 2, Druid: 1.5, Asn: 1.5
```

---

## Experience

### XP from Kill

```
base_xp = monster.experience[difficulty]   (from monstats.txt)

Group bonus (multiple killers in party):
  1 killer: base_xp × 1.0
  2 killers: base_xp × 1.0 (no penalty in v1.10+)
  3 killers: base_xp × 0.9
  4 killers: base_xp × 0.825
  5–8 killers: base_xp × (0.825 - (n-4)×0.05)  (diminishing)

Level difference penalty:
  If |pLvl - mLvl| > 10:
    penalty = (|diff| - 10) × 5%  per level beyond 10
    xp = base_xp × max(5%, 100% - penalty)
```

### XP Loss on Death

```
PvM death:
  Normal:     0% XP loss
  Nightmare:  5% XP loss (of XP earned in current level)
  Hell:       10% XP loss

PvP death:
  No XP loss regardless of difficulty

Hardcore: no XP loss (character dies permanently instead)
```

---

## Skill Damage Formulas

### Fireball (Sorceress)

```
min_fire = 8 × slvl + (base_min)
max_fire = 8 × slvl + (base_max)
synergy bonus from Inferno: +2% fire damage per level
synergy bonus from Firebolt: +4% fire damage per level
synergy bonus from Meteor:   +4% fire damage per level
```

### Frozen Orb (Sorceress)

```
min_cold = 20 + 2 × slvl
max_cold = 30 + 3 × slvl
freeze duration = (50 + 10 × slvl) × difficulty_modifier / 25  frames
(difficulty_modifier: Normal=1.0, NM=0.5, Hell=0.25)
```

### Zeal (Paladin)

```
attacks per cast = min(2 + slvl, 5)   (caps at 5 hits at level 3)
enhanced damage = 20 × slvl %
synergy from Sacrifice: +5% ED per level
The attack speed of each Zeal hit follows the standard melee formula.
```

### Whirlwind (Barbarian)

```
WW hits per frame depends on weapon speed:
  Step size = 15 (sub-tiles) per tick while spinning
  Hit frequency = every (weapon_frame_rate / 2) frames
  Minimum 4 hits total regardless of weapon speed
WW cannot be used with 2H bows/xbows.
```

---

## Conviction Aura Mechanics

```
Conviction reduces monster resistances below their natural floor.
For a monster immune to fire (e.g., 110% resist):
  effective_resist = 110 - (Conviction_reduction / 5)
  If result < 100, immunity is broken.
  Example: slvl 20 Conviction (-150%): 110 - 30 = 80% → fire hits at 20% damage

Party members do NOT benefit from breaking immunities — only the Paladin.
Conviction stacks multiplicatively with Lower Resist (Necro curse).
```
