#!/usr/bin/env python3
"""Set up local/ (git-ignored): your apps, IDs and keys.

The plugin's skills are generic. Everything specific to you lives in local/:
  local/apps.yaml      one block per app (links, bundle id, ASC / PostHog / RevenueCat / Figma ids)
  local/secrets.env    API keys and tokens (chmod 600)
  local/skills/<skill>/<app>.md   your own case notes, written by the skills as you work

  python3 scripts/setup.py                       # create local/ and add apps interactively
  python3 scripts/setup.py --check               # what is filled, what is empty; exit 1 if no apps
  python3 scripts/setup.py --add myapp name="My App" platforms=ios,android bundle_id=com.x.y
  python3 scripts/setup.py --set myapp.posthog_project_id=12345 shared.apple_ads_org_id=678
  python3 scripts/setup.py --get myapp.posthog_project_id
"""
import argparse
import os
import pathlib
import shutil
import stat
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
# HARNESS_LOCAL_DIR lets eval runs (and tests) use a throwaway folder instead of your real local/
LOCAL = pathlib.Path(os.environ.get("HARNESS_LOCAL_DIR") or ROOT / "local")
EXAMPLE = ROOT / "local.example"
APPS, SECRETS = LOCAL / "apps.yaml", LOCAL / "secrets.env"

TEMPLATE = yaml.safe_load((EXAMPLE / "apps.yaml").read_text())
FIELDS = list(TEMPLATE["apps"][0].keys())
SHARED = list(TEMPLATE.get("shared", {}).keys())
ASK = ["name", "platforms", "repo_path", "bundle_id", "app_store_url", "play_url", "site_url",
       "asc_app_id", "posthog_project_id", "revenuecat_project_id", "figma_file_key", "notes"]
HEADER = "# Your apps. Git-ignored. Format: local.example/apps.yaml\n"


def ensure_local():
    LOCAL.mkdir(exist_ok=True)
    (LOCAL / "skills").mkdir(exist_ok=True)
    if not SECRETS.exists():
        shutil.copy(EXAMPLE / "secrets.env", SECRETS)
    SECRETS.chmod(stat.S_IRUSR | stat.S_IWUSR)
    if not APPS.exists():
        save({"apps": [], "shared": {k: "" for k in SHARED}})


def load():
    data = yaml.safe_load(APPS.read_text()) if APPS.exists() else None
    data = data or {}
    data.setdefault("apps", [])
    data.setdefault("shared", {k: "" for k in SHARED})
    return data


def save(data):
    APPS.write_text(HEADER + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120))


def find(data, key):
    return next((a for a in data["apps"] if a.get("key") == key), None)


def coerce(field, value):
    if field == "platforms":
        return [p.strip() for p in value.split(",") if p.strip()]
    if field == "social":
        return dict(kv.split(":", 1) for kv in value.split(",") if ":" in kv)
    return value


def new_app(key):
    app = {f: ("" if not isinstance(TEMPLATE["apps"][0][f], (list, dict)) else type(TEMPLATE["apps"][0][f])())
           for f in FIELDS}
    app["key"] = key
    return app


def set_path(data, path, value):
    head, _, field = path.partition(".")
    if not field:
        sys.exit(f"use app.field or shared.field, got {path!r}")
    if head == "shared":
        data["shared"][field] = value
        return
    app = find(data, head)
    if app is None:
        sys.exit(f"no app {head!r}: add it first with --add {head}")
    if field not in FIELDS:
        sys.exit(f"unknown field {field!r}; fields: {', '.join(FIELDS)}")
    app[field] = coerce(field, value)


def check(data):
    if not data["apps"]:
        print("local/apps.yaml has no apps yet: run python3 scripts/setup.py")
        return 1
    for a in data["apps"]:
        empty = [f for f in ASK if not a.get(f)]
        notes = sorted(p.relative_to(LOCAL) for p in (LOCAL / "skills").glob(f"*/{a['key']}*.md"))
        print(f"{a['key']:12} {a.get('name') or '?':20} filled {len(ASK) - len(empty)}/{len(ASK)}"
              + (f"  empty: {', '.join(empty)}" if empty else "")
              + (f"\n{'':13}case notes: {', '.join(map(str, notes))}" if notes else ""))
    empty_shared = [k for k, v in data["shared"].items() if not v]
    if empty_shared:
        print(f"shared       empty: {', '.join(empty_shared)}")
    keys = [l.split("=", 1)[0] for l in SECRETS.read_text().splitlines()
            if "=" in l and not l.lstrip().startswith("#") and l.split("=", 1)[1].split("#")[0].strip()]
    print(f"secrets.env  {len(keys)} key(s) set" + (f": {', '.join(keys)}" if keys else ""))
    return 0


def interactive(data):
    print("Add your apps. Enter skips a field; an empty key finishes.\n")
    while True:
        try:
            key = input("app key (short, e.g. myapp): ").strip()
        except EOFError:
            break
        if not key:
            break
        app = find(data, key) or new_app(key)
        if app not in data["apps"]:
            data["apps"].append(app)
        for f in ASK:
            cur = app.get(f)
            v = input(f"  {f}{f' [{cur}]' if cur else ''}: ").strip()
            if v:
                app[f] = coerce(f, v)
        save(data)
    print("\nSaved local/apps.yaml. Keys go in local/secrets.env (see local.example/README.md).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--add", nargs="+", metavar=("KEY", "field=value"))
    ap.add_argument("--set", nargs="+", metavar="app.field=value")
    ap.add_argument("--get", metavar="app.field")
    a = ap.parse_args()

    if a.get:
        data = load()
        head, _, field = a.get.partition(".")
        src = data["shared"] if head == "shared" else (find(data, head) or {})
        v = src.get(field)
        if not v:
            sys.exit(f"{a.get} is empty: run python3 scripts/setup.py")
        print(",".join(v) if isinstance(v, list) else v)
        return

    ensure_local()
    data = load()
    if a.add:
        key, pairs = a.add[0], a.add[1:]
        app = find(data, key) or new_app(key)
        if app not in data["apps"]:
            data["apps"].append(app)
        for p in pairs:
            f, _, v = p.partition("=")
            set_path(data, f"{key}.{f}", v)
        save(data)
    if a.set:
        for p in a.set:
            path, _, v = p.partition("=")
            set_path(data, path, v)
        save(data)
    if a.check or a.add or a.set:
        sys.exit(check(load()) if a.check else 0)
    interactive(data)


if __name__ == "__main__":
    main()
