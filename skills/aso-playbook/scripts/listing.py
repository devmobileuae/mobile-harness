#!/usr/bin/env python3
# --- aso-playbook script (generic; works for any app on the ASC API key) ---
# Pushes an App Store listing to App Store Connect from a folder per locale: texts, screenshots, the app
# preview and subscription names. Read-only unless --apply. Never creates a version, never submits for review.
# Needs pyjwt[crypto] + requests (temp venv). Secrets: none in this file; credentials come from a git-ignored
# config.json (--config or $ASC_CONFIG).
# ---
"""Push an app's App Store listing to App Store Connect for one version.

  listing.py --bundle-id com.example.app --version 1.1 [--root .] [--locale fr-FR ...] [--apply]
             [--skip-shots | --only-shots] [--only 03.png] [--keep-keywords] [--desc-file FILE]
             [--preview | --drop-preview] [--subscriptions] [--copyright "2026 Name"]
             [--categories GAMES,GAMES_TRIVIA,EDUCATION] [--backup]

Bundle id: --bundle-id or $ASC_BUNDLE_ID. Credentials: --config or $ASC_CONFIG, default
<root>/appstore/asc/config.json, with keyId, issuerId and p8 (path to the .p8 key; relative paths resolve
next to config.json). Template: templates/asc-config.example.json.

Layout under --root (override with --metadata-dir / --shots-dir):
  appstore/metadata/<locale>/name.txt, subtitle.txt, description.txt, keywords.txt, promotional_text.txt,
                             release_notes.txt, support_url.txt, marketing_url.txt, privacy_url.txt,
                             subscriptions.json (optional)
  appstore/screenshots/<locale>/01*.png … 10*.png (uploaded in filename order), 00-app-preview.mp4 (optional)
A missing text file leaves that field alone. With one --locale, --shots-dir may also be a flat folder. A locale without a screenshot folder keeps what ASC has (it
inherits the primary language's set when it has none of its own).

Read-only by default: prints, per locale, which fields would change. With --apply it writes:
- version texts (description, keywords, promotional text, What's New, URLs) and name/subtitle/privacy URL,
  creating a localization ASC doesn't have yet; only changed fields are sent;
- the 6.9"/6.7" iPhone screenshots (replacing the set), or with --only FILE one image swapped in place
  with the order kept;
- --preview: the app preview from 00-app-preview.mp4 (poster frame retried while ASC processes it);
  --drop-preview: deletes the app preview (a video in slot 1 also becomes the first Apple Ads asset);
- once: copyright and categories when given; --subscriptions: group and product names per locale.
--keep-keywords never touches the live keyword field. --backup writes the current state to a JSON file
first, so a revert is a copy-paste away. What's New is skipped on a first version.
"""
import argparse, hashlib, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

import jwt, requests

API = "https://api.appstoreconnect.apple.com/v1"
# 1290x2796 and 1320x2868 slides go in the large Dynamic Island set (the 6.9"/6.7" slot).
SHOT_TYPE = "APP_IPHONE_67"
PREVIEW_TYPE = "IPHONE_67"
PREVIEW_FILE = "00-app-preview.mp4"


