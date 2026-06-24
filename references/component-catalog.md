# HTML Component Catalog — Templates and Usage Guide

This catalog documents every reusable HTML component for the reading notes. For each component, we provide the HTML template, when to use it, and notes on adaptation.

---

## Page Shell

The overall page skeleton — always use this exact structure. Two templates are available in `assets/`:
- `template.html` — Chinese annotation language (default)
- `template_en.html` — English annotation language

Pick the one that matches the annotation language chosen in Phase 0b, then copy it as the starting point.

**Template overview** (embedded CSS + JS, zero external dependencies):
```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[set by initMeta() from paper-title meta]</title>
<!-- Paper metadata — agent fills these 8 <meta> tags -->
<meta name="paper-title" content="...">
<meta name="paper-type" content="...">   <!-- system|algorithm|survey|empirical|position -->
<meta name="paper-authors" content="...">
<meta name="paper-venue" content="...">
<meta name="paper-date" content="...">
<meta name="paper-institution" content="...">
<meta name="paper-method" content="...">
<meta name="paper-key-finding" content="...">
<style>
  /* EMBED Part 1–3: CSS Variables + Layout + Component Styles */
</style>
</head>
<body>
<div id="progress-bar"></div>
<div class="top-bar">
  <div class="top-inner">
    <span class="top-badge">论文精读</span>
    <!-- initMeta() auto-populates top-meta from <meta> tags -->
    <span class="top-meta"><strong>...</strong> · ... · ...</span>
    <span class="top-spacer"></span>
    <button class="top-btn" onclick="toggleTheme()" title="...">🌓 主题</button>
    <button class="top-btn" onclick="window.print()" title="...">🖨 打印</button>
  </div>
</div>
<div class="container">
  <aside class="sidebar">...</aside>
  <div class="content"><!-- ALL SECTIONS here --></div>
</div>
<button id="btt" ...>↑</button>
<!-- Annotation system: notes panel, popup, sticky editor -->
<script>
  /* initMeta() + theme + sidebar + lightbox + annotation engine */
</script>
</body>
</html>
```

**Key**: Never hand-write `<title>`, `.top-meta`, `.meta-row`, or `<h1>` content — the `initMeta()` JavaScript function reads the 8 `<meta>` tags and auto-populates all of them. Fill only the meta tags per SKILL.md A4.2.

---

## Component 1: `.meta-row` — Paper Metadata

**When**: Always — first section of the document.  
**Content**: 3-4 metadata fields about the paper.

> ⚠️ **Auto-generated**: The `.meta-row` HTML is auto-populated by `initMeta()` JavaScript from the 8 `<meta name="paper-*">` tags in `<head>`. Do NOT hand-write this section. Only fill the meta tags, then `initMeta()` renders the DOM.

**Rendered output** (for reference — do not copy):
```html
<div class="meta-row">
<span>📄 <strong>作者</strong> Author1, Author2, Author3 (Institution)</span>
<span>🏫 <strong>机构</strong> Institution name</span>
<span>🔬 <strong>方法</strong> Method description</span>
<span>🎯 <strong>核心</strong> Key takeaway</span>
</div>
```

**Which meta tags map to which labels** (hardcoded in `initMeta()`):
- `paper-authors` → 📄 作者 (Authors)
- `paper-institution` → 🏫 机构 (Institution)  
- `paper-method` → 🔬 方法 (Method)
- `paper-key-finding` → 🎯 核心 (Key Finding)

Fields with empty `content` are automatically omitted from the rendered row.

---

## Component 2: `.callout` — Emphasis Callout Boxes

**When**: Need to highlight a key insight, warning, or takeaway.  
**Types**: info (blue), warn (amber), success (green), danger (red), purple, cyan

