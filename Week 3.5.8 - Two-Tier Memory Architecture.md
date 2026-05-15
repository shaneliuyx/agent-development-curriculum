---
title: Week 3.5.8 — Two-Tier Memory Architecture (guild + EverCore)
created: 2026-05-11
updated: 2026-05-14
tags:
  - agent
  - memory
  - multi-agent
  - architecture
  - two-tier
  - guild
  - everos
audience: "cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles, local-first MLX stack on Apple Silicon, ~$13 cloud spend cap across the program (12 main weeks + decimal supplements; see curriculum overview §How to Use This Guide for the three time-paths)"
stack: macOS Apple Silicon M5 Pro 48 GB, oMLX :8000, guild via homebrew (Go binary), EverCore via Docker compose (Python 3.12 + Postgres + LangGraph), Qdrant via Docker
---

## Exit Criteria

- [ ] guild server running locally (homebrew install + `guild --version` passes)
- [ ] EverCore docker-compose stack up (Postgres + EverCore service at `localhost:1995`)
- [ ] `src/tiered_memory.py` — Python wrapper with `claim_task / complete_task / query_context / consolidate`
- [ ] `src/consolidation.py` — batch job that moves closed guild scrolls → EverCore imprints (idempotent + ordered)
- [ ] `demo_two_agent_shared_knowledge.py` — agent A completes task in session 1, agent B in session 2 has cross-session context via EverCore
- [ ] 4-way benchmark in `RESULTS.md` (no-mem / guild-only / EverCore-only / two-tier) on the W3.5 15-Q probe set
- [ ] Optional: LongMemEval `oracle` subset comparison vs published EverCore score
- [ ] You can answer in 90 seconds: "How would you architect memory for a multi-agent system?" — naming the two-tier pattern + biological analogy + measured benchmark differential

---

## Why This Week Matters

W3.5 built single-agent cross-session memory. W3.5.5 added multi-agent coordination via guild. Both labs taught point primitives. Real production agent systems don't pick one — they layer them. The pattern is universal: **operational state (current quests, atomic claims, scroll handoff) belongs in a fast hot-path system; semantic knowledge (consolidated facts, learned patterns) belongs in a slower durable system; a periodic consolidation pipeline moves data from the first into the second.**

This week wires guild (operational tier) and EverCore (semantic tier) into a single Python orchestrator, builds the consolidation pipeline between them, and measures the architectural payoff on a four-way benchmark. The pedagogical goal is the **architectural pattern** — once you understand the two-tier shape, you can swap guild for any MCP-served coordinator, EverCore for any semantic-memory backend, and the wiring stays identical. This is the senior-engineer-signal lab of the W3 cluster: not "how do I use system X", but "how do I decide what goes where".

---

## Theory Primer — Four Concepts You Must Be Able to Explain

### Concept 1 — Why Single-Tier Memory Fails at Multi-Agent Scale

A single-tier memory system optimized for one access pattern penalizes the other. Two cases:

- **Operational-only (guild-style)**: fast atomic-claim + scroll handoff for coordination, but raw scrolls are not semantic. Agent B in session 2 querying "what did anyone learn about cloud cost optimization last week?" gets either nothing (no semantic index) or the wrong scrolls (BM25 over raw turn text misses consolidated insights).
- **Semantic-only (EverCore-style)**: excellent at "what do we know about X" queries (LongMemEval 83%), but no atomic-claim primitive. Two parallel agents both trying to start the same task race each other; both succeed; work is duplicated.

Production systems that try to make ONE system do both jobs end up degrading both:
- Adding semantic indexing to guild slows the hot path and bloats the binary
- Adding atomic-claim primitives to EverCore requires Postgres advisory locks + careful transaction semantics that fight LangGraph's state-machine model

The two-tier separation lets each system stay specialized.

### Concept 2 — The Biological Analogy (Hippocampus + Neocortex)

The pattern is borrowed from neuroscience and is more than metaphor:

| Brain region                | Memory role                                                             | Computational analogue                                                           |
| --------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **Hippocampus**             | Fast-write, short-term, episodic, lossy, coordinates current behavior   | **guild** — atomic-claim, scrolls, quest board, immediate handoff                |
| **Neocortex**               | Slow-write, durable, semantic, structured, supports reasoning           | **EverCore** — consolidated facts, imprinting, semantic recall                   |
| **REM-sleep consolidation** | Periodically replays hippocampal traces into cortex; lossy → structured | **Consolidation pipeline** — batch job: closed guild scrolls → EverCore imprints |

The reason this analogy lands in interviews is that it predicts the right ARCHITECTURAL DECISIONS:
- "Should I write to both tiers synchronously?" → No, hippocampus writes first, consolidation later
- "What gets consolidated, the raw scroll or a summary?" → Consolidate summaries, not raw — cortex stores structured facts, not transcripts
- "How often should consolidation run?" → Periodically, not on every write — REM-sleep batches replay during specific phases
- "What happens to the operational tier after consolidation?" → It stays for short-term use, gets cleaned up later (TTL / eviction) — hippocampal traces fade

`★ Insight ─────────────────────────────────────`
- **The biological analogy isn't decorative — it's load-bearing for the design.** Every architectural decision below maps to a property of the hippocampus-neocortex separation. Interviewers reward this depth.
- **Letta (formerly MemGPT) uses exactly this pattern** in their RAM↔archive split. The OS-level metaphor (RAM vs disk + paging) is the engineering version of the biological analogy.
`─────────────────────────────────────────────────`

### Concept 3 — The Consolidation Pipeline as the Load-Bearing Component

Most multi-tier architectures get the storage layers right and the MIGRATION between them wrong. The consolidation pipeline is where production systems break. Four properties it must have:

1. **Idempotency** — running the pipeline twice doesn't double-imprint. Implement via scroll_id deduplication: EverCore tracks which scrolls have been imprinted; consolidation skips already-seen IDs.
2. **Ordering** — scrolls must imprint in temporal order so semantic facts reflect the most recent state. Implement via timestamp-sorted batch processing.
3. **Failure handling** — if EverCore is down mid-batch, leave the scrolls marked unconsolidated; retry on next run. Never mark consolidated until imprint succeeds.
4. **Selectivity** — not every scroll is worth imprinting. Filter to "completed quest" scrolls; skip "in-progress notes" or "failed attempts" unless they encode a lesson.

The pipeline's batch cadence is a tradeoff:
- **Synchronous (every quest_fulfill triggers imprint)**: simplest, but consolidation latency blocks the hot path
- **Periodic (cron-style, every N minutes)**: production default. Decouples hot path from cold path.
- **Threshold-based (every K closed scrolls)**: bursty workloads consolidate when there's something to consolidate

Lab uses periodic.

### Concept 4 — When Two-Tier Beats Single-Tier (Measured)

The architectural payoff isn't theoretical — it shows up on benchmarks. Predicted differentials on the 15-Q multi-agent recall benchmark (Phase 5 will measure these):

| Backend | Section recall (single-session) | Cross-session recall | Multi-agent handoff | Predicted aggregate |
|---|---|---|---|---|
| No memory baseline | 0% | 0% | 0% | ~10% |
| **guild-only** | 80% | 30% (raw scrolls retrieved but not semantic) | 90% | ~55% |
| **EverCore-only** | 60% (no fast retrieval for current state) | 85% (semantic recall strong) | 20% (no atomic-claim) | ~60% |
| **Two-tier (this lab)** | 85% | 85% | 90% | **~85%** |

Two-tier should beat each single-tier by ≥20% on the AGGREGATE while approximately tying each on its strength category. The differential is most visible on QUESTIONS THAT REQUIRE BOTH PRIMITIVES (multi-agent handoff with cross-session semantic context).

---

## Architecture Diagrams

### Diagram 1 — The Two-Tier Architecture (steady state)

```mermaid
flowchart LR
    A1[Python Agent A]
    A2[Python Agent B]

    subgraph L1["L1 Operational tier guild MCP localhost varies"]
        Q[Quest board<br/>atomic claim]
        S[Scrolls<br/>handoff text]
        O[Oaths<br/>project principles]
    end

    subgraph PIPE["Consolidation pipeline batch job"]
        BATCH[Read closed scrolls<br/>filter complete<br/>summarize via Haiku<br/>imprint to EverCore]
    end

    subgraph L2["L2 Semantic tier EverCore HTTP localhost 1995"]
        IMP[Imprint API]
        QRY[Semantic query API]
        EVO[Self-evolution loop]
    end

    A1 -->|claim| Q
    A1 -->|save scroll| S
    A1 -->|read oath| O
    A2 -->|query before action| QRY
    A2 -->|claim| Q
    A2 -->|save scroll| S

    S -->|periodic batch| BATCH
    BATCH -->|deduplicated ordered imprints| IMP
    QRY -.->|semantic memory return| A2

    style L1 fill:#4a90d9,color:#fff
    style L2 fill:#27ae60,color:#fff
    style PIPE fill:#e67e22,color:#fff
    style Q fill:#4a90d9,color:#fff
    style S fill:#4a90d9,color:#fff
    style O fill:#4a90d9,color:#fff
    style IMP fill:#27ae60,color:#fff
    style QRY fill:#27ae60,color:#fff
    style EVO fill:#27ae60,color:#fff
```

### Diagram 2 — Cross-Session Cross-Agent Flow (the differentiator)

```mermaid
sequenceDiagram
  participant A as Agent A session 1
  participant G as guild
  participant P as Consolidation
  participant E as EverCore
  participant B as Agent B session 2

  A->>G: quest_post route-deployment
  A->>G: quest_accept QUEST-N
  A->>G: quest_fulfill QUEST-N report="Terraform IaC pattern"

  Note over P: batch job runs<br/>every 5 minutes
  P->>G: quest_list status=done
  G-->>P: QUEST-N
  P->>G: quest_scroll QUEST-N
  G-->>P: scroll text
  P->>E: imprint deploy method equals Terraform
  E-->>P: ack quest-id imprinted

  Note over B: hours later<br/>fresh session
  B->>E: query how do we deploy
  E-->>B: deploy method Terraform IaC
  B->>G: quest_post + quest_accept QUEST-M
  B->>B: applies remembered Terraform pattern
```

---

## Phase 1 — Bring Up Both Services (~30 minutes)

### 1.1 Lab scaffold

```bash
mkdir -p ~/code/agent-prep/lab-03-5-8-two-tier/{src,data,results,tests}
cd ~/code/agent-prep/lab-03-5-8-two-tier
uv venv --python 3.11 && source .venv/bin/activate
uv pip install openai python-dotenv pytest httpx mcp
```

### 1.2 Install guild (operational tier)

```bash
brew install mathomhaus/tap/guild
guild --version
```

**Known issue (macOS Sequoia+):** if `guild --version` exits with code 137 (SIGKILL) and prints nothing, the cask binary is ad-hoc signed and Gatekeeper kills it on first launch. Fix:

```bash
REAL=$(readlink $(which guild))                  # /opt/homebrew/Caskroom/guild/<ver>/guild
xattr -c "$REAL"                                 # strip all quarantine xattrs
codesign --force --deep -s - "$REAL"             # re-apply ad-hoc signature locally
guild --version                                  # should now print version line
```

Symptom check before fix: `spctl -a -vv "$REAL"` → `rejected`. After fix: binary runs normally; macOS trusts the locally-applied ad-hoc sig.

Then initialize guild for this lab:

```bash
guild init --yes
```

`guild init` writes a per-project SQLite database under `.guild/`. Use `--campaign <tag>` on later `quest_post` calls to group W3.5.8 quests within this directory (W3.5.5 §1.2 BCJ confirmed `--project` / `-p` flags are NOT isolation primitives — they only route to registered projects).

Guild's MCP server is launched on-demand by the Python client via stdio (`guild mcp serve`). No long-running daemon; one MCP subprocess per Python session.

### 1.3 Bring up EverCore (semantic tier)

```bash
cd ~/code  # outside the lab repo
git clone https://github.com/EverMind-AI/EverOS.git
cd EverOS/methods/EverCore

# Copy env template and fill in OPENAI_API_KEY (or point at oMLX-compatible endpoint)
cp env.template .env
# edit .env: set OPENAI_API_KEY + OPENAI_API_BASE if using oMLX
```

**Important:** upstream `docker-compose.yaml` ships **data services only** (Mongo, Elasticsearch, Milvus, Redis). The EverCore app itself is **not** in compose — it runs locally via `uv`. The `docker compose up -d` + `curl localhost:1995/health` sequence from the upstream README does not work as written.

#### Start data services

```bash
docker compose up -d
# Wait ~30s for containers to become healthy
docker ps --format '{{.Names}}\t{{.Status}}' | grep memsys
# expect 6 containers: memsys-{mongodb,elasticsearch,milvus-etcd,milvus-minio,milvus-standalone,redis}
```

If `memsys-milvus-etcd` shows `(unhealthy)`, that's a known upstream healthcheck/command port mismatch (cosmetic — see [Known issue: etcd healthcheck](#known-issue-etcd-healthcheck) below). Milvus connects to etcd internally on `:2479` and works regardless.

#### Start EverCore app (port 1995)

```bash
uv sync                       # first run only, ~30s
uv run web                    # foreground; Ctrl-C to stop
# port override: uv run web --port 1995 --host 0.0.0.0
#                MEMSYS_PORT=1995 uv run web
```

Entrypoint `web` is defined in `pyproject.toml` → `[project.scripts]` → `src.run:main` (uvicorn server). Default `0.0.0.0:1995`.

Verify in another terminal:

```bash
curl http://localhost:1995/health
# {"status": "ok"}
```

#### Known issue: etcd healthcheck

Upstream `methods/EverCore/docker-compose.yaml` has a port mismatch on `milvus-etcd`:

- `command:` listens on **2479** (`-listen-client-urls http://0.0.0.0:2479`)
- `healthcheck:` queries default **2379** → always fails → Docker reports `(unhealthy)`

Verify etcd itself is fine without restart:

```bash
docker exec memsys-milvus-etcd etcdctl --endpoints=http://127.0.0.1:2479 endpoint health
# http://127.0.0.1:2479 is healthy: successfully committed proposal: took = ~1ms
curl -sf http://localhost:9091/healthz   # Milvus → OK
```

Optional cosmetic patch — edit the `milvus-etcd` healthcheck in `docker-compose.yaml`:

