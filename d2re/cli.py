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
        output = module.main()
        return output if isinstance(output, int) else 0
    finally:
        sys.argv = old_argv


def _add_passthrough(subparsers: argparse._SubParsersAction, name: str, help_text: str) -> None:
    parser = subparsers.add_parser(name, help=help_text, description=help_text)
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments forwarded to the underlying module.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="d2re",
        description="Unified CLI for the D2RE toolkit. Running `d2re` with no command opens the visual workbench.",
        epilog=(
            "Examples:\n"
            "  d2re --no-gui\n"
            "  d2re parse MyChar.d2s --json\n"
            "  d2re roll --seed 0xDEADBEEF --ilvl 85 --mf 300\n"
            "  d2re extract --all-mpqs 'C:/Diablo II/' --table weapons --csv\n"
            "  d2re tc --tc 'Act 5 Super C' --resolve --top 25\n"
            "  d2re drops --tc 'Mephisto (N)' --item weap87 --runs 250000\n"
            "  d2re doctor\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"d2re {__version__}")
    parser.add_argument("--no-gui", action="store_true", help="Do not auto-launch the GUI when no command is supplied.")

    subparsers = parser.add_subparsers(dest="command")
    _add_passthrough(subparsers, "parse", "Run the .d2s save parser.")
    _add_passthrough(subparsers, "roll", "Run the item generation simulator.")
    _add_passthrough(subparsers, "extract", "Run the MPQ / CASC extractor.")
    _add_passthrough(subparsers, "sniff", "Run the packet sniffer.")
    _add_passthrough(subparsers, "map", "Run the map seed analysis tool.")
    _add_passthrough(subparsers, "tc", "Explore treasure class trees.")
    _add_passthrough(subparsers, "drops", "Run the Monte Carlo drop calculator.")
    _add_passthrough(subparsers, "doctor", "Run repository and environment self-checks.")
    _add_passthrough(subparsers, "gui", "Generate and optionally open the local visual workbench.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    parser = build_parser()
    ns = parser.parse_args(args)
    if not ns.command:
        if ns.no_gui:
            parser.print_help()
            return 0
        return _dispatch("d2re.gui", [], "d2re-gui")
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


def doctor_main() -> int:
    return _dispatch("d2re.doctor", sys.argv[1:], "d2re-doctor")


def gui_main() -> int:
    return _dispatch("d2re.gui", sys.argv[1:], "d2re-gui")
