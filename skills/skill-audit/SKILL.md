---
name: skill-audit
description: "Use for the monthly review of skills, CLAUDE.md and agent prompts: every line must prove it earns its context tokens or be deleted, rewritten or merged. Usage stats, with/without-skill evals, line ablation, a prosecutor vs defender. Triggers: \"skill audit\", \"skill review\", \"clean up the skills\", \"monthly skill review\"."
argument-hint: "[skill-name | all] [--month YYYY-MM]"
---

# Skill audit — prove it or delete it

Skills rot in three ways: the model learns to do the thing by default (the line is now dead
weight), the product changes (the line is wrong), or nobody triggers the skill (all of it is dead
weight that still costs listing tokens). The audit runs monthly; **the burden of proof is on the
line, not on the deleter.**

Your own cases for this skill live in `local/skills/skill-audit/` (git-ignored, see `local.example/README.md`).
Read them first if they exist; append the outcome of each round/incident there.

## Inputs

- Usage: `/skill-doctor` (or `/plugin stats`) → per-skill listing cost, 7-day uses, never-invoked.
- Evals: `evals/<skill>/…` cases. A skill without evals cannot pass the audit: writing its first
  2–3 cases from memory/feedback incidents is the first action item.
- Incident log: the feedback memories / postmortems each line was born from (`Why:` lines).

## Step 1 — Skill-level gate (cheap)

| Signal | Action |
|---|---|
| 0 uses in 60 days and no eval failure without it | propose **delete** (or `disable-model-invocation: true` if it's a manual tool) |
| `claude plugin eval --ablation with-without` Δ ≤ 0 | skill adds nothing → **delete or rewrite** |
| trigger eval: fires on negatives / misses positives | rewrite `description` only |
| Δ > 0 and used | go to step 2 |

## Step 2 — Line-level ablation

Split the SKILL.md into **units** (a bullet, a rule, a table row, an example). For each unit:

1. **Prosecutor** (`skill-prosecutor` agent) argues for deletion: redundant with model defaults,
   duplicated elsewhere, outdated (model/version/product changed), contradicted by another line,
   vague (can't be checked), or too specific to one past case.
2. **Defender** (`skill-defender` agent) may keep it only with evidence of one of:
   - **E1 eval**: an eval case fails (or its score drops ≥ 10%) when the unit is removed;
   - **E2 incident**: a dated incident (memory `Why:`, postmortem) the unit prevents, from the
     last 6 months, and the model without the unit still makes that mistake (test it: one run);
   - **E3 contract**: an external hard requirement (App Store guideline, platform safe zone, API).
   "It seems useful" is not evidence.
3. **Judge** decides per unit: `KEEP` / `DELETE` / `REWRITE` (shorter, checkable) / `MERGE` (into
   another skill or CLAUDE.md) / `NEEDS-EVAL` (keep 1 month, write the eval case now).

Run the ablation for real when a unit is contested: copy the skill to a temp plugin with the unit
removed, run `claude plugin eval <tmp> --case '<skill>-*' --runs 3`, compare to the full skill.
With only 3–5 cases a single-line ablation is noise, so **ablate by section, then bisect** inside a
section whose removal hurts. Compare mean ± spread over ≥ 3 runs; a drop inside the spread is "no
effect".

Quick categories that need no ablation (Anthropic's 2026 cut of >80% of the Claude Code system
prompt used these): compensates for an older model's weakness; conflicts with another line;
derivable from the repo/code; "the model already knows"; dated facts. **Never delete on these
grounds** facts about *your* environment (Figma file ids, account rules, product canon) — the model
cannot know them; they need E2/E3 or a rewrite, not deletion.

## Step 3 — Report and apply

Write `docs/audits/YYYY-MM-<skill>.md`:

```
Skill: frame-qa   uses (30d): 14   listing tokens: 180   eval Δ with/without: +0.42
| unit | verdict | evidence | note |
| "count fingers on close-ups" | KEEP | E2 incident: six fingers shipped in a frame; E1 case frame-qa-hands Δ −0.33 | |
| "no decorative filler motion" | MERGE → design-review | duplicate | |
| "Geist may not cover Cyrillic" | DELETE | font now bundled, no incident in 6 mo | |
Tokens: 1 240 → 910 (−27%)   Eval score after edit: 0.94 (was 0.93)
```

Apply only after the eval suite passes at or above the previous score. Commit with the report.
The owner approves deletions of whole skills; line edits ship if evals hold.

## Registry and provenance (Chesterton's fence with the reason written down)

- `skills/registry.yaml` holds per skill: `owner`, `reviewed` (date), `born_from` (incidents),
  `evals` (case globs), `target_model`. `scripts/check_registry.py` fails CI when a skill is missing
  from the registry, has no eval case, or `reviewed` is older than 90 days (a "time bomb", as for
  stale feature flags).
- Non-obvious lines carry `<!-- why: six fingers shipped in a close-up | eval frame-qa-hands -->`.
  A line with no `why` and no eval effect is deleted without debate.
- Inventory limit: a skill body may only grow if the same audit deletes at least as many tokens
  elsewhere, or the owner approves the growth.

## Routine (automated)

Scheduled task `skill-audit-biweekly` (1st and 15th, 10:00):
1. `git pull` → branch `audit/<date>`.
2. `check_registry.py` → full `run_evals.py` with/without (~$15).
3. Up to 4 skills: failing or Δ ≤ 0 first, then edited since the last audit, then the oldest
   `reviewed`.
4. `workflows/skill-audit.js`.
5. Apply only evidenced unit DELETE/REWRITE, then re-run evals; keep the edit only if the score holds.
6. Commit on the branch, no push.
7. A phone-readable report listing what needs the owner's approval: whole-skill deletions, MERGEs,
   NEEDS-EVAL cases.

Typical open items: a plugin skill that duplicates a user-level skill (Δ 0); a user-level skill that
contradicts a plugin rule and wins the trigger; a case with negative Δ or 0/0 to diagnose. Keep your
current list in `local/skills/skill-audit/`.

Scope: plugin skills first. Your own user-level skills join once each has a registry entry and two
eval cases.

## Cadence

- Every skill edit: run that skill's eval cases (cheap, like unit tests on commit).
- Model change: full suite with/without for every skill; model-compensation lines go first.
- Monthly (scheduled routine, first Monday, ~2 h): step 1 for all skills; step 2 for 5 skills in
  rotation (every skill deep-audited once a quarter) + any skill with a failing eval or edited
  this month.
- Every incident between audits: add the eval case the same day (see `eval-driven-skills`) — the
  audit then has evidence to work with.
- Quarterly: re-run baselines on the current model; lines that only patched an older model's
  weakness are the first to go.
