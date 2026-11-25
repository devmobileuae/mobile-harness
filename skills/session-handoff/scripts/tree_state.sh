#!/usr/bin/env bash
# Why: handoffs that restate the tree from memory are wrong about branch, ahead/behind, untracked files and
#   what is committed ("Branch release/1.2, last commit abc1234, nothing committed", "main is 5 commits ahead
#   of origin/main"); measure it instead.
# PURPOSE: print the "State of the tree" block of a handoff as Markdown, measured NOW, so the handoff never
#   restates what the agent remembers. Read-only, except --patch which writes one file (the WIP diff).
# USAGE:
#   bash tree_state.sh [repo_dir] [--patch path/to/wip.patch] [--paths "backend/ AppKit/"]
#   --patch : also save `git diff HEAD` (tracked changes, staged + unstaged) to that file — do this when a
#             session is paused mid-task and the work is not committed (in repos where the owner commits himself).
#   --paths : count uncommitted changes per listed path, for trees that hold two bundles at once
#             (e.g. a new feature and a hotfix bundle uncommitted on the same branch).
#   Paste the output under "## State of the tree" and add test/build numbers you just ran yourself.
set -euo pipefail
REPO="."; PATCH=""; PATHS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --patch) PATCH="$2"; shift 2 ;;
    --paths) PATHS="$2"; shift 2 ;;
    *) REPO="$1"; shift ;;
  esac
done
cd "$REPO"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "not a git repo: $REPO"; exit 1; }

br=$(git branch --show-current || true); [ -z "$br" ] && br="(detached at $(git rev-parse --short HEAD))"
echo "_Measured $(date '+%Y-%m-%d %H:%M %Z') in \`$(pwd)\`_"
echo
echo "- Branch \`$br\`, last commit \`$(git log -1 --format='%h %s (%cd)' --date=short)\`"
tags=$(git tag --points-at HEAD | tr '\n' ' ')
[ -n "$tags" ] && echo "- Tags on HEAD: $tags"
up=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [ -n "$up" ]; then
  read -r behind ahead < <(git rev-list --left-right --count "$up...HEAD")
  echo "- vs \`$up\`: $ahead ahead, $behind behind (ahead > 0 = commits not pushed)"
else
  echo "- No upstream for this branch (never pushed)"
fi
for m in main master; do
  if git show-ref --verify --quiet "refs/heads/$m" && [ "$br" != "$m" ]; then
    read -r b a < <(git rev-list --left-right --count "$m...HEAD")
    echo "- vs local \`$m\`: $a ahead, $b behind"
    if git show-ref --verify --quiet "refs/remotes/origin/$m"; then
      read -r ob oa < <(git rev-list --left-right --count "origin/$m...$m")
      echo "- local \`$m\` vs \`origin/$m\`: $oa ahead, $ob behind"
    fi
    break
  fi
done
mod=$(git status --porcelain | grep -vc '^??' || true)
unt=$(git ls-files --others --exclude-standard | wc -l | tr -d ' ')
echo "- Uncommitted: $mod tracked file(s) changed, $unt untracked"
if [ "$mod" != "0" ] || [ "$unt" != "0" ]; then
  echo '  ```'; git status --short | head -40 | sed 's/^/  /'; n=$(git status --short | wc -l | tr -d ' ')
  [ "$n" -gt 40 ] && echo "  … $((n-40)) more"; echo '  ```'
fi
if [ -n "$PATHS" ]; then
  for p in $PATHS; do echo "  - \`$p\`: $(git status --porcelain -- "$p" | wc -l | tr -d ' ') changed"; done
fi
st=$(git stash list | wc -l | tr -d ' '); [ "$st" != "0" ] && { echo "- Stashes: $st"; git stash list | head -5 | sed 's/^/  - /'; }
wt=$(git worktree list | wc -l | tr -d ' ')
[ "$wt" -gt 1 ] && { echo "- Worktrees ($wt):"; git worktree list | sed 's/^/  - /'; }
for d in docs docs/superpowers .superpowers; do
  [ -e "$d" ] && git check-ignore -q "$d/HANDOFF-probe.md" 2>/dev/null && echo "- \`$d/\` is git-ignored: files there exist only on this disk -> memory pointer required"
done
if [ -n "$PATCH" ]; then
  mkdir -p "$(dirname "$PATCH")"; git diff HEAD > "$PATCH"
  echo "- WIP saved: \`$PATCH\` ($(wc -l < "$PATCH" | tr -d ' ') lines; untracked files are NOT in it)"
fi
