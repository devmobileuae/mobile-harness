#!/usr/bin/env python3
"""Check one App Store localization folder against Apple's limits and our keyword rules.

  python3 check_meta.py es-MX [fr-FR ...] [--root appstore/metadata] [--brand myapp] [--competitors a,b,c]

Reads fastlane-layout folders <root>/<locale>/ (default root: ./appstore/metadata, run from the app repo).
--brand: your own brand word, allowed in both name and subtitle. --competitors: brand names that must not
appear in the keyword field (Guideline 2.3.7); also read from <root>/competitors.txt, one per line.

Limits: name 30, subtitle 30, keywords 100 UTF-8 bytes, promotional text 170, description and release notes 4000,
screenshots.txt exactly 10 headlines (<em>accent</em>, <br> for the line break).
Keyword rules: comma-separated without spaces, every term longer than 2 characters, no word that the name or
subtitle already index, no term repeated.
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path("appstore/metadata")
LIMITS = {"name": 30, "subtitle": 30, "promotional_text": 170, "description": 4000, "release_notes": 4000}
BRANDS = set()   # competitor brands, filled in main()
OWN = set()      # own brand word(s), filled in main()


def norm(w):
    w = unicodedata.normalize("NFKD", w.lower())
    return "".join(c for c in w if not unicodedata.combining(c))


def words(s):
    return {norm(w) for w in re.findall(r"[\w'-]+", s) if len(w) > 1}


def check(locale):
    d = ROOT / locale
    problems, info = [], []
    text = {}
    for f in ["name", "subtitle", "keywords", "promotional_text", "description", "release_notes"]:
        p = d / f"{f}.txt"
        if not p.exists():
            problems.append(f"missing {f}.txt")
            continue
        text[f] = p.read_text().strip()
        if f in LIMITS and len(text[f]) > LIMITS[f]:
            problems.append(f"{f}: {len(text[f])} > {LIMITS[f]} characters")
        info.append(f"{f}: {len(text[f])}")
    kw = text.get("keywords", "")
    nbytes = len(kw.encode("utf-8"))
    if nbytes > 100:
        problems.append(f"keywords: {nbytes} > 100 bytes")
    info.append(f"keywords: {nbytes} bytes")
    terms = kw.split(",") if kw else []
    indexed = words(text.get("name", "")) | words(text.get("subtitle", ""))
    seen = set()
    for t in terms:
        if t != t.strip() or not t:
            problems.append(f"keyword {t!r}: blank or spaces around it")
        if len(t.strip()) <= 2:
            problems.append(f"keyword {t!r}: 2 characters or fewer")
        n = norm(t.strip())
        if n in seen:
            problems.append(f"keyword {t!r}: repeated")
        seen.add(n)
        if n in indexed:
            problems.append(f"keyword {t!r}: already in the name or subtitle")
        if n in BRANDS:
            problems.append(f"keyword {t!r}: competitor brand")
    rep = (words(text.get("name", "")) & words(text.get("subtitle", ""))) - OWN
    if rep:
        problems.append(f"name and subtitle repeat {sorted(rep)}")
    shots = d / "screenshots.txt"
    if shots.exists():
        lines = [l for l in shots.read_text().splitlines() if l.strip()]
        if len(lines) != 10:
            problems.append(f"screenshots.txt: {len(lines)} headlines, want 10")
        for i, l in enumerate(lines, 1):
            plain = re.sub(r"<[^>]+>", "", l)
            if "<em>" not in l:
                problems.append(f"screenshot {i}: no <em> accent")
            longest = max(len(part) for part in re.sub(r"</?em>", "", l).split("<br>"))
            if longest > 22:
                problems.append(f"screenshot {i}: a line of {longest} characters (max 22): {plain}")
    else:
        problems.append("missing screenshots.txt")
    subs = d / "subscriptions.json"
    if subs.exists():
        s = json.loads(subs.read_text())
        for k, lim in (("group", 30), ("yearly_name", 30), ("yearly_description", 45),
                       ("monthly_name", 30), ("monthly_description", 45)):
            v = s.get(k, "")
            if not v or len(v) > lim:
                problems.append(f"subscriptions.{k}: {len(v)} characters (1–{lim})")
    else:
        problems.append("missing subscriptions.json")
    print(f"{locale}: " + ", ".join(info))
    for p in problems:
        print("   ", p)
    print(f"{locale}: {'ok' if not problems else str(len(problems)) + ' problems'}")
    return not problems


def main():
    global ROOT
    ap = argparse.ArgumentParser(description="Check App Store localization folders")
    ap.add_argument("locales", nargs="+")
    ap.add_argument("--root", default="appstore/metadata")
    ap.add_argument("--brand", default="", help="own brand word(s), comma-separated")
    ap.add_argument("--competitors", default="", help="competitor brands, comma-separated")
    a = ap.parse_args()
    ROOT = Path(a.root)
    OWN.update(norm(w) for w in a.brand.split(",") if w.strip())
    BRANDS.update(norm(w.strip()) for w in a.competitors.split(",") if w.strip())
    comp = ROOT / "competitors.txt"
    if comp.exists():
        BRANDS.update(norm(l.strip()) for l in comp.read_text().splitlines() if l.strip())
    ok = all([check(l) for l in a.locales])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
