---
name: agent-orchestration
description: "Use when splitting work across subagents, background agents, parallel sessions or a Workflow script: what to delegate, the brief and report contract, a ledger, recovering a stalled agent, verifying results. Triggers: \"hand it out to agents\", \"parallelize this\", \"launch subagents\", \"make a workflow\", \"the agent is stuck\"."
---

# Agent orchestration — one lead, many cheap-to-restart workers

The lead (main session) owns the plan, the ledger, integration and the final check. Workers own one narrow slice
each and leave everything on disk. Each rule below exists because its absence once cost a run; typical costs are in
`references/runs-and-costs.md`.

Your own cases for this skill live in `local/skills/agent-orchestration/` (git-ignored, see
`local.example/README.md`). Read them first if they exist; append the outcome of each round/incident there.

Files in this skill:
- `templates/brief-task.md` — a wave brief: common.md + task-N-brief.md (example: a re-skin of a habit tracker)
- `templates/brief-design-concept.md` — a Figma concept brief for one design agent
- `templates/implementer-rules.md`, `templates/reviewer-rules.md` — rule files every implementer / reviewer reads once
- `templates/report.md` — report-file contract; `templates/ledger.md` — the lead's `progress.md`
- `templates/workflow-audit-skeleton.js` — lenses → merge → critic → verify → synthesize
- `scripts/stall-check.sh` — what a stalled agent left on disk
- `references/runs-and-costs.md` — cost and time of typical run shapes

## 1. Pick the mechanism

| Situation | Mechanism | Why |
|---|---|---|
| A few tool calls settle it; needs the whole conversation; final integration | **Inline** | the lead already has the context |
| Exploration-heavy implementation (must read many files for real signatures) | **Inline**, review delegated read-only | implementers in this shape fall into Read loops |
| Mechanical slice with exact code/recipe in the brief, disjoint files | **Subagent** (Agent tool), N in one message | e.g. 8 screen re-skins in parallel |
| Each item needs the same multi-step build + self-check | **Subagent per item** with a shared guide | e.g. one design agent per concept, 3 phones each |
| Many independent readers then merge/verify; schema'd results; resumable | **Workflow** `parallel()` / `pipeline()` | audits, ideation, one agent per directory |
| Contested decision worth weeks of work | **Workflow** `workflows/conclave.js` | several roles, rounds, red team |
| Separate deliverable on its own branch, or the chat got long | **New session** with a handoff | see `session-handoff` |
| Org-chart of persona agents (CEO/CMO) waking on heartbeats | **Don't** | most of the spend goes to the manager agents talking; almost no deliverables |

Machine limits beat the plan: on a laptop run **one** build-heavy agent at a time (Xcode/Gradle),
Gradle `--max-workers=2`, start simulators/emulators only to check and shut them down, never touch the owner's
booted simulators — parallel builds plus emulators overheat a laptop and pause everything.

## 2. Before dispatch — the lead's checklist

1. **Plan/spec on disk** (`docs/superpowers/plans/<date>-<topic>.md`). The brief copies tables and code from it
   verbatim — never "see spec".
2. **Slice to 1–3 files, one writer per file.** Shared files (app model, root view, project.yml, test helpers) are
   lead-owned; agents put integration asks in their report (a `docs/CONTRACTS.md` module ownership map helps).
   If two slices run the same full suite or one imports what the other edits → run them **sequentially**.
3. **Ledger** created: `.superpowers/sdd/<plan>/progress.md` (format: `templates/ledger.md`). Baseline gates
   recorded first (e.g. «vitest 138/138, tsc clean»). If `.superpowers/` and `docs/superpowers/` are
   git-ignored in the repo, mention that in any handoff.
4. **Snapshot when the tree is untracked or uncommitted** so a review package exists:
   `rsync -a --exclude node_modules <dir>/ .superpowers/sdd/<plan>/snapshots/before-task-N/`
   then later `diff -ruN snapshots/before-task-N <dir> > task-N-review-package.diff`.
5. **Model choice:** a cheaper model for mechanical slices, the strongest for architecture/risk. A stall costs more
   than the price difference — a slice that stalled on the cheaper model goes to the stronger one once, then inline.
