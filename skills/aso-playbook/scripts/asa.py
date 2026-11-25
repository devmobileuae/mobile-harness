#!/usr/bin/env python3
"""Apple Ads through the Apple Ads Platform API (https://api.ads.apple.com/v1).

The older Campaign Management API (api.searchads.apple.com/api/v5) is sunset on 2027-01-26, so
this script talks to the Platform API only. Docs: developer.apple.com/documentation/apple-ads-platform-api

Everything app-specific lives in a plan folder (default ./asa, or --plan-dir):
    plan.json          {"prefix": "MYAPP_", "bid_currency": "USD", "device": "IPHONE",
                        "tiers": {"t1": [{"name": "MYAPP_T1_US_BRAND", "countries": ["US"], "daily": "5.00",
                                          "adgroups": [{"name": "ag_brand", "bid": "0.80", "keywords": "brand"}]}]}}
                       (template: templates/asa-plan.example.json; "later": true skips an ad group until --with-head)
    keywords-<name>.txt  one exact keyword per line; keywords-negative-broad.txt / keywords-negative-exact.txt
    config.json        clientId, teamId, keyId, privateKey path (git-ignored; templates/apple-ads-config.example.json)

    python3 asa.py --app myapp plan                 # what would be created, no network
    python3 asa.py --app myapp whoami               # token works? which ad accounts?
    python3 asa.py --app myapp create               # campaigns from the plan, PAUSED
    python3 asa.py --app myapp create --dry-run     # print the requests instead of sending them
    python3 asa.py --app myapp status               # campaigns, ad groups, keyword counts
    python3 asa.py --app myapp popularity           # Apple's own search popularity for the plan's keywords
    python3 asa.py --app myapp report --days 7      # keywords and search terms, also saved as CSV
    python3 asa.py --app myapp enable --yes         # starts spending: only on the owner's word
    python3 asa.py --app myapp pause

--app reads asc_app_id from local/apps.yaml (scripts/setup.py --get <app>.asc_app_id); or pass --adam-id.
"""
import argparse
import csv
import datetime as dt
import json
import sys
import time
from pathlib import Path

HERE = Path.cwd() / "asa"      # plan folder; set from --plan-dir in main()
CONFIG = HERE / "config.json"
API = "https://api.ads.apple.com/v1"
TOKEN_URL = "https://appleid.apple.com/auth/oauth2/token"


def _app_field(app, field):
    """<app>.<field> from local/apps.yaml via scripts/setup.py --get, searching upwards for the repo root."""
    import subprocess
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        for d in (start, *start.parents):
            setup = d / "scripts" / "setup.py"
            if setup.exists():
                out = subprocess.run([sys.executable, str(setup), "--get", f"{app}.{field}"],
                                     capture_output=True, text=True, cwd=d)
                if out.returncode == 0 and out.stdout.strip():
                    return out.stdout.strip()
                sys.exit(f"{app}.{field} is empty: python3 scripts/setup.py --set {app}.{field}=...")
    sys.exit("scripts/setup.py not found; pass --adam-id")


ADAM_ID = None        # the app's App Store id, set in main()
BID_CURRENCY = "USD"  # overridden by plan.json "bid_currency"
DEVICE = "IPHONE"     # plan.json "device": IPHONE for iPhone-only apps, or IPAD / both via a list
PREFIX = ""           # plan.json "prefix": only campaigns whose name starts with it are touched
PLAN = {}             # plan.json "tiers"


def load_plan():
    global BID_CURRENCY, DEVICE, PREFIX, PLAN
    f = HERE / "plan.json"
    if not f.exists():
        sys.exit(f"No {f}. Copy templates/asa-plan.example.json there and edit it.")
    p = json.loads(f.read_text())
    BID_CURRENCY, DEVICE, PREFIX, PLAN = p.get("bid_currency", "USD"), p.get("device", "IPHONE"), p["prefix"], p["tiers"]
    if not PREFIX:
        sys.exit("plan.json needs a non-empty prefix (it scopes status/pause/enable to your campaigns)")


NEGATIVES = [("negative-broad", "BROAD"), ("negative-exact", "EXACT")]


def keywords(name):
    """The lines of keywords-<name>.txt, in file order."""
    return [line.strip() for line in (HERE / f"keywords-{name}.txt").read_text().splitlines() if line.strip()]


def money(amount):
    return {"amount": amount, "currency": BID_CURRENCY}


# --- request bodies, kept apart from the network code so `plan` and the tests can use them ---------

