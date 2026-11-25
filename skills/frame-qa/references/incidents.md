# Visual-delivery incident log — format and the classes seen so far

Keep your real log in `local/skills/frame-qa/incidents.md` (git-ignored). Every row is a flaw that reached the
owner (or the public), how it was caught, and the rule it produced. Add a row every time it happens again.

| Date | Artefact (path) | Flaw | Caught by | Rule it produced |
|---|---|---|---|---|
| YYYY-MM-DD | `<repo>/growth/series/<ep>/` | <what was wrong, frame id> | Owner / me / reviewer, with the quote | <the rule, short> |

## Classes of flaw and the rule each produced

| Flaw class | Rule |
|---|---|
| Image model re-drew app screens (added checkboxes, 58%→56%, 2026→2025) | Never trust a generated phone screen; paste the real capture pixel-for-pixel and diff every number against the raw |
| Store phone pushed past the frame edge, tab bar cut | Store phone is whole, tab bar included; geometry is one parameter |
| AI-regenerated phone screens in a preview video warped UI text | Phone screens in motion come from real recordings |
| Italic/serif headline read as «handwritten»; phone not fully inside | Sans headline, no italics/serif; whole phone inside the frame |
| Captions over full-bleed app screens clipped UI text; a label under the platform's action rail; a black frame after a hard cut | Caption above a phone-in-frame; keep labels left of x 960; no fade-in after a hard cut |
| Extra limb on a background person; a line contradicting the notification on screen | Every frame at full size, count limbs per person; read each line against its frame; no fix after posting — log it |
| Legs cut by a step / kerb; a chest-up torso floating above visible ground | Check the whole body down to where it meets the ground; prompt «body continues past the bottom edge»; redraw, never crop |
| Cover from a dark episode frame; small labels; yellow title; tagline unreadable at grid size | Purpose-drawn bright key art; tagline 62–66 px; near-white title; text inside centre 3:4; check the 360-px preview |
| Demo video with decorative filler motion and off-brand object colours | No decorative motion; real-world colours; still of 3D props before building scenes |
| Video model re-drew text and logos under camera moves; misspelt tiny labels; TTS mispronounced a word | Locked-off camera or pinned first frame on text shots; delete tiny generated labels; transcribe every TTS take |
| An arm entering from nowhere; lock and hinges on the wrong side of a door | Say whose arm it is and where it enters; lock on the door, hinges opposite |
| 6 and 4 fingers on close-ups; then a 6th finger on the redraw | Crop + enlarge every hand before the FIRST preview; crease or tip = digit; reject any hand you cannot count |
| A card over a face | Check overlays on rendered stills, not on raw art |
| Map showing through a code-drawn phone screen; HUD on phone screens; a code-drawn hand | Opaque screen backgrounds; hide HUD on phone close-ups; never draw anatomy in code |
| Plates and subtitles over faces and chins; still/clip light mismatch | Move or delete plates rather than shrink them; darken a push-in to hide a seam |
| A new story's cover drawn in an older story's style | A new story's cover and avatar take that story's own palette |
| Missing glyph (tofu box); quiz props that leak the answer | Render every glyph you typed and look; check props for give-aways |

## How these get caught — the pattern

- Most are caught by the owner or the client, i.e. after "done", and most of those had been "checked" on a contact
  sheet or on raw art. The ones caught in-house were found on full-size stills of the composite or on frames pulled
  from the final file.
- One pass is not enough for hands: redraws fail too. Re-run the hand check on every redraw.
