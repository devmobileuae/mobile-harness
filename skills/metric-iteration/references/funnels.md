# Writing down an app's funnel

Keep one note per app in `local/skills/metric-iteration/<app>-funnel.md`. Read event names from the code (the
analytics enum or `docs/analytics.md` on the live release branch), not from memory, and date the read.

## Event list, in funnel order

```
Application Installed            (check: does it carry super-props? often not — filter by namespace only)
onboarding_step {step, step_name}  welcome > … > paywall    (list step names per version; they change)
onboarding_completed {…, notifications: yes|no|not_asked}
<item>_opened {item_id, replay}
<core action> {item_id, duration, …}     ← the activation event, e.g. "% of new users who do it on day 0"
review_prompt_requested {context}
paywall_shown {context|trigger}  > purchase_started > purchase_completed {product, trial}
rc_trial_started_event / rc_initial_purchase_event / rc_cancellation_event   (if RevenueCat forwards to PostHog)
```
Also list super-props (`app_version`, `build_type`, `cohort`) and which events lack them.

## Quirks section (each one changes a number)

Write every quirk with its date and size, for example:
- the core event double-fired in a replay path until version X (~12% inflation; share of players unaffected);
- `paywall_shown` fires per locked-item tap (39 shows on 18 users) — count users;
- an event lacks the item id; some modes send only the completion event;
- `$locale` holds the UI language; `$os_language` may not exist;
- debug builds produce hundreds of `offerings_failed` — filter namespace;
- the build number sits only on lifecycle events; custom events carry `$app_build`.

Privacy: for health or other sensitive apps, event names and funnel props only — never the sensitive values.

## Baselines table

| Date | n | Number |
|---|---|---|
| 2026-01-10 | 76 installs since launch | onboarding 75/76; item A 32 opened → 3 completed; core action on day 0 → 5/19 came back vs 2/39 |
| 2026-01-14 | cohorts 01-07..10, 76 | D1 18%, ever returned 25% |

Always n, date range and filters. A baseline older than the last release is re-pulled before use.
