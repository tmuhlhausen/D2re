# Getting Started with D2RE

This guide is the short path from a fresh checkout to a working D2RE command. The README remains the long-form reference; this page is the lantern at the cave mouth.

## What you need

- Python 3.8 or newer
- Git
- A terminal
- Optional, only for specific workflows:
  - Npcap on Windows or libpcap on Linux/macOS for live packet capture
  - A local Diablo II install if you want to extract MPQ data tables
  - A `.d2s` save file if you want to parse a character

D2RE does not ship Blizzard game assets or game data. Tools that need game data expect you to point them at files from your own installation.

## Install in one minute

```bash
git clone https://github.com/tmuhlhausen/D2re.git
cd D2re
python -m pip install -r requirements.txt
python -m pip install -e .
```

Check that the package entry point is available:

```bash
d2re --version
d2re --help
```

You can also run scripts directly, for example:

```bash
python scripts/item_roller.py --help
```

## Open the visual workbench

The fastest way to see the toolkit map is the local browser GUI:

```bash
d2re
```

You can also open it explicitly:

```bash
d2re gui
```

Generate static HTML without opening a browser:

```bash
d2re gui --static --out ./d2re-workbench.html --no-open
```

Show CLI help without opening the GUI:

```bash
d2re --no-gui
```

The Runic Workbench includes searchable modules, command builders, presets, favorites, browser-local run history, theme/density controls, output helpers, and guarded local execution for save parsing, item rolling, Treasure Class exploration, drop simulation, map research, packet decoding, and table extraction.

## First smoke test: no game files required

Run the packet sniffer demo mode. It uses built-in sample packets, so it does not require Diablo II, admin privileges, or a network interface.

```bash
python scripts/packet_sniffer.py --demo --verbose
```

Expected result: D2RE prints decoded sample packets with names, command bytes, and field annotations.

If this fails because `scapy` is missing, install dependencies again:

```bash
python -m pip install -r requirements.txt
```

## Parse a character save

Use this when you have a local `.d2s` file:

```bash
python scripts/d2s_parser.py "C:/Users/You/Saved Games/Diablo II/YourChar.d2s" --json
```

Common locations:

| Platform | Typical save location |
|---|---|
| Windows Classic / D2R offline | `C:/Users/<you>/Saved Games/Diablo II/` |
| Wine / Proton | varies by prefix, usually under `drive_c/users/<you>/Saved Games/` |
| macOS/Linux community setups | varies by wrapper or compatibility layer |

Start with `--json` if you want stable machine-readable output. Use the default text output when you want a quick human summary.

## Extract data tables from a D2 install

Many analysis tools become more useful after extracting `data/global/excel/*.txt` tables from MPQ archives.

```bash
python scripts/mpq_extract.py --all-mpqs "C:/Diablo II/" --out ./data_tables/
```

After extraction, tools such as treasure-class exploration and item simulation can use generated table data.

## Explore treasure classes

After generating `data_tables/tc_tree.json`, inspect a treasure class:

```bash
python scripts/tc_explorer.py --tc "Act 5 Super C"
```

Resolve a treasure class into terminal drops:

```bash
python scripts/tc_explorer.py --tc "Act 5 Super C" --resolve --top 25
```

Use JSON when scripting:

```bash
python scripts/tc_explorer.py --tc "Act 5 Super C" --resolve --json
```

## Run item simulations

Roll one deterministic seed:

```bash
python scripts/item_roller.py --seed 0xDEADBEEF --ilvl 85 --mf 300
```

Simulate a quality distribution for a base item:

```bash
python scripts/item_roller.py --base 7cr --ilvl 87 --mf 300 --runs 100000
```

Current limitation: `--brute` and `--target` are intentionally registered but disabled while brute-force seed search is implemented safely.

## Use the unified CLI

The package entry point forwards to the underlying tools:

```bash
d2re parse MyChar.d2s --json
d2re roll --seed 0xDEADBEEF --ilvl 85 --mf 300
d2re tc --tc "Act 5 Super C" --resolve --top 25
d2re drops --tc "Mephisto (N)" --item weap87 --runs 250000
d2re gui --static --out ./d2re-workbench.html --no-open
```

Current limitation: `d2re doctor` is intentionally visible but disabled. It is reserved for the upcoming self-check work.

## Troubleshooting

### `ModuleNotFoundError: scapy`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### Packet capture needs admin/root

Live capture requires elevated privileges on most platforms. Demo mode does not:

```bash
python scripts/packet_sniffer.py --demo --verbose
```

### Treasure class file not found

Generate the TC tree first:

```bash
python scripts/mpq_extract.py --all-mpqs "C:/Diablo II/" --out ./data_tables/ --tc-tree
```

### A command says it is disabled

That is deliberate for planned surfaces that were previously advertised before implementation. See `docs/maintenance/cleanup-checklist.md` for the staged cleanup and implementation plan.

## Next reading

- `README.md` for the full project overview
- `docs/gui-workbench.md` for GUI details
- `references/d2s-format.md` for save-file internals
- `references/item-generation.md` for item rolling and Treasure Class logic
- `references/packets.md` for protocol definitions
- `docs/maintenance/cleanup-checklist.md` for current cleanup status
