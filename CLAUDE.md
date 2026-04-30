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

## Authoring conventions (inferred from existing chapters)

Every chapter follows roughly this skeleton — match it when editing or creating:

1. **Why This Week Matters** — ~150 words. Production motivation + interview signal.
2. **Theory Primer** — long-form, ~1000 words. Cite original papers. Include real numbers, not vague claims.
3. **Mechanism / Diagram** — mermaid diagrams preferred (vault is Obsidian; mermaid renders).
4. **Lab** — runnable Python with real package versions. Numbered steps. End with verification commands and an expected metrics table.
5. **Bad-Case Journal** — 3–5 entries per chapter. Format: *Symptom → Root cause → Fix*. New entries also belong in the global `Bad-Case Journal.md`.
6. **Interview Soundbites** — 2–3 entries, ~70 words each, in user-voice, anchored to a measured outcome. These are the speak-aloud lines for mock interviews.
7. **References** — peer-reviewed papers + canonical docs + production blog posts. Link to arXiv where applicable.
8. **Cross-References** — `Builds on:` / `Distinguish from:` / `Consumed by:` lines connecting to other weeks. Maintain bidirectional links.

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
