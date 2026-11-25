---
name: android-kmp-engineering
description: "Use when writing, building, testing or releasing Android or Kotlin Multiplatform code: Gradle, Koin, Room migrations, expect/actual, push wake, Play. Use INSTEAD of generic Kotlin/Room knowledge and the generic swiftdata (and other framework) skills for persistence-migration advice. Triggers: \"build Android\", \"port it to KMP\", \"the push doesn't wake it\", \"add a field in Room\", \"build the AAB\"."
---

# Android / KMP engineering — how we write it

Your own cases for this skill live in `local/skills/android-kmp-engineering/` (git-ignored, see
`local.example/README.md`). Read them first if they exist; append the outcome of each round/incident there.
App ids, packages and repo paths: the app's block in `local/apps.yaml`.

This skill is the house style + trap library for Android and KMP code. It does not repeat the delivery
process: frame the change with the risk table, review and "Done means" from
`skills/mobile-feature-delivery/SKILL.md` (its §2 persistence rule and §8 update-gate release recital
apply here unchanged). Universal rules from `~/.claude/skills/ios-app-bootstrap/templates/CLAUDE.md`
that hold on Android too: money as `Int` minor units, wire formats never localize, nothing heavy at
startup, gates read authoritative state.

**Read first, every time:** the repo's own `CLAUDE.md` (and module-level ones where they exist — the closest
wins), then the project memory index in `~/.claude/projects/<project-slug>/memory/MEMORY.md`. Shapes and
module trees: `references/architecture.md`.

## 0. Machine and owner rules (learned, not optional)

- **Heat budget:** parallel agents + Gradle + emulators can overheat a laptop. One implementation agent at
  a time, every Gradle call with `--max-workers=2`, emulator/simulator up only for the check and shut down
  after (`adb emu kill`), `./gradlew --stop` when done. Never touch the owner's own booted sims. Pass
  `--max-workers=2` even where `gradle.properties` sets a higher `org.gradle.workers.max`.
- **Some repos forbid launching the emulator/simulator** and long foreground Gradle runs (the owner does
  device QA himself). Ask before booting anything in any repo.
- **Never `clean build`** (far too slow on a KMP module). Check the repo's CLAUDE.md before running detekt
  — it may be known-broken.
- **Do not commit.** `git add` is fine where the repo allows it, `git add -u` not `-A` (large untracked
  release APKs sit in `composeApp/release/`). Commit only on an explicit per-request go; where a clone
  appends a `Co-authored-by` trailer itself via a local `.git/hooks/prepare-commit-msg`, never hand-write
  it and never move the hook into the repo. Where release tags go through a repo skill, raw `git tag` is
  blocked — use the skill.
- **Never modify** `local.properties`, `google-services.json`, `*.keystore`, `*.jks`, signing config,
  QA-owned context files. Never paste keys into chat or files; auto-mode blocks committing
  files with API keys — hand those commits to the owner.
- **Plan first** when a list arrives with "think it over" / "make a plan".
- **Implementer subagents loop on explore-heavy tasks** (endless Read loops): implement directly, delegate
  only read-only review or fully specified mechanical work.
- **Fewer reviews:** one review per milestone; a separate reviewer only for native memory, threading,
  push/wake, persistence.

## 1. Pick the shape before writing code

| Situation | Our answer | Why |
|---|---|---|
| New Android app with an existing Swift iOS app | **Native Kotlin + Compose, no KMP** | iOS is already in Swift; a shared layer won't pay off |
| One team, both platforms, logic-heavy (SIP/WebRTC, sync engines) | **KMP, one `:composeApp` module, Compose UI on both**, platform code only at `expect/actual` | most code lands in `commonMain` |
| iOS-only system UI (CallKit, PushKit, AVAudioSession handoff) | **Swift side owns it**, Kotlin gets a thin bridge object | a `CallKitManager.swift` owns `CXProvider` |
| Port of a shipped Android app to KMP | **Faithful port**, diff 1:1 against the shipped tag | `references/kmp-port.md` |
| A CMP app the owner wants to feel native on iOS | **Rewrite in SwiftUI**, keep the data files | Room DB = plain SQLite (readable via GRDB); multiplatform-settings = NSUserDefaults |
| New feature in an app that has both native repos and an experimental KMP port | **Native repos**, not the port | a port is not automatically where new work lands |

