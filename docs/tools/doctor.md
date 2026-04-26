# `d2re doctor`

`d2re doctor` runs repository and environment self-checks for D2RE.

## What it checks

- required repository files and script entrypoints
- optional docs/examples that unlock documented workflows
- module imports for packaged commands
- optional dependencies such as `scapy`, `colorama`, and `mpyq`
- common Diablo II install paths and save-file locations

## Examples

```bash
d2re doctor
d2re doctor --json
d2re doctor --strict
d2re doctor --project-root /path/to/D2re
```

## Exit codes

- `0`: no errors
- `1`: warnings present and `--strict` was used
- `2`: one or more hard errors

This command supports the roadmap's foundational cleanup work by catching path drift, missing assets, and packaging regressions early.
