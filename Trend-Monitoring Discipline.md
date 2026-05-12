---
title: Trend-Monitoring Discipline
created: 2026-05-12
updated: 2026-05-12
tags:
  - meta
  - process
  - continuous-learning
  - curriculum-maintenance
audience: Curriculum maintainer (Yuxin / future contributors). Companion to the curriculum overview; complements Appendix G (Continuous Learning System) with the *trend-monitoring* slice specifically — keeping the curriculum current with 2026+ technical trends without emergency rescue audits.
stack: ~30 min / week skim cadence + quarterly triage; no tooling required beyond a markdown file (this one) and the six signal sources below.
---

# Trend-Monitoring Discipline

## Why this file exists

The 12 May 2026 audit of the teach_fireworks 11-section AI Engineer reading list surfaced three production-LLM-infra gaps the curriculum had not closed (prompt caching, cost attribution, provider routing). The audit took 4 hours and produced W7.3 + reference adds across 7 chapters. **That kind of audit should not be necessary every 6 months.** This file documents the ongoing discipline that prevents trend drift: 30 min/week of skimming, weekly Inbox entries, quarterly triage into chapter integration.

This file is the *process* companion to the curriculum overview's *content*. Appendix G (Continuous Learning System) in the overview covers the *learner's* continuous learning (~15 min/day flashcards, weekly paper reads, weekly bad-case journal). This file covers the *curriculum maintainer's* trend monitoring — they are different cadences with different consumers.

---

## The Six Signal Sources

### 1. Hiring-rubric drift (X / Twitter)

