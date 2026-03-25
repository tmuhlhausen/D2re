# D2 Monster AI States Reference

---

## AI Architecture

Each monster row in `monstats.txt` has an `Ai` column referencing one of 300
named AI behaviors. These map to function pointers in `D2Game.dll`.
The server runs at 25 Hz; each monster gets one AI tick per frame.

### AI Execution Order Each Tick

```
1. Check if monster is alive (not MM_DEAD or MM_DEATH)
2. Check if monster is in a loaded room (player nearby)
3. Update animation frame counter
4. Run AI function: g_AITable[aiCode](pMon, 0, &aiParam)
5. Process queued events (EVENT_GETHIT, EVENT_ATTACKED, etc.)
6. Update position along Path if PATHFLAG_MOVING
7. Check room transition
```

---

## Named AI Behaviors (Key Entries)

| aiCode | Name (monstats.txt) | Behavior | Example Monsters |
|---|---|---|---|
| 0 | `zombie` | Shamble toward player, melee attack | Zombies, Fallen |
| 1 | `tempest` | Melee + knockback | Carver |
| 2 | `npc` | Stand, talk when interacted with | Akara, Gheed |
| 3 | `idle` | Stationary, no AI | Town pets |
| 4 | `ranged` | Maintain distance, shoot projectiles | Fallen Shaman |
| 5 | `skeleton` | Walk/attack, flee if low HP | Skeletons |
| 6 | `mummy` | Raise fallen, melee | Greater Mummy |
| 7 | `scarab` | Aggressive charge, high speed | Dung Soldiers |
| 8 | `sandraider` | Ambush from off-screen | Sand Raiders |
| 9 | `suicideminion` | Run into player, explode | Suicide Minions (Duriel area) |
| 10 | `desert_mercenary` | Follow owner, assist attacks | Act 2 Mercenaries |
| 11 | `mummy_generator` | Spawn minions at interval | Mummy Sarcophagus |
| 12 | `vipers` | Poison spit + melee | Sand Leapers |
| 13 | `coldplains_zombie` | Slow zombie walk | Cold Plains zombies |
| 14 | `bloodraven` | Fly, summon undead | Blood Raven (boss) |
| 20 | `andariel` | Boss AI: phase-based poison spray + melee | Andariel |
| 21 | `duriel` | Boss: charge + Holy Freeze aura | Duriel |
| 24 | `radament` | Teleport + curse + skeletons | Radament (boss) |
| 30 | `mephisto` | Teleport, chain lightning, blizzard, bone spear | Mephisto |
| 31 | `diablo` | Fire nova, lightning hose, fire breath | Diablo |
| 32 | `baal` | Phase-based: tentacles, vortex, decoys | Baal |
| 40 | `fallen_rogue` | Stand and shoot, flee if player comes close | Fallen Shaman |
| 41 | `overlord` | Command buff: raises speed of nearby fallen | Carver Shaman |
| 50 | `summoner` | Teleport, cast spells at range | The Summoner |
| 55 | `council` | Phase: lightning, hydra, meteor | Council Members |
| 60 | `izual` | Melee, frost nova, inferno | Izual |
| 70 | `nihlathak` | Corpse Explosion spam, teleport | Nihlathak |
| 80 | `ancients` | Coordinated trio combat | Ancients |

---

## Standard Melee AI (ai=0 "zombie") — Reconstructed

This is the most common AI pattern. Understanding it helps reverse all variants.

```c
/* D2Game.dll — "zombie" AI function (reconstructed from v1.13c) */
void __fastcall AI_Zombie(UnitAny* pMon, int _edx, AIParam* pParam) {
    /* If in hit-stun: wait for animation to finish */
    if (pMon->dwMode == MM_GETHIT) return;
    if (pMon->dwMode == MM_DEATH || pMon->dwMode == MM_DEAD) return;

    /* Find nearest hostile unit */
    UnitAny* pTarget = D2Game_FindNearestHostile(pMon, pParam->dwAggroRange);
    if (!pTarget) {
        /* No target: idle or random walk */
        if (pMon->dwMode == MM_WALK || pMon->dwMode == MM_RUN)
            return;  /* already moving, let path finish */
        if (D2Game_Rand(100) < 5)  /* 5% chance per tick to start random walk */
            D2Game_StartRandomWalk(pMon, pParam->dwWalkRange);
        return;
    }

    /* Target found: check if in melee range */
    DWORD dist = D2Game_GetDistanceSq(pMon, pTarget);
    if (dist <= pParam->dwMeleeRange * pParam->dwMeleeRange) {
        /* In range: attack if not already attacking */
        if (pMon->dwMode != MM_ATTACK1 && pMon->dwMode != MM_ATTACK2) {
            D2Game_StartAttack(pMon, pTarget, 0);
        }
    } else {
        /* Out of range: path toward target */
        if (pMon->dwMode != MM_WALK && pMon->dwMode != MM_RUN) {
            D2Game_PathFind(pMon, pTarget->pPath->wPosX,
                                  pTarget->pPath->wPosY, PATHFLAG_MOVING);
            pMon->dwMode = (pParam->bCanRun && dist > 16*16) ? MM_RUN : MM_WALK;
        }
    }
}
```

