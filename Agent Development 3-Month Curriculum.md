---
title: Agent Development 3-Month Curriculum
created: 2026-04-23
tags:
  - agent
  - llm
  - rag
  - interview
  - mlx
  - local-first
audience: Cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles
stack: Local-first MLX. oMLX serves Qwen3.6-35B-A3B-nvfp4 + gemma-4-26B-A4B-it-heretic-4bit + gpt-oss-20b-MXFP4-Q8. vMLX serves gemma-4-31B-uncensored-heretic-mlx-4bit. Cloud spend ≈ $8 across 12 weeks.
---

# Agent Development 3-Month Curriculum

> A 12-week, project-driven study plan to convert a cloud infrastructure background into a hireable Agent / LLM Engineer profile.
> All hands-on labs default to local MLX inference on Apple Silicon. Cloud API spend is capped at ~$10 across the entire program.

---

## How to Use This Guide

**Time budget.** Plan ~12–15 hours per week: 4 hours theory/reading, 6–8 hours hands-on lab, 1–2 hours flashcards + mock answers. If you only have 8 hours, drop the flashcards and stretch each week to 1.5 weeks (≈ 18 weeks total) — do **not** drop the labs.

**Discipline rules.**
1. **No tutorial graveyard.** If you finish a week without a runnable artifact + measured number, you have not finished the week.
2. **Every lab gets a `RESULTS.md`.** Numbers, screenshots, what broke, what you fixed. This becomes your portfolio narrative and your bad-case journal.
3. **Speak the answers out loud.** Reading is recognition; speaking is recall. Interview signal lives in recall.
4. **Local first, cloud only when you must.** The whole point of the local stack is to remove the "API-cost anxiety" tax that makes people skip experiments.

**Output of the program.** By Week 12 you should have:
- 1 portfolio repo on GitHub (the capstone)
- 3 smaller "lab" repos linked from it
- ~300 Anki cards
- ~30 recorded mock-interview answers (audio is fine)
- A bad-case journal (single markdown, ~1,500 words) that becomes your behavioral-question fuel
- A 1-pager "system design cheat sheet" for whiteboard rounds

---

## Conceptual Framework — The Three Engineering Paradigms

Understanding where this curriculum sits in the 2024–2026 arc of AI engineering prevents you from treating it as a collection of disconnected skills.

### The nested structure

```
┌────────────────────────────────────────────────────┐
│  HARNESS ENGINEERING  (2026+)                      │
│  "What system should I build around the model?"    │
│  Reliability impact: 50–80% improvement            │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  CONTEXT ENGINEERING  (2025)                 │  │
│  │  "What information should I provide?"        │  │
│  │  Reliability impact: 15–30% improvement      │  │
│  │                                              │  │
│  │  ┌──────────────────────────────────────┐    │  │
│  │  │  PROMPT ENGINEERING  (2022–2024)     │    │  │
│  │  │  "What should I say to the model?"   │    │  │
│  │  │  Reliability impact: 5–15% improve.  │    │  │
│  │  └──────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

Each layer *absorbs* the previous one — it does not replace it. A harness contains a context window which contains prompts. Removing harness engineering destroys the container, not just one layer.

### Why the numbers matter

The same model (Claude Opus 4.5) scored **2% vs 12%** on a benchmark purely by changing the surrounding harness, with zero prompt changes. That 6× gap comes entirely from the environment. Martin Fowler (2025): *"An agent is a model plus a harness. The model is the intelligence; the harness is everything else."*

Andrej Karpathy on context engineering (2025): *"the delicate art of filling the context window with just the right information."* Context engineering is where most practitioners plateau — they optimize prompts but never instrument the context filling, the retrieval quality, or the information freshness that actually determines what the model reasons over.

Harness engineering is the step above: the loop structure, tool dispatch, retry/budget governance, verification passes, state persistence, and routing logic that *executes* around the model. This curriculum is primarily a harness engineering curriculum with context engineering embedded in every lab.

### Where CLI/Bash and MCP fit

A common false dichotomy is "bash vs MCP." The real question is token budget:

| Invocation style | Approx. token overhead | When to use |
|---|---|---|
| CLI / Bash subprocess | 500–2K tokens | Tight-context agents; quick file/git ops |
| MCP (optimized, schema-loaded lazily) | ~2K tokens | Standard tool contract; multi-model portability |
| MCP (naive, all schemas eager-loaded) | ~150K tokens | ← This is the anti-pattern |

The production pattern is **CLI-first, MCP-wrapper**: implement tools as CLI commands first (fast, testable, low overhead), then expose them via MCP transport when cross-model portability or the MCP ecosystem matters. The two are complementary, not competing. Linux Foundation backing for MCP (2026) makes the protocol durable; the optimization question is how you load and scope schemas, not whether to use the protocol.

---

## Local-First Stack Setup (Week 0 — Do Before Week 1)

> **Detailed step-by-step setup lives in the companion note: [[Week 0 - Environment Setup]].** This section is the summary and stack rationale; do the full setup guide before starting Week 1.

You already have **oMLX** and **vMLX** installed with a 4-model fleet on disk at `~/.omlx/models/`. Build the rest of the toolchain around it so cloud spend stays near zero.

### Your Model Fleet (already on disk)

| Model | Size | Architecture | Server | Tier | Best for |
|---|---|---|---|---|---|
| **Qwen3.6-35B-A3B-nvfp4** | ~19 GB | MoE (35B total, ~3B active/token), NVidia FP4 quant | oMLX :8000 | "opus" | Tool calling, agent loops, complex reasoning. **Latency closer to a 3B dense model** thanks to MoE; quality closer to a 35B dense. Strongest open tool-calling training as of 2026. |
| **gemma-4-26B-A4B-it-heretic-4bit** | ~14.6 GB | Dense 26B, A4B variant, 4-bit, **heretic = community-uncensored** | oMLX :8000 | "sonnet" | RAG synthesis, summarization, faithfulness checking. Long-context, strong instruction following. |
| **gpt-oss-20b-MXFP4-Q8** | ~11.3 GB | Dense 20B, MXFP4 + Q8 hybrid quant | oMLX :8000 | "haiku" | High-iteration loops, multi-agent worker tier, fast classifiers. **The only interview-safe model in your fleet** (clean OpenAI release, no refusal removal). |
| **gemma-4-31B-uncensored-heretic-mlx-4bit** | ~19 GB | Dense 31B, JANG v2.0 + crack-surgery refusal removal | vMLX | "experimental" | Self-study experiments where you want zero refusals. **Do not use in any portfolio repo, recorded mock answer, or interview demo.** |

### The Stack (libraries built around the fleet)

| Layer | Tool | Why |
|---|---|---|
| **Inference (chat / RAG)** | oMLX serving `gemma-4-26B-A4B-it-heretic-4bit` on :8000 | Sonnet-tier; cheap and high-quality long-context |
| **Inference (tool-calling / agent loops)** | oMLX serving `Qwen3.6-35B-A3B-nvfp4` on :8000 | MoE = fast; strongest 2026 open tool-calling training. Replaces the "install Qwen 2.5 14B" plan — you already have something better. |
| **Inference (worker / classifier)** | oMLX serving `gpt-oss-20b-MXFP4-Q8` on :8000 | Cheap haiku-tier for multi-agent workers, NLI judges, claim-splitters |
| **Inference (latency-critical / VLM)** | vMLX serving any of the above on a different port | Speculative decoding + prefix cache + paged KV cache → 30–50% faster on tool-heavy traces |
| **OpenAI-compatible API** | oMLX `/v1` (default :8000) and vMLX `/v1` | Standard endpoint — every Python LLM lib works against either |
| **Anthropic Messages API** | oMLX (already wired into your `cl`/`clb` aliases) and vMLX | Lets the `claude` CLI route opus → Qwen3.6, sonnet → Gemma 26B, haiku → gpt-oss 20B without code changes |
| **Embeddings** | `mlx_embedding_models` running **BGE-M3** or **Nomic-Embed-v2-MoE** | BGE-M3 = multilingual, supports dense+sparse+multi-vector in one model |
| **Reranker** | `BGE-reranker-v2-m3` via MLX | Local cross-encoder, ~50ms per pair on M-series |
| **Vector store** | **Qdrant** via Docker (or `pgvector` in Postgres) | Qdrant has the cleanest local dev story; pgvector wins if you already run Postgres |
| **Constrained decoding** | **Outlines** + `llguidance` / `xgrammar` | Outlines integrates with mlx-lm; xgrammar is 100× faster than naive grammar parsing |
| **Validation layer** | **Instructor** + **Pydantic** | Cross-provider portability; auto-retry on schema failure |
| **Observability** | **Phoenix** (Arize) self-hosted, or **Langfuse** self-hosted | Free; gives you traces, spans, eval dashboards |
| **Eval** | **RAGAS** + **TruLens** + custom pytest | RAGAS for RAG metrics, TruLens for feedback functions |
| **Cloud comparison budget** | $10 OpenAI + $10 Anthropic credits | Used **only** in Week 8 to benchmark schema reliability |

### Setup Checklist (≈ 90 minutes)

You have **three** options for the Python environment. Pick one:

- **Option A1 — Reuse oMLX's bundled MLX (saves ~5 GB).** Python 3.11.10 + mlx 0.31.1 + mlx_lm 0.31.2 + mlx_embeddings 0.1.0 + mlx_vlm 0.4.4 + mlx_audio 0.4.3. Wheels live in a sibling site-packages that needs `PYTHONPATH`; the `omlx-python` / `omlx-mlx-lm` shell wrappers in `~/.zshrc` (added 2026-04-23) handle that for you.
- **Option A2 — Reuse vMLX's bundled MLX (saves ~5 GB).** Python 3.12.12 + mlx 0.30.6 + mlx_lm 0.31.2 + mlx_embeddings 0.0.5 + mlx_vlm 0.4.4 + mlx_audio 0.4.1. Layout is cleaner — wheels are on the default `sys.path` already. The `vmlx-python` / `vmlx-mlx-lm` shell wrappers (added 2026-04-23) just point at the bundled interpreter.
- **Option B — Fresh `uv venv` (recommended for full isolation).** Adds ~5 GB but lets you pin and upgrade libs independently of either app. Below is the Option B setup.

#### oMLX vs vMLX — when to pick which

Both are MLX inference apps for Apple Silicon. Both expose OpenAI-compatible **and** Anthropic Messages API endpoints (so the `claude` CLI works against either). Both run the same model files. The differences that matter for this curriculum:

| Dimension | oMLX | vMLX |
|---|---|---|
| **UI** | Native macOS menu-bar app | Electron desktop app (richer chat UI) |
| **Bundled Python** | 3.11.10 | 3.12.12 |
| **MLX core version** | 0.31.1 (newer) | 0.30.6 |
| **Open source / pip-installable** | App-only | App + `pip install vmlx` |
| **Caching stack** | Continuous batching + SSD cache | Prefix cache + paged KV cache + KV q4/q8 quantization + continuous batching + persistent disk cache |
| **Speculative decoding** | No (as of v1.x) | Yes |
| **Per-model knobs** | Fine-grained `~/.omlx/model_settings.json` (turboquant KV, dflash, specprefill, thinking budget) | UI-driven |
| **VLM (vision-language) caching** | Partial | Full caching stack — currently the only MLX engine that does this |
| **Built-in agentic coding tools** | No | Yes (20+ ships with the app) |
| **Best for** | Lightweight always-on background server; fine-grained engine tuning per model | Latency-sensitive workflows (Week 4 ReAct, Week 7 tool harness); VLM experiments; when you want a chat UI to debug prompts |

**Recommended setup for this curriculum:** keep oMLX as your **default chat/RAG server on port 8000** (you already have it wired into your `cl`/`clb` aliases). Run **vMLX as a second backend on a different port** when you want speculative decoding for the agent-loop weeks (4, 7), or when a lab uses a VLM. You don't have to choose — both can coexist as long as their ports don't collide.

```bash
# Quick sanity check both work from CLI
omlx-python -c "import mlx.core as mx; print('oMLX:', mx.__version__, mx.default_device())"
vmlx-python -c "import mlx.core as mx; print('vMLX:', mx.__version__, mx.default_device())"
```

```bash
# 1. Python env (Option B — fresh venv)
mkdir -p ~/code/agent-prep && cd ~/code/agent-prep
uv venv --python 3.11
source .venv/bin/activate

