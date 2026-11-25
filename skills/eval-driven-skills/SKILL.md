---
name: eval-driven-skills
description: "Use when creating or changing a skill, agent prompt or CLAUDE.md rule, and whenever the user reports a repeated agent mistake: turn it into an eval case in evals/, run `claude plugin eval` with and without the skill, then edit the skill. Triggers: \"write an eval\", \"add a rule to the skill\", \"you did it again\", \"check the skill\"."
---

# Eval-driven skills — every incident becomes a regression test

A rule added to a skill without a test is a hope. The loop: **incident → eval case that fails →
skill edit → eval passes → commit both.** Same discipline as "bug → failing test → fix".

Your own cases for this skill live in `local/skills/eval-driven-skills/` (git-ignored, see
`local.example/README.md`). Read them first if they exist; append the outcome of each round/incident there.
Eval cases in the tracked `evals/` use fictional apps; keep your app names in local notes.

## 1. Capture the incident as a case

`evals/<skill>-<short-name>/prompt.md` — the task phrased the way the owner would ask, without
naming the skill. Frontmatter: `tags`, `runs: 3`, `allowed_tools`, `max_turns`.
Put input artifacts (a frame, a script, a diff) next to it and refer to them by path.

## 2. Pick graders — cheapest that can fail

| Grader | Use for | Example |
|---|---|---|
| `tool_used` | did the skill fire / was a tool called | `tool: Skill`, `input_match: frame-qa` |
| `tool_order` | process order | build ran before "done" message |
| `regex` | hard format/content rules | verdict line present; no "it's dad" |
| `file_exists` | an artifact was produced | `docs/HANDOFF-*.md` |
| `llm` | judgement with a crisp rubric | "flags the 6-finger hand in frame 07" |

LLM rubric rules: one property per grader; write PASS and FAIL conditions; name concrete evidence
the judge must find. "Is it good?" is not a rubric.

Always add at least one **negative** case (a prompt where the skill must *not* fire,
`tool_used` with `min: 0, max: 0, arm: both`).

## 3. Run with and without

```bash
claude plugin eval . --case '<skill>-*' --runs 3 --ablation with-without
```

Read the Δ column: the case should fail (or score low) without the skill and pass with it. If it
passes without the skill, the model already does this — **don't add the rule**.

## 4. Edit the skill minimally, re-run the whole suite

Shortest wording that turns the case green. Re-run all cases to catch regressions in neighbours.
Commit skill + case + the report summary line together.

## Metrics to track

- Pass rate per skill (target ≥ 0.9 on 3 runs), Δ with/without (target > 0.2).
- Trigger precision/recall on positive/negative prompts.
- Tokens: listing + body size. Smaller with the same score wins.

## What the first runs found (2026-11-25)

Full tables: `references/runs-2026-11-25.md`.

- **SwiftData**: the migration rule existed, but the user-level `swiftdata` skill won the trigger
  and both arms produced the crashing `var priority: Int = 0`. The fix went into the description,
  not more rule text.
- **frame-qa Δ 0**: a user-level serial-video skill already caught the same flaws, so this was a
  duplicate. `frame-qa` became the generic visual gate that defers to the more specific skill.
- **design-review Δ −0.33**: the skill didn't fire and the model already pushes back. Before adding
  rules, check whether the default is already good.
- **Harness traps**:
  - `arm: both` is needed on quality graders;
  - `max_turns` ≥ 25 for cases that write files;
  - an API error mid-run is infra, not signal;
  - 1 run is noise for Δ < 0.3.

## Human calibration

Once a month spot-check 5 LLM-judge verdicts by hand. If you disagree with ≥ 1, tighten that rubric:
the judge is also code that needs tests.
