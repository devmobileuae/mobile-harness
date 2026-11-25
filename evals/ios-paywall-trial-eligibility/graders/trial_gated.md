---
arm: both
type: llm
focus: final
weight: 2
---

The task: a paywall must say "Start N-day free trial" only when a trial really applies. App Store Guideline 3.1.2 rejects promising a trial to a user who already used it, so the trial wording must depend on BOTH the product having a free-trial intro offer AND this user being eligible for it.

PASS if the final code shows the trial wording (button and the "Free for N days" line) only when both hold:
(a) the product's intro discount is a free trial (e.g. `introductoryDiscount?.paymentMode == .freeTrial`), and
(b) a per-user eligibility check returned eligible (e.g. `Purchases.shared.checkTrialOrIntroDiscountEligibility(product:)` == `.eligible`, or StoreKit 2 `subscription.isEligibleForIntroOffer`),
and otherwise falls back to the "Subscribe for {price}/year" wording.

FAIL if the trial wording is shown whenever `introductoryDiscount` exists (or whenever its payment mode is free trial) without a per-user eligibility check, or if the eligibility check is only mentioned in prose and not used in the code.

Quote the condition that decides the trial wording.
