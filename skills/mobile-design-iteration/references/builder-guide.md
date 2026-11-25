<!-- Template of the builder guide every per-concept subagent reads before drawing phones in Figma.
     Copy it into the app's design folder, fill the <…> parts (file, page, nodes, kit API, art list, look),
     keep the tool rules, pixel rules, how-to-work and reviewer snippets. A filled guide for your own app
     can live in local/skills/mobile-design-iteration/. The Figma session id is valid for one session only:
     call create_session again and use the new id. -->

# <App> — builder guide for the "<round name>" board

You draw phone screens for the app <App> in Figma, to the pixel. Read this whole file before the first tool call.

- Figma file key: `<figma_file_key from local/apps.yaml>` · page id `<id>` · board frame `<id>`
- Figma session id (pass as `sessionId` on every Figma call): `<create_session id>`
- The kit (helper functions) and the pixel lint are stored inside the Figma file and are LOADED by three lines at the top of your script (section 2). Do not paste their source. Kit source node `<kit id>`; lint source node `<lint id>`.

## 1. Tool rules (hard)

1. The ONLY Figma tool you may call is `use_figma` on the Figma server whose tools are named `mcp__<figma-server-id>__*`. Load it with ToolSearch: `select:mcp__<figma-server-id>__use_figma`. If the Skill tool is available, load the skill `figma:figma-use` once first. Pass `skillNames: "figma-use,figma-generate-design"` on mutating calls and `"figma-use"` on read-only calls.
2. NEVER call `get_screenshot`, `get_metadata`, `get_design_context`, `get_variable_defs` or `search_design_system`: they draw on a small daily quota that is needed elsewhere. Screenshots come from inside `use_figma`: `await node.screenshot({ scale: 2 })` returns the image inline. If a call returns no image (full-screen gradients at scale 2), use `{ scale: 1.5 }` for the whole phone and scale 2–3 on a child node for details.
3. Touch only the nodes you were given (your phone frames). Never edit, move or delete anything else on the page: other agents are building next to you at the same time.
4. `use_figma` code rules: plain JavaScript with top-level `await` and a final `return {...}` (no IIFE around the whole script, no `figma.closePlugin`, no `figma.notify`, no `console.log` for output). Colours are 0–1 floats (the kit takes hex). No object spread `{...a}`, optional chaining `?.` or `??`. Every script starts with the kit loader from section 2 (it sets the page and loads the fonts). Build ONE phone per call.
5. Every build script must be re-runnable: start with `const phone = await figma.getNodeByIdAsync("<id>"); clear(phone);` then build everything again. To fix a detail later, re-run the full build with the change or run a small script that finds nodes by name inside your phone.
6. If a call fails, read the error, fix the script and call again. On rate limits wait 60 seconds (`python3 -c "import time; time.sleep(60)"`) and retry.

## 2. The kit API

Start EVERY build or fix script with exactly these lines:

```js
const AF = Object.getPrototypeOf(async function () {}).constructor;
const K = await new AF('figma', (await figma.getNodeByIdAsync("<kit id>")).characters)(figma);
const { T, R, E, F, S, pill, chunky, icon, iconBtn, statusBar, tabBar, homeIndicator, centerIn, bar, ring, avatar, svg, notif, grad, radial, place, fill, shadow, clear } = K;
```

Pixel lint (read-only; put your phone ids in the array):

```js
const AF = Object.getPrototypeOf(async function () {}).constructor;
return await new AF('figma', 'PHONE_IDS', (await figma.getNodeByIdAsync("<lint id>")).characters)(figma, ["<phone id 1>", "<phone id 2>"]);
```

All coordinates are in points inside the parent; the phone is <390 × 844>.

