#!/usr/bin/env python3
"""Chrome-free thumbnail + OG image generator for the 3 new Prism Arcade games.

No browser/svg rasterizer needed. Draws neon scenes with Pillow (screen-blend glow)
matching the existing site thumbnail style (dark purple->blue gradient, stars,
game title bottom-left, PRISM ARCADE top-right).

Output:
  thumbs/<slug>.jpg       480x270
  og/games/<slug>.jpg     1200x630
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THUMB_DIR = os.path.join(ROOT, "thumbs")
OG_DIR = os.path.join(ROOT, "og", "games")
os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(OG_DIR, exist_ok=True)

PALETTE = ["#7c5cff", "#ffb347", "#ffd24d", "#36d399", "#4aa3ff"]
PURPLE, ORANGE, YELLOW, GREEN, BLUE = PALETTE
RED = "#ff5f6d"


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def vgrad(w, h, top, bottom):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    t, b = hx(top), hx(bottom)
    for y in range(h):
        f = y / (h - 1)
        c = tuple(int(t[i] + (b[i] - t[i]) * f) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def stars(d, w, h, n, seed):
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.randint(0, w - 1)
        y = rnd.randint(0, h - 1)
        r = rnd.choice([1, 1, 1, 2])
        a = rnd.randint(120, 230)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(a, a, a))


def screen_blend(base, glow):
    return ImageChops.screen(base, glow).convert("RGB")


# ---- per-game scene drawers (bright neon shapes on a black layer) ----
def scene_bubbles(d, w, h):
    cx, cy = w * 0.52, h * 0.30
    r = min(w, h) * 0.07
    rowh = r * 1.75
    cols = 5
    for ri, row in enumerate(range(4)):
        offset = (ri % 2) * r
        for ci in range(cols):
            x = cx - (cols - 1) * r + ci * 2 * r + offset
            y = cy - 1.5 * rowh + row * rowh
            col = PALETTE[(ri * cols + ci) % len(PALETTE)]
            d.ellipse([x - r, y - r, x + r, y + r], fill=hx(col))
            hr = r * 0.32
            d.ellipse([x - r * 0.5 - hr, y - r * 0.5 - hr, x - r * 0.5 + hr, y - r * 0.5 + hr], fill=(255, 255, 255))
    ccx, ccy = w * 0.52, h * 0.58
    cr = min(w, h) * 0.06
    d.pieslice([ccx - cr, ccy - cr, ccx + cr, ccy + cr], 200, 340, fill=hx(ORANGE))


def scene_bricks(d, w, h):
    bw = w * 0.105
    bh = h * 0.07
    gap = w * 0.008
    top = h * 0.10
    cols = 7
    for r in range(3):
        for c in range(cols):
            x = w * 0.16 + c * (bw + gap)
            y = top + r * (bh + gap)
            col = PALETTE[(r * cols + c) % len(PALETTE)]
            d.rounded_rectangle([x, y, x + bw, y + bh], radius=bh * 0.3, fill=hx(col))
    pw = w * 0.18
    ph = h * 0.035
    px = w * 0.5 - pw / 2
    py = h * 0.68
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph / 2, fill=hx(BLUE))
    br = h * 0.028
    bx, by = w * 0.5, py - br * 2.2
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=hx(YELLOW))


def scene_mines(d, w, h):
    cols, rows = 6, 4
    cw = w * 0.115
    ch = h * 0.15
    gx = w * 0.5 - cols * cw / 2
    gy = h * 0.12
    revealed = {(1, 1), (2, 1), (3, 2), (4, 0)}
    mine = (2, 2)
    flag = (4, 3)
    for r in range(rows):
        for c in range(cols):
            x = gx + c * cw
            y = gy + r * ch
            pad = cw * 0.08
            if (c, r) in revealed:
                d.rounded_rectangle(
                    [x + pad, y + pad, x + cw - pad, y + ch - pad],
                    radius=cw * 0.12,
                    fill=(46, 34, 82),
                )
            d.rounded_rectangle(
                [x + pad, y + pad, x + cw - pad, y + ch - pad],
                radius=cw * 0.12,
                outline=hx(PURPLE),
                width=max(2, int(min(cw, ch) * 0.04)),
            )
            if (c, r) == mine:
                mx, my = x + cw / 2, y + ch / 2
                mr = min(cw, ch) * 0.22
                d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=hx(RED))
                for ang in range(0, 360, 45):
                    rad = math.radians(ang)
                    d.line(
                        [mx, my, mx + math.cos(rad) * mr * 1.5, my + math.sin(rad) * mr * 1.5],
                        fill=hx(RED),
                        width=2,
                    )
            if (c, r) == flag:
                fx, fy = x + cw / 2, y + ch / 2
                d.polygon(
                    [(fx, fy - ch * 0.18), (fx, fy + ch * 0.18), (fx + cw * 0.22, fy)],
                    fill=hx(GREEN),
                )


def post_mines(d, w, h):
    cols, rows = 6, 4
    cw = w * 0.115
    ch = h * 0.15
    gx = w * 0.5 - cols * cw / 2
    gy = h * 0.12
    nums = {(1, 1): "1", (2, 1): "2", (3, 2): "3", (4, 0): "1"}
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(min(cw, ch) * 0.5))
    for (c, r), s in nums.items():
        x = gx + c * cw
        y = gy + r * ch
        tw = d.textlength(s, font=font)
        d.text((x + cw / 2 - tw / 2, y + ch / 2 - min(cw, ch) * 0.28), s,
               font=font, fill=hx(ORANGE))


def scene_typing(d, w, h):
    """Neon keyboard + caret: typing test."""
    rows, cols = 3, 8
    kw = w * 0.085
    kh = h * 0.13
    gap = w * 0.012
    gx = w * 0.5 - (cols * (kw + gap) - gap) / 2
    gy = h * 0.30
    lit = (1, 3)
    for r in range(rows):
        for c in range(cols):
            x = gx + c * (kw + gap) + (r * kw * 0.22)
            y = gy + r * (kh + gap)
            col = PALETTE[(r * cols + c) % len(PALETTE)]
            if (r, c) == lit:
                d.rounded_rectangle([x, y, x + kw, y + kh], radius=kh * 0.28, fill=hx(ORANGE))
            else:
                d.rounded_rectangle([x, y, x + kw, y + kh], radius=kh * 0.28,
                                    outline=hx(col), width=max(2, int(w * 0.005)))
    # passage lines above the keyboard
    for i in range(2):
        lw = w * (0.44 if i == 0 else 0.30)
        lx = w * 0.5 - lw / 2
        ly = h * 0.12 + i * h * 0.075
        d.rounded_rectangle([lx, ly, lx + lw, ly + h * 0.035],
                            radius=h * 0.017, fill=(120, 132, 190))
    # caret
    cx = w * 0.5 + w * 0.15
    cy = h * 0.12
    d.rounded_rectangle([cx, cy, cx + w * 0.014, cy + h * 0.035],
                        radius=w * 0.006, fill=hx(YELLOW))


def scene_wordsearch(d, w, h):
    """Letter grid with a found word beam."""
    cols, rows = 8, 5
    cw = w * 0.088
    ch = h * 0.115
    gx = w * 0.5 - cols * cw / 2
    gy = h * 0.10
    for r in range(rows):
        for c in range(cols):
            x = gx + c * cw
            y = gy + r * ch
            d.rounded_rectangle([x + cw * 0.12, y + ch * 0.12,
                                 x + cw * 0.88, y + ch * 0.88],
                                radius=cw * 0.14,
                                outline=hx(PURPLE), width=max(2, int(w * 0.004)))
    # neon beam across one diagonal word
    x1, y1 = gx + cw * 1.5, gy + ch * 3.5
    x2, y2 = gx + cw * 6.5, gy + ch * 0.5
    d.line([x1, y1, x2, y2], fill=hx(GREEN), width=max(6, int(w * 0.022)))


def scene_blockfit(d, w, h):
    """8x8 board with placed blocks and a clearing row."""
    n = 8
    cs = min(w * 0.072, h * 0.085)
    gx = w * 0.5 - n * cs / 2
    gy = h * 0.08
    for r in range(n):
        for c in range(n):
            x = gx + c * cs
            y = gy + r * cs
            d.rounded_rectangle([x + cs * 0.08, y + cs * 0.08,
                                 x + cs * 0.92, y + cs * 0.92],
                                radius=cs * 0.2,
                                outline=hx(PURPLE), width=1)
    placed = [(0, 0), (1, 0), (0, 1), (4, 2), (5, 2), (4, 3), (5, 3), (7, 5), (7, 6)]
    for i, (c, r) in enumerate(placed):
        x = gx + c * cs
        y = gy + r * cs
        col = PALETTE[i % len(PALETTE)]
        d.rounded_rectangle([x + cs * 0.1, y + cs * 0.1, x + cs * 0.9, y + cs * 0.9],
                            radius=cs * 0.2, fill=hx(col))
    # cleared row highlight
    ry = gy + 4 * cs
    d.rounded_rectangle([gx, ry + cs * 0.1, gx + n * cs, ry + cs * 0.9],
                        radius=cs * 0.2, fill=hx(YELLOW))


def scene_nonogram(d, w, h):
    """Grid with clue numbers and solved blocks."""
    n = 7
    cs = min(w * 0.085, h * 0.1)
    gx = w * 0.5 - n * cs / 2 + w * 0.04
    gy = h * 0.22
    for r in range(n):
        for c in range(n):
            x = gx + c * cs
            y = gy + r * cs
            d.rounded_rectangle([x + cs * 0.08, y + cs * 0.08,
                                 x + cs * 0.92, y + cs * 0.92],
                                radius=cs * 0.18,
                                outline=hx(PURPLE), width=1)
    filled = [(0, 2), (1, 2), (2, 2), (0, 3), (2, 3), (4, 0), (4, 1), (5, 1), (6, 4), (6, 5), (6, 6), (3, 5)]
    for i, (c, r) in enumerate(filled):
        x = gx + c * cs
        y = gy + r * cs
        d.rounded_rectangle([x + cs * 0.12, y + cs * 0.12, x + cs * 0.88, y + cs * 0.88],
                            radius=cs * 0.18, fill=hx(PURPLE if i % 2 == 0 else BLUE))
    # clue bars on the left and top
    for r in range(n):
        bw = cs * 0.4
        d.rounded_rectangle([gx - cs * 0.62, gy + r * cs + cs * 0.32,
                             gx - cs * 0.22, gy + r * cs + cs * 0.68],
                            radius=cs * 0.1, fill=hx(ORANGE) if r % 3 else (110, 120, 175))
    for c in range(n):
        bh = cs * 0.4
        d.rounded_rectangle([gx + c * cs + cs * 0.32, gy - cs * 0.62,
                             gx + c * cs + cs * 0.68, gy - cs * 0.22],
                            radius=cs * 0.1, fill=hx(ORANGE) if c % 2 else (110, 120, 175))


SCENES = {
    "bubble-pop": scene_bubbles,
    "brick-breaker": scene_bricks,
    "minesweeper": scene_mines,
    "typing-test": scene_typing,
    "word-search": scene_wordsearch,
    "block-fit": scene_blockfit,
    "nonogram": scene_nonogram,
}
POST_TEXT = {"minesweeper": post_mines}
TITLES = {
    "bubble-pop": "Bubble Pop",
    "brick-breaker": "Brick Breaker",
    "minesweeper": "Minesweeper",
    "typing-test": "Typing Test",
    "word-search": "Word Search",
    "block-fit": "Block Fit",
    "nonogram": "Nonogram",
}


def load_fonts(w):
    try:
        bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(w * 0.085))
        reg = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(w * 0.032))
        small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(w * 0.026))
    except Exception:
        bold = ImageFont.load_default()
        reg = ImageFont.load_default()
        small = ImageFont.load_default()
    return bold, reg, small


def letterspaced(d, text, font, x, y, fill, spacing=4):
    cx = x
    for ch in text:
        d.text((cx, y), ch, font=font, fill=fill)
        cx += d.textlength(ch, font=font) + spacing


def render(slug, w, h):
    base = vgrad(w, h, "#241046", "#0c1330")
    bd = ImageDraw.Draw(base)
    stars(bd, w, h, max(40, int(w * 0.12)), seed=hash(slug) & 0xffff)

    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    SCENES[slug](gd, w, h)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=max(4, int(w * 0.014))))
    out = screen_blend(base, glow)

    d = ImageDraw.Draw(out)
    SCENES[slug](d, w, h)
    if slug in POST_TEXT:
        POST_TEXT[slug](d, w, h)

    bold, reg, small = load_fonts(w)
    letterspaced(d, "PRISM ARCADE", small, int(w * 0.05), int(h * 0.06),
                 (230, 230, 245), spacing=int(w * 0.004))
    tx = int(w * 0.05)
    ty = int(h * 0.74)
    d.text((tx, ty), TITLES[slug], font=bold, fill=(255, 255, 255))
    d.text((tx, ty + int(w * 0.092)), "Prism Arcade  -  Free & No Download",
           font=reg, fill=(214, 214, 236))
    return out


def main():
    for slug in SCENES:
        t = render(slug, 480, 270)
        tp = os.path.join(THUMB_DIR, f"{slug}.jpg")
        t.save(tp, "JPEG", quality=88)
        o = render(slug, 1200, 630)
        op = os.path.join(OG_DIR, f"{slug}.jpg")
        o.save(op, "JPEG", quality=88)
        print("wrote", tp, "and", op)


if __name__ == "__main__":
    main()
