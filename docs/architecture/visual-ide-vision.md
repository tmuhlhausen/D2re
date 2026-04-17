# D2RE Visual IDE Vision

> Foundation document for the next major evolution of D2RE: from a script-first
> reverse-engineering toolkit into a layered exploration environment for Diablo II
> internals, research, planning, simulation, and safe offline analysis.

---

## 1. Why this exists

D2RE already has the bones of a powerful toolkit: parsers, simulators,
extractors, packet documentation, and research-grade reference material.
What it does not yet have is a **single exploration surface** that lets a
user move naturally between:

- static reference data,
- save-file analysis,
- map and RNG exploration,
- packet and protocol inspection,
- item and skill simulation,
- modding-oriented table browsing,
- and future reverse-engineering helpers.

The Visual IDE initiative turns D2RE into an environment where a user can
*inspect, compare, simulate, annotate, and navigate* Diablo II systems without
jumping between disconnected scripts and ad-hoc notes.

This is not a replacement for the CLI. It is a higher-level orchestration
layer built on top of the CLI and shared core.

---

## 2. Product intent

The D2RE Visual IDE should feel like a cross between:

- a reverse-engineering workbench,
- a data exploration studio,
- a build/theorycraft planner,
- and a documentation browser.

It should support three modes of work:

### 2.1 Research mode

A user starts with a question such as:

- Why did this item roll the way it did?
- What exact stat IDs are present on this save-file item?
- Which packet sequence fires when the client opens a vendor?
- How does a specific map seed branch into room generation?

The IDE should let the user pivot from question to system, system to data,
and data to reference docs without context loss.

### 2.2 Builder mode

A user wants to construct something:

- a build plan,
- a treasure-class analysis,
- a drop simulation,
- a save-file fixture for tests,
- a modding workflow,
- or a reference bundle for emulator work.

The IDE should expose guided workflows with safe defaults and exportable output.

### 2.3 Audit mode

A user wants to validate and compare:

- save file A vs save file B,
- map seed X vs seed Y,
- one item roll against another,
- one patch's tables against another,
- or decoded packet streams against expected protocol behavior.

The IDE should provide structured diffs and explainable changes, not just raw bytes.

---

## 3. Non-goals

To keep the project sharp and ethically grounded, the Visual IDE must not become:

- a cheating client for official servers,
- a memory writer or trainer,
- a copyrighted-asset distribution vehicle,
- or a casual game launcher.

The IDE is a **research, documentation, simulation, and offline analysis tool**.

---

## 4. Architectural shape

The IDE should be introduced in layers so the repository remains stable and
maintainable.

### 4.1 Layer 1: shared core

Existing and future logic should converge into reusable packages under `d2re/`:

- `d2re.core`
- `d2re.parsers`
- `d2re.protocol`
- `d2re.sim`
- `d2re.maps`
- `d2re.docs`
- `d2re.ui_contracts`

This layer owns deterministic logic, schemas, identifiers, table loaders,
validators, and formatters.

### 4.2 Layer 2: workflow services

These are orchestration modules that combine several core systems into one
user-facing operation:

- save inspection service
- item explanation service
- map preview service
- packet timeline service
- reference cross-link service
- diff service
- export service

This layer should remain headless so it can serve CLI, TUI, web, and future
Devvit integrations.

### 4.3 Layer 3: experience shells

Multiple shells should be possible without forking the business logic:

- CLI for automation and scripting
- TUI for terminal-first investigation
- local web UI for the full Visual IDE
- future Reddit/Devvit surfaces for curated exploration experiences

---

## 5. Core panels in the first web IDE milestone

The first serious IDE milestone should focus on a modular panel system.
Each panel should be independently dockable, collapsible, and deep-linkable.

### 5.1 Navigator panel

Purpose:
- global search across docs, item codes, skill IDs, stat IDs, packets, levels,
  and tools.

Primary interactions:
- fuzzy search
- recent entities
- pinned investigations
- breadcrumbs

### 5.2 Reference panel

Purpose:
- read canonical docs and structured reference tables without leaving the current context.

Primary interactions:
- rich links between references
- inline glossary hovers
- anchorable sections
- compare-reference mode

### 5.3 Save inspector panel

Purpose:
- inspect `.d2s` data as character sheet, item tree, quests, waypoints,
  mercenary state, corpse inventory, and derived stats.

Primary interactions:
- load save file
- validate checksum
- filter inventory
- decode affixes
- compare two saves

### 5.4 Item lab panel

Purpose:
- explain item generation and affixes in plain language backed by deterministic logic.

Primary interactions:
- seed + ilvl simulations
- affix eligibility explorer
- runeword viability checks
- unique/set downgrade explanation
- ethereal/socket roll explanation

### 5.5 Map lab panel

Purpose:
- inspect map seeds, area layouts, room graphs, and seed cascades.

Primary interactions:
- seed entry or import from save
- area selection
- graph and tile preview
- room metadata
- compare seeds

### 5.6 Packet panel

Purpose:
- decode live or recorded packet streams into a searchable timeline.

Primary interactions:
- open pcap/json
- filter by direction / packet id / category
- inspect field-level decode
- highlight unknown fields
- export protocol notes

### 5.7 Planner panel

Purpose:
- connect skills, items, breakpoints, rune goals, and farming plans into one place.

Primary interactions:
- skill planning
- rune gap analysis
- drop target calculation
- route notes
- export/share plan bundles

### 5.8 Diff panel

Purpose:
- compare two structured artifacts.

Targets:
- save vs save
- table vs table
- seed vs seed
- packet trace vs packet trace
- generated item vs generated item

---

## 6. Interaction model

The most important UX rule is: **a user should never hit a dead end**.

Every result page or panel should provide next-hop actions, such as:

- open source table
- inspect linked stat
- view related packet
- compare with another artifact
- simulate from this state
- export as JSON
- pin to workspace

That turns D2RE from a toolbox into an actual investigation environment.

---

## 7. Data contracts the IDE needs

The IDE depends on stable machine-readable outputs. Every user-facing workflow
should be backed by a schema-first contract.

Initial required schema families:

- `save.character.v1`
- `save.item.v1`
- `item.roll.v1`
- `map.seed-analysis.v1`
- `packet.decode.v1`
- `reference.entity.v1`
- `diff.report.v1`
- `planner.build.v1`

Design rules:

- version every schema explicitly,
- prefer additive evolution,
- avoid silent field renames,
- and publish examples beside the schemas.

---

## 8. First implementation slice

The first implementation wave should favor leverage over spectacle.

### 8.1 Must ship early

- testing foundation
- CI pipeline
- developer docs
- architecture docs
- stable CLI contract tests
- schema directory and initial conventions

### 8.2 Next after foundation

- TUI or local web prototype for a small set of panels
- save inspector JSON schema
- packet decode JSON schema
- diff report schema
- panel routing and layout primitives

### 8.3 Only after that

- advanced graph exploration
- collaborative notes
- plugin marketplace concepts
- Devvit-specific presentation layers

---

## 9. Success criteria

The Visual IDE initiative is succeeding when:

- a new contributor can understand the architecture in one sitting,
- a researcher can answer a question without juggling five separate tools,
- test fixtures can be created and validated safely,
- machine-readable exports become the default rather than an afterthought,
- and every new capability fits the existing system instead of growing wild branches.

---

## 10. Immediate repo implications

This document implies the following concrete repository work:

1. strengthen testing and CI
2. formalize architecture docs
3. publish schema conventions
4. add security / legal guardrails
5. grow a reliable developer workflow
6. evolve D2RE toward service-style modules beneath the CLI

Those steps begin in this branch.
