#!/usr/bin/env python3
# Logged-out TikTok search / user / video / download via headless Chrome + CDP. No key, no credits.
# Needs: Google Chrome at /Applications, `pip install websocket-client`.
# Run from the project's growth/ dir, e.g.
#   python3 tt_scrape.py search "lock in" "winter arc" --pages 5 --out research/<topic>-<date>/search.jsonl
#   python3 tt_scrape.py user <handle> --pages 3 --out research/<topic>-<date>/user-<handle>.jsonl
#   python3 tt_scrape.py download <url> [...] --out research/<topic>-<date>/media
# Limits seen: ~15 rapid search queries -> 'blocked' (2026-10-25); download mode broke 2026-11-13 ('no ssr') -> use yt-dlp.
"""Logged-out TikTok research scraper: headless Chrome + CDP, no API key, no credits.

TikTok's web search API answers unsigned requests made from inside a tiktok.com page
(the page carries the ttwid/msToken cookies). So we open a muted headless Chrome,
land on tiktok.com once, then call the JSON endpoints with fetch() via CDP.

  tt_scrape.py search "habit tracker app" "discipline app" --pages 5 --out research/<topic>/search.jsonl
  tt_scrape.py user <handle> --out research/<topic>/user.jsonl
  tt_scrape.py video https://www.tiktok.com/@x/video/123 --out ...
  tt_scrape.py download <video urls | ids@author> --out research/<topic>-<date>/media   (dir)
      -> <id>.mp4 (video) or <id>/01.jpg… (photo post) + <id>.json (full itemStruct)

Each output line = one compact item (id, author, stats, music, desc, createTime,
duration, photo flag, query). Duplicates across queries are kept once (first query wins).
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, time, urllib.request
import websocket  # websocket-client

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")


class Tab:
    def __init__(self, port):
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                page = next(t for t in tabs if t.get("type") == "page")
                break
            except Exception:
                time.sleep(0.2)
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=120, suppress_origin=True)
        self.n = 0

    def cmd(self, method, **params):
        self.n += 1
        my = self.n
        self.ws.send(json.dumps({"id": my, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == my:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def js(self, expr):
        r = self.cmd("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"].get("text"))
        return r["result"].get("value")

    def goto(self, url, wait=6):
        self.cmd("Page.navigate", url=url)
        time.sleep(wait)


def compact(it, query=None):
    st = it.get("stats") or it.get("statsV2") or {}
    mu = it.get("music") or {}
    au = it.get("author") or {}
    v = it.get("video") or {}
    return {
        "id": it.get("id"),
        "author": au.get("uniqueId"),
        "author_followers": (it.get("authorStats") or {}).get("followerCount"),
        "plays": int(st.get("playCount") or 0),
        "likes": int(st.get("diggCount") or 0),
        "comments": int(st.get("commentCount") or 0),
        "shares": int(st.get("shareCount") or 0),
        "saves": int(st.get("collectCount") or 0),
        "created": it.get("createTime"),
        "duration": v.get("duration"),
        "photo": bool(it.get("imagePost")),
        "slides": len((it.get("imagePost") or {}).get("images") or []),
        "music_id": mu.get("id"),
        "music": f"{mu.get('title','')} — {mu.get('authorName','')}",
        "music_original": mu.get("original"),
        "desc": it.get("desc", ""),
        "cover": v.get("cover") or v.get("originCover"),
        "url": f"https://www.tiktok.com/@{au.get('uniqueId')}/video/{it.get('id')}",
        "query": query,
    }


SEARCH_JS = r"""
(async () => {
  const u = new URL('https://www.tiktok.com/api/search/general/full/');
  const p = {aid:1988, app_language:'en', app_name:'tiktok_web', device_platform:'web_pc',
             keyword:%(kw)s, count:20, cursor:%(cursor)d, offset:%(cursor)d, from_page:'search',
             region:'US', user_is_login:false, search_id:%(sid)s};
  Object.entries(p).forEach(([k,v]) => { if (v !== '') u.searchParams.set(k, v) });
  let t = '';
  try { const r = await fetch(u, {credentials:'include'}); t = await r.text(); } catch(e) { return {ok:false, head:'fetch: '+e} }
  try { const j = JSON.parse(t);
        return {ok:true, has_more:j.has_more, cursor:j.cursor, sid:(j.extra||{}).logid || (j.log_pb||{}).impr_id || '',
                items:(j.data||[]).filter(d => d.item).map(d => d.item)}; }
  catch(e) { return {ok:false, head:t.slice(0,200)} }
})()
"""

USER_JS = r"""
(async () => {
  const el = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__');
  let secUid = '';
  try { secUid = JSON.parse(el.textContent).__DEFAULT_SCOPE__['webapp.user-detail'].userInfo.user.secUid } catch(e) {}
  return {secUid};
})()
"""

USER_LIST_JS = r"""
(async () => {
  const u = new URL('https://www.tiktok.com/api/post/item_list/');
  const p = {aid:1988, app_language:'en', app_name:'tiktok_web', device_platform:'web_pc',
             secUid:%(sec)s, count:35, cursor:%(cursor)s, coverFormat:2, region:'US', user_is_login:false};
  Object.entries(p).forEach(([k,v]) => u.searchParams.set(k, v));
  const r = await fetch(u, {credentials:'include'});
  const t = await r.text();
  try { const j = JSON.parse(t); return {ok:true, has_more:j.hasMore, cursor:j.cursor, items:j.itemList||[]} }
  catch(e) { return {ok:false, head:t.slice(0,200)} }
})()
"""

DOM_GRID_JS = r"""
(() => [...document.querySelectorAll('a[href*="/video/"], a[href*="/photo/"]')].map(a => ({
  url:a.href, views:(a.querySelector('strong[data-e2e="video-views"]')||{}).textContent||'',
  desc:(a.querySelector('img')||{}).alt||''})))()
