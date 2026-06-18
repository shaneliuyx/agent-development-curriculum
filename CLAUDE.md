# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A 12-week, project-driven Agent / LLM Engineer interview-prep curriculum, authored as an Obsidian vault. **Prose-first: no application build, no test suite.** The chapters are Markdown. The one exception is `scripts/` — Python audit scripts that act as the vault's lint/CI layer, enforcing structural invariants across chapters (see [Audit commands](#audit-commands--the-vaults-lint-layer)). Each chapter is a long-form pedagogical document combining theory primer, hands-on lab, bad-case journal, and interview soundbites. The labs' own code lives in a separate repo (`~/code/agent-prep/lab-*`); selected lab/reference repos are also vendored under `code/` here. This vault is the *narrative* + *interview-prep* layer over those labs.

Reader profile in the frontmatter of `Agent Development 3-Month Curriculum.md`: cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles, local-first MLX stack on Apple Silicon, ~$10 cloud spend cap across 12 weeks.

## File organization

- `Agent Development 3-Month Curriculum.md` — top-level overview + discipline rules. Read first.
- `Week N - <Title>.md` — main weekly chapters (W0–W12).
- `Week N.M - <Title>.md` — supplementary chapters inserted between main weeks (W2.5 GraphRAG, W3.5 Cross-Session Memory, W3.7 Agentic RAG, W5.5 Metacognition, W6.5 Hermes, W6.7 Agent Skills, W7.5 Computer Use, W8.5 Voice AI, W11.5 Agent Security). Decimal numbering = "elective; cuts in between sequentially-prerequisite weeks."
- `README.md` — public-facing entry point ("How to read"). The reading-order map lives here.

Cross-cutting libraries (indexed by theme/pattern, not by week — keep in sync when chapters change):
- `Bad-Case Journal.md` — ops-pattern library. Every chapter's bad-case entries also live (or should live) here. Read order in its preamble. Documents WHAT broke + WHY + FIX, *after the fact*.
- `ANTI-PATTERNS.md` — companion to the Bad-Case Journal. Documents patterns to avoid *before* writing code. Read both before starting a new chapter or lab.
- `Engineering Decision Patterns.md` — design-decision library, indexed by pattern number. The audit scripts enforce the mechanically-checkable patterns here (e.g. Pattern 19, Pattern 21).
- `Interview Question Index.md` — pre-interview entry point; maps interview-question patterns → chapter + measured anchor. Open 24–48h before an interview.
- `FDE Track - Forward Deployed Engineer Path.md` — alternate chapter ordering for Forward Deployed Engineer interview prep.
- `Trend-Monitoring Discipline.md` — process doc for keeping the curriculum current with the field.

