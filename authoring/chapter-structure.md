# Chapter Structure — read when creating or editing a chapter

> On-demand authoring reference. Indexed from `CLAUDE.md`. The skeleton every chapter MUST follow. Three sections have deeper rules in companion files: §3 → `diagrams.md`, §4 walkthroughs → `code-walkthroughs.md`, §5 → `bad-case-journal.md`.

## Required chapter structure (normative — every chapter MUST contain these 9 sections)

The reference chapter is `Week 2 - Rerank and Context Compression.md`. Every other chapter — main week, decimal supplement, future addition — MUST match this structure. A chapter that skips a required section is incomplete and SHOULD be flagged before commit.

### Section 1 — Why This Week Matters (REQUIRED, ~150 words)

Production motivation + interview signal. Why does this matter in real systems? Why will an interviewer ask about it? Do **not** collapse to a one-line TL;DR. The 150-word length is intentional — it is the speak-aloud hook for the topic.

### Section 2 — Theory Primer (REQUIRED, ~1000 words)

Long-form explanatory prose. Cite original papers (arXiv links). Include real numbers, not vague claims ("hybrid recall@10 = 0.998 vs dense 0.993" not "hybrid is better"). Distinguish carefully from adjacent concepts that are commonly conflated.

### Section 3 — Mechanism / Architecture Diagram (REQUIRED)

Mermaid diagrams (Obsidian renders them natively). Every chapter has at least one diagram showing the system shape. Label every node and edge — unlabeled boxes are not diagrams. **Full Mermaid hygiene rules + font directives + render-validation → `diagrams.md`.**

### Section 4 — Lab Phases (REQUIRED — numbered phases with runnable code)

Phases are numbered and time-budgeted (`## Phase 1 — <name> (~2 hours)`). Each phase includes:
- A goal statement
- Setup commands (real package names, real versions)
- Step-by-step numbered actions with **runnable Python** (not pseudocode)
- Verification commands at the end of the phase
- An expected metrics table (recall@K, latency, cost, etc — measured on M5 Pro hardware)

Every Python script in a phase follows the **per-Python-block bundle** (Architecture diagram → Code → Walkthrough → Result → Insight) and one of the **two walkthrough modes** (per-block for partial code, execution-trace for complete runnable code). **Full bundle + walkthrough rules → `code-walkthroughs.md`; diagram rules → `diagrams.md`.**

### Section 5 — Bad-Case Journal (REQUIRED — 3–5 entries, exact format)

Each entry uses **exactly** this 3-field format:

```
**Entry N — <one-line symptom>.**
*Symptom:* what the operator observes
*Root cause:* what is actually broken
*Fix:* concrete remediation, with code or config when applicable
```

Entries also belong in the global `Bad-Case Journal.md`. **Every entry MUST be REAL + MEASURED — no predicted / `(planned)` / hypothetical entries. Full MEASURED-ONLY INVARIANT + the `ANTI-PATTERNS.md` graduation rule → `bad-case-journal.md`.**

### Section 6 — Interview Soundbites (REQUIRED — 2–3 entries, user-voice, ~70 words each)

Written in first-person, anchored to a measured outcome from §4 or §5. Each soundbite is a speak-aloud answer to an interview question, ~70 words. Avoid hedging language. Avoid generic advice. Reference specific numbers and specific findings from this chapter.

### Section 7 — References (REQUIRED)

Peer-reviewed papers + canonical docs + production blog posts. Format:
- **Author et al. (Year).** *Title.* Venue. arXiv:NNNN.NNNNN. One-line description of why this reference matters.

Link to arXiv where applicable. Include at least one production blog post or canonical implementation repo so the reader can see how the concept ships in practice, not just how it is described in papers.

### Section 8 — Cross-References (REQUIRED)

Use these four labels in this order:

- **Builds on:** explicit prerequisite chapters (the reader should have done these first).
- **Distinguish from:** adjacent topics that are commonly conflated. **This section is high-leverage; do not skip it.** It is what makes a candidate sound senior in interviews.
- **Connects to:** later chapters that use this material as a building block.
- **Foreshadows:** chapters where this material reaches its full production shape (often W11 System Design or W12 Capstone).

Cross-references must be bidirectional — if W7 says "Builds on: W4 ReAct", then W4 should say "Connects to: W7 Tool Harness". When you add a forward link, add the reverse link in the target chapter in the same edit.

### Section 9 — Frontmatter (REQUIRED on new chapters)

YAML frontmatter at the top of the file:

```yaml
---
title: <chapter title>
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - agent
  - <topic-specific tags>
audience: <who this chapter is for, copied from curriculum overview>
stack: <hardware + model assumptions>
---
```

Update `updated:` on every substantive edit. Tags should overlap with sibling chapters so Obsidian's graph view connects them.

## Optional sections (use when relevant)

- **Empirical findings subsection (§N.X.Y).** When you run experiments and produce measured results that contradict or refine the theory primer, add a numbered subsection (e.g., `### 2.2.1 Actual results — fp32 vs fp16 reranker on M5 Pro (2026-04-28 runs)`). W2 uses this pattern extensively for its rerank experiments. Date-tag the subsection.
- **Mini-lab.** A 30-minute hands-on exercise that doesn't warrant a full Phase. Use `### Mini-Lab — <name>`.
- **Production considerations.** When the chapter has a clear production deployment story, add a `## Production Considerations` section before §5 Bad-Case Journal. Cover sandboxing, cost ceilings, multi-tenancy, observability.

## Pre-commit checklist (run mentally before every chapter commit)

```
[ ] §1  Why This Week Matters — ~150 words present
[ ] §2  Theory Primer — ~1000 words, papers cited, real numbers
[ ] §3  Mermaid diagram present and labeled (hygiene + render-validated → diagrams.md)
[ ] §4  Lab phases numbered, time-budgeted, with runnable code
[ ] §4  Expected metrics table present
[ ] §4  Per-Python-block bundle present (Architecture mermaid → Code → Walkthrough → Result → Insight); correct walkthrough mode (→ code-walkthroughs.md)
[ ] §5  Bad-Case Journal — 3–5 entries, exact format, REAL + MEASURED (`audit_bcj_measured.py` exits 0; → bad-case-journal.md); new entries copied to global Bad-Case Journal.md
[ ] §6  Interview Soundbites — 2–3, user-voice, ~70 words, measured-outcome anchored
[ ] §7  References — papers + docs + production examples
[ ] §8  Cross-References — Builds on / Distinguish from / Connects to / Foreshadows; reverse links added in linked chapters
[ ] §9  Frontmatter updated
```
