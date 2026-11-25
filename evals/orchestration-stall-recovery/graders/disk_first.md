---
arm: both
type: llm
focus: final
---

PASS if, before deciding what to do with the slice, the answer tells the owner to check what the stalled worker left on disk: e.g. stop/kill the agent (and any leftover build process), then `git diff --stat` / `git status` on the five files, the worker's report file and the brief's grep guards, and run the build once to see whether the partial edits compile. The decision must be made from that disk state, not from the transcript.

FAIL if the answer decides (relaunch, split, finish) without first checking the files on disk and building, or only suggests reading the agent's transcript/logs.

Quote the step that inspects the disk state.