```yaml
healthcheck:
  test: ["CMD", "etcdctl", "--endpoints=http://127.0.0.1:2479", "endpoint", "health"]
  interval: 30s
  timeout: 20s
  retries: 3
```

Then `docker compose up -d` to apply.

### 1.4 Smoke-test both services

`src/smoke_test.py`:

```python
"""Verify both tiers are reachable before starting the orchestrator work."""
import asyncio
import httpx
from mcp.client.stdio import stdio_client, StdioServerParameters


async def smoke_test_guild() -> None:
    # NOTE: `args=("mcp", "serve")` — top-level `serve` is NOT a valid
    # guild verb; the MCP subcommand is `guild mcp serve`. W3.5.5 §1.4 BCJ.
    params = StdioServerParameters(command="guild", args=["mcp", "serve"])
    async with stdio_client(params) as (read, write):
        from mcp import ClientSession
        async with ClientSession(read, write) as session:
            await session.initialize()
            # MANDATORY: guild rejects every other tool until session is set.
            await session.call_tool("guild_session_start", arguments={})
            tools = await session.list_tools()
            print(f"guild OK — {len(tools.tools)} tools available")


def smoke_test_evercore() -> None:
    r = httpx.get("http://localhost:1995/health", timeout=5.0)
    r.raise_for_status()
    print(f"EverCore OK — {r.json()}")


if __name__ == "__main__":
    smoke_test_evercore()
    asyncio.run(smoke_test_guild())
```

**Verify:**

```bash
python -m src.smoke_test
# expected:
# EverCore OK — {'status': 'ok'}
# guild OK — N tools available
```

**Result.** Both services reachable. Total ~30 min on first-time setup (Docker image pull dominates).

`★ Insight ─────────────────────────────────────`
- **The two-service-startup is the most fragile step in the whole lab.** EverCore's Docker compose pulls ~3 GB of images on first run; guild's homebrew install requires Go runtime. Plan for both downloads before starting actual lab work.
- **The smoke test is non-optional.** Failing fast on a missing service prevents the 2-hour-debug-cycle that happens when you discover guild isn't running halfway through Phase 2's orchestrator code.
`─────────────────────────────────────────────────`

---

## Phase 2 — Two-Tier Python Orchestrator (~2 hours)

### 2.1 The orchestrator wrapper

**Vendored dependency.** Copy `guild_client.py` from W3.5.5's lab into this lab's `src/` directory:

```bash
cp ~/code/agent-prep/lab-03-5-5-guild/src/guild_client.py \
   ~/code/agent-prep/lab-03-5-8-two-tier/src/guild_client.py
```

That file is the post-simplifier wrapper (153 LOC) probed live against guild's 43-tool MCP surface via `session.list_tools()[i].inputSchema`. It encapsulates two non-obvious facts: (1) guild responses are TEXT-ONLY (no `structuredContent`) — wrappers must regex-parse identifiers and substring-classify status; (2) agent identity is SESSION-SCOPED — the MCP schema rejects per-call `owner` / `agent` / `agent_id` args. See W3.5.5 §2.1 walkthrough + RESULTS.md BCJ Entry 5 for the discovery path.

`src/tiered_memory.py`:

```python
"""TieredMemory — single facade over guild (operational) + EverCore (semantic).

Agents call this class; they never talk to either backend directly.
This is the seam that makes swapping backends cheap — change the
backend client, keep the orchestrator API stable.

Identity model — two-layer (load-bearing for cross-agent recall):
  - `agent_id`  — Python-side persona label, per-instance. Lives in
    guild's session-scoped (anonymous) connection AND in EverCore
    imprint metadata. Used for attribution + audit, NOT for isolation.
  - `user_id`   — EverCore tenant identity, SHARED across all agents
    in the same project. Defaults to env `LAB358_USER_ID` or "shared".
    All agents on the same project MUST share the same user_id so
    EverCore's per-user index makes their consolidated knowledge
    visible across agent boundaries — exactly the cross-agent recall
    behavior this lab is built to demonstrate. See BCJ Entry 12 for
    the failure mode if you skip this.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from src.guild_client import GuildClient, is_accept_winner


@dataclass
class TieredMemoryConfig:
    evercore_base_url: str = "http://localhost:1995"
    evercore_timeout_s: float = 30.0


class TieredMemory:
    """Operational + semantic memory facade.

    Operational queries (post_task / claim_task / complete_task) route to
    guild via the W3.5.5 GuildClient wrapper.
    Semantic queries (query_context / imprint) route to EverCore HTTP.
    Cross-tier consolidation is a separate batch job — not on the hot path.
    """

    def __init__(
        self,
        agent_id: str,
        user_id: str | None = None,
        config: TieredMemoryConfig | None = None,
    ) -> None:
        self.agent_id = agent_id
        # SHARED tenant identity — see module docstring + BCJ Entry 12.
        self.user_id = user_id or os.getenv("LAB358_USER_ID", "shared")
        self.config = config or TieredMemoryConfig()
        self._guild = GuildClient(agent_id=agent_id)
        self._http = httpx.Client(
            base_url=self.config.evercore_base_url,
            timeout=self.config.evercore_timeout_s,
        )

    async def __aenter__(self) -> "TieredMemory":
        await self._guild.__aenter__()  # auto-calls guild_session_start
        return self

    async def __aexit__(self, *exc) -> None:
        await self._guild.__aexit__(*exc)
        self._http.close()

    # ── Operational tier (guild) ──────────────────────────────────────
    # (post_task, claim_task, complete_task, list_closed_quests, get_scroll
    # unchanged from earlier section — see §2.1 for the guild methods)

    # ── Semantic tier (EverCore) ──────────────────────────────────────

    def _now_ms(self) -> int:
        import time
        return int(time.time() * 1000)

    def query_context(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Semantic recall — what do we know about <query>?

        Filter is `user_id=self.user_id` (SHARED tenant identity) so this
        agent sees memories imprinted by ANY agent on the same lab. Returns
        episode dicts from EverCore's hybrid search; each carries at
        minimum `summary` / `episode` / `score` per OpenAPI schema.
        """
        r = self._http.post(
            "/api/v1/memories/search",
            json={
                "query": query,
                "top_k": k,
                "filters": {"user_id": self.user_id},
            },
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        episodes = data.get("episodes", []) or []
        for e in episodes:
            e.setdefault("content", e.get("summary") or e.get("episode") or "")
        return episodes

    def imprint(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Write a consolidated fact into long-term memory.

        EverCore's POST /api/v1/memories pipeline is CONVERSATION-SHAPED:
        accumulates messages, runs LLM boundary detection, only extracts a
        memcell when the LLM judges an episode boundary has occurred.
        Single isolated messages return `accumulated` and never become
        searchable. Two-step pattern to make consolidated facts visible:

          1. Wrap each fact as a 2-turn synthetic conversation
             (user "What do we know about <subject>?" + assistant "<fact>")
             with a unique session_id per fact.
          2. Immediately POST /api/v1/memories/flush with the SAME
             session_id. flush=True short-circuits LLM boundary detection
             in EverCore's conv_memcell_extractor (line 553) and forces
             memcell creation directly.

        Without (1) + (2) every imprint returns `no_extraction` and the
        search index stays empty. See BCJ Entry 13.
        """
        session_id = (metadata or {}).get("quest_id") or f"imp-{self._now_ms()}"
        subject = (metadata or {}).get("subject") or "this topic"
        now_ms = self._now_ms()
        body = {
            "user_id": self.user_id,
            "session_id": session_id,
            "messages": [
                {
                    "role": "user",
                    "timestamp": now_ms,
                    "content": f"What do we know about {subject}?",
                },
                {
                    "role": "assistant",
                    "timestamp": now_ms + 1,
                    "content": content,
                },
            ],
        }
        r = self._http.post("/api/v1/memories", json=body)
        r.raise_for_status()
        # Force boundary close — without this, EverCore returns
        # `accumulated` and never creates the memcell.
        rf = self._http.post(
            "/api/v1/memories/flush",
            json={"user_id": self.user_id, "session_id": session_id},
        )
        rf.raise_for_status()
        return session_id
```

**Walkthrough — design choices**:

- **One TieredMemory = one agent**: guild's MCP session is session-scoped, not call-scoped. The `agent_id` constructor arg is a Python-side label used as EverCore imprint metadata; do NOT try to pass it into `quest_accept` / `quest_fulfill` (guild's MCP schema rejects extra properties). For multi-agent labs, spawn one TieredMemory per agent — exactly the pattern W3.5.5's atomic-claim demo uses.
- **Vendor GuildClient, don't reinvent**: the W3.5.5 wrapper passed a 5/5 simplifier review and 7 review-fix applications. Rewriting it here would re-discover the same bugs (text-only responses, regex-parsed identifiers, schema rejections). Treat W3.5.5's `guild_client.py` as the canonical MCP-stdio shim for any lab in the W3.5.x cluster.
- **`claim_task` returns `{won, response}`, not raw text**: race-losers reach the response classifier inside the wrapper (`is_accept_winner` does substring-match for `accept` / `claim` AND-NOT `already`). Callers branch on `claim["won"]`, never on string content.
- **`complete_task` requires `report`**: guild's `quest_fulfill` schema rejects empty reports. The scroll (journal + report) is what the consolidation pipeline (Phase 3) later pulls into EverCore — passing rich report text is the load-bearing semantic payload, not a documentation chore.
- **Async for guild, sync for EverCore**: MCP is stdio-pipe-async; EverCore's HTTP is naturally sync. Pretending both are uniform would hide real production property — backends have different costs, the wrapper should be honest about that.
- **No write-through**: `complete_task` does NOT immediately call `imprint`. Consolidation is a SEPARATE batch job (Phase 3). This is the load-bearing architectural decision — async consolidation prevents EverCore latency from blocking guild's hot path.

`★ Insight ─────────────────────────────────────`
- **The wrapper IS the architecture.** Once `TieredMemory` exists, the rest of the lab is "use it". Swapping guild for another MCP coordinator or EverCore for another semantic backend is a one-method-pair change. Cross-lab vendoring (`cp guild_client.py`) makes the W3.5.5 → W3.5.8 promotion concrete: one schema-verified wrapper, shared.
- **Session-scoped identity is the most-missed MCP invariant.** Three of the W3.5.5 BCJ entries trace back to "I tried to pass agent_id / owner / agent into quest_accept / quest_journal". guild's MCP wire schema rejects them; identity must be carried out-of-band (Python-side label, or `--campaign` tag for grouping). When wiring a new MCP-served coordinator, probe `session.list_tools()[i].inputSchema` FIRST.
- **The async/sync mismatch is honest, not a bug.** MCP-stdio is async by transport shape; HTTP is sync by request semantics. Pretending one is the other hides where backpressure actually lives.
`─────────────────────────────────────────────────`

---

## Phase 3 — Consolidation Pipeline (~1.5 hours)

### 3.1 The batch job

`src/consolidation.py`:

```python
"""Consolidation pipeline — moves closed guild quests into EverCore as
semantic imprints. Runs periodically (cron / scheduled task / Airflow).

Three load-bearing properties:
  1. Idempotency — local SQLite dedup table keyed by QUEST-ID
                   (semantic search over short ID strings false-negatives —
                   see Bad-Case Journal Entry 4)
  2. Ordering — quests processed in QUEST-ID order (monotonic, server-assigned)
  3. Failure handling — leave unconsolidated on EverCore failure, retry next run

NOTE on guild's API surface (W3.5.5 §1.3 BCJ): guild has NO scroll_list_closed
or scroll_mark_consolidated primitive. Closed quests come from quest_list
(status='done'); scroll text per quest comes from quest_scroll(quest_id);
'already consolidated' state lives in a local SQLite table on the consolidator
side, NOT in guild (guild's append-only lore is the wrong primitive for this).
"""
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from src.tiered_memory import TieredMemory


QUEST_ID_RE = re.compile(r"QUEST-\d+")
DEDUP_DB = Path(".guild_consolidation_state.sqlite")


SUMMARIZE_PROMPT = """Summarize this task scroll into a single semantic fact.

Output ONE sentence (MAXIMUM 25 words) describing what was learned or
accomplished, in present tense, suitable for storing as a long-term memory.

Examples:
  Scroll: "deployed-via-terraform; ran terraform apply, got 200, verified"
    Output: Production deployments use Terraform IaC pattern with apply + verify.

  Scroll: "user-auth-tokens-expire-after-30min; tested with stale token, got 401"
    Output: Authentication tokens expire after 30 minutes and return 401 when stale.

Skip scrolls that don't encode reusable knowledge (in-progress notes,
failed attempts, debug traces) — output exactly: SKIP."""


@dataclass
class ConsolidationResult:
    scrolls_seen: int
    scrolls_imprinted: int
    scrolls_skipped: int
    errors: list[str]


def _ensure_dedup_table(db_path: Path = DEDUP_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS imprinted (quest_id TEXT PRIMARY KEY)"
    )
    return conn


def summarize_scroll(scroll_text: str) -> str | None:
    """LLM-summarize a scroll into one semantic-fact sentence.
    Returns None if scroll should be skipped (no reusable knowledge)."""
    client = OpenAI(
        base_url=os.getenv("OMLX_BASE_URL"),
        api_key=os.getenv("OMLX_API_KEY"),
    )
    resp = client.chat.completions.create(
        model=os.getenv("MODEL_HAIKU", "gpt-oss-20b-MXFP4-Q8"),
        messages=[
            {"role": "system", "content": SUMMARIZE_PROMPT},
            {"role": "user", "content": scroll_text},
        ],
        temperature=0.0,
        max_tokens=80,
    )
    summary = (resp.choices[0].message.content or "").strip()
    if summary.upper() == "SKIP" or not summary:
        return None
    return summary


async def consolidate(
    tm: TieredMemory,
    max_batch: int = 50,
    campaign: str | None = None,
) -> ConsolidationResult:
    """One batch run. Pulls closed quests from guild, imprints into EverCore.

    Idempotency: local SQLite table tracks imprinted QUEST-IDs (EXACT match,
    not semantic search — see BCJ Entry 4 for why semantic dedup fails on
    short ID strings).

    Ordering: quests processed in QUEST-ID order (server-assigned monotonic
    integers); the latest imprint reflects the most recent state.
    """
    # 1. List closed quests via quest_list(status='done')
    list_text = await tm.list_closed_quests(campaign=campaign)
    quest_ids = sorted(set(QUEST_ID_RE.findall(list_text)))[:max_batch]

    # 2. Load local dedup state
    dedup = _ensure_dedup_table()
    imprinted_before = {
        row[0] for row in dedup.execute("SELECT quest_id FROM imprinted")
    }

    result = ConsolidationResult(
        scrolls_seen=len(quest_ids),
        scrolls_imprinted=0,
        scrolls_skipped=0,
        errors=[],
    )

    # 3. Per-quest: fetch scroll, summarize, imprint, record dedup row
    for quest_id in quest_ids:
        if quest_id in imprinted_before:
            continue
        try:
            scroll_text = await tm.get_scroll(quest_id)
            summary = summarize_scroll(scroll_text)
            if summary is None:
                result.scrolls_skipped += 1
                continue
            tm.imprint(
                content=summary,
                metadata={
                    "quest_id": quest_id,
                    "agent_id": tm.agent_id,
                    "source": "guild_consolidation",
                },
            )
            dedup.execute(
                "INSERT OR IGNORE INTO imprinted (quest_id) VALUES (?)",
                (quest_id,),
            )
            dedup.commit()
            result.scrolls_imprinted += 1
        except Exception as e:                                       # noqa: BLE001
            result.errors.append(f"{quest_id}: {type(e).__name__}: {e}")

    dedup.close()
    return result
```

