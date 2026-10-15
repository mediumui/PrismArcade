#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vidshell Image Generation Client
================================

Usage:
  python vidshell_image_gen.py --vk <your_vk_token> --prompt "short prompt"
  python vidshell_image_gen.py --vk <your_vk_token> --prompt "..." --size 1024x768 --out ./img

Notes:
- The gateway is OpenAI-compatible: base_url = https://aytrim.top/vidshell/v1
- Authentication: Authorization: Bearer vk_xxx
- The client model value is ignored by the server; the response model is rewritten to the public name vidshell-images-1.0
- Provide the token through the VIDSHELL_VK environment variable. Never hard-code secrets in files or version control:
      export VIDSHELL_VK="vk_..."      # Windows PowerShell: $env:VIDSHELL_VK="vk_..."

Dependencies: httpx only.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

BASE = "https://aytrim.top/vidshell"
GENERATE_URL = f"{BASE}/v1/images/generations"
# Match the gateway default 180s read timeout. Use a separate 15s connect timeout.
CONNECT_TIMEOUT = 15.0
READ_TIMEOUT = 180.0


def _resolve_vk(explicit: str) -> str:
    """Prefer the --vk argument, then the VIDSHELL_VK environment variable."""
    tok = (explicit or os.environ.get("VIDSHELL_VK", "")).strip()
    if not tok:
        print("Error: no vk token provided.", file=sys.stderr)
        print("  Option 1: python vidshell_image_gen.py --vk vk_xxx ...", file=sys.stderr)
        print("  Option 2: export VIDSHELL_VK=vk_xxx, then omit --vk", file=sys.stderr)
        sys.exit(2)
    return tok


def generate(vk: str, prompt: str, size: str = "1024x1024") -> dict:
    """Call the image endpoint and return the raw JSON response."""
    payload = {
        "model": "vidshell-images-1.0",   # Ignored by the server; any value is accepted.
        "prompt": prompt,
        "n": 1,                            # Currently only n=1 is supported.
        "size": size,
    }
    with httpx.Client(timeout=httpx.Timeout(READ_TIMEOUT, connect=CONNECT_TIMEOUT)) as client:
        resp = client.post(
            GENERATE_URL,
            headers={"Authorization": f"Bearer {vk}"},
            json=payload,
        )
    if resp.status_code >= 400:
        print(f"[HTTP {resp.status_code}] Image generation failed:\n{resp.text[:1000]}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def save_result(data: dict, out_dir: str) -> Path:
    """Save the returned image locally. Prefer URL download, then b64_json decoding."""
    item = (data.get("data") or [{}])[0]
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if item.get("b64_json"):
        p = out_path / f"vidshell_image_{stamp}.png"
        p.write_bytes(base64.b64decode(item["b64_json"]))
        return p
    if item.get("url"):
        p = out_path / f"vidshell_image_{stamp}.png"
        with httpx.Client(timeout=READ_TIMEOUT, follow_redirects=True) as client:
            img = client.get(item["url"]).content
        p.write_bytes(img)
        return p
    raise RuntimeError("Response contains neither b64_json nor url; unable to save image:\n" + str(data)[:500])


def main() -> None:
    ap = argparse.ArgumentParser(description="Vidshell image generation client")
    ap.add_argument("--vk", default="", help="Vidshell gateway token (or set the VIDSHELL_VK environment variable)")
    ap.add_argument("--prompt", required=True, help="Image prompt")
    ap.add_argument("--size", default="1024x1024", help="Output size, default 1024x1024")
    ap.add_argument("--out", default="./vidshell_images", help="Output directory for saved images")
    ap.add_argument("--json", action="store_true", help="Print the full response JSON (default prints only the saved file path)")
    args = ap.parse_args()

    vk = _resolve_vk(args.vk)
    print(f"-> POST {GENERATE_URL}  size={args.size}")
    data = generate(vk, args.prompt, args.size)
    if args.json:
        print(_pretty(data))
    p = save_result(data, args.out)
    print(f"[OK] Saved: {p.resolve()}")


def _pretty(d) -> str:
    import json
    return json.dumps(d, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
