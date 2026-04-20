#!/usr/bin/env python3
"""Compatibility wrapper for the enhanced D2RE GUI workbench."""

from __future__ import annotations

from .gui_beautified import *  # noqa: F401,F403
from .gui_beautified import main


if __name__ == "__main__":
    raise SystemExit(main())
