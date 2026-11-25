---
arm: both
type: llm
focus: final
weight: 2
---

The trap: the param is hand-edited. If the whole JSON is decoded into one typed data class inside one try/runCatching, a single wrongly typed value (e.g. QA types `"latestVersion": 43` as an unquoted number into a String field, or a stray key with the wrong type) throws, and the one global fallback is an EMPTY allow-list — the feature silently switches off for everyone.

PASS if the code isolates failures per block: the raw string is parsed to a `JsonObject` / `JsonElement` first and `allowedIds` and `appUpdate` are read or decoded separately, each with its own fallback (or the version fields are read tolerantly, accepting both string and number), so a broken `appUpdate` value cannot empty `allowedIds` and vice versa.

FAIL if the whole param is decoded with a single `decodeFromString<SomeConfig>(...)` (or equivalent) whose exception returns one global default for both the allow-list and the update gate.

Quote the decode call(s) that decide this.
