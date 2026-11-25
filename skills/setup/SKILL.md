---
name: setup
description: "Use when someone sets up this plugin for their own apps, adds a new app, or a skill needs an app value (bundle id, store link, ASC / PostHog / RevenueCat / Figma id) that local/apps.yaml does not have. Fills the git-ignored local/ folder with scripts/setup.py. Triggers: \"set up the harness\", \"configure it for my apps\", \"add my app\"."
---

# Setup: your apps, IDs and keys in local/

Skills in this plugin are generic. Everything specific to a user lives in the git-ignored `local/`:
`apps.yaml` (one block per app), `secrets.env` (keys), `skills/<skill>/<app>.md` (case notes the skills
write as you work). Format and rules: `local.example/README.md`.

## Steps

1. Run `python3 scripts/setup.py --check`. It creates `local/` if missing and shows each app's filled and
   empty fields.
2. Ask which apps to add: name, platforms, one line on what the app does. Then ask for the IDs, grouped
   per app in one short message, and say where to find each:
   - ASC app ID: App Store Connect → App Information → Apple ID;
   - PostHog project ID: PostHog → Settings → Project;
   - RevenueCat project ID: the `proj…` part of the dashboard URL;
   - Figma file key: the part of the file URL after `/design/`.
   Empty is fine.
3. Write answers with `python3 scripts/setup.py --add <key> name="…" platforms=ios,android …` and
   `--set <key>.<field>=<value>`. Edit `apps.yaml` by hand only if the script is unavailable.
4. Keys and tokens: never ask for them in chat. Name the line in `local/secrets.env` and let the user
   fill it; for key files ask only for the path.
5. Finish with `--check` and report what is filled and what other skills will ask for later.

## Rules

- Never write a personal value into a tracked file. Tracked files stay generic; values go to `local/`.
- A skill that needs a missing value stops, asks for it, and saves it with `--set`.
- `local/` must stay in `.gitignore`. If `git status` ever shows a file under `local/`, fix the ignore
  rule before anything else.
