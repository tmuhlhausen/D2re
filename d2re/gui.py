#!/usr/bin/env python3
"""Local browser workbench for D2RE.

The first GUI slice is intentionally static and read-only. It gives users a
visual launchpad for the existing toolkit without introducing a web framework,
background service, or unsafe file mutation path.
"""

from __future__ import annotations

import argparse
import html
import json
import tempfile
import webbrowser
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class WorkbenchCard:
    """One visible workbench module."""

    title: str
    status: str
    summary: str
    command: str
    detail: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class WorkbenchModel:
    """Serializable data used by the HTML workbench."""

    app_name: str
    version_label: str
    design_note: str
    cards: tuple[WorkbenchCard, ...]


DEFAULT_CARDS: tuple[WorkbenchCard, ...] = (
    WorkbenchCard(
        title="Save Codex",
        status="Active",
        summary="Inspect .d2s character files, stats, skills, items, quests, waypoints, and checksum state.",
        command="d2re parse MyChar.d2s --json",
        detail="Use this pane when a character file is the source of truth. Start in JSON mode when another tool needs stable output, then compare against references/d2s-format.md for field-level investigation.",
        tags=("save", "parser", "d2s", "items"),
    ),
    WorkbenchCard(
        title="Item Forge",
        status="Active",
        summary="Run deterministic item-quality experiments and Magic Find simulations.",
        command="d2re roll --seed 0xDEADBEEF --ilvl 85 --mf 300",
        detail="This is the fast lane for testing seed behavior, item level assumptions, and quality distribution changes before deeper Treasure Class work.",
        tags=("item", "rng", "magic-find", "quality"),
    ),
    WorkbenchCard(
        title="Treasure Labyrinth",
        status="Active",
        summary="Walk Treasure Class trees and resolve terminal drops after extracting tc_tree.json.",
        command="d2re tc --tc \"Act 5 Super C\" --resolve --top 25",
        detail="Use this view to explain why a drop can happen, where recursion enters another TC, and which terminal codes dominate the output.",
        tags=("treasure-class", "drops", "tc", "loot"),
    ),
    WorkbenchCard(
        title="Drop Oracle",
        status="Active",
        summary="Estimate target drop odds through Monte Carlo simulation.",
        command="d2re drops --tc \"Mephisto (N)\" --item weap87 --runs 250000",
        detail="Best for practical questions like target farming, confidence estimates, and comparing high-volume runs with different assumptions.",
        tags=("monte-carlo", "odds", "drop-rate", "simulation"),
    ),
    WorkbenchCard(
        title="Map Observatory",
        status="Active",
        summary="Inspect seeds, derive level seeds, and visualize predicted map layouts.",
        command="d2re map --seed 0x3F7A1B2C --level 21 --ascii",
        detail="Use this pane for seed archaeology, route research, and checking whether a predicted layout is plausible before writing deeper map tooling.",
        tags=("map", "seed", "drlg", "ascii"),
    ),
    WorkbenchCard(
        title="Packet Timeline",
        status="Active",
        summary="Decode known D2 packet commands and inspect demo traffic without a live capture.",
        command="d2re sniff --demo --verbose",
        detail="Start with demo mode for a safe baseline. Live capture can require admin privileges and platform-specific packet capture support.",
        tags=("packet", "network", "sniffer", "protocol"),
    ),
    WorkbenchCard(
        title="Data Excavator",
        status="Active",
        summary="Extract MPQ or CASC data tables into local analysis files.",
        command="d2re extract --all-mpqs \"C:/Diablo II/\" --out ./data_tables/",
        detail="This is the gateway for table-backed analysis. D2RE never ships game data, so users supply their own local installation paths.",
        tags=("mpq", "casc", "tables", "extract"),
    ),
    WorkbenchCard(
        title="Repository Doctor",
        status="Planned",
        summary="Future environment self-check for Python, optional dependencies, paths, and data-table readiness.",
        command="d2re doctor",
        detail="Visible by design, but still disabled until the diagnostic checks are implemented and tested.",
        tags=("doctor", "health", "planned", "diagnostics"),
    ),
)


def build_model() -> WorkbenchModel:
    """Return the static workbench model."""

    return WorkbenchModel(
        app_name="D2RE Visual Workbench",
        version_label="First GUI slice",
        design_note=(
            "Local, read-only, accessible browser interface using a dark gothic "
            "token system, responsive panels, keyboard-friendly controls, and reduced-motion support."
        ),
        cards=DEFAULT_CARDS,
    )


