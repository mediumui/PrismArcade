#!/usr/bin/env python3
"""Add a footer-bottom bar with an external link to PickWorth on every page.

Inserts a <div class="footer-bottom"> bar just before the closing </footer>.
Handles both compact (single-line) footers and multi-line footers by detecting
the actual format in each file.
"""
import pathlib

ROOT = pathlib.Path(r"D:\WorkBuddy\游戏工作室\arcade-site")

EXTERNAL_LINK = '<a href="https://www.pickworth.top/" target="_blank" rel="noopener">PickWorth &mdash; Honest AI Tool Reviews</a>'


def insert_compact(content: str) -> tuple[str, int]:
    """For single-line footers: insert bottom bar right before </footer> on the same line."""
    idx = content.rfind("</footer>")
    if idx == -1:
        return content, 0
    bar = (
        '<div class="footer-bottom">'
        + EXTERNAL_LINK
        + "</div>"
    )
    new = content[:idx] + bar + content[idx:]
    return new, 1


def insert_multiline(content: str) -> tuple[str, int]:
    """For multi-line footers: insert a new block just before the closing </footer> line."""
    idx = content.rfind("</footer>")
    if idx == -1:
        return content, 0
    # 4-space indent for direct children, 6 for the link
    block = (
        '    <div class="footer-bottom">\n'
        "      " + EXTERNAL_LINK + "\n"
        "    </div>\n"
    )
    new = content[:idx] + block + content[idx:]
    return new, 1


def process(path: pathlib.Path) -> int:
    text = path.read_text(encoding="utf-8")
    if "footer-bottom" in text:
        print(f"  [SKIP] {path.name}")
        return 0

    # Detect format: is <footer ...> on the same line as </footer>?
    last_close = text.rfind("</footer>")
    line_start = text.rfind("\n", 0, last_close) + 1
    same_line_open = text[line_start:last_close].find("<footer") != -1

    if same_line_open:
        new, n = insert_compact(text)
    else:
        new, n = insert_multiline(text)

    if n:
        path.write_text(new, encoding="utf-8")
        kind = "compact" if same_line_open else "multiline"
        print(f"  [OK]   {path.name}  ({kind})")
    else:
        print(f"  [WARN] {path.name}: no </footer> found")
    return n


def main():
    files = sorted(list(ROOT.glob("*.html")) + list(ROOT.glob("games/*.html")))
    print(f"Processing {len(files)} HTML files\n")
    total = sum(process(f) for f in files)
    print(f"\n{total}/{len(files)} files updated.")


if __name__ == "__main__":
    main()
