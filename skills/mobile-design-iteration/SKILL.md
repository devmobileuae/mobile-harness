---
name: mobile-design-iteration
description: "Use when designing or redesigning mobile screens, onboarding, paywalls or App Store screenshots in Figma, instead of generic brainstorming: real-app references, a round of variants on a board, picks, the next row, hand-off to code. Reviewing finished screens is design-review. Triggers: \"make variants in Figma\", \"research how others do it\", \"new home screen\", \"let's do it in Figma\"."
---

# Mobile design iteration (Figma)

Figma is the source of truth for screens and store slides. Order: **data → references → small round →
pick → assembled row → spec → "I'll approve and then you build it" → code**. "For now in Figma" = no code until the owner says so.

Your own cases for this skill live in `local/skills/mobile-design-iteration/` (git-ignored, see
`local.example/README.md`). Read them first if they exist; append the outcome of each round/incident there.

Read first: `references/env.md` (how to record file ids and kit nodes per app; the app's `figma_file_key`
is in `local/apps.yaml`) and the rounds log of the app you are on in `local/skills/mobile-design-iteration/`.
Naming: `references/figma-naming.md`. Building phones: `references/builder-guide.md` + `templates/kit-loader.js`.

## 0. Before any Figma call

1. Connector. If the Figma MCP isn't authorized, **stop and say "connect Figma via /mcp"**. Re-shooting store
   slides in the simulator and re-rendering headlines with a script instead comes out crooked; owners want
   the stop, not a workaround.
2. Load `figma:figma-use` (mandatory before `use_figma`). `create_session` with the file key; reuse the id.
3. Quota: `get_screenshot` / `get_metadata` / `get_design_context` share **~200 calls/day** (Pro). `use_figma`
   is not rate-limited (14 parallel calls fine). Screenshot inside `use_figma`: `await node.screenshot({scale: 1.5})`
   — a full phone with big gradients returns **no image at scale 2**; use 2–3 only on a child node.
4. Read the current page list and section bounds (`use_figma`) — node ids drift, other sessions add sections.

## 1. Data first, then one question

Write down the one number the screen should move before drawing (e.g. "32 opened the first pack → 3 finished").
If you can't name it, ask. Default to **iterations, not a whole-screen redesign at once**: one change on the
live app, one metric, ship, read. Multi-concept rounds only when the owner asks for them by count ("20 variants").

## 2. References = how real apps do it

- "Research it" means **look at other apps**, not a method. Abstract-method rounds (random focal objects →
  flows) get "don't like any of it"; a round of real store shots with ONE borrowed move per variant gets a pick.
- Sources, in order: Appllama MCP (needs Pro), AppKittie (credits run out), else the **public iTunes lookup API**
  for screenshot URLs → `upload_assets` into Figma; the owner's own screenshots.
  ```bash
  curl -s 'https://itunes.apple.com/lookup?id=<appId>&country=us' | python3 -c "import json,sys;r=json.load(sys.stdin)['results'][0];print('\n'.join(r['screenshotUrls']))"
  ```
- References go **into Figma** — a `Competitor refs` section next to the round, each shot captioned with the
  one move. Chat-only contact sheets don't count.
- Borrow structure, never the leader's signature marks (title typography, shapes, crests, outline style):
  close copies of the category leader get rejected as "too similar".

## 3. Round size and shape

| Round | Size | Example |
|---|---|---|
| Directions | 3–6 **genuinely different** | six variants each borrowing from a different app (streaming hero / store shelves / music recents / short video / books / travel log) |
| Detail | ~7 options on the same 4 states; "more" → next 7 | progress-on-tile options 1–7 then 8–14 on new / 4 of 12 / 9 of 12 / done |
| Fix | A/B/C + your pick named | three fixes for an overlapping ring, recommendation named |
| Assembly | one row built from pieces the owner liked | row F cloned from parts of E1, E2 and R4 |

