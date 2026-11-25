#!/usr/bin/env python3
# Per reference: sheet.jpg (contact sheet), hook.jpg (0/0.5/1/1.5/2/3 s), transcript.json (mlx-whisper small), meta.json.
# Needs ffmpeg/ffprobe, Pillow, `pip install mlx-whisper` (Apple Silicon). Label font: $REF_FONT (any .ttf), else a system font, else Pillow's default.
#   python3 ref_prep.py tiktok refs.json media/ prep/     # refs.json = list of tt_scrape rows (id, author, ...)
#   python3 ref_prep.py ads ads_dir/ prep/                # Meta Ads Library mp4s + active-ads.json
# Other scripts import prep_video() from it (see ig_prep_cuts.py, cartoons_prep.py).
"""Prepare reference videos for frame-by-frame analysis (no credits).

For every reference: <out>/<key>/
  sheet.jpg      timestamped contact sheet (whole clip; photo posts = all slides)
  hook.jpg       first 3 s at 0.0/0.5/1.0/1.5/2.0/3.0 s, large enough to OCR overlays
  transcript.json  local Whisper (mlx, small) segments with timestamps, or [] if silent
  meta.json      stats/caption/music when known

  ref_prep.py tiktok research/<topic>-<date>/refs.json research/<topic>-<date>/media research/<topic>-<date>/prep
  ref_prep.py ads research/<topic>-<date>/ads research/<topic>-<date>/prep
"""
import json, os, subprocess, sys, glob, hashlib
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [os.environ.get("REF_FONT", ""),
                   "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def label_font(size=20):
    for p in FONT_CANDIDATES:
        if p and os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except OSError: pass
    try: return ImageFont.load_default(size)
    except TypeError: return ImageFont.load_default()


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0


def frame(path, t, w):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                        "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True, stdin=subprocess.DEVNULL)
    if not r.stdout: return None
    import io
    return Image.open(io.BytesIO(r.stdout)).convert("RGB")


def grid(images, labels, cols, out):
    if not images: return
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    pad = 6
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + 26) + pad), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    f = label_font(20)
    for i, (im, lab) in enumerate(zip(images, labels)):
        x = pad + (i % cols) * (w + pad); y = pad + (i // cols) * (h + pad + 26)
        sheet.paste(im.resize((w, h)), (x, y + 26))
        d.text((x + 4, y + 2), lab, fill=(255, 210, 80), font=f)
    sheet.save(out, quality=82)


def prep_video(path, out):
    os.makedirs(out, exist_ok=True)
    dur = probe(path)
    # contact sheet: ~2 fps for short clips, capped at 40 frames
    step = 0.5 if dur <= 20 else (1.0 if dur <= 40 else dur / 40)
    ts = [round(i * step, 2) for i in range(int(dur / step) + 1) if i * step < dur - 0.05][:40]
    ims, labs = [], []
    for t in ts:
        im = frame(path, t, 240)
        if im: ims.append(im); labs.append(f"{t:.1f}s")
    grid(ims, labs, 8, os.path.join(out, "sheet.jpg"))
    hk = [t for t in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0) if t < dur]
    hims = [frame(path, t, 405) for t in hk]
    grid([i for i in hims if i], [f"{t:.1f}s" for t, i in zip(hk, hims) if i], 6, os.path.join(out, "hook.jpg"))
    tr = os.path.join(out, "transcript.json")
    if not os.path.exists(tr):
        try:
            import mlx_whisper
            r = mlx_whisper.transcribe(path, path_or_hf_repo="mlx-community/whisper-small-mlx",
                                       condition_on_previous_text=False, no_speech_threshold=0.6)
            segs = [{"start": round(s["start"], 1), "end": round(s["end"], 1), "text": s["text"].strip(),
                     "no_speech": round(s.get("no_speech_prob", 0), 2)} for s in r.get("segments", [])]
            json.dump({"language": r.get("language"), "segments": segs}, open(tr, "w"), ensure_ascii=False, indent=1)
        except Exception as e:
            json.dump({"error": str(e), "segments": []}, open(tr, "w"))
    return dur


def prep_photo(folder, out):
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(folder, "*.jpg")))
    ims = []
    for f in files:
        im = Image.open(f).convert("RGB"); im.thumbnail((360, 640)); ims.append(im)
    if ims:
        base = ims[0].size
        grid([i.resize(base) for i in ims], [f"slide {i+1}" for i in range(len(ims))], min(len(ims), 5),
             os.path.join(out, "sheet.jpg"))
        big = []
        for f in files[:2]:
            im = Image.open(f).convert("RGB"); im.thumbnail((720, 1280)); big.append(im)
        grid([b.resize(big[0].size) for b in big], [f"slide {i+1}" for i in range(len(big))], len(big),
             os.path.join(out, "hook.jpg"))
    json.dump({"segments": [], "note": "photo post — no audio track transcribed"}, open(os.path.join(out, "transcript.json"), "w"))
    return len(files)


def main():
    mode = sys.argv[1]
    if mode == "tiktok":
        refs = json.load(open(sys.argv[2])); media, outdir = sys.argv[3], sys.argv[4]
        for r in refs:
            out = os.path.join(outdir, f"tt-{r['author']}-{r['id']}")
            mp4 = os.path.join(media, r["id"] + ".mp4"); ph = os.path.join(media, r["id"])
            if os.path.exists(mp4): n = prep_video(mp4, out); r["media"] = mp4
            elif os.path.isdir(ph): n = prep_photo(ph, out); r["media"] = ph
            else: print("missing", r["id"]); continue
            full = os.path.join(media, r["id"] + ".json")
            if os.path.exists(full):
                it = json.load(open(full))
                r["music_full"] = it.get("music", {}).get("title"), it.get("music", {}).get("authorName")
                r["createTime"] = it.get("createTime")
                r["suggested_words"] = it.get("suggestedWords")
                r["contents_text"] = [c.get("desc") for c in (it.get("contents") or [])][:12]
            json.dump(r, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
            print("ok", out, n, flush=True)
    else:
        adsdir, outdir = sys.argv[2], sys.argv[3]
        meta = {a["ad_doc_id"][8:]: a for a in json.load(open(os.path.join(adsdir, "active-ads.json")))}
        seen = set()
        for f in sorted(glob.glob(os.path.join(adsdir, "*.mp4"))):
            h = hashlib.md5(open(f, "rb").read()).hexdigest()
            if h in seen: continue
            seen.add(h)
            key = os.path.basename(f)[:-4]
            out = os.path.join(outdir, f"ad-{key}")
            n = prep_video(f, out)
            m = dict(meta.get(key.split("-")[-1], {})); m["media"] = f; m["duration"] = n
            json.dump(m, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
            print("ok", out, round(n, 1), flush=True)


if __name__ == "__main__":
    main()
