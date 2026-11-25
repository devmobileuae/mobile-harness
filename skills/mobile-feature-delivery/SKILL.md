---
name: mobile-feature-delivery
description: "Use when implementing a feature or fix in an existing iOS or Android/KMP app, and ALWAYS when adding or changing a field on a persisted model (SwiftData @Model, Keychain, Room/SQLDelight) in a shipped app: that is a migration, not a one-line edit. Risk table, test gate, upgrade check, upload. Triggers: \"build the feature\", \"add a field to the model\", \"upload to TestFlight\", \"we got rejected\"."
---

# Mobile feature delivery (iOS + Android/KMP)

Your own cases for this skill live in `local/skills/mobile-feature-delivery/` (git-ignored, see
`local.example/README.md`). Read them first if they exist; append the outcome of each round/incident there.

New app → `ios-app-bootstrap` first; its `templates/CLAUDE.md` holds the universal **trap library**
(Swift 6 isolation traps, `ModelContext` not retaining its container, one sheet per view, `.task`
restarts…). Read it; this skill does not repeat it. This skill is for apps that already ship.

**Read first, every time:** the app's own `CLAUDE.md` (build gate, gotchas, guardrails) and the
project memory index. Ids and paths: the app's block in `local/apps.yaml` (format of a per-app env
note: `references/env.md`).

## 0. Owner rules that apply in every repo (learned, not optional)

- **Do not commit.** The owner commits; follow the repo's attribution rule. Commit only when told so in
  this session ("commit and continue" covers that unit only).
- **Who drives the simulator differs per repo** — some repos: the user runs sim/device, the agent runs the
  build+test gate; others: the agent must eyeball every touched screen in light AND dark; some forbid
  launching the emulator/simulator and long foreground Gradle runs. **Ask whether the sims are free**
  before an interactive pass — the owner may be tapping in them.
- **Plan before fixing** when a list arrives with "think it over"/"make a plan"/a planning skill. Plans
  are lean: files + seam signatures + rules + acceptance checks, ~150 lines for nine tasks. One question
  at a time, with a recommendation.
- Never upload, submit, release or publish Remote Config on your own. Upload only on an explicit go.

## 1. Frame — risk table before code

1. Acceptance criteria in user terms (what is seen/tapped), plus the metric — e.g. **% of new users who
   complete the core action on day 0**. Note its baseline before the change.
2. Fill the risk table (`templates/risk-table.md`, format from the bootstrap template):
   `| Surface | Tier | Why | Proof |`. core = persistence, money, score math, notifications, gates,
   anything reading user data written by an older build → test first, confirm it fails without the fix.
   ui = one smoke test + eyes. More than half in core = re-argue.
3. Classify persistence changes now (section 2). Touching IAP, HealthKit, permissions, onboarding or
   the paywall = review-critical → plan the E2E scope (`references/e2e-scope-example.md`).

## 2. Persistence changes (the additive-field rule)

A non-optional attribute with a default added to a shipped `@Model` crashes upgrade installs (SIGABRT in
the generated getter) while **every test passes** — every test uses a fresh in-memory container.
- **New attribute on an existing `@Model`:** optional stored `xValue` + computed non-optional `x`
  whose fallback is the *previous behaviour* + a test that sets `xValue = nil`. Code:
  `references/swiftdata-migration-incident.md`.
- **New entity:** non-optional is fine. Add it to `AppModelContainer.schema` and the reset-all path.
- **Never rename a stored attribute after release** (drops user data).
- Keychain: adding `kSecAttrAccessible` to queries breaks pre-existing items → `-25300`.
- Room/SQLDelight/DataStore: version bump + migration + a test that opens the previous version's store.
- Always run the **upgrade install** in section 5.

## 3. Platform rules

**iOS**
- `project.yml` is the source of truth; `.xcodeproj` is generated and git-ignored → `xcodegen generate`
  after adding/moving any file. Never hand-edit `.pbxproj`; never bump versions in Xcode's General tab.
- iPhone-only still runs on iPad in the **compatibility window (≈ iPhone 8 Plus height)**. App Review
  tests there (Guideline 4: «Continue button was cut off»). Every pinned-CTA screen scrolls
  (`ScrollView` + pinned CTA) or degrades (`ViewThatFits`). Check iPhone SE (3rd gen).
- `CODE_SIGNING_ALLOWED=NO` strips entitlements: HealthKit fails with `Missing
  com.apple.developer.healthkit entitlement` and "Connect" looks dead. Build without the flag to test Health.
- HealthKit read-only still needs `NSHealthUpdateUsageDescription` (ITMS "Missing purpose string")
  and must be **named "Apple Health" in the UI** (2.5.1).
- Analytics: add the event to the typed taxonomy **and** the golden list test (`AnalyticsEventTests`);
  never `onAppear`-track inside always-mounted panes (phantom `paywall_shown` at launch).
- Local notifications need the `UNUserNotificationCenterDelegate` with `nonisolated` witnesses and a
  re-lay on every foreground.
