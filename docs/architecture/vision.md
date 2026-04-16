# D2RE Vision: From Toolkit to Visual Research IDE

## Purpose

D2RE already covers a powerful spread of Diablo II reverse engineering topics:
packet inspection, save parsing, MPQ extraction, item generation, and map seed
analysis. The next step is to transform the repository from a collection of
excellent standalone tools into a **cohesive visual research environment**.

The long-term target is a Diablo IV-inspired visual IDE for exploring Diablo II
internals. The environment should feel like an arcane workshop rather than a
plain engineering dashboard: dark gothic surfaces, modular framed panels,
strong hierarchy, discoverable workflows, and an interface that rewards both
curiosity and rigor.

## Product Thesis

D2RE should become the place where five different audiences can work without
fighting the tool:

1. **Reverse engineers** who need structure maps, offsets, packet flows, and
   decompilation context.
2. **Tool builders** who need machine-readable outputs, schema guarantees, and
   stable APIs.
3. **Modders** who need data table visibility, item generation reasoning, and
   controlled experimentation.
4. **Theorycrafters and researchers** who need planners, simulations, and
   historical comparisons.
5. **Curious learners** who want the game explained in layers instead of being
   dropped into a hex swamp.

## Strategic Direction

The repository should evolve in three parallel tracks.

### 1. Research-grade engine core

The codebase should expose reusable modules for:

- save file parsing
- packet decoding
- data table extraction
- RNG and item generation simulation
- map generation and seed analysis
- metadata schemas and typed interchange formats

This is the bedrock. The future IDE is only as trustworthy as the engine under
its floorboards.

### 2. Documentation as product surface

Documentation should be treated as a first-class feature, not a sidecar.

That means:

- every major subsystem gets a conceptual guide
- every module gets a practical reference
- every CLI gets examples, edge cases, and expected outputs
- every ambiguous field gets provenance and confidence labels
- every roadmap slice explains what exists now, what is planned, and what is
  still uncertain

### 3. Visual IDE layer

The eventual interface should unify code-like, data-like, and world-like views
of Diablo II in one place. A user should be able to move from a packet, to the
unit it affects, to the stat that changes, to the item modifier responsible,
all without leaving the workspace.

## North-Star Experience

A user opens D2RE and lands in a Diablo IV-inspired command chamber.

On the left sits an **Explorer** showing entities such as Saves, Packets,
Items, Maps, Tables, Skills, and Structures. In the center is the active panel:
a parsed save file, a packet timeline, a structure viewer, or a simulation
result. On the right, a **Context and Insight** panel explains what the current
selection means in plain English, where the data comes from, and what related
artifacts are connected.

The workspace is not just a viewer. It should let users:

- trace data lineage from raw bytes to interpreted structures
- compare versions and patches
- launch simulations from current selections
- bookmark findings into research notebooks
- export normalized JSON, CSV, and Markdown artifacts
- attach confidence notes and hypotheses for unresolved areas

## Core Design Principles

### Explain before impressing

The UI can be theatrical, but comprehension comes first. Every screen should
answer:

- what am I looking at?
- where did this come from?
- how confident is the tool?
- what should I do next?

### Progressive depth

Beginners should get summaries. Experts should get byte offsets, formulas,
struct layouts, raw values, and reproducible steps.

### No orphaned data

Every important object should have backlinks and forward links. A stat should
link to item stat metadata. A packet should link to unit state transitions.
A map seed should link to generated room predictions.

### Determinism where possible

When a system is reproducible, D2RE should surface the deterministic path and
make it testable.

### Confidence labeling

Reverse engineering is uneven terrain. D2RE should distinguish:

- verified
- inferred
- approximate
- unresolved

## Initial Implementation Priorities

The first milestone is not the full visual IDE. It is the scaffolding that
makes it possible.

### Immediate priorities

- add architecture documentation for the IDE transition
- establish a testing baseline for parser and utility layers
- add CI so future work does not drift silently
- define conventions for schemas, fixtures, and examples
- create a phased roadmap for client, server, and shared modules

### Near-term priorities

- refactor scripts into reusable importable modules
- define canonical JSON output contracts
- add fixtures for save parsing and packet decoding regression tests
- create data dictionaries for shared domain objects
- begin a panel-oriented web architecture spec for a Devvit-friendly frontend

### Later priorities

- implement the visual explorer shell
- add workspace persistence and saved layouts
- add comparison tools and notebook workflows
- add simulation launchers and guided investigation flows

## What Success Looks Like

D2RE succeeds when a user can answer questions that are currently annoying,
scattered, or opaque:

- Why did this item roll this way?
- Which byte range in the save file represents this value?
- Which packet changed this state?
- Which structure or data table governs this mechanic?
- How does classic D2 differ from D2R here?
- What can I test next without leaving the tool?

When those questions feel one click away instead of buried under ten tabs and a
forum archaeology dig, D2RE will have crossed the bridge from repository to
instrument.
