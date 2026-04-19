# D2RE Cleanup Checklist

This checklist converts the repository audit into phased cleanup work. The goal is to make the project honest, incremental, and easy to repair without deleting planned surfaces prematurely.

Status legend: `[ ]` not started · `[~]` started · `[x]` complete · `[disabled]` intentionally retained but inactive

## Phase 1 — Stop misleading users

- [x] Keep `d2re doctor` registered but deactivate it until `d2re.doctor` exists.
- [x] Keep `d2re gui` registered while building it in phases.
- [x] Keep `item_roller --brute` and `--target` registered but deactivate the unfinished brute-force workflow.
- [x] Add smoke tests that prove disabled commands exit cleanly instead of raising `ModuleNotFoundError`.
- [x] Add smoke tests that prove disabled item roller flags return a clear message.

## Phase 2 — Repair release metadata

- [x] Decide whether the current branch is truly `1.1.0` or should be rolled back to `1.0.x`.
- [x] Replace placeholder changelog dates.
- [x] Split shipped work from planned work under `CHANGELOG.md`.
- [x] Add an `Unreleased` section for in-progress cleanup.

## Phase 3 — Repair documentation truthfulness

- [x] Mark the hooking guide as a draft placeholder.
- [x] Mark the emulator/server guide as a draft placeholder.
- [~] Fix clone URLs so they point to `https://github.com/tmuhlhausen/D2re.git`.
  - `docs/getting-started.md` is fixed.
  - `README.md` still needs a focused follow-up patch because it is a large legacy document.
- [x] Rewrite `docs/getting-started.md` into a short onboarding guide instead of a README duplicate.
- [ ] Update the README project tree to include the current `d2re/`, `tools/`, `scripts/`, `docs/architecture/`, and maintenance docs.
- [ ] Fix example paths so documented paths match the repository.

## Phase 4 — Stabilize CLI and packaging

- [ ] Add dedicated console entry points for `d2re-tc` and `d2re-drops`, or document that they are only available through `d2re tc` and `d2re drops`.
- [ ] Replace hand-written wrapper help with parser-generated help where possible.
- [ ] Move runtime compatibility shims out of wrappers and into canonical implementation modules.
- [ ] Add a small command registry that records each command's status: stable, experimental, disabled, or planned.

## Phase 5 — Add the minimum quality floor

- [x] Add disabled command smoke tests in `tests/test_disabled_commands.py`.
- [x] Add GUI workbench smoke tests in `tests/test_gui_workbench.py`.
- [ ] Add broader import smoke tests.
- [ ] Add a lightweight GitHub Actions workflow that runs smoke tests on Linux.
- [ ] Add fixtures only when their provenance and redistribution status are clear.

## Phase 6 — Implement disabled surfaces in steps

### `d2re doctor`

- [ ] Check Python version.
- [ ] Check optional dependencies and print install commands.
- [ ] Check whether data tables exist.
- [ ] Check whether configured D2 paths exist.
- [ ] Validate common docs paths referenced from README.

### `d2re gui`

- [x] Start with a local-only launcher message and design spec.
- [x] Add a read-only desktop dashboard or local web viewer.
- [x] Reuse stable parser outputs and command surfaces rather than shelling out to brittle scripts.
- [x] Clearly label experimental UI panes.
- [ ] Add local JSON import for parser output.
- [ ] Add schema-aware result viewers.
- [ ] Add a visual command builder for common workflows.

### `item_roller --brute`

- [ ] Define target matching rules.
- [ ] Add deterministic seed iteration.
- [ ] Add maximum search bounds.
- [ ] Add JSON output.
- [ ] Add tests for tiny bounded searches.

## Rule of the cleanup

Do not delete planned surfaces merely because they are unfinished. Keep them visible, but disabled, labeled, and safe until implementation catches up.
