# Trap library (what broke → fix)

Format: **trap.** What broke. → Fix / rule. Your dated, per-repo entries live in
`local/skills/android-kmp-engineering/` (append new incidents there; promote the generic lesson here).

## DI, process model, startup

- **Koin interface binding.** `RepositoryImpl(api: Fetcher)` with only `single { ApiImpl(get()) }` →
  `InstanceCreationException` on the first screen that resolves it; build + unit tests green. →
  `get<ApiImpl>()` or `single<Fetcher>`; open the screen after every DI edit.
- **Composition-scoped DI.** Koin + a call subsystem living inside `App()`: a push to a cold process has no
  graph, wake is a no-op. → `startKoin` + `Runtime.start()` in an `AppInitializer`; UI uses `KoinContext {}`.
- **Late-init globals.** iOS runtime start in `didFinishLaunching` ran before a Swift bridge was set →
  device crash; Android needs the app context first. → one `IosBootstrap.start(bridge)` from both
  `MainViewController()` and `didFinishLaunchingWithOptions` (after `FirebaseApp.configure()`, before
  PushKit); Android from `Application.onCreate` after the context is set.
- **No SupervisorJob** on the global scope — one failure cancels the app scope. → `SupervisorJob` + handler.
- **Startup work before frame one.** Ads SDK started in app init; offerings fetched in the paywall's frame 0.
  → defer ads to the first preload after onboarding; prefetch offerings in the purchase manager's `init`
  with an in-flight `Deferred` + 5-min TTL.

## Navigation, state, resources

- **`@Serializable` in SavedStateHandle.** A result type (was `@Parcelize`) seeded by `getStateFlow` →
  `IllegalArgumentException: Illegal value type` at `bundleOf` ← `NavBackStackEntry.saveState`. →
  SavedState codec (`encodeToSavedState`), a round-trip transport test.
- **Mistyped drawable map** (`drawable_onboarding_*` vs real `drawable_onb_*`, assets not copied) → blank
  onboarding and untappable banners (null painter → zero-size box). → diff the resolver 1:1, copy
  base-density webps into `composeResources/drawable`.
- **`@color/` in vector XML** crashes the CMP vector parser. → inline colours.
- **FontFamily per composition.** Wrong typeface metrics; many fonts loaded per text. → a font-family
  `CompositionLocal` provider at the app root.
- **Collector not ported.** Logout did nothing; the owner's iOS sim QA found it the same day. → port the
  `logOutTrigger → ReplaceAction(/auth)` collector.
- **Dark sheet theming.** The bottom-sheet slot is a sibling of the body, so the dark flag does not reach it.
  → hoist the dark-theme `CompositionLocal` above `ModalBottomSheetLayout`.
- **`remember`-held game state** lost on theme/locale/font change. → androidx `ViewModel` + `SavedStateHandle`.
- **Whole-list recomposition each second.** A grouping function returned a new Map per recomposition under a
  1 s timer. → `remember(state.items) { groupBy }`, one `LazyColumn` item per row keyed by id.

## Coroutines and tests

- **`actual` declared in `commonTest`** → "Actual has no corresponding expected", the whole
  `testDebugUnitTest` stops compiling. → fakes behind interfaces.
- **Endless ticker test hang.** Controller on its own `CoroutineScope(UnconfinedTestDispatcher())` +
  `advanceUntilIdle()`. → `runTest(UnconfinedTestDispatcher())` + `backgroundScope` (`templates/TickerTestPattern.kt`).
- **iOS `Dispatchers.IO`** without `import kotlinx.coroutines.IO` falls back to Default. → explicit import;
  restore `Main.immediate`.
- **Cancelled refresh logged users out.** → the token refresher rethrows `CancellationException`; MockEngine scenarios.
- **Paging race.** A stale load-more appended to a new query. → cancel `loadMoreJob` + generation token.
- **One broken test class blocks every unit test in the module.** → fix or exclude before reading a red run.

## Persistence

- **Room, not SQLDelight**, for a faithful port of an Android Room schema: port the schema/DAO faithfully;
  `BundledSQLiteDriver`, `setQueryCoroutineContext(Dispatchers.IO)`, expect/actual builder.
- **Keychain attribute change.** `kSecAttrAccessible` mixed into `KeychainSettings` queries → `-25300` crash
  on pre-existing items. → revert; an attribute migration is its own task.
- **Two tokens, one key.** A device-token store persisted under the same key another token used → iOS could
  register the wrong token. → a new key, seed from legacy once; guard on the `(sessionKey, token)` pair.
- **In-memory session.** Ktor `AcceptAllCookiesStorage` + an in-memory session store → cold wake refresh 401.
  → persist the session key in Settings + a cookie-less session-key login.
- **Data must survive a platform rewrite.** Room DB = plain SQLite (readable via GRDB on iOS),
  multiplatform-settings = NSUserDefaults. → never rename tables/keys before the rewrite ships.
- **House pattern:** `ALTER TABLE … ADD COLUMN … NOT NULL DEFAULT …` migrations, schemas exported — and a
  migration test that opens the previous version's file (the usual gap).

## Push, wake, calls (KMP calling app)

- **Malformed REGISTER.** SIP URIs used the WSS load-balancer FQDN instead of the SIP proxy, Via said `WS` →
  server-initiated BYE / hangup never routed back. → SIP domain = proxy address, Via `WSS`, plain Contact
  like SIP.js; REGISTER refresh at half the granted expires.
- **Asymmetric hangup.** Inbound gets no BYE and ICE stays Connected. → a hangup MESSAGE ends inbound, BYE
  outbound, ICE `Failed` backstop; `CallEnded` idempotent; re-register after every call.
