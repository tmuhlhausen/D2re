# D2RE — Expansion & Usability Roadmap

> A phased plan for growing the D2RE toolkit's script coverage and raising the
> day-to-day quality-of-life for everyone who uses it: modders, bot authors,
> emulator devs, researchers, and tool builders.

This roadmap is intentionally conservative on scope creep. Every new script
must justify itself against three questions:

1. **Does it fill a real gap** that users currently solve with ad-hoc code?
2. **Does it reuse the shared core** (parsers, data tables, RNG) instead of
   duplicating logic?
3. **Does it ship with the QoL baseline** (see §0) on day one?

Status legend: `[ ]` planned · `[~]` in progress · `[x]` shipped

---

## Table of Contents

- [§0 — The QoL Baseline (applies to every script)](#0--the-qol-baseline-applies-to-every-script)
- [§1 — Phase 1: Foundations & Cleanup](#1--phase-1-foundations--cleanup)
- [§2 — Phase 2: Core Script Expansion](#2--phase-2-core-script-expansion)
- [§3 — Phase 3: Interactive & Integrated Workflows](#3--phase-3-interactive--integrated-workflows)
- [§4 — Phase 4: Advanced Tooling & Research](#4--phase-4-advanced-tooling--research)
- [§5 — Phase 5: Ecosystem & Community](#5--phase-5-ecosystem--community)
- [§6 — Cross-Cutting Concerns](#6--cross-cutting-concerns)
- [§7 — Success Metrics](#7--success-metrics)

---

## §0 — The QoL Baseline (applies to every script)

Before adding any new tool, the toolkit needs a shared definition of what
"usable" means. Every script — existing and new — must conform to this
baseline. Think of it as the contract the user gets for free.

### 0.1 — Consistent CLI surface

- [ ] Unified argparse wrapper in `d2re/cli.py` providing:
  - `--version`, `--help`, `--quiet`, `--verbose`, `--debug`
  - `--json` / `--yaml` / `--csv` output format flags (where applicable)
  - `--no-color` and automatic TTY detection (don't emit ANSI to pipes)
  - `--config <path>` to load persistent defaults from `~/.d2re/config.toml`
  - Consistent exit codes: `0` ok, `1` user error, `2` input error, `3` runtime
- [ ] Every script responds to `-h` with **examples**, not just flag lists.
- [ ] Every script supports `--dry-run` where it mutates anything on disk.

### 0.2 — Sensible defaults

- [ ] Auto-detect Diablo II install paths on Windows/macOS/Linux (registry,
  common Steam/Blizzard paths, `$D2_HOME`).
- [ ] Auto-detect the D2 Saved Games folder for `.d2s` tools.
- [ ] Cache expensive derivations (TC trees, string tables) in
  `~/.cache/d2re/` with content-hash keys so re-runs are instant.
- [ ] Respect `NO_COLOR`, `CLICOLOR`, and `XDG_*` environment variables.

### 0.3 — Good errors

- [ ] Replace `raise Exception(...)` with a small hierarchy:
  `D2REError`, `InputError`, `ParseError`, `ChecksumError`, `NotFoundError`.
- [ ] Every error prints: *what failed*, *why*, *the likely fix*, and
  *a link to the relevant reference doc*.
- [ ] Graceful degradation when optional deps (`scapy`, `mpyq`, `colorama`)
  are missing — tell the user exactly which `pip install` fixes it.

### 0.4 — Progress & feedback

- [ ] Long-running operations show a progress bar (`tqdm`, optional dep,
  falls back to percent prints).
- [ ] `--quiet` mode is truly silent except for errors.
- [ ] Structured log output via `logging` with `--log-file` support.

### 0.5 — Machine-friendly output

- [ ] Every tool that prints a report can also emit structured JSON with the
  same information — no "pretty only" outputs.
- [ ] JSON schemas published under `schemas/` so downstream consumers can
  validate.
- [ ] Stable field names across versions (deprecate, don't rename silently).

### 0.6 — Safety rails

- [ ] **Never** overwrite a `.d2s` file without `--force` or an explicit
  `--backup` that writes `MyChar.d2s.bak.<timestamp>` first.
- [ ] Read-only by default everywhere; mutation requires an explicit verb
  (`edit`, `patch`, `write`).
- [ ] Refuse to run packet capture or memory reads without acknowledging the
  legal/TOS warning on first use (cached in config).

### 0.7 — Documentation parity

- [ ] Every script has a matching `docs/tools/<name>.md` page with: overview,
  every flag, three worked examples, troubleshooting, and links to relevant
  `references/*.md`.
- [ ] `README.md` tool table stays in sync via a CI check.

---

## §1 — Phase 1: Foundations & Cleanup

*Goal: make the repo a pleasant place to add new tools. No new features until
 the foundations are solid.*

### 1.1 — Package the toolkit

- [ ] Convert `scripts/` into an installable package `d2re/` with
  `pyproject.toml`, entry points (`d2re-parse`, `d2re-sniff`, `d2re-roll`,
  `d2re-map`, `d2re-mpq`), and `pip install -e .` dev workflow.
- [ ] Keep the old `python scripts/foo.py` invocation working via thin
  forwarders so existing docs and muscle memory don't break.

### 1.2 — Extract the shared core

Today each script carries its own copy of the LCG, bit reader, stat-id map,
and level-id tables. Consolidate into:

- [ ] `d2re/core/rng.py` — LCG, seed cascade, range rolls.
- [ ] `d2re/core/bitstream.py` — the bit reader used by `d2s_parser` and
  `item_roller`, with tests that pin every bit offset.
- [ ] `d2re/core/tables.py` — lazy loader for extracted `.txt` data tables
  with memoization and schema validation.
- [ ] `d2re/core/ids.py` — single source of truth for level IDs, stat IDs,
  skill IDs, item codes.
- [ ] `d2re/core/paths.py` — install detection + save-folder detection.

### 1.3 — Testing infrastructure

- [ ] `pytest` suite with:
  - Golden `.d2s` fixtures (tiny, synthetic, MIT-licensed characters).
  - Golden packet captures for the sniffer decoder.
  - Property tests for the LCG (idempotence, cascade invariants).
  - Round-trip tests: parse → re-serialize → parse, must match byte-exact
    once the writer lands (§2.1).
- [ ] GitHub Actions: lint (ruff), type check (mypy), test matrix
  (Py 3.8/3.10/3.12 × Linux/macOS/Windows).
- [ ] Coverage gate at 80% on `d2re/core/**`.

### 1.4 — Fix what's already shipped

- [ ] Audit existing scripts for the QoL baseline in §0 and bring each up to
  spec before any new scripts land.
- [ ] `packet_sniffer.py`: add `--pcapng` support and timestamps in ISO-8601.
- [ ] `d2s_parser.py`: surface the full quest/waypoint bitmaps, not just
  stats+items.
- [ ] `map_seed_tool.py`: cache BSP expansions per `(seed, act)` pair.
- [ ] `mpq_extract.py`: parallel extraction with `--jobs N`.
- [ ] `item_roller.py`: vectorize the Monte Carlo loop — a 1M-drop simulation
  should finish in seconds, not minutes.

---

## §2 — Phase 2: Core Script Expansion

*Goal: round out the "obvious missing tools" that almost every user ends up
 writing themselves.*

### 2.1 — `d2s_editor.py` — safe, scoped save-file writer

The parser is read-only today. A **careful** writer unlocks a huge class of
workflows: fixing corrupted saves, building test fixtures, migrating offline
characters to single-player for research.

- [ ] Editable fields behind explicit `--set` verbs:
  `stats.strength`, `stats.gold`, `waypoints.act2`, `quests.act1.cain`.
- [ ] Item mutation (add/remove/swap) using the parsed item tree, never raw
  bytes.
- [ ] Automatic checksum recomputation.
- [ ] **Required** `--backup` unless `--no-backup` is explicitly passed.
- [ ] `--diff old.d2s new.d2s` that shows human-readable field-level diffs.

### 2.2 — `tc_explorer.py` — treasure class walker

- [ ] Interactive TC tree walk: pick a monster → see the full resolved TC
  chain and every terminal item with its probability.
- [ ] Reverse lookup: "which monsters in act 5 hell can drop Shako?"
- [ ] CSV export of the full monster × item probability matrix.
- [ ] Respects `--mf` and `--players` parameters.

### 2.3 — `skill_calc.py` — skill & synergy calculator

- [ ] Given a class + skill + point allocation + gear, compute actual damage,
  mana cost, cooldown, and synergy contributions per level.
- [ ] Build-planner mode: `--plan Blizzard:20,GlacialSpike:20,ColdMastery:20`.
- [ ] Export the resulting curve to CSV/plot.

### 2.4 — `rune_word_finder.py`

- [ ] Given a parsed `.d2s` and the `runes.txt` table, list every runeword
  the character can currently assemble and what's missing for others.
- [ ] Scan shared stash (`.d2i`) files too.
- [ ] `--goal Enigma` to compute the missing-rune shortlist.

### 2.5 — `map_render.py` — ASCII & SVG map rendering

- [ ] Take a seed + area and output:
  - ASCII art for quick terminal inspection.
  - SVG with waypoint, entrance, and boss-room markers.
  - Optional PNG via `pillow` (lazy dep).
- [ ] `--overlay` mode to superimpose multiple seeds for seed-hunting
  visualization.

### 2.6 — `drop_calculator.py`

- [ ] Thin wrapper around the Monte Carlo in `item_roller.py` that answers
  the questions users actually ask:
  - "How many Mephisto runs for a Stone of Jordan at 300 MF?"
  - "What's the fastest TC87 farm per hour across areas?"
- [ ] Confidence intervals, not just point estimates.

---

## §3 — Phase 3: Interactive & Integrated Workflows

*Goal: move from "run a script, read the output" to "sit down and explore".*

### 3.1 — `d2re shell` — REPL / interactive mode

- [ ] A single `d2re shell` command that drops into a Python REPL with the
  core module pre-imported and tab completion for level names, skill names,
  item codes.
- [ ] IPython integration when installed; plain `code.InteractiveConsole`
  fallback.
- [ ] Built-in helpers: `load("MyChar.d2s")`, `roll(seed, ilvl)`,
  `seed_info(0xABCD1234)`.

### 3.2 — TUI dashboard (`d2re tui`)

- [ ] `textual`-based dashboard that:
  - Watches a save folder and shows live character stats after each save.
  - Shows live sniffer output with filter panes.
  - Renders the current area's map preview.
- [ ] All panes toggleable; keyboard-driven; works over SSH.

### 3.3 — Web viewer (`d2re serve`)

- [ ] Local-only FastAPI server that serves an HTML viewer for:
  - Parsed save files with sortable item tables.
  - Map seed previews with pan/zoom.
  - Packet-capture timelines.
- [ ] Static export (`--export ./site/`) for sharing research artifacts.
- [ ] **Never** binds to a public interface by default.

### 3.4 — Watch mode

- [ ] `--watch` flag on `d2s_parser`, `map_seed_tool`, and others: re-run
  automatically when the input file changes. Great for "edit → reload → see"
  research loops.

### 3.5 — Shell completions

- [ ] Bash, Zsh, and Fish completions generated from argparse, installable
  via `d2re completions install`.
- [ ] Completes flags, level names, skill names, and file paths.

---

## §4 — Phase 4: Advanced Tooling & Research

*Goal: the "wish list" tools that currently require a deep-dive project.*

### 4.1 — `memory_scanner.py`

- [ ] Safe, read-only process memory inspector for the local D2 process on
  Windows/Linux/macOS (where permitted).
- [ ] Uses the `UnitAny` / `PlayerData` struct definitions from
  `references/` to dump the live player state.
- [ ] Strictly forbids writing memory — this is a research tool, not a
  trainer. Document the distinction loudly.
- [ ] Gated behind an explicit `--i-understand-this-is-research` flag.

### 4.2 — Ghidra bridge

- [ ] `d2re/ghidra/` package containing the Python scripts that currently
  live in the reference doc, plus:
  - Auto-labeller that consumes `references/function-offsets.md`.
  - Struct importer for `UnitAny` and friends.
  - Symbol exporter back to JSON for cross-tool use.
- [ ] `d2re ghidra export <project>` CLI wrapper.

### 4.3 — `packet_replay.py`

- [ ] Replay a captured `.pcap` / `.json` session against a local test
  server for emulator development.
- [ ] Timing modes: real-time, fast-forward, step-through.
- [ ] Diffs expected-vs-actual responses.

### 4.4 — `dc6_viewer.py` / `dcc_viewer.py`

- [ ] Sprite decoders with a CLI that dumps frames to PNG.
- [ ] Optional TUI preview using kitty/iterm inline image protocol.
- [ ] Batch `--extract-all` for a whole MPQ.

### 4.5 — Emulator scaffold generator

- [ ] `d2re scaffold emulator ./my-server/` creates a minimal Python
  D2GS-compatible server skeleton wired up to the packet library in `d2re`.
- [ ] Not a working server — a *starting point* so new emulator projects
  don't start from zero.

---

## §5 — Phase 5: Ecosystem & Community

*Goal: make it easy for other people to extend D2RE without forking it.*

### 5.1 — Plugin system

- [ ] `d2re` discovers plugins via entry points (`d2re.plugins`).
- [ ] A plugin can register new subcommands, new output formatters, or new
  parsers for custom mod formats.
- [ ] Template repo `d2re-plugin-template` with CI and tests pre-wired.

### 5.2 — Versioned data bundles

- [ ] Publish pre-extracted, canonical data-table bundles on GitHub Releases
  so users without a D2 install can still use `item_roller`, `tc_explorer`,
  and friends. **Only metadata tables, never copyrighted art or audio.**
- [ ] `d2re fetch tables --version 1.14d` downloads and verifies via hash.

### 5.3 — Contribution UX

- [ ] `CONTRIBUTING.md` with a 5-minute local-dev quickstart.
- [ ] `make dev` / `just dev` task runner wrapping install + lint + test.
- [ ] Issue templates for "bug in parser", "new script proposal",
  "documentation gap".
- [ ] `good-first-issue` label guide.

### 5.4 — Benchmarks & regression tracking

- [ ] `pytest-benchmark` suite run in CI; regressions flagged on PRs.
- [ ] Public dashboard of parse-speed / roll-speed trends.

---

## §6 — Cross-Cutting Concerns

### 6.1 — Performance budget

| Operation | Target |
|---|---|
| Parse a single `.d2s` | < 50 ms |
| Extract all tables from `d2data.mpq` | < 3 s |
| 1M-drop Monte Carlo simulation | < 2 s |
| Decode 10k packets from `.pcap` | < 1 s |
| Resolve a full act-1 BSP | < 200 ms |

### 6.2 — Compatibility matrix

- [ ] Maintain explicit support for D2 Classic `1.09d`, `1.12a`, `1.13c`,
  `1.14d`, and D2R `1.x`.
- [ ] Version-aware parsers: `--d2-version 1.13c` where behaviour differs.
- [ ] A single test fixture per version in CI.

### 6.3 — Security & legal posture

- [ ] Never ship game data. Ever.
- [ ] Packet capture and memory reading gated behind consent prompts that
  cite D2R's TOS.
- [ ] `SECURITY.md` with a clear "this toolkit refuses to help with cheating
  on official servers" statement.
- [ ] Dependabot + `pip-audit` in CI.

### 6.4 — Accessibility

- [ ] All output works with screen readers (no reliance on color alone).
- [ ] High-contrast mode for the TUI.
- [ ] Every table is also printable as plain text (no box-drawing required).

### 6.5 — Internationalization

- [ ] String table extraction already exists; add a `--locale` flag to
  parsers so item/skill names print in the user's language when the
  `.tbl` files are available.

---

## §7 — Success Metrics

How we know the roadmap is working:

- **Usability:** a first-time user can go from `git clone` to a rendered
  character sheet in **under two minutes** without reading docs.
- **Expansion:** every new script lands with tests, docs, and a JSON mode on
  day one. No exceptions.
- **QoL:** the issue tracker's "friction" label (bad errors, surprising
  defaults, missing flags) trends toward zero.
- **Reuse:** no more than one implementation of the LCG, bit reader, or stat
  table in the whole repo.
- **Community:** at least one third-party plugin exists by the end of
  Phase 5.

---

## Out of scope (deliberately)

To keep the project focused, the following are **not** on the roadmap:

- A working D2 server implementation (scaffold only — §4.5).
- A character trainer, map hack, or memory writer.
- Anything that ships Blizzard-copyrighted assets.
- A GUI save editor aimed at casual players — D2RE stays a research toolkit.
- Mobile or console support.

If you want one of these, fork — the plugin system (§5.1) is designed so
you don't have to.

---

*This roadmap is a living document. Open an issue or PR to propose changes.*