# 2. Core MLX libs (skip if using Option A — already installed in oMLX bundle)
uv pip install mlx mlx-lm mlx-embedding-models mlx-openai-server

# 3. Tool-calling model — already on disk as Qwen3.6-35B-A3B-nvfp4 (oMLX). Skip.

# 4. Vector + observability
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant
docker run -d -p 6006:6006 --name phoenix arizephoenix/phoenix:latest

# 5. Python application libs
uv pip install qdrant-client outlines instructor pydantic ragas trulens-eval \
               langchain langchain-openai langgraph llama-index sentence-transformers \
               arize-phoenix openinference-instrumentation-openai

# 6. Inference servers — both already running via oMLX/vMLX menu-bar apps.
#    oMLX :8000 multi-routes opus/sonnet/haiku per ~/.omlx/settings.json.
#    vMLX serves gemma-4-31B-uncensored-heretic-mlx-4bit (use only for self-study experiments).
#    Pick the model per-request via the `model` field in the API call.
```

### Pointing client libraries at local

```python
from openai import OpenAI

# Single endpoint, three model tiers — oMLX routes by model name
omlx = OpenAI(base_url="http://localhost:8000/v1", api_key="Shane@7162")

# Pick the tier per task (these names match ~/.omlx/settings.json):
opus   = "Qwen3.6-35B-A3B-nvfp4"               # tool calling, agent loops
sonnet = "gemma-4-26B-A4B-it-heretic-4bit"     # RAG synthesis, summarization
haiku  = "gpt-oss-20b-MXFP4-Q8"                # workers, classifiers, NLI judges

