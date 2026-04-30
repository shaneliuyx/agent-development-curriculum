---
tags: [agent-curriculum, debugging, bad-cases, ops-pattern-library]
created: 2026-04-27
updated: 2026-04-27
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

---

— end —
