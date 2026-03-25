#!/usr/bin/env python3
"""
mpq_extract.py — Diablo II MPQ archive extractor and data table parser
Extracts all data tables, sprites, and string tables from D2 MPQ archives.

Requirements:
    pip install mpyq   (for MPQ access)
    pip install casc-extractor  (for D2R CASC access, optional)

Usage:
    python mpq_extract.py --mpq d2data.mpq --out ./extracted/
    python mpq_extract.py --mpq d2data.mpq --table weapons --csv
    python mpq_extract.py --all-mpqs "C:/Diablo II/" --out ./extracted/
    python mpq_extract.py --d2r "C:/Diablo II Resurrected/" --out ./extracted/
"""

import os, sys, csv, json, argparse, struct
from pathlib import Path
from typing import Dict, List, Optional, Any

# ─────────────────────────────────────────────────────────────────────────────
# MPQ access (requires mpyq)
# ─────────────────────────────────────────────────────────────────────────────

def open_mpq(path: str):
    try:
        import mpyq
        return mpyq.MPQArchive(path)
    except ImportError:
        raise ImportError("mpyq required: pip install mpyq")


class D2DataExtractor:
    """Extract and parse D2 data tables from MPQ archives."""

    # MPQ files in load order (later files override earlier)
    MPQ_LOAD_ORDER = [
        "d2data.mpq",
        "d2exp.mpq",
        "patch_d2.mpq",
    ]

    # All data table files in D2
    DATA_TABLES = [
        "weapons", "armor", "misc",
        "skills", "skilldesc",
        "monstats", "monstats2", "montype", "monpreset",
        "monstats", "monsounds", "monumod",
        "levels", "lvlprest", "lvlmaze", "lvlwarp", "lvlsub",
        "objects", "objgroup", "objpreset",
        "missiles", "states",
        "itemstatcost", "itemratio", "itemtypes",
        "belts", "inventory",
        "uniqueitems", "setitems", "sets",
        "runes", "gems",
        "cubemain",
        "treasureclassex",
        "hireling",
        "experience", "charstats",
        "plrmode", "monmode",
        "superuniques",
        "automagic", "magicprefix", "magicsuffix",
        "rareprefix", "raresuffix",
        "properties",
        "bodylocs", "storepages",
        "wanderingtrades",
        "npc",
        "difficultylevels",
    ]

    def __init__(self, *mpq_paths: str):
        self.archives = []
        for p in mpq_paths:
            if os.path.exists(p):
                self.archives.append(open_mpq(p))
        if not self.archives:
            raise FileNotFoundError(f"No MPQ archives found at: {mpq_paths}")

    @classmethod
    def from_install_dir(cls, d2_dir: str) -> "D2DataExtractor":
        """Open all MPQ files from a D2 installation directory."""
        paths = []
        for mpq_name in cls.MPQ_LOAD_ORDER:
            full = os.path.join(d2_dir, mpq_name)
            if os.path.exists(full):
                paths.append(full)
        return cls(*paths)

    def read_file(self, mpq_path: str) -> Optional[bytes]:
        """Read a file from the archive chain (later archives override earlier)."""
        data = None
        for archive in self.archives:
            try:
                result = archive.read_file(mpq_path)
                if result:
                    data = result
            except Exception:
                pass
        return data

    def get_table(self, table_name: str) -> List[Dict[str, str]]:
        """Parse a data table TSV file into a list of row dicts."""
        mpq_path = f"data\\global\\excel\\{table_name}.txt"
        raw = self.read_file(mpq_path)
        if raw is None:
            # Try alternate path formats
            mpq_path = f"data/global/excel/{table_name}.txt"
            raw = self.read_file(mpq_path)
        if raw is None:
            raise FileNotFoundError(f"Table not found: {table_name}")

        text = raw.decode("latin-1")
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        if len(lines) < 3:
            return []

        headers = lines[0].split("\t")
        # Skip header types row (row 2 in D2 format)
        rows = []
        for line in lines[2:]:
            if not line.strip():
                continue
            cols = line.split("\t")
            # Pad/trim to match headers
            while len(cols) < len(headers):
                cols.append("")
            rows.append(dict(zip(headers, cols[:len(headers)])))

        return rows

    def get_all_tables(self) -> Dict[str, List[Dict[str, str]]]:
        """Extract all known data tables."""
        result = {}
        for table in self.DATA_TABLES:
            try:
                result[table] = self.get_table(table)
                print(f"  ✓ {table} ({len(result[table])} rows)")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"  ✗ {table}: {e}")
        return result

    def get_string_table(self, locale: str = "ENG") -> Dict[str, str]:
        """Parse a .tbl string table file."""
        mpq_path = f"data\\local\\lng\\{locale}\\string.tbl"
        raw = self.read_file(mpq_path)
        if raw is None:
            return {}
        return parse_tbl(raw)

    def extract_all_to_dir(self, out_dir: str):
        """Extract everything to a directory."""
        os.makedirs(out_dir, exist_ok=True)
        for archive in self.archives:
            for fname in archive.files:
                fname_str = fname.decode("ascii", errors="replace")
                out_path = os.path.join(out_dir, fname_str.replace("\\", "/"))
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                try:
                    data = archive.read_file(fname.decode())
                    if data:
                        with open(out_path, "wb") as f:
                            f.write(data)
                        print(f"  → {fname_str}")
                except Exception as e:
                    print(f"  ✗ {fname_str}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# .tbl String Table Parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_tbl(data: bytes) -> Dict[str, str]:
    """
    Parse a Diablo II .tbl string table file.

    .tbl binary format:
      TblHeader (21 bytes)
      WORD[wHashTableSize]  hash table
      TblNode[wNumEntries]  per-entry metadata
      Then string data at offsets specified by TblNode
    """
    if len(data) < 21:
        return {}

    (crc, num_nodes, hash_table_size, unk1, unk2,
     data_start_offset, hash_table_offset,
     total_size) = struct.unpack_from("<HHHBBIcI", data, 0)

    strings = {}
    offset = 21  # TblHeader size

    # Read hash nodes
    for i in range(num_nodes):
        if offset + 9 > len(data):
            break
        active, hash_idx, unknown, key_offset, str_offset, str_len = \
            struct.unpack_from("<BHHIII", data, offset)
        offset += 17

        if active and key_offset < len(data) and str_offset < len(data):
            try:
                key = data[key_offset:data.find(b"\x00", key_offset)].decode("latin-1")
                val = data[str_offset:data.find(b"\x00", str_offset)].decode("latin-1")
                strings[key] = val
            except Exception:
                pass

    return strings


# ─────────────────────────────────────────────────────────────────────────────
# Item stats cross-reference builder
# ─────────────────────────────────────────────────────────────────────────────

def build_item_stat_reference(extractor: D2DataExtractor) -> Dict[str, Any]:
    """Build a cross-reference of item codes → possible stats → affixes."""
    weapons  = extractor.get_table("weapons")
    armor    = extractor.get_table("armor")
    misc     = extractor.get_table("misc")
    mprefix  = extractor.get_table("magicprefix")
    msuffix  = extractor.get_table("magicsuffix")

    ref = {
        "weapons": {row["code"]: row for row in weapons if row.get("code")},
        "armor":   {row["code"]: row for row in armor   if row.get("code")},
        "misc":    {row["code"]: row for row in misc     if row.get("code")},
        "magic_prefixes": [r for r in mprefix if r.get("Name")],
        "magic_suffixes": [r for r in msuffix if r.get("Name")],
    }
    return ref


# ─────────────────────────────────────────────────────────────────────────────
# Treasure Class tree builder
# ─────────────────────────────────────────────────────────────────────────────

def build_tc_tree(extractor: D2DataExtractor) -> Dict[str, Any]:
    """Build a navigable treasure class tree for drop simulation."""
    tc_table = extractor.get_table("treasureclassex")
    tree = {}
    for row in tc_table:
        name = row.get("Treasure Class", "")
        if not name:
            continue
        picks = int(row.get("Picks", "1") or "1")
        nodrop = int(row.get("NoDrop", "0") or "0")
        entries = []
        for i in range(1, 11):
            item_key = f"Item{i}"
            prob_key = f"Prob{i}"
            item = row.get(item_key, "")
            prob = row.get(prob_key, "")
            if item and prob:
                try:
                    entries.append({"item": item, "prob": int(prob)})
                except ValueError:
                    pass
        tree[name] = {"picks": picks, "nodrop": nodrop, "entries": entries}
    return tree


# ─────────────────────────────────────────────────────────────────────────────
# D2R CASC extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_d2r(d2r_dir: str, out_dir: str):
    """Extract D2R data tables from CASC storage."""
    try:
        import pycasc
        storage = pycasc.open(d2r_dir)
        os.makedirs(out_dir, exist_ok=True)
        for entry in storage.find("*.txt"):
            if "excel" in entry.name.lower():
                out_path = os.path.join(out_dir, os.path.basename(entry.name))
                data = storage.read(entry.name)
                if data:
                    with open(out_path, "wb") as f:
                        f.write(data)
                    print(f"  → {os.path.basename(entry.name)}")
    except ImportError:
        print("pycasc not installed. Install with: pip install pycasc")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="D2 MPQ extractor and data parser")
    ap.add_argument("--mpq",       help="Path to single MPQ file")
    ap.add_argument("--all-mpqs",  help="D2 installation directory (loads all MPQs)")
    ap.add_argument("--d2r",       help="D2R installation directory")
    ap.add_argument("--out",       default="./extracted", help="Output directory")
    ap.add_argument("--table",     help="Extract a single table by name")
    ap.add_argument("--csv",       action="store_true", help="Write tables as CSV")
    ap.add_argument("--json-out",  action="store_true", help="Write tables as JSON")
    ap.add_argument("--tc-tree",   action="store_true", help="Build TC drop tree")
    ap.add_argument("--strings",   action="store_true", help="Extract string tables")
    args = ap.parse_args()

    if args.d2r:
        extract_d2r(args.d2r, args.out)
        return

    # Build extractor
    if args.mpq:
        ext = D2DataExtractor(args.mpq)
    elif args.all_mpqs:
        ext = D2DataExtractor.from_install_dir(args.all_mpqs)
    else:
        ap.print_help()
        return

    os.makedirs(args.out, exist_ok=True)

    if args.table:
        rows = ext.get_table(args.table)
        print(f"Table '{args.table}': {len(rows)} rows")
        if args.csv:
            path = os.path.join(args.out, f"{args.table}.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            print(f"  → {path}")
        if args.json_out:
            path = os.path.join(args.out, f"{args.table}.json")
            with open(path, "w") as f:
                json.dump(rows, f, indent=2)
            print(f"  → {path}")
        if not args.csv and not args.json_out:
            for row in rows[:10]:
                print(" ", {k: v for k, v in row.items() if v})
            if len(rows) > 10:
                print(f"  ... ({len(rows)-10} more rows)")
        return

    if args.tc_tree:
        tree = build_tc_tree(ext)
        path = os.path.join(args.out, "tc_tree.json")
        with open(path, "w") as f:
            json.dump(tree, f, indent=2)
        print(f"TC tree saved to {path} ({len(tree)} entries)")
        return

    if args.strings:
        strs = ext.get_string_table()
        path = os.path.join(args.out, "strings.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(strs, f, indent=2, ensure_ascii=False)
        print(f"String table saved to {path} ({len(strs)} entries)")
        return

    # Default: extract all tables
    print("Extracting all data tables...")
    tables = ext.get_all_tables()
    for name, rows in tables.items():
        path = os.path.join(args.out, f"{name}.csv")
        if rows:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    print(f"\nDone. {len(tables)} tables extracted to {args.out}/")


if __name__ == "__main__":
    main()
