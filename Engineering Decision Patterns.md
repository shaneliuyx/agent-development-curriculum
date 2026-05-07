---
tags: [agent-curriculum, meta-skills, decision-making, working-with-ai]
created: 2026-04-28
updated: 2026-04-28
---

# Engineering Decision Patterns

A working playbook for **engineering decision-making in ambiguous-scope projects** — solo, with a teammate, or in collaboration with an AI agent. These patterns showed up repeatedly while building this curriculum, and they're transferable to any technical work where scope, trade-offs, and "what to do next" aren't pre-decided.

**Read together with:**
- [[Bad-Case Journal]] — captures *post-failure* lessons (what to do when you've already messed up)
- This doc captures *pre-failure* discipline (the patterns that prevent the bad cases)

> The single most expensive mistake in ambiguous work is **silent scope creep**: starting something small, watching it grow, finishing 4 hours later with a result that's only worth 1 hour. Every pattern below is designed to prevent that.

---

## How to use this doc

Each pattern has the same structure:
- **Name + one-line description**
- **When to use** — the trigger condition
- **Template** — the literal phrasing to use (or near-equivalent)
- **Why it works** — the mechanism
- **Anti-pattern** — what *not* to do, and what it costs

**Skim the names first.** Once you've internalized the pattern names ("scope-estimate-first," "options table," "honest pivot"), you can reach for them by name in the moment without re-reading the templates.

---

## Pattern 1 — Scope-Estimate-Before-Commit

**Description:** Never start a multi-hour task without first naming the scope and getting explicit go-ahead.

**When to use:** Any task that you suspect will take more than ~30 minutes of focused work, or has more than ~3 sub-steps.

**Template:**
> "Going X. Substantial scope (~Y hours): [list of sub-tasks]. [Specific first action]."

**Examples from this curriculum:**
- *"Going A+. Substantial scope (~3 hours): theory callout + Phase 7 in Week 2 + new `lab-02b-production-libs/` with 3 scripts + commit. Setting up directory structure and starting."*
- *"Cost so far for this one diagram: ~25 min. Six more would be ~2.5 hours. Pausing for honest cost-benefit check before continuing."*

**Why it works:** Surfaces three things in one line — your interpretation of the request, your time estimate, and your immediate next action. The user can correct any of the three before you commit time. The cost of one corrective sentence is much lower than the cost of a wrong-direction hour.

**Anti-pattern:** Diving in with "OK, doing it now" and surfacing scope after the fact. The user can't course-correct what they don't see.

---

## Pattern 2 — Options Table (A/B/C)

**Description:** When there are multiple paths forward, present 2-4 options as a table with **time + value/risk + recommendation**. Wait for explicit selection.

**When to use:** Whenever you genuinely see multiple defensible paths and the choice depends on user priorities you can't infer.

**Template:**

| Option | What I do | Time | Trade-off |
|---|---|---|---|
| A | [concrete action] | ~Xh | [what this buys vs costs] |
| B | [different action] | ~Yh | [what this buys vs costs] |
| C | [skip / defer] | 0 | [opportunity cost] |

> "My recommendation: **X** because [explicit rationale]. Or B if [different priority]. What do you want?"

**Examples from this curriculum:**
- "Three paths for UML in markdown: Mermaid native / PlantUML plugin / SVG generation"
- "Three options going forward: A — uniform polish (37 diagrams) / B — selective (12 diagrams) / C — skip Tier 1"
- "Three options for fixing: A — pragmatic revert / B — redo properly / C — switch to layout engine"

**Why it works:** A table forces you to state each option's cost as well as its benefit. Listing 2-4 options (not 1, not 7) communicates "I've considered alternatives, here are the live ones." The recommendation prevents sycophantic neutrality (see Pattern 3).

**Anti-pattern:** Presenting one option as if it's the only choice ("here's what I'm going to do") OR presenting many options without a recommendation ("here are 5 ideas, what do you think?"). First denies the user agency; second offloads the decision to them.

---

## Pattern 3 — Always Recommend; Never Be Neutrally Sycophantic

**Description:** Every options-table includes a recommendation with rationale. The user can override; you don't pre-emptively defer.

**When to use:** Any time you present > 1 option.

**Template:**
> "My recommendation: **X** because [trade-off reasoning]. If [different priority], pick Y instead."

**Why it works:** "Here are 3 options, what would you like?" shifts cognitive load to the user — they have to evaluate all 3 themselves. "I recommend A because it's the highest-leverage trade-off; pick B if you care more about Z" lets the user accept your judgment in 1 second OR override in 1 sentence. Same information, half the decision time.

**Anti-pattern:** "Whatever you prefer" / "I can do either" — feels respectful, actually wastes time. The expert is supposed to have an opinion.

**Sub-rule:** If you GENUINELY don't have a recommendation (rare — usually means scope is unclear), say so explicitly: "I don't have a strong recommendation here because [reason]. Either path is defensible; what's your priority?" That's different from sycophantic neutrality.

---

## Pattern 4 — Mid-Stream Honest Pivot

**Description:** When you discover mid-execution that a better path exists, **stop the original work and surface the discovery.** Don't grind through the now-suboptimal plan.

**When to use:** Any time new information makes your original plan suboptimal.

**Template:**
> "Pausing for an honest finding before continuing the [original plan]. **★ Insight:** [what I learned]. This changes the cost-benefit: [new analysis]. New options: A — [adjusted plan] / B — [original plan, eyes open]. Recommend A; what do you want?"

**Examples from this curriculum:**
- After Week 1 polish: *"Most of the remaining diagrams already have inline `style` directives. That makes my polish for ~25 of the 30 effectively a syntax refactor, not a visual improvement. Re-pitched: A uniform / B selective / C skip Tier 1."*
- After 1 Tier 3 SVG: *"Per-diagram cost is ~15-20 min. 6 more = 1.5-2 hours. Pausing to check direction before grinding."*
- After UML question: *"This changes the whole strategy. Mermaid natively supports most UML types. The expensive SVG path is only justified for showcase diagrams."*

**Why it works:** The cost of stopping for 1 minute to surface a discovery is much lower than the cost of completing 2 hours of work that you then have to redo. The user trusts you more, not less, when you flag changes mid-stream — it shows you're paying attention to the work, not just executing on autopilot.

**Anti-pattern:** **Sticky-progress fallacy** (see [[Bad-Case Journal#H6 — Sticky-Progress Fallacy]]). Having "made progress" makes it psychologically harder to abandon a plan; the discipline is to surface and re-decide, not just push through.

---

## Pattern 5 — Catch + Acknowledge

**Description:** When you make a mistake or miss something, acknowledge it explicitly with what was missed and why.

**When to use:** When you (or evidence from the user) catches something you got wrong.

**Template:**
> "Caught it — [what was missed]. I [defensive choice / wrong assumption] earlier; [correct action] now."

**Examples from this curriculum:**
- *"Caught the gap — I had defensively excluded `01b_latency.py` and `02_compress.py` as 'lower-value' earlier. Wrong call: `02_compress.py` inlines the retrieve+rerank logic, so it has the same dependencies."*
- *"Honest answer: no, I haven't been invoking it via the Skill tool. I've been reading the SKILL.md file directly and following its workflow manually."*
- *"Yes, I skipped formal skill invocation for diagrams 2-7 to save tokens. The visual issues are exactly what the validation checklist would have caught."*

**Why it works:** Pretending a miss didn't happen erodes trust. Naming it explicitly with the *why* (what assumption was wrong, what defense you bypassed) builds trust AND captures a learning moment. The user reading "I excluded these because they seemed lower-value" learns the failure mode by name and can apply it to their own work.

**Anti-pattern:** Silently fixing without acknowledging. The user doesn't know the issue existed, can't learn from it, and won't trust your future work as much because they sense the polish-over-honesty pattern.

---

## Pattern 6 — ★ Insight Callouts (Surface the Non-Obvious)

**Description:** Use compact callouts to surface 2-3 non-obvious things — what might surprise the reader, what's the deeper principle, what's the unwritten constraint.

**When to use:** Whenever you've finished a technical step and want to surface what's *interesting* about it (not just what was done).

**Template:**

```
★ Insight ─────────────────────────────────────
- [Non-obvious technical observation specific to this step]
- [Deeper principle or pattern this connects to]
- [Counterintuitive trade-off or hidden cost worth knowing]
─────────────────────────────────────────────────
```

**Examples from this curriculum:**
- After the Phase 4.5 atomic-config refactor: *"This is the embedding-model version of three operational shapes I've debugged on the cloud-infra side: Argo Workflow with empty artifacts, Lambda 200 with malformed payload, Argo CD `:latest` with stale image."*
- After lab-02b: *"The most subtle teaching moment is in the 'dense-only, not hybrid' callout — LangChain's `RetrievalMode.HYBRID` ≠ BGE-M3's hybrid (different sparse encoder). Same name, different thing."*

**Why it works:** A reader who only reads the first 30 seconds of your output (skimming) gets 80% of the substantive content from a well-written 3-bullet insight. It's the "interview soundbite" pattern applied to technical work.

**Anti-pattern:** Lists of every observation, regardless of importance. The point of the callout is *selection* — only the 2-3 most non-obvious things make it in.

---

## Pattern 7 — Checkpoint Discipline (Don't Grind Past Your Confidence)

**Description:** For multi-hour work, build in explicit checkpoints where you pause and confirm direction with the user. Don't grind 3 hours and present a fait accompli.

**When to use:** Any task projected to take > 1 hour. Insert checkpoints every ~30-60 minutes of work.

**Template:**
> "[X of Y sub-tasks done.] [Concrete result so far.] [Honest assessment.] **Continue with the remaining N, or pause to evaluate?**"

**Examples from this curriculum:**
- After Tier 3 diagram 1 of 7: *"Quality is solid — the layered tower is much more readable than the original Mermaid's 5 boxes. Replacing the Mermaid block in Week 8.md with the image embed. Remaining 6 are real work; honest options A / B / C."*
- After Tier 1 polish 1 of 37: *"Pausing for an honest cost-benefit check before continuing. Most diagrams already have inline styles, so polish on the rest is mostly cosmetic refactor."*

**Why it works:** Three things happen at a checkpoint that don't happen during a grind:
1. The user sees concrete progress and can sanity-check direction
2. You re-evaluate the *remaining* scope with the new information you've gained from the first chunk
3. Mistakes get caught early when they're cheap to fix

**Anti-pattern:** "I'll just finish all 7 first and then show you" — that's how you spend 3 hours building 7 things the user wanted to redirect after the first one.

---

## Pattern 8 — Trade-off Transparency

**Description:** Every recommendation includes **what it costs**, not just what it buys.

**When to use:** Always — there are no free lunches.

**Template:**
> "Recommend X because [benefit]. Cost: [what you lose / what you pay / what gets harder]."

**Examples from this curriculum:**
- *"`langchain-qdrant` gives you drop-in compatibility with chains/agents/retrievers. Cost: BGE-M3 sparse output isn't directly supported — for true hybrid you fall back to native client."*
- *"Hybrid retrieval is the cheap-first alternative to reranking — gets ~70-80% of the lift at ~5% of the latency cost. Cost: still leaves a measurable quality gap that reranking closes."*
- *"Mermaid auto-layout handles complex multi-subgraph diagrams cleanly. Cost: visually less polished than hand-tuned SVG."*

**Why it works:** A recommendation without a cost reads as marketing. A recommendation with explicit cost reads as engineering judgment. The user can then weigh whether the cost is acceptable for their context — you've given them everything they need to decide.

**Anti-pattern:** "X is great because [3 benefits, no costs]." Either you haven't thought about the costs, or you're hiding them. Both are bad signals.

---

## Pattern 9 — Bounded Scope Reduction

**Description:** When a task balloons during execution, **propose a tighter scope explicitly** instead of silently descoping.

**When to use:** When mid-task you realize the original scope is bigger than you estimated, OR that 80% of the value comes from 20% of the work.

**Template:**
> "Original scope was [X items]. After doing [N], I now realize [observation that changes the math]. Proposing tighter scope: [Y items, where Y < X]. The N items I'd skip are [specific items + why they're lower-value]. Continue tighter, or insist on full scope?"

**Examples from this curriculum:**
- *"Originally 30 polish edits across 30 templates. After doing Week 1, I now realize ~25 of the 30 already have inline styles — polish on those is syntax refactor, not visual improvement. Proposing 6 high-value edits instead."*
- *"Originally 7 Tier 3 diagrams. After 4, I now see complex multi-subgraph architectures break down at hand-coded SVG limits. Proposing: keep the 4 simple ones, revert 3 to Mermaid auto-layout."*

**Why it works:** Silent descoping ("I'll just do less and hope nobody notices") is dishonest and damages trust. Explicit descoping ("here's why less is actually right") is engineering discipline.

**Anti-pattern:** Either silently descoping OR completing the full original scope at much higher cost than was justified. Both fail to update on new information.

---

## Pattern 10 — Real Verification (Don't Trust Feedback Without Evidence)

**Description:** When you receive feedback claiming success or failure, **verify against actual evidence** before believing it.

**When to use:** Always, especially when feedback is cheap to produce (hooks, status messages, tool wrapper outputs).

**Template:**
> "[Feedback says X.] Verifying directly with [concrete check]. [Result: matches / contradicts.] [If contradicts: trust the direct evidence, log the false positive/negative.]"

**Examples from this curriculum:**
- The `Edit operation failed` hook noise was a known false negative throughout the entire session. Every Edit actually succeeded. The pattern: trust the actual tool result text, not the hook's secondary commentary.
- After the Nomic stale-cache incident: *"Don't trust exit codes; verify outputs against expected semantics."* The script exited 0, Qdrant said `points_count = 10000`, eval ran to completion — all "success" signals. The actual recall = 0.021 was the only signal that mattered.
- For tier-3 diagrams: validating SVG via `rsvg-convert` was *necessary but not sufficient*. The XML was valid, the visual was broken. Two different verification axes.

**Why it works:** Feedback layers (hooks, exit codes, status messages) have known false-positive and false-negative rates. The actual artifact (the file's contents, the model's output, the rendered image) is the ground truth. Verification cost is usually seconds; the cost of trusting a false positive can be hours of work on broken assumptions.

**Anti-pattern:** "The hook says it succeeded, so it succeeded." Or worse: "The eval script ran without errors, so the recall numbers must be right."

---

## Pattern 11 — Atomic Decision Records (commit the *why*, not just the *what*)

**Description:** When a non-obvious technical decision gets made (especially one that overrides defaults or rejects an alternative), **capture the rationale alongside the decision** — not just in commit messages, but in code comments or doc callouts.

**When to use:** Any time you make a decision that a future reader (or future-you) would otherwise have to reverse-engineer.

**Template:**
- In code: `# X = Y because [non-obvious reason]. Alternative considered: Z, rejected because [reason].`
- In commits: `feat: X. [Why this approach: ...] [What was tried first that didn't work: ...]`
- In docs: `> **Why X not Y?** [The non-obvious trade-off the reader would otherwise have to discover by trying Y first.]`

**Examples from this curriculum:**
- The `model_config.py` per-lab vs shared decision: documented in the spec docstring as *"per-lab spec for portfolio independence; small DRY violation but preserves clone-ability."*
- The "5 spec types instead of 1 over-modeled type" decision: documented in Week 2 §1.1.5 as *"three small specs that carry the fields that must change together for that kind of collection — generic over-modeling defeats the purpose."*
- The hand-coded SVG limits: documented in the revert commit as *"hand-coded SVG without auto-layout breaks down at multi-subgraph complexity. For those, use Mermaid (auto-layout) or Graphviz."*

**Why it works:** Code is read 10× more than it's written. The future reader (or future-you 6 months from now) doesn't have the context you have now. Capturing the *why* alongside the *what* prevents the next person from un-doing your decision because they don't understand what it was protecting against.

**Anti-pattern:** Cryptic commit messages like "refactor X" with no rationale. Six months later, a teammate "cleans up" your decision and re-introduces the bug it was preventing.

---

## Pattern 12 — Evidence-Driven Conversation (don't speculate when you can check)

**Description:** When the user asks a question that has a knowable answer ("does this work?", "is X actually used?"), **check directly** before answering. Don't speculate from memory.

**When to use:** Any time the answer is in a file, in a tool output, or in a quick web search away.

**Template:**
> "Let me check directly. [Read / grep / curl / test.] [Result: ...] [Now I can answer with evidence: ...]"

**Examples from this curriculum:**
- *"Let me verify the curriculum template matches the real src file."* (After user pointed out a possible gap.)
- *"Let me check the actual lab-02 directory state to know what to create vs leave alone."*
- *"Final scan to confirm the curriculum is fully spec-driven across all Week 2 templates."*

**Why it works:** Speculation is fast but unreliable. Direct checking is slower per-instance but compounds: by checking, you build a more accurate mental model, which makes your future answers faster AND more reliable. The user can also see the check happen, which builds confidence in the answer.

**Anti-pattern:** "I think it should work" / "Probably yes" — when the actual check is one tool call away, speculation is engineering laziness disguised as efficiency.

---

## Pattern 13 — Storage-Scale Match (right backend for current scale, no premature scaling)

> Distilled 2026-05-07 from [[Week 2.7 - Structure-Aware RAG#Production Considerations — Storage, Concurrency, Observability]]. Generalizes beyond tree-index — applies to any persistent-state decision (vector indexes, graph data, eval harnesses, agent memory).

**The pattern.** When a system has multiple storage candidates (filesystem / SQLite / Postgres / object store / cache layer), match the choice to the *current* scale, not the *eventual* scale. Build the decision boundary around concrete numbers (doc count, QPS, concurrency, dataset size), not vibes. Three or four scale tiers with explicit thresholds beat one "production-ready" backend that's wrong for both prototype and prod.

**Three-tier template:**

| Scale | Backend | Why |
|---|---|---|
| **Dev / lab / single-user** | Local filesystem (JSON / SQLite / disk file) | Operational simplicity. `git diff` shows changes; full rebuild is one command; zero infrastructure. |
| **Single-tenant prod (10–1,000 units)** | SQLite or Postgres `jsonb` / on-disk index | Concurrent reads. Per-record version history. ACID. No multi-tenancy load yet. |
| **Multi-tenant prod (1,000+ units, multi-user)** | Postgres + S3/blob + Redis cache | Tier the storage by access pattern. Hot in cache, warm in DB, cold in object store. |

**Decision matrix specifics from W2.7 tree-index:**

| Artifact | Property | Storage choice |
|---|---|---|
| `tree.json` (50–100 KB, hierarchical, read-mostly) | Document-shape, indexable JSON | Filesystem → Postgres `jsonb` (with index on `tree -> 'title'` for cross-doc title search) |
| Source PDF (10s–100s MB, immutable, page-range access) | Append-only blob | Filesystem → S3 with byte-range reads + Redis LRU cache for hot ranges |
| Cross-document index | Doc registry | None → SQLite → Postgres |

**Why it works.** A premature production backend forces *every* developer running the lab to bring up infrastructure that has no value at single-user scale (Postgres for one document is theatrical). A premature filesystem backend at 1,000-doc scale destroys concurrency. The match-to-scale decision lets each user pay only for the complexity their scale actually demands. The abstraction seam (in W2.7's case, the `page_provider` Protocol) is what makes scale transitions cheap — same `AgenticTreeRetriever` works against any of the three storage tiers; only the closure around the page fetch changes shape.

**Anti-pattern A — premature production scaffolding.** "We might scale to 100K docs someday, so let's start with Postgres + S3 + Redis." Now every developer setting up the lab needs three services running. The next 6 months of dev time is spent fighting infrastructure for the value of "we're production-ready" — which is fictional value if you have one user.

**Anti-pattern B — locked-in dev simplicity.** Filesystem-only design that has no abstraction seam between storage and the application logic. When you DO need to scale, the lift is a multi-week refactor, not a single closure swap. The fix at design time: introduce the seam (Protocol, callable, ABC) even if the filesystem implementation is the only one shipped. The seam is free; the absence of the seam costs a refactor.

**Anti-pattern C — wrong backend for the data shape.** Common mistake: putting structurally non-vector data (a tree, a graph, an event log) into a vector database because that's the database the project already runs. Vector DBs are for embeddings; trees go in jsonb / document stores; graphs go in graph DBs; event logs go in append-only logs. The blast radius is silent — the system "works" but every read pays JSON ↔ vector conversion overhead and cross-record queries break.

**5-second sanity test before adopting a backend:**
1. **What's the unit of work?** If hierarchical → document store / jsonb; if relational multi-hop → graph DB; if embedding similarity → vector DB; if append-only event → log store; if immutable blob → object store.
2. **What's the access pattern?** Read-mostly per-record vs read-many cross-record; concurrent vs single-writer; hot-tail vs uniform.
3. **What's the concurrency requirement?** 1 reader = file is fine. Multiple concurrent writers = need ACID. Multiple processes reading + occasional writes = SQLite is fine until QPS > ~100.
4. **What's the data size at the upper end of the current tier?** Filesystem fine to ~100 GB; SQLite to ~10 GB; Postgres jsonb to ~1 TB. Above those, scale tier up.

**See also:**
- Pattern 9 — Bounded Scope Reduction (don't bring production-grade infrastructure into a dev-grade lab; reduce scope to fit current need)
- Pattern 8 — Trade-off Transparency (state the rejected alternatives in the decision record so future-you knows why filesystem was chosen at first)
- Pattern 11 — Atomic Decision Records (commit the *why* the storage tier was picked, not just the choice)

---

## Meta-pattern: How these patterns interact

| Pattern | When in the work cycle | Prevents |
|---|---|---|
| 1 — Scope-Estimate | Before starting | Silent scope creep |
| 2 — Options Table | When multiple paths | Wrong-direction commitment |
| 3 — Always Recommend | Whenever options presented | User cognitive overload |
| 4 — Mid-Stream Pivot | During execution | Sticky-progress fallacy |
| 5 — Catch + Acknowledge | After mistakes | Trust erosion |
| 6 — ★ Insight Callouts | After technical step | Important things getting buried |
| 7 — Checkpoint Discipline | Every 30-60 min of work | Late-stage discovery of wrong direction |
| 8 — Trade-off Transparency | In every recommendation | Marketing-speak masquerading as engineering |
| 9 — Bounded Scope Reduction | When task balloons | Sunk-cost completion of low-value work |
| 10 — Real Verification | When feedback received | Trusting false signals |
| 11 — Atomic Decision Records | When decision is made | Future-self / future-team un-doing the decision |
| 12 — Evidence-Driven | When question can be checked | Speculation-as-laziness |
| 13 — Storage-Scale Match | Picking persistent-state backend | Premature production scaffolding / locked-in dev simplicity |

These patterns compound. The teams (or solo engineers) who use them feel "calm and deliberate" to work with; the ones who don't feel "frantic and surprising." The difference isn't IQ or experience — it's the discipline of slowing down at the right 5-10% of moments.

---

## When NOT to use these patterns (over-engineering risk)

These patterns add overhead. For *truly small* work, the overhead is wasted:
- A 5-minute task doesn't need a scope estimate
- A one-liner change doesn't need an options table
- A trivial verification doesn't need a checkpoint

**Heuristic:** if the entire task is under 30 minutes and the result will be visible immediately, skip the patterns and just do it. The patterns are for **ambiguous, multi-step, time-substantial** work — they're insurance against the mistakes that get expensive at scale.

The cost of patterns isn't zero. The art is knowing when the insurance is worth it.

---

## See also

- [[Bad-Case Journal]] — captures *post-failure* lessons; this doc captures *pre-failure* discipline
- Week 1 [[Week 1 - Vector Retrieval Baseline#Phase 4.5 — Atomic Config Refactor]] — Pattern 11 in action (atomic decision records via the spec)
- Week 2 [[Week 2 - Rerank and Context Compression#Concept 5: Production Libraries — When to Stop Writing Primitives]] — Pattern 8 in action (trade-off transparency for library adoption)

---

— end —
