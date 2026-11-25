---
arm: both
type: llm
weight: 2
---

PASS if the reply proposes or writes an eval case (prompt + grader) that reproduces the incident BEFORE or together with editing the skill, and mentions running it with and without the skill.
FAIL if it only adds a rule to the skill text with no test.
