#!/usr/bin/env python3
"""Generate PNG favicon tiles for Prism Arcade.

Standard library only (no PIL). Renders the "Prism" mark:
- rounded-rect tile with a 135deg gradient (#ffb347 -> #7c5cff) matching .brand-mark
- a white-outlined triangle (the glass prism) filled with a spectrum gradient
  (warm red/orange bottom-left -> violet top-right) = "light split by a prism"
- a thin white centre facet line + a small 4-point sparkle (arcade whimsy)
PNG sizes: favicon-32.png, favicon-64.png, apple-touch-icon.png (180).
Antialiased via SDF coverage + premultiplied box downsample.
"""
import os
import struct
import zlib

S = 256
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
os.makedirs(OUT, exist_ok=True)

A = (0xFF, 0xB3, 0x47)   # accent (orange)
B = (0x7C, 0x5C, 0xFF)   # accent-2 (purple)
WHITE = (255, 255, 255)

# Prism geometry in normalized [0,1] canvas space (apex up).
AX, AY = 0.500, 0.250
BX, BY = 0.203, 0.734
CX, CY = 0.797, 0.734
# bounding box of the triangle, for the spectrum axis
TX0, TX1 = 0.203, 0.797
TY0, TY1 = 0.250, 0.734
OUTLINE = 0.018          # half-width of the white outline (normalized)
FACET_W = 0.010          # half-width of the centre facet line
SPARK_X, SPARK_Y = 0.734, 0.273
SPARK_R = 0.040          # outer radius of the 4-point sparkle
SPARK_K = 0.32           # concavity (smaller = pointier)

# Spectrum: warm -> cool, brand-aligned (red, orange, yellow, green, blue, violet)
STOPS = [
    (0.00, (255, 95, 109)),
    (0.18, (255, 179, 71)),
    (0.36, (255, 210, 77)),
    (0.55, (54, 211, 153)),
    (0.74, (74, 163, 255)),
    (1.00, (124, 92, 255)),
]


def blend(a, b, t):
    return (int(round(a[0] + (b[0] - a[0]) * t)),
            int(round(a[1] + (b[1] - a[1]) * t)),
            int(round(a[2] + (b[2] - a[2]) * t)))


def tile_color(x, y, size=None):
    size = size or S
    t = ((x + y) / 2.0) / (size - 1)
    return blend(A, B, max(0.0, min(1.0, t)))


def spectrum(t):
    t = max(0.0, min(1.0, t))
    for i in range(len(STOPS) - 1):
        t0, c0 = STOPS[i]
        t1, c1 = STOPS[i + 1]
        if t0 <= t <= t1:
            lt = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return blend(c0, c1, lt)
    return STOPS[-1][1]


def rounded_sdf(x, y, size, r):
    """Signed distance to a rounded rect spanning [0,size]^2.
    Negative = inside, positive = outside. Coverage = clamp(0.5 - d, 0, 1)."""
    half = size / 2.0
    ax = abs(x - half)
    ay = abs(y - half)
    bx = max(ax - (half - r), 0.0)
    by = max(ay - (half - r), 0.0)
    dist = (bx * bx + by * by) ** 0.5
    inner = -r
    if ax <= half - r or ay <= half - r:
        inner = -(half - r)
    return dist + inner


def _sign(px, py, ax, ay, bx, by):
    return (px - bx) * (ay - by) - (ax - bx) * (py - by)


def in_triangle(px, py):
    d1 = _sign(px, py, AX, AY, BX, BY)
    d2 = _sign(px, py, BX, BY, CX, CY)
    d3 = _sign(px, py, CX, CY, AX, AY)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)


