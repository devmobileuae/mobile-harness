#!/usr/bin/env python3
"""Block personal values from reaching a tracked file.

Two layers:
  1. Generic patterns (CI and locally): store/project id formats, Figma file URLs, worker hosts,
     home paths, private keys and tokens.
  2. Your own values (locally, when local/ exists): every value in local/apps.yaml and
     local/ids.yaml, and every line of local/private-terms.txt (app names, employer, handles).
     CI cannot see these, so run this as a pre-commit hook:  python3 scripts/check_private.py --install-hook

  python3 scripts/check_private.py            # check tracked + staged files, exit 1 on a hit
  python3 scripts/check_private.py --staged   # only files staged for commit (the hook uses this)
"""
import argparse
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCAL = ROOT / "local"
SKIP = re.compile(r"^(local/|local\.example/|\.github/|scripts/check_private\.py$|LICENSE$)")

PATTERNS = {
    "home path": r"/Users/[a-z][\w.-]+|(?:^|[\s\"'`(=])/home/[a-z][\w.-]+/",
    "private key": r"BEGIN (EC |RSA |OPENSSH )?PRIVATE KEY",
    "token": r"\b(ghp_|github_pat_|phc_|sk-|xox[bp]-|AKIA)[A-Za-z0-9_]{16,}",
    "RevenueCat id": r"\b(proj|ofrng)[0-9a-f]{8,}\b|\bapp[0-9a-f]{10}\b",
    "Vercel project id": r"\bprj_[A-Za-z0-9]{20,}",
    "Figma file url": r"figma\.com/(design|file|board)/[A-Za-z0-9]{20,}",
    "App Store app id": r"apps\.apple\.com/[^\s)\"']*/id(?!0{8,})\d{8,}|\bid(?!0{9,})\d{9,10}\b",
    "Cloudflare worker host": r"\b[\w-]+\.[\w-]+\.workers\.dev\b",
    "private-repo marker": r"(?i)private repo",
}


def tracked(staged):
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"] if staged else ["git", "ls-files"]
    files = subprocess.check_output(cmd, cwd=ROOT, text=True).splitlines()
    return [f for f in files if f and not SKIP.match(f) and (ROOT / f).is_file()]


def own_values():
    vals = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k not in ("key", "platforms", "notes", "name"):  # generic words, not secrets
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif x not in (None, "") and len(str(x)) >= 5 and not str(x).startswith("~"):
            vals.add(str(x))

    for f in ("apps.yaml", "ids.yaml"):
        p = LOCAL / f
        if p.exists():
            walk(yaml.safe_load(p.read_text()) or {})
    terms = LOCAL / "private-terms.txt"
    if terms.exists():
        vals |= {l.strip() for l in terms.read_text().splitlines() if l.strip() and not l.startswith("#")}
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--install-hook", action="store_true")
    a = ap.parse_args()
    if a.install_hook:
        hook = ROOT / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexec python3 scripts/check_private.py --staged\n")
        hook.chmod(0o755)
        print(f"installed {hook.relative_to(ROOT)}")
        return

    rx = {name: re.compile(p) for name, p in PATTERNS.items()}
    values = own_values()
    terms = [(v, re.compile(r"(?i)(?<![\w.])" + re.escape(v) + r"(?![\w])")) for v in sorted(values)]
    hits = []
    for f in tracked(a.staged):
        try:
            lines = (ROOT / f).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines, 1):
            for name, r in rx.items():
                if r.search(line):
                    hits.append(f"{f}:{i}: {name}")
            for v, r in terms:
                if r.search(line):
                    hits.append(f"{f}:{i}: your value from local/ ({v[:3]}…)")
    if hits:
        print("Personal values in tracked files (move them to local/, see local.example/README.md):")
        print("\n".join("  " + h for h in hits[:200]))
        sys.exit(1)
    print(f"check_private: OK ({len(values)} local values, {len(PATTERNS)} patterns)")


if __name__ == "__main__":
    main()