# vMLX (different port, set via the vMLX UI — typically :8003 or :8002)
vmlx = OpenAI(base_url="http://localhost:8003/v1", api_key="not-used")
```

### Per-Week Model Routing (recommended)

| Week | Lab | Primary model | Reason |
|---|---|---|---|
| 1 | Vector baseline | `mlx_embeddings` (BGE-M3) | Embeddings, no LLM needed for retrieval itself |
| 2 | Rerank + compress | sonnet (Gemma 26B) for compression; `bge-reranker-v2-m3` for rerank | Long-context summarization plays to Gemma's strengths |
| 3 | RAG eval | sonnet for synthesis; haiku for LLM-as-judge | Cheap judge tier; better calibration than self-judging |
| 4 | ReAct from scratch | **opus (Qwen3.6 35B-A3B)** | Strongest tool-calling; MoE keeps it fast in tight loops |
| 5 | Pattern zoo (4 patterns) | opus as orchestrator/planner; **haiku (gpt-oss 20B)** as workers | Multi-agent cost discipline; haiku is fast enough to parallelize 3–5 workers |
| 6 | Claude Code source dive | sonnet for any synthesis | Reading-heavy week, model load is light |
| 7 | Tool harness | opus, then re-benchmark on **vMLX (any model + speculative decoding)** | Compare baseline tool latency vs spec-decoded |
| 8 | Schema reliability bench | All 3 oMLX tiers + vMLX/JANG + cloud GPT-4o-mini = **5-way comparison** (instead of the 3-way originally planned — you have more local diversity than the curriculum assumed) | More data points = stronger signature answer |
| 9 | Faithfulness checker | sonnet for claim-splitting; haiku for NLI judge | Structural task → Gemma; classification → cheap tier |
| 10 | Framework shootout | opus | Frameworks are the focus; pick the strongest model so framework differences dominate |
| 11 | System design rehearsal | N/A — verbal | Optional: have sonnet red-team your designs |
| 12 | Capstone | Capstone-A (RAG): sonnet. Capstone-B (coding agent): opus + haiku workers. Capstone-C (SRE agent): opus + sonnet. | Pick to match the target product |

> **Portfolio safety note (important).** **Two of your four local models are community-uncensored variants** — `gemma-4-31B-uncensored-heretic-mlx-4bit` (vMLX) and `gemma-4-26B-A4B-it-heretic-4bit` (oMLX). These are fine for *your own self-study*, where you want a model that doesn't refuse to discuss adversarial-prompt examples or red-team scenarios. They are **not** fine for anything you'll show to a hiring manager.
>
> For portfolio repos, recorded mock answers, README screenshots, and live demos, use **`gpt-oss-20b-MXFP4-Q8`** (clean OpenAI open-source release) or **`Qwen3.6-35B-A3B-nvfp4`** (clean Alibaba release). For Capstone repos that need a sonnet-tier model, swap in a clean variant from `mlx-community/gemma-4-27b-it-4bit` before publishing.
>
> The labs in this curriculum are written so any model in your fleet works — only the *publication-facing* artifacts need clean models.

---

## Phase 1 — Foundations & RAG Mastery (Weeks 1–3)

**Phase goal.** Make RAG your strongest interview dimension. You're a cloud infrastructure engineer — own the retrieval pipeline like you own a Terraform module.

> **Runbook pattern.** Each week has a dedicated step-by-step runbook in the vault: [[Week 1 - Vector Retrieval Baseline]], [[Week 2 - Rerank and Context Compression]], [[Week 3 - RAG Evaluation]]. The text below is the *overview*; the runbooks are the *how*. Treat each runbook like a preflight checklist — tick phases, don't just read. Runbooks for Weeks 4–12 follow the same template and are generated on demand (see §"Runbook Generation Pattern" at the bottom of this file).

### Week 1 — Embedding & Vector Retrieval Fundamentals
> Detailed runbook: [[Week 1 - Vector Retrieval Baseline]]

**Theory (4h).**
- Read: BGE-M3 paper (sections 1–4), Nomic Embed v2 paper, the Anthropic "Contextual Retrieval" blog post, Pinecone "What is a vector database" deep-dive.
- Concepts to master: dense vs sparse, BM25 + dense hybrid, ANN index types (HNSW, IVF, PQ, scalar quantization), recall@k vs MRR vs nDCG, embedding-model dimensionality vs cost tradeoff, cosine vs dot vs L2.

**Lab (8h) — `lab-01-vector-baseline`.**
1. Pull a 10K-doc corpus. Use the **MS MARCO dev set** (it has labeled query–doc relevance, free).
2. Embed with three models locally: `bge-m3`, `nomic-embed-text-v2`, `all-MiniLM-L6-v2`. Time it. Measure VRAM/RAM peak.
3. Index in Qdrant with HNSW; reindex with IVF-Flat. Measure index build time + query latency.
4. Compute recall@10, MRR@10, nDCG@10 on the labeled queries.
5. **Write `RESULTS.md`** with a comparison table and a 3-paragraph "what I learned."

**Exit criteria.** You can answer: "How would you choose an embedding model for a Chinese legal-document corpus?" and back it up with numbers from your own table.

**Infra bridge.** Vector indexing is just another Terraform apply. Frame chunking + embedding as a Spark/Terraform-style transformation: idempotent, partition-aware (by source doc), versioned (embedding model + chunker config = composite version key). This framing is gold in interviews.

### Week 2 — Chunking, Reranking, Context Compression
> Detailed runbook: [[Week 2 - Rerank and Context Compression]]

**Theory (4h).**
- Read: LlamaIndex chunking guide (semantic + sliding + parent-doc), Cohere Rerank docs, the original ColBERTv2 paper (skim §3), the "Contextual Compression" page in LangChain docs, the CAG (Cache-Augmented Generation) explainer.
- Master: bi-encoder vs cross-encoder, chunk-size vs overlap tradeoff, parent–child retrieval (small chunks for matching, big chunks for context), MMR diversification, contextual compression via LLM, summary-tree retrieval.

**Lab (8h) — `lab-02-rerank-compress`.**
1. Take Week 1's retrieval pipeline. Add the **BGE-reranker-v2-m3** stage on top-50 → top-5.
2. Re-measure recall@5 and nDCG@5 vs Week 1 baseline. Plot.
3. Add a **context-compression** stage: feed top-5 + query to your local Gemma-4-31B with prompt "extract only spans that answer the query." Measure token reduction and answer quality.
4. Build a **chunking sweep**: 256 / 512 / 1024 tokens × overlap 0 / 64 / 128. 9-cell heatmap of recall@5.

**Exit criteria.** You can defend a specific chunking strategy with your own numbers, and you can explain why reranking helps (cross-attention over query-doc pair > independent dot product).

**Infra bridge.** The reranker is a "feature engineering" layer. The compression stage is a "lossy serialization" — the same tradeoffs you make picking Parquet codecs.

### Week 2.5 — GraphRAG on a Wikipedia Subset (half-week insert, ~6h)
> Detailed runbook: [[Week 2.5 - GraphRAG]]

**Theory (2h).**
- Read: Microsoft GraphRAG paper (skim §3 + §5), LlamaIndex `KnowledgeGraphIndex` docs, neo4j-graphrag quickstart.
- Master: why vector RAG fails on multi-hop queries, the three stages of GraphRAG (entity extraction → community detection → query traversal), the production hybrid-routing pattern (classifier → vector vs graph vs both).

**Lab (4h) — `lab-02-5-graphrag`.**
1. Run Neo4j in Docker. Ingest 200 Wikipedia articles; extract entity/relationship triples with local Gemma-4-26B.
2. Build a GraphRAG query (seed-entity extraction → 2-hop subgraph retrieval → cited answer generation).
3. Hand-write 25 multi-hop eval questions; run **head-to-head vs Week 2's vector-RAG** pipeline on the same questions. Record recall, latency, and win/loss per question.

**Exit criteria.** 90-second answer to "When does GraphRAG beat vector RAG, and when does it lose?" grounded in your own numbers, plus a clear statement of the production hybrid pattern.

**Infra bridge.** GraphRAG ingestion is a materialised view: expensive to build, cheap at query time. Vector RAG is an index: cheap to build, only answers nearness queries. In production you run both, routed by a query classifier — same as dual-writing to Kafka for hot and cold-path analytics.

### Week 3 — Advanced RAG & Evaluation
> Detailed runbook: [[Week 3 - RAG Evaluation]]

**Theory (4h).**
- Read: HyDE paper, Self-RAG paper (skim), GraphRAG (Microsoft) intro post, RAGAS docs (faithfulness, context-precision, context-recall, answer-relevancy), Anthropic's "Building effective agents" post (the "agentic RAG" section).
- Master: query rewriting, multi-query fusion (RAG-Fusion), HyDE, sub-question decomposition, GraphRAG vs vanilla, agentic RAG (the model decides what to retrieve next).

**Lab (8h) — `lab-03-rag-eval`.**
1. Build a **RAGAS eval harness** on a 50-question dev set (write your own, drawn from the corpus).
2. Implement two upgrade paths and A/B them: (a) add HyDE; (b) add multi-query fusion. Score both vs the Week 2 baseline on faithfulness + context-precision + answer-relevancy.
3. Wire the whole thing into **Phoenix** so every retrieval has a trace.
4. Write a 1-page "RAG architecture decision record" (ADR) explaining your final pipeline.

**Exit criteria.** Cold-answer 25 RAG interview questions from Appendix A. Have one repo with a green `make eval` showing real RAGAS numbers.

**Infra bridge.** Your RAG eval harness = your OPA policy checks. The ADR format = your standard data architecture decision record. Bring both to interviews.

### Week 3.5 — Cross-Session Memory (half-week insert, ~5h)
> Detailed runbook: [[Week 3.5 - Cross-Session Memory]]

**Theory (2h).**
- Read: mem0 README + architecture post, Anthropic's "agent memory" patterns, LangGraph `add_messages` + `MemorySaver` docs.
- Master: the four memory types (working / episodic / semantic / procedural), the extract→store→retrieve→inject lifecycle, why naive turn-dumping fails, three forgetting strategies (TTL, confidence eviction, contradiction-triggered update).

**Lab (3h) — `lab-03-5-memory`.**
1. Stand up mem0 + Qdrant (reuse Week 1's instance) + SQLite. Dual-store: Qdrant for episodic memories, SQLite for semantic facts with an archive-on-contradiction rule.
2. Build `src/chat.py` — a REPL agent that `recall()`s at turn-start and `remember_turn()`s at turn-end.
3. Ship a non-interactive `demo_three_sessions.py` that proves cross-session recall (session 1 seeds facts; session 3 uses them in answering a compound question).
4. Write a 15-question recall benchmark (`tests/test_recall.py`), target ≥ 12/15 passing. Include at least one contradiction-update test and one multi-fact composition test.

**Exit criteria.** 90-second answer to "how do you give an agent long-term memory?" that names the four types, the lifecycle, and the forgetting strategies. The three-session demo transcript belongs in your portfolio.

**Infra bridge.** User memory is a slowly-changing dimension (SCD-2). Every contradiction archives the old row and writes a new one — identical to how a data warehouse tracks customer addresses. Archive-don't-delete isn't ops hygiene; it's SCD-2 by another name, and that framing lands with senior interviewers.

---

## Phase 2 — Agent Design Patterns & Claude Code Source Study (Weeks 4–6)

**Phase goal.** Stop being a demo-builder. Understand exactly why agents are unstable in production and how Claude Code (the current public reference implementation) fixes those failure modes.

### Week 4 — The ReAct Loop, Built From Scratch
> Detailed runbook: [[Week 4 - ReAct From Scratch]]

**Theory (4h).**
- Read: ReAct paper (Yao et al. 2022), Toolformer paper (skim §3), Anthropic's "Building effective agents" (Sept 2024 + 2026 updates), Lilian Weng's "LLM Powered Autonomous Agents" post.
- Master the canonical loop:
  ```
  context = system_prompt + tools_schema + user_msg + scratchpad
  while not done and iter < MAX_ITER:
      response = llm(context)
      if response.has_tool_calls:
          for call in response.tool_calls:
              result = dispatch(call)
              scratchpad.append((call, result))
      else:
          done = True
      context = system_prompt + tools_schema + user_msg + scratchpad
  return response.text
  ```

**Lab (8h) — `lab-04-react-from-scratch`.**
1. Implement the loop above in **~150 lines of Python**, no framework. Use `mlx-openai-server` with Qwen 2.5 14B as the model.
2. Tools: `web_search` (use a free DuckDuckGo wrapper), `python_repl` (sandboxed), `read_file`, `write_file`.
3. Add **observability** by hand: log every (iteration, prompt_tokens, completion_tokens, tool_name, tool_latency, tool_error) row to a SQLite table.
4. Build a **bad-case test suite** with 10 scenarios designed to break the loop:
   - infinite tool-calling loop
   - hallucinated tool name
   - tool returns a 50KB blob that overflows context
   - tool returns malformed JSON
   - model emits tool call with missing required arg
   - model "decides" mid-loop to stop without finishing
   - circular reasoning (calls same tool with same args 5x)
   - tool times out
   - tool returns an error message and model ignores it
   - context window approaches limit mid-loop
5. For each: identify the failure mode, then patch your loop. Document patches.

**Exit criteria.** Whiteboard the loop from memory. Name 5 stability failure modes and your mitigation for each.

**Infra bridge.** A ReAct loop is a Kubernetes reconciliation loop. The mitigations (idempotency keys, retry budgets, dead-letter queues, circuit breakers) are exactly the patterns you already use.

### Week 5 — Beyond ReAct: Plan-and-Solve, Reflexion, Multi-Agent
> Detailed runbook: [[Week 5 - Pattern Zoo]]

**Theory (4h).**
- Read: Plan-and-Solve paper, Reflexion paper, Tree-of-Thoughts (skim), Self-Refine, "Orchestrator-Worker" pattern from Anthropic's effective-agents post, LangGraph "graph as agent state machine" docs, AutoGen conversational pattern, CrewAI role-based pattern.
- Build a mental decision tree for "when to use which": linear task → ReAct; long-horizon planning → Plan-and-Solve; iterative quality improvement → Reflexion / Self-Refine; parallelizable subtasks → Multi-agent (orchestrator + workers); deeply branching exploration → Tree-of-Thoughts (rare in production).

**Lab (8h) — `lab-05-pattern-zoo`.**
1. Take one task — "research a company and produce a 1-page summary with citations" — and implement it 4 ways:
   - **(a) ReAct** (your Week 4 loop reused)
   - **(b) Plan-and-Solve** (planner LLM emits a numbered plan; executor runs each step; replanner triggered on step failure)
   - **(c) Reflexion** (ReAct + a critic LLM that produces written self-critique appended to the next iteration)
   - **(d) Multi-agent orchestrator-worker** (one orchestrator delegates "find sources", "extract financials", "summarize" to three workers in parallel)
2. Run all four on the same 10 companies. Measure: success rate, total tokens, total wall time, output quality (rubric-scored by Gemma-4-31B as judge).
3. Build a comparison table.

**Exit criteria.** Defend each pattern's tradeoffs from your own data. Articulate when reflexion makes things **worse** (it often does — it can amplify confident errors).

**Infra bridge.** Multi-agent = distributed compute. Orchestrator = scheduler. Workers = executors. Communication = message bus. Don't forget the dead-letter queue.

### Week 6 — Claude Code Source Dive
> Detailed runbook: [[Week 6 - Claude Code Source Dive]]

**Theory (6h).**
- Background: in March 2026, the v2.1.88 npm package shipped with a 59.8 MB sourcemap that exposed ~1,900 source files and ~512K LOC of TypeScript. Multiple write-ups now exist analyzing the architecture — read them in this order:
  1. **bits-bytes-nn** — Claude Code Architecture Analysis (best high-level overview)
  2. **VILA-Lab Dive-into-Claude-Code** GitHub (systematic analysis with diagrams)
  3. **DEV.to "Architecture Explained: Agent Loop, Tool System, Permission Model"** (focused on the three core subsystems)
  4. **engineerscodex Substack** post (engineering perspective)
- The headline insight: **only ~1.6% of the codebase is "AI logic." The other 98.4% is deterministic infrastructure** — permission gates, context management, tool routing, recovery logic, append-only session storage, MCP/plugin/skill/hook extensibility.

**Lab (6h) — `lab-06-claude-code-map`.**
- For each subsystem below, write a 1-paragraph "what problem does this solve" + a "how would I steal this idea for my own agent" line:
  1. **Agent loop** (the while-loop core)
  2. **Permission system** (7 modes + ML-based classifier)
  3. **5-layer compaction pipeline** (how context is squeezed when it gets long)
  4. **Tool routing** (built-in tools vs MCP vs subagents vs skills vs hooks)
  5. **Subagent dispatch** (how Task tool spawns isolated child agents with their own context)
  6. **Append-only session storage** (why it's append-only, not mutate-in-place)
  7. **Hook system** (PreToolUse, PostToolUse, Stop — and why deterministic guardrails beat "asking the model nicely")
  8. **Hidden PROACTIVE / KAIROS feature flags** (the always-on autonomous mode)
- Output: a single markdown "Claude Code Architecture Cheat Sheet" — bring this to interviews.

**Exit criteria.** You can sketch Claude Code's architecture on a whiteboard in 5 minutes. You can name three design decisions you'd copy and one you'd change.

**Infra bridge.** Append-only session storage = event sourcing. 5-layer compaction = your tiered storage strategy (hot/warm/cold). Permission classifier = your data-access RBAC. You've shipped all of these before.

---

## Phase 3 — Stability: Tools, Schema, Hallucination (Weeks 7–9)

**Phase goal.** Own the hard parts. This is where most candidates wash out and where senior signal is generated.

### Week 7 — Function Calling / Tool Use in Production
> Detailed runbook: [[Week 7 - Tool Harness]]

**Theory (4h).**
- Read: OpenAI function-calling docs, Anthropic tool-use docs, Gemini tool-use docs, the **MCP (Model Context Protocol)** spec — Anthropic introduced MCP in Nov 2024; OpenAI and Google adopted it in 2025–2026, OpenAI's Assistants API is being sunset mid-2026. Building on MCP now = less migration work later.
- Master: tool-definition design (clear name, terse description, strict JSON schema params), parallel tool calls, error-message-as-prompt (return errors so the model can self-correct on next iter), max-iteration guards, idempotency keys for non-idempotent tools, latency budgets, cost guards, timeout handling, ABI differences across providers.

**Lab (8h) — `lab-07-tool-harness`.**
1. Build a generic tool-calling harness (Python) that:
   - Takes a list of `Tool` objects (name, description, JSON schema, callable)
   - Exposes one method `run(query)` that drives the loop
   - Uses Qwen 2.5 14B locally
   - Supports: parallel tool calls, retry with error feedback, max-iter cap (15), per-tool timeout, per-tool budget (max calls)
   - Logs every event to Phoenix
2. Build a **bad-case test suite** of 20 scenarios (extend Week 4's 10):
   - tool returns `{"error": "rate limited"}` → does the loop back off?
   - two tools have similar names — does the model pick the right one?
   - tool requires arg `user_id: int` — does it fail clean on `"abc"`?
   - tool description is ambiguous — does the model hallucinate a use case?
   - tool returns inconsistent schema across calls — does the loop crash?
   - …(15 more, document each)
3. Run the same suite against a cloud model (Anthropic Claude Haiku, ~$0.50 of credit) and compare reliability. **This is your only cloud spend in Phase 3.**

**Exit criteria.** Cold-answer "What are the 5 things you do to make tool calling reliable in production?" with concrete examples from your own harness.

**Infra bridge.** Tool calls are RPC. Your tool harness is an RPC client with retry, backoff, circuit-breaker, dead-letter-queue, and instrumentation. Frame it as such in interviews — it lands.

### Week 8 — The Schema Reliability Playbook (Your Signature Question)
> Detailed runbook: [[Week 8 - Schema Reliability Bench]]

This is the week that earns you offers. Detailed playbook is in **Appendix B**; this week is the lab.

**Theory (3h).** Read Appendix B start to finish, then read: Outlines docs, Instructor docs, OpenAI structured-outputs blog, Anthropic "tool use as JSON enforcement" pattern, the XGrammar paper, the SLOT paper, the "always put reasoning before answer in CoT schemas" gotcha post.

**Lab (10h) — `lab-08-schema-bench`.**

Build a benchmark that runs **5 schema-reliability strategies** against the **same 100 prompts** designed to elicit a strict JSON schema (mix of clean prompts, ambiguous prompts, adversarial prompts).

| Strategy | Where it runs | Cloud spend |
|---|---|---|
| **L1 — Naive prompt** ("respond in JSON matching this schema") | Local Gemma + local Qwen | $0 |
| **L2 — Provider-native JSON mode** | OpenAI gpt-4o-mini structured outputs | ~$2 |
| **L3 — Constrained decoding (Outlines + xgrammar)** | Local Qwen via mlx-lm + Outlines | $0 |
| **L4 — Instructor + Pydantic + auto-retry** | Local Qwen via mlx-openai-server | $0 |
| **L5 — Post-validation + repair prompt** (parse → if invalid, send error back to model with one retry) | Local Gemma | $0 |

Measure for each: % syntactically valid, % semantically valid (passes `pydantic.model_validate`), p50/p95 latency, total cost, retry count.

Final deliverable: a comparison table + the **canonical "5-layer defense" diagram** from Appendix B drawn in your own hand. **You walk into every interview with this in your back pocket.**

**Exit criteria.** Five-minute uninterrupted explanation of "how do you guarantee a fixed schema" — with code, numbers, and tradeoff awareness. This single answer can move you up a level.

**Infra bridge.** This is data-quality engineering applied to LLM output. Pydantic = your `OPA / Checkov`. The 5 layers = your data-quality SLA tiers (raw → bronze → silver → gold).

### Week 9 — Hallucination Detection & Mitigation
> Detailed runbook: [[Week 9 - Faithfulness Checker]]

**Theory (4h).**
- Read: SelfCheckGPT paper, the Nature 2024 semantic-entropy paper (Farquhar et al.), Lakera "LLM Hallucinations 2026" guide, "MetaRAG: Metamorphic Testing for Hallucination Detection in RAG," and Anthropic's faithfulness-evaluation cookbook.
- Master taxonomy:
  - **Intrinsic** (contradicts source) vs **extrinsic** (unverifiable from source)
  - **Factual** (wrong about world) vs **faithful** (wrong about provided context)
  - For RAG: faithfulness ≫ factuality. You usually only care that the answer is supported by retrieved docs.

**Lab (8h) — `lab-09-faithfulness-checker`.**
1. Build a **faithfulness checker** that:
   - Splits an answer into atomic claims (use Gemma-4-31B with a prompt like "list every factual claim in this text as a JSON array")
   - For each claim, asks: "is this claim entailed by the following context?" using an NLI-style prompt
   - Flags claims with confidence < threshold
   - Returns `(answer, [(claim, supported, evidence_span)])`
2. Implement **SelfCheckGPT-lite**: regenerate the answer 3× at temperature 0.7, compute pairwise BERTScore, flag low-consistency spans.
3. Implement **abstention**: a router LLM that, given (query, retrieved_context), decides "answer / partial answer / refuse with reason."
4. Score all three against your Phase 1 RAG pipeline on a hand-labeled 30-question test set.

**Exit criteria.** Design (on paper) a hallucination-mitigation pipeline for a healthcare or legal RAG product. Defend why each component exists. Articulate the 2026 paradigm shift: **stop chasing zero hallucinations, start managing uncertainty measurably** — show confidence, abstain, cite, and let users decide.

**Infra bridge.** Faithfulness checking = data-lineage validation. Each claim must trace back to a source span — same as your column-level lineage in Terraform. Abstention = your "data quality circuit breaker."

---

## Phase 4 — Frameworks, System Design, Mock Interviews (Weeks 10–12)

**Phase goal.** Convert knowledge into hireable signal. Polish, rehearse, ship.

### Week 10 — Framework Selection: LangChain, LangGraph, LlamaIndex, DSPy
> Detailed runbook: [[Week 10 - Framework Shootout]]

**Theory (5h).**
- The 2026 LangChain reality you must internalize:
  - **LangChain 1.0 (Oct 2025) is now built on LangGraph** for any agent that needs state, loops, or multi-step reasoning.
  - The old `AgentExecutor` class **still exists but is effectively deprecated** for complex use cases.
  - **LCEL (LangChain Expression Language)** chains are still the right call for **linear DAG pipelines**: RAG, retrieval chains, document Q&A. Fast to build, easy to debug.
  - **LangGraph** earns its complexity for **stateful agents**: conditional branching, loops, human-in-the-loop interrupts, persistent sessions, durable execution.
- Read: the LangChain 1.0 announcement, "Is LangChain Still Relevant in 2026?" (bswen), the LangGraph overview docs, LlamaIndex "agentic" docs, DSPy intro, OpenAI Agents SDK docs, Mastra (TS) intro, Pydantic AI intro, Anthropic's "Building effective agents" (read again — it's now your bible).

**The Chain vs Agent answer (memorize a clean version of this):**

> A **Chain** is a deterministic, predefined DAG of steps — input flows through fixed transformations to output, with no decision about which step runs next. LCEL is the declarative way to build them.
>
> An **Agent** is a control-flow loop where an LLM **chooses** the next step at each iteration — typically by emitting a tool call. The graph is implicit and dynamic.
>
> The 2026 reality: in LangChain 1.0, "Agent" is a thin convention on top of LangGraph. The real distinction is **"is the next step decided at design time or at runtime?"** Chains = design time. Agents = runtime.

**Lab (8h) — `lab-10-framework-shootout`.**
1. Re-implement your Week 5 ReAct loop **three more ways**:
   - LangGraph (state-machine style)
   - LlamaIndex agent worker
   - OpenAI Agents SDK pointed at your local mlx-openai-server (works because it's OpenAI-compatible)
2. Compare: lines of code, traceability/observability, ease of adding human-in-the-loop, ease of swapping models, ease of unit-testing.
3. Write a **decision matrix** ("when do I pick which") — bring it to interviews.

**Exit criteria.** Crisp 90-second answer to "LangChain vs LangGraph?" and "Why not just use LangChain agents?" Defend a framework choice for a system the interviewer describes.

### Week 11 — System Design Rehearsal
> Detailed runbook: [[Week 11 - System Design]]

**Theory (3h).** Read 5 real Anthropic / OpenAI / Pinecone / Replit case studies on production agent systems. Note how they handle: cold-start, eval, drift, cost, on-call.

**Lab (10h) — Whiteboard 5 systems out loud, recording yourself.**

For each, spend ~2 hours: 30 min thinking, 60 min talking through architecture aloud (record), 30 min self-critique against the rubric below.

1. **Enterprise document Q&A with citations** — multi-tenant, ACL-aware retrieval, refusal on out-of-scope, audit log
2. **Multi-agent customer-support triage** — classifier agent + specialist agents (billing/tech/account), human escalation, SLA tracking
3. **Coding agent in Claude Code style** — sandboxed exec, git integration, permission model, context compaction
4. **Financial-research agent** — tool-heavy (search + EDGAR + spreadsheet), citation-required, refusal on speculation, deterministic eval
5. **Infra-aware SRE agent (your differentiator)** — reads Kubernetes API + Prometheus + distributed traces + Terraform plan JSON, can answer "why is `checkout-service` p99 up?" by hypothesis → verify reasoning

**Self-critique rubric** (use this every time):
- Did you draw the data flow before talking about prompts?
- Did you state the eval strategy?
- Did you name 3 failure modes and their mitigations?
- Did you discuss cost (tokens × latency × QPS)?
- Did you discuss cold-start (no labeled data on day 1) and drift (data changes over time)?
- Did you state what would make you not build this with an LLM at all?

**Exit criteria.** 5 recordings, each with self-critique notes. The infra-aware SRE agent (#5) is your interview-closer story.

### Week 12 — Mock Interviews + Portfolio Polish
> Detailed runbook: [[Week 12 - Capstone and Mocks]]

**Lab (12h) — Ship.**

1. **Pick your capstone direction** (one of):
   - (a) **RAG-heavy enterprise doc-Q&A** — best for "RAG-leaning" job posts
   - (b) **Coding agent in Claude Code style** — best if you're targeting dev-tools companies
   - (c) **Infra-aware SRE agent** — best for your infra story (recommended)
2. Polish the capstone repo: README that reads like a tech-design doc (problem → constraints → architecture → eval → results → tradeoffs → what's next).
3. Cross-link the 3 lab repos from Phase 1–3 in the capstone README.
4. **30 mock-interview questions** (pull from Appendix A): record yourself, listen back, write a 1-line "what to fix" for each.
5. LinkedIn / GitHub polish — pin the repos, add a short "currently studying" headline, post one technical write-up (the schema-reliability playbook, with credit, makes a great post).
6. Apply to ≥ 10 roles, with a tailored cover note for each that drops one specific result number from your labs.

**Exit criteria.** 1 portfolio repo + 3 lab repos public. 30 mock answers recorded. ≥ 10 applications submitted.

---

## Cross-Cutting Tracks (Run Continuously, All 12 Weeks)

### Daily — 15 min flashcard session
- Add ~5 cards/day from the week's reading. Build to ~300 cards by Week 12.
- Use Anki. The deck structure: `Topic → Q on front → A on back → 1 example on flip side`.

### Weekly — One paper Friday
- Curated reading list in **Appendix D**. Aim for 20–30 minutes per paper, not deep reading. Build literacy, not mastery.

### Weekly — Bad-case journal entry
- Single markdown. Each entry: **(date) — task — what failed — root cause — fix — lesson**.
- This becomes your behavioral-question answer bank. Interviewers love specific war stories.

### Weekly — Infra bridge
- 1 paragraph at the end of each week's lab `RESULTS.md` mapping the week's topic back to cloud-infrastructure concepts.
- These become the "but here's my unfair advantage" line in your phone-screen self-introduction.

---

## Appendix A — 100 Interview Questions (Answer Outlines Only)

> Format: question → 3–5 bullet answer outline. You write the full answer; that's the practice.

### A.1 RAG (25 questions)

1. **Bi-encoder vs cross-encoder, when each?** → independent embedding vs joint scoring; bi for retrieval scale, cross for top-k rerank precision; cost asymmetry; typical pipeline = bi → cross; recall vs precision tradeoff.
2. **How do you choose chunk size?** → corpus characteristics, retrieval granularity, downstream task, context budget, eval-driven sweep — never pick from a blog post.
3. **Why does naive cosine similarity fail on long documents?** → embedding compresses too much; reranker recovers signal; parent-doc retrieval; semantic chunking.
4. **HNSW vs IVF tradeoffs.**
5. **What is HyDE and when does it hurt?**
6. **Multi-query fusion vs single query — when worth it?**
7. **Hybrid retrieval — how do you fuse BM25 + dense?** → RRF (reciprocal rank fusion).
8. **Evaluating retrieval without labels.** → LLM-as-judge, synthetic labels with caveats, click data.
9. **RAGAS metrics — what does each measure?**
10. **Faithfulness vs answer-relevancy — can one be high while the other low?** → yes (faithful but irrelevant; relevant but unfaithful) — give example.
11. **GraphRAG — what problem does it solve that vector RAG doesn't?**
12. **When would you NOT use RAG?**
13. **How do you handle multi-hop queries?**
14. **What's contextual compression and what does it cost?**
15. **How do you handle queries that need recent info vs evergreen?**
16. **Reranker latency budget — how do you stay under 200ms?**
17. **Embedding model upgrades — how do you migrate without downtime?**
18. **How do you evict / refresh stale embeddings?**
19. **Multi-tenant retrieval — how do you isolate?**
20. **Adversarial queries — how do you detect and refuse?**
21. **How do you handle non-text data in RAG (tables, images)?**
22. **Cache strategy for RAG — what to cache, what not to.**
23. **Cost model for a RAG service at 100 QPS.**
24. **CAG vs RAG — when does CAG win?**
25. **How would you debug "the answer is right but not grounded in the cited doc"?**

### A.2 Agent Patterns (20 questions)

26. **Walk me through the ReAct loop.**
27. **5 ways the ReAct loop fails in production.**
28. **When do you choose Plan-and-Solve over ReAct?**
29. **When does Reflexion make outputs worse?**
30. **Multi-agent vs single-agent — what's the inflection point?**
31. **Orchestrator-worker pattern — how do you handle worker failures?**
32. **How do you bound context growth across iterations?**
33. **What is "scratchpad" and when do you compact it?**
34. **How do you make an agent loop deterministic for testing?**
35. **Subagent dispatch — when to spawn vs in-loop?**
36. **AutoGen vs CrewAI vs LangGraph — short answer.**
37. **How do you decide max_iterations?**
38. **Tree-of-Thoughts — when is it worth the cost?**
39. **Human-in-the-loop — where in the loop do you pause?**
40. **What's "context engineering" and how is it different from prompt engineering?**
41. **How do you A/B test a prompt change in an agent?**
42. **How do you handle stateful conversations across sessions?**
43. **What's a memory module — how would you implement one?**
44. **What's the difference between an agent and a workflow?**
45. **Self-Refine vs Reflexion vs Critic-Actor — distinguish.**

### A.3 Hallucination & Eval (15 questions)

46. **Intrinsic vs extrinsic hallucination — define and example.**
47. **Faithfulness vs factuality — which matters more for RAG?**
48. **How does SelfCheckGPT work?**
49. **What is semantic entropy? Why is it useful?**
50. **How do you build a labeled hallucination test set without humans?**
51. **Citation-required generation — how do you enforce?**
52. **How do you teach a model to say "I don't know"?**
53. **LLM-as-judge — failure modes.**
54. **NLI-based faithfulness checking — how does it work?**
55. **How do you detect hallucination at production runtime cheaply?**
56. **What's "calibration" and why does it matter?**
57. **When does retrieval reduce hallucination vs amplify it?**
58. **What's the "lost in the middle" effect?**
59. **How do you eval an agent end-to-end (not just per-step)?**
60. **Drift detection for an LLM-based product — what do you monitor?**

### A.4 Function Calling / Tool Use (15 questions)

61. **OpenAI function calling vs Anthropic tool use — what's actually different?**
62. **MCP — what is it and why does it matter?**
63. **How do you design a tool description?**
64. **Parallel tool calls — when worth it?**
65. **How do you handle a tool that's slow (5 sec)?**
66. **Error-message-as-prompt — show me the pattern.**
67. **How do you prevent infinite tool-calling loops?**
68. **How do you sandbox a code-execution tool?**
69. **What's a tool budget?**
70. **How do you handle a tool that returns 50KB of output?**
71. **How do you test tool-calling reliability?**
72. **How do you rate-limit a per-user tool budget?**
73. **Tool versioning — how do you handle breaking changes?**
74. **Idempotency — which tools need it and how?**
75. **Cross-provider tool ABI — how do you abstract?**

### A.5 Schema Reliability — your signature (10 questions)

76. **How do you guarantee fixed-schema output?** → 5-layer playbook (Appendix B).
77. **Constrained decoding — how does it work?**
78. **Instructor + Pydantic — what does Instructor add?**
79. **Why is constrained decoding sometimes faster than unconstrained?**
80. **In a CoT schema, where do you put the reasoning field and why?** → before the answer; greedy commit.
81. **What's the failure mode of provider-native JSON mode?**
82. **When would you choose post-validation + repair over constrained decoding?**
83. **Schema drift — how do you handle it?**
84. **Tool-use as schema enforcement — explain the pattern.**
85. **How do you measure schema-reliability in CI?**

### A.6 Frameworks & System Design (15 questions)

86. **LangChain Chain vs Agent — explain.**
87. **LangChain vs LangGraph — when each?**
88. **LCEL — what does the `|` actually do?**
89. **LangChain vs LlamaIndex — strengths.**
90. **DSPy — what's the core idea?**
91. **Pydantic AI — when worth it?**
92. **Anthropic's "Building effective agents" — what are the takeaways?**
93. **Design a doc-Q&A system for a law firm.**
94. **Design a customer-support triage system with agents.**
95. **Design a coding agent.**
96. **How do you cost-model an agent at 100 QPS?**
97. **Cold-start: no labeled data — how do you ship eval?**
98. **Drift: how do you detect prompt-rot?**
99. **On-call playbook for an agent — what's in it?**
100. **What would convince you NOT to use an LLM for a problem?**

---

## Appendix B — The Schema Reliability Playbook (Your Signature Question)

> Treat this appendix as a self-contained essay you can publish on LinkedIn or as a blog post. It's the single most-leveraged answer in this curriculum.

### The question

> "How do you guarantee that an agent stably outputs content matching a fixed schema?"

The answer is **never one technique**. It is a **layered defense** where each layer catches what the previous one missed. Strong candidates explain all five layers and their cost/reliability tradeoffs.

### The 5-Layer Defense

```
┌─────────────────────────────────────────────────────────┐
│ L5  Defensive parsing + field-level fallbacks           │
│     (last-resort: salvage what you can, log the rest)   │
├─────────────────────────────────────────────────────────┤
│ L4  Post-validation + repair prompt                     │
│     (parse → if invalid, send error back, retry once)   │
├─────────────────────────────────────────────────────────┤
│ L3  Validation wrapper (Instructor + Pydantic)          │
│     (auto-retry with schema-aware error injection)      │
├─────────────────────────────────────────────────────────┤
│ L2  Constrained decoding (Outlines / xgrammar / native) │
│     (token-level guarantee; logits filtered to schema)  │
├─────────────────────────────────────────────────────────┤
│ L1  Schema design + prompt design                       │
│     (clear field names, examples, reasoning-before-     │
│      answer ordering, minimal nesting)                  │
└─────────────────────────────────────────────────────────┘
```

### Layer 1 — Schema and Prompt Design

The cheapest layer. Most schema failures are self-inflicted.

- **Field naming.** Use unambiguous, descriptive names (`customer_email_address`, not `email`).
- **Reasoning-before-answer.** This is the one detail that separates seniors from juniors. In a chain-of-thought schema, **always put the reasoning field BEFORE the answer field**. Models commit greedily; if the answer field comes first, the model commits to an answer before finishing its reasoning, and you get syntactically-valid-but-wrong output that no validator can catch.
  ```python
  # WRONG
  class Output(BaseModel):
      answer: str
      reasoning: str

  # RIGHT
  class Output(BaseModel):
      reasoning: str
      answer: str
  ```
- **Minimize nesting.** Each level of nesting compounds failure rate. Flatten when you can.
- **Use enums for closed sets.** `category: Literal["billing", "tech", "account"]` is more reliable than `category: str` + a "must be one of" instruction.
- **Provide a worked example in the prompt.** Even with constrained decoding. The example anchors semantics, the constraint anchors syntax.

### Layer 2 — Constrained Decoding

The token-level guarantee. The model **cannot** emit a token that violates the schema, because the logits for invalid tokens are masked to `-inf` before sampling.

- **Outlines** — Python library, integrates with mlx-lm, transformers, vLLM. Compiles a JSON schema into an FSM (finite-state machine). Token-time overhead is near zero on hot paths.
- **XGrammar** (mlc-ai) — 100× faster than naive grammar parsing thanks to a persistent parsing stack and context-independent pre-checks. Best when you need context-free grammars (e.g., complex DSLs).
- **llguidance** (guidance-ai) — fast structured outputs with broad backend support.
- **Provider-native JSON mode** — OpenAI's `response_format={"type": "json_schema", ...}` with `strict: true` is constrained decoding under the hood. Anthropic's tool-use is effectively schema enforcement (the tool schema = the output schema). Gemini has `response_schema`.

**When constrained decoding hurts:**
- Very complex schemas can blow up FSM compile time (Outlines compilation timeouts are a known failure mode in 2026 benchmarks).
- Constrained decoding can lower output quality by forcing a token the model didn't "want" — particularly visible on small models.

### Layer 3 — Instructor + Pydantic

The validation wrapper. Instructor is the most-downloaded LLM utility library for a reason: it wraps every major provider with a Pydantic-first interface, so you get cross-provider portability + auto-retry-on-validation-failure.

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field

client = instructor.from_openai(
    OpenAI(base_url="http://localhost:8003/v1", api_key="local")
)

class Ticket(BaseModel):
    reasoning: str = Field(description="Explain your classification step by step")
    category: Literal["billing", "tech", "account"]
    urgency: Literal["low", "medium", "high"]
    suggested_action: str

ticket = client.chat.completions.create(
    model="qwen2.5-14b-instruct",
    response_model=Ticket,
    max_retries=3,  # auto-retry with the validation error injected as feedback
    messages=[{"role": "user", "content": user_text}],
)
```

