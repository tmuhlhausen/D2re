#!/usr/bin/env python3
"""Local browser command center for D2RE.

The GUI is a standalone, read-only browser workbench. It gives users a safe
visual front door, command builders for every public command surface, workflow
recipes, and copyable terminal commands without starting a server or executing
shell commands from the browser.
"""

from __future__ import annotations

import argparse
import html
import json
import tempfile
import webbrowser
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class WorkbenchCard:
    """One visible workbench module."""

    title: str
    status: str
    summary: str
    command: str
    detail: str
    tags: tuple[str, ...]
    builder_id: str


@dataclass(frozen=True)
class CommandField:
    """One command-builder field rendered by the GUI."""

    name: str
    label: str
    flag: str = ""
    kind: str = "text"
    placeholder: str = ""
    default: str = ""
    help: str = ""
    choices: tuple[str, ...] = ()
    checked: bool = False
    positional: bool = False


@dataclass(frozen=True)
class CommandSpec:
    """A complete command-builder specification."""

    id: str
    title: str
    base: str
    status: str
    summary: str
    safety: str
    fields: tuple[CommandField, ...]


@dataclass(frozen=True)
class WorkflowRecipe:
    """A copyable multi-step workflow."""

    title: str
    summary: str
    commands: tuple[str, ...]


@dataclass(frozen=True)
class WorkbenchModel:
    """Serializable data used by the HTML workbench."""

    app_name: str
    version_label: str
    startup_behavior: str
    design_note: str
    cards: tuple[WorkbenchCard, ...]
    command_specs: tuple[CommandSpec, ...]
    recipes: tuple[WorkflowRecipe, ...]


DEFAULT_CARDS: tuple[WorkbenchCard, ...] = (
    WorkbenchCard("Save Codex", "Active", "Inspect .d2s character files, stats, skills, items, quests, waypoints, and checksum state.", "d2re parse MyChar.d2s --json", "Use this pane when a character file is the source of truth. Start in JSON mode when another tool needs stable output, then compare against references/d2s-format.md for field-level investigation.", ("save", "parser", "d2s", "items"), "parse"),
    WorkbenchCard("Item Forge", "Active", "Run deterministic item-quality experiments and Magic Find simulations.", "d2re roll --seed 0xDEADBEEF --ilvl 85 --mf 300", "Use this for seed behavior, item-level assumptions, Magic Find curves, and quick item-quality checks.", ("item", "rng", "magic-find", "quality"), "roll"),
    WorkbenchCard("Treasure Labyrinth", "Active", "Walk Treasure Class trees and resolve terminal drops after extracting tc_tree.json.", "d2re tc --tc \"Act 5 Super C\" --resolve --top 25", "Use this view to explain why a drop can happen, where recursion enters another TC, and which terminal codes dominate the output.", ("treasure-class", "drops", "tc", "loot"), "tc"),
    WorkbenchCard("Drop Oracle", "Active", "Estimate target drop odds through Monte Carlo simulation.", "d2re drops --tc \"Mephisto (N)\" --item weap87 --runs 250000", "Best for practical target-farming questions, confidence estimates, and high-volume comparisons.", ("monte-carlo", "odds", "drop-rate", "simulation"), "drops"),
    WorkbenchCard("Map Observatory", "Active", "Inspect seeds, derive level seeds, and visualize predicted map layouts.", "d2re map --seed 0x3F7A1B2C --level 21 --ascii", "Use this for seed archaeology, route research, and plausibility checks before deeper map tooling.", ("map", "seed", "drlg", "ascii"), "map"),
    WorkbenchCard("Packet Timeline", "Active", "Decode known D2 packet commands and inspect demo traffic without live capture.", "d2re sniff --demo --verbose", "Start with demo mode for a safe baseline. Live capture can require admin/root privileges and platform-specific packet support.", ("packet", "network", "sniffer", "protocol"), "sniff"),
    WorkbenchCard("Data Excavator", "Active", "Extract MPQ or CASC data tables into local analysis files.", "d2re extract --all-mpqs \"C:/Diablo II/\" --out ./data_tables/", "This is the gateway for table-backed analysis. D2RE never ships game data, so users supply their own local installation paths.", ("mpq", "casc", "tables", "extract"), "extract"),
    WorkbenchCard("Workbench Launcher", "Active", "Generate, save, and reopen the standalone visual workbench.", "d2re gui --no-open --print-path", "Use this when you want a persistent local HTML launcher or a predictable output path for documentation and testing.", ("gui", "launcher", "html", "startup"), "gui"),
    WorkbenchCard("Repository Doctor", "Planned", "Future environment self-check for Python, optional dependencies, paths, and data-table readiness.", "d2re doctor", "Visible by design, but still disabled until diagnostic checks are implemented and tested.", ("doctor", "health", "planned", "diagnostics"), "doctor"),
)


COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec("parse", "Save Parser", "d2re parse", "Active", "Build commands for .d2s save parsing and JSON export.", "Read-only analysis of a local save path you provide.", (
        CommandField("save", "Save file", positional=True, placeholder="MyChar.d2s", default="MyChar.d2s", help="Path to the character save file."),
        CommandField("json", "JSON output", "--json", "checkbox", checked=True, help="Prefer stable machine-readable output."),
        CommandField("items", "Show items", "--items", "checkbox"),
        CommandField("verify", "Verify checksum", "--verify", "checkbox"),
    )),
    CommandSpec("roll", "Item Roller", "d2re roll", "Active", "Build deterministic item-generation and Magic Find simulation commands.", "The browser only builds the command. The terminal performs the simulation.", (
        CommandField("seed", "Seed", "--seed", placeholder="0xDEADBEEF", default="0xDEADBEEF"),
        CommandField("base", "Base item code", "--base", placeholder="7cr"),
        CommandField("ilvl", "Item level", "--ilvl", "number", default="85"),
        CommandField("mf", "Magic Find", "--mf", "number", default="300"),
        CommandField("tc", "Treasure Class", "--tc", placeholder="Act 5 Super C"),
        CommandField("runs", "Runs", "--runs", "number", default="100000"),
        CommandField("affix", "Roll magic affixes", "--affix", "checkbox"),
        CommandField("brute", "Brute-force search", "--brute", "checkbox", help="Registered but currently disabled by the CLI."),
        CommandField("target", "Target item", "--target", placeholder="Stone of Jordan", help="Registered but currently disabled by the CLI."),
    )),
    CommandSpec("extract", "Data Extractor", "d2re extract", "Active", "Build MPQ/CASC extraction commands for local game data.", "Only point this at game files you own. D2RE does not ship assets.", (
        CommandField("all_mpqs", "Classic D2 folder", "--all-mpqs", placeholder="C:/Diablo II/", default="C:/Diablo II/"),
        CommandField("out", "Output folder", "--out", placeholder="./data_tables/", default="./data_tables/"),
        CommandField("table", "Single table", "--table", placeholder="weapons"),
        CommandField("csv", "CSV output", "--csv", "checkbox"),
        CommandField("json_out", "JSON output", "--json-out", "checkbox"),
        CommandField("tc_tree", "Build TC tree", "--tc-tree", "checkbox"),
        CommandField("strings", "Extract strings", "--strings", "checkbox"),
        CommandField("d2r", "D2R install path", "--d2r", placeholder="C:/Program Files (x86)/Diablo II Resurrected/"),
    )),
    CommandSpec("sniff", "Packet Sniffer", "d2re sniff", "Active", "Build packet demo, list, pcap decode, and live capture commands.", "Live capture may require admin/root privileges. Demo mode is safest first.", (
        CommandField("demo", "Demo mode", "--demo", "checkbox", checked=True),
        CommandField("verbose", "Verbose annotations", "--verbose", "checkbox", checked=True),
        CommandField("interface", "Interface", "--interface", placeholder="Ethernet or eth0"),
        CommandField("live", "Live capture", "--live", "checkbox"),
        CommandField("pcap", "PCAP file", "--pcap", placeholder="session.pcap"),
        CommandField("decode", "Decode PCAP", "--decode", "checkbox"),
        CommandField("filter", "Packet filter", "--filter", placeholder="0x0F"),
        CommandField("output", "JSON output file", "--output", placeholder="session.json"),
        CommandField("list", "List packets", "--list", "checkbox"),
        CommandField("structs", "Generate C structs", "--generate-structs", "checkbox"),
    )),
    CommandSpec("map", "Map Seed Tool", "d2re map", "Active", "Build map seed, room listing, and ASCII layout commands.", "Use local saves or seed values. The UI does not edit save files.", (
        CommandField("d2s", "Save file", "--d2s", placeholder="MyChar.d2s"),
        CommandField("seed", "Seed", "--seed", placeholder="0x3F7A1B2C", default="0x3F7A1B2C"),
        CommandField("level", "Level ID", "--level", "number", default="21"),
        CommandField("show_seed", "Show seed", "--show-seed", "checkbox"),
        CommandField("ascii", "ASCII map", "--ascii", "checkbox", checked=True),
        CommandField("rooms", "List rooms", "--rooms", "checkbox"),
        CommandField("bsp", "Use BSP", "--bsp", "checkbox"),
        CommandField("brute", "Brute force", "--brute", "checkbox"),
        CommandField("max", "Max seeds", "--max", "number", placeholder="1000000"),
    )),
    CommandSpec("tc", "Treasure Class Explorer", "d2re tc", "Active", "Build Treasure Class inspection and resolution commands.", "Requires extracted TC data before deeper resolution commands work.", (
        CommandField("tc", "Treasure Class", "--tc", placeholder="Act 5 Super C", default="Act 5 Super C"),
        CommandField("resolve", "Resolve tree", "--resolve", "checkbox", checked=True),
        CommandField("top", "Top results", "--top", "number", default="25"),
        CommandField("json", "JSON output", "--json", "checkbox"),
    )),
    CommandSpec("drops", "Drop Calculator", "d2re drops", "Active", "Build Monte Carlo drop-calculation commands.", "High run counts may take time in the terminal.", (
        CommandField("tc", "Treasure Class", "--tc", placeholder="Mephisto (N)", default="Mephisto (N)"),
        CommandField("item", "Target item code", "--item", placeholder="weap87", default="weap87"),
        CommandField("runs", "Runs", "--runs", "number", default="250000"),
        CommandField("mf", "Magic Find", "--mf", "number", default="300"),
        CommandField("json", "JSON output", "--json", "checkbox"),
    )),
    CommandSpec("gui", "GUI Launcher", "d2re gui", "Active", "Build workbench generation commands.", "The GUI writes one local HTML file and optionally opens it.", (
        CommandField("out", "Output HTML path", "--out", placeholder="./d2re-workbench.html"),
        CommandField("no_open", "Do not open browser", "--no-open", "checkbox"),
        CommandField("print_path", "Print path only", "--print-path", "checkbox"),
    )),
    CommandSpec("doctor", "Repository Doctor", "d2re doctor", "Disabled", "Reserved for future environment and repository diagnostics.", "This command is intentionally disabled until checks are implemented.", ()),
)


