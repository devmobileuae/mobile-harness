---
arm: both
type: llm
focus: final
weight: 2
---

PASS if the answer rejects a third relaunch with the same brief and says that after a second stall on the same slice the lead finishes the remaining work inline (itself, in the main session). Acceptable variants: finish inline whatever is left; if all five files are already done and the build is green, the lead just verifies and records it; re-dispatching ONLY the untouched files is acceptable only as a secondary option, not as "relaunch the same agent".

FAIL if the answer endorses relaunching the same agent with the same prompt (with or without a longer timeout), or recommends re-running the whole five-file slice in a new agent as the main path.

Quote the sentence that states the recommendation.
