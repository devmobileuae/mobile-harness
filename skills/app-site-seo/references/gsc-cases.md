# GSC patterns — baseline, retargets, rewrite, consolidation, indexing

Keep each site's dated numbers in `local/skills/app-site-seo/`; this file holds the patterns.

## The baseline review

| Site | Clicks | Impr | Avg pos | Verdict |
|---|---|---|---|---|
| <site> | 90-day | 90-day | | e.g. "33 thin pages Discovered – not indexed → fix thin pages, not more pages" |

Typical verdicts: young site (< 8 weeks) → keep writing; impressions rising, clicks flat → CTR problem,
retarget; many pages not indexed on a link-poor domain → authority-bound, build a reference cluster and links,
not more templates; one page slid → refresh first.

## Retarget (snippet → the query the page already ranks for)

In GSC, filter to the page (`&page=!<url>&breakdown=query`), find queries at pos 3–10 that the title does not
contain, put that phrase first in title/H1/meta/OG/Article headline, add the missing visual if the query implies
one. Re-check in 3–4 weeks.

| Before (90d) | Change |
|---|---|
| "<x> pyramid" variants ≈ 365 impr @8–10, 0 clicks; page described the pyramid in a text list | title leads with "<X> Pyramid", added an SVG pyramid with alt text |
| 1,000 impr @6.4; 75-char title truncated; the biggest variant names the author | 57-char title with the variant word |
| tool-intent variants at pos 75–99 on a how-to page | new tool page (tool above the fold, 500–800 words, WebApplication schema), cross-linked |
| a query split between a guide and a post | pick one target, add a section answering it, the other links to it |
| a format query on a template page | title/H1 lead with the official format name; requirements rebuilt from the official source |

## Rewrite (a page that slid)

Symptom: weekly series drops from pos 7–8 to 14–27 while the 90-day average still looks fine. Rewrite in place
(same URL): the visual its queries ask for (inline SVG chart + table), a section per sub-topic, FAQ + FAQPage
schema, cited sources, visible "Updated" date + `dateModified`, new internal links; request indexing. Recovery to
pos 3–8 within days is common.

## Consolidation

When two pages split one intent and Google already lands the queries on one: 308 the loser (and its downloads)
into the survivor, fold the loser's best tips/FAQs in, add the modifiers it ranked for ("free / fillable /
sample") to the survivor's title. Do **not** noindex zero-impression pages: they are not indexed anyway, so
nothing is saved, and it closes the door on them.

## Thin/duplicate or crawl demand?

Measure before blaming quality: on built HTML inside `<main>`, boilerplate share and max pairwise 5-gram Jaccard
(Google folds pages at ~0.5+; 0.05–0.10 is not duplicate). Then read last-crawl dates of "Crawled – not indexed"
(Google not back for months = crawl demand), never-fetched URLs, and internal-link counts in GSC → Links. Fix =
internal-link registry + links + time. Tracking params (`/?ref=…`) in "Crawled – not indexed" are handled by the
canonical — no fix.

## Request-indexing quota

One quota per Google account across all properties and sessions: ~10–12/day, intermittent "Quota Exceeded"
(looks like a rate/per-property cap). Inspect first; skip anything crawled after the change. Priority:
retargeted pages with the most impressions → pages Google has not seen since the change → "Discovered". One
session owns the queue file.
