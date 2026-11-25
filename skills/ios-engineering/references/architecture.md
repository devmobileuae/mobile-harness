# Architecture — the shapes that hold up

"Where does X go" is answered by the repo's existing tree, not by a pattern catalogue. Your own apps'
trees live in `local/skills/ios-engineering/` — read the one for the repo you are in. Two shapes work:
**services + pure engines** and **strict MVVM with one composition root**. Don't move a repo from one
shape to the other inside a feature.

## Services + pure engine (example: a habit tracker)

```
App/
  App/        <App>App.swift (composition: one ModelContainer, a few @Observable services into .environment)
              AppDelegate.swift (UNUserNotificationCenterDelegate, nonisolated witnesses)
              RootRouter.swift (onboarding vs tabs)  RootTabView.swift  DemoSeed.swift (#if DEBUG)
  Config/     RevenueCatConfig.swift  AnalyticsConfig.swift   (public keys + ids + legal URLs)
  Core/
    Model/        Models.swift          (@Model types; additive fields = *Value optionals)
    Store/        AppModelContainer.swift (schema list)  DataService.swift (@MainActor @Observable, single truth)
                  EntitlementStore.swift  PremiumStatus.swift
                  AppVersionLedger.swift (install history, kept by resetAll)
    Engine/       ScoreEngine.swift (ALL math, pure, tuning constants on top)
    Content/      content.json  ContentSource.swift (Sendable seam: remote / local)
    Analytics/    Analytics.swift (facade)  AnalyticsBackend.swift  AnalyticsEvent.swift (taxonomy)
                  PostHogBackend.swift (only PostHog import)
    Notifications/ NotificationScheduler.swift (pure requests(...) + Task.detached reschedule)
    Design/       Theme  Palette  Typography  Buttons
  Features/   one folder per screen family (Home, History, Settings, Paywall, Onboarding…)
  Resources/  Fonts
  PrivacyInfo.xcprivacy  <App>.entitlements  Info.plist (generated from project.yml info:)
<App>Tests/   engines, golden lists, nil-row migration tests, facade spies
```
Rules that come with the shape: every mutation inserts an event row then `refresh()` re-derives from the
store; live progress is recomputed from sources of truth, never stored; live inputs are passed *into*
service methods, not retained (no retain cycles); helper services are built per call from a
`ModelContext`, not held by other services.

## App + pure Kit package (example: a forecast app with a widget)

```
<App>/        <App>App.swift (analytics setup BEFORE the app model; fonts registered)
  Models/ Services/ ViewModels/ Views/
<App>Kit/     SPM — deterministic engines + snapshot types + bundled content JSON
<App>Widgets/ provider, widgets, Localizable.xcstrings
Shared/       display helpers compiled into app AND widget
backend/      optional worker for sync features
```
Engines are deterministic and seeded by date (no `Date()` inside the Kit) so the widget and the app compute
the same reading from a few snapshot numbers. Design tokens come only from the design-system package —
raw hex is a bug (a design-lint subagent on every UI diff catches it).

## Flat feature files (example: a small puzzle game)

```
<App>/  <App>App.swift (DEBUG env hooks with debugHookDone latch)  RootView  feature views
        ContentStore (remote manifest sync)  Models  Paywall  EntitlementStore  Analytics (only PostHog import)
        Localizable.xcstrings  PrivacyInfo.xcprivacy
Config/<App>.storekit       docs/analytics.md (every event + property — the privacy policy can point here)
tools/  appstore/ (upload, listing)  l10n/  content/  device_run.sh
```
When the analytics doc is part of the public privacy story, update it with every event change.

## Strict MVVM, one composition root (example: a collection app)

```
<App>/
  App/            entry, root navigation, AppEnvironment (private init; live(...) / preview())
                  AppEnvironment+ViewModels.swift (VM factories)
  Features/<F>/   Screen + ViewModel pairs
  Core/<Domain>/  domain services (no SwiftUI imports)
  DesignSystem/   one glass helper, one remote-image view, shared sheets
<App>Tests/       Swift Testing, Fixtures/ as resources
tools/            data pipelines, proxies
```
Views render, VMs decide; VMs import no SwiftUI and hold no `ModelContext`; intent methods return `Void`
and never throw; gates read authoritative state; use cases only for multi-service flows; nothing heavy at startup.

## App + extensions + core package (example: a Screen Time app)

```
<App>/            App  AppCoordinator (publishes an immutable snapshot)  Presentation/ (per-screen
                  @Observable @MainActor VMs)  Screens  Services  Paywall (StoreKit 2)  Intents
<App>Extensions/  shield config / action / monitor / widgets (app-extension targets, App Group)
Packages/<App>Core/  engine  SharedStore  file-lock counters  DarwinNotifications  WidgetSnapshot
```
Cross-process state = App Group files + Darwin notifications; the widget reads a snapshot.

## App shell over local packages (example: a drawing / pattern app)

```
<App>App/   App  RootTabView  feature folders  Config.swift
Packages/   Engine (zero deps)  Canvas (SwiftData progress, Canvas immediate-mode — NOT view-per-cell)
            Rendering  Export (PDF)  Library (bundled JSON)  UI (tokens)  Monetization (RevenueCat)
```
Per-cell work in `Canvas` is snapshotted once per `body` — a per-cell String allocation is 10k
allocations per frame on a 100×100 grid.
