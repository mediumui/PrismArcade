#!/usr/bin/env python3
"""Regenerate sitemap.xml with real <lastmod> values.

Why lastmod matters: without it Google has to guess whether a page changed,
which slows re-crawling of updated game pages. A truthful lastmod (taken from
git commit date, falling back to file mtime) improves crawl scheduling.

Usage:
    python tools/gen_sitemap.py
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://www.prismarcade.top"

# path -> (priority, changefreq); games are appended automatically
ROOT_PAGES = [
    ("index.html", "1.0", "weekly"),
    ("games.html", "0.9", "weekly"),
    ("about.html", "0.6", "monthly"),
    ("contact.html", "0.6", "monthly"),
    ("privacy.html", "0.6", "monthly"),
]


def git_date(rel: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", rel],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )
        stamp = out.stdout.strip()
        if stamp:
            return stamp
    except Exception:
        pass
    return None


def lastmod(rel: str) -> str:
    stamp = git_date(rel)
    if not stamp:
        ts = (ROOT / rel).stat().st_mtime
        stamp = datetime.fromtimestamp(ts, timezone.utc).isoformat()
    # normalise to YYYY-MM-DD (W3C datetime is accepted; date-only is safest)
    return stamp[:10]


def url_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return f"{SITE}/"
    return f"{SITE}/{rel}"


def main() -> None:
    entries = []
    for rel, prio, freq in ROOT_PAGES:
        p = ROOT / rel
        if p.exists():
            entries.append((url_for(p), prio, freq, lastmod(rel)))

    for p in sorted((ROOT / "games").glob("*.html")):
        if p.name.startswith("_"):
            continue
        rel = p.relative_to(ROOT).as_posix()
        entries.append((url_for(p), "0.8", "monthly", lastmod(rel)))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url, prio, freq, mod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{mod}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{prio}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    out = ROOT / "sitemap.xml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} — {len(entries)} URLs")
    for e in entries[:6]:
        print("  ", e)


if __name__ == "__main__":
    main()
