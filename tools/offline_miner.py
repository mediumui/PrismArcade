#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Offline long-tail keyword generator for the Prism Arcade site.
================================================================
No API and no network needed. Synthesizes candidate search queries by
combining the 17 game mechanics we ship with audience and modifier
phrases, then scores each candidate on the same three axes as
kwinside_miner.py (volume proxy, specificity, competition), so the output
is directly usable for deciding which new game pages to build.

Because we have no live search volume, `volume` is a deterministic
relevance proxy (demand tier 1..3) rather than a true Google figure. The
`source` column is "synthetic" so it is never mistaken for live data.

USAGE:
  python offline_miner.py --out tools/top-keywords.csv
  python offline_miner.py --out tools/top-keywords.csv --top 200

OUTPUT columns:
  tier, keyword, volume, words, intent_hits, opportunity, source
"""

from __future__ import annotations
import argparse
import csv
from pathlib import Path

# (label, demand_proxy)
# demand_proxy is a 1..3 relevance tier: 3 = strong evergreen intent,
# 1 = weaker / more speculative. It is NOT a real search volume.
BASE_MECHANICS: list[tuple[str, int]] = [
    ("2048 game", 3),
    ("number merge game", 3),
    ("word merge game", 2),
    ("sliding puzzle game", 3),
    ("sliding block puzzle", 3),
    ("sudoku game", 3),
    ("memory match game", 3),
    ("sequence memory game", 2),
    ("pattern memory game", 2),
    ("flappy bird game", 3),
    ("endless runner game", 3),
    ("jump runner game", 3),
    ("snake game", 3),
    ("whack a mole game", 3),
    ("reaction time test", 3),
    ("reflex tap game", 2),
    ("quick tap game", 2),
    ("connect four game", 3),
    ("tic tac toe game", 3),
]

MODIFIERS: list[tuple[str, int]] = [
    ("", 0),
    ("online", 3),
    ("free", 2),
    ("no download", 3),
    ("without download", 2),
    ("unblocked", 2),
    ("html5", 2),
    ("browser", 2),
    ("for kids", 2),
    ("for adults", 1),
    ("2 player", 2),
    ("two player", 2),
    ("solo", 1),
    ("for school", 1),
]

INTENT_HINTS = [
    "no download", "without download", "free", "online", "unblocked",
    "html5", "browser", "solo", "2 player", "two player", "for kids",
    "for adults", "for school",
]


def build_candidates() -> list[dict]:
    rows = []
    seen = set()
    for mech, mech_tier in BASE_MECHANICS:
        for mod, mod_tier in MODIFIERS:
            kw = (f"{mech} {mod}".strip()) if mod else mech
            kw = " ".join(kw.split())
            if kw in seen:
                continue
            seen.add(kw)

            lower = kw.lower()
            words = len(lower.split())
            has_intent = sum(1 for h in INTENT_HINTS if h in lower)
            demand = mech_tier + min(mod_tier, 2)

            vol_score = demand * 8.0
            spec_score = min(words, 5) * 4.0 + has_intent * 6.0
            # pure single-mechanic with no modifier is treated as a head
            # term (higher expected KD)
            comp_penalty = 14.0 if (mod_tier == 0 and words <= 2) else 0.0
            opp = round(vol_score + spec_score - comp_penalty, 1)
            tier = "A" if opp >= 38 else "B" if opp >= 30 else "C"

            rows.append({
                "keyword": kw,
                "volume": demand,          # proxy, NOT a real volume
                "words": words,
                "intent_hits": has_intent,
                "opportunity": opp,
                "tier": tier,
                "source": "synthetic",
            })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Offline long-tail keyword generator")
    ap.add_argument("--out", default="top-keywords.csv")
    ap.add_argument("--top", type=int, default=200, help="Max rows to keep (top by opportunity)")
    args = ap.parse_args()

    rows = build_candidates()
    ranked = sorted(rows, key=lambda r: (r["opportunity"], r["volume"]), reverse=True)
    ranked = ranked[: args.top]

    out_path = Path(__file__).parent / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["tier", "keyword", "volume", "words", "intent_hits", "opportunity", "source"])
        for r in ranked:
            w.writerow([r["tier"], r["keyword"], r["volume"], r["words"], r["intent_hits"], r["opportunity"], r["source"]])

    print(f"Wrote {out_path.resolve()} with {len(ranked)} ranked candidates (synthetic, no live volume).")
    print(f"\nTop 20 by opportunity score:")
    for r in ranked[:20]:
        print(f"  [{r['tier']}] {r['keyword']:<44} opp={r['opportunity']:>5}  (vol-proxy {r['volume']})")


if __name__ == "__main__":
    main()
