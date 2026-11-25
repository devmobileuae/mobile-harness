#!/usr/bin/env python3
"""Free App Store keyword signals per storefront (no API key): autocomplete and who ranks.

  python3 aso_probe.py hints fr "géograph"            # autocomplete suggestions for a prefix
  python3 aso_probe.py depth fr "jeu de géographie"     # letters typed before the term is suggested
  python3 aso_probe.py top fr "drapeaux quiz" [-n 10]   # top apps for a search: name, ratings, genre
  python3 aso_probe.py batch fr terms.txt               # depth + top-3 for every line of a file

`depth` is a rough popularity proxy: a term suggested after 3 letters is searched far more than one that needs
the whole word. It compares terms that share a prefix, nothing more (Apple's own popularity is in Apple Ads).
"""
import argparse, json, plistlib, sys, time, urllib.parse, urllib.request

STOREFRONTS = {"us": 143441, "fr": 143442, "de": 143443, "it": 143450, "es": 143454, "mx": 143468,
               "br": 143503, "pt": 143453, "ca": 143455, "gb": 143444}
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppStore/3.0"


def get(url, headers=None, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def hints(country, prefix):
    url = ("https://search.itunes.apple.com/WebObjects/MZSearchHints.woa/wa/hints?clientApplication=Software&term="
           + urllib.parse.quote(prefix))
    data = plistlib.loads(get(url, {"X-Apple-Store-Front": f"{STOREFRONTS[country]},29"}))
    time.sleep(0.25)
    return [h["term"] for h in data.get("hints", [])]


def depth(country, term):
    """Shortest prefix (in letters) whose suggestions include the term, None if never suggested."""
    t = term.lower()
    for n in range(2, len(t) + 1):
        if t[n - 1] == " ":
            continue
        if t in (h.lower() for h in hints(country, t[:n])):
            return n
    return None


def top(country, term, n=10):
    url = ("https://itunes.apple.com/search?entity=software&limit=%d&country=%s&term=%s"
           % (n, country, urllib.parse.quote(term)))
    res = json.loads(get(url))["results"]
    time.sleep(0.4)
    return [(r["trackName"], r.get("userRatingCount", 0), r.get("primaryGenreName", "")) for r in res]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["hints", "depth", "top", "batch"])
    ap.add_argument("country", choices=sorted(STOREFRONTS))
    ap.add_argument("term")
    ap.add_argument("-n", type=int, default=10)
    a = ap.parse_args()
    if a.cmd == "hints":
        print("\n".join(hints(a.country, a.term)))
    elif a.cmd == "depth":
        d = depth(a.country, a.term)
        print(f"{a.term}\t{d if d else '-'}\t{len(a.term)} letters")
    elif a.cmd == "top":
        for name, ratings, genre in top(a.country, a.term, a.n):
            print(f"{ratings:>8}  {genre:<14} {name}")
    else:
        for line in open(a.term):
            term = line.strip()
            if not term:
                continue
            d = depth(a.country, term)
            t3 = "; ".join(f"{n} ({r})" for n, r, _ in top(a.country, term, 3))
            print(f"{term}\tdepth={d if d else '-'}/{len(term)}\t{t3}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
