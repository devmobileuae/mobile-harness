---
name: frame-qa
description: "Use before handing over ANY finished visual (reel, cover, carousel, store screenshots, demo video) and before saying \"done\" or sending it: the delivery gate. Full-size stills, hand/limb counts, safe zones, voiceover vs frame, continuity, cover at grid size. Triggers: \"check the frames\", \"ready to post?\", \"QA the reel\", \"how many fingers?\"."
---

# Frame QA: the delivery gate for every visual

Owners catch the flaws an agent already called ready — on a phone, at full size, often after posting. Most such
misses had been "checked" on a contact sheet or on raw art (`references/incidents.md` lists the classes). So this
gate runs **before the first preview**, not only before the final.

Your own cases for this skill live in `local/skills/frame-qa/` (git-ignored, see `local.example/README.md`).
Read them first if they exist (incident log, per-app store/demo facts, approved exceptions); append the outcome of
each incident there.

Episode-specific QA for a story serial (HUD band, caption-lift maps, narrator) lives in the
`interactive-serial-reel` skill. This skill covers what applies to every artefact and is the only QA source for
covers, store screenshots, carousels, code-drawn reels and demo videos.

## 0. Ground rules

1. **Contact sheets and boards are not a check.** `sheet_stills.py` (324-px tiles), `review_board.py` (180 px)
   and `ffmpeg tile` sheets show order, continuity and black frames. Anatomy, text and safe zones are judged
   only at ≥ 100% (six- and four-finger hands pass on a sheet).
2. **Check the composite, not the art.** Captions, HUD, plates and cards exist only in the rendered stills or in
   the final file. A fact card can sit on a face while the raw art is clean.
3. **Check frames pulled from the final encoded file too.** Some flaws exist only there (a map showing through a
   phone screen, a light/dark seam between a still and its clip).
4. **Redraw, don't hide.** A flaw is regenerated with the faulty frame as reference. No crop, no caption over it:
   owners look at the `art/` folder and read a hidden flaw as a defect.
5. **After a redraw, re-run the full check on that frame.** Redraws of hands regularly come back with a new extra finger.
6. **Posted = canon.** Once it is published, do not fix it unless asked. Log the flaw in the artefact's
   `script.md` and in `local/skills/frame-qa/incidents.md`.
7. **Say the cost before paying for a redraw** (e.g. an image model's credits per 9:16 frame, a video model's credits per second).

## 1. Procedure (every artefact)

```
1. Render full-size stills of the FINAL composite, one per shot (mid-shot) + first and last frame.
2. Tile every still with a person: crop_zoom.py <still> tiles   → open all 6 tiles (2× enlarged).
3. Crop every hand / face / small label: crop_zoom.py <still> boxes "x0,y0,x1,y1;…" (3×) → count.
4. Safe zones: safe_zones.py <still> --boxes "<text bboxes>"   (vertical video only; covers use step 6).
5. Narration table: every VO/caption line ↔ the frame it plays over (write it into script.md).
6. Cover / grid: grid_preview.py <cover.png> → read it at 360 px.
7. Pull 6–10 frames from the encoded file + a 1-fps sheet; check A/V and the end.
8. Hand-off text: say the pass was done, what was checked, what is knowingly imperfect.
```

### Exact commands

Stills of a code-overlay reel (puppeteer canvas; template in `templates/render_stills.cjs`):
```
cd <episode folder>
cat _engine.js _ep<n>.js > main.js && node render.cjs stills 0.5,2.1,4.3,6.8,…   # → stills/t0002.10.jpg
python3 scripts/sheet_stills.py out/sheet.jpg 6        # order/continuity only
```
Python-rendered reels: add a `stills` mode that writes the final composite at given seconds, optionally with the
unsafe bands tinted (bottom 420 px, right 120 px).

