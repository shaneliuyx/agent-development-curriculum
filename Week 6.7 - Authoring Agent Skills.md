# Week 6.7 - Authoring Agent Skills (Anthropic Pattern)

## Why This Week Matters

You have been a skill consumer for six weeks. Every time you ran `/benchmark`, `/canary`, or `/autoresearch`, you were on the receiving end of a SKILL.md file that someone authored and shipped. That file loaded into your Claude Code session, gave the model a specialized identity, constrained its tool access, and handed it a workflow it would otherwise invent fresh every time — inconsistently.

Production teams ship skills because ad-hoc prompting doesn't scale. A skill is the unit of repeatable agent capability: write it once, version it, install it globally, share it across a team. The gap between "I prompt Claude well" and "I ship agent tooling" is exactly this: do you have skills in `~/.claude/skills/`, or do you rephrase the same instructions session after session?

This week closes that gap. You will learn the anatomy of a skill file, the mechanics of trigger engineering, and you will author three production-quality skills from scratch. By the end you will understand why the description field is harder to write than the body, and why getting it wrong makes your skill either useless or noisy.

---

## Theory Primer — What Is a Skill?

### The Loading Mechanism

When Claude Code starts a session, it reads every installed skill's frontmatter `description` field and loads the descriptions into the system prompt context. When you send a message, the model compares your message against those descriptions and decides which skill (if any) to invoke via the `Skill` tool. The full SKILL.md body is then loaded into context only at invocation time.

This matters architecturally: the description is your skill's only advertisement. The body is loaded lazily. A skill whose description fails to match relevant user intent will never fire. A skill whose description is too broad will fire on everything.

The install location is `~/.claude/skills/<skill-name>/SKILL.md` for global skills or `.claude/skills/<skill-name>/SKILL.md` for project-local skills. Claude Code scans both directories on session start.

### Anatomy of a SKILL.md

```yaml
---
name: skill-name
description: |
  One to three sentences. What it does.
  Use when: specific triggers, keywords, contexts.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
---
```

The `name` field is the slash-command identifier: `name: code-review` means the user can type `/code-review` to invoke it explicitly. The `description` is the auto-discovery text. The `allowed-tools` list restricts which tools the model can use — this is your security surface.

**Body sections:**

- **Quick start / User-invocable**: one paragraph stating what triggers the skill and its argument variants.
- **Instructions / Workflow**: numbered phases with specific commands, output formats, and decision branches.
- **Escalation and stop conditions**: when to stop and ask, when to abort.
- **Examples**: concrete before/after or input/output pairs. Highest-leverage section because few-shot patterns are how the model learns intent faster than prose.

### Comparing to MCP Tools

An MCP tool is a callable function with a JSON schema for inputs. The model invokes it by issuing a structured call and receiving a structured response.

A skill is a loaded prompt. It injects instructions, workflows, and constraints into the model's context window. The model reads every word of the skill body and uses it to guide its own reasoning. There is no separate runtime, no server, no network call.

**Practical consequence:** MCP tools are better for deterministic, side-effectful operations (query a database, call an API). Skills are better for multi-step workflows where the model needs judgment at each step. A skill can call MCP tools. The reverse is not meaningful.

### Comparing to Custom GPTs and Cursor Rules

Custom GPTs (OpenAI) package a system prompt plus actions in a separate runtime. Cursor rules are always-on system prompt injections scoped to a repository — no invocation mechanism, no lazy loading.

Claude Code skills sit between: prompt-based like Cursor rules, but lazily loaded, invokable explicitly by slash command, and they carry a security model via `allowed-tools`.

---

## Trigger Engineering — Writing a Description That Works

The description field is the hardest part of authoring a skill. The body is just clear instructions. The description requires you to predict the space of user intents that should route to your skill, without capturing intents that belong elsewhere.

### Five Anti-Patterns

1. **Pure capability statement with no triggers.** `"Helps with code quality."` — no basis for the model to prefer it.
2. **Overlapping triggers with no differentiation.** `"Use when: review, check, analyze, inspect"` — applies to everything.
3. **Action verbs so common they match everything.** `"Use when: improve something"` — describes all software work.
4. **Triggers that are file-type based without context.** `"Use when: TypeScript files"` — fires constantly.
5. **Negation-only scoping.** `"Use when: not a simple question"` — model cannot reliably apply negation.

### Five Patterns That Work

1. **Trigger on proper nouns and tool names.** `"Use when: PR, pull request, diff, git review"`.
2. **Pair capability with explicit activity phrases.** `"Runs post-deploy canary monitoring. Use when: 'monitor deploy', 'post-deploy check', 'watch production'."`.
3. **Include the namespace for suite-based skills.** Append `(your-org)` for provenance.
4. **Separate what it is from when to use it.** First sentence: capability. Second sentence: trigger context.
5. **List `do_not_use_when` in the body, not the description.** Description for matching, body for exit conditions.

