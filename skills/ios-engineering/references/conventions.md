# Conventions — the detail behind SKILL.md §1–§7

App ids and paths: the app's block in `local/apps.yaml`. Your per-app conventions (which file already
does each thing): `local/skills/ios-engineering/`. Copy from the repo's existing file, not from memory.

## §1 project.yml (xcodegen)

Skeleton: `templates/project.yml`; extension snippet: `templates/widget-target.yml`; default-MainActor
settings for new apps: `~/.claude/skills/ios-app-bootstrap/templates/project.yml`.

- `options.bundleIdPrefix: <your reverse-DNS prefix>`, `deploymentTarget.iOS: "18.0"` (or the app's floor),
  `createIntermediateGroups: true`.
- `settings.base` carries `SWIFT_VERSION`, `TARGETED_DEVICE_FAMILY: "1"`, `MARKETING_VERSION`,
  `CURRENT_PROJECT_VERSION`, `CODE_SIGN_STYLE: Automatic`, `DEVELOPMENT_TEAM: <apple_team_id>`,
  `GENERATE_INFOPLIST_FILE: false` (the plist is written from `info.properties`).
- Info.plist properties in YAML, each non-obvious key with a comment saying why:
  `CFBundleDisplayName`, `CFBundleShortVersionString: "$(MARKETING_VERSION)"`, `CFBundleVersion:
  "$(CURRENT_PROJECT_VERSION)"`, `UIUserInterfaceStyle` (if the design is single-appearance), purpose
  strings, `UILaunchScreen { UIColorName, UIImageName }`, `UIRequiresFullScreen: true`, portrait only,
  `ITSAppUsesNonExemptEncryption: false`, `UIAppFonts` (static TTFs, licences in `Resources/Fonts`).
- Entitlements through `entitlements.properties` (e.g. `com.apple.developer.healthkit: true`, with a
  comment that the capability is still toggled on a signed build).
- Test target: `type: bundle.unit-test`, `GENERATE_INFOPLIST_FILE: true`, depends on the app; shared data
  files added by path with `buildPhase: resources` so `Bundle(for:)` decodes the same JSON the app ships.
- New apps: `SWIFT_APPROACHABLE_CONCURRENCY: YES`, `SWIFT_DEFAULT_ACTOR_ISOLATION: MainActor`,
  `SWIFT_UPCOMING_FEATURE_EXISTENTIAL_ANY: YES`, `ENABLE_USER_SCRIPT_SANDBOXING: YES`,
  `TEST_HOST`/`BUNDLE_LOADER` set explicitly, scheme `gatherCoverageData: true`. An existing app without
  default isolation — don't add it in passing.
- Localisation: `LOCALIZATION_PREFERS_STRING_CATALOGS: YES`, `SWIFT_EMIT_LOC_STRINGS: YES`,
  `developmentLanguage: en`.
- Local packages: `packages: { <App>Core: { path: Packages/<App>Core } }`. Package.swift can stay
  `.iOS(.v17)`; the app target's deployment target enforces the floor (`.v18` needs tools 6.0).

## §2 SwiftData

- Container: one process-wide `static let shared: ModelContainer = build()` in `AppModelContainer`;
  `fatalError` with the error on failure; App Intents use the same accessor. Template:
  `templates/AppModelContainer.swift`.
- `schema` is the single model list — tests and previews call
  `ModelContainer(for: AppModelContainer.schema, configurations: ModelConfiguration(isStoredInMemoryOnly: true))`.
- Additive attribute → `xValue: T?` + computed `x` (fallback = previous behaviour) + nil-row test + on-disk
  migration test (`templates/MigrationTests.swift`). Document the reason on the property
  («A Swift default is not a migration…»).
- New entity → non-optional allowed, comment that it is a new entity.
- Enums stored as `Codable` raw-value enums; display names are computed (`Tier.label`) so copy changes
  never touch stored values.
- Install history (`AppVersionRecord`) survives `resetAll()`; user data does not.
- Store-reading services retain the container: `@ObservationIgnored private let container`.
- Read-only catalogs are a bundled SQLite/FTS file, not SwiftData; user data only in SwiftData.
- Money: `Int` minor units + currency code; `Decimal` only for arithmetic/formatting.
- For an additive field the optional pattern is the migration; `SchemaMigrationPlan` is not needed.
  A real transform (split/rename/type change) → VersionedSchema + plan + the on-disk test with `LegacyV1`
  frozen exactly as the last release shipped (copy it from the release tag:
  `git show <tag>:<App>/Core/Model/Models.swift`).

## §3 Concurrency (code shapes)

```swift
// EntitlementStore — stream ownership
@MainActor @Observable final class EntitlementStore {
    @ObservationIgnored private var observerTask: Task<Void, Never>?
    private func observeCustomerInfo() {
        observerTask?.cancel()
        observerTask = Task { [weak self] in
            for await info in Purchases.shared.customerInfoStream {
                guard let self else { return }
                self.apply(info)
            }
        }
    }
}
```
```swift
// AppDelegate — ObjC delegate on an inferred-@MainActor class
nonisolated func userNotificationCenter(_ c: UNUserNotificationCenter, didReceive r: UNNotificationResponse,
                                        withCompletionHandler done: @escaping () -> Void) {
    let id = r.notification.request.identifier
    Task { @MainActor in NotificationCenter.default.post(name: .appNotificationTapped, object: id) }
    done()
}
```
```swift
// NotificationScheduler — values out, then detach
@MainActor static func reschedule(from settings: AppSettings, …) {
    let morning = timeComponents(from: settings.morningTime)   // read on main
    Task.detached { let center = UNUserNotificationCenter.current(); … }
}
```
```swift
// main-queue observer
NotificationCenter.default.addObserver(forName: AVPlayerItem.didPlayToEndTimeNotification,
                                       object: item, queue: .main) { [weak self] _ in
    MainActor.assumeIsolated { self?.startIdle() }
}
```
- Pure functions on a main-actor type: `nonisolated static func plan(...)`, `nonisolated static let maxFreeItems = 6`.
- Data seams: `protocol ContentSource: Sendable { func available() async -> [Item] }`.
- Default-MainActor repos: see SKILL.md §3 and bootstrap traps (UIColor providers, ObjC blocks, `@Sendable`
  label closures, `nonisolated deinit {}`).
- Heavy work (OCR, matching, export, aggregation) never on the main actor; `Task.detached` + a data
  signature so it reruns only when inputs change.

## §4 RevenueCat / StoreKit

- `Config/RevenueCatConfig.swift` holds: `apiKey` (public `appl_…`, sentinel `appl_PLACEHOLDER` = offline mode),
  `entitlementID`, `offeringID`, product ids with price + date comments (`<app>_weekly` with trial,
  `<app>_annual`, `<app>_monthly`, optional `<app>_lifetime`), `termsURL`/`privacyURL`, `isConfigured`.
- Alternative: keys in Info.plist (`RevenueCatAPIKey`; Debug = RC Test Store key, Release = `appl_`) and
  plans resolved by package id: `$rc_weekly`, `$rc_annual`, custom packages for one-time decline / final
  offers, each one-time via a persisted `…OfferUsed` flag.
- The paywall UI is ours; RevenueCat sells and unlocks. Prices always from the offering, with documented
  fallbacks only when `!isConfigured` (previews/dev).
- Entitlement → status for UI: `PremiumStatus(productID, isTrial, expiration, willRenew, hasBillingIssue)`.
- Purchase chokepoint emits analytics: `trial_started` vs `purchase_completed` by `periodType == .trial`,
  or `paywall_purchase_started/completed/failed/cancelled`.
- Recovery/win-back offer is a separate one-time product in its own offering.
- Trial reminder notification before the trial ends; the scheduler must not cancel it on settings edits.
- Legal: Terms + Privacy on every paywall, readable size and contrast.

## §5 PostHog

Facade: `Analytics.start(backend:distinctID:person:)` registers `build_type`, then `identify(distinctID,
properties: person.properties)`; `track` / `screen` / `setPerson` (`$set` only when the snapshot changed) /
`setEnabled`. `AnalyticsBackend: AnyObject` protocol with `NoopBackend` and `SpyBackend` (tests). Templates:
`templates/Analytics.swift`, `templates/AnalyticsEventTests.swift`.

Event naming: `<surface>_<object>_<verb past>` in snake_case — `paywall_purchase_completed`,
`onboarding_step_viewed`, `item_joined`, `app_version_changed`. Properties are small and coarse
(score buckets, text-length buckets, counter buckets).

Privacy bans per app category, written into the repo: no PII, typed text, step counts, names; health
apps never send cycle/symptom/health values or dates; anonymous apps never `identify` and send
`query_length`, never the query.

Reading data: the PostHog MCP's active project is shared state — `switch-organization` + `switch-project`
to the app's `posthog_project_id` (`local/apps.yaml`) first. RevenueCat is the money source of truth;
PostHog installs undercount when the SDK shipped after the first release.

## §6 Widgets / App Group

See SKILL.md §6. Snapshot struct pattern: `Codable, Equatable, Sendable`, static `appGroupID`, versioned
`defaultsKey` (`<name>-snapshot-v1`), `load()` / `save()` over `UserDefaults(suiteName:)`. Bump the key
suffix when the shape changes instead of migrating.

## §7 DEBUG hooks

See SKILL.md §7 and `templates/DemoSeed.swift`. Keep a list of the hooks in the repo's CLAUDE.md
(`-<App>OpenCollection`, `-<App>SeedCount <n>`…). Present-once hooks carry a latch.
