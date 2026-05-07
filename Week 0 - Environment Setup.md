---
title: "Week 0 — Environment Setup"
created: 2026-04-23
updated: 2026-05-03
tags: [agent, curriculum, week-0, setup, mlx, local-first]
audience: Cloud infrastructure engineer (3 yrs) targeting Agent / LLM Engineer roles
stack: macOS M5 Pro, oMLX, vMLX, Qdrant, Phoenix, Docker/OrbStack
---

# Week 0 — Environment Setup

> Step-by-step setup so every lab in the 3-month curriculum is copy-paste ready.
> Machine baseline: macOS 26.4.1 on Apple Silicon (arm64). If you're on a different machine, adjust paths.

---

## Why This Week Matters

Environment setup is not IT-department busywork. It is the foundation of reproducibility: the difference between "I built an agent that works" and "I built an agent that someone else can run six months later without debugging." A misconfigured environment (wrong Python version, stale model weights, network isolation broken, missing API keys) cascades into weeks of debugging. Production systems live in containers and managed infrastructure *because* local-machine entropy must be eliminated. This week mirrors that discipline: every step is versioned, every tool is pinned, every artifact is disk-local (models, code, configs). You will build an agent in W1–W12 using this environment; if the environment is fragile, every lab result becomes suspect. Interviewers ask about environment design because deployment readiness requires it. You'll need to articulate: why inference runs locally (cost, latency, data residency), how model weights are cached, why Docker or containers matter, and what happens when a dependency goes stale. This week teaches you to think like infrastructure.

---

## Theory Primer — Local-First Agent Infrastructure

The curriculum runs on **local-first architecture**: inference, embedding, reranking, and persistence all execute on your machine (or in local Docker containers). This is not the default. Cloud APIs (Claude API, OpenAI API, Google Vertex) are the standard for production agents. Why local-first here?

**Cost ceiling.** Anthropic's Claude API costs ~$0.005 per 1K input tokens (Haiku), ~$3 per 1M input tokens (Sonnet). Over 12 weeks of labs with iterative development, cloud costs would exceed $200–500. The same workload via local MLX models (Qwen, Gemma) on your M-series Mac costs $0 in runtime (only electricity, ~$10–20 total). Reasonable cap for a self-directed learner is <$50 total.

**Model versioning.** Cloud APIs versioned you: when OpenAI ships Claude 4.2, your old code may break or behave differently. Local models on disk are version-locked. `gemma-4-26B-A4B-it-heretic-4bit` weights, once downloaded, don't change. Reproducibility is guaranteed. This is critical for labs: if a lab's results drift between runs, you cannot debug whether your code is wrong or the model shifted. Local models eliminate that variable.

**Inference backends.** Two tools serve local models:
- **oMLX**: Inference server for large models (Qwen 35B, Gemma 31B). Runs on M3/M5 Pro/Max. Latency 50–150ms per token (vs. 10–20ms for cloud APIs). Cost: electricity.
- **vMLX**: Smaller/faster models. Benchmarking in W7/W8 compares oMLX (Opus-tier) vs vMLX (Haiku-tier) vs cloud APIs.

**Stateful services (Docker).** Qdrant (vector database) and Phoenix (tracing + observability) run in Docker. Docker ensures consistent environment across machines: same Qdrant version, same Phoenix schema. Without containerization, "works on my machine" becomes your nightmare. Phase 3 uses OrbStack (lightweight Docker daemon on macOS).

**Dependency isolation (venv).** Python's `uv` creates a project-specific virtual environment. Each lab gets its own venv; no global package pollution. `uv` is ~100x faster than pip. Weights are cached globally in `~/.cache/huggingface/`, so a second lab does not re-download 5GB of Qwen weights.

---

## Mechanism / Architecture Diagram

```mermaid
graph TB
    A["macOS Host<br/>(M3/M5 Pro)"] --> B["oMLX Server<br/>:8000<br/>(Qwen 35B,<br/>Gemma 26B)"]
    A --> C["vMLX Server<br/>:8002<br/>(Gemma 31B<br/>uncensored)"]
    A --> D["Python Venv<br/>(lab-01, lab-02, ...<br/>uv project isolation)"]
    D --> E["Lab Code<br/>(RAG, ReAct,<br/>Tool Harness, etc.)"]
    E -->|API calls| B
    E -->|API calls| C
    E -->|HTTP| F["Docker: Qdrant<br/>:6333<br/>(Vector DB)"]
    E -->|HTTP| G["Docker: Phoenix<br/>:6006<br/>(Tracing)"]
    F --> H["Disk: ~/.qdrant/<br/>(embeddings index)"]
    B --> I["Disk: ~/.omlx/models/<br/>(Qwen, Gemma weights)"]
    C --> J["Disk: ~/.cache/<br/>huggingface/<br/>(embedding models,<br/>weights)"]
    D --> K["Disk: ~/projects/<br/>agent-prep/<br/>lab-*/"]
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style F fill:#e8f5e9
    style G fill:#e8f5e9
```

---

## Pre-Flight Checklist — What You Already Have

Verified by a system survey on 2026-04-23. Skip the install step for anything marked ✓.

