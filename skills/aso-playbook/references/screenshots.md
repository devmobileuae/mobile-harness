# Store screenshots: demo seeder capture, Figma rows, upload

## Spec (developer.apple.com, checked 2026)

Only the 6.9″ slot is required (1–10 images, PNG/JPG, no alpha). Accepted portrait sizes: 1320×2868,
1290×2796, 1260×2736. ASC API display type `APP_IPHONE_67` takes 1320×2868 and 1290×2796; 6.5″
(1284×2778 / 1242×2688) is optional and scaled down by ASC. Header art (`PRODUCT_PAGE_HEADER_ASSET`)
is 3840×1646 and uploaded by hand in the ASC UI. On a real iPhone only about x 690–3150 is visible,
back/share buttons cover y 350–640 at both sides and the app card covers below y ≈ 1560 → scale header
content to ~76% and keep it in the visible crop.

## DEBUG demo seeder

A `#if DEBUG` file that runs only with a launch argument (e.g. `-DemoSeed`) on a fresh install. It seeds a
believable history through the app's real engines (30 days, one bad weekend so "where you slip" has data, tasks
across all day-parts, a streak, two challenges, a few journal lines, part of today done so rings show colours),
marks onboarding / intro / What's New as seen and suppresses the review sheet. Companion flags:
`-DebugPremium` (premium without StoreKit), `-HideMascot`, `-DemoTab <tab>`. Keep any history below thresholds
that open sheets on launch.

Re-shoot recipe:
```bash
UDID=<udid>                 # iPhone Pro Max sim, native 1320×2868 (full id: xcrun simctl list devices)
xcrun simctl uninstall $UDID <bundle_id>
xcrun simctl install $UDID <path>/App.app          # DEBUG build
xcrun simctl status_bar $UDID override --time "9:41" --dataNetwork wifi --wifiMode active \
  --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState charged --batteryLevel 100
xcrun simctl launch $UDID <bundle_id> -DemoSeed -DebugPremium
xcrun simctl io $UDID screenshot raw/01-today.png   # trust this, not the sim panel (it lags)
```
Every state in a shot must come from the seeder or from using the app (never edit the app's store on disk).
A state the seeder can't reach is a new seeder option. Sim taps through the panel use POINTS (440×956 on Pro
Max). Keep a shot list with exact scroll positions in the app repo; don't erase or rebuild onto the staging sim
mid-session — the demo build is lost.

Localized captures: `xcrun simctl launch <udid> <bundle_id> -AppleLanguages "(de)" -AppleLocale de_DE`, one
folder per locale.

## Figma: one row per locale

One row (or SECTION) per locale; only the headline is translated, everything under it pixel-identical to en-US.
Headline rules: ≤ 2 lines split with `<br>`, ≤ 22 chars per line, exactly one `<em>…</em>` accent, a searched
keyword where natural, numbers in local format. Elements on the seams between frames make the set read as one
strip. Export trick for a whole row: screenshot the section at a large `maxDimension` and slice tiles at
`pad + i*pitch`. Exports go to `appstore/screenshots/<locale>/`, pushed by `listing.py`. Subscription review
screenshots: `appstore/screenshots/review/`.

## Figma export gotchas

- `get_screenshot` caps at 1024 px when its schema loads opaque (numeric `maxDimension` arrives as a string) →
  export full size with `download_assets` (nodeId).
- `upload_assets` with `nodeId` swaps a screen image fill in place.
- The owner may edit Figma mid-flight: re-export and diff hashes before every upload.

## What tends to be accepted and rejected

- Generate ART with an image model, never UI pixels or caption text — it redraws checkboxes and changes numbers
  and years. Paste real screens locally (PIL) over the generated scene.
- Mascot «stickers» around phones read as decoration; use the mascot only where it is the content (hero, an
  evolution frame).
- Zooms that crop the phone and lose the background or the menu get rejected.
- A near 1:1 copy of a competitor's hero is "too similar" — borrow structure, not signature marks. A hero showing
  an unshipped screen is a 2.3 risk until it ships.
- Without a preview video the search result shows shots 1–3 → design 1–3 as a triptych.
- Honesty: with a handful of ratings, no «#1», no stars, no laurels with fake claims.

Record the owner's picks and rejections per app in `local/skills/aso-playbook/`.
