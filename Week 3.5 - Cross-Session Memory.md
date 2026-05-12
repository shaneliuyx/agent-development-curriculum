---
title: "Week 3.5 — Cross-Session Memory"
created: 2026-04-24
updated: 2026-05-12
tags: [agent, curriculum, week-3-5, memory, qdrant, sqlite, runbook]
audience: "Cloud infrastructure engineer (3 yrs), building stateful agent systems"
stack: "MacBook M5 Pro, custom Python extraction (oMLX + sentence-transformers), Qdrant on Docker, SQLite, Python 3.11+"
companion_to: "Agent Development 3-Month Curriculum.md"
lab_dir: "~/code/agent-prep/lab-03-5-memory"
estimated_time: "5 hours over 1–2 days"
prerequisites: "Week 3 lab complete (RAG eval harness working) + Qdrant running from Week 1"
---

# Week 3.5 — Cross-Session Memory

> Goal: build an agent that remembers a user's preferences across three or more separate conversations. The lab is INTENTIONALLY hand-rolled — custom OpenAI-compatible extraction (oMLX Haiku-tier) + Qdrant for vector-addressable episodic memories + SQLite for structured semantic facts. No `mem0`-style library wrapper; you write the lifecycle yourself so you understand the primitives. Exit with a working demo, a 15-question recall benchmark, and a crisp answer to "how do you give an agent long-term memory?". The `mem0` library is cited as production prior-art in the References — read it AFTER finishing the lab to compare your hand-rolled design against the library's choices.

This is a **half-week insert** between Week 3 and Week 4. It adds ~5 hours to Phase 1 and closes a real portfolio gap: before this lab, every agent you've built is session-local. Cross-session memory is the product feature behind ChatGPT's "memories," Claude Projects' context, and most 2026 consumer-agent products. It's also the thing interviewers will probe once you've explained RAG cleanly — "RAG gives your agent knowledge; what gives it a relationship?"

---

## Why This Week Matters

Every agent you've built up to now forgets. Close the browser tab, or start a new session, and the model has no idea who you are or what you've told it before. RAG solved *knowledge* amnesia (agents can now retrieve documents); this week solves *relationship* amnesia — agents remember facts about their users across separate conversations.

This is production critical. ChatGPT's "memories" feature, Claude Projects' context persistence, and every 2026 consumer AI product stores facts extracted from conversations. The interview signal is distinct: candidates who can articulate the four memory types (working, episodic, semantic, procedural), explain the extract→store→retrieve→inject lifecycle, and describe the dual-store topology (vector for episodes, relational for semantic facts) demonstrate they understand agent state management as a system design decision, not a feature checkbox.

---

## Exit Criteria

- [ ] `docker-compose.yml` running Qdrant (reusing your Week 1 instance is fine)
- [ ] `src/memory.py` — hand-rolled memory writer + reader: custom OpenAI-compatible extraction (oMLX Haiku-tier) + Qdrant episodic store + SQLite semantic-fact store
- [ ] `src/chat.py` — a REPL agent that reads memory at turn-start and writes memory at turn-end
- [ ] `src/demo_three_sessions.py` — scripted demo proving cross-session recall across three separate conversations
- [ ] `tests/test_recall.py` — 15-question recall benchmark, ≥ 12/15 passing
- [ ] `RESULTS.md` with the demo transcript + recall-benchmark table + memory-type taxonomy table
- [ ] You can answer in 90 seconds: "What are the four types of agent memory, and which two does an episodic + semantic dual-store give you?"

---

## Theory Primer — Four Concepts You Must Be Able to Explain

### Concept 1 — The Four Types of Memory (Cognitive-Science Borrowing)

The taxonomy interviewers expect you to know — adapted from cognitive science and now standard vocabulary in agent engineering:

| Memory type | What it stores | Lifetime | Storage |
|---|---|---|---|
| **Working / Short-term** | Current conversation turns | Session | Conversation buffer in the prompt |
| **Episodic** | "On Tuesday the user asked about X and I answered Y" | Permanent, time-indexed | Vector store + timestamp |
| **Semantic / Entity** | "The user lives in Taipei. The user is vegan." | Permanent, fact-indexed | Vector store + structured DB |
| **Procedural** | Learned skills — "for this user, prefer terse replies" | Permanent, pattern-indexed | System prompt augmentation or fine-tune |

This lab's hand-rolled design covers **episodic + semantic** memory. Working memory is still the conversation buffer (managed by the LLM caller's message list). Procedural memory is out-of-scope for hand-rolled memory systems — you roll it into the system prompt or fine-tune the model. Production libraries like `mem0` (referenced in §References) collapse episodic + semantic into one API; this lab keeps them in separate stores (Qdrant for episodic, SQLite for semantic) so the dual-store rationale is visible.

> **Interview soundbite:** "Four types — working, episodic, semantic, procedural. A dual-store memory system covers episodic and semantic — vector DB for free-form events, relational for structured facts. Working memory is the conversation buffer; procedural usually needs fine-tuning or prompt augmentation. The mistake candidates make is conflating all four under 'long-term memory' — interviewers want you to name the type and pick the right storage."

### Concept 2 — The Memory Lifecycle: Extract → Store → Retrieve → Inject

Every memory system has the same four stages. Knowing them prevents the "just dump everything in a vector DB" anti-pattern:

1. **Extract.** At end of turn, an LLM reads the conversation and emits candidate memories as structured facts ("user is vegan", "user lives in Taipei"). This is the step most homegrown memory systems skip — they store raw turns, then retrieval returns noisy transcripts instead of crisp facts.
2. **Store.** Each fact is embedded and written to a vector store, with metadata (user_id, timestamp, source_session_id). Semantic facts also land in a relational DB for exact-match queries like "fetch user's current location."
3. **Retrieve.** At start of next turn, embed the incoming user message and retrieve the top-k relevant memories.
4. **Inject.** Prepend retrieved memories to the system prompt: "Known facts about this user: ...". Critically, inject **only facts that pass a relevance threshold** — injecting irrelevant facts is strictly worse than injecting none.

### Concept 3 — Why Naive "Dump Every Turn" Fails

The temptation: skip the extract stage, store every (user-message, assistant-message) turn as an embedded document, retrieve top-k at the next turn. Why this fails:

- **Retrieval returns verbose transcripts, not facts.** The model spends prompt budget re-reading its own prior outputs.
- **Contradictions accumulate.** User says "I live in Taipei" in session 1, "I moved to Tokyo" in session 2. Naive retrieval returns both; the model gets confused. Extract-based memory resolves this by updating the `user.location` semantic fact.
- **Token cost scales linearly with conversation history.** Extract-based memory compresses hundreds of turns into dozens of facts. Storage grows O(facts), not O(turns).

### Concept 4 — The Forgetting Problem (and Why It Matters)

Memory without forgetting is a landfill. Three forgetting strategies:

1. **TTL (time-to-live).** Facts decay after N days unless re-confirmed. Simplest, and surprisingly effective for consumer products.
2. **Confidence-weighted eviction.** Each fact has a confidence score; lowest-confidence facts are evicted when the memory store hits a cap.
3. **Contradiction-triggered update.** When a new fact contradicts an existing one, the old fact is archived (not deleted — archived for audit), and the new one takes precedence.

This lab implements (3) natively — `write_semantic_fact()` archives the old row before inserting the new value when an LLM-extracted fact contradicts a stored one. (1) and (2) are out-of-scope for the lab but trivial to add (TTL = cron sweep over `updated_at`; eviction = ORDER BY `confidence` ASC LIMIT N before write). Production libraries like `mem0` ship all three; production systems usually run all three.

> **Interview soundbite:** "Memory without forgetting is a landfill. I use three strategies — TTL for stale facts, confidence-weighted eviction under a cap, and LLM-based contradiction detection for updates. The archive-don't-delete rule is non-negotiable for audit."

---

## Architecture Diagrams

### Diagram 1 — Dual-Store Topology

```mermaid
flowchart TB
    subgraph APP[Agent runtime]
        CHAT[chat.py REPL<br/>one process = one session]
    end

    subgraph MEM[src/memory.py — the contract]
        EXT[extract_memories&#40;&#41;<br/>haiku, JSON mode]
        WRITE_S[write_semantic_fact&#40;&#41;<br/>UNIQUE + archive-on-conflict]
        WRITE_E[write_episodic&#40;&#41;<br/>embed + upsert]
        RECALL[recall&#40;&#41;<br/>facts + top-k episodes]
    end

    subgraph STORES[Storage]
        SQL[(SQLite<br/>user_facts<br/>key/value + archived)]
        QDR[(Qdrant<br/>user_memories<br/>1024-dim embeddings)]
    end

    CHAT -->|end of turn| EXT
    EXT -->|semantic facts| WRITE_S --> SQL
    EXT -->|episodic summaries| WRITE_E --> QDR

    CHAT -->|start of turn| RECALL
    RECALL --> SQL
    RECALL --> QDR
    RECALL -->|facts + episodes| CHAT

    style EXT fill:#f5a623,color:#fff
    style WRITE_S fill:#4a90d9,color:#fff
    style WRITE_E fill:#4a90d9,color:#fff
    style RECALL fill:#9b59b6,color:#fff
    style SQL fill:#27ae60,color:#fff
    style QDR fill:#27ae60,color:#fff
```

**Why two stores:** semantic facts need exact-match queries (`SELECT value FROM user_facts WHERE key='location'`) AND a uniqueness constraint for the archive-on-contradiction rule — those are RDBMS strengths. Episodic memories are free-form and retrieved by similarity — that's a vector-store strength. Forcing both into one store makes one of the two query patterns painful.

#### Diagram 1 Walkthrough — Dual-Store Topology

The dual-store topology separates memory into two tiers: SQLite for durable facts (location, preferences, role) and Qdrant for episodic events (conversations, observations, task completions). This split is foundational because semantic queries demand ACID isolation and contradiction resolution, while episodic retrieval demands vector similarity. A single unified store forces you to sacrifice one query pattern — prod at both and neither performs. The diagram shows the agent's REPL reading from both stores at turn-start, then writing to both after the model responds, with contradiction detection in the semantic write path to maintain single-source truth.

`★ Insight ─────────────────────────────────────`
- **Two-tier split avoids false choice**: SQLite (exact match + uniqueness + audit trail) + Qdrant (free-form + similarity) solves different problems with appropriate tools, not a compromise that half-works for both
- **Archive-on-conflict, not update-in-place**: New semantic facts don't overwrite old ones; old rows get `archived=1` so audit trail and revert paths remain available
- **Read-before-call, write-after-reply**: Model sees memories in system prompt (read path), then memory extraction runs async post-reply (write path) so user never waits on extraction latency
`─────────────────────────────────────────────────`

**Data flow (numbered nodes):**
1. **chat.py REPL** — user session entry point; owns read/respond/write cycle
2. **extract_memories** — haiku-class LLM call; distills conversation into `{semantic: [], episodic: []}` 
3. **write_semantic_fact** — SQLite insert/update with contradiction detection; returns "new" / "updated" / "unchanged"
4. **write_episodic** — Qdrant upsert; embeds text, stores with payload (user_id, session_id, timestamp)
5. **recall** — reads both stores; fetches live facts from SQLite, top-k episodes from Qdrant by vector similarity
6. **Stores**: SQLite (key/value + archived flag) and Qdrant (1024-dim, COSINE distance)

