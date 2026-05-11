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

**Phase goal.** Make RAG your strongest interview dimension. You're a cloud infrastructure engineer — own the retrieval pipeline like you own a Terraform module. By end of Phase 1 you have empirically-measured numbers on **five RAG backends** (vector + hybrid + GraphRAG + structure-aware tree-index + agentic) and you can defend each one's failure mode in interviews, anchored to your own measured ceilings: vector hybrid recall@10 (W1-2), GraphRAG multi-hop W/L (W2.5), tree-v3 **16/16 = 1.000 GT-judge** on Berkshire 2023 (W2.7), RAGAS faithfulness deltas (W3), and the 5-node grade-rewrite agentic loop (W3.7).

> **Runbook pattern.** Each week has a dedicated step-by-step runbook in the vault: [[Week 1 - Vector Retrieval Baseline]], [[Week 2 - Rerank and Context Compression]], [[Week 2.5 - GraphRAG]], [[Week 2.7 - Structure-Aware RAG]], [[Week 3 - RAG Evaluation]], [[Week 3.5 - Cross-Session Memory]], [[Week 3.7 - Agentic RAG]]. The text below is the *overview*; the runbooks are the *how*. Treat each runbook like a preflight checklist — tick phases, don't just read. Runbooks for Weeks 4–12 follow the same template and are generated on demand (see §"Runbook Generation Pattern" at the bottom of this file).

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

> **Connects to W2.7.** This week's "when does GraphRAG beat vector" hypothesis is **re-tested** in Week 2.7 with a stricter judge (GT-judge) and a third backend (structure-aware tree). The Week 2.7 result reverses the May 7 "graph wins on Berkshire" reading — under GT-judge, Graph 0.375 / Vector 0.500 / Tree-v3 1.000 — confirming graph DOES degenerate on single-document corpora once the entity-recall judge stops favoring its broad keyword retrieval. The discipline rule: revisit refuted hypotheses when the eval set OR the judging methodology changes.

### Week 2.7 — Structure-Aware RAG (PageIndex / Tree-Index) (half-week insert, ~8–10h)
> Detailed runbook: [[Week 2.7 - Structure-Aware RAG]]

