// ---------------------------------------------------------------------------
// ORIGIN: DemoSeed.swift of a shipping app + the -<App>DebugPremium hook in its EntitlementStore.
// PURPOSE: DEBUG-only seeded state for screenshots and simulator QA, behind a launch arg.
// RUN:  xcrun simctl launch <udid> <bundle> -{{App}}DemoSeed -{{App}}DebugPremium
// RULES: whole file in #if DEBUG; never runs without the flag; never touches an existing
//        profile; called from App.init inside #if DEBUG; seeds look like real use.
// ---------------------------------------------------------------------------
#if DEBUG
import Foundation
import SwiftData

@MainActor
enum DemoSeed {
    static var requested: Bool { ProcessInfo.processInfo.arguments.contains("-{{App}}DemoSeed") }

    /// Value args: `-{{App}}SeedCount 500`.
    static func intArgument(_ name: String) -> Int? {
        let args = ProcessInfo.processInfo.arguments
        guard let i = args.firstIndex(of: name), i + 1 < args.count else { return nil }
        return Int(args[i + 1])
    }

    static func runIfRequested(context: ModelContext, score: ScoreService) {
        guard requested, score.profile == nil else { return }   // fresh install only
        let defaults = UserDefaults.standard
        defaults.set(true, forKey: "{{app}}.onboardingComplete") // skip onboarding / What's New / review ask
        defaults.set(true, forKey: "{{app}}.reviewDone")

        let cal = Calendar.current
        let today = cal.startOfDay(for: .now)
        func day(_ ago: Int) -> Date { cal.date(byAdding: .day, value: -ago, to: today)! }

        // Thirty days of believable use: a climb with one bad weekend.
        for ago in stride(from: 29, through: 1, by: -1) {
            let date = day(ago)
            _ = date // insert models for that day here; go through the SAME service/engine
                     // functions the app uses so derived numbers stay consistent.
        }
        try? context.save()
    }
}
#endif

// In the App's init:
//     #if DEBUG
//     DemoSeed.runIfRequested(context: container.mainContext, score: score)
//     #endif
//
// Forced premium in EntitlementStore:
//     #if DEBUG
//     private static let debugPremium = ProcessInfo.processInfo.arguments.contains("-{{App}}DebugPremium")
//     #endif
//     init: if Self.debugPremium { isPremium = true; status = PremiumStatus(… isTrial: true, 2 days left …) }
//     apply(_ info:): #if DEBUG guard !Self.debugPremium else { return } #endif   // real CustomerInfo must not undo it
//
// Present-once hooks (open a sheet/pack at launch) need a latch — .task(id:) re-fires on dismissal:
//     private static var debugHookDone = false
// Env-var hooks: SIMCTL_CHILD_OPEN_SCREEN=<id> xcrun simctl launch <udid> <bundle>
