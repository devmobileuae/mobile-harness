---
arm: both
type: llm
weight: 2
---

PASS if the output is a per-unit table or list with a verdict (keep/delete/rewrite/merge/needs-eval) for multiple rules AND each KEEP cites evidence of a specific kind (an eval case, a dated incident, or an external requirement such as platform safe zones), not just "useful".
FAIL if it keeps rules on vague grounds or gives one overall opinion.
