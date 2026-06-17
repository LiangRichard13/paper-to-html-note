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
{Insert the inline component catalog below. For the complete catalog (24 components), sub-agents may read references/component-catalog.md if they need a component not listed here.}

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

Include this condensed reference in every sub-agent prompt. For the full catalog (24 components with HTML snippets), sub-agents should read [Component Catalog](component-catalog.md).

```
## Quick Component Reference (condensed)

.callout — 6 intent-mapped types: .info / .purple / .warn / .success / .danger / .cyan
table — structured data: <table><tr><th>Col</th><td>val</td></tr></table>
.grid-2 > .mini-card — side-by-side comparison cards
.summary-grid > .sg-item — stats dashboard: .sg-val + .sg-lbl
.pbox — numbered principle: .pn + .pb + .tag
.tag — inline badge: <span class="tag bl">Label</span> (6 colors)
.formula-display — $$...$$ (display) / .formula-inline — $...$ (inline)
figure — <!-- FIG:N --> placeholder, NEVER <figure>/<img>/base64

Full catalog with HTML examples: references/component-catalog.md
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

#### CALLOUT CONTRACT (Execute with Clean Section Contract):

Also validate DOM structure patterns before returning JSON:

```python
from html.parser import HTMLParser
class CalloutCheck(HTMLParser):
    def __init__(self): super().__init__(); self.errors = []
    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get('class', '')
        if cls and cls.startswith('callout'):
            # Must have <strong> as first child, not a custom class like callout-title
            self._cur_callout = cls
    def handle_endtag(self, tag):
        if hasattr(self, '_cur_callout'): del self._cur_callout
    def handle_data(self, data):
        if hasattr(self, '_cur_callout') and data.strip():
            self.errors.append(f'Callout .{self._cur_callout}: first child must be <strong>, got text')
checker = CalloutCheck(); checker.feed(open('<output-dir>/section_{id}.html').read())
# Also reject self-invented patterns
assert 'callout-title' not in content, 'FAIL: use standard <strong> in callout, not .callout-title'
assert checker.errors == [], '\n'.join(checker.errors)
```

**IRON RULES for class names (apply to ALL components, not just callouts):**

✅ **Order is fixed**: component name first, modifier second.
  - `class="callout info"`, `class="callout purple"`, `class="callout warn"`, `class="callout success"`, `class="callout danger"`, `class="callout cyan"`
  - `class="tag bl"`, `class="tag gr"`, `class="tag or"`, `class="tag rd"`, `class="tag pu"`, `class="tag cy"`

❌ **Never reverse the order**. These are wrong:
  - `class="info callout"`, `class="purple callout"`, `class="insight callout"`, `class="warn callout"`
  - `class="bl tag"`, `class="rd tag"`

❌ **Never invent new class names**. These do NOT exist in the design system:
  - `.stat-card / .stat-num / .stat-label` → use `.sg-item / .sg-val / .sg-lbl` from `.summary-grid` instead
  - `.callout-title / .callout-body` → use `<strong>Title</strong><p>Body</p>` inside `.callout` instead
  - `.insight / .takeaway / .highlight` (as standalone classes) → these don't exist; use the matching `.callout TYPE` (e.g. `.callout.purple` for design insight, `.callout.success` for takeaway)
  - `.card / .box / .panel` (unqualified) → use `.mini-card` inside `.grid-2`/`.grid-3`, or `.pbox`

If a component you need is NOT in this Quick Reference, **read `references/component-catalog.md`** for the full 24-component canonical class list. Do not improvise.

**IRON RULES for callouts:**
- Every `.callout.*` must have `<strong>` as its first child element
- No self-invented class names (no `.callout-title`, `.callout-body`, etc.)
- Emoji prefix in `<strong>` is fine: `<strong>📌 Key Insight</strong>`
- `<strong>` is always INLINE — inside `.callout`, NOT wrapped in `<p>`

If any assertion fails, rewrite the section — same as Clean Section Contract.

**Exception**: The B3.5b Coherence Agent (cognition-first strategy) may perform lightweight Edits for transition injection and terminology unification. These edits MUST be followed by immediate div balance validation (see B3.5b DIV SAFETY RULE). For all other phases, rewriting on failure remains mandatory.

**Severity Note**: Clean Section Contract violations are the most severe pipeline errors. A single unbalanced div will corrupt the entire content area of the final HTML, and the cost of repair far exceeds rewriting the section. Therefore, rewriting is mandatory on failure — with the sole exception of B3.5b Coherence Agent edits that pass post-edit div validation.

**Why this works**: 8 sections × ~25KB HTML = ~200KB would flood the main context.
By writing to files, each sub-agent returns only ~50 bytes of metadata. The main
context stays lean. The structured JSON schema in the Workflow `agent()` call was
already changed to accept `{section_id, num, title, file_path}`, so raw HTML will be
rejected by the schema validator.

