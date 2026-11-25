---
name: metric-iteration
description: "Use when deciding what to change next in a live app or content channel, instead of a big redesign: one change tied to one PostHog/RevenueCat number with a dated baseline, read it, pick the next. The daily anomaly check is app-pulse. Triggers: \"what do we do next\", \"redesign the main screen\", \"why isn't it growing\", \"check posthog\", \"they don't pay\"."
---

# Metric iteration — one change, one number, one read-out

Your own cases for this skill live in `local/skills/metric-iteration/` (git-ignored, see
`local.example/README.md`). Read them first if they exist; append the outcome of each round/incident there.

Why this skill exists: rounds of multi-concept screen redesigns end with "I don't like any of it" and nothing
shipped, while the data usually already points at a narrower leak (one level that 30 people open and 3 finish;
people who finish it on day 0 return 2–3× more often). Fix the leak, one change at a time.

Files:
- `references/funnels.md` — how to write down an app's funnel, event quirks and dated baselines.
- `references/hogql.md` — reusable queries (taxonomy, per-person day, depth segments, per-item funnel,
  day-0 predictors, cohorts, reach, first hour by version, release before/after, day-N retention).
- `references/portfolio-snapshot.md` — the "am I making it?" read across all apps.
- `references/content-channel.md` — judging posts by installs per 1K views.
- `scripts/hogql.py` — REST runner when the PostHog MCP is down.
- `templates/hypothesis-card.md`, `templates/readout.md`.

App ids (`posthog_project_id`, `revenuecat_project_id`, `asc_app_id`, `bundle_id`) come from `local/apps.yaml`.

## 0. Connect and isolate real users (do this every time, it bites every session)

1. PostHog MCP tool is `exec`. The active project may be **shared across all sessions on the machine** and start
   wherever it was left. Always `exec "switch-project <posthog_project_id>"`, then
   `exec 'call execute-sql {"query": "..."}'`. Check the id, never the project name ("Default project" is common).
   If `learn` does not work for the client, skip it. Switch back if another session depends on the project.
2. Write a real-user filter per app and keep it in the app's local funnel note:

| Keep | Drop |
|---|---|
| store bundle: `properties.$app_namespace = '<bundle_id>'`, or `build_type != 'debug'`, `$is_testflight != true` (nulls pass so SDK lifecycle and `rc_*` events stay) | debug/Xcode bundle, emulators/simulators, the owner's own country `coalesce($geoip_country_code,'') != '<owner country>'` |

3. Never trust a project-level test-account filter (it can be inverted and show only the owner). Filter in SQL.
4. `Application Installed` often fires before super-props are registered: no `app_version`, `build_type`,
   `cohort`. Filter installs by namespace; take the version from `$app_version` or the person's next event.
5. Drop Apple's review device by hand: US, no city / Cupertino / San Mateo, tz America/Los_Angeles, model like
   iPhone99,7, appears minutes after each submission, installs and never becomes active, or taps buy and cancels
   in ~30 ms. Not a crash, not a user.
6. Apple Ads counts an install at download; PostHog sees a person at first open. "I see them in ASA" usually means
   they have not opened the app yet.
7. Ask what traffic was running (ASA, geo campaigns, a post) before calling anything "organic".

## 1. The loop

### Step 1 — Pull the day/week (5 min)
- "What are the new users doing?" → one row per new person today (Q2) and a summary: how many came (by country,
  version), finished onboarding, reached the core action, paywall shows (users, not events), purchases, rating
  asks, who got hooked.
- For a funnel read, run the taxonomy (Q1) first — event names drift between versions.

### Step 2 — Find the leak
- Depth segments (Q3) → which segment holds most people and how long they stayed.
- Per-item funnel (Q4) and first item + where they came from (Q5) → the specific object that kills.
- Day-0 predictors (Q6 / Q8) → which day-0 behaviour predicts return. That behaviour becomes the metric.
- Pick the step with the biggest drop that **one** change can move. Write the leak in one plain sentence with
  numbers ("level X, second read in a row: 3 opened, 0 completed, left").

### Step 3 — Hypothesis card (before any code; `templates/hypothesis-card.md`)
Show it to the owner: change (one sentence), metric with exact events and denominator, baseline with n and dates,
expected size, split, read date, kill threshold, confounds.

### Step 4 — Instrument first
If the event is missing, adding it is iteration 0 (e.g. "first attempt on step N", per-step time). Check for
double-firing events before trusting counts. Document every new event in the app's `docs/analytics.md` in the
same commit.

### Step 5 — Ship one change
- On top of the live release branch (cut from the shipped build; never an abandoned redesign branch). Branch per
  iteration.
- One change per build when you want a clean read; bundle only invisible fixes (analytics, crash).
- If the owner forbids remote flags (nothing remote may change what App Review saw), split locally:
  `hash(install_id) % 2` stored at first launch, sent as a super-prop.
- Build/upload is `mobile-feature-delivery`; the owner submits for review himself.