| Helper | What it makes |
|---|---|
| `T(parent, text, x, y, {size, style, color, opacity, w, align, lh, ls, caps, name})` | Text in the app font. Give `w` for a fixed-width box that wraps (then `align`). Returns the node (`.width`, `.height` valid). |
| `R(parent, x, y, w, h, {fill, paint, opacity, r, stroke, sw, edge, effects, rot, name})` | Rectangle; `edge` adds the app's button bottom edge if it has one. |
| `E(parent, cx, cy, w, h, {fill, paint, stroke, sw, arc: [startDeg, sweepDeg, innerRatio], name})` | Ellipse centred at (cx, cy); `arc` draws a ring segment (0° = 12 o'clock, clockwise). |
| `F(parent, x, y, w, h, {fill, paint, r, clip, stroke, sw, effects, name})` | Frame with absolute children; clips by default. Cards. |
| `S(parent, assetName, cx, cy, size, {rot, shadow, opacity, w, h, mode, r, name})` | Real app art (image fill named `assetName` in the assets frame), centred, aspect kept. |
| `pill(parent, label, x, y, {h, fill, color, size, px, r, icon, vicon, name})` | Hug-width capsule; read `.width` after creation to right-align. |
| `chunky(parent, label, x, y, w, {h, fill, edge, color, size, r})` | The app's primary button (plus neutral/dark variants). |
| `icon(parent, name, x, y, size, hex)` | Icon from ONE bold set cloned from the sprite node `<id>`; returns group `icon/<name>`. List the names here. Fixed meanings (coins, streak, level…) with fixed colours. |
| `await statusBar(phone, dark)` / `await tabBar(phone, {active})` / `homeIndicator(phone, dark)` | Chrome. Status bar first child; tab bar LAST child; home indicator last on screens without a tab bar. |
| `iconBtn`, `bar`, `ring`, `avatar`, `notif`, `svg`, `centerIn`, `place`, `grad`, `radial`, `fill`, `shadow`, `clear` | Round icon button, progress bar/ring, avatar badge, iOS notification banner, any SVG as `icon/<name>`, centring, paints, effects, empty the phone. |

Domain helpers go here too (e.g. for a map app: `flatXY` / `globeXY` / a `GEO` table so pins sit on the real place, never eyeballed).
For any other vector shape use `figma.createNodeFromSvg(...)`, name it `icon/<something>`; never build icons from rotated lines. Emoji are forbidden (foreign font): use art and icons.

## 3. Art you can use (asset names for `S`)

List every uploaded asset family with names and what they show (app icon, mascot, UI objects, content art by
category). Say how to add more: the originals folder in the repo, `sips -s format png <src> --out <name>.png`,
then (a) `use_figma` adds a 120 × 120 rectangle named like the file into the assets frame and returns its id,
(b) `upload_assets` with `fileKey`, `count: 1`, `nodeIds: [id]`, `scaleMode: "FIT"`, (c)
`curl -s -X POST -H 'Content-Type: image/png' --data-binary @file.png '<submitUrl>'`.

**People and dates on every screen** (so all concepts read as one product): one player name, one friend/rival,
2–3 others, each with a fixed avatar asset; a fixed "today" and daily number unless the brief says otherwise.

## 4. The app's look

Screen size, background, corner radius; type family and the ONLY allowed sizes; text colours; surfaces;
accents (which colour is THE primary action); radii; top bar pattern; button placement (one primary per screen,
bottom edge ≤ 744 above a tab bar; without one the primary sits at y ≈ 736 and the home indicator at 831);
how hero art is used; share cards (designed objects that make sense to a stranger); copy tone (short, concrete, true).

## 5. Pixel rules (what "to the pixel" means)

1. Every x, y, width and height is a whole number. Centre with even sizes so corners land on whole pixels.
2. Side margins: 20 for text and cards (16 for full-bleed cards and grids). No text closer than 16 to the edge.
3. Vertical rhythm on a 4-pt grid: gaps 8, 12, 16, 20, 24, 32 or 40; same gap between the same kinds of things.
4. Things that look aligned are exactly aligned: compute positions from one formula, never eyeball each one.
5. Text never touches another text, an icon or its container: ≥12 inner padding in cards, 14 in pills; never clipped. Place the next element at `prev.y + prev.height + gap`.
6. Text optically centred in buttons and pills; icons on the text's vertical centre.
7. Nothing important under the status bar (y < 50) or under the tab bar (y > 760); the tab bar is the last child.
8. Rotated art bleeds off the edge only on purpose; never clip a face or a label.
9. Contrast: light text on dark, ink on light. No dim grey text on coloured buttons.
10. Count what the brief asks for: 6 tiles, 5 dots, a streak of 7 — exactly that.

## 6. How to work

1. Read the brief. For each screen write a coordinate plan (every element with x, y, w, h, top to bottom) before code. Decide the vertical budget first.
2. Build screen 1 in one `use_figma` call: loader, `clear(phone)`, `statusBar`, content, `tabBar` or `homeIndicator`, `phone.screenshot({ scale: 2 })`, return ids.
3. Look at the screenshot like a picky art director: overlaps, cramped text, uneven gaps, near-misses in alignment, weak hierarchy, dead zones, wireframe look. Fix and re-shoot. Screens 2 and 3 the same way, consistent with screen 1.
4. Run the lint. Fix every error; fix warnings unless deliberate (say why).
5. Final call: screenshot all phones at scale 2, last look.

Definition of done: screens that tell the concept's story without a caption, zero lint errors, nothing you would be embarrassed to show a founder who asked for "pixel-perfect".

## 7. For reviewers: seeing and measuring

Screenshots and the geometry table: `templates/kit-loader.js` §4 and §5. Zoom by screenshotting a child node at
scale 3. To change a node: fetch it by id after the loader and set `x`, `y`, `resize(w, h)`, `characters`,
`fontSize`, `fills = fill('#hex')`, `remove()` — or rebuild the whole phone.
Style reference phones from an earlier round: `<ids>` (read-only, screenshot them to calibrate your eye).
