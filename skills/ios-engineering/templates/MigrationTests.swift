// ---------------------------------------------------------------------------
// ORIGIN: written for this skill from a real incident (TaskItem.source = .daily → SIGABRT on a
//         real upgrade install while the whole in-memory suite was green) and its nil-row test.
// VERIFIED: in a SwiftPM harness (macOS 14, SwiftData): with the optional pattern
//         the on-disk test PASSES; with `var source: TaskSource = .daily` it aborts
//         ("Exited with unexpected signal code 6") — i.e. it catches the real crash.
// PURPOSE: every additive change to a shipped @Model gets BOTH tests below.
// HOW: copy `LegacyV1` EXACTLY as the last release shipped it
//      (`git show <last-tag>:<App>/Core/Model/Models.swift`), keep only the entities you need.
//      SwiftData names the entity after the unqualified class name, so LegacyV1.TaskItem and
//      TaskItem map to the same table.
// ---------------------------------------------------------------------------
import XCTest
import SwiftData
@testable import MyApp   // ← your app module

/// Frozen copy of the model as the PREVIOUS release shipped it. Never edit after the fact.
enum LegacyV1 {
    @Model final class TaskItem {
        var title: String
        var detail: String
        init(title: String, detail: String = "") { self.title = title; self.detail = detail }
    }
}

final class TaskItemMigrationTests: XCTestCase {

    /// (a) Cheap unit test: what a pre-migration row decodes to reads as the previous behaviour.
    func testLegacyRowWithNoStoredValueReadsAsPreviousBehaviour() {
        let task = TaskItem(title: "legacy", detail: "", difficulty: .easy, lane: .body)
        task.sourceValue = nil
        XCTAssertEqual(task.source, .daily)
    }

    /// (b) The test that would have caught 2026-08-02: a store WRITTEN BY THE OLD SCHEMA on disk,
    /// reopened with the current schema. In-memory containers can never hit this path.
    @MainActor
    func testStoreWrittenByPreviousSchemaOpensAndReads() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: dir) }
        let url = dir.appendingPathComponent("store.sqlite")

        do { // old app: write a row, let the container go out of scope
            let old = try ModelContainer(for: Schema([LegacyV1.TaskItem.self]),
                                         configurations: ModelConfiguration(url: url))
            old.mainContext.insert(LegacyV1.TaskItem(title: "written by the previous release"))
            try old.mainContext.save()
        }

        // new app: lightweight migration runs here; a non-optional new attribute traps on read
        let new = try ModelContainer(for: Schema([TaskItem.self]),
                                     configurations: ModelConfiguration(url: url))
        let rows = try new.mainContext.fetch(FetchDescriptor<TaskItem>())
        XCTAssertEqual(rows.count, 1)
        XCTAssertNil(rows[0].sourceValue)          // old rows carry no value…
        XCTAssertEqual(rows[0].source, .daily)     // …and read as the previous behaviour
    }
}
// If the whole schema must open (relationships), use AppModelContainer.schema for `new`
// and a LegacyV1 copy of every entity in the relationship graph for `old`.
