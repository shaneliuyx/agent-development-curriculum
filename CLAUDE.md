# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A 12-week, project-driven Agent / LLM Engineer interview-prep curriculum, authored as an Obsidian vault. **Prose-first: no application build, no test suite.** The chapters are Markdown. The one exception is `scripts/` — Python audit scripts that act as the vault's lint/CI layer, enforcing structural invariants across chapters (see [Audit commands](#audit-commands--the-vaults-lint-layer)). Each chapter is a long-form pedagogical document combining theory primer, hands-on lab, bad-case journal, and interview soundbites. The labs' own code lives in a separate repo (`~/code/agent-prep/lab-*`); selected lab/reference repos are also vendored under `code/` here. This vault is the *narrative* + *interview-prep* layer over those labs.

Reader profile in the frontmatter of `Agent Development 3-Month Curriculum.md`: cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles, local-first MLX stack on Apple Silicon, ~$10 cloud spend cap across 12 weeks.

## File organization

- `Agent Development 3-Month Curriculum.md` — top-level overview + discipline rules. Read first.
- `Week N - <Title>.md` — main weekly chapters (W0–W12).
- `Week N.M - <Title>.md` — supplementary chapters inserted between main weeks (W2.5 GraphRAG, W3.5 Cross-Session Memory, W3.7 Agentic RAG, W5.5 Metacognition, W6.5 Hermes, W6.7 Agent Skills, W7.5 Computer Use, W8.5 Voice AI, W11.5 Agent Security). Decimal numbering = "elective; cuts in between sequentially-prerequisite weeks."
- `README.md` — public-facing entry point ("How to read"). The reading-order map lives here.

Cross-cutting libraries (indexed by theme/pattern, not by week — keep in sync when chapters change):
- `Bad-Case Journal.md` — ops-pattern library. Every chapter's bad-case entries also live (or should live) here. Read order in its preamble. Documents WHAT broke + WHY + FIX, *after the fact*.
- `ANTI-PATTERNS.md` — companion to the Bad-Case Journal. Documents patterns to avoid *before* writing code. Read both before starting a new chapter or lab.
- `Engineering Decision Patterns.md` — design-decision library, indexed by pattern number. The audit scripts enforce the mechanically-checkable patterns here (e.g. Pattern 19, Pattern 21).
- `Interview Question Index.md` — pre-interview entry point; maps interview-question patterns → chapter + measured anchor. Open 24–48h before an interview.
- `FDE Track - Forward Deployed Engineer Path.md` — alternate chapter ordering for Forward Deployed Engineer interview prep.
- `Trend-Monitoring Discipline.md` — process doc for keeping the curriculum current with the field.

