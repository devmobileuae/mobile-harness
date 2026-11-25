# Flows and agents

All flows are deterministic workflow scripts (`workflows/*.js`): branching, loops and fan-out are set
by code, not by the model. Agents are files in `agents/`; each has a narrow role and its own toolset.

## 1. Conclave — debates for decisions

```
            ┌──────────── Opening (isolated, no view of other positions) ────────────┐
 question → │  Skeptic   Builder   User-advocate   Growth   Data-analyst              │
 + brief    └─────────────────────────────┬────────────────────────────────────────────┘
                                          ▼
                         Moderator: cruxes, unanimous? → if yes, Skeptic must
                                          │                 argue against
            ┌──────────── Round k (they see the board of all positions) ────────────┐
            │ each: steelman the opponent → doubt about THEIR OWN position (empty = │
            │ ask again) → attack/concede by argument id → new position +           │
            │ confidence, moved_by if they moved                                    │
            └─────────────────────────────┬──────────────────────────────────────────┘
                                          ▼
                    Moderator: cruxes open/closed, flags (jump >15 without moved_by,
                    role dropped its own interest, polite convergence) → continue/stop
                          (stop only after ≥2 rounds and with no open cruxes)
                                          ▼
                          Draft verdict → Red team (fresh agent with no context)
                                 fatal flaw? ── yes → one more round through the flow
                                          ▼
     Verdict: decision + confidence, reverse-if, cruxes, strongest dissent verbatim,
              position-change log, next cheapest experiment
```

Why this, and not just "ask the model":
- **Isolated opening** stops the roles from herding right away (anchoring).
- **Mandatory doubt** every round stops the roles from digging in.
- **moved_by** forbids changing position without a named reason, so convergence is honest.
- **Red team without context** gives a fresh look at the final conclusion.
- **The owner decides**: the conclave only advises.

## 2. Feature delivery (iOS + Android)

```
criteria → Planner: risk tiers (core→TDD, ui→smoke), slices of 1–3 files, platform pitfalls
         → Build: ios-engineer / android-engineer in parallel, build after every file,
                  report in docs/agent-reports/<slice>.md
         → Review: mobile-reviewer per platform, sees only the diff + criteria
         → Verify: qa-verifier on simulator/emulator, upgrade-install, dark mode, large text
         → READY / NOT READY → release-manager checklist → (risky release) conclave go/no-go
```

## 3. Reel pipeline (growth / content)

```
niche → growth-researcher (formats, hooks, reach numbers, audience language)
      → conclave: which hypothesis to shoot as a series of 10
      → scenario-writer × N variants (different hook angles)
      → adversarial scenario review (0–16, PRODUCE/REWRITE/DROP)
      → generation (Higgsfield / code / ElevenLabs) — outside the flow
      → frame-inspector: frame-qa gate (anatomy, safe zones, VO vs frame) → SHIP / FIX FIRST
      → after posting: growth-analytics → repeat / pivot / scale (metric-iteration)
```

## 4. Monthly skill audit

```
first Monday of the month
  → check_registry.py (freshness, whether evals exist, size)
  → /skill-doctor: usage over 30 days, never-invoked
  → evals with/without across all skills → Δ ≈ 0 → deletion candidate
  → 5 skills in rotation: inventory → [prosecutor ∥ defender] → judge on each line
  → ablation of disputed sections via evals → edits only if the score did not drop
  → docs/audits/YYYY-MM-<skill>.md, update reviewed in the registry
```

## Agent map

| Group | Agents | Tools |
|---|---|---|
| Mobile | ios-engineer, android-engineer, mobile-reviewer, qa-verifier, release-manager | build/test; reviewer and QA without Edit |
| Growth | growth-researcher, scenario-writer, frame-inspector | web; writer without Bash |
| Conclave | conclave-moderator, -skeptic, -builder, -user-advocate, -growth-strategist, -data-analyst | read-only |
| Audit | skill-prosecutor, skill-defender, eval-judge | read + run evals |

Principle: **reviewers and judges have no write access**; they are given the code or diff, not the author's conclusion.
The question "is this right?" is put to someone who did not write the answer.
