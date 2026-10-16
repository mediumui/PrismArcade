#!/usr/bin/env python3
"""Replace the single-line '<script src="/js/analytics.js"></script>' on every
page with the inline GA4 gtag snippet, so AdSense's "pasted code" verification
(which greps the HTML source for Google markers) can find them.

Idempotent:
  - Pages already containing 'googletagmanager' (inline gtag) -> skip.
  - Pages still referencing /js/analytics.js -> replace that line with the
    inline snippet.
Indentation of the replacement matches the existing script line's indent.
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GA_ID = "G-83BMVG4W6Q"

INLINE = [
    '<!-- Google tag (gtag.js) -->',
    '<script async src="https://www.googletagmanager.com/gtag/js?id=' + GA_ID + '"></script>',
    '<script>',
    'window.dataLayer = window.dataLayer || [];',
    'function gtag(){dataLayer.push(arguments);}',
    "gtag('js', new Date());",
    "gtag('config', '" + GA_ID + "');",
    '</script>',
]


def html_files():
    out = []
    for root, _d, fs in os.walk(BASE):
        top = os.path.relpath(root, BASE).split(os.sep)[0]
        if top in ("tools", "node_modules", "out", "og", ".git", ".workbuddy"):
            continue
        for fn in fs:
            if fn.endswith(".html"):
                out.append(os.path.join(root, fn))
    return sorted(out)


def main():
    changed = skipped = 0
    for path in html_files():
        rel = os.path.relpath(path, BASE)
        with open(path, encoding="utf-8") as f:
            text = f.read()

        if "googletagmanager" in text:
            print(f"skip (already inline gtag): {rel}")
            skipped += 1
            continue

        # Find the line that references the global analytics.js
        lines = text.splitlines(keepends=True)
        idx = None
        for i, ln in enumerate(lines):
            if "/js/analytics.js" in ln:
                idx = i
                break
        if idx is None:
            print(f"!! no analytics.js line found: {rel}")
            continue

        m = re.match(r"^[ \t]*", lines[idx])
        indent = m.group(0)
        replacement = [indent + ln + "\n" for ln in INLINE]

        new_lines = lines[:idx] + replacement + lines[idx + 1:]
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(new_lines)
        changed += 1
        print(f"inlined: {rel} (indent {len(indent)})")

    print(f"\nDone: {changed} inlined, {skipped} skipped.")


if __name__ == "__main__":
    main()
