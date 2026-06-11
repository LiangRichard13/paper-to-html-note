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
   4. Reuse existing Phase A2 content pattern detection where possible: architecture descriptions reinforce "system", taxonomy/classification reinforces "survey", mathematical formulas without system architecture reinforce "algorithm".

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

**Question 3 — Use scenario.** Automatically maps to an organization strategy based on user intent and detected paper type. This merges what would otherwise be two separate questions (intent + strategy) into one, minimizing decision fatigue. Present these options:

| Option (Chinese) | Option (English) | → Auto Strategy | Best For |
|---|---|---|---|
| 我想复习之前读过的内容 | I've read it, need reference notes | paper-structure-aligned | Quick section-by-section lookup |
| 这是我第一次接触这篇论文 | I haven't read this paper yet | cognition-first or question-driven (auto-selected based on paper type) | Building understanding from scratch |
| 我想快速判断值不值得读 | I'm deciding whether to read this | question-driven | 5-minute overview of core contributions |
| 自定义组织方式... | Custom... | Expands to Q4 for manual strategy selection | Advanced users |

**Auto-selection logic for "第一次接触"**: Use the detected paper type from Phase 0a step 6.5 with the complete recommendation matrix below.

**Complete recommendation matrix (intent × paper_type → primary strategy)**:

| Intent | system | algorithm | survey | empirical | position |
|--------|--------|-----------|--------|-----------|----------|
| review (复习) | paper-structure | paper-structure | paper-structure | paper-structure | paper-structure |
| learn (初学) | cognition-first | question-driven | cognition-first | question-driven | cognition-first |
| locate (查找) | paper-structure | paper-structure | question-driven | paper-structure | question-driven |
| evaluate (评估) | question-driven | question-driven | cognition-first | question-driven | cognition-first |

**If paper type was ambiguous in Phase 0a step 6.5** (two types within 0.2 confidence), include a note in the Q3 prompt:
```
📋 注意：论文类型检测不确定（可能是 {type_a} 或 {type_b}）。
如果选择「第一次接触」，将默认按 {type_a} 组织（{type_a_strategy}）。
如需要 {type_b_strategy} 组织，请选择「自定义」手动切换。
```

**Q4 — Manual strategy selection** (only shown when Q3 = "自定义"):

| Option | Label (Chinese) | Best For |
|--------|-----------------|----------|
| paper-structure-aligned | 论文结构对齐 | You've read the paper; section-by-section reference |
| cognition-first | 认知先行 | You haven't read it; mental framework before details |
| question-driven | 问题驱动 | You want answers to core design questions |
| persona-driven | 实践者视角 | You're a practitioner evaluating whether/how to apply |

**Default**: paper-structure-aligned. If the user does not respond to Q3, this is the fallback — behavior identical to current.

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

**Q3: 请选择使用场景：**

🏷️ "这是我第一次接触这篇论文" → 自动推荐：cognition-first（认知先行）
    备选：question-driven（问题驱动）
