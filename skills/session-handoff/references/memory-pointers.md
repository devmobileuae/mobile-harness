# Memory pointers — examples of the format

Memory is keyed by cwd: `~/.claude/projects/<abs path with / and . replaced by ->/memory/`. When `docs/` is
git-ignored, `docs/superpowers/HANDOFF-*.md` exists only on disk and nothing in git or CLAUDE.md points at it: the
pointer is the only way the next session finds it. (Fictional project names below.)

## A. The feedback memory that starts the habit — `save-context-and-handoff.md`

```markdown
---
name: save-context-and-handoff
description: When a session gets long the owner prefers to save context and continue in a fresh session rather than push on
metadata:
  type: feedback
---

When a working session has grown long, write a handoff and let the owner restart in a fresh session.

**Why:** *"let's save the context and I'll start in a fresh session"* — said right after approving a large
design, before any implementation started.

**How to apply:** before starting a multi-day build at the end of a long chat, offer this proactively. A good
handoff = a dated `docs/superpowers/HANDOFF-*.md` (state of the tree, root causes, loose ends, resume point), the
approved spec saved in `docs/superpowers/specs/`, and short memory pointers to both.
```

## B. A project pointer — `cycleapp-handoff-2026-03-09.md`

```markdown
---
name: cycleapp-handoff-2026-03-09
description: Where the 2026-03-06…09 work stands — an uncommitted 1.4 bundle on hotfix/1.3 and the on-disk handoff doc to read first
metadata:
  type: project
---

As of 2026-03-09 the branch `hotfix/1.3` holds four finished, **uncommitted** changes meant to ship together as
1.4: the review-prompt fix, the insights screen, the system tab bar, a truthful analytics line in the privacy
sheet. 165 kit tests green, app builds.

The full state, root causes, loose ends and simulator notes are in `docs/superpowers/HANDOFF-2026-03-09.md`
(docs/ is git-ignored — on disk only).

**Why:** the owner asked to save context and continue in a fresh session after a very long chat.

**How to apply:** read that handoff before touching anything; don't redo the four changes; the next work item
is [[cycleapp-partner-sharing]]. Blocking debt before release: [[cycleapp-privacy-debt]].
```

What it does right: absolute date in the first words; branch + "uncommitted" + test count; the doc path with the
reason it is invisible; "don't redo"; the next item as a `[[link]]` to the memory that holds that design.

## C. A superseding pointer (description line)

```yaml
description: "READ FIRST — state of partner sharing after the 2026-03-09…10 sessions (Parts 1–3 built, Part 4 designed, nothing deployed or committed) and the owner's checklist; points at the on-disk handoff doc"
```

Body names what it supersedes and what the older note is still right about. A same-day update is appended as a
dated paragraph: «**Update, second session of 2026-03-10:** Part 3 is CLOSED … Still unverified: …».

## D. The index lines in `MEMORY.md` — current vs older

```markdown
- [Handoff 2026-03-11](cycleapp-handoff-2026-03-11.md) — READ FIRST: release 1.4 state with the owner's TestFlight checklist; doc in docs/superpowers/HANDOFF-2026-03-11.md
- [Handoff 2026-03-10](cycleapp-handoff-2026-03-10.md) — older: state before Part 4; still holds the original deploy checklist
- [Save context and hand off](save-context-and-handoff.md) — long session → write HANDOFF doc + memory pointers, owner restarts fresh
```

Only one line says READ FIRST. Older ones say "older:" and what they are still right about.

## E. Pause pointers inside long project memories (no separate doc)

> 2026-04-02 night, paused ("let's leave it for tomorrow"): tasks 1–12 and 14 merged in the worktree, Task 13 in its
> first fix round. Left: Task 15 translations, Task 16 simulator check, final review.
> Ledger with the resume list: .superpowers/sdd/2026-04-02-release/progress.md.

> 7-agent Workflow `wf_<id>` was STOPPED mid-run. Script: `…/workflows/scripts/<name>.js`.
> Resume: `Workflow({scriptPath, resumeFromRunId: "wf_<id>"})` — completed agents return cached; verify per module.

## F. After the work moves on — update the pointer

Append «**UPDATE after the daytime session:** steps (1)–(3) are DONE» and later «1.4 is submitted —
`WAITING_FOR_REVIEW`, build 14». A pointer that still says "in flight" a week later is a lie the next session acts on.