| Account | Why | Cadence |
|---|---|---|
| [@akshay_pachaar](https://x.com/akshay_pachaar) | Author of the 6-area rubric this curriculum maps onto. New "area" additions or list reshuffles are direct signals for chapter scope. | Weekly skim |
| [@teach_fireworks](https://x.com/teach_fireworks) | Curated source-material expansions of the 6-area framing. The 11-section reading list (May 2026) was the trigger for W7.3. | Weekly skim |
| [@hwchase17](https://x.com/hwchase17) | Harrison Chase (LangChain) — surfaces tools 2-4 weeks before mainstream when LangChain integrates them. | Weekly skim |
| [@hamelhusain](https://x.com/hamelhusain) | Hamel Husain — LLM-as-judge + eval discipline; the canonical practitioner source. | Weekly skim |
| [@sh_reya](https://x.com/sh_reya) | Shreya Shankar — eval + production-LLM observability; surfaces failure-mode papers. | Weekly skim |
| [@eugeneyan](https://x.com/eugeneyan) | Eugene Yan — applied-ML + LLM patterns; weekly newsletter is a compounding source. | Weekly newsletter |

### 2. New papers (arxiv-sanity + Papers With Code + HuggingFace daily)

- **arxiv-sanity-lite** (`arxiv-sanity.com`) filtered for `cs.CL` + `cs.LG` with keywords `llm serving`, `agent`, `kv cache`, `quantization`, `speculative decoding`, `evaluation`. Weekly skim — new SOTA in inference optimization lands here first.
- **HuggingFace Papers** (`huggingface.co/papers`) — daily-curated paper highlights with discussion threads. New benchmark releases (LongMemEval-v2, etc.) land here before academic publication.
- **Papers With Code** (`paperswithcode.com`) — benchmark leaderboard movements. When SOTA on a benchmark you cite shifts >5%, the chapter's number is stale.

### 3. Gateway + framework changelogs (production tooling)

| Project | Why | Cadence |
|---|---|---|
| LiteLLM (`github.com/BerriAI/litellm/releases`) | Gateway pattern primitives evolve fast — new providers, new routing strategies, new caching backends quarterly. | Monthly skim |
| Portkey (`portkey.ai/changelog`) | Direct competitor to LiteLLM; convergent feature set is the signal of "production pattern crystallizing." | Monthly skim |
| LangSmith (`docs.smith.langchain.com/changelog`) | Eval + observability standard for the LangChain ecosystem. New eval primitives → W3 update candidates. | Monthly skim |
| Phoenix (`docs.arize.com/phoenix/release-notes`) | OSS observability used in W3. | Monthly skim |
| GPTCache (`github.com/zilliztech/GPTCache/releases`) | Semantic-cache reference impl; new similarity functions = W7.3 update candidates. | Quarterly skim |

### 4. Provider feature drops

| Provider | What to watch | Cadence |
|---|---|---|
| Anthropic (`anthropic.com/news` + `docs.anthropic.com`) | New Claude versions, prompt-caching changes, Agents SDK, MCP server updates. Cache breakpoint changes have direct W7.3 impact. | Weekly skim |
| OpenAI (`openai.com/blog` + `platform.openai.com/docs`) | Structured Outputs evolution, Agents SDK, cached_tokens telemetry changes. | Weekly skim |
| Google AI / DeepMind (`deepmind.google/discover/blog`) | Gemini API surface changes; long-context advances. | Monthly skim |

### 5. arxiv-sanity LLM-serving filter (separate from papers)

Specifically: papers on **inference optimization** (PagedAttention descendants, KV-cache compression, speculative decoding variants, quantization-aware fine-tuning). The 2025-2026 SOTA churn rate here is high; once a quarter, sweep the latest 50 papers and flag candidates for W0/W2.7/W9.5 references.

### 6. Benchmark publications

- **LongMemEval** (`github.com/xiaowu0162/LongMemEval`) — anchored to W3.5.9; watch for v2.
- **FinanceBench** (`arxiv.org/abs/2311.11944`) — anchored to W2.7; watch for variants.
- **MS MARCO + BEIR + MTEB** — anchored to W1; watch for evaluation methodology updates.
- **MT-Bench + Chatbot Arena** — anchored to W2.7 + W3 + W3.5 + W9 judge discussions; watch for new judge-bias studies.

---

## The Weekly Cadence (~30 min)

```
Monday morning:
  10 min — X skim (sources 1 + 4)
  10 min — RSS / changelog skim (sources 3)
  10 min — arxiv-sanity + HF papers skim (sources 2 + 5)

If something looks load-bearing → drop into Inbox below.
If nothing surfaces → done in 30 min, no Inbox entry that week.
```

The discipline rule: **time-box the 30 min**. Trend-monitoring expanding to 2 hours every Monday is its own anti-pattern. The Inbox is for *promising signals*, not for *exhaustive coverage*.

---

## The Quarterly Triage

End of every calendar quarter:

1. **Read the Inbox** end to end.
2. **Sort each entry** into one of four buckets:
   - **Integrate** — citation worth adding to a specific chapter's References / Theory Primer.
   - **New chapter** — substantial enough to warrant its own supplemental (decimal week, e.g., W7.3 was born from one such entry).
   - **Watch** — interesting but not yet load-bearing; leave in Inbox another quarter.
   - **Drop** — superseded, debunked, or proven non-load-bearing.
3. **Apply Integrate items** — touch the chapters, commit.
4. **Plan New-chapter items** — draft scope, schedule writing time.
5. **Move Watch items** to "Watching" section below; clear Drop items.

Past quarterly triages get a dated summary entry under "Audit History" below.

---

## Inbox (current — weekly entries land here)

> Add entries below this line. Format: `**YYYY-MM-DD** — [Source] → [What] → [Why it matters] → [Candidate target chapter]`

**2026-05-12** — [yzddp/harnesscode audit] → **State-file blackboard + numbered priority decision table for multi-agent control flow** → Agents communicate via JSON state files on disk; an Orchestrator reads them and applies a fixed priority table (init missing → human-block → test-fail → review-fail → next-pending → tester → reviewer → done) to pick the next agent. Decouples role logic from control flow. Three other patterns from the same audit (idle watchdog / false-completion gate / typed-error envelope / structured human-handoff) were directly integrated into W7 + W7.3; this one is held over because it is **multi-agent architecture, not harness pattern** — wrong fit for W4 (single-agent), partial fit for W3.5.5 guild (which solves the same problem via SQLite atomic-claim instead of JSON blackboard). Candidate target: future supplemental on "Blackboard vs Atomic-Claim vs Message Queue for multi-agent coordination" — or absorb into W3.5.5 as a "Distinguish from" callout next time that chapter is touched. Watch quarter: 2026-Q3.

---

## Watching (held over from prior triages — not yet load-bearing)

*(Empty as of 2026-05-12.)*

---

## Audit History

### 2026-05-12 (later same day) — yzddp/harnesscode pattern audit

**Trigger:** User-suggested cross-reference review of `github.com/yzddp/harnesscode` for transferable harness patterns.
**Method:** Forked research agent fetched repo via WebFetch; skimmed README + 5-agent state-file pipeline (Orchestrator / Initializer / Coder / Tester / Fixer / Reviewer); scored 5 candidate patterns against existing W4 + W7 + W7.3 coverage; filtered patterns we already have.
**Findings:** 5 transferable patterns surfaced. 4 directly integrated (3 into W7 BCJ Entries 2-4, 1 into W7.3 Production Considerations). 1 parked in Inbox (above) for future multi-agent chapter.
**Actions taken:** W7 BCJ Entries 2-4 added (idle-timeout watchdog / false-completion verification gate / typed-error envelope with routing discriminator) + harnesscode reference. W7.3 Production Considerations addendum (structured human-handoff via missing_info pattern) + harnesscode reference. Trend-Monitoring Inbox entry for state-file blackboard pattern.
**Time spent:** ~30 min audit (forked agent) + ~25 min integration.
**Process learning:** A *single source* triage (one repo) is the right shape for the weekly skim — it took 55 min total. The 4-hour inaugural audit was an 11-source bulk triage. The two cadences (per-source weekly skim vs. bulk-list quarterly audit) need different time budgets; both belong in the discipline.

### 2026-05-12 — Inaugural 11-section audit

**Trigger:** teach_fireworks 11-section AI Engineer reading list (X post by @teach_fireworks).
**Method:** ghost-os MCP read of both X posts (parts 1–5 + parts 6–11); coverage map of 11 sections vs 12-week curriculum; 3-tier action plan.
**Findings:** 3 STRONG matches (sections 1, 5, 6 — covered by W4, W8, W3/W2.7), 5 PARTIAL matches (sections 3, 4, 8, 9, 11 — covered indirectly), 3 GAPS (sections 2, 7, 10 — all production-LLM-infra).
**Actions taken:** Tier A = reference adds to W0, W2.7, W3, W3.5, W4, W8, W9 (7 chapters, 18 new references). Tier B = W7.3 new chapter ("Production LLM Infrastructure") covering the 3 gaps via 6 lab phases. Tier C = curriculum-overview cross-cutting "Production Infrastructure" track + Akshay 6-area mapping table + both READMEs updated.
**Time spent:** ~4 hours.
**Process learning:** Auditing reactively at "I noticed a gap" is expensive — 4 hours quarterly is structurally cheaper than 4 hours of emergency rescue. This file is the discipline rule that converts emergency audits into scheduled triage.

---

## What this file is NOT

- **Not a paper-reading log.** That's the learner's job (Appendix G in the curriculum overview).
- **Not a daily firehose.** 30 min/week — anything more is its own anti-pattern.
- **Not a chapter-rewrite tracker.** When a chapter needs a rewrite, that lives in the chapter's own commit history.

This file is **the maintainer's input queue for keeping the curriculum current**, period.

---

## References

- **Pachaar, Akshay (2026).** *The Six Areas an AI Engineer Must Master.* X / @akshay_pachaar. The hiring-rubric framing the inaugural audit measured against.
- **teach_fireworks (2026).** *The AI Engineer 11-Section Reading List.* X / @teach_fireworks. The curated source list that triggered the inaugural audit.
- **Karpathy, Andrej (2025).** *Context engineering: the delicate art of filling the context window with just the right information.* X / @karpathy. The framing that prevents trend monitoring from expanding into trend obsession.

---

## Cross-References

- **Builds on:** [[Agent Development 3-Month Curriculum#Appendix G — Continuous Learning System]] — Appendix G is the *learner's* continuous learning; this file is the *maintainer's*.
- **Connects to:** [[Agent Development 3-Month Curriculum#The Six Areas an AI Engineer Must Master (2026 hiring rubric)]] — the 6-area mapping table updates as Akshay's rubric evolves.
- **Connects to:** [[Week 7.3 - Production LLM Infrastructure]] — W7.3 is the first chapter born from this discipline (12 May 2026 audit).
