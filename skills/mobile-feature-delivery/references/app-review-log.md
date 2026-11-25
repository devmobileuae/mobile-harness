# App Review — rejections, waits and what fixes them

Your own submission log (dates, builds, reviewer sessions) lives in
`local/skills/mobile-feature-delivery/app-review-log.md` — append each submission's outcome there.
This file keeps the generic lessons.

## A first submission, typically

| Step | What happens |
|---|---|
| Submit v1.0 + subscription group + subscriptions + any IAP | Manual release is safer for a first version. |
| Minutes to hours later | App Review's automated run opens the app (in analytics: device model `iPhone99,7`, ~4–13 min after each submit). Every paywall open logs `paywall_offerings_failed` — expected: first-version IAPs are not served until approved. |
| Days of "Waiting for Review" | Not silence: further automated runs may show up. After ~2 weeks, request **expedited review** once. |
| Rejection | Often several guidelines at once, reviewed on a current iPhone **and** an iPad in the iPhone-compat window. |
| Resubmit | A new review submission with every object re-added; fix all points the same day. |

## Common findings and fixes

1. **Guideline 4 (design) — "Continue button was cut off" on iPad.** An iPhone-only app
   (`TARGETED_DEVICE_FAMILY: "1"`) runs on iPad in the iPhone-compatibility window, which is shorter than
   current iPhones (≈ iPhone 8 Plus geometry). A fixed stack (illustration + question + rows + CTA) overflows.
   Fix: content in `ScrollView` + pinned CTA, or `ViewThatFits` (illustration shrinks → disappears); look for
   every other overflow while verifying. Verify on the **iPad Air 11" (M3) simulator** — the reviewer's
   exact screen. Rule: every pinned-CTA screen scrolls or degrades; check iPhone SE (3rd gen) too.
2. **2.3.2 — identical promotional images on several IAPs.** Delete them in the ASC UI.
   **The API refuses while a rejected submission is open:**
   `DELETE /v1/subscriptionImages/{id}` → 409 `STATE_ERROR.INVALID_REQUEST_ENTITY_STATE_INVALID`
   "Cannot delete image, version is not editable."; `DELETE /v1/reviewSubmissionItems/{id}` → 409
   "Item was already submitted." Do not burn time on the API route — tell the owner to use the UI.
3. **2.5.1 — HealthKit not identified in the UI.** Name it "Apple Health" wherever health data shows (a
   Settings entry, badges on health-derived items, "Verified by Apple Health"); copy says "Apple Health",
   never "HealthKit". Guard it in the repo's CLAUDE.md so it is not quietly renamed away.

### Read the reviewer's session before guessing a cause
- The review can run on **two devices in parallel** (an iPhone with purchase sheets and an iPad with a
  handful of events — enough for a Guideline 4 cut-off).
- A re-review may be a few events in seconds: they check only the cited point; other points can be
  accepted from Review Notes.
- Geography does not separate automation from a human. The model does: **`iPhone99,7` is not a retail
  device — it is Apple's automated run.**
- Filter test traffic in dashboards by `build_type is_not debug` + `$is_testflight is_not true`.

## Long waits
A later version can sit in WAITING_FOR_REVIEW for days while another app of the same account is already In
Review. After ~4 days: Contact Us (status inquiry) and/or expedited. **Do not cancel and resubmit** — it
loses the queue position. Check status read-only with `scripts/asc_status.py`.

## Other ASC traps that cost a submission
- **Upload validation demands `NSHealthUpdateUsageDescription`** even for read-only HealthKit
  (ITMS "Missing purpose string"). Say plainly that the app never writes to Apple Health.
- **The ASC submission flow adds objects one by one** — "Add for Review" on the group, each
  subscription, each IAP, and the version. The version page has no IAP picker. A new subscription
  group cannot ship without ≥1 subscription in the same draft.
- **2.1(b) "In-App Purchase products did not load" after a rejection:** rejected binaries leave attached
  subscriptions stuck in WAITING_FOR_REVIEW. Remedy: remove them from the dead submission → re-save each
  product's metadata (flips to Ready to Submit) → re-attach every one to the new submission (count them —
  the attachment silently drops) → wait ~1 h → sandbox purchase on a device → submit. Check with the
  RevenueCat MCP `get-product-store-state`.
- **Every attached IAP is on the reviewer's checklist:** a win-back offer shown only on the first paywall
  dismiss reads as "purchases did not load". Attach only visibly purchasable products to v1, or give Review
  Notes the exact path + a video.
- **ASC does NOT carry promotional text over to a new version** — copy it.
- **An App Preview takes the first slot of the Apple Search Ads ad** and can cut tap-through; drop it if
  ads matter more (`asc.py --drop-preview`).
- **A Privacy Policy URL behind a bot-challenge / attack mode** returns 403 to ASC's server-side validator
  while Safari renders it — turn the challenge off before submit.
- **No emoji in release notes**: they render as tofu boxes.
