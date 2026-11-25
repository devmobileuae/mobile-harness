#!/usr/bin/env python3
# For Instagram reels pulled with `yt-dlp --write-info-json` into ./media: runs ref_prep.prep_video, then
# ffmpeg scdet cut detection -> meta.json with likes, comments, upload_date, n_cuts, avg_shot.
# Run: python3 ig_prep_cuts.py <research-dir>   (reads <dir>/media, writes <dir>/prep; ref_prep.py next to this file)
"""Sheets, hook frames, Whisper transcripts and cut times for the downloaded reels: python3 ig_prep_cuts.py <dir>"""
import glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ref_prep import prep_video

if len(sys.argv) < 2:
    sys.exit("usage: ig_prep_cuts.py <research-dir>")
HERE = os.path.abspath(sys.argv[1])
for mp4 in sorted(glob.glob(os.path.join(HERE, "media", "*.mp4"))):
    key = os.path.basename(mp4)[:-4]
    out = os.path.join(HERE, "prep", key)
    dur = prep_video(mp4, out)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-vf", "scdet=threshold=12", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    cuts = [round(float(x), 2) for x in re.findall(r"lavfi.scd.time: ([0-9.]+)", r.stderr)]
    info = json.load(open(os.path.join(HERE, "media", key + ".info.json")))
    meta = {k: info.get(k) for k in ("uploader", "channel", "like_count", "comment_count", "upload_date",
                                     "description", "track", "artist", "duration", "width", "height")}
    meta.update(dur=round(dur, 1), cuts=cuts, n_cuts=len(cuts),
                avg_shot=round(dur / (len(cuts) + 1), 2))
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(key, meta["uploader"], meta["dur"], "cuts", len(cuts), "avg", meta["avg_shot"], flush=True)
