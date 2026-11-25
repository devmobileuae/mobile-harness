# KMP / Android lessons for delivery

The full method and trap library live in `skills/android-kmp-engineering` (`references/kmp-port.md`,
`references/traps.md`). Your own project lessons: `local/skills/mobile-feature-delivery/` and
`local/skills/android-kmp-engineering/`. This page is the delivery-side digest.

## Porting a shipped Android app → KMP + Compose Multiplatform
The Android original = the shipped release tag; an existing iOS app (if any) is a read-only reference.
Keep a resume file (`migration/full-port-state.md`), a landmines doc (`docs/LANDMINES.md`) and a
backlog folder (`status/`, one file per item with a `## Status` write-back).

**Method that works:** bulk-copy → de-Android → **4 compile gates** → Android device proof.
Gates: `:shared:compileKotlinIosSimulatorArm64`, `:shared:compileAndroidMain`,
`:composeApp:assembleDebug`, `iosSimulatorArm64Test`. Subagents only for code-only screen ports; the
orchestrator verifies gates itself.

**Compile-green ≠ working — proven runtime landmines:**
| Landmine | Symptom | Fix |
|---|---|---|
| kotlinx `@Serializable` in `SavedStateHandle` (was `@Parcelize` on Android) | `IllegalArgumentException: Illegal value type` at `bundleOf` ← `NavBackStackEntry.saveState` | transport as JSON string / SavedState codec, round-trip test |
| a client-version header (`X-User-Agent: <App>:ANDROID:<versionCode>`) gates server-driven UI | a placeholder versionCode shows tabs prod doesn't have | pin to the shipped release (`major*10000+minor*100+patch`); restore anything dropped from the tab allow-list |
| resolver map value `drawable_onboarding_*` vs real `drawable_onb_*`; assets not copied | blank onboarding **and untappable banners** (null painter → zero-size box) | diff the map 1:1 against Android; copy base-density webps into `composeResources/drawable` |
| `@color/` refs inside vector XML | CMP parser crash | inline colours |
| a "fix" for an empty refresh token inverted Android behaviour | session stranded instead of logout | one token refresher + MockEngine scenarios; `CancellationException` rethrown so a cancelled refresh ≠ logout |
| iOS `Dispatchers.IO` without `import kotlinx.coroutines.IO` | silently falls back to Default | import it; restore `Main.immediate` |
| a root VM never ported the `logOutTrigger → ReplaceAction(/auth)` collector | logout does nothing | port the collector |
| per-composition `FontFamily` churn | wrong typeface metrics | font-family `CompositionLocal` at app root (compose-resources `Font()` is sync via runBlocking) |

Other port facts: Room-KMP (not SQLDelight) for a faithful port of a Room schema (`BundledSQLiteDriver`,
`setQueryCoroutineContext(Dispatchers.IO)`, expect/actual builder); a manual `AppGraph` is fine; the global
scope needs `SupervisorJob`; R8 needs keeps for runtime-resolved serializers. Owner sim QA after each
batch finds real bugs the gates miss.

Prod cautions when a debug build talks to the production API: no OTP spam — iterate by relaunch;
deleteAccount, feedback and payments are REAL writes. New deps (Firebase, payments SDK) need owner OK.
Design mockups for such an app: build from its real drawables and design-system radii — invented icons
get rejected.

## KMP calling app (Android + iOS; CallKit/PushKit, FCM)
- **Koin has no graph verification.** A repository taking an interface param with only the concrete class
  bound → `InstanceCreationException` on the first screen that resolves it. Unit tests + build pass. Bind
  `single<Iface>` or `get<Impl>()`, then open the screen.
- **Endless-ticker test hangs:** run the class on `backgroundScope` with
  `runTest(UnconfinedTestDispatcher()) { … }`; never `advanceUntilIdle()` with an infinite `delay` loop.
- **WebView force-dark CCE on some OEM Android 11 builds:** `compose-webview-multiplatform` calls
  `setForceDarkStrategy` unconditionally; lib or androidx.webkit bumps don't help; vendoring fails on
  `internal set`. Only an upstream `runCatching`.
- **Two Firebase projects** (one Android, one iOS) with independent Remote Config. `available=false` = an id
  published in the wrong project, next to a similar foreign id.
- The iOS simulator is useless for Firebase Remote Config (Installations keychain -34018) — test on device.
- Real-time RC may not arrive through a phone VPN client; turn the VPN off when testing.
- **One build number for both apps:** `CURRENT_PROJECT_VERSION` in `iosApp/Configuration/Config.xcconfig`
  feeds iOS `CFBundleVersion` AND Android `versionCode` (`composeApp/build.gradle.kts` parses it). **Never
  edit Version/Build in Xcode's General tab** — it writes a target-level value that shadows the xcconfig.
