# D2 Item Generation Pipeline — Complete Reference

---

## Stage 1: Treasure Class Recursion

All loot starts in `TreasureClass` (`tc.txt`). Each TC row can reference
other TCs (recursive), item codes, or special tokens.

```c
/* TreasureClass resolution (simplified) */
typedef struct TCEntry {
    char   szCode[8];    /* item code OR "tc/<TreasureName>" OR "gld" */
    DWORD  dwProb;       /* relative probability weight */
} TCEntry;

typedef struct TreasureClass {
    char     szName[32];
    TCEntry  entries[10];   /* up to 10 possibilities */
    DWORD    dwNoDrop;       /* probability of dropping nothing */
    DWORD    dwPicks;        /* how many picks from this TC */
    DWORD    dwUnique;       /* % chance quality = Unique (0 = use normal roll) */
    DWORD    dwSet;
    DWORD    dwRare;
    DWORD    dwMagic;
} TreasureClass;

/* Recursive resolution */
const char* D2_ResolveTreasureClass(const char* szTC, DWORD* pSeed) {
    TreasureClass* pTC = LookupTC(szTC);
    if (!pTC) return szTC;  /* base case: szTC is an item code */

    DWORD total = pTC->dwNoDrop;
    for (int i = 0; i < 10 && pTC->entries[i].szCode[0]; i++)
        total += pTC->entries[i].dwProb;

    DWORD roll = D2_LCG_Range(pSeed, total);
    if (roll < pTC->dwNoDrop) return NULL;  /* NoDrop */

    roll -= pTC->dwNoDrop;
    for (int i = 0; i < 10; i++) {
        if (!pTC->entries[i].szCode[0]) break;
        if (roll < pTC->entries[i].dwProb)
            return D2_ResolveTreasureClass(pTC->entries[i].szCode, pSeed);
        roll -= pTC->entries[i].dwProb;
    }
    return NULL;
}
```

---

## Stage 2: Item Level (iLvl) Assignment

The item level gates which affixes can appear on an item.

```c
DWORD D2_CalcItemLevel(UnitAny* pMonster, DWORD dwAreaLevel) {
    DWORD mlvl = D2Common_GetUnitStat(pMonster, 0, STAT_LEVEL, 0);
    /* Boss bonus: +2 to mlvl for champions, +3 for uniques */
    if (pMonster->dwFlags & UNITFLAG_CHAMPION) mlvl += 2;
    if (pMonster->dwFlags & UNITFLAG_UNIQUE)   mlvl += 3;
    /* iLvl = min(mlvl, alvl × 2) — caps at twice the area level */
    return min(mlvl, dwAreaLevel * 2);
}
/* For objects/chests: iLvl = area level */
/* For gambling: iLvl = clvl + 5 (capped at clvl - 5 to clvl + 4 range) */
/* For crafting: iLvl = floor(clvl/2) + floor(ilvl_of_ingredient/2) */
```

---

## Stage 3: Quality Determination

Quality is determined by a series of cascading rolls, each with MF applied.

```c
DWORD D2_DetermineQuality(DWORD dwILvl, DWORD dwEffMF, UnitAny* pItem) {
    DWORD baseCode = GetItemBaseCode(pItem);  /* 3-char code from items txt */

    /* Check Unique: roll < (unique_ratio × (effMF + 250)) / 1024 */
    DWORD uniqueRatio = GetUniqueRatio(baseCode);   /* from UniqueItems.txt */
    if (uniqueRatio > 0) {
        DWORD threshold = uniqueRatio * (dwEffMF + 250) / 1024;
        if (D2_LCG_Range(pItemSeed, 1024) < threshold)
            return ITEMQUAL_UNIQUE;
    }

    /* Check Set */
    DWORD setRatio = GetSetRatio(baseCode);
    if (setRatio > 0 && D2_LCG_Range(pItemSeed, 1024) < setRatio * (dwEffMF + 500) / 1024)
        return ITEMQUAL_SET;

    /* Check Rare */
    DWORD rareRatio = GetRareRatio(baseCode);   /* from misc/weapon/armor txt */
    if (D2_LCG_Range(pItemSeed, 1024) < rareRatio * (dwEffMF + 600) / 1024)
        return ITEMQUAL_RARE;

    /* Check Magic */
    DWORD magicRatio = GetMagicRatio(baseCode);
    if (D2_LCG_Range(pItemSeed, 1024) < magicRatio * (dwEffMF + 1) / 1024)
        return ITEMQUAL_MAGIC;

    /* Check Superior */
    /* ... */

    return ITEMQUAL_NORMAL;
}
```

---

## Stage 4: Affix Selection

### Magic Items (1 prefix + 1 suffix)

```c
void D2_RollMagicAffixes(ItemData* pItemData, DWORD dwILvl) {
    DWORD seed = pItemData->dwSeed;

    /* Prefix roll: 50% chance of having a prefix at all */
    if (D2_LCG_Range(&seed, 2) == 0) {
        AffixPool* pPrefixes = GetEligiblePrefixes(pItemData, dwILvl);
        pItemData->wMagicPrefix = PickRandomAffix(&seed, pPrefixes);
    }

    /* Suffix roll: 50% chance (but at least one must be chosen) */
    if (D2_LCG_Range(&seed, 2) == 0 || pItemData->wMagicPrefix == 0) {
        AffixPool* pSuffixes = GetEligibleSuffixes(pItemData, dwILvl);
        pItemData->wMagicSuffix = PickRandomAffix(&seed, pSuffixes);
    }

    pItemData->dwSeed = seed;
}
```

