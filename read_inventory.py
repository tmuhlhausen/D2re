---
name: d2-reverse-engineering
description: >
  Elite-level Diablo 2 (D2 Classic 1.00–1.14d AND D2 Resurrected 1.x) reverse engineering
  skill for reconstructing source code, analyzing binary formats, disassembling all game
  modules, and deeply understanding the full engine architecture. ALWAYS consult this skill
  for ANY of: D2/D2R source reconstruction, disassembly of Game.exe or D2*.dll modules,
  MPQ/CASC archive parsing, binary file formats (.d2s .d2i .dc6 .dcc .bin .tbl .ds1 .dt1),
  memory structures and runtime layout, packet protocol analysis, DRLG map generation,
  item generation pipeline, monster AI state machines, skill/aura/missile systems,
  combat formula reconstruction, RNG/seed algorithms, stat engine internals, inventory
  grid system, experience/leveling math, D2Mod/D2SE/BaseMod/D2BS hook SDK patterns,
  Ghidra/IDA scripting for D2, Python tooling for MPQ/save parsing, D2GS/PVPGN emulator
  server reconstruction, D2R CASC format differences, creating trainers/analysis tools,
  modding framework design, or any request to write/analyze/reconstruct code related to
  Diablo 2 internals at any level of depth. Always use this skill before writing D2 code.
---

# Diablo 2 — Complete Reverse Engineering & Source Reconstruction Skill

## Table of Contents
1. Engine Architecture & Module Map
2. Core Data Structures
3. Memory Subsystem (Fog.dll)
4. RNG System
5. DRLG Map Generation Engine
6. Pathfinding & Collision
7. Item Generation Pipeline
8. Stat & Combat Engine
9. Monster AI State Machine
10. Skill / Aura / Missile System
11. Event & Timer System
12. Inventory Grid System
13. Network Protocol Architecture
14. Rendering Pipeline
15. Binary File Formats
16. Disassembly Methodology
17. Hooking Framework & Injection
18. D2Mod / D2BS / BaseMod SDK
19. D2R Resurrected Differences
20. Python & Ghidra Tooling
21. Source Reconstruction Guidelines
22. Reference Files Index

---

## 1. Engine Architecture

### Module Map (Classic D2 v1.09d – v1.13c)

