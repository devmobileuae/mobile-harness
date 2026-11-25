---
arm: both
type: tool_order
before: 'Bash:git( -C \S+)? (status|log|branch|rev-list|rev-parse)|tree_state'
after: 'Write:HANDOFF'
---
Trajectory: the tree is measured with git (or tree_state.sh) before the HANDOFF file is written.
