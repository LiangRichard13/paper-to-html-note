---
name: paper-to-html-note
description: >
  Convert CS/SE academic PDF papers into high-quality HTML reading notes. Use this skill when the user mentions "paper reading notes,"
  "PDF to HTML notes," "paper deep reading," provides a PDF file path requesting reading notes, or wants to convert a paper
  into a readable format. Applicable to arXiv, conference, and journal papers in computer science and software engineering.
  Even if the user doesn't say "HTML" or "reading notes" explicitly, consider this skill whenever extracting and organizing
  content from a PDF paper.
---

# Paper to HTML Reading Note

Convert CS/SE academic PDF papers into a self-contained, interactive HTML reading notes document with dark mode, sidebar navigation, rich component library, and user-chosen annotation language (Chinese or English).

## Phase 0: Mode Selection

This skill supports two execution pipelines. **The mode is not decided automatically — you present the choice to the user after gathering basic paper info.**

### Phase 0a: Pre-steps (always run first)

**Path conventions**: Throughout this skill:
- `<pdf-path>` = the absolute path to the PDF file provided by the user
- `<output-dir>` = the directory containing the PDF file. All intermediate files are written here.
- `<skill-dir>` = the directory containing this SKILL.md (i.e., `C:\Users\Administrator\.claude\skills\paper-to-html-note` or equivalent)

Before presenting the choice, gather the data needed for a good recommendation:

1. **Check dependencies**: Verify PyMuPDF is installed:
   ```bash
   python -c "import fitz; print(fitz.__version__)" 2>/dev/null || echo "MISSING"
   ```
   If missing: `pip install PyMuPDF`. Also check `pdftotext --help` is available.

2. Read `assets/template.html` — the complete CSS/JS shell (~40KB). Read this LAST since it's the largest reference file.

3. Read `references/component-catalog.md` — all 22 components. Read FIRST (smaller, needed to understand component patterns before seeing the template).

4. Extract PDF text with `pdftotext -layout` (or PyMuPDF fallback). After extraction, verify: if `wc -l` shows <50 lines AND `python -c "import fitz; print(fitz.open('<pdf-path>').page_count)"` also shows <2 pages, the PDF is likely unreadable (scanned, encrypted, or corrupted). Warn the user and ask whether to proceed.

5. Run `scripts/extract_figures.py` to get page count and figure count. **Read only the stdout summary** (page count, figure count, method breakdown) — do NOT read the full JSON file which contains multi-MB base64 strings. If the script reports 0 figures, note this for the user; the paper may have no figures or use non-standard caption formats.

6. **Hard guard**: If `pages ≥ 50` and Ultracode is NOT available, warn the user that Pipeline A risks context overflow and quality degradation. Proceed only with user acknowledgment.

### Phase 0b: Ask the user

Use `AskUserQuestion` to present **two choices**: pipeline mode and annotation language.

**Question 1 — Pipeline mode.** Include:
- **Page count** and **figure count** from Phase 0a
- **Your recommendation** and why
- **Key trade-offs** so the user can make an informed decision

Here's the decision framework for your recommendation:

| Mode | Agent Count | Best For | Speed | Quality |
|------|-------------|----------|-------|---------|
| **A: Sequential** | 1 agent | Short papers (<12 pages), quick previews | Faster start, predictable output | Single-agent coherence |
| **B: Parallel** (needs Ultracode) | 5–12 agents | Long papers (≥12 pages), figure-rich (>6), surveys/reviews, content-dense papers | Slower start, faster wall-clock for big papers | Each section written by dedicated agent |

**Recommendation logic** (use this to decide what to suggest):

```text
If Ultracode is NOT available:
  → Pipeline A is the only option. Inform the user and proceed.

If Ultracode IS available:
  Any of: pages ≥ 12, figures > 6, or the paper is a
  survey/review whose sections partition naturally?
    ├─ Yes → Recommend Pipeline B (parallelism wins on
    │         content that decomposes naturally)
    └─ No  → Recommend Pipeline A (small enough that a
              single agent's coherence matters more)
```

**Example question format:**

```markdown
📋 **论文基本信息**：29页，8张图，综述论文

检测到两个生成模式可选：

**Pipeline A（串行）** — 1个Agent完成全部工作
  - ✅ 输出风格一致，适合连贯性要求高的长文
  - ✅ 图直接嵌入对应章节
  - ⏱ 预计速度：较快
  - **推荐场景**：短文、公式多、或偏好单Agent一致性

**Pipeline B（并行）** — 5-12个Agent并行写作（需Ultracode）
  - ✅ 各章节由独立Agent撰写，深度更高
  - ✅ 适合分类体系清晰的综述论文
  - ⏱ 预计速度：启动慢但总时长可能更短
  - **推荐场景**：长论文、图表多、综述类

👉 **我的建议**：这篇是29页的综述论文，分类体系清晰（提取→存储→检索→进化），**推荐Pipeline B（并行）**。

请选择模式：
```

The user picks, and you proceed with the chosen pipeline. If the user does not respond, default to **Pipeline A**.

**Question 2 — Annotation language.** Use a second `AskUserQuestion`:

| Option | Label | Description |
|--------|-------|-------------|
| **Chinese** (Recommended) | 中文（简体）| All explanatory text, section titles, callout titles, and figure captions in Simplified Chinese. Technical terms, author names, code identifiers, and numerical values preserved in original. |
| **English** | English | All annotations in English. The `<html lang>` attribute should be set accordingly. |

**Default**: Chinese. If the user does not respond, proceed with Chinese.

**Language affects**:
- The `<html lang="...">` attribute in the template
- All section titles, callout titles, table headers, figure captions
- The Content Depth Rules and Sub-Agent Prompt (sub-agents are told which language to write in)
- Technical terms, code identifiers, author names, and numerical values are always preserved in original form regardless of language choice

Both pipelines share the same HTML template, component library, figure extractor, and quality checks — they differ in how work is scheduled across agents and how figures are embedded inline (Pipeline A: direct base64; Pipeline B: `<!-- FIG:N -->` placeholders replaced in a post-processing Python step).

**Example combined prompt:**

```markdown
📋 **论文基本信息**：29页，8张图，综述论文

**请选择生成模式：**

**Pipeline A（串行）** — 1个Agent
  - ✅ 输出风格一致
  - ✅ 图直接嵌入对应章节
  - **推荐场景**：短文、公式多

**Pipeline B（并行）** — 5-12个Agent（需Ultracode）
  - ✅ 各章节由独立Agent撰写，深度更高
  - ✅ 适合分类体系清晰的综述论文
  - **推荐场景**：长文、图表多、综述类

👉 **建议**：推荐Pipeline B（并行）。

**请选择注释语言：**

中文（简体） — 所有解释性文字使用中文
English — All annotations in English
```

---

## Content Depth Rules (Both Pipelines)

A reading note is not a translation or summary — it is a **curated analysis**. Every section must deliver more value than re-reading the original paper. These rules apply regardless of which pipeline is used.

### Principle 1: Follow Paper Structure, Invert Within Sections

