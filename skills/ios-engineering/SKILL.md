---
name: ios-engineering
description: "Use when writing or reviewing Swift/SwiftUI code in an existing iOS app: xcodegen, SwiftData models and migrations, Swift 6 concurrency, RevenueCat/StoreKit, analytics, widgets, tests, builds. Use INSTEAD of the generic swiftdata, swift-concurrency, storekit, widgetkit skills when they disagree. Triggers: \"add a field to the model\", \"migration\", \"paywall doesn't load plans\", \"Swift 6 complains\"."
---

# iOS engineering — how we write it

Your own cases for this skill live in `local/skills/ios-engineering/` (git-ignored, see
`local.example/README.md`). Read them first if they exist; append the outcome of each round/incident there.
App ids, bundle ids and paths: the app's block in `local/apps.yaml`.

This is the **code** layer. The delivery process (risk table, gate, review, upgrade install, ASC,
submit) is `skills/mobile-feature-delivery` — read it for *how a change ships*; this skill is *how the
code is written*. A brand-new app is `~/.claude/skills/ios-app-bootstrap` (its `templates/CLAUDE.md`
holds the universal trap library; this skill references it, it does not copy it).

**Precedence:** the repo's own `CLAUDE.md` > this skill > generic framework skills. When a generic
skill (swiftdata, swift-concurrency, storekit, widgetkit…) contradicts a rule here, the rule here is
the one that was paid for. Say so in one line when you override it.

## 0. Before touching code (every time)

1. Read the repo's `CLAUDE.md` and its memory index
   (`~/.claude/projects/<repo path with / as ->/memory/MEMORY.md`).
2. Note the repo's project generator, Swift mode / default isolation, deployment target, persistence,
   SDKs and test runner — they decide half the answers. Keep that row in your local notes.
3. Generated project? Run `xcodegen generate` after **any** add/move/delete of a file: a new `.swift`
   file without regeneration gives a green test run against a stale file set — a false pass.
4. Do not commit (the owner commits). Do not run `xcodebuild` from parallel sub-agents (shared-tree
   build races) — integrate and build yourself.

Module trees and where each concern lives: `references/architecture.md`.

## 1. Project setup — xcodegen conventions (`references/conventions.md` §1, `templates/project.yml`)

- `project.yml` is the only source; `.xcodeproj` is git-ignored. Never edit `.pbxproj`, never bump
  versions in Xcode's General tab. `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` live in
  `settings.base`; Info.plist reads `$(MARKETING_VERSION)` / `$(CURRENT_PROJECT_VERSION)` — the same
  two variables go into every extension's Info.plist so app and extension never drift.
- Info.plist keys are written in `targets.<App>.info.properties` **with a comment saying why** (e.g.
  `NSHealthUpdateUsageDescription` exists because upload validation demands it even for read-only HealthKit).
- Every SPM package has a comment naming the one file allowed to import it
  (`# Only Core/Analytics/PostHogBackend.swift may import it`).
- `ITSAppUsesNonExemptEncryption: false`, `TARGETED_DEVICE_FAMILY: "1"`, `UIRequiresFullScreen: true`,
  portrait only — iPhone-only apps still run on iPad in the compat window (see traps).
- Test target shares a resource with the app by path, never by copy
  (`- path: App/Core/Content/content.json  buildPhase: resources`).
- StoreKit config for the sim goes in the scheme (`schemes.<App>.run.storeKitConfiguration`). It only
  loads when **Xcode** runs the scheme — `simctl launch` ignores it.
- Optional: Debug keeps a separate bundle id (`<bundle>.debug`) so sim data stays put and analytics split
  store vs debug by `$app_namespace`. Cost: a Debug build on a device cannot load plans → purchases via TestFlight.
- A hand-kept `.pbxproj` (no xcodegen): a version bump touches every target × configuration slot (app +
  widget × Debug/Release); bump all of them together.

## 2. Persistence and migrations — THE rule (`references/conventions.md` §2)

**A new stored attribute on a `@Model` that already shipped is optional storage + a computed
non-optional accessor whose fallback is the previous behaviour.** A Swift default is not a migration.

```swift
// TaskItem — additive field on a shipped model
var sourceValue: TaskSource?                 // the only stored, migrating attribute
var source: TaskSource {                     // computed → ignored by @Model
    get { sourceValue ?? .daily }            // legacy rows = what the app did before
    set { sourceValue = newValue }
}
```
Same shape for collections and dates: `unlockedItemsValue: [Item]?` → `unlockedItems { unlockedItemsValue ?? [defaultItem] }`.

- **Why:** a non-optional attribute with a Swift default crashes upgrade installs (SIGABRT in the
  generated getter) while every in-memory test stays green. Reproduced in a SwiftPM harness:
  non-optional-with-default → `Exited with unexpected signal code 6`; the optional pattern → passes.