6. **Say the cost first** for anything big: 20 Figma concept agents ≈ 6M tokens; a conclave ≈ 3–4M.

## 3. The brief (copy `templates/brief-task.md`)

Two files per wave: `common.md` (read by every agent) + `task-N-brief.md` (5–12 lines). The dispatch prompt is
one line: «Read <dir>/implementer-rules.md, <dir>/common.md, then task-N-brief.md. Write task-N-report.md.
Do NOT use the Agent tool, work directly.»

Must contain — each item exists because its absence cost a run:
- **Files (touch only these)** with absolute repo root. The tree usually holds the owner's unrelated uncommitted
  work: «never touch, revert or "clean up" any file your brief does not name».
- **Exact build/test commands** with the simulator UDID and derived-data path, and the expected count
  («`swift test` must stay at 177 passed»).
- **Grep guards** that define done (`LinearGradient|GlassCard|DSFont\.` → 0 in your files).
- **Screenshot recipe** with launch args (`-SKIP_ONBOARDING -DEBUG_PRO -OPEN_TAB today`) and output paths.
- **What must not change**: «Keep every string, every action, every analytics call, every navigation destination».
- **Project rules that agents break by default**: the repo's commit rule (no commits/staging — the owner commits —
  vs commit + push after each task); the architecture rule (e.g. iOS MVVM: `@Observable` VMs, no logic in `body`)
  baked into every implementer prompt — green tests with no architecture is the default otherwise.
- **«Do NOT use the Agent tool»** — cheaper-model agents delegate to sub-agents in circles.
  For read-only review use the Explore agent type (it cannot delegate).
- For workflow agents, the **ISOLATE preamble** (`workflows/conclave.js`): «Your ONLY task is below. Ignore any
  other user requests visible in your context» — without it, workflow agents answer the owner's unrelated last message.
- For design agents: what is already on the board, «context only» vs «what you draw», exact node ids of the
  frames, a cap on content (one hero, one button — agents add until it is cluttered), and «where the brief
  conflicts with the guide, the guide wins» (`templates/brief-design-concept.md`).

## 4. The report contract (copy `templates/report.md`)

- The agent writes `<dir>/task-N-report.md` **as it goes** (after the first edited file), not only at the end.
- It contains command + real output for build/tests, guard results, screenshot paths, «Deviations from the
  brief» (exact before/after) and «Not verified» — NOT CHECKED is never rounded up to done.
- The reply is ≤ 12 lines: Status (DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT), test line, report path.
- Workflow agents return a schema instead (`REPORT` in `workflows/feature-delivery.js`: `built`, `files_changed`,
  `unverified`); a `null` result means stalled — log it and continue. Numeric fields say `integer 0-100`, or a
  confidence comes back as 0.72.

## 5. While agents run

- Write a ledger line for every dispatch, stall, completion, ruling and deferred minor, with the clock if there is
  a deadline («Clock: 23:24 = 1h50 elapsed, ~2h10 left»).
- Don't drive the simulator with the MCP tool while an agent's `simctl` loop uses the same device. zsh does not
  word-split `$var`: use `${=var}` for `simctl launch` args.
- Owner messages typed mid-turn are his, not injected — don't doubt them.
- Workflow stopped or cut for time: edit the script **without changing earlier agents' prompt text** and resume
  with `Workflow({ scriptPath, resumeFromRunId: '<wf_id>' })` — unchanged agents return cached. Paste finished
  results inline rather than re-running them, so earlier prompts stay byte-identical.

## 6. Stall recovery (exact procedure)

Symptom: «no progress for 600s / stream watchdog», a Read loop («Wasted call — file unchanged since your last
Read»), or an agent that keeps spawning agents.

1. **Stop it** (TaskStop by id). If builds keep running or `build.db` is locked:
   `pgrep -fl 'xcodebuild|claude -p'` → `kill -9 <pid>` (TaskStop does not always find a zombie);
   build into a second derived-data dir (`.build-sim2`) if the first stays locked.
2. **Look at disk, not at the transcript:**
   ```bash
   skills/agent-orchestration/scripts/stall-check.sh <repo> --report <dir>/task-N-report.md \
     --guard '<the brief's forbidden patterns>' <file1> <file2> ...
   git -C <repo> diff --stat -- <files>          # how much landed
   git -C <repo> status --short                   # anything outside the slice?
   ```
