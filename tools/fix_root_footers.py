#!/usr/bin/env python3
"""Fix root-page footers where footer-bottom was inserted outside </footer>."""
import pathlib

ROOT = pathlib.Path(r"D:\WorkBuddy\游戏工作室\arcade-site")
ROOTS = ["index.html", "games.html", "about.html", "contact.html", "privacy.html", "404.html"]

FOOTER_BOTTOM = (
    '<div class="footer-bottom">\n'
    '  <a href="https://www.pickworth.top/" target="_blank" rel="noopener">PickWorth &mdash; Honest AI Tool Reviews</a>\n'
    '</div>\n'
)


def fix(path: pathlib.Path):
    t = path.read_text(encoding="utf-8")
    if "footer-bottom" not in t:
        print(f"  [SKIP] {path.name}: no footer-bottom")
        return

    close = t.rfind("</footer>")
    if close == -1:
        print(f"  [WARN] {path.name}: no </footer>")
        return

    # Determine the indentation of the </footer> line
    foot_line_start = t.rfind("\n", 0, close) + 1
    indent = t[foot_line_start:close]
    n_indent = len(indent)

    # Check: does footer-bottom appear before </footer> and inside it?
    # In the broken case, footer-bottom is AFTER the grid's closing div,
    # but still before </footer>... actually it's placed before </footer>
    # but with wrong indentation (outside the footer div structure).
    # The safest fix: remove all existing footer-bottom blocks, reinsert.

    # Remove all footer-bottom blocks (they may span multiple lines or be inline)
    import re
    # Multi-line block: <div class="footer-bottom">\n...link...</div>\n
    t = re.sub(r'\s*<div class="footer-bottom">.*?</div>', "", t, flags=re.DOTALL)
    # Also remove any inline compact version: <div class="footer-bottom">...</div>
    t = re.sub(r'<div class="footer-bottom"><a[^>]*>.*?</a></div>', "", t)

    # Now reinsert before </footer> with correct indentation
    close2 = t.rfind("</footer>")
    new_block = indent + FOOTER_BOTTOM
    t = t[:close2] + new_block + t[close2:]

    path.write_text(t, encoding="utf-8")
    print(f"  [FIXED] {path.name}")


if __name__ == "__main__":
    for name in ROOTS:
        fix(ROOT / name)
    print("Done.")
