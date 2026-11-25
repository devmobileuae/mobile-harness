---
type: regex
pattern: 'verdict\s*[:：]?\s*\**\s*(SHIP|FIX FIRST)'
flags: i
target: last_message
match: contains
---
The answer ends with an explicit SHIP / FIX FIRST verdict line (frame-qa output contract).
