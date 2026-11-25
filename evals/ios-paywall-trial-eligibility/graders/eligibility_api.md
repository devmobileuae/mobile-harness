---
arm: both
type: regex
pattern: 'checkTrialOrIntroDiscountEligibility|isEligibleForIntroOffer'
target: last_message
match: contains
---
The answer's code calls a per-user intro-offer eligibility API (RevenueCat or StoreKit 2).
