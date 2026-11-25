# HogQL for the pulse

Replace `{ns}` with the store namespace/bundle and run per project after `switch-project`.
Dates are days in the owner's timezone `{tz}`; `{owner_country}` excludes the owner's devices.

## Daily counts of key events, last 29 days (yesterday + 4 same weekdays)

```sql
SELECT toDate(toTimeZone(timestamp, '{tz}')) AS day,
       event,
       count() AS events,
       count(DISTINCT person_id) AS people
FROM events
WHERE timestamp >= now() - INTERVAL 29 DAY
  AND event IN ('Application Installed', 'app_open', 'onboarding_completed', 'paywall_shown', '$exception')
  AND properties.$app_namespace = '{ns}'
  AND properties.$geoip_country_code != '{owner_country}'
GROUP BY day, event
ORDER BY day, event
```

Use the weekday of yesterday and the same weekday 7/14/21/28 days earlier for the median.

## Day-0 first core action for yesterday's installs

```sql
WITH installs AS (
  SELECT person_id, min(timestamp) AS t0
  FROM events
  WHERE event = 'Application Installed'
    AND properties.$app_namespace = '{ns}'
    AND properties.$geoip_country_code != '{owner_country}'
    AND toDate(toTimeZone(timestamp, '{tz}')) = yesterday()
  GROUP BY person_id
)
SELECT count() AS installs,
       countIf(person_id IN (
         SELECT person_id FROM events
         WHERE event = '{core_event}'            -- e.g. task_completed, pack_completed
           AND timestamp >= now() - INTERVAL 2 DAY
       )) AS did_core_action
FROM installs
```

## Release check: app_version share yesterday

```sql
SELECT properties.$app_version AS v, count(DISTINCT person_id) AS people
FROM events
WHERE event = 'app_open'
  AND toDate(toTimeZone(timestamp, '{tz}')) = yesterday()
  AND properties.$geoip_country_code != '{owner_country}'
GROUP BY v ORDER BY people DESC
```

Event names differ per app; confirm in `local/skills/app-pulse/apps.md` or with `read-data-schema` before
the first run on a new app. If `Application Installed` has no app_version, filter it by
namespace only.