**Section order must match the paper's own structure** — Introduction → Background → Method → Experiments → Discussion → Conclusion. Readers who know the paper should feel oriented, not lost.

**Within each section**, use inverted pyramid: state the conclusion first, then explain why.

```
❌ Paper-order: "The authors propose three memory types: text, vector, and graph.
    Text memory is... Vector memory is... Graph memory is..."
   → Reader must read everything to understand what matters.

✅ Inverted: "Memory boils down to three design choices: what to store (text/vector/graph),
    how to update (similarity/reasoning), and how to retrieve (content/structure/policy).
    Text is simplest but loses relations. Vector scales well but can't answer 'what caused what'.
    Graph captures everything but costs the most to build."
   → Reader grasps the framework in the first sentence.
```

### Principle 2: Mandatory Insight Types

Every section of 500+ words MUST include at least **2 of the following 4** insight types. Tag them explicitly so the reader can identify them:

| Type | Tag | What It Does | Example |
|------|-----|-------------|---------|
| **Design Motivation** | `callout.purple` | Why did the authors choose X over Y? What implicit tension drove this decision? | "MemGPT borrows OS paging not because it's clever, but because context windows have the same fundamental constraint as RAM: they're fast but tiny." |
| **Cross-Section Link** | `callout.warn` | How does this design choice ripple through to later results? | "The retrieval strategy chosen here (content-based vs structure-aware) directly determines whether the agent passes or fails MemoryArena's cross-session tests in Section 6." |
| **Practical Takeaway** | `callout.success` | If I were building this, what's the one thing I must get right? | "Start with Pattern B (context + retrieval store). Don't jump to learned memory policies until you have at least 3 months of production logs proving heuristic control is the bottleneck." |
| **Critical Observation** | `callout.danger` | What limitation does the paper NOT discuss but a practitioner would discover? | "The paper doesn't mention this, but a single incorrect reflection in a long-running agent can poison thousands of downstream decisions. The failure scales linearly with agent lifetime." |

### Principle 3: Two-Layer Depth Structure

Every section operates at two levels. Use different HTML components to distinguish them:

| Layer | Purpose | Primary Components |
|-------|---------|-------------------|
| **Summary Layer** (What the paper says) | Accurately convey the paper's claims, methods, and results | `table`, `.callout.info`, plain `<p>`, `<ul>` |
| **Insight Layer** (What it means) | Synthesize, critique, connect, and extract actionable lessons | `.callout.purple`, `.callout.warn`, `.callout.success`, `.callout.danger` |

**Rule of thumb**: A section should be roughly 60% summary layer and 40% insight layer. A section with zero insight callouts is a failed section — rewrite it.

### Principle 4: Component Choice by Intent

Choose components based on the **cognitive intent** of the content, not just what fits the data shape:

| Intent | Component | Why |
|--------|-----------|-----|
| "Here's what the paper found" | `table` | Tables are neutral; they present data without interpretation |
| "Here's the paper's main argument" | `.callout.info` | Blue = factual but highlighted |
| "This is why it matters" | `.callout.purple` | Purple = architectural/design insight |
| "Watch out — there's a tension here" | `.callout.warn` | Amber = caution, trade-off |
| "This is actionable" | `.callout.success` | Green = positive, practical takeaway |
| "This is a real risk" | `.callout.danger` | Red = danger, critical limitation |
| "Here are the parallel concepts" | `.grid-2 > .mini-card` | Cards = compare/contrast at a glance |

---

# Pipeline A: Sequential (Default)

Single-agent sequential pipeline. Extract → analyze → map → write → check. Figures and formulas are extracted first, then embedded inline as the agent writes each section — ensuring they appear in the correct context.

```
Text Extraction → Figure Extraction → Formula Extraction → Structure Analysis → Content Mapping → HTML Generation → Quality Check
```

## Phase A1: PDF Text Extraction

Uses `pdftotext` for text extraction, with a PyMuPDF fallback if the result is garbled.

**Path A — pdftotext (default)** — simple and fast. Formulas come out garbled (use rendered previews or manual transcription for critical equations).

### Step 1.1: Extract full text

```bash
pdftotext -layout "<pdf-path>" "<output-dir>/paper_text.txt"
```

Check the result: `wc -l` should show >100 lines for a real paper. If under 50 lines or output is garbled, fall back to PyMuPDF:

```bash
python -c "
import fitz
doc = fitz.open('<pdf-path>')
for page in doc:
    print(page.get_text())
" > "<output-dir>/paper_text.txt"
```

### Step 1.2: Extract paper figures as individual cropped images

Academic papers store figures as **vector graphics** (not raster images), so `page.get_images()` returns only small icons/emoji — not the actual diagrams. The correct approach is **layout-aware caption-driven cropping**, which detects "Fig. N" captions and crops only the figure region above each caption.

The skill's built-in **caption-driven smart cropping** (Tier 3) handles this automatically — no extra dependencies beyond PyMuPDF:

```bash
python "<skill-dir>/scripts/extract_figures.py" "<pdf-path>" --dpi 200 -o "<output-dir>/figures_b64.json"
```

**How it works** (implemented in `scripts/extract_figures.py`):

1. Scans all pages for "Fig. N" / "Figure N" caption text blocks using `page.get_text('blocks')`
2. For each caption found, estimates the initial **figure region**:
   - **Bottom edge** = caption top minus 2pt gap
   - **Top edge** = bottom of the nearest preceding **body paragraph** (not figure-internal labels), or page top margin
3. **Determines horizontal bounds from drawing extent** — NOT from caption width (which is unreliable: many full-width figures have short centered captions). Drawing cells in the vertical figure band are collected; if their x-extent spans >70% of the text area, the figure is full-width. Otherwise it is single-column, centered on the drawing extent.
4. **Refines bounds using actual drawing bbox edges** — vector graphics (`page.get_drawings()`) are collected; only drawings whose centers fall in the figure band and NOT inside body paragraphs are kept. The final crop uses the **min/max of actual drawing bounding box edges** (not grid cell centers) with 6pt padding — this correctly captures the visual extent of wide-spanning drawings whose centers are far from their edges.
5. **Critical distinction**: Only full-width (>70% text area) + substantial (>150 chars) paragraphs are treated as "body text" that constrains cropping. Short labels, dialogue examples, and taxonomy node text within figures are correctly retained as part of the figure region.
6. Renders **only the refined region** at target DPI using `page.get_pixmap(clip=clip_rect, dpi=200)`
7. Outputs individual base64 strings per figure (not per page), with a `method` field indicating whether `density` or `caption` was used