DI: **Koin** or a **hand-written `AppGraph`** (no Hilt; Dagger 2 only in legacy multi-module Android).
Navigation: Voyager, CMP `navigation-compose`, or plain state in an `AppNavigator`. Network: Ktor
(okhttp/darwin). Persistence: **Room KMP + `BundledSQLiteDriver`** + `multiplatform-settings`. Logging:
Kermit in KMP, Timber in plain Android. Serialization: kotlinx only — never Gson/Moshi. Details:
`references/conventions.md`.

## 2. Where code goes (KMP)

1. Default to `commonMain`. A platform source set only for audio routing, push, background survival,
   system call UI, WebView, secure storage, file paths.
2. Crossing = `expect` next to its callers + **both** actuals in the same change. A missing actual
   fails only that platform's compile — run both platform compiles (§4).
3. iOS globals set from Swift before DI (bridges for remote config, push tokens) must be set before
   anything resolves them — wrap them in one Swift-callable `object` (`IosBootstrap.start(bridge)`)
   called from both `MainViewController()` and `didFinishLaunchingWithOptions` (otherwise a device crash).
4. Tests in `commonTest`; `androidUnitTest` only for JVM-only APIs. Never declare an `actual` inside
   `commonTest` (it breaks the whole test compile).
5. New feature folder: `features/<name>/{data,domain,presentation}`; versions only in
   `gradle/libs.versions.toml`.
6. In commonMain use `KoinPlatformTools.defaultContext()`, not `GlobalContext` (not resolvable for iOS in
   koin 3.5).

## 3. Rules that bite only at runtime (compile-green ≠ working)

Run this list against every diff; each item has bitten. Full entries with fixes: `references/traps.md`.

- **DI graph:** neither Koin nor `AppGraph` has a graph test by default. A constructor param typed as an
  interface with only the impl bound → `InstanceCreationException` on first screen resolve. Bind
  `single<Iface> { Impl(...) }` or `get<Impl>()`, then open the screen. Module check:
  `templates/KoinGraphCheckTest.kt`.
- **SavedStateHandle:** never put a kotlinx-`@Serializable` object in it — Android `bundleOf` throws at
  `NavController.saveState()`. Encode through `androidx.savedstate.serialization` (`encodeToSavedState`)
  or a JSON string; pin with a round-trip test (`templates/NavResultTransport.kt`).
- **Screen state that must survive rotation/theme/locale/font change** → androidx `ViewModel` +
  `SavedStateHandle`, not `remember` (a `remember`-held game run resets on theme change).
- **Coroutines:** app scopes get `SupervisorJob()` + handler; rethrow `CancellationException` in every
  `runCatching`-style helper (a cancelled token refresh must not log out); iOS `Dispatchers.IO` needs
  `import kotlinx.coroutines.IO` or the code silently runs on Default.
- **Endless tickers in tests:** `runTest(UnconfinedTestDispatcher()) { Class(..., backgroundScope) }`,
  never `advanceUntilIdle()` (hangs forever). `templates/TickerTestPattern.kt`.
- **Resources:** a stringly-typed drawable lookup that misses renders nothing at **zero size** — blank and
  untappable. `@color/` inside vector XML crashes the CMP parser. Build `FontFamily` once at the root
  (`CompositionLocal`), never per `Text` — compose-resources `Font()` is synchronous via `runBlocking`.
- **Wire shapes lie:** decode tolerant (`ignoreUnknownKeys`, `@JsonNames` for snake/camel twins, branch on
  `JsonArray` vs `JsonObject`); dump the raw JSON before blaming permissions. Timestamps: check seconds vs
  millis against the server code.
