#!/usr/bin/env python3
"""Replace the nav brand-mark letter 'P' with the inline prism glyph SVG."""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OLD = '<span class="brand-mark">P</span>'

GLYPH = (
    '<span class="brand-mark">'
    '<svg viewBox="0 0 256 256" width="20" height="20" aria-hidden="true" focusable="false">'
    '<defs><linearGradient id="bmg" x1="0.2" y1="1" x2="0.8" y2="0">'
    '<stop offset="0" stop-color="#ff5f6d"/><stop offset="0.18" stop-color="#ffb347"/>'
    '<stop offset="0.36" stop-color="#ffd24d"/><stop offset="0.55" stop-color="#36d399"/>'
    '<stop offset="0.74" stop-color="#4aa3ff"/><stop offset="1" stop-color="#7c5cff"/>'
    '</linearGradient></defs>'
    '<path d="M128 64 L52 188 L204 188 Z" fill="url(#bmg)" stroke="#ffffff" '
    'stroke-opacity="0.92" stroke-width="12" stroke-linejoin="round"/>'
    '<path d="M188 58 L190.4 66.6 L199 69 L190.4 71.4 L188 80 L185.6 71.4 L177 69 L185.6 66.6 Z" fill="#ffffff"/>'
    '</svg></span>'
)

files = [BASE / n for n in ("index.html", "about.html", "404.html")] + sorted((BASE / "games").glob("*.html"))
done = 0
for f in files:
    t = f.read_text(encoding="utf-8")
    if OLD in t:
        t = t.replace(OLD, GLYPH)
        f.write_text(t, encoding="utf-8")
        done += 1
    elif 'class="brand-mark"' not in t:
        print("WARN no brand-mark:", f.name)
print("replaced in", done, "pages")