- Always a `0 · Now` / `G0 Now` frame first: the live screen, for comparison.
- Boards stay lean: ~6 phones + 2 short cards. 20+ phones with text cards read as "way overloaded";
  20/40-concept rounds tend to produce no pick at all.
- Show whole screens at full scroll height (tall frames).
- After two rejections in a row ("boring" then "overloaded"), stop proposing and ask for the owner's references —
  their own model usually wins right after.

## 4. Building phones: the kit-in-the-file method

Files: `references/builder-guide.md`, `templates/kit-loader.js`, `templates/brief-template.md`,
`templates/brief-example-01.md`, `templates/concept-example.json`.

1. **Kit**: helpers (`T R E F S pill chunky icon iconBtn statusBar tabBar bar ring avatar notif svg …`) live as
   text in a hidden node of the file, pixel lint in another. Every script starts with:
   ```js
   const AF = Object.getPrototypeOf(async function () {}).constructor;
   const K = await new AF('figma', (await figma.getNodeByIdAsync("<kit node id>")).characters)(figma);
   ```
   New app: write the kit once (status bar, tab bar, buttons, type scale, `icon()` from a sprite, `S()` for
   real assets by layer name → image hash), store it the same way. Deleting the holder frame breaks the loader.
2. **Assets**: upload the app's real art as image fills into an assets frame: create a named 120×120 rect →
   `upload_assets` with `nodeIds`, `scaleMode: "FIT"` →
   `curl -s -X POST -H 'Content-Type: image/png' --data-binary @file.png '<submitUrl>'`. Convert app art with
   `sips -s format png <src.heic> --out <name>.png`. Map apps: `scripts/render_map.py --world <outlines.json>`
   (`globe --lon 37 --lat 0 --hl KEN:#3cc24b`, `flat --style night|paper`); continent stickers from puzzle pieces:
   `scripts/make_map_stickers.py --catalog <catalog.json> <outdir> europe,africa`.
3. **Icons**: one bold set (e.g. Phosphor fill, MIT) cloned from a sprite in the file. A sprite entry = group
   [256 box with near-transparent fill, glyph] in that order, or `icon()` blanks the glyph.
4. **Concepts → briefs**: keep concepts in a `concepts.json` (name, tagline, pitch, 3 screens, note
   from/hook/loop/viral/retention/build) and generate both the board note cards and `briefs/NN.md` from it.
5. **One subagent per concept**: reads the guide + its brief, builds ≤3 phones in pre-made frames (ids in
   the brief), touches nothing else, screenshots itself, runs the lint to 0 errors. Expect 15–30 min and
   ~300k tokens per agent. The lead then screenshots every phone and lints all of them before the owner sees one.
6. **Stored builders** for screen families with many states: `fn.toString()` into the kit holder; patch the
   text and re-run → all states update. Never hand-edit 12 states.
7. **Variants by cloning** approved layers so approved parts stay pixel-identical.
8. Fixed cast and date so a board reads as one product (one player name, one friend/rival, a fixed "today"
   and daily number). Real content only — no hero art from a pack that doesn't contain it.

Pixel rules the lint enforces (guide §5): whole-number geometry, even sizes when centring, 20 pt side margins,
4-pt rhythm (8/12/16/20/24/32/40), ≥12 inner padding in cards and 14 in pills, nothing under y<50 or y>760,
one primary button per screen with bottom edge ≤744 above a tab bar, type only from the scale.

## 5. Picks, edits, and the owner's own Figma changes

- Mark the pick `✓ Picked` on the frame, log it in `local/skills/mobile-design-iteration/<app>.md` with the
  owner's exact quote and date, leave the rest on the board. Then build the next row from it the same day.
- The owner edits Figma too (moves a bubble, rewrites texts, changes a frame mid-upload). **Diff layer
  positions** against the earlier clone (`kit-loader.js` §6) before changing anything, port the edit to the
  other states, never overwrite their text, re-export before upload.