```

---

## Content Depth Rules (Both Pipelines)

A reading note is not a translation or summary — it is a **curated analysis**. Every section must deliver more value than re-reading the original paper. These rules apply regardless of which pipeline is used.

### Principle 1: Strategy-Aware Organization, Invert Within Sections

**Section order is determined by the chosen organization strategy** from Phase 0b. The default strategy (paper-structure-aligned) matches the paper's own structure — Introduction → Background → Method → Experiments → Discussion → Conclusion. Readers who know the paper should feel oriented, not lost. Other strategies (cognition-first, question-driven, persona-driven) reorder content around the reader's cognitive path. See the [Organization Strategy Reference](#organization-strategy-reference) for per-strategy ordering rules.

**Within each section**, regardless of strategy, use inverted pyramid: state the conclusion first, then explain why.

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

## Organization Strategy Reference

The four strategies below control how sections are ordered and grouped. The agent applies the chosen strategy during Phase A3 (content-to-component mapping), A4 (HTML generation), B2 (section assignment), and B3 (sub-agent writing). The default is `paper-structure-aligned`.

### Strategy Selection

Strategy is determined by a combination of **user intent** (from Phase 0b Q3) and **detected paper type** (from Phase 0a step 6.5). See the recommendation matrix in Phase 0b for which strategy to recommend for each (intent × paper_type) combination.

### Strategy 1: paper-structure-aligned (default)

**Goal**: Match the paper's structure for easy cross-reference.
**Best for**: review/locate intent, any paper type.
**Section order**: Follow the paper's own heading hierarchy. Identify which template section blocks correspond to which paper sections and place them in paper order.
**Sidebar grouping**: Groups follow paper structure (grouped by paper section number).

### Strategy 2: cognition-first

**Goal**: Build a cognitive framework from the ground up. Start with "what problem does this solve and why should I care?" before diving into details.
**Best for**: learn intent, system/survey/position papers.
**Section order**: Problem-first, solution-second, details-last.

```
1. Problem & Motivation (what gap exists, why it matters)
2. Core Idea / One-Liner (the paper's key insight in 1 paragraph)
3. Approach Overview (high-level architecture or taxonomy, with Fig 1)
4. Key Design Decisions (design principles, tradeoffs made)
5. How It Works (mechanisms, algorithms, implementation details)
6. Results & Evidence (does it actually work?)
7. Limitations & Open Questions (what's still unsolved)
8. Relationship to Prior Work (how it fits the landscape)
9. Methodology Notes (how the research was conducted)
10. Takeaways (what a practitioner should remember)
```

**Section merging**: Combine Introduction + Background into "Problem & Motivation". Split Method into "Core Idea" + "Key Design Decisions" + "How It Works". Move Related Work later.
**Sidebar grouping**: Groups follow the reader's learning journey: "Understanding the Problem" → "The Solution" → "Evidence" → "Broader Context".

### Strategy 3: question-driven

**Goal**: Organize content around 4-8 core questions the paper answers. Each section IS a question.
**Best for**: learn/evaluate intent, algorithm/empirical papers.
**Section order**: Questions in logical dependency order (foundational questions first). Agent generates questions from paper content.

**Question templates by paper type** (derive from paper content, not copy verbatim):

| Paper Type | Template Questions |
|------------|-------------------|
| system | What problem does this system solve? What is the key architectural insight? How are the components organized? What design tradeoffs were made? Does it perform well? What are its limitations? |
| algorithm | What problem does this algorithm solve? What is the core idea/insight? How does it work step by step? How does it compare to alternatives? Under what conditions does it fail? |
| survey | What is the landscape? How are approaches categorized? What are the key dimensions of comparison? What patterns emerge across categories? What open problems remain? |
| empirical | What was studied and why? How was the study designed? What were the key findings? How robust are the results? What should practitioners do differently? |
| position | What is the central argument? What evidence supports it? What assumptions underlie it? What would change if adopted? What are the counterarguments? |

**Section heading**: The h2 heading text IS the question itself (e.g., "系统如何在动态环境中保持记忆一致性？").
**Sidebar grouping**: One group = one question. The sidebar becomes an FAQ-like index.

**Bare-bones question-section template** (for Pipeline A; Pipeline B sub-agents use the same structure):

```html
<div class="section" id="{question_id}">
<h2><span class="num">{N}</span> {question_text}<a href="#{question_id}" class="anchor">#</a></h2>
<p>{开篇回答 — 1-2 sentences that directly answer the question. This is the most important sentence of the section.}</p>
<!-- Body: mix of callouts + optional figures/formulas. Use the same component catalog as other strategies. -->
</div>
```

### Strategy 4: persona-driven

**Goal**: Narrate the paper as if a practitioner is explaining it to a colleague.
**Best for**: evaluate intent, system/position papers.
**Section order**: Narrative arc from practitioner's perspective.

```
1. "Why I picked up this paper" (context + motivation)
2. "The one idea I can't stop thinking about" (core contribution)
3. "How it actually works — the 5-minute version" (architecture/mechanism walkthrough)
4. "Numbers that matter" (key results, with skepticism about generalizability)
5. "Where I'd be cautious" (limitations, unstated assumptions)
6. "When I'd use this" (practical applicability guide)
7. "What I'd build next" (future directions relevant to practitioners)
8. "Papers I'd read alongside this" (curated related work)
```

**Tone**: Use conversational section titles. Write section intros in first/second-person ("you", "I read this so you don't have to"). Technical claims remain precise — informality is in framing, not in data or claims.
**Sidebar grouping**: Conversational groups like "Why It Matters" / "How It Works" / "Should You Use It?".

### Strategy Implementation: buildSectionOrder()

For implementation, each strategy is an ordered list of section types with grouping metadata. The agent:

1. Selects which template section blocks to keep (from Phase A3 content mapping)
2. Orders those blocks per the strategy (not per the template's default order)
3. Groups sidebar entries per the strategy

**Key rule**: Content mapping determines WHICH sections exist. Strategy determines their ORDER. Never force content into sections the paper doesn't have — only change sequence and grouping.

### Pipeline B Compatibility

| Strategy | Pipeline B Support | Extra Mechanism | Cost |
|----------|:---:|---|------|
| paper-structure | ✅ Native | None | Zero |
| question-driven | ✅ Mild adaptation | B2 provides `previously_defined_concepts` list to each sub-agent to prevent re-definition | Low (~200 chars/sub-agent) |
| cognition-first | ⚠️ Needs coherence validation | B3.5 extended with Coherence Agent that checks cross-section transitions, concept consistency, and duplicates using pairwise checking | Medium (+1 agent call) |
| persona-driven | ❌ Not recommended | Warn user to switch to Pipeline A; unified narrative voice cannot be maintained across parallel sub-agents | Zero (warning only) |

### Figure & Formula Integration Across Strategies

**Formulas**: Formulas are embedded within text paragraphs. When B2 reorganizes text for any strategy, formulas travel with their surrounding text. **Prerequisite**: Formula LaTeX transcription MUST be completed during Phase 0a step 6.6 (before any pipeline selection), so that formulas can be located by their PDF context before sections are reorganized. See Phase 0a step 6.6.

**Figures**: Figures are independent objects with a single physical page location but variable logical attribution. B2 must explicitly reassign figures when strategies reorganize section boundaries:

| Strategy | Figure Handling |
|----------|----------------|
| paper-structure | Figures inherit paper section assignment. No change needed. |
| cognition-first | When B2 merges paper sections into thematic units, the `figures` field = **union** of all source sections' figure IDs. |
| question-driven | B2 may assign the **same figure to multiple questions**. `assemble_figures.py` handles this automatically: first occurrence gets full `<figure>`, subsequent occurrences become `.fig-ref` cross-references (existing Component 23 mechanism). |
| persona-driven | Same as cognition-first for assignment. Additional: `strategy_guidance` tells sub-agents to write figure captions in conversational tone. |

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

**If formulas were already pre-extracted in Phase 0a step 6.6**, skip manual transcription and use the pre-extracted formula data directly. The pre-extracted data provides `{id, latex, page, context}` for each formula — embed them using `$...$` or `$$...$$` in the appropriate content sections. No further transcription is needed.

**Otherwise** (pre-extraction was skipped, incomplete, or Pipeline A was invoked without Phase 0a), follow the options below:

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

### Strategy-Aware Section Ordering

After identifying which sections to include (from the mapping above), order them according to the chosen organization strategy. Refer to the [Organization Strategy Reference](#organization-strategy-reference) for each strategy's ordering rules.

**Key rule**: Content mapping determines WHICH sections exist. Strategy determines their ORDER. You never force content into sections the paper doesn't have — you only change the sequence and grouping.

**Strategy parameter**: `{organization_strategy}` from Phase 0b Q3/Q4. Default: `paper-structure-aligned`.

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

### A4.3 Select, order, and build content sections

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
27. **Strategy marker present**: The `<body>` tag has a `data-strategy` attribute matching the strategy chosen in Phase 0b (e.g., `data-strategy="cognition-first"`). Verify with: `grep -o 'data-strategy="[^"]*"' <output>.html`.
28. **Strategy section ordering**: The h2 titles appear in the sequence specified by the chosen strategy's ordering rules (from Organization Strategy Reference). When the strategy is NOT paper-structure-aligned, the section order should NOT match the template's default order.
29. **Strategy-specific heading style**: For question-driven, every h2 heading contains an actual question (ends with `？` or `?`). For persona-driven, section titles use conversational/practitioner-oriented language rather than academic section headings.

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

Each sub-agent receives this prompt structure:

```
You are writing ONE section of an academic paper reading note in {annotation_language}.

## Organization Strategy
This note uses the **{strategy}** organization strategy.
{strategy_guidance}

## Your Section
- Section number: {num}
- Section ID: {id}
- Section title: {title}
- Position in narrative: {position_context}

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
{Insert the inline component catalog below. For the complete catalog (23 components), sub-agents may read references/component-catalog.md if they need a component not listed here.}

## Content Rules
0. **Strategy awareness**: {strategy_specific_rule}
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

**Strategy-specific template values for sub-agent prompts**:

| Placeholder | paper-structure | cognition-first | question-driven | persona-driven |
|---|---|---|---|---|
| `{strategy_guidance}` | "Follow the paper's own subsection structure within your section. Readers will cross-reference the original." | "Open with the conceptual framework or problem statement before showing mechanics. Build understanding layer by layer." | "Your section heading IS the question. The entire section is the answer. Lead with the answer, then explain." | "Write as if explaining to a fellow practitioner. Use 'you' framing for practical takeaways. Keep technical claims precise." |
| `{position_context}` | "Section {num} of {total}" | "Section {num} of {total}. Preceded by: {prev_title}. Followed by: {next_title}." | "Question {num} of {total}. Preceding question: {prev_question}. Following question: {next_question}." | "Section {num} of {total} in the narrative arc. Preceded by: {prev_title}. Followed by: {next_title}." |
| `{strategy_specific_rule}` | "Match the paper's own section structure faithfully. Do NOT add extra wrapper <div> elements — exactly one outer <div class='section'> wrapper." | "Your chapter should naturally flow from the preceding chapter's framework and set up claims for the next chapter to verify. Do NOT add extra wrapper <div> elements — exactly one outer <div class='section'> wrapper." | "Answer the question directly in the first sentence. Reference previously defined concepts ({previously_defined_concepts}) without re-defining them. Do NOT add extra wrapper <div> elements — exactly one outer <div class='section'> wrapper." | "Write section intro in conversational first/second-person. Technical claims remain precise. Figure captions use natural language (not academic 'Fig. X:' format). Do NOT add extra wrapper <div> elements — exactly one outer <div class='section'> wrapper." |

### Component Reference for Sub-Agents

Include this condensed reference in every sub-agent prompt. For the full catalog (23 components with HTML snippets), sub-agents may read `references/component-catalog.md` if they need a component not listed here.

```
## Quick Component Reference

.callout — 6 intent-mapped types (match type to cognitive intent):
  .info     = "here's what the paper claims" (summary layer)
  .purple   = "here's WHY this design choice" (design motivation)
  .warn     = "this choice creates tension with X" (trade-off, cross-section link)
  .success  = "here's what you should do" (actionable takeaway)
  .danger   = "here's a risk the paper doesn't discuss" (critical observation)
  .cyan     = methodology note / clarification
  <div class="callout info"><strong>Title</strong><p>Body</p></div>

table — neutral data: <table><tr><th>Col</th></tr><tr><td>...</td></tr></table>
.grid-2 > .mini-card — compare parallel concepts side by side
.pbox — numbered principle: .pn (number) + .pb (body) + .tag (labels)
.tag — inline badge: <span class="tag bl">Label</span> (6 colors: bl gr or rd pu cy)
.formula-display — $$\sum x_i$$ (display) / .formula-inline — $E=mc^2$ (inline)
figure placeholder — <!-- FIG:N --> on its own line (NEVER <figure>/<img>/base64)

For any component not listed here, read references/component-catalog.md.
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

**Exception**: The B3.5b Coherence Agent (cognition-first strategy) may perform lightweight Edits for transition injection and terminology unification. These edits MUST be followed by immediate div balance validation (see B3.5b DIV SAFETY RULE). For all other phases, rewriting on failure remains mandatory.

**Severity Note**: Clean Section Contract violations are the most severe pipeline errors. A single unbalanced div will corrupt the entire content area of the final HTML, and the cost of repair far exceeds rewriting the section. Therefore, rewriting is mandatory on failure — with the sole exception of B3.5b Coherence Agent edits that pass post-edit div validation.

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
│                 **Set <body data-strategy="{strategy}">**  │
│                 to match the organization strategy chosen  │
│                 in Phase 0b (or "paper-structure-aligned" │
│                 if default).                                │
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