| Module | Size | Core Responsibility |
|---|---|---|
| `D2Game.dll` | ~2.4 MB | Server-side logic: monsters, skills, missiles, AI, loot, levels |
| `D2Client.dll` | ~2.1 MB | Client state, UI, local player prediction, automap |
| `D2Net.dll` | ~180 KB | TCP/UDP socket layer, packet queue, serialization |
| `D2Common.dll` | ~1.8 MB | Shared data tables, stat engine, item factory |
| `D2Lang.dll` | ~96 KB | .tbl string table loading and locale lookup |
| `D2Win.dll` | ~320 KB | Window creation, input, DirectDraw surface |
| `D2Gfx.dll` | ~260 KB | Renderer abstraction (Software / Glide / DirectX8) |
| `D2Sound.dll` | ~440 KB | Audio engine, .wav streaming, DirectSound |
| `D2CMP.dll` | ~160 KB | DC6/DCC sprite decompression and caching |
| `Fog.dll` | ~200 KB | Memory pools, file I/O, debug logging, HANDLE abstraction |
| `Storm.dll` | ~340 KB | MPQ v1/v2 archive reader (Blizzard's own Storm library) |
| `BNClient.dll` | ~480 KB | Battle.net auth, CD-key, MCP/BNCS chat protocol |

> **v1.14d change:** All DLLs merged into a single `Diablo II.exe`. All offsets become
> relative to that single base. See `references/function-offsets.md` for the 1.14d table.

### Calling Convention Identification

```
Prologue                               Convention    Stack cleanup
─────────────────────────────────────────────────────────────────
push ebp / mov ebp, esp + ret          __stdcall     callee (ret N)
push ebp / mov ebp, esp + no ret N    __cdecl       caller (add esp,N)
mov [esp-4], ecx at prologue top       __fastcall    callee; ecx=arg1, edx=arg2
push ecx; ecx used as "this"           __thiscall    callee; Blizzard OOP vtables
```

**Golden rule:** Internal helpers → `__fastcall`. Exported / callbacks → `__stdcall`.
When `__fastcall`, the second parameter in C reconstruction is always `int _edx`
(a dummy to consume the edx register that D2 doesn't use).

### Initialization Sequence

```
Diablo II.exe
 └─ Storm.dll       ← MPQ subsystem first
 └─ Fog.dll         ← Memory pools initialized here
 └─ D2Win.dll       ← Window + DirectDraw surface
 └─ D2Gfx.dll       ← Renderer backend selected
 └─ D2CMP.dll       ← Sprite cache init
 └─ D2Sound.dll     ← Audio
 └─ D2Lang.dll      ← String tables loaded from MPQ
 └─ D2Common.dll    ← Data tables parsed (weapons/armor/skills/etc.)
 └─ BNClient.dll    ← Only for Battle.net games
 └─ D2Net.dll       ← Only for multiplayer modes
 └─ D2Game.dll      ← Server logic (SP + host modes)
 └─ D2Client.dll    ← Always last; starts game loop
```

---

## 2. Core Data Structures

### 2.1 UnitAny — The Universal Entity

Every entity in the game is a `UnitAny`. This is the single most important struct.

```c
/* D2Common.dll — verified field offsets for v1.13c (32-bit) */

typedef enum UnitType {
    UNIT_PLAYER  = 0,
    UNIT_MONSTER = 1,
    UNIT_OBJECT  = 2,
    UNIT_MISSILE = 3,
    UNIT_ITEM    = 4,
    UNIT_TILE    = 5,
} UnitType;

typedef struct UnitAny {
    DWORD            dwType;         // 0x00 — UnitType
    DWORD            dwClassId;      // 0x04 — row index into class data table
    DWORD            dwMode;         // 0x08 — current animation mode enum
    DWORD            dwUnitId;       // 0x0C — runtime GUID (unique per session)
    DWORD            dwAct;          // 0x10 — act index 0–4
    struct ActMisc*  pAct;           // 0x14 — act-level data pointer
    DWORD            dwSeed[2];      // 0x18 — unit RNG seed pair
    DWORD            dwInitSeed;     // 0x20 — original spawn seed
    union {                          // 0x24 — type-specific extended data
        struct PlayerData*  pPlayerData;
        struct MonsterData* pMonsterData;
        struct ObjectData*  pObjectData;
        struct MissileData* pMissileData;
        struct ItemData*    pItemData;
    };
    DWORD            _unk_28[8];     // 0x28–0x44
    struct StatList* pStatList;      // 0x48 — stat block linked list head
    struct Inventory*pInventory;     // 0x4C — inventory/stash/belt grid
    struct Path*     pPath;          // 0x50 — position and movement
    DWORD            _unk_54[4];     // 0x54
    DWORD            dwGfxFrame;     // 0x64 — current animation frame index
    DWORD            dwFrameRemain;  // 0x68 — frames remaining in current anim
    WORD             wFrameRate;     // 0x6C — animation speed divisor
    WORD             _pad0;
    DWORD*           pGfxUnk;        // 0x70
    struct GfxData*  pGfxData;       // 0x74 — sprite and palette data
    struct Light*    pLight;         // 0x78 — dynamic light source
    DWORD            dwHoverTextId;  // 0x7C — string table ID for hover name
    DWORD            _unk_80;
    struct Info*     pInfo;          // 0x84 — type-specific metadata
    DWORD            _unk_88[6];
    struct Dungeon*  pDungeon;       // 0xA0 — server-only dungeon context
    struct UnitAny*  pRoomNext;      // 0xA4 — next unit in same Room1
    DWORD            dwNextTime;     // 0xA8 — tick for next AI action
    DWORD            dwOwnerType;    // 0xAC — UnitType of summoner/thrower
    DWORD            dwOwnerGuid;    // 0xB0 — dwUnitId of summoner/thrower
    DWORD            _unk_B4[2];
    struct Skill*    pSkills;        // 0xBC — skill linked list head
    struct Events*   pEvents;        // 0xC0 — queued event callbacks
    DWORD            _unk_C4;
    DWORD            dwFlags;        // 0xC8 — UNITFLAG_* bitmask
    DWORD            dwFlags2;       // 0xCC — extended flags
    DWORD            _unk_D0[4];
    struct UnitAny*  pTimerNext;     // 0xE0 — next in timer list
    DWORD            dwTickCount;    // 0xE4 — frames unit has been alive
    struct UnitAny*  pListNext;      // 0xE8 — next in unit hash bucket
    DWORD            dwDropItemCode; // 0xEC — forced drop code (0 = random)
} UnitAny; /* sizeof ~= 0xF4 */

/* Unit state flag bitmasks */
#define UNITFLAG_DEAD           0x00000001
#define UNITFLAG_NODRAW         0x00000010
#define UNITFLAG_NOHIT          0x00000020
#define UNITFLAG_UNFINDABLE     0x00000080
#define UNITFLAG_BOSS           0x01000000
#define UNITFLAG_CHAMPION       0x02000000
#define UNITFLAG_UNIQUE         0x04000000
#define UNITFLAG_MINION         0x08000000
#define UNITFLAG_GHOSTLY        0x10000000
```

### 2.2 PlayerData, MonsterData, ItemData

```c
typedef struct PlayerData {
    char    szName[16];           // 0x00 — character name, null-padded
    struct  QuestData* pQuests;   // 0x10 — quest flags per act per difficulty
    struct  WaypointData* pWps;   // 0x14 — waypoint activation bitmask
    DWORD   dwPlayerClass;        // 0x18 — 0=Amz 1=Nec 2=Bar 3=Sor 4=Pal 5=Dru 6=Asn
    BYTE    bAct;                 // 0x1C — furthest act reached
    BYTE    bProgression;         // 0x1D — quest step
    BYTE    bDifficulty;          // 0x1E — 0=Normal 1=NM 2=Hell
    BYTE    _pad;
    DWORD   dwCharFlags;          // 0x20 — hardcore/expansion/ladder bits
    struct  HirelingData* pMerc;  // 0x24 — mercenary unit back-ref (NULL if none)
    DWORD   dwSummonGuid;         // 0x28 — current golem/revive GUID
} PlayerData;

typedef struct MonsterData {
    struct  MonStats* pMonStats;  // 0x00 — pointer into monstats.txt row
    BYTE    _unk[9];
    BYTE    bBossFlags;           // 0x0D — boss/champion type bitmask
    WORD    wUniqueNo;            // 0x0E — superuniques.txt index (0 = not unique)
    BYTE    bLastMode;            // 0x10
    DWORD   dwDamageRngSeed;      // 0x14 — separate RNG seed for damage rolls
    BYTE    bPathSeed;            // 0x18 — random walk variation seed
    BYTE    bMonType;             // 0x19 — 0=normal 1=champion 2=unique 3=minion
    BYTE    bSpecialFlags;        // 0x1A — extra modifier flags
    BYTE    _pad;
    WORD    wEquip[9];            // 0x1C — equipped item class IDs
    DWORD   dwNameSeed;           // 0x2E — procedural name generation seed
    BYTE    bNameId;              // 0x32 — name table index
} MonsterData;

typedef struct ItemData {
    DWORD   dwQuality;            // 0x00 — ITEMQUAL_* enum
    DWORD   dwSeed;               // 0x04 — item RNG seed (determines all affixes)
    DWORD   dwInitSeed;           // 0x08 — original creation seed
    DWORD   dwItemFlags;          // 0x0C — ITEMFLAG_* bitmask
    DWORD   dwItemFlags2;         // 0x10
    struct  ItemData* pNextItem;  // 0x14 — next item in inventory linked list
    WORD    wVersion;             // 0x18 — save format version
    WORD    wInvRow;              // 0x1A — row in inventory grid
    WORD    wInvCol;              // 0x1C — column
    BYTE    bBodyLoc;             // 0x1E — equipped body slot (0 = not equipped)
    BYTE    bStoreLoc;            // 0x1F — STORELOC_INV/STASH/CUBE/BELT
    DWORD   dwEar;                // 0x20 — ear data if this is a player ear
    BYTE    bInvGfxIdx;           // 0x24 — inventory tile graphic index
    BYTE    bNumSocketsFilled;    // 0x25 — number of gems/runes currently socketed
    BYTE    _unk[2];
    DWORD   dwILvl;               // 0x28 — item level (governs affix tier access)
    WORD    wMagicPrefix;         // 0x2C — magic prefix table ID
    WORD    wMagicSuffix;         // 0x2E — magic suffix table ID
    WORD    wRarePrefix;          // 0x30 — rare prefix name ID
    WORD    wRareSuffix;          // 0x32
    WORD    wSetCode;             // 0x34 — set this item belongs to
    WORD    wUniqueCode;          // 0x36 — unique item ID in UniqueItems.txt
    DWORD   dwRunewordId;         // 0x38 — runeword if applicable
    DWORD   dwPersonalization;    // 0x3C — personalized name CRC
} ItemData;

typedef enum ItemQuality {
    ITEMQUAL_INFERIOR  = 1,
    ITEMQUAL_NORMAL    = 2,
    ITEMQUAL_SUPERIOR  = 3,
    ITEMQUAL_MAGIC     = 4,
    ITEMQUAL_SET       = 5,
    ITEMQUAL_RARE      = 6,
    ITEMQUAL_UNIQUE    = 7,
    ITEMQUAL_CRAFT     = 8,
} ItemQuality;

#define ITEMFLAG_IDENTIFIED    0x00000010
#define ITEMFLAG_SOCKETED      0x00000800
#define ITEMFLAG_EAR           0x00001000
#define ITEMFLAG_COMPACT       0x00020000  /* no extended data block */
#define ITEMFLAG_ETHEREAL      0x00400000
#define ITEMFLAG_PERSONALIZED  0x01000000
#define ITEMFLAG_RUNEWORD      0x04000000
```

### 2.3 Path, Room1, Room2, Level

```c
typedef struct Path {
    WORD    wPosX;            // 0x00 — tile-precise X
    WORD    _p0;
    WORD    wPosY;            // 0x04
    WORD    _p1;
    WORD    wTargetX;         // 0x08 — walk/run destination X
    WORD    wTargetY;         // 0x0A
    WORD    wDeltaX;          // 0x0C — sub-tile X offset (fine movement)
    WORD    wDeltaY;          // 0x0E
    struct  Room1* pRoom1;    // 0x14 — current room
    struct  Room1* pRoomNext; // 0x18 — room being transitioned to
    WORD    wPrePosX;         // 0x1C — last-tick position (for interpolation)
    WORD    wPrePosY;         // 0x1E
    DWORD   _unk;
    struct  UnitAny* pUnit;   // 0x28 — owning unit back-pointer
    DWORD   dwFlags;          // 0x2C — PATHFLAG_* bitmask
    DWORD   dwCollisionFlags; // 0x34 — what this unit can pass through
    DWORD   dwPathType;       // 0x38 — 0=player 1=monster 2=missile
} Path;

#define PATHFLAG_MOVING         0x01
#define PATHFLAG_RUNNING        0x02
#define PATHFLAG_COLLIDE_UNITS  0x04
#define PATHFLAG_COLLIDE_WALLS  0x08

typedef struct Room2 {
    struct  Room2**  pRooms;      // 0x00 — connected Room2 array
    DWORD   dwRoomsNear;          // 0x04
    struct  DRLGRoom* pDRLGRoom;  // 0x08
    struct  Level*   pLevel;      // 0x0C — parent level
    DWORD*  pPresetUnits;         // 0x10 — preset unit spawn data
    DWORD   dwPresetCount;        // 0x14
    WORD    wPosX;                // 0x18 — room origin in level tiles
    WORD    wPosY;
    WORD    wSizeX;               // 0x1C — room dimensions in tiles
    WORD    wSizeY;
    struct  Room1*   pRoom1;      // 0x20 — runtime counterpart (NULL if unloaded)
} Room2;

typedef struct Room1 {
    struct  Room1**  pRoomsNear;  // 0x00 — adjacent rooms
    DWORD   dwRoomsNear;          // 0x04
    struct  DRLGRoom* pDRLGRoom;  // 0x08
    DWORD*  pCollMap;             // 0x0C — collision bitmask (1 bit/sub-tile)
    DWORD   _unk1[3];
    struct  UnitAny* pUnitFirst;  // 0x1C — first unit in this room
    DWORD   _unk2;
    struct  Room2*   pRoom2;      // 0x24 — design counterpart
    struct  ActMisc* pAct;        // 0x28
    DWORD   _unk3[5];
    struct  UnitAny* pMonFirst;   // 0x40 — first monster shortcut
    struct  UnitAny* pObjFirst;   // 0x44
    struct  UnitAny* pItemFirst;  // 0x48
    DWORD   dwSeed;               // 0x4C — room RNG seed
} Room1;
```

### 2.4 Skill and Aura Structs

```c
typedef struct Skill {
    struct  SkillInfo* pSkillInfo;  // 0x00 — row pointer into skills.txt data
    struct  Skill*     pNext;       // 0x04 — next skill in unit's list
    DWORD   dwSkladId;              // 0x08 — skill ID (skills.txt row index)
    DWORD   dwLevel;                // 0x0C — hard points invested
    DWORD   dwQuantity;             // 0x10 — current charges
    DWORD   dwQuantityMax;          // 0x14 — max charges
    DWORD   _unk;
    DWORD   dwFlags;                // 0x1C — SKILLFLAG_*
    struct  StatList* pStatList;    // 0x20 — level-scaled bonus stats
} Skill;

typedef struct Aura {
    struct  Aura*      pNext;       // 0x00
    DWORD   dwSkillId;              // 0x04 — originating skill ID
    DWORD   dwLevel;                // 0x08 — effective skill level
    struct  UnitAny*   pSource;     // 0x0C — caster
    DWORD   dwRadius;               // 0x10 — radius in sub-tiles
    DWORD   dwFlags;                // 0x14 — AURAFLAG_*
    DWORD   dwExpire;               // 0x18 — tick when aura expires (0=permanent)
    struct  StatList*  pAuraStats;  // 0x1C — stats applied to affected units
} Aura;
```

---

## 3. Memory Subsystem

`Fog.dll` implements a slab/pool allocator with 10 predefined size classes.
ALL D2 allocations go through this — never assume raw malloc/free.

```c
#define FOG_POOL_UNIT       0   // UnitAny allocations
#define FOG_POOL_INVENTORY  1   // Inventory grids
#define FOG_POOL_ITEM       2   // ItemData
#define FOG_POOL_STATLIST   3   // StatList + StatEx arrays
#define FOG_POOL_PATH       4   // Path structs
#define FOG_POOL_SKILL      5   // Skill nodes
#define FOG_POOL_ROOM       6   // Room1/Room2
#define FOG_POOL_DRLG       7   // DRLG scratch buffers
#define FOG_POOL_GENERAL    8   // General <256 bytes
#define FOG_POOL_LARGE      9   // Allocations >256 bytes

/* Fog.dll+0x10B40 (v1.13c) */
void* __fastcall Fog_AllocPool(DWORD dwSize, DWORD dwPool,
                                const char* pszFile, DWORD dwLine);
/* Fog.dll+0x10B60 (v1.13c) */
void  __fastcall Fog_FreePool(void* pMem, DWORD dwPool);

#define D2ALLOC(sz, pool) Fog_AllocPool((sz),(pool),__FILE__,__LINE__)
#define D2FREE(ptr, pool) Fog_FreePool((ptr),(pool))

/* Unit hash table — D2Client.dll+0x11C2E0 (v1.13c) */
/* 6 types × 128 buckets. Lookup: bucket = dwUnitId & 0x7F */
extern UnitAny* g_UnitHashTables[6][128];

UnitAny* D2Common_GetUnitFromId(DWORD dwUnitId, DWORD dwUnitType) {
    if (dwUnitType > UNIT_TILE) return NULL;
    UnitAny* p = g_UnitHashTables[dwUnitType][dwUnitId & 0x7F];
    while (p) {
        if (p->dwUnitId == dwUnitId) return p;
        p = p->pListNext;
    }
    return NULL;
}
```

---

## 4. RNG System

D2 uses two PRNGs with distinct responsibilities.

### 4.1 LCG — Item/Monster/Map Seeds

```c
/* D2Common.dll+0x1B1A0 (v1.13c) */
DWORD D2_LCG_Next(DWORD* pSeed) {
    *pSeed = (*pSeed * 0x6AC690C5) + 1;
    return *pSeed;
}
DWORD D2_LCG_Range(DWORD* pSeed, DWORD dwMax) {
    if (!dwMax) return 0;
    return D2_LCG_Next(pSeed) % dwMax;  /* intentionally biased */
}
```

### 4.2 Blizzard Game Rand — Per-Tick Decisions

```c
/* D2Game.dll+0x1A120 (v1.13c) — AI rolls, hit chance, proc triggers */
static DWORD s_GameRandSeed = 0;
DWORD D2Game_Rand(DWORD dwMax) {
    s_GameRandSeed = (s_GameRandSeed * 0x343FD) + 0x269EC3;
    DWORD r = (s_GameRandSeed >> 16) & 0x7FFF;
    return dwMax ? r % dwMax : r;
}
void D2Game_SeedRand(DWORD dwSeed) { s_GameRandSeed = dwSeed; }
```

### 4.3 Item Seed Determinism

Item affixes are 100% reproducible from `ItemData.dwSeed`. Two LCG calls per affix:
one for tier selection, one for the specific affix within that tier. The seed is
stored back after each roll, so the full affix sequence is a pure function of the
original seed value.

---

## 5. DRLG Map Generation

See `references/drlg-map-gen.md` for the full deep-dive.

### Three Generator Types

| Type | Example Levels | Algorithm |
|---|---|---|
| `DRLG_PRESET` | Towns, Tristram, Arcane Sanctuary | Fixed tile layout, deterministic placement |
| `DRLG_MAZE` | Catacombs, Caves, Dungeons | Recursive BSP room partitioning |
| `DRLG_OUTDOOR` | Act 1/2/3 wilderness areas | Grid stamp selection and blending |

### Key DRLG Struct

```c
typedef struct DRLGRoom {
    DWORD   dwPosX, dwPosY;       // room origin in tiles
    DWORD   dwSizeX, dwSizeY;     // room dimensions in tiles
    BYTE*   pSubTileFlags;        // collision flags per sub-tile (5×5 per tile)
    DWORD   dwSubTileSizeX;       // dwSizeX * 5
    DWORD   dwSubTileSizeY;       // dwSizeY * 5
    struct  DRLGRoom* pNext;      // linked list
    DWORD   dwDRLGType;           // DRLG_PRESET=0 DRLG_OUTDOOR=1 DRLG_MAZE=2
    DWORD   dwFlags;
} DRLGRoom;

/* Sub-tile collision flag bits */
#define SUBTILE_WALK        0x0000   // walkable, no obstruction
#define SUBTILE_BLOCK_WALK  0x0001   // wall / solid obstruction
#define SUBTILE_BLOCK_LOS   0x0002   // blocks line-of-sight
#define SUBTILE_BLOCK_JUMP  0x0004   // blocks teleport/leap landing
#define SUBTILE_PLAYER_WALK 0x0008   // walk ok, blocks LOS (fences)
#define SUBTILE_BLOCK_LIGHT 0x0020   // blocks dynamic light
```

---

## 6. Pathfinding and Collision

D2 uses an A* variant on the sub-tile grid (5×5 sub-tiles per map tile).

```c
/* D2Game.dll+0x2B8A0 (v1.13c) */
BOOL D2Game_PathFind(UnitAny* pUnit, WORD wDstX, WORD wDstY, DWORD dwFlags);

/* D2Game.dll+0x6D2F0 (v1.13c) */
BOOL D2Game_CheckMissileCollide(UnitAny* pMissile, WORD wNewX, WORD wNewY);

/* Line-of-sight check between two map coordinates */
/* D2Common.dll+0x78B40 (v1.13c) */
BOOL D2Common_CheckLOS(Room1* pRoom, WORD x1, WORD y1, WORD x2, WORD y2);
```

---

## 7. Item Generation Pipeline

See `references/item-generation.md` for the complete 6-stage pipeline with all formulas.

### Quick Overview

```
1. TreasureClass recursion (tc.txt) → base item selection
2. Item level: iLvl = min(mlvl + bonus, alvl × 2)
3. Quality roll: Unique → Set → Rare → Magic → Superior → Normal → Inferior
4. Affix selection: filter by iLvl ≥ affix.level AND type compatibility
5. Unique/Set match lookup → downgrade to rare if iLvl < req
6. Socket/Ethereal/Personalization rolls
```

### Magic Find Formula

```c
/* Diminishing returns applied per quality tier */
DWORD CalcEffectiveMF(DWORD dwRawMF, DWORD dwQuality) {
    switch (dwQuality) {
        case ITEMQUAL_UNIQUE: return (dwRawMF * 250) / (dwRawMF + 250);
        case ITEMQUAL_SET:    return (dwRawMF * 500) / (dwRawMF + 500);
        case ITEMQUAL_RARE:   return (dwRawMF * 600) / (dwRawMF + 600);
        default:              return dwRawMF;  /* magic: no DR */
    }
}
```

---

## 8. Stat and Combat Engine

See `references/combat-formulas.md` for all formulas with proofs.

### GetUnitStat (The Stat API)

```c
/* D2Common.dll+0x63990 (v1.13c) — retrieve any stat from any unit */
/* This is called thousands of times per second; extremely hot path */
DWORD __fastcall D2Common_GetUnitStat(UnitAny* pUnit, int _edx,
                                       WORD wStatId, WORD wSubIndex) {
    /* Walks pUnit->pStatList chain summing all matching StatEx entries */
    /* Sub-index used for skill-specific stats (charged/per-skill bonuses) */
    DWORD total = 0;
    StatList* pList = pUnit->pStatList;
    while (pList) {
        for (WORD i = 0; i < pList->wNumStats; i++) {
            StatEx* s = &pList->pStats[i];
            if (s->wStatId == wStatId &&
                (wSubIndex == 0 || s->wSubIndex == wSubIndex))
                total += s->dwValue;
        }
        pList = pList->pNext;
    }
    return total;
}
```

### Attack Resolution

```c
/* D2Game.dll+0x5A3B0 (v1.13c) — simplified hit chance */
BOOL D2Game_ResolveAttack(UnitAny* pAtk, UnitAny* pDef) {
    DWORD AR  = D2Common_GetUnitStat(pAtk, 0, STAT_ATTACKRATING, 0);
    DWORD DEF = D2Common_GetUnitStat(pDef, 0, STAT_ARMOR, 0);
    DWORD aLv = D2Common_GetUnitStat(pAtk, 0, STAT_LEVEL, 0);
    DWORD dLv = D2Common_GetUnitStat(pDef, 0, STAT_LEVEL, 0);
    /* Formula: ChanceToHit% = AR/(AR+DEF) × 2×aLv/(aLv+dLv) × 100 */
    /* Clamped [5%, 95%] */
    DWORD pct = (AR + DEF == 0) ? 95 :
                (DWORD)(((UINT64)AR * 2 * aLv * 100) / ((AR + DEF) * (aLv + dLv)));
    pct = max(5, min(95, pct));
    return D2Game_Rand(100) < pct;
}
```

### Experience Formula

```c
/* D2Common — XP needed for level N (pre-computed table, this is the generator) */
/* Level cap: 99. XP for 99 = 3,520,485,254 */
DWORD D2_XPForLevel(DWORD dwLevel) {
    if (dwLevel <= 1) return 0;
    DWORD prev = D2_XPForLevel(dwLevel - 1);
    /* Increment = floor(prev^1.15) with class multiplier */
    return prev + (DWORD)powf((float)prev, 1.15f);
}
```

---

## 9. Monster AI State Machine

See `references/ai-states.md` for the full AI code table (300 entries).

```c
typedef void (__fastcall *MonsterAI_Fn)(UnitAny* pMon, int _edx, struct AIParam* pP);
extern MonsterAI_Fn g_AITable[300]; /* D2Game.dll+0x11A200 (v1.13c) */

/* Called every tick at 25 Hz for each monster in loaded rooms */
void D2Game_MonsterAI_Tick(UnitAny* pMon) {
    DWORD ai = pMon->pMonsterData->pMonStats->dwAiCode;
    if (ai < 300 && g_AITable[ai])
        g_AITable[ai](pMon, 0, &pMon->pMonsterData->aiParam);
}

/* Monster animation modes */
typedef enum MonsterMode {
    MM_DEATH=0, MM_SEQUENCE=1, MM_WALK=2, MM_GETHIT=3,
    MM_ATTACK1=4, MM_ATTACK2=5, MM_BLOCK=6, MM_CAST=7,
    MM_SKILL1=8, MM_SKILL2=9, MM_SKILL3=10, MM_SKILL4=11,
    MM_DEAD=12,  MM_KNOCK=13, MM_STUN=14, MM_STAND=15,
    MM_SPAWN=16, MM_RUN=17,   MM_RETREAT=18, MM_RESURRECT=19,
} MonsterMode;

/* Boss modifier bitmask */
#define BOSSMOD_EXTRA_STRONG      (1<<0)
#define BOSSMOD_EXTRA_FAST        (1<<1)
#define BOSSMOD_CURSED            (1<<2)  /* Amplify Damage aura */
#define BOSSMOD_MAGIC_RESISTANT   (1<<3)  /* 75% all resists */
#define BOSSMOD_FIRE_ENCHANTED    (1<<4)  /* fire aura + extra fire damage */
#define BOSSMOD_LIGHTNING_ENCHANTED (1<<5)
#define BOSSMOD_COLD_ENCHANTED    (1<<6)  /* nova on death */
#define BOSSMOD_MANA_BURN         (1<<7)  /* drains mana on hit */
#define BOSSMOD_TELEPORT          (1<<8)  /* random teleport behavior */
#define BOSSMOD_SPECTRAL_HIT      (1<<9)  /* random element per hit */
#define BOSSMOD_STONE_SKIN        (1<<10) /* extreme defense */
#define BOSSMOD_MULTIPLE_SHOTS    (1<<11) /* ranged: 3 simultaneous */
#define BOSSMOD_AURA_ENCHANTED    (1<<12) /* has paladin aura */
```

---

## 10. Skill / Aura / Missile System

See `references/skill-system.md` for the complete skill execution tree.

### Execution Flow

```
Client sends packet 0x0C (RightSkillOnLocation)
 └─ D2Game_ProcessClientPacket()
     └─ D2Game_UseSkill(pPlayer, skillId, tx, ty, pTarget)
         ├─ CheckManaReq → drain mana
         ├─ StartCastAnimation
         └─ SkillFuncTable[skillId](pPlayer, pSkill, tx, ty, pTarget)
             ├─ Projectile → D2Game_CreateMissile(...)
             ├─ AoE effect → D2Game_AreaEffect(...)
             ├─ Aura      → D2Game_AddAura(pPlayer, auraId, level)
             └─ Summon    → D2Game_SpawnMonster(classId, tx, ty)
```

### Missile Creation

```c
/* D2Game.dll+0x7A3C0 (v1.13c) */
UnitAny* __fastcall D2Game_CreateMissile(
    UnitAny* pOwner, int _edx,
    DWORD    dwMissileId,
    WORD     wSrcX,  WORD wSrcY,
    WORD     wDstX,  WORD wDstY,
    DWORD    dwParam             /* skill level or extra data */
);
```

### Aura Pulse (Called Every Tick)

```c
/* D2Game.dll+0x6E800 (v1.13c) */
void D2Game_AuraPulse(UnitAny* pSource) {
    /* Iterates all units in pSource room + adjacent rooms */
    /* For each unit within aura radius: apply aura StatList */
    /* Removes stats when unit leaves radius next tick */
}
```

---

## 11. Event and Timer System

```c
typedef enum D2EventId {
    EVENT_DEATH=0x01, EVENT_ENDOFLIFE=0x02, EVENT_CHANGING_LEVEL=0x03,
    EVENT_INIT=0x04, EVENT_ATTACKED=0x05, EVENT_FIREHIT=0x06,
    EVENT_GETHIT=0x07, EVENT_LEVELUP=0x08, EVENT_SKILL=0x09,
    EVENT_KILL=0x0A, EVENT_PLAYERKILL=0x0B, EVENT_CORPSE=0x0C,
    EVENT_MISSILEHIT=0x0E, EVENT_ACTIVATE=0x10,  /* shrine/object */
    EVENT_QUESTITEM=0x11, EVENT_PROGRESSQUEST=0x12,
} D2EventId;

typedef void (__fastcall *EventCallback)(UnitAny* pUnit, int _edx, void* pData);

typedef struct Events {
    EventCallback callbacks[0x30];  /* one slot per EventId */
    DWORD         dwRegistered;     /* bitmask of registered IDs */
} Events;

/* D2Game.dll+0x2A480 (v1.13c) */
void D2Game_RegisterEvent(UnitAny* pUnit, D2EventId eId, EventCallback pfn);
/* D2Game.dll+0x2A390 (v1.13c) */
void D2Game_TriggerEvent(UnitAny* pUnit, D2EventId eId, void* pData);
```

---

## 12. Inventory Grid System

```c
typedef struct Inventory {
    DWORD            dwSignature;   // 0x00 — 0xA55A5AA5
    struct ItemData* pFirstItem;    // 0x04 — item linked list head
    struct GridEntry*pGridData;     // 0x08 — cell occupancy array
    WORD             wGridWidth;    // 0x0C
    WORD             wGridHeight;   // 0x0E
    struct UnitAny*  pOwner;        // 0x10
    DWORD            dwGold;        // 0x14
} Inventory;

/* Body slot constants */
#define BODYLOC_NONE   0
#define BODYLOC_HEAD   1   /* Helmet */
#define BODYLOC_NECK   2   /* Amulet */
#define BODYLOC_TORSO  3   /* Armor */
#define BODYLOC_RARM   4   /* Right hand (weapon) */
#define BODYLOC_LARM   5   /* Left hand (shield) */
#define BODYLOC_RRING  6
#define BODYLOC_LRING  7
#define BODYLOC_BELT   8
#define BODYLOC_FEET   9
#define BODYLOC_GLOVES 10
#define BODYLOC_RARM2  11  /* Weapon switch slot */
#define BODYLOC_LARM2  12

/* D2Common.dll+0x56AC0 (v1.13c) */
BOOL D2Common_InsertItemInGrid(Inventory* pInv, UnitAny* pItem, WORD wCol, WORD wRow);

/* D2Common.dll+0x56B80 (v1.13c) */
BOOL D2Common_FindItemSlot(Inventory* pInv, UnitAny* pItem, WORD* pCol, WORD* pRow);
```

---

## 13. Network Protocol Architecture

See `references/packets.md` for ~180 full packet structs.
D2 uses raw TCP on port 4000 (game server) and 6112 (Battle.net relay).

```c
/* Server packet dispatch table — D2Client.dll+0x9F200 (v1.13c) */
typedef void (__stdcall *PacketHandler)(UnitAny* pPlayer, BYTE* pData, DWORD dwLen);
extern PacketHandler g_SPacketTable[0x100];  /* 256 server→client handlers */
extern PacketHandler g_CPacketTable[0x80];   /* 128 client→server handlers */

/* D2Net packet header — sequence/ack for reliable ordering */
#pragma pack(push,1)
typedef struct D2NetHeader {
    WORD  wSeqNum;   /* monotonically increasing */
    WORD  wAckNum;   /* last received seq from peer */
    BYTE  bCmd;      /* packet command byte */
} D2NetHeader;
#pragma pack(pop)

/* D2Net.dll+0x70A0 (v1.13c) — send raw packet data */
BOOL __fastcall D2Net_SendPacket(DWORD dwLen, int _edx, void* pData);

/* Hook example — intercept all WalkToLocation packets */
void __stdcall hk_C_WalkToLocation(UnitAny* pPlayer, BYTE* pData, DWORD dwLen) {
    WORD* pos = (WORD*)(pData + 1);
    LogPrintf("Walk: player=%s dest=(%d,%d)", pPlayer->pPlayerData->szName, pos[0], pos[1]);
    /* Call original handler */
    g_CPacketTable[0x01](pPlayer, pData, dwLen);
}
```

---

## 14. Rendering Pipeline

D2Gfx.dll provides a fully abstracted renderer with three backends.

```c
/* Renderer vtable (D2Gfx.dll internal) */
typedef struct D2GfxRenderer {
    void (__stdcall *Init)(HWND hWnd, DWORD dwW, DWORD dwH);
    void (__stdcall *Shutdown)(void);
    void (__stdcall *BeginScene)(void);
    void (__stdcall *EndScene)(void);
    void (__stdcall *DrawSprite)(DWORD x, DWORD y, struct DC6Frame* pFrame,
                                  DWORD dwPaletteId, BYTE bTransMode);
    void (__stdcall *SetPalette)(BYTE* pPalette, DWORD dwPaletteId);
    void (__stdcall *FlipScreen)(void);
} D2GfxRenderer;

extern D2GfxRenderer* g_pActiveRenderer; /* D2Gfx.dll+0x11300 (v1.13c) */

/* Transparency blend modes */
#define TRANSMODE_NONE      0   /* fully opaque */
#define TRANSMODE_25PCT     1   /* 25% — perspective shadows */
#define TRANSMODE_50PCT     2   /* 50% — bone armor, mana shield */
#define TRANSMODE_75PCT     3
#define TRANSMODE_ADDITIVE  4   /* additive — lightning, fire, auras */
#define TRANSMODE_SCREEN    5   /* screen blend — aura glow effects */
```

See `references/dcc-dc6-format.md` for DC6/DCC binary format specifications.

---

## 15. Binary File Formats

### .d2s Save File Layout

See `references/d2s-format.md` for byte-exact field documentation.

```
Offset  Size  Field
──────────────────────────────────────────────────────────────────────
0x00    4     Magic: 0xAA55AA55
0x04    4     Version: 96 (v1.10+)
0x08    4     File size
0x0C    4     Checksum (CRC, field zeroed during calculation)
0x10    4     Active weapon slot (0 or 1)
0x14    16    Character name (ASCII, null-padded)
0x24    1     Status flags (bit2=hardcore, bit3=dead, bit5=expansion)
0x28    1     Character class (0=Amz 1=Nec 2=Bar 3=Sor 4=Pal 5=Dru 6=Asn)
0x2B    1     Level
0x2C    4     Created (Unix timestamp)
0x30    4     Last played (Unix timestamp)
0x38    64    Skill hotkeys (16 × DWORD skill IDs)
0x78    4     Left skill
0x7C    4     Right skill
0x80    4     Left skill (switch)
0x84    4     Right skill (switch)
0xA8    3     Difficulty bytes (Normal/NM/Hell progression)
0xAB    4     Map seed
0xB1    4     Mercenary GUID
0xBC    144   Unknown / padding
0x14C+  var   Quest data   [magic: "Woo!" 0x576F6F21]
  ...   var   Waypoints    [magic: "WS" 0x57530000]
  ...   var   NPC flags    [magic: 0x01 0x77]
  ...   var   Stats        [magic: "gf" 0x6766] — bitstream encoded
  ...   var   Skills       [magic: "if" 0x6966]
  ...   var   Items        [magic: "JM" 0x4A4D]
  ...   var   Corpse items [magic: "JM"]
  ...   var   Merc items   [magic: "jf" then "JM"]
  ...   var   Iron Golem   [Necromancer only]
```

### .DS1 and .DT1 Map Files

```c
/* DS1 = map layer data (which tiles go where) */
typedef struct DS1Header {
    DWORD dwVersion;      /* 2–18 depending on act/patch */
    DWORD dwWidth;        /* map width in tiles, minus 1 */
    DWORD dwHeight;       /* map height in tiles, minus 1 */
    DWORD dwAct;          /* 0–4 */
    DWORD dwTagType;
    DWORD dwFileCount;    /* number of .dt1 tileset files referenced */
    /* null-terminated filenames follow (dwFileCount strings) */
    /* then: wall/floor/shadow/tag layer data */
} DS1Header;

/* DT1 = tile graphic data */
typedef struct DT1Header {
    DWORD dwVersion1;     /* 7 */
    DWORD dwVersion2;     /* 6 */
    BYTE  _unk[260];
    DWORD dwTileCount;
    DWORD dwTileOffset;   /* byte offset to TileHeader array */
} DT1Header;
```

---

## 16. Disassembly Methodology

### Tool Stack

```
Ghidra 11+         Free, excellent D2 community plugin support, scriptable in Python
IDA Pro 7.x        Best decompiler quality (Hex-Rays); expensive
x64dbg / OllyDbg   Dynamic analysis, live breakpoints, memory patching
Cheat Engine       Memory scanning, pointer chain tracing, struct dissection
Wireshark          Packet capture (filter: tcp.port == 4000 or tcp.port == 6112)
HxD / ImHex        Binary file inspection with template support
```

### Production Pattern Scanner

```c
typedef struct SigPattern {
    const char* szName;
    const BYTE* pBytes;
    const char* pMask;     /* 'x'=exact match, '?'=wildcard */
    DWORD       dwLen;
    INT         nOffset;   /* add to found address */
    DWORD       dwDeref;   /* dereference result N times */
} SigPattern;

DWORD ScanPattern(DWORD dwBase, DWORD dwSize, const SigPattern* pPat) {
    for (DWORD i = 0; i < dwSize - pPat->dwLen; i++) {
        BOOL bOk = TRUE;
        for (DWORD j = 0; j < pPat->dwLen && bOk; j++)
            if (pPat->pMask[j]=='x' && ((BYTE*)(dwBase+i))[j] != pPat->pBytes[j])
                bOk = FALSE;
        if (bOk) {
            DWORD r = dwBase + i + pPat->nOffset;
            for (DWORD d = 0; d < pPat->dwDeref; d++) r = *(DWORD*)r;
            return r;
        }
    }
    return 0;
}
```

### Version Auto-Detection

```c
DWORD D2_DetectVersion(void) {
    HMODULE hMod = GetModuleHandleA("D2Common.dll");
    if (!hMod) hMod = GetModuleHandle(NULL); /* v1.14d single exe */
    char szPath[MAX_PATH];
    GetModuleFileNameA(hMod, szPath, MAX_PATH);
    DWORD dummy, sz = GetFileVersionInfoSizeA(szPath, &dummy);
    if (!sz) return 0;
    void* pVer = alloca(sz);
    GetFileVersionInfoA(szPath, 0, sz, pVer);
    VS_FIXEDFILEINFO* pInfo;
    UINT uLen;
    VerQueryValueA(pVer, "\\", (void**)&pInfo, &uLen);
    /* Returns 0x0109=1.09 0x010C=1.12 0x010D=1.13c 0x010E=1.14d */
    return LOWORD(pInfo->dwFileVersionMS);
}
```

---

## 17. Hooking Framework

### Full Trampoline Hook with Restoration

```c
typedef struct Hook {
    void*  pTarget;
    void*  pDetour;
    void*  pTrampoline;
    BYTE   origBytes[16];
    DWORD  dwOrigLen;
    BOOL   bInstalled;
} Hook;

BOOL Hook_Install(Hook* pHook, void* pTarget, void* pDetour) {
    pHook->pTarget   = pTarget;
    pHook->pDetour   = pDetour;
    pHook->dwOrigLen = 5;
    memcpy(pHook->origBytes, pTarget, 5);

    /* Allocate executable trampoline */
    pHook->pTrampoline = VirtualAlloc(NULL, 32,
                          MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!pHook->pTrampoline) return FALSE;

    /* Trampoline = original 5 bytes + JMP back */
    BYTE* t = (BYTE*)pHook->pTrampoline;
    memcpy(t, pHook->origBytes, 5);
    t[5] = 0xE9;
    *(DWORD*)(t+6) = (DWORD)((BYTE*)pTarget+5) - (DWORD)(t+10);

    /* Write 5-byte JMP to detour over target */
    DWORD dwOld;
    VirtualProtect(pTarget, 5, PAGE_EXECUTE_READWRITE, &dwOld);
    BYTE patch[5] = {0xE9};
    *(DWORD*)(patch+1) = (DWORD)pDetour - (DWORD)pTarget - 5;
    memcpy(pTarget, patch, 5);
    VirtualProtect(pTarget, 5, dwOld, &dwOld);
    FlushInstructionCache(GetCurrentProcess(), pTarget, 5);
    pHook->bInstalled = TRUE;
    return TRUE;
}

void Hook_Remove(Hook* pHook) {
    if (!pHook->bInstalled) return;
    DWORD dwOld;
    VirtualProtect(pHook->pTarget, 5, PAGE_EXECUTE_READWRITE, &dwOld);
    memcpy(pHook->pTarget, pHook->origBytes, 5);
    VirtualProtect(pHook->pTarget, 5, dwOld, &dwOld);
    VirtualFree(pHook->pTrampoline, 0, MEM_RELEASE);
    pHook->bInstalled = FALSE;
}
```

### IAT (Import Address Table) Hook — More Stable for DLLs

```c
/* Hook a function via the IAT instead of patching code bytes */
/* More stable across patches because it doesn't depend on byte offsets */
BOOL IAT_Hook(const char* szModule, const char* szImportDll,
              const char* szFuncName, void* pDetour, void** ppOriginal) {
    HMODULE hMod = GetModuleHandleA(szModule);
    PIMAGE_DOS_HEADER pDOS = (PIMAGE_DOS_HEADER)hMod;
    PIMAGE_NT_HEADERS pNT  = (PIMAGE_NT_HEADERS)((BYTE*)hMod + pDOS->e_lfanew);
    DWORD iatRVA  = pNT->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    PIMAGE_IMPORT_DESCRIPTOR pImport = (PIMAGE_IMPORT_DESCRIPTOR)((BYTE*)hMod + iatRVA);

    while (pImport->Name) {
        char* szDll = (char*)((BYTE*)hMod + pImport->Name);
        if (_stricmp(szDll, szImportDll) == 0) {
            PIMAGE_THUNK_DATA pOrigThunk = (PIMAGE_THUNK_DATA)((BYTE*)hMod + pImport->OriginalFirstThunk);
            PIMAGE_THUNK_DATA pThunk     = (PIMAGE_THUNK_DATA)((BYTE*)hMod + pImport->FirstThunk);
            while (pOrigThunk->u1.Function) {
                PIMAGE_IMPORT_BY_NAME pName = (PIMAGE_IMPORT_BY_NAME)
                    ((BYTE*)hMod + pOrigThunk->u1.AddressOfData);
                if (strcmp((char*)pName->Name, szFuncName) == 0) {
                    *ppOriginal = (void*)pThunk->u1.Function;
                    DWORD dwOld;
                    VirtualProtect(&pThunk->u1.Function, sizeof(DWORD), PAGE_READWRITE, &dwOld);
                    pThunk->u1.Function = (DWORD)pDetour;
                    VirtualProtect(&pThunk->u1.Function, sizeof(DWORD), dwOld, &dwOld);
                    return TRUE;
                }
                pOrigThunk++; pThunk++;
            }
        }
        pImport++;
    }
    return FALSE;
}
```

### DLL Injection via CreateRemoteThread

```c
BOOL D2_InjectDLL(DWORD dwProcId, const char* szDllPath) {
    HANDLE hProc = OpenProcess(PROCESS_ALL_ACCESS, FALSE, dwProcId);
    if (!hProc) return FALSE;
    LPVOID pRemote = VirtualAllocEx(hProc, NULL, strlen(szDllPath)+1,
                                     MEM_COMMIT, PAGE_READWRITE);
    WriteProcessMemory(hProc, pRemote, szDllPath, strlen(szDllPath)+1, NULL);
    HANDLE hThread = CreateRemoteThread(hProc, NULL, 0,
        (LPTHREAD_START_ROUTINE)GetProcAddress(
            GetModuleHandleA("kernel32.dll"), "LoadLibraryA"),
        pRemote, 0, NULL);
    WaitForSingleObject(hThread, INFINITE);
    VirtualFreeEx(hProc, pRemote, 0, MEM_RELEASE);
    CloseHandle(hThread);
    CloseHandle(hProc);
    return TRUE;
}
```

---

## 18. Mod SDK Patterns

### D2Mod — Plugin Chain Loader

```c
/* Your mod DLL must export this function */
__declspec(dllexport) void __stdcall D2ModInit(void) {
    /* Called after all D2 DLLs are loaded — safe to hook here */
    DWORD base = (DWORD)GetModuleHandleA("D2Common.dll");
    Hook_Install(&g_GetUnitStatHook, (void*)(base + 0x63990), hk_GetUnitStat);
    Hook_Install(&g_SetUnitStatHook, (void*)(base + 0x63A00), hk_SetUnitStat);
}

__declspec(dllexport) void __stdcall D2ModShutdown(void) {
    Hook_Remove(&g_GetUnitStatHook);
    Hook_Remove(&g_SetUnitStatHook);
}
```

### D2BS / JavaScript Bridge

```javascript
// D2BS exposes D2 memory through a high-level JS API

// Access the local player unit
var me = getPlayerUnit();
print(me.name + " level " + me.charlvl + " at " + me.x + "," + me.y);
print("HP: " + me.hp + "/" + me.hpmax);

// Walk all units of a given type
var mon = getUnit(UNIT_MONSTER);
while (mon) {
    if (!mon.dead) {
        print(mon.name + " id=" + mon.gid + " hp=" + mon.hp + "/" + mon.hpmax);
        print("  flags: " + mon.spectype.toString(2));  // binary flags
    }
    mon = mon.getNext();
}

// Send a raw game packet
sendPacket(5, 0x0C, 0x54, 0,         // header (len=5, cmd=0x0C, skillHi, skillLo)
           0x08, 0x00,                 // targetX low/high bytes
           x & 0xFF, (x>>8) & 0xFF,   // x
           y & 0xFF, (y>>8) & 0xFF);  // y

// Print text in game chat
printToScreen("Hello from D2BS!", 4);  // color 4 = gold

// Game state flags
if (me.gameReady && me.area > 0) {
    print("In area: " + me.area + " (see levels.txt row " + me.area + ")");
}

// Iterate inventory items
var item = me.getItem();
while (item) {
    print(item.code + " ilvl=" + item.ilvl + " qual=" + item.quality);
    item = item.getNext();
}
```

### BaseMod — Config-Driven Patching

BaseMod uses an INI-based patch system for common modifications:

```ini
; BaseMod.ini — patch D2Common.dll to allow 8-player single player
[D2Common_Patch_1]
Address=0x58830
Bytes=08                  ; change max players from 08 to 08 (already 8 in MP)

[D2Common_Patch_2]
; Skip character name validation (allows special characters)
Address=0x1D9F0
Bytes=EB 3F               ; JMP short over validation block
```

---

## 19. D2R Resurrected Differences

| Aspect | Classic D2 | D2 Resurrected |
|---|---|---|
| Archive | MPQ v1/v2 | CASC (Content Addressable Storage) |
| Executable | Multiple DLLs | Single 64-bit exe |
| Renderer | DirectDraw / Glide / DX8 | DirectX 12 / Metal |
| Data format | Binary .bin compiled from .txt | JSON override files |
| Sprites | DC6 / DCC | DCC + new .anim container |
| Process | 32-bit | 64-bit (all pointers are QWORD) |
| Save format | .d2s local | .d2s + Blizzard cloud sync |
| Networking | D2Net custom TCP | Battle.net 2.0 relay |

### D2R CASC Access

```c
#include "CascLib.h"

HANDLE hStorage = NULL;
CascOpenStorage("C:\\Games\\Diablo II Resurrected", 0, &hStorage);

HANDLE hFile = NULL;
/* D2R paths: forward slashes, "data:" prefix, case-insensitive */
if (CascOpenFile(hStorage, "data:data/global/excel/weapons.txt",
                  CASC_LOCALE_ALL, 0, &hFile)) {
    DWORD sz, rd;
    CascGetFileSize(hFile, &sz);
    char* buf = malloc(sz + 1);
    CascReadFile(hFile, buf, sz, &rd);
    buf[rd] = '\0';
    CascCloseFile(hFile);
    free(buf);
}
CascCloseStorage(hStorage);
```

### D2R JSON Override System

```json
// <installdir>/mods/mymod/data/global/excel/weapons.txt.json
{
  "Weapons": [
    { "name": "Short Sword", "type": "swor", "mindam": 3, "maxdam": 12, "speed": 0 }
  ]
}
```

### D2R 64-bit Struct Differences

All pointer fields become QWORD (8 bytes) in D2R. The `UnitAny` struct is
significantly larger — when reconstructing D2R code, replace all `DWORD*` and
`struct Foo*` fields with `QWORD` or use the appropriate 64-bit pointer type.
Struct padding also changes — re-verify all field offsets against a live D2R process.

---

## 20. Python and Ghidra Tooling

### Python MPQ Extractor (`scripts/mpq_extract.py`)

```python
# Requires: pip install mpyq
# Usage: python scripts/mpq_extract.py <d2data.mpq> <output_dir>

import mpyq, os, sys, csv

def extract_all_tables(mpq_path, out_dir):
    archive = mpyq.MPQArchive(mpq_path)
    files = archive.files
    for f in files:
        if f.endswith(b'.txt') and b'excel' in f:
            data = archive.read_file(f.decode())
            name = f.decode().split('\\')[-1]
            with open(os.path.join(out_dir, name), 'wb') as fp:
                fp.write(data)
            print(f"Extracted {name}")

extract_all_tables(sys.argv[1], sys.argv[2])
```

### Python .d2s Bitstream Parser (`scripts/d2s_parser.py`)

```python
# D2 save files use a bit-packed format for stats and items
# This parser handles the bitstream section

class BitReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos  = 0  # bit position

    def read(self, n: int) -> int:
        """Read n bits LSB-first (D2 bit ordering)."""
        val = 0
        for i in range(n):
            byte_idx = self.pos >> 3
            bit_idx  = self.pos & 7
            val |= ((self.data[byte_idx] >> bit_idx) & 1) << i
            self.pos += 1
        return val

def parse_stats_section(data: bytes) -> dict:
    """Parse the 'gf' stats section from a .d2s file."""
    reader = BitReader(data)
    stats = {}
    while True:
        stat_id = reader.read(9)
        if stat_id == 0x1FF:  # end marker
            break
        # stat_id maps to itemstatcost.txt — read bits per that row's "CSvBits"
        bits = STAT_BITS.get(stat_id, 32)
        value = reader.read(bits)
        stats[stat_id] = value
    return stats

# Stat bit widths from itemstatcost.txt "CSvBits" column (key examples)
STAT_BITS = {
    0:  10,  # Strength
    1:  10,  # Energy
    2:  10,  # Dexterity
    3:  10,  # Vitality
    4:  10,  # Stat points
    5:   8,  # Skill points
    6:  21,  # Current HP (fixed-point ×256)
    7:  21,  # Max HP
    8:  21,  # Current Mana
    9:  21,  # Max Mana
    10: 21,  # Stamina
    11: 21,  # Max Stamina
    12:  7,  # Level
    13: 32,  # Experience
    14: 25,  # Gold
    15: 25,  # Gold bank
}
```

### Ghidra Scripts (`references/ghidra-scripts.md`)

```python
# D2_ApplySymbols.py — import community JSON symbol table into Ghidra
# Paste into Ghidra Script Manager and run against an open D2 binary

import json
from ghidra.program.model.symbol import SourceType

symbols_file = askFile("Select D2 symbols JSON", "Open")
with open(symbols_file.absolutePath) as f:
    symbols = json.load(f)

listing = currentProgram.getListing()
sym_table = currentProgram.getSymbolTable()
base = currentProgram.getImageBase()

for sym in symbols:
    addr = base.add(int(sym['offset'], 16))
    sym_table.createLabel(addr, sym['name'], SourceType.USER_DEFINED)
    if sym.get('signature'):
        func = listing.getFunctionAt(addr)
        if func:
            func.setName(sym['name'], SourceType.USER_DEFINED)

print(f"Applied {len(symbols)} symbols")
```

---

## 21. Source Reconstruction Guidelines

**Accuracy first.** Mark speculation: `/* ESTIMATED — verify in disassembly */`

**Version-target explicitly.** Always comment: `/* D2 v1.13c — D2Common.dll+0x63990 */`

**Preserve struct packing.** Use `#pragma pack(push,1)` for ALL binary-mapped structs.
Misalignment silently corrupts struct field reads in D2's 32-bit address space.

**Preserve calling convention.** Wrong `__fastcall` vs `__stdcall` crashes at return.
For `__fastcall`, always include `int _edx` as second parameter in the C signature.

**Use D2 types.** `WORD`/`DWORD`/`BYTE` not `uint16_t`/`uint32_t` — matches original.

**Match the community naming corpus:**
- `UnitAny`, `StatList`, `StatEx`, `Inventory`, `Room1`, `Room2`, `ActMisc`
- `D2Common_GetUnitStat`, `D2Game_CreateMissile`, `D2Net_SendPacket`

**Cross-check before writing any function:**
- Jarulf's Guide (definitive for statistical/damage formulas)
- PhrozenKeep forums (deep RE discussions)
- D2LOD-IDA community symbol file
- OpenD2 project (struct layout verification)
- D2BS/Kolbot (live game state reading patterns)

---

## 22. Reference Files

Load these on-demand for deep coverage of specific subsystems:

| File | Contents | When to Load |
|---|---|---|
| `references/stat-ids.md` | 220+ stat IDs, encoding types, bit widths | StatList/stat engine work |
| `references/function-offsets.md` | VAs for v1.09–v1.14d across all modules | Hooking, locating code |
| `references/packets.md` | ~180 packet structs, full C/S tables | Network RE, server emulation |
| `references/combat-formulas.md` | Hit%, damage, DR, block, MF, XP math | Combat system RE |
| `references/item-generation.md` | TC recursion, affix pipeline, quality | Item/loot RE |
| `references/drlg-map-gen.md` | BSP, DS1/DT1, preset/outdoor systems | Map generation RE |
| `references/ai-states.md` | AI code table, state machine, boss mods | Monster behavior RE |
| `references/skill-system.md` | Skill table, missiles, auras, charges | Skill system RE |
| `references/dcc-dc6-format.md` | Bit-exact DC6/DCC format specs | Sprite tools |
| `references/d2s-format.md` | Full bitstream save format, all sections | Save editor tools |
| `references/ghidra-scripts.md` | Python scripts for Ghidra automation | RE toolchain |
| `references/d2r-resurrected.md` | D2R struct diffs, CASC, JSON, 64-bit | D2R RE |

### Community Open-Source Corpus

| Project | Language | Primary Value |
|---|---|---|
| [OpenD2](https://github.com/OpenD2/OpenD2) | C++ | Struct layout, engine skeleton |
| [D2BS](https://github.com/noah-/d2bs) | C++/JS | Live unit access, packet hooks |
| [Kolbot](https://github.com/kolton/d2emu) | JavaScript | Game logic in readable JS |
| [D2Mod2](https://github.com/Zcarniv/D2Mod2) | C++ | Plugin hook framework |
| [PlugY](http://plugy.free.fr) | C++ | Inventory/stash extensions |
| [StormLib](https://github.com/ladislav-zezula/StormLib) | C | MPQ canonical implementation |
| [CascLib](https://github.com/ladislav-zezula/CascLib) | C | D2R CASC canonical implementation |
| [PVPGN](https://github.com/pvpgn/pvpgn-server) | C/C++ | Battle.net emulator server |
