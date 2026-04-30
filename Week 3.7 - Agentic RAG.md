---
title: "Week 3.7 — Agentic RAG (LangGraph-Canonical Architecture)"
created: 2026-04-27
tags: [agent, curriculum, week-3.7, rag, agentic-rag, langgraph, runbook, expansion-week]
companion_to: "Agent Development 3-Month Curriculum.md"
lab_dir: "~/code/agent-prep/lab-03.7-agentic-rag"
estimated_time: "6–8 hours over 2–3 sessions (expansion week — lighter than main weeks)"
prerequisites: "Weeks 1–3 complete (single-pass RAG baseline + RAGAS eval harness must exist); Week 5 ReAct loop helpful but not required"
---

# Week 3.7 — Agentic RAG (LangGraph-Canonical Architecture)

> Goal: Build the production successor to Week 3's single-pass RAG. Implement the canonical 5-node Agentic RAG graph (decide → retrieve → grade → rewrite → answer), measure the lift on ambiguous queries, and learn when the cost is worth it. Walk out with a published-vocabulary command of the field's named architectures (CRAG, Adaptive-RAG, GeAR) and the survey-paper taxonomy.

**Exit criteria.**
- [ ] LangChain's official `langgraph_agentic_rag.ipynb` notebook running end-to-end on your Week 1 corpus + Qdrant + BGE-M3
- [ ] Comparison harness measuring Week 3's single-pass RAG vs the 5-node Agentic RAG on the same 50-Q dev set
- [ ] Quantified lift on ambiguous queries specifically (faithfulness + context-recall delta)
- [ ] One CRAG (Corrective RAG) variant implemented with confidence-threshold + web-fallback
- [ ] `RESULTS.md` with comparison matrix + decision tree ("when does Agentic RAG help vs hurt?")
- [ ] You can name the 7 architectures from the Singh et al. survey + the 4 canonical papers (CRAG / Adaptive-RAG / GeAR / Agent-G) cold

---

## Why This Expansion Week Exists

Week 3 builds a single-pass RAG pipeline (dense retrieve → rerank → compress → synthesize) and measures it with RAGAS. That's the right baseline to learn first because every more-sophisticated pattern is *defined relative to it*. But single-pass is no longer the production default for any RAG system that needs to handle ambiguous queries or recover gracefully from bad retrieval.

The current production default — what every "Agentic RAG" tutorial, every LangChain doc, every 1.6k-star survey paper now describes — is a graph of agent nodes that **grade their own retrieval, rewrite their own queries when retrieval fails, and loop until they're confident or hit a budget**. Week 5 teaches the general orchestrator-worker / reflexion patterns; Week 3.7 teaches the specific specialization of those patterns to retrieval. **Agentic RAG is the bridge** between Week 3's RAG fundamentals and Week 5's agent patterns. Without this week, the curriculum has a gap where Reddit threads, LangChain docs, and survey papers all converge on "the obvious next thing" — and your interview answer for "tell me about RAG in production" stays stuck in 2024.

