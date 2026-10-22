#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redesign Prism Arcade OG / social share images (1200x630).

Each game's og image (og/games/<slug>.jpg) now EMBEDS the real gameplay
thumbnail (thumbs/<slug>.jpg) on the left — so the card shows actual game
art, not just text. The right side carries the brand, game name, category,
and a "Play Free" CTA, in the site's dark neon theme.

Layout (1200 x 630):
  - left panel  (~540px): gameplay screenshot in a rounded neon frame,
    with a soft glow + a small "category" chip
  - right panel (~560px): brand wordmark, big game title, one-line hook,
    "Play Free · No Download" CTA, and the domain

Regenerate all:
    C:/Users/.../Python312/python.exe tools/gen_og_images.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("Pillow not found. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(2)

BASE = Path(__file__).resolve().parent
SITE_ROOT = BASE.parent
OG_DIR = SITE_ROOT / "og"
THUMBS = SITE_ROOT / "thumbs"
GAMES_DATA = BASE / "seo_games_data.json"

W, H = 1200, 630

# brand palette (matches css vars)
BG = (16, 16, 36)            # --bg
PANEL = (22, 24, 48)         # --panel
PANEL2 = (29, 33, 64)        # --panel-2
INK = (247, 248, 255)       # --ink
MUTED = (183, 190, 221)      # --muted
ACCENT = (255, 179, 71)      # --accent (orange)
ACCENT2 = (124, 92, 255)     # --accent-2 (purple)

# schema.org category -> short human label for the chip
CATEGORY_LABEL = {
    "PuzzleGame": "Puzzle", "ActionGame": "Reflex", "BoardGame": "Board",
    "TriviaGame": "Trivia", "CardGame": "Card", "ArcadeGame": "Arcade",
    "PartyGame": "Party", "WordGame": "Word",
}


def find_font(size: int, bold: bool = False):
    """Pick a good-looking font; fall back to default."""
    cand = []
    if bold:
        cand = [
            "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    cand += [
        "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/SegoeUI.ttf",
        "C:/Windows/Fonts/consolas.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in cand:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def round_corners(im: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=radius, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im.convert("RGBA"), (0, 0), mask)
    return out


def fit_inside(img: Image.Image, tw: int, th: int) -> Image.Image:
    """Scale to FIT INSIDE the target box (contain, no crop) + optional pad.
    Preserves the full 16:9 gameplay frame instead of cover-cropping it."""
    iw, ih = img.size
    scale = min(tw / iw, th / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    return img.resize((nw, nh), Image.LANCZOS)


def make_neon_background() -> Image.Image:
    """Radial purple/orange glows on a dark base, like the site's body bg."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    # purple glow top-left, orange glow bottom-right (approx via stacked ellipses)
    for i in range(40):
        a = int(26 - i * 0.6)
        if a <= 0:
            break
        r0 = 220 + i * 9
        d.ellipse([60 - r0, 40 - r0, 60 + r0, 40 + r0], fill=(*ACCENT2, a // 2))
        r1 = 240 + i * 9
        d.ellipse([W - 220 - r1, H - 160 - r1, W - 220 + r1, H - 160 + r1],
                  fill=(*ACCENT, a // 4))
    return img.convert("RGB")


def draw_game_card(out: Path, name: str, label: str, thumb: Path, hook: str) -> None:
    canvas = make_neon_background()
    d = ImageDraw.Draw(canvas, "RGBA")

    # ---------------- left: gameplay screenshot in a neon frame ----------
    # thumb is native 16:9 (640x360 -> 480x270). Use a 16:9 box so the full
    # gameplay frame shows WITHOUT cover-cropping (which was cutting the
    # top/bottom of the art).
    Lw, Lh = 560, 315                      # 16:9
    Lx = 48
    Ly = (H - Lh) // 2                     # vertical-centre the 16:9 panel
    panel_img = Image.open(thumb).convert("RGB")
    frame = fit_inside(panel_img, Lw, Lh)  # contain -> full art, letterbox-free
    frame = round_corners(frame, 18)

    # pad the frame to exactly Lw x Lh with the site panel colour so the
    # border ring is a clean rectangle even if the art letterboxes
    pad = Image.new("RGBA", (Lw, Lh), (*PANEL2, 255))
    off_x, off_y = (Lw - frame.width) // 2, (Lh - frame.height) // 2
    pad.paste(frame, (off_x, off_y), frame)
    frame = pad

    # glow behind the frame (blurred copy)
    glow = frame.copy().filter(ImageFilter.GaussianBlur(24))
    glow.putalpha(120)
    canvas.paste(glow, (Lx - 6, Ly - 6), glow)
    canvas.paste(frame, (Lx, Ly), frame)

    # neon border ring
    ring = ImageDraw.Draw(canvas, "RGBA")
    ring.rounded_rectangle([Lx - 3, Ly - 3, Lx + Lw + 3, Ly + Lh + 3],
                           radius=22, outline=(*ACCENT2, 220), width=4)

    # category chip (top-left, over the screenshot)
    chip_font = find_font(26, bold=True)
    chip_txt = label.upper()
    bw = d.textbbox((0, 0), chip_txt, font=chip_font)
    chip_w = (bw[2] - bw[0]) + 36
    chip_h = 48
    cx, cy = Lx + 18, Ly + 18
    d.rounded_rectangle([cx, cy, cx + chip_w, cy + chip_h], radius=chip_h // 2,
                        fill=(*ACCENT, 235))
    d.text((cx + 18, cy + 8), chip_txt, font=chip_font, fill=(16, 16, 36))

    # "PRISM ARCADE" watermark top-right
    mark_font = find_font(20, bold=True)
    wm = "PRISM ARCADE"
    wmb = d.textbbox((0, 0), wm, font=mark_font)
    d.text((W - 32 - (wmb[2] - wmb[0]), 36), wm, font=mark_font,
           fill=(*MUTED, 150))

    # ---------------- right: text block ----------------
    rx = 650
    # small brand line
    d.text((rx, 150), "Prism Arcade", font=find_font(30, bold=True), fill=(*ACCENT,))

    # big game title (shrink to fit if long) — right column is 1200-650-32
    title_font = find_font(92, bold=True)
    title = name
    max_w = 518
    while d.textlength(title, font=title_font) > max_w and title_font.size > 40:
        title_font = find_font(title_font.size - 8, bold=True)
    d.text((rx, 190), title, font=title_font, fill=INK)

    # one-line hook (description, wrapped to 2 lines max)
    hook_font = find_font(30)
    words = hook.split()
    lines, cur = [], ""
    for w in words:
        if d.textlength(cur + " " + w, font=hook_font) <= 518:
            cur += (" " if cur else "") + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    lines = lines[:2]
    yy = 300
    for ln in lines:
        d.text((rx, yy), ln, font=hook_font, fill=MUTED)
        yy += 44

    # CTA pill
    cta_font = find_font(30, bold=True)
    cta = "Play Free  ·  No Download"
    cb = d.textbbox((0, 0), cta, font=cta_font)
    cw, ch = (cb[2] - cb[0]) + 56, 72
    cya = yy + 18
    d.rounded_rectangle([rx, cya, rx + cw, cya + ch], radius=ch // 2, fill=(*ACCENT,))
    d.text((rx + 28, cya + 14), cta, font=cta_font, fill=(27, 19, 11))

    # footer domain
    d.text((rx, H - 58), "www.prismarcade.top", font=find_font(24), fill=(*MUTED, 160))

    # accent divider line (top)
    d.rectangle([0, 0, W, 8], fill=(*ACCENT2,))

    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "JPEG", quality=85, optimize=True)
    print(f"[OK] {out.name}  ({name})")


def main() -> None:
    data = json.loads(GAMES_DATA.read_text(encoding="utf-8"))

    # ---- game cards: embed thumbs --------------------------------------
    for slug_file, d in data.items():
        slug = slug_file.replace(".html", "")
        name = d.get("name", slug)
        label = CATEGORY_LABEL.get(d.get("category", ""), "Game")
        thumb = THUMBS / f"{slug}.jpg"
        hook = d.get("desc", "")
        out = OG_DIR / "games" / f"{slug}.jpg"
        if not thumb.exists():
            print(f"[SKIP] {slug}: missing thumb {thumb}", file=sys.stderr)
            continue
        draw_game_card(out, name, label, thumb, hook)

    # ---- home: catalog thumb shows game variety ------------------------
    home_out = OG_DIR / "home.jpg"
    if (THUMBS / "_all-games.jpg").exists():
        draw_game_card(home_out, "22 Free Games", "Arcade",
                       THUMBS / "_all-games.jpg",
                       "Reflex, puzzle & brain games that load instantly in your browser.")
        print(f"[OK] home.jpg")

    # ---- about: clean brand card ---------------------------------------
    about_out = OG_DIR / "about.jpg"
    canvas = make_neon_background()
    d = ImageDraw.Draw(canvas, "RGBA")
    d.text((96, 220), "Prism Arcade", font=find_font(96, bold=True), fill=INK)
    d.text((96, 360), "A hand-crafted web arcade for players\nwho like instant play & clean screens.",
           font=find_font(34), fill=MUTED)
    d.text((96, H - 70), "www.prismarcade.top", font=find_font(26), fill=(*MUTED, 160))
    d.rectangle([0, 0, W, 8], fill=(*ACCENT2,))
    about_out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(about_out, "JPEG", quality=85, optimize=True)
    print(f"[OK] about.jpg")

    print(f"\nDone. Generated {len(data)} game OG cards + home + about in {OG_DIR}")


if __name__ == "__main__":
    main()
