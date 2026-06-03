---
tags: [agent-curriculum, meta-skills, decision-making, working-with-ai, multi-agent, delegation]
created: 2026-04-28
updated: 2026-06-02
---

# Agent Development Patterns — Memory · Retrieval · Multi-Agent · Eval · LLM-Ops

A reusable playbook of **agent-architecture decision patterns** — memory tiers, retrieval pipelines, multi-agent delegation, agent/RAG evaluation, and the LLM-ops to run them. Every pattern is grounded in a **built + measured lab** (W1…W3.5.9, on-disk RESULTS); each cites its source. Built to be reused in later labs (W4+ ReAct, tool harness, system design, capstone) without re-deriving.

> **Scope (refocused 2026-06-02).** This doc was pruned to agent-development domain patterns only. Generic engineering-process discipline (scope-estimate, options-table, verification, etc.) and curriculum-authoring discipline (forward-link panels, spec/disk fidelity, cross-ref invariants) were removed — they were correct but not agent-development knowledge. Pattern NUMBERS are preserved from the original (gaps are intentional) so existing chapter cross-references like `#Pattern 14` still resolve. Build frontier = W3.5.9; nothing below cites an unbuilt chapter as evidence.

---

## How to use this doc

Each pattern: **Rule** (when X → do Y) · **Evidence** (the measured lab behind it) · **Anti-pattern** · **Conditionality** (when it does NOT apply). Skim the names; reach for them by name when designing an agent's memory/retrieval/eval/coordination.

---
## Pattern 13 — Storage-Scale Match (right backend for current scale, no premature scaling)

