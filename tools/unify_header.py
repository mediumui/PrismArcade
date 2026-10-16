#!/usr/bin/env python3
"""Normalize the <header> nav block across all site pages so the top bar is
identical everywhere (Home / Games / Featured + a Start Playing CTA), with the
correct relative paths for root pages vs. the games/ subfolder."""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

GLYPH = (
    '<span class="brand-mark"><svg viewBox="0 0 256 256" width="20" height="20" '
    'aria-hidden="true" focusable="false"><defs><linearGradient id="bmg" x1="0.2" y1="1" x2="0.8" y2="0">'
    '<stop offset="0" stop-color="#ff5f6d"/><stop offset="0.18" stop-color="#ffb347"/>'
    '<stop offset="0.36" stop-color="#ffd24d"/><stop offset="0.55" stop-color="#36d399"/>'
    '<stop offset="0.74" stop-color="#4aa3ff"/><stop offset="1" stop-color="#7c5cff"/>'
    '</linearGradient></defs>'
    '<path d="M128 64 L52 188 L204 188 Z" fill="url(#bmg)" stroke="#ffffff" '
    'stroke-opacity="0.92" stroke-width="12" stroke-linejoin="round"/>'
    '<path d="M188 58 L190.4 66.6 L199 69 L190.4 71.4 L188 80 L185.6 71.4 L177 69 L185.6 66.6 Z" fill="#ffffff"/></svg></span>'
)

HEADER_RE = re.compile(r"<header[^>]*>.*?</header>", re.DOTALL)


def build_header(ind, home, games, featured):
    cta = games  # Start Playing -> games catalog
    return (
        f'{ind}<header class="site-header">\n'
        f'{ind}  <div class="container nav">\n'
        f'{ind}    <a class="brand" href="{home}" aria-label="Prism Arcade home">\n'
        f'{ind}      {GLYPH}\n'
        f'{ind}      <span>Prism Arcade</span>\n'
        f'{ind}    </a>\n'
        f'{ind}    <nav class="nav-links" aria-label="Primary">\n'
        f'{ind}      <a href="{home}">Home</a>\n'
        f'{ind}      <a href="{games}">Games</a>\n'
        f'{ind}      <a href="{featured}">Featured</a>\n'
        f'{ind}    </nav>\n'
        f'{ind}    <a class="btn btn-primary" href="{cta}">Start Playing</a>\n'
        f'{ind}  </div>\n'
        f'{ind}</header>'
    )


files = [BASE / n for n in ("index.html", "about.html", "404.html")] + sorted((BASE / "games").glob("*.html"))
done = 0
for f in files:
    t = f.read_text(encoding="utf-8")
    m = HEADER_RE.search(t)
    if not m:
        print("NO HEADER:", f.name)
        continue
    line0 = t[m.start(): t.find("\n", m.start())]
    ind = line0[: len(line0) - len(line0.lstrip(" "))]
    if f.parent.name == "games":
        block = build_header(ind, "../index.html", "../index.html#games", "../index.html#featured")
    else:
        block = build_header(ind, "index.html", "index.html#games", "index.html#featured")
    t = t[: m.start()] + block + t[m.end():]
    f.write_text(t, encoding="utf-8")
    done += 1
print("normalized", done, "headers")
