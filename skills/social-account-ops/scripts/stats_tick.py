#!/usr/bin/env python3
# Reads public stats only (no publishing code).
# The learning-loop collector: snapshots every live post, interpolates views at 1/3/24 h, scores vs the account median,
# flags hot/flat/zero, aggregates per template/sound/slot. Reads growth/accounts.json, writes growth/metrics/*.
# Runs every 30 min from launchd (label e.g. dev.<app>.tiktok-stats). Manual: python3 tools/stats_tick.py [--all]
# Owner's time zone for logs: $OWNER_TZ (IANA name, default UTC).
"""Stats tick: snapshot every live post's public numbers and score it against its own account
so reactions change the next posts. Runs every 30 min from launchd, no Claude.

Snapshots go to metrics/stats-history.jsonl (same rows collect_dashboard.py writes, plus
comments/shares/saves). Young posts are read often, old ones rarely:
  < 6 h every tick · 6–48 h hourly · 2–7 days every 6 h · older once a day.

Learning (pure numbers, no decisions here):
  - views at 1 h / 3 h / 24 h after posting (interpolated between snapshots);
  - score = views at the latest checkpoint ÷ the median of the same account's posts at that
    checkpoint (accounts differ too much to compare raw views);
  - flag: hot (≥ 2× median and ≥ 50 views) → a «part 2» candidate; flat (< 0.3× after 24 h);
  - per tag (template, sound, slot day/night, ET hour block, slides) — mean score, posts, views,
    engagement and save+share rates.
Writes metrics/dashboard/learn_posts.json, learn_tags.json, decisions.json (from
metrics/decisions.jsonl, which Claude appends to when it changes the plan) and metrics/signals.txt.

    python3 stats_tick.py [--all]   # --all: read every post now, ignoring the cadence
"""
import argparse, datetime as dt, json, os, re, statistics, sys, time
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tt_stats import video

ET = ZoneInfo('America/New_York')
OWN = ZoneInfo(os.environ.get('OWNER_TZ', 'UTC'))
GROWTH = os.environ.get('GROWTH_DIR') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY = os.path.join(GROWTH, 'metrics', 'stats-history.jsonl')
DECISIONS = os.path.join(GROWTH, 'metrics', 'decisions.jsonl')
OUT = os.path.join(GROWTH, 'metrics', 'dashboard')
TZ = {'EDT': ET, 'EST': ET, 'ET': ET, 'UTC': ZoneInfo('UTC')}


def zone(label):
    return TZ.get(label) or ZoneInfo(label)  # 'ET' / 'UTC' or any IANA name, e.g. 'Europe/Lisbon'
TEMPLATES = ['imessage', 'tweet', 'chatgpt', 'lockscreen', 'screentime']
CHECKPOINTS = [1, 3, 24]


def posted_at(p):
    """Unix time the post went out, from 'YYYY-MM-DD HH:MM <ET|UTC|IANA zone> …' (None if unknown)."""
    m = re.match(r'(\d{4}-\d\d-\d\d \d\d:\d\d) (\S+)', str(p.get('posted') or ''))
    if not m:
        return None
    return dt.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M').replace(tzinfo=zone(m.group(2))).timestamp()


def tags(acc, p, t0):
    f = p.get('file') or ''
    kind = 'slideshow' if p.get('post_as') == 'slideshow' else 'carousel' if '/carousels/' in f else 'video'
    name = os.path.basename(f.rstrip('/'))
    template = next((k for k in TEMPLATES if k in name), None)
    if not template:
        # format folders: /deck/, /stills/, /chart/, or f<N>-<slug>/ (the slug becomes the template tag)
        fmt = next((v for k, v in (('/deck/', 'deck'), ('/stills/', 'still'), ('/chart/', 'chart')) if k in f), None)
        mf = re.search(r'(?:^|/)f\d+-([a-z0-9-]+)/', f)
        template = fmt or (mf.group(1) if mf else None) or ('tips-photo' if kind == 'carousel' else 'ugc-demo' if 'renders' in f else 'video-other')
    e = dt.datetime.fromtimestamp(t0, ET)
    raw = p.get('live_sound') or p.get('expected_sound') or p.get('sound_actual') or p.get('sound') or ''
    sound = re.split(r' — | - |[:(]| from ', raw)[0].strip()[:40]
    slides = len([x for x in os.listdir(os.path.join(GROWTH, f)) if re.fullmatch(r'\d\d\.png', x)]) if kind == 'carousel' and os.path.isdir(os.path.join(GROWTH, f)) else None
    return {'account': re.sub(r'^[a-z0-9]+-(?=(?:tt|ig|yt)-)', '', acc['profile']), 'kind': kind, 'template': template, 'sound': sound or '?',
            'slot': 'day' if 7 <= e.hour < 15 else 'night', 'hour_et': f'{e.hour // 3 * 3:02d}–{e.hour // 3 * 3 + 3:02d} ET',
            'slides': slides, 'hook': (p.get('hook') or p.get('title') or (p.get('caption') or '').split(' #')[0] or name)[:80]}


