# Pre-submission E2E scope — format

Use this shape for any release that touches onboarding, paywall, permissions or purchases. Write it into
the app repo (`E2E-TEST-SCOPE.md`), run what the simulator can, and mark the rest DEFERRED with the
environment it needs. Your filled scopes: `local/skills/mobile-feature-delivery/`.

**Priority:** P0 = blocks submission / revenue · P1 = fix before ship · P2 = polish.
**Env:** SIM · DEV (Debug, RevenueCat Test Store key) · SBX (TestFlight + Sandbox Apple ID, prod key) · DEVICE.

## Sections (keep the order — P0 first)
1. **Build & config integrity (P0)** — build number bumped; purpose strings present in the BUILT
   `.app/Info.plist` (`NSFaceIDUsageDescription`, `NSHealthShareUsageDescription`,
   `NSHealthUpdateUsageDescription`); production RC key (`appl_…`, not `test_`); entitlements present
   in the built entitlements; no ATT/tracking SDKs vs the privacy label.
2. **Onboarding (P1)** — fresh install to the main screen; each permission sheet appears with our string;
   deny falls back gracefully.
3. **Core app (P1)** — each tab renders; writes persist; app lock (Face ID) if any; share cards leak nothing private.
4. **Paywall + offers + legal (P0, review-critical)** — renewal terms visible; Terms / Privacy open
   live pages (200, not 403); each offer step shows price + legal footer; only ONE plan shows a trial;
   Restore with nothing → "Nothing to restore".
5. **Purchase lifecycle — SANDBOX (P0)** — buy each product; restore after reinstall; cancel → expiry
   revokes; each purchase visible in RevenueCat; gating unlocks instantly. **Never on the simulator.**
6. **Deep links & widgets (P2).**
7. **Privacy claims audit (P1)** — every claim in ASO/site/policy matches the binary.
8. **ASC submission gate (P0)** — checklist: subscriptions localized + priced + review screenshot,
   intro offer, group localized, first subscription attached, Privacy URL returns 200, App Privacy
   questionnaire, age rating, screenshots, Review Notes with the exact path to every IAP.

## Results table (what "done" looks like)
| ID | Result | Notes |
|----|--------|-------|
| B3 | ✅ PASS | `RevenueCatAPIKey=appl_…` in binary; confirmed at runtime — the paywall showed the trial from the production offering |
| C3 | ✅ PASS | Face ID ON → background/reopen → "Unlock with Face ID" → Matching Face unlocks |
| PW3 | ✅ PASS | Terms opens the real page in Safari (bot challenge transparent to real browsers) |
| S1–S8 | DEFERRED | TestFlight + Sandbox Apple ID |

Then "Known risks to close first" — e.g. Privacy URL 403 to ASC's server-side validator under a bot
challenge even though Safari renders it.

## Privacy-claims debt
Shipping an analytics SDK while the policy still says "No third-party analytics or tracking SDKs" and the
site says "never leaves your phone / 100% on-device" is exactly what earns 1-star waves in sensitive
categories (health, finance). Close it by rewriting policy, site and the in-app privacy sheet together,
and flag the App Store privacy label to the owner. **Rule: adding an SDK or a server write is a release
item for policy + label + marketing claims, not just code.**
