#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix heading-order violations (h1 -> h3 jumps) across the site.

Lighthouse flagged `heading-order` on every page: the first heading after the
<h1> was an <h3>, skipping <h2>. Rule applied here: walk headings in document
order and demote any heading that skips a level down to prev + 1.

Only heading *levels* change, never text. css/style.css carries companion rules
so a promoted heading keeps the size it had as an <h3>.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APPLY = "--apply" in sys.argv
HEAD = re.compile(r"<(/?)h([1-6])([^>]*)>", re.I)

report = []
for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in {".git", "tools", "node_modules", ".workbuddy"}]
    for f in sorted(files):
        if not f.endswith(".html") or f == "googlec618091bcb9edff2.html":
            continue
        p = os.path.join(dirpath, f)
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        raw = open(p, encoding="utf-8", newline="").read()

        # mask script/style so JS or CSS strings containing "<h3>" are untouched
        masked = re.sub(r"<(script|style)\b.*?</\1>",
                        lambda m: " " * len(m.group(0)), raw, flags=re.S | re.I)

        edits = []          # (start, end, replacement)
        stack = []          # (orig_level, final_level)
        prev = 0
        for m in HEAD.finditer(masked):
            closing, lvl = bool(m.group(1)), int(m.group(2))
            attrs = raw[m.start(3):m.end(3)]
            if not closing:
                final = prev + 1 if (prev and lvl > prev + 1) else lvl
                stack.append((lvl, final))
                prev = final
                if final != lvl:
                    edits.append((m.start(), m.end(), "<h%d%s>" % (final, attrs)))
            else:
                if stack:
                    orig, final = stack.pop()
                    if final != orig and orig == lvl:
                        edits.append((m.start(), m.end(), "</h%d>" % final))

        if not edits:
            continue
        out, last = [], 0
        for start, end, rep in edits:
            out.append(raw[last:start])
            out.append(rep)
            last = end
        out.append(raw[last:])
        report.append((rel, [e for e in edits if e[2].startswith("<h") and not e[2].startswith("</")]))
        if APPLY:
            open(p, "w", encoding="utf-8", newline="").write("".join(out))

print("mode:", "APPLY" if APPLY else "DRY RUN")
for rel, opens in report:
    pairs = re.findall(r"<h(\d)", "".join(o[2] for o in opens))
    print("  %-26s %d heading(s) promoted" % (rel, len(opens)))
print("pages changed:", len(report))
if not APPLY:
    print("re-run with --apply to write")
