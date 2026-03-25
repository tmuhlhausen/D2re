# DRLG — Dungeon Random Level Generator Reference

---

## Three Generator Types

### DRLG_PRESET (type 0)

Used for: Towns (Act 1–5), Rogue Encampment, Lut Gholein, Kurast, Pandemonium Fortress,
Harrogath, Arcane Sanctuary, Tristram, Cow Level, Uber Tristram.

Preset levels are loaded from `.ds1` files and placed deterministically.
The "random" element is which tile variant is chosen when multiple options exist.

```c
/* D2Game.dll+0x8E200 (v1.13c) */
void DRLG_Preset_Generate(Level* pLevel, DWORD dwSeed) {
    /* 1. Load the .ds1 file for this level ID */
    DS1File* pDS1 = Storm_LoadDS1(g_LevelDS1Table[pLevel->dwLevelId]);
    /* 2. Place rooms according to DS1 layer data */
    /* 3. For each room: place preset units (monsters, NPCs, objects) */
    /* 4. Random variation: alternate tile selection within preset bounds */
}
```

### DRLG_OUTDOOR (type 1)

Used for: Blood Moor, Cold Plains, Stony Field, Dark Wood, Black Marsh,
Act 2 desert areas, Act 3 jungle areas, Arreat Plateau, etc.

Algorithm: grid-based stamp selection from a tile palette defined in `levels.txt`.

```c
void DRLG_Outdoor_Generate(Level* pLevel, DWORD dwSeed) {
    DWORD seed = dwSeed;
    DWORD gridW = pLevel->dwSizeX / 8;   /* each stamp is 8×8 tiles */
    DWORD gridH = pLevel->dwSizeY / 8;

    for (DWORD gy = 0; gy < gridH; gy++) {
        for (DWORD gx = 0; gx < gridW; gx++) {
            /* Pick a tile stamp from the level's environment palette */
            DWORD stampIdx = D2_LCG_Range(&seed, GetStampCount(pLevel->dwEnvCode));
            PlaceStamp(pLevel, gx * 8, gy * 8, stampIdx);
        }
    }
    /* Post-process: blend edges between different stamp types */
    DRLG_Outdoor_BlendEdges(pLevel);
    /* Place outdoor features: waypoints, special spawns */
    DRLG_Outdoor_PlaceSpecials(pLevel, &seed);
}
```

### DRLG_MAZE (type 2)

Used for: Catacombs, Caves, Dungeons, Underground Passage, Tower,
Sewers, Crypt, Mausoleum, Ancient Tunnels, Maggot Lair, Arcane Sanctuary detail floors,
Throne of Destruction.

Algorithm: Recursive Binary Space Partitioning (BSP).

```c
/* BSP node */
typedef struct BSPNode {
    WORD wX, wY, wW, wH;     /* rectangle this node covers */
    struct BSPNode* pLeft;    /* split result A */
    struct BSPNode* pRight;   /* split result B */
    BOOL bIsRoom;             /* leaf node = actual room */
    WORD wRoomX, wRoomY;     /* room within node (smaller than node) */
    WORD wRoomW, wRoomH;
} BSPNode;

BSPNode* DRLG_BSP_Partition(WORD x, WORD y, WORD w, WORD h,
                              DWORD dwDepth, DWORD* pSeed) {
    BSPNode* node = AllocBSPNode();
    node->wX = x; node->wY = y; node->wW = w; node->wH = h;

    /* Stop recursing if node is too small */
    if (w < 6 || h < 6 || dwDepth == 0) {
        /* Leaf: create a room within this node */
        node->bIsRoom = TRUE;
        node->wRoomW  = 4 + D2_LCG_Range(pSeed, w - 4);
        node->wRoomH  = 4 + D2_LCG_Range(pSeed, h - 4);
        node->wRoomX  = x + D2_LCG_Range(pSeed, w - node->wRoomW);
        node->wRoomY  = y + D2_LCG_Range(pSeed, h - node->wRoomH);
        return node;
    }

    /* Split horizontally or vertically based on aspect ratio */
    BOOL bSplitH = (w > h) ? TRUE :
                   (h > w) ? FALSE :
                   (D2_LCG_Range(pSeed, 2) == 0);

    if (bSplitH) {
        WORD split = w / 3 + D2_LCG_Range(pSeed, w / 3);
        node->pLeft  = DRLG_BSP_Partition(x, y, split, h, dwDepth-1, pSeed);
        node->pRight = DRLG_BSP_Partition(x+split, y, w-split, h, dwDepth-1, pSeed);
    } else {
        WORD split = h / 3 + D2_LCG_Range(pSeed, h / 3);
        node->pLeft  = DRLG_BSP_Partition(x, y, w, split, dwDepth-1, pSeed);
        node->pRight = DRLG_BSP_Partition(x, y+split, w, h-split, dwDepth-1, pSeed);
    }
    return node;
}

/* Connect rooms with L-shaped hallways */
void DRLG_BSP_ConnectRooms(BSPNode* pA, BSPNode* pB, DWORD* pSeed) {
    /* Find midpoints of each room */
    WORD ax = pA->wRoomX + pA->wRoomW / 2;
    WORD ay = pA->wRoomY + pA->wRoomH / 2;
    WORD bx = pB->wRoomX + pB->wRoomW / 2;
    WORD by = pB->wRoomY + pB->wRoomH / 2;

    /* Randomly decide: go horizontal-first or vertical-first */
    if (D2_LCG_Range(pSeed, 2) == 0) {
        CarveHallway(ax, ay, bx, ay, 2);   /* horizontal */
        CarveHallway(bx, ay, bx, by, 2);   /* then vertical */
    } else {
        CarveHallway(ax, ay, ax, by, 2);   /* vertical first */
        CarveHallway(ax, by, bx, by, 2);   /* then horizontal */
    }
}
```

