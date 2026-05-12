# Agent Development Curriculum

A 12-week, project-driven curriculum for cloud / infrastructure engineers transitioning into **AI Agent / LLM Engineer** roles. Authored as an Obsidian vault. Companion to the lab repo [`shaneliuyx/agent-prep`](https://github.com/shaneliuyx/agent-prep).

> **Tone**: each chapter is a long-form pedagogical document — theory primer, hands-on lab, bad-case journal, interview soundbites. No tutorial graveyard. Every week ends with a runnable artifact + measured number.

## How to read

Open `Agent Development 3-Month Curriculum.md` first — top-level overview + discipline rules. Then walk the weeks in order. Decimal-numbered weeks (`Week 2.5`, `Week 2.7`, etc.) are *electives* that cut between sequentially-prerequisite weeks; they're optional but strongly recommended for senior interview prep.

```
Week 0  — Environment Setup
Week 1  — Vector Retrieval Baseline
Week 2  — Rerank and Context Compression
Week 2.5 — GraphRAG on a Wikipedia Subset       ← v12.4m: 0.96 judge, 32/0/0 vs vector
Week 2.7 — Structure-Aware RAG (PageIndex)      ← 16/16 GT-judge vs Vector 0.500 / Graph 0.375
Week 3  — RAG Evaluation                        ← RAGAS, HyDE, Phoenix
Week 3.5 — Cross-Session Memory                 ← 15/15 + Phase 5 mem0 cross-check (10/14)
Week 3.5.5 — Multi-Agent Shared Memory          ← guild MCP integration + atomic-claim race
Week 3.5.8 — Two-Tier Memory Architecture       ← guild operational + EverCore semantic + consolidation
Week 3.5.9 — Memory Benchmarks + Hypergraph     ← LongMemEval 5-way + HyperMem L3 relational tier
Week 3.7 — Agentic RAG                          ← canonical 5-node graph
Week 4  — ReAct From Scratch
Week 5  — Pattern Zoo                           ← ReAct vs PaS vs Reflexion
Week 5.5 — Metacognition
Week 6  — Claude Code Source Dive
Week 6.5 — Hermes Agent Hands-On
Week 6.7 — Authoring Agent Skills
Week 7  — Tool Harness
Week 7.5 — Computer Use and Browser Agents
Week 8  — Schema Reliability Bench
Week 8.5 — Voice AI Agents
Week 9  — Faithfulness Checker
Week 10 — Framework Shootout                    ← LangGraph vs LlamaIndex vs OAI Agents SDK
Week 11 — System Design
Week 11.5 — Agent Security
Week 12 — Capstone and Mocks
```

## What this is NOT

- **Not a tutorial collection.** Tutorials teach syntax. This teaches measured engineering — every claim is anchored in numbers from a lab `RESULTS.md` in the [`agent-prep`](https://github.com/shaneliuyx/agent-prep) sibling repo.
- **Not framework-evangelism.** Each framework week (LangGraph, LlamaIndex, OpenAI Agents SDK) ends with a head-to-head comparison on the same task, so readers can pick on data, not vibes.
- **Not opinion-free.** Each chapter takes a position (when GraphRAG wins, when HyDE loses, when reasoning models are an anti-pattern), defends it with measurements, and shows the alternative cases.

## Stack assumptions

- **Hardware**: MacBook Pro M5 Pro, 48 GB unified memory (M-series Apple Silicon).
- **Local-first inference**: oMLX serving Gemma-4-26B-heretic / Qwen3.6-35B-A3B / gpt-oss-20b on `:8000`, plus `bge-m3-mlx-fp16` for embeddings.
- **Vector DB**: Qdrant via OrbStack (Docker) on `:6333`.
- **Memory infra (Weeks 3.5.5 / 3.5.8 / 3.5.9)**: `mathomhaus/guild` (Go MCP, single binary, embedded SQLite) for operational tier; EverMind-AI's EverCore (Python + Postgres via Docker compose, port 1995) for semantic tier; HyperMem (Docker compose, port 1996) for relational L3 tier. Benchmarked via LongMemEval `oracle` subset anchored to EverCore's published 83%.
- **Observability**: Phoenix on `:6006`.
- **Cloud spend cap**: ~$10 across 12 weeks. Used only when local can't substitute (mainly Week 7 frontier model benchmarks).

Lab code: [`shaneliuyx/agent-prep`](https://github.com/shaneliuyx/agent-prep) — every chapter's lab phases are runnable artifacts there.

## Required chapter structure

Every chapter follows the same 10-section template, defined in [`CLAUDE.md`](./CLAUDE.md):

1. Why This Week Matters (~150 words — production motivation + interview signal)
2. Theory Primer (~1000 words — papers cited, real numbers)
3. Mechanism / Architecture Diagram (mermaid, every node labeled)
4. Lab Phases (numbered, time-budgeted, with runnable Python)
5. Code Walkthroughs (block-by-block per script, ★ Insight callouts, runtime tables)
6. Bad-Case Journal (3-5 entries: symptom / root cause / fix)
7. Interview Soundbites (2-3 entries, ~70 words each, anchored to measurements)
8. References (peer-reviewed papers + production blogs)
9. Cross-References (Builds on / Distinguish from / Connects to / Foreshadows)
10. Frontmatter (YAML — title, created, updated, tags, audience, stack)

`Week 2 - Rerank and Context Compression.md` is the canonical reference; new chapters should match it structurally.

## License

[MIT](./LICENSE). Curriculum prose is original; references in each chapter cite their original authors (Anthropic, Microsoft GraphRAG, RAGAS, RAPTOR, PageIndex, etc.).
