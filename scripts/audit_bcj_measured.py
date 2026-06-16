#!/usr/bin/env python3
"""audit_bcj_measured.py — enforce the §5 MEASURED-ONLY INVARIANT.

Every Bad-Case Journal entry MUST be a real failure observed in a lab run —
not predicted, scoped, hypothetical, or a `(planned)` placeholder. See the
"MEASURED-ONLY INVARIANT" rule in CLAUDE.md §5.

This script flags entries that *read as* unmeasured: it scans the §5 Bad-Case
Journal section of every `Week*.md` chapter plus the global `Bad-Case
Journal.md`, looking for high-precision placeholder/prediction markers
("(planned)", "scoped-not-measured", "to be filled after lab run", TBD, ...).

It is deliberately high-precision, not high-recall: it cannot prove an entry
IS measured (only a human + the lab's RESULTS.md can), but it catches the
common ways an unmeasured entry announces itself. A clean run means "no entry
is *obviously* a guess"; it does not certify every entry as reproduced.

Exit code 0 = clean, 1 = violations found (CI-hook-friendly).
Walks `Week*.md` in the vault root + `Bad-Case Journal.md`.

Usage:
    python3 scripts/audit_bcj_measured.py
    python3 scripts/audit_bcj_measured.py --verbose   # show each flagged line
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

# High-precision markers: phrasings that only appear when an entry is a
# placeholder, a prediction, or scoped-but-not-run. Bare words like
# "predicted" / "hypothesis" / "scoped from" are intentionally EXCLUDED —
# they appear in legitimate theory prose and debugging advice and would
# produce false positives.
# (pattern, label, hard). HARD markers are unambiguous placeholders/promises —
# they are violations regardless of nearby affirming words. SOFT markers are the
# ones that also occur inside affirming disclaimers ("no hypothetical entries"),
# so the AFFIRM guard below may clear them.
MARKERS: list[tuple[str, str, bool]] = [
    (r"\(planned\)", "(planned) placeholder entry", True),
    (r"scoped[\s\-]?not[\s\-]?measured", "scoped-not-measured", True),
    (r"to be filled", "to-be-filled placeholder", True),
    (r"after (the )?lab run", "deferred to 'after lab run'", True),
    (r"not yet measured", "explicitly not yet measured", True),
    (r"will be (filled|populated|written)", "promised-but-absent content", True),
    (r"\bTBD\b", "TBD placeholder", True),
    (r"pre-?flight entr", "pre-flight (predicted) entries", True),
    (r"populated post[\s\-]implementation", "populated-post-implementation note", True),
    (r"final entries populated", "predicted-now / measured-later note", True),
    (r"SPEC\s*[—-]\s*to be filled", "SPEC placeholder", True),
    (r"predicted entr(y|ies)", "self-described predicted entry", False),
    (r"hypothetical entr", "self-described hypothetical entry", False),
]
COMPILED = [(re.compile(p, re.I), label, hard) for p, label, hard in MARKERS]

# Affirmation guard: a line that *asserts* its entries are measured is not a
# violation even if it mentions the word "hypothetical"/"predicted" (e.g. the
# common disclaimer "All entries below are real bugs observed... No hypothetical
# entries."). Without this guard the audit fails on lines that say the right
# thing — worse than a missed flag, because it blocks a compliant commit.
AFFIRM = re.compile(
    r"\b(real bug|real symptom|real failure|observed during|are observed|"
    r"observed (in|during) (this )?lab|no hypothetical|no predicted|"
    r"every entry below is|all entries below are real)\b", re.I)

SECTION_HEADING = re.compile(r"^##\s+.*Bad-?Case Journal", re.I)
NEXT_H2 = re.compile(r"^##\s+")


def bcj_section(text: str) -> tuple[int, str] | None:
    """Return (1-based start line of the §5 body, body text) for a chapter,
    or None if the chapter has no Bad-Case Journal section."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if SECTION_HEADING.match(line):
            start = i
            break
    if start is None:
        return None
    body: list[str] = []
    for j in range(start + 1, len(lines)):
        if NEXT_H2.match(lines[j]):
            break
        body.append(lines[j])
    # +2: 1-based, and body begins on the line after the heading.
    return start + 2, "\n".join(body)


def scan(body: str, base_line: int) -> list[tuple[int, str, str]]:
    """Return [(line_no, marker_label, line_text)] for every flagged line."""
    hits: list[tuple[int, str, str]] = []
    for offset, line in enumerate(body.splitlines()):
        affirmed = bool(AFFIRM.search(line))
        for rx, marker_label, hard in COMPILED:
            if rx.search(line):
                # Soft markers are cleared by an affirming disclaimer; hard
                # placeholders ((planned)/TBD/...) are violations regardless.
                if affirmed and not hard:
                    continue
                hits.append((base_line + offset, marker_label, line.strip()))
                break
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true",
                    help="show each flagged line + the marker that tripped it")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent
    total = 0
    flagged_files = 0

    targets: list[tuple[str, int, str]] = []  # (display_name, base_line, body)

    for chapter in sorted(root.glob("Week*.md")):
        section = bcj_section(chapter.read_text(encoding="utf-8"))
        if section is None:
            continue
        base, body = section
        targets.append((f"{chapter.name} §5", base, body))

    journal = root / "Bad-Case Journal.md"
    if journal.exists():
        targets.append(("Bad-Case Journal.md", 1, journal.read_text(encoding="utf-8")))

    for name, base, body in targets:
        hits = scan(body, base)
        if not hits:
            continue
        flagged_files += 1
        total += len(hits)
        print(f"[FLAG] {name}: {len(hits)} unmeasured-looking line(s)")
        if args.verbose:
            for line_no, marker_label, text in hits:
                snippet = text if len(text) <= 100 else text[:97] + "..."
                print(f"    L{line_no}: [{marker_label}] {snippet}")

    if total == 0:
        print("[OK] Bad-Case Journal measured-only invariant: clean "
              f"({len(targets)} sections scanned, 0 unmeasured-looking entries).")
        return 0
    print(f"\n[FAIL] {total} flagged line(s) across {flagged_files} section(s). "
          "Each must be a REAL measured failure or move to ANTI-PATTERNS.md "
          "(CLAUDE.md §5 MEASURED-ONLY INVARIANT). Run with --verbose for detail.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