### Step 6 — Read (`templates/readout.md`)
- Compare like with like: first hour after install per version (Q9), or install-day cohorts with matured days
  only (Q7; Q11's `el_dN` eligibility columns).
- Size limits at small-app volume (n per arm = 7.84 × [p1(1−p1)+p2(1−p2)] / Δ²):

| Effect | n per arm | Time at 25 installs/day 50/50 |
|---|---|---|
| opt-in 20% → 35% | 135 | ~11 days |
| D1 18% → 25% | 536 | ~43 days |
| D1 18% → 21% | ~2,730 | infeasible |

  So: decide on the step metric the change touches (opt-in, core action on day 0); D1 is a guardrail.
  Under 100 per arm say "a direction, not proof". A 0/7 vs 49% gap is still worth naming (p≈2.5%).
- Before/after windows are poisoned by ads on/off, new geo campaigns and other changes in the build. Name them.

### Step 7 — Next
Keep / revert / extend, then back to Step 1. End the message with ONE question and your recommendation; owners
decide fast that way and dislike long deliberation.

## 2. Funnels and baselines

Per app, keep in `local/skills/metric-iteration/`: the activation event (e.g. first task completed on day 0, first
level completed on install day, first forecast viewed → trial), the event list with quirks, and dated baselines.
Format: `references/funnels.md`. Re-pull a baseline older than the last release before using it.

## 3. Portfolio variant (`references/portfolio-snapshot.md`)

When the question is "am I making it?" or "what to do with the portfolio", do not pick a screen. Pull RevenueCat
`get-overview-metrics` for every live project, revenue / customers_new / trial_conversion charts, iTunes lookup for
ratings, strip the owner's country. If every app gets 40–150 installs a month and has ~0 ratings, the bottleneck is
installs and ratings, so iterations at this level are traffic and rating experiments (ASO, review-prompt mechanics,
ASA, content), not features. Main app = highest installs/day × revenue/user over two weeks.

## 4. Content-channel variant (`references/content-channel.md`)

Same loop, a series instead of a screen. Metric = **installs per 1K views** per account (store installs above the
daily baseline, on days with no ads change), not views. A serial can collect 150K views and add zero installs.
Without `ct=` campaign links per account or a CPP there is no attribution; set those up before asking for more
volume. Reach per series (median over ≥10 posts) is a secondary number and belongs to `growth-analytics`.

## 5. Traps in the data (each one produces a wrong statement sooner or later)

- An event that fires per tap (`paywall_shown` on every locked item) inflates counts. Count users.
- "Offerings failed" panics usually come from debug builds with no products. Filter namespace first.
- A day with zero events project-wide is an ingest gap, not behaviour. Check all events per day.
- RevenueCat v2 API can show stale prices or `duration = null`; a "default plan is wrong" claim needs the code and
  the store checked. Read the code and the store before naming a cause.
- "Event never fired" can mean the owner's test purchases predate the analytics build.
- "The few who came are really using it" without n is not a finding. Always show event counts and n with a claim.
- Correlation sold as cause: notification opt-in users return more, but they are also the ones who completed the
  core action. Discount the causal share (a skeptic's ~10 pp, not the raw gap).
- Before loosening a trigger, count its reach (Q8b): lowering a rating threshold may move reach only 25% → 27%.

## Lessons

- **Redesign rounds don't decide.** No new multi-concept rounds for a screen unless the owner asks; one change,
  one metric.
- **The first "iteration" is often three.** If the owner bundles changes, say once that the read will be
  unattributable and write down which metric belongs to which change, then follow.
- **"They don't pay" after one day.** 1–3% of installs is normal casual conversion; at ~20 installs/day zero in a
  day is expected. Call it at 300–500 installs on the version. Don't change price on 0 vs 1 purchase.
- **Run a small conclave before code when a change touches a permission or money.** "Move the notification ask
  after the first win" can cut total opt-ins (needs a far higher yes rate on a smaller reach); usually keep the
  early ask and re-ask "Not now" users after the first win.
- **A paywall stack kills activation.** Onboarding paywall → recovery offer → paywalls on every tap can drop
  day-0 core action from ~70% to near zero. No paywall on day 1 except the onboarding one.
- **Content without attribution or product in frame is not acquisition.** Stop a format after the first
  test-group reach (100–130 views vs thousands), not after ten posts.
- **Strip the owner's country before any verdict.** A third of a small app's users can be the owner and friends.
- **A review prompt can exist and still be broken** (re-asks every launch, burns its one try in onboarding). Read
  the review-prompt code before recommending "add a prompt".

## Working style

- Reply in the owner's language, tables over prose, numbers with n and dates, short. Code identifiers and event
  names in English.
- Do the read, then ask one question with a recommendation.
- Commits / uploads / store versions only on the owner's explicit word.
- After every read, append a dated "Read on <date>" line to the app's note in `local/skills/metric-iteration/` so
  the next session starts from the baseline, not from zero.
