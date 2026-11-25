<!--
A concept brief for ONE design agent that builds 3 phones in Figma (example: onboarding concept for a geography
sticker game). Typically produced by an ideation workflow (lenses x concepts, judges, top N, critic, final briefs),
then built by one subagent per concept: each reads BUILDER_GUIDE.md + its brief, builds into pre-made frames,
self-checks screenshots, runs the pixel lint. ~15–30 min and ~300k tokens per concept.
What makes it work:
  - the agent is told what is ALREADY on the board ("Why it exists … already printed") — it draws, it doesn't pitch
  - "Background … context only; the screens below are what you draw" separates context from deliverable
  - node ids of the exact frames to build in ("Build inside these frames and nowhere else")
  - conflict rule: "Where a brief conflicts with the guide …, the guide wins"
  - every string the screen shows is in the brief, in quotes
  - a content cap per phone (one hero, one primary button): agents add until the board is cluttered
Dispatch prompt: "Read design/figma-kit/BUILDER_GUIDE.md, then briefs/NN.md. Build the three phones. Screenshot each
inside use_figma (node.screenshot({scale:1.5})), fix what you see, run the lint (node <lint node id>). Do NOT use the Agent tool."
The Figma file is the app's `figma_file_key` from local/apps.yaml.
-->

# Brief · concept 01 · Walk It Home

**Drop it anywhere. It walks home. Every drop wins; the km are the score.**

The first round stops being a test you can fail. Any drop wins the sticker and shows how far off you were, so the game teaches the map instead of punishing it. One set of five a day, the same for everyone, ends in a result people paste into chats.

## Why it exists (already printed on the board next to your phones)

- Borrowed from: one-a-day puzzle grids; distance-scored geography games.
- First minute: No slides. A sticker is already under your thumb: drop it anywhere and it walks home to its country. Five drops, about 60 seconds, nobody fails.
- Main: yesterday's km to beat, a seven-day chart and one primary button for today's five.
- Spreads by: five coloured squares and the km, as text and as an image, after every daily.
- Comes back for: a number to beat tomorrow, the same five for everyone.
- Build: S–M.

## Background from the concept's author (context only; the screens below are what you draw)

- Onboarding game: flat world map; one card lifted under the thumb; 'Drop it anywhere.' Wherever it lands, the sticker walks home along a dotted line while a km counter ticks up, and the right country lights green with its name. Five drops, then a result type by total km, a name field, 'Share' and 'Beat it tomorrow', then the reminder ask.
- Main screen: top bar with streak pill; 'LOST-O-METER' with yesterday's km and a seven-slot bar chart; card 'TODAY'S FIVE' with one primary button 'DROP TODAY'S FIVE'. The one primary action: DROP TODAY'S FIVE.
- Share loop: plain-text result plus an optional image with five dotted walks and no names; offered after the very first round and after every daily.

## Art direction for this concept (overrides the screen briefs where they differ)

Flat world map, the home country highlighted green. Put the drop mark, the walk line and the sticker on real coordinates.

## Your three phones

Each phone frame already exists on the board (390 x 844, black, corner 48) with only a status bar inside. Build inside these frames and nowhere else. Treat sizes and y positions as intent, then lay everything out properly with the guide's margins, type scale and pixel rules. Where a brief conflicts with the guide (colours, fonts, radii, button style), the guide wins.

### Phone 1 · Onboarding game · "It walks home" · node id `<node id>`

Top grey caps 13: 'STICKER WALKED'. Big '1,370 km' black weight 56, white. Line 24, green: 'home'. Flat world map 361 pt wide (cream land on black, no labels): a grey 'x' where it was dropped, a dotted white line to the home country filled green, the sticker 64 pt landing with a white pop ring. Pill under the map: 'Sticker won'. Bottom: five dots, the first orange, caption 'Drop 1 of 5'.

### Phone 2 · Main · "The lost-o-meter" · node id `<node id>`

Top bar 44 pt: app name, flame pill '2'. Grey caps 13: 'LOST-O-METER'. Big '12,480 km' 56; label grey 16: 'yesterday'. Bar chart 60 pt high with seven slots; caption 'Beat it today.' Card 'TODAY'S FIVE - same for everyone': five face-down cards fanned; full-width primary button 'DROP TODAY'S FIVE', sub-label 'About 60 s - every drop wins the sticker'. Tab bar.

### Phone 3 · Share · "Today's walk" · node id `<node id>`

Result card 300x533, corner 28, black: '<App> #50' 22; '6,120 km lost' 40; a row of five rounded squares 40 pt: green, yellow, orange, red, green; flat world map 260 pt with five dotted walks and no names; footer grey 13: '<site domain>'. Under the card: primary button 'Share', grey button 'Copy as text'. Bottom caption: 'Next five in 14:22:10'.