| Category | Tool | Status | Notes |
|---|---|---|---|
| Shell | zsh | ✓ | with starship, zoxide, yazi |
| Package mgr | Homebrew 5.1.4 | ✓ | |
| Python mgr | uv 0.11.3 | ✓ | project venvs live here |
| Python | 3.14.3 (system) | ✓ | uv will pick 3.11 for the project venv |
| Git tooling | git 2.50.1, git-lfs 3.7.1, gh 2.89.0 | ✓ | |
| Container | Docker CLI 29.3.1, docker-compose 5.1.1 | ✓ | daemon = OrbStack (not running — see Phase 3) |
| Node toolchain | node 25.9 / bun 1.3.11 / pnpm 10.33 | ✓ | only needed for a couple of optional TS labs |
| HuggingFace | `hf` 1.11.0 at `~/.openharness-venv/bin/hf` | ✓ | used for pulling embedding + reranker weights |
| Inference apps | oMLX, vMLX | ✓ installed | start them in Phase 1 |
| LLM weights | Qwen3.6-35B-A3B-nvfp4, gemma-4-26B-A4B-it-heretic-4bit, gpt-oss-20b-MXFP4-Q8, gemma-4-31B-uncensored-heretic-mlx-4bit | ✓ on disk at `~/.omlx/models/` | |
| Shell wrappers | `omlx-python`, `omlx-mlx-lm`, `vmlx-python`, `vmlx-mlx-lm` | ✓ in `~/.zshrc` | added 2026-04-23 |

**Missing (optional):** `ripgrep` — install with `brew install ripgrep` if you want fast grep in the later labs.

---

## Phase 1 — Start the Inference Backends (~5 min)

### 1.1 Start oMLX

Launch `/Applications/oMLX.app` (or click its menu-bar icon if it's already running). Check the menu-bar → **"Server"** should show **`Running on 127.0.0.1:8000`**.

Your `~/.omlx/settings.json` already routes models like this:
```
opus_model   → Qwen3.6-35B-A3B-nvfp4
sonnet_model → gemma-4-26B-A4B-it-heretic-4bit
haiku_model  → gpt-oss-20b-MXFP4-Q8
```

Pick the tier in each API call via the `model` field.

### 1.2 Start vMLX

Launch `/Applications/vMLX.app`. In the vMLX **Settings → Server** tab, note the port (default is typically `8003` or `8002`). Enable the **OpenAI-compatible endpoint** if not already on. Load `gemma-4-31B-uncensored-heretic-mlx-4bit` from the vMLX model selector.

> **Record the vMLX port.** You'll need it for every Week 7/8 comparison. Add a line to the top of your lab `RESULTS.md`: `# vMLX on :<PORT>`.

### 1.3 Verify both are listening

```bash
# oMLX on :8000
curl -s http://127.0.0.1:8000/v1/models -H "Authorization: Bearer Shane@7162" | jq '.data[].id'

# vMLX — replace 8003 with the actual port from vMLX Settings
curl -s http://127.0.0.1:8003/v1/models | jq '.data[].id'
```

Expected: a list of model IDs from each server. If you get `curl: (7) Failed to connect`, the app isn't serving yet — open it and toggle the server on.

### 1.4 Smoke test one generation on each

```bash
# oMLX / sonnet (Gemma 26B)
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer Shane@7162" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-4-26B-A4B-it-heretic-4bit",
    "messages": [{"role":"user","content":"Reply with the single word OK."}],
    "max_tokens": 10
  }' | jq -r '.choices[0].message.content'

# vMLX (substitute your port)
curl -s http://127.0.0.1:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-4-31B-uncensored-heretic-mlx-4bit",
    "messages": [{"role":"user","content":"Reply with the single word OK."}],
    "max_tokens": 10
  }' | jq -r '.choices[0].message.content'
```

Both should return a short "OK"-ish response within a few seconds. If the first one is slow (20–40 s), that's the model being loaded into GPU memory — subsequent calls hit the warm cache and run fast.

---

## Phase 2 — Project Workspace + venv (~10 min)

Create the working directory and a fresh Python 3.11 venv via uv.

### 2.1 Directory layout

```bash
mkdir -p ~/code/agent-prep/{lab-01-vector-baseline,lab-02-rerank-compress,lab-03-rag-eval,lab-04-react-from-scratch,lab-05-pattern-zoo,lab-06-claude-code-map,lab-07-tool-harness,lab-08-schema-bench,lab-09-faithfulness-checker,lab-10-framework-shootout,capstone}
cd ~/code/agent-prep
git init
```

Create a top-level `.gitignore` so you never commit weights or API keys:

```bash
cat > .gitignore <<'EOF'
.venv/
__pycache__/
*.pyc
.env
.env.*
.DS_Store
models/
data/
*.sqlite
*.duckdb
traces/
.ragas_cache/
.omc/
EOF
```

### 2.2 Create the project venv

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
python --version     # → Python 3.11.x
```

### 2.3 Environment variables (`.env.example` + `.env`)

Both files are gitignored — `.env.example` is a local-only template so you never have to remember which variables the project needs. Any real token you paste in becomes a live secret the moment you save, which is why we don't commit the template either.

```bash
cat > .env.example <<'EOF'
# ===== Local inference =====
OMLX_BASE_URL=http://127.0.0.1:8000/v1
OMLX_API_KEY=Shane@7162
VMLX_BASE_URL=http://127.0.0.1:8003/v1       # update to your vMLX port
VMLX_API_KEY=not-used

# Model tier aliases (match ~/.omlx/settings.json)
MODEL_OPUS=Qwen3.6-35B-A3B-nvfp4
MODEL_SONNET=gemma-4-26B-A4B-it-heretic-4bit
MODEL_HAIKU=gpt-oss-20b-MXFP4-Q8
MODEL_VMLX=gemma-4-31B-uncensored-heretic-mlx-4bit

# ===== Cloud (Week 7 tool-call comparison + Week 8 schema bench) =====
# Leave blank until Phase 6 of this guide.
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ===== Local services =====
QDRANT_URL=http://127.0.0.1:6333
PHOENIX_COLLECTOR_ENDPOINT=http://127.0.0.1:6006

# ===== HuggingFace =====
HF_HOME=~/.cache/huggingface
# HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   # populate in §2.5
# In mainland China, route downloads through the community mirror.
# Comment out or flip to https://huggingface.co if outside CN.
HF_ENDPOINT=https://hf-mirror.com
EOF
cp .env.example .env
```

### 2.4 Auto-load `.env` with direnv

Rather than `source`-ing the file in every new shell, use **direnv** so every `cd` into the project auto-exports the variables and unsets them on `cd` out.

```bash
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

cd ~/code/agent-prep
echo 'dotenv' > .envrc
direnv allow
```

**Activate in your current terminal** (the hook was appended to `~/.zshrc`, but only *new* shells load it automatically):

```bash
source ~/.zshrc
cd ~/code/agent-prep    # expect: direnv: loading ~/code/agent-prep/.envrc
```

Verify:

```bash
echo "OMLX=$OMLX_BASE_URL  HF_ENDPOINT=$HF_ENDPOINT"
# → OMLX=http://127.0.0.1:8000/v1  HF_ENDPOINT=https://hf-mirror.com
```

> **Direnv gotchas worth knowing up front:**
> - direnv only loads env vars when your shell's `pwd` is *inside* the project tree. Run `hf`, `python`, or anything that uses these vars from inside `~/code/agent-prep`, never from `~`.
> - Editing `.envrc` requires re-running `direnv allow` (direnv hashes the file for security). Editing `.env` alone does not — direnv watches it via the `dotenv` directive.
> - The starship `(.venv)` indicator marks a directory's *presence*, not venv activation. Trust `echo $VIRTUAL_ENV` over the prompt.

### 2.5 HuggingFace token (required for downloads)

`hf download` works without a token but gets lower rate limits and slower CDN routing. A free read-only token fixes both.

1. Log in to https://huggingface.co/settings/tokens
2. Click **New token** → **Fine-grained** tab
3. Name it `agent-prep-lab-read`, scope = **Read** on public repos
4. Copy the `hf_...` value (HF shows it exactly once — if you lose it, delete and regenerate)
5. Paste it into `.env` by uncommenting and replacing the placeholder line:
   ```
   HF_TOKEN=hf_YOUR_REAL_TOKEN_HERE
   ```

Verify from inside the project directory (direnv will export `HF_TOKEN`):

```bash
cd ~/code/agent-prep
hf auth whoami           # → user=<your-hf-username>
```

> **On `HF_ENDPOINT=https://hf-mirror.com`:** the mirror is a reverse proxy over the real HF API. Same repo paths work (`BAAI/bge-m3`, etc.), `HF_TOKEN` forwards upstream so public and private downloads both succeed, and bandwidth from mainland China is typically 10–100× faster than direct access. If the mirror is ever unresponsive, comment the line out and requests fall back to `huggingface.co` with no other changes needed.

---

## Phase 3 — Docker Services: Qdrant + Phoenix (~10 min)

You use **OrbStack** as your Docker runtime. It's currently stopped (the daemon socket `/Users/yuxinliu/.orbstack/run/docker.sock` doesn't exist yet).