> Distilled 2026-05-07 from [[Week 2.7 - Structure-Aware RAG#Production Considerations — Storage, Concurrency, Observability]]. Generalizes beyond tree-index — applies to any persistent-state decision (vector indexes, graph data, eval harnesses, agent memory).

**The pattern.** When a system has multiple storage candidates (filesystem / SQLite / Postgres / object store / cache layer), match the choice to the *current* scale, not the *eventual* scale. Build the decision boundary around concrete numbers (doc count, QPS, concurrency, dataset size), not vibes. Three or four scale tiers with explicit thresholds beat one "production-ready" backend that's wrong for both prototype and prod.

**Three-tier template:**

| Scale | Backend | Why |
|---|---|---|
| **Dev / lab / single-user** | Local filesystem (JSON / SQLite / disk file) | Operational simplicity. `git diff` shows changes; full rebuild is one command; zero infrastructure. |
| **Single-tenant prod (10–1,000 units)** | SQLite or Postgres `jsonb` / on-disk index | Concurrent reads. Per-record version history. ACID. No multi-tenancy load yet. |
| **Multi-tenant prod (1,000+ units, multi-user)** | Postgres + S3/blob + Redis cache | Tier the storage by access pattern. Hot in cache, warm in DB, cold in object store. |

**Decision matrix specifics from W2.7 tree-index:**

| Artifact | Property | Storage choice |
|---|---|---|
| `tree.json` (50–100 KB, hierarchical, read-mostly) | Document-shape, indexable JSON | Filesystem → Postgres `jsonb` (with index on `tree -> 'title'` for cross-doc title search) |
| Source PDF (10s–100s MB, immutable, page-range access) | Append-only blob | Filesystem → S3 with byte-range reads + Redis LRU cache for hot ranges |
| Cross-document index | Doc registry | None → SQLite → Postgres |

**Why it works.** A premature production backend forces *every* developer running the lab to bring up infrastructure that has no value at single-user scale (Postgres for one document is theatrical). A premature filesystem backend at 1,000-doc scale destroys concurrency. The match-to-scale decision lets each user pay only for the complexity their scale actually demands. The abstraction seam (in W2.7's case, the `page_provider` Protocol) is what makes scale transitions cheap — same `AgenticTreeRetriever` works against any of the three storage tiers; only the closure around the page fetch changes shape.

**Anti-pattern A — premature production scaffolding.** "We might scale to 100K docs someday, so let's start with Postgres + S3 + Redis." Now every developer setting up the lab needs three services running. The next 6 months of dev time is spent fighting infrastructure for the value of "we're production-ready" — which is fictional value if you have one user.

**Anti-pattern B — locked-in dev simplicity.** Filesystem-only design that has no abstraction seam between storage and the application logic. When you DO need to scale, the lift is a multi-week refactor, not a single closure swap. The fix at design time: introduce the seam (Protocol, callable, ABC) even if the filesystem implementation is the only one shipped. The seam is free; the absence of the seam costs a refactor.

**Anti-pattern C — wrong backend for the data shape.** Common mistake: putting structurally non-vector data (a tree, a graph, an event log) into a vector database because that's the database the project already runs. Vector DBs are for embeddings; trees go in jsonb / document stores; graphs go in graph DBs; event logs go in append-only logs. The blast radius is silent — the system "works" but every read pays JSON ↔ vector conversion overhead and cross-record queries break.

**5-second sanity test before adopting a backend:**
1. **What's the unit of work?** If hierarchical → document store / jsonb; if relational multi-hop → graph DB; if embedding similarity → vector DB; if append-only event → log store; if immutable blob → object store.
2. **What's the access pattern?** Read-mostly per-record vs read-many cross-record; concurrent vs single-writer; hot-tail vs uniform.
3. **What's the concurrency requirement?** 1 reader = file is fine. Multiple concurrent writers = need ACID. Multiple processes reading + occasional writes = SQLite is fine until QPS > ~100.
4. **What's the data size at the upper end of the current tier?** Filesystem fine to ~100 GB; SQLite to ~10 GB; Postgres jsonb to ~1 TB. Above those, scale tier up.

**See also:**
- Pattern 26 — Write-Time Primitive Preserves Signal (the data-shape sanity test feeds the write-primitive choice)
- Pattern 28 — Memory-Tier Graduation (the memory-tier version of match-to-current-scale)
- [[Week 2.7 - Structure-Aware RAG#Production Considerations — Storage, Concurrency, Observability]] — the tree-index storage decision this distills

---

## Pattern 14 — Delegation Contract Template (brief subagents like new hires, not like teammates)

**When it applies:** any time a parent agent spawns a child / worker / subagent / delegate. Codex `Use parallel subagents`, Claude Code `description`-routed subagent, Hermes `delegate_task`, OpenClaw `/subagents spawn`, in-house `crew.kickoff`-style orchestrators — same pattern.

**Failure mode this prevents:** the *single most common* multi-agent failure mode in the wild — "subagents know nothing" (Hermes docs phrase, 2026). A parent agent has the full project context in its head; the child gets only what the parent decides to pass in. Saying `"fix the auth bug"` to a fresh child is the same as DM'ing `"fix the auth bug"` to a new hire on day one. They will guess, and the cost of guessing wrong is paid in token spend, time, AND main-context contamination when the wrong patch comes back.

**The 8-field contract** — fill every field for every delegation, even if the answer is `"none"`:

```text
Role:               you are a <read-only auth explorer | scoped implementation worker | security reviewer | …>
Goal:               what to answer or complete; what the boundary is
Context:            project paths, relevant files, error reproduction, user goal, judgements already made
Allowed actions:    which files readable; can run shell; can write files; can hit network
Ownership:          if writes are allowed, which directories / files are within bounds
Forbidden actions:  do-not-modify list; do-not-refactor list; do-not-ask-user; do-not-spawn-child
Output format:      findings / patch summary / test result / confidence / open questions
Stop condition:     what counts as done; when to stop and report blocked
```

**Why each field is load-bearing:**

- **Role** sets the persona priors. `read-only auth explorer` and `scoped implementation worker` produce different code even with identical Goal + Context.
- **Goal** is the contract. If the parent can't write it in one sentence, the parent doesn't know what it wants — spawning a child won't fix that.
- **Context** is what the child knows. Everything not in Context, the child guesses. Production rule: the child should never have to ask the user a clarifying question; if the parent omitted critical context, that's a parent bug, not a child bug.
- **Allowed actions** + **Ownership** + **Forbidden actions** are the sandbox. They are NOT redundant with each other: Allowed = capability gate (can-it), Ownership = scope gate (where-can-it), Forbidden = explicit anti-goal (don't-do-this-even-though-you-can). Codex's `agents.sandbox` config maps to Allowed; Hermes's `leaf` worker restrictions map to Forbidden.
- **Output format** is the merge contract. If the parent has to free-text-parse the child's response, the parent's reduce phase becomes the new bottleneck. Pre-declare the shape; child returns structured fields.
- **Stop condition** prevents two failure modes: child runs forever because "done" isn't defined; child stops at the first plausible answer because "good enough" isn't defined. Explicit stop conditions also enable retry semantics in durable systems like Hermes Kanban.

`★ Insight ─────────────────────────────────────`
- **The 8 fields ARE the audit log schema.** Compare to the AuditEntry primitive (W3.5.8 §3.4): `actor_agent_id` = Role, `payload_summary` = Goal+Context distilled, `metadata` = Allowed/Ownership/Forbidden/Output, `target_id`+`new_id` = Stop-condition outcome. Write-time contracts and read-time replay are two views of the same data.
- **Filling all 8 fields takes ~30 seconds and saves ~5 minutes per botched delegation.** If a child returns nonsense, look at the contract first: which of the 8 fields was empty or vague? That field is the bug. ~80% of cases will be Context (parent assumed shared state that doesn't exist) or Forbidden (parent didn't constrain blast radius).
- **Topology choice is downstream of the contract, not upstream.** Star fan-out / pipeline / mesh / durable-board don't change whether the contract is needed; they only change how many copies of the contract get written per task. A team-mesh with 4 teammates needs 4 contracts. A solo subagent needs 1. None of them work with 0.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 32 — Metered-Proxy Role-Split (delegating to a metered model needs the same context-passing + a no-persona local fallback)
- [[Week 3.5.8 - Two-Tier Memory Architecture]] §3.4 — AuditEntry primitive (the read-side mirror of this write-side contract)
- `(SPEC)` W4.6 Durable Agent Runtime, W6.5 Hermes — where the topologies that *use* this contract + the "subagents know nothing" maxim live (chapters drafted, labs not yet built)

**Source:** synthesized from Russell (2026), *多智能体协作调查：Agent 到底该怎么分工* — engineering survey of Codex / Claude Code / OpenClaw / Hermes delegation patterns. The 8-field template combines field names used across all 4 systems into one normative shape.

---

## Pattern 22 — Lifecycle Position Matters (early-binding vs late-binding for pipeline primitives)

**When it applies:** any data-processing or AI pipeline where the SAME primitive (summarisation, atomisation, embedding, classification, compression, masking) could plausibly run at multiple stages — write/ingest time, read/query time, or both. Specifically when the primitive is **lossy** and downstream consumers have heterogeneous needs.

**The invariant.** The lifecycle position of a primitive is **load-bearing** — same code, different stage, opposite outcome. Before placing a primitive, ask:

| Question | Early-binding (write-time) wins when… | Late-binding (read-time) wins when… |
|---|---|---|
| Is the consumer's query known? | No (logs, archival) — write-time still works because future queries are uniform | Yes (per-request agent memory) — atomise under the lens of the actual query |
| Is the primitive lossy? | Acceptable: the schema is known and stable | Hazardous: losing detail at write means it cannot be re-derived |
| Queries per memory? | ≪ 1 (log ingestion) — amortise the cost at write | ≫ 1 (agent memory) — pay per query, since writes are rare per memory |
| Error compounding? | Acceptable if downstream stages don't depend on this primitive's output for retrieval | Hazardous: error at write poisons embed → retrieve → compose downstream |
| Schema stability? | Stable, known in advance | Schema-of-interest = the query's own structure (idiosyncratic, late-bound) |
| Can the primitive be upgraded in production? | No — re-ingest required to apply new logic | Yes — change the read-time prompt/model and ALL old memories benefit immediately |

**The math.** Write-time = fixed projection π_write. Read-time = query-indexed family π_query(q). The family always dominates the fixed choice when q is observable, which it is at read time. Same logic as parametric vs hand-tuned models, JIT vs AOT compilation, dynamic vs static dispatch.

**Curriculum instance: W3.5.8 atomisation at write-time destroys signal; at read-time lifts +5pts across the capability range.** §3.2.1's `extract_atomic_facts` invoked as part of `consolidate()` at WRITE time on LongMemEval conversational haystacks: 0/20 correct, conversational facts skipped or paraphrased into tech-flavored summaries. The SAME primitive invoked at READ time (after Qdrant retrieval, before LLM compose) lifted BOTH a 4-bit dense Qwen3.6-27B model (60% → 65%) AND a Claude-Opus-distilled Qwen 27B model (70% → 75%) by +5pts each on the same slice. The architectural primitive is correct; the lifecycle position was wrong for conversational data. See [[Week 3.5.8 - Two-Tier Memory Architecture#5.3.3 Atomisation lifecycle — write-time vs read-time (the deeper §3.2.1 lesson)|W3.5.8 §5.3.3]] for the five-reason decomposition and the data-shape-vs-lifecycle architectural table.

**The discipline.**

1. **Name the lifecycle stage explicitly when describing a primitive.** "Atomisation" is ambiguous; "write-time atomisation" vs "read-time atomisation" are different decisions with different failure modes.
2. **Default to late-binding when query distribution is unknown or heterogeneous.** Most agent-memory and retrieval-augmented systems fit this shape. The intuition that "compress at write to save query cost" is imported from log-processing pipelines and is the wrong default for agent memory.
3. **Bind early only when the schema is genuinely known AND queries are uniform.** Structured durable facts (user preferences, ACID-eligible records) fit this. Conversational episodic data does not.
4. **Test the same primitive at both positions when in doubt.** A/B by environment flag, not by re-architecture. W3.5.8's `ATOMISE_AT_READ=1` flag is the minimal viable ablation harness.
5. **Treat lifecycle position as a tunable parameter, not a fixed pipeline shape.** Different data shapes inside the same system can have different lifecycle policies for the same primitive.

**Anti-pattern: log-processing intuition imported wholesale into agent-memory.** Many "two-tier memory" articles split by storage engine (SQL + vector) and assume write-time compression because that's what log pipelines do. The actual split that matters is **early-bound structured facts vs late-bound retrievable raw**. Same engine could serve both with different lifecycle policies; different engines could serve the same lifecycle. The discipline is the lifecycle choice, not the SQL-vs-vector choice.

**Sub-rule: Authority-Weight Calibration (refinement, added 2026-05-20).** Lifecycle position is necessary but not sufficient. The volume and prominence of derived facts in the consumer's prompt also matter — independently of lifecycle stage. Measured 2026-05-20: constrained read-time atomise (top-K=5 triples, prominently positioned at top of composer prompt, raw context preserved below) collapsed Qwen3.6-27B by −35pts AND Qwen-Opus by −30pts (uniform regression across a 40-pt capability gap). Same lifecycle stage as the successful unconstrained variant — only the volume changed. Compressed derived representations carry per-item authority weight that exceeds the consumer's threshold for overriding via raw context, regardless of model size. Production guardrails:

1. **Minimum-volume floor (K_min ≥ 8).** If extractor returns fewer than K_min triples for a non-trivial input, drop derived entirely; fall back to raw-only.
2. **Deployment calibration gate.** A/B test the deployed extractor: if `composer(raw + facts) ≤ composer(raw alone)`, do not ship — the extractor is poisoning, not helping.
3. **Position discipline.** Raw context FIRST in composer prompts; derived facts LAST with neutral framing. Composers anchor on early-prompt structured content.
4. **Never ship "K most relevant facts" without these guardrails.** The seductive design pattern of "let the extractor pick the 3 most relevant facts" appears frequently in production memory write-ups and is unsafe by construction at any model size when extractor accuracy < consumer trust threshold.

The Bayesian framing: many triples = Bayesian model averaging (errors cancel); few triples = MAP selection (errors fatal). Same math that makes random forests dominate single decision trees. See [[Week 3.5.8 - Two-Tier Memory Architecture#5.3.4 Volume buffers extraction error — the Bayesian framing of why unconstrained atomise works|W3.5.8 §5.3.4]] for the empirical phase transition.

`★ Insight ─────────────────────────────────────`
- **Read-time primitives are iterable in production; write-time primitives are not.** Ship a better atomiser at read-time and ALL old memories benefit immediately. Ship a better atomiser at write-time and only newly-ingested data benefits — old data requires re-ingest. This is the production-ops corollary of late-binding and a strong argument against eagerly compressing data at write time when the read path can absorb the cost.
- **"Where does this primitive belong in the pipeline?" is usually the wrong question.** The right question is "what data shape is being processed, and is its query distribution known at write time?" Lifecycle position is downstream of data-shape commitment, not an independent design choice.
- **The pattern generalises beyond memory.** RAG re-rankers, embedding-time chunking, write-time summarisation, schema-on-write databases, and ahead-of-time compilation all sit in the early-binding family and all break the same way when the consumer's needs are not known in advance. The early-vs-late binding tradeoff is a chapter-level invariant worth keeping at the front of your mind whenever you're placing a primitive in a pipeline.
- **The empirical signature of a lifecycle mismatch**: signal destruction at write time (zero recall on questions whose answers are in the raw input) AND recovery when the same primitive is moved to read time. If you see this signature, suspect lifecycle position before suspecting the primitive itself.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 26 — Write-Time Primitive Preserves Signal (Pattern 22 = *where* the primitive runs; Pattern 26 = *what* it extracts — paired decisions)
- Pattern 30 — New Complexity A/B-Earns Keep (the volume-buffer / K_min sub-rule that refines this pattern)
- [[Week 3.5.8 - Two-Tier Memory Architecture]] §3.2.1 (write-time) ↔ §5.3.3 (read-time + lifecycle decomposition)
- BCJ 2026-05-19 (write-time failure) + BCJ 2026-05-20 (read-time recovery) — the matched-pair empirical record

---

## RAG + Memory Architecture Patterns (domain patterns 23-32)

> **Category note.** Patterns 1-12 are *process/collaboration* discipline; 17-21 are *curriculum-authoring* discipline; this block is **technical-domain** discipline for retrieval-augmented + memory systems — joining the existing domain patterns 13 (Storage-Scale), 15 (Read/Write Mirror), 22 (Lifecycle Position). **Every pattern below is grounded in a built + measured lab** (W1…W3.5.9, all with on-disk RESULTS); each cites its source. Extracted 2026-06-02 to be reusable in W4+ (ReAct, tool harness, system design, capstone) without re-deriving.

### Pattern 23 — Cheap-First Retrieval Ladder (measure each rung before climbing)

**Rule.** Retrieval quality has a cost ladder: dense → +BM25 hybrid → +cross-encoder rerank → +LLM-rerank. Each rung costs ~10× the last. Climb only when the *measured* gap justifies it. **W2: hybrid (BM25+dense) captured ~70-80% of reranking's lift at ~5% of the latency; fp16 was 63% of the reranker speedup.** Start at the cheapest rung that clears your quality bar.
**Anti-pattern.** Reaching for an LLM-reranker first because it's "best," paying 100× latency for a gap a $0 BM25 channel would have closed.
**Conditionality (W2, measured).** Hybrid only *beats* dense on **ceiling-free** benchmarks (BEIR-FiQA: +0.5pp); it ties on saturated ones (MS MARCO recall ≥0.99). And SPLADE++ flipped the hybrid story — the sparse encoder choice matters. Measure on YOUR corpus; benchmark ceiling effects mask real differences. State the latency cost of each rung explicitly.

### Pattern 24 — Structural Index + Faithful-Refusal Contract (don't fabricate from fuzzy matches)

**Rule.** Two paired guards against RAG fabrication: **(a)** retrieve with a *structural/tokenized* index, not substring `CONTAINS` — and **(b)** prompt the reader to answer ONLY from retrieved facts and refuse when they're absent. **W2.5: substring match made "meta" hit metal/metalloid/metabolism → confident chemistry fabrication; a full-text Lucene index + "answer using ONLY the graph facts, else say so" made the LLM correctly refuse** the out-of-corpus "Mark Zuckerberg" query (9 token-overlap hits, 0 Zuckerberg facts → honest refusal).
**Anti-pattern.** Substring/`LIKE %x%` entity matching feeding a reader with no refusal contract → the model dresses noise as an answer.
**Conditionality.** The refusal contract trades recall for precision — on a workload where partial/inferred answers are wanted, soften it. *(Pattern 24b, the refusal half, is also the reader-side guard behind W3.5.9's cloak-framing — frame the reader as an extraction function.)*

### Pattern 25 — The Reader/Composer Is the Quality Lever; Retrieval + Extraction Are Commodity

**Rule.** Spend your strongest model on the **answer step**, a cheap/fast model on extraction. **W3.5.9 probe: the multi-session counting failures were the weak reader (gemma flaked 1↔2 at temp=0), not retrieval — Haiku as reader was stable and lifted every backend; swapping the extraction model among competent locals barely moved accuracy.** The needles were already in the store; the reasoning over them was the bottleneck.
**Anti-pattern.** Burning the capable (metered) model on high-volume extraction while a weak model does the final reasoning — exactly inverted.
**Conditionality.** Holds when retrieval surfaces the answer items at all (a strong reader on empty retrieval honestly returns "0" — that's the tell it's a retrieval problem, not a reader one). *(See Pattern 22 — and W3.5.9 §4.10.)*

### Pattern 26 — Write-Time Primitive Preserves-or-Destroys Signal (distinct from *where* it runs)

**Rule.** Pattern 22 governs *where* a primitive runs; this governs *what* it extracts. **The dimension you erase at write cannot be recovered at read.** W3.5.8: whole-scroll `summarize` SKIPped conversational detail → 0/20; per-message atomic extraction preserved the needles. W3.5.9: a memory that stores user-action facts answers count questions; one that summarizes narrative (qdrant, 0%) loses them. **Corollary — aggregation can live at read-time:** count questions need a deeper retrieval window + an enumerate-then-count reader, NOT a special write-time counting tier.
**Anti-pattern.** Choosing the write-time primitive for storage economy (summarize to save space) when the workload needs the detail summarize discards.
**Conditionality (the load-bearing one).** **User-turn-only extraction is workload-dependent:** it gave 9× S/N on user-centric count questions (W3.5.9) but would LOSE `single-session-assistant` questions where the assistant's recommendation is the answer (W3.5.9 §2.2 refinement). Route the extraction policy by question shape; don't hard-code one.

### Pattern 27 — Router Selects, Ensemble Unions; both can LOSE to the best single backend (RRF is non-monotonic for read-then-reason)

**Rule.** Two ways to combine backends, both with a ceiling — and on a read-then-reason task the simplest single backend can beat both.
- A question-type **router** dispatches each query to one backend → upper-bounded by *best-single-backend-per-axis*, and it only *wins* if (a) its table CONTAINS each axis's winner and (b) it routes each axis to that winner. **W3.5.9: the `hybrid` router scored 75% — 10 pts BELOW the best single backend (`atomic_fact` 85%)** — because its table was built from the design-time PREDICTION ("knowledge-update → 2-tier dedup") that measurement falsified (KU's real winner is atomic_fact's read-time latest-wins reader, 100%, not the 2-tier path, 80%), AND the multi-session winner (`mem0`, 80%) wasn't even in its table.
- An **ensemble** queries multiple backends and **RRF-merges** their retrieved facts (rank-based → fuses heterogeneous score spaces). It does NOT have "no ceiling": **RRF maximizes recall@k of the *union*, but the downstream reader reasons over a *fixed top-k window* — so fusion is NON-MONOTONIC for read-then-reason.** **W3.5.9: the ensemble scored 80% — also BELOW `atomic_fact` 85%.** It tied at the knowledge-update ceiling (100%, ≥ both members ✓) but dropped to 60% on multi-session, below BOTH members (af 70%, mem0 80%): net +1 gain (surfaced a needle af alone missed) −2 loss. Three measured loss mechanisms: **window truncation** (a needle both members kept individually falls out of the fused top-k), **recall dilution** (a low-recall member's facts displace a high-recall member's in the window), **distractor injection** (the union pulls one member's distractors into the other's clean set → over-count).
- **The actual best is a DATA-DRIVEN router** that routes each axis to its *measured* winner (KU→atomic_fact 100%, multi-session→mem0 80%) → **90%**, beating every single backend, the blind ensemble (80%), and the prediction-built router (75%). Also a ceiling, but the correct-and-reachable one.

**Anti-pattern.** Calling an ensemble "combines the best of each, so it can't lose" — it *unions*, and union ≠ improvement when a reader reasons over a fixed window (`three_tier`, a tier-union, fails the same way: 75% < atomic_fact 85%). And: building a router's table from design-time predictions instead of the measured matrix.
**Conditionality.** **Fuse for pure retrieval** (recall@k of the union ≥ either member — genuinely no ceiling there); **route by selection for read-then-reason** (fusion's non-monotonicity bites a reasoning reader). A router beats a single backend only when axes have different winners AND its table contains them AND it routes from measurement, not prediction. *(See W3.5.9 §4.16 for the full per-question accounting.)*

### Pattern 28 — Memory-Tier Graduation Triggers + Null-Result Discipline

**Rule.** Add a memory tier only at its **trigger condition**, and publish the null result when the trigger is absent. **W3.5.9: the L3 graph tier (HyperMem) serves multi-entity *intersection* queries; the slice had none, so `three_tier` (75%) scored as ≈ its atomic-fact L2 — L3 never fired (and the L1+L2 tier-union actually *diluted* it below standalone atomic_fact's 85%).** That null result ("the third tier earns nothing on this workload") is more honest + more useful than a synthetic win. Graduate: 1-tier → 2-tier when you need dedup/supersede; → graph-tier when you need multi-entity relational joins.
**Anti-pattern.** Adding a graph tier speculatively, then reporting it "matches" the cheaper tier as if that validates it — it indicts it (wasted operational cost on this workload). *(Mirror of Pattern 13's "no premature scaling," at the memory-tier level.)*

### Pattern 29 — Eval Integrity (the instrument shapes the result)

**Rule.** A benchmark number is only as trustworthy as the behavior it rewards. Disciplines, all measured:
- **Hold the judge constant** across compared systems (W3.5.8: judge-confound moved every score ≤1pt once fixed).
- **Calibrate dev-set difficulty** — a too-easy set hides differences (W3 Entry 1).
- **Exclude broken golds** — a question whose gold contradicts its own text (W3.5.9 `0a995998`: gold=3 counts a non-store item the question excludes) rewards crude reasoning over correct; quarantine it, don't tune to it.
- **Commitment bias** — golds that score a confident wrong guess and an honest abstention identically reward committing over calibrating (W3.5.8): the benchmark winner may be the worse production choice.
- **Aggregate over single questions** (N=20 → ±10pt; treat the *shape*, not the rank).
**Anti-pattern.** Tuning a prompt to hit one noisy gold; trusting a surprising number without suspecting the instrument first.

### Pattern 30 — New Complexity Must A/B-Earn Its Keep (prompt elaboration can REGRESS)

**Rule.** Every added pipeline stage (HyDE, query expansion, a longer prompt, a reranker, an extra tier) is a hypothesis — A/B it against the simpler baseline before shipping. **W3 Entry 2: a *more detailed* prompt made answers WORSE; Entry 6: HyDE added cost without improving the default pipeline.** W3.5.8: constrained "top-K=5 best facts" extraction collapsed accuracy 30-35pts. More machinery ≠ better.
**Anti-pattern.** Adding HyDE / multi-query / a tier because the literature uses it, without measuring that it beats your baseline on your data.
**Conditionality.** Volume buffers extraction error — *more* (unconstrained) extractions can help where *fewer* "high-confidence" ones poison (W3.5.8 K_min≥8). Counterintuitive: sometimes more-but-noisier beats fewer-but-authoritative (Bayesian model averaging vs MAP selection).

### Pattern 31 — Hand-Roll vs Production Library: A/B on YOUR Data; the Lib's "Failures" Are Often Contracts

**Rule.** Before adopting a memory/RAG library, A/B it against a minimal hand-roll on your own test set. **W3.5: hand-roll scored 15/15 vs mem0 v2 10/14 — but the 4 "failures" were different semantic *contracts* (contradiction archival, episodic/semantic separation), not bugs.** W3.5.9: the homebrew atomic-fact (85%) BEAT the mem0 SDK (75%) outright once the read-time levers (user-turn extraction + count-aware + latest-wins readers) were added — the write-time primitive plus a capable reader carried it past the production library on this slice. **Always test the cheaper hypothesis first** (W3.5: a 1-env-var model-swap, 72s, reframed "mem0 is flaky" → "mem0 has different contracts" — saved hours of wrong-direction patching).
**Anti-pattern.** Adopting the library on its published number, or dismissing it on a single local run, without isolating WHY the gap exists (model? contract? reader?).

### Pattern 32 — Metered-Proxy / Local-Cloud Role-Split (when your "API" is a rate-limited session)

**Rule.** When a capable model is reached through a metered/cloaking gateway (a Claude-subscription proxy, a shared key), treat it as a scarce, quirky resource: **(a) role-split** — high-volume roles (per-message extraction, ~1000s of calls) on a local model, capability-critical low-volume roles (the reader, ~120 calls) on the gateway; **(b) retry/backoff** on cooldown (503); **(c) make the judge non-fatal** — save predictions, rejudge later; **(d) cloak defense** — frame structured tasks as data-extraction (an injected persona will do "extract from these records" but refuse "answer my personal question"), detect residual persona refusals, fall back to a local model. **All measured in W3.5.9 (BCJ 5-7): all-Haiku-via-VibeProxy crashed the eval until the role-split + retry + cloak-fallback made it complete.**
**Anti-pattern.** Routing every LLM call through the metered gateway "for quality" → cooldown 503s mid-run, persona refusals scored as wrong answers, lost imprints.
**Conditionality.** Only relevant when the capable model is gateway-mediated; with a clean API key, just rate-limit politely. The local fallback is the read-side mirror of "the gateway might refuse the write."

## Meta-pattern: How these patterns interact

| Pattern | When in the work cycle | Prevents |
|---|---|---|
| 13 — Storage-Scale Match | Picking a store for retrieval/memory data | Wrong backend for data shape (vector DB for a tree/graph); premature scaffolding |
| 14 — Delegation Contract | Every parent → subagent spawn | "Subagents know nothing" + token-burn from under-briefed workers |
| 22 — Lifecycle Position Matters | Placing a lossy primitive (atomise/summarise/embed) in a memory pipeline | Right primitive at the wrong stage — silent signal destruction |
| 23 — Cheap-First Retrieval Ladder | Choosing retrieval quality vs cost | Paying 100× for a rerank a $0 BM25 channel would match |
| 24 — Structural Index + Faithful Refusal | Entity/keyword retrieval feeding an LLM | Substring-match fabrication; reader dressing noise as an answer |
| 25 — Reader Is the Quality Lever | Allocating models across a RAG/memory pipeline | Capable model on extraction, weak model on reasoning (inverted) |
| 26 — Write-Time Primitive Preserves Signal | Choosing WHAT to extract at write | Erasing a dimension the workload needs; hard-coding one extraction policy |
| 27 — Router Chooses / Ensemble Combines | Building a "hybrid" memory/RAG | Calling a router an ensemble; expecting it to beat its best member |
| 28 — Memory-Tier Graduation Triggers | Adding a tier (2-tier, graph) | Speculative tiers; reporting a "match" as validation not indictment |
| 29 — Eval Integrity | Any benchmark / A-B measurement | Drifting judge, easy dev-set, broken golds, commitment bias, single-Q ranks |
| 30 — New Complexity A/B-Earns Keep | Adding HyDE / multi-query / a tier / longer prompt | Shipping machinery the literature uses without measuring it beats baseline |
| 31 — Hand-Roll vs Library A/B | Deciding to adopt a memory/RAG library | Adopting on published number; dismissing on one run; not isolating WHY |
| 32 — Metered-Proxy Role-Split | Capable model behind a rate-limited/cloaking gateway | All-calls-through-gateway → cooldown crash, persona refusals, lost work |

These patterns compound. The teams (or solo engineers) who use them feel "calm and deliberate" to work with; the ones who don't feel "frantic and surprising." The difference isn't IQ or experience — it's the discipline of slowing down at the right 5-10% of moments.

---

## See also

- [[Bad-Case Journal]] — the empirical failure log these patterns are distilled from (W1…W3.5.9 incidents)
- [[Week 3.5.9 - Requirement-Driven Memory Architecture]] — source of Patterns 25-32 (reader-as-lever, router-vs-ensemble, memory-tier graduation, eval integrity, metered-proxy)
- [[Week 3.5.8 - Two-Tier Memory Architecture]] — source of Patterns 22, 26, 29-31 (lifecycle, write-time primitive, commitment-bias, volume buffers, hand-roll-vs-library)
- [[Week 2 - Rerank and Context Compression]] — source of Pattern 23 (cheap-first retrieval ladder)
- [[Week 2.5 - GraphRAG]] — source of Pattern 24 (structural index + faithful refusal)
- Engineering-process + curriculum-authoring patterns (scope-estimate, options-table, forward-link panels, spec/disk fidelity, …) were removed from this doc on 2026-06-02 to keep it agent-development-focused. They were generic, not agent-specific.

---

— end —
