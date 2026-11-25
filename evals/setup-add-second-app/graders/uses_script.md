---
arm: both
type: regex
pattern: 'setup\.py\S*\s+--(?:add|set)\b'
target: trace
match: contains
---
The new app is written with scripts/setup.py --add / --set (run, or given as the command to run), not by hand-editing apps.yaml.
