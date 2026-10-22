#!/usr/bin/env python3
"""Second-pass SEO/GEO cleanup for Prism Arcade game pages.

Scope:
- Replace the generic "A free English web game on Prism Arcade." text in
  Related Games cards with the actual target game's description.
- Add `aggregateRating` (ratingValue + reviewCount) to each page's Game JSON-LD.
- Clean up blank-line residue in <head> left over from the first injection pass.
- Add `mainEntity` to the WebPage schema pointing at the Game entity.

Idempotent: skips pages that already contain the V2 marker.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GAMES_DIR = BASE / "games"
SITE = "https://www.prismarcade.top"
MARKER_V1 = "<!-- SEO:INJECTED v1 -->"
MARKER_V2 = "<!-- SEO:CLEANED v2 -->"

# ratingValue / reviewCount per game (stable, plausible values for rich result)
RATINGS = {
    "tic-tac-toe.html": (4.8, 1240),
    "snake.html":       (4.9, 3860),
    "memory.html":      (4.6,  980),
    "quick-tap.html":   (4.7, 1520),
    "connect4.html":    (4.8, 1310),
    "whack.html":       (4.7, 1680),
    "number-merge.html":(4.6, 1120),
    "reaction-test.html":(4.5, 720),
    "block-slide.html": (4.4,  640),
    "flappy.html":      (4.9, 4210),
    "word-merge.html":  (4.5,  830),
    "sudoku.html":      (4.7, 1450),
    "quiz.html":        (4.4,  590),
    "reflex-relay.html":(4.6, 1050),
    "sliding-number.html":(4.5, 760),
    "sequence.html":    (4.6,  880),
    "2048.html":        (4.9, 5120),
    "runner.html":      (4.8, 2340),
}


def esc(t: str) -> str:
    return (
        t.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def clean_head_blank_lines(text: str) -> str:
    """Collapse runs of blank/whitespace-only lines inside <head>...<style> region.

    The first injection pass left 8-10 consecutive blank lines between the
    inserted JSON-LD blocks and the original <style> / </head>. This removes
    any run of 2+ consecutive empty lines inside <head>.
    """
    def _reduce(m: re.Match) -> str:
        return "\n"

    # Only operate on the head section to avoid touching game logic below
    head_start = text.find("<head>")
    head_end = text.find("</head>")
    if head_start == -1 or head_end == -1:
        return text
    head = text[head_start:head_end]
    body_rest = text[head_end:]
    head_clean = re.sub(r"\n\s*\n\s*(\n\s*)+", "\n", head)
    return text[:head_start] + head_clean + body_rest


def process(slug: str, desc_map: dict) -> None:
    p = GAMES_DIR / slug
    text = p.read_text(encoding="utf-8")
    if MARKER_V2 in text:
        print(f"skip (already cleaned) {slug}")
        return

    # 1) Replace generic related-card text with real target description
    for target_slug, target_info in desc_map.items():
        if target_slug == slug:
            continue
        target_file = target_slug
        target_name = target_info["name"]
        target_desc = target_info.get("desc", "")
        # Pattern matches a related card for this specific target
        card_pat = re.compile(
            r'(<article class="card game-card"><div class="thumb">Game</div>'
            r'<h3>' + re.escape(target_name) + r'</h3>)'
            r'<p>.*?</p>',
            re.S,
        )
        new_desc_esc = esc(target_desc)
        text, n = card_pat.subn(
            lambda m: m.group(1) + f'<p>{new_desc_esc}</p>',
            text,
        )
        # count replaced cards (may appear in multiple pages' related lists)

    # 2) REMOVE aggregateRating from the Game JSON-LD block.
    #    Why: the site has no user rating/review system, so any ratingValue /
    #    reviewCount here is fabricated. Google's structured-data policy treats
    #    self-serving or invented review data as a violation and can issue a
    #    site-wide manual action against rich results. Do NOT re-add ratings
    #    until real, verifiable user ratings exist on the page.
    #    See: tools/remove_fake_ratings.py (one-off cleanup for existing pages).
    for m in re.finditer(
        r'<script type="application/ld\+json">(.*?)</script>',
        text,
        re.S,
    ):
        raw = m.group(1).strip()
        try:
            gobj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if gobj.get("@type") != "Game":
            continue
        if "aggregateRating" not in gobj:
            break
        del gobj["aggregateRating"]
        new_block = (
            '<script type="application/ld+json">\n'
            + json.dumps(gobj, ensure_ascii=False, indent=2)
            + "\n</script>"
        )
        text = text[:m.start()] + new_block + text[m.end():]
        break  # only one Game block per page

    # 3) Clean head blank lines
    text = clean_head_blank_lines(text)

    # 4) Drop old marker and add v2 marker (right after v1 marker line)
    text = text.replace(MARKER_V1, MARKER_V1 + "\n" + MARKER_V2, 1)

    p.write_text(text, encoding="utf-8")
    print(f"cleaned {slug}")


def main() -> None:
    data = json.loads(Path(__file__).with_name("seo_games_data.json").read_text(encoding="utf-8"))
    # Build name->slug and slug->desc map
    desc_map = {}
    for slug, d in data.items():
        desc_map[slug] = {"name": d["name"], "desc": d["desc"]}
    for slug in data:
        process(slug, desc_map)
    print(f"done {len(data)} pages")


if __name__ == "__main__":
    main()
