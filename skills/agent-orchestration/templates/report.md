<!--
Template for the report file every subagent writes BEFORE replying, matching the "## Report" contract in
templates/implementer-rules.md.
Why a FILE and not just the reply: on a long day up to half of the agents stall ("no progress for 600s") and reply
nothing; the ones that had been writing their report as they went are picked up in minutes.
Rule for the agent: create the file after the FIRST edited file, append after each next one, finish it last.
Path: <ledger-dir>/task-<N>-report.md (SDD: .superpowers/sdd/<plan>/; harness workflows: docs/agent-reports/<slice>.md)
-->

# Task <N> — <title> · report

**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
<one line: build result, test count — e.g. "App build SUCCEEDED, widgets untouched, swift test 177/177 passed. No commits.">

## Per-file changes
### `<exact/path/File.swift>` (rewritten | edited | new)
- <what changed, with the before → after names: `ScreenGlow()` → `DSColor.paper.ignoresSafeArea()`>
- <every deliberate copy/behaviour change called out as such: "the only copy change in the task">
- "Every string, action, analytics call and navigation destination is byte-identical" — or list what is not.

## Verification (commands + their real output, not adjectives)
- Build: `<command>` → `** BUILD SUCCEEDED **`
- Tests: `<command>` → `Test run with 177 tests in 20 suites passed`
- Guards: `grep -nE "<forbidden patterns>" <my files>` → 0 hits (or: the 4 remaining hits are intentional because …)
- Screenshots: `docs/screenshots/<date>-<topic>/<name>.png` (one per surface named in the brief)
- TDD tasks: RED command + failing output and why expected; GREEN command + passing output

## Deviations from the brief
- <exact before/after> | none

## Not verified (never rounded up to done)
- <e.g. "pattern cards not screenshot-verified with data (no seed)">

## Notes / flags for the lead
- <things outside my files I noticed but did not touch; questions only the owner can answer>

---
Reply to the lead (≤ 12 lines): Status · one-line test summary · deviations/concerns one line each · report path.
