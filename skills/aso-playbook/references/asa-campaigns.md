# Apple Search Ads: economics, structures, stop rules

Method («App-maxxing»): competitor brand keywords as `[exact]`, Search Match OFF, Manage Bids, iPhone only,
New users, campaigns split by country tier, RevenueCat AdServices attribution, kill countries < 4.5★.
Keep each app's playbook, setup checklist (field-by-field console values) and result tables in
`local/skills/aso-playbook/`.

## Economics → max CPI (do this before choosing bids)

```
max CPT = net per payer (30 d) × (install → payer) × (tap → install)
```

| App type | Prices (US) | Net per payer | Ceiling |
|---|---|---|---|
| Subscription utility | annual $39.99 (net $33.99 at 15%), weekly $6.99 + trial | ≈ $30 | 3% → max CPI $0.90; 5% → $1.50; 8% → $2.40 |
| Casual game, soft paywall | $24.99/yr + 7-day trial, $3.99/mo | ≈ $15 | stop at CPI > $0.90; expand at ≤ $0.30 |

Raising prices moves breakeven (e.g. from 12–15% install→paid to ~7%); pick decline/final offers so hardcoded
% labels stay true. Small Business Program (15%) changes every number by ±20%: check ASC → Business →
Agreements first.

## Structures

```
APP_T1_US     brand core · brand tail · category (from day 7)     bids ×1
APP_T2_EN     GB CA AU IE NZ                                       bids ×0.6
APP_T3_ROW    cheap English-speaking geos                          bids ×0.3 — only if the app sells there
APP_<CC>_GEO  one campaign per localized market, local keywords from that storefront's autocomplete
```
- Two US campaigns (brand vs generic) because budgets are per campaign: generic heads eat a shared budget by
  noon. Pausing T3 does not move money to US; a starved campaign is BID-limited, not budget-limited.
- Negatives: a brand that sounds like a common word needs that word's family as broad negatives
  (`templates/negative-keywords-example.txt` for the always-on set).
- A bulk xlsx («Campaign_And_Adgroup_MetaData») rebuilds many ad groups at once.
- An owner may choose to run attribution-blind (no AdServices); don't re-add it without asking.
- Unverified competitor brands (guessed names) get removed when challenged — verify each brand exists.

## Stop / scale rules

Day 1–2: change nothing (delivery lags). Morning of day 3: no impressions → +30% bid (not ×2–3); impressions
but no taps → rating/first screenshot problem, not bid. After a bid change: hands off 48 h.

Day 7, per campaign:

| CPI | Action |
|---|---|
| > ceiling | Pause the campaign |
| 0.33–1 × ceiling | Keep measuring to ~500 installs, watch trials, expand nothing |
| ≤ 0.33 × ceiling | Raise brand budget; add the head ad group; launch T2 in week 2 |

Per keyword (from day 8; ≥ 20–30 installs per keyword):

| Condition | Action |
|---|---|
| CPI ≤ 0.7 × ceiling | +30% bid, move to its own ad group |
| 0.7–1.2 × ceiling | leave alone |
| > 1.5 × ceiling with ≥ 50 taps | bid to ceiling or pause |
| Spend > $10–20, 0 installs | pause keyword |
| 0 impressions at ≥ 2 × recommended bid | pause: no demand |

Every 2 weeks: rating per campaign country, switch off countries < 4.5★ (stars are per storefront — cheap T3
installs never lift US stars). Say the expected CPI next to any bid change.

## Before the first dollar

1. `Purchases.shared.attribution.enableAdServicesAttributionTokenCollection()` right after
   `Purchases.configure` **in the live build**. Not retroactive.
2. RevenueCat → Integrations → Apple Search Ads ON, or RC customers carry no campaign/keyword attributes.
3. No App Preview video unless it converts: it replaces the first 3 screenshots in the ad.
4. RC product catalog linked (otherwise null durations, empty prices in the offering).
5. A new app can take up to 24 h to appear in «Choose an app».
6. Never buy reviews (5.6.3). 10–15 honest ratings from people you know is the legal accelerator.

## Driving the console (Claude in Chrome; org = `shared.apple_ads_org_id`)

- Type into «Choose an app» only after the page settles; a late re-render wipes it. Click, type, wait 2–5 s, screenshot.
- Keyword dialogs: brackets = exact. Negatives default to Exact: select all → «Broad»; don't click the «Undo» that replaces the bar.
- Search Match switches itself back ON when an ad group is edited — re-check after every edit.
- Pause: tick row → Actions → Pause. Pause one keyword: All Keywords → search → tick → Actions → Pause.
- Direct `?tab=1` URLs render blank: open the campaign from the list, click «All Keywords», wait ~15 s.
- Read rows from `document.body.innerText` (`[kw]`, Running, ad group, bid, spend, CPA, CPT, imp, taps, installs).
- The list defaults to «Last 7 days», which excludes today; a smaller number on an owner screenshot is usually a «Today» view.
- When activating campaigns, move a future start date to now in the same pass.
- Popularity without saving: Add Keywords in an UNSAVED ad group form (type a bid first), read dots, cancel.
  The dots are US popularity whatever the countries. `getRecommendedKeywordsGql` (`/booking/graphql`, vars
  `adamId`, `text`, `storefronts`) returns a 0–100 global score, floor 5; callable with fetch from the page.
- API instead of browser: `scripts/asa.py --app <key> --plan-dir <folder>` (Apple Ads Platform API
  `https://api.ads.apple.com/v1`, header `X-AP-Context: adAccountId=…`; the old Campaign Management API v5
  sunsets 2027-01-26). Needs an Apple Account with the API Account Manager role; if the owner declines that, the
  console route is the working one. `create` is always PAUSED; `enable --yes` only on the owner's explicit word.
  Plan format: `templates/asa-plan.example.json`.
