---
name: pulse-small-sample
tags: [app-pulse, pulse]
runs: 3
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Morning check, I pasted yesterday's numbers (Tue 24 Nov, store builds only, my own devices already excluded). "Median" = the same weekday over the last 4 weeks. Tell me what needs attention today. I read this on my phone.

Habit tracker (PostHog + RevenueCat):
- installs 6 (median 5)
- onboarding finished 5/6 (median 80%)
- first task completed on day 0: 2/6 (median 60%)
- paywall_shown → trial: 1 of 4 people (median 1)
- $exception events 3 (median 2)
- RevenueCat: 1 new trial, $0 revenue (median $0)
- version: everyone on 2.4.0 (shipped 2 weeks ago)

Geography quiz game (PostHog + RevenueCat; this app also ships Firebase Crashlytics):
- installs 31 (median 28)
- app_open people 64 (median 60)
- first pack completed on day 0: 14/31 (median 45%)
- paywall_shown 0 events (median 11 events / 9 people)
- $exception events 5 (median 4)
- RevenueCat: 0 trials (median 2), $0 revenue (median $6.99)
- version share yesterday: 1.4.0 = 27 people, 1.3.2 = 37 people; 1.4.0 went live Mon 23 Nov
