---
name: aso-playbook
description: "Use for hands-on App Store growth: keyword research, name/subtitle/keyword fields per locale, the screenshot pipeline, ASC uploads, Apple Search Ads with day-3/day-7 stop rules. Complements app-store-aso / app-store-optimization (theory). Triggers: \"ASO\", \"keyword field\", \"Apple Search Ads\", \"store screenshots\", \"why no installs\", \"upload to ASC\"."
---

# ASO playbook

What converts, what doesn't, and how to redo it for a small portfolio with one ASC API key and one Apple Ads org.

Your own cases for this skill live in `local/skills/aso-playbook/` (git-ignored, see `local.example/README.md`).
Read them first if they exist (current listings, keyword records, campaign tables, audits); append the outcome
of each round/incident there. App ids (`asc_app_id`, `bundle_id`, `figma_file_key`) come from `local/apps.yaml`;
`shared.apple_ads_org_id` for Ads.

| Task | Read |
|---|---|
| Keyword research, tool calibration, the research record | `references/keyword-research.md` |
| Screenshots (seeder, launch args, Figma rows, gotchas) | `references/screenshots.md` |
| Apple Search Ads (economics, structures, stop rules, console tricks) | `references/asa-campaigns.md` |
| Brief for a sub-agent writing localized listings | `templates/localized-listing-brief.md` |

Scripts in `scripts/` (all read-only until `--apply` / `create` / `enable --yes`): `listing.py` (ASC listing push,
bundle id and config are arguments), `check_meta.py` (locale folder validator), `aso_probe.py` (free autocomplete
signals), `asa.py` (Apple Ads Platform API, plan folder per app), `upload.sh` (archive + upload).

## 0. First: is metadata even the bottleneck?

Check these three before writing a single keyword. Each one is the real problem often.

1. **Ratings.** An app with 2 ratings can sit at #49 for its own name while niche competitors have 5–60K
   ratings. No metadata change fixes that alone. A new app with 0 ratings ranks only for long-tail terms.
2. **First-session conversion.** A paywall stack after onboarding can drop day-0 core action to near zero; ads
   installs with 0 trials and every paywall dismissed is a product problem. That is a product conversation
   (`metric-iteration`), not ASO.
3. **Reach vs installs.** A content series with 150K views can move installs by zero. Judge content by installs
   per 1K views.

If 1 is the problem, do §5 first. If 2, fix the product first.

## 1. Keyword research (pipeline)

1. Seed list: competitors' title words, the app's own feature nouns, and slang the audience uses (for a
   discipline app: lock in, monk mode; for a geography game: the names of popular web geo games).
2. Free demand filter: `python3 scripts/aso_probe.py batch <cc> seeds.txt` (depth + top-3) and
   `hints <cc> "<prefix>"` to expand. Northstar `lookup_keywords` (free; NS pop < 35 → drop).
3. Apple's own number when an Ads account exists: Add Keywords dialog in an unsaved ad group (dots, US) or
   `getRecommendedKeywordsGql` (0–100, global). See `asa-campaigns.md` → console.
4. Walls: `top <cc> "<term>"` or AppKittie `get_keyword_difficulty` (paid credits). The wall is the review count
   of the top 5, not the difficulty number. Results full of apps with 0–6 ratings → winnable.
5. Where you rank today: iTunes Search API top 200 per term.
6. Drop wrong intent even when cheap: a word that means security apps, looksmaxxing, a telecom, a famous maps
   app or a sticker maker to the searcher brings installs that churn.
7. Write the record per locale (candidates with depth and top-3, what went into which field and why, what was
   left out) — format in `keyword-research.md`; save it in the app repo and a summary in
   `local/skills/aso-playbook/`.

## 2. Writing the fields

- Name: brand first + the market's top term (`Brand: Geography Sticker Game`). When the niche is name-squatted,
  go brandless and put the brand in the keyword field. ASC's duplicate-name check ignores case and `- : ,`;
  exotic symbols like `!` `+` `~` `·` survive. Have 3 fallbacks ready before opening ASC.
