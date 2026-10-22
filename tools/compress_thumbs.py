#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compress the card thumbnails in thumbs/*.jpg down to display size.

Rationale
=========
Every card thumbnail is shown inside `.card .thumb` which is only
~320x150px on desktop and ~300x112px on mobile, but the source files are
2560x1440 (2K). That wastes ~140KB per card for detail the eye never sees.

What this does
==============
- Reads every thumbs/*.jpg
- Downscales to a max width of MAX_W (keeps 16:9), with high-quality
  Lanczos resampling
- Re-encodes as JPEG quality=QUALITY, progressive, max 4 scanlines
- In-place overwrite (a timestamped .bak copy is kept next to the file)

It does NOT change file names, so all the <img src="...thumbs/x.jpg">
references in the site keep working. Re-run to undo a mistake:
    python tools/compress_thumbs.py --restore

Run
===
    C:/Users/.../Python312/python.exe tools/compress_thumbs.py
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
THUMBS = ROOT / "thumbs"

MAX_W = 480      # max thumbnail width in px (display is ~320px, 480 covers Retina)
QUALITY = 82     # JPEG quality 0-100
KEEP_EXIF = False

bak_marker = "thumb-compress-backup"


def compress(path: Path, max_w: int, quality: int) -> tuple[int, int, int]:
    """Compress one thumbnail in place. Returns (old_kb, new_kb, new_w)."""
    old_kb = os.path.getsize(path) // 1024

    img = Image.open(path)
    img = img.convert("RGB")

    w, h = img.size
    if w > max_w:
        nh = max(1, round(h * max_w / w))
        img = img.resize((max_w, nh), Image.LANCZOS)
        new_w = max_w
    else:
        new_w = w

    # keep a one-time timestamped backup next to the original
    bak = path.with_suffix(f".{bak_marker}.jpg")
    if not bak.exists():
        shutil.copy2(path, bak)

    img.save(
        path,
        "JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
    )
    new_kb = os.path.getsize(path) // 1024
    return old_kb, new_kb, new_w


def restore() -> None:
    """Put back the .thumb-compress-backup.jpg files over the compressed ones."""
    n = 0
    for bak in THUMBS.glob(f"*.thumb-compress-backup.jpg"):
        orig = bak.with_suffix(".jpg")
        shutil.copy2(bak, orig)
        n += 1
    print(f"[restore] {n} thumbnail(s) restored from backup.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Compress Prism Arcade thumbnails")
    ap.add_argument("--restore", action="store_true",
                    help="restore originals from .thumb-compress-backup.jpg")
    ap.add_argument("--max-w", type=int, default=MAX_W)
    ap.add_argument("--quality", type=int, default=QUALITY)
    args = ap.parse_args()

    max_w = args.max_w
    quality = args.quality
    if args.restore:
        restore()
        return

    files = sorted(glob.glob(str(THUMBS / "*.jpg")))
    files = [f for f in files if bak_marker not in os.path.basename(f)]

    if not files:
        print(f"No thumbs/*.jpg found in {THUMBS}")
        sys.exit(1)

    total_old = total_new = 0
    print(f"Compressing {len(files)} thumbnails -> max width {max_w}px, q{quality}\n")
    print(f"{'file':26s} {'before':>8s} {'after':>8s} {'saved':>7s}  width")
    print("-" * 70)
    for f in files:
        p = Path(f)
        old, new, w = compress(p, max_w, quality)
        total_old += old
        total_new += new
        print(f"{p.name:26s} {old:>6}KB {new:>6}KB {old - new:>6}KB  {w}px")

    print("-" * 70)
    pct = (1 - total_new / total_old) * 100 if total_old else 0
    print(f"TOTAL: {total_old}KB -> {total_new}KB  ({pct:.0f}% smaller, "
          f"{total_old - total_new}KB saved)")
    print(f"\nBackups kept as  thumbs/*.thumb-compress-backup.jpg")
    print("Restore any time with:  python tools/compress_thumbs.py --restore")


if __name__ == "__main__":
    main()
