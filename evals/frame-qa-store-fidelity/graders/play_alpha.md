---
arm: both
type: llm
weight: 1
focus: final
---

PASS if the reply flags that the Google Play PNGs must not have transparency: Play screenshots need RGB / 24-bit PNG or JPEG with no alpha channel, so the transparent rounded corners have to go (flatten on a solid background).
FAIL if it accepts the transparent-corner Play export or does not mention it.
Evidence to quote: the sentence about the Play export.
