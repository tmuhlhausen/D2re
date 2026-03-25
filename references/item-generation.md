# DC6 / DCC Sprite Format — Complete Specification
# Verified against community RE, StormLib analysis, and OpenD2 source

---

## DC6 Format — Static Sprites (UI, Items, Objects, Fonts)

DC6 files store pre-rendered sprites for multiple directions and frames.
Used for: inventory item graphics, UI panels, town objects, fonts.

### DC6 File Structure

```
DC6Header  (24 bytes)
FramePtrTable  (dwDirections × dwFramesPerDir × 4 bytes)
[FrameHeader + FrameData] × (dwDirections × dwFramesPerDir)
TerminationBlock (4 bytes: 0xEEEEEEEE or 0xCDCDCDCD)
```

### DC6Header (24 bytes)

```c
#pragma pack(push, 1)
typedef struct DC6Header {
    DWORD dwVersion;         // Always 6
    DWORD dwUnk1;            // Always 1
    DWORD dwUnk2;            // Always 0 (or 0xCDCDCDCD in some versions)
    DWORD dwTermination;     // 0xEEEEEEEE — end of file marker type
    DWORD dwDirections;      // Number of directions (1,4,8,16,32)
    DWORD dwFramesPerDir;    // Frames per direction
} DC6Header;
#pragma pack(pop)

/* Immediately follows header: frame pointer table */
/* DWORD[dwDirections × dwFramesPerDir] — byte offset to each DC6FrameHeader */
```

### DC6FrameHeader (32 bytes)

```c
#pragma pack(push, 1)
typedef struct DC6FrameHeader {
    DWORD dwFlip;            // 0 = no flip, 1 = flip vertically
    DWORD dwWidth;           // Frame width in pixels
    DWORD dwHeight;          // Frame height in pixels
    LONG  lOffsetX;          // X offset from origin (can be negative)
    LONG  lOffsetY;          // Y offset from origin (can be negative)
    DWORD dwUnknown;         // Varies
    DWORD dwNextBlock;       // Byte offset to next frame (or 0 if last)
    DWORD dwLength;          // Length of compressed pixel data in bytes
    /* Compressed pixel data follows immediately */
} DC6FrameHeader;
#pragma pack(pop)
```

### DC6 Compression Algorithm

DC6 pixels are RLE-compressed row by row, bottom-to-top (y inverted).

```c
/* Decompress DC6 frame pixels to an RGBA buffer */
void DC6_Decompress(const BYTE* pSrc, DWORD dwLen,
                    BYTE* pDst, DWORD dwWidth, DWORD dwHeight,
                    const BYTE* pPalette) {
    int x = 0, y = dwHeight - 1;  /* start at bottom-left */
    DWORD i = 0;

    while (i < dwLen) {
        BYTE b = pSrc[i++];

        if (b == 0x80) {
            /* End of scanline marker: move to next row up */
            x = 0;
            y--;
        } else if (b & 0x80) {
            /* Transparent run: (b & 0x7F) transparent pixels */
            x += (b & 0x7F);
        } else {
            /* Opaque run: b pixels of palette-indexed color */
            for (BYTE n = 0; n < b && i < dwLen; n++, x++) {
                BYTE palIdx = pSrc[i++];
                DWORD dstOff = (y * dwWidth + x) * 4;
                /* Map palette index to RGBA */
                pDst[dstOff + 0] = pPalette[palIdx * 3 + 0]; /* R */
                pDst[dstOff + 1] = pPalette[palIdx * 3 + 1]; /* G */
                pDst[dstOff + 2] = pPalette[palIdx * 3 + 2]; /* B */
                pDst[dstOff + 3] = (palIdx == 0) ? 0 : 255;  /* A (index 0 = transparent) */
            }
        }
    }
}
```

---

## DCC Format — Animated Sprites (Characters, Monsters, Missiles)

DCC (Diablo Character Compressed) uses direction-based delta compression.
Used for: all animated character/monster sprites, missile graphics.

### DCC File Structure

```
DCCHeader (23 bytes)
DCCDirection × dwNumDirections
  DCCDirHeader
  DCCFrame × dwFramesPerDir
    DCCFrameHeader
  DCCDirBitStreamData (Huffman + delta compressed)
```

### DCCHeader (23 bytes)

```c
#pragma pack(push, 1)
typedef struct DCCHeader {
    BYTE  bSignature;        // 0x74 — validates file type
    BYTE  bVersion;          // 6
    BYTE  bNumDirections;    // typically 1, 4, 8, 16, or 32
    DWORD dwFramesPerDir;    // frames per direction
    DWORD dwUnk1;            // typically 1
    DWORD dwTotalSizePx;     // total decompressed pixel count (all dirs + frames)
    /* Direction offsets follow: DWORD[bNumDirections] */
    /* Each is a file byte offset to the start of that direction's data */
} DCCHeader;
#pragma pack(pop)
```

