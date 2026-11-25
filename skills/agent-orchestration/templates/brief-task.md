<!--
A wave brief for parallel subagents (example: a visual re-skin of a habit tracker, 8 screen tasks on disjoint
files under a deadline). Why this shape: every agent that stalls still leaves work the lead can pick up, because
each brief names its files, its build command, its grep guards and its screenshot recipe. The matching report
format is templates/report.md.
How to use: keep the shape, replace the content. Two files per wave:
  <ledger-dir>/common.md   — read by every agent of the wave (constraints, commands, recipes, rules 1–6)
  <ledger-dir>/task-N-brief.md — 5–12 lines: Files (touch only these) + checklist + screenshots to take
Dispatch prompt (one line): "Read <ledger-dir>/common.md, then task-N-brief.md. Write task-N-report.md. Do NOT use the Agent tool."
-->

# ===== common.md =====

# Wave B — common brief (read this first, then your task brief)

## Global Constraints
- Spec: `docs/superpowers/specs/<date>-reskin-design.md` — ground truth; the token and mapping tables below are copied from it.
- Repo root: `<absolute repo path>`.
- Build (app): `xcodebuild -project HabitApp.xcodeproj -scheme HabitApp -destination 'platform=iOS Simulator,id=<SIM_UDID>' -derivedDataPath build/dd-reskin build 2>&1 | grep -E "error:|BUILD (SUCCEEDED|FAILED)"`
- Tests: `cd HabitKit && swift test 2>&1 | tail -3` — must stay at <N> passed.
- Simulator: <device>, <iOS version>, UDID `<SIM_UDID>`. Bundle id `<bundle_id from local/apps.yaml>`.
- Screenshot recipe (every UI task ends with it):
  ```bash
  SIM=<SIM_UDID>; APP=<bundle_id>
  xcrun simctl boot $SIM 2>/dev/null; xcrun simctl install $SIM build/dd-reskin/Build/Products/Debug-iphonesimulator/HabitApp.app
  xcrun simctl terminate $SIM $APP 2>/dev/null
  xcrun simctl launch $SIM $APP -SKIP_ONBOARDING -DEBUG_PRO -OPEN_TAB today
  sleep 3; mkdir -p docs/screenshots/<date>-reskin; xcrun simctl io $SIM screenshot docs/screenshots/<date>-reskin/today.png
  ```
- Guards (grep must return 0 in your files): no `LinearGradient|RadialGradient|AngularGradient`, no materials outside `GlassSurface.swift`, no `.custom(` fonts, no `design: .serif`.
- Copy: do not rewrite product copy — this is a visual change.
- Do not touch `HabitKit`, `Models/`, `Services/`, `ViewModels/` (except where a task names a file explicitly).

## Token reference / recipes
(the table and code snippets the agent must use verbatim — copied from the spec, not "see spec")

Common instructions for every task of this wave (the subagent prompt must include them):

1. Read the spec §Tokens, §Components, then the token reference + recipes above, then the design-system files `DSCell.swift`, `DSButton.swift`, `DSTag.swift`, `Typography.swift` (skim the public shapes).
2. In your files: replace `GlassCard {}` with `.dsCard()` on a padded `VStack`; legacy buttons with `Button {}.buttonStyle(.ds(.primary, .large, fillsWidth: true))`; `DSFont.sans(n, weight:)` with the nearest `DSType` (17→`body17R/M`, 15→`body15R/M`, 13→`body13R/M`, 26–32→`titleH3B`/`titleH2B`); numbers with `.dsText(DSType.number)` + `.monospacedDigit()`; list-like rows with `DSCell`; chips with `DSTag`; empty states with `DSEmptyState`.
3. Delete every `Gradient`, every `.blur` glow, every `.shadow(` not from `ds*Shadow()`, every material.
4. Keep every string, every action, every analytics call, every navigation destination exactly as is.
5. Build the app (command in Global Constraints). Fix only errors in your files. Then screenshot the surfaces listed in your task. Then run the tests.
6. Report: what changed per file, anything you could not map to a component (flag it, do not invent), `git diff --stat -- <your files>`, screenshot paths. No commits.


# ===== task-4-brief.md =====

### Task 4: Today

**Files:** `HabitApp/Views/Today/TodayView.swift`, `HabitApp/Views/Today/ShareCardView.swift`, `HabitApp/Views/Today/WidgetPromoCard.swift`

- [ ] Hero: streak number → `Text(count).dsText(DSType.numberLarge).monospacedDigit().contentTransition(.numericText())`; the "days" suffix `.dsText(DSType.body17R).foregroundStyle(DSColor.mutedInk)`; hero card is a plain `.dsCard()`.
- [ ] Habit rows → each a `DSCell(title:, rightTitle: "3/5")` with a `DSProgressMeter` trailing, inside one `dsSection("Today")`.
- [ ] Gear → `.toolbar { ToolbarItem(placement: .topBarTrailing) { Button { … } label: { Image(systemName: "gearshape") } } }`, tint ink.
- [ ] `ShareCardView`: white card, ink type, accent only on the ring; remove background glow.
- [ ] `WidgetPromoCard`: `.dsCard()`, steps as `DSCell` rows.
- [ ] Screenshots: `today` (free: launch without `-DEBUG_PRO`), `today-pro`.
