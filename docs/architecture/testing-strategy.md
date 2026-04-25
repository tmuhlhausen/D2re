# D2RE Testing Strategy

## Why this exists

D2RE is moving from a document-heavy toolkit toward a reusable engine and,
ultimately, a visual IDE. That shift raises the cost of silent breakage.

A parser that is merely "usually right" is dangerous. A simulation that drifts
from documented formulas erodes trust. A UI that presents inferred data as
confirmed fact creates false confidence.

Testing in D2RE therefore has one job above all others:

**protect interpretive trust.**

## Testing goals

The repository's quality strategy should support five goals.

### 1. Reproducibility

If an input is deterministic, D2RE should produce deterministic output.

Examples:

- checksum validation
- bit reader behavior
- save file field extraction
- seeded simulation steps
- packet decode lookups

### 2. Safe evolution

As scripts are refactored into modules, behavior must remain stable.

### 3. Confidence boundaries

Tests should cover what is known. Documentation and metadata should separately
mark what is inferred or approximate.

### 4. Regression visibility

When changes alter outputs intentionally, the diff should be obvious.

### 5. Low-friction contribution

Contributors should be able to run the full baseline quickly.

## Test pyramid

### Unit tests

Fast tests for pure logic.

Primary targets:

- bit reader semantics
- checksum verification
- fixed-point conversion helpers
- stat width lookups
- treasure class traversal helpers
- random number generator helpers
- map seed derivation helpers

### Fixture-based parser tests

Tests driven by curated sample files with expected outputs.

Primary targets:

- `.d2s` header parsing
- stats section extraction
- item list extraction
- quest and waypoint section detection
- malformed or truncated file handling

### Golden output tests

Reference output snapshots for stable CLI behavior.

Primary targets:

- human-readable parser summaries
- JSON output structures
- packet decoder demo mode
- generated references or exported structs

### Integration tests

Tests that exercise multi-step workflows.

Examples:

- parse save, then derive summary model
- extract tables, then run simulation inputs against extracted data
- open packet demo stream, decode entries, and aggregate categories

### Documentation tests

These are lightweight but important.

Examples:

- Markdown link checks
- command examples that remain syntactically valid
- file path references that still exist

## Core test domains

### Save parsing

This is currently the strongest candidate for immediate test coverage.

Minimum required cases:

- valid checksum file
- invalid checksum file
- bit-packed stat stream with sentinel termination
- item list with zero items
- item list with socketed items
- item list with ear records
- missing optional sections handled gracefully

### Packet decoding

Near-term cases:

- known command byte resolves expected name
- unknown command byte fails safely
- demo-mode packet output remains stable
- direction labeling remains correct
- filter logic selects only intended packets

### Item generation and simulation

Near-term cases:

- deterministic seeded roll reproduces output
- MF diminishing returns helper remains mathematically consistent
- quality cascade ordering remains intact
- impossible unique falls back correctly when applicable

### Map seed tools

Near-term cases:

- seed cascade math is deterministic
- ASCII renderer produces bounded output
- invalid level identifiers fail clearly

## Confidence labeling in tests

Not every subsystem has the same epistemic status. Tests should reflect that.

### Verified behavior

Use strict assertions.

### Approximate or inferred behavior

Use explicit naming and guardrails, for example:

- `test_estimated_d2r_layout_shape_is_stable`
- `test_inferred_field_mapping_does_not_crash`

This prevents approximate knowledge from masquerading as canonical truth.

## Fixtures strategy

D2RE should maintain a `tests/fixtures/` directory over time.

Recommended fixture categories:

- `saves/`
- `packets/`
- `tables/`
- `maps/`
- `expected/`

Each fixture should be accompanied by a short manifest describing:

- source or provenance
- game version
- whether the file is synthetic or captured
- whether expected outputs are verified or inferred
- legal or redistribution notes

## CI quality gates

The baseline CI workflow should enforce:

- repository checkout
- Python installation
- dependency installation
- test run with pytest
- optional lint pass for changed Python files later

Near-term CI should stay lean. The goal is reliability, not ceremonial build
machinery.

## What should fail the build immediately

- syntax errors
- failing parser unit tests
- checksum regression failures
- broken import paths in tests
- malformed workflow or test config

## What should warn but not necessarily fail yet

- documentation link drift
- missing fixtures for new subsystems
- experimental D2R approximation changes

## Local developer workflow

Recommended commands:

```bash
python -m pytest
python -m pytest tests/test_d2s_bitreader.py
python -m pytest -k checksum
```

Future expansion can add:

```bash
python -m pytest --cov
pre-commit run --all-files
```

## Phase 1 coverage target

The first implementation phase should not chase vanity percentages. It should
cover the parts of the repo most likely to become shared infrastructure.

### Priority order

1. `scripts/d2s_parser.py`
2. shared utility behavior extracted from parser logic
3. packet decoder demo behavior
4. deterministic simulation helpers

## Success criteria

This strategy is working when:

- contributors can make changes without breaking parser fundamentals
- CLI behavior becomes safer to refactor
- the repo begins accumulating trustworthy fixtures
- future UI work can consume stable outputs rather than shelling out to brittle
  ad hoc scripts

In other words, the tests should turn D2RE from a chest of artifacts into a
measured laboratory.
