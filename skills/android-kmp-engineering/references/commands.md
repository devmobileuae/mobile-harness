# Commands — exact, per repo shape

Every Gradle call gets `--max-workers=2` (heat budget). Finish with `./gradlew --stop`.
Never `clean build`. Shown without the flag below only where quoted verbatim from a repo file. Your per-repo
task names, device ids and quirks live in `local/skills/android-kmp-engineering/`.

## KMP single-module app (`:composeApp`)

```bash
./gradlew :composeApp:compileCommonMainKotlinMetadata --console=plain          # fastest gate, <1 s warm
./gradlew :composeApp:compileDebugKotlinAndroid --console=plain                # run BOTH platform compiles
./gradlew :composeApp:compileKotlinIosSimulatorArm64 --console=plain           #   when commonMain/expect changed
./gradlew :composeApp:testDebugUnitTest --console=plain                        # whole suite
./gradlew :composeApp:testDebugUnitTest --tests "*SignalingClient*" --console=plain
./gradlew :composeApp:linkDebugFrameworkIosSimulatorArm64 --console=plain      # only when Swift needs it
./gradlew :composeApp:installDebug                                             # emulator/device install
XCODEPROJ_PATH=iosApp/iosApp.xcodeproj ./gradlew :composeApp:integrateLinkagePackage   # after every posthog-kmp bump
```
- `:composeApp:iosSimulatorArm64Test` may not link when Firebase pods are involved (or `pod install` breaks on
  a new Ruby/CocoaPods) — run common tests through the Android JVM leg.
- Not caught by any of these: Koin bindings, audio routing, push wake, FGS, background survival.
- Debugging on device: grep logcat for your auth/reconcile tag, `fetchAndActivate`, the FCM service tag
  (payload, `priority=2/orig=2` = NORMAL), a periodic call-diagnostics line (bytes/packets must grow),
  REGISTER refresh and keepalive lines. FCM message id `0:<µs epoch>%…` = server push time.
- If the repo host's CLI lacks MR-create scope, open merge requests with git push options
  (`-o merge_request.create -o merge_request.target=<branch>`).

## Multi-module Android

```bash
./gradlew :feature:auth:testDebugUnitTest      # touched modules first
./gradlew lint
./gradlew testDebugAll                          # all modules, debug (templates/testDebugAll.gradle.kts)
./gradlew testDebugAll -PskipRobolectricTests=true   # what CI runs
./gradlew updateLintBaseline
./gradlew lint :app:verifyNativeLibAlignment    # report app/build/reports/nativeLibAlignment.txt
```
Release-candidate tags only through the repo's own skill when it has one; a PreToolUse guard may deny raw
`git tag`/`git push` of `v*`. 16 KB check by hand: `readelf -l` LOAD align `0x4000`;
`zipalign -c -P 16 -v 4 <apk>`.

## KMP `:shared` + `:composeApp` (a port)

```bash
./gradlew :shared:compileKotlinIosSimulatorArm64    # K/N compile (primary)
./gradlew :shared:compileAndroidMain
./gradlew :shared:iosSimulatorArm64Test             # all tests (commonTest; no JVM leg)
./gradlew :composeApp:assembleDebug
./gradlew :composeApp:assembleRelease               # R8 — needs keeps for runtime-resolved serializers
xcodebuild -project iosApp/iosApp.xcodeproj -scheme iosApp -sdk iphonesimulator build
git show <snapshot-commit>:<path>                   # the deleted Android original, for 1:1 diffs
```
Debug ⇒ stage API + mock navigation (fixtures in `shared/src/commonMain/composeResources/files/mocks/`);
release ⇒ prod. Where the owner forbids launching emulators/simulators, subagents may still run the four gates.

## Other KMP apps

Standard KMP task names (confirm with `./gradlew :composeApp:tasks`):
```bash
./gradlew --max-workers=2 :composeApp:compileKotlinIosSimulatorArm64 :composeApp:assembleDebug
./gradlew --max-workers=2 :composeApp:linkDebugFrameworkIosSimulatorArm64
./gradlew --max-workers=2 :composeApp:testDebugUnitTest
```
iOS smoke when the Simulator MCP needs `sudo xcode-select` and idb-companion won't install: computer-use
on Simulator.app works. Disk: `~/.konan` accumulates toolchains (≈ 1.4 GB each); keep only current Kotlin versions.

## Native Android with native libs

JDK 17. `./gradlew --max-workers=2 :app:assembleDebug`; fetch native tool binaries (e.g. Filament `matc`)
with the repo's script into a git-ignored folder before compiling materials; asset-sync tasks that read
the iOS repo need its path in `local.properties`.

## Maestro UI tests

```bash
maestro test -e APP_ID=<applicationId>.debug flow.yaml
maestro test -e APP_ID=<applicationId> --format junit --output report.xml maestro-tests/android/flow.yaml
maestro studio
```
Needs an app build with test tags on the nodes. `steps/` and `shared/` files are never run directly
(`templates/maestro-flow.yaml`). CI on a runner without `/dev/kvm`: API 28 arm64-v8a AVD on the legacy
emulator build (ARM-on-x86 TCG), boot timeout 1200 s, extra apt libs (`libpulse0 libasound2 libxtst6…`).

## Emulator / device

```bash
emulator -avd <avd_name> -dns-server 8.8.8.8,1.1.1.1      # under the host VPN
adb shell am kill <pkg>                                   # killed-app test; NOT force-stop
adb run-as <pkg> cat shared_prefs/<file>.xml              # read persisted token/flags (debug builds)
adb emu kill                                              # shut the emulator after the check
```
Real-time Remote Config may not arrive through a phone VPN client — VPN off when testing.
