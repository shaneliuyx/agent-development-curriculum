---
tags: [agent-curriculum, meta-skills, decision-making, working-with-ai, multi-agent, delegation]
created: 2026-04-28
updated: 2026-05-19
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

**See also:**
- Pattern 7 — Checkpoint Discipline (scope-estimates compound — restate the estimate at each checkpoint)
- Pattern 9 — Bounded Scope Reduction (the scope-estimate is also the *renegotiation contract* if the work balloons)
- Pattern 4 — Mid-Stream Pivot (a pivot is, mechanically, replacing one scope-estimate with another)

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

**See also:**
- Pattern 3 — Always Recommend (every options table comes with a recommendation; never offload the pick)
- Pattern 8 — Trade-off Transparency (each row's trade-off column makes cost visible)
- Pattern 16 — Multi-Axis Comparison Table (the 2D generalization of this 1D options table)

---

## Pattern 3 — Always Recommend; Never Be Neutrally Sycophantic

**Description:** Every options-table includes a recommendation with rationale. The user can override; you don't pre-emptively defer.

**When to use:** Any time you present > 1 option.

**Template:**
> "My recommendation: **X** because [trade-off reasoning]. If [different priority], pick Y instead."

**Why it works:** "Here are 3 options, what would you like?" shifts cognitive load to the user — they have to evaluate all 3 themselves. "I recommend A because it's the highest-leverage trade-off; pick B if you care more about Z" lets the user accept your judgment in 1 second OR override in 1 sentence. Same information, half the decision time.

**Anti-pattern:** "Whatever you prefer" / "I can do either" — feels respectful, actually wastes time. The expert is supposed to have an opinion.

**Sub-rule:** If you GENUINELY don't have a recommendation (rare — usually means scope is unclear), say so explicitly: "I don't have a strong recommendation here because [reason]. Either path is defensible; what's your priority?" That's different from sycophantic neutrality.

**See also:**
- Pattern 2 — Options Table (recommendation is the row your finger points at)
- Pattern 8 — Trade-off Transparency (explicit cost on each option lets the user *override* the recommendation in 1 sentence)
- Pattern 4 — Mid-Stream Pivot (the recommendation can shift mid-work; surface that, don't bury it)

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

**See also:**
- Pattern 7 — Checkpoint Discipline (pivots happen at checkpoints, not in the middle of grind)
- Pattern 9 — Bounded Scope Reduction (often the pivot IS a scope reduction)
- Pattern 12 — Evidence-Driven Conversation (a pivot is justified by new evidence, not by feeling)

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

**See also:**
- Pattern 10 — Real Verification (catching often comes from independent verification, not from re-reading your own work)
- Pattern 11 — Atomic Decision Records (the catch + its rationale is itself a decision record)
- Pattern 20 — Real-Data-Only Discipline (a "caught" bad-case journal entry is more credible than a hypothetical one)

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
- *After W3.5.8 §3.4 audit-log primitive (2026-05-19):* the 3-bullet insight callout calling the audit log a "schema canary" (a truly fresh `imprint` MUST emit `target_id=null`; otherwise the dedup classifier upstream silently leaked a phantom candidate) — the entire bug class is named in one bullet, more useful than 200 lines of prose.
- *After W4.6 §2.5 trigger × topology synthesis (2026-05-19):* the insight "the 8 questions are the inverse of the 7 anti-patterns" — surfaces a load-bearing symmetry that took 30 seconds to write but reframes the entire chapter for future readers.

**Why it works:** A reader who only reads the first 30 seconds of your output (skimming) gets 80% of the substantive content from a well-written 3-bullet insight. It's the "interview soundbite" pattern applied to technical work.

**Anti-pattern:** Lists of every observation, regardless of importance. The point of the callout is *selection* — only the 2-3 most non-obvious things make it in.

**See also:**
- Pattern 8 — Trade-off Transparency (the third bullet of an insight callout is often the hidden cost)
- Pattern 11 — Atomic Decision Records (insights are the prose form of decision records)
- Pattern 16 — Multi-Axis Comparison Table (a 3-bullet insight can summarize what a 4×6 grid showed)

---

## Pattern 7 — Checkpoint Discipline (Don't Grind Past Your Confidence)

**Description:** For multi-hour work, build in explicit checkpoints where you pause and confirm direction with the user. Don't grind 3 hours and present a fait accompli.

**When to use:** Any task projected to take > 1 hour. Insert checkpoints every ~30-60 minutes of work.

**Template:**
> "[X of Y sub-tasks done.] [Concrete result so far.] [Honest assessment.] **Continue with the remaining N, or pause to evaluate?**"

**Examples from this curriculum:**
- After Tier 3 diagram 1 of 7: *"Quality is solid — the layered tower is much more readable than the original Mermaid's 5 boxes. Replacing the Mermaid block in Week 8.md with the image embed. Remaining 6 are real work; honest options A / B / C."*
- After Tier 1 polish 1 of 37: *"Pausing for an honest cost-benefit check before continuing. Most diagrams already have inline styles, so polish on the rest is mostly cosmetic refactor."*
- *During W3.5.8 audit-log buildout (multi-session, 2026-05-14 → 2026-05-19):* checkpoint after each phase landed in the chapter (§3.1 baseline → §3.2 tests → §3.3 quality gate → §3.4 audit primitive → §9.7 wire-in). Each checkpoint surfaced new scope (test coverage, simplifier pass, on-disk fidelity sync) that would have buried a single-session attempt.
- *Mid-restructure of W3.5.8 §3.4 → §9.7 (2026-05-19):* paused after the section move to ask user whether to slim §3.4 in-place vs relocate entirely. The 60-second pause prevented committing a ~1000-line restructure to the wrong shape.

**Why it works:** Three things happen at a checkpoint that don't happen during a grind:
1. The user sees concrete progress and can sanity-check direction
2. You re-evaluate the *remaining* scope with the new information you've gained from the first chunk
3. Mistakes get caught early when they're cheap to fix

**Anti-pattern:** "I'll just finish all 7 first and then show you" — that's how you spend 3 hours building 7 things the user wanted to redirect after the first one.

**See also:**
- Pattern 1 — Scope-Estimate (checkpoints are scope-estimates mid-work)
- Pattern 4 — Mid-Stream Pivot (checkpoints are where pivots become possible)
- Pattern 9 — Bounded Scope Reduction (checkpoints often surface the case for tightening scope)

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

**See also:**
- Pattern 2 — Options Table (the trade-off column IS the transparency)
- Pattern 3 — Always Recommend (a recommendation without a cost reads as marketing)
- Pattern 11 — Atomic Decision Records (the trade-off + rejected alternative gets committed alongside the choice)
- Pattern 14 — Delegation Contract (the Forbidden field is where the trade-off becomes a written constraint)

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

**See also:**
- Pattern 4 — Mid-Stream Pivot (often the reduction *is* the pivot)
- Pattern 7 — Checkpoint Discipline (the reduction usually surfaces at a checkpoint)
- Pattern 13 — Storage-Scale Match (the storage version of "don't over-build for scale you don't have yet")

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
- *After §3.4 audit log fix (2026-05-19):* hook returned `Edit operation failed` (false negative — Edit actually succeeded). Trusted the tool result text + grep verification over the hook commentary. Pattern: tool-call result > hook secondary commentary > exit codes.
- *After simplifier-loop run on `dedup_synthesis.py` (2026-05-19):* simplifier subagent's environment was missing `OPENAI_API_KEY` so test 4 looked like it failed for unrelated reasons. Re-ran with proper `.env` sourced — 8/8 pass. The simplifier's failure report was unreliable; the direct test run was ground truth.
- *After consolidation gate-audit test regression (2026-05-19):* test passed once, then failed identically on re-run. Root cause was *not* re-running the same code but leftover SQLite rows from prior test run that the `patch()` couldn't reach (default-arg bug). The retry-and-it's-different signal pointed at state contamination, not at flaky code.

**Why it works:** Feedback layers (hooks, exit codes, status messages) have known false-positive and false-negative rates. The actual artifact (the file's contents, the model's output, the rendered image) is the ground truth. Verification cost is usually seconds; the cost of trusting a false positive can be hours of work on broken assumptions.

**Anti-pattern:** "The hook says it succeeded, so it succeeded." Or worse: "The eval script ran without errors, so the recall numbers must be right."

**See also:**
- Pattern 5 — Catch + Acknowledge (verification often produces the catch)
- Pattern 12 — Evidence-Driven Conversation (verification IS evidence-driven; this pattern is the after-the-fact half, Pattern 12 is the before-the-fact half)
- Pattern 20 — Real-Data-Only Discipline (the BCJ-specific application of this principle)

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
- *W3.5.8 §3.4 forward-link panel (2026-05-19):* the `Forward-links — where the rest of the 9-op AuditEntry surface lands` panel IS a decision record — it commits to a specific deferral schedule (§9.7 for wire-in, §7.2 for UUID fix, §10.3 for replay). A future reader who wonders "why isn't this complete here?" finds the answer inline rather than reverse-engineering from the section sequence.
- *`_ensure_dedup_table` default-arg fix (2026-05-19):* the 4-line `# Resolve default at CALL time so tests can monkeypatch...` comment block IS Pattern 11 in action. Future maintainers who see `if db_path is None:` won't "simplify" it back to the broken form because the comment names the test-isolation invariant being protected.
- *Pattern 14 source-line (2026-05-19):* citing Russell (2026) as the synthesis source instead of presenting the 8-field template as universal wisdom — both gives credit and lets future-readers fetch additional context from the original article when nuances matter.

**Why it works:** Code is read 10× more than it's written. The future reader (or future-you 6 months from now) doesn't have the context you have now. Capturing the *why* alongside the *what* prevents the next person from un-doing your decision because they don't understand what it was protecting against.

**Anti-pattern:** Cryptic commit messages like "refactor X" with no rationale. Six months later, a teammate "cleans up" your decision and re-introduces the bug it was preventing.

**See also:**
- Pattern 8 — Trade-off Transparency (the trade-off + rejected alternative is what gets recorded)
- Pattern 14 — Delegation Contract (every populated contract is itself a decision record)
- Pattern 15 — Read-Side / Write-Side Mirror Design (decisions about contracts often have a read-side replay form)

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
- *Before each W3.5.8 chapter sync edit (2026-05-19):* `grep -n` for the exact line numbers of stale references before doing any restructure. The grep output IS the evidence; the edit list is the action. Pattern: evidence first, action second.
- *During EDP audit (2026-05-19, this very edit cycle):* reading the whole EDP file before proposing new patterns, rather than guessing what's already covered from memory. The full read surfaced that Patterns 13-14 had "See also" sections but 1-12 didn't — a uniformity gap that wouldn't have shown up in a memory-driven audit.

**Why it works:** Speculation is fast but unreliable. Direct checking is slower per-instance but compounds: by checking, you build a more accurate mental model, which makes your future answers faster AND more reliable. The user can also see the check happen, which builds confidence in the answer.

**Anti-pattern:** "I think it should work" / "Probably yes" — when the actual check is one tool call away, speculation is engineering laziness disguised as efficiency.

**See also:**
- Pattern 10 — Real Verification (after-the-fact evidence-driven; Pattern 12 is the before-the-fact form)
- Pattern 5 — Catch + Acknowledge (failing to check produces silent errors that later require a catch)
- Pattern 20 — Real-Data-Only Discipline (evidence-driven applied specifically to BCJ entries)

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

## Pattern 14 — Delegation Contract Template (brief subagents like new hires, not like teammates)

**When it applies:** any time a parent agent spawns a child / worker / subagent / delegate. Codex `Use parallel subagents`, Claude Code `description`-routed subagent, Hermes `delegate_task`, OpenClaw `/subagents spawn`, in-house `crew.kickoff`-style orchestrators — same pattern.

**Failure mode this prevents:** the *single most common* multi-agent failure mode in the wild — "subagents know nothing" (Hermes docs phrase, 2026). A parent agent has the full project context in its head; the child gets only what the parent decides to pass in. Saying `"fix the auth bug"` to a fresh child is the same as DM'ing `"fix the auth bug"` to a new hire on day one. They will guess, and the cost of guessing wrong is paid in token spend, time, AND main-context contamination when the wrong patch comes back.

**The 8-field contract** — fill every field for every delegation, even if the answer is `"none"`:

```text
Role:               you are a <read-only auth explorer | scoped implementation worker | security reviewer | …>
Goal:               what to answer or complete; what the boundary is
Context:            project paths, relevant files, error reproduction, user goal, judgements already made
Allowed actions:    which files readable; can run shell; can write files; can hit network
Ownership:          if writes are allowed, which directories / files are within bounds
Forbidden actions:  do-not-modify list; do-not-refactor list; do-not-ask-user; do-not-spawn-child
Output format:      findings / patch summary / test result / confidence / open questions
Stop condition:     what counts as done; when to stop and report blocked
```

**Why each field is load-bearing:**

- **Role** sets the persona priors. `read-only auth explorer` and `scoped implementation worker` produce different code even with identical Goal + Context.
- **Goal** is the contract. If the parent can't write it in one sentence, the parent doesn't know what it wants — spawning a child won't fix that.
- **Context** is what the child knows. Everything not in Context, the child guesses. Production rule: the child should never have to ask the user a clarifying question; if the parent omitted critical context, that's a parent bug, not a child bug.
- **Allowed actions** + **Ownership** + **Forbidden actions** are the sandbox. They are NOT redundant with each other: Allowed = capability gate (can-it), Ownership = scope gate (where-can-it), Forbidden = explicit anti-goal (don't-do-this-even-though-you-can). Codex's `agents.sandbox` config maps to Allowed; Hermes's `leaf` worker restrictions map to Forbidden.
- **Output format** is the merge contract. If the parent has to free-text-parse the child's response, the parent's reduce phase becomes the new bottleneck. Pre-declare the shape; child returns structured fields.
- **Stop condition** prevents two failure modes: child runs forever because "done" isn't defined; child stops at the first plausible answer because "good enough" isn't defined. Explicit stop conditions also enable retry semantics in durable systems like Hermes Kanban.

`★ Insight ─────────────────────────────────────`
- **The 8 fields ARE the audit log schema.** Compare to the AuditEntry primitive (W3.5.8 §3.4): `actor_agent_id` = Role, `payload_summary` = Goal+Context distilled, `metadata` = Allowed/Ownership/Forbidden/Output, `target_id`+`new_id` = Stop-condition outcome. Write-time contracts and read-time replay are two views of the same data.
- **Filling all 8 fields takes ~30 seconds and saves ~5 minutes per botched delegation.** If a child returns nonsense, look at the contract first: which of the 8 fields was empty or vague? That field is the bug. ~80% of cases will be Context (parent assumed shared state that doesn't exist) or Forbidden (parent didn't constrain blast radius).
- **Topology choice is downstream of the contract, not upstream.** Star fan-out / pipeline / mesh / durable-board don't change whether the contract is needed; they only change how many copies of the contract get written per task. A team-mesh with 4 teammates needs 4 contracts. A solo subagent needs 1. None of them work with 0.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 2 — Options Table (the Role + Allowed-actions section is essentially a 1-row options table for "which kind of worker am I dispatching?")
- Pattern 8 — Trade-off Transparency (the Forbidden-actions field is where you make the trade-off explicit — saying "you can't refactor adjacent code" is also saying "we accept the tech debt for now")
- Pattern 11 — Atomic Decision Records (every populated delegation contract IS a decision record — log it alongside the run)
- W3.5.8 §3.4 — AuditEntry primitive (the read-side mirror of this write-side contract)
- W4.6 — Durable Agent Runtime and Process Topologies (where the topology choices that *use* this contract are catalogued)
- W6.5 — Hermes (where "subagents know nothing" lives as a load-bearing maxim)

**Source:** synthesized from Russell (2026), *多智能体协作调查：Agent 到底该怎么分工* — engineering survey of Codex / Claude Code / OpenClaw / Hermes delegation patterns. The 8-field template combines field names used across all 4 systems into one normative shape.

---

## Pattern 15 — Read-Side / Write-Side Mirror Design (events ↔ commands; audit ↔ contract)

**When it applies:** designing a system where state-mutating *commands* (what an agent decides to do) and *events* (the durable record of what happened) coexist. Multi-agent orchestrators, durable workflow engines, eval pipelines, CQRS-shaped backends, audit-logged services.

**The pattern.** When a write path and a read path both touch the same state, design them as *mirrors* of each other — the fields the writer is asked to fill ARE the fields the reader will surface. Mismatch between the two surfaces is the most common source of "we have logs but we can't replay" / "we have inputs but the eval can't see the decision."

**Canonical example from this curriculum:** the W3.5.8 §3.4 `AuditEntry` (read-side replay log) IS the 8-field [[Engineering Decision Patterns#Pattern 14 — Delegation Contract Template]] (write-side parent → child briefing) seen from the other direction. Field-by-field:

| Write-side (Delegation Contract) | Read-side (AuditEntry) | Why they pair |
|---|---|---|
| Role | `actor_agent_id` | who did this |
| Goal | `payload_summary` (first 120 chars) | what was the ask |
| Context | distilled into `payload_summary` + run metadata | what the worker knew |
| Allowed actions | `metadata.allowed_*` | capability gate |
| Ownership | `metadata.scope` or implicit in `target_id` | where the action landed |
| Forbidden actions | `metadata.forbidden_*` (if logged) | anti-goal gate |
| Output format | `metadata.output_kind` + the entry's `new_id`/`target_id` schema | shape contract |
| Stop condition | `metadata.stop_reason` + the operation's terminal state | when "done" was declared |

**Other curriculum instances:**
- W3.5.8 Phase 9.6 supersede / coexist actions (write) ↔ Phase 10.3 `replay_audit` (read) — same 9-operation Literal Union.
- W11.6 cost-telemetry tags written at request time (write) ↔ DuckDB rollup queries at billing time (read) — every tag the writer emits becomes a column the reader can group by.
- W11.8 CT pipeline training-data extraction (read) ↔ the audit log it consumes (write) — the writer's `metadata.quest_id` is what lets the reader reconstruct the gate→imprint chain.

**Why it works.** Most systems get the write side designed first (because that's where the action lives) and then the read side is "whatever fields we happened to capture." Mirror design flips this: pre-declare the read shape FIRST (what queries / replays / aggregations does downstream need?), then mechanically derive the write contract. Every read query unsupported by the write schema is a *missing field*, not a "we'll add ETL later" problem.

`★ Insight ─────────────────────────────────────`
- **The most expensive failure is silent**: a write-side field that the read side never references — pure overhead, but harmless. The expensive failure is the *inverse*: a read-side query that has no write-side column, discovered three months later when you need to debug a production incident. Mirror design catches the inverse mismatch at design time.
- **CQRS, event sourcing, audit logging, and "structured logging" are all instances of this pattern.** They differ in the shape of the read side (snapshots vs streams vs aggregates) but share the requirement that the writer-emitted schema is the reader-consumed schema.
- **Mirror design is what makes Pattern 14 + W3.5.8 §3.4 *one decision*, not two**. The 8-field delegation contract is the writer side of the same primitive whose reader side is AuditEntry. Doing one without the other leaves a gap a future maintainer will silently fall into.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 14 — Delegation Contract Template (the write-side surface for the multi-agent case)
- Pattern 13 — Storage-Scale Match (storage choice determines what kind of mirror is even possible — append-only log vs row-update vs document store)
- W3.5.8 §3.4 — AuditEntry primitive (the read-side mirror, fully implemented)
- W11.6 — Production Tracing and Cost Telemetry (write-time tags ↔ read-time rollups, applied to billing)

---

## Pattern 16 — Multi-Axis Comparison Table (when the world is 2D, don't draw a list)

**When it applies:** explaining or deciding across two or more orthogonal dimensions. Anytime you catch yourself writing a long list and then qualifying each item with "but this also depends on X" — that's the cue to draw the 2D grid instead.

**The pattern.** Pattern 2 (Options Table) is the 1D ancestor: rows = options, columns = facets (time / trade-off / recommendation). Pattern 16 is the 2D generalization: rows = one axis, columns = the other axis, cells = the meaningful combination. Two-axis tables turn implicit "if A and B then Z" reasoning into explicit cell-by-cell coverage.

**Curriculum instances** — each is a non-trivial decision the table made cheap:

| Where | Axis 1 | Axis 2 | What the table surfaced |
|---|---|---|---|
| W4.6 §2.5 (Russell 2026) | 4 trigger types (explicit / semantic / routing / queue) | 6 topology types (single / star / pipeline / tree / mesh / gateway / durable-board) | Most cells are *empty* in production; the empty cells are where engineers shouldn't ship novel combinations |
| W7.7 quantization | 3 weight regimes (full / 8-bit / 4-bit) | N quant techniques (GPTQ / AWQ / SmoothQuant / NF4 / SqueezeLLM / EXL2) | Cells expose technique-regime fit; uncovered cells = "use a different technique" |
| W3.5.8 §3.4 op×field matrix | 9 audit operations (imprint / promote / demote / update / supersede / coexist / delete / noop_duplicate / compact) | 2 ID fields (target_id / new_id) | Field semantics differ per op; one ID field = lost edge |
| Pattern 13 — Storage-Scale Match | 3 scale tiers (dev / single-tenant prod / multi-tenant prod) | N artifact types (tree.json / source PDF / cross-doc index) | Storage choice changes per axis combination, not just per artifact |
| W6.5 Hermes | 2 primitives (`delegate_task` RPC / Kanban durable queue) | 2 lifecycles (in-turn / cross-turn) | Right-cell / wrong-cell is the difference between RPC-misused-for-long-work and Kanban-overengineered-for-30-seconds |

**Design rules for the grid:**

1. **Cells contain *information*, not "yes/no".** A cell that just says "✓" is a 1D table in 2D disguise. Each cell should carry the *consequence* of that axis combination: a number, a system name, a failure mode, a recommendation.
2. **Empty cells are signal.** If 7 of 24 cells are empty, the table is also telling you "these 7 combinations have no good production precedent" — which is itself useful for the reader debating whether to ship a novel combination.
3. **Order axes by what's easier to recognize.** The axis the reader sees first (rows) should be the one they can identify about their own situation; the second axis (columns) is the one they need help thinking about. Russell's 4×6 puts trigger first because triggers are observable (you can name which kind your system has); topology second because topology is a choice (you can still pick).
4. **Don't draw a 2D table for 1D data.** If every row's columns vary only along one dimension, collapse it back to Pattern 2. The grid earns its complexity only when both axes genuinely vary.

`★ Insight ─────────────────────────────────────`
- **The grid IS the analysis.** Drawing it forces you to fill every cell or admit you don't know one. The empty cells are not "TODO" — they're "this combination is rare in practice, here's the design space the reader should think twice before entering."
- **Most chapter-zero multi-agent literature collapses Russell's 4×6 to a single 1D list of "topologies."** Reading that list, you can't tell which trigger they implicitly assume. Drawing the grid makes the assumption visible.
- **The 2D table is the upper bound for clarity; 3D is rarely worth it.** If you find yourself wanting axes 3 and 4, the better move is usually two separate 2D tables with one shared axis. Three orthogonal dimensions exceeds working memory.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 2 — Options Table (the 1D ancestor)
- Pattern 6 — ★ Insight Callouts (a 3-bullet insight often summarizes what the grid showed)
- Pattern 14 — Delegation Contract Template (the 8 fields are themselves a 1D collapse of a 2D capability × scope grid)
- W4.6 §2.5 — 4-trigger × 6-topology design space (canonical example)

---

## Pattern 17 — Forward-Link Panel for In-Flight Sections (declare the deferral, don't hide it)

**When it applies:** any chapter / section / module that *introduces a primitive* but won't fully wire it up until later. Common in pedagogical writing, layered architectures (interface declared at layer 1, implementation lands at layer 4), and roadmap docs.

**Failure mode this prevents:** the silent forward-reference — the section reads naturally to a writer who knows the whole story, but stops a first-time reader cold ("wait, what does *noop_duplicate* mean? It hasn't been introduced yet"). The reader either jumps forward (breaking flow) or skims (eroding trust). Either way, the section's pedagogy fails.

**The template.** When a section needs to forward-reference, replace silent gaps with an *explicit declarative panel*:

```text
**Forward-links — where the rest of the X surface lands:**

- **<Concept A that's only partially shown here>**: full treatment lands in §N (after prereq P is grounded).
- **<Concept B that's referenced but not built>**: shipped in §M alongside <where it's used>.
- **<Concept C that this section's tests would need>**: drop-in below; the primitive declaration above is the only piece you need at this point.

<One-sentence reassurance that the next sub-block is self-contained given what's been grounded so far.>
```

**Canonical curriculum example (W3.5.8 §3.4, 2026-05-19 restructure):** the AuditEntry primitive is *declared* at §3.4 (first writer is the §3.3 quality gate), but the full 9-op wire-in lands at §9.7 (after Phase 9 dedup grounds the other 6 ops). Forward-link panel in §3.4 declares: §9.7 has the wire-in, §7.2 has the Qdrant point-UUID surfacing, §10.3 has the replay primitive, and the BCJ MA-7 entry justifies the entire primitive's existence. Reader at §3.4 sees the contract upfront; reader at §9.7 sees the panel had told them to expect this section.

**Other curriculum instances:**
- W4.6 §1 forward-links to specific Phase implementations of each topology — the reader knows which Phase makes each topology runnable.
- W6.5 Hermes §1 forward-links delegate_task RPC (immediate) vs Kanban (later subsection) so the lifecycle split is visible from the chapter's opening.

**Design rules for the panel:**

1. **Sit it where the gap opens.** Not at chapter top, not at footer — inline at the exact point the reader would otherwise hit silence.
2. **Each forward-link names *both* the target section AND the prereq it's waiting on.** "Full execute_action wire-in ships in §9.7 (after dedup-and-synthesis is grounded in §9.1)." The prereq tells the reader *why* the deferral exists, not just where it resolves.
3. **End with a self-containment claim.** The panel's last sentence should be "the section that follows uses ONLY <subset> of the surface, so it's self-contained given what's been grounded so far." Without that claim, the panel reads as "this section is incomplete"; with it, the panel reads as "this section is *complete for what it's trying to do*."

`★ Insight ─────────────────────────────────────`
- **Forward-link panels are the doc equivalent of TypeScript's `declare` keyword** — they tell the reader the symbol exists and what shape to expect, even though the implementation lives elsewhere. Without `declare`, the type checker errors; without forward-link panels, the reader errors.
- **The panel makes the chapter's *information flow* visible.** Reader sees: "primitive declared here → 3 forward-links → primitive used in subsection below → full wire-in in §N → replay in §M." That's a graph, not a linear narrative — and forward-link panels are the only way to render the graph inside linear markdown.
- **Don't use forward-link panels for *missing* content** — those are TODOs, and they belong in a separate "Open Questions" or "Future Work" section. Forward-link panels are specifically for content that exists, is grounded later in the same document, and is needed by the reader to understand why a section is incomplete *on purpose*.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 11 — Atomic Decision Records (the panel IS a decision record: "we chose to defer X to §N because Y")
- Pattern 18 — Spec/Disk Fidelity for Pedagogical Code (forward-link panels prevent the chapter from drifting ahead of disk truth)
- W3.5.8 §3.4 — canonical implementation of the forward-link pattern

---

## Pattern 18 — Spec/Disk Fidelity for Pedagogical Code (chapter ≡ on-disk; copy-paste must run)

**When it applies:** any pedagogical writing where code blocks are also meant to be runnable. Curriculum chapters, tutorial blog posts, framework docs, README quickstarts, training material.

**Failure mode this prevents:** chapter and disk silently drift. Chapter says `record_audit(audit, log_path)` (path-required); disk implementation is `record_audit(audit, log_path=None)` (optional). Reader copy-pastes the chapter version → import-error or runtime breakage. Reader copy-pastes the disk version → loses the contextual comments only the chapter has. Both reads of the same "source of truth" produce different results. *This is the most common silent failure in long-running curriculum projects.*

**The discipline.**

1. **One artifact is canonical.** Either on-disk code is canonical (chapter renders it verbatim with annotations), or the chapter is canonical (the disk file is regenerated from chapter blocks via a build step). Pick one. Never both.
2. **Where they MUST differ (pedagogical simplification, type-stub baselines, alternate-language ports), declare the divergence inline.** Use comments like `# Pedagogical simplification: real code has 4 more validation branches; see disk for prod-grade`. The divergence is named.
3. **Sync as a separate commit per section.** When code changes on disk, sync the chapter in a single follow-up commit titled `docs(<week>): sync § N.M to disk — <one-line>`. Diff-able, revertable, audit-trail-able.
4. **Forward-link panels (Pattern 17) document expected drift.** When chapter intentionally shows a *baseline* form of code that disk has already evolved past, the forward-link panel says "§3.4 shows baseline primitive; full evolved version lives in §9.7." Drift is named, not silent.

**Curriculum instances:**

- W3.5.8 §3.4 audit.py block (chapter) ↔ `src/audit.py` on disk: baseline declaration matches; full evolution is at §9.7. Verified by the 2026-05-19 sync pass.
- W3.5.8 §3.4 gate-audit wire-in block ↔ `src/consolidation.py`: chapter has `# AUDIT (§3.4):` markers at the 5 emission sites; disk has the same markers. Reader copy-paste produces identical behavior.
- W3.5.8 §7.2 Qdrant `query_context()` ↔ `src/tiered_memory_qdrant.py:208`: chapter has `"id": hit["id"]` line; disk has it; the §7.2 forward-link explains *why* (downstream consumer is §9.7 audit log).
- W4.5 Phase 4 vote layer ↔ `lab-04-5-routing/src/vote.py`: per-block bundle is verbatim from disk plus walkthrough; the walkthrough explains *why* each block, not *what*.

**Anti-pattern A — chapter as marketing-copy.** Chapter shows a polished `record_audit(entry)` call without the `log_path or DEFAULT_AUDIT_PATH` resolution that disk actually uses. Reader pastes; their tests fail; they assume their setup is broken. The chapter looked cleaner but cost the reader 30 minutes of debugging.

**Anti-pattern B — disk as scratch-pad.** Disk has 6 commits' worth of fix-iteration history (`fix typo`, `revert that`, `try again`); chapter rendered the first version and never re-synced. The reader's copy-paste matches commit 1; production matches commit 6. The bug they hit was already fixed — they just can't tell from the chapter.

**Anti-pattern C — naming the file but not pasting it.** Chapter says "the implementation lives at `lab-04-6/src/scheduler.py`" without showing the code. Reader has to navigate to GitHub, find the right commit, copy from there. Every layer of indirection erodes the chapter's value as a self-contained teaching unit. CLAUDE.md's "complete runnable code per phase" rule exists specifically to prevent this.

`★ Insight ─────────────────────────────────────`
- **The annotation discipline (Pattern 18) is what makes Pattern 17 (forward-link panels) work.** Without inline `# NEW (§N)` / `# CHANGED (§N)` markers, the reader can't tell which lines of a "complete drop-in" block are new since the last section. Markers turn the code block into a self-contained diff.
- **Sync commits are cheap; sync skips are expensive.** A 5-minute "sync § N.M to disk" commit prevents the 30-minute debug session a future reader will pay if the chapter shipped stale. This is Pattern 12 (Evidence-Driven) applied to the chapter ↔ code relationship: verify the chapter actually matches disk *before* moving on.
- **The discipline scales to non-curriculum projects too.** Any project where README has setup instructions or where blog posts have code samples has this problem. The fix is the same: pick a canonical, declare the divergence, sync per change.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 11 — Atomic Decision Records (sync commits are decision records for "we shipped this version of the chapter against this version of disk")
- Pattern 17 — Forward-Link Panel for In-Flight Sections (forward-links document *expected* divergence between current section and later, more-evolved version)
- Pattern 20 — Real-Data-Only Discipline (the chapter shouldn't show BCJ entries from hypothetical incidents; only from real disk-run incidents)
- W3.5.8 — canonical multi-pass sync example (chapter ≡ disk, audit-marker discipline, forward-link panels working together)

---

## Pattern 19 — Spec → IMPLEMENTED Status Transition Marker

**When it applies:** chapters or sections that ship as *spec first* (theoretical / planned) and *implemented later* (with measured numbers, real failure modes). Common in roadmap chapters, agent runtime designs, "future work" sections, multi-week feature builds.

**Failure mode this prevents:** stale spec claims masquerading as implemented status. A section opens with "Phase 9 dedup-and-synthesis ships the 4-action primitive..." — six weeks later the implementation has 6 actions, but the section still says 4. Readers can't tell from the section text whether they're reading aspiration or measurement. Trust in the entire chapter erodes.

**The discipline.**

1. **Every section that includes work-to-be-done has an explicit status marker.** Chapter heading itself or a status line below it. Three states:
   - `(SPEC)` — design only; no code yet.
   - `(IMPLEMENTED YYYY-MM-DD)` — code shipped; numbers measured on that date.
   - `(STRETCH)` — optional / advanced sub-section, may never be implemented.
2. **Status transitions are commits.** When a spec section becomes implemented, the commit message names the transition: `docs(<week>): Phase N spec → IMPLEMENTED status with measured 2026-05-15 result`. Diff-able.
3. **Numbers replace adjectives.** A `(SPEC)` section says "~5× faster" or "much cleaner"; an `(IMPLEMENTED)` section says "47 atoms across 12 quests, 2026-05-19 lab run, 22 KB audit file." If the section is still using adjectives after the transition marker landed, the marker is lying.
4. **Failure modes get logged on transition.** When spec → implemented, the implementation likely surfaced 1-3 surprises. Those go into BCJ entries (Pattern 20) on the same commit as the status transition.

**Curriculum instances:**

- W3.5.8 Phase 9 (commit `ebee8dc`, 2026-05-15): `docs(week-3.5.8): Phase 9 spec → IMPLEMENTED status with measured 2026-05-15 result`. The section's opening line flipped from "ships when Phase 9 lands" to "shipped 2026-05-15, see `tests/test_dedup_synthesis.py` (5/5 PASS)".
- W3.5.8 Phase 9.6 supersede / coexist (commit `e630daf`, 2026-05-15): chapter heading went from `Phase 9.6 Bitemporal Extension (SPEC)` to `Phase 9.6 Bitemporal Extension (Step 1+2 implemented 2026-05-15)`.
- W7.7 quantization regime × technique grid (commit `7c952b0`, 2026-05-18): added with explicit `(SPEC)` markers on each technique row; flips to `(IMPLEMENTED)` per row as labs land.

**Anti-pattern: silent transition.** Code lands in disk; nobody touches the chapter; six weeks later the chapter still describes the spec form. The chapter looks current but is six weeks stale. Detection: grep for status markers older than the latest commit touching the corresponding lab directory.

`★ Insight ─────────────────────────────────────`
- **Status markers are the doc-level version of compile-time vs runtime types.** `(SPEC)` is "this type-checks but hasn't been executed"; `(IMPLEMENTED YYYY-MM-DD)` is "this type-checks AND we have evidence it ran on this date with this number." Without markers, every claim reads as either possibility — and the reader has to do the disambiguation work.
- **The discipline scales because the marker is small.** A 25-character status string per heading is the cheapest possible artifact-level fidelity check. Cheaper than tests, cheaper than CI; just a markdown discipline.
- **Date-stamping `(IMPLEMENTED YYYY-MM-DD)` is what makes Pattern 20 (Real-Data-Only) verifiable.** Without a date, a reader can't tell whether the "measured" claim is current or 6 months stale.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 11 — Atomic Decision Records (status transition is itself a decision: "we believe this section is now grounded")
- Pattern 18 — Spec/Disk Fidelity for Pedagogical Code (status markers help the reader know whether they should expect the chapter ≡ disk)
- Pattern 20 — Real-Data-Only Discipline (BCJ entries created at the spec→implemented transition are the most credible kind)

---

## Pattern 20 — Real-Data-Only Discipline (BCJ entries from symptoms, not from imagination)

**When it applies:** any bad-case journal, failure-mode catalog, lessons-learned register, or anti-pattern library. Specifically aimed at the temptation to write entries from "this *could* happen" rather than "this *did* happen at YYYY-MM-DD HH:MM."

**Failure mode this prevents:** the BCJ becomes a *theoretical* failure catalog rather than an *empirical* one. Theoretical entries are speculative — they describe failure modes that sound plausible but may not occur in this stack. Future readers can't trust theoretical entries because they have no symptom evidence; they end up writing parallel real entries anyway. The catalog bloats; signal-to-noise drops.

**The discipline.**

1. **Every BCJ entry has a date.** `YYYY-MM-DD — Week N — <symptom>`. If you can't put a date on it, it didn't happen, it's a hypothesis. Hypotheses belong in a separate "anticipated risks" doc, not in the BCJ.
2. **Every entry has a *Symptom* field with the observable evidence.** "Test output: `AssertionError: expected 2 promotes, got 0`" — that's a symptom. "The system might silently fail" — that's a hypothesis.
3. **Cross-cutting anti-patterns (e.g., the Russell 7) get a special section marker** — "anti-pattern catalog synthesized from external survey, dated YYYY-MM-DD." They're not real-incident entries; they're a *separate* class with their own labeling. Don't intermix them with real-incident entries.
4. **Hypothetical entries get removed on sight.** The commit `8f1e12c` (2026-05-14, "fix(extensions): remove hypothetical BCJ entries per real-data-only discipline") is the canonical case: a previous Claude write had filled BCJ slots with `predicted` entries; the human re-read and removed them all. Repeat as needed.

**Curriculum instances:**

- W3.5.8 BCJ Entries 6-13 (commit `7da1875`, 2026-05-14): all dated 2026-05-14, all from real lab runs against live guild + EverCore. Each entry's Symptom field quotes actual test output or actual log lines.
- Russell 2026 anti-pattern catalog (commit landed 2026-05-19, just now): explicitly labeled as `## 2026-05-19 — Cross-cutting — Multi-Agent Anti-Patterns (Russell 2026 synthesis)`. The header distinguishes catalog-from-survey vs incident-from-lab. Each "entry" prefixed `MA-N` to signal a different naming scheme.
- W3.5.8 BCJ Entry 14 (commit `6a49f90`, 2026-05-15): symptom = "Phase 9 dedup test: first scroll on 'fresh' campaign imprints 0 atoms because Qdrant collection has cross-test residue." Specific test output. Specific date.

**Anti-pattern: speculative BCJ entries.** "**Entry: Race condition in `_qdrant_delete`.** *Symptom:* concurrent writes might fail. *Root cause:* no locking. *Fix:* add fcntl.flock." None of those fields are evidence — they're a design review pretending to be a failure log. The fix is to either (a) prove the race condition by triggering it in a test, then dated-log the symptom; (b) move the speculation to a separate "open concerns" doc.

`★ Insight ─────────────────────────────────────`
- **Real-data discipline is what makes the BCJ *load-bearing* for interviews.** A speculative BCJ entry produces a speculative interview answer ("I think this could happen if..."); a real BCJ entry produces a concrete one ("On 2026-05-14 at the W3.5.8 §3.2.1 test run, the symptom was X; root cause was Y; the fix was Z and verified by Z' on 2026-05-15"). The latter is interview gold; the former is hand-waving.
- **External anti-pattern catalogs (Russell 7, OWASP Top 10, NASA software safety guidelines) are *useful inputs* to the BCJ but should not be mixed with incident logs.** Different epistemic class: synthesis from many real incidents at other organizations vs single incident here. Separate naming (MA-1 vs Entry 14), separate section headings, separate dates.
- **The simplest test: can you cite a specific test run, log line, or commit hash? Yes → real entry. No → speculation that doesn't belong in the BCJ.**
`─────────────────────────────────────────────────`

**See also:**
- Pattern 10 — Real Verification (the same discipline applied to feedback rather than failure-mode catalogs)
- Pattern 11 — Atomic Decision Records (BCJ entry from a real incident IS a decision record about how the system actually behaved)
- Pattern 19 — Spec → IMPLEMENTED Status Marker (BCJ entries are most credible when paired with the implementation that surfaced them)
- [[Bad-Case Journal]] — the catalog itself; the discipline applies to every entry

---

## Pattern 21 — Bidirectional Cross-Reference Invariant (every "Builds on" needs a "Connects to")

**When it applies:** any multi-document curriculum, knowledge base, wiki, or codebase with cross-document references. Specifically applies when document A says "I use idea from B" and document B's view of the world is incomplete without knowing "A uses my idea."

**The invariant.** Every directed reference must be bidirectional:

| If document A says | Then document B must say |
|---|---|
| "Builds on: W4 ReAct" | "Connects to: W7 Tool Harness" (where A is W7 and B is W4) |
| "Distinguish from: W3.5.5 Cross-Session Memory" | "Distinguish from: <reverse mention of A>" |
| "Cites: W2.7 PageIndex" | "Cited by: <list including A>" |
| "Foreshadows: W11 System Design" | "Builds on: <including A's contribution>" |

**Why it matters.** A unidirectional cross-reference is half-broken: a reader at B has no way to discover A. Multiply that across 41 chapters and ~10 cross-refs per chapter, and the curriculum has ~400 cross-refs where half can disappear silently. Six months later, refactoring W4 has no way to know W7 (and W5.5, and W6.5...) depend on it.

**The discipline.**

1. **Every cross-ref edit is a two-file commit.** Change W7 → also touch W4. Commit message: `docs(week-7): add cross-ref to W4 ReAct; reciprocal updated on W4`.
2. **The CLAUDE.md §9 (Cross-References) section codifies this** — "Cross-references must be bidirectional — if W7 says 'Builds on: W4 ReAct', then W4 should say 'Connects to: W7 Tool Harness'. When you add a forward link, add the reverse link in the target chapter in the same edit."
3. **Audit by grep.** Periodically: `grep -h "Builds on:" *.md | sort -u` → produces every edge; cross-check that every target chapter has the reverse. Discrepancies = silent half-edges.
4. **The same invariant applies to BCJ entries**: every chapter's local Bad-Case Journal section MUST mirror to the global `Bad-Case Journal.md`. Commit `4d81def` ("mirror 8 observed W3.5.8 entries to global journal (per CLAUDE.md §6 invariant)") is the canonical periodic-sync action.
5. **And to lab files**: when a lab adds a new file (e.g., `tests/test_consolidation_audit.py` lands on disk), the corresponding chapter section must reference it. When a chapter forward-references a lab module that doesn't yet exist, that's a TODO, not a stable cross-ref.

**Curriculum instances:**

- Commit `89481aa` (2026-05-14): `docs(week-5.6): close bidirectional cross-ref to W7.5 enum-action mini-lab`. The reverse link was missing; this commit closed it.
- Commit `b709dc7` (2026-05-18): `docs(curriculum): refine master doc — 4 entries audited against current chapters`. Periodic audit of master doc edges against chapter content.
- Commit `4d81def` (2026-05-15): mirror BCJ entries from chapter to global journal. The chapter's local BCJ is canonical; the global journal must reflect.

**Anti-pattern: unilateral cross-ref drift.** W7 chapter says "Builds on: W4 ReAct"; W4 chapter has no idea W7 cites it. Refactoring W4's ReAct contract silently breaks W7's narrative; the broken state isn't visible until a reader tries to follow the link both ways.

`★ Insight ─────────────────────────────────────`
- **Bidirectional invariants are the only invariants that can be checked by mechanical sweep.** Unilateral cross-refs require knowing what *should* be referenced — that's semantic. Bidirectional cross-refs require only that A↔B both exist — that's structural. Cheap to verify, hard to forget once the discipline is in place.
- **The reverse direction is usually *less informative* and that's the right shape.** W4 says "I built ReAct"; W7 says "I built tool harness, builds on W4's ReAct." W4's reverse mention ("Connects to: W7") is a single-line pointer, not a re-explanation of W7. The richness lives at the *forward-citing* end; the reverse end is purely an index entry. That asymmetry is fine.
- **Software-engineering analog: the same shape lives in symbol-cross-reference indexes (LSP / IDE go-to-references).** Code editors automate the reverse direction at compile time; curriculum writing has to do it manually. The discipline is the same; just the automation level differs.
`─────────────────────────────────────────────────`

**See also:**
- Pattern 18 — Spec/Disk Fidelity for Pedagogical Code (the chapter-vs-disk axis of cross-ref drift)
- Pattern 17 — Forward-Link Panel for In-Flight Sections (panels make the cross-ref graph visible in linear markdown)
- CLAUDE.md §9 (Cross-References) — the normative spec for the chapter-level invariant
- W3.5.8 § Bad-Case Journal ↔ global `Bad-Case Journal.md` — same invariant at the BCJ-entry level

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
| 14 — Delegation Contract | Every parent → subagent spawn | "Subagents know nothing" + token-burn from under-briefed workers |
| 15 — Read-Side / Write-Side Mirror Design | Designing event-sourced / audit-logged / CQRS systems | Read queries with no write-side support; logs that can't replay |
| 16 — Multi-Axis Comparison Table | Explaining or deciding across 2+ orthogonal dimensions | 1D-list reasoning that hides "depends on X" qualifications |
| 17 — Forward-Link Panel | Introducing primitives that get fully wired later | Silent forward-references that stop first-time readers cold |
| 18 — Spec/Disk Fidelity | Any pedagogical writing with runnable code | Chapter ↔ disk silent drift; reader copy-paste fails |
| 19 — Spec → IMPLEMENTED Status Marker | Roadmap chapters with work-to-be-done | Stale spec claims masquerading as implemented status |
| 20 — Real-Data-Only Discipline | Every BCJ / failure-mode entry | Speculative entries diluting the catalog's signal |
| 21 — Bidirectional Cross-Reference Invariant | Every cross-doc / cross-chapter reference | Silent half-edges that break under refactoring |

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