> **⚠️ Text-Only Figure Cropping Note**: Steps 3-4 above (drawing-extent-based) work best for vector graphics. For **text-rendered figures** (classification trees, tables, code structure diagrams, flowcharts), `page.get_drawings()` returns empty within the figure region. The script automatically falls back to caption-width-based horizontal bounds and enables text-block cluster refinement for vertical bounds (since v4.1). This covers ~99% of CS papers.
>
> If cropping is still unsatisfactory (too much body text included, or cropped too tightly), the body paragraphs near the figure may be too close, shifting the boundary estimate. Resolution:
> 1. First run `python scripts/extract_figures.py <pdf> --dpi 200 --save-images` to inspect each figure's PNG
> 2. For problematic figures, manually inspect text block coordinates with PyMuPDF:
>    ```python
>    import fitz
>    doc = fitz.open("<pdf>")
>    for b in doc[5].get_text('blocks'):
>        print(f"y=({b[1]:.0f}-{b[3]:.0f}) {b[4][:80]}")
>    ```
> 3. Specify a custom crop rect based on coordinates:
>    ```python
>    rect = fitz.Rect(36, 50, page_width - 36, 455)  # (left, top, right, bottom)
>    pix = page.get_pixmap(clip=rect, dpi=200)
>    ```

**Advantages over full-page rendering**:
- ~48% smaller total image data (drawing density tightens crop to actual figure bounds)
- Higher effective DPI on actual figures (200 DPI focused only on figure pixels)
- Clean individual crops — no surrounding headers, footnotes, or body text
- Figure-internal content preserved — axis labels, dialogue examples, taxonomy text stay in the crop
- Fully automatic — no manual page number specification needed
- Handles both full-width and single-column figure layouts automatically

**DPI guidance**: Use 200 DPI as default. For text-heavy figures, 150 DPI is sufficient. For detailed architecture diagrams, use 300 DPI.

**Output format**: JSON with per-figure metadata:

```json
{
  "figures": [
    {
      "page": 3,
      "fig_num": "1",
      "caption": "Fig. 1. Overview of...",
      "width": 1340,
      "height": 665,
      "dpi": 200,
      "base64": "iVBORw0KGgo..."
    }
  ],
  "summary": [...],
  "total_size_kb": 1535.2
}
```

**1.2b. Read the JSON metadata only**: Parse `figures_b64.json` to get figure metadata (page, fig_num, caption, width, height) and the `summary` array. **Do NOT read the full `base64` strings into context** — they are 1-5MB of binary data. Instead, construct data URIs inline when embedding each figure into the HTML:

```
data:image/png;base64,<base64-string>
```

These URIs go into `<img src="...">` attributes. **Each figure should be embedded inline in its most contextually relevant section** (e.g., architecture diagram in the architecture section, comparison chart in the comparison section), not all placed in a single gallery. A separate gallery section is optional for multi-figure papers (see Phase A4.2 and template note).

### Step 1.2-alt: Handle mathematical formulas

pdftotext cannot extract formulas as LaTeX (PDFs store rendered glyphs, not source code). Two options:

- **Manual transcription** (recommended): For critical formulas, read from the rendered page image (use PyMuPDF to quickly render a preview of the page) and write LaTeX inside `$$...$$` delimiters. This is the preferred approach since it enables KaTeX rendering, searchability, and dark mode support.
- **Figure extraction fallback**: If the formula count is very high (>15) and manual transcription is impractical, use caption-driven cropping (`scripts/extract_figures.py`) to extract the formula-heavy portion of the page as an image. Note that embedded formula images won't render in dark mode or support text search.

### Step 1.3: Assess paper length

Count lines: `<200` lines = short paper (read all at once); `200-600` = medium (read in 2-3 chunks); `>600` = long (read in 4+ chunks). Plan your reading strategy accordingly.

---

## Phase A2: Paper Structure Analysis

Read through the extracted text and identify:

### 2.1 Metadata
- Title, authors, institutions
- Venue (arXiv ID, conference, journal)
- Date of publication

### 2.2 Structural sections
Academic CS papers typically follow this pattern. Identify which sections exist:
- Abstract / Introduction
- Background / Related Work
- Design / Architecture / Methodology
- Implementation / Experiments
- Results / Analysis / Evaluation
- Discussion / Limitations
- Future Work / Open Questions
- Conclusion
- Appendix

### 2.3 Content patterns to recognize
As you read, identify which of these patterns exist in the paper (this will determine which HTML components to use):

| Pattern | Look for |
|---------|----------|
| **Core thesis/argument** | The paper's main claim, usually in abstract and introduction |
| **Key metrics** | Numbers, percentages, counts that quantify results (need ≥5 to use dashboard) |
| **Values/philosophies** | 3+ guiding principles, design philosophies, or motivations |
| **Design principles/rules** | 5+ enumerated rules, principles, or guidelines (especially with tags/categories) |
| **System architecture** | Description of components, layers, data flow, subsystem decomposition |
| **Code/pseudocode** | Algorithms, code snippets, API descriptions |
| **Layer/level descriptions** | Hierarchical structures — layers, tiers, levels with responsibilities |
| **Comparison/contrast** | Side-by-side comparison between systems, approaches, or designs |
| **Tensions/tradeoffs** | Value conflicts, design tensions, trade-off matrices |
| **Empirical evidence** | Citations of studies, experiments, surveys with specific data |
| **Mathematical formulas** | Equations, formal definitions, loss/cost functions, probability expressions, matrices |
| **Future directions** | 3+ open questions, future work items, or research directions |
| **Taxonomy/classification** | Categorization system — types, categories, taxonomies |
| **Methodology notes** | How the research was conducted, evidence tiers, limitations |
| **Figures/diagrams** | Architecture diagrams, flowcharts, system overviews, taxonomy illustrations, key charts |
| **Recurring patterns** | Cross-cutting themes or design commitments that recur across subsystems |

---

## Phase A3: Content-to-Component Mapping

Based on what patterns you found in Phase A2, decide which components to render. **Only include components whose corresponding content patterns exist in the paper.**

| If paper has... | Render this component | Notes |
|-----------------|----------------------|-------|
| Metadata | `.meta-row` | Always. 4 fields: authors, institution, method, key finding |
| Core thesis | `.callout.info` | Always. Capture the paper's central argument |
| ≥5 quantifiable metrics | `.summary-grid` | Dashboard of key numbers |
| 3+ values/philosophies | `.grid-2 > .mini-card` | Each value gets a card with description |
| 5+ design principles | `.pbox` numbered list | Each with name, tags (which values), one-line explanation |
| Architecture description | `table` (design questions/answers/alternatives) | 3-5 key architectural questions |
| Layered/hierarchical structure | `table` (layer/component/responsibility/files) | 4-7 layers or components |
| Code snippets | `<pre>` with syntax highlighting | Use `.c` `.kw` `.fn` `.s` `.num` classes |
| Mathematical formulas | `$...$` / `$$...$$` with KaTeX rendering | Inline via `$...$`, display via `$$...$$` in `.formula-display` block |
| Comparison between systems | `table` (dimension/A/B) | 4-8 comparison dimensions |
| Value tensions/tradeoffs | `table` (value-pair/tension/evidence) | 3-6 tension pairs |
| Empirical evidence citations | `ul` with study details | Cite specific papers and numbers |
| 3+ future directions | `.grid-2 > .mini-card` | Each direction as a numbered card |
| Taxonomy/classification | `table` (category/examples/pattern) | |
| Methodology description | `table` + `ul` | Evidence tiers, limitations |
| Key figures/diagrams | `figure.paper-fig` (base64, with lightbox) | Architecture diagram, system overview, taxonomy illustration, key chart |
| Cross-cutting patterns | `.grid-2 > .mini-card` | For recurring design commitments |
| Conclusion/takeaways | `.callout.success` series (3-5) | Synthesize key insights |
| ≥8 data points total | Summary `table` (metric/value/meaning) | End-of-document data recap |