"""

VIDEO_JS = r"""
(async () => {
  const r = await fetch(%(url)s, {credentials:'include'});
  const t = await r.text();
  const m = t.match(/<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)<\/script>/s);
  if (!m) return {ok:false};
  const j = JSON.parse(m[1]);
  const it = (((j.__DEFAULT_SCOPE__||{})['webapp.video-detail']||{}).itemInfo||{}).itemStruct;
  return {ok:!!it, item:it};
})()
"""


DOWNLOAD_JS = r"""
(async () => {
  const page = %(url)s;
  let t = '';
  try { t = await (await fetch(page, {credentials:'include'})).text(); } catch(e) { return {ok:false, err:'page '+e} }
  const m = t.match(/<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)<\/script>/s);
  if (!m) return {ok:false, err:'no ssr'};
  const it = ((JSON.parse(m[1]).__DEFAULT_SCOPE__||{})['webapp.video-detail']||{}).itemInfo?.itemStruct;
  if (!it) return {ok:false, err:'no item'};
  if (it.imagePost) {
    return {ok:true, photo:true, item:it,
            images:(it.imagePost.images||[]).map(im => (im.imageURL||{}).urlList?.[0]).filter(Boolean)};
  }
  const v = it.video || {};
  const src = v.playAddr || v.downloadAddr || ((v.bitrateInfo||[])[0]?.PlayAddr?.UrlList||[])[0];
  if (!src) return {ok:false, err:'no playAddr', item:it};
  try {
    const r = await fetch(src, {credentials:'include', referrer:'https://www.tiktok.com/'});
    const b = new Uint8Array(await r.arrayBuffer());
    let bin = ''; for (let i = 0; i < b.length; i += 0x8000) bin += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
    return {ok:r.ok, status:r.status, photo:false, item:it, b64:btoa(bin), bytes:b.length};
  } catch(e) { return {ok:false, err:'media '+e, item:it} }
})()
"""


def launch():
    prof = tempfile.mkdtemp(prefix="ttscrape-")
    port = 9333
    proc = subprocess.Popen([
        CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}",
        "--mute-audio", "--remote-allow-origins=*", "--no-first-run", "--no-default-browser-check", f"--user-agent={UA}",
        "--window-size=1280,900", "--autoplay-policy=user-gesture-required", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    tab = Tab(port)
    tab.cmd("Page.enable")
    return proc, prof, tab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["search", "user", "video", "download"])
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sleep", type=float, default=1.5)
    a = ap.parse_args()

    if a.mode == "download":
        return download(a)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    seen = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try: seen.add(json.loads(line)["id"])
            except Exception: pass
    out = open(a.out, "a")
    proc, prof, tab = launch()
    try:
        tab.goto("https://www.tiktok.com/search?q=discipline", wait=8)
        added = 0
        for t in a.targets:
            if a.mode == "search":
                cursor, sid = 0, ""
                for page in range(a.pages):
                    try:
                        r = tab.js(SEARCH_JS % {"kw": json.dumps(t), "cursor": cursor, "sid": json.dumps(sid)})
                    except RuntimeError as e:
                        print(f"[{t}] page {page}: js error {e}", file=sys.stderr); time.sleep(3); continue
                    if not r or not r.get("ok"):
                        print(f"[{t}] page {page}: blocked {r and r.get('head')}", file=sys.stderr); break
                    n = 0
                    for it in r["items"]:
                        if it.get("id") in seen: continue
                        seen.add(it["id"]); out.write(json.dumps(compact(it, t), ensure_ascii=False) + "\n"); n += 1
                    added += n
                    print(f"[{t}] page {page}: {len(r['items'])} items, {n} new", file=sys.stderr)
                    if not r.get("has_more"): break
                    cursor, sid = r.get("cursor") or cursor + 20, r.get("sid") or sid
                    time.sleep(a.sleep)
            elif a.mode == "user":
                h = t.lstrip("@")
                tab.goto(f"https://www.tiktok.com/@{h}", wait=7)
                sec = (tab.js(USER_JS) or {}).get("secUid")
                got = 0
                if sec:
                    cursor = "0"
                    for page in range(a.pages):
                        r = tab.js(USER_LIST_JS % {"sec": json.dumps(sec), "cursor": json.dumps(cursor)})
                        if not r or not r.get("ok") or not r.get("items"):
                            break
                        for it in r["items"]:
                            if it.get("id") in seen: continue
                            seen.add(it["id"]); out.write(json.dumps(compact(it, "@" + h), ensure_ascii=False) + "\n"); got += 1
                        if not r.get("has_more"): break
                        cursor = str(r.get("cursor")); time.sleep(a.sleep)
                if not got:  # fall back to the rendered grid (views only)
                    for g in tab.js(DOM_GRID_JS) or []:
                        vid = g["url"].rstrip("/").split("/")[-1]
                        if vid in seen: continue
                        seen.add(vid)
                        out.write(json.dumps({"id": vid, "author": h, "url": g["url"], "views_text": g["views"],
                                              "desc": g["desc"], "query": "@" + h, "grid_only": True},
                                             ensure_ascii=False) + "\n"); got += 1
                added += got
                print(f"[@{h}] {got} items (secUid={'yes' if sec else 'no'})", file=sys.stderr)
            else:
                r = tab.js(VIDEO_JS % {"url": json.dumps(t.replace("/photo/", "/video/"))})
                if r and r.get("ok"):
                    out.write(json.dumps(compact(r["item"], "video"), ensure_ascii=False) + "\n"); added += 1
                time.sleep(a.sleep)
            out.flush()
        print(f"added {added} -> {a.out}", file=sys.stderr)
    finally:
        out.close()
        proc.terminate()
        try: proc.wait(5)
        except Exception: proc.kill()
        shutil.rmtree(prof, ignore_errors=True)


def download(a):
    import base64
    os.makedirs(a.out, exist_ok=True)
    proc, prof, tab = launch()
    try:
        tab.goto("https://www.tiktok.com/search?q=discipline", wait=8)
        for t in a.targets:
            url = t if t.startswith("http") else "https://www.tiktok.com/@{1}/video/{0}".format(*t.split("@"))
            url = url.replace("/photo/", "/video/")
            vid = url.rstrip("/").split("/")[-1].split("?")[0]
            if os.path.exists(os.path.join(a.out, vid + ".json")):
                print(f"{vid}: cached", file=sys.stderr); continue
            try:
                r = tab.js(DOWNLOAD_JS % {"url": json.dumps(url)})
            except RuntimeError as e:
                print(f"{vid}: js error {e}", file=sys.stderr); continue
            if r and r.get("item"):
                json.dump(r["item"], open(os.path.join(a.out, vid + ".json"), "w"), ensure_ascii=False)
            if not r or not r.get("ok"):
                print(f"{vid}: FAILED {r and r.get('err')} {r and r.get('status')}", file=sys.stderr); continue
            if r.get("photo"):
                d = os.path.join(a.out, vid); os.makedirs(d, exist_ok=True)
                for i, im in enumerate(r["images"]):
                    subprocess.run(["curl", "-s", "-L", "-A", UA, "-e", "https://www.tiktok.com/", "-o",
                                    os.path.join(d, f"{i+1:02d}.jpg"), im], stdin=subprocess.DEVNULL)
                print(f"{vid}: photo x{len(r['images'])}", file=sys.stderr)
            else:
                open(os.path.join(a.out, vid + ".mp4"), "wb").write(base64.b64decode(r["b64"]))
                print(f"{vid}: video {r['bytes']//1024} KB", file=sys.stderr)
            time.sleep(a.sleep)
    finally:
        proc.terminate()
        try: proc.wait(5)
        except Exception: proc.kill()
        shutil.rmtree(prof, ignore_errors=True)


if __name__ == "__main__":
    main()
