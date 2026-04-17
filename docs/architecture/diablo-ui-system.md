# Diablo-Inspired UI System Foundations

> Visual language and interaction rules for future D2RE TUI/web IDE surfaces.

This document does **not** copy Diablo IV assets. It describes a compatible
*design grammar*: dark fantasy, panel hierarchy, restrained ornament, strong
contrast, and clear investigative workflows.

---

## 1. Design goals

The interface should feel like a research cathedral rather than a spreadsheet
accident. It must balance atmosphere with legibility.

Primary goals:

- dark gothic tone without sacrificing readability
- panel-first layout for complex workflows
- obvious navigation and strong information hierarchy
- keyboard-friendly operation
- graceful degradation to low-motion and high-contrast modes

---

## 2. Visual grammar

### 2.1 Surface hierarchy

Use a three-tier surface model:

1. **Sanctuary background**
   - low-contrast textured backdrop
   - subtle gradients, smoke, ash, parchment, or stone cues
   - never competes with content

2. **Primary panels**
   - dark iron / obsidian surfaces
   - heavy but clean border treatment
   - used for inspectors, editors, timelines, and graphs

3. **Inset cards and controls**
   - parchment, charcoal, or dark leather inflections
   - used for filters, field groups, metric summaries, and secondary actions

### 2.2 Accent philosophy

One accent should carry urgency and focus. For this project, default accent use is:

- ember red for active selections, warnings, important markers
- muted gold for metadata and structure
- cold stone gray for framing and neutral separators

Accent usage must stay sparse. If everything glows, nothing glows.

### 2.3 Ornament strategy

Decorative motifs should be used as *frame punctuation*, not wallpaper.

Allowed motifs:
- runic dividers
- carved-corner frames
- subtle sigils for panel categories
- faint line etching for headers and tabs

Avoid:
- dense filigree behind text
- animated flames under content
- high-frequency textures behind tables

---

## 3. Layout system

### 3.1 Panel model

The future IDE should use a dockable panel architecture with these concepts:

- left rail for navigation and entity search
- center workspace for the active investigation
- right rail for inspectors, explanations, and cross-links
- bottom tray for packet timelines, logs, and diff summaries

### 3.2 Panel states

Every panel should support:

- docked
- collapsed
- maximized
- detached view state
- pinned

### 3.3 Workspace behavior

Users should be able to save named workspaces such as:

- Save Inspection
- Map Research
- Packet Analysis
- Item Generation Lab
- Build Planner

---

## 4. Component families

### 4.1 Headers

Headers should carry:
- panel title
- entity context
- quick actions
- breadcrumbs
- optional status badge

### 4.2 Data tables

Tables are core to D2RE and must feel better than raw docs.

Required features:
- sticky headers
- column visibility control
- keyboard navigation
- inline explanation affordances
- row pinning
- export to JSON/CSV

### 4.3 Tree explorers

Use tree views for:
- inventory structures
- socket trees
- treasure class resolution
- documentation hierarchies
- packet field expansion

### 4.4 Timelines

Timelines should represent:
- packet sequences
- item generation stages
- save-file changes over time
- investigation sessions

### 4.5 Explanation blocks

A core UX pattern: every dense technical view should have a paired explanation block.

Example:
- left: packet fields
- right: why this packet appears, what triggered it, and what to inspect next

---

## 5. Motion rules

Motion should feel like embers and weight, not fireworks.

Allowed:
- soft fades
- panel slide-ins
- hover glows
- slow ambient background drift

Avoid:
- bouncing transitions
- large-scale parallax
- rapid pulsing effects
- flashy loader animations

Accessibility rule:
- support reduced-motion mode from day one

---

## 6. Typography rules

The interface may use atmospheric headings, but body text must remain extremely legible.

Suggested hierarchy:
- display / panel titles: strong serif or rune-adjacent treatment
- body / tables / technical data: clean sans or mono
- code / schema / offsets: monospace only

Principle:
- the fantasy belongs in the frame,
- the truth belongs in the text.

---

## 7. Iconography

Icon sets should distinguish investigative domains:

- packets: signal / waveform / glyph-node icon
- maps: compass / room graph / gate icon
- items: gem / blade / helm / socket icon
- docs: tome / parchment icon
- build planner: constellation / branch icon
- diff: split sigil / mirrored blades icon

Icons should be simple silhouettes with optional accent lines, not detailed illustrations.

---

## 8. Accessibility requirements

The atmosphere is optional. Readability is not.

Must-have requirements:
- color is never the sole carrier of meaning
- high-contrast mode
- keyboard traversal for all core panels
- focus rings visible on dark surfaces
- screen-reader-friendly headings and region labels
- reduced-motion support
- plain text export path for complex views

---

## 9. First-pass implementation guidance

The first actual UI implementation should not begin with a giant monolith.
Start with:

1. shared design tokens
2. panel shell component
3. card / table / badge primitives
4. theme variables for dark fantasy mode
5. one pilot workflow, likely the Save Inspector

This gives D2RE a believable, usable visual spine before more advanced panels land.

---

## 10. Practical translation to code

When the web shell begins, the UI system should be organized around:

- `theme/tokens.ts`
- `theme/modes.ts`
- `components/panel/*`
- `components/table/*`
- `components/tree/*`
- `components/explainer/*`
- `layouts/workspace/*`

For TUI work, the same information hierarchy should map into textual panels,
with ornament simplified but panel naming and navigation preserved.

---

## 11. Definition of done for the UI system

The design system is ready for broader use when:

- a panel can be reused without custom CSS drift
- tables, trees, and inspectors look like the same product family
- the interface feels atmospheric at a glance but precise at use time
- and new contributors can build a panel by following a stable recipe
