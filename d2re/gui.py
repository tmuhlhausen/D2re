#!/usr/bin/env python3
"""Local browser workbench for D2RE.

The GUI can run as a standalone command atlas or as a local interactive
workbench. The interactive mode starts a tiny loopback HTTP server that serves
the generated UI and exposes safe command execution endpoints for D2RE modules.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shlex
import subprocess
import sys
import tempfile
import threading
import webbrowser
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class FieldSpec:
    """A UI field that contributes one or more CLI arguments."""

    name: str
    label: str
    kind: str
    placeholder: str = ""
    default: str = ""
    flag: str = ""
    required: bool = False
    help: str = ""
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkbenchAction:
    """One executable D2RE workflow exposed in the GUI."""

    key: str
    title: str
    status: str
    summary: str
    module: str
    detail: str
    tags: tuple[str, ...]
    fields: tuple[FieldSpec, ...]
    fixed_args: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkbenchModel:
    """Serializable data used by the HTML workbench."""

    app_name: str
    version_label: str
    design_note: str
    actions: tuple[WorkbenchAction, ...]


DEFAULT_ACTIONS: tuple[WorkbenchAction, ...] = (
    WorkbenchAction(
        key="parse-save",
        title="Save Codex",
        status="Active",
        summary="Inspect .d2s character files, stats, skills, items, quests, waypoints, and checksum state.",
        module="parse",
        detail="Use this when a character file is the source of truth. JSON mode is ideal for piping into future result viewers.",
        tags=("save", "parser", "d2s", "items"),
        fields=(
            FieldSpec("path", "Save file path", "text", "C:/Users/You/Saved Games/Diablo II/YourChar.d2s", required=True),
            FieldSpec("json", "JSON output", "checkbox", flag="--json", help="Machine-readable output."),
            FieldSpec("items", "Show items", "checkbox", flag="--items", help="Request detailed item output when supported."),
            FieldSpec("verify", "Verify checksum", "checkbox", flag="--verify", help="Check save-file checksum when supported."),
        ),
    ),
    WorkbenchAction(
        key="item-roll",
        title="Item Forge",
        status="Active",
        summary="Run deterministic item-quality experiments and Magic Find simulations.",
        module="roll",
        detail="Use this for seed behavior, item-level assumptions, Magic Find experiments, and affix smoke checks.",
        tags=("item", "rng", "magic-find", "quality"),
        fields=(
            FieldSpec("seed", "Seed", "text", "0xDEADBEEF", flag="--seed"),
            FieldSpec("base", "Base item code", "text", "7cr", flag="--base"),
            FieldSpec("ilvl", "Item level", "number", "85", "85", "--ilvl"),
            FieldSpec("mf", "Magic Find", "number", "300", "300", "--mf"),
            FieldSpec("runs", "Runs", "number", "10000", "10000", "--runs"),
            FieldSpec("affix", "Roll magic affixes", "checkbox", flag="--affix"),
        ),
    ),
    WorkbenchAction(
        key="treasure-class",
        title="Treasure Labyrinth",
        status="Active",
        summary="Walk Treasure Class trees and resolve terminal drops after extracting tc_tree.json.",
        module="tc",
        detail="Use this to explain drop possibility chains and inspect TC recursion without hand-editing shell commands.",
        tags=("treasure-class", "drops", "tc", "loot"),
        fields=(
            FieldSpec("tc", "Treasure Class", "text", "Act 5 Super C", "Act 5 Super C", "--tc", True),
            FieldSpec("top", "Top results", "number", "25", "25", "--top"),
            FieldSpec("resolve", "Resolve recursively", "checkbox", flag="--resolve", default="true"),
            FieldSpec("json", "JSON output", "checkbox", flag="--json"),
        ),
    ),
    WorkbenchAction(
        key="drop-oracle",
        title="Drop Oracle",
        status="Active",
        summary="Estimate target drop odds through Monte Carlo simulation.",
        module="drops",
        detail="Best for target farming comparisons, confidence estimates, and high-volume simulation runs.",
        tags=("monte-carlo", "odds", "drop-rate", "simulation"),
        fields=(
            FieldSpec("tc", "Treasure Class", "text", "Mephisto (N)", "Mephisto (N)", "--tc", True),
            FieldSpec("item", "Target item/code", "text", "weap87", "weap87", "--item"),
            FieldSpec("runs", "Runs", "number", "250000", "250000", "--runs"),
            FieldSpec("mf", "Magic Find", "number", "300", "300", "--mf"),
            FieldSpec("json", "JSON output", "checkbox", flag="--json"),
        ),
    ),
    WorkbenchAction(
        key="map-observatory",
        title="Map Observatory",
        status="Active",
        summary="Inspect seeds, derive level seeds, and visualize predicted map layouts.",
        module="map",
        detail="Use this for seed archaeology, route research, and predicted layout checks.",
        tags=("map", "seed", "drlg", "ascii"),
        fields=(
            FieldSpec("seed", "Map seed", "text", "0x3F7A1B2C", "0x3F7A1B2C", "--seed"),
            FieldSpec("d2s", "Save file path", "text", "Optional .d2s path", flag="--d2s"),
            FieldSpec("level", "Level ID", "number", "21", "21", "--level"),
            FieldSpec("ascii", "Render ASCII", "checkbox", flag="--ascii", default="true"),
            FieldSpec("rooms", "List rooms", "checkbox", flag="--rooms"),
        ),
    ),
    WorkbenchAction(
        key="packet-timeline",
        title="Packet Timeline",
        status="Active",
        summary="Decode known D2 packet commands and inspect demo traffic without a live capture.",
        module="sniff",
        detail="Demo mode is the safe baseline. Live capture remains an advanced terminal workflow because it may require admin privileges.",
        tags=("packet", "network", "sniffer", "protocol"),
        fields=(
            FieldSpec("demo", "Demo mode", "checkbox", flag="--demo", default="true"),
            FieldSpec("verbose", "Verbose annotations", "checkbox", flag="--verbose", default="true"),
            FieldSpec("list", "List known packets", "checkbox", flag="--list"),
            FieldSpec("filter", "Command byte filter", "text", "0x0F", flag="--filter"),
        ),
    ),
    WorkbenchAction(
        key="data-excavator",
        title="Data Excavator",
        status="Active",
        summary="Extract MPQ or CASC data tables into local analysis files.",
        module="extract",
        detail="This is the gateway for table-backed analysis. D2RE never ships game data, so users supply their own local install paths.",
        tags=("mpq", "casc", "tables", "extract"),
        fields=(
            FieldSpec("all_mpqs", "Diablo II install path", "text", "C:/Diablo II/", flag="--all-mpqs"),
            FieldSpec("out", "Output directory", "text", "./data_tables/", "./data_tables/", "--out"),
            FieldSpec("table", "Single table", "text", "weapons", flag="--table"),
            FieldSpec("csv", "CSV output", "checkbox", flag="--csv"),
            FieldSpec("tc_tree", "Build TC tree", "checkbox", flag="--tc-tree"),
        ),
    ),
    WorkbenchAction(
        key="doctor",
        title="Repository Doctor",
        status="Planned",
        summary="Future environment self-check for Python, optional dependencies, paths, and data-table readiness.",
        module="doctor",
        detail="Visible by design, but still disabled until diagnostic checks are implemented and tested.",
        tags=("doctor", "health", "planned", "diagnostics"),
        fields=(),
    ),
)

MODULES: dict[str, tuple[str, str]] = {
    "parse": ("scripts.d2s_parser", "d2s_parser.py"),
    "roll": ("scripts.item_roller", "item_roller.py"),
    "extract": ("scripts.mpq_extract", "mpq_extract.py"),
    "sniff": ("scripts.packet_sniffer", "packet_sniffer.py"),
    "map": ("scripts.map_seed_tool", "map_seed_tool.py"),
    "tc": ("scripts.tc_explorer", "tc_explorer.py"),
    "drops": ("scripts.drop_calculator", "drop_calculator.py"),
}


def build_model() -> WorkbenchModel:
    """Return the workbench model."""

    return WorkbenchModel(
        app_name="D2RE Visual Workbench",
        version_label="Integrated command workbench",
        design_note=(
            "Local, accessible browser interface with integrated command builders, "
            "safe loopback execution, dark gothic panels, responsive layouts, and reduced-motion support."
        ),
        actions=DEFAULT_ACTIONS,
    )


def _json_for_script(model: WorkbenchModel) -> str:
    raw = json.dumps(asdict(model), ensure_ascii=False, indent=2)
    return raw.replace("</", "<\\/")


def action_by_key(key: str) -> WorkbenchAction | None:
    """Find an action by key."""

    return next((action for action in DEFAULT_ACTIONS if action.key == key), None)


def build_command(action: WorkbenchAction, values: Mapping[str, Any]) -> list[str]:
    """Build a module argv from trusted action metadata and untrusted form values."""

    if action.module not in MODULES:
        raise ValueError(f"Action '{action.key}' is not executable yet.")

    argv: list[str] = list(action.fixed_args)
    for field in action.fields:
        raw = values.get(field.name)
        if field.kind == "checkbox":
            enabled = raw is True or raw == "true" or raw == "on" or raw == "1"
            if enabled and field.flag:
                argv.append(field.flag)
            continue

        value = "" if raw is None else str(raw).strip()
        if field.required and not value:
            raise ValueError(f"Missing required field: {field.label}")
        if not value:
            continue
        if field.flag:
            argv.extend([field.flag, value])
        else:
            argv.append(value)
    return argv


def format_command(action: WorkbenchAction, argv: list[str]) -> str:
    """Return a copyable shell command for a built action."""

    return " ".join(shlex.quote(part) for part in ["d2re", action.module, *argv])


def run_action(key: str, values: Mapping[str, Any], timeout: int = 30) -> dict[str, Any]:
    """Run an action through the current Python interpreter."""

    action = action_by_key(key)
    if action is None:
        raise ValueError(f"Unknown action: {key}")
    argv = build_command(action, values)
    module_name, prog_name = MODULES[action.module]
    command = [sys.executable, "-m", module_name, *argv]
    completed = subprocess.run(
        command,
        cwd=os.getcwd(),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "action": key,
        "command": format_command(action, argv),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def render_workbench(model: WorkbenchModel | None = None, server_mode: bool = False) -> str:
    """Render the standalone HTML workbench."""

    model = model or build_model()
    payload = _json_for_script(model)
    title = html.escape(model.app_name)
    design_note = html.escape(model.design_note)
    server_note = "Interactive runner enabled" if server_mode else "Static command-builder mode"
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <style>
    :root {{ color-scheme: dark; --obsidian:#090706; --obsidian-2:#120d0c; --iron:#342824; --blood:#d13b32; --blood-2:#a92923; --ember:#f09a4a; --parchment:#f7ead0; --muted:#bba88d; --panel:rgba(20,14,12,.9); --panel-2:rgba(33,23,19,.96); --line:rgba(231,215,189,.2); --line-hot:rgba(209,59,50,.42); --focus:#ffd28a; --radius:20px; --control:12px; --shadow:0 18px 60px rgba(0,0,0,.42); --glow:0 0 32px rgba(209,59,50,.22); --font-body:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif; --font-display:Georgia,\"Times New Roman\",serif; --font-mono:\"SFMono-Regular\",Consolas,monospace; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; background:radial-gradient(circle at top left,rgba(209,59,50,.18),transparent 34rem),linear-gradient(135deg,var(--obsidian),var(--obsidian-2) 55%,#050403); color:var(--parchment); font-family:var(--font-body); line-height:1.55; }}
    body::before {{ content:\"\"; position:fixed; inset:0; pointer-events:none; background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px); background-size:44px 44px; mask-image:radial-gradient(circle at center,black,transparent 80%); }}
    .skip-link {{ position:absolute; left:1rem; top:-4rem; z-index:10; padding:.75rem 1rem; border-radius:var(--control); background:var(--parchment); color:var(--obsidian); }}
    .skip-link:focus {{ top:1rem; }}
    :focus-visible {{ outline:3px solid var(--focus); outline-offset:3px; }}
    .shell {{ width:min(1440px,100%); margin:0 auto; padding:clamp(1rem,2vw,2rem); }}
    .panel {{ position:relative; overflow:hidden; border:1px solid var(--line); border-radius:var(--radius); background:var(--panel); box-shadow:var(--shadow); }}
    .panel::before {{ content:\"\"; position:absolute; inset:0; pointer-events:none; background:linear-gradient(135deg,rgba(247,234,208,.11),transparent 18%,rgba(209,59,50,.08)); }}
    .hero {{ display:grid; grid-template-columns:minmax(0,1.25fr) minmax(280px,.75fr); gap:1.5rem; margin-bottom:1.5rem; }}
    .hero-main {{ padding:clamp(1.5rem,4vw,4rem); }}
    .hero-side {{ display:grid; gap:1rem; padding:1.25rem; background:var(--panel-2); }}
    .eyebrow {{ display:inline-flex; align-items:center; min-height:44px; color:var(--ember); letter-spacing:.16em; text-transform:uppercase; font-size:.78rem; font-weight:800; }}
    h1,h2,h3 {{ margin:0; font-family:var(--font-display); line-height:1.05; }}
    h1 {{ max-width:13ch; margin-top:.75rem; font-size:clamp(2.75rem,8vw,6.8rem); letter-spacing:-.06em; }}
    .hero-copy,.muted {{ color:var(--muted); }}
    .stat-card {{ min-height:44px; padding:1rem; border:1px solid var(--line); border-radius:16px; background:linear-gradient(180deg,rgba(247,234,208,.1),rgba(247,234,208,.035)); }}
    .toolbar {{ display:grid; grid-template-columns:minmax(220px,1fr) auto auto; gap:.75rem; align-items:end; margin-bottom:1.5rem; padding:1rem; }}
    label {{ display:grid; gap:.5rem; font-weight:700; }}
    input,select,button,textarea {{ min-height:44px; border-radius:var(--control); border:1px solid var(--line); font:inherit; }}
    input,select,textarea {{ width:100%; padding:.65rem 1rem; background:rgba(0,0,0,.26); color:var(--parchment); }}
    button {{ cursor:pointer; padding:0 1rem; background:linear-gradient(180deg,rgba(209,59,50,.95),rgba(118,25,22,.96)); color:var(--parchment); font-weight:800; box-shadow:var(--glow); }}
    button.secondary {{ background:rgba(247,234,208,.08); box-shadow:none; }}
    .layout {{ display:grid; grid-template-columns:280px minmax(0,1fr); gap:1.5rem; align-items:start; }}
    .nav-panel {{ position:sticky; top:1rem; padding:1rem; }}
    .module-list,.cards {{ display:grid; gap:.75rem; }}
    .cards {{ gap:1.25rem; }}
    .module-link {{ display:flex; justify-content:space-between; gap:.75rem; min-height:44px; padding:.75rem; border:1px solid transparent; border-radius:var(--control); color:var(--parchment); text-decoration:none; }}
    .module-link:hover {{ border-color:var(--line-hot); background:rgba(209,59,50,.12); }}
    .card {{ display:grid; gap:1rem; padding:1.25rem; }}
    .card-header {{ display:flex; justify-content:space-between; gap:1rem; align-items:start; }}
    .card h3 {{ font-size:clamp(1.45rem,3vw,2.3rem); }}
    .status {{ display:inline-flex; align-items:center; min-height:32px; padding:0 .75rem; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:.84rem; font-weight:800; white-space:nowrap; }}
    .status[data-status=\"Active\"] {{ border-color:rgba(240,154,74,.55); color:var(--ember); }}
    .form-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.75rem; }}
    .check-row {{ display:flex; align-items:center; gap:.6rem; min-height:44px; }}
    .check-row input {{ width:auto; min-height:auto; }}
    .command-row,.output {{ display:grid; gap:.75rem; padding:.75rem; border:1px solid var(--line); border-radius:16px; background:rgba(0,0,0,.28); }}
    .command-actions {{ display:flex; flex-wrap:wrap; gap:.75rem; }}
    code,pre {{ color:var(--parchment); font-family:var(--font-mono); overflow-wrap:anywhere; }}
    pre {{ white-space:pre-wrap; margin:0; max-height:24rem; overflow:auto; }}
    .tag-list {{ display:flex; flex-wrap:wrap; gap:.5rem; padding:0; margin:0; list-style:none; }}
    .tag-list li {{ padding:.2rem .55rem; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:.84rem; }}
    .toast {{ position:fixed; right:1rem; bottom:1rem; max-width:min(420px,calc(100vw - 2rem)); padding:1rem; border:1px solid var(--line-hot); border-radius:var(--control); background:var(--panel-2); box-shadow:var(--shadow); transform:translateY(140%); transition:transform 180ms ease; }}
    .toast[data-visible=\"true\"] {{ transform:translateY(0); }}
    .empty {{ display:none; padding:1.5rem; text-align:center; color:var(--muted); }} .empty[data-visible=\"true\"] {{ display:block; }}
    @media (max-width:920px) {{ .hero,.layout,.toolbar,.form-grid {{ grid-template-columns:1fr; }} .nav-panel {{ position:static; }} }}
    @media (max-width:560px) {{ .shell {{ padding:.75rem; }} .card-header {{ display:grid; }} button {{ width:100%; }} }}
    @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ scroll-behavior:auto!important; transition-duration:.001ms!important; animation-duration:.001ms!important; animation-iteration-count:1!important; }} }}
  </style>
</head>
<body>
  <a class=\"skip-link\" href=\"#workbench\">Skip to workbench modules</a>
  <div class=\"shell\">
    <header class=\"hero\" aria-labelledby=\"page-title\">
      <section class=\"panel hero-main\"><div class=\"eyebrow\">D2RE interface layer</div><h1 id=\"page-title\">Visual Workbench</h1><p class=\"hero-copy\">{design_note}</p></section>
      <aside class=\"panel hero-side\" aria-label=\"Workbench principles\"><div class=\"stat-card\"><strong>{server_note}</strong><br><span class=\"muted\">Build commands, copy them, and run supported workflows locally.</span></div><div class=\"stat-card\"><strong>Guardrailed execution</strong><br><span class=\"muted\">Only predefined D2RE modules can run. Free-form shell input is not accepted.</span></div><div class=\"stat-card\"><strong>Token driven</strong><br><span class=\"muted\">Dark panels, focus rings, spacing, and responsive controls share one visual system.</span></div></aside>
    </header>
    <section class=\"panel toolbar\" aria-label=\"Workbench controls\"><label for=\"search\">Search modules<input id=\"search\" type=\"search\" autocomplete=\"off\" placeholder=\"Try save, item, packet, map, tc\" /></label><label for=\"status\">Status<select id=\"status\"><option value=\"all\">All modules</option><option value=\"Active\">Active</option><option value=\"Planned\">Planned</option></select></label><button class=\"secondary\" type=\"button\" id=\"reset\">Reset filters</button></section>
    <main class=\"layout\" id=\"workbench\"><nav class=\"panel nav-panel\" aria-label=\"Workbench module navigation\"><h2>Modules</h2><div class=\"module-list\" id=\"module-list\"></div></nav><section class=\"cards\" id=\"cards\" aria-label=\"Workbench modules\"></section></main>
    <p class=\"empty\" id=\"empty\" data-visible=\"false\">No modules match the current filters.</p>
  </div>
  <div class=\"toast\" id=\"toast\" role=\"status\" aria-live=\"polite\"></div>
  <script id=\"workbench-data\" type=\"application/json\">{payload}</script>
  <script>
    const model = JSON.parse(document.getElementById('workbench-data').textContent);
    const serverMode = {str(server_mode).lower()};
    const cardsEl = document.getElementById('cards');
    const navEl = document.getElementById('module-list');
    const searchEl = document.getElementById('search');
    const statusEl = document.getElementById('status');
    const emptyEl = document.getElementById('empty');
    const toastEl = document.getElementById('toast');
    const resetEl = document.getElementById('reset');
    const outputs = new Map();
    function slugify(value) {{ return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''); }}
    function escapeHtml(value) {{ return String(value).replace(/[&<>\"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}})[c]); }}
    function matches(action) {{ const needle = searchEl.value.trim().toLowerCase(); const status = statusEl.value; const haystack = [action.title, action.status, action.summary, action.module, action.detail, ...action.tags].join(' ').toLowerCase(); return (status === 'all' || action.status === status) && (!needle || haystack.includes(needle)); }}
    function showToast(message) {{ toastEl.textContent = message; toastEl.dataset.visible = 'true'; clearTimeout(showToast.timeout); showToast.timeout = setTimeout(() => toastEl.dataset.visible = 'false', 2200); }}
    function fieldValue(form, field) {{ const el = form.elements[field.name]; if (!el) return ''; return field.kind === 'checkbox' ? el.checked : el.value; }}
    function buildPayload(action, form) {{ const values = {{}}; action.fields.forEach(field => values[field.name] = fieldValue(form, field)); return {{ action: action.key, values }}; }}
    function buildCommand(action, form) {{ const values = buildPayload(action, form).values; const parts = ['d2re', action.module]; action.fields.forEach(field => {{ const value = values[field.name]; if (field.kind === 'checkbox') {{ if (value && field.flag) parts.push(field.flag); return; }} if (!String(value || '').trim()) return; if (field.flag) parts.push(field.flag, String(value).trim()); else parts.push(String(value).trim()); }}); return parts.map(part => /\s|\"|'/.test(part) ? JSON.stringify(part) : part).join(' '); }}
    async function copyText(text) {{ try {{ await navigator.clipboard.writeText(text); showToast('Copied to clipboard.'); }} catch {{ showToast('Copy failed. Select the text manually.'); }} }}
    async function runAction(action, form, outputEl, commandEl) {{ if (!serverMode) {{ showToast('Open with d2re gui to enable running commands.'); return; }} outputEl.textContent = 'Running...'; const response = await fetch('/api/run', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(buildPayload(action, form)) }}); const data = await response.json(); commandEl.textContent = data.command || buildCommand(action, form); outputEl.textContent = `return code: ${{data.returncode}}\n\nSTDOUT\n${{data.stdout || ''}}\nSTDERR\n${{data.stderr || ''}}`; if (!response.ok || data.error) outputEl.textContent = data.error || outputEl.textContent; }}
    function renderField(field) {{ const id = `field-${{field.name}}-${{Math.random().toString(16).slice(2)}}`; if (field.kind === 'checkbox') return `<label class=\"check-row\"><input name=\"${{escapeHtml(field.name)}}\" type=\"checkbox\" ${{field.default === 'true' ? 'checked' : ''}} /> <span>${{escapeHtml(field.label)}}</span></label>`; const type = field.kind === 'number' ? 'number' : 'text'; return `<label for=\"${{id}}\">${{escapeHtml(field.label)}}<input id=\"${{id}}\" name=\"${{escapeHtml(field.name)}}\" type=\"${{type}}\" placeholder=\"${{escapeHtml(field.placeholder)}}\" value=\"${{escapeHtml(field.default || '')}}\" ${{field.required ? 'required' : ''}} /></label>`; }}
    function render() {{ const visible = model.actions.filter(matches); cardsEl.innerHTML = ''; navEl.innerHTML = ''; emptyEl.dataset.visible = String(visible.length === 0); visible.forEach((action, index) => {{ const id = slugify(action.title); const nav = document.createElement('a'); nav.className = 'module-link'; nav.href = `#${{id}}`; nav.innerHTML = `<span>${{escapeHtml(action.title)}}</span><span>${{escapeHtml(action.status)}}</span>`; navEl.appendChild(nav); const article = document.createElement('article'); article.className = 'panel card'; article.id = id; article.tabIndex = -1; article.innerHTML = `<div class=\"card-header\"><div><p class=\"eyebrow\">Module ${{index + 1}}</p><h3>${{escapeHtml(action.title)}}</h3></div><span class=\"status\" data-status=\"${{escapeHtml(action.status)}}\">${{escapeHtml(action.status)}}</span></div><p class=\"muted\">${{escapeHtml(action.summary)}}</p><form class=\"form-grid\">${{action.fields.map(renderField).join('')}}</form><div class=\"command-row\"><code></code><div class=\"command-actions\"><button type=\"button\" class=\"copy\">Copy command</button><button type=\"button\" class=\"run\" ${{action.status !== 'Active' ? 'disabled' : ''}}>Run</button></div></div><details><summary>When to use this module</summary><p>${{escapeHtml(action.detail)}}</p></details><ul class=\"tag-list\">${{action.tags.map(tag => `<li>${{escapeHtml(tag)}}</li>`).join('')}}</ul><div class=\"output\"><strong>Output</strong><pre aria-live=\"polite\">${{outputs.get(action.key) || 'No output yet.'}}</pre></div>`; const form = article.querySelector('form'); const commandEl = article.querySelector('code'); const outputEl = article.querySelector('pre'); const update = () => commandEl.textContent = buildCommand(action, form); form.addEventListener('input', update); article.querySelector('.copy').addEventListener('click', () => copyText(commandEl.textContent)); article.querySelector('.run').addEventListener('click', () => runAction(action, form, outputEl, commandEl)); update(); cardsEl.appendChild(article); }}); }}
    searchEl.addEventListener('input', render); statusEl.addEventListener('change', render); resetEl.addEventListener('click', () => {{ searchEl.value=''; statusEl.value='all'; render(); searchEl.focus(); }}); window.addEventListener('hashchange', () => {{ const target = document.querySelector(location.hash); if (target) target.focus(); }}); render();
  </script>
</body>
</html>
"""