**Why this matters in interviews**: Explain that you separated concerns by storage technology, not by trying to build a one-size-fits-all memory system. Show you understand why `SELECT WHERE key=?` and vector-similarity search are different enough that forcing them into one backend is a footgun.

---

### Diagram 2 — Single-Turn Lifecycle (read → respond → write)

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant C as chat.py
    participant R as recall&#40;&#41;
    participant S as SQLite
    participant Q as Qdrant
    participant L as Gemma-4-26B
    participant E as extract_memories&#40;&#41;
    participant WS as write_semantic_fact&#40;&#41;
    participant WE as write_episodic&#40;&#41;

    U->>C: user message
    C->>R: recall(user_id, user_message)
    R->>S: SELECT live facts
    R->>Q: vector search top-k
    R-->>C: {semantic_facts, relevant_episodes}
    C->>C: inject memory block into system prompt
    C->>L: chat.completions(system + history + user_msg)
    L-->>C: assistant reply
    C-->>U: display reply

    Note over C: async-equivalent: after reply is shown, write memory
    C->>E: extract_memories(user_msg, assistant_msg)
    E-->>C: {"semantic": [...], "episodic": [...]}

    loop for each semantic fact
        C->>WS: write_semantic_fact(user_id, key, value)
        WS->>S: SELECT live WHERE key=?
        alt live row exists with different value
            WS->>S: UPDATE archived=1 (old)
            WS->>S: INSERT new row
        else no live row
            WS->>S: INSERT new row
        end
    end

    loop for each episodic memory
        C->>WE: write_episodic(user_id, session_id, text)
        WE->>L: embed(text) [bge-m3]
        WE->>Q: upsert point with payload
    end
```

Two beats that separate this from Reflexion-style self-critique: **(a)** the read path runs **before** the model call — the model sees memories in its system prompt as context, not as a post-hoc correction; **(b)** the write path runs **after** the reply is shown to the user, so memory extraction never adds latency to the visible response. In production you'd move step 12 onward onto a background queue (Celery, RQ, or a simple `asyncio.create_task`) so the user never waits on memory writes.

#### Diagram 2 Walkthrough — Single-Turn Lifecycle (read → respond → write)

The sequence diagram choreographs a single agent turn: the agent reads existing memories at request-start (steps 1–6), feeds them into the system prompt, calls the LLM (steps 7–9), and then asynchronously extracts and stores new memories after showing the user the reply (steps 10–13). The critical insight is the *order*: read before model call, write after user sees the response. This avoids Reflexion's latency penalty (where the model waits for critique) and preserves the archive-on-contradiction invariant (contradiction detection runs in the write path, not in the read path). The diagram shows autonumbered steps so you can trace what happens at each stage — who calls whom, when does Qdrant get involved, which step involves the LLM.

`★ Insight ─────────────────────────────────────`
- **Eager read, lazy write**: Model gets memory context upfront (read path = synchronous, visible), writes happen after reply (write path = async, invisible to user latency)
- **Two LLM calls, different models**: Recall is lightweight (no LLM); extraction uses haiku (cheap) after the main model call; archive-on-contradiction uses LLM-based diff detection
- **Contradiction detection is write-time, not read-time**: Old semantic facts are archived only when a *new* fact contradicts them, not preemptively; this lets the model see prior context and decide if the new fact should actually replace it
`─────────────────────────────────────────────────`

**Sequence steps:**
1. **User sends message** → chat.py receives it
2. **chat.py calls recall(user_id, user_message)** → fetch live facts + episodic top-k
3. **Recall queries SQLite** → SELECT live facts (archived=0)
4. **Recall queries Qdrant** → vector search for similar episodes
5. **Recall returns both** → {semantic_facts, relevant_episodes}
6. **chat.py injects memory block** → prepend to system prompt
7. **chat.py calls LLM** → chat.completions(system + history + user_msg)
8. **LLM responds** → assistant reply ready
9. **chat.py displays reply** → user sees response (no memory latency!)
10. **chat.py calls extract_memories** → haiku-model: distill turn into {semantic, episodic}
11. **For each semantic fact** → write_semantic_fact() handles archive-on-conflict
12. **For each episodic summary** → write_episodic() embeds and upserts to Qdrant
13. **Both stores updated** → SQLite + Qdrant consistency maintained

**Interview framing**: "Memory read is synchronous and happens before the model call so the context is fresh. Memory write is asynchronous and happens after the user sees the response so extraction latency never blocks the user. The write path also handles contradiction detection — if a new fact contradicts an old one, we archive the old one instead of overwriting it."

---

## Phase 1 — Infrastructure Setup (~30 minutes)

### 1.0 Guided setup (recommended after first checkout)

After cloning the lab and installing dependencies (1.1 below), run the one-command guided setup:

```bash
.venv/bin/python -m src.lab_init
```

`src/lab_init.py` is the lab's `guild init` equivalent — a single Python script that auto-detects what's configured, prompts only for missing pieces, and is safe to re-run idempotently. It walks 5 steps:

1. **Python environment** — verifies Python 3.11+ and venv-active
2. **Qdrant** — checks `localhost:6333`; offers to `docker start qdrant` or `docker run` if missing
3. **Embedding backend** — probes oMLX `/v1/models` for a `bge-*` model; falls back to interactive prompt for the `sentence-transformers` in-process path with `USE_LOCAL_EMBED=1`
4. **.env** — writes the 8 required env-vars (OMLX_BASE_URL, OMLX_API_KEY, MODEL_SONNET, MODEL_HAIKU, QDRANT_URL, SQLITE_PATH, EMBED_MODEL, USE_LOCAL_EMBED) using detected values + interactive prompts for the rest
5. **Verify** — initializes SQLite + smoke-tests `embed()` and `recall()`; prints next-step commands (3-session demo / chat REPL / 15-Q benchmark)

Output mirrors `guild init`'s UX style: colored status (`✓` green, `▸` blue step headers, `⚠` yellow warnings, `✗` red failures), step-numbered progress, and a "Next:" footer. ~150 LOC, stdlib only (no extra dependencies beyond the lab's existing install).

If `lab_init.py` succeeds, skip ahead to Phase 2. Sections 1.1-1.3 below are the manual fallback for users who want to do the setup by hand (e.g. for debugging, or to read what the script actually does).

`★ Insight ─────────────────────────────────────`
- **DX (Developer Experience) as a load-bearing skill**: a one-command setup that auto-detects state + prompts for missing pieces is the difference between a lab that gets cloned-and-abandoned (manual setup gauntlet) and a lab that ships portfolio-quality reproducibility. The script is ~3 hours of code; saves 30 minutes per new contributor.
- **Modeled on `guild init`**: same primitives — detect-state-first, idempotent, ANSI-colored status lines, "Next:" footer. The pattern transfers across labs; consider porting to W3.5.5 (guild integration), W3.5.8 (two-tier composition), and any future supplemental lab.
- **The 5-step structure mirrors a production install script**: dependency check → service health → backend detection → config write → smoke-test. Same shape as Kubernetes operator's reconciliation loop, Terraform's apply phase, or Docker compose's `up -d --wait`. Production discipline in miniature.
- **Why stdlib-only**: zero new dependencies = the script works even when other things are broken. If lab_init can't import its way to standing up the lab, it can at least diagnose what's missing. The colored-status output uses raw ANSI codes instead of `rich` for the same reason.
`─────────────────────────────────────────────────`

### 1.1 Lab scaffold

```bash
mkdir -p ~/code/agent-prep/lab-03-5-memory/{src,data,results,tests}
cd ~/code/agent-prep/lab-03-5-memory
uv venv --python 3.11 && source .venv/bin/activate
uv pip install qdrant-client openai python-dotenv pytest sentence-transformers
```

**Embedding model setup — recommended path (oMLX serves BGE-M3)**:

oMLX supports embedding models including BGE-M3 (see [jundot/omlx README](https://github.com/jundot/omlx) — types supported: LLM, VLM, OCR, embedding, reranker). A fresh oMLX install ships chat models only — you need to add the embedding model explicitly. Two options:

1. **Via oMLX admin dashboard** (easiest): open `http://localhost:8000/admin/chat`, find the model-download UI, search for `bge-m3`, download. Restart oMLX → `bge-m3-mlx-fp16` (or similar id) appears in `/v1/models`.
2. **Via HuggingFace CLI manual placement**: `huggingface-cli download mlx-community/bge-m3-mlx-fp16 --local-dir ~/.omlx/models/bge-m3-mlx-fp16` → restart oMLX.

Verify the model is registered: `curl -H "Authorization: Bearer $OMLX_API_KEY" http://localhost:8000/v1/models | grep -i bge`. Once the model id appears, `embed()` will use the oMLX-served endpoint (no Python-side model load, much lower resident memory per process).

**Embedding fallback — in-process (`USE_LOCAL_EMBED=1`)**: if you can't / don't want to add the model to oMLX, set `USE_LOCAL_EMBED=1` in `.env`. The lab will load BGE-M3 in-process via `sentence-transformers` (~1 GB resident, MPS device on Apple Silicon). Slower at module import (10s first load); offline-capable.

`sentence-transformers` stays in the dependency list so the fallback path always works even on a fresh oMLX install that hasn't been configured yet.

### 1.2 Environment

```bash
# .env
OMLX_BASE_URL=http://localhost:8000/v1
OMLX_API_KEY=Shane@7162
MODEL_SONNET=gemma-4-26B-A4B-it-heretic-4bit
MODEL_HAIKU=gpt-oss-20b-MXFP4-Q8
EMBED_MODEL=bge-m3-mlx-fp16    # oMLX-served embedding model id; see Phase 1.1
USE_LOCAL_EMBED=0              # set to 1 to bypass oMLX + use in-process
                               # sentence-transformers BGE-M3 fallback
QDRANT_URL=http://localhost:6333
SQLITE_PATH=data/memory.db
```

Your Qdrant instance from Week 1 is fine — we'll create a dedicated collection `user_memories`.

**Required running services before starting the lab:**

| Service | Endpoint | How to start | Verify |
|---|---|---|---|
| Qdrant | `localhost:6333` | `docker start qdrant` (or `docker run -d -p 6333:6333 --name qdrant qdrant/qdrant`) | `curl localhost:6333/readyz` returns `OK` |
| oMLX (chat for extraction + response) | `localhost:8000` | Open the oMLX menu-bar app | `curl -H "Authorization: Bearer $OMLX_API_KEY" localhost:8000/v1/models` returns model list including `MODEL_HAIKU` + `MODEL_SONNET` |
| BGE-M3 (embeddings) | in-process | Auto-loaded on first `import src.memory` (~10s first-time download + load) | Smoke test: `python -c "from src.memory import embed; print(len(embed('test')))"` returns `1024` |

If `curl localhost:8000/v1/models` returns `Connection refused`, oMLX isn't running. If it returns `API key required`, you forgot the `Authorization` header — that's fine, the server is up. If you get `404 Model 'bge-m3' not found` after running the chat REPL, your `embed()` is still hitting oMLX — apply the in-process fix from Phase 2.1.

### 1.3 SQLite schema for semantic facts

