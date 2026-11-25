---
name: social-research
description: "Use when researching TikTok / Instagram Reels for an app's content: sweep a niche with a logged-out scraper, rank outliers by plays/followers, check content-market fit on whole accounts (series median, not one hit), write ranked hypotheses. Triggers: \"research TikTok\", \"find outliers\", \"what's taking off right now\", \"break down a competitor's Insta\", \"what format to shoot\"."
---

# Social research — the pipeline

Every sweep follows the five steps below. Scripts are in `scripts/`; calibration numbers are in `references/`.

Your own cases for this skill live in `local/skills/social-research/` (git-ignored, see `local.example/README.md`).
Read them first if they exist (past sweeps, own-account baselines, which paid tools have credits); append the
outcome of each sweep there.

Read first: `references/env.md` (what to record per app: research root, accounts, data tools' state). The app's
handles are under `social` and its PostHog project under `posthog_project_id` in `local/apps.yaml`.
`tools/` in the commands = `<app repo>/growth/tools/`; for a new app copy this skill's `scripts/` there.

## 1. Sweep (free, logged out)

```
cd <app repo>/growth
mkdir -p research/<topic>-<yyyy-mm-dd>
python3 tools/tt_scrape.py search "lock in" "winter arc" "discipline app" ... \
        --pages 5 --out research/<topic>-<date>/search.jsonl
```
- 20–22 niche queries per sweep → ~2,000 posts (10 queries → ~700).
- **~15 rapid queries → `blocked`, and an immediate re-run is blocked too.** Split into batches of ≤ 10
  with long gaps; never loop retries.
- Each row: id, author, author_followers, plays, likes, comments, shares, saves, created, duration, photo, slides, music, desc, url, query.
- Paid fallbacks only if the owner OKs credits: vidIQ `instagram_tiktok_outlier_search` (~5 credits), AppKittie
  `list_organic_content` (1 credit) for an app niche shortlist. Say the cost before calling.

**Instagram** (usually the owner's personal session — too much scraping risks a ban):
at most ~8 pages in their logged-in Chrome, with pauses, no fetch loops (16 searches + ~220 post pages is too much).
Media and likes/comments come from `yt-dlp` without login (`yt-dlp -J <url>`, 3 s between calls). Logged-out IG gives
likes/comments only; views ≈ 10–30× likes. Post date from the shortcode: decode base64url → `id >> 23` + 1314220021721 ms.

## 2. Rank outliers

Filter (python one-off over `search.jsonl`):
- posted in the window (45 days for a trendwatch; 24 days for "what works right now"; 24–75 days for settled numbers);
- plays ≥ 50K (trendwatch) or ≥ 150K (small-accounts sweep);
- sort by **plays ÷ author_followers**; for the format question keep accounts ≤ 10K followers — their hits are format, not audience.

Typical yields: ~2,000 → ~220 (≥ 50K, 45 d) → top ~17 studied; ~2,000 → ~30 (≥ 150K, ≤ 10K followers).
Check the format mix of fresh outliers (e.g. photo carousels can be ~5% when a niche's reach is video).

## 3. Check content-market fit (the step that kills most "trends")

```
python3 tools/tt_scrape.py user <handle1> <handle2> --pages 3 --out research/<topic>-<date>/user-<h>.jsonl
python3 tools/tt_stats.py @<handle>            # followers / likes / video count
```
- Pull **every** candidate account and compute median + max over its last 10–30 posts, split on-format vs off-format.
- CMF = high median (hundreds of thousands on a 200K account; ~180K on a ~1K account that found a format).
- Luck = one spike: median 3K, max 700K. Dead = the famous clip isn't in the last 9 posts.
- Also report the **format-wide** median: a wave can have dozens of posts ≥ 1M and a ~6K median → "post several variants".
- Calibration tables: `references/outliers.md`.

## 4. Watch the winners without credits

```
yt-dlp -o 'media/%(id)s.%(ext)s' --write-info-json <url>         # tt_scrape.py download can break; yt-dlp works
python3 tools/ref_prep.py tiktok refs.json media prep          # sheet.jpg, hook.jpg, transcript.json, meta.json
python3 tools/ig_prep_cuts.py research/<topic>-<date>          # IG reels: + scdet cuts, avg_shot, likes, upload_date
```
Then **open every hook.jpg and sheet.jpg** and write per reference: what moves at 0.0 s, on-screen text (OCR by
reading the frame), words per minute (Whisper), cuts per second, the payoff, the end card / CTA.
Measured patterns worth checking against: cartoon serials cut every 1.5–3.3 s; most hits have no silence at
0.0 s (below −38 dB in ~4 of 5); IG quiz metronome ~5 s per item.
Virality-predictor tools and paid video analysis are not worth credits (they score a 19M hit and a 2K flop the same).

## 5. Comments → script beats

- Read top comments under the 5–9 key videos (logged-out TikTok page / IG post page, a few pages).
- Comments are 0.01–0.4% of views and don't track reach; likes run 4–8%. Shares/sends are not public — don't claim them.
- What to copy: the "my brain step by step" template («my brain 1. china 2. china 3. wtf…»), locals answering
  («I was born there, ask questions»), requests for the next part, «game name?» (a bridge to the app), the fight
  in the comments.
- Paste them verbatim into the brief under "Audience language".

## 6. Write the brief

Folder files: `building-blocks.md` (or `findings.md`), `hypotheses/<n>-<slug>.md`, raw jsonl, prep.
The shape is in `references/brief-example.md`. Required parts:
1. Collection log **including what was not done** (tools out of credits, tag pages = top of distribution, anti-bot stop).
2. 3–5 findings, each with numbers.
3. Pattern table — a pattern counts only at ≥ 2 authors or ≥ 3 posts of one author; column "stability" = median / n of n.
4. Visual formulas, text-hook templates, audience language (verbatim).
5. Ranked hypotheses (character, visual formula, meaning formula, hook + caption, why with numbers, how the app fits, risks).
6. Hand-off: which hypothesis goes to `growth-production` / `interactive-serial-reel` / `conclave`.

Output block for the chat answer (in the owner's language):
```
Format: <name>   window: <dates>   sample: <n posts / n accounts>
Format median: 5.8K   share ≥1M: 13%
Accounts: @a (median 662K, CMF), @b (median 3.3K, max 735K — luck)
First 3 s: <what moves at 0.0 s + text>
Comments: <3 quotes with likes>
For <app>: <how, without forcing the product into the story>
Cost: vidIQ 0, paid scrapes 0
```

## 7. Judge success by installs, not views

- PostHog `Application Installed` per day (the app's `posthog_project_id` from `local/apps.yaml`) against the
  app's baseline. A serial with ~150K views can move installs by ~0 on a small app; a few bio taps per 5K views is normal.
- So every recommendation states installs per 1K views when known, and prefers formats where the product is the
  punchline (skit + app demo: millions of views on accounts with a few hundred followers) when the goal is installs.
- Series: quote the decay before recommending one (`references/serial-decay.md`): ep 2 loses 43–74%, the pilot
  carries 35–68%, a new premise resets reach, clones get ~7× less.
- When reach itself is the problem, first look at your own retention (`references/own-retention-pull.md`): if
  nearly every post loses most viewers at 0:01–0:02, fix the first second before researching more hooks.

## Lessons

- First posts "in the style of" a winner get ~130 views. Copy proven hits frame by frame in structure, change the content.
- TikTok search rate-limits after ~15 queries; re-runs right away are blocked too.
- "A pause usually helps an account" is folk wisdom. State it as a hypothesis with no number, or don't state it.
- Verify both data points exist before computing a ratio (an "ep 2 loses 75–90%" figure came from a grid where ep 2 wasn't visible).
- Scraping IG through the owner's Chrome too hard gets "don't go that hard". Few pages, pauses, yt-dlp for media.
- A competitor's reels tab can be 3 pinned 6–14M hits with 3–30K after them while growth runs on Meta ads. Always
  look past pinned posts and check the Meta Ads Library before calling a competitor's organic a model.
- A format proven elsewhere can stall under ~200 views on a brand-new account — separate account vs content before dropping it.
- `tt_scrape.py download` can break ("no ssr"); yt-dlp without login works.
- A "wave" can be ten months old. Check the post date before saying "trend".
- Paid sources (vidIQ, ScrapeCreators, AppKittie) can all be dry at once and TikTok shows an anti-bot page after
  ~40 tag-page loads. Plan research so the free path (tt_scrape + yt-dlp) is enough; tell the owner which paid source is dry.
