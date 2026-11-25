---
arm: both
type: llm
weight: 2
focus: final
---

Row p5 (US, Cupertino, America/Los_Angeles, model iPhone99,7, installed after the App Review submission, 0 events after install) is Apple's review device, not a user.

PASS if the reply identifies p5 as Apple's App Review device (or an Apple/review/test device, not a real user) and excludes it from the denominators before stating the rates.
FAIL if p5 is counted as a real user who dropped out (e.g. rates over 8 people, or p5 cited as evidence of a crash or an install-without-open leak).
