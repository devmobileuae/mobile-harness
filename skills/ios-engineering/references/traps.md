# iOS trap library

Format: **what broke** → fix. Your dated, per-app entries live in `local/skills/ios-engineering/`
(append new incidents there; promote the generic lesson here). Universal toolchain traps without an app
attached (didSet recursion on `@Observable`, one sheet per view, `simctl privacy grant photos` on iOS 26,
`URL.path()`…) live in `~/.claude/skills/ios-app-bootstrap/templates/CLAUDE.md` — they are not repeated.
Review rejections and ASC submission traps: `skills/mobile-feature-delivery/references/app-review-log.md`.

## Persistence / migrations

- **Non-optional attribute with a Swift default added to a shipped `@Model`** → the upgrade install crashes
  (SIGABRT in the generated getter) while every in-memory test passes; reproducible in a SwiftPM test
  (`Exited with unexpected signal code 6`). → optional `xValue` + computed `x`, nil-row test, and
  `templates/MigrationTests.swift` (that exact on-disk test).
- **Test/preview containers with hand-copied model lists** — one misses a model → runtime
  `could not locate an NSEntityDescription`. → `AppModelContainer.schema` public, every container built from it.
- **`context.model(for:)` on a deleted id** returns an invalidated placeholder; the first property access traps
  («backing data could no longer be found»). → fetch by `#Predicate { $0.persistentModelID == id }`; dead ids no-op.
- **Renaming an entity/attribute** is free only before ship and before CloudKit is live; after ship it is data loss.
- **Keychain query attributes changed** (e.g. adding `kSecAttrAccessible`) stop matching pre-existing items →
  `-25300` on upgrade. Same class as SwiftData: a storage-shape change is a migration.
- **Simulator without the App Group container:** SwiftData silently falls back to in-memory (benign CoreData
  log noise). Do not chase it on the sim; check on a signed device build.

## Concurrency / runtime isolation

- **`@MainActor` class with a synthesized `deinit`** (Swift 6.2, Xcode 26) crashes when released off-main
  (SIGABRT in libmalloc). → explicit `nonisolated deinit {}` on every `@MainActor` class that has one.
- **Default-MainActor target** breaks default-argument service construction and C-function-pointer callbacks.
  → optional params + `?? Service()` inside the body; mark callbacks `nonisolated`.
- **`UIColor { traits in }` providers inferred MainActor** are resolved by SwiftUI/Charts off-main →
  `dispatch_assert_queue_fail`; ObjC block closures (`PHPhotoLibrary.performChanges`) trap the same way.
  → form them in `nonisolated` functions/types (design-token files are the riskiest).
- **`UNUserNotificationCenterDelegate` on a `@MainActor` `AppDelegate`:** witnesses must be `nonisolated`
  (protocol is not isolated, parameters not `Sendable`); without the delegate iOS drops a due notification
  while the app is foreground. → `Task { @MainActor in post(...) }`.

## SwiftUI runtime

- **Reading `UIWindow` safe-area insets inside `body`** → AttributeGraph cycle, a screen freezes empty on
  some phone sizes. → derive from SwiftUI geometry.
- **A pushed/tabbed screen declaring its own `NavigationStack`** compiles and crashes at runtime:
  `AnyNavigationPath.Error.comparisonTypeMismatch`. → only sheet-presented screens own a stack
  (`SettingsScreen(presentation: .modal)` vs `.pushed`).
- **`ForEach(slots, id: \.hour)`** gave 7:00 and 7:30 one id → holes in a list; a comment claiming the id was
  unique fooled the reviewer. → key by `enumerated()` offset or a truly unique value.
- **`.task` + `.onAppear` both reloading** → two concurrent loads on every pop-back/tab re-visit. → `.task`
  only; one-shot DEBUG hooks need a latch.
- **Lazy `@State var vm: VM?` set in `.onAppear` inside `Group { if let vm { … } }` with no else** → zero
  children, `onAppear` never fires, blank screen. → build VMs eagerly in init/parent.
- **iOS 26 already floats sheets** — a custom floating sheet draws a second panel. → only paint
  `presentationBackground` on 26, keep the inset card for iOS 18.

## Monetisation / paywall

- **Debug bundle id differs from Release** → plans cannot load on a device. → test purchases through
  TestFlight (an internal group that gets every build).
- **`simctl launch` does not load the scheme's `.storekit` file** → paywall prices/trial lines empty. → run
  from Xcode for StoreKit-config checks.
- **Restore swallowed a network error** and told a paying subscriber they had no purchases. →
  `RestoreOutcome { restored, nothingToRestore, failed(String) }`.
- **App Review sees empty offerings** (first-version IAPs are not served before approval) and static prices with
  a CTA that can only fail; a purchase guard that returns *before* any event leaves a dead tap untraced. →
  honest unavailable card, Try Again, Restore reachable, `paywall_unavailable` + `paywall_offerings_failed`;
  offerings retried 3× (1 s, 2 s).