```html
<!-- Information / Core argument -->
<div class="callout info">
  <strong>📌 Title</strong>
  <p>Body text with <strong>bold emphasis</strong> and detail.</p>
</div>

<!-- Warning / Tension -->
<div class="callout warn">
  <strong>⚠️ Title</strong>
  <p>Body text explaining the warning or concern.</p>
</div>

<!-- Success / Key insight -->
<div class="callout success">
  <strong>✅ Title</strong>
  <p>Body text with positive finding or design win.</p>
</div>

<!-- Danger / Vulnerability -->
<div class="callout danger">
  <strong>🚨 Title</strong>
  <p>Body text about a critical issue or vulnerability.</p>
</div>

<!-- Purple / Architectural insight -->
<div class="callout purple">
  <strong>🏗️ Title</strong>
  <p>Body text about architecture or infrastructure direction.</p>
</div>

<!-- Cyan / Clarification or methodology note -->
<div class="callout cyan">
  <strong>💡 Title</strong>
  <p>Body text for methodology notes or architectural clarifications.</p>
</div>
```

**Rules**:
- Always use a `<strong>` as the first child (title line)
- The title includes an emoji prefix
- Body is in `<p>` tag(s)
- Use info for core thesis, warn for tensions/concerns, success for key insights, danger for security issues, purple for architecture notes, cyan for methodology

---

## Component 3: `.tag` — Inline Label Badges

**When**: Categorize items — principles serve which values, feature gates, mode types.

```html
<span class="tag bl">Authority</span>
<span class="tag gr">Safety</span>
<span class="tag or">Feature-flagged</span>
<span class="tag rd">Internal-only</span>
<span class="tag pu">Adaptability</span>
<span class="tag cy">Capability</span>
```

**Color mapping**: bl=accent(blue), gr=success(green), or=warn(amber), rd=danger(red), pu=purple, cy=cyan

---

## Component 4: `.grid-2` / `.grid-3` + `.mini-card`

**When**: Display 2+ parallel concepts, categories, or dimensions. Use grid-2 for even-numbered small sets, grid-3 for classifications of 6+.

```html
<div class="grid-2">
  <div class="mini-card">
    <strong>🏷️ Card Title</strong>
    <p>Description text. Can include <strong>bold</strong> and inline references.</p>
  </div>
  <div class="mini-card">
    <strong>🏷️ Another Card</strong>
    <p>Another description with key points.</p>
  </div>
</div>
```

**For spanning cards (odd number in grid-2)**:
```html
<div class="mini-card" style="grid-column:1/-1">
```

---

## Component 5: `.pbox` — Principle Box (Numbered List Item)

**When**: List of design principles, rules, or guidelines — each with a number, title, tags, and description.

```html
<div class="pbox">
  <div class="pn">1</div>
  <div class="pb">
    <strong>Principle Name (English translation)</strong>
    <span class="tag bl">Value1</span> <span class="tag gr">Value2</span>
    <p style="margin:3px 0 0;font-size:12.5px;color:var(--text2)">One-line explanation of what this principle means in practice.</p>
  </div>
</div>
```

**Rules**:
- `.pn` contains the number (1, 2, 3...)
- `strong` contains the principle name
- `.tag` elements show which values the principle serves
- `<p>` contains a single-sentence explanation
- Only use tags that match actual value categories from the paper

---

## Component 6: `.trace` — Ordered Step Trace

**When**: Trace a process or workflow through multiple steps (e.g., "how a request flows through the system").

```html
<ol class="trace">
  <li><strong>Step Name</strong> → subsystem → outcome <span class="fref">source.ts</span></li>
  <li><strong>Step Name</strong> → subsystem → outcome <span class="fref">source.ts</span></li>
</ol>
```

**Rules**:
- Use for 5-12 step sequential flows
- Each step has a bold name, brief description, and optional source reference
- Steps are auto-numbered with CSS counter (no manual numbering needed)

---

## Component 7: `.summary-grid` — Key Metrics Dashboard

**When**: Paper has 5+ quantifiable key metrics or statistics worth highlighting at a glance.

```html
<div class="summary-grid">
  <div class="sg-item"><div class="sg-val">1.6%</div><div class="sg-lbl">AI decision logic ratio</div></div>
  <div class="sg-item"><div class="sg-val">98.4%</div><div class="sg-lbl">Infrastructure ratio</div></div>
  <div class="sg-item"><div class="sg-val">5-values</div><div class="sg-lbl">Core human values</div></div>
  <!-- ... more items -->
</div>
```

