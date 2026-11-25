# Content-channel variant: judge posts by installs per 1K views

## Why views are not the metric

A typical incident: a story serial gets ~150K views over three days while store installs stay at the 1–3/day
baseline (2 / 1 / 2). A bio link gets ~0.44 taps per 1K views before any App Store drop-off. Every install spike in
the window has another cause (an ads launch day, the owner's own test devices). Per 1K views that is ≈0.03
installs even if every install is credited to the serial. Such a series is entertainment, not acquisition — say
so and stop judging it by installs.

Second pattern: "cute mascot" posts with an app end card stall at 100–130 views while the account's story format
starts at thousands. The end card reads as an ad and the platform does not push it past the first test group.
Close the line after the first test-group reach.

## Card format for a content experiment

```
Change:   format + hook (one variable), e.g. product visible in the first 2 s
Metric:   installs per 1K views over the posting window, per account
          installs = PostHog Application Installed on store build, owner's country out, minus the daily baseline,
          on days with no ads change
Second:   median views per post over ≥10 posts (reach), bio-link taps per 1K views
Baseline: <previous series installs/1K and bio taps/1K, dated>
Kill if:  ≥10 posts and installs/1K not above baseline noise
```

## What has to exist before more volume

1. Attribution per account: App Store campaign links with `ct=<account>` in each bio, or a Custom Product Page
   per account. Without it a content win and an ads day are indistinguishable.
2. A comment → DM keyword that sends the link (counts intent directly).
3. The product visible in the first seconds (the app IS the joke), not a moral or end card after a story.
4. No ads on/off switches during the window: installs dropping while ads are off look like a content flop or win.

## Paid traffic as the yardstick

Compare installs/1K views with the app's Apple Ads CPI (from `aso-playbook`): if a CPI of ~$1–3 buys installs,
content has to beat that per hour of work. Apple Ads shows an install at download, PostHog at first open — expect
fewer people in PostHog the same day. With no paid budget, content is the only lever and its metric is
installs/1K views, not views.
