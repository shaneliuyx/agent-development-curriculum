# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A 12-week, project-driven Agent / LLM Engineer interview-prep curriculum, authored as an Obsidian vault. **No code, no build, no tests.** Markdown only. Each chapter is a long-form pedagogical document combining theory primer, hands-on lab, bad-case journal, and interview soundbites. Labs themselves live in a separate repo (`~/code/agent-prep/lab-*`); this vault is the *narrative* + *interview-prep* layer over those labs.

Reader profile in the frontmatter of `Agent Development 3-Month Curriculum.md`: cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles, local-first MLX stack on Apple Silicon, ~$10 cloud spend cap across 12 weeks.

## File organization

- `Agent Development 3-Month Curriculum.md` — top-level overview + discipline rules. Read first.
- `Week N - <Title>.md` — main weekly chapters (W0–W12).
- `Week N.M - <Title>.md` — supplementary chapters inserted between main weeks (W2.5 GraphRAG, W3.5 Cross-Session Memory, W3.7 Agentic RAG, W5.5 Metacognition, W6.5 Hermes, W6.7 Agent Skills, W7.5 Computer Use, W8.5 Voice AI, W11.5 Agent Security). Decimal numbering = "elective; cuts in between sequentially-prerequisite weeks."
- `Bad-Case Journal.md` — cross-cutting ops-pattern library. Every chapter's bad-case entries also live (or should live) here. Read order in its preamble.
- `Engineering Decision Patterns.md` — cross-cutting design-decision library, indexed by pattern, not by week.
- `tasks/`, `assets/diagrams/` — supporting non-prose.

## Required chapter structure (normative — every chapter MUST contain these 10 sections)

The reference chapter is `Week 2 - Rerank and Context Compression.md`. Every other chapter — main week, decimal supplement, future addition — MUST match this structure. A chapter that skips a required section is incomplete and SHOULD be flagged before commit.

### Section 1 — Why This Week Matters (REQUIRED, ~150 words)

Production motivation + interview signal. Why does this matter in real systems? Why will an interviewer ask about it? Do **not** collapse to a one-line TL;DR. The 150-word length is intentional — it is the speak-aloud hook for the topic.

### Section 2 — Theory Primer (REQUIRED, ~1000 words)

Long-form explanatory prose. Cite original papers (arXiv links). Include real numbers, not vague claims ("hybrid recall@10 = 0.998 vs dense 0.993" not "hybrid is better"). Distinguish carefully from adjacent concepts that are commonly conflated.

### Section 3 — Mechanism / Architecture Diagram (REQUIRED)

Mermaid diagrams (Obsidian renders them natively). Every chapter has at least one diagram showing the system shape. Label every node and edge — unlabeled boxes are not diagrams.

### Section 4 — Lab Phases (REQUIRED — numbered phases with runnable code)

Phases are numbered and time-budgeted (`## Phase 1 — <name> (~2 hours)`). Each phase includes:
- A goal statement
- Setup commands (real package names, real versions)
- Step-by-step numbered actions with **runnable Python** (not pseudocode)
- Verification commands at the end of the phase
- An expected metrics table (recall@K, latency, cost, etc — measured on M5 Pro hardware)

**Per-Python-block bundle (NORMATIVE).** Each Python script (or substantive Python snippet) inside a Lab Phase MUST be presented as one self-contained bundle, in this exact order, before moving to the next block:

