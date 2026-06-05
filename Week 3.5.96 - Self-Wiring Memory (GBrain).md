---
title: "Week 3.5.96 — Self-Wiring Memory (GBrain — Garry Tan's Production Memory Layer for AI Agents)"
created: 2026-05-28
updated: 2026-06-04
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

W3.5.9 introduced the three-class memory taxonomy (1-tier atomic-fact / 2-tier consolidation / 3-tier graph) + HyperMem L3 as the worked-example graph-tier implementation. GBrain — built by Garry Tan (Y Combinator CEO) to run his actual agents — introduces a 4th class: MARKDOWN-FIRST, deterministic-extraction graph. The thesis: most agent memory is ALREADY structured (people, companies, events, meetings). Markdown can carry that structure NATIVELY; deterministic regex + parser passes can extract typed edges with ZERO LLM calls. Result: reproducible, auditable, cheap entity graphs. Measured production impact: 83% → 95% Recall@5 via HNSW + Postgres keyword RRF on a 240-page corpus. Powers Garry Tan's OpenClaw + Hermes deployments at 146K-page scale. For local-first engineers, GBrain is the "production memory layer you can self-host on $5/mo Postgres." Engineers who can articulate "deterministic extraction beats LLM extraction when the data structure is already known" move 10× faster than engineers who reflexively LLM-extract everything.

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

Create `~/code/agent-prep/gbrain/.env` with the block below, then fill the two
`<…>` placeholders. **Required** = the lab won't run without it; **optional** =
enables vector/hybrid search and query expansion (skip and you still get keyword
search). `.env` holds secrets — it's already in GBrain's `.gitignore`; never commit it.

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

**Goal:** the transferable skill behind this whole chapter — a **standalone agent
you build** (here: smolagents, *not* Claude Code) uses GBrain as its memory layer
over **MCP**: read raw → LLM-extract structured pages → `put_page` → `query`. Lab
repo: `~/code/agent-prep/lab-03-5-96-gbrain/` (full source + `RESULTS.md`).

**Framework choice (researched).** The agent's brain is local **oMLX, which has no
native tool-calling**. smolagents' `CodeAgent` — the LLM writes Python that calls
tools — is purpose-built for that; it doesn't need function-calling. (PydanticAI and
the OpenAI Agents SDK are cleaner/typed but *require* a tool-calling model — you'd
route the brain through VibeProxy→Haiku for those.) `use_structured_outputs_internally=True`
sidesteps oMLX's `<code>` parsing (smolagents issue #1851).

**Design: thin agent, fat tools.** A 14B can't reliably read files **and** write a
good extractor **and** compose markdown in one code loop — and the `CodeAgent` sandbox
blocks `pathlib`/`json`. So the hard work lives in tools (`read_sources`,
`extract_pages`); the agent's own code is ~4 lines of orchestration.

#### Probe first — can plain Python drive GBrain's MCP?

The smallest proof (`src/probe_mcp.py`, core): a Python MCP client spawns `gbrain
serve` over stdio and lists its tools. **An MCP server is a separate process — it
does NOT inherit your shell env**, so DB + oMLX vars are injected at spawn:

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

Brain = oMLX (no native tool-calls) → CodeAgent + use_structured_outputs_internally.
"""
from __future__ import annotations

import json
import os
import pathlib

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
        if f.is_file():
            parts.append(f"===== {f.relative_to(SOURCES.parent)} =====\n{f.read_text()}")
    return "\n\n".join(parts)


@tool
def extract_pages(raw: str) -> list:
    """Turn raw source text into structured GBrain pages via the local LLM.

    Args:
        raw: concatenated raw source text (from read_sources).
    """
    client = OpenAI(base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                    api_key=os.getenv("LLM_API_KEY", "dummy"))
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "Qwen2.5-Coder-14B-Instruct-MLX-4bit"),
        messages=[{"role": "user", "content": _EXTRACT_PROMPT.replace("{raw}", raw)}],
        temperature=0.0, max_tokens=4000, response_format={"type": "json_object"})
    data = json.loads(resp.choices[0].message.content or "{}")
    return [p for p in data.get("pages", []) if p.get("slug") and p.get("content")]


def _server_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = _BUN_BIN + os.pathsep + env.get("PATH", "")
    for k in ("GBRAIN_DATABASE_URL", "OLLAMA_BASE_URL", "OLLAMA_API_KEY"):
        if (v := os.getenv(k)):
            env[k] = v
    return env


TASK = """Build the brain, then answer a question, using ONLY the provided tools:
1. raw = read_sources()
2. pages = extract_pages(raw)
3. for each page in pages: call put_page(slug=page["slug"], content=page["content"])
4. answer = query(query="Who is anchoring the acme-seed round and on what terms?")
5. return answer via final_answer.
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
        answer = agent.run(TASK)
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

