#!/usr/bin/env python3
"""Repository and environment self-checks for D2RE."""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from d2re.core.paths import detect_install_paths, detect_save_paths, get_project_root


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    hint: str = ""


def result(name: str, status: str, detail: str, hint: str = "") -> CheckResult:
    return CheckResult(name, status, detail, hint)


def check_files(project_root: Path) -> List[CheckResult]:
    required = [
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "pyproject.toml",
        "scripts/d2s_parser.py",
        "scripts/item_roller.py",
        "scripts/mpq_extract.py",
        "scripts/packet_sniffer.py",
        "scripts/map_seed_tool.py",
        "scripts/tc_explorer.py",
        "scripts/drop_calculator.py",
        "d2re/cli.py",
        "d2re/core/paths.py",
    ]
    optional = [
        "docs/hooking-guide.md",
        "docs/emulator-server-guide.md",
        "docs/tools/doctor.md",
        "examples/find_best_seed.py",
        "data_tables/tc_tree.json",
    ]
    out: List[CheckResult] = []
    for rel in required:
        if (project_root / rel).exists():
            out.append(result(f"file:{rel}", "ok", "present"))
        else:
            out.append(result(f"file:{rel}", "error", "missing", "Restore the documented repo layout."))
    for rel in optional:
        if (project_root / rel).exists():
            out.append(result(f"optional:{rel}", "ok", "present"))
        else:
            out.append(result(f"optional:{rel}", "warn", "missing", "Some workflows may be limited."))
    return out


def check_imports() -> List[CheckResult]:
    modules = [
        "scripts.d2s_parser",
        "scripts.item_roller",
        "scripts.mpq_extract",
        "scripts.packet_sniffer",
        "scripts.map_seed_tool",
        "scripts.tc_explorer",
        "scripts.drop_calculator",
        "d2re.cli",
        "d2re.core.paths",
    ]
    out: List[CheckResult] = []
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            if module_name.startswith("scripts.") and not hasattr(module, "main"):
                out.append(result(f"import:{module_name}", "warn", "imported but no main()", "Keep CLI modules stable."))
            else:
                out.append(result(f"import:{module_name}", "ok", "imported"))
        except Exception as exc:
            out.append(result(f"import:{module_name}", "error", str(exc), "Run from repo root or install editable package."))
    return out


def check_dependencies() -> List[CheckResult]:
    out: List[CheckResult] = []
    for module_name in ("scapy", "colorama", "mpyq"):
        try:
            importlib.import_module(module_name)
            out.append(result(f"dependency:{module_name}", "ok", "installed"))
        except Exception:
            out.append(result(f"dependency:{module_name}", "warn", "not installed", f"pip install {module_name}"))
    return out


def check_paths() -> List[CheckResult]:
    installs = detect_install_paths()
    saves = detect_save_paths()
    return [
        result("env:install-paths", "ok" if installs else "warn", ", ".join(map(str, installs)) or "none detected", "Set D2_HOME or D2R_HOME."),
        result("env:save-paths", "ok" if saves else "warn", ", ".join(map(str, saves)) or "none detected", "Set D2_SAVE_DIR if needed."),
    ]


def run_checks(project_root: Optional[Path] = None) -> List[CheckResult]:
    root = project_root or get_project_root()
    checks: List[CheckResult] = []
    checks.extend(check_files(root))
    checks.extend(check_imports())
    checks.extend(check_dependencies())
    checks.extend(check_paths())
    return checks


def summarize(checks: Iterable[CheckResult]) -> tuple[int, int, int]:
    ok = warn = error = 0
    for check in checks:
        if check.status == "ok":
            ok += 1
        elif check.status == "warn":
            warn += 1
        else:
            error += 1
    return ok, warn, error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run repository and environment self-checks for D2RE.",
        epilog="Examples:\n  d2re doctor\n  d2re doctor --json\n  d2re doctor --strict",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors.")
    parser.add_argument("--project-root", type=Path, help="Override the repository root for file checks.")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    project_root = args.project_root or get_project_root()
    checks = run_checks(project_root)
    ok, warn, error = summarize(checks)

    if args.json:
        print(json.dumps({"project_root": str(project_root), "summary": {"ok": ok, "warn": warn, "error": error}, "results": [asdict(c) for c in checks]}, indent=2))
    else:
        for check in checks:
            label = {"ok": "OK", "warn": "WARN", "error": "ERR"}[check.status]
            print(f"[{label}] {check.name}: {check.detail}")
            if check.hint:
                print(f"       hint: {check.hint}")
        print(f"\nSummary: {ok} ok, {warn} warnings, {error} errors")

    if error:
        return 2
    if args.strict and warn:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
