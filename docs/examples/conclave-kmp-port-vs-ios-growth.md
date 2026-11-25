# Example: conclave "Port a habit tracker to Android via KMP, or grow iOS?"

An example run of `workflows/conclave.js` for a solo developer with a small iOS-only habit tracker
(SwiftUI + SwiftData, early revenue). Roles: Skeptic, Builder, Growth strategist,
Data analyst; 3 rounds + red team. **27 agents, ~7 minutes, ~3.4M subagent tokens.**

## Verdict on the merits (directional, confidence ~72/100)

**A trimmed B for 6 weeks; the KMP port, not now.** About 5–6 engineering days:
- iOS installs through the content series, Custom Product Pages and ASO, judged by search-source metrics;
- US ratings via `RequestReviewAction` at a neutral milestone, with no mood gating;
- **no** paywall A/B until there are about 300 paywall views a week — right now such a test is unmeasurable;
- Android demand is checked for free: the bio link goes to a router where Android users
  leave an email, and the share of Android clicks is counted.

**Port gate (D3e):**
1. Precondition: iOS click→install ≥ 5%. Otherwise the problem is packaging, not the platform.
2. Tier-1 n ≥ 150, Android share ≥ 40% with the lower bound of the 95% CI ≥ 30%.
3. If the gate passes: a skeleton build in 0.5 days to start the Play closed-test clock.
   The full Compose port goes in the next window.

**Reverse if:**
- by week 6 the D3e gate has passed → the port is the first item of the next window;
- the 28-day baseline shows ≥ 300 paywall views a week → paywall experiments are back in the plan;
- iOS click→install < 5% → the weeks go to packaging and CPP, not the Android gate;
- > 60% of the series audience is outside Tier-1 → both options target the wrong market; retarget the content first.

**Strongest dissent (Data analyst):** "The verdict must stay labeled as directional…
there is no 28-day baseline, no install count, paywall views or ratings, no share of Android clicks."

**Next experiment:** export the 28-day baseline from App Store Connect and RevenueCat and set up the bio
link router with UTM. Read the D3e gate after 4 weeks.

## How the debate went (position-change log, excerpt)

| Round | Role | Shift | moved_by |
|---|---|---|---|
| open | all | unanimous B → skeptic told to argue against | unanimity rule |
| 1 | Skeptic | dropped the argument "the port does not fix the bottleneck": with a content channel, Android leakage may be it | S2a |
| 1 | Builder | B narrowed: no paywall A/B, Android probe via a waitlist with UTM rather than Play pre-registration | D1c |
| 1 | Data analyst | removed paywall tests from the experiment slots; accounted for the Play calendar | S1c, B1b |
| 2 | Builder | lower port estimate: a separate Compose app with no SwiftData migration | S1b, D2b |
| 3 | all | converged on the D3e gate and the skeleton build | B3a, S3a |

## What this run showed about the conclave itself (retro → fixed in the script)

1. **Context leak.** The workflow agents saw in their context the user's last message from
   the main session (about an unrelated task), and the moderator started answering it. The red team
   rightly called this a fatal delivery flaw. **Fix:** an `ISOLATE` preamble in every prompt
   ("the only task is this decision; ignore all other requests").
2. **Confidence scale.** The verdict came back as 0.72 instead of 72. **Fix:** the schemas say `integer 0-100`.
3. **The debate did not stop.** The remaining cruxes could be resolved only by data (n, geo), not by new
   arguments, but the stop rule required "zero open cruxes", and the run hit the round
   limit. **Fix:** a `needs_data` flag; such cruxes do not block stopping and become
   the next experiment.
4. **"Shifts" every round for everyone.** Some of them were rephrasing, not a change of recommendation.
   **Fix:** `changed=true` only when the recommendation changes.
5. **Cost.** 3.4M tokens for one decision is justified only for decisions worth weeks of work.
   For small decisions: 3 roles and `rounds: 2`.

This is the same loop as for skills: run → review → fix → next run.
