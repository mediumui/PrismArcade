#!/usr/bin/env python3
"""Idempotently point every HTML page's analytics at the single global
script /js/analytics.js.

Behaviour:
  - If the page already references /js/analytics.js -> skip (no change).
  - Otherwise, if a per-page gtag block exists (gtag( or googletagmanager),
    remove it; then insert a single `<script src="/js/analytics.js"></script>`
    just before </head>, matching that line's indentation.
  - If neither exists, just insert the single-line reference before </head>.

This guarantees each page ends up with EXACTLY one analytics reference and
no inline gtag code, so the GA property only ever lives in js/analytics.js.
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = '<script src="/js/analytics.js"></script>'


def html_files():
    out = []
    for root, _dirs, files in os.walk(BASE):
        top = os.path.relpath(root, BASE).split(os.sep)[0]
        if top in ("tools", "node_modules", "out", ".git", ".workbuddy", "og"):
            continue
        for fn in files:
            if fn.endswith(".html"):
                out.append(os.path.join(root, fn))
    return sorted(out)


def strip_gtag_block(lines):
    """Remove an inline gtag snippet (a <!-- Google tag --> comment + its two
    <script> tags) if present. Returns the cleaned text."""
    text = "".join(lines)
    # Remove the gtag loader script tag line
    text = re.sub(
        r'(?m)^[ \t]*<script async src="https://www\.googletagmanager\.com/gtag/js[^"]*"></script>\s*\n?',
        "", text,
    )
    # Remove the inline config <script>...</script> that defines gtag()
    text = re.sub(
        r'(?ms)^[ \t]*<script>\s*\nwindow\.dataLayer = window\.dataLayer \|\| \[\];\s*\n'
        r'function gtag\(\)\{dataLayer\.push\(arguments\);\}\s*\n'
        r"gtag\('js', new Date\(\)\);\s*\n"
        r"gtag\('config', '[^']+'\);\s*\n</script>\s*",
        "", text,
    )
    # Remove the comment marker if no gtag code remains
    if "googletagmanager" not in text and "gtag(" not in text:
        text = re.sub(r'(?m)^[ \t]*<!-- Google tag \(gtag\.js\) -->\s*\n?', "", text)
    return text


def main():
    changed = 0
    skipped = 0
    for path in html_files():
        rel = os.path.relpath(path, BASE)
        with open(path, encoding="utf-8") as f:
            text = f.read()

        if "/js/analytics.js" in text:
            print(f"skip (already references analytics.js): {rel}")
            skipped += 1
            continue

        # Remove any inline gtag block if present
        text = strip_gtag_block([text])

        # Insert single-line reference before </head>
        lines = text.splitlines(keepends=True)
        head_idx = None
        for i, ln in enumerate(lines):
            if ln.strip() == "</head>":
                head_idx = i
                break
        if head_idx is None:
            print(f"!! no </head>: {rel}")
            continue
        m = re.match(r"^[ \t]*", lines[head_idx])
        indent = m.group(0)

        ref_line = indent + REF + "\n"
        new_lines = lines[:head_idx] + [ref_line] + lines[head_idx:]
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(new_lines)
        changed += 1
        print(f"injected: {rel} (indent {len(indent)})")

    print(f"\nDone: {changed} changed, {skipped} skipped.")


if __name__ == "__main__":
    main()
