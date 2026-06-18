# Bad-Case Journal (§5) — read when writing or editing Bad-Case entries

> On-demand authoring reference. Indexed from `CLAUDE.md`. Governs §5 of every chapter AND the global `Bad-Case Journal.md`. Mechanically enforced by `scripts/audit_bcj_measured.py`.

## Section 5 — Bad-Case Journal (REQUIRED — 3–5 entries, exact format)

Each entry uses **exactly** this 3-field format:

```
**Entry N — <one-line symptom>.**
*Symptom:* what the operator observes
*Root cause:* what is actually broken
*Fix:* concrete remediation, with code or config when applicable
```

Entries also belong in the global `Bad-Case Journal.md` cross-cutting library. Other chapters' interview soundbites cite specific entries — do not delete or rewrite entries without checking incoming references.

## MEASURED-ONLY INVARIANT (normative — non-negotiable)

Every Bad-Case Journal entry — in a chapter §5 AND in the global `Bad-Case Journal.md` — MUST be a *real failure actually observed in a lab run*: reproduced, with its symptom / root-cause / fix traceable to a run, an error message, a failing test, or a `RESULTS.md` row. **No predicted, scoped, hypothetical, anticipated, or `(planned)` entries. Ever.** A failure mode you *expect* but have *not yet observed* is not a bad-case entry — it belongs in `ANTI-PATTERNS.md` (the explicit "before you write code" companion), and only *graduates* to the Bad-Case Journal once you measure it. Why this is non-negotiable: the journal's entire value is that it documents what broke **after the fact**; a predicted entry teaches a failure that may never occur and quietly launders speculation as evidence — the exact judgment-atrophy failure the program exists to prevent. **If a chapter is still a spec draft, leave §5 empty** (or park anticipated modes in `ANTI-PATTERNS.md`); do NOT pre-fill §5 with guesses dressed as findings. The one allowed exception is an entry explicitly and visibly labelled as a *deferred/out-of-scope* mode (e.g. multi-host failures in a single-host lab) — but it must say so in-line and must not invent a symptom or a measured number. Mechanically enforced by `scripts/audit_bcj_measured.py` (exit 1 on any unmeasured-looking entry).

## Pre-commit BCJ check

- [ ] §5 Bad-Case Journal — 3–5 entries in exact 3-field format.
- [ ] Every entry is REAL + MEASURED (no predicted / (planned) / hypothetical) — `python3 scripts/audit_bcj_measured.py` exits 0.
- [ ] New entries copied to the global `Bad-Case Journal.md`.
