#!/usr/bin/env python3
"""Beautified Visual IDE shell for the D2RE GUI.

This module builds on ``gui_integrated``. It keeps the same guarded action
execution model while adding a richer interface: themes, presets, favorites,
history, a command palette, output tools, and a more cinematic panel system.
"""

from __future__ import annotations

import argparse
import html
import json
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable

from . import gui_integrated as core


PRESETS: tuple[dict[str, object], ...] = (
    {
        "key": "packet-demo",
        "title": "Packet demo study",
        "action": "packet-timeline",
        "values": {"demo": True, "verbose": True, "list": False, "filter": ""},
    },
    {
        "key": "act5-tc-scan",
        "title": "Act V TC scan",
        "action": "treasure-class",
        "values": {"tc": "Act 5 Super C", "top": "25", "resolve": True, "json": False},
    },
    {
        "key": "meph-drop-oracle",
        "title": "Meph drop oracle",
        "action": "drop-oracle",
        "values": {"tc": "Mephisto (N)", "item": "weap87", "runs": "250000", "mf": "300", "json": False},
    },
    {
        "key": "seed-route-check",
        "title": "Map seed route check",
        "action": "map-observatory",
        "values": {"seed": "0x3F7A1B2C", "d2s": "", "level": "21", "ascii": True, "rooms": True},
    },
    {
        "key": "table-extract",
        "title": "Extract core tables",
        "action": "data-excavator",
        "values": {"all_mpqs": "C:/Diablo II/", "out": "./data_tables/", "table": "", "csv": True, "tc_tree": True},
    },
)

ACTION_ICONS: dict[str, str] = {
    "parse-save": "◇",
    "item-roll": "✦",
    "treasure-class": "⌬",
    "drop-oracle": "☽",
    "map-observatory": "✣",
    "packet-timeline": "⌁",
    "data-excavator": "▣",
    "doctor": "✚",
}


