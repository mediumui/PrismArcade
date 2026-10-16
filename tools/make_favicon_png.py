#!/usr/bin/env python3
"""Generate PNG favicon tiles for Prism Arcade (brand gradient + 'P' monogram).

Standard library only (no PIL). Renders a 256x256 RGBA canvas:
- rounded-rect tile with a 135deg gradient (#ffb347 -> #7c5cff) matching .brand-mark
- bold dark 'P' monogram centred (#141527)
- antialiased via SDF coverage + premultiplied downsample
Writes favicon-32.png, favicon-64.png, apple-touch-icon.png (180) into ../icons/.
"""
import os
import struct
import zlib

S = 256
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
os.makedirs(OUT, exist_ok=True)

INK = (0x14, 0x15, 0x27)
A = (0xFF, 0xB3, 0x47)   # accent
B = (0x7C, 0x5C, 0xFF)   # accent-2


def blend(a, b, t):
    return (int(round(a[0] + (b[0] - a[0]) * t)),
            int(round(a[1] + (b[1] - a[1]) * t)),
            int(round(a[2] + (b[2] - a[2]) * t)))


def tile_color(x, y):
    t = ((x + y) / 2.0) / (S - 1)
    return blend(A, B, max(0.0, min(1.0, t)))


# 'P' monogram: a boolean mask on a PW x PH grid (True = ink).
PW, PH = 26, 38


def pcell(r, c):
    # stem (cols 0..8) full height; bowl (rows 0..22) extends to col 24
    if c <= 8:
        return True
    if 0 <= r <= 22 and c <= 24:
        # round the four corners of the bowl's right region
        rr = 0 if r < 3 or r > 19 else 1
        if c >= 24 - rr + 1 and rr:  # trim 1px at top/bottom-right corners
            return False
        # counter (hole) inside the bowl
        if 5 <= r <= 17 and 11 <= c <= 19:
            return False
        return True
    return False


P_MASK = [[pcell(r, c) for c in range(PW)] for r in range(PH)]


def rounded_sdf(x, y, size, r):
    """Signed distance to a rounded rect spanning [0,size]^2.
    Negative = inside, positive = outside. Coverage = clamp(0.5 - d, 0, 1)."""
    half = size / 2.0
    ax = abs(x - half)
    ay = abs(y - half)
    # rounded corners as distance to the corner circle centre
    bx = max(ax - (half - r), 0.0)
    by = max(ay - (half - r), 0.0)
    dist = (bx * bx + by * by) ** 0.5
    inner = -r
    # points within the straight edge bands
    if ax <= half - r or ay <= half - r:
        inner = -(half - r)
    return dist + inner


def render(size=S):
    # supersample 3x for clean AA at small sizes
    M = 3
    W = size * M
    margin = int(W * 0.03)
    tile = W - 2 * margin
    radius = tile * 0.24
    # glyph footprint (centered-ish, slightly left of optical centre)
    gx0 = W * 0.27
    gy0 = W * 0.15
    gw = W * 0.46
    gh = W * 0.70

    buf = [[(0, 0, 0, 0)] * W for _ in range(W)]
    for py in range(W):
        row = buf[py]
        for px in range(W):
            # signed distance to the rounded-rect tile; SDF is in [0,size]^2 space
            d = rounded_sdf(px + 0.5 - margin, py + 0.5 - margin, tile, radius)
            cov = 0.5 - d
            if cov <= 0:
                continue
            cov = cov if cov < 1 else 1.0
            base = tile_color(px, py)
            ink = False
            if gx0 <= px < gx0 + gw and gy0 <= py < gy0 + gh:
                c = int((px - gx0) / gw * PW)
                r = int((py - gy0) / gh * PH)
                c = min(PW - 1, c)
                r = min(PH - 1, r)
                ink = P_MASK[r][c]
            col = INK if ink else base
            row[px] = (col[0], col[1], col[2], int(round(255 * cov)))
    return buf


def downsample(buf, target):
    """Box-filter premultiplied downsample from W x W to target x target."""
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
        for (r, g, b, a) in row:
            raw += bytes((r, g, b, a))

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