Frames from any finished video:
```
ffmpeg -v error -ss 12.5 -i out/ep.mp4 -frames:v 1 qa/t12.5.png                     # one full-size frame
ffmpeg -v error -i out/ep.mp4 -vf "fps=1,scale=180:-1,tile=8x2" -frames:v 1 qa/sheet-video.jpg
python3 scripts/crop_zoom.py out/ep.mp4 tiles --t 12.5                              # frame + 6 enlarged tiles
```
Manual crop if the script is not at hand (a hand at 300–700 × 900–1300, 3×):
```
ffmpeg -v error -i art/u09.png -vf "crop=400:400:300:900,scale=1200:-1:flags=lanczos" qa/u09_hand.png
python3 -c "from PIL import Image;im=Image.open('art/u09.png');c=im.crop((300,900,700,1300));c.resize((c.width*3,c.height*3),Image.LANCZOS).save('qa/u09_hand.png')"
```
Batch triage (many pieces): `python3 scripts/review_board.py <batch-dir>` → `board-N.png`.
A/V drift: `ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 f.mp4` vs the same with `a:0`. They should differ by less than one frame (0.033 s).

## 2. Anatomy (any frame with a person, generated or image-to-video)

- Per person, top to bottom: head, arms, hands, **fingers one by one**, legs, feet, and where the body meets the
  ground. Every hand belongs to someone, and you can say whose arm enters from which edge (an arm «out of the wall» fails).
- Counting rule: anything that sticks out of a hand and has a crease or a tip is a digit, including the "edge of
  the palm". Nails on the palm side are an error. A hand you cannot count with certainty is rejected, not argued for.
- Redraw prompt that works for hands: name the count and the position of each digit («exactly ONE thumb on the
  left side of the phone, exactly FOUR fingers below its bottom edge, on the right side only the edge of her
  palm»). Better: a pose where every finger is visible whole (object on the palm, fingers knuckle to tip); generate 2 variants.
- Waist/chest-up figures must be cut by the frame edge. Prompt «his body continues past the bottom edge of the
  picture». «From the chest up» + «keep the bottom quarter calm» produces floating torsos.
- Feet and legs: steps, kerbs and walls cut legs.
- Crowds: state in the prompt how many hands each person has and what each does.
- Video-model clips: check ~8 frames across the used range. Shadows and hands drift after ~0.4–2.4 s, eyes change
  style on a glance, and actions can play reversed (store the clip reversed and use only the clean part).
- Never draw anatomy in code (an ellipse «hand» reads as a defect). Use speed lines or a flash instead.
- Code-drawn figures (silhouettes, stick figures): eyes on the head, the hero findable in under a second, no limb
  crossing through a prop.

## 3. Text, overlays and safe zones

Vertical 1080×1920 (Reels/TikTok/Shorts):

| Band | Pixels | Why |
|---|---|---|
| bottom | y > 1500 (≈420 px) | username, audio, caption |
| right | x > 960 (≈120 px) | action rail (like/comment/share) |
| top | y < 200 | status bar / tabs |

- Run `scripts/safe_zones.py frame.png --boxes "x0,y0,x1,y1;…"`. It exits 1 on an intersection and always writes
  `<frame>_safezones.png`. Look at the tinted still. The exit code only covers the boxes you passed.
- Owner-approved exceptions (a subtitle block that dips into the bottom band, a series-wide caption baseline)
  live in the local notes; respect them, don't re-flag them.
- Every caption, plate, chip or card: does it touch a face, eyes, chin or the object of the shot? Fixes, in this
  order of preference: move the plate, lift captions for that shot, delete the plate, hide the HUD on phone close-ups.
- Phone screens drawn in code need an opaque background.
- Captions over full-bleed app screens always clip UI text. Put the phone in frame and the caption above it.
- Generated text: image models misspell small labels, so delete them instead of re-asking. Video models re-draw
  text and logos when the camera moves: use a locked-off camera or pin the first frame over the text.
- Render every glyph you typed (many rounded UI fonts have no «→»; Cyrillic needs a font that has it).
- Graphic hygiene: nested rounded shapes are concentric, so outer radius = inner radius + gap. No capsule by
  default. Centre pill text on measured ink boxes (`ImageDraw.textbbox`), not on font metrics.

## 4. Narration ↔ screen and continuity

- Write a two-column table in the artefact's `script.md`: line → what is on screen at that moment. Read each row.
- Avoid «it's X» where X could be read as sender or subject («Call me. It's dad.» over a notification signed «Mom»).
- Any prop that carries the premise (contract, counter, store headline) states it in words.
- Continuity across consecutive shots: who holds which phone, HUD/day numbers, furniture and door sides, hinge vs
  lock side, wardrobe (video B-roll can drop a cap mid-clip), and light state between a still and its clip.
