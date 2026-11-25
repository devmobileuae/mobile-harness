#!/usr/bin/env python3
# PURPOSE: label-stamped contact sheet of stills/t*.jpg made by `node render.cjs stills ...`.
#   A sheet is for ORDER and CONTINUITY only - it is NOT the anatomy/safe-zone check (tiles are 324 px).
# USAGE (run inside the episode folder): python3 sheet_stills.py out/sheet.jpg [cols=6]
"""Contact sheet of stills/t*.jpg:  python3 sheet_stills.py out/name.jpg [cols]"""
import sys, glob, os
from PIL import Image, ImageDraw
fs = sorted(glob.glob('stills/t*.jpg')); cols = int(sys.argv[2]) if len(sys.argv) > 2 else 6
tw, th = 324, 576; rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    sheet.paste(Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    d.rectangle(((i % cols) * tw, (i // cols) * th, (i % cols) * tw + 70, (i // cols) * th + 18), fill=(0, 0, 0)); d.text(((i % cols) * tw + 4, (i // cols) * th + 3), os.path.basename(f)[1:-4], fill=(255, 220, 60))
sheet.save(sys.argv[1], quality=86); print(sheet.size, len(fs))
