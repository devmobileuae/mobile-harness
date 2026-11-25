<!-- A filled per-concept brief as handed to one subagent, for a fictional habit tracker. Template: templates/brief-template.md -->

# Brief · concept 01 · Chain of Seven

**Seven days, one chain. Miss a day and a link cracks, it doesn't break.**

Day-2 retention is the leak: most people log once and never come back. A visible weekly chain with forgiving
cracks gives them a reason to open the app tomorrow without the shame of a reset streak.

## Why it exists (already printed on the board next to your phones)

- Borrowed from: Duolingo's streak freeze; Apple Fitness rings close per day.
- First minute: No slides. The first habit is pre-filled ("Drink a glass of water"); one tap logs it and link 1 snaps shut.
- Main: Main is the chain: seven links for this week, today's link pulsing, one primary button "Log today".
- Spreads by: A week card (seven links, the habit, "7 of 7") offered after day 7.
- Comes back for: an open link tonight, and a cracked link that can be repaired by logging two days in a row.
- Build: S. Logging and reminders exist; the chain is a new view over the same data.

## Background from the concept's author (context only; the screens below are what you draw)

- Onboarding: (0–5 s) one card "Drink a glass of water" with a big check; (5–15 s) tap → link 1 closes with a
  click sound, "1 of 7"; (15–30 s) reminder ask "Nudge me at 9 pm?".
- Main, day 3: top bar with the app name and a streak pill "3"; the chain (links 1–2 closed, 3 pulsing, 4–7 open);
  card "TONIGHT" with the primary button; row "Repair a crack: log 2 days in a row".

## Art direction for this concept (overrides the screen briefs where they differ)

Use the app's own link and check icons from the sprite; no new illustration. Today is Thursday; the player is Maya.

## Your three phones

Each phone frame already exists on the board (390 × 844, corner 48) with only a status bar inside. Build inside
these frames and nowhere else. Sizes and y positions are intent; lay out with the guide's margins, type scale and
pixel rules. Where a brief conflicts with the guide, the guide wins.

### Phone 1 · Onboarding · "The first link" · node id `<id>`

Grey caps 13 "DAY 1". Card with the habit name 22 and a 96 pt check button. Under it the chain, link 1 closed,
caption "1 of 7". No tab bar; home indicator.

### Phone 2 · Main · "The chain" · node id `<id>`

Top bar: app name 30, streak pill "3". The seven-link chain, full width. Card "TONIGHT": habit name, primary
button "Log today". Row grey 14: "Repair a crack: log 2 days in a row". Tab bar.

### Phone 3 · Share · "Week card" · node id `<id>`

Card 300 × 533, corner 28: app name 22, "7 of 7" 40, the chain, the habit, a tiny footer with the site name.
Under the card: primary "Share", secondary "Save image".
