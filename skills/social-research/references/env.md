# Where things live — format

Keep the real values in `local/skills/social-research/env.md` (git-ignored). Per app record:

## <App> (<one-line category>)
- Research root: `<app repo>/growth/research/` — one folder per sweep: `<topic>-<yyyy-mm[-dd]>/`
  with `search.jsonl`, `user-<handle>.jsonl`, `media/`, `prep/` or `sheets/`/`strips/`, `findings.md`.
- Tools: `<app repo>/growth/tools/` (copies of this skill's `scripts/`).
- Own-account metrics: `growth/metrics/stats-history.jsonl`, `studio-<date>.csv`.
- PostHog: the app's `posthog_project_id` from `local/apps.yaml`, event `Application Installed`.
- Figma carousel templates: the app's `figma_file_key`, page name.
- Accounts: the app's `social` block in `local/apps.yaml` (platform, handle, role, status).
- App Store name used in copy; whether the store link goes in the bio yet.

## Data tools and their state (update the date each time)
| Tool | Cost | State |
|---|---|---|
| vidIQ MCP `instagram_tiktok_outlier_search` | ~5 credits/search; profile reels 5; watch 10 | <credits left, reset date> |
| AppKittie `list_organic_content` | 1 credit/call | <ok / 402> |
| ScrapeCreators | paid | <ok / 402> |
| `scripts/tt_scrape.py` | free | ~15 rapid searches → blocked; download mode may break |
| `yt-dlp` (no login) | free | works for TikTok and IG reels; `-J` for metadata |
| Virality-predictor tools | credits | not useful: score everything in a narrow band |
