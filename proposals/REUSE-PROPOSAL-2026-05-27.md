---
title: "Proposal: Lift Production Patterns from 4 Reference Repos into Curriculum"
created: 2026-05-27
updated: 2026-05-27
lifecycle: TEMPORARY
delete_when: All proposed chapter edits + lab-repo lifts delivered, or proposal rejected
sources:
  - https://github.com/rohitg00/ai-engineering-from-scratch (21.8K stars)
  - https://github.com/kunchenguid/gnhf (1.8K stars)
  - https://github.com/microsoft/AI-Engineering-Coach (1.5K stars)
  - https://github.com/rulyone/Simple-ReAct-Agent (113 stars)
audience: "Curriculum maintainer — yourself"
---

# Reuse Proposal — 4 Reference Repos → Curriculum Improvements

## TL;DR

Studied 4 GitHub repos. Found 7 design patterns to lift into existing chapters + 5 production-grade components to vendor into lab repos + 2 missing chapter topics worth creating. Highest-leverage lift: gnhf's `git.ts` + `orchestrator.ts` (production-quality iterative agent loop with commit/rollback/backoff/exit-summary). Second-highest: repo 4's hand-built ReAct idioms (stop-sequence dual defense, AST-eval `calculate`, error-as-observation). Both are tighter than what the curriculum currently teaches.

## Findings — what each repo gave us

### Repo 1: rohitg00/ai-engineering-from-scratch (21.8K ⭐, Python)

- 453 lessons / 20 phases / multi-language curriculum
- Phase 14 (Agent Engineering) lessons: 07-memory-virtual-context-memgpt / 08-memory-blocks-sleep-time-compute / 09-hybrid-memory-mem0 / 23-otel-genai-conventions / 24-agent-observability-platforms / 30-eval-driven-agent-development
- Code is teaching-style (single `main.py` per lesson), NOT production
- 6-beat lesson shape: MOTTO → PROBLEM → CONCEPT → BUILD IT → USE IT → SHIP IT
- **Useful for taxonomy validation**, not direct code lift

### Repo 2: kunchenguid/gnhf (1.8K ⭐, TypeScript) — HIGHEST LIFT VALUE

- Autonomous overnight agent loop. ralph/autoresearch-style commit-per-iteration with rollback.
- `src/core/` modules (one file + matching `.test.ts` per concern):
  - `orchestrator.ts` (843 LOC) — the main loop with `OrchestratorState` machine + EventEmitter events
  - `git.ts` — shell-injection-safe wrapper (`execFileSync(argv)` not shell strings, `GIT_TERMINAL_PROMPT=0`, `CommitFailedError` class)
  - `interrupt-state.ts` (33 LOC) — pure-function state machine for graceful stop
  - `exit-summary.ts` (237 LOC) — ASCII card with ANSI fallback, structured fields
  - `commit-message.ts`, `telemetry.ts`, `sleep.ts` (exponential backoff), `run.ts`, `debug-log.ts`
- `src/core/agents/` adapter pattern: one file per backend (`claude.ts`, `codex.ts`, `copilot.ts`, `acp.ts`) + `factory.ts` dispatcher
- Production-grade signals: every module has paired test file; sticky `tokensEstimated` flag for honest reporting; `pendingCommitFailure` carve-out (commit fails ≠ iteration fails)

### Repo 3: microsoft/AI-Engineering-Coach (1.5K ⭐, TypeScript)

- VS Code extension reading local AI session logs
- 45 anti-pattern rules across 5 categories: prompt quality / session hygiene / code review / tool mastery / context management
- Rule DSL with editor + interactive playground (`Rule Playground` page with field browser + function catalog)
- 5-card practice score model: severity ratings + concrete actions + example prompts
- **Useful for: anti-pattern catalog + meta-discipline encoding**

### Repo 4: rulyone/Simple-ReAct-Agent (113 ⭐, Python) — TIGHTEST IDIOMS

- 4 files / ~285 LOC total / Ollama + Llama 3.2 3B
- `react.py` (95 LOC) — ReAct loop with several idioms worth lifting
- `tools.py` (95 LOC) — TOOLS dict + AST-eval calculate + token-cheap web_search
- `llm.py` (40 LOC) — one pure function `chat(messages, stop) → text`
- `repl.py` (55 LOC) — multi-turn REPL with `/clear` `/history`
- **Useful for: W4 ReAct chapter idiom tightening**

