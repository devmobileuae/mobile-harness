---
arm: both
type: llm
---

PASS if the eval cases written under evals/ include at least one negative case: a prompt on which streak-rescue must NOT fire (an unrelated or nearby question), with a check that the skill is invoked zero times.
FAIL if every case expects the skill to fire, or if "negative" only means a bad answer to a prompt where the skill should fire.

Evidence: name the negative case's file path and quote its check.
