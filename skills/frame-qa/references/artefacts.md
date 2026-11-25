# Non-reel artefacts: checks and commands

Per-app facts (where each store set lives, sizes used, the owner's decisions per app, client demo history) go in
`local/skills/frame-qa/artefacts.md` (git-ignored). Record per app: folder of the working set, export size, how the
real screen is composed over a generated scene, the upload script, owner decisions with dates.

## App Store / Play screenshots

- Every number/date on a pasted screen equals the raw capture (compose the real capture over generated scenes with
  an image matcher, and check any frame kept as a generated rendition by hand).
- Whole phone with tab bar visible; geometry set by one parameter, with headroom for the caption.
- Locale captures really are in that locale: `xcrun simctl launch <udid> <bundle> -AppleLanguages "(de)" -AppleLocale de_DE`.
- Status bar 9:41. Export dimensions exact: `sips -g pixelWidth -g pixelHeight *.png`.
- Play needs RGB, no alpha: `python3 -c "from PIL import Image;import sys;[print(f,Image.open(f).mode) for f in sys.argv[1:]]" *.png`.
- No customer data on screens. The owner may edit master texts live in Figma — never overwrite them.

## Motion-graphics / demo video

Remotion + `@remotion/three`, 1920×1080, 30 fps. Render `npx remotion render <Composition> out/…mp4`
(`--gl=angle` in `remotion.config.ts`; ThreeCanvas `flat`).

- Video models re-draw text and logos when the camera moves → locked-off camera, or pin the first frame over the
  text, or run the shot from a 2K keyframe with the camera moved in code.
- Image models misspell tiny labels → delete the label; do not re-ask.
- Every TTS take is transcribed and diffed with the script.
- Cut on real silences (`ffmpeg -af silencedetect`) — Whisper word starts drift on a long file.

## Carousels

- Only native-UI templates survive (iMessage, X post, iOS lock screen, Screen Time, ChatGPT). Check status bar,
  real proportions, icon rows spread evenly; fake chats never have a public figure recommending the app
  (initials, no photo).
- Instagram carousels 1080×1350: check every glyph renders, check props for answer give-aways.
