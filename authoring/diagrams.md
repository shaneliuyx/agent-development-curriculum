# Diagram Rules (Mermaid) — read when adding or editing a diagram

> On-demand authoring reference. Indexed from `CLAUDE.md`. Governs §3 Mechanism diagrams and the Architecture diagram in every §4 per-block bundle.

## Section 3 — Mechanism / Architecture Diagram (REQUIRED)

Mermaid diagrams (Obsidian renders them natively). Every chapter has at least one diagram showing the system shape. Label every node and edge — unlabeled boxes are not diagrams.

## Mermaid hygiene rules (NORMATIVE)

- **Edge labels with parens** MUST be quote-wrapped (`-->|"text<br/>(parens)"| Node`). Bare parens in unquoted edge labels break the Mermaid parser.
- **Subgraph titles** MUST be ≤22 characters AND ≤ the cluster's narrowest sibling cluster width. Two constraints: (a) absolute char count to avoid wrapping at any zoom; (b) Mermaid sizes each cluster to its widest child node, so a title that fits in a wide cluster may wrap in a narrow sibling. Visual symmetry rule: side-by-side comparison subgraphs should have titles of matching word count and length — if one sibling cluster is narrower, shorten ALL titles to fit the narrowest. Move port numbers, version tags, qualifier suffixes into the section's prose paragraph or into child node labels (`Imprint API<br/>:1995`), not the cluster title.
- **Horizontal multi-cluster layouts** (`flowchart LR` with multiple `subgraph` blocks) MUST add invisible-link chaining (`C1 ~~~ C2 ~~~ C3`) when the subgraphs share no real edges. Without it, the layout engine stacks subgraphs vertically and wastes horizontal canvas, regardless of the top-level `LR` declaration.
- **Node labels** with multiple lines use `<br/>` (HTML break), not literal `\n`. Each line ≤20 chars to avoid box-width drift across siblings.
- **Diagram direction** — default to **`flowchart TD`** (vertical). Vertical diagrams stay narrow, fit the article column without downscaling, and render text at declared fontSize. **`flowchart LR`** is reserved for diagrams where horizontal layout is semantically load-bearing — typically side-by-side subgraph clusters used for visual comparison (e.g., Class 1 vs Class 2 vs Class 3 architectures, L1/L2/L3 tier topology). Wide linear pipelines (>5 nodes) MUST be TD; reading a 10-node horizontal scroll is worse than reading a 10-node vertical column.
- **Font size directive** — every mermaid block opens with a `%%{init: ...}%%` directive immediately after the ```` ```mermaid ```` fence. Two classes:
    - **Default (TD/TB diagrams):** `%%{init: {'theme':'default', 'themeVariables': {'fontSize':'20px'}}}%%`. Vertical diagrams don't downscale, so 20px declared renders at ~20px display (matches article body text).
    - **LR subgraph-cluster diagrams:** `%%{init: {'theme':'default', 'themeVariables': {'fontSize':'28px'}, 'flowchart':{'useMaxWidth':false, 'subGraphTitleMargin':{'top':20,'bottom':30}, 'nodeSpacing':40, 'rankSpacing':50}}}%%`. Three load-bearing settings: (a) `useMaxWidth:false` lets wide diagrams overflow horizontally so text stays at native pixel size; (b) `subGraphTitleMargin` adds explicit gap between cluster title and first child node (default margin is too tight at any fontSize ≥ 24px and causes title-vs-first-node text overlap); (c) `nodeSpacing` + `rankSpacing` open up the between-node gaps so dense LR diagrams don't pack arrows tight. Trade-off accepted: horizontal scroll inside the article container.

## Validate the render, not just the source (NORMATIVE)

A valid Mermaid *source* is not a valid *render*. Before shipping any diagram, validate that it actually renders:

```bash
npx @mermaid-js/mermaid-cli -i diagram.mmd -o diagram.svg   # SVG produced = parse OK
```

Known gotchas:
- `;` and `#` break Mermaid **even inside note/message text** (`;` is a statement separator). Replace with `—` or `,`.
- **Gantt** is fragile for abstract relative ticks (axis duplicates, bars overflow). For a worker/time concurrency view use **`sequenceDiagram`** with a `par … and … end` block — the `par` box shows parallelism cleanly and renders reliably.

## Pre-commit diagram check

- [ ] Default `flowchart TD` (LR only for side-by-side subgraph clusters); edge-label parens quote-wrapped (`-->|"text<br/>(parens)"|`); subgraph titles ≤22 chars (no wrap/clip); horizontal multi-cluster layouts use `~~~` invisible-link chaining; node labels use `<br/>` not `\n`; TD blocks open with `%%{init: ... 'fontSize':'20px' ...}%%`, LR cluster blocks open with `%%{init: ... 'fontSize':'28px', ... 'useMaxWidth':false, 'subGraphTitleMargin':{'top':20,'bottom':30}, 'nodeSpacing':40, 'rankSpacing':50 ...}%%`.
- [ ] Every diagram **render-validated** with `mmdc` (no `;`/`#` in text; no fragile Gantt for abstract ticks).
