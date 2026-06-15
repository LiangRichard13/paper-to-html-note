# Paper to HTML Reading Note

> [中文 README →](../README.md)

> **Token cost**: Generating a reading note consumes roughly **60k–120k tokens**, depending on paper length, pipeline mode, and organization strategy.

Convert academic CS/SE PDF papers into a single self-contained HTML reading note. Dark mode, sidebar navigation, built-in annotation system, and 4 organization strategies.

**One HTML file, zero external dependencies.** KaTeX loads from CDN on first visit, falls back to monospace when offline.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-%E2%89%A51.23-green)

---

## Features

- 🌓 Dark/light mode (persisted to `localStorage`)
- 📑 Sidebar navigation (IntersectionObserver, collapsible groups)
- 🖍 In-browser highlighter: select→highlight (6 colors), sticky note editor, sliding panel, cross-session persistence
- 📐 KaTeX math rendering (inline + display), monospace fallback when offline
- 🎯 4 organization strategies: paper-structure-aligned / cognition-first / question-driven / persona-driven, with auto-recommendation based on paper type
- 🔎 Paper type detection (system/algorithm/survey/empirical/position) for strategy recommendation
- 🖼 Caption-driven figure extraction (vector graphics + text-block cluster fallback)
- 📝 Formula pre-extraction — formulas transcribed to LaTeX before section reorganization
- 🔍 Lightbox zoom (← → Esc keyboard navigation)
- 📱 Mobile responsive (sidebar collapses to overlay below 960px)
- 📊 Reading progress bar + scroll-triggered entrance animation
- 📚 Index page generator — recursively scans a folder, builds a searchable/filterable catalog with file tree

---

## Quick Start

### Prerequisites

```bash
pip install PyMuPDF
```

`pdftotext` is recommended (included in `poppler-utils` on most systems).

### Usage (Claude Code skill)

```
/paper-to-html-note @paper.pdf
```

The skill gathers paper metadata, then asks you to choose pipeline, annotation language, and organization strategy:

| | Pipeline A (Sequential) | Pipeline B (Parallel) |
|---|:---:|:---:|
| **Agents** | 1 | 5–12 (requires Ultracode) |
| **Best for** | Short papers (<12pp), formula-heavy, quick previews | Long papers (≥12pp), figure-rich (>6), surveys |
| **Token cost** | ~60k–120k | ~70k–100k |
| **Figures** | Direct base64 inline | `<!-- FIG:N -->` placeholders + Python post-processing |

---

## Organization Strategies

Four strategies, chosen directly by the user in Phase 0b (Agent recommends based on paper type):

| Strategy | Best For | How It Works |
|----------|----------|-------------|
| paper-structure-aligned | Reviewing/locating | Follows the paper's own section order |
| cognition-first | First-time reading system/survey/position | Problem → Core idea → Design → Results |
| question-driven | First-time reading algorithm/empirical | Each section is a question + answer, FAQ style |
| persona-driven | Practitioner evaluation | First-person narrative: "Why I read this", "Where I'd be cautious" |

---

## Figure Extraction

Academic PDF figures are vector graphics, not embedded raster images. The extractor uses four geometric signals — no external models or APIs:

```
                Body paragraph (full-width, >150 chars)
                  ↓ constrains top edge
  ┌──────────────────────────────────┐  ← fig_top
  │    Vector drawings ██████████    │  ← drawing density tightens bounds
  │    (or text-block cluster)       │  ← fallback
  │    Figure content                │
  ├──────────────────────────────────┤  ← fig_bottom = caption_top − 2pt
  │  Fig. 1. Overview of ...         │  ← caption anchor
  └──────────────────────────────────┘
```

Covers ~95% of CS papers. Text-only figures use a text-block cluster fallback. A quick pre-check scans for "Fig."/"Figure" captions before extraction.

### Standalone use

```bash
python scripts/extract_figures.py paper.pdf --dpi 200 -o figures.json
python scripts/extract_figures.py paper.pdf --dpi 200 --save-images
```

---

## HTML Components

| Component | Use |
|-----------|-----|
| `.callout` (6 variants) | Insights, warnings, design motivation |
| `.grid-2 > .mini-card` | Parallel concepts, comparisons |
| `.pbox` numbered list | Design principles, rules |
| `table` inside `.table-wrap` | Architecture, taxonomy, benchmarks |
| `figure.paper-fig` | Embedded figures with lightbox + lazy loading |
| `.summary-grid` | Key metrics dashboard |
| `.formula-display` / `.formula-inline` | KaTeX formulas |
| `pre` + syntax highlighting | Pseudocode and code |
| `.mindmap` | Concept visualization |
| `.trace` ordered list | Numbered process flow |

---

## Context Safety (Pipeline B)

Pipeline B isolates base64 image data from LLM context through file I/O:

| Stage | Returns | Context |
|-------|---------|:------:|
| B1 Parallel extraction | JSON metadata (figure IDs, formula LaTeX) | <2KB |
| B2 Section assignment | Section assignments + context | <5KB |
| B3 Parallel writing | `{section_id, num, title, file_path}` | ~50B × N |
| B3.5a Quality review | Structured review JSON | <1KB |
| B3.5b Coherence validation | Pairwise edits + div safety | 0 (shell) |
| B4 Assembly | `assemble_figures.py` + concatenation | **0 tokens** |
| B4c Final check | Reads `sections_meta.json` + `paper_meta.json` | <2KB |

---

## Example

Reading note from "Towards Personalized LLM-Powered Agents" (29-page survey, 8 figures, Chinese annotations):

> [📄 View live →](https://htmlpreview.github.io/?https://github.com/LiangRichard13/paper-to-html-note/blob/master/assets/examples/toward_personalized_llm_powered_agents_reading_notes.html)

<img src="examples/screenshot.png" alt="Reading note screenshot" width="720">

6 content sections (Foundations → Memory → Profile → Retrieval → Evolution → Evaluation), inline architecture diagrams, insight callouts, comparison tables, executive summary dashboard, and the full in-browser annotation system.

---

## Project Structure

```
paper-to-html-note/
  SKILL.md
  README.md
  assets/
    README_en.md
    template.html              # Chinese template
    template_en.html           # English template (structurally identical)
    index-template.html        # Note index page template
    examples/
      screenshot.png
      toward_personalized_llm_powered_agents_reading_notes.html
  references/
    component-catalog.md
    design-system.md
    index-builder.md
  scripts/
    extract_figures.py
    assemble_figures.py
    build_manifest.py          # Index generator
```

---

## Supported Papers

Optimized for CS/SE academic papers (arXiv, ACM, IEEE, NeurIPS, ICML, etc.): two-column/single-column, vector graphics, math formulas, text-only figures.

## Limitations

| Scenario | Behavior |
|----------|----------|
| Scanned PDFs (raster-only) | Falls back to caption-based estimation |
| Non-English captions ("図 1") | Not detected; regex extension needed |
| Three-column layouts | Body paragraph detection may be inaccurate |
| Caption above figure (old-style) | Will crop incorrectly |
| Figure spanning page break | May be cut at page boundary |

## Dependencies

- Python 3.9+
- PyMuPDF (`fitz`)
- KaTeX (CDN-loaded, monospace fallback offline)
- pdftotext (optional)

## License

MIT
