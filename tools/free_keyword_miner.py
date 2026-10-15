#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Free Google Autocomplete keyword miner for the Prism Arcade site.

This script uses only the keyless Google Autocomplete endpoint and the
Google Trends RSS/CSV endpoints where available. It is suitable for
generating candidate long-tail queries. It does not provide exact
commercial KD values.

Usage:
  python free_keyword_miner.py --seed "snake game" --hl en --gl us --out tools/keyword-mine.json
"""

from __future__ import annotations
import argparse
import json
import urllib.parse
import urllib.request
import time
from pathlib import Path

BASE_AUTOCOMPLETE = "https://suggestqueries.google.com/complete/search"
MODIFIERS = [
    "", " a", " b", " c", " d", " e", " f", " g", " h", " i", " j", " k",
    "how to", "what is", "why", "which", "best", "free", "online", "for kids",
    "2 player", "no download", "unblocked", "browser",
]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; keyword-miner/0.1)"}


def fetch_json(url: str, timeout: int = 15) -> list:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, list) and len(payload) >= 2:
                return payload[1] or []
    except Exception:
        return []
    return []


def autocomplete(query: str, hl: str, gl: str) -> list:
    encoded = urllib.parse.quote(query)
    url = f"{BASE_AUTOCOMPLETE}?client=firefox&q={encoded}&hl={hl}&gl={gl}"
    return [item for item in fetch_json(url) if isinstance(item, str) and item.strip()]


def mine(seed: str, hl: str, gl: str) -> dict:
    found = {}
    for modifier in MODIFIERS:
        query = f"{seed} {modifier}".strip()
        suggestions = autocomplete(query, hl, gl)
        for suggestion in suggestions:
            key = suggestion.lower()
            if key not in found:
                found[key] = {
                    "keyword": suggestion,
                    "foundVia": query,
                    "modifiers": [m for m in MODIFIERS if m and f"{seed} {m}".strip().lower() in key],
                }
        time.sleep(0.12)

    rows = list(found.values())
    return {
        "seed": seed,
        "hl": hl,
        "gl": gl,
        "method": "google-autocomplete",
        "note": "Free, keyless source. Add Google Trends or a paid API later to estimate demand/KD.",
        "count": len(rows),
        "keywords": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True)
    parser.add_argument("--hl", default="en")
    parser.add_argument("--gl", default="us")
    parser.add_argument("--out", default="tools/keyword-mine.json")
    args = parser.parse_args()

    result = mine(args.seed, args.hl, args.gl)
    out_path = Path(__file__).parent / args.out
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Wrote {out_path.resolve()} with {result['count']} unique suggestions.")


if __name__ == "__main__":
    main()
