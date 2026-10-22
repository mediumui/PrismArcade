#!/usr/bin/env python3
"""Tag each game page's playable surface with `data-board`.

Why: the screenshot tool (tools/capture_thumbs.mjs) and any future tooling need
one stable way to find "the thing you actually play". Game boards currently use
inconsistent ids (#grid, #board, #tubes, #zone, #pads, #pool, #word, #options)
or are plain <canvas>. Renaming ids would break every `getElementById()` call
and matching CSS rule, so instead we add a single attribute and leave ids alone.

Idempotent: pages already carrying data-board are skipped.

Usage:
    python tools/tag_board.py --dry   # report only
    python tools/tag_board.py         # apply
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "games"

# ordered candidates — first match wins
CANDIDATES = [
    r"<canvas\b",                              # canvas games
    r"<div\b[^>]*\bid=\"board\"",              # connect4, sudoku
    r"<div\b[^>]*\bid=\"grid\"",               # 2048, memory, quick-tap, ...
    r"<div\b[^>]*\bid=\"tubes\"",              # color-sort
    r"<div\b[^>]*\bid=\"zone\"",               # reaction-test
    r"<div\b[^>]*\bid=\"pads\"",               # reflex-relay
    r"<div\b[^>]*\bid=\"pool\"",               # word-merge
    r"<div\b[^>]*\bid=\"word\"",               # hangman
    r"<div\b[^>]*\bid=\"options\"",            # quiz
    r"<div\b[^>]*\bclass=\"[^\"]*\bboard-grid\b",  # sliding-number, tic-tac-toe
]


def tag_once(html: str) -> tuple[str, str] | None:
    if "data-board" in html:
        return None
    for pattern in CANDIDATES:
        m = re.search(pattern, html)
        if not m:
            continue
        end = html.find(">", m.start())
        if end == -1:
            continue
        return html[:end] + " data-board" + html[end:], pattern
    return None


def main() -> None:
    dry = "--dry" in sys.argv
    tagged = skipped = failed = 0

    for p in sorted(GAMES.glob("*.html")):
        if p.name.startswith("_"):
            continue
        html = p.read_text(encoding="utf-8")
        res = tag_once(html)
        if res is None:
            if "data-board" in html:
                skipped += 1
                print(f"{p.name}: already tagged")
            else:
                failed += 1
                print(f"{p.name}: !! no candidate surface found")
            continue
        new_html, pattern = res
        if not dry:
            p.write_text(new_html, encoding="utf-8")
        tagged += 1
        print(f"{p.name}: tagged via {pattern}")

    print(f"\ntagged={tagged} already={skipped} failed={failed}")


if __name__ == "__main__":
    main()
