---
name: social-account-ops
description: "Use when running an app's own TikTok / Instagram accounts day to day: bio and link rules for new accounts, a cadence plan, which formats distribute on fresh accounts, sounds and AI labels, engagement-bait risk, the post-stats learning loop. Triggers: \"new account\", \"post schedule\", \"what are we posting today\", \"why 0 views\", \"link in bio\"."
---

# Social account operations — how to run the accounts

Scope: content, cadence as a plan, and measurement. Not covered: how posts are physically published. Out of scope on purpose: anything meant to
make automation look human or to dodge platform checks (scroll/warm-up scripts, timing jitter, device or network
choices for that purpose). If asked for those, say this skill doesn't cover them.
Hard lines: one honest brand/character per account; AI content labelled; no fake endorsements; sign-ups, SMS
codes, CAPTCHAs, passwords and payments are always the owner's.

Your own cases for this skill live in `local/skills/social-account-ops/` (git-ignored, see `local.example/README.md`).
Read them first if they exist (incident log, cadence decisions, per-account baselines); append the outcome of
each incident or plan change there.

Files: `scripts/stats_tick.py`, `scripts/cadence_plan.py`, `scripts/tt_stats.py`, `templates/learning-loop.md`;
reference data in `references/cadence-slots.md`, `references/incident-log.md`.
Handles: the app's `social` block in `local/apps.yaml`; paths: `../social-research/references/env.md`.
Live state per app: `<app repo>/growth/accounts.json` (every post: file, status, scheduled_at, url, sound),
`growth/metrics/posting-log.md`, `growth/metrics/decisions.jsonl`.

## 1. New account

- Bio on day one: no link, no 👇 pointing at one; end with «Search <exact App Store title> on the App Store».
  Add the link after a few posts and about a week. TikTok bio links need 1K followers → name the exact title in captions.
- Avatar/cover in the series' own palette.
- A first post can get 0 views for 30 h with "No outstanding issues" and the second 100 in 3 h.
  Don't judge a format on an account's first post.
- Separate account effect from content effect before dropping a format: a format that took another app account
  to 7/16 posts ≥ 250K can stall under ~200 on a brand-new account. Next step: post the same clip as a Trial Reel
  on an established account and on TikTok.
- One audience/angle per account; never the same format on two accounts; each post is a fresh take.
- Character accounts: the product may appear if the owner says so; story-serial accounts keep it out
  («No product in the video», `interactive-serial-reel`).

## 2. Cadence and slots

Rules, windows and what slot data tends to show: `references/cadence-slots.md`. Short version:
- 1/day in an account's first week → 2/day → 2/day with every other day 3.
- Two windows in the audience's zone: day (US morning/lunch, 07:35–13:25 ET) and night (US evening,
  16:35–20:55 ET). No US-early-morning slots.
- Re-time the whole queue:
  ```
  cd <app repo>/growth
  python3 tools/cadence_plan.py --tz <owner IANA zone>             # dry run → table + metrics/schedule-cadence.json
  python3 tools/cadence_plan.py --tz <owner IANA zone> --apply     # writes scheduled_at / slot_kind into accounts.json
  python3 tools/cadence_plan.py --keep 250                         # keep all scheduled posts, append new ones at the end
  ```
  Show the owner the table (or a PNG) and wait for «apply» before `--apply`.
- Measured on ~120 posts: day vs night average score is a wash (≈1.1 both) — slot tuning is not where the reach is.

## 3. Formats that distribute

- **Photo-mode carousels on fresh accounts: 0 distribution.** The same slides as a slideshow video (2.8–4.5 s per
  slide, 18–22 s total) got ~100 views in an hour. Default = slideshow.
- Native screenshot templates only (iMessage, Tweet card, iOS lock screen, Screen Time, ChatGPT) — "more like a
  screenshot from the app". A public figure or chatbot in a template never names or recommends the app —
  that would be a fabricated endorsement; the app goes in the caption. Initials, never a real person's photo.
- Read the best-scoring templates from `learn_tags.json` (decks and charts have scored 2–2.6× the account median;
  plain UGC demos ~0.9×).
