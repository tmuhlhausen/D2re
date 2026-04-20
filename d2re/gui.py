#!/usr/bin/env python3
"""Compatibility wrapper for the enhanced D2RE GUI workbench."""

from __future__ import annotations

from .gui_integrated import *  # noqa: F401,F403
from .gui_beautified import build_parser, main, render_workbench, serve_workbench, write_workbench


if __name__ == "__main__":
    raise SystemExit(main())
