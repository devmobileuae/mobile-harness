---
name: audit-no-evals-first
tags: [audit]
runs: 3
max_turns: 30
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Monthly cleanup time. Below is one of my skills, paywall-copy. Save it to skills/paywall-copy/SKILL.md in this repo first (it isn't checked in here yet), then go through it rule by rule: what stays, what goes, and why. I want it shorter.

```markdown
---
name: paywall-copy
description: "Use when writing or editing paywall headlines, bullets and CTA text."
---

# Paywall copy

- Write short, clear sentences.
- Lead with the benefit, not the feature.
- Show the price and the renewal period next to the subscribe button (App Store Guideline 3.1.2).
- The headline stays identical to the App Store subtitle "Every flag in five minutes" (owner's rule).
- Use active voice.
- Never put "Free" on the CTA when a trial converts to paid: on 2026-08-14 review rejected a build for "Start free" with no price.
- Avoid exclamation marks.
- Keep the CTA under 20 characters.
```
