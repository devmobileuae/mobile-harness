# Conventions — house rules

Your per-repo conventions and their history: `local/skills/android-kmp-engineering/`.

## Code style (multi-module Android house style; a KMP port copies it)

- Comments and KDoc **off by default**. A short comment only for a non-obvious constraint, ordering
  requirement or workaround, and as a rule only when the reviewer asks. KMP port adds: never write
  porting-history comments ("Wave-N…", "Android original did X…") — comments state live constraints only.
- No `!!` — use `?`, `let`/`run`/`apply`/`also`/`with`, sensible defaults.
- kotlinx.serialization only (never Gson/Moshi). Timber only in plain Android (never `android.util.Log`);
  Kermit in KMP, gated silent in release (`AppLogging.configure(isDebug)` — also a chance to remove
  PII logs such as hardware ids).
- Sealed classes/interfaces for restricted hierarchies; exhaustive `when`. Expected failures return
  `Result`/project result type, not exceptions.
- No wildcard imports, 4 spaces, trailing commas in multi-line declarations and calls, no two blank lines,
  brace on the declaration line. Import order: Kotlin stdlib, Android, AndroidX, third-party, project, static.
- Compose: `Modifier` is the first optional parameter defaulting to `Modifier`; conditional modifiers via
  `Modifier.conditional`. A file holding a composable is named after its primary composable
  (`LoginScreen.kt`); tests are `ClassNameTest`.
- Check whether `docs/` is gitignored-but-tracked (then new docs need `git add -f`) or gitignored and local
  only (then do not `add -f`).
- Report an unrelated problem; do not fix it in the same diff. No new modules or dependency bumps unless
  the task needs them.
- Commit format comes from the repo (a `commit` skill or CLAUDE.md): some want `<TICKET>:` then
  `- imperative, lower-case;` lines with the ticket taken from the branch name; others plain imperative
  sentences ("Bump version to 19 (2026.11.1)").

## KMP-specific shape (the port's `docs/LANDMINES.md` "sanctioned de-Android transforms")

| Android idiom | KMP replacement |
|---|---|
| Timber | Kermit `co.touchlab.kermit.Logger` |
| Dagger / `*Module.kt` | delete; manual wiring in `AppGraph` (or Koin in other repos) |
| `R.color.X` / `colorResource` | `ComponentColorReference.X.toColor()` |
| `R.drawable.X` / `painterResource` | `Res.allDrawableResources["X"]` / `dsDrawablePainter(name)` |
| `R.string` / `R.font` | Compose Resources (`composeResources/values/`, `Res.font.*`) |
| `java.util.Date`/`Locale`/`SimpleDateFormat`, `android.icu` | kotlinx-datetime + platform seam (device-local TZ — UTC is a bug) |
| `@Parcelize` | `@Serializable` — never stored raw in `SavedStateHandle` |
| Retrofit / OkHttp | Ktor (okhttp / darwin engines) |
| Room (Android) | Room KMP + bundled SQLite driver |
| DataStore | multiplatform-settings (SharedPreferences / Keychain) |
| AndroidX navigation-compose | CMP navigation-compose |
| `LocalConfiguration.screenWidthDp` | `BoxWithConstraints { maxWidth }` |
| any platform touch | `expect`/`actual` seam |

`kotlinx.datetime.Clock` → `kotlin.time.Clock` after Kotlin 2.4 / datetime 0.7.

## DI

- **Koin:** one graph file (`di/Dependencies.kt`). Interface
  params need `single<Iface> { Impl(...) }` or `get<Impl>()`. Per-screen objects (a recording controller,
  audio player) are `factory`; repositories/fetchers `single`; platform things needing `Context` go in the
  platform module. A Koin `factory` VM resolved with `koinInject` inside `AnimatedVisibility` re-creates the
  VM (and its network call) on every open — paywall jank.
- **AppGraph:** constructor-built singletons + `createXxxViewModel(...)`; nothing heavy at construction.
  An eager, untested graph is a known risk — a framework migration is a backlog item, not something to
  start unasked.
- Composition-scoped Koin (`KoinApplication {}` inside `App()`) is invisible to a push-started process —
  use `startKoin` in an `AppInitializer` + `KoinContext {}` in UI.

## Concurrency

- App-wide scope: `CoroutineScope(SupervisorJob() + Dispatchers.Default + handler)` — without
  `SupervisorJob` one failure cancels the app scope.
- Never swallow `CancellationException` in `runCatching`-style helpers; rethrow it (a cancelled refresh
  ≠ logout). Same rule in `Resultat` helpers.
- iOS: `import kotlinx.coroutines.IO` explicitly before `Dispatchers.IO`; restore `Dispatchers.Main.immediate`
  where the original used it.
- Audio/IO never on `Main.immediate` (an iOS audio player that plays on main, creates
  `AVAudioPlayer` in the tap frame and polls `while isPlaying delay(100)` janks). Create players on `Default`,
  configure the session once off-main (`Ambient` + `MixWithOthers`), wait `delay(duration)`.
- Paging/load-more: cancel the previous job and tag results with a generation token (otherwise a stale
  append races into a new query).
- `stateIn(WhileSubscribed(5_000))` re-emits a stale `Failure` on resubscribe; throttle reloads (Android
  uses `throttleFirst(1000ms)`) — matters when counting error events.
- Shared mutable state behind a `Mutex`; a coordinator mutex must not wrap a retry loop (keep a
  5 × 2 s wake-login retry outside it).
- Platform action flows that a cold start may emit before the collector exists: `MutableSharedFlow(replay = 1,
  onBufferOverflow = DROP_OLDEST)` or an explicit latch with TTL (e.g. 20 s).

