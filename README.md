# D2RE — Diablo II Reverse Engineering Toolkit

D2RE is a Python toolkit for researching, documenting, and experimenting with Diablo II internals. It focuses on save parsing, packet decoding, MPQ/CASC data extraction, item generation simulation, map seed analysis, and reference documentation for reverse engineering work.

> This project is for research, modding, education, interoperability, and private/offline experimentation. It does not ship Blizzard game assets or game code.

## Quick start

```bash
git clone https://github.com/tmuhlhausen/D2re.git
cd D2re
python -m pip install -r requirements.txt
python -m pip install -e .
```

Open the visual workbench:

```bash
d2re
```

Show CLI help without launching the GUI:

```bash
d2re --no-gui
```

Run a no-game-files smoke test:

```bash
python scripts/packet_sniffer.py --demo --verbose
```

For a fuller first-run walkthrough, see [`docs/getting-started.md`](docs/getting-started.md).

## What D2RE contains

| Area | What it does |
|---|---|
| Visual workbench | Opens a local Runic Workbench GUI with command builders, presets, favorites, run history, guarded execution, and dark gothic panels. |
| Save parsing | Reads `.d2s` character files, including headers, stats, skills, items, quests, waypoints, and checksum state. |
| Packet decoding | Captures or decodes Diablo II protocol packets and annotates known command bytes. |
| Archive extraction | Extracts Classic D2 MPQ data tables and D2R CASC data when optional dependencies are available. |
| Item simulation | Simulates quality rolls, Magic Find effects, affix selection helpers, and Treasure Class workflows. |
| Map research | Reads and derives seeds, explores map-generation behavior, and renders predicted layouts. |
| References | Documents function offsets, packets, stats, combat formulas, item generation, DRLG, AI, skills, save format, sprite formats, Ghidra workflows, and D2R differences. |

## Repository layout

```text
D2re/
├── d2re/                       # Installable package, CLI, and GUI workbench
│   ├── cli.py
│   ├── gui.py
│   ├── gui_integrated.py
│   └── gui_beautified.py
├── scripts/                    # User-facing script entry points
│   ├── d2s_parser.py
│   ├── drop_calculator.py
│   ├── item_roller.py
│   ├── map_seed_tool.py
│   ├── mpq_extract.py
│   ├── packet_sniffer.py
│   └── tc_explorer.py
├── tools/                      # Implementation modules used by script wrappers
├── references/                 # Deep reverse-engineering references
├── docs/                       # Guides, architecture docs, and maintenance notes
│   ├── architecture/
│   ├── maintenance/
│   ├── getting-started.md
│   ├── gui-workbench.md
│   ├── hooking-guide.md
│   └── emulator-server-guide.md
├── examples/                   # Small example workflows when present
├── tests/                      # Smoke and regression tests
├── pyproject.toml
├── requirements.txt
├── ROADMAP.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

## Common commands

Open the Runic Workbench:

```bash
d2re
```

Generate static workbench HTML:

```bash
d2re gui --static --out ./d2re-workbench.html --no-open
```

Parse a save file:

```bash
python scripts/d2s_parser.py "C:/Users/You/Saved Games/Diablo II/YourChar.d2s" --json
```

Run the packet demo:

```bash
python scripts/packet_sniffer.py --demo --verbose
```

Extract data tables from a Classic D2 install:

```bash
python scripts/mpq_extract.py --all-mpqs "C:/Diablo II/" --out ./data_tables/
```

Explore a Treasure Class after generating `data_tables/tc_tree.json`:

```bash
python scripts/tc_explorer.py --tc "Act 5 Super C" --resolve --top 25
```

Roll a deterministic item-generation seed:

```bash
python scripts/item_roller.py --seed 0xDEADBEEF --ilvl 85 --mf 300
```

Use the unified CLI wrapper:

```bash
d2re parse MyChar.d2s --json
d2re roll --seed 0xDEADBEEF --ilvl 85 --mf 300
d2re tc --tc "Act 5 Super C" --resolve --top 25
d2re drops --tc "Mephisto (N)" --item weap87 --runs 250000
```

## Command status

Some command surfaces are intentionally visible but disabled while they are implemented safely.

| Command or flag | Current status |
|---|---|
| `d2re` | Active; opens the Runic Workbench by default |
| `d2re --no-gui` | Active; prints CLI help without opening the GUI |
| `d2re gui` | Active |
| `d2re parse` | Active |
| `d2re roll` | Active |
| `d2re extract` | Active |
| `d2re sniff` | Active |
| `d2re map` | Active |
| `d2re tc` | Active |
| `d2re drops` | Active |
| `d2re doctor` | Registered but temporarily disabled |
| `item_roller --brute` | Registered but temporarily disabled |
| `item_roller --target` | Registered but temporarily disabled |

The disabled surfaces are tracked in [`docs/maintenance/cleanup-checklist.md`](docs/maintenance/cleanup-checklist.md).

## Documentation map

| Document | Use it for |
|---|---|
| [`docs/getting-started.md`](docs/getting-started.md) | First-run onboarding and common workflows. |
| [`docs/gui-workbench.md`](docs/gui-workbench.md) | Runic Workbench usage, safety model, and UI behavior. |
| [`ROADMAP.md`](ROADMAP.md) | Planned expansion, QoL goals, and long-term direction. |
| [`docs/architecture/testing-strategy.md`](docs/architecture/testing-strategy.md) | Testing philosophy and fixture strategy. |
| [`docs/maintenance/cleanup-checklist.md`](docs/maintenance/cleanup-checklist.md) | Current cleanup status and staged implementation plan. |
| [`docs/hooking-guide.md`](docs/hooking-guide.md) | Draft hook-research guide index. |
| [`docs/emulator-server-guide.md`](docs/emulator-server-guide.md) | Draft emulator/server research guide index. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution rules, style standards, and verification expectations. |

## Reference map

| Reference | Topic |
|---|---|
| `references/function-offsets.md` | Versioned function offsets and key addresses. |
| `references/packets.md` | Packet definitions and C-style structs. |
| `references/stat-ids.md` | Stat IDs and bit-width encoding notes. |
| `references/combat-formulas.md` | Combat, damage, Magic Find, and breakpoint formulas. |
| `references/item-generation.md` | Treasure Classes, quality rolls, affixes, gambling, crafting. |
| `references/drlg-map-gen.md` | Dungeon random level generation and seed behavior. |
| `references/ai-states.md` | Monster AI states and boss modifier notes. |
| `references/skill-system.md` | Skills, auras, charges, procs, and missile chains. |
| `references/d2s-format.md` | Byte-level `.d2s` file structure. |
| `references/dcc-dc6-format.md` | Sprite and animation formats. |
| `references/ghidra-scripts.md` | Ghidra automation workflows. |
| `references/d2r-resurrected.md` | D2R-specific differences and research notes. |

## Testing

Run the current smoke tests with the standard library:

```bash
python -m unittest discover tests
```

The current tests protect disabled command behavior, default GUI startup, guarded GUI execution, token rejection, static HTML output, and Runic Workbench UI markers.

## Legal notice

This project contains no game code, no game assets, and no copyrighted material from Diablo II or Diablo II: Resurrected. It contains documentation, reconstructed structures, and independent Python tooling for files and data owned by the user.

Diablo II and Diablo II: Resurrected are trademarks of Blizzard Entertainment, Inc. This project is not affiliated with or endorsed by Blizzard Entertainment.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening issues or pull requests. The best contributions are verified corrections, small tested improvements, clearer docs, and fixtures with clean provenance.
