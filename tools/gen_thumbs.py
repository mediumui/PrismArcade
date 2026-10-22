#!/usr/bin/env python3
"""Generate stylised gameplay thumbnails (640x360 SVG) for every game.

Design language mirrors the site: dark layered gradient, star field, neon
accent shapes with glow, purple/orange palette (#7c5cff / #ffb347 / #36d399 /
#4aa3ff). Each game gets a hand-drawn minimal "scene" so cards read as real
game art, not text placeholders.

Output: thumbs_svg/<slug>.svg  -> rendered to thumbs/<slug>.jpg by
tools/render_thumbs.mjs (headless Chrome).

Usage: python tools/gen_thumbs.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "thumbs_svg"
DATA = json.loads((ROOT / "tools" / "seo_games_data.json").read_text(encoding="utf-8"))

W, H = 640, 360
CY = 165  # art centre line

# palette
P = {
    "purple": "#7c5cff", "orange": "#ffb347", "gold": "#ffd24d",
    "green": "#36d399", "blue": "#4aa3ff", "red": "#ff5f6d",
    "ink0": "#0b0e1c", "ink1": "#171c38", "panel": "#1d2447",
}


def stars(seed: int, n: int = 26) -> str:
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.randint(8, W - 8), rnd.randint(8, H - 60)
        r = rnd.choice((0.9, 1.2, 1.6, 2.1))
        o = rnd.choice((0.25, 0.4, 0.6))
        c = rnd.choice(("#ffffff", "#cfc4ff", "#ffe0b0"))
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" opacity="{o}"/>')
    return "".join(out)


SHELL = """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{ink0}"/><stop offset="0.55" stop-color="{ink1}"/><stop offset="1" stop-color="#101532"/>
  </linearGradient>
  <radialGradient id="gl1" cx="0.22" cy="0.25" r="0.55">
    <stop offset="0" stop-color="{purple}" stop-opacity="0.34"/><stop offset="1" stop-color="{purple}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="gl2" cx="0.8" cy="0.8" r="0.55">
    <stop offset="0" stop-color="{orange}" stop-opacity="0.26"/><stop offset="1" stop-color="{orange}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#232b58"/><stop offset="1" stop-color="#12162e"/>
  </linearGradient>
  <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="7" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="softglow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="3.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect width="{w}" height="{h}" fill="url(#bg)"/>
