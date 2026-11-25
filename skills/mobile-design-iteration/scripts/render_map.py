#!/usr/bin/env python3
# WHAT: globes / flat world maps rendered from a map app's own country outlines JSON (country highlights, night globe). Used to make map/globe assets for Figma boards.
# RUN: python3 render_map.py --world <app>/Resources/world.json globe --lon 37 --lat 0 --size 1000 --hl KEN:#3cc24b --out out.png
#      python3 render_map.py --world <world.json> flat --w 1400 --visited FRA,ITA --hl JPN:#f26173 --style night --out out.png
#      (or set MAP_WORLD_JSON instead of --world)
"""Render clay-style globes and flat world maps from an app's own country outlines.

  render_map.py --world world.json globe --lon 15 --lat 45 [--size 1200] [--hl FRA:#3cc24b,ITA:#ffcc00] [--dim] --out globe.png
  render_map.py --world world.json flat  [--w 1400] [--visited FRA,ITA,JPN] [--hl BRA:#3cc24b] [--style night|paper] --out map.png

Globe: blue clay ocean, cream land, thin borders, soft shading, transparent outside the disc.
Flat:  equirectangular world, transparent background; `night` = navy land with yellow visited countries
       (the Profile card look), `paper` = cream land on nothing with coloured highlights.
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

WORLD = os.environ.get('MAP_WORLD_JSON', '')  # set by --world
SS = 3  # supersampling


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def parse_hl(s):
    out = {}
    if s:
        for part in s.split(','):
            part = part.strip()
            if not part:
                continue
            if ':' in part:
                k, v = part.split(':', 1)
                out[k.strip().upper()] = rgb(v)
            else:
                out[part.upper()] = rgb('#3cc24b')
    return out


def load():
    if not WORLD:
        sys.exit('pass --world <country outlines .json> (or set MAP_WORLD_JSON)')
    return json.load(open(os.path.expanduser(WORLD)))


def globe(args):
    size = args.size
    S = size * SS
    R = S / 2 - 2 * SS
    cx = cy = S / 2
    lon0 = math.radians(args.lon)
    lat0 = math.radians(args.lat)
    hl = parse_hl(args.hl)
    ocean = rgb('#2f6fc4') if not args.dim else rgb('#1d3f73')
    land = rgb('#efe4c8') if not args.dim else rgb('#5d6f8f')
    border = rgb('#b9ab8a') if not args.dim else rgb('#3a4a66')

    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=ocean + (255,))

    land_layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(land_layer)
    world = load()
    sl0, cl0 = math.sin(lat0), math.cos(lat0)

    def proj(lon, lat):
        lam = math.radians(lon) - lon0
        phi = math.radians(lat)
        cphi = math.cos(phi)
        x = cphi * math.sin(lam)
        y = cl0 * math.sin(phi) - sl0 * cphi * math.cos(lam)
        z = sl0 * math.sin(phi) + cl0 * cphi * math.cos(lam)
        return x, y, z

    order = sorted(world.keys(), key=lambda k: (k in hl))
    for iso in order:
        fill = hl.get(iso, land)
        for ring in world[iso]:
            pts = []
            vis = 0
            n = len(ring) // 2
            for i in range(n):
                x, y, z = proj(ring[2 * i], ring[2 * i + 1])
                if z >= 0:
                    vis += 1
                    pts.append((cx + x * R, cy - y * R))
                else:
                    m = math.hypot(x, y) or 1e-9
                    pts.append((cx + x / m * R, cy - y / m * R))
            if vis == 0 or len(pts) < 3:
                continue
            ld.polygon(pts, fill=fill + (255,))
            if vis == n:
                ld.line(pts + [pts[0]], fill=border + (255,), width=max(1, int(SS * size / 900)))
    # clip land to the disc
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    land_layer.putalpha(ImageChops.multiply(land_layer.split()[3], mask))
    img = Image.alpha_composite(img, land_layer)

    # clay shading: soft highlight top-left, darker rim bottom-right
    shade = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    steps = 60
    for i in range(steps):
        t = i / steps
        r = R * (1 - t)
        a = int(95 * (1 - t) ** 2.2)
        sd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(8, 20, 60, a), width=int(R / steps) + 2)
    hi = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hr = R * 0.62
    hx, hy = cx - R * 0.34, cy - R * 0.38
    hd.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(255, 255, 255, 46))
    hi = hi.filter(ImageFilter.GaussianBlur(R * 0.22))
    lo = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    lo_d = ImageDraw.Draw(lo)
    lr = R * 0.9
    lx, ly = cx + R * 0.42, cy + R * 0.46
    lo_d.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], fill=(6, 14, 50, 70))
    lo = lo.filter(ImageFilter.GaussianBlur(R * 0.3))
    inv = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    full = Image.new('RGBA', (S, S), (6, 14, 50, 60))
    inv.paste(full, (0, 0), ImageChops.subtract(mask, lo.split()[3].point(lambda v: 255 - v * 3 if v * 3 < 255 else 0)))
    for layer in (shade, hi):
        layer.putalpha(ImageChops.multiply(layer.split()[3], mask))
        img = Image.alpha_composite(img, layer)
    # darker lower-right limb
    limb = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    lm = ImageDraw.Draw(limb)
    lm.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(6, 14, 50, 90))
    cut = Image.new('L', (S, S), 0)
    off = R * 0.16
    ImageDraw.Draw(cut).ellipse([cx - R - off, cy - R - off, cx + R - off, cy + R - off], fill=255)
    cut = cut.filter(ImageFilter.GaussianBlur(R * 0.12))
    a = ImageChops.multiply(limb.split()[3], ImageChops.invert(cut))
    limb.putalpha(ImageChops.multiply(a, mask))
    img = Image.alpha_composite(img, limb)

    img = img.resize((size, size), Image.LANCZOS)
    img.save(args.out)
    print('wrote', args.out, img.size)


def flat(args):
    W = args.w
    lat_top, lat_bot = 84.0, -58.0
    H = int(round(W * (lat_top - lat_bot) / 360.0))
    S_W, S_H = W * SS, H * SS
    hl = parse_hl(args.hl)
    visited = set(x.strip().upper() for x in (args.visited or '').split(',') if x.strip())
    if args.style == 'night':
        land, vis_c, border = rgb('#2c4f93'), rgb('#f5c84c'), rgb('#16306b')
    else:
        land, vis_c, border = rgb('#efe4c8'), rgb('#3cc24b'), rgb('#b9ab8a')
    img = Image.new('RGBA', (S_W, S_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    world = load()

    def pt(lon, lat):
        return ((lon + 180.0) / 360.0 * S_W, (lat_top - lat) / (lat_top - lat_bot) * S_H)

    for iso, rings in world.items():
        if iso == 'ATA':
            continue
        fill = hl.get(iso) or (vis_c if iso in visited else land)
        for ring in rings:
            n = len(ring) // 2
            pts = [pt(ring[2 * i], ring[2 * i + 1]) for i in range(n)]
            if len(pts) < 3:
                continue
            xs = [p[0] for p in pts]
            if max(xs) - min(xs) > S_W * 0.5:
                continue  # ring wraps the antimeridian
            d.polygon(pts, fill=fill + (255,))
            d.line(pts + [pts[0]], fill=border + (255,), width=max(1, SS))
    img = img.resize((W, H), Image.LANCZOS)
    img.save(args.out)
    print('wrote', args.out, img.size)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--world', default=WORLD, help='country outlines JSON of the app (default: $MAP_WORLD_JSON)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('globe')
    g.add_argument('--lon', type=float, default=15)
    g.add_argument('--lat', type=float, default=40)
    g.add_argument('--size', type=int, default=1200)
    g.add_argument('--hl', default='')
    g.add_argument('--dim', action='store_true')
    g.add_argument('--out', required=True)
    f = sub.add_parser('flat')
    f.add_argument('--w', type=int, default=1400)
    f.add_argument('--visited', default='')
    f.add_argument('--hl', default='')
    f.add_argument('--style', default='night', choices=['night', 'paper'])
    f.add_argument('--out', required=True)
    a = ap.parse_args()
    WORLD = a.world
    (globe if a.cmd == 'globe' else flat)(a)
