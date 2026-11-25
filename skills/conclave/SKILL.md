---
name: conclave
description: "Use when a decision is expensive to get wrong and has no single right answer: product direction, architecture (native vs KMP), pricing, which content to scale, release go/no-go. Role agents debate in rounds, doubting themselves; a moderator gives a verdict with dissent kept. Triggers: \"conclave\", \"run a debate\", \"council\", \"I need a decision, not an opinion\"."
argument-hint: "[question] [--roles skeptic,builder,user-advocate,growth-strategist,data-analyst] [--rounds 3]"
---

# Conclave — debate until the position survives doubt

A single model asked "should we do X?" anchors on its first answer and then defends it. A conclave
breaks that: several agents with **different incentives** argue in rounds, each is **forced to doubt
its own position every round**, and nobody may change their mind without naming the argument that
moved them. The output is a decision *plus* the reasoning trail, the dissent and the conditions
that would reverse it.

Your own cases for this skill live in `local/skills/conclave/` (git-ignored, see `local.example/README.md`).
Read them first if they exist; append the outcome of each round/incident there.

## When to use / not to use

Use for decisions that are costly, reversible only at a price, and contested: product direction,
architecture, pricing, release go/no-go, which growth series to scale, killing an app.

Do **not** use for facts (look them up), for code correctness (use review + tests), or for taste
calls the owner has already made — the conclave advises, the owner decides.

## Protocol

1. **Frame** (moderator). Restate the question as a decision with options, the success metric and
   the constraints (deadline, budget, team = one person + agents). Collect evidence (PostHog
   numbers, App Store data, memory notes) into a short brief. No evidence → say so in the brief.
2. **Opening (isolated).** Each role writes a position *without seeing the others*:
   `position`, `confidence 0–100`, `top 3 arguments` (with ids), `assumptions`, `what evidence
   would change my mind`. Isolation prevents herding.
3. **Debate rounds (N, default 3).** Each role sees all current positions and must, in order:
   - **Steelman** the strongest opposing argument in its best form.
   - **Doubt**: name at least one real weakness in its *own* position (mandatory every round; an
     empty doubt is rejected and the turn is re-asked).
   - **Respond**: attack or concede specific arguments by id.
   - **Update**: new position + confidence. If it changed, cite the argument that caused it
     (`moved_by`). Confidence moving > 15 points without `moved_by` is flagged by the moderator.
4. **Moderator after each round**: list the cruxes (the 1–3 disagreements the decision hinges on),
   note who moved and why, and decide: continue / stop (converged). Stop early only after ≥ 2
   rounds **and** no open crux. Unanimity in the opening → the skeptic must argue the opposite.
5. **Red-team the verdict.** A fresh skeptic with no debate context attacks the draft verdict. A
   fatal flaw triggers one more round on that flaw only.
6. **Verdict.** Decision, confidence, conditions to reverse it, the strongest dissent verbatim, the
   position-change log, and the cheapest next experiment that settles the remaining crux.

## Roles (pick 3–5)

| Role | Incentive | Agent |
|---|---|---|
| Skeptic | find why this fails | `conclave-skeptic` |
| Builder | engineering cost, risk, maintenance for a 1-person team | `conclave-builder` |
| User advocate | what the user actually feels on the screen | `conclave-user-advocate` |
| Growth strategist | installs, ratings, content-market fit, revenue | `conclave-growth-strategist` |
| Data analyst | what the numbers actually support, sample sizes | `conclave-data-analyst` |
| Moderator | runs rounds, keeps cruxes, writes verdict, never votes | `conclave-moderator` |

Default sets: product → skeptic, user-advocate, growth-strategist, data-analyst.
Architecture → skeptic, builder, user-advocate. Release go/no-go → builder, skeptic, data-analyst.

## How to run

- Deterministic run: the workflow `workflows/conclave.js` —
  `Workflow({scriptPath: "<repo>/workflows/conclave.js", args: {question, brief, roles, rounds}})`.
- Cost: 4 roles × 3 rounds + red team ≈ 27 agents, ~3.4M subagent tokens, ~7 min per run.
  For smaller calls use 3 roles and `rounds: 2`. Example: `docs/examples/conclave-kmp-port-vs-ios-growth.md`.
- Light run without workflows: spawn the role agents in parallel for the opening, then feed each
  the others' positions per round; you act as moderator and follow the same rules.

## Output format

```
## Verdict: <decision> (confidence N/100)
Reverse if: <conditions>
Cruxes: 1) … 2) …
Strongest dissent (<role>): "<quote>"
Position changes: <role>: A→B in round 2, moved_by: <argument id>
Next experiment: <cheapest test that settles the open crux, metric, threshold, date>
```

## Lessons from the first runs (example: KMP port vs iOS growth for a small iOS app)

Full write-up: `docs/examples/conclave-kmp-port-vs-ios-growth.md`. Verdict shape: a narrowed option
(iOS installs and ratings, no paywall A/B below ~300 views a week) with the alternative gated by a
measurable condition (click→install ≥ 5%, n ≥ 150, Android share ≥ 40% with CI low bound ≥ 30%).
- **Unanimous opening (all B)**, so the forced devil's advocate fired. In round 1 the Skeptic
  conceded one argument to it (S2a). That is the mechanism working.
- **Context leak**: workflow agents saw the owner's latest unrelated message, and the moderator
  started answering it. Fix: the `ISOLATE` preamble on every prompt.
- **Never stopped**: open cruxes needed data (n, geo), not argument, so the run hit the round cap.
  Fix: a `needs_data` flag on cruxes; those become the next experiment.
- **Over-reported changes**: every role "changed" every round, mostly rewording. Fix: count only a
  changed recommendation.
- **Confidence 0.72 vs 72**: the scale is pinned in the schemas.
- **Cost**: 27 agents, ~3.4M tokens, ~7 min.

## Anti-patterns this skill exists to prevent

- Polite convergence: everyone's confidence rises with no `moved_by` → flagged, round repeated.
- A role abandoning its incentive ("as builder I agree with growth") without naming a reason.
- A verdict without reverse conditions — that is an opinion, not a decision.
- The conclave overriding a call the owner already made. It may say once what it costs.
