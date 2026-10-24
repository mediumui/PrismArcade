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


SCENES = {
    "bubble-pop": scene_bubbles,
    "brick-breaker": scene_bricks,
    "minesweeper": scene_mines,
}
POST_TEXT = {"minesweeper": post_mines}
TITLES = {
    "bubble-pop": "Bubble Pop",
    "brick-breaker": "Brick Breaker",
    "minesweeper": "Minesweeper",
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
