#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Keyword queue generator for the Prism Arcade site.
====================================================
This script maintains the manual "high-opportunity" keyword queue and
emits a clean JSON list of candidate new games to build.

It does NOT scrape Google or pull paid KD data (that requires a paid
keyword API such as Ahrefs / Semrush / DataForSEO). Instead it gives
you a repeatable, documented starting point you can score and expand
by hand. If you later plug in a paid API, replace the `seed` list and
the scoring step with live demand / KD values.

Usage:
  python keyword_queue.py

Output:
  tools/keyword-queue.json
"""

from __future__ import annotations
import json
from pathlib import Path

SEED_KEYWORDS = [
    # keyword, intent, demand (low/med/high), kd-proxy (low/med/high), reason
    ("number merge games online", "puzzle", "high", "low", "merge mechanic, simple, high intent"),
    ("reaction time test online", "reflex", "med", "low", "utility query, cheap to build"),
    ("sliding block puzzle no download", "puzzle", "med", "low", "long tail + no-download intent"),
    ("color sort puzzle online", "puzzle", "med", "med", "tube-sort mechanic, broad appeal"),
    ("quick tap reflex game", "reflex", "med", "med", "short arcade loop, easy to build"),
    ("2 player browser board games", "strategy", "high", "med", "multiplayer intent, two-player mode"),
    ("free html5 puzzle games no download", "puzzle", "high", "med", "broad but 'no download' qualifier lowers KD"),
]


def kd_score(demand: str, kd: str) -> float:
    """Higher = better opportunity (demand up, KD down)."""
    demand_score = {"low": 1, "med": 2, "high": 3}.get(demand, 1)
    kd_score = {"high": 1, "med": 2, "low": 3}.get(kd, 1)
    return round(demand_score * 10 + kd_score, 1)


def main() -> None:
    rows = []
    for kw, intent, demand, kd, reason in SEED_KEYWORDS:
        rows.append(
            {
                "keyword": kw,
                "intent": intent,
                "estimatedDemand": demand,
                "estimatedKD": kd,
                "opportunityScore": kd_score(demand, kd),
                "reason": reason,
            }
        )
    rows.sort(key=lambda r: r["opportunityScore"], reverse=True)
    out = {
        "note": "Seed queue. Re-score with a paid keyword API for live demand/KD before committing new game pages.",
        "keywords": rows,
    }
    p = Path(__file__).with_name("keyword-queue.json")
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Wrote {p.resolve()} with {len(rows)} candidates (top-first by opportunity).")


if __name__ == "__main__":
    main()
