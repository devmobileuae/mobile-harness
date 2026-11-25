# Evals: what they are and how I use them

## In short

An **eval** is an automated test for a non-deterministic system: a prompt, a skill, an agent. A unit test checks
a function's "input → output". An eval checks *behavior*: a set of real tasks plus the rules by which an answer
counts as good. Everything runs several times, and you compute the pass rate and the **delta against
baseline**.

| | Unit test | Eval |
|---|---|---|
| Subject | function | prompt / skill / agent / model |
| Result | pass/fail, deterministic | pass rate over N runs |
| Oracle | `assertEqual` | code grader, LLM judge, human |
| Main metric | all green | score **and Δ against baseline** |
| When to run | on every commit | on a skill change and on a model change |

## Anatomy of a case (`claude plugin eval` format)

```
evals/frame-qa-narration/
├── prompt.md          # the task as I would phrase it; the skill is not named
└── graders/
    ├── fired.md       # type: tool_used — did the skill fire at all?
    ├── narration.md   # type: llm — did it catch "It's dad" under a notification from Mom?
    └── hands_and_zones.md
```

## Graders

A grader is one yes/no check on one property of a run. A case usually has 2–4 of them: one that the skill
fired, one or two on the result, sometimes one on the process. The score of a run is the weighted share of
graders that passed.

### The types I use, from cheap to expensive

| Type | What it checks | Example in this repo | How it fails |
|---|---|---|---|
| `tool_used` | a tool or skill was called, `min`..`max` times | `fired.md`: `Skill` with `input_match: frame-qa` | proves the skill loaded, not that it helped |
| `tool_order` | trajectory: call A happened before call B | `handoff-writes-doc/skill_before_write.md`: `Skill:session-handoff` before `Write:HANDOFF` | over-constrains when several orders are fine |
| `regex` | a hard format or content rule in the answer or the trace | `aso-keyword-field/format.md` (comma list, no spaces, ≥ 6 terms); `frame-qa-narration/verdict_line.md` (`SHIP` / `FIX FIRST` line) | brittle to wording; only for rules that really are format |
| `file_exists` | an artifact was produced | `handoff-writes-doc/file.md`: `docs/HANDOFF-*.md` | a file exists, but its content may be wrong |
| `llm` | judgement against a narrow rubric | `frame-qa-narration/narration.md`: catches "It's Dad" under a notification from Mom | the judge has its own errors and biases |
| human | spot-check of judge verdicts | 5 verdicts a month | slow; does not scale |

Code graders (`tool_used`, `tool_order`, `regex`, `file_exists`) are fast, free and deterministic. Model
graders (`llm`) handle meaning. Humans calibrate the model graders. This split (code-based, model-based,
human) is the standard one in public eval guides; the rule is to use the cheapest grader that can fail.

### Rules for writing them

- **The cheapest grader that can fail.** If a rule is a format ("one verdict line", "keyword field with no
  spaces after commas"), a regex catches it with no cost and no noise. An LLM judge is only for meaning.
- **One property per grader.** "Is the answer good?" is not a rubric. "Flags the six-finger hand in frame 07"
  is.
- **PASS and FAIL written out**, plus the concrete evidence the judge must quote. The judge answers one
  line, `VERDICT: PASS` or `VERDICT: FAIL`, then one sentence of evidence.
- **Outcome and process are different graders.** The result can be right while the process is wrong
  (wrote the file before loading the skill) and the other way round. `tool_order` covers the process.
- **`arm: both` on quality graders.** By default a grader runs only in the WITH arm. A quality grader
  that is skipped in the baseline makes Δ meaningless; the first run had exactly this bug.
- **Negative cases are mandatory**: a prompt on which the skill must *not* fire (`tool_used` with
  `min: 0, max: 0, arm: both`). Without them, a skill that fires on everything looks great.
- **The judge is code too.** Run it on a cheap model (Haiku), use an odd number of votes when a verdict
  matters, and spot-check it by hand. If I disagree with one verdict in five, the rubric gets tightened.

### Reading runs: pass@k and pass^k

Each case runs k times (k = 3 here), because one run of an agent is noise.
- **pass@k**: at least one of k runs passed every grader. "Can it do this at all?"
- **pass^k**: all k runs passed every grader. "Can I rely on it every time?"

The gap between the two is the flakiness. Session handoff showed why it matters: with the skill pass^k was
3/3, without it 1/3, while the mean score moved only +0.42. For work that runs unattended (the morning
pulse, the audit), pass^k is the number that counts.

## Two arms: why a baseline

Each case runs twice: **WITH** the plugin and **WITHOUT** it.
- Δ ≈ 0 → the model already does this; the rule in the skill is dead weight and gets deleted.
- Δ > 0 → the skill really changes behavior; this is its measured value.
- Δ < 0 → the skill hurts (for example, it steers the wrong way).

## The loop (eval-driven skills)

```
incident ("mom has 6 fingers")
   → an eval case that fails now
   → the minimal skill edit
   → the case is green, the others did not break
   → commit: skill + case together
```
This is the same discipline as "bug → failing test → fix", only for prompts.

## How I have it set up

- **Source of cases: feedback memory.** Every "you did it again…" in the project memories of your apps
  is a failed eval. `registry.yaml` stores `born_from` for each skill: the incidents it grew out of.
  Eval cases in `evals/` use fictional apps; your own case notes stay in git-ignored `local/skills/`.
- **Runner.** `claude plugin eval` (official; I only have early access so far), and until then
  `scripts/run_evals.py`: the same case format, headless `claude -p`, both arms, an LLM judge on Haiku.
  ```bash
  python3 scripts/run_evals.py --tag frame-qa --runs 3          # one skill, with baseline
  python3 scripts/run_evals.py --runs 1 -j 6                    # the whole suite, fast
  claude plugin eval . --ablation with-without --threshold 0.8  # once access opens up
  ```
- **Gate.** `scripts/check_registry.py` in CI/pre-commit fails if a skill has no eval cases, if
  `reviewed` is older than 90 days (a "time bomb", like stale feature flags), or if SKILL.md is longer than
  500 lines.
- **Monthly audit** (`skills/skill-audit`, `workflows/skill-audit.js`): a prosecutor argues that
  a line should be deleted; a defender can keep it only with evidence: an eval case (E1), a dated
  incident (E2) or an external requirement (E3). A judge rules on each line. Ablation runs
  by section with bisection. More in [SKILL-REVIEW-RESEARCH.md](SKILL-REVIEW-RESEARCH.md).

## What the very first run caught (2026-11-25)

The `mobile-swiftdata-migration` case is a real crash pattern: a non-optional field with a default value
was added to the model of an app that was already in the store, and upgrade installs crashed.
- **Before the fix:** the `mobile-feature-delivery` skill did not fire. The model picked the general `swiftdata` skill
  and produced exactly the code that crashes installs (`var priority: Int = 0`). Score 0.0.
- **Cause:** the skill description had no trigger for "changing the data model in an app that has already
  shipped". On top of that, the eval itself was broken: the quality graders were not scored in the baseline, so the delta could not
  be computed.
- **Fix:** a trigger in `description` and `arm: both` for the quality graders. Results after the fix are
  in `evals/results/`.

This is the answer to "why evals": without them, the rule "SwiftData fields must be optional" sat in
the skill and looked like protection, but in practice never fired.

## Metrics I watch

- pass rate per skill (target ≥ 0.9 over 3 runs);
- Δ with/without (target > 0.2; near 0 → candidate for deletion);
- trigger precision / recall on positive and negative prompts;
- tokens: size of the skill's description and body (at equal score, the smaller one wins);
- cost of a suite run ($) and time.