RECIPES: tuple[WorkflowRecipe, ...] = (
    WorkflowRecipe("First safe tour", "Open the GUI, run the packet demo, then inspect command help.", ("d2re", "d2re sniff --demo --verbose", "d2re --help")),
    WorkflowRecipe("Save-file inspection", "Parse a character save and keep JSON for later comparison.", ("d2re parse MyChar.d2s --json > char_data.json", "d2re parse MyChar.d2s --items --verify")),
    WorkflowRecipe("Treasure Class research", "Extract table data, build the TC tree, then inspect a high-level class.", ("d2re extract --all-mpqs \"C:/Diablo II/\" --out ./data_tables/ --tc-tree", "d2re tc --tc \"Act 5 Super C\" --resolve --top 25", "d2re drops --tc \"Mephisto (N)\" --item weap87 --runs 250000")),
    WorkflowRecipe("Map seed study", "Read a seed from a save, then render a predicted ASCII layout.", ("d2re map --d2s MyChar.d2s --show-seed", "d2re map --seed 0x3F7A1B2C --level 21 --ascii --rooms")),
)


def build_model() -> WorkbenchModel:
    """Return the static workbench model."""

    return WorkbenchModel(
        app_name="D2RE Command Center",
        version_label="Integrated GUI wave",
        startup_behavior="Running plain `d2re` opens this workbench automatically. Use explicit subcommands for terminal-only workflows.",
        design_note=(
            "Local, read-only, accessible browser interface using tokenized dark-gothic panels, "
            "command builders, workflow recipes, keyboard-friendly controls, and reduced-motion support."
        ),
        cards=DEFAULT_CARDS,
        command_specs=COMMAND_SPECS,
        recipes=RECIPES,
    )


