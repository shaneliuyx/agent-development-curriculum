---
title: "Week 3.5.96 — Self-Wiring Memory (GBrain — Garry Tan's Production Memory Layer for AI Agents)"
created: 2026-05-28
updated: 2026-05-28
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
5. Run 10 queries comparing pure-vector search vs RRF (vector + keyword) on the same corpus. Measure Recall@5 delta — expect ~12pt improvement matching the published 83→95% claim.
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
> over MCP (P6) → verify the wired graph (P3)**. The earlier Claude-Code-driven
> ingestion path (scaffold skills + `claude mcp add` + trigger) was **dropped** in
> favor of that standalone agent — so Phase 2 below is just corpus prep, and the
> conversion lives in Phase 6.

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

**Goal:** stage raw, differently-shaped sources for the agent to convert. You do **not** format them — the conversion is the agent's job (Phase 6).

**Two layers, two owners** (`docs/GBRAIN_RECOMMENDED_SCHEMA.md`):
- **Raw sources** — emails, transcripts, any format. **Immutable**, kept in `sources/`; the agent *reads* them, never rewrites them.
- **The brain** — two-layer pages (*Compiled Truth* / `---` / *Timeline*) with `[[dir/slug]]` wikilinks. **The agent writes this layer** (Phase 6).

> **Anti-pattern (BCJ Entry 4):** hand-converting each source format, or hand-authoring the pages, does not scale and is not how GBrain works. The agent is the formatter; you curate.

```bash
mkdir -p ~/brain/{sources,people,companies,deals,meetings,concepts} && cd ~/brain && git init
# drop raw samples (any format) under sources/
```

**What we staged** — two synthetic, mutually-consistent fixtures, deliberately different shapes so one agent must handle both:
- `sources/emails/acme-thread.txt` — email thread (`From:/To:/Subject:` + reply chain)
- `sources/transcripts/dinner.txt` — timestamped speaker transcript

