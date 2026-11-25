# Apps note format (`local/skills/app-pulse/apps.md`)

One row per live app. Ids come from `local/apps.yaml` (`posthog_project_id`, `revenuecat_project_id`,
`firebase_project`); this note adds what the pulse needs on top.

```
Timezone: Europe/Berlin · exclude owner devices: $geoip_country_code != 'DE'

| App | PostHog project / dashboard | Store filter | Exclude | Key events | Revenue |
|---|---|---|---|---|---|
| myapp | 123456; dashboard "Overview" 987654 | `$app_namespace = 'com.example.myapp'` (debug: `com.example.myapp.debug`) | owner country; App Review installs | `Application Installed`, `app_open`, onboarding start→finish, first core action, `paywall_shown` | RevenueCat project |

Baselines (date each line; update when they shift):
- myapp (2026-01-10): installs 5–14/week; D1 17%; first core action d0 60%.

Firebase: which apps ship Crashlytics / a Remote Config `appUpdate` gate.
```

Quirks worth a line: events that lack `app_version`, events that fire per tap instead of per person,
the version from which attribution exists.