- **Remote Config JSON:** decode feature blocks as raw `JsonElement`; a typed field that throws drops the
  whole param to its fallback (an empty allow-list = feature off for everyone).
- **Process model:** anything a push must reach (DI graph, call runtime) is started from `Application` /
  `didFinishLaunching`, not from a composable (otherwise a cold wake is a no-op). Android 12+ refuses an
  FGS start from the background — start it at answer time or from a notification action.

## 4. Build, test, verify — the gates

Exact command lists (and what each does not catch): `references/commands.md`. Always add `--max-workers=2`.

```bash
# KMP single-module app — commonMain change: metadata compile (<1 s warm), then BOTH platform compiles, then tests
./gradlew --max-workers=2 :composeApp:compileCommonMainKotlinMetadata --console=plain
./gradlew --max-workers=2 :composeApp:compileDebugKotlinAndroid :composeApp:compileKotlinIosSimulatorArm64 --console=plain
./gradlew --max-workers=2 :composeApp:testDebugUnitTest --console=plain        # does NOT catch Koin bindings
# KMP :shared + :composeApp app — the four gates (all commonTest, hand fakes, no mockk)
./gradlew --max-workers=2 :shared:compileKotlinIosSimulatorArm64 :shared:compileAndroidMain :composeApp:assembleDebug
./gradlew --max-workers=2 :shared:iosSimulatorArm64Test
# multi-module Android — touched modules, then lint (CI runs the second line)
./gradlew --max-workers=2 :feature:auth:testDebugUnitTest && ./gradlew --max-workers=2 lint
./gradlew --max-workers=2 testDebugAll -PskipRobolectricTests=true
```

Test stack: `kotlin.test` + `assertk` + `turbine` + `kotlinx-coroutines-test` (KMP); plain Android adds
`mockk`, Robolectric only when the framework is truly needed. Report counts plainly: "389 green,
Android + iOS compile, merged manifest OK".

**Device/emulator proof is the only proof** for DI, push wake, audio, background, R8 and resources.
Keep your device list (models, API levels, AVD names) in your local notes. Behind a host VPN start the
emulator with `-dns-server 8.8.8.8,1.1.1.1`. Drive with mobile-mcp `list_elements_on_screen` (raw
coordinates mis-scale). Killed-app push test = launch → HOME → `adb shell am kill <pkg>` (**not**
`force-stop`: stopped state blocks FCM) → screen off → send. Firebase Remote Config never loads on the
iOS simulator (Installations keychain -34018) → device only.

## 5. Persistence and migrations

- Room KMP: `exportSchema = true`, `room { schemaDirectory("$projectDir/schemas") }`, KSP per target
  (`kspCommonMainMetadata`, `kspAndroid`, `kspIosArm64`, `kspIosSimulatorArm64`), builder expect/actual
  (Android `getDatabasePath`, iOS `NSDocumentDirectory`), `.setDriver(BundledSQLiteDriver())`,
  `.setQueryCoroutineContext(Dispatchers.IO)`. Real code: `templates/room-kmp/`.
