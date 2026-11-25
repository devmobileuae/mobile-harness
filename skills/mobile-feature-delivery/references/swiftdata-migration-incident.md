# SwiftData: the additive-field crash and the pattern that replaces it

Your own incident write-ups: `local/skills/mobile-feature-delivery/`.

## What happens
- Change: `TaskItem.source: TaskSource = .daily` added to an existing, shipped `@Model`.
- Result: real upgrade installs crash (**SIGABRT inside the generated getter**) on the first screen that
  reads the attribute.
- Test suite: **all green.** Every persistence test builds a fresh in-memory `ModelContainer`, so no
  test ever holds a row written under the older schema.
- Why: a Swift default value applies only at `init`. Rows already in the store have no value, and
  SwiftData's lightweight migration cannot add a non-optional attribute to a populated store.

## The fix pattern (copy this, not a SchemaMigrationPlan, for additive fields)

```swift
// Models.swift — TaskItem
/// Rows written before this shipped decode as `nil`, which `source` reads as `.daily`.
var sourceValue: TaskSource?                    // the ONLY stored, migrating attribute

/// Not persisted — computed properties are ignored by @Model.
var source: TaskSource {
    get { sourceValue ?? .daily }
    set { sourceValue = newValue }
}
```

Same pattern for collections: `unlockedItemsValue: [Item]?` with
`var unlockedItems: [Item] { unlockedItemsValue ?? [defaultItem] }` — the legacy default is the
*previous behaviour*, so nothing changes on first read after the update.

## The test that would have caught it

```swift
func testLegacyRowsWithNoStoredSourceReadAsDaily() {
    let task = TaskItem(title: "legacy")
    task.sourceValue = nil          // exactly what a pre-migration row decodes to
    XCTAssertEqual(task.source, .daily)
    // ...and such a row still counts toward the aggregates that read it
}
```
Plus the on-disk test: `skills/ios-engineering/templates/MigrationTests.swift`.

## Rules
- **New attribute on an existing @Model → optional storage + computed accessor + a nil-row test.**
- **New entity → non-optional is fine.** Lightweight migration adds whole entities cleanly. The two
  cases pull in opposite directions; don't generalise from one to the other.
- Adding an entity = update `AppModelContainer.schema` and the reset-all path. Every test and
  `#Preview` builds its container from `AppModelContainer.schema` — keep it single-sourced (hand-copied
  lists crash with `could not locate an NSEntityDescription`).
- **Renaming a stored attribute discards user data.** Converting a shipped non-optional attribute to the
  optional pattern is itself a rename — do it only before the first release, or migrate explicitly.
- The upgrade check is real, not simulated: install the **previous App Store build** (or the tagged
  archive: `git checkout <tag>` → build → run → make data), then install the new build over it and
  open every screen that reads the changed model. A version ledger that records the launch transition
  (`upgrade` / `fromLegacy` / `newBuild`) tells you which path ran.

## Same class on other stores
- **Keychain:** adding `kSecAttrAccessible` to `KeychainSettings` queries stops matching pre-existing
  items → `-25300` crash on upgrade. Revert; an attribute migration is a separate task.
- **DataStore → multiplatform-settings:** the update-in-place data migration for existing users must be
  scoped explicitly, or it is silently skipped.
- Room/SQLDelight: schema bump = migration + a test that opens a DB written by the previous version.
