---
name: evaldriven-negative-case
tags: [evaldriven]
runs: 3
max_turns: 25
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

I just wrote a new skill for my habit-tracker plugin, streak-rescue. It should kick in when someone asks how to win back users who broke a long streak, and it makes the agent propose one re-engagement push with a 48-hour "streak repair" window instead of a multi-step campaign.

Set up the eval cases for it under evals/ in this repo so I can run them with and without the skill later. Don't run anything yourself.
