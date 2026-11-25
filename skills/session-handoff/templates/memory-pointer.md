<!--
TEMPLATE for a project memory pointer (examples: ../references/memory-pointers.md).
Save to the memory dir of the repo the NEXT session will be opened in:
  ~/.claude/projects/<cwd with / replaced by ->/memory/<project>-handoff-YYYY-MM-DD.md
and add ONE line to that dir's MEMORY.md; relabel the previous handoff line "older: …".
Keep it ≤ 30 lines: the doc holds the detail, the pointer holds where + what not to redo.
-->
---
name: <project>-handoff-YYYY-MM-DD
description: "READ FIRST — <project> after the YYYY-MM-DD session: <state in ten words, incl. committed/deployed or not>; points at the on-disk handoff doc"
metadata:
  type: project
---

As of YYYY-MM-DD the branch `<branch>` <holds / has committed> <what>. <tests N, build green>.
<Nothing deployed / committed — the owner commits.>

The full state, the owner's checklist, the resume order and tooling facts are in
**`docs/<…>/HANDOFF-YYYY-MM-DD.md`** (<docs/ is git-ignored — on disk only>). It supersedes
[[<project>-handoff-<older>]] for <topic>; that note is still right about <what>.

**Why:** the owner asked for it («<his exact words>»), per [[save-context-and-handoff]].

**How to apply:** read the handoff doc before touching anything; don't redo <finished items>.
Next: <first resume step>. Still unverified, do not assume: <short list>.
Related: [[<design memory>]], [[<deadline/plan memory>]].
