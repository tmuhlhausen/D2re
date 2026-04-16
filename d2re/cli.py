#!/usr/bin/env python3
"""Unified command line interface for D2RE."""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Iterable, List, Tuple

from . import __version__

SCRIPT_MODULES: dict[str, Tuple[str, str]] = {
    "parse": ("scripts.d2s_parser", "d2s_parser.py"),
    "roll": ("scripts.item_roller", "item_roller.py"),
    "extract": ("scripts.mpq_extract", "mpq_extract.py"),
    "sniff": ("scripts.packet_sniffer", "packet_sniffer.py"),
    "map": ("scripts.map_seed_tool", "map_seed_tool.py"),
    "tc": ("scripts.tc_explorer", "tc_explorer.py"),
    "drops": ("scripts.drop_calculator", "drop_calculator.py"),
    "doctor": ("d2re.doctor", "d2re-doctor"),
    "gui": ("d2re.gui", "d2re-gui"),
}


def _dispatch(module_name: str, argv: List[str], prog_name: str) -> int:
    old_argv = sys.argv[:]
    forwarded = list(argv)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    try:
        sys.argv = [prog_name, *forwarded]
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


def _add_passthrough_parser(
    subparsers: argparse._SubParsersAction,
    name: str,
    help_text: str,
) -> None:
    parser = subparsers.add_parser(
        name,
        help=help_text,
        description=help_text,
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the underlying module.",
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
            "  d2re tc --tc 'Act 5 Super C' --resolve --top 25\n"
            "  d2re drops --tc 'Mephisto (N)' --item weap87 --runs 250000\n"
            "  d2re doctor\n"
            "  d2re gui"
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
    _add_passthrough_parser(subparsers, "tc", "Explore treasure class trees.")
    _add_passthrough_parser(subparsers, "drops", "Run the Monte Carlo drop calculator.")
    _add_passthrough_parser(subparsers, "doctor", "Run repository and environment self-checks.")
    _add_passthrough_parser(subparsers, "gui", "Launch the desktop GUI manager.")
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


def tc_main() -> int:
    return _dispatch("scripts.tc_explorer", sys.argv[1:], "tc_explorer.py")


def drops_main() -> int:
    return _dispatch("scripts.drop_calculator", sys.argv[1:], "drop_calculator.py")


def doctor_main() -> int:
    return _dispatch("d2re.doctor", sys.argv[1:], "d2re-doctor")


def gui_main() -> int:
    return _dispatch("d2re.gui", sys.argv[1:], "d2re-gui")
