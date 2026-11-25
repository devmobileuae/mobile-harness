---
name: ios-paywall-trial-eligibility
tags: [ios-engineering]
runs: 3
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our habit tracker (SwiftUI, RevenueCat 5, already on the App Store) has a paywall with one annual package. In App Store Connect the annual product now has a 7-day free trial intro offer. Make the button say "Start 7-day free trial" when there is a trial, and "Subscribe for {price}/year" otherwise, plus a small line under it: "Free for 7 days, then {price}/year". Take the trial length from the product, don't hardcode 7.

Current view:

```swift
import SwiftUI
import RevenueCat

struct PaywallView: View {
    @State private var annual: Package?
    @State private var purchasing = false

    var body: some View {
        VStack(spacing: 16) {
            Text("Unlock all habits").font(.title.bold())
            if let annual {
                Button("Subscribe for \(annual.storeProduct.localizedPriceString)/year") {
                    Task { await buy(annual) }
                }
                .buttonStyle(.borderedProminent)
                .disabled(purchasing)
            } else {
                ProgressView()
            }
        }
        .task { await load() }
    }

    private func load() async {
        annual = try? await Purchases.shared.offerings().current?.annual
    }

    private func buy(_ pkg: Package) async {
        purchasing = true
        defer { purchasing = false }
        _ = try? await Purchases.shared.purchase(package: pkg)
    }
}
```

Just give me the updated code.
