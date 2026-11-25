# Architecture — shapes, stacks, module trees

Versions drift; the repo's `gradle/libs.versions.toml` wins. Your repo map (paths, packages, status,
pinned versions) lives in `local/skills/android-kmp-engineering/`.

## Repo map — keep one per machine (in your local notes)

| Repo (local path) | What | Shape | Status |
|---|---|---|---|
| `~/code/<app>` | one line | KMP single module / KMP `:shared` + `:composeApp` / multi-module Android / native Android | live / in progress / experimental |

Note stale copies of a repo with the **same bundle id** — never release from them.

## KMP single module, Compose on both (example: a calling app)

Kotlin 2.4.x, CMP 1.10.x, Koin, Voyager, Ktor (check whether a Ktor minor pulls an OkHttp that needs a newer
compileSdk), `compose-webview-multiplatform`, `webrtc-kmp`, Kermit, multiplatform-settings, Firebase
(analytics, config, crashlytics, messaging), PostHog KMP, a notifier lib (pin it if you reflect into its
internals). Raise `org.gradle.jvmargs` (e.g. `-Xmx6g`) if the K/N release link runs out of heap.

```
composeApp/src/
  commonMain/  core/{analytics,data,domain,featuretoggle,log,network,ui}
               di/Dependencies.kt            # the entire Koin graph, one file
               features/home/                # WebView host, push bridge, auth-cookie bridge
               features/calls/
                 data/{dto,sip}              # signaling client, SIP builders, history API
                 domain/{model,state}        # CallManager (serial hub), SipReducer (pure), SipEffectExecutor
                 presentation/{activecall,incomingcall,outgoingcall,dialer,calls,...}
  androidMain/ actuals + FCM service, mic foreground service, shortService wake FGS
  iosMain/     call bootstrap, system-call-UI bridge, audio route actual
  commonTest/  most tests;  androidUnitTest/ only JVM-only APIs
iosApp/        Xcode + CocoaPods, Configuration/Config.xcconfig, a few Swift files
               (App: FirebaseApp.configure → call bootstrap → PKPushRegistry; CallKitManager owns CXProvider)
```

State ownership: `CallManager` is the single source of truth (serial event hub). `SipReducer` is pure:
`(SipSnapshot, SipEvent) -> (SipSnapshot, List<SipSideEffect>)`; `SipEffectExecutor` runs effects and
dispatches completions back. Screen models observe, never own call state. `SipEvent.CallEnded` is
idempotent (no-op when `activeCall == null`) because BYE, a hangup MESSAGE and ICE `Failed` can all end
the same call. The call runtime (commonMain) starts from `Application.onCreate` after the app context is
set on Android, and from a Swift-called bootstrap on iOS.

KMP boundary decisions: everything SIP/WebRTC/state in common; Android-only = FGS, full-screen intent
notification, `AudioManager.mode`, FCM service; iOS-only = CallKit, PushKit, `RTCAudioSession` manual audio,
all in Swift with thin Kotlin bridges.

## Multi-module Android (backend-driven UI)

`app → feature/* → domain/* and core/*` (no domain→feature, core→feature, feature→feature). `build-logic/`
convention plugins: build version from git tag (tag → versionCode), release signing, Android library/Compose,
lint, native-lib 16 KB alignment check (`:app:verifyNativeLibAlignment`). Backend-driven UI: a base VM without
page load, a legacy BDUI VM and a standard one with network monitoring + error handling; every BDUI VM takes a
KV bridge between backend JSON and Kotlin; widgets render through `ComponentXxxResolver`s in `:core:uikit`.
Module-level `CLAUDE.md` files (+ `AGENTS.md` symlink) — the closest one wins.

## KMP `:shared` + thin `:composeApp` (example: a port of the app above)

Kotlin 2.3.x, CMP 1.9.x, navigation-compose (JetBrains), Ktor, Room KMP + sqlite-bundled, Kermit,
multiplatform-settings, okio; no DI framework.

```
:shared        commonMain = the whole app (features, navigation, di/AppGraph.kt, BDUI engine, KV store)
               androidMain / iosMain: actuals (WebView, dates, network monitor, secure storage, image, push,
                                       SSL pinning)
               commonTest only (no JVM leg); composeResources/{drawable,font,values,files/mocks/*.json}
:composeApp    thin Android host (single Activity + Application, manifest, FileProvider)
iosApp/        SwiftUI WindowGroup wrapping MainViewController
build-logic/   kmp-library, kmp-compose, android-library/compose/lint, build-version, release-signing
status/        one file per backlog item;  judge/ review reports;  docs/LANDMINES.md
```

`AppGraph` = constructor-built singletons + `createXxxViewModel(...)` per route; route composables do
`viewModel { graph.createXxxViewModel(...) }`. Backend actions go through one app-scoped action processor onto
one navigation delegate. Navigation is URL-based.

## KMP single module with Room + ads (example: a language-learning app)

Kotlin 2.4.x, CMP 1.11.x, KSP, AGP 8.x, Koin 4.x, Voyager (+ JetBrains navigation-compose), Room +
sqlite-bundled, purchases-kmp, Firebase analytics, Play services ads + UMP, Play Billing, Play review,
media3, buildkonfig for obfuscated keys, an encrypt task for bundled content JSON. Packages by concern
(`database, designSystem, di, features, localization, navigation, services, ui`); DI split
`appModule.kt`, `commonModule.kt`, `databaseModule.kt` (expect `databasePlatformModule`), `PlatformModule.kt`.
Room schemas in `composeApp/schemas/`. iOS target set: iosArm64 + iosSimulatorArm64 (iosX64 dropped with CMP 1.11).

## KMP template app (`:composeApp` `:shared` `:backend`)

Starter templates carry extra targets (desktop, wasmJs) and a server module — leave them unless the task
removes them. Firebase Analytics only means no connector can read events: use RevenueCat customers for
per-user first/last seen.

## Native Android port of an iOS app (example: a 3D puzzle game)

AGP 9 (built-in Kotlin), Compose BOM, JDK 17, compileSdk 37, a minSdk raised by native libs (physics JNI
fails on old APIs), Filament (materials compiled by a `matc` fetched by a script), Coil 3, Room
(`exportSchema = true`, `MigrationTestHelper` from v1), DataStore Preferences, RevenueCat Android, PostHog
(same project as iOS, `platform: android` on every event). No Hilt: one `AppGraph` in `Application`.

```
:app :core:model(pure Kotlin) :core:data :core:ui :core:parity :feature:<x>:logic(pure Kotlin port of iOS rules) :feature:<x>
build-logic/  AndroidConventionPlugin, a materials-compile plugin, IosParityPlugin + report task
```

Rules: features depend on `:core:*`, never on each other; navigation only through `:app`
(`AppNavigator`: tabs + per-tab push stacks + sheets + one cover slot); RevenueCat only in `:billing`,
PostHog only in `:analytics`. Acceptance = iOS screenshot parity (Roborazzi vs `design/reference/ios/`),
JVM tests on fixtures exported from iOS ("divergence from iOS is a bug"). Decisions log: `docs/decisions.md`.