class ASC:
    def __init__(self, config: Path):
        cfg = json.loads(config.read_text())
        key = Path(cfg["p8"]).expanduser()
        if not key.is_absolute():
            key = config.parent / key
        now = int(time.time())
        token = jwt.encode({"iss": cfg["issuerId"], "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
                           key.read_text(), algorithm="ES256", headers={"kid": cfg["keyId"]})
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"

    def call(self, method, path, **kw):
        url = path if path.startswith("http") else API + path
        for attempt in range(5):
            r = self.s.request(method, url, timeout=120, **kw)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            break
        if r.status_code >= 400:
            sys.exit(f"{method} {path} -> {r.status_code}\n{r.text[:1500]}")
        return r.json() if r.text else {}

    def get(self, path, **kw): return self.call("GET", path, **kw)
    def post(self, path, body): return self.call("POST", path, json=body)
    def patch(self, path, body): return self.call("PATCH", path, json=body)
    def delete(self, path): return self.call("DELETE", path)


def read(p: Path):
    return p.read_text().strip() if p.exists() else None


def changed(label, current, wanted):
    """Print the diff line; True when the field would change."""
    if wanted is None:
        return False
    same = (current or "").strip() == wanted.strip()
    print(f"  {label}: {'same' if same else 'CHANGE'} ({len(wanted)} chars)")
    return not same


def upload(asc, kind, set_rel, set_type, set_id, path, extra=None):
    data = path.read_bytes()
    res = asc.post(f"/{kind}", {"data": {"type": kind,
        "attributes": {"fileName": path.name, "fileSize": len(data), **(extra or {})},
        "relationships": {set_rel: {"data": {"type": set_type, "id": set_id}}}}})["data"]
    for op in res["attributes"]["uploadOperations"]:
        chunk = data[op["offset"]: op["offset"] + op["length"]]
        headers = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}
        r = requests.request(op["method"], op["url"], data=chunk, headers=headers, timeout=300)
        if r.status_code >= 400:
            sys.exit(f"upload of {path.name} failed {r.status_code}: {r.text[:500]}")
    asc.patch(f"/{kind}/{res['id']}", {"data": {"type": kind, "id": res["id"],
        "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(data).hexdigest()}}})
    return res["id"]


def ensure(asc, existing, locale, kind, parent_rel, parent_type, parent_id, apply, attrs=None):
    """The localization of `kind` for `locale`, created on --apply when missing; None in a dry run."""
    if locale in existing:
        return existing[locale]
    print(f"  {kind}: NEW localization {locale}")
    if not apply:
        return None
    # App Store Connect wants the required fields (the app name) in the creating request itself.
    return asc.post(f"/{kind}", {"data": {"type": kind, "attributes": {"locale": locale, **(attrs or {})},
        "relationships": {parent_rel: {"data": {"type": parent_type, "id": parent_id}}}}})["data"]


def push_shots(asc, loc_id, folder: Path, apply, only=None):
    shots = sorted(folder.glob("[0-9][0-9]*.png"))
    if not folder.is_dir() or not shots:
        print(f"  screenshots: no local folder/files in {folder} — left as they are")
        return
    sets = asc.get(f"/appStoreVersionLocalizations/{loc_id}/appScreenshotSets")["data"] if loc_id else []
    sset = next((s for s in sets if s["attributes"]["screenshotDisplayType"] == SHOT_TYPE), None)
    existing = asc.get(f"/appScreenshotSets/{sset['id']}/appScreenshots")["data"] if sset else []
    print(f"  screenshots: {len(existing)} in App Store Connect, {len(shots)} local")
    if only:
        # Swap one image in place and keep the set's order, so a caption fix does not reshuffle the rest.
        names = [x["attributes"].get("fileName") for x in existing]
        if only not in names:
            print(f"  ! {only} is not in the set (has {names}) — run without --only")
            return
        idx = names.index(only)
        print(f"  replacing {only} at position {idx + 1}/{len(existing)}")
        if not apply:
            return
        asc.delete(f"/appScreenshots/{existing[idx]['id']}")
        ids = [x["id"] for x in existing]
        ids[idx] = upload(asc, "appScreenshots", "appScreenshotSet", "appScreenshotSets", sset["id"], folder / only)
        asc.patch(f"/appScreenshotSets/{sset['id']}/relationships/appScreenshots",
                  {"data": [{"type": "appScreenshots", "id": i} for i in ids]})
        print(f"  replaced {only}, order kept")
        return
    if not apply:
        return
    if len(shots) > 10:
        sys.exit(f"expected 1-10 screenshots in {folder}, found {len(shots)}")
    if not sset:
        sset = asc.post("/appScreenshotSets", {"data": {"type": "appScreenshotSets",
            "attributes": {"screenshotDisplayType": SHOT_TYPE},
            "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": loc_id}}}}})["data"]
    for old in existing:
        asc.delete(f"/appScreenshots/{old['id']}")
    ids = [upload(asc, "appScreenshots", "appScreenshotSet", "appScreenshotSets", sset["id"], p) for p in shots]
    asc.patch(f"/appScreenshotSets/{sset['id']}/relationships/appScreenshots",
              {"data": [{"type": "appScreenshots", "id": i} for i in ids]})
    print(f"  uploaded {len(shots)} screenshots")


