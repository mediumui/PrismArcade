#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local GEO readiness audit for Prism Arcade.

Replicates the 7 checks used by the upstream geo-optimizer audit:
  1. llms.txt        -> HTTP 200
  2. robots.txt      -> HTTP 200
  3. sitemap.xml     -> HTTP 200 (+ new game URLs present)
  4. Homepage JSON-LD -> schema.org JSON-LD present
  5. Homepage <h1>    -> has <h1>
  6. FAQ/QA markup   -> FAQPage detected (visible + JSON-LD)
  7. About/Author signals -> about/author refs found (about.html reachable)

Usage:
  python tools/geo_audit.py http://localhost:8080
"""
import sys
import urllib.request
import urllib.error

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8080"
NEW_GAMES = [
    "/games/typing-test.html",
    "/games/word-search.html",
    "/games/block-fit.html",
    "/games/nonogram.html",
]

# Cloudflare answers 403 to the default python-urllib UA, so audits against
# the live site must present a normal browser UA (same as the local run).
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(path):
    url = BASE + path
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa
        return -1, f"ERR:{e}"


def check(name, ok, detail=""):
    mark = "✅ PASS" if ok else "❌ FAIL"
    print(f"| {name:<22} | {mark} | {detail}")
    return ok


def main():
    results = []
    print(f"# GEO Audit — {BASE}\n")
    print("| Check                | Result  | Detail |")
    print("|----------------------|---------|--------|")

    # 1. llms.txt
    s, b = get("/llms.txt")
    results.append(check("llms.txt", s == 200 and "Prism Arcade" in b,
                         f"HTTP {s}, {len(b)} bytes" if s == 200 else f"HTTP {s}"))

    # 2. robots.txt
    s, b = get("/robots.txt")
    results.append(check("robots.txt", s == 200,
                         f"HTTP {s}" if s == 200 else f"HTTP {s}"))

    # 3. sitemap.xml
    s, b = get("/sitemap.xml")
    missing = [g for g in NEW_GAMES if g not in b]
    results.append(check("sitemap.xml", s == 200 and not missing,
                         f"HTTP {s}" + ("" if not missing else f", missing {missing}")))

    # 4. Homepage JSON-LD
    s, b = get("/")
    has_ld = s == 200 and "application/ld+json" in b and "schema.org" in b
    results.append(check("Homepage JSON-LD", has_ld,
                         f"HTTP {s}" if s == 200 else f"HTTP {s}"))

    # 5. Homepage <h1>
    has_h1 = s == 200 and "<h1" in b
    results.append(check("Homepage <h1>", has_h1,
                         f"HTTP {s}" if s == 200 else f"HTTP {s}"))

    # 6. FAQ/QA markup
    has_faq = s == 200 and "FAQPage" in b
    results.append(check("FAQ/QA markup", has_faq,
                         f"HTTP {s}" if s == 200 else f"HTTP {s}"))

    # 7. About/Author signals
    s2, b2 = get("/about.html")
    about_ok = s2 == 200 and ("about" in b2.lower() or "author" in b2.lower())
    # homepage must also link to about; the site now serves clean URLs
    # (/about), so accept either form
    link_ok = s == 200 and ("about.html" in b or 'href="about"' in b)
    results.append(check("About/Author signals", about_ok and link_ok,
                         f"about.html HTTP {s2}, home->about link={'yes' if link_ok else 'no'}"))

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n## Result: {passed}/{total} checks PASS")
    if passed == total:
        print("✅ All GEO checks passed.")
        return 0
    print("❌ Some checks failed — fix before deploy.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