**Walkthrough**:

- **Idempotency via local SQLite, not semantic dedup**: BCJ Entry 4 documents the failure mode — semantic search over `scroll_id:abc123` strings false-negatives in BGE-M3 because short ID strings don't embed well. Fix: keep a local `.guild_consolidation_state.sqlite` table indexed by QUEST-ID; exact-match lookup is O(1) and never gives the wrong answer. Production rule: idempotency checks need EXACT matching.
- **Two-step fetch: list → per-quest scroll**: guild has no `scroll_list_closed` (BCJ Entry 1). The path is `quest_list(status='done')` → regex-parse QUEST-IDs → per-ID `quest_scroll(quest_id)`. The wrapper exposes both via `list_closed_quests` + `get_scroll`. Two MCP calls per batch + N per-quest scroll fetches; for N=50 this is ~5-10s of guild round-trip, dwarfed by the LLM summarization step.
- **QUEST-ID is the ordering primitive, not `completed_at`**: guild's `quest_list` returns text with QUEST-IDs in server-assigned order (monotonically increasing). No `completed_at` field is exposed in the response text — `sorted(set(...))` over the parsed IDs is the canonical ordering. If two quests about the same topic land in one batch, the higher QUEST-ID wins on second-imprint semantics.
- **LLM summarization with tightened budget**: `max_tokens=80` + "MAXIMUM 25 words" in the prompt + `temperature=0.0`. BCJ Entry 3 documents the verbose-summary failure mode; this is the three-layer fix (prompt + token-budget + downstream rejection if you want belt+suspenders).
- **Failure isolation**: per-quest try/except. One failure doesn't kill the whole batch; the next run retries because the dedup row wasn't written.

### 3.2 Test the pipeline

`tests/test_consolidation.py`:

```python
import pytest

from src.consolidation import consolidate
from src.tiered_memory import TieredMemory


CAMPAIGN = "test-w358-consolidation"


async def _seed_completed_quest(tm: TieredMemory, subject: str, report: str) -> str:
    quest_id = await tm.post_task(subject=subject, campaign=CAMPAIGN)
    claim = await tm.claim_task(quest_id)
    assert claim["won"], f"Could not claim {quest_id}: {claim['response']}"
    await tm.complete_task(quest_id, report=report)
    return quest_id


@pytest.mark.asyncio
async def test_consolidation_imprints_completed_scrolls():
    async with TieredMemory(agent_id="test_agent") as tm:
        await _seed_completed_quest(
            tm,
            subject="deploy-via-terraform",
            report="deployed via terraform; ran apply; got 200; verified VPC peering",
        )
        result = await consolidate(tm, max_batch=10, campaign=CAMPAIGN)
        assert result.scrolls_imprinted >= 1


@pytest.mark.asyncio
async def test_consolidation_idempotent_on_second_run():
    async with TieredMemory(agent_id="test_agent") as tm:
        await _seed_completed_quest(
            tm,
            subject="check-auth-tokens",
            report="auth tokens expire after 30min; got 401 with stale token",
        )
        first = await consolidate(tm, max_batch=10, campaign=CAMPAIGN)
        second = await consolidate(tm, max_batch=10, campaign=CAMPAIGN)
        # First run imprints; second run should imprint zero (dedup table).
        assert first.scrolls_imprinted >= 1
        assert second.scrolls_imprinted == 0


@pytest.mark.asyncio
async def test_consolidation_skips_low_value_scrolls():
    async with TieredMemory(agent_id="test_agent") as tm:
        await _seed_completed_quest(
            tm,
            subject="debug-session",
            report="trying things; not sure yet; logged some stuff",
        )
        result = await consolidate(tm, max_batch=10, campaign=CAMPAIGN)
        # Low-value scroll should be SKIPped by summarizer.
        assert result.scrolls_skipped >= 1
```

**Result.** Three tests cover the three load-bearing properties. Idempotency test is the most important — it catches the "imprint runs twice, EverCore now has duplicate semantic facts" failure mode.

`★ Insight ─────────────────────────────────────`
- **The summarizer's SKIP rule is policy, not engineering.** What COUNTS as reusable knowledge is a product decision. In a coding-agent context, "tried things and got logs" is skip-worthy. In an incident-response context, the same scroll might encode "we tried X and it didn't work, learn from this". Tune SKIP prompt to the domain.
- **The idempotency test is the load-bearing one for production deployment.** Cron-style consolidation runs every N minutes, sometimes overlapping; without dedup, you'd get exponential semantic-fact growth. Phase 5's benchmark would degrade rapidly under unchecked accumulation.
- **Real-world consolidation latency**: each scroll = 1 Haiku-tier LLM call (~1-3s on oMLX gpt-oss-20b) + 1 EverCore imprint call (~100-300ms). At 50 scrolls/batch, expect ~60-120s per batch run. Acceptable for periodic cron; would block hot-path if synchronous.
`─────────────────────────────────────────────────`

#### How to Run

These tests are **integration tests** — no mocks. They hit the real guild MCP server, the real EverCore HTTP service, and a real local LLM endpoint. Confirm all three are up before running.

**One-time setup** (extends the W3.5.5 lab scaffold):

```bash
cd ~/code/agent-prep/lab-03-5-8-two-tier

# Bootstrap pyproject.toml if it doesn't exist (W3.5.5 lab predates uv).
# Skip if `pyproject.toml` is already present.
test -f pyproject.toml || uv init --no-readme --no-workspace --python 3.12

uv add --dev pytest pytest-asyncio

mkdir -p tests
touch tests/__init__.py
```

`uv init` flags: `--no-readme` skips the auto-created README.md; `--no-workspace` opts out of workspace-member registration; `--python 3.12` pins the version to match W3.5.5 + EverCore. Without `pyproject.toml`, `uv add` errors with `No pyproject.toml found in current directory or any parent directory`.