### 3.1 Start OrbStack

Launch `/Applications/OrbStack.app`. Menu-bar icon should turn green once the daemon is up. Verify:

```bash
docker info | head -3   # should print Server info without errors
docker ps               # should list nothing (empty is fine)
```

### 3.2 Qdrant (vector database)

```bash
docker run -d \
  --name qdrant \
  --restart unless-stopped \
  -p 6333:6333 -p 6334:6334 \
  -v ~/docker-data/qdrant:/qdrant/storage \
  qdrant/qdrant:latest
```

Verify:

```bash
curl -s http://127.0.0.1:6333/healthz      # → "healthz check passed"
open http://127.0.0.1:6333/dashboard       # Qdrant UI in a browser
```

### 3.3 Phoenix (observability / traces)

```bash
docker run -d \
  --name phoenix \
  --restart unless-stopped \
  -p 6006:6006 -p 4317:4317 \
  -v ~/docker-data/phoenix:/mnt/data \
  arizephoenix/phoenix:latest
```

Verify:

```bash
curl -sI http://127.0.0.1:6006 | head -1    # → HTTP/1.1 200 OK
open http://127.0.0.1:6006                  # Phoenix UI
```

### 3.4 Optional alternative: Langfuse (richer UI, more DB setup)

Skip unless you specifically prefer Langfuse's UI. Phoenix is lighter for the curriculum's scope.

### 3.5 Bring them back up after a reboot

OrbStack auto-restarts the containers (we added `--restart unless-stopped`). After reboot, only OrbStack needs launching.

---

## Phase 4 — Python Application Libraries (~15 min)

Install everything into the venv you made in Phase 2.

### 4.1 Core libraries (installs together, ~3 min over fast network)

```bash
cd ~/code/agent-prep
source .venv/bin/activate

uv pip install \
  openai anthropic pydantic pydantic-settings python-dotenv \
  qdrant-client sentence-transformers einops \
  instructor outlines xgrammar \
  langchain langchain-openai langchain-community langgraph \
  llama-index llama-index-vector-stores-qdrant \
  ragas trulens-eval datasets \
  arize-phoenix openinference-instrumentation-openai openinference-instrumentation-langchain \
  rich typer ipython jupyter \
  pytest pytest-asyncio
```

