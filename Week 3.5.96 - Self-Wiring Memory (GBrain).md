---
title: "Week 3.5.96 — Self-Wiring Memory (GBrain — Garry Tan's Production Memory Layer for AI Agents)"
created: 2026-05-28
updated: 2026-06-08
status: SPEC + executable lab
tags:
  - agent
  - memory
  - gbrain
  - self-wiring
  - knowledge-graph
  - hybrid-search
  - rrf
  - postgres
  - markdown-first
audience: "cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles"
stack: "Python 3.11+, Postgres + pgvector, GBrain (MIT-licensed)"
prerequisites:
  - "[[Week 3.5.5 - Multi-Agent Shared Memory]] — multi-agent memory foundations"
  - "[[Week 3.5.8 - Two-Tier Memory Architecture]] — two-tier consolidation pattern"
  - "[[Week 3.5.9 - Requirement-Driven Memory Architecture]] — architecture-choice meta-skill (this chapter introduces a 4th class)"
estimated_time: "~5-7 hours"
---

## Exit Criteria

1. State the GBrain thesis in one sentence: zero-LLM-call entity-graph extraction via DETERMINISTIC Markdown parsing + typed-edge wiring; hybrid search (HNSW vector + Postgres keyword + Reciprocal Rank Fusion) lifts Recall@5 from 83% to 95% on a 240-page corpus.
2. Identify the 5 canonical typed edges GBrain extracts deterministically: `attended`, `works_at`, `invested_in`, `founded`, `advises`. Why these 5: they cover ~80% of person-company-event knowledge graphs without needing LLM disambiguation.
3. Explain why "zero LLM calls" matters at write time: deterministic extraction is reproducible + auditable + cheap; LLM-based extraction is non-deterministic + expensive + opaque. GBrain's choice mirrors W3.5.9's "atomic-fact write-time" thesis applied to graph extraction.
4. Install GBrain locally + ingest a 50-page Markdown corpus (mix of meeting notes, tweets, emails). Verify auto-wired graph: query for one entity, see its typed-edge connections.
5. Run 10 queries comparing keyword vs pure-vector vs RRF on the same corpus (at the *engine* layer — the CLI can't A/B them). Measure recall@3 + MRR. On a small, semantic-heavy corpus, expect **pure vector to win** and RRF to add nothing or slightly hurt — the published 83→95 RRF lift needs a larger, exact-term-heavy corpus (Phase 6).
6. Identify GBrain's place in the W3.5.x memory taxonomy: it's a 4th class (alongside W3.5.9's 1-tier atomic-fact, 2-tier consolidation, 3-tier graph). GBrain = markdown-first deterministic-graph; complements rather than replaces.
7. Defend "GBrain vs HyperMem" in interview answer: when is deterministic-Markdown the right substrate vs LLM-extracted hyperedges?

---

## 1. Why This Week Matters 

W3.5.9 introduced the three-class memory taxonomy (1-tier atomic-fact / 2-tier consolidation / 3-tier graph) + HyperMem L3 as the worked-example graph-tier implementation. GBrain — built by Garry Tan (Y Combinator CEO) to run his actual agents — introduces a **4th class: markdown-first, deterministic-extraction graph.** The thesis: most agent memory is ALREADY structured (people, companies, events, meetings), so Markdown can carry that structure natively and deterministic regex/parser passes extract typed edges with ZERO LLM calls — reproducible, auditable, cheap. Measured production impact: **83% → 95% Recall@5** via HNSW + Postgres-keyword RRF on a 240-page corpus; it powers Garry Tan's OpenClaw + Hermes at 146K-page scale, self-hostable on $5/mo Postgres.

But the chapter's real subject is **using GBrain as your agent's memory**, not admiring it from outside. We build a standalone agent (smolagents, *not* Claude Code) that wires GBrain's MCP tools — read raw → LLM-extract pages → `put_page` → `query` — under a **thin-agent / fat-tools** design: the transferable pattern for plugging *any* MCP-exposed memory system into *your* agent. Then we extend it where production actually bites. **(1) Large-volume ingest:** Phase 3's one-shot "concatenate every file into one prompt" hits a context wall and is un-resumable, so we stream **per file**, stage on disk, defer cross-file entity merge, and dual-checkpoint extraction + writes — each entity embedded exactly once, a crash resumes mid-corpus. **(2) Automatic search-policy selection:** GBrain ships fixed hybrid search, but **hybrid-RRF is not always the winner — it must be adjusted to the real case, not assumed.** Phase 6 shows the right arm (keyword / vector / hybrid) is *corpus-and-query-shape dependent*: RRF only helps when *both* arms are individually competitive; when one is weak on a corpus, fusion demotes the strong arm's hits and pure vector (or keyword) beats hybrid. That published 83→95 lift is corpus-specific, not a law — measured on our own data, RRF sometimes *loses* to a single arm. So we score the arms against a real golden question set, write the winner to a policy artifact, route the agent's queries through it, and re-evaluate on every ingest. Retrieval **self-tunes as the corpus drifts** (measured: the policy moves vector → hybrid when the brain grows from a 10-K to a mixed corpus).

Interview signal: engineers who can say "deterministic extraction beats LLM extraction when the structure is already known — *and* the retrieval strategy should be measured per corpus on real queries, never assumed" move 10× faster than those who reflexively LLM-extract everything and hard-code hybrid search.

---

## 2. Theory Primer

### 2.1 The deterministic-Markdown thesis

LLM-based entity extraction is the dominant 2024-2026 pattern: take unstructured text, run an LLM, get back structured entities + relationships. Works well; costs scale linearly with corpus size; results are non-deterministic (same input → different output across runs); audit trail is opaque.

GBrain's counter-thesis: when the data is ALREADY structured (meeting notes, calendar events, contact lists, tweets), Markdown can carry that structure natively. A meeting note `# Dinner with Alice 2026-05-12` parses deterministically into `(person: Alice, event: dinner, date: 2026-05-12)` without an LLM. Same for `@alice works at Anthropic` → `(alice, works_at, Anthropic)`. The grammar is regular; the extraction is reproducible; the audit trail is the parser code itself.

GBrain ships the parser for the 5 most common typed edges in person-company-event domains: `attended`, `works_at`, `invested_in`, `founded`, `advises`. Together these cover ~80% of operational knowledge-graph use cases (CRM-shaped, founder-network-shaped, advisor-shaped).

### 2.2 The hybrid-search-with-RRF lift

Single-modality retrieval has known weaknesses. Pure vector search (HNSW over dense embeddings) misses exact-term queries (acronyms, names, exact phrases). Pure keyword search (Postgres full-text) misses semantic-equivalent queries (synonyms, paraphrases). Reciprocal Rank Fusion combines both: each retriever produces a ranked list; fused score = `1/(rank + k)` summed across retrievers; higher fused score → better candidate.

GBrain measures the impact: on a 240-page corpus, Recall@5 = 83% with vector alone vs 95% with RRF (vector + keyword). +12pt absolute improvement. +30 more correct answers in top-5 across the eval set. The lift is mostly on queries containing proper nouns / exact phrases that pure-vector underweights.

This is the W3.5.8 §6.x hybrid-search pattern applied at the production-memory layer.

### 2.3 The synthesis layer — citations + "what we don't know"

GBrain doesn't just return ranked passages; it SYNTHESIZES answers with explicit citations. Example output:

```
Q: Who did Alice meet with in May 2026?
A: Alice met with Bob (meeting note, 2026-05-03) and Carol
   (calendar event, 2026-05-12). I don't have visibility into
   meetings outside Alice's tracked corpus — checking other
   sources may surface additional meetings.
```

The "what brain doesn't know yet" framing is load-bearing: agents that always answer confidently are worse than agents that flag knowledge gaps. GBrain's synthesis layer surfaces gaps as first-class output.

### 2.4 Place in the W3.5.x memory taxonomy — 4th class

W3.5.9's three classes:
- **Class 1 — One-tier atomic-fact** (Mem0, ChatGPT memory): per-message fact extraction → vector store
- **Class 2 — Two-tier consolidation** (Letta, EverCore): operational tier + episodic-extraction tier
- **Class 3 — Graph-tier temporal** (Graphiti, Zep): per-message typed-edge extraction → temporal graph

GBrain adds:
- **Class 4 — Markdown-first deterministic-graph**: structured Markdown → deterministic parser → typed-edge graph + HNSW + keyword + RRF. Zero LLM calls at write time.

When to use Class 4 vs Class 3 graph-tier:
- **Class 4 wins** when the corpus is already structured (your own meeting notes, internal docs, calendar). Cheap, reproducible, auditable.
- **Class 3 wins** when the corpus is UNSTRUCTURED (raw conversations, scraped web pages, free-form chat logs). LLM extraction is required to derive structure.

Many production systems use BOTH: GBrain for the structured operational data + HyperMem-class for the unstructured conversational data.

### 2.5 Production scale — Garry Tan's deployment

GBrain at production scale (per the project page):
- **146,646 pages** ingested
- **24,585 people** entities
- **5,339 companies** entities
- **66 autonomous cron jobs** running against the graph
- **74 MCP tools** exposed for agent access

This is a Y Combinator CEO's actual operational memory layer; not a research demo. Worth reading the project's commit history to see how it evolves with real usage.

### 2.6 Distinguish-from box

**GBrain vs Mem0** — Mem0 is 1-tier atomic-fact with LLM extraction. GBrain is graph with deterministic extraction. Different substrates, different cost profiles.

**GBrain vs HyperMem (W3.5.9 Phase 6-9)** — HyperMem extracts hyperedges from arbitrary text via LLM. GBrain extracts typed edges from Markdown via regex. HyperMem is more flexible; GBrain is more reproducible.

**GBrain vs Notion / Obsidian** — Notion / Obsidian are markdown-first PIM tools without the agent-memory layer. GBrain is the agent-memory layer ON TOP of markdown — adds typed-edge auto-wiring + HNSW + RRF + MCP tools + synthesis.

**GBrain vs Graphiti / Zep** — Graphiti / Zep are LLM-extracted temporal graphs. GBrain is deterministic-extracted Markdown graph. Complementary; pick by data shape.

### 2.7 Papers + references — pointer list

- **GBrain (Garry Tan / Y Combinator, 2025-2026).** https://gbrain.homes/. MIT-licensed.
- **MarkTechPost tutorial (May 2026).** Step-by-step coding tutorial.
- **Hermes Atlas project page.** https://hermesatlas.com/projects/garrytan/gbrain.
- **PyShine GBrain article.** Self-wiring knowledge graph explainer.
- **Reciprocal Rank Fusion (Cormack et al. 2009).** SIGIR 2009. The foundational RRF paper.

---

## 3. System Architecture 

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  WR[Markdown write<br/>meeting note / tweet / email] --> PARSE[Deterministic parser<br/>extract entities + typed edges<br/>ZERO LLM calls]
  PARSE --> PG[Postgres<br/>pages + entities + edges tables]
  PARSE --> VEC[HNSW vector index<br/>via pgvector]
  Q[Query] --> H[Hybrid search]
  H -->|vector| VEC
  H -->|keyword| PG
  VEC --> RRF[Reciprocal Rank Fusion]
  PG --> RRF
  RRF --> SYN[Synthesis layer<br/>answer + citations<br/>+ what-we-don't-know]
  SYN --> A[Agent reads via MCP<br/>74 tools exposed]
```

> **Markdown is the write-time substrate, not the run-time memory store.** Write
> path: Markdown → deterministic parser → **Postgres** (`pages`/`entities`/`edges`
> tables + a pgvector HNSW embedding column). The query path is **entirely
> Postgres** — vector (HNSW) and keyword (tsvector FTS) fused by RRF; retrieval
> never re-parses the `.md` files. So Markdown is the auditable, diff-friendly,
> human-editable *source of truth*; once embedded, **PG serves all query-time
> recall**. "Markdown-first" describes the write contract (deterministic,
> zero-LLM extraction), not the retrieval engine — that's pgvector + tsvector.

### 3.1 The end-to-end pipeline — corpus ingest to query

§3 is the *engine's* write/read shape. This subsection is the **operational lifecycle you actually run in production**: how a raw corpus becomes a queryable, self-tuning brain, and how every Lab Phase below slots into one pipeline. Read this once and the rest of the chapter is "here is each box in detail." There are four stages and one feedback loop; the same two entrypoints (`ingest_agent.py` for small corpora, `resumable_ingest.py` at scale) run all of stages 1-3 in `main()`, and `query_policy.ts` is stage 4.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  SRC[Corpus<br/>~/brain/sources/*<br/>ground truth]
  subgraph ING["1 - Resumable Ingest"]
    EX[Per-file/chunk extract<br/>driver-side LLM]
    ST[Disk stage<br/>.ingest_stage]
    MG[merge_from_disk<br/>dedup across files]
    WR[put_page over MCP<br/>embed ONCE]
    EX --> ST --> MG --> WR
  end
  RC[2 - reconcile_graph<br/>extract links --source db<br/>0-LLM · wikilinks to edges]
  DEC{golden_eval.json<br/>exists?}
  PE[policy_eval.ts<br/>score 3 arms · real Qs<br/>discounted grounding@C]
  AE[auto_eval.ts<br/>cold-start known-item proxy]
  POL[(search_policy.json<br/>winning arm + rrf_k)]
  subgraph QRY["4 - Query Apply"]
    QP[query_policy.ts<br/>read policy]
    SW{QUERY_ROUTER?}
    GA[global arm<br/>keyword / vector / hybrid]
    RT[per-query route<br/>+ entity-aware<br/>one-hop assembly]
    QP --> SW
    SW -->|off · default| GA
    SW -->|on · accuracy switch| RT
  end
  ANS[Answer + citations<br/>+ what-we-don't-know]
  SRC --> EX
  WR --> RC
  RC -->|"3 - run_auto_eval()<br/>every ingest"| DEC
  DEC -->|yes · current| PE
  DEC -->|no · cold start| AE
  PE --> POL
  AE --> POL
  POL --> QP
  GA --> ANS
  RT --> ANS
```
*The production lifecycle. Stages 1-3 run inside one `main()` (small: `ingest_agent.py`; large: `resumable_ingest.py`); stage 4 is `query_policy.ts`. The loop: every ingest re-runs `run_auto_eval()`, which re-selects the search arm against the current corpus and rewrites `search_policy.json` - so retrieval self-tunes as the corpus drifts, with no human in the loop.*

**Stage 1 - Resumable ingest (large-volume capability).** Raw files stream through a **per-file, per-chunk** extractor that runs *driver-side* (outside the agent's 30 s sandbox), stages results on **disk** (never embedded), merges duplicate entities across files once, then writes only the **canonical** pages to GBrain over MCP - so each entity is **embedded exactly once**. Three on-disk checkpoints (stage / merge / write, the last *verify-then-mark*) make a crash mid-corpus resume rather than restart. Measured at scale: embedding calls dropped **65 → 18** with `staging_in_db = 0`, and a killed run re-embedded **nothing** on resume. Small corpora use the one-shot `ingest_agent.py`; the same lifecycle, just without the streaming machinery. **(Phase 3 small-corpus, Phase 8 scale.)**

**Stage 2 - Reconcile (`reconcile_graph()`).** A deterministic, **zero-LLM** `gbrain extract links --source db` pass materializes the `[[wikilinks]]` the extractor wrote into typed graph edges. It must run *after* all writes and *before* any query, because `put_page` over MCP is a remote caller (GBrain skips inline auto-link) and forward references only resolve once the whole corpus exists. **(Phase 4.)**

**Stage 3 - Auto-eval + policy selection (`run_auto_eval()`, the self-tuning hook).** Immediately after reconcile, `main()` calls `run_auto_eval()` - the keystone that makes retrieval adaptive instead of a hard-coded `hybrid`. It branches on whether a **real** golden set exists:

- **`data/golden_eval.json` exists → `policy_eval.ts`** (the trustworthy source): scores all three arms - keyword, vector, hybrid-RRF - on the *real* question set using **discounted grounding@C** (substring coverage × a rank/budget discount over the production injected-chunk count `C`), a **0-LLM** deterministic metric. It writes the winning arm + `rrf_k` to `results/search_policy.json`.
- **No golden set yet → `auto_eval.ts`** (cold-start fallback): a known-item proxy that auto-generates qrels so a brand-new brain still gets a defensible policy on day one. It is a regression guardrail, not the oracle (Bad-Case Entry 20).

`run_auto_eval()` is **best-effort**: any failure returns a string instead of raising, so a broken eval never breaks an ingest (disable entirely with `AUTO_EVAL=0`). Because it re-runs on **every ingest**, the policy is re-selected against the *current* corpus each time - this is what flipped the measured policy **vector → hybrid** when a 10-K landed on the entity brain. **(Phase 6 benchmark, Phase 9 policy loop.)**

**Stage 4 - Query apply + the accuracy switch (`query_policy.ts`).** At read time the agent calls `query_with_policy()` → `query_policy.ts`, which reads `search_policy.json` and routes accordingly - **not** a hard-coded hybrid. Two modes:

- **`QUERY_ROUTER` off (default):** every query uses the single **global arm** the selector chose (`keyword` | `vector` | `hybrid`).
- **`QUERY_ROUTER=on` (the accuracy switch):** classify each query's shape and route *per-query* (`kw → keyword`, `vec → vector`, `mixed → hybrid`), plus **entity-aware one-hop graph expansion** that pulls in directly-linked pages. This is the extra switch you flip to buy accuracy on a mixed corpus where one global arm leaves recall on the table. **(Phase 9 Blocks C/E.)**

**Why the loop is cheap (the cost model that makes self-tuning affordable).** The selector in stage 3 runs on *every* ingest - the hot loop - and it is **0-LLM** (deterministic grounding, no model call). The tempting alternative, an LLM answer-judge per arm per question per ingest, is wrong three ways: cost (a single uncapped answer-eval measured ~1.5 M tokens), latency (ingest blocks on dozens of generate-then-judge round-trips), and confounding (judging *retrieval* by *answer* quality lets the policy flip on generation noise). The expensive LLM judge is reserved for **event-triggered** checks only - a GATE when the policy *flips*, a CALIBRATOR on a domain shift. What licenses the cheap proxy is the measured correlation **`r = +0.820`** between discounted grounding and the answer-judge: cheap-and-continuous in the hot path, expensive-and-rare on the edges. **(Phase 9 Block D.)**

> [!tip] One-paragraph mental model
> **Ingest streams and stages so it scales and resumes; reconcile wires the graph for free; auto-eval measures the corpus on real questions for free and writes the winning search arm; query reads that policy and (optionally) routes per-query for extra accuracy.** Large volume comes from stage 1's disk-staging + embed-once + checkpoints; low-cost self-tuning comes from stage 3's 0-LLM selector run every ingest; accuracy-on-demand comes from stage 4's `QUERY_ROUTER` switch. Everything below is one of these four boxes in full.

---

## 4. Lab Phases

> **Executed vs spec (this records only what was actually run).** Phases marked
> **[executed]** were run and measured on this machine; **[spec — not yet run]**
> phases are specified but not executed. The real flow we ran: **install (P1) → drop
> raw files in `sources/` (P2) → a standalone smolagents agent converts raw→pages
> over MCP (P3) → verify the wired graph (P4)**. The earlier Claude-Code-driven
> ingestion path (scaffold skills + `claude mcp add` + trigger) was **dropped** in
> favor of that standalone agent — so Phase 2 below is just corpus prep, and the
> conversion lives in Phase 3.

### Phase 1 — Install GBrain + provision Postgres [executed]

> **Engine choice.** GBrain ships two storage engines (`docs/ENGINES.md`): **PGLite**
> (embedded Postgres via WASM, the zero-config default — `gbrain init`, no server) and
> **Postgres + pgvector** (the scale path). This lab uses the **Postgres engine** so you
> exercise the production wiring; the DB runs in a throwaway Docker container.
> Note GBrain is a **Bun + TypeScript** CLI (not Python), and its embeddings are
> **hosted** (ZeroEntropy default, or OpenAI/Voyage) — not local MLX. Without an
> embedding key, keyword search still works.

```bash
# 1) Bun runtime (GBrain is a Bun + TypeScript CLI — no Python/uv/pip)
curl -fsSL https://bun.sh/install | bash
export PATH="$HOME/.bun/bin:$PATH"

# 2) Postgres + pgvector via Docker. OrbStack supplies the Docker engine on macOS
#    (`brew install orbstack`, then the standard `docker` CLI — no Docker Desktop).
docker run -d --name gbrain-pg \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=gbrain \
  -p 5432:5432 \
  pgvector/pgvector:pg16            # the same image GBrain's own CI uses; ships pgvector
# wait until it accepts connections, then ensure the extension (init also creates it)
until docker exec gbrain-pg pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
docker exec gbrain-pg psql -U postgres -d gbrain -c "CREATE EXTENSION IF NOT EXISTS vector;"
# teardown:  docker rm -f gbrain-pg   (data is ephemeral — re-run to reset)

# 3) Install GBrain. Deterministic clone path (robust for a lab; the README's
#    `bun install -g github:garrytan/gbrain` also works — see INSTALL_FOR_AGENTS.md).
cd ~/code/agent-prep
git clone https://github.com/garrytan/gbrain.git
cd gbrain && bun install && bun link    # `gbrain` now on PATH

# 4) Create the schema against the Docker Postgres (the .env from step 4-detail
#    is auto-loaded by Bun). --url = self-hosted Postgres; NOT --supabase (that
#    runs the interactive Supabase pooler flow). Embedding model is fixed AT init.
gbrain init --url "postgresql://postgres:postgres@localhost:5432/gbrain" \
  --embedding-model ollama:nomicai-modernbert-embed-base-bf16   # oMLX via the ollama provider (probes dim; no --embedding-dimensions)

# 5) (optional) chat/query-expansion via VibeProxy — add AFTER init. Do NOT set
#    OPENROUTER_API_KEY before init, or init auto-picks openrouter for embeddings.
```

**Verification:** `gbrain doctor` — all checks pass (engine reachable, schema migrated, embedding provider resolved).

#### Detailed walkthrough

Each step below = command + what it does + how to confirm + the gotcha that bites. Canonical sources in the repo: `INSTALL_FOR_AGENTS.md` (9-step), `docs/ENGINES.md`, `docs/GBRAIN_VERIFY.md`.

**1. Bun runtime.** GBrain's `package.json` declares `engines: { bun: ">=1.3.10" }` and `bin: { gbrain: "src/cli.ts" }` — it runs on Bun, not Node, not Python.

```bash
curl -fsSL https://bun.sh/install | bash
export PATH="$HOME/.bun/bin:$PATH"      # add to ~/.zshrc so it survives new shells
bun --version                           # must be ≥ 1.3.10
```

> **Gotcha:** if `bun` or later `gbrain` is "command not found," the PATH export didn't reach your profile — restart the shell or append the export to `~/.zshrc`.

**2. Postgres + pgvector container (OrbStack).** OrbStack is a lightweight Docker-engine replacement for macOS; once it's running the commands are plain `docker`.

```bash
brew install orbstack                    # one-time; starts the Docker engine
docker run -d --name gbrain-pg \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=gbrain \
  -p 5432:5432 \
  -v gbrain-pgdata:/var/lib/postgresql/data \   # named volume → survives restarts
  pgvector/pgvector:pg16
until docker exec gbrain-pg pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
docker exec gbrain-pg psql -U postgres -d gbrain -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

> **Gotcha (port conflict):** GBrain's own CI deliberately maps Postgres to ports 5434–5437 because 5432/5433 are "manual / sibling-project" ports that often clash. If `docker run` fails with "port already allocated," map a free host port (`-p 5433:5432`) and put that port in the `GBRAIN_DATABASE_URL` below.
> **Gotcha (readiness):** `docker run -d` returns when the container *starts*, not when Postgres *accepts connections* — the `until pg_isready` loop is what stops the next command racing the DB boot. Without it, `CREATE EXTENSION` fails intermittently.
> **Persistence:** the `-v gbrain-pgdata:` named volume keeps data across `docker restart`. Drop it for a pure throwaway; full reset is `docker rm -f gbrain-pg && docker volume rm gbrain-pgdata`.

**3. Install the GBrain CLI.** The deterministic clone path is the most robust for a lab; the README's `bun install -g github:garrytan/gbrain` is the one-liner alternative.

```bash
cd ~/code/agent-prep
git clone https://github.com/garrytan/gbrain.git
cd gbrain && bun install && bun link     # symlinks `gbrain` into ~/.bun/bin
export PATH="$HOME/.bun/bin:$PATH"        # ensure that dir is on PATH (persist in ~/.zshrc)
gbrain --version                         # prints a version (e.g. 0.42.x)
```

> **Gotcha (`gbrain: command not found`):** `bun link` registers the package and symlinks the CLI into `~/.bun/bin` (`~/.bun/bin/gbrain → …/src/cli.ts`) — it does **not** add that dir to PATH. The Bun installer often doesn't write the PATH line to `~/.zshrc` either, so a *new shell* loses it. Fix: `echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc` (this is step 1's export — make it permanent). Quick check: `ls ~/.bun/bin/gbrain` exists ⇒ it's purely PATH. Or just run it directly: `bun run src/cli.ts <args>` from the repo.
> **Gotcha (#218):** Bun occasionally blocks the global-install postinstall hook, so schema migrations don't auto-run and `gbrain doctor` reports `schema_version: 0`. Fix: `gbrain apply-migrations --yes`. The deterministic clone+`bun link` path above avoids it.

**4. Configure via `.env`, then create the schema.** GBrain runs on Bun, which **auto-loads `.env`** from the working directory — so put settings in a file instead of `export`-ing each shell (the repo ships `.env.testing.example` as precedent). The `PostgresEngine` reads `GBRAIN_DATABASE_URL` (pooler override: `GBRAIN_DIRECT_DATABASE_URL`).

##### The `.env` file (copy-paste)

Create `~/code/agent-prep/gbrain/.env` with the block below, then fill the two `<…>` placeholders. **Required** = the lab won't run without it; **optional** = enables vector/hybrid search and query expansion (skip and you still get keyword search). `.env` holds secrets — it's already in GBrain's `.gitignore`; never commit it.

```bash
cat > ~/code/agent-prep/gbrain/.env <<'EOF'
# ─── REQUIRED ────────────────────────────────────────────────────────────────
# Postgres engine = the Docker container from step 2
GBRAIN_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gbrain

# ─── EMBEDDINGS (required for vector/hybrid search; pick ONE provider) ────────
# Default: oMLX (local, OpenAI-compatible) via the `ollama` PROVIDER. Use ollama,
# NOT llama-server: the ollama provider PROBES the endpoint for the vector dim, so
# it sidesteps the llama-server catch-22 (see BCJ). oMLX is OpenAI-compatible at :8000.
OLLAMA_BASE_URL=http://localhost:8000/v1           # oMLX endpoint (note: the ollama PROVIDER, pointed at oMLX)
OLLAMA_API_KEY=<your-oMLX-key>                     # oMLX needs a real key
#   alt — real ollama daemon:     OLLAMA_BASE_URL=http://localhost:11434/v1  (+ ollama pull <model>)
#   alt — hosted OpenAI:          OPENAI_API_KEY=sk-...
#   alt — hosted ZeroEntropy:     ZEROENTROPY_API_KEY=ze-...

# ─── CHAT / QUERY EXPANSION (optional; add AFTER init) ───────────────────────
# VibeProxy = OpenAI-compatible proxy → Haiku, for chat/query-expansion ONLY
# (it canNOT embed — Anthropic has no /v1/embeddings). KEEP THESE COMMENTED during
# `gbrain init`: a present OPENROUTER_API_KEY makes init auto-pick openrouter for
# EMBEDDINGS too, silently overriding your local oMLX choice. Uncomment post-init.
# OPENROUTER_API_KEY=dummy                          # VibeProxy ignores it; any non-empty value
# OPENROUTER_BASE_URL=http://localhost:8317/v1      # VibeProxy port
#   alt — direct Anthropic:       ANTHROPIC_API_KEY=sk-ant-...

# ─── OPTIONAL OVERRIDES ──────────────────────────────────────────────────────
# GBRAIN_DIRECT_DATABASE_URL=postgresql://...       # bypass a pooler for DDL/bulk
EOF
```

Init the Postgres engine, **fixing the embedding model at init time** (it can't be changed later — step 5):

```bash
gbrain init --url "postgresql://postgres:postgres@localhost:5432/gbrain" \
  --embedding-model ollama:nomicai-modernbert-embed-base-bf16
# EMBEDDINGS: use the `ollama` PROVIDER pointed at oMLX (OLLAMA_BASE_URL in .env).
# It PROBES the endpoint for the vector dim → NO --embedding-dimensions, and it
# avoids the llama-server catch-22 (BCJ Entry below). Swap in your own oMLX embed
# model id (here: a 768-d nomic/ModernBERT). On success init prints
# "Embedding: ollama:<model> (768d)".
# `--url <conn>` = manual/self-hosted Postgres (our Docker container); it runs the
# DDL (pgvector ext, pg_trgm, tables, triggers, HNSW index) + applies a search mode.
# The OTHER engine flags: --supabase (interactive Supabase), --pglite (embedded PGLite).
gbrain providers test --model ollama:nomicai-modernbert-embed-base-bf16   # smoke-test oMLX
```

> **Gotcha (`--supabase` prompts for a URL / embeddings went to openrouter):** two traps bit the first run. (1) `--supabase` runs the **interactive Supabase flow** and ignores `GBRAIN_DATABASE_URL` — use `--url <conn>` for a self-hosted container. (2) If `OPENROUTER_API_KEY` is set in `.env`, `gbrain init` **auto-picks openrouter for embeddings** ("Detected OPENROUTER_API_KEY … Using openrouter:…"), overriding your local oMLX intent — keep it commented until after init, and always pass `--embedding-model` explicitly (it wins over auto-detect).
> **Gotcha (re-init refuses with the OLD dimensions):** if a first init picked the wrong embedder (e.g. openrouter 1536d), the model + dim are persisted in `~/.gbrain/config.json` **and** baked into the schema's vector column. Re-running init then fails with `model "bge-m3" does not support custom dimensions 1536` — the `1536` is the *stale* value, not your command. With 0 pages, reset cleanly before retrying:
> ```bash
> docker exec gbrain-pg psql -U postgres -c "DROP DATABASE gbrain;"
> docker exec gbrain-pg psql -U postgres -c "CREATE DATABASE gbrain;"
> docker exec gbrain-pg psql -U postgres -d gbrain -c "CREATE EXTENSION IF NOT EXISTS vector;"
> rm -f ~/.gbrain/config.json
> ```
> Then re-run `gbrain init --url … --embedding-model ollama:<oMLX-model>` against the fresh DB.

**5. Providers — the local-first / VibeProxy split.** GBrain uses providers for two *different* jobs that proxy differently:

- **Embeddings** need an embedding-capable endpoint. **VibeProxy can NOT serve these** — it proxies to Claude/Haiku, and Anthropic has no `/v1/embeddings`. Use a real embedder:
  - **Local (recommended, $0 — the W3.5.9 "embeddings stay local" pattern):** point GBrain's **`ollama` provider** at **oMLX** (OpenAI-compatible) — `OLLAMA_BASE_URL=http://localhost:8000/v1` + `OLLAMA_API_KEY`, then `--embedding-model ollama:<oMLX-model>` with **no `--embedding-dimensions`** (the ollama provider PROBES the endpoint for the vector dim). oMLX must expose `/v1/embeddings` with an embedding model loaded; on success init prints `Embedding: ollama:<model> (Nd)`. **Do NOT use the `llama-server` provider here:** it's "user-driven" and hits a catch-22 — it *requires* `--embedding-dimensions` yet *rejects* it for any model GBrain's registry recognizes (bge-m3, nomic/modernbert), so init is impossible (BCJ Entry 1). The `ollama` provider sidesteps it by probing. Real-ollama-daemon alternative: `ollama pull nomic-embed-text` + `--embedding-model ollama:nomic-embed-text`. Smoke-test: `gbrain providers test --model ollama:<model>`.
  - **Hosted:** `openai:text-embedding-3-small` (1536d) or ZeroEntropy — match `--embedding-dimensions`.
  - **Gotcha:** the embedding model is baked into the vector-column width, so `gbrain config set embedding_model` is **refused**. Choose it at `init`; change later only via `gbrain reinit-pglite …` (PGLite) or `docs/embedding-migrations.md` (Postgres).
- **Chat / query expansion** (optional, sharpens search): **VibeProxy works here** — it's OpenAI-compatible. Route it through the `openrouter` provider, explicitly designed to "point at a self-hosted OR-compatible proxy": `OPENROUTER_BASE_URL=http://localhost:8317/v1` (in the `.env` above) + an `openrouter:<model>` chat model.

> **So "can VibeProxy replace OpenAI?" — half.** Yes for the chat/LLM calls; no for embeddings (Anthropic has no embedding endpoint). Keep embeddings on a local embedder (oMLX/ollama). With no embedding provider at all, keyword (BM25/tsvector) search still works.

**6. Confirm the search mode (controls per-query cost).** `gbrain init` auto-applies a mode; do NOT silently accept it — the corner-to-corner cost spread is ~25×. For a budget-capped lab, `balanced` is the sane middle.

```bash
gbrain config set search.mode balanced   # conservative | balanced | tokenmax
gbrain search modes                      # confirm the active mode
```

| mode | budget | LLM expansion | chunks | fits |
|------|--------|---------------|--------|------|
| conservative | 4K | off | 10 | Haiku / high-volume / cost-sensitive |
| balanced | 12K | off | 25 | Sonnet-tier sweet spot |
| tokenmax | none | on | 50 | Opus / frontier, max recall |

**7. Verify the install** (`docs/GBRAIN_VERIFY.md`):

```bash
gbrain doctor --json     # connection (N pages) · pgvector installed · rls enabled ·
                         # schema_version current · embeddings coverage %
gbrain check-update --json
```

The signal that Phase 1 worked is the **embedding line** plus the core DB checks — measured on a fresh brain:

```
[OK] embedding_provider: ollama:<model> ✓ 250ms, 768 dims, DB aligned
[OK] embedding_width_consistency: Schema width (768d) matches gateway
[OK] connection · pgvector · rls N/N · schema_version 113 (latest)
Overall health score: 85/100. All checks OK (some warnings).
```

A fresh, empty brain legitimately shows a few **benign WARNs** — don't chase them: `embeddings: No embeddings yet` (0 pages; clears after Phase 3's `import` + `embed --stale`), `pack_upgrade_available` (optional `gbrain-base-v2` upgrade), `takes_count: 0` (opt-in). The `embedding_provider … ✓ … DB aligned` line is the one that proves oMLX is wired. If `pgvector` fails, step 2's `CREATE EXTENSION` didn't run; if `schema_version: 0`, run `gbrain apply-migrations --yes` (gotcha #218).

> **Your brain ≠ this repo.** The cloned `gbrain/` is the *tool*. Your actual notes live in a *separate* brain repo (`mkdir ~/brain && cd ~/brain && git init`), organized MECE — `people/ companies/ concepts/ …` per `docs/GBRAIN_RECOMMENDED_SCHEMA.md`. That corpus is Phase 2.

### Phase 2 — Prepare the raw corpus [executed]

**Goal:** stage raw, differently-shaped sources for the agent to convert. You do **not** format them — the conversion is the agent's job (Phase 3).

**Two layers, two owners** (`docs/GBRAIN_RECOMMENDED_SCHEMA.md`):
- **Raw sources** — emails, transcripts, any format. **Immutable**, kept in `sources/`; the agent *reads* them, never rewrites them.
- **The brain** — two-layer pages (*Compiled Truth* / `---` / *Timeline*) with `[[dir/slug]]` wikilinks. **The agent writes this layer** (Phase 3).

> **Anti-pattern (BCJ Entry 4):** hand-converting each source format, or hand-authoring the pages, does not scale and is not how GBrain works. The agent is the formatter; you curate.

```bash
mkdir -p ~/brain/{sources,people,companies,deals,meetings,concepts} && cd ~/brain && git init
# drop raw samples (any format) under sources/
```

**What we staged** — two synthetic, mutually-consistent fixtures, deliberately different shapes so one agent must handle both:
- `sources/emails/acme-thread.txt` — email thread (`From:/To:/Subject:` + reply chain)
- `sources/transcripts/dinner.txt` — timestamped speaker transcript

The raw→structured conversion is **not** a deterministic command (it's an LLM judgment — which entities, which directory, which typed edge), so it's done by the standalone agent in **Phase 3**, which emits pages shaped like:

```text
# Alice Chen
Founder of [[companies/acme-ai]]; previously at [[companies/anthropic]]; angel in [[companies/stripe]].
---
## Timeline
- 2026-05-12 — dinner re [[deals/acme-seed]] (source: sources/transcripts/dinner.txt)
```

**Verification:** the raw fixtures exist under `~/brain/sources/`; the structured `people/…`, `companies/…`, `deals/…` pages appear only after the Phase 3 agent runs (then Phase 4 verifies the graph).

### Phase 3 — A future agent uses GBrain as memory over MCP [executed, measured]

> **This is the ingestion engine for the whole lab.** It converts the Phase 2 raw
> fixtures into structured pages; Phase 4 then verifies the graph it wired.

**Goal:** the transferable skill behind this whole chapter — a **standalone agent you build** (here: smolagents, *not* Claude Code) uses GBrain as its memory layer over **MCP**: read raw → LLM-extract structured pages → `put_page` → `query`. Lab repo: `~/code/agent-prep/lab-03-5-96-gbrain/` (full source + `RESULTS.md`).

**Framework choice (researched).** The agent's brain is local **oMLX, which has no native tool-calling**. smolagents' `CodeAgent` — the LLM writes Python that calls tools — is purpose-built for that; it doesn't need function-calling. (PydanticAI and the OpenAI Agents SDK are cleaner/typed but *require* a tool-calling model — you'd route the brain through VibeProxy→Haiku for those.) `use_structured_outputs_internally=True` sidesteps oMLX's `<code>` parsing (smolagents issue #1851).

**Design: thin agent, fat tools.** A 14B can't reliably read files **and** write a good extractor **and** compose markdown in one code loop — and the `CodeAgent` sandbox blocks `pathlib`/`json`. So the hard work lives in tools (`read_sources`, `extract_pages`); the agent's own code is ~4 lines of orchestration.

#### Probe first — can plain Python drive GBrain's MCP?

The smallest proof (`src/probe_mcp.py`, core): a Python MCP client spawns `gbrain serve` over stdio and lists its tools. **An MCP server is a separate process — it does NOT inherit your shell env**, so DB + oMLX vars are injected at spawn:

**When to use:** Reach for `probe_mcp.py` when you want to confirm the GBrain MCP server is reachable from plain Python before building any agent - it isolates the spawn + handshake + tool-enumeration concern so a later failure in `ingest_agent.py` has exactly one cause (the prompt/agent logic) rather than two (plumbing + logic).

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  PY[Python MCP client] -->|"StdioServerParameters<br/>env = _server_env()"| SP[spawn gbrain serve<br/>separate process]
  SP --> INIT[session.initialize]
  INIT --> LT[list_tools]
  LT --> T[~70 tools<br/>put_page · query · search · ...]
```
*`probe_mcp.py` flow. A plain Python client spawns the GBrain MCP server over stdio and enumerates its tools - the smallest possible proof the MCP path works from non-Claude-Code Python before any agent is built. The env dict is injected at spawn because the server is a child process that does not inherit the shell.*

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def _server_env() -> dict[str, str]:
    env = dict(os.environ)                                   # inherit, then add:
    env["PATH"] = os.path.expanduser("~/.bun/bin") + os.pathsep + env["PATH"]
    for k in ("GBRAIN_DATABASE_URL", "OLLAMA_BASE_URL", "OLLAMA_API_KEY"):
        if os.getenv(k): env[k] = os.environ[k]
    return env

params = StdioServerParameters(command=GBRAIN, args=["serve"], env=_server_env())
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = (await session.list_tools()).tools           # ~70 tools
```

**Walkthrough:**
- **The env dict is the whole point.** A stdio MCP server is a *child process*; it does not inherit your interactive shell's exports. `_server_env()` rebuilds what GBrain needs - `~/.bun/bin` on `PATH` (so `gbrain` resolves) plus `GBRAIN_DATABASE_URL` / `OLLAMA_BASE_URL` / `OLLAMA_API_KEY` - and passes it via `StdioServerParameters(env=...)`. Skip this and the server starts but can't reach Postgres or the embedder, and every tool call fails opaquely.
- **Probe-first is de-risking, not ceremony.** Before wiring smolagents, this ~15-line client proves the spawn + handshake + tool list work from plain Python. If the probe lists `put_page`/`query`, the agent's only remaining variable is the *prompt* - you've separated "is the MCP plumbing alive?" from "can the model drive it?", so a later failure has one cause, not two. The same `_server_env()` is then reused verbatim by `ingest_agent.py`.

**Result:** ~70 tools exposed; `put_page, add_link, add_timeline_entry, query, search` all present. The MCP path works from non-Claude-Code Python.

#### The agent

**When to use:** Reach for `ingest_agent.py` when your corpus fits in a single LLM context window (tens of files, up to a few hundred pages) and you want the full WRITE - RECONCILE - AUTO-EVAL - READ lifecycle in one blocking script. Use `resumable_ingest.py` instead when the source set is large enough that a single extraction call would exceed the model's context or timeout, or when you need per-file retry and progress checkpointing.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  M[main]
  M -->|0 warm cache| EP0[extract_pages<br/>oMLX · driver-side<br/>outside sandbox]
  M -->|1 WRITE| AG[CodeAgent loop<br/>thin · orchestrates]
  subgraph TOOLS["fat tools"]
    RS[read_sources<br/>local file I/O]
    EP[extract_pages<br/>raw to pages · cached]
    PP[put_page<br/>MCP write]
  end
  AG --> RS
  AG --> EP
  AG -->|per page| PP
  PP --> GB[(GBrain<br/>Postgres + pgvector)]
  M -->|2 RECONCILE| RG[reconcile_graph<br/>extract links · 0-LLM]
  M -->|2.5 AUTO-EVAL| RA[run_auto_eval<br/>policy_eval / auto_eval]
  M -->|3 READ| QW[query_with_policy<br/>query_policy.ts]
  RG --> GB
  RA --> POL[(search_policy.json)]
  POL --> QW
  QW --> GB
```
*`ingest_agent.py` call graph. The thin `CodeAgent` only orchestrates (read → extract → loop put_page); the capability lives in the two `@tool`s and the three driver-side infra calls (`reconcile_graph` → `run_auto_eval` → `query_with_policy`) `main()` runs in order around the agent. The cache is warmed once outside the 30 s sandbox so the in-agent `extract_pages` returns instantly.*

**Code:** `src/ingest_agent.py` (full)

```python
"""W3.5.96 — a memory-augmented agent (smolagents) that uses GBrain as its memory
layer over MCP. The transferable pattern for FUTURE agent development.

Design = idiomatic smolagents: **thin agent, fat tools.** A small local model can't
reliably read files AND write a good extractor AND compose markdown in one code loop
(and the CodeAgent sandbox blocks `pathlib`/`json` anyway). So the hard work lives in
TOOLS; the agent just orchestrates:

  tools given to the agent:
    - read_sources()        local  — returns the raw text of ~/brain/sources/*
    - extract_pages(raw)    local  — LLM (oMLX) raw → structured GBrain pages (list)
    - put_page, query, ...  MCP    — GBrain, loaded via ToolCollection.from_mcp

  the agent's whole job (a few lines of code it writes itself):
    raw = read_sources(); pages = extract_pages(raw)
    for p in pages: put_page(slug=p['slug'], content=p['content'])
    answer = query(query="..."); final_answer(answer)

After the agent run, main() calls reconcile_graph() — a deterministic, zero-LLM
`gbrain extract links --source db` pass that materializes the [[wikilinks]] into
typed edges. This is infra, NOT an agent tool: put_page over MCP skips inline
auto-link (remote caller) and inline auto-link can't wire forward references
anyway, so the graph must be reconciled once the full corpus exists.

Then main() calls run_auto_eval() — a best-effort, post-ingest retrieval-health +
search-policy step (golden_eval.json present → policy_eval.ts on REAL questions,
else auto_eval.ts cold-start proxy). It re-selects keyword/vector/hybrid against
the current corpus and writes results/search_policy.json, so retrieval self-tunes
on every ingest. It never raises (AUTO_EVAL=0 disables it). Queries then read that
policy via query_with_policy() → query_policy.ts (Phase 9), not a hard-coded hybrid.

Brain = oMLX (no native tool-calls) → CodeAgent + use_structured_outputs_internally.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess

from dotenv import load_dotenv
from mcp import StdioServerParameters
from openai import OpenAI
from smolagents import CodeAgent, OpenAIServerModel, ToolCollection, tool

_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

SOURCES = pathlib.Path(os.path.expanduser("~/brain/sources"))
_BUN_BIN = os.path.expanduser("~/.bun/bin")
_GBRAIN = os.getenv("GBRAIN_BIN", "gbrain")
if _GBRAIN == "gbrain":
    _GBRAIN = os.path.join(_BUN_BIN, "gbrain")

NEEDED_TOOLS = {"put_page", "query"}   # the MCP tools the agent calls

_EXTRACT_PROMPT = """Convert raw notes into GBrain pages. One page per entity.

Slug: path-qualified kebab-case — people/<name>, companies/<name>, deals/<name>, meetings/<name>.

content MUST follow this exact two-layer shape:

# <Title>

<one-paragraph summary. EVERY other entity you mention MUST be a path-qualified
wikilink [[dir/slug]], e.g. [[people/alice-chen]], [[companies/acme-ai]].>

---
## Timeline
- YYYY-MM-DD — <event, also using [[dir/slug]] wikilinks> (source: <raw filename>)

HARD RULES (a page that breaks these is WRONG):
- The separator between summary and Timeline is a line that is EXACTLY `---` (three hyphens). Never an HTML comment.
- EVERY mention of another entity is a [[dir/slug]] wikilink. A page with zero wikilinks is invalid.
- If you mention an entity, also emit its page, and link to it by the SAME slug.
- Deduplicate across docs (one page per entity). Use ONLY facts in the raw text.

Worked example of one page's content field:
"# Alice Chen\\n\\nFounder & CEO of [[companies/acme-ai]]; angel in [[companies/stripe]]; raising [[deals/acme-seed]] with [[people/sam-okafor]].\\n\\n---\\n## Timeline\\n- 2026-05-12 — dinner with [[people/sam-okafor]] re [[deals/acme-seed]] (source: sources/transcripts/dinner.txt)"

Output ONLY JSON: {"pages":[{"slug":"people/alice-chen","content":"..."}]}.

RAW:
{raw}
"""


@tool
def read_sources() -> str:
    """Read every raw file under ~/brain/sources/ and return their concatenated text,
    each prefixed with its relative path as a header."""
    parts = []
    for f in sorted(SOURCES.rglob("*")):
        # skip non-files AND anything under a dotted path part (.DS_Store, .omc-state/…)
        if not f.is_file() or any(part.startswith(".") for part in f.relative_to(SOURCES).parts):
            continue
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue  # skip binary / non-UTF-8 files rather than crash the ingest
        parts.append(f"===== {f.relative_to(SOURCES.parent)} =====\n{text}")
    return "\n\n".join(parts)


_PAGES_CACHE: list | None = None


@tool
def extract_pages(raw: str) -> list:
    """Turn raw source text into structured GBrain pages via the local LLM.

    Cached: the ~60s oMLX extraction exceeds smolagents' 30s per-step sandbox
    timeout, and the agent re-runs its whole code block on each step. main()
    warms this cache ONCE before the agent loop (outside the sandbox, no
    timeout), so the agent's `extract_pages(raw)` call returns instantly and
    ingest finishes in one step. Single-corpus assumption: the cache ignores
    `raw` after the first compute.

    Args:
        raw: concatenated raw source text (from read_sources).
    """
    global _PAGES_CACHE
    if _PAGES_CACHE is not None:
        return _PAGES_CACHE
    client = OpenAI(base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                    api_key=os.getenv("LLM_API_KEY", "dummy"))
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "Qwen2.5-Coder-14B-Instruct-MLX-4bit"),
        messages=[{"role": "user", "content": _EXTRACT_PROMPT.replace("{raw}", raw)}],
        temperature=0.0, max_tokens=4000, response_format={"type": "json_object"})
    data = json.loads(resp.choices[0].message.content or "{}")
    _PAGES_CACHE = [p for p in data.get("pages", []) if p.get("slug") and p.get("content")]
    return _PAGES_CACHE


def _server_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = _BUN_BIN + os.pathsep + env.get("PATH", "")
    for k in ("GBRAIN_DATABASE_URL", "OLLAMA_BASE_URL", "OLLAMA_API_KEY"):
        if (v := os.getenv(k)):
            env[k] = v
    return env


def reconcile_graph() -> str:
    """Deterministic post-ingest pass (zero LLM): materialize the `[[wikilinks]]`
    the agent wrote into typed graph edges. REQUIRED after an agent/MCP ingest,
    for two reasons baked into GBrain:
      1. `put_page` over MCP is a *remote* caller, so GBrain skips inline auto-link
         (operations.ts -> `skipped: 'remote'`); nothing wires on write.
      2. Even inline auto-link only wires targets that ALREADY exist (FK-safety),
         so the forward references a single-pass ingest creates would be dropped.
    `extract links --source db` reconciles the FINISHED corpus (all pages present),
    resolving every forward ref. Run it once, after all put_page writes."""
    out = subprocess.run(
        [_GBRAIN, "extract", "links", "--source", "db"],
        capture_output=True, text=True, env=_server_env(),
    )
    lines = [ln for ln in (out.stdout or out.stderr).splitlines() if ln.strip()]
    return lines[-1] if lines else "(no output)"


def run_auto_eval() -> str:
    """Post-ingest retrieval-health + search-policy step. BEST-EFFORT: a failed or
    absent eval must NEVER break an ingest, so every error path returns a string
    instead of raising. Disable with AUTO_EVAL=0.

    Branch: prefer the REAL-question policy source when a golden set exists; fall
    back to the known-item proxy only as cold-start (no golden set yet). The proxy
    is a regression guardrail, not the policy oracle (Bad-Case Entry 20)."""
    if os.getenv("AUTO_EVAL", "1") != "1":
        return "(skipped: AUTO_EVAL=0)"
    bun = shutil.which("bun", path=_server_env().get("PATH"))
    if not bun:
        return "(skipped: bun not found on PATH)"
    golden = pathlib.Path(__file__).resolve().parent.parent / "data" / "golden_eval.json"
    script = pathlib.Path(__file__).resolve().parent / (
        "policy_eval.ts" if golden.exists() else "auto_eval.ts")   # ← the decision
    try:
        out = subprocess.run([bun, str(script)], capture_output=True, text=True,
                             env=_server_env(), timeout=600)
    except Exception as e:  # noqa: BLE001 — eval is advisory; never fail the ingest
        return f"(auto-eval error: {e})"
    if out.stdout:
        print(out.stdout, end="")
    lines = [ln for ln in (out.stdout or out.stderr).splitlines() if ln.strip()]
    return lines[-1] if lines else "(no output)"


def query_with_policy(query: str, limit: int = 5) -> str:
    """APPLY half of the loop: run a query through query_policy.ts, which reads the
    corpus-selected strategy from results/search_policy.json (written by the last
    run_auto_eval) and routes to keyword/vector/hybrid accordingly — instead of a
    hard-coded hybrid. This is how the agent's retrieval honors the per-corpus
    verdict. With QUERY_ROUTER=on it routes per-query + adds entity-aware one-hop
    assembly (Phase 9). Returns the actuator's stdout (policy line + ranked slugs)."""
    env = _server_env()
    bun = shutil.which("bun", path=env.get("PATH"))
    if not bun:
        return "(query_policy skipped: bun not found)"
    script = pathlib.Path(__file__).resolve().parent / "query_policy.ts"
    out = subprocess.run([bun, str(script), query, str(limit)],
                         capture_output=True, text=True, env=env, timeout=120)
    return (out.stdout or out.stderr).strip()


# Two phases on purpose: WRITE, then (infra reconcile), then READ. The query must
# run AFTER reconcile_graph() or it reads a graph whose edges aren't materialized.
INGEST_TASK = """Build the brain using ONLY the provided tools:
1. raw = read_sources()
2. pages = extract_pages(raw)
3. for each page in pages: call put_page(slug=page["slug"], content=page["content"])
4. return the number of pages written via final_answer.
"""
QUERY_TASK = """Answer using ONLY the query tool:
1. answer = query(query="Who is anchoring the acme-seed round and on what terms?")
2. return answer via final_answer.
"""


def main() -> None:
    server = StdioServerParameters(command=_GBRAIN, args=["serve"], env=_server_env())
    model = OpenAIServerModel(
        model_id=os.getenv("LLM_MODEL", "Qwen2.5-Coder-14B-Instruct-MLX-4bit"),
        api_base=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
        api_key=os.getenv("LLM_API_KEY", "dummy"))

    with ToolCollection.from_mcp(server, trust_remote_code=True) as tc:
        mcp_tools = [t for t in tc.tools if t.name in NEEDED_TOOLS]
        print(f">>> GBrain MCP tools: {sorted(t.name for t in mcp_tools)}")
        agent = CodeAgent(
            tools=[read_sources, extract_pages, *mcp_tools],
            model=model, max_steps=6,
            use_structured_outputs_internally=True, verbosity_level=1)

        # 0. WARM the extraction cache OUTSIDE the agent sandbox. The oMLX
        # extraction is ~60s; smolagents kills any single step's code at 30s, so
        # if the agent triggered it inside its loop every step would time out and
        # re-extract. Running it once here (no sandbox) means the agent's
        # extract_pages(raw) call returns the cached result instantly.
        extract_pages(read_sources())

        # 1. WRITE — the agent ingests raw sources into GBrain pages (cache-fast).
        print(">>> ingest: " + str(agent.run(INGEST_TASK)))

        # 2. RECONCILE — deterministic, zero-LLM. NOT an agent tool (must not depend
        # on the LLM remembering). Materializes the [[wikilinks]] into typed edges
        # BEFORE the read, so the query sees the wired graph. See reconcile_graph().
        print(">>> reconcile graph: " + reconcile_graph())

        # 2.5 AUTO-EVAL — retrieval-health + search-policy after every ingest.
        # golden_eval.json present → policy_eval.ts (real Qs); else auto_eval.ts
        # (cold start). Writes results/search_policy.json. Best-effort: never
        # breaks the ingest (AUTO_EVAL=0 disables). See Phase 9 for the loop.
        print(">>> auto-eval: " + run_auto_eval())

        # 3. READ — query now runs over the reconciled graph AND the chosen policy.
        answer = agent.run(QUERY_TASK)
        print("\n>>> agent final answer:\n" + str(answer))


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **`ToolCollection.from_mcp` + filter.** smolagents loads GBrain's MCP tools straight in (needs `smolagents[mcp]`). We pass only the ~2 the agent calls — GBrain exposes ~70, and handing all to a 14B blows its context and confuses tool selection.
- **The two `@tool`s are where the intelligence lives.** `read_sources` does file I/O (the agent can't — sandbox blocks `pathlib`); `extract_pages` makes the one focused oMLX call that turns raw text into structured pages with wikilinks. The agent itself just loops `put_page` and calls `query`.
- **The extraction prompt is the load-bearing part.** It *hard-mandates* `[[wikilinks]]` with a worked example — because without that the model writes prose and the graph never wires (see Result).
- **`main()` runs the whole lifecycle in order: WRITE → RECONCILE → AUTO-EVAL → READ** (§3.1). After the agent writes pages, `reconcile_graph()` wires the edges, then `run_auto_eval()` re-selects the search policy against the now-current corpus (`policy_eval.ts` if `data/golden_eval.json` exists, else the `auto_eval.ts` cold-start proxy) and writes `results/search_policy.json`. It is **best-effort** — wrapped so a failed eval returns a string instead of raising, because an advisory retrieval check must never break an ingest (`AUTO_EVAL=0` skips it). The READ step then honors that policy via `query_with_policy()` → `query_policy.ts` (Phase 9), not a hard-coded hybrid. This is the seam that makes retrieval self-tune on every ingest.

**Result:** `uv run python src/ingest_agent.py` — the agent wrote **10 pages** via `put_page`, then `gbrain extract links --source db` produced **11 typed edges**. `query "who is anchoring acme-seed?"` → top hit `deals/acme-seed` (**score 0.93**): *"Seed round for `[[companies/acme-ai]]`… `[[people/sam-okafor]]` is anchoring the remainder."* `graph-query deals/acme-seed` traverses `--invested_in->` / `--works_at->` / `--mentions->` across people + companies (depth 1–5).

**Critical finding — graph quality = extraction quality.** Run 1 (extraction prompt *without* the wikilink mandate): 5 pages stored fine, but `extract links` → **`Links: 0`** — the 14B wrote "Alice Chen, founder of Acme AI" as plain prose. Run 2 (few-shot + "zero wikilinks = invalid"): **`Links: 11`**. The framework + MCP plumbing was the easy part; the graph only materialized once the prompt enforced the typed-link contract.

`★ Insight ─────────────────────────────────────`
- This is the answer to "how do I use a memory system in my own agent?": wire its **MCP tools** into a framework (smolagents here), keep the agent **thin** (orchestrate), and put capability in **tools**. You don't build a bespoke converter and you don't hand-author pages — the agent + a disciplined extraction prompt is the converter.
- A capable-but-small local model will **silently** store well-written prose and produce a zero-edge "graph," because it dropped the wikilinks. Measure **edges, not pages** — the storage call succeeding tells you nothing about whether the graph wired.
`─────────────────────────────────────────────────`

---

### Phase 4 — Verify the self-wiring graph [executed, measured]

**Goal:** confirm the `[[wikilinks]]` the agent wrote became typed graph edges — deterministically, zero LLM. As of the wired agent, **Phase 3 already reconciles**: its `main()` calls `reconcile_graph()` (`gbrain extract links --source db`) after the writes and before the query. So this phase *verifies* the materialized graph and explains **why that pass is required, not automatic.**

**Why the reconcile pass is required (by design, not a glitch):**
1. The agent writes via MCP `put_page` — a **remote** caller — so GBrain *skips inline auto-link* (`operations.ts` → `skipped: 'remote'`); nothing wires on write.
2. Even inline auto-link only wires targets that **already exist** (FK-safety), so the *forward references* a single-pass ingest creates (`people/lin-zhao` cites `companies/acme-ai` before that page exists) would be dropped anyway.

`extract links --source db` reconciles the **finished** corpus — every page present, every forward ref resolvable. That's why our links went **11 → 45** only after the batch pass (BCJ Entry 7).

```bash
# the agent already ran reconcile_graph(); these VERIFY it (re-running extract is idempotent)
gbrain stats                         # pages · links · embedded chunks
gbrain graph-query deals/acme-seed   # typed-edge traversal: --invested_in-> / --works_at-> / --mentions->
gbrain extract links --source db     # idempotent re-check — "0 new links" if already reconciled
```

> **Gotcha:** there is no `gbrain ingest` (it's `import`) and no `gbrain entity` (use `graph-query` / `backlinks` / `get`). `links: 0` means the agent's pages had no wikilinks (the real failure we hit — BCJ Entry 5), since the reconcile pass is now automatic.

**Result (measured):** the wired agent reconciles automatically — small-corpus **10 pages → 11 edges**; scaled 8-source run **19 pages → 45 edges** (`extract links --source db` created 34); the large-corpus `resumable_ingest.py` run reached **23 pages / 63 links** with per-file merge. `gbrain graph-query deals/acme-seed` traverses `--invested_in->` / `--works_at->` / `--mentions->` (depth 1–5). **Deterministic:** re-running `extract` yields identical edges (regex/parser, zero LLM). The first run produced `links: 0` until the extraction prompt mandated wikilinks (BCJ Entry 5) — *graph quality = extraction quality.*

### Phase 5 — Synthesis layer + "what we don't know" check [executed, measured]

**Goal:** confirm the synthesis layer flags gaps instead of fabricating, on a fact the corpus does **not** contain.

> **Two corrections from running it:** (1) synthesis is **`gbrain think`** — *"multi-hop synthesis … cited answer with conflict + gap analysis."* `ask`/`query` are *retrieval* (ranked chunks), not synthesis. (2) `think` needs a **chat LLM**; an embeddings-only install returns retrieval only. We wired the chat model at **VibeProxy → Claude** (the chapter's chat-via-VibeProxy path) while embeddings stayed local on oMLX:

```bash
export OPENROUTER_API_KEY=dummy OPENROUTER_BASE_URL=http://localhost:8317/v1   # VibeProxy (chat)
gbrain think "What did Alice Chen do on 2026-06-15?" \
  --model openrouter:claude-sonnet-4-5-20250929        # date ABSENT from the corpus
```

**Result (measured):**
```
# What did Alice Chen do on 2026-06-15?
No information available about Alice Chen's activities on 2026-06-15.
Model: openrouter:claude-sonnet-4-5-20250929 | Pages: 9 | Citations: 0
```
**Gap correctly flagged — no fabrication.** Synthesis pulled 9 candidate pages but honestly reported no info for that date rather than inventing an event. This is the **embeddings-local-oMLX / chat-via-VibeProxy** split working end-to-end (the W3.5.9 topology).

**Verification:** ✅ the absent date returns an explicit "no information," not a fabricated event; for a *present* fact (Phase 3's `query`) the same brain answers with score 0.93.

### Phase 6 — Keyword vs vector vs hybrid-RRF benchmark [executed, measured]

**Goal:** measure, on a labeled 10-query set, whether hybrid-RRF actually beats its component retrievers (keyword FTS, pure vector). **Result: it did not** — on this corpus pure vector won, and RRF's keyword arm was dead weight. The reproducible path below is more important than the headline, because two traps make the *naive* version of this benchmark silently wrong.

**Step A — scale the corpus (2 → 8 raw sources, 19 pages).** Two sources can't exercise retrieval. Drop four more differently-shaped fixtures under `~/brain/sources/` (two intro emails, a CTO email, a seed-deal email, a VC's tweets, two meeting transcripts), then re-run the Phase-3 agent over the whole `sources/` tree:

```bash
# fixtures already staged under ~/brain/sources/{emails,tweets,transcripts}/
cd ~/code/agent-prep/lab-03-5-96-gbrain
python3 src/ingest_agent.py      # Phase-3 agent, now over 8 sources → 19 pages
```

**Step B — materialize the graph (the first trap).** The agent writes `[[wikilinks]]` into page *text* via `put_page`, but on the expanded run the link **count stayed at 11** while the text held ~68 wikilinks. Self-wiring is **not** a `put_page` side-effect — it is a deliberate batch pass, and for pages written over MCP (not from files) you must point it at the DB, not a brain directory:

```bash
export PATH="$HOME/.bun/bin:$PATH" \
  GBRAIN_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gbrain \
  OLLAMA_BASE_URL=http://localhost:8000/v1 OLLAMA_API_KEY=<key>
cd ~/brain
gbrain extract links              # → "No brain directory configured" — the trap
gbrain extract links --source db  # → "created 34 links from 19 pages" → 45 total
```

> **Why `--source db`?** The bare `extract links` walks a registered brain *directory* of `.md` files; our pages live only in Postgres because the agent wrote them through the MCP `put_page` tool. `--source db` re-parses the stored `compiled_truth`/`timeline` columns. (Aside: it does **not** stamp `pages.links_extracted_at` — that column tracks the file-source path only — so don't use that column to decide whether DB-source extraction ran.)

**Step C — the second trap: the CLI cannot A/B keyword vs hybrid.** The obvious benchmark is `gbrain search` (keyword) vs `gbrain query` (hybrid). It is **invalid**: both subcommands fall through to the *same* handler (`src/cli.ts:771-772 — case 'search': case 'query':`), so they return byte-identical rankings, scores included. The real keyword/vector/hybrid split lives one layer down — `engine.searchKeyword` / `engine.searchVector` / `hybridSearch` — exposed only through GBrain's own eval harness, `src/core/search/eval.ts:runEval()`. The benchmark must call that directly.

Below: the harness bootstraps the engine + AI gateway exactly as the CLI does, then runs `runEval()` once per strategy on one qrel set.

**When to use:** reach for `bench_strategies.ts` when you need a rigorous, engine-layer A/B of keyword vs vector vs hybrid-RRF - specifically because `gbrain search` and `gbrain query` alias to the same CLI handler and cannot be differentiated from the shell; use its Python sibling `bench_rrf.py` only for a quick sanity check on a loaded brain where CLI-layer hit@3 is sufficient.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  Q["10 labeled qrels<br/>(query → gold slug)"] --> RE["runEval()<br/>gbrain eval engine"]
  RE --> KW["strategy: keyword<br/>engine.searchKeyword<br/>(tsvector FTS)"]
  RE --> VEC["strategy: vector<br/>embed(q) + searchVector<br/>(oMLX 768-d HNSW)"]
  RE --> HY["strategy: hybrid<br/>hybridSearch<br/>(vector+keyword+RRF)"]
  KW --> M["recall@3 / MRR / nDCG@3"]
  VEC --> M
  HY --> M
```

**Code:** `src/bench_strategies.ts` (run with `bun`, not `python` — it imports GBrain's TypeScript engine directly):

```typescript
/**
 * Phase 6 benchmark (CORRECT path) — keyword FTS vs pure vector vs hybrid-RRF.
 *
 * WHY this exists: `gbrain search` and `gbrain query` CLI commands fall through
 * to the SAME hybrid handler (cli.ts:771-772), so they cannot be A/B'd from the
 * shell — they return byte-identical rankings. The real keyword/vector/hybrid
 * split lives one layer down in gbrain's own eval harness (src/core/search/eval.ts),
 * which calls engine.searchKeyword / engine.searchVector / hybridSearch directly.
 * This script bootstraps the engine + AI gateway exactly as the CLI does, then
 * runs runEval() three times on one labeled qrel set.
 *
 * Run: bun src/bench_strategies.ts   (needs GBRAIN_DATABASE_URL + OLLAMA_* env)
 */
const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;

const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { runEval } = await import(`${GB}/core/search/eval.ts`);

// (query, relevant-slug, kind) — single gold per query; kind documents intent.
const QRELS = [
  { query: "Lin Zhao",                          relevant: ["people/lin-zhao"],             kind: "exact" },
  { query: "Ridgeline Capital",                 relevant: ["companies/ridgeline-capital"], kind: "exact" },
  { query: "Northstar Ventures",                relevant: ["companies/northstar-ventures"],kind: "exact" },
  { query: "Marcus Webb",                       relevant: ["people/marcus-webb"],          kind: "exact" },
  { query: "dinner at Tartine",                 relevant: ["meetings/tartine-dinner"],     kind: "exact" },
  { query: "who runs serving infrastructure",   relevant: ["people/lin-zhao"],             kind: "semantic" },
  { query: "protein design foundation models",  relevant: ["companies/helix-bio"],         kind: "semantic" },
  { query: "inference optimization startup",    relevant: ["companies/quanta-labs"],       kind: "semantic" },
  { query: "early-stage bio funding round",     relevant: ["deals/helix-series-a"],        kind: "semantic" },
  { query: "payments company angel investment", relevant: ["companies/stripe"],            kind: "semantic" },
];

const K = 3;

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
const { reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
await reconfigureGatewayWithEngine(engine);

const qrels = QRELS.map(({ query, relevant }) => ({ query, relevant }));
const strategies = ["keyword", "vector", "hybrid"] as const;

// Per-query rank table (rank of the gold slug under each strategy).
const reports: Record<string, any> = {};
for (const strategy of strategies) {
  reports[strategy] = await runEval(engine, qrels, { strategy, expand: false }, K);
}

const pad = (s: string, n: number) => s.padEnd(n);
console.log(pad("query", 38) + pad("kind", 10) + pad("keyword", 10) + pad("vector", 10) + pad("hybrid", 10));
console.log("-".repeat(78));
QRELS.forEach((q, i) => {
  let row = pad(q.query, 38) + pad(q.kind, 10);
  for (const s of strategies) {
    const hits: string[] = reports[s].queries[i].hits;
    const rank = hits.indexOf(q.relevant[0]) + 1; // 0 → not found
    row += pad(rank > 0 ? `@${rank}` : "MISS", 10);
  }
  console.log(row);
});
console.log("-".repeat(78));
console.log("\n" + pad("strategy", 12) + pad(`recall@${K}`, 12) + pad("MRR", 10) + pad(`nDCG@${K}`, 10));
for (const s of strategies) {
  const r = reports[s];
  console.log(pad(s, 12) + pad(r.mean_recall.toFixed(3), 12) + pad(r.mean_mrr.toFixed(3), 10) + pad(r.mean_ndcg.toFixed(3), 10));
}

await engine.disconnect?.();
process.exit(0);
```

**Walkthrough:**
- **Block 1 — dynamic imports of GBrain internals.** The harness lives in the lab repo but `await import()`s GBrain's `.ts` modules by absolute path. Bun resolves transitive deps (postgres.js, the gateway) from GBrain's own `node_modules`, so no install is needed in the lab. We import `runEval` (the eval engine), plus the four bootstrap functions the CLI uses.
- **Block 2 — the qrel set.** Ten queries split 50/50 between **exact** (proper nouns a keyword index can match) and **semantic** (paraphrases with *no shared surface token* — `who runs serving infrastructure` shares nothing lexical with the `lin-zhao` page that answers it). The split is the whole experiment: it's designed to expose where keyword and vector diverge.
- **Block 3 — CLI-identical bootstrap.** `loadConfig()` → `configureGateway(buildGatewayConfig())` → `createEngine` → `connectWithRetry` → `reconfigureGatewayWithEngine`. This exact sequence (from `cli.ts:1962-2050`) is what makes `embed(query)` work: the vector strategy must embed the *query string* at run-time via oMLX, and that needs the gateway configured. Skip it and vector search silently no-ops (`hybrid.ts:975` — "skip vector search if the gateway has no embedding provider").
- **Block 4 — three runs, `expand:false`.** One `runEval` per strategy. Expansion is off for eval stability (it's an LLM call that adds variance); we're measuring the retrievers, not the query rewriter. `rank = hits.indexOf(gold)+1` turns each result list into the gold slug's rank for the per-query table.

**Result** (19-page brain, oMLX `nomicai-modernbert` 768-d embeddings, 2026-06-04):

| strategy | recall@3 | MRR | nDCG@3 |
|---|---|---|---|
| keyword (tsvector FTS) | 0.600 | 0.500 | 0.526 |
| **vector (HNSW)** | **0.900** | **0.917** | **0.900** |
| hybrid (RRF) | 0.900 | 0.783 | 0.813 |

Per-query: keyword **MISSED all four** purely-semantic queries (no lexical overlap); vector found 9/10 in the top-3; **RRF matched vector's recall but lost MRR and nDCG** because fusing the dead keyword arm pushed strong vector hits down a rank (`dinner at Tartine` vector @1 → hybrid @3; `early-stage bio` vector @1 → hybrid @2).

**Conclusion (refutes the original projection):** on a small, semantic-heavy corpus, **pure vector beats hybrid-RRF**. RRF is not a free upgrade — it helps only when *both* arms are individually competitive and complementary. Garry Tan's published **83→95 Recall@5** lift was on a 240-page corpus with enough exact-term traffic that the keyword arm earns its weight; do not assume that direction transfers to a 19-page brain. (To see RRF win here you'd need more proper-noun / exact-phrase queries, or a corpus large enough that vector recall degrades and keyword starts catching the tail.)

`★ Insight ─────────────────────────────────────`
- **Two silent traps gate this benchmark, and both look like "it worked".** (1) Wikilinks in `put_page` text don't become edges until `extract links --source db` runs — the graph reads as built when it isn't. (2) `gbrain search` and `gbrain query` are the same CLI handler — an A/B between them shows zero difference and reads as "no lift," when in fact you never measured two different things. Always benchmark at the engine layer (`runEval`), never the CLI.
- **RRF can lose to its own input.** The reflexive "hybrid > vector > keyword" ranking is corpus-dependent. Here the keyword arm is net-negative for 40% of queries, so RRF's fusion *demotes* correct vector hits. Measure before claiming the lift; a hybrid that includes a weak arm can underperform that arm's strong sibling alone.
`─────────────────────────────────────────────────`

#### Why GBrain still defaults to RRF — and how to choose without guessing

The lab result does **not** refute RRF; it refutes *transplanting the published 83→95 projection onto this corpus*. RRF is a **conditional** upgrade: it wins only when both arms are individually competitive and complementary. GBrain ships it as the default because its target domain — production CRM / founder-network data at 146K-page scale (§2.5), dense with proper nouns (people, companies, acronyms, dates) — is exactly the shape where the keyword arm earns its weight. The 19-page, semantic-heavy lab brain is the opposite shape, so vector-only wins there.

**But corpus size is the wrong discriminator** (it's a confounded proxy). A *large* corpus that happens to be proper-noun-sparse — long-form prose, paraphrase-heavy chat logs — will still lose to RRF, because the keyword arm has nothing exact to catch. The causal variable is **per-query lexical signal × per-arm competitiveness**, not page count. Route on *that*, never on size. A practical three-layer auto-selection design (each layer label-cheaper than learning a full LTR router):

1. **Runtime, per-query, label-free — score-gated weighted fusion.** RRF's specific defect is that it is **rank-only**: a confident vector hit @1 and a garbage keyword hit @1 both cast a `1/(rank+k)` vote of equal weight, so a dead arm *demotes* a strong one. Fix it at the root — make fusion **score-aware**. Per query, read each arm's top score (`ts_rank`/BM25 for keyword, cosine for vector), normalize, and weight each arm's contribution by its own confidence. When a purely-semantic query yields a near-zero keyword top-score, that arm's weight collapses to ~0 and hybrid **degenerates to vector-only automatically** — so it can no longer underperform the better arm. When an exact-term query makes the keyword arm confident, the lift returns. This is corpus-size-agnostic *and* proper-noun-density-agnostic because the decision is made per query from live signal.
2. **Optional fast-path — query-feature pre-router.** Before retrieving, cheaply scan the query string for exact-term signal: quoted phrases, capitalized multi-word spans, all-caps acronyms (len ≥ 2), digits/dates, or tokens whose corpus document-frequency is low (rare = high-IDF). Signal present → run both arms (hybrid); absent → skip the keyword retrieval entirely and go vector-only. Coarser than score-gating but cheaper (it avoids the keyword round-trip when it's pointless); use it as a pre-filter, with score-gating as the accurate arbiter.
3. **Offline backbone — rolling-qrel calibration + drift guard.** The honest version of "which default, and what threshold τ" is a *measured output*, not a hand-set guess. Keep a small labeled qrel set (seed by hand; grow it from weak labels — accepted answers, click-throughs), and run the engine-layer `runEval` harness (the Phase 6 script) on a schedule: it (a) picks the global default, (b) calibrates the per-arm gate threshold τ, and (c) **alarms when the winning strategy flips**, which is your signal that the corpus shape drifted (e.g. you ingested a large prose dump and the proper-noun ratio fell). The decision stays anchored to evidence as the corpus evolves.

The meta-principle is the W3.5.9 thesis applied to retrieval: **don't reflexively default to hybrid, and don't pick by a size heuristic — gate per query on measured lexical signal, and let an eval harness, not intuition, set the thresholds.**

**Deliverable:** `src/bench_strategies.ts` in the lab repo + the table above (also in the lab's `RESULTS.md`).

> **Sibling benchmark - `src/bench_rrf.py` (the CLI-layer counterpart).** The same exact-vs-semantic question set also has a Python runner that shells out to `gbrain search` (keyword) and `gbrain query` (hybrid), parses the `[score] slug -- text` lines, and reports **hit@3 + MRR** per method. Keep it for a quick sanity check on a loaded brain, but the **engine-layer `bench_strategies.ts` above is the one to trust for an arm A/B**: `gbrain search` and `gbrain query` fall through to the *same* handler (Bad-Case Entry 8), so a CLI-level comparison can read as "no difference" between keyword and hybrid even when the engine arms genuinely diverge. `bench_rrf.py` is the artifact that surfaced that trap - which is exactly why the shown benchmark moved to the engine layer.

`src/bench_rrf.py` shells out to the GBrain CLI and measures **hit@3 + MRR** across 10 labeled queries (5 exact-name, 5 semantic-paraphrase), running both `gbrain search` (keyword/FTS) and `gbrain query` (hybrid-RRF) so you can see where the two CLI arms agree and where they diverge on this specific brain.

**When to use:** Reach for `bench_rrf.py` when you want a fast, dependency-light sanity check on a live brain - it requires only `gbrain` on PATH and a running Postgres instance. Use `bench_strategies.ts` instead whenever you need a trustworthy arm A/B, because the CLI routes both commands through the same handler (Bad-Case Entry 8) and can mask real engine-level differences.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  A["QUERIES list<br/>10 labeled tuples<br/>(query, gold_slug, kind)"] --> B["_ranked_slugs()<br/>subprocess: gbrain<br/>search OR query"]
  B --> C["stdout lines<br/>parse _LINE regex<br/>extract slug list"]
  C --> D["_rank_of()<br/>find gold in<br/>ranked slugs"]
  D --> E["hit@3 + RR<br/>accumulate per method"]
  E --> F{"all queries done?"}
  F -->|"no"| B
  F -->|"yes"| G["print per-query table<br/>+ summary hit@3 / MRR"]
  subgraph Env["_env() injection"]
    H["PATH += ~/.bun/bin"]
    I["GBRAIN_DATABASE_URL<br/>OLLAMA_BASE_URL"]
  end
  B -.->|"uses env"| Env
```
*`bench_rrf.py` data flow - query list drives two subprocess calls per row; ranked slugs are parsed from stdout and scored against the gold label.*

**Code: `src/bench_rrf.py`**

```python
"""Phase 6 benchmark — keyword FTS (`gbrain search`) vs hybrid-RRF (`gbrain query`).

Runs a labeled query set against the live brain, parses GBrain's ranked output
(`[score] slug -- text` lines), and reports hit@3 + MRR per method. The query
set deliberately mixes EXACT-NAME queries (proper nouns — favor keyword/FTS) with
SEMANTIC-PARAPHRASE queries (no shared surface token — favor vector). The whole
point is to show WHERE the two retrievers diverge, not just an aggregate.

Honest-measurement note: this brain is ~19 pages. On a corpus this small both
retrievers nearly saturate, so the RRF lift here is a floor, not the 240-page
number. We report what we measured.
"""
from __future__ import annotations

import os
import re
import subprocess

_BUN = os.path.expanduser("~/.bun/bin")
_GBRAIN = os.path.join(_BUN, "gbrain")

# (query, gold_slug, kind) — gold is the single page that best answers.
QUERIES: list[tuple[str, str, str]] = [
    ("Lin Zhao",                          "people/lin-zhao",             "exact"),
    ("Ridgeline Capital",                 "companies/ridgeline-capital", "exact"),
    ("Northstar Ventures",                "companies/northstar-ventures","exact"),
    ("Marcus Webb",                       "people/marcus-webb",          "exact"),
    ("dinner at Tartine",                 "meetings/tartine-dinner",     "exact"),
    ("who runs serving infrastructure",   "people/lin-zhao",             "semantic"),
    ("protein design foundation models",  "companies/helix-bio",         "semantic"),
    ("inference optimization startup",    "companies/quanta-labs",       "semantic"),
    ("early-stage bio funding round",     "deals/helix-series-a",        "semantic"),
    ("payments company angel investment", "companies/stripe",            "semantic"),
]

K = 3  # hit@K
_LINE = re.compile(r"^\[[-\d.]+\]\s+(\S+)\s+--")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = _BUN + os.pathsep + env.get("PATH", "")
    env.setdefault("GBRAIN_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gbrain")
    env.setdefault("OLLAMA_BASE_URL", "http://localhost:8000/v1")
    return env


def _ranked_slugs(cmd: str, query: str) -> list[str]:
    """Run `gbrain <cmd> <query> --json --limit 10`, return ordered slugs."""
    out = subprocess.run(
        [_GBRAIN, cmd, query, "--json", "--limit", "10"],
        capture_output=True, text=True, env=_env(),
    ).stdout
    slugs: list[str] = []
    for line in out.splitlines():
        m = _LINE.match(line.strip())
        if m:
            slugs.append(m.group(1))
    return slugs


def _rank_of(gold: str, slugs: list[str]) -> int | None:
    for i, s in enumerate(slugs, 1):
        if s == gold:
            return i
    return None


def main() -> None:
    methods = {"search (keyword)": "search", "query (hybrid-RRF)": "query"}
    agg: dict[str, dict] = {m: {"hits": 0, "rr": 0.0} for m in methods}
    print(f"{'query':<38}{'kind':<10}{'keyword':<12}{'hybrid-RRF':<12}")
    print("-" * 72)
    for q, gold, kind in QUERIES:
        row = f"{q:<38}{kind:<10}"
        for label, cmd in methods.items():
            rank = _rank_of(gold, _ranked_slugs(cmd, q))
            hit = rank is not None and rank <= K
            agg[label]["hits"] += int(hit)
            agg[label]["rr"] += (1.0 / rank) if rank else 0.0
            row += f"{('@' + str(rank)) if rank else 'MISS':<12}"
        print(row)
    n = len(QUERIES)
    print("-" * 72)
    print(f"\n{'method':<22}{'hit@'+str(K):<10}{'MRR':<8}")
    for m in methods:
        print(f"{m:<22}{agg[m]['hits']}/{n} ({agg[m]['hits']/n:.0%})  {agg[m]['rr']/n:.3f}")


if __name__ == "__main__":
    main()
```

**Walkthrough:**

- **Block 1 - QUERIES constant.** The list is typed as `list[tuple[str, str, str]]` and every entry carries a `kind` tag (`"exact"` vs `"semantic"`). The split is deliberate: exact-name queries favor FTS/keyword (token overlap is 1.0), semantic-paraphrase queries favor vector (no shared surface token). Without this split you cannot tell which retriever failed on which query class - an aggregate hit@3 hides cancellation between the two groups.
- **Block 2 - _env() injection.** Rather than assuming `gbrain` is on the user's login PATH, `_env()` prepends `~/.bun/bin` at call time and sets the two DB/embedding URLs with `setdefault` (so an existing env var is never clobbered). This keeps the script portable across machines without editing PATH in the shell profile.
- **Block 3 - _ranked_slugs().** The only output contract GBrain's CLI guarantees is the `[score] slug -- text` line format, so the function runs the subprocess and regex-parses stdout instead of relying on structured JSON. `--json --limit 10` is passed but the fallback parse handles cases where JSON framing is inconsistent across GBrain versions. Returning a plain `list[str]` (ordered slugs) keeps `_rank_of` decoupled from the retrieval path.
- **Block 4 - main() accumulator.** `agg` accumulates integer hit counts and float reciprocal-rank sums in one pass; MRR is computed at the end as `rr_sum / n` rather than averaging per-query, which avoids a div-by-zero edge case when `rank` is `None` (a miss contributes 0.0). The aligned `f-string` print format means the output table is copy-pasteable directly into `RESULTS.md` without reformatting.

### Phase 7 — Ground-Truth Hierarchy: memory-as-authoritative A/B [executed, measured]

**Goal:** leverage a principle from **ClaudioDrews/memory-os** — the *Ground-Truth Hierarchy*: injected memory is **authoritative**; an agent must not re-derive or re-fetch facts it already holds. memory-os names the anti-pattern **"memory-zero"** (re-establishing context from scratch every turn). GBrain is the authoritative store, so this is a natural fit: we A/B a 5-turn conversation that chains on overlapping entities (`Lin Zhao → Acme AI → its seed → investors`), comparing a memory-zero agent (re-query every turn) against a ground-truth agent (retrieve the subgraph once, inject it as authoritative, reuse).

> **Provenance (kept honest):** the *Ground-Truth Hierarchy* principle is **ClaudioDrews/memory-os**'s. The sibling heat/eviction mechanism (W3.5.95) comes from a *different* repo, **BAI-LAB/MemoryOS** — don't conflate them.

**When to use:** reach for `ground_truth_ab.py` when you need to measure the concrete cost of memory-zero vs ground-truth-authoritative memory on a real multi-turn conversation - specifically any time you have a chain of turns that share overlapping entities and you want numbers (retrieval calls, context tokens, coreference correctness) rather than intuition. Use it as a baseline template when introducing a new GBrain brain or a new entity-dense topic; its siblings (`eval_memory_policies.py`, `bench_strategies.ts`) benchmark retrieval arm strategy and eval scoring instead.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  subgraph MZ["Mode A — memory-zero"]
    A1["turn 1..5"] --> A2["fresh gbrain query<br/>per turn"]
    A2 --> A3["top-3 pages<br/>(this turn only)"]
    A3 --> A4["answer<br/>(no carried context)"]
  end
  subgraph GT["Mode B — ground-truth"]
    B1["retrieve subgraph<br/>ONCE"] --> B2["inject full pages<br/>as authoritative"]
    B2 --> B3["reuse across turns<br/>via history"]
    B3 --> B4["answer<br/>(coreference resolved)"]
  end
  MZ ~~~ GT
```

**Code:** `src/ground_truth_ab.py` (chat via VibeProxy→Haiku; retrieval + embeddings local):

```python
"""Phase 7 — Ground-Truth Hierarchy A/B (memory-os principle, leveraged).

Principle (ClaudioDrews/memory-os): injected memory is AUTHORITATIVE — an agent
must not re-derive or re-fetch facts it already holds. The anti-pattern memory-os
names is "memory-zero": re-establishing context from scratch every turn.

We test it as an A/B over the live GBrain brain — a 5-turn conversation whose
turns chain on overlapping entities (Lin Zhao → Acme AI → its seed → investors):

  - Mode A "memory-zero": every turn issues a FRESH `gbrain query`, fetches the
    top pages, and feeds only that turn's retrieval. Overlapping entities get
    re-retrieved, and per-turn retrieval variance lets the same fact drift.
  - Mode B "ground-truth": retrieve the conversation's subgraph ONCE, inject the
    full pages as authoritative context, and reuse them across turns via history.

Measures: retrieval calls, retrieved-context tokens, total LLM prompt tokens.
Chat LLM via VibeProxy (:8317 → Claude); retrieval + embeddings stay local (oMLX).

Two gotchas this script encodes (both cost a debugging round):
  1. `gbrain query --json` returns only a TRUNCATED snippet — useless as grounding.
     Pull full page bodies with `gbrain get <slug>`.
  2. VibeProxy injects a "you are Claude Code" identity that overrides the system
     role and makes the model REFUSE "questions about people." Frame the task as
     grounded document Q&A in the USER message; don't rely on the system prompt.
"""
from __future__ import annotations

import os
import re
import subprocess

from openai import OpenAI

_BUN = os.path.expanduser("~/.bun/bin")
_GBRAIN = os.path.join(_BUN, "gbrain")
_LINE = re.compile(r"^\[[-\d.]+\]\s+(\S+)\s+--")
_CHAT_MODEL = os.getenv("CHAT_MODEL", "claude-haiku-4-5-20251001")

# Turns deliberately chain on shared entities so a memory-holding agent can reuse.
TURNS = [
    "Who is Lin Zhao?",
    "What company does he lead, and what does it do?",
    "Who invested in that company's seed round?",
    "What other deals is that investor involved in?",
    "Summarize Lin Zhao's professional network in two sentences.",
]

# The instruction lives in the USER turn (system role is overridden by the proxy).
_MEMZERO_TMPL = (
    "You are answering questions from a personal knowledge base (markdown notes). "
    "Using ONLY the notes below, answer the question. If a fact is not in the notes, "
    "say you don't have it.\n\nNOTES:\n{ctx}\n\nQUESTION: {q}"
)
_GROUNDTRUTH_PREAMBLE = (
    "You are answering a short series of questions about a personal knowledge base. "
    "The NOTES below are AUTHORITATIVE ground truth — trust them, never contradict "
    "them, and do not ask to re-fetch anything already present. Answer concisely "
    "from the notes and the conversation so far.\n\nNOTES (authoritative):\n{ctx}"
)


def _server_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = _BUN + os.pathsep + env.get("PATH", "")
    env.setdefault("GBRAIN_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gbrain")
    env.setdefault("OLLAMA_BASE_URL", "http://localhost:8000/v1")
    return env


def _run(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True, env=_server_env()).stdout


def gbrain_query_slugs(q: str, limit: int) -> list[str]:
    """Hybrid retrieval — one call. Returns ranked slugs (snippets are too thin)."""
    slugs: list[str] = []
    for line in _run([_GBRAIN, "query", q, "--json", "--limit", str(limit)]).splitlines():
        m = _LINE.match(line.strip())
        if m:
            slugs.append(m.group(1))
    return slugs


def gbrain_get(slug: str) -> str:
    """Full page body — the actual grounding `query`'s snippet lacks."""
    body = _run([_GBRAIN, "get", slug])
    return "\n".join(ln for ln in body.splitlines() if not ln.startswith(("Starting", "[gbrain")))


def _context(slugs: list[str]) -> str:
    return "\n\n".join(gbrain_get(s) for s in slugs)


def _client() -> OpenAI:
    return OpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL", "http://localhost:8317/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY", "vibeproxy"),
    )


def _ask(client: OpenAI, messages: list[dict]) -> tuple[str, int]:
    r = client.chat.completions.create(model=_CHAT_MODEL, messages=messages, temperature=0)
    return (r.choices[0].message.content or "").strip(), (r.usage.prompt_tokens if r.usage else 0)


def run_memory_zero(client: OpenAI) -> dict:
    """Re-query + re-fetch every turn; feed only that turn's retrieval."""
    calls, ctx_chars, prompt_tokens, answers = 0, 0, 0, []
    for q in TURNS:
        ctx = _context(gbrain_query_slugs(q, limit=3))
        calls += 1
        ctx_chars += len(ctx)
        ans, ptok = _ask(client, [{"role": "user", "content": _MEMZERO_TMPL.format(ctx=ctx, q=q)}])
        prompt_tokens += ptok
        answers.append(ans)
    return {"calls": calls, "ctx_tokens": ctx_chars // 4, "prompt_tokens": prompt_tokens, "answers": answers}


def run_ground_truth(client: OpenAI) -> dict:
    """Retrieve the subgraph ONCE, inject full pages as authoritative, reuse."""
    ctx = _context(gbrain_query_slugs("Lin Zhao Acme AI seed round investors network", limit=6))
    calls, ctx_chars = 1, len(ctx)
    history: list[dict] = [{"role": "user", "content": _GROUNDTRUTH_PREAMBLE.format(ctx=ctx)},
                           {"role": "assistant", "content": "Understood — I'll answer from those notes."}]
    prompt_tokens, answers = 0, []
    for q in TURNS:
        history.append({"role": "user", "content": q})
        ans, ptok = _ask(client, history)
        prompt_tokens += ptok
        history.append({"role": "assistant", "content": ans})
        answers.append(ans)
    return {"calls": calls, "ctx_tokens": ctx_chars // 4, "prompt_tokens": prompt_tokens, "answers": answers}


def main() -> None:
    client = _client()
    a = run_memory_zero(client)
    b = run_ground_truth(client)

    def row(name: str, d: dict) -> str:
        return f"{name:<16}{d['calls']:<14}{d['ctx_tokens']:<16}{d['prompt_tokens']:<14}"

    print(f"{'mode':<16}{'retrievals':<14}{'retr. ctx tok':<16}{'LLM prompt tok':<14}")
    print("-" * 60)
    print(row("memory-zero", a))
    print(row("ground-truth", b))
    print(
        f"\nre-query waste avoided by treating memory as ground truth: "
        f"{a['calls'] - b['calls']} retrievals, ~{a['ctx_tokens'] - b['ctx_tokens']} retrieval-context tokens"
    )
    for i, q in enumerate(TURNS):
        print(f"\nQ{i + 1}: {q}")
        print(f"  [memory-zero ] {a['answers'][i][:170]}")
        print(f"  [ground-truth] {b['answers'][i][:170]}")


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **Block 1 — `gbrain_query_slugs` + `gbrain_get` (two-step retrieval).** A copy-paster's first instinct is to feed `gbrain query --json` straight to the LLM — but that output is ranked *snippets* (slug + first line), and the model correctly complains it "doesn't include the actual content." So we use `query` only to *rank* slugs, then `gbrain get <slug>` to pull full page bodies. Retrieval and grounding are two different calls.
- **Block 2 — instruction in the USER turn, not `system`.** VibeProxy fronts a Claude-Code identity that overrides the `system` role; with the instruction in `system`, the model refuses ("I'm Claude Code, I can't help with questions about people"). Moving the instruction + notes into the USER message reframes it as grounded document Q&A — which the same model answers happily.
- **Block 3 — the two policies.** `run_memory_zero` re-queries and re-fetches on *every* turn, passing only that turn's pages with no conversation history — so coreference ("he", "that company") has no antecedent and the fresh query can drift to the wrong entity cluster. `run_ground_truth` retrieves the subgraph *once*, injects the full pages as authoritative, and carries them in `history` — every later turn resolves against the same anchored context.
- **Block 4 — what's measured.** Retrieval *calls* (the expensive embedding+search+fetch round-trip), retrieval-context *tokens* (`chars//4` proxy), and total LLM `prompt_tokens` from `usage`. The split matters: the win is in retrieval, not total tokens.

**Result** (live 19-page brain, VibeProxy→Haiku 4.5, 2026-06-05):

| mode | retrievals | retr. ctx tokens | LLM prompt tokens |
|---|---|---|---|
| memory-zero | 5 | 11,167 | 22,254 |
| **ground-truth** | **1** | **2,233** | 23,001 |

The headline number (4 retrievals / ~8.9K retrieval-tokens avoided) understates the real finding, which is in the **answers**: memory-zero **failed 3 of 5 turns** — Q2 and Q4 lost coreference ("you haven't specified who 'he' is"), and **Q3 retrieved the wrong company** (Quanta/Ridgeline instead of Acme/Northstar) because a standalone query for "*that company's* seed round" has no anchor and drifts. Ground-truth answered all five correctly, resolving every "he/that company/that investor" against the injected subgraph. Note the honest nuance: total LLM prompt tokens are **roughly equal** (ground-truth's accumulating history ≈ memory-zero's repeated per-turn context) — the win is retrieval cost *and correctness*, not raw token count.

`★ Insight ─────────────────────────────────────`
- **memory-zero's failure mode isn't cost — it's drift + lost coreference.** Re-retrieving per turn means "that company" embeds with no anchor and lands on the wrong cluster; the agent then answers confidently about the wrong entity. Treating memory as authoritative + persistent is what keeps multi-turn reasoning *correct*, which is exactly memory-os's Ground-Truth Hierarchy claim — here measured on a real brain.
- **Don't oversell the token math.** A naive write-up would claim "ground-truth is cheaper." It isn't, on total prompt tokens — history accumulation roughly cancels the per-turn-retrieval savings. The defensible claims are: 80% less *retrieval* work, and a correctness lift on coreference-heavy conversations. Precision here is the difference between a real result and a demo-gamed one.
`─────────────────────────────────────────────────`

**Deliverable:** `src/ground_truth_ab.py` + the table above (also in the lab's `RESULTS.md`).

### Phase 8 — Large-corpus ingest: per-file streaming + checkpoint + merge [executed, measured]

**Goal:** scale the Phase 3 agent to a *large* number of files. Phase 3 warms one extraction over **all** files concatenated — fine for 8 files, fatal at scale: the single prompt blows the context window and is un-resumable. The fix is a different shape, not a bigger prompt.

**The three scale problems (the 30s sandbox limit is *not* the main one):**
1. **Extraction context wall** — you cannot put thousands of files in one LLM call.
2. **Cross-file entity dedup** — the same entity appears in many files; one-big-prompt merged them "for free," per-file extraction can't.
3. **Throughput** — at thousands of files the ceiling is embedding calls + DB upserts, not the agent loop.

**The large-file architecture at a glance — each scale problem maps to one mechanism:**

| Scale problem                                             | Solution                                                                                                                                                                        |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Extraction context wall (can't fit N files in one prompt) | per-file extraction, driver-side                                                                                                                                                |
| One *file* too big for the extract context                | split into deterministic line-aligned chunks `<file>#0/#1/…` (`CHUNK_CHARS`); resume per chunk                                                                                  |
| 30s agent sandbox                                         | extraction leaves the sandbox; agent only does bounded `put_page` (the 30s is `executor_kwargs={"timeout_seconds": N}`-configurable, but a no-kill thread timeout — see BCJ 12) |
| Run dies on file 4,000 = lose everything                  | TWO disk checkpoints — extraction (`.ingest_stage/<file>.json`) + writes (`.ingest_written.json`) → resume re-does nothing already done                                         |
| One page so big its single embed nears 30s                | write that page **driver-side** (no sandbox), not via the agent                                                                                                                 |
| Same entity across many files                             | group on disk + one `merge_from_disk()` (deferred dedup)                                                                                                                        |
| Resume re-runs the (LLM) merge every time                 | cache merged canonical (`.ingest_merged.json`) keyed by a stage fingerprint → unchanged stage = skip re-merge                                                                   |
| Wasted embedding on throwaway staging                     | stage on DISK (no embed); GBrain embeds only canonical → **each entity embedded ONCE**                                                                                          |
| Throughput at thousands of files                          | batch embeds + bulk upsert (next ceiling beyond this lab)                                                                                                                       |

**The shape:** stream **per file**, stage on **disk**, merge, then write **only canonical** pages to GBrain.
- **Extraction is driver-side** (no 30s sandbox). A file bigger than the extract context is **split into deterministic, line-aligned chunks** `<file>#0/#1/…` (`CHUNK_CHARS`); a small file is just a 1-chunk file. So "many files" and "one huge file" are the same problem — the unit is a *chunk*.
- **Staging is on DISK** (`~/brain/.ingest_stage/<file>#<idx>.json`), **not in GBrain** — so the throwaway intermediate is never embedded. A staged chunk JSON IS the checkpoint: re-run skips chunks already staged (`rm -rf` the dir to restart). A crash mid-file re-extracts only the unfinished chunk.
- **`merge_from_disk()`** groups staged pages by entity across files, merges multi-file entities (one LLM call each — the *only* place merge cost is paid), and yields canonical pages.
- The **agent writes only the CANONICAL pages** via `put_page` over MCP, in bounded batches → **each entity embedded exactly once**. (The agent still uses GBrain as memory — it writes the finals and queries them; only the disposable staging left the store.)
- A **write checkpoint** (`~/brain/.ingest_written.json`) records a canonical slug **only after `_verify_written` confirms its page is actually in GBrain** (verify-then-mark) — so a silently-failed `put_page` stays un-checkpointed and retries; the checkpoint can never claim a page that isn't there. A resumed run re-embeds **only un-written pages**, so "embed once" survives a crash. Oversized pages (> `BIG_PAGE_CHARS`) skip the agent and write **driver-side** (no 30s limit on a single big embed).
- Then **`reconcile_graph()`** wires the `[[wikilinks]]`.

**The pipeline is 4 derived layers — each a rebuildable cache of the one above.** This is what makes the whole thing resumable *and* crash-recoverable: losing any derived layer is regenerated from the layer above; the only unrecoverable loss is the source corpus itself.

```text
source files            ~/brain/sources/*                 ← ground truth (only true loss)
  └─ stage chunks        ~/brain/.ingest_stage/<file>#<idx>.json   ← gone → re-extract from source
       └─ merged canonical  ~/brain/.ingest_merged.json            ← gone/stale → re-merge from stage
            └─ embedded     GBrain pages (Postgres+pgvector)       ← gone → re-write from canonical
```

Each layer has a checkpoint so resume *skips* what's already built; if a layer is *missing*, it's *rebuilt* from the one above. The full state machine, per unit:

| derived layer present? | recorded in its checkpoint? | action on resume |
|---|---|---|
| yes | yes | skip (already done) |
| yes | no | (re-)build from this layer |
| **no** | yes | skip — done, content was discarded (fine) |
| **no** | no | **rebuild from the layer ABOVE** (e.g. stage gone + unwritten → re-extract from source) — *not* a dead end |

Drawn **C4-style, left→right**: each **layer is a colored box** (bold title · «role» · `[tool]` · what it does + its on-disk checkpoint). The **pink edge labels are the resume rule** — work is skipped when that layer's checkpoint says it's already done. Dark blue = the operator (person); blue = pipeline containers (Layers 1–3, inside the dashed system boundary); grey = external (Layer 0 source of truth, GBrain store). Reads as one pipeline left→right: `ingest → stage → merge → embed → query`. *(Wide diagram — scroll horizontally; `useMaxWidth:false` keeps the text at full size rather than shrinking to fit the column.)*

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'26px','lineColor':'#888','primaryBorderColor':'#888'}, 'flowchart':{'useMaxWidth':false,'nodeSpacing':38,'rankSpacing':55,'padding':14}}}%%
flowchart LR
  OP["<b>Operator</b> «person»<br/>re-runs after a crash<br/>resumes from checkpoint"]
  L0["<b>Layer 0 · Source</b> «external»<br/>~/brain/sources/*<br/>ground truth"]
  subgraph PIPE["Resumable Ingest Pipeline «system»"]
    direction LR
    L1["<b>Layer 1 · Staged chunks</b><br/><i>extract_file · no embed</i><br/>big files → chunks<br/>ckpt .ingest_stage/<br/>{file}#idx.json"]
    L2["<b>Layer 2 · Merged</b><br/><i>merge_from_disk · LLM</i><br/>entity merged<br/>across files<br/>cache .ingest_merged.json"]
    L3["<b>Layer 3 · Embedded</b><br/><i>put_page · embed ONCE</i><br/>verify-then-mark<br/>ckpt .ingest_written.json"]
    L1 -->|"merge by entity<br/>skip if cached"| L2
    L2 -->|"write canonical<br/>skip if written"| L3
  end
  GB[("<b>GBrain store</b> «external»<br/>Postgres + Qdrant<br/>pages + wikilink edges")]
  Q(["query"])
  OP -->|ingest| L0
  L0 -->|"per-file chunk<br/>skip if staged"| L1
  L3 -->|"put_page +<br/>reconcile_graph"| GB
  GB -->|"after<br/>reconcile"| Q
  classDef person fill:#08427b,stroke:#052e56,color:#fff;
  classDef ext fill:#8a8a8a,stroke:#5f5f5f,color:#fff;
  classDef cont fill:#438dd5,stroke:#2e6295,color:#fff;
  class OP person
  class L0,GB ext
  class L1,L2,L3 cont
```

`resumable_ingest.py` is the large-corpus entry point. It replaces the single-prompt ingest with a four-phase pipeline - extract per file chunk to disk, merge across files, write only canonical pages to GBrain, reconcile - so each entity is embedded exactly once and the run is resumable at every expensive boundary.

**When to use:** reach for `resumable_ingest.py` (instead of `ingest_agent.py`) when the source corpus is too large for a single extract call, spans many files that mention the same entities, or must survive crashes without re-doing expensive work; use `ingest_agent.py` for small, fresh, single-session corpora where simplicity matters more than throughput.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  SRC[("~/brain/sources/*")]
  FILES["_files()<br/>glob + decode"]
  CHUNK["_chunk_text()<br/>line-aligned split<br/>at CHUNK_CHARS"]
  EXTRACT["extract_file()<br/>driver-side LLM<br/>JSON pages"]
  STAGE[(".ingest_stage/<br/>{stem}#{idx}.json")]
  SKIP1{"chunk staged?<br/>skip"}
  STAGEKEY["_stage_key()<br/>name+mtime+size<br/>fingerprint"]
  MERGECACHE{"cache HIT?<br/>.ingest_merged.json"}
  MERGE["merge_from_disk()<br/>group by slug<br/>across files"]
  MERGEOP["_merge()<br/>one LLM call<br/>per multi-file entity"]
  CANONICAL[["canonical pages"]]
  WRITTEN[(".ingest_written.json")]
  PENDING{"slug written?<br/>skip"}
  BIG{"content ><br/>BIG_PAGE_CHARS?"]
  DRIVER["_gbrain_put()<br/>subprocess driver-side"]
  AGENT["CodeAgent.run()<br/>WRITE_TASK<br/>batches of BATCH"]
  VERIFY["_verify_written()<br/>psql pages table<br/>existence check"]
  MARK["_mark_written()<br/>verify-then-mark"]
  RECONCILE["reconcile_graph()<br/>wire wikilinks"]
  EVAL["run_auto_eval()<br/>golden eval + policy"]
  QUERY["agent.run()<br/>QUERY_TASK"]

  SRC --> FILES
  FILES --> CHUNK
  CHUNK --> SKIP1
  SKIP1 -->|"not staged"| EXTRACT
  EXTRACT --> STAGE
  SKIP1 -->|"already staged"| STAGE
  STAGE --> STAGEKEY
  STAGEKEY --> MERGECACHE
  MERGECACHE -->|"HIT: load cache"| CANONICAL
  MERGECACHE -->|"MISS: re-merge"| MERGE
  MERGE --> MERGEOP
  MERGEOP --> CANONICAL
  CANONICAL --> PENDING
  PENDING -->|"not written"| BIG
  PENDING -->|"already written"| WRITTEN
  BIG -->|"oversized"| DRIVER
  BIG -->|"normal"| AGENT
  DRIVER --> VERIFY
  AGENT --> VERIFY
  VERIFY --> MARK
  MARK --> WRITTEN
  WRITTEN --> RECONCILE
  RECONCILE --> EVAL
  EVAL --> QUERY
```
*`resumable_ingest.py` internal call flow: four phases (extract-to-disk, merge, agent write with verify-then-mark, reconcile+eval+query); pink decision nodes are the resume gates - each one skips work already done.*

**Code:** `src/resumable_ingest.py`:

```python
"""W3.5.96 — LARGE-CORPUS ingest: per-file streaming + on-DISK staging + final
merge, so GBrain (the embedded store) only ever sees CANONICAL pages — each entity
is embedded exactly once. The scale variant of ingest_agent.py.

Earlier draft staged into GBrain itself (one put_page per file-variant). That made
the store embed every variant and then throw it away at merge — ~71% wasted
embedding on the 8-file run (46 staging embeds for 19 final pages). Embedding is
the throughput ceiling at scale, so staging must NOT touch the embedded store.

This version stages on disk (cheap, no embedding) and only writes finals to GBrain:

  driver, per file (resumable — skip files already staged on disk):
    pages = extract_file(file)                 # DRIVER-side LLM (no 30s sandbox)
    write pages -> ~/brain/.ingest_stage/<file>.json   # disk staging, NO embedding
  merge_from_disk(): group by entity across files, merge multi-file entities (one
    LLM call each) -> a list of CANONICAL pages
  agent: put_page each canonical page over MCP, in bounded batches  # embedded ONCE
  reconcile_graph(); run_auto_eval(); query   # same WRITE→RECONCILE→AUTO-EVAL→READ as ingest_agent

The "agent uses GBrain as memory" lesson is intact: the agent still WRITES the
canonical pages and QUERIES them over MCP. Only the throwaway intermediate left
the embedded store.

A big file is split into deterministic chunks (`<file>#0`, `#1`, … by CHUNK_CHARS,
line-aligned), each its own staging unit — so "one file too big for the extract
context" is handled, and resume works at chunk granularity.

Each derived layer is a cache of the one above, rebuildable from it — so resume
re-does no expensive work, and losing a derived layer is recoverable, not fatal:
  source files (ground truth) → stage chunks → merged canonical → embedded
  - EXTRACTION: a file CHUNK with a stage JSON (`<file>#<idx>.json`) is skipped;
    a MISSING chunk is re-extracted from its source file (not a dead end).
  - MERGE: cached to ~/brain/.ingest_merged.json keyed by a stage fingerprint;
    unchanged staging → load cache, skip the (LLM-costly) re-merge.
  - WRITES: ~/brain/.ingest_written.json records written canonical slugs — but a
    slug is recorded only after its page is VERIFIED present in GBrain
    (verify-then-mark), so a silently-failed write stays un-checkpointed and is
    retried on resume. A resumed run re-embeds ONLY un-written pages — "embed
    once" survives a crash; the checkpoint can never claim a page that isn't there.
Oversized pages (> BIG_PAGE_CHARS) are written driver-side (no 30s sandbox) since
one such page's single embed could approach the agent's per-step limit.

Run: python src/resumable_ingest.py   (re-run to resume)
Restart: rm -rf ~/brain/.ingest_stage ~/brain/.ingest_merged.json ~/brain/.ingest_written.json
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess

from mcp import StdioServerParameters
from openai import OpenAI
from smolagents import CodeAgent, OpenAIServerModel, ToolCollection, tool

from ingest_agent import (
    NEEDED_TOOLS, QUERY_TASK, _EXTRACT_PROMPT, _GBRAIN, _server_env,
    reconcile_graph, run_auto_eval,
)

SOURCES = pathlib.Path(os.path.expanduser("~/brain/sources"))
STAGE_DIR = pathlib.Path(os.path.expanduser("~/brain/.ingest_stage"))   # disk staging
MERGED = pathlib.Path(os.path.expanduser("~/brain/.ingest_merged.json"))  # merge cache
WRITTEN = pathlib.Path(os.path.expanduser("~/brain/.ingest_written.json"))  # write checkpoint
BATCH = 8                 # canonical pages per agent write call (bounded < 30s)
BIG_PAGE_CHARS = 8000     # bigger pages are written driver-side (one page's embed may near 30s)
CHUNK_CHARS = 6000        # a file > this is split into <file>#0, #1, … (extract context budget)

_CURRENT: list = []       # the current write batch; the agent's tool reads this


def _files() -> list[tuple[str, str]]:
    """(stem, text) for every readable source file (skip dotted parts + binaries)."""
    out = []
    for f in sorted(SOURCES.rglob("*")):
        if not f.is_file() or any(part.startswith(".") for part in f.relative_to(SOURCES).parts):
            continue
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        out.append((str(f.relative_to(SOURCES)).replace("/", "-").rsplit(".", 1)[0], text))
    return out


def _llm() -> OpenAI:
    return OpenAI(base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                  api_key=os.getenv("LLM_API_KEY", "dummy"))


# ── write checkpoint (so a resumed run re-embeds only un-written pages) ──────
def _written_done() -> set[str]:
    if WRITTEN.exists():
        return set(json.loads(WRITTEN.read_text()).get("done", []))
    return set()


def _mark_written(slugs: list[str]) -> None:
    done = _written_done() | set(slugs)
    WRITTEN.write_text(json.dumps({"done": sorted(done)}))


def _gbrain_put(slug: str, content: str) -> None:
    """Driver-side write (no 30s sandbox) — used for oversized pages whose single
    embed could approach the agent's per-step limit."""
    subprocess.run([_GBRAIN, "put", slug], input=content, capture_output=True,
                   text=True, env=_server_env())


def _verify_written(slugs: list[str]) -> list[str]:
    """Return the subset of `slugs` that ACTUALLY landed in GBrain. Existence in
    `pages` (deleted_at IS NULL) is the proof of a successful put_page (embed +
    upsert); only verified slugs get checkpointed, so a silently-failed write
    stays un-checkpointed → retried on resume. The invariant: a slug is in the
    write checkpoint IFF its page is really in the store."""
    if not slugs:
        return []
    cont = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                          capture_output=True, text=True).stdout
    name = next((n for n in cont.splitlines() if "gbrain-pg" in n), "gbrain-pg")
    arr = "{" + ",".join(slugs) + "}"   # slugs are kebab + '/', safe in a PG array literal
    sql = f"select slug from pages where deleted_at is null and slug = any('{arr}');"
    out = subprocess.run(["docker", "exec", "-i", name, "psql", "-U", "postgres",
                          "-d", "gbrain", "-tAc", sql], capture_output=True, text=True).stdout
    got = {s.strip() for s in out.splitlines() if s.strip()}
    return [s for s in slugs if s in got]


# ── per-file extraction → DISK staging (no embedding) ───────────────────────
def extract_file(text: str) -> list:
    """LLM-extract ONE file into pages (canonical base slugs — no DB namespacing
    needed; the disk filename records which file)."""
    resp = _llm().chat.completions.create(
        model=os.getenv("LLM_MODEL", "Qwen2.5-Coder-14B-Instruct-MLX-4bit"),
        messages=[{"role": "user", "content": _EXTRACT_PROMPT.replace("{raw}", text)}],
        temperature=0.0, max_tokens=4000, response_format={"type": "json_object"})
    data = json.loads(resp.choices[0].message.content or "{}")
    return [p for p in data.get("pages", []) if p.get("slug") and p.get("content")]


def _chunk_text(text: str, max_chars: int) -> list[str]:
    """Split into ≤max_chars chunks on LINE boundaries (never mid-line). A file
    that fits returns one chunk; a big file returns several. Deterministic: the
    same input always yields the same chunks, so chunk N == the same bytes."""
    chunks, cur, n = [], [], 0
    for line in text.splitlines(keepends=True):
        if n + len(line) > max_chars and cur:
            chunks.append("".join(cur)); cur, n = [], 0
        cur.append(line); n += len(line)
    if cur:
        chunks.append("".join(cur))
    return chunks or [""]


def stage_all() -> None:
    """Extract every not-yet-staged file CHUNK to ~/brain/.ingest_stage/<stem>#<idx>.json.

    A file > CHUNK_CHARS is split into deterministic chunks (extract context budget);
    each chunk is its own staging unit. Resumable at CHUNK granularity for free —
    the existing 'skip if the JSON exists' check now skips already-staged chunks,
    so a crash mid-file re-extracts only the unfinished chunk(s). Cross-chunk
    entities are reunited later by merge_from_disk (same path as cross-file)."""
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    for stem, text in _files():
        chunks = _chunk_text(text, CHUNK_CHARS)
        for idx, chunk in enumerate(chunks):
            out = STAGE_DIR / f"{stem}#{idx}.json"
            if out.exists():
                continue
            pages = extract_file(chunk)
            out.write_text(json.dumps(pages))
            tag = f"{stem}#{idx}" + (f" of {len(chunks)}" if len(chunks) > 1 else "")
            print(f">>> staged {tag} ({len(chunk)} chars): {len(pages)} pages (disk, no embedding)")


# ── merge across files (disk, no DB reads) ──────────────────────────────────
def _merge(base: str, contents: list[str]) -> str:
    """Merge per-file variants of one entity into a single page (one LLM call)."""
    joined = "\n\n--- VARIANT ---\n\n".join(contents)
    prompt = (
        f"These are {len(contents)} notes about the SAME entity ({base}), from "
        "different source files. Merge into ONE GBrain page with the exact two-layer "
        "shape (summary with [[dir/slug]] wikilinks, then a line that is exactly "
        "`---`, then `## Timeline` with the UNION of all timeline lines, deduplicated, "
        "chronological). Keep every distinct fact. Output ONLY the merged markdown.\n\n"
        f"{joined}"
    )
    resp = _llm().chat.completions.create(
        model=os.getenv("LLM_MODEL", "Qwen2.5-Coder-14B-Instruct-MLX-4bit"),
        messages=[{"role": "user", "content": prompt}], temperature=0.0, max_tokens=2000)
    return (resp.choices[0].message.content or contents[0]).strip()


def _stage_key() -> str:
    """Fingerprint of the staged chunks (name + mtime + size). If it's unchanged
    since the cached merge, the merge result is still valid — so resume can skip
    the (LLM-costly) re-merge. Any re-extracted chunk changes its mtime → miss."""
    parts = []
    for f in sorted(STAGE_DIR.glob("*.json")):
        st = f.stat()
        parts.append(f"{f.name}:{int(st.st_mtime)}:{st.st_size}")
    return "|".join(parts)


def merge_from_disk() -> list:
    """Group staged pages by entity across all files; return CANONICAL pages.
    Single-file entities pass through; multi-file entities are merged once (LLM).

    Cached: the merge (its per-entity LLM calls) is expensive, so the result is
    cached to MERGED keyed by the stage fingerprint. A resume whose staging is
    unchanged loads the cache and skips re-merging; if any chunk was re-extracted
    (fingerprint differs) it re-merges and re-caches."""
    key = _stage_key()
    if MERGED.exists():
        cached = json.loads(MERGED.read_text())
        if cached.get("key") == key:
            canonical = cached["canonical"]
            print(f">>> merge cache HIT: {len(canonical)} canonical (skipped re-merge)")
            return canonical

    groups: dict[str, list[str]] = {}
    for jf in sorted(STAGE_DIR.glob("*.json")):
        for p in json.loads(jf.read_text()):
            groups.setdefault(p["slug"], []).append(p["content"])
    canonical, merged = [], 0
    for slug, contents in groups.items():
        content = contents[0] if len(contents) == 1 else _merge(slug, contents)
        if len(contents) > 1:
            merged += 1
        canonical.append({"slug": slug, "content": content})
    MERGED.write_text(json.dumps({"key": key, "canonical": canonical}))
    print(f">>> merge_from_disk: {len(canonical)} canonical ({merged} merged from >1 file), cached")
    return canonical


@tool
def current_pages() -> list:
    """Return the current batch of canonical pages ({slug, content}) for the agent
    to write. The driver sets this before each agent.run."""
    return _CURRENT


WRITE_TASK = """Write the current pages using ONLY the provided tools:
1. pages = current_pages()
2. for each page in pages: call put_page(slug=page["slug"], content=page["content"])
3. call final_answer with how many you wrote.
"""


def main() -> None:
    server = StdioServerParameters(command=_GBRAIN, args=["serve"], env=_server_env())
    model = OpenAIServerModel(
        model_id=os.getenv("LLM_MODEL", "Qwen2.5-Coder-14B-Instruct-MLX-4bit"),
        api_base=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
        api_key=os.getenv("LLM_API_KEY", "dummy"))

    global _CURRENT
    # 1. EXTRACT every file to disk staging (resumable, no embedding).
    stage_all()
    # 2. MERGE across files → canonical pages (driver-side, no DB).
    canonical = merge_from_disk()

    with ToolCollection.from_mcp(server, trust_remote_code=True) as tc:
        mcp_tools = [t for t in tc.tools if t.name in NEEDED_TOOLS]
        agent = CodeAgent(
            tools=[current_pages, *mcp_tools], model=model, max_steps=3,
            use_structured_outputs_internally=True, verbosity_level=1)

        # 3. WRITE canonical pages to GBrain — embedded EXACTLY ONCE, and the
        # write checkpoint means a resumed run re-embeds only un-written pages.
        written = _written_done()
        pending = [p for p in canonical if p["slug"] not in written]
        print(f">>> {len(canonical)} canonical, {len(canonical) - len(pending)} "
              f"already written (resume), {len(pending)} to write")

        # Oversized pages → driver-side (a single big embed could near the 30s
        # sandbox limit); normal pages → agent, in bounded batches.
        big = [p for p in pending if len(p["content"]) > BIG_PAGE_CHARS]
        small = [p for p in pending if len(p["content"]) <= BIG_PAGE_CHARS]
        for p in big:
            _gbrain_put(p["slug"], p["content"])
            _mark_written(_verify_written([p["slug"]]))  # checkpoint ONLY if it landed
            print(f">>> big page driver-side: {p['slug']} ({len(p['content'])} chars)")
        for i in range(0, len(small), BATCH):
            batch = small[i:i + BATCH]
            _CURRENT = batch
            print(f">>> write batch {i // BATCH + 1} ({len(batch)} pages) -> "
                  + str(agent.run(WRITE_TASK)))
            # Verify-then-mark: checkpoint ONLY slugs confirmed present in GBrain.
            # A silently-failed put_page stays un-checkpointed → retried on resume.
            landed = _verify_written([p["slug"] for p in batch])
            _mark_written(landed)
            if len(landed) < len(batch):
                missing = sorted(set(p["slug"] for p in batch) - set(landed))
                print(f">>> WARNING: {len(missing)} page(s) did not land, left un-checkpointed "
                      f"(retry on resume): {missing}")

        # 4. RECONCILE links, then the agent queries its memory.
        print(">>> reconcile graph: " + reconcile_graph())

        # 4.5 AUTO-EVAL — retrieval-health + search-policy after every ingest
        # (best-effort; never breaks the ingest). golden_eval.json → policy_eval.ts,
        # else auto_eval.ts. Writes results/search_policy.json. Same hook as the
        # small-corpus path (ingest_agent.py), so the scale path self-tunes too.
        print(">>> auto-eval: " + run_auto_eval())

        answer = agent.run(QUERY_TASK)
        print("\n>>> agent final answer:\n" + str(answer))


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **Block 1 — `_files()` skips dotted *path parts*, not just dotted filenames.** A real source directory accumulates `.DS_Store` (binary → `UnicodeDecodeError`) and, here, `.omc-state/` *directories* a tool wrote in. Skipping `f.name.startswith(".")` misses files *inside* a dotted dir; `any(part.startswith("."))` over the relative parts catches both (BCJ Entry 13).
- **Block 2 — extraction is driver-side, writes are agent-side; big files chunk.** `extract_file` runs in `main()` (no sandbox), so a per-file (or per-chunk) LLM call can take as long as it needs; the agent only loops `put_page` (bounded, never near 30s). `_chunk_text` splits a file over `CHUNK_CHARS` into deterministic line-aligned chunks so even one huge file fits the extract context; each chunk stages independently. This is the inversion that kills the timeout: the slow thing leaves the sandbox, the bounded thing stays.
- **Block 3 — disk staging defers the dedup AND keeps it out of the embedded store.** Each file's pages go to `~/brain/.ingest_stage/<file>.json` — no embedding. `merge_from_disk` groups by base slug across files; only entities in >1 file pay an LLM merge, singletons pass through. GBrain only ever sees the canonical result.
- **Block 4 — TWO disk checkpoints, because the cost lives in two phases.** Extraction is checkpointed per file **chunk** (skip staged `<file>#<idx>.json`); writes are checkpointed per canonical slug (`.ingest_written.json`). Both expensive ops — the per-chunk LLM extract and the per-page embed — are protected, so a resumed run re-does *neither*. Idempotency alone wasn't enough: without the write checkpoint a crash mid-write re-embeds every page on resume, silently breaking "embed once."
- **Block 5 — verify-then-mark: the checkpoint can't lie.** A slug enters `.ingest_written.json` only after `_verify_written` confirms its page is actually in `pages` (existence == a successful embed+upsert). Marking a whole batch right after `agent.run` returned would *trust the agent loop* — a silently-swallowed `put_page` error would checkpoint a page that never landed, and resume would skip it forever. Verify-then-mark makes the invariant exact: **a slug is in the checkpoint iff its page is really in the store**, so an un-landed page stays un-checkpointed and retries.
- **Block 6 — the merge is cached, keyed by a stage fingerprint.** Resume re-reads stage chunks to rebuild `canonical` — but the merge's per-entity LLM calls are expensive, so `merge_from_disk` caches its result to `.ingest_merged.json` under `_stage_key()` (each chunk's name+mtime+size). Unchanged staging → cache HIT, skip the re-merge entirely; re-extract any chunk and its mtime changes → fingerprint differs → MISS → re-merge + re-cache. The fingerprint is the invalidation: the cache is valid exactly while its inputs are.

**Result (measured, 8-file corpus, 2026-06-05):**

```text
staged 8 files to disk (no embedding)
merge_from_disk: 18 canonical (14 merged from >1 file)
write batch 1/2/3: 8 + 8 + 2 = 18 pages (embedded ONCE each)
reconcile graph: 23 pages, 73 links
staging_in_db = 0          # the throwaway staging never hit the embedded store
query -> people/sam-okafor (top hit)
```

**0 sandbox timeouts; embedding calls 65 → 18.** Two proofs the design is right: (1) **`14 merged from 19 entities`** — 14 entities spanned multiple files and were consolidated into one canonical page each (the cross-file dedup one-big-prompt did implicitly, now explicit in `merge_from_disk`); (2) **`staging_in_db = 0`** — the disposable per-file variants never touched GBrain, so each entity is embedded exactly once instead of once-per-file-mention.

**Resume proof (write checkpoint):**
```text
run #1:  18 canonical, 0 already written, 18 to write   → .ingest_written.json = 18 slugs
run #2:  18 canonical, 18 already written (resume), 0 to write   → 0 write batches, 0 re-embeds
```
The second run re-embeds nothing — "embed once" holds across a crash, not just an uninterrupted run.

**Big-file chunk resume (one file too big for the extract context):** a synthetic 13.9 KB file → `_chunk_text` → 3 chunks [5937, 5941, 1984] (≤budget, lossless, line-aligned, deterministic).
```text
RUN 1 (fresh):  staged #0:13, #1:13, #2:10 pages
delete #1 (simulate crash)
RUN 2 (resume): skip #0, staged #1, skip #2     # only the lost chunk re-extracts
13 entities span >1 chunk (sam-okafor/lin-zhao/… in [0,1,2]) → merge_from_disk consolidates
```

`★ Insight ─────────────────────────────────────`
- **At scale the 30s sandbox was a red herring.** The real walls are the *extraction context limit*, *cross-file dedup*, and *embedding throughput*. Moving extraction to the driver dissolves the timeout as a side effect; the architecture is driven by those three, not by the sandbox.
- **Staging belongs in a cheap, disposable layer — not the embedded store.** v1 staged into GBrain and embedded every file-variant, then deleted them at merge: ~71% wasted embedding (65 calls for 18 final pages). Disk staging drops that to 18 — embed only the canonical. Don't make a throwaway intermediate pay the final state's cost; embedding is the one expensive op here, so optimize against *embedding count*, not DB writes.
- **`merge_from_disk` is the dedup-on-write pattern, deferred.** "Entity in file 7 already exists from file 2 → merge" is exactly `dedup_synthesis.decide_action` (W3.5.8/3.5.9). Batched post-pass vs on-every-write trades freshness for far fewer LLM calls — only multi-file entities merge. Same lesson, different lifecycle position ([[Engineering Decision Patterns#Pattern 22 — Lifecycle Position Matters (early-binding vs late-binding for pipeline primitives)|Pattern 22]]).
- **The teaching point survives the optimization.** The agent still writes the canonical pages and queries them over MCP — it uses GBrain as memory. Only the disposable staging moved to disk. Efficiency and the "agent-uses-GBrain" lesson aren't in tension; the *query* is what needs GBrain, and that never moved.
- **Checkpoint at the unit of *expensive work*, not just the loop boundary.** The first cut checkpointed only extraction (per file) and leaned on `put_page` idempotency for the rest — but idempotent ≠ free: a resumed write re-embeds everything. The fix was a *second* checkpoint at the write/embed boundary. Rule: every expensive op needs its own resume marker; "the writes are idempotent" hides a full re-embed behind a true-but-irrelevant claim.
`─────────────────────────────────────────────────`

**Deliverable:** `src/resumable_ingest.py` + the measured run above (also in the lab's `RESULTS.md`).

**Run the tests** — 17 deterministic tests lock the resume machinery (chunker: ≤budget/lossless/line-aligned/deterministic; dotted-path skip; write checkpoint + resume filter; oversized split; cross-chunk merge; merge-cache HIT/MISS; verify-gate; extract-cache; the `[score] slug -- text` parser). No LLM (temp dirs + stubbed `_merge`/`OpenAI`); one DB-gated integration test.

```bash
# from the lab root. NOTE: use `python -m pytest`, not plain `uv run pytest` —
# the latter resolves the wrong interpreter; this runs pytest in the project
# venv where smolagents/mcp/openai are installed.
uv run --with pytest python -m pytest tests/ -v
# → 17 passed   (test_resumable_ingest.py · test_ingest_agent.py · test_parsers.py)
```

### Phase 9 — A corpus-adaptive search policy, tuned on a real golden eval set [executed, measured]

**Goal:** make the agent's retrieval strategy **self-tune to the corpus**. After every ingest, score the three retrieval arms (keyword / vector / hybrid) against a **fixed golden set of real, labeled questions**, write the winning arm to a policy artifact, and route subsequent agent queries through it. Because the eval re-runs as the brain grows, the policy **adapts to drift** — search quality tracks the corpus without hand-tuning. This turns Phase 6's one-off finding ("the right arm is query/corpus-shape dependent") into a running, self-correcting control loop.

> **The policy MUST come from real questions — the rejected first cut.** The first
> version generated *known-item* queries automatically: sample a page, use its
> **title** as the query, gold = that page. It's label-free and convenient — and
> **wrong as a policy source.** On the 10-K it selected `keyword` (titles are
> keyword-friendly); but real financial questions made keyword the *worst* arm by
> ~5× (see the comparison below). A policy is only as trustworthy as the
> representativeness of its eval queries. So known-item is demoted to a **cold-start
> fallback** (better than nothing on a brand-new brain) + a regression guardrail,
> and a **golden set of real, labeled questions is the policy source.** (Bad-Case
> Entry 20.)

> **Why an actuator at all?** Stock `gbrain query`/`search` are hybrid-only (Entry 8) —
> there is no GBrain knob for "default strategy = keyword." So the apply step governs
> only the path *we* own (the agent's retrieval call) via a small wrapper. It steers
> the agent, not the stock CLI — a GBrain surface constraint, named honestly.

The loop — **measure → decide → apply**, re-fired on every ingest, so the policy tracks the corpus on its own:

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  GOLD[("golden_eval.json<br/>fixed real-Q ruler")] -.->|measuring stick| PE
  ING["ingest + reconcile<br/>corpus grows/drifts"] --> PE["MEASURE<br/>policy_eval.ts<br/>score 3 arms<br/>disc. grounding@C"]
  PE -->|"winner can flip<br/>vector→hybrid"| POL[("DECIDE<br/>search_policy.json<br/>winning arm + rrf_k")]
  POL --> QP["APPLY<br/>query_policy.ts<br/>route agent queries"]
  QP --> ANS["agent retrieval<br/>honors the verdict"]
  ANS -.->|every new ingest re-fires| ING
```

The dashed loop is the "self-tuning": new pages → re-MEASURE over the current corpus → the DECIDE step can pick a different arm than last time (Phase A→B flipped `vector → hybrid`), and APPLY routes the agent through it — no human, no code change. The golden set is the one fixed thing (the ruler); everything else moves with the corpus.

#### Block A — `data/golden_eval.json`: the measuring stick

The golden set is a **stable, version-controlled** artifact — kept *separate from the corpus* (which changes). 18 real, labeled questions, domain-tagged:
- **`tenk` (12):** W2.7's labeled Berkshire-10-K questions (factoid / synthesis / citation). The 4 out-of-document *refusal* questions are dropped — they test generation refusal, not retrieval, and have no gold section to find.
- **`entity` (6):** hand-written from the W3.5.96 `~/brain/sources` fixtures, keyed on proper nouns that reliably appear (`Sam Okafor`, `Lin Zhao`, `Ridgeline`, …).

Each question carries `expected_entities` — the substrings a correct answer-bearing section must contain. That's the gold: **no per-slug labels needed**, so the set is cheap to extend as the real query distribution shifts.

```json
{ "q": "Who is anchoring the acme-seed round?",
  "expected_entities": ["Sam Okafor", "Northstar"], "domain": "entity" }
```

#### Block B — `policy_eval.ts`: score real questions, write the policy

**When to use:** reach for `policy_eval.ts` whenever `data/golden_eval.json` is present and you want a trustworthy, corpus-adaptive policy - it uses real, labeled questions and position-aware discounted grounding@C to select the best retrieval arm. Use `auto_eval.ts` instead only as a fallback when no golden set exists yet.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  G[(golden_eval.json<br/>real labeled Qs<br/>+ expected_entities)] --> CK{golden<br/>exists?}
  CK -->|no| FB[exit 1<br/>caller falls back<br/>to auto_eval.ts]
  CK -->|yes| BOOT[bootstrap GBrain engine<br/>same seq as the CLI]
  BOOT --> ARM[for each arm:<br/>keyword · vector · hybrid]
  ARM --> SR[search top-K<br/>per golden question]
  SR --> SC[grounding.ts · 0-LLM<br/>grnd@C↓ = max coverage x disc i<br/>answ@C = all entities in some top-C]
  SC --> AGG[per arm: mean grnd@C↓<br/>+ mean answ@C<br/>+ per-domain g@C tenk · entity]
  AGG --> WIN[winner = argmax grnd@C↓]
  WIN --> TIE{grnd@C↓ tie?}
  TIE -->|no| POL[(search_policy.json<br/>winner + rrf_k<br/>source: golden_eval)]
  TIE -->|"yes · 平手"| TB[tie-break<br/>argmax answ@C]
  TB --> POL
```
*`policy_eval.ts` data flow. The golden set is the fixed ruler; for every arm it searches the live corpus and scores each question on two 0-LLM metrics in `grounding.ts` - `grnd@C↓` (position-weighted best coverage over the generator's budget `C`) and `answ@C` (answerable@C: fraction of questions where some top-C section covers ALL expected entities). The winner is `argmax(grnd@C↓)`; on a tie it falls back to `argmax(answ@C)` (`groundingFor(b)-groundingFor(a) || answerableFor(b)-answerableFor(a)`), then writes the winning arm to `search_policy.json`. Absent golden set → exit 1, and `run_auto_eval()` runs `auto_eval.ts` instead.*

**Code (full source `src/policy_eval.ts`):**

```typescript
/**
 * policy_eval.ts — REAL-question policy generator (the trustworthy policy source).
 *
 * Replaces eval.ts's known-item PROXY as the thing that writes the policy.
 * The proxy used page titles as queries and mis-selected `keyword`; real questions
 * refuted that ~5×. So the policy must come from a real, labeled golden set.
 *
 * Reads data/golden_eval.json (real questions + expected_entities, domain-tagged),
 * runs keyword/vector/hybrid over the CURRENT corpus, scores DISCOUNTED grounding
 * over the context budget, picks the overall winner, and WRITES
 * results/search_policy.json. Re-run after every ingest → the policy ADAPTS as the
 * corpus drifts (new pages = distractors that can shift which arm retrieves best).
 *
 * Why discounted-over-budget, not the old rank-blind max-over-top-K:
 *   The real objective is ANSWER quality, not raw retrieval. Hybrid RRF can fuse a
 *   keyword distractor above the dense answer chunk — the answer is still "in top-K"
 *   (rank-blind grounding unchanged) but it now reads later, or falls past the chunks
 *   the generator is actually given. Rank-blind grounding cannot see that; it's the
 *   exact RRF failure we care about. So we score the prompt the generator really sees:
 *
 *   grounding@C  = mean over questions of  max_i coverage_i · disc(i)   over top-C
 *                  (position-weighted best coverage; primacy via disc, budget via C).
 *                  Answer demoted by RRF → lower; answer pushed past C → 0.
 *   answerable@C = fraction of questions where some top-C section covers ALL entities.
 *
 * K = retrieval depth (how many hits we pull); C = context budget (how many chunks
 * the generator reads, C ≤ K). Set C to the production injected-chunk count so the
 * metric measures "did the answer survive into the prompt?". The golden set is a
 * stable measuring stick (version-controlled); keep it representative of the workload.
 *
 * Run: bun src/policy_eval.ts        (needs the corpus loaded + OLLAMA_* up)
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { budgetScore, coverage } from "./grounding.ts";

const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;
const GOLDEN = `${import.meta.dir}/../data/golden_eval.json`;
const POLICY = `${import.meta.dir}/../results/search_policy.json`;
const K = Number(process.env.POLICY_K ?? "5");   // retrieval depth (hits pulled)
const C = Number(process.env.POLICY_C ?? "3");   // context budget (chunks the generator reads; C ≤ K)

interface GoldenQ { q: string; expected_entities: string[]; domain: string }
type Strategy = "keyword" | "vector" | "hybrid";

if (!existsSync(GOLDEN)) {
  console.error(`no golden set at ${GOLDEN} — run auto_eval.ts (known-item fallback) instead.`);
  process.exit(1);
}
const golden: GoldenQ[] = JSON.parse(readFileSync(GOLDEN, "utf-8")).questions;

// ── engine bootstrap (identical sequence to auto_eval.ts / the CLI) ─────────
const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway, reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { runEval } = await import(`${GB}/core/search/eval.ts`);

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
await reconfigureGatewayWithEngine(engine);
const nPages = (await engine.listPages()).length;

// section text cache (slug → lowercased title+body+timeline)
const textCache = new Map<string, string>();
async function sectionText(slug: string): Promise<string> {
  if (textCache.has(slug)) return textCache.get(slug)!;
  const p = await engine.getPage(slug);
  const t = p ? `${p.title}\n${p.compiled_truth}\n${p.timeline}`.toLowerCase() : "";
  textCache.set(slug, t);
  return t;
}
const domains = [...new Set(golden.map(g => g.domain))];
const strategies: readonly Strategy[] = ["keyword", "vector", "hybrid"];

// Per strategy, per question: discounted grounding@C (drives policy) + raw best
// coverage in budget (feeds answerable@C). Retrieval pulls K hits; we score only the
// C the generator actually reads, so an RRF reorder that demotes the answer — or
// pushes it past C — is penalised. See grounding.ts for the scoring contract.
const perQ = {} as Record<Strategy, number[]>;       // discounted grounding@C
const perQFull = {} as Record<Strategy, number[]>;   // raw best coverage within budget
for (const strategy of strategies) {
  const report = await runEval(
    engine,
    golden.map(g => ({ query: g.q, relevant: [] as string[] })),
    { strategy, expand: false, limit: K },
    K,
  );
  const gDisc: number[] = [];
  const gFull: number[] = [];
  for (let i = 0; i < golden.length; i++) {
    const topC: string[] = report.queries[i].hits.slice(0, C); // limit fetches to the budget window
    const ents = golden[i].expected_entities;
    const coverages = await Promise.all(topC.map(async slug => coverage(await sectionText(slug), ents)));
    const { gDisc: d, gFull: full } = budgetScore(coverages, C);
    gDisc.push(d);
    gFull.push(full);
  }
  perQ[strategy] = gDisc;
  perQFull[strategy] = gFull;
}

const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const groundingFor = (s: Strategy, domain?: string) =>
  mean(perQ[s].filter((_, i) => !domain || golden[i].domain === domain));
// flatFor = the OLD rank-blind metric (mean raw best-coverage in budget). Shown next
// to the discounted score: where flat > discounted, the answer sits below rank 0 —
// i.e. an arm (often hybrid RRF) demoted it. The gap is the penalty we added.
const flatFor = (s: Strategy, domain?: string) =>
  mean(perQFull[s].filter((_, i) => !domain || golden[i].domain === domain));
const answerableFor = (s: Strategy) =>
  mean(perQFull[s].map(v => (v === 1 ? 1 : 0)));

// ── report: overall + per-domain grounding@C ────────────────────────────────
const pad = (s: string, n: number) => s.padEnd(n);
const f = (x: number) => x.toFixed(3);
console.log(`policy_eval: golden set = ${golden.length} real questions ` +
  `(${domains.map(d => `${d}:${golden.filter(g => g.domain === d).length}`).join(", ")}) ` +
  `· corpus = ${nPages} pages · retrieval K=${K} · context budget C=${C}\n`);
console.log(pad("strategy", 10) + pad(`grnd@${C}↓`, 12) + pad(`flat@${C}`, 11) + pad(`answ@${C}`, 11) +
  domains.map(d => pad(`g@${C}:${d}`, 13)).join(""));
console.log("-".repeat(44 + domains.length * 13));
for (const s of strategies) {
  console.log(pad(s, 10) + pad(f(groundingFor(s)), 12) + pad(f(flatFor(s)), 11) + pad(f(answerableFor(s)), 11) +
    domains.map(d => pad(f(groundingFor(s, d)), 13)).join(""));
}

// ── decide + write policy (winner = overall discounted grounding, tie → answerable) ──
const winner = [...strategies].sort((a, b) =>
  groundingFor(b) - groundingFor(a) || answerableFor(b) - answerableFor(a))[0];

const policy = {
  strategy: winner,
  rrf_k: 60,
  k: K,
  c: C,
  metric: "discounted_grounding@C (position-weighted best coverage over the context budget)",
  source: "golden_eval",
  n_questions: golden.length,
  n_pages: nPages,
  grounding: groundingFor(winner),
  per_domain: Object.fromEntries(domains.map(d => [d, groundingFor(winner, d)])),
  note: "auto-selected from data/golden_eval.json (REAL questions, discounted grounding@C: "
    + "rank- and budget-aware, so an RRF reorder that demotes the answer is penalized). "
    + "Read by query_policy.ts; does NOT change stock `gbrain query` (hybrid-only).",
};
mkdirSync(dirname(POLICY), { recursive: true });
writeFileSync(POLICY, JSON.stringify(policy, null, 2) + "\n");
console.log(`\napplied policy → strategy=${winner} (grnd@${C}↓=${f(groundingFor(winner))})  ` +
  `← results/search_policy.json [source: golden_eval]`);

await engine.disconnect?.();
process.exit(0);
```

**Walkthrough:**
- **Discounted grounding@C, not rank-blind grounding@K.** With no gold *slug*, "did retrieval surface a section *containing the answer entities*" is the honest, label-cheap signal. But the old `max`-over-top-K was **rank- and budget-blind** — it scored 1.0 whether the answer sat at rank 0 or rank 4. RRF's failure mode is exactly rank: fuse a keyword distractor above the dense answer and the answer reads later, or falls past the `C` chunks the generator is actually handed. So we score the prompt the model sees — `gDisc = max_i coverage_i · disc(i)` over the top-`C`, where `disc(rank0)=1/log2(rank0+2)` rewards early placement and a section past `C` scores 0. `C` is the **production injected-chunk count** (here 3, read off `ground_truth_ab.py`), not a tunable — it is *measured off the agent*, never hand-picked.
- **Per-domain breakdown is the diagnostic.** `g@C:tenk` vs `g@C:entity` shows *which corpus the policy is serving*, and makes drift visible — an absent domain scores ~0 until its data is ingested.
- **Winner = `argmax(grnd@C↓)`, ties broken by `argmax(answ@C)`.** The selection is one sort: `strategies.sort((a,b) => groundingFor(b)-groundingFor(a) || answerableFor(b)-answerableFor(a))[0]`. Primary key is discounted grounding (does the answer land high *and* inside the budget); the `||` only fires when two arms tie on grounding, then the more *answerable* arm (more questions whose top-C covers ALL expected entities) wins. This is why both `grnd@C↓` and `answ@C` columns are computed per arm even though only grounding usually decides - `answ@C` is the documented deterministic tiebreaker, not decoration.
- **Re-runs on every ingest.** `run_auto_eval()` prefers `policy_eval.ts` whenever `data/golden_eval.json` exists, so the policy is re-selected against the *current* corpus each time; the loop tracks drift automatically.

#### Block C — `auto_eval.ts`: cold-start SELECTOR + regression guardrail

`auto_eval.ts` is the fallback SELECTOR that fires when no `golden_eval.json` exists yet. Instead of real labeled questions it synthesizes its own qrels from the live corpus: each sampled page contributes an **exact** query (the page title - exercises keyword FTS) and a **semantic** query (body words with the title tokens stripped - the gold page name is never a literal substring, so keyword cannot trivially win). Sample size scales with corpus size (`Q = clamp(ceil(ratio·N), Q_MIN, Q_MAX)`) and a seeded shuffle keeps runs reproducible. It scores all three arms via `runEval()`, writes the winner to `results/search_policy.json`, and appends the run record to `results/auto_eval.jsonl` so the next run can detect a regression.

**When to use:** reach for `auto_eval.ts` (via `run_auto_eval()`) when the brain is brand-new and no hand-labeled golden set exists yet - it gives a retrieval-health signal and a policy artifact immediately, at zero labeling cost. Prefer `policy_eval.ts` once real questions are available; `auto_eval.ts` is demoted to a cold-start fallback and a run-to-run regression guardrail (Δrecall@K across ingests), not a trusted policy source.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  PAGES["engine.listPages()<br/>all N pages"] --> SORT["sort by slug<br/>(order-independent)"] 
  SORT --> SHUF["seededShuffle<br/>mulberry32 PRNG<br/>seed=42"]
  SHUF --> SAMPLE["sample Q pages<br/>Q=clamp(ceil(ratio·N),<br/>Q_MIN,Q_MAX)"]
  SAMPLE --> EXACT["exact query<br/>= page.title<br/>gold = page.slug"]
  SAMPLE --> SEM["semanticQuery()<br/>body-minus-title tokens<br/>≥3 words kept"]
  EXACT --> QRELS["AutoQrel set<br/>exact + semantic"]
  SEM --> QRELS
  QRELS --> RE["runEval() × 3<br/>keyword · vector · hybrid"]
  RE --> WIN["winner = argmax recall@K<br/>tie-break: argmax MRR"]
  WIN --> POL[("search_policy.json<br/>strategy + recall")]
  WIN --> LOG[("auto_eval.jsonl<br/>run history")]
  LOG --> REG{"previous run<br/>exists?"}  
  REG -->|"yes"| DIFF["Δrecall@K per arm<br/>⚠ if < -ε"]
  REG -->|"no"| BASE["baseline run"]
```
*`auto_eval.ts` data flow. The corpus itself generates the qrels (known-item proxy) - no human labeling required. `mulberry32` is a tiny seeded PRNG so the sampled page-set is reproducible for a given (corpus, seed) pair. The regression check compares the new run against the last `auto_eval.jsonl` line and emits a warning when any arm drops more than `REGRESS_EPS` (default 0.05).*

**Code: `src/auto_eval.ts`**

```typescript
/**
 * auto_eval.ts — post-ingest retrieval-health regression check.
 *
 * WIRED INTO THE INGEST FLOW: ingest_agent.py / resumable_ingest.py call this
 * via `bun src/auto_eval.ts` right after reconcile_graph(), so every corpus
 * write is followed by a keyword-vs-vector-vs-hybrid measurement on the LIVE
 * brain. It runs at the ENGINE layer (engine.searchKeyword / searchVector /
 * hybridSearch via gbrain's runEval) — the CLI cannot A/B these (Phase 6 trap:
 * `gbrain search` and `gbrain query` share one handler).
 *
 * AUTO-LABELING (no hand-built qrels): this is a KNOWN-ITEM eval. We sample Q
 * pages and synthesize one query per page whose gold answer IS that page's own
 * slug:
 *   - exact    query = the page TITLE          → exercises the keyword arm
 *   - semantic query = body words MINUS the title tokens → exercises the vector
 *                      arm (the gold page's name is NOT a literal substring, so
 *                      keyword cannot trivially win it)
 * Q scales with corpus size: Q = clamp(ceil(ratio·N), Q_MIN, Q_MAX), sampled
 * with a SEEDED shuffle so a given page-set is reproducible run-to-run.
 *
 * HONEST LIMITATION (do not oversell): known-item queries are drawn from each
 * doc's OWN vocabulary, so they are a PROXY for real user queries, not a
 * substitute for a hand-labeled gold set that reflects the real query
 * distribution. This harness answers "did retrieval regress / which arm wins on
 * THIS corpus shape?" — it is a guardrail + trend signal, not a quality verdict.
 *
 * Config (env): AUTO_EVAL_RATIO=0.30  AUTO_EVAL_QMIN=5  AUTO_EVAL_QMAX=50
 *   AUTO_EVAL_K=3  AUTO_EVAL_SEED=42  AUTO_EVAL_REGRESS_EPS=0.05  AUTO_EVAL_STRICT=0
 * Run: bun src/auto_eval.ts   (needs GBRAIN_DATABASE_URL + OLLAMA_* env)
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;
const RESULTS = `${import.meta.dir}/../results/auto_eval.jsonl`;
// The APPLY target: the decision artifact the policy-aware query path reads to
// honor the corpus-selected strategy (closes the measure→decide→apply loop).
const POLICY = `${import.meta.dir}/../results/search_policy.json`;

const RATIO = Number(process.env.AUTO_EVAL_RATIO ?? "0.30");
const Q_MIN = Number(process.env.AUTO_EVAL_QMIN ?? "5");
const Q_MAX = Number(process.env.AUTO_EVAL_QMAX ?? "50");
const K = Number(process.env.AUTO_EVAL_K ?? "3");
const SEED = Number(process.env.AUTO_EVAL_SEED ?? "42") || 42;
const REGRESS_EPS = Number(process.env.AUTO_EVAL_REGRESS_EPS ?? "0.05");
const STRICT = process.env.AUTO_EVAL_STRICT === "1";

export interface PageLite { slug: string; title: string; compiled_truth: string }
export type Kind = "exact" | "semantic";
export interface AutoQrel { query: string; relevant: string[]; kind: Kind }
type Strategy = "keyword" | "vector" | "hybrid";

// Q scales with corpus size: clamp(ceil(ratio·N), Q_MIN, Q_MAX), never above N.
export function computeQ(n: number, ratio: number, qMin: number, qMax: number): number {
  return Math.min(n, qMax, Math.max(qMin, Math.ceil(ratio * n)));
}

// ── deterministic sampling ────────────────────────────────────────────────
// mulberry32: tiny seeded PRNG so the sampled page-set is reproducible for a
// given (corpus, seed). Adding pages reshuffles — the eval is a per-run trend,
// not a frozen gold set.
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function seededShuffle<T>(arr: readonly T[], seed: number): T[] {
  const rand = mulberry32(seed);
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

// ── known-item query synthesis ────────────────────────────────────────────
const WIKILINK = /\[\[([^\]]+)\]\]/g;

// Replace [[dir/slug]] with its readable tail ("companies/acme-ai" → "acme ai")
// so the body becomes plain words, not link markup.
function deLink(text: string): string {
  return text.replace(WIKILINK, (_m, inner: string) => {
    const tail = inner.split("/").pop() ?? "";
    return tail.replace(/-/g, " ");
  });
}

function tokenize(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+/g) ?? [];
}

// Semantic probe: first body sentence, de-linked, with the page's TITLE tokens
// removed — so the gold page's name is never a literal substring of the query
// (keyword cannot trivially match it; the vector arm has to earn the hit).
// Returns null when too few content words survive to be a meaningful query.
export function semanticQuery(page: PageLite): string | null {
  const body = (page.compiled_truth ?? "").replace(/^#.*$/m, "").trim();
  const plain = deLink(body).replace(/\s+/g, " ").trim();
  const firstSentence = (plain.split(/(?<=[.!?])\s+/)[0] ?? "").trim();
  if (!firstSentence) return null;
  const titleTokens = new Set(tokenize(page.title));
  const kept = tokenize(firstSentence).filter(t => t.length > 2 && !titleTokens.has(t));
  return kept.length >= 3 ? kept.join(" ") : null;
}

export function buildQrels(sample: readonly PageLite[]): AutoQrel[] {
  const qrels: AutoQrel[] = [];
  for (const page of sample) {
    const exact = page.title?.trim();
    if (exact) qrels.push({ query: exact, relevant: [page.slug], kind: "exact" });
    const semantic = semanticQuery(page);
    if (semantic) qrels.push({ query: semantic, relevant: [page.slug], kind: "semantic" });
  }
  return qrels;
}

// ── live run (engine layer) — only when executed directly, not on import ────
async function main(): Promise<void> {
// engine bootstrap (identical sequence to bench_strategies.ts / the CLI)
const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway, reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { runEval } = await import(`${GB}/core/search/eval.ts`);

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
await reconfigureGatewayWithEngine(engine);

// ── sample + label ─────────────────────────────────────────────────────────
const allPages: PageLite[] = await engine.listPages();
const N = allPages.length;
if (N === 0) {
  console.log("auto-eval: empty brain (0 pages) — nothing to evaluate.");
  await engine.disconnect?.();
  process.exit(0);
}

const Q = computeQ(N, RATIO, Q_MIN, Q_MAX);
// Sort by slug first so the seeded shuffle is order-independent of listPages().
const bySlug = [...allPages].sort((a, b) => (a.slug < b.slug ? -1 : 1));
const sample = seededShuffle(bySlug, SEED).slice(0, Q);
const qrels = buildQrels(sample);

const nExact = qrels.filter(q => q.kind === "exact").length;
const nSemantic = qrels.filter(q => q.kind === "semantic").length;
console.log(
  `auto-eval: N=${N} pages · ratio=${RATIO} · Q=${Q} sampled (seed=${SEED}) · ` +
  `${qrels.length} known-item queries (${nExact} exact / ${nSemantic} semantic) · K=${K}`,
);

// ── run the three strategies ────────────────────────────────────────────────
const strategies: readonly Strategy[] = ["keyword", "vector", "hybrid"];
const plain = qrels.map(({ query, relevant }) => ({ query, relevant }));
const reports: Record<Strategy, any> = {} as Record<Strategy, any>;
for (const strategy of strategies) {
  reports[strategy] = await runEval(engine, plain, { strategy, expand: false }, K);
}

// per-kind recall: where does each arm actually win?
function recallByKind(strategy: Strategy, kind: Kind): number {
  const vals = qrels
    .map((q, i) => (q.kind === kind ? reports[strategy].queries[i].recall_at_k : null))
    .filter((v): v is number => v !== null);
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : NaN;
}

const f = (x: number) => (Number.isNaN(x) ? "  n/a" : x.toFixed(3));
const pad = (s: string, n: number) => s.padEnd(n);

console.log("\n" + pad("strategy", 10) + pad(`recall@${K}`, 11) + pad("MRR", 9) +
  pad(`nDCG@${K}`, 10) + pad("R@K exact", 11) + pad("R@K seman", 11));
console.log("-".repeat(62));
for (const s of strategies) {
  const r = reports[s];
  console.log(
    pad(s, 10) + pad(f(r.mean_recall), 11) + pad(f(r.mean_mrr), 9) +
    pad(f(r.mean_ndcg), 10) + pad(f(recallByKind(s, "exact")), 11) +
    pad(f(recallByKind(s, "semantic")), 11),
  );
}

// winner by recall@K, tie-broken by MRR
const winner = [...strategies].sort((a, b) =>
  reports[b].mean_recall - reports[a].mean_recall ||
  reports[b].mean_mrr - reports[a].mean_mrr)[0];
console.log(`\nwinner on this corpus: ${winner} ` +
  `(recall@${K}=${f(reports[winner].mean_recall)}, MRR=${f(reports[winner].mean_mrr)})`);

// ── persist + regression check vs the previous run ──────────────────────────
const record = {
  ts: new Date().toISOString(),
  n_pages: N, q: Q, ratio: RATIO, seed: SEED, k: K, n_queries: qrels.length,
  winner,
  strategies: Object.fromEntries(strategies.map(s => [s, {
    recall: reports[s].mean_recall, mrr: reports[s].mean_mrr, ndcg: reports[s].mean_ndcg,
    recall_exact: recallByKind(s, "exact"), recall_semantic: recallByKind(s, "semantic"),
  }])),
};

let previous: typeof record | null = null;
if (existsSync(RESULTS)) {
  const lines = readFileSync(RESULTS, "utf-8").trim().split("\n").filter(Boolean);
  if (lines.length) {
    try { previous = JSON.parse(lines[lines.length - 1]); } catch { previous = null; }
  }
}

mkdirSync(dirname(RESULTS), { recursive: true });
appendFileSync(RESULTS, JSON.stringify(record) + "\n");

// ── APPLY: write the corpus-selected policy the query path will honor ────────
// Winner = recall@K winner (tie-broken by MRR). This is the actuator half: the
// next agent query reads search_policy.json and routes to this strategy instead
// of bare hybrid. Stock `gbrain query` is hybrid-only and is NOT affected.
const policy = {
  strategy: winner,
  rrf_k: 60,                       // GBrain RRF default; only used when strategy==="hybrid"
  k: K,
  n_pages: N,
  recall: reports[winner].mean_recall,
  per_kind: { exact: recallByKind(winner, "exact"), semantic: recallByKind(winner, "semantic") },
  ts: record.ts,
  note: "auto-selected by auto_eval.ts (known-item eval). Read by query_policy.ts; "
    + "does NOT change stock `gbrain query` (hybrid-only).",
};
writeFileSync(POLICY, JSON.stringify(policy, null, 2) + "\n");
console.log(`applied search policy → strategy=${winner}  (results/search_policy.json)`);

let regressed = false;
if (previous) {
  console.log(`\nvs previous run (${previous.ts}, N=${previous.n_pages}):`);
  for (const s of strategies) {
    const d = reports[s].mean_recall - previous.strategies[s].recall;
    const tag = d < -REGRESS_EPS ? "  ⚠ REGRESSION" : "";
    if (d < -REGRESS_EPS) regressed = true;
    console.log(`  ${pad(s, 10)} Δrecall@${K} = ${d >= 0 ? "+" : ""}${d.toFixed(3)}${tag}`);
  }
  if (!regressed) console.log("  no strategy regressed beyond ε=" + REGRESS_EPS);
} else {
  console.log("\n(no previous run — this is the baseline)");
}

console.log("\nnote: known-item proxy eval (queries drawn from each page's own text). " +
  "Measures retrieval health + per-arm fit, NOT real-query quality.");

await engine.disconnect?.();
process.exit(regressed && STRICT ? 2 : 0);
}

if (import.meta.main) {
  await main();
}
```

**Walkthrough:**
- **Known-item auto-labeling avoids cold-start paralysis.** Without any hand-built qrels a brand-new brain still gets a policy. The trick: each page's own title makes a valid exact-keyword query (gold = that slug), and the first body sentence with title tokens removed makes a semantic probe the keyword arm cannot trivially win. The split between `exact` and `semantic` kinds is load-bearing - it exposes *per-arm* recall so you see whether keyword or vector is doing the work (the `R@K exact` / `R@K seman` columns in the output table).
- **`mulberry32` + sort-before-shuffle makes runs reproducible.** A standard PRNG seeded differently each run would make the sampled page-set non-deterministic; the same seed but random `listPages()` order would do the same. Sorting by slug first eliminates the second source of variance, so a given (corpus state, SEED) always samples the same pages - adding new pages changes the sorted order and reshuffles, but the eval is a per-run trend signal, not a frozen gold set, so that is correct behavior.
- **`semanticQuery` strips title tokens precisely to prevent trivial keyword wins.** If the title `Lin Zhao` appeared verbatim in the semantic query, keyword FTS would match it by exact token overlap and inflate keyword recall - the semantic arm would not be tested at all. Removing title tokens forces the vector arm to earn hits on paraphrase, giving an honest arm comparison on small corpora where keyword precision can otherwise mask poor vector coverage.
- **Regression check compares against the last `auto_eval.jsonl` line, not a fixed baseline.** This means every ingest automatically detects drift: if corpus changes degrade any arm by more than `REGRESS_EPS` (default 0.05), a `⚠ REGRESSION` line appears. `STRICT=1` exits with code 2 so a CI hook can catch it. The JSONL append is the audit trail - historical recall@K is always recoverable even when `search_policy.json` has been overwritten many times.
- **APPLY step closes the measure-decide-apply loop.** `search_policy.json` is not just a log - it is the artifact `query_policy.ts` reads on every agent retrieval call. Writing it here (with `source: auto_eval`) is the actuator step; the next query the agent issues will honor the corpus-selected arm without any code change.

**Result — the drift experiment (live, isolated `gbrain_brk` DB):**

> The two tables below are the **original rank-blind `grounding@5`** runs (the
> superseded metric — kept because the *drift narrative* is what they illustrate).
> The metric was later upgraded to **budget-aware discounted grounding@C**; the
> re-measured numbers and the C-sweep are in *Metric upgrade* below.

*Phase A — corpus = 10-K only (44 pages):*

| arm | grounding@5 | g@5 tenk | g@5 entity |
|---|---|---|---|
| keyword | 0.167 | 0.250 | 0.000 |
| **vector** | **0.667** | 0.958 | 0.083 |
| hybrid | 0.667 | 0.958 | 0.083 |

→ **policy v1 = `vector`.** Vector nails 10-K factoid retrieval (`tenk 0.958`); the entity questions score ~0 because that data isn't in the corpus yet (correctly uninformative — the per-domain split makes that legible).

*Phase B — ingest the W3.5.96 entity corpus → mixed (59 pages); the eval auto-re-fires:*

| arm | grounding@5 | g@5 tenk | g@5 entity |
|---|---|---|---|
| keyword | 0.222 | 0.250 | 0.167 |
| vector | 0.944 | 0.958 | 0.917 |
| **hybrid** | **0.972** | 0.958 | **1.000** |

→ **policy v2 = `hybrid`.** The policy **changed on its own**, triggered by the ingest, with no code change. It's data-justified: entity questions are proper-noun lookups (`Sam Okafor`, `Lin Zhao`) that revive the keyword arm, while vector still owns 10-K semantics — both arms now competitive, so RRF earns its weight (entity `g@5`: hybrid **1.000** > vector 0.917). And `tenk` grounding held at 0.958 across both phases: the +15 distractor pages didn't degrade 10-K retrieval; the policy shifted to *capture new value*, not to recover lost ground.

##### Metric upgrade — budget-aware discounted grounding@C (2026-06-06)

**The setup.** Retrieval returns `K` candidates, ranked by score. The generator reads only the top-`C` (= **3**, the agent's real injected-chunk count, from `ground_truth_ab.py:110`) that you actually paste into the prompt — and it weights earlier chunks more heavily. So the metric we tune the policy on must score *the prompt the generator sees*, in order, not the raw retrieval list.

**Rank-blind grounding (`flat@C`, the old metric)** asks only "is the answer *anywhere* in the top-`C`?" — `max` coverage over the window, **ignoring position**. An answer chunk at rank 0 and one at rank 2 both score 1.0. The problem: RRF fusion (hybrid) can **reorder** — it can take an answer chunk that one arm ranked at position 0 and *demote* it to position 2, or push it past `C` entirely. Rank-blind can't see that; it still says "answer in budget, score 1.0" even though the generator now sees it buried (or never sees it).

**Discounted grounding@C (`grnd@C↓`, the new metric)** is position-weighted: `coverage(rank r) × disc(r)`, where `disc(0)=1.0`, `disc(1)=0.63`, `disc(2)=0.5` (the `1/log₂(r+2)` curve in `grounding.ts`). The *same* answer scores **1.0 at rank 0** but only **0.5 at rank 2** — the metric now *feels* where the answer sits in the budget.

**The demotion tax = `flat − grnd↓`** is exactly how much answer mass got pushed below rank 0 within the budget — *the lie the rank-blind metric was telling*. Answer always at rank 0 → tax 0 (the two metrics agree, the upgrade would be pointless). Answer demoted to rank 2 → `flat` 1.0 but discounted 0.5 → tax 0.5. The tax makes RRF's reorder cost a *visible number* instead of a hidden one.

**Why this matters for the design.** The metric's whole job is to **predict answer quality cheaply** so the SELECTOR can run on every ingest *without* an LLM (see Block D). A demotion-blind metric mis-predicts: it credits "hybrid grounds 1.0" when hybrid's RRF demoted the answer to rank 2 and the generator then fumbled it. The discounted metric catches that demotion → tracks answer quality better → correlates with the answer-judge more strongly (`r = +0.820`, Block D) → the 0-LLM selector is *justified*. A rank-blind metric, by contrast, would have a *lower* correlation, because it over-credits demoted answers the generator never uses.

**Why vector's tax *growing* reinforces the choice — not threatens it.** The discounted-over-rank-blind decision is only worth making if the demotion tax is **non-zero in the data**; if every answer sat at rank 0 the two metrics would agree and the upgrade would be ceremony. In the measured table below, **vector** carries the biggest tax (**0.090**) — its best chunk often lands at rank 1–2, not 0 — so a rank-blind metric would miss that entire 0.090 and over-credit vector. The sharpest case is the **C-sweep at C=5**: vector's `flat` *ties* hybrid (`0.972 = 0.972`), so rank-blind would call them **equal and the selector could pick wrong** — but discounted separates them (`hybrid 0.910 > vector 0.836`) because vector hides ~14% of its answer mass at ranks 4–5 the generator never reads. Bigger tax = the rank-blind metric lies more = *stronger* case for the discounted one. (The mid-session corpus drift that nudged vector's tax up from 0.061 to 0.090 therefore didn't threaten the decision — it produced *more* evidence rank-blind is inadequate.)

Re-measured on the live **mixed brain (67 pages, 10-K re-ingested over the entity corpus)**:

| arm | grnd@3↓ | flat@3 (old) | demotion tax | g@3:tenk | g@3:entity |
|---|---|---|---|---|---|
| keyword | 0.306 | 0.306 | 0.000 | 0.250 | 0.417 |
| vector | 0.836 | 0.926 | 0.090 | 0.858 | 0.794 |
| **hybrid** | **0.910** | 0.972 | 0.062 | 0.927 | 0.877 |

`flat@C` is the old rank-blind metric; the **demotion tax** (`flat − grnd↓`) is the answer mass sitting below rank 0 within the budget. **Vector** pays the most (0.090) — its best chunk often lands at rank 1–2, not 0 — and **hybrid** pays 0.062, but hybrid still wins outright on *both* the flat (0.972) *and* the discounted score (**0.910 > vector's 0.836**), so RRF's reorder cost is real yet more than covered. The upgrade **validated** the `vector→hybrid` verdict on answer-quality grounds *and* priced the reorder cost, instead of rubber-stamping it rank-blind.

**C-sensitivity sweep** (same corpus) — the verdict is stable, no cliff:

| C | winner | vector↓ | hybrid↓ | hybrid flat | vector flat |
|---|---|---|---|---|---|
| 1 | hybrid | 0.759 | 0.861 | 0.861 | 0.759 |
| 2 | hybrid | 0.802 | 0.903 | 0.944 | 0.843 |
| 3 | hybrid | 0.836 | 0.910 | 0.972 | 0.926 |
| 5 | hybrid | 0.836 | 0.910 | 0.972 | **0.972** |

The payoff shows at **C=5**: the old metric *ties* vector and hybrid (`flat 0.972 = 0.972`, decided by sort order), but discounted grounding separates them (`0.910 > 0.836`) — vector hides ~14% of its answer mass at ranks 4–5 (its `flat` climbs 0.926 → 0.972 from C=3 to C=5 while its discounted score stays 0.836), outside a 3-chunk prompt the generator never reads; hybrid keeps answers in the top-3. Same arms, same corpus — the cutoff `C` is the entire difference. **How to choose `C`:** measure it off the agent's context-assembly (injected-chunk count, or `floor(token_budget / avg_page_tokens)`), then sweep `C∈{1,2,3,5}` to confirm the verdict isn't sitting on a cliff; if it flips between adjacent C, pin the exact production number.

##### Per-query routing — rejected on the natural corpus, accepted on a mixed-type one (2026-06-06 → 06-07)

The policy picks ONE arm for the whole corpus. Natural next question: the best arm is query-dependent (proper-noun lookups favour keyword/hybrid, semantic factoids favour vector), so should we route *each query* to its own best arm? Built `src/route_eval.ts` to measure it — three routers scored with the same discounted grounding@C:
- **global** — every query → the corpus winner (`hybrid`). The baseline.
- **heuristic** — a zero-LLM classifier (proper-noun-heavy short query → keyword, else hybrid).
- **oracle** — every query → its own best arm. The *ceiling*; unattainable in production (it peeks at the labels) but it bounds how much routing can ever help.

**Build the ceiling before the classifier.** On the 67-page mixed brain:

| router | grnd@3↓ | Δ vs global |
|---|---|---|
| global (hybrid) | 0.910 | — |
| heuristic | 0.736 | −0.174 |
| **oracle (ceiling)** | **0.910** | **+0.000** |

The oracle *equals* global hybrid — **hybrid weakly dominates every one of the 18 questions**, so per-query routing has zero grounding headroom, and a real cheap classifier only loses (it mis-routes semantic questions to the weak keyword arm). One free number (the oracle) killed the whole feature before any classifier was tuned.

> **Scope this honestly — the verdict is the *workload's*, not a law.** Routing beats global hybrid only when (a) different queries favor different arms AND (b) fusion sometimes demotes the winner. This golden set has neither: by query class it is **11 vector-only (semantic) · 6 both-find-it · 1 hybrid-only · 0 keyword-only**, and on **0 of 18** did RRF score below the best single arm. It's vector-skewed with no pure exact-match queries and no RRF-adversarial cases — so hybrid dominates by *construction*, and routing can't win. So I built that set and re-ran the oracle (`data/golden_balanced.json`, `GOLDEN_EVAL=… bun src/route_eval.ts`): **24 questions, the same answer targets phrased two ways** — keyword-style (exact distinctive tokens) vs vector-style (paraphrase with the answer terms removed). **Routing was still rejected: oracle 0.831 vs global hybrid 0.823 (Δ +0.008), heuristic −0.242.** And the reason turned out *deeper* than question balance: I couldn't even *build* keyword-favoring queries — GBrain's FTS arm returned grounding **0** on half the exact-token queries (`Itochu Marubeni…`, `Item 1C`, `Lin Zhao Quanta`, `Helix Bio protein`) while vector nailed every one. **Vector dominates this corpus regardless of phrasing**: `0/24` queries had keyword as the strict best, and only `1/24` had RRF demote the winner. So the no-headroom verdict is **not a sampling artifact** — it's one-arm (vector) dominance, *because the keyword arm contributes nothing on these queries.* Routing is rejected robustly **for the pipeline as built**.

> **But the keyword arm isn't weak — it's mis-fed (deep-dive + fix, measured).** GBrain's keyword search is conjunctive: `websearch_to_tsquery('english', q)` ANDs every token over chunk-grain, so all terms must co-occur in one chunk. Bare exact tokens rank **~1.0** (`Itochu Marubeni Mitsubishi Mitsui Sumitomo` → the houses page at 0.993); adding context words (`… trading houses`, or any natural question) ANDs to **0** — every extra token is one more clause the answer chunk must also satisfy. The fix is one query-rewrite on *our* side, no GBrain change: drop stop/question words and **OR-join** the salient tokens (`a OR b OR c`), turning AND into best-match. Measured (`src/route_eval_kwpp.ts`, 24-Q balanced set): the keyword arm jumps **grnd@C 0.271 → 0.799** and **g@C:kw 0.500 → 1.000** — and with keyword finally competitive, per-query routing's oracle headroom *returns*: **+0.065** vs the fixed hybrid (`4/24` questions where a single arm strictly beats hybrid), up from +0.008. So "routing rejected / vector dominates" traced entirely to the **conjunctive-keyword × verbose-query mismatch** — fixable upstream. The *cleaner* move is to preprocess the keyword query **inside the arm** so global hybrid improves (no router needed); routing's gain is modest and its oracle is unattainable — a real classifier captures less (the heuristic still *lost*). Lesson: fix the query shape, not the arm — and the biggest architectural verdicts can rest on one `AND`-vs-`OR` default.

**Result — keyword revival, all five arms (re-verified 2026-06-07, `GOLDEN_EVAL=data/golden_balanced.json bun src/route_eval_kwpp.ts`, 24 Q · K=5 C=3):**

| arm | grnd@C | g@C:kw | g@C:vec | g@C:mixed |
|---|---|---|---|---|
| `key` (raw, conjunctive) | 0.271 | 0.500 | 0.000 | 0.375 |
| **`key_pp` (OR-preprocessed)** | **0.799** | **1.000** | 0.588 | 0.824 |
| `vector` | 0.811 | 0.925 | 0.763 | 0.647 |
| `hyb` (GBrain default hybrid) | 0.823 | 0.925 | 0.745 | 0.763 |
| `hyb_pp` = RRF(`key_pp`, `vector`) | 0.823 | 0.950 | 0.695 | 0.824 |

Routing with the revived keyword arm — **three of these four numbers are computed *per question*, so only the first is a cell you can read off the table above:**

- **global `hyb_pp` = 0.823** — *this one is in the table*: the `hyb_pp` row, `grnd@C` column. It's the shippable single-policy baseline.
- **oracle = 0.887** — *not in the table.* For each of the 24 questions, take the **best** of `key_pp` / `vector` / `hyb_pp` *for that question*, then average those 24 winners. It needs the per-question values (dumped in `results/principle_slugs.json`), not the column means.
- **Δ +0.065** — derived: `oracle − global` = 0.887 − 0.823.
- **4/24** — *not in the table*: the count of questions where some arm's per-question score strictly beats `hyb_pp`.

**Why oracle isn't a cell:** the table shows *average-then-display* (each cell = the mean over 24 Q for one arm). Oracle is *max-per-question-then-average* — it picks the winner **inside each question first**. Because `max-then-average ≠ average-of-columns`, 0.887 can't be recovered from the column means, and it must sit above every column (0.887 > the best column, 0.823). That gap is exactly the unattainable ceiling — no real classifier knows the per-question best in advance. Reading the columns (these all *are* table cells): OR-preprocessing lifts `key` on *every* class (`g@C:kw` 0.500 → 1.000; `g@C:vec` 0.000 → 0.588 — even paraphrases share enough salient tokens to escape the AND-to-zero trap), but raw `vector` (0.811) and `hyb` (0.823) still match or beat `key_pp` (0.799) overall, so the revived keyword buys **routing headroom, not a new global winner**. And note `hyb_pp` (0.823) now exactly *equals* plain `hyb` (0.823) — OR-fusing the revived keyword into hybrid is **neutral** for the global policy (an earlier, corpus-overfit stop-list made it *trail*; with a generic stop-list that artifact is gone). The +0.065 only exists under an oracle that peeks at labels; the shippable global default is left no better.

---

**`src/route_eval_kwpp.ts` — keyword-revival probe**

This script measures whether OR-preprocessing the keyword query revives the conjunctive-FTS arm and, if so, whether that creates per-query routing headroom. It scores five arms (`key`, `key_pp`, `vector`, `hyb`, `hyb_pp`) on the 24-Q balanced golden set and then computes oracle vs global-`hyb_pp` to quantify the routing ceiling.

**When to use:** reach for `route_eval_kwpp.ts` when you suspect the keyword arm is broken by verbose or conjunctive queries and want to measure whether an OR-rewrite fixes it - and whether that fix reopens routing headroom. Use `route_eval.ts` instead when the keyword arm health is already known and you just want the standard three-arm routing ceiling.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  ENV["ENV: GOLDEN_EVAL<br/>POLICY_K · POLICY_C"] --> LOAD[Load golden JSON<br/>GoldenQ list]
  LOAD --> BOOT[Bootstrap GBrain engine<br/>loadConfig · createEngine<br/>connectWithRetry]
  BOOT --> LOOP[for each golden question]
  LOOP --> KR[searchKeyword<br/>raw q]
  LOOP --> PP[preprocessOR q<br/>drop stopwords<br/>OR-join tokens]
  PP --> KPP[searchKeyword<br/>preprocessed q]
  LOOP --> VEC[searchVector<br/>embed q]
  LOOP --> HYB[hybridSearch<br/>raw q]
  KPP --> HYBPP["RRF(key_pp, vector)<br/>hyb_pp"]  
  KR --> GK[ground key]
  KPP --> GKPP[ground key_pp]
  VEC --> GV[ground vector]
  HYB --> GH[ground hyb]
  HYBPP --> GHP[ground hyb_pp]
  GK & GKPP & GV & GH & GHP --> SCORES[score arrays<br/>per arm · 24 Q]
  SCORES --> TABLE[Print arm table<br/>grnd@C · per-domain]
  SCORES --> ORACLE["oracle = mean(max per Q<br/>over key_pp / vector / hyb_pp)"]
  ORACLE --> HEADROOM[Print routing headroom<br/>global hyb_pp · oracle · Δ<br/>wins / total]
```
*`route_eval_kwpp.ts` data flow. Five arms are scored in parallel per question; the arm table reveals the AND-vs-OR gap; the oracle block reveals how much routing headroom the revived keyword arm reopens.*

**Code (`src/route_eval_kwpp.ts`):**

```typescript
/**
 * route_eval_kwpp.ts — does KEYWORD-QUERY PREPROCESSING revive the keyword arm,
 * and does that re-open per-query routing headroom?
 *
 * Diagnosis (deep-dive): GBrain's keyword arm uses conjunctive `websearch_to_tsquery`
 * over chunk-grain — every query token must co-occur in one chunk, so verbose queries
 * (natural questions, padded exact queries) AND to ZERO. Bare exact tokens rank ~1.0.
 *
 * Fix tested here, entirely on OUR side (no GBrain change): preprocess the keyword query —
 * drop stop/question words, then **OR-join** the salient tokens. OR (`a OR b OR c`) switches
 * websearch from AND to best-match, so a missing token lowers rank instead of zeroing the match.
 *
 * Arms scored with the same discounted grounding@C as the policy:
 *   key      — engine.searchKeyword(raw q)            (conjunctive, current behavior)
 *   key_pp   — engine.searchKeyword(preprocessOR(q))  (the fix)
 *   vector   — engine.searchVector(embed(q))
 *   hyb      — hybridSearch(raw q)                     (GBrain's current hybrid)
 *   hyb_pp   — RRF(key_pp, vector)                     (fixed hybrid using the revived keyword)
 * Then: per-class grounding + oracle{key_pp, vector, hyb_pp} vs global(hyb_pp) → routing headroom?
 *
 * Run: GOLDEN_EVAL=data/golden_balanced.json bun src/route_eval_kwpp.ts
 */
import { readFileSync } from "node:fs";

import { budgetScore, coverage } from "./grounding.ts";
import { preprocessOR } from "./query_routing.ts";

const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;
const GOLDEN = process.env.GOLDEN_EVAL ?? `${import.meta.dir}/../data/golden_eval.json`;
const K = Number(process.env.POLICY_K ?? "5");
const C = Number(process.env.POLICY_C ?? "3");

interface GoldenQ { q: string; expected_entities: string[]; domain: string }
const golden: GoldenQ[] = JSON.parse(readFileSync(GOLDEN, "utf-8")).questions;

// `preprocessOR` (drop generic stop-words, OR-join salient tokens) is the shared, corpus-AGNOSTIC
// version from ./query_routing.ts — the same one the production router uses. An earlier local copy
// baked in corpus/question-specific words (`berkshire`, `anchor`, `funding`…); that overfit the
// eval and is gone.

// ── simple RRF over two ranked slug lists ────────────────────────────────────
function rrf(a: string[], b: string[], k = 60): string[] {
  const score = new Map<string, number>();
  for (const list of [a, b]) {
    list.forEach((slug, i) => score.set(slug, (score.get(slug) ?? 0) + 1 / (k + i + 1)));
  }
  return [...score.entries()].sort((x, y) => y[1] - x[1]).map(([s]) => s);
}

// ── engine bootstrap ──────────────────────────────────────────────────────────
const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway, reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { embed } = await import(`${GB}/core/embedding.ts`);
const { hybridSearch } = await import(`${GB}/core/search/hybrid.ts`);

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
await reconfigureGatewayWithEngine(engine);

const textCache = new Map<string, string>();
async function sectionText(slug: string): Promise<string> {
  if (textCache.has(slug)) return textCache.get(slug)!;
  const p = await engine.getPage(slug);
  const t = p ? `${p.title}\n${p.compiled_truth}\n${p.timeline}`.toLowerCase() : "";
  textCache.set(slug, t);
  return t;
}
async function ground(slugs: string[], ents: string[]): Promise<number> {
  const covs = await Promise.all(slugs.slice(0, C).map(async s => coverage(await sectionText(s), ents)));
  return budgetScore(covs, C).gDisc;
}
const slugsOf = (rs: { slug: string }[]) => rs.map(r => r.slug);

// ── per-question scoring across the five arms ────────────────────────────────
type Arm = "key" | "key_pp" | "vector" | "hyb" | "hyb_pp";
const arms: Arm[] = ["key", "key_pp", "vector", "hyb", "hyb_pp"];
const score = Object.fromEntries(arms.map(a => [a, [] as number[]])) as Record<Arm, number[]>;

for (const g of golden) {
  const ents = g.expected_entities;
  const keyRaw = slugsOf(await engine.searchKeyword(g.q, { limit: K }));
  const keyPP = slugsOf(await engine.searchKeyword(preprocessOR(g.q), { limit: K }));
  const vec = slugsOf(await engine.searchVector(await embed(g.q), { limit: K }));
  const hyb = slugsOf(await hybridSearch(engine, g.q, { limit: K, expansion: false, rrfK: 60 }));
  const hybPP = rrf(keyPP, vec).slice(0, K);
  score.key.push(await ground(keyRaw, ents));
  score.key_pp.push(await ground(keyPP, ents));
  score.vector.push(await ground(vec, ents));
  score.hyb.push(await ground(hyb, ents));
  score.hyb_pp.push(await ground(hybPP, ents));
}

// ── report ───────────────────────────────────────────────────────────────────
const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const pad = (s: string, n: number) => s.padEnd(n);
const f = (x: number) => x.toFixed(3);
const domains = [...new Set(golden.map(g => g.domain))];
const meanFor = (a: Arm, d?: string) => mean(score[a].filter((_, i) => !d || golden[i].domain === d));

console.log(`route_eval_kwpp: ${golden.length} questions · K=${K} C=${C}\n`);
console.log(pad("arm", 10) + pad("grnd@C", 9) + domains.map(d => pad(`g@C:${d}`, 9)).join(""));
console.log("-".repeat(10 + 9 + domains.length * 9));
for (const a of arms) {
  console.log(pad(a, 10) + pad(f(meanFor(a)), 9) + domains.map(d => pad(f(meanFor(a, d)), 9)).join(""));
}

// routing headroom with the REVIVED keyword arm: oracle over {key_pp, vector, hyb_pp} vs global hyb_pp
const routeArms: Arm[] = ["key_pp", "vector", "hyb_pp"];
const global = mean(score.hyb_pp);
const oracle = mean(golden.map((_, i) => Math.max(...routeArms.map(a => score[a][i]))));
const wins = golden.filter((_, i) => {
  const best = Math.max(...routeArms.map(a => score[a][i]));
  return best > score.hyb_pp[i] + 1e-9;   // a non-hybrid arm strictly beats fixed-hybrid
}).length;
console.log(`\nrouting (with revived keyword): global hyb_pp ${f(global)} · oracle ${f(oracle)} · Δ ${f(oracle - global)}`);
console.log(`${wins}/${golden.length} questions where some arm strictly beats hyb_pp (real routing headroom)`);

await engine.disconnect?.();
process.exit(0);
```

**Walkthrough:**
- **Five arms, one loop - the design is comparative, not productive.** The script's purpose is measurement, not retrieval. All five arms (`key`, `key_pp`, `vector`, `hyb`, `hyb_pp`) run on the same 24 questions using the same `grounding.ts` primitive (`budgetScore(...).gDisc`) so any score difference is purely the query-rewrite or fusion choice, not a metric artifact.
- **`preprocessOR` is imported from `query_routing.ts`, not redefined.** An earlier iteration had a local stop-list that included corpus-specific tokens (`berkshire`, `anchor`...) - that overfit the eval and made `hyb_pp` trail `hyb`. Importing the production-shared, corpus-agnostic version removes that artifact: `hyb_pp` now ties `hyb` globally (0.823 = 0.823), confirming the preprocessing is neutral as a global policy change.
- **`rrf` is inlined (not imported) because this is a measurement instrument.** The script needs its own local `rrf` to construct `hyb_pp = RRF(key_pp, vector)` without depending on GBrain's hybrid path - it is deliberately building a hypothetical arm to measure, not calling the production hybrid. Inlining keeps the probe self-contained and auditable.
- **`sectionText` with `textCache` avoids re-fetching pages.** The same slug can appear in multiple arms' top-K across different questions; caching the compiled text means each page is fetched from Postgres at most once per run, not once per (question x arm x rank) hit.
- **The oracle block is the load-bearing output.** The per-arm table answers "is `key_pp` competitive?"; the oracle block answers "does that competitiveness reopen routing headroom?" - `oracle = mean(max per Q over key_pp / vector / hyb_pp)` is the ceiling no real classifier can reach, and `Δ = oracle - global` is the available prize. On 24 Q with OR-preprocessing: Δ +0.065 with 4/24 movers vs Δ +0.008 with raw keyword - the entire routing-headroom story depends on which keyword arm you hand the classifier.

---

**Answer-quality check — and a generation confound caught in the act.** Grounding takes the *max* coverage over the top-C, so it's blind to whether the *other* in-budget chunks are distractors. So we judged the answers too (`src/answer_route_ab.py`): generate from the global-hybrid context vs the routed context, LLM-judge against each question's `pass_criteria`. Run on **two generator tiers**:

| generator | global pass | routed pass | Δ | on differing-context Qs |
|---|---|---|---|---|
| local 14B (Qwen-Coder) | 1.000 | 0.750 | −0.250 | 1.000 → 0.500 |
| **Claude Opus 4.5** | 0.917 | 0.917 | **+0.000** | 0.800 → 0.800 |

The weak 14B *regressed* under routing — but Opus shows **Δ 0**, identical even on the questions whose context differed. The regression was the **generator's** context-composition sensitivity, **not** a retrieval effect: a weak model is rattled by a different (grounding-tied) context; a capable one extracts the answer regardless. This is the *confounding* trap named in `Engineering Decision Patterns` — scoring a retrieval choice by answer quality mixes in generation variance; pin the generator (here: a strong model) before attributing a delta to retrieval. **Verdict (this natural, vector-skewed corpus): keep the single global hybrid policy.** *Here* routing adds a classifier, a per-query branch, and a calibration surface for *zero* gain — and its one apparent win was a weak-model artifact. (Deterministic ceiling: `bun src/route_eval.ts`; answer A/B: `uv run python src/answer_route_ab.py` with `CHAT_MODEL` set.) **But that verdict is the *corpus's*, not the *principle's*** — the next subsection re-tests the honest version (route to the *fixed* keyword arm, on a workload that actually spans query types) and the result **reverses**: routing wins on both grounding and answer quality, even on a strong generator.

**When to use:** Reach for `answer_route_ab.py` when you want to test whether per-query routing changes *answer quality* (not just grounding coverage) on the natural, vector-skewed corpus - specifically to separate a retrieval effect from a generator-sensitivity effect before accepting or rejecting the routing design.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  SLUGS[(route_slugs.json<br/>from route_eval.ts)] --> LOAD[load per-question<br/>global_slugs +<br/>routed_slugs]
  GT[(W2.7 ground truth<br/>pass_criteria<br/>tenk Qs only)] --> CRIT[_pass_criteria_by_q]
  CRIT --> LOOP
  LOAD --> LOOP[for each tenk Q]
  LOOP --> DIFFERS{routed ≠ global?}
  DIFFERS -->|"yes (DIFF)"| GBOTH[build both contexts<br/>via build_context]
  DIFFERS -->|"no (same)"| GBOTH
  GBOTH --> GA[_answer<br/>global_slugs + Q]
  GBOTH --> RA[_answer<br/>routed_slugs + Q]
  GA --> GJ[_judge vs criteria<br/>PASS / FAIL]
  RA --> RJ[_judge vs criteria<br/>PASS / FAIL]
  GJ --> ROWS[accumulate rows]
  RJ --> ROWS
  ROWS --> REPORT[pass rates<br/>global vs routed<br/>+ DIFF-context split]
```
*`answer_route_ab.py` flow. Pre-computed slugs arrive from `route_eval.ts`; the script only runs generation + judgment. DIFF-context questions (routed_slugs ≠ global_slugs) are reported separately so a corpus-level tie doesn't hide per-question movement.*

**Code (`src/answer_route_ab.py`):**

```python
"""answer_route_ab.py — does per-query ROUTING beat global hybrid at ANSWER time?

route_eval.ts already showed routing has ZERO *grounding* headroom on this corpus
(hybrid weakly dominates per-query). This script tests the one effect grounding can't
see: discounted grounding takes the *max* coverage over the top-C, so it ignores
whether the OTHER chunks in the budget are distractors. Two contexts with the same
best chunk score identically — but the generator reads all C, and hybrid's fused set
may carry distractors a clean single-arm set avoids. So we judge the ANSWERS.

For each tenk golden question (those carry `pass_criteria` in eval_ground_truth.json):
  - build the GLOBAL-hybrid context (top-C pages) and the ROUTED best-arm context,
  - generate an answer from each (temp 0, VibeProxy → Claude),
  - LLM-judge each PASS/FAIL against the question's pass_criteria,
  - compare pass rates. Questions where routed_slugs == global_slugs are identical by
    construction (reported separately — they can't show a difference).

Inputs: results/route_slugs.json (from `bun src/route_eval.ts`) + the W2.7 ground truth.
Run: uv run python src/answer_route_ab.py
"""
from __future__ import annotations

import json
import os
import pathlib
import time

from openai import APIConnectionError, APIError

from ground_truth_ab import _MEMZERO_TMPL, _ask, _client, gbrain_get


class LLMUnavailable(RuntimeError):
    """The chat endpoint refused after retries — skip this question, don't crash the run."""


def _resilient(fn, *args, retries: int = 4, backoff: float = 2.0):
    """Retry an LLM call through transient connection drops (the local 14B MLX chat
    server falls over under memory pressure). Raise LLMUnavailable if it never recovers."""
    for attempt in range(retries):
        try:
            return fn(*args)
        except (APIConnectionError, APIError) as exc:
            if attempt == retries - 1:
                raise LLMUnavailable(str(exc)) from exc
            time.sleep(backoff * (attempt + 1))
    raise LLMUnavailable("unreachable")

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SLUGS = _ROOT / "results" / "route_slugs.json"
_GROUND_TRUTH = pathlib.Path(
    "~/code/agent-prep/lab-02-7-pageindex/data/eval_ground_truth.json").expanduser()

_JUDGE_TMPL = (
    "You are grading a candidate answer against a rubric. Reply with EXACTLY one word: "
    "PASS or FAIL.\n\nRUBRIC (what makes the answer correct):\n{criteria}\n\n"
    "CANDIDATE ANSWER:\n{answer}\n\nVerdict (PASS or FAIL):"
)


def _pass_criteria_by_q() -> dict[str, str]:
    """Map question text → pass_criteria from the W2.7 ground-truth (tenk questions)."""
    raw = json.loads(_GROUND_TRUTH.read_text())
    out: dict[str, str] = {}
    for key, entry in raw.items():
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        if entry.get("q") and entry.get("pass_criteria"):
            out[entry["q"].strip()] = entry["pass_criteria"]
    return out


class SnippetRegression(RuntimeError):
    """A reader injected a truncated `query --json` snippet instead of a full
    `gbrain get` body — the failure mode the lab fixed once and must not regress to."""


_MIN_BODY_CHARS = 80   # a `gbrain get` page body; a `query --json` snippet is a short fragment
# Optional per-body char cap. Default 0 = full bodies (unchanged). Set MAX_BODY_CHARS to
# fit a small-context generator (e.g. the local 14B chokes on ~70K-token 10-K sections).
_MAX_BODY_CHARS = int(os.getenv("MAX_BODY_CHARS", "0"))
_body_check_logged = False


def build_context(slugs: list[str]) -> str:
    """Assemble reader context from FULL `gbrain get` page bodies — never the truncated
    `query --json` snippet (which lacks the grounding the generator needs; ground_truth_ab
    gotcha #1). Guards the seam: logs body sizes once so a regression is visible, and raises
    SnippetRegression (fail loud) if any injected body is suspiciously short. MAX_BODY_CHARS
    (opt-in) caps each body for small-context generators."""
    global _body_check_logged
    bodies = [gbrain_get(s) for s in slugs]
    if _MAX_BODY_CHARS:
        bodies = [b[:_MAX_BODY_CHARS] for b in bodies]
    sizes = [len(b.strip()) for b in bodies]
    if not _body_check_logged:
        print(f"  [reader] full-body check: {len(slugs)} slugs, body chars={sizes} "
              f"(via `gbrain get`, not `query --json` snippets)")
        _body_check_logged = True
    short = [(s, n) for s, n in zip(slugs, sizes) if n < _MIN_BODY_CHARS]
    if short:
        raise SnippetRegression(
            f"injected body too short {short} — reader must pull full `gbrain get` bodies, "
            f"not `query --json` snippets")
    return "\n\n".join(bodies)


def _answer(client, slugs: list[str], q: str) -> str:
    ctx = build_context(slugs)
    msg = [{"role": "user", "content": _MEMZERO_TMPL.format(ctx=ctx, q=q)}]
    ans, _ = _resilient(_ask, client, msg)
    return ans


def _judge(client, answer: str, criteria: str) -> bool:
    msg = [{"role": "user", "content": _JUDGE_TMPL.format(criteria=criteria, answer=answer)}]
    verdict, _ = _resilient(_ask, client, msg)
    return verdict.strip().upper().startswith("PASS")


def main() -> None:
    dump = json.loads(_SLUGS.read_text())
    criteria_by_q = _pass_criteria_by_q()
    client = _client()

    rows: list[tuple[str, bool, bool, bool]] = []  # (q, differs, global_pass, routed_pass)
    for item in dump:
        q = item["q"].strip()
        criteria = criteria_by_q.get(q)
        if criteria is None:
            continue  # entity questions have no pass_criteria — skip (judge needs a rubric)
        differs = item["routed_slugs"] != item["global_slugs"]
        try:
            g_pass = _judge(client, _answer(client, item["global_slugs"], q), criteria)
            r_pass = _judge(client, _answer(client, item["routed_slugs"], q), criteria)
        except LLMUnavailable as exc:
            print(f"  [skip] chat endpoint down — {q[:52]} ({exc})")
            continue
        rows.append((q, differs, g_pass, r_pass))
        tag = "DIFF" if differs else "same"
        print(f"  [{tag}] global={'P' if g_pass else 'F'} routed={'P' if r_pass else 'F'}  {q[:52]}")

    n = len(rows)
    g_rate = sum(g for _, _, g, _ in rows) / n if n else 0.0
    r_rate = sum(r for _, _, _, r in rows) / n if n else 0.0
    diff = [row for row in rows if row[1]]
    print(f"\njudged {n} tenk questions ({len(diff)} have a routed≠global context)")
    print(f"  global (hybrid) pass rate : {g_rate:.3f}")
    print(f"  routed (per-query) pass   : {r_rate:.3f}   Δ {r_rate - g_rate:+.3f}")
    if diff:
        dg = sum(g for _, _, g, _ in diff) / len(diff)
        dr = sum(r for _, _, _, r in diff) / len(diff)
        print(f"  on the {len(diff)} DIFF-context questions: global {dg:.3f} → routed {dr:.3f}  Δ {dr - dg:+.3f}")


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **Design principle - separate the retrieval question from the generation question.** Grounding@C is blind to distractor chunks: two slug sets that share the top-1 answer page score identically even if one includes three off-topic pages the generator must read past. This script provides the complementary signal - does changing the context (same question, different slug set) change the *answer*? Running two generators side-by-side (local 14B, Opus) isolates whether a delta is a retrieval effect or a generator-sensitivity effect.
- **Pre-computed slugs decouple retrieval cost from generation cost.** `route_slugs.json` (written by `bun src/route_eval.ts`) already contains both `global_slugs` and `routed_slugs` for every question. This script never touches the vector DB - it only calls `gbrain_get` for page bodies. That separation means you can re-run the answer A/B with a different `CHAT_MODEL` (swap generator tier) without re-running retrieval, and it keeps the LLM call count manageable (2 generates + 2 judges per question, not `num_arms × num_questions` as in `verify_arch.py`).
- **`build_context` guards the snippet-vs-body seam.** The critical invariant is that the generator receives *full page bodies* (`gbrain get`), not the short snippets `query --json` returns. `_MIN_BODY_CHARS = 80` catches the regression at runtime - a short body raises `SnippetRegression` immediately rather than silently feeding a context-starved generator. `MAX_BODY_CHARS` (env, default 0 = off) is the escape valve for small-context local models that choke on 70K-token 10-K sections.
- **`_resilient` wraps every LLM call because local inference is fragile under memory pressure.** The 14B MLX server can drop connections mid-run. Rather than crashing the whole experiment, `_resilient` retries with linear backoff (4 attempts, 2/4/6/8 s gaps). If it never recovers, `LLMUnavailable` is raised; `main` catches it per-question with a `[skip]` log so the run continues and the final pass rate is computed over the questions that did complete.
- **DIFF-context split is the load-bearing diagnostic.** Questions where `routed_slugs == global_slugs` are identical by construction and cannot show a delta - including them in the headline rate would dilute any real signal. The script reports both the full-set rate and the subset where contexts actually differ, so a corpus-level tie (Δ 0) that hides a large per-question swing is visible rather than masked.
- **`_judge` is a one-word gate.** The prompt ends with `Verdict (PASS or FAIL):` and the parser calls `.startswith("PASS")` after stripping. This is deliberately narrow - a partial-credit rubric would require a scoring prompt and a float parser, adding both prompt complexity and judge variance. Binary PASS/FAIL on a `pass_criteria` rubric is the cheapest judge that still tests the real objective (does the answer satisfy the information need?).

##### Re-tested with the keyword fix — routing accepted on a mixed-type workload (2026-06-07)

The rejection above rests on two things the *natural* corpus baked in: it is vector-skewed (one dominant query type), and `route_eval.ts` routed `kw` queries to the **raw** keyword arm — the one GBrain's conjunctive FTS had crippled (it scored `g@C:kw` 0.500, *worse* than hybrid's 0.925, so "route to keyword" could only lose). Fix both and the original design principle gets a fair trial: classify each query by type and send it to the arm that fits — `kw → key_pp` (the OR-preprocessed keyword arm), `vec → vector`, `mixed → hyb`. Three policies, balanced 24-Q set, deterministic classifier (24/24 vs the gold type label), `src/route_principle_ab.ts`:

**Grounding A/B (discounted grounding@C):**

| policy                                                      | grnd@C    | g@C:kw    | g@C:vec | g@C:mixed | Δ vs baseline |
| ----------------------------------------------------------- | --------- | --------- | ------- | --------- | ------------- |
| baseline (global `hyb`)                                     | 0.823     | 0.925     | 0.745   | 0.763     | —             |
| **router** (`kw`→`key_pp` · `vec`→`vector` · `mixed`→`hyb`) | **0.862** | **1.000** | 0.763   | 0.763     | **+0.039**    |
| strengthened-global (`hyb` on OR-preprocessed query)        | 0.837     | 1.000     | 0.745   | 0.658     | +0.014        |

The router strictly beats baseline on **+2 / 0 worse / 22 tie** — only **2 of the 24** questions move; the other 22 route to the arm baseline already used, so they're identical. Here are the **2 movers** (the rows where `router ≠ baseline`, from `bun src/route_principle_ab.ts`):

| question | routed type → arm | baseline `hyb` | router | gain |
|---|---|---|---|---|
| `Itochu Marubeni Mitsubishi Mitsui Sumitomo…` | `kw` → `key_pp` | 0.252 | **1.000** | +0.748 |
| `how the company guards against digital intrusions…` | `vec` → `vector` | 0.315 | **0.500** | +0.185 |

Both are answer pages that global hybrid's RRF **demoted** below the 3-chunk reader budget (so `hyb` scores them low — 0.252, 0.315); routing each to the arm its type favours recovers the page — one via the OR-preprocessed keyword arm, one via dense vector. Note the +2 are **not** both keyword queries: one `kw`, one `vec` — routing helps wherever the global arm buried the answer, not just on exact-token lookups. The whole +0.039 is just these two: `(0.748 + 0.185) / 24 = +0.039`; the other 22 contribute 0. (This is also why the `kw`-class *mean* moved `g@C:kw` 0.925 → 1.000 — nine of ten `kw` questions already scored 1.0 under hybrid; only `Itochu` was demoted, and `key_pp` fixes it.) The *strengthened-global* alternative (no router — just OR-preprocess the whole query before hybrid) edges baseline by only **+0.014** and still trails the router (0.862) by a wide margin: OR-joining the whole query slightly helps the keyword leg but does nothing for the dense leg, so it can't recover the `kw`-class queries the way a router pointed at `key_pp` does. So the principle **must** be honored by a router, not by strengthening the single global arm.

**Answer-quality A/B (entity coverage, pinned Opus 4.5 — `src/answer_principle_ab.py`):**

`answer_principle_ab.py` closes the loop that `route_principle_ab.ts` opened: grounding measures whether the right chunks were retrieved, but this script asks whether a *strong generator* can turn those chunks into correct answers. It reads the slug-sets already dumped by `route_principle_ab.ts`, fetches full `gbrain get` page bodies for each arm, generates an answer with a pinned Opus model, and judges pass/fail by entity coverage - so the verdict reflects retrieval quality, not small-model fragility.

**When to use:** reach for this script (rather than `answer_route_ab.py`) when you want to confirm that the *3-way routing principle* (baseline vs router vs strengthened-global) holds at answer time on the balanced, multi-type question set - i.e. when you need entity-coverage judgement rather than `pass_criteria` judgement, and the slug source is `principle_slugs.json` rather than `route_slugs.json`.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  SLUGS["results/principle_slugs.json<br/>(baseline · router · strong_g<br/>slug lists + expected_entities)"] --> LOOP["for each question"]
  LOOP --> ARM["for each arm<br/>(baseline · router · strong_g)"]
  ARM --> BUILD["build_context()<br/>gbrain_get per slug<br/>→ full page bodies"]
  BUILD --> GUARD{"body length<br/>≥ MIN_BODY_CHARS?"]
  GUARD -->|"no"| ERR["raise SnippetRegression<br/>(snippet, not full body)"]
  GUARD -->|"yes"| ANS["_answer()<br/>MEMZERO_TMPL + Opus<br/>via _resilient()"]
  ANS --> JUDGE["_judge()<br/>JUDGE_TMPL → PASS/FAIL<br/>entity coverage"]
  JUDGE --> ACC["accumulate passes[]<br/>+ types[]"]
  ACC --> PRINT["per-arm pass-rate table<br/>broken out by kw/vec/mixed"]
```

*`answer_principle_ab.py` data flow: slug lists in, full bodies fetched, Opus generates answer, judge scores entity coverage, per-arm pass-rates printed.*

**Code (`src/answer_principle_ab.py`):**

```python
"""answer_principle_ab.py — does the per-query ROUTER produce better ANSWERS than global
hybrid (and than a strengthened global), on a PINNED strong generator?

route_principle_ab.ts settled the *grounding* A/B on the balanced set: router 0.862 beats
baseline hybrid 0.823 (+0.039), strengthened-global loses. Grounding takes the max coverage
over the top-C, so it can't see whether the OTHER in-budget chunks are distractors. This
script closes that gap at answer time: for each balanced question, generate an answer from
each policy's context and judge whether it actually identifies the question's expected
entities. Pin a STRONG generator (Opus via VibeProxy) so the verdict reflects retrieval, not
the small-model context-sensitivity confound caught earlier (answer_route_ab.py).

The balanced set carries `expected_entities`, not W2.7 `pass_criteria`, so the judge rubric is
"the answer correctly identifies <entities>" — answer-level coverage, aligned with grounding.

Inputs: results/principle_slugs.json (from `bun src/route_principle_ab.ts`).
Run:    CHAT_MODEL=claude-opus-4-5 JUDGE_MODEL=claude-opus-4-5 uv run python src/answer_principle_ab.py
"""
from __future__ import annotations

import json
import os
import pathlib
import time

from openai import APIConnectionError, APIError

from ground_truth_ab import _MEMZERO_TMPL, _ask, _client, gbrain_get

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SLUGS = _ROOT / "results" / "principle_slugs.json"
_ARMS = ("baseline", "router", "strong_g")
_MIN_BODY_CHARS = 80
_MAX_BODY_CHARS = int(os.getenv("MAX_BODY_CHARS", "0"))

_JUDGE_TMPL = (
    "You are grading whether a candidate answer correctly identifies the required facts. "
    "Reply with EXACTLY one word: PASS or FAIL.\n\n"
    "The answer PASSES only if it correctly names/identifies ALL of these (synonyms and the "
    "full entity for an abbreviation are fine):\n{entities}\n\n"
    "CANDIDATE ANSWER:\n{answer}\n\nVerdict (PASS or FAIL):"
)


class LLMUnavailable(RuntimeError):
    """Chat endpoint refused after retries — skip the question, don't crash the run."""


class SnippetRegression(RuntimeError):
    """A body came back as a truncated `query --json` snippet, not a full `gbrain get` page."""


def _resilient(fn, *args, retries: int = 4, backoff: float = 2.0):
    for attempt in range(retries):
        try:
            return fn(*args)
        except (APIConnectionError, APIError) as exc:
            if attempt == retries - 1:
                raise LLMUnavailable(str(exc)) from exc
            time.sleep(backoff * (attempt + 1))
    raise LLMUnavailable("unreachable")


def build_context(slugs: list[str]) -> str:
    """Assemble reader context from FULL `gbrain get` page bodies (never `query --json`
    snippets — the grounding-loss gotcha). Fail loud if a body is suspiciously short."""
    bodies = [gbrain_get(s) for s in slugs]
    if _MAX_BODY_CHARS:
        bodies = [b[:_MAX_BODY_CHARS] for b in bodies]
    short = [(s, len(b.strip())) for s, b in zip(slugs, bodies) if len(b.strip()) < _MIN_BODY_CHARS]
    if short:
        raise SnippetRegression(f"injected body too short {short} — pull full `gbrain get` bodies")
    return "\n\n".join(bodies)


def _answer(client, slugs: list[str], q: str) -> str:
    msg = [{"role": "user", "content": _MEMZERO_TMPL.format(ctx=build_context(slugs), q=q)}]
    ans, _ = _resilient(_ask, client, msg)
    return ans


def _judge(client, answer: str, entities: list[str]) -> bool:
    rubric = "; ".join(entities)
    msg = [{"role": "user", "content": _JUDGE_TMPL.format(entities=rubric, answer=answer)}]
    verdict, _ = _resilient(_ask, client, msg)
    return verdict.strip().upper().startswith("PASS")


def main() -> None:
    dump = json.loads(_SLUGS.read_text())
    client = _client()
    print(f"generator/judge: {os.getenv('CHAT_MODEL', '(default)')} · {len(dump)} questions\n")

    # per-arm pass flags, and per-class accumulators
    passes: dict[str, list[bool]] = {a: [] for a in _ARMS}
    types: list[str] = []
    for item in dump:
        q = item["q"].strip()
        ents = item["expected_entities"]
        row = {}
        try:
            for arm in _ARMS:
                ans = _answer(client, item[f"{arm}_slugs"], q)
                row[arm] = _judge(client, ans, ents)
        except LLMUnavailable as exc:
            print(f"  [skip] chat endpoint down — {q[:48]} ({exc})")
            continue
        for arm in _ARMS:
            passes[arm].append(row[arm])
        types.append(item["type"])
        differs = item["router_slugs"] != item["baseline_slugs"]
        tag = "DIFF" if differs else "same"
        flags = " ".join(f"{a[:4]}={'P' if row[a] else 'F'}" for a in _ARMS)
        print(f"  [{tag}] {flags}  ({item['type']}) {q[:46]}")

    n = len(types)
    if not n:
        print("\nno questions judged (endpoint down?)")
        return
    rate = lambda a, cls=None: (  # noqa: E731
        sum(p for p, t in zip(passes[a], types) if cls is None or t == cls)
        / max(1, sum(1 for t in types if cls is None or t == cls)))
    base = rate("baseline")
    print(f"\njudged {n} questions on a pinned generator")
    classes = ["kw", "vec", "mixed"]
    hdr = f"  {'policy':12}{'pass':8}" + "".join(f"{'p:'+c:9}" for c in classes) + "Δ vs base"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for a in _ARMS:
        cols = "".join(f"{rate(a, c):<9.3f}" for c in classes)
        print(f"  {a:12}{rate(a):<8.3f}{cols}{rate(a) - base:+.3f}")


if __name__ == "__main__":
    main()
```

**Walkthrough:**

- **Design principle - pin a strong generator to isolate retrieval.** The whole point is to measure retrieval quality, not generator sensitivity. By pinning Opus (`CHAT_MODEL=claude-opus-4-5`) as both generator and judge, any remaining pass/fail difference between arms is attributable to context quality, not model fragility. This directly addresses the confound exposed by `answer_route_ab.py`, where small-model variance overwhelmed retrieval signal.
- **`build_context()` - full bodies only, never snippets.** Slugs are fetched via `gbrain_get()` (the full `gbrain get` page body), not the `query --json` snippet path. The `_MIN_BODY_CHARS = 80` guard + `SnippetRegression` exception exist because a previous version of the pipeline accidentally injected truncated query snippets instead of full pages, silently tanking context quality without any visible error. The guard makes that regression loud and immediate.
- **Entity-coverage judge, not `pass_criteria` judge.** The balanced set (`golden_balanced.json`) carries `expected_entities` fields (e.g. `["ridgeline-capital", "dev-patel"]`), not the W2.7 `pass_criteria` free-text rubrics. The `_JUDGE_TMPL` is calibrated to this: it asks Opus to confirm ALL required entities are named (synonyms and abbreviations accepted), which aligns with what `discounted grounding@C` measures at the chunk level - both are entity-coverage metrics.
- **`_resilient()` wraps every LLM call, `LLMUnavailable` skips rather than crashes.** The outer loop catches `LLMUnavailable` and prints a `[skip]` line rather than aborting the run. This matters for long eval runs against VibeProxy (which can throttle mid-run) - partial results are still useful for trend analysis even if a few questions are dropped.
- **Per-class breakdown (`kw`/`vec`/`mixed`) is load-bearing.** The aggregate pass-rate can hide type-skewed gains. Printing per-class rates is what revealed that the router's +0.042 came entirely from `kw` queries (`0.800 → 0.900`), while `vec` and `mixed` held flat - confirming the routing gain is type-specific, not a broad improvement.

| policy | pass | p:kw | p:vec | p:mixed | Δ vs baseline |
|---|---|---|---|---|---|
| baseline (global `hyb`) | 0.792 | 0.800 | 0.800 | 0.750 | — |
| **router** | **0.833** | 0.900 | 0.800 | 0.750 | **+0.042** |
| strengthened-global | 0.833 | 0.900 | 0.800 | 0.750 | +0.042 |

The edge **survives a strong generator** (+0.042 on Opus, on par with the grounding gap): the router fixes answers global hybrid gets wrong — `Itochu…` F→**P**, `Item 8 Notes` F→**P** — net +1 question after one regression (`Item 1C` P→F), with ~1 question of Opus judge variance at temp 0. Modest, but the *direction* is the opposite of the natural-set `Δ 0`: there routing changed nothing real on a one-type corpus; here, on a workload that spans types, routing recovers compromised queries at *answer* time, not just at grounding time — Opus still cannot extract an answer from a wrong-context chunk set. (An earlier, corpus-overfit keyword stop-list had inflated this to +0.083; the generic stop-list gives the honest +0.042.)

**Why router and strengthened-global show an *identical* +0.042 here — and why it isn't a tie.** Both pass **20/24**, but on *different* questions: the router passes `the part of the filing that lists what could go wrong` (F for strong_g) while strong_g passes `which venture firm is the angel investor` (F for the router). The two diffs cancel, so the *aggregates* coincide even though the underlying answers don't. And the router's loss is **not** a mis-route: it correctly classified `which venture firm…` as `vec → vector`, and vector retrieved *both* answer pages (`ridgeline-capital`, `dev-patel`) — but ranked `dev-patel` at **#4**, one slot outside the `C=3` reader budget, so the generator saw Ridgeline but not Dev Patel and couldn't name the investor. `strong_g` happened to rank `dev-patel` at #3. It's a **rank-cutoff near-miss at `C=3`** (the very demotion effect `discounted grounding@C` measures) on a 2-hop question that needs two entities in the same 3-slot window — not a routing mistake. The lesson: a binary pass-rate at n=24 is **too coarse to rank router vs strengthened-global** — single-slot rank-boundary flips, not equivalence. The arms are separated by the *continuous, deterministic* metric, not this one: on **grounding** the router (0.862) clearly beats strengthened-global (0.837). So the answer A/B establishes only that *both beat baseline*; the choice between them is made on grounding + the architectural argument (strong_g can't recover the `kw`-class the way a `key_pp` route can), not on these identical pass rates.

**Refined verdict — routing is worth building, conditionally.** Per-query routing pays iff **three gates all hold**: (a) the traffic genuinely **spans query types** (keyword-focused *and* semantic), (b) the keyword arm is **OR-preprocessed** (else its target is the crippled raw arm and routing can only lose), and (c) a **cheap type-classifier** can actually detect the type. All three held here → +0.039 grounding, +0.042 answer quality. On the production brain as-is (vector-skewed, single dominant type) gate (a) fails, so the earlier "keep global hybrid" still stands *for that corpus* — and precisely so: a router doesn't *lose by design* there (it can always default to hybrid). The realizable gain decomposes as **(oracle − global) − classifier_error_cost**. On a single-type corpus the first term is **0** (oracle = global, the 0.910 = 0.910 tie), so a *perfect* router merely **ties** and a *real* classifier nets **negative** — its mis-routes have no headroom to offset them. All-risk-no-reward, so don't route. The headroom is the *budget* a router has to spend on its own classifier errors: 0 on single-type (can't afford any), +0.065 oracle on the mixed set (enough to cover a good classifier and still net +0.039 / +0.042). The honest scope: the classifier is 24/24 only because this set is built type-separable (`kw` = token-lists, `vec` = prose); real queries blur that, so +0.042 is the **strong-classifier ceiling** — production gain is ≤ that and shrinks with classifier error. Net: don't reject the principle — gate it on the workload. (Grounding A/B: `GOLDEN_EVAL=data/golden_balanced.json bun src/route_principle_ab.ts`; answer A/B: `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/answer_principle_ab.py`.)

`src/route_principle_ab.ts` is the **grounding-layer A/B harness** that gives the three-way verdict above a number. It runs every arm for every question, picks the best strengthened-global variant post-loop, routes each question by its detected type, then scores and reports all three policies in one pass. The per-arm slug dump (`results/principle_slugs.json`) feeds the downstream answer-quality A/B (`answer_principle_ab.py`) so the retrieval and answer evaluations share the same context sets.

**When to use:** reach for `route_principle_ab.ts` (instead of `route_eval.ts`) when you want a **three-way comparison** - router vs. global-hybrid baseline vs. a strengthened-global fallback - on a **balanced, multi-type golden set** where OR-preprocessed keyword retrieval is already validated; use `route_eval.ts` for the earlier single-arm routing headroom probe or when you only need the slug dump for `answer_route_ab.py`.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  ENV["GOLDEN_EVAL +<br/>POLICY_K / POLICY_C"] --> LOAD["load golden_balanced.json"]
  LOAD --> LOOP["for each question"]
  LOOP --> PP["preprocessOR(q)"]
  LOOP --> EMB["embed(q)"]
  PP --> KPP["engine.searchKeyword<br/>key_pp arm"]
  EMB --> VEC["engine.searchVector<br/>vector arm"]
  LOOP --> HYB["hybridSearch<br/>hyb arm"]
  KPP --> G1["rrf(key_pp, vec)<br/>g1 variant"]
  LOOP --> G2["hybridSearch<br/>(preprocessOR(q))<br/>g2 variant"]
  KPP --> SCORE["ground each arm<br/>budgetScore"]
  VEC --> SCORE
  HYB --> SCORE
  G1 --> SCORE
  G2 --> SCORE
  SCORE --> PICK["gWhich = better of<br/>g1 vs g2 by mean"]
  PICK --> ROUTE["classifyType per Q<br/>kw→key_pp<br/>vec→vector<br/>mixed→hyb"]
  ROUTE --> POLICIES["baseline / router /<br/>strong_g per question"]
  POLICIES --> REPORT["console: Δ vs baseline<br/>per-class breakdown<br/>win/loss/tie rows"]
  POLICIES --> DUMP["writeFileSync<br/>results/principle_slugs.json"]
```
*`route_principle_ab.ts` - 3-way routing A/B: for every golden question all five arms are scored in one loop; the best strengthened-global variant is elected after the loop; policy slugs are dumped for the answer-quality A/B downstream.*

**Code (full source `src/route_principle_ab.ts`):**

```typescript
/**
 * route_principle_ab.ts — honor the per-query principle in the LIVE path, three ways, A/B'd.
 *
 * The design intent of per-query routing: pick the arm that fits the QUERY TYPE, because a
 * single global policy compromises queries whose best arm isn't the global winner. The earlier
 * rejection (route_eval.ts) was unfair — its router targeted the RAW keyword arm, which GBrain's
 * conjunctive FTS had crippled (route_eval_kwpp.ts: raw key g@C:kw 0.500 vs preprocessed 1.000).
 * Route to the *preprocessed* keyword arm and the routing decision should finally pay on kw-class.
 *
 * Three contestants, measured with the same discounted grounding@C, on the balanced 24-Q set:
 *   baseline  — every query → global hybrid `hyb`         (the current shipped default)
 *   router    — classify query type, route kw→key_pp · vec→vector · mixed→hyb   (the principle)
 *   strong_g  — every query → strengthened global, no router:
 *                 g1 = RRF(key_pp, vector)        (hybrid w/ preprocessed keyword leg)
 *                 g2 = hybridSearch(preprocessOR(q))  (whole query preprocessed)
 *               we report whichever global variant scores higher.
 *
 * Decision: does either honor-the-principle arm beat baseline by a margin a real classifier can
 * keep? Router needs its classifier to actually detect type; strong_g needs no classifier at all.
 * Dumps per-arm top-C slugs → results/principle_slugs.json for the answer-quality A/B.
 *
 * Run: GOLDEN_EVAL=data/golden_balanced.json bun src/route_principle_ab.ts
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

import { budgetScore, coverage } from "./grounding.ts";
import { classifyType, preprocessOR, type QueryType } from "./query_routing.ts";

const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;
const GOLDEN = process.env.GOLDEN_EVAL ?? `${import.meta.dir}/../data/golden_balanced.json`;
const SLUG_DUMP = `${import.meta.dir}/../results/principle_slugs.json`;
const K = Number(process.env.POLICY_K ?? "5");
const C = Number(process.env.POLICY_C ?? "3");

interface GoldenQ { q: string; expected_entities: string[]; domain: string }
const golden: GoldenQ[] = JSON.parse(readFileSync(GOLDEN, "utf-8")).questions;

// `preprocessOR` + `classifyType` (the shippable router's brain) live in ./query_routing.ts —
// the SAME module the production actuator (query_policy.ts) imports, so this A/B validates the
// exact classifier production ships. type alias for readability:
type Type = QueryType;

// ── RRF over two ranked slug lists ───────────────────────────────────────────
function rrf(a: string[], b: string[], k = 60): string[] {
  const score = new Map<string, number>();
  for (const list of [a, b]) {
    list.forEach((slug, i) => score.set(slug, (score.get(slug) ?? 0) + 1 / (k + i + 1)));
  }
  return [...score.entries()].sort((x, y) => y[1] - x[1]).map(([s]) => s);
}

// ── engine bootstrap (identical sequence to the other probes / the CLI) ──────
const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway, reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { embed } = await import(`${GB}/core/embedding.ts`);
const { hybridSearch } = await import(`${GB}/core/search/hybrid.ts`);

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
await reconfigureGatewayWithEngine(engine);

const textCache = new Map<string, string>();
async function sectionText(slug: string): Promise<string> {
  if (textCache.has(slug)) return textCache.get(slug)!;
  const p = await engine.getPage(slug);
  const t = p ? `${p.title}\n${p.compiled_truth}\n${p.timeline}`.toLowerCase() : "";
  textCache.set(slug, t);
  return t;
}
async function ground(slugs: string[], ents: string[]): Promise<number> {
  const covs = await Promise.all(slugs.slice(0, C).map(async s => coverage(await sectionText(s), ents)));
  return budgetScore(covs, C).gDisc;
}
const slugsOf = (rs: { slug: string }[]) => rs.map(r => r.slug);

// ── per-question: compute every arm's top-C slugs, then the three policies ───
type Arm = "key_pp" | "vector" | "hyb" | "g1" | "g2";
interface Row {
  q: string; domain: string; type: Type;
  baseline: string[]; router: string[]; strong_g: string[];
  arm: Record<Arm, number>;       // grounding of each candidate arm (for transparency)
}
const rows: Row[] = [];
let gWhich: "g1" | "g2" = "g1";    // decided after the loop by mean grounding

const perArm = { key_pp: [] as number[], vector: [] as number[], hyb: [] as number[],
                 g1: [] as number[], g2: [] as number[] };
const raw: { q: string; domain: string; type: Type; slugs: Record<Arm, string[]>; ents: string[] }[] = [];

for (const g of golden) {
  const ents = g.expected_entities;
  const keyPP = slugsOf(await engine.searchKeyword(preprocessOR(g.q), { limit: K }));
  const vec = slugsOf(await engine.searchVector(await embed(g.q), { limit: K }));
  const hyb = slugsOf(await hybridSearch(engine, g.q, { limit: K, expansion: false, rrfK: 60 }));
  const g1 = rrf(keyPP, vec).slice(0, K);
  const g2 = slugsOf(await hybridSearch(engine, preprocessOR(g.q), { limit: K, expansion: false, rrfK: 60 }));
  const slugs: Record<Arm, string[]> = { key_pp: keyPP, vector: vec, hyb, g1, g2 };
  perArm.key_pp.push(await ground(keyPP, ents));
  perArm.vector.push(await ground(vec, ents));
  perArm.hyb.push(await ground(hyb, ents));
  perArm.g1.push(await ground(g1, ents));
  perArm.g2.push(await ground(g2, ents));
  raw.push({ q: g.q, domain: g.domain, type: classifyType(g.q), slugs, ents });
}

const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
gWhich = mean(perArm.g1) >= mean(perArm.g2) ? "g1" : "g2";  // strengthened-global = better variant

// route each question by its detected type → the arm the principle assigns
const armForType: Record<Type, Arm> = { kw: "key_pp", vec: "vector", mixed: "hyb" };
for (let i = 0; i < raw.length; i++) {
  const r = raw[i];
  const routerArm = armForType[r.type];
  rows.push({
    q: r.q, domain: r.domain, type: r.type,
    baseline: r.slugs.hyb, router: r.slugs[routerArm], strong_g: r.slugs[gWhich],
    arm: { key_pp: perArm.key_pp[i], vector: perArm.vector[i], hyb: perArm.hyb[i],
           g1: perArm.g1[i], g2: perArm.g2[i] },
  });
}

// ── scoring helpers ──────────────────────────────────────────────────────────
const score = {
  baseline: rows.map((_, i) => perArm.hyb[i]),
  router:   rows.map((r, i) => perArm[armForType[r.type]][i]),
  strong_g: rows.map((_, i) => perArm[gWhich][i]),
};
const classes: Type[] = ["kw", "vec", "mixed"];
const meanFor = (xs: number[], cls?: Type) => mean(xs.filter((_, i) => !cls || rows[i].type === cls));

// ── report ───────────────────────────────────────────────────────────────────
const pad = (s: string, n: number) => s.padEnd(n);
const f = (x: number) => x.toFixed(3);
console.log(`route_principle_ab: ${rows.length} questions · K=${K} C=${C} · strengthened-global = ${gWhich}\n`);

// classifier confusion vs gold domain
const correct = rows.filter(r => r.type === r.domain).length;
console.log(`classifier vs gold domain: ${correct}/${rows.length} correct`);
console.log("  per-q:  " + rows.map(r => (r.type === r.domain ? r.type : `${r.domain}->${r.type}`)).join(" "));
console.log();

console.log(pad("policy", 12) + pad("grnd@C", 9) + classes.map(c => pad(`g@C:${c}`, 9)).join(""));
console.log("-".repeat(12 + 9 + classes.length * 9));
for (const [name, xs] of Object.entries(score)) {
  console.log(pad(name, 12) + pad(f(meanFor(xs)), 9) + classes.map(c => pad(f(meanFor(xs, c)), 9)).join(""));
}
const base = mean(score.baseline);
console.log(`\nΔ vs baseline(hyb ${f(base)}):  router ${f(mean(score.router) - base)}  ·  strong_g(${gWhich}) ${f(mean(score.strong_g) - base)}`);

// how often each honor-the-principle arm strictly beats baseline (where the principle pays)
const rWins = rows.filter((_, i) => score.router[i] > score.baseline[i] + 1e-9).length;
const rLoses = rows.filter((_, i) => score.router[i] < score.baseline[i] - 1e-9).length;
console.log(`router vs baseline per-question:  +${rWins} better  ·  -${rLoses} worse  ·  ${rows.length - rWins - rLoses} tie`);

// show the questions where router differs from baseline — the evidence behind the +N/-N count
console.log("\nwhere router ≠ baseline (the only rows that move the average):");
rows.forEach((r, i) => {
  const d = score.router[i] - score.baseline[i];
  if (Math.abs(d) <= 1e-9) return;
  const arm = armForType[r.type];
  console.log(`  ${d > 0 ? "WIN " : "LOSS"}  ${r.type}  baseline(hyb) ${f(score.baseline[i])} → router(${arm}) ${f(score.router[i])}   "${r.q.slice(0, 50)}"`);
});

// ── dump slugs for the answer-quality A/B ────────────────────────────────────
const dump = rows.map(r => ({
  q: r.q, domain: r.domain, type: r.type,
  expected_entities: golden.find(g => g.q === r.q)!.expected_entities,
  baseline_slugs: r.baseline, router_slugs: r.router, strong_g_slugs: r.strong_g,
  strong_g_variant: gWhich,
}));
mkdirSync(dirname(SLUG_DUMP), { recursive: true });
writeFileSync(SLUG_DUMP, JSON.stringify(dump, null, 2) + "\n");
console.log(`\nwrote per-arm slugs → ${SLUG_DUMP}`);

await engine.disconnect?.();
process.exit(0);
```

**Walkthrough:**
- **The three-contestant design is the whole point.** Routing can be rejected two ways - either via a head-to-head where the router loses to the baseline, or via a head-to-head where a classifier-free alternative (`strong_g`) matches or beats it. This script forces both comparisons simultaneously so the verdict can't be gamed by cherry-picking the weaker foil. `strong_g` is elected post-loop (`gWhich = better of g1 vs g2`) so it is always presented at its best.
- **One loop, all five arms, deferred routing.** All five arm arrays (`key_pp`, `vector`, `hyb`, `g1`, `g2`) are filled in the single golden-question loop, and the policy assignment (`armForType[r.type]`) runs in a second pass after `gWhich` is known. This avoids a double-pass over the database while keeping the `gWhich` election logically after all grounding data is collected.
- **`rrf` is local, not imported.** The two-list RRF used for `g1` is a 10-line utility defined in this file. It is deliberately NOT shared with `grounding.ts` or `query_routing.ts` - it is a one-off experiment variant, and premature promotion to shared infra would blur the boundary between lab scaffolding (this file) and production plumbing (`query_routing.ts`, `grounding.ts`).
- **The slug dump feeds `answer_principle_ab.py`** - that downstream script reads `principle_slugs.json` and calls the LLM judge, so retrieval and answer evaluation share exactly the same context sets with no re-retrieval. This is the same data-dependency chain documented in the running-reference table.
- **`classifyType` is imported from `query_routing.ts`**, the same module `query_policy.ts` ships in production. Any classifier drift between the A/B and production would invalidate the measured +0.039/+0.042 claim - sharing the import guarantees they are identical.

**Result (`GOLDEN_EVAL=data/golden_balanced.json bun src/route_principle_ab.ts`, balanced 24-Q set, K=5 C=3):**

| policy | grnd@C | g@C:kw | g@C:vec | g@C:mixed | Δ vs baseline |
|---|---|---|---|---|---|
| baseline (`hyb`) | 0.823 | 0.925 | 0.745 | 0.763 | — |
| **router** | **0.862** | **1.000** | 0.763 | 0.763 | **+0.039** |
| strengthened-global (`g1`) | 0.837 | 1.000 | 0.745 | 0.658 | +0.014 |

classifier 24/24 correct; router wins +2 / loses 0 / ties 22 questions.

#### Entity-aware assembly — one-hop graph expansion (2026-06-07)

Routing fixes *which arm* retrieves; it can't fix a **2-hop question** where the answer needs **two** entity pages in the same `C`-chunk budget and retrieval ranks the second one at `C+1`. We saw this in the answer A/B: `which venture firm is the angel investor associated with` retrieved both `ridgeline-capital` (rank 3, in budget) and `people/dev-patel` (rank 4, **out**) — the generator saw the firm but not the investor. GBrain is a knowledge graph, so there's a cheap fix the chapter's whole premise points at: `dev-patel` is a **1-hop neighbor** of the in-budget `ridgeline-capital` (`invested_in` / `founded` edges). Pull the neighbor's page into the context — one edge traversal, no NER. Assembly becomes *entity-aware*: it guarantees the graph-completion of an in-budget entity rather than blindly taking the top-`C` by score.

The rule is deliberately high-precision: pull a demoted page **only** when it is *both* graph-connected to an in-budget page *and* itself retrieved-but-demoted (in the top-`K` pool, ranked past `C`). That keeps single-hop queries at exactly `C` and spends extra budget only along a real edge to an already-relevant page.

**When to use:** Reach for `assembly.ts` when your workload contains genuine multi-hop questions - ones that need two entity pages co-present in the reader budget - AND those neighbor pages are small (entity pages, not 10-K sections). Skip it when failures are distractor-dominated (wrong pages outranking right ones) or when a larger `C` or a reranker can close the gap more cheaply.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  Q["query"] --> ARM["routed arm"]
  ARM --> RANK["top-K ranked"]
  RANK --> TOPC["top-C<br/>reader budget"]
  RANK --> TAIL["demoted tail<br/>ranks C+1..K"]
  TOPC --> NBR["1-hop neighbors<br/>getLinks +<br/>getBacklinks"]
  NBR --> M{"demoted page<br/>is a neighbor?"}
  TAIL --> M
  M -->|"yes · up to maxPull"| PULL["pull page<br/>into context"]
  M -->|"no"| SKIP["keep top-C"]
  TOPC --> CTX["assembled<br/>context"]
  PULL --> CTX
  CTX --> GEN["generator"]
```

**Code (full source `src/assembly.ts`):**

```typescript
/**
 * assembly.ts — entity-aware context assembly via 1-hop GRAPH EXPANSION.
 *
 * The gap it closes (measured): a 2-hop question needs TWO entity pages in the same C-chunk
 * reader budget. Rank-only assembly (`ranked.slice(0, C)`) can drop the second one when retrieval
 * ranks it at C+1 — e.g. "which venture firm is the angel investor associated with" retrieved both
 * `ridgeline-capital` (#3, in budget) and `people/dev-patel` (#4, OUT), so the generator saw the
 * firm but not the investor and failed (route_principle_ab / answer_principle_ab).
 *
 * GBrain is a knowledge graph, so the fix is one edge traversal: `dev-patel` is a 1-hop neighbor
 * of the in-budget `ridgeline-capital` (`invested_in` / `founded` edges, both directions). Pull it
 * into the context. We pull a neighbor only when it is (a) graph-connected to an in-budget page AND
 * (b) itself retrieved-but-demoted (in the top-K pool, ranked past C) — high precision: the page was
 * relevant enough to retrieve, and the graph says it completes an in-budget entity. `maxPull` caps
 * the spend so single-hop queries stay at C.
 */

interface GraphEngine {
  getLinks(slug: string, opts?: { sourceId?: string }): Promise<{ to_slug: string }[]>;
  getBacklinks(slug: string, opts?: { sourceId?: string }): Promise<{ from_slug: string }[]>;
}

/** 1-hop neighbors of `slug`: union of outgoing (`getLinks.to`) and incoming (`getBacklinks.from`). */
export async function neighborSlugs(engine: GraphEngine, slug: string): Promise<string[]> {
  const [out, back] = await Promise.all([engine.getLinks(slug), engine.getBacklinks(slug)]);
  const s = new Set<string>();
  for (const l of out) s.add(l.to_slug);
  for (const l of back) s.add(l.from_slug);
  s.delete(slug);
  return [...s];
}

export interface ExpandOpts {
  C: number;                 // reader budget (injected-chunk count)
  maxPull?: number;          // max neighbors to pull beyond C (default 2)
  poolOnly?: boolean;        // pull only retrieved-but-demoted neighbors (default true, high precision)
}

export interface ExpandResult {
  slugs: string[];           // assembled context: top-C + pulled neighbors (length C..C+maxPull)
  pulled: string[];          // the graph-pulled neighbor slugs (empty = no expansion happened)
}

/**
 * Graph-expanded assembly. Takes the full ranked candidate list (top-K from one search arm),
 * keeps the top-C, then appends up to `maxPull` 1-hop neighbors of the in-budget pages.
 *
 * poolOnly=true  → only neighbors that were themselves retrieved (in `ranked`) but demoted past C.
 * poolOnly=false → any 1-hop neighbor of an in-budget page (pure graph reach; lower precision).
 */
export async function graphExpand(
  engine: GraphEngine,
  ranked: string[],
  { C, maxPull = 2, poolOnly = true }: ExpandOpts,
): Promise<ExpandResult> {
  const topC = ranked.slice(0, C);
  const inBudget = new Set(topC);

  // 1-hop neighbor set of the in-budget pages
  const nbr = new Set<string>();
  for (const ns of await Promise.all(topC.map(p => neighborSlugs(engine, p)))) {
    for (const n of ns) nbr.add(n);
  }

  // candidates to pull, in priority order
  const candidates = poolOnly
    ? ranked.slice(C).filter(s => nbr.has(s))         // retrieved-but-demoted AND graph-connected
    : [...nbr].filter(s => !inBudget.has(s));         // any graph neighbor (incl. never-retrieved)

  const pulled: string[] = [];
  for (const s of candidates) {
    if (pulled.length >= maxPull) break;
    if (!inBudget.has(s) && !pulled.includes(s)) pulled.push(s);
  }
  return { slugs: [...topC, ...pulled], pulled };
}
```

**Walkthrough:**
- **`neighborSlugs` is the one-hop traversal** — union of `getLinks` (outgoing edges, `to_slug`) and `getBacklinks` (incoming, `from_slug`). GBrain's edges are typed and bidirectional (`ridgeline-capital —invested_in→ dev-patel`, `dev-patel —founded→ ridgeline-capital`), so the investor↔firm link is already in the graph — no entity extraction, no second model.
- **The pull condition is `pool ∩ neighbors`, not just neighbors.** `poolOnly` keeps only demoted pages that were *retrieved* (so already judged relevant by the arm) **and** graph-connected to something in budget. Pulling arbitrary neighbors (`poolOnly=false`) would drag in every linked page — high recall, low precision. The intersection is the entity-aware sweet spot.
- **`maxPull` bounds the budget blow-up.** Single-hop queries have no demoted neighbor, so `pulled` is empty and the context stays exactly `C`. Only genuine multi-hop questions pay the +1–2 pages — the cost lands where the benefit is.

**Result (balanced 24-Q, on top of the router; `src/assembly_graph_ab.ts` + `src/assembly_answer_ab.py`):**

| metric | plain top-C | graph-expanded | note |
|---|---|---|---|
| lexical entity coverage | 0.986 | 0.986 | **saturated** — related pages cross-name each other, so coverage is blind to this |
| answer pass (Opus 4.5), all 24 | 0.792 | **0.833** | **Δ +0.042** — 1 fixed, 0 broke |
| answer pass, the **7** where it fired | 0.714 | **0.857** | **Δ +0.143** |
| avg context size | 3.00 | 3.46 | grows only on the 7 fired questions |

The single fix is `What does Quanta Labs work on?` (F→P): the deal page `deals/quanta-seed` was retrieved-but-demoted and one edge from the in-budget Quanta page; pulling it gave the generator the answer. The motivating `which venture firm` question **stays F** — that one is *distractor-dominated* (two `northstar` pages outrank `ridgeline`), and additive expansion adds the right page without removing the wrong ones. Graph expansion fixes *missing-neighbor* 2-hop failures, not *distractor* failures.

`★ Insight ─────────────────────────────────────`
- **Coverage said useless, the answer judge said +1.** Lexical coverage was already 0.986 because `ridgeline`'s page text *names* "Dev Patel" — the string is in budget even when the page isn't. Only judging the answer exposed that the generator needs the *page*, not the mention. Same lesson as the routing A/B: grounding metrics under-measure; pin a strong generator and judge.
- **Two failure modes, one fix each.** Missing-neighbor (Quanta's deal page demoted) → graph expansion. Distractor-dominated (Northstar outranks Ridgeline) → rerank / dedup, which *removes* a page rather than adding one. Recognizing which mode a failure is in tells you which lever to pull.
- **The graph was free.** GBrain already wired the edges at ingest (`invested_in`, `founded`); assembly just walks one hop. That's the "self-wiring memory" thesis paying off downstream — the structure built once is reused at read time with no extra model.
`─────────────────────────────────────────────────`

---

`assembly_graph_ab.ts` is the **A/B harness** that measured whether 1-hop graph expansion (implemented in `assembly.ts`) actually moves entity coverage and answer quality. It routes each golden question through its typed arm, assembles two contexts - plain top-C and graph-expanded - scores both with the `coverage` metric, and dumps per-question slug lists so the downstream Python answer A/B (`assembly_answer_ab.py`) can reuse the retrieval without re-hitting the DB.

**When to use:** reach for `assembly_graph_ab.ts` when you want to empirically measure the coverage and answer-quality impact of graph expansion on a new golden set or a new corpus, or when you need the `results/assembly_slugs.json` dump as input to `assembly_answer_ab.py` - not when you want to understand the expansion logic itself (that lives in `assembly.ts`).

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  ENV["env: GOLDEN_EVAL<br/>POLICY_K · POLICY_C<br/>MAX_PULL"] --> BOOT["load config +<br/>create engine"]
  BOOT --> GOLDEN["read golden_balanced.json<br/>GoldenQ list"]
  GOLDEN --> LOOP["for each question"]
  LOOP --> ROUTE["rankedFor(q)<br/>classifyType → arm<br/>keyword / vector / hybrid"]
  ROUTE --> PLAIN["plain = ranked.slice(0,C)"]
  ROUTE --> EXPAND["graphExpand(engine, ranked,<br/>C, maxPull)<br/>→ {slugs, pulled}"]
  PLAIN --> COVP["setCoverage(plain, ents)<br/>= coverage(text, ents)"]
  EXPAND --> COVE["setCoverage(expanded, ents)"]
  COVP --> ROW["Row: q, type, plain_slugs,<br/>expanded_slugs, covPlain,<br/>covExp, pulled, size"]
  COVE --> ROW
  ROW --> DUMP["write assembly_slugs.json"]
  DUMP --> REPORT["console report:<br/>fired / improved / hurt<br/>avg context size"]
```
*`assembly_graph_ab.ts` data flow: routes each golden question, assembles plain and expanded contexts in parallel, scores coverage, dumps slugs, prints the A/B report.*

**Code `src/assembly_graph_ab.ts`:**

```typescript
/**
 * assembly_graph_ab.ts — does GRAPH-EXPANDED assembly get more answer entities into the C-chunk
 * budget than plain top-C? Measured on the balanced 24-Q set.
 *
 * For each question: route it to its type's arm (same classifier as production), take that arm's
 * top-K ranked candidates, then assemble two contexts —
 *   plain     = ranked.slice(0, C)                 (rank-only, the current behaviour)
 *   expanded  = graphExpand(ranked, C, maxPull)    (top-C + 1-hop retrieved-but-demoted neighbors)
 * — and score entity COVERAGE of each (fraction of the question's expected_entities present in the
 * assembled pages' text). Reports where expansion pulls a neighbor and whether coverage rises,
 * plus the context-size cost.
 *
 * Run: GOLDEN_EVAL=data/golden_balanced.json bun src/assembly_graph_ab.ts
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

import { graphExpand } from "./assembly.ts";
import { coverage } from "./grounding.ts";
import { classifyType, preprocessOR, TYPE_TO_STRATEGY } from "./query_routing.ts";

const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;
const GOLDEN = process.env.GOLDEN_EVAL ?? `${import.meta.dir}/../data/golden_balanced.json`;
const K = Number(process.env.POLICY_K ?? "5");
const C = Number(process.env.POLICY_C ?? "3");
const MAX_PULL = Number(process.env.MAX_PULL ?? "2");

interface GoldenQ { q: string; expected_entities: string[]; domain: string }
const golden: GoldenQ[] = JSON.parse(readFileSync(GOLDEN, "utf-8")).questions;

const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway, reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { embed } = await import(`${GB}/core/embedding.ts`);
const { hybridSearch } = await import(`${GB}/core/search/hybrid.ts`);

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
await reconfigureGatewayWithEngine(engine);

const textCache = new Map<string, string>();
async function sectionText(slug: string): Promise<string> {
  if (textCache.has(slug)) return textCache.get(slug)!;
  const p = await engine.getPage(slug);
  const t = p ? `${p.title}\n${p.compiled_truth}\n${p.timeline}`.toLowerCase() : "";
  textCache.set(slug, t);
  return t;
}
async function setCoverage(slugs: string[], ents: string[]): Promise<number> {
  const text = (await Promise.all(slugs.map(sectionText))).join("\n");
  return coverage(text, ents);
}
const slugsOf = (rs: { slug: string }[]) => rs.map(r => r.slug);

// route a query to its type's arm and return that arm's ranked candidates (top-K)
async function rankedFor(q: string): Promise<string[]> {
  const strat = TYPE_TO_STRATEGY[classifyType(q)];
  if (strat === "keyword") return slugsOf(await engine.searchKeyword(preprocessOR(q), { limit: K }));
  if (strat === "vector") return slugsOf(await engine.searchVector(await embed(q), { limit: K }));
  return slugsOf(await hybridSearch(engine, q, { limit: K, expansion: false, rrfK: 60 }));
}

const SLUG_DUMP = `${import.meta.dir}/../results/assembly_slugs.json`;
interface Row {
  q: string; type: string; expected_entities: string[];
  plain_slugs: string[]; expanded_slugs: string[];
  covPlain: number; covExp: number; pulled: string[]; size: number;
}
const rows: Row[] = [];
for (const g of golden) {
  const ranked = await rankedFor(g.q);
  const plain = ranked.slice(0, C);
  const { slugs: expanded, pulled } = await graphExpand(engine, ranked, { C, maxPull: MAX_PULL });
  rows.push({
    q: g.q, type: classifyType(g.q), expected_entities: g.expected_entities,
    plain_slugs: plain, expanded_slugs: expanded,
    covPlain: await setCoverage(plain, g.expected_entities),
    covExp: await setCoverage(expanded, g.expected_entities),
    pulled, size: expanded.length,
  });
}
mkdirSync(dirname(SLUG_DUMP), { recursive: true });
writeFileSync(SLUG_DUMP, JSON.stringify(rows.map(r => ({
  q: r.q, type: r.type, expected_entities: r.expected_entities,
  plain_slugs: r.plain_slugs, expanded_slugs: r.expanded_slugs, pulled: r.pulled,
})), null, 2) + "\n");

// ── report ───────────────────────────────────────────────────────────────────
const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const f = (x: number) => x.toFixed(3);
console.log(`assembly_graph_ab: ${rows.length} questions · K=${K} C=${C} maxPull=${MAX_PULL}\n`);

const expandedRows = rows.filter(r => r.pulled.length > 0);
console.log(`graph expansion fired on ${expandedRows.length}/${rows.length} questions:`);
for (const r of expandedRows) {
  const tag = r.covExp > r.covPlain + 1e-9 ? "↑ COVERAGE" : r.covExp < r.covPlain - 1e-9 ? "↓" : "= (already covered)";
  console.log(`  ${tag}  cov ${f(r.covPlain)}→${f(r.covExp)}  +${r.pulled.length}p (size ${r.size})  pulled[${r.pulled.join(", ")}]  "${r.q.slice(0, 44)}"`);
}

const improved = rows.filter(r => r.covExp > r.covPlain + 1e-9).length;
const hurt = rows.filter(r => r.covExp < r.covPlain - 1e-9).length;
console.log(`\nentity coverage:  plain ${f(mean(rows.map(r => r.covPlain)))}  →  graph-expanded ${f(mean(rows.map(r => r.covExp)))}`);
console.log(`questions improved: ${improved}  ·  hurt: ${hurt}  ·  unchanged: ${rows.length - improved - hurt}`);
console.log(`avg context size:  plain ${C}  →  expanded ${f(mean(rows.map(r => r.size)))}  (pulls only where an edge says a retrieved page completes an in-budget entity)`);

await engine.disconnect?.();
process.exit(0);
```

**Walkthrough:**
- **GBrain is booted with dynamic imports from `GBRAIN_SRC`.** The engine, gateway, and embedding imports are deferred so the script can run against a different GBrain source tree via env - the same pattern `policy_eval.ts` and `route_eval.ts` use. `connectWithRetry` with `noRetry: true` fails fast rather than hanging if Postgres is down.
- **`rankedFor` reuses the production classifier exactly.** `classifyType` + `TYPE_TO_STRATEGY` from `query_routing.ts` is the same code path the actuator (`query_policy.ts` with `QUERY_ROUTER=on`) uses. The A/B therefore measures expansion *on top of the same routing logic that ships* - not a synthetic baseline.
- **`setCoverage` is the only scoring primitive.** It fetches each slug's compiled text (cached in `textCache` to avoid re-fetching the same page across the plain/expanded pair), concatenates, and calls the pure `coverage` function from `grounding.ts`. Caching is load-bearing: the plain and expanded slug sets overlap heavily (top-C is shared), so without the cache every question would re-fetch C pages twice.
- **The slug dump is the handoff to `assembly_answer_ab.py`.** The JSON written to `results/assembly_slugs.json` contains only `plain_slugs`, `expanded_slugs`, and `pulled` - no page bodies. The Python answer script reads those slugs, fetches bodies from Postgres via `gbrain get`, and runs the generator. Keeping the dump slug-only means the TypeScript A/B (cheap, deterministic) and the Python answer A/B (expensive, needs a chat endpoint) are decoupled and can be re-run independently.
- **The report prints only the questions where expansion fired**, not all 24. That keeps the output focused on the cases that matter - if `pulled` is empty, expansion was a no-op and the row is uninteresting. The `↑ COVERAGE` / `↓` / `= (already covered)` tags let you scan the firing questions at a glance.

##### Decision — measured, NOT shipped to production (2026-06-07)

Graph expansion *works*, and it is left in the repo as a tested, reproducible module (`src/assembly.ts` + the two A/B probes) — but it is **deliberately not wired into the production actuator** (`query_policy.ts`). The benefit does not clear the cost-and-complexity bar. The full reasoning, because "we built it and chose not to ship it" is itself the lesson:

1. **The benefit is marginal and fragile.** It fixed exactly **one** of 24 questions (`Quanta Labs`, +0.042 overall). That is the *same magnitude as the judge's run-to-run variance* (~1 question at temp 0 on Opus) — so the gain is barely separable from noise. A continuous metric can't even see it: lexical entity coverage was 0.986 → 0.986, because related pages cross-name each other. A win that only one expensive measurement can detect, and only by one question, is not a robust production signal.

2. **It fixes only one of the two failure modes.** Graph expansion is additive — it *adds* the missing neighbor page. That fixes **missing-neighbor** 2-hop failures (Quanta's deal page was retrieved-but-demoted, one edge away). It does **nothing** for **distractor-dominated** failures: the motivating `which venture firm` question stayed `F`, because two `northstar` pages outrank `ridgeline` and adding `dev-patel` doesn't remove the distractors. The more common and more damaging failure mode needs *rerank / dedup* (which **removes** a wrong page, net-zero token cost), not expansion. So the feature addresses the cheaper half of the problem.

3. **The runtime cost is small here but *unbounded in general*.** The DB side is free (6 indexed `getLinks`/`getBacklinks` reads, ~ms, no LLM). The real cost is **generator input tokens**: every fired query injects the pulled neighbor's *full page body*. On this corpus the pulled pages were tiny entity pages (+0.46 pages ≈ **+0.1%** tokens — `775K` vs `773K` over the answer A/B). But that is a property of *this* workload, not the mechanism: pull a neighbor that happens to be a **30K-token 10-K section** and every fired query pays 30K extra input tokens. The benefit is a flat ~1 question; the cost is **proportional to neighbor page size** — they don't scale together, and on a document-heavy corpus the trade goes sharply negative. (For scale: the answer A/B itself runs ~**1.5M input tokens** because full 10-K bodies are injected uncapped — a stark reminder that the real budget is *tokens*, not *chunks*. Cap page bodies with `MAX_BODY_CHARS` before any such eval.)

4. **It adds a production stage, a switch, and a calibration surface** (`maxPull`, `poolOnly`, the pull condition) — the same complexity tax that gated per-query routing on single-type corpora. A marginal, fragile, one-failure-mode benefit does not earn that surface.

**Verdict:** keep `assembly.ts` as a documented experiment; do not run it in the live path. **Revisit only if** a real workload is (a) heavy on *missing-neighbor* multi-hop questions AND (b) the neighbor pages are small (entity pages, not document sections) AND (c) a cheaper fix (rerank-to-swap-a-distractor, or a slightly larger `C`) has been ruled out first. On this corpus none of those hold, so the honest engineering call is: **measured, shelved.** This is the chapter's "what NOT to build" discipline applied to our own feature — the experiment that earns its place by telling us *not* to ship.

##### Answer-quality A/B for graph expansion — `src/assembly_answer_ab.py`

`assembly_graph_ab.ts` measured *coverage* and found it unchanged (0.986 → 0.986) — because related entity pages already name each other, so the string is in budget even when the page is not. Coverage cannot see whether having the neighbor's full page changes the generated answer. `assembly_answer_ab.py` closes that gap: it replays the same plain-vs-expanded slug sets (read from `results/assembly_slugs.json`) through a strong generator (Opus), LLM-judges each answer against `expected_entities`, and reports pass rates overall and for the 7 questions where expansion actually fired.

**When to use:** reach for `assembly_answer_ab.py` when you want to know whether 1-hop graph expansion changes the *answer*, not just the *coverage score* - specifically after `assembly_graph_ab.ts` has dumped its slug file and you want a final yes/no on whether the expanded context makes the generator more correct.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  SLUGS[(assembly_slugs.json<br/>plain_slugs · expanded_slugs<br/>pulled · expected_entities)] --> LOOP[for each question]
  LOOP --> AP[_answer<br/>plain_slugs → context<br/>→ generator · Opus]
  LOOP --> AE[_answer<br/>expanded_slugs → context<br/>→ generator · Opus]
  AP --> JP[_judge<br/>PASS / FAIL<br/>vs expected_entities]
  AE --> JE[_judge<br/>PASS / FAIL<br/>vs expected_entities]
  JP --> ACC[accumulate pp · pe<br/>fired_pp · fired_pe]
  JE --> ACC
  ACC --> RPT["report: all-N pass rates<br/>+ fired-only pass rates<br/>Δ plain → expanded"]
```
*`assembly_answer_ab.py` flow. Both arms share the same generator and judge so the only variable is the slug set (plain top-C vs expanded top-C + pulled neighbor). The fired subset isolates the signal to questions where expansion actually changed the context.*

**Code (`src/assembly_answer_ab.py`):**

```python
"""assembly_answer_ab.py — does GRAPH-EXPANDED assembly produce better ANSWERS than plain top-C?

assembly_graph_ab.ts showed graph expansion fires on 7/24 questions but lexical entity COVERAGE
doesn't move — because a related entity's page already names the other entity (ridgeline's page
says "Dev Patel"), so the string is in budget even when the page isn't. Coverage is blind to that;
the real question is whether having the neighbor's full PAGE (and the distractors it sits beside)
changes the generated answer. So we judge the answers, pinned to a strong generator (Opus).

Two arms per question (from results/assembly_slugs.json):
  plain     — top-C context
  expanded  — top-C + 1-hop graph-pulled neighbors
Judge entity coverage of each answer. Report pass rates, focused on the questions where expansion
actually pulled a neighbor.

Run: CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/assembly_answer_ab.py
"""
from __future__ import annotations

import json
import os
import pathlib
import time

from openai import APIConnectionError, APIError

from ground_truth_ab import _MEMZERO_TMPL, _ask, _client, gbrain_get

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SLUGS = _ROOT / "results" / "assembly_slugs.json"
_MIN_BODY = 80

_JUDGE_TMPL = (
    "You are grading whether a candidate answer correctly identifies the required facts. "
    "Reply with EXACTLY one word: PASS or FAIL.\n\n"
    "The answer PASSES only if it correctly names/identifies ALL of these (synonyms / full entity "
    "for an abbreviation are fine):\n{entities}\n\nCANDIDATE ANSWER:\n{answer}\n\nVerdict (PASS or FAIL):"
)


class LLMUnavailable(RuntimeError):
    pass


def _resilient(fn, *args, retries: int = 4, backoff: float = 2.0):
    for attempt in range(retries):
        try:
            return fn(*args)
        except (APIConnectionError, APIError) as exc:
            if attempt == retries - 1:
                raise LLMUnavailable(str(exc)) from exc
            time.sleep(backoff * (attempt + 1))
    raise LLMUnavailable("unreachable")


def _context(slugs: list[str]) -> str:
    bodies = [gbrain_get(s) for s in slugs]
    short = [(s, len(b.strip())) for s, b in zip(slugs, bodies) if len(b.strip()) < _MIN_BODY]
    if short:
        raise RuntimeError(f"body too short {short}")
    return "\n\n".join(bodies)


def _answer(client, slugs: list[str], q: str) -> str:
    msg = [{"role": "user", "content": _MEMZERO_TMPL.format(ctx=_context(slugs), q=q)}]
    return _resilient(_ask, client, msg)[0]


def _judge(client, answer: str, entities: list[str]) -> bool:
    msg = [{"role": "user", "content": _JUDGE_TMPL.format(entities="; ".join(entities), answer=answer)}]
    return _resilient(_ask, client, msg)[0].strip().upper().startswith("PASS")


def main() -> None:
    rows = json.loads(_SLUGS.read_text())
    client = _client()
    print(f"generator/judge: {os.getenv('CHAT_MODEL', '(default)')} · {len(rows)} questions\n")

    pp = pe = 0
    fired_pp = fired_pe = fired_n = 0
    for r in rows:
        ents = r["expected_entities"]
        fired = len(r["pulled"]) > 0
        try:
            ap = _judge(client, _answer(client, r["plain_slugs"], r["q"]), ents)
            ae = _judge(client, _answer(client, r["expanded_slugs"], r["q"]), ents)
        except LLMUnavailable as exc:
            print(f"  [skip] {r['q'][:46]} ({exc})")
            continue
        pp += ap; pe += ae
        if fired:
            fired_n += 1; fired_pp += ap; fired_pe += ae
            tag = "FIXED " if (ae and not ap) else ("BROKE " if (ap and not ae) else "same  ")
            print(f"  [{tag}] plain={'P' if ap else 'F'} expanded={'P' if ae else 'F'}  +{len(r['pulled'])}p  \"{r['q'][:44]}\"")

    n = len(rows)
    print(f"\nall {n} questions:        plain {pp / n:.3f}  →  graph-expanded {pe / n:.3f}  (Δ {(pe - pp) / n:+.3f})")
    if fired_n:
        print(f"the {fired_n} where expansion fired: plain {fired_pp / fired_n:.3f}  →  expanded {fired_pe / fired_n:.3f}  (Δ {(fired_pe - fired_pp) / fired_n:+.3f})")


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **Design principle - judge answers, not strings.** `assembly_graph_ab.ts` already measured lexical coverage and found it flat. This script exists because the *answer* is the real objective and coverage is its surrogate. Running a separate answer-quality A/B with a pinned strong generator (Opus via `CHAT_MODEL`) isolates the retrieval change from generation noise - the only thing that differs between the two arms is the slug set.
- **`assembly_slugs.json` is the load-bearing input.** `assembly_graph_ab.ts` writes this file with `plain_slugs`, `expanded_slugs`, `pulled`, `expected_entities`, and `q` for every golden question. `assembly_answer_ab.py` consumes it purely - it never calls a retrieval arm itself. That separation keeps the answer A/B cheap and reproducible: re-run it any number of times without touching Postgres or the embedding service.
- **`_judge_tmpl` is entity-coverage, not `pass_criteria`.** Unlike `verify_arch.py` or `answer_route_ab.py`, this script checks `expected_entities` (a list of required proper nouns) rather than a prose rubric. The entity list is narrower and binary - it is the right judge for the expansion experiment because expansion targets missing *entity pages*, so the verdict should hinge on whether those entities appear in the answer.
- **`_resilient` wraps every LLM call.** Four retries with linear backoff guard against VibeProxy transient failures. A `LLMUnavailable` skips the question with a `[skip]` line rather than crashing - important because the full A/B over 24 questions with 2 arms x 2 calls each runs ~96 LLM round-trips; one flaky call should not abort the run.
- **`_MIN_BODY = 80` is a fast sanity guard.** `gbrain_get` can return an empty or stub body if a slug is stale. Raising early (`body too short`) prevents the generator from answering from thin context and recording a misleading FAIL - it's cheaper to abort one question than to silently corrupt the pass-rate.
- **`fired` partitioning surfaces the signal.** Overall pass rates dilute the effect across the 17 questions where expansion changed nothing. The `fired_*` counters isolate the 7 questions where `pulled` is non-empty - the only ones where the slug sets differ. That sub-rate (`0.714 → 0.857, Δ +0.143`) is the direct measure of expansion's effectiveness on its own firing condition.

**Result (balanced 24-Q, Opus 4.5 generator + judge, `results/assembly_slugs.json`):** all-24 pass rate plain 0.792 → expanded **0.833** (Δ +0.042). The 7 fired questions: plain 0.714 → expanded **0.857** (Δ +0.143). One question fixed (`Quanta Labs work on?`, F→P); zero broke. Distractor-dominated failure (`which venture firm`) stayed F — expansion added the right page but did not remove the wrong distractors.

#### Block C — `query_policy.ts`: the actuator

The actuator closes the auto-eval loop by reading `results/search_policy.json` and routing each query through the engine arm that `auto_eval.ts` measured as best for this corpus. It is the right script to reach for when you want to run a query and have the corpus-tuned strategy applied automatically - not when you want to measure strategies (use `auto_eval.ts`) or when you need the raw GBrain CLI for one-off exploration.

**When to use:** Reach for `query_policy.ts` (instead of bare `gbrain query`) whenever the corpus has been evaluated and you want retrieval steered by the measured-best strategy - global policy by default, per-query routing via `QUERY_ROUTER=on` only when traffic is mixed-type and the classify cost is justified. Use `auto_eval.ts` when you want to re-measure; use `auto_eval.ts` + `query_policy.ts` together as the full closed loop.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  Q[query text] --> POL[(search_policy.json<br/>read winning arm + rrf_k)]
  POL -->|file missing| FB[fallback<br/>hybrid · GBrain default]
  POL --> SW{QUERY_ROUTER?}
  SW -->|off · default| GA[global arm<br/>keyword / vector / hybrid]
  SW -->|on · accuracy switch| RT[query_routing.ts<br/>classifyType + preprocessOR]
  RT --> PA[per-query arm<br/>kw to keyword · vec to vector<br/>mixed to hybrid]
  GA --> ENG[GBrain engine path]
  PA --> ENG
  FB --> ENG
  ENG --> R[ranked slugs<br/>+ resolved-policy line]
```
*`query_policy.ts` actuator. It reads the arm the selector chose and runs the query through that engine path - never the stock hybrid-only `gbrain query`. `QUERY_ROUTER` off serves the single global arm (default); on flips to per-query routing via `query_routing.ts` (the accuracy switch). No policy file yet → hybrid fallback.*

**Code (full source `src/query_policy.ts`):**

```typescript
/**
 * query_policy.ts — the APPLY/actuator half of the auto-eval loop.
 *
 * Stock `gbrain query` is hybrid-only (Phase 6 trap), so it cannot honor a
 * corpus-selected strategy. This helper does: it reads the policy artifact
 * `results/search_policy.json` (written by auto_eval.ts after it measures the
 * current corpus) and routes the query to the WINNING engine path —
 * keyword / vector / hybrid — instead of bare hybrid. That closes the loop:
 *
 *   ingest → reconcile → auto_eval (measure+decide+write policy) → THIS (apply)
 *
 * The agent calls this for its retrieval; the per-corpus verdict steers it.
 *
 * Fallback: if no policy file exists yet, default to hybrid (GBrain's own default).
 *
 * Per-query ROUTER switch (opt-in): set `QUERY_ROUTER=on` to route each query to the arm its
 * TYPE favours (kw→OR-preprocessed keyword · vec→vector · mixed→hybrid) instead of the single
 * global policy. DEFAULT OFF — routing is a *conditional* win (route_principle_ab.ts: +0.039
 * grounding / ~+0.04 answer-quality ONLY when the workload spans query types AND a cheap
 * classifier detects them; on a single-type corpus a perfect router merely ties global and a
 * real classifier nets negative). So it ships off; turn it on when the traffic is mixed-type
 * and the extra accuracy is worth the per-query classify step.
 *
 * Usage: bun src/query_policy.ts "<query text>" [limit]      (global policy — default)
 *        QUERY_ROUTER=on bun src/query_policy.ts "<query>" [limit]   (per-query router)
 */
import { existsSync, readFileSync } from "node:fs";

import { type Strategy, classifyType, preprocessOR, TYPE_TO_STRATEGY } from "./query_routing.ts";

const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;
const POLICY = `${import.meta.dir}/../results/search_policy.json`;

const ROUTER_ON = ["1", "on", "true", "yes"].includes((process.env.QUERY_ROUTER ?? "").toLowerCase());

const query = process.argv[2];
if (!query) {
  console.error('usage: bun src/query_policy.ts "<query text>" [limit]');
  process.exit(1);
}
const limit = Number(process.argv[3] ?? "5");

// ── load the corpus-selected policy (fallback: hybrid) ──────────────────────
let strategy: Strategy = "hybrid";
let rrfK = 60;
let source = "default (no policy file yet)";
if (existsSync(POLICY)) {
  const p = JSON.parse(readFileSync(POLICY, "utf-8"));
  if (p.strategy === "keyword" || p.strategy === "vector" || p.strategy === "hybrid") {
    strategy = p.strategy;
  }
  if (typeof p.rrf_k === "number") rrfK = p.rrf_k;
  source = `results/search_policy.json (n_pages=${p.n_pages}, recall=${p.recall})`;
}

// ── bootstrap engine (identical sequence to auto_eval.ts / the CLI) ──────────
const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway, reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { embed } = await import(`${GB}/core/embedding.ts`);
const { hybridSearch } = await import(`${GB}/core/search/hybrid.ts`);

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
await reconfigureGatewayWithEngine(engine);

// ── pick the strategy: per-query router (opt-in) or the global policy (default) ──
// Router ON: classify the query's type and route to the arm it favours; the keyword arm is
// fed the OR-preprocessed query (the validated path). Router OFF: the single global strategy.
let routeNote = "";
function pickStrategy(): { strategy: Strategy; kwQuery: string } {
  if (!ROUTER_ON) {
    // global policy = whatever auto_eval wrote (keyword | vector | hybrid) — NOT always hybrid;
    // hybrid is only the fallback when no policy file exists. Surface the actual arm.
    const knob = strategy === "hybrid" ? ` rrf_k=${rrfK}` : "";
    routeNote = `router OFF · global policy = ${strategy}${knob}  ←  ${source}`;
    return { strategy, kwQuery: query };
  }
  const type = classifyType(query);
  const routed = TYPE_TO_STRATEGY[type];
  routeNote = `router ON · type=${type} → ${routed}`;
  return { strategy: routed, kwQuery: routed === "keyword" ? preprocessOR(query) : query };
}

async function search(): Promise<{ slug: string }[]> {
  const { strategy: strat, kwQuery } = pickStrategy();
  if (strat === "keyword") return engine.searchKeyword(kwQuery, { limit });
  if (strat === "vector") return engine.searchVector(await embed(query), { limit });
  return hybridSearch(engine, query, { limit, expansion: false, rrfK });
}

const results = await search();
console.log(`policy: ${routeNote}`);
console.log(`query: ${JSON.stringify(query)}  (limit=${limit})`);
for (const [i, r] of results.entries()) console.log(`  ${i + 1}. ${r.slug}`);

await engine.disconnect?.();
process.exit(0);
```

**Walkthrough:**
- **Router OFF (default) = the global policy, *not* hardcoded hybrid.** `strategy` is whatever `auto_eval` wrote to `search_policy.json` — `keyword`, `vector`, **or** `hybrid`. On this 67-page mixed corpus that's `hybrid` (the Phase-6 `vector → hybrid` flip), but on a keyword-heavy or tiny corpus the same OFF path would route `keyword` or `vector`. The log prints the resolved arm (`global policy = hybrid rrf_k=60`) so the choice is never assumed. `hybrid` is only the **fallback** when no policy file exists yet.
- **Router ON (opt-in, `QUERY_ROUTER=on`) ignores the single global arm and routes per query type** via `pickStrategy()` → `classifyType` + `TYPE_TO_STRATEGY` from `query_routing.ts`. The `kw` branch feeds the keyword arm the **OR-preprocessed** query (`kwQuery`), the validated path; `vec`/`mixed` embed/hybrid the raw query. Default off because routing is a *conditional* win — see the re-test above (gates: mixed-type traffic + OR-preprocessed keyword + a cheap classifier).
- **One classifier, two callers.** `query_routing.ts` is imported by both this actuator and the A/B (`route_principle_ab.ts`), so production routes by the *exact* classifier the +0.039 / +0.042 numbers were measured on — no drift between "tested" and "shipped". The vector arm must `embed()` at run-time, which needs the same gateway bootstrap as the eval (`hybrid.ts:975` silently no-ops without it).

**When to use:** reach for `query_routing.ts` (imported, no `main`) whenever you need the shared `classifyType` + `preprocessOR` + `TYPE_TO_STRATEGY` logic - import it into any caller that routes queries by type, rather than duplicating the classifier; use `query_policy.ts` instead when you want a runnable actuator that also reads `search_policy.json` and drives the GBrain engine end-to-end.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  Q[query text] --> CL[classifyType]
  CL -->|exact-token probe| KW[kw]
  CL -->|prose paraphrase<br/>high function-word ratio| VEC[vec]
  CL -->|natural question| MIX[mixed]
  KW --> PRE[preprocessOR<br/>drop STOP · OR-join<br/>avoid conjunctive AND-to-zero]
  PRE --> SK[keyword]
  VEC --> SV[vector]
  MIX --> SH[hybrid]
  SK --> OUT[Strategy<br/>returned to caller]
  SV --> OUT
  SH --> OUT
```
*`query_routing.ts` - the shared classifier brain. One canonical `classifyType` + `preprocessOR`, imported by BOTH the production actuator (`query_policy.ts` under the router switch) AND the A/B that validated it (`route_principle_ab.ts`), so production routes by exactly the tested classifier. `preprocessOR` OR-joins keyword terms so GBrain's conjunctive FTS doesn't AND a verbose query to zero (g@C:kw 0.500 → 1.000).*

**Code (full source `src/query_routing.ts` — the shared router brain):**

```typescript
/**
 * query_routing.ts — shared per-query TYPE classifier + keyword preprocessing.
 *
 * ONE canonical definition, imported by BOTH the production actuator (query_policy.ts, behind
 * the QUERY_ROUTER switch) and the A/B that validated it (route_principle_ab.ts). If the two
 * diverged, the measured win would not transfer — production would route by an unvalidated
 * classifier. Co-locating them guarantees production == tested.
 *
 * The principle this implements: a single global policy compromises queries whose best arm
 * isn't the global winner. Route by query TYPE instead —
 *   exact-token probe  → keyword, OR-preprocessed (so GBrain's conjunctive FTS doesn't AND a
 *                         verbose query to zero; route_eval_kwpp.ts: g@C:kw 0.500 → 1.000)
 *   semantic paraphrase → vector
 *   natural question    → hybrid
 * Measured on the balanced 24-Q set (route_principle_ab.ts): classifier 24/24, router +0.039
 * grounding and ~+0.04 answer-quality (pinned Opus; ±1 question of judge variance) over global
 * hybrid — a modest, real win on mixed-type traffic.
 */
export type QueryType = "kw" | "vec" | "mixed";
export type Strategy = "keyword" | "vector" | "hybrid";

// Generic English stop-words + WH question words dropped before OR-joining the keyword query.
// DELIBERATELY corpus-AGNOSTIC: an earlier version baked in content words from the test questions
// (`berkshire`, `anchor`, `funding`, `guards`…) — that games the eval and breaks on any other
// corpus (dropping `funding` deletes a real search term). Keep only words that are noise in ANY
// English query. Domain/boilerplate stop terms, if ever needed, belong in a per-corpus config
// loaded at run-time, not hardcoded in the shared router.
export const STOP = new Set([
  "a", "an", "the", "of", "in", "on", "at", "for", "to", "and", "or", "is", "are", "was", "were",
  "be", "been", "being", "am", "it", "its", "this", "that", "these", "those", "with", "from", "by",
  "as", "into", "than", "then", "there", "here", "about", "what", "which", "who", "whom", "whose",
  "where", "when", "how", "why", "did", "does", "do", "done", "has", "have", "had", "will", "would",
  "could", "should", "shall", "can", "may", "might", "must", "their", "his", "her", "they", "them",
  "he", "she", "we", "you", "i", "my", "our", "your", "his", "hers", "not", "no",
]);

// Function words used to detect a prose paraphrase (high ratio → semantic, not exact-token).
export const FUNCTION = new Set([
  "the", "a", "an", "of", "in", "on", "for", "to", "and", "or", "is", "are", "was", "were",
  "that", "this", "with", "from", "by", "as", "at", "be", "it", "they", "its", "his", "her",
  "their", "how", "who", "which", "where", "what", "when", "could", "following",
]);

/**
 * Drop stop/question words, then OR-join the salient tokens. OR switches GBrain's
 * `websearch_to_tsquery` from AND (every token must co-occur in one chunk → verbose queries
 * score 0) to best-match (a missing token lowers rank instead of zeroing the match).
 */
export function preprocessOR(q: string): string {
  const toks = (q.toLowerCase().match(/[a-z0-9]+/g) ?? []).filter(t => t.length > 1 && !STOP.has(t));
  const uniq = [...new Set(toks)];
  return uniq.length ? uniq.join(" OR ") : q;   // fall back to raw if we stripped everything
}

/**
 * Deterministic, zero-LLM query-type classifier. A natural question (ends '?') is mixed;
 * a high function-word ratio / leading lowercase connective marks a semantic paraphrase;
 * otherwise distinctive exact tokens (Item N, ALL-CAPS, capitalised entity runs, digit+%) or a
 * capitalised lead marks an exact-token keyword probe.
 */
export function classifyType(q: string): QueryType {
  const raw = q.trim();
  if (/\?\s*$/.test(raw)) return "mixed";
  const words = raw.split(/\s+/);
  const distinctive = raw.match(
    /\bItem\s+\d+[A-Z]?\b|\b[A-Z]{2,}\b|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b|\b\d+\s*(?:percent|%)\b/g,
  ) ?? [];
  const fnRatio = words.filter(w => FUNCTION.has(w.toLowerCase())).length / words.length;
  const leadsLowerFn = FUNCTION.has(words[0].toLowerCase()) && /^[a-z]/.test(words[0]);
  if (leadsLowerFn || fnRatio >= 0.4) return "vec";
  if (distinctive.length >= 1 || /^[A-Z]/.test(words[0])) return "kw";
  return "vec";
}

// Arm each query type routes to. `kw` → keyword arm, fed the OR-preprocessed query.
export const TYPE_TO_STRATEGY: Record<QueryType, Strategy> = {
  kw: "keyword",
  vec: "vector",
  mixed: "hybrid",
};
```

**Walkthrough:**
- **`classifyType` is a deterministic ladder, no LLM.** `?`-terminated → `mixed` (natural question); else a high function-word ratio or a leading lowercase connective → `vec` (prose paraphrase); else distinctive exact tokens (`Item N`, ALL-CAPS, capitalised runs, `27 percent`) or a capitalised lead → `kw`. It's cheap enough to run per query, which is the whole point — a per-query branch can't afford an LLM classifier.
- **`preprocessOR` is the load-bearing line.** Dropping stop-words then OR-joining flips GBrain's conjunctive FTS from "every token must co-occur" (verbose queries → 0) to best-match. Without it, routing `kw → keyword` routes to a crippled arm and *loses* — the OR-preprocess is what makes the `kw` route a win (`g@C:kw` 0.500 → 1.000).
- **The honest caveat the classifier carries:** 24/24 on the balanced set is partly because that set is built type-separable (`kw` = token-lists, `vec` = prose). Real traffic blurs the boundary, so production accuracy < 24/24 and the realized gain shrinks toward the classifier's error rate. It's a *starting* classifier, not a finished one.

#### Block D — the recommended architecture (measured policy, three layers)

Phase 9 converges on a reusable shape for any self-tuning retrieval policy — see `[[Engineering Decision Patterns#Pattern 37 — Measured Search-Policy Architecture (selector / gate / calibrator; score the prompt, not the retrieval)|Pattern 37]]`. Three layers, and little else:

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  NEW["new data"] --> ING["ingest +<br/>reconcile<br/>graph self-wires"]
  ING -->|"every ingest"| SEL["SELECTOR<br/>policy_eval.ts<br/>disc. grounding@C<br/>global arm · 0-LLM"]
  SEL -->|"writes"| POL[("search_policy.json")]
  POL -->|"steady state"| ACT{"actuator<br/>query_policy.ts"}
  ACT -->|"default"| GLOB["apply global<br/>policy arm"]
  ACT -->|"QUERY_ROUTER on"| RTR["classify query type<br/>→ per-arm route<br/>kw · vec · mixed"]
  GLOB --> ANS["agent answer"]
  RTR --> ANS
  ANS -.->|"next ingest re-tunes"| NEW
  POL -.->|"on policy flip"| GATE["GATE<br/>answer-judge<br/>old vs new arm<br/>adopt iff no regress"]
  SEL -.->|"on domain shift"| CAL["CALIBRATOR<br/>verify_arch.py<br/>corr grnd vs answer<br/>+0.820 measured"]
```

The **loop is the point**: every ingest re-runs the SELECTOR, which re-measures the arms and rewrites `search_policy.json` — the system re-tunes itself as the corpus grows, with no human in the loop (this is what flipped `vector → hybrid` in Phase 6 when the 10-K landed on the entity brain). The **actuator** then serves each query *either* by the single global policy arm (default) *or*, with `QUERY_ROUTER=on`, by classifying the query's type and routing per-arm (`kw → key_pp`, `vec → vector`, `mixed → hybrid`). GATE and CALIBRATOR are **event-triggered, not per-query** — the GATE answer-judge fires only when the selector *flips* the policy (adopt the new arm iff it doesn't regress), and the CALIBRATOR re-checks `corr(grounding, answer)` only on a domain shift. Both stay out of the hot path; only the 0-LLM selector and the deterministic actuator run continuously.

**Verified end-to-end** on the **`tenk` subset — the 12 10-K questions that carry `pass_criteria`** (`src/verify_arch.py`, judge = Claude Opus 4.5, 3 arms × 12 Q = **36 cells**). Grounding here is the **`g@3:tenk` column** of the metric table above — *not* a new measurement — so `hybrid` reads **0.927** (the 12-Q tenk slice), which is why it differs from the 18-Q full-set `0.910` (metric table) and the balanced-set `0.823` (routing tables): **same metric, three different question sets**. The point of this table is the second column (answer pass-rate), which only exists for questions with a rubric:

| arm        | grnd@3↓ (`tenk`, 12 Q) | answer pass-rate (`tenk`, 12 Q) |
| ---------- | -------------------------- | ------------------------------- |
| keyword    | 0.250                      | 0.167                           |
| vector     | 0.858                      | 0.917                           |
| **hybrid** | **0.927**                  | **1.000**                       |

> **Provenance note (re-verified 2026-06-07, `results/verify_arch.out`).** Both columns are **current**: re-run uncapped on Opus 4.5 after the corpus picked up the combined **PageIndex+GBrain** ingest (the `**Location:**` breadcrumbs — see the combined-solution subsection). That ingest is what moved the numbers — keyword/vector grounding rose (`vector 0.816 → 0.858`) *and* their answers rose with them (`vector pass 0.750 → 0.917`, `hybrid 0.917 → 1.000`), which is why the calibrator went **up**, not down. The earlier worry that the drift might break the architecture was the right thing to check and it resolved favourably: grounding and answers moved *together*.

> **What `corr` means, and where its inputs live (it is *not* in the table above).** `corr` is the **Pearson correlation coefficient** `r` — a single number on `[−1, +1]` that says how tightly two paired series move together: `+1` = perfectly in step, `0` = unrelated, `−1` = opposite. Here `+0.820` means *high discounted grounding strongly tends to coincide with a PASS*. Crucially, it is computed over the **36 individual `(arm × question)` cells** — 3 arms × 12 `tenk` questions — where each cell is one pair **`(discounted grounding@C, answer-pass)`** with `PASS = 1`, `FAIL = 0`. It is **not** derivable from the 3-row table above: collapsing each arm to a single `(mean-grounding, mean-pass)` point discards the spread a correlation needs (three points can't give a meaningful `r`). The 36 raw cells are persisted in **`results/verify_arch.out`**, one line each — e.g. `vector grnd=1.000 ans=P` → `(1.000, 1)`. The cells that pull `r` below `1.0` are the residual disagreements: a false-**positive** (`keyword` on the Notes question — `grnd=1.000, ans=F`) and a false-**negative** (`vector` on the 'not-so-secret weapon' question — `grnd=0.375, ans=P`, the strong generator answering from thin context). So the table answers *"does the winning arm rank the same on both axes?"* (selector validity); the correlation answers *"does grounding track answer quality point-by-point across every cell?"* (calibrator) — two different questions, two different granularities.

- **Calibrator** — `corr(discounted grounding@C, answer-pass) = +0.820` (36 cells, re-verified 2026-06-07). The cheap, deterministic metric strongly predicts the expensive answer-judge.

    > **Why "0-LLM selector / no judge in the hot loop" is the keystone — in detail.** The SELECTOR runs on **every ingest** — that's the hot loop. It picks the search policy by computing `discounted grounding@C` per arm: substring coverage × a position discount, a pure deterministic calculation with **no model call**. The tempting alternative is to score each arm with an LLM *answer-judge* on every ingest — and it's wrong three ways. **(1) Cost:** a judge call per arm × per question × every ingest meters the self-tuning loop with API spend that scales with corpus churn (and, as this very phase showed, a single uncapped answer-eval is ~1.5M tokens). **(2) Latency:** ingest would block on dozens of generate-then-judge round-trips before the policy could update. **(3) Confounding:** judging *retrieval* by *answer quality* folds generation variance into a retrieval decision, so a policy could flip on model noise rather than a real retrieval change — the exact trap that sank the LLM-in-selector idea and produced the weak-model confound in the routing A/B. The calibrator `r = +0.820` is what **licenses** the cheap proxy: because grounding predicts the judge strongly, you run the deterministic metric *continuously* in the loop and reserve the expensive judge for **event-triggered** checks only — the GATE (on a policy flip) and the CALIBRATOR itself (on a domain shift). **Cheap-and-continuous in the hot path; expensive-and-rare on the edges.** If `r` were low, that split would collapse: you couldn't trust the cheap metric, the judge would have to move into the hot loop, and the self-tuning economics (free re-tune on every ingest) break. So `r` isn't a vanity statistic — it is the single number that determines whether the architecture is *affordable*.

- **Selector validity** — the max-grounding arm (`hybrid`) is also the answer-quality winner (`1.000` pass), and the ordering `keyword < vector < hybrid` holds on **both** axes (grounding `0.250 < 0.858 < 0.927`; answer `0.167 < 0.917 < 1.000`) → CONFIRMED.
- **The residual (r=0.820, not 1.0) is instructive — and the gap it once flagged is now *closed*.** Earlier *"Where are the Notes to Consolidated Financial Statements located?"* grounded **1.000 on all three arms yet the answer FAILED** for every arm: a **false-positive grounding** — the chunks (`sections/brk_0034/0039/0040`) contained the `Item 8` / `Notes to Consolidated` substrings, but as a buried page-header marker, not a clean "*the Notes are in Item 8, pages 99–147*" statement. The **combined PageIndex+GBrain ingest** (see the combined-solution subsection) fixed exactly this: every section now carries a `**Location:** Item 8 — Notes to Consolidated Financial Statements · pages 99–147` breadcrumb *in its body*, so the shipped policy (`hybrid`) and `vector` now **answer it correctly** — only the `keyword` arm still fails (it retrieves the body without surfacing the location line at rank 0). What remains of the residual `r=0.820 < 1.0` is now a *mix*: keyword's leftover false-positives, **plus the reverse case** — the strong generator passing from *low*-grounding context (the 'not-so-secret weapon' question: `vector` grounds only 0.375 yet the answer PASSES — a false *negative* for the metric). The metric↔answer agreement **rose** (0.719 → 0.820) precisely because the structural fix landed: once the location is *in the page*, the cheap substring metric and answer quality line up. The residual is where they still diverge — a retrieval-*representation* effect (now partly a generator-strength effect), not pure noise.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  HITS[retrieved hits<br/>per-rank coverage array] --> BS[budgetScore<br/>scan top-C only]
  BS --> CV[coverage r<br/>entities matched / total]
  BS --> DI[disc r<br/>1 / log2 rank+2<br/>rank0=1 · rank1=0.63]
  CV --> MX[gDisc = max of<br/>coverage x disc<br/>over top-C]
  DI --> MX
  CV --> GF[gFull = max coverage<br/>over top-C]
  MX --> OUT[BudgetScore<br/>gDisc drives policy]
  GF --> OUT
```
*`grounding.ts` scoring flow. Pure functions, no I/O - which is why they live apart from `policy_eval.ts` and are unit-tested. `budgetScore` reads only the top-`C` ranks (the generator's budget); `gDisc` rewards early placement via `disc(rank)`, so an RRF reorder that demotes the answer chunk lowers the score and a chunk pushed past `C` scores 0.*

**When to use:** Reach for `grounding.ts` whenever you need to compute `discounted grounding@C` or `answerable@C` outside of `policy_eval.ts` - for example, writing a new eval script, a unit test, or a one-off probe - because it is the single source of truth for both `coverage` and `disc`, and importing it keeps all scoring logic consistent and avoids reimplementing the position-discount formula by hand.

**The load-bearing primitive — complete source** (`src/grounding.ts`, pure + unit-tested):

```typescript
/**
 * grounding.ts — pure scoring primitives for the policy eval (no I/O, unit-testable).
 *
 * The policy's objective is ANSWER quality, not raw retrieval. The generator reads
 * only the top-C chunks, in order — so the metric scores the prompt it actually sees:
 * position-weighted best coverage over the context budget. An RRF reorder that demotes
 * the answer chunk, or pushes it past C, lowers the score; the old rank-blind
 * max-over-top-K could not see either.
 */

/** Substring coverage of a section's (lowercased) text against expected entities, ∈ [0,1]. */
export const coverage = (lowercasedText: string, ents: string[]): number =>
  ents.length ? ents.filter(e => lowercasedText.includes(e.toLowerCase())).length / ents.length : 0;

/** Position discount: rank-0 = 1.0, decaying with depth. disc(0)=1, disc(1)=0.63, disc(2)=0.5. */
export const disc = (rank0: number): number => 1 / Math.log2(rank0 + 2);

export interface BudgetScore {
  /** max_i coverage_i · disc(i) over the top-C window — drives the policy. */
  gDisc: number;
  /** max_i coverage_i over the top-C window — raw best coverage (feeds answerable@C). */
  gFull: number;
}

/**
 * Score one question from the per-rank coverage of its retrieved hits.
 * `coverages` is coverage at each retrieved rank (length ≤ K); only the first `c`
 * (the context budget) are read — anything past C contributes nothing, modelling
 * "the answer fell out of the prompt".
 */
export function budgetScore(coverages: number[], c: number): BudgetScore {
  let gDisc = 0;
  let gFull = 0;
  for (let r = 0; r < Math.min(coverages.length, c); r++) {
    gDisc = Math.max(gDisc, coverages[r] * disc(r));
    gFull = Math.max(gFull, coverages[r]);
  }
  return { gDisc, gFull };
}
```

**Walkthrough:**
- **`coverage` is the label-cheap gold.** It asks only "does this section's text contain the expected entity substrings?" - no per-slug relevance labels, so the golden set stays cheap to extend as the query distribution shifts. Lowercasing both sides makes it case-robust.
- **`disc` encodes primacy, DCG-style.** `1/log2(rank+2)` gives rank-0 a weight of 1.0, rank-1 0.63, rank-2 0.5 - a smooth decay that punishes burying the answer. This is the exact signal a rank-blind `max`-over-top-K throws away, and it's why the metric can *see* an RRF reorder that demotes the dense answer below a keyword distractor.
- **`budgetScore` scores the prompt the generator actually reads.** It scans only the first `c` ranks (the production injected-chunk count), so a hit past `C` contributes nothing - modelling "the answer fell out of the context window". `gDisc` (position-weighted) drives the policy; `gFull` (raw best coverage) feeds the separate `answerable@C` diagnostic.
- **Pure + no I/O is the whole reason it's its own file.** Keeping the math free of engine/DB calls makes it unit-testable in isolation (the deterministic grounding tests) and reusable by every orchestration script below without dragging in GBrain - the same separation-of-concerns that lets the 0-LLM selector run on every ingest cheaply.

**The deterministic contract — unit tests for `grounding.ts`** (`src/grounding.test.ts`)

Because `grounding.ts` is pure math with no I/O, every correctness claim about the metric can be pinned by a fast offline test. `grounding.test.ts` exercises exactly the three failure modes the new metric was designed to catch: the `disc` decay values at each rank, RRF demotion (answer pushed from rank 0 to rank 1), and context-budget overflow (answer retrieved but pushed past `C` so the generator never reads it). Each test also runs the *old* rank-blind `max-over-top-K` side-by-side to document the delta - making the regression visible as executable specification rather than prose.

**When to use:** reach for `grounding.test.ts` when you change any formula in `grounding.ts` (discount factor, coverage logic, budget window) and need to confirm the three failure modes are still caught - or when onboarding a reader who needs to understand *why* the metric is shaped this way before reading the policy eval scripts.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  IMP["import budgetScore,<br/>coverage, disc<br/>from grounding.ts"] --> T1["disc primacy test<br/>rank 0=1.0, 1=0.63, 2=0.5"]
  IMP --> T2["coverage test<br/>case-insensitive fraction"]
  IMP --> T3["rank-0 perfect score<br/>gDisc == 1.0"]
  IMP --> T4["RRF demotion test<br/>old metric: blind<br/>new metric: sees demotion"]
  IMP --> T5["budget overflow test<br/>rank 3 past C=3<br/>old: 1.0 · new: 0"]
  IMP --> T6["partial coverage<br/>magnitude preserved"]
  IMP --> T7["gFull vs gDisc<br/>position-blind vs weighted"]
  OLD["oldRankBlind<br/>max over top-K"] --> T4
  OLD --> T5
```
*`grounding.test.ts` call flow. Each test imports the three pure functions and runs `bun test` with no services. Tests T4 and T5 also invoke `oldRankBlind` (the superseded metric) to document exactly where it was blind - making the regression an executable specification.*

**Code: `src/grounding.test.ts`**

```typescript
/**
 * Verifies the budget-aware discounted grounding metric behaves where the old
 * rank-blind max-over-top-K was blind: RRF reorders and budget overflow.
 *
 * Run: bun test src/grounding.test.ts
 */
import { expect, test } from "bun:test";

import { budgetScore, coverage, disc } from "./grounding.ts";

const C = 3;
const oldRankBlind = (covs: number[], k: number) => Math.max(0, ...covs.slice(0, k)); // the metric we replaced

test("disc encodes primacy: 1.0, 0.63, 0.5 at ranks 0,1,2", () => {
  expect(disc(0)).toBe(1);
  expect(disc(1)).toBeCloseTo(0.6309, 3);
  expect(disc(2)).toBe(0.5);
});

test("coverage is fraction of expected entities present (case-insensitive)", () => {
  expect(coverage("sam okafor anchors northstar", ["Sam Okafor", "Northstar"])).toBe(1);
  expect(coverage("sam okafor only", ["Sam Okafor", "Northstar"])).toBe(0.5);
  expect(coverage("nothing relevant", ["Sam Okafor"])).toBe(0);
});

test("answer at rank 0 scores a perfect 1.0", () => {
  expect(budgetScore([1, 0, 0], C).gDisc).toBe(1);
});

test("RRF demotion (distractor at rank 0, answer at rank 1) is penalised — old metric was blind", () => {
  const demoted = [0, 1, 0]; // answer pushed to rank 1 by a fused distractor
  const top = [1, 0, 0];
  // The failure the user named: old rank-blind max says both are identical...
  expect(oldRankBlind(demoted, 5)).toBe(oldRankBlind(top, 5)); // both 1.0 — blind
  // ...the new metric sees the demotion.
  expect(budgetScore(demoted, C).gDisc).toBeCloseTo(0.6309, 3);
  expect(budgetScore(demoted, C).gDisc).toBeLessThan(budgetScore(top, C).gDisc);
});

test("answer pushed PAST the context budget scores 0 — retrieved (in K) but out of the prompt", () => {
  const pastBudget = [0, 0, 0, 1]; // answer at rank 3, budget C=3 reads ranks 0..2
  expect(oldRankBlind(pastBudget, 5)).toBe(1); // old metric: still "in top-K", looks fine
  expect(budgetScore(pastBudget, C).gDisc).toBe(0); // new metric: it never reaches the generator
  expect(budgetScore(pastBudget, C).gFull).toBe(0);
});

test("partial coverage is preserved, not rounded up (answer-quality magnitude kept)", () => {
  expect(budgetScore([0.5, 0, 0], C).gDisc).toBe(0.5); // half the entities, at rank 0
  expect(budgetScore([0.5, 1, 0], C).gDisc).toBeCloseTo(0.6309, 3); // full@1 (0.63) beats half@0 (0.5)
});

test("gFull (answerable source) ignores position; gDisc (policy) respects it", () => {
  const s = budgetScore([0, 1, 0], C);
  expect(s.gFull).toBe(1); // a fully-covering section exists in budget → answerable
  expect(s.gDisc).toBeCloseTo(0.6309, 3); // but it's demoted → graded down for the policy
});
```

**Walkthrough:**
- **Structure mirrors the metric's design contract, not test-by-test mechanics.** The test file is organised around the three failure modes the new metric was *designed to catch*: rank decay (`disc`), RRF reorder blindness, and context-budget overflow. Reading the tests in order is the fastest way to understand *why* `grounding.ts` is shaped the way it is - each test is a proof-by-example that the old `max-over-top-K` was insufficient.
- **`oldRankBlind` is inlined as living documentation.** Rather than prose-commenting that the old metric was blind, the tests make it executable: `expect(oldRankBlind(demoted, 5)).toBe(oldRankBlind(top, 5))` pins *exactly* the failure (both return 1.0 regardless of rank), then the next assertion shows the new metric returns 0.63 for the demoted case. Any future reader who deletes `disc` from `grounding.ts` will see these two tests fail together - the regression is self-describing.
- **Budget overflow test documents the hardest-to-see failure.** `pastBudget = [0, 0, 0, 1]` with `C=3` is the case where retrieval *looks* successful (top-K contains the answer) but the generator never reads it. `oldRankBlind(pastBudget, 5)` returns 1 - looks fine; both `gDisc` and `gFull` return 0 - the generator window is the real unit. This is the principal argument for `C` as a first-class parameter of the metric.
- **No services, no I/O, pure Bun test.** `bun test src/grounding.test.ts` runs in milliseconds from any machine without GBrain, Postgres, or oMLX - the separation-of-concerns in `grounding.ts` pays off directly here as test isolation. This is what lets the metric be verified in CI without a live stack.

The orchestration scripts consume this primitive: `policy_eval.ts` (selector — writes the policy), `route_eval.ts` (routing headroom + per-arm dump), `route_eval_kwpp.ts` + `route_principle_ab.ts` (the keyword-revival and per-query-routing A/Bs), `answer_route_ab.py` / `answer_principle_ab.py` (answer A/Bs), `verify_arch.py` (calibrator + selector audit). **What NOT to build** (each measured into the ground this phase): an LLM judge in the every-ingest selector (confounds retrieval choice with generation variance, *and* meters the loop); a rank-blind metric (can't see RRF demotion); a hand-picked `C` (scores a context the model never reads); **entity-aware graph expansion in the live path** (fixes only 1/24 — judge-noise magnitude — and only *missing-neighbor* 2-hop, not distractor failures; runtime token cost is unbounded in neighbor page size; kept as a tested module, shelved — see "Decision — measured, NOT shipped"). Most of the win was **deletion** — the final system is simpler than the naïve one *and* better, because each cut piece failed a measurement.

**What we DID build (gated): the per-query router.** Unlike the shelved items above, per-query routing earned its place — it is shipped in `query_policy.ts` behind `QUERY_ROUTER`, **default-off**. On a single-type corpus the oracle ceiling equals global hybrid (Δ0), so you leave it off; once the workload spans query types and the keyword arm is OR-preprocessed it **reverses to +0.039 grounding / +0.042 answer** and you switch it on. So the router is not a "don't build" — it's a "build it, gate it on the workload."

**The calibrator + selector audit — complete source** (`src/verify_arch.py`)

This is the script behind the `r = +0.820` number above - the **one place the expensive LLM judge runs**, on purpose, as a one-off audit rather than in the every-ingest hot loop. The "measured policy, three layers" design rests on a single empirical claim: the cheap, deterministic SELECTOR metric (`discounted grounding@C`) predicts ANSWER quality well enough to pick the right arm *without* an LLM in the loop. `verify_arch.py` tests that claim directly. It pairs, for every arm × every `tenk` golden question (the ones carrying `pass_criteria`), the **cheap metric** (`grnd@C↓` from `arm_scores.json`, zero-LLM) with the **real objective** (generate an answer from that arm's top-C context, judge PASS/FAIL against the rubric with a strong model), then reports two different things at two different granularities: the **CALIBRATOR** (cell-level `corr(grounding, answer-pass)` - does the surrogate track the objective?) and the **SELECTOR validity** check (arm-level - does max-grounding also win on answers?).

**When to use:** Reach for `verify_arch.py` once after building a new corpus (or after a major grounding-metric change) to confirm that the cheap surrogate still predicts answer quality well enough to justify keeping the LLM out of the hot-loop selector - use the sibling A/B scripts (`route_eval.ts`, `answer_route_ab.py`) for ongoing per-arm experiments instead.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  AS[(arm_scores.json<br/>grnd@C↓ per arm x Q<br/>0-LLM · route_eval.ts)] --> PAIR[for arm x tenk-Q:<br/>pair grnd@C↓ with answer]
  GT[(W2.7 ground truth<br/>pass_criteria · tenk only)] --> PAIR
  PAIR --> ANS[_answer<br/>generate from arm top-C<br/>strong model · Opus]
  ANS --> JG[_judge<br/>PASS / FAIL vs pass_criteria]
  JG --> CELLS[36 cells<br/>grnd , pass 0 or 1]
  CELLS --> CAL[CALIBRATOR<br/>Pearson r · cell-level<br/>grnd vs pass<br/>+0.820]
  CELLS --> SEL[SELECTOR audit<br/>per-arm mean grnd vs pass]
  SEL --> V{argmax grnd<br/>== argmax pass?}
  V -->|yes| OK[CONFIRMED]
  V -->|no| MM[MISMATCH]
```
*`verify_arch.py` flow. The cheap grounding scores arrive pre-computed and zero-LLM; the expensive half (generate + judge with Opus) runs only here, off the hot path. CALIBRATOR correlates the two over all 36 `arm × question` cells; SELECTOR validity checks the arm-level winners match. This is the GATE/CALIBRATOR of Block D's three-layer diagram, run as a one-off audit.*

**Code (full source `src/verify_arch.py`):**

```python
"""verify_arch.py — does the recommended architecture actually hold on this corpus?

The "measured policy, three layers" design rests on ONE empirical claim: the cheap,
deterministic SELECTOR metric (discounted grounding@C) predicts ANSWER quality well
enough to pick the right arm without an LLM in the hot loop. This script tests that
claim directly — the CALIBRATOR step — and confirms the SELECTOR's pick is the
answer-quality winner (the GATE's job, run here as a one-off audit).

For every arm (keyword/vector/hybrid) × every tenk golden question (those carry
pass_criteria), it pairs:
  - the cheap metric : discounted grounding@C  (from results/arm_scores.json, zero-LLM)
  - the real objective: answer PASS/FAIL        (generate from that arm's top-C context,
                                                 judge against pass_criteria — strong model)
Then reports:
  1. correlation(grounding, answer-pass) across all arm×question cells  → does the cheap
     surrogate track the objective? (the architecture's load-bearing assumption)
  2. per-arm mean grounding vs answer pass-rate → does the SELECTOR's winner (max grounding)
     also win on answers? (selector validity)

Inputs: results/arm_scores.json (from `bun src/route_eval.ts`) + the W2.7 ground truth.
Run with a STRONG generator so the answer signal isn't generation-noise-limited:
  OPENROUTER_BASE_URL=http://localhost:8317/v1 OPENROUTER_API_KEY=vibeproxy \
  CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/verify_arch.py
"""
from __future__ import annotations

import json
import pathlib
import statistics

from answer_route_ab import LLMUnavailable, _answer, _judge, _pass_criteria_by_q
from ground_truth_ab import _client

_ARMS = ("keyword", "vector", "hybrid")
_ARM_SCORES = pathlib.Path(__file__).resolve().parent.parent / "results" / "arm_scores.json"


def _correlation(xs: list[float], ys: list[float]) -> float | None:
    """Pearson r; None if either series is constant (correlation undefined)."""
    if len(xs) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return statistics.correlation(xs, ys)


def main() -> None:
    dump = json.loads(_ARM_SCORES.read_text())
    criteria_by_q = _pass_criteria_by_q()
    client = _client()

    g_all: list[float] = []        # grounding per arm×question cell
    p_all: list[float] = []        # answer pass (0/1) per cell
    per_arm: dict[str, dict[str, list[float]]] = {a: {"g": [], "p": []} for a in _ARMS}

    for item in dump:
        q = item["q"].strip()
        criteria = criteria_by_q.get(q)
        if criteria is None:
            continue  # entity questions have no rubric — skip
        for arm in _ARMS:
            grounding = float(item["grounding"][arm])
            try:
                passed = _judge(client, _answer(client, item["slugs"][arm], q), criteria)
            except LLMUnavailable as exc:
                print(f"  [skip] {arm:7s} {q[:44]} ({exc})")
                continue
            p = 1.0 if passed else 0.0
            g_all.append(grounding)
            p_all.append(p)
            per_arm[arm]["g"].append(grounding)
            per_arm[arm]["p"].append(p)
            print(f"  {arm:7s} grnd={grounding:.3f} ans={'P' if passed else 'F'}  {q[:44]}")

    n = len(g_all)
    corr = _correlation(g_all, p_all)
    print(f"\n=== CALIBRATOR — does the cheap metric predict answer quality? ===")
    print(f"  cells judged: {n}")
    print(f"  corr(discounted grounding@C, answer-pass) = "
          f"{'n/a' if corr is None else f'{corr:+.3f}'}")

    print(f"\n=== SELECTOR — is the max-grounding arm the answer-quality winner? ===")
    print(f"  {'arm':8s} {'mean grnd':>10s} {'ans pass':>9s}")
    arm_grnd = {a: statistics.fmean(per_arm[a]["g"]) if per_arm[a]["g"] else 0.0 for a in _ARMS}
    arm_pass = {a: statistics.fmean(per_arm[a]["p"]) if per_arm[a]["p"] else 0.0 for a in _ARMS}
    for a in _ARMS:
        print(f"  {a:8s} {arm_grnd[a]:10.3f} {arm_pass[a]:9.3f}")
    g_winner = max(_ARMS, key=lambda a: arm_grnd[a])
    p_winner = max(_ARMS, key=lambda a: arm_pass[a])
    verdict = "CONFIRMED" if g_winner == p_winner else "MISMATCH"
    print(f"\n  selector pick (max grounding) = {g_winner};  answer winner = {p_winner}"
          f"  → {verdict}")


if __name__ == "__main__":
    main()
```

**Walkthrough:** *(design principle first, then the details that make it trustworthy)*
- **Design principle - this script earns the right to keep the LLM out of the hot loop.** The whole self-tuning economy (re-select on *every* ingest, free) depends on a deterministic metric standing in for an expensive judge. That substitution is only legitimate if someone *measured* that the cheap metric tracks the real objective. `verify_arch.py` is that measurement - the expensive judge run **once, deliberately, off the hot path**, the exact opposite of the rejected "judge in the selector" design. The output `r` is a license: high `r` → trust the proxy continuously and reserve the judge for event-triggered GATE/CALIBRATOR checks; low `r` → the architecture is unsafe and the judge would have to move into the loop, collapsing the economics.
- **Cell-level pairing, not arm-means - because correlation needs spread.** It accumulates one `(grounding, pass)` pair per `arm × question` **cell** (`g_all`/`p_all`) → 36 points (3 arms × 12 `tenk` questions). Collapsing each arm to a single `(mean-grounding, mean-pass)` point leaves 3 points - too few for a meaningful `r`, and it hides the within-arm disagreements that are the whole diagnostic. The per-arm aggregates (`per_arm`) are computed **separately**, only for the SELECTOR-validity view.
- **Strong generator is load-bearing, not a luxury.** Answers are generated and judged with Opus (the `CHAT_MODEL` env in the docstring). With a weak model, a FAIL could mean "the model couldn't write the answer" rather than "the context didn't contain it" - and the correlation would measure *generation* noise instead of *retrieval* quality. Pinning a strong generator makes a FAIL mean a retrieval-representation gap, which is precisely what the calibrator must detect.
- **Two outputs, two questions, two granularities.** CALIBRATOR = `corr` over all cells: *does the cheap surrogate track the objective, point by point?* SELECTOR validity = per-arm `argmax grnd == argmax pass`: *does the arm the selector would pick also win on answers?* They can disagree (a high-but-imperfect `r` with a still-correct winner) - exactly the `r=0.820 < 1.0` yet `CONFIRMED` situation.
- **`_correlation` guards the undefined case.** `statistics.correlation` is undefined when either series is constant (zero variance), so the helper returns `None` (printed `n/a`) if `<2` distinct values exist - e.g. very early, before the corpus produces any answer variation. Cheap defensiveness that keeps the audit from throwing on a thin brain.
- **It reuses the A/B lineage, not bespoke plumbing.** `_answer`/`_judge`/`_pass_criteria_by_q` come from `answer_route_ab.py` and `_client` from `ground_truth_ab.py` - the same generate-and-judge code the routing experiments used, so the calibrator measures exactly what those A/Bs measured (no drift between "what we tested" and "what we audit").

**Result (measured, `results/verify_arch.out`, re-verified 2026-06-07, judge = Claude Opus 4.5, 36 cells):** `corr(discounted grounding@C, answer-pass) = +0.820`. Per-arm SELECTOR view - `keyword 0.250 grnd / 0.167 pass`, `vector 0.858 / 0.917`, `hybrid 0.927 / 1.000` - so `argmax grnd = hybrid` and `argmax pass = hybrid` → **CONFIRMED**. The residual (`r < 1.0`) is the handful of cells where the two disagree (keyword's false-positive grounding on the Notes question; vector answering correctly from low-grounding context on the "not-so-secret weapon" question) - documented above as a retrieval-*representation* effect, not noise.

#### Block D.1 — `route_eval.ts`: routing headroom + per-arm dump

`route_eval.ts` is the **oracle experiment** that decides whether per-query routing is worth building. It runs all three retrieval arms over every golden question with the same discounted grounding@C as `policy_eval.ts`, then compares three routers: the *global* baseline (one arm for all queries), a *heuristic* zero-LLM classifier, and the *oracle ceiling* (each query gets its own best arm, label-peeking). The two JSON dumps it writes - `arm_scores.json` and `route_slugs.json` - are the pre-computed feed for every downstream Python A/B (`verify_arch.py`, `answer_route_ab.py`, `reader_ab.py`), so this script must run before any of them.

**When to use:** reach for `route_eval.ts` when you want to know whether per-query routing has any headroom on your corpus before investing in a classifier - run it once on a new golden set; if oracle equals global, routing is all-risk-no-reward and you stop; if oracle beats global, the gap is the budget a classifier can spend on its own errors. Its siblings `route_eval_kwpp.ts` and `route_principle_ab.ts` extend this measurement to specific keyword fixes and 3-policy comparisons; use those only after `route_eval.ts` confirms there is headroom to investigate.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  GQ[(golden_eval.json<br/>questions + entities)] --> BOOT
  ENV["GBRAIN_SRC / env vars<br/>K=5  C=3"] --> BOOT
  BOOT["engine bootstrap<br/>loadConfig · createEngine<br/>connectWithRetry<br/>configureGateway"] --> ARMS
  ARMS["for each arm:<br/>keyword · vector · hybrid"] --> EVAL
  EVAL["runEval<br/>top-K slugs per query"] --> SCORE
  SCORE["coverage + budgetScore<br/>→ gDisc per question"] --> CACHE
  CACHE["sectionText cache<br/>getPage · compiled_truth"] --> SCORE
  SCORE --> MATRIX["score matrix<br/>3 arms × N questions"]
  MATRIX --> GLOBAL["global router<br/>every query → hybrid"]
  MATRIX --> HEUR["heuristic router<br/>classify → kw or hybrid"]
  MATRIX --> ORA["oracle router<br/>each query → best arm"]
  GLOBAL --> RPT["per-question table<br/>+ summary means + Δ"]
  HEUR --> RPT
  ORA --> RPT
  MATRIX --> SLUGDUMP[(route_slugs.json<br/>global vs routed slugs)]
  MATRIX --> ARMDUMP[(arm_scores.json<br/>grnd + slugs per arm × Q)]
```
*`route_eval.ts` data flow. The engine bootstrap is identical to `policy_eval.ts`; the loop scores all three arms in one pass so the oracle comparison is exact (same corpus state, same embed run). Dumps feed the Python A/Bs without a second retrieval round.*

**Code (`src/route_eval.ts`):**

```typescript
/**
 * route_eval.ts — does PER-QUERY routing beat the single global policy?
 *
 * The global loop (policy_eval.ts) picks ONE arm for the whole corpus. But the best
 * arm is query-dependent: proper-noun lookups favour keyword/hybrid, semantic factoids
 * favour dense vector. This script measures whether routing each query to its own best
 * arm beats committing to the global winner — and how close a CHEAP heuristic classifier
 * gets to that ceiling.
 *
 * It scores three routers with the same budget-aware discounted grounding@C as the policy:
 *   - global   : every query → the global winner (here hybrid). The baseline to beat.
 *   - heuristic : a zero-LLM classifier picks an arm per query (the shippable router).
 *   - oracle   : every query → its own best arm. The CEILING; unattainable in production
 *                (it peeks at the labels) but it bounds how much routing can ever help.
 *
 * If oracle ≈ global, routing has no headroom on this corpus — report it and stop.
 *
 * Run: bun src/route_eval.ts        (needs the corpus loaded + OLLAMA_* up)
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

import { budgetScore, coverage } from "./grounding.ts";

const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;
const GOLDEN = process.env.GOLDEN_EVAL ?? `${import.meta.dir}/../data/golden_eval.json`;
const SLUG_DUMP = `${import.meta.dir}/../results/route_slugs.json`;
const ARM_DUMP = `${import.meta.dir}/../results/arm_scores.json`; // per-arm grounding + slugs (verify_arch.py)
const K = Number(process.env.POLICY_K ?? "5");
const C = Number(process.env.POLICY_C ?? "3");

interface GoldenQ { q: string; expected_entities: string[]; domain: string }
type Strategy = "keyword" | "vector" | "hybrid";
const strategies: readonly Strategy[] = ["keyword", "vector", "hybrid"];
const GLOBAL: Strategy = "hybrid"; // current global policy winner on the mixed corpus

const golden: GoldenQ[] = JSON.parse(readFileSync(GOLDEN, "utf-8")).questions;

// ── cheap, deterministic query classifier (the shippable router) ─────────────
// Signal: proper-noun lookups (capitalised entity tokens, short query) are exact-term
// territory → keyword's strength; everything else stays on the global hybrid default.
const STOP = new Set(["What", "Who", "Where", "Which", "When", "How", "Why", "Does",
  "Did", "Is", "Are", "The", "In", "Of", "A", "An"]);
function classify(q: string): Strategy {
  const properNouns = (q.match(/\b[A-Z][a-zA-Z]+\b/g) ?? []).filter(w => !STOP.has(w));
  const words = q.split(/\s+/).length;
  if (properNouns.length >= 2 && words <= 9) return "keyword"; // short proper-noun lookup
  return "hybrid";
}

// ── engine bootstrap (identical sequence to policy_eval.ts / the CLI) ────────
const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway, reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { runEval } = await import(`${GB}/core/search/eval.ts`);

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
await reconfigureGatewayWithEngine(engine);
const nPages = (await engine.listPages()).length;

const textCache = new Map<string, string>();
async function sectionText(slug: string): Promise<string> {
  if (textCache.has(slug)) return textCache.get(slug)!;
  const p = await engine.getPage(slug);
  const t = p ? `${p.title}\n${p.compiled_truth}\n${p.timeline}`.toLowerCase() : "";
  textCache.set(slug, t);
  return t;
}

// ── per-arm, per-question discounted grounding@C + top-C slugs ───────────────
const score = {} as Record<Strategy, number[]>;      // score[arm][i] = gDisc for question i
const slugsByArm = {} as Record<Strategy, string[][]>; // slugsByArm[arm][i] = top-C slugs (for the answer A/B)
for (const strategy of strategies) {
  const report = await runEval(
    engine,
    golden.map(g => ({ query: g.q, relevant: [] as string[] })),
    { strategy, expand: false, limit: K },
    K,
  );
  const row: number[] = [];
  const slugs: string[][] = [];
  for (let i = 0; i < golden.length; i++) {
    const topC: string[] = report.queries[i].hits.slice(0, C);
    const ents = golden[i].expected_entities;
    const covs = await Promise.all(topC.map(async s => coverage(await sectionText(s), ents)));
    row.push(budgetScore(covs, C).gDisc);
    slugs.push(topC);
  }
  score[strategy] = row;
  slugsByArm[strategy] = slugs;
}

// ── routers ──────────────────────────────────────────────────────────────────
const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const bestArm = (i: number): Strategy =>
  strategies.reduce((best, s) => (score[s][i] > score[best][i] ? s : best), strategies[0]);

const globalScores    = golden.map((_, i) => score[GLOBAL][i]);
const heuristicPicks  = golden.map(g => classify(g.q));
const heuristicScores = golden.map((_, i) => score[heuristicPicks[i]][i]);
const oracleScores    = golden.map((_, i) => score[bestArm(i)][i]);

// ── report ───────────────────────────────────────────────────────────────────
const pad = (s: string, n: number) => s.padEnd(n);
const f = (x: number) => x.toFixed(3);
console.log(`route_eval: ${golden.length} questions · ${nPages} pages · K=${K} C=${C}\n`);
console.log(pad("#", 3) + pad("dom", 7) + pad("key", 7) + pad("vec", 7) + pad("hyb", 7) +
  pad("best", 9) + pad("heur", 9) + "question");
console.log("-".repeat(86));
golden.forEach((g, i) => {
  const best = bestArm(i);
  const flag = best !== GLOBAL ? " *" : "";              // * = routing could beat global here
  console.log(pad(String(i), 3) + pad(g.domain, 7) +
    pad(f(score.keyword[i]), 7) + pad(f(score.vector[i]), 7) + pad(f(score.hybrid[i]), 7) +
    pad(best + flag, 9) + pad(heuristicPicks[i], 9) + g.q.slice(0, 40));
});
console.log("-".repeat(86));
const wins       = golden.filter((_, i) => bestArm(i) !== GLOBAL).length;
const mGlobal    = mean(globalScores);
const mHeuristic = mean(heuristicScores);
const mOracle    = mean(oracleScores);
console.log(`\nrouter             grounding@${C}   Δ vs global`);
console.log(`global (${GLOBAL})    ${f(mGlobal)}        —`);
console.log(`heuristic          ${f(mHeuristic)}        ${f(mHeuristic - mGlobal)}`);
console.log(`oracle (ceiling)   ${f(mOracle)}        ${f(mOracle - mGlobal)}`);
console.log(`\n${wins}/${golden.length} questions have a non-global best arm (routing headroom).`);

// ── dump per-question slugs for the answer-quality A/B (answer_route_ab.py) ──
const dump = golden.map((g, i) => {
  const best = bestArm(i);
  return {
    q: g.q,
    domain: g.domain,
    best_arm: best,
    global_arm: GLOBAL,
    global_slugs: slugsByArm[GLOBAL][i],
    routed_slugs: slugsByArm[best][i],
  };
});
mkdirSync(dirname(SLUG_DUMP), { recursive: true });
writeFileSync(SLUG_DUMP, JSON.stringify(dump, null, 2) + "\n");
console.log(`wrote per-question slugs → ${SLUG_DUMP}`);

// ── dump per-arm grounding + slugs for architecture verification (verify_arch.py) ──
const armDump = golden.map((g, i) => ({
  q: g.q,
  domain: g.domain,
  grounding: Object.fromEntries(strategies.map(s => [s, score[s][i]])),
  slugs: Object.fromEntries(strategies.map(s => [s, slugsByArm[s][i]])),
}));
writeFileSync(ARM_DUMP, JSON.stringify(armDump, null, 2) + "\n");
console.log(`wrote per-arm grounding+slugs → ${ARM_DUMP}`);

await engine.disconnect?.();
process.exit(0);
```

**Walkthrough:**
- **Design principle - build the ceiling before the classifier.** The oracle loop (`bestArm(i)`) asks "what is the theoretical maximum if routing were perfect?" at zero classifier cost. If oracle equals global hybrid, the ceiling is 0 - a real classifier can only lose (its mis-routes have no headroom to cover them). That single number kills or validates the routing feature before any classifier is written; this is why `route_eval.ts` runs *before* `route_principle_ab.ts`, not after.
- **Single retrieval pass over all three arms, then compare in memory.** The outer `for (const strategy of strategies)` loop calls `runEval` once per arm and accumulates `score[strategy]` and `slugsByArm[strategy]`. All routers (global, heuristic, oracle) are then computed as pure index lookups into that matrix - no second DB round-trip. This keeps the corpus state identical across arms (same embed model, same pages) so the per-question best is a fair comparison.
- **`sectionText` cache avoids O(N × K × arms) DB reads.** Each slug's compiled text is fetched at most once and stored in `textCache`. Without it, the `coverage` calls would hit Postgres for every `(question, arm, rank)` triple - 3 × K × N reads instead of at most N × K unique slugs. The cache is populated lazily inside the arm loop so it also serves subsequent arms that retrieve the same page.
- **The heuristic classifier is deliberately dumb.** Two proper-noun tokens AND query length ≤ 9 words routes to keyword; everything else stays on hybrid. It intentionally captures only the most obvious exact-match queries ("Itochu Marubeni Mitsubishi"-style token lists). Its purpose is not to win - it is to show how much a zero-LLM, zero-cost classifier *loses* relative to the oracle ceiling. When heuristic < global, the classifier is net-negative, which is the key finding on the vector-skewed natural corpus.
- **Two dumps serve two different consumers.** `route_slugs.json` carries `global_slugs` vs `routed_slugs` per question - shaped for `answer_route_ab.py`, which needs exactly two context sets to generate and compare answers. `arm_scores.json` carries all three arms' grounding scores AND slugs per question - shaped for `verify_arch.py` (which pairs grounding with answer-pass across all arm × question cells) and `reader_ab.py` (which fixes retrieval and A/Bs the generator). One retrieval run, two file formats, three downstream consumers - no redundant compute.
- **`process.exit(0)` is load-bearing.** Bun's top-level await leaves open DB connections after `engine.disconnect?.()` returns; without the explicit exit the process would hang. This mirrors `policy_eval.ts` for the same reason.

#### Block E — the reader is the lever, measured (2026-06-07)

Retrieval is solved here (hybrid grounding ~0.93); the open question is the *generation* step — W2.7's 0.96 grounding → 0.25 answer gap, and the "Notes" question that grounds 1.000 yet answers 0/3. So we fixed retrieval (always the winning arm = hybrid, **full `gbrain get` bodies**) and A/B'd the READER STRATEGY against the golden `pass_criteria` (`src/reader_ab.py`; gen = the reader under test, judge = a fixed strong grader so the verdict isn't self-graded):

**When to use:** Reach for `reader_ab.py` when retrieval is already solved (grounding ≥ 0.90) and you want to isolate whether the answer gap comes from the *reader prompt* or from *model capability* - it holds context fixed (always the winning arm) and sweeps four prompt strategies across two generator tiers with a single strong judge.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  ENV["env: GEN / JUDGE<br/>preset or raw override"] --> RESOLVE["_resolve(role)<br/>→ client + model id"]
  RESOLVE --> GEN_CLIENT["gen client<br/>(reader under test)"]
  RESOLVE --> JUDGE_CLIENT["judge client<br/>(fixed strong grader)"]
  ARM_SCORES["results/arm_scores.json<br/>from route_eval.ts"] --> MAIN["main()"]
  MAIN --> BUILD_CTX["build_context(slugs<br/>'hybrid')<br/>full bodies,<br/>snippet-guarded"]
  BUILD_CTX --> READERS
  subgraph READERS ["four reader strategies"]
    R1["plain<br/>one LLM call"]
    R2["authoritative<br/>one LLM call"]
    R3["cite<br/>one LLM call"]
    R4["extract-then-answer<br/>two LLM calls"]
  end
  READERS -->|"answer"| JUDGE["_judge()<br/>Opus grades PASS/FAIL"]
  JUDGE --> PASSES["passes dict<br/>per strategy"]
  PASSES --> TABLE["pass-rate table<br/>+ delta vs plain"]
```
*`reader_ab.py` data flow - retrieval is fixed at the hybrid arm; the four reader strategies are the only variable.*

**Code: `src/reader_ab.py`**

```python
"""reader_ab.py — hold retrieval FIXED, vary the READER; which reader writes better answers?

Retrieval is solved on this corpus (hybrid grounding ~0.93). The leverage is the
generation step — W2.7's 0.96 grounding → 0.25 answer gap, and the "Notes" question that
grounds 1.000 yet answers 0/3. So we fix the context (always the winning arm = hybrid,
full `gbrain get` bodies) and A/B the READER STRATEGY against the same golden pass_criteria:

  - plain          : "answer from the notes" (baseline)
  - authoritative  : frame the notes as AUTHORITATIVE ground truth (memory-os) — don't
                     re-derive, don't hedge
  - extract        : authoritative + extract-then-answer (pull the answer-bearing span
                     first, then compose)
  - cite           : authoritative + require a source citation per claim

Generator = the reader UNDER TEST; judge = a fixed STRONG grader (so the verdict isn't the
generator grading itself). Each role is a NAMED MODEL PRESET — switch with no code change:

  GEN=14b JUDGE=opus uv run python src/reader_ab.py     # weak gen, strong judge
  GEN=haiku JUDGE=opus uv run python src/reader_ab.py   # mid gen, strong judge

Presets resolve endpoint+key+model (see _PROFILES). Raw escape hatch: set <ROLE>_MODEL
(+ optional <ROLE>_BASE_URL / <ROLE>_API_KEY) to bypass the registry. Both roles read .env
for the oMLX key. Context comes from build_context() → full bodies, snippet-guarded.

Inputs: results/arm_scores.json (from `bun src/route_eval.ts`) + the W2.7 ground truth.
"""
from __future__ import annotations

import json
import os
import pathlib

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from answer_route_ab import (
    LLMUnavailable,
    _JUDGE_TMPL,
    _pass_criteria_by_q,
    _resilient,
    build_context,
)

_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")  # for the oMLX key used by the local-model presets

_ARM_SCORES = _ROOT / "results" / "arm_scores.json"
_FIXED_ARM = "hybrid"  # retrieval held fixed at the corpus-winning arm

# ── model registry: name → (base_url, api_key, model id). Add a line to add a model. ──
_VIBE = ("http://localhost:8317/v1", os.getenv("OPENROUTER_API_KEY", "vibeproxy"))   # cloud Claude
_OMLX = ("http://localhost:8000/v1", os.getenv("LLM_API_KEY", "") or os.getenv("OLLAMA_API_KEY", ""))  # local MLX
_PROFILES: dict[str, tuple[str, str, str]] = {
    "haiku": (*_VIBE, "claude-haiku-4-5-20251001"),
    "opus": (*_VIBE, "claude-opus-4-5-20251101"),
    "14b": (*_OMLX, "Qwen2.5-Coder-14B-Instruct-MLX-4bit"),
    "qwen": (*_OMLX, "Qwen2.5-Coder-14B-Instruct-MLX-4bit"),
}


def _resolve(role: str, default_profile: str) -> tuple[OpenAI, str, str]:
    """Resolve a role (GEN/JUDGE) to (client, model id, label). A named preset via
    e.g. GEN=14b; or a raw override via <ROLE>_MODEL (+ optional <ROLE>_BASE_URL/API_KEY)."""
    if os.getenv(f"{role}_MODEL"):  # raw escape hatch
        base = os.getenv(f"{role}_BASE_URL", _VIBE[0])
        key = os.getenv(f"{role}_API_KEY", _VIBE[1])
        model = os.environ[f"{role}_MODEL"]
        return OpenAI(base_url=base, api_key=key), model, model
    name = os.getenv(role, default_profile)
    if name not in _PROFILES:
        raise SystemExit(f"unknown {role}={name!r}; choose from {sorted(_PROFILES)} "
                         f"or set {role}_MODEL for a raw override")
    base, key, model = _PROFILES[name]
    return OpenAI(base_url=base, api_key=key), model, name


# ── reader prompt strategies ─────────────────────────────────────────────────
_PLAIN = (
    "Using ONLY the notes below, answer the question. If a fact is not in the notes, "
    "say you don't have it.\n\nNOTES:\n{ctx}\n\nQUESTION: {q}"
)
_AUTHORITATIVE = (
    "The NOTES below are AUTHORITATIVE ground truth — trust them, never contradict them, "
    "do not re-derive or re-fetch. Answer concisely from the notes. If the answer is not "
    "in the notes, say 'insufficient context'.\n\nNOTES (authoritative):\n{ctx}\n\nQUESTION: {q}"
)
_CITE = _AUTHORITATIVE + "\n\nCite the source section in [brackets] for each factual claim."
_EXTRACT_STEP = (
    "From the notes below, copy VERBATIM the sentence(s) that contain the answer to the "
    "question. If none do, reply exactly NONE.\n\nNOTES:\n{ctx}\n\nQUESTION: {q}"
)
_ANSWER_FROM_SPANS = (
    "These extracted facts are AUTHORITATIVE. Answer the question concisely from them; "
    "if they are insufficient, say 'insufficient context'.\n\nFACTS:\n{spans}\n\nQUESTION: {q}"
)


def _gen(client: OpenAI, messages: list[ChatCompletionMessageParam], model: str) -> str:
    r = client.chat.completions.create(model=model, messages=messages, temperature=0)
    return (r.choices[0].message.content or "").strip()


def _one(client: OpenAI, prompt: str, model: str) -> str:
    msg: list[ChatCompletionMessageParam] = [{"role": "user", "content": prompt}]
    return _resilient(_gen, client, msg, model)


def read_plain(client: OpenAI, ctx: str, q: str, model: str) -> str:
    return _one(client, _PLAIN.format(ctx=ctx, q=q), model)


def read_authoritative(client: OpenAI, ctx: str, q: str, model: str) -> str:
    return _one(client, _AUTHORITATIVE.format(ctx=ctx, q=q), model)


def read_cite(client: OpenAI, ctx: str, q: str, model: str) -> str:
    return _one(client, _CITE.format(ctx=ctx, q=q), model)


def read_extract(client: OpenAI, ctx: str, q: str, model: str) -> str:
    spans = _one(client, _EXTRACT_STEP.format(ctx=ctx, q=q), model)
    return _one(client, _ANSWER_FROM_SPANS.format(spans=spans, q=q), model)


_READERS = {
    "plain": read_plain,
    "authoritative": read_authoritative,
    "extract": read_extract,
    "cite": read_cite,
}
_BASELINE = "plain"


def _judge(client: OpenAI, answer: str, criteria: str, model: str) -> bool:
    verdict = _one(client, _JUDGE_TMPL.format(criteria=criteria, answer=answer), model)
    return verdict.strip().upper().startswith("PASS")


def main() -> None:
    dump = json.loads(_ARM_SCORES.read_text())
    criteria_by_q = _pass_criteria_by_q()
    gen_client, gen_model, gen_name = _resolve("GEN", "haiku")        # the reader under test
    judge_client, judge_model, judge_name = _resolve("JUDGE", "opus")  # fixed strong grader
    print(f"reader_ab: retrieval FIXED at '{_FIXED_ARM}' · gen={gen_name} ({gen_model}) "
          f"· judge={judge_name} ({judge_model})\n")

    passes: dict[str, list[float]] = {name: [] for name in _READERS}
    for item in dump:
        q = item["q"].strip()
        criteria = criteria_by_q.get(q)
        if criteria is None:
            continue  # entity questions have no rubric — skip
        ctx = build_context(item["slugs"][_FIXED_ARM])   # full bodies, snippet-guarded
        marks: list[str] = []
        for name, reader in _READERS.items():
            try:
                ok = _judge(judge_client, reader(gen_client, ctx, q, gen_model), criteria, judge_model)
            except LLMUnavailable as exc:
                marks.append(f"{name}=skip")
                print(f"  [skip] {name} on {q[:40]} ({exc})")
                continue
            passes[name].append(1.0 if ok else 0.0)
            marks.append(f"{name}={'P' if ok else 'F'}")
        print(f"  {' '.join(marks):42s} {q[:44]}")

    print(f"\nreader strategy     pass-rate   Δ vs {_BASELINE}")
    base = sum(passes[_BASELINE]) / len(passes[_BASELINE]) if passes[_BASELINE] else 0.0
    for name in _READERS:
        vals = passes[name]
        rate = sum(vals) / len(vals) if vals else 0.0
        delta = "—" if name == _BASELINE else f"{rate - base:+.3f}"
        print(f"  {name:16s}  {rate:.3f}      {delta}   (n={len(vals)})")
    best = max(_READERS, key=lambda n: (sum(passes[n]) / len(passes[n])) if passes[n] else 0.0)
    print(f"\n  best reader = {best}")


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **Design principle - hold one variable fixed.** Retrieval is already the corpus-winning arm (hybrid, grounding ~0.93); varying it here would confound the reader signal. `_FIXED_ARM = "hybrid"` pins context assembly to a single known-good configuration so every pass-rate difference is attributable to the prompt strategy alone.
- **Two-role model registry (`_PROFILES` + `_resolve`).** Generator and judge are independent named presets resolved from environment variables (`GEN=haiku`, `JUDGE=opus`). The raw escape hatch (`<ROLE>_MODEL` / `<ROLE>_BASE_URL`) means any OpenAI-compatible endpoint drops in with no code change - the separation of `gen_client` and `judge_client` is intentional: self-grading (generator judging itself) inflates scores.
- **Four prompt strategies as first-class functions.** Each reader (`read_plain`, `read_authoritative`, `read_cite`, `read_extract`) wraps the same `_one()` helper; `_READERS` is a dict so the main loop treats them uniformly and the table prints in insertion order. `read_extract` is the only two-call reader - it first extracts the answer-bearing span verbatim, then composes from that span - deliberately separated to test whether explicit extraction helps or just adds a lossy step.
- **`build_context` from `answer_route_ab`** fetches full `gbrain get` bodies for the slugs pre-dumped by `route_eval.ts` into `arm_scores.json`. Importing rather than re-implementing this keeps the context assembly identical to the routing A/B (no calibration drift between what was benchmarked and what is being read here).
- **Pass-rate table + delta vs baseline.** The final summary prints each strategy's pass-rate and its signed delta vs `plain` - the delta is the whole point: a positive delta would justify adopting the strategy; the measured result showed all deltas ≤ 0 (no prompt technique beat plain), which is the finding.

**Two generator tiers, judge = Opus 4.5, fixed hybrid context:**

| reader strategy | Haiku 4.5 (full ctx) | local 14B (ctx-capped) |
|---|---|---|
| **plain** ("answer from the notes") | **0.917** | **0.500** |
| authoritative (notes are ground truth) | 0.917 (+0.000) | 0.417 (−0.083) |
| extract-then-answer | 0.417 (−0.500) | 0.083 (−0.417) |
| cite (source per claim) | 0.917 (+0.000) | 0.417 (−0.083) |

The four readers differ ONLY in the prompt wrapped around the same `{ctx}` (full hybrid bodies) and `{q}` (the question) — verbatim from `src/reader_ab.py`:

```text
plain:
  "Using ONLY the notes below, answer the question. If a fact is not in the notes, say you don't have it.

   NOTES:
   {ctx}

   QUESTION: {q}"

authoritative:
  "The NOTES below are AUTHORITATIVE ground truth — trust them, never contradict them, do not re-derive or re-fetch. Answer concisely from the notes. If the answer is not in the notes, say 'insufficient context'.

   NOTES (authoritative):
   {ctx}

   QUESTION: {q}"

cite:
  <the authoritative prompt above>
  + "\n\nCite the source section in [brackets] for each factual claim."

extract-then-answer  (TWO LLM calls):
  step 1 — extract:
    "From the notes below, copy VERBATIM the sentence(s) that contain the answer to the question. If none do, reply exactly NONE.

     NOTES:
     {ctx}

     QUESTION: {q}"
  step 2 — answer from the extracted spans:
    "These extracted facts are AUTHORITATIVE. Answer the question concisely from them;
     if they are insufficient, say 'insufficient context'.

     FACTS:
     {spans}      ← step-1 output

     QUESTION: {q}"

judge  (fixed, Opus 4.5 — grades every reader's answer identically):
  "You are grading a candidate answer against a rubric. Reply with EXACTLY one word:
   PASS or FAIL.

   RUBRIC (what makes the answer correct):
   {criteria}    ← the question's pass_criteria from eval_ground_truth.json

   CANDIDATE ANSWER:
   {answer}

   Verdict (PASS or FAIL):"
```

**`plain` wins on both tiers; no prompt technique beats it, and `extract`-then-answer regresses hard on both.** Four reads:
- **No headroom on a capable model.** Haiku ceilings at 0.917, *identical to Opus* — the model
  + good context already answer 11/12, so there is nothing for a prompt technique to add. The quality came from *assembly + capability* (hybrid + full bodies + a capable model), not wording — 0.917 vs W2.7's 0.25 on the same 10-K is that pipeline, not a clever prompt.
- **Technique does NOT substitute for capability.** The weak 14B just scores lower (0.500), and the "smart" framings (`authoritative`/`cite`) even slightly *hurt* (−0.083) while plain stays best. You can't prompt a weak model up to a strong one's answers.
- **`extract` is a lossy two-step** on both tiers (−0.500 Haiku, −0.417 14B): extracting "the answer-bearing sentence" first lets the model drop/mangle the span, so the answer step gets *worse* material than the full context. Added a step, added a failure point (Pattern 30).
- **The "Notes" question fails on every reader and model *for GBrain* — but W2.7 answers it.** Grounded 1.000 (the chunks contain `Item 8`/`K-75`/`Notes to Consolidated` as buried substrings), yet GBrain's flat-body chunks never state the *location* in answerable form, so no reader prompt recovers it — it's a **retrieval-representation** gap, not a reader one. The answer is in the document: W2.7's structure/page-aware index reads "pages 99-141" straight from section metadata and passes (see comparison below). So this isn't a dead-end question — it's the **structural / "where-is-X-located" class** where flat-chunk hybrid loses to a structure-aware index. Reader technique is the wrong lever here; the right one is a structural index.

**A capacity finding fell out of it.** The *first* 14B attempt (full bodies, no cap) **crashed the oMLX server after one question**: a single question's five generations over the ~70K-token full-body context exhausted it. Full-body reading of large sections demands a large-context model; bounding the context (`MAX_BODY_CHARS=8000 GEN=14b uv run python src/reader_ab.py`) let it run, at the cost of truncating sections (hence the lower 14B absolute rates). The snippet-regression guard (`build_context`) confirmed full bodies throughout (`body chars=[36252, 54411, 190984]`).

**Verdict:** keep the `plain` reader; spend reader effort on **assembly** (full bodies, tight `C`, a capable large-context model), not prompt elaboration — the gains live upstream of the prompt.

#### Comparison to W2.7 (same 10-K, different axis)

W2.7 scored **answer quality** across **index types** (Vector / GraphRAG / tree-index); this lab scores **retrieval grounding** across **arms** (keyword / vector / hybrid). Not numerically comparable — compare which method wins which query *class*:

| | measured | factoid winner | note |
|---|---|---|---|
| W2.7 three-way | answer quality (LLM-judge) | **Vector** 0.50 | aggregate Graph 0.48 / Tree 0.44 / Vector 0.25 |
| this lab (golden, real Q) | retrieval grounding@5 | **vector/hybrid** 0.96 | keyword 0.19 |

Shapes converge: dense vector is strongest at 10-K *factoid retrieval* in both. And grounding 0.96 ≫ W2.7's vector answer-judge 0.25 ⇒ in W2.7 the bottleneck was **generation, not retrieval** — GBrain surfaces the answer-bearing section ~96% of the time; turning that into a correct answer is the separate, harder step.

> **Path A script - `src/bench_w27_questions.ts`.** The "real Q" `grounding@5` row above (`vector/hybrid 0.96`, `keyword 0.19`) is produced by this script: it runs W2.7's own labeled financial questions (`{q, expected_entities}`) through GBrain's three arms over the 10-K and scores **substring grounding@K / answerable@K** - the *real-question* measurement that refuted the known-item proxy (Bad-Case Entry 20). Call it **Path A** (real W2.7 questions → GBrain retrieval); `load_brk_corpus.py` below is **Path B** (load the 10-K so the auto-eval loop can self-select an arm on it). Path A is *why* the policy moved off `keyword` to `vector/hybrid` on real financial queries, and its question set is the seed of `data/golden_eval.json` (the `tenk` domain) that `policy_eval.ts` now scores every ingest.

`bench_w27_questions.ts` loads W2.7's human-authored financial questions, boots the same GBrain engine used in production, and for each of the three retrieval arms fetches the top-K pages, then scores entity coverage as substring grounding@K and answerable@K. It is the "honest" replacement for known-item proxy queries.

**When to use:** reach for this script when you want to measure retrieval quality on the *same question set* W2.7 used and need a grounding-level (not answer-level) signal - i.e. does GBrain surface answer-bearing pages at all, regardless of whether the reader model can express the answer? Use `eval_brk16.py` instead when you need answer-pass-rate on the 16 canonical questions.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  EV1["eval_v2.json<br/>{q, expected_entities}"] --> DEDUP
  EV2["eval.json<br/>{q, expected_entities}"] --> DEDUP
  DEDUP["dedup by q<br/>N unique questions"] --> QRELS["qrels list<br/>query strings only"]
  BOOT["GBrain engine<br/>loadConfig · createEngine<br/>connectWithRetry"] --> GATEWAY["configureGateway<br/>buildGatewayConfig"]
  GATEWAY --> ENGINE[("engine<br/>hybrid-indexed")]
  QRELS --> LOOP
  ENGINE --> LOOP
  LOOP{"for each strategy<br/>keyword / vector / hybrid"}
  LOOP -->|"runEval (K hits)"| HITS["ranked slug list<br/>per question"]
  HITS --> COVER["sectionText + coverage<br/>best top-K entity fraction"]
  COVER -->|"grounding@K<br/>answerable@K"| TABLE["console table<br/>strategy · grounding · answerable"]
```
*`bench_w27_questions.ts` data flow - real W2.7 questions deduped from two eval files, then run through each GBrain arm; page bodies fetched lazily via `sectionText` cache and scored by substring entity coverage.*

**Code - `src/bench_w27_questions.ts`:**

```typescript
/**
 * bench_w27_questions.ts — the REAL W2.7 comparison (Path A, honest version).
 *
 * Runs W2.7's own labeled financial questions (data/eval_v2.json + eval.json:
 * `{q, expected_entities}`) through GBrain retrieval over the brk 10-K, and scores
 * by whether the RETRIEVED sections actually contain the expected entities
 * (substring grounding@K). This replaces the known-item PROXY queries with real
 * human questions.
 *
 * Metric note (kept honest): W2.7's three-way scored ANSWER quality across INDEX
 * TYPES (vector / GraphRAG / tree-index). This scores RETRIEVAL grounding across
 * GBrain's ARMS (keyword / vector / hybrid). Same corpus + same questions, but a
 * retrieval metric, not an answer-generation metric — so compare the SHAPE of the
 * findings (which method wins which query class), not the absolute numbers.
 *
 *   grounding@K   = mean over questions of the BEST top-K section's entity coverage
 *                   (fraction of expected_entities found as substrings in it)
 *   answerable@K  = fraction of questions where some top-K section covers ALL entities
 *
 * Run: bun src/bench_w27_questions.ts   (needs gbrain_brk loaded + OLLAMA_* up)
 */
import { readFileSync } from "node:fs";

const GB = process.env.GBRAIN_SRC ?? `${import.meta.dir}/../../gbrain/src`;
const EVAL_DIR = "/Users/yuxinliu/code/agent-prep/lab-02-7-pageindex/data";
const K = Number(process.env.BENCH_K ?? "5");

interface W27Q { q: string; expected_entities: string[]; type?: string }
type Strategy = "keyword" | "vector" | "hybrid";

// ── load + dedup W2.7's labeled questions ───────────────────────────────────
const raw: W27Q[] = ["eval_v2.json", "eval.json"].flatMap(f =>
  JSON.parse(readFileSync(`${EVAL_DIR}/${f}`, "utf-8")));
const seen = new Set<string>();
const questions = raw.filter(q => q.q && q.expected_entities?.length &&
  !seen.has(q.q) && (seen.add(q.q), true));

// ── engine bootstrap (same sequence as auto_eval.ts / the CLI) ──────────────
const { loadConfig, toEngineConfig } = await import(`${GB}/core/config.ts`);
const { createEngine } = await import(`${GB}/core/engine-factory.ts`);
const { connectWithRetry } = await import(`${GB}/core/db.ts`);
const { configureGateway, reconfigureGatewayWithEngine } = await import(`${GB}/core/ai/gateway.ts`);
const { buildGatewayConfig } = await import(`${GB}/core/ai/build-gateway-config.ts`);
const { runEval } = await import(`${GB}/core/search/eval.ts`);

const config = loadConfig();
configureGateway(buildGatewayConfig(config));
const engine = await createEngine(toEngineConfig(config));
await connectWithRetry(engine, toEngineConfig(config), { noRetry: true });
await reconfigureGatewayWithEngine(engine);

// section text cache (slug → "title + compiled_truth + timeline", lowercased)
const textCache = new Map<string, string>();
async function sectionText(slug: string): Promise<string> {
  if (textCache.has(slug)) return textCache.get(slug)!;
  const p = await engine.getPage(slug);
  const t = p ? `${p.title}\n${p.compiled_truth}\n${p.timeline}`.toLowerCase() : "";
  textCache.set(slug, t);
  return t;
}

// fraction of expected_entities present as substrings in a section
function coverage(text: string, entities: string[]): number {
  const hit = entities.filter(e => text.includes(e.toLowerCase())).length;
  return entities.length ? hit / entities.length : 0;
}

const strategies: readonly Strategy[] = ["keyword", "vector", "hybrid"];
const qrels = questions.map(q => ({ query: q.q, relevant: [] as string[] }));

const summary: Record<Strategy, { grounding: number; answerable: number }> =
  {} as Record<Strategy, { grounding: number; answerable: number }>;

for (const strategy of strategies) {
  // reuse runEval purely to get ranked hits per query (metrics ignored — no gold slug)
  const report = await runEval(engine, qrels, { strategy, expand: false, limit: K }, K);
  let groundingSum = 0;
  let answerable = 0;
  for (let i = 0; i < questions.length; i++) {
    const hits: string[] = report.queries[i].hits.slice(0, K);
    const ents = questions[i].expected_entities.map(e => e.toLowerCase());
    let best = 0;
    for (const slug of hits) best = Math.max(best, coverage(await sectionText(slug), ents));
    groundingSum += best;
    if (best === 1) answerable++;
  }
  summary[strategy] = {
    grounding: groundingSum / questions.length,
    answerable: answerable / questions.length,
  };
}

const pad = (s: string, n: number) => s.padEnd(n);
console.log(`W2.7 real-question retrieval over brk 10-K — ${questions.length} questions · K=${K}\n`);
console.log(pad("strategy", 12) + pad(`grounding@${K}`, 15) + pad(`answerable@${K}`, 15));
console.log("-".repeat(42));
for (const s of strategies) {
  console.log(pad(s, 12) + pad(summary[s].grounding.toFixed(3), 15) + pad(summary[s].answerable.toFixed(3), 15));
}
console.log("\nmetric: retrieval grounding (do retrieved sections CONTAIN the expected entities), " +
  "NOT answer quality. Compare the winner SHAPE vs W2.7's three-way, not absolute numbers.");

await engine.disconnect?.();
process.exit(0);
```

**Walkthrough:**

- **Design principle first - grounding@K not answer quality.** The script deliberately scores whether retrieved sections *contain* the expected entity strings as substrings, not whether a reader model produces the right answer. That is a weaker, cheaper, LLM-free signal that answers a prior question: does GBrain even surface the answer-bearing page? If grounding is low no reader prompt will save you; if grounding is high the bottleneck shifts to generation. This is why the script exists as a standalone step before `eval_brk16.py`.
- **Block 1 - load + dedup.** Both `eval_v2.json` and `eval.json` are read and merged, then deduped by the `q` string using a `Set`. The one-liner `!seen.has(q.q) && (seen.add(q.q), true)` is intentionally compact - it exploits the `&&` short-circuit so the side-effecting `seen.add` only fires when the predicate passes, avoiding a separate filter+forEach pair.
- **Block 2 - engine bootstrap.** The import sequence (`loadConfig` → `createEngine` → `connectWithRetry` → `configureGateway`) mirrors `auto_eval.ts` and the GBrain CLI exactly. `{ noRetry: true }` is deliberate - a benchmark run should fail fast if the DB is not up rather than silently retrying and skewing timing.
- **Block 3 - `sectionText` cache.** Page bodies are fetched lazily and memoized. The concatenation `title + compiled_truth + timeline` covers all three GBrain fields that hold entity-bearing text; lowercasing once at read time means every downstream `includes()` call is O(1) string search without repeated `.toLowerCase()` allocations.
- **Block 4 - `runEval` reuse (important gotcha).** `runEval` was designed to score recall against gold slugs; here there are no gold slugs - `relevant: []` for every query. The function is called purely to get ranked hit lists per query. The internal MRR/nDCG scores it computes are discarded; only `report.queries[i].hits` is used. This is intentional reuse of existing plumbing rather than writing a raw search loop.
- **Block 5 - grounding accumulation.** For each question the script takes the *best* coverage across the top-K hits (not average), because a retriever that surfaces the right page anywhere in K is doing its job. `answerable` counts questions where best coverage reaches 1.0 - i.e. every expected entity appears in at least one retrieved section.
- **Block 6 - console table.** `padEnd` is used instead of a library formatter to keep the script dependency-free. The closing disclaimer line - "NOT answer quality" - is printed intentionally to prevent copy-pasting the numbers into a context where answer quality is the claim.

##### Results comparison — answer quality on the same 10-K (and why it's a wash, but GBrain's architecture still fits better)

Now that `reader_ab.py` scores ANSWER pass-rate against the same `pass_criteria` W2.7 used, the two are finally on one axis:

| system | retrieval architecture | per-document build | answer pass-rate (same 10-K `pass_criteria`) |
|---|---|---|---|
| W2.7 three-way (baseline) | Vector / GraphRAG / tree-index — **3 specialized backends** | Graph 71.9 min (Neo4j extract); Tree LLM multipass | Vector 0.25 · Graph 0.48 · Tree 0.44 (LLM-judge) |
| W2.7 optimized (`ab_v2`, reader prompt-dev) | same backends, tuned reader | + reader optimization | **gt_pass 1.000** (16/16; judge 0.818) |
| W3.5.96 GBrain | **hybrid** (BM25 + dense, RRF) — **one arm** | deterministic chunk + embed; **no LLM build, no per-query nav** | **gt_pass 0.917** (11/12 in-doc; Opus judge) |

**Read it honestly — the score is a wash, not a GBrain win.** W2.7's *optimized* config edges GBrain on raw pass-rate (1.000 vs 0.917), partly on an easier mix (its 16 include 4 out-of-document refusals that tree/graph nail) and a different judge model — not a controlled head-to-head. And the headline gap people quote — GBrain 0.92 vs W2.7 *baseline* 0.25–0.48 — is mostly the **reader** (full bodies + a capable model), not the retrieval architecture: W2.7 closed that same gap to 1.0 once *it* tuned its reader. Both labs confirm the chapter's thesis — *generation is the lever* — from opposite directions.

**GBrain's one missed question is the honest counter-evidence.** GBrain's single in-document failure — *"Where are the Notes to Consolidated Financial Statements located?"* — is one **W2.7 answers** (*"pages 99-141"*, from page-range metadata). GBrain grounds it 1.000 (the chunks contain `Item 8`) but its flat-body chunks don't *state the location*, so the reader can't answer. That's a **structural / location / citation** question — and structure-aware indexes (W2.7's tree/page-index, its GraphRAG) genuinely beat flat-chunk hybrid on that class. So GBrain's hybrid is **not** "one arm covers everything": it owns factoid + exact-term, and loses the structural class.

**Where GBrain's architecture IS the better fit: economy and generality, not universal accuracy.** W2.7 needed **three specialized backends**, each winning one query class (Vector→factoid, Graph→citation, Tree→synthesis) and therefore a **router** to pick among them — plus expensive per-document construction (Graph's ~72-minute Neo4j extract; Tree's LLM multipass build). GBrain reaches comparable answer quality with **one deterministic pipeline** — chunk + embed + hybrid-RRF (keyword catches `Item 1C` / dollar figures, vector catches semantics), zero per-document LLM construction, self-tuning on drift, generalizing to a mixed corpus. The trade is explicit: GBrain gives up the structural-question edge that W2.7's heavier, structure-aware backends buy. So GBrain is the more suitable architecture for *most* document retrieval **not because it scores higher** (it doesn't) **but because it reaches comparable quality with cheaper, general, deterministic machinery** — and you reach for a structure-aware index only when location/citation questions dominate.

##### The fix — PageIndex + GBrain combined ingest (closes the structural gap, measured)

The structural-class loss isn't a law — it's a **dropped column at ingest**. PageIndex's `build_tree.py` already extracts per-section page ranges + hierarchy into `tree.json`; the flat loader just discarded them. So the combined design keeps both halves: **PageIndex's structure (built once) + GBrain's hybrid retrieval (cheap, every query), with no per-query tree navigation.**

**When to use:** reach for `load_brk_corpus.py` when you want to benchmark keyword vs vector vs hybrid retrieval on a dense, exact-term-heavy corpus (10-K financials, legal docs, spec sheets) - use `ingest_agent.py` instead when the corpus is unstructured text that needs LLM extraction and graph reconciliation to become page-shaped.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  PDF["brk-2023-ar.pdf<br/>152 pages"] -->|build_tree.py| TREE[("tree.json<br/>title · pages<br/>hierarchy")]
  PDF -->|_brk_corpus.py| RAW["brk_corpus.json<br/>id · title · text"]
  TREE -.->|join by title| ENR
  RAW --> ENR["load_brk_corpus.py<br/>+ Location header<br/>+ frontmatter<br/>item · pages · src"]
  ENR -->|gbrain put + embed| BRAIN["GBrain pages<br/>body has location<br/>hybrid-indexed"]
  BRAIN -->|hybrid retrieve| ANS["reader sees<br/>Item 8 · pp 99-147<br/>answers location"]
```

`load_brk_corpus.py` joins `tree.json` **by title** (the on-disk ids had drifted off-by-one — joining by `node_id` wrote *wrong* locations; titles are stable) and prepends a `**Location:**` breadcrumb to each section's **body** — the load-bearing choice, since GBrain indexes title+body+timeline, so a location *in the body* is retrievable and injected, whereas an unknown frontmatter key is not. The Notes section now carries: `**Location:** Item 8 — Notes to Consolidated Financial Statements · pages 99-147 · source: …`.

**Measured on all 16 W2.7 questions (GBrain hybrid retrieval, Opus reader + judge, `src/eval_brk16.py`):**

| ingest | gt_pass | the "Notes located?" question |
|---|---|---|
| flat (`{id,title,text}`) | 15/16 = 0.938 | **FAIL** (grounds 1.000, but body has no locational statement) |
| **PageIndex-enriched** | **16/16 = 1.000** | **PASS** (reads `Item 8 · pages 99-147` from the Location line) |

The single structural failure flipped to pass, **zero regressions** on the other 15 — and GBrain now matches W2.7's *optimized* 16/16, but with the cheaper architecture (deterministic hybrid + static structural metadata, no per-query tree-walk). Honest edges: `build_tree.py` is a one-time LLM pass (the only document-specific LLM step); `tree.json`'s page ranges are slightly noisy (some single-page), but the `Item N` inheritance is the reliable signal and is what the rubric rewards; and this is the structural class only — factoid/semantic never needed it.

> **Where the scripts live** (this pipeline spans two labs):
> - `build_tree.py`, `_brk_corpus.py` — **W2.7's PageIndex lab**, `~/code/agent-prep/lab-02-7-pageindex/src/`. Artifacts they write: `tree.json`, `brk_corpus.json` in that lab's `data/`.
> - `load_brk_corpus.py` (the tree→GBrain join), `eval_brk16.py` (the 16-question harness) — **this lab**, `~/code/agent-prep/lab-03-5-96-gbrain/src/`.
> - `eval_ground_truth.json` (the 16 questions + `pass_criteria`) — `lab-02-7-pageindex/data/`.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  BRK[(brk_corpus.json<br/>flat sections<br/>id · title · text)] --> J[join on section id]
  TREE[(tree.json<br/>PageIndex hierarchy<br/>+ page ranges)] --> J
  J --> LOC[add Location breadcrumb<br/>Item 8 · pages 99-147]
  LOC --> PG[put_page · deterministic<br/>slug = sections/id<br/>no LLM · no reconcile]
  PG --> EMB[embed --stale]
  EMB --> AE[run_auto_eval<br/>keyword vs vector vs hybrid]
```
*`load_brk_corpus.py` data flow. The 10-K sections are already page-shaped, so this is a deterministic load (no LLM extraction, no graph reconcile - we test retrieval, not wiring). Joining the PageIndex `tree.json` in writes a `**Location:**` breadcrumb into each page body, which is what makes structural "where-is-X" questions answerable without per-query tree navigation. It ends by calling the same `run_auto_eval()` - the loop, pointed at a different corpus.*

**Code — the tree→GBrain join (full source `src/load_brk_corpus.py`):** the `flatten_tree` +
title-join + `**Location:**` breadcrumb is the combined-solution core.

```python
"""W3.5.96 Path B — load the W2.7 Berkshire 10-K corpus into GBrain as a richer,
EXACT-TERM-HEAVY test corpus for the auto-eval harness.

WHY this corpus: the 19-page entity brain is semantic-heavy, so pure vector wins
and RRF adds nothing (Phase 6). A 10-K is the opposite shape — dense with dollar
figures, segment names, subsidiaries, "Scorecard", "operating earnings" — exactly
where the KEYWORD arm earns its weight and hybrid-RRF should win. Loading it lets
`auto_eval.ts` test that hypothesis directly.

The W2.7 sections (`brk_corpus.json`) are ALREADY page-shaped — `{id, title, text}` — so this is a DETERMINISTIC load (slug = sections/<id>), no LLM extraction and no graph reconcile (we're testing retrieval, not wiring). After loading we embed, then the existing `run_auto_eval()` measures keyword vs vector vs hybrid over them.

Run: python src/load_brk_corpus.py     (needs GBRAIN_DATABASE_URL + OLLAMA_* up)
Env: BRK_CORPUS=<path>  SLUG_PREFIX=sections  AUTO_EVAL=1
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess

from ingest_agent import _GBRAIN, _server_env, run_auto_eval

_DEFAULT_CORPUS = pathlib.Path(os.path.expanduser(
    "~/code/agent-prep/lab-02-7-pageindex/data/brk_corpus.json"))
# PageIndex tree (built by lab-02-7 build_tree.py) carries the STRUCTURE the flat
# brk_corpus.json drops: per-section page ranges + hierarchy. Joining it in is the
# "PageIndex + GBrain" combined ingest — it makes structural/"where-is-X" questions
# answerable from the page itself, with no per-query tree navigation.
_DEFAULT_TREE = pathlib.Path(os.path.expanduser(
    "~/code/agent-prep/lab-02-7-pageindex/data/tree.json"))
_SLUG_PREFIX = os.getenv("SLUG_PREFIX", "sections")
_ITEM_RE = re.compile(r"\bItem\s+\d+[A-Z]?\b")


def _clean_title(raw: str, fallback: str) -> str:
    """The W2.7 titles are breadcrumbs ("Berkshire ... Annual Report > Chairman's
    Letter"). The shared prefix repeats across all 44 sections, so using the whole
    breadcrumb makes keyword drown in boilerplate. Keep only the distinctive TAIL
    after the last '>' ("Chairman's Letter") as the page title / exact probe."""
    tail = raw.split(">")[-1].strip() if raw else ""
    return tail or fallback


def flatten_tree(node: dict, parent_title: str = "", inherited_item: str = "",
                 out: dict | None = None) -> dict:
    """node_id → {title, start_page, end_page, parent, item}. `item` is inherited from the nearest ancestor whose title matches `Item N` (so a sub-section of Item 8 still knows it's in Item 8). Used to enrich each GBrain page with its document location."""
    if out is None:
        out = {}
    title = str(node.get("title", ""))
    m = _ITEM_RE.search(title)
    item = m.group(0) if m else inherited_item
    nid = str(node.get("node_id", "")).strip()
    if nid:
        out[nid] = {"title": title, "start_page": node.get("start_page"),
                    "end_page": node.get("end_page"), "parent": parent_title, "item": item}
    for child in node.get("nodes", []):
        flatten_tree(child, title, item, out)
    return out


def build_pages(corpus: list[dict], prefix: str = _SLUG_PREFIX,
                tree_meta: dict | None = None, source: str = "") -> list[tuple[str, str]]:
    """Pure transform: W2.7 sections → (slug, GBrain-page-content) pairs. Each section becomes a markdown page with YAML frontmatter under `<prefix>/<id>`. The frontmatter `title:` is AUTHORITATIVE — `gbrain put` titles from frontmatter, NOT from the `# heading` (that seam is why a slug-only write gets titled "Brk 0002").

    PageIndex-enriched (when `tree_meta` is supplied): frontmatter gains `source` / `item` / `pages` / `parent`, AND a `**Location:**` breadcrumb is prepended to the BODY. The body line is the load-bearing bit — GBrain indexes title+body+timeline, so a location *in the body* is retrievable (keyword + vector) and injected into the reader's context, whereas unknown frontmatter keys are not. That is what makes "where are the Notes located?" answerable. Sections with no id or empty text are skipped.
    """
    pages: list[tuple[str, str]] = []
    tree_meta = tree_meta or {}
    for sec in corpus:
        sid = str(sec.get("id", "")).strip()
        text = str(sec.get("text", "")).strip()
        if not sid or not text:
            continue
        title = _clean_title(str(sec.get("title", "")), sid)
        esc = title.replace('"', '\\"')
        slug = f"{prefix}/{sid}"
        # Join by TITLE, not node_id: the on-disk brk_corpus.json and tree.json can carry
        # drifted node_ids (regenerated independently), but section titles are stable.
        meta = tree_meta.get(title, {})

        fm = [f'title: "{esc}"']
        loc = ""
        if source:
            fm.append(f'source: "{source}"')
        if meta.get("item"):
            fm.append(f'item: "{meta["item"]}"')
        if meta.get("parent"):
            fm.append(f'parent: "{_clean_title(meta["parent"], "").replace(chr(34), "")}"')
        if meta.get("start_page") and meta.get("end_page"):
            pages_str = f'{meta["start_page"]}-{meta["end_page"]}'
            fm.append(f'pages: "{pages_str}"')
            where = meta.get("item") or title
            loc = (f"**Location:** {where} — {title} · pages {pages_str}"
                   + (f" · source: {source}" if source else "") + "\n\n")

        content = f'---\n' + "\n".join(fm) + f'\n---\n\n# {title}\n\n{loc}{text}\n'
        pages.append((slug, content))
    return pages


def _put_page(slug: str, content: str) -> bool:
    """Write one page via the local `gbrain put` CLI (stdin = content)."""
    out = subprocess.run([_GBRAIN, "put", slug], input=content,
                         capture_output=True, text=True, env=_server_env())
    if out.returncode != 0:
        print(f">>> WARNING: put failed for {slug}: {(out.stderr or out.stdout).strip()[:200]}")
    return out.returncode == 0


def _embed_stale() -> str:
    """Embed newly-written chunks so the vector arm has vectors to search."""
    out = subprocess.run([_GBRAIN, "embed", "--stale"],
                         capture_output=True, text=True, env=_server_env())
    lines = [ln for ln in (out.stdout or out.stderr).splitlines() if ln.strip()]
    return lines[-1] if lines else "(no output)"


def main() -> None:
    corpus_path = pathlib.Path(os.getenv("BRK_CORPUS", str(_DEFAULT_CORPUS)))
    if not corpus_path.exists():
        raise SystemExit(f"corpus not found: {corpus_path} (set BRK_CORPUS=<path>)")

    corpus = json.loads(corpus_path.read_text())

    # PageIndex join: pull per-section page ranges + hierarchy from tree.json (if present).
    tree_path = pathlib.Path(os.getenv("BRK_TREE", str(_DEFAULT_TREE)))
    tree_meta, source = {}, ""
    if tree_path.exists():
        tree = json.loads(tree_path.read_text())
        # key by title (see build_pages: id join is unreliable across regenerated files)
        tree_meta = {m["title"].strip(): m for m in flatten_tree(tree).values() if m.get("title")}
        source = str(tree.get("title", "")).strip()
        print(f">>> PageIndex enrich: {tree_path.name} → {len(tree_meta)} nodes "
              f"(source '{source}')")
    else:
        print(f">>> no tree.json at {tree_path} — ingesting WITHOUT structural metadata")

    pages = build_pages(corpus, tree_meta=tree_meta, source=source)
    print(f">>> {corpus_path.name}: {len(corpus)} sections → {len(pages)} pages "
          f"(prefix '{_SLUG_PREFIX}')")

    written = sum(_put_page(slug, content) for slug, content in pages)
    print(f">>> wrote {written}/{len(pages)} pages")

    print(">>> embed --stale: " + _embed_stale())
    print(">>> auto-eval: " + run_auto_eval())


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **Deterministic load, on purpose.** The W2.7 sections arrive as `{id, title, text}` - already page-shaped - so there is no LLM extraction and no `reconcile_graph()`. This block tests *retrieval* on a new corpus shape, not graph wiring, so skipping extraction keeps the experiment clean and cheap.
- **The corpus choice IS the hypothesis.** The 19-page entity brain is semantic-heavy (vector wins, RRF adds nothing - Phase 6). A 10-K is the opposite: dollar figures, segment names, "operating earnings" - exact-term-heavy, where the keyword arm earns its weight and hybrid-RRF should win. Loading it lets `run_auto_eval()` test that directly (and it's what flipped the policy `vector → hybrid`).
- **The tree-join is the combined PageIndex+GBrain fix.** Flat `brk_corpus.json` drops structure; `tree.json` carries per-section page ranges + hierarchy. Joining it writes a `**Location:** Item 8 · pages 99-147` breadcrumb *into the page body*, so structural "where are the Notes?" questions answer from the page itself - this is what closed the false-positive-grounding gap on the Notes question (Block D).
- **It ends in the same loop.** `embed --stale` then `run_auto_eval()` - identical hook to `ingest_agent.py`, so a brand-new corpus self-selects its arm with no extra wiring.

```mermaid
%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%
flowchart TD
  GT[(eval_ground_truth.json<br/>16 Qs + pass_criteria)] --> Q[per question]
  Q --> SL[gbrain_query_slugs<br/>hybrid · C=3]
  SL --> CTX[build_context<br/>full bodies]
  CTX --> GEN[chat · gen=Opus<br/>answer from notes only]
  GEN --> JG[judge=Opus<br/>vs pass_criteria]
  JG --> ROW[pass / fail row]
  ROW --> AGG[answer pass-rate<br/>before vs after<br/>structural ingest]
```
*`eval_brk16.py` flow. Retrieves each W2.7 question through GBrain's hybrid arm at `C=3` (the selector's budget), answers with Opus from those notes only, and judges against the same `pass_criteria` W2.7 used. Run before *and* after the PageIndex-structure ingest to see the structural questions start passing without regressing the rest - this is the answer-side half of the calibrator story.*

**When to use:** Reach for `eval_brk16.py` when you want a full end-to-end answer-quality check against the 16-question W2.7 golden set - specifically to verify that a corpus change (such as the PageIndex-structure ingest enrichment) improves structural questions without regressing factual recall. Use `policy_eval.ts` instead when you only need to re-score retrieval grounding; use `eval_brk16.py` when you need the answer + judge layer to confirm that better grounding actually translates to correct answers.

**Code — the 16-question verifier (full source `src/eval_brk16.py`, reuses `shared/`):**

```python
"""eval_brk16.py — run GBrain on ALL 16 W2.7 questions; answer pass-rate vs `pass_criteria`.

The full W2.7 eval (12 in-document + 4 out-of-document refusals), retrieved through GBrain's hybrid arm (C=3, full bodies), answered + judged against the same rubric W2.7 used. Run it BEFORE and AFTER the PageIndex-structure ingest enrichment to see whether the structural "where-is-X" questions (esp. the Notes question) start passing — without regressing the rest.

Reuses shared/ (per AGENTS.md): llm (resolve/chat/judge/load_pass_criteria) + gbrain_cli (gbrain_query_slugs/build_context). Generator + judge default to Opus so a failure is a retrieval-representation gap, not a weak-generator artifact.

Run (services: gbrain-pg, oMLX :8000 for query embed, VibeProxy :8317 for gen/judge): 
  GEN=opus JUDGE=opus OPENROUTER_BASE_URL=http://localhost:8317/v1 \
  OPENROUTER_API_KEY=vibeproxy \
  uv run python src/eval_brk16.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/Users/yuxinliu/code/agent-prep/shared")
from gbrain_cli import build_context  # noqa: E402
from llm import LLMUnavailable, chat, judge, load_pass_criteria, resilient, resolve  # noqa: E402

_GT = "/Users/yuxinliu/code/agent-prep/lab-02-7-pageindex/data/eval_ground_truth.json"
_PROMPT = ("Using ONLY the notes below, answer the question. If a fact is not in the notes, "
           "say 'insufficient context'.\n\nNOTES:\n{ctx}\n\nQUESTION: {q}")
_C = 3


def _slugs(q: str, limit: int) -> list[str]:
    # local import so a missing gbrain CLI surfaces clearly
    from gbrain_cli import gbrain_query_slugs
    return gbrain_query_slugs(q, limit)


def main() -> None:
    criteria_by_q = load_pass_criteria(_GT)
    gen_c, gen_m, gen_n = resolve("GEN", "opus")
    judge_c, judge_m, judge_n = resolve("JUDGE", "opus")
    print(f"eval_brk16: {len(criteria_by_q)} questions · gen={gen_n} · judge={judge_n} · C={_C}\n")

    rows: list[tuple[str, bool]] = []
    for q, criteria in criteria_by_q.items():
        slugs = _slugs(q, _C)
        try:
            ctx = build_context(slugs) if slugs else ""
            answer = resilient(chat, gen_c, _PROMPT.format(ctx=ctx, q=q), gen_m)
            ok = judge(judge_c, answer, criteria, judge_m)
        except LLMUnavailable as exc:
            print(f"  [skip] {q[:56]} ({exc})")
            continue
        rows.append((q, ok))
        print(f"  {'P' if ok else 'F'}  {q[:66]}")

    n = len(rows)
    passed = sum(1 for _, ok in rows if ok)
    print(f"\ngt_pass: {passed}/{n} = {passed / n:.3f}" if n else "\nno rows")
    notes = [ok for q, ok in rows if "Notes to Consolidated" in q]
    if notes:
        print(f"structural 'Notes located?' question: {'PASS' if notes[0] else 'FAIL'}")


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **Opus as both generator AND judge is deliberate.** With a strong generator a failure cannot be blamed on a weak model - it isolates a *retrieval-representation* gap (the answer wasn't in the retrieved chunks in a usable form). This is the fix for the weak-model confound that muddied the earlier routing A/B; the eval measures retrieval, not generation horsepower.
- **It reuses `shared/`, by the rule-of-three.** `resolve` / `chat` / `judge` / `load_pass_criteria` come from `shared/llm.py` and the GBrain query helpers from `shared/gbrain_cli.py` - infra introduced in earlier chapters and imported here, not re-implemented (the agent-prep `shared/` convention).
- **`C=3`, full bodies - the same budget as the selector.** The verifier reads the same top-3 context the `discounted grounding@C` selector scores, so the cheap metric and the expensive answer-judge measure the *same prompt*. That alignment is what lets the calibrator (`r=+0.820`) license the cheap proxy in the hot loop.
- **Before/after is the experiment.** Running the same questions pre- and post- the PageIndex-structure ingest is how the chapter proves the structural fix made the Notes question pass *without* regressing the other 15 - measured, not a vibe.

`★ Insight ─────────────────────────────────────`
- **A policy is only as good as its eval queries.** The convenient known-item proxy (titles as queries) selected `keyword`; the real golden set selected `vector`/`hybrid` — opposite verdicts on the *same corpus*. The whole value of the loop rides on a representative golden set, which is why it's the version-controlled centerpiece, not an afterthought. Convenience (auto-generated queries) bought a *wrong* policy.
- **Drift adaptation, measured.** A *fixed* golden set re-scored against a *changing* corpus moved the policy `vector → hybrid` with zero code change, and the move was justified (mixed query classes make both arms competitive → RRF wins). That's the "search quality tracks the corpus" claim, demonstrated end-to-end — and the exact loop that improves the agent as its brain grows.
- **Honest edges:** in Phase A vector and hybrid *tied* (0.667; entity data absent), so v1 was a tie resolved by order — the decisive signal is Phase B. Grounding ≠ answer quality, the entity golden set is only 6 questions, and the policy steers the agent's retrieval path, not stock `gbrain query`.
`─────────────────────────────────────────────────`

#### Reproduce — the drift experiment, end to end

Prereqs: the Phase-1 stack up — Postgres+pgvector container (`gbrain-pg`) and the oMLX embedding server on `:8000`. All commands run from `~/code/agent-prep/lab-03-5-96-gbrain/` with the lab `.env` loaded (`set -a; . ./.env; set +a`) and `~/.bun/bin` on `PATH`.

**Step 1 — an isolated DB, so the 10-K measures alone first.** A fresh database keeps the 10-K corpus uncontaminated by the entity brain for Phase A.

```bash
docker exec gbrain-pg psql -U postgres -c "CREATE DATABASE gbrain_brk;"
docker exec gbrain-pg psql -U postgres -d gbrain_brk -c "CREATE EXTENSION IF NOT EXISTS vector;"
gbrain init --url postgresql://postgres:postgres@localhost:5432/gbrain_brk \
  --embedding-model ollama:nomicai-modernbert-embed-base-bf16
export GBRAIN_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gbrain_brk
```

**Step 2 — ingest corpus #1: the 10-K.** `load_brk_corpus.py` reads W2.7's parsed sections (`lab-02-7-pageindex/data/brk_corpus.json` — the PDF already segmented into 44 `{id,title,text}` sections), writes each as a GBrain page with YAML-frontmatter title (Entry 19), embeds, and triggers the golden auto-eval.

```bash
.venv/bin/python src/load_brk_corpus.py     # 44 pages, ~429 chunks embedded
gbrain stats | head -3                       # Pages: 44
```

**Step 3 — Phase A: generate policy v1 on the 10-K-only corpus.**

```bash
bun src/policy_eval.ts        # scores the 18 golden Qs over the current 44 pages
cat results/search_policy.json # → "strategy": "vector"  (tenk g@5 0.958; entity ~0, data absent)
```

**Step 4 — ingest corpus #2: the W3.5.96 entity data, INTO THE SAME DB.** This is the drift event. The raw fixtures live under `~/brain/sources/` (the emails, dinner/ board-call/pitch transcripts, and tweets from Phase 2); the **thin-agent + fat-tools** pipeline (Phase 3) extracts entities and writes them via `put_page` over MCP, then reconciles links — now pointed at `gbrain_brk`, so the entity pages land *alongside* the 44 brk sections. Because `data/golden_eval.json` exists, `run_auto_eval()` fires `policy_eval.ts` automatically at the end of the ingest.

```bash
.venv/bin/python src/ingest_agent.py   # warms extraction cache → agent put_page's
                                       # ~15 entity pages → reconcile_graph() →
                                       # run_auto_eval() RE-FIRES policy_eval (golden)
gbrain stats | head -3                 # Pages: 59  (44 brk + 15 entity)
```

**Step 5 — Phase B: observe the policy changed, and the actuator honors it.**

```bash
cat results/search_policy.json                 # "strategy": "vector" → "hybrid"
bun src/policy_eval.ts                          # full per-domain table (idempotent re-check)
bun src/query_policy.ts "Who is anchoring the acme-seed round?"              # global policy (= hybrid on THIS corpus; auto_eval's pick)
QUERY_ROUTER=on bun src/query_policy.ts "Item 1C Cybersecurity governance"   # per-query router → keyword (OR-preprocessed)
```

**Verification:** `gbrain stats` shows pages 44 → 59 after Step 4; `search_policy.json` `strategy` flips `vector → hybrid`; `policy_eval` per-domain shows `entity g@5` rising from ~0 (Phase A) to 1.000 (Phase B, hybrid) while `tenk g@5` holds at 0.958. Teardown: `docker exec gbrain-pg psql -U postgres -c "DROP DATABASE gbrain_brk;"`.

**Step 6 — (combined PageIndex + GBrain) structural-question ingest.** To make location/citation questions answerable ("where are the Notes located?"), carry PageIndex's section structure into GBrain. Build the tree once in **W2.7's lab**, then re-ingest with the tree-join enrichment in **this lab** (see *Where the scripts live* under the comparison above):

```bash
# W2.7's PageIndex lab — build the structure (one-time LLM pass)
cd ~/code/agent-prep/lab-02-7-pageindex
python src/build_tree.py        # PDF → data/tree.json (per-section page ranges + hierarchy)
python src/_brk_corpus.py       # PDF + tree.json → data/brk_corpus.json (section articles)

# this lab — join tree.json into each GBrain page (frontmatter + **Location:** body line)
cd ~/code/agent-prep/lab-03-5-96-gbrain
uv run python src/load_brk_corpus.py    # re-ingests 44 sections, now structure-enriched

# verify on all 16 W2.7 questions (GBrain hybrid retrieval + Opus reader/judge)
OPENROUTER_BASE_URL=http://localhost:8317/v1 OPENROUTER_API_KEY=vibeproxy GEN=opus JUDGE=opus \
  uv run python src/eval_brk16.py       # flat 15/16 → enriched 16/16; "Notes located?" flips PASS
```

**Verification:** `gbrain get sections/brk_0039` shows `**Location:** Item 8 … pages 99-147`; `eval_brk16.py` reports `gt_pass 16/16` with the Notes question PASS and no regression on the other 15.

> **Cold-start note:** delete `data/golden_eval.json` and `run_auto_eval()` falls back
> to the known-item `auto_eval.ts` (proxy) — useful on a brand-new brain with no real
> questions yet, but it can mis-select the arm (Entry 20), so add a real golden set as
> soon as you have representative questions.

**Deliverable:** `data/golden_eval.json` (18 real Qs) + `src/policy_eval.ts` (policy source) + `src/query_policy.ts` (actuator) + `src/load_brk_corpus.py`. `run_auto_eval()` prefers the golden eval, falling back to the known-item `src/auto_eval.ts` only at cold start (when no golden set exists). Tests: `tests/auto_eval.test.ts` (15), `tests/test_load_brk_corpus.py` (7); regression gate **24 pytest + 15 bun** green. Policy artifact `results/search_policy.json`; full numbers in `RESULTS.md`.

#### Script roles — 离线审计 · 在线运行 · 测试 (what each `src/` file is for)

All paths are relative to the lab repo `~/code/agent-prep/lab-03-5-96-gbrain/`. The split that matters in production: a **few** scripts run automatically in the agent's ingest→query path (online); **most** are run by hand to measure and decide (offline audit / A-B); a couple are one-off setup; one is a unit test.

**在线运行 / Online runtime — the production agent path (run automatically, in the loop).**

| file (location)           | role · when it runs                                                                                                      | chapter           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| `src/ingest_agent.py`     | small-corpus ingest entrypoint: WRITE → reconcile → auto-eval → READ                                                     | Phase 3           |
| `src/resumable_ingest.py` | large-corpus ingest entrypoint (per-file stream + checkpoint + merge)                                                    | Phase 8           |
| `src/policy_eval.ts`      | **SELECTOR** — scores 3 arms on the golden set, writes `search_policy.json`; fired by `run_auto_eval()` **every ingest** | Phase 9 · Block B |
| `src/auto_eval.ts`        | cold-start SELECTOR fallback (no golden set yet); also fired by `run_auto_eval()`                                        | Phase 9           |
| `src/query_policy.ts`     | **actuator** — routes each query by the policy (global arm, or per-query with `QUERY_ROUTER=on`); runs **every query**   | Phase 9 · Block C |
| `src/query_routing.ts`    | router/classifier library (imported, no `main`) — one canonical classifier shared by actuator + A/B                      | Phase 9 · Block C |
| `src/grounding.ts`        | pure metric primitive library (`coverage`/`disc`/`budgetScore`, imported, no `main`)                                     | Phase 9 · Block D |
| `src/assembly.ts`         | 1-hop graph-expansion library (`graphExpand`, imported; **gated/shelved** — not in the live path by default)             | Phase 9           |

**离线审计 / Offline audit & A-B experiments — run by hand to measure & decide (NOT in the hot path).**

| file (location) | role · what it measures | chapter |
|---|---|---|
| `src/verify_arch.py` | **CALIBRATOR** — `corr(grounding, answer-pass)` + selector-validity audit (the `r=+0.820`) | Phase 9 · Block D |
| `src/route_eval.ts` | routing headroom + dumps `arm_scores.json` / `route_slugs.json` (feeds the Python A-Bs) | Phase 9 |
| `src/route_eval_kwpp.ts` | keyword-revival probe (raw FTS vs OR-preprocessed) | Phase 9 |
| `src/route_principle_ab.ts` | 3-way routing A-B on grounding (router vs global vs strengthened-global) | Phase 9 · Block E |
| `src/assembly_graph_ab.ts` | graph-expansion A-B on coverage (plain vs 1-hop expanded) | Phase 9 |
| `src/answer_route_ab.py` | answer-quality A-B for routing (reads `route_slugs.json`) | Phase 9 |
| `src/answer_principle_ab.py` | answer-quality A-B across 3 policies (reads `principle_slugs.json`) | Phase 9 · Block E |
| `src/assembly_answer_ab.py` | graph-expansion answer A-B (plain vs expanded) | Phase 9 |
| `src/reader_ab.py` | reader A-B — generator/judge model sweep on fixed retrieval (`GEN`/`JUDGE` presets) | Phase 9 · Block E |
| `src/ground_truth_ab.py` | memory-as-authoritative A-B (ground-truth hierarchy) | Phase 7 |
| `src/eval_brk16.py` | 16-question answer verifier vs W2.7 `pass_criteria` (before/after structural ingest) | W2.7 comparison |
| `src/bench_strategies.ts` | Phase-6 keyword/vector/hybrid benchmark — **engine-layer** (recall@3/MRR/nDCG@3) | Phase 6 |
| `src/bench_rrf.py` | Phase-6 keyword-vs-hybrid benchmark — **CLI-layer** sibling (hit@3/MRR); the one that exposed BCJ Entry 8 | Phase 6 |
| `src/bench_w27_questions.ts` | **Path A** — real W2.7 questions through GBrain arms, grounding@K (seeded `golden_eval.json`) | W2.7 comparison |

**一次性设置 / 诊断 · One-off setup & diagnostics.**

| file (location) | role | chapter |
|---|---|---|
| `src/load_brk_corpus.py` | **Path B** — deterministic load of the W2.7 10-K corpus into GBrain (no LLM extract) | W2.7 comparison |
| `src/probe_mcp.py` | MCP smoke test — proves plain Python can drive GBrain's MCP before building the agent | Phase 3 |

**测试 / Tests.**

| file (location) | role | chapter |
|---|---|---|
| `src/grounding.test.ts` | unit tests for the grounding metric (`bun test`, no services) | Phase 9 |

> **The one-line takeaway:** only the **online** group (8 files) runs in production - and within it the *self-tuning* is just `policy_eval.ts` / `auto_eval.ts` (every ingest) + `query_policy.ts` (every query); the **offline** group (14 files) is the measurement scaffolding that *justified* those choices once, off the hot path; the rest are setup + one unit test.

#### Running reference — scripts, env, parameters

Every script in this chapter is parameterised by environment variables (and a couple by argv). This is the canonical "how do I run it" table — what each needs, and in what order. Phase-9 scripts first, then the ingest, library, benchmark, and Phase-7 scripts.

**Services + shell (run all commands from `~/code/agent-prep/lab-03-5-96-gbrain/`):**
- **`gbrain-pg`** — Postgres+pgvector container. `GBRAIN_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gbrain`.
- **oMLX `:8000`** — local MLX server. Serves **embeddings** (`OLLAMA_BASE_URL`/`OLLAMA_API_KEY`) for the vector/hybrid arms, AND the local **14B chat** model.
- **VibeProxy `:8317`** — OpenAI-compatible proxy to **cloud Claude** (`OPENROUTER_BASE_URL`/`OPENROUTER_API_KEY=vibeproxy`); used as the answer generator / judge.
- Load the lab `.env` (`set -a; . ./.env; set +a`) and put `~/.bun/bin` on `PATH`. `.env` holds `GBRAIN_DATABASE_URL`, `OLLAMA_*`, `LLM_*` (oMLX key + local chat model), `OPENROUTER_*`.

| script                   | role                                                                        | params / env (default)                                                                                  | services                 | run                                                                                                                                             |
| ------------------------ | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `grounding.test.ts`      | unit tests for the metric                                                   | —                                                                                                       | none                     | `bun test src/grounding.test.ts`                                                                                                                |
| `policy_eval.ts`         | **SELECTOR** — write the policy                                             | `POLICY_K` (5), `POLICY_C` (3)                                                                          | pg + oMLX embed          | `bun src/policy_eval.ts` · sweep: `POLICY_C=5 bun src/policy_eval.ts`                                                                           |
| `query_policy.ts`        | actuator — global policy **or** per-query router                            | argv `"<query>" [limit=5]`; **`QUERY_ROUTER`** (off→global policy · on→type-route)                      | pg + oMLX embed          | global: `bun src/query_policy.ts "Who is anchoring acme-seed?" 3` · router: `QUERY_ROUTER=on bun src/query_policy.ts "Item 1C Cybersecurity" 3` |
| `query_routing.ts`       | **ROUTER brain** — type classifier + kw OR-preprocess (shared, no main)     | — (imported)                                                                                            | none                     | imported by `query_policy.ts` + `route_principle_ab.ts` (one canonical classifier → production == tested)                                       |
| `route_eval.ts`          | routing headroom + **dumps**                                                | `POLICY_K` (5), `POLICY_C` (3)                                                                          | pg + oMLX embed          | `bun src/route_eval.ts` → writes `results/route_slugs.json`, `results/arm_scores.json`                                                          |
| `route_eval_kwpp.ts`     | keyword-revival probe (raw vs OR-preprocessed)                              | `GOLDEN_EVAL`, `POLICY_K` (5), `POLICY_C` (3)                                                           | pg + oMLX embed          | `GOLDEN_EVAL=data/golden_balanced.json bun src/route_eval_kwpp.ts`                                                                              |
| `route_principle_ab.ts`  | **3-way routing A/B** (grounding) — router vs global vs strengthened-global | `GOLDEN_EVAL`, `POLICY_K`/`_C`; writes `results/principle_slugs.json`                                   | pg + oMLX embed          | `GOLDEN_EVAL=data/golden_balanced.json bun src/route_principle_ab.ts`                                                                           |
| `assembly.ts`            | **ASSEMBLY lib** — 1-hop graph expansion (`graphExpand`, shared, no main)   | — (imported); uses `getLinks`/`getBacklinks`                                                            | none                     | imported by `assembly_graph_ab.ts` (the entity-aware-assembly fix)                                                                              |
| `assembly_graph_ab.ts`   | graph-expansion A/B (coverage) + slug dump                                  | `GOLDEN_EVAL`, `POLICY_K`/`_C`, `MAX_PULL` (2); writes `results/assembly_slugs.json`                    | pg + oMLX embed          | `GOLDEN_EVAL=data/golden_balanced.json bun src/assembly_graph_ab.ts`                                                                            |
| `load_brk_corpus.py`     | ingest the 10-K corpus                                                      | `BRK_CORPUS` (path), `SLUG_PREFIX` (`sections`)                                                         | pg + oMLX embed          | `uv run python src/load_brk_corpus.py`                                                                                                          |
| `answer_route_ab.py`     | answer A/B (routing)                                                        | `OPENROUTER_BASE_URL`/`_API_KEY`, `CHAT_MODEL`, `MAX_BODY_CHARS` (0); reads `route_slugs.json`          | pg + chat (`:8317`)      | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/answer_route_ab.py`                                                                      |
| `answer_principle_ab.py` | answer-quality A/B (3 policies, entity coverage)                            | `CHAT_MODEL`, `MAX_BODY_CHARS` (0); reads `principle_slugs.json`                                        | pg + chat (`:8317`)      | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/answer_principle_ab.py`                                                                  |
| `assembly_answer_ab.py`  | graph-expansion answer A/B (plain vs expanded)                              | `CHAT_MODEL`, `MAX_BODY_CHARS` (0); reads `assembly_slugs.json`                                         | pg + chat (`:8317`)      | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/assembly_answer_ab.py`                                                                   |
| `verify_arch.py`         | **CALIBRATOR** — corr(metric, answer)                                       | `OPENROUTER_BASE_URL`/`_API_KEY`, `CHAT_MODEL`; reads `arm_scores.json`                                 | pg + chat (`:8317`)      | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/verify_arch.py`                                                                          |
| `reader_ab.py`           | reader A/B (fixed retrieval)                                                | **`GEN=`/`JUDGE=`** preset (`haiku`/`opus`/`14b`/`qwen`), `MAX_BODY_CHARS` (0); reads `arm_scores.json` | pg + gen/judge endpoints | `GEN=14b JUDGE=opus uv run python src/reader_ab.py`                                                                                             |
| `ingest_agent.py` | ingest (small corpus): WRITE → reconcile → auto-eval → READ | `LLM_MODEL`/`LLM_BASE_URL`/`LLM_API_KEY`, `AUTO_EVAL` (1), `GBRAIN_BIN` | pg + oMLX (embed+chat) + bun | `uv run python src/ingest_agent.py` |
| `resumable_ingest.py` | ingest (large corpus): per-file stream + checkpoint + merge | `LLM_*`; consts `CHUNK_CHARS` (6000) / `BATCH` (8) / `BIG_PAGE_CHARS` (8000) | pg + oMLX + bun | `uv run python src/resumable_ingest.py` (re-run to resume · restart: `rm -rf ~/brain/.ingest_*`) |
| `probe_mcp.py` | MCP smoke test — list GBrain tools from plain Python | `GBRAIN_BIN`; server env `GBRAIN_DATABASE_URL`/`OLLAMA_*` | pg + oMLX + bun | `uv run python src/probe_mcp.py` |
| `auto_eval.ts` | cold-start SELECTOR fallback (no golden set) — known-item proxy | `AUTO_EVAL_K`/`_QMIN`/`_QMAX`/`_RATIO`/`_SEED`/`_STRICT`/`_REGRESS_EPS`, `GBRAIN_SRC` | pg + oMLX embed | `bun src/auto_eval.ts` (auto-run by `run_auto_eval()` when `data/golden_eval.json` is absent) |
| `grounding.ts` | pure metric primitive lib (`coverage`/`disc`/`budgetScore`, no `main`) | — (imported) | none | imported by `policy_eval.ts`/`route_eval.ts`/…; tests: `bun test src/grounding.test.ts` |
| `bench_strategies.ts` | Phase-6 benchmark, **engine-layer** — recall@3 / MRR / nDCG@3 | `GBRAIN_SRC` | pg + oMLX embed | `bun src/bench_strategies.ts` |
| `bench_rrf.py` | Phase-6 benchmark, **CLI-layer** sibling — hit@3 / MRR (exposed BCJ Entry 8) | — (hardcoded query set; shells to `gbrain`) | pg + oMLX + bun | `uv run python src/bench_rrf.py` |
| `bench_w27_questions.ts` | **Path A** — real W2.7 questions → arms, grounding@K / answerable@K | `BENCH_K` (5), `GBRAIN_SRC` | pg + oMLX embed | `bun src/bench_w27_questions.ts` |
| `ground_truth_ab.py` | memory-as-authoritative A/B (ground-truth hierarchy, Phase 7) | `CHAT_MODEL`, `OPENROUTER_BASE_URL`/`_API_KEY` | pg + chat (`:8317`) | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/ground_truth_ab.py` |
| `eval_brk16.py` | 16-question answer verifier vs W2.7 `pass_criteria` (before/after) | `GEN`/`JUDGE` (opus), `OPENROUTER_*`, `_C` (3) | pg + chat (`:8317`) | `GEN=opus JUDGE=opus uv run python src/eval_brk16.py` |

**Data-dependency order (don't skip):** the four analysis scripts consume dumps, so retrieval runs first. `route_eval.ts` → writes `route_slugs.json` + `arm_scores.json` → which `answer_route_ab.py`, `verify_arch.py`, `reader_ab.py` then read. `policy_eval.ts` and `route_eval.ts` both need a **loaded corpus + oMLX embeddings up** (vector/hybrid arms embed at run-time); the three Python A/B scripts need a **chat endpoint** but NOT oMLX embeddings (slugs are already dumped; bodies come from Postgres via `gbrain get`). The **routing re-test** is its own chain: `route_principle_ab.ts` → writes `results/principle_slugs.json` → read by `answer_principle_ab.py` (pin a strong generator with `CHAT_MODEL`). The per-query **router itself ships in `query_policy.ts` behind `QUERY_ROUTER` (default off)** and shares one classifier with the A/B via `query_routing.ts`, so what production routes is exactly what the A/B scored.

**`reader_ab.py` model presets (no code change to switch).** `GEN`/`JUDGE` each resolve a named model to endpoint+key+model id from the `_PROFILES` registry:

| preset | endpoint | model |
|---|---|---|
| `haiku` | VibeProxy `:8317` | `claude-haiku-4-5-20251001` |
| `opus` | VibeProxy `:8317` | `claude-opus-4-5-20251101` |
| `14b` / `qwen` | oMLX `:8000` | `Qwen2.5-Coder-14B-Instruct-MLX-4bit` |

Add a model = one line in `_PROFILES`. Raw escape hatch: set `<ROLE>_MODEL` (+ optional `<ROLE>_BASE_URL` / `<ROLE>_API_KEY`) to bypass the registry, e.g. `GEN_MODEL=… GEN_BASE_URL=… uv run python src/reader_ab.py`. `MAX_BODY_CHARS` (default 0 = full bodies) caps each injected body for a small-context generator like the local 14B.

#### Metric & column glossary

Every term that appears in a Phase-9 table, in one place.

**Building blocks**
- **coverage** — for one section, the fraction of a question's `expected_entities` that appear as substrings in its text, ∈ [0,1]. The atom every grounding metric is built from.
- **arm** — the retrieval strategy under test: **keyword** (FTS / BM25-style exact match), **vector** (dense embedding similarity), **hybrid** (RRF fusion of keyword + vector).
- **C (context budget)** — how many top-ranked chunks the generator actually reads (here **3**, measured off the agent). **K (retrieval depth)** — how many hits retrieval pulls (here 5); C ≤ K.
- **disc(rank)** — position discount `1/log2(rank+2)`: rank-0 = 1.00, rank-1 = 0.63, rank-2 = 0.50.

**Domains** (the golden set is domain-tagged)
- **tenk** — the 12 Berkshire 10-K questions (factoid / synthesis / citation).
- **entity** — the 6 proper-noun questions from the W3.5.96 fixtures (Sam Okafor, Lin Zhao, …).

**Retrieval-grounding metrics**

Notation: $q$ ranges over the $N$ golden questions; $\text{cov}_{q,i}\in[0,1]$ is the coverage of the rank-$i$ retrieved section for $q$ (top hit = rank $i{=}0$); $\text{disc}(i)=\tfrac{1}{\log_2(i+2)}$. A per-domain variant ($g@5{:}\text{tenk}$, $g@C{:}\text{entity}$, …) restricts the mean to the $q$ in that domain.

- **grounding@5 / g@5 tenk / g@5 entity** *(original, rank-blind — superseded)* — best raw coverage over the top-5, averaged over questions; blind to rank and to the context budget. $\;\text{grounding@5}=\dfrac{1}{N}\sum_{q}\max_{0\le i<5}\text{cov}_{q,i}$
  - *reads:* $\max_{0\le i<5}$ keeps the single best of the top-5 sections (one good hit is enough); $\tfrac{1}{N}\sum_q$ averages that best over all $N$ questions. No $\text{disc}$ factor, so where in the top-5 the answer sits is ignored.
- **discounted grounding@C / grnd@C↓ / g@C:tenk / g@C:entity** *(current)* — position-weighted best coverage over the top-$C$; rewards a section that is BOTH high-ranked AND inside the $C$ chunks the generator reads (a section RRF demoted, or pushed past $C$, scores lower or 0). The `↓` marks "discounted". $\;\text{grnd@C}\!\downarrow=\dfrac{1}{N}\sum_{q}\max_{0\le i<C}\big(\text{cov}_{q,i}\cdot\text{disc}(i)\big)$
  - *reads:* each section is scored $\text{cov}_{q,i}\cdot\text{disc}(i)$ — coverage times its rank weight ($1,\,0.63,\,0.5,\dots$); $\max_{0\le i<C}$ keeps the best within the budget $C$; average over $q$. A full answer at rank 0 scores $1.0$, at rank 2 scores $0.5$, past rank $C$ it is outside the window so it contributes $0$.
- **flat@C (old)** — the rank-blind contrast: discounted grounding@C with $\text{disc}(i)\equiv1$ (no position discount, so an answer at rank 0 and at rank 4 score identically). In `grounding.ts` this is `budgetScore.gFull` (the discounted score is `gDisc`). Where $\text{flat}>\text{grnd}\!\downarrow$, the answer sits below rank 0. $\;\text{flat@C}=\dfrac{1}{N}\sum_{q}\max_{0\le i<C}\text{cov}_{q,i}$
  - *reads:* identical to $\text{grnd@C}\!\downarrow$ but with every $\text{disc}(i)=1$ — best raw coverage in the top-$C$, position thrown away. The *only* difference from the discounted score is that flat does not care WHERE the best section ranks.
- **demotion tax** — the answer-mass an arm (usually hybrid RRF) pushes below rank 0; the cost of fusion's reordering, always $\ge 0$ since $\text{disc}(i)\le 1$. $\;\text{demotion tax}=\text{flat@C}-\text{grnd@C}\!\downarrow$
  - *reads:* the two metrics differ only by the $\text{disc}$ weight, so their difference is exactly what the position discount subtracted. A large tax means the best-covering section is being demoted below rank 0 (fusion reordered it down).
- **answerable@C** — fraction of questions where some top-$C$ section fully covers the expected entities (the tie-breaker when grounding ties). $\;\text{answerable@C}=\dfrac{1}{N}\sum_{q}\mathbf{1}\!\left[\max_{0\le i<C}\text{cov}_{q,i}=1\right]$
  - *reads:* the indicator $\mathbf{1}[\,\cdot=1\,]$ is $1$ only when some top-$C$ section covers EVERY expected entity (coverage exactly $1$), else $0$; the mean is the fraction of fully-answerable questions. A strict binary check — used only to break grounding ties.

**Answer-quality metrics** (`verify_arch.py`, `reader_ab.py`)
- **mean grnd@3↓** — per-arm average of the cheap discounted grounding@C=3 metric (the `↓` marks it discounted; bare `grounding@N` without the `↓` denotes the *old rank-blind* metric — see `grounding@5` above — so the current metric always carries `↓`).
- **answer pass-rate** — fraction of generated answers a strong LLM judge marks **PASS** against the question's `pass_criteria`. The real objective; grounding is its cheap surrogate (corr +0.820).

**Reader strategies** (`reader_ab.py` — same retrieval, different prompt)
- **plain** — "Using only the notes, answer; if a fact isn't there, say you don't have it." Baseline.
- **authoritative** — frames the notes as AUTHORITATIVE ground truth: trust them, don't re-derive, don't re-fetch, don't hedge (the memory-os pattern).
- **extract-then-answer** — two steps: first copy the answer-bearing sentence(s) verbatim, then answer from that extraction. Decouples "find the fact" from "compose the answer".
- **cite** — authoritative + require a `[bracketed]` source citation for each factual claim.

## 6. Bad-Case Journal (real, observed)

_Observed during the real Phase-1 → Phase-6 runs (GBrain 0.42.25.0):_

**Entry 1 — `llama-server` provider is a catch-22 for registry-known embed models (OBSERVED).** `--embedding-model llama-server:bge-m3` (and `:nomicai-modernbert-embed-base-bf16`) refuses *both* ways: **with** `--embedding-dimensions` → "does not support custom dimensions N (this model only emits its default vector size)"; **without** → "llama-server requires --embedding-dimensions <N> (user-driven recipes have no default dimension)." No value satisfies both → init impossible. *Fix:* use the **`ollama` provider** pointed at oMLX (`OLLAMA_BASE_URL=http://localhost:8000/v1`, `OLLAMA_API_KEY=<key>`, `--embedding-model ollama:<model>`, **no** `--embedding-dimensions`) — it *probes* the endpoint for the dim instead of demanding/rejecting it. (Worth a GBrain issue; strip keys before filing.)

**Entry 2 — init is stateful + greedy; a botched first run poisons every retry (OBSERVED).** Three compounding traps: (a) `--supabase` runs the *interactive Supabase flow* and ignores `GBRAIN_DATABASE_URL` — use `--url`; (b) a present `OPENROUTER_API_KEY` makes init **auto-pick openrouter for embeddings** (probe failed 404 on a dummy key) even with `--embedding-model` set — keep it commented until post-init; (c) a wrong first init persists `~/.gbrain/config.json` + a baked vector-column width, so re-init fails citing the *stale* dimension. *Fix (0 pages → safe):* `DROP DATABASE gbrain; CREATE DATABASE gbrain;` + `rm ~/.gbrain/config.json`, then re-init. Lesson: **GBrain init is stateful and greedy — reset clean if anything looks off, and read the "Using …" line, not the green migration checkmarks.**

**Entry 3 — `gbrain` not found after `bun link` (OBSERVED).** `bun link` symlinks the CLI into `~/.bun/bin` but does not add it to PATH; the installer often doesn't persist the PATH line either. *Fix:* `echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc`. Tell-apart: `ls ~/.bun/bin/gbrain` exists ⇒ pure PATH issue, not a broken install.

**Entry 4 — trying to hand-format every source type into brain pages (DESIGN anti-pattern).** Emails, tweets, and meeting transcripts each have a different shape; writing a per-format converter (or authoring the 50 pages by hand) does not scale and is *not* GBrain's model. *Root cause:* mistaking who owns the structured layer. GBrain splits **raw sources** (immutable, any format, in `sources/`) from **the brain** (two-layer pages the **agent** writes). *Fix:* never author structured pages manually — drop raw under `sources/` (or `gbrain capture`), then let the agent convert via **ingest skills** (`meeting-ingestion`, `article-enrichment`, `voice-note-ingest` → `put_page`/`add_link`) or, in production, the credentialed **integration recipes** (`email-to-brain`, `x-to-brain`, `meeting-sync`). The agent is the universal formatter; you curate. (Drove the Phase 2 rewrite.)

**Entry 5 — the agent stored pages fine but the graph had zero edges (OBSERVED, Phase 3).** A smolagents `CodeAgent` (oMLX) drove GBrain over MCP and wrote 5 well-formed pages via `put_page`, yet `gbrain extract links` reported `Links: 0`. *Root cause:* the LLM extraction wrote entity mentions as **plain prose** ("Alice Chen, founder of Acme AI") and used `<!-- timeline -->` instead of `---`, so there were no `[[wikilinks]]` to extract. The framework + MCP plumbing worked; the *contract* didn't. *Fix:* the extraction prompt must **hard-mandate** path-qualified `[[dir/slug]]` wikilinks with a worked example + "a page with zero wikilinks is invalid" → `Links: 0 → 11`. **Graph quality = extraction quality; measure edges, not pages.**

**Entry 6 — fully-autonomous `CodeAgent` failed on a 14B (OBSERVED, Phase 3).** Asking the agent to read files + write an extractor + compose markdown in one code loop produced a naive regex placeholder + `InterpreterError: import pathlib not allowed` (the CodeAgent sandbox blocks `pathlib`/`json`). *Fix:* **thin agent, fat tools** — move file I/O and extraction into `@tool`s (`read_sources`, `extract_pages`); the agent only orchestrates. Also: filter `ToolCollection.from_mcp` to the ~few tools needed (GBrain exposes ~70; a 14B drowns), depend on `smolagents[mcp]` (mcpadapt), pass DB/oMLX env via `StdioServerParameters(env=…)` (an MCP server is a separate process), and use `use_structured_outputs_internally=True` (oMLX has no native tool_calls). Lab: `~/code/agent-prep/lab-03-5-96-gbrain/`.

**Entry 7 — graph reads as "built" but has no new edges (OBSERVED, Phase 6).** After re-ingesting an expanded corpus, `gbrain stats` showed **19 pages but Links: 11** — unchanged from the 10-page run — even though the new pages' text held ~68 `[[wikilinks]]`. *Root cause:* self-wiring is a **batch extraction pass, not a `put_page` side-effect**. Pages written over MCP live only in Postgres; bare `gbrain extract links` walks a brain *directory* of `.md` files and errors `No brain directory configured`, so extraction never ran on them. *Fix:* `gbrain extract links --source db` re-parses the stored `compiled_truth`/`timeline` columns → `created 34 links from 19 pages` → 45 total. Do **not** gate on `pages.links_extracted_at` — that column tracks the file-source path only and stays null after DB-source extraction.

**Entry 8 — keyword-vs-hybrid benchmark shows zero difference (OBSERVED, Phase 6).** `gbrain search "<q>"` and `gbrain query "<q>"` returned byte-identical rankings *and* scores; an A/B "keyword vs hybrid" read as "no lift." *Root cause:* both subcommands fall through to the **same handler** (`src/cli.ts:771-772 — case 'search': case 'query':`). The CLI has no pure-keyword command; `keywordSearch` is an internal building block *inside* the hybrid pipeline, not a separate path. *Fix:* benchmark at the **engine layer** via `src/core/search/eval.ts:runEval()` with `strategy: 'keyword'|'vector'|'hybrid'`, bootstrapping engine + gateway exactly as the CLI does. **Never A/B retrievers through the CLI.**

**Entry 9 — hybrid-RRF underperformed pure vector (OBSERVED, Phase 6).** On the 19-page brain, RRF scored recall@3 = 0.90 but MRR **0.78** — *worse* than pure vector (0.90 / **0.92**). The expected 83→95 RRF win was a slight regression instead. *Root cause:* the keyword arm missed all four purely-semantic queries (no lexical overlap); RRF fusion folded that dead arm back in, demoting correct vector hits a rank (`dinner at Tartine` vector @1 → hybrid @3). RRF helps only when *both* arms are individually competitive and complementary. *Fix:* on a small, semantic-heavy corpus, **prefer pure vector**; reserve RRF for corpora with enough exact-term / proper-noun traffic that keyword earns its weight. Always measure on your own corpus before quoting the published lift.

**Entry 10 — retrieved "context" is just a slug + one-line snippet; the LLM can't answer (OBSERVED, Phase 7).** The first Ground-Truth A/B fed `gbrain query --json` straight to the model, which replied "the context shows `[[people/lin-zhao]]` but doesn't include the actual content." *Root cause:* `gbrain query` returns ranked **snippets** (slug + compiled-truth first line) for *display*, not full page bodies for grounding. *Fix:* use `query` only to *rank* slugs, then pull each body with `gbrain get <slug>` before injecting. Retrieval (rank) and grounding (fetch) are two separate calls. **Entry 11 — the chat model refuses the task, insisting it's "Claude Code" (OBSERVED, Phase 7).** With the task instruction in the `system` role, VibeProxy→Claude answered every turn with "I'm Claude Code… I can't help with questions about people." *Root cause:* VibeProxy fronts the Claude-Code CLI identity and **overrides the caller's `system` prompt**, so a "you are a knowledge-base assistant" system message is discarded and the model falls back to refusing non-coding requests. *Fix:* put the instruction *and* the grounding notes in the **USER** message as a document-Q&A task ("using ONLY these notes, answer…"); don't depend on `system`. The same model then answers correctly.

**Entry 12 — every agent step "Code execution exceeded the maximum execution time of 30 seconds"; ingest never finishes (OBSERVED, Phase 3/8).** Scaling to 8 sources, the agent burned all 6 steps timing out, re-extracting each time, ~6 min wasted. *Root cause:* `extract_pages` is a ~60s oMLX call, but smolagents' CodeAgent kills any single step's code at **30s** — and the agent re-runs its whole `read_sources(); extract_pages(...)` block every step. The heavy LLM call can never complete inside the sandbox. *Fix:* warm `extract_pages` **once outside the sandbox** (module-level cache in `main()`); the agent's call then returns instantly → ingest finishes in 1 step, 7.5s. At true scale, move extraction fully driver-side and stream per file (Phase 8 / `resumable_ingest.py`). *The 30s IS configurable — but a bump is the wrong fix.* The limit is `MAX_EXECUTION_TIME_SECONDS = 30` in smolagents' `local_python_executor.py`, overridable per agent:
```python
from smolagents import CodeAgent
agent = CodeAgent(tools=[...], model=model,
                  executor_kwargs={"timeout_seconds": 120})   # raise it; or None to disable
```
Two reasons we still move the slow work out of the sandbox instead of bumping: (1) it's a **thread timeout with no kill** — on timeout it raises `ExecutionTimeoutError` but the runaway thread keeps running in the background (Python can't force-kill a thread), so a bigger number just lets slow code *finish*, it adds no real preemption (and it's the *local* executor only; a remote E2B/Docker executor has its own). (2) A bigger timeout solves *nothing* of the actual scale walls — extraction context limit, cross-file dedup, embed-once, resume — and extraction time varies with corpus + model, so you'd keep chasing the number. Moving extraction driver-side makes the timeout value **irrelevant** and is required for the other walls anyway.

**Entry 13 — ingest crashes on `.DS_Store` / picks up `.omc-state/` as "files" (OBSERVED, Phase 8).** `read_sources` threw `UnicodeDecodeError` on a binary `.DS_Store`; the resumable driver also checkpointed two `.omc-state-*` entries (0 pages each). *Root cause:* the walk skipped dotted *filenames* but rglob descended into dotted *directories* and grabbed the non-dotted files inside; binary files aren't UTF-8. *Fix:* skip any **dotted path part** (`any(part.startswith(".") for part in rel.parts)`) AND catch `UnicodeDecodeError`. A real source dir always has `.DS_Store`, `.git/`, tool-state dirs — defend the read boundary.

**Entry 14 — a large corpus can't be ingested in one shot (OBSERVED, Phase 8).** Phase 3's warm-once extraction concatenates *all* files into one prompt → context-window wall + un-resumable (lose the run = lose everything). *Root cause:* the binding scale limits are extraction *context* and cross-file entity *dedup*, not the 30s sandbox. One prompt can't hold thousands of files, and one prompt is the only thing that dedups entities "for free." *Fix:* per-file streaming + **disk** staging (no embedding) + a final `merge_from_disk()` (the deferred dedup-on-write) + agent writes only canonical pages (embedded once) + reconcile — `resumable_ingest.py` (Phase 8). Resumable, bounded, embeds each entity once, scales with file count.

**Entry 15 — a resumed bulk-ingest silently re-embeds everything (OBSERVED, Phase 8).** The first resumable cut checkpointed only EXTRACTION (per file); the write phase relied on `put_page` idempotency. A crash mid-write → resume re-writes ALL canonical → every page embedded a *second* time, quietly negating "embed once." *Root cause:* **idempotent ≠ resumable.** Re-running is *correct* but not *cheap* — the expensive op (embedding) had no resume marker, only the outer extraction loop did. *Fix:* a write checkpoint `~/brain/.ingest_written.json` (written canonical slugs), marked after each batch; the write loop skips done slugs. Proven: a resumed run does **0 write batches, 0 re-embeds**. Checkpoint every *expensive* op, not just the outer loop — "the writes are idempotent" hides a full re-embed behind a true-but-irrelevant claim.

**Entry 16 — a single file too big for the extract context (OBSERVED, Phase 8).** Per-file staging assumed one file fits one extract prompt; a huge file (log, book, long transcript) breaks that and is un-resumable mid-file. *Root cause:* the resume unit was the whole *file*; the binding limit (extract context) is hit *within* a file. *Fix:* `_chunk_text` splits a file > `CHUNK_CHARS` into deterministic, line-aligned chunks `<file>#0/#1/…`, each its own staging unit. **Chose deterministic chunk-index over a `{file: last_line}` offset** — chunk-file existence is an atomic checkpoint (can't be half-written), reuses the per-file resume mechanism unchanged, and collapses "many files" + "one huge file" into one concept (a chunk; a small file = 1 chunk). Cross-chunk entities are reunited by `merge_from_disk` (same path as cross-file). Proven: 13.9 KB → 3 chunks; delete #1 → only #1 re-extracts.

**Entry 17 — the write checkpoint marked a page that never landed (OBSERVED-class, Phase 8).** Marking a whole batch right after `agent.run` returned trusts the agent loop; if a `put_page` failed silently (agent swallows the error, still returns a final answer), the slug gets checkpointed → resume skips it → the page is lost, with no error anywhere. *Root cause:* the checkpoint recorded "the agent's batch code finished," not "the page is in the store." Those differ exactly in the silent-failure case. *Fix:* **verify-then-mark** — `_verify_written` queries `pages` (existence == successful embed+upsert) and the loop checkpoints only the verified subset; un-landed slugs stay un-checkpointed and retry. Invariant: a slug is in the write checkpoint IFF its page is really in GBrain. Gate tested: `_verify_written([real, fake]) → [real]`. Lesson: a checkpoint must record *confirmed durable state*, not "the code that should have written it returned."

**Entry 18 — resume re-ran the (LLM) merge every time (OBSERVED, Phase 8).** Resume re-reads stage chunks to rebuild the canonical list, which re-fired `merge_from_disk`'s per-entity LLM merges — correct but wasteful (same "idempotent ≠ cheap" as the write phase, one layer up). *Root cause:* the merge is a derived layer with no cache; the extraction and write layers were checkpointed but the layer between them wasn't. *Fix:* cache the merge result to `.ingest_merged.json`, keyed by a **stage fingerprint** (each chunk's name+mtime+size). Unchanged staging → cache HIT (skip re-merge); a re-extracted chunk changes the fingerprint → MISS → re-merge + re-cache. Completes the picture: **every derived layer (stage, merge, write) has its own checkpoint**, so resume rebuilds nothing already built. The fingerprint *is* the invalidation — the cache is valid exactly while its inputs are unchanged.

**Entry 19 — CLI `gbrain put` titled pages from the slug, not the `# heading` (OBSERVED, Phase 9).** Loading the 44 brk 10-K sections via `gbrain put sections/brk_0002` with `# Berkshire … > Table of Contents`-headed content produced pages titled **"Brk 0002"**. The known-item eval's *exact* probes then queried "Brk 0002" — tokens absent from the body — so `keyword R@K exact = 0.000` and the whole brk run was contaminated. *Root cause:* CLI `put` derives the title from **YAML frontmatter** (falling back to the slug), NOT from the `# heading` — unlike MCP `put_page`, which parses the heading (which is why the entity pages got real titles). Two write paths, two titling rules; the loader used the wrong one. *Fix:* emit YAML frontmatter `title:` (authoritative), using the breadcrumb **tail** ("Chairman's Letter"), not the full "Berkshire … Annual Report > X" (the shared prefix repeats across all 44 → keyword drowns). exact recall `0.000 → 0.786`. **Measure the stored artifact (the title), not the write's return code** — the same "storage succeeded ≠ data is right" lesson as Entry 5.

**Entry 20 — the auto-tuned policy selected the WORST arm for real queries (OBSERVED, Phase 9).** The known-item auto-eval picked `strategy=keyword` on the 10-K (recall@3 = 0.72) and wrote it to `search_policy.json`. But on 16 **real** W2.7 questions, keyword grounding@5 was **0.19** vs vector/hybrid **0.95** — the policy routes real financial questions to the weakest arm. *Root cause:* known-item probes use page **titles** as "exact" queries (keyword-friendly); real questions are **paraphrases** with no shared surface tokens (vector-friendly). The proxy query distribution ≠ the real one, so the measured winner doesn't transfer. *Fix:* drive the policy from a **representative/real** query set (Path A), and treat known-item auto-eval as a **regression guardrail**, not the policy oracle. An auto-tuning loop inherits the bias of its eval queries — measure the *decision input's* representativeness, not just the loop's mechanics.

**Pre-run predictions vs. what actually happened** (these were guessed *before* Phases 3–6 ran; now resolved against the measured outcomes — **3 of 4 missed**, which is the honest record: predictions are cheap, the observed Entries above are the truth).

| Predicted bad case | Outcome | What actually happened |
|---|---|---|
| **Phase 3** — agent over-relies on GBrain for general knowledge | ✗ didn't occur | Real Phase-3 failures were more basic: zero graph edges (Entry 5) + `CodeAgent` crash on a 14B (Entry 6). The Ground-Truth A/B (Phase 7) showed correct answering-*from*-brain. |
| **Phase 4** — `@handle` markdown-convention mismatch | ✗ didn't occur | Agent emits `[[dir/slug]]` wikilinks → GBrain parses them directly (45 edges). Real issue: MCP `put_page` skips inline auto-link → needs an `extract links --source db` reconcile (Entry 7). |
| **Phase 5** — synthesis emits a wrong "we don't know" | ✗ didn't occur | Gap-honesty worked: absent date → "no information"; present fact → 0.93 (Phase 5 §Verification). |
| **Phase 6** — RRF lift smaller than 12pts | ✓ confirmed, *stronger* — but later refined | Not just a smaller lift — pure vector **beat** RRF on the small entity corpus (Entry 9). The projected cause ("short corpus") was a *proxy*: **Phase 9's drift experiment** sharpened it to **RRF wins iff both arms are individually competitive** — the policy auto-flipped `vector → hybrid` once the brain grew to a mixed 10-K+entity corpus (proper-noun queries revived the keyword arm). So "vector beats RRF" is scoped to single-query-class corpora, not a law. |

---

## 7. Interview Soundbites

**(a) "Why deterministic extraction over LLM extraction for the graph?"**
> Because my data was already structured, so I let the structure do the work. The agent writes Markdown pages with `[[dir/slug]]` wikilinks; GBrain turns those into typed edges by regex — zero LLM calls — so re-running extraction yields identical edges every time. On my corpus that was 45 reproducible edges from the agent's wikilinks. LLM extraction is the right tool for *unstructured* text — raw conversations, scraped web — not for notes that already carry their own links. It's a workload decision, not philosophy; production stacks run both tiers.

**(b) "Does hybrid-RRF always beat plain vector search?"**
> No — and I measured it rather than assume. On my 19-page brain, pure vector hit recall@3 = 0.90, MRR 0.92; RRF *matched* recall but dropped MRR to 0.78 — the keyword arm missed every semantic query and fusing it demoted strong vector hits a rank. So I built a **self-tuning policy**: a cheap, deterministic metric scores keyword/vector/hybrid on a real golden set after *every* ingest and routes the agent to the winner. It auto-flipped `vector → hybrid` the moment the brain grew to a mixed 10-K corpus — no code change. RRF only wins when both arms are competitive; I never assume the published 83→95 lift.

**(c) "How do you make a bulk ingest into a memory store crash-resumable?"**
> Checkpoint every *expensive* layer, not just the outer loop. Mine has three on disk: per-file-chunk extraction (skip staged chunks), a fingerprint-keyed merge cache, and a verify-then-mark write checkpoint — a page's slug is recorded only after I confirm it's actually in the store. Killed mid-run, the resume re-embedded nothing already done — zero write batches on the second pass. The trap I hit: "the writes are idempotent" hides a full re-embed. Idempotent isn't cheap; checkpoint against confirmed durable state.

**(d) "Retrieval works — why are the answers still wrong?"**
> Generation is the bottleneck, not retrieval. On the same 10-K my hybrid grounded the answer-bearing section ~96% of the time, yet the *weak setup* answered correctly only ~25% (W2.7's vector baseline): **vector-only retrieval**, **thin snippet context** (`query --json` truncations, not full pages), and **a small local model** reading. Three assembly changes closed it to 15/16 — hybrid retrieval (keyword + vector RRF), injecting **full page bodies** via `gbrain get` instead of snippets, and **a capable reader** (Opus). The one remaining miss — a structural "where are the Notes located?" question — I fixed at **ingest** (joining PageIndex's page-ranges into the page body → 16/16), not by prompt-tuning. Reader gains are assembly, not wording.

**(e) "Tell me about a technical verdict you reversed."**
> Per-query routing — I killed it, then reversed myself, and the reversal is the better engineer. First pass: I built the oracle (route each query to its labeled-best arm) *before* writing any classifier; it tied global hybrid exactly (0.910), so even perfect play had zero headroom — reject. Then I caught that my own test was rigged: the corpus was vector-skewed (one query type), and the router fed GBrain's *raw* keyword arm, which its conjunctive FTS had crippled to 0.5 — so "route to keyword" could only lose. I OR-preprocessed the keyword query and built a type-balanced set, and the verdict flipped: router +0.039 grounding and +0.042 answer-quality on a *pinned Opus* generator, beating global even on a strong model. Lesson: build the ceiling before the classifier — but make sure the ceiling test isn't rigged by a broken arm or a one-type corpus. I shipped routing gated on the workload, not as a blanket default.

---

## 8. References

- **GBrain.** https://gbrain.homes/. MIT-licensed. Built by Garry Tan (Y Combinator) for his actual agents (OpenClaw, Hermes).
- **MarkTechPost — GBrain tutorial (May 22, 2026).** https://www.marktechpost.com/2026/05/22/a-step-by-step-coding-tutorial-to-implement-gbrain-the-self-wiring-memory-layer-built-by-y-combinators-garry-tan-for-ai-agents/.
- **Hermes Atlas — GBrain project page.** https://hermesatlas.com/projects/garrytan/gbrain.
- **Vectorize — What Is GBrain? Garry Tan's AI Agent Memory System Explained.** https://vectorize.io/articles/what-is-gbrain.
- **Cormack et al. (2009).** *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods.* SIGIR 2009. Foundational RRF paper.
- **MarkTechPost tutorial repo.** https://github.com/Marktechpost/AI-Agents-Projects-Tutorials. Contains `gbrain-tutorial.ipynb`.
- **ClaudioDrews — memory-os.** `https://github.com/ClaudioDrews/memory-os`. The 7-layer memory stack (built for the Hermes Agent) whose **Ground-Truth Hierarchy** principle Phase 7 leverages — injected memory is authoritative; the "memory-zero" anti-pattern re-establishes context every turn. NOT a library/MCP/REST; we port the *principle*, not the code.
- **BAI-LAB — MemoryOS.** `https://github.com/BAI-LAB/MemoryOS`. A *different* "MemoryOS" — segmented memory with a heat/eviction mechanism, leveraged in [[Week 3.5.95 - Self-Observability Memory]] Phase 7. Listed here only to flag the easy name collision.

---

## 9. Cross-References

- **Builds on:** [[Week 3.5.5 - Multi-Agent Shared Memory]] (multi-agent memory foundations); [[Week 3.5.8 - Two-Tier Memory Architecture]] (two-tier consolidation pattern); [[Week 3.5.9 - Requirement-Driven Memory Architecture]] (architecture-choice meta-skill — this chapter is Class 4).
- **Distinguish from:** [[Week 3.5.9 - Requirement-Driven Memory Architecture]] §2 three-class taxonomy (Class 1/2/3 are LLM-extracted; GBrain is Class 4 deterministic).
- **Connects to:** [[Week 6.65 - MCP Production Transports]] (GBrain exposes 74 MCP tools); [[Week 6.5 - Hermes Agent Hands-On]] (Hermes is one of GBrain's downstream consumers); [[Week 12 - Capstone]] (capstones with structured operational data can use GBrain as memory layer); [[Week 3.5.95 - Self-Observability Memory]] — the *sibling* memory-os leverage: Phase 7 here ports ClaudioDrews/memory-os's Ground-Truth Hierarchy, while W3.5.95 Phase 7 ports BAI-LAB/MemoryOS's heat/eviction.
- **Foreshadows:** continued production memory-layer evolution; expect GBrain v2 with broader typed-edge vocabulary (skills, contracts, transactions).

---

## What's Next

After W3.5.96: use GBrain alongside W3.5.8's two-tier OR W3.5.9's three-tier for operational data. Combine with W4 ReAct agent (W7 Tool Harness) for memory-augmented agent. Future: integrate with W3.5.95 PAI v7.6 self-observability for agent-self-knowledge graph.
