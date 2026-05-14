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
Week 3.5.8 — Two-Tier Memory Architecture       ← guild operational + EverCore semantic + consolidation + Phase 7 Qdrant stretch
Week 3.5.9 — Memory Benchmarks + Hypergraph     ← LongMemEval 5-way + HyperMem L3 relational tier
Week 3.5.95 — Self-Observability Memory         ← PAI v7.6 OBSERVABILITY + LEARNING self-facing axes (SPEC, v0)
Week 3.7 — Agentic RAG                          ← canonical 5-node graph
Week 4  — ReAct From Scratch
Week 4.5 — Model Routing and Effort Tiering     ← local Qwen-1.5B classifier + cost-latency Pareto front (SPEC, v0)
Week 4.6 — Durable Agent Runtime + Topologies   ← AutoGPT executor/scheduler/lock kernel + PraisonAI 4-mode process (SPEC, v0)
Week 5  — Pattern Zoo                           ← ReAct vs PaS vs Reflexion
Week 5.5 — Metacognition
Week 5.6 — ISA-Driven Metacognition             ← PAI v5.0 Ideal-State Artifact as falsifiable termination contract (SPEC, v0)
Week 6  — Claude Code Source Dive
Week 6.5 — Hermes Agent Hands-On
Week 6.6 — MCP Schema Bridge                    ← type-hint → JSON Schema producer + AsyncGenerator streaming (SPEC, v0)
Week 6.7 — Authoring Agent Skills
Week 7  — Tool Harness
Week 7.3 — Production LLM Infrastructure          ← gateway + caching + cost attribution + fallback (Akshay 6-area #2+#5)
Week 7.5 — Computer Use and Browser Agents
Week 8  — Schema Reliability Bench
Week 8.5 — Voice AI Agents
Week 9  — Faithfulness Checker
Week 10 — Framework Shootout                    ← LangGraph vs LlamaIndex vs OAI Agents SDK
Week 11 — System Design
Week 11.5 — Agent Security
Week 12 — Capstone and Mocks
```

## How this maps to the Akshay 6-area hiring rubric (2026)

| Area | Where covered |
|---|---|
| 1. Harness engineering | W4, W5, W7 |
| 2. Inference serving (KV cache, paged attention, spec decoding, quantization) | W0, W2.7 BCJ #23, W9.5 |
| 3. Structured output reliability | W8 |
| 4. Evals + observability | W3, W2.7, W3.5 |
| 5. Production LLM infrastructure (gateway, caching, cost attribution, fallback) | W7.3 |
| 6. Fine-tune vs in-context | W9, W9.5 |

See [`Agent Development 3-Month Curriculum.md` → "The Six Areas an AI Engineer Must Master"](./Agent%20Development%203-Month%20Curriculum.md) for the mapping table. Trend-monitoring cadence (~30 min / week) keeping this current is documented in [`Trend-Monitoring Discipline.md`](./Trend-Monitoring%20Discipline.md).

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
- **Cloud spend cap**: **~$13 across the program** (W7–8 frontier-model comparisons ~$8 + W7.3 cross-provider gateway routing ~$3 + W9.5 optional cloud GPU $0–30). Diagnostic threshold $20 — exceed it, audit which lab is leaking. Used only when local can't substitute.

Lab code: [`shaneliuyx/agent-prep`](https://github.com/shaneliuyx/agent-prep) — every chapter's lab phases are runnable artifacts there.

## Required chapter structure

Every chapter follows the same 10-section template, defined in [`CLAUDE.md`](./CLAUDE.md):

1. Why This Week Matters (~150 words — production motivation + interview signal)
2. Theory Primer (~1000 words — papers cited, real numbers)
3. Mechanism / Architecture Diagram (mermaid, every node labeled)
4. Lab Phases (numbered, time-budgeted, with per-Python-block bundle: Architecture mermaid → Code → Walkthrough → Result → ★ Insight)
5. *(deprecated — walkthroughs live inline next to their code per §4 per-block-bundle rule as of 2026-05-07)*
6. Bad-Case Journal (3-5 entries: symptom / root cause / fix; mark `(observed YYYY-MM-DD)` for entries from real lab runs, `(pre-scoped)` for theory-derived predictions pending validation)
7. Interview Soundbites (2-3 entries, ~70 words each, anchored to measurements)
8. References (peer-reviewed papers + production blogs)
9. Cross-References (Builds on / Distinguish from / Connects to / Foreshadows — bidirectional invariant)
10. Frontmatter (YAML — title, created, updated, tags, audience, stack)

`Week 2 - Rerank and Context Compression.md` is the canonical reference; new chapters should match it structurally.

## License

[MIT](./LICENSE). Curriculum prose is original; references in each chapter cite their original authors (Anthropic, Microsoft GraphRAG, RAGAS, RAPTOR, PageIndex, etc.).
