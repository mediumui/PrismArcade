#!/usr/bin/env python3
"""GEO pass: add a visible 'How to Play' section to every Prism Arcade game page.

Why a separate pass:
- Game pages already have SEO:INJECTED v1 / SEO:CLEANED v2 markers (overview + FAQ + related).
- This adds the *gameplay steps* that the GEO audit scope asked for, in its own
  idempotent block so it never collides with seo_inject / seo_clean pipelines.

Output: inserts a `<section class="container seo-howto">` right BEFORE the existing
`seo-faq` section on each page. Skips pages that already contain the GEO:HOWTO marker.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GAMES_DIR = BASE / "games"
DATA = json.loads((BASE / "tools" / "seo_games_data.json").read_text(encoding="utf-8"))
MARKER = "<!-- GEO:HOWTO v1 -->"

HOWTO = {
    "tic-tac-toe.html": [
        "Take turns with your opponent placing your symbol (X or O) in any empty square.",
        "Try to line up three of your symbols in a row, a column, or a diagonal.",
        "Block your opponent from completing a line while building your own.",
        "The first player to get three in a row wins; a full board with no line is a draw.",
    ],
    "snake.html": [
        "Use the arrow keys on desktop or the on-screen buttons on mobile to steer the snake.",
        "Collect the glowing energy nodes to grow longer and raise your score.",
        "Avoid running into the walls or into your own body.",
        "Survive as long as you can — the snake speeds up with every point you collect.",
    ],
    "memory.html": [
        "Flip any two cards to reveal the symbols underneath.",
        "If the two symbols match, they stay face-up; if not, they flip back down.",
        "Remember where each symbol is to make faster matches.",
        "Clear the whole board in as few moves as possible.",
    ],
    "quick-tap.html": [
        "Watch for glowing targets to appear on the grid.",
        "Tap each target before it disappears.",
        "Hit targets back-to-back to build a streak.",
        "Score as many points as you can in the 30-second round.",
    ],
    "connect4.html": [
        "Take turns dropping a disc into any column.",
        "The disc falls to the lowest empty spot in that column.",
        "Line up four of your discs in a row, column, or diagonal.",
        "The first player to connect four wins the round.",
    ],
    "whack.html": [
        "Dots pop up at random spots across the play area.",
        "Tap or click each dot as quickly as it appears.",
        "Keep your accuracy high by not missing too many.",
        "Chase the highest score before the timer runs out.",
    ],
    "number-merge.html": [
        "Tap one tile, then tap an equal-value tile to merge them.",
        "Merged tiles combine into a higher value.",
        "Plan your taps to build the biggest combined total.",
        "Keep merging to beat your best score.",
    ],
    "reaction-test.html": [
        "Wait for the screen to turn green.",
        "As soon as it does, tap or click as fast as you can.",
        "Your time is recorded in milliseconds after each round.",
        "Repeat to find your fastest, most consistent reaction.",
    ],
    "block-slide.html": [
        "Slide blocks into the single open space to rearrange them.",
        "Clear every green target by moving a block onto it.",
        "Plan moves ahead to finish with fewer steps.",
        "Complete the level once all targets are cleared.",
    ],
    "flappy.html": [
        "Tap or click to make the bird flap upward.",
        "Release to let gravity pull it back down.",
        "Guide the bird through the gaps between the pipes.",
        "Travel as far as you can without hitting a pipe.",
    ],
    "word-merge.html": [
        "Drag letters and smaller words into the bin.",
        "Combine them to form longer, valid words.",
        "Longer words unlock bonus points.",
        "Clear the pool to level up and keep the chain going.",
    ],
    "sudoku.html": [
        "Fill the 4x4 grid with the numbers 1 to 4.",
        "Each row, column, and 2x2 box must contain 1 to 4 exactly once.",
        "Use the given clues to deduce the empty cells.",
        "Complete the grid with no repeats to finish.",
    ],
    "quiz.html": [
        "Read each question and choose the best answer.",
        "Get instant feedback after every pick.",
        "A mix of topics keeps each round varied.",
        "Replay to improve your score and reaction.",
    ],
    "reflex-relay.html": [
        "Watch the pads light up in a sequence.",
        "Repeat the sequence by tapping the pads in the same order.",
        "Each round adds one more step to remember.",
        "Keep the combo alive as the sequence speeds up.",
    ],
    "sliding-number.html": [
        "Slide the numbered tiles into the open space.",
        "Arrange them in order from 1 to 8.",
        "Plan your moves to avoid trapping a tile.",
        "Solve the grid in as few moves as you can.",
    ],
    "sequence.html": [
        "Watch the light sequence play out.",
        "Repeat it back by tapping the matching pads.",
        "Each round adds one more step.",
        "Push your memory as the pattern grows longer.",
    ],
    "2048.html": [
        "Use the arrow keys or swipes to slide all tiles in one direction.",
        "Equal tiles that collide merge into their sum.",
        "Plan moves to keep the board open and build big numbers.",
        "Reach the 2048 tile to win, or chase a higher score.",
    ],
    "runner.html": [
        "Tap or click to make your runner jump.",
        "Clear obstacles and gaps in your path.",
        "Time your jumps to keep your momentum.",
        "Travel the farthest distance you can without crashing.",
    ],
    "color-sort.html": [
        "Tap a tube to pick up the top balls from it.",
        "Tap another tube to pour them in.",
        "You can only pour onto an empty tube or a tube whose top color matches.",
        "Sort every color into its own tube, using Undo if you get stuck.",
    ],
    "stack-tower.html": [
        "Watch the block slide back and forth above your tower.",
        "Tap, click, or press Space to drop it onto the tower.",
        "Line it up cleanly so no part overhangs and gets sliced away.",
        "Five clean drops in a row rebuild your width — chase the tallest tower.",
    ],
    "hangman.html": [
        "Pick a word category such as Animals, Fruits, Countries, or General.",
        "Tap a letter or press a key to guess it.",
        "Correct letters fill in the hidden word; wrong letters add to the gallows.",
        "Reveal the whole word before six wrong guesses to win.",
    ],
    "maze.html": [
        "Move the orange dot from the top-left corner toward the green exit.",
        "Use arrow keys or WASD on desktop, or swipe on mobile.",
        "Each maze is random, so find the route before you run out of time.",
        "Tap Show Path to reveal the shortest route to the exit.",
    ],
}


def build(slug: str) -> str:
    d = DATA[slug]
    name = d["name"]
    steps = HOWTO[slug]
    items = "\n".join(f"          <li><strong>{i}.</strong> {s}</li>" for i, s in enumerate(steps, 1))
    return (
        f"      {MARKER}\n"
        f'      <section class="container seo-howto" aria-label="How to play">\n'
        f'        <div class="section-title"><div><h2>How to Play</h2>'
        f'<p>Quick steps to start {name} on Prism Arcade.</p></div></div>\n'
        f'        <ul class="list">\n{items}\n        </ul>\n'
        f"      </section>"
    )


def process(slug: str) -> None:
    p = GAMES_DIR / slug
    text = p.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"skip (already has how-to) {slug}")
        return
    idx = text.find('class="container seo-faq"')
    if idx == -1:
        print(f"WARN: no seo-faq anchor in {slug}, skipping")
        return
    insert_at = text.rfind("<section", 0, idx)
    block = build(slug)
    text = text[:insert_at] + block + "\n\n" + text[insert_at:]
    p.write_text(text, encoding="utf-8")
    print(f"added how-to to {slug}")


if __name__ == "__main__":
    for slug in DATA:
        if slug in HOWTO:
            process(slug)
        else:
            print(f"WARN: no how-to defined for {slug}")
    print(f"done — {len(HOWTO)} game pages targeted")