def seg_dist(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    length2 = dx * dx + dy * dy
    if length2 == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    tt = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
    cx = ax + tt * dx
    cy = ay + tt * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def triangle_edge_dist(px, py):
    return min(seg_dist(px, py, AX, AY, BX, BY),
               seg_dist(px, py, BX, BY, CX, CY),
               seg_dist(px, py, CX, CY, AX, AY))


def render(size=S):
    M = 3                       # supersample for clean AA
    W = size * M
    margin = W * 0.035
    tile = W - 2 * margin
    radius = tile * 0.22

    # prism geometry scaled to the supersampled canvas
    sx = lambda v: v * W
    ax, ay = sx(AX), sx(AY)
    bx, by = sx(BX), sx(BY)
    cx, cy = sx(CX), sx(CY)
    tx0, tx1 = sx(TX0), sx(TX1)
    ty0, ty1 = sx(TY0), sx(TY1)
    w = OUTLINE * W
    fw = FACET_W * W
    spx, spy = sx(SPARK_X), sx(SPARK_Y)
    spr = SPARK_R * W
    spk = SPARK_K

    buf = [[(0, 0, 0, 0)] * W for _ in range(W)]
    for py in range(W):
        row = buf[py]
        for px in range(W):
            d = rounded_sdf(px + 0.5 - margin, py + 0.5 - margin, tile, radius)
            cov = 0.5 - d
            if cov <= 0:
                continue
            tc = cov if cov < 1 else 1.0
            col = tile_color(px, py, W)
            a = tc

            # prism body: spectrum fill
            if in_triangle(px / W, py / W):
                t = ((px / W - TX0) / (TX1 - TX0) + (TY1 - py / W) / (TY1 - TY0)) / 2.0
                col = spectrum(t)

            # white outline around the prism
            ed = triangle_edge_dist(px / W, py / W) * W
            if ed < w:
                oa = min(1.0, (w - ed) / (0.006 * W))
                col = blend(col, WHITE, oa)

            # centre facet line (vertical, inside the prism only)
            if in_triangle(px / W, py / W):
                fy0, fy1 = sx(0.273), sx(0.719)
                if fy0 <= py <= fy1:
                    dx = abs(px - W * 0.5)
                    if dx < fw:
                        fa = min(1.0, (fw - dx) / (0.004 * W))
                        col = blend(col, WHITE, 0.34 * fa)

            # 4-point sparkle (arcade whimsy)
            dx = px - spx
            dy = py - spy
            ss = abs(dx) + abs(dy)
            sm = max(abs(dx), abs(dy))
            if sm < spr * spk and ss < spr:
                sa = min(1.0, (spr - ss) / (0.012 * W))
                col = blend(col, WHITE, sa)

            row[px] = (col[0], col[1], col[2], int(round(255 * a)))
    return buf


def downsample(buf, target):
    W = len(buf)
    ratio = W / target
    out = [[(0, 0, 0, 0)] * target for _ in range(target)]
    for oy in range(target):
        x0 = int(oy * ratio)
        x1 = int((oy + 1) * ratio)
        if x1 <= x0:
            x1 = x0 + 1
        for ox in range(target):
            y0 = int(ox * ratio)
            y1 = int((ox + 1) * ratio)
            if y1 <= y0:
                y1 = y0 + 1
            r = g = b = a = 0
            n = 0
            for yy in range(x0, min(W, x1)):
                brow = buf[yy]
                for xx in range(y0, min(W, y1)):
                    pr, pg, pb, pa = brow[xx]
                    r += pr * pa
                    g += pg * pa
                    b += pb * pa
                    a += pa
                    n += 1
            if a == 0:
                out[oy][ox] = (0, 0, 0, 0)
            else:
                out[oy][ox] = (r // a, g // a, b // a, min(255, a // max(1, n)))
    return out


def write_png(path, data):
    h = len(data)
    w = len(data[0])
    raw = b""
    for row in data:
        raw += b"\x00"
        for (rr, gg, bb, aa) in row:
            raw += bytes((rr, gg, bb, aa))

    def chunk(tag, payload):
        c = payload
        length = len(c).to_bytes(4, "big")
        crc = (zlib.crc32(tag + c) & 0xFFFFFFFF).to_bytes(4, "big")
        return length + tag + c + crc

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    body = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(body)


def main():
    hi = render(S)
    for name, sz in (("favicon-32.png", 32), ("favicon-64.png", 64), ("apple-touch-icon.png", 180)):
        png = downsample(hi, sz)
        write_png(os.path.join(OUT, name), png)
        print("wrote", name, sz, "x", sz)


if __name__ == "__main__":
    main()