def write_workbench(path: str | Path | None = None, model: WorkbenchModel | None = None, server_mode: bool = False) -> Path:
    """Write the workbench HTML and return its path."""

    if path is None:
        path = Path(tempfile.gettempdir()) / "d2re_visual_workbench.html"
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_workbench(model, server_mode=server_mode), encoding="utf-8")
    return output


class WorkbenchRequestHandler(BaseHTTPRequestHandler):
    """Tiny loopback-only HTTP handler for the interactive GUI."""

    server_version = "D2REWorkbench/1.0"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib hook name
        if self.path not in ("/", "/index.html"):
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        body = render_workbench(server_mode=True).encode("utf-8")
        self._send(200, body, "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802 - stdlib hook name
        if self.path != "/api/run":
            self._send(404, b'{"error":"Not found"}', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            result = run_action(str(payload.get("action", "")), payload.get("values") or {})
            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
        except Exception as exc:  # pragma: no cover - defensive server boundary
            body = json.dumps({"error": str(exc), "returncode": 1}, ensure_ascii=False).encode("utf-8")
            self._send(400, body, "application/json; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        return


def serve_workbench(host: str = "127.0.0.1", port: int = 0, open_browser: bool = True) -> tuple[ThreadingHTTPServer, str]:
    """Start the local interactive workbench server."""

    server = ThreadingHTTPServer((host, port), WorkbenchRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_host, actual_port = server.server_address[:2]
    url = f"http://{actual_host}:{actual_port}/"
    if open_browser:
        webbrowser.open(url)
    return server, url


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="d2re-gui", description="Open the local D2RE Visual Workbench.")
    parser.add_argument("--out", help="Write standalone HTML to this path instead of running the interactive local server.")
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser automatically.")
    parser.add_argument("--print-path", action="store_true", help="Print the generated path or local URL.")
    parser.add_argument("--static", action="store_true", help="Generate static HTML instead of starting the local action server.")
    parser.add_argument("--port", type=int, default=0, help="Port for the local action server. Defaults to an available port.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = list(argv) if argv is not None else None
    ns = build_parser().parse_args(args)

    if ns.static or ns.out:
        output = write_workbench(ns.out, server_mode=False)
        if not ns.no_open:
            webbrowser.open(output.as_uri())
        print(output if ns.print_path else f"D2RE Visual Workbench written to: {output}")
        if ns.no_open and not ns.print_path:
            print("Open this file in a browser to use the static GUI.")
        return 0

    server, url = serve_workbench(port=ns.port, open_browser=not ns.no_open)
    print(url if ns.print_path else f"D2RE Visual Workbench running at: {url}")
    if ns.no_open:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