def push_preview(asc, loc_id, folder: Path, apply, drop, frame):
    psets = asc.get(f"/appStoreVersionLocalizations/{loc_id}/appPreviewSets")["data"] if loc_id else []
    for s in psets:
        n = len(asc.get(f"/appPreviewSets/{s['id']}/appPreviews")["data"])
        print(f"  previews {s['attributes']['previewType']}: {n}")
    video = folder / PREVIEW_FILE
    if drop:
        print("  app preview: DROP")
        if apply:
            for s in psets:
                for old in asc.get(f"/appPreviewSets/{s['id']}/appPreviews")["data"]:
                    asc.delete(f"/appPreviews/{old['id']}")
        return
    if not video.exists():
        print(f"  app preview: no {video} — left as it is")
        return
    print(f"  app preview: REPLACE with {video.name}")
    if not apply:
        return
    pset = next((s for s in psets if s["attributes"]["previewType"] == PREVIEW_TYPE), None)
    if not pset:
        pset = asc.post("/appPreviewSets", {"data": {"type": "appPreviewSets",
            "attributes": {"previewType": PREVIEW_TYPE},
            "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": loc_id}}}}})["data"]
    for old in asc.get(f"/appPreviewSets/{pset['id']}/appPreviews")["data"]:
        asc.delete(f"/appPreviews/{old['id']}")
    pid = upload(asc, "appPreviews", "appPreviewSet", "appPreviewSets", pset["id"], video, {"mimeType": "video/mp4"})
    # ASC ignores the poster frame on create and refuses to change it (409) until the video is processed.
    body = {"data": {"type": "appPreviews", "id": pid, "attributes": {"previewFrameTimeCode": frame}}}
    for _ in range(24):
        if asc.s.patch(f"{API}/appPreviews/{pid}", json=body).status_code < 300:
            print(f"  poster frame {frame}")
            return
        time.sleep(10)
    print(f"  poster frame NOT set — set {frame} in App Store Connect")