- When the top-25 for a term is full of 0-review apps, the gate is relevance: lead the title with the exact
  phrase (apps with the phrase first outrank one with it buried).
- Keyword field: commas, no spaces, ≤ 100 **UTF-8 bytes** (é = 2), no word from name/subtitle, no
  singular+plural, no primary-category word (already indexed), no competitor brands (2.3.7). If the owner keeps a
  competitor brand in the field knowingly, don't remove it: mention the 2.3.7 risk in one line and upload with
  `--keep-keywords`. <!-- why: the owner's explicit call overrides the rule; eval aso-keyword-field -->
- es-MX is indexed in the US storefront: a second 100-byte field for US. Must be real Spanish.
- Each locale is written from that storefront's autocomplete, not translated. Paired locales split terms
  (es-MX/es-ES, fr-FR/fr-CA, pt-BR/pt-PT). Brief for a sub-agent: `templates/localized-listing-brief.md`.
- Never promise more than the app ships in that language (UI translated but content still English → mention the
  content without naming its language).
- Validate: `python3 scripts/check_meta.py <locale> --brand <brand>` until `ok`.
- Promo text: not indexed, no review, and **not carried over to a new version** — copy it forward. Release notes:
  no emoji (empty boxes).
- Privacy claims must match the SDKs shipped ("no third-party analytics" with an analytics SDK live invites
  1-star waves, especially for health apps).

## 3. Screenshots (pipeline)

1. Seed real data: DEBUG-only seeder behind a launch argument, on a fresh install
   (`xcrun simctl launch <udid> <bundle_id> -DemoSeed -DebugPremium`). Locale captures:
   `-AppleLanguages "(de)" -AppleLocale de_DE`.
2. Status bar: `xcrun simctl status_bar <udid> override --time "9:41" …` (full line in `screenshots.md`).
3. Capture with `xcrun simctl io <udid> screenshot <file>` (the sim panel lags). Native 1320×2868 on a Pro Max
   sim; 1290×2796 is also valid for `APP_IPHONE_67`.
4. Every state on a shot comes from the seeder or from using the app; a state it can't reach is a new seeder
   option, never an edit of the app's store on disk.
5. Layout in Figma, one row per locale, only the headline translated; headline carries a searched keyword
   (screenshot text is indexed since 2025). Image generators only for art/backgrounds; paste real screens
   locally — generators change numbers and years in UI.
6. Export with Figma `download_assets` (not `get_screenshot`: 1024 px cap). Diff hashes against the last
   export — the owner may edit Figma mid-flight.
7. Upload (step 4 below). Shots 1–3 are what search and the ASA ad show when there's no video: design them as a
   triptych.

## 4. Upload to App Store Connect

All scripts are read-only until `--apply`; none submits for review (the owner submits).

```bash
# Run from the app repo root (fastlane-style appstore/metadata/<locale>/ + appstore/screenshots/<locale>/)
python3 scripts/listing.py --bundle-id <bundle_id> --version 1.1 [--locale es-MX] [--apply] [--subscriptions]
# Categories and copyright once
python3 scripts/listing.py --bundle-id <bundle_id> --version 1.1 --categories GAMES,GAMES_TRIVIA,EDUCATION --apply
# Re-shoot without touching texts, drop the preview video, keep the owner's keyword field
python3 scripts/listing.py --bundle-id <bundle_id> --version <v> --locale en-US --only-shots --drop-preview \
  --keep-keywords --shots-dir marketing/screenshots/<set> --apply
# Swap one image in place (order kept); --backup dumps the live texts first
python3 scripts/listing.py --bundle-id <bundle_id> --version <v> --only-shots --only 03.png --apply
# Build upload (signs with the Xcode Apple ID; the API key can't cloud-sign)
scripts/upload.sh <build number> [App.xcodeproj] [scheme] [ExportOptions.plist]
```
Traps: a description drafted in a markdown file keeps its hard wraps — pass `--desc-file` with the clean text;
a new app preview's poster PATCH 409s «Asset Not in Complete state» until processed (script retries ~4 min);
header art (3840×1646) is uploaded by hand; the "medium display" tab reuses the 6.9″ set and shows clouds while
PENDING.