- Copy proven hits frame by frame in structure — research via `social-research`.

## 4. Sound and labels

- Narrated videos: no added track or the track at 0–10%. Otherwise a Hot top-5 track, not one sound everywhere
  (one track on every post reads as a template).
- Set the sound in the app at posting; an upload's reference sound can get swapped for a random «original sound».
  After posting, `python3 tools/tt_stats.py <url>` → check `music_id`.
- If the planned track has left Hot, Hot #1 is an accepted fallback — write it into `sound_actual`.
- Switch on the AI-generated label for AI content.

## 5. Engagement-bait risk

- A serial's views are ~99.8% non-followers, i.e. recommendations. Instagram (May 2024 @Creators) won't recommend
  content that "explicitly asks for engagement through shares, comments, tags" — example: comment a specific word.
- One-word comment vote: tolerated in practice (every 2–19M serial in a teardown of 1M+ serials uses it).
- Direct "send this to someone who…" plate: the exact named pattern → tell the owner before using it; prefer a personal
  question («Who gets your contract?»).
- Aggressive selling in captions: an account whose 1.8M clip sold the app in a long caption got deactivated.

## 6. Learning loop (measurement)

Collector: `scripts/stats_tick.py`, launchd every 30 min (label `dev.<app>.tiktok-stats`, log in `~/Library/Logs/`;
`OWNER_TZ` sets the zone of the logs). Reads young posts often (< 6 h every tick; 6–48 h hourly; 2–7 d every 6 h;
then daily), interpolates views at 1/3/24 h.
- **score** = views at the latest checkpoint ÷ median of the same account's posts at that checkpoint (needs ≥ 2 posts).
- **hot** = ≥ 2× the account's 3 h (or 1 h) median **and** ≥ 50 views, within 12 h. **flat** = score < 0.3 after 24 h. **zero** = 0 views after 24 h.
- Outputs: `metrics/signals.txt`, `metrics/dashboard/learn_posts.json`, `learn_tags.json` (per template/sound/slot/ET-hour/slides/kind), `decisions.json`.

Rules at each review (`templates/learning-loop.md`):
1. Hot → part 2 in that account's next free slot (same template, new angle). E.g. a post at 5.5× the account
   median in 3 h → its continuation moves up to the next slot.
2. Explore/exploit 70/30; with < 3 scored posts per variant, keep alternating.
3. Flat/zero × 3 in a row → pause that template on that account.
4. After ~6 posts per account shift the D/N mix to the better slot, keep ≥ 1 in 4 in the weaker one.
5. Never change a post in the 45 min before its slot; never delete a published post.
6. Log every plan change as one line in `metrics/decisions.jsonl` `{at, account, what, why}` — in the owner's language, with the number.
Check whether a hot signal is a format switch before cloning the topic (the first slideshow after zero-view
carousels looks hot because of the format, not the topic).
0-view carousels give no signal; with 2 posts/day/account the first stable read takes about a week.

Beyond views: when the public numbers plateau, pull Studio analytics (sources, avg watch, drop point) — see
`../social-research/references/own-retention-pull.md`. Weekly, installs per 1K views from PostHog (the app's
`posthog_project_id` in `local/apps.yaml`) against the install baseline: big reach can leave installs flat.
Instagram: views from the profile `/reels/` grid; sends, skip rate, retention only from the owner's Insights screenshots — ask.

## 7. Before blaming content

Read `references/incident-log.md` and your local incident log first. A post more than 45 min past its
`scheduled_at` is re-slotted and logged, not posted late. Wrong sound → `tt_stats.py <url>` and compare `music_id`.
Empty caption → fix the caption before judging the post. Only then look at content (Studio pull, learning loop).

## Lessons

- First posts in your own style go flat (~135 views) → copy proven hits frame by frame.
- Photo carousels get 0 views on fresh accounts; a slideshow video of the same slides gets distribution.
- An account with 0 on every post gets paused, not fed more content.
- Many posts cut from the same few clips cap an account at ~250 views; one fresh take per post.
- "A pause usually helps" an account is folk wisdom with no evidence. Say "hypothesis" or say nothing.
- No link in a new account's bio for the first week.
