# D2RE Command Center

The D2RE Visual Workbench is the default front door for the toolkit. Running `d2re` with no subcommand opens a local browser UI automatically.

The current shell is the **Runic Workbench**: a visual IDE-style cockpit with command builders, presets, favorites, local run history, output tools, theme controls, density controls, and guarded local execution through a loopback-only server.

## Startup behavior

Running the package entry point with no subcommand now opens the GUI automatically:

```bash
d2re
```

Terminal workflows still work through explicit subcommands:

```bash
d2re parse MyChar.d2s --json
d2re roll --seed 0xDEADBEEF --ilvl 85 --mf 300
d2re tc --tc "Act 5 Super C" --resolve --top 25
```

## Launch commands

Generate and open the command center:

```bash
d2re
```

Or explicitly:

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
d2re gui --out ./d2re-command-center.html --no-open
```

Use the dedicated entry point:

```bash
d2re-gui
```

## IDE enhancements

| Feature | What it does |
|---|---|
| Theme selector | Switches between Blood, Ember, and Spectral visual themes. |
| Density selector | Switches between comfortable and compact panel spacing. |
| Favorites | Stars frequently used modules and filters to them. |
| Command palette | Press `Ctrl+K` or `Cmd+K` to jump to modules and presets. |
| Presets | Loads common workflows such as packet demo, Act V TC scan, Meph drop oracle, map seed route check, and table extraction. |
| Run history | Stores recent commands locally in the browser for quick copy/reuse. |
| Output tools | Copy output, clear output, and try Pretty JSON formatting for JSON stdout. |
| Runic panels | Adds icon-like rune markers, stronger hierarchy, animated ambience, and Diablo-inspired dark paneling. |

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
- output copy / clear / Pretty JSON tools
- favorite toggle
- status labels, tags, and usage guidance

| Builder | Purpose |
|---|---|
| Save Parser | Build `.d2s` parsing, item listing, checksum, and JSON commands. |
| Item Roller | Build deterministic seed, Magic Find, Treasure Class, and affix commands. |
| Data Extractor | Build MPQ/CASC extraction, table export, string extraction, and TC-tree commands. |
| Packet Sniffer | Build demo, verbose, live capture, PCAP decode, filter, output, list, and struct-generation commands. |
| Map Seed Tool | Build save-seed, explicit-seed, level, ASCII, rooms, BSP, and brute-force commands. |
| Treasure Class Explorer | Build TC inspection, resolution, top-N, and JSON commands. |
| Drop Calculator | Build Monte Carlo drop-estimation commands. |
| GUI Launcher | Build command-center output/opening commands. |
| Repository Doctor | Shows the planned diagnostic surface while `d2re doctor` remains disabled. |

The browser never executes these commands. It only previews and copies them so the user can run them deliberately in a terminal.

## Extra functionality

The command center adds more than the original module cards:

- command builders for all public commands
- command preview that updates as form fields change
- copy buttons for generated commands
- workflow recipes with multi-command scripts
- search and status filtering
- module cards linked to their builders
- startup guidance explaining that plain `d2re` opens the GUI

## UX and design decisions

This GUI applies the uploaded UI/UX skill pack as a practical implementation checklist.

### Accessibility

- Visible skip link for keyboard users.
- Sequential headings.
- Full keyboard focus visibility with a high-contrast focus ring.
- Controls meet a 44px minimum interaction target.
- Output regions use polite live-region behavior.
- Motion respects `prefers-reduced-motion`.
- Theme and density preferences are stored locally in the browser.

### Layout

- Three-column desktop IDE layout with left module/preset rail, central work cards, and right history/notes rail.
- Responsive collapse for tablet and phone layouts.
- Search, favorites, command palette, and presets for progressive disclosure.

### Visual system

- Tokenized CSS variables for surfaces, focus, spacing, radius, typography, and dark gothic colors.
- Obsidian surfaces, blood-red accents, ember/spectral variants, parchment text, and metal-like panel borders.
- Rune-style module markers and animated ambient overlays.
- No external images, fonts, frameworks, or third-party frontend scripts.

## Implementation notes

`d2re/gui.py` is a compatibility wrapper. It preserves the core API from `d2re/gui_integrated.py` while routing the rendered UI and CLI entrypoint through `d2re/gui_beautified.py`.

Main structures and functions:

| Name | Purpose |
|---|---|
| `build_model()` | Builds the action/card data displayed by the workbench. |
| `build_command()` | Converts trusted action metadata and form values into module argv. |
| `run_action()` | Executes predefined D2RE modules through `sys.executable -m ...`. |
| `render_workbench()` | Renders the enhanced Runic Workbench HTML. |
| `write_workbench()` | Writes static HTML. |
| `serve_workbench()` | Starts the loopback interactive server. |
| `wait_for_server()` | Keeps the server alive until interrupted. |
| `main()` | CLI entry point. |

Smoke tests live in `tests/test_gui_workbench.py`.

## Next GUI steps

- Add schema-aware result viewers for parser and TC JSON outputs.
- Add workflow-specific result cards such as drop-rate confidence intervals and TC recursion maps.
- Add file picker helpers where browser security permits it.
- Add more presets for farming, save-analysis, packet-study, and data extraction workflows.
- Add a deeper IDE layout with dockable panels once stable JSON schemas are available.