**Guidelines**:
- `.sg-val`: short value (number, percentage, count). Use large font automatically.
- `.sg-lbl`: one-line label explaining what the value represents
- Aim for 6-16 items
- Auto-fill grid: items wrap based on min-width (140px each)

---

## Component 8: `table` — Data Table

**When**: Structured data with rows and columns — mechanisms, comparisons, taxonomies.

```html
<table>
  <tr><th style="width:15%">Column 1</th><th style="width:45%">Column 2</th><th>Column 3</th></tr>
  <tr>
    <td><strong>Row label</strong></td>
    <td>Detailed description. Can include <code>code</code> and <span class="tag or">tags</span>.</td>
    <td>Comparison or alternative.</td>
  </tr>
</table>
```

**Rules**:
- Use `<th>` for header row only
- Use percentage widths on `<th>` for key columns to control proportions (e.g., 12%, 44%, 44%)
- Use `<strong>` for row labels
- Use `<code>` for file names, function names, identifiers
- Use `.tag` for categorical values
- Cell content can include `<br>` for multiple items

---

## Component 9: `pre` — Code Block

**When**: Pseudocode, algorithm outlines, or actual code snippets from the paper.

```html
<pre>
<span class="c">// Comment explaining context</span>
<span class="kw">while</span> (<span class="kw">not</span> stopped) {
    <span class="c">// step 1: description</span>
    result = <span class="fn">functionCall</span>(args);
    <span class="kw">if</span> (condition) <span class="kw">break</span>;
}</pre>
```

**Syntax highlighting classes**: `.c`=comment(gray), `.kw`=keyword(purple), `.s`=string(green), `.fn`=function(blue), `.num`=number(orange)

---

## Component 10: `.run-ex` — Running Example Callout

**When**: The paper uses a running example throughout. Include this at the start of the notes to trace the example through subsystems.

```html
<div class="run-ex">
  <strong>🔍 Running Example: "[Example description from paper]"</strong>
  <p style="margin-top:4px">Brief description of how the example is traced through the paper's sections.</p>
</div>
```

---

## Component 11: `.mindmap` — Concept Visualization

**When**: Architecture overview or high-level concept map — visually group related ideas.

```html
<div class="mindmap">
  <div class="center-node">Central Concept</div>
  <div class="children">
    <span class="child">Idea A</span>
    <span class="child">Idea B</span>
    <span class="child">Idea C</span>
    <span class="child">Idea D</span>
    <span class="child">Idea E</span>
  </div>
</div>
```

**Use sparingly** — only for the most important conceptual overview. Usually just once in the architecture section.

---

## Component 12: `.eq-pair` — Value/Principle Chain

**When**: Showing a chain of mapping (e.g., values → principles → implementation).

```html
<div class="eq-pair">
  <span class="eq-box">5 Human Values</span>
  <span class="eq-arrow">→</span>
  <span class="eq-box">13 Design Principles</span>
  <span class="eq-arrow">→</span>
  <span class="eq-box">Implementation Choices</span>
</div>
```

---

## Component 13: `.fref` / `.src-link` — Source File References

**When**: Referencing specific source files or line numbers (mostly for systems/code papers).

```html
<span class="fref">query.ts:365-453</span>
<span class="src-link">compact.ts</span>
```

- `.fref`: gray monospace, subtle — for general references
- `.src-link`: blue monospace, stands out — for clickable/important references

---

## Component 14: Section Title with Number Badge

**When**: Every h2 section heading.

```html
<h2><span class="num">1</span> Section Title in Chinese</h2>
```

The `.num` span creates a small blue rounded square with the section number. Use sequential numbers for main content sections; use 📋 or other emoji for appendix/supplementary sections.

---

## Component 15: Sidebar Entry

**When**: Building the sidebar navigation — one entry per major section.

