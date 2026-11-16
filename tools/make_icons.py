#!/usr/bin/env python3
"""make_icons.py - build docs/favicon.ico (16 + 32 px PNG entries) and docs/apple-touch-icon.png (180 x 180, opaque Paper
background) from the Pacta logo, with the dependency-free tools/pacta_raster.py (no fonts needed). Deterministic output.

    python3 tools/make_icons.py [--out-dir docs]
"""
import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pacta_raster import Canvas, draw_pacta_logo, write_png  # noqa: E402

BG = "#f7f7f5"


def png_bytes(size, alpha, pad, tmp):
    cv = Canvas(size, size, BG, alpha=alpha)
    draw_pacta_logo(cv, pad, pad, size - 2 * pad, ss=8)
    write_png(tmp, cv)
    b = open(tmp, "rb").read()
    os.remove(tmp)
    return b


def ico(pngs):
    """ICO container with PNG-compressed entries (supported by every current browser)."""
    head = struct.pack("<HHH", 0, 1, len(pngs))
    off, dirs, body = 6 + 16 * len(pngs), b"", b""
    for size, b in pngs:
        dirs += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(b), off + len(body))
        body += b
    return head + dirs + body


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs"))
    a = ap.parse_args(argv)
    tmp = os.path.join(a.out_dir, ".icon-tmp.png")
    data = ico([(16, png_bytes(16, True, 0, tmp)), (32, png_bytes(32, True, 0, tmp))])
    open(os.path.join(a.out_dir, "favicon.ico"), "wb").write(data)
    touch = png_bytes(180, False, 22, tmp)
    open(os.path.join(a.out_dir, "apple-touch-icon.png"), "wb").write(touch)
    print("favicon.ico bytes", len(data), "apple-touch-icon.png bytes", len(touch))


if __name__ == "__main__":
    main()