## 5. Ratings

- System sheet only. A good policy: first ask after a few launches or right after an aha moment (a level-up, a
  completed goal), then every Nth launch; ≥ 30 days apart; never on a day the user's progress went down.
- Permanent Settings row → `https://apps.apple.com/app/id<ID>?action=write-review` (not counted against the
  3-per-year limit).
- Check in analytics how often the ask actually fires before assuming it works.
- 10–15 honest ratings from people the owner knows; never paid or swapped (5.6.3).

## 6. Apple Search Ads (pipeline)

1. Prerequisites (each one fails silently): AdServices token collection in the LIVE build, RC → Integrations →
   Apple Search Ads on, no App Preview in the first slot, RC catalog linked, Small Business Program.
2. Economics: `max CPT = net/payer × install→payer × tap→install`; write the ceiling down (e.g. $30 net/payer
   at 3% → max CPI $0.90).
3. Structure: exact keywords only, Search Match OFF (re-check after every ad-group edit), Manage Bids, iPhone,
   New users, default product page. Separate campaigns for brand and generic (budgets are per campaign).
   Localized geos get their own campaign with local keywords from that storefront's autocomplete; no T3 for apps
   that don't sell there.
4. Create PAUSED (console via Claude in Chrome, or `scripts/asa.py --app <key> create`). Enabling = spending:
   only on the owner's word; when he enables, move a future start date to now.
5. Day 3: Search Terms (catch autocorrect leaks: a misspelled brand → a common word) and impressions. Day 7:
   Keywords report + RC trials by keyword → apply the stop table in `asa-campaigns.md`.
6. Judge by install→trial by geo, not CPI alone: a ~$5 CPI with 0 trials is a conversion problem, not a bid
   problem.
7. CPPs only after ~$300 spend or when a keyword group needs a different first screenshot. A new CPP reaches
   Apple Ads with a lag («No Custom Product Pages Available» self-resolves).

## 7. Prices

PPP localisation with a price tool in dry-run first, then live. Price raises for ASA economics are done as
scheduled ASC changes that preserve existing subscribers; pick prices so hardcoded «40% off» labels stay true.

## Lessons

- **Check the brand word's shelf before naming.** A same-niche app with 15K ratings that owns your brand word
  keeps you at #49 for your own name; a rename decided but never shipped fixes nothing.
- **Generated store scenes rewrite UI numbers and years**; every UI pixel comes from the simulator. Decorative
  mascots around phones read as "just for the sake of it"; use the mascot only where it is the content.
- **First review.** Waiting ~2 weeks is possible; expedited review is picked up fast. Common rejections: Guideline
  4 (the iPad-compat window cuts a button), 2.3.2 (duplicate IAP promo images), 2.5.1 (HealthKit not visible in
  UI). Before submitting an iPhone-only app, check it in the iPad window.
- **ASA launched without the AdServices token in the live build and the RC integration off → no keyword revenue
  ever.** An App Preview takes the first ad slot and can halve taps.
- **A near-copy of a competitor's hero is "too similar"**: borrow the structure, not the marks. A hero showing an
  unshipped screen is a 2.3 risk — ship the screen first.
- **Review waits**: never cancel/resubmit; wait, then a status inquiry.
- **Paid keyword tools run out of credits mid-research**; the free stack (autocomplete + Apple Ads popularity +
  Northstar) is enough for 8 locales and ASA keyword lists.
- **Bids at Apple's suggestion can land CPI at 4–5× the stop line.** Say the expected CPI next to any bid change.
- **Geo matters more than the keyword set:** the same keywords can cost $0.92 per install in one EU country and
  $4.47 in another. Exact brand terms of a famous app are traps (searchers want that app); its misspellings are
  the inventory.
- **Pausing ads shows the organic floor** (e.g. 26–29 installs/day → 3–9/day). Know it before reading any other
  change.
- **Subtitle words often rank nowhere**; exact title phrases do. Re-measure ranks before defending a field.
