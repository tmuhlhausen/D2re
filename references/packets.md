# D2R — Diablo II: Resurrected Deep Reference
# Engine changes, 64-bit struct layout, CASC access, JSON overrides, modding

---

## Architecture Overview

| Feature | Classic D2 (1.14d) | D2 Resurrected |
|---|---|---|
| Process | 32-bit, single .exe | 64-bit, single .exe |
| Pointer width | 4 bytes (DWORD) | 8 bytes (QWORD/uintptr_t) |
| Archive | MPQ v1/v2 | CASC (Content Addressable Storage) |
| Renderer | DirectX 8 / Software | DirectX 12 (PC), Metal (Mac) |
| Data tables | Binary .bin compiled at startup | JSON + legacy .bin loader |
| Save format | .d2s local only | .d2s + Battle.net cloud sync |
| Networking | D2Net (custom TCP) | Battle.net 2.0 relay + DTLS |
| Sprites | DC6 / DCC | DCC (legacy) + .anim container |
| Resolution | 800×600 fixed | Arbitrary (4K, ultrawide) |
| Physics | Tile-locked | Smooth sub-pixel interpolation |
| Modding API | D2Mod / INI patches | Official mod framework (mpq-style directories) |

---

## 64-bit Struct Layout Changes

When all pointers grow from 4→8 bytes, struct sizes change significantly.
**Critical rule: Never assume Classic D2 field offsets in D2R code.**

### D2R UnitAny (Approximate — Subject to Patch Changes)

```c
/* D2R UnitAny — 64-bit build, approximate offsets */
typedef struct D2R_UnitAny {
    DWORD            dwType;          // 0x00
    DWORD            dwClassId;       // 0x04
    DWORD            dwMode;          // 0x08
    DWORD            dwUnitId;        // 0x0C
    DWORD            dwAct;           // 0x10
    DWORD            _pad0;           // 0x14 — alignment pad
    struct ActMisc*  pAct;            // 0x18 — 8 bytes (was 0x14 in classic)
    DWORD            dwSeed[2];       // 0x20
    DWORD            dwInitSeed;      // 0x28
    DWORD            _pad1;           // 0x2C
    union {                           // 0x30 — pointer, 8 bytes
        struct PlayerData*  pPlayerData;
        struct MonsterData* pMonsterData;
        struct ItemData*    pItemData;
        /* ... */
    };
    /* ... fields shifted by 8+ bytes vs classic ... */
    struct StatList* pStatList;       // ~0x68 (was 0x48)
    struct Inventory*pInventory;      // ~0x70 (was 0x4C)
    struct Path*     pPath;           // ~0x78 (was 0x50)
    DWORD            dwFlags;         // ~0xE0 (was 0xC8)
    struct UnitAny*  pListNext;       // ~0x118 (was 0xE8)
    /* ... */
} D2R_UnitAny;

/* IMPORTANT: Use pattern scanning or live CE inspection to find
   current D2R offsets — they change frequently with patches.
   Do NOT hardcode offsets for D2R without version pinning. */
```

### D2R Path Struct

```c
typedef struct D2R_Path {
    WORD    wPosX;           // 0x00
    WORD    _p0;
    WORD    wPosY;           // 0x04
    WORD    _p1;
    WORD    wTargetX;        // 0x08
    WORD    wTargetY;        // 0x0A
    DWORD   _unk;            // 0x0C
    struct  Room1* pRoom1;   // 0x10 — 8 bytes in D2R
    struct  Room1* pRoomNext;// 0x18
    WORD    wPrePosX;        // 0x20
    WORD    wPrePosY;        // 0x22
    DWORD   _unk2;
    struct  UnitAny* pUnit;  // 0x28 — 8 bytes
    DWORD   dwFlags;         // 0x30
} D2R_Path;
```

---

## CASC Archive Access

D2R uses the CASC storage format instead of MPQ. Use CascLib for access.

```c
#include "CascLib.h"

/* ── Open D2R storage ── */
HANDLE hStorage = NULL;
const char* d2rPath = "C:\\Program Files (x86)\\Diablo II Resurrected";

if (!CascOpenStorage(d2rPath, 0, &hStorage)) {
    fprintf(stderr, "CASC open failed: %lu\n", GetLastError());
    return;
}

/* ── List all files (enumerate the CASC manifest) ── */
CASC_FIND_DATA findData;
HANDLE hFind = CascFindFirstFile(hStorage, "*", &findData, NULL);
if (hFind != INVALID_HANDLE_VALUE) {
    do {
        printf("%s (%llu bytes)\n", findData.szFileName, findData.FileSize);
    } while (CascFindNextFile(hFind, &findData));
    CascFindClose(hFind);
}

/* ── Read a specific file ── */
HANDLE hFile = NULL;
/* D2R path format: "data:data/global/excel/weapons.txt" */
/* The "data:" prefix is required to access game data files */
if (CascOpenFile(hStorage, "data:data/global/excel/weapons.txt",
                  CASC_LOCALE_ALL, CASC_OPEN_BY_NAME, &hFile)) {
    DWORD dwSize, dwRead;
    CascGetFileSize(hFile, &dwSize);
    char* buf = (char*)malloc(dwSize + 1);
    if (CascReadFile(hFile, buf, dwSize, &dwRead)) {
        buf[dwRead] = '\0';
        /* buf now contains the TSV data */
    }
    CascCloseFile(hFile);
    free(buf);
}

CascCloseStorage(hStorage);
```

### Python CASC Access (via casclib Python wrapper)

