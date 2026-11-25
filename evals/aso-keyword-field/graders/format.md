---
arm: both
type: regex
pattern: '(?m)^`{0,3}\s*[a-z0-9]+(?:[ ][a-z0-9]+)*(?:,[a-z0-9]+(?:[ ][a-z0-9]+)*){5,}\s*`{0,3}$'
flags: i
target: last_message
match: contains
---
The answer contains a keyword field line: comma-separated, no space after commas, at least 6 terms.
