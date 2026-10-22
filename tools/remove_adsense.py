#!/usr/bin/env python3
"""Remove the old Google AdSense script from all HTML pages.

Each page has exactly one AdSense <script ...adsbygoogle.js...> line in <head>.
This deletes that whole line (and collapses a resulting duplicate blank line).
Idempotent: files with no adsbygoogle reference are skipped.
"""
import pathlib, re

ROOT = pathlib.Path(r"D:\WorkBuddy\游戏工作室\arcade-site")


def process(path: pathlib.Path) -> int:
    text = path.read_text(encoding="utf-8")
    if "adsbygoogle" not in text:
        return 0

    lines = text.split("\n")
    kept = [ln for ln in lines if "adsbygoogle" not in ln]
    removed = len(lines) - len(kept)
    if removed == 0:
        return 0

    # Collapse runs of 3+ blank lines down to one blank line (tidies the gap
    # left behind in <head> without touching other formatting).
    out, blanks = [], 0
    for ln in kept:
        if ln.strip() == "":
            blanks += 1
            if blanks > 1:
                continue
        else:
            blanks = 0
        out.append(ln)
    new = "\n".join(out)

    path.write_text(new, encoding="utf-8")
    return removed


def main():
    files = sorted(list(ROOT.glob("*.html")) + list(ROOT.glob("games/*.html")))
    files = [f for f in files if f.name != "googlec618091bcb9edff2.html"]
    total_files = total_lines = 0
    for f in files:
        n = process(f)
        if n:
            total_files += 1
            total_lines += n
            print(f"  [OK]   {f.name}: removed {n}")
        else:
            print(f"  [SKIP] {f.name}")
    print(f"\nDone: {total_files} files cleaned, {total_lines} script lines removed.")


if __name__ == "__main__":
    main()