```python
# pip install pycasc  (unofficial wrapper around CascLib)
import pycasc

storage = pycasc.open("C:/Program Files (x86)/Diablo II Resurrected")

# List files matching a pattern
for entry in storage.find("*.txt"):
    print(entry.name, entry.size)

# Read a specific file
data = storage.read("data:data/global/excel/weapons.txt")
lines = data.decode("utf-8").split("\r\n")
headers = lines[0].split("\t")
rows = [dict(zip(headers, l.split("\t"))) for l in lines[2:] if l.strip()]
# (Skip first row = headers, second row = column types)
```

---

## JSON Override System

D2R supports data overrides through JSON files placed in the mod directory.
This is the official D2R modding API.

### File Structure

```
<D2R install>/mods/<modname>/
  manifest.json           ← mod metadata
  data/
    global/
      excel/
        weapons.txt.json  ← override weapons table
        skills.txt.json   ← override skills
        monstats.txt.json ← override monsters
      ui/
        Loading screens, custom strings
    hd/                   ← HD asset overrides
      global/
        items/            ← 3D model overrides
```

### manifest.json

```json
{
  "name": "MyD2Mod",
  "savePath": "MyD2Mod",
  "description": "My D2R mod",
  "expansion": true,
  "author": "Author",
  "version": "1.0.0",
  "website": "https://example.com"
}
```

### JSON Table Override Format

```json
// weapons.txt.json — override specific rows
// Array of objects; each object matches by "name" field
// Only specified fields are changed; others remain default
{
  "Weapons": [
    {
      "name": "Short Sword",
      "mindam": 3,
      "maxdam": 15,
      "speed": -10,
      "StrBonus": 80
    },
    {
      "name": "Phase Blade",
      "maxdam": 180
    }
  ]
}
```

### Modifying String Tables

```json
// string.json — add or override string table entries
{
  "String": [
    {
      "Key": "ItemStats1e",
      "enUS": "+{0}% Enhanced Damage",
      "Comments": "Custom tooltip override"
    },
    {
      "Key": "MyCustomString",
      "enUS": "Hello from my mod!"
    }
  ]
}
```

---

## D2R Rendering Pipeline Hooks

D2R uses DirectX 12 with a command list architecture. Unlike D2 Classic's
immediate-mode DirectDraw, D2R batches draw calls.

```c
/* D2R still exposes a GfxEnvironment object for sprite submission */
/* Hooking: intercept the DX12 Present call via DXGI swap chain vtable */

typedef HRESULT (STDMETHODCALLTYPE *Present_t)(IDXGISwapChain*, UINT, UINT);
static Present_t oPresent = NULL;

HRESULT STDMETHODCALLTYPE hk_Present(IDXGISwapChain* pSwapChain, UINT SyncInterval, UINT Flags) {
    /* Your per-frame overlay logic here */
    /* e.g., draw ImGui overlay using D3D12 backend */
    return oPresent(pSwapChain, SyncInterval, Flags);
}

/* Hook via swap chain vtable (offset 8 = Present) */
void Hook_DX12Present(void) {
    /* Get swap chain from D3D12 device */
    /* Modify vtable entry 8 */
    void** pVtable = *(void***)pSwapChain;
    DWORD dwOld;
    VirtualProtect(&pVtable[8], sizeof(void*), PAGE_READWRITE, &dwOld);
    oPresent = (Present_t)pVtable[8];
    pVtable[8] = hk_Present;
    VirtualProtect(&pVtable[8], sizeof(void*), dwOld, &dwOld);
}
```

---

## D2R .anim Format

The new `.anim` container wraps legacy DCC animations with a metadata header
and supports smooth interpolation between frames.

```c
/* .anim file header (D2R specific) */
#pragma pack(push, 1)
typedef struct AnimHeader {
    DWORD dwMagic;           // 0x44494C42 ("DILB" = Diablo)
    DWORD dwVersion;         // 2 for D2R
    DWORD dwDirections;
    DWORD dwFramesPerDir;
    float fPlaybackSpeed;    // FPS multiplier for smooth animation
    DWORD dwDCCOffset;       // byte offset to embedded DCC data
    DWORD dwDCCSize;         // size of embedded DCC block
    DWORD dwFlags;           // ANIMFLAG_LOOP, ANIMFLAG_PINGPONG, etc.
} AnimHeader;
#pragma pack(pop)
```

---

## D2R Memory Reading (Cheat Engine / External Tooling)

Pattern signatures for D2R (updated frequently — use these as examples):

```python
# D2R memory scanner patterns (as of patch 2.6.x, subject to change)
# All are relative to D2R.exe base

PATTERNS = {
    # Find UnitAny* for local player
    "player_unit": {
        "sig":  b"\x48\x8B\x05\x00\x00\x00\x00\x48\x85\xC0\x74",
        "mask": b"xxx????xxxx",
        "deref_offset": 3,  # 4-byte RIP-relative offset at byte 3
        "type": "rip_relative",
    },
    # Find game tick counter
    "game_tick": {
        "sig":  b"\xFF\x05\x00\x00\x00\x00\x48\x8B",
        "mask": b"xx????xx",
        "deref_offset": 2,
        "type": "rip_relative",
    },
}

def find_rip_relative(process_handle, base_addr, pattern):
    """Scan for a RIP-relative pattern and resolve the final address."""
    sig   = pattern["sig"]
    found = scan_memory(process_handle, base_addr, sig, pattern["mask"])
    if not found: return None
    # RIP-relative: read 4-byte signed offset at found+deref_offset
    rva_bytes = read_memory(process_handle, found + pattern["deref_offset"], 4)
    rva = int.from_bytes(rva_bytes, 'little', signed=True)
    # RIP = found + deref_offset + 4
    return found + pattern["deref_offset"] + 4 + rva
```
