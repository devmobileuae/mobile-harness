#!/usr/bin/env python3
# Re-times every QUEUED/SERVER post in <growth>/accounts.json into a 2-post (DN) / 3-post (DDN|DNN) rhythm per
# audience day, alternating per account. Windows are given in the AUDIENCE time zone (default US Eastern:
# day 07:35-13:25 = morning/lunch, night 16:35-20:55 = evening); output is shown in the owner's zone too.
# >=25 min between any two publishes, >=3.5 h between one account's posts; posts due within --keep hours stay.
# It only plans times; publishing is out of scope.
#   python3 cadence_plan.py --growth <app>/growth                 # dry run: table + metrics/schedule-cadence.json
#   python3 cadence_plan.py --growth <app>/growth --apply         # writes scheduled_at / slot_kind into accounts.json
#   python3 cadence_plan.py --growth <app>/growth --keep 250      # keep every scheduled post, append new ones at the end
"""Re-time the live queue at 2 / 3 posts per audience day, alternating.

Per account and audience day the pattern is DN (2 posts) or a 3-post day: DDN or DNN (two posts in one
window, >=3.5 h apart). Accounts alternate which day starts with 3 posts and which 3-post shape they use,
so the load is spread. Paused accounts (`"paused": true`) are skipped. Optional per-account `"order"`: a list
of file suffixes that sets the order of unscheduled posts (rotate formats so one account never posts the same
format twice in a row).

accounts.json shape: {"accounts": [{"profile": "myapp-tt-01", "paused": false, "order": [...],
  "posts": [{"file": "...", "status": "QUEUED", "scheduled_at": "2026-11-28 16:10 America/New_York", ...}]}]}
"""
import argparse, datetime as dt, json, os, random, re
from zoneinfo import ZoneInfo