### 4.2 MLX bridge (so Python code can hit your local MLX stack directly)

```bash
uv pip install mlx-lm mlx-embedding-models
```

> Note: these duplicate what's already in oMLX/vMLX bundles, but **Option B** of the curriculum (fresh venv) expects a self-contained install. If you prefer to reuse oMLX's bundled MLX (Option A1 / A2), skip this command and use `omlx-python` / `vmlx-python` wrappers for MLX-specific scripts. Non-MLX code doesn't care either way — it all goes through the OpenAI-compatible HTTP endpoint.

### 4.3 DuckDuckGo search (free tool for Week 4's agent loop)

```bash
uv pip install ddgs
```

### 4.4 Optional — nicer CLI for model downloads

Already available at `~/.openharness-venv/bin/hf`. If you want it on PATH in this venv:

```bash
uv pip install huggingface_hub   # provides `hf` inside the venv
```

### 4.5 Verify imports

```bash
python -c "
import openai, anthropic, qdrant_client, instructor, outlines, pydantic
import langchain, langgraph, llama_index, ragas, phoenix
from sentence_transformers import SentenceTransformer
print('core stack: OK')
"
```

Expect: `core stack: OK`. Any `ImportError` → the matching `uv pip install <package>` failed; re-run it alone to see the real error.

---

## Phase 5 — Download Embedding + Reranker Models (~20 min, ~3 GB disk)

You'll use these locally for all retrieval labs.

### 5.1 BGE-M3 (dense + sparse + multi-vector embeddings, 1024-dim)

```bash
hf download BAAI/bge-m3 --local-dir ~/models/bge-m3
```

Size: ~2.3 GB. Works via `sentence-transformers` directly on MPS (Apple GPU).

Smoke test:

```bash
python -c "
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('$HOME/models/bge-m3', device='mps', trust_remote_code=True)
v = m.encode(['hello agent world'])
print('BGE-M3 dim:', v.shape, '| device:', m.device)
"
```

Expected: `BGE-M3 dim: (1, 1024) | device: mps`.

### 5.2 BGE-reranker-v2-m3 (cross-encoder reranker)

```bash
hf download BAAI/bge-reranker-v2-m3 --local-dir ~/models/bge-reranker-v2-m3
```

Size: ~1.1 GB.

Smoke test:

```bash
python -c "
from sentence_transformers import CrossEncoder
m = CrossEncoder('$HOME/models/bge-reranker-v2-m3', device='mps')
s = m.predict([('what is mlx?', 'MLX is Apple\'s array framework.')])
print('reranker score:', float(s[0]))
"
```

Expected: a positive float, e.g. `0.91`.

### 5.3 Nomic Embed v2 (optional, for Week 1's model comparison lab)

```bash
hf download nomic-ai/nomic-embed-text-v2-moe --local-dir ~/models/nomic-embed-v2
```

Size: ~2.1 GB. Only needed if you want a 3-way embedding comparison; Week 1 lab works fine with just BGE-M3.

### 5.4 Why there is no MLX-quantized BGE-M3 variant

You might look for an `mlx-community/bge-m3-*` conversion — it doesn't exist, and the reasoning is worth internalizing. `mlx-community` hosts LLMs (Llama, Qwen, Gemma, Phi), not embedding models. Two reasons nobody bothered porting BGE-M3:

1. **BGE-M3 already runs at ~85–95% of peak on Apple Silicon via PyTorch MPS.** MLX's wins on LLMs come from fused attention kernels and KV-cache optimizations that matter for autoregressive generation — a BERT-style encoder doing one forward pass per batch gains almost nothing from those optimizations.
2. **4-bit quantization hurts embedding retrieval much more than LLM perplexity.** For LLMs, 4-bit costs you 1–3% because next-token is a 50k-way argmax that tolerates logit noise. For embeddings, the output vector *is* the similarity-comparison target — quantization noise directly corrupts retrieval geometry, dropping MRR@10 by 5–15% on MTEB benchmarks.

**Stick with `BAAI/bge-m3` on MPS.** If you later need a smaller footprint, the credible options are `aapot/bge-m3-onnx` (ONNX Runtime + CoreML) or `gpustack/bge-m3-GGUF` (llama.cpp embedding server). Don't try to `mlx_lm.convert` BGE-M3 yourself — `mlx_lm` targets causal LMs and will fail on BERT architectures.

---

## Phase 6 — Cloud API Keys (only for Weeks 7 & 8, ~5 min)

**Do this only when you start Week 7.** Total spend across both weeks ≈ $8.

### 6.1 OpenAI (Week 8 schema-reliability benchmark, ~$2)

1. Create an account + add a $5 minimum payment method at https://platform.openai.com/
2. Set a **hard spend limit of $5** in Billing → Usage limits. (This is your guardrail.)
3. Create an API key.
4. Add it to `.env`:
   ```bash
   echo "OPENAI_API_KEY=sk-proj-xxxxxxxx" >> .env
   ```

### 6.2 Anthropic (Week 7 tool-calling comparison, ~$0.50)

1. Create an account + add $5 credit at https://console.anthropic.com/
2. Set a **hard spend limit of $5**.
3. Create an API key.
4. Add it to `.env`:
   ```bash
   echo "ANTHROPIC_API_KEY=sk-ant-api03-xxxx" >> .env
   ```

### 6.3 Verify keys work (smoke test)

