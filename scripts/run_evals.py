#!/usr/bin/env python3
"""Local eval runner for this plugin — same case format as `claude plugin eval`.

Cases: evals/<case>/prompt.md (frontmatter: name, tags, runs, max_turns, allowed_tools, model)
       evals/<case>/graders/*.md (type: tool_used | regex | file_exists | llm; weight; arm)
Each case runs in two arms in a fresh temp dir via headless `claude -p`:
  WITH    --plugin-dir <this repo>
  WITHOUT no plugin (baseline)
Score per run = weighted share of graders passed (arm: with-only graders are skipped in WITHOUT).
Delta = WITH - WITHOUT. That delta is the skill's measured value.
pass@k = at least one of k WITH runs passed every grader ("can it do it at all");
pass^k = all k WITH runs passed every grader ("can I rely on it every time").
Graders: tool_used, tool_order (trajectory: before/after as "Tool" or "Tool:regex"), regex, file_exists, llm.

Usage:
  run_evals.py [--tag frame-qa ...] [--case 'glob'] [--runs N] [--votes 1] [-j 4]
               [--judge-model haiku] [--model <id>] [--no-baseline] [--out evals/results/<name>]
Note: user-level skills in ~/.claude/skills still load in both arms; the baseline is
"my normal setup without this plugin", not a clean model.
"""
import argparse
import concurrent.futures as cf
import fnmatch
import glob
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"


def parse_md(path):
    t = path.read_text()
    if t.startswith("---"):
        _, fm, body = t.split("---", 2)
        return yaml.safe_load(fm) or {}, body.strip()
    return {}, t.strip()


def load_cases(tags, case_glob):
    cases = []
    for d in sorted(p for p in EVALS.iterdir() if (p / "prompt.md").exists()):
        fm, body = parse_md(d / "prompt.md")
        fm.setdefault("name", d.name)
        if case_glob and not fnmatch.fnmatch(fm["name"], case_glob):
            continue
        if tags and not set(tags) & set(fm.get("tags", [])):
            continue
        graders = []
        for g in sorted((d / "graders").glob("*.md")):
            gfm, gbody = parse_md(g)
            gfm["name"], gfm["body"] = g.stem, gbody
            graders.append(gfm)
        cases.append({"dir": d, "fm": fm, "prompt": body, "graders": graders})
    return cases


def run_claude(prompt, cwd, plugin, fm, model):
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--max-turns", str(fm.get("max_turns", 10)), "--strict-mcp-config",
           "--no-session-persistence"]
    tools = fm.get("allowed_tools") or []
    if tools:
        cmd += ["--allowedTools", *tools]
    if plugin:
        cmd += ["--plugin-dir", str(ROOT)]
    if model or fm.get("model"):
        cmd += ["--model", model or fm["model"]]
    t0 = time.time()
    # never let a case touch the owner's real local/ (setup.py honours HARNESS_LOCAL_DIR)
    env = {**os.environ, "HARNESS_LOCAL_DIR": str(pathlib.Path(cwd) / "local")}
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env,
                       timeout=fm.get("timeout_seconds", 600))
    events = []
    for line in p.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    tool_calls, last, cost = [], "", 0.0
    got_result = any(e.get("type") == "result" for e in events)
    is_error = any(e.get("type") == "result" and e.get("is_error") for e in events)
    error = None
    if p.returncode != 0 or not got_result or is_error:
        error = f"claude exit {p.returncode}, result event {'present' if got_result else 'missing'}" \
                f"{', is_error' if is_error else ''}: {p.stderr[-300:].strip()}"
    for e in events:
        if e.get("type") == "assistant":
            for c in e.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    tool_calls.append({"name": c.get("name"), "input": json.dumps(c.get("input", {}), ensure_ascii=False)})
                elif c.get("type") == "text":
                    last = c.get("text", last)
        if e.get("type") == "result":
            last = e.get("result") or last
            cost = e.get("total_cost_usd", 0.0) or 0.0
    trace = "\n".join(f"[tool] {t['name']} {t['input'][:400]}" for t in tool_calls) + "\n[final]\n" + last
    return {"tool_calls": tool_calls, "last": last, "trace": trace, "cost": cost,
            "seconds": round(time.time() - t0, 1), "stderr": p.stderr[-500:], "error": error}