## Compose performance (CMP on iOS)

- Read animated values in lambdas (`Modifier.offset { }`, `graphicsLayer { }`, `drawBehind { }`), never in
  composition — otherwise animated elements recompose every frame.
- Infinite transitions only when needed (create a blink only when `shouldBlink`).
- Scroll positions in plain VM vars, not in `UiState` (otherwise the whole screen recomposes per pixel).
- `remember` derived collections (`remember(state.items) { groupBy }` — otherwise a list recomposes each
  second under a 1 s timer).
- Pagers: `beyondViewportPageCount = 1` only shifts the cold composition into the animation; precompose
  pages in stages one frame after entry.
- Modals: a precomposed slide-up / scale-fade overlay in the design system — compose
  one frame before the slide, warm-draw one frame at alpha 0.01, `keepContentComposed` between opens,
  prewarm 800 ms (modal) / 1400 ms (full-screen) after start. Fire screen analytics from `onShown()`, not VM
  `init`, or prewarm logs a false `Screen("paywall")`.
- Honest iOS perf numbers need a Release Kotlin framework: Edit Scheme → Run → Build Configuration =
  Release. `KOTLIN_FRAMEWORK_BUILD_TYPE` is a no-op for configurations named Debug/Release (KGP 2.2.0
  decompiled); it only works for custom names like Staging.

## Network

- Ktor everywhere in KMP; set explicit timeouts (e.g. 15 s; with none, OkHttp ~10 s / NSURLSession
  60 s defaults can eat a 10 s push-wake window).
- Bearer refresh: one `TokenRefresher` + `BearerTokenSource`, empty refresh token ⇒ wipe + logout (Android
  parity), cancellation rethrown; covered by 8 MockEngine scenarios.
- Cookie jars are in-memory (`AcceptAllCookiesStorage`) — persist what a cold process needs.
- Mobile backends detect "mobile" by User-Agent regex: native Ktor requests send a mobile UA or
  `X-Client-Platform: mobile`. UA shape changes (digits in versionName or OS
  version) can remap a device on the backend — check before changing `versionName` format.
- Server-driven content gated by client version (an `X-User-Agent: <App>:ANDROID:<versionCode>` header):
  replay the endpoint with the device token (`adb run-as <pkg> cat shared_prefs/*.xml`) and vary the header.
- Prod cautions when a debug build talks to the production API: page GETs are safe; OTP sends real SMS —
  iterate by relaunch; deleteAccount, ShareFeedback, payments are real writes.

## Monetisation

- RevenueCat: entitlement `premium`, offering `default` with `$rc_annual` / `$rc_monthly` (or weekly /
  monthly / annual). Play: one subscription with base plans (`<app>_plus`: `yearly` with a 1-week
  free-trial offer, `monthly`). Prices read from the offering, never hardcoded. Purchases tested with Play License testing accounts.
- Freemium gate: `configuration.isPaid(kind) && !isPremium` — gates read the entitlement stream,
  not a cached display flag.
- Payments drop-in SDKs (Adyen): any SDK bump needs a real payment / 3DS2 run before release.

## Analytics

- `core/analytics/`: `AnalyticsClient` → `AnalyticsClientDefault.fanOut` (each provider call in
  `runCatching`) → providers: Firebase (Android), Swift bridge (iOS), common `PostHogAnalyticsProvider`.
  Sealed `AnalyticsEvent` = `TelemetryEvent` (GA4) | `ProductEvent` (PostHog). Identity through
  `setUserId`/`reset`. PostHog names snake_case. Setup failures caught — analytics can never crash the app.
  Tests pass `FakeAnalyticsClient` (no no-op client anymore).
- Telemetry holes worth checking before trusting a funnel: a state property hardcoded as a stub; a
  "registered" event that reports success before the server confirmed; steps deduped once per process
  instead of once per push.
- Native iOS + Android pair sharing a KMP analytics lib (event names / params / screens / user-property keys),
  shipped prebuilt (`.aar` + `.xcframework`): new event names go into the library; string literals only
  where it has none.
- Android port of an iOS app: same PostHog project as iOS, names from the iOS repo's analytics doc,
  `platform: android`, the same privacy rules and opt-out switch.
- Firebase Analytics only: no connector can read it — use RevenueCat customers for per-user first/last seen.

## Testing tiers (as actually practised)

| Tier | Where | Tools | Catches |
|---|---|---|---|
| pure logic | `commonTest` / `:core:model` JVM | kotlin.test, assertk, turbine, coroutines-test, hand fakes (KMP port), mockk (plain Android) | reducers, mappers, rules — "matches iOS on the same fixtures" for ports |
| contract | `commonTest` | MockEngine (Ktor), registry contract tests, `NavigationResultTransportTest`, `KmpNotifierReflectionGuardTest` | API semantics, landmine classes, library internals we reflect into |
| graph smoke | `commonTest` | AppGraph smoke test (port); Koin `verify()` proposed | wiring |
| migration | android/JVM test | Room `MigrationTestHelper`, template in `templates/room-kmp/` | upgrade installs |
| screenshot | Android | Roborazzi vs iOS references | parity |
| UI flow | device/emulator | Maestro (separate UI-test repo), Kaspresso deps (androidTest dirs ~empty) | flows |
| device | your phones (incl. a foldable) | logcat tags, `[CALL_DIAG]`, mobile-mcp | DI, push, audio, FGS, R8 |

The multi-module Android CI runs unit tests without Robolectric (`-PskipRobolectricTests=true` excludes the classes
found by `RobolectricTestClasses`). One permanently broken test class blocks every unit test in a module —
fix or exclude it before trusting a red run.
