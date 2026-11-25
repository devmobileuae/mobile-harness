#!/bin/zsh
# Archive the Release build and upload it to App Store Connect (TestFlight).
#   upload.sh <build number> [project.xcodeproj] [scheme] [ExportOptions.plist]
# Run from the app repo root. Defaults: the only *.xcodeproj in the root, scheme = project name,
# ExportOptions.plist next to this script (templates/ExportOptions.plist with your apple_team_id).
# Every upload needs a new build number; the version itself is MARKETING_VERSION in project.yml.
# Signs with the Apple ID logged in to Xcode: the App Store Connect API key has no cloud-signing rights.
set -e
BUILD=${1:?build number}
[[ -f project.yml ]] && xcodegen generate -q
PROJ=${2:-$(ls -d *.xcodeproj | head -1)}
SCHEME=${3:-${PROJ:r}}
OPTS=${4:-$(dirname "$0")/ExportOptions.plist}
rm -rf build-archive
xcodebuild archive -project "$PROJ" -scheme "$SCHEME" -configuration Release \
  -destination 'generic/platform=iOS' -archivePath "build-archive/$SCHEME.xcarchive" \
  -allowProvisioningUpdates CURRENT_PROJECT_VERSION=$BUILD 2>&1 | grep -E "error:|ARCHIVE (SUCCEEDED|FAILED)"
xcodebuild -exportArchive -archivePath "build-archive/$SCHEME.xcarchive" \
  -exportOptionsPlist "$OPTS" -exportPath build-archive/export \
  -allowProvisioningUpdates 2>&1 | grep -E "error:|Upload succeeded|EXPORT (SUCCEEDED|FAILED)"
