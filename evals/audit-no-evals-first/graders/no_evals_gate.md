---
arm: both
type: llm
weight: 2
---

Context: the skill paywall-copy has no eval cases anywhere.

PASS if the output says the skill has no eval cases (or no eval evidence) and makes writing its first eval cases an explicit action item, OR marks the units it cannot prove as NEEDS-EVAL / "keep until an eval exists" instead of final verdicts.
FAIL if it gives final keep/delete verdicts for every rule and never mentions that the skill has no evals.

Evidence: quote the sentence about evals or the NEEDS-EVAL verdicts.
