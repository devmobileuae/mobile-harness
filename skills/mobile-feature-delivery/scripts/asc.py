#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# WHAT: pushes one version's en-US listing to App Store Connect via the ASC API:
#   texts (description / keywords / promo / What's New), APP_IPHONE_67 screenshots
#   (01-10.png), IPHONE_67 app preview (00-app-preview.mp4). Never submits for review.
# RUN (read-only by default; prints current state):
#   python3 scripts/asc.py --app <key> --version 1.2.0
#   python3 scripts/asc.py --app <key> --version 1.2.0 --apply --only-screenshots --drop-preview \
#       --shots-dir <repo>/marketing/screenshots/<set>
#   --keep-keywords  leave the live keyword field (e.g. owner-set keywords after approval)
#   --metadata FILE  markdown with "## Description", "## Keywords field", "## Promotional text",
#                    "## Release notes — <version>" sections (needed unless --only-screenshots/--only-preview)
#   --desc-file X    use this description instead of the metadata file's
# APP: --app <key> reads bundle_id from local/apps.yaml (python3 scripts/setup.py --get <key>.bundle_id),
#   or pass --bundle explicitly.
# CREDS: ASC_ISSUER_ID / ASC_KEY_ID / ASC_KEY_PATH from the environment
#   (set -a; . local/secrets.env; set +a), or --config <json> with {"issuerId","keyId","p8"}.
#   Never read creds from another project.
# DEPS: pip install pyjwt requests cryptography pyyaml
# ---------------------------------------------------------------------------
"""Push an app's App Store listing to App Store Connect for one version.

Read-only by default: prints the version's current state. With --apply it
writes the en-US texts, replaces the iPhone 6.9" screenshots and the app
preview. Never submits for review.
"""
import argparse, hashlib, json, os, re, sys, time
from pathlib import Path

import jwt, requests

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                      # plugin root (holds local/apps.yaml)
LOCALE = "en-US"
API = "https://api.appstoreconnect.apple.com/v1"
SHOT_TYPE = "APP_IPHONE_67"      # 6.9"/6.7" slot, accepts 1320x2868
PREVIEW_TYPE = "IPHONE_67"


def app_field(key, field):
    """A field of one app from local/apps.yaml (see local.example/apps.yaml)."""
    import yaml
    path = REPO / "local/apps.yaml"
    if not path.exists():
        sys.exit(f"{path} missing: run python3 scripts/setup.py")
    apps = (yaml.safe_load(path.read_text()) or {}).get("apps") or []
    app = next((a for a in apps if a.get("key") == key), None)
    if not app or not app.get(field):
        sys.exit(f"local/apps.yaml: no {field} for app '{key}' (python3 scripts/setup.py --set {key}.{field}=...)")
    return app[field]


def load_creds(config=None):
    if config:
        return json.loads(Path(config).expanduser().read_text())
    env = {k: os.environ.get(k) for k in ("ASC_ISSUER_ID", "ASC_KEY_ID", "ASC_KEY_PATH")}
    if not all(env.values()):
        sys.exit("ASC creds: set ASC_ISSUER_ID/ASC_KEY_ID/ASC_KEY_PATH (set -a; . local/secrets.env; set +a) or pass --config")
    return {"issuerId": env["ASC_ISSUER_ID"], "keyId": env["ASC_KEY_ID"], "p8": env["ASC_KEY_PATH"]}


def resolve_bundle(a):
    if getattr(a, "bundle", None):
        return a.bundle
    if getattr(a, "app", None):
        return app_field(a.app, "bundle_id")
    sys.exit("pass --app <key> or --bundle <bundle id>")


def token(cfg):
    key = Path(cfg["p8"]).expanduser()
    now = int(time.time())
    return jwt.encode({"iss": cfg["issuerId"], "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
                      key.read_text(), algorithm="ES256", headers={"kid": cfg["keyId"]})


class ASC:
    def __init__(self, cfg):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token(cfg)}"

    def call(self, method, path, **kw):
        url = path if path.startswith("http") else API + path
        r = self.s.request(method, url, **kw)
        if r.status_code >= 400:
            sys.exit(f"{method} {path} -> {r.status_code}\n{r.text[:1500]}")
        return r.json() if r.text else {}

    get = lambda self, p, **k: self.call("GET", p, **k)
    post = lambda self, p, body: self.call("POST", p, json=body)
    patch = lambda self, p, body: self.call("PATCH", p, json=body)
    delete = lambda self, p: self.call("DELETE", p)


