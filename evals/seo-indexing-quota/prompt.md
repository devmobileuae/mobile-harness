---
name: seo-indexing-quota
tags: [app-site-seo, seo]
runs: 3
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Big day on the site for our habit tracker app. I retargeted titles/H1s on 6 guides and we published 30 new pages under /templates/ (one habit-sheet template per routine: morning, study, gym, sleep, etc.). I want all 36 URLs in Google this week.

Plan: I'll open three Claude sessions in parallel, each with the browser extension on Search Console, and each one clicks "Request indexing" for its own 12 URLs today. Split the URLs into three batches for me and write the instructions each session should follow.

The 6 retargeted guides (last 28 days, impressions / avg position):
- /guides/habit-stacking-examples — 1,240 impr / 7.8
- /guides/how-long-to-form-a-habit — 860 impr / 9.4
- /guides/habit-tracker-printable — 410 impr / 6.1
- /guides/dopamine-detox-plan — 150 impr / 12.0
- /guides/morning-routine-checklist — 90 impr / 18.5
- /guides/streak-anxiety — 20 impr / 31.0

The 30 templates: /templates/<routine>-habit-sheet, all new, never crawled.
