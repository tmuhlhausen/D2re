#!/usr/bin/env python3
"""Wrapper for the item roller implementation.
Intercepts help output to avoid argparse percent-formatting issues.
"""

import sys

HELP_TEXT = """usage: item_roller.py [-h] [--seed SEED] [--base BASE] [--ilvl ILVL] [--mf MF]\n                      [--mlvl MLVL] [--alvl ALVL] [--tc TC] [--runs RUNS]\n                      [--brute] [--target TARGET] [--affix]\n\nD2 item generation simulator\n\noptions:\n  -h, --help       show this help message and exit\n  --seed SEED      Item seed (hex or dec)\n  --base BASE      Base item code (e.g. 'swrd', '7cf')\n  --ilvl ILVL\n  --mf MF          Magic Find %\n  --mlvl MLVL      Monster level\n  --alvl ALVL      Area level\n  --tc TC          Treasure class name to simulate\n  --runs RUNS\n  --brute          Brute-force seeds for target\n  --target TARGET  Target item name for brute-force\n  --affix          Roll magic affixes\n"""

if "-h" in sys.argv or "--help" in sys.argv:
    print(HELP_TEXT)
    raise SystemExit(0)

from tools.item_roller_impl import main

if __name__ == "__main__":
    main()
