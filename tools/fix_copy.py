#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply the remaining copy fixes: over-long <title>, over-long meta
descriptions, and weak <h1> text lacking category keywords.

Every replacement is an explicit old -> new pair (no regex guessing). The same
string is usually present in meta description, og:description and JSON-LD, so
all occurrences are replaced together to keep them consistent.
"""
import os, sys, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APPLY = "--apply" in sys.argv

TITLES = [
    ("games/bubble-pop.html",
     "Play Bubble Pop — Bubble Shooter Game Online No Download | Prism Arcade",
     "Play Bubble Pop — Bubble Shooter Online No Download | Prism Arcade"),
    ("games/color-sort.html",
     "Play Color Sort Puzzle Online No Download - Free Brain Teaser | Prism Arcade",
     "Color Sort Puzzle Online No Download - Brain Teaser | Prism Arcade"),
    ("games/reaction-test.html",
     "Reaction Time Test Online No Download - Reflex Benchmark | Prism Arcade",
     "Reaction Time Test Online No Download - Reflex Test | Prism Arcade"),
    ("games/stack-tower.html",
     "Play Stack Tower Online No Download - Block Stacking Game | Prism Arcade",
     "Play Stack Tower Online No Download - Stacking Game | Prism Arcade"),
]

H1 = [
    ("games/2048.html", "2048", "Play 2048 Online — Free Merge Puzzle Game"),
    ("games/maze.html", "Maze", "Play Maze Online — Free Random Maze Puzzle"),
    ("games/hangman.html", "Hangman", "Play Hangman Online — Free Word Guessing Game"),
    ("games/flappy.html", "Sky Flap", "Play Sky Flap Online — Free Reflex Game"),
    ("games/bubble-pop.html", "Bubble Pop", "Play Bubble Pop Online — Free Bubble Shooter"),
    ("games/quiz.html", "Brain Quiz", "Play Brain Quiz Online — Free Quiz Game"),
    ("games/snake.html", "Neon Snake", "Play Neon Snake Online — Free Reflex Game"),
    ("games/runner.html", "Jump Runner", "Play Jump Runner Online — Free Endless Runner"),
    ("games/stack-tower.html", "Stack Tower", "Play Stack Tower Online — Free Stacking Game"),
    ("games/sudoku.html", "Easy Sudoku", "Play Easy 4x4 Sudoku Online — Free Logic Puzzle"),
    ("games/tic-tac-toe.html", "Tic Tac Toe", "Play Tic Tac Toe Online — Free 2-Player Game"),
    ("games/whack.html", "Whack-a-Dot", "Play Whack-a-Dot Online — Free Reflex Game"),
    ("games/minesweeper.html", "Minesweeper", "Play Minesweeper Online — Free Logic Puzzle"),
    ("games/word-merge.html", "Word Merge", "Play Word Merge Online — Free Word Puzzle"),
    ("contact.html", "Contact Us", "Contact Prism Arcade"),
]

DESCS = [
    ("games.html",
     "Browse all 25 free online games on Prism Arcade — reflex, puzzle, strategy, and memory games with no download and no sign-up. Paginated catalog with filters by game type.",
     "Browse all 25 free online games on Prism Arcade — reflex, puzzle, strategy, and memory games with no download and no sign-up. Filter by game type."),
    ("privacy.html",
     "How Prism Arcade handles your data: no accounts, no personal data required to play, and how third-party advertising (Google AdSense) cookies work, plus your GDPR and CCPA rights.",
     "How Prism Arcade handles your data: no accounts, no personal data required to play, how Google AdSense cookies work, and your GDPR and CCPA rights."),
    ("games/block-slide.html",
     "Play Block Slide Puzzle online with no download. Slide blocks into the open space, clear the green targets, and finish each level with fewer moves. Free, one-screen logic game.",
     "Play Block Slide Puzzle online with no download. Slide blocks into the open space, clear the green targets, and finish each level with fewer moves."),
    ("games/color-sort.html",
     "Play Color Sort Puzzle online for free with no download. Pour colored balls between tubes until each tube holds one color. A calm, always-solvable logic puzzle for quick brain breaks.",
     "Play Color Sort Puzzle online for free with no download. Pour colored balls between tubes until each tube holds one color. A calm, always-solvable logic puzzle."),
    ("games/connect4.html",
     "Play Connect 4 online for two players with no download. Drop discs, build four-in-a-row lines, and win with tactical board strategy. Free, local two-player arcade game.",
     "Play Connect 4 online for two players with no download. Drop discs, build four-in-a-row lines, and win with tactical board strategy."),
    ("games/hangman.html",
     "Play Hangman online for free with no download. Guess hidden words across Animals, Fruits, Countries and General categories. A classic word game that builds vocabulary.",
     "Play Hangman online for free with no download. Guess hidden words across Animals, Fruits, Countries and General categories."),
    ("games/maze.html",
     "Play Maze online for free with no download. Solve a fresh random maze every time, from small to large, and race the clock to the exit with arrow keys, swipe, or a click.",
     "Play Maze online for free with no download. Solve a fresh random maze every time, from small to large, and race the clock to the exit."),
    ("games/number-merge.html",
     "Play Number Merge online with no download. Tap one tile then tap an equal tile to combine them, build the highest total score, and chase your best run. Free merge puzzle.",
     "Play Number Merge online with no download. Tap one tile then tap an equal tile to combine them, build the highest total score, and chase your best run."),
    ("games/stack-tower.html",
     "Play Stack Tower online for free with no download. Drop sliding blocks to build the tallest tower, trim the overhang, and chase a new best height in quick one-tap rounds.",
     "Play Stack Tower online for free with no download. Drop sliding blocks to build the tallest tower, trim the overhang, and chase a new best height."),
]

problems = []
def apply(group, wrap=None):
    for rel, old, new in group:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            problems.append("missing file " + rel)
            continue
        s = open(p, encoding="utf-8", newline="").read()
        if old not in s:
            problems.append("pattern not found in %s: %s" % (rel, old[:60]))
            continue
        n = s.count(old)
        target = wrap(old) if wrap else old
        target_new = wrap(new) if wrap else new
        if wrap:
            if target not in s:
                problems.append("wrapped pattern not found in %s" % rel)
                continue
            s = s.replace(target, target_new)
        else:
            s = s.replace(target, target_new)
        if APPLY:
            open(p, "w", encoding="utf-8", newline="").write(s)
        print("  %-26s %d occurrence(s)  %d -> %d chars" % (rel, n, len(old), len(new)))

def h1wrap(text):
    return None

print("TITLES" + ("" if APPLY else " (dry run)"))
for rel, old, new in TITLES:
    p = os.path.join(ROOT, rel)
    s = open(p, encoding="utf-8", newline="").read()
    if "<title>" + old + "</title>" not in s:
        problems.append("title not found in %s" % rel)
        continue
    if APPLY:
        s = s.replace("<title>" + old + "</title>", "<title>" + new + "</title>")
        open(p, "w", encoding="utf-8", newline="").write(s)
    print("  %-26s %d -> %d chars" % (rel, len(old), len(new)))

print("\nH1" + ("" if APPLY else " (dry run)"))
for rel, old, new in H1:
    p = os.path.join(ROOT, rel)
    s = open(p, encoding="utf-8", newline="").read()
    m = re.search(r"(<h1[^>]*>)" + re.escape(old) + r"(</h1>)", s)
    if not m:
        problems.append("h1 not found in %s: %s" % (rel, old))
        continue
    if APPLY:
        s = s[:m.start()] + m.group(1) + new + m.group(2) + s[m.end():]
        open(p, "w", encoding="utf-8", newline="").write(s)
    print("  %-26s %d -> %d chars" % (rel, len(old), len(new)))

print("\nDESCRIPTIONS" + ("" if APPLY else " (dry run)"))
apply(DESCS)

print("\nproblems:", len(problems))
for p in problems:
    print("   ", p)
