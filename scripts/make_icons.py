#!/usr/bin/env python3
"""Generate app icons (PNG) for the PWA using only the Python standard library.

Draws the Star Drifter ship over a dark gradient background so the game has a
recognizable home-screen icon without needing any image libraries.
"""
import struct
import zlib
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")


def lerp(a, b, t):
    return int(round(a + (b - a) * t))


def draw(size, padding_ratio=0.0):
    """Return an RGBA bytearray (size*size*4) with the icon rendered."""
    px = bytearray(size * size * 4)

    # Background vertical gradient: top #131d36 -> bottom #060912
    top = (0x13, 0x1d, 0x36)
    bot = (0x06, 0x09, 0x12)

    cx = size / 2.0
    cy = size / 2.0
    # ship geometry, shrunk into the "safe zone" if padding is requested
    scale = (1.0 - padding_ratio) * size / 480.0

    # A handful of background stars (deterministic positions).
    stars = []
    seed = 12345
    for _ in range(size // 6):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sx = seed % size
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sy = seed % size
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sr = 1 + (seed % 3)
        stars.append((sx, sy, sr))

    # Ship triangle vertices (in a 480-space, centered), matching the game art.
    v = [(0, -150), (120, 130), (0, 60), (-120, 130)]
    vs = [(cx + x * scale, cy + y * scale * 0.9) for (x, y) in v]

    def in_ship(x, y):
        # point-in-polygon for the 4-point ship outline
        inside = False
        n = len(vs)
        j = n - 1
        for i in range(n):
            xi, yi = vs[i]
            xj, yj = vs[j]
            if (yi > y) != (yj > y):
                xint = (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi
                if x < xint:
                    inside = not inside
            j = i
        return inside

    accent = (0x6e, 0xa8, 0xff)

    for y in range(size):
        t = y / (size - 1)
        br = lerp(top[0], bot[0], t)
        bg = lerp(top[1], bot[1], t)
        bb = lerp(top[2], bot[2], t)
        row = y * size * 4
        for x in range(size):
            r, g, b = br, bg, bb
            # radial glow near top-center
            dx = (x - cx) / size
            dy = (y - cy * 0.6) / size
            glow = max(0.0, 0.35 - (dx * dx + dy * dy) * 1.6)
            r = min(255, int(r + glow * 90))
            g = min(255, int(g + glow * 110))
            b = min(255, int(b + glow * 150))
            o = row + x * 4
            px[o] = r
            px[o + 1] = g
            px[o + 2] = b
            px[o + 3] = 255

    # stars
    for (sx, sy, sr) in stars:
        for yy in range(max(0, sy - sr), min(size, sy + sr + 1)):
            for xx in range(max(0, sx - sr), min(size, sx + sr + 1)):
                o = (yy * size + xx) * 4
                px[o] = min(255, px[o] + 120)
                px[o + 1] = min(255, px[o + 1] + 130)
                px[o + 2] = min(255, px[o + 2] + 150)

    # ship (draw last, on top)
    minx = int(min(p[0] for p in vs)) - 1
    maxx = int(max(p[0] for p in vs)) + 1
    miny = int(min(p[1] for p in vs)) - 1
    maxy = int(max(p[1] for p in vs)) + 1
    for y in range(max(0, miny), min(size, maxy)):
        for x in range(max(0, minx), min(size, maxx)):
            if in_ship(x + 0.5, y + 0.5):
                o = (y * size + x) * 4
                px[o] = accent[0]
                px[o + 1] = accent[1]
                px[o + 2] = accent[2]
                px[o + 3] = 255

    return px


def write_png(path, size, px):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    raw = bytearray()
    stride = size * 4
    for y in range(size):
        raw.append(0)  # filter type 0
        raw += px[y * stride:(y + 1) * stride]

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    targets = [
        ("icon-192.png", 192, 0.30),
        ("icon-512.png", 512, 0.30),
        ("icon-maskable-512.png", 512, 0.42),
        ("apple-touch-icon.png", 180, 0.26),
    ]
    for name, size, pad in targets:
        px = draw(size, pad)
        write_png(os.path.join(OUT_DIR, name), size, px)
        print("wrote", name, size)


if __name__ == "__main__":
    main()
