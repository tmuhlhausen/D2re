# Changelog

All notable changes to D2RE are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2024-XX-XX  *(Initial Public Release)*

### Added — Scripts

- **`scripts/packet_sniffer.py`** — Full D2 packet capture and annotator.
  - Live capture via Scapy on ports 4000 and 6112.
  - Decodes ~80 known C2S and S2C packet types with field-level definitions.
  - Rich plain-English explanations for every packet: what triggers it, what
    each field means, what the server/client does with it.
  - `GameStateTracker` for contextual annotations: active skill names, HP drop
    warnings, latency estimates, suspicious pattern detection.
  - Field enrichment: unit types, skill IDs, stat IDs, waypoint names,
    state IDs, mode names all decoded to human-readable strings.
  - Color-coded output by packet category (movement, combat, item, skill, etc.).
  - `--demo` mode: runs against hardcoded sample packets, no network required.
  - `--generate-structs`: outputs C struct definitions for all known packets.
  - `--list`: prints all known packets with command bytes and categories.
  - Session summary on Ctrl+C: packet frequency table, suspicious activity log.
  - JSON output for offline analysis.

- **`scripts/d2s_parser.py`** — Complete `.d2s` save file parser.
  - Parses all sections: header, quests, waypoints, NPC flags, stats (bit-stream),
    skills, items, corpse items, mercenary items.
  - Full item bit-stream decoder: quality, affixes, ethereal, socketed sub-items,
    personalized name, ear data.
  - Checksum verification (D2's rotate-and-add algorithm).
  - JSON output mode for programmatic use.
  - `BitReader` class for LSB-first variable-width bit fields.

- **`scripts/mpq_extract.py`** — MPQ archive extractor and data table parser.
  - Extracts all 40+ data tables to CSV or JSON.
  - `.tbl` string table parser.
  - Treasure Class tree builder for drop simulation.
  - D2R CASC extraction support (requires `pycasc`).
  - Handles multi-MPQ load order with proper override semantics.

- **`scripts/item_roller.py`** — Item generation pipeline simulator.
  - Implements the full 6-stage D2 item generation pipeline in Python.
  - Exact LCG PRNG matching D2's `D2Common.dll+0x1B1A0`.
  - Quality determination with correct MF diminishing returns per quality tier.
  - Magic affix rolling with iLvl filtering.
  - Treasure Class drop Monte Carlo simulation.
  - Item level formulas for monsters, gambling, and crafting.

- **`scripts/map_seed_tool.py`** — Map seed analyzer and BSP predictor.
  - Reads map seed from `.d2s` save files.
  - Derives per-act and per-level seeds using the same LCG as the game.
  - BSP room layout predictor using D2's exact partition algorithm.
  - ASCII map renderer.
  - Entrance/exit room heuristics.
  - Seed brute-forcer with custom predicate support.
  - 134-entry level ID reference.

### Added — References

- **`references/function-offsets.md`** — Virtual address table for 80+ key
  functions across D2 v1.09d, v1.12a, v1.13c, and v1.14d. Covers D2Common,
  D2Game, D2Client, D2Net, Fog, D2Lang, D2Win, Storm. Includes global pointer
  addresses.

- **`references/packets.md`** — Complete C2S/S2C packet library with C struct
  definitions, field descriptions, and category tags.

- **`references/stat-ids.md`** — All 220+ stat IDs from `itemstatcost.txt`,
  with CSvBits widths, encoding notes (fixed-point, signed, etc.).

- **`references/combat-formulas.md`** — Verified formulas: PvM/PvP hit chance,
  physical damage pipeline, elemental pipeline with absorb ordering, Open
  Wounds rate, IAS/FCR/FHR breakpoint tables (per class), experience loss on death.

- **`references/item-generation.md`** — 6-stage item gen pipeline in C and
  Python: TC recursion, iLvl math, quality cascade, magic/rare/unique affix
  rolling, cube recipe structure, gambling/crafting iLvl formulas.

- **`references/drlg-map-gen.md`** — BSP maze algorithm in C, outdoor stamp
  system, 3 population passes (presets, monsters, objects), level ID enum
  (134 values), map seed cascade derivation, map seed extraction from memory.

- **`references/ai-states.md`** — Selected AI code table entries from D2Game's
  300-entry dispatch table, boss modifier bitmasks, flee system, aggro
  system reconstruction, phase detection pattern.

- **`references/skill-system.md`** — Skill ID tables for all 7 classes (170+
  entries), proc/charge mechanics, aura pulse reconstruction, missile chain
  examples (Lightning Fury, Meteor).

- **`references/d2s-format.md`** — Byte-exact `.d2s` format: every field in
  the fixed header, all variable sections with magic numbers, item bit-stream
  field table with bit widths, quest ID table (Act 1), checksum algorithm.

- **`references/dcc-dc6-format.md`** — DC6 RLE decompression algorithm in C,
  DCC delta/Huffman decompression pipeline, PL2 palette format (32 light
  levels + blend tables), font system with glyph structs, animation mode IDs,
  DCC file naming conventions.

- **`references/ghidra-scripts.md`** — 5 Ghidra Python scripts:
  `D2_ImportSymbols.py`, `D2_FindUnitAny.py`, `D2_MapPacketHandlers.py`,
  `D2_ExportOffsets.py`, `D2_AnnotateStatEngine.py`, `D2_FindVersionString.py`.

- **`references/d2r-resurrected.md`** — D2R vs Classic comparison table,
  64-bit `UnitAny` approximate layout, CASC access in C and Python, JSON
  override format with examples, DX12 swap chain hook pattern, `.anim` header,
  RIP-relative pattern scanning for D2R memory reading.

### Added — Core Documentation

- **`SKILL.md`** — Full 22-section reverse engineering skill document for
  Claude AI integration. Covers all engine subsystems with annotated C code,
  calling convention identification, complete data structures, and methodology.

- **`README.md`** — This file. 800+ lines explaining every aspect of the
  project with scenarios, worked examples, and conceptual explanations.

- **`CONTRIBUTING.md`** — Detailed contribution guide with style standards.

- **`LICENSE`** — MIT License with additional notice on intended use.

- **`requirements.txt`** — Annotated dependency list with optional sections.

---

## Planned for [1.1.0]

- Example scripts in `examples/` with inline tutorials
- `docs/hooking-guide.md` — step-by-step guide to writing a D2 hook DLL
- `docs/emulator-server-guide.md` — D2GS architecture and packet handling
- Automated tests for `d2s_parser.py` and `item_roller.py`
- Additional packet definitions for remaining unknown command bytes
- D2R patch-specific offset table (kept up to date with patches)
- Ghidra project file with pre-applied symbols for v1.13c

---

## Planned for [1.2.0]

- Interactive web-based packet decoder (HTML/JS, no server required)
- Character planner integration with `d2s_parser.py` output
- Bulk save file analyzer for batch item auditing
- Collision map extractor from DS1/DT1 files
- Monster drop rate calculator with full TC tree visualization
