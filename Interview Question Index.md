---
title: Interview Question Index
created: 2026-05-18
updated: 2026-05-18
tags:
  - interview-prep
  - index
  - cross-reference
audience: anyone doing a pre-interview review pass over the curriculum
stack: vault-internal lookup table
---

# Interview Question Index

Pre-interview review entry point. Map common interview-question patterns to the chapter + measured anchor that answers them. Open this file 24-48 hours before an interview; follow the wikilinks to refresh on the specific chapter sections.

> Format: each row carries a **question pattern** (paraphrased typical interview ask), the **chapter** that covers it, and a **measured anchor** — the specific number / output / commit ID that turns a soundbite from claim to evidence.

---

## Tier 1 — Foundations (LLM Internals, Tokenizer, Attention)

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "What does the model see when you type 'hello'?" | [[Week 0.5 - LLM Internals Speedrun]] Concept 1 | 5-stage pipeline: tokenize → embed → positional → blocks → sample |
| "Walk me through self-attention. Why three matrices?" | [[Week 0.5 - LLM Internals Speedrun]] Concept 2 + Phase 2 | 4-token by-hand worked example with row-0 softmax weights $(0.39, 0.14, 0.235, 0.235)$ |
| "Is the same token's vector identical at different positions?" | [[Week 0.5 - LLM Internals Speedrun]] Concept 3 + Phase 3 | Cosine sim on real MLX model: ~0.85-0.95, never 1.0 |
| "Why isn't `temperature=0` truly deterministic?" | [[Week 0.5 - LLM Internals Speedrun]] Concept 5 | Softmax tail numerical noise; near-tied logits flip on argmax |
| "What's the difference between `top_p`, `top_k`, `temperature`?" | [[Week 0.5 - LLM Internals Speedrun]] Concept 5 | Orthogonal knobs; tune in that order |

## Tier 2 — RAG (Retrieval + Eval)

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "Walk me through your RAG pipeline." | [[Week 1 - Vector Retrieval Baseline]] + [[Week 2 - Rerank and Context Compression]] + [[Week 3 - RAG Evaluation]] | hybrid recall@10 = 0.998 vs dense 0.993 |
| "When does GraphRAG win over vector RAG?" | [[Week 2.5 - GraphRAG]] | v12.4m: ALL judge 0.96, 32/0/0 W/L/T vs VectorRAG |
| "How do you evaluate a RAG system?" | [[Week 3 - RAG Evaluation]] | RAGAS faithfulness + answer relevance + Phoenix |
| "Multi-dimensional query rewriting + user-in-loop" | [[Week 3.7 - Agentic RAG]] | Self-RAG + CRAG decomposition; user-in-loop in roadmap |
| "Recall pipeline" | [[Week 1 - Vector Retrieval Baseline]] + [[Week 2.7 - Structure-Aware RAG]] | 16/16 GT-judge on PageIndex vs Vector 0.5 / Graph 0.375 |

## Tier 3 — Memory (Cross-Session, Multi-Agent, Two-Tier)

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "How would you give an agent long-term memory?" | [[Week 3.5 - Cross-Session Memory]] | 15/15 recall benchmark; mem0 cross-check 10/14 |
| "How would you architect memory for a multi-agent system?" | [[Week 3.5.8 - Two-Tier Memory Architecture]] | Two-tier 85% on 15-Q benchmark vs single-tier baselines |
| "How do you handle long-term agent memory under contradiction?" | [[Week 3.5.8 - Two-Tier Memory Architecture]] §9.6 | 6-action classifier (add/update/supersede/coexist/delete/no-op); 5/5 tests PASS in 76.5s |
| "What did you learn building a consolidation pipeline?" | [[Week 3.5.8 - Two-Tier Memory Architecture]] §3 | Idempotency / ordering / failure isolation; `facts_deduplicated=2` on duplicate-scroll test |
| "Atomic-claim race in multi-agent systems" | [[Week 3.5.5 - Multi-Agent Shared Memory]] | guild SQLite `UPDATE WHERE owner IS NULL` primitive |