def campaign_body(c, ad_account_id, status="PAUSED"):
    return {
        "name": c["name"],
        "adAccountId": ad_account_id,
        "billingEvent": "TAPS",
        "promotedObjectType": "APPSTORE_APP",
        "promotedObjectId": ADAM_ID,
        "dailyBudget": {"value": money(c["daily"])},
        "targeting": {
            "supplySource": {"include": ["APPSTORE"]},
            "supplyPlacement": {"include": ["APPSTORE_SEARCH_RESULTS"]},
            "countryOrRegion": {"include": c["countries"]},
        },
        "bidStrategy": {"bidStrategyType": "MANUAL_CPT", "bidStrategyGoal": "TAP"},
        "status": status,
    }


def adgroup_body(g, campaign_id, start):
    return {
        "campaignId": campaign_id,
        "name": g["name"],
        "pricingModel": "CPT",
        "bidStrategy": {"bidStrategyType": "MANUAL_CPT", "bidStrategyGoal": "TAP", "bid": money(g["bid"])},
        # Search Match off: exact keywords only.
        "automatedKeywordsOptIn": False,
        "status": "ENABLED",
        "startTime": start,
        "targeting": {
            "deviceClass": {"include": DEVICE if isinstance(DEVICE, list) else [DEVICE]},
            "appDownloader": {"exclude": [ADAM_ID]},  # new users: skip people who already have the app
        },
    }


def keyword_items(adgroup_id, words):
    return [{"correlationId": i, "data": {"adGroupId": adgroup_id, "text": w, "matchType": "EXACT", "status": "ENABLED"}}
            for i, w in enumerate(words)]


def negative_items(campaign_id, words, match):
    return [{"correlationId": i, "data": {"campaignId": campaign_id, "text": w, "matchType": match, "status": "ENABLED"}}
            for i, w in enumerate(words)]


def planned(tier, with_head):
    """The campaigns of a tier with the ad groups that are due now."""
    out = []
    for c in PLAN[tier]:
        groups = [g for g in c["adgroups"] if with_head or not g.get("later")]
        out.append({**c, "adgroups": groups})
    return out


# --- network ---------------------------------------------------------------------------------------

class Ads:
    def __init__(self, cfg, dry_run=False):
        self.cfg, self.dry_run = cfg, dry_run
        self._token, self._expires = None, 0
        self.ad_account_id = cfg.get("adAccountId")

    def token(self):
        if self._token and time.time() < self._expires - 60:
            return self._token
        import jwt
        import requests
        now = int(time.time())
        key = Path(self.cfg["privateKey"]).expanduser().read_text()
        secret = jwt.encode({"sub": self.cfg["clientId"], "aud": "https://appleid.apple.com", "iat": now,
                             "exp": now + 3600, "iss": self.cfg["teamId"]},
                            key, algorithm="ES256", headers={"kid": self.cfg["keyId"]})
        r = requests.post(TOKEN_URL, headers={"Content-Type": "application/x-www-form-urlencoded"},
                          data={"grant_type": "client_credentials", "client_id": self.cfg["clientId"],
                                "client_secret": secret, "scope": "searchadsorg"}, timeout=30)
        if r.status_code != 200:
            sys.exit(f"Token request failed ({r.status_code}): {r.text[:400]}")
        body = r.json()
        self._token, self._expires = body["access_token"], time.time() + int(body.get("expires_in", 3600))
        return self._token

    def call(self, method, path, body=None, scoped=True):
        if self.dry_run and method != "GET" and not path.endswith("/query"):
            print(f"DRY {method} {path}\n{json.dumps(body, indent=2)[:1200]}")
            return {"result": {"id": 0}}
        import requests
        headers = {"Authorization": f"Bearer {self.token()}"}
        if scoped:
            headers["X-AP-Context"] = f"adAccountId={self.ad_account_id}"
        for attempt in range(5):
            r = requests.request(method, API + path, headers=headers, json=body, timeout=60)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", 2 ** attempt)))
                continue
            break
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:800]}")
        return r.json() if r.text else {}

    def query(self, path, filters=None, page=1000):
        """Every row of a /query endpoint."""
        rows, offset = [], 0
        while True:
            res = self.call("POST", path + "/query", {"filters": filters or [], "pagination": {"offset": offset, "pageSize": page}})
            got = res.get("result") or []
            rows += got
            if len(got) < page:
                return rows
            offset += page

    def pick_account(self):
        """Uses adAccountId from the config, or the only ad account the token can see."""
        if self.ad_account_id:
            return self.ad_account_id
        acls = self.call("GET", "/acls", scoped=False)["result"]["acls"]
        if len(acls) != 1:
            names = ", ".join(f'{a["adAccount"]["id"]} {a["adAccount"]["name"]}' for a in acls) or "none"
            sys.exit(f"Set adAccountId in {CONFIG.name}. Ad accounts visible to this key: {names}")
        self.ad_account_id = acls[0]["adAccount"]["id"]
        return self.ad_account_id


