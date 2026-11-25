# Cadence and slots

The audience is assumed US; windows are given in US Eastern and converted to the owner's zone by
`cadence_plan.py --tz`. Your own decisions table (dates, the owner's words, per-account patterns, real
schedule slices) goes in `local/skills/social-account-ops/cadence-slots.md`.

## Rules that worked

| Rule | Why |
|---|---|
| 1 post/day in an account's first week, then 2/day | young accounts first, then volume |
| second slot for carousel/slideshow accounts from day 5 | same ramp, cheaper format |
| no US-early-morning slots (move them to US lunch) | ~8 AM ET is a dead hour |
| alternate day and night per account: D / N / DD / NN / DN patterns per audience day | keeps the comparison alive |
| build each post live at its slot, not from platform drafts | fresh takes, current sound |
| 2 posts/day everywhere, every other day 3 | volume once formats are confirmed |

## Windows

| Window | US Eastern | Meaning |
|---|---|---|
| Day | 07:35–13:25 | US morning/lunch |
| Night | 16:35–20:55 | US evening |

Spacing in `cadence_plan.py`: ≥ 25 min between any two publishes, ≥ 3.5 h between one account's posts,
posts due within `--keep` hours (default 2) are not moved. A post more than 45 min past its slot is re-slotted, not posted late.
Half the accounts start with a 3-post day, half with a 2-post day; 3-post shapes alternate DDN / DNN.
Per-account `order` in accounts.json rotates formats so an account never posts the same one twice in a row.

## What slot data tends to show (`metrics/dashboard/learn_tags.json`)

| Tag | Typical avg score (views ÷ account median) |
|---|---|
| slot:day vs slot:night | ≈1.1 vs ≈1.1 — a wash |
| kind:video, kind:slideshow | ≈1.15 |
| kind:carousel (photo mode, fresh accounts) | 0 |
| best templates (decks, charts) | 2–2.6 |
| plain UGC demos | ≈0.9 |

Read: don't spend effort on slot tuning; format is what moves the score. On Instagram, evening/night in the
audience's zone has looked better than mornings (weak evidence).
