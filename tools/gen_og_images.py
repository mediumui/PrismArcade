#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate placeholder OG images (1200x630) for Prism Arcade.

Creates:
  og/home.jpg
  og/about.jpg
  og/games/<slug>.jpg  (for each game in tools/seo_games_data.json)

Uses PIL to render a clean dark card with brand name, game name, and domain.
Requires Pillow. If Pillow is not installed, the script exits with a message.
"""

import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not found. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(2)

BASE = Path(__file__).resolve().parent
SITE_ROOT = BASE.parent
OG_DIR = SITE_ROOT / "og"
GAMES_DATA = BASE / "seo_games_data.json"

W, H = 1200, 630


def find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try a few common font locations; fall back to default."""
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/consolas.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_og(out_path: Path, lines: list[str], bg: tuple[int, int, int] = (17, 19, 27)):
    """
    Render a simple OG card.
    lines: list of text lines to stack vertically (centered).
    """
    img = Image.new("RGB", (W, H), color=bg)
    d = ImageDraw.Draw(img)

    # subtle top accent
    d.rectangle([0, 0, W, 8], fill=(124, 92, 255))

    font_main = find_font(56)
    font_sub = find_font(32)
    font_small = find_font(24)

    # title lines
    y = 120
    for i, text in enumerate(lines):
        font = font_main if i == 0 else font_sub
        bbox = d.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        color = (245, 245, 245) if i == 0 else (160, 165, 180)
        d.text((x, y), text, font=font, fill=color)
        y += 80 if i == 0 else 56

    # footer
    footer_font = find_font(28)
    footer = "Prism Arcade  •  www.prismarcade.top"
    bbox = d.textbbox((0, 0), footer, font=footer_font)
    fw = bbox[2] - bbox[0]
    d.text(((W - fw) // 2, H - 80), footer, font=footer_font, fill=(100, 105, 120))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=82, optimize=True)
    print(f"[OK] {out_path}")


def main():
    data = json.loads(GAMES_DATA.read_text(encoding="utf-8"))

    # home
    render_og(OG_DIR / "home.jpg", [
        "Prism Arcade",
        "18 Free Online Games — No Download",
    ])

    # about
    render_og(OG_DIR / "about.jpg", [
        "About Prism Arcade",
        "Built for fast play & global discovery",
    ])

    # games
    for slug, d in data.items():
        name = d.get("name", slug)
        tag = d.get("category", "Game")
        render_og(OG_DIR / "games" / slug.replace(".html", ".jpg"), [
            name,
            f"Free {tag} Online  •  No Download",
        ])

    print(f"Done. Generated {2 + len(data)} OG images in {OG_DIR}")


if __name__ == "__main__":
    main()
