// ---------------------------------------------------------------------------
// ORIGIN: AnalyticsEventTests.swift + AnalyticsFacadeTests.swift (SpyBackend) of a shipping app.
// PURPOSE: pin the event taxonomy (golden list) and naming/PII rules; spy the facade.
// Adding an event = a new case + an entry in `samples` + a line in `golden`, in the same change.
// ---------------------------------------------------------------------------
import XCTest
@testable import MyApp   // ← your app module

final class SpyBackend: AnalyticsBackend {
    var identified: [(id: String, properties: [String: Any])] = []
    var captured: [(event: String, properties: [String: Any])] = []
    var superProperties: [[String: Any]] = []
    var optIns = 0, optOuts = 0, flushes = 0
    func identify(_ id: String, properties: [String: Any]) { identified.append((id, properties)) }
    func capture(_ e: String, properties: [String: Any]) { captured.append((e, properties)) }
    func screen(_ name: String) {}
    func setPersonProperties(_ p: [String: Any]) {}
    func register(_ p: [String: Any]) { superProperties.append(p) }
    func optIn() { optIns += 1 }; func optOut() { optOuts += 1 }; func flush() { flushes += 1 }
}

final class AnalyticsEventTests: XCTestCase {

    static let golden: [String] = [
        "paywall_shown", "paywall_offerings_failed", "paywall_unavailable", "analytics_toggled",
    ]

    private static let snake = try! NSRegularExpression(pattern: "^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
    private func isSnake(_ s: String) -> Bool {
        Self.snake.firstMatch(in: s, range: NSRange(s.startIndex..., in: s)) != nil
    }

    func testSamplesCoverTheGoldenListExactly() {
        XCTAssertEqual(AnalyticsEvent.samples.map(\.name), Self.golden)
    }

    func testNamesAndKeysAreSnakeCase() {
        for e in AnalyticsEvent.samples {
            XCTAssertTrue(isSnake(e.name), e.name)
            for k in e.properties.keys { XCTAssertTrue(isSnake(k), "\(e.name).\(k)") }
        }
    }

    func testNoPIIShapedKeys() {
        let banned = ["name", "email", "text", "body", "note", "steps", "phone"]
        for e in AnalyticsEvent.samples {
            for k in e.properties.keys { XCTAssertFalse(banned.contains(k), "\(e.name).\(k)") }
        }
    }

    func testValuesAreScalarsOrStringArrays() {
        for e in AnalyticsEvent.samples {
            for (k, v) in e.properties {
                XCTAssertTrue(v is String || v is Int || v is Bool || v is [String], "\(e.name).\(k)")
            }
        }
    }
}

@MainActor
final class AnalyticsFacadeTests: XCTestCase {
    func testBuildTypeIsRegisteredBeforeIdentify() {
        let spy = SpyBackend()
        Analytics.start(backend: spy, distinctID: "install-uuid", person: [:])
        XCTAssertEqual(spy.superProperties.first?["build_type"] as? String, "debug")
        XCTAssertNil(spy.superProperties.first?["build"])   // collides with the SDK's CFBundleVersion
        XCTAssertEqual(spy.identified.first?.id, "install-uuid")
    }
}
