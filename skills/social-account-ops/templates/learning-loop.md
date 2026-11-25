<!-- The rules Claude applies at each stats review; the collector is ../scripts/stats_tick.py.
     Copy into <app repo>/growth/tools/ and set the paths and the launchd label. -->
# Learning loop — how reactions change the next posts

Goal: the audience's reactions to posts are evaluated in near real time and change the next posts,
around the clock, alternating day and night.

## Moving parts
- **Collector (no Claude):** launchd `~/Library/LaunchAgents/dev.<app>.tiktok-stats.plist` runs
  `tools/stats_tick.py` every 30 min (log `~/Library/Logs/<app>-tiktok-stats.log`; set `OWNER_TZ`). It appends
  snapshots to `metrics/stats-history.jsonl` and writes `metrics/dashboard/learn_posts.json`,
  `learn_tags.json`, `decisions.json` and `metrics/signals.txt`.
  Stop it: `launchctl bootout gui/$(id -u)/dev.<app>.tiktok-stats`.
- **Score:** views at 1 / 3 / 24 h ÷ median of the same account's posts at that age. Flags: `hot`
  (≥ 2× and ≥ 50 views within 12 h), `flat` (< 0.3× after 24 h), `zero` (0 views after 24 h).
- **Slots:** `tools/cadence_plan.py` — day (US morning/lunch) and night (US evening) windows; each account gets
  its own D / N / DD / NN / DN pattern per audience day.
- **Decisions log:** every change to the plan is one line in `metrics/decisions.jsonl`
  ({at, account, what, why}).

## Rules Claude applies at each review (and when building new posts)
1. **Hot post → part 2.** Next free slot on that account gets a «part 2» of the same hook/template
   (new angle, same format). If the queued post there is a different template, swap it later in the queue.
2. **Explore / exploit.** About 70 % of new posts use the best-scoring template/sound/slot for that
   account, 30 % test something new. With < 3 scored posts per variant, keep alternating instead.
3. **Flat ×3 → pause.** A template with three flat/zero posts in a row on an account is paused there;
   its queued posts are swapped for the best template, or rewritten.
4. **Time of day.** After ~6 posts per account, shift the D/N mix toward the better slot (keep ≥ 1 in 4
   in the weaker slot so the comparison stays alive).
5. **Never** change a post in the 45 min before its slot; never delete a published post.
6. Each review: log decisions, refresh the dashboard.

Caveats: 0-view carousels give no signal — the loop can only rank what gets distributed. With
2 posts/day/account the first stable reads come after ~a week.
