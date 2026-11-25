---
arm: both
type: llm
weight: 2
focus: final
---

The skill's rule: "Request indexing" has ONE daily quota (~10–12 URLs/day) for the whole Google account, shared by every parallel session, so three sessions do not triple throughput; one session owns a single queue spread over several days.

PASS if the reply rejects or corrects the three-parallel-sessions plan because the request-indexing quota is shared across the account (any stated daily cap of roughly 10–12 counts), and instead proposes one queue worked by one session across several days.
FAIL if it splits the 36 URLs into three batches for parallel sessions to submit today, or only warns vaguely about "limits" while still delivering the three-session plan as the way to go.