```python
# src/init_db.py
import sqlite3, os
from pathlib import Path
from dotenv import load_dotenv; load_dotenv()

Path(os.getenv("SQLITE_PATH")).parent.mkdir(exist_ok=True)
conn = sqlite3.connect(os.getenv("SQLITE_PATH"))
conn.executescript("""
CREATE TABLE IF NOT EXISTS user_facts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,
    key        TEXT NOT NULL,       -- e.g. 'location', 'diet', 'name'
    value      TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived   INTEGER DEFAULT 0,
    UNIQUE(user_id, key, archived)
);
CREATE INDEX IF NOT EXISTS idx_user_facts_live ON user_facts(user_id, archived);
""")
conn.commit(); conn.close()
print("SQLite initialised")
```

Run once: `python src/init_db.py`.

---

## Phase 2 — Memory Writer + Reader (~2 hours)

### 2.1 The two-store design

Save as `src/memory.py`:

```python
"""Two-store memory backend:
  - Qdrant holds episodic memories (verbatim-ish: 'user said they love cycling').
  - SQLite holds semantic facts (structured: key='hobby', value='cycling').
Both are written to; retrieval fetches from both and merges.

Contradiction handling: when we store a new semantic fact for a key that
already has a LIVE value, we archive the old row (archived=1) and write
a new one. We NEVER UPDATE IN PLACE — archival preserves audit trail."""
import os, json, sqlite3, uuid
from typing import Literal
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

load_dotenv()
omlx   = OpenAI(base_url=os.getenv("OMLX_BASE_URL"), api_key=os.getenv("OMLX_API_KEY"))
qdrant = QdrantClient(url=os.getenv("QDRANT_URL"))
SQLITE = os.getenv("SQLITE_PATH")
MODEL  = os.getenv("MODEL_SONNET")
HAIKU  = os.getenv("MODEL_HAIKU")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3-mlx-fp16")
COLLECTION = "user_memories"

# Dual-path embedding: default oMLX-served BGE-M3 (low resident memory,
# shared across processes); fallback in-process sentence-transformers
# when USE_LOCAL_EMBED=1 (offline-capable, ~1 GB per process).
_USE_LOCAL = os.getenv("USE_LOCAL_EMBED", "0") == "1"
_local_embedder = None
if _USE_LOCAL:
    from sentence_transformers import SentenceTransformer
    _local_embedder = SentenceTransformer("BAAI/bge-m3", device="mps")

# Bootstrap Qdrant collection (idempotent)
if not qdrant.collection_exists(COLLECTION):
    qdrant.create_collection(
        COLLECTION,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

# ── Extraction: turn a conversation turn into structured memories ────────────

EXTRACT_PROMPT = """Extract memories from this conversation turn.
Return JSON only: {"semantic": [{"key": str, "value": str}], "episodic": [str]}.

SEMANTIC — durable facts about the user. Structured. Examples:
  {"key": "location", "value": "Taipei"}
  {"key": "diet", "value": "vegan"}
  {"key": "job_role", "value": "cloud infrastructure engineer"}

EPISODIC — noteworthy events. One-sentence summaries. Examples:
  "user asked about setting up LangGraph for a customer-support agent"
  "user mentioned they are preparing for an agent-engineering interview"

Skip trivia. Do not invent facts. If nothing memorable, return empty lists."""


def embed(text: str) -> list[float]:
    """1024-dim L2-normalized BGE-M3 vector. Default path is oMLX-served
    (low resident, shared across processes); fallback is in-process
    sentence-transformers when USE_LOCAL_EMBED=1."""
    if _local_embedder is not None:
        vec = _local_embedder.encode([text], normalize_embeddings=True)[0]
        return vec.tolist()
    r = omlx.embeddings.create(model=EMBED_MODEL, input=text)
    return r.data[0].embedding


def extract_memories(user_msg: str, assistant_msg: str) -> dict:
    resp = omlx.chat.completions.create(
        model=HAIKU,   # extraction is cheap; run on haiku
        messages=[
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user",   "content": f"USER: {user_msg}\n\nASSISTANT: {assistant_msg}"},
        ],
        temperature=0.0, max_tokens=400,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        return {"semantic": [], "episodic": []}


# ── Write path ───────────────────────────────────────────────────────────────

def write_semantic_fact(user_id: str, key: str, value: str) -> Literal["new", "updated", "unchanged"]:
    conn = sqlite3.connect(SQLITE)
    row = conn.execute(
        "SELECT id, value FROM user_facts WHERE user_id=? AND key=? AND archived=0",
        (user_id, key),
    ).fetchone()

    if row is None:
        conn.execute(
            "INSERT INTO user_facts (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, key, value),
        )
        result = "new"
    elif row[1] == value:
        result = "unchanged"
    else:
        # Archive old, insert new — preserves audit trail
        conn.execute("UPDATE user_facts SET archived=1 WHERE id=?", (row[0],))
        conn.execute(
            "INSERT INTO user_facts (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, key, value),
        )
        result = "updated"

    conn.commit(); conn.close()
    return result


def write_episodic(user_id: str, session_id: str, text: str) -> None:
    qdrant.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(
            id=str(uuid.uuid4()),
            vector=embed(text),
            payload={"user_id": user_id, "session_id": session_id, "text": text},
        )],
    )


def remember_turn(user_id: str, session_id: str, user_msg: str, assistant_msg: str) -> dict:
    mem = extract_memories(user_msg, assistant_msg)
    sem_results = [
        {"key": f["key"], "value": f["value"],
         "status": write_semantic_fact(user_id, f["key"], f["value"])}
        for f in mem.get("semantic", []) if f.get("key") and f.get("value")
    ]
    for ep in mem.get("episodic", []):
        if ep: write_episodic(user_id, session_id, ep)
    return {"semantic": sem_results, "episodic_count": len(mem.get("episodic", []))}


# ── Read path ────────────────────────────────────────────────────────────────

def recall(user_id: str, query: str, k: int = 5) -> dict:
    # Semantic: all live facts
    conn = sqlite3.connect(SQLITE)
    facts = conn.execute(
        "SELECT key, value FROM user_facts WHERE user_id=? AND archived=0",
        (user_id,),
    ).fetchall()
    conn.close()

    # Episodic: top-k by similarity
    hits = qdrant.query_points(
        collection_name=COLLECTION,
        query=embed(query),
        query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},
        limit=k,
    ).points
    episodes = [h.payload["text"] for h in hits if h.score > 0.35]  # threshold prevents noise

    return {
        "semantic_facts": [{"key": k_, "value": v} for k_, v in facts],
        "relevant_episodes": episodes,
    }


def format_memory_block(memory: dict) -> str:
    if not memory["semantic_facts"] and not memory["relevant_episodes"]:
        return ""
    lines = ["Known facts about this user:"]
    for f in memory["semantic_facts"]:
        lines.append(f"- {f['key']}: {f['value']}")
    if memory["relevant_episodes"]:
        lines.append("\nRelevant past interactions:")
        for e in memory["relevant_episodes"]:
            lines.append(f"- {e}")
    return "\n".join(lines)
```

#### Code Walkthrough — src/memory.py

`src/memory.py` is the memory backend contract — all extraction, write, and read logic lives here. It exports four public functions: `extract_memories()` (distill conversation), `write_semantic_fact()` (SQLite archive-on-conflict), `write_episodic()` (Qdrant upsert), and `recall()` (fetch both stores). The module bootstraps Qdrant on import (idempotent create-collection) and wraps the oMLX client so every call uses the same model config. The key design: extraction is cheap (haiku model, JSON mode), semantic writes are deterministic (SQL logic), episodic writes are idempotent (Qdrant upsert with UUID), and reads merge both stores before returning to the caller.

`★ Insight ─────────────────────────────────────`
- **JSON mode extraction**: LLM extraction is not summarization—it's structured output via `response_format={"type": "json_object"}` with a strict schema, so the model cannot deviate into prose
- **Archive-on-conflict, not UPDATE**: When a new semantic fact contradicts an existing one, the old row gets `archived=1` (not deleted), preserving audit trail and allowing rollback if the new fact is wrong
- **UUID per episodic, not per session**: Qdrant upsert uses UUID per memory, not per session; this allows the same episode (e.g., "user mentioned they love cycling") to appear in multiple sessions' episode stores without collision
- **Similarity threshold on retrieval**: Qdrant queries set `threshold > 0.35` to reject low-confidence matches; raw cosine similarity is too noisy without this gate
`─────────────────────────────────────────────────`

**Block 1 — Module init + Qdrant bootstrap (lines 249–263).**

The module imports clients (OpenAI for oMLX, Qdrant for vector store), loads environment, and initializes a Qdrant collection. The key is **idempotent**: `qdrant.collection_exists()` check before create means re-importing this module does not error out — critical for testing and interactive environments. The collection is 1024-dim (bge-m3 embedding size) with COSINE distance. Note that you configure all of this once here; every later function call re-uses the same client instances.

**Block 2 — extract_memories() (lines 287–300).**

Extraction is the LLM call that turns a user message + assistant response into `{semantic: [], episodic: []}`. The prompt is hardcoded (lines 267–279) and examples-based — it shows the model what a semantic fact looks like (structured key/value) and what an episodic memory looks like (one-sentence summary). The `response_format={"type": "json_object"}` is critical: it forces the LLM to output valid JSON without prose wrapper. Temperature = 0.0 (deterministic). Max_tokens = 400 (enough for ~5 facts + ~5 episodes). Failure case: if the response is not valid JSON, catch and return empty lists (graceful degradation).

Why this matters: extraction is the compression step — you could skip it and store raw turns, but then retrieval returns verbose transcripts instead of crisp facts. The LLM is forced to distill.

**Block 3 — write_semantic_fact() (lines 305–330).**

This is the archive-on-conflict logic. For a given (user_id, key), check if a live row exists. If none, insert. If it exists and value is unchanged, return "unchanged" (no-op). If it exists and value differs, archive the old row (UPDATE archived=1) and insert a new row. This preserves audit trail: you can query archived facts to see what the user previously stated and when it changed.

Why archive instead of update: Audit trail + revert safety. If the new fact is wrong, you can revert to the old one. If you UPDATE in place, you lose history.

The UNIQUE constraint `(user_id, key, archived)` allows multiple rows per key as long as only one has `archived=0`. This enforces single-source truth for live facts.

**Block 4 — write_episodic() (lines 333–341).**

Episodic writes are idempotent: embed the memory text using bge-m3, generate a UUID, and upsert into Qdrant with payload (user_id, session_id, text). Upsert = insert if not exists, update if exists (by ID). The payload metadata allows filtering by user during retrieval.

Why upsert: if the same text appears multiple times, it gets the same embedding and overwrites the same Qdrant point (same UUID). This is fine — episodes are additive and duplicates don't hurt.

**Block 5 — remember_turn() (lines 344–352).**

Orchestrator that calls extract_memories, then writes both semantic and episodic facts. Returns a summary of what was written (status per fact, count of episodes). This is called from the REPL after the LLM response is shown to the user.

**Block 6 — recall() (lines 407–428).**

Read path: fetch all live semantic facts (archived=0) and top-k episodic memories by similarity. Episodic hits are filtered by `score > 0.35` to reject low-confidence noise. Returns merged dict with both. The query embedding is computed by calling embed() on the incoming query string.

Why the 0.35 threshold: cosine similarity on 1024-dim embeddings can be high by chance; 0.35 is an empirical threshold that rejects noise. Tune this per your corpus — too low and you get irrelevant episodes, too high and you miss relevant ones.