---

## Lab — Build 3 Production Skills (~6 hours)

### Skill 1: `code-review`

```markdown
---
name: code-review
description: |
  Static analysis and structured review for code diffs and pull requests.
  Checks style, correctness, security surface, and test coverage gaps.
  Use when: "review", "PR", "pull request", "diff", "review my code",
  "code review", "check this diff".
allowed-tools:
  - Bash
  - Read
  - Glob
---

# Code Review

You are a senior engineer reviewing code before merge. Catch bugs, flag security issues, identify missing test coverage. Do not nitpick style unless it creates bugs.

## Workflow

### Phase 1: Context
```bash
git diff HEAD~1 --stat
git log -1 --oneline
```

### Phase 2: Static checks
```bash
[ -f package.json ] && npx eslint --max-warnings 0 . 2>&1 | tail -20
[ -f .flake8 ] && python -m flake8 . 2>&1 | tail -20
```

### Phase 3: Structured review
For each finding:
```
[SEVERITY] file.ts:42 — short description
Context: one sentence of why this matters.
Suggestion: concrete alternative if applicable.
```
SEVERITY: CRITICAL | HIGH | MEDIUM | LOW.

### Phase 4: Coverage gap check
```bash
git diff HEAD~1 --name-only | grep -v test | grep -v spec
```

### Phase 5: Summary
```
REVIEW SUMMARY
══════════════
Files reviewed: N
Critical: N  High: N  Medium: N  Low: N
Verdict: APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION
```

## Do not use when
- User asking general questions about how code works (no diff context).
- User wants to refactor (use a refactor skill).

## Escalation
If you find a CRITICAL security issue, stop the review, state the finding clearly, and do not bury it in a list.
```

### Skill 2: `deploy-canary`

```markdown
---
name: deploy-canary
description: |
  Post-deploy canary monitoring. Polls error rates, latency, and health
  endpoints for 30 minutes after a deploy. Recommends rollback when
  thresholds are breached.
  Use when: "deploy", "canary", "post-deploy check", "monitor deploy",
  "merged to main".
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
---

# Deploy Canary

You are an on-call SRE watching a fresh deploy. You poll metrics, watch error rates, and make the rollback call when numbers go wrong. Show the data and make a recommendation — never guess.

## Arguments
- `/deploy-canary <service>`
- `/deploy-canary --url <health-endpoint>`
- `/deploy-canary --duration 15m`

## Workflow

### Phase 1: Baseline
```bash
curl -sf <health-endpoint>/health | jq '{status, version, uptime}'
```

### Phase 2: Monitor loop (30 min, every 2 min)
```bash
for i in $(seq 1 15); do
  START=$(date +%s%3N)
  STATUS=$(curl -sf -o /dev/null -w "%{http_code}" <health-endpoint>/health)
  END=$(date +%s%3N)
  echo "$(date -u +%H:%M:%S) status=$STATUS latency=$((END - START))ms"
  sleep 120
done
```

### Phase 3: Threshold breach protocol
On CRITICAL:
```
CANARY ALERT — CRITICAL THRESHOLD BREACHED
RECOMMENDATION: ROLLBACK
Rollback command (confirm before running):
  git revert HEAD && git push
```
STOP. Wait for user confirmation.

### Phase 4: Report
Write `.canary/YYYY-MM-DD-HH-MM-<service>.md` with full log + verdict: PASS | WARN | ROLLBACK_RECOMMENDED.

## Escalation
If you cannot reach the health endpoint in Phase 1: report BLOCKED. Do not start monitoring against a dead endpoint.
```

### Skill 3: `internal-knowledge`

```markdown
---
name: internal-knowledge
description: |
  Answers questions using the internal knowledge base. Use when: user asks
  about internal systems, internal APIs, internal tooling, or uses
  company-specific product names (Orion, DataBridge, AuthService, PlatformCore).
  Do NOT use for general programming questions.
allowed-tools:
  - Bash
---

# Internal Knowledge

You surface answers from the internal knowledge base. Always query the RAG endpoint first — never answer from training data when an internal topic is involved.

## Trigger phrases
Trigger on:
- Internal product names: Orion, DataBridge, AuthService, PlatformCore
- "internal docs", "confluence", "our wiki"
- Team names: Platform Team, Data Eng

Do not trigger on:
- Generic "how do I use React" questions
- Standard library questions

## Workflow

### Phase 1: RAG query
```bash
curl -sf -X POST "$INTERNAL_KB_URL/query" \
  -H "Authorization: Bearer $INTERNAL_KB_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"<user_question>\", \"top_k\": 5}" \
  | jq '.results[] | {score, title, excerpt}'