- **FGS from background.** Mic FGS at inbound RINGING on a push-woken process →
  `ForegroundServiceStartNotAllowedException` ("1st call worked, 2nd didn't"). → start at answer only;
  the notification Answer action starts it (temporary exemption).
- **Silent push-woken calls.** iOS `AVAudioSession.setActive(true)` fails from background; Android
  `AudioManager.mode` never set on the answer path. → `RTCAudioSession.useManualAudio` + `isAudioEnabled`
  toggled in CallKit `didActivate`/`didDeactivate`; `MODE_IN_COMMUNICATION` on answer.
- **iOS killed app never wakes = backend.** A manual APNs push (`apns-push-type: voip`, `apns-topic:
  <bundle id>.voip`, priority 10) woke it; the prod endpoint gave `400 BadDeviceToken` for a dev token,
  sandbox `200`. → the push gateway needs per-iOS `topic <bundle>.voip`, `push_type voip`, sandbox for dev /
  production for TestFlight. Prove the client with one manual push first.
- **iOS release logs missing.** Kermit `platformLogWriter()` on iOS writes os_log DEBUG/INFO, never persisted
  on device. → a temporary NSLog writer for triage, reverted before store.
- **Notification-block FCM.** `onMessageReceived` never fires in background/killed; logcat
  `W/FirebaseMessaging: Missing Default Notification Channel metadata`. → backend sends DATA-ONLY
  (`data.type=incoming_call`, `data.caller`), high priority; hybrid messages are broken too.
- **Stale registrar binding.** A random per-process contact left the dead process bound; the client parsed
  the first (foreign) contact's expires → re-REGISTER frenzy. → persisted contact seed; parse our own
  contact from the 200 OK.
- **Click-to-call dial-back** arrives as an incoming-call push → dead full-screen UI. → a guard in the
  wake-push handler; iOS CallKit reports before Kotlin, so it needs a backend fix too.
- **Two Firebase projects.** Allow-list id published in the wrong project → `available=false`.
- **Seconds vs millis.** A credentials validity check read the expiry (Unix seconds) as ms → the cached cold
  wake never ran. → one shared `expiresAtMs()`.
- **Push priority dropped.** An older push gateway copied `priority` only when the request had a sound; the
  data-only call push arrived NORMAL (`priority=2/orig=2`) → Doze deferral. → `android: {priority: high}`
  in the gateway request; check the gateway version.
- **Backend "is registered" gate blind.** Any unexpired registrar row counts while the location DB lags
  seconds → INVITE into a dead socket. → the app verifies REGISTER (≤ 2 s ack) before trusting a wake;
  backend: live lookup + registration time ≥ push time.
- **Newer Android kills sockets** ~20–40 s after leaving foreground while the binding outlives them. → unREGISTER
  on background or a backend freshness gate.

## Firebase, WebView, analytics

- **GA4 string-only dimensions.** A status code sent as Long → "(not set)"; dimensions not retroactive. → send
  strings; register dimensions before reading data.
- **PostHog silently off.** The logger no-ops when the CI secret for the key is empty. → the build warns;
  check before reading dashboards.
- **WebView force-dark CCE.** `WebSettingsWrapper cannot be cast to ContentSettingsAdapter` on some OEM
  Android 11 builds. `compose-webview-multiplatform` calls `setForceDarkStrategy` unconditionally; lib and
  androidx.webkit bumps don't help; vendoring fails on `internal set`. → upstream `runCatching` + bump; fork
  via `includeBuild` only if it recurs.
- **RC decode fallback.** Typed field + unquoted number → empty allow-list for everyone. → raw `JsonElement`,
  `fetchedThisProcess`, shape guard (`release.md` §2).
- **Real-time RC through a phone VPN** may never arrive, with no error. → VPN off.
- **Analytics provider failure** crashes or blocks others. → the fan-out wraps each provider in `runCatching`;
  typed events pick GA4 vs PostHog.

## Toolchain and Gradle

- **Old code on a new toolchain.** Months-old code on today's Kotlin/CMP → inset and dead-tab CMP bugs;
  builds cut from an uncommitted tree; a stale fork with the same bundle id. → release only from the tree
  that matches the shipped build; DerivedData can hold tens of GB when the disk fills.
- **CMP upgrade.** New CMP klibs need a newer Kotlin than the docs say ("KLIB resolver: Could not find"; the
  real cause, incompatible ABI, is one line above); `iosX64` dropped (remove target + `kspIosX64`);
  `kotlinx.datetime.Clock` → `kotlin.time.Clock`. `KOTLIN_FRAMEWORK_BUILD_TYPE` is a no-op for
  Debug/Release. `~/.konan` grows by a toolchain per Kotlin version.
- **An SDK forces Kotlin.** posthog-kmp needs a recent Kotlin → a big jump in Kotlin/CMP/AGP/JVM; a Ktor minor
  can pull an OkHttp that needs a newer compileSdk → stay on the previous Ktor. Pin libs you reflect into and
  guard them with a reflection test. `embedAndSignAppleFrameworkForXcode` refuses to link until
  `integrateLinkagePackage` is re-run.
- **Native-lib classifier.** A release AAR with no classes → use the debug classifier for debug, release AAR +
  the plain host jar for release; `pickFirsts` for duplicate native resources. Old API levels fail `dlopen`
  on unwinder symbols → raise minSdk. A 3D engine can force compileSdk up.
- **Heat.** Parallel subagents + emulators overheat the machine; everything pauses. → one agent,
  `--max-workers=2`, emulators only for the check, `./gradlew --stop`.
- **R8 never run.** → `assembleRelease` once (expect a large APK shrink and keeps for runtime-resolved serializers).
- **Rebase hygiene.** `git add -A` would stage a large `composeApp/release/` APK; a removed plain
  `GoogleService-Info.plist` ref (Prod/Stage variants now) — don't re-add.
