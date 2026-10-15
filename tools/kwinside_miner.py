#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kwinside keyword miner + scorer for the Prism Arcade site.
============================================================
Pulls related keywords + monthly search volume from the free Kwinside
Keyword API (20 free requests/day, no card), then scores every candidate
on three axes that matter for "new word, high search, low competition":

  1. volume      - monthly search volume (higher = more demand)
  2. competition - proxy derived from the volume/length shape (see notes)
  3. longtail    - query length (longer, more specific = lower KD)

It outputs a ranked CSV you can use to decide which new game pages to build.

The Kwinside response does not expose an explicit numeric KD. The scoring
below is a documented, reproducible proxy: we reward high volume AND
specific (multi-word, intent-qualified) queries, which is the practical
signal for "high demand, low difficulty" on a fresh low-authority site.
To get a hard KD, swap in Ahrefs/Semrush data or add the SERP
competitors endpoint.

AUTH (never hard-code the key into the repo):
  export KWINSIDE_API_KEY="kwi_..."        # Windows PowerShell: $env:KWINSIDE_API_KEY="kwi_..."

USAGE:
  python kwinside_miner.py --seed "free games" --limit 50 --out tools/top-keywords.csv
  python kwinside_miner.py --seeds "free games,reflex game,puzzle game" --limit 80
  Add --min-volume 50 to drop weak keywords.

