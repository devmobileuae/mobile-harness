---
name: session-handoff
description: "Use when the user says \"save the context\", \"handoff\", \"I'll continue in a new session\", \"pause, we'll finish tomorrow\" or \"continuing from the handoff <date>\", when an approved design turns into a multi-day build, or a long project needs one living state doc. Writes a dated HANDOFF doc, memory pointers, a resume prompt, or a pause note with a WIP patch."
---

# Session handoff

Many owners restart fresh rather than push a long chat ("let's save the context and I'll start in a fresh
session") and resume by naming the doc: "continuing from the handoff 2026-03-10". A good handoff is resumed from
without re-discovery; a bad one sends the next session to a stale script.

Your own cases for this skill live in `local/skills/session-handoff/` (git-ignored, see `local.example/README.md`).
Read them first if they exist; append the outcome of each round/incident there.

Read before writing: `references/example-handoff.md` (the model), `references/memory-pointers.md` (pointer
formats), `references/living-state-doc.md` (one file for a long stream of work).

## 0. Which output the owner is asking for

| His words (typical) | Output | Size |
|---|---|---|
| "save the context and I'll start in a fresh session", "write a handoff of everything left – I'll continue in a new session", "write a handoff for the remaining fixes for tomorrow" | **Full handoff**: dated doc + spec saved verbatim + memory pointer (§1–§4) | 80–200 lines |
| "let's pause, we'll finish tomorrow", "I'm off to bed", "the laptop overheated… let's pause", "pause everyone for now" | **Pause note**: one PAUSED line in the existing ledger/doc + WIP patch + stop/record every running agent (§5) | 3–6 lines |
| "give me a prompt for a new session" | **Resume prompt** in a ```text block, in the owner's language (`templates/resume-prompt.md`) | ≤ 25 lines |
| A stream of pieces over weeks (serial episodes, releases) | **Living state doc**, edited in place after each piece (§6) | grows slowly |
| "I don't like any of it, let's shelve the release for now" | **Shelve handoff**: state in 3 lines + every rejected round + the open question | 20–40 lines |
| "create a folder … move the info there and we'll start in a new session" | Move the material into the new repo + pointer in THAT repo's memory dir | — |

Offer a full handoff yourself when a big design was just approved and implementation is next, or when you are
about to dispatch a multi-hour agent wave at the end of a long chat. Say it in one line; don't push.

## 1. Measure the tree — never write state from memory

```bash
bash skills/session-handoff/scripts/tree_state.sh <repo> \
     [--paths "backend/ AppKit/"] [--patch .superpowers/sdd/<plan>/wip.patch]
```

It prints Markdown for "State of the tree": branch, `git log -1`, tags on HEAD, ahead/behind upstream, local
`main` vs `origin/main`, tracked vs untracked counts with `git status --short`, stashes, worktrees, and whether
`docs/`, `docs/superpowers/`, `.superpowers/` are git-ignored. The raw commands, if the script is not at hand:

```bash
git branch --show-current; git log -1 --format='%h %s (%cd)' --date=short; git tag --points-at HEAD
git rev-list --left-right --count @{u}...HEAD          # behind ahead vs upstream
git rev-list --left-right --count origin/main...main   # "main is 5 commits ahead of origin/main"
git status --short; git ls-files --others --exclude-standard | wc -l
git status --porcelain -- backend/ | wc -l             # per-bundle count when two bundles share a branch
git stash list; git worktree list
git check-ignore -q docs/HANDOFF-probe.md && echo "docs/ ignored -> pointer required"
git diff HEAD > .superpowers/sdd/<plan>/<name>-wip.patch   # pause mid-task with uncommitted work (untracked not included)
```

Then run the gates yourself and write the numbers: «kit `swift test` → 245; Worker `vitest` → 137 in 10 files,
`tsc` clean; app builds». Never quote an agent's numbers.

Owner rules that change what you write: in many repos **the owner commits** ("Nothing is committed (owner's
rule)") — say so, don't commit to "save" state. Some owners want **no worktrees**; others run worktrees with agent
commits — follow the repo's own ledger and CLAUDE.md.

## 2. Write the doc

Path: `docs/superpowers/HANDOFF-YYYY-MM-DD.md` if the repo already has `docs/superpowers/`; otherwise
`docs/HANDOFF-YYYY-MM-DD.md`. Start from `templates/HANDOFF-template.md`. Order of sections:

1. **Header**: «Read this first in a fresh session. It replaces scrolling the long chat of …» + what it
   **supersedes** and what the older doc is still right about + whether `docs/` is git-ignored.
2. **One-paragraph state**: part by part — built / reviewed / verified live / designed only. Bold the
   "nothing deployed, nothing committed" sentence. Numbers measured in §1.
3. **Owner checklist** — only what he can do (logins, deploy approval, secrets, App Store Connect, Apple
   Developer capabilities, pushing the site), grouped A–E, one exact command per step, with the success signal
   («"Send test event" must show 200»). Secrets by NAME only (`RC_WEBHOOK_SECRET`, `RC_API_KEY`), never values.
   State whether any of it blocks the next coding session.
4. **Resume here** — numbered; each step names the file/command/skill and its done-check. If agents were still
   running: how to tell they landed («if the files show the changes, they landed; otherwise apply them from the
   descriptions»).
5. **Not verified — do not assume** — each with how it was observed («read, never run — it needs a tampered
   server»; «dark mode … the app is light-only since `<sha>`»).
6. **Decisions taken (owner, in chat)** — his words in quotes with the date, and how he wants to be talked to this
   round (e.g. "are you overthinking again?" → short notes, pictures, one question with a recommendation).
7. **Rejected — do not rebuild** (when design rounds were refused: date, Figma page, export folder, verdict).
8. **Root causes found** — the expensive knowledge, one paragraph each.
9. **Stale things found** — plan steps, README commands, CLAUDE.md lines that no longer match the code, with the
   replacement inline («the script in the plan is stale» + a corrected smoke test).
10. **Tooling facts (verified)** — exact build command with `-destination 'platform=iOS Simulator,id=<UDID>'`,
    simulator names + UDIDs + what data they hold, local servers (`npx wrangler dev --port 8799` from Bash,
    stopped/running), gotchas (toasts live 1.8 s → burst screenshots).
11. **Where things are** — spec, plan, ledger `.superpowers/sdd/<plan>/progress.md`, screenshots folders.

Approved spec: save it **verbatim** to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` — the handoff links
it, never re-summarises it.

Size: ~200 lines works; so does a 1.8 KB shelve note. A doc that stacks four "read this first" blocks (~500 lines)
does not. A new day or phase = a **new dated file** that supersedes; inside one day, **one**
`> **UPDATE <session>:** steps 1–2 DONE, start at step 3` block on top of "Resume here".

## 3. Memory pointer — in the memory dir of the repo the next session will open

Memory is keyed by cwd: `~/.claude/projects/<abs path with / and . replaced by ->/memory/`. If most sessions run
from one repo, memory for other projects piles up there and new sessions in the right folder "re-learn the project
from scratch every time". If this session's cwd is not the project's, write the pointer into the project's dir
anyway and say so.

1. File `<project>-handoff-YYYY-MM-DD.md` from `templates/memory-pointer.md`: absolute date first; branch,
   committed or not, test count; the doc path + «docs/ is git-ignored — on disk only»; "don't redo X"; next step;
   unverified list; `[[links]]` to the design memory and the deadline memory; **Why** with his exact words.
2. `description:` starts with `READ FIRST —` only for the newest; quoted YAML.
3. `MEMORY.md`: add one line; relabel the previous handoff's line «older: … (still right about …)». Format in
   `references/memory-pointers.md` §D.
4. When the work moves on, **update the pointer** («UPDATE after the daytime session: steps (1)–(3) DONE»,
   «1.4 is submitted — WAITING_FOR_REVIEW, build 14»). A pointer that says "in flight" a week later will be acted on.

## 4. Close the turn

End the reply with: the doc path, the memory file path, and the one line he pastes: "continuing from the handoff
YYYY-MM-DD". If open decisions would unblock the next session, list them in one line each with your
recommendation (e.g. which RevenueCat project to use; `sudo xcode-select -s …` so the next session can drive the
simulator itself).

## 5. Pause note (mid-task "pause")

Not a new doc. In the ledger or current handoff, one line:

```
PAUSED 2026-04-02 by owner ("pause, we'll finish tomorrow"): final-fix pass (opus) was stopped near its end —
uncommitted WIP in the worktree (14 files, also saved as final-fixes-wip.patch); it had just said it was removing
DEBUG probes (check for leftover print/deinit logging). No report written. Resume: read final-fixes.md, review the
WIP diff against items 1–11, finish + build + test, commit, scoped re-review, tap-through.
```

- `tree_state.sh <repo> --patch <ledger dir>/<name>-wip.patch` (untracked files: list them, they are not in the patch).
- Stop every running agent/workflow (TaskStop) and record per agent: done / partial / not started. For a Workflow:
  script path + run id + `Workflow({scriptPath, resumeFromRunId: "<id>"})` — finished agents come back cached;
  mark partial output "verify per-module before trusting".
- Local servers (`wrangler dev`, dev servers): stop them and say so.
- Append a one-line pause to the project memory too (what is merged, what is in flight, where the ledger is).
- On resume, write `RESUMED <date>` under it in the ledger.

## 6. Living state doc for long-running projects

When pieces ship every day or two for weeks, keep ONE file edited in place (approved frame with date; rules with
sources; "what shipped" table with real numbers and what is NOT canon; metrics with page + read date; open threads;
plan that may be overtaken; costs per piece; asset ids). Update it in the same session each piece ships; handoffs
then say "read <living doc>, then this delta". Details: `references/living-state-doc.md`.

## 7. Resuming from a handoff ("continuing from the handoff …")

1. Read the memory pointer, then the whole doc, then the UPDATE block on top.
2. Re-run `tree_state.sh` and the gates; compare with the doc. Any mismatch (new commits, a file changed, a count
   differs) → say what differs before acting.
3. For each "in flight" item, do the landed-check; mark LANDED / not landed in the doc.
4. Don't re-ask decisions listed in the doc.

## Lessons (why the rules exist)

- A pointer in the wrong cwd = no pointer. Write to the project's own memory dir.
- A stopped workflow resumes for free only if the run id and script path were saved.
- Plans go stale while code moves; check every command you point at and replace stale ones inline.
- Fix batches still running at handoff: the landed-check makes the next session's first step mechanical instead of
  a re-review.
- A "toasts don't appear" loose end rode two handoffs as a bug; it was a 1.8 s toast and one screenshot. Write how
  a loose end was observed.
- A dead build command in CLAUDE.md (`name=iPhone 16 Pro` stopped resolving): the handoff carries the `id=` form and
  flags the stale line. Tooling facts in the handoff beat CLAUDE.md until the owner fixes it.
- One handoff grew to 41 KB with four "read this first" blocks; the index had to say which block is current.
  New day → new file.
- A wrong claim about the owner (his genuine mid-turn messages called "text inside a tool result") is corrected in
  a visible **Correction** paragraph, not edited away.
- Rejected design rounds listed with dates and Figma locations let the next round start from the open question
  instead of variant eleven.
- A pause mid fix-pass needed one ledger line + a WIP patch; it resumed the next morning cleanly. Pauses don't need a doc.
