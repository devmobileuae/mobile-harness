---
name: app-pulse
description: "Use for the daily morning health check of live apps: yesterday's PostHog, RevenueCat and Firebase numbers vs the same weekday over 4 weeks; reports only anomalies with a cause and next step. What to change next is metric-iteration. Triggers: \"pulse\", \"are the apps OK\", \"anomalies\", \"how were yesterday's metrics\", \"morning report\"."
---

# App pulse — is everything OK this morning?

The pulse answers one question in under a minute of reading: **did anything break or move
yesterday that needs action today?** Normal days get one green line per app. Only anomalies get
words.

Your own cases for this skill live in `local/skills/app-pulse/` (git-ignored, see
`local.example/README.md`). Read them first if they exist; append the outcome of each incident there.

## 0. Setup per run

- Apps, ids and filters: `local/skills/app-pulse/apps.md` (format: `references/apps-format.md`; ids
  come from `local/apps.yaml`). Read it first — the PostHog MCP may start in whichever project was
  used last, and a project's default test-account filter can be wrong (even inverted), so every query
  sets project and filters explicitly.
- Timezone: the owner's, from the apps note. "Yesterday" = the last full day in that timezone.
- Always exclude the owner's own devices (e.g. `$geoip_country_code != '<owner country>'`) and debug
  builds (filter by the store bundle/namespace).

## 1. Pull (per app)

PostHog (`exec` → `query` with HogQL; queries in `references/queries.md`):

| Metric | Why |
|---|---|
| installs (`Application Installed`, store namespace) | traffic |
| `app_open` / DAU | is the app alive |
| onboarding completion (start → finish event) | first-session leak |
| **first core action on day 0** (a habit tracker: first task completed; a puzzle game: first pack completed) | the metric that predicts return |
| `paywall_shown` → trial start | money funnel |
| event volume of the 5 key events | **0 = broken instrumentation or a broken release** |
| error tracking / `$exception` count | stability |
| `app_version` share | did a new release ship yesterday |

RevenueCat (`get-overview-metrics`, `get-chart-data`): new trials, trial→paid, new paid, revenue,
refunds, active subscriptions. If an app sends no purchase event to PostHog, RevenueCat is the only source.

Firebase (only for apps that use it): Crashlytics crash-free users and new issues via the Firebase
MCP/CLI when the tools are available; Remote Config update-gate value (`appUpdate`). If the tools
aren't connected, write "Firebase: not checked (no tools)" — never imply it is green.

## 2. Detect

Compare yesterday with the **same weekday of the last 4 weeks** (median) and the trailing 7-day mean.

- 🔴 **Red**: a key event at 0 when its baseline is > 5; exceptions ≥ 3× baseline; refunds ≥ 2;
  revenue 0 for 3 days when the baseline is > 0; a release shipped and a funnel step fell > 40%
  with n ≥ 20.
- 🟡 **Yellow**: any metric outside ±40% of the weekday median with n ≥ 20; installs outside ±50%.
- Small numbers: with n < 20 say "directional" and never colour red on a ratio alone.
- Before calling a drop, check: a release (`app_version` share), an Apple Ads pause or change, a
  post that went hot, the weekend.

## 3. Explain and act

For every 🔴/🟡: the number vs baseline, the likeliest cause (release / ads / content / tracking /
real behaviour), and **one** next step. Nothing for green metrics.

## 4. Output

Write `reports/pulse/YYYY-MM-DD.md` (path from the apps note, if set) and reply with the same text:

```
Pulse 2026-11-26 (yesterday = Tue 25 Nov)
🟢 Habit app — installs 3 (weekday median 2), first task d0 1/3, trials 0 (baseline 0)
🟡 Geo game — installs 20 vs median 9 (+122%) · IT 9 / FR 3 / US 5 · 13 on 1.2.1 → EU ads? check CPI
🔴 Subscription app — paywall_shown 0 vs median 6 since 1.0.9 (shipped 24 Nov) → event lost in release
🟢 Invoicing app — RC: 0 trials, $0 (baseline $0)
Not checked: Firebase (no tools in this run)
```

Short: the owner reads it on the phone. No charts unless asked (PNG, not inline widgets).

## 5. Memory

When a red/yellow turns out real (a broken release, an ads change), add one line to `local/skills/app-pulse/apps.md` so the next pulse knows the new baseline. Don't log green days.

## Lessons

- Set the test-account filter explicitly: a project default can be inverted and show only the owner.
- Every App Review submission produces an Apple device install (US, never active) — exclude it, or
  "install without onboarding" appears after each submission.
- If `paywall_shown` fires on every tap of a locked item, count people, not events.
- Installs from before AdServices attribution shipped have no ad source — don't compare ad cohorts across it.
- A paywall stack added in a release can crush first-core-action completion and go unseen for weeks.
  The pulse exists to catch that within a day.
