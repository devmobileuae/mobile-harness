#!/usr/bin/env python3
"""Safe-zone QA for vertical 1080x1920 frames (Instagram Reels / TikTok / Shorts).

Usage:
  safe_zones.py frame.png [--boxes "x0,y0,x1,y1;..."] [--out qa.png]

Renders a QA still with unsafe bands tinted red (bottom ~420 px, right ~120 px, top 200 px).
If --boxes is given (bounding boxes of text / key elements, in source pixels), exits 1 when any
box intersects an unsafe band and prints which. Without boxes it only renders the still: a human
or a vision model must look at it.
"""
import argparse
import sys

from PIL import Image, ImageDraw

REF_W, REF_H = 1080, 1920
# (x0, y0, x1, y1) in 1080x1920 reference space
BANDS = {
    "top status bar": (0, 0, 1080, 200),
    "bottom caption/username/audio": (0, 1500, 1080, 1920),
    "right action rail": (960, 0, 1080, 1920),
}


def scale_band(band, w, h):
    sx, sy = w / REF_W, h / REF_H
    x0, y0, x1, y1 = band
    return (x0 * sx, y0 * sy, x1 * sx, y1 * sy)


def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--boxes", default="")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    img = Image.open(args.frame).convert("RGBA")
    w, h = img.size
    if abs(w / h - REF_W / REF_H) > 0.02:
        print(f"WARN: aspect {w}x{h} is not 9:16; bands are scaled anyway")

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    scaled = {name: scale_band(b, w, h) for name, b in BANDS.items()}
    for b in scaled.values():
        draw.rectangle(b, fill=(255, 0, 0, 90))

    failures = []
    if args.boxes:
        for raw in args.boxes.split(";"):
            box = tuple(float(v) for v in raw.split(","))
            draw.rectangle(box, outline=(0, 255, 0, 255), width=4)
            for name, band in scaled.items():
                if intersects(box, band):
                    failures.append(f"box {raw} intersects {name}")

    out = args.out or args.frame.rsplit(".", 1)[0] + "_safezones.png"
    Image.alpha_composite(img, overlay).convert("RGB").save(out)
    print(f"QA still: {out}")
    if failures:
        print("FAIL")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("PASS" if args.boxes else "RENDERED (no boxes given; inspect the still)")


if __name__ == "__main__":
    main()