**Mobile toggle**: The `#sidebar-toggle` button (`☰`) appears below 960px viewport width to show/hide the sidebar as a floating overlay. It is already in the template — no manual HTML needed.

```html
<details open>
  <summary>Group Name</summary>
  <a href="#section-id">Section Title</a>
  <a href="#section-id">Section Title</a>
</details>
```

Group 4-6 related sections under each `<details>` element. Use `open` attribute on all groups initially.

---

## Component 16: `.section-entrance` — Scroll Entrance Animation

**When**: The first 2-3 content sections to create a polished "page reveal" feel. Overuse dilutes the effect.

```html
<div class="section section-entrance" id="intro">
  <!-- section content -->
</div>
```

**CSS requirement**: See `design-system.md` Part 5a for the CSS and required JS snippet.  
**Print**: Add `.section-entrance{opacity:1!important;transform:none!important}` to `@media print` so printed view shows all content.

---

## Component 17: `.card-lift` — Hover Lift Effect on Cards

**When**: Any `.mini-card` or `.section` you want to feel interactive and "touchable." Creates tactile depth on hover.

```html
<div class="mini-card card-lift">
  <strong>🏷️ Card Title</strong>
  <p>This card lifts 3px on hover with a deeper shadow.</p>
</div>
```

**CSS**: See `design-system.md` Part 5b. Template.html already applies hover lift to `.mini-card` (2px), `.pbox` (3px right), and `.sg-item` (3px up) by default — `.card-lift` is for additional elements.

---

## Component 18: `.bg-texture` / `.accent-gradient` — Background and Accent Enhancements

**When**: Want to go beyond flat colors. `bg-texture` adds a subtle dot grid to the page background. `accent-gradient` replaces flat accent bars with a gradient.

```html
<!-- Texture on page background -->
<body class="bg-texture">
  <!-- ... -->
</body>

<!-- Gradient progress bar -->
<div id="progress-bar" class="accent-gradient"></div>

<!-- Gradient section divider -->
<hr class="accent-gradient" style="height:3px;border:none;border-radius:2px;margin:20px 0">
```

**CSS**: See `design-system.md` Parts 5c and 5d.

---

## Component 19: Figure with Caption (Base64 Embedded)

**When**: The paper has important architecture diagrams or charts extracted via Phase 1.2. Use sparingly — only for figures that genuinely add understanding. Images are embedded as base64 data URIs to keep the HTML self-contained (zero external dependencies).

```html
<figure class="paper-fig">
  <img src="data:image/png;base64,[BASE64_DATA]"
       alt="[ALT_DESCRIPTION_CN]"
       loading="lazy"
       data-caption="图：[FIGURE_CAPTION_CN]（原文 Figure N）">
  <figcaption>图：[FIGURE_CAPTION_CN]（原文 Figure N）</figcaption>
</figure>
```

**Rules**:
- `data-caption` attribute on `<img>` is **mandatory** — it feeds the lightbox overlay caption
- `loading="lazy"` defers image decoding until scrolled into view
- Base64 size guideline: keep each embedded image under ~2MB (corresponds to ~1.5MP image at 200 DPI). For larger figures, reduce extraction DPI to 150
- Clicking the image opens a full-resolution lightbox (see Component 21)
- Works in both light and dark modes (border color auto-adjusts via `[data-theme="dark"]`)

**CSS**: See `design-system.md` Part 3 and `template.html` for the complete `figure.paper-fig` and `.lightbox` styles.

---

## Component 20: Reading Time Badge

**When**: In the title section, below the meta row. Gives the reader an immediate sense of commitment.

```html
<span class="reading-time">⏱ 预计阅读 ~[N] 分钟</span>
```

**Estimate**: Roughly 300 words/minute for Chinese text. Count the extracted paper text word count and divide.

**CSS** (already in template.html):
```css
.reading-time{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;background:var(--code-bg);border-radius:12px;font-size:12px;color:var(--text2);border:1px solid var(--border)}
```

---

## Component 21: Figure Lightbox — Click-to-Zoom Overlay

**When**: Always included when Component 19 (paper figures) is used. Enables full-resolution viewing with zero external dependencies.

