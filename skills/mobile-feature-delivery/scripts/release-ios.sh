#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# ASSEMBLED FOR THIS SKILL from a release recipe that shipped several versions of an
# xcodegen app. Commands are the ones used; the wrapper is new.
# RUN from the app repo root:  <plugin>/skills/mobile-feature-delivery/scripts/release-ios.sh MyApp 1.2.0 14
#   (bump MARKETING_VERSION / CURRENT_PROJECT_VERSION in project.yml FIRST)
# KEY FACTS:
#   - archive works with -allowProvisioningUpdates (+ API-key flags if you have them);
#   - EXPORT must use the Xcode-signed-in account, NO API-key flags: the ASC key lacks
#     cloud-signing rights and there is no local distribution cert;
#   - ExportOptions: method app-store-connect, destination upload (templates/ExportOptions.plist)
#     -> the export step uploads the build itself.
#   - never submits for review: the owner attaches the build and presses Submit.
# ---------------------------------------------------------------------------
set -euo pipefail
SCHEME=${1:?scheme}; VER=${2:?marketing version}; BUILD=${3:?build number}
OPTS=${EXPORT_OPTIONS:-build/ExportOptions.plist}
ARCHIVE="build/release/${SCHEME}-${VER}-${BUILD}.xcarchive"

grep -q "MARKETING_VERSION: \"${VER}\"" project.yml || { echo "project.yml MARKETING_VERSION != ${VER}"; exit 1; }
grep -q "CURRENT_PROJECT_VERSION: \"${BUILD}\"" project.yml || { echo "project.yml CURRENT_PROJECT_VERSION != ${BUILD}"; exit 1; }
[ -f "$OPTS" ] || { echo "missing $OPTS (copy templates/ExportOptions.plist, set teamID)"; exit 1; }

xcodegen generate
# Gate: the same build+test the CLAUDE.md demands. Signing off for the gate only.
xcodebuild test -project "${SCHEME}.xcodeproj" -scheme "$SCHEME" \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
  -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO | tail -5

xcodebuild archive -project "${SCHEME}.xcodeproj" -scheme "$SCHEME" \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath "$ARCHIVE" -allowProvisioningUpdates

xcodebuild -exportArchive -archivePath "$ARCHIVE" \
  -exportOptionsPlist "$OPTS" -exportPath build/release/export -allowProvisioningUpdates

echo "Uploaded ${VER} (${BUILD}). Next: wait for processing, attach in ASC, owner submits."
