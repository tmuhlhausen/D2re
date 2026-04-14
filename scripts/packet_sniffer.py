#!/usr/bin/env python3
"""Wrapper for the packet sniffer implementation.
Adds a compatibility shim for PacketDef.notes so demo mode works.
"""

from tools.packet_sniffer_impl import *  # noqa: F401,F403

if not hasattr(PacketDef, "notes"):
    PacketDef.notes = ""

if __name__ == "__main__":
    main()
