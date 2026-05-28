---
title: "Proposal: Lift 2026-05 Trend Tools into Curriculum (lab-driven adoption)"
created: 2026-05-28
updated: 2026-05-28
lifecycle: TEMPORARY
delete_when: All proposed labs + chapter extensions + reference adds delivered, or proposal rejected
sources:
  - microsoft/RAMPART (pytest-native safety/security testing)
  - microsoft/SkillOpt (text-space optimizer for skills)
  - microsoft/apm (Agent Package Manager)
  - denoland/clawpatrol (security firewall for agents)
  - NousResearch/hermes-agent (self-improving agent)
  - microsoft/magentic-ui + microsoft/fara (MagenticLite + Fara1.5)
  - GBrain (Garry Tan / Y Combinator — self-wiring memory)
  - perplexityai/bumblebee (supply-chain scanner)
  - workos/auth.md (agent registration protocol)
audience: "Curriculum maintainer — yourself"
---

# Trends-Lift Proposal — 11 Tools → Lab-Driven Chapter Additions

## TL;DR

User approved Tier 1 + Tier 2 + Tier 3 with constraint "better to add labs to use these tools." Delivers 3 NEW chapters (Tier 1) + 5 chapter extensions (Tier 2) + 4 reference adds (Tier 3). Every new chapter / extension includes EXECUTABLE LAB STEPS using the actual tool, not just SPEC pointers. Total estimated effort ~30h.

## Sprint structure (same pattern as PHASE-LIFT)

### Sprint A — Tier 1 new chapters (~12-18h)

- **A1: W6.75 — SkillOpt (Skill Optimization in Text Space)**
  Theory: epochs/batchsize/learning-rate applied to MARKDOWN-as-weights. Lab: clone microsoft/SkillOpt, run on ALFWorld benchmark with frozen Qwen-3 8B locally OR Claude-Sonnet-4.6 via :8317 proxy, observe trajectory-driven edits + validation-gated updates + `best_skill.md` artifact production. Compare optimized skill vs base skill on held-out tasks.
- **A2: W7.6 — Small-Model Agent Stacks (MagenticLite + Fara1.5)**
  Theory: agentic capability from tool orchestration, NOT knowledge alone — small models suffice when training matches inference tool schemas. Lab: install microsoft/magentic-ui locally; load Fara1.5-9B (recommended flagship) via MLX or vLLM; run on Online-Mind2Web subset; benchmark vs Claude-Sonnet baseline on same tasks. Measure tokens/cost/wall-time.
- **A3: W3.5.96 — Self-Wiring Memory (GBrain)**
  Theory: zero-LLM entity extraction via deterministic Markdown parsing + typed edges (attended/works_at/invested_in/founded/advises); HNSW vector + Postgres keyword RRF (83→95% Recall@5 measured). Lab: clone gbrain.homes; ingest 50-page corpus (mix of meeting notes / tweets / emails); verify auto-wired graph; run 10 queries comparing pure-vector vs RRF.

### Sprint B — Tier 2 chapter extensions (~10-15h)

- **B1: W11.5 + RAMPART** — `pytest -k rampart` red-team suite covering 5 attack classes (adversarial / benign failure / harm categories). Lab: `pip install RAMPART`; write 3 RAMPART tests against your existing W7 ReAct agent; measure pass-rate per attack class.
- **B2: W6.7 + apm** — `apm.yml` manifest in your lab repos. Lab: write `apm.yml` declaring skills + MCP server deps; `apm install` against a clean repo; verify all 3 of (Claude Code / Cursor / Copilot CLI) pick up the config.
- **B3: W11.5 + clawpatrol** — wire-level firewall in front of agent. Lab: `clawpatrol gateway config.hcl` with 3 rules (block destructive SQL, pause `kubectl delete`, deny secrets-namespace egress); route W7 agent through gateway; trigger each rule, observe block.
- **B4: W6.65 + WorkOS auth.md** — agent-registration protocol. Lab: write an `auth.md` at `/Users/yuxinliu/Documents/Obsidian\ Vault/Agent\ Development\ Curriculum/auth.md` example (won't deploy; teaches the shape); walk the agent-verified flow vs user-claimed flow.
- **B5: W11.5 + perplexityai/bumblebee** — supply-chain scanner. Lab: install Bumblebee on your dev endpoint; run baseline + project + deep scans; produce inventory of npm + PyPI + MCP configs + browser extensions; cross-check against one synthetic CVE advisory.

### Sprint C — Tier 3 reference adds (~1-2h)

- **C1: W6.5 update for current Hermes** — learning loop + autonomous skill creation + multi-platform gateway + Honcho dialectic user modeling notes.
- **C2: W11.6 references** — Langfuse production pipeline tutorial + TDS Token Burn article.
- **C3: W6.9 references** — HuggingFace Context Course + TDS Control Layer article.

### Sprint D — Meta updates

- **D1: README + curriculum overview** for 3 new chapters (W6.75, W7.6, W3.5.96) and updated extension scope.

## Execution order

Sprint A → B → C → D. Same ordering rationale as PHASE-LIFT: high-leverage first (new chapters), then extensions, then references, then meta.

## Lab-driven adoption — what "use these tools" means here

Each chapter / extension includes:
1. **Install commands** that actually work on M5 Pro / local-MLX target
2. **One concrete lab task** the reader runs against the tool
3. **Verification step** (measurable output: pass-rate, token cost, wall-time, recall@K)
4. **Comparison to baseline** (what was the curriculum-existing approach; what does the new tool change)
5. **Source attribution** inline (repo URL, license, paper citation if applicable)

Labs are SPEC-level for code (~50-100 LOC each) — the heavy lifting is the install + execute + measure + compare cycle, not writing from-scratch implementations.

## Decision required

Already approved (option 1 + lab-driven). Execute now.