```bash
# direnv already exported OPENAI_API_KEY + ANTHROPIC_API_KEY when you cd'd in
python -c "
from openai import OpenAI
from anthropic import Anthropic
r = OpenAI().chat.completions.create(model='gpt-4o-mini', messages=[{'role':'user','content':'Reply \"OK\"'}], max_tokens=5)
print('OpenAI:', r.choices[0].message.content)
r = Anthropic().messages.create(model='claude-haiku-4-5', max_tokens=5, messages=[{'role':'user','content':'Reply \"OK\"'}])
print('Anthropic:', r.content[0].text)
"
```

Each call costs < $0.0001.

---

## Phase 7 — End-to-End Smoke Test (~10 min)

One script that exercises every layer of the stack. If this passes, you can start Week 1 with zero surprises.

Save as `~/code/agent-prep/smoke-test.py`:

```python
"""Week 0 smoke test — verifies inference, embeddings, vector store, reranker, traces."""
import os, time
from pathlib import Path
from openai import OpenAI
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

HOME = os.path.expanduser("~")

# 1. oMLX chat completion (sonnet tier — Gemma 26B)
client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="Shane@7162")
t0 = time.time()
resp = client.chat.completions.create(
    model="gemma-4-26B-A4B-it-heretic-4bit",
    messages=[{"role": "user", "content": "Reply with exactly: smoke-test-ok"}],
    max_tokens=64,   # surgery-modified models burn extra template tokens; 20 is too tight
)
# OpenAI-compat lets message.content be null when a model emits tool_calls or
# reasoning_content instead — tolerate both shapes rather than crashing on .strip().
choice = resp.choices[0]
text = (choice.message.content or getattr(choice.message, "reasoning_content", None) or "").strip()
if not text:
    raise RuntimeError(
        f"oMLX returned empty content. finish_reason={choice.finish_reason}, "
        f"usage={resp.usage}, raw={choice.message.model_dump()}"
    )
print(f"[1/5] oMLX chat OK in {time.time()-t0:.1f}s → {text}")

# 2. Embedding (BGE-M3 on MPS)
emb = SentenceTransformer(f"{HOME}/models/bge-m3", device="mps", trust_remote_code=True)
vec = emb.encode(["hello agent world"])
print(f"[2/5] BGE-M3 embed OK → shape {vec.shape}")

# 3. Qdrant — create collection, upsert a point, search
qd = QdrantClient(url="http://127.0.0.1:6333")
if qd.collection_exists("smoke"):
    qd.delete_collection("smoke")
qd.create_collection("smoke", vectors_config=VectorParams(size=1024, distance=Distance.COSINE))
qd.upsert("smoke", points=[PointStruct(id=1, vector=vec[0].tolist(), payload={"text": "hello agent world"})])
# qdrant-client removed .search() in 1.15 — use .query_points() which returns
# a QueryResponse with a .points list.
hit = qd.query_points("smoke", query=vec[0].tolist(), limit=1).points[0]
print(f"[3/5] Qdrant upsert+search OK → id={hit.id} score={hit.score:.3f}")

# 4. Reranker — cross-encode a pair
rr = CrossEncoder(f"{HOME}/models/bge-reranker-v2-m3", device="mps")
score = float(rr.predict([("what is mlx?", "MLX is Apple's array framework.")])[0])
print(f"[4/5] BGE reranker OK → score {score:.2f}")

# 5. Phoenix reachable
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:6006") as r:
    print(f"[5/5] Phoenix UI reachable → HTTP {r.status}")

print("\nALL SMOKE TESTS PASSED — ready for Week 1.")
```

Run:

```bash
python ~/code/agent-prep/smoke-test.py
```

Expected output:

```
[1/5] oMLX chat OK in 1.2s → smoke-test-ok
[2/5] BGE-M3 embed OK → shape (1, 1024)
[3/5] Qdrant upsert+search OK → id=1 score=1.000
[4/5] BGE reranker OK → score 0.91
[5/5] Phoenix UI reachable → HTTP 200

ALL SMOKE TESTS PASSED — ready for Week 1.
```

**Troubleshooting:**
- `[1/5] Connection refused` → oMLX isn't serving. Open the app, toggle server on.
- `[2/5] CUDA not available` → the BGE code defaulted to `cuda` instead of `mps`. Confirm `device='mps'` in the call.
- `[3/5] ConnectionError` → OrbStack is off, or Qdrant container died. `docker ps` to check.
- `[4/5] OSError: can't find model at ...` → Phase 5.2 didn't finish. `ls ~/models/bge-reranker-v2-m3` to verify.
- `[5/5] URLError` → Phoenix container is off. `docker start phoenix`.

---

## Phase 8 — Nice-to-Have Extras (~15 min, optional)

### 8.1 Anki for flashcards

```bash
brew install --cask anki
```

Create a deck called **"Agent Interview"** with card types: Q → A → optional code example.

### 8.2 ripgrep (fast grep, used in a few later labs)

```bash
brew install ripgrep
```

### 8.3 direnv

Already covered — see **§2.4 Auto-load `.env` with direnv**. It's part of the required setup, not optional, because every subsequent phase assumes env vars are auto-exported on `cd`.

### 8.4 A second `cl`-style alias for vMLX

If you want the `claude` CLI to target vMLX too (with the JANG model as its "opus"), add to `~/.zshrc` (replace `8003` with your actual vMLX port):

```bash
# Claude Code → local vMLX server (gemma-4-31B-uncensored-heretic-mlx-4bit)
alias clv="ANTHROPIC_BASE_URL='http://127.0.0.1:8003' ANTHROPIC_DEFAULT_OPUS_MODEL='gemma-4-31B-uncensored-heretic-mlx-4bit' ANTHROPIC_DEFAULT_SONNET_MODEL='gemma-4-31B-uncensored-heretic-mlx-4bit' ANTHROPIC_DEFAULT_HAIKU_MODEL='gemma-4-31B-uncensored-heretic-mlx-4bit' API_TIMEOUT_MS=3000000 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 claude --dangerously-skip-permissions"
```

