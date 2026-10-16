#!/usr/bin/env python3
"""Batch-rename the public brand 'Flappy Bird' -> 'Sky Flap' across user-facing pages.

Only the brand string is replaced. The file name (flappy.html), the canvas id
(#flappy / .flappy-wrap), and the localStorage key (flappyBest) are deliberately
left untouched so links, CSS, and the game logic keep working.
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def process_file(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new, n = re.subn(r"Flappy Bird", "Sky Flap", text)
    if n:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    return n


# Root pages: index.html, about.html, 404.html
for fn in ("index.html", "about.html", "404.html"):
    n = process_file(os.path.join(BASE, fn))
    print(f"{fn}: {n}")

# All games/*.html (includes the related-card blocks AND flappy.html itself)
games_dir = os.path.join(BASE, "games")
total = 0
for fn in sorted(os.listdir(games_dir)):
    if not fn.endswith(".html"):
        continue
    n = process_file(os.path.join(games_dir, fn))
    if n:
        print(f"games/{fn}: {n}")
        total += n
print(f"games dir total: {total}")
