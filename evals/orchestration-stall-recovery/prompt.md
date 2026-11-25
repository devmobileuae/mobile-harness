---
name: orchestration-stall-recovery
tags: [agent-orchestration]
runs: 3
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

I'm running a re-skin of our geography quiz app (SwiftUI) with background agents, one slice each. The worker on slice 4 (five files: QuizView, QuestionCard, AnswerGrid, ResultView, StreakBadge) just died with "no progress for 600s". It's the second time on this slice: I relaunched it an hour ago with the same brief and it stalled again. I don't know how far it got.

My plan: relaunch it a third time with the same prompt and a longer timeout. Good idea? Tell me exactly what to do now, short.
