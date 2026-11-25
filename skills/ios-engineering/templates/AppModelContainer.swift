// ---------------------------------------------------------------------------
// ORIGIN: AppModelContainer.swift of a shipping SwiftData app + the App Group probe it used
//         while it had a widget.
// PURPOSE: one process-wide ModelContainer and ONE public schema list that every test and
//          #Preview builds from (hand-copied lists crashed: "could not locate an NSEntityDescription").
// ---------------------------------------------------------------------------
import Foundation
import SwiftData

enum AppModelContainer {

    /// Set only if a widget/extension must share the store. Prefer a snapshot in App Group
    /// UserDefaults for widgets (a versioned Codable snapshot) and keep this nil.
    static let appGroupID: String? = nil   // e.g. "group.com.example.{{app}}"

    static let shared: ModelContainer = build()

    private static func build() -> ModelContainer {
        var config = ModelConfiguration()
        if let group = appGroupID,
           // SwiftData TRAPS (not throws) when handed a groupContainer the process isn't entitled
           // to — unsigned test host, CODE_SIGNING_ALLOWED=NO builds. Probe first.
           FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: group) != nil {
            config = ModelConfiguration(groupContainer: .identifier(group))
        }
        do {
            return try ModelContainer(for: schema, configurations: config)
        } catch {
            fatalError("Failed to build the ModelContainer: \(error)")
        }
    }

    /// The one true model list. Adding an entity: add it here AND to the reset routine
    /// (e.g. DataService.resetAll()). Adding an ATTRIBUTE to a shipped model: optional
    /// storage + computed accessor + templates/MigrationTests.swift.
    static var schema: Schema {
        Schema([
            // UserProfile.self,
            // TaskItem.self,
        ])
    }

    /// Tests / previews:
    static func inMemory() throws -> ModelContainer {
        try ModelContainer(for: schema, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
    }
}
// A ModelContext does not retain its container: services keep the container
// (`@ObservationIgnored private let container`) and tests hold it for the test's lifetime.