- **This overrides** the generic `swiftdata` skill's «keep required scalars nonoptional when
  initializers, defaults, or migrations provide valid values». Defaults do not reach old rows.
- **New entity:** non-optional is fine (lightweight migration adds whole entities). The two cases pull in
  opposite directions — say so in a comment on the new entity.
- **One schema list:** `AppModelContainer.schema` is public and every test/`#Preview` builds from it
  (hand-copied lists crash with `could not locate an NSEntityDescription`). New entity = add it there
  **and** to the app's reset-all path.
- **Never rename a stored attribute** (drops the column's data). Need a new name in code → computed alias.
- CloudKit-ready apps: every stored property defaulted or optional, optional to-many, no
  `@Attribute(.unique)` — from day one, because retrofitting is a migration.
- **Tests:** (a) a nil-row unit test (set `xValue = nil`, assert the accessor returns the legacy value);
  (b) the on-disk test in `templates/MigrationTests.swift` — writes a store with a frozen `LegacyV1`
  copy of the model, reopens it with the current schema, reads the row. Passes with the optional pattern,
  aborts (signal 6) with a default. Run it for every additive change.
- `ModelContext` does not retain its container: services keep `@ObservationIgnored private let container`;
  tests hold the container for the test's lifetime. `context.model(for:)` on a deleted id is a trap, not nil —
  look up by `#Predicate { $0.persistentModelID == id }`.

## 3. Concurrency — patterns that hold (`references/conventions.md` §3)

Two modes exist; follow the repo, don't convert it in a feature change.

- **Swift 6, no default isolation:** observable services are `@MainActor @Observable final class`
  (`EntitlementStore`, the main data service); facades are `@MainActor enum` (`Analytics`, `DemoSeed`);
  pure math inside a main-actor type is `nonisolated static func`; data seams are
  `protocol ContentSource: Sendable` + `struct Client: Sendable`.
- Long-lived streams: `@ObservationIgnored private var observerTask: Task<Void, Never>?` +
  `Task { [weak self] in for await info in Purchases.shared.customerInfoStream { … } }`.
- Off-main system work: capture plain values first, then `Task.detached { … }` (a notification
  scheduler reads times from settings before detaching).
- ObjC delegate protocols on a `@MainActor` class: witnesses are `nonisolated` and hop back with
  `Task { @MainActor in … }` (`AppDelegate`, `UNUserNotificationCenterDelegate`).
- `NotificationCenter` observer with `queue: .main` → body wrapped in `MainActor.assumeIsolated { … }`.
- **Default-MainActor targets:** `UIColor { traits in }` providers, ObjC-callback closures and C function
  pointers must be formed in `nonisolated` code; `@Sendable` label closures (`PhotosPicker`) read values
  into a `let` first; a `@MainActor` class with a `deinit` needs `nonisolated deinit {}` (Swift 6.2 /
  Xcode 26: SIGABRT in libmalloc when released off-main); default-argument service construction breaks →
  optional param + `?? Service()` in the body.
- Swift 5 repos: a non-isolated `@Observable` store hops with `await MainActor.run { self.apply(info) }`.
- Heavy aggregation off-main with a data-signature guard (`Task.detached` + a signature of the inputs) —
  it kills recompute-per-`body` bugs.

## 4. Monetisation — RevenueCat wiring (`templates/EntitlementStore.swift`, `references/conventions.md` §4)

- `EntitlementStore` (`@MainActor @Observable`) is the only `import RevenueCat` besides the paywall.
  Config enum (`Config/RevenueCatConfig.swift`) holds public key, entitlement id, offering ids, product
  ids with price comments, Terms/Privacy URLs.
- **Guard every `Purchases.shared` with `RevenueCatConfig.isConfigured`** — `Purchases.shared` before
  `configure` is a `fatalError`, not a throw; `try?` does not catch it.
- `Purchases.configure(withAPIKey:appUserID: InstallIdentity.id.uuidString)` — a Keychain install UUID
  that is also the analytics `distinct_id` (and any backend cohort key), so RC's PostHog integration lands
  `rc_*` on the same person. The reverse also works: identify PostHog with `Purchases.shared.appUserID`.
- `Purchases.shared.attribution.enableAdServicesAttributionTokenCollection()` **after** configure — not on by
  default; without it Apple Search Ads installs arrive as "No Attribution".
- Seed from `customerInfo()`, then observe `customerInfoStream`; trial = `entitlement.periodType == .trial`.
- Paywall rules (all came from rejections or review findings — `references/traps.md`):
  offerings load → 3 attempts with 1 s/2 s back-off → honest `.unavailable` state («Plans aren't available
  right now», Try Again, Restore reachable) + `paywall_offerings_failed` / `paywall_unavailable` events;
  name a trial only if `introductoryDiscount.paymentMode == .freeTrial` **and**
  `checkTrialOrIntroDiscountEligibility == .eligible` (3.1.2); restore returns
  `.restored / .nothingToRestore / .failed(msg)` — never swallow the error; resolve packages by
  convenience slot then product id, or by package id `$rc_annual` (works for Test Store and App Store
  alike); Terms + Privacy links live and 200 (not a bot-challenge 403).
- Debug builds may run the RC **Test Store** key; all purchase E2E = TestFlight + sandbox.

## 5. Analytics — PostHog conventions (`templates/Analytics.swift`, `references/conventions.md` §5)

- **One file imports PostHog** (`Core/Analytics/PostHogBackend.swift`). Call sites use
  `@MainActor enum Analytics { track / screen / setPerson / setEnabled }`.
- **Typed taxonomy:** `enum AnalyticsEvent` with associated values → `name` + `properties`; `snake_case`
  names and keys; values = enum raw values, small ints, bools, string arrays; never names, typed text,
  health or personal data. `AnalyticsEventTests.golden` pins the full list — **a new event is added to
  `samples` and to the golden list in the same change.**
- SDK config: lifecycle events ON, crash autocapture ON; `captureScreenViews`,
  `captureElementInteractions`, `enableSwizzling`, `sessionReplay`, `preloadFeatureFlags` OFF unless the
  app reads flags (don't add flag reads without asking).
- **Super-properties registered before `identify`:** `build_type` = `debug|release`. Never call it
  `build` — collides with the SDK's lifecycle `build` (CFBundleVersion). Add `app`, `app_version` and
  coarse bucketed counters where useful (`0,1-9,10-49,…,1000+`).
- **Store vs debug namespace:** filter store users by `$app_namespace` (the release bundle id) —
  `Application Installed` fires before super-properties and carries no `build_type`. Dashboards:
  `build_type is_not debug` + `$is_testflight is_not true`. `iPhone99,7` = Apple's automated review run.
- Unit-test host is the app: swap in `NoopBackend` when `XCTestConfigurationFilePath` is set.
- Opt-out: track the toggle event, `flush()`, then `optOut()`; opted-out users load nothing.
- **Never `onAppear`-track inside always-mounted panes** — inline paywalls take `isActive:` (otherwise
  phantom `paywall_shown` at launch). Tab roots are tracked from the tab selection.
- Reading data: the PostHog MCP's active project is shared state — switch org/project to the app's
  `posthog_project_id` from `local/apps.yaml` first. Check the project's host (US vs EU) matches the
  code default, or set `POSTHOG_HOST`.

## 6. Widgets and App Group (`templates/widget-target.yml`, `templates/AppModelContainer.swift`)

- Widget reads a **snapshot**, not the SwiftData stack: mirror a few values into a versioned
  `Codable` snapshot in the App Group `UserDefaults` and let the widget recompute with the same
  deterministic engine; the bridge saves + calls `WidgetCenter.shared.reloadAllTimelines()` **only when
  the snapshot changed**.
- Sharing exact source files with the widget: add them to the widget target's `sources:` list, never
  duplicate files.
- Handing SwiftData a `groupContainer` the process is not entitled to **traps** (SIGTRAP), it does not throw:
  probe `FileManager.containerURL(forSecurityApplicationGroupIdentifier:) != nil` first, fall back to the
  default store (unsigned test host, `CODE_SIGNING_ALLOWED=NO` builds).
- **Image pixel budget:** WidgetKit archives every image an entry draws; over budget → `ArchivingError.imageTooLarge`,
  placeholder forever (medium ≈ 2.1 Mpx, small ≈ 1 Mpx). Ship widget-sized assets and pin the budget with a
  test. Logs: `xcrun simctl spawn <udid> log show --predicate 'process == "<App>Widgets"'`.
- App Group `UserDefaults` = privacy-manifest reason `1C8F.1` (standard suite only = `CA92.1`).
- Fonts and string catalogs must exist in the extension too (register fonts in every process; give the
  widget its own `Localizable.xcstrings` and compile shared display helpers into both targets).
- Widgets often see near-zero adoption in small apps. Ask before building one.

## 7. DEBUG launch-arg seeds (`templates/DemoSeed.swift`)

- File wrapped in `#if DEBUG … #endif`, `@MainActor enum DemoSeed`,
  `static var requested: Bool { ProcessInfo.processInfo.arguments.contains("-<App>DemoSeed") }`,
  `guard requested, profile == nil` — never touches an existing profile, never in Release.
  Called from `App.init` inside `#if DEBUG`.
- Names are `-<App><Thing>`: `-<App>DemoSeed -<App>DebugPremium -<App>OpenTab <tab>`
  (value args read with `firstIndex(of:)`). Env-var hooks work too (`OPEN_SCREEN`, `PAYWALL`) →
  `SIMCTL_CHILD_OPEN_SCREEN=… xcrun simctl launch …` / `devicectl … --environment-variables`.
- Forced premium: `EntitlementStore` reads `-<App>DebugPremium` in a `#if DEBUG static let`, sets a
  realistic status (weekly trial ending in 2 days) and `apply(_:)` early-returns so a real
  CustomerInfo can't undo it.
- Present-once hooks need a `@State`/static latch (`debugHookDone`) — `.task(id:)` re-fires on dismissal.
- Seed realistic data for screenshots (30 days of use, an upward trend with one bad weekend, a streak).

## 8. Tests — tiers

- **core** (persistence, money, score math, gates, notifications schedule, anything reading older data):
  test first, confirm it fails without the fix. **ui:** one smoke test per screen + eyes on the sim.
  Keep core small (≈ 5 rows per feature); gate tests include one that deliberately does NOT call `load()` first.
- XCTest or Swift Testing (`@Test`, `#expect`) — follow the repo, never mix inside a repo.
- Pin specs as golden tests: analytics list, content counts, design-token invariants, button metrics,
  widget pixel budget.
- Pure engines take dates as input — no `Date()` inside engine logic (seeded by date).
- Warnings: only a **clean** build re-emits them (`xcodebuild clean build-for-testing … | grep warning:`).
- No simulator in the session: cross-compile packages with
  `swift build --sdk "$(xcrun --sdk iphonesimulator --show-sdk-path)" --triple arm64-apple-ios18.0-simulator`.

## 9. Commands (full list: `references/commands.md`)

```sh
xcodegen generate
xcodebuild test -project <App>.xcodeproj -scheme <App> \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
  -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO
#   ambiguous name → 'platform=iOS Simulator,id=<udid>'  (xcrun simctl list devices available)
#   one test → -only-testing:<App>Tests/<Class>/<testMethod>
cd <Kit> && swift test                               # logic in a local package
xcrun simctl launch <udid> <bundle_id> -<App>DemoSeed -<App>DebugPremium
xcrun simctl io <udid> screenshot /tmp/shot.png      # trust this, not the MCP panel's own frame
```
Device and simulator walk-through (iPad compat window, SE, dark/light, upgrade install) →
`mobile-feature-delivery` §5. HealthKit needs a build **without** `CODE_SIGNING_ALLOWED=NO`.

## 10. Release-build traps (procedure lives in `mobile-feature-delivery` §7)

- Build number strictly increases per upload, set in `project.yml`. An upload script that passes
  `CURRENT_PROJECT_VERSION=$BUILD` on the command line leaves `project.yml` at the old number — bump it too.
- No emoji in release notes / What's New — tofu boxes.
- `PrivacyInfo.xcprivacy` (`templates/PrivacyInfo.xcprivacy`) = ASC App Privacy label = policy: RevenueCat →
  Device ID (IDFV), PostHog GeoIP → Coarse Location. New SDK = update all.
- Export signs with the Xcode-logged-in Apple ID; the ASC API key has no cloud-signing rights.
- Variable fonts: named instances don't resolve by PostScript name on iOS → ship static per-weight TTFs.
  Check with `UIFont(name:)` in the simulator, not NSFont on macOS.

## Traps / Lessons (full library with fixes: `references/traps.md`)

- SwiftData additive attribute with a default crashes upgrade installs while in-memory tests pass → run
  the on-disk migration test, don't argue from in-memory tests.
- An event fired from two code paths for one user action double-counts → send once per action, tag the
  path in a property. Count users, not events (`paywall_shown` fires per locked-item tap).
- Parallel builds fill the disk → at most 2 DerivedData folders at a time.
- Reading `UIWindow` insets inside `body` → AttributeGraph cycle, screen freezes empty → use SwiftUI geometry.
- Restore that swallows the error tells a paying user «no purchases» → `RestoreOutcome`.
- Guideline 4: CTA cut off on the iPad compat window → pinned-CTA screens scroll or `ViewThatFits`;
  `CODE_SIGNING_ALLOWED=NO` makes HealthKit "Connect" look dead.
- `build` super-property collides with the SDK's `build`; inline paywalls in mounted panes fire phantom
  `paywall_shown`; WidgetKit image budget; App Review sees empty offerings for first-version IAPs.
- `Purchases.shared` before configure = `fatalError` → `isConfigured` guard.
- `@MainActor` class + synthesized deinit can crash → `nonisolated deinit {}`; lazy VM in an empty
  `Group { if let vm }` + `.onAppear` = blank screen → build VMs eagerly.
- AdServices token not collected by default → ASA "No Attribution"; variable-font tofu; emoji in notes.