### Component reading

Before generating HTML, read these reference files:

1. Read `assets/template.html` — this is your starting point. The complete CSS/JS is already inlined. Your job is to fill in the `<!-- SECTION: xxx -->` placeholders with paper-specific content.
2. Read `references/component-catalog.md` for detailed component templates if you need them for specific patterns.
3. Reference `references/design-system.md` if you need to understand a CSS variable or add custom styles.

---

## Phase A4: HTML Generation (Template-Driven)

### A4.0 Choose the right template

Two templates are available in `assets/`, selected based on the annotation language chosen in Phase 0b:

| Template | Language | When to Use | Key Differences |
|----------|----------|-------------|-----------------|
| `assets/template.html` | Chinese (default) | User chose **Chinese** annotation language | Badge: "论文精读"; sidebar labels in Chinese; meta row labels (作者/机构/方法/核心); callout titles; section headings; code copy button text (复制/已复制); footer; lightbox tooltips |
| `assets/template_en.html` | English | User chose **English** annotation language | Badge: "Paper Reading"; sidebar labels in English; meta row labels (Authors/Institution/Method/Key Finding); all UI text in English; code copy button text (Copy/Copied); footer; lightbox tooltips |

**Rule**: Always select the template that matches the annotation language. Do not mix — e.g., do NOT use the Chinese template to produce an English-language reading note, as sidebar labels, button text, and figure captions would remain in Chinese.

### A4.1 Start from the template

Copy the chosen template to your output path:
```
cp "<skill-dir>/assets/template.html" "<output-dir>/<paper-short-name>_reading_notes.html"
# OR for English:
cp "<skill-dir>/assets/template_en.html" "<output-dir>/<paper-short-name>_reading_notes.html"
```

### A4.2 Fill content placeholders

The template uses `<!-- SECTION: NAME --> ... <!-- /SECTION: NAME -->` comments to mark insertion points. Work through each SECTION block and replace the placeholder text with actual paper content:

| Placeholder | What to fill |
|---|---|
| `[PAPER_TITLE]` etc. in top-bar + intro | Paper metadata |
| `SECTION: INTRO_*` | Paper title, subtitle, meta-row, core thesis callout |
| `SECTION: TLDR_*` | Summary grid metrics + one-liner |
| `SECTION: FIGURES` (optional gallery) | Optional consolidated view. Do NOT put all figures here. See below. |
| Figures (inline, between sections) | Embed each `<figure class="paper-fig">` in the section where it is most contextually relevant. See **figure placement rule** below. |
| Formulas (inline) | Use `$...$` within `<p>` or `<span class="formula-inline">` — auto-rendered by KaTeX |
| Formulas (display) | Use `$$...$$` within `<div class="formula-display">` — auto-rendered by KaTeX |
| `SECTION: SIDEBAR_*` | Adjust sidebar links to match the actual sections you create |
| Between SIDEBAR and TAKEAWAYS | Add/remove `.section` blocks based on Phase A3 mapping |
| `SECTION: TAKEAWAYS_*` | 3-5 callout.success insights + data recap table |
| `SECTION: FOOTER` | Paper citation and links |

**Figure placement rule (Pipeline A)**: After filling the placeholder sections, go back and insert `<figure class="paper-fig">` blocks directly into content sections where each figure is most relevant:

| Figure | Best placement |
|--------|---------------|
| Architecture overview (Fig 1) | In the intro section, after the core thesis callout |
| Taxonomy / classification | In the taxonomy / classification section |
| System comparison | In the comparison section |
| Workflow / pipeline | In the corresponding mechanism section |
| Results / evaluation charts | In the experiments / results section |

This means deleting `<!-- SECTION: FIGURES -->` if all figures are placed inline. The optional gallery is only for residual figures or quick-reference thumbnails.

### A4.3 Select content sections

Based on your Phase A3 content-to-component mapping, keep only the `.section` blocks that match the paper's actual content. Delete unused template section blocks. Add new ones if the paper has content patterns not covered by the defaults.

Template provides pre-built section blocks for: values (mini-cards), principles (pboxes), architecture (tables), mechanisms (tables + code + trace), comparison, discussion (tension matrix + evidence), future directions, methodology.

**Important**: After deleting or adding sections, renumber all `<span class="num">N</span>` elements in `<h2>` headings sequentially (1, 2, 3, ...) to keep section numbering contiguous. Use 📋 (no number) for supplementary/reference sections.

### A4.4 Adjust the sidebar

Update the sidebar `<details>` groups and `<a>` links to match your final set of sections. Each section's `id` must match its sidebar `href`.

### A4.5 Apply enhancement styles (optional)

From `references/design-system.md` Part 5, selectively apply enhancements:
- Add `section-entrance` class to the first 2-3 sections for scroll reveal animation
- Add `card-lift` class to key mini-cards for hover depth
- Use `accent-gradient` on the progress bar for a polished accent bar
- Add `bg-texture` to `<body>` for subtle paper-like texture

### A4.6 Content translation

All explanatory text must be in the **user's chosen annotation language** (from Phase 0b). Preserve technical terms, code identifiers, author names, and numerical values in original form regardless of language choice.

- If **Chinese**: section titles, callout titles, table headers, figure captions in Simplified Chinese
- If **English**: all of the above in English
- Either way: `<html lang="...">` attribute must match the chosen language

### A4.7 Quality Check

Before declaring the output complete, verify:

1. **CSS completeness**: All 6 semantic color families have both light and dark variables
2. **JS completeness**: Progress bar, back-to-top, IntersectionObserver sidebar highlight, theme toggle + localStorage persistence, print handler, entrance animation, lightbox (click-to-zoom + keyboard nav), mobile sidebar toggle, code block copy button, table horizontal scroll detection — all 10 features present
3. **Sidebar**: Links match section IDs, all `<details>` are `open`
4. **Print styles**: `@media print` hides sidebar, top-bar, progress-bar, btt; reveals all entrance-animated sections
5. **Content accuracy**: Compare key claims and numbers against the extracted paper text
6. **No orphan components**: Every rendered component corresponds to actual paper content
7. **Language consistency**: All user-facing text is in the chosen annotation language (Chinese or English). No mixed-language annotations except preserved terms.
8. **No leftover placeholders**: No `[PLACEHOLDER_TEXT]` remains in the output
9. **Base64 integrity**: Open the HTML in a browser; all figures render without broken-image icons. Each `<img src="data:image/png;base64,...">` is well-formed
10. **Image sizing**: No inline image exceeds 100% container width or 500px height; `max-width` and `max-height` CSS constraints are in effect
11. **Lightbox functional**: Clicking any `figure.paper-fig img` opens the lightbox overlay displaying the full-resolution image
12. **Lightbox dismiss**: The lightbox closes on × button, backdrop click, and Escape key
13. **Gallery navigation**: With 2+ figures, prev/next arrows and ArrowLeft/ArrowRight keyboard keys navigate between them
14. **Dark mode images**: Toggle dark mode; images have visible borders (`border-color:#334155`) and are not washed out against the dark background
15. **Print images**: Print preview shows images at reasonable size (`max-height:300px`); lightbox overlay is hidden
16. **Lazy loading + caption**: Every `figure.paper-fig img` has both `loading="lazy"` and `data-caption` attributes; `data-caption` matches its `figcaption` text
17. **Figure cropping quality**: Each embedded figure is an individual cropped image (not a full-page render). Verify by checking that figures don't contain surrounding body text, page headers, or footnotes — the image should show only the diagram/figure itself
18. **Formula rendering**: All `$...$` and `$$...$$` formulas render correctly when KaTeX loads; check for `\` command typos and unmatched braces
19. **Formula normalization**: Any pdftotext-mangled symbols (e.g., ∑ → `Sigma`) have been corrected back to proper LaTeX
20. **Formula explanation**: Every display formula (`$$...$$`) is followed by an explanation in the user's chosen annotation language
21. **KaTeX fallback**: When the CDN is unavailable, `.formula-inline` and `.formula-display` fallback styles show readable monospace content
22. **Mobile sidebar toggle**: On viewports <960px, sidebar is hidden and ☰ button appears at bottom-right. Tapping opens sidebar as overlay with semi-transparent backdrop. Tapping backdrop closes it.
23. **Code copy button**: Hovering over any `<pre>` block reveals a "复制" button at top-right. Clicking copies the code to clipboard and shows "已复制" for 1.5s. Falls back gracefully if clipboard API is unavailable.
24. **Table scroll indicator**: When a table overflows its container, a gradient fade appears on the right edge to indicate scrollability. Disappears when fully scrolled.
25. **Section flash on :target**: When navigating to a section via anchor link (sidebar or h2 anchor), the section briefly flashes with a blue highlight (`section-flash` animation) to orient the reader.
26. **No intermediate file references**: The final HTML is self-contained (CSS/JS inline, images as base64 data URIs). Grep for any local file paths that might have leaked — there should be no references to `paper_text.txt`, `figures_b64.json`, `section_*.html`, or `assembled_body.html`.

### Phase A5: Post-Verification Cleanup

After the HTML passes all quality checks, delete all intermediate files:

```bash
rm -f <output-dir>/paper_text.txt \
      <output-dir>/figures_b64.json \
      <output-dir>/fix_figures.py \
      <output-dir>/redistribute_figures.py
```

**What to keep**: Only `<paper>_reading_notes.html` — the self-contained final output.

**Biggest space savings**: `figures_b64.json` (1–5MB). Once figures are base64-embedded in the HTML, this file serves no purpose — the HTML never references it.

**Caution**: Open the HTML and verify all figures render before deleting `figures_b64.json`. If you need to re-extract a mis-cropped figure later, you'll have to re-run `extract_figures.py`.

---

# Pipeline B: Parallel (Ultracode)

Multi-agent parallel pipeline. Requires Ultracode mode (user says "ultracode" or session has it enabled). Suited for long papers, surveys, and content-rich papers where a single agent's output would be constrained by context window or attention.

```
Parallel Extraction (2 agents) → Structure Split (main) → Parallel Writing (N agents) → Assembly (main)
```

## Phase B1: Parallel Extraction

Launch two agents simultaneously via `parallel()`. Both are read-only — they extract structured data from the PDF, not write HTML.

### Agent 1: Figure Extractor

Uses caption-driven drawing density cropping. Zero extra dependencies.

```bash
python "<skill-dir>/scripts/extract_figures.py" "<pdf-path>" --dpi 200 -o "<output-dir>/figures_b64.json"
```

Then read the **summary + metadata** from `figures_b64.json` (not the base64 strings themselves — these are 1-5MB). Output a structured mapping:

```json
{
  "fig_1": {"base64": "...", "caption": "Fig. 1. Overview of...", "page": 3, "width": 1156, "height": 572},
  ...
}
```

### Agent 2: Formula Extractor

Scan the full extracted text (`paper_text.txt`) for mathematical formulas. Normalize to LaTeX, identify which section each formula belongs to, and output:

```json
{
  "formulas": [
    {"id": "eq1", "latex": "a_t \\sim \\pi(a_t \\mid s_t, h_t, \\theta_u)", "section": "2.2", "context": "The agent's behavior can be abstracted as a policy..."},
    ...
  ],
  "formula_count": 6,
  "sections_with_formulas": ["2.1", "2.2", "5.1"]
}
```

If the paper has no formulas, return `{"formulas": [], "formula_count": 0}`.

### Merge Results

After both agents complete, the main agent merges their output into a unified resource map:

```json
{
  "figures": {...},
  "formulas": {...},
  "paper_title": "...",
  "total_pages": 35
}
```

## Phase B2: Structure Analysis & Section Assignment

The main agent analyzes the paper text and divides it into **N sections** (typically 4–8). Each section is a self-contained unit with its own text, figures, and formulas.

### Section Assignment Schema

```json
[
  {
    "id": "foundations",
    "num": 1,
    "title": "Foundations and Formalization",
    "text": "<full text of this section from the PDF>",
    "figures": ["1"],
    "formulas": ["eq1", "eq2", "eq3"],
    "component_hints": ["callout.info", "grid-2", "table", "formula-display"]
  },
  {
    "id": "profile",
    "num": 2,
    "title": "Profile Modeling",
    "text": "<full text of this section from the PDF>",
    "figures": [],
    "formulas": [],
    "component_hints": ["table", "grid-2", "callout.warn"]
  },
  ...
]
```

**Rules for section division:**
- Follow the paper's own heading structure (Section 2, Section 3, etc.)
- Combine short adjacent sections if needed (e.g., "Discussion + Future Work" → one section)
- Target 2000–4000 Chinese characters per section for optimal sub-agent output
- Assign figures to the section where they are first referenced in the body text
- Assign formulas to the section where they are defined (not just cited)
- `component_hints` guide the sub-agent on which HTML components to use

## Phase B3: Parallel Section Writing

Launch **N agents** via `pipeline(sections, writeSection)`. Each agent receives its section assignment (text + figures + formulas + component hints) and outputs a complete HTML section block.

### Sub-Agent Prompt Template

Each sub-agent receives this prompt structure:

```
You are writing ONE section of an academic paper reading note in {annotation_language}.

## Your Section
- Section number: {num}
- Section ID: {id}
- Section title: {title}

## Paper Text for This Section
{text}

## Figures Available (use placeholders, NOT base64)
DO NOT embed base64 image data. Use placeholders instead:
  <!-- FIG:1 -->
  <!-- FIG:3 -->
Available figures for this section: {figure_id_list}
Caption reference: {figure_captions}

## Formulas to Embed
{formulas_with_latex}

## HTML Components You Should Use
{component_hints}

## Component Reference (inline catalog)
{Insert the full Inline Component Catalog from the section below — all 22 components with their HTML snippets and usage notes.}