### DCCDirHeader (per direction)

```c
typedef struct DCCDirHeader {
    DWORD dwOutSizeCoded;    // total bytes in compressed bitstream for this dir
    DWORD dwOutSizeDecoded;  // bytes after decompression
    // 5 compression flags (1 bit each):
    BYTE  bEqualCellsStreamPresent;
    BYTE  bPixelMaskStreamPresent;
    BYTE  bEncodingTypeStreamPresent;
    BYTE  bRawPixelCodeStreamPresent;
    BYTE  bCompressEqualCells;
    DWORD dwVar0Size;        // bit widths for variable-length fields
    DWORD dwWidthSize;
    DWORD dwHeightSize;
    DWORD dwXOffsetSize;
    DWORD dwYOffsetSize;
    DWORD dwOptionalBytesSize;
    DWORD dwCodedBytesSize;
} DCCDirHeader;
```

### DCCFrameHeader (per frame within direction)

```c
typedef struct DCCFrameHeader {
    DWORD dwVar0;            // misc data (varies by direction)
    DWORD dwWidth;           // frame width
    DWORD dwHeight;          // frame height
    LONG  lXOffset;          // X offset
    LONG  lYOffset;          // Y offset
    DWORD dwOptionalBytes;   // extra bytes (usually 0)
    DWORD dwCodedBytes;      // bytes of pixel data
    DWORD dwLastFrameFlag;   // 1 if this is the last frame
} DCCFrameHeader;
```

### DCC Decompression Algorithm

DCC uses a cell-based delta system with Huffman coding. Significantly more complex than DC6.

```c
/* High-level decompression pipeline */
void DCC_DecompressDirection(DCCDirection* pDir, BYTE* pOut) {
    /* Step 1: Determine bounding box for this direction */
    RECT bbox = DCC_CalcBBox(pDir);

    /* Step 2: For each frame: decode header fields from packed bit streams */
    for (DWORD f = 0; f < pDir->dwFrameCount; f++) {
        DCCFrame* pFrame = &pDir->pFrames[f];
        pFrame->dwWidth   = ReadBits(pDir->pWidthStream,   pDir->dwWidthSize);
        pFrame->dwHeight  = ReadBits(pDir->pHeightStream,  pDir->dwHeightSize);
        pFrame->lXOffset  = ReadSignedBits(pDir->pXOffStream, pDir->dwXOffSize);
        pFrame->lYOffset  = ReadSignedBits(pDir->pYOffStream, pDir->dwYOffSize);
    }

    /* Step 3: Build 4×4 pixel cells for each frame */
    DCC_BuildCells(pDir);

    /* Step 4: Decode pixel data using Equal Cells + Pixel Mask + Huffman */
    DCC_DecodePixels(pDir, pOut);
}

/* Cell pixel reconstruction */
void DCC_DecodePixels(DCCDirection* pDir, BYTE* pOut) {
    /* For each cell in each frame: */
    for (DWORD cellY = 0; cellY < numCellsY; cellY++) {
        for (DWORD cellX = 0; cellX < numCellsX; cellX++) {
            BOOL equalCell = ReadBit(pDir->pEqualCellStream);
            if (equalCell) {
                /* Copy cell from previous frame — delta compression */
                CopyCellFromPrevFrame(pOut, cellX, cellY);
            } else {
                /* Read new pixel data for this cell */
                BYTE pixelMask = ReadBits(pDir->pPixelMaskStream, 4);
                /* 4 bits correspond to 4 quadrants of the 4×4 cell */
                for (int quad = 0; quad < 4; quad++) {
                    if (pixelMask & (1 << quad)) {
                        /* Read Huffman-coded pixel value */
                        BYTE pixel = Huffman_Decode(pDir->pPixelStream);
                        WriteQuadPixels(pOut, cellX, cellY, quad, pixel);
                    }
                }
            }
        }
    }
}
```

---

## Palette System

D2 uses 256-color indexed palettes. Palette files are `.dat` files
loaded from MPQ: `data\global\palette\<area>\Pal.PL2`.