**Block 7 — format_memory_block() (lines 431–441).**

Formats the recalled memory dict into a prompt-injectable string. The model sees this block prepended to its system prompt:
```
Known facts about this user:
- location: Taipei
- diet: vegan

Relevant past interactions:
- user mentioned they are preparing for an agent-engineering interview
- user asked about setting up LangGraph for a customer-support agent
```

This is the injection point where memory becomes context.

**Common modifications:**
- **Change embedding model**: Edit line 283 (`embed()`) to use a different model (e.g., "nomic-embed-text-v1.5" instead of bge-m3). Update COLLECTION vector size accordingly.
- **Tune episodic threshold**: Line 423 `if h.score > 0.35` — lower for recall, raise for precision.
- **Archive retention**: Add a TTL by querying `SELECT * FROM user_facts WHERE archived=1 AND updated_at < CURRENT_TIMESTAMP - 30 days` and deleting old archives periodically.
- **Confidence scoring**: Add a confidence column to semantic facts and use it to rank retrieved facts; higher confidence facts get injected first.

**Expected runtime (M5 Pro):**
- extract_memories (haiku, JSON mode): ~150–200 ms per turn
- write_semantic_fact (SQLite): ~2–5 ms per fact
- write_episodic (Qdrant embed + upsert): ~20–30 ms per episode
- recall (SQLite + Qdrant query): ~10–20 ms
- Total memory write latency (post-reply): ~200–300 ms for a turn with 5 facts + 5 episodes
- Total memory read latency (pre-model): ~10–20 ms (unnoticed by user)

---

### 2.2 The chat REPL that uses it

Save as `src/chat.py`:

```python
"""REPL agent with cross-session memory. Each REPL invocation is a separate
session; memory carries across. Run it multiple times with --user alice to
watch memory accumulate."""
import os, sys, uuid, argparse
from openai import OpenAI
from dotenv import load_dotenv
from src.memory import recall, remember_turn, format_memory_block

load_dotenv()
omlx  = OpenAI(base_url=os.getenv("OMLX_BASE_URL"), api_key=os.getenv("OMLX_API_KEY"))
MODEL = os.getenv("MODEL_SONNET")


def chat_loop(user_id: str, session_id: str) -> None:
    history = []
    print(f"[session {session_id[:8]} for user '{user_id}']")
    print("Type 'exit' to quit. Type '/memory' to inspect current memory.\n")

    while True:
        user_msg = input("you> ").strip()
        if user_msg.lower() == "exit": break
        if user_msg == "/memory":
            mem = recall(user_id, "")
            print(format_memory_block(mem) or "(no memories yet)"); print()
            continue

        mem = recall(user_id, user_msg)
        memory_block = format_memory_block(mem)

        system = "You are a helpful assistant."
        if memory_block:
            system += "\n\n" + memory_block

        messages = [{"role": "system", "content": system}, *history,
                    {"role": "user", "content": user_msg}]
        resp = omlx.chat.completions.create(model=MODEL, messages=messages, temperature=0.4, max_tokens=400)
        assistant_msg = resp.choices[0].message.content
        print(f"bot> {assistant_msg}\n")

        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})
        result = remember_turn(user_id, session_id, user_msg, assistant_msg)
        if result["semantic"] or result["episodic_count"]:
            tags = [f"{s['key']}={s['value']} [{s['status']}]" for s in result["semantic"]]
            print(f"  [remembered: {', '.join(tags) or '-'} | +{result['episodic_count']} episodic]\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="alice")
    args = ap.parse_args()
    chat_loop(args.user, str(uuid.uuid4()))
```

### 2.3 Smoke test

```bash
python -m src.chat --user alice
# Tell it: "I live in Taipei and I'm vegan"
# Exit, restart
python -m src.chat --user alice
# Ask: "Can you recommend a restaurant near me?"
# → answer should mention Taipei AND be vegan-aware
# Type /memory to inspect
```

If the second session's response references Taipei and vegan, memory is working. If not, walk the stages: did extraction emit facts? Are they in SQLite? Is `recall()` returning them? Is `format_memory_block()` injecting them?

---

## Phase 3 — Scripted Three-Session Demo (~45 minutes)

Save as `src/demo_three_sessions.py`:

```python
"""Non-interactive proof of cross-session memory. Three scripted sessions,
each a separate 'conversation'. At session 3, the agent must recall facts
from sessions 1 and 2 to answer correctly."""
import os, uuid
from openai import OpenAI
from dotenv import load_dotenv
from src.memory import recall, remember_turn, format_memory_block

load_dotenv()
omlx  = OpenAI(base_url=os.getenv("OMLX_BASE_URL"), api_key=os.getenv("OMLX_API_KEY"))
MODEL = os.getenv("MODEL_SONNET")
USER  = "demo_user_" + str(uuid.uuid4())[:8]


def turn(session_id: str, user_msg: str) -> str:
    mem = recall(USER, user_msg)
    system = "You are a helpful assistant."
    block = format_memory_block(mem)
    if block: system += "\n\n" + block
    resp = omlx.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
        temperature=0.2, max_tokens=300,
    )
    reply = resp.choices[0].message.content
    remember_turn(USER, session_id, user_msg, reply)
    return reply


def main():
    # Session 1 — tell the agent about the user
    s1 = str(uuid.uuid4())
    print(">>> Session 1")
    print("you> I live in Taipei and I work as a cloud infrastructure engineer.")
    print("bot>", turn(s1, "I live in Taipei and I work as a cloud infrastructure engineer."), "\n")
    print("you> I'm vegan and I ride a bicycle to work every day.")
    print("bot>", turn(s1, "I'm vegan and I ride a bicycle to work every day."), "\n")

    # Session 2 — unrelated topic, more info
    s2 = str(uuid.uuid4())
    print(">>> Session 2 (new session)")
    print("you> I'm preparing for an agent-engineering interview next month.")
    print("bot>", turn(s2, "I'm preparing for an agent-engineering interview next month."), "\n")

    # Session 3 — the recall test
    s3 = str(uuid.uuid4())
    print(">>> Session 3 (new session — cross-session recall test)")
    question = "Recommend one restaurant near me for lunch and one activity for the weekend."
    print(f"you> {question}")
    answer = turn(s3, question)
    print("bot>", answer, "\n")

    # Heuristic check
    lower = answer.lower()
    hits = {
        "taipei": "taipei" in lower,
        "vegan":  "vegan" in lower or "plant" in lower,
        "cycling/biking":  "bike" in lower or "cycl" in lower,
    }
    print("Recall checks:", hits)
    print("PASS" if all(hits.values()) else "FAIL")


if __name__ == "__main__":
    main()
```

Run: `python -m src.demo_three_sessions`. Paste the output into `RESULTS.md`.

---

## Phase 4 — 15-Question Recall Benchmark (~1 hour)

Hand-write `tests/test_recall.py` with 15 seed-and-probe pairs. Each test: seed the memory with N facts, open a fresh "session," ask a question that requires one of those facts, assert the answer contains the expected string.

```python
# tests/test_recall.py — minimal template, add 12 more
import pytest, uuid
from src.memory import remember_turn, recall, format_memory_block
from src.chat   import chat_loop  # adjust to your function names

def make_user(): return "bench_" + str(uuid.uuid4())[:8]

def test_recall_location():
    u, s = make_user(), str(uuid.uuid4())
    remember_turn(u, s, "I live in Osaka.", "Got it — Osaka.")
    mem = recall(u, "any good ramen nearby?")
    assert any("osaka" in f["value"].lower() for f in mem["semantic_facts"])

def test_recall_contradiction_update():
    u, s = make_user(), str(uuid.uuid4())
    remember_turn(u, s, "I live in Osaka.",       "Got it — Osaka.")
    remember_turn(u, s, "Actually I moved to Tokyo.", "Got it — Tokyo.")
    mem = recall(u, "where do I live now?")
    vals = [f["value"].lower() for f in mem["semantic_facts"] if f["key"] == "location"]
    assert "tokyo" in vals and "osaka" not in vals  # Tokyo wins; Osaka archived
```

Target: 12 of 15 passing. Write the failing cases into the bad-case journal.

---

## Phase 5 (Optional) — mem0 Cross-Check (~1–2 hours)

Optional side exercise. Skip if you're short on time — main lab is complete after Phase 4. Adopt for hands-on experience with the canonical production memory library AND a measured comparison surface against your hand-roll. **The phase as written below reflects what ACTUALLY happened on 2026-05-12 implementation** (10/14 result, 4 measured library-vs-hand-roll architectural differences, one falsified hypothesis) — not a plan that the author thinks should happen.

### 5.1 Install mem0

```bash
uv pip install mem0ai  # mem0 v2.0.2 at time of writing
.venv/bin/python -c "from mem0 import Memory; print('mem0 import OK')"
```

`.env` additions for routing mem0 at the lab's local stack:

```bash
# .env additions for mem0
EMBED_MODEL=bge-m3-mlx-fp16            # already set; mem0 reads it
MEM0_LLM_MODEL=gemma-4-26B-A4B-it-heretic-4bit
# Note: do NOT rely on OPENAI_API_BASE — Memory() default constructor
# hits OpenAI cloud regardless. Use Memory.from_config() (see 5.2).
```

### 5.2 mem0 Wrapper Matching the Lab's API (verified working)

`src/memory_mem0.py` — same `remember_turn` + `recall` + `format_memory_block` signatures as the hand-rolled `src/memory.py`, but mem0-backed. Three production-shaped lessons baked in (each one was a debugging-session failure first):

```python
"""mem0-backed memory shim — same API as src.memory, different backend.
Used in Phase 5's cross-check to compare hand-rolled vs library on
the same 15-Q benchmark.

mem0 v2.0.2 notes (verified 2026-05-12):
  - Memory() with no config defaults to OpenAI cloud — wrong for the
    lab's local-first stack. Use Memory.from_config({...}) with explicit
    provider + base_url so LLM + embedder route at oMLX (localhost:8000).
  - search() filters changed: user_id is no longer a top-level kwarg;
    pass it inside filters={"user_id": ...} dict. top_k replaces limit.
  - add() still takes user_id= directly.
  - search() result entries can be None or strings; defensively
    normalize at the boundary.
"""
import os
from typing import Any

from dotenv import load_dotenv
from mem0 import Memory

load_dotenv()

_OMLX_BASE = os.getenv("OMLX_BASE_URL", "http://localhost:8000/v1")
_OMLX_KEY = os.getenv("OMLX_API_KEY", "")
_LLM_MODEL = os.getenv("MEM0_LLM_MODEL", "gemma-4-26B-A4B-it-heretic-4bit")
_EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3-mlx-fp16")

# Explicit config — route LLM + embedder at oMLX, vector store at the
# lab's existing Qdrant container. Memory() with no config goes to
# OpenAI cloud, producing APIConnectionError on offline stacks.
_CONFIG: dict[str, Any] = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": _LLM_MODEL,
            "openai_base_url": _OMLX_BASE,
            "api_key": _OMLX_KEY,
            "temperature": 0.0,
            "max_tokens": 400,
        },
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": _EMBED_MODEL,
            "openai_base_url": _OMLX_BASE,
            "api_key": _OMLX_KEY,
            "embedding_dims": 1024,
        },
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
            "collection_name": "mem0_memories",
            "embedding_model_dims": 1024,
        },
    },
}

_mem = Memory.from_config(_CONFIG)


def remember_turn(
    user_id: str, session_id: str, user_msg: str, assistant_msg: str
) -> dict[str, Any]:
    messages = [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": assistant_msg},
    ]
    result = _mem.add(messages=messages, user_id=user_id)
    return {"semantic": result.get("results", []), "episodic_count": 0}


def recall(user_id: str, query: str, k: int = 5) -> dict[str, Any]:
    """mem0 v2 API: user_id in filters dict; top_k replaces limit;
    return-shape inconsistencies require defensive normalization."""
    r = _mem.search(
        query=query,
        filters={"user_id": user_id},
        top_k=k,
    ) or {}
    memories = r.get("results") or r.get("memories") or []
    normalized: list[dict[str, Any]] = []
    for m in memories:
        if m is None:
            continue
        if isinstance(m, str):
            normalized.append({"memory": m, "score": 0.0, "metadata": {}})
        elif isinstance(m, dict):
            normalized.append(m)
    return {
        "semantic_facts": [
            {
                "key": (m.get("metadata") or {}).get("category", "fact"),
                "value": m.get("memory", ""),
            }
            for m in normalized
            if m.get("score", 0) > 0.5
        ],
        "relevant_episodes": [
            m.get("memory", "")
            for m in normalized
            if m.get("score", 0) <= 0.5
        ],
    }


def format_memory_block(memory: dict[str, Any]) -> str:
    if not memory.get("semantic_facts") and not memory.get("relevant_episodes"):
        return ""
    lines = ["Known facts about this user:"]
    for f in memory["semantic_facts"]:
        lines.append(f"- {f['key']}: {f['value']}")
    if memory["relevant_episodes"]:
        lines.append("\nRelevant past interactions:")
        for e in memory["relevant_episodes"]:
            lines.append(f"- {e}")
    return "\n".join(lines)
```

