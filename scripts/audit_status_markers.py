#!/usr/bin/env python3
"""Audit chapter sections for Pattern 19 status markers.

Pattern 19 (Spec → IMPLEMENTED Status Transition Marker — see
Engineering Decision Patterns) requires that every section
describing work-to-be-done carries an explicit lifecycle marker:
  (SPEC)                  — design only, no code yet
  (IMPLEMENTED YYYY-MM-DD) — code shipped, numbers measured
  (STRETCH)               — optional / advanced; may never ship

This script scans Week*.md files for two things:
  (1) Implicit-status markers in section headings: TBD, OUTLINED,
      "FULL TEXT IN ROUND N", placeholder, draft — flags them as
      Pattern 19 violations that should be made explicit.
  (2) Existing explicit markers — inventory of who already
      complies.

USAGE
=====
  python3 scripts/audit_status_markers.py
  python3 scripts/audit_status_markers.py --vault-root /path/to/vault
  python3 scripts/audit_status_markers.py --fix  (rewrite implicit → SPEC)

The --fix flag does a CONSERVATIVE replacement: only modifies
HEADING lines (lines starting with `#`). Code blocks and prose
mentions of "TBD" are left intact intentionally — those describe
deliverables in the lab repo, not chapter status.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


# Implicit-status markers that should be replaced with (SPEC) or similar
IMPLICIT_TRANSFORMS = [
    (re.compile(r"OUTLINED,?\s*FULL TEXT IN ROUND \d+"), "(SPEC)"),
    (re.compile(r"\bOUTLINED\b(?!\))"), "(SPEC)"),
    (re.compile(r"TBD-fill in round \d+"), "(SPEC)"),
    (re.compile(r"TBD code,?\s*scoped now"), "(SPEC — code lands when lab runs)"),
    (re.compile(r"TBD AFTER LAB RUN"), "(SPEC — to be filled after lab run)"),
    (re.compile(r"\(TBD\)"), "(SPEC)"),
    (re.compile(r"\bTBD\b(?!\))"), "(SPEC)"),
]

# Cleanup patterns for double-paren / orphan-close artifacts that arise
# when the source heading already had outer parens.
CLEANUP_TRANSFORMS = [
    (re.compile(r"\(\(SPEC\)\)"), "(SPEC)"),
    (re.compile(r"\(\(SPEC\)-fill\)"), "(SPEC)"),
    (re.compile(r"\(~(\d+) words — REQUIRED — \(SPEC\)"), r"(~\1 words — REQUIRED — SPEC)"),
]

# Heading detection — lines starting with #
HEADING_PATTERN = re.compile(r"^#{1,6} ")

# Explicit-status marker grep patterns (for inventory)
EXPLICIT_STATUS_PATTERN = re.compile(r"\((SPEC|IMPLEMENTED \d{4}-\d{2}-\d{2}|STRETCH)\b[^)]*\)")


def scan_chapter(text: str) -> tuple[list[tuple[int, str, str]], list[tuple[int, str]]]:
    """Return (implicit_violations, explicit_markers).

    implicit_violations: (line_no, original_heading, suggested_replacement)
    explicit_markers: (line_no, heading_with_status)
    """
    implicit: list[tuple[int, str, str]] = []
    explicit: list[tuple[int, str]] = []
    for i, line in enumerate(text.split("\n"), 1):
        if not HEADING_PATTERN.match(line):
            continue
        # Check for implicit (violating) markers
        suggested = line
        for pat, repl in IMPLICIT_TRANSFORMS:
            suggested = pat.sub(repl, suggested)
        if suggested != line:
            implicit.append((i, line.rstrip(), suggested.rstrip()))
        # Check for explicit status (compliant)
        if EXPLICIT_STATUS_PATTERN.search(line):
            explicit.append((i, line.rstrip()))
    return implicit, explicit


def apply_fix(text: str) -> tuple[str, int]:
    """Apply IMPLICIT_TRANSFORMS to heading lines only, then CLEANUP_TRANSFORMS globally.

    Returns (new_text, num_changes).
    """
    changes = 0
    out = []
    for line in text.split("\n"):
        if HEADING_PATTERN.match(line):
            original = line
            for pat, repl in IMPLICIT_TRANSFORMS:
                line = pat.sub(repl, line)
            if line != original:
                changes += 1
        out.append(line)
    new_text = "\n".join(out)
    # Apply cleanup globally (handles double-paren artifacts)
    for pat, repl in CLEANUP_TRANSFORMS:
        new_text = pat.sub(repl, new_text)
    return new_text, changes


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument(
        "--vault-root",
        type=Path,
        default=Path("."),
        help="Vault root containing Week*.md files (default: cwd)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rewrite implicit markers to (SPEC). Modifies files in place.",
    )
    parser.add_argument(
        "--list-explicit",
        action="store_true",
        help="Also show chapters that already have explicit status markers (Pattern 19-compliant).",
    )
    args = parser.parse_args()

    chapters = sorted(args.vault_root.glob("Week*.md"))
    total_violations = 0
    chapters_with_violations = 0

    for f in chapters:
        text = f.read_text()
        implicit, explicit = scan_chapter(text)

        if implicit and not args.fix:
            chapters_with_violations += 1
            total_violations += len(implicit)
            print(f"\n{f.name} — {len(implicit)} implicit-status heading(s):")
            for lineno, original, suggested in implicit:
                print(f"  L{lineno}: {original}")
                print(f"  → {suggested}")

        if args.fix and implicit:
            new_text, n = apply_fix(text)
            f.write_text(new_text)
            chapters_with_violations += 1
            total_violations += n
            print(f"FIXED {f.name}: {n} heading(s) rewritten")

        if args.list_explicit and explicit:
            print(f"\n{f.name} — {len(explicit)} explicit Pattern-19 marker(s):")
            for lineno, line in explicit:
                print(f"  L{lineno}: {line}")

    print()
    print(f"Total chapters with implicit-status headings: {chapters_with_violations}")
    print(f"Total implicit-status heading violations: {total_violations}")
    if args.fix:
        print("(--fix applied; re-run without --fix to verify zero violations remain)")
    return 0 if total_violations == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
