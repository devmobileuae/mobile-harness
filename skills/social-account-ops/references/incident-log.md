# Incident log — format and known classes

Keep your real log in `local/skills/social-account-ops/incident-log.md` (git-ignored); sources: the app's
`growth/metrics/decisions.jsonl`. Each row: symptom → real cause → what fixed it → rule it left.

| Date | Symptom | Cause | Fix | Rule |
|---|---|---|---|---|
| YYYY-MM-DD | <what the numbers showed> | <real cause, or "unproven"> | <what changed> | <rule, short> |

## Known classes

| Symptom | Cause | Fix | Rule |
|---|---|---|---|
| Posts came out with a random «original sound» instead of the planned track | TikTok auto-picks a recommended sound for silent uploads and the upload path kept it | set the sound in the app at posting; verify `music_id` with `tt_stats.py` after posting | never rely on an upload API's reference sound for a post that needs a specific track |
| Photo carousels: 0 views after 2–28 h; public, not under review (playCount 0 via `/video/<id>`) | photo mode gets no distribution on fresh accounts | same slides as a 16–22 s slideshow video → ~100 views in 1 h | slideshow video is the default on carousel accounts |
| One account: 0 views on every post, any format | the account gets no impressions | pause it, hold its queue | don't feed a dead account |
| An account stuck at ~250 views | many posts re-cut from a few clips — likely near-duplicate dampening (unproven) | one fresh take per post | never re-cut the same footage into many posts |

## Learning-loop decisions that fired (pattern)

- A post at ~5× the account median in 3 h → a continuation moved up to the next slot (rule 1).
- A "part 2" built for a post with ~90–300 views in 6 h on a young account.
- A slideshow flagged hot right after zero-view carousels → **no** part 2: the jump came from the format switch.
- A format confirmed 2/2 (e.g. decks ~250 views, 6% likes, saves) → several more queued.
