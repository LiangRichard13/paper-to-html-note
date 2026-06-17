## Organization Strategy Reference

The four strategies below control how sections are ordered and grouped. The agent applies the chosen strategy during Phase A3 (content-to-component mapping), A4 (HTML generation), B2 (section assignment), and B3 (sub-agent writing). The default is `paper-structure-aligned`.

### Strategy Selection

The user directly chooses from the 4 strategies in Phase 0b Q3. The Agent provides a recommendation based on the **detected paper type** (from Phase 0a step 6.5) and content characteristics, but the user makes the final choice.

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

### Strategy Implementation: Section Ordering

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