## Tier 4 — Agents (ReAct, Routing, Tools, Skills)

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "Build a ReAct loop from scratch" | [[Week 4 - ReAct From Scratch]] | ~150 LOC no-framework |
| "MLX Studio gateway + role map" | [[Week 4 - ReAct From Scratch]] §1.5 | 7-role ROLE_MAP; gateway adds 0% overhead; JANG `tool=1.00` vs heretic `tool=0.00` |
| "How do you route between model tiers?" | [[Week 4.5 - Model Routing and Effort Tiering]] | 3 tiers × 3 modes classifier + BART vote + 4-way bench |
| "How do you parallelize intent recognition?" | [[Week 4.5 - Model Routing and Effort Tiering]] §Phase 4 | `asyncio.gather` vote layer + SQLite disagreement log + safety-bias tie-break |
| "How do you control inference cost?" | [[Week 4.5 - Model Routing and Effort Tiering]] §Phase 5 | $-cost rate card; 4-way Pareto bench |
| "Single-agent vs multi-agent / sub-agent design" | [[Week 3.5.5 - Multi-Agent Shared Memory]] + [[Week 5 - Pattern Zoo]] | guild as operational tier for sub-agent handoff |
| "Skills implementation" | [[Week 6.7 - Authoring Agent Skills]] | Anthropic Claude Skills pattern; markdown + code package |

## Tier 5 — Prompt Engineering + Context

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "How are prompt templates constructed?" | [[Week 6.85 - Prompt Template Engineering Patterns]] | 5-axis design space; schema-enforce-with-retry-once |
| "How do you handle malformed LLM output?" | [[Week 6.85 - Prompt Template Engineering Patterns]] §2 | Strip-fence + Pydantic validate + retry-once-with-error; turned ~30% fence-wrap failures to zero |
| "When do you use few-shot vs zero-shot?" | [[Week 6.85 - Prompt Template Engineering Patterns]] Axis 4 | 3 rules: zero / one / many; embedded-example for tight schemas |
| "Tell me about context engineering" | [[Week 6.9 - Context Engineering and Todo Mechanisms]] | 4 shapes: rolling / summarized / RAG-recalled / structured-state |
| "Why do todo lists make models more focused?" | [[Week 6.9 - Context Engineering and Todo Mechanisms]] | Cognitive narrowing; ~300 tokens for 5-item list ~3% overhead |
| "Walk me through context engineering for a long-running agent" | [[Week 6.9 - Context Engineering and Todo Mechanisms]] | 80-LOC TodoList primitive + 4-state semantics + budget formula |

## Tier 6 — Code Agents

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "How does your code agent parse code?" | [[Week 7.8 - Code-Agent Patterns AST Coverage Mocks]] | tree-sitter AST + multilspy LSP; LSP queries ~10-50ms vs LLM ~1-5s |
| "Branch coverage statistics + AST instrumentation" | [[Week 7.8 - Code-Agent Patterns AST Coverage Mocks]] Concept 3 | `coverage.py --branch`; sys.settrace mechanism |
| "Which code can't your agent generate unit tests for?" | [[Week 7.8 - Code-Agent Patterns AST Coverage Mocks]] Concept 4 | 4 classes: I/O / decorated / dynamic-dispatch / concurrency |
| "How do you mock?" | [[Week 7.8 - Code-Agent Patterns AST Coverage Mocks]] Concept 5 | DI > `patch` > monkey-patch; spec-validated MagicMock |
| "How do you improve coverage iteratively?" | [[Week 7.8 - Code-Agent Patterns AST Coverage Mocks]] §3 | Loop: missed branches → LLM prompt for edge tests; hit 92% from 65% baseline |

## Tier 7 — Inference Optimization + Production Infra

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "When do you quantize a model?" | [[Week 7.7 - Quantization and Inference Optimization]] | Bit-width hierarchy; 70B at MXFP4 = 35GB fits where FP16 doesn't |
| "Walk me through inference optimization for real-time agents" | [[Week 7.7 - Quantization and Inference Optimization]] | 3 levers: quant + KV-cache cap + memory-bound regime; M5 Pro ~30 tok/s on 20B-MXFP4 |
| "Difference between PTQ and QAT?" | [[Week 7.7 - Quantization and Inference Optimization]] Concept 2 | PTQ cheap +0.5-3% PPL; QAT for <4-bit; AWQ/GPTQ for calibration-aware |
| "Memory-bound vs compute-bound" | [[Week 7.7 - Quantization and Inference Optimization]] Concept 4 | $\text{tok/s} = \text{Mem BW} / (N_{\text{params}} \cdot b_w)$; AR decoding is memory-bound at batch=1 |
| "How would you observe a production agent?" | [[Week 11.6 - Production Tracing and Cost Telemetry]] | OTel + Langfuse + DuckDB; 5-10% per-call overhead; 10x debuggability gain |
| "Why p99 and not mean?" | [[Week 11.6 - Production Tracing and Cost Telemetry]] Concept 4 | Heavy-tail; p99=7800ms while mean=850ms |
| "Walk me through cost attribution" | [[Week 11.6 - Production Tracing and Cost Telemetry]] §3 | $C_{\text{call}} = t_{\text{in}} \cdot p_{\text{in}} + t_{\text{out}} \cdot p_{\text{out}}$; loop=30%cost+80%calls vs finisher=30%cost+1%calls |
| "Production LLM infrastructure (gateway, caching, fallback)" | [[Week 7.3 - Production LLM Infrastructure]] | Akshay 6-area #2+#5 |

