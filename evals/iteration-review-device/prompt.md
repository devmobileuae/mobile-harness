---
name: iteration-review-device
tags: [metric-iteration, iteration]
runs: 3
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Yesterday's new users of my geography quiz game, one row per person, straight from PostHog (store bundle only, version 1.3.0; I submitted 1.3.1 to App Review yesterday afternoon). I'm based in Berlin. What's the onboarding and first-pack completion rate, where is the leak, and what should we change next?

| person | country | city | timezone | device | installed (UTC) | events after install | onboarding done | first pack done |
|---|---|---|---|---|---|---|---|---|
| p1 | IT | Milan | Europe/Rome | iPhone15,2 | 08:12 | 41 | yes | no |
| p2 | FR | Lyon | Europe/Paris | iPhone14,5 | 09:40 | 12 | no | no |
| p3 | DE | Berlin | Europe/Berlin | iPhone16,1 | 10:05 | 96 | yes | yes |
| p4 | US | Austin | America/Chicago | iPhone13,2 | 13:22 | 35 | yes | no |
| p5 | US | Cupertino | America/Los_Angeles | iPhone99,7 | 15:47 | 0 | no | no |
| p6 | BR | São Paulo | America/Sao_Paulo | iPhone12,1 | 17:03 | 58 | yes | yes |
| p7 | ES | Madrid | Europe/Madrid | iPhone14,7 | 19:30 | 27 | yes | no |
| p8 | IT | Naples | Europe/Rome | iPhone13,4 | 21:15 | 9 | no | no |
