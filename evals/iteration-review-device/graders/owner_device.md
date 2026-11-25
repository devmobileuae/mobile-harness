---
arm: both
type: llm
focus: final
---

The owner says they are in Berlin. Row p3 (DE, Berlin, 96 events, finished everything) is most likely the owner's own device.

PASS if the reply flags p3 as probably the owner's device and excludes it (or explicitly shows the rates with and without it).
FAIL if p3 is silently counted as a real user, so the first-pack rate includes the owner's own completion.