def _json_for_script(model: WorkbenchModel) -> str:
    raw = json.dumps(asdict(model), ensure_ascii=False, indent=2)
    return raw.replace("</", "<\\/")


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <style>
    :root{color-scheme:dark;--primitive-obsidian-950:#080605;--primitive-obsidian-900:#120d0c;--primitive-iron-800:#241b18;--primitive-iron-700:#342824;--primitive-blood-600:#a92923;--primitive-blood-500:#d13b32;--primitive-ember-400:#f09a4a;--primitive-parchment-100:#f7ead0;--primitive-muted-300:#bba88d;--surface-page:radial-gradient(circle at 10% 0%,rgba(209,59,50,.22),transparent 32rem),linear-gradient(135deg,var(--primitive-obsidian-950),var(--primitive-obsidian-900) 58%,#050403);--surface-panel:rgba(20,14,12,.9);--surface-panel-strong:rgba(34,24,20,.97);--surface-parchment:linear-gradient(180deg,rgba(247,234,208,.1),rgba(247,234,208,.035));--border-metal:rgba(231,215,189,.22);--border-blood:rgba(209,59,50,.45);--text-primary:var(--primitive-parchment-100);--text-secondary:var(--primitive-muted-300);--accent:var(--primitive-blood-500);--accent-hot:var(--primitive-ember-400);--focus:#ffd28a;--radius-panel:20px;--radius-control:12px;--shadow-glow:0 0 32px rgba(209,59,50,.22);--shadow-panel:0 18px 60px rgba(0,0,0,.42);--space-2:.5rem;--space-3:.75rem;--space-4:1rem;--space-5:1.25rem;--space-6:1.5rem;--font-display:Georgia,"Times New Roman",serif;--font-body:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--font-mono:"SFMono-Regular",Consolas,"Liberation Mono",monospace}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;min-height:100vh;background:var(--surface-page);color:var(--text-primary);font-family:var(--font-body);font-size:16px;line-height:1.55}body:before{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:44px 44px;mask-image:radial-gradient(circle at center,black,transparent 80%)}a{color:var(--primitive-parchment-100)}:focus-visible{outline:3px solid var(--focus);outline-offset:3px}.skip-link{position:absolute;left:1rem;top:-4rem;z-index:10;padding:.75rem 1rem;border-radius:var(--radius-control);background:var(--primitive-parchment-100);color:#080605}.skip-link:focus{top:1rem}.shell{width:min(1500px,100%);margin:0 auto;padding:clamp(1rem,2vw,2rem)}.panel{position:relative;overflow:hidden;border:1px solid var(--border-metal);border-radius:var(--radius-panel);background:var(--surface-panel);box-shadow:var(--shadow-panel)}.panel:before{content:"";position:absolute;inset:0;pointer-events:none;border-radius:inherit;background:linear-gradient(135deg,rgba(247,234,208,.11),transparent 18%,rgba(209,59,50,.08))}.hero{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr);gap:var(--space-6);align-items:stretch;margin-bottom:var(--space-6)}.hero-main{padding:clamp(1.5rem,4vw,4rem)}.hero-side{display:grid;gap:var(--space-4);padding:var(--space-5);background:var(--surface-panel-strong)}.eyebrow{display:inline-flex;align-items:center;min-height:44px;color:var(--accent-hot);letter-spacing:.16em;text-transform:uppercase;font-size:.78rem;font-weight:800}h1,h2,h3{margin:0;font-family:var(--font-display);line-height:1.05}h1{max-width:13ch;margin-top:.75rem;font-size:clamp(2.75rem,8vw,6.8rem);letter-spacing:-.06em}.hero-copy{max-width:75ch;margin:1.25rem 0 0;color:var(--text-secondary);font-size:clamp(1rem,1.4vw,1.2rem)}.stat-card{min-height:44px;padding:var(--space-4);border:1px solid var(--border-metal);border-radius:16px;background:var(--surface-parchment)}.stat-card strong{display:block;color:var(--text-primary)}.stat-card span{color:var(--text-secondary)}.toolbar{display:grid;grid-template-columns:minmax(220px,1fr) auto auto;gap:var(--space-3);align-items:center;margin-bottom:var(--space-6);padding:var(--space-4)}label{display:grid;gap:.5rem;font-weight:700;color:var(--text-primary)}input,select,button,textarea{min-height:44px;border-radius:var(--radius-control);border:1px solid var(--border-metal);font:inherit}input,select,textarea{width:100%;padding:0 1rem;background:rgba(0,0,0,.26);color:var(--text-primary)}textarea{padding:1rem;min-height:120px;font-family:var(--font-mono)}button{cursor:pointer;padding:0 1rem;background:linear-gradient(180deg,rgba(209,59,50,.95),rgba(118,25,22,.96));color:var(--text-primary);font-weight:800;box-shadow:var(--shadow-glow)}button.secondary{background:rgba(247,234,208,.08);box-shadow:none}.layout{display:grid;grid-template-columns:280px minmax(0,1fr);gap:var(--space-6);align-items:start}.nav-panel{position:sticky;top:1rem;padding:1rem}.module-list{display:grid;gap:.5rem;margin-top:1rem}.module-link{display:flex;justify-content:space-between;align-items:center;gap:.75rem;min-height:44px;padding:.75rem;border:1px solid transparent;border-radius:var(--radius-control);color:var(--text-primary);text-decoration:none}.module-link:hover,.module-link[aria-current=true]{border-color:var(--border-blood);background:rgba(209,59,50,.12)}.cards,.builders,.recipes{display:grid;gap:1.25rem}.card,.builder,.recipe{display:grid;gap:1rem;padding:1.25rem}.card-header,.builder-header{display:flex;justify-content:space-between;gap:1rem;align-items:start}.card h3,.builder h3{font-size:clamp(1.45rem,3vw,2.3rem)}.status{display:inline-flex;align-items:center;min-height:32px;padding:0 .75rem;border:1px solid var(--border-metal);border-radius:999px;color:var(--text-secondary);font-size:.84rem;font-weight:800;white-space:nowrap}.status[data-status=Active]{border-color:rgba(240,154,74,.55);color:var(--accent-hot)}.summary{max-width:72ch;margin:0;color:var(--text-secondary)}.command-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:.75rem;align-items:center;padding:.75rem;border:1px solid var(--border-metal);border-radius:16px;background:rgba(0,0,0,.28)}code{color:var(--text-primary);font-family:var(--font-mono);overflow-wrap:anywhere}.tag-list{display:flex;flex-wrap:wrap;gap:.5rem;padding:0;margin:0;list-style:none}.tag-list li{padding:.2rem .55rem;border:1px solid var(--border-metal);border-radius:999px;color:var(--text-secondary);font-size:.84rem}.section-title{margin:2rem 0 1rem}.builder-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}.builder-output{position:sticky;bottom:1rem;z-index:2}.small{font-size:.9rem;color:var(--text-secondary)}.toast{position:fixed;right:1rem;bottom:1rem;max-width:min(420px,calc(100vw - 2rem));padding:1rem;border:1px solid var(--border-blood);border-radius:var(--radius-control);background:var(--surface-panel-strong);color:var(--text-primary);box-shadow:var(--shadow-panel);transform:translateY(140%);transition:transform 180ms ease}.toast[data-visible=true]{transform:translateY(0)}.empty{display:none;padding:1.5rem;text-align:center;color:var(--text-secondary)}.empty[data-visible=true]{display:block}@media(max-width:980px){.hero,.layout,.toolbar{grid-template-columns:1fr}.nav-panel{position:static}.builder-grid{grid-template-columns:1fr}}@media(max-width:560px){.shell{padding:.75rem}.card-header,.builder-header,.command-row{display:grid;grid-template-columns:1fr}button{width:100%}}@media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;transition-duration:.001ms!important;animation-duration:.001ms!important;animation-iteration-count:1!important}}
  </style>
</head>
<body>
  <a class="skip-link" href="#command-center">Skip to command center</a>
  <div class="shell">
    <header class="hero" aria-labelledby="page-title">
      <section class="panel hero-main">
        <div class="eyebrow">D2RE startup surface</div>
        <h1 id="page-title">Command Center</h1>
        <p class="hero-copy">__DESIGN_NOTE__</p>
      </section>
      <aside class="panel hero-side" aria-label="Workbench principles">
        <div class="stat-card"><strong>Auto-load startup</strong><span>Running plain <code>d2re</code> opens this GUI workbench.</span></div>
        <div class="stat-card"><strong>Integrated commands</strong><span>Every public command has a builder, command preview, and copy button.</span></div>
        <div class="stat-card"><strong>Safe by design</strong><span>The browser builds commands but never executes shell actions.</span></div>
      </aside>
    </header>

    <section class="panel toolbar" aria-label="Workbench controls">
      <label for="search">Search modules
        <input id="search" type="search" autocomplete="off" placeholder="Try save, item, packet, map, tc, doctor" />
      </label>
      <label for="status">Status
        <select id="status"><option value="all">All modules</option><option value="Active">Active</option><option value="Planned">Planned</option><option value="Disabled">Disabled</option></select>
      </label>
      <button class="secondary" type="button" id="reset">Reset filters</button>
    </section>

    <main class="layout" id="workbench">
      <nav class="panel nav-panel" aria-label="Workbench navigation">
        <h2>Modules</h2>
        <div class="module-list" id="module-list"></div>
      </nav>
      <section>
        <h2 class="section-title">Discovery panels</h2>
        <div class="cards" id="cards" aria-label="Workbench modules"></div>
        <p class="empty" id="empty" data-visible="false">No modules match the current filters.</p>
        <h2 class="section-title" id="command-center">Command builders</h2>
        <div class="builders" id="builders"></div>
        <h2 class="section-title">Workflow recipes</h2>
        <div class="recipes" id="recipes"></div>
      </section>
    </main>
  </div>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>
  <script id="workbench-data" type="application/json">__PAYLOAD__</script>
  <script>
    const model = JSON.parse(document.getElementById('workbench-data').textContent);
    const cardsEl = document.getElementById('cards');
    const buildersEl = document.getElementById('builders');
    const recipesEl = document.getElementById('recipes');
    const navEl = document.getElementById('module-list');
    const searchEl = document.getElementById('search');
    const statusEl = document.getElementById('status');
    const emptyEl = document.getElementById('empty');
    const toastEl = document.getElementById('toast');
    const resetEl = document.getElementById('reset');
    const builderState = {};

    function slugify(value){return value.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'')}
    function escapeHtml(value){return String(value ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]))}
    function quoteArg(value){const text=String(value ?? '').trim(); if(!text)return ''; if(!/[\s\"']/.test(text))return text; return '"'+text.replace(/"/g,'\\"')+'"'}
    function matches(card){const needle=searchEl.value.trim().toLowerCase();const status=statusEl.value;const hay=[card.title,card.status,card.summary,card.command,card.detail,...card.tags].join(' ').toLowerCase();return (status==='all'||card.status===status)&&(!needle||hay.includes(needle))}
    async function copyText(text){try{await navigator.clipboard.writeText(text);showToast('Copied to clipboard.')}catch(error){showToast('Copy failed. Select the text manually.')}}
    function showToast(message){toastEl.textContent=message;toastEl.dataset.visible='true';clearTimeout(showToast.timeout);showToast.timeout=setTimeout(()=>toastEl.dataset.visible='false',2200)}

    function getFieldValue(specId, field){const key=`${specId}.${field.name}`;return builderState[key] ?? (field.kind==='checkbox' ? Boolean(field.checked) : field.default || '')}
    function setFieldValue(specId, field, value){builderState[`${specId}.${field.name}`]=value}
    function buildCommand(spec){const parts=spec.base.split(' ');for(const field of spec.fields){const value=getFieldValue(spec.id,field);if(field.kind==='checkbox'){if(value)parts.push(field.flag);continue}if(!String(value).trim())continue;if(field.positional){parts.push(quoteArg(value));continue}parts.push(field.flag,quoteArg(value))}return parts.filter(Boolean).join(' ')}

    function renderField(spec, field){const id=`${spec.id}-${field.name}`;const value=getFieldValue(spec.id,field);if(field.kind==='checkbox'){return `<label for="${id}"><span><input id="${id}" data-spec="${spec.id}" data-field="${field.name}" type="checkbox" ${value?'checked':''}/> ${escapeHtml(field.label)}</span><span class="small">${escapeHtml(field.help)}</span></label>`}if(field.kind==='select'){return `<label for="${id}">${escapeHtml(field.label)}<select id="${id}" data-spec="${spec.id}" data-field="${field.name}">${field.choices.map(choice=>`<option value="${escapeHtml(choice)}" ${choice===value?'selected':''}>${escapeHtml(choice)}</option>`).join('')}</select><span class="small">${escapeHtml(field.help)}</span></label>`}return `<label for="${id}">${escapeHtml(field.label)}<input id="${id}" data-spec="${spec.id}" data-field="${field.name}" type="${field.kind==='number'?'number':'text'}" value="${escapeHtml(value)}" placeholder="${escapeHtml(field.placeholder)}"/><span class="small">${escapeHtml(field.help)}</span></label>`}

    function renderCards(){const visible=model.cards.filter(matches);cardsEl.innerHTML='';navEl.innerHTML='';emptyEl.dataset.visible=String(visible.length===0);visible.forEach((card,index)=>{const id=slugify(card.title);const nav=document.createElement('a');nav.className='module-link';nav.href=`#${id}`;nav.innerHTML=`<span>${escapeHtml(card.title)}</span><span>${escapeHtml(card.status)}</span>`;navEl.appendChild(nav);const article=document.createElement('article');article.className='panel card';article.id=id;article.tabIndex=-1;article.innerHTML=`<div class="card-header"><div><p class="eyebrow">Module ${index+1}</p><h3>${escapeHtml(card.title)}</h3></div><span class="status" data-status="${escapeHtml(card.status)}">${escapeHtml(card.status)}</span></div><p class="summary">${escapeHtml(card.summary)}</p><div class="command-row"><code>${escapeHtml(card.command)}</code><button class="copy-command" type="button">Copy command</button></div><details><summary>When to use this module</summary><p>${escapeHtml(card.detail)}</p></details><ul class="tag-list" aria-label="Module tags">${card.tags.map(tag=>`<li>${escapeHtml(tag)}</li>`).join('')}</ul><a href="#builder-${escapeHtml(card.builder_id)}">Open builder</a>`;article.querySelector('.copy-command').addEventListener('click',()=>copyText(card.command));cardsEl.appendChild(article)})}

    function renderBuilders(){buildersEl.innerHTML='';model.command_specs.forEach(spec=>{const article=document.createElement('article');article.className='panel builder';article.id=`builder-${spec.id}`;article.innerHTML=`<div class="builder-header"><div><p class="eyebrow">Command builder</p><h3>${escapeHtml(spec.title)}</h3><p class="summary">${escapeHtml(spec.summary)}</p><p class="small">${escapeHtml(spec.safety)}</p></div><span class="status" data-status="${escapeHtml(spec.status)}">${escapeHtml(spec.status)}</span></div><div class="builder-grid">${spec.fields.length?spec.fields.map(field=>renderField(spec,field)).join(''):'<p class="summary">This command is reserved and currently disabled.</p>'}</div><div class="command-row builder-output"><code data-output="${spec.id}">${escapeHtml(buildCommand(spec))}</code><button type="button" data-copy-builder="${spec.id}">Copy built command</button></div>`;buildersEl.appendChild(article)});buildersEl.querySelectorAll('input,select').forEach(input=>{input.addEventListener('input',event=>{const spec=model.command_specs.find(item=>item.id===event.target.dataset.spec);const field=spec.fields.find(item=>item.name===event.target.dataset.field);setFieldValue(spec.id,field,field.kind==='checkbox'?event.target.checked:event.target.value);const output=buildersEl.querySelector(`[data-output="${spec.id}"]`);output.textContent=buildCommand(spec)})});buildersEl.querySelectorAll('[data-copy-builder]').forEach(button=>button.addEventListener('click',()=>{const spec=model.command_specs.find(item=>item.id===button.dataset.copyBuilder);copyText(buildCommand(spec))}))}

    function renderRecipes(){recipesEl.innerHTML='';model.recipes.forEach(recipe=>{const article=document.createElement('article');article.className='panel recipe';const script=recipe.commands.join('\n');article.innerHTML=`<h3>${escapeHtml(recipe.title)}</h3><p class="summary">${escapeHtml(recipe.summary)}</p><textarea readonly>${escapeHtml(script)}</textarea><button type="button">Copy workflow</button>`;article.querySelector('button').addEventListener('click',()=>copyText(script));recipesEl.appendChild(article)})}

    function render(){renderCards();renderBuilders();renderRecipes()}
    searchEl.addEventListener('input',renderCards);statusEl.addEventListener('change',renderCards);resetEl.addEventListener('click',()=>{searchEl.value='';statusEl.value='all';renderCards();searchEl.focus()});window.addEventListener('hashchange',()=>{const target=document.querySelector(location.hash);if(target)target.focus()});render();
  </script>
</body>
</html>
"""


def render_workbench(model: WorkbenchModel | None = None) -> str:
    """Render the standalone HTML workbench."""

    model = model or build_model()
    return (
        HTML_TEMPLATE
        .replace("__TITLE__", html.escape(model.app_name))
        .replace("__DESIGN_NOTE__", html.escape(model.design_note))
        .replace("__PAYLOAD__", _json_for_script(model))
    )


def write_workbench(path: str | Path | None = None, model: WorkbenchModel | None = None) -> Path:
    """Write the workbench HTML and return its path."""

    if path is None:
        path = Path(tempfile.gettempdir()) / "d2re_command_center.html"
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_workbench(model), encoding="utf-8")
    return output


def build_parser() -> argparse.ArgumentParser:
    """Build the GUI command parser."""

    parser = argparse.ArgumentParser(
        prog="d2re-gui",
        description="Generate and optionally open the local D2RE Command Center.",
    )
    parser.add_argument("--out", help="Path for the generated standalone HTML file. Defaults to the system temp directory.")
    parser.add_argument("--no-open", action="store_true", help="Write the command center without opening a browser.")
    parser.add_argument("--print-path", action="store_true", help="Print only the generated file path after writing.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point for the local GUI workbench."""

    args = list(argv) if argv is not None else None
    ns = build_parser().parse_args(args)
    output = write_workbench(ns.out)

    if not ns.no_open:
        webbrowser.open(output.as_uri())

    if ns.print_path:
        print(output)
    else:
        print(f"D2RE Command Center written to: {output}")
        if ns.no_open:
            print("Open this file in a browser to use the GUI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