```c
/* D2 palette entry: 3-byte BGR (NOT RGB) */
typedef struct PaletteEntry {
    BYTE b, g, r;  /* blue first — matches DirectDraw PALETTEENTRY for old GPUs */
} PaletteEntry;

typedef struct D2Palette {
    PaletteEntry entries[256];     /* 768 bytes */
    BYTE         lightTable[32][256]; /* pre-computed light level variants */
    BYTE         shadowTable[256];    /* pre-computed shadow palette */
} D2Palette;

/* Active palette index — D2Win.dll+0xC8A0 (v1.13c) */
extern DWORD g_dwActivePalette;

/* D2Gfx.dll+0x9050 (v1.13c) — load palette for current act/area */
void D2Gfx_LoadPalette(DWORD dwPaletteId) {
    /* PaletteId 0=RogueCamp, 1=Act2, 2=Act3, 3=Act4, etc. */
    /* Reads Pal.PL2 for the area from MPQ */
    /* Sets g_dwActivePalette and uploads to DirectDraw palette */
}
```

### Pre-computed Blend Tables

D2 pre-computes all blending operations into lookup tables for speed.

```c
/* Located in each Pal.PL2 file — 116 tables of 256 entries = 29,696 bytes */
typedef struct PL2File {
    PaletteEntry  palette[256];           /* base palette */
    BYTE          lightLevel[32][256];    /* 32 light intensities */
    BYTE          alphaBlend[3][256];     /* 25/50/75% transparency tables */
    BYTE          additiveBlend[256];     /* additive blend (fire/lightning) */
    BYTE          screenBlend[256];       /* screen blend (aura glows) */
    BYTE          darkenTable[256];       /* darken palette (cave/dungeon) */
    BYTE          skyTable[256];          /* outdoor sky color mapping */
    BYTE          unitTransfer[13][256];  /* unit-specific color transforms */
    /* ... additional tables ... */
} PL2File;
```

---

## Font System

D2 fonts are stored as DC6 files with a corresponding `.tbl` index.

```
data\local\font\latin\font<size>.dc6   — glyph sprites
data\local\font\latin\font<size>.tbl   — glyph width table
```

```c
typedef struct FontGlyph {
    WORD  wChar;      /* Unicode character */
    BYTE  bWidth;     /* glyph advance width in pixels */
    BYTE  bHeight;    /* glyph height */
    WORD  wUnk;
    WORD  wFrameIdx;  /* DC6 frame index for this glyph */
} FontGlyph;

/* Render a string — D2Win.dll+0xF0A0 (v1.13c) */
void D2Win_DrawText(const WCHAR* pszText, DWORD dwX, DWORD dwY,
                    DWORD dwColor, DWORD dwFont) {
    /* Iterates characters, looks up FontGlyph, blits DC6 frame at current x,y */
    /* Advance x by glyph.bWidth each character */
}

/* Color codes for in-game text */
#define D2COLOR_WHITE    0
#define D2COLOR_RED      1
#define D2COLOR_GREEN    2  /* set item names */
#define D2COLOR_BLUE     3  /* magic item names */
#define D2COLOR_GOLD     4  /* unique item names / gold */
#define D2COLOR_GRAY     5  /* socketed gems / lore */
#define D2COLOR_BLACK    6
#define D2COLOR_TAN      7
#define D2COLOR_ORANGE   8  /* crafted item names */
#define D2COLOR_YELLOW   9  /* rare item names */
#define D2COLOR_DKGREEN  10 /* set item complete bonus */
#define D2COLOR_PURPLE   11 /* magic find / +skills */
```

---

## Animation Modes per Unit Type

### Player Animation Mode IDs

```c
typedef enum PlayerMode {
    PM_DEATH     = 0,  /* DT */
    PM_KNOCKOUT  = 1,  /* KN */
    PM_NEUTRAL   = 2,  /* NU — standing idle */
    PM_WALK      = 3,  /* WL */
    PM_RUN       = 4,  /* RN */
    PM_GETHIT    = 5,  /* GH */
    PM_TOWNNEUT  = 6,  /* TN — town walk idle */
    PM_TOWNWALK  = 7,  /* TW */
    PM_ATTACK1   = 8,  /* A1 */
    PM_ATTACK2   = 9,  /* A2 */
    PM_BLOCK     = 10, /* BL */
    PM_CAST      = 11, /* SC — spell cast */
    PM_THROW     = 12, /* TH */
    PM_KICK      = 13, /* KI — kick (Assassin) */
    PM_SEQUENCE  = 14, /* S1 — skill sequence */
    PM_DEAD      = 15, /* DD — corpse lying dead */
} PlayerMode;
```

### DCC File Naming Convention

```
data\global\monsters\<monster_token>\<direction_token>\<mode_code>
                                                            DT = death
                                                            A1 = attack1
                                                            WL = walk
                                                            NU = neutral/idle
                                                            GH = gethit
                                                            SK = skill
data\global\chars\<class_token>\<component_code>\<mode>.dc6

/* Component codes for player characters */
HD = head        TR = torso       LG = legs
RA = right arm   LA = left arm    RH = right hand (weapon)
LH = left hand   SH = shield      S1–S8 = special components
```
