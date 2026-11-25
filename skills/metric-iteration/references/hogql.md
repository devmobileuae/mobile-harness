# HogQL library for metric iteration

How to run: PostHog MCP `exec "switch-project <posthog_project_id>"`, then
`exec 'call execute-sql {"query": "<one line of SQL>"}'`. Without the MCP: `scripts/hogql.py --app <key> file.sql`.

Placeholders: `{ns}` store bundle / `$app_namespace`; `{oc}` the owner's country code; `{tz}` the owner's timezone
(e.g. `Europe/Berlin`); `{start}` launch or window start (`2026-01-10 00:00:00`); `{core}` the core-action event
(e.g. `level_completed`); `{open}` the item-opened event (e.g. `level_opened`); `{item}` its id property
(e.g. `level_id`). Save each app's filled-in queries and results in `local/skills/metric-iteration/`.

Real-user filter every query uses:
```sql
WHERE properties.$app_namespace = '{ns}'                  -- store build, not the debug bundle
  AND coalesce(properties.$geoip_country_code, '') != '{oc}'  -- owner's own devices
-- installs: event = 'Application Installed' (often carries NO app_version/build_type super-props)
-- days: toDate(toTimeZone(timestamp, '{tz}'))             -- the owner reads "today" in local time
```
Apple's review device (US, Cupertino / no city, tz America/Los_Angeles, model like iPhone99,7, installs minutes
after each submission, cancels purchases in ~30 ms): drop it by hand from per-user tables.

### Q1 · Event taxonomy (first step of every new read; names drift between versions)
```sql
SELECT event, count() AS n, uniq(person_id) AS users, min(timestamp) AS first_seen
FROM events
WHERE properties.$app_namespace = '{ns}' AND coalesce(properties.$geoip_country_code, '') != '{oc}'
  AND timestamp >= toDateTime('{start}')
GROUP BY event ORDER BY n DESC LIMIT 100
```

### Q2 · Who came today, one row per person
```sql
WITH nu AS (
  SELECT person_id AS pid, min(timestamp) AS t0, any(properties.$geoip_country_code) AS cc
  FROM events
  WHERE event = 'Application Installed' AND properties.$app_namespace = '{ns}'
    AND toDate(toTimeZone(timestamp,'{tz}')) = today()
    AND coalesce(properties.$geoip_country_code,'') != '{oc}'
  GROUP BY pid)
SELECT any(nu.cc) cc, formatDateTime(toTimeZone(min(nu.t0),'{tz}'),'%H:%i') inst,
  any(e.properties.$app_version) ver, any(e.properties.$locale) loc,
  dateDiff('minute', min(e.timestamp), max(e.timestamp)) mins,
  countIf(e.event='onboarding_completed') onb, countIf(e.event='{open}') opened,
  countIf(e.event='{core}') done, countIf(e.event='paywall_shown') pw,
  countIf(e.event ILIKE '%purchase%' OR e.event ILIKE '%trial%') buy,
  countIf(e.event ILIKE '%review%') rate,
  groupUniqArrayIf(e.properties.{item}, e.event IN ('{open}','{core}')) items
FROM events e INNER JOIN nu ON e.person_id = nu.pid
WHERE e.timestamp > now() - INTERVAL 2 DAY
GROUP BY e.person_id ORDER BY inst
```

### Q3 · Depth of first engagement — finds the leak
```sql
WITH u AS (
  SELECT person_id, countIf(event = '{open}') AS opened, countIf(event = '{core}') AS done,
    dateDiff('second', min(timestamp), max(timestamp)) AS span_s, argMax(event, timestamp) AS last_event
  FROM events
  WHERE properties.$app_namespace = '{ns}' AND coalesce(properties.$geoip_country_code, '') != '{oc}'
    AND timestamp >= toDateTime('{start}')
  GROUP BY person_id HAVING countIf(event = 'onboarding_completed') > 0)
SELECT multiIf(done > 0, '2 completed', opened > 0, '1 opened, not completed', '0 never opened') AS segment,
  count() AS users, round(median(span_s) / 60, 1) AS median_minutes, topK(4)(last_event) AS top_last_events
FROM u GROUP BY segment ORDER BY segment
```
Add app-specific intermediate counts (rewards won, misses, hints) as extra segments.

