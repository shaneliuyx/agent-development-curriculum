---
title: "Session Wrap-up — Curriculum Expansion 2026-05-27 → 2026-05-28"
created: 2026-05-28
updated: 2026-05-28
lifecycle: REFERENCE — retain as session retrospective
tags:
  - session-wrap
  - retrospective
  - phase-lift
  - trends-lift
audience: "Curriculum maintainer — future self"
---

# Session Wrap-up — Curriculum Expansion 2026-05-27 → 2026-05-28

Two-day intensive session. Two coordinated lift programs (PHASE-LIFT + TRENDS-LIFT) each followed proposal-then-execute pattern with lab-driven adoption + source attribution discipline.

## 1. Scope

**PHASE-LIFT (May 27)** — Deep-research `rohitg00/ai-engineering-from-scratch` (21.8K⭐, 453 lessons across 20 phases). Cross-map vs curriculum's existing ~30 chapters. Identify gaps. Ship 5 new chapters + 7 extensions + 4 references covering Phase 12 (Multimodal) / Phase 13 (Tools/Protocols) / Phase 16 (Multi-Agent) / Phase 17 (Infrastructure) / Phase 18 (Ethics).

**TRENDS-LIFT (May 28)** — Deep-research 11 trending May-2026 tools/articles. Ship 3 new chapters with executable labs + 5 chapter extensions + 4 references covering microsoft/SkillOpt + MagenticLite/Fara1.5 + GBrain (Garry Tan/YC) + microsoft/RAMPART + microsoft/apm + denoland/clawpatrol + perplexityai/bumblebee + WorkOS auth.md + NousResearch/hermes-agent + Langfuse / HF Context Course / TDS articles.

## 2. Commits — git log compressed

PHASE-LIFT thread (curriculum repo):
- `ddb9a0c` W3.5.9 merge (Requirement-Driven + Three-Tier Hypergraph)
- `0df2c81` Diagram LR sweep + 28px fontSize directive
- `80a803f` replay.py complete
- `d16d35b` portability.py complete
- `f049bca` memory_tools.py NEW
- `314c1ad` §8.7 6-branch test
- `3ffe1d7` §9.5 test_phase9.py 15 tests
- `d2e73ff` + `d5820bd` 3-bug fix from real test run → 15/15 PASS
- `c1d577f` W3.5.9 §2.1 bitemporal write-time semantics
- `f3c4125` §3.2 Class 3 title wrap fix
- `269d445` REUSE-PROPOSAL doc
- `5f2cc94` W4 Sprint 1 — repo 4 reference
- `9fab637` (agent-prep repo) Sprint 2 — agent_loop_tools shared module
- `f354688` W4.6 Sprint 3 — gnhf reference
- `4092a7d` Sprint 4 — ANTI-PATTERNS.md seed (20 entries)
- `08773ad` Proposal cleanup

PHASE-LIFT-2 (Tier 1 + Tier 2 + Tier 3):
- `1d175df` Tier 1 — W6.65 MCP Production Transports + W6.95 A2A Protocol
- `7ee690e` Tier 1 cont — W3.5.5.5 Topology + W12.5 Multimodal + W11.55 Provenance
- `bd8b4c4` Tier 2 — 7 chapter extensions
- `bfc8b65` ToC updates for 5 new chapters

TRENDS-LIFT thread:
- `c173736` Sprint A — W6.75 SkillOpt + W7.6 MagenticLite/Fara1.5 + W3.5.96 GBrain
- `3606696` Sprint B — W11.5 7-layer + W6.7 apm + W6.65 auth.md
- `1016971` Sprint C+D — references + ToC updates + proposal rm

**Total commits across both lifts: 24 to curriculum + 1 to agent-prep.**

## 3. New artifacts shipped

### 8 new chapters