def due(age_h, last_age_min):
    if last_age_min is None:
        return True
    step = 25 if age_h < 6 else 55 if age_h < 48 else 6 * 60 - 5 if age_h < 168 else 24 * 60 - 5
    return last_age_min >= step


def at_age(snaps, t0, h):
    """Views h hours after posting, linear between the snapshots around it (None if not bracketed)."""
    pts = sorted(((ts - t0) / 3600, v) for ts, v in snaps)
    if not pts or pts[-1][0] < h:
        return None
    prev = (0.0, 0)
    for age, v in pts:
        if age >= h:
            a0, v0 = prev
            return round(v0 + (v - v0) * (h - a0) / (age - a0)) if age > a0 else v
        prev = (age, v)
    return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--all', action='store_true'); a = ap.parse_args()
    now = time.time()
    accounts = json.load(open(os.path.join(GROWTH, 'accounts.json')))['accounts']
    hist = [json.loads(l) for l in open(HISTORY)] if os.path.exists(HISTORY) else []
    snaps = {}
    for h in hist:
        ts = dt.datetime.strptime(h['at'], '%Y-%m-%d %H:%M').replace(tzinfo=OWN).timestamp()
        snaps.setdefault(h['post'], []).append((ts, h))

    live = []
    for acc in accounts:
        for p in acc.get('posts', []):
            m = re.search(r'/(?:video|photo)/(\d+)', p.get('url') or '')
            t0 = posted_at(p)
            if m and t0:
                live.append((m.group(1), acc, p, t0))

    new_rows, read, failed = [], 0, 0
    for pid, acc, p, t0 in live:
        age_h = (now - t0) / 3600
        last = max((ts for ts, _ in snaps.get(pid, [])), default=None)
        if not a.all and not due(age_h, None if last is None else (now - last) / 60):
            continue
        try:
            s = video(p['url'])
        except Exception as e:
            failed += 1
            print(f'{pid}: {type(e).__name__}', file=sys.stderr)
            continue
        read += 1
        row = {'post': pid, 'at': dt.datetime.fromtimestamp(now, OWN).strftime('%Y-%m-%d %H:%M'), 'views': s['views'],
               'likes': s['likes'], 'comments': s['comments'], 'shares': s['shares'], 'saves': s['saves'], 'src': 'tick'}
        new_rows.append(row)
        snaps.setdefault(pid, []).append((now, row))
        time.sleep(2)
    if new_rows:
        with open(HISTORY, 'a') as fh:
            for r in new_rows:
                fh.write(json.dumps(r) + '\n')

    # --- learning ---------------------------------------------------------------------------------
    posts = []
    for pid, acc, p, t0 in live:
        ss = sorted(snaps.get(pid, []), key=lambda x: x[0])
        if not ss:
            continue
        last = dict(ss[-1][1])
        for k in ('comments', 'shares', 'saves'):     # collect_dashboard.py rows carry only views/likes
            if k not in last:
                last[k] = next((r[k] for _, r in reversed(ss) if k in r), 0)
        row = {'post': pid, 'url': p['url'], **tags(acc, p, t0),
               'posted_local': dt.datetime.fromtimestamp(t0, OWN).strftime('%Y-%m-%d %H:%M'),
               'age_h': round((now - t0) / 3600, 1), 'views': last['views'], 'likes': last.get('likes') or 0,
               'comments': last.get('comments') or 0, 'shares': last.get('shares') or 0, 'saves': last.get('saves') or 0}
        for h in CHECKPOINTS:
            row[f'v{h}h'] = at_age([(ts, r['views']) for ts, r in ss], t0, h)
        posts.append(row)
    med = {}
    for h in CHECKPOINTS:
        for accn in {r['account'] for r in posts}:
            vals = [r[f'v{h}h'] for r in posts if r['account'] == accn and r[f'v{h}h'] is not None]
            med[(accn, h)] = statistics.median(vals) if len(vals) >= 2 else None
    for r in posts:
        r['score'], r['flag'], r['vs'] = None, '', ''
        for h in reversed(CHECKPOINTS):
            v, m = r[f'v{h}h'], med.get((r['account'], h))
            if v is not None and m:
                r['score'] = round(v / m, 2); r['vs'] = f'{h} h'
                break
            if v is not None and m == 0:
                r['score'] = None; r['vs'] = f'{h} h'
                break
        early = next((r[f'v{h}h'] for h in (3, 1) if r[f'v{h}h'] is not None), r['views'] if r['age_h'] < 6 else None)
        m_early = med.get((r['account'], 3)) or med.get((r['account'], 1))
        if early is not None and r['age_h'] < 12 and early >= 50 and (not m_early or early >= 2 * m_early):
            r['flag'] = 'hot'
        elif r['age_h'] >= 24 and r['score'] is not None and r['score'] < 0.3:
            r['flag'] = 'flat'
        elif r['age_h'] >= 24 and r['views'] == 0:
            r['flag'] = 'zero'
        eng = r['likes'] + r['comments'] + r['shares'] + r['saves']
        r['eng_rate'] = round(eng / r['views'], 3) if r['views'] else None
        r['keep_rate'] = round((r['shares'] + r['saves']) / r['views'], 4) if r['views'] else None

    tag_rows = []
    for dim in ['template', 'sound', 'slot', 'hour_et', 'slides', 'kind']:
        groups = {}
        for r in posts:
            if r[dim] is not None:
                groups.setdefault(str(r[dim]), []).append(r)
        for val, rs in groups.items():
            scored = [r['score'] for r in rs if r['score'] is not None]
            views = sum(r['views'] for r in rs)
            tag_rows.append({'id': f'{dim}:{val}', 'dimension': dim, 'value': val, 'posts': len(rs), 'scored': len(scored),
                             'avg_score': round(statistics.mean(scored), 2) if scored else None, 'views': views,
                             'eng_rate': round(sum(r['likes'] + r['comments'] + r['shares'] + r['saves'] for r in rs) / views, 3) if views else None,
                             'keep_rate': round(sum(r['shares'] + r['saves'] for r in rs) / views, 4) if views else None,
                             'zero_posts': sum(1 for r in rs if r['views'] == 0 and r['age_h'] >= 24)})
    tag_rows.sort(key=lambda r: (r['dimension'], -(r['avg_score'] or 0), -r['views']))
    decisions = [json.loads(l) for l in open(DECISIONS)] if os.path.exists(DECISIONS) else []

    os.makedirs(OUT, exist_ok=True)
    posts.sort(key=lambda r: r['posted_local'], reverse=True)
    for name, rows in [('learn_posts', posts), ('learn_tags', tag_rows), ('decisions', decisions[::-1])]:
        json.dump(rows, open(os.path.join(OUT, f'{name}.json'), 'w'), ensure_ascii=False, indent=1)
    sig = [f"{r['flag'].upper():4} {r['account']:6} {r['views']:>6} views at {r['age_h']} h  {r['template']:15} «{r['hook'][:50]}» {r['url']}"
           for r in posts if r['flag']]
    open(os.path.join(GROWTH, 'metrics', 'signals.txt'), 'w').write(
        f"updated {dt.datetime.fromtimestamp(now, OWN):%Y-%m-%d %H:%M} {OWN.key}\n" + ('\n'.join(sig) or 'no signals') + '\n')
    print(f'{dt.datetime.fromtimestamp(now, OWN):%d.%m %H:%M} read {read}, failed {failed}, posts {len(posts)}, signals {len(sig)}')


if __name__ == '__main__':
    main()