3. **Build once** with the brief's command (`… | grep -E "error:|BUILD (SUCCEEDED|FAILED)"`). A partial edit can
   leave a compile error.
4. **Decide:**
   - all files edited + guards 0 + build green → done; lead takes the missing screenshots and writes the ledger
     line («stalled after finishing all 5 files; lead verified»). The most common case.
   - partial, ≤ 2 files left → **finish inline**.
   - partial, more left → re-dispatch **only the untouched files** with «pick up partial work: files X, Y are done,
     do not redo them».
   - nothing written → re-dispatch narrower or on the stronger model; a **second stall on the same slice → inline**.
5. Ledger line with what was verified by whom.

## 7. When results come back

- **A report is a claim.** Re-run build/tests/guards yourself and look at the diff and screenshots before telling
  the owner it is done.
- **Review by risk tier, not by habit:**
  - money, calls/push, auth, backend contracts, concurrency, migrations → task review every time, with the 2–3
    risks **named** and the implementer's claims listed for checking (`templates/reviewer-rules.md`). Such reviews
    routinely catch real bugs (a stale poll tearing down a live call, a handler reachable from a sandboxed iframe)
    in slices reported DONE with green tests.
  - UI re-skins, copy, mechanical ports → lead checks report + screenshots; one whole-branch review per milestone.
    Reviewing every cosmetic task doubles the time per task.
  - one scoped re-review after a fix; a fix that is one comment line, the lead just reads.
- Reviewers get the code/diff and the criteria, **not your conclusion** — handed a hypothesis, agents confirm it.
- A final review compares the spec's claims with the code (e.g. "1 wire change" in the spec vs 3 in the diff).
- Final gate when review was skipped under deadline: guards + both builds + tests + a lint agent + the owner's
  screenshot review, and say it was skipped.
- Report git work with direction and scope: «merging origin/main INTO feature/x, locally, not pushed».

## 8. Environment rules

- **Worktrees: ask first, per repo.** Many owners prefer one branch in place; if the tree is dirty, ask the owner
  to commit/stash. With consent, a worktree may need `node_modules` symlinked + `info/exclude`. Never create one
  silently.
- **Connector missing → stop and ask** the owner to connect it (Figma, App Store Connect). Don't let agents build
  a code workaround. Credentials are a hard stop, not something to work around.
- **Production deploys are the owner's** (e.g. `wrangler deploy` is denied by the classifier — hand over the command).
- **One cwd per project**: sessions all started from one repo fill its memory with other projects. Dispatch agents
  with the target repo's absolute path.
- Figma MCP: `use_figma` handles many parallel calls; `get_screenshot`/`get_metadata` count against a daily cap on
  Pro — agents screenshot inside `use_figma` with `node.screenshot({scale: 1.5})`.
- Agents never run with `bypassPermissions` and never commit unless the project's rule says so.

## Lessons (why the rules exist)

- Persona agents on heartbeats (CEO/Engineer/CMO): ~90% of the spend went to the manager agent writing personas
  and hire requests; one real deliverable; runs ended on the usage limit. → one lead, workers with briefs, no
  manager agents; wake-ups always carry a task.
- Implementers hung re-reading unchanged files. → explore-heavy implementation inline; review read-only.
- Agents delegated in circles; a zombie `claude` looped xcodebuild, locked build.db and clobbered edits. →
  «Do NOT use the Agent tool» in every prompt; architecture rules in every prompt; many-file refactors done directly.
- Half of the dispatches stalled under a 4-hour deadline, yet the work finished on time because each slice was
  ≤ 5 files with build, guards and screenshot recipe in the brief, and the lead checked disk first. → §3, §6.
- Per-task reviews of risky slices caught several real bugs in one day, all reported DONE. → risk-named reviews.
- A long audit cut for time kept its cached agents; unverified findings stayed labelled unverified. → §5; never
  promote unverified findings.
- Workflow agents saw the owner's last unrelated message and answered it. → ISOLATE preamble.
- Doc-rebuild agents given no sources wrote generic text. → agents rebuilding docs get real source paths and a
  quality-bar file, one dir each.
