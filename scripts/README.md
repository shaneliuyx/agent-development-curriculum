# Curriculum Audit Scripts

Mechanical audits that enforce the invariants codified in [[Engineering Decision Patterns]]. Run these any time the chapter set changes substantially.

## Available audits

| Script | Pattern enforced | What it checks |
|---|---|---|
| `audit_cross_refs.py` | Pattern 21 — Bidirectional Cross-Reference Invariant | Every "Builds on: B" / "Connects to: B" / "Distinguish from: B" / "Foreshadows: B" / "Cited by: B" on chapter A has a reciprocal mention on chapter B |
| `audit_status_markers.py` | Pattern 19 — Spec → IMPLEMENTED Status Transition Marker | Section headings with implicit-state markers (TBD / OUTLINED / "FULL TEXT IN ROUND N") are flagged for conversion to explicit `(SPEC)` / `(IMPLEMENTED YYYY-MM-DD)` / `(STRETCH)` |

## Usage

```bash
# Run from vault root
cd 'Agent Development Curriculum/'

# Cross-reference audit (Pattern 21)
python3 scripts/audit_cross_refs.py
python3 scripts/audit_cross_refs.py --verbose   # show every missing edge

# Status-marker audit (Pattern 19)
python3 scripts/audit_status_markers.py
python3 scripts/audit_status_markers.py --list-explicit  # also show compliant headings
python3 scripts/audit_status_markers.py --fix            # rewrite implicit → (SPEC)
```

Exit codes: `0` on clean (no violations); `1` on violations found. Useful for CI hooks.

## Adding a new audit

The two existing scripts share a shape:

1. Walk `Week*.md` files in the vault root.
2. Parse a specific invariant (regex or text-based).
3. Report violations grouped by source / target / type.
4. Optionally apply `--fix` (rewrite in place; conservative — heading lines only).

When codifying a new pattern in [[Engineering Decision Patterns]], if the invariant is mechanically checkable, add a script here. Anything taste-based (Pattern 6 ★ Insight Callouts, Pattern 8 Trade-off Transparency) stays human-review-only.

## History

Both scripts were extracted from inline `python3 <<PY` blocks used during the Pattern 19 + Pattern 21 audit-and-backfill commits on 2026-05-19 (`a700157`, `39168c7`, `9a41b56`, `322a4dc`). The inline shell approach got us from 39% bidirectional coverage to 100% in 4 commits across 28 chapters — moving the logic to permanent scripts means future audits don't have to re-derive the regex.