def section(md, title):
    """Text of the first ``` block after a heading that starts with `title`."""
    m = re.search(r"^## " + re.escape(title) + r".*?```\n(.*?)```", md, re.S | re.M)
    return m.group(1).strip() if m else None


def texts(metadata, version):
    md = Path(metadata).read_text()
    promo = re.search(r"^## Promotional text.*?\n> (.*?)\n", md, re.S | re.M).group(1).strip()
    kw = re.search(r"^## Keywords field.*?```\n(.*?)\n```", md, re.S | re.M).group(1).strip()
    return {
        "description": section(md, "Description"),
        "keywords": kw,
        "promotionalText": promo,
        "whatsNew": section(md, f"Release notes — {version}"),
    }


def upload(asc, kind, set_id, path, rel, extra=None):
    data = path.read_bytes()
    body = {"data": {"type": kind, "attributes": {"fileName": path.name, "fileSize": len(data), **(extra or {})},
                     "relationships": {rel: {"data": {"type": rel + "s" if not rel.endswith("Set") else rel + "s", "id": set_id}}}}}
    body["data"]["relationships"][rel]["data"]["type"] = {"appScreenshotSet": "appScreenshotSets",
                                                          "appPreviewSet": "appPreviewSets"}[rel]
    if kind == "appPreviews":
        body["data"]["attributes"]["mimeType"] = "video/mp4"
    res = asc.post(f"/{kind}", body)["data"]
    for op in res["attributes"]["uploadOperations"]:
        chunk = data[op["offset"]: op["offset"] + op["length"]]
        hdrs = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}
        r = requests.request(op["method"], op["url"], data=chunk, headers=hdrs)
        if r.status_code >= 400:
            sys.exit(f"upload chunk failed {r.status_code}: {r.text[:500]}")
    asc.patch(f"/{kind}/{res['id']}", {"data": {"type": kind, "id": res["id"], "attributes": {
        "uploaded": True, "sourceFileChecksum": hashlib.md5(data).hexdigest()}}})
    return res["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", help="app key in local/apps.yaml")
    ap.add_argument("--bundle", help="bundle id (instead of --app)")
    ap.add_argument("--config", help="JSON creds {issuerId,keyId,p8} instead of ASC_* env vars")
    ap.add_argument("--version", required=True)
    ap.add_argument("--metadata", help="markdown file with the listing texts")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--skip-media", action="store_true")
    ap.add_argument("--desc-file", help="use this description instead of metadata.md")
    ap.add_argument("--keep-keywords", action="store_true", help="leave the live keyword field alone")
    ap.add_argument("--shots-dir", help="folder with 01-10.png and 00-app-preview.mp4")
    ap.add_argument("--only-preview", action="store_true",
                    help="replace the app preview only: texts and screenshots stay as they are")
    ap.add_argument("--preview-frame", default="00:00:07:00",
                    help="poster frame of the app preview, HH:MM:SS:FF")
    ap.add_argument("--drop-preview", action="store_true",
                    help="delete the app preview (no replacement); combine with --only-screenshots")
    ap.add_argument("--only-screenshots", action="store_true",
                    help="replace the 6.9\" screenshots only: texts and the preview stay as they are")
    a = ap.parse_args()

    bundle = resolve_bundle(a)
    asc = ASC(load_creds(a.config))
    found = asc.get("/apps", params={"filter[bundleId]": bundle})["data"]
    if not found:
        sys.exit(f"no ASC app with bundle id {bundle}")
    app = found[0]
    print("app", app["id"], app["attributes"]["name"])
    vers = asc.get(f"/apps/{app['id']}/appStoreVersions",
                   params={"filter[versionString]": a.version, "filter[platform]": "IOS"})["data"]
    if not vers:
        sys.exit(f"version {a.version} not found")
    v = vers[0]
    print("version", v["attributes"]["versionString"], v["attributes"]["appStoreState"])
    locs = asc.get(f"/appStoreVersions/{v['id']}/appStoreVersionLocalizations")["data"]
    loc = next(l for l in locs if l["attributes"]["locale"] == LOCALE)
    texts_only_media = a.only_screenshots or a.only_preview
    if not a.metadata and not texts_only_media:
        sys.exit("pass --metadata <file> (or --only-screenshots / --only-preview)")
    want = texts(a.metadata, a.version) if a.metadata else {}
    if a.desc_file:
        want["description"] = Path(a.desc_file).read_text().strip()
    if a.keep_keywords:
        want.pop("keywords")
    for k, val in want.items():
        cur = loc["attributes"].get(k) or ""
        print(f"  {k}: {'same' if cur.strip() == (val or '').strip() else 'CHANGE'} ({len(val or '')} chars)")

    sets = asc.get(f"/appStoreVersionLocalizations/{loc['id']}/appScreenshotSets")["data"]
    for s in sets:
        n = len(asc.get(f"/appScreenshotSets/{s['id']}/appScreenshots")["data"])
        print("  screenshots", s["attributes"]["screenshotDisplayType"], n)
    psets = asc.get(f"/appStoreVersionLocalizations/{loc['id']}/appPreviewSets")["data"]
    for s in psets:
        n = len(asc.get(f"/appPreviewSets/{s['id']}/appPreviews")["data"])
        print("  previews", s["attributes"]["previewType"], n)

    if not a.apply:
        print("\nread-only; pass --apply to write")
        return

    if not a.shots_dir and not a.skip_media:
        sys.exit("pass --shots-dir <folder> (or --skip-media)")
    shots_dir = Path(a.shots_dir) if a.shots_dir else None
    if not (a.only_screenshots or a.only_preview):
        asc.patch(f"/appStoreVersionLocalizations/{loc['id']}", {"data": {
            "type": "appStoreVersionLocalizations", "id": loc["id"], "attributes": want}})
        print("texts written")
        if a.skip_media:
            return

    shots = [] if a.only_preview else sorted(shots_dir.glob("[0-9][0-9].png"))
    if not a.only_preview and not 1 <= len(shots) <= 10:
        sys.exit(f"expected 1-10 screenshots in {shots_dir}, found {len(shots)}")
    sset = next((s for s in sets if s["attributes"]["screenshotDisplayType"] == SHOT_TYPE), None)
    if not sset:
        sset = asc.post("/appScreenshotSets", {"data": {"type": "appScreenshotSets",
            "attributes": {"screenshotDisplayType": SHOT_TYPE},
            "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": loc["id"]}}}}})["data"]
    for old in ([] if a.only_preview else asc.get(f"/appScreenshotSets/{sset['id']}/appScreenshots")["data"]):
        asc.delete(f"/appScreenshots/{old['id']}")
    for p in shots:
        upload(asc, "appScreenshots", sset["id"], p, "appScreenshotSet")
        print("  shot", p.name)
    if a.drop_preview:
        for s in psets:
            for old in asc.get(f"/appPreviewSets/{s['id']}/appPreviews")["data"]:
                asc.delete(f"/appPreviews/{old['id']}")
            print("  previews dropped", s["attributes"]["previewType"])
    if a.only_screenshots or a.drop_preview:
        return

    pset = next((s for s in psets if s["attributes"]["previewType"] == PREVIEW_TYPE), None)
    if not pset:
        pset = asc.post("/appPreviewSets", {"data": {"type": "appPreviewSets",
            "attributes": {"previewType": PREVIEW_TYPE},
            "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": loc["id"]}}}}})["data"]
    for old in asc.get(f"/appPreviewSets/{pset['id']}/appPreviews")["data"]:
        asc.delete(f"/appPreviews/{old['id']}")
    pid = upload(asc, "appPreviews", pset["id"], shots_dir / "00-app-preview.mp4", "appPreviewSet")
    print("  preview uploaded")
    # ASC ignores the poster frame on create, and refuses to change it (409) until the video
    # has been processed — keep asking for a few minutes.
    body = {"data": {"type": "appPreviews", "id": pid, "attributes": {"previewFrameTimeCode": a.preview_frame}}}
    for _ in range(24):
        if asc.s.patch(f"{API}/appPreviews/{pid}", json=body).status_code < 300:
            print("  poster frame", a.preview_frame)
            break
        time.sleep(10)
    else:
        print(f"  poster frame NOT set — set {a.preview_frame} in App Store Connect")


if __name__ == "__main__":
    main()
