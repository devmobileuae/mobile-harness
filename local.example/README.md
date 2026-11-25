# local/: your apps, IDs, keys and case notes

The plugin is generic: skills hold rules and methods, not anyone's apps. What is specific to you lives in
`local/`, which git ignores:

```
local/                     ← git-ignored, yours only
├── apps.yaml              ← your apps: links, bundle IDs, ASC / PostHog / RevenueCat / Figma IDs
├── secrets.env            ← API keys and tokens (chmod 600); never pasted into chat or committed
└── skills/<skill>/*.md    ← your own case notes per skill: past design rounds, incident logs,
                             baselines, keyword sets. Skills read them when they exist.
```

## Set it up

Ask Claude Code in this repo: "set up the harness for my apps". The `setup` skill asks about your apps
and fills `apps.yaml`. Or run the script:

```bash
python3 scripts/setup.py           # creates local/, adds apps interactively
python3 scripts/setup.py --check   # shows what is filled and what is empty
python3 scripts/setup.py --get myapp.posthog_project_id
```

Leave anything you don't have empty. A skill that needs a missing value asks for it and saves it.

## How skills use it

- "The app's `<field>` from `local/apps.yaml`" means the field of the app you are working on.
- Scripts take the app as an argument (`--app myapp`) or read keys from the environment; load them with
  `set -a; . local/secrets.env; set +a`.
- Case notes: when a skill finishes a round, an incident or an audit for your app, it appends the
  outcome to `local/skills/<skill>/<app>.md`. Next time it reads that file first, so it learns your
  preferences without them ever reaching the repo.
- Key files (App Store Connect `.p8`, Apple Ads private key) stay where you keep them; `secrets.env`
  holds only their paths.