**HTML**: The lightbox overlay is created dynamically by JavaScript — no additional HTML markup is needed. Simply adding `figure.paper-fig img` elements with `data-caption` attributes automatically enables lightbox on them.

**CSS requirement**: See `design-system.md` Part 5g for the complete `.lightbox` CSS (overlay, img, caption, close/prev/next buttons).

**JS behavior** (inlined in `template.html` Part 5A):
- Creates overlay DOM once (`div.lightbox` with img, caption, close/nav buttons)
- Attaches click handlers to all `figure.paper-fig img` elements automatically
- Shows prev/next arrows when 2+ figures exist (hides them for single figures)
- Keyboard controls: `Escape` → close, `ArrowLeft` → prev, `ArrowRight` → next
- Locks body scroll while open (`document.body.style.overflow = 'hidden'`)
- Closes on: × button click, backdrop click, Escape key

**Rules**:
- All `figure.paper-fig img` elements automatically get lightbox behavior — no per-image setup needed
- The `data-caption` attribute on `<img>` is mandatory — it provides the caption text shown in the overlay
- Works with any number of figures (0: no behavior; 1: no arrows; 2+: prev/next arrows appear)
- Lightbox is hidden in print via `@media print { .lightbox{display:none!important} }`

---

## Component 22: KaTeX Formula Block

**When**: The paper contains mathematical formulas, equations, or formal definitions. KaTeX is loaded from CDN in `<head>` and auto-renders `$...$` (inline) and `$$...$$` (display) delimiters on page load.

**Dependency**: CDN-delivered KaTeX (katex.min.css ~20KB + katex.min.js ~60KB + auto-render.min.js). Requires network on first load; browser caches it afterwards. Falls back to monospace display when offline.

### Inline Formula
```html
<p>根据链式法则，梯度可以表示为 <span class="formula-inline">$\frac{\partial \mathcal{L}}{\partial \theta}$</span>。</p>
```

### Display Formula (centered block)
```html
<div class="formula-display">
$$ \mathcal{L}(\theta) = -\frac{1}{N}\sum_{i=1}^{N} \log p(y_i|x_i;\theta) + \lambda\|\theta\|_2^2 $$
</div>
```

### Multi-line Array
```html
<div class="formula-array">
$$ P = \begin{bmatrix} 0.7 & 0.2 & 0.1 \\ 0.3 & 0.5 & 0.2 \\ 0.1 & 0.3 & 0.6 \end{bmatrix} $$
</div>
```

**Rules**:
- `$...$` for inline, `$$...$$` for display; always wrap in `.formula-inline` / `.formula-display` for offline fallback
- After each formula block, include an explanation in the user's chosen annotation language
- KaTeX supports: `\sum`, `\prod`, `\int`, `\frac`, `\partial`, `\mathcal{}`, `\mathbb{}`, `\text{}`, matrices, cases, most LaTeX math
- If the paper has 5+ significant formulas, consider adding a dedicated "核心公式" section

---

## Component 23: `.fig-ref` — Duplicate Figure Cross-Reference

When a figure is referenced multiple times within the HTML (e.g., the same architecture diagram discussed in both the Design section and the Discussion section), `assemble_figures.py` only embeds the full `<figure>` once. Subsequent `<!-- FIG:N -->` placeholders are replaced with a lightweight cross-reference link pointing to the first occurrence.

```html
<p class="fig-ref">📊 <em>参见 <a href="#fig-2">Fig. 2. System Architecture Overview</a></em></p>
```

**CSS** (in template.html):
```css
.fig-ref { font-size: 13px; color: var(--text2); padding: 4px 0 }
.fig-ref a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px }
.fig-ref a:hover { color: var(--accent-dk) }
```

**Rules**:
- This component is auto-generated by `assemble_figures.py` — sub-agents do NOT write `.fig-ref` directly
- Each figure receives an `id="fig-N"` anchor on its first `<figure>` element for the link target
- Do NOT intentionally duplicate `<!-- FIG:N -->` placeholders to force cross-references; let the assembly script handle deduplication naturally

