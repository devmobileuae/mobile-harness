# MCP servers I use regularly

MCP (Model Context Protocol) servers give agents real tools and data: Figma, analytics, stores,
generation. The rule of thumb: **if the source of truth lives in a tool, connect its MCP; don't
build a workaround** (see `agent-orchestration` → connectors-first).

The most used, roughly in order: Higgsfield, Figma, AppKittie, RevenueCat, PostHog, Vercel, Firebase,
Supabase, ElevenLabs, iOS Simulator, vidIQ, Claude in Chrome, Northstar, Appllama.

## Design

| MCP | What I use it for | Gotchas |
|---|---|---|
| **Figma** | source of truth for screens, store slides and marketing boards; building variants with a builder kit; reading designs into code | `get_screenshot`/`get_metadata` share ~200 calls/day, so take screenshots inside `use_figma`; `html_to_figma` without `nodeId` lands on Page 1; load the `figma-use` skill before every `use_figma` |
| **Appllama** | revenue-ranked iOS apps, every screen in journey order, for references | needs a Pro plan; every call costs a credit; watermark is provenance, not design |

## Store, ASO and competitors

| MCP | Use | Gotchas |
|---|---|---|
| **AppKittie** | app search, keyword difficulty, who ranks, competitor ads, organic creator content, reviews | 10 credits per keyword; overrates generic terms; `batch_keyword_difficulty` and `get_app_reviews` unreliable; credits run out fast |
| **Northstar** (local) | free App Store keyword demand filter | runs on localhost; first step of keyword research |
| **iOS Simulator** | build, launch and verify apps; screenshots for QA and the store | simulator only, not physical devices; open the live panel before building |

## Product analytics and revenue

| MCP | Use | Gotchas |
|---|---|---|
| **PostHog** | funnels (onboarding → first action → paywall), retention, event checks after each release; the baseline for `metric-iteration` | isolate real store users from TestFlight/dev; note dashboard ids in memory |
| **RevenueCat** | offerings, paywalls, entitlements, experiments, revenue and trial conversion | AdServices attribution must be in the live build for Apple Ads keyword attribution |
| **Firebase** | Remote Config (update gate), Android/iOS projects | separate Firebase projects per platform; flip the update gate in both before every release |
| **Supabase** | backends (auth, Postgres, edge functions) | inspect tables and advisors before migrations |

## Web

| MCP | Use | Gotchas |
|---|---|---|
| **Vercel** | deployments, logs, env, domains for app sites and SEO sites | index only on production (`VERCEL_ENV`); check runtime logs before guessing |
| **Google Search Console** (via browser) | indexing, queries, retargeting | request-indexing quota ~10/day per Google account, shared across sessions |

## Content production

| MCP | Use | Gotchas |
|---|---|---|
| **Higgsfield** | images (nano_banana_pro), video, lip-sync, consistent AI personas for reels | credits are scarce, so prefer frame-OCR over video analysis; `soul_2` drifts identity, so use image-edit to keep a face; `virality_predictor` scored a 19M hit and a 2K flop the same, ignore it |
| **ElevenLabs** | narrator voice-over, voice design | never retry a generation call (it charges again); voice_id only from the list or the user |
| **vidIQ** | Instagram/TikTok outlier search, profile reels, transcripts | ~5–10 credits per call, so budget the searches |

## Browsing

| MCP | Use | Gotchas |
|---|---|---|
| **Claude in Chrome** | my logged-in browser for Instagram research, store consoles, GSC | gentle: a few pages with pauses, never bulk fetches (ban risk to my own account) |

## Productivity

Gmail, Google Drive, Notion, Linear and Slack, connected through claude.ai, for drafts, docs and
tickets. Messages are always drafted for me to send.

## How MCPs show up in this plugin

- Skills name the MCP they rely on: `aso-playbook` uses AppKittie, Northstar and RevenueCat.
  `mobile-design-iteration` uses Figma and Appllama. `social-research` uses vidIQ and AppKittie.
  `metric-iteration` uses PostHog and RevenueCat.
- Evals run with `--strict-mcp-config`, so a skill's behaviour doesn't depend on a live MCP. Cases
  that need one should use mocks (`evals/mocks/<server>/<tool>.md` in the official runner).
- Credits are a budget: research skills state the per-call cost and the fallback when credits run
  out.
