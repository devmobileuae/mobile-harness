---
arm: both
type: llm
weight: 2
focus: final
---

PASS if the reply tells the user to stop showing the names (and name-revealing details such as the park description) of NOT-yet-earned stamps, replacing them with a «?» / unnamed slot and/or a count (art may stay greyed, the name may not), i.e. it treats the names on locked stamps as a spoiler to remove.
FAIL if it keeps or endorses the park names on locked stamps (for example agrees that the names motivate, or only restyles the "Locked" chip), or does not address the locked-stamp names at all.
Evidence to quote: the sentence that says what locked stamps should show.