def judge(criteria, target_text, judge_model, votes):
    prompt = ("You are a strict eval grader. Apply the rubric to the agent output below. "
              "Answer with one line: VERDICT: PASS or VERDICT: FAIL, then one sentence of evidence.\n\n"
              f"RUBRIC:\n{criteria}\n\nAGENT OUTPUT:\n{target_text[:20000]}")
    passes, valid, notes = 0, 0, []
    for _ in range(votes):
        try:
            p = subprocess.run(["claude", "-p", prompt, "--model", judge_model, "--max-turns", "1",
                                "--strict-mcp-config", "--no-session-persistence", "--output-format", "json"],
                               capture_output=True, text=True, timeout=180)
            out = json.loads(p.stdout).get("result", "") if p.returncode == 0 else ""
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            out = ""
        verdict = re.search(r"VERDICT:\s*(PASS|FAIL)", out)
        if not verdict:
            notes.append(f"judge error: no verdict ({out.strip()[:120] or 'empty'})")
            continue
        valid += 1
        passes += verdict.group(1) == "PASS"
        notes.append(out.strip().splitlines()[-1][:200])
    # None = the judge itself failed; the caller reports it as an error, never as FAIL
    if valid == 0:
        return None, notes
    return passes * 2 > valid, notes


def grade(g, run, cwd, judge_model, votes):
    t = g.get("type")
    if t == "tool_used":
        pat = re.compile(g["input_match"]) if g.get("input_match") else None
        n = sum(1 for c in run["tool_calls"] if c["name"] == g["tool"] and (not pat or pat.search(c["input"])))
        lo, hi = g.get("min", 1), g.get("max", 10**9)
        return lo <= n <= hi, f"{g['tool']} matched {n}x (want {lo}..{hi if hi < 10**9 else '∞'})"
    if t == "tool_order":
        def first(spec):
            name, _, pat = spec.partition(":")
            rx = re.compile(pat) if pat else None
            for i, c in enumerate(run["tool_calls"]):
                if c["name"] == name and (not rx or rx.search(c["input"])):
                    return i
            return None
        b, a = first(g["before"]), first(g["after"])
        ok = b is not None and a is not None and b < a
        return ok, f"{g['before']} at {b}, {g['after']} at {a}"
    if t == "regex":
        text = run["trace"] if g.get("target") == "trace" else run["last"]
        n = len(re.findall(g["pattern"], text, re.I if "i" in g.get("flags", "") else 0))
        m = g.get("match", "contains")
        ok = n > 0 if m == "contains" else n == 0 if m == "not_contains" else n == int(str(m).split(":")[1])
        return ok, f"pattern hits {n}"
    if t == "file_exists":
        hits = glob.glob(str(pathlib.Path(cwd) / g["path"]))
        ok = bool(hits) == g.get("exists", True)
        return ok, f"{len(hits)} file(s) match {g['path']}"
    if t == "llm":
        # focus: trace (default) = tool calls + final answer; final = only the final answer
        text = run["last"] if g.get("focus") == "final" else run["trace"]
        return judge(g["body"], text, judge_model, votes)
    return False, f"unknown grader type {t}"


