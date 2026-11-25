#!/usr/bin/env python3
# PURPOSE: the cover check the owner actually looks at — a phone-grid-sized read. Writes one JPEG with
#   (1) the full 9:16 cover, (2) the centre 3:4 crop the Instagram profile grid shows (y 240-1680 on 1080x1920),
#   (3) the cover at 360 px wide — roughly one grid tile on a phone. If the top line or title is not readable
#   in (3), it fails.
# USAGE: python3 grid_preview.py covers/ep-16.png [out_preview.jpg]
#   default out: <cover>_preview.jpg
import os
import sys

from PIL import Image

W, H = 1080, 1920


def preview(im, out):   # the full cover, the centre 3:4 the profile grid shows, and the size it has in the grid on a phone
    pv = Image.new('RGB', (W + 40 + W + 40 + 360, H), (18, 18, 18)); pv.paste(im, (0, 0)); pv.paste(im.crop((0, 240, W, 1680)), (W + 40, 240))
    pv.paste(im.resize((360, 640), Image.LANCZOS), (2 * W + 80, 640)); pv.resize((pv.width // 2, pv.height // 2), Image.LANCZOS).save(out, quality=88)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__ or 'usage: grid_preview.py cover.png [out.jpg]')
    src = sys.argv[1]
    im = Image.open(src).convert('RGB')
    if im.size != (W, H):
        print(f'WARN: {im.size} is not 1080x1920; resized for the preview')
        im = im.resize((W, H), Image.LANCZOS)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + '_preview.jpg'
    preview(im, out)
    print(out)
