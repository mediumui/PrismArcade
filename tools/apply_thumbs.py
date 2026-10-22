#!/usr/bin/env python3
"""Swap placeholder card thumbs for real generated images (thumbs/<slug>.jpg).

Handles every <article class="card game-card">...</article> block on:
  * index.html and games.html   -> thumbs/<slug>.jpg
  * games/<page>.html (related) -> ../thumbs/<slug>.jpg

The game slug comes from the card's Play link. Cards that are not a single
game (e.g. "All Games" -> ../index.html#games) fall back to the generic
_all-games.jpg catalog image.

Idempotent: blocks already containing thumbs/<slug>.jpg are skipped.

Usage: python tools/apply_thumbs.py
"""

from __future__ import annotations

import html as htmllib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THUMB_DIR = ROOT / "thumbs"
PAGES = ([ROOT / "index.html", ROOT / "games.html", ROOT / "404.html"]
         + sorted((ROOT / "games").glob("*.html")))

BLOCK = re.compile(r'<article class="card game-card".*?</article>', re.S)
THUMB = re.compile(r'<div class="thumb">.*?</div>', re.S)
# game links: absolute (/games/x.html), parent (../games/x.html) or bare (x.html)
HREF = re.compile(r'href="(?:/|\.\./)?(?:games/)?([a-z0-9-]+)\.html"')
H3 = re.compile(r"<h3>(.*?)</h3>", re.S)
FALLBACK = "_all-games"
# 404.html is served at arbitrary URLs, so it needs root-absolute asset paths
ROOT_ABS_PAGES = {"404.html"}


def fix_page(p: Path) -> int:
    if p.name in ROOT_ABS_PAGES:
        prefix = "/"
    elif p.parent.name == "games":
        prefix = "../"
    else:
        prefix = ""
    text = p.read_text(encoding="utf-8")
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        block = m.group(0)
        if "thumbs/" in block:
            return block
        href = HREF.search(block)
        slug = href.group(1) if href else FALLBACK
        if slug == "index":  # e.g. ../index.html#games
            slug = FALLBACK
        if not (THUMB_DIR / f"{slug}.jpg").exists():
            return block
        name_m = H3.search(block)
        raw = htmllib.unescape(name_m.group(1)).strip() if name_m else slug.replace("-", " ")
        alt = htmllib.escape(f"{raw} game preview", quote=True)
        new_block, n = THUMB.subn(
            f'<div class="thumb"><img src="{prefix}thumbs/{slug}.jpg" alt="{alt}" '
            f'width="640" height="360" loading="lazy" decoding="async"></div>',
            block, count=1,
        )
        if n:
            count += 1
        return new_block

    text = BLOCK.sub(repl, text)
    p.write_text(text, encoding="utf-8")
    return count


def main() -> None:
    total = 0
    for p in PAGES:
        n = fix_page(p)
        total += n
        print(f"{p.relative_to(ROOT)}: {n} thumbs swapped")
    print(f"\ntotal: {total}")


if __name__ == "__main__":
    main()
