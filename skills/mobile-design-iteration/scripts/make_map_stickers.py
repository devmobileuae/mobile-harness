#!/usr/bin/env python3
# WHAT: Continent map stickers (pastel pieces + white die-cut edge) from a map-puzzle app's catalog.json pieces; cleaner than photos of maps, which crop badly in tiles.
# RUN: python3 make_map_stickers.py --catalog <app>/Resources/catalog.json <outdir> europe,africa,asia,north-america,south-america,oceania
"""Continent map stickers for map-puzzle covers, drawn from the game's own puzzle pieces.

Each map in catalog.json has pieces with polygons in normalized map coordinates
(x in 0..1 of the width, y in 0..aspect). We draw every piece in a soft pastel,
thin darker borders, then give the whole shape a white die-cut edge and a soft
shadow, on a transparent background, like the app's clay stickers.
"""
import json, os, sys, math
from PIL import Image, ImageDraw, ImageFilter, ImageChops

import argparse
_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument('--catalog', default=os.environ.get('MAP_CATALOG_JSON', ''), help='catalog.json with maps[].pieces (default: $MAP_CATALOG_JSON)')
_ap.add_argument('outdir')
_ap.add_argument('ids', help='comma-separated map ids, e.g. europe,africa')
_a = _ap.parse_args()
if not _a.catalog:
    sys.exit('pass --catalog <catalog.json> (or set MAP_CATALOG_JSON)')
CATALOG = os.path.expanduser(_a.catalog)
OUT = _a.outdir
IDS = _a.ids.split(',')
SIZE = 640          # longest side of the drawn map, px
EDGE = 14           # white die-cut width, px
PAD = 40            # transparent margin around the sticker
SS = 3              # supersampling

PALETTE = ['#f6a96b', '#f7d66e', '#f39bb0', '#bfa3e6', '#97d39a', '#86cfc8', '#f2a08a', '#a9c3f2']
BORDER = (255, 255, 255, 210)


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


cat = json.load(open(CATALOG))
maps = {m['id']: m for m in cat['maps']}

for mid in IDS:
    m = maps[mid]
    def area(poly):
        a = 0.0
        n = len(poly) // 2
        for i in range(n):
            x1, y1 = poly[2 * i], poly[2 * i + 1]
            x2, y2 = poly[(2 * i + 2) % (2 * n)], poly[(2 * i + 3) % (2 * n)]
            a += x1 * y2 - x2 * y1
        return abs(a) / 2
    allp = [poly for p in m['pieces'] for poly in p['polys']]
    ax = [q[i] for q in allp for i in range(0, len(q), 2)]; ay = [q[i] for q in allp for i in range(1, len(q), 2)]
    minA = 0.0008 * (max(ax) - min(ax)) * (max(ay) - min(ay))
    for p in m['pieces']:
        p['polys'] = [q for q in p['polys'] if len(q) >= 6 and area(q) >= minA]
    m['pieces'] = [p for p in m['pieces'] if p['polys']]
    polys = [(p['id'], poly) for p in m['pieces'] for poly in p['polys']]
    xs = [poly[i] for _, poly in polys for i in range(0, len(poly), 2)]
    ys = [poly[i] for _, poly in polys for i in range(1, len(poly), 2)]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0, y1 - y0
    scale = SIZE / max(w, h)
    W = int(w * scale) + 2 * (PAD + EDGE)
    H = int(h * scale) + 2 * (PAD + EDGE)
    S = SS
    img = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    off = (PAD + EDGE) * S

    def pt(x, y):
        return ((x - x0) * scale * S + off, (y - y0) * scale * S + off)

    # stable colour per piece, spread by label position so neighbours tend to differ
    pieces = m['pieces']
    order = sorted(pieces, key=lambda p: (round(p['label'][1] * 40), p['label'][0]))
    colour = {p['id']: rgb(PALETTE[i % len(PALETTE)]) for i, p in enumerate(order)}
    for p in pieces:
        for poly in p['polys']:
            pts = [pt(poly[i], poly[i + 1]) for i in range(0, len(poly), 2)]
            if len(pts) >= 3:
                d.polygon(pts, fill=colour[p['id']] + (255,))
    for p in pieces:
        for poly in p['polys']:
            pts = [pt(poly[i], poly[i + 1]) for i in range(0, len(poly), 2)]
            if len(pts) >= 3:
                d.line(pts + [pts[0]], fill=BORDER, width=max(1, int(1.6 * S)), joint='curve')

    img = img.resize((W, H), Image.LANCZOS)
    alpha = img.split()[3]
    # die-cut: grow the land, smooth it, fill white
    grown = alpha.point(lambda a: 255 if a > 20 else 0)
    for _ in range(EDGE // 2):
        grown = grown.filter(ImageFilter.MaxFilter(5))
    grown = grown.filter(ImageFilter.GaussianBlur(2)).point(lambda a: 255 if a > 110 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(1))
    white = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    white.putalpha(grown)
    # soft shadow under the sticker
    shadow = Image.new('RGBA', (W, H), (20, 30, 60, 0))
    shadow.putalpha(grown.point(lambda a: int(a * 0.28)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    shadow = ImageChops.offset(shadow, 0, 8)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out = Image.alpha_composite(out, shadow)
    out = Image.alpha_composite(out, white)
    out = Image.alpha_composite(out, img)
    path = f'{OUT}/mapsticker-{mid}.png'
    out.save(path)
    print(path, out.size)
