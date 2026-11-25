---
arm: both
type: llm
weight: 3
---

PASS if the proposed model makes the new attribute optional (e.g. `var priority: Int?` or an optional stored value with a computed non-optional accessor) OR adds a real SchemaMigrationPlan, AND the reply warns that a Swift default value alone does not migrate existing stores / can crash on real installs.
FAIL if it simply adds `var priority: Int = 0` as a non-optional stored property without a migration plan.
