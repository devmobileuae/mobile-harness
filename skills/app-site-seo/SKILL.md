---
name: app-site-seo
description: "Use when building, auditing or growing an app's SEO site: keyword sweeps, successor pages, programmatic pages, robots/sitemap/JSON-LD, Search Console retargets and consolidations, indexing quota, outreach. Triggers: \"SEO\", \"app site\", \"GSC\", \"why isn't it indexed\", \"should we write articles\", \"keywords for the site\"."
---

# App-site SEO

The site exists to rank for intents the app serves and send installs to the store. For small apps where paid
CAC is far above LTV, these sites are the channel, and they grow slowly.

Your own cases for this skill live in `local/skills/app-site-seo/` (git-ignored, see `local.example/README.md`).
Read them first if they exist (sites, repos, deploy rights, GSC baselines, sweeps, outreach logs); append the
outcome of each round/incident there. Per-app fields (`site_url`, `vercel_project_id`, `asc_app_id`,
`app_store_url`, `play_url`) come from `local/apps.yaml`.

What usually works: **successor pages for dead apps** (a retired app's name with a "what to use instead" page
can bring most of a young site's clicks), **snippet retargets** to queries a page already ranks for, **one
reference guide on a fresh regulation**. What usually does not: head terms, ~128-word programmatic pages, cold
outreach from a new domain.

**Read first, every time:** the site's notes in `local/skills/app-site-seo/` (repo, host, GSC account, deploy
rights), then the site repo's own `keywords.md`, content plan, GSC notes and indexing queue.

## 1. Decide what the site needs

"Should we write more articles?" is answered per site, from GSC, not by default:

| Signal in GSC | Do | Not |
|---|---|---|
| < 6–8 weeks of data, few pages | write: pillars + satellites | — |
| page at pos 3–10 for a query its title lacks | retarget title/H1/meta (+ the visual the query implies) | a new article |
| page slid (weekly series, not the 90-day average) | rewrite in place, keep URL | a sibling page |
| tool intent (pos 75–99) on a how-to page | separate tool page, cross-link | stuffing the guide |
| two pages split one intent; Google already picked one | 308 the loser into the survivor, fold content | noindex |
| "Discovered/Crawled – not indexed" with decent pages | internal links from ranking pages + home, request indexing, links | more pages |
| thin programmatic pages (~128 words) not indexed | raise them through the content gate | more of them |

Worked patterns for every row: `references/gsc-cases.md`.

## 2. New site / new cluster pipeline

1. **Listing → `app.md`.** Scrape the store page (+ `https://itunes.apple.com/lookup?id=<id>&country=us`):
   name, ids, price, features, screenshot list. This is the copy source of truth; never invent features or prices.
2. **Sweep → `keywords.md`.** Run 4–8 research agents in parallel, one per intent angle (core category,
   competitor/alternative, problem-phrased questions, privacy/brand-vacuum, crossovers). For every candidate
   **open the live Google SERP** and classify who ranks:
   - institutional / medical / brand wall → reject (write the reason down);
   - App Store listings only → it is an **ASO** term: store keyword field, not a web page;
   - real app pages → compete only with a sharper angle;
   - forums, Quora, Scribd, APK mirrors, retirement notices, 2000s gap-fill sites → **go**.
   App Store popularity (AppKittie `get_keyword_difficulty`, US, apple_mobile) is a demand proxy only.
   Output shape: home target + 8 guides with SERP evidence + 8 home-FAQ questions + rejected list with reasons
   (e.g. ~100 candidates → 1 + 8 + 8). Format in `references/keyword-sweeps.md`.
3. **Verify every "is it dead" claim before a successor page.** Check both stores return 404 and cite the date;
   a "retired" app that is actually alive (current version, thousands of ratings) is a false premise.
4. **Show the owner the keyword map before building.** He decides the home term and the guide set.
5. **Build.** Static HTML (`website/` + `templates/static/vercel.json`) or Next.js. Next.js wiring — copy from
   `templates/next/`: `site-config.ts` → `lib/site.ts`, `robots.ts`, `sitemap.ts`, `guides.ts` (link registry),
   `schema.ts` (home graph + FAQ/Breadcrumb/Article), `next.config.mjs` (redirects + noindex headers); tests from
   `templates/tests/` + `vitest.config.ts`. Static home graph: `templates/static/home-graph.html`.
6. **Content per page** (agents in writer+reviewer pairs, one keyword each): answer the query in the first two
   paragraphs, then the mechanism, then "how the app automates it", one CTA; own screenshots only (simulator
   Debug build, ~720 px WebP); FAQ visible on page when FAQPage schema is used.