- Nested `NavigationStack` compiles and crashes at runtime (`comparisonTypeMismatch`).
- iOS 26 Liquid Glass modifiers need a fallback for the app's deployment target.
- `ForEach(slots, id: \.hour)` gives 7:00 and 7:30 one id → holes in the list; key by a truly unique
  value. A comment claiming otherwise can fool the code reviewer; the owner's eyes on the sim do not.

**Android / KMP** (full list: `skills/android-kmp-engineering`, `references/kmp-android-lessons.md`)
- Compile-green ≠ working. Known classes: `@Serializable` in `SavedStateHandle` (Bundle crash),
  server UI gated by a client-version header (keep = shipped release), missing
  `composeResources` drawables (blank + untappable), `@color/` in vector XML, Koin bindings with no
  graph verification (`InstanceCreationException` on first resolve).
- Faithful port = diff allow-lists, resolver maps and nav collectors 1:1 against the Android tag
  (`git show <tag>:<path>`), not against a stale checkout.
- iOS `Dispatchers.IO` needs `import kotlinx.coroutines.IO`; app scopes need `SupervisorJob`.
- Ticker tests: `runTest(UnconfinedTestDispatcher())` + `backgroundScope`, never `advanceUntilIdle()`.

## 4. Build in slices — the gate

One slice = builds + tests green. Parallel workers (`agent-orchestration`) must **not** run
`xcodebuild` (shared-tree build races) — integrate and build yourself.

```sh
# iOS (logic in a local package: cd <App>Kit && swift test)
xcodegen generate
xcodebuild test -project <App>.xcodeproj -scheme <App> \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
  -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO
# one test: add -only-testing:<App>Tests/<Class>/<testMethod>
# ambiguous device name → use an id from: xcrun simctl list devices available
```
```sh
# KMP :shared + :composeApp — the four gates
./gradlew :shared:compileKotlinIosSimulatorArm64 :shared:compileAndroidMain :composeApp:assembleDebug
./gradlew :shared:iosSimulatorArm64Test
# KMP single-module app
./gradlew :composeApp:testDebugUnitTest   # does NOT catch Koin binding errors — open the screen
```
Report counts plainly: "253/253", "kit 288, backend 138, Debug + Release build".

## 5. Verify like a user (simulator path)

1. **Drive the sim with the iOS Simulator MCP** (`mcp__Claude_Code_iOS_Simulator__control`): attach,
   launch the built `.app`, tap/swipe in **points** (iPhone 16 Pro ≈ 402×874, Pro Max 440×956).
   If it says "Xcode is installed but not selected", give the owner
   `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` (needs their password).
2. **Trust `xcrun simctl io <udid> screenshot`, not the panel** — the panel's own screenshot lags.
   Coordinates from screenshots miss; prefer element frames. After every tap, screenshot and verify
   before the next (taps can double-fire through two onboarding steps).
3. Anything that appears mid-scroll (sticky headers, bottom-bar clearance) is verified by swiping, not
   by one static frame. Toasts live ~2 s: shoot a burst and group by file size (otherwise you will
   wrongly report "toasts do not appear").
4. Seeded states via DEBUG launch args (`-<App>DemoSeed -<App>DebugPremium`, fixture paths). Steps in
   Health: Health app → Steps → Add Data (simctl can't inject samples).
5. Screens to walk: empty / loaded / error, **iPad Air 11" (M3) compat window**, iPhone SE, dark (and
   light where the app has it), largest Dynamic Type on text-heavy screens. Note sim limits: RevenueCat
   offerings and backends may not load (expect the honest "Plans aren't available" state); Firebase
   Remote Config fails on the iOS sim (-34018) → device.
6. Pipeline bugs (OCR/Vision): compile the real source files into a macOS `swiftc` harness
   (`main.swift`, print every stage) — it shows exactly which stage misreads.
7. **Upgrade install:** previous release build (tag or `.xcarchive`) → create data → install the new
   build over it → open every screen reading changed models. An `AppVersionLedger` that records the
   launch transition should report `upgrade`.
8. Say what was seen and what was not: "Criteria 1 ✓ 2 ✓ 3 not checked (offline)".

## 6. Review

Self-review the diff → fresh `mobile-reviewer` with the diff only → fix → re-review the fixes.
A pre-release review after QA passed still finds real defects (settle races, toast vs review-ask
collisions, per-second whole-screen redraws). Run a design-lint subagent on every UI diff where the app
has a design system (raw hex, off-register font sizes, stock `.sheet`). Go/no-go on risky releases →
`conclave` (builder, skeptic, data-analyst).

## 7. Release (iOS) — the checklist

1. Bump `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` in `project.yml`.
   Build numbers strictly increase per upload.
