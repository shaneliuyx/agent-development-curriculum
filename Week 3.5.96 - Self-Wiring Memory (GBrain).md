---
title: "Week 3.5.96 — Self-Wiring Memory (GBrain — Garry Tan's Production Memory Layer for AI Agents)"
created: 2026-05-28
updated: 2026-06-07
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

**Result:** ~70 tools exposed; `put_page, add_link, add_timeline_entry, query, search` all present. The MCP path works from non-Claude-Code Python.

#### The agent

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

Brain = oMLX (no native tool-calls) → CodeAgent + use_structured_outputs_internally.
"""
from __future__ import annotations

import json
import os
import pathlib
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

        # 3. READ — query now runs over the reconciled graph.
        answer = agent.run(QUERY_TASK)
        print("\n>>> agent final answer:\n" + str(answer))


if __name__ == "__main__":
    main()
```

**Walkthrough:**
- **`ToolCollection.from_mcp` + filter.** smolagents loads GBrain's MCP tools straight in (needs `smolagents[mcp]`). We pass only the ~2 the agent calls — GBrain exposes ~70, and handing all to a 14B blows its context and confuses tool selection.
- **The two `@tool`s are where the intelligence lives.** `read_sources` does file I/O (the agent can't — sandbox blocks `pathlib`); `extract_pages` makes the one focused oMLX call that turns raw text into structured pages with wikilinks. The agent itself just loops `put_page` and calls `query`.
- **The extraction prompt is the load-bearing part.** It *hard-mandates* `[[wikilinks]]` with a worked example — because without that the model writes prose and the graph never wires (see Result).

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

### Phase 7 — Ground-Truth Hierarchy: memory-as-authoritative A/B [executed, measured]

**Goal:** leverage a principle from **ClaudioDrews/memory-os** — the *Ground-Truth Hierarchy*: injected memory is **authoritative**; an agent must not re-derive or re-fetch facts it already holds. memory-os names the anti-pattern **"memory-zero"** (re-establishing context from scratch every turn). GBrain is the authoritative store, so this is a natural fit: we A/B a 5-turn conversation that chains on overlapping entities (`Lin Zhao → Acme AI → its seed → investors`), comparing a memory-zero agent (re-query every turn) against a ground-truth agent (retrieve the subgraph once, inject it as authoritative, reuse).

> **Provenance (kept honest):** the *Ground-Truth Hierarchy* principle is **ClaudioDrews/memory-os**'s. The sibling heat/eviction mechanism (W3.5.95) comes from a *different* repo, **BAI-LAB/MemoryOS** — don't conflate them.

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
  reconcile_graph(); query

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
    NEEDED_TOOLS, QUERY_TASK, _EXTRACT_PROMPT, _GBRAIN, _server_env, reconcile_graph,
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

**Code (full source `src/policy_eval.ts`):**

```typescript
/**
 * policy_eval.ts — REAL-question policy generator (the trustworthy policy source).
 *
 * Replaces auto_eval.ts's known-item PROXY as the thing that writes the policy.
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
- **Re-runs on every ingest.** `run_auto_eval()` prefers `policy_eval.ts` whenever `data/golden_eval.json` exists, so the policy is re-selected against the *current* corpus each time; the loop tracks drift automatically.

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

| router | grounding@3 | Δ vs global |
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

**Answer-quality check — and a generation confound caught in the act.** Grounding takes the *max* coverage over the top-C, so it's blind to whether the *other* in-budget chunks are distractors. So we judged the answers too (`src/answer_route_ab.py`): generate from the global-hybrid context vs the routed context, LLM-judge against each question's `pass_criteria`. Run on **two generator tiers**:

| generator | global pass | routed pass | Δ | on differing-context Qs |
|---|---|---|---|---|
| local 14B (Qwen-Coder) | 1.000 | 0.750 | −0.250 | 1.000 → 0.500 |
| **Claude Opus 4.5** | 0.917 | 0.917 | **+0.000** | 0.800 → 0.800 |

The weak 14B *regressed* under routing — but Opus shows **Δ 0**, identical even on the questions whose context differed. The regression was the **generator's** context-composition sensitivity, **not** a retrieval effect: a weak model is rattled by a different (grounding-tied) context; a capable one extracts the answer regardless. This is the *confounding* trap named in `Engineering Decision Patterns` — scoring a retrieval choice by answer quality mixes in generation variance; pin the generator (here: a strong model) before attributing a delta to retrieval. **Verdict (this natural, vector-skewed corpus): keep the single global hybrid policy.** *Here* routing adds a classifier, a per-query branch, and a calibration surface for *zero* gain — and its one apparent win was a weak-model artifact. (Deterministic ceiling: `bun src/route_eval.ts`; answer A/B: `uv run python src/answer_route_ab.py` with `CHAT_MODEL` set.) **But that verdict is the *corpus's*, not the *principle's*** — the next subsection re-tests the honest version (route to the *fixed* keyword arm, on a workload that actually spans query types) and the result **reverses**: routing wins on both grounding and answer quality, even on a strong generator.

##### Re-tested with the keyword fix — routing accepted on a mixed-type workload (2026-06-07)

The rejection above rests on two things the *natural* corpus baked in: it is vector-skewed (one dominant query type), and `route_eval.ts` routed `kw` queries to the **raw** keyword arm — the one GBrain's conjunctive FTS had crippled (it scored `g@C:kw` 0.500, *worse* than hybrid's 0.925, so "route to keyword" could only lose). Fix both and the original design principle gets a fair trial: classify each query by type and send it to the arm that fits — `kw → key_pp` (the OR-preprocessed keyword arm), `vec → vector`, `mixed → hyb`. Three policies, balanced 24-Q set, deterministic classifier (24/24 vs the gold type label), `src/route_principle_ab.ts`:

**Grounding A/B (discounted grounding@C):**

| policy | grnd@C | g@C:kw | g@C:vec | g@C:mixed | Δ vs baseline |
|---|---|---|---|---|---|
| baseline (global `hyb`) | 0.823 | 0.925 | 0.745 | 0.763 | — |
| **router** (`kw`→`key_pp` · `vec`→`vector` · `mixed`→`hyb`) | **0.862** | **1.000** | 0.763 | 0.763 | **+0.039** |
| strengthened-global (`hyb` on OR-preprocessed query) | 0.837 | 1.000 | 0.745 | 0.658 | +0.014 |

The router strictly beats baseline on **+2 / 0 worse / 22 tie** — only **2 of the 24** questions move; the other 22 route to the arm baseline already used, so they're identical. Here are the **2 movers** (the rows where `router ≠ baseline`, from `bun src/route_principle_ab.ts`):

| question | routed type → arm | baseline `hyb` | router | gain |
|---|---|---|---|---|
| `Itochu Marubeni Mitsubishi Mitsui Sumitomo…` | `kw` → `key_pp` | 0.252 | **1.000** | +0.748 |
| `how the company guards against digital intrusions…` | `vec` → `vector` | 0.315 | **0.500** | +0.185 |

Both are answer pages that global hybrid's RRF **demoted** below the 3-chunk reader budget (so `hyb` scores them low — 0.252, 0.315); routing each to the arm its type favours recovers the page — one via the OR-preprocessed keyword arm, one via dense vector. Note the +2 are **not** both keyword queries: one `kw`, one `vec` — routing helps wherever the global arm buried the answer, not just on exact-token lookups. The whole +0.039 is just these two: `(0.748 + 0.185) / 24 = +0.039`; the other 22 contribute 0. (This is also why the `kw`-class *mean* moved `g@C:kw` 0.925 → 1.000 — nine of ten `kw` questions already scored 1.0 under hybrid; only `Itochu` was demoted, and `key_pp` fixes it.) The *strengthened-global* alternative (no router — just OR-preprocess the whole query before hybrid) edges baseline by only **+0.014** and still trails the router (0.862) by a wide margin: OR-joining the whole query slightly helps the keyword leg but does nothing for the dense leg, so it can't recover the `kw`-class queries the way a router pointed at `key_pp` does. So the principle **must** be honored by a router, not by strengthening the single global arm.

**Answer-quality A/B (entity coverage, pinned Opus 4.5 — `src/answer_principle_ab.py`):**

| policy | pass | p:kw | p:vec | p:mixed | Δ vs baseline |
|---|---|---|---|---|---|
| baseline (global `hyb`) | 0.792 | 0.800 | 0.800 | 0.750 | — |
| **router** | **0.833** | 0.900 | 0.800 | 0.750 | **+0.042** |
| strengthened-global | 0.833 | 0.900 | 0.800 | 0.750 | +0.042 |

The edge **survives a strong generator** (+0.042 on Opus, on par with the grounding gap): the router fixes answers global hybrid gets wrong — `Itochu…` F→**P**, `Item 8 Notes` F→**P** — net +1 question after one regression (`Item 1C` P→F), with ~1 question of Opus judge variance at temp 0. Modest, but the *direction* is the opposite of the natural-set `Δ 0`: there routing changed nothing real on a one-type corpus; here, on a workload that spans types, routing recovers compromised queries at *answer* time, not just at grounding time — Opus still cannot extract an answer from a wrong-context chunk set. (An earlier, corpus-overfit keyword stop-list had inflated this to +0.083; the generic stop-list gives the honest +0.042.)

**Why router and strengthened-global show an *identical* +0.042 here — and why it isn't a tie.** Both pass **20/24**, but on *different* questions: the router passes `the part of the filing that lists what could go wrong` (F for strong_g) while strong_g passes `which venture firm is the angel investor` (F for the router). The two diffs cancel, so the *aggregates* coincide even though the underlying answers don't. And the router's loss is **not** a mis-route: it correctly classified `which venture firm…` as `vec → vector`, and vector retrieved *both* answer pages (`ridgeline-capital`, `dev-patel`) — but ranked `dev-patel` at **#4**, one slot outside the `C=3` reader budget, so the generator saw Ridgeline but not Dev Patel and couldn't name the investor. `strong_g` happened to rank `dev-patel` at #3. It's a **rank-cutoff near-miss at `C=3`** (the very demotion effect `discounted grounding@C` measures) on a 2-hop question that needs two entities in the same 3-slot window — not a routing mistake. The lesson: a binary pass-rate at n=24 is **too coarse to rank router vs strengthened-global** — single-slot rank-boundary flips, not equivalence. The arms are separated by the *continuous, deterministic* metric, not this one: on **grounding** the router (0.862) clearly beats strengthened-global (0.837). So the answer A/B establishes only that *both beat baseline*; the choice between them is made on grounding + the architectural argument (strong_g can't recover the `kw`-class the way a `key_pp` route can), not on these identical pass rates.

**Refined verdict — routing is worth building, conditionally.** Per-query routing pays iff **three gates all hold**: (a) the traffic genuinely **spans query types** (keyword-focused *and* semantic), (b) the keyword arm is **OR-preprocessed** (else its target is the crippled raw arm and routing can only lose), and (c) a **cheap type-classifier** can actually detect the type. All three held here → +0.039 grounding, +0.042 answer quality. On the production brain as-is (vector-skewed, single dominant type) gate (a) fails, so the earlier "keep global hybrid" still stands *for that corpus* — and precisely so: a router doesn't *lose by design* there (it can always default to hybrid). The realizable gain decomposes as **(oracle − global) − classifier_error_cost**. On a single-type corpus the first term is **0** (oracle = global, the 0.910 = 0.910 tie), so a *perfect* router merely **ties** and a *real* classifier nets **negative** — its mis-routes have no headroom to offset them. All-risk-no-reward, so don't route. The headroom is the *budget* a router has to spend on its own classifier errors: 0 on single-type (can't afford any), +0.065 oracle on the mixed set (enough to cover a good classifier and still net +0.039 / +0.042). The honest scope: the classifier is 24/24 only because this set is built type-separable (`kw` = token-lists, `vec` = prose); real queries blur that, so +0.042 is the **strong-classifier ceiling** — production gain is ≤ that and shrinks with classifier error. Net: don't reject the principle — gate it on the workload. (Grounding A/B: `GOLDEN_EVAL=data/golden_balanced.json bun src/route_principle_ab.ts`; answer A/B: `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/answer_principle_ab.py`.)

#### Entity-aware assembly — one-hop graph expansion (2026-06-07)

Routing fixes *which arm* retrieves; it can't fix a **2-hop question** where the answer needs **two** entity pages in the same `C`-chunk budget and retrieval ranks the second one at `C+1`. We saw this in the answer A/B: `which venture firm is the angel investor associated with` retrieved both `ridgeline-capital` (rank 3, in budget) and `people/dev-patel` (rank 4, **out**) — the generator saw the firm but not the investor. GBrain is a knowledge graph, so there's a cheap fix the chapter's whole premise points at: `dev-patel` is a **1-hop neighbor** of the in-budget `ridgeline-capital` (`invested_in` / `founded` edges). Pull the neighbor's page into the context — one edge traversal, no NER. Assembly becomes *entity-aware*: it guarantees the graph-completion of an in-budget entity rather than blindly taking the top-`C` by score.

The rule is deliberately high-precision: pull a demoted page **only** when it is *both* graph-connected to an in-budget page *and* itself retrieved-but-demoted (in the top-`K` pool, ranked past `C`). That keeps single-hop queries at exactly `C` and spends extra budget only along a real edge to an already-relevant page.

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

##### Decision — measured, NOT shipped to production (2026-06-07)

Graph expansion *works*, and it is left in the repo as a tested, reproducible module (`src/assembly.ts` + the two A/B probes) — but it is **deliberately not wired into the production actuator** (`query_policy.ts`). The benefit does not clear the cost-and-complexity bar. The full reasoning, because "we built it and chose not to ship it" is itself the lesson:

1. **The benefit is marginal and fragile.** It fixed exactly **one** of 24 questions (`Quanta Labs`, +0.042 overall). That is the *same magnitude as the judge's run-to-run variance* (~1 question at temp 0 on Opus) — so the gain is barely separable from noise. A continuous metric can't even see it: lexical entity coverage was 0.986 → 0.986, because related pages cross-name each other. A win that only one expensive measurement can detect, and only by one question, is not a robust production signal.

2. **It fixes only one of the two failure modes.** Graph expansion is additive — it *adds* the missing neighbor page. That fixes **missing-neighbor** 2-hop failures (Quanta's deal page was retrieved-but-demoted, one edge away). It does **nothing** for **distractor-dominated** failures: the motivating `which venture firm` question stayed `F`, because two `northstar` pages outrank `ridgeline` and adding `dev-patel` doesn't remove the distractors. The more common and more damaging failure mode needs *rerank / dedup* (which **removes** a wrong page, net-zero token cost), not expansion. So the feature addresses the cheaper half of the problem.

3. **The runtime cost is small here but *unbounded in general*.** The DB side is free (6 indexed `getLinks`/`getBacklinks` reads, ~ms, no LLM). The real cost is **generator input tokens**: every fired query injects the pulled neighbor's *full page body*. On this corpus the pulled pages were tiny entity pages (+0.46 pages ≈ **+0.1%** tokens — `775K` vs `773K` over the answer A/B). But that is a property of *this* workload, not the mechanism: pull a neighbor that happens to be a **30K-token 10-K section** and every fired query pays 30K extra input tokens. The benefit is a flat ~1 question; the cost is **proportional to neighbor page size** — they don't scale together, and on a document-heavy corpus the trade goes sharply negative. (For scale: the answer A/B itself runs ~**1.5M input tokens** because full 10-K bodies are injected uncapped — a stark reminder that the real budget is *tokens*, not *chunks*. Cap page bodies with `MAX_BODY_CHARS` before any such eval.)

4. **It adds a production stage, a switch, and a calibration surface** (`maxPull`, `poolOnly`, the pull condition) — the same complexity tax that gated per-query routing on single-type corpora. A marginal, fragile, one-failure-mode benefit does not earn that surface.

**Verdict:** keep `assembly.ts` as a documented experiment; do not run it in the live path. **Revisit only if** a real workload is (a) heavy on *missing-neighbor* multi-hop questions AND (b) the neighbor pages are small (entity pages, not document sections) AND (c) a cheaper fix (rerank-to-swap-a-distractor, or a slightly larger `C`) has been ruled out first. On this corpus none of those hold, so the honest engineering call is: **measured, shelved.** This is the chapter's "what NOT to build" discipline applied to our own feature — the experiment that earns its place by telling us *not* to ship.

#### Block C — `query_policy.ts`: the actuator

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

| arm | grounding@3 (`tenk`, 12 Q) | answer pass-rate (`tenk`, 12 Q) |
|---|---|---|
| keyword | 0.250 | 0.167 |
| vector | 0.858 | 0.917 |
| **hybrid** | **0.927** | **1.000** |

> **Provenance note (re-verified 2026-06-07, `results/verify_arch.out`).** Both columns are **current**: re-run uncapped on Opus 4.5 after the corpus picked up the combined **PageIndex+GBrain** ingest (the `**Location:**` breadcrumbs — see the combined-solution subsection). That ingest is what moved the numbers — keyword/vector grounding rose (`vector 0.816 → 0.858`) *and* their answers rose with them (`vector pass 0.750 → 0.917`, `hybrid 0.917 → 1.000`), which is why the calibrator went **up**, not down. The earlier worry that the drift might break the architecture was the right thing to check and it resolved favourably: grounding and answers moved *together*.

- **Calibrator** — `corr(discounted grounding@C, answer-pass) = +0.820` (36 cells, re-verified 2026-06-07). The cheap, deterministic metric strongly predicts the expensive answer-judge.

    > **Why "0-LLM selector / no judge in the hot loop" is the keystone — in detail.** The SELECTOR runs on **every ingest** — that's the hot loop. It picks the search policy by computing `discounted grounding@C` per arm: substring coverage × a position discount, a pure deterministic calculation with **no model call**. The tempting alternative is to score each arm with an LLM *answer-judge* on every ingest — and it's wrong three ways. **(1) Cost:** a judge call per arm × per question × every ingest meters the self-tuning loop with API spend that scales with corpus churn (and, as this very phase showed, a single uncapped answer-eval is ~1.5M tokens). **(2) Latency:** ingest would block on dozens of generate-then-judge round-trips before the policy could update. **(3) Confounding:** judging *retrieval* by *answer quality* folds generation variance into a retrieval decision, so a policy could flip on model noise rather than a real retrieval change — the exact trap that sank the LLM-in-selector idea and produced the weak-model confound in the routing A/B. The calibrator `r = +0.820` is what **licenses** the cheap proxy: because grounding predicts the judge strongly, you run the deterministic metric *continuously* in the loop and reserve the expensive judge for **event-triggered** checks only — the GATE (on a policy flip) and the CALIBRATOR itself (on a domain shift). **Cheap-and-continuous in the hot path; expensive-and-rare on the edges.** If `r` were low, that split would collapse: you couldn't trust the cheap metric, the judge would have to move into the hot loop, and the self-tuning economics (free re-tune on every ingest) break. So `r` isn't a vanity statistic — it is the single number that determines whether the architecture is *affordable*.

- **Selector validity** — the max-grounding arm (`hybrid`) is also the answer-quality winner (`1.000` pass), and the ordering `keyword < vector < hybrid` holds on **both** axes (grounding `0.250 < 0.858 < 0.927`; answer `0.167 < 0.917 < 1.000`) → CONFIRMED.
- **The residual (r=0.820, not 1.0) is instructive — and the gap it once flagged is now *closed*.** Earlier *"Where are the Notes to Consolidated Financial Statements located?"* grounded **1.000 on all three arms yet the answer FAILED** for every arm: a **false-positive grounding** — the chunks (`sections/brk_0034/0039/0040`) contained the `Item 8` / `Notes to Consolidated` substrings, but as a buried page-header marker, not a clean "*the Notes are in Item 8, pages 99–147*" statement. The **combined PageIndex+GBrain ingest** (see the combined-solution subsection) fixed exactly this: every section now carries a `**Location:** Item 8 — Notes to Consolidated Financial Statements · pages 99–147` breadcrumb *in its body*, so the shipped policy (`hybrid`) and `vector` now **answer it correctly** — only the `keyword` arm still fails (it retrieves the body without surfacing the location line at rank 0). What remains of the residual `r=0.820 < 1.0` is now a *mix*: keyword's leftover false-positives, **plus the reverse case** — the strong generator passing from *low*-grounding context (the 'not-so-secret weapon' question: `vector` grounds only 0.375 yet the answer PASSES — a false *negative* for the metric). The metric↔answer agreement **rose** (0.719 → 0.820) precisely because the structural fix landed: once the location is *in the page*, the cheap substring metric and answer quality line up. The residual is where they still diverge — a retrieval-*representation* effect (now partly a generator-strength effect), not pure noise.

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

The orchestration scripts consume this primitive: `policy_eval.ts` (selector — writes the policy), `route_eval.ts` (routing headroom + per-arm dump), `route_eval_kwpp.ts` + `route_principle_ab.ts` (the keyword-revival and per-query-routing A/Bs), `answer_route_ab.py` / `answer_principle_ab.py` (answer A/Bs), `verify_arch.py` (calibrator + selector audit). **What NOT to build** (each measured into the ground this phase): an LLM judge in the every-ingest selector (confounds retrieval choice with generation variance, *and* meters the loop); a rank-blind metric (can't see RRF demotion); a hand-picked `C` (scores a context the model never reads); **entity-aware graph expansion in the live path** (fixes only 1/24 — judge-noise magnitude — and only *missing-neighbor* 2-hop, not distractor failures; runtime token cost is unbounded in neighbor page size; kept as a tested module, shelved — see "Decision — measured, NOT shipped"). Most of the win was **deletion** — the final system is simpler than the naïve one *and* better, because each cut piece failed a measurement.

**What we DID build (gated): the per-query router.** Unlike the shelved items above, per-query routing earned its place — it is shipped in `query_policy.ts` behind `QUERY_ROUTER`, **default-off**. On a single-type corpus the oracle ceiling equals global hybrid (Δ0), so you leave it off; once the workload spans query types and the keyword arm is OR-preprocessed it **reverses to +0.039 grounding / +0.042 answer** and you switch it on. So the router is not a "don't build" — it's a "build it, gate it on the workload."

#### Block E — the reader is the lever, measured (2026-06-07)

Retrieval is solved here (hybrid grounding ~0.93); the open question is the *generation* step — W2.7's 0.96 grounding → 0.25 answer gap, and the "Notes" question that grounds 1.000 yet answers 0/3. So we fixed retrieval (always the winning arm = hybrid, **full `gbrain get` bodies**) and A/B'd the READER STRATEGY against the golden `pass_criteria` (`src/reader_ab.py`; gen = the reader under test, judge = a fixed strong grader so the verdict isn't self-graded):

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

#### Running reference — scripts, env, parameters

Every Phase-9 script is parameterised by environment variables (and a couple by argv). This is the canonical "how do I run it" table — what each needs, and in what order.

**Services + shell (run all commands from `~/code/agent-prep/lab-03-5-96-gbrain/`):**
- **`gbrain-pg`** — Postgres+pgvector container. `GBRAIN_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gbrain`.
- **oMLX `:8000`** — local MLX server. Serves **embeddings** (`OLLAMA_BASE_URL`/`OLLAMA_API_KEY`) for the vector/hybrid arms, AND the local **14B chat** model.
- **VibeProxy `:8317`** — OpenAI-compatible proxy to **cloud Claude** (`OPENROUTER_BASE_URL`/`OPENROUTER_API_KEY=vibeproxy`); used as the answer generator / judge.
- Load the lab `.env` (`set -a; . ./.env; set +a`) and put `~/.bun/bin` on `PATH`. `.env` holds `GBRAIN_DATABASE_URL`, `OLLAMA_*`, `LLM_*` (oMLX key + local chat model), `OPENROUTER_*`.

| script               | role                                  | params / env (default)                                                                                  | services                 | run                                                                                    |
| -------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------ | -------------------------------------------------------------------------------------- |
| `grounding.test.ts`  | unit tests for the metric             | —                                                                                                       | none                     | `bun test src/grounding.test.ts`                                                       |
| `policy_eval.ts`     | **SELECTOR** — write the policy       | `POLICY_K` (5), `POLICY_C` (3)                                                                          | pg + oMLX embed          | `bun src/policy_eval.ts` · sweep: `POLICY_C=5 bun src/policy_eval.ts`                  |
| `query_policy.ts`    | actuator — global policy **or** per-query router | argv `"<query>" [limit=5]`; **`QUERY_ROUTER`** (off→global policy · on→type-route)        | pg + oMLX embed          | global: `bun src/query_policy.ts "Who is anchoring acme-seed?" 3` · router: `QUERY_ROUTER=on bun src/query_policy.ts "Item 1C Cybersecurity" 3` |
| `query_routing.ts`   | **ROUTER brain** — type classifier + kw OR-preprocess (shared, no main) | — (imported)                                                       | none                     | imported by `query_policy.ts` + `route_principle_ab.ts` (one canonical classifier → production == tested) |
| `route_eval.ts`      | routing headroom + **dumps**          | `POLICY_K` (5), `POLICY_C` (3)                                                                          | pg + oMLX embed          | `bun src/route_eval.ts` → writes `results/route_slugs.json`, `results/arm_scores.json` |
| `route_eval_kwpp.ts` | keyword-revival probe (raw vs OR-preprocessed) | `GOLDEN_EVAL`, `POLICY_K` (5), `POLICY_C` (3)                                                  | pg + oMLX embed          | `GOLDEN_EVAL=data/golden_balanced.json bun src/route_eval_kwpp.ts`                     |
| `route_principle_ab.ts` | **3-way routing A/B** (grounding) — router vs global vs strengthened-global | `GOLDEN_EVAL`, `POLICY_K`/`_C`; writes `results/principle_slugs.json`        | pg + oMLX embed          | `GOLDEN_EVAL=data/golden_balanced.json bun src/route_principle_ab.ts`                  |
| `assembly.ts`        | **ASSEMBLY lib** — 1-hop graph expansion (`graphExpand`, shared, no main) | — (imported); uses `getLinks`/`getBacklinks`                                  | none                     | imported by `assembly_graph_ab.ts` (the entity-aware-assembly fix)                     |
| `assembly_graph_ab.ts` | graph-expansion A/B (coverage) + slug dump | `GOLDEN_EVAL`, `POLICY_K`/`_C`, `MAX_PULL` (2); writes `results/assembly_slugs.json`           | pg + oMLX embed          | `GOLDEN_EVAL=data/golden_balanced.json bun src/assembly_graph_ab.ts`                   |
| `load_brk_corpus.py` | ingest the 10-K corpus                | `BRK_CORPUS` (path), `SLUG_PREFIX` (`sections`)                                                         | pg + oMLX embed          | `uv run python src/load_brk_corpus.py`                                                 |
| `answer_route_ab.py` | answer A/B (routing)                  | `OPENROUTER_BASE_URL`/`_API_KEY`, `CHAT_MODEL`, `MAX_BODY_CHARS` (0); reads `route_slugs.json`          | pg + chat (`:8317`)      | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/answer_route_ab.py`             |
| `answer_principle_ab.py` | answer-quality A/B (3 policies, entity coverage) | `CHAT_MODEL`, `MAX_BODY_CHARS` (0); reads `principle_slugs.json`                            | pg + chat (`:8317`)      | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/answer_principle_ab.py`         |
| `assembly_answer_ab.py` | graph-expansion answer A/B (plain vs expanded) | `CHAT_MODEL`, `MAX_BODY_CHARS` (0); reads `assembly_slugs.json`                              | pg + chat (`:8317`)      | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/assembly_answer_ab.py`          |
| `verify_arch.py`     | **CALIBRATOR** — corr(metric, answer) | `OPENROUTER_BASE_URL`/`_API_KEY`, `CHAT_MODEL`; reads `arm_scores.json`                                 | pg + chat (`:8317`)      | `CHAT_MODEL=claude-opus-4-5-20251101 uv run python src/verify_arch.py`                 |
| `reader_ab.py`       | reader A/B (fixed retrieval)          | **`GEN=`/`JUDGE=`** preset (`haiku`/`opus`/`14b`/`qwen`), `MAX_BODY_CHARS` (0); reads `arm_scores.json` | pg + gen/judge endpoints | `GEN=14b JUDGE=opus uv run python src/reader_ab.py`                                    |

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
- **mean grounding@3** — per-arm average of the cheap discounted grounding@C=3 metric.
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
