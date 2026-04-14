#!/usr/bin/env python3
"""examples/find_best_seed.py — simple wrapper around map_seed_tool brute force mode."""

import os
import sys
import subprocess

if __name__ == "__main__":
    script = os.path.join(os.path.dirname(__file__), "..", "scripts", "map_seed_tool.py")
    raise SystemExit(subprocess.call([sys.executable, script, *sys.argv[1:]]))
