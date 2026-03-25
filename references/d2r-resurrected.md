# D2 Skill System — Complete Reference

---

## Skill Data Pipeline

Skills are defined in `skills.txt` (behavior) and `skilldesc.txt` (tooltip display).
The game loads both at startup into indexed arrays in `D2Common.dll`.

### Key skills.txt Columns

| Column | Effect |
|---|---|
| `Id` | Unique skill ID used everywhere in code |
| `skilldesc` | Cross-reference to skilldesc.txt display data |
| `anim` | Casting animation ID (SC_NU for no-cast) |
| `monanim` | Monster equivalent |
| `seqtrans` | Pre-cast animation sequence |
| `range` | 0=melee, 1=ranged, 2=magic range |
| `Mana` | Base mana cost |
| `ManaLvl` | Additional mana per level |
| `calc1–calc4` | Formula expressions evaluated at skill use |
| `param1–param8` | Skill behavior parameters (meaning varies per skill) |
| `Ethit` | Which element type deals damage |
| `EType` | Element type for damage calcs |
| `EMin/EMax` | Base elemental damage at level 1 |
| `EMinLvl1–5` | Scaling per level breakpoints |
| `EMaxLvl1–5` | |
| `ToHit` | Bonus attack rating |
| `HitFlags` | HITFLAG_* bitmask |
| `Aura` | 1 = this is a passive/active aura skill |
| `Interrupt` | 1 = attacking a casting unit interrupts the cast |
| `InTown` | 1 = can be used in town |
| `Summon` | ID of monster summoned by this skill |
| `CallFunc` | Pre-cast effect function index |
| `PrgFunc1–3` | Missile or DoT progression function indices |

---

## Skill ID Table (Selected)

### Amazon Skills
| ID | Name | Notes |
|---|---|---|
| 0 | Magic Arrow | Free; generates mana |
| 1 | Fire Arrow | Fire conversion |
| 2 | Inner Sight | Defense reduction aura |
| 3 | Critical Strike | Deadly Strike passive |
| 4 | Jab | 3-hit sequence |
| 5 | Cold Arrow | Cold conversion |
| 6 | Multiple Shot | 4–24 arrows |
| 7 | Dodge | Passive block vs melee |
| 8 | Power Strike | Lightning melee |
| 9 | Poison Javelin | DoT trail |
| 10 | Exploding Arrow | AoE fire |
| 11 | Slow Missiles | Reduces missile speed |
| 12 | Avoid | Passive dodge vs ranged |
| 13 | Impale | High AR/dmg, breaks weapon |
| 14 | Lightning Bolt | Converts jav to lightning |
| 15 | Ice Arrow | Freezes on hit |
| 16 | Guided Arrow | Tracks target |
| 17 | Penetrate | AR passive |
| 18 | Charged Strike | Lightning discharge |
| 19 | Plague Javelin | AoE poison cloud |
| 20 | Strafe | 10 arrows in arc |
| 21 | Immolation Arrow | Fire wall + explosion |
| 22 | Decoy | Illusion |
| 23 | Evade | Upgraded Avoid |
| 24 | Fend | 4-hit melee |
| 25 | Lightning Strike | Chain lightning melee |
| 26 | Lightning Fury | Mass jav lightning |
| 27 | Valkyrie | Summon warrior |

### Sorceress Skills (partial)
| ID | Name |
|---|---|
| 36 | Fire Bolt |
| 37 | Warmth |
| 38 | Charged Bolt |
| 39 | Ice Bolt |
| 40 | Frozen Armor |
| 41 | Inferno |
| 42 | Static Field |
| 43 | Telekinesis |
| 44 | Frost Nova |
| 45 | Ice Blast |
| 46 | Blaze |
| 47 | Fire Ball |
| 48 | Nova |
| 49 | Lightning |
| 50 | Shiver Armor |
| 51 | Fire Wall |
| 52 | Enchant |
| 53 | Chain Lightning |
| 54 | Teleport |
| 55 | Glacial Spike |
| 56 | Meteor |
| 57 | Thunder Storm |
| 58 | Energy Shield |
| 59 | Blizzard |
| 60 | Chilling Armor |
| 61 | Frozen Orb |
| 62 | Cold Mastery |
| 63 | Fire Mastery |
| 64 | Lightning Mastery |

---

## Charge-Based Skills

Charged skills store `(maxCharges << 8) | curCharges` in the stat value.