The raw→structured conversion is **not** a deterministic command (it's an LLM judgment — which entities, which directory, which typed edge), so it's done by the standalone agent in **Phase 6**, which emits pages shaped like:

```text
# Alice Chen
Founder of [[companies/acme-ai]]; previously at [[companies/anthropic]]; angel in [[companies/stripe]].
---
## Timeline
- 2026-05-12 — dinner re [[deals/acme-seed]] (source: sources/transcripts/dinner.txt)
```

**Verification:** the raw fixtures exist under `~/brain/sources/`; the structured `people/…`, `companies/…`, `deals/…` pages appear only after the Phase 6 agent runs (then Phase 3 verifies the graph).

### Phase 3 — Verify the self-wiring graph [executed, measured]

**Goal:** confirm the `[[wikilinks]]` the agent wrote (Phase 6) became typed graph edges — deterministically, with zero LLM calls. **Run after Phase 6** (it operates on the pages the agent produced).

```bash
export GBRAIN_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gbrain
gbrain extract links --source db     # backfill typed edges from the agent's wikilinks
gbrain stats                         # pages · links · embedded chunks
gbrain graph-query deals/acme-seed   # typed-edge traversal
```

> **Gotcha:** there is no `gbrain ingest` (it's `import`) and no `gbrain entity` (use `graph-query` / `backlinks` / `get`). `links: 0` means either you skipped `extract links` **or** the agent's pages had no wikilinks — the real failure we hit (BCJ Entry 5).

**Result (measured):** on the agent's output — **10 pages → `extract links` created 11 typed edges**. `gbrain graph-query deals/acme-seed` traverses `--invested_in->` / `--works_at->` / `--mentions->` across people + companies (depth 1–5). **Deterministic:** re-running `extract` yields identical edges (regex/parser, zero LLM calls). The first run produced `links: 0` until the extraction prompt was made to mandate wikilinks (BCJ Entry 5) — *graph quality = extraction quality.*

### Phase 4 — Keyword vs hybrid-RRF benchmark [spec — not yet run]

**Goal:** measure the RRF lift on a labeled 10-query set. *(Not executed — the corpus
so far is the ~10-page demo brain, too small for a meaningful Recall@5 benchmark.
Commands + method below for when the brain is larger.)*

> **Spec correction:** GBrain has no `--mode vector-only|rrf`. `query` is *always* hybrid (vector + keyword + RRF + query expansion); `search` is keyword-only (tsvector). The honest A/B is **`search` vs `query`**. `--mode` selects the cost tier (`conservative|balanced|tokenmax`); `--limit` sets K (default 20); `--explain` shows per-stage scoring.

```bash
# keyword-only baseline (tsvector / BM25-style)
gbrain search "investments in fintech companies" --limit 5
# hybrid (vector + keyword + RRF + expansion)
gbrain query  "investments in fintech companies" --limit 5 --explain
# repeat across 10 queries: name-specific, semantic-only, exact-phrase, mixed
```

**Measurement:** label the expected hits per query, then compute Recall@5 for `search` vs `query`. Garry Tan's published figure is **83% → 95% Recall@5** (graph-disabled vs hybrid+graph, 240-page corpus) — reproduce the *direction* on your corpus; treat the exact delta as **projected until you run it** (this chapter is a SPEC; no end-to-end run yet).

**Deliverable:** `~/brain/outputs/rrf_benchmark.md` — a 10-query × {`search`, `query`} Recall@5 table.

### Phase 5 — Synthesis layer + "what we don't know" check [spec — not yet run]

**Goal:** confirm the synthesis layer flags gaps instead of fabricating. *(Not
executed — we ran `query` and got a correct cited answer (Phase 6, score 0.93),
but did not run the deliberate gap/absent-fact test below.)*

```bash
gbrain ask "what did Alice do on 2026-06-15?"   # `ask` = alias for `query`; that date is absent from the corpus
# Expect: an answer that explicitly names the gap ("no visibility into 2026-06-15 for Alice…"),
#         not an invented event.
gbrain query "Alice" --no-expand                 # --no-expand skips LLM query expansion (cheaper, deterministic)
```

**Verification:** the answer surfaces the gap explicitly **and** cites brain pages for what it *does* know; it does not invent a 2026-06-15 event.

### Phase 6 — A future agent uses GBrain as memory over MCP [executed, measured]

> **This is the ingestion engine for the whole lab.** It converts the Phase 2 raw
> fixtures into structured pages; Phase 3 then verifies the graph it wired. (Logically
> it runs *before* Phase 3 — kept at number 6 so the heavy code stays in one place.)


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

## 6. Bad-Case Journal (3-5 entries — SPEC)

_Observed during the real Phase-1 run (GBrain 0.42.25.0):_

- **Entry 1 — `llama-server` provider is a catch-22 for registry-known embed models (OBSERVED).** `--embedding-model llama-server:bge-m3` (and `:nomicai-modernbert-embed-base-bf16`) refuses *both* ways: **with** `--embedding-dimensions` → "does not support custom dimensions N (this model only emits its default vector size)"; **without** → "llama-server requires --embedding-dimensions <N> (user-driven recipes have no default dimension)." No value satisfies both → init impossible. *Fix:* use the **`ollama` provider** pointed at oMLX (`OLLAMA_BASE_URL=http://localhost:8000/v1`, `OLLAMA_API_KEY=<key>`, `--embedding-model ollama:<model>`, **no** `--embedding-dimensions`) — it *probes* the endpoint for the dim instead of demanding/rejecting it. (Worth a GBrain issue; strip keys before filing.)
- **Entry 2 — init is stateful + greedy; a botched first run poisons every retry (OBSERVED).** Three compounding traps: (a) `--supabase` runs the *interactive Supabase flow* and ignores `GBRAIN_DATABASE_URL` — use `--url`; (b) a present `OPENROUTER_API_KEY` makes init **auto-pick openrouter for embeddings** (probe failed 404 on a dummy key) even with `--embedding-model` set — keep it commented until post-init; (c) a wrong first init persists `~/.gbrain/config.json` + a baked vector-column width, so re-init fails citing the *stale* dimension. *Fix (0 pages → safe):* `DROP DATABASE gbrain; CREATE DATABASE gbrain;` + `rm ~/.gbrain/config.json`, then re-init. Lesson: **GBrain init is stateful and greedy — reset clean if anything looks off, and read the "Using …" line, not the green migration checkmarks.**
- **Entry 3 — `gbrain` not found after `bun link` (OBSERVED).** `bun link` symlinks the CLI into `~/.bun/bin` but does not add it to PATH; the installer often doesn't persist the PATH line either. *Fix:* `echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc`. Tell-apart: `ls ~/.bun/bin/gbrain` exists ⇒ pure PATH issue, not a broken install.
- **Entry 4 — trying to hand-format every source type into brain pages (DESIGN anti-pattern).** Emails, tweets, and meeting transcripts each have a different shape; writing a per-format converter (or authoring the 50 pages by hand) does not scale and is *not* GBrain's model. *Root cause:* mistaking who owns the structured layer. GBrain splits **raw sources** (immutable, any format, in `sources/`) from **the brain** (two-layer pages the **agent** writes). *Fix:* never author structured pages manually — drop raw under `sources/` (or `gbrain capture`), then let the agent convert via **ingest skills** (`meeting-ingestion`, `article-enrichment`, `voice-note-ingest` → `put_page`/`add_link`) or, in production, the credentialed **integration recipes** (`email-to-brain`, `x-to-brain`, `meeting-sync`). The agent is the universal formatter; you curate. (Drove the Phase 2 rewrite.)

- **Entry 5 — the agent stored pages fine but the graph had zero edges (OBSERVED, Phase 6).** A smolagents `CodeAgent` (oMLX) drove GBrain over MCP and wrote 5 well-formed pages via `put_page`, yet `gbrain extract links` reported `Links: 0`. *Root cause:* the LLM extraction wrote entity mentions as **plain prose** ("Alice Chen, founder of Acme AI") and used `<!-- timeline -->` instead of `---`, so there were no `[[wikilinks]]` to extract. The framework + MCP plumbing worked; the *contract* didn't. *Fix:* the extraction prompt must **hard-mandate** path-qualified `[[dir/slug]]` wikilinks with a worked example + "a page with zero wikilinks is invalid" → `Links: 0 → 11`. **Graph quality = extraction quality; measure edges, not pages.**
- **Entry 6 — fully-autonomous `CodeAgent` failed on a 14B (OBSERVED, Phase 6).** Asking the agent to read files + write an extractor + compose markdown in one code loop produced a naive regex placeholder + `InterpreterError: import pathlib not allowed` (the CodeAgent sandbox blocks `pathlib`/`json`). *Fix:* **thin agent, fat tools** — move file I/O and extraction into `@tool`s (`read_sources`, `extract_pages`); the agent only orchestrates. Also: filter `ToolCollection.from_mcp` to the ~few tools needed (GBrain exposes ~70; a 14B drowns), depend on `smolagents[mcp]` (mcpadapt), pass DB/oMLX env via `StdioServerParameters(env=…)` (an MCP server is a separate process), and use `use_structured_outputs_internally=True` (oMLX has no native tool_calls). Lab: `~/code/agent-prep/lab-03-5-96-gbrain/`.

_Projected (to confirm during Phases 3–6):_

- **Phase 3 — Markdown convention mismatch.** Likely surface: your `# Meeting with Alice` doesn't trigger the `attended` edge because GBrain's parser expects `# Dinner with @alice`. Fix: read GBrain's parser regex; adopt the `@handle` convention consistently.
- **Phase 4 — RRF lift smaller than 12pts.** Likely surface: corpus too short OR queries too name-specific (both retrievers already agree). Fix: expand corpus to 200+ pages OR pick queries with mix of semantic + exact-phrase types.
- **Phase 5 — Synthesis layer hallucinates a "we don't know" caveat that's wrong.** Likely surface: gap-flagging logic uses a heuristic that triggers on missing entities even when the answer IS in the corpus. Fix: synthesis prompt includes the retrieved citations explicitly; gap-flag triggers only when retrieval returned zero matches.
- **Phase 6 — Agent over-relies on GBrain for general knowledge.** Likely surface: agent uses GBrain context for questions GBrain shouldn't know (general world facts). Fix: agent prompt distinguishes "questions about MY people/companies/events" (use GBrain) vs "general questions" (use base LLM knowledge).

---

## 7. Interview Soundbites (2-3 entries — SPEC)

- **Planned Soundbite 1 — "Why deterministic extraction over LLM extraction?"** Anchors: §2.1 + §2.4. 70 words: when data is already structured (Markdown notes, calendar events, contact lists), deterministic parsing is cheap, reproducible, auditable. LLM extraction is the right tool for UNSTRUCTURED text (raw conversations, scraped web). GBrain's choice is workload-driven, not philosophical. Many production stacks use both: GBrain for structured operational data + LLM-extracted graphs for unstructured conversations.
- **Planned Soundbite 2 — "Walk me through the 83→95 Recall@5 lift."** Anchors: Phase 4 measurement. 70 words: pure HNSW vector search recall@5 = 83% on 240-page corpus. RRF (HNSW + Postgres keyword) recall@5 = 95%. The +12pt lift comes from exact-term queries (names, acronyms, proper nouns) that pure-vector underweights. Production rule: RRF is the cheapest hybrid-search upgrade; ~50 LOC of Postgres + RRF math on top of any vector store.
- **Planned Soundbite 3 — "Where does GBrain fit vs HyperMem in your taxonomy?"** Anchors: §2.4 + W3.5.9 cross-link. 70 words: GBrain is Class 4 — markdown-first deterministic-graph. HyperMem is Class 3 — LLM-extracted hyperedges. Complementary: GBrain for the structured operational data you control (meetings, contacts, internal docs); HyperMem-class for unstructured conversational data. Many production systems run both with a thin router routing by data shape.

---

## 8. References

- **GBrain.** https://gbrain.homes/. MIT-licensed. Built by Garry Tan (Y Combinator) for his actual agents (OpenClaw, Hermes).
- **MarkTechPost — GBrain tutorial (May 22, 2026).** https://www.marktechpost.com/2026/05/22/a-step-by-step-coding-tutorial-to-implement-gbrain-the-self-wiring-memory-layer-built-by-y-combinators-garry-tan-for-ai-agents/.
- **Hermes Atlas — GBrain project page.** https://hermesatlas.com/projects/garrytan/gbrain.
- **Vectorize — What Is GBrain? Garry Tan's AI Agent Memory System Explained.** https://vectorize.io/articles/what-is-gbrain.
- **Cormack et al. (2009).** *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods.* SIGIR 2009. Foundational RRF paper.
- **MarkTechPost tutorial repo.** https://github.com/Marktechpost/AI-Agents-Projects-Tutorials. Contains `gbrain-tutorial.ipynb`.

---

## 9. Cross-References

- **Builds on:** [[Week 3.5.5 - Multi-Agent Shared Memory]] (multi-agent memory foundations); [[Week 3.5.8 - Two-Tier Memory Architecture]] (two-tier consolidation pattern); [[Week 3.5.9 - Requirement-Driven Memory Architecture]] (architecture-choice meta-skill — this chapter is Class 4).
- **Distinguish from:** [[Week 3.5.9 - Requirement-Driven Memory Architecture]] §2 three-class taxonomy (Class 1/2/3 are LLM-extracted; GBrain is Class 4 deterministic).
- **Connects to:** [[Week 6.65 - MCP Production Transports]] (GBrain exposes 74 MCP tools); [[Week 6.5 - Hermes Agent Hands-On]] (Hermes is one of GBrain's downstream consumers); [[Week 12 - Capstone]] (capstones with structured operational data can use GBrain as memory layer).
- **Foreshadows:** continued production memory-layer evolution; expect GBrain v2 with broader typed-edge vocabulary (skills, contracts, transactions).

---

## What's Next

After W3.5.96: use GBrain alongside W3.5.8's two-tier OR W3.5.9's three-tier for operational data. Combine with W4 ReAct agent (W7 Tool Harness) for memory-augmented agent. Future: integrate with W3.5.95 PAI v7.6 self-observability for agent-self-knowledge graph.
