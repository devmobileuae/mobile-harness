// ---------------------------------------------------------------------------
// ORIGIN: EntitlementStore.swift of a shipping app (status, AdServices, RestoreOutcome) + the
//         offerings loader from its PaywallView.swift. Trimmed.
// PURPOSE: the one RevenueCat seam: offline-safe config, install-UUID appUserID, AdServices,
//          stream-driven isPremium, honest restore, offerings with retry + eligibility.
// Keys: public SDK key in Config/RevenueCatConfig.swift — never in a skill, chat or log.
// ---------------------------------------------------------------------------
import Foundation
import Observation
import RevenueCat

enum RevenueCatConfig {
    static let apiKey = "appl_PLACEHOLDER"          // sentinel = offline mode (dev/previews)
    static let entitlementID = "premium"
    static let offeringID = "default"
    static var isConfigured: Bool { apiKey != "appl_PLACEHOLDER" }
    static let termsURL = URL(string: "https://example.com/terms")!     // must be live (3.1.2)
    static let privacyURL = URL(string: "https://example.com/privacy")!
}

@MainActor
@Observable
final class EntitlementStore {
    var isPremium = false
    @ObservationIgnored private var observerTask: Task<Void, Never>?

    init() { configureIfPossible() }

    private func configureIfPossible() {
        // Purchases.shared before configure() is a fatalError, not a throw.
        guard RevenueCatConfig.isConfigured else { return }
        if !Purchases.isConfigured {
            Purchases.logLevel = .warn
            // Same id as PostHog distinct_id and backend rows → rc_* events land on one person.
            Purchases.configure(withAPIKey: RevenueCatConfig.apiKey, appUserID: InstallIdentity.id.uuidString)
        }
        // Not on by default; without it ASA installs are "No Attribution".
        // Must come AFTER configure.
        Purchases.shared.attribution.enableAdServicesAttributionTokenCollection()
        Task { await refresh() }
        observerTask?.cancel()
        observerTask = Task { [weak self] in
            for await info in Purchases.shared.customerInfoStream {
                guard let self else { return }
                self.apply(info)
            }
        }
    }

    private func refresh() async {
        guard RevenueCatConfig.isConfigured else { return }
        if let info = try? await Purchases.shared.customerInfo() { apply(info) }  // keep last state on error
    }

    private func apply(_ info: CustomerInfo) {
        isPremium = info.entitlements[RevenueCatConfig.entitlementID]?.isActive == true
    }

    /// The caller must tell "never bought" from "the call failed" (a review finding).
    enum RestoreOutcome: Equatable { case restored, nothingToRestore, failed(String) }

    @discardableResult
    func restorePurchases() async -> RestoreOutcome {
        guard RevenueCatConfig.isConfigured else { return .nothingToRestore }
        do {
            apply(try await Purchases.shared.restorePurchases())
            return isPremium ? .restored : .nothingToRestore
        } catch {
            return .failed(error.localizedDescription)   // state stays as it was
        }
    }
}

// MARK: - Paywall offerings loader (lives in the paywall view/VM)

enum OfferingsState { case loading, ready, unavailable }

@MainActor
func loadPackages(attempt: Int = 1) async -> (state: OfferingsState, packages: [Package], trialDays: [String: Int]) {
    guard RevenueCatConfig.isConfigured else { return (.ready, [], [:]) }   // documented fallback prices
    do {
        let offerings = try await Purchases.shared.offerings()
        guard let offering = offerings.offering(identifier: RevenueCatConfig.offeringID) ?? offerings.current,
              !offering.availablePackages.isEmpty
        else { throw URLError(.resourceUnavailable) }       // empty offering = same dead end as an error
        var trials: [String: Int] = [:]
        for pkg in offering.availablePackages {
            // Promise a trial only if the product HAS a free-trial intro AND this user is eligible (3.1.2).
            guard let intro = pkg.storeProduct.introductoryDiscount, intro.paymentMode == .freeTrial else { continue }
            let status = await Purchases.shared.checkTrialOrIntroDiscountEligibility(product: pkg.storeProduct)
            if status == .eligible { trials[pkg.identifier] = intro.subscriptionPeriod.value }
        }
        return (.ready, offering.availablePackages, trials)
    } catch {
        // Cold StoreKit cache + App Review's flaky env: two more tries, 1 s then 2 s.
        if attempt < 3 {
            try? await Task.sleep(for: .seconds(attempt))
            return await loadPackages(attempt: attempt + 1)
        }
        // UI: "Plans aren't available right now." + Try Again + Restore still reachable.
        // Track paywall_offerings_failed ONLY if this paywall is actually visible (isActive).
        return (.unavailable, [], [:])
    }
}
// First-version IAPs are not served to App Review until approved — the unavailable state is
// what the reviewer sees. A purchase tap with no package must
// still emit an event (paywall_unavailable), never return silently.
