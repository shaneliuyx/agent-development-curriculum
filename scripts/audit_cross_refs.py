#!/usr/bin/env python3
"""Audit chapter cross-references for the Pattern 21 invariant.

Pattern 21 (Bidirectional Cross-Reference Invariant — see
Engineering Decision Patterns) requires that every chapter A's
"Builds on: B" / "Connects to: B" / "Distinguish from: B" /
"Foreshadows: B" reference has a reciprocal mention on chapter B.

This script scans all `Week*.md` files in the vault, builds the
directed-edge graph from cross-reference sections, and prints any
edges (A, B) where B never mentions A back.

USAGE
=====
  cd 'Agent Development Curriculum/'
  python3 scripts/audit_cross_refs.py

  # Or from anywhere:
  python3 path/to/scripts/audit_cross_refs.py --vault-root path/to/curriculum

OUTPUT
======
- Total directed edges across the vault
- Missing-reverse count (Pattern 21 violations)
- Coverage percentage
- Per-target breakdown of which chapters cite it without reciprocal

RECOGNIZED EDGE FORMATS
=======================
The audit captures cross-ref edges in two shapes:
  (a) Label-line: `**Builds on:** [[Week 4 - ReAct From Scratch]] ...`
      — chapter IDs extracted from the rest of the line via regex.
  (b) Sub-bullet under "Cited by:" / "Builds on:" etc.:
      `  - **W6.5**: <context>` — multi-line aware.

If a future format uses some other structure (e.g. YAML
frontmatter `connects_to: [W4]`), extend the regex set.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


LABEL_PATTERN = re.compile(
    r"(?:\*\*)?(Builds on|Connects to|Distinguish from|Foreshadows|Consumed by|Cited by)(?:\*\*)?:\s*(.+)",
    re.IGNORECASE,
)
SUB_BULLET_PATTERN = re.compile(
    r"^\s+-\s+\*\*(W\d+(?:\.\d+(?:\.\d+)?)?)\*\*",
    re.MULTILINE,
)
CHAPTER_ID_PATTERN = re.compile(r"W(\d+(?:\.\d+(?:\.\d+)?)?)")
CHAPTER_FILE_PATTERN = re.compile(r"Week (\d+(?:\.\d+(?:\.\d+)?)?)\b")


def chapter_id_from_filename(filename: str) -> str | None:
    m = CHAPTER_FILE_PATTERN.match(filename)
    return f"W{m.group(1)}" if m else None


def collect_edges(vault_root: Path) -> tuple[set[tuple[str, str]], dict[str, str]]:
    """Walk all Week*.md files; return (edges, id_to_file).

    edges is a set of (source_chapter_id, target_chapter_id) pairs.
    id_to_file maps chapter IDs to their source filenames.
    """
    chapters = sorted(vault_root.glob("Week*.md"))
    id_to_file = {
        cid: f.name
        for f in chapters
        if (cid := chapter_id_from_filename(f.name))
    }
    edges: set[tuple[str, str]] = set()
    for f in chapters:
        src = chapter_id_from_filename(f.name)
        if not src:
            continue
        text = f.read_text()
        if "Cross-Ref" not in text:
            continue
        # Scan only the portion after the first Cross-Ref mention
        after = text.split("Cross-Ref", 1)[1]
        # Label-line edges
        for match in LABEL_PATTERN.finditer(after):
            line_rest = match.group(2)
            for cm in CHAPTER_ID_PATTERN.finditer(line_rest):
                tgt = f"W{cm.group(1)}"
                if tgt != src:
                    edges.add((src, tgt))
        # Sub-bullet edges (e.g. "  - **W6.5**: <context>" lines)
        for sm in SUB_BULLET_PATTERN.finditer(after):
            tgt = sm.group(1)
            if tgt != src:
                edges.add((src, tgt))
    return edges, id_to_file


def find_violations(
    edges: set[tuple[str, str]],
    id_to_file: dict[str, str],
) -> set[tuple[str, str]]:
    """Return edges (src, tgt) where (tgt, src) is not in the graph."""
    return {
        (s, t)
        for s, t in edges
        if (t, s) not in edges and t in id_to_file
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument(
        "--vault-root",
        type=Path,
        default=Path("."),
        help="Vault root containing Week*.md files (default: cwd)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show every missing reverse edge",
    )
    args = parser.parse_args()

    edges, id_to_file = collect_edges(args.vault_root)
    missing = find_violations(edges, id_to_file)

    total = len(edges)
    covered = total - len(missing)
    coverage_pct = 100.0 * covered / total if total else 0.0

    print(f"Total directed cross-ref edges: {total}")
    print(f"Missing-reverse pairs: {len(missing)}")
    print(f"Bidirectional coverage: {coverage_pct:.1f}%")

    if missing:
        target_counts = Counter(t for _, t in missing)
        print(f"\nTop targets needing reciprocal links:")
        for tgt, count in target_counts.most_common(15):
            file = id_to_file.get(tgt, "?")
            incoming = sorted({s for s, t in missing if t == tgt})
            print(f"  {tgt}: {count} incoming need reverse  ({file})")
            if args.verbose:
                print(f"    citing chapters: {incoming}")

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
