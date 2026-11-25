#!/usr/bin/env python3
"""Freshness / provenance gate for skills (run in CI and in the monthly audit).

Fails (exit 1) when:
  - a skills/<name>/SKILL.md is not in skills/registry.yaml
  - a registry entry has fewer than MIN_POSITIVE matching positive eval cases in evals/
    (positive = a case whose graders require the skill to fire; negatives with max: 0 do not count)
  - `reviewed` is older than MAX_AGE_DAYS (time bomb, like a stale feature flag)
  - a SKILL.md exceeds MAX_LINES
Usage: check_registry.py [--today YYYY-MM-DD] [--max-age 90]
"""
import argparse
import datetime as dt
import fnmatch
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_LINES = 500
MIN_POSITIVE = 2


def is_positive(case_dir):
    for g in (case_dir / "graders").glob("*.md"):
        txt = g.read_text()
        if txt.startswith("---"):
            fm = yaml.safe_load(txt.split("---", 2)[1]) or {}
            if fm.get("type") == "tool_used" and fm.get("tool") == "Skill" and fm.get("max", 1) != 0:
                return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=dt.date.today().isoformat())
    ap.add_argument("--max-age", type=int, default=90)
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today)

    reg = yaml.safe_load((ROOT / "skills/registry.yaml").read_text()) or {}
    skills = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
    cases = sorted(p.name for p in (ROOT / "evals").iterdir() if p.is_dir() and p.name != "results")
    problems, rows = [], []

    for s in skills:
        lines = len((ROOT / "skills" / s / "SKILL.md").read_text().splitlines())
        if s not in reg:
            problems.append(f"{s}: not in registry.yaml")
            continue
        e = reg[s]
        reviewed = e.get("reviewed")
        reviewed = reviewed if isinstance(reviewed, dt.date) else dt.date.fromisoformat(str(reviewed))
        age = (today - reviewed).days
        matched = [c for c in cases for g in e.get("evals", []) if fnmatch.fnmatch(c, g)]
        if age > a.max_age:
            problems.append(f"{s}: reviewed {age} days ago (> {a.max_age}) — run skill-audit")
        positive = [c for c in set(matched) if is_positive(ROOT / "evals" / c)]
        if len(positive) < MIN_POSITIVE:
            problems.append(f"{s}: {len(positive)} positive eval case(s) match {e.get('evals')}, need {MIN_POSITIVE}")
        if not e.get("born_from"):
            problems.append(f"{s}: born_from is empty — why does this skill exist?")
        if lines > MAX_LINES:
            problems.append(f"{s}: {lines} lines > {MAX_LINES}")
        rows.append(f"{s:26} reviewed {age:>3}d ago  evals {len(set(matched)):>2} (positive {len(positive)})  lines {lines:>3}")

    for k in reg:
        if k not in skills:
            problems.append(f"{k}: in registry but skills/{k}/SKILL.md is missing")

    print("\n".join(rows))
    if problems:
        print("\nFAIL")
        print("\n".join("  - " + p for p in problems))
        sys.exit(1)
    print("\nOK")


if __name__ == "__main__":
    main()