## Proposed Improvements

### A. Chapter-content lifts (teach IN the curriculum)

| # | Pattern | Source | Curriculum slot | Edit size |
|---|---|---|---|---|
| A1 | **Stop-sequence dual defense** — server-side `stop=["Observation:"]` AND client-side `ACTION_RE` regex | repo 4 `react.py` | **W4 ReAct** §3 mechanism + Phase X code | ~30 LOC + walkthrough block |
| A2 | **Observation-as-user-message (not tool role)** — 2022-paper convention; works on local models that don't honor tool role | repo 4 `react.py` | **W4 ReAct** §2 theory + W4 + local-MLX cross-ref | ~15 LOC prose insight |
| A3 | **Error-as-observation loop-tolerance** — tool exceptions become `Observation: Error from X: <exc>` so model reacts instead of crashing | repo 4 `react.py` | **W4 ReAct** Phase X + new BCJ entry | ~10 LOC code + 1 BCJ entry |
| A4 | **`finish` as sentinel NOT in TOOLS dict** — clean separation of tool-call action vs loop-end action | repo 4 `react.py` | **W4 ReAct** §4 + insight | 1 insight callout |
| A5 | **AST-eval security for `calculate`** — `ast.parse(..., mode="eval")` + whitelisted operator dispatch (NEVER `eval()` on LLM output) | repo 4 `tools.py` | **W4 ReAct** + W11.5 Agent Security checklist | ~25 LOC code + security-warning callout |
| A6 | **Token-cheap tool output discipline** — cap per-result body length to prevent context-window blowup | repo 4 `tools.py` (`_WEB_BODY_CAP=200`) | **W2.7 Tool Harness** + W4 ReAct | 1 paragraph + cap constant pattern |
| A7 | **`OrchestratorState` machine** — explicit state enum + sticky flags + consecutive-failure tracking | repo 2 `orchestrator.ts` | **W11 Production Runtimes** new chapter OR W3.5.8 §10 Production Considerations | New section ~80 LOC + walkthrough |

### B. Production components to vendor into lab repos

| # | Component | Source | Target lab | Effort saved |
|---|---|---|---|---|
| B1 | `git.ts` shell-injection-safe wrapper (port to Python or use as-is in TS labs) | repo 2 `src/core/git.ts` | All labs that automate git commits | ~1 day of debugging shell-quoting + credential-hang bugs |
| B2 | `exit-summary.py` (port from `exit-summary.ts`) — structured session-end card | repo 2 `src/core/exit-summary.ts` | All labs replacing ad-hoc `RESULTS.md` updates | Standardizes "session ended" UX; ~half-day to port |
| B3 | `telemetry.py` token usage accumulator with sticky-estimated flag | repo 2 `src/core/telemetry.ts` | Any lab calling LLMs | Standardizes cost-tracking; ~2 hours to port |
| B4 | `sleep.py` exponential backoff with retry-state | repo 2 `src/core/sleep.ts` | Labs hitting transient errors (oMLX, EverCore, HyperMem timeouts) | Standard backoff pattern; ~1 hour to port |
| B5 | `interrupt_state.py` graceful-stop state machine (33 LOC, trivial port) | repo 2 `src/core/interrupt-state.ts` | Long-running labs (consolidate pipelines, eval runs) | Cleaner than signal handlers; ~30 min to port |

### C. New chapter proposals (gaps in current curriculum)

| # | Proposed chapter | Slot | Source material | Justification |
|---|---|---|---|---|
| C1 | **W11.6 — Production Agent Runtimes** (the gnhf shape: per-iteration commit + rollback + exponential backoff + exit summary + graceful interrupt) | Insert before W12 Capstone, after W11 System Design | repo 2 entire `src/core/` | Curriculum has memory architecture + tool harness + agent loop but NO unified production runner. This is the missing piece. |
| C2 | **W11.7 — Agent Adapter Layer** (run-anywhere agents across Claude Code / Codex / OpenCode / Copilot CLI / Pi via uniform adapter interface) | After W11.6 | repo 2 `src/core/agents/` (acp/claude/codex/copilot/factory) | Multi-client portability matrix in W3.5.8 §9.1 PROMISES this but doesn't ship the adapter layer. C1 + C2 together close that loop. |

### D. Meta-improvements (vault-wide)