2. Gate green (section 4). Release notes in user language, no emoji (they render as tofu).
3. Privacy: `PrivacyInfo.xcprivacy` + ASC App Privacy label + policy + site claims match the binary
   (e.g. Product Interaction, Other Usage Data, Crash Data, User ID, Device ID, Coarse Location,
   Purchase History — all not linked). New SDK or server write = update all four.
4. Archive + export/upload — `scripts/release-ios.sh <Scheme> <ver> <build>`, which runs:
   ```sh
   xcodebuild archive -project <App>.xcodeproj -scheme <App> -configuration Release \
     -destination 'generic/platform=iOS' -archivePath build/release/<App>-<ver>-<build>.xcarchive \
     -allowProvisioningUpdates
   xcodebuild -exportArchive -archivePath build/release/<App>-<ver>-<build>.xcarchive \
     -exportOptionsPlist build/ExportOptions.plist -exportPath build/release/export -allowProvisioningUpdates
   ```
   **Export uses the Xcode-signed-in account, no API-key flags** — the ASC key lacks cloud-signing
   rights when there is no local distribution cert. ExportOptions: `templates/ExportOptions.plist`
   (app-store-connect / upload).
5. ASC version: create it, attach the build, copy the promo text (ASC does not carry it over).
6. Listing via `scripts/asc.py --app <key>`: read-only first, then e.g.
   `python3 scripts/asc.py --app <key> --version <ver> --apply --only-screenshots --drop-preview --shots-dir <dir>`.
   `--keep-keywords` keeps owner-set keywords; a bare `--apply` rewrites the description from the metadata file.
   If the owner edits designs mid-flight → re-export and diff before every upload.
7. IAPs on first submission or after a rejection: add each object for review separately; re-save +
   re-attach stuck subscriptions (`references/app-review-log.md`).
8. **The owner** submits (manual or AFTER_APPROVAL release), tags (`git tag -a <ver>`) and releases.
   Status, read-only: `scripts/asc_status.py --app <key>`.
9. After review, read the reviewer's session in analytics (`iPhone99,7` = Apple automation) before
   guessing a rejection cause. Waiting > 4 days: Contact Us / expedited; never cancel-and-resubmit.
10. After launch: compare the metric named in step 1.

## 8. Release (KMP app with a Remote Config update gate) — say this unprompted on every release mention

Whenever a bump, archive, aab, TestFlight or Play upload comes up, recite:
1. Bump `CURRENT_PROJECT_VERSION` in `iosApp/Configuration/Config.xcconfig` = N (iOS CFBundleVersion
   **and** Android versionCode) + Android `versionName`. Never Xcode's General tab.
2. Before N reaches users: in **both** Firebase projects (Android and iOS) check `remote` → `appUpdate`
   has no leftover test values above N (a stray QA `latest` above N would prompt everyone on N) and
   `storeUrl` is the real Play / TestFlight link. Resting value `min N / latest N`.
3. Only after the store serves N: optionally `latest N` (prompt) or `min N` (force). Publishing earlier
   blocks users with nothing to install; release clients refetch at most hourly.
4. Edit the existing `remote` JSON; never drop the feature allow-list (empty = feature off for everyone).

## Done means

```
Criteria seen on sim: 1 ✓ 2 ✓ 3 ✗ (not checked: offline)   iPad compat ✓  SE ✓  dark ✓
Tests: 253/253 (core: 3 new, fail-first ✓); legacy nil-row test ✓
Upgrade install <prev> → <new>: ✓ (ledger: upgrade)   Review: 8 findings, all fixed, 248/248
Not done (owner): commit, archive upload, ASC attach, submit
```

## Lessons

- **A green suite is not evidence a schema change is safe.** A non-optional attribute with a default crashes
  upgrade installs with every test green. → Section 2 pattern + nil-row test + upgrade install.
- **App Review sees empty offerings on a first submission** (IAPs unreviewed). Ship an honest
  "plans unavailable" state.
- **Several rejections can land in one pass** (G4 iPad cut-off, 2.3.2 duplicate IAP promo images, 2.5.1
  Apple Health not named). Fix all and resubmit the same day. The API cannot delete promo images while
  the rejected submission is open (409) — send the owner to the UI.
- **The sim lies about Health** when `CODE_SIGNING_ALLOWED=NO` strips the entitlement.
- **Export with the API key can fail** where the Xcode-account export works. A pre-release review after QA
  still finds defects.
- **An App Preview takes the first slot of an Apple Search Ads ad** and can cost taps; ASC does not carry the
  promo text over to a new version.
- **KMP port: compile-green, runtime-broken** is the norm; owner sim QA after every batch finds what the
  gates miss (keychain -25300, a missing logout collector).
- **`available=false` from Remote Config**: the user id was published in the other Firebase project.
- **Privacy claims lag the binary** (a site saying "no analytics" with an analytics SDK live). Category
  reviews punish exactly this; policy, site, in-app privacy sheet and label move with the code.
- **A monetisation surface can crush activation** (an onboarding + paywall stack that collapses day-0
  core-action completion). Check the activation metric before it ships.