## Tier 8 — Production ML (CI/CD/CT, Drift, Eval Gates)

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "Walk me through your CI/CD/CT pipeline" | [[Week 11.8 - Continuous Training and MLOps Pipelines]] | 3 tiers; PSI 3-day rule → retrain workflow → eval gate → 5% shadow → ramp |
| "How do you detect drift in production?" | [[Week 11.8 - Continuous Training and MLOps Pipelines]] Concept 3 | PSI per feature; chi-square label dist; rolling 7-day accuracy |
| "What's MLOps Level 3 and why does it matter?" | [[Week 11.8 - Continuous Training and MLOps Pipelines]] Concept 1 | Automated retraining triggered by signals, not by humans |
| "Eval-gated deployment" | [[Week 11.8 - Continuous Training and MLOps Pipelines]] §2 | $\text{deploy iff cand} \geq \text{prod} - \epsilon$; PR gates on RAGAS faithfulness |

## Tier 9 — Generative Media

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "Fine-tune diffusion for brand-consistent generation" | [[Week 8.7 - Generative Media and Fine-tuning]] | LoRA r=16 + DreamBooth-style; 8-15 ref images; ~30 min M5 Pro training |
| "How do you evaluate generative output quality?" | [[Week 8.7 - Generative Media and Fine-tuning]] Concept 5 | CLIP + FID + human panel; CLIP saturates ~0.32; FID ~7-10 for SDXL on COCO |
| "Difference between LoRA, DreamBooth, ControlNet?" | [[Week 8.7 - Generative Media and Fine-tuning]] Concept 4 | Identity (LoRA) + structure (ControlNet) + style (IP-Adapter) — orthogonal levers |
| "Video extension + temporal consistency" | [[Week 8.7 - Generative Media and Fine-tuning]] Concept 6 | SVD I2V; AnimateDiff motion module; per-frame LoRA insufficient |

## Tier 10 — Security + System Design

| Question pattern | Chapter | Measured anchor |
|---|---|---|
| "Agent security threats" | [[Week 11.5 - Agent Security]] | (see chapter — prompt injection, data exfil, etc) |
| "System design for an agent at scale" | [[Week 11 - System Design]] | Multi-tenancy, observability, cost, fallback |
| "Framework shootout" | [[Week 10 - Framework Shootout]] | LangGraph vs LlamaIndex vs OAI Agents SDK head-to-head |

---

## How to use this index

**Pre-interview review (24-48 hours before):**

1. Skim this index → flag rows where you don't immediately recall the measured anchor.
2. Open the chapter via wikilink; re-read the specific Concept / Phase referenced.
3. Drill the soundbite (each chapter has 2-3 interview-soundbite entries in §7).
4. Note any FAILURE MODE entry from the chapter's Bad-Case Journal — interviewer probes failure modes more than happy paths.

**During the interview:**

If you're asked a question pattern that's in this index → answer with the measured anchor first, then the mechanism. "p99 latency on JANG_4M was 12 seconds" beats "p99 is generally important." The number is the engineering signal.

If you're asked a question pattern NOT in this index → that's the index's gap; flag for post-interview update.

**After the interview:**

Convert any newly-encountered question pattern into an index row. The index is a living document; each interview that asks something new is signal to add a row.

---

## Index maintenance

This file is in the vault root. When a new chapter is added:

1. Identify which Tier (1-10) the chapter belongs to (or add a new Tier).
2. Add rows for the chapter's interview soundbites (§7 of the chapter).
3. Include measured-anchor numbers — pull from `RESULTS.md` in the lab repo, NOT from vibes.
4. Update the chapter's Cross-References (§9) to back-link to this index.

If a chapter's measured numbers change (lab re-run produces new numbers), update the anchor cell here too. The whole index should agree with the chapters at any commit.
