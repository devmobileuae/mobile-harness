# Typical multi-agent run shapes, what they cost, what they return

Use these figures when telling the owner what a run will cost and how long it takes. Token counts are subagent
tokens, not the lead's. Record your own runs in `local/skills/agent-orchestration/` and prefer them once you have some.

| Shape | Mechanism | Typical cost / time | What to expect |
|---|---|---|---|
| Persona "agent company" (CEO, engineer, CMO) on heartbeats | external heartbeat runner | ≈ $20 in an hour | ~90% spent by the manager agent; one deliverable; runs end on the usage limit |
| Explore-heavy implementation by subagents | SDD implementer subagents | — | implementers hang in a Read loop → do it inline, review read-only |
| One agent per module dir + integrator owning shared files | Workflow, 7 agents | resumable next day from cache | the agent on the most stateful module may die twice → lead writes it |
| Feature waves on a cheaper model, no architecture rule in the prompt | subagent waves | — | tests green, code without architecture → put the rules in every prompt |
| Risky tasks on the strongest model, mechanical on a cheaper one | SDD: implementer → spec-reviewer → quality-reviewer | 8 tasks merged the same day | works when slices are disjoint |
| 16 dispatches under a 4-hour deadline, 8 in parallel on disjoint files | SDD | **up to half stall** ("no progress for 600s") | finishes on time only if every brief names files + build + guards + screenshots |
| iOS and Android chains in two worktrees, review on every task | SDD | roughly halves wall clock | reviews catch bugs every implementer reported DONE |
| Audit: 8 lenses → merge → gap critic → 1 verifier per critical/high | Workflow | hours; can be cut for time and resumed | medium/low stay unverified — label them so |
| Parallel subagents + emulators on one laptop | subagents | — | the machine overheats → one build agent at a time |
| Ideation: 8 lenses × 7 concepts, 4 judges, top 20, critic, briefs → one design agent per concept | Workflow + subagents | **~300k tokens and 15–30 min per concept** | 20 concepts on boards; cap content in the brief or boards come out cluttered |
| Conclave: 4 roles, 3 rounds + red team | `workflows/conclave.js` | **~27 agents, ~7 min, ~3.4M tokens** | directional verdict with a confidence |

## Rules of thumb

- A conclave is ~3–4M tokens: only for decisions worth weeks of work. Small decisions: 3 roles, `rounds: 2`.
- A design subagent that builds 3 Figma phones is ~300k tokens. 20 of them ≈ 6M — say so before launching.
- Expect **up to half** of background subagents to stall on a long day. Plan the slice size for that.
- Org-chart agents spend money on talking to each other.
- Parallel builds are bounded by the machine, not the plan.
