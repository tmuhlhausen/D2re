# Changelog

All notable changes to D2RE are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

- Add the first local Visual Workbench GUI through `d2re gui` and `d2re-gui`.
- Add `d2re/gui.py` with standalone HTML generation for a read-only browser workbench.
- Add `docs/gui-workbench.md` describing launch commands, design decisions, accessibility, safety, and next steps.
- Add GUI smoke tests in `tests/test_gui_workbench.py`.

### Changed

- Activate `d2re gui` while keeping `d2re doctor` disabled.
- Keep `item_roller --brute` and `--target` registered but disabled until bounded brute-force search is implemented.

### Cleanup in progress

- Deactivate unfinished command surfaces without removing them:
  - `d2re doctor`
  - `item_roller --brute`
  - `item_roller --target`
- Rewrite `docs/getting-started.md` as a short onboarding guide instead of a README duplicate.
- Mark placeholder guides as drafts until their worked examples are implemented.
- Add a phased cleanup checklist under `docs/maintenance/cleanup-checklist.md`.
- Add smoke tests for temporarily disabled command surfaces.
- Make the Visual Workbench the default `d2re` startup surface when no subcommand is supplied.
- Add `--no-gui` to preserve terminal-first help behavior.
- Add `d2re/gui_integrated.py` with a loopback-only interactive workbench server.
- Add `d2re/gui_beautified.py` with the enhanced Runic Workbench shell.
- Add integrated GUI command builders and guarded run actions for:
  - save parsing
  - item rolling
  - treasure-class exploration
  - drop simulation
  - map seed analysis
  - packet demo/list/filter workflows
  - MPQ/CASC data extraction
- Add per-session token validation for GUI `/api/run` requests.
- Add static mode through `d2re gui --static` for read-only command building and documentation use.
- Add Runic Workbench UI enhancements:
  - Blood, Ember, and Spectral themes
  - comfortable and compact density modes
  - favorites and favorites filtering
  - `Ctrl+K` / `Cmd+K` command palette
  - preset workflows for packet demo, TC scanning, drop simulation, map seed checks, and table extraction
  - browser-local run history
  - output copy, clear, and Pretty JSON controls
  - rune-style module markers and animated ambient background treatment
- Expand GUI smoke tests for default launch, command building, guarded subprocess execution, token rejection, and beautified UI markers.

### Changed

- `d2re gui` now starts the interactive local workbench server by default instead of only writing static HTML.
- `d2re/gui.py` now preserves the core GUI API while routing the rendered UI and CLI entrypoint through the beautified shell.
- Update `docs/gui-workbench.md` to describe default startup, interactive mode, static mode, safety boundaries, Runic Workbench enhancements, and implementation details.
- Keep `d2re doctor` disabled until diagnostic checks are implemented.
- Keep `item_roller --brute` and `--target` registered but disabled until bounded brute-force search is implemented.

### Planned next

- Add schema-aware result viewers that can render parser, TC, and drop JSON inside the GUI.
- Add workflow-specific result cards such as drop-rate confidence intervals and TC recursion maps.
- Add more workflow presets for farming, save analysis, packet study, and data extraction.
- Implement `d2re doctor` as an environment and repository self-check command.
- Add result-viewer panels that can consume stable JSON outputs.
- Implement bounded brute-force seed search for `item_roller --brute`.

---

## [1.1.0] — 2026-04-18

This section reflects the package version currently declared in `pyproject.toml` and `d2re/__init__.py`.

### Added

- Installable package metadata in `pyproject.toml`.
- Unified CLI entry point through `d2re/cli.py`.
- Console entry points for core workflows:
  - `d2re`
  - `d2re-parse`
  - `d2re-roll`
  - `d2re-extract`
  - `d2re-sniff`
  - `d2re-map`
- Treasure Class exploration workflow through `scripts/tc_explorer.py` and `d2re tc`.
- Monte Carlo drop calculator workflow through `scripts/drop_calculator.py` and `d2re drops`.
- Architecture and testing strategy documentation under `docs/architecture/`.
- Expansion and usability roadmap in `ROADMAP.md`.
- Implementation modules under `tools/` for wrapper-backed script entry points.

### Known limitations

- `d2re doctor` is a reserved command surface but is not implemented yet.
- `item_roller --brute` and `--target` are reserved flags but are not implemented yet.
- Some long-form guides remain drafts and need worked examples.

---

## [1.0.0] — Initial public release

### Added — Scripts

- **`scripts/packet_sniffer.py`** — Full D2 packet capture and annotator.
  - Live capture via Scapy on ports 4000 and 6112.
  - Decodes known C2S and S2C packet types with field-level definitions.
  - Rich plain-English explanations for packets: what triggers them, what each field means, and what the server/client does with them.
  - `GameStateTracker` for contextual annotations: active skill names, HP drop warnings, latency estimates, suspicious pattern detection.
  - Field enrichment: unit types, skill IDs, stat IDs, waypoint names, state IDs, and mode names decoded to human-readable strings.
  - Color-coded output by packet category.
  - `--demo` mode using hardcoded sample packets.
  - `--generate-structs` for C struct definitions.
  - `--list` for known packets, command bytes, and categories.
  - Session summary on Ctrl+C.
  - JSON output for offline analysis.

- **`scripts/d2s_parser.py`** — `.d2s` save file parser.
  - Parses header, quests, waypoints, NPC flags, stats, skills, items, corpse items, and mercenary items.
  - Item bit-stream decoder for quality, affixes, ethereal flags, socketed sub-items, personalized names, and ear data.
  - Checksum verification.
  - JSON output mode.
  - `BitReader` class for LSB-first variable-width bit fields.

- **`scripts/mpq_extract.py`** — MPQ archive extractor and data table parser.
  - Extracts data tables to CSV or JSON.
  - `.tbl` string table parser.
  - Treasure Class tree builder for drop simulation.
  - D2R CASC extraction support when optional dependencies are installed.
  - Multi-MPQ load order handling.

- **`scripts/item_roller.py`** — Item generation pipeline simulator.
  - D2-style LCG PRNG helper.
  - Quality determination with Magic Find diminishing returns by quality tier.
  - Magic affix rolling with item-level filtering.
  - Treasure Class drop Monte Carlo simulation.
  - Item-level formulas for monsters, gambling, and crafting.

- **`scripts/map_seed_tool.py`** — Map seed analyzer and BSP predictor.
  - Reads map seed from `.d2s` save files.
  - Derives per-act and per-level seeds.
  - BSP room layout prediction.
  - ASCII map rendering.
  - Entrance/exit room heuristics.
  - Seed brute-forcing hooks.
  - Level ID reference.

### Added — References

- `references/function-offsets.md`
- `references/packets.md`
- `references/stat-ids.md`
- `references/combat-formulas.md`
- `references/item-generation.md`
- `references/drlg-map-gen.md`
- `references/ai-states.md`
- `references/skill-system.md`
- `references/d2s-format.md`
- `references/dcc-dc6-format.md`
- `references/ghidra-scripts.md`
- `references/d2r-resurrected.md`

### Added — Core documentation

- `SKILL.md`
- `README.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `requirements.txt`

---

## Future roadmap

Future work is tracked in `ROADMAP.md` and `docs/maintenance/cleanup-checklist.md` rather than as faux release sections in this changelog.
