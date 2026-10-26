#!/usr/bin/env python3
"""Re-inject the AdSense Auto-Ads <script> for the current publisher account.

The old account's script was removed site-wide (commit 3141f26) and only
ads.txt was updated for the new pub id. The page <head> scripts were never
re-added, so Google can't find the ad code during review ("site not ready").

This re-adds the correct script right before the `<!-- Google tag (gtag.js) -->`
marker (the original position), using the new publisher id from ads.txt.

Idempotent: files that already contain an adsbygoogle client script are skipped.
"""
import pathlib
import re

ROOT = pathlib.Path(r"D:\WorkBuddy\游戏工作室\arcade-site")
PUB_ID = "ca-pub-4276717672284472"
SCRIPT = (
    '  <script async src="https://pagead2.googlesyndication.com/pagead/'
    f'js/adsbygoogle.js?client={PUB_ID}" crossorigin="anonymous"></script>'
)
GTAG_RE = re.compile(r"(?m)^(\s*)<!-- Google tag \(gtag\.js\) -->")


def process(path: pathlib.Path) -> int:
    text = path.read_text(encoding="utf-8")
    if "adsbygoogle.js?client=" in text:
        return 0  # already has an ad script; leave it alone
    m = GTAG_RE.search(text)
    if not m:
        if "</head>" in text:
            text = text.replace("</head>", SCRIPT + "\n\n</head>", 1)
        else:
            return 0
    else:
        line = m.group(0)
        text = GTAG_RE.sub(SCRIPT + "\n\n" + line, text, count=1)
    path.write_text(text, encoding="utf-8")
    return 1


def main():
    files = sorted(list(ROOT.glob("*.html")) + list(ROOT.glob("games/*.html")))
    files = [f for f in files if f.name != "googlec618091bcb9edff2.html"]
    total = 0
    for f in files:
        n = process(f)
        total += n
        print(f"  [{'OK' if n else 'SKIP'}] {f.name}")
    print(f"\nDone: injected into {total} file(s).")


if __name__ == "__main__":
    main()
