# Risk table — paste into the plan before the first line of code

Format from `~/.claude/skills/ios-app-bootstrap/templates/CLAUDE.md` § "Risk table and testing standard",
filled with an example (a habit tracker release: a stats radar fix + a muted header redesign).

| Surface | Tier | Why | Proof |
| --- | --- | --- | --- |
| `HistoryStats.categoryRates` (finished ÷ dealt per category) | core | radar scale was relative → every even category hit the rim ("looks maxed") | test first, fails before fix; full suite green |
| new stored attribute on `@Model` | core | non-optional with a default crashes real upgrade installs | optional + computed accessor + nil-row test; upgrade install |
| `ChallengeService.settle` callers | core | two callers can race and pay out twice | one caller only; test |
| `ReviewAskPolicy` | core | HIG + guardrails (never onboarding, never after paywall, never on a bad day) | pinned tests |
| `TodayHeader` muted backdrop | ui | visual only | one smoke test + sim screenshot vs the design frame |
| `FilterChip` 40 pt / r12 | ui | visual only | screenshot |

Rules:
- core = TDD; a test that passes without the change is worse than none. Confirm it fails first.
- ui = exactly one smoke test per screen + eyes on the simulator.
- More than half the rows in core = flat rigor sneaking back; re-argue each row.
- Gates and destructive writes read authoritative state; add a test that does NOT call `load()` first.
