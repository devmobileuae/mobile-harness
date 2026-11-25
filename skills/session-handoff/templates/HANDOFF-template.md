<!--
TEMPLATE for a full handoff (worked example: ../references/example-handoff.md); a shelve handoff uses only the
state, rejected rounds and open question sections. Delete sections that are empty;
never leave a heading with "n/a". Target 80–200 lines. Dates absolute. Secrets by NAME only.
Save as: docs/superpowers/HANDOFF-YYYY-MM-DD.md if the repo already has docs/superpowers/, else docs/HANDOFF-YYYY-MM-DD.md.
-->
# Handoff — YYYY-MM-DD

Read this first in a fresh session. It replaces scrolling the long chat of YYYY-MM-DD…DD and
**supersedes `HANDOFF-<older date>.md`** for <topic> (that file is still right about <what>).
`docs/` <is | is not> git-ignored<: everything here exists only on disk>.

## One-paragraph state

<Feature/part by part: built / reviewed / verified live / designed only / not started.> **Nothing is
<deployed | committed | pushed>** — <who commits: "the owner commits" | "agent commits on the branch">.
Branch `<branch>`, last commit `<sha>`; <ahead/behind main and origin, from scripts/tree_state.sh>.

Numbers at handoff (run by me just now, not quoted from an agent): <tests N/N>, <build green/red>, <lint>.

## Owner checklist (things only he can do)

<Say whether any of it blocks the next coding session.>

**A. Look and decide** — <screenshots folder>, <copy he hasn't read>, <decision with my recommendation>.
**B. <Deploy / accounts / store>** — numbered, one command per step, exact:
1. `<command>` — <what success looks like>.
2. …

## Resume here

> **UPDATE <date/session>:** steps <n> DONE. Start at step <m>. <Only ONE update block; a new day = a new file.>

1. **<First step>** — exact file / command / skill (`superpowers:executing-plans` with `<plan path>`), and the
   done-check (`<test command>` → <expected>).
2. If agents were still running at handoff: <agent/task> — landed if `<file>` contains `<symbol>`; otherwise
   apply from: <description>.
3. …

## Not verified — do not assume

- <claim> — <how it was (not) observed: read the code / one screenshot / never ran on device>.

## Decisions taken (owner, in chat)

- <decision> («<his words>», YYYY-MM-DD). <What it replaces.>
- How he wants to be talked to this round: <e.g. short status notes, pictures, one question with a recommendation>.

## Rejected — do not rebuild

- YYYY-MM-DD: <what was shown> (<where: Figma page / folder>) — «<his verdict>».
- Open question to ask before the next round: <…>

## Root causes found

- <bug> — <cause in one line> — fixed in `<file>` / not fixed.

## Stale things I found

- `<plan/README/CLAUDE.md line>` is stale: <why>. Use instead: <inline replacement>.

## Tooling facts (verified this session)

- Build: `<exact xcodebuild/gradle command with -destination id=…>`.
- Simulators/devices: `<name>` `<UDID>` — <state of its data>.
- Local servers: `<command>` from Bash, port <n>, <stopped/running at handoff>.
- Gotchas: <…>.

## Where things are

- Spec: `docs/…/specs/<topic>.md` (verbatim as approved). Plan: `…`. Ledger: `.superpowers/sdd/<plan>/progress.md`.
- Screenshots: `docs/screenshots/<date>-<topic>/`.
