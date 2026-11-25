# Figma page / section / frame naming

Your own file's real examples: `local/skills/mobile-design-iteration/` if present.

## Pages (after a "tidy it up, add navigation" pass)

```
★ Start here                         ← cover + linked index frame «Map»; each NOW/SHIPPED page links back
---
● NOW · Onboarding v2 + Paywall (<Mon YYYY>)
● NOW · TikTok · Carousel templates
App Store                            (stacked newest-first)
---
SHIPPED <version> · App / Onboarding / DS · Foundations / DS · Components / Motion
---
EXPLORE · <proposal> / Today · progress options / …
---
ARCHIVE · Directions / Round 2 / App Store · v1 (test) / …
```
Every NOW/SHIPPED page starts with a «Read me» section and a «← Back to the map» link.
A design-system file may use numbered pages instead: `01 · Foundations`, `02 · Icons`, `03 · Components`, `05 · Explorations`.

## Sections — one per round, to the right of the previous one

`<Screen> — <what this round is> (<Mon D>)`, e.g.:
- `Home — grid of packs (Nov 18)` → `Home A2` → `A2b — progress on the tile` → `A2b — outline ring without overlap` → `Main v1 — final`
- `Main — what other apps do (Nov 19)` → `Main — dynamic Today` → `Today lite — one thing at a time`
- References get their own section next to the round: `Competitor refs`.
- A new iteration gets its own PAGE: `Iteration 1 — first game (<Mon D>)`.
- Store work: `S · Store set <version>`, `H · First screenshot — 4 options`.

When sections pile up, place by measuring: another session may have put a section where you planned yours.
Read existing section bounds before placing a new one.

## Rows and frames

- Rows are letters on an iteration board, frames are letter+number: `A1 Welcome`, `E1 Featured hero (Netflix)`, `G6 · Glass, centred`. `G0 Now` / `0 · Now` = the live screen for comparison, always first in a row.
- Directions = capital letters (`A · One big thing`, `B · The map is the stage`); fixes of one problem = `A/B/C` inside a section with the recommendation named.
- Research-borrowed variants carry the source in the name: `R4 · Recent + shelves (Spotify)`.
- Screen codes for whole flows: `O01–O23` onboarding, `A1–F9` app rows (row = tab).
- Long screens: `A1 · Today (Premium) — full scroll`; crops: `G2 Avatar ring` 390×520.
- Picks: a `✓ Picked` label on the frame; the rest stay as explored.
- Layers: icons `icon/<name>` (so a pass can swap hundreds of icons by name), assets named like their file (`c07-globe-KEN`), builders named by screen family (`TODAY`, `LEVELS2`).

## Frame sizes
- Phones 390×844 or 393×852 (corner ~48); a phone shell 402×874, bezel 12, radius 56/44.
- App Store 1320×2868 (6.9") or 1290×2796 (6.7"); Google Play 1080×1920; header asset 3840×1646.
