#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inject resource hints (preconnect / dns-prefetch) into every page <head>.

The audit found 31/31 pages loading googletagmanager.com, pagead2.googlesyndication.com
and static.cloudflareinsights.com with no connection warm-up at all. The hints are
placed before the AdSense / gtag scripts so the DNS+TLS handshake overlaps with
HTML parsing.

Idempotent: pages that already carry the hint are skipped.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APPLY = "--apply" in sys.argv

HINTS = (
    '    <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin />\n'
    '    <link rel="preconnect" href="https://pagead2.googlesyndication.com" crossorigin />\n'
    '    <link rel="dns-prefetch" href="https://static.cloudflareinsights.com" />\n'
)

changed, skipped = [], []
for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in {".git", "tools", "node_modules", ".workbuddy"}]
    for f in sorted(files):
        if not f.endswith(".html") or f == "googlec618091bcb9edff2.html":
            continue
        p = os.path.join(dirpath, f)
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        src = open(p, encoding="utf-8", newline="").read()
        if "googletagmanager.com" in src and 'rel="preconnect"' in src:
            skipped.append(rel)
            continue

        m = re.search(r"^([ \t]*)<meta\s+name=[\"']viewport[\"'][^>]*>\s*$", src, re.M | re.I)
        if not m:
            # fall back: insert right before the first <script> or <link rel="stylesheet">
            m2 = re.search(r"^([ \t]*)<(script|link)[ \t]", src, re.M | re.I)
            if not m2:
                skipped.append(rel + " (no anchor)")
                continue
            anchor, indent = m2.start(), m2.group(1)
        else:
            anchor, indent = m.end() + 1, m.group(1)

        block = "\n".join(indent + line.strip() for line in HINTS.strip().split("\n")) + "\n"
        new = src[:anchor] + block + src[anchor:]
        if APPLY:
            open(p, "w", encoding="utf-8", newline="").write(new)
        changed.append(rel)

print("mode:", "APPLY" if APPLY else "DRY RUN")
print("pages updated:", len(changed), "| skipped:", len(skipped))
for s in skipped:
    print("   skip:", s)
if not APPLY:
    print("re-run with --apply to write")
