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
- `<output-dir>` = the directory where the final HTML note will be saved (typically the user's notes directory). All intermediate files are written here.
- `<skill-dir>` = the directory containing this SKILL.md (resolved automatically at runtime)
- `<ascii-work-dir>` = an ASCII-only temporary directory for processing non-ASCII PDF paths (e.g., `<output-dir>` if it is ASCII-safe, or a temporary path like `/tmp/paper-skill/` on Unix / `C:\tmp\paper-skill\` on Windows). Created during pre-flight.

Before presenting the choice, gather the data needed for a good recommendation:

1. **Check dependencies**: Verify PyMuPDF is installed:
   ```bash
   python -c "import fitz; print(fitz.__version__)" 2>/dev/null || echo "MISSING"
   ```
   If missing: `pip install PyMuPDF`. Also check `pdftotext --help` is available.

2. Read `references/component-catalog.md` — all 24 components. Read this FIRST (smaller, needed to understand component patterns before seeing the template).

3. Read the template files in order: `assets/template.html` (HTML shell, ~19KB), `assets/template.css` (all styles, ~29KB), and `assets/template.js` (all JS including annotation engine, ~26KB). The CSS and JS are extracted separately to serve as the **canonical source** — agents must never hand-write CSS or JS. A self-contained `template.html.bak` is also available for reference.

**Pre-flight (Windows + non-ASCII PDF path)**: If the PDF path contains Chinese characters, spaces, or other non-ASCII bytes, **copy the PDF to an ASCII working directory first**. This avoids three concrete failures observed in the field: (a) `pdftotext` subprocess encoding errors on Windows with GBK code page, (b) Claude Code Bash auto-mode declining non-ASCII paths (one report: 3 consecutive denials before workaround), (c) downstream script path-quoting bugs across `cmd`/`bash`/`subprocess`.

   ```bash
   python -c "
   import shutil, os
   src = r'<original-pdf-path-with-chinese>'
   dst = r'<ascii-work-dir>/paper.pdf'
   os.makedirs(os.path.dirname(dst), exist_ok=True)
   shutil.copy(src, dst)
   print(dst)
   "
   ```

   Use the printed ASCII path as `<pdf-path>` in all subsequent steps. The output directory (`<output-dir>`) can still be non-ASCII — only the **PDF input path** needs normalization, because outputs are written by Python with explicit `encoding='utf-8'`.

   Skip this step if your PDF path is already ASCII (most arXiv downloads, English filenames, etc.).

4. Extract PDF text. Prefer `pdftotext -layout` (fast, UTF-8 output). If unavailable, use PyMuPDF fallback below. **Always write to file directly — do NOT use shell `>` redirection** (breaks Unicode on Windows with GBK encoding).

   ```bash
   # Option A: pdftotext (writes UTF-8 by default)
   pdftotext -layout "<pdf-path>" "<output-dir>/paper_text.txt"

   # Option B: PyMuPDF fallback (explicit UTF-8, avoids shell redirection)
   python -c "
   import fitz, os
   os.environ['PYTHONIOENCODING'] = 'utf-8'
   doc = fitz.open('<pdf-path>')
   with open('<output-dir>/paper_text.txt', 'w', encoding='utf-8') as f:
       for page in doc:
           f.write(page.get_text())
   "
   ```

   After extraction, verify: if `wc -l` shows <50 lines AND `python -c "import fitz; print(fitz.open('<pdf-path>').page_count)"` also shows <2 pages, the PDF is likely unreadable (scanned, encrypted, or corrupted). Warn the user and ask whether to proceed.

5. **Quick pre-check for figures**: Before running the full extractor, scan for standard figure captions:

   ```bash
   python -c "
   import fitz
   doc = fitz.open('<pdf-path>')
   has_fig = any('Fig.' in page.get_text() or 'Figure' in page.get_text() for page in doc)
   print('HAS_FIGURES' if has_fig else 'NO_FIGURES')
   "
   ```

   - If `NO_FIGURES`: skip `extract_figures.py` entirely. Note: "论文可能无图表或使用非标准 caption 格式，跳过图表提取。"
   - If `HAS_FIGURES`: proceed with step 5b below.

5b. Run `scripts/extract_figures.py` to get page count and figure count. **Read only the stdout summary** (page count, figure count, method breakdown) — do NOT read the full JSON file which contains multi-MB base64 strings. If the script reports 0 figures, note this for the user; the paper may have no figures or use non-standard caption formats.

6. **Hard guard**: If `pages ≥ 50` and Ultracode is NOT available, warn the user that Pipeline A risks context overflow and quality degradation. Proceed only with user acknowledgment.

6.5. **Detect paper type** from the extracted text. Read the abstract and section headings, then classify the paper into one of the following types. This classification is used in Phase 0b to recommend an organization strategy.

   | Type | Signals (any 2+ confirm) | Typical Structure |
   |------|--------------------------|-------------------|
   | **system** | "we built", "we implemented", "architecture", "system design", "deployed", named system/framework, architecture diagram as Fig 1 | Intro → Design/Architecture → Implementation → Evaluation → Related Work → Conclusion |
   | **algorithm** | "we propose", "our method", formal problem statement, pseudocode/algorithm listing, theorem/proof, convergence analysis, benchmark tables | Intro → Problem Formulation → Proposed Method → Theoretical Analysis → Experiments → Related Work → Conclusion |
   | **survey** | "we survey", "taxonomy", "literature review", "categorize", "landscape", structured comparison tables, classification diagrams | Intro → Background → Taxonomy → Category-by-Category Analysis → Comparison → Open Challenges → Conclusion |
   | **empirical** | "we measure", "we evaluate", "benchmark", "dataset", "user study", "A/B test", "reproducibility", hypothesis testing, statistical significance | Intro → Methodology/Study Design → Results → Analysis/Discussion → Threats to Validity → Conclusion |
   | **position** | "we argue", "we envision", "roadmap", "grand challenge", "manifesto", "call to action", few/no experiments, normative language | Intro → Problem Statement → Argument/Position → Evidence/Examples → Implications → Conclusion |

   **Detection process**:
   1. Scan the abstract for signal phrases from the table above. Assign confidence scores (0-1) for each type.
   2. Scan the top-level section headings for structural clues (e.g., "Architecture" → system, "Theoretical Analysis" → algorithm, "Taxonomy" → survey).
   3. Pick the type with the highest combined score. If ambiguous (two types within 0.2 of each other), note both and let the user resolve in Phase 0b.
   4. Apply the same content pattern signals that will later be used in Phase A2: architecture descriptions reinforce "system", taxonomy/classification reinforces "survey", mathematical formulas without system architecture reinforce "algorithm".

6.6. **Pre-extract formulas** before structure analysis. Scan the full extracted text for mathematical formulas. This step runs BEFORE any section reorganization so that formulas can be located by their original PDF context. Generate structured data:

   ```json
   {
     "formulas": [
       {"id": "eq1", "latex": "a_t \\sim \\pi(a_t \\mid s_t, h_t, \\theta_u)", "page": 3, "context": "The agent's behavior can be abstracted as a policy..."},
       ...
     ],
     "formula_count": 6,
     "sections_with_formulas": ["2.1", "2.2", "5.1"]
   }
   ```

   - For papers with <5 formulas: manually transcribe each formula to LaTeX from the rendered PDF page.
   - For papers with 5-15 formulas: transcribe critical formulas; for the rest, note page position for later reference.
   - For papers with >15 formulas: use `scripts/extract_figures.py` on formula-heavy pages to capture them as images. Note that formula images won't render in dark mode.
   - The transcribed formulas are immutable source data — regardless of which organization strategy is chosen later, formulas are embedded into the reorganized sections by matching their `context` and `page` fields.

### Phase 0b: Ask the user

Use `AskUserQuestion` to present choices

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
  → Pipeline A is the only option. Skip Q1 (no choice to make),
    inform the user:"仅 Pipeline A（串行）可用", and proceed to Q2.

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

**Question 3 — Organization strategy.** Present all 4 strategies directly. For each, explain the organizational logic and best-use scenario. The Agent MUST recommend a strategy based on the detected paper type and content characteristics from Phase 0a.

| Strategy | Label | Best For | How It Works |
|----------|-------|----------|--------------|
| paper-structure-aligned | 论文结构对齐 | Reviewing or locating content | Follows the paper's own section order for easy cross-reference |
| cognition-first | 认知先行 | First-time reading system/survey/position papers | Problem → Core idea → Design → Results, building a cognitive framework from scratch |
| question-driven | 问题驱动 | First-time reading algorithm/empirical papers | Each section IS a question the paper answers — FAQ style, great for quick evaluation |
| persona-driven | 实践者视角 | Practitioner evaluation | First-person conversational narrative: "Why I read this", "Where I'd be cautious", "When I'd use this" |

**Agent recommendation**: Reference the detected paper type (Phase 0a step 6.5) and specific content features (e.g., system architecture diagrams, taxonomy/classification structure, experiment design, formal proofs) to explain the recommendation.

```
根据这篇论文的类型（{paper_type}）和内容特点（{content_notes}），我的建议：
- 如果你还没读过 → 推荐 **{strategy_a}**（{reason}）
- 如果你已经读过、需要复习/查找 → 推荐 **paper-structure-aligned**
```

**Default**: paper-structure-aligned. If the user does not respond to Q3, this is the fallback.

**Pipeline B warning for persona-driven**: If the user selects persona-driven AND Pipeline B, issue this warning:

```
⚠️ persona-driven 策略需要统一的叙事人格，并行模式（Pipeline B）会削弱叙事一致性，
因为多个子代理各自模仿同一人格会产生风格差异。建议切换到 Pipeline A（串行）。

用户可选择：[切换到 Pipeline A] [坚持 Pipeline B（接受风险）]
```

Both pipelines share the same HTML template, component library, figure extractor, and quality checks — they differ in how work is scheduled across agents and how figures are embedded inline (Pipeline A: direct base64; Pipeline B: `<!-- FIG:N -->` placeholders replaced in a post-processing Python step). The chosen organization strategy applies to both pipelines — it controls section ordering and grouping, not the generation method.

**Example combined prompt:**

```markdown
📋 **论文基本信息**：29页，8张图，综述论文

**Q1: 请选择生成模式：**

**Pipeline A（串行）** — 1个Agent
  - 输出风格一致，图直接嵌入对应章节
  - **推荐场景**：短文、公式多

**Pipeline B（并行）** — 5-12个Agent（需Ultracode）
  - 各章节由独立Agent撰写，深度更高
  - **推荐场景**：长文、图表多、综述类

👉 **建议**：推荐Pipeline B（并行）。

**Q2: 请选择注释语言：**

中文（简体） / English

**Q3: 请选择组织策略：**

根据这篇综述论文的内容特点（有清晰的分类体系、8个对比维度），我的建议：
- 如果你还没读过 → 推荐 **cognition-first**（从分类框架入手逐步构建理解）
- 如果你需要快速查找 → **paper-structure-aligned**

| 策略 | 适合 | 组织逻辑 |
|------|------|---------|
| 论文结构对齐 | 复习/查找 | 按论文原章节顺序 |
| 认知先行 ⭐ | 初学综述 | 问题→核心思想→设计→结果 |
| 问题驱动 | 初学算法/实证 | 每节一个问题+答案 |
| 实践者视角 | 评估 | 第一人称叙事 |
```

---

## Content Depth Rules (Both Pipelines)

A reading note is not a translation or summary — it is a **curated analysis**. All sections must follow the four principles below. Full details in [Content Depth Rules](references/content-depth-rules.md).

| Principle | Rule |
|-----------|------|
| **倒金字塔结构** | 每节先给结论/框架，再解释。 |
| **强制洞察类型** | 500+ 字章节必须包含 ≥2 种 callout（purple/warn/success/danger）。 |
| **双层深度** | ~60% 总结层 + ~40% 洞察层。零洞察 callout 的章节为失败。 |
| **按意图选组件** | table = 展示数据；callout.info = 论文主张；callout.purple = 设计动机；callout.warn = 权衡；callout.success = 可操作建议；callout.danger = 风险。 |

**Callout 结构要求**（不可违反）：每个 `.callout.*` 的第一个子元素必须是 `<strong>emoji Title</strong>`，其后跟 `<p>`。禁止自创类名（`.callout-title`, `.callout-body`）。Callout 的排序顺序固定：component 名在前、修饰符在后（如 `class="callout info"` 而非 `class="info callout"`）。

---

## Organization Strategy Reference

四种组织策略的完整定义、章节排序模板和跨策略兼容性详见 [Organization Strategies](references/organization-strategies.md)。

快速参考：

| Strategy | Best For | 说明 | 章节顺序 |
|----------|----------|------|---------|
| **paper-structure-aligned** | 复习/查找 | 按论文原章节顺序 | 与论文一致 |
| **cognition-first** | 初学系统/综述 | 问题→核心→架构→设计→工作→结果→局限 | 重新排序为认知路径 |
| **question-driven** | 算法/实证 | 每节一个核心问题+答案 | 逻辑依赖顺序 |
| **persona-driven** | 实践者评估 | 第一人称叙事："为什么读"→"哪里谨慎"→"何时用" | 叙事弧线 |

**关键规则**：Content mapping 决定**哪些**章节存在；Strategy 决定它们的**顺序**。不要强制内容放入不存在的章节——只改变序列和分组。

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

**If `paper_text.txt` already exists** from Phase 0a step 4, reuse it. Skip to Step 1.2. The Phase 0a extraction already validated line count and performed PyMuPDF fallback if needed. No re-extraction or re-validation is necessary.

**Otherwise** (standalone Pipeline A invocation without Phase 0a), extract via pdftotext:

```bash
pdftotext -layout "<pdf-path>" "<output-dir>/paper_text.txt"
```

Check the result: `wc -l` should show >50 lines for a real paper (same threshold as Phase 0a step 4). If under 50 lines or output is garbled, fall back to PyMuPDF:

```bash
python -c "
import fitz, sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
doc = fitz.open('<pdf-path>')
with open('<output-dir>/paper_text.txt', 'w', encoding='utf-8') as f:
    for page in doc:
        f.write(page.get_text())
"
```

### Step 1.2: Extract paper figures as individual cropped images

**If `figures_b64.json` already exists** (generated by Phase 0a step 5b), skip extraction entirely. Go directly to step 1.2a. Likewise, if Phase 0a detected `NO_FIGURES`, skip extraction and create an empty manifest: `{"figures": [], "summary": [], "total_size_kb": 0}`.

**Otherwise** (no pre-extraction data), run:

Academic papers store figures as **vector graphics** (not raster images), so `page.get_images()` returns only small icons/emoji — not the actual diagrams. The correct approach is **layout-aware caption-driven cropping**, which detects "Fig. N" captions and crops only the figure region above each caption. The skill's built-in extractor handles this automatically — no extra dependencies beyond PyMuPDF:

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

**Step 1.2a: Read the JSON metadata only**: Parse `figures_b64.json` to get figure metadata (page, fig_num, caption, width, height) and the `summary` array. **Do NOT read the full `base64` strings into context** — they are 1-5MB of binary data. Instead, construct data URIs inline when embedding each figure into the HTML:

```
data:image/png;base64,<base64-string>
```

These URIs go into `<img src="...">` attributes. **Each figure should be embedded inline in its most contextually relevant section** (e.g., architecture diagram in the architecture section, comparison chart in the comparison section), not all placed in a single gallery. A separate gallery section is optional for multi-figure papers (see the figure placement rule in Phase A4 and the template comment in `SECTION: FIGURES`).

### Step 1.3: Handle mathematical formulas

**If formulas were already pre-extracted in Phase 0a step 6.6**, skip manual transcription and use the pre-extracted formula data directly. The pre-extracted data provides `{id, latex, page, context}` for each formula — embed them using `$...$` or `$$...$$` in the appropriate content sections. No further transcription is needed.

**Otherwise** (pre-extraction was skipped, incomplete, or Pipeline A was invoked without Phase 0a), follow the options below:

- **Manual transcription** (recommended): For critical formulas, read from the rendered page image (use PyMuPDF to quickly render a preview of the page) and write LaTeX inside `$$...$$` delimiters. This is the preferred approach since it enables KaTeX rendering, searchability, and dark mode support.
- **Figure extraction fallback**: If the formula count is very high (>15) and manual transcription is impractical, use caption-driven cropping (`scripts/extract_figures.py`) to extract the formula-heavy portion of the page as an image. Note that embedded formula images won't render in dark mode or support text search.

### Step 1.4: Assess paper length

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
| Metadata | `.meta-row` (template pre-built) | Always. Template already contains `.meta-row`; `initMeta()` populates it from `<meta>` tags filled in A4.2. No manual editing needed. |
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

### Strategy-Aware Section Ordering

After identifying which sections to include (from the mapping above), order them according to the chosen organization strategy. Refer to the [Organization Strategy Reference](#organization-strategy-reference) for each strategy's ordering rules.

**Key rule**: Content mapping determines WHICH sections exist. Strategy determines their ORDER. You never force content into sections the paper doesn't have — you only change the sequence and grouping.

**Strategy parameter**: `{organization_strategy}` from Phase 0b Q3. Default: `paper-structure-aligned`.

**Section building per strategy**:

| Strategy | Section Building Approach |
|----------|--------------------------|
| paper-structure | Use template pre-built section blocks. Delete unused ones, add new ones as needed (current behavior). |
| cognition-first | Reuse the closest pre-built block where possible (e.g., `#architecture` structure for "Design Decisions" chapter). Merge template blocks when multiple paper sections combine into one thematic unit. |
| question-driven | Build each section from the bare-bones question-section template defined in Organization Strategy Reference. The h2 heading IS the question text. Body uses the same component catalog as other strategies. |
| persona-driven | Same as cognition-first for structure, but use conversational section titles. |

**Figure placement per strategy**: In cognition-first and persona-driven, B2 reassigns figures to the new thematic units. In question-driven, the same figure may appear in multiple questions — the first occurrence gets the full `<figure>`, subsequent ones get a `.fig-ref` cross-reference (handled automatically by `assemble_figures.py` in Pipeline B, or manually in Pipeline A).

### Component reading

Before generating HTML, read these reference files:

1. Read `assets/template.html` (HTML shell), `assets/template.css` (all styles), and `assets/template.js` (all scripts) — these three files together form the complete template.
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

Copy the chosen template and inline CSS/JS assets into it. The template shell (`template.html`) contains `<!-- STYLESHEET -->` and `<!-- SCRIPT -->` placeholders that must be replaced with the canonical CSS/JS from the extracted files.

```bash
# Step 1: Copy template shell to output
cp "<skill-dir>/assets/template.html" "<output-dir>/<paper-short-name>_reading_notes.html"
# OR for English:
cp "<skill-dir>/assets/template_en.html" "<output-dir>/<paper-short-name>_reading_notes.html"

# Step 2: Inline CSS and JS from the canonical source files
# (Never hand-write CSS or JS — always read from the extracted assets)
python -c "
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
out = '<output-dir>/<paper-short-name>_reading_notes.html'
html = open(out, encoding='utf-8').read()
css = open('<skill-dir>/assets/template.css', encoding='utf-8').read()
js  = open('<skill-dir>/assets/template.js', encoding='utf-8').read()
html = html.replace('<!-- STYLESHEET -->', '<style>\n' + css + '\n</style>')
html = html.replace('<!-- SCRIPT -->', '<script>\n' + js + '\n</script>')
open(out, 'w', encoding='utf-8').write(html)
"
```

### A4.2 Fill metadata `<meta>` tags

**CRITICAL**: Before filling section placeholders, fill the `<meta>` tags in `<head>`. These are the canonical source for paper metadata, consumed by `build_manifest.py` and `initMeta()` JS.

```html
<meta name="paper-title" content="[PAPER_TITLE]">
<meta name="paper-type" content="system"><!-- valid: system | algorithm | survey | empirical | position -->
<meta name="paper-authors" content="[AUTHORS]">
<meta name="paper-venue" content="[VENUE]">
<meta name="paper-date" content="[DATE]">
<meta name="paper-institution" content="[INSTITUTIONS]">
<meta name="paper-method" content="[METHOD_SUMMARY]">
<meta name="paper-key-finding" content="[KEY_INSIGHT]">
```

Use the paper type detected in Phase 0a step 6.5. Pick exactly one value: `system`, `algorithm`, `survey`, `empirical`, or `position`.

> ⚠️ **CRITICAL**: The index page generator (`build_manifest.py`) derives its type tags, color bars, and filter buttons from this meta tag. **Leaving `paper-type` empty makes the note uncategorizable in the index.** All 8 meta tags must have non-empty `content`. Verify each one before proceeding.

### A4.3 Fill content placeholders

The template uses `<!-- SECTION: NAME --> ... <!-- /SECTION: NAME -->` comments to mark insertion points. Work through each SECTION block and replace the placeholder text with actual paper content.

> **Note**: Top-bar title/venue/date and `.meta-row` (authors, institution, method, key finding) are auto-populated by `initMeta()` from the `<meta>` tags filled in A4.2. You do NOT need to fill those placeholders — JS handles them. Only fill the placeholders listed below.

| Placeholder | What to fill |
|---|---|
| `<h1>` title in `SECTION: INTRO_HEADING` | Auto-populated by `initMeta()` `paper-title` meta tag. Verify it renders, but no manual editing needed. |
| Core thesis callout in `SECTION: INTRO_OVERVIEW` | `.callout.purple` with paper's key insight |
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

### A4.4 Select, order, and build content sections

Based on your Phase A3 content-to-component mapping AND the chosen organization strategy:

1. **Select**: Keep only the `.section` blocks that match the paper's actual content. Delete unused template section blocks. Add new ones if the paper has content patterns not covered by the defaults.

2. **Order**: Arrange the kept section blocks according to the strategy's ordering rules from [Organization Strategy Reference](#organization-strategy-reference). The template's default section order (Values → Principles → Architecture → Mechanisms → Comparison → Discussion → Future → Methodology) is correct only for `paper-structure-aligned`. Other strategies reorder sections per their cognitive/narrative sequence.

3. **Build per strategy**: Use the section building approach from [Strategy-Aware Section Ordering](#strategy-aware-section-ordering). For question-driven, start each section from the bare-bones template defined in the Organization Strategy Reference.

4. **Regroup sidebar**: Rebuild the sidebar `<details>` groups and `<a>` links to match the strategy's grouping logic — not the template's default four groups. See Organization Strategy Reference for per-strategy sidebar grouping.

5. **Renumber**: After reordering, renumber all `<span class="num">N</span>` elements in `<h2>` headings sequentially (1, 2, 3, ...). Use 📋 (no number) for supplementary/reference sections.

6. **Add strategy marker**: Add a `data-strategy="{strategy}"` attribute to the `<body>` tag:

```html
<body data-strategy="cognition-first">
```

7. **Section titles per strategy**: For question-driven, use the generated question as the h2 heading text. For persona-driven, use conversational titles. For cognition-first, use problem-oriented titles where appropriate.

Template provides pre-built section blocks for: values (mini-cards), principles (pboxes), architecture (tables), mechanisms (tables + code + trace), comparison, discussion (tension matrix + evidence), future directions, methodology.

### A4.5 Rebuild the sidebar from the final section list (HARD REQUIREMENT)

The template's default sidebar contains **placeholder** link text and IDs (核心价值/设计原则/架构总览/核心机制/图示速览/对比分析/讨论与权衡/方法论/未来方向, hrefs `#values`/`#principles`/`#architecture`/etc.). These are scaffolding, not final content. They are the most common source of TOC/section drift bugs.

**Do not** leave any template-default sidebar entry in the output. Treat the template sidebar as 100% throwaway — every `<a>` must be regenerated from the actual section list you ended up with.

Procedure (mandatory):

1. **Enumerate the final section list.** After A4.4 finishes, list every `<div class="section" id="...">` you actually emitted, in document order, with its `<h2>` heading text.
2. **Group sections into 2-4 `<details>` blocks** using the strategy chosen in Phase 1 (see Organization Strategy Reference for per-strategy grouping rules). Group titles: 概览 / 核心分析 / 详细机制 / 扩展讨论 / 参考与总结 (zh) or Overview / Core Analysis / Detailed Mechanisms / Extended Discussion / Reference & Summary (en). Use the same language as the rest of the note.
3. **Build each `<a>` from the section's own data, not from memory:**
   - `href` MUST equal the section's `id` attribute, verbatim (no translation, no abbreviation, no slug rewrite)
   - Visible text MUST be the section's `<h2>` heading text, with the leading numeric prefix (`1` / `2` / `📋` / `📌`) preserved
   - Do not invent new section names that don't correspond to a real h2
4. **If the note has more than 9 sections** (e.g., a 11-section deep paper), the template's default 4-block / 9-slot layout is structurally too small. **Add a new `<details>` block** (e.g., "详细机制" / "Detailed Mechanisms") to hold the overflow sections. Do not drop sections from the sidebar.
5. **Do not keep placeholder entries** like "图示速览（可选）" / "Adjust links based on paper content" HTML comments that ship with the template. Either fill them with real content or delete the whole `<a>` line.

Self-check (must pass before moving to A4.6):

- [ ] For every `<a href="#xxx">` in the sidebar, `id="xxx"` exists somewhere in the document
- [ ] For every section `<div class="section" id="xxx">`, there is exactly one `<a href="#xxx">` in the sidebar
- [ ] The visible text of each `<a>` matches its target h2 heading (substring match, ≥ 4 characters overlap)
- [ ] No template placeholder text ("核心价值" / "设计原则" / "架构总览" / "图示速览（可选）" / "Adjust links based on...") remains in the final HTML unless it coincidentally matches a real h2
- [ ] Total `<a>` count in sidebar == total section `<div>` count (excluding `<div id="math">` if present, which is a formula block not a navigable section)

### A4.6 Apply enhancement styles (optional)

From `references/design-system.md` Part 5, selectively apply enhancements:
- Add `section-entrance` class to the first 2-3 sections for scroll reveal animation
- Add `card-lift` class to key mini-cards for hover depth
- Use `accent-gradient` on the progress bar for a polished accent bar
- Add `bg-texture` to `<body>` for subtle paper-like texture

### A4.7 Content translation

All explanatory text must be in the **user's chosen annotation language** (from Phase 0b). Preserve technical terms, code identifiers, author names, and numerical values in original form regardless of language choice.

- If **Chinese**: section titles, callout titles, table headers, figure captions in Simplified Chinese
- If **English**: all of the above in English
- Either way: `<html lang="...">` attribute must match the chosen language

### A4.8 Quality Check

按 [Quality Checks](references/quality-checks.md) 逐项验证全部 29 项检查。必检项包括：

| # | 检查项 | 严重度 |
|---|--------|:----:|
| 3 | **侧边栏 ↔ 章节对齐（HARD GATE）**：每个 `href` 都必须有对应 `id`，反之亦然；可见文本与 h2 匹配 ≥4 字符；无模板残留文本。所有 `<details>` 必须 `open`。 | 🔴 硬闸 |
| 26 | **无中间文件泄露**：grep 确认无 `paper_text.txt`、`figures_b64.json`、`template.css`、`template.js`、`<!-- STYLESHEET -->` 等路径残留。 | 🔴 |
| 9-17 | **图片渲染**：Base64 无断链、sizing 合规、灯箱功能、暗色模式、打印、懒加载。 | 🟡 |
| 18-21 | **公式渲染**：KaTeX 正确加载、手写 LaTeX 无误、每个 display formula 后带解释。 | 🟡 |
| 1-2, 22-25 | **CSS/JS 完整**：10 个 JS 功能、响应式、复制按钮、滚动表格指示。 | 🟢 |
| 27-29 | **策略标记**：`data-strategy` 存在、章节顺序符合策略、标题风格符合策略。 | 🟢 |

> 上述为缩略清单。完整 29 项见 [Quality Checks](references/quality-checks.md)，每项必须逐条过检。

### Phase A5: Post-Verification Cleanup

After the HTML passes all quality checks, delete all intermediate files:

```bash
rm -f <output-dir>/paper_text.txt \
      <output-dir>/figures_b64.json
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

## Phase B1: Resource Marshalling

Phase 0a already extracted figures (step 5/5b) and formulas (step 6.6). B1 does NOT re-extract — it reads and structures the pre-extracted data for downstream phases.

Launch two agents simultaneously via `parallel()`. Both are read-only.

### Agent 1: Figure Indexer

Read the **summary + metadata** from `figures_b64.json` (generated by Phase 0a step 5b). **Do NOT read the full base64 strings** — they are 1-5MB. Output a structured index:

```json
{
  "fig_1": {"page": 3, "caption": "Fig. 1. Overview of...", "width": 1156, "height": 572},
  ...
}
```

If Phase 0a found no figures (`NO_FIGURES`), return `{}`.

### Agent 2: Formula Pass-Through

Read the pre-extracted formula data from Phase 0a step 6.6. If formulas were transcribed in Phase 0a, pass them through unchanged:

```json
{
  "formulas": [...],
  "formula_count": 6,
  "sections_with_formulas": ["2.1", "2.2", "5.1"]
}
```

If no formulas were found in Phase 0a, return `{"formulas": [], "formula_count": 0}`.

### Merge

After both agents complete, merge into a unified resource map:

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
    "component_hints": ["callout.info", "grid-2", "table", "formula-display"],
    "strategy": "paper-structure-aligned"
  },
  {
    "id": "profile",
    "num": 2,
    "title": "Profile Modeling",
    "text": "<full text of this section from the PDF>",
    "figures": [],
    "formulas": [],
    "component_hints": ["table", "grid-2", "callout.warn"],
    "strategy": "paper-structure-aligned"
  },
  ...
]
```

**Example: cognition-first section assignment** (merged thematic unit):

```json
{
  "id": "design_decisions",
  "num": 3,
  "title": "Key Design Decisions",
  "text": "<merged text from paper Sections 3 and 4>",
  "figures": ["1", "2"],
  "formulas": ["eq3", "eq5"],
  "component_hints": ["table", "callout.warn", "callout.success"],
  "strategy": "cognition-first",
  "position_context": "Section 3 of 6. Preceded by: 'Core Idea'. Followed by: 'How It Works'."
}
```

**Example: question-driven section assignment** (cross-boundary text assembly):

```json
{
  "id": "q3_safety_usability",
  "num": 3,
  "title": "系统如何平衡安全性和用户体验？",
  "text": "<relevant passages from Sections 5 and 11>",
  "figures": ["4"],
  "formulas": [],
  "component_hints": ["table", "callout.warn", "callout.success"],
  "strategy": "question-driven",
  "previously_defined_concepts": ["deny-first evaluation", "permission modes", "graduated trust spectrum"],
  "question_context": "Question 3 of 5. Preceding: Q2 (权限系统如何工作？). Following: Q4 (上下文窗口不够用怎么办？)."
}
```

**Rules for section division — strategy-dependent**:

| Strategy | Section Division Logic |
|----------|----------------------|
| **paper-structure-aligned** | Follow the paper's own heading structure (Section 2, Section 3, etc.). Combine short adjacent sections if needed. |
| **cognition-first** | Merge paper sections into thematic units per strategy template (e.g., Intro + Background → "Problem & Motivation"). Target 5-7 merged sections. When merging, `text` = concatenated text from source sections, `figures` = union of source sections' figure IDs, `formulas` = union of source sections' formula IDs. |
| **question-driven** | (1) Generate 4-8 questions from paper content. (2) For each question, extract relevant text from `paper_text.txt` using grep+Read (two-stage method to avoid context overflow). Do NOT load the entire paper into context. (3) `text` = assembled relevant passages, `figures` = figures referenced in those passages (may overlap across questions). (4) Attach `previously_defined_concepts` — concepts already defined by earlier questions, to prevent re-definition. |
| **persona-driven** | Same merging logic as cognition-first. Additional: `persona_context` field with 1-2 sentence framing guidance for conversational tone. |

**General rules (all strategies)**:
- Target 2000–4000 Chinese characters per section for optimal sub-agent output
- Assign formulas to the section where they are defined (not just cited). Formulas travel with their surrounding text.
- `component_hints` guide the sub-agent on which HTML components to use
- Include `strategy` field in every section assignment JSON entry

## Phase B3: Parallel Section Writing

Launch **N agents** via `pipeline(sections, writeSection)`. Each agent receives its section assignment (text + figures + formulas + component hints) and outputs a complete HTML section block.

### Sub-Agent Prompt Template

子代理的完整提示模板（含策略占位符表、Quick Component Reference、File Output Instructions、Clean Section Contract、Callout Contract、IRON RULES）详见 [Subagent Prompt Reference](references/subagent-prompt-reference.md)。

**B3 执行要点**：
1. 用模板填充章节信息后作为 agent prompt
2. agent 写完 section HTML 后必须执行 Clean Section Contract + Callout Contract
3. 平衡校验失败时必须重写整个文件（禁止 Edit 修复）
4. 输出通过结构化 JSON 返回文件路径，不返回 HTML 原文

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

### Phase B3.5a: Quality Review (optional but recommended)

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
- **Coherence (simplified — cognition-first only)**: Read each section's h2 heading + first paragraph + last paragraph only (not the full section). Check:
  - Does section N's opening naturally follow from section N-1's closing? (count as `transition_breaks`)
  - Are core concept names consistent across section boundaries? (count as `terminology_inconsistencies`)
  - Is the same concept defined in multiple sections? (count as `duplicate_definitions`)

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
  ],
  "coherence": {
    "transition_breaks": 0,
    "terminology_inconsistencies": 0,
    "duplicate_definitions": 0,
    "needs_coherence_pass": false
  }
}

Then fix issues inline where possible:
- Minor (typo, formatting): Edit section_{id}.html directly with Edit tool
- Major (missing content, fabricated claims, <2 insight callouts): Mark fixes_needed: true
```

After the reviewer completes, if any section has `fixes_needed: true`, launch a new sub-agent to re-write that section. Use the corrected instructions and the reviewer's `issues[]` as guidance for what to fix. The new sub-agent overwrites the old `section_{id}.html`. At most one retry per section.

**Coherence gate**: Check `coherence.needs_coherence_pass`:
- If `false` → skip Phase B3.5b entirely, proceed to B4 Assembly. The sub-agents' `position_context` in their B3 prompts was sufficient for natural transitions between sections.
- If `true` → proceed to Phase B3.5b below. At least 2 coherence issues were detected that merit attention.

### Phase B3.5b: Coherence Validation (CONDITIONAL — only if B3.5 reports ≥2 coherence issues)

When the organization strategy is `cognition-first`, run an additional **Coherence Agent** pass after the quality review. This is necessary because parallel sub-agents write their sections independently, but the cognition-first strategy requires a linear narrative arc with natural flow between sections.

**Why needed**: Readers expect a cognitive narrative — "Problem → Core Idea → Design → Results → Limits" — where each section builds on the previous one. Sub-agents writing in isolation cannot ensure this flow.

**Method: Pairwise checking**. The Coherence Agent checks adjacent section pairs rather than reading all sections at once, keeping context consumption bounded.

```
For each adjacent pair (section_i, section_{i+1}):
  1. Read section_{i}.html and section_{i+1}.html
  2. Check:
     - Transition: Does section_{i+1} naturally follow from section_i? Or is there a "jump"?
     - Concept consistency: Are core concepts named the same way in both sections?
     - Definition before use: Are concepts defined in earlier sections before being referenced in later ones?
     - Deduplication: Is the same concept defined in multiple sections? If so, keep the first definition, add a cross-reference in the later one.
     - Claim-evidence chain: Does a claim made in an earlier section have a corresponding evidence mention in a later one?
  3. Fix: Lightweight Edit to inject transition sentences, unify terminology, and remove duplicate definitions.
     Do NOT rewrite content. If sections are severely disconnected, mark rather than repair.

**⚠️ DIV SAFETY RULE (MANDATORY): After ALL Edits to a single section file
are complete, validate div balance before moving to the next file:**

```bash
python -c "
import re
c = open('<output-dir>/section_{id}.html').read().strip()
inner = re.sub(r'^<div class=\"section\"[^>]*>\s*', '', c)
inner = re.sub(r'\s*</div>\s*$', '', inner)
assert inner.count('<div ') == inner.count('</div>'), 'DIV IMBALANCE after coherence edits'
print('OK')
"
```

If the assertion fails: **revert ALL Edits to this file** (not just the last one).
Restore the pre-coherence version of the file. Do NOT attempt to identify which
specific Edit caused the imbalance — the cost of diagnosis exceeds the cost of
reverting. This prevents Coherence Agent edits from introducing structural
corruption into section HTML files.
```

**After pairwise checks**, a final global pass reads only the first paragraph + last paragraph of each section to verify the overall argument chain.

**Output**: A modified set of `section_{id}.html` files with injected transitions and unified terminology.

**Edge case**: If the paper has only 3-4 sections after cognition-first merging, the pairwise approach checks all pairs in 2-3 calls. If it has 7-8 sections, this is 6-7 calls. The cost scales linearly with section count but each call only reads 2 files (~6-10KB total).

### Post-Coherence Validation

After all coherence edits are complete, re-run the **Clean Section Contract** (from Phase B3) on EVERY section file that was modified by the Coherence Agent.

For each modified file:
1. Run the full Clean Section Contract validation (same Python assertions as Phase B3)
2. If any assertion fails → discard all Coherence Agent edits to that file (revert to the pre-coherence version from the B3.5 quality review backup)
3. Log which files were reverted and why

This ensures that coherence improvements (transition injection, terminology unification) never come at the cost of structural integrity. A section whose div structure was corrupted by Edit operations is restored to its structurally valid pre-coherence state.

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
│                                                                     │
│ # 4. Write paper_meta.json with Phase 0a paper metadata (zero LLM tokens) │
│ python -c "                                                             │
│ import json                                                             │
│ meta = {                                                                │
│   'paper_title': '...',                       ← actual title from Phase 0a │
│   'paper_type': '...',       ← system|algorithm|survey|empirical|position │
│   'paper_authors': '...',                                                │
│   'paper_venue': '...',                                                  │
│   'paper_date': '...',                                                   │
│   'paper_institution': '...',                                            │
│   'paper_method': '...',                                                 │
│   'paper_key_finding': '...'                                             │
│ }                                                                        │
│ with open('<output-dir>/paper_meta.json','w',encoding='utf-8') as f:    │
│   json.dump(meta,f,ensure_ascii=False)                                   │
│ "                                                                        │
│ # ALL 8 fields must be filled (avoids shell encoding issues on Windows) │
└────────────────────────────────────────────────────────┘
                         ↓
┌── FINAL AGENT ───────────────────────────────────────┐
│ B4c. Read sections_meta.json + paper_meta.json.           │
│      sections_meta.json → build sidebar links.             │
│      paper_meta.json → fill <meta> tags.                   │
│                                                         │
│      ⚠️ TEMPLATE PRIORITY RULE (MANDATORY):               │
│      You MUST NOT hand-write any CSS or JavaScript.       │
│      The canonical CSS is in assets/template.css.         │
│      The canonical JS  is in assets/template.js.          │
│      Read these files and embed their content verbatim    │
│      into head.html/tail.html via <!-- STYLESHEET -->     │
│      and <!-- SCRIPT --> placeholders.                    │
│                                                         │
│      Step 1: Choose the correct template shell:           │
│        - zh:  assets/template.html                        │
│        - en:  assets/template_en.html                     │
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
│                 **Set <body data-strategy="{strategy}">**  │
│                 to match the organization strategy chosen  │
│                 in Phase 0b (or "paper-structure-aligned" │
│                 if default).                                │
│                 **Fill all <meta name="paper-*"> tags**    │
│                 from paper_meta.json values. See A4.2      │
│                 for the HTML syntax.                       │
│                 **Embed CSS via <!-- STYLESHEET -->**       │
│                 Read assets/template.css, wrap in           │
│                 <style>...</style>, insert at placeholder. │
│                 + intro section (title, meta, thesis)     │
│                 + TL;DR section (summary grid)            │
│      tail.html: takeaways section (callouts + table)      │
│                 + footer                                   │
│                 **Embed JS via <!-- SCRIPT -->**            │
│                 Read assets/template.js, wrap in            │
│                 <script>...</script>, insert at placeholder.│
│                 + </body></html>                            │
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

**B4c bracket-placeholder discipline (CRITICAL — common Pipeline B failure mode)**

template.html ships with `[BRACKET]` placeholders. `initMeta()` auto-fills only the top-bar, `<h1>`, and `.meta-row` from the `<meta>` tags. **Everything else you MUST hand-replace in `head.html` and `tail.html` before `cat`.** Observed failure mode: agents fill the 8 `<meta>` tags and the `<h1>` correctly, then forget the body-level `[OPENING_PARAGRAPH]` / `[CORE_THESIS]` inside `SECTION: INTRO_OVERVIEW` and the `[VALUE]` / `[LABEL_CN]` / `[ONE_SENTENCE_SUMMARY_CN]` inside `SECTION: TLDR_*`, leaving the bracket literals visible to the reader in the final HTML.

| File | Placeholders requiring hand-fill | Source |
|------|----------------------------------|--------|
| `head.html` | `[LANGUAGE_CODE]` (line 2), `[ORGANIZATION_STRATEGY]` (line 447), the 8 `<meta name="paper-*">` tags in `<head>`, **`[OPENING_PARAGRAPH]` + `[CORE_THESIS]` in `SECTION: INTRO_OVERVIEW`**, **`[VALUE]` × N + `[LABEL_CN]` × N + `[ONE_SENTENCE_SUMMARY_CN]` in `SECTION: TLDR_*`** | `paper_meta.json` for paper-level fields. For INTRO_OVERVIEW: write `[OPENING_PARAGRAPH]` as 2–4 sentences summarizing the paper's motivation/method/result, and `[CORE_THESIS]` as a 1–3 sentence main argument inside a `.callout.purple`. For TLDR: pick 4–6 key metrics from the paper (e.g. dataset size, model count, accuracy delta) plus a one-sentence summary. |
| `tail.html` | `[CALLOUT_TITLE]` + `[CALLOUT_BODY_CN]` (`SECTION: TAKEAWAYS_*`, ~3–5 callouts), plus any placeholders inside `SECTION: FOOTER` | Synthesize 3–5 actionable takeaways from the section content (each `.callout.success`); FOOTER fields from `paper_meta.json`. |

**Self-check before running `cat`** (observation-only, NOT a hard gate — you decide whether to fix):

```bash
grep -nE '\[[A-Z_]{3,}\]' <output-dir>/head.html <output-dir>/tail.html
```

Any line that comes back → return to the wrapper file and fill the placeholder before `cat`. Once `cat`-ed, the literal `[FOO]` ships to the reader. The grep is safe to apply to `head.html` / `tail.html` only — paper text containing `[Algorithm 1]` or `[Theorem 2]` would land in `assembled_body.html`, never in the wrappers, so this check on wrappers alone has no false-positive risk.

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
- All 8 `<meta name="paper-*">` tags in `<head>` are filled (no `content=""` or bracket placeholders)
- No `<!-- FIG:` placeholders remain (assemble_figures.py also reports this)
- Section divs are well-formed, tags properly closed
- h2 numbering is contiguous (1, 2, 3...)
- Section IDs match sidebar hrefs, no duplicates
- All formulas are wrapped in `.formula-display` or `.formula-inline`
- **No intermediate file references** in the final HTML
- **Strategy marker present**: `<body>` has `data-strategy` matching Phase 0b Q3
- **Strategy section ordering**: h2 titles follow the strategy's sequence from Organization Strategy Reference
- **Strategy-specific heading style**: question-driven h2s end with `？`/`?`; persona-driven uses conversational titles

**What the human operator should spot-check**:
- Key numbers, names, and claims against the original text
- Section coverage against paper structure
- **UI checks**: base64 images render, lightbox opens/dismisses/navigates (Esc, ← →), mobile sidebar toggles, print layout correct, code copy works, KaTeX renders. See [Quality Checks](references/quality-checks.md) items 9-25 for full list.

**What requires B3.5 review** (deeper per-section check):
- Each section has ≥2 insight callouts (depth requirement)
- Content accuracy across all subsections
- No orphan components or force-fit patterns
- **No orphaned bold text**: `<strong>`/`<b>` flows inline within paragraphs
- **Figure cropping quality**: each figure is an individual crop, not full-page
- **Formula rendering**: LaTeX syntax correct, no mangled symbols, every display formula has explanation

### Phase B5: Post-Verification Cleanup

After the HTML passes all quality checks, delete all intermediate files:

```bash
rm -f <output-dir>/paper_text.txt \
      <output-dir>/figures_b64.json \
      <output-dir>/paper_meta.json \
      <output-dir>/section_*.html \
      <output-dir>/sections_meta.json \
      <output-dir>/sections_raw.html \
      <output-dir>/assembled_body.html
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

- **🔴 模板优先规则 (Template Priority Rule) — HARD REQUIREMENT**: Agent 在任何情况下都不得手写 CSS 或 JavaScript。所有 CSS 的规范来源是 `assets/template.css`，所有 JavaScript 的规范来源是 `assets/template.js`。Pipeline A 在 A4.1 通过 Python 脚本内联；Pipeline B 在 B4c 通过读取文件后填入 `<!-- STYLESHEET -->` / `<!-- SCRIPT -->` 占位符。违反此规则意味着 CSS/JS 与模板产生偏差，属于必须修复的缺陷。
- **Adapt, don't force-fit.** If the paper doesn't have design principles, don't create a principles section. Map content to the most natural component. If the chosen organization strategy would create an unnatural structure for this paper (e.g., question-driven on a pure position paper with no clear questions), fall back to paper-structure-aligned and note the reason in a comment.
- **Be thorough but not exhaustive.** Cover the paper's key contributions deeply. Don't enumerate every minor detail.
- **Prioritize insight over transcription.** Don't just copy the paper's text. Synthesize, connect ideas, highlight what matters.
- **One HTML file, zero dependencies.** Everything is inline — no external CSS, JS, fonts, or images. The file must work offline.
- **Dark mode is a first-class feature.** All colors must work in both light and dark themes. Test mentally: would this color be readable on a dark background?
- **In Parallel mode, sub-agents write HTML to files, never return HTML in their response.** Each sub-agent uses the Write tool to save `section_{id}.html` and returns the file path via structured JSON. This keeps the Workflow context lean (~50B per section instead of ~25KB). The component catalog, paper text, figure references, and formula LaTeX are inlined in each sub-agent's prompt — sub-agents should avoid re-reading shared files (template.html, component-catalog.md). If a sub-agent is unsure about a component pattern, it may read `references/component-catalog.md` once.
- **Working directory encoding**: If your paths contain non-ASCII characters (Chinese, spaces, etc.), Python subprocess calls may encounter encoding issues. Mitigation: (a) pass `--output` with an ASCII-only path to Python scripts, (b) set `PYTHONIOENCODING=utf-8` in your shell, or (c) on Windows, use short paths (`dir /x` to find them).
- **Section granularity matters.** Too many tiny sections produce fragmented notes. Too few large sections lose the benefit of parallelism. Aim for 4–8 sections.
- **Strategy affects order, not content.** The organization strategy controls section ORDER and GROUPING. Content depth rules (Principles 2-4), component choice, and quality checks apply identically regardless of strategy. Never omit insight callouts or depth because a question-driven section "is short."
- **Pipeline B + question-driven: use two-stage text extraction.** For question-driven in Pipeline B, B2 must NOT load the entire paper into context to extract passages. Instead: (1) generate questions, (2) grep keywords in paper_text.txt, (3) Read only matched passages. This prevents context overflow on long papers.
- **Pipeline B + cognition-first: run B3.5b Coherence Agent.** After quality review, run pairwise coherence checks on adjacent sections. See Phase B3.5b for the full procedure.
- **Pipeline B + persona-driven: warn the user.** Persona-driven requires a unified narrative voice that parallel sub-agents cannot maintain. Warn the user and recommend switching to Pipeline A.
- **Clean up after verification.** Once the HTML passes all quality checks (all figures render, no broken references, dark mode works, sidebar links functional), delete all intermediate files. The final HTML is fully self-contained — every image is a base64 data URI, every style and script is inline. Run `grep -c 'paper_text.txt\|figures_b64.json\|section_.*\.html\|assembled_body' <paper>_reading_notes.html` — it must output `0`.

## Note Indexing

> **Activation**: When the user says "更新索引", "刷新索引", "重建目录", "重建索引", "构建索引", "build index", "refresh index", or similar — follow this section. This applies regardless of whether the user is currently working on a note or not.

Generated notes can be organized with a searchable index page. `scripts/build_manifest.py` scans all `.html` notes in a directory, extracts metadata from `<meta name="paper-*">` tags and annotation data from `<script id="ppr-annotation-data">`, then injects everything into `assets/index-template.html` to produce a self-contained `index.html`.

### First-time setup

When a user asks for an index, ask for their notes directory and run:

```bash
python "<skill-dir>/scripts/build_manifest.py" "<notes-directory>"
```

**After the first successful build**, create a clickable refresh script in the notes directory. Detect the user's OS from the environment and create exactly one script:

- **Windows** (`Platform: win32`): create `refresh_index.bat`
- **macOS / Linux** (`Platform: darwin` or `Platform: linux`): create `refresh_index.sh`

**Important — direct write only**: Write the file using Python's `open().write()` or the Write tool (not `sed`/`echo`/shell redirection) to avoid encoding corruption of non-ASCII paths (e.g. Chinese characters in directory names).

**Windows** (`refresh_index.bat`):
```batch
@echo off
chcp 65001 >nul
python "<skill-dir>/scripts/build_manifest.py" "<notes-directory>"
echo.
pause
```

**Unix / macOS** (`refresh_index.sh`):
```bash
#!/bin/bash
python3 "<skill-dir>/scripts/build_manifest.py" "<notes-directory>"
```

Replace `<skill-dir>` and `<notes-directory>` with absolute paths (use `resolve()` to get absolute paths).

### Subsequent refreshes

If `refresh_index.bat` (Windows) or `refresh_index.sh` (Unix/macOS) already exists in the notes directory, tell the user they can simply double-click that script to rebuild the index — no need to invoke the skill again.

If the user moves the notes directory or wants a different template, re-run the first-time setup with the new paths.

### Features

The generated `index.html` provides:
- **Search**: real-time filtering by title, authors, institution, venue
- **Tag filters**: 5 paper types (system/algorithm/survey/empirical/position)
- **File tree**: folders expand/collapse, click to scroll to matching card
- **Cards**: paper title (serif), type badge, authors/venue/date, annotation count + content preview (up to 2)
- **Dark/light theme**: persisted to localStorage
- **Mobile responsive**: sidebar collapses to overlay below 840px
