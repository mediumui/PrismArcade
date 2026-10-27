#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert thumbs/*.jpg to WebP and repoint every reference to the .webp file.

The .jpg originals are kept on disk as a rollback path (nothing loads them once
the HTML points at .webp). og/ images are deliberately left as JPEG because
social crawlers prefer jpg/png.

Lighthouse modern-image-formats flagged thumbs/minesweeper.jpg (28 KB -> ~38 KB
saving on desktop); converting the whole set cuts the catalog page's image
payload substantially on mobile connections.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
THUMBS = os.path.join(ROOT, "thumbs")
APPLY = "--apply" in sys.argv

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

converted = []
total_before = total_after = 0
for f in sorted(os.listdir(THUMBS)):
    if not f.lower().endswith(".jpg"):
        continue
    src = os.path.join(THUMBS, f)
    dst = os.path.join(THUMBS, f[:-4] + ".webp")
    before = os.path.getsize(src)
    im = Image.open(src).convert("RGB")
    if APPLY:
        im.save(dst, "WEBP", quality=82, method=6)
    after = os.path.getsize(dst) if os.path.exists(dst) else 0
    if not APPLY:
        # estimate size without writing
        import io
        b = io.BytesIO()
        im.save(b, "WEBP", quality=82, method=6)
        after = len(b.getvalue())
    total_before += before
    total_after += after
    converted.append((f, f[:-4] + ".webp", before, after))

print("%s  %d images  %.0f KB -> %.0f KB  (-%.0f%%)" % (
    "APPLIED" if APPLY else "DRY RUN", len(converted),
    total_before / 1024, total_after / 1024,
    100 * (1 - total_after / total_before) if total_before else 0))
for a, b, x, y in converted[:6]:
    print("   %-24s -> %-24s  %6.1f KB -> %5.1f KB" % (a, b, x / 1024, y / 1024))

refs = 0
pages = 0
for dp, d, fs in os.walk(ROOT):
    d[:] = [x for x in d if x not in {".git", "tools", "node_modules", ".workbuddy", "og"}]
    for f in sorted(fs):
        if not f.endswith((".html", ".txt", ".xml")):
            continue
        p = os.path.join(dp, f)
        s = open(p, encoding="utf-8", newline="").read()
        new = re.sub(r"(thumbs/[A-Za-z0-9_\-]+)\.jpg", r"\1.webp", s)
        if new != s:
            refs += len(re.findall(r"thumbs/[A-Za-z0-9_\-]+\.jpg", s))
            pages += 1
            if APPLY:
                open(p, "w", encoding="utf-8", newline="").write(new)
print("\nrepointed %d references across %d files" % (refs, pages))
if not APPLY:
    print("re-run with --apply to write")
