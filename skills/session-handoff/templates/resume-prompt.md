<!--
TEMPLATE for the reply to "give me a prompt for a new session"; a handoff can also be written AS such a prompt
("Paste everything below into a fresh Claude Code session opened in <repo>").
Give it in a ```text block in the owner's language. ≤ 25 lines. It points at files; it does not
repeat them. Then, outside the block, list what he should add if he has decided it (open owner decisions).
-->
```text
Project <Name>: <absolute repo path> (<one-line what it is; stack; simulator/device>).
Open Claude Code in exactly this folder (memory is tied to the cwd).

Read first:
1. CLAUDE.md — project rules and pitfalls
2. <docs/…/HANDOFF-YYYY-MM-DD.md> — the handoff from the last session, in full
3. <spec / plan / ledger path> — <why>

State in brief: branch <branch> <green: N tests, build with no warnings>; <what is done>;
<what is in flight / unverified>. <Nothing is committed — the owner commits.>

Task: <the one next job>, steps are in the handoff's "Resume here" section. <The main point in one sentence.>

Work by the project rules: <skill to load first>, <test gate command>, <no worktrees / no commits if that is
the rule here>. Verify yourself; don't ask me to look at screenshots unless necessary.
```

Add to the prompt if decided:
- <open decision 1> (<what it unblocks>)
- <owner-only setup step> (<what it lets the next session do by itself>)