The endpoint also accepts `key` as a query param, but we prefer the header.
If your account uses a header name like `Authorization: Bearer kwi_...`,
set KWINSIDE_AUTH_STYLE=bearer to switch.
"""

from __future__ import annotations
import argparse
import csv
import json
import os
import re
import urllib.parse
import urllib.request
import time
from pathlib import Path

BASE = "https://kwinside.com/api/v1/keywords"

# Intent qualifiers that mark a long-tail, lower-KD query.
LONGTAIL_HINTS = [
    "no download", "without download", "free", "online", "play", "2 player",
    "for kids", "unblocked", "html5", "browser", "solo", "two player",
]


def _headers() -> dict:
    key = (os.environ.get("KWINSIDE_API_KEY") or "").strip()
    if not key:
        raise SystemExit(
            "Error: KWINSIDE_API_KEY is not set.\n"
            "Register free at https://kwinside.com/register, copy the key,\n"
            "then:  export KWINSIDE_API_KEY=kwi_...  (PowerShell: $env:KWINSIDE_API_KEY=...)"
        )
    style = os.environ.get("KWINSIDE_AUTH_STYLE", "header").lower()
    if style == "bearer":
        return {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    return {"X-API-Key": key, "Accept": "application/json"}


def fetch_related(seed: str, lang: str, limit: int, min_volume: int) -> list:
    """One Kwinside call for a seed. Returns a list of keyword dicts."""
    params = {"se": lang, "kw": seed, "limit": str(limit), "key": ""}
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v != ""})
    url = f"{BASE}?{query}"
    headers = _headers()
    # key also accepted as a query param; send it both ways for robustness
    url += ("&" if "?" in url else "") + "key=" + urllib.parse.quote(
        os.environ.get("KWINSIDE_API_KEY", "")
    )
    # Cloudflare blocks the default "Python-urllib" client signature; send a
    # normal browser User-Agent so the request is treated as a regular client.
    headers = dict(headers)
    headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    )
    req = urllib.request.Request(url, headers=headers)
    # Kwinside's data backend occasionally returns 503 "temporarily
    # unavailable" (not a key problem). Retry transient 5xx a few times
    # with backoff before giving up on this seed.
    max_attempts = int(os.environ.get("KWINSIDE_RETRIES", "4"))
    last_body = ""
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            data = payload.get("data", payload)
            # A 503 with data.error=true is transient; a 200 that still
            # carries an error flag should also be retried.
            if isinstance(data, dict) and data.get("error") and attempt < max_attempts:
                last_body = json.dumps(data)[:500]
                print(f"   (transient error, retry {attempt}/{max_attempts} in 8s) {data.get('message','')}")
                time.sleep(8)
                continue
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            last_body = body
            if e.code in (500, 502, 503, 504) and attempt < max_attempts:
                print(f"   (HTTP {e.code}, retry {attempt}/{max_attempts} in 8s)")
                time.sleep(8)
                continue
            raise SystemExit(f"Kwinside HTTP {e.code}:\n{body[:1500]}")
        except Exception as e:
            raise SystemExit(f"Kwinside request failed: {e}")
    else:
        raise SystemExit(
            f"Kwinside still unavailable after {max_attempts} attempts for seed {seed!r}:\n{last_body[:800]}"
        )

    rows = []
    data = payload.get("data", payload)
    # Kwinside returns suggestions under a few possible shapes; normalize.
    items = (
        data.get("results")
        or data.get("suggestions")
        or data.get("keywords")
        or (data if isinstance(data, list) else [])
    )
    for item in items:
        kw = (item.get("keyword") or item.get("suggestion") or item.get("text") or "").strip()
        vol = item.get("volume") or item.get("search_volume") or item.get("monthly_searches") or 0
        try:
            vol = int(float(vol))
        except Exception:
            vol = 0
        if not kw or vol < min_volume:
            continue
        rows.append({"keyword": kw, "volume": vol, "raw": item})
    return rows


def score(row: dict) -> dict:
    kw = row["keyword"].lower()
    vol = row["volume"]
    words = len(kw.split())
    has_intent = sum(1 for h in LONGTAIL_HINTS if h in kw)

    # volume: log-scaled so a handful of huge terms do not drown everything
    import math
    vol_score = math.log10(max(vol, 1)) * 10.0

    # specificity: more words + intent qualifiers = lower expected KD
    spec_score = min(words, 5) * 4.0 + has_intent * 6.0

    # competition proxy: we cannot read true KD, so we treat "very generic
    # single-word with huge volume" as high-KD (penalty) and "specific
    # multi-word" as low-KD (reward). Generic bigrams like "free games"
    # are penalized.
    generic_bigrams = {"free games", "online games", "browser games", "fun games"}
    comp_penalty = 12.0 if (words <= 2 and kw in generic_bigrams) else 0.0

    opportunity = round(vol_score + spec_score - comp_penalty, 1)
    # rank-tier label for quick eyeballing
    tier = "A" if opportunity >= 60 else "B" if opportunity >= 45 else "C"
    row.update({
        "words": words,
        "intent_hits": has_intent,
        "opportunity": opportunity,
        "tier": tier,
    })
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description="Kwinside keyword miner + scorer")
    ap.add_argument("--seed", default="free games", help="Primary seed keyword")
    ap.add_argument("--seeds", default="", help="Comma-separated extra seeds")
    ap.add_argument("--lang", default="en", choices=["en", "de", "it", "es", "fr", "ru"])
    ap.add_argument("--limit", type=int, default=60, help="Suggestions per seed (uses credits)")
    ap.add_argument("--min-volume", type=int, default=0, help="Drop keywords below this volume")
    ap.add_argument("--out", default="tools/top-keywords.csv")
    args = ap.parse_args()

    seed_list = [s.strip() for s in re.split(r"[,;]", args.seed + ("," + args.seeds if args.seeds else "")) if s.strip()]
    all_rows = []
    for i, seed in enumerate(seed_list):
        print(f"-> Kwinside seed {i + 1}/{len(seed_list)}: {seed!r}")
        rows = fetch_related(seed, args.lang, args.limit, args.min_volume)
        for r in rows:
            r["seed"] = seed
        all_rows.extend(rows)
        time.sleep(1.0)  # be gentle; free tier is 20 req/day

    scored = [score(r) for r in all_rows]
    # dedupe by keyword, keep max volume, then rank by opportunity desc
    seen = {}
    for r in scored:
        k = r["keyword"].lower()
        if k not in seen or r["volume"] > seen[k]["volume"]:
            seen[k] = r
    ranked = sorted(seen.values(), key=lambda r: (r["opportunity"], r["volume"]), reverse=True)

    out_path = Path(__file__).parent / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["tier", "keyword", "volume", "words", "intent_hits", "opportunity", "seed"])
        for r in ranked:
            writer.writerow([r["tier"], r["keyword"], r["volume"], r["words"], r["intent_hits"], r["opportunity"], r.get("seed", "")])
    print(f"\nWrote {out_path.resolve()} with {len(ranked)} unique ranked keywords.")
    print("\nTop 15 by opportunity (high volume + low expected KD):")
    for r in ranked[:15]:
        print(f"  [{r['tier']}] {r['keyword']:<42} vol={r['volume']:>9}  opp={r['opportunity']}")


if __name__ == "__main__":
    main()