| Slot | Title | Source | LOC |
|---|---|---|---|
| W6.65 | MCP Production Transports | Phase 13 #09/15/17 | 226 |
| W6.95 | A2A Protocol | Phase 13 #19 + Phase 16 #12 | 245 |
| W3.5.5.5 | Multi-Agent Topology Patterns | Phase 16 #05/06/10/11/15 | 230 |
| W12.5 | Multimodal Agents | Phase 12 #01-05/20/23/24 | 260 |
| W11.55 | Content Provenance + AI Regulatory | Phase 18 #23/24/25/26/27 | 230 |
| W6.75 | Skill Optimization (SkillOpt) | microsoft/SkillOpt | 245 |
| W7.6 | Small-Model Agent Stacks | microsoft/magentic-ui + fara | 270 |
| W3.5.96 | Self-Wiring Memory (GBrain) | Garry Tan / YC | 270 |

### 12 chapter extensions

W4 ReAct (repo 4 reference) / W4.6 Durable Runtime (LangGraph + gnhf) / W3.5.5 Multi-Agent (Smallville + MAST) / W6.5 Hermes (current features) / W6.6 (no change) / W6.7 Authoring Skills (apm) / W6.65 MCP Transports (auth.md) / W6.9 Context Eng (HF Context Course + TDS Control Layer) / W11.5 Agent Security (bias/fairness/Model Cards + 7-layer defense) / W11.6 Production Tracing (cost-governors + A/B canary + Langfuse + TDS Token Burn) / W11.8 CT MLOps (LoRA primer) / W12.5 / W11.55 cross-link extensions.

### New shared utility (agent-prep repo)

`shared/agent_loop_tools/` Python module:
- `interrupt_state.py` — graceful-stop state machine (33 LOC port from gnhf TS)
- `token_accounting.py` — sticky-estimated flag for honest token reporting
- README + tests (12/12 PASS)
- MIT compatibility with source attribution to kunchenguid/gnhf

### Cross-cutting artifacts

- `ANTI-PATTERNS.md` (NEW) — 20-entry seed catalog across 5 categories (Prompt Quality / Loop Hygiene / Memory & State / Tooling & Dispatch / Production Discipline)
- Mermaid hygiene rules in `CLAUDE.md` (subgraph titles ≤22 chars / `~~~` chaining / 28px fontSize directive)

### ToC updates

- README.md — 8 new one-liners + 4 extension notes
- Agent Development 3-Month Curriculum.md — 8 new index-table rows + 5 extension annotations

## 4. Patterns that worked

1. **Proposal-then-execute** — both lift programs started with `proposals/*.md` declaring scope + TEMPORARY lifecycle + delete_when condition. Forced reassessment (W4 already had 3/5 patterns; W11.6 slot was taken; W4.6 covers most C1 scope). Saved redundant work. Proposal removed after delivery.

2. **Sprint-by-sprint commits** — each sprint ships independently. README/curriculum overview ToC updates happen LAST after all chapters land. Reduces sprawl in any single commit.

3. **Honest TBD marking** — every chapter SPEC has "code lands when lab runs" + every Result line has "TBD pending Phase X-Y runs" markers per user's "no fake measurements" rule. Real measurements only after labs execute.

4. **Source attribution inline** — every lifted pattern names source repo + license + paper/blog URL + cross-link to chapter section. Reader can verify provenance + comply with MIT/Apache 2 redistribution. Survived 25 commits without drift.

5. **Real-execution validation** — TRENDS-LIFT bypassed but PHASE-LIFT W3.5.8 §9.5 test suite REAL-EXECUTED on lab repo → caught 3 chapter bugs in 5.84s. Two iterations of fix (kwarg drift / invented method / pytest-asyncio fixture pattern) → 15/15 PASS. BCJ Entry 20 documents the iteration path honestly.

6. **Reading existing chapters before writing** — repeated discovery: chapters were tighter than proposal estimated. W4 ReAct already had 3/5 idioms. W4.6 already covered "Production Agent Runtimes" scope. W11.6 slot was taken. Reading first prevented redundant chapter authoring. Net effect: smaller deltas + higher leverage per change.

## 5. Open items / unresolved

### Labs not yet executed

Every new chapter ships at SPEC + executable-lab status. Labs have install commands + verification steps but the user hasn't RUN them yet. Each chapter's Result line is TBD until labs run.