```c
/* Read charge info from item */
DWORD chargeData = GetItemStatBySkill(pItem, STAT_CHARGED, dwSkillId);
DWORD maxCharges = (chargeData >> 8) & 0xFF;
DWORD curCharges = chargeData & 0xFF;
DWORD skillLevel = (chargeData >> 16) & 0xFF;

/* Use a charge */
if (curCharges > 0) {
    curCharges--;
    DWORD newData = (maxCharges << 8) | curCharges | (skillLevel << 16);
    SetItemStat(pItem, STAT_CHARGED, dwSkillId, newData);
}
```

---

## Proc Skills (On-Hit / On-Attack)

```c
/* Check proc trigger — D2Game.dll+0x6F900 (v1.13c) */
void D2Game_CheckProcs(UnitAny* pAttacker, UnitAny* pVictim, DWORD dwHitFlags) {
    /* Iterate attacker's equipped items */
    /* For each item with STAT_SKILLONHIT: */
    /*   prob  = (stat_value >> 8) & 0xFF  (percentage chance) */
    /*   skill = stat_value & 0xFF          (skill ID) */
    /*   level = (stat_value >> 16) & 0x3F (skill level) */
    StatList* pList = pAttacker->pStatList;
    while (pList) {
        for (WORD i = 0; i < pList->wNumStats; i++) {
            StatEx* s = &pList->pStats[i];
            if (s->wStatId == STAT_SKILLONHIT) {
                BYTE prob  = (s->dwValue >> 8) & 0xFF;
                BYTE skill = s->dwValue & 0xFF;
                BYTE level = (s->dwValue >> 16) & 0x3F;
                if (D2Game_Rand(100) < prob) {
                    D2Game_UseSkill(pAttacker, skill, level,
                                    pVictim->pPath->wPosX,
                                    pVictim->pPath->wPosY, pVictim);
                }
            }
        }
        pList = pList->pNext;
    }
}
```

---

## Aura Enumeration

### Paladin Auras by Skill ID

| ID | Name | Type |
|---|---|---|
| 91 | Prayer | Regeneration |
| 92 | Resist Fire | Passive fire resist |
| 93 | Defiance | Defense % |
| 94 | Resist Cold | Passive cold resist |
| 95 | Cleansing | Curse/poison reduction |
| 96 | Resist Lightning | Passive lightning resist |
| 97 | Vigor | Run speed + stamina regen |
| 98 | Meditation | Mana regeneration |
| 99 | Thorns | Reflect damage |
| 100 | Blessed Aim | +Attack Rating |
| 101 | Concentration | +Damage |
| 102 | Holy Fire | Fire nova + aura |
| 103 | Holy Freeze | Cold slow aura |
| 104 | Holy Shock | Lightning aura |
| 105 | Sanctuary | vs undead |
| 106 | Redemption | Convert corpses to life/mana |
| 107 | Salvation | All resists |
| 108 | Fanaticism | IAS + AR + Damage |
| 109 | Conviction | Reduce enemy resists and defense |

---

## Missile System Deep Dive

Each missile type has its own row in `missiles.txt`. Key columns:

| Column | Meaning |
|---|---|
| `Vel` | Initial velocity in sub-tiles/frame |
| `MaxVel` | Velocity cap |
| `VelLvl` | Velocity scaling per skill level |
| `Accel` | Acceleration per frame |
| `Range` | Maximum travel distance |
| `SubLoop` | Collision behavior |
| `ServerHitFunc` | Server-side on-hit callback index |
| `ClientHitFunc` | Client-side on-hit callback (visual only) |
| `ServerDmgFunc` | Damage calculation function index |
| `ClientHitSubseq` | Spawned on client hit (explosion graphics) |
| `SrvHitSubseq` | Spawned on server hit (new missile) |
| `ExplosionMissile` | Sub-missile spawned on explosion |
| `NumDirections` | How many travel directions the sprite has |
| `LocalBlood` | Spawns blood effect on hit |
| `DamageType` | Physical/fire/cold/lightning/magic/poison |

### Missile Chains

Many skills work by chaining missiles:
```
Lightning Fury (skill) → spawns Jav missile
  → on hit: spawns N Lightning Bolt missiles (N scales with level)
    → each LB missile does lightning damage independently
```

```c
/* missiles.txt chain example — Meteor */
/* Primary missile: slow falling rock (visual only, no damage) */
/*   SrvHitSubseq → spawns "Meteor Explosion" on landing */
/*     Meteor Explosion → AoE fire damage */
/*       ExplosionMissile → spawns "Fire Wall" tile for 2 seconds */
```