Supporting directories:
- `scripts/` — Python audit scripts (the vault's lint layer). See [Audit commands](#audit-commands--the-vaults-lint-layer).
- `code/` — vendored lab/reference repos (`agent-prep`, `EverOS`, `LongMemEval`, `self-improving-agents-curriculum`). Source for measured numbers; not part of the prose.
- `proposals/` — draft chapter proposals before they become full `Week N.M` chapters.
- `research/` — research notes backing specific chapters (e.g. structure-aware RAG tree construction).
- `tasks/`, `assets/diagrams/` — supporting non-prose.

## Audit commands — the vault's lint layer

There is no build or test suite. The closest equivalent is `scripts/`, which mechanically enforces the checkable invariants in `Engineering Decision Patterns.md`. Run from the vault root any time the chapter set changes substantially:

```bash
# Cross-reference audit (Pattern 21 — bidirectional cross-ref invariant):
# every "Builds on:/Connects to:/Distinguish from:/Foreshadows:/Cited by: B" on
# chapter A must have a reciprocal mention on chapter B.
python3 scripts/audit_cross_refs.py
python3 scripts/audit_cross_refs.py --verbose          # show every missing edge

# Status-marker audit (Pattern 19 — Spec → IMPLEMENTED transition markers):
# flags implicit-state headings (TBD / OUTLINED / "FULL TEXT IN ROUND N").
python3 scripts/audit_status_markers.py
python3 scripts/audit_status_markers.py --list-explicit # also show compliant headings
python3 scripts/audit_status_markers.py --fix           # rewrite implicit → (SPEC)
```

Exit code `0` = clean, `1` = violations found (CI-hook-friendly). Both scripts walk `Week*.md` in the vault root. Taste-based patterns (★ Insight callouts, trade-off transparency) stay human-review-only — do not try to automate them. When you codify a new mechanically-checkable pattern in `Engineering Decision Patterns.md`, add a matching script here (`scripts/README.md` documents the shared shape).

## Required chapter structure (normative — every chapter MUST contain these 9 sections)

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

1. **Architecture diagram** — Mermaid (non-ASCII) showing the data flow / call graph for THIS script. Place immediately before the code. Mermaid hygiene rules (NORMATIVE):
    - **Edge labels with parens** MUST be quote-wrapped (`-->|"text<br/>(parens)"| Node`). Bare parens in unquoted edge labels break the Mermaid parser.
    - **Subgraph titles** MUST be ≤22 characters AND ≤ the cluster's narrowest sibling cluster width. Two constraints: (a) absolute char count to avoid wrapping at any zoom; (b) Mermaid sizes each cluster to its widest child node, so a title that fits in a wide cluster may wrap in a narrow sibling. Visual symmetry rule: side-by-side comparison subgraphs should have titles of matching word count and length — if one sibling cluster is narrower, shorten ALL titles to fit the narrowest. Move port numbers, version tags, qualifier suffixes into the section's prose paragraph or into child node labels (`Imprint API<br/>:1995`), not the cluster title.
    - **Horizontal multi-cluster layouts** (`flowchart LR` with multiple `subgraph` blocks) MUST add invisible-link chaining (`C1 ~~~ C2 ~~~ C3`) when the subgraphs share no real edges. Without it, the layout engine stacks subgraphs vertically and wastes horizontal canvas, regardless of the top-level `LR` declaration.
    - **Node labels** with multiple lines use `<br/>` (HTML break), not literal `\n`. Each line ≤20 chars to avoid box-width drift across siblings.
    - **Diagram direction** — default to **`flowchart TD`** (vertical). Vertical diagrams stay narrow, fit the article column without downscaling, and render text at declared fontSize. **`flowchart LR`** is reserved for diagrams where horizontal layout is semantically load-bearing — typically side-by-side subgraph clusters used for visual comparison (e.g., Class 1 vs Class 2 vs Class 3 architectures, L1/L2/L3 tier topology). Wide linear pipelines (>5 nodes) MUST be TD; reading a 10-node horizontal scroll is worse than reading a 10-node vertical column.
    - **Font size directive** — every mermaid block opens with a `%%{init: ...}%%` directive immediately after the ```` ```mermaid ```` fence. Two classes:
        - **Default (TD/TB diagrams):** `%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%`. Vertical diagrams don't downscale, so 20px declared renders at ~20px display (matches article body text).
        - **LR subgraph-cluster diagrams:** `%%{init: {'theme':'default', 'themeVariables': {'fontSize':'28px'}, 'flowchart':{'useMaxWidth':false, 'subGraphTitleMargin':{'top':20,'bottom':30}, 'nodeSpacing':40, 'rankSpacing':50}}}%%`. Three load-bearing settings: (a) `useMaxWidth:false` lets wide diagrams overflow horizontally so text stays at native pixel size; (b) `subGraphTitleMargin` adds explicit gap between cluster title and first child node (default margin is too tight at any fontSize ≥ 24px and causes title-vs-first-node text overlap); (c) `nodeSpacing` + `rankSpacing` open up the between-node gaps so dense LR diagrams don't pack arrows tight. Trade-off accepted: horizontal scroll inside the article container.
2. **Code** — full `\`\`\`python` block. Annotate `**Code:**` header above for visual delineation.
3. **Walkthrough** — `**Walkthrough:**` header, then bullet-per-block analysis (`**Block 1 — <title>.**` + 2–4 sentences answering *why*, not what). Cover gotchas a copy-paster would miss.
4. **Result** — `**Result:**` header, then measured numbers from the actual lab run (wall time per stage, output sizes, aggregate scores). Pull from `RESULTS.md` in the lab repo. Mark `~estimated` if not yet measured; update after the run.
5. **Insight callout** — `\`★ Insight ─────────────────────────────────────\`` / `\`─────────────────────────────────────────────────\`` border around 2–3 bullets calling out non-obvious design choices, model superpowers being exploited, deliberate trade-offs.

The bundle is one continuous reading unit — do not split mermaid into one section, code into another, walkthrough into a separate `## Phase 5 — Code Walkthroughs` section. The old `## Phase 5` separate-section pattern is **deprecated** as of 2026-05-07. Reference: `Week 2.7 - Structure-Aware RAG.md` Phase 2/3/4 — every Python block follows this bundle shape.

**The non-negotiable bar:** the walkthrough portion must answer "why is this code shaped this way?" — a reader who copy-pastes the script must come away understanding the design choices, not just having a working script. If you cannot answer "why" for a block, you do not understand it well enough; spike the code first, then write.

### Walkthroughs are inline — no separate walkthrough section

There is **no separate code-walkthrough section** (the old `## Phase 5 — Code Walkthroughs` pattern is gone). Walkthroughs live inline next to their code per the §4 per-block-bundle rule above. **Do not emit a `## 5. (deprecated)` stub or any deprecated placeholder.**

Section numbering is **continuous, 1–9** (no gap). After §4 Lab Phases the next section is **§5 Bad-Case Journal** — the sections below renumbered down by one when the old deprecated §5 slot was removed (2026-06-16). When you touch a chapter that still carries a leftover `## 5. (deprecated)` stub or a §4→§6 gap, delete the stub and renumber the remaining sections so they run 1–9 continuously (move any walkthrough text back into its Phase first, then renumber §6→§5 … §10→§9, and fix that chapter's internal `§N` references — taking care NOT to touch cited-paper section numbers like "RouteLLM §5").

### Section 5 — Bad-Case Journal (REQUIRED — 3–5 entries, exact format)

Each entry uses **exactly** this 3-field format:

```
**Entry N — <one-line symptom>.**
*Symptom:* what the operator observes
*Root cause:* what is actually broken
*Fix:* concrete remediation, with code or config when applicable
```

Entries also belong in the global `Bad-Case Journal.md` cross-cutting library. Other chapters' interview soundbites cite specific entries — do not delete or rewrite entries without checking incoming references.

### Section 6 — Interview Soundbites (REQUIRED — 2–3 entries, user-voice, ~70 words each)

Written in first-person, anchored to a measured outcome from §4 or §5. Each soundbite is a speak-aloud answer to an interview question, ~70 words. Avoid hedging language. Avoid generic advice. Reference specific numbers and specific findings from this chapter.

### Section 7 — References (REQUIRED)

Peer-reviewed papers + canonical docs + production blog posts. Format:
- **Author et al. (Year).** *Title.* Venue. arXiv:NNNN.NNNNN. One-line description of why this reference matters.

Link to arXiv where applicable. Include at least one production blog post or canonical implementation repo so the reader can see how the concept ships in practice, not just how it is described in papers.

### Section 8 — Cross-References (REQUIRED)

Use these four labels in this order:

- **Builds on:** explicit prerequisite chapters (the reader should have done these first).
- **Distinguish from:** adjacent topics that are commonly conflated. **This section is high-leverage; do not skip it.** It is what makes a candidate sound senior in interviews.
- **Connects to:** later chapters that use this material as a building block.
- **Foreshadows:** chapters where this material reaches its full production shape (often W11 System Design or W12 Capstone).

Cross-references must be bidirectional — if W7 says "Builds on: W4 ReAct", then W4 should say "Connects to: W7 Tool Harness". When you add a forward link, add the reverse link in the target chapter in the same edit.

### Section 9 — Frontmatter (REQUIRED on new chapters)

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
- **Production considerations.** When the chapter has a clear production deployment story, add a `## Production Considerations` section before §5 Bad-Case Journal. Cover sandboxing, cost ceilings, multi-tenancy, observability.

## Pre-commit checklist (run mentally before every chapter commit)

```
[ ] §1  Why This Week Matters — ~150 words present
[ ] §2  Theory Primer — ~1000 words, papers cited, real numbers
[ ] §3  Mermaid diagram present and labeled
[ ] §4  Lab phases numbered, time-budgeted, with runnable code
[ ] §4  Expected metrics table present
[ ] §4  Per-Python-block bundle present (Architecture mermaid → Code → Walkthrough → Result → Insight) for every Python script
[ ] §4  Mermaid hygiene: default `flowchart TD` (LR only for side-by-side subgraph clusters); edge-label parens quote-wrapped (`-->|"text<br/>(parens)"|`); subgraph titles ≤22 chars (no wrap/clip); horizontal multi-cluster layouts use `~~~` invisible-link chaining; node labels use `<br/>` not `\n`; TD blocks open with `%%{init: ... 'fontSize':'20px' ...}%%`, LR cluster blocks open with `%%{init: ... 'fontSize':'28px', ... 'useMaxWidth':false, 'subGraphTitleMargin':{'top':20,'bottom':30}, 'nodeSpacing':40, 'rankSpacing':50 ...}%%` for article-body-sized text + no title-vs-first-node overlap
[ ] §5  Bad-Case Journal — 3–5 entries in exact 3-field format
[ ] §5  New entries copied to global Bad-Case Journal.md
[ ] §6  Interview Soundbites — 2–3, user-voice, ~70 words, measured-outcome anchored
[ ] §7  References — papers + docs + production examples
[ ] §8  Cross-References — Builds on / Distinguish from / Connects to / Foreshadows
[ ] §8  Reverse links added in linked chapters
[ ] §9  Frontmatter updated
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
