---
name: design-review
description: "Use when a screen is unclear, overloaded or confusing to new users, before adding labels, sections or explainer cards, and as the gate before showing any screen, Figma board, store screenshot or landing page. For running a Figma design round use mobile-design-iteration. Triggers: \"the screen is unclear\", \"add labels\", \"review the mockup\", \"it's overloaded\"."
---

# Design review — settled rules

Run this before anything reaches the owner. Building and Figma method live in `mobile-design-iteration`.

Your own cases for this skill live in `local/skills/design-review/` (git-ignored, see `local.example/README.md`).
Read them first if they exist — they hold the owner's per-app palette canon and past verdicts with quotes;
append the outcome of each review there. Round logs: `local/skills/mobile-design-iteration/`.

Output of a review: a numbered list of findings, each = rule broken → frame/node → fix, worst first.

## 1. Structure (check first)

- **HUD inventory** before any fix: list every element and sort it into must-show / contextual / on-demand /
  hidden. On Main only the next action is must-show; counters are small icon + number; timers, mascot and news
  appear only when they change what the user does; new users see fewer elements than veterans.
  <!-- why: a home screen with level ring + XP bar + pills + mascot + week strip + labelled challenge got "cool, but very overloaded" -->
- "It's unclear" is never answered with labels, sections or explanation cards — that is how overload happens.
  Answer: one hero object, one primary button, the rest one tap away. Too many mascots → one, or none plus a progress bar.
- **No spoilers** (collection apps): navigation keeps its levels (theme → packs → pack → game; only a finished
  pack has a page). Unwon content shows no name — a «?» slot and a count (art may show, names may not).
- **Two-tap reachability**: every item reachable in two taps, not only via recommendations (search chip,
  «See all», a full grid).
- **Truth**: content must exist in the app (no hero art from a pack that doesn't contain it); numbers on mocks
  match the real economy/prices (flag placeholders); no fabricated comparisons («Top N%» on a hardcoded curve),
  no «#1»/stars the rating doesn't support.

## 2. Geometry

- Nested rounded shapes are concentric: outer radius = inner radius + gap. Corner button inset ≈12,
  radius = card radius − inset (r28 card → r16 button at inset 12). A typical radius ladder: chip 8 / tile 10 /
  control 14 / card 16 / sheet 30. No capsule by default; children always smaller radius than parent.
- Rounded corners stay even on full-bleed cards.
- Text in pills optically centred by ink box, not font metrics.
- Pixel lint numbers (`../mobile-design-iteration/references/builder-guide.md` §5): whole-pixel geometry, 20 pt
  margins, 4-pt rhythm, ≥12 padding in cards / 14 in pills, nothing under the status bar (y<50) or tab bar, one
  primary per screen. Check alignment with the geometry table (`../mobile-design-iteration/templates/kit-loader.js` §5), not by eye.

## 3. Assets and colour

- Icons from one ready-made bold/filled set kept in the kit (e.g. Phosphor fill). Hand-drawn thin stroke icons
  read "creepy". An app with its own icon set: only that set. Missing glyph → add from the same set.
- Real app assets and real DS radii only — hand-drawn icons and wrong radii get «very bad».
- Real-world objects in real colours (coins gold); fixed meanings per app (streak, level, freeze each one colour).
- Per-app palette canon (banned colours, accent rules) lives in the local notes; check it every review.
  General: one accent moment per screen; depth by a darker hue, never by mixing toward black.
- Light: one light source; no glow plates behind mascots; background heroes faded and dimmed, never louder than
  the UI. No frosted-glass sheets unless the app's system uses them — sheets stay solid.
- Contrast: low-opacity captions fail WCAG (a 0.6-opacity coral caption ≈ 2.2:1) → a faint-text token, not opacity.

## 4. Anti-slop (reject on sight)

Bento grids, eyebrow labels over every heading, decorative gradients, fake big numbers, flying filler
motion, generic «AI landing» hero, near-copies of the category leader (its title typography, mono caps,
signature shapes, outlines, crests — "too similar"). When the owner calls a build "AI slop", run a de-slop pass
against this list. Pages about agents/Claude: Claude UI language (ivory #FAF9F5 / dark #262624, serif answers,
mono tool calls, a real session as content) — generic directions get "AI slop".

## 5. Store screenshots and social templates

- Store set = strict system (fixed headline position and size, same phone placement, phone fully inside the
  frame, one pop-out crop). No serif/italic headlines. Varied compositions read «too random».
- Mascot only where it IS the content (hero + one evolution frame); no stickers around phones "just because".
- First shot: offer 3–4 options; check the store preview video isn't eating slot 1.
- Rendered scenes: verify every number/word against the real screen (image models change 58→56, duplicate words).
- Social templates must look like real native screenshots (iMessage, X post, iOS lock screen, Screen Time);
  designed templates don't survive. Fake chats never endorse the app.

## 6. Process gates

- Show a still of risky visual pieces (3D props, a new style, a mascot) early and get a reaction.
- Short complaint → a two-option question with pictures about what to cut, not two rebuilds on a guess.
- Before reviewing, diff the owner's own Figma edits; never «fix» them back.
- Source of truth in Figma → fix in Figma (ask for the connector), don't re-render around it.
- Say in the hand-off which checks ran (lint, spoiler, reachability, contrast).
