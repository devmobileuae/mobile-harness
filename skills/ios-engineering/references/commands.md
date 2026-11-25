# Commands — exact shapes

zsh is the shell. Your per-repo command lists (scheme names, sim ids, seed args, tool scripts) live in
`local/skills/ios-engineering/`. Release upload/ASC steps beyond the archive line live in
`skills/mobile-feature-delivery` §7 and its `scripts/release-ios.sh`, `scripts/asc.py`, `scripts/asc_status.py`.

## Simulators and devices

| What | Device |
|---|---|
| test gate | one fixed iPhone sim (e.g. iPhone 16 Pro); use its `id=` once the name is ambiguous |
| store screenshots | iPhone Pro Max size, 1320×2868 |
| deployment-floor check | a sim on the oldest supported iOS |
| App Review's iPad | iPad Air 11" (M3) — iPhone-compat window check |
| perf / purchases | a physical iPhone via `devicectl` (id from `xcrun devicectl list devices`) |

Points for MCP taps: iPhone 16 Pro ≈ 402×874, Pro Max 440×956.

## Build, test, seeded run (xcodegen app)

```sh
xcodegen generate
xcodebuild build -project <App>.xcodeproj -scheme <App> \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
  -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO
xcodebuild test -project <App>.xcodeproj -scheme <App> \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
  -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO
# one class / one test
  -only-testing:<App>Tests/<Class>/<testMethod>
# HealthKit on the sim: same build WITHOUT CODE_SIGNING_ALLOWED=NO
cd <App>Kit && swift test                               # logic in a local package
```
Built app: `build/DerivedData/Build/Products/Debug-iphonesimulator/<App>.app`.

```sh
xcrun simctl uninstall <udid> <bundle_id>
xcrun simctl install <udid> build/DerivedData/Build/Products/Debug-iphonesimulator/<App>.app
xcrun simctl launch <udid> <bundle_id> -<App>DemoSeed -<App>DebugPremium
SIMCTL_CHILD_OPEN_SCREEN=<id> xcrun simctl launch <udid> <bundle_id>      # env-var hooks
xcrun simctl io <udid> screenshot /tmp/<app>-home.png
```
Screenshot states come only from the DEBUG seed and from using the app; a state the seed can't reach
is a new seed option in `DemoSeed.swift`, never an edit of the app's store on disk.

Release archive (owner's go only):
```sh
xcodebuild archive -project <App>.xcodeproj -scheme <App> -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/release/<App>-<ver>-<build>.xcarchive \
  -allowProvisioningUpdates
xcodebuild -exportArchive -archivePath build/release/<App>-<ver>-<build>.xcarchive \
  -exportOptionsPlist build/ExportOptions.plist -exportPath build/release/export -allowProvisioningUpdates
```
Export uses the Apple ID signed into Xcode, no API-key flags.

Hand-kept `.pbxproj` (no xcodegen): `xcodebuild -project <App>.xcodeproj -scheme <App> -destination
'platform=iOS Simulator,id=<udid>' build`; walk every touched screen in light AND dark + Dynamic Type XL
on text-heavy screens.

## Device runs, warnings, packages

```sh
xcrun devicectl device process launch --console --terminate-existing --device <id> \
  --environment-variables '{"PERF_FPS":"1"}' <bundle_id>          # Release on the iPhone with an FPS probe
xcodebuild clean build-for-testing -project <App>.xcodeproj -scheme <App> \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' | grep warning:
swift build --sdk "$(xcrun --sdk iphonesimulator --show-sdk-path)" --triple arm64-apple-ios18.0-simulator  # no sim
```
`xcodebuild` does not refresh `Localizable.xcstrings` — keep a sync script and run it after code changes.
ASC scripts: a temp venv with `pyjwt[crypto]` + `requests`; creds in a git-ignored `config.json` next to the
script (ask the owner to copy it in). OCR/Vision pipeline bugs: compile the real source files into a macOS
`swiftc` harness that prints every stage.

## Diagnostics

```sh
xcrun simctl list devices available                     # ids when a name is ambiguous
xcrun simctl spawn <udid> log show --last 5m --predicate 'process == "<App>Widgets"'   # widget failures
xcrun simctl io <udid> screenshot out.png               # the MCP panel's own frame lags
xcrun simctl privacy <udid> grant photos <bundle>       # writes TCC but iOS 26 still says notDetermined — tap Allow once
```
Steps in Health on the sim: Health app → Steps → Add Data (simctl cannot inject samples).
Toasts live ~2 s: shoot a background burst and group frames by file size.