---

## Adaptation Rules

### Component 24: In-Browser Highlighter & Annotation System

**What**: A complete client-side annotation system embedded in the HTML output. Users highlight text with a 6-color palette, then click highlights to recolor/delete/edit notes via a floating sticky note editor. All annotations are listed in a sliding right-side panel.

**When**: Always included (auto-enabled by CSS/JS in the template). Not visible until the user interacts.

**Two-step interaction flow**:
1. **Select text → pick color** → text is highlighted immediately (palette has only color swatches).
2. **Click existing highlight** → palette expands with: color swatches, ∅ delete button, ✎ edit button. Clicking edit opens a floating **sticky note editor** where the user writes their annotation.

**Architecture**:
- Highlight marks: `<mark class="hl-{color}" data-annotation-id="...">` with `data-has-note` for annotated content. Annotated marks show a 📎 paperclip indicator.
- Sticky note editor: fixed-position `.sticky-editor` with warm paper texture background, subtle rotation (0.5°), pin graphic, spring animation on open.
- Notes panel: `.notes-panel` slides from right edge (320px wide), default collapsed showing only a 28px arrow handle. Uses `transform: translateX(calc(100% - 36px))` transition, never pushes content.
- Notes list: Each item rendered as a mini sticky card (`transform: rotate(0.3deg)` alternating angles), with color bar, truncated text, timestamp, and hover-revealed edit/delete buttons.
- Persistence: manual save via `saveHtml()` button. Annotations are serialized into an embedded `<script id="ppr-annotation-data">` tag — user must click "Save" to persist the updated file to disk. On reload, annotations are restored from this tag. No localStorage is used.

**Key CSS variables**: `--hl-yellow` through `--hl-purple` (highlighter colors), `--sticky-bg` (note paper background), `--sticky-shadow` (layered paper shadow).

**Key HTML IDs**: `#notesPanel` (sliding panel), `#hl-popup` (color palette), `#stickyEditor` (floating note), `#stickyTextarea`, `#hlToast` (warning messages), `#notes-toggle` (mobile toggle only).

**Key JS functions**: `serializeSelection()`, `applyMarkWrapper()`, `restoreHighlights()`, `confirmHighlight(color)`, `showHighlightPopup(e,id)`, `bindMarkClicks()`, `openStickyEditor()`, `closeStickyEditor()`, `renderNotesList()`, `toggleNotesPanel()`.

**Caveats**:
- Highlights use text character offsets (not DOM paths) — works because `.content` `textContent` is stable
- On page reload, highlights are stripped and re-applied from annotations data (clean-state strategy)
- Overlapping highlights create nested `<mark>` elements; CSS cascade handles visual precedence
- KaTeX math formula regions are automatically excluded from highlighting
- The popup dynamically adds/removes the delete swatch and edit button depending on whether it's a new highlight (no delete/edit) or editing an existing one

---

When generating HTML from a paper:

1. **Always include**: Page shell (from template), at least one callout.info (core thesis), sidebar, footer. The meta-row is auto-generated by `initMeta()` — just fill the meta tags.
2. **Include if paper has**: The component that best fits the paper's content pattern (see mapping table in SKILL.md)
3. **Skip if paper doesn't have**: Don't force-fit content into components. For example, if the paper has no "design principles", don't create a principle box section.
4. **If the paper has figures**: Always include the FIGURES section — use the `SECTION: FIGURES` block from template.html. Place it after the architecture/taxonomy section (wherever diagrams are contextually relevant). Figures without analytical context are useless.
5. **Combine when appropriate**: A paper might have both a comparison table AND a taxonomy table — use both.
6. **Section ordering**: Determined by the chosen organization strategy (see SKILL.md Organization Strategy Reference). Default (paper-structure-aligned): follow the paper's own structure — intro first, then design/method, then results/analysis, then discussion/conclusion. Put summary/takeaways last. Other strategies (cognition-first, question-driven, persona-driven) reorder sections per their cognitive/narrative rules.