### Rare Items (3 pre + 3 suf pool → pick 3–6 total)

```c
void D2_RollRareAffixes(ItemData* pItemData, DWORD dwILvl) {
    DWORD seed = pItemData->dwSeed;

    /* Rare name: 2 random indices into RarePrefix/RareSuffix name tables */
    pItemData->wRarePrefix = D2_LCG_Range(&seed, GetRarePrefixCount());
    pItemData->wRareSuffix = D2_LCG_Range(&seed, GetRareSuffixCount());

    /* Build pool: up to 3 prefixes + 3 suffixes */
    WORD affixes[6] = {0};
    DWORD count = 0;
    DWORD numAffixes = 3 + D2_LCG_Range(&seed, 4);  /* 3–6 affixes total */

    /* Alternate prefix/suffix picks, ensuring balance */
    BOOL bPrefixTurn = (D2_LCG_Range(&seed, 2) == 0);
    for (DWORD i = 0; i < numAffixes && count < 6; i++) {
        AffixPool* pool = bPrefixTurn ?
            GetEligiblePrefixes(pItemData, dwILvl, affixes, count) :
            GetEligibleSuffixes(pItemData, dwILvl, affixes, count);
        if (pool->count > 0) {
            affixes[count++] = PickRandomAffix(&seed, pool);
        }
        bPrefixTurn = !bPrefixTurn;
    }

    pItemData->dwSeed = seed;
    /* Store affixes in StatList via SetUnitStat for each property */
}
```

---

## Stage 5: Unique and Set Matching

```c
BOOL D2_TryAssignUnique(ItemData* pItemData, DWORD dwILvl) {
    /* Find all unique items sharing this base code */
    UniqueItem* pMatches[16];
    DWORD nMatches = 0;
    for (each row in UniqueItems.txt) {
        if (row.code == pItemData->baseCode)
            pMatches[nMatches++] = row;
    }
    if (nMatches == 0) return FALSE;

    /* If iLvl >= unique.lvl, assign it */
    /* Multiple uniques of same base: pick by seed roll */
    UniqueItem* pPick = pMatches[D2_LCG_Range(&pItemData->dwSeed, nMatches)];
    if (dwILvl >= pPick->lvl) {
        pItemData->wUniqueCode = pPick->id;
        return TRUE;
    }
    /* Downgrade to Rare */
    pItemData->dwQuality = ITEMQUAL_RARE;
    D2_RollRareAffixes(pItemData, dwILvl);
    return FALSE;
}
```

---

## Stage 6: Sockets, Ethereal, Superior

```c
DWORD D2_RollSockets(DWORD dwBaseCode, DWORD dwILvl, DWORD dwDifficulty) {
    /* Max sockets from items.txt "MaxSock1/2/3" columns per difficulty */
    DWORD maxSock = GetMaxSockets(dwBaseCode, dwDifficulty);

    /* Roll: D2_LCG_Range(seed, 6) + 1, capped at maxSock */
    DWORD rolled = D2_LCG_Range(&gSeed, 6) + 1;
    return min(rolled, maxSock);
}

BOOL D2_RollEthereal(DWORD dwBaseCode, UnitAny* pSource) {
    /* Only monsters can drop ethereal; shops and gambling cannot */
    /* 1-in-17 base chance for eligible item types */
    if (!CanBeEthereal(dwBaseCode)) return FALSE;
    if (pSource->dwType != UNIT_MONSTER) return FALSE;
    return (D2_LCG_Range(&gSeed, 17) == 0);
}
```

---

## Cube Recipes

Horadric Cube recipes are defined in `cubemain.txt`. Each row specifies:
- Input item codes/quantities (up to 6 ingredients)
- Output item code and quantity
- Required NPC, class, or flags

```c
typedef struct CubeRecipe {
    char    szDescription[64];
    char    szEnabled;
    WORD    wVersion;              /* 0=classic, 100=expansion */
    char    szClass[8];            /* "" = any class */
    char    szOp;                  /* operation type: 28=upgrade, 36=socket, etc. */
    WORD    wParam;
    char    szValue[32];
    /* Ingredient specs (up to 6): code + qty + quality flags */
    struct { char code[8]; WORD qty; DWORD flags; } inputs[6];
    /* Output specs */
    char    szOutputCode[8];
    WORD    wOutputQty;
    DWORD   dwOutputFlags;
} CubeRecipe;

/* Key operation codes */
#define CUBE_OP_UPGRADE_NORMAL_TO_EXCEPTIONAL  28
#define CUBE_OP_UPGRADE_EXCEPTIONAL_TO_ELITE   36
#define CUBE_OP_REROLL_MAGIC                    5
#define CUBE_OP_SOCKET_ITEM                    26
#define CUBE_OP_REPLENISH_CHARGES              10
```

---

## Affix Level (aLvl) and clvl Relationship

For gambling and crafting, the effective item level differs from drop items:

```
Gambling:
  Displayed as Normal quality base item
  Actual quality determined on purchase:
    iLvl = clvl + 5
    But affixes limited to min(clvl-5, iLvl) to max(iLvl) range
    Caps at 99 for both endpoints

Crafting (Horadric Cube):
  craft_ilvl = floor(req_lvl_of_highest_ingredient / 2) + floor(clvl / 2)
  craft_ilvl caps at 99
  Craft items always have:
    - 4 fixed affixes from the recipe type (blood/caster/hitpower/safety)
    - 1–4 random magic affixes at the craft_ilvl
```