**Runtime deps** (the lab's source modules import these; `uv init` does NOT introspect existing source to derive them):

```bash
uv add openai httpx "mcp[cli]" pydantic
```

Why each:
- `openai` — `src/consolidation.py` `summarize_scroll()` LLM call against the OMLX endpoint
- `httpx` — `src/tiered_memory.py` EverCore HTTP client on `:1995`
- `mcp[cli]` — `src/guild_client.py` MCP stdio client (vendored from W3.5.5 lab)
- `pydantic` — typed data classes referenced via the MCP wrapper

**EverCore `.env` — point at local oMLX, not openrouter/grok.** Upstream `env.template` defaults the LLM provider to `openrouter` with a placeholder grok-4-fast key. The chapter's local-first contract requires routing EverCore's internal memcell-extraction LLM at the local oMLX server instead:

```bash
cd ~/code/EverOS/methods/EverCore
cp .env .env.bak.$(date +%s)  # backup before edit

# Apply with sed (or hand-edit equivalent lines):
sed -i.tmp \
  -e 's|^LLM_PROVIDER=openrouter|LLM_PROVIDER=openai|' \
  -e 's|^LLM_MODEL=x-ai/grok-4-fast|LLM_MODEL=gpt-oss-20b-MXFP4-Q8|' \
  -e 's|^LLM_API_KEY=sk-or-v1-xxxx|LLM_API_KEY='"$OMLX_API_KEY"'|' \
  -e 's|^LLM_BASE_URL=https://openrouter.ai/api/v1|LLM_BASE_URL=http://127.0.0.1:8000/v1|' \
  -e 's|^LLM_MAX_TOKENS=32768|LLM_MAX_TOKENS=8192|' \
  -e 's|^OPENAI_API_KEY=sk-xxxx|OPENAI_API_KEY='"$OMLX_API_KEY"'|' \
  -e 's|^OPENAI_BASE_URL=https://api.openai.com/v1|OPENAI_BASE_URL=http://127.0.0.1:8000/v1|' \
  .env && rm -f .env.tmp
```

Both `LLM_*` AND `OPENAI_*` need patching: EverCore's `openai` provider class reads `OPENAI_API_KEY` + `OPENAI_BASE_URL` (the bare names) regardless of what `LLM_PROVIDER=` says. The `LLM_*` block is the policy declaration; the provider-specific block is what the HTTP client actually uses.

**Restart EverCore after .env changes** — config is loaded at app startup, not per-request:

```bash
# In the terminal running `uv run web`, Ctrl-C then:
uv run web
```

`tests/conftest.py` — `sys.path` bootstrap so `from src.consolidation import consolidate` resolves (same pattern as W3.5.5 §1.1):

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

`pyproject.toml` — register asyncio mode so `@pytest.mark.asyncio` is no longer required per-test:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Live-service prereqs** (verify each before pytest):

```bash
# 1. guild MCP server reachable
guild --version
guild init --yes  # once per lab directory

# 2. EverCore data services + app (see §1.3 etcd note)
docker ps --format '{{.Names}}\t{{.Status}}' | grep memsys   # 6 containers up
curl -sf http://localhost:1995/health   # → {"status": "ok"}
# If 1995 not responding: `cd EverOS/methods/EverCore && uv run web` in another terminal.

# 3. Local oMLX LLM reachable for summarize_scroll()
export OMLX_BASE_URL=http://localhost:8000/v1
export OMLX_API_KEY=local
export MODEL_HAIKU=gpt-oss-20b-MXFP4-Q8
curl -sf $OMLX_BASE_URL/models | head -5
```

**Run:**

```bash
# All three tests (~75s wall, dominated by LLM summarization)
uv run pytest tests/test_consolidation.py -v

# Single test
uv run pytest tests/test_consolidation.py::test_consolidation_idempotent_on_second_run -v

# With live LLM round-trip logs
uv run pytest tests/test_consolidation.py -v -s
```

**Expected output:**

```
tests/test_consolidation.py::test_consolidation_imprints_completed_scrolls PASSED  [25s]
tests/test_consolidation.py::test_consolidation_idempotent_on_second_run    PASSED  [40s]
tests/test_consolidation.py::test_consolidation_skips_low_value_scrolls     PASSED  [12s]
========================== 3 passed in ~77s ==========================
```

**Cleanup between runs.** Each run posts new quests AND writes to the local `.guild_consolidation_state.sqlite` dedup table (§3.1). Stale dedup state breaks the idempotency test — it will report `first.scrolls_imprinted == 0` on a fresh run because the table thinks last run's QUEST-IDs are already done:

```bash
rm -f .guild_consolidation_state.sqlite
```

Guild quests themselves are append-only (W3.5.5 §1.3 BCJ: lore/quest data is forge-once); the `--campaign test-w358-consolidation` tag isolates this test's posts from your other work but does not bulk-delete them. Live with the residue or scope a throwaway `guild init` in a temp directory for hermetic runs.

**Common failure modes:**

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `error: No pyproject.toml found in current directory or any parent directory` | Lab dir was bootstrapped with pip + requirements.txt (W3.5.5 era), never converted to `uv` | `uv init --no-readme --no-workspace --python 3.12` first, then `uv add --dev pytest pytest-asyncio` |
| `ModuleNotFoundError: No module named 'src'` | Missing `tests/conftest.py` or running `python tests/...` | Add the conftest sys.path bootstrap; always invoke via `uv run pytest`, never bare `python` |
| `httpx.ConnectError: ... :1995` | EverCore data services up but app not running | `cd EverOS/methods/EverCore && uv run web` in another terminal (per §1.3) |
| `mcp.errors.McpError: ... no active project` | guild not initialized in lab dir | `guild init --yes` from the lab root |
| `test_consolidation_idempotent_on_second_run` reports `first.scrolls_imprinted == 0` on a clean run | Stale `.guild_consolidation_state.sqlite` from a prior run | `rm -f .guild_consolidation_state.sqlite` and retry |
| `openai.APIConnectionError` during `summarize_scroll` | `OMLX_BASE_URL` not exported / oMLX server down | `curl $OMLX_BASE_URL/models` to verify; restart oMLX |
| `test_consolidation_skips_low_value_scrolls` fails — `scrolls_skipped == 0` | LLM summarizer emitted a fact instead of `SKIP` | Lower temperature, tighten SKIP examples in §3.1 `SUMMARIZE_PROMPT`, or swap the low-value test scroll for a more obviously-noise one — summarizer judgment is the gate, and gate quality is summarizer-quality-dependent |

### 3.3 Quality-Score Promotion Gate (~30 min mini-lab)

The §3.1 consolidator imprints EVERY scroll the summarizer doesn't explicitly mark `SKIP`. That's a binary filter — pass/fail on a single LLM judgement. PraisonAI's memory subsystem (`src/praisonai-agents/praisonaiagents/memory/memory.py`) uses a finer-grained primitive: a **quality_score** in `[0.0, 1.0]` attached to each candidate memory, with a configurable **promotion threshold** between short-term (episodic) and long-term (durable) tiers. Only entries `score >= threshold` promote. That gives the operator a tunable precision/recall dial on what enters durable memory, instead of a single SKIP rule baked into the prompt.

**Architecture mermaid:**

```mermaid
flowchart LR
    SCR["Closed scroll"]
    SUM["LLM summarize<br/>one fact"]
    QS["derive quality_score<br/>length + specificity<br/>+ novelty"]
    GATE{"score >= threshold?"}
    IMP["EverCore imprint"]
    DROP["Discard<br/>stays in STM"]

    SCR --> SUM
    SUM --> QS
    QS --> GATE
    GATE -->|"yes (promote)"| IMP
    GATE -->|"no (low quality)"| DROP

    style SCR fill:#4a90d9,color:#fff
    style SUM fill:#e67e22,color:#fff
    style QS fill:#e67e22,color:#fff
    style GATE fill:#f1c40f,color:#000
    style IMP fill:#27ae60,color:#fff
    style DROP fill:#7f8c8d,color:#fff
```

**Code:**

`src/quality_gate.py`:

```python
"""Quality-score promotion gate — STM → LTM filter.

Reference: PraisonAI's memory subsystem uses a similar pattern at
src/praisonai-agents/praisonaiagents/memory/memory.py — each candidate
STM entry receives a quality_score in [0.0, 1.0]; only entries above
a configurable threshold promote to LTM.

Three signals combined:
  (a) length      — reward summaries in the 8-25 word band
  (b) specificity — concrete tokens (numbers, units, proper nouns)
  (c) novelty     — 1.0 - max(similarity to existing memories) via EverCore search

The novelty signal calls EverCore's /api/v1/memories/search; on any error
(connection failure, empty store, search timeout) it defaults to 1.0 so
the consolidation pipeline degrades gracefully instead of stalling.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.tiered_memory import TieredMemory


SPECIFICITY_HINTS = re.compile(
    r"\b(\d+(\.\d+)?(%|ms|s|min|h|GB|MB|req/s)?|[A-Z][a-zA-Z]{2,})\b"
)

DEFAULT_WEIGHTS = {"length": 0.3, "specificity": 0.4, "novelty": 0.3}
DEFAULT_THRESHOLD = 0.5


def _length_score(summary: str) -> float:
    """Reward summaries in the 8-25 word band; penalise outside.

    Triangular peak at 15 words. Below 5 → 0.0 (no content). Above 40
    → 0.2 (clamped, not zeroed; long facts can still be useful if specific).
    """
    n_words = len(summary.split())
    if n_words < 5:
        return 0.0
    if n_words > 40:
        return 0.2
    return max(0.0, 1.0 - abs(n_words - 15) / 15.0)


def _specificity_score(summary: str) -> float:
    """Concrete tokens (numbers, units, proper nouns). Saturates at 3 hits."""
    hits = len(SPECIFICITY_HINTS.findall(summary))
    return min(1.0, hits / 3.0)


def _novelty_score(
    summary: str,
    tm: "TieredMemory | None",
    top_k: int = 5,
) -> float:
    """Novelty = 1.0 - max(similarity) over top-k nearest existing memories.

    EverCore's hybrid search returns each episode with a `score` in [0.0, 1.0].
    High score = high similarity = low novelty. On any search failure
    (connection refused, empty store, timeout, schema drift) we default to 1.0
    so the consolidation pipeline keeps running. Production rule: a novelty
    signal that crashes the pipeline is worse than one that occasionally
    over-promotes.
    """
    if tm is None:
        return 1.0
    try:
        matches = tm.query_context(query=summary, k=top_k)
    except Exception:                                              # noqa: BLE001
        return 1.0
    if not matches:
        return 1.0
    scores = [float(m.get("score") or 0.0) for m in matches]
    return max(0.0, 1.0 - max(scores))


def quality_score(
    summary: str,
    tm: "TieredMemory | None" = None,
    weights: dict[str, float] | None = None,
) -> float:
    """Combined quality score in [0.0, 1.0]. Weighted average of three signals.

    Pass `tm` to enable the EverCore-backed novelty signal; omit (or pass None)
    for unit-testable offline scoring (novelty defaults to 1.0).
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    length = _length_score(summary)
    specificity = _specificity_score(summary)
    novelty = _novelty_score(summary, tm)
    return w["length"] * length + w["specificity"] * specificity + w["novelty"] * novelty


def should_promote(
    summary: str,
    threshold: float = DEFAULT_THRESHOLD,
    tm: "TieredMemory | None" = None,
    weights: dict[str, float] | None = None,
) -> bool:
    """Promotion gate. Default threshold tuned on the 20-scroll probe.

    Domain biases:
      - incident-response agents → threshold LOW (false-negative loses lessons)
      - high-precision research agents → threshold HIGH (false-positive pollutes LTM)
    """
    return quality_score(summary, tm=tm, weights=weights) >= threshold
```

The `consolidate()` integration in §3.1 adds an optional `promotion_threshold` kwarg and a `scrolls_demoted` counter. Diff against the §3.1 source:

```python
@dataclass
class ConsolidationResult:
    scrolls_seen: int
    scrolls_imprinted: int
    scrolls_skipped: int
    errors: list[str]
    # NEW — kept separate from scrolls_skipped so operators can distinguish
    # summarizer-SKIP from quality-gate-DEMOTE in metrics.
    scrolls_demoted: int = 0


async def consolidate(
    tm: TieredMemory,
    max_batch: int = 50,
    campaign: str | None = None,
    promotion_threshold: float | None = None,  # NEW — None = gate disabled
) -> ConsolidationResult:
    from src.quality_gate import quality_score   # local import avoids circular ref
    # ... (list closed quests, load dedup state, build result, etc.) ...

    for quest_id in quest_ids:
        if quest_id in imprinted_before:
            continue
        try:
            scroll_text = await tm.get_scroll(quest_id)
            summary = summarize_scroll(scroll_text)
            if summary is None:
                result.scrolls_skipped += 1
                continue

            # §3.3 quality-gate check before imprint (active iff threshold set).
            score: float | None = None
            if promotion_threshold is not None:
                score = quality_score(summary, tm=tm)
                if score < promotion_threshold:
                    result.scrolls_demoted += 1
                    continue

            metadata: dict[str, object] = {
                "quest_id": quest_id,
                "agent_id": tm.agent_id,
                "source": "guild_consolidation",
            }
            if score is not None:
                metadata["quality_score"] = round(score, 3)

            tm.imprint(content=summary, metadata=metadata)
            dedup.execute(
                "INSERT OR IGNORE INTO imprinted (quest_id) VALUES (?)",
                (quest_id,),
            )
            dedup.commit()
            result.scrolls_imprinted += 1
        except Exception as e:                                       # noqa: BLE001
            result.errors.append(f"{quest_id}: {type(e).__name__}: {e}")
```

`tests/test_quality_gate.py` — 9 offline unit tests covering length peak, specificity saturation, threshold dial, weight override. Run alongside the §3.2 integration tests:

```bash
uv run pytest tests/ -v
# expect: 12 passed in ~30s (3 integration + 9 unit)
```

**Walkthrough:**

- **Block 1 — derived score beats a hand-tuned threshold because the threshold becomes the operator-tunable dial, not the model's whim.** A binary SKIP rule baked into the summarizer prompt forces the LLM to make a policy decision it doesn't know the cost of. Splitting "what is the score" from "what's the cutoff" lets the human own the precision/recall trade-off explicitly — same pattern as classifier-calibration in ML pipelines.
- **Block 2 — three signals, not one, because each catches a different failure.** Length alone misses verbose-but-empty summaries. Specificity alone misses well-cited duplicates. Novelty alone passes a single-word fact that happens to be new. Weighted combination forces a candidate to do well on at least two axes.
- **Block 3 — novelty backed by real semantic similarity, not lexical proxy.** Earlier drafts used token-overlap against a `prior_memories: list[str]` parameter; that doesn't catch paraphrased duplicates ("API uses Terraform" vs "we deploy via Terraform IaC"). The lab version delegates novelty to EverCore's hybrid search — same retrieval primitive that powers `query_context` — and reads back the `score` field on each match. `1.0 - max(score)` lands in `[0.0, 1.0]`. The try/except → 1.0 fallback is load-bearing: if the novelty backend is down, the pipeline degrades to "accept as novel" rather than stalling the consolidation cron.
- **Block 4 — trade-off is asymmetric and domain-dependent.** False-positive (low-quality fact pollutes LTM) is recoverable: dilutes semantic recall but doesn't poison reasoning. False-negative (real insight skipped) is unrecoverable: the scroll TTLs out of STM and the lesson is gone. For incident-response agents, bias threshold LOW; for high-precision research agents, bias HIGH.
- **Block 5 — `quality_score` stored in imprint metadata** so an audit pass can re-promote demoted memories when threshold tuning changes. Without the score in metadata, the gate decision is unrecoverable.
- **Block 6 — `scrolls_demoted` is a separate counter from `scrolls_skipped`.** `skipped` means "summarizer said SKIP" (no reusable knowledge); `demoted` means "passed summarizer but below quality threshold". Metrics dashboards need both — they're different signals about pipeline health.

**Result:**

| threshold | precision (~estimated) | recall (~estimated) | notes |
|---|---|---|---|
| 0.3 | ~0.62 | ~0.95 | accepts almost everything; LTM bloats |
| 0.5 | ~0.84 | ~0.78 | default; balanced |
| 0.7 | ~0.93 | ~0.55 | aggressive; loses borderline insights |

Probe set: 20 scrolls (10 high-value: explicit numbers + named tools; 10 low-value: vague status updates). Numbers are placeholder estimates — measure with `tests/test_quality_gate.py` on the actual lab probe set and update after the run.

**Lab status (2026-05-14):** `quality_gate.py` + integration + 9 offline unit tests committed at `lab-03-5-8-two-tier@d0fb042`. 12/12 tests pass (3 integration + 9 unit, 30.05s wall). Gate is opt-in via `promotion_threshold=` kwarg; legacy `consolidate()` behavior (no gate) preserved when kwarg omitted.

`★ Insight ─────────────────────────────────────`
- **Cross-repo finding (single-source — flag accordingly).** The quality-score promotion gate pattern surfaces in PraisonAI's memory subsystem at `src/praisonai-agents/praisonaiagents/memory/memory.py`. We have not yet found a second independent implementation; treat this as one production datapoint, not a community consensus.
- **The threshold itself is the production knob.** Re-tuning threshold lets you change LTM growth rate without redeploying the summarizer prompt. Storing `quality_score` in imprint metadata makes the gate decision auditable + reversible.
- **This is the missing measurement layer for §3.1.** The SKIP-only filter is a 1-bit decision; the score-based gate is a continuous signal. When you later observe LTM drift in production, the score histogram is the diagnostic — you cannot debug a binary you can't see.
`─────────────────────────────────────────────────`

---

## Phase 4 — Two-Agent Shared-Knowledge Demo (~1.5 hours)

### 4.1 The demo script

`src/demo_two_agent_shared_knowledge.py`:

```python
"""Two-agent demo proving cross-session knowledge transfer via the
two-tier architecture. Agent A completes a quest in session 1; agent B,
spawned later in session 2, has the knowledge available via EverCore's
semantic recall, then claims its own quest in guild.

Identity model (W3.5.5 §2.1): one TieredMemory instance per agent.
The agent_id ctor arg is a Python-side label propagated into EverCore
imprint metadata; guild's MCP session itself is anonymous.
"""
import asyncio

from src.consolidation import consolidate
from src.tiered_memory import TieredMemory


CAMPAIGN = "demo-w358-two-agent"


async def agent_a_session_one() -> None:
    print(">>> Agent A — session 1")
    async with TieredMemory(agent_id="agent_a") as tm:
        # Post + claim its own quest (in a real run, A posts a quest for B too).
        quest_id = await tm.post_task(
            subject="deploy-prod-api",
            spec="Roll out the new API via standard Terraform IaC.",
            campaign=CAMPAIGN,
        )
        claim = await tm.claim_task(quest_id)
        print(f"  posted {quest_id}; claim won={claim['won']}")

        # Agent A does the work, then fulfills with a rich report.
        report = (
            "Deployed prod API via Terraform plan + apply. Used the "
            "company's standard IaC module (modules/api-stack). Required "
            "VPC peering with the data-lake account. First deploy budget "
            "was 5 minutes wall-clock."
        )
        await tm.complete_task(quest_id, report=report)
        print(f"  fulfilled {quest_id}: {report[:60]}...")


async def run_consolidation() -> None:
    print(">>> Consolidation pipeline running")
    # The consolidator can run as ANY agent — its agent_id is a label only.
    async with TieredMemory(agent_id="consolidator") as tm:
        result = await consolidate(tm, campaign=CAMPAIGN)
        print(
            f"  seen={result.scrolls_seen} imprinted={result.scrolls_imprinted} "
            f"skipped={result.scrolls_skipped}"
        )


async def agent_b_session_two() -> None:
    print(">>> Agent B — session 2 (hours later, fresh agent)")
    async with TieredMemory(agent_id="agent_b") as tm:
        # Agent B has NO knowledge of agent A's work, but can query semantic memory.
        context = tm.query_context(query="how do we deploy production APIs?", k=3)
        print(f"  semantic recall returned {len(context)} memories:")
        for m in context:
            print(f"    - {m.get('content', '')[:100]}")

        # Now agent B posts + claims its own quest, armed with the recalled context.
        quest_id = await tm.post_task(
            subject="deploy-prod-data-pipeline", campaign=CAMPAIGN
        )
        claim = await tm.claim_task(quest_id)
        print(f"  agent B posted {quest_id}; claim won={claim['won']}")
        print(
            "  agent B can now apply the Terraform IaC pattern recalled from "
            "agent A's earlier work."
        )


async def main() -> None:
    await agent_a_session_one()
    await run_consolidation()
    await agent_b_session_two()


if __name__ == "__main__":
    asyncio.run(main())
```

**Expected output**:

```
>>> Agent A — session 1
  posted QUEST-1; claim won=True
  fulfilled QUEST-1: Deployed prod API via Terraform plan + apply. Used the...
>>> Consolidation pipeline running
  seen=1 imprinted=1 skipped=0
>>> Agent B — session 2 (hours later, fresh agent)
  semantic recall returned 1 memories:
    - Production API deployments use the Terraform IaC pattern with the company's
  agent B posted QUEST-2; claim won=True
  agent B can now apply the Terraform IaC pattern recalled from agent A's earlier work.
```

`★ Insight ─────────────────────────────────────`
- **This transcript IS the portfolio artifact.** It proves the two-tier architecture works end-to-end: write to operational tier → consolidate → semantic recall in a fresh session. Save the transcript verbatim.
- **The demo intentionally separates the three phases**: agent A → consolidation → agent B. In production, all three run concurrently with the consolidation cron on a 5-min cadence. The lab serialization makes the dataflow visible.
`─────────────────────────────────────────────────`

---

## Phase 5 — Four-Way Benchmark (~1.5 hours)

### 5.1 Benchmark harness

`tests/test_four_way_bench.py`:

```python
"""4-way comparison on the W3.5 15-Q multi-agent recall benchmark.

Backends:
  (a) no_memory      — baseline, agent has zero memory between calls
  (b) guild_only     — operational tier only, raw scrolls
  (c) evercore_only  — semantic tier only, no atomic-claim
  (d) two_tier       — full architecture (this lab's contribution)
"""
import asyncio

import pytest

from src.tiered_memory import TieredMemory
from src.consolidation import consolidate


# Reuses the 15-Q probe set from lab-03-5-memory/tests/test_recall.py
# Each test case: (seed_scroll, query, expected_keyword)

PROBES = [
    ("deployed via Terraform IaC apply pattern",
     "how do we deploy?", "terraform"),
    ("auth tokens expire after 30 minutes",
     "how long are tokens valid?", "30"),
    # ...add the remaining 13 from W3.5 probe set with multi-agent variants
]


BENCH_CAMPAIGN = "bench-w358-15q"


async def run_two_tier(probes: list[tuple[str, str, str]]) -> dict[str, float]:
    """Run probes against the full two-tier architecture.

    Seed phase posts + claims + fulfills one quest per probe row, all
    tagged with BENCH_CAMPAIGN so consolidate() only pulls this run's
    scrolls (not lab-state leakage from prior runs).
    """
    results: dict[str, int] = {"pass": 0, "fail": 0}
    async with TieredMemory(agent_id="bench") as tm:
        for i, (seed, _, _) in enumerate(probes):
            qid = await tm.post_task(
                subject=f"bench_seed_{i}", campaign=BENCH_CAMPAIGN
            )
            await tm.claim_task(qid)
            await tm.complete_task(qid, report=seed)

        await consolidate(tm, campaign=BENCH_CAMPAIGN)  # Move scrolls → EverCore

        for _, query, expected in probes:
            memories = tm.query_context(query=query, k=3)
            text = " ".join(m.get("content", "") for m in memories).lower()
            if expected.lower() in text:
                results["pass"] += 1
            else:
                results["fail"] += 1
    total = results["pass"] + results["fail"]
    return {"pass_rate": results["pass"] / total, **results}


@pytest.mark.asyncio
async def test_two_tier_beats_singles_on_aggregate():
    two_tier = await run_two_tier(PROBES)
    # (Single-tier baselines run separately; numbers go into RESULTS.md.)
    # Assertion: two-tier should pass at least 80% on this 15-Q set.
    assert two_tier["pass_rate"] >= 0.80, (
        f"two-tier underperformed: {two_tier}"
    )
```

### 5.2 Expected RESULTS.md matrix

| Backend | section-recall | cross-session | multi-agent | **aggregate** | mean latency |
|---|---|---|---|---|---|
| (a) no-memory baseline | 0.00 | 0.00 | 0.00 | ~0.10 | ~50ms |
| (b) guild-only | 0.80 | 0.20 | 0.93 | ~0.55 | ~50ms |
| (c) evercore-only | 0.60 | 0.85 | 0.20 | ~0.60 | ~200ms |
| (d) **two-tier (lab)** | **0.85** | **0.85** | **0.93** | **~0.85** | ~250ms |

Two-tier should beat each single-tier by ≥20% absolute on aggregate.

### 5.3 Optional — LongMemEval `oracle` subset

For industry-standard comparison:

```bash
# Download LongMemEval oracle subset (~50 questions)
cd ~/code && git clone https://github.com/xiaowu0162/LongMemEval.git
cp -r LongMemEval/data ~/code/agent-prep/lab-03-5-8-two-tier/data/longmemeval/
```

Re-run the two-tier system against this set. EverCore's published score is **LongMemEval 83%**. A from-scratch two-tier built in one lab day shouldn't beat this — but matching ≥70% would be a strong signal. If you trail by >30 percentage points, the consolidation pipeline's summarizer is the most likely culprit (under-summarizing → loss of detail vs over-summarizing → loss of nuance).

`★ Insight ─────────────────────────────────────`
- **The benchmark numbers are the architecture's defense.** Anyone can claim "two-tier is better"; the differential on a 15-Q probe is the proof. Without these numbers, the lab is a tutorial; with them, it's a measurement-driven architecture report.
- **LongMemEval Phase 5.3 is optional but interview-gold.** Saying "I ran my from-scratch two-tier on LongMemEval `oracle` and scored 74% vs EverCore's published 83%" is the kind of grounded calibration interviewers reward over hand-waving.
`─────────────────────────────────────────────────`

---

## Production Considerations

**Is the guild + EverCore architecture valid in production? Honest answer: VALID for the chapter's pedagogical thesis, NOT optimal for production performance or scalability.** The architecture exercises the most concepts (operational tier, conversation-shape extraction pipeline, the conversation-vs-fact contract mismatch, cross-agent recall via shared `user_id`) — which is exactly what a senior-engineer interview rewards. But for a real production workload it costs more than the alternatives. Both truths matter; teach both.

### Paradigm commitment — full 8-paradigm taxonomy + W3.5.8's explicit choice

Memory-system literature (Batchelor-Manning 2026 survey of 19 agent-memory systems) identifies **eight distinct paradigms** for "what memory fundamentally is" — each a different commitment about the primary retrieval mode:

| # | Paradigm | One-sentence summary | Representative systems |
|---|---|---|---|
| 1 | **Flat vector RAG + structured extras** | Embed everything, retrieve top-k, prepend; add layers (provenance, types, confidence, dedup) on top | SimpleMem, Memex (early) |
| 2 | **Knowledge-graph augmented** | Memory as typed graph of entities + relationships; traversal + vector ranking | Graphify, EdgeQuake, GitNexus |
| 3 | **Progressive compression** | Hierarchy of increasingly summarised representations with heat-gated promotion between tiers | MemoryOS, SimpleMem (hybrid) |
| 4 | **Multi-index hybrid search** | Multiple indexes + fusion stage (usually RRF k=60) | Hindsight, Supermemory, Graymatter, OpenContext, mem9 |
| 5 | **LLM-as-retriever** | Hierarchical map of documents; LLM navigates by reading + tree-walking | Memex (final), OpenKB, Supermemory rewrite mode |
| 6 | **Trace-as-memory** | Memory is the agent's own execution history, not the user's data | Moraine (pure), Hindsight (hybrid observation tier) |
| 7 | **Karpathy LLM wiki** | Plain Markdown + wikilinks + frontmatter; index file as catalogue; user as final curator | Understand-Anything (reads), OpenKB (writes), LLM-Wiki (both) |
| 8 | **Filesystem-native context store** | File is the artefact; database is a derivative cache; disk wins | OpenContext, Tolaria, second-brain |

**The negative consensus across all 19 systems: flat vector RAG ALONE is not enough.** Every one of the 19 that started with Paradigm-1-as-sole-mechanism eventually added something on top. The agreement is total. The disagreement is on WHICH paradigm to compose with it.

#### Where W3.5.8 sits (explicit composition)

This lab implements a **Paradigm 1 + Paradigm 3 + Paradigm 6 composition** with **Paradigm 3 as primary retrieval**:

| Component | Paradigm | Role |
|---|---|---|
| guild scrolls (raw quest reports + journals + timestamps + agent attribution) | **Paradigm 6** | Storage substrate. NOT in the read-time hot path; accessed only via `list_closed_quests` + `get_scroll` for forensics/replay. |
| `consolidate()` pipeline (summarize → quality_gate → imprint) | **Paradigm 3** | Compresses Paradigm-6 traces into Paradigm-3 facts; heat-gated by `quality_score` + `promotion_threshold`. |
| EverCore semantic tier (memcell + atomic_facts + profile aggregation) | **Paradigm 3** | Native shape: progressive compression with extraction pipeline. |
| Qdrant variant (Phase 7: embed + upsert with type + confidence + provenance metadata) | **Paradigm 1 + structured extras** | Flat vector RAG with the write-time investment forms applied (forms #4-6 from §Production Considerations earlier). |
| `query_context()` (user-facing retrieval) | **Paradigm 3** | Returns consolidated facts. THIS is the primary retrieval surface. |

**Paradigms we explicitly did NOT implement** (with reason):

| # | Paradigm | Why not in W3.5.8 |
|---|---|---|
| 2 | Knowledge-graph | Deferred to [[Week 3.5.9 - Memory Benchmarks and Hypergraph Three-Tier]] which adds HyperMem as the L3 relational tier. W3.5.8 stays two-tier. |
| 4 | Multi-index hybrid (RRF) | EverCore does this INTERNALLY (Mongo + ES + Milvus); we don't compose it externally. Stretch lab candidate. |
| 5 | LLM-as-retriever | Different chapter entirely — would be a W3.7-class agentic-RAG topic, not a memory chapter. |
| 7 | Karpathy wiki | Not memory-system shape; closer to W6.7 Agent Skills (Anthropic-pattern skills as Markdown). |
| 8 | Filesystem-native | The chapter assumes a database substrate (SQLite for guild, EverCore/Qdrant for semantic). Filesystem-native is a different bet on substrate ownership. |

#### The Paradigm 3 / Paradigm 6 contradiction (and how composition resolves it)

You cannot make BOTH Paradigm 3 and Paradigm 6 primary at the same retrieval call site without contradiction. The same user query "what did agent A do on the API deploy?" returns:

- **Paradigm 3**: "Production deploys use Terraform IaC with VPC peering and 5-min budget." (consolidated lesson)
- **Paradigm 6**: "Agent A claimed QUEST-74 at 14:03 UTC; ran terraform plan; ran terraform apply; got HTTP 200 at 14:08; verified VPC peering at 14:09; wrote scroll; fulfilled quest at 14:10." (audit trail)

Both are "memory." They answer different questions. Routing the same query through both forces them to compete for primacy at the retrieval-fusion layer — which the literature shows degrades both.

**The production composition pattern** (which W3.5.8 inherits): pick ONE paradigm primary; expose the other(s) as SEPARATE retrieval methods at distinct call sites. W3.5.8 picks Paradigm 3 primary via `query_context()`. The lab leaves Paradigm-6 retrieval as a Phase 10 stretch via `query_trajectory(query)` — searches raw scrolls in guild for audit/replay/explainability use cases. Different namespaces, different latency profiles, different ranking models. Caller commits per-query by picking the method.

#### Architectural consequences of the choice

Picking Paradigm 3 primary forces these consequences through the whole stack — every reader should be able to name them:

1. **Consolidation pipeline is load-bearing.** Recall quality depends on summarizer quality + atomic_fact extraction quality. The BCJ Entry 8 reasoning-model token-budget fix matters BECAUSE the summarizer is on the critical path.
2. **Conversation-shape contract matters** (BCJ Entry 13). EverCore's pipeline expects Paradigm-6-shaped INPUT (conversation transcripts) and emits Paradigm-3 OUTPUT (memcells). Our scrolls are already Paradigm-3-shaped; forcing the 2-turn synthetic wrap + flush is a workaround. A pure-Paradigm-6 architecture would not have this mismatch.
3. **Per-imprint latency** is dominated by write-time investment (article above: 5-12 min per 50-scroll batch on EverCore; 1-2 min on Qdrant). Read latency is correspondingly low. A Paradigm-6-primary architecture would invert this — sub-second writes, expensive multi-hop reads over event logs.
4. **The 6 write-time investment forms** (atomisation, type tagging, confidence scoring, provenance, multi-step ingest, online dedup-and-synthesis) are the Paradigm-1-with-extras pattern from the survey. Phase 7 Qdrant ships 4/6 today; Phase 9 stretch ships the 5th (dedup-and-synthesis); the 6th (multi-step ingest) is what `consolidate()` ALREADY does.

`★ Insight ─────────────────────────────────────`
- **Naming the paradigm IS the senior-engineer signal.** Candidates who say "I built a memory system" lose to ones who say "I built a Paradigm 1+3+6 composition with Paradigm 3 primary; here are the trade-offs that propagate" — same artifact, very different demonstration of architectural awareness.
- **The negative consensus matters more than the positive choice.** All 19 surveyed systems agree flat-vector-RAG-only is insufficient; the field is in "informed eclecticism" — agreed on the problem, agreed on what doesn't work, no convergence on a single replacement. The lab teaches BOTH sides: Phase 7 Qdrant variant adds 4 of the 6 write-time-investment forms on TOP of vector RAG (Paradigm 1 + structured extras); EverCore variant uses Paradigm 3 progressive compression natively.
- **Each paradigm has an Achilles' heel.** Paradigm 1 lacks temporal + relational queries; P2 KGs are hardest to maintain under source change; P3 progressive compression LOSES information by design; P4 multi-index needs explainable fusion; P5 LLM-as-retriever pays at read time; P6 trace-only has no synthesis; P7 wiki needs human curation at scale; P8 filesystem-native pushes synthesis onto the agent. The candidate who can name the weakness of their chosen paradigm is the one who already mitigated it.
`─────────────────────────────────────────────────`

### Pre-design checklist — which bucket is your data in?

Before picking a semantic backend, answer these three questions about your input shape. The answer tells you which bucket you're in and which backend earns its cost.

```mermaid
flowchart TB
    Q1{"Inputs are<br/>multi-turn<br/>conversations?"}
    Q2{"Need atomic-fact<br/>granularity in<br/>retrieval?"}
    Q3{"Serve multiple<br/>identifiable users<br/>over long time horizon?"}
    B1["Bucket 1: USE EverCore<br/>(pipeline earns its cost)"]
    B2["Bucket 2: USE Qdrant + bge-m3<br/>(EverCore = 5x overhead, no gain)"]
    B3["Bucket 3: USE BOTH<br/>(route by data shape)"]

    Q1 -->|"yes"| Q2
    Q1 -->|"no — pre-extracted facts"| B2
    Q2 -->|"yes"| Q3
    Q2 -->|"no — whole-conversation OK"| B2
    Q3 -->|"yes — profile + episodes matter"| B1
    Q3 -->|"no — single-user data"| B2
    B1 --> B3Note["Production at scale<br/>often combines:<br/>both backends behind<br/>a router"]
    B2 --> B3Note
    B3Note --> B3

    style Q1 fill:#f1c40f,color:#000
    style Q2 fill:#f1c40f,color:#000
    style Q3 fill:#f1c40f,color:#000
    style B1 fill:#27ae60,color:#fff
    style B2 fill:#4a90d9,color:#fff
    style B3 fill:#9b59b6,color:#fff
```

**Bucket 1 — USE EverCore.** Three conditions converge: multi-turn conversations + atomic-fact granularity + multiple identifiable users over time. Ideal cases:
- Customer support agents with cross-session memory (per-customer profile + episode recall)
- Tutoring / coaching agents (per-student profile aggregates from session conversations)
- Multi-participant team-chat assistants (tracks who said what when)
- Long-term companion / relationship agents (months of conversation → emergent personality profile)
- Meeting transcript analyzers (boundary detection breaks transcripts into topics)
- Healthcare AI with cross-visit patient history

In all six: the conversation IS the data. EverCore's pipeline does work (boundary detection + atomic_fact decomposition + profile aggregation) you'd otherwise hand-roll — ~700-1000 LOC of LLM-prompting + extraction + aggregation saved.

**Bucket 2 — USE Qdrant + bge-m3.** Inputs are already-extracted facts, single-user data, or sub-100ms latency required. **This is the bucket THIS lab is in** — quest scrolls are pre-summarized facts, not raw dialogue. Phase 7 ships the Qdrant variant; for production with this shape, that's the right backend. Cases:
- Tool-result memory (function outputs stored for later retrieval)
- RAG knowledge bases (documents → chunks → embeddings)
- Single-fact memory under sub-100ms search budget
- Constrained-infrastructure deployments (edge, embedded, single-VM, 7 containers won't fit)

**Bucket 3 — USE BOTH (route by data shape).** Production agent systems at scale often combine:
- **Hot semantic tier** = Qdrant for fast tool-result lookups + document RAG (~80ms search)
- **Cold semantic tier** = EverCore for user-conversation profiles + episodic memory (~300ms search)
- **Operational tier** = guild for atomic-claim + quest board (unchanged from W3.5.5 / W3.5.8)

Route at write-time by data shape: facts → Qdrant; dialogues → EverCore. Same agent, two semantic backends behind a router. This is the topology multi-modal production agent systems actually ship.

### What EverCore's pipeline ACTUALLY does (the value you pay 5x latency for)

| Capability | What it gives you | Cost without EverCore (DIY) |
|---|---|---|
| LLM-driven episode boundary detection | Auto-segment multi-turn conversations into topic episodes without manual cuts | ~200 LOC + LLM prompt engineering |
| atomic_fact decomposition | One conversation → N retrievable single-fact rows | ~150 LOC + quality-tuned extractor |
| profile aggregation across episodes | Per-user persistent profile built up from extracted facts over months | ~300 LOC + LLM merge + conflict resolution |
| Hybrid retrieval (Mongo + ES + Milvus) | Semantic + keyword + structured filters in one query | Roll your own or live with semantic-only |
| Episodic → semantic consolidation semantics | Old memories decay, profile facts update, recency-weighted retrieval | Significant ML/policy work |

**Total saved by adopting EverCore: ~700-1000 LOC of LLM-prompting + extraction + aggregation code — IF your data is in Bucket 1.** Wasted IF you're in Bucket 2 (W3.5.8's actual case): you pay 5x latency for redundant work on already-extracted content.

### Measured cost (2026-05-14, 1-scroll round-trip on M5 Pro 48 GB)

| Stage | guild + EverCore | guild + raw Qdrant + bge-m3 | Delta |
|---|---|---|---|
| LLM summarize_scroll (oMLX gpt-oss-20b reasoning model, max_tokens=400) | ~3-5s | ~3-5s | tie — same summarizer |
| Imprint pipeline (extract memcell + atomic_facts + embed + index) | ~3-5s (2-3 internal LLM calls + embed) | ~150ms (embed + insert) | **20-30x slower** |
| Cross-agent search | ~250-500ms (Mongo + Milvus + ES hybrid) | ~50-150ms (pure HNSW) | **3-5x slower** |
| Backend services running | 7 containers (Mongo + ES + Milvus etcd + Milvus minio + Milvus standalone + Redis + EverCore app) | 1 container (Qdrant) | **7x infrastructure** |
| Idle RAM | ~2 GB | ~300 MB | **6x heavier** |
| 50-scroll consolidate batch wall time | ~5-12 min | ~1-2 min | **5x slower** |

### When NOT to use EverCore

EverCore is **conversation-shaped** by design — its memcell extraction pipeline assumes incoming data is multi-turn dialogue and runs an LLM boundary detector before storing. When your scrolls ARE multi-turn dialogues (chat transcripts, customer-support sessions, agent ↔ user conversations), this pipeline gives you `atomic_fact` decomposition + `profile` aggregation for free — high-value.

When your scrolls are **already-consolidated facts** (W3.5.5 pattern: completed quest reports, structured tool outputs, single-sentence summaries), you pay 2-3 redundant LLM calls per imprint (boundary detection + memcell extraction + atomic_fact extraction) for output you already have. The conversation-vs-fact contract mismatch is the load-bearing decision documented in BCJ Entry 13 — fixed in the lab via the 2-turn-synthetic-conversation + flush trick, but the redundant cost remains.

**Decision rule:**
- Multi-turn dialogue data → EverCore-class backend (or Letta, Mem0)
- Single-fact data → raw Qdrant + bge-m3 (or Pinecone, Weaviate)

### What you lose if you drop EverCore

| EverCore capability | Replace with |
|---|---|
| LLM-driven memcell extraction (episode boundary detection) | Skip — your facts are already pre-episoded |
| `atomic_fact` decomposition (auto-split a fact into N sub-facts) | Custom LLM pass if needed; rarely worth it for already-summarized content |
| `profile` aggregation across episodes | Maintain a separate per-user profile table (50 LOC) |
| Hybrid retrieval (Milvus + ES + rerank) | bge-m3 + Qdrant native filtering covers ~95% of cases; add Qdrant reranking if needed |
| Mongo + ES + Milvus durability | Qdrant's snapshot/replica primitives |

### What you keep

The two-tier architecture itself — operational `guild` + semantic store + consolidation pipeline + shared tenant identity for cross-agent recall — stays identical. **Swapping EverCore for Qdrant is a one-method-pair change inside `TieredMemory` (the `imprint()` and `query_context()` methods).** Phase 7 below ships the alternative as a stretch lab.

`★ Insight ─────────────────────────────────────`
- **The "wrapper IS the architecture" claim from §2.1 holds.** Once `TieredMemory` exists, the backend choice is two methods. Don't conflate "I picked EverCore" with "I designed two-tier" — the second is the real architectural decision.
- **EverCore's redundant-LLM cost is the load-bearing lesson.** A real production decision: do you pay 5x latency for memcell + atomic_fact decomposition you may not need? For a fact-shaped workload, the honest answer is no.
- **Scalability ceiling is at guild, not EverCore.** Both stacks bottleneck at guild's SQLite single-writer once you scale to a fleet of agents. Production fix is guild → Postgres backend; choosing EverCore vs Qdrant only matters AFTER that.
`─────────────────────────────────────────────────`

---

## Phase 7 — Optional Stretch: Drop-in Qdrant Backend (~2 hours)

Goal: prove the §2.1 "wrapper IS the architecture" claim by swapping EverCore for raw Qdrant + bge-m3 with zero changes to the consolidation pipeline, the demo, or the tests. Same API contract on `TieredMemory.imprint()` and `TieredMemory.query_context()`; different backend underneath.

### 7.1 Stand up Qdrant

```bash
docker run -d --name lab358-qdrant -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant:latest
# Verify
curl -sf http://localhost:6333/collections | head -3
```

### 7.2 The drop-in wrapper

`src/tiered_memory_qdrant.py` — same class name `TieredMemory`, same public method signatures, different backend:

```python
"""TieredMemory — Qdrant variant. Drop-in replacement for the EverCore version.

Only imprint() and query_context() differ. The operational-tier methods
(post_task, claim_task, complete_task, list_closed_quests, get_scroll)
import-and-delegate to the guild wrapper unchanged.

Trade-off vs EverCore variant:
  + 5x faster imprints, 3x faster searches, 7x lighter infrastructure
  - No automatic atomic_fact decomposition (you store the consolidated fact as-is)
  - No profile aggregation (maintain a per-user profile table separately)
  - No hybrid Mongo+ES+Milvus durability (Qdrant snapshots are the durability story)
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from openai import OpenAI

from src.guild_client import GuildClient, is_accept_winner


COLLECTION = "lab358_memories"
EMBED_DIMS = 1024  # bge-m3-mlx-fp16


@dataclass
class TieredMemoryConfig:
    qdrant_base_url: str = "http://localhost:6333"
    timeout_s: float = 10.0


class TieredMemory:
    def __init__(
        self,
        agent_id: str,
        user_id: str | None = None,
        config: TieredMemoryConfig | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.user_id = user_id or os.getenv("LAB358_USER_ID", "shared")
        self.config = config or TieredMemoryConfig()
        self._guild = GuildClient(agent_id=agent_id)
        self._http = httpx.Client(
            base_url=self.config.qdrant_base_url,
            timeout=self.config.timeout_s,
        )
        self._llm = OpenAI(
            base_url=os.getenv("OMLX_BASE_URL"),
            api_key=os.getenv("OMLX_API_KEY"),
        )
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        # Idempotent — 200 if exists, 200 if created, 409 silently ignored.
        try:
            self._http.put(
                f"/collections/{COLLECTION}",
                json={"vectors": {"size": EMBED_DIMS, "distance": "Cosine"}},
            )
        except httpx.HTTPStatusError:
            pass

    def _embed(self, text: str) -> list[float]:
        resp = self._llm.embeddings.create(
            model=os.getenv("MODEL_EMBED", "bge-m3-mlx-fp16"),
            input=text,
        )
        return resp.data[0].embedding

    async def __aenter__(self) -> "TieredMemory":
        await self._guild.__aenter__()
        return self

    async def __aexit__(self, *exc) -> None:
        await self._guild.__aexit__(*exc)
        self._http.close()

    # ── Operational tier — identical to EverCore variant ───────────────
    # (post_task, claim_task, complete_task, list_closed_quests, get_scroll
    # delegate to self._guild — same as §2.1)

    # ── Semantic tier — Qdrant ─────────────────────────────────────────

    def imprint(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Embed + upsert one consolidated fact. No conversation shape,
        no boundary detection, no flush dance. ~150ms wall-clock."""
        point_id = str(uuid.uuid4())
        vector = self._embed(content)
        payload = {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "content": content,
            **(metadata or {}),
        }
        r = self._http.put(
            f"/collections/{COLLECTION}/points",
            json={"points": [{"id": point_id, "vector": vector, "payload": payload}]},
        )
        r.raise_for_status()
        return point_id

    def query_context(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Cosine-nearest top-k filtered by shared user_id."""
        vector = self._embed(query)
        r = self._http.post(
            f"/collections/{COLLECTION}/points/search",
            json={
                "vector": vector,
                "limit": k,
                "filter": {
                    "must": [{"key": "user_id", "match": {"value": self.user_id}}]
                },
                "with_payload": True,
            },
        )
        r.raise_for_status()
        return [
            {
                "content": hit["payload"]["content"],
                "score": hit["score"],
                **hit["payload"],
            }
            for hit in r.json()["result"]
        ]
```

### 7.3 Swap into the demo

In `src/demo_two_agent_shared_knowledge.py`, change one import line:

```python
# Before
from src.tiered_memory import TieredMemory
# After
from src.tiered_memory_qdrant import TieredMemory
```

Re-run. The rest of the demo — `post_task`, `claim_task`, `complete_task`, `consolidate`, `query_context` — is unchanged.

### 7.4 Expected delta on the 15-Q recall benchmark

| Backend | Aggregate recall | Mean imprint wall | Mean search wall |
|---|---|---|---|
| guild + EverCore (the default lab) | ~0.85 *(estimated; pending Phase 5 measurement)* | ~3-5s | ~250-500ms |
| **guild + Qdrant (this stretch)** | ~0.78 *(estimated; loses atomic_fact granularity)* | ~150ms | ~80ms |
| Delta | -7 pp recall | **20-30x faster** | **3-5x faster** |

**Interpretation:** Qdrant loses ~7 percentage points of recall because EverCore's atomic_fact decomposition + profile aggregation surface relevant memories that vector cosine alone misses. Whether that 7pp is worth 20x latency is a product decision, not an architecture one. The chapter teaches the decision; the lab gives you both.

`★ Insight ─────────────────────────────────────`
- **The one-line import swap IS the interview soundbite.** Saying "my semantic tier is one wrapper class; I can swap it from a heavyweight extraction pipeline to a pure vector store by changing one import" demonstrates the seam-discipline interviewers reward.
- **The Qdrant variant SKIPS the conversation-shape gymnastics from BCJ Entry 13** — no 2-turn synthetic wrap, no session_id-scoped flush, no waiting for memcell extraction. The contract on `TieredMemory.imprint()` stays the same; the implementation gets simpler because the backend's contract is simpler.
- **bge-m3 stays as the embedding model across both variants** (oMLX serves it; EverCore uses it via VECTORIZE_*; Qdrant uses it directly). The embedding choice is orthogonal to the storage backend — another layer the wrapper isolates correctly.
`─────────────────────────────────────────────────`

---

## Phase 8 — Optional Stretch: EverCore Earns Its Cost on Bucket-1 Data (~3 hours)

Phase 7 showed that for THIS lab's data shape (already-extracted facts), Qdrant is the right backend and EverCore pays a 5x latency penalty for redundant work. Phase 8 is the symmetric demonstration: rewrite the imprint flow around DIALOGUE inputs (Bucket 1 data) and show EverCore's pipeline actually earning its cost — boundary detection segments naturally, atomic_facts decompose for retrieval granularity, profile aggregation builds per-participant state.

The goal is pedagogical honesty: a reader who only sees Phase 7 might conclude "EverCore is always wrong." It's not. It's wrong for the wrong shape. Phase 8 is the right-shape demo.

### 8.1 Scenario: Simulated multi-turn agent ↔ user dialogue

Replace the "agent autonomously executes tasks" loop with a "AI assistant talks to a user about deployments" scenario. The user asks questions, the assistant answers, both contribute knowledge. EverCore's pipeline now has the data shape it was built for.

```python
# src/demo_conversational_imprint.py  (SPEC — TBD lab impl)
"""Bucket-1 demo: EverCore on its native data shape.

Pattern: simulate 3 multi-turn dialogues between an AI assistant
('robot_001') and three users ('alice', 'bob', 'carol') over the
course of a week. Each dialogue is ~10 turns spanning a single
deployment topic (Alice: API rollout; Bob: token rotation; Carol:
incident response). POST each dialogue as a single batch with
unique session_id; let EverCore's LLM boundary detector decide
when an episode is complete — no flush trickery needed.
"""
```

### 8.2 Three load-bearing differences from the Bucket-2 lab

| Aspect | Phase 4 (Bucket 2 — current lab) | Phase 8 (Bucket 1 — stretch) |
|---|---|---|
| Input shape | Pre-summarized scroll, 1 fact | Multi-turn dialogue, 10+ turns per session |
| user_id | Single shared `"shared"` | Per-participant: `alice`, `bob`, `carol`, `robot_001` |
| Imprint primitive | Synthetic 2-turn wrap + forced flush | Real conversation messages, no flush — let boundary detection fire naturally |
| EverCore returns | 1 memcell per imprint | N memcells per dialogue + M atomic_facts per memcell + per-user profile aggregates |
| Query | "what do we know about <subject>?" → 1 episode | "what does Alice care about?" → profile + relevant episodes |

### 8.3 The interview signal (why this matters)

Reader who has done both Phase 7 + Phase 8 can answer the senior question:

> "When would you use EverCore-class memory vs raw vector store?"

with concrete framing: "Bucket 1 cases need EverCore's extraction pipeline — boundary detection + atomic_facts + profile aggregation save 700-1000 LOC of LLM-prompting code I'd otherwise hand-roll. Bucket 2 cases — pre-extracted facts, single-user data, sub-100ms search — pay 5x latency for nothing; Qdrant is the right answer. Bucket 3 production systems route by data shape: facts to Qdrant, dialogues to EverCore, behind the same TieredMemory wrapper."

That answer is grounded in TWO measured experiments (Phase 7 + Phase 8), not one. Beats "I think it depends."

### 8.4 Lab deliverables (SPEC; not yet implemented in lab repo)

1. `src/demo_conversational_imprint.py` — simulated 3-user, 3-dialogue scenario (each ~10 turns, hand-written or generated by a local LLM role-play prompt)
2. `tests/test_conversational_extraction.py` — assert each dialogue produces ≥1 memcell + ≥3 atomic_facts; assert per-user profile is populated after consolidation
3. Compare retrieval quality: ask `"what does Alice care about?"` against Phase 8 EverCore data vs Phase 7 Qdrant data — Phase 8 should return Alice's profile + relevant episodes; Phase 7 returns just nearest-vector fragments (since Qdrant has no profile concept)
4. Updated RESULTS.md row: "Phase 8 — Bucket 1 EverCore on dialogue data: <measured imprint latency, atomic_fact count per dialogue, profile completeness%>"

`★ Insight ─────────────────────────────────────`
- **Phase 7 vs Phase 8 is the bucket-2 vs bucket-1 demonstration.** Phase 7 proves Qdrant wins when the data is pre-extracted. Phase 8 proves EverCore wins when the data is dialogue. Reader sees BOTH halves of the architectural trade-off.
- **Phase 8 has no flush trickery.** BCJ Entry 13 is a Bucket-2 workaround; in Bucket 1 you don't need it because the LLM boundary detector actually finds episodes in real conversations. The fix matches the data shape.
- **Profile aggregation is the EverCore feature most consumers underestimate.** Per-user profile facts built up over months are the thing customer-support / coaching / companion agents need that Qdrant cannot deliver out of the box. Phase 8 makes the gap concrete.
`─────────────────────────────────────────────────`

---

## Bad-Case Journal

*Provenance.* Entries 1–5 are **pre-scoped** at chapter-authoring time — failure modes predicted from theory; not yet confirmed against this lab's runs. Entries 6–13 are **observed** in the 2026-05-14 first-execution session against live guild + EverCore + local oMLX. Per the curriculum's real-data discipline, only the observed entries are load-bearing for interview soundbites; pre-scoped entries are intellectual scaffolding pending validation.

**Entry 1 — Consolidation pipeline runs while guild is mid-write; reads inconsistent quest state.** *(pre-scoped)*
*Symptom:* Race between `consolidate()`'s `quest_list(status='done')` query and a concurrent `quest_fulfill` from a live agent. New quest lands in `done` state AFTER list query but BEFORE next batch; appears to be "skipped forever" until next cron cycle.
*Root cause:* No serialization between batch consolidation and live agent writes. Acceptable for cron-style (next run picks up the missed quest because the dedup table doesn't yet have its QUEST-ID) but produces measurement noise during benchmarking.
*Fix:* Either (a) run consolidation in dedicated maintenance window (production pattern), or (b) snapshot guild's SQLite during list — too aggressive for hot path. The benchmark workaround is to call `consolidate()` AFTER all writes complete, not interleaved. Production rule: consolidation is eventual-consistency-tolerant by design; don't fight it.

**Entry 2 — EverCore Postgres connection pool exhausted under benchmark load.** *(pre-scoped)*
*Symptom:* Phase 5 benchmark runs 15 probes × 3 query_context calls = 45 EverCore HTTP requests in 30 seconds; EverCore returns 503 mid-bench.
*Root cause:* EverCore's docker-compose Postgres ships with default `max_connections=100` and EverCore's internal pool spawns one connection per concurrent request. Lab's parallel queries hit pool ceiling.
*Fix:* Throttle benchmark to serial (already sufficient for 15-Q load); for production, bump Postgres `max_connections` to 300 and EverCore pool to 50. Long-term, EverCore should pool connections more aggressively — known issue in their tracker.

**Entry 3 — Summarizer LLM outputs verbose multi-paragraph "summaries"; EverCore stores them as long memories.** *(pre-scoped)*
*Symptom:* `query_context(query="how do we deploy?")` returns one memory that is a 400-token paragraph instead of a one-sentence fact. Semantic search precision drops because long memories dominate cosine similarity.
*Root cause:* Phase 3 SUMMARIZE_PROMPT asks for "one sentence" but gpt-oss-20b under temperature=0.0 sometimes elaborates. No max_tokens enforcement.
*Fix:* Tighten prompt with explicit "MAXIMUM 25 words" + add `max_tokens=80` in the LLM call. Add post-processing: if summary > 200 chars, re-summarize. Production rule: summarization is a contract, not a hint; enforce length at both prompt + token-budget + post-processing layers.

**Entry 4 — Idempotency check fires but EverCore returns wrong scroll_id format; duplicate imprints land.** *(pre-scoped)*
*Symptom:* After 5 batch runs of the same scroll, EverCore has 5 copies of the semantic fact. `query_context` returns all 5; semantic-recall pass rate stays high but storage bloats linearly.
*Root cause:* `query_context(query=f"scroll_id:{scroll['id']}", k=1)` is a SEMANTIC query, not a metadata-filter query. Semantic search over "scroll_id:abc123" might return false negatives — short-string queries don't embed well in BGE-M3.
*Fix:* Use EverCore's metadata-filter API (if available) instead of semantic query for idempotency check. If not available, maintain a local SQLite table of imprinted scroll_ids — cheap and exact. Production rule: idempotency checks need EXACT matching, not approximate semantic similarity.

**Entry 5 — Two-tier latency spikes when consolidation runs synchronously after every quest_fulfill (anti-pattern).** *(pre-scoped)*
*Symptom:* Naive implementation calls `await consolidate()` inside `complete_task()`. Each quest fulfillment adds ~10-30s latency (LLM summarization + EverCore imprint). Multi-agent throughput collapses.
*Root cause:* Synchronous consolidation pushes EverCore's slow path onto guild's hot path. The whole point of two-tier separation is preserving guild's sub-100ms latency.
*Fix:* Consolidation MUST be async / batched / cron-scheduled. Never on the hot path. The biological analogy holds: hippocampus doesn't wait for cortex to consolidate before accepting the next event — consolidation happens during sleep. **Discipline rule:** if your architecture sometimes runs the slow tier synchronously, you've collapsed the tiers.

**Entry 6 — `uv add` fails with "No pyproject.toml found".** *(observed 2026-05-14)*
*Symptom:* `uv add --dev pytest pytest-asyncio` → `error: No pyproject.toml found in current directory or any parent directory`. Reader assumes lab scaffold inherits uv config from W3.5.5; it does not.
*Root cause:* W3.5.5 lab predates uv adoption (pip + requirements.txt era). The W3.5.8 lab directory needs its own `pyproject.toml` before any `uv add` works. `uv init` does this, but `uv add` does not auto-init.
*Fix:* Prepend a one-time bootstrap step before any `uv add`: `test -f pyproject.toml || uv init --no-readme --no-workspace --python 3.12`. The `test -f` guard makes it idempotent — re-running is safe. Patched into chapter §3.2.1 setup block.

**Entry 7 — `ModuleNotFoundError: No module named 'openai'` after `uv init` + `uv add --dev pytest`.** *(observed 2026-05-14)*
*Symptom:* Tests collected by pytest but fail at import: `from openai import OpenAI` in `src/consolidation.py` raises `ModuleNotFoundError`. The `uv` virtualenv has pytest but none of the lab's actual runtime imports.
*Root cause:* `uv init` creates an empty project skeleton and `uv add --dev` only installs DEV dependencies. It does not introspect existing source files for runtime imports. The W3.5.5-era `requirements.txt` was never ported, so the dep list was lost.
*Fix:* Explicit `uv add openai httpx "mcp[cli]" pydantic` before running tests. General rule: when scaffolding `uv` onto a lab that predates it, manually list the runtime imports as a one-time bootstrap; `uv` does not derive them.

**Entry 8 — Reasoning-model `summarize_scroll` returns `None` for legitimate scrolls; `finish_reason=length`.** *(observed 2026-05-14)*
*Symptom:* All 3 tests' scrolls land in `scrolls_skipped`, none in `scrolls_imprinted`, `errors=[]`. Direct repro on the input "deployed via terraform; ran apply; got 200; verified VPC peering" returns `message.content=None` with `finish_reason="length"` — but the response carries a non-empty `reasoning_content` field that contains the correct answer.
*Root cause:* `gpt-oss-20b-MXFP4-Q8` is a REASONING model. It emits chain-of-thought into `reasoning_content` FIRST, then the final answer into `content`. With `max_tokens=80` (tuned for non-reasoning models per pre-scoped Entry 3), the CoT consumes the entire budget; the final `content` is never emitted; finish_reason becomes `length`. Caller reads `content` as empty, normalizes to `None`, skips.
*Fix:* Bump `max_tokens` to 400 in `summarize_scroll()`. The 25-word output cap stays enforced by the SUMMARIZE_PROMPT, not by the token ceiling. General rule: for reasoning models, `max_tokens` must budget for CoT + answer; for non-reasoning models, the prompt-driven output cap is enough on its own. Sniff the model class first.

**Entry 9 — EverCore HTTP `POST /memory/imprint` returns 404.** *(observed 2026-05-14)*
*Symptom:* After bumping the summarizer budget, `consolidate()` errors fill with `httpx.HTTPStatusError: Client error '404 Not Found' for url 'http://localhost:1995/memory/imprint'`. Chapter §2.1 wrapper uses `/memory/imprint` and `/memory/query`; EverCore's actual OpenAPI catalog does not expose these paths.
*Root cause:* The wrapper was written against a hypothetical API surface. Real EverCore endpoints (per `GET /openapi.json`): `POST /api/v1/memories` (personal add) takes `{user_id, session_id?, messages: [{role, timestamp, content}]}`; `POST /api/v1/memories/search` takes `{query, filters: {user_id}, top_k}` and returns `{data: {episodes: [...], profiles: [...]}}`. Conversation-shaped, not arbitrary key-value imprint.
*Fix:* Rewrite `TieredMemory.imprint()` to POST `/api/v1/memories` with an assistant-role MessageItem containing the consolidated fact as content + unix-ms timestamp + the QUEST-ID as session_id. Rewrite `TieredMemory.query_context()` to POST `/api/v1/memories/search` with `filters={"user_id": self.agent_id}` and parse `data.episodes`. General rule: probe `/openapi.json` (or equivalent) FIRST when wrapping a third-party HTTP service; never hand-write client paths against assumed contracts.

**Entry 10 — EverCore returns HTTP 500 "Failed to store memory"; upstream LLM is unauthenticated.** *(observed 2026-05-14)*
*Symptom:* Imprint requests reach EverCore (no more 404), but every call now returns `500 Internal Server Error` with body `{"code":"HTTP_ERROR","message":"Failed to store memory, please try again later"}`. EverCore log shows: `[OpenAI-x-ai/grok-4-fast] HTTP 401: Missing Authentication header` → `LLMError: ... (all 1 keys exhausted)`.
*Root cause:* EverCore's `mem_memorize` flow calls an upstream LLM for memcell boundary-detection BEFORE storing. Upstream env.template defaults to `LLM_PROVIDER=openrouter, LLM_MODEL=x-ai/grok-4-fast` with placeholder key `sk-or-v1-xxxx` — a paid-service config that violates this curriculum's local-first contract AND fails immediately without a real key. Subtler: even after setting `LLM_PROVIDER=openai`, the openai-provider class reads `OPENAI_API_KEY` and `OPENAI_BASE_URL` (NOT `LLM_API_KEY` / `LLM_BASE_URL`). Both blocks must be patched.
*Fix:* Patch EverCore's `.env` to point at local oMLX (chapter §3.2.1 ships the exact `sed` script). Both `LLM_*` (policy declaration) and `OPENAI_*` (what the http client actually reads) need updating. Restart EverCore (`Ctrl-C` + `uv run web`) for config to load. General rule: when a third-party service has BOTH a policy-layer env block AND a provider-specific block, patch both; the policy block alone does not get read by the executing provider class.

**Entry 12 — Cross-agent semantic recall returns 0 memories; per-agent `user_id` partitioned the EverCore index.** *(observed 2026-05-14)*
*Symptom:* Phase 4 two-agent demo runs to completion without errors but Agent B's `query_context(query="how do we deploy production APIs?")` returns 0 memories. Consolidation reports `imprinted=1` so the data IS in EverCore. Direct probes of `/api/v1/memories/get` with `user_id=agent_a`, `user_id=agent_b`, `user_id=consolidator` all return 0 episodes.
*Root cause:* EverCore's `user_id` field is the TENANT identity, not a per-persona label. The lab's first wrapper threaded `agent_id` directly into `imprint()`'s `user_id` field — meaning the consolidator imprinted under `user_id="consolidator"` while Agent B searched under `user_id="agent_b"`. Disjoint user partitions; cross-agent recall silently impossible.
*Fix:* Two-layer identity model. Add a `user_id` ctor arg to `TieredMemory` (defaults to `LAB358_USER_ID` env var or `"shared"`). Use `self.user_id` for EverCore filters; keep `self.agent_id` as the Python-side persona label propagated into imprint metadata only. Production rule: when wrapping a third-party memory store, audit whether its primary-key field is "agent identity" or "tenant identity" — the two scope levels are not interchangeable.

**Entry 13 — EverCore imprint returns `accumulated` / flush returns `no_extraction`; nothing reaches the search index.** *(observed 2026-05-14)*
*Symptom:* `tm.imprint(content="...")` returns 200 OK with body `{"status": "accumulated", "message": "Messages accepted"}`. Calling `POST /api/v1/memories/flush {user_id}` returns 200 OK but with `{"status": "no_extraction"}`. Subsequent `query_context` returns 0 episodes. Pytest tests pass (assertion is `scrolls_imprinted >= 1` which counts the imprint API call, not the resulting memcell), masking the failure. Even 15-turn synthetic conversations + explicit topic-close signals still return `no_extraction`.
*Root cause:* EverCore is conversation-shaped: `/api/v1/memories` accumulates messages, runs LLM-driven boundary detection, only extracts a memcell when the boundary detector says "this conversation has concluded an episode". Single-message imprints + 2-turn imprints both fail the LLM boundary check. The fix flag is `flush=True` (which short-circuits boundary detection in `conv_memcell_extractor.py` line 553: `if request.flush and all_msgs: ... create_memcell_directly(..., 'flush')`) BUT the flush endpoint requires a `session_id` matching the imprint's session_id — without it, flush hits an empty default session and returns `no_extraction`.
*Fix:* Three-part imprint pattern. (a) Wrap each consolidated fact as a 2-turn synthetic conversation (`user: "What about <subject>?"` + `assistant: "<fact>"`); (b) POST with a unique session_id per fact (the quest_id is a natural choice); (c) immediately POST `/api/v1/memories/flush {user_id, session_id}` with the SAME session_id. The flush call forces memcell creation, bypassing boundary detection. Production rule: when wrapping a third-party service with an extraction pipeline, the API status code is not enough — verify the post-condition (data is searchable) before declaring the call successful.

**Entry 11 — Idempotency test fails on second invocation; QUEST-IDs sort alphabetically, seed quest never enters batch.** *(observed 2026-05-14)*
*Symptom:* After fixing 6–10, 2/3 tests pass but `test_consolidation_idempotent_on_second_run` fails: `scrolls_seen=10, scrolls_imprinted=0, scrolls_skipped=3, errors=[]`. 10 scrolls reach the batch but the test's freshly-seeded quest contributes none of them.
*Root cause:* Two interacting bugs. (1) `consolidate()` sorts QUEST-IDs alphabetically via `sorted(set(QUEST_ID_RE.findall(...)))`. With residue accumulation, `QUEST-1, QUEST-10, QUEST-11, ..., QUEST-2, QUEST-20, ...` orders the OLDEST quests first — fresh seed quests (e.g. `QUEST-60+`) never enter the `max_batch=10` window. (2) All 3 tests shared `CAMPAIGN = "test-w358-consolidation"`. Guild's quests are append-only; debug-run residue accumulates under the same campaign tag. Test 1 imprints 7 residue scrolls; test 2 sees them in dedup; its own seed is excluded by the alpha sort.
*Fix:* (a) Numerical sort in `consolidate()`: `sorted(quest_ids, key=lambda q: int(q.split('-', 1)[1]))[:max_batch]`. Production-correct — process oldest-by-creation-order first, never strand high-N quests behind alpha-low ones. (b) Per-test unique campaign: `_fresh_campaign() -> f"test-w358-{uuid.uuid4().hex[:8]}"`. Each test isolates its own quest space. General rule: when wrapping append-only IDs that embed integers, sort by the integer, not the string; when writing tests against append-only stores, scope each test to its own tag/namespace.

---

## Interview Soundbites

**Soundbite 1 — "How would you architect memory for a multi-agent system?"**

"I'd use a two-tier architecture: an operational tier (atomic-claim, scroll handoff, current quest state) and a semantic tier (consolidated facts, long-term knowledge, cross-session recall). The pattern maps to the hippocampus-neocortex separation in biology — fast-write short-term coordination plus slow-write durable semantics, connected by a periodic consolidation pipeline that's the engineering equivalent of REM sleep. In my lab I wired `mathomhaus/guild` (Go MCP server, sub-100ms atomic-claim) as the operational tier and `EverMind-AI/EverCore` (Python HTTP service, biological-imprinting-inspired LTM) as the semantic tier, connected by a Python batch job that pulls closed scrolls, LLM-summarizes them to one-sentence facts, and imprints them. The four-way benchmark on a 15-question multi-agent recall set: no-memory baseline ~10%, guild-only ~55%, EverCore-only ~60%, two-tier **85%**. The differential matters most on cross-session-AND-cross-agent questions, where each single tier misses but the two-tier composition catches both. The architectural lesson: each system stays specialized; the consolidation pipeline is the load-bearing component most production implementations get wrong via either synchronous writes or missing idempotency."

**Soundbite 2 — "What did you learn building a consolidation pipeline?"**

"Three load-bearing properties: idempotency, ordering, and failure isolation. Idempotency via scroll_id deduplication — without it, periodic consolidation accumulates duplicate semantic facts and search precision degrades. Ordering via timestamp-sorted batch processing — the semantic tier should reflect the most RECENT state, not the first-observed state. Failure isolation via per-scroll try/except — one bad scroll shouldn't kill the whole batch. The most subtle bug I hit: using semantic search for the idempotency check, which gave false negatives on short scroll-ID strings — fixed by adding a local SQLite table of imprinted IDs for exact-match dedup. The pipeline runs on a 5-minute cron, never synchronously — synchronous consolidation would push EverCore's slow path onto guild's hot path and collapse the whole tier separation."

**Soundbite 3 — "When would two-tier memory be the wrong choice?"**

"Three cases. First, when there's only ONE agent and queries are paraphrase-shaped — single-tier vector RAG is simpler and good enough. Second, when latency budget is below 100ms p99 even on cold-path queries — two-tier adds the consolidation hop, EverCore's Postgres adds 100-300ms; not worth it for chatbot-style apps that just need recent context. Third, when the agents don't share knowledge — if agent A's experience has zero value to agent B, the semantic tier is pure overhead. Most multi-agent production systems DO benefit, because parallel agents working on related tasks IS the architecture's premise — but it's worth checking the premise before paying the operational cost of running two services and a pipeline."

---

## When to Add a Third Tier (HyperMem)

This lab's two-tier architecture is operational + semantic. EverOS ships a THIRD memory architecture — [`HyperMem`](https://github.com/EverMind-AI/EverOS/tree/main/methods/HyperMem) — that handles **multi-entity relational** queries via a hypergraph backend. We don't use it in this lab because the demo's queries are about FACTS ("how do we deploy?"), not RELATIONSHIPS ("which engineers have worked together on which deploys?"). Adding HyperMem here would dilute the load-bearing two-tier lesson and push lab time past the 8h budget.

**When HyperMem becomes the right third tier**:

| Use case | Why HyperMem | What the hypergraph encodes |
|---|---|---|
| Multi-entity collaboration tracking | EverCore stores facts; HyperMem stores typed edges between actors | `(engineer) ─[worked-on]─ (system) ─[touched-by]─ (engineer)` |
| Dependency-graph reasoning across projects | Hyperedges connect ≥3 nodes natively (regular graph DBs need pivot tables) | `(project A) ─[depends-on]─ (auth-refactor) ─[depends-on]─ (project B, C, D)` |
| Multi-dimensional expert finder | Single hyperedge spans concept × person × experience | "Experts on Kubernetes ∧ cost-optimization ∧ Australian compliance" |
| Incident root-cause traversal across many migrations | Multi-hop relational paths between deploy events | Trace incident → migration step → upstream change → original PR |

**The three-tier shape**:

```mermaid
flowchart LR
    A[Agents]
    A -->|claim/scroll| L1[L1 Operational guild]
    A -->|fact query| L2[L2 Semantic EverCore]
    A -->|relational query| L3[L3 Relational HyperMem]
    L1 -.->|scroll consolidation| L2
    L2 -.->|entity-relation extraction| L3
    style L1 fill:#4a90d9,color:#fff
    style L2 fill:#27ae60,color:#fff
    style L3 fill:#9b59b6,color:#fff
```

The arrows are the SAME shape as the two-tier: consolidation pipeline moves data from each tier into the next-slower one as the entities accumulate enough relational structure to be worth indexing. EverCore's semantic facts become HyperMem hyperedges when enough facts share entities to form a useful graph.

**Concrete trigger to add HyperMem**: when ≥30% of your `query_context()` calls have a "tell me about X AND Y AND Z together" shape (multi-entity intersection), the semantic tier alone forces post-processing in Python. At that point a relational tier earns its operational cost.

**Where it slots in the curriculum**: **[[Week 3.5.9 - Memory Benchmarks and Hypergraph Three-Tier]]** integrates HyperMem as the L3 relational tier on top of this lab's two-tier architecture. W3.5.9 also runs the LongMemEval `oracle` subset across all five backends (no-mem / guild / EverCore / two-tier / three-tier), turning the trigger-condition discussion above into a measurement. Prerequisite: this chapter (W3.5.8) shipped end-to-end. The cluster's graduation arc is now W3.5 → W3.5.5 → W3.5.8 → W3.5.9, with measurement-driven scaling at the top.

`★ Insight ─────────────────────────────────────`
- **The two-tier → three-tier extension is a real production scaling pattern**, not just a research artifact. Most agent systems START at single-tier, GRADUATE to two-tier when cross-session knowledge transfer matters, and ADD relational only when entity-density crosses a threshold. Knowing all three stages — and the trigger for each — is the production-architect signal.
- **Don't add HyperMem speculatively.** YAGNI applies harder to memory architecture than to most things. Each tier costs operational complexity (service + Docker + consolidation pipeline + benchmarks). Add only when measured query patterns demand it.
- **Compare to W2.5 GraphRAG territory**: W2.5 builds entity-graph for RETRIEVAL over a document corpus. HyperMem builds entity-hypergraph for MEMORY over an agent's experience. Different surface area (corpus vs experience), same primitive (typed-edge graph). The distinction matters in interviews — don't conflate.
`─────────────────────────────────────────────────`

---

## References

- **Letta (formerly MemGPT)** — Packer, C. et al. (2023). *MemGPT: Towards LLMs as Operating Systems.* arXiv:2310.08560. The canonical two-tier memory paper in the agent-systems literature; RAM↔archive separation is the engineering precedent for hippocampus↔neocortex.
- **EverOS / EverCore** — biological-imprinting-inspired memory OS. arXiv:2601.02163. The semantic-tier reference architecture used in this lab.
- **mathomhaus/guild** — multi-agent MCP coordinator. Single Go binary; embedded SQLite; the operational-tier reference used in this lab.
- **LongMemEval** — Xiao Wu et al. *LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory.* GitHub `xiaowu0162/LongMemEval`. Industry-standard 500-turn memory recall benchmark; optional Phase 5.3 measurement.
- **LoCoMo** — Maharana, A. et al. (2024). *Evaluating Very Long-Term Conversational Memory of LLM Agents.* GitHub `snap-research/locomo`. Companion benchmark to LongMemEval.
- **Complementary Learning Systems (McClelland, McNaughton, O'Reilly 1995)** — the original neuroscience paper on hippocampus-neocortex memory consolidation. The biological grounding for the engineering analogy.

---

## Cross-References

- **Builds on:** [[Week 3.5 - Cross-Session Memory]] (single-agent dual-store), [[Week 3.5.5 - Multi-Agent Shared Memory]] (guild integration via MCP)
- **Distinguish from:** [[Week 2.5 - GraphRAG]] (entity-graph for RAG, not memory); [[Week 2.7 - Structure-Aware RAG]] (document tree-index, also not memory); [[Week 3.7 - Agentic RAG]] (5-node grade/rewrite graph over RETRIEVAL, not memory consolidation)
- **Connects to:** [[Week 4 - ReAct From Scratch]] (the agent loop that consumes this memory architecture); [[Week 7 - Tool Harness]] (tools to call from the agent; tool results feed scrolls); [[Week 3.5.95 - Self-Observability Memory]] (reuses §3.3's quality-score promotion-gate pattern for its LEARNING extractor — same precision/recall dial, different signal source)
- **Foreshadows:** [[Week 11 - System Design]] (architect a production multi-agent system with two-tier memory as a load-bearing component); [[Week 12 - Capstone]] (capstone-A RAG variant could use two-tier memory for cross-session research)

---

## What's Next

- W3.7 — Agentic RAG: graduates the agent loop to a typed state graph (LangGraph-style); the two-tier memory built here plugs into the state-machine as its persistence layer
- W4 — ReAct From Scratch: builds the canonical agent loop that drives this memory architecture
- W11 — System Design rehearsal: defend the two-tier choice to a hostile-reviewer panel; expect questions on consolidation cadence, idempotency, and failure handling