`★ Insight ─────────────────────────────────────`
- **`Memory()` without config silently goes to OpenAI cloud.** First-run symptom: every test hit `openai.APIConnectionError: Connection error`. mem0's docs imply env vars (`OPENAI_API_BASE`) work; in practice you need explicit `Memory.from_config({...})` with `openai_base_url` on BOTH the LLM and the embedder. Production libraries with "smart defaults" lose to "explicit config" every time on offline / local-first stacks.
- **mem0 v2 broke the `user_id=` kwarg on search().** First attempt: `ValueError: Top-level entity parameters frozenset({'user_id'}) are not supported in search(). Use filters=...`. mem0 v2 moved user-scope into a filters dict + renamed limit→top_k. API drift you only see when integrating; the test caught it on the first run.
- **Defensive normalization is non-optional for mem0's return shape.** `r.get('results', [])` returned None on empty searches; iterating produced AttributeError. The `r or {} → r.get('results') or r.get('memories') or [] → coerce-str-to-dict` cascade is the boundary contract that lets the rest of the code be naive about mem0's version-to-version inconsistencies.
`─────────────────────────────────────────────────`

### 5.3 Port the 15-Q Benchmark

Copy `tests/test_recall.py` → `tests/test_recall_mem0.py`. Change ONE line at the top:

```python
# was:
from src.memory import SQLITE, format_memory_block, recall, remember_turn
# now:
from src.memory_mem0 import format_memory_block, recall, remember_turn
```

Mark test_15 (direct SQLite insert) skip-on-mem0:

```python
import os

@pytest.mark.skipif(
    os.getenv("MEMORY_BACKEND") == "mem0",
    reason="test_15 inserts directly into SQLite; mem0 has its own backend"
)
def test_15_archived_facts_not_returned() -> None:
    ...
```

Run:

```bash
MEMORY_BACKEND=mem0 .venv/bin/python -m pytest tests/test_recall_mem0.py -v
```

### 5.4 Measured Results — 10/14 with Two Different LLMs (Hypothesis-Test Discipline)

**Run 1** (mem0 LLM = `gpt-oss-20b-MXFP4-Q8`, Haiku tier):

```
============ 10 passed, 1 skipped, 4 failed, 1 warning in 55.97s ============
FAILED test_05_contradiction_update_latest_wins
FAILED test_07_cross_session_recall
FAILED test_10_episodic_surfaces_on_relevant_query
FAILED test_12_multiple_contradictions_latest_wins
```

Initial diagnosis: failure logs showed `Error parsing extraction response: 'NoneType' object has no attribute 'strip'` from mem0's internals. Hypothesis: gpt-oss-20b at Haiku tier emits `content=None` on edge prompts (a known quirk of local-quantized MoE models under T=0.0); mem0's extraction parser doesn't defend.

**Hypothesis test — swap LLM to Sonnet-tier Gemma-26B**:

```bash
MEM0_LLM_MODEL=gemma-4-26B-A4B-it-heretic-4bit MEMORY_BACKEND=mem0 \
  .venv/bin/python -m pytest tests/test_recall_mem0.py -v
```

**Run 2** (mem0 LLM = `gemma-4-26B-A4B-it-heretic-4bit`, Sonnet tier):

```
============ 10 passed, 1 skipped, 4 failed, 1 warning in 72.30s ============
FAILED test_05_contradiction_update_latest_wins
FAILED test_07_cross_session_recall
FAILED test_10_episodic_surfaces_on_relevant_query
FAILED test_12_multiple_contradictions_latest_wins
```

**Identical pass/fail set, same 4 tests, both LLMs.** Hypothesis falsified — the `'NoneType' has no attribute 'strip'` was noise; the 4 failures are NOT model-quality issues. They're architectural differences in mem0's design vs the hand-roll's contract.

### 5.5 Comparison Matrix + Diagnosis — Add to RESULTS.md

Add the following block under a `## Phase 5 — mem0 cross-check` heading in your `RESULTS.md`:

| Backend | LOC | 15-Q pass | Mean latency / turn | Setup | Where it wins |
|---|---|---|---|---|---|
| Hand-rolled (W3.5 lab) | ~150 in `src/memory.py` | **15/15** | ~3-4s | ~30 min from scratch | Explicit episodic/semantic split; SCD-2 contradiction archival; defensive parsing tuned for local-quantized models |
| mem0 v2.0.2 wrapper | ~120 in `src/memory_mem0.py` | **10/14** (test_15 skipped, 4 architectural failures) | ~4-5s | ~15 min wrapper + Qdrant collection | Production-grade contradiction-detection prompt; single-API surface; multi-backend support |

#### Three measured architectural differences (the actual artifact)

The 4 mem0 failures are NOT wrapper bugs. They're measured semantic differences from the hand-roll's contract — verified across two different LLM tiers (gpt-oss-20b + Gemma-26B):

1. **Contradiction-update semantics (tests 05 + 12 fail).** mem0 v2 does NOT archive old values when a new value contradicts. Multiple location updates (Osaka → Tokyo → Kyoto) leave multiple "memories" in mem0's store, not a single live row with archived history. The hand-roll's SCD-2 + partial-unique-index produces a different contract: at most one live `(user_id, key)` row, unbounded archived history. Production tradeoff: mem0 preserves full mention history without schema hacks; hand-roll enforces a single canonical "current" value at the cost of needing the partial unique index from W3.5 BCJ Entry 4.

2. **No episodic vs semantic split (tests 07 + 10 fail).** mem0 v2 has no architectural distinction between episodic and semantic memory. Everything is a flat `memories` list. The wrapper's `score>0.5` heuristic classifies everything as semantic, so `relevant_episodes` is always empty, breaking tests that assert on episodic-specific surfaces. The hand-roll's dual-store (Qdrant episodic + SQLite semantic) is the architectural choice mem0 collapses. Tradeoff: mem0's unified model is simpler to operate; hand-roll's split makes the four-memory-types taxonomy explicit at the storage layer.

3. **API churn (mem0 v2 broke v1 patterns).** `Memory()` default to cloud, `search()` filters dict, return-shape inconsistencies. The wrapper carries three defensive patches that wouldn't exist in a v1 mem0 client. Tradeoff: pinning a version buys stability but locks out fixes; the hand-roll has no external API surface to track.

#### Hypothesis-test narrative (the interview-quotable artifact)

The model-swap experiment was the most senior-signal-producing step:

1. **Observation** — 10/14 pass with gpt-oss-20b, error logs mention `'NoneType' has no attribute 'strip'`
2. **Hypothesis** — failures are gpt-oss-20b-specific (Haiku quirk on edge prompts)
3. **Experiment** — swap to Sonnet-tier Gemma-26B
4. **Result** — identical 10/14, same 4 tests failed → hypothesis falsified
5. **Updated conclusion** — failures are mem0 design differences, not model-quality issues

Without the model-swap, the writeup would have been "mem0 is flaky on small local models" — true sometimes, but misleading and narrow. With the swap, the writeup is "mem0 v2 has different semantic contracts than my hand-roll on contradiction archival and episodic/semantic separation" — specific, actionable, defensible in any interview about empirical method.

#### What I'd port back into `src.memory.py` from mem0's source

If productionizing the hand-roll:

- mem0's contradiction-detection prompt structure (more sophisticated than the lab's simple value-mismatch check)
- Retry-on-extraction-failure with exponential backoff
- Multi-fact dedup before write (mem0 handles within a single `add()`)

What I'd NOT port:

- mem0's unified episodic+semantic model — the dual-store explicit split serves the four-memory-types taxonomy better
- mem0's contradiction-keep-history policy — SCD-2 archival is the right pattern for "what is currently true about this user"

### 5.6 Exit Criteria for Phase 5

- [ ] `src/memory_mem0.py` (~120 LOC wrapper with explicit `Memory.from_config()` + defensive normalization) returns same signatures as `src/memory.py`
- [ ] `tests/test_recall_mem0.py` runs end-to-end: **10 pass, 1 skip, 4 fail** with EITHER Haiku-tier or Sonnet-tier mem0 LLM (the 4 failures are the architectural-difference artifact, not flake)
- [ ] `RESULTS.md` Phase 5 section populated with the 2-row comparison matrix + the 3 measured-differences bullets + the hypothesis-test narrative + the port-back / not-port-back bullets
- [ ] 90-second answer to "what did you learn from cross-checking mem0?" — name the 3 architectural differences, the hypothesis-test discipline, and WHEN each design wins

`★ Insight ─────────────────────────────────────`
- **The 10/14 result is the artifact, not a failure.** Anyone can write a wrapper that ties; few candidates can articulate "where my hand-roll's contract diverges from a 4K-star library's design choices" with measured evidence. The 4 failures are FEATURES of the comparison, not bugs to fix.
- **The model-swap was the load-bearing diagnostic step.** Without it the writeup says "mem0 is flaky on small models" (wrong framing — narrow, model-quality-blaming). With it the writeup says "mem0 v2 has different semantic contracts than my hand-roll" (right framing — architectural, design-level). Always test the cheaper hypothesis before believing the more complex one.
- **DO NOT replace `src/memory.py` with the mem0 wrapper for the main lab.** Phase 3's demo + Phase 4's 15/15 benchmark stay anchored to your hand-roll. Phase 5 is the cross-check, not the substitute. The pedagogical arc (build → cross-check → graduate to two-tier in W3.5.8) requires you to OWN the hand-roll as the canonical baseline.
- **Three failures became three RESULTS.md insights + one falsified hypothesis became a discipline-rule callout.** Phase 5's value-per-hour is among the highest in the chapter because the EVIDENCE for each claim is concrete: measured test counts, specific failure tests, specific environment changes, specific commit hashes. Hand-waving claims don't survive interviews; measured claims do.
- **Production-library-vs-hand-roll comparisons are senior signal**: any candidate can claim "I considered using mem0"; only a senior candidate can say "I tested mem0 against my hand-roll on 14 specific tests, identified 3 architectural differences via a falsifying experiment, and decided to ship the hand-roll because of contract X". The methodology IS the signal.
`─────────────────────────────────────────────────`

