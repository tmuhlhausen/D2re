# D2RE Visual IDE Specification

## Objective

This document defines the first serious UI architecture for the future D2RE
visual IDE. The target is a workspace that visually echoes Diablo IV while
remaining readable, fast, and practical for technical investigation.

This is not a theme-only exercise. The aesthetic exists to support a specific
kind of focus: deep inspection, contextual navigation, and rapid movement
between raw data and interpreted meaning.

## Design Language

### Visual tone

The UI should borrow from Diablo IV's presentation language:

- dark stone, iron, ash, charcoal, and desaturated leather tones
- restrained blood-red accents for active, dangerous, or high-priority states
- gilded or steel framing for major panels
- parchment or carved-slate surfaces for readable information zones
- ambient animated backgrounds used sparingly and only behind low-information
  regions
- rune-like iconography for categories such as items, skills, structures,
  packets, maps, and experiments

### Non-negotiable usability rules

The UI must not become cosplay for clarity. Therefore:

- body text must remain high contrast and calm
- ornamental textures cannot reduce legibility
- panel edges and controls must stay visually distinct
- motion must be slow, ambient, and optional
- important states must not rely on red alone

## Workspace Model

The IDE should use a modular panel system with a stable shell.

### Recommended shell layout

- **Top bar**: workspace title, active source, global search, quick actions,
  export menu, settings
- **Left rail**: section navigation with icons and labels
- **Explorer panel**: tree or graph navigation across domain objects
- **Main canvas**: primary panel area, tabs or split panes
- **Right inspector**: metadata, explanation, provenance, relationships,
  warnings, confidence state
- **Bottom drawer**: logs, traces, packet stream, test output, console, notes

## Primary Panels

### 1. Explorer

The explorer is the user's anchor. It should support both hierarchy and search.

Categories should include:

- Saves
- Packets
- Structures
- Offsets
- Items
- Skills
- Monsters
- Maps
- Tables
- Simulations
- Notes
- Sessions

Each node should expose badges such as:

- verified
- inferred
- draft
- experimental
- deprecated

### 2. Main analysis panel

This is the central working space. It should support multiple view types.

#### View types

- **Structured document view** for guides and references
- **Schema/table view** for extracted game data
- **Timeline view** for packets and state changes
- **Hex-plus-meaning view** for raw binary with interpreted overlays
- **Diff view** for comparing versions, saves, or generated outputs
- **Graph view** for relationships such as TC recursion and struct references
- **Map canvas** for seed analysis and layout predictions
- **Simulation results view** for Monte Carlo and deterministic pipelines

### 3. Context inspector

The right-hand inspector should explain the currently selected entity in layers.

Suggested sections:

- summary
- provenance
- field dictionary
- related entities
- caveats
- likely next actions

For example, if a user selects a stat inside an item record, the inspector
should show:

- human-readable name
- raw stat ID
- bit width or encoding rules
- source table linkage
- how it displays in-game
- relevant formulas or quirks

### 4. Bottom drawer

This should be a practical diagnostic zone, not clutter.

Modes:

- console output
- parser warnings
- test results
- packet log
- debug trace
- notes scratchpad

## Interaction Patterns

### Global search

Search should understand multiple entity types and allow direct jumps.

Useful queries:

- `unitany`
- `0x0c`
- `phase blade`
- `stat 6`
- `mephisto tc`
- `v1.13c hp update`
- `maggot lair level 3`

Search results should show type, short explanation, and confidence level.

### Cross-linking

Every major view should support jump actions.

Examples:

- packet to structure
- structure field to documentation
- item stat to source table
- map seed to generated rooms
- save value to underlying bit offset
- simulation result to governing formulas

### Multi-select comparisons

Comparisons should be a first-class workflow, not an afterthought.

Users should be able to compare:

- two saves
- two patch versions
- two packet traces
- two treasure classes
- classic D2 vs D2R records

## Accessibility and comfort

Even a dark fantasy interface must behave like professional software.

Requirements:

- full keyboard navigation for panel switching and search
- readable focus states
- reduced motion mode
- high-contrast mode
- icon plus text labeling in primary navigation
- scalable typography

## Reddit and Devvit constraints

Because the eventual interface is intended to fit a Reddit-hosted surface,
the architecture should assume constrained environments.

### Embed-aware design rules

- primary workflows must work in a medium-height viewport
- dense views should collapse secondary chrome intelligently
- heavy visual effects must degrade safely
- virtualization is mandatory for large tables and packet streams
- the shell should permit mobile-safe fallback views

### Progressive enhancement strategy

1. Start with a panel-oriented web app shell.
2. Deliver a simplified embedded mode with the same domain vocabulary.
3. Provide deeper standalone workflows for local or full-browser usage.

## Component System

### Core UI components

- panel frame
- section header
- rune icon button
- searchable tree
- filter chips
- diff badge
- provenance pill
- confidence tag
- metadata table
- timeline row
- hex viewer row
- formula block
- related-links card

### Visual states

Each component should support:

- idle
- hover
- selected
- focused
- warning
- unresolved
- disabled

## Example Workflows

### Workflow: investigate a drop

1. Open a saved simulation or recorded drop event.
2. Select the dropped item.
3. Inspect the generation path in the side panel.
4. Jump into treasure class recursion.
5. Open the affix table entry.
6. Export the reasoning chain as Markdown or JSON.

### Workflow: decode a save value

1. Open a `.d2s` file.
2. Click a displayed HP value.
3. Jump to the raw stat record.
4. Highlight the underlying bit range.
5. Open the stat definition and fixed-point explanation.
6. Compare the displayed value to raw storage.

### Workflow: trace a skill action

1. Open a packet timeline.
2. Filter by skill packets.
3. Select a cast event.
4. Inspect packet fields and target coordinates.
5. Jump to skill metadata.
6. Open related unit state changes in the same time window.

## Recommended technical stack for future implementation

For the eventual UI shell, the following stack is a strong fit:

- React for the application shell
- TypeScript for domain and UI contracts
- TanStack Table for large data grids
- React Flow for relationship graphs and investigative canvases
- CodeMirror or Monaco for structured text and schema editing views
- a lightweight docking system for panel layouts

## Deliverables for the first UI milestone

The first real UI milestone should produce:

- a stable shell layout
- left navigation and explorer model
- one main structured view
- one comparison view
- one inspector panel
- one bottom diagnostic drawer
- theme tokens for the Diablo IV-inspired look
- a reduced-motion and high-contrast toggle

When this milestone lands, D2RE will stop feeling like a pile of powerful
scrolls and start feeling like a research sanctum with doors between rooms.
