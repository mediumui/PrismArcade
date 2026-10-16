#!/usr/bin/env python3
"""Inject SEO/GEO metadata into Prism Arcade game pages.

Scope:
- rewrites <title> / meta description / robots / canonical / OG / Twitter in head
- injects JSON-LD: WebPage, BreadcrumbList, Game, FAQPage
- inserts a visible FAQ section + Related Games section before </main>
- does NOT change game logic, CSS, or JS behavior
- idempotent: skips pages containing MARKER
"""
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GAMES_DIR = BASE / "games"
SITE = "https://www.prismarcade.top"
MARKER = "<!-- SEO:INJECTED v1 -->"
STYLE = '<link rel="stylesheet" href="../css/style.css" />'

def esc(t):
    return t.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")

def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False, indent=2) + "\n</script>"

def build_head(slug, d):
    url = f"{SITE}/games/{slug}"
    faq_schema = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q["q"],"acceptedAnswer":{"@type":"Answer","text":q["a"]}} for q in d["faq"]
    ]}
    breadcrumb = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"Games","item":SITE+"/index.html#games"},
        {"@type":"ListItem","position":3,"name":d["name"],"item":url},
    ]}
    game = {"@context":"https://schema.org","@type":"Game","name":d["name"],"url":url,
            "description":d["desc"],"gameCategory":d["category"],"playMode":d["playmode"],
            "isAccessibleForFree":True,"inLanguage":"en",
            "offers":{"@type":"Offer","price":0,"priceCurrency":"USD","url":url},
            "brand":{"@type":"Organization","name":"Prism Arcade","url":SITE+"/"}}
    webpage = {"@context":"https://schema.org","@type":"WebPage","name":d["title"],"url":url,
               "description":d["desc"],"inLanguage":"en"}
    og_img = f"{SITE}/og/games/{slug[:-5]}.jpg"
    meta = (
        f'  <title>{esc(d["title"])}</title>\n'
        f'  <meta name="description" content="{esc(d["desc"])}" />\n'
        f'  <meta name="robots" content="index, follow" />\n'
        f'  <link rel="canonical" href="{url}" />\n'
        f'  <meta property="og:type" content="website" />\n'
        f'  <meta property="og:title" content="{esc(d["og_title"])}" />\n'
        f'  <meta property="og:description" content="{esc(d["desc"])}" />\n'
        f'  <meta property="og:url" content="{url}" />\n'
        f'  <meta property="og:site_name" content="Prism Arcade" />\n'
        f'  <meta property="og:image" content="{og_img}" />\n'
        f'  <meta name="twitter:card" content="summary_large_image" />\n'
        f'  <meta name="twitter:title" content="{esc(d["og_title"])}" />\n'
        f'  <meta name="twitter:description" content="{esc(d["desc"])}" />\n'
        f'  <meta name="twitter:image" content="{og_img}" />\n'
        '  <meta name="twitter:site" content="@prismarcade" />\n'
    )
    schemas = "\n".join([jsonld(webpage), jsonld(breadcrumb), jsonld(game), jsonld(faq_schema)])
    return meta + "\n" + schemas + "\n  " + STYLE + "\n"

def build_faq_html(d):
    lines = ['      <section class="container seo-faq" aria-label="Frequently asked questions">']
    lines.append('        <div class="section-title"><div><h2>FAQ</h2><p>Clear answers for players, search engines, and AI assistants.</p></div></div>')
    lines.append('        <div class="faq-grid">')
    for q in d["faq"]:
        lines.append(f'          <article class="card"><h3>{esc(q["q"])}</h3><p>{esc(q["a"])}</p></article>')
    lines.append("        </div>")
    lines.append("      </section>")
    return "\n".join(lines)

def build_related_html(d):
    lines = ['      <section class="container seo-related" aria-label="Related games">']
    lines.append('        <div class="section-title"><div><h2>Related Games</h2><p>Keep playing with similar free browser games on Prism Arcade.</p></div></div>')
    lines.append('        <div class="grid related-grid">')
    for r in d["related"]:
        lines.append(f'          <article class="card game-card"><div class="thumb">Game</div><h3>{esc(r["name"])}</h3><p>A free English web game on Prism Arcade.</p><a class="btn btn-ghost" href="{r["file"]}">Play</a></article>')
    lines.append('          <article class="card game-card"><div class="thumb">All</div><h3>All Games</h3><p>Browse the full Prism Arcade catalog.</p><a class="btn btn-ghost" href="../index.html#games">Browse</a></article>')
    lines.append("        </div>")
    lines.append("      </section>")
    return "\n".join(lines)

def build_overview_html(d):
    return f'      <section class="container seo-overview" aria-label="Game overview">\n        <div class="hero-card"><h3>About {esc(d["name"])}</h3><p>{esc(d["overview"])}</p></div>\n      </section>'

def process(slug):
    d = GAMES[slug]
    p = GAMES_DIR / slug
    text = p.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"skip (already injected) {slug}")
        return
    # replace head block: from first <title> up to and including the stylesheet link or </head>
    head_new = build_head(slug, d)
    # Remove old <title>...</title> and everything up to </head> before stylesheet, then rebuild
    # Strategy: keep lines before <head>, keep charset/viewport, replace rest until </head>
    m_head = re.search(r"(<head>.*?<meta name=\"viewport\"[^>]*>)", text, re.S)
    if m_head:
        prefix = text[:m_head.end()]
        rest = text[m_head.end():]
        rest = re.sub(r"<title>.*?</title>", "", rest, flags=re.S)
        rest = re.sub(r'<meta name="description"[^>]*>', "", rest, flags=re.S)
        rest = re.sub(r'<meta name="robots"[^>]*>', "", rest, flags=re.S)
        rest = re.sub(r'<link rel="canonical"[^>]*>', "", rest, flags=re.S)
        rest = re.sub(r'<meta property="og:[^"]*"[^>]*>', "", rest, flags=re.S)
        rest = re.sub(r'<meta name="twitter:[^"]*"[^>]*>', "", rest, flags=re.S)
        rest = re.sub(r'<script type="application/ld\+json">.*?</script>', "", rest, flags=re.S)
        rest = re.sub(r'<link rel="stylesheet" href="\.\./css/style\.css" />', "", rest, flags=re.S)
        # now insert our new head content right after viewport, and keep the rest (style blocks etc.)
        # The rest may still contain <style> blocks and </head>. We need to place schema before </head>.
        # Find </head> position in rest
        head_end = rest.find("</head>")
        if head_end == -1:
            raise RuntimeError(f"no </head> found in {slug}")
        pre = rest[:head_end]
        post = rest[head_end:]
        text = prefix + "\n" + head_new + "\n" + pre + post

    # inject overview + faq + related before </main>
    close_main = text.find("</main>")
    if close_main == -1:
        raise RuntimeError(f"no </main> in {slug}")
    insert = MARKER + "\n" + build_overview_html(d) + "\n" + build_faq_html(d) + "\n" + build_related_html(d)
    text = text[:close_main] + insert + "\n  " + text[close_main:]

    p.write_text(text, encoding="utf-8")
    print(f"updated {slug}")

if __name__ == "__main__":
    GAMES = json.loads(Path(__file__).with_name("seo_games_data.json").read_text(encoding="utf-8"))
    for slug in GAMES:
        process(slug)
    print(f"done {len(GAMES)} pages")