### 8.5 Install agent-skills plugin for Claude Code (★ highly recommended)

During labs 1–11 and especially throughout the Capstone in Week 12, install **[Addy Osmani's agent-skills](https://github.com/addyosmani/agent-skills)** — a Claude Code plugin (21.8k⭐, MIT-licensed) that encodes **20 senior-engineer workflow skills** as executable `SKILL.md` files your `claude` CLI can invoke via slash commands. Each skill enforces discipline at a specific lifecycle phase: a skill will *refuse to mark a step complete* until its verification criteria are met.

Run these two slash commands inside any Claude Code session (they're not bash — type them at the Claude prompt):

```
/plugin marketplace add addyosmani/agent-skills
/plugin install agent-skills@addy-agent-skills
```

Verify:

```
/plugin
```

You should see `agent-skills` listed under installed plugins.

> **Name decoded:** `addyosmani/agent-skills` is the GitHub repo. The marketplace defines itself as `addy-agent-skills` in `.claude-plugin/marketplace.json`, and the one plugin it exposes is called `agent-skills` — hence `agent-skills@addy-agent-skills`. Claude Code uses `<plugin-name>@<marketplace-name>` to disambiguate when multiple marketplaces expose plugins with the same short name.
>
> **Do not `git clone` the repo directly into `~/.claude/plugins/`** — the plugin system manages its own directory layout (hashed paths under `~/.claude/plugins/cache/`) and won't register a bare clone. The `/plugin install` command is the only supported path.

**What you get:** six slash commands mapped to the software lifecycle — `/spec` (Define), `/plan` (Plan), `/build` (Build), `/test` (Verify), `/review` (Review), `/ship` (Ship) — backed by 20 skill files covering spec-driven-development, TDD, incremental-implementation, code-review-and-quality, code-simplification, security-and-hardening (OWASP Top 10), performance-optimization (Core Web Vitals), git-workflow-and-versioning, ci-cd-and-automation, shipping-and-launch, documentation-and-ADRs, debugging-and-error-recovery (5-step triage), and more.

**Why install now, not just in Week 12:** practicing with the slash commands during the Week 4–7 labs builds muscle memory for discipline-enforced workflows. By Week 12 the commands feel native, which is exactly when you want them least intrusive.

> **Interview angle.** "I shipped the capstone using Addy Osmani's agent-skills throughout — the `/ship` command's pre-launch checklist caught 3 bugs I would have missed, and the `/review` command's five-axis criteria made every PR cleaner than my unaided review would have been." That is a concrete tool-usage story hiring managers at dev-tools companies will recognize and value.

#### Troubleshooting: `/plugin install` fails with SSH host key error

If `/plugin install` reports something like:

```
Failed to clone repository: ...
No ED25519 host key is known for github.com and you have requested strict checking.
Host key verification failed.
```

…there are **two stacked problems** to fix, in order. This affects any first-time plugin install on a machine that has never connected to GitHub via SSH (which is most fresh macOS setups, since `gh` defaults to HTTPS for its own operations).

**Problem 1 — `~/.ssh/known_hosts` is missing GitHub's keys.** The plugin's git clone hits `github.com:22` over SSH, and OpenSSH refuses to proceed under StrictHostKeyChecking when it has no recorded fingerprint to compare against.

**Problem 2 — Plugin installer prefers SSH form (`git@github.com:...`) for cloning.** Even with host keys fixed, SSH would then fail at the auth stage because you have no SSH key registered with your GitHub account. For installing public-repo plugins, redirecting git to HTTPS for github.com URLs is the right fix — no auth needed, no key management.

**Fix (one-time, ~30 seconds — then the plugin install just works):**

```bash
# Step 1 — fetch GitHub's host keys and verify fingerprints against published values
ssh-keyscan -t rsa,ecdsa,ed25519 github.com 2>/dev/null > /tmp/github_keys.txt
ssh-keygen -lf /tmp/github_keys.txt
# Compare each printed fingerprint against the official list at
# docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints
# As of 2026-04-24 they should be:
#   RSA    : SHA256:uNiVztksCsDhcc0u9e8BujQXVUpKZIDTMczCvj3tD2s
#   ECDSA  : SHA256:p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM
#   ED25519: SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU
# If they match, append to known_hosts:
mkdir -p ~/.ssh && touch ~/.ssh/known_hosts
grep -v "^#" /tmp/github_keys.txt >> ~/.ssh/known_hosts
chmod 600 ~/.ssh/known_hosts

# Step 2 — redirect git to use HTTPS for github.com (avoids needing an SSH key)
# Use --add (NOT plain `git config`) so both rewrite rules are kept; plain assign overwrites.
git config --global --add url."https://github.com/".insteadOf "git@github.com:"
git config --global --add url."https://github.com/".insteadOf "ssh://git@github.com/"

# Verify both rules survived (should print TWO lines)
git config --global --get-all url."https://github.com/".insteadOf

# Sanity test — this should now succeed without prompting
git ls-remote git@github.com:addyosmani/agent-skills HEAD
```

Then retry the install:

```
/plugin install agent-skills@addy-agent-skills
```

> **Why both fixes are needed.** Either alone leaves a problem: with only the host keys, SSH gets past the host-check but fails at auth (no SSH key); with only the HTTPS rewrite, git would still try the original SSH form for some sub-operations. Doing both makes the install bulletproof and unblocks every future plugin install + any github-hosted MCP that includes a clone step.

> **Side benefit.** The HTTPS rewrite also speeds up `gh repo clone`, eliminates SSH-key-setup as a prereq for any future `git clone git@github.com:...` paste, and removes one entire class of "why doesn't git work" errors for the rest of the curriculum. The cost is zero — if you ever do want SSH-based push access later, undo with `git config --global --unset-all url."https://github.com/".insteadOf`.

### 8.6 Portable model-runner script

Save as `~/code/agent-prep/run_local.py` so every lab has a one-line model call:

```python
import os
from openai import OpenAI

_omlx = OpenAI(base_url=os.getenv("OMLX_BASE_URL", "http://127.0.0.1:8000/v1"),
               api_key=os.getenv("OMLX_API_KEY", "not-used"))
_vmlx = OpenAI(base_url=os.getenv("VMLX_BASE_URL", "http://127.0.0.1:8003/v1"),
               api_key=os.getenv("VMLX_API_KEY", "not-used"))

TIERS = {
    "opus": (_omlx, os.getenv("MODEL_OPUS", "Qwen3.6-35B-A3B-nvfp4")),
    "sonnet": (_omlx, os.getenv("MODEL_SONNET", "gemma-4-26B-A4B-it-heretic-4bit")),
    "haiku": (_omlx, os.getenv("MODEL_HAIKU", "gpt-oss-20b-MXFP4-Q8")),
    "vmlx": (_vmlx, os.getenv("MODEL_VMLX", "gemma-4-31B-uncensored-heretic-mlx-4bit")),
}

def chat(tier: str, messages: list[dict], **kwargs) -> str:
    client, model = TIERS[tier]
    r = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return r.choices[0].message.content
```

Use it anywhere:

```python
from run_local import chat
print(chat("opus", [{"role": "user", "content": "Plan a 3-step recipe."}], max_tokens=200))
```

---

## Configuration Walkthroughs

### Walkthrough 1 — Shell Wrapper Pattern (~8.2)

The shell wrappers in `~/.zshrc` (added in Phase 1) let you call local models from any terminal:

```bash
omlx-python  # launches Python with OMLX_BASE_URL pre-set
vmlx-python  # launches Python with VMLX_BASE_URL pre-set
```

**Why this pattern:** Each lab runs in its own venv (isolation), but still needs to know where oMLX/vMLX are listening. Environment variables (not hardcoded URLs) let you swap inference backends. If you move oMLX to port 9000, one `.zshrc` edit fixes all 12 labs.

**Block 1 — Shell wrapper definition:**
```bash
alias omlx-python='OMLX_BASE_URL=http://127.0.0.1:8000/v1 /Users/yuxinliu/.openharness-venv/bin/python'
alias vmlx-python='VMLX_BASE_URL=http://127.0.0.1:8003/v1 /Users/yuxinliu/.openharness-venv/bin/python'
```

The wrapper sets two things: (1) the URL environment variable, (2) the absolute path to the Python interpreter in the venv. Avoid `which python` here — it is shell-version dependent and can pick the system Python instead of your venv.

**Common modifications:** If oMLX is on a different port (say 9000), change `8000` to `9000`. If vMLX is on 8002 instead of 8003, update accordingly. These settings live in `~/.zshrc` because they are machine-specific and global.

### Walkthrough 2 — uv Project Isolation Pattern (~4)

Each lab creates a venv via `uv`:

```bash
cd ~/code/agent-prep/lab-01-vector-retrieval
uv venv
uv sync --requirement requirements.txt
```

**Why this pattern:** `uv` is 100x faster than `pip`. It also enforces version locks — `requirements.txt` pins exact versions (e.g., `anthropic==0.24.2`). If W1 worked with Anthropic SDK 0.24.2, W6 (six weeks later) still runs with 0.24.2, not a broken 0.30.0 from PyPI. No silent upgrade surprises.

**Block 1 — Venv initialization:**
The first call `uv venv` creates `.venv/` locally. The second call `uv sync` installs packages. `uv` caches wheels in `~/.cache/uv/`, so the second lab's install is instant (wheels already downloaded).

**Common modifications:** If `requirements.txt` is in a different location, adjust the path. If you add a new package mid-lab, run `uv pip install package-name` to add it to the .venv without recreating the entire venv.

---

## Bad-Case Journal

> _W0 has no runnable lab — it is environment setup only. Bad-case entries will be added as users hit real setup failures and document them with reproducible symptoms and fixes. Pre-experiment speculation about "what could go wrong" was removed in the 2026-05-07 audit pass; the chapter spec ([[CLAUDE.md]] §6) requires entries to be anchored to observed events, not predicted ones._

---

## Optional Pre-Read Before Week 1

> **Never built an agent before?** Read hoeem's ["I want to build an AI agent today"](https://x.com/hooeem/status/2037250422403113188) (~30 min) for a gentle orientation before the curriculum goes deep. It covers the core loop, the five Anthropic workflow patterns, and beginner-friendly SDK examples (Anthropic + OpenAI) at a much lighter depth than Weeks 4–7. Skip if you've already built even one agent — the curriculum's Week 4 Theory Primer covers the same material with production depth.

---

## Final Checklist (tick each before starting Week 1)

- [ ] oMLX running on `:8000` — `curl http://127.0.0.1:8000/v1/models` returns model list
- [ ] vMLX running on its port — you recorded the port somewhere
- [ ] OrbStack running — `docker ps` shows no error
- [ ] Qdrant container up — http://127.0.0.1:6333/dashboard loads
- [ ] Phoenix container up — http://127.0.0.1:6006 loads
- [ ] `~/code/agent-prep/.venv` exists, Python 3.11.x
- [ ] `.env` populated (cloud keys can wait until Week 7)
- [ ] BGE-M3 at `~/models/bge-m3`, reranker at `~/models/bge-reranker-v2-m3`
- [ ] `python smoke-test.py` prints `ALL SMOKE TESTS PASSED`
- [ ] (Optional) Anki installed, empty deck created

Once everything is ticked, start **Week 1 — Embedding & Vector Retrieval Fundamentals**.

---

## Appendix — Disk Footprint

| Item | Approx. size |
|---|---|
| oMLX app + Python bundle | ~2 GB |
| vMLX app + Python bundle | ~2 GB |
| oMLX models (Qwen 3.6 + Gemma 26B + gpt-oss 20B) | ~45 GB |
| vMLX model (Gemma 31B JANG) | ~19 GB |
| BGE-M3 | ~2.3 GB |
| BGE-reranker-v2-m3 | ~1.1 GB |
| Nomic Embed v2 (optional) | ~2.1 GB |
| Project venv + libraries | ~2.5 GB |
| Qdrant + Phoenix Docker images | ~1.5 GB |
| **Working total (no Nomic)** | **~75 GB** |

Keep at least ~25 GB free for model loading overhead and traces.

---

## Appendix — Recovering From a Broken State

If something stops working mid-curriculum:

```bash
# 1. Restart inference apps (fastest fix)
killall oMLX vMLX 2>/dev/null
open /Applications/oMLX.app
open /Applications/vMLX.app

# 2. Restart Docker services
docker restart qdrant phoenix

# 3. Rebuild the project venv (loses nothing — no state in venv)
cd ~/code/agent-prep
rm -rf .venv
uv venv --python 3.11 .venv
source .venv/bin/activate
# Re-run Phase 4.1 / 4.2

# 4. Full reset (nuclear)
docker rm -f qdrant phoenix
rm -rf ~/docker-data/{qdrant,phoenix}
# Re-run Phase 3.2 / 3.3
```

Your Anki deck, bad-case journal, and lab `RESULTS.md` files are git-tracked — never lost.

— end —


---

## Interview Soundbites

**Soundbite 1 — Why local-first matters for an agent stack.** Running inference locally on Apple Silicon eliminated the latency floor that makes iterative agent loops impractical at cloud prices. With oMLX serving Gemma 26B on `:8000`, warm-cache calls return in roughly 1.2 seconds — fast enough for a ReAct loop where the model calls tools 5–10 times per task. Cloud equivalents at that throughput would cost dollars per run, not fractions of a cent, which makes systematic bad-case journaling financially impossible.

**Soundbite 2 — Why BGE-M3 runs on PyTorch MPS rather than MLX.** I investigated whether to port BGE-M3 to MLX and decided against it. BERT-style encoders do one forward pass per batch, so they gain almost nothing from MLX's fused autoregressive kernels. More importantly, 4-bit quantization — the technique that makes LLMs viable on 48 GB unified memory — degrades embedding geometry by 5–15% on MTEB MRR@10, because the output vector is the similarity target, not a 50k-way argmax that tolerates logit noise. BGE-M3 on MPS at fp32 already hits 85–95% of peak hardware throughput.

**Soundbite 3 — Three-tier model routing as a cost-control primitive.** I mapped the oMLX model roster to haiku/sonnet/opus tiers before writing a single lab: gpt-oss-20B for fast single-hop retrieval checks, Gemma 26B for standard reasoning, Qwen 35B for architecture and deep analysis. Every script selects a tier by name, not by model ID, so swapping a backend model never touches application code. Cloud APIs are deferred until Weeks 7–8 where the curriculum explicitly needs them, capping total spend at roughly $8 across the full 12 weeks.

---

## References

- **Apple MLX GitHub (ml-explore/mlx)** — https://github.com/ml-explore/mlx — primary framework repo; explains unified memory + fused attention kernels.
- **mlx-community on HuggingFace** — https://huggingface.co/mlx-community — model hub for MLX-quantized LLMs.
- **BAAI/bge-m3 model card** — https://huggingface.co/BAAI/bge-m3 — three embedding modes documentation.
- **Qdrant documentation** — https://qdrant.tech/documentation/ — query_points API, vector config schema.
- **Arize Phoenix** — https://docs.arize.com/phoenix — OTLP trace collector + UI.
- **oMLX (omlx.app)** — macOS inference server wrapping mlx-lm with OpenAI-compatible HTTP.
- **vMLX (vmlx.app)** — companion app for second isolated MLX inference process.
- **uv package manager** — https://docs.astral.sh/uv/ — Python environment manager used throughout.

---

## Cross-References

- **Builds on:** Familiarity with Python venvs (uv/pip), Docker basics, OpenAI Chat Completions API shape.
- **Distinguish from:** MLX (Apple's array framework, used inside oMLX/vMLX) vs PyTorch+MPS (used for BGE-M3, different optimization profile) vs Ollama (cross-platform LLM runner, not used here) vs llama.cpp (CPU-first quantized; slower on Apple Silicon for large models).
- **Connects to:** Every subsequent week — oMLX/vMLX endpoints, Qdrant collection, Phoenix collector, BGE-M3, BGE reranker are persistent infrastructure all labs build on.
- **Foreshadows:** W11 System Design (three-tier routing → cost-aware dispatch), W12 Capstone (full-stack smoke test → production startup probe).
