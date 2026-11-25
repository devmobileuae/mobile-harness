# Portfolio snapshot: "am I making it?"

Use when the owner asks about the whole set of apps rather than one screen.

## Procedure

1. RevenueCat MCP `list-projects`, then per project `get-overview-metrics {project_id, currency: "USD"}`
   (`revenuecat_project_id` per app in `local/apps.yaml`; skip apps the owner marked dead or paused).
2. Per live app `get-chart-data` with `chart_name` = `revenue`, `customers_new`, `trial_conversion`
   (`resolution: "2"` = monthly, `"0"` = daily for a fresh launch), start = store launch date.
3. Live version and ratings per bundle id: `curl -s "https://itunes.apple.com/lookup?bundleId=<bundle>"`.
4. Git activity per repo: `git -C <repo> log --format='%ad' --date=short | sort | uniq -c` (where attention went).
5. One table: app | in store since | users | revenue all time | last 28 d | MRR | $ per user | trend.
6. Strip the owner's own country (and friends in launch month) before any verdict.

## The logic: when the bottleneck is installs and ratings, features are not iterations

- Typical small-portfolio picture: every app gets 40–150 installs a month and fades after 2–3 months; $ per user
  rises release to release while traffic does not; almost no ratings in the main market.
- Arithmetic decides: at $0.87/user an app needs ~1,200 installs/month for $1,000; a new app gets the same ~50
  installs, so a new app does not change the sum.
- Therefore the weekly portfolio iteration is a **traffic or rating experiment** (ASO field, review-prompt
  mechanics, content series, ASA test), not a feature.
- Choosing the main app: for each live app take the last two weeks' installs/day × revenue/user; the leader gets
  the focus, second gets the rest, others zero hours for the quarter.
- A target that fits: one app with 20 ratings in the main market and a revenue goal by a date.
- A moratorium on new apps until the target is hit works when it is dated. When the owner pulls a feature forward,
  say once what it costs the date, then follow; move scope, not the date.

## Retractions are the method

Write down every claim that the data later retracted, with the reason:
- "funnel is broken" → a third of users were the owner's country; on ~37 real users zero purchases is noise;
- first payment came from the owner's country → real revenue is lower;
- "add a review prompt" → prompts existed; the mechanics were broken (re-asked every launch after "not now",
  "yes" sent to the written-review page, the single system attempt burned in onboarding);
- "the offer is weak" → ~5% to paid on 42 real users is not weak; complexity (hundreds of files for "one number")
  was the issue. Defer a restyle until there are ~20 installs a day, otherwise the effect can't be measured.

Save each snapshot with its table and retractions in `local/skills/metric-iteration/portfolio-<date>.md`.
