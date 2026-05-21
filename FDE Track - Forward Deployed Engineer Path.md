---
title: FDE Track - Forward Deployed Engineer Path
created: 2026-05-21
updated: 2026-05-21
tags:
  - agent
  - career
  - fde
  - track
  - interview-prep
audience: "cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles, local-first MLX stack on Apple Silicon, ~$13 cloud spend cap across the program"
stack: macOS Apple Silicon M5 Pro 48 GB, oMLX :8000, Qdrant via Docker
---

# FDE Track - Forward Deployed Engineer Path

> **Overlay note - not a week.** This threads the existing 40-chapter curriculum into the **Forward Deployed Engineer (FDE)** path. It writes no new lab. It re-shelves what already exists so the curriculum reads as an FDE program for a reader who wants that specific outcome. Read this once early, then use the mapping table as a navigation index.

## Why this track exists

By May 2026 the FDE became the most-hired engineering role in AI. Job listings spiked roughly 800%; OpenAI and Anthropic both launched FDE ventures within days of each other; average total compensation at Palantir-class employers sits near $238K, with staff-level FDEs clearing $630K+. The role is not a niche - it is where the agent industry's "pilots to production" shift created demand faster than the talent pool could fill it.

This curriculum was written before "FDE" was a common title, but it already teaches every technical skill the role requires. This note makes the path explicit so the reader does not have to reverse-engineer it.

## What a Forward Deployed Engineer is

An FDE is an engineer **embedded inside the customer's organization** who ships production AI code in that customer's real environment. The role lives in the gap between *"our AI product works in the demo"* and *"our AI product is live inside Acme Corp's compliance workflow."* It sits at the intersection of three disciplines:

- **Engineering** - writes production code, builds integrations, fixes edge cases, navigates APIs and data pipelines.
- **Consulting** - translates a business problem into a technical spec, explains complex systems to non-technical executives.
- **Solutions architecture** - decomposes a messy real-world system into something an agent can act on reliably.

The defining differentiator, repeated across every 2026 FDE write-up: **customer context**. The only way to acquire it is to ship something to a customer - and internal stakeholders count.

## The FDE skill stack (2026)

| Skill area | What it means in practice |
|---|---|
| Core engineering | Python and TypeScript fluency; clean code; APIs; data pipelines (SQL) |
| RAG fundamentals | Retrieval, chunking, reranking, vector stores, hybrid search, graph retrieval |
| Agentic orchestration | Agent loops, multi-agent coordination, named frameworks (LangGraph, CrewAI, DSPy) |
| MCP and integration | Model Context Protocol, tool wiring, schema bridging across systems |
| Evaluation and guardrails | Eval suites that catch hallucinations, regressions, grounding gaps; LLM-as-judge |
| Observability | Multi-turn tracing, failure-mode analysis, production telemetry, cost rollups |
| Production deployment | Docker, Kubernetes, cloud, secrets management, identity propagation, policy enforcement |
| Security and compliance | Threat modelling, sandboxing, compliance-aware deployment |
| Customer context | Requirements intake, scoping, SLA definition, stakeholder handoff, feedback iteration |
| Business translation | Turning business needs into technical specs; executive communication |

## The skill stack mapped to this curriculum

Every FDE skill area already has a home. This table is the navigation index - read down the column that matches the skill you want to build.

| FDE skill area | Curriculum weeks | What you build |
|---|---|---|
| Core engineering | W0.5 LLM Internals, W1 Vector Retrieval | Baseline pipelines, embedding ingestion, MPS profiling |
| RAG fundamentals | W1, W2 Rerank, W2.5 GraphRAG, W2.7 Structure-Aware RAG, W3 RAG Evaluation, W3.7 Agentic RAG | Hybrid retrieval + reranking + graph + tree-index, all benchmarked head-to-head |
| Agentic orchestration | W4 ReAct From Scratch, W4.5 Model Routing, W5 Pattern Zoo, W5.5 Metacognition, W10 Framework Shootout | ReAct from scratch, then the same task in LangGraph / LlamaIndex / OpenAI Agents SDK |
| MCP and integration | W6 Claude Code Source Dive, W6.6 MCP Schema Bridge, W6.8 Protocol Survey | MCP server/client, schema bridging, A2A / ANP protocol survey |
| Memory | W3.5 Cross-Session Memory, W3.5.5 Multi-Agent Shared Memory, W3.5.8 Two-Tier Memory, W3.5.9 Memory Benchmarks | Two-tier memory architecture, LongMemEval benchmarking, judge-controlled measurement |
| Evaluation and guardrails | W2.7 GT-Judge, W3 RAG Evaluation, W9 Hallucination Detection, W9.3 Agent Performance Evaluation, W3.5.8 §5.3 | Per-trajectory rubrics, LLM-as-judge, the judge-confound and commitment-bias findings |
| Observability | W9.3, W11.6 Production Tracing + Cost Telemetry, W3.5.95 Self-Observability Memory | OTel spans, DuckDB cost rollups, multi-turn trace analysis |
| Production deployment | W7.3 Production LLM Infrastructure, W11.6, W11.8 Continuous Training + MLOps | Containerised serving, drift detection, shadow ramps |
| Security and compliance | W11.5 Agent Security | Threat modelling, sandboxing, prompt-injection defence |
| Tool use | W4, W7 Tool Harness, W7.5 Computer Use, W7.8 Code-Agent Patterns | 20-scenario bad-case reliability suite, browser agents, AST-aware code agents |
| Customer context and delivery | W12 Capstone + **FDE Delivery Mode** (see W12) | Intake brief, scoping doc, SLA, handoff README, feedback loop |
| Business translation | W12 FDE Delivery Mode - stakeholder brief artifact | One-page executive translation of the technical build |

