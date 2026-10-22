#!/usr/bin/env python3
"""Replace old GA measurement ID with new one across all HTML pages.

Only the literal ID string is swapped, preserving each file's existing
indentation / layout exactly. Idempotent: skips files already on the new ID.
"""
import pathlib

ROOT = pathlib.Path(r"D:\WorkBuddy\游戏工作室\arcade-site")
OLD = "G-83BMVG4W6Q"
NEW = "G-3ZWV1GWSD3"


def main():
    files = sorted(list(ROOT.glob("*.html")) + list(ROOT.glob("games/*.html")))
    total_files = total_reps = 0
    for f in files:
        t = f.read_text(encoding="utf-8")
        n = t.count(OLD)
        if n == 0:
            print(f"  [SKIP] {f.name}")
            continue
        t = t.replace(OLD, NEW)
        f.write_text(t, encoding="utf-8")
        total_files += 1
        total_reps += n
        print(f"  [OK]   {f.name}: {n} replacements")
    print(f"\nDone: {total_files} files, {total_reps} replacements.")


if __name__ == "__main__":
    main()