**Goal:** confirm the `[[wikilinks]]` the agent wrote (Phase 3) became typed graph edges — deterministically, with zero LLM calls. **Run after Phase 3** (it operates on the pages the agent produced).

```bash
export GBRAIN_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gbrain
gbrain extract links --source db     # backfill typed edges from the agent's wikilinks
gbrain stats                         # pages · links · embedded chunks
gbrain graph-query deals/acme-seed   # typed-edge traversal
```

> **Gotcha:** there is no `gbrain ingest` (it's `import`) and no `gbrain entity` (use `graph-query` / `backlinks` / `get`). `links: 0` means either you skipped `extract links` **or** the agent's pages had no wikilinks — the real failure we hit (BCJ Entry 5).

**Result (measured):** on the agent's output — **10 pages → `extract links` created 11 typed edges**. `gbrain graph-query deals/acme-seed` traverses `--invested_in->` / `--works_at->` / `--mentions->` across people + companies (depth 1–5). **Deterministic:** re-running `extract` yields identical edges (regex/parser, zero LLM calls). The first run produced `links: 0` until the extraction prompt was made to mandate wikilinks (BCJ Entry 5) — *graph quality = extraction quality.*

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
const GB = "/Users/yuxinliu/code/agent-prep/gbrain/src";

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

## 6. Bad-Case Journal (real, observed)

_Observed during the real Phase-1 → Phase-6 runs (GBrain 0.42.25.0):_

**Entry 1 — `llama-server` provider is a catch-22 for registry-known embed models (OBSERVED).** `--embedding-model llama-server:bge-m3` (and `:nomicai-modernbert-embed-base-bf16`) refuses *both* ways: **with** `--embedding-dimensions` → "does not support custom dimensions N (this model only emits its default vector size)"; **without** → "llama-server requires --embedding-dimensions <N> (user-driven recipes have no default dimension)." No value satisfies both → init impossible.
*Fix:* use the **`ollama` provider** pointed at oMLX (`OLLAMA_BASE_URL=http://localhost:8000/v1`, `OLLAMA_API_KEY=<key>`, `--embedding-model ollama:<model>`, **no** `--embedding-dimensions`) — it *probes* the endpoint for the dim instead of demanding/rejecting it. (Worth a GBrain issue; strip keys before filing.)

**Entry 2 — init is stateful + greedy; a botched first run poisons every retry (OBSERVED).** Three compounding traps: (a) `--supabase` runs the *interactive Supabase flow* and ignores `GBRAIN_DATABASE_URL` — use `--url`; (b) a present `OPENROUTER_API_KEY` makes init **auto-pick openrouter for embeddings** (probe failed 404 on a dummy key) even with `--embedding-model` set — keep it commented until post-init; (c) a wrong first init persists `~/.gbrain/config.json` + a baked vector-column width, so re-init fails citing the *stale* dimension.
*Fix (0 pages → safe):* `DROP DATABASE gbrain; CREATE DATABASE gbrain;` + `rm ~/.gbrain/config.json`, then re-init. Lesson: **GBrain init is stateful and greedy — reset clean if anything looks off, and read the "Using …" line, not the green migration checkmarks.**

**Entry 3 — `gbrain` not found after `bun link` (OBSERVED).** `bun link` symlinks the CLI into `~/.bun/bin` but does not add it to PATH; the installer often doesn't persist the PATH line either.
*Fix:* `echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc`. Tell-apart: `ls ~/.bun/bin/gbrain` exists ⇒ pure PATH issue, not a broken install.

**Entry 4 — trying to hand-format every source type into brain pages (DESIGN anti-pattern).** Emails, tweets, and meeting transcripts each have a different shape; writing a per-format converter (or authoring the 50 pages by hand) does not scale and is *not* GBrain's model.
*Root cause:* mistaking who owns the structured layer. GBrain splits **raw sources** (immutable, any format, in `sources/`) from **the brain** (two-layer pages the **agent** writes).
*Fix:* never author structured pages manually — drop raw under `sources/` (or `gbrain capture`), then let the agent convert via **ingest skills** (`meeting-ingestion`, `article-enrichment`, `voice-note-ingest` → `put_page`/`add_link`) or, in production, the credentialed **integration recipes** (`email-to-brain`, `x-to-brain`, `meeting-sync`). The agent is the universal formatter; you curate. (Drove the Phase 2 rewrite.)

**Entry 5 — the agent stored pages fine but the graph had zero edges (OBSERVED, Phase 3).** A smolagents `CodeAgent` (oMLX) drove GBrain over MCP and wrote 5 well-formed pages via `put_page`, yet `gbrain extract links` reported `Links: 0`.
*Root cause:* the LLM extraction wrote entity mentions as **plain prose** ("Alice Chen, founder of Acme AI") and used `<!-- timeline -->` instead of `---`, so there were no `[[wikilinks]]` to extract. The framework + MCP plumbing worked; the *contract* didn't.
*Fix:* the extraction prompt must **hard-mandate** path-qualified `[[dir/slug]]` wikilinks with a worked example + "a page with zero wikilinks is invalid" → `Links: 0 → 11`. **Graph quality = extraction quality; measure edges, not pages.**

**Entry 6 — fully-autonomous `CodeAgent` failed on a 14B (OBSERVED, Phase 3).** Asking the agent to read files + write an extractor + compose markdown in one code loop produced a naive regex placeholder + `InterpreterError: import pathlib not allowed` (the CodeAgent sandbox blocks `pathlib`/`json`).
*Fix:* **thin agent, fat tools** — move file I/O and extraction into `@tool`s (`read_sources`, `extract_pages`); the agent only orchestrates. Also: filter `ToolCollection.from_mcp` to the ~few tools needed (GBrain exposes ~70; a 14B drowns), depend on `smolagents[mcp]` (mcpadapt), pass DB/oMLX env via `StdioServerParameters(env=…)` (an MCP server is a separate process), and use `use_structured_outputs_internally=True` (oMLX has no native tool_calls). Lab: `~/code/agent-prep/lab-03-5-96-gbrain/`.

**Entry 7 — graph reads as "built" but has no new edges (OBSERVED, Phase 6).** After re-ingesting an expanded corpus, `gbrain stats` showed **19 pages but Links: 11** — unchanged from the 10-page run — even though the new pages' text held ~68 `[[wikilinks]]`.
*Root cause:* self-wiring is a **batch extraction pass, not a `put_page` side-effect**. Pages written over MCP live only in Postgres; bare `gbrain extract links` walks a brain *directory* of `.md` files and errors `No brain directory configured`, so extraction never ran on them.
*Fix:* `gbrain extract links --source db` re-parses the stored `compiled_truth`/`timeline` columns → `created 34 links from 19 pages` → 45 total. Do **not** gate on `pages.links_extracted_at` — that column tracks the file-source path only and stays null after DB-source extraction.

**Entry 8 — keyword-vs-hybrid benchmark shows zero difference (OBSERVED, Phase 6).** `gbrain search "<q>"` and `gbrain query "<q>"` returned byte-identical rankings *and* scores; an A/B "keyword vs hybrid" read as "no lift."
*Root cause:* both subcommands fall through to the **same handler** (`src/cli.ts:771-772 — case 'search': case 'query':`). The CLI has no pure-keyword command; `keywordSearch` is an internal building block *inside* the hybrid pipeline, not a separate path.
*Fix:* benchmark at the **engine layer** via `src/core/search/eval.ts:runEval()` with `strategy: 'keyword'|'vector'|'hybrid'`, bootstrapping engine + gateway exactly as the CLI does. **Never A/B retrievers through the CLI.**

**Entry 9 — hybrid-RRF underperformed pure vector (OBSERVED, Phase 6).** On the 19-page brain, RRF scored recall@3 = 0.90 but MRR **0.78** — *worse* than pure vector (0.90 / **0.92**). The expected 83→95 RRF win was a slight regression instead.
*Root cause:* the keyword arm missed all four purely-semantic queries (no lexical overlap); RRF fusion folded that dead arm back in, demoting correct vector hits a rank (`dinner at Tartine` vector @1 → hybrid @3). RRF helps only when *both* arms are individually competitive and complementary.
*Fix:* on a small, semantic-heavy corpus, **prefer pure vector**; reserve RRF for corpora with enough exact-term / proper-noun traffic that keyword earns its weight. Always measure on your own corpus before quoting the published lift.

**Entry 10 — retrieved "context" is just a slug + one-line snippet; the LLM can't answer (OBSERVED, Phase 7).** The first Ground-Truth A/B fed `gbrain query --json` straight to the model, which replied "the context shows `[[people/lin-zhao]]` but doesn't include the actual content."
*Root cause:* `gbrain query` returns ranked **snippets** (slug + compiled-truth first line) for *display*, not full page bodies for grounding.
*Fix:* use `query` only to *rank* slugs, then pull each body with `gbrain get <slug>` before injecting. Retrieval (rank) and grounding (fetch) are two separate calls.
**Entry 11 — the chat model refuses the task, insisting it's "Claude Code" (OBSERVED, Phase 7).** With the task instruction in the `system` role, VibeProxy→Claude answered every turn with "I'm Claude Code… I can't help with questions about people."
*Root cause:* VibeProxy fronts the Claude-Code CLI identity and **overrides the caller's `system` prompt**, so a "you are a knowledge-base assistant" system message is discarded and the model falls back to refusing non-coding requests.
*Fix:* put the instruction *and* the grounding notes in the **USER** message as a document-Q&A task ("using ONLY these notes, answer…"); don't depend on `system`. The same model then answers correctly.

_Projected (to confirm during Phases 3–6):_

- **Phase 3 — Agent over-relies on GBrain for general knowledge.** Likely surface: agent uses GBrain context for questions GBrain shouldn't know (general world facts). Fix: agent prompt distinguishes "questions about MY people/companies/events" (use GBrain) vs "general questions" (use base LLM knowledge).
- **Phase 4 — Markdown convention mismatch.** Likely surface: your `# Meeting with Alice` doesn't trigger the `attended` edge because GBrain's parser expects `# Dinner with @alice`. Fix: read GBrain's parser regex; adopt the `@handle` convention consistently.
- **Phase 5 — Synthesis layer hallucinates a "we don't know" caveat that's wrong.** Likely surface: gap-flagging logic uses a heuristic that triggers on missing entities even when the answer IS in the corpus. Fix: synthesis prompt includes the retrieved citations explicitly; gap-flag triggers only when retrieval returned zero matches.
- **Phase 6 — RRF lift smaller than 12pts.** Likely surface: corpus too short OR queries too name-specific (both retrievers already agree). Fix: expand corpus to 200+ pages OR pick queries with mix of semantic + exact-phrase types.

---

## 7. Interview Soundbites (2-3 entries — SPEC)

- **Planned Soundbite 1 — "Why deterministic extraction over LLM extraction?"** Anchors: §2.1 + §2.4. 70 words: when data is already structured (Markdown notes, calendar events, contact lists), deterministic parsing is cheap, reproducible, auditable. LLM extraction is the right tool for UNSTRUCTURED text (raw conversations, scraped web). GBrain's choice is workload-driven, not philosophical. Many production stacks use both: GBrain for structured operational data + LLM-extracted graphs for unstructured conversations.
- **Soundbite 2 — "Does hybrid-RRF always beat plain vector search?"** Anchors: Phase 6 measurement. ~70 words: No — and I measured it rather than assume. On my 19-page brain, pure vector hit recall@3 = 0.90, MRR 0.92; RRF *matched* the recall but dropped MRR to 0.78, because the keyword arm missed every purely-semantic query and fusing it demoted strong vector hits a rank. RRF only wins when both arms are individually competitive — on a small, semantic-heavy corpus it's net-negative. I don't trust the published 83→95 lift without re-running on my own corpus.
- **Planned Soundbite 3 — "Where does GBrain fit vs HyperMem in your taxonomy?"** Anchors: §2.4 + W3.5.9 cross-link. 70 words: GBrain is Class 4 — markdown-first deterministic-graph. HyperMem is Class 3 — LLM-extracted hyperedges. Complementary: GBrain for the structured operational data you control (meetings, contacts, internal docs); HyperMem-class for unstructured conversational data. Many production systems run both with a thin router routing by data shape.

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
