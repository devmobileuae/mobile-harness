#!/usr/bin/env bash
# stall-check.sh — what did a stalled / silent subagent actually leave on disk?
#
# Why: when many subagents stall ("no progress for 600s") or a zombie `claude` loops xcodebuild and locks build.db,
#   the lead needs the state of each slice from disk, not from the transcript.
# Purpose: decide in one minute between "work is done, only the report is missing", "partial — finish inline",
#   and "nothing happened — re-dispatch narrower".
# Usage:
#   scripts/stall-check.sh <repo> [--report <report.md>] [--guard '<egrep regex>'] <file> [<file> ...]
# Example:
#   scripts/stall-check.sh ~/code/HabitApp \
#     --report .superpowers/sdd/<plan>/task-6-report.md \
#     --guard 'LinearGradient|RadialGradient|GlassCard|DSFont\.' \
#     HabitApp/Views/Calendar/CalendarView.swift HabitApp/Views/Calendar/MonthView.swift
# It never edits anything. Run the project's own build command afterwards (it is in the brief).
set -uo pipefail

[ $# -lt 2 ] && { sed -n '2,20p' "$0"; exit 2; }
REPO=$1; shift
REPORT=""; GUARD=""; FILES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --report) REPORT=$2; shift 2 ;;
    --guard)  GUARD=$2;  shift 2 ;;
    *) FILES+=("$1"); shift ;;
  esac
done
cd "$REPO" || exit 2
now=$(date +%s)

echo "== 1. Status of the slice's files (M = edited, ?? = new, blank = untouched)"
for f in "${FILES[@]}"; do
  st=$(git status --short -- "$f" 2>/dev/null | cut -c1-2)
  if [ -e "$f" ]; then
    age=$(( now - $(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f") ))
    printf '  [%-2s] %-70s last write %ss ago\n' "${st:-  }" "$f" "$age"
  else
    printf '  [--] %-70s MISSING\n' "$f"
  fi
done

echo; echo "== 2. Diff size per file"
git diff --stat -- "${FILES[@]}" 2>/dev/null | tail -n 20

echo; echo "== 3. Files OUTSIDE the slice changed in the last 30 min (an agent that strayed)"
git status --short | awk '{print $2}' | while read -r p; do
  [ -e "$p" ] || continue
  m=$(stat -f %m "$p" 2>/dev/null || stat -c %Y "$p")
  [ $(( now - m )) -lt 1800 ] || continue
  inslice=0; for f in "${FILES[@]}"; do [ "$p" = "$f" ] && inslice=1; done
  [ $inslice -eq 0 ] && echo "  $p"
done

if [ -n "$GUARD" ]; then
  echo; echo "== 4. Guard hits (should be 0 when the slice is done): /$GUARD/"
  grep -nE "$GUARD" "${FILES[@]}" 2>/dev/null | head -n 30 || true
  echo "  total: $(grep -cE "$GUARD" "${FILES[@]}" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')"
fi

echo; echo "== 5. Unfinished edits (merge markers, TODO-agent, truncated files)"
grep -nE '^(<<<<<<<|>>>>>>>)|TODO\(agent\)|FIXME\(agent\)' "${FILES[@]}" 2>/dev/null | head -n 10 || true

if [ -n "$REPORT" ]; then
  echo; echo "== 6. Report file"
  if [ -f "$REPORT" ]; then
    echo "  $(wc -l < "$REPORT") lines, status line: $(grep -m1 -i 'status' "$REPORT")"
  else
    echo "  NO REPORT — the agent stalled before writing it; judge by sections 1–5 + a build"
  fi
fi

echo; echo "== 7. Leftover agent processes (zombie builds lock DerivedData/build.db)"
pgrep -fl 'xcodebuild|gradle.*daemon|swift-build' 2>/dev/null | head -n 10 || echo "  none"
pgrep -fl 'claude .*--print|claude -p' 2>/dev/null | head -n 5 || true
echo
echo "Verdict guide: all files M + guards 0 + build green  -> DONE, write the ledger line yourself"
echo "               some files M, others blank            -> finish inline if <= 2 files, else re-dispatch ONLY the blank ones"
echo "               nothing changed                       -> re-dispatch narrower (1 file) or on another model; 2nd stall -> do it inline"