7. **Gate** (`templates/tests/registry.test.ts`): title ≤ 60, meta 120–165, one H1, 2-paragraph intro ≥ 120
   words, ≥ 4 tips of 30–110 words, ≥ 7 FAQs, 6–8 how-to steps of 30–80 words, related slugs resolve. Pages
   that pass land around 2,000–2,400 words with max 5-gram Jaccard ≤ 0.10 between siblings.
8. **QA + push + smoke + GSC** (§4, §5).

## 3. Page types

| Type | Rule | Example |
|---|---|---|
| Home | one "<category> app" term; WebSite+Organization+MobileApplication graph, `sameAs` = every store listing | `templates/static/home-graph.html` |
| Successor / brand vacuum | tell the retirement story with dates, state "no affiliation", re-check every few months | `<retired-app>-app` |
| Comparison / alternatives | say plainly "we make X"; competitor facts only from their store listing/site with the check date; **no competitor logos or screenshots** | `<competitor>-alternatives`, `x-vs-y` |
| Free tool | tool above the fold, 500–800 words below, WebApplication schema; cross-link with the guide (guide = method, tool = answer) | `/<thing>-calculator` |
| Programmatic | typed registry + the vitest gate, never without it | invoice / estimate templates per trade |
| Reference / linkable asset | official-source facts, "As of <Month YYYY>", source list in code, a re-check script | statistics page, a regulation cluster |
| Blog satellite | 800–1,200 words, links its pillar in the first screen, 2/week in waves of 12, wave 2 only if wave 1 indexes | content plan |