def load_config():
    if not CONFIG.exists():
        sys.exit(f"No {CONFIG}. Copy config.example.json to config.json and fill in clientId, teamId and keyId.")
    cfg = json.loads(CONFIG.read_text())
    missing = [k for k in ("clientId", "teamId", "keyId", "privateKey") if not cfg.get(k) or "PASTE" in str(cfg[k])]
    if missing:
        sys.exit(f"{CONFIG.name} is missing: {', '.join(missing)}")
    return cfg


# --- commands --------------------------------------------------------------------------------------

def cmd_plan(args):
    total_daily = 0.0
    for c in planned(args.tier, args.with_head):
        total_daily += float(c["daily"])
        print(f'{c["name"]}  ${c["daily"]}/day  {", ".join(c["countries"])}  search results, created PAUSED')
        for g in c["adgroups"]:
            words = keywords(g["keywords"])
            print(f'   {g["name"]:12} max CPT ${g["bid"]}  {len(words):3} exact keywords  iPhone, new users, Search Match off')
        for name, match in NEGATIVES:
            print(f'   negatives    {len(keywords(name)):3} {match.lower()}')
    print(f"Daily budget in total: ${total_daily:.2f}  (${total_daily * 7:.2f} a week if it all spends)")


def cmd_whoami(args):
    ads = Ads(load_config())
    me = ads.call("GET", "/me", scoped=False)["result"]
    print(f'userId {me.get("userId")}  orgId {me.get("orgId")}')
    for a in ads.call("GET", "/acls", scoped=False)["result"]["acls"]:
        acc = a["adAccount"]
        ads.ad_account_id = acc["id"]
        d = ads.call("GET", f'/ad-accounts/{acc["id"]}')["result"]
        print(f'adAccount {acc["id"]}  {acc.get("name")}  roles {a.get("roles")}  {d.get("currency")} {d.get("timezone")} '
              f'{d.get("paymentModel")} {d.get("systemStatus")} {d.get("systemStatusReasons") or ""} features {d.get("productFeatures")}')


def cmd_create(args):
    ads = Ads(load_config(), dry_run=args.dry_run)
    account = ads.pick_account()
    info = ads.call("GET", f"/ad-accounts/{account}")["result"]
    if info.get("currency") != BID_CURRENCY:
        sys.exit(f'The ad account bills in {info.get("currency")}, the plan is in {BID_CURRENCY}. Stopping.')
    existing = {c["name"]: c for c in ads.query("/campaigns")}
    start = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")
    for c in planned(args.tier, args.with_head):
        if c["name"] in existing:
            camp = existing[c["name"]]
            print(f'= campaign {c["name"]} exists (id {camp["id"]}, {camp.get("status")})')
        else:
            camp = ads.call("POST", "/campaigns", campaign_body(c, account))["result"]
            print(f'+ campaign {c["name"]} id {camp["id"]} PAUSED ${c["daily"]}/day')
        cid = camp["id"]

        have_neg = {(n["text"].lower(), n["matchType"]) for n in ads.query("/negative-keywords", [{"field": "campaignId", "operator": "EQUALS", "value": cid}])} if cid else set()
        for name, match in NEGATIVES:
            words = [w for w in keywords(name) if (w.lower(), match) not in have_neg]
            if words:
                bulk(ads, "/negative-keywords/bulk-create", negative_items(cid, words, match), f"negatives {match.lower()}")

        groups = {g["name"]: g for g in ads.query("/adgroups", [{"field": "campaignId", "operator": "EQUALS", "value": cid}])} if cid else {}
        for g in c["adgroups"]:
            if g["name"] in groups:
                gid = groups[g["name"]]["id"]
                print(f'  = ad group {g["name"]} exists (id {gid})')
            else:
                gid = ads.call("POST", "/adgroups", adgroup_body(g, cid, start))["result"]["id"]
                print(f'  + ad group {g["name"]} id {gid} max CPT ${g["bid"]}')
            have = {k["text"].lower() for k in ads.query("/keywords", [{"field": "adGroupId", "operator": "EQUALS", "value": gid}])} if gid else set()
            words = [w for w in keywords(g["keywords"]) if w.lower() not in have]
            if words:
                bulk(ads, "/keywords/bulk-create", keyword_items(gid, words), f'keywords for {g["name"]}')
    print("Done. Campaigns are PAUSED: nothing spends until they are enabled.")


