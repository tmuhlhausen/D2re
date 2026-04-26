"""Filesystem and environment path helpers for D2RE."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Iterable, List

INSTALL_ENV_KEYS = ("D2_HOME", "D2R_HOME", "DIABLO2_HOME", "DIABLO2R_HOME")
SAVE_ENV_KEYS = ("D2_SAVE_DIR", "D2R_SAVE_DIR", "DIABLO2_SAVE_DIR")


def _existing_unique(paths: Iterable[Path]) -> List[Path]:
    out: List[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = str(path.expanduser())
        if resolved in seen:
            continue
        seen.add(resolved)
        if Path(resolved).exists():
            out.append(Path(resolved))
    return out


def get_project_root() -> Path:
    """Return the repository root for an editable or source checkout."""
    return Path(__file__).resolve().parents[2]


def candidate_install_paths() -> List[Path]:
    candidates: List[Path] = []
    for key in INSTALL_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            candidates.append(Path(value))

    home = Path.home()
    system = platform.system().lower()

    if system == "windows":
        pf = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        pfx86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        candidates += [
            pf / "Diablo II",
            pfx86 / "Diablo II",
            pf / "Diablo II Resurrected",
            pfx86 / "Diablo II Resurrected",
            home / "Games" / "Diablo II",
            home / "Games" / "Diablo II Resurrected",
        ]
    elif system == "darwin":
        candidates += [
            Path("/Applications/Diablo II"),
            Path("/Applications/Diablo II Resurrected"),
            home / "Applications" / "Diablo II",
            home / "Applications" / "Diablo II Resurrected",
        ]
    else:
        candidates += [
            home / "Games" / "Diablo II",
            home / "Games" / "Diablo II Resurrected",
            home / ".steam" / "steam" / "steamapps" / "common" / "Diablo II Resurrected",
            home / ".local" / "share" / "Steam" / "steamapps" / "common" / "Diablo II Resurrected",
            Path("/opt/Diablo II"),
            Path("/opt/Diablo II Resurrected"),
        ]
    return candidates


def detect_install_paths() -> List[Path]:
    """Return detected Diablo II / D2R install paths."""
    return _existing_unique(candidate_install_paths())


def candidate_save_paths() -> List[Path]:
    candidates: List[Path] = []
    for key in SAVE_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            candidates.append(Path(value))

    home = Path.home()
    system = platform.system().lower()

    if system == "windows":
        saved_games = home / "Saved Games"
        documents = home / "Documents"
        candidates += [
            saved_games / "Diablo II",
            saved_games / "Diablo II Resurrected",
            documents / "Diablo II",
            documents / "Diablo II Resurrected",
        ]
    elif system == "darwin":
        candidates += [
            home / "Library" / "Application Support" / "Diablo II",
            home / "Library" / "Application Support" / "Diablo II Resurrected",
            home / "Documents" / "Diablo II",
            home / "Documents" / "Diablo II Resurrected",
        ]
    else:
        candidates += [
            home / ".local" / "share" / "Diablo II",
            home / ".local" / "share" / "Diablo II Resurrected",
            home / "Saved Games" / "Diablo II",
            home / "Saved Games" / "Diablo II Resurrected",
        ]
    return candidates


def detect_save_paths() -> List[Path]:
    """Return detected Diablo II / D2R save paths."""
    return _existing_unique(candidate_save_paths())