What Instructor adds beyond raw constrained decoding:
- **Auto-retry on `ValidationError`** with the error message fed back as context, giving the model a chance to self-correct.
- **Cross-provider abstraction** — same code works against OpenAI, Anthropic, local mlx-openai-server, Cohere, Gemini.
- **Streaming Pydantic objects** — yield partial fields as they arrive (great for UX).

### Layer 4 — Post-Validation + Repair Prompt

For when constrained decoding isn't available (older OSS models, custom protocols) or when validation involves business rules constrained decoding can't express ("`end_date` must be after `start_date`," "total must equal sum of line items").

```python
def with_repair(model_call, validate, max_repairs=1):
    output = model_call()
    for _ in range(max_repairs):
        ok, error = validate(output)
        if ok:
            return output
        output = model_call(extra_context=f"Your previous output failed validation: {error}. Fix it and emit only the corrected JSON.")
    raise ValueError("Max repairs exhausted")
```

This is L3 but explicit and customizable for **semantic** validation, not just schema validation.

### Layer 5 — Defensive Parsing + Field-Level Fallbacks

Last resort. When everything fails, salvage what you can.

```python
def parse_defensively(raw: str) -> Ticket:
    try:
        return Ticket.model_validate_json(raw)
    except ValidationError:
        # Try field-by-field extraction
        cat = re.search(r'"category"\s*:\s*"(billing|tech|account)"', raw)
        urg = re.search(r'"urgency"\s*:\s*"(low|medium|high)"', raw)
        return Ticket(
            reasoning="(degraded: parsed defensively)",
            category=cat.group(1) if cat else "tech",  # safe default
            urgency=urg.group(1) if urg else "medium",
            suggested_action="(manual review required)",
        )
```

