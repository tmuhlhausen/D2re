# Phase 1 Foundation Roadmap

## Phase summary

Phase 1 is about laying stone, not carving angels into the arches.

The goal is to prepare D2RE for a larger transformation without destabilizing
what already works. This phase establishes structure, trust, and a practical
path from standalone scripts toward a reusable research platform.

## Primary outcomes

By the end of Phase 1, the repository should have:

- a documented architectural direction
- a clear UI and IDE product target
- a baseline automated test suite
- continuous integration for fast feedback
- contributor-facing development conventions
- a staged plan for modularization

## Scope of Phase 1

### In scope

- architecture documents
- testing strategy
- CI workflow
- basic pytest scaffolding
- development tool configuration
- changelog and roadmap hygiene
- first wave of parser-centric tests

### Explicitly out of scope

- full React or Devvit frontend implementation
- major parser rewrites
- large package refactors that move everything at once
- high-risk behavior changes to existing scripts
- full plugin system implementation

## Workstreams

### Workstream A: documentation architecture

Deliverables:

- `docs/architecture/vision.md`
- `docs/architecture/ui-ide-spec.md`
- `docs/architecture/testing-strategy.md`
- `docs/roadmap/phase-1-foundation.md`

Success looks like a contributor being able to answer:

- where the project is going
- what the first milestone includes
- what standards new work should follow

### Workstream B: quality baseline

Deliverables:

- pytest configuration
- initial parser-focused test suite
- CI workflow running tests on push and pull request

Success looks like the repo catching obvious regressions automatically.

### Workstream C: developer experience

Deliverables:

- tool configuration in `pyproject.toml`
- optional pre-commit configuration
- documented local commands

Success looks like new contributors having a short path from clone to useful
work.

### Workstream D: release hygiene

Deliverables:

- an unreleased changelog section
- a documented foundation milestone

Success looks like the branch history telling a coherent story instead of a
fog of disconnected edits.

## Suggested implementation order

1. create branch for foundation work
2. add architecture and roadmap docs
3. add test scaffolding and CI
4. add contributor tooling config
5. add changelog entry for unreleased foundation work
6. begin parser-safe modularization in later slices

## Risks

### Risk: over-refactoring too early

If Phase 1 turns into a broad code migration, regressions become likely and the
work loses focus.

**Mitigation:** keep behavior changes minimal and bias toward scaffolding.

### Risk: documentation that promises too much

A grand roadmap with no practical sequence becomes decorative.

**Mitigation:** each roadmap item should map to concrete files or milestones.

### Risk: testing without fixtures

A test suite with only synthetic micro-tests can miss real-world parser issues.

**Mitigation:** begin synthetic coverage now, then add curated fixtures in the
next slice.

## Exit criteria

Phase 1 is complete when all of the following are true:

- branch contains architecture docs for the IDE direction
- parser utilities have initial automated tests
- CI runs automatically on the repo
- local developer commands are obvious
- an unreleased changelog entry reflects the work
- Phase 2 can begin without reopening foundational debates

## What comes after Phase 1

### Phase 2: modular engine extraction

- move reusable parser and utility logic into importable modules
- define stable JSON contracts
- add fixture-backed parser tests
- begin packet and simulation regression coverage

### Phase 3: workspace shell

- implement panel-based application shell
- add explorer, inspector, and main content views
- apply Diablo IV-inspired theme tokens
- support embedded and full-browser layouts

### Phase 4: investigative workflows

- save explorer
- packet timeline and decoder
- map explorer
- item generation laboratory
- comparison tools and note capture

## Operating principle

Phase 1 should make future work easier, safer, and more legible. If a change is
flashy but does not improve those three things, it belongs in a later phase.