YMYL (health, money, law): wellness framing, no medical claims, no clinical/teen/lab-level angles; money facts
pinned by tests or scripts (`expect(OFFICIAL_LIST).toHaveLength(<n>)`; `scripts/check-boe-rates.mjs` pattern).
Facts that could not be verified are left out (don't attach a settlement figure from a different case).

## 4. Technical — every item here breaks sooner or later

- Index only production: `isIndexable` = `VERCEL_ENV === "production"` unless `NEXT_PUBLIC_SITE_INDEXABLE` says
  otherwise (keeps `*.vercel.app` out until the domain exists). Static sites: never publish a preview copy on a
  public host.
- One canonical host (www or apex, the other 308s). All canonicals/OG/sitemap/JSON-LD use that host. Internal
  links extensionless (`cleanUrls`) to skip the 308 hop.
- Sitemap home = `https://host/` with the slash, or URL Inspection says "No referring sitemaps detected".
  Canonical rendering without the slash is fine — don't "fix" it.
- No `useSearchParams()` in client islands on static routes: the page renders ~50 words +
  `BAILOUT_TO_CLIENT_SIDE_RENDERING` to Google. Read the query on mount; `curl` a tool page and read the words
  Google gets.
- `X-Robots-Tag: noindex, nofollow` on downloadable files; `noindex` + robots Disallow on scaffolds
  (`guides/_template.html`). Tracking/redirect endpoints (`/get` → App Store) stay out of the sitemap.
- No SearchAction in the graph unless the site has search. Stable `@id`s (`/#website`, `/#organization`, `/#app`).
- Every page registered in one list that feeds nav/footer/home/hubs/sitemap (`templates/next/guides.ts`). A site
  with single-digit internal links in GSC will not get deep pages indexed.
- Smart App Banner: `metadata.itunes = { appId, appArgument: site.url }` (Next) on every page.
- AI-search layer: `public/llms.txt` (H1 site, one-line description, Key tools / Templates / Reference sections
  with one-line dated facts, contact) + "As of <Month YYYY>" in fact intros.
- Mobile: `.prose { min-width: 0 }` so tables scroll instead of widening the page; `img { height: auto }` in the
  reset when width/height attributes are present.
- Tests (copy `templates/tests/`): registry gate, sitemap (count, slash, no `/get`, lastmod), robots (4 env
  cases), headers (308s + noindex), guides (page file exists, hrefs unique, hub first).
- Don't run `npm run build` while a Next dev server is up — it deletes the dev server's `.next`.

## 5. Deploy and verify

Deploy rights differ per repo — record them in the site's local note: some repos let Claude commit and push
main; some deploy to production only on the owner's word; some need a "yes, deploy" per change. Ask when unsure.

```sh
npm test && npm run build                 # Next sites; static sites: open every changed page locally
git push origin main                      # Vercel deploys in < 1 min
scripts/smoke.sh https://example.app 45 \
  --path /guides/some-guide \
  --redirect /templates/old-slug=/templates/new-slug \
  --noindex /templates/some-template.docx
scripts/smoke.sh https://www.example.app 9   # static site, www primary
```

`scripts/smoke.sh` checks robots Allow + Sitemap, `<loc>` count, home with slash, meta robots, llms.txt, 200s,
308 targets, X-Robots-Tag. When a registry gains or loses a page, update the expected count in the site's notes
too. Bump `lastmod` / `dateModified` on materially edited static pages.

## 6. GSC loop

- New property: **Domain** property via DNS TXT (no token in code) → submit `sitemap.xml` → ~48 h: sitemap
  "Success", inspect home → days: Pages report ("Discovered – not indexed" is normal for a young domain) →
  1–2 weeks: Performance → 8–12 weeks: the real review.
- Note which Google account holds the properties (`/u/<n>/` in the URL) in the local note. Exact-page filter:
  append `&page=!<url-encoded full URL>` (`*` = contains) and `breakdown=query`. In the browser extension,
  Performance/Index drilldown tables keep all rows in the DOM even when paginated →
  `document.querySelectorAll('tr')` returns the whole list; strip query strings from output.
- The review: per-site Clicks/Impr/Pos for 90 days; per page queries; read the **weekly** series for the top
  pages; Index report reasons with last-crawl dates. Write the numbers into the site's local note as the next
  baseline.
- Retarget recipe: the query phrase goes first in title (≤ 60 — longer titles get truncated), H1, meta, OG,
  Article headline; add the visual the query names (an SVG chart/diagram with alt text — Google Images is extra
  surface). Re-check 3–4 weeks later.
- **Request indexing is one quota for the whole Google account**, shared by every parallel session: ~10–12/day,
  intermittent "Quota Exceeded". Inspect first (free); skip URLs crawled after the change; queue: retargeted pages
  with the most impressions → pages Google hasn't seen since the edit → "Discovered". Keep the queue in one file
  and tick it off; one session owns the queue.
- Do not read a weekend or the last 2 days of data as a trend (partial data). Compare with product analytics
  before blaming a change.

## 7. Links

Read `references/outreach.md` before proposing any link work. Summary: directories give a baseline, editorial
links come only from an asset that corrects something checkable (stale rate, repealed penalty, wrong deadline)
pitched with T3; one follow-up, then stop; never paid/PBN/badge rings/exact-match anchors. Claude drafts, the
owner sends and reports "sent"; log the same day. Expect weeks before GSC → Links shows anything.

## Lessons

- A tool page can serve ~50 words to Google through a client-side bailout. Check what Google gets, not the browser.
- GSC beats the keyword sweep after week 2: a 2-week export already shows intents (e.g. calculator queries at
  pos 75–99). Plan from it.
- A home URL without the trailing slash in the sitemap → "No referring sitemaps detected". Make it a test.
- A dozen outreach emails from a young domain can yield zero links Google sees after two months. Don't sell
  outreach as a ranking lever.
- A post can slide from pos 7–8 to 14–27 while its 90-day average looks fine; a rewrite in place can bring it
  back within days. Always check the weekly line.
- "Near-duplicate templates" is a hypothesis to measure (5-gram Jaccard), not to assume; the real cause is often
  crawl demand + few internal links. Measure before rewriting dozens of pages.
- Parallel sessions burn the shared request-indexing quota in ~11 requests. One session owns the queue.
- Data overrides old plans ("don't touch the home title" vs 139 impressions @6 for an unclaimed query); note the
  override in the commit.
- Reference pages go stale with regulations (a replaced penalty table while ranking @6). Give them a re-check date
  and a source list in code.
- Review every GSC property, not only the ones in the last plan.

## Files in this skill

- `references/keyword-sweeps.md` — the sweep deliverable format and SERP classification examples.
- `references/gsc-cases.md` — retarget, rewrite, consolidation, duplicate measurement and indexing-quota patterns.
- `references/outreach.md` — tracks A–F, directory verdicts, T1/T2/T3 + follow-up templates, ground rules.
- `templates/next/*` — site-config, robots, sitemap, guides registry, schema (home graph), next.config redirects/headers.
- `templates/tests/*` — registry, sitemap, robots, headers, guides tests + vitest config.
- `templates/static/*` — vercel.json (cleanUrls), robots.txt, home-graph.html.
- `scripts/smoke.sh` — live post-deploy check. `scripts/check-boe-rates.mjs` — fact-freshness checker pattern.
