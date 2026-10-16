#!/usr/bin/env python3
"""Insert favicon <link> tags into all Prism Arcade HTML pages, after the viewport meta.

Root pages (index/about/404) reference icons/... ; game pages reference ../icons/...
Idempotent: skips pages that already have a rel="icon" link.
"""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT_PAGES = ["index.html", "about.html", "404.html"]
GAME_DIR = BASE / "games"


def links(prefix: str) -> str:
    return (
        f'    <link rel="icon" href="{prefix}icons/favicon.svg" type="image/svg+xml" />\n'
        f'    <link rel="icon" href="{prefix}icons/favicon-32.png" sizes="32x32" type="image/png" />\n'
        f'    <link rel="icon" href="{prefix}icons/favicon-64.png" sizes="64x64" type="image/png" />\n'
        f'    <link rel="apple-touch-icon" sizes="180x180" href="{prefix}icons/apple-touch-icon.png" />\n'
        f'    <link rel="mask-icon" href="{prefix}icons/favicon.svg" color="#7c5cff" />'
    )


def process(path: Path, prefix: str):
    text = path.read_text(encoding="utf-8")
    if 'rel="icon"' in text:
        print(f"skip (already has icon) {path.name}")
        return
    m = re.search(r'<meta name="viewport"[^>]*>\n', text)
    if not m:
        raise RuntimeError(f"viewport meta not found in {path.name}")
    ins = m.end()
    text = text[:ins] + "\n" + links(prefix) + text[ins:]
    path.write_text(text, encoding="utf-8")
    print(f"updated {path.name}")


def main():
    for name in ROOT_PAGES:
        process(BASE / name, "")
    for f in sorted(GAME_DIR.glob("*.html")):
        process(f, "../")


if __name__ == "__main__":
    main()
