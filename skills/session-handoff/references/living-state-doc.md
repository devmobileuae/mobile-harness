# Living state doc — one file for a long-running stream of work

A dated HANDOFF is a snapshot: it is right on the day it is written and then decays. A project that runs for weeks
with a new piece every day or two (a serial, a release train, a growth experiment log) needs ONE file that is edited
in place after each piece ships and is always current. Handoffs then only say "what changed since" and point at it.

## Its sections (example: a short-video serial season)

| Section | Content | Why it's there |
|---|---|---|
| title + approval line | "Approved by the owner <date>: 10 episodes, about two a day, finale — <ending>" | The owner-approved frame, dated, so nobody re-litigates it |
| Rules | Rules learned the hard way, each with its source file | So they are applied, not rediscovered |
| Already released | Table: piece · date · what happened · audience choice with real counts and the read date | Canon. Also records what is NOT canon (withdrawn cuts) |
| Metrics | Views per piece measured on a named page on a named date; the trend line; the owner's verdict | Numbers with provenance |
| Open threads | Setups planted so far, dated per piece | So the next piece doesn't contradict or forget one |
| Destination | Where it is all heading | Every piece must keep it reachable |
| Remaining plan | Plan table | Allowed to be overtaken — say so with a date |
| Production costs | Credits/money per piece | Real costs to quote before spending |
| Assets | Cover rules + title → generation job id | So art can be referenced or regenerated |

## Rules for keeping one

1. **Edit in place after every shipped piece**, in the same session, before saying "done".
2. **Facts carry provenance:** where and when a number was read, who decided and when.
3. **Rejected / withdrawn work stays in, marked** ("not part of the canon"), so it is not rebuilt.
4. **The plan section is allowed to be wrong**; when reality overtakes it, say so with a date, don't silently rewrite it.
5. **Language = the owner's.** Skill bodies are English.
6. Per-piece detail lives next to the piece (`<series>/<piece>/script.md`, `metrics.md`); the living doc holds
   only what the NEXT piece needs.
7. **Memory pointer once**, to the living doc, not one per piece.

## When to use which

| Situation | Use |
|---|---|
| Long chat, big approved design about to become code; multi-day build; release prep | Dated `HANDOFF-YYYY-MM-DD.md` + memory pointer |
| Owner says "pause" mid-task | One PAUSED line in the existing ledger/handoff + WIP patch |
| A stream of similar pieces over weeks | Living state doc, edited after each piece; a handoff, if any, says "read <living doc>, then this delta" |
| Owner wants to paste something himself ("give me a prompt") | Resume prompt (template) pointing at the doc |

Other living docs worth keeping: SDD ledgers `.superpowers/sdd/<plan>/progress.md` (append-only, one line per event:
PAUSED / RESUMED / commit / decision), and the memory dir's `MEMORY.md` index, which says which handoff is current.
