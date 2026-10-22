#!/usr/bin/env python3
"""One-off cleanup: strip fabricated aggregateRating blocks from JSON-LD.

Background (2026-10-21 SEO audit):
    `seo_clean_games.py` used to inject `aggregateRating` (ratingValue +
    reviewCount) into every game page's `Game` JSON-LD using a hardcoded table
    of "plausible" values. Prism Arcade has no user rating or review feature, so
    those numbers described reviews that do not exist. That is a structured-data
    policy violation and risks a site-wide manual action against rich results.

This script removes `aggregateRating` from every JSON-LD block on every HTML
page in the site. It is idempotent - pages without ratings are left untouched.

Usage:
    python tools/remove_fake_ratings.py          # apply
    python tools/remove_fake_ratings.py --dry    # report only
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LD_PATTERN = re.compile(
    r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S
)


def strip_ratings(obj):
    """Recursively drop aggregateRating / review / rating keys. Returns count."""
    removed = 0
    if isinstance(obj, dict):
        for bad in ("aggregateRating", "review", "reviews", "reviewCount", "ratingValue"):
            if bad in obj:
                del obj[bad]
                removed += 1
        for v in list(obj.values()):
            removed += strip_ratings(v)
    elif isinstance(obj, list):
        for item in obj:
            removed += strip_ratings(item)
    return removed


def process(path: Path, dry: bool) -> int:
    text = path.read_text(encoding="utf-8")
    total = 0
    out = text
    offset = 0

    for m in LD_PATTERN.finditer(text):
        raw = m.group(2).strip()
        if "aggregateRating" not in raw and "ratingValue" not in raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        removed = strip_ratings(data)
        if not removed:
            continue
        total += removed
        new_block = m.group(1) + "\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n" + m.group(3)
        start, end = m.start() + offset, m.end() + offset
        out = out[:start] + new_block + out[end:]
        offset += len(new_block) - (m.end() - m.start())

    if total and not dry:
        path.write_text(out, encoding="utf-8")
    return total


def main() -> None:
    dry = "--dry" in sys.argv
    pages = sorted(
        p for p in ROOT.rglob("*.html")
        if "out" not in p.parts and "node_modules" not in p.parts
    )
    changed = 0
    for p in pages:
        n = process(p, dry)
        if n:
            changed += 1
            rel = p.relative_to(ROOT)
            print(f"{'[dry] ' if dry else ''}{rel}: removed {n} rating key(s)")
    verb = "would clean" if dry else "cleaned"
    print(f"\n{verb} {changed}/{len(pages)} page(s).")


if __name__ == "__main__":
    main()
