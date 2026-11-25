#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# WHAT IT DOES: runs one HogQL query against a PostHog project over the REST API and prints
#   the result as a tab-separated table. Use it when the PostHog MCP is not connected
#   (some connectors expose only render-ui, no exec). When the MCP IS connected, prefer it:
#   exec "switch-project <id>"  then  exec 'call execute-sql {"query": "..."}'.
# HOW TO RUN:
#   POSTHOG_PERSONAL_API_KEY=phx_... python3 hogql.py --app myapp query.sql
#   POSTHOG_PERSONAL_API_KEY=phx_... python3 hogql.py --project 123456 - <<'SQL'
#   select event, count() from events where timestamp > now() - interval 1 day group by event
#   SQL
# --app reads posthog_project_id from local/apps.yaml (scripts/setup.py --get <app>.posthog_project_id).
# --host defaults to US cloud (https://us.posthog.com); use https://eu.posthog.com for EU projects.
# The key is the owner's personal key (local/secrets.env); never write it to a file.
# ---------------------------------------------------------------------------
import argparse, json, os, subprocess, sys, urllib.request


def app_field(app, field):
    """Read <app>.<field> via scripts/setup.py --get, searching upwards for the repo root."""
    d = os.path.dirname(os.path.abspath(__file__))
    for start in (os.getcwd(), d):
        cur = start
        while True:
            setup = os.path.join(cur, "scripts", "setup.py")
            if os.path.exists(setup):
                out = subprocess.run([sys.executable, setup, "--get", f"{app}.{field}"],
                                     capture_output=True, text=True, cwd=cur)
                val = out.stdout.strip()
                if out.returncode == 0 and val:
                    return val
                sys.exit(f"{app}.{field} is empty: python3 scripts/setup.py --set {app}.{field}=...")
            if os.path.dirname(cur) == cur:
                break
            cur = os.path.dirname(cur)
    sys.exit("scripts/setup.py not found; pass --project <id>")


def main():
    ap = argparse.ArgumentParser(description="Run a HogQL query via the PostHog REST API")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--app", help="app key in local/apps.yaml")
    g.add_argument("--project", help="numeric PostHog project id")
    ap.add_argument("--host", default=os.environ.get("POSTHOG_HOST", "https://us.posthog.com"))
    ap.add_argument("sql", help="file with the query, or - for stdin")
    a = ap.parse_args()
    project = a.project or app_field(a.app, "posthog_project_id")
    sql = sys.stdin.read() if a.sql == "-" else open(a.sql).read()
    key = os.environ.get("POSTHOG_PERSONAL_API_KEY") or sys.exit("set POSTHOG_PERSONAL_API_KEY")
    req = urllib.request.Request(
        f"{a.host.rstrip('/')}/api/projects/{project}/query/",
        data=json.dumps({"query": {"kind": "HogQLQuery", "query": sql}}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = json.load(r)
    cols = body.get("columns") or []
    if cols:
        print("\t".join(cols))
    for row in body.get("results", []):
        print("\t".join("" if v is None else str(v) for v in row))


if __name__ == "__main__":
    main()