def push_subscriptions(asc, app_id, meta_root: Path, locales, apply):
    """subscriptions.json: {"group": "...", "products": {"<productId>": {"name": "...", "description": "..."}}}
    (older files with yearly_name/yearly_description/monthly_name/monthly_description still work)."""
    for g in asc.get(f"/apps/{app_id}/subscriptionGroups")["data"]:
        g_locs = {l["attributes"]["locale"]: l for l in asc.get(f"/subscriptionGroups/{g['id']}/subscriptionGroupLocalizations")["data"]}
        subs = asc.get(f"/subscriptionGroups/{g['id']}/subscriptions")["data"]
        for locale in locales:
            s = json.loads(read(meta_root / locale / "subscriptions.json") or "null")
            if not s:
                continue
            print(f"{locale} subscriptions: group {s['group']!r}")
            if not apply:
                continue
            if locale in g_locs:
                asc.patch(f"/subscriptionGroupLocalizations/{g_locs[locale]['id']}", {"data": {"type": "subscriptionGroupLocalizations",
                    "id": g_locs[locale]["id"], "attributes": {"name": s["group"]}}})
            else:
                asc.post("/subscriptionGroupLocalizations", {"data": {"type": "subscriptionGroupLocalizations",
                    "attributes": {"locale": locale, "name": s["group"]},
                    "relationships": {"subscriptionGroup": {"data": {"type": "subscriptionGroups", "id": g["id"]}}}}})
            for sub in subs:
                pid = sub["attributes"]["productId"]
                if pid in s.get("products", {}):
                    attrs = s["products"][pid]
                else:
                    kind = "yearly" if pid.endswith("yearly") else "monthly"
                    if f"{kind}_name" not in s:
                        continue
                    attrs = {"name": s[f"{kind}_name"], "description": s[f"{kind}_description"]}
                existing = {l["attributes"]["locale"]: l for l in asc.get(f"/subscriptions/{sub['id']}/subscriptionLocalizations")["data"]}
                if locale in existing:
                    asc.patch(f"/subscriptionLocalizations/{existing[locale]['id']}", {"data": {"type": "subscriptionLocalizations",
                        "id": existing[locale]["id"], "attributes": attrs}})
                else:
                    asc.post("/subscriptionLocalizations", {"data": {"type": "subscriptionLocalizations",
                        "attributes": {"locale": locale, **attrs},
                        "relationships": {"subscription": {"data": {"type": "subscriptions", "id": sub["id"]}}}}})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle-id", default=os.environ.get("ASC_BUNDLE_ID"))
    ap.add_argument("--version", required=True)
    ap.add_argument("--root", default=".", help="app repo root (default: current directory)")
    ap.add_argument("--config", default=os.environ.get("ASC_CONFIG"), help="default: <root>/appstore/asc/config.json")
    ap.add_argument("--metadata-dir", help="default: <root>/appstore/metadata")
    ap.add_argument("--shots-dir", help="default: <root>/appstore/screenshots (one folder per locale)")
    ap.add_argument("--locale", action="append", help="default: every locale folder with a name.txt or description.txt")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--skip-shots", action="store_true", help="texts only")
    ap.add_argument("--only-shots", action="store_true", help="screenshots/preview only, texts stay as they are")
    ap.add_argument("--only", metavar="FILE", help="replace just this screenshot (e.g. 03.png), keeping the order")
    ap.add_argument("--keep-keywords", action="store_true", help="leave the live keyword field alone")
    ap.add_argument("--desc-file", help="use this description for every pushed locale instead of description.txt")
    ap.add_argument("--preview", action="store_true", help=f"replace the app preview with <shots>/<locale>/{PREVIEW_FILE}")
    ap.add_argument("--drop-preview", action="store_true", help="delete the app preview")
    ap.add_argument("--preview-frame", default="00:00:07:00", help="poster frame, HH:MM:SS:FF")
    ap.add_argument("--subscriptions", action="store_true")
    ap.add_argument("--copyright", help='e.g. "2026 Your Name"; not touched when omitted')
    ap.add_argument("--categories", help="PRIMARY,PRIMARY_SUB,SECONDARY ids, e.g. GAMES,GAMES_TRIVIA,EDUCATION")
    ap.add_argument("--backup", action="store_true", help="write the current listing state to backup-<time>.json first")
    a = ap.parse_args()
    if not a.bundle_id:
        sys.exit("pass --bundle-id or set ASC_BUNDLE_ID")

    root = Path(a.root).expanduser().resolve()
    meta_root = Path(a.metadata_dir).expanduser() if a.metadata_dir else root / "appstore/metadata"
    shots_root = Path(a.shots_dir).expanduser() if a.shots_dir else root / "appstore/screenshots"
    config = Path(a.config).expanduser() if a.config else root / "appstore/asc/config.json"
    locales = a.locale or sorted(p.name for p in meta_root.iterdir()
                                 if (p / "name.txt").exists() or (p / "description.txt").exists())

    asc = ASC(config)
    apps = asc.get("/apps", params={"filter[bundleId]": a.bundle_id})["data"]
    if not apps:
        sys.exit(f"no app with bundle id {a.bundle_id} on this key")
    app = apps[0]
    print("app", app["id"], app["attributes"]["name"])
    versions = asc.get(f"/apps/{app['id']}/appStoreVersions",
                       params={"filter[versionString]": a.version, "filter[platform]": "IOS"})["data"]
    if not versions:
        sys.exit(f"no version {a.version} in App Store Connect: create it there first")
    version = versions[0]
    first = len(asc.get(f"/apps/{app['id']}/appStoreVersions")["data"]) == 1
    print("version", version["attributes"]["versionString"], version["attributes"]["appStoreState"])
    infos = asc.get(f"/apps/{app['id']}/appInfos")["data"]
    info = next((i for i in infos if i["attributes"].get("appStoreState") != "READY_FOR_SALE"), infos[0])
    v_locs = {l["attributes"]["locale"]: l for l in asc.get(f"/appStoreVersions/{version['id']}/appStoreVersionLocalizations")["data"]}
    i_locs = {l["attributes"]["locale"]: l for l in asc.get(f"/appInfos/{info['id']}/appInfoLocalizations")["data"]}

    if a.backup:
        dump = {"takenAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "app": app["id"],
                "version": version["attributes"]["versionString"],
                "versionLocalizations": {k: v["attributes"] for k, v in v_locs.items()},
                "appInfoLocalizations": {k: v["attributes"] for k, v in i_locs.items()}}
        out = Path(f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
        out.write_text(json.dumps(dump, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("backup written to", out.resolve())

    for locale in locales:
        print(f"\n{locale}")
        d = meta_root / locale
        loc = None
        if not a.only_shots:
            version_texts = {"description": read(Path(a.desc_file)) if a.desc_file else read(d / "description.txt"),
                             "keywords": None if a.keep_keywords else read(d / "keywords.txt"),
                             "promotionalText": read(d / "promotional_text.txt"),
                             "supportUrl": read(d / "support_url.txt"), "marketingUrl": read(d / "marketing_url.txt"),
                             "whatsNew": None if first else read(d / "release_notes.txt")}
            info_texts = {"name": read(d / "name.txt"), "subtitle": read(d / "subtitle.txt"),
                          "privacyPolicyUrl": read(d / "privacy_url.txt")}
            loc = ensure(asc, v_locs, locale, "appStoreVersionLocalizations", "appStoreVersion", "appStoreVersions",
                         version["id"], a.apply)
            # Creating the version localization can create the app info one too: read them again.
            if a.apply and locale not in i_locs:
                i_locs = {l["attributes"]["locale"]: l for l in asc.get(f"/appInfos/{info['id']}/appInfoLocalizations")["data"]}
            info_loc = ensure(asc, i_locs, locale, "appInfoLocalizations", "appInfo", "appInfos", info["id"], a.apply,
                              {k: v for k, v in info_texts.items() if v})
            v_new = {k: v for k, v in version_texts.items()
                     if changed(k, (loc or {}).get("attributes", {}).get(k), v)}
            i_new = {k: v for k, v in info_texts.items()
                     if changed(k, (info_loc or {}).get("attributes", {}).get(k), v)}
            if a.apply and v_new:
                asc.patch(f"/appStoreVersionLocalizations/{loc['id']}", {"data": {
                    "type": "appStoreVersionLocalizations", "id": loc["id"], "attributes": v_new}})
            if a.apply and i_new:
                asc.patch(f"/appInfoLocalizations/{info_loc['id']}", {"data": {
                    "type": "appInfoLocalizations", "id": info_loc["id"], "attributes": i_new}})
            if a.apply and (v_new or i_new):
                print("  texts written")
        else:
            loc = v_locs.get(locale)
        if a.skip_shots:
            continue
        if loc is None:
            print("  screenshots: localization does not exist yet (push texts first)")
            continue
        folder = shots_root / locale
        if not folder.is_dir() and len(locales) == 1:
            folder = shots_root  # a flat --shots-dir is accepted when exactly one locale is pushed
        push_shots(asc, loc["id"], folder, a.apply, a.only)
        if a.preview or a.drop_preview:
            push_preview(asc, loc["id"], folder, a.apply, a.drop_preview, a.preview_frame)

    if a.copyright and changed("copyright", version["attributes"].get("copyright"), a.copyright) and a.apply:
        asc.patch(f"/appStoreVersions/{version['id']}", {"data": {
            "type": "appStoreVersions", "id": version["id"], "attributes": {"copyright": a.copyright}}})
    if a.categories:
        keys = ["primaryCategory", "primarySubcategoryOne", "secondaryCategory"]
        cats = {k: v for k, v in zip(keys, a.categories.split(",")) if v}
        print("  categories:", cats)
        if a.apply:
            asc.patch(f"/appInfos/{info['id']}", {"data": {"type": "appInfos", "id": info["id"], "relationships": {
                k: {"data": {"type": "appCategories", "id": v}} for k, v in cats.items()}}})
    if a.subscriptions:
        push_subscriptions(asc, app["id"], meta_root, locales, a.apply)
    if not a.apply:
        print("\nread-only; pass --apply to write")


if __name__ == "__main__":
    main()
