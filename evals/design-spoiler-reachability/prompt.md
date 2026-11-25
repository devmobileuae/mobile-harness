---
name: design-spoiler-reachability
tags: [design-review]
runs: 3
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Quick look before I show the owner tomorrow. Our hiking app has a stamp collection: 24 regions, each region is a pack of 10 national-park stamps you earn by logging a hike there. Here's the new layout:

```
Home tab
- header: avatar, "7 / 240 stamps"
- hero card "Picked for you": horizontal shelf of 6 region packs (rotates daily, chosen by distance)
- "Continue": the pack you're working on
- tab bar: Home / Map / Journal / Profile

Pack screen (opens from the shelf or Continue)
- region name + cover art
- grid of 10 stamps
  - earned: full-colour stamp + park name + date earned
  - not earned: greyscale stamp art + park name + "Locked" chip, tap → park description and trail list
- progress bar "3 / 10"
```

The idea is that seeing the park names of locked stamps motivates people to go there. Anything you'd change? Give me the list.
