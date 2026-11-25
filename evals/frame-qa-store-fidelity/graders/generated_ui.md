---
arm: both
type: llm
weight: 2
focus: final
---

PASS if the reply says the app UI that the image model redrew on slides 2–5 cannot be trusted as is: generated screens drift on numbers, dates and labels (e.g. "58" can become "56", the date or chart can change), so every number/date/label must be diffed against the raw simulator capture, or better, the real capture pixels pasted over the phone screen.
FAIL if it accepts the model-rendered phone screens because they "look sharp", or only comments on style, lighting or the hand.
Evidence to quote: the sentence about the model-rendered phone UI.
