# Unified D2RE CLI

D2RE now ships with a single installed command, `d2re`, that dispatches to the repository's main tools.

## Available subcommands

- `d2re parse` → `scripts/d2s_parser.py`
- `d2re roll` → `scripts/item_roller.py`
- `d2re extract` → `scripts/mpq_extract.py`
- `d2re sniff` → `scripts/packet_sniffer.py`
- `d2re map` → `scripts/map_seed_tool.py`

## Examples

```bash
# Parse a save file
d2re parse MyChar.d2s --json

# Simulate item generation
d2re roll --seed 0xDEADBEEF --ilvl 85 --mf 300

# Extract a single data table
d2re extract --all-mpqs "C:/Diablo II/" --table weapons --csv

# Run the packet sniffer in demo mode
d2re sniff --demo --verbose

# Analyze a map seed from a save file
d2re map --d2s MyChar.d2s --level 15 --ascii
```

## Alternate entry points

The package also installs direct console aliases:

- `d2re-parse`
- `d2re-roll`
- `d2re-extract`
- `d2re-sniff`
- `d2re-map`

These are useful if you prefer one binary per tool while still using package installs.