def bulk(ads, path, items, label):
    res = ads.call("POST", path, {"allowPartialSuccess": True, "items": items})
    if ads.dry_run:
        print(f"    ({len(items)} {label})")
        return
    results = res.get("result") or []
    failed = [(items[r["correlationId"]]["data"]["text"], (r.get("error") or {})) for r in results if not r.get("success")]
    print(f"    + {len(results) - len(failed)} of {len(items)} {label}")
    for text, err in failed:
        print(f"      ! {text}: {json.dumps(err)[:200]}")


def our_campaigns(ads):
    return [c for c in ads.query("/campaigns") if c["name"].startswith(PREFIX)]


def cmd_status(args):
    ads = Ads(load_config())
    ads.pick_account()
    for c in our_campaigns(ads):
        budget = ((c.get("dailyBudget") or {}).get("value") or {})
        print(f'{c["name"]}  id {c["id"]}  {c.get("status")} / {c.get("displayStatus") or c.get("systemStatus")}  '
              f'{budget.get("amount")} {budget.get("currency")}/day')
        for g in ads.query("/adgroups", [{"field": "campaignId", "operator": "EQUALS", "value": c["id"]}]):
            n = len(ads.query("/keywords", [{"field": "adGroupId", "operator": "EQUALS", "value": g["id"]}]))
            bid = ((g.get("bidStrategy") or {}).get("bid") or {}).get("amount")
            print(f'   {g["name"]:12} id {g["id"]}  {g.get("status")}  max CPT {bid}  keywords {n}  Search Match {g.get("automatedKeywordsOptIn")}')


def set_status(args, status):
    ads = Ads(load_config())
    ads.pick_account()
    for c in our_campaigns(ads):
        if args.tier and not c["name"].startswith(f"{PREFIX}{args.tier.upper()}_"):
            continue
        ads.call("PUT", f'/campaigns/{c["id"]}', {"status": status})
        print(f'{c["name"]} -> {status}')


def cmd_enable(args):
    if not args.yes:
        sys.exit("Enabling starts spending the daily budgets. Run again with --yes once the owner has said so.")
    set_status(args, "ENABLED")


def cmd_pause(args):
    set_status(args, "PAUSED")


def cmd_popularity(args):
    """Apple's search popularity (1-100 across all genres) for every keyword in the plan."""
    ads = Ads(load_config())
    ads.pick_account()
    words = sorted({w for t in PLAN.values() for c in t for g in c["adgroups"] for w in keywords(g["keywords"])})
    end = dt.date.today().replace(day=1) - dt.timedelta(days=1)  # last full month
    body = {"timeRange": {"start": end.replace(day=1).isoformat(), "end": end.isoformat(), "granularity": "MONTHLY"},
            "filters": [{"field": "countryOrRegion", "operator": "EQUALS", "value": args.country},
                        {"field": "searchTerm", "operator": "IN", "value": words}],
            "fields": ["searchTerm", "genre", "rankInGenre", "searchPopularity1to100", "searchPopularity1to5"],
            "pagination": {"offset": 0, "pageSize": 5000}}
    try:
        res = ads.call("POST", "/insights/apps/search-term-popularity/query", body)
    except RuntimeError:
        # The request schema does not list `fields`; if the API refuses it, ask for the default columns.
        body.pop("fields")
        res = ads.call("POST", "/insights/apps/search-term-popularity/query", body)
    rows = (res.get("result") or {}).get("rows") or []
    best = {}
    for r in rows:
        t = r["searchTerm"].lower()
        if t not in best or (r.get("searchPopularity1to100") or 0) > (best[t].get("searchPopularity1to100") or 0):
            best[t] = r
    for t, r in sorted(best.items(), key=lambda kv: -(kv[1].get("searchPopularity1to100") or 0)):
        print(f'{r.get("searchPopularity1to100") or "":>4}  {r.get("searchPopularity1to5") or "":>2}/5  #{r.get("rankInGenre")} in {r.get("genre")}  {t}')
    missing = [w for w in words if w.lower() not in best]
    print(f"\n{len(best)} of {len(words)} keywords are in Apple's top lists for {args.country} ({end:%Y-%m}).")
    print("Not listed (under 500 searches a month or outside the top 500 of a genre): " + ", ".join(missing))