**Theory (2–3h).**
- Read: PageIndex (Couchbase 2024) — agentic tree-index, RAPTOR (Sarthi et al. 2024) — recursive hierarchical clustering, Anthropic's "Contextual Retrieval" — why fine chunks lose document context.
- Master: why both vector and graph backends degenerate on long *structured* documents (10-Ks, RFCs, research papers), the agentic-loop vs greedy-tree-walk distinction (PageIndex's "navigator only sees titles" failure mode), Level-2 RAPTOR-style cluster pre-fetch, top-K δ-band cluster routing for noise-floor tiebreak, BGE-M3 dense+sparse hybrid as a chunk-level fallback layer.

**Lab (6–7h) — `lab-02-7-pageindex`.**
1. Pull a long structured PDF (Berkshire's 2023 10-K, 152 pages) and parse via `pypdf` → page-position map.
2. Build the tree index: LLM-driven heading detection → JSON tree builder → `split_large_nodes` for oversized leaves → per-node fact-rich summarization. ~70 LLM calls, `tree.json` ~100 KB.
3. Build the cluster index (`summary_index.json`): K-means on BGE-M3 node-summary embeddings (k=8 or `--auto-k` via silhouette), per-cluster TF-IDF tags + centroid summary.
4. Build the page-vector index (`page_vectors.npy` + `.sparse.json`): BGE-M3 hybrid encoder (dense + sparse in one forward pass) for the chunk-level fallback layer.
5. Wire `AgenticTreeRetriever` — multi-iter loop (max_iter=4) with `get_page_content(start, end)` tool, cluster-hint pre-fetch, BUDGET EXHAUSTED forced synthesis with 5 strict rules (anti-hallucination + output-format pressure), composite-signal low-quality detection, chunk-level fallback with neighbor-page expansion.
6. Run the **3-way comparison v3**: Vector vs GraphRAG (lab-02-5) vs Tree-v3 on a hand-curated 16-Q eval (4 categories: section-specific factoid, cross-section synthesis, citation-required, out-of-document refusal). Score with GT-judge (binary pass/fail against pre-authored `pass_criteria` per question) anchored to PDF-grounded ground truth, not entity-recall.
7. `RESULTS.md` includes the per-category comparison table, the eval methodology (GT-judge vs entity-recall disagreement analysis), and a phase-progression log showing 0.44 → 0.79 → 0.885 → 0.938 → 1.000 across Phases 1-9.

**Exit criteria.** 90-second answer to "When does tree-index RAG beat vector and graph?" — name the cluster-pre-fetch + BUDGET-prompt + chunk-fallback combo, cite the **16/16 = 1.000 GT-judge final** on Berkshire 2023 vs Vector 0.500 / Graph 0.375, name the per-category breakdown (cross-section 1.00 vs vector/graph 0.00 — categorical win), and name the latency tradeoff (~40× vector — production routing sends factoid + OOD to vector and reserves tree for cross-section synthesis). Bonus: explain why entity-recall judging is structurally broken for synthesis questions and why GT-judge `pass_criteria` is permission-to-be-partial encoded as natural-language predicates.

**Infra bridge.** Tree-index re-build is a **DAG of materialized views** with distinct refresh frequencies: tree (~10 min, LLM-bound, refresh on PDF change) → cluster (~30s, K-means over tree summaries, refresh on K-knob tuning) → entity (~3 min, regex over tree bodies, refresh on tree change) → page-vector (~5 min, BGE-M3 over PDF pages, independent of tree). The atomic-swap deployment pattern (build all four to `data/staging/`, run the 16-Q eval gate, swap to `data/` only on pass_rate ≥ baseline − tolerance) is exactly the **blue-green deployment** discipline applied to retrieval indexes — same primitive, different artifact.

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

> **Eval-methodology cross-ref.** RAGAS's faithfulness / context-precision / answer-relevancy metrics all still rest on lexical-or-embedding signals over candidate vs reference text — fast and broadly correct, but they undercount substantive synthesis (long answers that paraphrase) and overcount confident hallucinations (right keywords arranged into wrong claims). See [[Week 2.7 - Structure-Aware RAG#Evaluation Reference — GT-Judge Methodology]] for the **GT-judge** complement: binary pass/fail with hand-curated `pass_criteria` per question that encodes the author's judgment about what counts as a correct answer. Use RAGAS for continuous regression-detection on every commit; reserve GT-judge for release-gate runs and architectural-decision evidence. Two-tier eval is the production discipline.

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

### Week 3.5.5 — Multi-Agent Shared Memory (Guild MCP) (half-week insert, ~4–6h)
> Detailed runbook: [[Week 3.5.5 - Multi-Agent Shared Memory]] *(brief; runbook generated on demand)*

**Theory (1–2h).**
- Read: [`mathomhaus/guild`](https://github.com/mathomhaus/guild) README + `internal/store/sqlite/` schema + `internal/retrieve/` (BM25 + dense + RRF fusion k=60) + `internal/mcp/` tool surface. Anthropic's MCP spec — focus on the resource + tool primitives.
- Master: where multi-agent memory diverges from single-agent W3.5 memory (atomic claims on concurrent task acquisition, scroll-versioning across timeline-overlapping sessions, oath as procedural principle vs lore as semantic archive), why MCP-protocol-native memory beats library-bound memory when agents span multiple harnesses (Claude Code / Cursor / Codex sharing one substrate).

**Lab (3–4h) — `lab-03.5.5-guild-multiagent`.**
1. Install guild via the pre-built `install.sh` (with `-tags=withembed` for semantic retrieval). Verify with `guild --version`. Run `guild init` in a fresh test project; answer the MCP-client-registration prompts.
2. Open the test project in TWO MCP clients (e.g. Claude Code + Cursor). Confirm both clients see the same `guild_session_start()` output. Demonstrate "same state, any agent" with a 5-line scripted scenario.
3. **Atomic-claim scenario**: spawn two agent sessions in parallel; have each call `quest_accept` on the same available quest within 2 seconds. Demonstrate that exactly ONE wins the lock and the other receives a "claimed by..." rejection. Trace the SQLite WAL to show the atomicity guarantee.
4. **Cross-session handoff**: run a 3-act session — agent A completes a quest, writes a scroll, exits. Spawn agent B; it picks up the scroll, completes a dependent quest, writes another scroll. Spawn agent C; it sees the full chain. Document the handoff in `RESULTS.md`.
5. Write a comparison `RESULTS.md` matrix: your W3.5 single-agent lab vs guild on (a) memory primitive count, (b) retrieval latency, (c) concurrent-agent support, (d) MCP-client portability, (e) installation overhead.
6. Compose a 15-Q multi-agent recall benchmark (5 same-agent recall, 5 cross-agent handoff, 5 contradiction-during-parallel-work). Target ≥ 12/15 passing.

**Exit criteria.** 90-second answer to "how do you give MULTIPLE agents a shared memory substrate?" — name the atomic-lock primitive (compare to W3.5's single-agent recall/remember), the MCP-protocol-as-memory-API pattern (every harness consumes the same tools), and the SCD-2 versioning that survives concurrent edits. Cite the side-by-side W3.5-lab-vs-guild comparison table in `RESULTS.md`.

**Infra bridge.** Multi-agent shared memory is a distributed-systems primitive in miniature. SQLite WAL + atomic-claim locks is the same pattern as Postgres advisory locks or DynamoDB conditional writes. Guild proves you don't need a Raft cluster or a service mesh to coordinate agents — embedded SQLite + careful schema design handles single-host parallel-agent workloads. When you DO need cross-host coordination, the pattern transfers to a real distributed lock service (Consul / etcd) without architectural rework — same primitive, different physical substrate.

### Week 3.5.8 — Two-Tier Memory Architecture (guild + EverCore) (half-week insert, ~6–8h)
> Detailed runbook: [[Week 3.5.8 - Two-Tier Memory Architecture]] *(brief; chapter file written)*

The capstone of the W3.5 cluster. W3.5 built single-agent memory; W3.5.5 added multi-agent coordination via guild; W3.5.8 wires guild (operational tier) and EverCore (semantic tier) into a single production-shaped two-tier architecture with an explicit consolidation pipeline between them. Includes the LongMemEval benchmark from the retired W3.5.7 as Phase 5's measurement step.

**Theory (1.5h).**
- Read: the biological-memory analogy — hippocampus (fast-write, short-term, coordination) + neocortex (slow-write, durable, semantic) + memory consolidation during sleep. [Letta (formerly MemGPT) paper](https://arxiv.org/abs/2310.08560) for the canonical RAM↔archive two-tier in agent systems. [LongMemEval](https://github.com/xiaowu0162/LongMemEval) + [LoCoMo](https://github.com/snap-research/locomo) for industry-standard memory benchmarks. EverOS's `methods/EverCore/evaluation/` for production-grade benchmark harness shape.
- Master:
  - WHEN to use each tier (atomic-claim → guild; semantic recall → EverCore; never the reverse)
  - The consolidation pipeline as the load-bearing pattern (when to consolidate, what to consolidate, idempotency + ordering)
  - The cache-aside / Debezium-style data-movement analogy from data engineering
  - Why two-tier beats single-tier on cross-session-AND-cross-agent questions

**Lab (5–6.5h) — `lab-03.5.8-two-tier-memory`.**
1. **Phase 1 — Bring up both services (~30min)**: guild via homebrew install + EverCore via docker compose. Verify both reachable with smoke-test scripts.
2. **Phase 2 — Two-tier Python orchestrator (~2h)**: build `TieredMemory(guild_client, evercore_client)` wrapper with `claim_task() / complete_task(scroll) / query_context(query) / consolidate()` methods. guild handles claim+scroll; EverCore handles semantic query+imprint.
3. **Phase 3 — Consolidation pipeline (~1.5h)**: batch job that pulls closed scrolls from guild, extracts task summaries, imprints them into EverCore as semantic memories. Idempotency via scroll_id deduplication; ordering via timestamp. Tests for both.
4. **Phase 4 — Two-agent shared-knowledge demo (~1.5h)**: agent A completes a task in session 1 → consolidation runs → agent B starts session 2 with cross-session context retrieved from EverCore, then claims next quest in guild.
5. **Phase 5 — Four-way benchmark (~1.5h)**: same 15-Q multi-agent recall, run against (a) no-memory baseline, (b) guild-only, (c) EverCore-only, (d) **two-tier**. Optional extension: run LongMemEval `oracle` subset for industry-standard scoring (carries the retired W3.5.7's purpose into this lab's Phase 5).

**Exit criteria.** 90-second answer to "how would you architect memory for a multi-agent system?" — name the two-tier pattern (operational + semantic), the biological analogy (hippocampus + neocortex + REM-sleep consolidation), the consolidation pipeline (REM-sleep-style batch transfer with idempotency + ordering). Cite the measured 4-way benchmark differential — two-tier should beat each single-tier by ≥10% on cross-session questions. Articulate WHY each system is wrong for the OTHER's job. Bonus: name Letta as the canonical production parallel.

**Infra bridge.** Two-tier memory is the cache-aside pattern applied to agent state. guild is Redis-tier (hot, sub-100ms, ephemeral). EverCore is Postgres-tier (cold, slower, durable, semantic-indexable). The consolidation pipeline is Debezium / Kafka Connect moving rows from transactional → analytical store — same primitive, different artifact. Pattern transfers directly to any agent system where short-term coordination and long-term institutional knowledge have different access patterns.

### Week 3.7 — Agentic RAG (half-week insert, ~6–8h)
> Detailed runbook: [[Week 3.7 - Agentic RAG]]

**Theory (2–3h).**
- Read: LangChain's `langgraph_agentic_rag.ipynb`, Singh et al. *Agentic Retrieval-Augmented Generation* survey (2025), CRAG (Yan et al., 2024), Adaptive-RAG, GeAR.
- Master: the canonical 5-node graph (decide → retrieve → grade → rewrite → answer), where single-pass RAG breaks (ambiguous queries, low-confidence retrieval), the four named architectures (CRAG / Adaptive-RAG / Self-RAG / GeAR) and the tradeoffs between them.

> **Builds on:** W2.7's agentic multi-iter loop is the underlying primitive that the 5-node graph formalizes. W2.7 hand-rolls the loop (LLM emits tool_call → fetch → observation → next LLM call) without explicit decide/grade/rewrite nodes; this week graduates that primitive to a typed state graph. The W2.7 BUDGET EXHAUSTED + low-quality detection + chunk-level fallback chain is the manual version of CRAG's confidence-threshold + retrieve-fallback pattern — read W2.7's Phase 8 Block 4 + Phase 9 Block 2 before this lab to internalize WHY the formal graph matters.

**Lab (4–5h) — `lab-03.7-agentic-rag`.**
1. Run LangChain's official Agentic RAG notebook end-to-end against your Week 1 corpus + Qdrant + BGE-M3.
2. Build a comparison harness scoring Week 3's single-pass pipeline vs the 5-node graph on the same 50-Q dev set; quantify the lift on ambiguous queries specifically.
3. Implement one CRAG variant with a confidence threshold and web-search fallback.
4. `RESULTS.md` includes a comparison matrix + decision tree — when does Agentic RAG help, when does the cost/latency exceed the quality gain.

**Exit criteria.** 90-second answer to "what's wrong with single-pass RAG and what's the production fix?" — name the 5 nodes, cite a measured lift from your bench, name CRAG by author + year.

**Infra bridge.** Agentic RAG = retry-with-backoff over a retrieval index. The "grade → rewrite → retry" loop is the same shape as a circuit breaker around an unreliable downstream service — same operational primitive, different failure signal.

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

### Week 5.5 — Metacognition: Reflexion + Self-Critique (half-week insert, ~5–6h)
> Detailed runbook: [[Week 5.5 - Metacognition]]

**Theory (2h).**
- Read: Reflexion (Shinn et al., 2023), Self-Refine (Madaan et al., 2023), Self-Consistency (Wang et al., 2023).
- Master: why a ReAct loop alone keeps making the same mistake, the verifier-signal → episodic-memory → reflection-pass loop, when sampling diversity + majority vote is cheaper than a critic, and the failure mode where reflection makes the agent worse (overcorrection).

**Lab (3h) — `lab-05.5-metacognition`.**
1. Wrap your Week 4 ReAct agent with a Reflexion outer loop: verifier tags each trajectory pass/fail, failure stories get appended to an episodic memory and replayed on the next attempt.
2. Implement Self-Consistency on top: sample N=5, majority-vote the answer, compare cost/quality vs Reflexion on the same task set.
3. Add one ablation that intentionally injects a bad critic and shows the overcorrection failure mode in action.

**Exit criteria.** Cold answer to "how would you handle an agent that keeps making the same mistake?" — name the loop, cite a paper, name one failure mode.

**Infra bridge.** Reflexion's episodic memory is a post-mortem corpus. Production SRE runbooks and Reflexion's experience replay are the same primitive: write down what failed, retrieve when something similar happens, prevent the regression.

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

### Week 6.5 — Hermes Agent Hands-On (half-week insert, ~6–8h)
> Detailed runbook: [[Week 6.5 - Hermes Agent Hands-On]]

**Theory (2h).**
- Read: Hermes Agent README + skill-creation loop docs, Pi repo (the minimalist counter-thesis from W6), the Anthropic "model-coded skills" research notes.
- Master: the extensibility-spectrum trade-off triangle — Claude Code (curated, 20+ surfaces) vs Pi (on-demand, 4 tools) vs Hermes (learned, auto-generated). Why each ships, where each breaks, the audit-trail problem unique to learned-skill systems.

**Lab (4–6h) — `lab-06.5-hermes-handson`.**
1. Run Hermes Agent locally against your oMLX or vMLX endpoint.
2. Execute the same canonical task in three agents (Claude Code, Pi, Hermes); capture comparison notes.
3. Observe at least one skill being created by Hermes; inspect the generated code on disk.
4. Audit one learned skill — read the generated code, decide whether you'd trust it in production, write up the reasoning.
5. `RESULTS.md` ships a 3×3 matrix (3 agents × 3 axes: extensibility, auditability, cost) + decision tree for "when would I ship which?"

**Exit criteria.** 60-second answer to "what is Hermes Agent's skill-creation loop, and what is its biggest production risk?" grounded in your own observation, not theory.

**Infra bridge.** Hermes' learned-skill cache is a build artifact — generated, persisted, versioned. Auditing a learned skill before promoting it = code review of an autogenerated migration. Same governance pattern, new surface.

### Week 6.7 — Authoring Agent Skills (Anthropic Pattern) (half-week insert, ~5h)
> Detailed runbook: [[Week 6.7 - Authoring Agent Skills]]

**Theory (1.5h).**
- Read: Anthropic's SKILL.md spec, the `~/.claude/skills/` discovery mechanism, the trigger-engineering pattern (description-field design).
- Master: the loading mechanism (frontmatter routing, capability scoping), why the description field is harder than the body, what makes a trigger pattern fire reliably vs noisily, and the consumer-vs-author mental shift.

**Lab (3.5h) — `lab-06.7-skill-authoring`.**
1. Author three production-quality skills end-to-end — pick from `/benchmark`, `/canary`, `/compress`, `/grade`, or another reusable workflow you've actually wanted.
2. Each skill ships with a SKILL.md, a working trigger pattern, and a verification step ("run this prompt, observe this behavior").
3. Install all three globally to `~/.claude/skills/` and use them in real sessions for a week. Track: did the trigger fire when expected, did it misfire, did the description field need tuning.
4. Write up the description-field iteration log — before/after pairs that show what made the skill go from useless or noisy to reliable.

**Exit criteria.** You ship three skills, you can articulate the description-field design rule, and you can answer "what's the difference between a prompt and a skill?" without hand-waving.

**Infra bridge.** A skill is the unit of repeatable agent capability. Same shape as a versioned IaC module — write it once, version it, install it globally, share it across a team. Skill authoring is to prompt engineering what Terraform modules are to one-off scripts.

### Week 6.8 — Agent Communication Protocol Survey (MCP / A2A / ANP) (half-week insert, ~3h)
> Detailed runbook: [[Week 6.8 - Protocol Survey]] *(brief; reading-heavy, no major lab artifact)*

**Theory (2h).**
- Read: hello-agents Ch 10 [Agent Communication Protocols](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter10/Chapter10-Agent-Communication-Protocols.md). Anthropic MCP spec (definitive). Google's A2A (Agent2Agent) protocol announcement + spec. ANP (Agent Network Protocol) — third entrant, focuses on decentralized agent discovery + identity.
- Master:
  - **MCP (Anthropic, Nov 2024)** — tool/resource/prompt primitives between a host (agent) and a server (capability provider). Stdio + HTTP+SSE transports. Now adopted by OpenAI + Google. Best for *single-agent connects to many capabilities*.
  - **A2A (Google, Apr 2025)** — agent-to-agent collaboration protocol. Capability advertisement, task delegation, message passing between PEER agents. Best for *multi-agent task decomposition + cross-vendor agent collaboration*.
  - **ANP (open spec, 2025)** — decentralized agent discovery + DID (decentralized identity)-based authentication. W3C-aligned. Best for *agent-to-agent communication across organizational boundaries without a central broker*.
  - The three philosophies compared: MCP is "agent + tools" (server is dumb capability), A2A is "agent + agent" (both sides are smart, peer-to-peer), ANP is "agent in a network" (discovery + identity primitives, no central hub).
  - Where they overlap, where they don't, and the migration story (W7 lab harness is MCP-native; A2A wraps MCP for inter-agent flows; ANP adds the discovery layer above both).

**Lab (1h) — `lab-06.8-protocol-survey`.**
1. Write a 1-page comparison ADR (`docs/PROTOCOL-SURVEY-ADR.md`) covering: (a) what each protocol solves, (b) which transport each uses, (c) authentication model, (d) interop story, (e) one concrete use case where each is the right pick.
2. Annotate your W3.5.5 guild server: which of the three protocols does it implement (MCP), which would be needed if multiple guild instances coordinated across hosts (A2A or ANP).
3. Optional: install one A2A reference implementation (Google's open-sourced reference exists as of 2026) and run a 2-agent handshake. ~30 min.

**Exit criteria.** 90-second answer to "what's the difference between MCP, A2A, and ANP — and which would you pick for X?" — name the three primitives (agent↔tool / agent↔agent peer / agent↔agent decentralized), give one concrete use case per protocol, articulate the layering (ANP discovery above A2A communication above MCP capability). Bonus: explain why MCP won the single-agent-tool battle (open spec + Anthropic/OpenAI/Google all adopted) but A2A + ANP are still in play for multi-agent + cross-org cases.

**Infra bridge.** The three protocols are agent-world analogues to service-mesh primitives: MCP ≈ service-to-database (capability access), A2A ≈ service-to-service mTLS (peer communication), ANP ≈ service discovery + identity (Consul + SPIFFE). The protocol landscape is going through the same consolidation cycle that service meshes went through in 2018-2020 — bet on the open spec with multi-vendor adoption, hedge with thin wrappers around the others.

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

### Week 7.5 — Computer Use and Browser Agents (half-week insert, ~5–6h)
> Detailed runbook: [[Week 7.5 - Computer Use and Browser Agents]]

**Theory (2h).**
- Read: Anthropic Computer Use beta blog (Oct 2024), OpenAI Operator launch post (Jan 2025), browser-use README, Selenium/Playwright docs (one chapter each).
- Master: the three generations of browser automation (deterministic DOM scripts → vision-language CUA → hybrid DOM-aware planners), why Generation 1 is structurally brittle, where the cost/latency curve flips, and the production safety controls (visual diff, action allowlist, cost ceiling).

**Lab (3–4h) — `lab-07.5-computer-use`.**
1. Write the same task three ways: a Playwright script (Gen 1), a browser-use agent (Gen 3 hybrid), and a pure Computer Use loop (Gen 2 vision-only).
2. Measure cost, latency, and success rate on a 10-task suite that includes one CSS-class rename ablation to expose Gen 1's brittleness.
3. Build a safety wrapper: action allowlist, per-step budget cap, screenshot diff alarm.

**Exit criteria.** Cold answer to "when does computer use beat Playwright in production?" — name the breakpoint (cost-per-task vs human-maintenance), name one safety control you'd require before shipping.

**Infra bridge.** CUA is RPA with an LLM as the recognizer. Same governance shape as RPA: every action is an audit-log event, every credential is a least-privilege principal, every page change is a regression candidate.

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

### Week 8.5 — Voice AI Agents (half-week insert, ~5–6h)
> Detailed runbook: [[Week 8.5 - Voice AI Agents]]

**Theory (2h).**
- Read: OpenAI Realtime API launch (Oct 2024), faster-whisper docs, ElevenLabs / Cartesia TTS architecture posts, the Anthropic / OpenAI agent + voice integration guides.
- Master: cascaded pipeline (VAD → STT → LLM → TTS) vs end-to-end native-audio architecture, the latency budget (target <500ms total time-to-first-audio), interruption handling (barge-in detection), the cost-per-minute breakdown.

**Lab (3–4h) — `lab-08.5-voice`.**
1. Build a local cascaded pipeline — faster-whisper + Claude + ElevenLabs (or Coqui locally). Wire it to a microphone + speaker. Measure end-to-end latency on a 20-turn conversation.
2. Compare against OpenAI Realtime API on the same script — capture latency + cost-per-minute deltas.
3. Add barge-in handling: if the user starts speaking while the agent is talking, cut TTS and restart with the new audio.

**Exit criteria.** 90-second answer to "design a customer-support voice agent" that names the architecture choice, the latency budget, the interruption handling, and the cost ceiling.

**Infra bridge.** Voice = real-time pipeline with a hard latency SLA. Same operational shape as a low-latency trading or ad-bidding pipeline — every component has a budget, every queue is bounded, every fallback is pre-wired.

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

### Week 9.5 — Agentic RL Fine-Tuning (half-week insert, ~8–10h)
> Detailed runbook: [[Week 9.5 - Agentic RL Fine-Tuning]] *(brief; runbook generated on demand)*

**Theory (3h).**
- Read: hello-agents Ch 11 [Agentic-RL](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter11/Chapter11-Agentic-RL.md) (the canonical SFT→GRPO walkthrough). DeepSeek-R1 paper (GRPO algorithm origin). RLHF survey (Ouyang et al. 2022 — InstructGPT). DPO paper (Rafailov et al. 2023 — preference learning without RL). Anthropic's Constitutional AI paper for the RLAIF variant.
- Master:
  - The two-stage LLM training pipeline (pretrain → post-train) and what post-train accomplishes (instruction-following + alignment + multi-step reasoning)
  - SFT vs RLHF vs DPO vs GRPO — what each optimizes, where each breaks
  - **Agentic RL framing**: LLM as policy in (state = current context + scratchpad, action = next token / next tool call, reward = task success). Multi-step credit assignment via group-relative advantages.
  - **GRPO's group-relative trick**: skip the value-function critic; for each prompt, sample N completions, score them, normalize advantages within the group. ~50% less compute than PPO, comparable quality on reasoning tasks.
  - When agentic RL is the right move (cold-start reasoning tasks, tool-use refinement) and when SFT alone suffices (instruction-following, format compliance, refusal patterns)

**Lab (5–7h) — `lab-09.5-agentic-rl`.**
1. **Pre-train baseline measurement**: pick a small open-source base model (Qwen3-0.5B or gpt-oss-3B). Run it zero-shot on the GSM8K-mini test set (50 questions). Record pass rate, mean tokens per answer, refusal rate. This is the floor.
2. **SFT stage**: curate 200-500 (problem, chain-of-thought, answer) tuples from GSM8K-train. Fine-tune the base model via mlx-lm or unsloth (use LoRA r=16 for memory efficiency). Re-run on test set. Record delta.
3. **GRPO stage**: implement GRPO on the SFT model. For each problem in a small training set (~50 problems × 8 epochs), sample N=8 completions, score each by answer correctness (1.0 if correct, 0.0 otherwise), normalize advantages within the group, apply policy update. Re-run on test set. Record delta from SFT.
4. **Ablation table**: 4-row comparison of pre-train / SFT / GRPO / SFT+GRPO on (pass rate, mean tokens, refusal rate, train wall-time, train cost). Write `RESULTS.md`.
5. **Tool-use extension** (optional, advanced): swap the math task for a tool-using task. Define reward = (correct answer AND valid tool calls AND no hallucinated tool args). Measure improvement on tool reliability — this is the production-relevant signal that pure math reasoning misses.

**Exit criteria.** 90-second answer to "how do you train an agent's reasoning capability beyond what its base model gives?" — name the three stages (pretrain / SFT / RL), name the GRPO group-relative trick (skip the critic, sample N per prompt, normalize within-group), cite your measured delta (pre-train → SFT → GRPO on GSM8K-mini), name the tradeoff (RL training requires a clean reward signal — works for math/code/games, breaks on open-ended subjective tasks). Bonus: when interviewers ask "have you trained an agent?", answer YES and cite the lab.

**Infra bridge.** Agentic RL training is a feedback-loop system identical to CI/CD: training data flows in (the training set + reward signal), the policy gets updated (the deploy), eval metrics gate the next iteration (the test stage), failures route to investigation (debugging a low-reward batch is the same shape as debugging a flaky test suite). The "8-epoch GRPO loop" is a CI pipeline with cost-per-run on the order of single-digit GPU-hours; same operational discipline applies (atomic commits, reproducible runs, eval-as-gate). Local MLX on M-series Macs makes this affordable for self-study; cloud cost would be ~$10-30 per SFT+GRPO run on Modal or RunPod.

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

### Week 11.5 — Agent Security (half-week insert, ~5–6h)
> Detailed runbook: [[Week 11.5 - Agent Security]]

**Theory (2.5h).**
- Read: Anthropic / Greshake et al. on indirect prompt injection, the OWASP LLM Top 10 (with focus on tool-poisoning and excessive agency), Llama Guard / Constitutional Classifier docs, firejail/Docker sandbox patterns.
- Master: the four trust tiers (system prompt > developer-supplied tools > user message > retrieved/tool-output content), the five attack classes (direct/indirect injection, tool poisoning, exfil-via-side-channel, privilege escalation), the three defense layers (input validation, capability containment, output filtering).

**Lab (3h) — `lab-11.5-agent-security`.**
1. Take your Week 7 tool harness and write a 10-attack red-team suite — one entry per attack class above, plus three indirect-injection variants delivered via RAG.
2. Implement each defense layer: pydantic-validated tool input, firejail sandbox for shell tools, Llama Guard or Constitutional Classifier on outputs.
3. Run the attack suite before/after each defense — record the kill rate per layer. The goal is a layered-defense table, not a single perfect filter.

**Exit criteria.** Cold-answer "design a permission system for an agent that writes files and sends emails" — name the trust tiers, name two attack classes, name two defenses, cite the Greshake paper or equivalent.

**Infra bridge.** Agent security is RBAC + WAF + sandbox. Trust tiers = principals; tools = privileged operations; output filter = egress firewall. The composition is what's new; each primitive maps to something you've shipped.

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
├── GraphRAG / multi-hop knowledge-graph retrieval ──────────→ Week 2.5
├── Agentic RAG / CRAG / Adaptive-RAG / iterative retrieval ─→ Week 3.7
├── Cross-session memory / persistent agent memory ──────────→ Week 3.5
├── ReAct loop / scratchpad design / max-iter / errors ──────→ Week 4
├── Multi-agent / Plan-and-Solve / Orchestrator-Worker ──────→ Week 5
├── Reflexion / Self-Refine / Self-Consistency / metacog ────→ Week 5.5
├── Claude Code / Aider / Codex CLI / source-leak analysis ──→ Week 6
├── Hermes Agent / learned skills / Pi minimalism ───────────→ Week 6.5
├── Authoring Claude Code skills / SKILL.md / triggers ──────→ Week 6.7
├── Tool use / MCP / function calling / permission systems ──→ Week 7
├── Computer Use / browser agents / CUA / Playwright ────────→ Week 7.5
├── Structured output / constrained decoding / JSON schema ──→ Week 8
├── Voice AI / Realtime API / Whisper + TTS pipelines ───────→ Week 8.5
├── Hallucination / faithfulness / verification / abstention →→ Week 9
├── LangGraph / LlamaIndex / framework comparison / Chain ───→ Week 10
├── System design pattern / SRE agent / enterprise platform ─→ Week 11
├── Prompt injection / tool poisoning / agent sandbox ───────→ Week 11.5
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

## Appendix H — Job-Search Execution: Targeting, Reality-Check, Negotiation

> Added 2026-05-07 from the alexeygrigorev/ai-engineering-field-guide gap analysis. The technical curriculum (W0–W12 + supplements) is thorough; this appendix closes the *job-search execution* layer — segment targeting, reality-vs-JD reading, AI-Support sub-track recognition, references, offers, negotiation. Reader profile: cloud infra eng (3 yrs at AWS, exited March 2026 in 14k layoff), local-first MLX stack, currently full-time on the 12-week ramp. The recommendations here are calibrated to that profile, not generic "AI Engineer" advice.

### H.1 — Market Segmentation: Three AI-Engineer Job Buckets

The "AI Engineer" job title spans three distinct company segments with different interview emphases and tech-stack expectations. Spray-applying a single resume across all three is the most common job-search mistake; targeted framing per segment doubles response rates.

| Segment | Examples | Interview emphasis | Stack expectations | Fit for the reader profile |
|---|---|---|---|---|
| **Product** (AI-first product companies) | Cursor, Hebbia, Granola, Limitless, Glean | Product judgment + UX + RAG quality | Cloud APIs, vector DBs, LLM-orchestration libs (LangChain / LlamaIndex / DSPy) | Mid — competes with PM/design-fluent candidates; differentiator is the W7+W8 stability work, not the RAG depth |
| **Infrastructure** (AI-tooling / infra) | Modal, Pinecone, Braintrust, Weaviate, Astronomer, Tecton | Systems design + cost economics + reliability | Distributed systems, GPU infra, SRE tooling, observability | **Strongest fit** — 3-yr AWS infra background maps directly; W7 tool harness + W11 system design + Capstone C are the portfolio anchors |
| **Model labs** (frontier-model companies) | OpenAI, Anthropic, Meta AI, DeepMind | ML research + scaling laws + paper depth | Distributed training, CUDA, JAX/PyTorch internals, paper-citing fluency | Low — ~4% of jobs are primary-FT roles; curriculum is right to skip pretraining; deprioritize |

**Action:** Maintain a single `target_companies.md` (in `~/Documents/Obsidian Vault/job-search/`) listing 15 companies bucketed by segment. For each, record one resume-bullet → JD-keyword mapping. Build during W11 alongside the system-design rehearsals so the framing is fresh when W12 applications go out.

### H.2 — The AI-Support Sub-Track (28.5% of Jobs, Lower Competition)

The field guide flags a distinct sub-segment: **AI Platform Engineer / AI Infra Engineer / ML Platform Engineer**. These roles work *near* AI but not *on* AI — they build the platforms, observability, evaluation infrastructure, and deployment pipelines that AI Engineers consume. The field guide measured this at ~28.5% of all "AI Engineer"-adjacent JDs.

**Why this matters for the reader profile specifically:**
- AI-Support roles competition pool is mostly *other infra engineers* who lack hands-on LLM experience. The 12-week curriculum closes that gap.
- Capstone C (infra-aware SRE agent) qualifies for **both** "AI Engineer" (via the agent) AND "AI Platform Engineer" (via the platform engineering signal).
- Salary bands often comparable to AI Engineer at a given level; sometimes higher because supply is tighter.

**Action:** Maintain **two README variants** for Capstone C in the same lab repo:
- `README.md` — leads with the agent, frames as "AI Engineer with platform depth." Use for Product + Infrastructure segment applications.
- `README-platform.md` — leads with the platform engineering (PromQL integration, k8s rollout correlation, Prometheus alerting, observability story), frames as "Platform Engineer with AI fluency." Use for AI-Support sub-track applications.
- 30 minutes of work; doubles the addressable JD pool.

### H.3 — Reading JDs Realistically (the "80% Glue Code" Reality Check)

The field guide's role-analysis section (sample of 895–2,445 JDs) finds that the day-to-day work in most "AI Engineer" jobs is *not* prompt engineering or model selection — it is glue code, monitoring, debugging long agent chains, and managing eval pipelines. Three-bucket taxonomy from the field guide:

| Work-type bucket | What the role actually does | Curriculum mapping |
|---|---|---|
| **Orchestrator** | Build agent loops, tool integrations, state management | W4 (ReAct), W5 (patterns), W7 (tool harness), W6.5 (Hermes) |
| **Evals Specialist** | Build offline evals, online monitoring, regression detection | W3 (RAGAS), W9 (faithfulness), W11 (system design rubric) |
| **Efficiency Wrapper** | Cost reduction, latency optimization, caching, model routing | W2 (rerank/compress), W11 Gate 7 (cost-cut), W2.5 routing |

**Action:** For each of the ≥10 applications in W12, annotate the JD with a 3-line "what this job actually is" guess using the bucket taxonomy. Tailor your cover note to the inferred bucket — a JD that says "build agentic systems" but lists 70% of duties as eval/monitoring/cost-tuning is an Evals Specialist role wearing an Orchestrator title. Frame your application around your W3 + W9 + W11 work, not your W4 ReAct lab.

**Discipline rule:** Never apply to a JD without spending 5 minutes annotating it. Tailored applications convert at 5–10× the rate of spray-applied generic ones, especially with a non-FAANG resume.

### H.4 — References, Offers, Negotiation (the Layoff-Specific Risks)

Post-AWS layoff increases two risks the field guide flagged as common stumbles:

**Risk 1 — References go cold fast.** Top labs (OpenAI, Anthropic, Cursor, Hebbia) require 2–3 references at offer stage. After a layoff, your AWS network is disrupted; warm-call your references within 60 days of separation, not at offer stage. Maintain a `references.md` with 4 contacts (target: 2 strong, 2 backup), each pre-warmed with a 15-min call and a heads-up that you're job-searching.

**Risk 2 — Offer-window pressure + weak BATNA.** Field guide reports candidates accepting first offers under 7-day expiration windows because they had nothing else in pipeline. Compounded by layoff narrative if the candidate signals desperation in negotiation. Mitigations:
- Apply in batches of 5–10 simultaneously so multiple offer timelines overlap.
- Always ask for a 2-week extension on offer windows (~70% success rate per field guide). Frame: "I'm in late-stage with two other companies and want to make a thoughtful decision; can we extend to [date]?"
- Negotiate base + equity together, not separately. Equity-heavy offers from pre-IPO companies are not always better — discount by ~50% for liquidity risk.
- Comp benchmarking: levels.fyi for big tech, open-comp.org for startups, layoffstracker.com for layoff-affected reset pricing. Don't anchor your ask on your AWS L5 number — anchor on the band for the role you're targeting.

**Action:** Build `offer_decision.md` template with these columns before the first phone screen lands:

```markdown
| Company | Segment | Base | Equity (4yr) | Bonus | Sign-on | Window | Notes |
|---|---|---|---|---|---|---|---|
```

### H.5 — Project Deep-Dive Defense Rehearsal

Field guide identifies "project deep-dive" as one of three dominant interview formats (alongside coding + system design). Interviewers grill on: design decisions, what broke, what would you change, why this approach over alternative X. The bad-case journals across W2/W2.5/W2.7/W7/W8 are raw material; they need to be converted into defendable project narratives.

**Action:** For each major lab (W2, W7, W8, W9, plus the W12 capstone), write a `PROJECT_DEFENSE.md` containing:

```markdown
# {Lab name} — Project Defense Notes

## Three trade-offs I made and why
1. {trade-off}: {alternative I rejected and why}
2. ...
3. ...

## Three things that broke and how I diagnosed them
1. {symptom}: {root cause}: {fix} (cite Bad-Case Entry N)
2. ...
3. ...

## Three things I would change with more time
1. ...
2. ...
3. ...

## The one number I lead with
"{specific measured number that anchors the whole story}"
```

Rehearse one project deep-dive per week during W11 + W12 mocks. Record a 25-min mock per lab: 5 min architecture, 10 min defending decisions, 10 min "what would you change?"

### H.6 — Top 3 Actions This Week

If you only do three things from this appendix:

1. **Build `target_companies.md`** during W11 — 15 companies bucketed by segment, each with one resume-bullet → JD-keyword mapping (~90 min).
2. **Write `README-platform.md` for Capstone C** during W12 — alternate framing for AI-Support sub-track applications (~30 min).
3. **Pre-warm 4 references** within the first 30 days of starting the curriculum, not at offer stage (~3 hours total: 4 × 15-min calls + 4 × 30-min email follow-ups).

The technical depth from W0–W12 + W2.7 + W11.7 closes the *capability* gap. This appendix closes the *go-to-market* gap. Both are necessary; neither is sufficient.

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
| 2.5 | [[Week 2.5 - GraphRAG]] | Neo4j + Wikipedia subset; entity/relation extraction with local Gemma; 2-hop subgraph traversal; 25-Q multi-hop head-to-head vs Week 2 vector RAG; comparison matrix in `RESULTS.md`; v12 Wikidata QID linking closed entity-fragmentation ceiling |
| 2.7 | [[Week 2.7 - Structure-Aware RAG]] | PageIndex / tree-index RAG on Berkshire 2023 annual report (152 pages); 4-index architecture (LLM tree + K-means cluster + entity reverse-index + BGE-M3 hybrid page-vector fallback); agentic multi-iter loop with cluster pre-fetch + BUDGET EXHAUSTED 5-rule synthesis + chunk-level fallback; same-corpus three-way comparison vs vector + graph; per-Python-block bundle structure (mermaid → code → walkthrough → result → insight); GT-judge methodology (binary pass/fail against PDF-grounded `pass_criteria`) replaces entity-recall; Phase 9 ceiling = **16/16 = 1.000** (vector 0.500, graph 0.375 — graph DOES degenerate on single-document corpora under GT-judge; the May 7 "refuted" reading was an entity-recall artifact, see Phase 8 Block 1) |
| 3.5 | [[Week 3.5 - Cross-Session Memory]] | mem0 + Qdrant + SQLite dual-store; recall/remember REPL; 3-session demo proving cross-session recall; 15-Q recall benchmark with contradiction-update + multi-fact composition tests; production-comparator section reading `mathomhaus/guild` after lab completion |
| 3.5.5 | [[Week 3.5.5 - Multi-Agent Shared Memory]] | Install `mathomhaus/guild` (Go MCP server, single binary, embedded SQLite, BM25+dense+RRF retrieval); two parallel MCP clients (Claude Code + Cursor) sharing one substrate; atomic-claim scenario proving exactly-one-winner lock; 3-act cross-session handoff (A → B → C scroll chain); side-by-side W3.5-vs-guild comparison matrix; 15-Q multi-agent recall benchmark (same-agent + cross-agent + contradiction-during-parallel-work) |
| 3.5.8 | [[Week 3.5.8 - Two-Tier Memory Architecture]] | Two-tier capstone of the W3.5 cluster. Phase 1 spin up guild + EverCore. Phase 2 build `TieredMemory` Python wrapper (claim_task / complete_task / query_context / consolidate). Phase 3 consolidation pipeline (closed scrolls → EverCore imprints, idempotent + ordered). Phase 4 two-agent shared-knowledge demo (A in session 1 → consolidate → B in session 2 has cross-session context). Phase 5 four-way benchmark (no-mem / guild-only / EverCore-only / two-tier) + optional LongMemEval `oracle` subset. Biological analogy (hippocampus + neocortex + REM-sleep consolidation); Letta as the canonical production parallel. |
| 3.7 | [[Week 3.7 - Agentic RAG]] | Phase 1-4: LangChain official 5-node Agentic RAG notebook end-to-end + head-to-head vs Week 3 single-pass on 50-Q dev set + CRAG variant + decision tree (when help vs hurt). Phase 6: hand-rolled Self-RAG + CRAG baseline ported from `shaneliuyx/rag` to current stack (Qdrant + oMLX + `shared/rag_hybrid`). Phase 7: query decomposition with topological execution (DAG-based planning, IRCoT-style). Phase 8: FastMCP server wrapper exposing the lab as 3 tools (`rag_query`, `rag_status`, `rag_decompose`) consumable from Claude Desktop / Cursor — first MCP-server pattern in the curriculum |
| 4 | [[Week 4 - ReAct From Scratch]] | (1) 150-line `react.py` with no framework; (2) 4 local tools (search, repl, read_file, write_file); (3) SQLite trace logging; (4) 15+ bad-case scenarios with a before/after diff per patch; (5) `RESULTS.md` with failure-mode table |
| 5 | [[Week 5 - Pattern Zoo]] | 4 parallel implementations (ReAct, Plan-and-Solve, Reflexion, Orchestrator-Worker) on one task ("research + 1-page summary"); LLM-as-judge rubric scoring; cost/latency/quality 4-way comparison |
| 5.5 | [[Week 5.5 - Metacognition]] | Reflexion outer loop on top of W4 ReAct agent; Self-Consistency N=5 ablation; one bad-critic injection showing the overcorrection failure mode; episodic-memory replay across attempts |
| 6 | [[Week 6 - Claude Code Source Dive]] | Reading-only week. 8 subsystem study sheets filled in; one "Architecture Cheat Sheet" markdown that you can bring to interviews; 3 "what I would steal" design ideas |
| 6.5 | [[Week 6.5 - Hermes Agent Hands-On]] | Hermes Agent running locally; same canonical task in 3 agents (Claude Code / Pi / Hermes); observe one skill creation + audit one learned skill; 3×3 comparison matrix (extensibility / auditability / cost) |
| 6.7 | [[Week 6.7 - Authoring Agent Skills]] | Three production-quality skills authored end-to-end; SKILL.md + trigger pattern + verification step each; install globally + use for one week; description-field iteration log capturing trigger-tuning |
| 6.8 | [[Week 6.8 - Protocol Survey]] | Reading-heavy half-week (~3h). hello-agents Ch 10 + Anthropic MCP + Google A2A + open-spec ANP. 1-page Protocol-Survey ADR comparing transport, auth, interop, use cases. Annotate W3.5.5 guild for which protocol it implements + what would be needed for cross-host coordination. Optional A2A reference-impl 2-agent handshake. Service-mesh-primitive infra-bridge framing |
| 7 | [[Week 7 - Tool Harness]] | Generic `Tool`/`ToolHarness` classes; retry + timeout + budget + idempotency; 20-scenario bad-case suite; local (Qwen3.6) vs cloud (Claude Haiku) reliability comparison |
| 7.5 | [[Week 7.5 - Computer Use and Browser Agents]] | Same task three ways (Playwright / browser-use / Claude Computer Use); 10-task suite with one CSS-rename ablation; safety wrapper (action allowlist + budget cap + screenshot diff alarm) |
| 8 | [[Week 8 - Schema Reliability Bench]] | **The signature-question lab.** 5-way comparison (naive prompt / provider-native / Outlines+xgrammar / Instructor+retry / post-validation+repair) across 4 local models + GPT-4o-mini, 100 prompts; draws the 5-layer defense diagram |
| 8.5 | [[Week 8.5 - Voice AI Agents]] | Local cascaded pipeline (faster-whisper + Claude + ElevenLabs/Coqui); 20-turn latency measurement; OpenAI Realtime API head-to-head; barge-in handling implemented |
| 9 | [[Week 9 - Faithfulness Checker]] | Claim-splitter prompt; NLI-based entailment scorer; SelfCheckGPT-lite (3× sample + BERTScore); abstention router; 30-Q hand-labeled test set |
| 9.5 | [[Week 9.5 - Agentic RL Fine-Tuning]] | Pretrain → SFT (LoRA r=16, 200-500 CoT tuples on GSM8K-train) → GRPO (N=8 group-relative advantages, 8 epochs); 4-row ablation table (pretrain / SFT / GRPO / SFT+GRPO) on pass-rate + tokens + refusal-rate + wall-time + cost; optional tool-use extension swapping math reward for tool-reliability reward. Anchored to hello-agents Ch 11 |
| 10 | [[Week 10 - Framework Shootout]] | Re-implement Week 4 loop in LangGraph, LlamaIndex agent worker, OpenAI Agents SDK pointing at local mlx server; LOC + traceability + testability decision matrix |
| 11 | [[Week 11 - System Design]] | 5 × 2-hour whiteboard exercises (doc-QA / multi-agent triage / coding agent / financial-research / infra-aware); self-recorded; **7-point self-critique rubric** (Gate 7 = quotable cost-cut from a prior lab + named routing rule, the offer-closing senior signal) |
| 11.5 | [[Week 11.5 - Agent Security]] | 10-attack red-team suite extending W7 tool harness (5 attack classes + 3 indirect-injection variants); three defense layers (pydantic input validation / firejail sandbox / Llama Guard output filter); kill-rate-per-layer table |
| 11.7 | [[Week 11.7 - Take-Home Dress Rehearsal]] | 4-hour timed take-home rehearsal: small RAG with citations + RAGAS eval committed BEFORE main code (evals-first discipline visible in `git log`) + 5-min Loom defense screencast + RESULTS.md scored against the 30/30/25/15 take-home rubric; one quotable cost-cut number captured for W12 mock funnel |
| 12 | [[Week 12 - Capstone and Mocks]] | Pick capstone (A/B/C), polish to portfolio bar; 30 mock-interview recordings; 10 job applications submitted with 1 tailored number each; one mock = project deep-dive on the W11.7 take-home repo |

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
