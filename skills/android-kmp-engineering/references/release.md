# Release — Android side, Firebase gates, signing

The update-gate release recital for a KMP app with a Remote Config update gate (bump → check `appUpdate`
in both projects → raise thresholds only after the store serves N → keep the allow-list) is in
`mobile-feature-delivery` §8 — say it unprompted on every release mention. This file holds the
engineering detail behind it. Never upload, roll out, or publish Remote Config yourself. Your per-repo
version sources and release history: `local/skills/android-kmp-engineering/`.

## 1. Version source per repo shape

| Shape | Where the number lives | Rule |
|---|---|---|
| KMP single module, shared build number | `iosApp/Configuration/Config.xcconfig` `CURRENT_PROJECT_VERSION` = iOS `CFBundleVersion` AND Android `versionCode` (`composeApp/build.gradle.kts` parses it, fails on non-integer — `templates/xcconfig-version.gradle.kts`) | one integer for both; `versionName` = a display label (e.g. `YYYY.M.N`); iOS `MARKETING_VERSION` may stay fixed; never edit Version/Build in Xcode's General tab (writes a shadowing target-level value) |
| multi-module Android | git tag via a build-version convention plugin: `vX.Y.Z-N` → major·10000 + minor·100 + patch; CI tag else `git describe` | tags only through the repo's release skill |
| KMP port | build-version convention plugin with a minimum-tag contract; older versions fail fast | a reported client-version header is a separate pin (= shipped Android release) |
| simple KMP app | hardcoded `versionCode` / `versionName` in `composeApp/build.gradle.kts` | bump both by hand |
| KMP template app | iOS plist binary version ≠ store version | release only from the one checkout that matches the shipped tree; never from a stale copy with the same bundle id |

A `versionName` whose digit shape changes changes the User-Agent, and a backend that keys devices by UA
may map the device to a new identity — check with the backend before changing the format.

## 2. Firebase Remote Config — the update gate

Param `remote` (type JSON) in **both** Firebase projects (Android and iOS; iOS Stage + Prod may share one).
Inside: the feature allow-list `allowedIds` (empty list = feature off for everyone) and
`appUpdate { minSupportedVersion, latestVersion, storeUrl }`. Shape: `templates/remote-config-appUpdate.json`.

Client rules, all deliberate:
- `appUpdate` decoded as raw `JsonElement`: a toggles decoder that falls back to an EMPTY allow-list on any
  decode exception would switch the feature off if a typed field got an unquoted number.
- "Failed to load → let them in": `FeatureTogglesState.Ready.fetchedThisProcess`; a failed cold-start fetch
  on Android still returns the on-disk copy, which may hold a mandatory threshold — ignored.
- Shape guard: a threshold with a different segment count than the running version is ignored.
- Decision latched at cold start / resume / call end; a call always wins; `UpdateGate.relaxIfLooser`
  applies a looser config at once; tightening waits for a trigger.
- Debug fetch interval 0, release 1 h → a bad publish can block users up to an hour without real-time.
- Builds older than the gate ignore it: ship first, publish thresholds after.

Order: (1) bump N; (2) before N reaches users, check both projects: no QA leftovers above N (a stray
`latest` above N prompts everyone on N), real `storeUrl` (Play / TestFlight); (3) after the store serves N,
optionally raise `latest` (prompt) or `min` (force). Edit the existing JSON — never delete the param.

`available=false` triage: reconcile log line → activated list after `fetchAndActivate` → exact id match
(an id published in the wrong project, next to a near-identical foreign id, looks exactly like this).

## 3. Play release steps

- Multi-module Android: RC from a `v*` tag → CI release-candidate job (`assembleRelease
  bundleRelease` + mapping upload) → **Play internal → closed testing → production**.
- targetSdk policy: Play requires each update to target the current API level after its yearly deadline.
  Possible temporary opt-outs: `android.window.PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY=true`
  (keeps portrait on sw ≥ 600dp; a later API ignores it) and `android:enableOnBackInvokedCallback="false"`
  (predictive back never fires when each screen's `BackHandler` registers after NavHost). Real fix =
  `PredictiveBackHandler` migration.
- 16 KB pages: `:app:verifyNativeLibAlignment` gates `assembleRelease`/`bundleRelease`; prove the gate with a
  misaligned canary `.so` ("aligns LOAD segments to 0x1000").
- A new app: RevenueCat + Play subscription, then closed testing, then production; the owner provides the
  Play Console app + Play App Signing.
- iOS side of a KMP app may ship via TestFlight only (builds expire after 90 days).

**Ask, do not assert:** the closed-testing tester-count/days rule for new personal developer accounts,
staged-rollout percentages, who presses Promote.

## 4. Signing (names only — never values)

- A signing convention plugin that reads env `KEY_STORE_FILE`, `KEY_STORE_KEY_ALIAS` (+ the matching
  password vars) else `keystore.properties` and **falls back to the debug signature with only a WARN** lets a
  debug-signed "RC" ship unnoticed. Verify with `apksigner verify --print-certs`.
- Update-in-place needs the same `applicationId` and signing key; a KMP port with a new `applicationId`
  cannot replace the shipped app.
- A Firebase Android API key restricted to package + Play app-signing + upload SHA-1s + one machine's debug
  SHA-1 means a debug build from another machine cannot register for FCM.
- KMP iOS: entitlements (push, Apple Pay) must exist before an archive; `CODE_SIGNING_ALLOWED=NO` builds
  lose keychain access (-34018).

## 5. Pre-release cleanup (things left in trees before)

- Temporary triage logging (an NSLog of a push token, a release triage log writer) — revert before a store build.
- Mock fixtures in the release APK.
- R8 never exercised = not releasable.
