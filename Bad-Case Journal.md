---
tags: [agent-curriculum, debugging, bad-cases, ops-pattern-library]
created: 2026-04-27
updated: 2026-04-30
---

> **Read order:** Diagnostic Heuristics → Entry Template → Entries → Cross-cutting patterns. The heuristics are pre-debugging discipline (how to think); the template is post-debugging discipline (how to log).

# Bad-Case Journal

A running log of the failures that *didn't* announce themselves with a stack trace — silent failures, wrong-hypothesis chases, version mismatches, and operational gotchas that ate time on the first encounter and should take seconds the second time.

The point of this journal is not "what broke" — that's in commit messages and `RESULTS.md` files. The point is **the wrong path I went down first**, **the 5-second test that would have caught it instantly**, and **the broader pattern it belongs to** so I can recognize the shape in a different system later.

---

## Diagnostic Heuristics

A growing set of pre-debugging mental moves. The point is to make these mechanical — when symptom X appears, run heuristic Y *before* generating fix candidates. Each one was paid for with real time burned on a real bad case.

---

### H1 — Symptom → Cause-Shape Mapping (run this FIRST, always)

**Rule:** Before generating any fix candidates, characterize the symptom *shape* in one sentence and ask "what *classes of mechanism* produce this exact shape?" Only generate hypotheses that fit the shape.

**Why it works:** Most failures have a small, identifiable set of cause-shapes given the symptom. Random hypothesis generation pulls from "things I've seen go wrong with this tool" (availability), which is a much bigger and noisier set than "things that produce *this specific symptom*."

**Anti-pattern it counters:** Jumping straight to fix candidates without bounding the hypothesis space. ("Let me try X" before "what kind of failure is this?")

**Quick example (from Week 1):**
- Symptom shape: *"model loads cleanly, encodes inputs, returns correctly-shaped vectors, but those vectors retrieve at random-chance baseline."*
- Cause-shapes that fit: (a) weights file truncated/corrupted, (b) model class doesn't match weights file (random-init layers), (c) wrong base model loaded, (d) embedding normalization disabled when index assumes normalized.
- Cause-shapes that DO NOT fit: missing `trust_remote_code` (produces *load failure*, not silent noise), wrong vector dim (produces *exception at insert*, not bad recall), wrong distance metric (produces *consistently wrong* results, not random).
- Heuristic outcome: `trust_remote_code` would never make the shortlist if you do shape-matching first.

---

### H2 — Famous-Fix Recall is an availability trap

**Rule:** When a tool/library/model has a well-known gotcha (e.g., `trust_remote_code` for Nomic, `pin_memory` for PyTorch DataLoader, `--legacy-peer-deps` for npm), only invoke that fix if the *current symptom matches the famous fix's known signature*. The famous fix is not a universal answer to "tool X is misbehaving."

**Why it works:** Your brain serves up famous fixes by tool identity, not by symptom shape. That's the availability heuristic: famous-fix recall is loud, symptom-matching is quiet.

**Anti-pattern it counters:** "Nomic v2 is failing → must be `trust_remote_code`." "Build is slow → must be cache miss." "Model output is bad → must be temperature."

**Quick check:** Before applying a famous fix, write down (in one sentence) *what symptom that fix is known to resolve* and confirm it matches yours. If you can't, you're in availability-trap territory.

---

### H3 — Look at the producer, not the consumer

**Rule:** When a bad value appears in code A but is produced by code B, the diagnostic evidence almost certainly lives in B's logs/output, not A's. Go upstream to the producer immediately, even if the symptom surfaced downstream.

**Why it works:** The consumer is where you noticed the problem; the producer is where the problem happened. These are usually different files and often different runs.

**Anti-pattern it counters:** "Looking under the streetlight" — debugging the file you're currently looking at because that's where the bad number printed.

