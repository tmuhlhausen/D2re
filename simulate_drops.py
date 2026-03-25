# D2RE — Python Dependencies
# Install with: pip install -r requirements.txt

# ── Core (required for all scripts) ──────────────────────────────────────────
# No mandatory third-party deps for d2s_parser.py and item_roller.py.
# Standard library only: struct, argparse, json, dataclasses, pathlib, csv

# ── Packet Sniffer ────────────────────────────────────────────────────────────
# Live packet capture (requires Npcap on Windows, libpcap on Linux/macOS)
scapy>=2.5.0

# Color terminal output (gracefully degrades if missing)
colorama>=0.4.6

# ── MPQ Extraction (Classic D2) ───────────────────────────────────────────────
# Pure-Python MPQ reader — works for d2data.mpq, d2exp.mpq, patch_d2.mpq
mpyq>=0.2.5

# ── CASC Extraction (D2 Resurrected) ─────────────────────────────────────────
# Optional — only needed if you work with D2R's CASC archives
# Uncomment to install:
# pycasc>=1.0.0

# ── Optional: Faster binary parsing ──────────────────────────────────────────
# The bit-stream parser in d2s_parser.py uses pure Python by default.
# For very large batch operations, installing bitarray speeds it up 10–20×.
# bitarray>=2.8.0

# ── Development / Testing ─────────────────────────────────────────────────────
# Uncomment for development:
# pytest>=7.0.0
# pytest-cov>=4.0.0
# black>=23.0.0
# mypy>=1.0.0