1. **Architecture diagram** — Mermaid (non-ASCII) showing the data flow / call graph for THIS script. Place immediately before the code. Edge labels containing parens (`...(over-recall)...`) MUST be quote-wrapped (`-->|"text<br/>(parens)"| Node`) — bare parens in unquoted edge labels break the Mermaid parser.
2. **Code** — full `\`\`\`python` block. Annotate `**Code:**` header above for visual delineation.
3. **Walkthrough** — `**Walkthrough:**` header, then bullet-per-block analysis (`**Block 1 — <title>.**` + 2–4 sentences answering *why*, not what). Cover gotchas a copy-paster would miss.
4. **Result** — `**Result:**` header, then measured numbers from the actual lab run (wall time per stage, output sizes, aggregate scores). Pull from `RESULTS.md` in the lab repo. Mark `~estimated` if not yet measured; update after the run.
5. **Insight callout** — `\`★ Insight ─────────────────────────────────────\`` / `\`─────────────────────────────────────────────────\`` border around 2–3 bullets calling out non-obvious design choices, model superpowers being exploited, deliberate trade-offs.

The bundle is one continuous reading unit — do not split mermaid into one section, code into another, walkthrough into a separate `## Phase 5 — Code Walkthroughs` section. The old `## Phase 5` separate-section pattern is **deprecated** as of 2026-05-07. Reference: `Week 2.7 - Structure-Aware RAG.md` Phase 2/3/4 — every Python block follows this bundle shape.

**The non-negotiable bar:** the walkthrough portion must answer "why is this code shaped this way?" — a reader who copy-pastes the script must come away understanding the design choices, not just having a working script. If you cannot answer "why" for a block, you do not understand it well enough; spike the code first, then write.

### Section 5 — (deprecated)

The previous `## Phase 5 — Code Walkthroughs` separate section is no longer used. Walkthroughs live inline next to their code per the §4 per-block-bundle rule above. Existing chapters with a standalone §5 should be migrated when next touched: move each walkthrough back into the Phase that contains its code, then delete §5.

### Section 6 — Bad-Case Journal (REQUIRED — 3–5 entries, exact format)

Each entry uses **exactly** this 3-field format:

```
**Entry N — <one-line symptom>.**
*Symptom:* what the operator observes
*Root cause:* what is actually broken
*Fix:* concrete remediation, with code or config when applicable
```

Entries also belong in the global `Bad-Case Journal.md` cross-cutting library. Other chapters' interview soundbites cite specific entries — do not delete or rewrite entries without checking incoming references.

### Section 7 — Interview Soundbites (REQUIRED — 2–3 entries, user-voice, ~70 words each)

Written in first-person, anchored to a measured outcome from §4 or §6. Each soundbite is a speak-aloud answer to an interview question, ~70 words. Avoid hedging language. Avoid generic advice. Reference specific numbers and specific findings from this chapter.

### Section 8 — References (REQUIRED)

Peer-reviewed papers + canonical docs + production blog posts. Format:
- **Author et al. (Year).** *Title.* Venue. arXiv:NNNN.NNNNN. One-line description of why this reference matters.

Link to arXiv where applicable. Include at least one production blog post or canonical implementation repo so the reader can see how the concept ships in practice, not just how it is described in papers.

### Section 9 — Cross-References (REQUIRED)

Use these four labels in this order:

- **Builds on:** explicit prerequisite chapters (the reader should have done these first).
- **Distinguish from:** adjacent topics that are commonly conflated. **This section is high-leverage; do not skip it.** It is what makes a candidate sound senior in interviews.
- **Connects to:** later chapters that use this material as a building block.
- **Foreshadows:** chapters where this material reaches its full production shape (often W11 System Design or W12 Capstone).

Cross-references must be bidirectional — if W7 says "Builds on: W4 ReAct", then W4 should say "Connects to: W7 Tool Harness". When you add a forward link, add the reverse link in the target chapter in the same edit.

### Section 10 — Frontmatter (REQUIRED on new chapters)

YAML frontmatter at the top of the file:

```yaml
---
title: <chapter title>
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - agent
  - <topic-specific tags>
audience: <who this chapter is for, copied from curriculum overview>
stack: <hardware + model assumptions>
---
```

Update `updated:` on every substantive edit. Tags should overlap with sibling chapters so Obsidian's graph view connects them.

## Optional sections (use when relevant)

