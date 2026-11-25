#!/usr/bin/env python3
# WHY: hand crops done ad hoc get skipped, and six-finger hands slip past contact sheets.
# PURPOSE: look at a frame at MORE than full size, region by region, so nothing is judged from a thumbnail.
#   Two modes:
#   tiles  — cuts the frame into a 2x3 grid with 10% overlap and enlarges each tile 2x -> 6 PNGs + an index.
#            Run it on every still that has a person; open each tile. Nothing escapes between tiles.
#   boxes  — enlarges given regions (hands, faces, a label, a price) 3x for digit/finger/letter counting.
#   Input may be an image or a video + --t seconds (frame grabbed with ffmpeg, as review_board.py does).
# USAGE:
#   python3 crop_zoom.py stills/t0012.50.jpg tiles                       -> stills/zoom/t0012.50_r1c1.png ...
#   python3 crop_zoom.py art/u09.png boxes "300,900,700,1300;620,820,980,1180" --scale 3
#   python3 crop_zoom.py out/day-16.mp4 tiles --t 14.2
#   Box coordinates are in the source image's pixels (x0,y0,x1,y1). Find them on the full-size still first.
import argparse
import io
import os
import subprocess
import sys

from PIL import Image, ImageDraw


def load(path, t):
    if t is None:
        return Image.open(path).convert('RGB'), os.path.splitext(os.path.basename(path))[0]
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', path, '-frames:v', '1',
                        '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, stdin=subprocess.DEVNULL)
    if not r.stdout:
        sys.exit(f'no frame at {t}s in {path}')
    return Image.open(io.BytesIO(r.stdout)).convert('RGB'), f'{os.path.splitext(os.path.basename(path))[0]}_t{t:07.2f}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('mode', choices=['tiles', 'boxes'])
    ap.add_argument('boxes', nargs='?', default='')
    ap.add_argument('--t', type=float, default=None, help='seconds, when src is a video')
    ap.add_argument('--scale', type=float, default=None, help='enlargement (tiles 2, boxes 3)')
    ap.add_argument('--out', default=None, help='output dir (default <src dir>/zoom)')
    a = ap.parse_args()

    im, stem = load(a.src, a.t)
    w, h = im.size
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.src)), 'zoom')
    os.makedirs(out, exist_ok=True)
    regions = []
    if a.mode == 'tiles':
        cols, rows, ov = 2, 3, 0.10
        tw, th = w / cols, h / rows
        for r in range(rows):
            for c in range(cols):
                x0, y0 = max(0, c * tw - ov * tw), max(0, r * th - ov * th)
                x1, y1 = min(w, (c + 1) * tw + ov * tw), min(h, (r + 1) * th + ov * th)
                regions.append((f'r{r + 1}c{c + 1}', (int(x0), int(y0), int(x1), int(y1))))
        scale = a.scale or 2
    else:
        if not a.boxes:
            sys.exit('boxes mode needs "x0,y0,x1,y1;..."')
        for i, raw in enumerate(a.boxes.split(';')):
            regions.append((f'box{i + 1}', tuple(int(float(v)) for v in raw.split(','))))
        scale = a.scale or 3

    index = im.copy()
    d = ImageDraw.Draw(index)
    for name, box in regions:
        crop = im.crop(box)
        crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
        p = os.path.join(out, f'{stem}_{name}.png')
        crop.save(p)
        print(p, box)
        d.rectangle(box, outline=(0, 255, 120), width=4)
        d.text((box[0] + 8, box[1] + 6), name, fill=(0, 255, 120))
    ip = os.path.join(out, f'{stem}_index.jpg')
    index.save(ip, quality=88)
    print(ip)


if __name__ == '__main__':
    main()