```

### Phase 2: Answer construction
1. Cite source title and link.
2. Flag documents older than 90 days.
3. If all scores < 0.6, say: "No confident match. Try direct search: <INTERNAL_KB_URL>/search?q=..."

## Output format
```
INTERNAL KNOWLEDGE RESULT
Query: [what was searched]
Sources: N documents (top score: X.XX)

Answer:
[2-5 sentences]

Sources:
- [Title] (score: 0.94, updated: YYYY-MM-DD) — <link>

Confidence: HIGH | MEDIUM | LOW
```

## Security note
This skill has `allowed-tools: [Bash]` only. Credentials read from env vars — never hardcoded.
```

---

## Skill Distribution and Versioning

### Install locations

- Global: `~/.claude/skills/<name>/SKILL.md`
- Project-local: `.claude/skills/<name>/SKILL.md`

Project-local takes precedence when both exist.

### Marketplace pattern

skills.sh and oh-my-claudecode follow the same convention: install as directories under `~/.claude/skills/`. The `version` field enables update checking. Install via `npx skills add <repo>@<skill>` or manual copy.

### Trust model

Skills run with the full permissions of the Claude Code session. The `allowed-tools` whitelist is a strong hint to the model, **not a hard runtime sandbox**. For genuine isolation, scope permissions at the session level in `settings.json`.

Distributing a skill to a team is equivalent to distributing a shell script with elevated permissions — same review threshold required. The marketplace model does not vet skills for security.

---

## Bad-Case Journal

**Entry 1: The skill that fires on everything.**
Description: `"Helps improve code quality. Use when: writing, editing, reviewing, or discussing code."` Every message matches at least one verb. The skill's 3,000-token preamble loads on every prompt; subsequent responses are subtly colored by code-quality lens. Fix: anchor triggers to specific phrases users type.

**Entry 2: Two skills, one task, no winner.**
Both `code-review` and `security-review` include "review", "PR", "diff" in triggers. Model picks semi-arbitrarily. Fix: differentiate by primary noun, not action verb. `code-review` triggers on "code quality"; `security-review` triggers on "security, vulnerability, auth, OWASP". Zero overlap.

**Entry 3: The 50k token context bleed.**
A knowledge-base skill embedded its full document corpus directly in SKILL.md as a giant markdown block. 52,000 tokens consumed at session start. Fix: skills are routing instructions, not data dumps. Reference external data via runtime queries.

**Entry 4: `allowed-tools` not enforced.**
Developer set `allowed-tools: [Bash]` for a knowledge-lookup skill. Model used `Read`, `Write`, and git commands anyway. `allowed-tools` is a strong hint to the model, not runtime-enforced. For genuine sandboxing, configure session-level permissions.

---

## Interview Soundbites

**Soundbite 1 — Skill vs MCP tool**
"A skill is a document. When invoked, it loads into the model's context and the model reads it. There's no separate runtime, no function call, no structured input/output schema. An MCP tool is a callable function: model issues a typed invocation, server executes code, model receives structured result. Skills encode workflow judgment. MCP tools encode deterministic operations. A well-designed agent uses both."

**Soundbite 2 — Trigger engineering is harder than the body**
"Writing the workflow is just clear instructions. Trigger engineering is predicting the full space of user intent that should route to your skill, then drawing a boundary that excludes everything adjacent. You're writing a classifier in natural language with no training loop. Most authors spend 20 minutes on the body and 5 minutes on the description. Should be the reverse."

**Soundbite 3 — Trust model**
"Skills run with the full permissions of the Claude Code session. `allowed-tools` is a hint to the model, not a sandbox. Distributing a skill to a team is equivalent to distributing a shell script with elevated permissions — same review threshold required. The marketplace makes installation trivially easy, which makes vetting before installation more important, not less."

---

## References

- Claude Code Skills documentation: https://docs.anthropic.com/en/docs/claude-code/skills
- skills.sh marketplace
- oh-my-claudecode skill collection
- The `write-a-skill` meta-skill (bootstraps skill authoring)

---

## Cross-References

**Builds on: W6 Claude Code Source Dive.** Understanding context loading at session start (W6) explains why the description field is the only thing the model sees before invocation.

**Sets up: W11 System Design.** The skill-as-unit-of-capability pattern scales to service architecture. A skill with `allowed-tools` is a microservice with an API contract.

**Distinguish from: W7 Tool Harness.** Tools are callable functions with JSON schemas. Skills are loaded prompts. A skill can invoke tools; a tool cannot invoke a skill. Most production agents need both layers.
