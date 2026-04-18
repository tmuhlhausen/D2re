# Emulator / Server Guide

> **Status: Draft placeholder.** This page is intentionally not presented as a complete emulator implementation guide yet.

This guide currently links together the references needed for server-emulation research while the full workflow is built in phases.

## Current scope

Use this page as an index for:

- packet references
- combat and simulation rules
- item generation notes
- map generation notes
- future emulator scaffold planning

## Start here

- `references/packets.md` for packet definitions
- `references/combat-formulas.md` for simulation rules
- `references/item-generation.md` for drop logic
- `references/drlg-map-gen.md` for map generation behavior

## Not complete yet

The following sections still need full implementation:

- minimal D2GS-compatible server architecture
- connection handshake walkthrough
- packet routing and validation examples
- local-only test harness
- packet replay workflow
- expected-vs-actual response diffing
- legal and safety boundaries for emulator research

Until those sections are written, treat this page as a signpost rather than a final guide.