def cmd_report(args):
    ads = Ads(load_config())
    ads.pick_account()
    end = dt.date.today()
    start = end - dt.timedelta(days=args.days - 1)
    out_dir = HERE / "reports"
    out_dir.mkdir(exist_ok=True)
    kw_rows, st_rows = [], []
    groups = {}
    for c in our_campaigns(ads):
        for g in ads.query("/adgroups", [{"field": "campaignId", "operator": "EQUALS", "value": c["id"]}]):
            groups[g["id"]] = g["name"]
        body = {"timeRange": {"start": start.isoformat(), "end": end.isoformat(), "timeZone": "ORTZ"},
                "filters": [{"field": "campaignId", "operator": "EQUALS", "value": c["id"]}],
                "pagination": {"offset": 0, "pageSize": 5000}}
        for kind, rows in (("keywords", kw_rows), ("searchterms", st_rows)):
            res = ads.call("POST", f"/reports/apps/{kind}/query", body)
            for r in (res.get("result") or {}).get("rows") or []:
                m, meta = r.get("totalMetrics") or {}, r.get("metadata") or {}
                text = meta.get("text") if kind == "keywords" else meta.get("searchTermText")
                rows.append({
                    "campaign": c["name"], "adGroup": groups.get(meta.get("adGroupId"), meta.get("adGroupId")),
                    "term": text, "keyword": (meta.get("keyword") or {}).get("text") if kind == "searchterms" else text,
                    "impressions": m.get("impressions") or 0, "taps": m.get("taps") or 0,
                    "installs": m.get("tapInstalls") or 0, "spend": float((m.get("localSpend") or {}).get("amount") or 0),
                })
    for name, rows in (("keywords", kw_rows), ("searchterms", st_rows)):
        path = out_dir / f"{name}-{start}-{end}.csv"
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["campaign", "adGroup", "term", "keyword", "impressions", "taps", "installs", "spend"])
            w.writeheader()
            w.writerows(rows)
        print(f"{len(rows)} rows -> {path}")
    by_group = {}
    for r in kw_rows:
        t = by_group.setdefault((r["campaign"], r["adGroup"]), {"impressions": 0, "taps": 0, "installs": 0, "spend": 0.0})
        for k in t:
            t[k] += r[k]
    print(f"\n{start} .. {end}")
    print(f'{"campaign / ad group":38} {"impr":>7} {"taps":>6} {"TTR":>6} {"inst":>5} {"CR":>6} {"spend":>8} {"CPT":>6} {"CPI":>6}')
    for (camp, group), t in sorted(by_group.items()):
        ttr = t["taps"] / t["impressions"] if t["impressions"] else 0
        cr = t["installs"] / t["taps"] if t["taps"] else 0
        cpt = t["spend"] / t["taps"] if t["taps"] else 0
        cpi = t["spend"] / t["installs"] if t["installs"] else 0
        print(f'{camp[len(PREFIX):] + " / " + str(group):38} {t["impressions"]:7} {t["taps"]:6} {ttr:6.1%} {t["installs"]:5} {cr:6.1%} {t["spend"]:8.2f} {cpt:6.2f} {cpi:6.2f}')


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    who = p.add_mutually_exclusive_group(required=True)
    who.add_argument("--app", help="app key in local/apps.yaml (reads asc_app_id)")
    who.add_argument("--adam-id", help="App Store app id")
    p.add_argument("--plan-dir", default="asa", help="folder with plan.json, keywords-*.txt, config.json")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("plan", cmd_plan), ("create", cmd_create)):
        s = sub.add_parser(name)
        s.add_argument("--tier", default="t1")
        s.add_argument("--with-head", action="store_true", help="also the ag_head ad group (day 7)")
        if name == "create":
            s.add_argument("--dry-run", action="store_true")
        s.set_defaults(fn=fn)
    sub.add_parser("whoami").set_defaults(fn=cmd_whoami)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    s = sub.add_parser("popularity")
    s.add_argument("--country", default="US")
    s.set_defaults(fn=cmd_popularity)
    s = sub.add_parser("report")
    s.add_argument("--days", type=int, default=7)
    s.set_defaults(fn=cmd_report)
    s = sub.add_parser("enable")
    s.add_argument("--yes", action="store_true")
    s.add_argument("--tier")
    s.set_defaults(fn=cmd_enable)
    s = sub.add_parser("pause")
    s.add_argument("--tier")
    s.set_defaults(fn=cmd_pause)
    args = p.parse_args()
    global ADAM_ID, HERE, CONFIG
    HERE = Path(args.plan_dir).expanduser().resolve()
    CONFIG = HERE / "config.json"
    load_plan()
    if getattr(args, "tier", None) and args.tier not in PLAN:
        sys.exit(f"unknown tier {args.tier}; plan.json has {', '.join(sorted(PLAN))}")
    ADAM_ID = args.adam_id or _app_field(args.app, "asc_app_id")
    args.fn(args)


if __name__ == "__main__":
    main()