---

## Boss AI Phase Detection

Many bosses have phase transitions based on HP percentage.

```c
/* Generic boss phase helper */
DWORD D2Game_GetBossPhase(UnitAny* pBoss) {
    DWORD curHP = D2Common_GetUnitStat(pBoss, 0, STAT_HITPOINTS, 0) >> 8;
    DWORD maxHP = D2Common_GetUnitStat(pBoss, 0, STAT_MAXHP, 0) >> 8;
    if (maxHP == 0) return 0;
    DWORD pct = curHP * 100 / maxHP;
    if (pct >= 75) return 1;
    if (pct >= 50) return 2;
    if (pct >= 25) return 3;
    return 4;
}

/* Diablo uses this for: */
/*  Phase 1 (100–75%): Fire Nova + Lightning Hose */
/*  Phase 2 (75–50%): Adds Red Lightning Hose */
/*  Phase 3 (50–25%): Adds Fire Wall spawn */
/*  Phase 4 (<25%):   Adds Bone Prison on player */
```

---

## Aggro System

```c
/* D2Game.dll+0x84270 (v1.13c) — find nearest hostile in range */
UnitAny* D2Game_FindNearestHostile(UnitAny* pMon, DWORD dwRange) {
    UnitAny* pBest = NULL;
    DWORD dwBestDist = dwRange * dwRange;

    /* Iterate all units in current room + adjacent rooms */
    Room1** pRooms = pMon->pPath->pRoom1->pRoomsNear;
    for (DWORD r = 0; r < pMon->pPath->pRoom1->dwRoomsNear; r++) {
        UnitAny* pUnit = pRooms[r]->pUnitFirst;
        while (pUnit) {
            if (D2Game_IsHostile(pMon, pUnit)) {
                DWORD dist = D2Game_GetDistanceSq(pMon, pUnit);
                if (dist < dwBestDist) {
                    dwBestDist = dist;
                    pBest = pUnit;
                }
            }
            pUnit = pUnit->pRoomNext;
        }
    }
    return pBest;
}

/* Hostility matrix */
BOOL D2Game_IsHostile(UnitAny* pA, UnitAny* pB) {
    /* Monsters are hostile to players and pets */
    /* Players are hostile to monsters */
    /* Player-vs-player hostility depends on game flags + hostile declaration */
    if (pA->dwType == UNIT_MONSTER && pB->dwType == UNIT_PLAYER) return TRUE;
    if (pA->dwType == UNIT_PLAYER  && pB->dwType == UNIT_MONSTER) return TRUE;
    if (pA->dwType == UNIT_MONSTER && pB->dwType == UNIT_MONSTER)
        return (pA->dwOwnerGuid == 0 && pB->dwOwnerGuid != 0) ||  /* wild vs pet */
               (pA->dwOwnerGuid != 0 && pB->dwOwnerGuid == 0);    /* pet vs wild */
    return FALSE;
}
```

---

## Flee AI

Some monsters flee when health is low or when a specific event occurs
(e.g., Fallen flee when their Shaman is killed).

```c
/* Shaman death triggers flee in all nearby Fallen */
/* D2Game.dll — EVENT_DEATH handler for Shaman units */
void __fastcall AI_Shaman_OnDeath(UnitAny* pShaman, int _edx, void* pData) {
    /* Iterate units in nearby rooms */
    Room1* pRoom = pShaman->pPath->pRoom1;
    for each unit in room {
        if (unit.dwType == UNIT_MONSTER &&
            unit.pMonsterData->pMonStats->szAi == "fallen") {
            /* Set flee flag: run away from players for 10 seconds */
            unit.pMonsterData->bSpecialFlags |= MONFLAG_FLEEING;
            unit.dwNextTime = GetCurrentTick() + 25 * 10;  /* 10 seconds */
        }
    }
}
```