Specific labs awaiting execution:
- W6.65 Phase 1-6 (Streamable HTTP server skeleton + Origin validation + SSE replay + gateway)
- W6.95 Phase 1-6 (Agent Card + task lifecycle + AP2 signing)
- W3.5.5.5 Phase 1-6 (5 topology implementations + decision matrix)
- W12.5 Phase 1-6 (CLIP + BLIP-2 + LLaVA + ColPali + multimodal RAG)
- W11.55 Phase 1-6 (SynthID watermark + C2PA + EchoLeak probe + regulatory mapping)
- W6.75 Phase 1-6 (SkillOpt install + SearchQA training run)
- W7.6 Phase 1-6 (Magentic-UI install + Fara1.5 + Online-Mind2Web)
- W3.5.96 Phase 1-6 (GBrain install + corpus ingest + RRF benchmark)

When labs run, replace TBD Result lines + add concrete BCJ entries + fill soundbites with measured numbers.

### Cross-references to verify

8 new chapters add cross-references to existing chapters. Reverse-cross-references in target chapters NOT yet added. Per CLAUDE.md "cross-references must be bidirectional" rule — when adding "Connects to: W6.65" in W6.6, the W6.6 chapter should also reference back. Audit pass needed.

### Index sync

8 new chapters + 12 extensions are reflected in README.md + curriculum overview but NOT yet in:
- `FDE Track - Forward Deployed Engineer Path.md` — may need update for FDE-relevant new chapters (W11.55 regulatory + W6.65 production transports)
- `Engineering Decision Patterns.md` — new chapters may add new decision patterns worth cataloging

## 6. Recommendations for future sessions

1. **Run one lab per session.** Pick a new chapter + execute its full lab + fill TBD measurements. Capture per-lab BCJ entry. This is the highest-leverage next step — chapters convert from SPEC to MEASURED status.

2. **Audit reverse-cross-references.** Half-day pass across the 8 new chapters: for each "Connects to: X" or "Distinguish from: X" in a new chapter, add the reverse link in chapter X.

3. **Keep ANTI-PATTERNS.md alive.** Growth protocol documented at file end. When new BCJ entries surface during lab execution, promote generalized form to ANTI-PATTERNS.md.

4. **Resist the "more chapters" reflex.** Curriculum now has ~40 chapters. Next phase should be DEPTH (lab execution / measured results / chapter polish) NOT BREADTH (more new chapters). Avoid lift-fatigue.

5. **Run TRENDS-LIFT cadence quarterly.** Most TRENDS-LIFT items had ≤30-day publication-to-curriculum-integration time. That's fast. Quarterly trend-research keeps curriculum within 90 days of production state-of-art without becoming a news feed.

## 7. Production-rule summary (what to internalize)

- **Proposal-then-execute** — declare scope + lifecycle BEFORE writing chapters; reassess at proposal time; delete after delivery.
- **Lab-driven adoption** — every chapter's lab phase has install command + verification step + comparison-to-baseline measurement.
- **Source attribution inline** — cite repo + license + paper/blog + chapter cross-link at every lift.
- **TBD over fabrication** — mark Result lines TBD until labs run; never invent numbers.
- **Reading existing chapters first** — prevents redundant authoring + surfaces tighter integration points.
- **Honest iteration in BCJ** — when first fix doesn't work, document WHY + what attempt 2 changed. Iteration discipline is the senior-engineer signal.
- **Mermaid hygiene** — `flowchart TD` default; `LR` only for side-by-side subgraphs; 28px fontSize; ≤22-char subgraph titles; `~~~` chaining for multi-cluster.

## 8. Numerical close

- **8 new chapters** shipped at SPEC + executable-lab status
- **12 chapter extensions** landed across W3.5/4/6/7/11 clusters
- **20-entry anti-patterns catalog** seeded
- **1 shared Python utility** (`shared/agent_loop_tools/`) with 12/12 tests passing
- **25 commits** (24 curriculum + 1 lab repo)
- **~3000 new lines** of curriculum content with full source attribution
- **2 proposal files** created + delivered + removed per TEMPORARY lifecycle

Curriculum now covers May-2026 production landscape end-to-end: MCP production transports + A2A + multi-agent topology + multimodal + content provenance + regulatory + skill optimization + small-model agent stacks + self-wiring memory + 7-layer defense + apm + auth.md. Engineers preparing for Agent/LLM Engineer interviews at enterprise / multimodal / regulated / local-first companies have dedicated chapter coverage for every 2026 interview-frequency topic.