| # | Improvement | Source | Effort |
|---|---|---|---|
| D1 | **`ANTI-PATTERNS.md` cross-cutting catalog** — 45-rule shape adapted to agent dev: prompt quality / session hygiene / code review / tool mastery / context management. Living document like BCJ. | repo 3 rule catalog inspiration | ~1 day to write initial 15-20 rules; grows over time |
| D2 | **Chapter authoring sub-beat: `BUILD IT → USE IT`** as explicit per-block discipline. Currently implicit; making it explicit forces "write minimal version first, then library version" cadence. | repo 1 6-beat shape | Single edit to CLAUDE.md authoring rules + retrofit on next chapter |
| D3 | **`scripts/agent-loop-tools/`** — Python ports of B1-B5 as shared utility module, importable across all lab repos | repo 2 lifted ports | ~1-2 days for the full port |

## Sequencing — what to do first

**Sprint 1 (highest leverage / lowest risk):** A1 + A3 + A4 + A5 + A6 — five W4 ReAct chapter idiom tightenings. All small edits, none touch existing infra. ~2-3 hours total. **Why first**: W4 ReAct is the foundation chapter all later agent chapters build on; tightening it now compounds across the curriculum.

**Sprint 2:** B5 + B3 — port `interrupt_state.py` (trivial 33-LOC port) + `telemetry.py` to a shared `scripts/agent-loop-tools/` utility module. Establishes the vendor pattern. ~half day. **Why second**: smallest production-grade lifts; sets up the shared-utility convention for later B-series ports.

**Sprint 3:** C1 — write W11.6 Production Agent Runtimes chapter. Reuses gnhf's `OrchestratorState` shape + commit-per-iteration discipline + exit-summary card pattern. New chapter slot, ~2 days for spec + 1 week for full chapter authoring. **Why third**: requires concentrated authoring time, but unblocks a clear curriculum gap.

**Sprint 4:** D1 — start `ANTI-PATTERNS.md` with first 15-20 entries pulled from observed BCJ entries + cross-cutting curriculum patterns. ~1 day. **Why fourth**: useful but lower leverage than chapter content.

**Defer indefinitely (only if explicit need surfaces):** A2 + A7 + B1 + B2 + B4 + C2 + D2 + D3.

## Per-item detail (Sprint 1 expanded)

### A1 — Stop-sequence dual defense (W4 ReAct)

**Current W4 likely has:** server-side stop only OR client-side parsing only.

**Lift:**
```python
ACTION_RE = re.compile(r"Action:\s*(\w+)\s*\[(.*?)\]", re.DOTALL)

def agent_turn(messages: list[dict], max_steps: int = 8) -> str:
    for step in range(1, max_steps + 1):
        # SERVER-SIDE stop: model halts BEFORE writing "Observation:"
        reply = chat(messages, stop=["Observation:"])
        # CLIENT-SIDE stop: catch stragglers if server stop misses
        thought, action, arg = parse_action(reply)
        # ... dispatch + observation
```

**Insight to add:**
> Belt-and-suspenders defense. Server-side `stop` halts generation BEFORE the model writes `Observation:`. Client-side `ACTION_RE` catches the case where server-side fails (some models / proxies ignore stop sequences). Both defenses together ensure exactly one action per assistant message.

### A3 — Error-as-observation (W4 ReAct + new BCJ entry)

**Lift:**
```python
try:
    observation = dispatch(action, arg)
except Exception as exc:
    observation = f"Error from {action}: {exc}"
messages.append({"role": "user", "content": f"Observation: {observation}"})
```

**Insight to add:**
> Tool exception ≠ loop crash. Convert exception → `Observation: Error from X: <msg>` and feed it back to the model. The model sees the error as observed feedback and can adapt (try different args, switch tools, finish with apology). Crashing the loop on first tool failure is the design smell; loop-tolerance is the production shape.

**BCJ entry:**
> **Entry N — Tool exception crashes ReAct loop instead of feeding back as Observation.**
> *Symptom:* First tool failure (404 from web_search, ValueError from calculate) raises through the loop, ends the user turn with traceback instead of recovered answer.
> *Root cause:* `dispatch(action, arg)` called without try/except. Exception bubbles up past `agent_turn`'s loop boundary.
> *Fix:* Wrap dispatch in try/except; format exception as `f"Error from {action}: {exc}"`; append as Observation. Model sees error as feedback. Loop continues until `finish` or `max_steps`.

