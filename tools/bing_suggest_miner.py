#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real long-tail keyword miner for Prism Arcade (Bing Autocomplete).
===================================================================
No API key, no paid service. Uses the public Bing suggestion endpoint
(https://api.bing.com/osjson.aspx?query=...) which returns real
autocomplete phrases that searchers actually type.

Strategy
--------
1. Start from seed phrases (head terms of our niche).
2. Expand each seed with:
   - alphabet suffix  (seed + " a" .. "z")
   - question prefix  ("how to ", "what is ", "best ", "is ", "can i ")
   - intent suffix    ("no download", "unblocked", "free", "online", "for kids")
3. Dedupe, score, and cluster into game categories.

USAGE
-----
  python tools/bing_suggest_miner.py                # full run
  python tools/bing_suggest_miner.py --quick        # seeds + alphabet only
  python tools/bing_suggest_miner.py --out tools/x.csv

OUTPUT
------
  tools/longtail-keywords.csv   tier,keyword,words,hits,seeds,score,source
  tools/longtail-keywords.json  raw + cluster summary
"""
from __future__ import annotations

import argparse
import csv
import json
import gzip
import io
import string
import threading
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent import futures
from pathlib import Path

ENDPOINT = "https://api.bing.com/osjson.aspx"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# ---------------------------------------------------------------- seeds
SEEDS = [
    # generic intent (our money modifiers)
    "free online game",
    "browser game",
    "online game no download",
    "unblocked game",
    "html5 game",
    "play game online",
    "free game no download",
    "online puzzle game",
    "quick game online",
    # mechanics we already ship (find long-tail variants)
    "puzzle game",
    "memory game",
    "snake game",
    "sudoku",
    "2048 game",
    "number merge game",
    "word game",
    "sliding puzzle",
    "reaction test",
    "whack a mole game",
    "runner game",
    "tic tac toe",
    "connect 4",
    # mechanics we do NOT ship yet (expansion candidates)
    "solitaire",
    "mahjong",
    "chess",
    "checkers",
    "tetris",
    "jigsaw puzzle",
    "bubble shooter",
    "word search",
    "typing game",
    "darts game",
    "bowling game",
    "pinball",
    "plinko",
    "cookie clicker",
    "idle game",
    "tower defense",
    "platformer game",
    "car game",
    "fishing game",
    "basketball game",
    "pool game",
    "pong game",
    "breakout game",
    "minesweeper",
    "hangman",
    "quiz game",
    "trivia game",
    "color matching game",
    "match 3 game",
    "hidden object game",
    "escape room game",
    "uno card game",
    "domino game",
    "yahtzee",
    "bingo game",
    "spider solitaire",
    "freecell",
    "nonogram",
    "picross",
    "crossword puzzle",
    "wordle",
    "anagram game",
    "math game",
    "logic puzzle",
    "tangram",
    "rush hour puzzle",
    "parking puzzle",
    "merge game",
    "stack game",
    "balance game",
    "aim trainer",
    "typing test",
    "brain training game",
]

QUESTION_PREFIXES = ["how to play ", "what is a ", "best ", "can i play ", "is there a "]
INTENT_SUFFIXES = [
    "no download", "without download", "unblocked", "free", "online",
    "in browser", "for kids", "2 player", "html5",
]


def suggest(query: str, mkt: str = "en-us", retries: int = 2) -> list[str]:
    params = urllib.parse.urlencode({"query": query, "mkt": mkt})
    req = urllib.request.Request(f"{ENDPOINT}?{params}", headers={
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip",
    })
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                data = json.loads(raw.decode("utf-8", "replace"))
                if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                    return [str(x) for x in data[1]]
                return []
        except Exception:
            if attempt == retries:
                return []
            time.sleep(0.6 * (attempt + 1))
    return []


def fetch_all(queries: list[tuple[str, str]], workers: int = 8, pause: float = 0.0
              ) -> dict[str, set[str]]:
    """Query Bing autocomplete concurrently; ~8x faster than serial requests."""
    hits: dict[str, set[str]] = defaultdict(set)
    lock = threading.Lock()

    def work(item):
        q, seed = item
        got = suggest(q)
        if got:
            with lock:
                for s in got:
                    k = " ".join(s.lower().split())
                    if len(k) >= 6:
                        hits[k].add(seed)
        if pause:
            time.sleep(pause)

    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for i, _ in enumerate(pool.map(work, queries), 1):
            if i % 200 == 0:
                print(f"    ...{i}/{len(queries)}  unique={len(hits)}")
    return hits


def build_queries(quick: bool) -> list[tuple[str, str]]:
    """Return list of (query, seed_label)."""
    out: list[tuple[str, str]] = []
    for seed in SEEDS:
        out.append((seed, seed))
        if not quick:
            for p in QUESTION_PREFIXES:
                out.append((p + seed, seed))
        for ch in string.ascii_lowercase:
            out.append((f"{seed} {ch}", seed))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="longtail-keywords.csv")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--workers", type=int, default=8, help="parallel suggest requests")
    args = ap.parse_args()

    queries = build_queries(args.quick)
    print(f"[i] {len(queries)} queries to ask Bing autocomplete ({args.workers} workers) ...")
    hits = fetch_all(queries, workers=args.workers)

    INTENT_HINTS = ["no download", "without download", "unblocked", "free",
                    "online", "in browser", "for kids", "2 player",
                    "two player", "html5", "browser", "play"]

    rows = []
    for k, seeds in hits.items():
        words = len(k.split())
        n_intent = sum(1 for h in INTENT_HINTS if h in k)
        n_seeds = len(seeds)
        # score: long-tail-ness (words) + intent modifiers + corroboration
        score = round(min(words, 8) * 6 + n_intent * 7 + n_seeds * 3, 1)
        tier = "A" if score >= 60 else "B" if score >= 45 else "C"
        rows.append({
            "tier": tier, "keyword": k, "words": words, "intent_hits": n_intent,
            "seed_hits": n_seeds, "score": score, "source": "bing-autocomplete",
            "seeds": "|".join(sorted(seeds)),
        })
    rows.sort(key=lambda r: (r["score"], r["words"]), reverse=True)

    out_csv = Path(__file__).parent / args.out
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["tier", "keyword", "words", "intent_hits", "seed_hits", "score", "source"])
        for r in rows:
            w.writerow([r["tier"], r["keyword"], r["words"], r["intent_hits"],
                        r["seed_hits"], r["score"], r["source"]])

    out_json = out_csv.with_suffix(".json")
    out_json.write_text(json.dumps({
        "generatedAt": time.strftime("%Y-%m-%d"),
        "method": "Bing autocomplete (api.bing.com/osjson.aspx), live network",
        "queryCount": len(queries),
        "uniqueKeywords": len(rows),
        "keywords": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[ok] {len(rows)} unique long-tail keywords")
    print(f"     csv : {out_csv}")
    print(f"     json: {out_json}")
    print("\nTop 40:")
    for r in rows[:40]:
        print(f"  [{r['tier']}] {r['keyword']:<52} score={r['score']:>6} "
              f"words={r['words']} intent={r['intent_hits']} seeds={r['seed_hits']}")


if __name__ == "__main__":
    main()
