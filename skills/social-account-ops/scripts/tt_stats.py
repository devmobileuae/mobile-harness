#!/usr/bin/env python3
# Imported by stats_tick.py (same file as social-research/scripts/tt_stats.py).
#   python3 tt_stats.py https://www.tiktok.com/@user/video/<id> | @user
"""Public TikTok stats for videos or a profile, read from the page's SSR JSON (no login, no playback).

    python3 tt_stats.py https://www.tiktok.com/@user/video/123 [...]
    python3 tt_stats.py @user            # profile: followers / likes / video count
"""
import json, re, sys, urllib.request

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36'


def scope(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
    m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(m.group(1))['__DEFAULT_SCOPE__']


def video(url):
    # photo (carousel) posts only expose their stats under the /video/<id> form of the link
    it = scope(url.replace('/photo/', '/video/'))['webapp.video-detail']['itemInfo']['itemStruct']
    s = it['stats']
    return {'id': it['id'], 'views': s['playCount'], 'likes': s['diggCount'], 'comments': s['commentCount'],
            'shares': s['shareCount'], 'saves': int(s.get('collectCount') or 0), 'sound': it['music']['title'], 'music_id': it['music']['id'],
            'sound_author': it['music'].get('authorName'),
            'author_followers': (it.get('authorStats') or {}).get('followerCount')}


def profile(handle):
    u = scope(f'https://www.tiktok.com/{handle}')['webapp.user-detail']['userInfo']
    s = u['stats']
    return {'handle': handle, 'followers': s['followerCount'], 'likes': s['heartCount'], 'videos': s['videoCount']}


if __name__ == '__main__':
    for a in sys.argv[1:]:
        try:
            print(json.dumps(profile(a) if a.startswith('@') else video(a), ensure_ascii=False))
        except Exception as e:
            print(json.dumps({'target': a, 'error': repr(e)}))