- **Empirical findings subsection (§N.X.Y).** When you run experiments and produce measured results that contradict or refine the theory primer, add a numbered subsection (e.g., `### 2.2.1 Actual results — fp32 vs fp16 reranker on M5 Pro (2026-04-28 runs)`). W2 uses this pattern extensively for its rerank experiments. Date-tag the subsection.
- **Mini-lab.** A 30-minute hands-on exercise that doesn't warrant a full Phase. Use `### Mini-Lab — <name>`.
- **Production considerations.** When the chapter has a clear production deployment story, add a `## Production Considerations` section before §6 Bad-Case Journal. Cover sandboxing, cost ceilings, multi-tenancy, observability.

## Pre-commit checklist (run mentally before every chapter commit)

```
[ ] §1  Why This Week Matters — ~150 words present
[ ] §2  Theory Primer — ~1000 words, papers cited, real numbers
[ ] §3  Mermaid diagram present and labeled
[ ] §4  Lab phases numbered, time-budgeted, with runnable code
[ ] §4  Expected metrics table present
[ ] §4  Per-Python-block bundle present (Architecture mermaid → Code → Walkthrough → Result → Insight) for every Python script
[ ] §4  Mermaid edge labels with parens are quote-wrapped (`-->|"text<br/>(parens)"|`)
[ ] §6  Bad-Case Journal — 3–5 entries in exact 3-field format
[ ] §6  New entries copied to global Bad-Case Journal.md
[ ] §7  Interview Soundbites — 2–3, user-voice, ~70 words, measured-outcome anchored
[ ] §8  References — papers + docs + production examples
[ ] §9  Cross-References — Builds on / Distinguish from / Connects to / Foreshadows
[ ] §9  Reverse links added in linked chapters
[ ] §10 Frontmatter updated
```

## Hard rules from `Agent Development 3-Month Curriculum.md`

These are stated discipline rules in the curriculum overview. Honor them when editing:

1. **No tutorial graveyard.** Every week must end with a runnable artifact + measured number. Do not write a chapter without empirical anchors.
2. **Every lab gets a `RESULTS.md`** — numbers, screenshots, what broke, what was fixed. (RESULTS.md lives in the lab repo, not the vault — but the vault's bad-case journals reference it.)
3. **Speak the answers out loud.** This is why interview soundbites exist; do not skip that section.
4. **Local-first, cloud only when you must.** Default examples to MLX/Ollama/local Whisper. Cloud APIs only when the lesson requires them.

## Cross-reference syntax

Internal vault links use Obsidian wikilinks: `[[Week 2 - Rerank and Context Compression#Phase 1 — Hybrid Retrieval|Phase 1]]`. Section anchors are `#<exact heading text>`. Maintain alphabet-only / no-emoji headings if you want stable anchors across renderers (most existing headings already comply).

Cross-reference order at the end of every chapter:
- `Builds on:` — explicit prerequisites
- `Distinguish from:` — adjacent topics that are commonly conflated (this section is high-leverage; do not skip)
- `Connects to:` / `Consumed by:` — chapters that use this material later

## Numbers and citations

Numbers in this vault are empirically measured on the user's hardware (MacBook Pro M5 Pro, 48 GB unified memory) unless stated. When citing latency, recall, cost, or throughput, prefer the user's measured numbers from the lab repo's `results/*.json` over public benchmark numbers. If you must use public numbers, cite the source.

## Editing safety

- **Do not delete cross-references** without first checking the linked chapter's `Builds on:` / `Distinguish from:` blocks — these are bidirectional invariants.
- **Preserve the `Bad-Case Journal` symptom → root cause → fix format.** Other chapters' interview soundbites cite specific entries.
- **Do not collapse the `Why This Week Matters` opening into a TL;DR.** It is the interview hook for that topic and is intentionally ~150 words, not 30.
- **Frontmatter** (where present) carries `tags`, `created`, `updated`, `audience`, `stack`. Update `updated` on substantive edits.