def _payload(csrf_token: str) -> str:
    model = core.build_model()
    return json.dumps(
        {
            "model": core.asdict(model),
            "presets": PRESETS,
            "icons": ACTION_ICONS,
            "serverMode": bool(csrf_token),
            "csrfToken": csrf_token,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")


def render_workbench(
    model: core.WorkbenchModel | None = None,
    *,
    server_mode: bool = False,
    csrf_token: str = "",
) -> str:
    """Render the enhanced visual IDE shell."""

    active_token = csrf_token if server_mode else ""
    payload = _payload(active_token)
    title = html.escape((model or core.build_model()).app_name)
    return f"""<!doctype html>
<html lang="en" data-theme="blood" data-density="comfortable">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>
:root {{ color-scheme: dark; --bg:#060403; --bg2:#120d0c; --panel:rgba(20,14,12,.92); --panel2:rgba(35,24,20,.97); --line:rgba(231,215,189,.2); --line2:rgba(209,59,50,.44); --text:#f7ead0; --muted:#bba88d; --accent:#d13b32; --accent2:#f09a4a; --good:#9fd39b; --bad:#ff9a90; --focus:#ffd28a; --radius:20px; --control:12px; --pad:1rem; --shadow:0 18px 60px rgba(0,0,0,.45); --glow:0 0 36px rgba(209,59,50,.24); --font-body:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; --font-display:Georgia,"Times New Roman",serif; --font-mono:"SFMono-Regular",Consolas,monospace; }}
html[data-theme="ember"] {{ --accent:#e06f2e; --accent2:#ffd08a; --line2:rgba(224,111,46,.46); --glow:0 0 36px rgba(224,111,46,.22); }}
html[data-theme="spectral"] {{ --accent:#7f95ff; --accent2:#9ff4ff; --line2:rgba(127,149,255,.46); --glow:0 0 36px rgba(127,149,255,.22); }}
html[data-density="compact"] {{ --pad:.7rem; --radius:14px; --control:10px; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; min-height:100vh; background:radial-gradient(circle at top left,color-mix(in srgb,var(--accent) 18%,transparent),transparent 34rem),linear-gradient(135deg,var(--bg),var(--bg2) 55%,#050403); color:var(--text); font-family:var(--font-body); line-height:1.55; }}
body::before, body::after {{ content:""; position:fixed; inset:0; pointer-events:none; }}
body::before {{ background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px); background-size:44px 44px; mask-image:radial-gradient(circle at center,black,transparent 80%); }}
body::after {{ background:radial-gradient(circle at 20% 10%,color-mix(in srgb,var(--accent2) 10%,transparent),transparent 10rem),radial-gradient(circle at 80% 30%,color-mix(in srgb,var(--accent) 12%,transparent),transparent 14rem); animation:emberDrift 12s ease-in-out infinite alternate; }}
@keyframes emberDrift {{ from {{ opacity:.55; transform:translateY(0); }} to {{ opacity:.88; transform:translateY(18px); }} }}
.skip-link {{ position:absolute; left:1rem; top:-4rem; z-index:20; padding:.75rem 1rem; border-radius:var(--control); background:var(--text); color:var(--bg); }} .skip-link:focus {{ top:1rem; }} :focus-visible {{ outline:3px solid var(--focus); outline-offset:3px; }}
.shell {{ width:min(1480px,100%); margin:0 auto; padding:clamp(1rem,2vw,2rem); position:relative; z-index:1; }}
.panel {{ position:relative; overflow:hidden; border:1px solid var(--line); border-radius:var(--radius); background:var(--panel); box-shadow:var(--shadow); backdrop-filter:blur(10px); }} .panel::before {{ content:""; position:absolute; inset:0; pointer-events:none; background:linear-gradient(135deg,rgba(247,234,208,.11),transparent 18%,color-mix(in srgb,var(--accent) 12%,transparent)); }}
.hero {{ display:grid; grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr); gap:1rem; margin-bottom:1rem; }} .hero-main {{ padding:clamp(1.4rem,4vw,4rem); }} .hero-side {{ display:grid; grid-template-columns:1fr; gap:.75rem; padding:var(--pad); background:var(--panel2); }}
.eyebrow {{ display:inline-flex; min-height:44px; align-items:center; gap:.5rem; color:var(--accent2); letter-spacing:.16em; text-transform:uppercase; font-size:.78rem; font-weight:850; }}
h1,h2,h3 {{ margin:0; font-family:var(--font-display); line-height:1.05; }} h1 {{ max-width:13ch; margin:.5rem 0 1rem; font-size:clamp(2.75rem,8vw,6.9rem); letter-spacing:-.06em; }}
.muted,.hero-copy {{ color:var(--muted); }} .stat-card,.rune-chip {{ min-height:44px; padding:var(--pad); border:1px solid var(--line); border-radius:16px; background:linear-gradient(180deg,rgba(247,234,208,.1),rgba(247,234,208,.035)); }}
.topbar {{ display:grid; grid-template-columns:minmax(220px,1fr) auto auto auto auto; gap:.75rem; align-items:end; margin-bottom:1rem; padding:var(--pad); }}
label {{ display:grid; gap:.45rem; font-weight:760; }} input,select,button,textarea {{ min-height:44px; border-radius:var(--control); border:1px solid var(--line); font:inherit; }} input,select,textarea {{ width:100%; padding:.65rem .9rem; background:rgba(0,0,0,.28); color:var(--text); }} button {{ cursor:pointer; padding:0 .95rem; background:linear-gradient(180deg,var(--accent),color-mix(in srgb,var(--accent) 58%,#000)); color:var(--text); font-weight:850; box-shadow:var(--glow); }} button.secondary {{ background:rgba(247,234,208,.08); box-shadow:none; }} button.ghost {{ background:transparent; box-shadow:none; }} button:disabled {{ opacity:.46; cursor:not-allowed; }}
.workspace {{ display:grid; grid-template-columns:290px minmax(0,1fr) 320px; gap:1rem; align-items:start; }} .rail {{ position:sticky; top:1rem; display:grid; gap:1rem; }} .rail .panel {{ padding:var(--pad); }} .module-list,.cards,.history-list,.preset-list {{ display:grid; gap:.65rem; }}
.module-link,.preset-btn,.history-item {{ display:flex; justify-content:space-between; gap:.75rem; min-height:44px; padding:.72rem; border:1px solid transparent; border-radius:var(--control); color:var(--text); background:rgba(247,234,208,.035); text-decoration:none; }} .module-link:hover,.preset-btn:hover,.history-item:hover {{ border-color:var(--line2); background:color-mix(in srgb,var(--accent) 12%,transparent); }}
.cards {{ gap:1rem; }} .card {{ display:grid; gap:1rem; padding:var(--pad); }} .card-header {{ display:flex; justify-content:space-between; gap:1rem; align-items:start; }} .title-row {{ display:flex; align-items:center; gap:.75rem; }} .rune {{ display:grid; place-items:center; width:2.4rem; height:2.4rem; border:1px solid var(--line2); border-radius:50%; color:var(--accent2); box-shadow:var(--glow); }} .card h3 {{ font-size:clamp(1.45rem,3vw,2.35rem); }}
.status {{ display:inline-flex; align-items:center; min-height:32px; padding:0 .75rem; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:.84rem; font-weight:850; }} .status[data-status="Active"] {{ border-color:color-mix(in srgb,var(--accent2) 56%,transparent); color:var(--accent2); }}
.form-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.75rem; }} .check-row {{ display:flex; align-items:center; gap:.6rem; min-height:44px; }} .check-row input {{ width:auto; min-height:auto; }}
.command-row,.output,.json-viewer {{ display:grid; gap:.75rem; padding:.75rem; border:1px solid var(--line); border-radius:16px; background:rgba(0,0,0,.28); }} .command-actions,.output-actions {{ display:flex; flex-wrap:wrap; gap:.6rem; }} code,pre {{ color:var(--text); font-family:var(--font-mono); overflow-wrap:anywhere; }} pre {{ white-space:pre-wrap; margin:0; max-height:24rem; overflow:auto; }}
.tag-list {{ display:flex; flex-wrap:wrap; gap:.45rem; padding:0; margin:0; list-style:none; }} .tag-list li {{ padding:.18rem .55rem; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:.82rem; }}
.palette {{ position:fixed; inset:0; display:none; place-items:start center; padding-top:8vh; background:rgba(0,0,0,.62); z-index:50; }} .palette[data-open="true"] {{ display:grid; }} .palette-box {{ width:min(720px,calc(100vw - 2rem)); padding:1rem; }} .palette-results {{ display:grid; gap:.5rem; margin-top:.75rem; }}
.toast {{ position:fixed; right:1rem; bottom:1rem; z-index:60; max-width:min(420px,calc(100vw - 2rem)); padding:1rem; border:1px solid var(--line2); border-radius:var(--control); background:var(--panel2); box-shadow:var(--shadow); transform:translateY(140%); transition:transform 180ms ease; }} .toast[data-visible="true"] {{ transform:translateY(0); }} .empty {{ display:none; padding:1.5rem; text-align:center; color:var(--muted); }} .empty[data-visible="true"] {{ display:block; }}
@media (max-width:1120px) {{ .workspace {{ grid-template-columns:260px minmax(0,1fr); }} .right-rail {{ grid-column:1/-1; position:static; }} .topbar {{ grid-template-columns:1fr 1fr; }} }} @media (max-width:780px) {{ .hero,.workspace,.form-grid,.topbar {{ grid-template-columns:1fr; }} .rail {{ position:static; }} }} @media (max-width:560px) {{ .shell {{ padding:.75rem; }} .card-header {{ display:grid; }} button {{ width:100%; }} }} @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ scroll-behavior:auto!important; transition-duration:.001ms!important; animation-duration:.001ms!important; animation-iteration-count:1!important; }} }}
</style>
</head>
<body>
<a class="skip-link" href="#workbench">Skip to workbench modules</a>
<div class="shell">
<header class="hero" aria-labelledby="page-title"><section class="panel hero-main"><div class="eyebrow">✦ D2RE visual IDE</div><h1 id="page-title">Runic Workbench</h1><p class="hero-copy">A command-forging interface for Diablo II reverse-engineering workflows: searchable, preset-driven, history-aware, and guarded by local-only execution rails.</p></section><aside class="panel hero-side"><div class="stat-card"><strong id="mode-label">Interactive runner</strong><br><span class="muted">Build, copy, run, inspect, and repeat.</span></div><div class="stat-card"><strong id="module-count">0 modules</strong><br><span class="muted">Active tools surfaced as panels.</span></div><div class="stat-card"><strong>Ctrl/⌘ + K</strong><br><span class="muted">Open command palette.</span></div></aside></header>
<section class="panel topbar" aria-label="Workbench controls"><label>Search modules<input id="search" type="search" autocomplete="off" placeholder="save, item, packet, map, tc" /></label><label>Theme<select id="theme"><option value="blood">Blood</option><option value="ember">Ember</option><option value="spectral">Spectral</option></select></label><label>Density<select id="density"><option value="comfortable">Comfortable</option><option value="compact">Compact</option></select></label><button class="secondary" type="button" id="favorites-only">Favorites</button><button class="secondary" type="button" id="palette-open">Command palette</button></section>
<main class="workspace" id="workbench"><aside class="rail left-rail"><section class="panel"><h2>Modules</h2><div class="module-list" id="module-list"></div></section><section class="panel"><h2>Presets</h2><div class="preset-list" id="preset-list"></div></section></aside><section class="cards" id="cards" aria-label="Workbench modules"></section><aside class="rail right-rail"><section class="panel"><h2>Run History</h2><p class="muted">Stored locally in this browser.</p><div class="history-list" id="history-list"></div><button class="ghost" type="button" id="clear-history">Clear history</button></section><section class="panel"><h2>IDE Notes</h2><p class="muted">Static mode can build and copy commands. Interactive mode can run guarded D2RE actions through the local server.</p></section></aside></main><p class="empty" id="empty" data-visible="false">No modules match the current filters.</p>
</div><div class="palette" id="palette"><section class="panel palette-box"><label>Command palette<input id="palette-input" type="search" placeholder="Jump to module or preset" /></label><div class="palette-results" id="palette-results"></div></section></div><div class="toast" id="toast" role="status" aria-live="polite"></div>
<script id="workbench-data" type="application/json">{payload}</script>
<script>
const boot=JSON.parse(document.getElementById('workbench-data').textContent); const model=boot.model; const presets=boot.presets; const icons=boot.icons; const serverMode=boot.serverMode; const csrfToken=boot.csrfToken;
const $=id=>document.getElementById(id); const cardsEl=$('cards'),navEl=$('module-list'),searchEl=$('search'),emptyEl=$('empty'),toastEl=$('toast'),themeEl=$('theme'),densityEl=$('density'),historyEl=$('history-list'),presetEl=$('preset-list'),palette=$('palette'),paletteInput=$('palette-input'),paletteResults=$('palette-results');
let favorites=new Set(JSON.parse(localStorage.getItem('d2re.favorites')||'[]')); let favoritesOnly=false; let history=JSON.parse(localStorage.getItem('d2re.history')||'[]');
function esc(v){{return String(v).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c])}} function slug(v){{return v.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'')}} function toast(m){{toastEl.textContent=m;toastEl.dataset.visible='true';clearTimeout(toast.t);toast.t=setTimeout(()=>toastEl.dataset.visible='false',2200)}}
function savePrefs(){{localStorage.setItem('d2re.favorites',JSON.stringify([...favorites]));localStorage.setItem('d2re.history',JSON.stringify(history.slice(0,30)))}} function applyPrefs(){{document.documentElement.dataset.theme=localStorage.getItem('d2re.theme')||'blood';document.documentElement.dataset.density=localStorage.getItem('d2re.density')||'comfortable';themeEl.value=document.documentElement.dataset.theme;densityEl.value=document.documentElement.dataset.density}}
function visibleActions(){{const q=searchEl.value.trim().toLowerCase();return model.actions.filter(a=>(!favoritesOnly||favorites.has(a.key))&&(!q||[a.title,a.status,a.summary,a.module,a.detail,...a.tags].join(' ').toLowerCase().includes(q)))}}
function fieldValue(form,f){{const e=form.elements[f.name];return !e?'':f.kind==='checkbox'?e.checked:e.value}} function payloadFor(a,form){{const values={{}};a.fields.forEach(f=>values[f.name]=fieldValue(form,f));return{{action:a.key,values}}}} function quote(p){{return /\s|"|'/.test(p)?JSON.stringify(p):p}} function commandFor(a,form){{const vals=payloadFor(a,form).values,parts=['d2re',a.module];a.fields.forEach(f=>{{const v=vals[f.name];if(f.kind==='checkbox'){{if(v&&f.flag)parts.push(f.flag);return}}if(!String(v||'').trim())return;if(f.flag)parts.push(f.flag,String(v).trim());else parts.push(String(v).trim())}});return parts.map(quote).join(' ')}}
async function copyText(t){{try{{await navigator.clipboard.writeText(t);toast('Copied.')}}catch{{toast('Copy failed; select manually.')}}}} function setField(form,name,value){{const e=form.elements[name];if(!e)return;if(e.type==='checkbox')e.checked=!!value;else e.value=value}}
function applyPreset(p){{location.hash='#'+slug(model.actions.find(a=>a.key===p.action).title);setTimeout(()=>{{const form=document.querySelector(`[data-action="${{p.action}}"] form`);if(!form)return;Object.entries(p.values).forEach(([k,v])=>setField(form,k,v));form.dispatchEvent(new Event('input',{{bubbles:true}}));toast('Preset loaded: '+p.title)}},30)}}
function addHistory(entry){{history.unshift(entry);history=history.slice(0,30);savePrefs();renderHistory()}} function renderHistory(){{historyEl.innerHTML=history.length?history.map(h=>`<button class="history-item" type="button" data-cmd="${{esc(h.command)}}"><span>${{esc(h.title)}}</span><span>${{esc(String(h.returncode))}}</span></button>`).join(''):'<p class="muted">No runs yet.</p>';historyEl.querySelectorAll('[data-cmd]').forEach(b=>b.addEventListener('click',()=>copyText(b.dataset.cmd)))}}
function pretty(stdout){{try{{return JSON.stringify(JSON.parse(stdout),null,2)}}catch{{return stdout||'No JSON detected.'}}}}
async function runAction(a,form,out,code){{if(!serverMode){{toast('Static mode: copy the command instead.');return}}out.textContent='Running...';try{{const r=await fetch('/api/run',{{method:'POST',headers:{{'Content-Type':'application/json','X-D2RE-Token':csrfToken}},body:JSON.stringify(payloadFor(a,form))}});const d=await r.json();code.textContent=d.command||commandFor(a,form);out.dataset.stdout=d.stdout||'';out.textContent=d.error||`return code: ${{d.returncode}}\n\nSTDOUT\n${{d.stdout||''}}\nSTDERR\n${{d.stderr||''}}`;addHistory({{title:a.title,command:code.textContent,returncode:d.returncode,at:new Date().toISOString()}})}}catch(e){{out.textContent='Request failed: '+e}}}}
function renderField(f){{const id=`f-${{f.name}}-${{Math.random().toString(16).slice(2)}}`;if(f.kind==='checkbox')return`<label class="check-row"><input name="${{esc(f.name)}}" type="checkbox" ${{f.default==='true'?'checked':''}} /> <span>${{esc(f.label)}}</span></label>`;const type=f.kind==='number'?'number':'text';return`<label for="${{id}}">${{esc(f.label)}}<input id="${{id}}" name="${{esc(f.name)}}" type="${{type}}" placeholder="${{esc(f.placeholder)}}" value="${{esc(f.default||'')}}" ${{f.required?'required':''}} /></label>`}}
function render(){{const visible=visibleActions();cardsEl.innerHTML='';navEl.innerHTML='';emptyEl.dataset.visible=String(!visible.length);$('module-count').textContent=`${{model.actions.filter(a=>a.status==='Active').length}} active modules`;visible.forEach((a,i)=>{{const id=slug(a.title),fav=favorites.has(a.key),rune=icons[a.key]||'✦';navEl.insertAdjacentHTML('beforeend',`<a class="module-link" href="#${{id}}"><span>${{rune}} ${{esc(a.title)}}</span><span>${{esc(a.status)}}</span></a>`);const article=document.createElement('article');article.className='panel card';article.id=id;article.tabIndex=-1;article.dataset.action=a.key;article.innerHTML=`<div class="card-header"><div class="title-row"><span class="rune">${{rune}}</span><div><p class="eyebrow">Panel ${{i+1}}</p><h3>${{esc(a.title)}}</h3></div></div><div><button class="ghost fav" type="button" aria-label="Toggle favorite">${{fav?'★':'☆'}}</button> <span class="status" data-status="${{esc(a.status)}}">${{esc(a.status)}}</span></div></div><p class="muted">${{esc(a.summary)}}</p><form class="form-grid">${{a.fields.map(renderField).join('')}}</form><div class="command-row"><code></code><div class="command-actions"><button type="button" class="copy">Copy command</button><button type="button" class="run" ${{a.status!=='Active'?'disabled':''}}>Run</button></div></div><details><summary>When to use this module</summary><p>${{esc(a.detail)}}</p></details><ul class="tag-list">${{a.tags.map(t=>`<li>${{esc(t)}}</li>`).join('')}}</ul><div class="output"><div class="output-actions"><strong>Output</strong><button type="button" class="ghost copy-output">Copy output</button><button type="button" class="ghost pretty">Pretty JSON</button><button type="button" class="ghost clear">Clear</button></div><pre aria-live="polite">No output yet.</pre></div>`;const form=article.querySelector('form'),code=article.querySelector('code'),out=article.querySelector('pre'),update=()=>code.textContent=commandFor(a,form);form.addEventListener('input',update);article.querySelector('.copy').addEventListener('click',()=>copyText(code.textContent));article.querySelector('.run').addEventListener('click',()=>runAction(a,form,out,code));article.querySelector('.copy-output').addEventListener('click',()=>copyText(out.textContent));article.querySelector('.pretty').addEventListener('click',()=>out.textContent=pretty(out.dataset.stdout));article.querySelector('.clear').addEventListener('click',()=>out.textContent='No output yet.');article.querySelector('.fav').addEventListener('click',()=>{{favorites.has(a.key)?favorites.delete(a.key):favorites.add(a.key);savePrefs();render()}});update();cardsEl.appendChild(article)}});renderPalette()}}
function renderPresets(){{presetEl.innerHTML=presets.map(p=>`<button class="preset-btn" type="button" data-preset="${{esc(p.key)}}"><span>${{esc(p.title)}}</span><span>Load</span></button>`).join('');presetEl.querySelectorAll('[data-preset]').forEach(b=>b.addEventListener('click',()=>applyPreset(presets.find(p=>p.key===b.dataset.preset))))}}
function renderPalette(){{const q=paletteInput.value.trim().toLowerCase();const rows=[...model.actions.map(a=>({{kind:'module',title:a.title,key:a.key,target:slug(a.title)}})),...presets.map(p=>({{kind:'preset',title:p.title,key:p.key,preset:p}}))].filter(x=>!q||x.title.toLowerCase().includes(q));paletteResults.innerHTML=rows.map(x=>`<button class="module-link" type="button" data-kind="${{x.kind}}" data-key="${{x.key}}"><span>${{esc(x.title)}}</span><span>${{x.kind}}</span></button>`).join('');paletteResults.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{{const kind=b.dataset.kind,key=b.dataset.key;palette.dataset.open='false';if(kind==='preset')applyPreset(presets.find(p=>p.key===key));else location.hash='#'+slug(model.actions.find(a=>a.key===key).title)}}))}}
applyPrefs();renderPresets();renderHistory();render();themeEl.addEventListener('change',()=>{{document.documentElement.dataset.theme=themeEl.value;localStorage.setItem('d2re.theme',themeEl.value)}});densityEl.addEventListener('change',()=>{{document.documentElement.dataset.density=densityEl.value;localStorage.setItem('d2re.density',densityEl.value)}});searchEl.addEventListener('input',render);$('favorites-only').addEventListener('click',()=>{{favoritesOnly=!favoritesOnly;render();toast(favoritesOnly?'Showing favorites':'Showing all modules')}});$('clear-history').addEventListener('click',()=>{{history=[];savePrefs();renderHistory()}});$('palette-open').addEventListener('click',()=>{{palette.dataset.open='true';paletteInput.focus();renderPalette()}});paletteInput.addEventListener('input',renderPalette);palette.addEventListener('click',e=>{{if(e.target===palette)palette.dataset.open='false'}});document.addEventListener('keydown',e=>{{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){{e.preventDefault();palette.dataset.open='true';paletteInput.focus();renderPalette()}} if(e.key==='Escape')palette.dataset.open='false'}});
</script>
</body></html>"""


def write_workbench(path: str | Path | None = None, model: core.WorkbenchModel | None = None, server_mode: bool = False) -> Path:
    if path is None:
        path = Path(core.tempfile.gettempdir()) / "d2re_visual_workbench.html"
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_workbench(model, server_mode=server_mode), encoding="utf-8")
    return output


class WorkbenchServer(ThreadingHTTPServer):
    token: str


class WorkbenchRequestHandler(BaseHTTPRequestHandler):
    server_version = "D2REWorkbench/2.0"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in ("/", "/index.html"):
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        token = getattr(self.server, "token", "")
        self._send(200, render_workbench(server_mode=True, csrf_token=token).encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run":
            self._send(404, b'{"error":"Not found"}', "application/json; charset=utf-8")
            return
        expected = getattr(self.server, "token", "")
        if self.headers.get("X-D2RE-Token") != expected:
            self._send(403, b'{"error":"Invalid workbench token","returncode":1}', "application/json; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            result = core.run_action(str(request.get("action", "")), request.get("values") or {})
            self._send(200, json.dumps(result, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
        except Exception as exc:  # pragma: no cover
            body = json.dumps({"error": str(exc), "returncode": 1}, ensure_ascii=False).encode("utf-8")
            self._send(400, body, "application/json; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        return


def serve_workbench(host: str = "127.0.0.1", port: int = 0, open_browser: bool = True) -> tuple[WorkbenchServer, str]:
    server = WorkbenchServer((host, port), WorkbenchRequestHandler)
    server.token = secrets.token_urlsafe(24)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_host, actual_port = server.server_address[:2]
    url = f"http://{actual_host}:{actual_port}/"
    if open_browser:
        webbrowser.open(url)
    return server, url


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="d2re-gui", description="Open the D2RE Runic Workbench.")
    parser.add_argument("--out", help="Write standalone HTML to this path instead of running the interactive server.")
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser automatically.")
    parser.add_argument("--print-path", action="store_true", help="Print the generated path or local URL.")
    parser.add_argument("--static", action="store_true", help="Generate static HTML instead of starting the action server.")
    parser.add_argument("--port", type=int, default=0, help="Port for the local action server. Defaults to an available port.")
    parser.add_argument("--no-wait", action="store_true", help="Start, print, then shut down immediately. Intended for tests and automation.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    ns = build_parser().parse_args(list(argv) if argv is not None else None)
    if ns.static or ns.out:
        output = write_workbench(ns.out, server_mode=False)
        if not ns.no_open:
            webbrowser.open(output.as_uri())
        print(output if ns.print_path else f"D2RE Visual Workbench written to: {output}")
        return 0
    server, url = serve_workbench(port=ns.port, open_browser=not ns.no_open)
    print(url if ns.print_path else f"D2RE Runic Workbench running at: {url}")
    print("Press Ctrl+C to stop the local workbench server.")
    if ns.no_wait:
        server.shutdown(); server.server_close(); return 0
    core.wait_for_server(server)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
