#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Switch every internal URL to the extensionless (clean) form that Cloudflare
Workers Assets actually serves.

Why: with the platform default html_handling, /games/snake.html answers 307 and
redirects to /games/snake. Canonical, sitemap, og:url, JSON-LD and internal links
all pointed at the .html form, so every hop paid a redirect and the canonical
disagreed with the URL that finally rendered.

Usage:
    python tools/clean_urls.py --apply     # rewrite files
    python tools/clean_urls.py             # dry run, print a summary
"""
import os, re, sys, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = "https://www.prismarcade.top"
APPLY = "--apply" in sys.argv

HTML_FILES = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in {".git", "tools", "node_modules", ".workbuddy"}]
    for f in filenames:
        if f.endswith(".html") or f.endswith(".xml") or f == "llms.txt":
            HTML_FILES.append(os.path.join(dirpath, f))
HTML_FILES.sort()

PAGES = {"index.html", "games.html", "about.html", "contact.html", "privacy.html", "404.html"}
GAME_DIR = os.path.join(ROOT, "games")

stats = collections.Counter()
examples = []


def note(kind):
    stats[kind] += 1


def clean_abs(url):
    """https://www.prismarcade.top/foo.html -> https://www.prismarcade.top/foo"""
    m = re.match(r"^(https?://[^\s\"'<>]+?)\.html([#?][^\s\"'<>]*)?$", url)
    if not m:
        return url
    base, suffix = m.group(1), m.group(2) or ""
    base = re.sub(r"/index$", "/", base)      # /index.html -> /
    return base + suffix


def clean_rel(href):
    """Relative .html href -> extensionless."""
    if href.endswith(".html"):
        base = href[:-5]
    else:
        m = re.match(r"^([^#?]*)\.html([#?].*)$", href)
        if not m:
            return href
        base, suffix = m.group(1), m.group(2)
        if base in ("index", "./index", "../index", ".././index"):
            return ("../" if base.startswith("..") else "./") + suffix
        return base + suffix
    # plain foo.html
    if base in ("index", "./index", "../index"):
        return "../" if base.startswith("..") else "./"
    if base == "":
        return "./"
    return base


def process(path):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    src = open(path, encoding="utf-8", newline="").read()
    orig = src

    # 1) absolute https://www.prismarcade.top/....html
    def sub_abs(m):
        old = m.group(0)
        new = clean_abs(old)
        if new != old:
            note("abs")
            return new
        return old
    src = re.sub(r"https?://[^\s\"'<>]*?\.html(?:[#?][^\s\"'<>]*)?", sub_abs, src)

    # 2) href / src / url attributes that end in .html
    src = re.sub(r"(?:href|src|url)=([\"'])([^\"']*\.html(?:#[^\"']*)?)\1",
                 lambda m: (m.group(0).split("=")[0] + "=" + m.group(1)
                            + clean_rel(m.group(2)) + m.group(1)), src)
    src = re.sub(r"(\"url\"\s*:\s*\")([^\"]*\.html)",
                 lambda m: m.group(1) + clean_abs(m.group(2)), src)

    # 3) sitemap <loc>
    src = re.sub(r"(<loc>)([^<]*\.html)(</loc>)",
                 lambda m: m.group(1) + clean_abs(m.group(2)) + m.group(3), src)

    if src != orig and APPLY:
        open(path, "w", encoding="utf-8", newline="").write(src)
    return src != orig


changed = []
for p in HTML_FILES:
    if process(p):
        changed.append(os.path.relpath(p, ROOT).replace("\\", "/"))

print("mode:", "APPLY" if APPLY else "DRY RUN")
print("files that would change:", len(changed))
print("absolute URLs rewritten:", stats["abs"], "| relative hrefs rewritten:", stats["rel"])
for e in examples:
    print("   ", e)
if not APPLY:
    print("\nre-run with --apply to write")
else:
    print("\nchanged files:")
    for c in changed:
        print("   ", c)
