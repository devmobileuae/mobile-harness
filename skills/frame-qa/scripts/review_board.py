#!/usr/bin/env python3
# Self-contained (probe/frame helpers inlined from social-research/scripts/ref_prep.py). Font: --font <ttf>
#   (Bold; a sibling *Regular* file is used for body text if present), else a system font, else PIL's default.
# PURPOSE: one row per piece of a production BATCH (title, duration, caption.txt, sound.txt, 8 evenly spaced
#   frames). Use it to triage a batch (wrong caption, wrong sound, black frames, a piece that is all one shot).
#   180-px tiles: it is NOT an anatomy or safe-zone check.
# USAGE: python3 review_board.py <batch-dir> [--per-page 6] [--font Some-Bold.ttf]  -> <dir>/board-N.png
#   expects <dir>/<format>/<piece>/final.mp4 (or slideshow.mp4) + optional caption.txt / sound.txt
"""Review board for a production batch: one row per piece (title + 8 evenly spaced frames).

    python3 review_board.py <batch-dir> [--per-page 6]   # → <dir>/board-N.png

Reads <dir>/<format>/<piece>/final.mp4 (or slideshow.mp4), caption.txt and sound.txt.
"""
import glob, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont


class R:  # from ref_prep.py
    @staticmethod
    def probe(path):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        try: return float(r.stdout.strip())
        except ValueError: return 0.0

    @staticmethod
    def frame(path, t, w):
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                            "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                           capture_output=True, stdin=subprocess.DEVNULL)
        if not r.stdout: return None
        import io
        return Image.open(io.BytesIO(r.stdout)).convert("RGB")

FONT = sys.argv[sys.argv.index('--font') + 1] if '--font' in sys.argv else '/System/Library/Fonts/Helvetica.ttc'
FONT_R = FONT.replace('Bold', 'Regular') if os.path.exists(FONT.replace('Bold', 'Regular')) else FONT


def _tt(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()
FW, FH, N = 180, 320, 8


def piece_row(d):
    vid = next((p for p in (os.path.join(d, 'final.mp4'), os.path.join(d, 'slideshow.mp4')) if os.path.exists(p)), None)
    if not vid:
        return None
    dur = R.probe(vid)
    ts = [dur * (i + 0.5) / N for i in range(N)]
    frames = [R.frame(vid, t, FW) for t in ts]
    row = Image.new('RGB', (FW * N + 8 * (N + 1), FH + 110), (18, 18, 20))
    dr = ImageDraw.Draw(row)
    rel = '/'.join(d.rstrip('/').split('/')[-2:])
    cap = open(os.path.join(d, 'caption.txt')).read().strip().replace('\n', ' ') if os.path.exists(os.path.join(d, 'caption.txt')) else ''
    snd = open(os.path.join(d, 'sound.txt')).read().strip().split('\n')[0] if os.path.exists(os.path.join(d, 'sound.txt')) else ''
    dr.text((10, 8), f'{rel}   {dur:.1f}s', font=_tt(FONT, 28), fill=(255, 200, 80))
    dr.text((10, 44), cap[:150], font=_tt(FONT_R, 22), fill=(220, 220, 225))
    dr.text((10, 74), ('♪ ' + snd)[:150], font=_tt(FONT_R, 20), fill=(150, 150, 160))
    for i, (f, t) in enumerate(zip(frames, ts)):
        if f:
            row.paste(f.resize((FW, FH)), (8 + i * (FW + 8), 104))
    return row


def main():
    root = sys.argv[1]
    per = int(sys.argv[sys.argv.index('--per-page') + 1]) if '--per-page' in sys.argv else 6
    dirs = sorted(d for d in glob.glob(os.path.join(root, '*', '*')) if os.path.isdir(d) and '/_' not in d)
    rows = [r for r in (piece_row(d) for d in dirs) if r]
    for p in range(0, len(rows), per):
        chunk = rows[p:p + per]
        page = Image.new('RGB', (chunk[0].width, sum(r.height + 6 for r in chunk)), (8, 8, 9))
        y = 0
        for r in chunk:
            page.paste(r, (0, y)); y += r.height + 6
        out = os.path.join(root, f'board-{p // per + 1}.png')
        page.save(out)
        print(out, len(chunk))


if __name__ == '__main__':
    main()