### A4 — `finish` as sentinel (W4 ReAct insight callout only)

**Lift insight:**
> `finish[answer]` is NOT in the TOOLS dict — it's a sentinel handled by `agent_turn`'s control flow. Clean separation: TOOLS holds actions that CALL something external; `finish` is an action that ENDS the loop. Mixing them ("finish" as a no-op tool) muddies the dispatcher and breaks token-budget accounting.

### A5 — AST-eval security (W4 ReAct + W11.5 security checklist)

**Lift:**
```python
import ast, operator

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}

def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"unsupported expression node: {type(node).__name__}")

def calculate(expression: str) -> str:
    tree = ast.parse(expression.strip(), mode="eval")
    return str(_eval_node(tree.body))
```

**SECURITY warning callout:**
> **⚠ Never `eval()` LLM output.** `eval("__import__('os').system('rm -rf /')")` is a one-line remote code execution. The LLM controls the expression string; if you `eval` it, you've given the LLM shell access. AST-walk with a whitelisted operator dispatch is the production-safe alternative — supports the math without unlocking arbitrary Python.

Add to W11.5 Agent Security `## Mandatory Security Checks` checklist:
> - [ ] No `eval()` / `exec()` / `compile(..., 'exec')` on LLM output. Use AST-walk with whitelisted ops or a sandbox.

### A6 — Token-cheap tool output (W2.7 + W4)

**Lift:**
```python
_WEB_MAX_RESULTS = 2
_WEB_BODY_CAP = 200

def web_search(query: str) -> str:
    hits = ...
    lines = []
    for hit in hits:
        body = hit.get("body", "")[:_WEB_BODY_CAP].rsplit(" ", 1)[0] + "..."
        lines.append(f"- {hit.get('title', '')}: {body}")
    return "\n".join(lines)
```

**Insight to add:**
> Tool output size is a context-window risk. A verbose `web_search` returning 5KB per hit blows the context within 2-3 iterations. Cap body length at write-time (`_WEB_BODY_CAP`), cap result count at query-time (`_WEB_MAX_RESULTS`), word-boundary truncate (`rsplit(" ", 1)[0] + "..."`). Same discipline applies to ANY tool with variable output: cap at the tool layer, not at the agent layer.

## Effort summary

| Sprint | Items | Effort | Leverage |
|---|---|---|---|
| 1 | A1, A3, A4, A5, A6 | ~3 hours | HIGH (compounds across all later agent chapters) |
| 2 | B5, B3 ports | ~half day | MEDIUM (establishes vendor pattern) |
| 3 | C1 — W11.6 Production Agent Runtimes chapter | ~1 week | HIGH (closes curriculum gap) |
| 4 | D1 — ANTI-PATTERNS.md initial 15-20 entries | ~1 day | MEDIUM |

Total committed effort if all sprints execute: ~2 weeks.

## What's deliberately NOT proposed

- **Lifting repo 1's lesson code**: it's teaching-style single `main.py` per lesson, no production value beyond curriculum taxonomy validation
- **Repo 3's VS Code extension as a whole**: it's an analytics UI, not memory architecture infra
- **Repo 4's DDGS `web_search`**: fine for demos, not production. Real labs need a vetted search API.
- **Full port of gnhf's `orchestrator.ts` 843 LOC**: too heavy for a teaching chapter; C1 distills the SHAPE without the full implementation

## Cross-references to existing vault

- **CLAUDE.md** discipline rules: A5 security check + A6 token-cap rule should land in `~/.claude/rules/common/security.md` or curriculum-local CLAUDE.md
- **Bad-Case Journal.md**: A3 BCJ entry + any A1/A5 surfaces during retrofitting
- **Engineering Decision Patterns.md**: A7 OrchestratorState pattern is a decision pattern worth cataloging
- **`proposals/W3.5.9-PROPOSAL.md`**: shows the proposal-then-execute pattern this file follows; same lifecycle (delete after delivered)

## Decision required from you

Pick one:
1. **Approve Sprint 1 only** — small low-risk wins, defer rest
2. **Approve Sprints 1 + 2** — wins + start vendor pattern
3. **Approve full sequence (1-4)** — ~2 weeks committed
4. **Cherry-pick subset** — tell me which items
5. **Reject** — close proposal, archive lifecycle marker

I'll execute whichever you pick. Default if no instruction: Sprint 1 only (highest leverage / lowest risk / no new chapter authoring required).
