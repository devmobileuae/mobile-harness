#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# READ-ONLY review-status check: never POST/PATCH/DELETE. Useful during a long review wait.
# RUN:
#   python3 scripts/asc_status.py --app <key>            # bundle_id from local/apps.yaml
#   python3 scripts/asc_status.py --bundle com.example.app
# CREDS: same as asc.py (ASC_* env vars from local/secrets.env, or --config <json>).
# PRINTS: each version + appStoreState, each review submission + state + decoded items.
# Review-submission item ids are base64 of "{submissionId}|{typeCode}|{objectId}";
# type 6 = app version, 17 = subscription group, 18 = subscription, 19 = IAP
# (the API exposes no relationships on those items).
# ---------------------------------------------------------------------------
import argparse, base64, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asc import ASC, load_creds, resolve_bundle  # noqa: E402

TYPES = {"6": "appVersion", "17": "subscriptionGroup", "18": "subscription", "19": "iap"}


def decode(item_id):
    try:
        raw = base64.b64decode(item_id + "=" * (-len(item_id) % 4)).decode()
        sub, typ, obj = raw.split("|")
        return f"{TYPES.get(typ, typ)} {obj}"
    except Exception:
        return item_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", help="app key in local/apps.yaml")
    ap.add_argument("--bundle", help="bundle id (instead of --app)")
    ap.add_argument("--config", help="JSON creds {issuerId,keyId,p8} instead of ASC_* env vars")
    a = ap.parse_args()
    asc = ASC(load_creds(a.config))
    app = asc.get("/apps", params={"filter[bundleId]": resolve_bundle(a)})["data"][0]
    print("app", app["id"], app["attributes"]["name"])
    for v in asc.get(f"/apps/{app['id']}/appStoreVersions", params={"limit": 5})["data"]:
        at = v["attributes"]
        print(f"  version {at['versionString']:8} {at['appStoreState']:24} release={at.get('releaseType')}")
    subs = asc.get("/reviewSubmissions", params={"filter[app]": app["id"], "limit": 5})["data"]
    for s in subs:
        at = s["attributes"]
        print(f"  submission {s['id'][:8]} {at.get('state'):22} submitted={at.get('submittedDate')}")
        for it in asc.get(f"/reviewSubmissions/{s['id']}/items")["data"]:
            print(f"      {it['attributes'].get('state'):20} {decode(it['id'])}")


if __name__ == "__main__":
    main()