- Read short words literally against what exists: "globe" = the app's own hero asset, not a new render;
  "remove pack" = the button named «Pack info». When unsure, a two-option question with pictures.
- Status notes: short, one picture per decision, one question, recommendation first.

## 6. Store screenshots in Figma

- System, not a gallery: one headline font and size at a fixed y, an identical centred phone at a fixed scale,
  one pop-out crop alternating L/R, the same gradient. Random variety per slide reads "too random".
- Phones fully inside the frame (e.g. scale 1.45, 64 px bottom margin); no serif/italic headlines (read as
  «handwritten»); no fake proof (no «#1» on a 3.5★ app with two reviews).
- First 3 shots = a triptych when there is no preview video (search shows 1–3). An App Preview video takes
  slot 1 of the Apple Ads ad — suspect it first when ad taps drop after adding one.
- Generated scenes (image models) redraw UI numbers (58→56, 2026→2025): paste the real screen pixels over
  the render. Per-locale sets = one SECTION per locale, frames at a fixed x-pitch (e.g. 1450); export the
  section at `maxDimension` = pitch × count, slice tiles at `40 + i*pitch`.
- Offer 3–4 style directions for the first shot before committing the set.

## 7. Design system parity (when the app has Swift tokens)

Tokens are parsed, never typed — `scripts/extract_tokens.py --repo <app repo>` → `tokens.json` →
`scripts/make_parity.py` → `parity.js`; run `parity.js` as one `use_figma` call → `{ok:true}` or drifts.
Library = only components the app uses. DS file separate from the store file (libraries publish per file;
moving components later breaks every instance).

## 8. Figma API traps (each cost a rebuild)

- `html_to_figma` without `nodeId` lands on Page 1 (`0:1`), and the page gets renamed by mistake. Create the page first.
- `createComponentFromNode` REPLACES the node — read its name first. `resize()` resets sizing to FIXED — set
  HUG/FILL after. A failing `use_figma` script rolls the whole run back.
- `findAll` skips nested instances; recolouring through instances needs a manual walk.
- Size overrides on instance sublayers don't stick → progress via hard-stop gradient fills (ring: angular
  gradient rotated +90°, hard stops at p). `dashPattern` restarts per segment → partial SVG path.
- Re-binding a paint to a variable with base {0,0,0} can render black → pass the resolved colour as base.
- Effect styles carry no modes → light/dark shadows are separate styles.
- Plugin API can't keyframe instance sublayers (Figma Motion); `export_video` + ffmpeg sampling verifies motion.
- Restyling one section: don't edit a main component with dozens of instances (e.g. the tab bar).
- Emoji render in a foreign font — use stickers/icons. Fonts must be loaded (the kit does it).

## 9. Hand-off to code

Spec in `docs/specs/YYYY-MM-DD-<topic>-design.md`, decisions listed with the owner's quotes; wait for
"I approve"; plan → waves (`mobile-feature-delivery`). Export PNGs of the picked frames into the repo
(`design/figma-YYYY-MM-DD/`). Live paywall/legal text beats a new design when the owner says so.

## Lessons

- ~100 concepts in 7 big rounds produce no pick; a references round, then small rows on the live app, ship. Default to small.
- "The icons are lame" → replace hand-drawn stroke icons with one bold set, swapped by layer name. Never hand-draw icons.
- "Way overloaded" → HUD inventory (must-show / contextual / on-demand / hidden) before layout.
- Collection games: keep the structure (theme → packs → game); unwon content stays «?». Spoiler-check every pack screen.
- Nested corners: inner radius = outer radius minus the inset (inset 12, button r16 in a r28 card).
- Every item reachable in two taps (search chip, See all, full grid). Curated shelves alone hide the catalog.
- No glow plates behind mascots; they read cheap.
- Several re-skins rejected in a row → the missing «soul» is usually a character, not a palette.
- Social carousel templates: only native-looking chrome (messages, posts, lock screen) survives; designed frames don't.