## The compressed FDE reading path

If a reader is optimising specifically for FDE interviews and cannot do all 40 chapters, this is the priority spine. It front-loads the role's load-bearing skills.

1. **Foundations** - W0.5, W1, W2, W3 (retrieval + eval baseline)
2. **Agents** - W4 ReAct from scratch, W5 Pattern Zoo, W10 Framework Shootout (named frameworks)
3. **Integration** - W6 Claude Code Source Dive, W6.6 MCP Schema Bridge
4. **Memory** - W3.5.8 Two-Tier Memory (the measured-engineering centrepiece)
5. **Evaluation** - W9.3 Agent Performance Evaluation, W3.5.8 §5.3 (the eval-discipline showcase)
6. **Production** - W7.3 Production LLM Infrastructure, W11.5 Agent Security, W11.6 Production Tracing
7. **Delivery** - W12 Capstone C (Infra-Aware SRE Agent) run in **FDE Delivery Mode**

## The one gap this curriculum closes deliberately: customer context

Every technical FDE skill is covered above. The single skill a self-directed curriculum cannot teach by default is **customer context** - because labs are built for yourself, not delivered to a stakeholder.

The fix is **FDE Delivery Mode** in [[Week 12 - Capstone and Mocks#FDE Delivery Mode - run the capstone as a forward-deployed engagement|Week 12]]. It does not replace the technical capstone; it wraps the existing Capstone C build in a customer-engagement simulation: a stakeholder intake brief, a scoping doc with an explicit SLA, a handoff README, and one feedback-iteration cycle. That converts "I built an SRE agent" into "I delivered an SRE agent to a stakeholder and iterated on their feedback" - the sentence an FDE interviewer is listening for.

## Your unfair advantage

The FDE role is engineering ∩ consulting ∩ solutions-architecture. Most ML-engineer and software-engineer candidates can show the engineering third and have **zero** evidence for the consulting third. A reader arriving from a cloud-infrastructure delivery background - Kubernetes, Terraform, observability, and a customer-facing delivery role with a satisfaction KPI - already has the consulting third. That is rare and hard to fake.

The track's job is to make both halves visible: the technical chapters prove the engineering, and W12 FDE Delivery Mode plus the stakeholder brief prove the consulting. Capstone C (the Infra-Aware SRE Agent) is the build where an infra background stops being something to explain away and becomes the differentiator.

## Interview framing

> "Forward Deployed Engineer is the role where my background composes instead of competing. Most LLM-engineer candidates come from ML or pure software and have never run Kubernetes in production or sat in a customer's delivery review. I have done both. My curriculum capstone is an infra-aware SRE agent - it reads the Kubernetes API, Prometheus, and Terraform plans to answer 'why is checkout-service p99 up?' - and I ran it as a forward-deployed engagement: intake brief, scoped SLA, handoff doc, one feedback cycle. The technical half is measured engineering, every claim backed by a RESULTS.md. The delivery half is the part most candidates can't show."

## References

- **The New Stack (2026).** *Forward deployed engineer is AI's hottest job as OpenAI and Google race to hire.* thenewstack.io. Role definition, the OpenAI/Anthropic FDE-venture launches, the 800% listing spike.
- **MarkTechPost (2026).** *What is a Forward Deployed Engineer.* marktechpost.com, 2026-05-20. Skill-stack breakdown, hiring landscape.
- **FDE Academy (2026).** *How to Become a Forward Deployed Engineer.* fde.academy. The "customer context - internal counts too" framing; the curriculum-as-roadmap approach.
- **MachineLearningMastery (2026).** *7 Agentic AI Trends to Watch in 2026.* machinelearningmastery.com. The pilots-to-production shift; integration + governance as 60% of project budgets.
- Surfaced via `/last30days` research run, 2026-05-21. Raw evidence: `~/Documents/Last30Days/ai-agent-development-trends-and-ai-forward-deployed-engineer-skills-raw-v3.md`.

## Cross-References

- **Builds on:** the full curriculum - this is an overlay, not a prerequisite chain.
- **Distinguish from:** [[Trend-Monitoring Discipline]] (a maintenance practice, not a career track); the Applied AI Engineer path (FDE adds the embedded-delivery and customer-context dimension that a pure Applied AI Engineer role does not require).
- **Connects to:** [[Week 12 - Capstone and Mocks#FDE Delivery Mode - run the capstone as a forward-deployed engagement|Week 12 FDE Delivery Mode]] - where the customer-context gap is closed.
