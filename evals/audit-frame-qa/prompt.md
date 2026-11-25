---
name: audit-frame-qa
tags: [audit]
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

Run the monthly audit of the frame-qa skill from this plugin (skills/frame-qa/SKILL.md). For each rule decide: keep, delete, rewrite or merge — and justify it.
