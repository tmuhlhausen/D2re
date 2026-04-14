#!/usr/bin/env python3
"""Unified command line interface for D2RE.

This wraps the repository's existing scripts behind a single installed command.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Iterable, List

from . import __version__

SCRIPT_MODULES = {
    "parse": ("scripts.d2s_parser", "d2s_parser.py"),
    "roll": ("scripts.item_roller", "item_roller.py"),
    "extract": ("scripts.mpq_extract", "mpq_extract.py"),
    "sniff": ("scripts.packet_sniffer", "packet_sniffer.py"),
    "map": ("scripts.map_seed_tool", "map_seed_tool.py"),
}


def _dispatch(module_name: str, argv: List[str], prog_name: str) -> int:
    old_argv = sys.argv[:]
    try:
        sys.argv = [prog_name, *argv]
        module = importlib.import_module(module_name)
        if not hasattr(module, "main"):
            raise SystemExit(f"{module_name} does not expose a main() entry point")
        result = module.main()
        if result is None:
            return 0
        if isinstance(result, int):
            return result
        return 0
    finally:
        sys.argv = old_argv


def _add_passthrough_parser(subparsers: argparse._SubParsersAction, name: str, help_text: str) -> None:
    parser = subparsers.add_parser(
        name,
        help=help_text,
        description=help_text,
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the underlying script.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="d2re",
        description="Unified CLI for the D2RE toolkit.",
        epilog=(
            "Examples:\n"
            "  d2re parse MyChar.d2s --json\n"
            "  d2re roll --seed 0xDEADBEEF --ilvl 85 --mf 300\n"
            "  d2re extract --all-mpqs 'C:/Diablo II/' --table weapons --csv\n"
            "  d2re sniff --demo --verbose\n"
            "  d2re map --d2s MyChar.d2s --level 15 --ascii"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"d2re {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    _add_passthrough_parser(subparsers, "parse", "Run the .d2s save parser.")
    _add_passthrough_parser(subparsers, "roll", "Run the item generation simulator.")
    _add_passthrough_parser(subparsers, "extract", "Run the MPQ / CASC extractor.")
    _add_passthrough_parser(subparsers, "sniff", "Run the packet sniffer.")
    _add_passthrough_parser(subparsers, "map", "Run the map seed analysis tool.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    parser = build_parser()
    ns = parser.parse_args(args)

    if not ns.command:
        parser.print_help()
        return 0

    module_name, prog_name = SCRIPT_MODULES[ns.command]
    return _dispatch(module_name, ns.args, prog_name)


def parse_main() -> int:
    return _dispatch("scripts.d2s_parser", sys.argv[1:], "d2s_parser.py")


def roll_main() -> int:
    return _dispatch("scripts.item_roller", sys.argv[1:], "item_roller.py")


def extract_main() -> int:
    return _dispatch("scripts.mpq_extract", sys.argv[1:], "mpq_extract.py")


def sniff_main() -> int:
    return _dispatch("scripts.packet_sniffer", sys.argv[1:], "packet_sniffer.py")


def map_main() -> int:
    return _dispatch("scripts.map_seed_tool", sys.argv[1:], "map_seed_tool.py")