**Quick example (from Week 1):**
- Bad recall printed in `04_eval.py` output → I read `04_eval.py`.
- But the model weights were loaded in `03_ingest_nomic.py`, where the `LOAD REPORT` with `MISSING:` and `UNEXPECTED:` weight lists was written to stderr hours earlier.
- All the diagnostic evidence existed; it was in the wrong file's logs.
- Fix to the heuristic: when a number is wrong, ask *"which process/script computed this number?"* before opening any file.

---

### H4 — Recently-Touched Bias

**Rule:** Don't blame the last code you edited just because it's mentally available. Causal proximity (what's actually broken) is independent of chronological proximity (what you most recently touched).

**Why it works:** Your working memory has the recent edits highlighted; nothing else gets that prominence. So "recent edits" become the default hypothesis pool. But bugs in *unchanged* code are equally likely — especially failures that depend on cached state, environment, or upstream version drift.

**Anti-pattern it counters:** "I just edited X and now Y is broken, so X must be the cause" — even when Y has nothing to do with X.

**Quick check:** Before blaming recent edits, ask *"would this symptom appear if I reverted my recent changes?"* If you genuinely don't know, that's evidence the recent edits aren't necessarily causal.

---

### H5 — The Cheap-Fix Trap

**Rule:** A fix that costs ~30 seconds to try is not "free" — it has hidden costs in evaluation time, sticky-progress bias (H6), and opportunity cost of the right hypothesis you didn't generate. **Spend 60 seconds thinking before trying any fix**, even cheap ones.

**Why it works:** Cost-of-trying is what gets weighed in the moment; cost-of-being-wrong (re-evaluation, abandoning the lead, dismissing it as "well at least I ruled that out") is paid later and forgotten in the moment.

**Anti-pattern it counters:** "Adding one kwarg costs nothing, let me just try it." (It costs the next 10 minutes of "did the fix take effect? let me re-run. is the cache stale? let me clear it. is the import path right?")

**Quick example (from Week 1):** Adding `trust_remote_code=True` was a 30-second edit. It cost ~10-15 minutes of follow-on confusion when recall stayed at 0.021, partly because of H6.

---

### H6 — Sticky-Progress Fallacy

**Rule:** Once you've "made a fix," you'll resist abandoning that lead even when the symptom doesn't change. **Predict the verification result *before* running it** — if your prediction is right and the symptom persists, abandon the lead in the same breath, don't re-run "to make sure."

**Why it works:** Predicting first commits you to a falsifiable claim. Running first lets you rationalize ("maybe the fix didn't take effect", "maybe the cache is interfering", "maybe I need to restart the kernel") and stay attached to the lead.

**Anti-pattern it counters:** "My fix is in, let me see if it worked" → result unchanged → "let me try it once more / restart / clear caches" → still unchanged → 15 more minutes burned before the lead is finally dropped.

**Quick check:** Write the predicted symptom-after-fix in one sentence *before* running. If it matches reality and the bug persists, the lead is dead — move on immediately.

---

### H7 — Cache as Step Zero

**Rule:** When a system reports success exit codes everywhere but produces wrong output, *or* "worked yesterday but not today," invalidate caches **before** any deeper debugging. This is a cheap discriminator that resolves a large class of silent failures.

**Why it works:** Caches are designed to lie convincingly — that's their job. Stale cache hits are indistinguishable from correct results until you compare against ground truth. Invalidating them costs ~5 seconds and either fixes the bug or definitively rules out cache as the cause.

**Anti-pattern it counters:** "The code is right, the config is right, the inputs are right — must be a logic bug" → 30 minutes later → "oh, the cache was stale."

**Cache locations worth knowing for this curriculum:**
- `~/.cache/huggingface/modules/transformers_modules/<org>/<model>/<oid>/` — custom modeling code (the Week 1 culprit)
- `~/.cache/huggingface/hub/models--<org>--<model>/` — weights / tokenizer
- `~/.cache/torch/sentence_transformers/` — sentence-transformers wrappers
- `__pycache__/` and `.pyc` files — usually harmless but can wedge after refactors
- Docker layer cache, OrbStack image cache — rebuild with `--no-cache` to discriminate
- npm/pnpm/uv lockfile + node_modules — `rm -rf node_modules` is the cheap test

---

## Entry template

```markdown
## YYYY-MM-DD — Week N — One-line title

**Symptom:** What I saw that looked wrong, and what made me notice it.

**Why it's a bad case:** Pattern this represents (silent failure / wrong-hypothesis chase / version mismatch / cache staleness / etc.)

**False leads:**
1. Hypothesis I chased — what I tried — what made me drop it
2. ...

**Root cause:** Exact mechanism, with receipts (commit OIDs, file paths, version strings).

**Fix:** Exact commands. Should be minimal.

**Time cost:** Burned vs. cost-with-lesson.

**5-second sanity test:** The diagnostic that would have caught this instantly.

**Generalizes to:** Other systems / contexts where the same shape shows up.

**Tags:** #area #pattern #lab-N
```

---

## 2026-04-27 — Week 1 — Nomic Embed v2 silent embedding failure (stale HF modules cache)

**Symptom:** First eval run on the 6,980-query MS MARCO dev set produced sane recall for both BGE-M3 collections (`recall@10 = 0.993`) but `recall@10 = 0.021` for `nomic_hnsw` — basically the random-chance baseline (~0.001 for 10K-doc / top-10). Nothing in the logs flagged an error: `04_ingest_nomic.py` exited 0, Qdrant reported `points_count = 10000`, eval ran to completion. Every exit code said success; the numbers said the model was outputting noise.

**Why it's a bad case:** Classic silent-failure pattern. The system reports success at every observable layer (exit code, container state, row count, eval completion) while producing semantically meaningless output. No exception ever fires because the failure is in *what the model computed*, not whether it computed.

**False leads:**

1. **`trust_remote_code=True` missing on the eval-side `SentenceTransformer` constructor.** This was a real bug — Nomic v2 ships a custom `NomicBertModel` class via `trust_remote_code`, and the eval script was instantiating without that flag. Added it, re-ran, recall stayed at 0.021. **Necessary fix but not sufficient** — the actual model loading was succeeding (no exception thrown when the flag was absent because the cached modeling code was already on disk), so adding the flag changed nothing about the output. ~10 minutes burned here, partly because the fix *felt* like the kind of thing that would be the cause.

2. **Vector dimensionality / collection schema mismatch.** Briefly suspected the Qdrant collection was created with the wrong vector size for Nomic (768 vs BGE's 1024). Confirmed via `qd.get_collection('nomic_hnsw').config.params.vectors.size` — was correctly `768`. Dropped this lead in ~2 minutes.

**Root cause:** Stale state in the HuggingFace modules cache at `~/.cache/huggingface/modules/transformers_modules/nomic_hyphen_ai/nomic_hyphen_bert_hyphen_2048/<oid>/modeling_hf_nomic_bert.py`. The cached `modeling_hf_nomic_bert.py` and the on-disk weights file were out of sync: the modeling class definition expected dense MLP weights (`mlp.up_proj.weight`, `mlp.gate_proj.weight`, `mlp.down_proj.weight`), but the weights file contained MoE expert tensors (`mlp.experts.mlp.w1`, `mlp.router.layer.weight`). The class either lacked the MoE wiring entirely or was a partial revision missing the layer-integration code that connects MoE to `NomicBertBlock`.

> **Note on OID forensics:** an earlier version of this entry pinned the broken state to a specific commit OID (`7710840...`) and named a different commit (`46cf2dead046...`) as the "upstream-current fix." That specific OID-comparison claim turned out to be over-specified — see the **Correction** section near the end of this entry. The mechanism above (MISSING/UNEXPECTED weight mismatch) is what survives.

The receipts were in stderr the whole time, in the `LOAD REPORT` block:
- `MISSING:` dense MLP weights (the class defined them, the file didn't have them)
- `UNEXPECTED:` MoE expert weights (the file had them, the class didn't know what to do with them)

`transformers` does what it's documented to do here: missing weights get **randomly initialized** and unexpected weights get **silently discarded**. Result: a model whose dense layers are random noise on top of a partially-loaded backbone. It encodes, it produces 768-dim vectors, every shape is right — the vectors are just statistically untethered from the input text. Hence ~random retrieval performance.

**Fix:**
```bash
rm -rf ~/.cache/huggingface/modules/transformers_modules/nomic_hyphen_ai/
# re-run ingest — forces fresh modeling code download (whatever upstream is now)
python src/03_ingest_nomic.py
python src/04_eval.py
```

Recall jumped `0.021 → 0.997`.

**Time cost:** ~30 minutes burned. ~15 of those were on the `trust_remote_code` wrong lead. With the lesson below, this is a 2-minute fix (run sanity test → see non-determinism → nuke cache → re-ingest).

**5-second sanity test:**
```python
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("nomic-ai/nomic-embed-text-v2-moe", trust_remote_code=True, device="mps")
import numpy as np
a = m.encode("the quick brown fox", normalize_embeddings=True)
b = m.encode("the quick brown fox", normalize_embeddings=True)
print("bit-identical:", np.array_equal(a, b))
print("first 5 dims:", a[:5])
```

If `bit-identical` is `False`, the model has random-init layers (encoding the same string twice with a deterministic model on a fixed seed should yield bit-identity). If the first 5 dims look random-ish across re-runs, the cache is stale. Both check the same thing from different angles.

A second instant test: scan stderr for the strings `MISSING` and `UNEXPECTED` after the model loads. If either appears with a non-trivial weight list, the class definition and the weights file disagree — investigate before doing anything else with the model.

**Generalizes to:** This is the embedding-model version of three operational shapes I've debugged on the cloud-infra side:

1. **Argo Workflow that succeeds on every node but produces empty artifacts.** Same pattern: every layer reports success (pod exit 0, status `Succeeded`, downstream consumer triggered), the artifact is just garbage or empty. Diagnostic: never trust pipeline exit codes alone; assert on the *content* of the artifact against a known contract.

2. **Lambda returning `200 OK` with a malformed payload.** Status code lies because the handler ran to completion; the JSON it returned doesn't match the schema downstream expects. Diagnostic: schema-validate at the consumer boundary, not just at the producer.

3. **Helm/Argo CD reporting `Synced + Healthy` while the deployed image is months stale because the image tag is `:latest` and the cluster's local cache is pinned.** Same cache-invalidation root cause as the HF modules cache. Diagnostic: pin by digest, not tag; or invalidate on every deploy.

The diagnostic muscle is the same across all four: **don't trust exit codes; verify outputs against expected semantics**, and **treat caches as a first-class source of "looks fine but isn't" failures** — invalidate them as step zero of any debugging session that involves "but it worked yesterday" type symptoms.

**Correction (2026-04-27, surfaced during Phase 4.5 refactor verification):**

When the Week 1 lab was re-run after the atomic-config refactor (Week 1 runbook Phase 4.5), the eval output included a `transformers` warning showing the cached modeling code path:

```
.../nomic_hyphen_ai/nomic_hyphen_bert_hyphen_2048/7710840340a098cfb869c4f65e87cf2b1b70caca/modeling_hf_nomic_bert.py
```

The OID is `7710840...` — the same OID my original Root cause section had pinned as the *broken* version. But this run produced `recall@10 = 0.997`, not the broken `0.021`. So the OID-specific narrative cannot be right as originally written. Two readings of the new evidence:

- **Option A (more likely):** `7710840...` is actually a *working* version of the modeling code. The pre-fix broken cache must have been at some other OID I didn't capture before nuking it. After `rm -rf`, HF re-fetched and landed at `7710840...` clean.
- **Option B (less likely):** Same OID, different file contents — HF may have written a corrupted/partial file the first time, then a clean one after the rm.

Either way, my original specific OID-forensics claim ("stale was `7710840`, upstream-current was `46cf2de`") was **over-specified** — I extrapolated from the path I happened to observe at fix-time without preserving the pre-fix path for comparison. What survives:

| Still high-confidence | What I got wrong |
|---|---|
| Symptom shape (silent failure, success exit codes everywhere, recall ≈ random) | The pre-fix and post-fix OIDs and which was which |
| Diagnostic mechanic (`MISSING:` / `UNEXPECTED:` in the LOAD REPORT, random-init behavior of `transformers`) | The specific commit OIDs as a stable pair |
| The fix (`rm -rf ~/.cache/huggingface/modules/transformers_modules/<org>/`) | Claiming the fix "picks up commit `46cf2de`" — there's no evidence that's true |
| The lesson — cache as step zero ([[#H7 — Cache as Step Zero]]) | — |

**Lesson behind the lesson:** *if you're going to make commit-OID-specific claims in a bad-case writeup, capture the broken-state OID before applying the fix that destroys the evidence.* Investigative artifacts are write-once — you can't make precise post-hoc claims if the diagnostic state is gone.

This may be worth promoting to a future heuristic ("**H8 — Preserve diagnostic state before applying the fix**") if the pattern recurs. For now, leaving as a self-contained correction so the journal models the meta-discipline of revising prior claims when new evidence arrives.

**Repo-side note:** the same over-specified OID claim appears in `lab-01-vector-baseline/results/RESULTS.md` (public, on GitHub). Whether to amend it there is a separate decision — public correction becomes a git-history event, which has portfolio implications either way.

**Tags:** #embedding #huggingface #cache-invalidation #silent-failure #lab-1 #wrong-hypothesis-chase #ops-pattern #correction-applied

**Captured in curriculum at:** [[Week 1 - Vector Retrieval Baseline]] Phase 3.2 gotcha #4
**Lab artifact:** [`lab-01-vector-baseline/results/RESULTS.md`](https://github.com/shaneliuyx/agent-prep/blob/main/lab-01-vector-baseline/results/RESULTS.md) — Bad-case journal section

---

## 2026-04-30 — Week 2.5 — GraphRAG seed-extraction → fuzzy-match cascade (`edges_used: 0`)

**Symptom:** A working GraphRAG pipeline (3,952 entities, 2,859 edges in Neo4j, validated by `MATCH (n:Entity) RETURN n.name LIMIT 20`) returns `edges_used: 0` for queries the corpus clearly contains. `python src/query_graph.py "What movements influenced anarchism?"` → no seeds extracted. After loosening the seed prompt to allow movements/concepts: `seeds: ["early anarchist thinkers"]` for the next query — but still `edges_used: 0`. The graph has plenty of relevant nodes (`anarchist movement`, `anarchist doctrines`, `Anarchists`, `William Godwin`); the pipeline just won't connect query → graph. Two consecutive failures with two completely different root causes, both at zero retrieval depth, both presenting the same `edges_used: 0` symptom.

**Why it's a bad case:** Cascade failure across pipeline stages — the *same* downstream symptom (`edges_used: 0`) had two different upstream causes on consecutive runs. Fixing the first cause exposed the second. This is the multi-stage-pipeline version of "the consumer is downstream of the bug" (heuristic [[#H3 — Look at the producer, not the consumer]]) — but extended: each pipeline stage can hide the next stage's bug. Until you fix Stage A, you can't observe Stage B's failure mode at all.

**False leads:**

1. **First instinct: "the graph wasn't built right."** Spent ~2 minutes running entity-count and sample-name Cypher queries to verify the graph populated correctly. It had — 3,952 nodes, 2,859 edges, samples included `Anarchism`, `William Godwin`, `Wilhelm Weitling`, `Paris Commune`. Drop this lead. The graph was always fine.

2. **After fixing Stage A (seed prompt) → still `edges_used: 0` on a different query.** Briefly suspected the fix had regressed something. It hadn't — the new query ("Who were the early anarchist thinkers?") simply hit a *different* failure mode at the *next* stage (fuzzy-match Cypher). Without the Stage A fix, this Stage B bug would have been invisible.

**Root cause:** Two distinct bugs, in series:

**Stage A — Seed extraction prompt was too narrow.** `EXTRACT_SYSTEM` in `src/query_graph.py:23` restricted entities to "concrete nouns: companies, people, places, products" — categorically excluding the movements, ideologies, and concepts that dominate the early-Wikipedia article slice (`train[:200]` of `wikimedia/wikipedia` is heavy on philosophy and political theory). The seed extractor returned `[]` for any query about an excluded category, even when the corpus explicitly contained that category.

**Stage B — Whole-phrase `CONTAINS` matching is brittle for descriptive seeds.** The `fetch_subgraph` Cypher query was:
```cypher
MATCH (n:Entity)
WHERE toLower(n.name) CONTAINS toLower($seed)
WITH n LIMIT 3
MATCH path = (n)-[*1..2]-(m) ...
```
The seed extractor (correctly preserving the user's phrasing) returned `"early anarchist thinkers"` — a 24-character descriptive phrase. Graph nodes are atomic concepts: `anarchist movement` (18 chars), `anarchist doctrines` (19 chars), `Anarchists` (10 chars). No node name `CONTAINS` the literal phrase "early anarchist thinkers". Match count: 0 across the entire graph.

**Fix:**

Stage A — loosen the seed extractor prompt to cover the corpus's actual entity types and use the explicit JSON object envelope:
```python
"Extract 1-5 entities from the query as a JSON object {\"entities\": [...]}. "
"Include any noun phrase a graph could store: people, places, products, "
"organizations, movements, ideologies, events, concepts, time periods. "
"Prefer specific surface forms over generic ones. "
"If the query is generic ('tell me about X'), extract X."
```

Stage B — token-level matching with a stop-word filter, in `fetch_subgraph`:
```python
words = [w for w in seed.lower().split() if len(w) >= 4] or [seed.lower()]
result = session.run(
    f"""
    MATCH (n:Entity)
    WHERE ANY(w IN $words WHERE toLower(n.name) CONTAINS w)
    WITH n LIMIT 5
    MATCH path = (n)-[*1..{max_hops}]-(m)
    ...
    """,
    words=words,
)
```
The 4-character minimum drops the most common stop words ("the", "a", "of", "in", "is") that would match every entity. After both fixes, "Who were the early anarchist thinkers?" returns `edges_used: 11` and the synthesizer produces *"The early anarchist thinkers were William Godwin and Wilhelm Weitling."* — a multi-hop graph-grounded answer with citations, exactly the GraphRAG capability the lab is supposed to demonstrate.

**Time cost:** ~25 minutes total. ~5 minutes verifying the graph was correctly built (Cypher queries). ~10 minutes diagnosing Stage A and writing the prompt fix. ~10 minutes diagnosing Stage B once Stage A unblocked it. With the lesson below, this is a 2-minute fix on re-encounter.

**5-second sanity test:** When `edges_used == 0`, run these two probes in order before assuming the graph or the LLM is broken:

```python
# 1. Did the seed extractor return anything?
seeds = extract_seed_entities(query)
print("seeds:", seeds)
# If [] — Stage A bug (prompt too narrow). Loosen seed extractor.
# If ["multi word phrase"] — Stage B candidate; continue to probe 2.
```

```cypher
// 2. Does the graph contain ANY entity matching ANY word from the seed?
WITH split(toLower($seed), ' ') AS words
UNWIND words AS w
MATCH (n:Entity)
WHERE size(w) >= 4 AND toLower(n.name) CONTAINS w
RETURN w, count(DISTINCT n) AS matches
```
If probe 2 returns rows but the script returns `edges_used: 0`, the bug is in the Cypher predicate (Stage B). Fix the matcher. If probe 2 returns no rows, the seed truly has no overlap with graph content — that's a *corpus mismatch*, not a code bug.

**Generalizes to:** Any multi-stage NLP pipeline where each stage can independently swallow the input.

1. **Two-stage retrieval (retriever + reranker):** retriever returns 0 candidates → reranker is invisible. Always inspect each stage's output independently before debugging the next.

2. **Tool-using agents (planner + tool dispatcher):** planner returns no tools → executor reports "no action taken." Same shape — the symptom appears at the *terminal* stage, but the bug is upstream. Heuristic [[#H3 — Look at the producer, not the consumer]] applies.

3. **ETL pipelines (extractor + transformer + loader):** if the extractor returns an empty result set due to an over-restrictive filter, the transformer runs successfully on zero rows and the loader writes zero rows, all reporting success. This is the "silent failure on empty input" pattern — every stage operates on what it received and reports success on what it produced, but the input was already empty.

**The diagnostic muscle:** when a multi-stage pipeline reports a downstream "no result" symptom, **probe each stage's input and output separately** before generating fix candidates for any single stage. The downstream stage's "0 results" is *evidence about its input*, not evidence about its own logic. This is heuristic [[#H3]] generalized: in pipelines, the producer chain extends backwards through every prior stage. Walk it.

**Tags:** #graphrag #neo4j #cypher #multi-stage-pipeline #cascade-failure #lab-2-5 #wrong-hypothesis-chase #ops-pattern

**Captured in curriculum at:** [[Week 2.5 - GraphRAG#Bad-Case Journal]] Entries 3 & 4
**Lab artifact:** `lab-02-5-graphrag/src/query_graph.py` — `extract_seed_entities` (Stage A) + `fetch_subgraph` (Stage B)

---

## 2026-04-30 — Week 2.5 — Reasoning model exhausts max_tokens budget → empty seeds → non-deterministic answers

**Symptom:** Same query produces different results across runs. `python src/query_graph.py "Which companies did Steve Jobs co-found?"` returned a full answer with 29 graph edges on one invocation, then `"No relevant entities found in the graph"` with 0 edges and `seeds: []` on the next invocation. `temperature=0.0` was set throughout. Wall time on the failing run was 38 seconds vs 6 seconds on the working run.

**Diagnostic walk-through.**

```bash
# 1. Did the seed extractor produce empty output?
# Yes — seeds: [] confirmed in JSON output of failing run.

# 2. Did the LLM call return content=None?
# Yes — added a finish_reason check; finish_reason="length" on failures.
# This is the budget-exhaustion fingerprint.

# 3. Why does the SAME query, same model, temperature=0 produce different outputs?
# The HAIKU model is gpt-oss-20b — a REASONING model. It spends max_tokens
# on internal reasoning_content (chain-of-thought) BEFORE emitting visible
# content. Reasoning length is stochastic across runs even at temperature=0.
# When chain-of-thought happens to be long enough to consume max_tokens=3000,
# the model never gets to emit the JSON body, content=None, the fallback
# returns [], and the downstream pipeline produces the empty-edges error.
```

**Root cause:** Reasoning models do not have a deterministic content-emission budget. The split between reasoning_content and content is non-deterministic across runs. `temperature=0` controls token sampling but not chain-of-thought *length*. Using a reasoning model for a structured-output task (extract entities → JSON) means you have a contract that says "produce valid JSON" wired to a model whose first behavior is "spend up to 3000 tokens thinking, *then* maybe produce JSON if I have budget left." The contract and the mechanism are mismatched.

**Fix.** Three changes in `lab-02-5-graphrag/src/query_graph.py`:
1. **Switch the entity-extraction call to a non-reasoning model.** Replaced `model=HAIKU` (`gpt-oss-20b`) with `model=MODEL` (`gemma-4-26B-A4B-it-heretic-4bit`). Non-reasoning models emit content directly; `temperature=0` is fully deterministic. Lowered `max_tokens` from 3000 to 400 (gemma is direct, doesn't need a reasoning budget).
2. **Add a regex fallback** for empty content. `re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", query)` captures proper nouns ("Steve Jobs", "Apple", "NeXT") via capitalization and works without any LLM call. This is defense-in-depth: if the LLM does fail (network blip, model swap), the pipeline degrades gracefully instead of returning "no entities found."
3. **Log finish_reason on empty content.** Future failures will surface immediately as `[WARN] LLM returned empty content (finish_reason=length)` rather than silently producing 0-edge results.

**Verification.** Ran the same query three times after the fix. Output identical to four decimals: `seeds: ["Steve Jobs"]`, `edges_used: 14`, same answer text. Determinism restored.

**The diagnostic muscle:** When a structured-output call returns `None` and the symptom is non-deterministic, the first probe should be `finish_reason`. If it's `"length"`, the model hit the budget. If `"stop"` with empty content, something else broke (model crash, prompt-injection-induced refusal). Most LLM SDKs default to suppressing `finish_reason` from logs — explicitly print it on every empty-content path.

**Tags:** #reasoning-model #structured-output #non-determinism #graphrag #lab-2-5 #budget-exhaustion #ops-pattern

**Captured in curriculum at:** [[Week 2.5 - GraphRAG#Bad-Case Journal]] Entry 6
**Lab artifact:** `lab-02-5-graphrag/src/query_graph.py` — `extract_seed_entities()`, `_regex_seed_fallback()`

---

## Cross-cutting patterns (fill in as entries accumulate)

> Update this section every ~3 entries to surface recurring shapes. The goal is to stop treating each bad case as one-off.

### Silent failures (exit code lies)
- 2026-04-27 — Week 1 — Nomic stale cache produces random-output model with success exit codes

### Wrong-hypothesis chases (the cost of jumping to the most-recent-thing-I-touched)
- 2026-04-27 — Week 1 — Chased `trust_remote_code` for ~15 min before reading the LOAD REPORT

### Cache invalidation as step-zero
- 2026-04-27 — Week 1 — `~/.cache/huggingface/modules/transformers_modules/`

### Version / commit mismatches (model class vs. weights, library vs. API)
- 2026-04-27 — Week 1 — Nomic modeling code commit `7710840` vs upstream `46cf2de`
- 2026-04-27 — Week 1 (separate) — `qdrant-client` v1.15 removed `.search()`, must use `.query_points(...).points`

### Reasoning-model budget exhaustion (non-determinism in structured-output tasks)
- 2026-04-30 — Week 2.5 — `gpt-oss-20b` reasoning model burns `max_tokens=3000` on chain-of-thought, returns `content=None`, `seeds=[]`, downstream sees 0 edges. Lesson: never use reasoning models for structured-output tasks where empty content = silent failure. Reserve reasoning models for tasks that benefit from chain-of-thought (math, code review, planning); use non-reasoning models for extraction, classification, routing.

### Mismatched contract vs mechanism (model capability vs task shape)
- 2026-04-30 — Week 2.5 — "Produce valid JSON" contract wired to a reasoning model. Contract requires deterministic emission; mechanism is "spend N tokens thinking, then maybe emit." Pattern generalizes: if the contract is "do X reliably with bounded latency," using a model whose first behavior is unbounded internal reasoning is a category mistake. Always check whether the chosen model is reasoning vs non-reasoning when the task is structured output.

---

— end —