### Q4 · Per-item open → complete
```sql
SELECT toString(properties.{item}) AS item,
  uniqIf(person_id, event = '{open}') AS opened_users, uniqIf(person_id, event = '{core}') AS completed_users,
  round(avgIf(toFloatOrNull(toString(properties.duration)), event = '{core}'), 0) AS avg_duration_s
FROM events
WHERE properties.$app_namespace = '{ns}' AND coalesce(properties.$geoip_country_code, '') != '{oc}'
  AND timestamp >= toDateTime('{start}') AND event IN ('{open}', '{core}')
GROUP BY item ORDER BY opened_users DESC LIMIT 20
```
Use `toFloatOrNull(toString(...))`: `toFloat(properties.x)` fails on JSON properties.

### Q5 · Which item is opened first, and from where
```sql
WITH s AS (
  SELECT person_id, timestamp, event, toString(properties.{item}) AS item,
    lagInFrame(concat(event, ':', coalesce(toString(properties.section), toString(properties.$screen_name), '')))
      OVER (PARTITION BY person_id ORDER BY timestamp ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS prev
  FROM events
  WHERE properties.$app_namespace = '{ns}' AND coalesce(properties.$geoip_country_code, '') != '{oc}'
    AND event NOT IN ('Application Backgrounded', 'Application Opened')),
firsts AS (SELECT person_id, argMin(item, timestamp) AS first_item, argMin(prev, timestamp) AS came_from
           FROM s WHERE event = '{open}' GROUP BY person_id)
SELECT first_item, came_from, count() AS users FROM firsts GROUP BY first_item, came_from ORDER BY users DESC LIMIT 15
```

### Q6 · Does the core action on day 0 predict return?
```sql
WITH u AS (
  SELECT person_id, toDate(minIf(timestamp, event = 'Application Installed')) AS d0,
    countIf(event = 'Application Installed') > 0 AS has_inst,
    groupUniqArray(toDate(timestamp)) AS days, minIf(toDate(timestamp), event = '{core}') AS first_done
  FROM events
  WHERE properties.$app_namespace = '{ns}' AND coalesce(properties.$geoip_country_code, '') != '{oc}'
    AND timestamp >= toDateTime('{start}')
  GROUP BY person_id HAVING countIf(event = 'onboarding_completed') > 0)
SELECT if(first_done = d0, 'core action on day 0', 'did not') AS day0, count() AS users,
  countIf(arrayExists(x -> x > d0, days)) AS came_back_later
FROM u WHERE has_inst AND d0 <= today() - 2      -- only cohorts that had a chance to return
GROUP BY day0
```

### Q7 · Install-day cohorts D1/D2/D3/D7+
```sql
WITH a AS (SELECT person_id, toDate(toTimeZone(timestamp,'{tz}')) AS d
           FROM events WHERE timestamp > toDateTime('{start}','{tz}')
             AND properties.$geoip_country_code != '{oc}' GROUP BY person_id, d),
     f AS (SELECT person_id, min(d) AS d0 FROM a GROUP BY person_id)
SELECT f.d0 AS cohort, uniq(f.person_id) AS users,
  uniqIf(a.person_id, a.d = f.d0 + 1) AS d1, uniqIf(a.person_id, a.d = f.d0 + 2) AS d2,
  uniqIf(a.person_id, a.d = f.d0 + 3) AS d3, uniqIf(a.person_id, a.d >= f.d0 + 7) AS d7plus,
  uniqIf(a.person_id, a.d > f.d0) AS ever_back
FROM f JOIN a ON a.person_id = f.person_id GROUP BY cohort ORDER BY cohort
```

### Q8 · Returners vs non-returners, day-0 behaviour
```sql
WITH a AS (SELECT person_id, toDate(toTimeZone(timestamp,'{tz}')) AS d
           FROM events WHERE timestamp > toDateTime('{start}','{tz}')
             AND properties.$geoip_country_code != '{oc}' GROUP BY person_id, d),
     f AS (SELECT person_id, min(d) AS d0, max(d) AS dl FROM a GROUP BY person_id HAVING d0 <= today() - 3),
     day0 AS (SELECT e.person_id AS pid, if(any(f.dl) > any(f.d0), 1, 0) AS back,
       dateDiff('second', min(e.timestamp), max(e.timestamp))/60 AS mins,
       countIf(e.event='{core}') AS done, uniq(e.$session_id) AS sessions
     FROM events e JOIN f ON e.person_id=f.person_id
     WHERE toDate(toTimeZone(e.timestamp,'{tz}')) = f.d0 GROUP BY e.person_id)
SELECT back AS returned, count() AS people, round(median(mins),1) AS med_min,
  round(avg(done>0),2) AS share_core, round(avg(sessions),1) AS avg_sessions
FROM day0 GROUP BY returned
```
Read notification opt-in separately from the permission-result event on day 0.