def parse_hm(s):
    a, b = s.split('-')
    return tuple(int(x) for x in a.split(':')), tuple(int(x) for x in b.split(':'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--growth', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help='growth folder with accounts.json and metrics/ (default: parent of this script dir)')
    ap.add_argument('--audience-tz', default='America/New_York')
    ap.add_argument('--tz', default=os.environ.get('OWNER_TZ', 'UTC'), help="owner's zone for display and scheduled_at")
    ap.add_argument('--day', default='07:35-13:25', help='day window in the audience zone')
    ap.add_argument('--night', default='16:35-20:55', help='night window in the audience zone')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--seed', type=int, default=1025)
    ap.add_argument('--keep', type=float, default=2.0)
    ap.add_argument('--lead', type=int, default=20, help='minutes from now before the first new slot')
    a = ap.parse_args()
    AUD, OWN = ZoneInfo(a.audience_tz), ZoneInfo(a.tz)
    DAY, NIGHT = parse_hm(a.day), parse_hm(a.night)
    rng = random.Random(a.seed)
    path = os.path.join(a.growth, 'accounts.json'); acc = json.load(open(path))
    accounts = [x for x in acc['accounts'] if not x.get('paused')]
    now = dt.datetime.now().timestamp()

    def at(day, hm):
        return dt.datetime.strptime(day, '%Y-%m-%d').replace(hour=hm[0], minute=hm[1], tzinfo=AUD).timestamp()

    def wins(day, pat):
        D, N = (at(day, DAY[0]), at(day, DAY[1])), (at(day, NIGHT[0]), at(day, NIGHT[1]))
        gap = 3.5 * 3600
        two = lambda w: [(w[0], w[1] - gap), (w[0] + gap, w[1])]
        return {'DN': [D, N], 'DDN': two(D) + [N], 'DNN': [D] + two(N)}[pat]

    def ts(p):
        m = re.match(r'(\d{4}-\d\d-\d\d \d\d:\d\d)\s*(\S+)?', p.get('scheduled_at') or '')
        if not m:
            return None
        try:
            z = ZoneInfo({'ET': 'America/New_York'}.get(m.group(2), m.group(2))) if m.group(2) else OWN
        except Exception:
            z = OWN
        return dt.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M').replace(tzinfo=z).timestamp()

    first_day = dt.datetime.now(AUD)
    live = lambda p: (p.get('status') or '').startswith(('QUEUED', 'SERVER'))
    due_soon = lambda p: ts(p) and now < ts(p) < now + a.keep * 3600
    taken, plan, anchors = [], [], {}
    for A in accounts:  # anchors: anything due within --keep hours stays put
        for p in A['posts']:
            if live(p) and due_soon(p):
                t = ts(p); anchors.setdefault(A['profile'], []).append(t); taken.append(t); plan.append((A['profile'], p, t, 'keep'))
    for i, A in enumerate(accounts):
        pr = A['profile']
        posts = [p for p in A['posts'] if live(p) and not due_soon(p)]
        sched = sorted([p for p in posts if ts(p)], key=ts)
        rest = [p for p in posts if not ts(p)]
        if A.get('order'):
            rest.sort(key=lambda p: next((k for k, s in enumerate(A['order']) if p['file'].endswith(s)), 999))
        seq = sched + rest
        prev = max(anchors.get(pr, [0]))
        three_first, shape = i % 2 == 0, ('DDN', 'DNN')[(i // 2) % 2]
        slots, day_i = [], 0
        while len(slots) < len(seq) + 40:
            day = (first_day + dt.timedelta(days=day_i)).strftime('%Y-%m-%d')
            pat = shape if (day_i % 2 == 0) == three_first else 'DN'
            slots += [(day, pat, w) for w in wins(day, pat)]
            day_i += 1
        si = 0
        for p in seq:
            while True:
                day, pat, (lo, hi) = slots[si]; si += 1
                lo = max(lo, now + a.lead * 60, prev + 3.5 * 3600)
                if lo >= hi:
                    continue
                t = None
                for _ in range(5000):
                    c = rng.uniform(lo, hi); c -= c % 60
                    if any(abs(c - x) < 25 * 60 for x in taken):
                        continue
                    t = c; break
                if t is not None:
                    break                      # else: this window is full, try the next one
            taken.append(t); prev = t
            plan.append((pr, p, t, f'{day} {pat}'))
    plan.sort(key=lambda r: r[2])
    out = []
    for pr, p, t, why in plan:
        d = dt.datetime.fromtimestamp(t, OWN); e = dt.datetime.fromtimestamp(t, AUD)
        e_min = e.hour * 60 + e.minute
        kind = 'day' if DAY[0][0] * 60 + DAY[0][1] <= e_min <= DAY[1][0] * 60 + DAY[1][1] else 'night'
        print(f"{d:%a %d.%m %H:%M} ({e:%a %H:%M} aud) {kind:5} {pr:14} {why:15} {p['file'][-52:]}")
        out.append({'owner_time': f'{d:%Y-%m-%d %H:%M}', 'aud_day': f'{e:%Y-%m-%d}', 'kind': kind, 'account': pr, 'file': p['file'],
                    'hook': p.get('hook') or p.get('title') or '', 'sound': p.get('live_sound', ''), 'keep': why == 'keep'})
        if a.apply and why != 'keep':
            p['scheduled_at'] = f'{d:%Y-%m-%d %H:%M} {a.tz}'
            p['slot_kind'] = kind
    os.makedirs(os.path.join(a.growth, 'metrics'), exist_ok=True)
    json.dump(out, open(os.path.join(a.growth, 'metrics/schedule-cadence.json'), 'w'), ensure_ascii=False, indent=1)
    per = {}
    for r in out:
        per.setdefault(r['account'], {}).setdefault(r['aud_day'], 0); per[r['account']][r['aud_day']] += 1
    for k, v in per.items():
        print(k, ' '.join(f'{d[5:]}:{n}' for d, n in sorted(v.items())))
    if a.apply:
        json.dump(acc, open(path, 'w'), ensure_ascii=False, indent=2); print('accounts.json updated')


if __name__ == '__main__':
    main()
