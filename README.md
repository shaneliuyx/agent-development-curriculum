# Agent Development Curriculum

A 12-week, project-driven curriculum for cloud / infrastructure engineers transitioning into **AI Agent / LLM Engineer** roles. Authored as an Obsidian vault. Companion to the lab repo [`shaneliuyx/agent-prep`](https://github.com/shaneliuyx/agent-prep).

> **Tone**: each chapter is a long-form pedagogical document — theory primer, hands-on lab, bad-case journal, interview soundbites. No tutorial graveyard. Every week ends with a runnable artifact + measured number.

## How to read

Open `Agent Development 3-Month Curriculum.md` first — top-level overview + discipline rules. Then walk the weeks in order. Decimal-numbered weeks (`Week 2.5`, `Week 2.7`, etc.) are *electives* that cut between sequentially-prerequisite weeks; they're optional but strongly recommended for senior interview prep.

```
Week 0  — Environment Setup
Week 0.3 — Agent History + Foundational Narrative ← 5-era lineage (symbolic → reactive → BDI → RL → LLM) + 3-property agent def (hello-agents Ch1+2, SPEC, v0)
Week 0.5 — LLM Internals Speedrun              ← tokenize → embed → QKV → sample (interview Q13/Q14 cover, SPEC, v0)
Week 1  — Vector Retrieval Baseline
Week 2  — Rerank and Context Compression
Week 2.5 — GraphRAG on a Wikipedia Subset       ← v12.4m: 0.96 judge, 32/0/0 vs vector
Week 2.7 — Structure-Aware RAG (PageIndex)      ← 16/16 GT-judge vs Vector 0.500 / Graph 0.375
Week 3  — RAG Evaluation                        ← RAGAS, HyDE, Phoenix
Week 3.5 — Cross-Session Memory                 ← 15/15 + Phase 5 mem0 cross-check (10/14)
Week 3.5.5 — Multi-Agent Shared Memory          ← guild MCP integration + atomic-claim race
Week 3.5.8 — Two-Tier Memory Architecture       ← guild operational + EverCore semantic + Phase 8.6 bitemporal supersede/coexist (5/5 tests)
Week 3.5.9 — Requirement-Driven Memory Arch.    ← LongMemEval decomposition + 6-backend matrix (1-tier / 2-tier / hybrid / three-tier HyperMem L3)
Week 3.5.95 — Self-Observability Memory         ← PAI v7.6 OBSERVABILITY + LEARNING self-facing axes (SPEC, v0)
Week 3.7 — Agentic RAG                          ← canonical 5-node graph
Week 4  — ReAct From Scratch                    ← + §1.5 MLX Studio gateway role-map (2026-05-15 sync)
Week 4.5 — Model Routing and Effort Tiering     ← local Qwen-1.5B classifier + cost-latency Pareto front (SPEC, v0)
Week 4.6 — Durable Agent Runtime + Topologies   ← AutoGPT executor/scheduler/lock kernel + PraisonAI 4-mode process (SPEC, v0)
Week 5  — Pattern Zoo                           ← ReAct vs PaS vs Reflexion
Week 5.5 — Metacognition
Week 5.6 — ISA-Driven Metacognition             ← PAI v5.0 Ideal-State Artifact as falsifiable termination contract (SPEC, v0)
Week 6  — Claude Code Source Dive
Week 6.4 — Low-Code Agent Platforms (Dify / Coze / n8n / LangFlow) ← 5-axis low-code-vs-custom matrix + Dify/Coze/n8n side-by-side (hello-agents Ch5, SPEC, v0)
Week 6.5 — Hermes Agent Hands-On
Week 6.6 — MCP Schema Bridge                    ← type-hint → JSON Schema producer + AsyncGenerator streaming (SPEC, v0)
Week 6.7 — Authoring Agent Skills
Week 6.8 — Agent Communication Protocol Survey  ← MCP / A2A / ANP (SPEC, planned)
Week 6.85 — Prompt Template Engineering Patterns ← 5-axis design space + schema-enforce + 4 anti-patterns (interview Q1, SPEC, v0)
Week 6.9 — Context Engineering + Todo Mechanisms ← 4 context shapes + cognitive-narrowing argument + 80-LOC TodoList primitive (interview Q11, SPEC, v0)
Week 7  — Tool Harness
Week 7.3 — Production LLM Infrastructure          ← gateway + caching + cost attribution + fallback (Akshay 6-area #2+#5)
Week 7.5 — Computer Use and Browser Agents
Week 7.7 — Quantization + Inference Optimization ← FP16 → MXFP4 hierarchy + KV-cache math + memory-bound regime (JD#1, SPEC, v0)
Week 7.8 — Code-Agent Patterns (AST + Coverage + Mocks) ← tree-sitter + LSP + branch coverage + 4-class testability filter (interview Q3-Q7, SPEC, v0)
Week 8  — Schema Reliability Bench
Week 8.5 — Voice AI Agents
Week 8.7 — Generative Media + Fine-tuning       ← diffusion + LoRA + ControlNet + IP-Adapter for brand-consistent gen (JD#4, SPEC, v0)
Week 9  — Faithfulness Checker
Week 9.3 — Agent Performance Evaluation         ← AgentBench / GAIA / SWE-bench + 5-dim per-trajectory rubric + LLM-as-judge with Cohen's κ (hello-agents Ch12, SPEC, v0)
Week 9.5 — Agentic RL Fine-Tuning (SFT + GRPO)  ← LoRA r=16 SFT + GRPO group-relative + 4-row ablation table on GSM8K-mini (hello-agents Ch11)
Week 10 — Framework Shootout                    ← LangGraph vs LlamaIndex vs OAI Agents SDK
Week 11 — System Design
Week 11.5 — Agent Security
Week 11.6 — Production Tracing + Cost Telemetry ← OpenTelemetry + Langfuse + DuckDB rollups + p99 vs mean argument (JD#2, SPEC, v0)
Week 11.7 — Take-Home Dress Rehearsal           ← 4-hour timed take-home + evals-first git discipline + 5-min Loom defense + 30/30/25/15 rubric scoring
Week 11.8 — Continuous Training + MLOps         ← PSI drift detector + eval-gated CI + shadow ramp + MLOps Level 3 (JD#3, SPEC, v0)
Week 12 — Capstone and Mocks
```

> **Interview-prep spine:** see [[Interview Question Index]] for question → chapter → measured-anchor lookups. Use it as the pre-interview review entry point.

> **FDE career track:** see [[FDE Track - Forward Deployed Engineer Path]] — an overlay note that maps every week above onto the Forward Deployed Engineer skill stack (agentic orchestration, evals and guardrails, production deployment, MCP integration, customer context) and gives a compressed FDE reading path. Read it if you are targeting Forward Deployed Engineer roles specifically. The customer-context gap it identifies is closed by Week 12's FDE Delivery Mode.

## How this maps to the Akshay 6-area hiring rubric (2026)

| Area | Where covered |
|---|---|
| 1. Harness engineering | W4, W5, W7, W7.8 (code-agent variant) |
| 2. Inference serving (KV cache, paged attention, spec decoding, quantization) | W0, W0.5 (LLM internals primer), W2.7 BCJ #23, **W7.7** (quantization + KV-math + memory-bound regime), W9.5 |
| 3. Structured output reliability | W8, W6.85 (prompt-template schema-enforce layer) |
| 4. Evals + observability | W3, W2.7, W3.5, **W11.6** (production tracing + cost telemetry), W11.8 (CT eval-gated CI) |
| 5. Production LLM infrastructure (gateway, caching, cost attribution, fallback) | W7.3, **W11.6** (OTel + Langfuse + DuckDB cost rollups), W4 §1.5 (MLX Studio gateway) |
| 6. Fine-tune vs in-context | W9, W9.5, **W8.7** (diffusion LoRA + DreamBooth for brand-consistent generation) |
| 7. Production ML / CI-CD-CT (additional JD axis) | **W11.8** (PSI drift detection + eval gates + shadow ramp + MLOps Level 3) |
| 8. Code-agent skills (additional JD axis) | **W7.8** (AST + LSP + branch coverage + mock-injection + 4-class testability filter) |

### Interview question coverage

The following common interview-Q clusters map to dedicated chapters:

| Question pattern | Chapter |
|---|---|
| Q1: "How are prompt templates constructed?" | W6.85 |
| Q3-Q7: AST / coverage / mocks / code parsing | W7.8 |
| Q9: "Parallelized intent recognition" | W4.5 §Phase 4 vote layer |
| Q11: "Context engineering / todo lists" | W6.9 |
| Q12: "Skills implementation" | W6.7 |
| Q13: "What does the model see when you type X?" | W0.5 |
| Q14: "Self-attention / QKV mechanics" | W0.5 |

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
