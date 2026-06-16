---
title: Anti-Patterns to Avoid — Agent Development
created: 2026-05-27
updated: 2026-06-16
tags:
  - anti-patterns
  - cross-cutting
  - meta-discipline
audience: "cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles"
status: SEED — initial 18 entries; grows over time as new failure modes surface
---

# Anti-Patterns — Things NOT to Do in Agent Development

Companion to `Bad-Case Journal.md`. BCJ documents WHAT broke + WHY + FIX after the fact; this file documents PATTERNS to avoid BEFORE writing code. Read both before starting a new chapter or lab.

## Source attribution

Catalog inspired by **[microsoft/AI-Engineering-Coach](https://github.com/microsoft/AI-Engineering-Coach)** (1.5K ⭐, MIT-licensed VS Code extension). Coach maintains a 45-rule anti-pattern catalog across 5 categories — prompt quality / session hygiene / code review / tool mastery / context management — with severity ratings + concrete actions + example prompts. Our agent-dev catalog adapts the shape (severity + symptom + fix) to topics specific to the curriculum's W3.5.x memory cluster + W4 ReAct + W4.6 durable runtime + W11.x production discipline.

Entries derived from observed BCJ entries are marked `(BCJ)` with cross-link; entries derived from cross-cutting CLAUDE.md hygiene rules are marked `(rules)`. Entries are NOT speculative — each one names a real failure mode we've hit (in this lab or in cited reference repos) or a rule with concrete production-anchored justification.

## Severity legend

- **CRITICAL** — silent data loss, security vulnerability, irreversible cost. Always fix.
- **HIGH** — wrong measurements, broken contract, accuracy hit > 5pts. Fix before next commit.
- **MEDIUM** — readability, maintenance debt, paper-tiger discipline. Fix when convenient.
- **LOW** — style, naming, micro-optimization. Optional.

---

## Category 1 — Prompt Quality

### AP-001 — Mixing system-role with user-role inside the same prompt (CRITICAL)

*Symptom:* Caller embeds `system:` instructions inside a `user:` message OR sets a `system` field while a proxy is in the middle.
*Why it fails:* Proxies (CLIProxyAPI / VibeProxy / similar) overwrite the `system` field for OAuth-fingerprint coherence. Caller's instructions silently lost; model responds conversationally instead of following the contract.
*Fix:* User-only payload pattern — no `system` role. Embed contract in the user message. (BCJ Entry 19, W3.5.8 §7.7)

### AP-002 — Asking for JSON without specifying "no markdown fence, no prose" (HIGH)

*Symptom:* `json.loads(response)` fails ~10-20% of the time because model wrapped output in ` ```json ` fence OR prefaced with "Here's the JSON:".
*Fix:* Prompt explicitly says "Output JSON (no markdown fence, no prose):" AND add client-side fence-stripping fallback before `json.loads`.
*Source:* W3.5.8 §8.1 DEDUP_PROMPT + repo 4 `react.py` parse_action's defensive regex.

### AP-003 — Generic "be helpful" framing instead of contract framing (MEDIUM)

*Symptom:* System prompt says "You are a helpful assistant" or similar. Model produces variable-length, variable-format outputs.
*Fix:* Replace with a CONTRACT: "Output EXACTLY one of: <enum>. Schema: <JSON shape>. No prose, no explanation." Production-grade prompts are contracts, not personalities. (W4 Concept 3 — "Prompt 不是人格")

---

## Category 2 — Loop Hygiene

### AP-101 — `except Exception: pass` in the agent loop (CRITICAL)

*Symptom:* Tool call fails → exception caught silently → loop continues with no `Observation` for that step → model has no idea anything went wrong → reasoning derails.
*Fix:* Tool exceptions become Observations: `Observation: Error from {tool}: {exc}`. Model sees error as feedback and adapts. (BCJ candidate, repo 4 `react.py`, W4 Concept 5)

### AP-102 — No max-iteration guard on the agent loop (HIGH)

*Symptom:* Loop runs until cost ceiling hits or terminal kill. No structured exit. Cost spike.
*Fix:* Explicit `max_steps: int` parameter with a default. After max_steps, return `"(stopped: max_steps reached without finish)"`. (W4 Patch 1, repo 4 `react.py`)

### AP-103 — `finish` action handled as a regular tool (MEDIUM)

*Symptom:* `finish` is in the TOOLS dict + dispatcher; loop-end logic muddled with tool-call logic; token-budget accounting wrong.
*Fix:* `finish[answer]` is a SENTINEL handled by the agent_turn control flow, NOT a tool. Clean separation: tools CALL something external; finish ENDS the loop. (repo 4 `react.py`)

### AP-104 — Single-stop-sequence defense (MEDIUM, text-parsing ReAct only)

*Symptom:* Server-side `stop=["Observation:"]` works MOST of the time but model occasionally writes past it (some models/proxies ignore stop). Multi-action messages corrupt scratchpad.
*Fix:* Belt + suspenders — server stop AND client-side `ACTION_RE` regex parse. (repo 4 `react.py`, W4 Concept 1 "Two paths" callout)

---

## Category 3 — Memory & State

### AP-201 — Embedding-based idempotency for short scroll IDs (HIGH)

*Symptom:* Use semantic search to check "did we already imprint this scroll?" → false negatives on short ID strings → duplicate semantic facts accumulate → search precision degrades.
*Fix:* Add a local SQLite table of imprinted IDs for exact-match dedup. Semantic search is for SEMANTIC dedup; exact-match is for IDEMPOTENCY. Different problems. (W3.5.8 Interview Soundbite 2)

### AP-202 — Bitemporal write-time prediction of `valid_to` (HIGH)

*Symptom:* Schema requires `valid_to` at write time; engineer tries to predict when fact will stop being true; chooses arbitrary horizon (1 year? 1 month?); facts age out incorrectly.
*Fix:* `valid_to = None` (open-ended sentinel) at write. When contradicting fact arrives, supersede pipeline finds prior + patches `valid_to = now()` + writes new with `valid_from = now()`, `valid_to = None`. (W3.5.9 §2.1 bitemporal block, W3.5.8 §8.6)

### AP-203 — Dual-write reconciliation between memory tiers (HIGH)

*Symptom:* Write fact to L1 atomic-fact store AND L2 episodic store synchronously. Reconciliation contract between them = production fire.
*Fix:* Single-write + smart-read. Write once to the canonical tier; reads route by question shape. (W3.5.9 §2.3 router patterns, W3.5.8 §3 consolidation)

### AP-204 — Per-test residue in shared collection name (HIGH)

*Symptom:* All tests share `lab358_memories` collection in Qdrant. First test's writes pollute second test's assertions. Matrix scrambled.
*Fix:* Per-test uuid-suffixed namespace: `f"af_{uuid.uuid4().hex[:8]}"`. (BCJ Entry 14, W3.5.8 §7.5)

### AP-205 — Auditing reads (HIGH)

*Symptom:* `memory_query` emits AuditEntry per call. Read-heavy workload blows audit log size 10× without informational gain. Replay becomes slow.
*Fix:* Asymmetric audit policy — writes audit, reads don't. Same convention as Kafka / WAL. (W3.5.8 §9.1.1 memory_tools, AuditEntry contract)

---

## Category 4 — Tooling & Dispatch

### AP-301 — `eval()` on LLM-generated expressions (CRITICAL)

*Symptom:* `calculate` tool does `eval(llm_output)`. LLM controls the string. RCE via `__import__('os').system('rm -rf /')` is a one-line attack.
*Fix:* AST-walk with whitelisted operator dispatch. `ast.parse(expr, mode="eval")` + walk + reject any non-numeric / non-whitelisted node. (repo 4 `tools.py`, W11.5 Security checklist)

### AP-302 — Variable-length tool output without caps (HIGH)

*Symptom:* `web_search` returns 5KB per hit. Context window blows in 2-3 iterations. Reader LLM truncates mid-evidence.
*Fix:* Cap at tool layer: `_WEB_MAX_RESULTS = 2`, `_WEB_BODY_CAP = 200`. Word-boundary truncate so output stays clean. (repo 4 `tools.py`)

### AP-303 — Tool dispatch via dict-of-functions without docstring source (MEDIUM)

*Symptom:* `TOOLS = {"calculate": calculate, "web_search": web_search}`. Adding a tool also requires editing the system prompt's tool list. Two-write rule violated.
*Fix:* `TOOLS: dict[str, tuple] = {"calculate": (calculate, "calculate[expr] - eval math expr")}`. Add tool = ONE entry. System prompt's tool list auto-generates via `docs()`. Single source of truth. (repo 4 `tools.py`)

### AP-304 — Shell-string git commands inside agent automation (CRITICAL)

*Symptom:* `subprocess.run(f"git commit -m '{message}'", shell=True)`. LLM-controlled message contains `'`, `$`, `;` → shell injection. Or hangs forever on credential prompt.
*Fix:* `execFileSync` / `subprocess.run([list, of, args], shell=False)`. Set `GIT_TERMINAL_PROMPT=0` to prevent credential hangs. (gnhf `src/core/git.ts`, lifted to W4.6 §8 references)

### AP-305 — Assuming tool calling works without probing the model × server-parser pairing (HIGH)

*Symptom:* Valid `tools=` + `tool_choice="auto"` sent, schema correct, but `message.tool_calls` is empty and the call sits in `content` as `<tools>`/`<function>`/`<tool_call>` text. The same model "supports tools" on a different server. On oMLX, `Qwen2.5-Coder-{7B,14B}` fail on **both** the OpenAI and Anthropic surfaces; Gemma / Qwen3 / gpt-oss pass.
*Fix:* Tool calling is a model × server-*parser* pairing, not a model property — probe the pairing, never the model alone, and re-probe on every engine upgrade (an upgrade can flip a tool score with no model change). Prefer a parsed family; or recover client-side with `extract_text_tool_calls()` before reading `tool_calls`. (BCJ 2026-06-15 W4, repo 4 `scripts/probe_fleet.py`)

### AP-306 — Routing a reasoning-distilled model to a format-sensitive role (HIGH)

*Symptom:* A reasoning-distilled model scores `tool=1.00` but `json=0.00` / `instr=0.00` — "return only JSON" comes back as prose or clipped, "exactly N words" comes back empty. The `<think>` block consumes the `max_tokens` budget before the answer.
*Fix:* Route format-sensitive roles (json_extractor / compose / strict-instruction) to a non-reasoning model; or suppress thinking (`enable_thinking=false` / `reasoning_effort=low`) and re-probe. Reserve reasoning-distilled models for raw `tool_calls` emission, where the structured field is unaffected. (BCJ 2026-06-15 W4 + 2026-04-30 W2.5, repo 4 `src/models.py`)

---

## Category 5 — Production Discipline

### AP-401 — Reporting estimated tokens as exact (HIGH)

*Symptom:* Adapter doesn't emit `usage_update` (ACP protocol, some local-MLX endpoints). Caller's token counter accumulates message-byte estimates AS IF exact. Cost report wrong by 20-40%.
*Fix:* Sticky `tokens_estimated` flag. Once any iteration reports estimated, the WHOLE run's totals are estimates. Exit summary prefixes with `~`. (gnhf `OrchestratorState.tokensEstimated`, ported to `agent_loop_tools/token_accounting.py`)

### AP-402 — Synchronous consolidation in the hot path (HIGH)

*Symptom:* Agent calls `consolidate()` immediately after each scroll close. Semantic-tier slow path bleeds into operational-tier hot path. Per-request latency 10×.
*Fix:* Consolidation on a cron OR event-triggered batch — never synchronous. Operational tier stays fast; semantic tier stays correct. (W3.5.8 Interview Soundbite 2)

### AP-403 — Optimizing for benchmark without measuring vs published baseline (HIGH)

*Symptom:* Lab tunes prompt + model + retrieval until LongMemEval score is 65%. Doesn't measure published Mem0 (94.4%) or EverCore (83%) baselines on the same slice.
*Fix:* Pareto-frontier discipline — measure-vs-published-baselines is the senior signal. Score is meaningless without the comparison. (W3.5.9 §2.8 Measuring vs optimizing)

### AP-404 — Fabricated measurements in chapter / commit / soundbite (CRITICAL)

*Symptom:* Chapter draft includes "Result: 14/20 PASS in 4.2s" before the test has been run. Soundbite cites a number that came from estimation, not measurement.
*Fix:* Always mark TBD until measured. Once measured, replace with the actual `pytest --durations` output or `RESULTS.md` row. Per the curriculum's real-data discipline, only OBSERVED entries are load-bearing for interview soundbites. (BCJ provenance preamble convention)

### AP-405 — A benchmark cap that converts a correctness test into a brevity test (HIGH)

*Symptom:* A known-capable model scores implausibly low on an eval (e.g. `reason=0` for a model that clearly does the arithmetic); the score is unstable run-to-run and downstream selection logic flip-flops. Root: the probe's `max_tokens` is too small, so a verbose-but-correct model gets clipped (`finish_reason="length"`) before emitting the graded token. The metric silently measures terseness-under-cap, not the property it claims to.
*Fix:* Size each probe's token cap to the property under test — generous for reasoning/derivation (correctness), tight only where brevity IS the property (json-only, exact-word-count). When a score looks wrong for a capable model, check `finish_reason` before blaming the model. Re-baseline after the fix. (BCJ 2026-06-15 W4 "Probe token-cap manufactured a false reason=0"; repo 4 `scripts/probe_fleet.py::probe_reasoning`)

### AP-406 — Split status + event writes in a durable state machine (HIGH)

*Symptom:* A node is marked `done` in the `nodes` table but its `done` event never lands in the log — a crash (or exception) between the status `UPDATE` and the event `INSERT` leaves live state and audit trail disagreeing, and a downstream forensic count is silently off by one. Nothing errors; the divergence only shows when you cross-check the two.
*Fix:* Wrap the status update, the event append, and any dependent state promotion (`PENDING→READY`) in ONE transaction (`with self._connect() as conn:`) so they commit together or not at all. Generalizes to any system pairing a live state field with an append-only log of changes (outbox, CDC, workflow engines, double-entry ledgers): split writes drift under crash. (W4.6 `graph_store.py::mark_done` — designed-against; not yet observed, the bench never crashed mid-write.)

### AP-407 — In-memory retry counter in a restartable runtime (HIGH)

*Symptom:* A node that fails validation retries, the process restarts mid-run, and the node's attempt budget is back to zero — the classic AutoGPT infinite-cost retry storm. A `while attempts < N` loop in process locals does not survive `kill -9`, so every restart re-grants the full budget and a permanently-flaky node burns unbounded cost.
*Fix:* Persist the retry counter in durable state (`nodes.attempts` column), bump it at claim time, and read it in `mark_failed`: terminal `FAILED` at `attempts >= max_attempts`, else requeue `READY`. A counter that was never in memory cannot be reset by a restart. (W4.6 `graph_store.py` durable `attempts` — designed-against; the bench ran zero retries so the storm never fired.)

### AP-408 — Cost-meter row keyed by event, not by unit of work (HIGH)

*Symptom:* A node that failed once and succeeded on retry writes two `node_cost` rows; the run's `cost_report` over-reports tokens and cloud-equivalent USD versus the work actually done. Without an idempotency key tied to the unit of work, every retry inserts a fresh row (the AutoGPT Platform `cost_tracking.py` early-commit failure mode).
*Fix:* Key the cost row to the unit of work, not the wall-clock event: `node_cost` carries `UNIQUE(run_id, node_name, attempt)` and the meter writes with `INSERT OR IGNORE`, so re-recording the same `(node, attempt)` is a deliberate no-op. The ledger stays correct under retry — the exact failure the runtime is built to survive. (W4.6 `cost_meter.py` — designed-against; not separately observed because the bench ran zero retries.)

### AP-409 — Multi-scheduler cron without a single-scheduler invariant (HIGH, multi-host — deferred to W11.5/W12)

*Symptom:* A cron-registered graph starts two runs per tick after a restart; an operator sees duplicated work and doubled cost with no error. Without leader election or an idempotency key, a restart can leave a zombie timer running alongside the new one (the APScheduler / classic-AutoGPT scheduler-duplication mode).
*Fix:* Leader election (one scheduler owns the cron lease) or an idempotency key on `(graph_id, tick_bucket)` so a duplicate tick is a no-op `start_run` — the same unit-of-work-keying discipline as AP-408. Out of scope for a single-host lab: W4.6 ships one in-thread `threading.Timer` per graph with an idempotent `stop_cron`, so duplication only arises in the multi-host deployment deferred to W11.5/W12. (W4.6 `scheduler.py` — designed-against; never observed, single-host by construction.)

---

## How this catalog grows

New entries land when:
- A new BCJ entry surfaces a pattern that's not chapter-specific (e.g., applies across W4 / W3.5.8 / W11.x) → promote a generalized version into ANTI-PATTERNS.md
- A reference repo (rohitg00/ai-engineering-from-scratch, kunchenguid/gnhf, microsoft/AI-Engineering-Coach, rulyone/Simple-ReAct-Agent, or future additions) demonstrates a pattern by absence (their code shows the right way; the wrong way becomes an anti-pattern entry)
- A code-review pass on a chapter or lab catches a recurring issue → encode it here so future chapters skip the rediscovery cost

When an entry lands here, also:
1. Cross-link the source BCJ entry (if applicable) so the abstract anti-pattern has a concrete observed instance to point at
2. Add a one-line note to the relevant chapter's §9 Cross-References (`Distinguish from:` or `Connects to:` block) so chapter readers see the anti-pattern when they read the chapter
3. Bump `updated:` in this file's frontmatter

## Cross-references

- **`Bad-Case Journal.md`** — observed-instance journal; each entry here may have one or more BCJ entries as its concrete examples
- **`Engineering Decision Patterns.md`** — companion file cataloging DECISION patterns (e.g., when to dual-write vs single-write); this file catalogs ANTI-patterns (what NOT to do)
- **`CLAUDE.md`** — vault-wide editorial discipline rules; some anti-patterns here are encoded as positive rules there (e.g., AP-404 fabricated measurements → CLAUDE.md "no fake measurements" rule)
- **`proposals/REUSE-PROPOSAL-2026-05-27.md`** — source proposal that kicked off this catalog (D1 deliverable from Sprint 4)