Pair with logging + alerting. Field-level fallback is a degraded mode, not a target. If you're hitting L5 more than 0.1% of the time, fix L1–L3.

### How to deliver the answer in an interview

1. **Restate** the question: "There are five layers of defense; let me walk through each, then say how I'd combine them for your use case."
2. **Walk the diagram.** ~30 sec per layer.
3. **Give the reasoning-before-answer detail** as your "I've actually shipped this" tell.
4. **Drop one number from your benchmark** ("In my benchmark on Qwen 2.5 14B, naive prompting gave 73% valid; constrained decoding + Instructor pushed it to 99.4%, with p95 latency increasing only 8%").
5. **Close with the tradeoff.** "I default to constrained decoding + Instructor + minimal repair. I avoid heavy repair loops because they hide the underlying schema problem and inflate cost."

That's a 5-minute answer that demonstrates depth, hands-on experience, and engineering taste. **Practice it until it's muscle memory.**

---

## Appendix C — Claude Code Source Study Map

Use this as a reading guide for Week 6.

### Read order

1. **bits-bytes-nn — Claude Code Architecture Analysis** (March 2026 post). Best diagrams. Start here.
2. **VILA-Lab — Dive-into-Claude-Code** (GitHub). Systematic analysis with subsystem breakdowns.
3. **DEV.to — "Architecture Explained: Agent Loop, Tool System, Permission Model"**. Focused on the three biggest pieces.
4. **engineerscodex Substack — "Diving into Claude Code's Source Code Leak"**. Engineering perspective, less academic.
5. **claudefa.st — "Source Leak: Everything Found"**. Catalog of what's in the leaked code.

### Subsystem study sheet (fill in for each)

For each of the 8 subsystems below, write 4 lines:
- (a) **What problem does this solve?**
- (b) **What's the data structure / control flow at the core?**
- (c) **What's the failure mode it's preventing?**
- (d) **What would I steal for my own agent?**

The 8 subsystems:
1. **The agent loop** (~1.6% of LOC; the rest is infrastructure)
2. **Permission system** (7 modes + ML-based classifier for tool-call risk)
3. **5-layer compaction pipeline** (how context is squeezed when long)
4. **Tool routing** (built-in vs MCP vs subagents vs skills vs hooks — 4 extension mechanisms)
5. **Subagent dispatch** (the `Task` tool spawns isolated child agents)
6. **Append-only session storage** (event-sourced session log)
7. **Hook system** (PreToolUse, PostToolUse, Stop — deterministic guardrails)
8. **PROACTIVE / KAIROS feature flags** (the always-on background agent mode behind feature flags)

### Headline insight to memorize

> Claude Code is ~512K LOC of TypeScript. **Only 1.6% is AI decision logic.** The other 98.4% is deterministic infrastructure: permission gates, context management, tool routing, recovery logic. **The hard problem in production agents is not the loop. It is everything around the loop.**

That sentence wins interviews.

---

## Appendix D — Curated Reading List

### Papers (Friday reading)
- ReAct (Yao et al. 2022)
- Toolformer (Schick et al. 2023)
- Reflexion (Shinn et al. 2023)
- Plan-and-Solve (Wang et al. 2023)
- Self-Refine (Madaan et al. 2023)
- HyDE (Gao et al. 2022)
- Self-RAG (Asai et al. 2023)
- Constitutional AI (Anthropic, 2022)
- SelfCheckGPT (Manakul et al. 2023)
- Semantic Entropy (Farquhar et al., Nature 2024)
- BGE-M3
- Nomic Embed v2
- XGrammar
- SLOT (structuring LLM output)
- "Lost in the Middle" (Liu et al. 2023)
- Multi-Agent Collaboration Mechanisms: A Survey (2025)

### Engineering essays
- **Anthropic — Building effective agents** (Sept 2024 + 2026 updates) — your bible
- **Anthropic — Contextual Retrieval** blog post
- **Lilian Weng — LLM Powered Autonomous Agents**
- **Simon Willison — anything tagged "agent"**
- **Hamel Husain — Your AI product needs evals**
- **Eugene Yan — Patterns for Building LLM-Based Systems & Products**

### Framework docs to skim
- LangChain 1.0 announcement + LangGraph overview
- LlamaIndex agentic docs
- DSPy intro
- OpenAI Agents SDK
- Pydantic AI
- Mastra (TS-first)
- Outlines, Instructor, XGrammar, llguidance

### Claude Code architecture analyses (Week 6)
- bits-bytes-nn (March 2026)
- VILA-Lab GitHub
- DEV.to architecture explainer
- engineerscodex Substack
- claudefa.st source-leak catalog