---

## Dungeon Population

After geometry generation, three population passes run in order:

### Pass 1: Preset Units

Placed at fixed positions defined in the `.ds1` file or `LvlPrest.txt`.
These are: stairs (level exits), waypoints, chest spawns, boss spawn markers,
specific NPCs (Deckard Cain cage, Mephisto's altar, etc.).

```c
void DRLG_PopulatePresets(Level* pLevel) {
    for each PresetUnit in pLevel->pRoom2First->pPresetUnits {
        WORD wx = preset.wX + room.wPosX;
        WORD wy = preset.wY + room.wPosY;
        switch (preset.dwType) {
            case PRESETTYPE_NPC:     D2Game_SpawnMonster(preset.dwCode, wx, wy, pLevel); break;
            case PRESETTYPE_OBJECT:  D2Game_SpawnObject(preset.dwCode, wx, wy, pLevel);  break;
            case PRESETTYPE_ITEM:    D2Game_SpawnItem(preset.dwCode, wx, wy, pLevel);    break;
        }
    }
}
```

### Pass 2: Monster Population

Monster density and types come from `levels.txt` columns:
`Mon1`–`Mon25` (which monster types can spawn), `MonDen` (density),
`MonUMin`/`MonUMax` (unique/champion count range).

```c
void DRLG_PopulateMonsters(Level* pLevel, DWORD dwDifficulty) {
    LevelData* pLD = &g_LevelTable[pLevel->dwLevelId];
    DWORD seed = pLevel->dwSeed;

    /* Density: number of monsters per room area */
    DWORD density = pLD->dwMonDen[dwDifficulty];
    for each Room1 in pLevel {
        DWORD count = (room.area * density) / 1000;
        for (DWORD i = 0; i < count; i++) {
            /* Pick monster type from Mon1–Mon25 pool */
            DWORD monIdx = D2_LCG_Range(&seed, pLD->dwMonCount);
            DWORD monCode = pLD->wMonTypes[monIdx];
            /* Find walkable spawn position */
            WORD wx, wy;
            if (FindWalkablePos(pRoom, &wx, &wy, &seed))
                D2Game_SpawnMonster(monCode, wx, wy, pLevel);
        }
        /* Boss/champion packs */
        DWORD uniqueCount = pLD->wMonUMin + D2_LCG_Range(&seed, pLD->wMonUMax - pLD->wMonUMin + 1);
        for (DWORD u = 0; u < uniqueCount; u++)
            DRLG_SpawnBossPack(pRoom, pLD, dwDifficulty, &seed);
    }
}
```

### Pass 3: Objects (Shrines, Chests, Barrels)

Objects come from `Objgroup.txt` and `Objects.txt`.
Shrines are placed near walkable areas with a minimum spacing requirement.

---

## Level ID Enum (Key Values)

```c
typedef enum LevelId {
    LEVEL_ROGUE_ENCAMPMENT    = 1,
    LEVEL_BLOOD_MOOR          = 2,
    LEVEL_COLD_PLAINS         = 3,
    LEVEL_STONY_FIELD         = 4,
    LEVEL_DARK_WOOD           = 5,
    LEVEL_BLACK_MARSH         = 6,
    LEVEL_TAMOE_HIGHLAND      = 7,
    LEVEL_DEN_OF_EVIL         = 8,
    LEVEL_CAVE_LEVEL1         = 9,
    LEVEL_UNDERGROUND_PASSAGE1= 10,
    LEVEL_HOLE_LEVEL1         = 11,
    LEVEL_PIT_LEVEL1          = 12,
    LEVEL_CATACOMBS_LEVEL1    = 21,
    LEVEL_CATACOMBS_LEVEL4    = 24,  /* Andariel */
    LEVEL_LUT_GHOLEIN         = 40,
    LEVEL_ARCANE_SANCTUARY    = 74,
    LEVEL_CANYON_OF_MAGI      = 76,
    LEVEL_KURAST_DOCKS        = 79,
    LEVEL_DURANCE_OF_HATE_L3  = 103, /* Mephisto */
    LEVEL_PANDEMONIUM_FORTRESS = 109,
    LEVEL_CHAOS_SANCTUARY     = 131, /* Diablo */
    LEVEL_HARROGATH           = 132,
    LEVEL_WORLDSTONE_KEEP_L3  = 128, /* Baal */
    LEVEL_SECRET_COW_LEVEL    = 112,
    LEVEL_UBER_TRISTRAM       = 117,
    /* ... 134 total level IDs in expansion */
} LevelId;
```

---

## Map Seed and Reproducibility

The entire map for a game session is deterministic from the game's map seed.
The map seed is stored in the `.d2s` file at offset 0xAB.

```
GameSeed (32-bit)
 └─ Each Act generates ActSeed = LCG(GameSeed, actIndex)
     └─ Each Level generates LevelSeed = LCG(ActSeed, levelId)
         └─ Each Room generates RoomSeed = LCG(LevelSeed, roomIndex)
```

This means given the same game seed, all maps are identical — which is
exploited by the D2 community's "map hacking" tools that pre-generate
the map before entering an area.

Map seed extraction from a live process:

```c
/* Read map seed from the ActMisc structure */
DWORD GetGameMapSeed(void) {
    UnitAny* pPlayer = *(UnitAny**)( (DWORD)GetModuleHandleA("D2Client.dll") + 0x11C3D0 );
    if (!pPlayer || !pPlayer->pAct) return 0;
    return pPlayer->pAct->pGameData->dwMapSeed;  /* or read from .d2s 0xAB */
}
```