- TTS: transcribe every take and diff it against the script («fight alerts» for «flight alerts» happens).
- Subtitles equal the spoken word at 3–4 sample points (beginning, middle, end). The first and last word are not clipped.

## 5. Per-artefact checklists

**Story reel (serial / pilot), 9:16.** All of §1–4. Then: no black card or old footage in the first second,
end card ≈ 2.3 s after the last word, a `-send` copy under 30 MB, every earlier cut kept beside the current one.
Serial specifics are in `interactive-serial-reel`.

**Code-drawn reel.** Feet ≥ ~1380 px from the top (above the bottom band). Labels and numbers over the heads stay
inside x 54–960 / y 200–1500. Lightning/flash effects last only 2–4 frames. Render one at a time with `nice -n 10`
(laptops overheat). Cap the bitrate: crf 19 + grain can produce a 180 MB file. Check the end card's app-icon pill radius.

**Cover / avatar.** `python3 scripts/grid_preview.py <cover.png>`. All text inside the centre 3:4 (y 240–1680).
The tagline must be readable in the 360-px panel (62–66 px at 1080 wide). Bright, purpose-drawn key art beats a
dark episode frame; a near-white title reads better than yellow. Each story uses its own video's palette. An
avatar is a calm face on a plain ground in the story's colour. Do not run `safe_zones.py` on a cover: a title
baseline inside the grid crop is meant to be there.

**Carousel.** Every slide at full size. Native-UI templates must look like real screenshots: status bar,
proportions, evenly spread icon rows. No fake endorsement (a public figure in a chat never recommends the app).
No answer give-aways in quiz props (a landmark next to its country's flag). Every glyph renders. Details: `references/artefacts.md`.

**App Store / Play screenshots.** Diff every on-screen number, date and label against the raw simulator capture.
Generated screens drift (58→56, 2026→2025, invented checkboxes), so paste the real pixels. The whole phone is
visible, tab bar included. Exact export size: 1320×2868 or 1290×2796 for iOS, 1080×1920 RGB with no alpha for Play.
Check that the locale is right per section and that the status bar shows 9:41. Never overwrite text the owner
edited live in Figma. Checks and commands: `references/artefacts.md`; per-app sizes and decisions: local notes.

**Motion-graphics / demo video (Remotion, video models, 16:9).** No decorative filler motion (flying coins,
wobbling cards); every motion must carry information. Objects keep real-world colours (gold coins, not brand
violet). Show a still of the 3D props before building scenes on them. Stills of every text-heavy shot must show no
warping, and logos must be correct. Check the seams between clips (6–8 frames, no flash of the card underneath),
A/V drift under one frame, and `+faststart`. Delivery length fits the brief.

## 6. Hand-off format

```
FRAME QA — <file>  (<n> stills full size, <m> frames from the encoded file)
anatomy:      PASS | FAIL (u09: 6th finger along the phone → redraw, <cost>)
overlays/safe: PASS | FAIL (t12.5: "DAY 9" at y=1610 under the username)
narration:    PASS | FAIL (line 4 «it's dad» vs sender «Mom»)
continuity:   PASS | FAIL (door light in still, dark in clip)
cover/grid:   PASS | n/a     store fidelity: PASS | n/a     A/V: Δ0.01 s
knowingly imperfect: <list, e.g. caption crosses the hero's wrist, fingers clear>
not checkable by me: sound by ear
verdict: SHIP | FIX FIRST
```

## Lessons (classes; your dated log lives in `local/skills/frame-qa/incidents.md`)

- Posting after looking at ~340-px tiles only lets through a three-armed extra and a line that contradicts the
  frame. Hence rule 0.1 and §4.
- Counting arms is not enough: check legs cut by steps and torsos floating above the ground, down to the feet.
- Hands fail twice: first draft and redraw. Crop-and-enlarge before the first preview; re-check after every redraw.
- Labels under the username line → the tinted-band step. A capsule pill → the concentric radii rule.
- The passes that find everything themselves run on every shot's full-size still **and** on frames from the final
  file. Use that pairing as the minimum.
- Generated phone screens lie about numbers and warp text. Real captures only.
- Filler motion and wrong object colours get called «slop». Show a still before animating.
- Covers: too dark, yellow title, small top line, wrong palette for a new story. Use the 360-px read and the story's own palette.