- **RevenueCat does not collect the AdServices token by default** → Apple Search Ads installs arrive as
  "No Attribution". → `Purchases.shared.attribution.enableAdServicesAttributionTokenCollection()` right after `configure`.
- **`Purchases.shared` before `configure()`** → `fatalError` (not a throw; `try?` doesn't help). → guard with
  `Purchases.isConfigured` / `RevenueCatConfig.isConfigured`.
- **A trial-end reminder wiped by `reschedule()`'s `removeAll`.** → persist it and re-assert it inside
  `reschedule()`, or never cancel the trial id on settings edits.
- **RevenueCat's API shows different prices / `duration = null`** than the live StoreKit sheet. → trust
  StoreKit/ASC for prices; `duration=null` on app_store products is not a blocker.
- **A local "free window" stamp stored in SwiftData resets on reinstall.** → anchor at
  `min(customerInfo.originalPurchaseDate, firstLaunchAt)`.
- **A win-back offer shown only on first paywall dismiss** reads to App Review as "purchases did not load"
  (2.1(b)). → attach only visibly purchasable products, or give Review Notes the exact path.

## Analytics

- **One finish fired the completion event twice** (two code paths). → one event per finish, a property for the path.
- **`paywall_shown` fires on every tap of a locked item**; some events lack the id you want to group by. →
  read users not events; note quirks in the repo's analytics doc.
- **PostHog's default test-account filter can be inverted** (e.g. filtering to the owner's country), so
  default insights show only the owner. → check the project filter first; exclude test traffic explicitly.
- **Inline paywalls in always-mounted panes** log phantom `paywall_shown` at launch. → `isActive:
  router.tab == …`; never `onAppear`-track in a pane. A super-property named `build` collides with the SDK's
  lifecycle `build` (CFBundleVersion) → `build_type`, registered before `identify`.
- **The unit-test host is the app** — test runs register as installs. → `NoopBackend` when
  `XCTestConfigurationFilePath` is set; the version ledger skips the test host too.
- **A `fullScreenCover` paywall is invisible to a sheet host's `onChange(activeSheet)` observer.** → the cover
  fires `paywall_shown`/`paywall_dismissed` itself.
- **"The event never fired"** when the test purchases ran on a build without the event. → confirm the build
  carries the event before calling capture broken.
- **SDK host default (EU) vs project region (US)** → nothing arrives. → set `POSTHOG_HOST`. SDK renames
  (`apiKey` → `projectToken`) break on bumps.

## Widgets / App Group / extensions

- **Widget never leaves its placeholder:** it drew a full-screen texture; WidgetKit archives every image and
  rejects the entry (`ArchivingError.imageTooLarge`, medium ≈ 2.1 Mpx, small ≈ 1 Mpx). → widget-sized @3x
  asset + a test pinning the budget; debug with `log show --predicate 'process == "<App>Widgets"'`.
- **SwiftData *traps* (not throws) given a `groupContainer` the process isn't entitled to** (unsigned test
  host). → probe `containerURL(forSecurityApplicationGroupIdentifier:)`, fall back to `ModelConfiguration()`.
  Remove the `1C8F.1` privacy reason with the App Group.
- **Hand-kept pbxproj:** app + widget × Debug + Release version slots must move together; an extension on
  another `CFBundleVersion` draws an upload warning. xcodegen apps use `$(CURRENT_PROJECT_VERSION)` in both plists.
- **Engine display names English inside widgets.** → a shared display helper compiled into app + widget wraps
  them in `String(localized:)`; the widget has its own `Localizable.xcstrings`.

## Fonts / localisation

- **Tofu with a variable font:** a named instance resolved to the variable file's default instance, which
  renders `.notdef` on some iOS versions (the newest sim may not reproduce). → static per-weight TTFs via
  `fontTools.varLib.instancer`, registered first in `App.init`.
- **`.xcstrings` duplicate keys differing by case/apostrophe** → translating the orphan twin produced a
  Swift-symbol collision → BUILD FAILED. → revert orphans to `{}`.
- **`xcodebuild` does not refresh `Localizable.xcstrings`.** → run the repo's sync script. Wire formats and
  analytics props never localize (theme id `food`, not the English title).

## Build / toolchain / environment

- **Parallel worktree builds fill the disk.** → keep at most two DerivedData folders; delete only with the owner's OK.
- **`CODE_SIGNING_ALLOWED=NO` strips entitlements:** HealthKit fails with `Missing com.apple.developer.healthkit
  entitlement`, Connect looks dead. → build without the flag (ad-hoc `-` signing embeds the simulated
  entitlements) to test Health; keep the flag for the gate.
- **iOS Simulator MCP: «Xcode is installed but not selected».** → owner runs
  `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` (needs their password).
- **Warnings reached a commit** because an incremental build doesn't re-emit diagnostics. →
  `xcodebuild clean build-for-testing … | grep warning:`.
- **No Xcode GUI/sim in session.** → cross-compile SPM packages for the iOS simulator triple.
- **`name=iPhone 16 Pro` stops resolving** once several runtimes have that name → use `id=`.
- **zsh: `for x in $var` does not word-split.**