The week is **optional**: skip if your Q1 timeline is tight, revisit anytime in Q2 (per Appendix G's quarterly cadence map). It is **lighter than main weeks** — 6–8 hours rather than 12–15 — because most of the implementation reuses your Week 1–3 artifacts (corpus, Qdrant collection, dev set, RAGAS harness). What's new is the graph topology, the grading node, and the comparison.

---

## Architecture — The Canonical 5-Node Agentic RAG Graph

The reference architecture per [LangChain's official docs](https://docs.langchain.com/oss/python/langgraph/agentic-rag):

```mermaid
flowchart TD
    User([User Query]) --> Decide{"**generate_query_or_respond**<br/>LLM with retriever-tool access<br/>decides: retrieve or respond direct?"}

    Decide -->|"tool calls emitted"| Retrieve["**retrieve**<br/>execute retriever tool<br/>(BGE-M3 over Qdrant)"]
    Decide -->|"no tool needed"| Direct([Direct Response])

    Retrieve --> Grade{"**grade_documents**<br/>LLM judges relevance<br/>of retrieved chunks"}

    Grade -->|"relevant"| Generate["**generate_answer**<br/>synthesize from context<br/>+ enforce citations"]
    Grade -->|"irrelevant"| Rewrite["**rewrite_question**<br/>reformulate query<br/>(different keywords / angle)"]

    Rewrite -.->|"loop with new query"| Decide
    Generate --> Answer([Final Answer])

    subgraph Budget["Budget Discipline"]
        IterCount["max_iter cap<br/>(typically 3–5)"]
        IterCount -.->|"if exceeded"| Direct
    end

    Decide -.-> IterCount

    %% UML Activity polish — consolidated palette via classDef
    classDef decision fill:#fff,stroke:#1f4068,stroke-width:1.5px,color:#1f2937
    classDef activity fill:#eff6ff,stroke:#bfdbfe,stroke-width:1.5px,color:#111827
    classDef rewrite  fill:#fef2f2,stroke:#fecaca,stroke-width:1.5px,color:#7b2d26
    classDef terminal fill:#f0fdf4,stroke:#bbf7d0,stroke-width:1.5px,color:#1b4332

    class Decide,Grade decision
    class Retrieve,Generate activity
    class Rewrite rewrite
    class Direct,Answer terminal
```

**Reading the diagram:** the **two blue diamonds** are the agent decision points (decide-to-retrieve, grade-relevance) — these are what make it "agentic" rather than fixed-pipeline. The **red rewrite node** is the recovery path that single-pass RAG doesn't have. The **dashed iteration loop** is bounded by `max_iter` (the only thing standing between the agent and an infinite query-rewrite spiral). Compare this to your Week 3 baseline, which is purely linear: query → retrieve → rerank → compress → answer, with no grading, no loop, no recovery.

---

## Theory Primer (~45 min)

> Three concepts. Lighter than main-week primers because the lab itself is the teacher this week — running the canonical notebook teaches more than reading prose.

### Concept 1 — The Canonical 5-Node Architecture (LangChain's Production Default)

[LangChain's official Agentic RAG documentation](https://docs.langchain.com/oss/python/langgraph/agentic-rag) defines the production-canonical graph as exactly five nodes, each with a single responsibility. The shape is small enough to memorize, opinionated enough to be defensible in interviews:

1. **`generate_query_or_respond`** — first-line decision node. The LLM, given the user query and access to the retriever as a tool, decides whether retrieval is needed at all. For a query like "what's 2 + 2," it answers directly without retrieval. For "what does our refund policy say about international orders," it emits a tool call to the retriever. This is the node that prevents wasteful retrieval on unambiguously knowable answers.

2. **`retrieve`** — executes the retriever tool. Same dense+rerank stack from Weeks 1–2 (BGE-M3 over Qdrant + BGE-reranker). No agentic logic here; this is a pure tool execution node.

3. **`grade_documents`** — the relevance-grading node. Given the retrieved chunks and the original query, an LLM judges: are these documents actually relevant? Returns binary or graded. This is the **critical addition over single-pass RAG** — without grading, the agent has no signal that retrieval failed.

4. **`rewrite_question`** — the recovery path. When `grade_documents` says "no, these docs don't help," the rewriter reformulates the query (often using a different angle, broader keywords, or a HyDE-style hypothesized answer) and the graph loops back to `generate_query_or_respond`. Without this node, bad retrieval = bad answer; with it, bad retrieval triggers a recovery attempt.

5. **`generate_answer`** — the terminal synthesis node. Given the validated relevant context, produces the final answer with citations. Same shape as Week 3's synthesis stage, just gated by upstream relevance checking.

The implementation in LangGraph is a `StateGraph(MessagesState)` with conditional edges routed by `tools_condition` (whether the LLM emitted a tool call) and custom grading logic (whether documents pass relevance threshold). The whole graph fits in ~150 lines of Python — small enough that you'll read every node in Phase 1.

> **Interview soundbite:** "The canonical Agentic RAG architecture is five nodes — decide-to-retrieve, retrieve, grade, rewrite, answer — with a loop from rewrite back to decide. The two LLM-decision nodes are what make it agentic; the rewrite loop is what makes it production-grade. Compared to single-pass RAG, you get graceful recovery from bad retrieval at the cost of 2–4× latency and LLM calls."

---

### Concept 2 — The 7-Architecture Taxonomy (Singh et al. Feb 2025)

The [AgenticRAG-Survey](https://github.com/asinghcsu/AgenticRAG-Survey) paper (Aditi Singh, Abul Ehtesham, Saket Kumar, Tala Talaei Khoei, Feb 2025, 1.6k⭐) is the canonical taxonomy reference. It identifies **seven major architecture families**:

| # | Architecture | One-line description | When it wins |
|---|---|---|---|
| 1 | **Single-agent RAG** | The 5-node canonical (Concept 1 above) | Default for most production systems |
| 2 | **Multi-agent RAG** | Multiple specialist agents (researcher / synthesizer / critic) collaborating on retrieval | Genuinely complex queries needing role-specialized retrieval (e.g., legal + technical + financial sub-questions) |
| 3 | **Hierarchical agentic RAG** | Tree of agents — coordinator delegates to sub-coordinators which delegate to workers | Very large knowledge bases (>10M docs) where a single retriever scope is too broad |
| 4 | **Corrective agentic RAG (CRAG)** | Adds a confidence threshold — when retrieved docs score below threshold, falls back to web search or alternative source | Open-domain questions where local corpus may not have the answer |
| 5 | **Adaptive agentic RAG** | Dynamically picks retrieval strategy based on question complexity (no retrieval / single-step / multi-step) | Mixed query workloads — some simple, some complex, system shouldn't pay multi-step cost on simple |
| 6 | **Graph-based agentic RAG** | Combines GraphRAG (Week 2.5) with agent loop — agent traverses knowledge graph, decides next hop | Highly relational corpora (org charts, research citation networks, code dependencies) |
| 7 | **Agentic Document Workflows (ADW)** | Document-centric — agent processes individual documents through a multi-step workflow (extract → enrich → cross-reference → output) | Document-heavy workflows like contract review, research synthesis, regulatory filings |

**The three you must know cold for interviews:** single-agent (Concept 1, the default), CRAG (#4, the most-cited confidence-recovery pattern), Adaptive-RAG (#5, the most-cited efficiency-routing pattern). The other four are situational; name them as "see the Singh survey for the full taxonomy."

> **Interview soundbite:** "Agentic RAG isn't one architecture, it's seven — the Singh 2025 survey is the canonical taxonomy. The three you reach for most often are the single-agent canonical, Corrective RAG (CRAG) when local corpus may miss the answer, and Adaptive-RAG when query complexity varies enough that one-size-fits-all retrieval wastes compute on simple queries."

---

### Concept 3 — The Three Canonical Papers Worth Knowing by arXiv ID

Three named-paper architectures show up in the survey, in production tutorials, and in interviews — knowing them by arXiv ID and one-line claim is high-leverage interview signal.

**Corrective Retrieval Augmented Generation (CRAG) — [arXiv 2401.15884](https://arxiv.org/abs/2401.15884) (Yan et al. Jan 2024).** The thesis: dense retrieval is *brittle on out-of-distribution queries* — it returns results regardless of whether they're actually relevant, and downstream synthesis amplifies the brittleness. CRAG adds a *retrieval evaluator* (lightweight classifier scoring retrieved docs) that produces three buckets: Correct (use as-is), Incorrect (discard, fall back to web search), Ambiguous (combine local + web). The architectural addition is small (one classifier + one fallback path) but the impact on out-of-domain robustness is large. CRAG is the most-cited "make my RAG less wrong" paper of 2024–2025.

**Adaptive-RAG: Learning to Adapt through Question Complexity — [arXiv 2403.14403](https://arxiv.org/abs/2403.14403) (Jeong et al. Mar 2024).** The thesis: not every question deserves the same retrieval effort. A trained classifier routes queries to one of three strategies: (A) no retrieval — model knows the answer; (B) single-step retrieval — Week 3 baseline; (C) multi-step retrieval — full agentic loop. Saves significant compute on simple queries while preserving quality on complex ones. Adaptive-RAG is the canonical paper for "when you can't afford full Agentic RAG on every query."

**GeAR: Graph-enhanced Agent for Retrieval-augmented Generation — [arXiv 2412.18431](https://arxiv.org/abs/2412.18431) (Dec 2024).** The thesis: combining knowledge graph traversal with the agent loop produces stronger multi-hop reasoning than either alone. Maps directly onto Week 2.5's GraphRAG content but adds the agent decision-loop on top. GeAR is the most-cited "GraphRAG + agents" hybrid paper.

A fourth paper worth naming when asked about multi-agent RAG specifically: **Agent-G** (multi-agent framework for graph-augmented retrieval, exact arXiv ID varies by version). Less canonical than the three above but appears in survey citations.

> **Interview soundbite:** "The three canonical Agentic RAG papers I'd name are CRAG (arXiv 2401.15884) for confidence-aware retrieval with web fallback, Adaptive-RAG (arXiv 2403.14403) for complexity-based routing, and GeAR (arXiv 2412.18431) for graph-augmented multi-hop. Each names a specific failure mode of single-pass RAG and a specific architectural fix; together they're the 2024–2025 canon."

---

### Companion Texts

- **[LangChain official Agentic RAG docs](https://docs.langchain.com/oss/python/langgraph/agentic-rag)** — the canonical 5-node architecture; runnable example notebook linked from there
- **[asinghcsu/AgenticRAG-Survey](https://github.com/asinghcsu/AgenticRAG-Survey)** (Singh et al. Feb 2025, 1.6k⭐) — the 7-architecture taxonomy reference
- **[langgraph/examples/rag/langgraph_agentic_rag.ipynb](https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_agentic_rag.ipynb)** — official runnable notebook
- **[GiovanniPasq/agentic-rag-for-dummies](https://github.com/GiovanniPasq/agentic-rag-for-dummies)** — minimal LangGraph implementation, good study target if the official one feels too dense
- **[nicoladisabato/MultiAgenticRAG](https://github.com/nicoladisabato/MultiAgenticRAG)** — multi-agent variant for the curious
- **[jamwithai/production-agentic-rag-course](https://github.com/jamwithai/production-agentic-rag-course)** — full course material; useful for Phase 4 production-discipline grounding
- **CRAG paper — [arXiv 2401.15884](https://arxiv.org/abs/2401.15884)** — read sections 3–4 for the architecture, skim section 5 for benchmarks
- **Adaptive-RAG paper — [arXiv 2403.14403](https://arxiv.org/abs/2403.14403)** — section 3 for the complexity classifier, section 4 for the routing logic
- **Cross-curriculum**: revisit Week 3's RAGAS harness (you'll reuse it for the comparison) and Week 5's orchestrator-worker pattern (Agentic RAG is a specific application of it)

---

## Phase 1 — Run the LangChain Canonical Notebook (~1.5 hours)

### 1.1 Lab scaffold

```bash
mkdir -p ~/code/agent-prep/lab-03.7-agentic-rag
cd ~/code/agent-prep/lab-03.7-agentic-rag
mkdir -p src observations results data
git init
```

### 1.2 Install LangGraph + dependencies

Reuse your project venv from Week 0:

```bash
source ~/code/agent-prep/.venv/bin/activate
uv pip install -U langchain langgraph langchain-openai langchain-community langchain-qdrant
```

### 1.3 Clone the official example notebook

```bash
# Get just the one notebook + dependencies, not the whole langgraph repo
curl -sL https://raw.githubusercontent.com/langchain-ai/langgraph/main/examples/rag/langgraph_agentic_rag.ipynb -o langgraph_agentic_rag.ipynb

# OR skim GiovanniPasq's "for dummies" version if you want a smaller starting point:
git clone https://github.com/GiovanniPasq/agentic-rag-for-dummies.git
```

### 1.4 Adapt for local oMLX + your Week 1 Qdrant collection

The official notebook uses OpenAI by default — repoint to your local oMLX. Save as `src/01_canonical_agentic_rag.py`:

```python
"""LangChain canonical Agentic RAG, adapted to local oMLX + Week 1 Qdrant collection."""
import os
from langchain_openai import ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.tools import create_retriever_tool
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode, tools_condition

# Local oMLX endpoint (sonnet tier — Gemma 26B)
llm = ChatOpenAI(
    model=os.getenv("MODEL_SONNET", "gemma-4-26B-A4B-it-heretic-4bit"),
    base_url=os.getenv("OMLX_BASE_URL", "http://127.0.0.1:8000/v1"),
    api_key=os.getenv("OMLX_API_KEY", "Shane@7162"),
    temperature=0.0,
)

# Week 1 Qdrant collection (already populated with bge-m3 embeddings)
client = QdrantClient(url="http://127.0.0.1:6333")
# NOTE: vector store needs an embedding function compatible with what was indexed.
# Reuse your Week 1 BGE-M3 wrapper here.
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(
    model_name=os.path.expanduser("~/models/bge-m3"),
    model_kwargs={"device": "mps"},
)
vectorstore = QdrantVectorStore(
    client=client, collection_name="bge_m3_hnsw", embedding=embeddings,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
retriever_tool = create_retriever_tool(
    retriever, name="search_corpus", description="Search the corpus for documents relevant to the query."
)

# Build the 5-node graph
# (Following the LangChain official example structure; abridged here — see notebook for full nodes.)
# ... generate_query_or_respond, grade_documents, rewrite_question, generate_answer ...

graph = StateGraph(MessagesState)
# graph.add_node("generate_query_or_respond", ...)
# graph.add_node("retrieve", ToolNode([retriever_tool]))
# graph.add_node("grade_documents", ...)
# graph.add_node("rewrite_question", ...)
# graph.add_node("generate_answer", ...)
# (Wire up edges per the canonical diagram — see official notebook)
app = graph.compile()

# Smoke test
result = app.invoke({"messages": [("user", "Your test query here")]})
print(result["messages"][-1].content)
```

### Code walkthrough

**Chunk 1 — Local-first model wiring (lines 5-13):** Points the LangChain `ChatOpenAI` client at your oMLX endpoint instead of OpenAI. The `base_url` + `api_key` swap is the entire local adaptation — no other changes needed because oMLX exposes the same OpenAI-compatible API surface.

**Chunk 2 — Reuse Week 1 vectorstore (lines 16-30):** Critical detail — point `QdrantVectorStore` at the same `bge_m3_hnsw` collection you populated in Week 1. The `embeddings` argument must match the model used at indexing time (BGE-M3) for correct query-vector / doc-vector compatibility.

**Chunk 3 — `create_retriever_tool` (lines 31-34):** Wraps the retriever as a LangChain Tool. The `description` is what `generate_query_or_respond` reads when deciding whether to invoke retrieval — make it specific to your corpus, not generic ("Search the corpus" is too vague; "Search 10K MS MARCO passages on diverse topics" is what the LLM actually needs).

> **Why:** the description is part of the agent's prompt — vague descriptions cause the agent to over-invoke retrieval on questions it could answer directly, wasting time and tokens.

**Chunk 4 — Graph compilation (lines 36-44):** The full node implementations come from the official notebook (skipped here for brevity). The structure: `StateGraph(MessagesState)` for the type system, conditional edges via `tools_condition` for the decide-to-retrieve branch, custom edge function for the relevance-grading branch.

**Common modifications:** swap `MODEL_SONNET` for `MODEL_OPUS` (Qwen3.6-35B) for stronger grading on harder corpora; change `search_kwargs={"k": 5}` to `{"k": 10}` if your reranker is downstream.

### 1.5 Run the notebook + capture observations

Open `langgraph_agentic_rag.ipynb` in Jupyter or VS Code. Execute cells top-to-bottom. Run the example queries the notebook ships with first; then try **3 of your own queries** drawn from your Week 3 dev set:

1. **A simple factual query** — should route directly to `generate_answer` after one retrieve, no rewrite
2. **An ambiguous query** — should trigger at least one rewrite loop
3. **A query the corpus probably can't answer** — should hit the iteration cap

For each, capture in `observations/run-canonical.md`:
- How many graph iterations occurred (count the `rewrite_question` invocations)
- Final answer quality (subjective 1–5)
- Wall time vs your Week 3 single-pass baseline on the same query

---

## Phase 2 — Comparison Harness: Single-Pass vs Agentic (~2.5 hours)

### 2.1 Wire the comparison

Save as `src/02_comparison_harness.py`:

```python
"""Run the Week 3 single-pass pipeline AND the Week 3.7 Agentic pipeline on the same dev set.
Capture per-query: faithfulness, context_recall, latency, total LLM calls."""
import json, time
from pathlib import Path

# Import your Week 3 single-pass pipeline
from week3_pipeline import run_single_pass  # adapt path

# Import the canonical Agentic RAG graph from Phase 1
from canonical_agentic_rag import app as agentic_app

# Load Week 3 dev set
dev = [json.loads(l) for l in open("data/dev_set.jsonl")]

results = []
for q in dev:
    # Single-pass run
    t0 = time.time()
    sp_answer, sp_contexts = run_single_pass(q["question"])
    sp_latency = time.time() - t0
    sp_calls = 1  # single-pass = 1 LLM synthesis call (excluding grading)

    # Agentic run
    t0 = time.time()
    ag_result = agentic_app.invoke({"messages": [("user", q["question"])]})
    ag_latency = time.time() - t0
    ag_answer = ag_result["messages"][-1].content
    ag_calls = sum(1 for m in ag_result["messages"] if m.type == "ai")  # count AI message turns

    results.append({
        "qid": q["qid"], "question": q["question"], "ground_truth": q["short_answer"],
        "single_pass": {"answer": sp_answer, "latency": sp_latency, "llm_calls": sp_calls, "contexts": sp_contexts},
        "agentic": {"answer": ag_answer, "latency": ag_latency, "llm_calls": ag_calls},
    })

Path("results/comparison_raw.json").write_text(json.dumps(results, indent=2))
```

### Code walkthrough

**Chunk 1 — Pipeline imports (lines 1-9):** The harness imports both pipelines as black boxes. Keep the Week 3 single-pass module unchanged — modifying it would invalidate the comparison.

**Chunk 2 — Per-query timing + call-counting (lines 17-30):** The two metrics that matter for the comparison are **latency** (wall-clock cost) and **LLM call count** (compute cost). Single-pass has a fixed call count (1); agentic varies per query — that variance IS the data.

> **Why:** the agentic pipeline's promise is "I'll spend more compute on the queries that need it." If the call-count distribution doesn't match query difficulty, the pipeline isn't earning its complexity tax.

**Common modifications:** add a `temperature` field to compare quality vs determinism trade-off; capture which `grade_documents` decisions were made for later qualitative review.

### 2.2 Score with RAGAS

Reuse the RAGAS harness from Week 3 (`src/02b_ragas_eval.py`). Run it twice — once with `single_pass.answer` + `single_pass.contexts`, once with `agentic.answer` + (the agentic pipeline's final retrieved contexts). Compare faithfulness, answer_relevancy, context_precision, context_recall.

### 2.3 Stratify by query difficulty

The interesting comparison isn't "which pipeline wins on average" — it's "where does each one win?" Stratify the dev set into three buckets:

- **Easy** — single-pass answer matches ground truth exactly
- **Medium** — single-pass answer is partially correct
- **Hard / ambiguous** — single-pass answer is wrong or "insufficient context"

Run RAGAS on each bucket separately. The expected pattern: agentic and single-pass tie or single-pass wins on Easy (cheaper, equally good), agentic wins on Hard (the rewrite loop recovers what single-pass dropped).

---

## Phase 3 — Implement CRAG Variant (~1.5 hours)

The canonical Agentic RAG (Phase 1) handles the case where retrieved docs are irrelevant by rewriting the question. **CRAG handles the case where local corpus genuinely doesn't have the answer** by falling back to web search.

### 3.1 Add the CRAG node

Save as `src/03_crag_variant.py`:

```python
"""CRAG variant — adds confidence-threshold + web-fallback to the canonical 5-node graph."""
from typing import Literal
from langgraph.graph import StateGraph, MessagesState

def grade_with_confidence(state) -> dict:
    """Grade retrieved docs and return a confidence score (0.0–1.0).
    Three-bucket output: Correct (use), Incorrect (web fallback), Ambiguous (combine)."""
    # Use a small classifier or LLM-based judge
    # Simplest: prompt LLM with "rate relevance 0-1" then bucket
    ...

def web_fallback(state) -> dict:
    """Fall back to web search when local retrieval scores Incorrect."""
    from langchain_community.tools.tavily_search import TavilySearchResults
    # OR use Exa MCP if you wired it up in Week 0
    web_tool = TavilySearchResults(max_results=3)  # requires TAVILY_API_KEY
    # Or use built-in WebSearch
    ...

def combine_local_and_web(state) -> dict:
    """When confidence is Ambiguous, retrieve from both local + web and combine."""
    ...

# Build CRAG graph: same as canonical but add the three new nodes after grade_documents
graph = StateGraph(MessagesState)
# graph.add_node("grade_with_confidence", grade_with_confidence)
# Conditional edge from grade based on bucket:
#   Correct -> generate_answer
#   Incorrect -> web_fallback -> generate_answer
#   Ambiguous -> combine_local_and_web -> generate_answer
crag_app = graph.compile()
```

### 3.2 Run CRAG on out-of-corpus queries

Construct a 10-question test set of queries your local corpus *cannot* answer (current events, post-corpus-cutoff topics, niche entities not in MS MARCO). Run all three pipelines:

- Week 3 single-pass — should fail (no answer or wrong answer)
- Phase 1 canonical Agentic — should also fail (rewrites can't conjure data that isn't there)
- Phase 3 CRAG — should succeed via web fallback

Capture results in `observations/crag-out-of-corpus.md`. CRAG's lift here is the headline result of Phase 3.

---

## Phase 4 — When Does Agentic RAG Help vs Hurt? (~1.5 hours)

The honest engineering question this expansion week exists to answer. Read your Phase 2 + Phase 3 results carefully and write `observations/decision-tree.md`:

```markdown
## When to ship which RAG pipeline

### Ship single-pass (Week 3 baseline) when:
- Corpus is well-curated and queries are well-specified (e.g., enterprise doc Q&A with internal taxonomy)
- Latency budget is < 1s per query
- Cost per query matters and queries are high-volume
- You have RAGAS measuring single-pass at faithfulness ≥ 0.85

### Ship canonical Agentic RAG (Phase 1) when:
- Query distribution is mixed (some clear, some ambiguous)
- Latency budget allows 2–4× single-pass (typically 2–5 sec)
- Faithfulness on ambiguous queries dropped > 15pp in Phase 2 results
- Users care more about "answer quality even on hard questions" than "speed on easy ones"

### Ship CRAG (Phase 3) when:
- Corpus has known gaps and web fallback is acceptable (legal: probably not; consumer Q&A: yes)
- You can afford the web search latency (+1–3 sec per fallback)
- Users explicitly need answers to questions outside the local corpus
- You have a TOS-compatible web search backend wired up

### Ship Adaptive-RAG (read paper, don't implement here) when:
- Query distribution is HEAVILY skewed simple (>80% don't need agentic)
- Compute cost matters enough that running canonical Agentic on simple queries is wasteful
- You're willing to train a complexity classifier (or use LLM-as-classifier)
```

This decision tree IS the artifact of Phase 4. Bring it to interviews when asked "tell me about RAG architectures."

---

## Phase 5 — RESULTS.md and the Comparison Matrix (~1 hour)

Save as `results/RESULTS.md`. Required sections:

```markdown
# Lab 03.7 — Agentic RAG (LangGraph-Canonical Architecture)

**Date:** 2026-MM-DD
**Pipelines compared:** Week 3 single-pass (baseline) / Phase 1 canonical Agentic / Phase 3 CRAG variant
**Dev set:** Week 3's 50-Q dev set + 10-Q out-of-corpus extension

## 1. Three-Pipeline Comparison Matrix

| Metric | Single-pass | Canonical Agentic | CRAG |
|---|---|---|---|
| Faithfulness (full dev set) | x.xx | x.xx | x.xx |
| Faithfulness (Hard subset) | x.xx | x.xx | x.xx |
| Context_recall (Hard subset) | x.xx | x.xx | x.xx |
| Answer_relevancy | x.xx | x.xx | x.xx |
| Mean LLM calls/query | 1 | x.x | x.x |
| Mean latency p50 | x.x s | x.x s | x.x s |
| Mean latency p95 | x.x s | x.x s | x.x s |
| Out-of-corpus success | x/10 | x/10 | x/10 |

## 2. Quality lift on ambiguous queries

(2 paragraphs — what specifically did agentic recover that single-pass missed? Cite 2-3 example queries with side-by-side answers.)

## 3. Cost breakdown

(Mean LLM calls per query, mean wall-time, mean tokens. Show the cost multiplier vs single-pass clearly.)

## 4. Decision tree

(Copy from Phase 4 observations/decision-tree.md.)

## 5. What I learned that I did not expect

(Free-form 2-3 paragraphs.)

## 6. Bad-case journal

(One incident worth remembering — a query where agentic looped infinitely until iter cap, or a CRAG web fallback that surfaced wrong content, etc.)

## 7. Infra bridge

(Cloud infra mapping: the 5-node graph IS a state machine — cleanly maps to Argo Workflows, Step Functions, or Airflow's BranchPythonOperator. The grade-and-loop pattern IS the same as a CI pipeline's "test → fix → re-test" gate. The CRAG fallback IS the "circuit breaker pattern" from your platform-engineering background.)
```

---

## Lock-In (~45 min)

### Anki cards (5)

1. **Name the 5 nodes of the canonical Agentic RAG graph in order.**
   → generate_query_or_respond → retrieve → grade_documents → rewrite_question (loop) → generate_answer.

2. **What is CRAG and how does it differ from the canonical?**
   → Corrective RAG (Yan et al., arXiv 2401.15884). Adds a confidence-threshold on retrieval; when low-confidence, falls back to web search. Three buckets: Correct / Incorrect / Ambiguous.

3. **What is Adaptive-RAG and what problem does it solve?**
   → Adaptive-RAG (Jeong et al., arXiv 2403.14403). Classifier routes queries to no-retrieval / single-step / multi-step based on complexity. Solves the "wasting compute on simple queries" problem.

4. **The Singh 2025 survey identifies how many architecture families and what are the three you reach for most often?**
   → Seven (single-agent, multi-agent, hierarchical, corrective, adaptive, graph-based, ADW). Three you use most: single-agent canonical, CRAG, Adaptive-RAG.

5. **The two LLM-decision nodes that make Agentic RAG "agentic" are which?**
   → generate_query_or_respond (decide whether to retrieve) and grade_documents (decide whether retrieval succeeded). These are the two places the LLM's judgment routes the graph.

### Spoken interview questions (3)

1. *"Walk me through Agentic RAG. What does it add over the RAG you described before?"* (60-90 sec — name 5 nodes + the rewrite loop + the cost trade-off.)
2. *"When would you NOT use Agentic RAG?"* (Use the Phase 4 decision tree — single-pass wins on well-specified queries with tight latency budgets.)
3. *"What's CRAG, and what production problem made it necessary?"* (Out-of-corpus questions where local retrieval has nothing relevant — without a fallback, the agent loops forever rewriting an unanswerable query.)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `langgraph_agentic_rag.ipynb` cells fail with "model not found" | Default OpenAI model not pointing at oMLX | Set `OPENAI_BASE_URL` env var to `http://127.0.0.1:8000/v1` before launching Jupyter |
| Agent loops to max_iter on every query | `grade_documents` is too strict — labels everything irrelevant | Loosen the relevance threshold prompt; or switch grader from binary to graded score with threshold ≥ 0.6 |
| Faithfulness *worse* than single-pass | Rewriter is generating better-but-different queries that pull in unrelated docs | Constrain the rewriter prompt: "preserve the original intent; only change keywords/angle" |
| CRAG web fallback returns garbage | Web search backend rate-limited or wrong API key | Try Tavily, Exa MCP, or built-in WebSearch — each has different quality/cost trade-offs |
| LLM call count exploding (>10 per query) | No `max_iter` cap | Add `recursion_limit` to `app.invoke({"messages": ...}, {"recursion_limit": 8})` |
| Local oMLX times out on grading | Sonnet-tier model slow on grading prompts | Switch grader to haiku-tier (`gpt-oss-20b`) — grading is a classification task, not a synthesis task |

---

## What's Next

Open [[Week 4 - ReAct From Scratch]] when this lab's `RESULTS.md` is committed. The Agentic RAG graph you built here IS the ReAct loop specialized to retrieval — Week 4 will teach you to build the general ReAct loop from scratch, after which the LangGraph abstractions in this week will read as "the framework's opinion about what you just hand-built."

> **Saturday Trend-Tracking note (Appendix G).** When you start the post-Week-12 ritual, the Singh AgenticRAG-Survey repo is one of the eight weekly sources to skim for new architectures. The taxonomy is already at 7; if it grows to 8+, that's the signal that a new architecture has earned canonical naming. Apply the G.3 triangulation filter — named author + thesis + contradicts existing curriculum — to decide if it earns a Week 3.8 expansion.

— end —


---

## Interview Soundbites

**Soundbite 1.** Single-pass RAG is a linear pipeline — query, retrieve, synthesize, done. Agentic RAG wraps that in a two-decision-point loop: first the LLM decides whether retrieval is even needed; then a grading node decides whether what was retrieved is actually relevant. That second judgment is the key addition. The loop is worth the 2–4× latency cost when query intent is ambiguous or single retrieval predictably misses — in my comparison harness, the canonical 5-node graph recovered faithfulness on hard/ambiguous queries where single-pass dropped 15+ percentage points.

**Soundbite 2.** Query rewriting is the recovery path, not the happy path — fires only when `grade_documents` returns irrelevant. Two failure clusters: rewriter preserves wrong keywords and produces semantically shifted query that pulls in unrelated documents, corrupting context window on next pass (fix: constrain rewriter prompt to "change angle, not intent"). And: too-strict grading threshold means every retrieval fails, rewriter loops indefinitely, burns entire `max_iter` budget on a query the corpus could have answered — visible as LLM call count exploding past ten per query with no quality improvement.

**Soundbite 3.** Three-branch decision framework. Ship single-pass when corpus is well-curated, latency must be sub-1s, and RAGAS faithfulness already clears 0.85 on hard queries — the loop adds cost without lift. Ship canonical agentic RAG when query distribution is mixed and you can afford 2–5s; rewrite loop earns its cost on ambiguous queries. Add CRAG's confidence-threshold + web-fallback layer when local corpus has known gaps and open-domain fallback is acceptable. GraphRAG is a separate dimension: use when corpus is highly relational and multi-hop reasoning is the bottleneck.

---

## References

- **Yan et al. (2024).** *Corrective Retrieval Augmented Generation.* arXiv:2401.15884. Three-bucket confidence evaluator + web fallback.
- **Jeong et al. (2024).** *Adaptive-RAG.* arXiv:2403.14403. Lightweight classifier routing queries to no/single/multi-step retrieval.
- **Jiang et al. (2024).** *GeAR: Graph-enhanced Agent for RAG.* arXiv:2412.18431. KG traversal + agent decision loop.
- **AgenticRAG-Survey (2025).** GitHub: asinghcsu/AgenticRAG-Survey. Seven-architecture taxonomy.
- **Yao et al. (2023).** *ReAct.* arXiv:2210.03629. The general loop agentic RAG specializes.
- **Asai et al. (2023).** *Self-RAG.* arXiv:2310.11511. Inline reflection tokens as alternative to explicit grading node.
- **LangChain (2024-25).** Agentic RAG official docs: docs.langchain.com/oss/python/langgraph/agentic-rag.

---

## Cross-References

- **Builds on:** W2 Rerank (retrieve node reuses BGE-M3 + reranker stack), W3 RAG Eval (RAGAS reused for comparison matrix), W3 single-pass baseline.
- **Distinguish from:** Static RAG (single linear pass, no grading, no loop); GraphRAG (graph traversal is retrieval strategy not agent decision); hybrid retrieval (deterministic dense+sparse fusion, no agent judgment); Self-RAG (internalizes grading via reflection tokens vs explicit grading node).
- **Connects to:** W5 Pattern Zoo (5-node graph = ReAct specialized to retrieval); W7 Tool Harness (retriever wrapped via `create_retriever_tool` is tool-calling pattern; grading conditional edge is tool-result routing).
- **Foreshadows:** W11 System Design (5-node graph maps to Argo / Step Functions / Airflow BranchPythonOperator; CRAG fallback = circuit breaker pattern); W12 Capstone (default retrieval substrate for mixed-complexity queries).