Supporting directories:
- `authoring/` — the chapter-authoring spec, split into focused on-demand files (see [Chapter authoring](#chapter-authoring--read-the-relevant-spec-on-demand)).
- `scripts/` — Python audit scripts (the vault's lint layer). See [Audit commands](#audit-commands--the-vaults-lint-layer).
- `code/` — vendored lab/reference repos (`agent-prep`, `EverOS`, `LongMemEval`, `self-improving-agents-curriculum`). Source for measured numbers; not part of the prose.
- `proposals/` — draft chapter proposals before they become full `Week N.M` chapters.
- `research/` — research notes backing specific chapters (e.g. structure-aware RAG tree construction).
- `tasks/`, `assets/diagrams/` — supporting non-prose.

## Audit commands — the vault's lint layer

There is no build or test suite. The closest equivalent is `scripts/`, which mechanically enforces the checkable invariants in `Engineering Decision Patterns.md`. Run from the vault root any time the chapter set changes substantially:

```bash
# Cross-reference audit (Pattern 21 — bidirectional cross-ref invariant):
# every "Builds on:/Connects to:/Distinguish from:/Foreshadows:/Cited by: B" on
# chapter A must have a reciprocal mention on chapter B.
python3 scripts/audit_cross_refs.py
python3 scripts/audit_cross_refs.py --verbose          # show every missing edge

# Status-marker audit (Pattern 19 — Spec → IMPLEMENTED transition markers):
# flags implicit-state headings (TBD / OUTLINED / "FULL TEXT IN ROUND N").
python3 scripts/audit_status_markers.py
python3 scripts/audit_status_markers.py --list-explicit # also show compliant headings
python3 scripts/audit_status_markers.py --fix           # rewrite implicit → (SPEC)

# Bad-Case Journal measured-only audit (§5 MEASURED-ONLY INVARIANT):
# flags any §5 / global-journal entry that reads as predicted/scoped/hypothetical
# rather than a real observed failure ((planned), "predicted", "scoped-not-measured",
# "to be filled after lab run", TBD, "not yet measured", etc.).
python3 scripts/audit_bcj_measured.py
python3 scripts/audit_bcj_measured.py --verbose         # show each flagged entry + reason
```

Exit code `0` = clean, `1` = violations found (CI-hook-friendly). Both scripts walk `Week*.md` in the vault root. Taste-based patterns (★ Insight callouts, trade-off transparency) stay human-review-only — do not try to automate them. When you codify a new mechanically-checkable pattern in `Engineering Decision Patterns.md`, add a matching script here (`scripts/README.md` documents the shared shape).

## Chapter authoring — read the relevant spec on demand

The detailed chapter-authoring rules are split into focused files under `authoring/`. They are **NOT auto-loaded** — read the one your task needs:

| When you are… | Read |
|---|---|
| creating or editing a chapter's structure | [`authoring/chapter-structure.md`](authoring/chapter-structure.md) — the 9 required sections + optional sections + the pre-commit checklist |
| adding or editing any diagram | [`authoring/diagrams.md`](authoring/diagrams.md) — Mermaid hygiene + font directives + render-validation |
| writing a §4 lab-phase code block | [`authoring/code-walkthroughs.md`](authoring/code-walkthroughs.md) — the per-Python-block bundle + the two walkthrough modes (per-block vs execution-trace) |
| writing or editing Bad-Case entries | [`authoring/bad-case-journal.md`](authoring/bad-case-journal.md) — §5 entry format + the MEASURED-ONLY invariant |

**Hard invariants (always in force — full detail in the files above):**
- Every chapter has the **9 required sections**, numbered continuously 1–9 (`chapter-structure.md`).
- Every §4 code block uses the **per-block bundle** (Architecture diagram → Code → Walkthrough → Result → Insight). **Complete runnable scripts** get an **execution-trace** walkthrough (Step 0…N, code + state snapshot per step, real measured output); partial code gets the `Block N` style (`code-walkthroughs.md`).
- Every diagram is **render-validated** (`mmdc`); no `;` / `#` inside Mermaid text (`diagrams.md`).
- Every §5 Bad-Case entry is **REAL + MEASURED** (`scripts/audit_bcj_measured.py` exits 0); predicted modes go to `ANTI-PATTERNS.md` (`bad-case-journal.md`).
- All numbers are **measured + traceable to `RESULTS.md`**; cross-references are **bidirectional**.

## Hard rules from `Agent Development 3-Month Curriculum.md`

These are stated discipline rules in the curriculum overview. Honor them when editing:

1. **No tutorial graveyard.** Every week must end with a runnable artifact + measured number. Do not write a chapter without empirical anchors.
2. **Every lab gets a `RESULTS.md`** — numbers, screenshots, what broke, what was fixed. (RESULTS.md lives in the lab repo, not the vault — but the vault's bad-case journals reference it.)
3. **Speak the answers out loud.** This is why interview soundbites exist; do not skip that section.
4. **Local-first, cloud only when you must.** Default examples to MLX/Ollama/local Whisper. Cloud APIs only when the lesson requires them.

## Cross-reference syntax

Internal vault links use Obsidian wikilinks: `[[Week 2 - Rerank and Context Compression#Phase 1 — Hybrid Retrieval|Phase 1]]`. Section anchors are `#<exact heading text>`. Maintain alphabet-only / no-emoji headings if you want stable anchors across renderers (most existing headings already comply).

Cross-reference order at the end of every chapter:
- `Builds on:` — explicit prerequisites
- `Distinguish from:` — adjacent topics that are commonly conflated (this section is high-leverage; do not skip)
- `Connects to:` / `Consumed by:` — chapters that use this material later

## Numbers and citations

Numbers in this vault are empirically measured on the user's hardware (MacBook Pro M5 Pro, 48 GB unified memory) unless stated. When citing latency, recall, cost, or throughput, prefer the user's measured numbers from the lab repo's `results/*.json` over public benchmark numbers. If you must use public numbers, cite the source.

## Editing safety

- **Do not delete cross-references** without first checking the linked chapter's `Builds on:` / `Distinguish from:` blocks — these are bidirectional invariants.
- **Preserve the `Bad-Case Journal` symptom → root cause → fix format.** Other chapters' interview soundbites cite specific entries.
- **Do not collapse the `Why This Week Matters` opening into a TL;DR.** It is the interview hook for that topic and is intentionally ~150 words, not 30.
- **Frontmatter** (where present) carries `tags`, `created`, `updated`, `audience`, `stack`. Update `updated` on substantive edits.
