# Code Walkthroughs — read when writing a §4 lab-phase code block

> On-demand authoring reference. Indexed from `CLAUDE.md`. Governs the per-Python-block bundle and the walkthrough that accompanies every code block in §4 Lab Phases. Diagram rules live in `diagrams.md`.

## Per-Python-block bundle (NORMATIVE)

Each Python script (or substantive Python snippet) inside a Lab Phase MUST be presented as one self-contained bundle, in this exact order, before moving to the next block:

1. **Architecture diagram** — Mermaid (non-ASCII) showing the data flow / call graph for THIS script, placed immediately before the code. Full Mermaid hygiene + font directives + render-validation → `diagrams.md`.
2. **Code** — full `\`\`\`python` block. Annotate `**Code:**` header above for visual delineation.
3. **Walkthrough** — `**Walkthrough:**` header. Style depends on what the code IS — see "Two walkthrough modes" below.
4. **Result** — `**Result:**` header, then measured numbers from the actual lab run (wall time per stage, output sizes, aggregate scores). Pull from `RESULTS.md` in the lab repo. Mark `~estimated` if not yet measured; update after the run.
5. **Insight callout** — `` `★ Insight ─────────────────────────────────────` `` / `` `─────────────────────────────────────────────────` `` border around 2–3 bullets calling out non-obvious design choices, model superpowers being exploited, deliberate trade-offs.

The bundle is one continuous reading unit — do not split mermaid into one section, code into another, walkthrough into a separate `## Phase 5 — Code Walkthroughs` section. The old `## Phase 5` separate-section pattern is **deprecated** as of 2026-05-07. Reference: `Week 2.7 - Structure-Aware RAG.md` Phase 2/3/4 — every Python block follows this bundle shape.

**The non-negotiable bar:** the walkthrough portion must answer "why is this code shaped this way?" — a reader who copy-pastes the script must come away understanding the design choices, not just having a working script. If you cannot answer "why" for a block, you do not understand it well enough; spike the code first, then write.

## Two walkthrough modes — pick by what the code block IS (NORMATIVE)

- **Partial code** (a function/class/snippet excerpted from a larger module) → the **per-block `Block 1 / Block 2 …`** analysis: `**Block 1 — <title>.**` + 2–4 sentences per logical block answering *why*, not what. Cover gotchas a copy-paster would miss.
- **Complete, runnable code** (an entrypoint / demo / `main()` / CLI that executes **end-to-end** — e.g. `examples/example_graph.py`) → an **execution-trace walkthrough**. Do NOT use bare `Block N` for a script you can actually run; trace the run instead, in this exact shape:
    1. **Numbered steps in execution order** (`Step 0 … Step N`), one per phase of the run (setup → build → trigger → execute → observe).
    2. **Per step: the actual code slice + a state snapshot of what changed** — show the relevant lines in a ```` ```python ```` block, then the resulting DB rows / data structure / files in a ```` ```text ```` block. The reader must *see* state mutate, not just be told it did (e.g. `nodes: n1 READY | n2 PENDING …`).
    3. **For concurrent or stateful runtimes: a per-tick trace** (`t0 … tN`) of the state transitions (claim → execute → mark-done → promote), each tick pinned to the code that drives it.
    4. **A real measured output sample** in a ```` ```text ```` block — the *actual* stdout of the run with REAL numbers pulled from `RESULTS.md`. Never invent or carry placeholder numbers (no illustrative `tokens=437` when the real run is `195`).
    5. **A validated runtime diagram** — `sequenceDiagram` for ordering/concurrency (its `par` block shows parallelism cleanly; Gantt is fragile for abstract ticks — avoid), `flowchart` for structure. Validate that it renders (`mmdc`) per `diagrams.md`.
    6. **Insight callout** as usual (3–4 bullets).

  Every step's code slice + every `file:line` reference MUST match the current lab file verbatim (the bidirectional code↔runbook sync rule). Reference implementation: `Week 4.6 — Durable Agent Runtime` § *The end-to-end demo — `examples/example_graph.py`*.

## Walkthroughs are inline — no separate walkthrough section

There is **no separate code-walkthrough section** (the old `## Phase 5 — Code Walkthroughs` pattern is gone). Walkthroughs live inline next to their code per the per-block-bundle rule above. **Do not emit a `## 5. (deprecated)` stub or any deprecated placeholder.**

Section numbering is **continuous, 1–9** (no gap). After §4 Lab Phases the next section is **§5 Bad-Case Journal** — the sections below renumbered down by one when the old deprecated §5 slot was removed (2026-06-16). When you touch a chapter that still carries a leftover `## 5. (deprecated)` stub or a §4→§6 gap, delete the stub and renumber the remaining sections so they run 1–9 continuously (move any walkthrough text back into its Phase first, then renumber §6→§5 … §10→§9, and fix that chapter's internal `§N` references — taking care NOT to touch cited-paper section numbers like "RouteLLM §5").
