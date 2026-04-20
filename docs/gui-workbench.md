# D2RE Visual Workbench

The D2RE Visual Workbench is the default front door for the toolkit. Running `d2re` with no subcommand now opens a local browser UI automatically.

The workbench is no longer just a command atlas. It includes editable forms for the major D2RE workflows, live command previews, copy buttons, and guarded local execution through a loopback-only server.

## Launch

Open the interactive workbench automatically:

```bash
d2re
```

Open it explicitly:

```bash
d2re gui
```

Show CLI help without launching the GUI:

```bash
d2re --no-gui
```

Start the server without opening a browser:

```bash
d2re gui --no-open --print-path
```

Generate static HTML instead of starting the interactive server:

```bash
d2re gui --static --out ./d2re-workbench.html --no-open
```

Use the dedicated entry point:

```bash
d2re-gui
```

## What it includes

| Module | Integrated UI behavior |
|---|---|
| Save Codex | Builds and runs `.d2s` parser commands with JSON, item, and checksum options. |
| Item Forge | Builds and runs item seed, base item, iLvl, Magic Find, run-count, and affix workflows. |
| Treasure Labyrinth | Builds and runs Treasure Class inspection and recursive resolution workflows. |
| Drop Oracle | Builds and runs Monte Carlo drop-estimation workflows. |
| Map Observatory | Builds and runs seed, save-path, level, ASCII, and room-list workflows. |
| Packet Timeline | Builds and runs packet demo, verbose, list, and filter workflows. |
| Data Excavator | Builds and runs MPQ/CASC extraction, output directory, table, CSV, and TC-tree workflows. |
| Repository Doctor | Visible as a planned diagnostic surface while `d2re doctor` remains disabled. |

## Interaction model

Each module card has:

- editable fields for known command options
- generated command preview
- copy button
- run button for active workflows
- inline output with return code, stdout, and stderr
- status labels, tags, and usage guidance

The browser never submits arbitrary shell text. It sends an action key and form values to the local D2RE server. Python maps that action key to predefined module metadata and runs only approved module entry points through `sys.executable -m ...`.

## Safety model

The interactive server binds to `127.0.0.1` only and uses a per-session token for `/api/run` requests.

The GUI does not:

- accept free-form shell input
- run arbitrary executables
- mutate save files directly
- start live packet capture by default
- bundle game assets or game data

The GUI can run supported D2RE commands, so users should still review generated commands before running them.

## Static mode versus interactive mode

| Mode | Command | Can run workflows? | Best for |
|---|---|---:|---|
| Interactive default | `d2re` | Yes | Normal use |
| Explicit interactive | `d2re gui` | Yes | Normal use |
| Server no-open | `d2re gui --no-open --print-path` | Yes, while the process is running | Remote/manual browser opening |
| Static HTML | `d2re gui --static --out workbench.html` | No | Documentation, screenshots, read-only command building |
| CLI help | `d2re --no-gui` | No | Terminal-only users |

## Stopping the server

The interactive server remains alive while the process runs. Stop it with:

```text
Ctrl+C
```

## UX and design decisions

This GUI applies the uploaded UI/UX skill pack as a practical implementation checklist.

### Accessibility

- Visible skip link for keyboard users.
- Sequential headings.
- Full keyboard focus visibility with a high-contrast focus ring.
- Controls meet a 44px minimum interaction target.
- Output regions use polite live-region behavior.
- Motion respects `prefers-reduced-motion`.

### Layout

- Responsive two-column desktop layout.
- Single-column layout on smaller screens.
- Sticky module navigation on large screens.
- Search and status filters for progressive disclosure.

### Visual system

- Tokenized CSS variables for surfaces, focus, spacing, radius, typography, and dark gothic colors.
- Obsidian surfaces, blood-red accents, parchment text, and metal-like panel borders.
- No external images, fonts, frameworks, or third-party frontend scripts.

## Implementation notes

`d2re/gui.py` is a compatibility wrapper. The integrated implementation lives in `d2re/gui_integrated.py`.

Main functions:

| Function | Purpose |
|---|---|
| `build_model()` | Builds the action/card data displayed by the workbench. |
| `build_command()` | Converts trusted action metadata and form values into module argv. |
| `run_action()` | Executes predefined D2RE modules through `sys.executable -m ...`. |
| `render_workbench()` | Renders standalone HTML. |
| `write_workbench()` | Writes static HTML. |
| `serve_workbench()` | Starts the loopback interactive server. |
| `wait_for_server()` | Keeps the server alive until interrupted. |
| `main()` | CLI entry point. |

Smoke tests live in `tests/test_gui_workbench.py`.

## Next GUI steps

- Add schema-aware result viewers for parser and TC JSON outputs.
- Add file picker helpers where browser security permits it.
- Add presets for common farming, save-analysis, and packet-study workflows.
- Add command history stored locally in the browser.
- Add a deeper IDE layout with dockable panels once stable JSON schemas are available.
