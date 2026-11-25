<!-- Template: hypothesis card. Fill it BEFORE building and show it to the owner in their language, 5-7 lines.
     Past cards for your apps: local/skills/metric-iteration/. -->
```
App / build:  <app 1.2.2 (11) on branch release-1-2-2 from release-1-2-1>
Change:       <one sentence; if you need "and", it is two cards>
Metric:       <event-based, with the exact events and denominator, e.g.
               users with level_completed on install day (local tz) ÷ users with onboarding_completed>
Baseline:     <value> (n=<people>, <date range>, query <Q6 in references/hogql.md>, filters: store namespace, owner country out)
Expect:       <direction and size, e.g. 8/15 → 11/15>
Split:        <before/after | hash(install_id) % 2 at first launch | feature flag, if the app reads flags>
Read on:      <date> or n ≥ <N per arm from the sample-size table in SKILL.md>
Guardrails:   <onboarding completion, D1, paywall views…>
Kill if:      <threshold>
Confounds:    <ads on/off, new geo campaigns, another change in the same build, App Review devices>
```
