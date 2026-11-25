# Pulling your own accounts' retention (TikTok Studio / IG Insights)

Use it when public views can't explain a plateau: traffic sources, average watch and the drop point are not public.

## How

- Only from the owner's own phone/app session, a few posts at a time; or ask the owner for Insights screenshots.
  One way: screenshot each post's Studio Analytics screen, OCR it (e.g. a small macOS Vision binary).
- Save as `growth/metrics/studio-<date>.csv` with columns
  `account,post_id,file,hook,views,avg_watch_s,full_pct,new_followers,avg_pct,drop_at,dur_s,foryou_pct`
  so later pulls compare. Per account compute: rows, median views, max, avg watch, For You %, how many drop at 0:01–0:02.
  Your pulls go in `local/skills/social-research/`.

## What a typical pull of a young multi-account setup shows

1. 90–99% of views come from For You → the platform is not suppressing the accounts (unless one gets ~0 impressions).
2. ~3 s average watch on every format; almost every post loses most viewers at 0:01–0:02.
3. Higher full-watch % on very short posts doesn't lift reach on its own.
4. → The problem is the first second plus no payoff to wait for, not volume or hooks in captions. Research next
   the formats with motion at 0.0 s, 1-word labels and a winner to wait for.
