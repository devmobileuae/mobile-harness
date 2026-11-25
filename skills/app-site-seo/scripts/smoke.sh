#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Run after every push to main.
# WHAT: checks a LIVE production site the way Googlebot sees it:
#   1. robots.txt says Allow + carries the Sitemap line (prod-only gate is open)
#   2. sitemap <loc> count equals what you expect (catches a registry that lost/gained pages)
#   3. the home entry is listed WITH a trailing slash ("No referring sitemaps detected" otherwise)
#   4. home <meta name="robots"> is index, follow (not the preview noindex)
#   5. llms.txt is served
#   6. every extra path returns 200 (new routes), every --redirect pair returns 308/301 → target
#   7. every --noindex path sends X-Robots-Tag: noindex
# RUN:
#   scripts/smoke.sh https://example.app 45 \
#     --path /guides/some-guide --path /templates/landscaping \
#     --redirect /templates/lawn-mowing=/templates/landscaping \
#     --noindex /templates/cleaning-invoice-template.docx
#   scripts/smoke.sh https://www.example.app 9        # static site, www is primary
# Exit 1 on the first failed check group (prints every failure first).
# ─────────────────────────────────────────────────────────────────────────────
set -u
BASE="${1:?usage: smoke.sh <https://host> <expected-loc-count> [--path P]... [--redirect FROM=TO]... [--noindex P]...}"
EXPECT="${2:?expected sitemap <loc> count}"
shift 2
BASE="${BASE%/}"
fail=0
ok()  { printf '  ok   %s\n' "$1"; }
bad() { printf '  FAIL %s\n' "$1"; fail=1; }

echo "robots.txt"
robots="$(curl -fsSL "$BASE/robots.txt" || true)"
grep -qi '^allow: /' <<<"$robots" && ok "Allow: /" || bad "no 'Allow: /' (preview gate closed on prod?)"
grep -qi "^sitemap: $BASE/sitemap.xml" <<<"$robots" && ok "Sitemap line" || bad "no Sitemap: $BASE/sitemap.xml"

echo "sitemap.xml"
sm="$(curl -fsSL "$BASE/sitemap.xml" || true)"
n="$(grep -o '<loc>' <<<"$sm" | wc -l | tr -d ' ')"
[ "$n" = "$EXPECT" ] && ok "$n <loc>" || bad "$n <loc>, expected $EXPECT"
grep -q "<loc>$BASE/</loc>" <<<"$sm" && ok "home listed as $BASE/" || bad "home not listed as $BASE/ (trailing slash)"

echo "home meta robots"
home="$(curl -fsSL "$BASE/" || true)"
if grep -qi 'name="robots"' <<<"$home"; then
  grep -i 'name="robots"' <<<"$home" | grep -qi 'noindex' && bad "home carries noindex" || ok "robots meta has no noindex"
else
  ok "no robots meta (defaults to index, follow)"
fi

echo "llms.txt"
code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/llms.txt")"
[ "$code" = 200 ] && ok "llms.txt 200" || printf '  skip llms.txt -> %s (site ships none)\n' "$code"

while [ $# -gt 0 ]; do
  case "$1" in
    --path)
      code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE$2")"
      [ "$code" = 200 ] && ok "$2 200" || bad "$2 -> $code"; shift 2;;
    --redirect)
      from="${2%%=*}"; to="${2#*=}"
      read -r code loc < <(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$BASE$from")
      { [ "$code" = 308 ] || [ "$code" = 301 ]; } && [ "$loc" = "$BASE$to" ] \
        && ok "$from -> $code $to" || bad "$from -> $code $loc (want 308 $BASE$to)"; shift 2;;
    --noindex)
      curl -sI "$BASE$2" | grep -qi '^x-robots-tag:.*noindex' && ok "$2 X-Robots-Tag noindex" || bad "$2 missing X-Robots-Tag"; shift 2;;
    *) echo "unknown arg $1"; exit 2;;
  esac
done

exit $fail