- **Every version bump = an explicit `Migration(n, n+1)` + schema JSON committed + a test that opens the
  previous version's file** (`templates/room-kmp/RoomMigrationTest.kt`). `ALTER TABLE … ADD COLUMN …
  NOT NULL DEFAULT …` is safe in SQLite; never `fallbackToDestructiveMigration` on shipped data.
- multiplatform-settings / Keychain: never change the query attributes of existing items
  (`kSecAttrAccessible` → -25300 on old items). Moving a stored value to a new key = seed-from-legacy once.
- Session data a cold process needs (cookies, session key) must be persisted; Ktor `AcceptAllCookiesStorage`
  is in-memory (a killed-app wake 401s).
- Then the upgrade-install check from mobile-feature-delivery §5.7.

## 6. Monetisation and analytics wiring

- RevenueCat **purchases-kmp** in KMP, the native SDK in plain Android. Prefetch offerings once in the
  purchase manager's `init` with an in-flight `Deferred` and a 5-min stale-while-revalidate TTL; never
  fetch inside the paywall's first animation frame. iOS: call
  `enableAdServicesAttributionTokenCollection()` (otherwise Search Ads attribution is blind).
  Show an honest "plans unavailable" state when offerings fail.
- Ads: `MobileAds.start` deferred to the first preload after onboarding, never before frame one.
- Analytics: one `AnalyticsClient` fanning out to providers, each call in `runCatching`; typed sealed
  events where the type picks the backend (GA4 `TelemetryEvent` vs PostHog `ProductEvent`). GA4 text
  dimensions only fill from **String** params (a Long shows "(not set)"), and custom dimensions are not
  retroactive. PostHog token: env var → `local.properties` → `BuildConfig`; nothing defaulted (missing key
  = PostHog uninitialised, loud). Tag persons with `environment` (production | stage | debug) when there is
  no stage project. Native iOS + Android apps can share one event vocabulary from a KMP library
  (prebuilt `.aar` / `.xcframework`).

## 7. Firebase, push, WebView

Two Firebase projects per app where iOS and Android differ (one Android, one iOS; iOS Stage + Prod may
share one): every Remote Config edit happens **twice**. The `appUpdate` update-gate procedure, the feature
allow-list, and the release-time checks: `references/release.md` §2. Push contract and the wake chain
(FCM data-only + `priority: high`; APNs topic `<bundle>.voip`, sandbox vs production):
`references/traps.md` (push section). WebView force-dark `ClassCastException` on some OEM Android 11
builds has **no** dependency-bump fix — see traps.

## 8. Release (Android side)

Version source per repo shape, Play steps, targetSdk deadline, 16 KB alignment gate, signing (env names
only), what to ask rather than assert (closed-testing tester rules, staged-rollout percentages):
`references/release.md`. Never upload, publish Remote Config or roll out yourself.

## 9. Porting Android → KMP

Method, wave order, the `status/` backlog protocol, the snapshot diff ref and the landmines:
`references/kmp-port.md`. One-line version: bulk-copy → de-Android by the sanctioned table →
four compile gates → device proof after every batch; diff allow-lists, resolver maps and nav collectors
1:1 against the shipped tag, and keep the reported client versionCode equal to the shipped release.

## Traps / Lessons (top 12; all entries in `references/traps.md`)

- Koin `get()` for an unbound interface → `InstanceCreationException` on first screen; build + tests green.
  Bind the interface; open the screen after DI edits.
- A ticker test hung forever (foreign scheduler + `advanceUntilIdle`). Fix:
  `runTest(UnconfinedTestDispatcher())` + `backgroundScope`.
- `@Serializable` result in `SavedStateHandle` crashed on navigation. Fix: SavedState codec + round-trip test.
- A placeholder client versionCode made prod serve server-driven tabs the shipped app does not have. Fix:
  pin to the shipped release.
- Mic FGS started at inbound RINGING from a push-woken process → `ForegroundServiceStartNotAllowedException`.
  Fix: start at answer only.
- "iOS killed app never wakes" was the backend: no `.voip` topic, production APNs for a dev build
  (`400 BadDeviceToken`). Prove the client with one manual APNs push first.
- Backend sent a notification-block FCM; `onMessageReceived` never ran (`Missing Default Notification
  Channel metadata`). Contract: data-only, high priority.
- Logout did nothing in a port: a root VM collector was never ported. Port collectors, not just state.
- CMP upgrades can need a newer Kotlin than the docs say and drop targets (`iosX64`); read the line above
  "KLIB resolver: Could not find".
- WebView force-dark CCE on some OEM Android 11 devices: no upgrade fixes it, vendoring fails on
  `internal set`; only an upstream `runCatching`.
- A typed Remote Config field fed an unquoted number empties the allow-list. Fix: raw `JsonElement`,
  `fetchedThisProcess`, shape guard.
- Parallel agents + emulators overheat the machine. Rule in §0.