<rect width="{w}" height="{h}" fill="url(#gl1)"/>
<rect width="{w}" height="{h}" fill="url(#gl2)"/>
{grid}{stars}
{art}
<text x="32" y="318" font-family="'Segoe UI',Arial,sans-serif" font-size="30" font-weight="700" fill="#ffffff" filter="url(#softglow)">{name}</text>
<text x="32" y="342" font-family="'Segoe UI',Arial,sans-serif" font-size="14" fill="#8f97c4">Prism Arcade &#183; Free &amp; No Download</text>
<text x="{wr}" y="42" text-anchor="end" font-family="'Segoe UI',Arial,sans-serif" font-size="13" font-weight="600" letter-spacing="2" fill="#6f77a8">PRISM ARCADE</text>
</svg>"""


def grid_lines() -> str:
    step = 46
    v = "".join(
        f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#7c5cff" stroke-opacity="0.05"/>'
        for x in range(step, W, step)
    )
    hz = "".join(
        f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#7c5cff" stroke-opacity="0.05"/>'
        for y in range(step, H, step)
    )
    return v + hz


def shell(name: str, art: str, seed: int) -> str:
    return SHELL.format(
        w=W, h=H, wr=W - 32, ink0=P["ink0"], ink1=P["ink1"], purple=P["purple"], orange=P["orange"],
        grid=grid_lines(), stars=stars(seed), art=art, name=name,
    )


# ---------------------------------------------------------------- per-game art

def rr(x, y, w, h, fill, rx=10, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>'


def art_snake() -> str:
    body = (f'<path d="M150 {CY+30} h110 a34 34 0 0 1 0 68 h-60 a34 34 0 0 0 0 68 h180 a40 40 0 0 0 40 -40 v-40'
            f'" fill="none" stroke="{P["green"]}" stroke-width="26" stroke-linecap="round" filter="url(#glow)" opacity="0.95"/>')
    head = (f'<circle cx="420" cy="{CY-12}" r="20" fill="#4ee8ae" filter="url(#glow)"/>'
            f'<circle cx="426" cy="{CY-18}" r="3.2" fill="#0b0e1c"/><circle cx="414" cy="{CY-18}" r="3.2" fill="#0b0e1c"/>')
    food = f'<circle cx="510" cy="{CY+40}" r="11" fill="{P["red"]}" filter="url(#glow)"/>'
    # shrink + lift the scene so the tail clears the caption block
    return f'<g transform="translate(320 180) scale(0.9) translate(-320 -180) translate(0 -16)">{body + head + food}</g>'


def art_2048() -> str:
    vals = [("2", "#3b3f66"), ("4", "#4a4180"), ("128", P["orange"]), ("2048", P["gold"])]
    cells = []
    for i, (v, c) in enumerate(vals):
        x = 205 + (i % 2) * 122
        y = 55 + (i // 2) * 122
        tc = "#0e1230" if c in (P["orange"], P["gold"]) else "#ffffff"
        cells.append(
            rr(x, y, 108, 108, c, rx=16,
               extra=f'filter="url(#softglow)" opacity="0.97"')
            + f'<text x="{x+54}" y="{y+66}" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="{30 if len(v)<3 else 24}" font-weight="800" fill="{tc}">{v}</text>'
        )
    return "".join(cells)


def art_flappy() -> str:
    pipes = (
        rr(150, 0, 66, 120, "#2f9e6e", rx=8) + rr(142, 108, 82, 26, "#37b87f", rx=8)
        + rr(430, 210, 66, 150, "#2f9e6e", rx=8) + rr(422, 198, 82, 26, "#37b87f", rx=8)
    )
    bird = (
        f'<g filter="url(#glow)"><circle cx="300" cy="{CY+6}" r="26" fill="{P["gold"]}"/>'
        f'<circle cx="310" cy="{CY}" r="4" fill="#101532"/><circle cx="312" cy="{CY-1.5}" r="1.6" fill="#fff"/>'
        f'<path d="M292 {CY+6} l-18 8 18 8 z" fill="{P["orange"]}"/>'
        f'<path d="M282 {CY+10} q16 -14 34 -2 q-16 10 -34 2" fill="#e8a13a"/></g>'
    )
    return pipes + bird


def art_memory() -> str:
    cards = []
    pos = [(168, 70), (296, 70), (424, 70)]
    # two face-down, one revealed
    for i, (x, y) in enumerate(pos):
        if i < 2:
            cards.append(rr(x, y, 108, 150, f'url(#cardback)', rx=14)
                         .replace("url(#cardback)", P["purple"])
                         + f'<circle cx="{x+54}" cy="{y+75}" r="26" fill="none" stroke="#ffffff" stroke-opacity="0.5" stroke-width="4"/>'
                         + f'<text x="{x+54}" y="{y+86}" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="30" font-weight="800" fill="#ffffff" opacity="0.85">?</text>')
        else:
            cards.append(rr(x, y, 108, 150, P["orange"], rx=14, extra='filter="url(#glow)"')
                         + f'<circle cx="{x+54}" cy="{y+75}" r="30" fill="none" stroke="#101532" stroke-width="6"/>'
                         + f'<circle cx="{x+54}" cy="{y+75}" r="12" fill="{P["gold"]}"/>')
    return "".join(cards)


def art_whack() -> str:
    holes = []
    for i, (x, y) in enumerate([(190, 210), (320, 210), (450, 210)]):
        holes.append(f'<ellipse cx="{x}" cy="{y}" rx="58" ry="16" fill="#0a0d1a"/>')
        lit = i in (0, 2)
        col = P["gold"] if lit else "#3a3f66"
        extra = 'filter="url(#glow)"' if lit else ""
        holes.append(f'<circle cx="{x}" cy="{y-26}" r="30" fill="{col}" {extra}/>')
        if lit:
            holes.append(f'<circle cx="{x-10}" cy="{y-32}" r="4" fill="#101532"/><circle cx="{x+10}" cy="{y-32}" r="4" fill="#101532"/>')
    return "".join(holes)


def art_tictactoe() -> str:
    ln = f'stroke="#5a61a0" stroke-width="7" stroke-linecap="round" opacity="0.9"'
    g = (f'<line x1="250" y1="60" x2="250" y2="270" {ln}/><line x1="390" y1="60" x2="390" y2="270" {ln}/>'
         f'<line x1="160" y1="130" x2="480" y2="130" {ln}/><line x1="160" y1="200" x2="480" y2="200" {ln}/>')
    xmark = (f'<g stroke="{P["orange"]}" stroke-width="12" stroke-linecap="round" filter="url(#glow)">'
             f'<line x1="278" y1="78" x2="362" y2="112"/><line x1="362" y1="78" x2="278" y2="112"/></g>')
    omark = (f'<circle cx="320" cy="235" r="26" fill="none" stroke="{P["blue"]}" stroke-width="12" filter="url(#glow)"/>'
             f'<g stroke="{P["orange"]}" stroke-width="12" stroke-linecap="round" filter="url(#glow)">'
             f'<line x1="418" y1="148" x2="462" y2="182"/><line x1="462" y1="148" x2="418" y2="182"/></g>')
    return g + xmark + omark


def art_connect4() -> str:
    board = rr(170, 48, 300, 224, "#20305e", rx=18)
    cells = []
    colors = {(0, 1): P["red"], (1, 2): P["gold"], (2, 1): P["red"], (1, 1): P["gold"], (2, 3): P["gold"], (0, 3): P["red"]}
    for row in range(4):
        for col in range(6):
            cx, cy = 205 + col * 46, 84 + row * 50
            fill = colors.get((row, col), "#141a38")
            cells.append(f'<circle cx="{cx}" cy="{cy}" r="17" fill="{fill}"/>')
    return board + "".join(cells)


def art_sudoku() -> str:
    g = ['<g stroke="#5a61a0" stroke-width="2" opacity="0.9">']
    for i in range(5):
        off = i * 70
        wdt = 4 if i in (0, 2, 4) else 2
        g.append(f'<line x1="{200+off}" y1="55" x2="{200+off}" y2="265" stroke-width="{wdt}"/>')
        g.append(f'<line x1="200" y1="{55+off}" x2="440" y2="{55+off}" stroke-width="{wdt}"/>')
    g.append("</g>")
    nums = [((235, 105), "2", P["gold"]), ((305, 105), "3", "#cfd4f5"), ((375, 175), "1", P["orange"]),
            ((235, 245), "4", "#cfd4f5"), ((305, 245), "1", P["gold"])]
    t = "".join(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="34" font-weight="700" fill="{c}">{n}</text>'
                for (x, y), n, c in nums)
    return "".join(g) + t


def art_reaction() -> str:
    return (
        f'<circle cx="320" cy="{CY}" r="95" fill="none" stroke="{P["red"]}" stroke-width="14" opacity="0.85"/>'
        f'<circle cx="320" cy="{CY}" r="62" fill="none" stroke="{P["gold"]}" stroke-width="14" opacity="0.9"/>'
        f'<circle cx="320" cy="{CY}" r="30" fill="{P["green"]}" filter="url(#glow)"/>'
        f'<text x="320" y="{CY+9}" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="26" font-weight="800" fill="#0e1230">GO</text>'
    )


def art_sequence() -> str:
    pads = [(P["purple"], False), (P["orange"], True), (P["green"], False), (P["blue"], False)]
    out = []
    for i, (c, lit) in enumerate(pads):
        x, y = 236 + (i % 2) * 110, 70 + (i // 2) * 110
        extra = 'filter="url(#glow)" opacity="1"' if lit else 'opacity="0.55"'
        out.append(rr(x, y, 92, 92, c, rx=18, extra=extra))
        out.append(f'<text x="{x+46}" y="{y+60}" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="38" font-weight="800" fill="#0e1230" opacity="{0.9 if lit else 0.55}">{i+1}</text>')
    return "".join(out)


def art_quicktap() -> str:
    out = []
    lit = (1, 0)
    for r in range(3):
        for c in range(3):
            x, y = 205 + c * 84, 62 + r * 84
            on = (c, r) == lit
            col = P["gold"] if on else "#242b52"
            extra = 'filter="url(#glow)"' if on else ""
            out.append(rr(x, y, 70, 70, col, rx=14, extra=extra))
            if on:
                out.append(f'<circle cx="{x+35}" cy="{y+35}" r="12" fill="#101532"/>'
                           f'<circle cx="{x+35}" cy="{y+35}" r="4" fill="{P["gold"]}"/>')
    return "".join(out)


def art_maze() -> str:
    ln = f'stroke="#7c86c9" stroke-width="6" stroke-linecap="round" fill="none"'
    walls = (f'<path d="M180 70 h200 v60 h-140 v60 h180" {ln}/>'
             f'<path d="M180 70 v190 h280 v-70 h-80" {ln}/>'
             f'<path d="M240 190 v70" {ln} stroke-opacity="0.6"/>')
    start = f'<circle cx="200" cy="92" r="11" fill="{P["green"]}" filter="url(#glow)"/>'
    goal = f'<circle cx="460" cy="238" r="11" fill="{P["gold"]}" filter="url(#glow)"/>'
    return walls + start + goal


def art_stack() -> str:
    bars = []
    widths = [260, 240, 220, 200, 180]
    cols = [P["purple"], "#6a4fe0", P["blue"], "#3d8fe0", P["green"]]
    for i, (wd, c) in enumerate(zip(widths, cols)):
        x = 320 - wd / 2 + (i * 6)
        y = 250 - i * 40
        op = "1" if i < 4 else "0.95"
        extra = 'filter="url(#glow)"' if i == 3 else ""
        bars.append(rr(x, y, wd, 32, c, rx=8, extra=f'{extra} opacity="{op}"'))
    tilt = f'<g transform="rotate(-8 320 66)">{rr(260, 50, 200, 32, P["orange"], rx=8, extra="filter=\"url(#glow)\"")}</g>'
    return "".join(bars) + tilt


def art_runner() -> str:
    moon = f'<circle cx="520" cy="80" r="26" fill="#e8ecff" opacity="0.9"/><circle cx="510" cy="72" r="26" fill="{P["ink1"]}"/>'
    ground = f'<rect x="0" y="252" width="{W}" height="10" fill="#2b3260"/>'
    hero = (f'<g filter="url(#glow)">{rr(230, 176, 52, 52, P["orange"], rx=12)}'
            f'<circle cx="248" cy="196" r="4.5" fill="#101532"/><circle cx="266" cy="196" r="4.5" fill="#101532"/>'
            f'<path d="M244 212 q11 8 24 0" stroke="#101532" stroke-width="3.5" fill="none" stroke-linecap="round"/></g>')
    spike = f'<path d="M400 252 l20 -34 20 34 z" fill="{P["red"]}" filter="url(#softglow)"/>'
    dust = f'<circle cx="216" cy="238" r="6" fill="#cfc4ff" opacity="0.5"/><circle cx="200" cy="244" r="4" fill="#cfc4ff" opacity="0.35"/>'
    return moon + ground + hero + spike + dust


def art_slide() -> str:
    nums = ["1", "2", "3", "4", "5", "6", "7", None]
    out = []
    for i, n in enumerate(nums):
        x, y = 236 + (i % 3) * 82, 66 + (i // 3) * 82
        if n is None:
            out.append(rr(x, y, 70, 70, "#12162e", rx=12, extra='stroke="#3a4180" stroke-dasharray="6 6"'))
            continue
        c = P["purple"] if (i % 2 == 0) else "#5a48c8"
        out.append(rr(x, y, 70, 70, c, rx=12, extra='filter="url(#softglow)" opacity="0.95"'))
        out.append(f'<text x="{x+35}" y="{y+48}" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="32" font-weight="800" fill="#ffffff">{n}</text>')
    return "".join(out)


def art_colorsort() -> str:
    tube_cols = [(P["red"], P["orange"]), (P["green"], P["blue"]), (P["gold"], P["purple"]), (P["blue"], P["red"])]
    out = []
    for i, (c1, c2) in enumerate(tube_cols):
        x = 190 + i * 78
        out.append(rr(x, 70, 46, 170, "#141a38", rx=16, extra='stroke="#3a4180" stroke-width="2"'))
        out.append(rr(x + 5, 200, 36, 32, c1, rx=8))
        out.append(rr(x + 5, 168, 36, 30, c2, rx=8))
        if i == 1:
            out.append(rr(x + 5, 140, 36, 26, c1, rx=8, extra='filter="url(#softglow)"'))
    return "".join(out)


def art_hangman() -> str:
    gallows = (f'<g stroke="#8f97c4" stroke-width="7" stroke-linecap="round">'
               f'<line x1="180" y1="252" x2="300" y2="252"/><line x1="210" y1="252" x2="210" y2="80"/>'
               f'<line x1="210" y1="80" x2="300" y2="80"/><line x1="300" y1="80" x2="300" y2="106"/></g>')
    head = f'<circle cx="300" cy="128" r="20" fill="none" stroke="{P["orange"]}" stroke-width="6" filter="url(#softglow)"/>'
    blanks = "".join(
        f'<line x1="{372 + i * 44}" y1="180" x2="{404 + i * 44}" y2="180" stroke="#cfd4f5" stroke-width="5" stroke-linecap="round"/>'
        for i in range(4)
    )
    letters = (f'<text x="388" y="168" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="30" font-weight="800" fill="{P["green"]}">C</text>'
               f'<text x="432" y="168" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="30" font-weight="800" fill="{P["green"]}">A</text>')
    return gallows + head + blanks + letters


def art_quiz() -> str:
    q = (f'<circle cx="238" cy="118" r="44" fill="{P["purple"]}" filter="url(#glow)"/>'
         f'<text x="238" y="136" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="46" font-weight="800" fill="#ffffff">?</text>')
    opts = []
    for i, (txt, ok) in enumerate([("2 + 2 = 4", True), ("Fire is cold", False), ("Cats can fly", False)]):
        y = 196 + i * 44
        c = P["green"] if ok else "#242b52"
        extra = 'filter="url(#softglow)"' if ok else ""
        opts.append(rr(310, y, 200, 34, c, rx=17, extra=extra))
        opts.append(f'<text x="{410}" y="{y+23}" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="17" font-weight="600" fill="{"#0e1230" if ok else "#aeb6e8"}">{txt}</text>')
    return q + "".join(opts)


def art_numbermerge() -> str:
    a = (rr(200, 110, 110, 110, P["orange"], rx=20, extra='filter="url(#softglow)"')
         + f'<text x="255" y="180" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="44" font-weight="800" fill="#0e1230">8</text>')
    plus = f'<text x="330" y="182" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="44" font-weight="800" fill="#8f97c4">+</text>'
    b = (rr(356, 110, 110, 110, P["orange"], rx=20, extra='filter="url(#softglow)"')
         + f'<text x="411" y="180" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="44" font-weight="800" fill="#0e1230">8</text>')
    res = (f'<g transform="translate(306,90) rotate(45)"><rect x="-14" y="-40" width="28" height="80" rx="6" fill="{P["gold"]}" filter="url(#glow)"/></g>'
           f'<text x="521" y="180" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="40" font-weight="800" fill="{P["gold"]}">16</text>')
    return a + plus + b + res


def art_wordmerge() -> str:
    letters = [("W", P["purple"]), ("O", P["orange"]), ("R", P["green"]), ("D", P["blue"])]
    out = []
    for i, (ch, c) in enumerate(letters):
        x = 196 + i * 66
        out.append(rr(x, 120, 56, 56, c, rx=12, extra='filter="url(#softglow)" opacity="0.95"'))
        out.append(f'<text x="{x+28}" y="{158}" text-anchor="middle" font-family="\'Segoe UI\',Arial" font-size="30" font-weight="800" fill="#ffffff">{ch}</text>')
    tray = rr(180, 210, 280, 14, "#2b3260", rx=7)
    return "".join(out) + tray


def art_blockslide() -> str:
    out = []
    blocks = [(0, 0, 2, 1, P["purple"]), (2, 0, 1, 1, "#4a4180"), (3, 0, 1, 2, P["blue"]),
              (0, 1, 1, 1, "#4a4180"), (1, 1, 1, 2, P["orange"]), (2, 2, 2, 1, "#4a4180"),
              (0, 2, 1, 1, P["green"])]
    for c, r, cs, rs, col in blocks:
        x, y = 210 + c * 66, 70 + r * 66
        out.append(rr(x + 3, y + 3, cs * 66 - 6, rs * 66 - 6, col, rx=10,
                      extra='filter="url(#softglow)" opacity="0.95"' if col in (P["orange"], P["green"]) else ""))
    return "".join(out)


def art_reflexrelay() -> str:
    return art_sequence()  # same family of memory pads


def art_flappy_alt() -> str:
    return art_flappy()


def art_catalog() -> str:
    """Grid of mini tiles — used by the 'All Games' card in the related strip."""
    cols, rows, cw, ch, gap = 4, 3, 96, 62, 14
    x0 = (W - (cols * cw + (cols - 1) * gap)) / 2
    y0 = 26
    hues = (P["purple"], P["orange"], P["gold"], P["green"], P["blue"], P["red"])
    glyphs = ("◆", "▲", "●", "■", "✦", "▮")
    rnd = random.Random(7)
    out = []
    for r in range(rows):
        for c in range(cols):
            x, y = x0 + c * (cw + gap), y0 + r * (ch + gap)
            col = hues[(r * cols + c) % len(hues)]
            g = glyphs[(r * cols + c) % len(glyphs)]
            alpha = rnd.choice((0.55, 0.75, 0.92))
            out.append(
                rr(x, y, cw, ch, col, rx=12, extra=f'opacity="{alpha}" filter="url(#softglow)"')
            )
            out.append(
                f'<text x="{x + cw / 2}" y="{y + ch / 2 + 7}" text-anchor="middle" '
                f'font-family="Segoe UI Symbol,Arial" font-size="22" fill="#0d1130" opacity="0.72">{g}</text>'
            )
    return "".join(out)


ART = {
    "snake": art_snake, "2048": art_2048, "flappy": art_flappy, "memory": art_memory,
    "whack": art_whack, "tic-tac-toe": art_tictactoe, "connect4": art_connect4,
    "sudoku": art_sudoku, "reaction-test": art_reaction, "sequence": art_sequence,
    "reflex-relay": art_reflexrelay, "quick-tap": art_quicktap, "maze": art_maze,
    "stack-tower": art_stack, "runner": art_runner, "sliding-number": art_slide,
    "color-sort": art_colorsort, "hangman": art_hangman, "quiz": art_quiz,
    "number-merge": art_numbermerge, "word-merge": art_wordmerge, "block-slide": art_blockslide,
}


# non-game cards that still need a real preview image
EXTRA = {"_all-games": (art_catalog, "All Games")}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    jobs = [(s, fn, DATA.get(f"{s}.html", {}).get("name", s.replace("-", " ").title()))
            for s, fn in ART.items()]
    jobs += [(s, fn, nm) for s, (fn, nm) in EXTRA.items()]
    for slug, fn, name in jobs:
        svg = shell(name, fn(), seed=sum(ord(c) for c in slug))
        (OUT / f"{slug}.svg").write_text(svg, encoding="utf-8")
        print(f"{slug}.svg  ({name})")
    print(f"\n{len(jobs)} SVGs -> {OUT}")


if __name__ == "__main__":
    main()