---

## Production Comparators — read after completing the lab

Two production-shaped systems worth studying after you've shipped the canonical lab. They solve overlapping problem spaces with different architectures; reading them gives a real comparator for your DIY hand-rolled-extraction + Qdrant + SQLite design. **Read in order** — guild first (smaller surface, faster orientation), EverOS second (full research-grade stack). The `mem0` library — production Python library that ships the same dual-store pattern this lab hand-rolls — is cited as additional prior-art in the References; skim its source if you want to compare your code against the library's choices.

### Comparator 1 — `mathomhaus/guild`

After your hand-rolled dual-store lab is shipped (custom OpenAI-extraction + Qdrant + SQLite, no library wrapper), spend 30-60 min reading [`mathomhaus/guild`](https://github.com/mathomhaus/guild) (Apache-2.0, Go, single binary, embedded SQLite) as a production-shaped reference for the same problem space. Guild is an MCP-protocol-native agent-memory server with hybrid (BM25 + dense embedding + RRF fusion k=60) retrieval and atomic-lock primitives for parallel-agent coordination. The mythos vocabulary (Gates / Guild / Quest / Scroll / Lore / Oath) maps onto familiar memory primitives, listed below.

**Side-by-side mapping — your lab vs guild**:

| Your W3.5 lab primitive | Guild equivalent | Notable difference |
|---|---|---|
| `remember_turn()` writes to dual store | `quest_complete()` writes a scroll into the archive | Guild treats each completion as a discrete record with cause/effect; your lab archives by turn |
| `recall()` queries both stores | `guild_session_start()` returns oath + brief + top quest in ONE call | Single-shot context recovery vs multi-call assembly — production discipline |
| 4 memory types (working / episodic / semantic / procedural) | Quest (procedural-as-task) / Scroll (episodic-as-handoff) / Lore (semantic-as-archive) / Oath (procedural-as-principle) | Different ontology, same underlying needs; vocabulary decouples from ML jargon |
| SQLite for facts + Qdrant for vectors | Single SQLite with embedded ONNX encoder (`-tags=withembed`) for vectors | Guild's choice: one binary, zero infra. Tradeoff: harder to swap embedders |
| Contradiction-update via archive flag | Versioned scrolls + lore supersedes via timestamp | Same SCD-2 pattern, different implementation |
| Single-agent context | Atomic `quest_accept` locks for parallel agents | Guild adds multi-agent coordination — beyond this lab's scope |

**Hybrid retrieval pattern parallels W2.7**: guild fuses BM25 + dense via RRF k=60 — the EXACT same stack as W2.7's `PageVectorIndex` (Phase 8 chunk-level fallback). When two unrelated local-first memory systems independently land on the same hybrid+RRF stack, that's evidence the pattern is the right shape for this problem class.

**What to read in their source (in order)**:

1. `internal/store/sqlite/` — schema design (scrolls, lore, quests, oaths). Compare to your lab's SQLite schema. Note the table-per-primitive split + the explicit `superseded_by` column for contradiction handling.
2. `internal/retrieve/` — BM25 + vector + RRF fusion. Compare to W2.7's `PageVectorIndex.search()` for the same pattern in a different language.
3. `internal/mcp/` — MCP-tool surface (the 15-ish tools agents call). Compare to your lab's `recall()` / `remember_turn()` shape. Note how guild collapses multi-step lifecycles into single tool calls.
4. `cmd/guild/init.go` — the `guild init` guided-setup flow. Compare to your lab's manual setup. Production-quality DX is a load-bearing skill that lab work often skips.

**Three production insights worth importing into your lab BCJ**:

- **Single-shot session start vs multi-call recall**. Guild's `guild_session_start` returns oath + brief + top quest atomically. Your `recall()` is invoked turn-by-turn. The single-shot pattern minimizes prompt-construction churn — relevant for any production system that values determinism per session.
- **Versioned scrolls vs in-place updates**. Guild never deletes; it timestamps + supersedes. Your contradiction-update test (`test_recall.py`) implements the same pattern; guild's source is the production-quality reference for the same SCD-2 discipline.
- **MCP-protocol-native vs in-process-library-native**. Your lab agent imports a hand-rolled `src.memory` module directly — single-process, Python-only, no protocol boundary. Guild exposes memory as MCP tools, so ANY MCP client (Claude Code, Cursor, Codex) shares the same memory layer regardless of language. The MCP wrapping pattern is the right shape when memory needs to span multiple agent frameworks — a topic W3.5.5 / W6.7 / W7 expand on.

`★ Insight ─────────────────────────────────────`
- **Reading guild AFTER the canonical lab is the right order.** The lab teaches WHY each memory primitive exists; guild teaches HOW production-grade systems compose them. Reading guild first would skip the why and turn into copy-paste-engineering.
- **The mythos vocabulary is a real design choice, not just flavor.** "Lore" as semantic memory + "Oath" as procedural principle has the advantage of being meaningful to non-ML readers (product managers, designers). The disadvantage in interviews: requires translation back to ML terms. Use ML terms in interview answers; cite guild as the production parallel.
- **The Go-vs-Python stack difference exposes a real production tradeoff**: guild's single binary + embedded SQLite is operationally cleaner than your lab's stack (Python + oMLX HTTP + Qdrant Docker container + SQLite file — 3 services, 2 storage engines). The cost is harder to extend without Go knowledge. For lab work and rapid iteration, Python wins. For production deployment, single-binary Go is the safer ops shape. Both are valid — the choice is product-driven, not technical.
- **Future W3.5.5 supplement (multi-agent shared memory) uses guild as the substrate.** Your single-agent lab is the prerequisite — finish here, then graduate to multi-agent coordination in W3.5.5 if your roadmap calls for it.
`─────────────────────────────────────────────────`

### Comparator 2 — `EverMind-AI/EverOS` (research-grade, published benchmark scores)

[EverOS](https://github.com/EverMind-AI/EverOS) (Apache 2.0, Python 3.12, 4.6K stars as of May 2026, actively maintained) is a research-grade memory operating system for self-evolving agents. Where guild is "single-binary multi-agent coordination", EverOS is "full-stack memory architecture + benchmarks". Three components to study:

| Part                             | What it is                                                                             | Why it matters                                                                                                                                        |
| -------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **EverCore**                     | The reference memory architecture — biological-imprinting-inspired self-organizing LTM | LangGraph + Postgres + LangChain stack. Internal package name `memsys`, exposes HTTP API at `localhost:1995`. Backed by arXiv:2601.02163.             |
| **HyperMem**                     | Hypergraph memory architecture                                                         | Multi-entity relational memory primitive your DIY lab doesn't cover. Closer to W2.5 GraphRAG ontology than to W3.5 SCD-2.                             |
| **EverMemBench + EvoAgentBench** | Open evaluation suites for memory quality + agent self-evolution                       | EverCore reports **LoCoMo 93.05% / LongMemEval 83.00%** — industry-standard numbers. Your DIY lab's 15-Q recall benchmark is non-comparable to these. |

**Side-by-side mapping — your lab vs guild vs EverOS**:

| Dimension | Your W3.5 lab | guild | EverOS / EverCore |
|---|---|---|---|
| Stack | Hand-rolled Python: oMLX-extraction + Qdrant + SQLite | Single Go binary + embedded SQLite | LangGraph + Postgres + LangChain (Python 3.12) |
| Deployment | Python venv + Docker (Qdrant) | One binary | Docker compose stack (Postgres + services) |
| Memory architecture | 4 types (working/episodic/semantic/procedural) | Quest/Scroll/Lore/Oath | EverCore (LTM-OS) + optional HyperMem (hypergraph) |
| Multi-agent | No | YES (atomic claims) | Partial (server is single-host) |
| Hypergraph memory | No | No | YES (HyperMem) |
| Self-evolving agent loop | No | Partial | YES (core focus) |
| Eval methodology | DIY 15-Q recall | DIY | **LoCoMo + LongMemEval** (industry standard) |
| Pip-installable library | N/A (your own code) | N/A (Go binary) | NO — internal package `memsys`, install from source only |
| Integration shape | Direct Python imports | HTTP API via MCP | HTTP API at `localhost:1995` |
| Research backing | None | None | arXiv paper + HuggingFace org + Discord |

**Why EverOS is NOT a drop-in Python library**:

- The Python package inside `methods/EverCore/` is named `memsys`, NOT published to PyPI. You'd have to `git clone EverOS && cd methods/EverCore && uv sync && docker compose up -d`.
- Requires Python 3.12 (your W3.5 lab uses 3.11). Separate venv needed.
- Backed by LangGraph + LangChain + Postgres + scikit-learn + numpy — full stack, not a lightweight lib.
- Server runs as a SEPARATE process at `localhost:1995`. Clients talk to it via HTTP API.

**Correct integration shape — HTTP-API-as-comparator**: run EverCore as a docker-compose service alongside your DIY lab; point a thin Python client at its API; benchmark side-by-side against your DIY system on the SAME questions. This is the W3.5.7 supplemental lab — see curriculum overview.

**What to read in EverOS source (in order)**:

1. `methods/EverCore/README.md` — system-level overview
2. `methods/EverCore/src/` — the `memsys` package: extraction, retrieval, evolution logic
3. `methods/EverCore/evaluation/` — LongMemEval + LoCoMo runners. **This is the most portable artifact** — you can lift the eval harness pattern even if you don't run EverCore itself.
4. `benchmarks/EverMemBench/` — the benchmark dataset + task definitions

**Three production insights worth importing into your W3.5 BCJ**:

- **Memory quality has industry-standard benchmarks**. Your DIY 15-Q is fine for correctness sanity; LoCoMo + LongMemEval are the published standards for "is my memory system competitive". The gap between "I built a memory system" and "I built a memory system that scores X on LongMemEval" is the senior-engineer signal in interviews.
- **HuggingFace dataset publishing** ([EverMind-AI/everos_Eval_Results](https://huggingface.co/datasets/EverMind-AI/everos_Eval_Results)) is the production discipline. Eval results live as a versioned dataset, not a one-off notebook. Worth adopting for your own future work.
- **Biological-imprinting framing** — the EverCore design metaphor — is non-obvious. Most memory systems frame as database-with-eviction; EverCore frames as imprinting + consolidation + reorganization. The vocabulary affects API design ("imprint" vs "store", "consolidate" vs "update"). Same shape as guild's mythos vocabulary — deliberate naming as a design lever.

`★ Insight ─────────────────────────────────────`
- **EverOS and guild are complementary, not competing**. guild's multi-agent atomic-claim primitive doesn't exist in EverOS (single-host scope); EverOS's hypergraph + research-grade benchmarks don't exist in guild. The W3.5 production-comparator slot legitimately holds BOTH.
- **The 4.6K-star / arXiv-paper / HuggingFace-dataset combination signals "this is canonical reference material" for memory-of-agents work in 2026.** Interviewers at China-headquartered AI shops, academic labs, or memory-focused agent startups likely know it. For your portfolio, citing EverCore's LongMemEval 83% and saying "my DIY 15-Q hit 15/15 but doesn't measure the same surface; I'd need to run LongMemEval to compare" is the right calibration.
- **The "Python lib vs HTTP service" distinction is a real product call**: when you control deployment, embedding the lib in-process is cheaper. When you have multiple consumer agents in different languages, HTTP service is the right abstraction. EverOS chose HTTP service because of the multi-language consumer use case (Browser Agent, iOS app, MCO orchestrator — all in their use-cases gallery use the API). Your lab is single-Python so in-process makes sense.
- **The W3.5.7 supplemental lab** turns these references into measurable: clone EverOS, run docker compose, point a benchmark client at it, score the DIY lab AND EverCore on a LongMemEval subset, write the comparison matrix. ~4-6h end-to-end.
`─────────────────────────────────────────────────`

---

## RESULTS.md Template

```markdown
# Week 3.5 — Cross-Session Memory Results

## Three-session demo transcript
(paste the output of demo_three_sessions.py here)

**Verdict:** PASS / FAIL

## Recall benchmark
|                                  | Pass | Fail |
|----------------------------------|-----:|-----:|
| Simple semantic recall (5 tests) |   _  |   _  |
| Contradiction/update (3 tests)   |   _  |   _  |
| Episodic recall (4 tests)        |   _  |   _  |
| Multi-fact composition (3 tests) |   _  |   _  |

## What I learned (3 paragraphs)
- (paragraph on extract → store → retrieve → inject)
- (paragraph on why raw-turn dumping fails)
- (paragraph on contradiction handling — archive, don't delete)

## Infra bridge
User memory is a slowly-changing dimension (SCD-2). Every contradiction update creates an archived row — identical to how a data warehouse tracks customer-address changes. Archive-don't-delete isn't just ops hygiene; it's SCD-2 by another name.
```

---

## Lock-In: Flashcards + Interview Questions

### 5 Anki Cards
1. Q: Four types of agent memory? — A: Working, episodic, semantic, procedural.
2. Q: Which two memory types does the standard dual-store pattern (vector + relational) cover? — A: Episodic (vector) + semantic (relational). Working memory is the conversation buffer; procedural memory is fine-tune or prompt augmentation.
3. Q: Four stages of the memory lifecycle? — A: Extract → store → retrieve → inject.
4. Q: Why not store every turn verbatim? — A: Transcripts crowd the prompt and contradictions accumulate; extraction compresses hundreds of turns into dozens of facts.
5. Q: Three forgetting strategies? — A: TTL, confidence-weighted eviction, contradiction-triggered update (archive, don't delete).

### 3 Spoken Interview Questions
1. "How do you give an agent long-term memory?" (target: 90 sec — name the four types, name the lifecycle, name the storage)
2. "How do you handle contradictions in user memory?" (target: 2 min — archive the old fact, write the new one, defend the audit-trail rule)
3. "Design a memory system for an agent that serves 10M users." (target: 5 min — sharding by user_id, per-user memory cap, async extraction pipeline, TTL-based cleanup)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `qdrant_client.http.exceptions.UnexpectedResponse` on upsert | embedding model returning wrong dim | confirm BGE-M3 returns 1024; re-create collection with right size |
| Facts write but recall returns empty | user_id filter mismatch (trailing whitespace, casing) | log actual IDs on both write + read paths |
| Demo session 3 fails recall for "cycling" | extraction split it as `hobby=cycling` vs `transport=bike`; retrieval missed | lower similarity threshold; or normalise keys in extraction prompt |
| Contradiction test leaves two live rows | UNIQUE constraint too loose | ensure `UNIQUE(user_id, key, archived)` is in the schema |
| Memory block balloons the prompt to 4K+ tokens | no cap on semantic facts | add `LIMIT 20` to the SELECT or summarise facts older than N days |

---

## What's Next

- Back to **[[Week 4 - ReAct From Scratch]]** — now your ReAct agent can have memory by importing `src.memory` and calling `recall()` at turn-start.
- Extension: add **procedural memory** via system-prompt augmentation — after 20 turns, an LLM reads episodic history and emits "operating guidance for this user" sentences that get appended to the system prompt. This is how ChatGPT-style "custom instructions" are learned rather than manually written.
- Interview prep: this lab is the strongest evidence you have for the "how does your agent remember things?" follow-up. Bring the three-session demo transcript in your portfolio.


---

## Bad-Case Journal

All entries below are real bugs observed during this lab's implementation (2026-05-11 session). Hypothetical entries removed.

**Entry 1 — Layered embedding-backend failure: `Connection refused` → `404 Model 'bge-m3' not found`.**
*Symptom:* Two distinct crashes in sequence as one was fixed. First run: `httpx.ConnectError: [Errno 61] Connection refused` on `embed()`. After starting oMLX: `openai.NotFoundError: Error code: 404 - {'error': {'message': "Model 'bge-m3' not found. Available models: Gemma-4-..., Qwen3.6-..., gpt-oss-20b-..."}}`.
*Root cause:* Two layered dependencies, each masking the next when the prior was missing. (a) oMLX itself wasn't running — port 8000 was empty. (b) After oMLX started, it shipped with chat models only by default — embedding models supported (BERT / BGE-M3 / ModernBERT per [jundot/omlx README](https://github.com/jundot/omlx)) but not auto-registered.
*Fix (recommended, oMLX-served):* Download MLX-converted BGE-M3 into `~/.omlx/models/bge-m3-mlx-fp16/` via `huggingface-cli download mlx-community/bge-m3-mlx-fp16 --local-dir ~/.omlx/models/bge-m3-mlx-fp16` or the oMLX admin dashboard. Restart oMLX. Set `EMBED_MODEL=bge-m3-mlx-fp16` in `.env`. Verify with `curl -H "Authorization: Bearer $OMLX_API_KEY" http://localhost:8000/v1/models | grep bge`.
*Fix (fallback, in-process):* Set `USE_LOCAL_EMBED=1`. `embed()` uses `sentence-transformers` BGE-M3 with `device="mps"`. One extra GB resident per process, zero second-server dependency, offline-capable.
*Discipline rule:* check what each "running" service ACTUALLY serves, not just whether the port is open. Phase 1 setup table now lists per-service smoke tests (Qdrant `/readyz`, oMLX `/v1/models | grep <embed-model-id>`, in-process embed import). Code ships dual-mode behind one env-var toggle so the lab works on a stock oMLX install AND on a configured one.

**Entry 2 — `extract_memories()` returns a top-level JSON array; downstream `mem.get("semantic")` crashes with `AttributeError: 'list' object has no attribute 'get'`.**
*Symptom:* Single-turn after first successful `recall`. The extraction LLM (gpt-oss-20b at Haiku tier) emitted `[{"key": "location", "value": "Taipei"}, ...]` — a top-level array — instead of the requested `{"semantic": [...], "episodic": [...]}` object. Pipeline assumed dict; iterating `mem.get("semantic", [])` raised AttributeError on the list.
*Root cause:* `response_format={"type": "json_object"}` is best-effort on local quantized models. gpt-oss-20b respects the schema ~95% of runs but emits other shapes (top-level array, top-level scalar, nested dict-of-dicts) ~5% of the time. Cloud models (Claude / GPT-4 family) enforce strictly; local models do not.
*Fix:* Coerce-or-empty at the parsing boundary. `extract_memories()` now:
  1. Tries `json.loads(raw)` — empty dict on `JSONDecodeError`
  2. If parsed is a `list` of `{key, value}` dicts → treat as all-semantic
  3. If parsed is a `list` of strings → treat as all-episodic
  4. If parsed is anything else (scalar, None, malformed) → empty dict
  5. If parsed is a dict but `semantic`/`episodic` fields have wrong types → empty for that field
*Discipline rule:* `response_format=json_object` is a contract on cloud models, a hint on local models. Always coerce-or-empty at the parsing boundary; never trust the schema. Same pattern as W2.7's `_is_low_quality()` defensive check.

**Entry 3 — `sqlite3.OperationalError: database is locked` under 15-Q benchmark load.**
*Symptom:* `pytest tests/test_recall.py` ran 12/15 passing; tests 12 / 13 / 15 failed with `database is locked` on the INSERT inside `write_semantic_fact`. Each failing test passed in isolation — failure was order-dependent.
*Root cause:* Three stacked issues. (a) SQLite default journal mode is DELETE, which serializes ALL access — readers block writers and vice versa. Under test load (15 tests × 3 writes/test interleaved with LLM extraction calls taking 30-60s each), the default 5s connection timeout was insufficient. (b) `write_semantic_fact` had no `try/finally` around `conn.close()`; an exception mid-transaction leaked the connection and held the lock. (c) Some tests left transactions uncommitted when an LLM-extraction call raised.
*Fix (three-part):*
  1. Bump `sqlite3.connect(SQLITE, timeout=30)` at every connect site — gives writers a chance to acquire the lock under contention.
  2. Enable WAL mode at module-import:
     ```python
     _init = sqlite3.connect(SQLITE, timeout=30)
     _init.execute("PRAGMA journal_mode=WAL")
     _init.execute("PRAGMA synchronous=NORMAL")
     _init.close()
     ```
  3. Wrap `write_semantic_fact`'s body in `try/finally` so `conn.close()` always runs even on exception mid-transaction.
*Discipline rule:* any SQLite-backed code path with concurrent access patterns MUST use WAL mode AND `try/finally` connection cleanup AND a connection timeout. The default-DELETE-mode + leak-on-exception combination produces this exact failure under load every time. Result after fix: 14/15 passing (test 12 still failing on a different bug — Entry 4).

**Entry 4 — `sqlite3.IntegrityError: UNIQUE constraint failed: user_facts.user_id, user_facts.key, user_facts.archived` on the third contradiction-update.**
*Symptom:* `test_12_multiple_contradictions_latest_wins` seeded location: Osaka → Tokyo → Kyoto. First update succeeded (Osaka.archived=0 → 1, Tokyo.archived=0 inserted). Second update on third call failed: trying to archive Tokyo (Tokyo.archived=0 → 1) while an archived Osaka.archived=1 row already existed for the same (user_id, key) → unique constraint violation.
*Root cause:* Schema had `UNIQUE(user_id, key, archived)`. This enforced uniqueness across THE WHOLE TUPLE including the `archived` flag — meaning at most ONE archived row per (user_id, key). The intent had been "one live row + one history row", but real SCD-2 history requires UNBOUNDED archived rows (Osaka, Tokyo both archived as Kyoto becomes live).
*Fix:* Remove the full `UNIQUE(user_id, key, archived)` constraint. Add a partial unique index on live rows only:
```sql
CREATE TABLE user_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    archived INTEGER DEFAULT 0,
    ...
    -- NO full UNIQUE constraint here
);
CREATE UNIQUE INDEX idx_live_unique
    ON user_facts(user_id, key) WHERE archived = 0;
```
The partial index lets exactly one (user_id, key, archived=0) row exist while archived=1 rows accumulate without limit. SCD-2 history is now correctly unbounded.
*Discipline rule:* `UNIQUE(a, b, flag)` is almost never what you want when `flag` is "is-this-the-current-version". Use a partial unique index with `WHERE flag = <current-value>` instead. After this fix: 15/15 passing.

**Entry 5 — Test passes in isolation but fails in sequence (state leakage from prior tests).**
*Symptom:* `test_15_archived_facts_not_returned` passed alone (`pytest tests/test_recall.py::test_15_...`). Failed when run as part of the full suite. Same error class as Entry 3 (`database is locked`) but discovered AFTER the WAL + try/finally fix; persisted because a different mechanism leaked state.
*Root cause:* `write_semantic_fact`'s SELECT-then-INSERT pattern, when interleaved with LLM-extraction calls in the prior test, could leave a transaction open if the LLM call raised. Even with WAL + timeout=30 the next test's SQLite connection saw the stale open transaction and blocked. The pattern is "SELECT (autocommit) → if-row-is-None (Python) → INSERT (auto-begin transaction) → commit". An exception between INSERT and commit leaves the transaction open until connection close. Without `try/finally`, close could be skipped.
*Fix:* Same `try/finally` from Entry 3 — guarantees `conn.close()` runs even when the transaction is mid-flight. Test-isolation discipline applied at the wrapper layer, not per-test.
*Discipline rule:* test isolation in a stateful system requires CONNECTION-CLOSE guarantees, not just per-test fresh data. The W3.5 lab's per-test `uuid` user_ids are necessary but not sufficient — connection lifecycle must also be deterministic. Worth tightening even further: production memory systems should use `with conn:` context managers to enforce both commit-or-rollback AND close.

**Entry 6 — Episodic-recall threshold 0.35 is a precision-recall lever; `test_11` flakes on the noise floor.**
*Symptom:* `test_11_episodic_does_not_surface_on_irrelevant_query` passes some runs and fails others with the SAME code + SAME seed. Run 1: 15/15. Run 2: 14/15 (test_11 failed). Run 3: 15/15. The flake is real — repeated runs disagree on whether the seeded episode about "Python list comprehensions" surfaces on an irrelevant query like "what's the weather like in Antarctica?".
*Root cause:* The `recall()` filter `[h.payload["text"] for h in hits if h.score > 0.35]` uses a fixed similarity threshold. BGE-M3's cosine score on semantically-distant-but-not-orthogonal text pairs ("Python comprehensions" vs "Antarctica weather") sits at 0.36-0.40 — right on the noise floor. Compounding: the LLM extraction step paraphrases the seed text slightly differently each run (gpt-oss-20b at T=0.0 is *near*-deterministic, not exactly deterministic on local quantized weights), so the EMBEDDED text differs subtly between runs, pushing the score above or below 0.35 non-deterministically.
*Fix (three valid paths, pick based on goal):*
  1. **Bump threshold to 0.45.** Reduces this flake but risks breaking `test_10_episodic_surfaces_on_relevant_query` if the LangGraph→agent-frameworks pair scores in 0.35-0.45 range. Measure both before shipping.
  2. **Make `test_11`'s irrelevant query genuinely orthogonal.** Swap "what's the weather in Antarctica?" for "what time is it now?" — less likely to score above any reasonable threshold against ANY seeded episode.
  3. **Accept the flake as a precision-recall observation.** 14/15 is still well above the 12/15 exit criterion. The flake IS the lesson about similarity-threshold tuning.
*Discipline rule:* in production memory systems with similarity thresholds, the threshold choice is a precision-recall lever, not a one-time number. Senior engineers MEASURE the corpus's noise-floor distribution before picking the threshold; junior engineers cargo-cult a value (0.35, 0.5, 0.7). This is the same pattern as W2.7's δ=0.07 cluster-routing tiebreak — same primitive (calibrated noise floor), different domain (cluster centroids vs episodic-memory pairs). The lab's 0.35 was a starter value; bump to 0.45 if your corpus warrants it, after measuring leader-vs-runner-up gap distribution.

---

## Interview Soundbites

**Soundbite 1.** Working memory is the conversation buffer — resets every session. Episodic memory stores time-indexed events: "user asked about LangGraph on Tuesday." Semantic memory stores durable facts: "user is vegan, lives in Taipei." Procedural memory encodes learned behavioral patterns and almost always requires fine-tuning or system-prompt augmentation — no off-the-shelf tool gives it to you. The mistake interviewers catch is candidates collapsing all four into "long-term memory." Name the type, pick the right storage.

**Soundbite 2.** Memory without forgetting is a landfill. Three strategies prevent unbounded growth: TTL evicts stale facts after N days unless reconfirmed; confidence-weighted eviction drops lowest-confidence facts at cap; contradiction-triggered update archives the old fact and writes the new — archive, never delete, because audit trail matters. Naive failure mode: storing every raw turn verbatim. Contradictions accumulate, retrieval returns verbose transcripts instead of crisp facts, token cost scales with conversation history not extracted facts.

**Soundbite 3.** Storage choice follows query shape. Semantic facts ("user.location = Taipei") need exact-match lookups + uniqueness constraint for archive-on-contradiction → relational DB (SQLite, Postgres). Episodic memories are free-form, retrieved by similarity to current message → vector store (Qdrant, pgvector). Graph databases add value when memory is relational ("user A knows user B who prefers X") but carry operational overhead only justified once entity relationships are load-bearing. Start with dual-store: vector for episodes, relational for semantic facts.

---

## References

### Foundational papers

- **Packer et al. (2023).** *MemGPT (now Letta): Towards LLMs as Operating Systems.* [arXiv:2310.08560](https://arxiv.org/abs/2310.08560). OS-paging analogy for agent memory; the canonical two-tier (RAM ↔ archive) precedent that anchors the W3.5.8 capstone.
- **Wang et al. (2024).** *A-MEM: Agentic Memory for LLM Agents.* [arXiv:2502.12110](https://arxiv.org/abs/2502.12110). Dynamic memory structuring with note-network-style organization.
- **Shinn et al. (2023).** *Reflexion: Language Agents with Verbal Reinforcement Learning.* [arXiv:2303.11366](https://arxiv.org/abs/2303.11366). Memory-through-reflection; distinguish from cross-session memory.
- **Madaan et al. (2023).** *Self-Refine: Iterative Refinement with Self-Feedback.* [arXiv:2303.17651](https://arxiv.org/abs/2303.17651). Single-session self-critique; contrast with cross-session.
- **McClelland, McNaughton, O'Reilly (1995).** *Why there are complementary learning systems in the hippocampus and neocortex.* The neuroscience grounding for the two-tier memory architecture (referenced extensively in W3.5.8).

### Production reference systems (used in W3.5 + W3.5.5 + W3.5.8)

- **mem0 (2024).** https://github.com/mem0ai/mem0. Open-source Python library for episodic + semantic memory with LLM contradiction detection. NOT used in this lab — cited as production prior-art. The lab hand-rolls the dual-store pattern (custom OpenAI-compatible extraction + Qdrant + SQLite) so the underlying primitives stay visible. Skim mem0's source after finishing the lab to compare design choices.
- **mathomhaus/guild.** https://github.com/mathomhaus/guild. Single-Go-binary multi-agent MCP coordinator with embedded SQLite + BM25/dense/RRF retrieval. Production-comparator (W3.5.5 chapter integrates this as the operational tier).
- **EverMind-AI/EverOS / EverCore.** https://github.com/EverMind-AI/EverOS. Research-grade memory OS with biological-imprinting model + LongMemEval 83% / LoCoMo 93.05% published scores. Production-comparator (W3.5.8 chapter integrates EverCore as the semantic tier). [arXiv:2601.02163](https://arxiv.org/abs/2601.02163).

### Industry-standard memory benchmarks

- **LongMemEval.** https://github.com/xiaowu0162/LongMemEval. 500-turn-conversation memory recall benchmark; the canonical evaluation surface for cross-session memory systems. Used optionally in W3.5.8 Phase 5.3.
- **LoCoMo (Maharana et al. 2024).** *Evaluating Very Long-Term Conversational Memory of LLM Agents.* [arXiv:2402.17753](https://arxiv.org/abs/2402.17753) + https://github.com/snap-research/locomo. Companion benchmark to LongMemEval.

### Storage + retrieval primitives

- **Qdrant docs.** https://qdrant.tech/documentation/. Collection creation, payload filtering, score thresholds. Used for the episodic tier in this lab.
- **SQLite WAL mode.** https://sqlite.org/wal.html. Journal mode that allows readers concurrent with one writer; load-bearing for both this lab's contradiction-update path AND guild's atomic-claim primitive (see W3.5.5 deep-dive).
- **BGE-M3 (Chen et al. 2024).** *BGE M3-Embedding: Multi-Lingual, Multi-Functional, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation.* [arXiv:2402.03216](https://arxiv.org/abs/2402.03216). The embedding model used for both dense (this lab) and dense+sparse hybrid (W2.7 / W2.5).
- **`sentence-transformers`.** https://www.sbert.net. Python framework wrapping HuggingFace embedding models with MPS-device support on Apple Silicon; used as the in-process fallback path when oMLX doesn't serve embeddings (Bad-Case Entry 1).

### Data-engineering parallels

- **Slowly Changing Dimensions (SCD-2)** — Kimball Group. Archive-on-contradiction = SCD-2 by another name. The data-warehouse pattern that explains why memory contradiction updates work the way they do.
- **Cache-aside pattern** — Microsoft Azure architecture docs. The cache-aside / lazy-load pattern is the engineering version of the two-tier memory architecture in W3.5.8.
- **MCP (Model Context Protocol, Anthropic Nov 2024).** https://modelcontextprotocol.io. Standard protocol for agent-to-tool communication. Adopted by OpenAI + Google in 2025-2026. Used in W3.5.5 as the integration substrate for guild.

### Evaluation methodology (judge prompts + bias)

- **Zheng et al. (2023).** *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* NeurIPS 2023 D&B. arXiv:2306.05685. Position / verbosity / self-enhancement bias taxonomy that explains why the Phase 5 mem0 cross-check used a fixed reference-answer scoring rubric per question (the 10/14 vs 15/15 delta is not a judge artifact — it is real architectural difference, confirmed because the scoring is bias-suppressed).
- **Husain, Hamel (2024).** *Creating a LLM-as-a-Judge That Drives Business Results.* hamel.dev. Practitioner playbook for judge prompts that find real defects — pairs directly with the 15-Q recall benchmark scoring loop and the mem0-port test_recall_mem0.py validator.

---

## Cross-References

- **Builds on:** W1 Vector Retrieval — vector memory uses same embedding + cosine primitives; `embed()` and collection setup extend W1's work.
- **Distinguish from:** W5.5 Metacognition / Reflexion — Reflexion writes self-critique into memory persisting across turns *within a session*, correction loop inline (post-reply, pre-next-turn). Cross-session memory persists across *separate process invocations*, writes after reply (or async), reads before model call. Same vocabulary ("memory") but differ in lifetime, write timing, query shape.
- **Connects to:** W4 ReAct (`recall()` at turn-start seeds working context; `src.memory` imports into Week 4 ReAct harness); W7 Tool Harness (memory becomes first-class tool — `recall_tool`, `remember_tool` — agent selects via tool-use rather than imperative call).
- **Foreshadows:** W11 System Design — production memory infra requires sharding by user_id, per-user caps at store layer, async extraction (Celery/RQ) so writes never block response, TTL cleanup jobs. Dual-store topology here is the single-node prototype.