def _json_for_script(model: WorkbenchModel) -> str:
    """Serialize model data safely for embedding in a script tag."""

    raw = json.dumps(asdict(model), ensure_ascii=False, indent=2)
    return raw.replace("</", "<\\/")


def render_workbench(model: WorkbenchModel | None = None) -> str:
    """Render the standalone HTML workbench."""

    model = model or build_model()
    payload = _json_for_script(model)
    title = html.escape(model.app_name)
    design_note = html.escape(model.design_note)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: dark;
      --primitive-obsidian-950: #090706;
      --primitive-obsidian-900: #120d0c;
      --primitive-iron-800: #241b18;
      --primitive-iron-700: #342824;
      --primitive-iron-600: #5b4942;
      --primitive-blood-600: #a92923;
      --primitive-blood-500: #d13b32;
      --primitive-ember-400: #f09a4a;
      --primitive-parchment-200: #e7d7bd;
      --primitive-parchment-100: #f7ead0;
      --primitive-muted-300: #bba88d;
      --surface-page: radial-gradient(circle at top left, rgba(209, 59, 50, 0.18), transparent 34rem), linear-gradient(135deg, var(--primitive-obsidian-950), var(--primitive-obsidian-900) 55%, #050403);
      --surface-panel: rgba(20, 14, 12, 0.88);
      --surface-panel-strong: rgba(33, 23, 19, 0.96);
      --surface-parchment: linear-gradient(180deg, rgba(247, 234, 208, 0.10), rgba(247, 234, 208, 0.035));
      --border-metal: rgba(231, 215, 189, 0.20);
      --border-blood: rgba(209, 59, 50, 0.42);
      --text-primary: var(--primitive-parchment-100);
      --text-secondary: var(--primitive-muted-300);
      --text-danger: #ffb1aa;
      --accent: var(--primitive-blood-500);
      --accent-hot: var(--primitive-ember-400);
      --focus: #ffd28a;
      --radius-panel: 20px;
      --radius-control: 12px;
      --shadow-glow: 0 0 32px rgba(209, 59, 50, 0.22);
      --shadow-panel: 0 18px 60px rgba(0, 0, 0, 0.42);
      --space-1: 0.25rem;
      --space-2: 0.5rem;
      --space-3: 0.75rem;
      --space-4: 1rem;
      --space-5: 1.25rem;
      --space-6: 1.5rem;
      --space-8: 2rem;
      --font-display: Georgia, \"Times New Roman\", serif;
      --font-body: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
      --font-mono: \"SFMono-Regular\", Consolas, \"Liberation Mono\", monospace;
    }}

    * {{ box-sizing: border-box; }}

    html {{ scroll-behavior: smooth; }}

    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--surface-page);
      color: var(--text-primary);
      font-family: var(--font-body);
      font-size: 16px;
      line-height: 1.55;
    }}

    body::before {{
      content: \"\";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image: linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
      background-size: 44px 44px;
      mask-image: radial-gradient(circle at center, black, transparent 80%);
    }}

    a {{ color: var(--primitive-parchment-100); }}

    .skip-link {{
      position: absolute;
      left: var(--space-4);
      top: -4rem;
      z-index: 10;
      padding: var(--space-3) var(--space-4);
      border-radius: var(--radius-control);
      background: var(--primitive-parchment-100);
      color: var(--primitive-obsidian-950);
      transition: top 160ms ease;
    }}

    .skip-link:focus {{ top: var(--space-4); }}

    :focus-visible {{
      outline: 3px solid var(--focus);
      outline-offset: 3px;
    }}

    .shell {{
      width: min(1440px, 100%);
      margin: 0 auto;
      padding: clamp(1rem, 2vw, 2rem);
    }}

    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
      gap: var(--space-6);
      align-items: stretch;
      margin-bottom: var(--space-6);
    }}

    .panel {{
      position: relative;
      overflow: hidden;
      border: 1px solid var(--border-metal);
      border-radius: var(--radius-panel);
      background: var(--surface-panel);
      box-shadow: var(--shadow-panel);
    }}

    .panel::before {{
      content: \"\";
      position: absolute;
      inset: 0;
      pointer-events: none;
      border-radius: inherit;
      background: linear-gradient(135deg, rgba(247, 234, 208, 0.11), transparent 18%, rgba(209, 59, 50, 0.08));
    }}

    .hero-main {{ padding: clamp(1.5rem, 4vw, 4rem); }}

    .eyebrow {{
      display: inline-flex;
      align-items: center;
      min-height: 44px;
      gap: var(--space-2);
      color: var(--accent-hot);
      letter-spacing: 0.16em;
      text-transform: uppercase;
      font-size: 0.78rem;
      font-weight: 800;
    }}

    h1, h2, h3 {{
      margin: 0;
      font-family: var(--font-display);
      line-height: 1.05;
    }}

    h1 {{
      max-width: 13ch;
      margin-top: var(--space-3);
      font-size: clamp(2.75rem, 8vw, 6.8rem);
      letter-spacing: -0.06em;
    }}

    .hero-copy {{
      max-width: 68ch;
      margin: var(--space-5) 0 0;
      color: var(--text-secondary);
      font-size: clamp(1rem, 1.4vw, 1.2rem);
    }}

    .hero-side {{
      display: grid;
      gap: var(--space-4);
      padding: var(--space-5);
      background: var(--surface-panel-strong);
    }}

    .stat-card {{
      min-height: 44px;
      padding: var(--space-4);
      border: 1px solid var(--border-metal);
      border-radius: 16px;
      background: var(--surface-parchment);
    }}

    .stat-card strong {{
      display: block;
      margin-bottom: var(--space-1);
      color: var(--primitive-parchment-100);
    }}

    .stat-card span {{ color: var(--text-secondary); }}

    .toolbar {{
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto auto;
      gap: var(--space-3);
      align-items: center;
      margin-bottom: var(--space-6);
      padding: var(--space-4);
    }}

    label {{
      display: grid;
      gap: var(--space-2);
      font-weight: 700;
      color: var(--primitive-parchment-100);
    }}

    input, select, button {{
      min-height: 44px;
      border-radius: var(--radius-control);
      border: 1px solid var(--border-metal);
      font: inherit;
    }}

    input, select {{
      width: 100%;
      padding: 0 var(--space-4);
      background: rgba(0, 0, 0, 0.26);
      color: var(--text-primary);
    }}

    button {{
      cursor: pointer;
      padding: 0 var(--space-4);
      background: linear-gradient(180deg, rgba(209, 59, 50, 0.95), rgba(118, 25, 22, 0.96));
      color: var(--primitive-parchment-100);
      font-weight: 800;
      box-shadow: var(--shadow-glow);
    }}

    button.secondary {{
      background: rgba(247, 234, 208, 0.08);
      color: var(--primitive-parchment-100);
      box-shadow: none;
    }}

    .layout {{
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      gap: var(--space-6);
      align-items: start;
    }}

    .nav-panel {{
      position: sticky;
      top: var(--space-4);
      padding: var(--space-4);
    }}

    .nav-panel h2 {{ font-size: 1.35rem; }}

    .module-list {{
      display: grid;
      gap: var(--space-2);
      margin-top: var(--space-4);
    }}

    .module-link {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: var(--space-3);
      min-height: 44px;
      padding: var(--space-3);
      border: 1px solid transparent;
      border-radius: var(--radius-control);
      color: var(--text-primary);
      text-decoration: none;
    }}

    .module-link:hover, .module-link[aria-current=\"true\"] {{
      border-color: var(--border-blood);
      background: rgba(209, 59, 50, 0.12);
    }}

    .cards {{
      display: grid;
      gap: var(--space-5);
    }}

    .card {{
      display: grid;
      gap: var(--space-4);
      padding: var(--space-5);
    }}

    .card-header {{
      display: flex;
      justify-content: space-between;
      gap: var(--space-4);
      align-items: start;
    }}

    .card h3 {{ font-size: clamp(1.45rem, 3vw, 2.3rem); }}

    .status {{
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 0 var(--space-3);
      border: 1px solid var(--border-metal);
      border-radius: 999px;
      color: var(--text-secondary);
      font-size: 0.84rem;
      font-weight: 800;
      white-space: nowrap;
    }}

    .status[data-status=\"Active\"] {{
      border-color: rgba(240, 154, 74, 0.55);
      color: var(--accent-hot);
    }}

    .status[data-status=\"Planned\"] {{
      border-color: rgba(187, 168, 141, 0.38);
      color: var(--text-secondary);
    }}

    .summary {{
      max-width: 72ch;
      margin: 0;
      color: var(--text-secondary);
    }}

    .command-row {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: var(--space-3);
      align-items: center;
      padding: var(--space-3);
      border: 1px solid var(--border-metal);
      border-radius: 16px;
      background: rgba(0, 0, 0, 0.28);
    }}

    code {{
      color: var(--primitive-parchment-100);
      font-family: var(--font-mono);
      overflow-wrap: anywhere;
    }}

    details {{
      padding: var(--space-4);
      border: 1px solid var(--border-metal);
      border-radius: 16px;
      background: rgba(247, 234, 208, 0.035);
    }}

    summary {{
      min-height: 44px;
      cursor: pointer;
      font-weight: 800;
    }}

    .tag-list {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-2);
      padding: 0;
      margin: 0;
      list-style: none;
    }}

    .tag-list li {{
      padding: 0.2rem 0.55rem;
      border: 1px solid var(--border-metal);
      border-radius: 999px;
      color: var(--text-secondary);
      font-size: 0.84rem;
    }}

    .toast {{
      position: fixed;
      right: var(--space-4);
      bottom: var(--space-4);
      max-width: min(420px, calc(100vw - 2rem));
      padding: var(--space-4);
      border: 1px solid var(--border-blood);
      border-radius: var(--radius-control);
      background: var(--surface-panel-strong);
      color: var(--primitive-parchment-100);
      box-shadow: var(--shadow-panel);
      transform: translateY(140%);
      transition: transform 180ms ease;
    }}

    .toast[data-visible=\"true\"] {{ transform: translateY(0); }}

    .empty {{
      display: none;
      padding: var(--space-6);
      text-align: center;
      color: var(--text-secondary);
    }}

    .empty[data-visible=\"true\"] {{ display: block; }}

    @media (max-width: 920px) {{
      .hero, .layout, .toolbar {{ grid-template-columns: 1fr; }}
      .nav-panel {{ position: static; }}
    }}

    @media (max-width: 560px) {{
      .shell {{ padding: var(--space-3); }}
      .card-header, .command-row {{ grid-template-columns: 1fr; }}
      .card-header {{ display: grid; }}
      button {{ width: 100%; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        scroll-behavior: auto !important;
        transition-duration: 0.001ms !important;
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
      }}
    }}
  </style>
</head>
<body>
  <a class=\"skip-link\" href=\"#workbench\">Skip to workbench modules</a>
  <div class=\"shell\">
    <header class=\"hero\" aria-labelledby=\"page-title\">
      <section class=\"panel hero-main\">
        <div class=\"eyebrow\" aria-label=\"Current release stage\">D2RE interface layer</div>
        <h1 id=\"page-title\">Visual Workbench</h1>
        <p class=\"hero-copy\">{design_note}</p>
      </section>
      <aside class=\"panel hero-side\" aria-label=\"Workbench principles\">
        <div class=\"stat-card\"><strong>Read-only by default</strong><span>Commands are presented for deliberate copy and terminal execution.</span></div>
        <div class=\"stat-card\"><strong>Keyboard ready</strong><span>Tab, search, copy buttons, and focus rings are first-class paths.</span></div>
        <div class=\"stat-card\"><strong>Token driven</strong><span>Colors, spacing, radius, focus, and panels use a shared CSS variable system.</span></div>
      </aside>
    </header>

    <section class=\"panel toolbar\" aria-label=\"Workbench controls\">
      <label for=\"search\">Search modules
        <input id=\"search\" type=\"search\" autocomplete=\"off\" placeholder=\"Try save, item, packet, map, tc\" />
      </label>
      <label for=\"status\">Status
        <select id=\"status\">
          <option value=\"all\">All modules</option>
          <option value=\"Active\">Active</option>
          <option value=\"Planned\">Planned</option>
        </select>
      </label>
      <button class=\"secondary\" type=\"button\" id=\"reset\">Reset filters</button>
    </section>

    <main class=\"layout\" id=\"workbench\">
      <nav class=\"panel nav-panel\" aria-label=\"Workbench module navigation\">
        <h2>Modules</h2>
        <div class=\"module-list\" id=\"module-list\"></div>
      </nav>
      <section class=\"cards\" id=\"cards\" aria-label=\"Workbench modules\"></section>
    </main>
    <p class=\"empty\" id=\"empty\" data-visible=\"false\">No modules match the current filters.</p>
  </div>
  <div class=\"toast\" id=\"toast\" role=\"status\" aria-live=\"polite\"></div>

  <script id=\"workbench-data\" type=\"application/json\">{payload}</script>
  <script>
    const model = JSON.parse(document.getElementById('workbench-data').textContent);
    const cardsEl = document.getElementById('cards');
    const navEl = document.getElementById('module-list');
    const searchEl = document.getElementById('search');
    const statusEl = document.getElementById('status');
    const emptyEl = document.getElementById('empty');
    const toastEl = document.getElementById('toast');
    const resetEl = document.getElementById('reset');

    function slugify(value) {{
      return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
    }}

    function matches(card) {{
      const needle = searchEl.value.trim().toLowerCase();
      const status = statusEl.value;
      const haystack = [card.title, card.status, card.summary, card.command, card.detail, ...card.tags].join(' ').toLowerCase();
      return (status === 'all' || card.status === status) && (!needle || haystack.includes(needle));
    }}

    async function copyCommand(command) {{
      try {{
        await navigator.clipboard.writeText(command);
        showToast('Command copied to clipboard.');
      }} catch (error) {{
        showToast('Copy failed. Select the command text manually.');
      }}
    }}

    function showToast(message) {{
      toastEl.textContent = message;
      toastEl.dataset.visible = 'true';
      window.clearTimeout(showToast.timeout);
      showToast.timeout = window.setTimeout(() => {{
        toastEl.dataset.visible = 'false';
      }}, 2200);
    }}

    function render() {{
      const visible = model.cards.filter(matches);
      cardsEl.innerHTML = '';
      navEl.innerHTML = '';
      emptyEl.dataset.visible = String(visible.length === 0);

      visible.forEach((card, index) => {{
        const id = slugify(card.title);
        const nav = document.createElement('a');
        nav.className = 'module-link';
        nav.href = `#${{id}}`;
        nav.innerHTML = `<span>${{card.title}}</span><span>${{card.status}}</span>`;
        navEl.appendChild(nav);

        const article = document.createElement('article');
        article.className = 'panel card';
        article.id = id;
        article.tabIndex = -1;
        article.innerHTML = `
          <div class=\"card-header\">
            <div>
              <p class=\"eyebrow\">Module ${{index + 1}}</p>
              <h3>${{card.title}}</h3>
            </div>
            <span class=\"status\" data-status=\"${{card.status}}\">${{card.status}}</span>
          </div>
          <p class=\"summary\">${{card.summary}}</p>
          <div class=\"command-row\">
            <code>${{card.command}}</code>
            <button type=\"button\" data-command=\"${{card.command.replaceAll('\\\"', '&quot;')}}\">Copy command</button>
          </div>
          <details>
            <summary>When to use this module</summary>
            <p>${{card.detail}}</p>
          </details>
          <ul class=\"tag-list\" aria-label=\"Module tags\">
            ${{card.tags.map(tag => `<li>${{tag}}</li>`).join('')}}
          </ul>`;
        cardsEl.appendChild(article);
      }});

      document.querySelectorAll('[data-command]').forEach(button => {{
        button.addEventListener('click', () => copyCommand(button.dataset.command));
      }});
    }}

    searchEl.addEventListener('input', render);
    statusEl.addEventListener('change', render);
    resetEl.addEventListener('click', () => {{
      searchEl.value = '';
      statusEl.value = 'all';
      render();
      searchEl.focus();
    }});

    window.addEventListener('hashchange', () => {{
      const target = document.querySelector(location.hash);
      if (target) target.focus();
    }});

    render();
  </script>
</body>
</html>
"""


def write_workbench(path: str | Path | None = None, model: WorkbenchModel | None = None) -> Path:
    """Write the workbench HTML and return its path."""

    if path is None:
        path = Path(tempfile.gettempdir()) / "d2re_visual_workbench.html"
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_workbench(model), encoding="utf-8")
    return output


def build_parser() -> argparse.ArgumentParser:
    """Build the GUI command parser."""

    parser = argparse.ArgumentParser(
        prog="d2re-gui",
        description="Generate and optionally open the local D2RE Visual Workbench.",
    )
    parser.add_argument(
        "--out",
        help="Path for the generated standalone HTML file. Defaults to the system temp directory.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Write the workbench without opening a browser.",
    )
    parser.add_argument(
        "--print-path",
        action="store_true",
        help="Print only the generated file path after writing.",
    )
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
        print(f"D2RE Visual Workbench written to: {output}")
        if ns.no_open:
            print("Open this file in a browser to use the GUI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
