## Content Depth Rules (Both Pipelines)

A reading note is not a translation or summary — it is a **curated analysis**. Every section must deliver more value than re-reading the original paper. These rules apply regardless of which pipeline is used.

### Principle 1: Strategy-Aware Organization, Invert Within Sections

**Section order is determined by the chosen organization strategy** from Phase 0b. The default strategy (paper-structure-aligned) matches the paper's own structure — Introduction → Background → Method → Experiments → Discussion → Conclusion. Readers who know the paper should feel oriented, not lost. Other strategies (cognition-first, question-driven, persona-driven) reorder content around the reader's cognitive path. See the [Organization Strategy Reference](organization-strategies.md) for per-strategy ordering rules.

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

**Callout structure**: Every `.callout.*` must begin with `<strong>emoji Title</strong>` as its first child, followed by one or more `<p>`. No self-invented classes (`.callout-title`, `.callout-body`). Emoji in the `<strong>` is the only variation allowed. Pipeline A's single agent is naturally consistent, but verify during A4.8 quality check.

---