def run_case_arm(case, arm, a):
    results = []
    for i in range(a.runs or case["fm"].get("runs", 1)):
        with tempfile.TemporaryDirectory(prefix=f"eval-{case['fm']['name']}-") as cwd:
            subprocess.run(["git", "init", "-q"], cwd=cwd)
            run = run_claude(case["prompt"], cwd, arm == "with", case["fm"], a.model)
            if run["error"]:
                # A crashed run is infra, not signal: never grade it (a negative case would
                # otherwise score 1.0 on "no tool calls").
                results.append({"run": i + 1, "score": None, "error": run["error"], "graders": [],
                                "cost": run["cost"], "seconds": run["seconds"], "final": run["last"][:500]})
                continue
            total = got = 0.0
            verdicts = []
            for g in case["graders"]:
                if arm == "without" and g.get("arm", "with-only") == "with-only":
                    continue
                ok, note = grade(g, run, cwd, a.judge_model, a.votes)
                if ok is None:
                    verdicts.append({"grader": g["name"], "pass": None, "note": note})
                    continue
                w = float(g.get("weight", 1))
                total += w
                got += w if ok else 0
                verdicts.append({"grader": g["name"], "pass": ok, "note": note})
            judge_errors = [v["grader"] for v in verdicts if v["pass"] is None]
            if judge_errors:
                results.append({"run": i + 1, "score": None, "error": f"judge failed on {', '.join(judge_errors)}",
                                "graders": verdicts, "cost": run["cost"], "seconds": run["seconds"],
                                "final": run["last"][:500]})
                continue
            results.append({"run": i + 1, "score": round(got / total, 3) if total else None,
                            "graders": verdicts, "cost": run["cost"], "seconds": run["seconds"],
                            "final": run["last"][:1500],
                            "skills": [c["input"] for c in run["tool_calls"] if c["name"] == "Skill"]})
    return results


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", nargs="*", default=[])
    ap.add_argument("--case", default=None)
    ap.add_argument("--runs", type=int, default=None)
    ap.add_argument("--votes", type=int, default=1)
    ap.add_argument("-j", type=int, default=4)
    ap.add_argument("--judge-model", default="haiku")
    ap.add_argument("--model", default=None)
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cases = load_cases(a.tag, a.case)
    if not cases:
        sys.exit("no cases matched")
    arms = ["with"] if a.no_baseline else ["with", "without"]
    jobs = {}
    with cf.ThreadPoolExecutor(max_workers=a.j) as ex:
        for c in cases:
            for arm in arms:
                jobs[ex.submit(run_case_arm, c, arm, a)] = (c["fm"]["name"], arm)
        out = {}
        for f in cf.as_completed(jobs):
            name, arm = jobs[f]
            try:
                out.setdefault(name, {})[arm] = f.result()
            except Exception as e:  # noqa: BLE001
                out.setdefault(name, {})[arm] = [{"error": repr(e), "score": None}]
            print(f"  done {name} [{arm}]", flush=True)

    rows, cost = [], 0.0
    passk = {}
    for c in cases:
        n = c["fm"]["name"]
        w = mean(r.get("score") for r in out[n].get("with", []))
        wo = mean(r.get("score") for r in out[n].get("without", [])) if "without" in out[n] else None
        cost += sum(r.get("cost", 0) for arm in out[n].values() for r in arm)
        rows.append((n, w, wo, None if w is None or wo is None else round(w - wo, 3)))
        runs_w = [r.get("score") for r in out[n].get("with", [])]
        k = len(runs_w)
        errs = {arm: sum(1 for r in out[n].get(arm, []) if r.get("error")) for arm in arms}
        # a run passes only if every grader passed (score 1.0); an errored run is never a pass,
        # so pass^k is false whenever any WITH run crashed
        passk[n] = {"k": k, "errors": errs,
                    "pass@k": any(s == 1.0 for s in runs_w),
                    "pass^k": k > 0 and all(s == 1.0 for s in runs_w)}

    print("\n| case | WITH | W/OUT | Δ | pass@k | pass^k | errors (with/without) |\n|---|---|---|---|---|---|---|")
    for n, w, wo, d in rows:
        pk = passk[n]
        e = pk["errors"]
        err = f"{e.get('with', 0)}/{e.get('without', '-')}" if any(e.values()) else ""
        print(f"| {n} | {w if w is not None else 'ERR'} | {wo if wo is not None else ('ERR' if e.get('without') else '-')} "
              f"| {d if d is not None else '-'} | {'✓' if pk['pass@k'] else '✗'} | {'✓' if pk['pass^k'] else '✗'} (k={pk['k']}) | {err} |")
    overall = mean(r[1] for r in rows)
    deltas = [r[3] for r in rows if r[3] is not None]
    rel = sum(1 for v in passk.values() if v["pass^k"])
    n_err = sum(sum(v["errors"].values()) for v in passk.values())
    print(f"\noverall WITH {overall}  mean Δ {mean(deltas)}  pass^k {rel}/{len(passk)} cases  cost ${cost:.2f}"
          + (f"  ⚠ {n_err} errored run(s) excluded from scores; rerun them" if n_err else ""))

    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = pathlib.Path(a.out or EVALS / "results" / stamp)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "aggregate-result.json").write_text(json.dumps(
        {"overallScore": overall, "meanDelta": mean(deltas), "costUsd": round(cost, 2),
         "passK": passk,
         "cases": [{"name": n, "with": w, "without": wo, "delta": d, "passAtK": passk[n]["pass@k"], "passPowK": passk[n]["pass^k"], "runs": out[n]} for n, w, wo, d in rows]},
        ensure_ascii=False, indent=1))
    print(f"results: {dest}/aggregate-result.json")


if __name__ == "__main__":
    main()