### Q8b · Reach of candidate moments before changing a trigger
```sql
SELECT count() AS new_users, countIf(done >= 1) AS did_core_once, countIf(done >= 2) AS did_core_twice,
  countIf(days >= 2 AND done >= 1) AS returned_and_did_core
FROM (SELECT person_id, countIf(event = '{core}') AS done,
        count(DISTINCT toDate(toTimeZone(timestamp, '{tz}'))) AS days
      FROM events WHERE timestamp >= now() - INTERVAL 14 DAY AND properties.$geoip_country_code != '{oc}'
      GROUP BY person_id HAVING sum(event = 'Application Installed') > 0)
```
Count reach for each candidate threshold before loosening a rating or paywall trigger.

### Q9 · First hour after install, by version
```sql
WITH inst AS (
  SELECT person_id, min(timestamp) AS t_inst, argMin(properties.$app_version, timestamp) AS ver
  FROM events WHERE event = 'Application Installed' AND timestamp >= now() - INTERVAL 14 DAY
    AND properties.$geoip_country_code != '{oc}'
  GROUP BY person_id)
SELECT inst.ver AS ver, count() AS n, countIf(done > 0) AS did_core, countIf(opened > 0) AS opened,
  round(median(mins),1) AS med_minutes, countIf(mins >= 10) AS stayed_10m
FROM (SELECT e.person_id AS pid, countIf(e.event = '{core}') AS done, countIf(e.event = '{open}') AS opened,
        dateDiff('second', min(e.timestamp), max(e.timestamp)) / 60 AS mins
      FROM events e INNER JOIN inst ON e.person_id = inst.person_id
      WHERE e.timestamp >= now() - INTERVAL 14 DAY AND e.timestamp <= inst.t_inst + INTERVAL 1 HOUR
      GROUP BY e.person_id) AS s
INNER JOIN inst ON s.pid = inst.person_id
GROUP BY inst.ver
```

### Q10 · Release before/after on the activation event, and splitting spikes
```sql
WITH s AS (SELECT person_id AS pid, min(timestamp) AS t0 FROM events
           WHERE event='onboarding_started' AND timestamp > now() - INTERVAL 75 DAY GROUP BY pid)
SELECT if(t0 >= toDateTime('{release_time}'), 'new', 'before') AS ver, count() AS started,
  countIf(pid IN (SELECT person_id FROM events WHERE event='onboarding_completed')) AS completed,
  countIf(pid IN (SELECT person_id FROM events WHERE event='{core}')) AS did_core,
  countIf(pid IN (SELECT person_id FROM events WHERE event='paywall_shown')) AS saw_paywall
FROM s GROUP BY ver
```
Then list the paywall triggers new users hit (`JSONExtractString(properties,'trigger')`). Split every install spike
by `build_type` and country before believing it: owner test devices and an ads launch day look like growth.

### Q11 · Day-N retention with complete-day eligibility
```sql
SELECT toStartOfMonth(d0) AS cohort_month, count() AS new_users,
  countIf(d0 <= today() - 2) AS el_d1, countIf(d0 <= today() - 2 AND has(days, addDays(d0, 1))) AS d1,
  countIf(d0 <= today() - 8) AS el_d7, countIf(d0 <= today() - 8 AND has(days, addDays(d0, 7))) AS d7,
  countIf(d0 <= today() - 31) AS el_d30, countIf(d0 <= today() - 31 AND has(days, addDays(d0, 30))) AS d30
FROM (SELECT person_id, min(toDate(timestamp)) AS d0, groupUniqArray(toDate(timestamp)) AS days
      FROM events
      WHERE timestamp >= toDateTime('{start}') AND event IN ('Application Opened', 'app_open')
        AND coalesce(toString(properties.$is_emulator), '') != 'true'
        AND coalesce(toString(properties.$is_testflight), '') != 'true'
      GROUP BY person_id)
GROUP BY cohort_month ORDER BY cohort_month
```
The eligibility column (`el_dN`) is the point: never divide day-N returners by a cohort that has not lived N days.
Add a split by first build or by an onboarding choice (`argMaxIf(properties.choice, timestamp, event = '...')`)
to see which release or choice moved D1.
