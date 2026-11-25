<!--
The rules file every implementer subagent reads ONCE before its task brief. Dispatch prompt =
  "Read <path>/implementer-rules.md, then <path>/task-N-brief.md. Report file: <path>/task-N-report.md."
Edit only the commit line per project (some repos: commit + push per task; others: the owner commits, agents never do).
-->
# Implementer rules (read once, then your task brief)

## Your job
1. Implement exactly what the task brief specifies — the brief contains the exact code and values; use them verbatim.
2. Follow the brief's TDD order: write the failing test, RUN it and capture the failure, implement, RUN it and capture the pass.
3. **Do NOT commit, stage, stash, or switch branches. No `git add`, no `git commit`.** The owner commits. The working tree already holds unrelated uncommitted work — never touch, revert or "clean up" any file your brief does not name.
4. Self-review, then report.

If the brief's code does not compile or a test fails for a reason that is a defect in the brief itself (not a typo of yours), make the smallest fix that keeps the brief's intent and its public interface, and describe it precisely in your report under "Deviations from the brief". If the needed fix would change a public name/signature, a test expectation's meaning, or a constant from the brief — STOP and report BLOCKED instead.

While iterating run the focused test for what you change; run the wider suite once at the end.
Ask questions (report NEEDS_CONTEXT) rather than guess. It is always OK to say "this is too hard" (report BLOCKED) — bad work is worse than no work.

## Self-review before reporting
- Everything in the brief implemented? Nothing extra (YAGNI)?
- Test output pristine — no warnings from the files you created?
- Only the files the brief names were created/modified? (`git status --short` — compare against the brief.)

## Report
Write the full report to the report file named in your dispatch:
- What you implemented
- **TDD evidence** — RED: command + the relevant failing output and why it was expected; GREEN: command + passing output
- Files created/modified (exact paths)
- Deviations from the brief (exact before/after), or "none"
- Concerns, or "none"

Then reply with ONLY (under 12 lines):
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- One-line test summary (e.g. "7/7 passing, output pristine")
- Deviations/concerns in one line each, if any
- The report file path
If BLOCKED or NEEDS_CONTEXT, put the specifics in the reply itself.

## After review findings
You may be resumed with reviewer findings. Fix them, re-run the covering tests, append a "Fix round N" section to the same report file (what changed, command, output), and reply with the same short contract.
