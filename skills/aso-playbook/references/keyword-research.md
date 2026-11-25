# Keyword research: tools, calibration, the record

## The four signals and how they disagree

| Source | Cost | What it is good for | Known failure |
|---|---|---|---|
| App Store autocomplete (`scripts/aso_probe.py`, MZSearchHints, header `X-Apple-Store-Front: <id>,29`) | free | demand order among terms with a shared prefix; real typed spellings | not a volume; only comparable inside one prefix |
| Apple Ads popularity (console dots 1–5, GraphQL 0–100) | free with an Ads account | Apple's own demand | dots are US whatever the countries; GraphQL score is global, floor 5 |
| Northstar MCP (`http://127.0.0.1:21517/mcp`, `open -a Northstar` first) | free, unlimited | demand pre-filter: NS pop < 35 skip, ≥ 40 proceed | slow (≤ 2–3 kw per call, 90–120 s timeout); difficulty doesn't separate cracks from walls; has write tools (`set_metadata`, `push_to_asc`) — never push without the owner's ok |
| AppKittie `get_keyword_difficulty` | paid credits per keyword | top-ranking apps + their review counts (the real wall) | credits run out (HTTP 402); overrates generic terms, underrates brands |

Calibration: NS pop ≈ AppKittie pop minus 15–30. A third-party "75" can be Apple's 1 dot; Apple's 3 dots is the
ceiling for most niches (only mass brands/categories reach 4). Spelling matters: «abc mouse» 4 vs «abcmouse» 1;
«jigsaw puzzle» 3 vs «jigsaw puzzles» 1. Score ≠ impressions: a term scoring 6 can bring most installs while one
scoring 27 gets zero impressions at the same bid.

## aso_probe.py

```bash
python3 scripts/aso_probe.py hints mx "geo"                 # autocomplete for a prefix
python3 scripts/aso_probe.py depth us "geography game"      # letters typed before it is suggested; "-" never
python3 scripts/aso_probe.py top fr "drapeaux quiz" -n 10   # name, ratings, genre of who ranks
python3 scripts/aso_probe.py batch de terms.txt             # depth + top-3 per line
```
Storefronts in the script: us 143441, fr 143442, de 143443, it 143450, es 143454, mx 143468, br 143503,
pt 143453, ca 143455, gb 143444. It sleeps between calls — don't parallelize.
Where you rank (no tool): iTunes Search API top 200 per term.

## The research record (one per locale, e.g. `appstore/aso/es-MX.md`)

| Term (mx) | Depth | Top 3 (ratings) |
|---|---|---|
| paises | 3/6 | three apps with 100–350 ratings |
| geografia | 4/9 | 260–660 ratings |
| stickers | 8/8 | a sticker maker with 325k — wrong intent |
| quiz geografia | - | never suggested |

Then: read ("top apps have 7–700 ratings → winnable"), what went into name / subtitle / keywords, what was
dropped and why.

## Rules from practice

- Low difficulty does not mean the term fits the app: terms with the wrong intent rank nowhere and bring churn.
  Re-check after three months and remove them.
- When the owner asks for an anomaly ("pop ≥ 85 / diff ≤ 10") that a sweep of hundreds of keywords doesn't find,
  say so early; report the best spreads instead.
- Brand collisions: check who owns your brand word and words that autocorrect to common words (a misspelled
  geo-game name → «travel», a pun name → «horoscope»). Add autocorrect targets as exact negatives in Ads; a term
  that is another app's name (a hypermarket, a telecom) gets impressions and no taps.
