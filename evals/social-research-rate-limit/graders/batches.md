---
arm: both
type: llm
weight: 2
focus: final
---

The skill's rule: TikTok search blocks after ~15 rapid queries and an immediate re-run is blocked too, so queries go in batches of at most 10 with long gaps between batches.

PASS if the script/plan splits the 30 queries into batches of 10 or fewer with a long pause between batches (tens of minutes or more), and says why (the block after ~15 rapid queries).
FAIL if it runs all 30 queries back to back (with or without short per-query sleeps of seconds), or uses batches larger than 10.
