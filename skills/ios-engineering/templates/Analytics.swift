// ---------------------------------------------------------------------------
// ORIGIN: Core/Analytics/{Analytics,AnalyticsBackend,PostHogBackend}.swift of a shipping app,
//         condensed into one file for copying.
// PURPOSE: vendor-hidden PostHog analytics: one importing file, typed events, build_type
//          super-property, test-host Noop, opt-out toggle.
// SPLIT BACK into Core/Analytics/: Analytics.swift, AnalyticsBackend.swift, PostHogBackend.swift
// (PostHogBackend.swift = the ONLY `import PostHog` in the app). Token lives in Config/AnalyticsConfig.swift
// (public by design; never paste it into skills or chat).
// ---------------------------------------------------------------------------
import Foundation
import PostHog   // ← only in PostHogBackend.swift after splitting

protocol AnalyticsBackend: AnyObject {
    func identify(_ distinctID: String, properties: [String: Any])
    func capture(_ event: String, properties: [String: Any])
    func screen(_ name: String)
    func setPersonProperties(_ properties: [String: Any])
    func register(_ superProperties: [String: Any])
    func optIn(); func optOut(); func flush()
}

final class NoopBackend: AnalyticsBackend {
    func identify(_ distinctID: String, properties: [String: Any]) {}
    func capture(_ event: String, properties: [String: Any]) {}
    func screen(_ name: String) {}
    func setPersonProperties(_ properties: [String: Any]) {}
    func register(_ superProperties: [String: Any]) {}
    func optIn() {}; func optOut() {}; func flush() {}
}

final class PostHogBackend: AnalyticsBackend {
    init(projectToken: String, host: String, optedOut: Bool) {
        let config = PostHogConfig(projectToken: projectToken, host: host)  // US: https://us.i.posthog.com
        config.captureApplicationLifecycleEvents = true   // Installed/Opened/Updated/Backgrounded
        config.captureScreenViews = false                 // screens are explicit
        config.captureElementInteractions = false
        config.enableSwizzling = false
        config.sessionReplay = false
        config.preloadFeatureFlags = false                // on only if the app reads flags
        config.errorTrackingConfig.autoCapture = true     // $exception on next launch
        config.optOut = optedOut
        PostHogSDK.shared.setup(config)
    }
    func identify(_ id: String, properties: [String: Any]) { PostHogSDK.shared.identify(id, userProperties: properties) }
    func capture(_ e: String, properties: [String: Any]) { PostHogSDK.shared.capture(e, properties: properties) }
    func screen(_ name: String) { PostHogSDK.shared.screen(name) }
    func setPersonProperties(_ p: [String: Any]) { PostHogSDK.shared.capture("$set", properties: nil, userProperties: p) }
    func register(_ p: [String: Any]) { PostHogSDK.shared.register(p) }
    func optIn() { PostHogSDK.shared.optIn() }
    func optOut() { PostHogSDK.shared.optOut() }
    func flush() { PostHogSDK.shared.flush() }
}

@MainActor
enum Analytics {
    static let enabledKey = "{{app}}.analyticsEnabled"     // absent = enabled
    private static var backend: AnalyticsBackend = NoopBackend()

    static var isEnabled: Bool { UserDefaults.standard.object(forKey: enabledKey) as? Bool ?? true }

    /// Register super-properties BEFORE identify so they ride the first event.
    /// Name it `build_type`, never `build` — the SDK's lifecycle events already carry
    /// `build` = CFBundleVersion and the two overwrite each other (renamed to build_type).
    static func start(backend: AnalyticsBackend, distinctID: String, person: [String: Any]) {
        self.backend = backend
        guard isEnabled else { return }
        #if DEBUG
        backend.register(["build_type": "debug"])
        #else
        backend.register(["build_type": "release"])
        #endif
        backend.identify(distinctID, properties: person)
    }

    static func track(_ event: AnalyticsEvent) {
        guard isEnabled else { return }
        backend.capture(event.name, properties: event.properties)
    }

    /// Off: record the toggle, flush, then opt out. On: opt in, then record.
    static func setEnabled(_ enabled: Bool) {
        if enabled {
            UserDefaults.standard.set(true, forKey: enabledKey); backend.optIn()
            track(.analyticsToggled(enabled: true))
        } else {
            track(.analyticsToggled(enabled: false)); backend.flush()
            UserDefaults.standard.set(false, forKey: enabledKey); backend.optOut()
        }
    }
}

/// Taxonomy = code. snake_case names/keys; values = enum raw values, small ints, bools, string arrays.
/// No PII, no free text, no health numbers. Adding a case = add to `samples` + the golden test list.
enum AnalyticsEvent: Equatable {
    case paywallShown(trigger: String)
    case paywallOfferingsFailed(error: String)
    case paywallUnavailable(trigger: String, plan: String)
    case analyticsToggled(enabled: Bool)

    var name: String {
        switch self {
        case .paywallShown: "paywall_shown"
        case .paywallOfferingsFailed: "paywall_offerings_failed"
        case .paywallUnavailable: "paywall_unavailable"
        case .analyticsToggled: "analytics_toggled"
        }
    }
    var properties: [String: Any] {
        switch self {
        case let .paywallShown(t): ["trigger": t]
        case let .paywallOfferingsFailed(e): ["error": e]
        case let .paywallUnavailable(t, p): ["trigger": t, "plan": p]
        case let .analyticsToggled(e): ["enabled": e]
        }
    }
    static let samples: [AnalyticsEvent] = [
        .paywallShown(trigger: "onboarding"), .paywallOfferingsFailed(error: "x"),
        .paywallUnavailable(trigger: "onboarding", plan: "annual"), .analyticsToggled(enabled: true),
    ]
}

// App.init wiring:
//   let isTestHost = ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil
//   let backend: AnalyticsBackend = AnalyticsConfig.isConfigured && !isTestHost
//       ? PostHogBackend(projectToken: AnalyticsConfig.projectToken, host: AnalyticsConfig.host,
//                        optedOut: !Analytics.isEnabled)
//       : NoopBackend()
//   Analytics.start(backend: backend, distinctID: InstallIdentity.id.uuidString, person: …)
// distinct_id = Keychain install UUID = RevenueCat appUserID → rc_* events land on the same person.
// Never .onAppear-track inside always-mounted panes; pass isActive: to inline paywalls.