### 2026 interview-question banks
- DataCamp: Top 30 RAG Interview Questions (2026)
- KalyanKS-NLP/RAG-Interview-Questions-and-Answers-Hub (GitHub)
- Analytics Vidhya: 30 Agentic AI Interview Questions
- The Interview Guys: Top 10 Context Engineer Interview Questions
- amitshekhariitbhu/ai-engineering-interview-questions (GitHub)

---

## Appendix E — Portfolio Project Briefs

Pick **one** capstone in Week 12. The other two stay as labs.

### Capstone Option A — Enterprise Doc-Q&A (RAG-leaning)
- **Pitch:** Multi-tenant RAG for a fictional law firm. Per-tenant ACL on retrieval. Citation-required answers. Refusal on out-of-scope. Audit log.
- **Stack:** Local Gemma-4-31B for synthesis, BGE-M3 embeddings, BGE-reranker, Qdrant with per-tenant collections, Phoenix for traces, RAGAS for eval.
- **Differentiator:** ACL-aware retrieval (hard to fake), audit log (what enterprise actually pays for), eval dashboard.
- **Show in interviews:** the eval dashboard + the ACL test case + the "what happens when retrieval is empty" refusal flow.

### Capstone Option B — Coding Agent (Claude Code style)
- **Pitch:** A minimal coding agent that can read/write files, run shell, run tests, with a permission model and append-only session log.
- **Stack:** Local Qwen 2.5 32B (better tool use than Gemma), custom tool harness (your Week 7 work), SQLite session storage, simple CLI UI.
- **Differentiator:** the permission model (don't ship dangerous shell commands without confirmation), session replay (event-sourced), the bad-case test suite from Week 4.
- **Show in interviews:** the permission flow, a session replay, your "5 failure modes I patched" list.

### Capstone Option C — Infra-Aware SRE Agent (your infra story) ★ Recommended
- **Pitch:** An agent that reads Kubernetes API, Prometheus metrics, distributed traces, Terraform plan output, and an embedded runbook corpus to answer questions like "why is `checkout-service` p99 latency up?" or "what will `terraform apply` change in prod?" or "which services breached SLO this week?" — and proposes actionable, safe fixes.
- **Stack:** Local Qwen3.6-35B as orchestrator, tools for `kubectl_get_pods`, `promql_query`, `walk_distributed_trace`, `parse_terraform_plan`, `fetch_pagerduty_incident`, and `semantic_runbook_search`; Qdrant for embedded runbook corpus (BGE-M3); LangGraph for the agent loop; Phoenix for traces.
- **Differentiator:** **nobody else competing for this job has built this.** You have three years of lived experience with Kubernetes, Terraform, and observability stacks — you know which artifacts exist, what they contain, and where the failure modes live. Every tool call returns real, deterministic data; the LLM only synthesizes the final narrative. All write operations (rollback, scale) require explicit human confirmation.
- **Show in interviews:** a 60-second demo (record a screencast) where you ask "why did `payments-api` OOM at 03:17 UTC?" and the agent pulls pod events, memory metrics, and recent deploy history, then proposes either a rollback or a replica-scale action. Narrate the hypothesis → verify → converge reasoning pattern live.

---

## Final Notes

**Where to put your effort if you only have 6 weeks instead of 12.**
Compress like this: skip Week 5 (do only ReAct in Phase 2), skip Week 11 (do only one system design instead of five), skip Anki. **Do not skip:** Week 4 (ReAct from scratch), Week 6 (Claude Code source), Week 7 (tool harness), Week 8 (schema reliability — your signature). Those four weeks are the differentiating signal.

**Where the cloud spend goes.**
- ~$2 OpenAI in Week 8 (schema-reliability comparison, GPT-4o-mini)
- ~$0.50 Anthropic in Week 7 (tool-calling reliability comparison, Claude Haiku)
- ~$5 buffer for Week 11 system-design rehearsal (use Claude/GPT to red-team your designs)
- **Total: ~$8 for the entire 3-month program.**

**When you hit a wall.**
- Stuck on a concept → re-read Anthropic's "Building effective agents." It's the highest-density agent material on the public internet.
- Stuck on stability → re-read Claude Code architecture posts. Every stability problem you'll hit, they've already solved.
- Stuck on motivation → open your bad-case journal and read your last 3 entries. You're learning faster than you think.

**Ship.** Public repos beat private mastery. Posting one thoughtful technical write-up on LinkedIn or a personal blog will do more for your job hunt than 20 unposted projects.

---

## Appendix F — Companion Texts Map

Three reference series complement this curriculum. Each takes a different angle on agent systems; together they cover breadth, production-depth, and comparative architecture. You don't need all three — pick one path (or none) based on how much reading time you have. Primary chapter pointers are also embedded in each week's "Theory Primer → Optional deep dives / Companion Texts" subsection.

### F.1 Gulli — *Agentic Design Patterns* (Antonio Gulli, Springer 2026)

**Angle:** Breadth. The broadest pattern catalog available. 424-page book + one runnable Jupyter notebook per chapter at [github.com/evoiz/Agentic-Design-Patterns](https://github.com/evoiz/Agentic-Design-Patterns). Royalties donated to Save the Children.

**When to use:** When you want named-pattern vocabulary for interviews and runnable baselines you can copy before you build your own. Framework-agnostic (LangChain, AutoGen, CrewAI examples throughout).

| Gulli Ch | Pattern | Week(s) |
|---|---|---|
| 1 | Prompt Chaining | 4, 5 |
| 2 | Routing | 5, 10 |
| 3 | Parallelization | 5, 7 |
| 4 | Reflection | **5 ★**, 9 |
| 5 | Tool Use | **7 ★** |
| 6 | Planning | **5 ★** |
| 7 | Multi-Agent | **5 ★** |
| 8 | Memory Management | **6 ★** |
| 9 | Learning and Adaptation | 11 |
| 10 | Model Context Protocol (MCP) | **7 ★** |
| 11 | Goal Setting and Monitoring | 5, 11 |
| 12 | Exception Handling and Recovery | 4, 7 |
| 13 | Human-in-the-Loop | 10, 11 |
| 14 | Knowledge Retrieval (RAG) | 1, 2, 3 |
| 15 | Inter-Agent Communication (A2A) | 5 |
| 16 | Resource-Aware Optimization | 7, 11 |
| 17 | Reasoning Techniques | 4, 9 |
| 18 | Guardrails / Safety Patterns | 7, 11 |
| 19 | Evaluation and Monitoring | 3, 9 |
| 20 | Prioritization | 5, 11 |
| 21 | Exploration and Discovery | 5 |
| Appx A | Advanced Prompting Techniques | 4, 8 |
| Appx B | From GUI to Real World | 12B |
| Appx C | Agentic Frameworks Overview | 10 |
| Appx D | AgentSpace | 10 |
| Appx E | AI Agents on the CLI | 6, 12 |
| Appx F | Reasoning Engines | 4, 5 |
| Appx G | Coding Agents | 12B |

★ = strong map; read chapter + run notebook before starting the week.

### F.2 Gerred — *Building an Agentic System* (Gerred Dillon, 2024–2026)

**Angle:** Production depth on specific real systems. Three-book series reverse-engineering Claude Code, Sourcegraph Amp, and open-source alternatives. English, free online at [gerred.github.io/building-an-agentic-system](https://gerred.github.io/building-an-agentic-system/).

**When to use:** When you want to see exactly how one real system was built — architecture, code patterns, failure modes, and the reasoning behind them. Complements the curriculum's Week 6 Claude Code source dive directly.

| Gerred Book | Focus | Strong Week Match |
|---|---|---|
| **Book 1** — *Building an Agentic System* (introduction, 29 chapters across 3 books framed here) | Core architecture: streaming & reactivity, permission systems, tool extensibility, parallel execution, command loops | **4, 6, 7** |
| **Book 2** — *Amping Up an Agentic System* (Sourcegraph Amp case study) | Server-first architecture, real-time collaboration, thread management at scale, observable-based state, multi-agent orchestration, enterprise patterns | **5, 9, 11** |
| **Book 3** — *Contextualizing an Agentic System* ("Arming") | Tool taxonomy (file ops, system interaction, memory, communication) + Commands (config, workflow, dev support, maintenance) | **7, 6** (hook system) |

### F.3 agentway.dev — *Harness Engineering* (2026)

**Angle:** Comparative architecture, in Chinese with English technical terms. Two-book series: Book 1 analyzes Claude Code's harness design; Book 2 compares Claude Code vs OpenAI Codex control-plane philosophies. Central thesis: *"先有规矩，再谈聪明"* (System First, Model Second — infrastructure matters more than model cleverness).

**When to use:** When you want to understand the *why* behind Claude Code's design decisions and how they contrast with Codex's. Central to Week 6 (source dive), Week 7 (tool harness), and Week 10 (framework shootout).

| Harness Book | Chapter | Title | Week(s) |
|---|---|---|---|
| Bk 1 | 1 | 为什么需要 Harness Engineering (Why Harness Engineering) | 6 |
| Bk 1 | 2 | Prompt 不是人格 (Prompt is not a personality — layered prompts) | 4, 6 |
| Bk 1 | 3 | Query Loop (the heartbeat) | **4 ★**, 6 |
| Bk 1 | 4 | 工具、权限与中断 (Tools, permissions, interrupts) | **7 ★** |
| Bk 1 | 5 | 上下文治理 (Context governance — CLAUDE.md, MEMORY.md, auto-compact) | **6 ★** |
| Bk 1 | 6 | 错误与恢复 (Errors and recovery) | 4, 7 |
| Bk 1 | 7 | 多代理与验证 (Multi-agent and verification) | **5 ★**, 9 |
| Bk 1 | 8 | 团队落地 (Team adoption) | 11, 12 |
| Bk 2 | 1 | Why compare Claude Code and Codex together | 10 |
| Bk 2 | 2 | 两种控制面 (Two control planes — runtime-first vs policy-first) | **10 ★** |
| Bk 2 | 3 | 心跳放在哪 (Heartbeat placement — main-loop vs split-state) | 4, 10 |
| Bk 2 | 4 | 工具、沙箱与策略语言 (Tools, sandboxes, policy languages) | 7 |
| Bk 2 | 5 | 技能、Hook 与本地规则 (Skills, Hooks, local rules) | 6 |
| Bk 2 | 6 | 委派、验证与持久状态 (Delegation, verification, persistent state) | 5, 9 |
| Bk 2 | 7 | 殊途同归 (Convergence vs divergence) | 10 |
| Bk 2 | 8 | 如果你要自己做 (If you want to build your own) | 11, 12 |

PDFs live at `~/Downloads/book1-claude-code.pdf` (88 pp) and `~/Downloads/book2-comparing.pdf` (54 pp). Extract Chinese text to paraphrase via `pdftotext -layout -f <start> -l <end> <file> -`.

### F.4 Reading Strategy — Pick a Path

| Path | What you read | Extra time/week | Who it's for |
|---|---|---|---|
| **Minimum** | Just the Theory Primers | 0 h | Time-starved; interview-prep only |
| **Breadth (recommended)** | Primers + Gulli chapters flagged ★ each week, run the notebook | +1–2 h | Most readers; best ROI |
| **Depth** | Primers + Gerred Book 1 (Weeks 4/6/7) + Harness Engineering Book 1 (Weeks 4/6/7) + Book 2 (Week 10) | +3–5 h | Full-time study; targeting senior roles |
| **Complete** | All three series | +6–8 h | Career-pivot sabbatical; transitioning from adjacent field |

**Stack ranking for interview-signal-per-hour:** Theory Primer (10×) > Gulli's flagged chapters (4×) > agent-skills (3×, once Week 12) > Harness Engineering (3×) > Gerred (2×). All are positive-ROI; priority matters only if time is tight.

### F.5 Beginner Gateways (before the curriculum)

**Angle:** Orientation. Short, accessible reads for someone who has never built an agent before. Intended as *pre-curriculum* warm-up, not as curriculum content. Expect to outgrow them by Week 4.

**When to use:** Before Week 0 if you've never touched an agent SDK. After Week 12 if you want to explain the curriculum to a colleague without overwhelming them.

| Resource | Angle | Time | Use for |
|---|---|---|---|
| **[hoeem — "I want to build an AI agent today"](https://x.com/hooeem/status/2037250422403113188)** | 8-section practitioner walkthrough: core loop → 5 Anthropic patterns → Anthropic + OpenAI SDK starter examples → tools/memory/testing basics → multi-agent timing | ~30 min | Pre-Week-0 orientation. Introduces three useful mnemonics the curriculum now captures: the 5-element formula (*Role + Goal + Tools + Rules + Output format*), the 5 beginner-agent archetypes (Research / Content / Workflow / Personal-Knowledge / Operator), and the 4-question scoping checklist. |
| **[Anthropic — *Building Effective Agents*](https://www.anthropic.com/research/building-effective-agents)** | Canonical 2024 post defining the 5 workflow patterns the curriculum teaches; referenced ~20 times across primers | ~25 min | Read before Week 4 if hoeem's article felt too light. Still the highest-density short read on the public internet. |
| **[DeepLearning.AI — Short agent courses](https://www.deeplearning.ai/courses/)** | Andrew Ng's short video courses on ReAct, multi-agent, and function calling; ~1 hr each | ~3 h total | If video format helps you retain material better than prose. Skip if reading works. |

**Reading strategy tie-in:** The F.4 paths assume you can already hold an agent conversation in your head. If you can't — start here, spend one evening on hoeem + Anthropic, then enter Week 0 fresh.

### F.6 Practitioner Toolkits (install-and-use, not read)

**Angle:** Discipline as executable workflow. Distinct from F.1–F.3 (reference texts) and F.5 (gateway reads) — this is an **installable plugin** you run inside your `claude` CLI during lab and capstone work. Reading these skills without installing them misses the point; the value is in having the slash commands enforce discipline in real time.

**When to use:** Install in Week 0 Phase 8.5. Practice with slash commands during Weeks 7, 9 labs. Rely on them heavily in Week 12 Capstone.

#### agent-skills (Addy Osmani, 21.8k⭐ MIT-licensed)

[github.com/addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) — 20 production-grade SKILL.md files + 3 agent personas + 4 reference checklists + 7 slash commands. Compatible with Claude Code, Cursor, Gemini CLI, Windsurf, OpenCode, Copilot, Kiro IDE.

| Phase | Slash cmd | Skills (with week links) |
|---|---|---|
| **Define** | `/spec` | idea-refine · spec-driven-development → Week 11, Week 12 |
| **Plan** | `/plan` | planning-and-task-breakdown → Week 5, Week 12 |
| **Build** | `/build` | incremental-implementation · test-driven-development · context-engineering · source-driven-development · frontend-ui-engineering · api-and-interface-design → Week 4, Week 7, Week 12 |
| **Verify** | `/test` | browser-testing-with-devtools · debugging-and-error-recovery (5-step triage) → Week 4, Week 7 |
| **Review** | `/review` | code-review-and-quality · code-simplification · security-and-hardening · performance-optimization → Week 11, Week 12 |
| **Ship** | `/ship` | git-workflow-and-versioning · ci-cd-and-automation · deprecation-and-migration · documentation-and-adrs · shipping-and-launch → Week 12 |

**Intellectual foundation:** the skills synthesize patterns from Google's *Software Engineering at Google* — Hyrum's Law (interface design), the Beyonce Rule (testing), change-sizing norms (~100-line reviews), Chesterton's Fence (simplification), trunk-based development, Shift Left CI/CD.

**Why it's the 3rd-highest stack-ranked resource (after Gulli and your own primers):** unlike reading, install-and-use produces *measurable signal* — every `/ship` run leaves traces that say "these gates passed." That trail is concrete interview evidence, not just claimed best practice.

**Reading strategy 5th path — "Executable discipline":** curriculum primers + agent-skills installed from Week 0 + slash-command usage during every lab that involves shipping code. Zero extra *reading* time beyond the curriculum; added *execution* time is saved by catching issues the manual checklist would miss. Net effort-adjusted ROI: positive.

---

## Appendix G — Continuous Learning System

> The 12-week program ends, but the field doesn't. This appendix turns the curriculum from a finite course into a sustainable learning practice. Read once after Week 12; revisit Section G.1 weekly forever.

This appendix exists because the agent-engineering field publishes faster than any curriculum can be written. Stanford's single-vs-multi-agent paper (Concept 6 in Week 5) didn't exist when this curriculum was first drafted. PASTE (Concept 6 in Week 7) didn't exist. Pi (the counter-thesis in Weeks 6 + 7) didn't exist. Microsoft Agent Framework 1.0 didn't exist. And by the time you reach Week 12, several more thesis-level updates will have shipped that aren't in this document yet.

The wrong response is to chase every announcement — that's a full-time job that produces no shipping. The right response is a **bounded weekly ritual** with explicit filters, plus a **multi-quarter cadence** for deeper specialization. This appendix gives you both.

---

### G.1 The Saturday Trend-Tracking Ritual (~30 minutes/week)

A weekly half-hour habit, ideally Saturday morning before the news cycle resets. Three steps:

**1. Skim ~8 sources** (G.2 lists them with refresh cadence). Don't read deeply — scan headlines, abstract first sentences, repo READMEs. Build a queue of items, not opinions.

**2. Apply the triangulation filter** (G.3). For each item: named author? thesis (not just product feature)? does it contradict something in the curriculum? Items that score 3/3 earn deep reading; 2/3 earn skim+archive; 0–1/3 dismiss.

**3. Capture verdicts** in a single append-only log file (`~/Documents/Obsidian Vault/trend-tracker.md`). One line per item: `2026-MM-DD | source | item | type | verdict`.

**Template for the log file (start of each week's section):**

```markdown
## 2026-WW-DD (week N post-curriculum)

| Source | Item | Type | Triangulation | Verdict |
|---|---|---|---|---|
| Anthropic blog | [title](url) | post | 3/3 (named, thesis, contradicts W6) | revisit Week 6 |
| arXiv cs.CL | [paper title](url) | paper | 2/3 (named, thesis, no contradiction) | skim + archive in `papers/` |
| LangGraph changelog | v1.4.0 release | tool | 1/3 (named only) | note version, dismiss content |
| Vendor X press release | platform announcement | product | 0/3 | dismiss |

**This week's revisit:** Week 6 update planned for next Saturday after re-reading Anthropic post.
**Time spent:** 28 min.
```

**The discipline points:**
- **Time-box hard.** 30 min, alarm on phone. Going over means you're reading instead of triaging — a different mode, not part of this ritual.
- **Append-only.** Don't edit past entries. Old verdicts that turned out wrong are signal — they teach you what to weight more heavily next time.
- **Output-driven.** A week with zero "revisit Week N" verdicts is fine. Most weeks should produce 0–2. Five-plus is suspicious; you're being too lenient with the filter.

---

### G.2 Curated Source List (with refresh cadence)

Eight sources, grouped by how often you check them. Not exhaustive — these are the ones with the highest signal-to-noise on agent engineering as of 2026.

#### Weekly skim (the Saturday ritual — 8 sources)

| Source | URL pattern | What to look for |
|---|---|---|
| **Anthropic — research + engineering** | anthropic.com/research, anthropic.com/news | New papers (about 2/month), Building Effective Agents updates, Claude release notes affecting tool use |
| **OpenAI research blog** | openai.com/research | Agent SDK updates, new tool primitives, evaluation work |
| **Hugging Face Daily Papers** | huggingface.co/papers (filter: cs.AI agents tag) | Top-voted papers; usually 1–2/week worth opening |
| **Latent Space (newsletter + podcast)** | latent.space | Best-curated industry signal in agent space; ~2 issues/week |
| **AINews (Smol AI)** | news.smol.ai | Daily digest condensed to weekly skim — read Saturday's "this week" recap |
| **GitHub trending — agents** | github.com/trending?topic=agent | Catches new framework launches, Pi-style minimalist tools |
| **Armin Ronacher's blog** | lucumr.pocoo.org | Low frequency (~1 post/month), high signal — Pi was found here |
| **Anthropic Discord (#research-papers, #building-agents)** | discord.com/invite/anthropic | Real-time discussion; skim Saturday morning's previous-week activity |

#### Monthly review (~20 min/month)

| Source | What changed |
|---|---|
| LangGraph changelog (`langchain-ai/langgraph`) | Stateful API changes, persistence backends, human-in-the-loop primitives |
| LlamaIndex release notes | Agent worker pattern updates, query engine refactors |
| OpenAI Agents SDK + Codex CLI release notes | New handoff primitives, tracing changes |
| Microsoft Agent Framework releases | Convergence direction with LangGraph, new connectors |
| MCP spec releases (`modelcontextprotocol/specification`) | Protocol-level changes affecting tool design |
| Anthropic prompting guide (docs.anthropic.com) | Cache management, tool-use best practices |

#### Quarterly survey (~2 hours/quarter)

| Source | Why quarterly |
|---|---|
| Major framework shootout posts | Aggregated comparisons that test what you'd otherwise have to test yourself |
| Stanford NLP / Princeton / MIT agent papers | Academic work consolidates into theses every 3 months |
| Vendor enterprise announcements (Google, Microsoft, Salesforce, AWS) | Quarterly product cycles align with vendor calendars |
| Eval benchmarks (SWE-Bench, AgentBench, GAIA, OSWorld) | Leaderboard movement signals what techniques are landing in production |
| Anthropic + OpenAI + Google model releases | When tool-use APIs change, retest your harness |

#### Ad-hoc / event-driven

When a major model releases (Claude X.Y, GPT-N, Gemini-N), spend ~2 hours within a week:
1. Read the model card's tool-use section.
2. Run your Week 7 tool harness against the new model — measure reliability delta vs your local fleet.
3. If reliability changes by more than ±5pp, the change earns a curriculum-update verdict.

---

### G.3 The Triangulation Filter (3-Question Test)

Before spending more than 5 minutes on any new item, run these 3 questions:

**Q1: Is there a named author?**
- ✓ Paper authors, blog post author, repo maintainer with commit history
- ✗ Anonymous Reddit thread, vendor press release, "the team at $COMPANY"

Named authors create *accountability* — you can compare their claims to their prior work, look up other things they wrote, follow their citation tree. Anonymous content can't be triangulated.

**Q2: Is there a thesis?**
- ✓ A claim about how to do agents better — "X helps because Y" / "Z is wrong, do W instead" / "the trade-off in V is misunderstood"
- ✗ A product feature list, a benchmark number without explanation, a tutorial

Theses generalize across systems; product features don't. PASTE has a thesis ("speculation cuts agent latency the way it cuts CPU latency"). Salesforce Agent Fabric is a product launch — useful to know about, but the announcement isn't where the thesis lives.

**Q3: Does it contradict something the curriculum already teaches?**
- ✓ Stanford 2025 contradicting "default to multi-agent" → updates Week 5
- ✓ Pi contradicting "default to MCP plugin architecture" → updates Weeks 6 + 7
- ✗ Yet another LangGraph tutorial that re-teaches what Week 10 covers

Contradictions are *thesis-correcting* — they have higher learning rate per minute spent. Material that confirms what you already know is pleasant but low-value.

**Scoring:**
- **3/3** → deep reading; if compelling, write a curriculum update PR to yourself this week
- **2/3** → skim + 1-paragraph summary in archive; revisit if a 3/3 item later cites it
- **1/3** → record name only (you should be able to *recognize* the item if it comes up in conversation, but you don't owe it your time)
- **0/3** → dismiss

This filter is the single most important habit in this appendix. It's how you stay current without burning out.

---

### G.4 "Which Week to Revisit" — Decision Tree

When the triangulation filter says 3/3 and you have a curriculum-update verdict, this lookup tells you which week's primer to update.

```
New item earns 3/3 — what does it concern?
│
├── Embedding model / vector index / hybrid retrieval ─────────→ Week 1
├── Reranker / chunking / context compression / CAG ──────────→ Week 2
├── RAG eval methodology / RAGAS metrics / HyDE / fusion ─────→ Week 3
├── Agentic RAG / iterative retrieval / GraphRAG ─────────────→ Week 2.5 or Week 3
├── Cross-session memory / persistent agent memory ──────────→ Week 3.5
├── ReAct loop / scratchpad design / max-iter / errors ──────→ Week 4
├── Multi-agent / Plan-and-Solve / Reflexion / patterns ──────→ Week 5
├── Claude Code / Aider / Codex CLI / source-leak analysis ──→ Week 6
├── Tool use / MCP / function calling / permission systems ──→ Week 7
├── Structured output / constrained decoding / JSON schema ──→ Week 8
├── Hallucination / faithfulness / verification / abstention →→ Week 9
├── LangGraph / LlamaIndex / framework comparison / Chain ───→ Week 10
├── System design pattern / SRE agent / enterprise platform ─→ Week 11
├── Capstone polish / portfolio / job-hunt / interview ──────→ Week 12
└── Doesn't fit any week ─────────────────────────────────────→ Add to G.6 wish list (potential Week 13+)
```

When updating a primer, do it as a small Edit (single concept addition or small revision). Don't rewrite the primer wholesale — that loses the prior context that made the rest of the primer cohere.

---

### G.5 The 12-Month Cadence Map

The curriculum ends at Week 12. Here's what the *next 9 months* should look like, broken into quarters.

#### Q1 (the curriculum quarter — months 1–3)

You're doing this now. Goal: ship the capstone, apply to ≥10 roles, complete the 12-week program. **Don't run the Saturday ritual during Q1** — your time is fully booked. Start G.1 the week *after* Week 12.

#### Q2 (months 4–6) — capstone iteration + technique adoption

Two parallel tracks:

**Track A: Capstone V2 from real feedback.** When you ship the capstone in Week 12 and start applying, you'll get specific feedback: hiring managers asking "why didn't you do X?", phone-screen questions revealing gaps. Capture those. In Q2, ship V2 of the capstone that addresses the top 3 feedback items.

**Track B: Try 2–3 techniques from the Q1 trend-tracker.** By end of Q1, your `trend-tracker.md` will have 5–10 items with "revisit Week N" verdicts that you didn't have time to actually try. Q2 is when you try them — one per month, lab-sized scope. Each becomes a small public artifact (gist, blog post, repo branch).

**Track C (optional): One OSS contribution.** Pick one of LangGraph / LlamaIndex / OpenAI Agents SDK / agent-skills / your favorite framework. Open one issue → one PR. Doesn't have to land — the visible attempt + maintainer interaction is the artifact.

#### Q3 (months 7–9) — pick a specialization

By month 7, you'll have noticed which type of agent work energized you. Pick one:

| Specialization lane | Indicator you should pick this | Year-1 deliverables |
|---|---|---|
| **Eval & observability** | You enjoyed Weeks 3, 9; you naturally measure things; phoenix traces fascinated you | Open-source eval framework contribution; one published benchmark; a "how we evaluate agents" blog post |
| **Multi-agent orchestration** | You enjoyed Week 5; the Stanford paper bothered you in a productive way; orchestrator-worker patterns clicked | Multi-agent framework contributions; one "when does multi-agent actually help" study |
| **Agent infrastructure / SRE** | Capstone C was your favorite; you debug naturally; you talk about cost & latency | Infra-aware agent open-source project; conference talk on agent observability |
| **On-device / local inference** | You loved that the curriculum runs locally; oMLX/vMLX intrigued you; you optimize for cost | MLX library contributions; on-device agent reference implementation |
| **Agent-platform engineering** | You'd rather build *the framework* than build *with the framework* | Framework or DSL repo; one technical write-up on framework design tradeoffs |

Spend Q3 going deep in your chosen lane: 2–3 substantial projects, one technical write-up per month.

#### Q4 (months 10–12) — output and visibility

By Q4 you've been working on agents for 9 months post-curriculum. The work needs to become visible:

- **Three public technical write-ups** on the specialization you chose. Posted to LinkedIn, your blog, dev.to — wherever your network is. One per month, ~1500 words each.
- **One local meetup talk** or open-source maintainer presentation. Speaking forces clarity.
- **Curriculum revision.** Re-read Weeks 1–12 with 9 months of practice perspective. The gaps you'd fix now are the curriculum's V2. If you choose, fork it publicly — your annotated curriculum becomes its own portfolio piece.

By month 12, you're not someone who completed an interview prep program. You're someone with **a year of demonstrated agent-engineering trajectory** — capstone shipped, iterated; 5+ artifacts in your specialization lane; published writing; visible community participation. That profile gets *recruited*, not just hired.

---

### G.6 Anti-Patterns (what to actively avoid)

**Reading without shipping.** A 3:1 read-to-ship ratio is sustainable; 10:1 is paralysis. If your trend-tracker is 50 items deep but you haven't shipped a lab in 6 weeks, you're consuming, not learning.

**Framework-chasing.** "I'll switch from LangGraph to X because X has better benchmarks." Almost always wrong. Frameworks differ in *layer of complexity allocation*, not raw quality (Week 10 Concept 5). Switch only when your current framework's complexity layer fundamentally mismatches your problem — about once every 12–18 months at most.

**Vendor announcement FOMO.** Microsoft, Google, AWS, Salesforce all ship agent platform features quarterly. You cannot evaluate every one. The triangulation filter exists specifically to defend against this.

**Curriculum bloat.** Resist the urge to add every interesting thing to a weekly primer. The primers are interview-density compressed. If you find yourself adding a 4th paragraph to a Concept, you're probably better off creating a Week N+0.5 expansion week (as Week 2.5 GraphRAG and Week 3.5 Cross-Session Memory exemplify) — keep the original primer cohesive.

**Specialization too early.** Don't pick your Q3 specialization in Q1 or Q2 — you don't have enough data on what energizes you yet. The curriculum exposes you to all six lanes (eval, multi-agent, infra, on-device, platform, retrieval); let preferences emerge from the 9 months of work, not from theory.

**Solo learning without community.** Lurking is the 80% solution; participating is the 100%. By Q3, you should be in at least one Discord/Slack/forum where you ask + answer questions weekly. Network effects compound; learning alone has constant returns.

---

### G.7 Wish List (potential Week 13+ topics)

When the trend-tracker accumulates items that don't fit any current week and earn 3/3 triangulation scores, append them here. Once 3+ items cluster around a topic, that's the signal to write a Week 13+ runbook for it.

Empty as of curriculum-completion date. Examples of clusters worth watching for:

- **Agent-specific compilers / DSPy-style optimization** — could become Week 13 if Compiler-driven prompt optimization sees serious enterprise adoption.
- **On-device agent runtime** — could become Week 14 if MLX / Apple FoundationModels / on-device inference matures into a coherent specialization.
- **Agent governance and red-teaming** — could become Week 15 if regulation or compliance creates real demand.
- **Multi-agent at production scale** — could become Week 16 if the Stanford 2025 finding gets refined enough that "when multi-agent helps" has measurable answers.

---

### G.8 The single Saturday-morning checklist

If you remember nothing else from this appendix, remember this:

```
Saturday morning, 30 min:
[ ] Skim 8 weekly sources (G.2)
[ ] Apply 3-question filter to each item (G.3)
[ ] Capture verdicts in trend-tracker.md (G.1)
[ ] If any 3/3 items: schedule update for next Saturday
[ ] Stop at 30 min, no exceptions
```

Do this 50+ times a year, you'll be ahead of 95% of people in the field — not because you read more, but because you triage better.

---

## Runbook Generation Pattern

Each weekly runbook in the vault (Weeks 0–3 complete; 4–12 generate on demand) follows the same template so you always know what to expect.

### Standard runbook structure

1. **Frontmatter** — title, tags, `companion_to` pointer, lab dir path, time estimate, prerequisites.
2. **Goal + Exit criteria** — a 2-line goal and a checklist of measurable outcomes. You don't "finish" the week until every box is ticked.
3. **Numbered Phases** (usually 5–8 per week):
   - Exact CLI commands you can copy-paste
   - Full Python files saved under `src/NN_purpose.py`
   - A verification block with **expected output** so you know when a step succeeded
4. **`RESULTS.md` template** — the file you commit as proof-of-work. Portfolio narrative lives here.
5. **Lock-in section** — 5 Anki cards + 3 out-loud interview questions. This is what separates the runbook from a "tutorial."
6. **Troubleshooting table** — symptom → likely cause → fix, covering the known failure modes.
7. **Next-week pointer** — explicit wikilink to the next runbook.

### When you want the next runbook, ask like this

> "Generate the Week 4 runbook. Focus especially on the bad-case test suite — I want at least 15 failure scenarios."

Useful modifiers you can add to any generation request:
- **Deeper on X** — "go deeper on the tool-call error-feedback loop"
- **Include Y** — "include a LangGraph variant as a second implementation"
- **Cap at Z hours** — "cap the total week at 10 hours since I'll be traveling"
- **Portfolio-safe only** — "every code sample must use the clean `gpt-oss-20b` or `Qwen3.6-35B-A3B-nvfp4` — no heretic / JANG references"

### Week-by-week runbook briefs (what each will contain when generated)

| Week | Runbook file | Core phases the runbook will contain |
|---|---|---|
| 4 | [[Week 4 - ReAct From Scratch]] | (1) 150-line `react.py` with no framework; (2) 4 local tools (search, repl, read_file, write_file); (3) SQLite trace logging; (4) 15+ bad-case scenarios with a before/after diff per patch; (5) `RESULTS.md` with failure-mode table |
| 5 | [[Week 5 - Pattern Zoo]] | 4 parallel implementations (ReAct, Plan-and-Solve, Reflexion, Orchestrator-Worker) on one task ("research + 1-page summary"); LLM-as-judge rubric scoring; cost/latency/quality 4-way comparison |
| 6 | [[Week 6 - Claude Code Source Dive]] | Reading-only week. 8 subsystem study sheets filled in; one "Architecture Cheat Sheet" markdown that you can bring to interviews; 3 "what I would steal" design ideas |
| 7 | [[Week 7 - Tool Harness]] | Generic `Tool`/`ToolHarness` classes; retry + timeout + budget + idempotency; 20-scenario bad-case suite; local (Qwen3.6) vs cloud (Claude Haiku) reliability comparison |
| 8 | [[Week 8 - Schema Reliability Bench]] | **The signature-question lab.** 5-way comparison (naive prompt / provider-native / Outlines+xgrammar / Instructor+retry / post-validation+repair) across 4 local models + GPT-4o-mini, 100 prompts; draws the 5-layer defense diagram |
| 9 | [[Week 9 - Faithfulness Checker]] | Claim-splitter prompt; NLI-based entailment scorer; SelfCheckGPT-lite (3× sample + BERTScore); abstention router; 30-Q hand-labeled test set |
| 10 | [[Week 10 - Framework Shootout]] | Re-implement Week 4 loop in LangGraph, LlamaIndex agent worker, OpenAI Agents SDK pointing at local mlx server; LOC + traceability + testability decision matrix |
| 11 | [[Week 11 - System Design]] | 5 × 2-hour whiteboard exercises (doc-QA / multi-agent triage / coding agent / financial-research / infra-aware); self-recorded; 6-point self-critique rubric |
| 12 | [[Week 12 - Capstone and Mocks]] | Pick capstone (A/B/C), polish to portfolio bar; 30 mock-interview recordings; 10 job applications submitted with 1 tailored number each |

### How runbooks grow over the quarter

Early runbooks (Weeks 1–3) are **heavy on code scaffolding** because you're learning the stack. Later runbooks (Weeks 7–12) shift toward **design checklists and rubrics** because by then you've absorbed the libraries and the bottleneck is judgment, not syntax. The per-week time estimate stays at 12–15 hours throughout — the balance between coding and thinking is what changes.

---

## Foundational References — System Design

These resources apply across the full curriculum but become most critical from Week 8 onward when design judgment replaces syntax fluency as the bottleneck.

| Resource | Why | Link |
|---|---|---|
| **System Design Interview Vol 1 & 2** (Alex Xu) | Standard interview framework — chapters on API Gateway, Rate Limiter, CDN map directly to Week 11 exercises | Buy or borrow |
| **karanpratapsingh/system-design** | Free, 42k stars, covers DNS → distributed transactions → CQRS; best breadth-first read before Week 11 | [github.com/karanpratapsingh/system-design](https://github.com/karanpratapsingh/system-design) |
| **system-design-primer-update** | Evolution of the original system-design-primer, updated for the GenAI era with AI-native examples and interactive simulations | [github.com/ido777/system-design-primer-update](https://github.com/ido777/system-design-primer-update) |

> The AI-native complement to the above — **NarendraKoya999/system-design-handbook** (covers LLM/RAG/agent system design specifically) — is listed in [[Week 11 - System Design]] under Companion Texts.

— end —