## Content Rules
1. Write in {annotation_language} (user's choice from Phase 0b). Preserve technical terms, author names, numbers.
2. Insert figures ONLY as `<!-- FIG:N -->` on its own line. NEVER use `<figure>`, `<img>`, or base64.
   Each figure should appear AT MOST ONCE per section.
3. Embed formulas inline (`$...$`) or as display blocks (`$$...$$`). Follow display formulas with an explanation in the user's chosen annotation language.
4. `<strong>` is INLINE — always inside `<p>` or `<li>`. Never standalone.

## Depth Requirements (MANDATORY)
5. **Inverted pyramid**: Open each subsection with the conclusion or framework, then explain.
6. **Mandatory insights**: Include at least 2 of the following callout types:
    - `.callout.purple` — design motivation (WHY this design choice)
    - `.callout.warn` — cross-section connection (how this ripples through the paper)
    - `.callout.success` — practical takeaway (what a builder must get right)
    - `.callout.danger` — critical observation (a limitation the paper doesn't discuss)
7. **Two-layer structure**: ~60% summary (tables, `.callout.info`, plain text) + ~40% insight callouts.
8. **Component intent**: Choose the component that matches what you're trying to SAY, not just what fits the data shape.
```

### Inline Component Catalog for Sub-Agents

Include this catalog in every sub-agent prompt:

```
.callout — 6 types, each with a specific intent:
  .info     — 📌 "Here's what the paper claims" (summary layer)
  .purple   — 🏗️ "Here's WHY they designed it this way" (design motivation, insight layer)
  .warn     — ⚠️  "This choice creates a tension with X" (trade-off, cross-section link)
  .success  — ✅ "Here's what you should do" (actionable takeaway, insight layer)
  .danger   — 🚨 "Here's a risk the paper doesn't discuss" (critical observation, insight layer)
  .cyan     — 💡 "Methodology note / clarification" (supplementary, either layer)
  <div class="callout info"><strong>📌 Title</strong><p>Body</p></div>

table — neutral data presentation ("here's what they found")
  <table><tr><th style="width:20%">Col</th><th>Col</th></tr>
  <tr><td><strong>Row</strong></td><td>Content</td></tr></table>

.grid-2 — compare/contrast parallel concepts at a glance
  <div class="grid-2"><div class="mini-card card-lift">
  <strong>Title</strong><p>Description</p></div>...</div>

.pbox — numbered principle/rule
  <div class="pbox"><div class="pn">1</div><div class="pb">
  <strong>Title</strong><span class="tag bl">Tag</span>
  <p>Explanation</p></div></div>

.tag — inline badge (6 colors: .bl .gr .or .rd .pu .cy)
  <span class="tag bl">Label</span>

.formula-display / .formula-inline — KaTeX math (always follow with an explanation in the user's chosen annotation language)
  <div class="formula-display">$$\sum_{i=1}^n x_i$$</div>
  <span class="formula-inline">$E = mc^2$</span>

figure placeholder — use a comment tag, NOT <figure>/<img>/base64
  <!-- FIG:N -->
  Place on its own line. The assembly step replaces it with the actual figure HTML.

Key CSS classes: .summary-grid (metrics dashboard), .callout (6 types with intent mapping),
  .grid-2/.grid-3 (cards), table, .pbox, .tag, .formula-display, .formula-inline,
  .mini-card, .card-lift
```

### File Output Instructions (CRITICAL — placed at end intentionally)

⚠️ **DO NOT return HTML in your response.** Your response goes through a structured JSON schema
that ONLY accepts `{section_id, num, title, file_path}` — it will reject raw HTML.

Append this verbatim to every sub-agent prompt:

```
---BEGIN FILE OUTPUT INSTRUCTIONS---
CRITICAL: You MUST save your section HTML to a file, then return metadata.
Do NOT return HTML in your response body.

1. Write your section HTML using the Write tool to: <output-dir>/section_{id}.html

   The file must contain exactly this structure:
   <div class="section" id="{id}">
   <h2><span class="num">{num}</span> {title}</h2>
   ... (all section content: paragraphs, callouts, tables, <!-- FIG:N --> placeholders) ...
   </div>

2. AFTER writing the file, set your structured output to:
   {section_id: "{id}", num: {num}, title: "{title}", file_path: "<output-dir>/section_{id}.html"}

IRON RULES:
- First line of the file MUST be: <div class="section" id="{id}">
- Last line of the file MUST be: </div>
- Figures ONLY as <!-- FIG:N --> on its own line. NEVER use <figure>, <img>, or base64.
- <strong> is INLINE — always inside <p> or <li>. Never standalone. No <br> around it.
- Do NOT include <html>, <head>, <body> tags in the file.
---END FILE OUTPUT INSTRUCTIONS---
```

#### CLEAN SECTION CONTRACT (Execute Immediately After Writing):

Each sub-agent MUST execute the following validation after writing `section_{id}.html` and before returning JSON:

```python
import re
content = open('<output-dir>/section_{id}.html').read()
strip = content.strip()
assert strip.startswith('<div class="section"'), f'FAIL: missing section open tag'
assert strip.endswith('</div>'), f'FAIL: missing section close tag'
assert content.count('<div class="section"') == 1, f'FAIL: nested section divs detected'
# Count div balance (excluding the outer section div itself)
inner = re.sub(r'^<div class="section"[^>]*>\s*', '', content)
inner = re.sub(r'\s*</div>\s*$', '', inner)
opens = inner.count('<div ')
closes = inner.count('</div>')
assert opens == closes, f'FAIL: div balance (open={opens}, close={closes})'
```

If any assertion fails, **the entire section file MUST be rewritten** — do NOT attempt to Edit it manually.

**Severity Note**: Clean Section Contract violations are the most severe pipeline errors. A single unbalanced div will corrupt the entire content area of the final HTML, and the cost of repair far exceeds rewriting the section. Therefore, rewriting is mandatory on failure — no exceptions.

**Why this works**: 8 sections × ~25KB HTML = ~200KB would flood the main context.
By writing to files, each sub-agent returns only ~50 bytes of metadata. The main
context stays lean. The structured JSON schema in the Workflow `agent()` call was
already changed to accept `{section_id, num, title, file_path}`, so raw HTML will be
rejected by the schema validator.

### Parallel Execution

`buildSubAgentPrompt(section)` is a helper you construct: fill the prompt template from "Sub-Agent Prompt Template" above with the section's `{num}`, `{id}`, `{title}`, `{text}`, `{figure_id_list}`, `{figure_captions}`, `{formulas_with_latex}`, `{component_hints}`, and the inline component catalog. The template is provided above — your implementation substitutes the placeholders.

**Critical design**: Sub-agents must NOT return full HTML through the pipeline. Instead, each sub-agent writes its section HTML to a file during execution (sub-agents have full tool access, including Write), and returns only a lightweight file reference. This keeps the main context free of ~200KB of accumulated HTML.

```javascript
// In the Workflow script:
phase('Section Writing')

const results = await pipeline(
  sectionAssignments,
  (section) => agent(buildSubAgentPrompt(section), {
    label: `write:${section.id}`,
    phase: 'Section Writing',
    schema: {
      type: 'object',
      properties: {
        section_id: { type: 'string' },
        num: { type: 'integer' },
        title: { type: 'string' },
        file_path: { type: 'string' }
      },
      required: ['section_id', 'num', 'title', 'file_path']
    }
  })
)
```

Each agent runs independently. `pipeline()` means all N sections are processed concurrently (limited by the pool cap of ~10).

**Sub-agent must include in its instructions**: after writing the section HTML, use the Write tool to save the section block to `<output-dir>/section_{id}.html`, then return the file path. The section file should contain exactly:

```html
<div class="section" id="{id}">
<h2><span class="num">{num}</span> {title}</h2>
... (all content, with <!-- FIG:N --> placeholders) ...
</div>
```

### Phase B3.5: Quality Review (optional but recommended)

Before assembly, run a review pass to catch sub-agent errors before they become expensive to fix. Launch **1 reviewer agent** with this prompt:

```
You are reviewing N sections of an academic paper reading note for quality.

Sections: {sections_meta_json}
Original paper text: Read paper_text.txt in the same directory.

For EACH section:
1. Read section_{id}.html from {output_dir}
2. Read the corresponding portion of paper_text.txt

Check:
- Content accuracy: Are key claims in the section ACTUALLY in the paper text? Flag any unsupported claims.
- Coverage: Were important subsections or findings from the paper text missed?
- Depth: Count insight callouts (.callout.purple/.warn/.success/.danger). Must have ≥2.
- HTML validity: Tags properly closed? No orphan elements? Wrapping <div> present?
- **Div balance (CRITICAL)**: Read each `section_{id}.html` and validate:
  - Exactly 1 `<div class="section" ...>` opening tag
  - Inner `<div>` count == `</div>` count
  - If imbalance found, set `fixes_needed: true` — do NOT attempt Edit repair
- Figure refs: Are all <!-- FIG:N --> placeholders referencing figures that exist? No broken references?

Output a structured report:

{
  "review": [
    {
      "section_id": "section_id",
      "accurate": true/false,
      "coverage": "high/medium/low",
      "insight_count": 3,
      "issues": ["specific issue description"],
      "fixes_needed": true/false
    }
  ]
}

Then fix issues inline where possible:
- Minor (typo, formatting): Edit section_{id}.html directly with Edit tool
- Major (missing content, fabricated claims, <2 insight callouts): Mark fixes_needed: true
```

After the reviewer completes, if any section has `fixes_needed: true`, launch a new sub-agent to re-write that section. Use the corrected instructions and the reviewer's `issues[]` as guidance for what to fix. The new sub-agent overwrites the old `section_{id}.html`. At most one retry per section.

## Phase B4: Assembly

B4 spans **four execution boundaries**: inside the Workflow script → main agent file operations → Python shell → final agent. This avoids accumulating large HTML or base64 data in the LLM context at any step.

```
┌── WORKFLOW SCRIPT ───────────────────────────────────┐
│ B4a. Collect section metadata from B3 results          │
│   results = [{section_id, num, title, file_path}, ...]│
│   - Return the array as the workflow result            │
│   - No HTML content in context — only file paths       │
│   - This is the last action inside the Workflow        │
└────────────────────────────────────────────────────────┘
                         ↓  exit Workflow
┌── MAIN AGENT (shell, no LLM) ────────────────────────┐
│ # 1. Write sections_meta.json from workflow result    │
│ python -c "import json; json.dump(..., open(...))"     │
│                                                        │
│ # 2. Concatenate section files in num order (NOT alpha)   │
│ # ⚠️  Strip each section's outer <div class="section"> wrapper   │
│ # and wrap uniformly to prevent nesting issues.           │
│ python -c "                                               │
| import re, json                                           │
│ meta = json.load(open('<output-dir>/sections_meta.json')) │
│ ordered = sorted(meta, key=lambda s: s['num'])            │
│ with open('<output-dir>/sections_raw.html','w') as out:   │
│   for s in ordered:                                       │
│     with open(s['file_path']) as f:                       │
│         content = f.read().strip()                        │
│     # Strip the outer <div class="section" id="..."> and </div> │
│     # Keep only the pure inner content                    │
│     inner = re.sub(r'^<div class=\"section\"[^>]*>\\s*', '', content) │
│     inner = re.sub(r'\\s*</div>\\s*$', '', inner)        │
│     # Re-wrap uniformly — one canonical wrapper per section│
│     out.write(f'<div class=\"section\" id=\"{s["id"]}\">\\n') │
│     out.write(inner.strip() + '\\n')                       │
│     out.write('</div>\\n\\n')                              │
│ "                                                         │
│                                                           │
│ ⚠️ CRITICAL: Do NOT use `cat section_*.html` — shell      │
│ glob sorts alphabetically, not by section number.         │
│ section_storage.html would appear before section_taxonomy │
│ even when taxonomy is Section 1 and storage is Section 3. │
│                                                        │
│ # 3. Run figure assembly + div balance validation (zero LLM tokens) │
│ python "<skill-dir>/scripts/assemble_figures.py"                    │
│   --sections <output-dir>/sections_raw.html                         │
│   --figures <output-dir>/figures_b64.json                           │
│   --meta <output-dir>/sections_meta.json                            │
│   --output <output-dir>/assembled_body.html                         │
│   --validate-divs                                                   │
│   --no-renumber                                                     │
│                                                                     │
│ ⚠️  NEVER pass --fix or --force-wrap. If validation fails, abort.   │
│                                                                     │
│ Performs programmatically:                                          │
│   • <!-- FIG:N --> → <figure> with base64 <img>                     │
│   • Structural validation — reports exact issues                    │
│   • Div balance check — FAILS if any section has open>close         │
│   • Prints warnings for leftover placeholders                       │
└────────────────────────────────────────────────────────┘
                         ↓
┌── FINAL AGENT ───────────────────────────────────────┐
│ B4c. Read sections_meta.json and choose the correct    │
│      template based on annotation language:             │
│      - Chinese: assets/template.html                     │
│      - English:  assets/template_en.html                 │
│      Read the chosen template's <head> and <script>     │
│      sections (instructions embedded in HTML comments). │
│                                                         │
│   assembled_body.html (which now contains multi-MB        │
│   of base64 image data after assemble_figures.py).        │
│                                                           │
│   Structural verification (shell, zero LLM context):      │
│   python -c "                                              │
│   import re                                                │
│   html = open('<output-dir>/assembled_body.html').read()   │
│   print('Sections:', html.count('class=\"section\"'))      │
│   print('FIG leftovers:', html.count('<!-- FIG:'))         │
│   "                                                        │
│   Verify: FIG leftovers must be 0. Section count must     │
│   match sections_meta.json length.                        │
│                                                           │
│   1. Read sections_meta.json → build sidebar              │
│      <details> groups with <a href="#{id}">{title}</a>    │
│                                                           │
│   2. Write wrapper files (no base64 in context):           │
│      head.html: template <head> through <body> opening    │
│                 + intro section (title, meta, thesis)     │
│                 + TL;DR section (summary grid)            │
│      tail.html: takeaways section (callouts + table)      │
│                 + footer + <script> + </body></html>      │
│                                                           │
│   3. Assemble (shell, zero LLM context):                   │
│   cat <output-dir>/head.html \                             │
│       <output-dir>/assembled_body.html \                   │
│       <output-dir>/tail.html \                             │
│       > <output-dir>/<paper>_reading_notes.html            │
│                                                           │
│   ⚠️ The agent NEVER reads assembled_body.html with the   │
│   Read tool — it would load multi-MB base64 into context. │
│   All structural checks happen via shell commands.         │
└────────────────────────────────────────────────────────┘

┌── FINAL STRUCTURE VALIDATION (shell, MUST run after cat) ──┐
│ python -c "                                                  │
│ import re, os                                                │
│ html = open('<paper>_reading_notes.html').read()             │
│                                                               │
│ # Check content div balance                                   │
│ cm = re.search(r'<div class=\"content\">(.*?)</div><!-- /content -->', html, re.DOTALL)
│ if cm:                                                        │
│     inner = cm.group(1)                                       │
│     opens = len(re.findall(r'<div\s', inner))                 │
│     closes = inner.count('</div>')                            │
│     assert opens == closes, \                                  │
│         f'CONTENT DIV IMBALANCE: {opens} opens vs {closes} closes' │
│     print(f'✅ Content div balanced: {opens} opens, {closes} closes') │
│                                                                │
│ # Check no nested section divs                                 │
│ nested = len(re.findall(                                       │
│     r'<div class=\"section\"[^>]*>\s*<div class=\"section\"', html │
│ ))                                                             │
│ assert nested == 0, f'NESTED SECTIONS: {nested} found'         │
│ print('✅ No nested sections')                                  │
│                                                                │
│ # Check sidebar-toggle and BTT are outside container           │
│ cont_close = html.find('</div><!-- /container -->')             │
│ toggle_pos = html.find('sidebar-toggle')                        │
│ btt_pos = html.find('id=\"btt\"')                              │
│ assert toggle_pos > cont_close, 'sidebar-toggle inside container' │
│ assert btt_pos > cont_close, 'BTT inside container'             │
│ print('✅ sidebar-toggle and BTT outside container')             │
│ print('✅ STRUCTURAL VALIDATION PASSED')                        │
│ "                                                               │
│                                                                  │
│ ⚠️ If any assertion fails, delete the corrupted <paper>_reading_notes.html,       │
│ abort the process. Do NOT attempt to repair — go back to B3 and regenerate the   │
│ problematic section.                                                              │
└──────────────────────────────────────────────────────────────────┘
```

**Key design decision**: Why the extra shell step outside the Workflow?

The Workflow script is a pure JS sandbox with no filesystem access and no Node.js APIs. It cannot write files, spawn processes, or run Python. So the `<!-- FIG:N -->` → base64 replacement (which involves reading multi-MB JSON + writing multi-MB HTML files) MUST happen outside the Workflow. The boundary is explicit: Workflow returns lightweight metadata → main agent orchestrates the shell steps → final agent reads the clean result.

### Quality Check (B4)

Pipeline B has an inherent limitation: the final agent (B4c) reads pre-written sections and can do structural checks, but **cannot deeply verify every claim**. The B3.5 review phase is the main safeguard for content accuracy.

**What B4c verifies** (structural, no paper text needed):
- No `<!-- FIG:` placeholders remain (assemble_figures.py also reports this)
- Section divs are well-formed, tags properly closed
- h2 numbering is contiguous (1, 2, 3...)
- Section IDs match sidebar hrefs, no duplicates
- All formulas are wrapped in `.formula-display` or `.formula-inline`
- **No intermediate file references** in the final HTML (no paths to `paper_text.txt`, `figures_b64.json`, `section_*.html`, etc.)

**What the human operator should spot-check**:
- Key numbers, names, and claims against the original text
- Section coverage against paper structure

**What requires B3.5 review** (deeper per-section check):
- Each section has ≥2 insight callouts (depth requirement)
- Content accuracy across all subsections
- No orphan components or force-fit patterns

### Phase B5: Post-Verification Cleanup

After the HTML passes all quality checks, delete all intermediate files:

```bash
rm -f <output-dir>/paper_text.txt \
      <output-dir>/figures_b64.json \
      <output-dir>/section_*.html \
      <output-dir>/sections_meta.json \
      <output-dir>/sections_raw.html \
      <output-dir>/assembled_body.html \
      <output-dir>/fix_figures.py \
      <output-dir>/redistribute_figures.py
```

**What to keep**: Only `<paper>_reading_notes.html`.

**Why safe**: The final HTML is fully self-contained — all CSS/JS is inline, all images are base64 data URIs. No `<script src>`, `<img src>`, or `<link href>` points to any of these intermediate files. Verify with a quick grep before deleting:

```bash
grep -c 'paper_text.txt\|figures_b64.json\|section_.*\.html\|sections_raw\|assembled_body' <paper>_reading_notes.html
# Must output 0
```

**Biggest space savings**: `figures_b64.json` (1–5MB) + `assembled_body.html` (~200KB).

---

## Important Rules (Both Pipelines)

- **Adapt, don't force-fit.** If the paper doesn't have design principles, don't create a principles section. Map content to the most natural component.
- **Be thorough but not exhaustive.** Cover the paper's key contributions deeply. Don't enumerate every minor detail.
- **Prioritize insight over transcription.** Don't just copy the paper's text. Synthesize, connect ideas, highlight what matters.
- **One HTML file, zero dependencies.** Everything is inline — no external CSS, JS, fonts, or images. The file must work offline.
- **Dark mode is a first-class feature.** All colors must work in both light and dark themes. Test mentally: would this color be readable on a dark background?
- **In Parallel mode, sub-agents write HTML to files, never return HTML in their response.** Each sub-agent uses the Write tool to save `section_{id}.html` and returns the file path via structured JSON. This keeps the Workflow context lean (~50B per section instead of ~25KB). The component catalog, paper text, figure references, and formula LaTeX are inlined in each sub-agent's prompt — sub-agents should avoid re-reading shared files (template.html, component-catalog.md). If a sub-agent is unsure about a component pattern, it may read `references/component-catalog.md` once.
- **Working directory encoding**: If your paths contain non-ASCII characters (Chinese, spaces, etc.), Python subprocess calls may encounter encoding issues. Mitigation: (a) pass `--output` with an ASCII-only path to Python scripts, (b) set `PYTHONIOENCODING=utf-8` in your shell, or (c) on Windows, use short paths (`dir /x` to find them).
- **Section granularity matters.** Too many tiny sections produce fragmented notes. Too few large sections lose the benefit of parallelism. Aim for 4–8 sections.
- **Clean up after verification.** Once the HTML passes all quality checks (all figures render, no broken references, dark mode works, sidebar links functional), delete all intermediate files. The final HTML is fully self-contained — every image is a base64 data URI, every style and script is inline. Run `grep -c 'paper_text.txt\|figures_b64.json\|section_.*\.html\|assembled_body' <paper>_reading_notes.html` — it must output `0`.
